# Tree-Sitter Grammar Writing Guide

A comprehensive guide to writing tree-sitter grammars for version 25.x/26.x. Use this skill when developing or modifying grammar rules for tree-sitter parsers.

## Core Principles

Tree-sitter grammar writing requires two essential properties:

1. **Intuitive Structure**: Since Tree-sitter produces concrete syntax trees where each node corresponds to grammar symbols, your grammar's structure should directly reflect recognizable language constructs rather than abstract intermediaries.

2. **LR(1) Adherence**: Tree-sitter uses GLR parsing, functioning most efficiently with LR(1) grammars - similar to Yacc/Bison but distinct from ANTLR or ambiguous language specs.

---

## Grammar DSL Functions

### Core Pattern Matching

| Function | Description | EBNF Equivalent |
|----------|-------------|-----------------|
| `seq(rule1, rule2, ...)` | Matches rules in sequence | Concatenation |
| `choice(rule1, rule2, ...)` | Matches one of several rules | `\|` (pipe) |
| `repeat(rule)` | Matches zero or more occurrences | `*` |
| `repeat1(rule)` | Matches one or more occurrences | `+` |
| `optional(rule)` | Matches zero or one occurrence | `?` |

### Terminal Symbols

Terminals are defined using JavaScript strings and regular expressions:

```javascript
// String literal
'function'

// Regular expression (Rust regex syntax)
/[a-z_][a-z0-9_]*/

// Explicit Rust regex with flags
new RustRegex('(?i)[a-z_][a-z0-9_]*')
```

**Supported regex features**: character classes, ranges, sets, quantifiers, alternation, grouping, Unicode escapes.

**Not supported**: lookahead/lookaround assertions (LR(1) constraint).

### Precedence and Associativity

| Function | Purpose |
|----------|---------|
| `prec(number, rule)` | Parse precedence (higher = binds tighter) |
| `prec.left([number], rule)` | Left associativity (prefers earlier endings) |
| `prec.right([number], rule)` | Right associativity (prefers later endings) |
| `prec.dynamic(number, rule)` | Runtime precedence for genuine ambiguities |

**Default precedence is zero.**

### Token Functions

| Function | Purpose |
|----------|---------|
| `token(rule)` | Treat complex rule as single token |
| `token.immediate(rule)` | Match only without preceding whitespace |

### Syntax Tree Annotation

| Function | Purpose |
|----------|---------|
| `alias(rule, name)` | Make rule appear under alternative name |
| `field(name, rule)` | Assign field name to matched child node |
| `reserved(wordset, rule)` | Override reserved words for contextual keywords |

---

## Grammar Configuration Fields

```javascript
module.exports = grammar({
    name: 'my_language',

    // Token appearing anywhere (default: whitespace)
    extras: $ => [/\s/, $.comment],

    // Rules to remove by inlining
    inline: $ => [$._expression_inner],

    // Intended LR(1) conflicts (enables GLR)
    conflicts: $ => [
        [$.array, $.array_pattern],
    ],

    // External scanner tokens
    externals: $ => [$.indent, $.dedent, $.newline],

    // Named precedence levels (descending order)
    precedences: $ => [
        ['call', 'unary', 'binary'],
    ],

    // Keyword extraction optimization
    word: $ => $.identifier,

    // Abstract categories hidden from tree
    supertypes: $ => [$.expression, $.statement],

    // Contextual reserved word sets
    reserved: $ => ({
        property_names: ['get', 'set'],
    }),

    rules: {
        // Grammar rules here
    }
});
```

---

## Standard Rule Naming Conventions

| Rule Name | Purpose |
|-----------|---------|
| `source_file` | Root node for entire file |
| `expression` / `statement` | Choice rules for constructs |
| `block` | Parent for block scopes |
| `type` | Language type representations |
| `identifier` | Variable/function names (often `word` token) |
| `string` | String literal representation |
| `comment` | Comments (commonly an extra) |

---

## Grammar Development Strategy

### Breadth-First Skeleton Development

Begin with major symbol groupings before detailed implementation:

