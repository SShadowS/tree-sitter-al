# Tree-Sitter Grammar DSL Reference

Complete reference guide for tree-sitter grammar development (v0.25.x/0.26.x).

## Grammar Structure

A tree-sitter grammar is a JavaScript module exporting a grammar object:

```javascript
module.exports = grammar({
  name: 'language_name',

  rules: {
    // Required: Grammar rules
  },

  // Optional configuration
  extras: $ => [],
  inline: $ => [],
  conflicts: $ => [],
  externals: $ => [],
  supertypes: $ => [],
  word: $ => $.identifier,
  precedences: $ => [],
  reserved: $ => ({}),
});
```

## Core DSL Functions

### Sequence and Choice

| Function | Description | Example |
|----------|-------------|---------|
| `seq(rule1, rule2, ...)` | Match rules in order | `seq('if', $.expression, $.block)` |
| `choice(rule1, rule2, ...)` | Match one of the rules | `choice($.number, $.string)` |

### Repetition

| Function | Description | Example |
|----------|-------------|---------|
| `repeat(rule)` | Zero or more | `repeat($.statement)` |
| `repeat1(rule)` | One or more | `repeat1($.digit)` |
| `optional(rule)` | Zero or one | `optional($.else_clause)` |

### Tokens

| Function | Description | Example |
|----------|-------------|---------|
| `token(rule)` | Produce single token (no children) | `token(seq('0x', /[0-9a-f]+/))` |
| `token.immediate(rule)` | No whitespace before match | `token.immediate(/[a-z]+/)` |

**Use `token()` when:**
- Combining literals/regexes into single token
- Applying precedence at lexical level
- Performance optimization for complex patterns

### Precedence and Associativity

| Function | Description | Example |
|----------|-------------|---------|
| `prec(n, rule)` | Numeric precedence | `prec(2, seq($.expr, '*', $.expr))` |
| `prec.left([n], rule)` | Left associative | `prec.left(1, seq($.expr, '+', $.expr))` |
| `prec.right([n], rule)` | Right associative | `prec.right(seq($.expr, '=', $.expr))` |
| `prec.dynamic(n, rule)` | Runtime precedence | `prec.dynamic(1, $.ambiguous_rule)` |

**Precedence Guidelines:**
- Higher number = higher precedence (binds tighter)
- `prec.left()` - prefer shorter match (left recursion)
- `prec.right()` - prefer longer match (right recursion)
- `prec.dynamic()` - resolve at parse time, not generation time

### Node Manipulation

| Function | Description | Example |
|----------|-------------|---------|
| `field(name, rule)` | Assign field name to child | `field('condition', $.expression)` |
| `alias(rule, name)` | Rename node in tree | `alias($.identifier, $.type_name)` |

**Field Names:**
- Enable named access to children: `node.childForFieldName('condition')`
- Essential for tooling and queries
- Use consistently for semantic elements

**Alias Patterns:**
```javascript
// Rename to existing rule type
alias($.identifier, $.type_name)

// Rename to anonymous string (hidden in tree)
alias('keyword', 'special_keyword')

// Make hidden rule visible
alias($._hidden_rule, $.visible_name)
```

### Reserved Words (v0.24+)

```javascript
reserved: $ => ({
  contextual: ['async', 'await'],
  strict: ['class', 'function'],
}),

rules: {
  // Use reserved() to allow keywords as identifiers in context
  identifier: $ => reserved('contextual', /[a-z_]+/),
}
```

### Terminal Symbols

```javascript
// String literals (exact match)
'keyword'
"keyword"

// Regular expressions
/[a-zA-Z_][a-zA-Z0-9_]*/

// Unicode escapes
/[\u0080-\uFFFF]/

// RustRegex for advanced patterns (inline flags)
RustRegex('(?i)keyword')  // case-insensitive
```

**Regex Limitations:**
- No lookahead/lookbehind (LR(1) constraint)
- No backreferences
- No atomic groups

## Grammar Configuration

### extras

Tokens that may appear anywhere (whitespace, comments):

```javascript
extras: $ => [
  /\s/,
  $.comment,
  $.line_continuation,
],
```

**Best Practice:** Define complex patterns as named rules, then reference in extras.

### inline

Rules to inline (remove from tree, substitute content):

```javascript
inline: $ => [
  $._expression_base,
  $._statement_base,
],
```

**Use for:**
- Reducing tree depth
- Wrapper rules that add no semantic value

### conflicts

Declare intentional LR(1) conflicts:

```javascript
conflicts: $ => [
  [$.array_literal, $.array_pattern],
  [$.function_expression, $.arrow_function],
],
```

**When to use:**
- Legitimate syntactic ambiguity exists
- Context-dependent interpretation needed
- Parser should explore multiple paths

### externals

Tokens handled by external scanner (C code):

```javascript
externals: $ => [
  $.indent,
  $.dedent,
  $.newline,
  $._string_content,
],
```

**Use for:**
- Indentation-sensitive syntax
- Heredocs/raw strings
- Context-dependent tokenization
- State-dependent lexing

### word

Keyword extraction optimization:

```javascript
word: $ => $.identifier,
```

**Benefits:**
- Smaller, faster lexer
- Prevents `instanceofX` tokenizing as `instanceof` + `X`
- Required for proper keyword handling

### supertypes

Abstract category rules (hidden but queryable):

```javascript
supertypes: $ => [
  $.expression,
  $.statement,
  $.declaration,
],
```

**Use for:**
- Choice-based categorization rules
- Query pattern matching
- Reducing tree noise

