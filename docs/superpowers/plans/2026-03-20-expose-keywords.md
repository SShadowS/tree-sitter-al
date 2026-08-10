# Expose Keywords as Named Nodes — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make all ~80 AL keywords visible in the parse tree as named nodes so they can be matched in tree-sitter queries for syntax highlighting.

**Architecture:** Add named rules (`begin_keyword: $ => kw('begin')`) for each keyword, then replace all inline `kw()` calls with references to these rules. Single big-bang commit with test expectation update via `tree-sitter test -u`.

**Tech Stack:** tree-sitter grammar.js DSL, tree-sitter queries (.scm)

**Spec:** `docs/superpowers/specs/2026-03-20-expose-keywords-design.md`

---

## Pre-Implementation Notes

### Key Facts

- `grammar.js` is ~8500 lines. All changes are in this file plus query files.
- `begin` is the ONLY keyword using `kw_literal()` — its named rule MUST use `kw_literal()`.
- `break` has NO `kw()` call site — it only appears in `_enum_keyword`. Its named rule will only be used there.
- `actions` and `layout` use bare string `choice('actions', 'Actions', 'ACTIONS')` patterns, NOT `kw()`. Their named rules should wrap the existing pattern.
- `view` uses bare string `'view'` in `view_definition` (line 7716) and `kw('view')` in `run_page_mode_value` (line 3446). Only the `kw()` site converts.
- **CRITICAL — Precedence stays at call sites:** Every `kw('keyword', N)` becomes `prec(N, $.keyword_keyword)`, NOT bare `$.keyword_keyword`. Dropping precedence causes regressions. Keywords with precedence include: `if`(10), `then`(10), `else`(10), `case`(10), `of`(10), `begin`(10), `exit`(10), `continue`(10), `with`(10), `asserterror`(10), `in`(10), `interface`(10), and others. Always check the original `kw()` call for a second argument.
- `kw('end')` at line ~1915 is inside `shortcut_key_property` (as a key value, not a block delimiter). Convert it to `$.end_keyword` — the keyword node appears in property value context, which is acceptable (queries use parent context to distinguish).
- `kw('temporary')` at line ~3560 is inside `table_type_value` (as an enum value). Convert it to `$.temporary_keyword` — same rationale as above.
- `alias(kw('end'), $.identifier)` sites (lines 4565, 6436, 8356) are EXCLUDED — keep as-is.
- `alias(kw('enum'), $.identifier)` sites (lines 4590, 6429, 8365) are EXCLUDED — keep as-is.
- `kw_with_coloncolon()` sites for table/page/codeunit/report/xmlport/query are EXCLUDED — separate tokens.

### Existing Named Rules to Refactor

These already-existing rules wrap keywords and need updating to use the new keyword rules:

| Existing Rule | Line | Contains | Action |
|---|---|---|---|
| `procedure_modifier` | 5823 | `kw('local')`, `kw('internal')`, `kw('protected')` | Replace with `$.local_keyword`, `$.internal_keyword`, `$.protected_keyword` |
| `modifier` | 6098 | `kw('var')` | Replace with `$.var_keyword` |
| `temporary` | 6192 | `kw('temporary')` | Replace with `$.temporary_keyword`; rename existing `temporary` rule or adjust |
| `in_operator` | 6505 | `kw('in')` in various forms | Keep `in_operator` as-is; `in_keyword` covers `foreach...in` usage |

### State Count Baseline

Current parser state count: ~29,345. If it exceeds ~59,000 after generation, reduce scope per spec.

---

## Task 1: Add All Keyword Rule Definitions

**Files:**
- Modify: `grammar.js` — add a new "Keyword Rules" section

- [ ] **Step 1: Find insertion point**

Add keyword rules as a block before the existing `zeroorone_keyword` rule (around line 8441). Search for `zeroorone_keyword:` to find the location.

- [ ] **Step 2: Add Tier 1 keyword rules (Control Flow & Declarations)**

Insert before `zeroorone_keyword`:

