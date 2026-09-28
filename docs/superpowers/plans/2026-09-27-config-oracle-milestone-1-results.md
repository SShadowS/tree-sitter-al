# Config oracle — milestone 1 results

Measured on 2026-09-28, grammar `61299ce05fb988e7` (report header; HEAD `1243f8c`,
branch `feat/config-oracle`). Corpora: BC.History `87e7d2a19d2`, DC `5e67e5b9c`,
BC 28.1 W1 `4fc2ccf16` (`H:/Git/BC28.1`, branch `bc28.1-w1`). Every run below was
wrapped in `./tools/ts-lock.sh`.

## Exit criteria (spec, Milestones item 1)

| Criterion | Result | Evidence |
|---|---|---|
| Replay 2 caught (structure) | CAUGHT | `replay 2 (bad36e4^, case_else_preprocessor_test.txt): CAUGHT`. Case `#2` (all 8 configs) carries `structure\|parent` and `structure\|missing` items; the record status is `directive-mismatch` because `end-extent` items ride along, but the comparison ran. |
| Replay 3 caught (structure) | **NOT MET as specified** | `replay 3 (f47350d^, scanner_lookahead_extras_test.txt): CAUGHT`, detected by `multi-config-parse:has-error@65`, **not by structure**. The pre-fix defect was CLI-silent (hidden MISSING token) but not API-silent: `has_error` is true, so the multi-config parse is rejected and the structure check never runs. The expected kind (structure) was not shown. |
| Replay 4 caught (directive-mismatch) | CAUGHT, with two qualifications | `replay 4 (c6b8107^, hand-built): CAUGHT` — `directive\|condition-extent\|preproc_if@86`. Input is hand-built and labelled (no pre-fix fixture exists). The HEAD positive control for this input is a strict xfail: `XFAIL test_current_parser_passes_the_same_cases[head-4] - needs preproc_conditional_expression_tail lowering (milestone 2)`. |
| Replay 5 caught by representation, NOT structure | CAUGHT | `replay 5 (04ff498^, preproc_split_procedure_tail_test.txt): CAUGHT` — both configs `representation-violation`, `var-block-without-var@116`, no structure item, structure ran. |
| No replay masked by cannot-validate | **NOT MET for replay 3** | Replays 2, 4, 5: no cannot-validate among the detecting records. Replay 3's only records (CLEAN22=0, CLEAN22=1) are `cannot-validate`; `replay.py` does not count them as masked because the has-error item *is* its detection, but under the spec's rule ("no earlier cannot-validate masks it") the structural detection was never reached. |
| Positive controls pass | MET except head-4 | `python -m pytest tools/config_oracle/tests -q`: `225 passed, 8 deselected in 2.09s`. `-m slow`: `7 passed, 225 deselected, 1 xfailed in 50.65s` (the xfail is head-4 above). |
| Resolver sweep: resolver-* cannot-validate | **0** | resolve-sweep summary: `pass: 5792`, `0 configurations not validated (none)`, exit code 0 |
| Resolver sweep: reference-error | **0** | same summary |
| Elapsed time, resolve sweep | 221.1 s inside `runner.run`; 5 m 26 s wall including corpus read and lock | summary `elapsed: 221.1s`; `time` wrapper `real 5m25.919s` |
| Peak memory, resolve sweep | 525 MiB (max over processes, not a sum) | summary `peak RSS (max over processes): 525 MiB` |
| Elapsed time and peak memory, quick tier | 0.6 s, 57 MiB (max over processes) | quick summary |

**Controller ruling on replay 3:** the controller accepted the has_error backstop as
replay 3's detection (the old defect was CLI-silent, not API-silent); the spec
criterion as literally worded stays NOT MET.

Verdict: milestone 1 exit **not fully met as literally worded** — replay 3 is detected
by the has_error backstop through a cannot-validate record rather than by structure
(accepted by the controller, above), and replay 4's HEAD control is an xfail until
milestone 2.

### Resolve sweep

```
./tools/ts-lock.sh python -m tools.config_oracle run --tier resolve \
  --root ./BC.History --root ./DC --root "H:/Git/BC28.1" \
  --report tools/config_oracle/reports/resolve-sweep
```

- 33,638 `.al` files: 31,252 without conditional directives, 2,386 with
  (BC.History 1,281 / BC 28.1 1,061 / DC 44), giving 5,792 configurations
  (3,120 / 2,580 / 92). Every one `pass`. File total checked against
  15,358 + 1,352 + 16,928.
