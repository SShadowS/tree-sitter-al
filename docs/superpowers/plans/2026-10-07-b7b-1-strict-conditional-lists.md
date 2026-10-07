# B7b-1: Conditional Groups in Strict Delimited Lists — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every admitted strict delimited list (implements, key/fieldgroup field lists, sorting and
order-by inner lists, move-modification elements, array dimensions, attribute arguments, variable
names) accepts `#if` groups at its separators with a correct, oracle-verified tree, while every
valid production tree stays identical.

**Architecture:** A route manifest freezes the target verdicts first. A grammar generator emits one
hidden seam unit and one visible `preproc_conditional_<family>` node per host; hosts convert one per
task. The config oracle gains a family-schema registry with pre-selection attachment validation and
complete-region separator checks. The B7a audit re-run proves every admitted cell against the frozen
manifest.

**Tech Stack:** tree-sitter 0.27 grammar DSL (`grammar.js`), C external scanner (`src/scanner.c`),
Python tools (`tools/b7_audit`, `tools/config_oracle`, `tools/perf`), alc 18.0.41 via `tools/alc_probe`.

**Spec:** `docs/superpowers/specs/2026-10-07-b7b-1-strict-conditional-lists-design.md` (rev 2). §N refers to it.

## Global Constraints

- Valid AL keeps its tree EXACTLY: four-corpus full cursor-tree parity (BC.History, DC, BC28.1,
  BCApps-29.0) including anonymous nodes, fields, spans, grammar names (§4.3).
- Expected trees of new and changed fixtures are HAND-WRITTEN from the flat reading, then checked
  against the 0.27 CLI — never copied from it (§4.3, §7). snip/py-tree-sitter 0.25 recovers errors
  differently from the 0.27 CLI (CLAUDE.md).
- Commit `src/parser.c`, `src/grammar.json`, `src/node-types.json` together; every commit ends with a
  measured `[BC.History: N errors, X% success]` trailer.
- Wrap every al.dll user in `./tools/ts-lock.sh`; `MSYS_NO_PATHCONV=1` for alc; Git Bash, Windows
  paths, never `2>nul`, never `find /`, no `git checkout --` / reset / stash drop.
- The frozen manifest is the gate: refreshing assertions may never redefine away a failed admitted
  cell or a new SILENT result (§2, §7).
- Field contract (§4.1): new item fields `multiple: true`, `required: false`; unfielded hosts stay
  unfielded; `_F_e`/`_F_list` never fielded wholesale.
- Budgets (STATE_COUNT, perf) are guidelines, not caps.
- After any parser/scanner/oracle change: `python -m tools.b7_audit assert --refresh`, full `run`,
  `report` before relying on the matrix.

## Review Focus

1. **A valid declaration whose only comma is conditional** (`A #if X , B #endif : Integer;`) must parse
   as one variable_declaration with both names (Task 11 test `test_only_comma_conditional`).
2. **A group in a move TARGET or before the fixed `;`** must not be accepted as an element group
   (Task 8 negative fixture `move target group stays ERROR`; Task 5 attachment validator).
3. **Escaped quote in an attributed variable name** (`[A] "X""Y", Z: Integer;`) must keep
   `var_attribute_open` (Task 12 test `test_attribute_escaped_quote_name`).
4. **Incremental edit after an unchanged attribute prefix** must give the fresh tree (Task 12 test
   `test_incremental_names_after_attribute`).
5. **Long and deeply nested conditional lists** must parse in near-linear time (Task 13 scaling
   benchmark with explicit limits).

---

## File Structure

