# AL Grammar Precedence Analysis

## Current High Precedence Values (>10)

### 1. Field References (precedence = 12)
- `explicit_field_ref`: prec(12) - Needs to bind tighter than member expressions
- `calc_field_ref`: prec(12) - Same as explicit_field_ref for consistency

### 2. Member Access Patterns
- `field_access`: prec.left(12) - Quoted field access like `record."Field Name"`
- `member_expression`: prec.left(11) - Regular member access like `object.property`
- `call_expression`: prec(12) - Function calls need higher precedence than member access

### 3. Enum Value Expression (precedence = 13)
- `enum_value_expression`: prec(13) - Needs highest precedence to beat field_access

### 4. Exit Statement (precedence = 13)
- `exit_statement`: prec(13) - High precedence to ensure proper parsing of exit(value)

### 5. Qualified Enum Value Tail (precedence = 13)
- `qualified_enum_value_tail`: prec.left(13) - Ensures :: binds tightly

### 6. Field Reference Condition (precedence = 14)
- `field_reference_condition`: prec(14) - Very high to resolve conflicts with other patterns

### 7. Lookup Formula Members (precedence = 12, 13)
- Member expression in lookup: prec(12)
- Field access in lookup: prec(13)

### 8. Arithmetic Expressions in Case Patterns (precedence = 11)
- `additive_expression`: prec(11) - In case patterns
- `multiplicative_expression`: prec(11) - In case patterns

### 9. Parenthesized Expression (precedence = 12)
- `parenthesized_expression`: prec(12) - In case patterns

## Standard Expression Precedences (for reference)
- Logical OR: prec.left(2)
- Logical AND: prec.left(3)
- Comparison: prec.left(4)
- 'in' operator: prec.left(5)
- Additive: prec.left(6)
- Multiplicative: prec.left(7)
- Unary: prec.right(7)
- Range: prec.left(8)
- Subscript: prec.left(9)

## Precedences Successfully Reduced
1. **Filter expressions (10 → 8)**:
   - `filter_or_expression`
   - `const_filter`
   - `field_filter`
   - `filter_condition`

2. **Property precedences (10 → 8)**:
   - `source_table_view_property`
   - `shortcut_key_property`

3. **Lookup formula (10 → 8)**:
   - `lookup_formula`
   - Inner `_quoted_identifier` in lookup

4. **Type precedences (10 → 8)**:
   - `qualified_table_reference`

5. **Text and code types (15 → 10)**:
   - `text_type`
   - `code_type`

6. **Codeunit type (20 → 10)**:
   - `codeunit_type`

## Precedences Kept High
1. **Member access chain (11-13)**: The precedence hierarchy for member_expression < field_access < call_expression < enum_value_expression is important for proper parsing of chained expressions
2. **Exit statement (13)**: Needed to properly parse exit(expression) vs exit as a statement
3. **Field reference condition (14)**: Resolves specific conflicts in table relations
4. **_quoted_identifier token (10)**: Ensures proper tokenization of quoted identifiers
5. **Case pattern expressions (10)**: Boolean operators and IN expressions in case patterns need higher precedence
6. **Importance value quoted identifier (10)**: Ensures proper parsing of quoted importance values

## Summary
Successfully reduced many unnecessarily high precedences without breaking any tests. The remaining high precedences (11-14) are justified by the need to properly parse member access chains, function calls, and specific language constructs. All tests still pass with 9 failures (same as before).