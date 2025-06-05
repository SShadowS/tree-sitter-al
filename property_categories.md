# Property Categorization - Proposed Architecture

## Overview

This document defines the semantic property categories for the centralized grammar architecture. Categories are based on AL language semantics and usage patterns, not object context.

## Centralized Property Categories

### 1. Universal Properties (`_universal_properties`)
Properties that work in most/all contexts and provide basic metadata:

```javascript
_universal_properties: $ => choice(
  $.caption_property,              // Display label
  $.caption_ml_property,           // Multi-language display label  
  $.description_property,          // Descriptive text
  $.application_area_property,     // Feature area filtering
  $.tool_tip_property,            // Help text
  $.tool_tip_ml_property,         // Multi-language help text
  $.obsolete_reason_property,     // Deprecation reason
  $.obsolete_state_property,      // Deprecation status
  $.obsolete_tag_property,        // Deprecation version tag
  $.usage_category_property,      // Usage classification
)
```

**Usage**: ~40 instances across all object types
**Rationale**: These properties provide universal metadata applicable to most AL elements regardless of context.

### 2. Display Properties (`_display_properties`)
Properties controlling UI visibility, interaction, and presentation:

```javascript
_display_properties: $ => choice(
  $.visible_property,             // Element visibility
  $.enabled_property,             // Interaction enabled state
  $.editable_property,           // Edit permission
  $.style_property,              // Visual styling
  $.style_expr_property,         // Dynamic styling
  $.width_property,              // Element width
  $.row_span_property,           // Grid row spanning
  $.column_span_property,        // Grid column spanning  
  $.importance_property,         // Priority/emphasis level
  $.show_caption_property,       // Caption visibility
  $.show_mandatory_property,     // Mandatory field indication
  $.multi_line_property,         // Multi-line text support
  $.hide_value_property,         // Value masking (e.g., passwords)
)
```

**Usage**: ~45 instances in pages, fields, and UI elements
**Rationale**: These properties control how elements appear and behave in the user interface.

### 3. Validation Properties (`_validation_properties`)
Properties enforcing data integrity and input constraints:

```javascript
_validation_properties: $ => choice(
  $.min_value_property,          // Minimum allowed value
  $.max_value_property,          // Maximum allowed value
  $.not_blank_property,          // Required field validation
  $.numeric_property,            // Numeric input only
  $.decimal_places_property,     // Decimal precision
  $.blank_zero_property,         // Display blank for zero
  $.blank_numbers_property,      // Blank number display rules
  $.unique_property,             // Uniqueness constraint
  $.values_allowed_property,     // Enumerated valid values
  $.validate_table_relation_property, // FK validation
)
```

**Usage**: ~20 instances in table fields and page fields
**Rationale**: These properties ensure data quality and enforce business rules.

### 4. Data Source Properties (`_data_properties`)
Properties defining data sources, relationships, and calculations:

```javascript
_data_properties: $ => choice(
  $.source_expr_property,        // Data source expression
  $.table_relation_property,     // Foreign key relationship
  $.calc_fields_property,        // Calculated field definition
  $.calc_formula_property,       // Calculation formula
  $.lookup_property,             // Lookup behavior
  $.auto_format_expression_property, // Format expression
  $.auto_format_type_property,   // Format type
  $.auto_increment_property,     // Auto-increment behavior
  $.field_class_property,        // Field classification
  $.init_value_property,         // Default value
)
```

**Usage**: ~25 instances in data-bound elements  
**Rationale**: These properties define how data is sourced, calculated, and formatted.

### 5. Navigation Properties (`_navigation_properties`)
Properties enabling navigation and interaction between objects:

```javascript
_navigation_properties: $ => choice(
  $.lookup_pageid_property,      // Lookup page reference
  $.drilldown_pageid_property,   // Drill-down page reference
  $.navigation_page_id_property, // Navigation target
  $.run_object_property,         // Action target object
  $.run_page_link_property,      // Page link parameters
  $.run_page_view_property,      // Page view settings
  $.card_page_id_property,       // Associated card page
)
```