```javascript
rules: {
    source_file: $ => repeat($._definition),

    _definition: $ => choice(
        $.function_definition,
        $.variable_definition,
    ),

    function_definition: $ => seq(
        'func',
        field('name', $.identifier),
        field('parameters', $.parameter_list),
        field('return_type', optional($._type)),
        field('body', $.block),
    ),

    _statement: $ => choice(
        $.return_statement,
        $.if_statement,
        $.expression_statement,
    ),

    expression: $ => choice(
        $.identifier,
        $.number,
        $.binary_expression,
    ),

    _type: $ => choice(
        $.primitive_type,
        $.array_type,
    ),
}
```

### Progressive Implementation

1. Establish skeleton structure
2. Progressively flesh out individual sections
3. Test frequently with `tree-sitter parse`
4. Add corpus tests for each rule

---

## Managing Ambiguity

### Precedence for Expression Hierarchies

Flat expression structures create inherent ambiguity. Use precedence to indicate binding tightness:

```javascript
unary_expression: $ => prec(2, choice(
    seq('-', $.expression),
    seq('!', $.expression),
)),

binary_expression: $ => choice(
    prec.left(2, seq($.expression, '*', $.expression)),
    prec.left(2, seq($.expression, '/', $.expression)),
    prec.left(1, seq($.expression, '+', $.expression)),
    prec.left(1, seq($.expression, '-', $.expression)),
),
```

**Higher precedence values bind more tightly.**

### Associativity for Repeated Operators

For expressions like `a * b * c`, use `prec.left` or `prec.right`:

```javascript
// a * b * c => (a * b) * c (left associative)
prec.left(2, seq($.expression, '*', $.expression))

// a = b = c => a = (b = c) (right associative)
prec.right(1, seq($.expression, '=', $.expression))
```

### Intentional Conflicts

When constructs legitimately parse multiple ways, declare conflicts explicitly:

```javascript
conflicts: $ => [
    [$.array, $.array_pattern],
    [$.object, $.object_pattern],
    [$.primary_expression, $.pattern],
]
```

This enables GLR parsing for those specific ambiguities.

---

## Rule Organization Techniques

### Hidden Rules (Underscore Prefix)

Prefix rules with underscores to hide them from syntax trees:

```javascript
// Visible in tree
expression: $ => choice(...),

// Hidden from tree - just a wrapper
_expression: $ => choice(
    $.identifier,
    $.binary_expression,
    $.call_expression,
),
```

**Use hidden rules for**: wrapper rules, internal groupings, abstract categories.

### Fields for Named Children

Name child nodes for easier programmatic access:

```javascript
function_definition: $ => seq(
    'func',
    field('name', $.identifier),
    field('parameters', $.parameter_list),
    field('return_type', optional($._type)),
    field('body', $.block),
),
```

**Benefits**:
- Clearer tree navigation in queries
- Self-documenting grammar structure
- Stable API across grammar changes

### Extras for Ubiquitous Tokens

Define tokens that can appear anywhere:

```javascript
extras: $ => [
    /\s/,
    $.comment,
],
```

**Best Practice**: Define complex extras as rules rather than inline patterns to reduce parser size:

```javascript
// Good: reduces parser size
extras: $ => [/\s/, $.comment],
rules: {
    comment: $ => token(choice(
        seq('//', /.*/),
        seq('/*', /[^*]*\*+([^/*][^*]*\*+)*/, '/'),
    )),
}

// Avoid: larger parser
extras: $ => [
    /\s/,
    token(seq('//', /.*/)),  // Inline complex pattern
],
```

### Supertypes for Abstract Categories

Prevent visible nodes for abstract category rules while keeping them query-able:

```javascript
supertypes: $ => [
    $.expression,
    $.statement,
],

rules: {
    expression: $ => choice(
        $.identifier,
        $.binary_expression,
        $.call_expression,
    ),
}
```

---

## Lexical Analysis

Tree-sitter's two-phase process (lexing then parsing) determines token selection through this hierarchy:

1. **Context-aware Lexing**: Only valid tokens at current position are considered
2. **Lexical Precedence**: Higher `prec()` values within `token()` win
3. **Match Length**: Longest matching sequence selected
4. **Match Specificity**: String literals preferred over regexes
5. **Rule Order**: Earlier grammar appearance wins ties

