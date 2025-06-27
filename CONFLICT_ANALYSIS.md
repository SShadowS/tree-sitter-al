# AL Grammar Conflict Analysis

## Known Parsing Issues

### 1. Complex Preprocessor Patterns in Table Extensions
**File**: `./BC.History/SubscriptionBilling/Source/Subscription Billing/Service Objects/Table Extensions/Item.TableExt.al`

**Issue**: Parser fails to correctly parse table extensions with complex preprocessor conditionals that wrap if statements where:
- The condition check and `begin` keyword are inside `#if`
- The actual block content is outside the preprocessor conditional
- Multiple nested preprocessor blocks exist in procedures

**Pattern**:
```al
#if not CLEAN25
    if PriceCalculationMgt.IsExtendedPriceCalculationEnabled() then begin
#endif
        // statements here
#if not CLEAN25
    end;
#endif
```

**Status**: This edge case affects a small number of files. The grammar handles simpler preprocessor patterns correctly. Further investigation needed for complex nested cases.

## Current Architecture Analysis

### Property Definition Patterns

**1. Direct Literal Keywords (Major Conflict Source)**
```javascript
// Line 2207-2212
importance_property: $ => seq(
  'Importance',           // Direct literal string - CONFLICTS with variable names
  '=',
  field('value', $.importance_value),
  ';'
),

// Line 1340-1345  
subtype_property: $ => seq(
  choice('Subtype', 'SubType', 'subtype', 'SUBTYPE'),  // Multiple case variants
  '=', 
  field('value', alias($.subtype_value, $.value)),
  ';'
),
```

**2. Case-Insensitive Regex Patterns**
```javascript
// Line 2526-2531
description_property: $ => seq(
  alias(/[dD][eE][sS][cC][rR][iI][pP][tT][iI][oO][nN]/, 'Description'),
  '=',
  field('value', $.string_literal),
  ';'
),
```

### Variable Declaration Architecture

**Current Precedence Levels:**
- **prec(3)**: Variable with value assignment (`:=`)
- **prec(2)**: Label variable declaration  
- **prec(1)**: Regular variable declaration

**Variable Name Resolution Chain:**
```javascript
variable_declaration → _variable_name_list → _unquoted_variable_name → _unreserved_identifier
```

**Manual Conflict Resolution (Current Approach):**
```javascript
// Line 4139-4157
_unreserved_identifier: $ => choice(
  alias($.identifier, $.identifier),
  // Manual aliases for each conflicting property keyword:
  alias('Importance', $.identifier),                                      // Importance property
  alias(/[dD][eE][sS][cC][rR][iI][pP][tT][iI][oO][nN]/, $.identifier),   // Description property
  alias(/[sS][oO][uU][rR][cC][eE][tT][aA][bB][lL][eE]/, $.identifier),   // SourceTable property
  alias('IncludeCaption', $.identifier),                                  // IncludeCaption property
  alias('ExcludeCaption', $.identifier),                                  // ExcludeCaption property
  alias(choice('Subtype', 'SubType', 'subtype', 'SUBTYPE'), $.identifier) // SubType property
),
```

### Property Hierarchy and Usage

**Property Precedence:**
- **prec.left(3)**: property_list
- **prec(2)**: individual property rules
- **prec(4)**: optional property_list in object contexts
- **Special high precedence**: source_table_view_property (prec(10)), hide_value_property (prec(12))

**Property Categories:**
- `_universal_properties` (line 5334): Includes description_property, subtype_property
- `_display_properties` (line 5350): Includes importance_property
- Combined in field/page/object contexts through composed choice rules

### Root Cause of Conflicts

**1. Lexical Ambiguity:**
Property keywords like `'Importance'` are recognized globally in the lexical phase, causing conflicts when the same string appears in variable contexts.

**2. Precedence Insufficient:**
Current variable precedence (1-3) vs property precedence (2-4) creates overlapping ranges where both interpretations are valid.

**3. Context Insensitivity:**
Property keywords are defined as global literals rather than context-sensitive patterns, making them always "available" for matching.

**4. Reactive Maintenance:**
Each new conflict requires manual addition to `_unreserved_identifier`, making the grammar non-scalable.

## Specific Conflict Examples

### High-Impact Conflicts (Currently Manually Resolved)
1. **Importance**: Property keyword that's commonly used as variable name for enum types
2. **Description**: Universal property that conflicts with descriptive variable names  
3. **SubType**: Property with multiple case variants that conflicts with common variable pattern
4. **SourceTable**: Property keyword that conflicts with table reference variables
5. **IncludeCaption/ExcludeCaption**: Label-related properties that conflict with boolean variables

### Parsing Ambiguity Examples
```al
// This could be parsed as either:
Importance = Additional;  // Property assignment
Importance : Option;      // Variable declaration

// Currently resolved by manual aliases in _unreserved_identifier
```

## Current Limitations

1. **Non-scalable**: Every new property keyword potentially requires manual conflict resolution
2. **Reactive**: Conflicts are discovered and fixed after they cause parsing failures
3. **Maintenance overhead**: _unreserved_identifier becomes a growing list of special cases
4. **Architectural debt**: Fundamental issue not addressed, only symptoms patched

## Recommended Solution: Contextual Keyword Pattern

The most robust and scalable solution is to adopt a **Contextual Keyword Pattern**. This pattern resolves ambiguity by explicitly defining that certain keywords can be treated as identifiers in specific contexts, such as variable declarations. This approach is proactive, scalable, and eliminates the need for a `conflicts` array for these specific issues.

### Core Principles

1.  **Case-Insensitive Keywords**: All property keywords must be defined using the `kw('keyword')` helper function. This ensures that `Importance`, `importance`, and `IMPORTANCE` are all treated as the same token, reducing complexity.

2.  **Contextual Aliasing**: For any keyword that can also be used as a variable name, a corresponding alias must be added to the `_unquoted_variable_name` rule. The alias should also use the `kw()` helper to maintain case-insensitivity.

    ```javascript
    // In _unquoted_variable_name rule
    alias(kw('importance'), $.identifier)
    ```

3.  **High Precedence for Variable Declarations**: Variable declaration rules (`variable_declaration`, `parameter_declaration`) should have a higher precedence than property assignment rules. This ensures that in an ambiguous situation like `Importance : Enum "My Enum";`, the parser correctly interprets it as a variable declaration.

### Implementation Steps

1.  **Identify Conflicting Keywords**: Systematically identify all keywords that can be used as both property names and variable identifiers.
2.  **Convert to `kw()`**: Ensure all property definitions use the `kw()` helper.
3.  **Add Aliases**: For each conflicting keyword, add an `alias(kw('keyword'), $.identifier)` to the `_unquoted_variable_name` rule.
4.  **Remove Manual Aliases**: Remove the old, case-sensitive aliases from `_unreserved_identifier`.
5.  **Verify Precedence**: Ensure that variable-related rules have appropriate precedence to win in ambiguous contexts.
6.  **Test Extensively**: Add test cases that specifically target these contextual keywords in both property and variable contexts to prevent regressions.

By implementing this pattern, the grammar becomes more resilient, easier to maintain, and correctly reflects the contextual nature of the AL language's keywords. This strategy has already been successfully applied to several keywords and should be expanded to cover all remaining conflicts.