# Migration Strategy - Phase 2 Results

## Migration Order and Timeline

### Step-by-Step Migration Order

Based on complexity analysis and impact assessment, the migration will proceed in this order:

#### 1. **Field Properties** (HIGHEST PRIORITY - Week 1)
**Target**: Replace 3 field variants with centralized `$._field_properties`
**Complexity**: High (126 duplicate property definitions)
**Impact**: Critical - addresses the MinValue/MaxValue issue that triggered this migration

**Current State**:
- Standard field: `field(Name) { ... }` - 42 properties (lines 2145-2196)
- Field with control: `field(Name)(ControlName) { ... }` - 42 properties (lines 2209-2250) 
- Combined field: `field(ControlId; SourceOrFieldName) { ... }` - 42 properties (lines 2263-2314)

**Target State**: Single `$._field_properties` reference used in all three variants

#### 2. **Page Properties** (HIGH PRIORITY - Week 1-2)
**Target**: Replace `_page_element` property list with `$._page_properties`
**Complexity**: High (67 individual properties listed)
**Impact**: High - frequently modified, high visibility

**Current State**: Lines 1854-1950 contain 67 direct property references
**Target State**: Composed `$._page_properties` group

#### 3. **Table Properties** (MEDIUM PRIORITY - Week 2)
**Target**: Replace table declaration properties with `$._table_properties`
**Complexity**: Medium (stable object type)
**Impact**: Medium - foundation objects, stability important

#### 4. **Codeunit Properties** (MEDIUM PRIORITY - Week 2)
**Target**: Replace codeunit property lists with `$._codeunit_properties`
**Complexity**: Medium (fewer properties than pages)
**Impact**: Medium - business logic container

#### 5. **Report Properties** (LOW PRIORITY - Week 3)
**Target**: Replace report property lists with `$._report_properties`
**Complexity**: Low (specialized, less frequently modified)
**Impact**: Low - specific use cases

#### 6. **Other Object Types** (LOW PRIORITY - Week 3)
**Target**: Enum, Interface, XMLPort properties
**Complexity**: Low (fewer properties, stable)
**Impact**: Low - specialized objects

## Backwards Compatibility Strategy

### Zero-Disruption Approach
The migration uses **additive changes only** - no existing functionality is removed until the new system is fully validated.

#### Phase 1: Add Centralized Categories
1. **Add new property categories** to grammar.js (bottom of file)
2. **Keep existing property lists** unchanged 
3. **No behavioral changes** - existing tests continue to pass

#### Phase 2: Parallel Implementation
1. **Create alternative rules** using centralized properties
2. **Maintain both old and new patterns** simultaneously
3. **Test new patterns** against existing test corpus

#### Phase 3: Gradual Replacement
1. **Replace one object type at a time**
2. **Validate each replacement** with full test suite
3. **Rollback capability** maintained at each step

#### Phase 4: Cleanup
1. **Remove old property lists** only after full validation
2. **Clean up redundant code**
3. **Update documentation**

### Compatibility Validation
- **All 187 existing tests** must continue passing
- **No changes to parse tree structure** for existing AL code
- **Performance baseline maintained** (4,335 bytes/ms average)

## Rollback Strategy

### Git-Based Rollback Points
Each migration step will be a separate commit with clear rollback instructions:

```bash
# Rollback commands for each phase
git reset --hard <commit-before-field-properties>    # Rollback field migration
git reset --hard <commit-before-page-properties>     # Rollback page migration  
git reset --hard <commit-before-table-properties>    # Rollback table migration
```

### Validation Checkpoints
Before each migration step:
1. **Create git tag**: `git tag pre-migration-step-X`
2. **Run full test suite**: `tree-sitter test`
3. **Performance benchmark**: `tree-sitter test --stat all`
4. **Real file parsing**: `./parse-al.sh` if available

After each migration step:
1. **Run full test suite**: Must maintain 100% pass rate
2. **Compare performance**: Must not degrade > 10%
3. **Spot check parse trees**: Validate structure unchanged

