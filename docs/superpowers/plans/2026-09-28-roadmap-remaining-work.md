# Roadmap: the remaining open work (from 2026-09-28, revision 2)

This roadmap sequences every open item into sub-projects. It is not a task-level
implementation plan. Each sub-project gets its own cycle: a design, a spec where
the work is architectural or changes the public tree, then a task plan and a
reviewed execution, the way milestone 2 and G6 were done.

**Revision 2** folds in gpt-6-astra's review of revision 1
(`scratchpad/astra-roadmap.md` of the 2026-09-28 session). The user approved it
and adopted its recommendations on all five decisions. The review also found a
defect that revision 1 missed. It is confirmed and scheduled first in Phase B:
`#if not A and B` parses as `not (A and B)`.

**The sources:**
- `docs/deferred-work.md`: items 1-4, 6, 7, 9-16;
- the oracle registry (`tools/config_oracle/contracts.py`), by type, host, arm shape and reading, not only its `unsupported` entries;
- the milestone-2 results document;
- CI (`.github/workflows/ci.yml`);
- the `[Unreleased]` section of `CHANGELOG.md`.

**The goal** is a parser that parses AL *correctly*: no ERROR on valid AL, no
silent wrong tree, and node types and fields that tell the truth. Three kinds of
progress are tracked separately throughout, because progress in one is not
completion of the others:

- **correctness:** the grammar builds the right tree;
- **verification coverage:** what the gates can see;
- **delivery compatibility:** consumers, queries and artifacts.

**A limit of the oracle:** it checks *configuration consistency*, not correctness.
Both parses share one grammar, so a defect present in both the multi-configuration
and the flat parse is invisible to it. The condition-grouping defect and G9 are
examples. Independent instruments cover that gap: alc differential probes, the
precedence table, and hand-written contracts.

## Ordering principles

1. **Gates and baselines first,** including the oracle that already exists. Item 12
   showed a defect class every command-line gate misses. Protection that already
   exists should gate now, not after every handler is written.
2. **Interleave oracle coverage with grammar work.** Item 8 showed that unsupported
   types hide defects. Stable, high-impact lowering comes early. Lowering that
   depends on a pending representation change waits for it.
3. **Silent wrong trees before ERRORs.** Production sites come first within each class.
4. **Settle design dependencies before implementing their dependents.** The ML
   design (B4) comes before the ML separator host (B3). The dotted-reference design
   (B5) comes before relation-specific lowering.
5. **Measure size early, optimise late.** The expanded oracle may drive further
   shape changes.
6. **Design the configuration-aware parse early, implement it against an agreed
   contract.** Do not assume it removes grammar or oracle work: it cannot fix a
   flat misparse, and an API layer does not fix the native CST that editors and
   WASM consumers use.

## Phase A: gates, instruments, baselines