- `grammar.js` — generator `strictConditionalList`, host conversions.
- `src/scanner.c` — variable-attribute recognizer (Task 12).
- `tools/b7_audit/manifest.py`, `tools/b7_audit/b7b1-manifest.tsv`, `tools/b7_audit/tests/test_manifest.py` (Task 1).
- `tools/alc_probe/cases/b7b1/` — new probes (Task 2).
- `tools/perf/parity.py` (+ `__main__` subcommand), `tools/perf/tests/test_parity.py` or the repo's perf test location (Task 3).
- `tools/config_oracle/lowering/conditional_lists.py` — family schema registry, pre-selection validation,
  region adapters, complete-region validator, rewrites; hooks in `engine.py`/`select.py`; `contracts.py`
  registrations; `tools/config_oracle/tests/test_conditional_lists.py` (Task 5, extended per host).
- `tools/check-field-types.py` — `required` dimension + new invariants.
- `traversal/policy.json` — classes for new node types.
- `test/corpus/strict_conditional_<family>_test.txt` — hand-written positive fixtures per host.
- `test/corpus/b7_gap_*_test.txt` — admitted witnesses removed/moved; excluded stay.
- Docs: CHANGELOG, `docs/deferred-work.md`, roadmap row B7, matrix.

## Host Conversion Procedure (HCP)

Each host task (6-11) runs these steps with the host's values from its task table.

1. **RED fixtures** — create `test/corpus/strict_conditional_<family>_test.txt` with HAND-WRITTEN
   expected trees (fields included) for: a group at each separator placement (sep-before, sep-after),
   separator-only arm, both-in-arm arm, first-element replacement, nested group, adjacent independent
   and complementary groups, empty arm, `//` and `/* */` comments at each boundary, `#if not`, plus the
   host's preservation shapes (plain list, quoted incl. escaped `""` and contextual-keyword elements,
   host inside an enclosing whole-declaration `#if`, list wholly inside one arm). Run
   `./tools/ts-lock.sh tree-sitter test --file-name strict_conditional_<family>_test.txt` → the
   conditional cases FAIL (ERROR), preservation cases PASS.
2. **Grammar** — replace the host's list with `...strictConditionalList($, '<family>', <atom>, '<sep>')`
   at the host's insertion boundary only; keep the host node, its delimiters and its other fields.
   `./tools/ts-lock.sh tree-sitter generate`; record STATE_COUNT, LARGE_STATE_COUNT, SYMBOL_COUNT,
   parser.c bytes, generation seconds, conflicts added (standalone and cumulative). If generate needs a
   conflict, add the narrowest one with a comment naming the two readings.
   *Superseded signature:* as shipped, the host inlines `...strictListBody($, '<family>', '<sep>')` and
   `...strictConditionalList('<family>', $ => <atom>, '<sep>'[, groupDynamic])` is spread into `rules`; see spec
   execution amendment 1 (`docs/superpowers/specs/2026-10-07-b7b-1-strict-conditional-lists-design.md`).
3. **GREEN** — the fixture file passes; `./tools/ts-lock.sh tree-sitter test` full suite passes (total
   moves by exactly the cases added).
4. **Field contract** — add `Invariant(...)` rows to `tools/check-field-types.py` for the new node's item
   field (`multiple=True`, `required=False`, `anon=set()`) and for the host field if it became optional;
   `python tools/check-field-types.py` passes; list API changes for the CHANGELOG in the task report.
5. **Traversal + coverage** — add `preproc_conditional_<family>` to `traversal/policy.json` (class
   `conditional-container`-style per the existing entries — read the file); `python tools/traversal_census.py`
   exit 0; `python -m tools.query_coverage.qc run` exit 0 or a justified `qc accept`.
6. **Oracle family** — register the family in `conditional_lists.FAMILIES` (Task 5 interface) with the
   task's region adapter, element kinds, separator, cardinality; add the family's mutation tests
   (attachment, field name, separator count, order, nesting, empty group, unselected arm, wrong outer-arm
   ownership, neighbouring nested region) and at least one LOWERED pass fixture per placement;
   `./tools/ts-lock.sh python -m pytest tools/config_oracle/tests -q` green; quick tier exit 0.
