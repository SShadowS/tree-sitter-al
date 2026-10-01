# AL conditional-directive semantics (compiler-verified)

Established with `alc` on 2026-09-27 by `python -m tools.config_oracle.probe_alc --check`.
Every row is one or more probes in `PROBES`. Re-run the probe before relying on a row
after a compiler upgrade. The configuration-consistency oracle's resolver
(`tools/config_oracle/directives.py`) implements exactly this table; its tests are
derived from it, never from its own output.

Method: text that must be inactive is `GARBAGE!!`. alc does not parse inactive
text, so a probe compiles iff the compiler chose exactly the predicted arms. Each
positive probe has a control that must fail.

## Conditions

| Question | Answer | Probes |
|---|---|---|
| Are symbols case-sensitive? | **Yes**, both `preprocessorSymbols` and `#define`d symbols | `symbol_case_*`, `defined_symbol_case_sensitive` |
| Operators | `and`, `or`, `not`, parentheses. Keywords are case-insensitive (`AND`, `NOT`) | `and_*`, `or_*`, `not_*`, `paren_true` |
| Rejected operators | `&&`, `\|\|`, `xor` (AL0631); `!`, `==` (AL0629). The grammar dropped `&&`/`\|\|` in B2 (2026-10-01): they are now an ERROR in the condition | `*_rejected` |
| Precedence | `not` > `and` > `or`. The grammar encodes it since B1 (`preproc_not_expression` is `prec(3)`), pinned by `test/corpus/preproc_condition_precedence_test.txt`; the config oracle's condition-structure stage checks the tree's grouping against the resolver per configuration | `prec_*` |
| Literals | `true`, `false`, case-insensitive | `*_literal` |
| Malformed | empty condition, two operands with no operator, `#elif` with no condition: rejected | `two_words_rejected`, `empty_condition_rejected`, `elif_without_condition_rejected` |
| A condition left incomplete at the end of its line (`#if A and` / `B`, `#if not` / `A`, `#elif A or` / `B`, `#if A and // c` / `B`, `#if (A and` / `B)`), or empty with the operand on the next line (`#if` / `A`, `#if // c` / `A`, `#elif` / `A`) | Rejected (AL0629), with every symbol defined: the next line is never read as the operand. A stray `)` (`#if A)`) is AL0631. One-line forms, and a `(` inside the trailing `//` comment, are accepted. The parser makes the line an ERROR since B3 (2026-10-01) | `dangling_*_rejected`, `unbalanced_*_paren_rejected`, `empty_*_next_line_rejected`, `one_line_and_control`, `paren_one_line_comment_paren_control`, `symbol_band_control` |
| Symbol shape | `[A-Za-z_][A-Za-z0-9_]*` (digits and `_` allowed) | `digit_symbol`, `underscore_symbol` |
| A symbol spelled like an operator (`and`) | **Not established**: the probe did not discriminate. The resolver fails closed | — |

## Arms

| Question | Answer | Probes |
|---|---|---|
| `#elif` | First true arm wins; later true arms are inactive | `elif_*` |
| Nested arm no assignment selects | Legal; simply never active | `nested_unreachable_arm` |
| An arm holding only a binary operator, the operand after `#endif` (`i := 1 #if X + #endif 2;`) | Legal with X defined (`1 + 2`), rejected without it (`1 2`, AL0104/AL0111), split and flat. The parser takes it since B3 as the operator-only form of `preproc_conditional_expression_tail` | `tools/alc_probe/cases/oracle-negative/split-operator.al` |

## Directive lines

