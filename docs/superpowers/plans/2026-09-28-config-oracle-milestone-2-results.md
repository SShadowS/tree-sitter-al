# Config oracle — milestone 2 results

Measured on 2026-09-28 on branch `feat/config-oracle-m2`. The runs used different
commits; each section names its own (the grammar hash is the report header's):

| Section | HEAD | grammar |
|---|---|---|
| Resolve sweep | `6b94cd9` | `2c3928c57fe98fc7` |
| First production run, run 1; Triage (clusters of run 1) | `df7997c` | `2c3928c57fe98fc7` |
| First production run, run 3 (the recorded state) | `eb189bf` | `e8a637023c3d15ca` |
| Exit table | after `0bea280` (no grammar change since `eb189bf`) | `e8a637023c3d15ca` |

The final fix wave's scanner change (`673528e`) moves the grammar hash to
`0148e8d7e4ec0526`; the quick tier gives the same numbers there.

Corpora: BC.History `87e7d2a19d2`, DC `5e67e5b9c`,
BC 28.1 W1 `4fc2ccf16` (`H:/Git/BC28.1`), BCApps 29.0 `e16d6c30`
(`H:/Git/BCApps-29.0`). Every run below was wrapped in `./tools/ts-lock.sh`.

## Resolve sweep

```
./tools/ts-lock.sh python -m tools.config_oracle run --tier resolve \
  --root ./BC.History --root ./DC --root H:/Git/BC28.1 --root H:/Git/BCApps-29.0 \
  --report tools/config_oracle/reports/resolve-m2
```

Summary: 14,662 configurations checked, `pass` 14,655, `cannot-validate` 7
(`reference-error:error` 7), 0 `resolver:*`, 0 internal errors; 64,624 inputs without
conditional directives; `elapsed: 482.4s` inside `runner.run` (13 m 44 s wall,
including corpus read and lock); peak RSS 1,256 MiB (max over processes); exit code 1.
The exit code is 1 because the resolve tier has no classification file: the 7 records
are classified here, not in `fixture-classes.tsv`, which covers fixtures only.

| Corpus | `.al` files | with `#if` | configurations | pass | `reference-error:error` | `resolver:*` |
|---|---|---|---|---|---|---|
| BC.History | 15,358 | 1,281 | 3,120 | 3,120 | 0 | 0 |
| DC | 1,352 | 44 | 92 | 92 | 0 | 0 |
| BC 28.1 | 16,928 | 1,061 | 2,580 | 2,580 | 0 | 0 |
| BCApps 29.0 | 36,717 | 3,345 | 8,870 | 8,863 | 7 | 0 |
| **total** | **70,355** | **5,731** | **14,662** | **14,655** | **7** | **0** |

File total checked: 64,624 + 5,731 = 70,355, the sum of `.al` files under the four
roots. The three older corpora give the same `#if` file and configuration counts as
milestone 1 (1,281 / 44 / 1,061 and 3,120 / 92 / 2,580), all still `pass` after the
BC 29 fixes and G1 to G5.

The two known BCApps parse-error files:
- `Apps/DE/EDocumentDE/app/src/EDocumentServiceDE.PageExt.al` (deferred-work item 10):
  all 4 configurations `pass`. Each configuration on its own is valid AL; only the
  multi-configuration parse fails, and the resolve tier does not use it.
- `Layers/APAC/Tests/SINGLESERVER/ERMPurchaseReportsIII.Codeunit.al` (invalid source):
  it has no conditional directive, so it is one of the 64,624 flat inputs and the
  resolve tier does not check it.

No `#if`/`#elif` line in BCApps 29.0 uses `&&` or `||` (grep), so deferred-work item 9
still has zero production impact across all four corpora.

### Classification

One cluster, 3 files, 7 configurations. Every record was examined; none was sampled.

| Cluster | Records | Files (configuration) | Classification | Evidence |
|---|---|---|---|---|
| Table field opened inside `#if not CLEANSCHEMA<n>` and closed after `#endif` (the `preproc_split_table_field_open` family) | 7 | `Apps/IN/INFADepreciation/app/src/table/FixedAssetShift.Table.al` (`CLEANSCHEMA26=1`); `Apps/W1/SalesOrderAgent/app/src/Setup/SOASetup.Table.al` (`CLEAN28=0,CLEANSCHEMA28=1`, `CLEAN28=1,CLEANSCHEMA28=1`); `Layers/FR/BaseApp/Bank/BankAccount/BankAccount.Table.al` (all four `CLEAN27`×`CLEAN28` with `CLEANSCHEMA31=1`) | **invalid source in that configuration** | See below. |

Every one of the 7 records has `CLEANSCHEMA<n>=1`, and every configuration of these
files with that symbol undefined is `pass`. The first error offset sits right after the
field's closing `}`: FixedAssetShift line 206 (after `#if` 195 / `#endif` 205), SOASetup
line 42 (`#if` 28 / `#endif` 40), BankAccount line 1087 (`#if` 1032 / `#endif` 1085).
With the symbol defined, the resolver removes the field header and `{`, but not the
`}` after `#endif`. That `}` closes `fields` early, so the following `field(...)` lines
land outside any section. The grammar comment on `preproc_split_table_field_open`
names these three files and says that only the `#if`-taken configuration compiles.

Four-way alc probe, re-run for this task on self-contained repros of all three shapes:
FixedAssetShift (the body continues with a trigger after `#endif`), SOASetup (a nested
`#if not CLEAN28 … #else … #endif` before the outer `#endif`), and BankAccount (a nested
`#if CLEAN28 … #else` whose else arm carries a trigger). The harness was
`probe_alc.compile_probe`, with the flat text taken from `directives.resolve`.
Controls: sanity ACCEPT, garbage REJECT (AL0183, AL0198).

| Shape | schema symbol undefined, split / flat | schema symbol defined, split / flat |
|---|---|---|
| FixedAssetShift (`CLEANSCHEMA26`) | ACCEPT / ACCEPT | REJECT / REJECT (AL0104, AL0162, AL0198) |
| SOASetup (`CLEANSCHEMA28`), `CLEAN28` undefined and defined | ACCEPT / ACCEPT (both) | REJECT / REJECT (AL0104, AL0198) (both) |
| BankAccount (`CLEANSCHEMA31`), `CLEAN28` undefined and defined | ACCEPT / ACCEPT (both) | REJECT / REJECT (AL0104, AL0198) (both) |

The compiler rejects exactly the configurations the oracle reports, and accepts every
configuration the oracle passes. The oracle and the grammar are both right here: this
is Microsoft source that nobody builds with `CLEANSCHEMA<n>` defined.

### Fixes made

None. No resolver defect was found (0 `resolver:*` records), and no grammar defect
(every `reference-error` is a configuration alc also rejects).

### Findings for Task 18

None from the resolve sweep.

## First production run (P6)

The first full-tier run over production, with no baseline and no gate (base
milestone 5's first stage). Every run was wrapped in `./tools/ts-lock.sh`.

```
./tools/ts-lock.sh python -m tools.config_oracle run --tier full \
  --root ./BC.History --root ./DC --root H:/Git/BC28.1 --root H:/Git/BCApps-29.0 \
  --report tools/config_oracle/reports/full-m2
```

Corpora as in the resolve sweep: BC.History `87e7d2a19d2`, DC `5e67e5b9c`, BC 28.1
`4fc2ccf16`, BCApps 29.0 `e16d6c30`.

### Run 1: before any Task 18 fix

HEAD `df7997c`, grammar `2c3928c57fe98fc7`. `elapsed: 633.9s` inside `runner.run`
(10 m 41 s wall), peak RSS 1,256 MiB (max over processes), exit code 1.

| Corpus | `#if` files | configurations | pass | discrepancy | directive-mismatch | cannot-validate |
|---|---|---|---|---|---|---|
| BC.History | 1,281 | 3,120 | 2,549 | 0 | 48 | 523: `empty-node` 279, `unsupported-type` 242, `arm-content` 2 |
| DC | 44 | 92 | 80 | 0 | 0 | 12: `empty-node` 10, `unsupported-type` 2 |
| BC 28.1 | 1,061 | 2,580 | 2,209 | 0 | 6 | 365: `empty-node` 303, `unsupported-type` 58, `arm-content` 4 |
| BCApps 29.0 | 3,345 | 8,870 | 7,636 | 0 | 20 | 1,214: `empty-node` 1,088, `unsupported-type` 100, `one-reading` 10, `reference-error` 7, `arm-content` 5, `multi-config-parse` 4 |
| **total** | **5,731** | **14,662** | **12,474** | **0** | **74** | **2,114** |

Zero `structure`, `coverage`, `leaf-boundary` or `trivia` discrepancies over 12,547
compared configurations (12,474 pass plus 73 directive-mismatch records whose
comparison ran). The 74 directive-mismatch records compared clean; each
carried only directive items (one also carried `empty-node`).

### Run 3: after the Task 18 fixes (the recorded state)

HEAD `eb189bf` (grammar `e8a637023c3d15ca`; the later commits change no grammar
file). `elapsed: 902.8s` inside `runner.run` (21 m 49 s wall), peak RSS 1,256 MiB,
exit code 1. It is slower than run 1 on the same input. Two causes are known and
neither was isolated: 1,680 configurations that run 1 refused early are now fully
compared, and the C: drive held 2.1 GB free during the run.

```
./tools/ts-lock.sh python -m tools.config_oracle run --tier full \
  --root ./BC.History --root ./DC --root H:/Git/BC28.1 --root H:/Git/BCApps-29.0 \
  --report tools/config_oracle/reports/full-m2-final
```

| Corpus | configurations | pass | discrepancy | directive-mismatch | cannot-validate by reason |
|---|---|---|---|---|---|
| BC.History | 3,120 | 2,876 | 0 | 0 | 244: `unsupported-type` 242, `arm-content` 2 |
| DC | 92 | 90 | 0 | 0 | 2: `unsupported-type` 2 |
| BC 28.1 | 2,580 | 2,518 | 0 | 0 | 62: `unsupported-type` 58, `arm-content` 4 |
| BCApps 29.0 | 8,870 | 8,744 | 0 | 0 | 126: `unsupported-type` 100, `one-reading` 10, `reference-error` 7, `arm-content` 5, `multi-config-parse` 4 |
| **total** | **14,662** | **14,228** | **0** | **0** | **434** |

Summary line: `0 unclassified findings, 0 classified, 434 configurations not
validated (lowering:unsupported-type 402, lowering:arm-content 11,
lowering:one-reading 10, reference-error:error 7, multi-config-parse:error 4)`.
Validated configurations rose from 12,547 to 14,228 (97.0% of all 14,662).

**Time budget.** 634 s to 903 s inside the runner, 11 to 22 minutes wall, peak RSS
1.26 GiB. That is the full tier's cost over four corpora at 5,731 `#if` files.

**Run 2 is not recorded.** It was started after the oracle and directive fixes,
but grammar.js and scanner.c were edited for G7 while it read the corpus, and the
runner's `ensure_library` regenerated the parser from the edited files before it
dispatched. Its numbers belong to no commit, so run 3 replaced it. Lesson: edit
nothing under `src/` or grammar.js while a run is reading its corpus.

## Triage

Every cluster of run 1, grouped by `(check, kind, first special type on the path)`
(scratchpad script, not in the repo), then the fixture-found findings.

### Production clusters

| # | Cluster | Records | Class | Evidence and fix |
|---|---|---|---|---|
| P1 | `directive / end-extent / preproc_if` | 74 records, 128 items, 34 files (BC.History 21, BCApps 10, BC 28.1 3) | **(a) grammar, fixed** `687ad60` | `#if X` followed by blank lines: the tree's `preproc_if` ended on the LAST blank line. The terminator `token(/\r?\n/)` is also a whitespace separator, and longest match skipped newlines and took the last. Now a hidden external `_directive_eol` takes exactly one `\r?\n`. (`token.immediate(/[ \t]*\r?\n/)` was tried and rejected: it made 5 BC 28.5 comments start one column early.) alc four-way ACCEPT on the repro. tree-harness: BC.History 21 files, BC 28.5 4 files changed, every hunk a `preproc_if` end moving back to the line after the directive. |
| P2 | `lowering:empty-node at source_file` | 1,656 (1,655 cannot-validate + 1 directive-mismatch) | **(b) oracle, fixed** `b666ced` | A whole object inside `#if not CLEANnn`: the other configuration is an EMPTY FILE. The reference parses it as a childless `source_file`; lowering refused the emptied root, and the comparator read a childless root as one leaf spanning the file. Now the root lowers to a childless `source_file` and is still compared (a mutation test pins a non-empty reference surfacing as a discrepancy). |
| P3 | `lowering:empty-node at action_body` / `layout_body` | 22 + 3 | **(b) oracle, fixed** `b666ced` | An area whose only actions, or a layout whose only elements, sit inside the `#if`. Every site of both is `optional(field('body', ...))` (checked in grammar.js), so both join `EMPTY_REMOVABLE`. |
| P4 | `lowering:unsupported-type` | 402 configurations | **(c) accepted: milestone 3** | Every type is registered `unsupported` with milestone 3 named (`0bea280`). Breakdown under "Registry state at exit". |
| P5 | `lowering:arm-content at case_else_branch` | 11 (6 files) | **(c) accepted: Task 6 ruling** | A case-else inside `preproc_conditional_case`: it is `case_statement`'s sibling field, not `case_body` content, and needs a re-parenting fragment (milestone 3). |
| P6 | `lowering:one-reading` | 10 (`open_statement` 6, `else_begin_over_endif` 2, `container_reopen` 1, `block_end_in_else` 1) | **(c) accepted: declared one-reading (P4)** | Each is the configuration outside its type's declared `reading`. None is a pass. |
| P7 | `reference-error:error` | 7 (3 BCApps files) | **(c) accepted: invalid source** | The resolve sweep's cluster (above): `CLEANSCHEMA<n>` defined, alc rejects the same configurations. |
| P8 | `multi-config-parse:error` | 4 (EDocumentServiceDE.PageExt.al) | **(c) accepted: deferred-work item 10** | The split `add*` layout open; no rule lowers it. |

No production cluster was a discrepancy.

### Quick tier's `lowering:empty-node` records

Task 4 left 22 unidentified. Identified against the current quick tier, all 22 were
the P2 and P3 classes: **21 whole-file-inactive configurations** (the
`preprocessor_wrapped_*`, `file_level_preprocessor_test.txt`,
`enum_empty_value_test.txt`, `preproc_expression_parens_test.txt` cases, and 12
configurations of the `lossless_keyword_nodes_test.txt` type-keywords case) and
**1 emptied `action_body`** (`preprocessor_actions_test.txt`, EnableBeta=0,
TESTMODE=1). All 22 pass now. A 23rd, an emptied `xmlport_body`
(`xmlport_preprocessor_elements_test.txt`, CLEAN23=0,LOCALAPP=0), surfaced once
these were gone: **(b) fixed** `7b53ebd`, `xmlport_body` has one site,
`optional(field('body', ...))`.

### Fixture-found findings (G1 to G9)

| Finding | Class | State |
|---|---|---|
| G1 `table_relation_property` value lacked the `table_relation_value` wrapper | (a) | fixed, Task 8b `a5450a8`, oracle `dd96c63` |
| G2 bare relation in a whole-value arm was `table_relation_expression` | (a) | fixed, Task 8b `c0a31af` |
| G3 a `#if` nested in a whole-value arm had relation arms | (a) | fixed, Task 11b `ee1edff`, `dce6682` |
| G4 string/boolean arms ERRORed, integer arms were table relations | (a) | fixed, Task 11b `9966e45` |
| G5 a `#if`-continued property value was a bare expression | (a) | fixed, Task 11b `bbd0484`, oracle `46cf2ae` |
| G6 `preproc_conditional_table_relation` wraps arms that are not table relations | naming | **fixed on branch `feat/g6-property-value-conditional`**: the whole-value `#if` is `preproc_conditional_property_value` with a `value` field per arm; `preproc_conditional_table_relation` keeps only relation continuations. Oracle: new `whole-value-select` contract. tree-harness byte-identical, BC.History and BC 28.5. (Was: open, awaiting the user's decision; G8 widened it to any property value.) |
| G7 `Visible = -1 < Rec.O;` ERRORed (signed-literal token won by longest match) | (a) | **fixed** `503f0db`: the signed literal is an external token, emitted only before `;` `,` `#` or EOF. alc: ACCEPT. Note: alc rejects `MinValue = -1 + 2;` (AL0104), but only because MinValue takes a literal (`MinValue = 1 + 2;` is rejected the same way), so the flat form of the ledger's example was invalid AL. tree-harness byte-identical, BC.History and BC 28.5. |
| G7, split form: `MinValue = -1 #if X + 2 #endif ;` ERRORed | (a) | **fixed** `3c6ca40`: the continued value's base also takes the signed literal (+1 state). The tail-live configuration reads unary minus flat (two leaves where the tree has one), so the oracle declares it one-reading; the tail-inactive configuration passes. |
| G8 whole-value arms that are lists or compound values ERRORed | (a) | **fixed** `eb189bf`: an arm is `_property_value` itself. +85 states, 7 conflicts (2 removed). 12 shapes x 2 `;` placements pass in every configuration. tree-harness byte-identical on BC.History, BC 28.5, BCApps 29.0 and DC. |
| G8, `A.B` arm gets the table-relation shape | (c) | Flat `SourceTable = A.B;` gives the same `table_relation_value`. Not a defect. |
| G9 flat `CaptionML = ENU='c';` is `property_expression(comparison)` | (a), deferred | **New.** alc accepts it. Only the property name separates it from a comparison (`Visible = A = 'b';`), the `CalcFormula` situation. 0 production sites (all 6 ML files have two or more pairs). `docs/deferred-work.md` item 11; strict xfail in `test_table_relation.py`. |

Production sites of G7, G8 and G9: zero. The G7 and G8 fixes changed no production
tree (tree-harness byte-identical: BC.History and BC 28.5 for both; BCApps 29.0 and
DC as well for G8), and a grep for a property value that is a whole `#if` finds only
`Permissions`, which `preproc_conditional_permissions` handles.

## Exit table

| Exit item (spec "Exit, demonstrated") | Evidence |
|---|---|
| The quick tier has zero discrepancies | `python -m tools.config_oracle run --tier quick`: `0 unclassified findings`, `configurations checked: 668`, `pass: 523`, `cannot-validate: 145`, no `discrepancy` line |
| Replays 1 to 6 caught with their expected kinds; replay-4 HEAD control passes | `python -m tools.config_oracle replay`: `replay 1` to `replay 6 ... CAUGHT`; `pytest test_replay.py -m "slow or not slow"`: `test_replay_is_detected_as_specified[replay-1..6] PASSED`, `test_current_parser_passes_the_same_cases[head-1..6] PASSED` |
| The precedence self-test passes all 9 cases | `pytest tools/config_oracle/tests/test_precedence.py -v`: `test_there_are_9_cases PASSED` and 9 `test_recompose_matches_fixture[...] PASSED` |
| Every P2 to P5 type has a complete witness matrix and its mutations | `pytest tools/config_oracle/tests -q`: `432 passed, 14 deselected, 1 xfailed`; `-m slow`: `14 passed` |
| The resolve sweep over all four corpora is clean, or each exception classified | "Resolve sweep" above: 14,655 pass, 7 `reference-error` classified as invalid source |
| The P6 run is recorded, every cluster classified, every (a) fixed | This section: 8 production clusters (1 a, 2 b, 5 c), all (a) and (b) fixed; fixture findings G7 and G8 fixed, G9 deferred with measurements, G6 awaiting the user |
| `unsupported` remains only on types assigned to milestone 3 | `tools/config_oracle/contracts.py`: every `unsupported` entry names milestone 3 (`0bea280`); table below |

`./validate-grammar.sh`: every step green except Step 9, `Committed wasm is stale`.

## Registry state at exit

Types still `unsupported`, all milestone 3, with the configurations each blocks in
run 3 (configurations / files):

| Type | Run 3 | Milestone-3 note |
|---|---|---|
| `preproc_split_if_then_begin` | 138 / 46 | split-if family: one "prefix plus continuation" assembler |
| `preproc_split_if_else_statement` | 106 / 45 | split-if family |
| `preproc_split_declaration` | 62 / 25 | per-branch declaration header |
| `preproc_split_if_statement` | 30 / 15 | split-if family |
| `preproc_split_procedure_body` | 20 / 3 | procedure-tail pieces |
| `preproc_split_table_field_open` | 7 / 3 | BC 29 family D; the other configuration is invalid AL |
| `preproc_split_open_statement`, complete-prefix arms | 5 / 3 | split-if family (the else-led arm is one-reading) |
| `preproc_conditional_case_patterns` | 4 / 1 | |
| `preproc_split_code_block_over_endif` | 4 / 1 | |
| `preproc_split_if_then_begin_else_shared` | 4 / 2 | split-if family |
| `preproc_split_key` | 4 / 1 | BC 29 family E, per-branch header |
| `preproc_split_permissions_property` | 4 / 2 | head per branch, shared tail |
| `preproc_split_case_branch` | 2 / 1 | |
| `preproc_split_field` | 2 / 1 | |
| `preproc_split_brace_close` | 2 / 1 | |
| `preproc_guarded_statement` | 2 / 1 | |
| `preproc_split_modify` | 2 / 1 | BC 29 family E |
| `preproc_split_report_dataitem_header` | 2 / 1 | GB SalesShipment's third construct |
| `preproc_conditional_table_relation` in `table_relation_expression:<children>` (a host slot, not a type) | 2 / 1 | the arm must merge into the enclosing else chain |
| `preproc_conditional_impl_values`, `preproc_fragmented_else_tail`, `preproc_split_brace_close_if_only`, `preproc_split_call_statement`, `preproc_split_case_extended`, `preproc_split_complete_body`, `preproc_split_if_begin_asymmetric`, `preproc_split_if_begin_else`, `preproc_split_procedure_preamble`, `preproc_split_table_field` | 0 in production | registered, no production configuration reaches them |

Also open for milestone 3: the `case_else_branch` arm content (11 configurations),
and the one-reading configurations' other readings (10), which only a
configuration-aware parse can show.