7. **Parity** — `./tools/ts-lock.sh python -m tools.perf parity --lib-a <main lib> --lib-b <branch lib> --corpus all`
   (Task 3) reports 0 differing files on all four corpora. Any difference stops the task.
8. **has_error** — `python tools/has_error_sweep.py --root` each corpus and `--corpus-fixtures` clean.
9. **Commit** grammar + generated files + fixtures + oracle + invariants, measured trailer.

---

### Task 1: Route manifest and checker

**Files:** Create `tools/b7_audit/manifest.py`, `tools/b7_audit/b7b1-manifest.tsv`,
`tools/b7_audit/tests/test_manifest.py`; modify `tools/b7_audit/__main__.py`.

**Interfaces:** Produces `manifest.load(path) -> list[Entry]` with
`Entry(cell_id, family, route_host, placement, disposition, reason, owner, frozen_vector, expected_verdict)`;
`manifest.check(entries, evidence_records, verdicts) -> list[str]` (problems); CLI
`python -m tools.b7_audit manifest --check [--manifest PATH]` exit 0/1/2.

- [ ] **Step 1: Tests (RED).** `test_manifest.py`: (a) an admitted entry whose current verdict differs
  from `expected_verdict` is a problem; (b) an excluded/deferred entry whose verdict changed is a problem
  unless the entry records the new verdict; (c) a frozen_vector mismatch with the evidence's alc vector is
  a problem; (d) a cell of a candidate family missing from the manifest is a problem; (e) header
  required. Run `./tools/ts-lock.sh python -m pytest tools/b7_audit/tests/test_manifest.py -q` → FAIL.
- [ ] **Step 2: Implement** `manifest.py` (TSV, header
  `cell_id\tfamily\troute_host\tplacement\tdisposition\treason\towner\tfrozen_vector\texpected_verdict`,
  dispositions `admitted|excluded|deferred`), wiring into `__main__` (`manifest --check`), reading the
  committed evidence/verdicts via `tools.b7_audit.evidence.read` and `report.analyse` (or `judge.verdict`).
- [ ] **Step 3: Generate the manifest** for families var-names, implements, move-modification,
  key-fields, sorting, order-by, array-dimensions, attribute-arguments, type-arguments from the committed
  evidence; apply spec §2's known dispositions verbatim (addfirst excluded; move cells whose group supplies
  or replaces the fixed `;` or the target excluded owner B7b-3; outer `order_by_list` excluded; sorting
  suffix cells and the B13 seed excluded owner B13; type-arguments deferred owner B7b-1g); admitted cells
  get `expected_verdict` CONSISTENT (or MIXED with the configuration-specific expectation where alc
  rejects some configurations); frozen_vector = the evidence's per-configuration alc acceptance.
  Write the generator as a scratch script (not committed); the TSV is the artifact.
- [ ] **Step 4:** tests GREEN; `python -m tools.b7_audit manifest --check` on the CURRENT tree must report
  every admitted cell as a problem (they are GAP today) — record that count in the report; this proves the
  check can fail.
- [ ] **Step 5: Commit** `feat(b7b-1): route manifest and checker`.

### Task 2: alc evidence for routes and var-name attributes

**Files:** Create `tools/alc_probe/cases/b7b1/*.al`; modify `tools/b7_audit/b7b1-manifest.tsv` (cardinality).

- [ ] **Step 1: Empty-interior probes** (§4.2), one file each, predicted `// expect:` then measured:
  `sorting()` via `SourceTableView = sorting();`, `ascending()` in OrderBy, `key(PK; )`, a fieldgroup with
  an empty list, `[A()]` and `[A]` attribute arguments, `array[]`, `implements` with nothing, a move with
  an empty element list. Record per route which §4.2 case applies (1-4) in the manifest's `reason`/`owner`
  fields and a `cardinality` note; classify syntax vs semantic codes (AL0104/AL0107/AL0111/AL0224/AL0125
  syntax; others semantic) with a compiling control per probe.
