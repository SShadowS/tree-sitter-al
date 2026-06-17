# Query-Ergonomics Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the structural/field-naming/node-type decisions that hurt query authors, textobject support, and code navigation — the siblings of GitHub issue #19, plus gaps the #19 fix itself created.

**Architecture:** Continue the #19 convention — every scoped construct exposes its content as a single node via a `body` field, and positional children that consumers target get explicit field names. Introduce one shared `statement_block` content node (analogous to `object_body`) so code blocks, `repeat` loops, and preprocessor-split bodies all expose content the same way.

**Tech Stack:** tree-sitter grammar DSL (`grammar.js`), C external scanner (`src/scanner.c` — not touched here), corpus tests (`test/corpus/*.txt`), BC.History production parse gate (15,358 files).

---

## Background: what we're fixing

From the issue #19 retrospective + Gemini 3.1 Pro cross-check, ranked:

| # | Problem | Root cause | Action |
|---|---------|-----------|--------|
| 1 | `repeat_statement` has no `body` field (every other loop does) | flat statement list | Task 4 |
| 2 | `case_statement` branch list is flat/unnamed | flat list | Task 2 |
| 3 | `parameter_list` has no `parameters` field (proc/trigger/event) | missing field | Task 1 |
| 4 | preproc-split statement bodies are flat | coverage gap from #19 | Task 5 |
| 5 | `code_block` keeps begin/end inside + reused | delimiters-inside, no content node | Task 3 |
| 6 | `var_section` has no body wrapper | flat list | Task 6 |
| 7 | `case` `end` uses anonymous `kw('end')` not named `end_keyword` | keyword exposure inconsistency | Task 7 |
| 8 | `object_body` node type reused for non-objects (misleading name) | naming | Task 8 (cosmetic) |
| 9 | attributes are siblings, not attached | deliberate design | Task 9 (decision, no code) |
| 10 | empty body → no node; single-statement body → no block node | tree-sitter limitation | Task 10 (docs only) |

**NOT in scope / non-issues:**
- A body-bearing **supertype** is unnecessary — the uniform `body` field already enables the one generic query `(_ body: (_) @inside)`. No action.
- Gemini's proposed empty-body "fix" (`repeat` instead of `repeat1`) is **invalid** — tree-sitter rejects named rules that match the empty string (`"The rule X matches the empty string"`). The `optional(field('body', …))` + `repeat1` pattern is the only correct shape. Documented in Task 10.

## Repo-specific verification loop (used by every task)

This repo has **no unit-TDD**; the equivalent of "write the failing test" is: parse a sample and observe the CURRENT (wrong) tree, change the grammar, then observe the corrected tree. The hard gate is corpus tests + BC.History.

Standard cycle per grammar change:
1. `tree-sitter generate` — must exit 0; watch for unresolved-conflict errors.
2. `tree-sitter parse /tmp/<sample>.al` — confirm the new field/node appears, no `(ERROR)`/`(MISSING)`.
3. `tree-sitter test 2>&1 | grep -oE '\((ERROR|MISSING)'` — must be empty.
4. `tree-sitter test -u` — update corpus expectations (ONLY after step 3 is clean).
5. At milestones: `./parse-al-parallel.sh ./BC.History/ .` — must stay **0 errors, 15,358/15,358**.

**Conflict protocol:** if `tree-sitter generate` reports an unresolved conflict for a new `*_block`/`*_body` rule, add a single-rule entry `[$.<rule>]` to the `conflicts` array (`grammar.js:106`) with a one-line comment, then regenerate. If the conflict cascades (more than one new entry needed, or state count balloons >2%), STOP and revert that task — note it as needing design review.

**Commit convention (from CLAUDE.md):** stage `grammar.js src/parser.c src/grammar.json src/node-types.json` together (+ tests/queries/docs). Commit message MUST include the BC error count, e.g. `[BC.History: 0 errors, 100% success]`.

---

## Task 1: Add `parameters` field to procedure / trigger / event

**Files:**
- Modify: `grammar.js` — `_procedure_name_and_params` (~2447), `trigger_declaration` (~2629), `event_declaration` (~2409)

Lowest risk, highest ergonomic value (`@parameter` textobjects, tags). `_procedure_name_and_params` is shared by `procedure` and `interface_procedure`, so one edit covers both.

- [ ] **Step 1: Observe current tree (no field)**

