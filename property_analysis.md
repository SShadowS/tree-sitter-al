# Property Analysis - Phase 1 Results

## Executive Summary

The current grammar contains **46 different property choice lists** scattered throughout the codebase, confirming the DRY principle violation. This analysis identifies **216 unique property definitions** with extensive duplication across contexts.

## Key Findings

### 1. Property Distribution
- **Total unique properties**: 216 
- **Property choice lists**: 46 instances of `repeat(choice(...))` patterns
- **Most duplicated properties**: caption_property, application_area_property, tool_tip_property appear in 20+ contexts each
- **Test coverage**: 100% success rate (187/187 tests passing)

### 2. Current Duplication Hotspots

Based on the property usage analysis, the most duplicated properties are:

1. **Caption-related properties** (39 instances):
   - `caption_property` - Universal UI labeling
   - `caption_ml_property` - Multi-language captions  
   - `caption_class_property` - Dynamic caption generation

2. **Tooltip properties** (35 instances):
   - `tool_tip_property` - Help text
   - `tool_tip_ml_property` - Multi-language help text

3. **Visibility/Control properties** (45+ instances):
   - `application_area_property` - Feature area filtering
   - `visible_property` - Element visibility
   - `enabled_property` - Element interaction state
   - `editable_property` - Data modification permission

4. **Data validation properties** (20+ instances):
   - `min_value_property` - Minimum allowed values
   - `max_value_property` - Maximum allowed values  
   - `decimal_places_property` - Numeric precision
   - `table_relation_property` - Foreign key relationships

## 3. Context Analysis

### Field Section Properties
Field sections show the highest property complexity with three variants:
- Standard field: `field(Name) { ... }` - 42 properties
- Field with control: `field(Name)(ControlName) { ... }` - 42 properties  
- Combined field: `field(ControlId; SourceOrFieldName) { ... }` - 42 properties

**High duplication**: Each field variant repeats the same 42 property definitions.

### Page Element Properties  
Page elements contain 67 different properties directly listed in `_page_element` choice, including:
- Object-specific: `page_type_property`, `source_table_property`
- Universal: `caption_property`, `application_area_property`, `description_property`
- Display: `visible_property`, `enabled_property`, `editable_property`

### Table Declaration Properties
Table properties show semantic groupings:
- Data management: `data_per_company_property`, `replicate_data_property`
- Performance: `compression_type_property`, `column_store_index_property`
- Access control: `permissions_property`, `inherent_permissions_property`

## 4. Property Categories (Preliminary)

Based on usage patterns and AL language semantics, properties naturally group into:

### Universal Properties (used across most contexts)
- Caption and descriptions: `caption_property`, `description_property`, `caption_ml_property`
- Help text: `tool_tip_property`, `tool_tip_ml_property`
- Feature areas: `application_area_property`, `usage_category_property`
- Lifecycle: `obsolete_state_property`, `obsolete_reason_property`, `obsolete_tag_property`

### Display/UI Properties (UI elements)
- Visibility: `visible_property`, `enabled_property`, `editable_property`
- Layout: `width_property`, `row_span_property`, `column_span_property`
- Styling: `style_property`, `style_expr_property`, `importance_property`

### Data Validation Properties (data fields)
- Constraints: `min_value_property`, `max_value_property`, `not_blank_property`
- Formatting: `decimal_places_property`, `auto_format_type_property`, `blank_zero_property`
- Data integrity: `numeric_property`, `unique_property`

### Data Source Properties (data-bound elements)
- Sources: `source_expr_property`, `table_relation_property`, `calc_formula_property`
- Relationships: `lookup_property`, `calc_fields_property`
- Auto-generation: `auto_format_expression_property`, `auto_increment_property`

### Navigation Properties (interactive elements)
- Pages: `lookup_pageid_property`, `drilldown_pageid_property`, `navigation_page_id_property`
- Actions: `run_object_property`, `run_page_link_property`

### Object-Specific Properties (context-dependent)
- Page-only: `page_type_property`, `source_table_property`, `card_page_id_property`
- Codeunit-only: `table_no_property`, `single_instance_property`, `subtype_property`
- Table-only: `table_type_property`, `data_per_company_property`

## 5. Performance Baseline

Current test suite performance (baseline for comparison):
- **Total tests**: 187
- **Success rate**: 100% (187/187 passing)
- **Average parse speed**: 4,335 bytes/ms
- **Slow tests** (< 1000 bytes/ms): 4 tests identified

## 6. Risk Assessment

### High-Impact Areas
1. **Field sections**: Most complex with 3 variants × 42 properties = 126 duplicate definitions
2. **Page elements**: 67 properties, high risk of missing additions
3. **Table fields**: Critical for data validation properties

### Medium-Impact Areas  
1. **Codeunit properties**: Lower complexity but important for business logic
2. **Report properties**: Specialized but less frequently modified

## 7. Migration Priority

Based on complexity and maintenance burden:

1. **Phase 3.2 - Field Properties** (HIGHEST PRIORITY)
   - Affects 3 field variants with 42 properties each
   - Highest duplication ratio
   - Critical for MinValue/MaxValue issue that triggered this migration

2. **Phase 3.3 - Page Properties** 
   - 67 properties, frequent modifications
   - High visibility to end users

3. **Phase 3.4 - Table Properties**
   - Foundation objects, stability important
   - Clear semantic groupings

4. **Phase 3.5 - Other Objects**
   - Lower complexity objects
   - Easier to validate

## Recommendations

1. **Start with field properties** to address the immediate DRY violation
2. **Create semantic property categories** rather than context-based groupings
3. **Maintain 100% test coverage** throughout migration
4. **Use incremental approach** to minimize risk
5. **Validate against real AL files** after each phase

---

**Next Steps**: Proceed to Phase 2 (Migration Strategy) using this analysis as foundation.