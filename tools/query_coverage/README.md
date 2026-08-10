# Query-Coverage Harness

Proves the AL parse tree is lossless over the source and that values are
reachable through queries. Complements the existing gates rather than
replacing them: `parse-al-parallel.sh` counts errors, `tools/tree-harness.sh`
proves a refactor changed no tree, `tree-sitter test` pins hand-written trees.
None of those can see a token that was lexed and then dropped.

Design: `docs/superpowers/specs/2026-08-09-query-coverage-harness-design.md`

## Commands

```
$ python -m tools.query_coverage.qc select      # rebuild manifest.tsv by set-cover
$ python -m tools.query_coverage.qc run         # detectors + baseline diff
$ python -m tools.query_coverage.qc run --all   # full picture, always exits 0
$ python -m tools.query_coverage.qc accept      # promote the current report to baseline
```

Dead-pattern detection defaults to the manifest subset. Add `--full-query-scan`
to tally over all 15,358 files, which is the scope the design calls for — the
subset can miss a pattern kept alive by a construct set-cover happened to pick
up from one file. Every run prints which scope it used.

`select` re-derives the manifest from scratch via set-cover over `BC.History`
(~52s); `run` over the resulting 59-file manifest takes ~11.5s. The manifest
covers 357 of the grammar's 391 named node types — the other 34 appear in no
corpus file and are listed in `reports/never-observed.json`.

`run --full-corpus` (combined with `--all`) sweeps every file under
`BC.History` through every detector, not just the dead-pattern tally — a
30m52s run producing 925,562 findings in 204 clusters the last time it ran.
Its counts are not comparable to the manifest baseline (59 files vs.
15,358), so `run` refuses `--full-corpus` without `--all`, and `accept`
refuses a `--full-corpus` report outright — a full sweep can only inform,
never contaminate the baseline.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | No new cluster, no cluster above its ratcheted count |
| 1 | Regression: new cluster, or count above the ratchet |
| 2 | Corpus broken: a manifest file is missing or its sha256 drifted |
| 3 | Stale parser: the build stamp does not match grammar.js + src/scanner.c |

`run --all` always exits 0 regardless of findings — it is the reporting mode,
not the gate.

## The baseline ratchets

`run` lowers an accepted count whenever it observes a smaller one, and prints
every ratchet it applies. This is the one place `run` modifies a committed
file — `tools/query_coverage/baseline.json`. Without it, a cluster fixed to 0
and later regressed to below its accepted count would pass silently. `accept`
is the only way to raise a count or admit a new cluster. This means a clean
`git status` after a successful `run` is not guaranteed: a modified
`baseline.json` is the harness doing its job, not a bug.

## Output

- `reports/findings.jsonl` — provenance header, then one finding per line,
  stably sorted. This is the LLM-facing artifact.
- `reports/summary.md` — clusters with counts and up to three examples each.
- `reports/never-observed.json` — named node types the corpus never produced.

## Detectors

1. **gaps** — non-whitespace source bytes covered by no leaf node.
2. **errors** — ERROR and MISSING census with context.
3. **fields** — declared fields absent from the node type (static), and
   required fields returning `None` on an instance (dynamic).
4. **reserved** — a hard-reserved word appearing as a plain identifier.
5. **anchors** — lexical anchor counts versus node counts, via an independent lexer.
6. **shipped_queries** — keyword capture coverage and fully-dead patterns. Informational
   — excluded from the exit code (see `INFORMATIONAL_DETECTORS` in `qc.py`) because it
   was written for editor highlighting, not exhaustive extraction, so a gap in it is a
   note, not a regression.

## Self-tests

A first `run --all` must report:

- gap clusters for `:=`, `record`, `field`, `tabledata`
- dropped `operator` fields on `assignment_statement`, `assignment_expression`,
  `is_expression`, `as_expression`
- dropped-field findings on `xmlport_attribute` (`attribute_type`) and
  `xmlport_element` (`element_type`)

If any is missing, the detector is broken — not the grammar.

## Known limitations

Not caught by any detector: wrong-parent attachment with correct spans,
precedence and associativity misparses inside expressions, and scanner
over-consumption where a string or comment token swallows code. Closing those
needs structural assertions against expected trees, which is what
`test/corpus/` provides.

The `field(` anchor is deliberately excluded from detector 5 — see
"Coverage deliberately not checked" in `reports/summary.md` for the live list
and reasons, sourced from `EXCLUDED_ANCHORS` in `anchors.py`.

## Validation gate

`validate-grammar.sh` runs `qc run` whenever `tools/query_coverage/baseline.json`
exists — which is every clone, since the baseline is a tracked, committed
file. The corpus it runs against (`BC.History`) is not committed, so the step
reads `qc run`'s exit code rather than treating any failure the same way:
exit 0 passes, exit 2 ("corpus broken" — `BC.History` missing or drifted)
prints a warning and skips, and anything else (a real regression) fails
validation. A fresh clone without `BC.History` validates cleanly; a clone
with a drifted or partial corpus is warned, not silently passed and not
hard-failed.