Run: `printf 'codeunit 1 C { procedure P(x: Integer; var y: Text) begin end; }\n' > /tmp/param.al && tree-sitter parse /tmp/param.al`
Expected: a bare `(parameter_list …)` child with NO `parameters:` field label.

- [ ] **Step 2: Edit `_procedure_name_and_params`**

```javascript
    _procedure_name_and_params: $ => seq(
      field('name', $._identifier_or_quoted),
      '(',
      optional(field('parameters', $.parameter_list)),
      ')',
    ),
```

- [ ] **Step 3: Edit `trigger_declaration` parameter line**

Change `      optional($.parameter_list),` to:
```javascript
      optional(field('parameters', $.parameter_list)),
```

- [ ] **Step 4: Edit `event_declaration` parameter line**

Change `      optional($.parameter_list),` to:
```javascript
      optional(field('parameters', $.parameter_list)),
```

- [ ] **Step 5: Generate + verify field appears**

Run: `tree-sitter generate && tree-sitter parse /tmp/param.al | grep -E 'parameters:|ERROR'`
Expected: `parameters: (parameter_list …)` present, no `ERROR`.

- [ ] **Step 6: Corpus check + update**

Run: `tree-sitter test 2>&1 | grep -oE '\((ERROR|MISSING)'` (expect empty), then `tree-sitter test -u`.

- [ ] **Step 7: Commit**

```bash
git add grammar.js src/parser.c src/grammar.json src/node-types.json test/corpus
git commit -m "feat(grammar): add parameters field to procedure/trigger/event

[BC.History: not yet re-run — gate at Task 3 milestone]"
```

---

## Task 2: Wrap `case_statement` branches in a `case_body` node

**Files:**
- Modify: `grammar.js` — `case_statement` (~2350)

- [ ] **Step 1: Observe current flat tree**

Run: `printf 'codeunit 1 C { procedure P() begin case i of 1: x:=1; 2: x:=2; end; end; }\n' > /tmp/case.al && tree-sitter parse /tmp/case.al | grep -E 'case_statement|case_branch|case_body'`
Expected: `case_branch` nodes are direct children of `case_statement`; NO `case_body`.

- [ ] **Step 2: Edit `case_statement` + add `case_body`**

```javascript
    case_statement: $ => prec(2, seq(
      $.case_keyword,
      field('expression', $._expression),
      $.of_keyword,
      optional(field('body', $.case_body)),
      optional($.case_else_branch),
      kw('end')
    )),

    case_body: $ => repeat1(choice(
      $.case_branch,
      $.preproc_conditional_case,
      $.preproc_split_case_extended,
    )),
```

- [ ] **Step 3: Generate (watch for conflict)**

Run: `tree-sitter generate; echo EXIT=$?`
Expected: `EXIT=0`. If unresolved conflict mentions `case_body` vs `case_else_branch`, add `[$.case_body]` to `conflicts` (`grammar.js:106`) with comment `// case_body branch list vs trailing case_else_branch`, then regenerate.

- [ ] **Step 4: Verify body node**

Run: `tree-sitter parse /tmp/case.al | grep -E 'case_body|ERROR'`
Expected: `body: (case_body …)` wrapping the branches, no `ERROR`.

- [ ] **Step 5: Corpus check + update**

Run: `tree-sitter test 2>&1 | grep -oE '\((ERROR|MISSING)'` (expect empty), then `tree-sitter test -u`.

- [ ] **Step 6: Commit**

```bash
git add grammar.js src/parser.c src/grammar.json src/node-types.json test/corpus
git commit -m "feat(grammar): wrap case branches in case_body for textobjects

[BC.History: gate at Task 3 milestone]"
```

---

## Task 3: Extract `statement_block` content node inside `code_block`

**Files:**
- Modify: `grammar.js` — `code_block` (~2613)

This is the linchpin: `statement_block` becomes the reusable content-only node (no `begin`/`end`) that Tasks 4 and 5 also use. `code_block` keeps `begin`/`end` (it is still reused as a nested statement block), but now exposes its statements via a `body` field. Highest-risk task — `code_block` is referenced in routines, if/else, all loops, and case branches.

- [ ] **Step 1: Observe current tree (begin/end inside, flat statements)**

Run: `printf 'codeunit 1 C { procedure P() begin x:=1; y:=2; end; }\n' > /tmp/blk.al && tree-sitter parse /tmp/blk.al | grep -E 'code_block|statement_block'`
Expected: `code_block` contains `begin_keyword`, the statements, `end_keyword` — NO `statement_block`.

