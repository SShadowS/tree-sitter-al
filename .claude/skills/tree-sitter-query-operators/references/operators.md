# Tree-sitter Query Operators Reference

A comprehensive guide to query operators in tree-sitter (versions 0.25.x/0.26.x).

## Overview

Query operators are the building blocks for matching patterns in syntax trees. They control how nodes are captured, quantified, grouped, and constrained.

---

## Node Pattern Syntax (S-expressions)

The fundamental structure for matching nodes.

```scheme
; Basic node match
(identifier)

; Node with specific children
(binary_expression (number_literal) (number_literal))

; Nested patterns
(call_expression
  function: (member_expression
    object: (identifier)
    property: (property_identifier)))
```

---

## Capture Operator (@)

Associates names with matched nodes for later reference. Captures always follow the node they annotate.

### Syntax
```scheme
(node_type) @capture_name
```

### Examples

```scheme
; Single capture
(identifier) @variable

; Multiple captures in one pattern
(assignment_expression
  left: (identifier) @left_side
  right: (identifier) @right_side)

; Capture entire complex structure
(function_declaration
  name: (identifier) @function_name
  body: (block) @function_body) @function

; Capture with field constraint
(call_expression
  function: (identifier) @callee
  arguments: (arguments) @args)
```

### Capture Naming Conventions

| Pattern | Use Case |
|---------|----------|
| `@variable` | General variable reference |
| `@function.name` | Dotted names for scope |
| `@keyword.control` | Highlight category |
| `@local.definition` | Semantic role |
| `@_hidden` | Underscore prefix for internal use |

---

## Field Operator (:)

Constrains matches to specific child relationships defined in the grammar.

### Syntax
```scheme
(parent_type field_name: (child_type))
```

### Examples

```scheme
; Match by field name
(class_declaration
  name: (identifier) @class_name)

; Multiple fields
(function_declaration
  name: (identifier) @name
  parameters: (parameter_list) @params
  body: (block) @body)

; Nested field access
(assignment_expression
  left: (member_expression
    object: (identifier) @object
    property: (property_identifier) @property))
```

### Benefits
- More precise matching than positional children
- Self-documenting queries
- Robust against grammar changes

---

## Negated Field Operator (!)

Matches nodes that DO NOT have a specific field.

### Syntax
```scheme
(node_type !field_name)
```

### Examples

```scheme
; Match classes without type parameters
(class_declaration !type_parameters) @class

; Match functions without return type
(function_declaration !return_type) @procedure

; Match objects without a specific optional field
(object_literal !trailing_comma) @object

; Combine with positive field constraints
(function_declaration
  name: (identifier) @name
  !async) @sync_function
```

### Use Cases
- Distinguish between syntax variants
- Match simplified forms
- Enforce absence of optional constructs

---

## Wildcard Operators (_ and (_))

Match any node without specifying the type.

### Named Wildcard: `(_)`

Matches any **named** node (excludes anonymous tokens).

```scheme
; Match any expression as function argument
(call_expression
  arguments: (arguments (_) @arg))

; Match any statement in a block
(block (_) @statement)

; Match any node type in a position
(binary_expression
  left: (_) @operand
  right: (_) @operand)
```

### Anonymous-Inclusive Wildcard: `_`

Matches **any** node including anonymous tokens (operators, punctuation).

```scheme
; Match anything including operators
(binary_expression _ @child)

; Capture all tokens in array
(array _ @element)
```

### Comparison

| Wildcard | Matches Named | Matches Anonymous |
|----------|--------------|-------------------|
| `(_)` | Yes | No |
| `_` | Yes | Yes |

---

## Quantification Operators (+, *, ?)

Control how many times a pattern can repeat.

### Plus (+): One or More

Matches one or more consecutive occurrences.

```scheme
; Match one or more comments
(comment)+ @doc_comments

; Match consecutive attributes
(attribute)+ @attributes

; Match repeated elements
(array (expression)+ @elements)
```

### Asterisk (*): Zero or More

Matches zero or more occurrences.

```scheme
; Match optional decorators
(decorator)* @decorators
(function_declaration) @function

; Match any number of leading comments
(comment)* @leading_comments
(class_declaration) @class

; Optional repeated modifiers
(modifier)* (function_declaration) @function
```

### Question Mark (?): Optional (Zero or One)

Marks a node as optional.

```scheme
; Optional return type
(function_declaration
  name: (identifier) @name
  return_type: (type)? @return_type)

; Optional else clause
(if_statement
  consequence: (block) @then
  alternative: (block)? @else)

; Optional visibility modifier
(visibility_modifier)? (function_declaration) @function
```

