---
name: Tree-sitter Grammar DSL
description: Reference for tree-sitter grammar.js DSL functions (v0.25.x/0.26.x). Use when writing grammar rules with seq, choice, repeat, optional, prec, field, alias, token, or configuring extras, conflicts, externals, inline, supertypes, word, precedences, reserved. Covers all DSL functions, grammar configuration, and common patterns.
---

# Tree-sitter Grammar DSL

Quick reference for grammar.js functions. See `references/grammar-dsl.md` for detailed documentation.

## Grammar Structure

```javascript
module.exports = grammar({
  name: 'language_name',
  rules: { /* required */ },

  // Optional configuration
  extras: $ => [/\s/, $.comment],
  inline: $ => [$._wrapper],
  conflicts: $ => [[$.a, $.b]],
  externals: $ => [$.indent, $.dedent],
  word: $ => $.identifier,
  supertypes: $ => [$.expression],
  precedences: $ => [['high', 'low']],
  reserved: $ => ({ keywords: ['if', 'else'] }),
});
```

## Core Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `seq(a, b, ...)` | Match in order | `seq('if', $.expr, $.block)` |
| `choice(a, b, ...)` | Match one of | `choice($.num, $.str)` |
| `repeat(rule)` | Zero or more | `repeat($.stmt)` |
| `repeat1(rule)` | One or more | `repeat1($.digit)` |
| `optional(rule)` | Zero or one | `optional($.else)` |

## Precedence & Associativity

| Function | Purpose |
|----------|---------|
| `prec(n, rule)` | Numeric precedence (higher = tighter) |
| `prec.left([n], rule)` | Left associative |
| `prec.right([n], rule)` | Right associative |
| `prec.dynamic(n, rule)` | Runtime precedence |

```javascript
// Operator precedence
binary_expression: $ => choice(
  prec.left(2, seq($.expr, '*', $.expr)),
  prec.left(1, seq($.expr, '+', $.expr)),
),
```

## Node Manipulation

| Function | Purpose | Example |
|----------|---------|---------|
| `field(name, rule)` | Name child node | `field('name', $.id)` |
| `alias(rule, name)` | Rename in tree | `alias($.id, $.type)` |
| `token(rule)` | Single token | `token(seq('0x', /[0-9a-f]+/))` |
| `token.immediate(rule)` | No whitespace | `token.immediate(/[a-z]+/)` |

## Configuration Fields

| Field | Purpose |
|-------|---------|
| `extras` | Tokens allowed anywhere (whitespace, comments) |
| `inline` | Rules to inline (remove from tree) |
| `conflicts` | Declared LR(1) conflicts |
| `externals` | External scanner tokens |
| `word` | Keyword extraction token |
| `supertypes` | Abstract category rules |
| `precedences` | Named precedence levels |
| `reserved` | Contextual keyword sets |

## Hidden Rules

Rules prefixed with `_` are hidden from syntax tree:

```javascript
_expression: $ => choice($.id, $.num),  // Hidden wrapper
expression: $ => choice($.id, $.num),   // Visible node
```

## Common Patterns

```javascript
// Case-insensitive keyword helper
const kw = word => new RegExp(
  word.split('').map(c => `[${c.toLowerCase()}${c.toUpperCase()}]`).join('')
);

// Comma-separated list
function commaSep(rule) {
  return optional(seq(rule, repeat(seq(',', rule))));
}

// Operator precedence table
const PREC = { OR: 1, AND: 2, CMP: 3, ADD: 4, MUL: 5 };
```