- [ ] **Step 2: Edit `code_block` + add `statement_block`**

```javascript
    code_block: $ => prec.right(seq(
      choice($.begin_keyword, kw('begin')),
      optional(field('body', $.statement_block)),
      choice(
        seq(choice($.end_keyword, kw('end')), optional(';')),
        $.preproc_split_code_block_end,
      ),
    )),

    // Content-only statement run (no begin/end). Shared by code_block,
    // repeat_statement, and preprocessor-split bodies so every statement
    // container exposes its inside as a single node. repeat1 (tree-sitter
    // forbids empty-matching rules) → wrap in optional() at each use site.
    statement_block: $ => repeat1($._statement),
```

- [ ] **Step 3: Generate (watch for conflict with preproc_split_code_block_end)**

Run: `tree-sitter generate; echo EXIT=$?`
Expected: `EXIT=0`. Likely conflict: `statement_block` reduction vs entering `preproc_split_code_block_end` (both follow the statement run). If reported, add `[$.statement_block]` to `conflicts` with comment `// statement_block vs preproc_split_code_block_end after the statement run`, regenerate. If state count grows >2% (`grep STATE_COUNT src/parser.c` before/after) or conflict cascades, STOP and revert — escalate for design review.

- [ ] **Step 4: Verify nested body node**

Run: `tree-sitter parse /tmp/blk.al | grep -E 'statement_block|ERROR'`
Expected: `code_block` now has `body: (statement_block …)`, begin/end remain code_block children, no `ERROR`.

- [ ] **Step 5: Corpus check + update**

Run: `tree-sitter test 2>&1 | grep -oE '\((ERROR|MISSING)'` (expect empty), then `tree-sitter test -u`.

- [ ] **Step 6: MILESTONE — full BC.History gate**

Run: `./parse-al-parallel.sh ./BC.History/ .`
Expected: `Errors : 0`, `Parsed OK : 15358`. If any errors, inspect with `tree-sitter parse <failing-file> 2>&1 | grep -E 'ERROR|MISSING'` and fix before committing.

- [ ] **Step 7: Commit (Tasks 1–3 verified against BC.History)**

```bash
git add grammar.js src/parser.c src/grammar.json src/node-types.json test/corpus
git commit -m "feat(grammar): extract statement_block content node in code_block

Exposes code block statements via a body field (no begin/end), the
reusable content node for repeat/preproc-split bodies.

[BC.History: 0 errors, 100% success]"
```

---

## Task 4: Give `repeat_statement` a `body` field via `statement_block`

**Files:**
- Modify: `grammar.js` — `repeat_statement` (~3444)

- [ ] **Step 1: Observe current flat tree**

Run: `printf 'codeunit 1 C { procedure P() begin repeat x:=1; until done; end; }\n' > /tmp/rep.al && tree-sitter parse /tmp/rep.al | grep -E 'repeat_statement|statement_block|body:'`
Expected: statements are direct children of `repeat_statement`; no `body`.

- [ ] **Step 2: Edit `repeat_statement`**

```javascript
    repeat_statement: $ => seq(
      $.repeat_keyword,
      optional(field('body', $.statement_block)),
      $.until_keyword,
      field('condition', $._expression)
    ),
```

- [ ] **Step 3: Generate + verify**

Run: `tree-sitter generate && tree-sitter parse /tmp/rep.al | grep -E 'body:|ERROR'`
Expected: `body: (statement_block …)` between repeat/until, no `ERROR`. If conflict, add `[$.statement_block]` (if not already present from Task 3).

- [ ] **Step 4: Corpus check + update**

Run: `tree-sitter test 2>&1 | grep -oE '\((ERROR|MISSING)'` (expect empty), then `tree-sitter test -u`.

- [ ] **Step 5: Commit**

```bash
git add grammar.js src/parser.c src/grammar.json src/node-types.json test/corpus
git commit -m "feat(grammar): add body field to repeat_statement

[BC.History: gate at Task 6 milestone]"
```

---

## Task 5: Wrap preprocessor-split statement bodies in `statement_block`

**Files:**
- Modify: `grammar.js` — `preproc_split_procedure_body` (~2466), `_pspb_if_branch` (~2475), `_preproc_branch_body` (~2503)

These are the coverage gap the #19 fix created: shared statement runs inside preproc-split routine bodies are flat. Wrap each clean `repeat($._statement)` run. Do them one sub-edit at a time, regenerating after each, because GLR interaction with the preproc machinery is delicate.

