# Preprocessor Split Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 13 remaining parse failures in DO.Support-Reviewer3 by adding/fixing preprocessor split rules and property variants.

**Architecture:** Each fix adds a targeted split rule or property variant at the closest container boundary. Generic rules (`property`, `_expression`) stay strict. New rules use `prec(25)` consistent with existing split rules. The scanner's depth-tracking for `begin`/`end` at depth > 0 is leveraged where needed.

**Tech Stack:** tree-sitter grammar.js (JavaScript DSL), src/scanner.c (C external scanner), tree-sitter CLI for generate/test/parse.

---

## File Map

- **Modify:** `grammar.js` — All grammar rule additions/changes
- **Modify:** `src/scanner.c` — Only if Group I requires scanner changes (unlikely)
- **Create:** `test/corpus/preproc_split_permissions_property.txt` — Tests for Group A
- **Create:** `test/corpus/preproc_split_procedure_with_var.txt` — Tests for Group B
- **Create:** `test/corpus/preproc_split_table_relation_branch.txt` — Tests for Group C
- **Create:** `test/corpus/preproc_split_complete_body.txt` — Tests for Group D
- **Create:** `test/corpus/preproc_split_call_argument.txt` — Tests for Group F
- **Create:** `test/corpus/preproc_split_case_extra_branches.txt` — Tests for Group G
- **Create:** `test/corpus/preproc_split_layout_closing.txt` — Tests for Group H
- **Create:** `test/corpus/preproc_split_if_begin_outside.txt` — Tests for Group I
- **Modify:** `test/corpus/preproc_split_field_test.txt` — Fix existing test expectations for Group E

---

## Task 1: Group E — Fix `_field_header` bug (1 file: TempFile.Table.al)

**Files:**
- Modify: `grammar.js:1507-1514` (`_field_header` rule)
- Modify: `test/corpus/preproc_split_field_test.txt` (update expectations if needed)

**Why:** `preproc_split_field` already exists and handles the exact pattern needed. But `_field_header` is wrong — it expects `field(id; expression)` instead of `field(id; name; type)`.

- [ ] **Step 1: Write a failing test**

Create `test/corpus/preproc_split_field_type.txt`:

```
========================================================================
Field header type split across preprocessor branches
========================================================================
table 1 T
{
    fields
    {
#if not CLOUD
        field(1; Path; Text[2048])
#else
        field(1; Path; Text[250])
#endif
        {
            Caption = 'Path';
        }
    }
}
------------------------------------------------------------------------
(expected tree — run with -u after fix)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `tree-sitter generate && tree-sitter test -i "Field header type split"`
Expected: FAIL with ERROR nodes

- [ ] **Step 3: Fix `_field_header` to match real field syntax**

Change `grammar.js:1507-1514` from:
```javascript
_field_header: $ => seq(
  kw('field'),
  '(',
  $._identifier_or_quoted,
  ';',
  $._expression,
  ')',
),
```

To:
```javascript
_field_header: $ => seq(
  kw('field'),
  '(',
  field('id', $.integer),
  ';',
  field('name', $._identifier_or_quoted),
  ';',
  field('type', $.type_specification),
  ')',
),
```

This matches the real `field_declaration` syntax at `grammar.js:954-962`.

- [ ] **Step 4: Generate and run tests**

Run: `tree-sitter generate && tree-sitter test -u -i "Field header type split"`
Expected: PASS (update expectations)

Run: `tree-sitter test` (full suite)
Expected: All tests pass (existing `preproc_split_field` tests may need tree updates via `-u`)

- [ ] **Step 5: Verify against production file**

Run: `tree-sitter parse "U:/Git/DO.Support-Reviewer3/Core/Cloud/Specialization/TempFile.Table.al" 2>&1 | grep -E "ERROR|MISSING"`
Expected: No output (clean parse)

- [ ] **Step 6: Commit**

```bash
git add grammar.js src/parser.c test/corpus/preproc_split_field_type.txt test/corpus/preproc_split_field_test.txt
git commit -m "fix: correct _field_header to use field(id; name; type) syntax

Fixes TempFile.Table.al where field type differs across #if/#else branches."
```

---

## Task 2: Group A — Permissions property with `;` inside `#if` (2 files)

