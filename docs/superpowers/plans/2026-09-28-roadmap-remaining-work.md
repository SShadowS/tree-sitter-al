# Roadmap: the remaining open work (from 2026-09-28)

This roadmap sequences every open item into sub-projects. It is not a task-level
implementation plan. Each sub-project below gets its own cycle: a design, a spec
where the work is architectural or changes the public tree, then a task plan and
reviewed execution, the way milestone 2 and G6 were done.

**The sources:**
- `docs/deferred-work.md`: items 1-4, 6, 7, 9-16, and the longer-lived proposals;
- the oracle registry (`tools/config_oracle/contracts.py`): the types still `unsupported`;
- the milestone-2 results document;
- the release checklist in `CHANGELOG.md` `[Unreleased]`.

**The goal:** a parser that parses AL *correctly*. That means no ERROR on valid AL,
no silent wrong tree, and node types and fields that tell the truth. The oracle
must be able to prove this over production code and gate on it.

## Ordering principles

1. **Gates before grammar.** Item 12 showed a class of defect that every
   command-line gate misses. Grammar work done before that gate exists can hide a
   regression. Automating the four-way alc probe (item 7) also makes every later
   grammar fix cheaper to verify.
2. **Silent wrong trees before ERRORs.** A silent misparse survives every error
   count, and an ERROR at least announces itself. Within each class, production
   sites come first.
3. **Settle the tree shape before optimising it.** State reduction comes after the
   grammar changes, so it is not redone.
4. **Oracle coverage follows grammar stability.** Lowering a node type that is
   about to change shape is wasted work.
5. **Architecture projects come last.** They build on everything before them.

## Phase A: gates and instruments

| # | Sub-project | Items | Kind | Exit, demonstrated |
|---|---|---|---|---|
| A1 | **`has_error` sweep gate.** It fails on any file whose `root_node.has_error` is true with no visible ERROR/MISSING, and runs in `validate-grammar.sh --full` and CI. It also fixes the `parse-al-parallel.sh` comment. | 12 | bounded | A mutation that re-introduces a hidden MISSING, such as reverting `_directive_eol`'s whitespace loop, fails the gate. All four corpora are clean. |
| A2 | **Split-matrix probe tooling.** The four-way alc compile (symbol defined and undefined, flat and split) is a tool under `tools/`, with its own self-test. It builds on `tools/config_oracle/probe_alc.py`. | 7 | bounded | It reproduces the recorded verdicts of existing probes (the BC 29 families, G11). A deliberately broken probe project is reported as broken, not as a rejection. |
| A3 | **Production classification file.** A classification file for `--tier resolve` and `--tier full`, keyed like `fixture-classes.tsv`, holding the 7 BCApps invalid-source records and the unsupported-type records. | 14 | bounded | A clean production run exits 0. A new unclassified record exits 1. A stale entry fails the run. |

## Phase B: grammar correctness

Order within the phase: silent wrong trees, then ERRORs on valid AL, then decisions.

