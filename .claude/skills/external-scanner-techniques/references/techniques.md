# Tree-Sitter External Scanner Techniques

A comprehensive guide to external scanner patterns and techniques learned from analyzing 10+ tree-sitter parsers. Use this skill when developing or debugging external scanners for tree-sitter grammars.

## Quick Reference: When to Use Each Pattern

| Scenario | Pattern | Source Parser |
|----------|---------|---------------|
| Context-dependent structures (preprocessor in different contexts) | Pure grammar with helper function | tree-sitter-c |
| Character-level disambiguation only | Stateless scanner with `valid_symbols[]` | tree-sitter-elixir |
| Single parameter across tokens (e.g., delimiter count) | Single-value scanner state | tree-sitter-rust |
| Deep nesting (multiple levels) | Stack-based scanner state | tree-sitter-python |
| Multi-line constructs split by intervening content | Stack + serialization | tree-sitter-bash |
| Implicit block boundaries | Zero-width tokens | tree-sitter-yaml |

## Decision Tree: Do I Need Scanner State?

```
Does the construct need lookahead?
├─ No → Use pure grammar (no scanner needed)
└─ Yes → Does parser state track context via valid_symbols[]?
    ├─ Yes → Stateless scanner (Elixir pattern)
    └─ No → Does the construct nest?
        ├─ No → Single value state (Rust pattern)
        └─ Yes → Does it nest multiply?
            ├─ No (one level) → Single value + serialization
            └─ Yes (multiple) → Stack + serialization (Python/Bash)
```

---

## Pattern 1: Pure Grammar with Helper Function (tree-sitter-c)

**Best for:** Context-specific preprocessor handling, no scanner state needed.

### The Pattern

```javascript
/**
 * Generate preprocessor rules for different contexts
 * @param {string} suffix - Context identifier (e.g., '_in_var_section')
 * @param {function} content - Function returning what can appear in context
 * @param {number} precedence - Optional precedence for conflicts
 */
function preprocIf(suffix, content, precedence = 0) {
    function alternativeBlock($) {
        return choice(
            suffix ? alias($['preproc_else' + suffix], $.preproc_else) : $.preproc_else,
            suffix ? alias($['preproc_elif' + suffix], $.preproc_elif) : $.preproc_elif,
        );
    }

    return {
        ['preproc_if' + suffix]: $ => prec(precedence, seq(
            '#if',
            field('condition', $.preproc_condition),
            repeat(content($)),  // Content varies by context!
            field('alternative', optional(alternativeBlock($))),
            '#endif',
        )),
        ['preproc_else' + suffix]: $ => prec(precedence, seq(
            '#else',
            repeat(content($)),
        )),
        ['preproc_elif' + suffix]: $ => prec(precedence, seq(
            '#elif',
            field('condition', $.preproc_condition),
            repeat(content($)),
            field('alternative', optional(alternativeBlock($))),
        )),
    };
}

// Usage: Generate rules for each context
module.exports = grammar({
    rules: {
        ...preprocIf('', $ => $._top_level_item),
        ...preprocIf('_in_var_section', $ => $.variable_declaration),
        ...preprocIf('_in_properties', $ => $._property),
        ...preprocIf('_in_fields', $ => $.field),
    }
});
```

### Grammar Integration

```javascript
// Use aliasing to normalize parse tree
var_section: $ => seq(
    'var',
    repeat(choice(
        $.variable_declaration,
        alias($.preproc_if_in_var_section, $.preproc_if),  // Aliased!
    )),
),
```

### Why It Works

- Grammar explicitly models what can appear in each context
- Parser's LR state machine naturally knows context
- No state synchronization issues
- No serialization complexity

---

## Pattern 2: Stateless Scanner with valid_symbols[] (tree-sitter-elixir)

**Best for:** Character-level disambiguation where grammar can track context.

### The Pattern

```c
void *tree_sitter_lang_external_scanner_create() { return NULL; }

unsigned tree_sitter_lang_external_scanner_serialize(void *payload, char *buffer) {
    return 0;  // Zero bytes - no state
}

bool tree_sitter_lang_external_scanner_scan(
    void *payload,
    TSLexer *lexer,
    const bool *valid_symbols
) {
    // Parser tells us context via valid_symbols
    if (valid_symbols[QUOTED_CONTENT_DOUBLE]) {
        // Scan double-quoted string content
        return scan_string_content(lexer, '"');
    }
    if (valid_symbols[QUOTED_CONTENT_SINGLE]) {
        // Scan single-quoted string content
        return scan_string_content(lexer, '\'');
    }
    return false;
}
```

