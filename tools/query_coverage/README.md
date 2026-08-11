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
covers **377 of the grammar's 421** named node types — the other 44 appear in
no corpus file, are listed in `reports/never-observed.json`, and are carried in
`baseline.json` as `corpus|never-observed|*` clusters. (This read 357/391/34
until 4.0.0. Named `*_keyword` types went 84 → 111 over the defect fixes, which
is most of the growth; 10 of the 44 never-observed entries are keyword types for
constructs no BC.History file writes — `testpage_keyword`, `public_keyword`,
`upperlimit_keyword` and 7 others.)

`run --full-corpus` (combined with `--all`) sweeps every file under
`BC.History` through every detector, not just the dead-pattern tally. It cost
30m52s until `81ab477` and was measured at **407 s** after it. A run on this
branch reported 233 clusters across all detectors over all 15,358 files
(`terminator-report.md`); a later census of detector 1 alone put its own share
at 574,694 findings in 164 clusters (`a316d8e`).

Its counts are not comparable to the manifest baseline (59 files vs. 15,358),
so `run` refuses `--full-corpus` without `--all`, and `accept` refuses a
`--full-corpus` report outright — a full sweep can only inform, never
contaminate the baseline. **Always state which scope a figure came from.** The
manifest is chosen by set-cover to hit every node type at least once, so it is
far denser in constructs per file than real code and its absolute counts do not
scale: `baseline.json`'s 3,895 byte-gap findings are 574,694 at corpus scope,
~147x, and `a316d8e` exists because that manifest number was published as the
parser's.

It is also a **reporting** pass, not a gate: `cmd_run` sets an empty `Diff()`
on that branch, so exit 0 from `--full-corpus` means "it ran", not "no
regressions". The gating run is the 59-file manifest one.

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
| 3 | Stale parser: the build stamp does not match `loader.STAMPED_FILES` |

The stamp covers `grammar.js` and `src/scanner.c` (what the library is built
from) **and** `src/parser.c`, `src/grammar.json`, `src/node-types.json` (what
it is generated into). The last two are read directly by detectors 3 and 7, so
a stale generated artifact would otherwise change findings while the freshness
check passed. `ensure_library` runs `tree-sitter generate` before building and
stamps the post-generate state, so the stamp always describes what is on disk.

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
- `reports/summary.md` — clusters with counts and up to three examples each,
  then two sections that exist so the harness cannot check nothing quietly:
  "Coverage deliberately not checked" (the excluded anchors, from
  `anchors.EXCLUDED_ANCHORS`) and "Checks that are vacuous by construction"
  (checks that run but cannot currently emit a finding, from
  `inventory.inert_checks`). Both are derived, so neither can go stale
  against the code.
- `reports/never-observed.json` — named node types the corpus never produced.
- `reports/edge-census.json` — the full `{(parent, field, child): instance count}`
  map from detector 8, plus the scope and file count it was taken at. Not part
  of the gate; it is the artifact you diff before and after a refactor to prove
  edge-for-edge that only what you intended moved. Both sides must be taken at
  the same scope — a manifest census and a corpus census are not comparable.

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
8. **edges** — the `(parent, field, child)` edge census. Every other detector asks a
   question about nodes; this one asks which node is attached to which parent through
   which field. Two categories: `edge-kind` (one finding per distinct edge kind observed
   — a NEW kind is a node attached somewhere it never was) and `field-never-populated`
   (a declared `(parent, field)` that nothing in scope populated, while the parent type
   itself was produced — the disappearance half, needed because `baseline.diff` treats a
   vanished cluster as `fixed` and exits 0).

   Why it exists: a wrong-parent attachment can preserve every node's type and every
   byte's span, and detectors 1, 2, 5 and 7 are all structurally blind to that. The three
   precedence fixes on this branch are the proof — they rewrote 636 trees across
   BC.History, and the census recorded **13,339,003 fielded edges on both sides with
   `node_types: 0 changed`**. Every node type kept its exact count while 48 edge kinds
   moved.

   Cardinality is a fingerprint set, never per instance: 920 kinds over 13.3M edges at
   corpus scope, 642 at manifest scope. Per-instance would emit millions of findings.
   Cost measured on a full-corpus run: **423s before, 445s after (+22s, +5.2%)**.

## Self-tests

**`run --all` reports no `gaps` cluster and no dropped field at all, and that
is the correct result.** Measured on 4.0.0, each at its own scope — not
inferred from the baseline's key list, which is a different statement and
settles nothing:

