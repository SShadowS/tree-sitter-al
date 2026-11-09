# Tree-Sitter External Scanners - Official API Reference

Official documentation reference for tree-sitter external scanners (v0.24.x - v0.26.x). Use this skill when you need to understand the scanner API, implement scanner callbacks, or troubleshoot scanner behavior.

**Related skill**: `external-scanner-techniques.md` covers implementation patterns learned from analyzing other parsers.

---

## When to Use External Scanners

External scanners handle tokens whose structure cannot be described with regular expressions. Common use cases:

| Use Case | Example |
|----------|---------|
| Indentation-based syntax | Python's INDENT/DEDENT tokens |
| Heredocs | Bash `<<EOF...EOF` |
| Percent strings | Ruby `%w[foo bar]` |
| Raw strings with dynamic delimiters | Rust `r##"..."##` |
| Context-dependent tokenization | Same character means different things |
| Complex string interpolation | Nested quotes within interpolations |

**Key principle**: "An external scanner is a set of C functions that you, the grammar author, can write by hand to add custom logic for recognizing certain tokens."

---

## Setup Requirements

### 1. Grammar Configuration

Add `externals` array listing all external token names:

```javascript
module.exports = grammar({
  name: "my_language",

  externals: $ => [
    $.indent,
    $.dedent,
    $.newline,
    $.string_content,
    $._error_sentinel,  // Hidden token for error recovery
  ],

  rules: {
    // ... your grammar rules
  }
});
```

### 2. Scanner File Location

Create scanner at `src/scanner.c` (automatically included by tree-sitter).

### 3. Token Enumeration

Order MUST match the `externals` array exactly:

```c
#include "tree_sitter/parser.h"
#include "tree_sitter/alloc.h"
#include "tree_sitter/array.h"

enum TokenType {
  INDENT,       // Must match order in externals array
  DEDENT,
  NEWLINE,
  STRING_CONTENT,
  ERROR_SENTINEL,
};
```

---

## The Five Required Functions

Every external scanner must implement these five functions. The naming convention is `tree_sitter_{language_name}_external_scanner_{function}`.

### 1. create()

```c
void *tree_sitter_my_language_external_scanner_create() {
  // Allocate and initialize scanner state
  // Called once when parser initializes the language

  // Return NULL if no state needed
  return NULL;

  // Or allocate state:
  Scanner *scanner = ts_calloc(1, sizeof(Scanner));
  array_init(&scanner->indent_stack);
  return scanner;
}
```

**Purpose**: Initialize scanner object. Allocate heap memory if state is needed.

**Returns**: Pointer to scanner state, or `NULL` if stateless.

### 2. destroy()

```c
void tree_sitter_my_language_external_scanner_destroy(void *payload) {
  if (payload == NULL) return;

  Scanner *scanner = (Scanner *)payload;
  array_delete(&scanner->indent_stack);
  ts_free(scanner);
}
```

**Purpose**: Clean up resources when parser is deleted or language changes.

**Parameter**: The pointer returned by `create()`.

### 3. serialize()

```c
unsigned tree_sitter_my_language_external_scanner_serialize(
  void *payload,
  char *buffer
) {
  if (payload == NULL) return 0;

  Scanner *scanner = (Scanner *)payload;
  size_t size = 0;

  // Store each state variable
  buffer[size++] = scanner->inside_string;
  buffer[size++] = scanner->indent_stack.size;

  for (uint32_t i = 0; i < scanner->indent_stack.size; i++) {
    if (size >= TREE_SITTER_SERIALIZATION_BUFFER_SIZE) break;
    buffer[size++] = scanner->indent_stack.contents[i];
  }

  return size;
}
```

**Purpose**: Persist complete scanner state for syntax tree storage and incremental parsing.

**Returns**: Number of bytes written (max: `TREE_SITTER_SERIALIZATION_BUFFER_SIZE`, typically 1024).

**Critical**: "The `serialize` function must store its entire state, and `deserialize` must restore the entire state."

### 4. deserialize()

