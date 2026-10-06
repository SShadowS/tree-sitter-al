# B7a: the separator and continuation audit (design)

Roadmap row B7, first sub-project (user decision 2026-10-06: audit first, then one bounded fix per host
family, ordered by this audit's matrix). Deferred-work items 1, 2, 30 and 39 feed it. Status: design,
awaiting review.

## 1. Why

`812ace7` (4.0.0) made comma-separated lists a sequence of runs with `#if` groups between them, so an arm
can supply the separator its neighbour lacks. An audit then listed 26 separator sites and six positions
without a preprocessor host (deferred-work item 1). That list was never re-verified, item 2 showed that a
rule existing is not the same as a shape being covered (`X, #if FOO Y #endif` parses, `X #if FOO , Y
#endif` ERRORs), and B6 added two valid split shapes that are loud ERRORs because their hosts have no
continuation (item 39). Fixing hosts from a stale hand list repeats the 4.0.0 mistake: the fix order,
and which hosts exist at all, must come from a complete, reproducible measurement.

B7a measures. It changes no grammar rule.

## 2. Goals and non-goals

Goals:
- A complete census of every separator site and every expression slot in the grammar, derived from
  `src/grammar.json`, so completeness is checked, not asserted.
- For each site, the `#if` placements that matter, each judged by alc (split and flat) and by the parser
  (has_error and, for clean parses, the config oracle).
- A generated, committed matrix that ranks the fix sub-projects (B7b onward).
- A gate that fails when the grammar gains a site the registry does not classify.

Non-goals: fixing any host (B7b+); deciding a host's tree shape; validating non-`#if` separator syntax
beyond what item 30 (trailing comma) already raises.

## 3. Census

`tools/b7_audit/census.py` reads `src/grammar.json` and emits two lists, each key stable across
regenerations:

- **Separator sites.** Every `STRING` `,` or `;` inside a `REPEAT`/`REPEAT1`, keyed `(rule, path)` where
  `path` is the member-index path inside the rule. Measured 2026-10-06: 31 rules with a `,`, 3 with a
  `;`. A hidden helper rule (`_link_value_run`) is reported with the visible rules that reach it, so the
  registry can attach a template to the host a user writes.
- **Expression slots.** Every `SYMBOL _expression` (directly or through one hidden rule), keyed
  `(rule, field or path)`, marked `tail` when the same `SEQ` is followed by an optional
  `preproc_conditional_expression_tail` (9 rules have one today: `assignment_statement`, `if_statement`,
  `for_statement`, `while_statement`, `exit_statement`, `_argument_expression`, `subscript_expression`,
  `list_literal`, `_property_value_with_split`).

The census is pure (grammar.json in, two lists out) and has a unit test on a hand-written mini grammar.

## 4. Registry

`tools/b7_audit/sites.tsv`, one row per census key:

| column | meaning |
|---|---|
| `key` | the census key |
| `class` | `separator`, `continuation`, `na`, or `same-as <key>` |
| `template` | AL source with one `⟨HOLE⟩`, a self-contained object that compiles (`tools/alc_probe` rules: no Base App symbols) |
| `elements` | the list elements (or the expression and operand) placed around the hole |
| `reason` | required for `na` and `same-as`: why no probe is meaningful, or which row covers it |

`na` is for sites where no `#if` placement can occur or no alc-valid input exists (e.g. a separator
inside a token-level construct). Every `na` needs a reason a reviewer can check.

The gate (`python -m tools.b7_audit census --check`, validate-grammar.sh new step, CI): exit 1 when a
census key has no row or a row names no census key (stale); exit 2 when grammar.json is missing.

## 5. Placements

For a `separator` row with elements `A`, `B`, `C` and separator `s`:

| id | shape (directives on their own lines) |
|---|---|
| `sep-after` | `A s #if X B s #endif C` (separator before the arm's element) |
| `sep-before` | `A #if X s B #endif s C` (separator inside the arm, leading) |
| `lead` | `#if X A s #endif B` (the list opens inside an arm) |
| `trail` | `A s #if X B #endif` (the list closes inside an arm) |
| `empty` | `A s #if X #endif B` |
| `else` | `A #if X s B #else s C #endif` |
| `elif` | `sep-before` with an `#elif Y` arm |
| `nested` | `sep-before` with the arm's element inside a nested `#if Y` |

For a `continuation` row with expression `E` and operand `F`, operator `op` (one arithmetic, one
comparison, one keyword operator per slot):

| id | shape |
|---|---|
| `op-arm` | `E #if X op F #endif` |
| `op-arm-else` | `E #if X op F #else op G #endif` |
| `op-only` | `E #if X op #endif F` |
| `semi-in-arms` | `E #if X op F; #else ; #endif` (statement hosts only) |

Placements a host cannot take (`semi-in-arms` outside a statement) are not generated; the row records
which were skipped and why.

## 6. Judging a cell

Each generated input is run three ways:

1. **alc** via `tools.alc_probe` (every symbol assignment, split and flat; controls first; `BROKEN`
   rows are template bugs and fail the run, never a verdict).
2. **Parser** `has_error` on the split source.
3. **Oracle** `tools.config_oracle.runner.check_input` on the split source, when the parser is clean.

Verdicts:

| verdict | alc | parser | oracle |
|---|---|---|---|
| `OK` | accepts every configuration | clean | pass for every configuration |
| `OK-NEG` | rejects some configuration | ERROR | — |
| `GAP` | accepts every configuration | ERROR | — |
| `SILENT` | accepts every configuration | clean | a discrepancy |
| `REVIEW` | accepts every configuration | clean | cannot-validate for some configuration |
| `OVER` | rejects some configuration | clean | — |

`SILENT` is the worst class (a wrong tree with no ERROR); `REVIEW` rows get a hand check (the tree read against the flat reading of each configuration),
recorded in `tools/b7_audit/review.tsv`, before the matrix is final. A split/flat
disagreement inside alc is reported as `MISMATCH` and blocks the cell.

## 7. Outputs

- `docs/b7-separator-continuation-matrix.md`, generated by `python -m tools.b7_audit report`: one table
  per class with the verdict of every placement, totals, the production impact of each host (sites from
  `./tools/corpus-grep.sh`, recorded with the command), and the ranked fix list.
- Generated inputs are not committed. Every `GAP`, `SILENT` and `OVER` cell gets a committed alc probe
  under `tools/alc_probe/cases/b7-audit/` (`--check` clean) and a fixture pinning today's tree:
  `GAP` in `test/corpus/b7_gap_<family>_test.txt` (deliberate negatives, oracle `debt(B7)`), `SILENT`
  and `OVER` the same way with the defect named in the header, so B7b+ flips a pinned case.
- Item 1 and item 2 rewritten from the matrix; item 30 and item 39 cross-referenced to their cells.
- The ranked list: B7b+ order by (`SILENT` count, `GAP` count, production sites), with item 39's two
  shapes placed by the same rule.

## 8. Gates

- `python -m tools.b7_audit census --check` exit 0 (and in validate-grammar.sh and CI).
- `python -m tools.b7_audit run` reproduces the committed matrix byte-for-byte from a clean checkout
  (no hand edits; each `REVIEW` hand check is a row in `tools/b7_audit/review.tsv`: cell id, verdict `OK` or `SILENT`, and the reason, which the report reads).
- alc_probe `--check` over the new cases clean; `tree-sitter test` total moves by exactly the cases
  added; has_error sweep over corpus fixtures clean; oracle quick tier exit 0 with the new `debt(B7)`
  entries; `validate-grammar.sh --full` green.
- No change to `grammar.js`, `src/`, or any existing expected tree.

## 9. Cost

About 35 separator sites x 8 placements + about 40 expression slots x 4 placements is roughly 440
inputs; at two configurations, split and flat, about 1,800 alc compiles. alc_probe runs a compile in
about 1-2 s, so a full run is 30-60 minutes; `run --only <key>` re-runs one site. The census gate is
instant.