- Discriminating-power control (the sweep being all-green needs one):
  `runner.check_input(..., mode="resolve")` on four synthetic inputs gives
  `#if A && B` → `resolver:unsupported-condition-token@55`; `#iff A` →
  `resolver:unknown-directive@49`; garbage in the active arm → A=1
  `reference-error:error@70,...`, A=0 `pass`; a clean `#if/#else` → both `pass`.
- No production file uses `&&`/`||` in a directive (grep over all three roots).

## Classified findings

### Resolve tier

None: zero non-pass records, so Step 2's grouping prints nothing.

### Quick tier — the 9 discrepancies

| Group | Count | Example | Classification | Action |
|---|---|---|---|---|
| `var_body` hosts `preproc_split_procedure` (split shape; the conditional shape of the same defect, 183 production nodes, is not yet visible to the oracle) | 8 | `preproc_interrupted_var_section.txt#0` CLEAN24=0; also `attribute_preproc_procedure.txt#0` (×2), `preproc_interrupted_var_section.txt#0..#2` (×2 each) | **(a) grammar defect** | `docs/deferred-work.md` item 8 |
| mid-file U+FEFF counted as uncovered | 1 | `scanner_single_read_dispatch_test.txt#3` CLEAN22=0, `coverage\|uncovered\|ref@148` and `low@148` | **(b) oracle defect** | follow-up below |

**Group 1 evidence.** In every configuration the multi-config tree (and hence the
lowered one) has `var_section [26-379] > var_body > preproc_split_procedure`, while
the reference has `var_section [26-110]` followed by sibling `attribute_item` and
`procedure` in `declaration_body`. The masked text of either configuration is a plain
var section followed by an (attributed) procedure. The multi-config tree is wrong in
the grammar, not in lowering: `var_body`'s `choice` lists `preproc_split_procedure`
directly, and the lowered tree only mirrors that. alc four-way probe on a
Integer-typed copy of the fixture: flat undefined ACCEPT, flat defined ACCEPT, split
undefined ACCEPT, split defined ACCEPT (sanity ACCEPT, garbage REJECT). One
production site: `BC.History/.../Shipping/ShippingAgent.Table.al:87`. The resolve tier
cannot see this (no lowering), which is why the sweep is clean. The same defect has a
second shape the quick tier cannot yet reach: `preproc_conditional_var` admits
`_body_element`, so a complete `#if … procedure … #endif` after a global `var` section
is also swallowed — 183 nodes (459 procedures) over the three corpora, reported as
`lowering:unsupported-type` because that type has no handler in milestone 1. Census,
examples and fix direction: deferred-work item 8.

**Group 2 evidence.** Byte 148 is a U+FEFF on its own line between a split `end;` and
`#else`. grammar.js:153 declares `/\uFEFF/` an `extra`; tree-sitter produces no node
for it, exactly like whitespace, so *both* sides leave it uncovered and agree.
`compare.coverage` exempts only a BOM at offset 0 (`lead`) and `_WS`, so a mid-file
BOM is counted significant. alc accepts the CLEAN22-undefined split file (probe
ACCEPT). Not a grammar or contract issue; related to deferred-work item 6 (the
doubled BOM), which leaves open what the CST *should* do with a non-leading BOM.

### Quick tier — resolver/reference cannot-validate (25 configurations, not classified here)

Recorded, not investigated in this task: these are fixture inputs, several
deliberately invalid (`*_negative_test`, `*_known_wrong_test`, word-boundary probes).

| Reason | Fixture files |
|---|---|
| `resolver:unknown-directive` (10) | `directive_word_boundary_test`, `preproc_if_elif_whitespace_tolerance_test`, `scanner_single_read_dispatch_test` |
| `reference-error:error` (9) | `preproc_begin_end_named_test`, `preproc_define_undef_test`, `preproc_if_elif_whitespace_tolerance_test`, `preproc_split_block_over_endif_test`, `preproc_split_brace_and_case_test`, `preproc_split_if_begin_outside`, `scanner_lookahead_extras_test` |
| `reference-error:missing` (6) | `preproc_split_brace_and_case_test`, `preproc_split_code_block_end_elif_test`, `preproc_split_layout_closing` |
| `resolver:trailing-token` (4) | `preprocessor_table_relation_test`, `table_relation_preprocessor_test` |
| `multi-config-parse:error` (3) | `preproc_if_elif_whitespace_tolerance_test`, `preproc_split_operator_negative_test` |
| `resolver:unsupported-condition` (1) | `preproc_dangling_operator_known_wrong_test` |