```c
void tree_sitter_my_language_external_scanner_deserialize(
  void *payload,
  const char *buffer,
  unsigned length
) {
  Scanner *scanner = (Scanner *)payload;

  // Always reset state first!
  scanner->inside_string = false;
  array_clear(&scanner->indent_stack);

  if (length == 0) return;  // Initial state

  size_t size = 0;
  scanner->inside_string = buffer[size++];

  uint8_t stack_size = buffer[size++];
  for (uint32_t i = 0; i < stack_size && size < length; i++) {
    array_push(&scanner->indent_stack, buffer[size++]);
  }
}
```

**Purpose**: Restore scanner state from serialized bytes.

**Best practice**: Explicitly clear/reset all state variables before restoration.

### 5. scan()

```c
bool tree_sitter_my_language_external_scanner_scan(
  void *payload,
  TSLexer *lexer,
  const bool *valid_symbols
) {
  Scanner *scanner = (Scanner *)payload;

  // Check what tokens the parser expects
  if (valid_symbols[INDENT]) {
    // Try to recognize an INDENT token
    // ...
  }

  if (valid_symbols[STRING_CONTENT]) {
    return scan_string_content(scanner, lexer);
  }

  return false;  // No token recognized
}
```

**Purpose**: Core lexical analysis - recognize and emit tokens.

**Returns**: `true` if token recognized, `false` otherwise.

---

## TSLexer Structure

The `scan()` function receives a `TSLexer` pointer providing access to the input:

| Field/Method | Type | Purpose |
|--------------|------|---------|
| `lookahead` | `int32_t` | Current Unicode code point (32-bit) |
| `result_symbol` | `TSSymbol` | Set this to the recognized token type |
| `advance(lexer, skip)` | function | Move to next character. `skip=true` treats char as whitespace |
| `mark_end(lexer)` | function | Mark current position as token boundary |
| `get_column(lexer)` | function | Get current column (code points since line start) |
| `is_at_included_range_start(lexer)` | function | Check if parser skipped characters (multi-language) |
| `eof(lexer)` | function | Check for end-of-file |

### Typical Scan Pattern

```c
bool scan_string_content(Scanner *scanner, TSLexer *lexer) {
  bool has_content = false;

  while (!lexer->eof(lexer)) {
    if (lexer->lookahead == '"') {
      // End of string - mark boundary before the quote
      lexer->mark_end(lexer);
      break;
    }

    if (lexer->lookahead == '\\') {
      // Escape sequence
      lexer->advance(lexer, false);
      if (!lexer->eof(lexer)) {
        lexer->advance(lexer, false);
      }
    } else {
      lexer->advance(lexer, false);
    }

    has_content = true;
  }

  if (has_content) {
    lexer->result_symbol = STRING_CONTENT;
    return true;
  }

  return false;
}
```

---

## Helper Libraries

### Memory Allocation (`tree_sitter/alloc.h`)

Always use tree-sitter's allocators for consistent memory management:

```c
#include "tree_sitter/alloc.h"

void *ptr = ts_malloc(size);        // Instead of malloc
void *ptr = ts_calloc(count, size); // Instead of calloc
void *ptr = ts_realloc(ptr, size);  // Instead of realloc
ts_free(ptr);                        // Instead of free
```

### Dynamic Arrays (`tree_sitter/array.h`)

Use the array macros for collections:

```c
#include "tree_sitter/array.h"

// Declare array type
typedef Array(uint16_t) IndentStack;

// In scanner struct
typedef struct {
  IndentStack indents;
} Scanner;

// Usage
void *create() {
  Scanner *s = ts_calloc(1, sizeof(Scanner));
  array_init(&s->indents);
  return s;
}

void push_indent(Scanner *s, uint16_t level) {
  array_push(&s->indents, level);
}

uint16_t pop_indent(Scanner *s) {
  return array_pop(&s->indents);  // Returns value
}

uint16_t *peek_indent(Scanner *s) {
  return array_back(&s->indents);  // Returns pointer
}

void clear_indents(Scanner *s) {
  array_clear(&s->indents);
}

void destroy(void *payload) {
  Scanner *s = payload;
  array_delete(&s->indents);
  ts_free(s);
}
```

