# External Scanner Rules

The external scanner (`src/scanner.c`) handles what the grammar alone cannot express. Each
rule here carries its one-line why; the defects and measurements behind them are in
`docs/scanner-design-notes.md`, and the comment at each site in `src/scanner.c` is the other home.

## Scanner State

`ScannerState.depth` counts `#if`/`#endif` nesting: a **`uint32_t`, serialized as 4 bytes**.
It was a `uint8_t` and wrapped at 256 open blocks (silently, the split tokens just stopped);
a `_Static_assert` on `sizeof(depth) >= 4` fails the build if anyone narrows it again.

## Scanner Tokens

| Token | Purpose | Depth Effect |
|-------|---------|-------------|
| `PROPERTY_NAME` | `identifier` followed by `=` (not `:=`) — property/variable disambiguation | none |
| `CONTINUE_AS_IDENTIFIER` | `continue` followed by `:=` `(` `.` `[` `::` `+=` `-=` `*=` `/=` — used as a name, not the statement | none |
| `VAR_ATTRIBUTE_OPEN` | the `[` of a variable attribute (one character, `mark_end` right after it): the lookahead scans past the attribute and any chained `[...]`, then requires a variable name list ending at its `:` (`var_name_list_follows`); otherwise declines and the `[` is a procedure `attribute_item` | none |
| `PREPROC_OPEN` | `#if` | depth++ |
| `PREPROC_CLOSE` | `#endif` | depth-- |
| `BEGIN_KEYWORD` | `begin` at any depth — named node for queries | none |
| `END_KEYWORD` | `end` at any depth — named node for queries | none |
| `PREPROC_SPLIT_BEGIN` | `begin` at depth > 0, immediately before `#endif` — split detection | none |
| `PREPROC_SPLIT_END` | `end` at depth > 0, followed by `;` then `#elif`/`#else`/`#endif` — split detection | none |
| `CALC_FORMULA_PROPERTY_NAME` | `CalcFormula` followed by `=` — keyed by name; falls back to `PROPERTY_NAME` where the grammar does not offer it | none |
| `ML_PROPERTY_NAME` | one of the compiler's 13 ML names (`ML_PROPERTY_NAMES` in `scanner.c`, never a suffix match) followed by `=` (B4); same fallback | none |
| `NAMESPACES_PROPERTY_NAME` | `Namespaces` followed by `=` (B4); same fallback | none |
| `TABLE_RELATION_PROPERTY_NAME` | `TableRelation` followed by `=` (whole word; `ValidateTableRelation` stays `WORD_OTHER`) (B5); same fallback | none |
| `LINK_PROPERTY_NAME` | one of the six link-family names (`LINK_PROPERTY_NAMES` in `scanner.c`: `ColumnFilter`, `DataItemLink`, `DataItemTableFilter`, `LinkFields`, `RunPageLink`, `SubPageLink`; never a suffix match) followed by `=` (B5b); same fallback | none |
| `DIRECTIVE_EOL` | the ONE `\n` ending an `#if`/`#elif` line, after skipping every extra-space character except `\n` (`is_extra_space`), hidden `_directive_eol`. Valid alone, so it returns without trying other tokens. A lexical newline took the LAST of a run of blank lines; skipping only space and tab left `\f\n` a hidden MISSING | none |
| `NEGATIVE_INTEGER` / `NEGATIVE_DECIMAL` | `-1` / `-1.5` as one signed literal, emitted only when `;` `,` `#` or EOF follows; otherwise declines and `-` is unary minus (as lexical tokens `Visible = -1 < X;` ERRORed). Only a `-` commits the block | none |
| `MALFORMED_DIRECTIVE` | hidden `_malformed_directive`, in **no** grammar rule, emitted unasked for a `#` line alc rejects (AL0621 not a directive, AL0631 trailing text or block comment, AL0629 incomplete condition): the line becomes an ERROR (B2/B3). A directive after code on the same line (AL0620) is NOT caught (deferred item 26) | none |
| `SCANNER_HOOK` | hidden `_scanner_hook`, in `extras`, **never emitted**. Exists only so every parse state has a valid external token and calls the scanner, so the `#` gatekeeper sees every directive line. **Never return it** | none |

**Scan function order:** error recovery guard → DIRECTIVE_EOL → NEGATIVE_INTEGER/DECIMAL → the
`#` dispatch (PREPROC_OPEN / PREPROC_CLOSE / MALFORMED_DIRECTIVE) → VAR_ATTRIBUTE_OPEN →
identifier dispatch (`BEGIN_KEYWORD` | `PREPROC_SPLIT_BEGIN` | `END_KEYWORD` |
`PREPROC_SPLIT_END` | the five keyed property names / `PROPERTY_NAME` | `CONTINUE_AS_IDENTIFIER`).
`VAR_ATTRIBUTE_OPEN` runs **before** the identifier tokens: after them, a leading `b` was
absorbed into a following `[`.

## Single-Read Identifier Dispatch

**Every identifier-initial token is decided in ONE scan over ONE read of the word.** Eleven
tokens compete for the same text and cannot be sequential blocks that each do their own read,
for two reasons that each produced live bugs:

- A scan that returns false **discards every advance and is not re-entered at the same
  position**, so a block that reads, fails and declines destroys every later block's chance.
- A walking matcher stops at the first mismatch **with the matched prefix already consumed**,
  so the next branch starts mid-identifier (`b1 = 5;` lost its property; `#iendif` parsed as `#endif`).

