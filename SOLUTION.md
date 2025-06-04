# AL Grammar Property Placement Solution

## Overview

This document outlines the changes needed to fix property placement issues in the tree-sitter-al grammar.js file. While all 32 AL properties have been successfully defined, many are not properly accessible in their correct contexts according to the AL documentation.

## Required Changes

### 1. Update `_table_element` Rule

The most critical fix is to update the `_table_element` rule to include all table-applicable properties:

```javascript
_table_element: $ => prec(1, choice(
  $.fields,  // Fields section should be primary
  
  // Existing triggers
  $.oninsert_trigger,
  $.onmodify_trigger,
  $.ondelete_trigger,
  $.onrename_trigger,
  $.onvalidate_trigger,
  $.onaftergetrecord_trigger,
  $.onafterinsertevent_trigger,
  $.onaftermodifyevent_trigger,
  $.onafterdeleteevent_trigger,
  $.onbeforeinsertevent_trigger,
  $.onbeforemodifyevent_trigger,
  $.onbeforedeleteevent_trigger,
  
  // Other existing elements
  $.keys,
  $.procedure,
  $.var_section,
  $.fieldgroups_section,
  
  // Existing properties
  $.caption_property,
  $.data_classification_property,
  $.permissions_property,
  $.drilldown_pageid_property,
  $.lookup_pageid_property,
  $.table_type_property,
  $.access_property,
  
  // Existing table-related properties
  $.moved_from_property,
  $.moved_to_property,
  $.linked_in_transaction_property,
  $.linked_object_property,
  
  // Missing HIGH PRIORITY properties
  $.data_caption_fields_property,    // HIGH PRIORITY
  $.extensible_property,             // HIGH PRIORITY
  $.data_per_company_property,       // HIGH PRIORITY
  $.replicate_data_property,         // HIGH PRIORITY
  $.column_store_index_property,     // HIGH PRIORITY
  $.compression_type_property,       // HIGH PRIORITY
  $.inherent_permissions_property,   // HIGH PRIORITY
  $.inherent_entitlements_property,  // HIGH PRIORITY
  
  // Missing MEDIUM/LOW PRIORITY properties
  $.external_schema_property,        // MEDIUM PRIORITY
  $.paste_is_valid_property,         // MEDIUM PRIORITY 
  $.description_property,            // MEDIUM PRIORITY
  $.obsolete_reason_property,        // MEDIUM PRIORITY
  $.obsolete_state_property,         // MEDIUM PRIORITY
  $.obsolete_tag_property,           // MEDIUM PRIORITY
  $.caption_ml_property,             // MEDIUM PRIORITY
  $.external_name_property           // MEDIUM PRIORITY
)),
```

### 2. Verify All Field-Level Properties 

Ensure all field-applicable properties are included in the `field_declaration` rule:

```javascript
field_declaration: $ => seq(
  'field',
  '(',
  field('id', $.integer),
  token(';'),
  field('name', choice(
    $._quoted_identifier,
    $.identifier
  )),
  token(';'),
  field('type', $.type_specification),
  ')',
  optional(seq(
    '{',
    repeat(choice(
      // Existing field properties
      $.caption_property,
      $.data_classification_property,
      $.decimal_places_property,
      $.field_trigger_declaration,
      $.access_by_permission_property,
      $.allow_in_customizations_property,
      $.auto_format_expression_property,
      $.auto_format_type_property,
      $.auto_increment_property,
      $.blank_numbers_property,
      $.table_relation_property,
      $.field_class_property,
      $.calc_formula_property,
      $.blank_zero_property,
      $.editable_property,
      $.option_members_property,
      $.option_caption_property,
      $.closing_dates_property,
      $.char_allowed_property,
      $.compressed_property,
      $.date_formula_property,
      $.description_property,
      $.external_access_property,
      $.external_name_property,
      $.external_type_property,
      $.init_value_property,
      $.max_value_property,
      $.min_value_property,
      $.not_blank_property,
      $.numeric_property,
      $.obsolete_reason_property,
      $.obsolete_state_property,
      $.obsolete_tag_property,
      $.option_ordinal_values_property,
      $.paste_is_valid_property,
      $.sign_displacement_property,
      $.sql_data_type_property,
      $.sql_timestamp_property,
      $.test_table_relation_property,
      $.tool_tip_property,
      $.unique_property,
      $.validate_table_relation_property,
      $.values_allowed_property,
      $.extended_datatype_property,
      
      // Multi-language properties
      $.caption_ml_property,
      $.option_caption_ml_property,
      $.tool_tip_ml_property
    )),
    '}'
  ))
)
```

### 3. Update Page Elements Context

Ensure page-specific properties are correctly included in the `_page_element` rule:

```javascript
_page_element: $ => choice(
  $.property_list,
  $.layout_section,
  $.actions_section,
  $.procedure,
  $.var_section,
  $.trigger_declaration,
  
  // Direct properties
  $.description_property,
  $.caption_property,
  $.scope_property,
  $.promoted_property,
  $.promoted_category_property,
  $.promoted_only_property,
  $.promoted_is_big_property,
  $.run_object_property,
  $.run_page_link_property,
  $.run_page_view_property,
  $.image_property,
  $.tool_tip_property,
  
  // Missing page properties
  $.data_caption_fields_property,
  $.extensible_property,
  $.inherent_permissions_property,
  $.inherent_entitlements_property,
  $.caption_ml_property,
  $.source_table_property,
  $.usage_category_property,
  $.permissions_property
)
```

### 4. Update XMLPort Element Context

Ensure XMLPort-specific properties are correctly included in the `_xmlport_element` rule:

```javascript
_xmlport_element: $ => choice(
  $.property_list,
  $.xmlport_schema_element,
  $.var_section,
  $.procedure,
  $.trigger_declaration,
  
  // Missing XMLPort properties
  $.inherent_permissions_property,
  $.inherent_entitlements_property,
  $.caption_property,
  $.caption_ml_property,
  $.description_property
)
```

## Testing Strategy

After implementing these changes, create test files to validate that properties parse correctly in their contexts:

1. **Table Property Tests**:
   - Create test files with various table properties
   - Verify all HIGH and MEDIUM PRIORITY properties parse correctly

2. **Field Property Tests**:
   - Create test files with field properties 
   - Ensure multi-language properties work correctly

3. **Page Property Tests**:
   - Test page-specific properties in context

## Implementation Notes

- All properties are already defined correctly in the grammar.js file
- The issue is purely with placement in context rules
- No changes are needed to property definitions, only to context rules
- After implementing these changes, the grammar should fully support all 32 documented AL properties in their correct contexts

## Future Work

- Consider implementing additional properties from the AL documentation
- Improve test coverage for all property types