---

## The valid_symbols Array

The `valid_symbols` parameter tells the scanner which token types the parser expects at the current position:

```c
bool scan(void *payload, TSLexer *lexer, const bool *valid_symbols) {
  // Check if parser expects INDENT token
  if (valid_symbols[INDENT]) {
    // This token type is valid here
  }

  // Multiple tokens might be valid simultaneously
  if (valid_symbols[STRING_START] || valid_symbols[IDENTIFIER]) {
    // Parser could accept either
  }
}
```

### Priority During Error Recovery

During error recovery, ALL tokens may be marked valid. Use a sentinel token to detect this:

```javascript
// In grammar.js
externals: $ => [
  $.indent,
  $.dedent,
  $._error_sentinel,  // Hidden sentinel
],
```

```c
bool scan(void *payload, TSLexer *lexer, const bool *valid_symbols) {
  // Detect error recovery mode
  if (valid_symbols[ERROR_SENTINEL]) {
    // Either:
    // 1. Handle error recovery specially
    // 2. Return false to let tree-sitter handle it
    return false;
  }

  // Normal scanning logic
  // ...
}
```

---

## Keyword Handling

External scanners can handle literal keywords:

```javascript
externals: $ => [
  'if',
  'then',
  'else',
  $.custom_token,
],
```

The scanner has priority over tree-sitter's internal lexer. If the scanner returns `true`, that token is used. If it returns `false`, tree-sitter's lexer handles it.

**Warning**: If you list a keyword in `externals` without defining it in grammar rules, the scanner becomes solely responsible for recognizing it.

---

## Scanner Priority

"External scanners have priority over Tree-sitter's normal lexing process. When a token listed in the externals array is valid at a given position, the external scanner is called first."

This enables:
- Overriding default tokenization in specific contexts
- Complex disambiguation beyond regex capabilities
- Context-sensitive token recognition

---

## Common Pitfalls and Warnings

### Infinite Loops

External scanners can easily create infinite loops. Always:
- Use `lexer->eof(lexer)` in while loops (not `lookahead == 0`)
- Ensure you advance the lexer or return
- Never emit zero-width tokens without advancing

```c
// DANGEROUS - potential infinite loop
while (lexer->lookahead != '"') {
  lexer->advance(lexer, false);
}

// SAFE - check for EOF
while (!lexer->eof(lexer) && lexer->lookahead != '"') {
  lexer->advance(lexer, false);
}
```

### Zero-Width Tokens

