# AL Grammar Conflict Analysis

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

## Recommended Solution Strategy

**Context-Sensitive Parsing**: Replace global property literals with contextual property identifiers that only match in property assignment contexts, combined with high precedence for variable declarations to ensure variable names take priority in variable contexts.