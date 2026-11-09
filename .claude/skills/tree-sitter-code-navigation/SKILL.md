---
name: Tree-sitter Code Navigation
description: Reference for implementing code navigation with tree-sitter (v0.25.x/0.26.x). Use when writing tags.scm for definitions/references, locals.scm for scope tracking, or implementing Go to Definition, Find References, and symbol search. Covers standard tag vocabulary, scope analysis, and editor integration.
---

# Tree-sitter Code Navigation

See `references/code-navigation.md` for detailed documentation.

## Overview

- **tags.scm**: Identify definitions and references for navigation
- **locals.scm**: Track variable scopes for consistent highlighting

## Tags Queries

### Standard Definitions

| Capture | Purpose |
|---------|---------|
| `@definition.function` | Function declarations |
| `@definition.class` | Class declarations |
| `@definition.method` | Method declarations |
| `@definition.variable` | Variable declarations |
| `@definition.field` | Field/property declarations |
| `@definition.type` | Type declarations |

### Standard References

| Capture | Purpose |
|---------|---------|
| `@reference.call` | Function/method calls |
| `@reference.class` | Class references |
| `@reference.type` | Type references |

### Example

```scheme
; Function definition
(function_declaration
  name: (identifier) @name) @definition.function

; Method call
(call_expression
  function: (member_expression
    property: (property_identifier) @name)) @reference.call
```

## Locals Queries

### Fixed Captures

| Capture | Meaning |
|---------|---------|
| `@local.scope` | Introduces new scope |
| `@local.definition` | Variable definition |
| `@local.reference` | Potential reference |

### Example

```scheme
; Scopes
(function_declaration) @local.scope
(block) @local.scope

; Definitions
(formal_parameters (identifier) @local.definition)
(variable_declarator name: (identifier) @local.definition)

; References
(identifier) @local.reference
```

## Integration with Highlights

```scheme
; Only highlight as function if not a local variable
((identifier) @function.call
  (#is-not? local))
```

## File Structure

```
queries/
  highlights.scm    # Syntax highlighting
  locals.scm        # Variable scope tracking
  tags.scm          # Code navigation
```

## tree-sitter.json Configuration

```json
{
  "grammars": [{
    "name": "my_language",
    "highlights": "queries/highlights.scm",
    "locals": "queries/locals.scm",
    "tags": "queries/tags.scm"
  }]
}
```

## CLI Commands

```bash
tree-sitter tags file.py           # Show tags
tree-sitter tags -t file.py        # With timing
tree-sitter tags -q file.py        # Quiet (validate only)
```

## Testing

```ruby
# test/tags/test.rb
def foo
  # ^ definition.function
end

foo()
# ^ reference.call
```