- [ ] **Step 2: Var-name attribute probes** (§5.1): attributed multi-name declarations with a group at
  each separator placement, separator-only group, group before the first name, nested group, `#elif`,
  adjacent groups, escaped-quote (`"X""Y"`) and Unicode/contextual names, malformed directive prefix,
  unterminated group, directives inside comments and quotes — and the procedure-attribute counterparts
  (`[A] procedure P()` under the same groups). Each with split and flat verdicts via `tools.alc_probe`.
- [ ] **Step 3:** `MSYS_NO_PATHCONV=1 ./tools/ts-lock.sh python -m tools.alc_probe run tools/alc_probe/cases/b7b1 --check`
  exit 0. Record the var-name conclusion (syntax-accepted shapes) in the report; Task 12 depends on it.
- [ ] **Step 4: Commit** `test(alc): B7b-1 route cardinality and var-attribute evidence`.

### Task 3: Tree-only parity over four corpora

**Files:** Create `tools/perf/parity.py`; modify `tools/perf/__main__.py`; test in the repo's perf test
location (read `tools/perf/` for it; create `tools/perf/tests/test_parity.py` if none).

**Interfaces:** Produces CLI `python -m tools.perf parity --lib-a A.dll --lib-b B.dll --corpus all|<label>...`
printing per corpus `files, differing` and listing differing paths; exit 0 when none differ, 1 otherwise,
2 when a library or corpus is missing. Reuses `ab.trees_identical` (`tools/perf/ab.py:64`) per file.

- [ ] **Step 1: Test (RED):** two tiny grammar libraries are not available in tests, so test with a fake
  `trees_identical`/loader injection: one corpus with a planted difference → exit 1 and the path listed;
  identical → exit 0; missing corpus root → exit 2.
- [ ] **Step 2: Implement** (no timing, all files of each corpus, parallel workers like `ab`).
- [ ] **Step 3: Base library helper:** document in the module docstring how to build main's library
  without touching the working tree (a throwaway `git worktree add` OUTSIDE the repo of `main`, compile
  `src/parser.c` + `src/scanner.c` with the loader's compiler command from
  `tools/query_coverage/loader.py`, remove the worktree after). Build it once now; record its path in the
  report for later tasks.
- [ ] **Step 4:** run `parity` main-lib vs main-lib on all four corpora → exit 0 (sanity).
- [ ] **Step 5: Commit** `feat(perf): tree-only parity over the four corpora`.

### Task 4: Generator spike on `implements`

**Files:** Modify `grammar.js` (new top-level function after `moveArgs`, `implements_clause`); create
`test/corpus/strict_conditional_implements_test.txt`; modify `tools/check-field-types.py` (add the
`required` dimension), `traversal/policy.json`.

**Interfaces:** Produces `strictConditionalList($, family, atom, sep)` returning an object of rules to
spread into `rules` — names `_<family>_list`, `_<family>_e`, `_<family>_t`, `preproc_conditional_<family>`,
`_<family>_b`, `_<family>_r`. Rule factories take `$`:

```js
// One hidden seam unit per strict delimited list (B7b-1 spec §3). `atom` is a function
// ($) => rule for ONE raw item, fielded as the host fields its items.
function strictConditionalList(family, atom, sep) {
  const L = `_${family}_list`, E = `_${family}_e`, T = `_${family}_t`,
        G = `preproc_conditional_${family}`, B = `_${family}_b`, R = `_${family}_r`;
  return {
    [L]: $ => seq($[E], repeat(seq(sep, $[E]))),
    [E]: $ => choice(seq(atom($), optional($[T])), $[T]),
    [T]: $ => seq($[G], optional($[E])),
    [G]: $ => seq(
      $.preproc_if, optional($[B]),
      repeat(seq($.preproc_elif, optional($[B]))),
      optional(seq($.preproc_else, optional($[B]))),
      $.preproc_endif),
    [B]: $ => choice(seq(sep, optional($[R])), $[R]),
    [R]: $ => seq($[E], repeat(seq(sep, $[E])), optional(sep)),
  };
}
```
(The rules object is spread into `rules: { ... }`: `...strictConditionalList('implements', $ => field('interface', $._identifier_or_quoted), ',')`.
If the DSL needs `$` at call time, adapt minimally and document it.)