```javascript
    // =========================================================================
    // Keyword Rules — Named nodes for query matching
    // See: docs/superpowers/specs/2026-03-20-expose-keywords-design.md
    // =========================================================================

    // -- Tier 1: Control Flow & Declarations --
    begin_keyword: $ => kw_literal('begin'),  // MUST use kw_literal (word boundary)
    end_keyword: $ => kw('end'),
    if_keyword: $ => kw('if'),
    then_keyword: $ => kw('then'),
    else_keyword: $ => kw('else'),
    case_keyword: $ => kw('case'),
    of_keyword: $ => kw('of'),
    while_keyword: $ => kw('while'),
    do_keyword: $ => kw('do'),
    for_keyword: $ => kw('for'),
    foreach_keyword: $ => kw('foreach'),
    in_keyword: $ => kw('in'),
    repeat_keyword: $ => kw('repeat'),
    until_keyword: $ => kw('until'),
    var_keyword: $ => kw('var'),
    procedure_keyword: $ => kw('procedure'),
    trigger_keyword: $ => kw('trigger'),
    exit_keyword: $ => kw('exit'),
    break_keyword: $ => kw('break'),
    continue_keyword: $ => kw('continue'),
    with_keyword: $ => kw('with'),
    asserterror_keyword: $ => kw('asserterror'),
```

- [ ] **Step 3: Add Tier 2 keyword rules (Object Types & Structure)**

```javascript
    // -- Tier 2: Object Types & Structure --
    table_keyword: $ => kw('table'),
    tableextension_keyword: $ => kw('tableextension'),
    page_keyword: $ => kw('page'),
    pageextension_keyword: $ => kw('pageextension'),
    codeunit_keyword: $ => kw('codeunit'),
    report_keyword: $ => kw('report'),
    reportextension_keyword: $ => kw('reportextension'),
    query_keyword: $ => kw('query'),
    xmlport_keyword: $ => kw('xmlport'),
    enum_keyword: $ => kw('enum'),
    enumextension_keyword: $ => kw('enumextension'),
    interface_keyword: $ => kw('interface'),
    controladdin_keyword: $ => kw('controladdin'),
    dotnet_keyword: $ => kw('dotnet'),
    profile_keyword: $ => kw('profile'),
    profileextension_keyword: $ => kw('profileextension'),
    permissionset_keyword: $ => kw('permissionset'),
    permissionsetextension_keyword: $ => kw('permissionsetextension'),
    entitlement_keyword: $ => kw('entitlement'),
    pagecustomization_keyword: $ => kw('pagecustomization'),
    namespace_keyword: $ => kw('namespace'),
    using_keyword: $ => kw('using'),
    implements_keyword: $ => kw('implements'),
    extends_keyword: $ => kw('extends'),
    customizes_keyword: $ => kw('customizes'),
```

- [ ] **Step 4: Add Tier 3 keyword rules (Sections & Modifiers)**

```javascript
    // -- Tier 3: Sections & Modifiers --
    fields_keyword: $ => kw('fields'),
    keys_keyword: $ => kw('keys'),
    key_keyword: $ => kw('key'),
    fieldgroups_keyword: $ => kw('fieldgroups'),
    fieldgroup_keyword: $ => kw('fieldgroup'),
    actions_keyword: $ => token(choice('actions', 'Actions', 'ACTIONS')),  // bare string pattern
    layout_keyword: $ => token(choice('layout', 'Layout', 'LAYOUT')),     // bare string pattern
    area_keyword: $ => kw('area'),
    group_keyword: $ => kw('group'),
    repeater_keyword: $ => kw('repeater'),
    cuegroup_keyword: $ => kw('cuegroup'),
    fixed_keyword: $ => kw('fixed'),
    grid_keyword: $ => kw('grid'),
    part_keyword: $ => kw('part'),
    systempart_keyword: $ => kw('systempart'),
    usercontrol_keyword: $ => kw('usercontrol'),
    chartpart_keyword: $ => kw('chartpart'),
    dataset_keyword: $ => kw('dataset'),
    elements_keyword: $ => kw('elements'),
    dataitem_keyword: $ => kw('dataitem'),
    column_keyword: $ => kw('column'),
    filter_keyword: $ => kw('filter'),
    labels_keyword: $ => kw('labels'),
    rendering_keyword: $ => kw('rendering'),
    requestpage_keyword: $ => kw('requestpage'),
    schema_keyword: $ => kw('schema'),
    views_keyword: $ => kw('views'),
    view_keyword: $ => kw('view'),
    local_keyword: $ => kw('local'),
    internal_keyword: $ => kw('internal'),
    protected_keyword: $ => kw('protected'),
    event_keyword: $ => kw('event'),
    temporary_keyword: $ => kw('temporary'),
```

