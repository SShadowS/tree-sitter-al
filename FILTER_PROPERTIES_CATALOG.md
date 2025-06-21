# Filter Properties Catalog

## Overview
This document catalogs all filter-related properties in the AL grammar and their current patterns.

## Filter Property Patterns

### Pattern 1: Detailed Filter Pattern (FILTER Function Context)
**Usage**: Properties that use FILTER() function calls
**Grammar Rule**: Direct choice of all filter expression types
```javascript
choice(
  $.filter_or_expression,
  $.filter_not_equal_expression, 
  $.filter_equal_expression,
  $.filter_range_expression,
  $.identifier, $._quoted_identifier, $.integer, $.string_literal
)
```

**Properties Using This Pattern:**
1. **filter_expression_function** (line 694-708)
   - Used within FILTER() function calls
   - Supports: range expressions, OR expressions, equal expressions, literals
   - Context: SubPageLink, RunPageLink, DataItemLink properties

2. **run_page_link_value** (line 1305-1315) 
   - Used in RunPageLink, SubPageLink properties
   - Supports: same as filter_expression_function
   - Context: Action and page field properties

### Pattern 2: Generic Filter Pattern (Table View Context)
**Usage**: Properties that accept complex table view expressions
**Grammar Rule**: Uses existing `filter_expression` rule
```javascript
$.filter_expression  // Complex sorting/where combinations
```

**Properties Using This Pattern:**
1. **view_filters_property** (line 2026-2031)
   - Used in page views section
   - Supports: where clauses, sorting clauses, complex expressions
   - Context: Page view definitions

2. **source_table_view_property** (line 789-794)
   - Used in SourceTableView properties
   - Value: `$.source_table_view_value` (combines sorting/where)
   - Context: Page and table objects

3. **data_item_table_view_property** (line 5503-5508)
   - Used in DataItemTableView properties  
   - Value: `$.source_table_view_value`
   - Context: Report dataitem sections

### Pattern 3: Mixed Pattern (Property Value Context)
**Usage**: Properties that accept either simple values OR filter expressions
**Grammar Rule**: Choice combining basic types with filter_expression
```javascript
choice(
  $.identifier, $._quoted_identifier, $.string_literal,
  $.filter_expression
)
```

**Properties Using This Pattern:**
1. **filters_property** (line 5453-5463)
   - Used in query dataitem sections
   - Supports: identifiers, strings, OR complex filter expressions
   - Context: Query object filters

### Pattern 4: Specialized Patterns (Non-Filter Context)
**Properties that contain "filter" but don't use filter expressions:**

1. **request_filter_fields_property** (line 224-229)
   - Pattern: `$._identifier_choice_list`
   - Purpose: List of field names for request page filtering
   - Context: Report request pages

2. **request_filter_heading_property** (line 232-235)
   - Pattern: `$._string_property_template`
   - Purpose: String caption for filter heading
   - Context: Report request pages

3. **request_filter_heading_ml_property** (line 238+)
   - Pattern: ML (multi-language) string template
   - Purpose: Multi-language filter heading
   - Context: Report request pages

4. **show_filter_property** (line 515-518)
   - Pattern: `$._boolean_property_template`
   - Purpose: Boolean to show/hide filter UI
   - Context: Page objects

## Semantic Categories for Unification

### Category A: Simple Filter Values
**Target Rule**: `_simple_filter_value`
**Current Users**: filter_expression_function, run_page_link_value
**Purpose**: Values used within FILTER() function calls

### Category B: Table View Filters  
**Target Rule**: `_table_view_filter` (alias to filter_expression)
**Current Users**: view_filters_property, source_table_view_property, data_item_table_view_property
**Purpose**: Complex table view expressions with sorting/where

### Category C: Property Filter Values
**Target Rule**: `_property_filter_value`
**Current Users**: filters_property
**Purpose**: Properties accepting either simple values or complex filters

### Category D: Non-Filter Properties
**No Changes Needed**: request_filter_fields_property, request_filter_heading_property, show_filter_property
**Purpose**: Properties with "filter" in name but different semantics

## Current Issues

1. **Code Duplication**: Pattern 1 is duplicated in 2 locations with identical structure
2. **Inconsistent Capabilities**: Different properties support different filter expression types
3. **Maintenance Burden**: Adding new filter types requires updating multiple locations
4. **Unclear Semantics**: Similar property names have different value patterns

## Proposed Unification Benefits

1. **Eliminate Duplication**: Single definition for each semantic pattern
2. **Consistent Behavior**: All FILTER() contexts support same expressions
3. **Easier Maintenance**: New filter types added once, available everywhere appropriate
4. **Clearer Architecture**: Semantic naming indicates intended usage context