| # | Sub-project | Items | Exit, demonstrated |
|---|---|---|---|
| A1 | **The `has_error` gate.** A py-tree-sitter sweep runs in `validate-grammar.sh --full` and CI. It fails on any file whose `root_node.has_error` is true, and reports hidden-only errors as their own diagnostic category. Positive corpus fixtures also run through `has_error`. It also corrects the `parse-al-parallel.sh` comment. | 12 | A mutation that re-introduces a hidden MISSING (reverting `_directive_eol`'s whitespace loop) fails the gate. A missing input and a broken build each fail it. All four corpora are clean. |
| A2 | **Split-matrix probe tooling.** It runs every symbol assignment of a multi-symbol probe, in isolated projects with fresh output. It records the compiler's identity, runs valid and invalid controls, and tells a broken environment apart from a syntax rejection. It builds on `tools/config_oracle/probe_alc.py`. | 7 | It reproduces the recorded verdicts of existing probes (BC 29 families, G11, items 17 and 18). A deliberately broken project is reported as broken. |
| A3 | **The oracle as a CI gate now.** A config-oracle CI job runs pytest, the quick tier, `replay`, and the registry census plus self-tests (which the CLI does not invoke today). It adds the base spec's per-corpus accounting: every requested root must be non-empty and accounted for, so an empty corpus beside a healthy one fails. | base spec §4 | The CI job is red on a planted discrepancy, on an unregistered special type, on a stale classification, and on an empty corpus root. |
| A4 | **Exact classification of production refusals.** One file, loaded by `--tier resolve|full`, keyed by exact identity: source, configuration, reason, type and host. It separates three categories: **expected invalid input** (with compiler evidence), **temporary verification debt** (each entry with an owner and a removal milestone), and everything else. It covers every current refusal: the 7 invalid-source records, the 11 `arm-content`, the 10 `one-reading`, the 4 EDocumentDE `multi-config-parse:error`, and the milestone-3 `unsupported-type` records. | 14 | A clean production run exits 0. A new unclassified refusal exits 1. A stale entry exits 1. No classification can make a configuration count as validated. |
| A5 | **Performance and resource baselines.** It records native and WASM full-parse throughput over the four corpora, per-file tail latency, fresh-parse against incremental-parse tree equivalence on sample edits, generate and build time, `parser.c` size, and oracle wall time with aggregate process-tree memory. The recorded 1,256 MiB was a per-process maximum, and the run-3 timing was confounded. | new | The numbers are recorded in a baselines document, with the commands, and are reproducible. Later sub-projects compare against them. |
| A6 | **Backlog hygiene.** Close revision 1's F4: the Python bindings already use `PyCapsule` (`bindings/python/tree_sitter_al/binding.c`); replace it with a compatibility check against the declared tree-sitter runtime range. Reconcile `docs/improvements-for-owned-ir-consumer.md` against the current `node-types.json`. Move the state-reduction method, now private memory, into a repository doc. | rev-1 F4, F5 | The stale documents are updated or closed, and the method doc is in the repository. |
| A7 | **The F1 scope decision (design only, no implementation).** Is the deliverable a correct native multi-configuration CST, a configured-tree API, or both? The decision must cover representation of alternatives, configuration-dependent tokenisation (the G7 signed literal), incremental updates, and which runtimes are supported. | 10 | A spec approved by the user. Later phases schedule against it. |

## Phase B: grammar correctness, interleaved with oracle coverage

Silent wrong trees first. Each grammar fix ships its oracle witnesses in the same
change. For B3 and B4, the matrix is host × separator/terminator placement ×
branch × nesting.

| # | Sub-project | Items | Kind | Notes |
|---|---|---|---|---|
| B1 | **`#if` condition grouping.** This is a silent wrong tree, confirmed on 2026-09-28. `#if not A and B` parses as `not (A and B)`, and `#if not A or B` as `not (A or B)`. alc's rule is `not` > `and` > `or` (`docs/preproc-directive-semantics.md`). `preproc_not_expression` has no precedence (`grammar.js`, the `preproc_*_expression` rules). Production has 0 sites in all four corpora (grep, 2026-09-28). The fix also adds a **condition-structure check** to the oracle: the tree's condition is evaluated per configuration and compared against the resolver's choice, as a truth table. The oracle must still never select branches from the tree under test. | new | bounded | The fixture pins all three operators and parentheses. The new check must fail on today's grammar. |
| B2 | **Directive-word boundaries, and removing `&&`/`||`.** `#elif`/`#else` are matched with prefix regexes, and the scanner documents accepting the prefixes (`grammar.js` `preproc_elif`/`preproc_else`, `src/scanner.c` directive dispatch). Also remove the `&&`/`||` alternatives (decision 3), and update `queries/highlights.scm`, which captures them. Also reject a token after `#endif`: `#endif;` is AL0631 to alc, but parses with no error, its `;` read as a property terminator or an empty statement (0 production sites in all four corpora; `#endregion;` is valid and has 2) | 9, 20, new | bounded | alc-probe each prefix form (A2). Negative fixtures. The oracle resolver's `unsupported-condition-token` path then becomes a real parse error. |
| B3 | **The dangling-operator residual.** `#if FOO and`, with the operand on the next line, is absorbed into the condition: a silent wrong tree, which alc rejects (AL0629). Its fixture is a tripwire that asserts the defect. A second shape (found 2026-09-29): an operator ALONE in a `#if` arm, `i := 1 #if X + #endif 2;`, is valid AL with X defined (alc accepts it split and flat; `tools/alc_probe/cases/oracle-negative/split-operator.al`), and the parser ERRORs on it. | 3 | bounded | Flip the tripwire deliberately, and update its header. For the second shape, `test/corpus/preproc_split_operator_negative_test.txt` stops asserting the ERROR, its entry leaves `tools/deliberate-negatives.txt`, and its `debt(B3)` line in `fixture-classes.tsv` goes stale and is removed. |
| B4 | **G9: a one-pair ML value, by name-keying** (decision 1). `CaptionML = ENU='c';` parses as a comparison. The keying is narrow: a finite, documented, compiler-probed ML-property family, not "every name ending in ML". Unknown names keep the generic path. Language codes and hosts are not validated. It lives in the scanner's single-read dispatch; its word buffer covers only `calcformula` today (`src/scanner.c`, `read_identifier_word`). | 11 | **spec** | Tests: prefix collisions, casing, comments, Unicode continuations, scanner-state combinations, incremental edits. One pair and many pairs, whole-value `#if`, both `;` placements, list-internal splits, `TextConst` reuse. Ordinary comparisons must be unchanged. |
| B5 | **Dotted references and G10: a neutral node** (decision 2). `Visible = Rec.A;` is `table_relation_value(... simple_table_relation table: (member_expression))`, and `Visible = Rec.A #if X and B #endif ;` ERRORs. An ambiguous dotted property value gets a neutral reference structure with no `table` field, unless relation syntax establishes the relation role. It has the same shape in flat, whole-value and continued forms. No broad name-keying. | 13, 15 | **spec, tree-shape change** | A hand-written node and field contract, a production impact census, exact intentional tree deltas, query capture tests, and a consumer migration note. |
| B6 | **`_expression_statement` narrowing** (decision 4), as a correctness backstop. The grammar's own comment (the rule's comment block in `grammar.js`) says the permissive rule lets valid split expressions tear into unrelated siblings silently. Investigate de-inlining, and separate genuine statement syntax from split-fragment allowances. | 4 | research, then **spec** | Every valid call, member, assignment and split form is preserved. Demonstrate that the historical detached-expression shapes cannot return silently. **Never merge an intermediate state that loses production coverage;** the earlier attempts dropped to about 35%. |
| B7 | **Separator and continuation audit, then fixes.** First a FRESH audit: the six-site list from 4.0.0 was never re-verified. It covers separator positions and expression continuation hosts (`foreach` iterable, `repeat` condition and `with` operand have no continuation facility today, and `in`/`is`/`as` are not continuation operators). The output is an enumerated, compiler-tested matrix. Then the fixes: `parameter_list` (`;`-led), `implements_clause`, the key field list and comma-leading option members, independently. The comma-leading `link_value_list` goes with a shared link/property ambiguity matrix, because the G8/G11 history shows the interaction. `ml_value_list` comes after B4. | 1, 2, new | audit, then bounded per host | Every host has BOTH comma placements pinned, and active oracle witnesses ship in the same change. |
| B8 | **CalcFormula whole-value conditional.** | 16 | bounded | First alc-probe that it is valid. The arms stay formula-shaped (`aggregate_formula` / `lookup_formula`). |
| B9 | **The doubled BOM.** | 6 | bounded | Probe alc first. Its verdict decides between absorbing it as an extra and surfacing it as text. |