| Question | Answer | Probes |
|---|---|---|
| Directive after code on the same line | Rejected (AL0620): a directive must be the first token on its line | `*_after_code_rejected` |
| Whitespace | Leading indentation and spaces/tabs between `#` and the word are allowed | `space_after_hash`, `tab_after_hash`, `indented_directives` |
| Directive word case | Case-insensitive (`#IF`, `#ELSE`, `#ENDIF`) | `upper_directive_words` |
| Trailing `//` comment on `#if`, `#elif`, `#else`, `#endif` | Allowed | `line_comment_on_if_else_endif`, `elif_trailing_line_comment` |
| Trailing `/* */` comment on a directive | Rejected (AL0631), on `#if` and `#elif` lines too | `block_comment_on_*_rejected` |
| A second directive on an `#if`/`#elif` line (`#if A #region R`, `#if A #pragma …`, `#elif A #region R`) | Rejected (AL0631); a `#` inside the line's trailing `//` comment is allowed. The parser makes it an ERROR since B2 fix round 2 | `if_then_region_rejected`, `if_then_pragma_rejected`, `elif_then_region_rejected`, `if_line_comment_with_hash_accepted` |
| Extra token after `#else` or `#endif` (`#else B`, `#else;`, `#endif;`, `#endif X`) | Rejected (AL0631) | `else_trailing_word_rejected`, `else_semicolon_rejected`, `endif_semicolon_rejected`, `endif_trailing_word_rejected` |
| Extra token after `#endregion` (`#endregion;`) | Allowed: region lines take free text | `endregion_semicolon_accepted` |
| A directive word with more word characters after it (`#ifx`, `#endifx`, `#elsex`, `#elsewhere`, `#elifx`, `#regionx`, `#endregionx`, `#pragmax`, `#definex`, `#undefx`) | Rejected (AL0621): the word is matched whole | `prefix_*_rejected` |
| `#endif` as the last line with no newline after it | Allowed | `endif_at_eof_no_newline` |

**What the parser does with these (B2, 2026-10-01).** These rejected forms are an ERROR on
their line: a directive word with more word characters after it, anything but a `//`
comment after `#else`/`#endif`, and a block comment or a second directive (`#if A #region
R`, probes `if_then_*_rejected`, `elif_then_region_rejected`) on an `#if`/`#elif` line.
**Not covered:** a directive after code on the same line (AL0620, the first row of
this table) still parses clean, tracked as `docs/deferred-work.md` item 26. (`&&`/`||`
are an ERROR too, inside the condition, because the grammar no longer has them.) The
scanner's `#` dispatch (`src/scanner.c`) reads
the directive word once and checks the rest of the line; a malformed line becomes the
hidden external token `_malformed_directive`, which no grammar rule takes. For the covered
forms this holds in every parse state: the never-emitted extra `_scanner_hook` makes
tree-sitter call the scanner everywhere. Until B2 most of
these parsed with zero ERROR nodes (`#elsewhere` as `#else` plus an identifier, `#endif;`
as `#endif` plus an empty statement). Fixtures:
`test/corpus/directive_line_rejected_negative_test.txt` and
`test/corpus/directive_line_accepted_test.txt`. The table is still the resolver's
contract: `tools/config_oracle/directives.py` refuses the same lines
(`resolver:unknown-directive`, `resolver:trailing-token`,
`resolver:block-comment-on-directive`, `resolver:unsupported-condition-token`).

**B3 (2026-10-01): incomplete conditions.** The same check on an `#if`/`#elif` line
(`opener_line_is_malformed`, one pass over the rest of the line) also refuses a line whose
last condition word before any `//` is `and`, `or` or `not`, that has no condition word at
all, or whose parentheses do not balance (the Conditions table's "incomplete at the end of its line" row). Before B3 the
condition grammar simply continued across the newline and `#if A and` / `B` parsed clean as
`A and B`. Fixture: `test/corpus/preproc_dangling_operator_negative_test.txt`. The resolver
refuses the same lines (`resolver:unsupported-condition`).

## Lexing

| Question | Answer | Probes |
|---|---|---|
| Inactive text | **Not lexed.** An unterminated `'` or `/*` in an inactive arm does not hide the next directive | `unterminated_*_inactive` |
| Active text | Lexed normally; an unterminated `'` in active text is an error | `unterminated_quote_active_control` |
| `#if` inside an active block comment, line comment, or multi-line verbatim string `@'…'` | Not a directive | `if_inside_*` |

## Symbol definition

| Question | Answer | Probes |
|---|---|---|
| `#define` inside an inactive arm | No effect | `define_in_inactive_arm_no_effect` |
| `#define` inside an active arm | Takes effect for later directives | `define_in_active_arm_effect` |
| `#undef` of a symbol set by `preprocessorSymbols` | Removes it | `undef_removes_assigned_symbol` |

Placement rules for `#define`/`#undef` (before the first token) are in
`docs/preproc-define-undef.md`; they are a linter concern, not the resolver's.
