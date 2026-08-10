#!/usr/bin/env python3
"""Find query-coverage baseline clusters that name a node type the grammar no longer has.

WHY THIS EXISTS

`tools/query_coverage/baseline.json` is the one committed file that `qc run`
writes to on its own (the ratchet), and it is the file three parallel branches
all touch. Git will auto-merge it into something plausible that no run ever
produced -- the same failure mode as auto-merging `src/grammar.json`.

The ratchet cannot save you here. `run` lowers an accepted count when it
observes a smaller one, so a cluster for a node type that no longer exists just
sits at its accepted count forever, observed zero times, never contradicted.
Nothing else in the harness compares the baseline against the grammar.

WHAT IT CANNOT DO

It answers "does every node type named by a baseline key still exist?" It does
NOT answer "is every cluster that should exist present?" -- a cluster dropped by
a bad merge reappears as NEW on the next run and exits 1, which is the safe
direction and already covered.

USAGE

    python tools/check_baseline_types.py                 # repo defaults
    python tools/check_baseline_types.py BASELINE NODETYPES
    python tools/check_baseline_types.py --self-test     # prove it can fail

EXIT CODES

    0  every node type named by a baseline key exists
    1  at least one stale reference, or an unclassified key shape
    2  the check could not run (missing/empty/malformed input)

Exit 2 is deliberate and load-bearing: a checker that reports "no stale
clusters" because it parsed nothing is the exact fault shape this release has
been about. An empty baseline, an empty node-type set, or zero parsed keys is a
broken check, not a clean one.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASELINE = REPO_ROOT / "tools/query_coverage/baseline.json"
DEFAULT_NODE_TYPES = REPO_ROOT / "src/node-types.json"

# Node types tree-sitter synthesises that never appear in node-types.json.
# `source_file` IS in node-types.json; ERROR/MISSING are not, and detector 1's
# `enclosing_named_covering` can legitimately report ERROR.
SYNTHETIC_TYPES = frozenset({"ERROR", "MISSING"})

# Keys whose subject position is a sentinel word rather than a node type.
# Listed explicitly so a NEW sentinel shows up as unclassified instead of being
# silently waved through by a substring match.
KNOWN_NON_TYPE_KEYS = frozenset(
    {
        "fields|skipped|aliased-at-use-site",
        "fields|skipped|hidden-rule",
    }
)


def node_type_positions(key: str) -> list[tuple[str, bool]] | None:
    """The node types a cluster key names, or None if the shape is unrecognised.

    Each entry is (type, anonymous_ok). Shapes are detector-specific and NOT
    uniform -- do not try to generalise this into "the last part is a node
    type". Each is written out because getting one wrong silently skips a whole
    detector's keys:

      corpus|never-observed|<type>                -> [(type, named-only)]
      edges|edge|<parent>|<field>|<child>         -> [(parent, named-only),
                                                      (child, anonymous ok)]
      edges|field-never-populated|<type>|<field>  -> [(type, named-only)]
      fields|<type>|<field>                       -> [(type, named-only)]
      gaps|<gap_text>|<enclosing>                 -> [(enclosing, named-only)]
      shipped_queries|uncaptured|<type>           -> [(type, anonymous ok)]

    Two positions accept ANONYMOUS types, and both were found by running this
    against the real integration baseline rather than by reasoning about it:

      * An `edges` CHILD is routinely anonymous, because a field can hold a bare
        token -- `edges|edge|additive_expression|operator|+` is the operator
        field, and `+` is an anonymous type. Validating that position against
        named types alone reported nine perfectly healthy keys as stale.
      * `shipped_queries|uncaptured` covers keywords AND operator tokens, and
        the operators are anonymous.

    The `edges` PARENT stays named-only: an anonymous node has no fields, so it
    can never be the parent of an edge.

    `gaps` is the shape that bites on parsing rather than on kind. Its gap text
    can itself contain '|' -- the real key `gaps|||filter_value` is AL's filter
    alternation operator, not an empty field -- so the enclosing type is the
    LAST part and the gap text is everything between. Splitting on '|' with a
    fixed part count drops that key silently.
    """
    if key in KNOWN_NON_TYPE_KEYS:
        return []

    parts = key.split("|")
    detector = parts[0]
    NAMED_ONLY, ANON_OK = False, True

    if detector == "corpus" and len(parts) == 3 and parts[1] == "never-observed":
        return [(parts[2], NAMED_ONLY)]

    if detector == "edges":
        if len(parts) == 5 and parts[1] == "edge":
            return [(parts[2], NAMED_ONLY), (parts[4], ANON_OK)]  # parts[3] is a FIELD
        if len(parts) == 4 and parts[1] == "field-never-populated":
            return [(parts[2], NAMED_ONLY)]                       # parts[3] is a FIELD
        return None

    if detector == "fields" and len(parts) == 3:
        return [(parts[1], NAMED_ONLY)]                           # parts[2] is a FIELD

    if detector == "gaps" and len(parts) >= 3:
        return [(parts[-1], NAMED_ONLY)]                          # gap text may contain '|'

    if detector == "shipped_queries" and len(parts) == 3 and parts[1] == "uncaptured":
        return [(parts[2], ANON_OK)]

    return None


def load_counts(path: Path) -> dict:
    if not path.is_file():
        die(f"baseline not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        die(f"baseline is not valid JSON ({exc}) -- a bad merge leaves conflict markers here")
    counts = data.get("counts")
    if not isinstance(counts, dict):
        die(f"baseline has no 'counts' object: {path}")
    return counts


def load_types(path: Path) -> tuple[set[str], set[str]]:
    """(named, anonymous). Both are needed -- see node_type_positions."""
    if not path.is_file():
        die(f"node-types.json not found: {path}")
    try:
        entries = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        die(f"node-types.json is not valid JSON ({exc})")
    named = {e["type"] for e in entries if e.get("named")}
    anonymous = {e["type"] for e in entries if not e.get("named")}
    return named, anonymous


def die(message: str) -> None:
    print(f"check-baseline-types: CANNOT RUN -- {message}", file=sys.stderr)
    raise SystemExit(2)


def check(counts: dict, named: set[str], anonymous: set[str] = frozenset()) -> tuple[list, list, int]:
    """Pure classification pass. Returns (stale, unclassified, classified_count).

    Deliberately never exits: an unclassified key is a RESULT, not a crash, and
    an earlier version that died here could not be handed a single unknown key
    without taking the self-test down with it. The fatal conditions live in
    refuse_to_run_on_nothing(), which the real entry point calls and the
    self-test can exercise directly.
    """
    valid_named = named | SYNTHETIC_TYPES
    valid_any = valid_named | anonymous
    stale: list[tuple[str, str]] = []
    unclassified: list[str] = []
    classified = 0

    for key in sorted(counts):
        types = node_type_positions(key)
        if types is None:
            unclassified.append(key)
            continue
        classified += 1
        for node_type, anonymous_ok in types:
            if node_type not in (valid_any if anonymous_ok else valid_named):
                stale.append((key, node_type))

    return stale, unclassified, classified


def refuse_to_run_on_nothing(counts: dict, named: set[str], classified: int) -> None:
    """The three ways this check can look clean without having checked anything."""
    if not counts:
        die("baseline 'counts' is EMPTY -- refusing to report a clean check over nothing")
    if not named:
        die("node-types.json yielded NO named types -- run `tree-sitter generate`")
    if classified == 0:
        die(
            f"parsed {len(counts)} keys and classified NONE of them -- the key grammar "
            "has changed and this checker is blind to it"
        )


def report(counts: dict, named: set[str], anonymous: set[str] = frozenset()) -> int:
    stale, unclassified, classified = check(counts, named, anonymous)
    refuse_to_run_on_nothing(counts, named, classified)

    print(f"baseline clusters: {len(counts)}   grammar named types: {len(named)}")

    if unclassified:
        print(f"\nUNCLASSIFIED KEY SHAPES ({len(unclassified)}) -- not checked, treat as a failure:")
        for key in unclassified:
            print(f"  {key}")

    if stale:
        print(f"\nSTALE TYPE REFERENCES ({len(stale)}):")
        for key, node_type in stale:
            print(f"  {node_type!r} no longer exists, named by: {key}")

    if not stale and not unclassified:
        print("\nOK: every node type named by a baseline key exists in the grammar")
        return 0
    return 1


def self_test() -> int:
    """Prove the checker can fail. A checker nobody has seen fail is not a check."""
    named = {"real_type", "other_type"}
    anon = {"+", "<="}
    failures = []

    # 1. A stale key MUST be caught.
    stale, _, _ = check({"corpus|never-observed|deleted_type": 1}, named)
    if not stale:
        failures.append("stale corpus key was NOT caught")

    # 2. Control: a clean baseline must produce nothing, or the checker is a
    #    rubber stamp that always fires.
    stale, unclassified, _ = check({"corpus|never-observed|real_type": 1}, named)
    if stale or unclassified:
        failures.append(f"clean baseline produced findings: {stale} {unclassified}")

    # 3. Each detector shape must be classified, and the type position must be
    #    the one that is actually a node type -- not the field name beside it.
    cases = {
        "edges|edge|real_type|body|other_type": [],
        "edges|edge|real_type|body|deleted_type": ["deleted_type"],
        "edges|field-never-populated|real_type|body": [],
        "edges|field-never-populated|gone_type|body": ["gone_type"],
        "fields|real_type|operator": [],
        "fields|gone_type|operator": ["gone_type"],
        "gaps|<>|real_type": [],
        "gaps|||real_type": [],          # gap text is a literal '|'
        "gaps|||gone_type": ["gone_type"],
        "shipped_queries|uncaptured|gone_type": ["gone_type"],
        "fields|skipped|hidden-rule": [],
        # An edges CHILD may be anonymous -- the operator-field case that made
        # nine healthy keys on the real integration baseline look stale.
        "edges|edge|real_type|operator|+": [],
        "edges|edge|real_type|operator|~": ["~"],
        # ...but an edges PARENT may not: an anonymous node has no fields.
        "edges|edge|+|operator|other_type": ["+"],
        # uncaptured covers operator tokens, which are anonymous.
        "shipped_queries|uncaptured|<=": [],
    }
    for key, expected in cases.items():
        stale, unclassified, _ = check({key: 1}, named, anon)
        if unclassified:
            failures.append(f"{key!r} was not classified")
            continue
        got = [t for _, t in stale]
        if got != expected:
            failures.append(f"{key!r}: expected stale {expected}, got {got}")

    # 4. A field NAME must never be mistaken for a node type. 'body' is a field
    #    in three of the shapes above and is not in `named`; if any shape read
    #    the wrong position, case 3 would already have flagged it -- this makes
    #    the intent explicit.
    stale, _, _ = check({"edges|edge|real_type|not_a_type|other_type": 1}, named)
    if stale:
        failures.append(f"field-name position was checked as a node type: {stale}")

    # 5. Each way of checking nothing must be fatal, not clean. These print
    #    their CANNOT RUN line to stderr while running -- that noise is the
    #    test working, not the test failing.
    for label, args in (
        ("empty counts", ({}, named, 0)),
        ("empty node types", ({"corpus|never-observed|real_type": 1}, set(), 1)),
        ("nothing classified", ({"brandnew|shape": 1}, named, 0)),
    ):
        try:
            refuse_to_run_on_nothing(*args)
        except SystemExit as exc:
            if exc.code != 2:
                failures.append(f"{label}: expected exit 2, got {exc.code}")
        else:
            failures.append(f"{label}: did NOT fail")

    # 6. An unrecognised shape must be listed, never silently skipped -- and it
    #    must not take the classification pass down with it.
    _, unclassified, classified = check(
        {"brandnew|some|shape|here": 1, "corpus|never-observed|real_type": 1}, named
    )
    if not unclassified:
        failures.append("unknown key shape was silently skipped")
    if classified != 1:
        failures.append(f"expected 1 classified alongside the unknown shape, got {classified}")

    if failures:
        print("SELF-TEST FAILED:")
        for failure in failures:
            print(f"  {failure}")
        return 1
    print(f"self-test passed ({len(cases) + 5} cases): the checker fires on stale "
          "references, stays quiet on clean ones, and refuses empty input")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    baseline = Path(argv[0]) if len(argv) > 0 else DEFAULT_BASELINE
    node_types = Path(argv[1]) if len(argv) > 1 else DEFAULT_NODE_TYPES
    named, anonymous = load_types(node_types)
    return report(load_counts(baseline), named, anonymous)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