### precedences (Named Precedence)

Define precedence levels by name:

```javascript
precedences: $ => [
  [
    'member',      // highest
    'call',
    'unary',
    'binary_times',
    'binary_plus',
    'binary_compare',
    'ternary',
    'assignment',  // lowest
  ],
],

rules: {
  binary_expression: $ => choice(
    prec.left('binary_times', seq($.expr, '*', $.expr)),
    prec.left('binary_plus', seq($.expr, '+', $.expr)),
  ),
}
```

## Hidden Rules

Rules starting with `_` are hidden from syntax tree:

```javascript
rules: {
  // Visible in tree
  expression: $ => choice(...),

  // Hidden - content appears but not this node
  _expression_inner: $ => choice(...),
}
```

**Use for:**
- Grouping rules without semantic meaning
- Internal grammar organization
- Reducing tree clutter

## Best Practices

### Grammar Design

1. **Start breadth-first**: Define major constructs first, then expand
2. **Flatten hierarchies**: Use precedence instead of deep nesting
3. **Use fields consistently**: Name all semantic children
4. **Hide helper rules**: Prefix with `_` for internal rules

### Conflict Resolution

1. **Lexical precedence**: Use `token(prec(n, ...))` for token selection
2. **Parse precedence**: Use `prec()` for rule selection
3. **Explicit conflicts**: Declare in `conflicts` array
4. **Associativity**: Use `prec.left()`/`prec.right()` for operators

### Token Selection Priority

When multiple tokens could match:

1. Context-aware validity (what parser expects)
2. Explicit precedence values
3. Match length (maximal munch)
4. Specificity (string > regex)
5. Rule order in grammar

### Performance

- Use `word` token for keyword extraction
- Inline wrapper rules
- Prefer `token()` for complex literals
- Keep `extras` minimal

## External Scanner Integration

Declare external tokens:

```javascript
externals: $ => [
  $.custom_token,
  $._scanner_hint,
],
```

Scanner provides these tokens via C code in `src/scanner.c`. External scanner has priority over normal lexing.

**Common patterns:**
- Indentation tracking (Python-style)
- Heredocs and raw strings
- Context-dependent keywords
- Preprocessor handling

## Common Patterns

### Case-Insensitive Keywords

```javascript
// Helper function
const kw = (word, precedence) => {
  const pattern = word.split('').map(c =>
    /[a-zA-Z]/.test(c) ? `[${c.toLowerCase()}${c.toUpperCase()}]` : c
  ).join('');
  const rule = new RegExp(pattern);
  return precedence !== undefined ? prec(precedence, rule) : rule;
};

// Usage
rules: {
  select_statement: $ => seq(kw('select'), ...),
}
```

### Optional Trailing Comma

```javascript
// Allow: (a, b) or (a, b,)
seq('(', commaSep($.element), optional(','), ')')

// Helper
function commaSep(rule) {
  return optional(seq(rule, repeat(seq(',', rule))));
}
```

### Operator Precedence Table

```javascript
const PREC = {
  ASSIGN: 1,
  OR: 2,
  AND: 3,
  COMPARE: 4,
  ADD: 5,
  MULT: 6,
  UNARY: 7,
  CALL: 8,
  MEMBER: 9,
};

binary_expression: $ => choice(
  prec.left(PREC.OR, seq($.expr, 'or', $.expr)),
  prec.left(PREC.AND, seq($.expr, 'and', $.expr)),
  prec.left(PREC.ADD, seq($.expr, choice('+', '-'), $.expr)),
  prec.left(PREC.MULT, seq($.expr, choice('*', '/'), $.expr)),
),
```

### Contextual Keywords

```javascript
// Keyword in one context, identifier in another
identifier: $ => choice(
  $._identifier_token,
  // Allow 'async' as identifier except in specific contexts
  reserved('contextual', 'async'),
),
```

## Version Notes (v0.25.x/v0.26.x)

### v0.26.x
- Windows MinGW-w64 support
- Improved error messages (quoted invalid nodes)
- WASI-SDK for WebAssembly compilation
- Removed deprecated `--no-bindings` flag

### v0.25.x
- Performance optimizations
- Error recovery improvements (prevent infinite loops)
- Build system refinements

### Configuration File

Modern projects use `tree-sitter.json`:

```json
{
  "grammars": [{
    "name": "language",
    "scope": "source.language",
    "file-types": ["ext"],
    "highlights": "queries/highlights.scm",
    "tags": "queries/tags.scm"
  }],
  "bindings": {
    "c": true,
    "node": true,
    "rust": true
  }
}
```

## Debugging Tips

1. **Generate and test incrementally**: Small changes, frequent testing
2. **Use `tree-sitter parse -d`**: Debug output shows parse decisions
3. **Check for conflicts**: `tree-sitter generate` reports them
4. **Test edge cases**: Empty inputs, single tokens, nested structures
5. **Validate with real code**: Test against production files

## Quick Reference Card

```
seq(a, b)        - a then b
choice(a, b)     - a or b
repeat(a)        - a* (zero or more)
repeat1(a)       - a+ (one or more)
optional(a)      - a? (zero or one)

prec(n, a)       - precedence n
prec.left(n, a)  - left associative
prec.right(n, a) - right associative
prec.dynamic(n, a) - runtime precedence

field('name', a) - named child
alias(a, b)      - rename node
token(a)         - single token
token.immediate(a) - no whitespace

$._rule          - hidden rule
$.rule           - visible rule
```
