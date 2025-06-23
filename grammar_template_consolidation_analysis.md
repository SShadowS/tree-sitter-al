# Grammar Template Consolidation Analysis

## Executive Summary

The tree-sitter-al grammar has significant opportunities for consolidation using template functions. Analysis reveals that over 250 property definitions manually implement patterns that could use existing or new templates, leading to unnecessary code duplication and maintenance overhead.

## Key Findings

### 1. Properties Not Using `_value_property_template` (50+ instances)

Many properties manually implement the `seq(keyword, '=', field('value', value), ';')` pattern instead of using the existing `_value_property_template`.

#### Examples of Manual Implementation:
```javascript
// Current (manual):
request_filter_fields_property: $ => seq(
  kw('requestfilterfields'),
  '=',
  field('value', $.request_filter_fields_value),
  ';'
),

// Should be:
request_filter_fields_property: _value_property_template(
  $ => kw('requestfilterfields'),
  $ => $.request_filter_fields_value
),
```

#### Properties to Refactor:
- `request_filter_fields_property`
- `order_by_property`
- `source_table_property`
- `table_no_property`
- `odata_key_fields_property`
- `data_item_link_property`
- `application_area_property`
- `page_type_property`
- `run_object_property`
- `promoted_category_property`
- `drilldown_pageid_property`
- `lookup_pageid_property`
- `card_page_id_property`
- `navigation_page_id_property`
- `implementation_property`
- `rendering_type_property`
- `entitlement_type_property`
- `object_entitlements_property`
- `permissionset_permissions`
- `view_filters_property`
- `sub_page_link_property`
- `source_expr_property`
- `grid_layout_property`
- `data_caption_fields_property`
- And many more...

### 2. Properties Using Predefined Templates Inconsistently

Some properties use templates like `_boolean_property_template` with `seq()` wrapper when they could use `_value_property_template`:

```javascript
// Current:
auto_replace_property: $ => seq(
  kw('AutoReplace'),
  $_boolean_property_template
),

// Should be:
auto_replace_property: _value_property_template(
  $ => kw('AutoReplace'),
  $ => $.boolean
),
```

### 3. Common Value Patterns That Need Templates

#### A. Identifier List Pattern
Many properties use lists of identifiers with the same structure:
```javascript
// Pattern: identifier, repeat(seq(',', identifier))
// Used in: request_filter_fields, odata_key_fields, object_entitlements, 
// included_permission_sets, excluded_permission_sets, column_store_index,
// included_fields, sql_index, sum_index_fields
```

**Suggested Template:**
```javascript
function _identifier_list_value_template() {
  return $ => field('value', $._identifier_choice_list);
}
```

#### B. Flexible Identifier List Pattern
Similar to above but allows string literals:
```javascript
// Used in: application_area, values_allowed, data_caption_fields,
// cuegroup_layout, freeze_column, custom_action_type, various layout properties
```

**Suggested Template:**
```javascript
function _flexible_identifier_list_value_template() {
  return $ => field('value', seq(
    $._flexible_identifier_choice,
    repeat(seq(',', $._flexible_identifier_choice))
  ));
}
```

#### C. Simple Enum Pattern
Properties with a choice of keyword values:
```javascript
// Used in: tree_initial_state, grid_layout, compression_type, access,
// obsolete_state, extended_datatype, test_permissions, show_as,
// preview_mode, transaction_type, pdf_font_embedding
```

**Suggested Template:**
```javascript
function _simple_enum_value_template(...choices) {
  return $ => field('value', choice(...choices.map(c => kw(c))));
}
```

#### D. Page ID Reference Pattern
```javascript
// Used in: drilldown_pageid, lookup_pageid, card_page_id, navigation_page_id
```

**Suggested Template:**
```javascript
function _page_id_value_template() {
  return $ => field('value', $.page_id_value);
}
```

### 4. Complex Patterns with Shared Sub-structures

#### String with Attributes Pattern
The pattern for strings with optional locked/comment/maxlength attributes appears in:
- `instructional_text_property`
- `label_declaration`
- `_caption_full_template`
- `_about_template`

**Suggested Template:**
```javascript
function _string_with_attributes_template(includeMaxLength = false) {
  return $ => seq(
    field('value', $.string_literal),
    repeat(seq(',',
      choice(
        seq(kw('locked'), '=', $.boolean),
        seq(kw('comment'), '=', $.string_literal),
        includeMaxLength ? seq(kw('maxlength'), '=', $.integer) : null
      ).filter(Boolean)
    ))
  );
}
```

## Implementation Recommendations

### Phase 1: Apply Existing Templates (Quick Wins)
1. Replace all manual `seq(name, '=', value, ';')` with `_value_property_template`
2. Simplify boolean properties to use `_value_property_template(name, $ => $.boolean)`
3. Simplify string properties to use `_value_property_template(name, $ => $.string_literal)`

### Phase 2: Create New Value Templates
1. Implement the suggested templates for common value patterns
2. Apply these templates to existing properties
3. Update documentation to encourage template usage

### Phase 3: Consolidate Complex Patterns
1. Implement `_string_with_attributes_template`
2. Refactor affected properties
3. Look for other complex patterns that can be consolidated

## Expected Benefits

1. **Code Reduction**: Estimated 30-40% reduction in property definition lines
2. **Consistency**: All properties follow standardized patterns
3. **Maintainability**: Changes to property structure only need updates in templates
4. **Readability**: Clearer intent with less boilerplate
5. **Error Prevention**: Reduced chance of missing semicolons, field wrappers, etc.

## Example Refactoring

### Before (15 lines):
```javascript
application_area_property: $ => seq(
  kw('applicationarea'),
  '=',
  field('value', seq(
    $._flexible_identifier_choice,
    repeat(seq(',', $._flexible_identifier_choice))
  )),
  ';'
),
```

### After (4 lines):
```javascript
application_area_property: _value_property_template(
  $ => kw('applicationarea'),
  _flexible_identifier_list_value_template()
),
```

## Validation Steps

1. Run `./validate-grammar.sh` after each refactoring batch
2. Ensure all tests continue to pass
3. Test with real AL files to verify parsing behavior remains consistent
4. Check for any performance impacts (template functions should have minimal overhead)