### Quantifier Behavior Notes

1. **Greedy Matching**: Quantifiers match as many nodes as possible
2. **Capture Scope**: Quantified captures may contain multiple nodes
3. **Predicate Behavior**: By default, predicates must match ALL quantified nodes (use `any-` prefix for any-match behavior)

```scheme
; All comments must match the pattern
(((comment)+ @doc)
  (#match? @doc "^///"))

; ANY comment matches (any- prefix)
(((comment)+ @has_todo)
  (#any-match? @has_todo "TODO"))
```

---

## Grouping Operator (Parentheses)

Groups sibling sequences so quantifiers can apply to the entire group.

### Syntax
```scheme
(sibling1 sibling2)*
```

### Examples

```scheme
; Match comma-separated items
(argument_list
  (expression) ("," (expression))* @args)

; Match key-value pairs
(object
  ((property_name) ":" (expression))* @pairs)

; Group complex repeating pattern
((comment) (decorator)* (function_declaration))+ @documented_functions

; Optional grouped sequence
((visibility) (static_modifier))? (field_declaration) @field
```

### Use Cases
- Comma-separated lists
- Repeating compound structures
- Optional multi-node sequences

---

## Alternation Operator ([])

Matches any one of several alternative patterns. Similar to regex character classes.

### Syntax
```scheme
[pattern1 pattern2 pattern3]
```

### Examples

```scheme
; Match multiple node types
[
  (identifier)
  (member_expression property: (property_identifier))
] @function_reference

; Match keyword tokens
["break" "continue" "return" "throw"] @keyword.control

; Match alternative expression types
(binary_expression
  operator: ["+" "-" "*" "/"] @operator)

; Complex alternatives with captures
[
  (function_declaration name: (identifier) @name)
  (method_definition name: (property_identifier) @name)
  (arrow_function) @name
] @function
```

### Alternation Best Practices

1. **Simplest First**: Put simpler patterns first for performance
2. **Shared Captures**: Captures work across alternatives
3. **Token Matching**: Excellent for matching operator sets

```scheme
; Arithmetic operators
(binary_expression
  operator: [
    "+"  ; addition
    "-"  ; subtraction
    "*"  ; multiplication
    "/"  ; division
    "%"  ; modulo
  ] @operator.arithmetic)

; Comparison operators
(binary_expression
  operator: [
    "==" "!=" "<" ">" "<=" ">="
  ] @operator.comparison)
```

---

## Anchor Operator (.)

Constrains positional matching for children within a parent node.

### Syntax Positions

| Position | Meaning |
|----------|---------|
| `. child` | Child must be first named child |
| `child .` | Child must be last named child |
| `a . b` | `b` must immediately follow `a` |

### First Child Anchor

```scheme
; Match only if identifier is first child
(array . (identifier) @first_element)

; First statement in block
(block . (_) @first_statement)

; First parameter
(parameter_list . (parameter) @first_param)
```

### Last Child Anchor

```scheme
; Match only if expression is last child
(array (expression) @last_element .)

; Last statement
(block (_) @last_statement .)

; Return statement must be last
(block (return_statement) @final_return .)
```

### Immediate Sibling Anchor

```scheme
; Comments immediately before function
(comment) @doc . (function_declaration) @function

; Consecutive identifiers (no nodes between)
(identifier) @first . (identifier) @second

; Attribute immediately followed by declaration
(attribute) @attr . (declaration) @decl
```

### Important Notes

1. **Ignores Anonymous Nodes**: Anchors only consider named nodes
2. **Multiple Anchors**: Can combine anchor constraints
3. **With Quantifiers**: Anchors apply after quantification

```scheme
; First element and immediately followed by another
(array . (identifier) @first . (identifier) @second)

; All comments before function (greedy), with adjacency
(comment)+ @docs . (function_declaration) @function
```

---

## Anonymous Node Matching (Quoted Strings)

Matches literal tokens (operators, keywords, punctuation) that appear in the source.

### Syntax
```scheme
"token"
```

### Examples

```scheme
; Match operators
(binary_expression operator: "+" @plus_operator)
(binary_expression operator: "==" @equality)

; Match punctuation
(array "[" @open "]" @close)
(object "{" @brace.open "}" @brace.close)

; Match keywords (when they're tokens)
(if_statement "if" @keyword)
(return_statement "return" @keyword)

; Use in alternations
(binary_expression
  operator: ["and" "or" "not"] @keyword.operator)
```

