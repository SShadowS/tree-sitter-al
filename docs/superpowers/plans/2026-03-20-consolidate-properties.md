# Consolidate Simple Properties — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace 241 simple property rules with a single `generic_property` rule to reduce parser.c from 106 MB to under 100 MB.

**Architecture:** Expand the existing `generic_property` rule to accept `$._expression` as its value, add it as a fallback to all property choice lists, then delete simple property rules and their exclusive value types. Single big-bang commit.

**Tech Stack:** tree-sitter grammar.js DSL

**Spec:** `docs/superpowers/specs/2026-03-20-consolidate-properties-design.md`

---

## Pre-Implementation Notes

### Key Facts

- `generic_property` already exists at line ~1412. It currently accepts only `identifier | quoted_identifier | string | integer | boolean`. It needs to be expanded to `$._expression`.
- All `kw_with_eq()` calls are in COMPLEX properties that stay. No `kw_with_eq()` removal needed.
- Property choice lists use a hierarchy: `_page_properties` includes `_universal_properties`, `_display_properties`, etc. Add `$.generic_property` to every list that contains simple properties.
- `generic_property` must be the LAST entry in each choice list so complex properties are tried first.
- The `property` wrapper rule (which wraps individual property rules into a named node) may need updating — check how it interacts with `generic_property`.

### The `property` Wrapper Rule

There is a `property` rule (~line 4259) that contains ~50 individual property entries. It is used in:
- `property_list` — used in preproc contexts
- `_key_properties` — key declarations
- `fieldgroup_declaration` — alongside `caption_property`
- `preproc_conditional_object_properties` — codeunit preprocessor conditionals

This rule MUST be updated in parallel with the semantic category lists: add `$.generic_property` as last entry, remove simple property entries, keep complex ones. If simple rules are deleted from `property` but the references remain, `tree-sitter generate` will fail with "undefined rule" errors.

### How to Identify Simple Properties

A property is SIMPLE if it follows one of these patterns:
- `_value_property_template(kw('Name'), $ => simple_value)` — Name = Value ;
- `seq(kw('Name'), $._boolean_property_template)` — Name = Boolean ;
- `seq(kw('Name'), $._string_property_template)` — Name = String ;
- `seq(kw('Name'), $._identifier_property_template)` — Name = Identifier ;
- `seq(kw('Name'), $._expression_property_template)` — Name = Expression ;
- `seq(kw('Name'), $._integer_property_template)` — Name = Integer ;
- Any `seq(kw/choice/literal('Name'), '=', field('value', simple_type), ';')`
- **Bare string literal patterns** like `seq('AutoSplitKey', $._boolean_property_template)` or `seq('PromotedOnly', ...)` — these also qualify as SIMPLE

A property is COMPLEX if it has:
- `kw_with_eq()` — needed for disambiguation
- ML list values (`ml_value_list`)
- Comma-separated field lists
- Where clauses, FIELD() functions, FILTER() functions
- Sub-properties (Locked, Comment, MaxLength)
- Permission lists (tabledata X = RIMD)
- Multiple nested seq/choice structures beyond `Name = Value ;`
- Special precedence (`prec(N, ...)`) that may be needed for disambiguation — e.g., `shortcut_key_property` uses `prec(8)` and accepts keyword aliases (`kw('return')`, `kw('end')`, etc.). **Keep these as complex.**

### Definitive Approach

Rather than classifying each property bottom-up, use the **spec's list of 56 complex properties** as the source of truth. Any property NOT on that list is SIMPLE and gets removed. When in doubt, check the spec.

---

## Task 1: Expand `generic_property` to Accept Expressions

**Files:**
- Modify: `grammar.js` — update `generic_property` rule (~line 1412)

- [ ] **Step 1: Find and update `generic_property`**

Search for `generic_property:` in grammar.js. Change its value from the restricted list to `$._expression`:

```javascript
// Before
generic_property: $ => prec(10, seq(
  field('name', $.identifier),
  '=',
  field('value', choice(
    $.identifier,
    $._quoted_identifier,
    $.string_literal,
    $.integer,
    $.boolean
  )),
  ';'
)),

// After
generic_property: $ => prec(10, seq(
  field('name', $.identifier),
  '=',
  field('value', $._expression),
  ';'
)),
```

- [ ] **Step 2: Verify generation succeeds**

Run: `tree-sitter generate`
Expected: Success.

---

## Task 2: Add `generic_property` to All Property Choice Lists

**Files:**
- Modify: `grammar.js` — add `$.generic_property` as last entry in each property choice list

- [ ] **Step 1: Add to sub-category choice lists**

Search for each of these rules and add `$.generic_property` as the LAST entry in their `choice()`:

- `_universal_properties` (~line 7795)
- `_display_properties` (~line 7833)
- `_validation_properties` (~line 7856)
- `_data_properties` (~line 7874)
- `_navigation_properties` (~line 7893)
- `_access_properties` (~line 7906)

For each, add `$.generic_property` as the last entry. Example:

```javascript
// Before
_universal_properties: $ => choice(
  $.caption_property,
  $.description_property,
  // ...
),

// After
_universal_properties: $ => choice(
  $.caption_property,
  $.description_property,
  // ...
  $.generic_property,  // Catches all simple Name = Value properties
),
```

- [ ] **Step 2: Add to the `property` wrapper rule**

Find the `property` rule (~line 4259). It contains ~50 individual property entries and is used in `property_list`, `_key_properties`, `fieldgroup_declaration`, and `preproc_conditional_object_properties`. Add `$.generic_property` as its last entry.

- [ ] **Step 3: Add to top-level and context-specific choice lists**

Add `$.generic_property` as the last entry in:

- `_page_specific_properties` (~line 7918)
- `_codeunit_specific_properties` (~line 7923)
- `_table_specific_properties` (~line 7929)
- `_report_specific_properties` (~line 7935)
- `_query_properties` (~line 7948)
- `_permissionset_properties` (~line 7968)
- `_controladdin_properties` (~line 7978)
- `_entitlement_properties` (~line 7985)
- `_profile_properties` (~line 7996)
- `_enum_properties` (~line 8015)
- `_field_properties` (~line 8026)
- `_page_properties` (~line 8060)
- `_table_properties` (~line 8153)
- `_codeunit_properties` (~line 8189)
- `_report_properties` (~line 8205)
- `_dataitem_properties` (~line 8252)
- `_report_column_properties` (~line 8268)
- `_xmlport_properties` (~line 8296)
- `_action_properties` (~line 8325)
- `_key_properties` (search for it)
- Any other `_*_properties` choice list

If a list already has `$.generic_property`, don't duplicate it.

- [ ] **Step 4: Verify generation succeeds**

Run: `tree-sitter generate`
Expected: Success. There may be new conflicts — add them to the `conflicts` array if needed.

---

## Task 3: Remove Simple Properties from Choice Lists

**Files:**
- Modify: `grammar.js` — remove simple property entries from all choice lists

- [ ] **Step 1: Remove simple properties from sub-category lists**

For each sub-category list (`_universal_properties`, `_display_properties`, etc.), remove entries that are simple properties. Keep complex properties.

The implementer must check EACH entry against the simple/complex criteria in the Pre-Implementation Notes. When in doubt, check the property's rule definition — if it's more than `Name = SimpleValue ;`, keep it.

**Example — `_universal_properties`:**
```javascript
// Before (30 entries)
_universal_properties: $ => choice(
  $.caption_property,          // COMPLEX (Locked/Comment) — KEEP
  $.caption_ml_property,       // COMPLEX (ML list) — KEEP
  $.caption_class_property,    // COMPLEX (expression) — KEEP
  $.description_property,      // COMPLEX (kw_with_eq) — KEEP
  $.application_area_property, // COMPLEX (comma list) — KEEP
  $.obsolete_reason_property,  // SIMPLE (= string) — REMOVE
  $.obsolete_tag_property,     // SIMPLE (= string) — REMOVE
  // ... check each one
  $.generic_property,          // Catches removed entries
),
```

- [ ] **Step 2: Remove simple properties from top-level lists**

Same process for all top-level and context-specific lists. Work through each list systematically.

- [ ] **Step 3: Remove simple properties from the `property` wrapper rule**

The `property` rule (~line 4259) must have its simple entries removed in parallel with the semantic category lists. Keep complex entries, keep `$.generic_property`.

- [ ] **Step 4: Remove simple properties from `_field_properties`**

`_field_properties` is the largest list. It includes sub-categories plus many individual entries. Remove simple ones like:
`assist_edit_property`, `drill_down_property`, `quick_entry_property`, `title_property`, `sign_displacement_property`, `moved_from_property`, `moved_to_property`, `external_name_property`, `optimize_for_text_search_property`, `image_property`, etc.

- [ ] **Step 5: Remove simple properties from `_page_properties`**

Remove: `delete_allowed_property`, `insert_allowed_property`, `modify_allowed_property`, `source_table_temporary_property`, `analysis_mode_enabled_property`, `auto_split_key_property`, `change_tracking_allowed_property`, `delayed_insert_property`, `links_allowed_property`, `multiple_new_lines_property`, `populate_all_fields_property`, `refresh_on_activate_property`, `save_values_property`, `clear_actions_property`, `clear_layout_property`, `clear_views_property`, `promoted_property`, `promoted_only_property`, `promoted_is_big_property`, `in_footer_bar_property`, etc.

- [ ] **Step 6: Remove simple properties from all remaining lists**

Work through `_report_properties`, `_xmlport_properties`, `_action_properties`, `_dataitem_properties`, `_report_column_properties`, `_table_properties`, `_codeunit_properties`, `_enum_properties`, and any other lists. Use the spec's 56-property keep list as the source of truth.

- [ ] **Step 7: Verify generation succeeds**

Run: `tree-sitter generate`
Expected: Success.

---

## Task 4: Delete Simple Property Rule Definitions

**Files:**
- Modify: `grammar.js` — delete rule definitions for all simple properties

- [ ] **Step 1: Identify all simple property rules to delete**