### Critical Distinction

> "Parse precedence determines rule choice for token sequences; lexical precedence determines token selection at text positions. These operate at different levels, with lexing occurring first."

Misunderstanding this distinction causes most difficult bugs.

### Example: Lexical vs Parse Precedence

```javascript
// Lexical precedence (inside token)
hex_literal: $ => token(prec(2, /0x[0-9a-f]+/)),
integer: $ => token(prec(1, /[0-9]+/)),

// Parse precedence (outside token)
binary_expression: $ => prec.left(1, seq($.expression, '+', $.expression)),
```

---

## Keywords and Word Tokens

Specify a `word` token to extract keywords automatically:

```javascript
grammar({
    name: 'javascript',
    word: $ => $.identifier,

    rules: {
        binary_expression: $ => choice(
            prec.left(1, seq($.expression, 'instanceof', $.expression)),
        ),
        identifier: $ => /[a-z_][a-z0-9_]*/,
    },
})
```

**How it works**:
- Tree-sitter matches keywords through the word token first
- Prevents `instanceofSomething` from tokenizing as `instanceof` + identifier
- Improves error detection
- Reduces parser compilation time

**Requirement**: The word token must be unique and not reused elsewhere.

---

## External Scanners

Use external scanners for tokens that cannot be expressed through regular expressions.

### Common Use Cases

- Indent/dedent tokens (Python)
- Heredocs (Bash, Ruby)
- Raw strings with variable delimiters (Rust)
- Context-dependent tokenization

### Grammar Configuration

```javascript
externals: $ => [
    $.indent,
    $.dedent,
    $.newline,
    $.error_sentinel,  // For error recovery
]
```

### Required C Functions

```c
// Create scanner state
void* tree_sitter_my_lang_external_scanner_create() {
    return ts_calloc(1, sizeof(Scanner));
}

// Destroy scanner state
void tree_sitter_my_lang_external_scanner_destroy(void *payload) {
    ts_free(payload);
}

// Serialize state for undo/redo
unsigned tree_sitter_my_lang_external_scanner_serialize(
    void *payload, char *buffer
) {
    // Return bytes written (max 1024)
}

// Restore state from buffer
void tree_sitter_my_lang_external_scanner_deserialize(
    void *payload, const char *buffer, unsigned length
) {
    // Restore state
}

// Main scan function
bool tree_sitter_my_lang_external_scanner_scan(
    void *payload,
    TSLexer *lexer,
    const bool *valid_symbols
) {
    // Return true if token recognized
}
```

### TSLexer Interface

| Field/Method | Purpose |
|--------------|---------|
| `lookahead` | Current unicode character (32-bit) |
| `result_symbol` | Assign recognized token type |
| `advance(skip)` | Move to next character (skip=true for whitespace) |
| `mark_end()` | Mark token boundary |
| `get_column()` | Current column position |
| `eof()` | Check end-of-file |

### Error Recovery Pattern

```c
// Handle error recovery mode
if (valid_symbols[ERROR_SENTINEL]) {
    return false;  // Let internal lexer handle errors
}
```

**See**: `.claude/skills/external-scanner-techniques.md` for detailed patterns.

---

## Testing

### Test File Format

Tests use specially-formatted files in `test/corpus/`:

```
==================
Return statements
==================

func x() int {
  return 1;
}

---

(source_file
  (function_definition
    name: (identifier)
    parameters: (parameter_list)
    return_type: (primitive_type)
    body: (block
      (return_statement (number)))))
```

### Test Commands

| Command | Purpose |
|---------|---------|
| `tree-sitter test` | Run all tests |
| `tree-sitter test -i 'pattern'` | Run matching tests |
| `tree-sitter test -u` | Update expected trees |
| `tree-sitter test -d` | Show debug output |

### Test Attributes

| Attribute | Purpose |
|-----------|---------|
| `:cst` | Output as concrete syntax tree |
| `:error` | Assert parse contains errors |
| `:fail-fast` | Stop testing if this fails |
| `:skip` | Skip this test |
| `:language(LANG)` | Specify parser for multi-parser repos |

