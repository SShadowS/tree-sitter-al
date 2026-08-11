# The query-coverage harness (`tools/query_coverage/`)

Proves the CST is lossless over the source and that values are reachable by query.
Complements the other gates: `parse-al-parallel.sh` counts errors, `tree-harness.sh`
proves a refactor changed no tree, `tree-sitter test` pins hand-written trees. None of
those can see a token that was lexed and then dropped.

`tools/query_coverage/README.md` is the living document. This memory records the
semantics that are easy to get wrong.

## Two scopes — never mix their numbers

- **manifest** (59 files, chosen by set-cover over node types) — this is **the gate**.
  Far denser in constructs per file than real code; absolute counts do not scale.
- **`--full-corpus`** (15,358 files) — a **reporting** pass, not a gate. `cmd_run` sets
  an empty `Diff()` and `--all` forces exit 0. `accept` refuses a full-corpus report
  outright. Exit 0 there means "it ran", not "no regressions".

Always state which scope a figure came from.

## Baseline semantics

`baseline.json` **ratchets**: `run` lowers an accepted count whenever it observes a
smaller one and prints that it did. `accept` is the only way to raise a count or admit a
new cluster. So a modified `baseline.json` after a successful run is the harness working.

Failure directions are asymmetric: accepted-too-high is silently ratcheted down;
accepted-too-low exceeds the observation and exits 1, loudly. The dangerous case is a
baseline **committed without a run in between**.

## Concurrency

**Never run two `qc` invocations at once, and never one alongside `validate-grammar.sh`**
— its Step 5d runs a manifest-scope `qc`. All share one `reports/` and one
`baseline.json`; nothing detects the collision. Both complete, both print plausible
results, neither is trustworthy. `tools/gate_selftest.py` is a third caller.

## Exit codes

0 clean · 1 regression · 2 corpus broken / manifest missing / `--full-corpus` without
`--all` / baseline accepted under a different manifest · 3 stale parser (build stamp
mismatch).

## What it cannot see

- Precedence and associativity misparses — every byte is still covered.
- Wrong-parent attachment that preserves node types and byte spans. The `(parent, field,
  child)` edge census (detector 8) makes these **visible and diffable**, but gates them
  only where the 59-file manifest happens to exercise the edge kind — it produces 642 of
  the corpus's 920 kinds, and **none of the three 4.0.0 precedence defects would have
  tripped the manifest-scope gate**. Closing that means set-covering `qc select` over
  edge kinds rather than node types, which forces a full re-`accept`.
- A keyword rule reverting from `alias(kw())` to bare `kw()` inside a named rule — the
  node is still produced, only `(x_keyword "word")` patterns go dark.
- One node type carrying two shapes because a `choice()` mixes aliased and bare
  alternatives — the bytes are covered either way.

## Detector unit tests

`tools/query_coverage/tests/` historically pinned the grammar's own defects as fixtures
(`test_hidden_type_keywords_are_gaps`, `test_finds_the_known_dropped_operator_fields`).
Those fail the moment the defect is fixed, and a detector that can only prove itself
while the grammar is broken cannot prove itself afterwards. Assert against synthetic
input; keep one genuine end-to-end case.