**Files:**
- Modify: `grammar.js:439-444` (keep `property` strict, add `permissions_property` nearby)
- Modify: `grammar.js:390-428` (add `permissions_property` to `_body_element`)
- Modify: `grammar.js:797-827` (update `preproc_conditional_permissions` to allow `;` in branches)
- Create: `test/corpus/preproc_split_permissions_property.txt`

**Why:** The property's terminating `;` is inside `#if` branches. Can't make generic `property` `;` optional (cascading conflicts). Instead, add a dedicated `permissions_property` aliased as `property` for AST consistency.

- [ ] **Step 1: Write failing tests**

Create `test/corpus/preproc_split_permissions_property.txt` with two tests:

Test 1 — `#if` only (no `#else`), `;` inside:
```al
permissionset 1 "Test"
{
    Permissions =
        tabledata Foo = rimd,
        tabledata Bar = rimd
#if not CLEAN29
        ,
        tabledata Baz = Rim;
#endif
}
```

Test 2 — `#if`/`#else`, `;` in both branches:
```al
codeunit 1 T
{
    Permissions = tabledata Foo = d,
                  tabledata Bar = d
#if not CLEAN27
                  ,
                  tabledata Old = d;
#else
                  ,
                  tabledata New = d;
#endif
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `tree-sitter generate && tree-sitter test -i "permissions"`
Expected: FAIL with ERROR nodes at `;` positions

- [ ] **Step 3: Update `preproc_conditional_permissions` to allow `;` in branches**

In `grammar.js`, update each branch's repeat content to allow `;` after the last entry:

```javascript
preproc_conditional_permissions: $ => seq(
  $.preproc_if,
  optional(','),
  repeat(choice(
    seq($.tabledata_permission, optional(choice(',', ';'))),
    $.preproc_conditional_permissions,
  )),
  repeat(seq(
    $.preproc_elif,
    optional(','),
    repeat(choice(
      seq($.tabledata_permission, optional(choice(',', ';'))),
      $.preproc_conditional_permissions,
    )),
  )),
  optional(seq(
    $.preproc_else,
    optional(','),
    repeat(choice(
      seq($.tabledata_permission, optional(choice(',', ';'))),
      $.preproc_conditional_permissions,
    )),
  )),
  $.preproc_endif,
),
```

- [ ] **Step 4: Add `permissions_property` rule**

Add after the `property` rule in `grammar.js`:

```javascript
// Permissions property variant: ';' may be consumed inside preproc branches
permissions_property: $ => seq(
  field('name', $.property_name),
  '=',
  field('value', $.tabledata_permission_list),
),
```

- [ ] **Step 5: Add `permissions_property` to `_body_element`**

In `_body_element`, add `alias($.permissions_property, $.property)` alongside `$.property`:

```javascript
_body_element: $ => choice(
  $.property,
  alias($.permissions_property, $.property),
  // ... rest unchanged
),
```

- [ ] **Step 6: Handle conflicts**

If `tree-sitter generate` reports conflicts between `property` and `permissions_property`, add to the conflicts list:
```javascript
[$.property, $.permissions_property],
```

Or use `prec.dynamic(-1)` on `permissions_property` so it only wins when `property` fails.

- [ ] **Step 7: Generate, update tests, run full suite**

Run: `tree-sitter generate && tree-sitter test -u -i "permissions" && tree-sitter test`
Expected: All tests pass

- [ ] **Step 8: Verify against production files**

Run:
```bash
tree-sitter parse "U:/Git/DO.Support-Reviewer3/DeliveryNetwork/Cloud/Resources/CTSCDNBasic.PermissionSet.al" 2>&1 | grep -E "ERROR|MISSING"
tree-sitter parse "U:/Git/DO.Support-Reviewer3/DocumentCapture/Cloud/.dependencies/DC/Codeunit/CDCGlobalTriggerMgt.Codeunit.al" 2>&1 | grep -E "ERROR|MISSING"
```
Expected: No output

- [ ] **Step 9: Commit**

```bash
git add grammar.js src/parser.c test/corpus/preproc_split_permissions_property.txt
git commit -m "fix: handle property-terminating ; inside #if in permission lists