- [ ] **Step 1: Extend `check-field-types.py`** with an optional `required` attribute on `Invariant`
  (checked against node-types.json's `required` when set); test by asserting a known required field and
  a known optional one; run `python tools/check-field-types.py` → pass.
- [ ] **Step 2..9:** run the **HCP** with: family `implements`; host `implements_clause`; insertion
  boundary = the interface list after `implements_keyword`; atom = `field('interface', $._identifier_or_quoted)`;
  sep `,`; host field `interface` may become `required: false` (record); oracle family registration is
  deferred to Task 5 (skip HCP step 6 here; note it).
- [ ] **Step 10: Spike report** — the generator's generate time, STATE_COUNT delta, conflicts; whether any
  seam property (§3) had to change and why. If the seam factoring needs refinement, change the generator
  here (once) and say how it preserves every §3 property.

### Task 5: Oracle family-schema infrastructure (with `implements`)

**Files:** Create `tools/config_oracle/lowering/conditional_lists.py`,
`tools/config_oracle/tests/test_conditional_lists.py`; modify `lowering/engine.py`, `lowering/select.py`
(hooks), `contracts.py` (registrations).

**Interfaces:** Produces `conditional_lists.FAMILIES: dict[str, Family]` with
`Family(name, host_kinds, region: Callable[[Node], tuple[int,int]] , item_kinds, sep, item_field,
cardinality: 'nonempty'|'empty-interior'|'optional-wrapper', recursive=True)`;
`validate_split(root) -> list[str]` (pre-selection attachment problems, §6.1);
`lower_region(host_node, lowered_children, family) -> list[Node]` (splice + complete-region alternation, §6.3);
rewrite note names `optional-list-removed:<kind>`.

- [ ] **Step 1: Tests (RED)** for `implements`: a LOWERED pass for each placement fixture of Task 4
  (select every configuration, compare with the flat parse); mutation tests each producing a discrepancy
  or a validation problem — moved group outside the region, group with a field, wrong separator count,
  swapped order, nesting in the wrong arm, empty group, unselected arm content leaking, wrong outer-arm
  ownership, neighbouring nested region. Run → FAIL.
- [ ] **Step 2: Implement** `validate_split` (pre-selection: permitted parent/slot, recursive self only,
  unfielded, span within region and enclosing arm, order and containment), `lower_region` (splice
  selected arms' items and separators, then validate `item (sep item)*` on the complete region only —
  a NEW validator, `_check_alternation` untouched for other families), the empty policy and the
  `optional-list-removed` rewrite; hook both into the lowering pipeline for registered families only.
- [ ] **Step 3:** register `preproc_conditional_implements` in `contracts.py`; family `implements` in
  `FAMILIES`.
- [ ] **Step 4:** tests GREEN; `python -m pytest tools/config_oracle/tests -q`; `python -m tools.config_oracle replay`
  exit 0; quick tier exit 0; full tier (`./tools/ts-lock.sh python -m tools.config_oracle run --tier full --root ./BC.History --root ./DC --root H:/Git/BC28.1 --root H:/Git/BCApps-29.0`) exit 0, 0 discrepancies.
- [ ] **Step 5: Commit** `feat(oracle): family-schema registry for strict conditional lists`.

### Task 6: Key and fieldgroup field lists

HCP with: family `field_list_items`; host `field_list` (visible, unfielded — keep) at call sites
`key_declaration`, `preproc_split_key`, `fieldgroup_declaration`, `addlast_fieldgroup_modification`;
**`addfirst_fieldgroup_modification` excluded** (manifest) — if the shared `field_list` change makes
addfirst accept groups, record it as a classified over-acceptance in the manifest and the report, not a
fix; atom = `$._identifier_or_quoted` (unfielded); sep `,`; region = `field_list` children; cardinality
per Task 2 (`key(PK; )` result). Extra fixture: a fieldgroup modification with a group.

### Task 7: Sorting and order-by inner lists

HCP twice. (a) family `sorting_fields`; host `sorting_value`'s inner list inside `sorting( … )` ONLY
(order/where suffixes untouched; no `field_list` wrapper); atom unfielded `$._identifier_or_quoted`; sep `,`.
(b) family `order_by_fields`; host `order_by_item`'s inner list inside `ascending( … )`/`descending( … )`
ONLY; the outer `order_by_list` untouched (excluded). Cardinality per Task 2 (`sorting()`, `ascending()`).
Extra fixtures: `SourceTableView = sorting(#if X K,N #endif) where(...)` with the suffix intact; a group
between two order_by_items stays ERROR (outer list excluded) — negative fixture listed in
deliberate-negatives.

### Task 8: Move-modification elements

HCP with: family `move_elements`; host `moveafter/movebefore/movefirst/movelast_modification` via
`moveArgs`; boundary = the element list AFTER the fixed `;`; atom = `field('element', $._identifier_or_quoted)`;
sep `,`; host field `element` may become optional. Negative fixtures (deliberate-negatives): a group
supplying the fixed `;` and a group replacing the target stay ERROR (`move target group stays ERROR`);
the attachment validator rejects a group in the target slot (oracle mutation test).

### Task 9: Array dimensions

HCP with: family `array_dimensions`; host `array_type`; boundary = the dimension list inside `[ ]`; atom =
the existing dimension item (read `array_type`, keep its field if any); sep `,`.

### Task 10: Attribute arguments

HCP with: family `attribute_args`; host `attribute_argument_list` (unfielded); boundary = the list inside
`attribute_arguments`' parentheses; atom = the existing argument item; sep `,`; cardinality
`optional-wrapper` (§4.2 case 2): an emptied configuration lowers with the `optional-list-removed:attribute_argument_list`
rewrite — oracle test with `[A(#if X 1 #endif)]` under X undefined.

### Task 11: Variable names (grammar)

HCP with: family `var_names`; host `variable_declaration`; merge the multi-name arm and the regular arm
into one ordinary-type arm over `_var_names_list` (label arm and TextConst arm unchanged); atom =
`field('name', $._identifier_or_quoted)`; sep `,`; region = names up to `:`. Tests: existing trees of every
valid declaration shape unchanged (preservation fixtures for single name, multi-name, label, TextConst,
quoted, attributed-without-groups), `test_only_comma_conditional` (Review Focus 1) as a corpus case.
Attributed declarations with groups depend on Task 12 — their fixtures are added there.

### Task 12: Variable-attribute recognizer (scanner)

**Files:** Modify `src/scanner.c` (the `var_attribute_open` lookahead ~900-935); fixtures
`test/corpus/strict_conditional_var_names_attr_test.txt`; pytest `tools/config_oracle/tests/test_var_attribute_scanner.py`.

- [ ] **Step 1: RED** — corpus cases (hand-written trees) pinning which node owns `[` for every shape
  Task 2 found syntax-accepted; `test_attribute_escaped_quote_name` (`[A] "X""Y", Z: Integer;`);
  a `has_error` pytest over the same; `test_incremental_names_after_attribute` (edit names/directives
  after an unchanged `[A]` prefix; fresh vs incremental full trees equal); procedure-attribute
  counterparts must keep their current trees. Run → FAIL.
- [ ] **Step 2: Implement** the recognizer per §5.2: a local peek from the `[` (mark_end before peeking,
  non-marking advances after, never touching `ScannerState.depth`) over `name` / `,` / balanced
  `#if`/`#elif`/`#else`/`#endif` lines (directive word read whole via `read_word_ci`, condition skipped to
  end of line, branch payload limited to names, commas, comments) ending at `:`; fail at `(`, `;`, `{`,
  `}`, a procedure keyword, EOF; quoted names honour escaped `""`. Shapes alc rejects as SYNTAX stay
  declined; semantic-only rejections are accepted (§5.1).
- [ ] **Step 3:** GREEN; full suite; `has_error_sweep` four corpora + fixtures; parity four corpora;
  incremental test.
- [ ] **Step 4: Commit** `feat(scanner): variable-attribute lookahead over conditional name streams`.

### Task 13: Audit re-run, witnesses, scaling and performance

- [ ] **Step 1:** `python -m tools.b7_audit assert --refresh`; full `MSYS_NO_PATHCONV=1 ./tools/ts-lock.sh python -m tools.b7_audit run --jobs 12`;
  `report`. `python -m tools.b7_audit manifest --check` → exit 0 (every admitted cell at its frozen
  expected verdict; excluded/deferred unchanged or as recorded). A failure is fixed at its cause, never
  by editing the manifest's frozen columns.
- [ ] **Step 2: Witnesses** — admitted `test/corpus/b7_gap_*` cases are removed (their shapes live in the
  hand-written `strict_conditional_*` fixtures); excluded cases stay `:error`; update
  `tools/deliberate-negatives.txt`, `tools/config_oracle/fixture-classes.tsv` (stale entries removed,
  new records classified), `tools/b7_audit/assertions.tsv` (rows for admitted cells rewritten to the
  true trees, fingerprints refreshed). Oracle quick tier exit 0.
- [ ] **Step 3: Incremental** — add `tools/config_oracle/tests/test_strict_lists_incremental.py`: per
  family, edits moving a separator into/out of an arm, deleting `#else`, adding/removing a group; fresh
  vs incremental full trees equal.
- [ ] **Step 4: Scaling** — a script under `tools/perf/` (committed, documented) generating synthetic
  files growing in list length (10…10,000 items) and nesting depth (1…20) per family, parsing with the
  branch library, asserting near-linear growth (time ratio per doubling < 2.5) and memory under a stated
  limit; record the table.
- [ ] **Step 5: Perf** — `./tools/ts-lock.sh python -m tools.perf ab --lib-a <main lib> --lib-b <branch lib> --corpus dc --rounds 24`,
  three runs; record ratios and CIs.
- [ ] **Step 6: Commit** evidence, matrix, assertions, witnesses, bookkeeping, scaling script.

### Task 14: Docs, WASM, final gates

- [ ] **Step 1: Docs** — CHANGELOG `[Unreleased]`: new node types, field API changes per host (fields now
  optional), the scanner change, the oracle families; `docs/deferred-work.md`: items for B7b-1b…g (with
  their witnesses and owners, incl. type-arguments B7b-1g and the move fixed-`;` cells B7b-3), item 1
  updated; roadmap row B7: B7b-1 DONE with numbers; CLAUDE.md: one paragraph on `strictConditionalList`
  and the family-schema registry (where, how to add a host).
- [ ] **Step 2: WASM** in its own commit: `./tools/ts-lock.sh tree-sitter build --wasm -o tree-sitter-al.wasm && tools/check-wasm-fresh.sh --update && tools/check-wasm-fresh.sh`.
- [ ] **Step 3: Final gates** — `./validate-grammar.sh --full` green; parity four corpora 0; manifest
  --check 0; `assert --refresh` 0; report byte-identical; oracle full tier 0 discrepancies; field
  invariants; traversal census; tree-sitter test total = previous + added − removed (state both).
- [ ] **Step 4: Commit** docs.
