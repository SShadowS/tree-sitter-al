# External Scanner Rules

The external scanner (`src/scanner.c`) handles patterns that can't be expressed in JavaScript grammar alone.

## Scanner State

The scanner maintains a `ScannerState` holding a `depth` counter tracking `#if`/`#endif` nesting. `depth` is a **`uint32_t`, serialized as 4 bytes**.

**It was a `uint8_t` until 4.0.0, and that wrapped.** At exactly 256 simultaneously-open `#if` blocks the counter returned to 0, the scanner believed it was at top level, and the split-construct tokens stopped being offered — measured as a `call_statement` plus 258 ERROR/MISSING nodes at 255 enclosing blocks, while 254 and 256 were clean. Real AL comes nowhere near this (BC.History's deepest nesting across 15,358 files is **3**), but the failure was silent-ish and cost nothing to remove. A `_Static_assert` on `sizeof(depth) >= 4` fails the build if anyone narrows it again.

## Scanner Tokens

| Token | Purpose | Depth Effect |
|-------|---------|-------------|
| `PROPERTY_NAME` | `identifier` followed by `=` (not `:=`) — property/variable disambiguation | none |
| `CONTINUE_AS_IDENTIFIER` | `continue` followed by `:=` `(` `.` `[` `::` `+=` `-=` `*=` `/=` — used as a name, not the statement | none |
| `PREPROC_OPEN` | `#if` — with string literal fallback in grammar | depth++ |
| `PREPROC_CLOSE` | `#endif` — with string literal fallback in grammar | depth-- |
| `BEGIN_KEYWORD` | `begin` at any depth — named node for queries | none |
| `END_KEYWORD` | `end` at any depth — named node for queries | none |
| `PREPROC_SPLIT_BEGIN` | `begin` at depth > 0, immediately before `#endif` — split detection | none |
| `PREPROC_SPLIT_END` | `end` at depth > 0, followed by `;` then `#elif`/`#else`/`#endif` — split detection | none |
| `CALC_FORMULA_PROPERTY_NAME` | `CalcFormula` followed by `=` — the one property keyed by name; falls back to `PROPERTY_NAME` where the grammar does not offer it | none |
| `DIRECTIVE_EOL` | the ONE `\n` ending an `#if`/`#elif` line, after skipping every extra-space character except `\n` (`is_extra_space`: space, tab, `\r`, `\f`, `\v`, U+FEFF), hidden `_directive_eol`. Skipping only space and tab once left `\f\n` and `\r\r\n` a hidden MISSING token that only `has_error` shows. A lexical `/\r?\n/` is also a separator, and longest match took the LAST newline of a run of blank lines; `token.immediate(/[ \t]*\r?\n/)` grew a following comment leftward over the space. Valid alone (or in error recovery), so it returns without trying other tokens | none |
| `NEGATIVE_INTEGER` / `NEGATIVE_DECIMAL` | `-1` / `-1.5` as one signed literal (issue #23), emitted only when `;` `,` `#` or EOF follows (after whitespace and comments); otherwise it declines and `-` lexes as unary minus. As lexical tokens they won by longest match and `Visible = -1 < X;` ERRORed (G7). Only a `-` commits the block | none |
| `MALFORMED_DIRECTIVE` | hidden `_malformed_directive`, in **no** grammar rule. The `#` dispatch emits it for a directive line alc rejects: a word that is not exactly a directive (`#elsewhere`, `#regionX`, `#ifx`; AL0621), anything but spaces and a `//` comment after `#endif`/`#else` (`#endif;`, `#else B`; AL0631), or a block comment on an `#if`/`#elif` line (AL0631). It covers the line up to its last non-space character; the parser has no action for it, so the line becomes an ERROR. Never valid outside error recovery, so it is emitted unasked (B2) | none |
| `SCANNER_HOOK` | hidden `_scanner_hook`, in `extras`, **never emitted**. Exists only so every parse state has a valid external token and therefore calls the scanner, which lets the `#` gatekeeper see every directive line (B2 fix round 1) | none |

**Scan function order:** error recovery guard → DIRECTIVE_EOL → NEGATIVE_INTEGER/DECIMAL → the `#` dispatch (PREPROC_OPEN / PREPROC_CLOSE / MALFORMED_DIRECTIVE; runs whatever is valid) → VAR_ATTRIBUTE_OPEN → identifier dispatch (`BEGIN_KEYWORD` | `PREPROC_SPLIT_BEGIN` | `END_KEYWORD` | `PREPROC_SPLIT_END` | `PROPERTY_NAME` / `CALC_FORMULA_PROPERTY_NAME` | `CONTINUE_AS_IDENTIFIER`)

`VAR_ATTRIBUTE_OPEN` runs **before** the identifier tokens, not after — it did not until 4.0.0, and the old order is why a leading `b` was absorbed into a following `[`, producing a two-column `[` token whose text was `b[`.

## Single-Read Identifier Dispatch

**Every identifier-initial token is decided in ONE scan over ONE read of the identifier.** Seven tokens compete for the same text — `BEGIN_KEYWORD`, `END_KEYWORD`, their two `PREPROC_SPLIT_*` competitors, `PROPERTY_NAME`, `CALC_FORMULA_PROPERTY_NAME` and `CONTINUE_AS_IDENTIFIER` — and they cannot be sequential blocks that each do their own read.

Two independent reasons, both of which produced live bugs:

- A scan that returns false **discards every advance and is not re-entered at the same position**, so a block that reads text, fails and declines destroys every later block's only chance to fire.
- A walking matcher stops at the first mismatching character **with the matched prefix already consumed**, and there is no backtracking inside a scan, so the next branch starts *mid-identifier*.

The second is how `b1 = 5;` lost its property: the `begin` attempt ate the `b`, then `PROPERTY_NAME`'s `is_identifier_start` check saw `1` and declined — while `x1 = 5;` in the same position parsed as a property. Parse states 20 and 22 offer `property_name` and `begin_keyword` together, so the two are genuinely co-valid. **Do not assert that two symbols are never co-valid without reading `ts_external_scanner_states` in `src/parser.c`** — that table is the exhaustive universe of `valid_symbols` combinations, it is cheap to read, and reasoning about it instead has been wrong every time.

The shape:

```c
enum IdentifierWord word = read_identifier_word(lexer);  // ONE read, into a buffer
lexer->mark_end(lexer);                                  // pin the token to the word
// then classify: the split tokens get first refusal at depth > 0,
// BEGIN_KEYWORD / END_KEYWORD are the fallback at EVERY depth.
```

`read_identifier_word` returns `WORD_NOT_IDENTIFIER` when the lookahead cannot start an identifier and `WORD_OTHER` when the word is longer than the longest keyword tested (`calcformula`, 11 chars; it was `continue`, 8, until the CalcFormula token). `mark_end` before any lookahead is what makes the fallback safe, since the lookaheads advance well past the word.

A failed lookahead is not a failed scan — `begin` is still a `begin`.

Before 4.0.0 `BEGIN_KEYWORD`/`END_KEYWORD` were additionally guarded by `state->depth == 0`, so a complete `begin … end` inside any `#if` block fell through to an anonymous `kw('begin')` — a `token(PATTERN)`, which tree-sitter renders as a hidden `aux_sym_*` symbol. The keyword was lexed and then dropped from the tree entirely.

**Two different `#` conventions, do not mix them.** `peek_directive_ci_skip_extras` takes BARE directive words and consumes the `#` itself; the `PREPROC_OPEN`/`PREPROC_CLOSE` dispatch advances past `#` manually before reading its word.

**The `#` dispatch is the gatekeeper for directives it does not emit (B2).** `#elif`, `#else` and the five extras stay grammar regexes, and a regex cannot refuse a prefix (`\b` and lookahead are rejected by the lexer compiler) or a trailing token. So the dispatch reads every `#` word once, calls `mark_end`, checks the rest of the line, and either claims a malformed line as `MALFORMED_DIRECTIVE` or declines a well-formed `#elif`/`#else`/extras line to its regex. Making `#else`/`#elif` external tokens instead was measured: STATE_COUNT 15,870 → 25,301, parser.c 39.6 MB → 67.9 MB. Every directive word is compared whole now, in the dispatch and in the lookaheads (`word_in`); the prefix mode the lookaheads kept to agree with the old `#else`/`#elif` regexes is gone. 

**`SCANNER_HOOK` makes the gatekeeper run in every parse state (B2 fix round 1).** tree-sitter calls the scanner only in states where some external token is valid. Before the hook, 3,937 of 15,870 states had none (77 of the 2,628 states where `#else` is valid, 71 of 2,602 for `#elif`), and `#elsebegin`, `#else /* c */` at NoSeriesSetupImpl.Codeunit.al:199, or `x := Rec.` + `#regionX`, still parsed clean. `_scanner_hook` is an external listed in `extras`, so it is valid in every state, and the scanner **never returns it**; after it, 0 states lack an external lex state. Counted from `src/parser.c`: a state calls the scanner iff its `ts_lex_modes` entry has a non-zero `external_lex_state` (mind the `.reserved_word_set_id` entries); a token is valid in a state iff the large or small parse table has an action on it. Cost: STATE_COUNT unchanged, parser.c +1.9%, `tools.perf ab` over DC at 24 rounds 0.998 (CI 0.991-1.007); a first run gave 0.978 (CI 0.964-0.985). Both warned of a busy machine. **It cannot change a tree, and must stay that way:** never return `SCANNER_HOOK`, and keep every other emitted token guarded by `valid_symbols` (only `MALFORMED_DIRECTIVE` is emitted unasked, and only for lines alc rejects).

**Error recovery after a malformed line is wide, on purpose not narrowed.** The whole line is one invalid token, so the arm structure around it is lost, and in recovery the guard declines every external, so the next `#endif`/`begin`/`end` lex as fragments and the following procedure can be swallowed. The review's alternative (emit the valid word, set a serialized "tail pending" flag, claim only the rest of the line on the next call) adds scanner state and a second token boundary for input alc already rejects; not worth it while the ERROR is visible and on the right line.

## Transparent Extras

Every lookahead must step over everything `grammar.js` declares as `extras` — comments included, not just directives. Three helpers own this:

- `skip_comment` — consumes a `//` or `/* */` comment. Consumes the leading `/` either way; returns false for a bare `/` so callers that can't tolerate one decline.
- `skip_whitespace_and_comments` — whitespace plus comments.
- `peek_directive_ci_skip_extras(lexer, targets)` — skips whitespace, comments and transparent directive lines, then tests whether the next `#` directive is one of `targets` (bare words, no `#`). `TRANSPARENT_DIRECTIVES` = `pragma`, `region`, `endregion`, `define`, `undef`. **Keep it in sync with the `extras` array.**

**Nothing in this scanner matches a keyword against the live lexer. Do not reintroduce anything that does.** Every word — directive names, `begin`/`end`/`continue`, and both split lookaheads — is read ONCE into a buffer via `read_word_ci` and then compared whole.

The walking matcher this replaced (`read_keyword_ci`, deleted in 4.0.0) produced **three separate live defects in this one file**, which is why the tool is gone rather than documented:

- `read_keyword_ci("else") || read_keyword_ci("endif")` in `PREPROC_SPLIT_END` burned the `e` on the failed `else` and made the `endif` arm permanently unreachable.
- A per-keyword `begin` attempt ate the `b` of `b1 = 5;`, so `PROPERTY_NAME` then saw `1` and declined — while `x1 = 5;` in the same position parsed fine.
- **`#iendif` was accepted as `#endif`.** The `PREPROC_OPEN`/`PREPROC_CLOSE` dispatch chained `read_keyword_ci("if")` then `read_keyword_ci("endif")`; on `#iendif` the first matched the `i` before failing, the second read the *remaining* `endif` and returned **true**, yielding `(preproc_close)` over all seven bytes, decrementing `depth`, exit 0, no ERROR node.

Note what did **not** save the `#elif`/`#else` case: the two words differing at character 0 is not the reason. `#elif` genuinely burns a character on the `endif` attempt. It was harmless only because every path out of that block was a `return`, so the burn had no successor — a guarantee that dies the instant a third arm is added, which is exactly how the `else`/`endif` bug entered.

Consuming `#` is likewise irreversible within one scan.

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