Adds permissions_property variant and allows ; in preproc_conditional_permissions branches.
Fixes CTSCDNBasic.PermissionSet.al and CDCGlobalTriggerMgt.Codeunit.al."
```

---

## Task 3: Group C — TableRelation last branch in `#if/#else` (2 files)

**Files:**
- Modify: `grammar.js` (add `table_relation_property` near `property` rule)
- Modify: `grammar.js:390-428` (add to `_body_element`)
- Create: `test/corpus/preproc_split_table_relation_branch.txt`

**Why:** Same root cause as Group A — the `;` terminating the TableRelation property lives inside `#if/#else` branches. `preproc_conditional_table_relation` already supports `optional(';')` in branches (line 755). Need a property variant that doesn't require trailing `;`.

**Key subtlety:** CDCDataTranslation.Table.al has `else` on its own line before `#if`. The `else` belongs to the outer `if_table_relation` chain. The `#if` wraps the final `if(...)` branch. `if_table_relation` uses `field('else_relation', $.table_relation_expression)` which can be a `preproc_conditional_table_relation` — so the chaining should work IF the property `;` issue is solved.

CDCTempDocumentLine.Table.al has `else if` entirely inside both `#if` and `#else` branches — this is a standard `preproc_conditional_table_relation` wrapping the last branch.

- [ ] **Step 1: Write failing tests**

Create `test/corpus/preproc_split_table_relation_branch.txt`:

Test 1 — `else if` inside both branches:
```al
table 1 T
{
    fields
    {
        field(1; F; Code[20])
        {
            TableRelation = if (Type = const(Item)) Item
                else
#if BC24
                if (Type = const("Alloc")) "Alloc Account" where("Account Type" = const(Fixed));
#else
                IF (Type = CONST("Alloc")) "G/L Account";
#endif
        }
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `tree-sitter generate && tree-sitter test -i "TableRelation"`
Expected: FAIL

- [ ] **Step 3: Add `table_relation_property` rule**

```javascript
// TableRelation property variant: ';' may be consumed inside preproc branches
table_relation_property: $ => seq(
  field('name', $.property_name),
  '=',
  field('value', $.table_relation_value),
),
```

Add `alias($.table_relation_property, $.property)` to `_body_element`.

- [ ] **Step 4: Handle conflicts, generate, test**

Same approach as Task 2. Add conflict entries if needed.

Run: `tree-sitter generate && tree-sitter test -u && tree-sitter test`

- [ ] **Step 5: Verify against production files**

Run:
```bash
tree-sitter parse "U:/Git/DO.Support-Reviewer3/DocumentCapture/Cloud/.dependencies/DC/Table/CDCDataTranslation.Table.al" 2>&1 | grep -E "ERROR|MISSING"
tree-sitter parse "U:/Git/DO.Support-Reviewer3/DocumentCapture/Cloud/.dependencies/DC/Table/CDCTempDocumentLine.Table.al" 2>&1 | grep -E "ERROR|MISSING"
```
Expected: No output

- [ ] **Step 6: Commit**

```bash
git add grammar.js src/parser.c test/corpus/preproc_split_table_relation_branch.txt
git commit -m "fix: handle TableRelation property ; inside #if/#else branches

Adds table_relation_property variant for cases where the closing ; is inside preprocessor branches.
Fixes CDCDataTranslation.Table.al and CDCTempDocumentLine.Table.al."
```

---

## Task 4: Group B — Procedure header + var both split (2 files)

**Files:**
- Modify: `grammar.js:2244-2256` (extend `preproc_split_procedure` or add new rule)
- Modify: `grammar.js:390-428` (add to `_body_element` if new rule)
- Create: `test/corpus/preproc_split_procedure_with_var.txt`

**Why:** Existing `preproc_split_procedure` puts `optional(var_section)` AFTER `#endif`. These files have var inside each `#if/#else` branch along with the header, followed by shared `begin...end`.

**Approach:** Extend `_procedure_header` (or create `_procedure_preamble`) to include an optional var_section, so each branch can contain header + var.

- [ ] **Step 1: Write failing test**

Create `test/corpus/preproc_split_procedure_with_var.txt`:

```al
codeunit 1 T
{
#if FEATURE
    procedure Update(DocType: Enum "Doc Type"; Type: Enum "Reason Type"; Code: Code[10])
    var
        Rec: Record "New Table";
#else
    procedure Update(DocType: Integer; Type: Integer; Code: Code[10])
    var
        Rec: Record "Old Table";
#endif
    begin
        if Rec.Get(Code) then
            Rec.Delete();
    end;
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `tree-sitter generate && tree-sitter test -i "procedure.*var"`
Expected: FAIL

- [ ] **Step 3: Create `_procedure_preamble` helper and update split rule**

Add a new helper that includes header + optional var:

```javascript
// Procedure preamble: header + optional var (used in split rules where both are inside branches)
_procedure_preamble: $ => seq(
  $._procedure_header,
  optional(';'),
  optional(choice(
    $.var_section,
    $.preproc_conditional_var_block,
  )),
),
```

Add a new rule `preproc_split_procedure_preamble`:

```javascript
// Preprocessor-split procedure preamble: header+var in #if/#else, shared code_block
preproc_split_procedure_preamble: $ => prec(25, seq(
  $.preproc_if,
  $._procedure_preamble,
  repeat(seq($.preproc_elif, $._procedure_preamble)),
  optional(seq($.preproc_else, $._procedure_preamble)),
  $.preproc_endif,
  $.code_block,
)),
```

Add to `_body_element`:
```javascript
$.preproc_split_procedure_preamble,
```

- [ ] **Step 4: Generate, update tests, run full suite**

Run: `tree-sitter generate && tree-sitter test -u -i "procedure" && tree-sitter test`

- [ ] **Step 5: Verify against production files**

Run:
```bash
tree-sitter parse "U:/Git/DO.Support-Reviewer3/DocumentCapture/DemoApp/.dependencies/DC/Setup/Codeunit/CDCDemoCreateDemoData.Codeunit.al" 2>&1 | grep -E "ERROR|MISSING"
tree-sitter parse "U:/Git/DO.Support-Reviewer3/DocumentCapture/DemoApp/AL/Continia One/CDCDemoContiniaOneScenar.Codeunit.al" 2>&1 | grep -E "ERROR|MISSING"
```
Expected: No output

- [ ] **Step 6: Commit**

```bash
git add grammar.js src/parser.c test/corpus/preproc_split_procedure_with_var.txt
git commit -m "fix: handle procedure header+var split across #if/#else branches

Adds preproc_split_procedure_preamble for cases where both header and var section
differ across preprocessor branches with shared code_block after #endif.
Fixes CDCDemoCreateDemoData.Codeunit.al and CDCDemoContiniaOneScenar.Codeunit.al."
```

---

## Task 5: Group D — Complete body split across `#if/#else` (2 files)

**Files:**
- Modify: `grammar.js` (add `preproc_split_complete_body` rule)
- Modify: `grammar.js` (add to procedure and trigger declaration choices)
- Create: `test/corpus/preproc_split_complete_body.txt`

**Why:** Unlike `preproc_split_procedure_body` (shared statements after `#endif`), here each branch contains a COMPLETE `var+begin+end;` body with NO shared code after `#endif`. This appears in both triggers (CDCPurchaseReasonCodes) and procedures (CDCDocumentCaptureSetup).

**Approach:** New rule for complete body alternatives in `#if/#else`. Each branch contains `optional(var) begin stmts end;`. Wire into both `procedure` and `trigger_declaration`.

- [ ] **Step 1: Write failing tests**

Create `test/corpus/preproc_split_complete_body.txt`:

Test 1 — Trigger with complete body split:
```al
table 1 T
{
    fields
    {
        field(1; Code; Code[10])
        {
            trigger OnValidate()
#if FEATURE
            var
                Rec: Record "New Table";
            begin
                Rec.Get(Rec.Code);
            end;
#else
            var
                Rec: Record "Old Table";
            begin
                Rec.Get(Rec.Code);
            end;
#endif
        }
    }
}
```