```c
enum IdentifierWord word = read_identifier_word(lexer);  // ONE read, into a buffer
lexer->mark_end(lexer);                                  // pin the token to the word
// then classify: the split tokens get first refusal at depth > 0,
// BEGIN_KEYWORD / END_KEYWORD are the fallback at EVERY depth.
```

`mark_end` before any lookahead is what makes the fallback safe: a failed lookahead is not a
failed scan, `begin` is still a `begin`. **Nothing in this scanner matches a keyword against
the live lexer; do not reintroduce anything that does.** Every word goes through
`read_word_ci` into a buffer and is compared whole (`word_in`); the buffer is sized to the
longest word tested, and a longer word is `WORD_OTHER`.

The keyed property names are emitted in the order CalcFormula → ML → Namespaces →
TableRelation → Link → generic `PROPERTY_NAME` → decline, each only if `valid_symbols` offers
it. **Every keyed token must be added to all three guards that list them** (the error-recovery
all-valid guard, the identifier-dispatch entry guard, the property-block entry guard); missing
one leaves the token unreachable in some states, and each of B4, B5 and B5b needed all three.

**Do not assert that two symbols are never co-valid without reading
`ts_external_scanner_states` in `src/parser.c`**: that table is the exhaustive universe of
`valid_symbols` combinations, and reasoning about it instead has been wrong every time.

## The `#` dispatch is the gatekeeper

`#elif`, `#else` and the five directive extras stay grammar regexes (making them external
tokens was measured at +60% states and +70% parser.c). A regex cannot refuse a prefix or a
trailing token, so the dispatch reads every `#` word once, calls `mark_end`, checks the rest of
the line, and either claims a malformed line as `MALFORMED_DIRECTIVE` or declines a well-formed
line to its regex. **Two `#` conventions, do not mix them:** `peek_directive_ci_skip_extras`
takes BARE directive words and consumes the `#` itself; the `PREPROC_OPEN`/`PREPROC_CLOSE`
dispatch advances past `#` manually before reading its word.

`SCANNER_HOOK` makes the gatekeeper run in every state (before it, a quarter of the states
never called the scanner and `#elsebegin` parsed clean). It costs ~5% on incremental parses
(every leaf reuse now needs an exact lex-mode match). **It cannot change a tree, and must stay
that way:** never return it, and keep every other emitted token guarded by `valid_symbols`
(only `MALFORMED_DIRECTIVE` is emitted unasked, and only for lines alc rejects).

Error recovery after a malformed line is wide on purpose: the ERROR is visible and on the
right line, and narrowing it would add scanner state for input alc already rejects.

## Transparent Extras

Every lookahead must step over everything `grammar.js` declares as `extras`, comments
included: a lookahead that stops on an extra does not always produce an ERROR (a
`PREPROC_SPLIT_END` that failed on a trailing comment reparsed as a clean `call_statement`).
Helpers: `skip_comment` (returns false for a bare `/`), `skip_whitespace_and_comments`,
`peek_directive_ci_skip_extras(lexer, targets)` with `TRANSPARENT_DIRECTIVES` = `pragma`,
`region`, `endregion`, `define`, `undef`, and `var_name_list_follows`, which parses directive
lines itself. **Keep `TRANSPARENT_DIRECTIVES` in sync with the `extras` array.**

## `var_name_list_follows` (B7b-1)

`VAR_ATTRIBUTE_OPEN`'s recognizer: after the attribute(s) it reads names, commas and
`#if`/`#elif`/`#else`/`#endif` lines and accepts only at a `:` at local depth 0 with a name
seen and no comma just before; it declines at `(`, `;`, `{`, `}`, `[`, EOF, the word
`procedure`, a `:` inside a group, a malformed directive, so a procedure attribute before a
conditional header stays a procedure attribute. It uses a local nesting count, never
`ScannerState.depth`, and every advance is non-marking. Its declines on input alc accepts are
`docs/deferred-work.md` item 45; the full shape is in `docs/scanner-design-notes.md`.

## PROPERTY_NAME Token

When the parser state allows both properties and variables, the scanner reads the identifier,
skips whitespace, and emits `PROPERTY_NAME` iff the next char is `=` and not part of `:=` or
`==`; otherwise it declines and the grammar reads an `identifier`. **`PROPERTY_NAME` must never
be in `valid_symbols` inside `var_section` or statement contexts**; the grammar ensures this
because properties appear only in object/section bodies.

## Adding Scanner Features

1. Add the token to the `TokenType` enum in `src/scanner.c` and to `externals` in `grammar.js` (same order).
2. Implement the lookahead inside the existing dispatch (one read, `mark_end`, then classify); never a new sequential block.
3. Add the token to every guard that lists its siblings.
4. Create grammar rules using the token; test with edge cases, including a `has_error` check if the token is hidden.

## Debugging

`#define SCANNER_DEBUG 1` in `src/scanner.c`, then trace `valid_symbols` at the lookahead:
```c
if (SCANNER_DEBUG) {
    fprintf(stderr, "SCANNER: valid_symbols PROPERTY_NAME=%d CONTINUE=%d at '%c'\n",
            valid_symbols[PROPERTY_NAME], valid_symbols[CONTINUE_AS_IDENTIFIER],
            (char)lexer->lookahead);
}
```