### Key Insight

The parser's LR state machine tracks context. Scanner just uses `valid_symbols[]` to know which token type the parser expects.

```c
// Parser is asking: "Is this token X or Y?"
// Scanner answers based on character lookahead
int8_t find_token_type(const bool *valid_symbols) {
    for (int i = 0; i < TOKEN_COUNT; i++) {
        if (valid_symbols[i]) return i;
    }
    return -1;  // No valid token
}
```

---

## Pattern 3: Single-Value State (tree-sitter-rust)

**Best for:** Matching paired delimiters with parameters.

### The Pattern

```c
typedef struct {
    uint8_t opening_hash_count;  // Just one value
} Scanner;

// Scan raw string start: r##"
bool scan_raw_string_start(Scanner *scanner, TSLexer *lexer) {
    if (lexer->lookahead != 'r') return false;
    lexer->advance(lexer, false);

    uint8_t hash_count = 0;
    while (lexer->lookahead == '#') {
        lexer->advance(lexer, false);
        hash_count++;
    }

    if (lexer->lookahead != '"') return false;
    lexer->advance(lexer, false);

    scanner->opening_hash_count = hash_count;  // Store for later
    lexer->result_symbol = RAW_STRING_START;
    return true;
}

// Scan raw string end: "##
bool scan_raw_string_end(Scanner *scanner, TSLexer *lexer) {
    while (lexer->lookahead != 0) {
        if (lexer->lookahead == '"') {
            lexer->mark_end(lexer);
            lexer->advance(lexer, false);

            uint8_t hash_count = 0;
            while (lexer->lookahead == '#' && hash_count < scanner->opening_hash_count) {
                lexer->advance(lexer, false);
                hash_count++;
            }

            if (hash_count == scanner->opening_hash_count) {
                lexer->result_symbol = RAW_STRING_END;
                return true;
            }
        }
        lexer->advance(lexer, false);
    }
    return false;
}

// Serialization: 1 byte
unsigned serialize(Scanner *scanner, char *buffer) {
    buffer[0] = scanner->opening_hash_count;
    return 1;
}
```

---

## Pattern 4: Stack-Based State (tree-sitter-python)

**Best for:** Nested constructs like indentation blocks or nested strings.

### The Pattern

```c
typedef struct {
    Array(uint16_t) indents;      // Stack of indent levels
    Array(Delimiter) delimiters;   // Stack of string delimiters
    bool inside_interpolation;
} Scanner;

// Push new indent level when entering block
void push_indent(Scanner *scanner, uint16_t level) {
    array_push(&scanner->indents, level);
}

// Pop indent level and emit DEDENT
bool check_dedent(Scanner *scanner, TSLexer *lexer, uint16_t current_indent) {
    if (scanner->indents.size == 0) return false;

    uint16_t expected = *array_back(&scanner->indents);
    if (current_indent < expected) {
        array_pop(&scanner->indents);
        lexer->result_symbol = DEDENT;
        return true;
    }
    return false;
}

// Serialization must preserve stack
unsigned serialize(Scanner *scanner, char *buffer) {
    size_t size = 0;

    buffer[size++] = scanner->inside_interpolation;
    buffer[size++] = scanner->delimiters.size;

    for (uint32_t i = 0; i < scanner->delimiters.size; i++) {
        buffer[size++] = scanner->delimiters.contents[i].flags;
    }

    for (uint32_t i = 0; i < scanner->indents.size && size < BUFFER_SIZE - 2; i++) {
        uint16_t indent = scanner->indents.contents[i];
        buffer[size++] = indent & 0xFF;
        buffer[size++] = (indent >> 8) & 0xFF;
    }

    return size;
}
```

---

## Pattern 5: Heredoc/Block Tracking (tree-sitter-bash)

**Best for:** Multi-line constructs with content between open and close.

### The Pattern

