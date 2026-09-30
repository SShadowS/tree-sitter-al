"""Same-session, interleaved A/B timing of two native grammar libraries: the decision-grade
speed comparison (roadmap D1).

    python -m tools.perf ab --lib-a PATH --lib-b PATH [--corpus LABEL ...] [--rounds N]

Why not compare two baselines: single-threaded figures drifted ~30% between sessions on this
machine with clean load readings, and CCD placement alone moved a DC pass ~12%. A ratio of two
libraries measured in the SAME process, on the SAME pinned CPU, interleaved A,B,B,A,A,B,...
cancels both: a drift during the run hits A and B alike, and the ABBA order cancels a linear
trend within each pair of rounds.

Before any timing, both libraries parse every file and the complete cursor-derived trees
(tools/perf/incremental.rows: every node, named and anonymous, type, grammar symbol, fields,
spans, has_error) must be identical, or the run exits 1: a speed ratio between parsers that
build different trees answers nothing.
"""
from __future__ import annotations

import hashlib
import random
import time
from pathlib import Path

from tools.perf import common, stats


def schedule(rounds):
    """ABBA interleaving: round r runs A then B when r is even, B then A when odd."""
    out = []
    for r in range(rounds):
        out += ["A", "B"] if r % 2 == 0 else ["B", "A"]
    return out


def ratios(order, seconds):
    """Per round, time_A / time_B (>1: B is faster). `order` is schedule(); `seconds` the pass
    times in the same order."""
    if len(order) != len(seconds) or len(order) % 2:
        raise ValueError("one time per scheduled pass, two passes per round")
    out = []
    for i in range(0, len(order), 2):
        t = dict(zip(order[i:i + 2], seconds[i:i + 2]))
        out.append(t["A"] / t["B"])
    return out


def bootstrap_ci(values, level=0.95, resamples=4000, seed=0):
    """Percentile bootstrap CI of the MEDIAN; deterministic (seeded)."""
    rng = random.Random(seed)
    meds = sorted(stats.median([rng.choice(values) for _ in values]) for _ in range(resamples))
    lo = meds[int((1 - level) / 2 * resamples)]
    hi = meds[min(resamples - 1, int((1 + level) / 2 * resamples))]
    return lo, hi


def trees_identical(pa, pb, files):
    """-> [differing file ids] (empty when every tree is identical)."""
    from tools.perf import incremental
    bad = []
    for label, rel, src in files:
        if incremental.rows(pa.parse(src)) != incremental.rows(pb.parse(src)):
            bad.append(f"{label}:{rel}")
    return bad


def _lib_info(path):
    from tools.perf import procs
    p = Path(path)
    return {"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "pe_linker_version": procs._pe_linker_version(p)}


def run(lib_a, lib_b, labels, rounds=8):
    from tools.perf import pin
    from tools.query_coverage import loader
    files, _ = common.load(labels)
    pa = loader.make_parser(loader.load_language(Path(lib_a)))
    pb = loader.make_parser(loader.load_language(Path(lib_b)))
    common.log(f"ab: checking that both libraries build identical trees on {len(files)} files")
    differ = trees_identical(pa, pb, files)
    result = {"lib_a": _lib_info(lib_a), "lib_b": _lib_info(lib_b), "corpora": list(labels),
              "files": len(files), "bytes": sum(len(s) for *_, s in files),
              "trees_identical": not differ, "differing_files": differ[:50]}
    if differ:
        common.warn(f"ab: {len(differ)} files parse differently; no timing (a ratio would be meaningless)")
        return result
    order = schedule(rounds)
    parsers = {"A": pa, "B": pb}
    secs = []
    with pin.Pinned() as p:
        for who in ("A", "B"):                                    # warm-up, discarded
            for *_, s in files:
                parsers[who].parse(s)
        for i, who in enumerate(order):
            common.log(f"ab: pass {i + 1}/{len(order)} ({who})")
            parser, t = parsers[who], time.perf_counter_ns()
            for *_, s in files:
                parser.parse(s)
            secs.append((time.perf_counter_ns() - t) / 1e9)
            p.note()
    r = ratios(order, secs)
    lo, hi = bootstrap_ci(r)
    result.update({
        "rounds": rounds, "order": "".join(order), "pin": p.record(),
        "seconds": {"A": [s for w, s in zip(order, secs) if w == "A"], "B": [s for w, s in zip(order, secs) if w == "B"]},
        "ratio_a_over_b": {"median": stats.median(r), "min": min(r), "max": max(r), "runs": r,
                           "ci95_median": [lo, hi], "ci_method": "percentile bootstrap of the median, 4000 resamples, seed 0"},
    })
    return result