**Oracle work interleaved into Phase B (the start of C1).** These are the
recorded leading blockers (milestone-2 results), and none waits on a
representation change:
- `preproc_split_if_then_begin` (138 blocked configurations; revision 1 omitted it);
- `preproc_split_if_else_statement` (106);
- `preproc_split_declaration` (62);
- then the rest of the split-if family, sharing one "prefix + continuation" assembler with the complete arms of `preproc_split_open_statement`;
- `preproc_split_procedure_body` / `_complete_body`;
- `preproc_split_report_dataitem_header`, which blocks the GB SalesShipment report.

Run production after each handler family: removing one refusal can reveal the next
defect deeper in the same tree. Relation-specific lowering waits for B5.

## Phase C: finish the oracle's coverage and make it the full gate

| # | Sub-project | Exit, demonstrated |
|---|---|---|
| C1 | **Milestone 3, complete.** An inventory by **type × host × arm shape × reading**, including refusal paths inside handlers. That covers the unsupported `table_relation_expression:<children>` host, `case_else_branch` in `preproc_conditional_case` (a re-parenting fragment design), the four `ARM_EXEMPT` entries, the complete-prefix arms of `preproc_split_open_statement`, and the G7 signed-literal one-reading, which today lives only in `ExpressionContinuation.apply`. It also adds the base spec's deterministic transformations. | No valid path is unsupported within scope. Active witness coverage is enforced. Mutations prove that wrong attachment is *detected*, never repaired. Refusals that remain are only expected invalid input and enumerated debt, each classified (A4). The 4 EDocumentDE records stay explicit debt until F1 or a grammar solution. |
| C2 | **Milestone 4: the quick tier is mandatory** (validate-grammar Step 5e, CI, `gate_selftest` cases). Its exit replaces revision 1's "zero cannot-validate and no classification file", which contradicted deliberate negatives. | Zero discrepancies and zero representation violations. Zero unexpected refusals. Every positive supported witness is actually compared. Deliberate negatives are checked against their exact expected failures. Debt is enumerated separately and shrinking. Every gate failure mode is tested. |
| C3 | **Milestone 5: the full tier as a staged gate** over the four corpora. It adds content manifests per corpus (production ids are filesystem paths today, and headers record corpus HEADs, not content). The grammar identity is taken AFTER any rebuild (today the hash is computed before the runner may rebuild). Per-root completeness, and reproducible resource measurements. Update CLAUDE.md with the oracle's contract and its limit. | Every (file, configuration) is accounted for, per root. Mutation tests cover a missing corpus and an empty corpus. The baseline is empty. |

