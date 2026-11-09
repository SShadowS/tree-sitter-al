---
name: Tree-sitter Grammar Writing Guide
description: Guide for writing tree-sitter grammars (v0.25.x/0.26.x). Use when developing new grammars, handling conflicts, managing precedence, organizing rules, testing grammars, or debugging parse issues. Covers breadth-first development, conflict resolution, lexical vs parse precedence, and performance optimization.
---

# Tree-sitter Grammar Writing Guide

See `references/writing-grammar.md` for detailed documentation.

## Core Principles

1. **Intuitive Structure**: Nodes should reflect recognizable language constructs
2. **LR(1) Adherence**: GLR parsing works best with LR(1) grammars

## Development Strategy

### Breadth-First Skeleton

```javascript
rules: {
  source_file: $ => repeat($._definition),
  _definition: $ => choice($.function_def, $.class_def),
  function_def: $ => seq('func', field('name', $.id), $.params, $.block),
  _statement: $ => choice($.return_stmt, $.if_stmt, $.expr_stmt),
  expression: $ => choice($.id, $.number, $.binary_expr),
}
```

### Progressive Implementation

1. Establish skeleton structure
2. Flesh out individual sections
3. Test frequently with `tree-sitter parse`
4. Add corpus tests for each rule

## Conflict Resolution

### Precedence for Operators

```javascript
binary_expression: $ => choice(
  prec.left(2, seq($.expr, '*', $.expr)),  // Higher = binds tighter
  prec.left(1, seq($.expr, '+', $.expr)),
),
```

### Associativity

```javascript
prec.left(...)   // a * b * c => (a * b) * c
prec.right(...)  // a = b = c => a = (b = c)
```

### Declared Conflicts

```javascript
conflicts: $ => [
  [$.array, $.array_pattern],  // Intentional ambiguity
],
```

## Lexical vs Parse Precedence

**Critical distinction:**
- **Lexical**: Inside `token()`, determines token selection
- **Parse**: Outside `token()`, determines rule selection

```javascript
// Lexical precedence
hex: $ => token(prec(2, /0x[0-9a-f]+/)),
int: $ => token(prec(1, /[0-9]+/)),

// Parse precedence
binary: $ => prec.left(1, seq($.expr, '+', $.expr)),
```

## Rule Organization

| Technique | Purpose |
|-----------|---------|
| `_rule` prefix | Hide from tree (wrapper rules) |
| `field()` | Name children for access |
| `supertypes` | Abstract categories |
| `inline` | Remove wrapper nodes |

## Testing

```
==================
Test Name
==================
func add(x, y) { return x + y }
---
(source_file
  (function_definition
    name: (identifier)
    ...))
```

Commands:
- `tree-sitter test` - Run all tests
- `tree-sitter test -i 'pattern'` - Filter tests
- `tree-sitter test -u` - Update expectations
- `tree-sitter parse file.txt -d` - Debug output

## Common Issues

| Symptom | Fix |
|---------|-----|
| Unexpected ERROR | Check rule coverage, add prec() |
| Wrong associativity | Add prec.left/right |
| Conflict warnings | Add to conflicts[] or restructure |
| Keywords as identifiers | Set word field |
