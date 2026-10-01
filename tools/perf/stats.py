"""The statistics every perf number is reduced with. Kept separate so the tests can pin them."""
from __future__ import annotations

import math


def percentile(values, q):
    """The q-th percentile (0..100) by linear interpolation between closest ranks: numpy's
    default ("linear", Hyndman-Fan type 7). p0 is the min, p100 the max. Empty input raises."""
    xs = sorted(values)
    if not xs:
        raise ValueError("percentile of no values")
    if not 0 <= q <= 100:
        raise ValueError(f"percentile out of range: {q}")
    pos = (len(xs) - 1) * q / 100
    lo = math.floor(pos)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def median(values):
    return percentile(values, 50)


def spread(runs):
    """{median, min, max, runs} of repeated measurements of one quantity."""
    runs = list(runs)
    return {"median": median(runs), "min": min(runs), "max": max(runs), "runs": runs}


def latency(ms):
    """Per-file latency summary, in milliseconds."""
    return {f"p{q}": percentile(ms, q) for q in (50, 95, 99)} | {"max": max(ms), "mean": sum(ms) / len(ms)}
