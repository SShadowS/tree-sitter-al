---
name: Tree-sitter External Scanners
description: Reference for tree-sitter external scanner API (v0.25.x/0.26.x). Use when implementing custom tokenization in C for indentation, heredocs, raw strings, context-dependent tokens, or complex string interpolation. Covers the 5 required functions, TSLexer interface, valid_symbols, serialization, and common pitfalls.
---

# Tree-sitter External Scanners

See `references/external-scanners.md` for detailed documentation.

## When to Use

- Indentation-based syntax (Python INDENT/DEDENT)
- Heredocs (`<<EOF...EOF`)
- Raw strings with variable delimiters
- Context-dependent tokenization

## Setup

### grammar.js

```javascript
externals: $ => [
  $.indent,
  $.dedent,
  $._error_sentinel,
],
```

### src/scanner.c

```c
#include "tree_sitter/parser.h"
#include "tree_sitter/alloc.h"

enum TokenType {
  INDENT,           // Must match externals order
  DEDENT,
  ERROR_SENTINEL,
};
```

## Five Required Functions

```c
// 1. Create scanner state
void *tree_sitter_lang_external_scanner_create() {
  return ts_calloc(1, sizeof(Scanner));
}

// 2. Destroy scanner
void tree_sitter_lang_external_scanner_destroy(void *payload) {
  ts_free(payload);
}

// 3. Serialize state (max 1024 bytes)
unsigned tree_sitter_lang_external_scanner_serialize(void *payload, char *buffer) {
  Scanner *s = payload;
  buffer[0] = s->state;
  return 1;
}

// 4. Deserialize state
void tree_sitter_lang_external_scanner_deserialize(void *payload, const char *buffer, unsigned len) {
  Scanner *s = payload;
  s->state = len > 0 ? buffer[0] : 0;
}

// 5. Main scan function
bool tree_sitter_lang_external_scanner_scan(void *payload, TSLexer *lexer, const bool *valid_symbols) {
  if (valid_symbols[INDENT]) {
    // Recognize INDENT token
  }
  return false;
}
```

## TSLexer Interface

| Field/Method | Purpose |
|--------------|---------|
| `lookahead` | Current Unicode code point (int32_t) |
| `result_symbol` | Set to recognized token type |
| `advance(lexer, skip)` | Move to next char (skip=true for whitespace) |
| `mark_end(lexer)` | Mark token boundary |
| `get_column(lexer)` | Current column position |
| `eof(lexer)` | Check end-of-file |

## valid_symbols Array

```c
// Check what tokens parser expects
if (valid_symbols[INDENT]) { /* INDENT is valid here */ }

// Error recovery detection (all tokens valid)
if (valid_symbols[ERROR_SENTINEL]) {
  return false;  // Let tree-sitter handle it
}
```

## Common Pitfalls

### Infinite Loops

```c
// DANGEROUS
while (lexer->lookahead != '"') { lexer->advance(lexer, false); }

// SAFE
while (!lexer->eof(lexer) && lexer->lookahead != '"') {
  lexer->advance(lexer, false);
}
```

### Zero-Width Tokens

Only use when:
- Marking structural boundaries
- Grammar ensures single match per position

### mark_end() Behavior

After `mark_end()`, further `advance()` doesn't expand token:

```c
scan_word(lexer, "foo");
lexer->mark_end(lexer);     // Token ends here
scan_word(lexer, "bar");     // Not part of token
```

## Quick Reference

| Task | Code |
|------|------|
| Get current char | `lexer->lookahead` |
| Advance | `lexer->advance(lexer, false)` |
| Skip whitespace | `lexer->advance(lexer, true)` |
| Mark token end | `lexer->mark_end(lexer)` |
| Set result | `lexer->result_symbol = TOKEN` |
| Check EOF | `lexer->eof(lexer)` |
| Allocate | `ts_malloc(size)` |
| Free | `ts_free(ptr)` |