- [ ] **Step 5: Verify generation succeeds**

Run: `tree-sitter generate`
Expected: Success. Note the state count from `src/parser.c` (search for `STATE_COUNT`).

---

## Task 2: Replace Tier 1 Call Sites (Control Flow & Declarations)

**Files:**
- Modify: `grammar.js` — replace all inline `kw()` / `kw_literal()` calls for Tier 1 keywords

- [ ] **Step 1: Replace `begin` call sites**

Replace all `kw_literal('begin', 10)` and `kw_literal('begin')` with `prec(10, $.begin_keyword)` or `$.begin_keyword` (preserving precedence where it exists).

Sites: lines ~5923, 5927, 5977, 5996, 6018, 6199

- [ ] **Step 2: Replace `end` call sites**

Replace `kw('end')` with `$.end_keyword` (no precedence on end).
**EXCLUDE** `alias(kw('end'), $.identifier)` at lines 4565, 6436, 8356 — keep as-is.
**INCLUDE** line ~1915 (`shortcut_key_property` value context).

Sites to convert: lines ~1915, 5930, 5982, 6003, 6022, 6201, 6601

- [ ] **Step 3: Replace `if` and `then` call sites**

Replace `kw('if', 10)` with `prec(10, $.if_keyword)` and `kw('then', 10)` with `prec(10, $.then_keyword)`.

`if` sites: ~5938, 5958, 5974, 5991, 6013, 6034, 6042, 6052, 6551
`then` sites: ~5940, 5960, 5976, 5993, 6015, 6036, 6044, 6054, 6553

- [ ] **Step 4: Replace `else` call sites**

Replace `kw('else', 10)` with `prec(10, $.else_keyword)`. All `else` sites carry precedence 10.

Sites: ~5206, 5945, 5995, 6017, 6559, 6760

- [ ] **Step 5: Replace `case` and `of` call sites**

Replace `kw('case', 10)` → `prec(10, $.case_keyword)`.
Replace `kw('of', 10)` → `prec(10, $.of_keyword)` at case statement site (~6595).
Replace `kw('of')` → `$.of_keyword` at type sites (~4843, 4851, 5110) — no precedence in type context.

`case` sites: ~6593
`of` sites: ~4843 (list_type), 4851 (dictionary_type), 5110 (array_type), 6595 (case_statement)

- [ ] **Step 6: Replace `while`, `do`, `for`, `foreach`, `repeat`, `until` call sites**

Replace each `kw('keyword')` or `kw('keyword', N)` with `$.keyword_keyword` or `prec(N, $.keyword_keyword)`.

`while`: ~6245; `do`: ~6247, 6257, 6280, 6292; `for`: ~6265;
`foreach`: ~6288; `repeat`: ~6302; `until`: ~6304

- [ ] **Step 7: Replace `var` call sites**

Replace `kw('var')` with `$.var_keyword`.
Also update `modifier: $ => kw('var')` to `modifier: $ => $.var_keyword`.

Sites: ~4476 (var_section), 6098 (modifier)

- [ ] **Step 8: Replace `procedure` call sites**

Replace `kw('procedure')` with `$.procedure_keyword`.

Sites: ~2335, 2370, 5829, 5860, 5906, 6069

- [ ] **Step 9: Replace `trigger` call sites**

Replace `kw('trigger')` with `$.trigger_keyword`.
Note: `_trigger_keyword` rule (line 8346) may need dedup or removal.

Sites: ~1699 (fileuploadaction_trigger), ~3317 (trigger_declaration), plus any through `_trigger_keyword`

- [ ] **Step 10: Intermediate validation**

Run: `tree-sitter generate`
Expected: Success. This catches errors before continuing with remaining keywords.