**Usage**: ~15 instances in pages and actions
**Rationale**: These properties create navigation paths and object relationships.

### 6. Access Control Properties (`_access_properties`)
Properties controlling permissions and security:

```javascript
_access_properties: $ => choice(
  $.access_property,             // Access level
  $.permissions_property,        // Permission definitions
  $.inherent_permissions_property, // Built-in permissions
  $.inherent_entitlements_property, // Built-in entitlements
  $.access_by_permission_property, // Conditional access
  $.test_permissions_property,   // Test environment permissions
)
```

**Usage**: ~12 instances in various objects
**Rationale**: These properties manage security and access control.

### 7. Object-Specific Properties (`_object_specific_properties`)
Properties that are unique to specific object types:

```javascript
_object_specific_properties: $ => choice(
  // Page-specific
  $.page_type_property,          // Page type (List, Card, etc.)
  $.source_table_property,       // Source table reference
  $.card_page_id_property,       // Associated card page
  
  // Codeunit-specific  
  $.table_no_property,           // Associated table
  $.single_instance_property,    // Singleton pattern
  $.subtype_property,           // Codeunit subtype
  $.event_subscriber_instance_property, // Event handling
  
  // Table-specific
  $.table_type_property,         // Table type (Normal, Temporary, etc.)
  $.data_per_company_property,   // Multi-tenancy support
  $.replicate_data_property,     // Replication settings
  
  // Report-specific
  $.processing_only_property,    // Processing-only report
  $.use_request_page_property,   // Request page usage
)
```

**Usage**: Varies by object type
**Rationale**: These properties only make sense in specific contexts and cannot be universally applied.

## Composed Property Groups

### Field Properties (`_field_properties`)
Combination for all field contexts:

```javascript
_field_properties: $ => choice(
  $._universal_properties,
  $._display_properties, 
  $._validation_properties,
  $._data_properties,
  $._navigation_properties,
  $.field_trigger_declaration,   // Field-specific triggers
)
```

### Page Properties (`_page_properties`)
Combination for page-level properties:

```javascript
_page_properties: $ => choice(
  $._universal_properties,
  $._display_properties,
  $._access_properties,
  $._navigation_properties,
  $._object_specific_properties,
  // Page-specific additions
  $.data_caption_expression_property,
  $.instructional_text_property,
  $.save_values_property,
  $.refresh_on_activate_property,
)
```

### Table Properties (`_table_properties`)
Combination for table-level properties:

```javascript
_table_properties: $ => choice(
  $._universal_properties,
  $._access_properties,
  $._object_specific_properties,
  // Table-specific additions
  $.data_caption_fields_property,
  $.extensible_property,
  $.compression_type_property,
  $.column_store_index_property,
)
```

## Benefits of This Architecture

### 1. DRY Principle Compliance
- Properties defined once in semantic categories
- Reused across appropriate contexts
- Single point of maintenance

### 2. Semantic Organization
- Properties grouped by purpose, not location
- Easier to understand relationships
- Better developer experience

### 3. Extensibility  
- New properties added to appropriate category
- Automatically available in all relevant contexts
- Clear guidance on where new properties belong

### 4. Type Safety
- Prevents inappropriate property/context combinations
- Category composition controls availability
- Compile-time validation of property usage

### 5. Maintainability
- Centralized property definitions
- Consistent behavior across contexts
- Easier to track property usage

## Migration Impact

### Reduced Complexity
- From 46 scattered choice lists to 7 semantic categories
- From 216 duplicate definitions to ~120 centralized definitions
- Clearer property inheritance model

### Improved Development Workflow
- Add new property once to appropriate category
- Automatic availability in composed groups
- No need to hunt for all usage locations

---

**Next Steps**: Use these categories as the foundation for Phase 3 implementation.