A reference-error on a configuration alc accepts would be a grammar defect; these
need the four-way probe before any is filed.

### Oracle follow-ups

1. **`compare.coverage` must treat every U+FEFF as trivia**, not only a leading one:
   grammar.js declares it an extra. Reproducer: `scanner_single_read_dispatch_test.txt#3`,
   CLEAN22=0 — `coverage|uncovered|ref@148` and `low@148` on an otherwise identical
   pair. Decide together with deferred-work item 6.
2. **Replay 3: spec text to be updated to match the ruling.** The spec's replay table
   says "structure"; the controller accepted the has_error backstop as replay 3's
   detection, so the table entry and the "no earlier cannot-validate" rule need a
   stated exception for replay 3.
3. Replay 4 HEAD control: `preproc_conditional_expression_tail` lowering (milestone 2).
4. `&&`/`||` in `#if`: grammar accepts, alc rejects (AL0631); the oracle reports
   `cannot-validate`. Grammar side filed as deferred-work item 9.

## Quick tier snapshot

`./tools/ts-lock.sh python -m tools.config_oracle run --tier quick --report tools/config_oracle/reports/quick`

- configurations checked: 589 — pass 246, discrepancy 9, cannot-validate 334; exit code 1
- inputs without conditional directives: 1,386
- cannot-validate: `lowering:unsupported-type` 301, `resolver:unknown-directive` 10,
  `reference-error:error` 9, `reference-error:missing` 6, `resolver:trailing-token` 4,
  `multi-config-parse:error` 3, `resolver:unsupported-condition` 1

Unsupported types (configurations), which order milestone 2–3 work:

| Count | Type | Count | Type |
|---|---|---|---|
| 56 | `preproc_conditional_object` | 4 | `preproc_conditional_layout` |
| 22 | `preproc_conditional_var` | 4 | `preproc_operand_prefix` |
| 20 | `preproc_conditional_actions` | 4 | `preproc_split_if_then_begin` |
| 18 | `preproc_conditional_permissions` | 4 | `preproc_split_call_statement` |
| 18 | `preproc_conditional_expression_tail` | 4 | `preproc_split_procedure_preamble` |
| 16 | `preproc_conditional_controladdin` | 4 | `preproc_split_procedure_body` |
| 10 | `preproc_split_if_statement` | 2 | `preproc_conditional_where` |
| 10 | `preproc_split_if_else_statement` | 2 | `preproc_conditional_case_patterns` |
| 10 | `preproc_conditional_xmlport` | 2 | `preproc_conditional_fields` |
| 8 | `preproc_conditional_fieldgroups` | 2 | `preproc_split_else_begin_over_endif` |
| 7 | `preproc_split_if_begin_asymmetric` | 2 | `preproc_conditional_labels` |
| 6 | `preproc_split_declaration` | 2 | `preproc_conditional_rendering` |
| 6 | `preproc_split_code_block_over_endif` | 2 | `preproc_conditional_option_members` |
| 6 | `preproc_split_if_then_begin_else_shared` | 2 | `preproc_conditional_list_elements` |
| 6 | `preproc_split_complete_body` | 2 | `preproc_split_report_dataitem_header` |
| 6 | `preproc_conditional_table_relation` | 2 | `preproc_split_case_extended` |
| 6 | `preproc_conditional_link_values` | 2 | `preproc_split_field` |
| 4 | `preproc_conditional_case` | 2 | `preproc_split_table_field` |
| 4 | `preproc_conditional_keys` | 2 | `preproc_split_if_begin_else` |
| 2 | `preproc_split_brace_close_if_only` | 2 | `preproc_conditional_dataset` |
| 2 | `preproc_guarded_statement` | 2 | `preproc_conditional_report` |
| 2 | `preproc_conditional_layout_mixed` | 1 | `preproc_split_report_dataitem_open_over_endif` |
| 1 | `preproc_split_report_brace_close` | | |

Production parse at the same HEAD: `./parse-al-parallel.sh ./BC.History/ .` —
15,358 / 15,358 parsed, 0 errors, 100.0%.