### Emergency Rollback Triggers
Immediate rollback if:
- **Test success rate drops** below 100%
- **Performance degrades** > 15%
- **Parse tree structure changes** unexpectedly
- **Grammar conflicts** introduced

## Migration Templates

### Template 1: Property Category Definition

```javascript
// Add to grammar.js after existing property definitions

// =============================================================================
// CENTRALIZED PROPERTY CATEGORIES
// =============================================================================

// Universal properties (work in most/all contexts)
_universal_properties: $ => choice(
  $.caption_property,
  $.caption_ml_property, 
  $.description_property,
  $.application_area_property,
  $.tool_tip_property,
  $.tool_tip_ml_property,
  $.obsolete_reason_property,
  $.obsolete_state_property,
  $.obsolete_tag_property,
  $.usage_category_property,
),

// Display/UI control properties
_display_properties: $ => choice(
  $.visible_property,
  $.enabled_property,
  $.editable_property,
  $.style_property,
  $.style_expr_property,
  $.width_property,
  $.row_span_property,
  $.column_span_property,
  $.importance_property,
  $.show_caption_property,
  $.show_mandatory_property,
  $.multi_line_property,
  $.hide_value_property,
),

// Data validation properties  
_validation_properties: $ => choice(
  $.min_value_property,
  $.max_value_property,
  $.not_blank_property,
  $.numeric_property,
  $.decimal_places_property,
  $.blank_zero_property,
  $.blank_numbers_property,
  $.unique_property,
  $.values_allowed_property,
  $.validate_table_relation_property,
),

// Data source/relationship properties
_data_properties: $ => choice(
  $.source_expr_property,
  $.table_relation_property,
  $.calc_fields_property,
  $.calc_formula_property,
  $.lookup_property,
  $.auto_format_expression_property,
  $.auto_format_type_property,
  $.auto_increment_property,
  $.field_class_property,
  $.init_value_property,
),

// Navigation/interaction properties
_navigation_properties: $ => choice(
  $.lookup_pageid_property,
  $.drilldown_pageid_property,
  $.navigation_page_id_property,
  $.run_object_property,
  $.run_page_link_property,
  $.run_page_view_property,
  $.card_page_id_property,
),

// Access control properties
_access_properties: $ => choice(
  $.access_property,
  $.permissions_property,
  $.inherent_permissions_property,
  $.inherent_entitlements_property,
  $.access_by_permission_property,
  $.test_permissions_property,
),

// Object-specific properties (context-dependent)
_object_specific_properties: $ => choice(
  // Page-specific
  $.page_type_property,
  $.source_table_property,
  
  // Codeunit-specific
  $.table_no_property,
  $.single_instance_property,
  $.subtype_property,
  $.event_subscriber_instance_property,
  
  // Table-specific
  $.table_type_property,
  $.data_per_company_property,
  $.replicate_data_property,
  
  // Report-specific
  $.processing_only_property,
  $.use_request_page_property,
),

// Composed property groups for different contexts
_field_properties: $ => choice(
  $._universal_properties,
  $._display_properties,
  $._validation_properties,
  $._data_properties,
  $._navigation_properties,
  $.field_trigger_declaration,
  // Field-specific additions
  $.assist_edit_property,
  $.quick_entry_property,
  $.caption_class_property,
  $.option_caption_property,
  $.sign_displacement_property,
  $.title_property,
  $.extended_datatype_property,
  $.page_about_title_property,
  $.page_about_text_property,
  $.page_about_title_ml_property,
  $.page_about_text_ml_property,
),
```

### Template 2: Field Section Migration