- [ ] **Step 11: Replace remaining Tier 1 keywords**

All of these carry precedence — preserve it at call sites:

- `exit`: `kw('exit', 10)` → `prec(10, $.exit_keyword)` (site: ~6309)
- `break`: only in `_enum_keyword` — convert there (Task 5)
- `continue`: `kw('continue', 10)` → `prec(10, $.continue_keyword)` (site: ~6318). Leave `continue_as_identifier` scanner token unchanged. Note: outer `prec(13, ...)` wrapping the rule stays.
- `with`: `kw('with', 10)` → `prec(10, $.with_keyword)` (site: ~6255)
- `asserterror`: `kw('asserterror', 10)` → `prec(10, $.asserterror_keyword)` (sites: ~6323, 6330)
- `in`: `kw('in', 10)` → `prec(10, $.in_keyword)` for foreach usage (site: ~6290). Leave `in_operator` as-is.

- [ ] **Step 12: Verify generation succeeds**

Run: `tree-sitter generate`
Expected: Success.

---

## Task 3: Replace Tier 2 Call Sites (Object Types & Structure)

**Files:**
- Modify: `grammar.js` — replace all inline `kw()` calls for Tier 2 keywords

- [ ] **Step 1: Replace object declaration keywords**

For each object type, replace `kw('objecttype')` with `$.objecttype_keyword` in the declaration rules.

Key patterns:
```
table_declaration:     kw('table')     → $.table_keyword
tableextension_declaration: kw('tableextension') → $.tableextension_keyword
page_declaration:      kw('page')      → $.page_keyword
pageextension_declaration:  kw('pageextension')  → $.pageextension_keyword
codeunit_declaration:  kw('codeunit')  → $.codeunit_keyword
report_declaration:    kw('report')    → $.report_keyword
reportextension_declaration: kw('reportextension') → $.reportextension_keyword
query_declaration:     kw('query')     → $.query_keyword
xmlport_declaration:   kw('xmlport')   → $.xmlport_keyword
enum_declaration:      kw('enum')      → $.enum_keyword
enumextension_declaration: kw('enumextension') → $.enumextension_keyword
interface_declaration: kw('interface') → $.interface_keyword
controladdin_declaration: kw('controladdin') → $.controladdin_keyword
dotnet_declaration:    kw('dotnet')    → $.dotnet_keyword
profile_declaration:   kw('profile')   → $.profile_keyword
profileextension_declaration: kw('profileextension') → $.profileextension_keyword
permissionset_declaration: kw('permissionset') → $.permissionset_keyword
permissionsetextension_declaration: kw('permissionsetextension') → $.permissionsetextension_keyword
entitlement_declaration: kw('entitlement') → $.entitlement_keyword
pagecustomization_declaration: kw('pagecustomization') → $.pagecustomization_keyword
```

**IMPORTANT:** Also replace `kw()` calls for these keywords in type references (e.g., `kw('codeunit')` in `codeunit_type`, `kw('page')` in `page_type`, etc.). Search for each keyword across the entire file.

**EXCLUDE:** `alias(kw('enum'), $.identifier)` sites and `kw_with_coloncolon()` sites.

- [ ] **Step 2: Replace structure keywords**

```
namespace_declaration: kw('namespace') → $.namespace_keyword
using_statement:       kw('using')     → $.using_keyword
implements_clause:     kw('implements') → $.implements_keyword
extends (various):     kw('extends')   → $.extends_keyword
customizes:            kw('customizes') → $.customizes_keyword
```

Search for ALL `kw('extends')` occurrences — it appears in multiple extension declarations.

- [ ] **Step 3: Verify generation succeeds**

Run: `tree-sitter generate`
Expected: Success.

---

## Task 4: Replace Tier 3 Call Sites (Sections & Modifiers)

**Files:**
- Modify: `grammar.js` — replace all inline `kw()` and bare string calls for Tier 3 keywords

- [ ] **Step 1: Replace section keywords**

For each section keyword, find all `kw('keyword')` calls and replace with `$.keyword_keyword`.