### Anonymous vs Named

| Type | Example | Grammar Rule |
|------|---------|--------------|
| Named | `identifier`, `string` | Defined as rule |
| Anonymous | `"+"`, `"if"` | Literal in rule |

---

## Special Node Types

### ERROR Node

Matches unrecognized/unparseable text.

```scheme
; Capture error regions for highlighting
(ERROR) @error

; Find errors in specific contexts
(function_declaration (ERROR) @syntax_error)
```

### MISSING Node

Matches zero-width nodes inserted by error recovery.

```scheme
; Generic missing node
(MISSING) @missing

; Typed missing node (v0.25+)
(MISSING identifier) @missing_identifier
(MISSING ";") @missing_semicolon
```

### Supertype Matching

Match abstract categories that include multiple concrete types.

```scheme
; Match any expression type
(expression) @any_expression

; Match specific subtype through supertype
(expression/binary_expression) @binary

; Combined with other patterns
(assignment_expression
  right: (expression) @value)
```

---

## Operator Precedence

When combining operators, understand their interaction:

1. **Parentheses** bind tightest (grouping)
2. **Quantifiers** apply to immediately preceding pattern
3. **Fields** constrain within node context
4. **Anchors** apply positional constraints
5. **Alternations** create pattern choices

### Complex Pattern Example

```scheme
; Match documented public functions
((comment)+ @documentation           ; One or more comments
  .                                   ; Immediately followed by
  [                                   ; Either:
    ("public" (function_declaration)) ;   public function
    ("export" (function_declaration)) ;   exported function
  ] @function)
```

---

## Version-Specific Features

### Tree-sitter 0.24.x
- Added `ts_query_end_byte_for_pattern` API
- Fixed pattern_map optimization for wildcards with immediate children

### Tree-sitter 0.25.x
- **MISSING node support in queries**: Can match `(MISSING)` and typed variants like `(MISSING identifier)`
- **Supertype query validation**: Structural verification prevents invalid patterns
- **Wildcard matching fixes**: Wildcards don't incorrectly mark child patterns as guaranteed
- Query timeout API for long-running queries
- Streaming iterator for query results

### Tree-sitter 0.26.x
- Performance improvements for query matching
- Better error messages for invalid queries
- Maintenance and stability fixes

---

## Query Performance Tips

1. **Be Specific**: Use field names over positional matching
2. **Limit Depth**: Deep nesting increases match complexity
3. **Use Fields**: `name: (identifier)` faster than `(identifier)`
4. **Prefer Anchors**: Constrain search space when possible
5. **Simple Alternations**: Fewer alternatives = faster matching

```scheme
; SLOWER: Positional matching
(function_declaration (identifier) (parameter_list) (block))

; FASTER: Field-based matching
(function_declaration
  name: (identifier)
  parameters: (parameter_list)
  body: (block))
```

---

## Quick Reference

```scheme
; === OPERATORS ===

; Capture: Associates name with node
(identifier) @name

; Field: Constrains by relationship
(parent field: (child))

; Negated Field: Node lacks field
(node !missing_field)

; Wildcards
(_)                    ; Any named node
_                      ; Any node (including anonymous)

; Quantifiers
(pattern)+            ; One or more
(pattern)*            ; Zero or more
(pattern)?            ; Optional

; Grouping
(a b)+                ; Quantify group

; Alternation
[pattern1 pattern2]   ; Match any

; Anchors
. child               ; Must be first
child .               ; Must be last
a . b                 ; Immediate siblings

; Anonymous Nodes
"token"               ; Match literal

; Special Nodes
(ERROR)               ; Parse error
(MISSING)             ; Error recovery
(MISSING type)        ; Typed missing (0.25+)
(supertype/subtype)   ; Supertype match
```

---

## Sources

- [Tree-sitter Query Operators](https://tree-sitter.github.io/tree-sitter/using-parsers/queries/2-operators.html)
- [Tree-sitter Query Syntax](https://tree-sitter.github.io/tree-sitter/using-parsers/queries/1-syntax.html)
- [Tree-sitter Predicates and Directives](https://tree-sitter.github.io/tree-sitter/using-parsers/queries/3-predicates-and-directives.html)
- [Cursorless Query Syntax](https://www.cursorless.org/docs/contributing/tree-sitter-query-syntax/)
- [Tree-sitter Releases](https://github.com/tree-sitter/tree-sitter/releases)