Search grammar.js for each simple property's rule definition. A simple property looks like:

```javascript
some_property: _value_property_template(kw('SomeName'), $ => $.string_literal),
// or
some_property: $ => seq(kw('SomeName'), $._boolean_property_template),
// or
some_property: $ => seq(kw('SomeName'), '=', field('value', $.boolean), ';'),
```

- [ ] **Step 2: Delete simple property rules in batches**

Work through the grammar file systematically. Delete each simple property rule definition. There are ~241 of these.

**DO NOT DELETE:**
- Complex property rules (see spec for the 56 to keep)
- `generic_property` itself
- Template functions (`_value_property_template`, `_boolean_property_template`, etc.) — some are used by complex properties
- Value type rules shared with complex properties

- [ ] **Step 3: Delete orphaned value type rules**

After deleting simple property rules, search for value rules that are no longer referenced:

```bash
# For each value rule, check if it's still used
grep -n 'some_value' grammar.js
```

Delete value rules that have zero remaining references (excluding their own definition). Examples of likely orphans:
`obsolete_reason_value`, `obsolete_tag_value`, `external_name_value`, `sql_timestamp_value`, `test_table_relation_value`, `paste_is_valid_value`, `sign_displacement_value`, `blank_zero_value`, `closing_dates_value`, `compressed_value`, `not_blank_value`, `numeric_value`, `data_per_company_value`, `replicate_data_value`, `assignment_compatibility_value`, `auto_increment_value`, `extensible_value`, `column_span_value`

- [ ] **Step 4: Delete orphaned template functions**

Check if any template functions are now unused:
- `_boolean_property_template` — check if any complex property still uses it
- `_string_property_template` — same
- `_identifier_property_template` — same
- `_integer_property_template` — same
- `_expression_property_template` — same

Only delete if truly orphaned (zero references outside their definition).

- [ ] **Step 5: Verify generation succeeds**

Run: `tree-sitter generate`
Expected: Success. Fix any "undefined rule" errors by finding missed references.

---

## Task 5: Validate and Finalize

**Files:**
- All modified files

- [ ] **Step 1: Generate parser**

Run: `tree-sitter generate`
Expected: Success.

- [ ] **Step 2: Check parser.c size**

Run: `wc -c src/parser.c`
Expected: Under 100,000,000 bytes (100 MB). Target is ~70-80 MB.

- [ ] **Step 3: Check symbol count**

Run: `grep 'SYMBOL_COUNT' src/parser.c | head -1`
Expected: Significantly less than 2,249 (target ~1,950 or lower).

- [ ] **Step 4: Spot-check production files**

Parse a few files to verify no regressions:
```bash
tree-sitter parse "./BC.History/BaseApp/Source/Base Application/CRM/Reports/ContactCoverSheet.Report.5085.al" 2>&1 | grep ERROR
tree-sitter parse "./BC.History/BaseApp/Source/Base Application/Projects/Project/Reports/ItemsperJob.Report.al" 2>&1 | grep ERROR
```
Expected: No errors.

- [ ] **Step 5: Update test expectations**

**Warning:** This will produce a large diff — ~60+ test files will change from individual property node types (e.g., `(editable_property ...)`) to `(generic_property name: (identifier) value: ...)`. This is expected.

Run: `tree-sitter test -u`

Then manually verify no ERROR or MISSING nodes in updated tests:
```bash
grep -r "ERROR\|MISSING" test/corpus/ | head -5
```
Expected: No ERROR or MISSING in test expectations.

- [ ] **Step 6: Run full test suite**

Run: `tree-sitter test`
Expected: 1225/1225 tests pass (count may change slightly if tests reference deleted nodes).

- [ ] **Step 7: Run full production parse**

Run: `./parse-al-parallel.sh ./BC.History/ .`
Expected: 14 errors (matching baseline). Success rate 99.91%.

- [ ] **Step 8: Validate query files**

Run:
```bash
echo 'codeunit 50100 "T" { var x: Integer; procedure F() begin end; }' > /tmp/qtest.al
for qf in queries/*.scm; do
  result=$(tree-sitter query "$qf" /tmp/qtest.al 2>&1)
  if echo "$result" | grep -q "Error"; then echo "FAIL: $qf"; fi
done
```
Expected: No failures.

- [ ] **Step 9: Commit and push**

```bash
git add grammar.js src/parser.c src/grammar.json src/node-types.json src/tree_sitter/array.h test/corpus/
git commit -m "refactor: consolidate 241 simple properties into generic_property

Replace individual property rules (editable_property, promoted_property,
etc.) with the existing generic_property rule. Complex properties with
unique syntax (CalcFormula, TableRelation, Permissions, ML lists, etc.)
are kept as individual rules.

This reduces SYMBOL_COUNT and parser.c size to under GitHub's 100 MB
file size limit, consistent with how all other tree-sitter grammars
handle properties.

SYMBOL_COUNT: XXXX (was 2,249)
parser.c: XX MB (was 106 MB)
[BC.History: 14 errors, 99.91% success]"

git push
```
