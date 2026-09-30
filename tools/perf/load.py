"""Machine load while a group runs: how much CPU processes OUTSIDE our own tree used.

A start-only reading (the first baseline's `busy` flag) passed a run whose native passes
were 20% slow; a 20% threshold on a 32-thread machine is 6.4 busy threads, and the idle
floor here is already ~10%. So the monitor samples for the whole group:

    outside cores = (system busy CPU-seconds - our tree's CPU-seconds) / wall seconds

per interval. System busy is user + system from psutil.cpu_times() (cheap), our tree is
this process and every descendant (a handful of cpu_times() calls). No per-process scan of
the whole machine runs while measuring -- that scan costs ~0.4 of a core by itself -- only
one top-5 snapshot at the start of the group, to name what was running.
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import time

INTERVAL = 1.0
# Thresholds, in logical cores, calibrated on 2026-09-30 on the idle workstation (desktop
# apps only: Task Manager, Teams, WmiPrvSE, MemCompression, fan control) with
# `python -m tools.perf.load SECONDS`, twice:
#     180 s: mean 3.37, p95 5.94, max 10.32 cores
#     120 s: mean 2.86, p95 5.04, max  6.03 cores
# The idle floor bursts: a 1 s max of 10 cores happens with nothing running. So:
#   - MAX (the coordinator's rule): idle max + 1 core = 11.3, rounded to 11.5. It catches a
#     heavy burst (a build, a test run) and nothing the idle machine already does.
#   - MEAN: idle mean + 1 core = 4.4, rounded to 4.5. It catches what the max cannot: one
#     competing thread held for the whole group, the smallest disturbance worth naming.
# Either flags the group. Neither was sampled for the first baseline's discarded 20%-slow
# run, so neither is proven to catch it; they catch what they are calibrated for.
OUTSIDE_MAX_CORES = 11.5
OUTSIDE_MEAN_CORES = 4.5


class _TreeCpu:
    """Cumulative CPU-seconds of a process tree, including processes that have EXITED.

    Reading each live descendant's cpu_times() loses a process's last slice when it exits
    between two samples; a pool of 31 workers exiting together then reads as up to 31 cores
    of "outside" CPU (measured: a 31-worker spin read as 13 outside cores). On Windows this
    keeps a handle open to every tree process it has seen: GetProcessTimes on an open handle
    still answers after the process exits, so nothing is lost. Elsewhere it falls back to the
    live reading, whose error is an over-read of outside CPU, never an under-read."""

    def __init__(self, root):
        self.root, self.handles, self.fallback = root, {}, {}

    def total(self):
        import psutil
        try:
            pids = [self.root.pid, *(c.pid for c in self.root.children(recursive=True))]
        except psutil.NoSuchProcess:
            pids = []
        if sys.platform == "win32":
            import ctypes
            k32 = ctypes.windll.kernel32
            for pid in pids:
                if pid not in self.handles:
                    h = k32.OpenProcess(0x1000, False, pid)      # PROCESS_QUERY_LIMITED_INFORMATION
                    if h:
                        self.handles[pid] = h
            total = 0
            for h in self.handles.values():
                c, e, k, u = (ctypes.c_ulonglong() for _ in range(4))
                if k32.GetProcessTimes(ctypes.c_void_p(h), *(ctypes.byref(x) for x in (c, e, k, u))):
                    total += k.value + u.value
            return total / 1e7                                     # 100 ns units
        for pid in pids:
            try:
                t = psutil.Process(pid).cpu_times()
                self.fallback[pid] = t.user + t.system
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return sum(self.fallback.values())

    def close(self):
        if sys.platform == "win32":
            import ctypes
            for h in self.handles.values():
                ctypes.windll.kernel32.CloseHandle(ctypes.c_void_p(h))
        self.handles.clear()


class LoadMonitor(threading.Thread):
    """Samples outside-CPU every INTERVAL s from start() to stop()."""

    def __init__(self, interval=INTERVAL, root_pid=None):
        super().__init__(daemon=True)
        import psutil
        self.tree = _TreeCpu(psutil.Process(root_pid or os.getpid()))
        self.interval, self._halt = interval, threading.Event()
        self.samples = []

    def run(self):
        import psutil
        last_wall = time.perf_counter()
        ct = psutil.cpu_times()
        last_busy, last_ours = ct.user + ct.system, self.tree.total()
        while not self._halt.wait(self.interval):
            wall = time.perf_counter()
            ct = psutil.cpu_times()
            busy, ours = ct.user + ct.system, self.tree.total()
            # A process first seen in this interval contributes all its CPU so far: it started
            # inside the interval (or was missed before, which only shifts it between samples).
            dt = wall - last_wall
            if dt > 0:
                self.samples.append(max(0.0, (busy - last_busy) - (ours - last_ours)) / dt)
            last_wall, last_busy, last_ours = wall, busy, ours
        self.tree.close()

    def stop(self):
        self._halt.set()
        self.join()
        return summary(self.samples)


def summary(samples):
    if not samples:
        return {"sampled": False}
    s = sorted(samples)
    out = {"sampled": True, "interval_s": INTERVAL, "samples": len(s),
           "outside_cores_mean": round(sum(s) / len(s), 3), "outside_cores_max": round(s[-1], 3),
           "outside_cores_p95": round(s[min(len(s) - 1, int(0.95 * len(s)))], 3),
           "threshold_max_cores": OUTSIDE_MAX_CORES, "threshold_mean_cores": OUTSIDE_MEAN_CORES}
    out["flagged"] = s[-1] > OUTSIDE_MAX_CORES or out["outside_cores_mean"] > OUTSIDE_MEAN_CORES
    return out


def snapshot():
    """One named reading at a group's start: total CPU over 2 s, the top 5 processes, free
    RAM, the CPU clock and the power plan."""
    import psutil
    procs = list(psutil.process_iter(["name", "pid"]))
    for p in procs:
        try:
            p.cpu_percent(None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    total = psutil.cpu_percent(interval=2)
    top = []
    for p in procs:
        try:
            if p.pid:
                top.append((p.cpu_percent(None), p.info["name"]))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    freq = psutil.cpu_freq()
    return {"cpu_percent_2s": total, "ram_available_bytes": psutil.virtual_memory().available,
            "top5": [f"{n} {c:.0f}%" for c, n in sorted(top, reverse=True)[:5]],
            "cpu_mhz": freq.current if freq else None, "power_plan": power_plan()}


def power_plan():
    if sys.platform != "win32":
        return "n/a"
    try:
        out = subprocess.run(["powercfg", "/getactivescheme"], capture_output=True, text=True).stdout
        return out.split("(", 1)[1].rsplit(")", 1)[0] if "(" in out else out.strip()
    except OSError:
        return "?"


if __name__ == "__main__":          # calibration: python -m tools.perf.load SECONDS
    m = LoadMonitor()
    m.start()
    time.sleep(float(sys.argv[1]) if len(sys.argv) > 1 else 60)
    print(m.stop(), snapshot())
