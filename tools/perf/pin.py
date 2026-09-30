"""CPU topology, and pinning the single-threaded timing thread to one fixed logical CPU.

Why: this machine's Ryzen 9 9950X3D has two asymmetric CCDs -- one with 3D V-Cache (96 MiB
L3), one with 32 MiB L3 and higher boost clocks -- and the scheduler plus the AMD 3D V-Cache
driver choose a CCD per session. Unpinned, the CCD a thread lands on moved a DC pass by ~12%
and sessions drifted ~30% with clean load readings (A5 re-review N2). Pinning holds the
placement fixed and makes it part of the record.

The layout is READ, not assumed: GetLogicalProcessorInformationEx gives each L3 cache's
logical CPUs and size (RelationCache) and each physical core's logical CPUs (RelationProcessorCore,
i.e. the SMT pairs). The pin is one logical CPU of one physical core on the CCD with the
LARGEST L3 -- the parse tables (parser.c is 37 MiB) are cache-bound, and the measurement in
docs/performance-baselines.md ("CPU topology") confirms the choice. Core 0 of that CCD is
skipped: Windows steers interrupts and DPCs to CPU 0. The SMT sibling is left unpinned (it
cannot be reserved), and is named in the record.

Only the calling THREAD is pinned (SetThreadAffinityMask), so worker processes spawned later
keep the whole machine. GetCurrentProcessorNumber after every parse records where the thread
really ran.
"""
from __future__ import annotations

import os
import struct
import sys
import time
from collections import Counter


# ---- topology -------------------------------------------------------------------------

def _slpi(relation):
    import ctypes
    k = ctypes.windll.kernel32
    n = ctypes.c_ulong(0)
    k.GetLogicalProcessorInformationEx(relation, None, ctypes.byref(n))
    buf = ctypes.create_string_buffer(n.value)
    if not k.GetLogicalProcessorInformationEx(relation, buf, ctypes.byref(n)):
        raise OSError("GetLogicalProcessorInformationEx failed")
    raw, off, out = buf.raw, 0, []
    while off < n.value:
        _, size = struct.unpack_from("<II", raw, off)
        out.append(raw[off:off + size])
        off += size
    return out


def _cpus(mask, group):
    return [group * 64 + i for i in range(64) if mask >> i & 1]


def topology():
    """-> {"ccds": [{"l3_bytes", "cpus", "smt_pairs"}], "source"}; CCDs are the L3 domains,
    largest L3 first. None when it cannot be read (not Windows)."""
    if sys.platform != "win32":
        return None
    l3 = []
    for rec in _slpi(2):                                     # RelationCache
        level, _assoc, _line, size, _type = struct.unpack_from("<BBHII", rec, 8)
        mask, group = struct.unpack_from("<QH", rec, 40)
        if level == 3:
            l3.append((size, _cpus(mask, group)))
    cores = []
    for rec in _slpi(0):                                     # RelationProcessorCore
        mask, group = struct.unpack_from("<QH", rec, 32)
        cores.append(_cpus(mask, group))
    ccds = [{"l3_bytes": size, "cpus": cpus, "smt_pairs": [c for c in cores if set(c) <= set(cpus)]}
            for size, cpus in sorted(l3, key=lambda x: (-x[0], x[1]))]
    return {"ccds": ccds, "source": "GetLogicalProcessorInformationEx (RelationCache L3, RelationProcessorCore)"}


def choose_pin(topo):
    """-> (cpu, why). The first logical CPU of the SECOND physical core of the largest-L3 CCD."""
    if not topo:
        return 0, "topology unreadable on this platform: logical CPU 0"
    ccd = topo["ccds"][0]
    cores = ccd["smt_pairs"]
    core = cores[1] if len(cores) > 1 else cores[0]
    return core[0], (f"logical CPU {core[0]}: physical core {cores.index(core)} (SMT pair {core}) of the "
                     f"CCD with the largest L3 ({ccd['l3_bytes'] >> 20} MiB, CPUs {ccd['cpus'][0]}-"
                     f"{ccd['cpus'][-1]}); core 0 skipped (interrupt/DPC traffic); sibling "
                     f"{[c for c in core if c != core[0]]} not reserved")


