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
| `BEGIN_KEYWORD` | `begin` at any depth — named node for queries | none |
| `END_KEYWORD` | `end` at any depth — named node for queries | none |
| `PREPROC_SPLIT_BEGIN` | `begin` at depth > 0, immediately before `#endif` — split detection | none |
| `PREPROC_SPLIT_END` | `end` at depth > 0, followed by `;` then `#else`/`#endif` — split detection | none |

**Scan function order:** error recovery guard → PREPROC_OPEN/CLOSE → 'begin' dispatch (PREPROC_SPLIT_BEGIN | BEGIN_KEYWORD) → 'end' dispatch (PREPROC_SPLIT_END | END_KEYWORD) → VAR_ATTRIBUTE_OPEN → CONTINUE_AS_IDENTIFIER → PROPERTY_NAME

## Single-Scan Dispatch (begin/end)

`BEGIN_KEYWORD` and `PREPROC_SPLIT_BEGIN` compete for the same text, so they **must** be decided inside one scan. A scan that returns false discards every advance it made and the scanner is not re-entered at the same position — so a split block that reads `begin`, fails its lookahead and declines destroys `BEGIN_KEYWORD`'s only chance to fire.

```c
if (valid_symbols[BEGIN_KEYWORD] || valid_symbols[PREPROC_SPLIT_BEGIN]) {
  skip_whitespace(lexer);
  if (read_keyword_ci(lexer, "begin")) {
    lexer->mark_end(lexer);              // pin the token to 'begin'
    if (state->depth > 0 && valid_symbols[PREPROC_SPLIT_BEGIN] &&
        peek_directive_ci_skip_extras(lexer, DIRECTIVE_ENDIF)) { ... SPLIT ... }
    if (valid_symbols[BEGIN_KEYWORD]) { ... BEGIN_KEYWORD ... }
    return false;
  }
  if (state->depth > 0 && valid_symbols[PREPROC_SPLIT_BEGIN]) return false;
}
```

The split token gets first refusal at depth > 0; the named keyword is the fallback at every depth. A failed lookahead is not a failed scan — `begin` is still a `begin`. `mark_end` before the lookahead is what makes the fallback safe, since the lookahead advances well past the keyword.

The `end` dispatch is the same shape with `DIRECTIVE_ELSE_ENDIF` and the `;` check.

Before 3.4.0 these were separate blocks and `BEGIN_KEYWORD`/`END_KEYWORD` were guarded by `state->depth == 0`, so a complete `begin … end` inside any `#if` block fell through to an anonymous `kw('begin')` — a `token(PATTERN)`, which tree-sitter renders as a hidden `aux_sym_*` symbol. The keyword was lexed and then dropped from the tree entirely.

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
