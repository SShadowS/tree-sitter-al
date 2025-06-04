# WHERE Clause Unification Plan

This document outlines the plan for merging the different WHERE clause implementations in the tree-sitter-al grammar.

## Current State Analysis

Currently, the grammar contains multiple implementations of WHERE clauses used in different contexts:

### 1. Standard WHERE Clause (SourceTableView/TableRelation)
```javascript
where_clause: $ => seq(
  /[wW][hH][eE][rR][eE]/,
  '(',
  field('filter', $.filter_expression_list),
  ')'
),

filter_expression_list: $ => seq(
  $.filter_expression,
  repeat(seq(
    optional(/[aA][nN][dD]/),
    $.filter_expression
  ))
),

filter_expression: $ => seq(
  field('field', $.field_reference),
  field('operator', $.filter_operator),
  field('value', $.filter_value)
),
```

Used in contexts like:
- SourceTableView properties
- Table relation expressions

### 2. Calculation Formula WHERE Clause
```javascript
calc_where_clause: $ => seq(
  choice('where', 'WHERE', 'Where'),
  '(',
  field('conditions', $.calc_where_conditions),
  ')'
),

calc_where_conditions: $ => seq(
  $.calc_where_condition,
  repeat(seq(',', $.calc_where_condition))
),

calc_where_condition: $ => prec(15, seq(
  field('field', $.field_ref),
  '=',
  choice(
    seq(
      choice('field', 'FIELD', 'Field'),
      '(',
      field('target_field', $.field_ref),
      ')'
    ),
    seq(
      choice('const', 'CONST', 'Const'),
      '(',
      optional(field('value', choice($.string_literal, $.field_ref))),
      ')'
    )
  )
)),
```

Used in contexts like:
- Count formulas
- Sum formulas
- Average formulas
- Min/Max formulas

### 3. Lookup Formula WHERE Conditions
```javascript
lookup_where_conditions: $ => seq(
  $.lookup_where_condition,
  repeat(seq(',', $.lookup_where_condition))
),

lookup_where_condition: $ => seq(
  field('field', $.field_ref),
  '=',
  choice(
    seq(
      choice('field', 'FIELD', 'Field'),
      '(',
      field('value', $.field_ref),
      ')'
    ),
    seq(
      field('keyword', alias(choice('const', 'CONST', 'Const'), $.const)),
      '(',
      optional(field('value', $.string_literal)),
      ')'
    )
  )
),
```

Used in contexts like:
- Lookup formulas

## Key Differences

1. **Syntax Patterns**:
   - Standard WHERE: `field op value` patterns with various operators (`=`, `<>`, `>=`, etc.)
   - Calc WHERE: Only `=` operator with `FIELD(...)` or `CONST(...)` patterns
   - Lookup WHERE: Similar to Calc WHERE but with slightly different structure

2. **Field References**:
   - Different field reference patterns and handling

3. **Context-Specific Formatting**:
   - Different separator patterns (AND vs. comma)
   - Different naming conventions in the AST

## Unification Goal

Create a single, flexible WHERE clause implementation that:
1. Handles all current use cases
2. Maintains backward compatibility
3. Simplifies the grammar
4. Makes future extensions easier

## Implementation Plan

### Phase 1: Create Unified WHERE Condition Types

1. **Create a unified `where_condition` rule** that encompasses all current condition types:

```javascript
where_condition: $ => choice(
  // Standard filter expression (field = value, field <> value, etc.)
  $.filter_expression_condition,
  
  // FIELD(...) reference condition
  $.field_reference_condition,
  
  // CONST(...) value condition
  $.const_value_condition
),

// Existing filter expression pattern
filter_expression_condition: $ => seq(
  field('field', $.field_ref),
  field('operator', $.filter_operator),
  field('value', $.filter_value)
),

// FIELD(...) reference pattern
field_reference_condition: $ => prec(15, seq(
  field('field', $.field_ref),
  '=',
  choice('field', 'FIELD', 'Field'),
  '(',
  field('reference', $.field_ref),
  ')'
)),

// CONST(...) value pattern
const_value_condition: $ => prec(15, seq(
  field('field', $.field_ref),
  '=',
  choice('const', 'CONST', 'Const'),
  '(',
  optional(field('value', choice($.string_literal, $.field_ref, $.integer, $.boolean))),
  ')'
)),
```