def amd_vcache_driver():
    """The AMD 3D V-Cache Performance Optimizer driver's readable state: whether it is
    installed, and Preferences\\DefaultType (AMD: 0 = frequency, 1 = cache; not verified
    here). Its live State key needs admin rights and is not read."""
    if sys.platform != "win32":
        return "n/a"
    import winreg
    base = r"SYSTEM\CurrentControlSet\Services\amd3dvcache"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base + r"\Preferences") as k:
            default = winreg.QueryValueEx(k, "DefaultType")[0]
    except OSError:
        return {"installed": False}
    return {"installed": True, "preferences_default_type": default,
            "state": "not readable without admin rights"}


_TOPO = None


def pin_cpu():
    global _TOPO
    if _TOPO is None:
        _TOPO = topology()
    return choose_pin(_TOPO)


# ---- pinning --------------------------------------------------------------------------

def _k32():
    import ctypes
    k = ctypes.windll.kernel32
    k.GetCurrentThread.restype = ctypes.c_void_p
    k.SetThreadAffinityMask.restype = ctypes.c_size_t
    k.SetThreadAffinityMask.argtypes = (ctypes.c_void_p, ctypes.c_size_t)
    return k


def pin_thread(cpus):
    """Pin the calling thread to `cpus`; -> the previous mask/set, for unpin_thread()."""
    cpus = tuple(cpus)
    if sys.platform == "win32":
        prev = _k32().SetThreadAffinityMask(_k32().GetCurrentThread(), sum(1 << c for c in cpus))
        if not prev:
            raise OSError(f"SetThreadAffinityMask({cpus}) failed")
        return prev
    prev = os.sched_getaffinity(0)
    os.sched_setaffinity(0, set(cpus))
    return prev


def unpin_thread(prev):
    if sys.platform == "win32":
        _k32().SetThreadAffinityMask(_k32().GetCurrentThread(), prev)
    else:
        os.sched_setaffinity(0, prev)


def current_cpu():
    if sys.platform == "win32":
        return _k32().GetCurrentProcessorNumber()
    return os.sched_getcpu() if hasattr(os, "sched_getcpu") else -1


class Pinned:
    """with Pinned() as p: ... p.note() after each timed parse; p.record() for the JSON."""

    def __init__(self, cpus=None):
        if cpus is None:
            cpus = (pin_cpu()[0],)
        self.cpus, self.counts = tuple(cpus), Counter()

    def __enter__(self):
        self.prev = pin_thread(self.cpus)
        return self

    def __exit__(self, *exc):
        unpin_thread(self.prev)

    def note(self):
        self.counts[current_cpu()] += 1

    def record(self):
        return {"pinned_to": list(self.cpus), "ran_on": {str(k): v for k, v in sorted(self.counts.items())}}


def pin_process(pid, cpus):
    """Pin a whole child process (the WASM run's node) to `cpus`."""
    import psutil
    psutil.Process(pid).cpu_affinity(list(cpus))


# ---- calibration ----------------------------------------------------------------------

def calibrate(candidates, rounds=6, labels=("dc",)):
    """Interleaved passes on each candidate CPU set; round r visits the sets in rotated order,
    so a drift of the machine does not favour one set. -> {name: [seconds per pass]}."""
    from tools.perf import common
    files, _ = common.load(list(labels))
    parser = common.parser()
    for _, _, s in files:                                    # warm-up
        parser.parse(s)
    names, out = list(candidates), {n: [] for n in candidates}
    for r in range(rounds):
        for n in names[r % len(names):] + names[:r % len(names)]:
            with Pinned(candidates[n]):
                t = time.perf_counter_ns()
                for _, _, s in files:
                    parser.parse(s)
                out[n].append((time.perf_counter_ns() - t) / 1e9)
    return out


if __name__ == "__main__":
    # python -m tools.perf.pin                  -> the topology and the chosen pin
    # python -m tools.perf.pin calibrate [N]    -> the pin against one core on the other CCD
    import json
    from tools.perf import stats
    topo = topology()
    print(json.dumps(topo), pin_cpu(), amd_vcache_driver())
    if sys.argv[1:2] == ["calibrate"]:
        other = topo["ccds"][1]["smt_pairs"][1][0] if topo and len(topo["ccds"]) > 1 else 0
        res = calibrate({"pinned (cache CCD)": (pin_cpu()[0],), "other CCD": (other,)},
                        int(sys.argv[2]) if len(sys.argv) > 2 else 10)
        for n, xs in res.items():
            m = stats.median(xs)
            print(f"{n:20} median {m:.3f} s  min {min(xs):.3f}  max {max(xs):.3f}  runs {[round(x, 3) for x in xs]}")