```c
typedef struct {
    bool started;
    bool allows_indent;
    String delimiter;  // Dynamic string
} Heredoc;

typedef struct {
    Array(Heredoc) heredocs;  // Stack of open heredocs
} Scanner;

// Priority ordering: check close BEFORE content
bool scan(Scanner *scanner, TSLexer *lexer, const bool *valid_symbols) {
    // PRIORITY 1: Check for heredoc end
    if (valid_symbols[HEREDOC_END] && scanner->heredocs.size > 0) {
        Heredoc *heredoc = array_back(&scanner->heredocs);
        if (at_line_start(lexer) && match_delimiter(lexer, heredoc)) {
            array_pop(&scanner->heredocs);
            lexer->result_symbol = HEREDOC_END;
            return true;
        }
    }

    // PRIORITY 2: Scan heredoc content
    if (valid_symbols[HEREDOC_CONTENT] && scanner->heredocs.size > 0) {
        return scan_heredoc_content(scanner, lexer);
    }

    // PRIORITY 3: Check for heredoc start
    if (valid_symbols[HEREDOC_START]) {
        // ...
    }

    return false;
}
```

### Critical: Serialization of Dynamic Strings

```c
unsigned serialize(Scanner *scanner, char *buffer) {
    size_t size = 0;

    buffer[size++] = scanner->heredocs.size;

    for (uint32_t i = 0; i < scanner->heredocs.size; i++) {
        Heredoc *h = &scanner->heredocs.contents[i];

        buffer[size++] = h->started;
        buffer[size++] = h->allows_indent;

        // Store delimiter length + contents
        uint32_t len = h->delimiter.size;
        memcpy(&buffer[size], &len, sizeof(uint32_t));
        size += sizeof(uint32_t);

        memcpy(&buffer[size], h->delimiter.contents, len);
        size += len;
    }

    return size;
}
```

---

## Pattern 6: Zero-Width Tokens (tree-sitter-yaml)

**Best for:** Marking structural boundaries without consuming input.

### The Pattern

```c
// Mark token boundary at CURRENT position (before advancing)
static inline void mark_end_here(TSLexer *lexer) {
    lexer->mark_end(lexer);  // Token ends here
}

// Emit zero-width block-end token
if (valid_symbols[BLOCK_END] && indent_decreased(scanner)) {
    mark_end_here(lexer);  // Don't advance!
    pop_indent(scanner);
    lexer->result_symbol = BLOCK_END;
    return true;  // Token emitted but no characters consumed
}
```

### Grammar Integration

```javascript
// Zero-width tokens as structural markers
block_sequence: $ => seq(
    $._block_seq_start,
    repeat($._block_seq_entry),
    $._block_end  // Zero-width end marker
),
```

---

## Critical Lessons: Scanner Token Integration

### Token Placement Rules

**DO: Place tokens as alternatives in `choice()`**

```javascript
repeat(choice(
    $.normal_pattern,
    $.scanner_token  // Helps parser choose
))
```

**DON'T: Place tokens after structural boundaries**

```javascript
seq(
    repeat($.normal_pattern),
    optional($.scanner_token)  // TOO LATE - decision already made
)
```

### Why Placement Matters

1. Parser decides to exit `repeat()` BEFORE checking optional elements
2. Wrong placement changes shift/reduce decisions even when scanner returns false
3. Scanner gets called at every position, corrupting parse decisions

### Debug Technique

```c
if (valid_symbols[MY_TOKEN]) {
    fprintf(stderr, "SCANNER: MY_TOKEN valid at '%c' (0x%02x)\n",
            lexer->lookahead >= 32 ? lexer->lookahead : '?',
            lexer->lookahead);
}
```

If scanner is called at unexpected positions (';', identifiers, etc.), token placement is wrong.

---

## Serialization Best Practices

### Buffer Size

- Default: `TREE_SITTER_SERIALIZATION_BUFFER_SIZE = 1024 bytes`
- Always check before writing
- Return 0 on overflow (triggers error recovery)

### Template

