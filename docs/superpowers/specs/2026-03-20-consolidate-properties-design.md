# Design: Consolidate Simple Properties into Generic Rule

**Date:** 2026-03-20
**Status:** Approved

## Problem

The AL grammar has 291 individual property rules (`caption_property`, `editable_property`, etc.), contributing to a SYMBOL_COUNT of 2,249 and a parser.c of 106 MB — nearly 4x larger than C# (29 MB). This exceeds GitHub's 100 MB file size limit, preventing pushes. The individual property rules provide parse-time value type validation (e.g., Caption only accepts strings), but no tree-sitter grammar does this — validation belongs in linters/LSP servers.

## Solution

Replace 241 simple property rules with a single `generic_property` rule. Keep 56 complex properties that have unique syntax (formulas, field references, ML lists, etc.).

## Generic Property Rule

```javascript
generic_property: $ => seq(
  field('name', $.identifier),
  '=',
  field('value', $._expression),
  ';'
),
```

The value uses `$._expression` as a single, comprehensive alternative. This subsumes all value types (strings, integers, booleans, identifiers, member expressions, etc.) and also handles expression-accepting properties (see below). The `;` terminator unambiguously ends the property value.

Note: `generic_property` already exists in the grammar and is used as a fallback. This change expands its role to replace all simple properties.

## Expression-Accepting Properties

Nine properties accept full expressions via `_expression_property_template`. These are consolidated into `generic_property` since `$._expression` covers them:

- `enabled_property`, `editable_property`, `hide_value_property`, `show_mandatory_property` — boolean expressions
- `auto_format_expression_property` — string/expression
- `init_value_property`, `max_value_property`, `min_value_property` — numeric expressions
- `indentation_column_property` — expression
- `visible_property`, `caption_class_property` — also accept expressions
- `source_expr_property` — member expressions and field access

All of these are simple `Name = Expression;` patterns that `generic_property` handles.

## Case-Insensitivity and kw_with_eq() Disambiguation

Individual property rules currently use `kw('PropertyName')` or `kw_with_eq('propertyname')` for case-insensitive matching. After consolidation:

- **Property names match via `$.identifier`**, which is the grammar's `word` rule. Since `identifier` matches any casing, `Editable`, `EDITABLE`, `editable` all match. Note: the `name` field will contain the source casing as-is (e.g., `editable` not `Editable`) — AST consumers should case-fold when comparing property names.

- **`kw_with_eq()` properties** (including but not limited to `Visible`, `Filters`, `IsPreview`, `Description`, `Style`, `StyleExpr`, `HelpLink`, `Width`, `Importance`, `Subtype`, `SourceTable`, `TableNo`, `ShowFilter`, `IncludeCaption`, `InDataSet`, `CaptionClass`, and others) currently use a regex that includes `=` to disambiguate from variable names. After consolidation, all `kw_with_eq()` matchers for consolidated simple properties are deleted (identify by searching grammar.js for `kw_with_eq` in rules being removed). The disambiguation still works because:
  - In **property context** (inside object body `{ ... }`), `generic_property` matches `Identifier = Value ;`
  - In **variable context** (inside `var` section), `variable_declaration` matches `Identifier : Type ;`
  - The `:` vs `=` after the identifier is what distinguishes them, not the `kw_with_eq()` lookahead
  - The contextual keyword aliases (`alias('Style', $.identifier)`, etc.) in `_contextual_keyword_aliases` / `_unquoted_variable_name` remain unchanged for variable-name disambiguation

## Complex Properties to Keep (56)

These have unique syntax that cannot be captured by the generic rule:

### Formula/Calc Properties
- `calc_formula_property` — `sum/count/lookup/average/min/max/exist(Table where(...))`
- `table_relation_property` — `Table.Field where(...)` with if/else branching

### Permission Properties
- `permissions_property` — `tabledata X = RIMD, tabledata Y = R`
- `permissionset_permissions` — same permission list structure
- `access_by_permission_property` — `tabledata X = RIMD`
- `test_permissions_property` — typed enum alias

### Link/Filter Properties
- `data_item_link_property` — `Field = FIELD(OtherField)` pairs
- `data_item_table_filter_property` — `Field = FILTER(expr)` pairs
- `sub_page_link_property` — `Field = CONST(v), Field = FIELD(x)` with preprocessor
- `run_page_link_property` — `Field = CONST(v)` / `FIELD(x)` / `FILTER(expr)`
- `link_fields_property` — `Field = FIELD(Other)` field mapping pairs
- `column_filter_property` — `Field = FILTER(expr)` or `CONST(v)`