## Phase D: size and performance

| # | Sub-project | Exit |
|---|---|---|
| D1 | **The state-reduction pass,** after the Phase B and C1 grammar triage, over the split and whole-value rules added since 4.0.0 (STATE_COUNT 14,060 → 15,870; `parser.c` 38.8 MB). It uses the method doc from A6. | Preservation across all four corpora: complete cursor-derived trees including anonymous tokens, fields and spans; `has_error`; full oracle results; and fresh-parse against incremental-parse equivalence. `node-types.json` is byte-identical. There is no material parse-speed or incremental regression against the A5 baselines. Fewer states alone is not success. |
| D2 | **A permanent performance and fuzzing workstream.** Scheduled fuzzing (today the fuzz job runs only on scanner diffs against `HEAD^`), seeded with split constructs and scanner-sensitive edits. Pathological-GLR inputs, and tail latency. | Scheduled jobs are green. Regression thresholds are set from the A5 baselines. |

## Phase E: delivery compatibility

These are release gates, not an afterthought.

| # | Sub-project |
|---|---|
| E1 | **Query behaviour tests.** Capture tests for all six shipped query files: CI checks validity only, and the query-coverage harness treats shipped queries as informational. A deliberate policy, with a witness, for each special type a query covers or omits. That includes `tags.scm` for split object declarations and split-procedure preambles, and the conditional families in folds and indents. |
| E2 | **Consumer migration validation** for every tree-shape change in the release (G1-G8, G6, G11, P1, and B5 when it lands). Executable old/new consumer examples. Field-cardinality checks for each arm's `value`. Tests that tell whole-value selection apart from relation continuation. Regeneration and parity testing of the downstream owned-IR consumer. |
| E3 | **Artifact verification.** `tools/check-wasm-fresh.sh` hashes only `parser.c` and `scanner.c`, although the scanner includes `unicode_id.h`, so extend its provenance. Add a WASM load-and-parse behavioural comparison, since a freshness stamp alone is not a test. Test the Python package against the declared runtime range. |

## Phase F: architecture

| # | Sub-project |
|---|---|
| F1 | **Configuration-aware parsing,** implemented against the A7 spec. It must define selection, presence predicates, alternative parentage and tokenisation, source and trivia preservation, invalid configurations, configuration explosion, incremental updates, cancellation, and supported runtimes. Demonstrate it on EDocumentDE and on every one-reading family. A configured-tree API must never be presented as a fix to the native CST it bypasses. |

## Release and publishing (decision 5)

- **Pushing is separate from releasing.** Pushing reviewed commits to origin, for
  backup and CI, needs the user's explicit approval each time: re-check the
  repository state first. It does not wait for a release.
- **The next stable major release** comes after the tree-breaking Phase B work
  (B5, and B4 and B6 if they change trees), the operational gates (A1 to A4, C2),
  and the consumer migration validation (E1 to E3). The end of Phase A is a
  checkpoint or release-candidate boundary, not the stable release.
- **At release:** consolidate the CHANGELOG, bump the major version (node and field
  structure are public API, `CHANGELOG.md` header), rebuild and test the
  distributed artifacts, and release from the exact verified commit.

## Order

A1 → A2 → A3 → A4 → A5 → A6 → A7 (spec)
→ B1 → B2 → B3, with C1's first handlers (split-if-then-begin, split-if-else, split-declaration) interleaved
→ B4 (spec) → B5 (spec) → B6 (research + spec) → B7 (audit, then hosts) → B8 → B9, with the rest of C1 interleaved
→ C1 complete → C2 → C3
→ D1 → D2
→ E1 → E2 → E3 → stable major release
→ F1 (per the A7 contract; it may start earlier if A7 decides so).

Specs B4, B5, B6 and A7 each wait for user approval. Work continues on other
items while a spec is under review.
