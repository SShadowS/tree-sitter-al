# Implementation Specification

## Detailed Pseudocode for Context-Sensitive Architecture

### Core Rule Modifications

#### 1. Property Identifier Rule (New)
```javascript
property_identifier: $ => choice(
  // Core property keywords that commonly conflict
  'Importance',
  'Description',
  'SourceTable', 
  'SubType',
  'Subtype',
  'subtype',
  'SUBTYPE',
  'IncludeCaption',
  'ExcludeCaption',
  
  // Additional properties that may conflict
  'Caption',
  'Visible',
  'Enabled',
  'Editable',
  'Width',
  'Height',
  
  // Fallback to regular identifier for non-property contexts
  $.identifier
),
```

#### 2. Variable Identifier Chain (Modified)
```javascript
// Simplified variable identifier - no manual aliases
variable_identifier: $ => alias($.identifier, $.identifier),

// Clean variable name list
variable_name_list: $ => seq(
  field('name', $.variable_identifier),
  repeat(seq(',', field('name', $.variable_identifier)))
),

// Simplified unreserved identifier (remove all manual aliases)
_unreserved_identifier: $ => alias($.identifier, $.identifier),

// Updated unquoted variable name  
_unquoted_variable_name: $ => $.variable_identifier,
```

#### 3. High-Precedence Variable Declarations (Modified)
```javascript
variable_declaration: $ => choice(
  // Variable with value assignment - highest precedence
  prec.left(15, seq(
    field('names', $.variable_name_list),
    ':',
    optional(field('type', $.type_specification)),
    ':=',
    field('value', $._expression),
    ';'
  )),
  
  // Label variable with attributes - high precedence
  prec.left(12, seq(
    field('names', $.variable_name_list),
    ':',
    field('type', alias(choice('Label', 'LABEL', 'label'), $.basic_type)),
    field('value', $.string_literal),
    optional(seq(',', field('attributes', seq(
      $.label_attribute,
      repeat(seq(',', $.label_attribute))
    )))),
    ';'
  )),
  
  // Regular variable declaration - medium-high precedence  
  prec.left(10, seq(
    field('names', $.variable_name_list),
    ':',
    field('type', $.type_specification),
    optional(field('temporary', $.temporary)),
    ';'
  ))
),
```

#### 4. Context-Sensitive Property Assignments (Modified)
```javascript
// Individual property assignment with context-sensitive identifier
property_assignment: $ => prec.right(5, seq(
  field('name', $.property_identifier),  // Uses new context-sensitive rule
  '=',
  field('value', $.property_value),
  ';'
)),

// Property list with medium precedence
property_list: $ => prec.left(6, seq(
  $.property_assignment,
  repeat($.property_assignment)
)),

// Legacy property rule for compatibility (updated to use property_identifier)
property: $ => prec(5, choice(
  $.access_by_permission_property,
  $.allow_in_customizations_property,
  // ... all existing property types, but they should use property_identifier where applicable
)),
```

#### 5. Object Context Hierarchy (Modified)
```javascript
// Page object body with clear context separation
page_body: $ => repeat(choice(
  // Highest precedence - variables always win
  prec(8, $.var_section),
  
  // High precedence - fields with their own property contexts
  prec(7, $.field_section),
  prec(7, $.area_section),
  prec(7, $.actions_section),
  
  // Medium precedence - object-level properties
  prec(6, $.property_list),
  
  // Lower precedence - procedures and triggers
  prec(5, $.procedure),
  prec(5, $.trigger),
  
  // Fallback
  prec(1, $._generic_element)
)),

// Table object body (similar pattern)
table_body: $ => repeat(choice(
  prec(8, $.var_section),      // Variables first
  prec(7, $.field_section),    // Fields second  
  prec(6, $.property_list),    // Properties third
  prec(5, $.procedure),        // Procedures fourth
  prec(5, $.trigger),         // Triggers fourth
  prec(1, $._generic_element)  // Fallback
)),

// Variable section with high precedence
var_section: $ => prec.left(8, seq(
  'var',
  repeat1($.variable_declaration)  // High precedence variables
)),
```

### Specific Property Rule Updates

#### Update Individual Property Rules
```javascript
// Example: Update importance property to use property_identifier
importance_property: $ => seq(
  // Remove direct 'Importance' literal
  // 'Importance',  // OLD
  field('name', alias('Importance', $.property_name)),  // NEW - more explicit
  '=',
  field('value', $.importance_value),
  ';'
),

// OR, use the global property_assignment pattern:
// Remove individual property rules and rely on:
// property_assignment: $ => seq($.property_identifier, '=', $.property_value, ';')
```

### Migration Strategy

#### Phase 1: Add New Rules (No Breaking Changes)
```javascript
// Add new rules alongside existing ones
property_identifier: $ => choice(/* all property keywords */, $.identifier),
variable_identifier: $ => alias($.identifier, $.identifier),
property_assignment: $ => prec.right(5, seq($.property_identifier, '=', $.property_value, ';')),
```

#### Phase 2: Update Variable Precedence  
```javascript
// Increase precedence levels for variable declarations
variable_declaration: $ => choice(
  prec.left(15, /* assignment variables */),
  prec.left(12, /* label variables */), 
  prec.left(10, /* regular variables */)
),
```

#### Phase 3: Update Context Hierarchy
```javascript
// Add precedence to object body elements
object_body: $ => repeat(choice(
  prec(8, $.var_section),
  prec(7, $.field_section),
  prec(6, $.property_list),
  // ...
)),
```

#### Phase 4: Clean Up Manual Aliases
```javascript
// Simplify _unreserved_identifier (remove all manual aliases)
_unreserved_identifier: $ => alias($.identifier, $.identifier),
```

### Testing Strategy

#### Test Case Categories
1. **Existing Tests**: All 314 tests must continue passing
2. **Conflict Resolution**: Property keywords as variable names
3. **Context Sensitivity**: Same keyword in property vs variable context
4. **New Properties**: Future property keywords work automatically

#### Example Test Cases
```al
// Test 1: Property keyword as variable name (should work automatically)
page 123 "Test" {
    var
        Importance: Option Low,Normal,High;  // Should parse without manual alias
        Description: Text[100];              // Should parse without manual alias
        SubType: Text[20];                   // Should parse without manual alias
}

// Test 2: Same keywords in property context (should still work)  
page 124 "Test2" {
    Importance = Additional;     // Property context
    Description = 'Test page';   // Property context
    
    var
        Importance: Option;      // Variable context - different parsing path
        Description: Text;       // Variable context - different parsing path
}

// Test 3: New property keywords (should work automatically)
page 125 "Test3" {
    NewPropertyKeyword = SomeValue;  // Property context
    
    var
        NewPropertyKeyword: Text;    // Variable context - should work without manual alias
}
```

This specification provides the complete technical details needed for implementing the context-sensitive architecture.