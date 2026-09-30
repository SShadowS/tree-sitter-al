"""Native (py-tree-sitter, in-process) full-parse throughput and per-file latency."""
from __future__ import annotations

import os
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import shared_memory
from pathlib import Path

from tools.perf import common, stats

REPEATS = 3
CHUNK = 8          # files per task in the parallel run
SLOWEST = 10
MiB = 2 ** 20
# The known state (docs/deferred-work.md item 12): BCApps has 2 visible-error files
# (EDocumentDE, APAC ERMPurchaseReportsIII); the other corpora are clean.
KNOWN_HAS_ERROR = {"bc-history": 0, "dc": 0, "bc28.1": 0, "bcapps-29.0": 2}


def _throughput(seconds_runs, files, nbytes):
    return {"seconds": stats.spread(seconds_runs),
            "files_per_s": stats.spread([files / s for s in seconds_runs]),
            "mib_per_s": stats.spread([nbytes / MiB / s for s in seconds_runs])}


def single(parser, files):
    """Warm-up pass (discarded), then REPEATS passes. -> (per-file ns [repeat][file], has_error flags).
    Only the parse() call is timed, per file."""
    clock = time.perf_counter_ns
    errors = [parser.parse(src).root_node.has_error for _, _, src in files]   # warm-up
    runs = []
    for r in range(REPEATS):
        common.log(f"native single-threaded pass {r + 1}/{REPEATS}")
        ns = []
        for _, _, src in files:
            t = clock()
            tree = parser.parse(src)
            ns.append(clock() - t)
            del tree
        runs.append(ns)
    return runs, errors


# ---- parallel: workers read the corpus from one shared-memory block, so no I/O and no
# per-file pickling of the source is inside the timed region.
_W = {}


def _init(shm_name, offsets, lib):
    from tools.query_coverage import loader
    _W["shm"] = shared_memory.SharedMemory(name=shm_name, track=False)
    _W["off"] = offsets
    _W["parser"] = loader.make_parser(loader.load_language(Path(lib)))


def _parse_range(rng):
    buf, off, p = _W["shm"].buf, _W["off"], _W["parser"]
    return sum(p.parse(bytes(buf[off[i]:off[i + 1]])).root_node.has_error for i in range(*rng))


def _ready(_):
    time.sleep(0.5)
    return os.getpid()


def start_all(pool, workers):
    """Every worker spawned and initialised (library loaded) before anything is timed: the
    pool spawns lazily, and a spawn is ~0.5 s on Windows, which the first timed pass ate."""
    seen = set()
    while len(seen) < workers:
        seen |= set(pool.map(_ready, range(workers * 2)))


def parallel(pool, index_ranges):
    """One timed pass: wall time from dispatch until every chunk returned. -> (seconds, has_error count)."""
    t = time.perf_counter_ns()
    errors = sum(pool.map(_parse_range, index_ranges))
    return (time.perf_counter_ns() - t) / 1e9, errors


def _chunks(lo, hi):
    return [(i, min(i + CHUNK, hi)) for i in range(lo, hi, CHUNK)]


def measure(labels, workers=common.DEFAULT_WORKERS):
    files, read_s = common.load(labels)
    total_bytes = sum(len(s) for *_, s in files)
    common.log(f"native: {len(files)} files, {total_bytes / MiB:.1f} MiB read in {read_s:.2f} s")
    runs, errors = single(common.parser(), files)
    per_file_ms = [stats.median([runs[r][i] for r in range(REPEATS)]) / 1e6 for i in range(len(files))]

    spans, i = {}, 0      # label -> (lo, hi) index range; load() keeps corpora contiguous
    for label in labels:
        n = sum(1 for f in files if f[0] == label)
        spans[label] = (i, i + n)
        i += n
    spans["combined"] = (0, len(files))

    result = {"read_seconds": read_s, "repeats": REPEATS, "workers": workers, "chunk": CHUNK, "corpora": {}}
    for name, (lo, hi) in spans.items():
        sub = files[lo:hi]
        nbytes = sum(len(s) for *_, s in sub)
        err_ids = [f"{l}:{p}" for (l, p, _), e in zip(sub, errors[lo:hi]) if e]
        ms = per_file_ms[lo:hi]
        slow = sorted(range(lo, hi), key=lambda k: -per_file_ms[k])[:SLOWEST]
        result["corpora"][name] = {
            "files": hi - lo, "bytes": nbytes, "has_error": len(err_ids), "has_error_files": err_ids,
            "single": _throughput([sum(r[lo:hi]) / 1e9 for r in runs], hi - lo, nbytes),
            "latency_ms": stats.latency(ms),
            "slowest": [{"file": f"{files[k][0]}:{files[k][1]}", "bytes": len(files[k][2]),
                         "ms": round(per_file_ms[k], 3)} for k in slow],
        }

    for label in labels:
        got = result["corpora"][label]["has_error"]
        if got != KNOWN_HAS_ERROR.get(label, got):
            common.warn(f"{label}: {got} has_error files, the known state is {KNOWN_HAS_ERROR[label]}")

    blob = b"".join(s for *_, s in files)
    offsets = [0]
    for *_, s in files:
        offsets.append(offsets[-1] + len(s))
    shm = shared_memory.SharedMemory(create=True, size=max(1, len(blob)))
    try:
        shm.buf[:len(blob)] = blob
        del blob
        with ProcessPoolExecutor(workers, initializer=_init,
                                 initargs=(shm.name, offsets, str(common.library()))) as pool:
            start_all(pool, workers)
            for name, (lo, hi) in spans.items():
                entry, ranges = result["corpora"][name], _chunks(lo, hi)
                parallel(pool, ranges)                              # warm-up
                secs = []
                for r in range(REPEATS):
                    common.log(f"native {workers}-process pass {r + 1}/{REPEATS}: {name}")
                    s, e = parallel(pool, ranges)
                    if e != entry["has_error"]:
                        raise RuntimeError(f"{name}: parallel has_error {e} != single-threaded {entry['has_error']}")
                    secs.append(s)
                entry["parallel"] = _throughput(secs, entry["files"], entry["bytes"])
    finally:
        shm.close()
        shm.unlink()
    return result