```c
unsigned serialize(Scanner *scanner, char *buffer) {
    size_t size = 0;

    // Guard against overflow
    if (size >= TREE_SITTER_SERIALIZATION_BUFFER_SIZE) return 0;

    // Single values: direct assignment
    buffer[size++] = (char)scanner->flag;

    // 16-bit values: memcpy
    if (size + sizeof(uint16_t) > BUFFER_SIZE) return 0;
    memcpy(&buffer[size], &scanner->value, sizeof(uint16_t));
    size += sizeof(uint16_t);

    // Arrays: length prefix + contents
    buffer[size++] = (char)scanner->stack.size;
    for (uint32_t i = 0; i < scanner->stack.size; i++) {
        if (size >= BUFFER_SIZE) return 0;
        buffer[size++] = scanner->stack.contents[i];
    }

    return size;
}

void deserialize(Scanner *scanner, const char *buffer, unsigned length) {
    if (length == 0) {
        // Reset to initial state
        array_clear(&scanner->stack);
        scanner->flag = false;
        return;
    }

    size_t size = 0;
    scanner->flag = buffer[size++];

    memcpy(&scanner->value, &buffer[size], sizeof(uint16_t));
    size += sizeof(uint16_t);

    uint8_t stack_size = buffer[size++];
    array_clear(&scanner->stack);
    for (uint32_t i = 0; i < stack_size && size < length; i++) {
        array_push(&scanner->stack, buffer[size++]);
    }
}
```

---

## Scanner Debugging Techniques

### Enable Debug Output

```c
#define SCANNER_DEBUG 1

#if SCANNER_DEBUG
    #define DEBUG_LOG(...) fprintf(stderr, __VA_ARGS__)
#else
    #define DEBUG_LOG(...)
#endif
```

### Trace valid_symbols

```c
bool scan(Scanner *scanner, TSLexer *lexer, const bool *valid_symbols) {
    DEBUG_LOG("SCANNER: valid=[");
    for (int i = 0; i < TOKEN_COUNT; i++) {
        if (valid_symbols[i]) DEBUG_LOG("%d,", i);
    }
    DEBUG_LOG("] lookahead='%c'\n", lexer->lookahead);
    // ...
}
```

### Trace State Changes

```c
DEBUG_LOG("STATE: before push stack.size=%d\n", scanner->stack.size);
array_push(&scanner->stack, value);
DEBUG_LOG("STATE: after push stack.size=%d\n", scanner->stack.size);
```

### Common Issues and Solutions

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| Scanner called at wrong positions | Token in `optional()` after `repeat()` | Move to `choice()` inside `repeat()` |
| State lost between calls | Missing/broken serialization | Verify serialize/deserialize roundtrip |
| Keywords not matching | Case sensitivity | Use `tolower()` or case-insensitive compare |
| Infinite loops | Not advancing lexer | Ensure `lexer->advance()` called |
| Parser ignores scanner token | Token not in grammar | Add to `externals` and grammar rules |

---

## Reference: Array Helpers

Tree-sitter's array implementation (from `tree_sitter/array.h`):

```c
// Declare array type
Array(Type) my_array;

// Initialize
array_init(&my_array);

// Add element
array_push(&my_array, value);

// Get element
Type *elem = array_get(&my_array, index);

// Get last element
Type *last = array_back(&my_array);

// Remove last element
array_pop(&my_array);

// Clear array
array_clear(&my_array);

// Free memory
array_delete(&my_array);
```

---

## Related Files in This Project

- `EXTERNAL_SCANNER_RESEARCH.md` - Detailed research on Elixir/Python/Rust/C scanners
- `SCANNER_RESEARCH_SUMMARY.md` - Executive summary of findings
- `BASH_HEREDOC_LESSONS_SUMMARY.md` - Bash heredoc pattern deep dive
- `YAML_SCANNER_RESEARCH.md` - Zero-width token analysis
- `SCANNER_TOKEN_INTEGRATION_LESSONS.md` - Critical integration pitfalls
- `SCANNER_BLOCK_TRACKING_IMPLEMENTATION.md` - Implementation guide
- `PREPROC_HELPER_PATTERN.md` - C-style grammar helper function

---

## Summary: Choose the Right Pattern

1. **Start with pure grammar** - No scanner if context-specific rules work
2. **Use stateless scanner** if `valid_symbols[]` provides needed context
3. **Use single-value state** for simple delimiter matching
4. **Use stack state** for nested constructs
5. **Always serialize** if you have any state
6. **Place tokens at decision points** in `choice()`, not after `repeat()`
7. **Check close before content** in priority ordering
8. **Zero-width tokens** for structural boundaries without input consumption
