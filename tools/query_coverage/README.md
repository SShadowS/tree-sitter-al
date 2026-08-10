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

## Not concurrency-safe

**Never run two `qc` invocations at once, and never run one alongside
`./validate-grammar.sh`** — its Step 5d runs a manifest-scope `qc`. Every invocation shares
one `reports/` directory and one `baseline.json`, and nothing detects the collision or warns
you. Both runs complete and both print plausible results; neither is trustworthy.

This has already happened once: a full-corpus run was backgrounded and `validate-grammar.sh`
started while it was in flight. Both outputs were discarded and the gates re-run serially.
If you are unsure whether a result was taken cleanly, it was not — re-run it.

`python tools/gate_selftest.py` is a third caller to keep out of the way: most of
its cases run `validate-grammar.sh` end to end, so each one reaches Step 5d. It
runs its cases **serially**, and each runs inside its own scratch copy of the
repo, so `reports/` and `baseline.json` resolve to that copy and the real ones
are never touched — but do not start it alongside a `qc` run of your own. In CI
and in scratch there is no `BC.History`, so Step 5d exits 2 and warns rather than
running the corpus gate at all.

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
7. **corpus** — named node types still declared in `src/node-types.json` that no file in
   this run's scope produced. Catches a type the grammar still declares but that stops
   being emitted anywhere in the corpus, with byte coverage staying intact. Detector 1
   cannot see this: it works from byte coverage, and a type going unproduced says nothing
   about which bytes are covered. See "Known limitations" for two cases that look like
   this trigger but produce zero corpus findings.

## Self-tests

A first `run --all` must report:

- gap clusters for `:=`, `record`, `field`, `tabledata`
- dropped `operator` fields on `assignment_statement`, `assignment_expression`,
  `is_expression`, `as_expression`
- dropped-field findings on `xmlport_attribute` (`attribute_type`) and
  `xmlport_element` (`element_type`)

If any is missing, the detector is broken — not the grammar.

## Known limitations

Not caught by any detector: precedence and associativity misparses inside
expressions (`a + b * c` grouped wrongly covers every byte correctly), and
scanner over-consumption where a string or comment token swallows adjacent
code. Wrong-parent attachment is caught only when the misparse also changes
a node's type along the way — detector 4 catches the `case`/dangling-`else`
mis-association this way, because that misparse degrades a keyword into a
plain `identifier`. Attachment errors that preserve every node's type and
every byte's span are not caught by anything here; closing those needs
structural assertions against expected trees, which is what `test/corpus/`
provides.

Detector 3's dynamic half is narrower than "every field": it flags a
`required: true` field returning `None` on a real instance, which is 241 of
the 392 field declarations in `src/node-types.json`. An *optional* field
whose content is a `choice()` mixing visible and hidden alternatives passes
the static check (its name is present in `node-types.json`) and is never
examined by the dynamic one — that is the majority of the grammar's fields.

A named node type that stops being produced by anything in the corpus while
staying declared in `src/node-types.json` is caught by the **corpus**
detector. It works only for types this run's scope actually exercises: the
manifest covers 357 of 391 named types, and the other 34 are already
never-observed (dead grammar or genuinely uncovered constructs) and stay
that way regardless of what changes — see `reports/never-observed.json`.

Two things that look like this trigger but are not caught by it:

- **A keyword rule losing its `alias()` and reverting to a bare `kw()`
  pattern.** Per the keyword-shape table in `CLAUDE.md`, a bare `kw('word')`
  inside a named rule still yields a childless leaf — `(x_keyword)` is still
  produced and still matches; only `(x_keyword "word")` patterns go dark.
  This produces zero corpus findings.
- **A rule inlined to a bare string literal.** The type then leaves
  `node-types.json` too, so `never_observed` no longer iterates it and no
  finding is possible. This is caught only incidentally, and only for a type
  a shipped `.scm` names by hand (e.g. `queries/highlights.scm` has
  `(begin_keyword)`): `tree_sitter.Query` raises `QueryError: Invalid node
  type` for an unknown type, so `qc run` dies on an uncaught traceback
  rather than reporting a finding. A type absent from every `.scm` is not
  caught at all.

The historical `begin`/`end` dropped-inside-`#if` bug is not an instance of
either case above: `begin_keyword` was still emitted at depth 0, so it was
never in the never-observed set. That bug is detector 1's byte-gap catch.

The `field(` anchor is deliberately excluded from detector 5 — see
"Coverage deliberately not checked" in `reports/summary.md` for the live list
and reasons, sourced from `EXCLUDED_ANCHORS` in `anchors.py`.

## Validation gate

`validate-grammar.sh` runs `qc run` whenever `tools/query_coverage/baseline.json`
exists — which is every clone, since the baseline is a tracked, committed
file. The corpus it runs against (`BC.History`) is not committed, so the step
reads `qc run`'s exit code rather than treating any failure the same way.
Exit 2 covers four distinct causes (see "Exit codes" above and `qc.py`): a
missing or drifted corpus file, a manifest that can't be found, `--full-corpus`
without `--all`, and a baseline accepted under a different manifest (stale
`select` without a follow-up `accept`). Only the first is "nothing to check
here", so the step warns and skips on exit 2 only when `BC.History` is
entirely absent — with the directory present, exit 2 fails validation the
same as exit 1, because it means something is genuinely wrong rather than
uncloned. A fresh clone without `BC.History` validates cleanly; a clone with
a drifted corpus, a partial corpus, or a stale baseline is not silently
passed.