- [ ] **Step 1: Read current text**

Run: `sed -n '2463,2512p' grammar.js`
Expected: see `preproc_split_procedure_body`, `_pspb_if_branch`, `_preproc_branch_body`, each containing `repeat($._statement)`.

- [ ] **Step 2: Edit `preproc_split_procedure_body`**

Replace its `repeat($._statement),` (the shared tail after `_pspb_else_branch`) with:
```javascript
      optional(field('body', $.statement_block)),
```

- [ ] **Step 3: Generate after sub-edit**

Run: `tree-sitter generate; echo EXIT=$?`
Expected: `EXIT=0` (add `[$.statement_block]` conflict if reported and not present). If it cascades, revert THIS sub-edit only and mark the rule as "left flat — preproc interaction" in the spec; continue to Step 4.

- [ ] **Step 4: Edit `_pspb_if_branch`**

Replace its `repeat($._statement),` (between `kw('begin')` and `optional($._preproc_if_header)`) with:
```javascript
      optional(field('body', $.statement_block)),
```
Then regenerate (`tree-sitter generate; echo EXIT=$?`, expect 0; same conflict/revert rule).

- [ ] **Step 5: Edit `_preproc_branch_body`**

Replace its `repeat($._statement),` (between `kw('begin')` and `kw('end')`) with:
```javascript
      optional(field('body', $.statement_block)),
```
Then regenerate (expect 0; same conflict/revert rule).

- [ ] **Step 6: Verify against a known preproc-split file**

Run: `grep -rl 'preproc_split' test/corpus | head -1 | xargs -I{} tree-sitter test --file-name {} 2>&1 | grep -oE '\((ERROR|MISSING)'`
Expected: empty. Then full check: `tree-sitter test 2>&1 | grep -oE '\((ERROR|MISSING)'` (expect empty), then `tree-sitter test -u`.

- [ ] **Step 7: MILESTONE — BC.History gate (preproc-heavy; this is the real test)**

Run: `./parse-al-parallel.sh ./BC.History/ .`
Expected: `Errors : 0`, `Parsed OK : 15358`.

- [ ] **Step 8: Commit**

```bash
git add grammar.js src/parser.c src/grammar.json src/node-types.json test/corpus
git commit -m "feat(grammar): wrap preproc-split statement bodies in statement_block

Closes the textobject coverage gap for preprocessor-split routine bodies.

[BC.History: 0 errors, 100% success]"
```

---

## Task 6: Give `var_section` a `body` field via `var_body`

**Files:**
- Modify: `grammar.js` — `var_section` (~2670)

- [ ] **Step 1: Observe current flat tree**

Run: `printf 'codeunit 1 C { procedure P() var a: Integer; b: Text; begin end; }\n' > /tmp/var.al && tree-sitter parse /tmp/var.al | grep -E 'var_section|var_body|variable_declaration'`
Expected: `variable_declaration` nodes are direct children of `var_section`; no `var_body`.

- [ ] **Step 2: Edit `var_section` + add `var_body`**

```javascript
    var_section: $ => prec.right(seq(
      optional(choice($.protected_keyword, $.local_keyword)),
      $.var_keyword,
      optional(field('body', $.var_body)),
    )),

    var_body: $ => repeat1(choice(
      $.variable_declaration,
      $.var_attribute_item,
      $.preproc_conditional_var,
      $.preproc_split_procedure,
    )),
```

- [ ] **Step 3: Generate (watch boundary with following begin)**

Run: `tree-sitter generate; echo EXIT=$?`
Expected: `EXIT=0`. The risk is the `var_body`→`begin` boundary (var_section is `prec.right`, no closing delimiter). If conflict, add `[$.var_body]` to `conflicts` with comment `// var_body run terminates at the following begin`, regenerate. Revert if it cascades.

- [ ] **Step 4: Verify**

Run: `tree-sitter parse /tmp/var.al | grep -E 'var_body|ERROR'`
Expected: `body: (var_body …)`, no `ERROR`.

- [ ] **Step 5: Corpus check + update**

Run: `tree-sitter test 2>&1 | grep -oE '\((ERROR|MISSING)'` (expect empty), then `tree-sitter test -u`.

- [ ] **Step 6: Commit**

```bash
git add grammar.js src/parser.c src/grammar.json src/node-types.json test/corpus
git commit -m "feat(grammar): add body field (var_body) to var_section

[BC.History: gate at Task 8 milestone]"
```

---