- **manifest scope (59 files), the `run --all` default** — no `gaps` cluster.
- **corpus scope (15,358 files)** — detector 1 returns **0 findings over 0
  dropped bytes**. The manifest result does not imply this one; it was swept
  separately.
- **detector 3's static half** — **0** `dropped-field` findings. This one has
  no file scope at all: it reads `src/grammar.json` and `src/node-types.json`,
  so it covers every rule in the grammar regardless of what any corpus
  exercises.

So this section can no longer be a list of findings you should see. It was one
for three releases, and each release invalidated it:

| required by the list | closed by |
|---|---|
| `:=` gap; `operator` on `assignment_statement`/`assignment_expression` | `37771f1` |
| `xmlport_attribute`/`xmlport_element` dropped fields | `8c23096` |
| `record`, `field`, `code`, `tabledata` gaps; `operator` on `is_expression`/`as_expression` | the 4.0.0 losslessness work |

Each time, the list was trimmed to whatever defect was still open. That is a
loop with one exit, and 4.0.0 reached it: **there is no live finding left to
point at.** The version of this section that preceded it had already made the
argument against itself — it explained that requiring an already-fixed defect
"would report a correct grammar as a broken detector", then kept
`is_expression`/`as_expression` on the grounds that they were "deliberately
untouched". They were named in 4.0.0 and both went 1 → 0, so that
justification is void rather than merely stale. Do not re-point this list at
the next open defect; there may not be one, and the exercise is what produced
three wrong sections in a row.

### What actually distinguishes a working detector from a silent one

`python -m pytest tools/query_coverage/tests -q`

The positive controls live there, built as synthetic input rather than
borrowed from the grammar, so they hold whether or not any real AL construct
still drops a token:

| control | proves |
|---|---|
| `test_fields.py::test_finds_a_dropped_field_that_shares_its_name_with_a_surviving_one` | detector 3 still finds a dropped field, per owning type — a set-level rewrite returns zero here |
| `test_fields.py::test_set_level_check_would_miss_the_dropped_field` | the mis-implementation, run rather than described, and required to disagree |
| `test_gaps.py::test_dropped_token_survives_a_chunk_straddling_an_error_edge` | detector 1 still reports a gap, and `_split_by_errors` still beats blanket suppression |
| `test_gaps.py::test_dropped_token_between_two_error_ranges_survives_both_subtractions` | the multi-interval subtraction path |

The ratchets in the same files are the other half — `test_gaps.py::test_type_keywords_are_no_longer_gaps`, `::test_tabledata_keyword_is_no_longer_a_gap`,
`test_fields.py::test_the_real_grammar_drops_no_fields_at_all`. Each asserts
both that the defect is gone *and* that the construct is present as a real
node, because "no finding" alone also passes on a detector that reports
nothing. Neither half is worth much alone; a green suite means both hold.

**`./validate-grammar.sh` does not run pytest.** Only CI's
`query-coverage-selftest` job does (`.github/workflows/ci.yml`). A green
`validate-grammar.sh` is therefore not evidence about any of the above — that
gap is how the three superseded lists above all reached `main`.

The living version of the accepted state is
`tools/query_coverage/baseline.json`, which is diffed on every run. Prefer it
over this prose whenever the two disagree.

## Known limitations

**Still not caught by any detector: scanner over-consumption**, where a string
or comment token swallows adjacent code.

**Precedence and associativity misparses are still not caught here either**, and
that is worth stating precisely rather than crossing off. Three real ones were
found on this branch (`a171c19`, `d4e8433`, `168c5ec`) — `..` binding tighter
than `+`, unary binding looser than `*`, and the comparison operators binding
tighter than `and`/`or`/`xor` when AL is the exact inverse. **Every gate in this
repo reported success the whole time**, including this harness: byte coverage
was complete, the error count was 0/15,358, and no node type changed. They were
found by differential probes against `alc`, not by anything here, and nothing
here would find the next one. What detector 8 *does* give is the ability to see
the blast radius once you suspect one — see below.

**Wrong-parent attachment is now partly covered, by detector 8.** It was
previously caught only when the misparse also changed a node's type along the
way (detector 4 catches the `case`/dangling-`else` mis-association that way,
because that misparse degrades a keyword into a plain `identifier`). Detector 8
adds two specific signals that need no type change and no byte movement:

- a node attached through an edge kind that has **never** existed before
  (`edge-kind`, a NEW cluster), and