### Phase 2: Create Unified WHERE Conditions List

1. **Create a unified `where_conditions` rule** that can handle both comma and AND-separated conditions:

```javascript
where_conditions: $ => choice(
  // Comma-separated conditions (calc/lookup style)
  seq(
    $.where_condition,
    repeat(seq(',', $.where_condition))
  ),
  
  // AND-separated conditions (filter style)
  seq(
    $.where_condition,
    repeat(seq(
      optional(/[aA][nN][dD]/),
      $.where_condition
    ))
  )
),
```

### Phase 3: Create Unified WHERE Clause

1. **Update the `where_clause` rule** to use the unified conditions:

```javascript
where_clause: $ => seq(
  choice(/[wW][hH][eE][rR][eE]/, 'where', 'WHERE', 'Where'),
  '(',
  field('conditions', $.where_conditions),
  ')'
),
```

### Phase 4: Update Usage Points

1. **Update SourceTableView**:
```javascript
source_table_view_value: $ => choice(
  // At least sorting clause present
  seq(
    $.sorting_clause,
    optional($.order_clause),
    optional($.where_clause) // Updated to use unified where_clause
  ),
  // ...other patterns
),
```

2. **Update Calculation Formulas**:
```javascript
count_formula: $ => seq(
  choice('count', 'COUNT', 'Count'),
  '(',
  field('table', alias($._table_reference, $.table_reference)),
  optional($.where_clause), // Updated from calc_where_clause
  ')'
),

sum_formula: $ => seq(
  choice('sum', 'SUM', 'Sum'),
  '(',
  field('target', $.calc_field_ref),
  optional($.where_clause), // Updated from calc_where_clause
  ')'
),

// Similar updates for average_formula, min_formula, max_formula
```

3. **Update Lookup Formula**:
```javascript
lookup_formula: $ => seq(
  choice('lookup', 'LOOKUP', 'Lookup'),
  '(',
  field('target', $.field_ref),
  optional(seq(
    choice('where', 'WHERE', 'Where'),
    '(',
    field('conditions', $.where_conditions), // Updated from lookup_where_conditions
    ')'
  )),
  ')'
),
```

4. **Update TableRelation**:
```javascript
_simple_table_relation: $ => seq(
  field('table', $._table_reference),
  optional(seq('.', field('field', $.field_ref))),
  optional($.where_clause) // Already using where_clause, no change needed
),
```

### Phase 5: Remove Duplicate Rules

1. After all usage points are updated and tests pass, remove:
   - `calc_where_clause`
   - `calc_where_conditions`
   - `calc_where_condition`
   - `lookup_where_conditions`
   - `lookup_where_condition`

## Migration Strategy

1. **Incremental Changes**:
   - First introduce the new unified rules while keeping old ones
   - Then update usage points one by one
   - Only remove old rules after all usage points are updated

2. **Backward Compatibility**:
   - Ensure the new rules handle all edge cases from original implementations
   - Maintain same field names and node structure where possible

## Testing and Validation

1. **Run existing test cases** to ensure no regressions
2. **Add new test cases** that specifically test:
   - Edge cases for all condition types
   - Mixed condition types in the same where clause
   - All operator types
   - All contexts where where clauses are used

3. **Verification Steps**:
   - Parse existing AL code samples
   - Verify AST structure matches expected output
   - Ensure no syntax errors are introduced

## Implementation Sequence

1. Add new unified condition rules
2. Add unified where_conditions rule
3. Update where_clause to use unified conditions
4. Update usage points one by one, starting with simpler contexts
5. Run tests after each update
6. Remove duplicate rules
7. Final testing pass

## Risk Assessment

1. **Potential Issues**:
   - AST structure changes might break existing tooling
   - Edge cases in condition syntax might be missed
   - Precedence issues might arise

2. **Mitigation**:
   - Thorough testing with diverse examples
   - Incremental changes with validation at each step

## Rollback Plan

If issues are discovered during implementation:
1. Revert to the pre-unification grammar
2. Create a more detailed test suite targeting the problem areas
3. Attempt incremental changes with more targeted scope

## Future Improvements

After successful unification:
1. Further simplify field reference handling
2. Add support for more complex conditions (e.g., nested conditions)
3. Improve error recovery for malformed WHERE clauses