## Task 7: Expose `case` `end` as the named `end_keyword`

**Files:**
- Modify: `grammar.js` — `case_statement` (~2350)

`code_block` already uses `choice($.end_keyword, kw('end'))`; `case_statement` uses bare `kw('end')`, so the `end` of a case is not query-addressable as `end_keyword`. `repeat_statement` ends at `until_keyword` (already named) — no change needed there.

- [ ] **Step 1: Edit `case_statement` end**

Change its trailing `      kw('end')` to:
```javascript
      choice($.end_keyword, kw('end'))
```

- [ ] **Step 2: Generate (begin/end scanner is depth-sensitive)**

Run: `tree-sitter generate; echo EXIT=$?`
Expected: `EXIT=0`. The `end_keyword` external token is emitted at preprocessor depth 0; a top-level `case … end` is depth 0, so this should match. If generate fails or BC.History later regresses, REVERT this task — keyword-node exposure for `end` is known to interact with the stateful scanner (see `.claude/rules/contextual-keywords.md`), and naming is a nice-to-have, not a correctness fix.

- [ ] **Step 3: Verify**

Run: `tree-sitter parse /tmp/case.al | grep -E 'end_keyword|ERROR'`
Expected: the case's closing `end` shows as `(end_keyword)`, no `ERROR`.

- [ ] **Step 4: Corpus check + update**

Run: `tree-sitter test 2>&1 | grep -oE '\((ERROR|MISSING)'` (expect empty), then `tree-sitter test -u`.

- [ ] **Step 5: Commit**

```bash
git add grammar.js src/parser.c src/grammar.json src/node-types.json test/corpus
git commit -m "feat(grammar): expose case 'end' as named end_keyword

[BC.History: gate at Task 8 milestone]"
```

---

## Task 8: Rename `object_body` → `declaration_body` (cosmetic)

**Files:**
- Modify: `grammar.js` — the `object_body` rule definition (~311) and all `$.object_body` references (~17)
- Modify: `queries/textobjects.scm` (none reference `object_body` by type — verify)

`object_body` is the shared `_body_element` wrapper but is reused for fields, keys, enum values, etc., where the type name `object_body` is misleading. Queries key off the `body` FIELD, not the type, so this is cosmetic. Recommended for clarity; skip if churn is unwelcome.

- [ ] **Step 1: Count references**

Run: `grep -cE '\$\.object_body|object_body:' grammar.js`
Expected: ~18 (1 definition + ~17 uses).

- [ ] **Step 2: Rename rule + all references**

Run: `sed -i 's/object_body/declaration_body/g' grammar.js`
Then sanity-check no unrelated identifier was hit: `grep -nE 'declaration_body' grammar.js | head` (all should be the body rule).

- [ ] **Step 3: Generate + verify**

Run: `tree-sitter generate && tree-sitter parse /tmp/full.al | grep -E 'declaration_body|object_body|ERROR'`
Expected: `declaration_body` appears, `object_body` gone, no `ERROR`.

- [ ] **Step 4: Corpus check + update**

Run: `tree-sitter test 2>&1 | grep -oE '\((ERROR|MISSING)'` (expect empty), then `tree-sitter test -u`.

- [ ] **Step 5: MILESTONE — BC.History gate**

Run: `./parse-al-parallel.sh ./BC.History/ .`
Expected: `Errors : 0`, `Parsed OK : 15358`.

- [ ] **Step 6: Commit**

```bash
git add grammar.js src/parser.c src/grammar.json src/node-types.json test/corpus queries
git commit -m "refactor(grammar): rename object_body -> declaration_body

Shared body node is reused beyond objects (fields, keys, enum values);
neutral name reflects that. Queries key off the body field, unaffected.

[BC.History: 0 errors, 100% success]"
```

---

## Task 9: Attributes-as-siblings — decision (no grammar change)

**Files:**
- Modify: `docs/superpowers/specs/2026-06-17-body-field-textobjects-design.md` (append decision)
- Modify: `queries/tags.scm` (optional helper — only if it already lists declarations)

