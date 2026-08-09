# External Scanner Rules

The external scanner (`src/scanner.c`) handles patterns that can't be expressed in JavaScript grammar alone.

## Scanner State

The scanner maintains a 1-byte `ScannerState` with a `depth` counter (uint8_t) tracking `#if`/`#endif` nesting. Serialized as 1 byte via lifecycle functions.

## Scanner Tokens

| Token | Purpose | Depth Effect |
|-------|---------|-------------|
| `PROPERTY_NAME` | `identifier` followed by `=` (not `:=`) — property/variable disambiguation | none |
| `CONTINUE_AS_IDENTIFIER` | `continue` followed by `:=` — used as variable name | none |
| `PREPROC_OPEN` | `#if` — with string literal fallback in grammar | depth++ |
| `PREPROC_CLOSE` | `#endif` — with string literal fallback in grammar | depth-- |
| `BEGIN_KEYWORD` | `begin` at depth 0 — named node for queries | none |
| `END_KEYWORD` | `end` at depth 0 — named node for queries | none |
| `PREPROC_SPLIT_BEGIN` | `begin` at depth > 0, immediately before `#endif` — split detection | none |
| `PREPROC_SPLIT_END` | `end` at depth > 0, followed by `;` then `#else`/`#endif` — split detection | none |

**Scan function order:** error recovery guard → PREPROC_OPEN/CLOSE → BEGIN_KEYWORD → END_KEYWORD → PREPROC_SPLIT_BEGIN → PREPROC_SPLIT_END → VAR_ATTRIBUTE_OPEN → CONTINUE_AS_IDENTIFIER → PROPERTY_NAME

## Transparent Extras

Every lookahead must step over everything `grammar.js` declares as `extras` — comments included, not just directives. Three helpers own this:

- `skip_comment` — consumes a `//` or `/* */` comment. Consumes the leading `/` either way; returns false for a bare `/` so callers that can't tolerate one decline.
- `skip_whitespace_and_comments` — whitespace plus comments.
- `peek_directive_ci_skip_extras(lexer, targets)` — skips whitespace, comments and transparent directive lines, then tests whether the next `#` directive is one of `targets` (bare words, no `#`). `TRANSPARENT_DIRECTIVES` = `pragma`, `region`, `endregion`, `define`, `undef`. **Keep it in sync with the `extras` array.**

**Never match candidate keywords in sequence in a lookahead.** Consuming `#` is irreversible within one scan, and so is consuming a shared prefix. `read_keyword_ci(lexer,"else") || read_keyword_ci(lexer,"endif")` burns the `e` on the failed `else` attempt and makes the `endif` arm permanently unreachable — that bug was live in `PREPROC_SPLIT_END`. Read the directive word into a buffer ONCE, then compare against every target.

A lookahead that stops on an extra does not always produce an ERROR node. `PREPROC_SPLIT_END` failing on a trailing comment let the run reparse as a `call_statement` with a clean error count, invisible to `parse-al-parallel.sh` and `validate-grammar.sh`. Add a corpus fixture pinning the node, not just the error count.

## PROPERTY_NAME Token

This is the V2 grammar's key architectural innovation. When the parser state allows both properties and variables, the scanner checks what follows the identifier:

1. Match identifier regex (Unicode-aware)
2. Skip whitespace
3. If next char is `=` and NOT part of `:=` or `==`: emit `PROPERTY_NAME`
4. Otherwise: don't match, let grammar handle as `identifier`

**Critical constraint:** `PROPERTY_NAME` must never be in `valid_symbols` inside `var_section` or statement contexts. The grammar naturally ensures this because properties appear in object/section bodies, not in code blocks.

## Adding Scanner Features

1. Add token to `TokenType` enum in `src/scanner.c`
2. Add token to `externals` array in `grammar.js`
3. Implement lookahead logic in `tree_sitter_al_external_scanner_scan`
4. Create grammar rules using the token
5. Test with edge cases

## Debugging

Enable debug output:
```c
#define SCANNER_DEBUG 1
```

Trace what the parser is asking for:
```c
if (SCANNER_DEBUG) {
    fprintf(stderr, "SCANNER: valid_symbols PROPERTY_NAME=%d CONTINUE=%d at '%c'\n",
            valid_symbols[PROPERTY_NAME],
            valid_symbols[CONTINUE_AS_IDENTIFIER],
            (char)lexer->lookahead);
}
```
