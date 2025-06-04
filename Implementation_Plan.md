# AL Grammar Property Placement Implementation Plan

## Summary

All 32 AL properties have been successfully defined in our grammar.js file, but many aren't correctly accessible in their appropriate contexts according to the AL documentation. This implementation plan outlines the specific changes needed to correct these placement issues.

## Current Status

- All property definitions exist (32/32 properties implemented)
- Property placement issues identified in multiple contexts
- Test files created for validating property placement

## Required Changes

### 1. Update `_table_element` Rule

The most critical issue is that many table-applicable properties are missing from the `_table_element` rule. The patch file `table_element_fix.patch` shows the exact changes needed to fix this issue.

```javascript
_table_element: $ => prec(1, choice(
  $.fields,  // Fields section should be primary
  
  // Existing triggers and elements (unchanged)...
  
  // Add missing HIGH PRIORITY properties
  $.data_caption_fields_property,
  $.extensible_property,
  $.data_per_company_property,
  $.replicate_data_property,
  $.column_store_index_property,
  $.compression_type_property,
  $.inherent_permissions_property,
  $.inherent_entitlements_property,
  
  // Add missing MEDIUM/LOW PRIORITY properties
  $.external_schema_property,
  $.paste_is_valid_property,
  $.description_property,
  $.obsolete_reason_property,
  $.obsolete_state_property,
  $.obsolete_tag_property,
  $.caption_ml_property,
  $.external_name_property
)),
```

### 2. Update `_page_element` Rule

Ensure page-specific properties are correctly included in the `_page_element` rule:

```javascript
_page_element: $ => choice(
  // Existing elements (unchanged)...
  
  // Missing page properties
  $.data_caption_fields_property,
  $.extensible_property,
  $.inherent_permissions_property,
  $.inherent_entitlements_property,
  $.caption_ml_property,
  $.usage_category_property,
  $.permissions_property
),
```

### 3. Update `_xmlport_element` Rule

Ensure XMLPort-specific properties are correctly included in the `_xmlport_element` rule:

```javascript
_xmlport_element: $ => choice(
  // Existing elements (unchanged)...
  
  // Missing XMLPort properties
  $.inherent_permissions_property,
  $.inherent_entitlements_property,
  $.caption_property,
  $.caption_ml_property,
  $.description_property
),
```

### 4. Verify Field Property Contexts

Field properties appear to be well-implemented in the `field_declaration` rule. The current implementation includes all field-applicable properties from the AL documentation.

## Testing Strategy

The following test files have been created to validate property placement:

1. **`test/corpus/table_properties.txt`**:
   - Tests high-priority table properties
   - Tests medium/low priority table properties
   - Tests field properties within tables

2. **`test/corpus/page_xmlport_properties.txt`**:
   - Tests page properties
   - Tests XMLPort properties

Once the grammar.js file is updated, use these test files to validate that properties parse correctly in their contexts.

## Implementation Steps

1. **Apply Table Element Fix**:
   - Apply the changes from `table_element_fix.patch` to grammar.js
   - This adds all missing table properties to the `_table_element` rule

2. **Update Page Element Context**:
   - Modify the `_page_element` rule to include all missing page properties
   - Follow the pattern in the code snippet provided above

3. **Update XMLPort Element Context**:
   - Modify the `_xmlport_element` rule to include all missing XMLPort properties
   - Follow the pattern in the code snippet provided above

4. **Test Grammar**:
   - Run `tree-sitter test` to validate the changes
   - Verify that test files parse correctly

5. **Review and Finalize**:
   - Check for any remaining property placement issues
   - Ensure all properties are accessible in their correct contexts

## Benefits

After implementing these changes:

1. The grammar will fully support all 32 documented AL properties in their correct contexts
2. IntelliSense and syntax highlighting will work correctly for all properties
3. AL files with these properties will parse without errors
4. The grammar will match the official AL property documentation exactly

## Future Considerations

- Add additional properties that may be missing from the current list
- Implement more comprehensive test coverage for properties
- Consider adding validation for property values where applicable