```
fields:      kw('fields')      → $.fields_keyword
keys:        kw('keys')        → $.keys_keyword
key:         kw('key')         → $.key_keyword
fieldgroups: kw('fieldgroups') → $.fieldgroups_keyword
fieldgroup:  kw('fieldgroup')  → $.fieldgroup_keyword
dataset:     kw('dataset')     → $.dataset_keyword
elements:    kw('elements')    → $.elements_keyword
labels:      kw('labels')      → $.labels_keyword
rendering:   kw('rendering')   → $.rendering_keyword
requestpage: kw('requestpage') → $.requestpage_keyword
schema:      kw('schema')      → $.schema_keyword
views:       kw('views')       → $.views_keyword
```

- [ ] **Step 2: Replace `actions` and `layout` bare string patterns**

These use `choice('actions', 'Actions', 'ACTIONS')` — replace with `$.actions_keyword` and `$.layout_keyword` (which wrap the same pattern in the named rule).

`actions` site: ~1466
`layout` sites: ~2474, 2901

- [ ] **Step 3: Replace layout element keywords**

```
area:        kw('area')        → $.area_keyword
group:       kw('group')       → $.group_keyword
repeater:    kw('repeater')    → $.repeater_keyword
cuegroup:    kw('cuegroup')    → $.cuegroup_keyword
fixed:       kw('fixed')       → $.fixed_keyword
grid:        kw('grid')        → $.grid_keyword
part:        kw('part')        → $.part_keyword
systempart:  kw('systempart')  → $.systempart_keyword
usercontrol: kw('usercontrol') → $.usercontrol_keyword
chartpart:   kw('chartpart')   → $.chartpart_keyword
```

- [ ] **Step 4: Replace data/query element keywords**

```
dataitem:  kw('dataitem')  → $.dataitem_keyword
column:    kw('column')    → $.column_keyword
filter:    kw('filter')    → $.filter_keyword
view:      kw('view')      → $.view_keyword (only kw() sites, not bare 'view')
```

Note: `filter` has an existing `_filter_keyword` rule that may need dedup.

- [ ] **Step 5: Replace modifier keywords**

Update `procedure_modifier` rule:
```javascript
// Before
procedure_modifier: $ => choice(kw('local'), kw('internal'), kw('protected')),
// After
procedure_modifier: $ => choice($.local_keyword, $.internal_keyword, $.protected_keyword),
```

Also replace standalone modifier keyword sites outside `procedure_modifier`:
- `kw('local')` at line ~2281 (entitlement_role_type_property value) → `$.local_keyword`
- `kw('internal')` at lines ~2355 (interface access), ~3715 (access_value) → `$.internal_keyword`
- `kw('protected')` at line ~4475 (protected var section) → `$.protected_keyword`

Replace `kw('event')` with `$.event_keyword` (site: ~2326).

Handle `temporary`:
- The existing `temporary` named rule (line ~6192) uses `kw('temporary')` — update to reference `$.temporary_keyword`.
- Replace `kw('temporary')` at line ~3560 (table_type_value) → `$.temporary_keyword`.

- [ ] **Step 6: Verify generation succeeds**

Run: `tree-sitter generate`
Expected: Success.

---

## Task 5: Update `_enum_keyword` Rule

**Files:**
- Modify: `grammar.js` — update `_enum_keyword` to use named keyword rules

- [ ] **Step 1: Find `_enum_keyword` rule**

Search for `_enum_keyword:` in `grammar.js` (around line 7561).

- [ ] **Step 2: Replace all `kw()` calls with named keyword references**

Every `kw('If')`, `kw('Begin')`, `kw('Table')`, etc. inside `_enum_keyword` should be replaced with the corresponding `$.if_keyword`, `$.begin_keyword`, `$.table_keyword`, etc.

Note: `_enum_keyword` uses title-case in `kw()` calls (e.g., `kw('If')` not `kw('if')`), but since `kw()` is case-insensitive, the named rule `if_keyword: $ => kw('if')` matches the same tokens. The replacement is safe.

- [ ] **Step 3: Verify generation succeeds**

Run: `tree-sitter generate`
Expected: Success.

---

## Task 6: Handle Existing Named Rules (Dedup & Cleanup)