### View Properties
- `source_table_view_property` — `SORTING(f1,f2) ORDER(asc) WHERE(...)`
- `run_page_view_property` — same compound view syntax
- `sub_page_view_property` — same
- `data_item_table_view_property` — same
- `view_filters_property` — `where(...)` clause
- `view_order_by_property` — sorting clause
- `order_by_property` — `ascending(F1, F2), descending(F3)`

### ML (Multilingual) Properties
- `caption_ml_property` — `ENU='English', DEU='German'`
- `option_caption_ml_property`, `tool_tip_ml_property`, `about_title_ml_property`, `about_text_ml_property`, `instructional_text_ml_property`, `request_filter_heading_ml_property`, `additional_search_terms_ml_property`, `entity_caption_ml_property`, `entity_set_caption_ml_property`

### Properties with Sub-fields (Locked/Comment)
- `caption_property` — `'text', Locked = true, Comment = '...'`
- `tool_tip_property` — same optional sub-properties
- `about_title_property`, `about_text_property` — same
- `instructional_text_property` — same
- `option_caption_property` — string with optional per-value captions

### List Properties (comma-separated values)
- `application_area_property` — `X, Y, Z`
- `calc_fields_property`, `data_caption_fields_property`, `request_filter_fields_property`, `odata_key_fields_property` — field lists
- `column_store_index_property`, `sql_index_property`, `sum_index_fields_property`, `included_fields_property` — key field lists
- `option_members_property` — identifier list
- `object_entitlements_property`, `included_permission_sets_property`, `excluded_permission_sets_property` — identifier lists
- `profile_customizations_property` — name list
- `api_version_property` — repeated string list
- `namespaces_property` — `prefix = 'uri'` pairs

### Other Complex Properties
- `decimal_places_property` — `2:5` colon syntax
- `implementation_property`, `default_implementation_property`, `unknown_value_implementation_property` — `Interface = Codeunit` pairs
- `assembly_property` — `choice(Version=..., Culture=..., PublicKeyToken=...)`

## Migration Pattern

### Choice List Updates

In each property choice list (`_universal_properties`, `_page_properties`, `_table_properties`, etc.), replace all simple property entries with `$.generic_property` as the **last** alternative:

```javascript
_table_properties: $ => choice(
  // Complex properties first (tried before generic)
  $.calc_formula_property,
  $.table_relation_property,
  $.permissions_property,
  // ... other complex properties for this context

  // Generic catches all simple properties last
  $.generic_property,
),
```

### Cleanup

1. Delete all 241 simple property rule definitions from grammar.js
2. Delete value type rules used exclusively by simple properties (e.g., `obsolete_state_value`, `usage_category_value`, `extended_datatype_value`, etc.). These enum value rules provided parse-time validation that is now intentionally removed — any identifier is accepted as a property value. Identify exclusively-used value rules by searching for references; keep any shared with complex properties.
3. Replace simple property entries in all choice lists with `$.generic_property`
4. Remove `kw_with_eq()` matchers for consolidated properties — disambiguation is handled by syntactic context (`:` for variables vs `=` for properties)

### Precedence

The current `generic_property` has `prec(10, ...)`. After consolidation, review whether this value is appropriate. Since `generic_property` is the last alternative in each choice list, its precedence only matters relative to other constructs at the same level (statements, triggers, etc.). With `$._expression` as the value, the `;` terminator prevents ambiguity with expression statements. Keep `prec(10)` unless generation reveals conflicts.

### Parse Tree Change

Before:
```
(property
  (editable_property
    value: (boolean)))
```

After:
```
(generic_property
  name: (identifier)
  value: (boolean))
```

## Expected Impact

| Metric | Before | After (estimated) |
|--------|--------|-------------------|
| SYMBOL_COUNT | 2,249 | ~1,950 |
| parser.c size | 106 MB | ~70-80 MB |
| Property rules | 291 | ~56 |
| Production parse rate | 99.91% | 99.91% or better |

## Validation

1. `tree-sitter generate` — must succeed
2. `tree-sitter test -u` — update test expectations (property node types change)
3. **Manually review the diff** produced by `-u` to confirm no ERROR or MISSING nodes crept in. Per CLAUDE.md: "Use `tree-sitter test -u` only if no ERROR/MISSING nodes exist."
4. `tree-sitter test` — all tests pass
5. Production parse — maintain 99.91% (14 errors on 15,358 files)
6. Verify parser.c < 100 MB
7. `git push` — must succeed

## Risk

**Low risk.** The generic property rule accepts a superset of what the individual rules accepted. No valid AL code will fail to parse. Some previously-rejected invalid property values will now parse — this is the intended behavior, consistent with all other tree-sitter grammars. Enum value rules (e.g., `obsolete_state_value` accepting only `Pending`/`Removed`) are intentionally opened to accept any identifier.

**Rollback:** Single commit, single `git revert`.