- a declared field that **stops being populated anywhere** in scope
  (`field-never-populated`, also a NEW cluster).

**The gate only sees 70% of the field graph, and that limit is bigger than the
detector's own.** The gating scope is the 59-file manifest, which produces 642
of the corpus's 920 edge kinds — **278 kinds are invisible to `qc run`**. The
manifest is chosen by set-cover over node *types*, so it guarantees every type
appears at least once and guarantees nothing at all about attachment variety.

Measured consequence, stated plainly: **none of the three precedence defects
fixed on this branch would have tripped the manifest-scope gate.** All five edge
kinds their fixes created —

```
range_expression|left|unary_expression
range_expression|left|additive_expression
range_expression|right|additive_expression
multiplicative_expression|left|unary_expression
comparison_expression|left|logical_expression
```

— are absent from the manifest. `-a * b` and `a = b and c` simply do not occur
in those 59 files. Detector 8 saw all three clearly at **corpus** scope, which
is a reporting pass and never gates. So the honest claim is: detector 8 makes
attachment regressions *visible and diffable*, and gates them only where the
manifest happens to exercise the edge kind.

Closing that would mean teaching `qc select` to set-cover over edge kinds rather
than node types. That is a real change with a real cost — a different manifest,
a different `manifest_hash`, and a full re-`accept` of every detector's counts —
so it is written down here rather than done quietly mid-release.

What detector 8 does **not** catch at any scope: an edge moving between two kinds
that both already exist elsewhere, where the source field also stays populated by
other nodes. Nothing about the kind set or the field set changes, so neither
category fires. Catching that requires per-kind *counts* in the gate, which
cannot be expressed as cluster counts without one finding per instance —
millions of them.
`reports/edge-census.json` exists for exactly that case: it carries the full
`{kind: count}` map, so a refactor can be proved edge-for-edge by taking it
before and after and diffing, without turning every intentional tree change into
a build failure. That is how the three precedence fixes were bounded to exactly
4, 629 and 3 sites, and how the terminator restructure was proved to have moved
exactly 25 edges.

Structural assertions against expected trees — `test/corpus/` — remain the only
thing that pins a specific tree shape.

Detector 3's dynamic half is narrower than "every field": it flags a
`required: true` field returning `None` on a real instance, which is 245 of the
396 field declarations in `src/node-types.json`. The other **151 (38%) are
optional** and its dynamic half never examines them — an optional field whose
content is a `choice()` mixing visible and hidden alternatives passes the static
check (its name is present in `node-types.json`) and is never looked at again.
(This paragraph used to say those 151 were "the majority of the grammar's
fields". They are a substantial minority: 151 of 396.)

**Detector 8's `field-never-populated` covers that gap from the other side**, and
it covers all 396 rather than only the optional ones. `None` on an optional field
is legal for any single instance — that is what optional means — so the naive
per-instance check would be all false positives. The corpus-wide question is not
naive: a field that is **never once populated** while its parent type IS produced
is either dead grammar or a hidden-token bug, and it is one finding per field
rather than one per node. Measured over all 15,358 files, **37 of the 396
declared fields are never populated, and 33 of those belong to node types that
never appear at all** (already detector 7's finding, so detector 8 suppresses
them). **Four remain, all of them optional:**

| field | declared children |
|---|---|
| `fieldgroup_declaration.body` | `declaration_body` |
| `interface_declaration.access_value` | `identifier`, `internal_keyword`, `public_keyword` |
| `preproc_split_declaration.base_object` | `identifier`, `quoted_identifier` |
| `preproc_split_if_statement.else_branch` | 54 statement/expression types |

These are **reported, not fixed** — each is a grammar change to be sequenced
deliberately. Note this is exactly the shape of release defects 4 and 5
(`area_section.type`, `action_area_section.type`), where a rare `$.identifier`
fallback kept a field declared while every real instance read `None`. Those two
were caught only because they are `required: true`; the same defect on any of
these four would have been invisible.

At manifest scope the same check reports 13 rather than 4, because a 59-file
sample legitimately fails to exercise some constructs. The 4 is the corpus-scope
number and is the one to act on; run `qc run --all --full-corpus` to reproduce it.

A named node type that stops being produced by anything in the corpus while
staying declared in `src/node-types.json` is caught by the **corpus**
detector. It works only for types this run's scope actually exercises: the
manifest covers 377 of 421 named types, and the other 44 are already
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