Attributes (`attribute_item`) are siblings of their target, not children/fields. This is deliberate (Rust/C# pattern; preprocessor directives can sit between attribute and target — see `.claude/rules/attributes.md`). Re-attaching would be a large restructure, contradict documented design, and gain little for textobjects.

- [ ] **Step 1: Record the decision in the spec**

Append to the spec a "Decisions: attributes stay siblings" section stating: re-association is a consumer/LSP concern (post-parse), not the parser's; the sibling model is preserved deliberately; rationale = preprocessor directives between attribute and declaration, and the established first-class-statement design.

- [ ] **Step 2: Commit (docs only)**

```bash
git add docs/superpowers/specs/2026-06-17-body-field-textobjects-design.md
git commit -m "docs: record decision to keep attributes as siblings"
```

---

## Task 10: Document inherent limitations (empty body, single-statement body)

**Files:**
- Modify: `docs/superpowers/specs/2026-06-17-body-field-textobjects-design.md`

Two behaviours are tree-sitter-inherent, not bugs — document so consumers/future-us don't "re-fix" them:
1. **Empty body → no node.** A named rule cannot match the empty string, so `{ }` / `begin end` / empty `var` emit no body node. `optional(field('body', …))` + `repeat1` is the only valid shape. (Gemini's `repeat`-instead-of-`repeat1` suggestion fails `tree-sitter generate`.)
2. **Single-statement body → no block node.** When an `if`/loop body is a bare statement (no `begin`/`end`), `field('body', …)` points at the statement itself, not a `statement_block`. `@function.inside` on such a body selects the statement. This is correct (there is no block) and matches the `then_branch`/`else_branch`/loop-`body` `choice($._statement, $.code_block)` design.

- [ ] **Step 1: Append the "Inherent limitations" section** with the two points above.

- [ ] **Step 2: Commit (docs only)**

```bash
git add docs/superpowers/specs/2026-06-17-body-field-textobjects-design.md
git commit -m "docs: document inherent empty-body / single-statement-body behaviour"
```

---

## Task 11: Update textobjects query + CLAUDE.md metrics

**Files:**
- Modify: `queries/textobjects.scm`
- Modify: `CLAUDE.md` (Parser Metrics table — test count, named keywords)

- [ ] **Step 1: Extend `textobjects.scm` with the new captures**

Add, after the existing function block:
```scm
; Loops / case bodies (statement_block / case_body via the generic block rule)
(repeat_statement body: (statement_block) @function.inside)
(case_statement body: (case_body) @block.inside)

; Code-block inner statements (excludes begin/end)
(code_block body: (statement_block) @function.inside)

; Parameters
(parameter_list) @parameter.around
```
(The generic `(_ body: (_) @block.inside)` already covers `case_body`, `var_body`, and the renamed `declaration_body`; the explicit lines above give precise `@function.inside`/`@parameter` mappings editors expect.)

- [ ] **Step 2: Verify query compiles**

Run: `tree-sitter query queries/textobjects.scm /tmp/full.al 2>&1 | grep -iE 'error|invalid'`
Expected: empty (no output).

- [ ] **Step 3: Update CLAUDE.md Parser Metrics**

Set the Tests row to the post-`-u` count (run `tree-sitter test 2>&1 | tail -1` to read `Total parses`), and note the new body/field nodes if the "Named keywords" or architecture notes need it.

- [ ] **Step 4: Final full validation**

Run: `./validate-grammar.sh --full`
Expected: tests pass, no NEW orphans/duplicates (the 2 pre-existing orphans `break_keyword`/`chartpart_keyword` are unrelated), BC.History 0 errors.

- [ ] **Step 5: Commit**

```bash
git add queries/textobjects.scm CLAUDE.md
git commit -m "docs+queries: textobject captures for new body fields; metrics

[BC.History: 0 errors, 100% success]"
```

---

## Self-Review

**Spec coverage:** all 10 problems from the Background table map to a task (1→T4, 2→T2, 3→T1, 4→T5, 5→T3, 6→T6, 7→T7, 8→T8, 9→T9, 10→T10) plus consumer/query updates (T11). The "no-action" items (supertype, Gemini's invalid empty-body fix) are explicitly recorded as non-issues.

**Risk ordering:** trivial/low-risk first (T1, T2), the linchpin `statement_block` (T3) before its dependents (T4, T5), then independent low-risk (T6, T7), cosmetic (T8), docs (T9, T10), consumer (T11). BC.History milestones gate after T3, T5, T8.

**Type consistency:** `statement_block` is defined once (T3) and reused by name in T4/T5/T11. `case_body`/`var_body`/`declaration_body` names are used identically in their definition, the generic query, and T11. `parameters` field name matches across T1 and T11.

**Revert discipline:** T3, T5, T6, T7 each carry an explicit "revert if it cascades / regresses BC.History" instruction so a risky structural change can't silently degrade the 100% gate.