| # | Sub-project | Items | Kind | Notes |
|---|---|---|---|---|
| B1 | **Dangling-operator residual.** `#if FOO and` with its operand on the next line is absorbed into the condition, a silent wrong tree that alc rejects (AL0629). The fixture asserts the defect as a tripwire. | 3 | bounded | The fix must flip the tripwire fixture deliberately, with its header updated. |
| B2 | **Separator hosts.** These positions have no host yet: `parameter_list` (`;`-led), `implements_clause`, the comma-leading `option_member_list`, the comma-leading `link_value_list` (G11 review reproducer), the key field list, and `ml_value_list`. Each host needs BOTH comma placements pinned (item 2). | 1, 2 | bounded per host, one plan | Use A2 for every probe. Oracle list-run witnesses go in for each host. |
| B3 | **G9: a one-pair ML value.** `CaptionML = ENU='c';` parses as a comparison; alc accepts it. The fix is property-name keying, which CLAUDE.md says not to generalise lightly. | 11 | **architectural: spec** | This needs a decision: a name-keyed scanner token for the ML property family (the `CalcFormula` route), or a value-shape rule if one can be found. The spec must enumerate the ML property names from the BC docs and justify why keying on names is correct here. |
| B4 | **Dotted references and G10.** `Visible = Rec.A;` is a `table_relation_value` with `table:` fields, and `Visible = Rec.A #if X and B #endif ;` ERRORs. | 13, 15 | **architectural: spec, tree-shape change** | This is a property-grammar redesign: one neutral representation for an ambiguous dotted reference that the flat and split forms both give. Alternatives: a neutral node, contextual keying, or letting the expression reading win. It needs production-site counts and a migration note. |
| B5 | **CalcFormula whole-value conditional.** `CalcFormula = #if X sum(T.A) #else count(T) #endif;` | 16 | bounded | First, alc-probe that this is valid. The arms must stay formula-shaped (`aggregate_formula` / `lookup_formula`), not `_property_value`. |
| B6 | **Doubled BOM.** A second UTF-8 BOM at offset 3 is claimed by no node. | 6 | bounded | Probe alc first. Its verdict decides between absorbing the BOM as an extra and surfacing it as text. |
| B7 | **Decision: `&&` / `\|\|` in `#if`.** The grammar accepts them and alc rejects them (AL0631). | 9 | decision | Options: keep (parse structure, don't validate) and close the item, or remove the two string alternatives. |
| B8 | **Decision and research: `_expression_statement`.** It accepts any expression as a statement. Two narrowing attempts dropped BC.History to about 35%. The unexplored lead is the `inline` array. | 4 | research, then decision | First decide whether narrowing is in scope under "parse structure, don't validate". The bare-literal statement is invalid AL, but the tree does not misrepresent it. |

## Phase C: size

| # | Sub-project | Kind | Exit |
|---|---|---|---|
| C1 | **State-reduction pass** over the split and whole-value rules added since 4.0.0. STATE_COUNT went 14,060 → 15,870; `parser.c` is 38.8 MB. Apply the methods in memory `feedback_preproc_rule_extraction`: measure each rule's marginal cost by stubbing it, factor complete-unit hidden rules, share repeat symbols, and never use `prec` to break GLR. | bounded, measurement-driven | tree-harness byte-identical on both corpora, the oracle quick tier unchanged, `node-types.json` byte-identical, and a recorded reduction. There is no target number: stop when the next candidate costs more than it saves. |

## Phase D: the oracle to a full gate

Base spec milestones 3-5, updated by what milestone 2 learned.

| # | Sub-project | Kind | Exit |
|---|---|---|---|
| D1 | **Milestone 3:** lowering for every remaining `unsupported` type. The first items are:<ul><li>the split-if family (`preproc_split_if_statement`, `preproc_split_if_else_statement`, and the complete arms of `preproc_split_open_statement`, sharing one "prefix + continuation" assembler);</li><li>`preproc_split_procedure_body` / `_complete_body`;</li><li>`preproc_split_report_dataitem_header` (which blocks the GB SalesShipment report);</li><li>`case_else_branch` inside `preproc_conditional_case`;</li><li>the split-header family (`preproc_split_key`, `preproc_split_modify`, `preproc_split_permissions_property`, `preproc_split_field`, `preproc_split_table_field(_open)`, `preproc_split_declaration`);</li><li>the rest by production frequency.</li></ul> | architectural: spec (an amendment of the milestone-2 kind) | No `unsupported` registry entries remain. Every type has its witness matrix and mutations. The base-spec deterministic transformations pass. The production run's cannot-validate count is only one-reading and invalid-source records, each classified (A3). |
| D2 | **Milestone 4:** the quick tier becomes a mandatory gate (validate-grammar Step 5e, CI, `gate_selftest` cases). | bounded | The quick tier runs with 0 discrepancies, 0 cannot-validate and no classification file, and every gate-integration failure mode is tested. |
| D3 | **Milestone 5:** the full tier as a staged gate over BC.History, DC, BC28.1 and BCApps 29.0, with an exact-id baseline and Step 6b. After that, update CLAUDE.md with the oracle's contract and its limit (both parses share one grammar). | bounded | Every (file, configuration) is accounted for. Every discrepancy is investigated. Grammar defects are fixed in their own commits, and the baseline is empty. |

## Phase E: architecture

| # | Sub-project | Items | Kind |
|---|---|---|---|
| E1 | **A configuration-aware parse:** parse each configuration and merge the trees. This is the general answer to constructs that cross the `#if` ranges, which the grammar now covers one reading at a time. It fixes EDocumentDE without the measured +835 to +2,270 states. It reuses the oracle's resolver. | 10, the one-reading contracts | **architectural: brainstorm, then spec.** It changes what the parser's output is, and so likely needs a separate API or layer alongside the CST rather than inside it. |

## Phase F: release and packaging

These can be done at any phase boundary. Phase A's end is the natural first
release point, because `[Unreleased]` already holds tree-shape changes G1-G8, G6,
G11 and P1.

| # | Item |
|---|---|
| F1 | **Consolidate the CHANGELOG.** Review each Tree-shape entry and each migration note (G6's in particular). |
| F2 | **Version bump.** The CHANGELOG declares node and field structure public API, so G1-G8, G6 and P1 make this a **major** release. |
| F3 | **Rebuild the WASM** (validate-grammar Step 9), then push `main` (about 125 commits ahead of origin) and tag. |
| F4 | **Python bindings modernisation** (`docs/python-bindings-modernization.md`): `PyCapsule` for tree-sitter 0.24+. |
| F5 | **Reconcile `docs/improvements-for-owned-ir-consumer.md`** against the current `node-types.json`, and close stale items. |

## Decisions needed from you

1. **B3 (G9):** do you accept property-name keying for the ML property family, the CalcFormula precedent? The spec will lay out the alternatives, but the principle needs your yes or no.
2. **B4:** the representation of an ambiguous dotted reference is a tree-shape choice. It goes in a spec for your approval.
3. **B7 (`&&`/`||`):** keep them and close the item, or remove them?
4. **B8 (`_expression_statement`):** is narrowing it in scope?
5. **F2/F3:** release timing. Is Phase A's end the first release point, and do you want to push before it?

## The proposed order

A1 → A2 → A3 → B1 → B2 → B3 → B4 → B5 → B6 → (B7, B8 decisions) → C1 → D1 → F1-F3 (release)
→ D2 → D3 → E1 → F4, F5.

Once A2 exists, B5 and B6 are small and can go in either order. B3 and B4 each wait for their spec
approval, and the phase can continue past them while a spec is under review.
