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
| Rejected operators | `&&`, `\|\|`, `xor` (AL0631); `!`, `==` (AL0629) | `*_rejected` |
| Precedence | `not` > `and` > `or`. The grammar encodes it since B1 (`preproc_not_expression` is `prec(3)`), pinned by `test/corpus/preproc_condition_precedence_test.txt`; the config oracle's condition-structure stage checks the tree's grouping against the resolver per configuration | `prec_*` |
| Literals | `true`, `false`, case-insensitive | `*_literal` |
| Malformed | empty condition, two operands with no operator, `#elif` with no condition: rejected | `two_words_rejected`, `empty_condition_rejected`, `elif_without_condition_rejected` |
| Symbol shape | `[A-Za-z_][A-Za-z0-9_]*` (digits and `_` allowed) | `digit_symbol`, `underscore_symbol` |
| A symbol spelled like an operator (`and`) | **Not established**: the probe did not discriminate. The resolver fails closed | — |

## Arms

| Question | Answer | Probes |
|---|---|---|
| `#elif` | First true arm wins; later true arms are inactive | `elif_*` |
| Nested arm no assignment selects | Legal; simply never active | `nested_unreachable_arm` |

## Directive lines

| Question | Answer | Probes |
|---|---|---|
| Directive after code on the same line | Rejected (AL0620): a directive must be the first token on its line | `*_after_code_rejected` |
| Whitespace | Leading indentation and spaces/tabs between `#` and the word are allowed | `space_after_hash`, `tab_after_hash`, `indented_directives` |
| Directive word case | Case-insensitive (`#IF`, `#ELSE`, `#ENDIF`) | `upper_directive_words` |
| Trailing `//` comment on `#if`, `#elif`, `#else`, `#endif` | Allowed | `line_comment_on_if_else_endif`, `elif_trailing_line_comment` |
| Trailing `/* */` comment on a directive | Rejected (AL0631) | `block_comment_on_*_rejected` |
| Extra token after `#else` | Rejected (AL0631) | `else_trailing_word_rejected` |

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
