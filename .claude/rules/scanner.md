# External Scanner Rules

The external scanner (`src/scanner.c`) handles patterns that can't be expressed in JavaScript grammar alone.

## Scanner State

The scanner maintains a `ScannerState` holding a `depth` counter tracking `#if`/`#endif` nesting. `depth` is a **`uint32_t`, serialized as 4 bytes**.

**It was a `uint8_t` until 4.0.0, and that wrapped.** At exactly 256 simultaneously-open `#if` blocks the counter returned to 0, the scanner believed it was at top level, and the split-construct tokens stopped being offered — measured as a `call_statement` plus 258 ERROR/MISSING nodes at 255 enclosing blocks, while 254 and 256 were clean. Real AL comes nowhere near this (BC.History's deepest nesting across 15,358 files is **3**), but the failure was silent-ish and cost nothing to remove. A `_Static_assert` on `sizeof(depth) >= 4` fails the build if anyone narrows it again.

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
| `PREPROC_SPLIT_END` | `end` at depth > 0, followed by `;` then `#elif`/`#else`/`#endif` — split detection | none |

**Scan function order:** error recovery guard → PREPROC_OPEN/CLOSE → VAR_ATTRIBUTE_OPEN → identifier dispatch (`BEGIN_KEYWORD` | `PREPROC_SPLIT_BEGIN` | `END_KEYWORD` | `PREPROC_SPLIT_END` | `PROPERTY_NAME` | `CONTINUE_AS_IDENTIFIER`)

`VAR_ATTRIBUTE_OPEN` runs **before** the identifier tokens, not after — it did not until 4.0.0, and the old order is why a leading `b` was absorbed into a following `[`, producing a two-column `[` token whose text was `b[`.

## Single-Read Identifier Dispatch

**Every identifier-initial token is decided in ONE scan over ONE read of the identifier.** Six tokens compete for the same text — `BEGIN_KEYWORD`, `END_KEYWORD`, their two `PREPROC_SPLIT_*` competitors, `PROPERTY_NAME` and `CONTINUE_AS_IDENTIFIER` — and they cannot be sequential blocks that each do their own read.

Two independent reasons, both of which produced live bugs:

- A scan that returns false **discards every advance and is not re-entered at the same position**, so a block that reads text, fails and declines destroys every later block's only chance to fire.
- `read_keyword_ci` stops at the first mismatching character **with the matched prefix already consumed**, and there is no backtracking inside a scan, so the next branch starts *mid-identifier*.

The second is how `b1 = 5;` lost its property: the `begin` attempt ate the `b`, then `PROPERTY_NAME`'s `is_identifier_start` check saw `1` and declined — while `x1 = 5;` in the same position parsed as a property. Parse states 20 and 22 offer `property_name` and `begin_keyword` together, so the two are genuinely co-valid. **Do not assert that two symbols are never co-valid without reading `ts_external_scanner_states` in `src/parser.c`** — that table is the exhaustive universe of `valid_symbols` combinations, it is cheap to read, and reasoning about it instead has been wrong every time.

The shape:

```c
enum IdentifierWord word = read_identifier_word(lexer);  // ONE read, into a buffer
lexer->mark_end(lexer);                                  // pin the token to the word
// then classify: the split tokens get first refusal at depth > 0,
// BEGIN_KEYWORD / END_KEYWORD are the fallback at EVERY depth.
```

`read_identifier_word` returns `WORD_NOT_IDENTIFIER` when the lookahead cannot start an identifier and `WORD_OTHER` when the word is longer than the longest keyword tested (`continue`, 8 chars). `mark_end` before any lookahead is what makes the fallback safe, since the lookaheads advance well past the word.

A failed lookahead is not a failed scan — `begin` is still a `begin`.

Before 4.0.0 `BEGIN_KEYWORD`/`END_KEYWORD` were additionally guarded by `state->depth == 0`, so a complete `begin … end` inside any `#if` block fell through to an anonymous `kw('begin')` — a `token(PATTERN)`, which tree-sitter renders as a hidden `aux_sym_*` symbol. The keyword was lexed and then dropped from the tree entirely.

**Two different `#` conventions, do not mix them.** `peek_directive_ci_skip_extras` takes BARE directive words and consumes the `#` itself; the `PREPROC_OPEN`/`PREPROC_CLOSE` dispatch advances past `#` manually before reading its word.

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