**Files:**
- Modify: `grammar.js` — resolve conflicts between new keyword rules and existing rules

- [ ] **Step 1: Handle `_trigger_keyword` (line ~8346)**

If `_trigger_keyword` just wraps `kw('trigger')`, it can be replaced by `$.trigger_keyword`. Update all references from `$._trigger_keyword` to `$.trigger_keyword`.

- [ ] **Step 2: Handle `_filter_keyword` (line ~8632)**

If `_filter_keyword` wraps `kw('filter')`, replace with `$.filter_keyword`. Update all references.

- [ ] **Step 3: Handle `temporary` rule (line ~6192)**

The existing `temporary` named rule wraps `kw('temporary')`. Options:
- **Option A:** Change `temporary` to reference the new keyword: `temporary: $ => $.temporary_keyword`
- **Option B:** Remove `temporary_keyword` and keep `temporary` as-is (it's already a named rule wrapping a keyword)

Option B is simpler — just rename the existing `temporary` to `temporary_keyword` and update all references. But this changes the node name in the parse tree from `temporary` to `temporary_keyword`. Choose based on whether existing queries reference `(temporary)` — they do in `highlights.scm`.

**Recommended:** Keep `temporary` as a wrapper: `temporary: $ => $.temporary_keyword`. This preserves backward compatibility in queries while also exposing the keyword.

- [ ] **Step 4: Handle `modifier` rule (line ~6098)**

Already handled in Task 2 Step 7: `modifier: $ => $.var_keyword`.

- [ ] **Step 5: Verify generation succeeds**

Run: `tree-sitter generate`
Expected: Success. Note final state count.

---

## Task 7: Validate Grammar

**Files:**
- Read: `grammar.js`, `src/parser.c`

- [ ] **Step 1: Generate parser**

Run: `tree-sitter generate`
Expected: Success.

- [ ] **Step 2: Check state count**

Run: `grep 'STATE_COUNT' src/parser.c`
Expected: A number. If > 59,000 (2x baseline of 29,345), stop and reduce scope per spec.

- [ ] **Step 3: Verify keyword nodes in node-types.json**

Run: `grep -c '_keyword' src/node-types.json`
Expected: ~80+ entries (one per keyword rule, plus existing ones).

- [ ] **Step 4: Spot-check for ERROR/MISSING nodes**

Parse a few production files to verify no regressions:
```bash
tree-sitter parse "./BC.History/APIReportsFinance/Source/API Reports - Finance/src/APIFinanceAccPeriods.Page.al" 2>&1 | grep -c ERROR
```
Expected: 0

- [ ] **Step 5: Update test expectations**

Run: `tree-sitter test -u`
Expected: All 1225 tests updated with new keyword nodes in parse trees.

- [ ] **Step 6: Run test suite**

Run: `tree-sitter test`
Expected: 1225/1225 tests pass.

- [ ] **Step 7: Run full production parse**

Run: `./validate-grammar.sh --full`
Expected: 99.91% success rate maintained (14 or fewer errors on 15,358 files).

---

## Task 8: Update Query Files

**Files:**
- Modify: `queries/highlights.scm`
- Modify: `queries/locals.scm`
- Modify: `queries/tags.scm`
- Modify: `queries/indents.scm`
- Modify: `queries/folds.scm`

- [ ] **Step 1: Update highlights.scm with keyword nodes**

Add keyword highlight groups using the new named nodes:

```scheme
; Control flow keywords
[
  (if_keyword) (then_keyword) (else_keyword)
  (case_keyword) (of_keyword)
  (while_keyword) (do_keyword)
  (for_keyword) (foreach_keyword) (in_keyword)
  (repeat_keyword) (until_keyword)
  (exit_keyword) (break_keyword) (continue_keyword)
  (with_keyword) (asserterror_keyword)
] @keyword.control

; Block delimiters
[(begin_keyword) (end_keyword)] @keyword

; Declaration keywords
[(procedure_keyword) (trigger_keyword) (var_keyword) (event_keyword)] @keyword.declaration

; Object type keywords
[
  (table_keyword) (tableextension_keyword)
  (page_keyword) (pageextension_keyword)
  (codeunit_keyword)
  (report_keyword) (reportextension_keyword)
  (query_keyword) (xmlport_keyword)
  (enum_keyword) (enumextension_keyword)
  (interface_keyword) (controladdin_keyword)
  (dotnet_keyword)
  (profile_keyword) (profileextension_keyword)
  (permissionset_keyword) (permissionsetextension_keyword)
  (entitlement_keyword) (pagecustomization_keyword)
] @keyword.type

; Structure keywords
[
  (namespace_keyword) (using_keyword)
  (extends_keyword) (implements_keyword) (customizes_keyword)
] @keyword.import

; Section keywords
[
  (fields_keyword) (keys_keyword) (key_keyword)
  (fieldgroups_keyword) (fieldgroup_keyword)
  (actions_keyword) (layout_keyword)
  (area_keyword) (group_keyword) (repeater_keyword)
  (cuegroup_keyword) (fixed_keyword) (grid_keyword)
  (part_keyword) (systempart_keyword) (usercontrol_keyword) (chartpart_keyword)
  (dataset_keyword) (elements_keyword) (dataitem_keyword)
  (column_keyword) (filter_keyword)
  (labels_keyword) (rendering_keyword) (requestpage_keyword)
  (schema_keyword) (views_keyword) (view_keyword)
] @keyword.structure

; Modifier keywords
[(local_keyword) (internal_keyword) (protected_keyword) (temporary_keyword)] @keyword.modifier
```

Remove now-redundant highlights that used parent nodes for keyword highlighting:
- Remove `(procedure_modifier) @keyword.modifier` — individual keywords now captured
- Remove `(modifier) @keyword.modifier` — `var_keyword` now captured via `@keyword.declaration`
- Remove `(temporary) @keyword.modifier` — `temporary_keyword` now captured
- Keep `(procedure_modifier)` if you want it as a secondary capture for different styling

- [ ] **Step 2: Update locals.scm if needed**

Check if any new keyword nodes create scope or definition issues. Likely no changes needed — keyword nodes are leaf nodes.

- [ ] **Step 3: Update tags.scm if needed**

Likely no changes — tags captures use field names and parent nodes, not keyword tokens.

- [ ] **Step 4: Update indents.scm if needed**

Consider whether `(begin_keyword)` and `(end_keyword)` can improve indentation precision. Likely minor or no changes.

- [ ] **Step 5: Update folds.scm if needed**

Likely no changes — fold regions are defined by parent nodes.

- [ ] **Step 6: Validate all query files**

Run:
```bash
for qf in queries/*.scm; do
  echo "=== $qf ===" && tree-sitter query "$qf" /tmp/test_queries.al 2>&1 | head -3
done
```
Expected: No errors in any query file.

---

## Task 9: Final Validation & Commit

**Files:**
- All modified files

- [ ] **Step 1: Run full test suite**

Run: `tree-sitter test`
Expected: All tests pass.

- [ ] **Step 2: Run highlight test**

Create a test file covering all keyword tiers and verify highlighting works:
```bash
echo 'codeunit 50100 "Test" { var x: Integer; procedure Foo() begin if true then exit; end; }' > /tmp/kw_test.al
tree-sitter highlight /tmp/kw_test.al
```
Expected: Keywords appear highlighted (colored) in output.

- [ ] **Step 3: Run full production parse**

Run: `./validate-grammar.sh --full`
Expected: 99.91% success rate maintained.

- [ ] **Step 4: Record metrics**

Document in commit message:
- New state count vs baseline (29,345)
- Test count (should still be 1225)
- Production parse success rate
- Number of new keyword node types added

- [ ] **Step 5: Commit**

```bash
git add grammar.js src/parser.c src/node-types.json queries/
git commit -m "feat: expose ~80 keywords as named nodes for query matching

Add named rules (e.g., begin_keyword, if_keyword, table_keyword) for all
AL keywords so they appear in the parse tree and can be matched in
tree-sitter queries for syntax highlighting.

Follows Pascal grammar pattern (kBegin, kEnd, kIf) adapted to AL naming
convention (_keyword suffix).

State count: XXXXX (was 29,345)
[BC.History: XX errors, XX.XX% success]"
```