Be extremely careful with zero-width tokens (tokens that don't consume input):

```c
// Zero-width token - marks position without consuming
if (should_emit_marker) {
  lexer->mark_end(lexer);  // Token ends at current position
  lexer->result_symbol = BLOCK_END;
  return true;  // Returned without advancing!
}
```

Only use zero-width tokens when:
- Marking structural boundaries (like block end)
- The grammar ensures they can only match once per position

### mark_end() Behavior

After calling `mark_end()`, subsequent `advance()` calls don't expand the token:

```c
// Token includes "foo" only, not "bar"
scan_word(lexer, "foo");
lexer->mark_end(lexer);      // Token boundary set here
scan_word(lexer, "bar");      // Advanced but not part of token
lexer->result_symbol = FOO;
return true;
```

---

## Version-Specific Notes (0.24.x - 0.26.x)

### v0.26.4 (February 2025)
- Fix: `result_symbol` field of lexer reset in wasm memory between invocations
- Fix: Memory management bugs in WebAssembly scanner contexts

### v0.26.1 (December 2024)
- Windows support using MinGW-w64 for scanner compilation
- Fix: Crash when loading languages with old ABI via wasm

### v0.25.9 (September 2024)
- Warning: Grammar validation warns when extra rules can lead to parser hangs
- Reserved word DSL declarations

### General Compatibility
- Serialize/deserialize must be deterministic for incremental parsing
- Maximum serialization buffer: `TREE_SITTER_SERIALIZATION_BUFFER_SIZE` (1024 bytes)
- Scanner state must be self-contained (no external references)

---

## Complete Minimal Example

```c
#include "tree_sitter/parser.h"
#include "tree_sitter/alloc.h"

enum TokenType {
  STRING_CONTENT,
  RAW_STRING_START,
  RAW_STRING_END,
};

typedef struct {
  uint8_t raw_string_hash_count;
} Scanner;

void *tree_sitter_example_external_scanner_create() {
  return ts_calloc(1, sizeof(Scanner));
}

void tree_sitter_example_external_scanner_destroy(void *payload) {
  ts_free(payload);
}

unsigned tree_sitter_example_external_scanner_serialize(
  void *payload,
  char *buffer
) {
  Scanner *scanner = payload;
  buffer[0] = scanner->raw_string_hash_count;
  return 1;
}

void tree_sitter_example_external_scanner_deserialize(
  void *payload,
  const char *buffer,
  unsigned length
) {
  Scanner *scanner = payload;
  scanner->raw_string_hash_count = 0;
  if (length > 0) {
    scanner->raw_string_hash_count = buffer[0];
  }
}

bool tree_sitter_example_external_scanner_scan(
  void *payload,
  TSLexer *lexer,
  const bool *valid_symbols
) {
  Scanner *scanner = payload;

  if (valid_symbols[RAW_STRING_START]) {
    if (lexer->lookahead != 'r') return false;
    lexer->advance(lexer, false);

    uint8_t hash_count = 0;
    while (lexer->lookahead == '#') {
      lexer->advance(lexer, false);
      hash_count++;
    }

    if (lexer->lookahead != '"') return false;
    lexer->advance(lexer, false);

    scanner->raw_string_hash_count = hash_count;
    lexer->result_symbol = RAW_STRING_START;
    return true;
  }

  if (valid_symbols[RAW_STRING_END]) {
    while (!lexer->eof(lexer)) {
      if (lexer->lookahead == '"') {
        lexer->mark_end(lexer);
        lexer->advance(lexer, false);

        uint8_t hash_count = 0;
        while (lexer->lookahead == '#' &&
               hash_count < scanner->raw_string_hash_count) {
          lexer->advance(lexer, false);
          hash_count++;
        }

        if (hash_count == scanner->raw_string_hash_count) {
          lexer->result_symbol = RAW_STRING_END;
          return true;
        }
      } else {
        lexer->advance(lexer, false);
      }
    }
  }

  return false;
}
```

---

## Debugging Tips

Enable debug output in scanner:

```c
#define SCANNER_DEBUG 1

#if SCANNER_DEBUG
  #define LOG(...) fprintf(stderr, "SCANNER: " __VA_ARGS__)
#else
  #define LOG(...)
#endif

bool scan(void *payload, TSLexer *lexer, const bool *valid_symbols) {
  LOG("At '%c' (0x%02x), column %d\n",
      lexer->lookahead >= 32 ? lexer->lookahead : '?',
      lexer->lookahead,
      lexer->get_column(lexer));

  LOG("Valid tokens: ");
  for (int i = 0; i < TOKEN_COUNT; i++) {
    if (valid_symbols[i]) LOG("%d ", i);
  }
  LOG("\n");

  // ... rest of scan logic
}
```

Run with debug output:
```bash
tree-sitter parse file.txt 2>&1 | grep SCANNER
```

---

## Quick Reference Card

| Task | Code |
|------|------|
| Get current character | `lexer->lookahead` |
| Move to next character | `lexer->advance(lexer, false)` |
| Skip whitespace character | `lexer->advance(lexer, true)` |
| Mark token end | `lexer->mark_end(lexer)` |
| Set result token | `lexer->result_symbol = TOKEN_TYPE` |
| Check end of file | `lexer->eof(lexer)` |
| Get column position | `lexer->get_column(lexer)` |
| Check if token valid | `valid_symbols[TOKEN_TYPE]` |
| Allocate memory | `ts_malloc(size)` |
| Free memory | `ts_free(ptr)` |
| Max serialization | `TREE_SITTER_SERIALIZATION_BUFFER_SIZE` |
