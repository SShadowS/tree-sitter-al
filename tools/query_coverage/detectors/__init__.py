"""Detector registry.

`PER_FILE` entries are pure functions of (tree, source, path) — one file in,
findings for that file out.

`RUN_LEVEL` entries cannot have that shape, because their finding is a property
of the whole run rather than of any one file. They are accumulate-then-report:
qc.cmd_run builds the accumulator once, feeds it every tree inside the single
streaming pass, and calls the reporter after the loop. `shipped_queries` already
worked this way (QueryTally + detect_dead); `edges` is registered here so the
registry names every detector rather than only the ones whose signature happens
to fit.
"""

from . import anchor_counts, edges, errors, gaps, reserved

PER_FILE = (
    ("gaps", gaps.detect),
    ("errors", errors.detect),
    ("reserved", reserved.detect),
    ("anchors", anchor_counts.detect),
)

# (name, accumulator factory, reporter). The reporter's second argument is
# src/node-types.json, which is what the declared universe is read from.
RUN_LEVEL = (
    ("edges", edges.EdgeCensus, edges.detect),
)