```javascript
// BEFORE (current):
field_section: $ => choice(
  // Standard field
  seq(
    /[fF][iI][eE][lL][dD]/,
    '(',
    field('name', choice($.identifier, $._quoted_identifier)),
    ')',
    '{',
    repeat(choice(
      $.caption_property,
      $.caption_class_property,
      // ... 40 more properties ...
    )),
    '}'
  ),
  // ... 2 more variants with same property lists
),

// AFTER (centralized):
field_section: $ => choice(
  // Standard field
  seq(
    /[fF][iI][eE][lL][dD]/,
    '(',
    field('name', choice($.identifier, $._quoted_identifier)),
    ')',
    '{',
    repeat($._field_properties),
    '}'
  ),
  // Field with control name
  seq(
    /[fF][iI][eE][lL][dD]/,
    '(',
    field('name', choice($.identifier, $._quoted_identifier)),
    ')',
    '(',
    field('control_name', choice($.identifier, $._quoted_identifier)),
    ')',
    '{',
    repeat($._field_properties),
    '}'
  ),
  // Combined field
  seq(
    /[fF][iI][eE][lL][dD]/,
    '(',
    field('control_id', choice($.string_literal, $._quoted_identifier, $.integer, $.identifier)),
    ';',
    field('source_or_field_name', $._expression),
    ')',
    '{',
    repeat($._field_properties),
    '}'
  ),
),
```

### Template 3: Validation Checkpoint

```bash
#!/bin/bash
# Migration validation script

echo "=== Pre-Migration Validation ==="
echo "1. Running full test suite..."
tree-sitter test
if [ $? -ne 0 ]; then
    echo "❌ Tests failing before migration - abort!"
    exit 1
fi

echo "2. Performance baseline..."
tree-sitter test --stat all | grep "average speed" > pre_migration_performance.txt

echo "3. Creating rollback point..."
git tag "pre-migration-$(date +%Y%m%d-%H%M%S)"

echo "✅ Pre-migration validation complete"

# Apply migration changes here...

echo "=== Post-Migration Validation ==="
echo "1. Re-running full test suite..."
tree-sitter test
if [ $? -ne 0 ]; then
    echo "❌ Tests failing after migration!"
    echo "Consider rollback: git reset --hard <previous-tag>"
    exit 1
fi

echo "2. Performance comparison..."
tree-sitter test --stat all | grep "average speed" > post_migration_performance.txt
echo "Performance comparison:"
echo "Before: $(cat pre_migration_performance.txt)"
echo "After:  $(cat post_migration_performance.txt)"

echo "✅ Post-migration validation complete"
```

## Risk Mitigation

### High-Risk Areas
1. **Field sections**: Most complex migration with 3 variants
   - **Mitigation**: Test each variant separately
   - **Validation**: Comprehensive field property test corpus

2. **Test corpus dependency**: 187 tests rely on current structure
   - **Mitigation**: Parallel implementation, no removal until validated
   - **Validation**: 100% test pass rate maintained

3. **Parse tree compatibility**: Downstream tools may depend on structure
   - **Mitigation**: No changes to parse tree node names or structure
   - **Validation**: Compare parse trees before/after

### Medium-Risk Areas
1. **Grammar conflicts**: New categories may conflict with existing rules
   - **Mitigation**: Careful precedence management
   - **Validation**: Grammar generation without conflicts

2. **Performance impact**: Centralized properties may affect parse speed
   - **Mitigation**: Benchmark at each step
   - **Validation**: <10% performance degradation acceptable

## Success Criteria

### Functional Requirements
- [ ] All 187 existing tests continue passing
- [ ] Grammar generates without conflicts
- [ ] Property choice lists reduced from 46 to ~7 categories
- [ ] New properties can be added in one location

### Performance Requirements  
- [ ] Parse speed maintained within 10% of baseline (4,335 bytes/ms)
- [ ] Grammar generation time not significantly increased
- [ ] Memory usage not significantly increased

### Quality Requirements
- [ ] Code duplication eliminated (DRY principle satisfied)
- [ ] Grammar more maintainable and semantic
- [ ] Clear property inheritance model
- [ ] Comprehensive documentation updated

---

**Next Steps**: Begin Phase 3 implementation using these migration templates and validation procedures.