Test 2 — Procedure with complete body split (one branch has var, other doesn't):
```al
codeunit 1 T
{
    local procedure Validate(FieldNo: Integer)
#if FEATURE
    var
        Custom: Codeunit "Custom Fields";
    begin
        Custom.Validate(Rec, FieldNo);
    end;
#else
    begin
    end;
#endif
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `tree-sitter generate && tree-sitter test -i "complete body"`
Expected: FAIL

- [ ] **Step 3: Add `preproc_split_complete_body` rule**

```javascript
// Complete body split: each #if/#else branch has a full var+begin+end body
// No shared code after #endif. Used when the entire body differs per branch.
preproc_split_complete_body: $ => prec.right(25, seq(
  $.preproc_if,
  optional($.var_section),
  kw('begin'),
  repeat($._statement),
  kw('end'),
  optional(';'),
  repeat(seq(
    $.preproc_elif,
    optional($.var_section),
    kw('begin'),
    repeat($._statement),
    kw('end'),
    optional(';'),
  )),
  optional(seq(
    $.preproc_else,
    optional($.var_section),
    kw('begin'),
    repeat($._statement),
    kw('end'),
    optional(';'),
  )),
  $.preproc_endif,
)),
```

- [ ] **Step 4: Wire into procedure and trigger_declaration**

In `procedure` (line 2213), add `$.preproc_split_complete_body` as a choice alongside `$.preproc_split_procedure_body`:

```javascript
choice(
  seq(
    optional(choice($.var_section, $.preproc_conditional_var_block)),
    $.code_block,
  ),
  $.preproc_split_procedure_body,
  $.preproc_split_complete_body,
)
```

In `trigger_declaration` (line 2358-2362), similarly replace the strict `$.code_block` with a choice:

```javascript
choice(
  seq(
    optional(choice($.var_section, $.preproc_conditional_var_block)),
    $.code_block,
  ),
  $.preproc_split_complete_body,
),
```

Note: This changes trigger_declaration's structure — currently var_section is before the choice, code_block is last. Restructure so the var+code_block combination and the split_complete_body are alternatives.

- [ ] **Step 5: Generate, update tests, run full suite**

Run: `tree-sitter generate && tree-sitter test -u && tree-sitter test`

- [ ] **Step 6: Verify against production files**

Run:
```bash
tree-sitter parse "U:/Git/DO.Support-Reviewer3/DocumentCapture/Cloud/.dependencies/DC/Page/CDCPurchaseReasonCodes.Page.al" 2>&1 | grep -E "ERROR|MISSING"
tree-sitter parse "U:/Git/DO.Support-Reviewer3/DocumentCapture/Cloud/.dependencies/DC/Table/CDCDocumentCaptureSetup.Table.al" 2>&1 | grep -E "ERROR|MISSING"
```
Expected: No output

- [ ] **Step 7: Commit**

```bash
git add grammar.js src/parser.c test/corpus/preproc_split_complete_body.txt
git commit -m "fix: handle complete body split across #if/#else in procedures/triggers

Adds preproc_split_complete_body for cases where each branch contains a full
var+begin+end body with no shared code after #endif.
Fixes CDCPurchaseReasonCodes.Page.al and CDCDocumentCaptureSetup.Table.al."
```

---

## Task 6: Group H — Layout section closing inside `#if` (1 file: CDCServiceOrder.PageExtension.al)

**Files:**
- Modify: `grammar.js` (update `preproc_conditional_layout` or add handling for `addlast` closing inside `#if`)
- Create: `test/corpus/preproc_split_layout_closing.txt`

**Why:** `#if not CLEAN28` wraps a field + the closing `}` of the `addlast` group. The `}` is inside `#if`, so after `#endif` the parser can't close the group.

**Approach:** This is similar to `preproc_split_brace_close` (line 1354) but for extension modifications (`addlast`, etc). The `addlast_modification` rule needs to accept a split closing brace.

- [ ] **Step 1: Examine `addlast_modification` rule structure**

Read the current `addlast_modification` rule and determine how to add `preproc_split_brace_close` or a similar construct as an alternative to the closing `}`.

- [ ] **Step 2: Write failing test**

Create `test/corpus/preproc_split_layout_closing.txt`:

```al
pageextension 1 "Test" extends "Source"
{
    layout
    {
        addlast(General)
        {
#if not CLEAN28
            field(Status; Status)
            {
                Caption = 'Status';
            }
        }
#endif
    }

    var
        Status: Text;
}
```

- [ ] **Step 3: Implement fix**

The approach depends on whether `addlast_modification` uses a hardcoded `}` or a reusable closing construct. If it uses `}`, change it to `choice('}', $.preproc_split_brace_close)` like `area_section` does. OR handle it as a `preproc_conditional_layout` that wraps the field + `}`.

This may require allowing `preproc_conditional_layout` to contain `}` as the last element, or creating a variant of `preproc_split_brace_close` that supports the "content + `}` inside `#if`, nothing in `#else`" pattern (no `#else` branch).

- [ ] **Step 4: Generate, test, verify**

Run: `tree-sitter generate && tree-sitter test -u && tree-sitter test`
Verify: `tree-sitter parse "U:/Git/DO.Support-Reviewer3/DocumentCapture/Cloud/Al/Standard Extensions/Page Extensions/CDCServiceOrder.PageExtension.al" 2>&1 | grep -E "ERROR|MISSING"`

- [ ] **Step 5: Commit**

```bash
git add grammar.js src/parser.c test/corpus/preproc_split_layout_closing.txt
git commit -m "fix: handle layout section closing brace inside #if block

Fixes CDCServiceOrder.PageExtension.al where addlast group } is inside #if."
```

---

## Task 7: Group I — `if...then begin` inside `#if`, `end` outside (1 file: CDCContiniaOnlineMgt.Codeunit.al)

**Files:**
- Modify: `grammar.js:2666-2689` (adjust `preproc_split_if_then_begin` or add variant)
- Create: `test/corpus/preproc_split_if_begin_outside.txt`

**Why:** Existing `preproc_split_if_then_begin` expects `end` inside a second `#if` block. But here the `end;` is completely outside any `#if` — it's just a normal `end;` at depth 0.

**Pattern:**
```al
#if not CLEAN27
    if not Http.Execute(...) then begin
#endif
        HandleError();
        exit(false);
    end;
```

**Approach:** Add a simpler variant of `preproc_split_if_then_begin` where: `#if` contains `if expr then begin`, `#endif`, then shared statements, then `end;` at depth 0 (no second `#if`). The `begin` is at depth > 0 (`preproc_split_begin`). The `end` is a regular `end_keyword` or `kw('end')` at depth 0.

- [ ] **Step 1: Write failing test**

Create `test/corpus/preproc_split_if_begin_outside.txt`:

```al
codeunit 1 T
{
    procedure X()
    begin
#if not CLEAN27
        if not DoSomething() then begin
#endif
            HandleError();
            exit(false);
        end;
    end;
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `tree-sitter generate && tree-sitter test -i "if begin outside"`

- [ ] **Step 3: Add variant rule**

Add alongside existing `preproc_split_if_then_begin`:

```javascript
// Asymmetric if-then-begin: the if...then begin is inside #if, but end is outside
// #if / if expr then begin / #endif / shared_stmts end;
preproc_split_if_begin_asymmetric: $ => prec(26, seq(
  $.preproc_if,
  $.if_keyword,
  field('condition', $._expression),
  $.then_keyword,
  $.preproc_split_begin,
  $.preproc_endif,
  repeat($._statement),
  choice($.end_keyword, kw('end')),
  optional(';'),
)),
```

Add to `_statement` choices (wherever `preproc_split_if_then_begin` is listed, around line 2812-2814):
```javascript
$.preproc_split_if_begin_asymmetric,
```

- [ ] **Step 4: Generate, test, verify**

Run: `tree-sitter generate && tree-sitter test -u && tree-sitter test`
Verify: `tree-sitter parse "U:/Git/DO.Support-Reviewer3/DocumentCapture/Cloud/Modules/Continia Online/Codeunit/CDCContiniaOnlineMgt.Codeunit.al" 2>&1 | grep -E "ERROR|MISSING"`

- [ ] **Step 5: Commit**

```bash
git add grammar.js src/parser.c test/corpus/preproc_split_if_begin_outside.txt
git commit -m "fix: handle if...then begin inside #if with end outside

Adds preproc_split_if_begin_asymmetric for patterns where the if conditional
is inside #if but the matching end is at depth 0.
Fixes CDCContiniaOnlineMgt.Codeunit.al."
```

---

## Task 8: Group F — Function call argument split (1 file: CDCContiniaConfigMgt.Codeunit.al)

**Files:**
- Modify: `grammar.js` (add `preproc_split_call_expression` rule)
- Modify: `grammar.js` (add to `_statement` or `_expression` choices)
- Create: `test/corpus/preproc_split_call_argument.txt`

**Why:** The function name + first argument are in `#if/#else`, remaining args + `)` are shared after `#endif`. No existing rule covers this.

**Approach:** Add a `preproc_split_call_statement` that parses: `#if` branch provides `FuncName(arg1,`, `#else` provides `FuncName(arg1,`, shared suffix is `arg2, arg3, ...);`. This is a statement-level rule (the call is a statement), not an expression-level rule, to avoid polluting `_expression`.

- [ ] **Step 1: Write failing test**

Create `test/corpus/preproc_split_call_argument.txt`:

```al
codeunit 1 T
{
    procedure X()
    begin
#if FEATURE
        ImportTable(Database::"Old Table",
#else
        ImportTable(Database::"New Table",
#endif
            Rec.FieldNo("ID"), Format(Rec."ID"),
            Rec.FieldNo("Type"), Format(Rec.Type));
    end;
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `tree-sitter generate && tree-sitter test -i "call argument"`

- [ ] **Step 3: Add `preproc_split_call_statement` rule**

```javascript
// Split call statement: function call where first argument(s) differ across #if/#else
// #if / func(arg1, / #else / func(arg1, / #endif / shared_args);
preproc_split_call_statement: $ => prec(25, seq(
  $.preproc_if,
  $._preproc_call_prefix,
  repeat(seq($.preproc_elif, $._preproc_call_prefix)),
  optional(seq($.preproc_else, $._preproc_call_prefix)),
  $.preproc_endif,
  // Shared remaining arguments and closing paren
  optional(seq($._expression, repeat(seq(',', $._expression)))),
  ')',
  ';'
)),

// Call prefix inside a preproc branch: function_name(arg1, arg2,
_preproc_call_prefix: $ => seq(
  $._expression,  // function name (may be member_expression)
  '(',
  $._expression,
  repeat(seq(',', $._expression)),
  ','  // trailing comma leads into shared args
),
```

Add `$.preproc_split_call_statement` to the `_statement` choices.

- [ ] **Step 4: Generate, test, verify**

Run: `tree-sitter generate && tree-sitter test -u && tree-sitter test`
Verify: `tree-sitter parse "U:/Git/DO.Support-Reviewer3/DocumentCapture/Cloud/.dependencies/DC/Codeunit/CDCContiniaConfigMgt.Codeunit.al" 2>&1 | grep -E "ERROR|MISSING"`

Note: This file has 2 occurrences of this pattern. Both should be fixed.

- [ ] **Step 5: Commit**

```bash
git add grammar.js src/parser.c test/corpus/preproc_split_call_argument.txt
git commit -m "fix: handle function call with first argument split across #if/#else

Adds preproc_split_call_statement for patterns where the call prefix
(function name + first args) differs across preprocessor branches.
Fixes CDCContiniaConfigMgt.Codeunit.al."
```

---

## Task 9: Group G — Case with extra branches + modified pattern in `#if` (1 file: CDO E-Mail.al)

**Files:**
- Modify: `grammar.js` (add `preproc_split_case_extended` rule)
- Modify: `grammar.js` (add to case_branch choices)
- Create: `test/corpus/preproc_split_case_extra_branches.txt`

**Why:** `#if DOSMTP` adds a complete extra case branch AND provides the pattern for the next branch. `#else` provides an alternate pattern. The shared body follows `#endif`.

**Approach:** New rule: `#if` branch can contain zero or more complete `case_branch` entries plus a trailing case-pattern-with-colon (header only). `#else` branch has an alternate case-pattern-with-colon. Shared body follows `#endif`.

- [ ] **Step 1: Write failing test**

Create `test/corpus/preproc_split_case_extra_branches.txt`:

```al
codeunit 1 T
{
    procedure X()
    var
        Method: Option SMTP,"Email Accounts",Azure;
    begin
        case Method of
#if DOSMTP
            Method::SMTP:
                begin
                    DoSMTP();
                end;
            Method::"Email Accounts":
#else
            Method::"Email Accounts", Method::SMTP:
#endif
                begin
                    DoEmail();
                end;
            Method::Azure:
                begin
                    DoAzure();
                end;
        end;
    end;
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `tree-sitter generate && tree-sitter test -i "case extra"`

- [ ] **Step 3: Add `preproc_split_case_extended` rule**

Factor out a helper for case branch header:
```javascript
_case_branch_header: $ => seq(
  field('pattern', $._case_pattern),
  ':'
),
```

Then the extended split rule:
```javascript
// Extended case split: #if adds complete branches + provides header for next shared branch
// #if / [complete_branch]* header / #else / alt_header / #endif / shared_body
preproc_split_case_extended: $ => prec(25, seq(
  $.preproc_if,
  repeat($.case_branch),          // zero or more complete extra branches
  $._case_branch_header,          // header-only for the next branch
  repeat(seq(
    $.preproc_elif,
    repeat($.case_branch),
    $._case_branch_header,
  )),
  optional(seq(
    $.preproc_else,
    repeat($.case_branch),
    $._case_branch_header,
  )),
  $.preproc_endif,
  field('body', choice(
    $.code_block,
    alias($._if_statement_no_else, $.if_statement),
    $._statement,
  ))
)),
```

Add to `case_statement`'s body as a sibling to `case_branch`.

- [ ] **Step 4: Handle conflicts**

This will likely conflict with `preproc_conditional_case` and `preproc_split_case_branch`. Add necessary conflict entries.

- [ ] **Step 5: Generate, test, verify**

Run: `tree-sitter generate && tree-sitter test -u && tree-sitter test`
Verify: `tree-sitter parse "U:/Git/DO.Support-Reviewer3/DocumentOutput/Cloud/Al/Codeunit/Codeunit 6175280 CDO E-Mail.al" 2>&1 | grep -E "ERROR|MISSING"`

- [ ] **Step 6: Commit**

```bash
git add grammar.js src/parser.c test/corpus/preproc_split_case_extra_branches.txt
git commit -m "fix: handle case statement with extra branches in #if and modified pattern

Adds preproc_split_case_extended for patterns where #if adds complete branches
and provides a different pattern for the next shared-body branch.
Fixes CDO E-Mail.al."
```

---

## Task 10: Final Validation

- [ ] **Step 1: Run full test suite**

Run: `tree-sitter test`
Expected: All tests pass

- [ ] **Step 2: Run BC.History regression check**

Run: `./parse-al-parallel.sh ./BC.History/ .`
Expected: 0 errors, 15,358/15,358 success

- [ ] **Step 3: Run all DO.Support-Reviewer3 directories**

```bash
./parse-al-parallel.sh "U:/Git/DO.Support-Reviewer3/Core/" .
./parse-al-parallel.sh "U:/Git/DO.Support-Reviewer3/DeliveryNetwork/" .
./parse-al-parallel.sh "U:/Git/DO.Support-Reviewer3/DocumentCapture/" .
./parse-al-parallel.sh "U:/Git/DO.Support-Reviewer3/DocumentOutput/" .
```
Expected: 0 errors across all 4 directories

- [ ] **Step 4: Update CLAUDE.md metrics if needed**

Update test count and any other metrics that changed.

- [ ] **Step 5: Commit final state**

```bash
git add CLAUDE.md
git commit -m "docs: update metrics after preproc split fixes"
```

---

## Execution Order & Dependencies

| Task | Group | Files Fixed | Effort | Dependencies |
|------|-------|------------|--------|-------------|
| 1 | E | 1 (TempFile) | Low | None |
| 2 | A | 2 (permissions) | Medium | None |
| 3 | C | 2 (TableRelation) | Medium | Informed by Task 2 approach |
| 4 | B | 2 (procedure header+var) | Medium | None |
| 5 | D | 2 (complete body) | Medium | None |
| 6 | H | 1 (layout closing) | Medium | None |
| 7 | I | 1 (if-begin asymmetric) | Medium | None |
| 8 | F | 1 (call argument) | High | None |
| 9 | G | 1 (case extended) | High | None |
| 10 | — | Validation | Low | All above |

Tasks 1-7 are independent and can be parallelized. Tasks 8-9 are higher risk (new expression/case patterns). Task 10 must run last.
