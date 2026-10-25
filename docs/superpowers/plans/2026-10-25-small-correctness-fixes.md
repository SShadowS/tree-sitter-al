# Small correctness fixes (empty-`#else` tail, items 61, 62) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Three inputs alc accepts and the parser ERRORs on get correct trees, with no other tree changing.

**Architecture:** Each fix is a small grammar change at the rule that lacks the shape, pinned by field-labelled
fixtures generated from CLI `tree-sitter parse` output and by a committed alc probe; the gap witnesses move to the
fixed side; the oracle and audit follow.

**Tech Stack:** tree-sitter 0.27 grammar (`grammar.js`), py-tree-sitter gates, `tools/config_oracle`, `tools/b7_audit`, `tools/alc_probe`.

**Spec:** none separate; agreed in chat 2026-10-25 ("go ahead"). The binding contract is CLAUDE.md, `docs/expression-regions.md` (the B7b-2 region contract) and the deferred-work items named below.

## Global Constraints

- Correctness first (user decision): no valid input's tree may change except the fixed inputs; `node-types.json` changes only by what each fix needs, each change justified.
- Ceilings are strong preferences, reported when crossed: STATE ≤ 28,770, LARGE ≤ 10,723, parser.c ≤ 80 MiB. Current (main c89c2ec): 26,968 / 9,389 / 61,703,620 B.
- Speed: no regression, `python -m tools.perf ab` two 24-round runs per corpus (dc, bc-history), each ≥ 0.97, `ab_accept` passes (never wrap `ab` in ts-lock) (amended 2026-10-25 by user decision: screen rule in docs/agent-brief-rules.md 'Gate tiers'; bc-history passed its 8-round screen at 1.003, so no 24-round runs or ab_accept).
- Every fix: fixture(s) from CLI output with fields, proven to fail with a `bogus:` field rename; the gap witness moved from `:error` to a tree; `tools/deliberate-negatives.txt` updated; `tools/config_oracle/fixture-classes.tsv` classified; four-corpus `python -m tools.perf delta` shows 0 changed files; `python tools/has_error_sweep.py` clean as before; `./validate-grammar.sh` passes; `census --check` 0; `assert --refresh` 0 unexplained flips.
- Never `tree-sitter test -u`; Edit/Write only on tracked files; commit trailer `[BC.History: N errors, X% success]`.

## Review Focus

- A fix that adds an empty arm must not let an empty group stand where alc rejects it (a lone `#if X #endif` tail with nothing at all is already a decoration case — check it is not newly read as a tail).
- The unary-only arm (`#if X - #endif 1`) must bind as unary over the following operand in that configuration, by the §3 ladder, not as a binary with a missing left.
- The property prefix-plus-tail fix must keep `property.value` single (`tools/check-field-types.py`).

---

### Task 1: A tail whose `#else` arm is empty

**Input (issue #38 variant, alc ACCEPT both configurations, probe in the controller's scratchpad `p38/empty-else-tail.al`):**
`until (A > 10) #if LETHALX or (B > 5) #else #endif ;` and `x := a #if X + b #else #endif ;` (directives on their own lines). Today both ERROR (`#end` in an ERROR).

- [ ] Commit the probe under `tools/alc_probe/cases/b7b-2/tails/empty-else-tail.al` with `// expect:` and `// source: issue #38` headers; `--check` clean.
- [ ] RED fixture `test/corpus/b7b2_tail_empty_else_test.txt`: the assignment, `repeat … until`, `while … do`, an `#elif` with an empty `#else`, and a call argument; expected trees per `docs/expression-regions.md` (the empty arm is an arm of `preproc_conditional_expression_tail` with no members). Run: fails.
- [ ] Grammar: allow an empty `#else` (and `#elif`) arm in the tail's arm list. Generate, metrics.
- [ ] GREEN; full suite count moved by exactly the cases added; the oracle lowering accepts an empty arm (add/extend a `tools/config_oracle/tests/test_regions.py` case per configuration).
- [ ] Gates (Global Constraints); commit `fix(b7b-2): a tail's #else arm may be empty (issue #38)`.

### Task 2: Item 61 — an arm that is only a unary operator

Read `docs/deferred-work.md` item 61 for the witnesses, probe and mechanism.

- [ ] RED fixture from item 61's witnesses (`x := #if X - #endif 1;`, `B := Ok and #if X not #endif Ok;`, `if #if X not #endif a then;`) with trees per the region contract; move the `:error` witnesses out of `test/corpus/b7b2_unary_op_only_gap_test.txt`.
- [ ] Grammar at the prefix rule; generate, metrics; GREEN.
- [ ] Oracle: the leading-prefix lowering handles a unary-only arm (test per configuration).
- [ ] Gates; close item 61 in deferred-work with the fixture; commit `fix(b7b-2): an operand prefix may be a unary operator alone (item 61)`.

### Task 3: Item 62 — a property value with a leading prefix and a tail

Read `docs/deferred-work.md` item 62 (cause: `property_expression`'s leading-prefix arm lacks the tail).

- [ ] RED fixture: the action `Visible = #if X Ok and #endif Ok #if Y or Ok #endif;` from the committed probe `tools/alc_probe/cases/b7b-2/prefixes/property-prefix-then-tail.al`; move its `:error` witness.
- [ ] Grammar: the likely fix `optional($.preproc_conditional_expression_tail)` on that arm; generate, metrics; GREEN.
- [ ] Gates; close item 62; commit `fix(b7b-2): a prefixed property value may take a tail (item 62)`.

### Task 4: Close-out

- [ ] Full gates once: `./validate-grammar.sh --full`, the full B7a `run` + `report` (byte-identical), `--tier full` oracle 0 discrepancies, `ab` per Global Constraints vs main c89c2ec, WASM rebuild + `tools/check-wasm-fresh.sh`.
- [ ] CHANGELOG `[Unreleased]` entries with old/new trees; deferred-work items 61/62 closed; commit `docs: small correctness fixes (issue #38 empty #else tail, items 61, 62); wasm`.
