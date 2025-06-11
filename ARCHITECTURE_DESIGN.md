# Context-Sensitive Property Parsing Architecture

## Design Overview

This architecture eliminates lexical ambiguity between property keywords and variable names by creating context-sensitive parsing rules with clear precedence hierarchies.

## Core Design Principles

1. **Context Separation**: Property keywords only recognized in property assignment contexts
2. **High Variable Precedence**: Variable declarations get maximum precedence in variable contexts  
3. **Fallback Strategy**: Property identifiers fallback to regular identifiers when not in property context
4. **Elimination of Manual Aliases**: No more reactive additions to `_unreserved_identifier`

## Architecture Components

### 1. Context-Sensitive Property Identifier

**New Rule: `property_identifier`**
```javascript
property_identifier: $ => choice(
  // Property keywords - only valid in property assignment contexts
  'Importance',
  'Description', 
  'SourceTable',
  'SubType',
  'Subtype',
  'subtype', 
  'SUBTYPE',
  'IncludeCaption',
  'ExcludeCaption',
  // ... all other property keywords
  
  // Fallback to regular identifier for non-property contexts
  $.identifier
),
```

**Benefits:**
- Property keywords contained within property contexts
- Automatic fallback to identifier parsing
- No global lexical conflicts

### 2. High-Precedence Variable Parsing

**Enhanced Variable Declaration with Maximum Precedence:**
```javascript
variable_declaration: $ => choice(
  // Variable with value assignment - precedence 15
  prec.left(15, seq(
    field('names', $.variable_name_list),
    ':',
    optional(field('type', $.type_specification)),
    ':=',
    field('value', $._expression),
    ';'
  )),
  
  // Label variable declaration - precedence 12  
  prec.left(12, seq(
    field('names', $.variable_name_list),
    ':',
    field('type', alias(choice('Label', 'LABEL', 'label'), $.basic_type)),
    field('value', $.string_literal),
    optional(seq(',', field('attributes', $.label_attributes))),
    ';'
  )),
  
  // Regular variable declaration - precedence 10
  prec.left(10, seq(
    field('names', $.variable_name_list),
    ':',
    field('type', $.type_specification),
    optional(field('temporary', $.temporary)),
    ';'
  ))
)
```

**Benefits:**
- Variables always win conflicts in variable contexts
- Clear precedence hierarchy (10-15 vs current 1-3)
- Left-associative to handle multiple variables correctly

### 3. Clean Variable Identifier Chain

**Simplified Variable Name Resolution:**
```javascript
variable_name_list: $ => seq(
  field('name', $.variable_identifier),
  repeat(seq(',', field('name', $.variable_identifier)))
),

variable_identifier: $ => alias($.identifier, $.identifier),

// Simplified _unreserved_identifier (no manual aliases needed)
_unreserved_identifier: $ => alias($.identifier, $.identifier),
```

**Benefits:**
- Direct identifier reference without conflict resolution
- No manual property keyword aliases required
- Clean, maintainable code path

### 4. Context-Bound Property Assignments

**Enhanced Property Assignment with Context Binding:**
```javascript
property_assignment: $ => prec.right(5, seq(
  field('name', $.property_identifier),  // Context-sensitive property keywords
  '=',
  field('value', $.property_value),
  ';'
)),

property_list: $ => prec.left(6, seq(
  $.property_assignment,
  repeat($.property_assignment)
)),
```

**Benefits:**
- Properties only recognized in property assignment contexts
- Medium precedence (5-6) below variable precedence (10-15)
- Right-associative for proper property value binding

### 5. Object Context Hierarchy

**Clear Context Separation at Object Level:**
```javascript
object_body: $ => repeat(choice(
  // High precedence contexts
  prec(8, $.var_section),        // Variables get priority
  prec(7, $.field_section),      // Fields with their own property contexts
  
  // Medium precedence contexts  
  prec(6, $.property_list),      // Properties in object context
  prec(5, $.procedure),          // Procedures
  prec(5, $.trigger),           // Triggers
  
  // Low precedence fallbacks
  prec(1, $.generic_element)
)),

var_section: $ => prec.left(8, seq(
  'var',
  repeat1($.variable_declaration)  // High precedence variables
)),
```

**Benefits:**
- Clear hierarchy: Variables > Fields > Properties > Procedures
- Context boundaries prevent parsing ambiguity
- Explicit precedence ordering

## Precedence Strategy

### New Precedence Hierarchy
```
15: Variable with assignment (:=)
12: Label variable declaration  
10: Regular variable declaration
8:  Variable section context
7:  Field section context
6:  Property list context
5:  Property assignment, procedures, triggers
2:  Legacy property compatibility
1:  Generic fallback elements
```

### Conflict Resolution Strategy
1. **Variable Context**: Variables always win (precedence 10-15)
2. **Property Context**: Properties only valid in property assignments (precedence 5-6)
3. **Ambiguous Context**: Defaults to identifier parsing
4. **Legacy Support**: Existing precedence maintained for compatibility

## Implementation Phases

### Phase 1: Foundation Rules
```javascript
// New fundamental rules
property_identifier: $ => choice(/* property keywords */, $.identifier)
variable_identifier: $ => alias($.identifier, $.identifier)
property_assignment: $ => prec.right(5, seq($.property_identifier, '=', $.property_value, ';'))
```

### Phase 2: Variable Precedence Enhancement  
```javascript
// Enhanced variable declarations with high precedence
variable_declaration: $ => choice(
  prec.left(15, /* variable with assignment */),
  prec.left(12, /* label variable */),
  prec.left(10, /* regular variable */)
)
```

### Phase 3: Context Hierarchy
```javascript
// Object-level context separation
object_body: $ => repeat(choice(
  prec(8, $.var_section),
  prec(7, $.field_section), 
  prec(6, $.property_list),
  // ... other contexts
))
```

### Phase 4: Legacy Cleanup
```javascript
// Simplified without manual aliases
_unreserved_identifier: $ => alias($.identifier, $.identifier)
```

## Expected Behavior

### Before (Current)
```al
// Requires manual alias in _unreserved_identifier
Importance: Option Low,Normal,High;  // ❌ Conflicts without manual alias
```

### After (Context-Sensitive)
```al
// Automatically works without manual intervention
Importance: Option Low,Normal,High;  // ✅ Variable context, high precedence

// Property context still works
object {
    Importance = Additional;  // ✅ Property context, property_identifier
}
```

## Validation Criteria

1. **All 314 existing tests pass** - No regression in functionality
2. **New property keywords work automatically** - No manual aliases needed
3. **Context sensitivity** - Same keyword works differently in different contexts
4. **Performance maintained** - No significant parsing slowdown
5. **Maintainability improved** - No more reactive conflict resolution

## Risk Mitigation

1. **Precedence Conflicts**: Use explicit precedence levels with clear hierarchy
2. **Performance Impact**: Minimize precedence complexity, use efficient left-associativity  
3. **Regression Risk**: Comprehensive testing with existing test suite
4. **Edge Cases**: Fallback to identifier parsing for ambiguous contexts

This architecture provides a robust, scalable solution that automatically handles property/variable conflicts without manual maintenance.