### Best Practices

- Add tests for every grammar rule
- Test all permutations of language constructs
- Include edge cases and error scenarios
- Never delete tests - fix underlying issues

---

## Performance Considerations

### Reduce Parser Size

1. **Define extras as rules** instead of inline patterns
2. **Use word token** for keyword extraction
3. **Inline simple wrapper rules** via `inline` configuration

### Optimize Lexer

1. **Use specific patterns** over broad ones
2. **Prefer string literals** over equivalent regexes
3. **Order rules by frequency** (common cases first)

### Grammar Structure

1. **Avoid deep nesting** in choice rules
2. **Minimize conflicts** - each conflict adds parser states
3. **Use prec sparingly** - prefer grammar restructuring

---

## Common Patterns

### Comma-Separated Lists

```javascript
// Optional trailing comma
parameter_list: $ => seq(
    '(',
    optional(seq(
        $.parameter,
        repeat(seq(',', $.parameter)),
        optional(','),
    )),
    ')',
),

// Using commaSep helper
function commaSep(rule) {
    return optional(commaSep1(rule));
}

function commaSep1(rule) {
    return seq(rule, repeat(seq(',', rule)));
}
```

### Binary Operators with Precedence

```javascript
// Table-driven approach
const PREC = {
    OR: 1,
    AND: 2,
    COMPARE: 3,
    ADD: 4,
    MULT: 5,
    UNARY: 6,
};

binary_expression: $ => choice(
    prec.left(PREC.OR, seq($.expression, 'or', $.expression)),
    prec.left(PREC.AND, seq($.expression, 'and', $.expression)),
    prec.left(PREC.COMPARE, seq($.expression, choice('==', '!='), $.expression)),
    prec.left(PREC.ADD, seq($.expression, choice('+', '-'), $.expression)),
    prec.left(PREC.MULT, seq($.expression, choice('*', '/'), $.expression)),
),
```

### Contextual Keywords

```javascript
// Use reserved() for property names that are usually keywords
object_property: $ => seq(
    reserved($._property_name, choice('get', 'set', 'async')),
    ':',
    $.expression,
),
```

---

## Debugging Grammar Issues

### Parse a File

```bash
tree-sitter parse file.txt -d > debug.log 2>&1
```

### Generate Debug Graphs

```bash
tree-sitter test -D  # Creates log.html with parse trees
```

### Common Issues

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Unexpected ERROR nodes | Missing rule or wrong precedence | Check rule coverage, add prec() |
| Wrong associativity | Missing prec.left/right | Add associativity to binary rules |
| Token not recognized | Pattern too specific | Broaden regex or add alternatives |
| Conflict warnings | Ambiguous grammar | Add to conflicts[] or restructure |
| Keywords as identifiers | Missing word token | Set word field in grammar |

---

## Version Notes (25.x/26.x)

### Recent Features

- **RustRegex class**: Explicit Rust regex patterns with flags
- **reserved() function**: Contextual reserved words
- **Dynamic precedence improvements**: Better GLR handling
- **Enhanced test attributes**: `:cst`, `:fail-fast`, `:language()`

### Migration Considerations

- `word` token now required for proper keyword handling
- `inline` should be used for simple wrapper rules
- External scanners should use `ts_malloc`/`ts_free` for allocation

---

## Quick Reference: Decision Flow

```
Does this token need context-sensitive lexing?
├─ No → Use string/regex in grammar
└─ Yes → Does it need complex lookahead?
    ├─ No → Use token() with prec()
    └─ Yes → Use external scanner

Is there a parsing conflict?
├─ Intentional ambiguity → Add to conflicts[]
├─ Precedence issue → Add prec() or prec.left/right()
└─ Grammar structure issue → Restructure rules

Should this node appear in the tree?
├─ Yes → Normal rule name
├─ No (wrapper) → Underscore prefix: _rule
└─ Abstract category → Add to supertypes[]
```

---

## Related Skills

- `external-scanner-techniques.md` - Detailed scanner patterns
- Project `CLAUDE.md` - AL-specific grammar patterns
