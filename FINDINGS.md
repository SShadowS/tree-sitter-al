# Grammar Analysis Findings

This document outlines opportunities for consolidation and improvement within the `grammar.js` file. The analysis focuses on identifying redundant or overly specific definitions that can be generalized.

## 1. Object Reference Consolidation

**Observation**:
Several properties that refer to AL objects (like Tables or Pages) share a common value pattern but use different or inline rule definitions. The typical pattern for an object reference is a choice between an integer (object ID) and an identifier (object name).

For example:
- `page_id_value`: `choice($.integer, $.identifier, $._quoted_identifier)`
- `source_table_property`: The value is defined inline as `choice($.integer, $.identifier, $._quoted_identifier)`

These rules are functionally identical but are defined separately, leading to redundancy.

**Resolution**:
A new, centralized rule `_object_reference` should be created to represent a generic reference to any AL object.

```javascript
_object_reference: $ => choice($.integer, $.identifier, $._quoted_identifier),
```

All properties that refer to an object by its ID or name should be refactored to use this single rule. This includes:
- `drilldown_pageid_property`
- `lookup_pageid_property`
- `card_page_id_property`
- `source_table_property`

This change will improve maintainability and ensure consistency across the grammar.

## 2. Permission Definition Consolidation

**Observation**:
The grammar defines permission structures in two different places for two different properties: `Permissions` and `AccessByPermission`. The underlying structure of these permissions is identical, but they are built from separate sets of rules.

- For the `Permissions` property, the structure is defined through `permission_value`, `tabledata_permission`, and `object_permission`.
- For the `AccessByPermission` property, the structure is defined through `access_by_permission_value` and `permission_object_type`.

Both boil down to the same pattern: `[type] [name] = [permissions]`, where `type` is `tabledata` or `object`.

**Resolution**:
A single, unified rule named `_permission_definition` should be created to capture this common pattern.

```javascript
_permission_definition: $ => seq(
  field('type', choice(kw('tabledata'), kw('object'))),
  field('name', $._identifier_choice),
  '=',
  field('permissions', choice($.string_literal, $._quoted_identifier))
),
```

Both `permission_value` (for the `Permissions` property) and `access_by_permission_value` (for the `AccessByPermission` property) should be refactored to use this new, consolidated rule. This will eliminate several redundant rules (`tabledata_permission`, `object_permission`, `permission_object_type`, `permission_set`) and simplify the grammar.

## 3. Filter Expression Duplication

**Observation**:
The name `filter_expression` is used for two different rule definitions in the grammar, creating a potential conflict and making the grammar harder to understand.

1.  **Definition 1 (Source View Filter)**: Used within `source_table_view_value`, it is defined as a combination of `where_clause` and `sorting_clause`.
    ```javascript
    filter_expression: $ => seq(
      choice(
        $.where_clause,
        $.sorting_clause,
        seq($.where_clause, $.sorting_clause),
        seq($.sorting_clause, $.where_clause)
      )
    ),
    ```

2.  **Definition 2 (Simple Filter)**: Used within `table_filter_value`, it is defined as a `filter()` function call.
    ```javascript
    filter_expression: $ => seq(
      kw('filter'),
      '(',
      $._filter_value_simple,
      ')'
    ),
    ```

**Resolution**:
These two rules should be renamed to more accurately reflect their specific contexts. This will resolve the name collision and improve the clarity of the grammar.

- **Recommendation**:
  - Rename the first definition to `source_view_filter_expression`.
  - Rename the second definition to `simple_filter_expression`.

This change will make the purpose of each rule explicit and prevent any potential parsing ambiguities.

## 4. Redundant `ident()` function

**Observation**:
The grammar defines a helper function `ident()` that is not used anywhere in the file.

**Resolution**:
The `ident()` function should be removed to clean up the code.

## 5. Overly specific property templates

**Observation**:
The grammar uses several templates for properties (e.g., `_boolean_property_template`, `_string_property_template`, `_identifier_property_template`). These templates are too specific and lead to a proliferation of similar-looking rules.

**Resolution**:
The generic `_value_property_template` should be used more broadly to replace these specific templates. This will require creating more generic value rules (e.g., a generic `_string_value` rule) that can be passed to the template, promoting reusability and reducing the number of rules.

## 6. Inconsistent use of `kw()` for keywords

**Observation**:
The `kw()` helper function for case-insensitive keyword matching is not used consistently. Some keywords are defined using `kw()`, while others use a `choice()` of all possible case variations (e.g., `choice('IsPreview', 'ispreview', 'ISPREVIEW')`).

**Resolution**:
All keywords should be defined using the `kw()` function to ensure consistency and improve readability. This will make the grammar more robust and easier to maintain.

## 7. Consolidation of `About` properties

**Observation**:
The properties `about_title_property` and `about_text_property` are defined, and comments indicate that `page_about_text_property` and `page_about_title_property` have been consolidated into them. However, there are still separate `page_about_text_ml_property` and `page_about_title_ml_property` rules.

**Resolution**:
These ML properties should be consolidated into more generic `about_text_ml_property` and `about_title_ml_property` rules if they are used in the same way across different object types. This will reduce redundancy and simplify the grammar.

## 8. Lack of a centralized `_boolean_value` rule

**Observation**:
Many properties that accept a boolean value define the choice of `true` or `false` inline.

**Resolution**:
A centralized `_boolean_value` rule should be created to make the grammar more consistent and easier to maintain. This rule would be defined as:
```javascript
_boolean_value: $ => choice(kw('true'), kw('false')),
```
This would replace the current `$.boolean` token and be used in all boolean properties.