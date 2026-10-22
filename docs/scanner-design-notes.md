# External scanner: design notes and the defects behind the rules

Carried out of `.claude/rules/scanner.md` on 2026-10-21. That file keeps each rule with a
one-line why; this is the record of the measurements and the live defects that produced
them. The scanner is `src/scanner.c`.

## The depth counter wrapped at 256

`ScannerState.depth` was a `uint8_t` until 4.0.0. At exactly 256 simultaneously-open `#if`
blocks the counter returned to 0, the scanner believed it was at top level, and the
split-construct tokens stopped being offered: measured as a `call_statement` plus 258
ERROR/MISSING nodes at 255 enclosing blocks, while 254 and 256 were clean. Real AL comes
nowhere near this (BC.History's deepest nesting across 15,358 files is **3**), but the failure
was silent-ish and cost nothing to remove. It is now a `uint32_t`, serialized as 4 bytes, and
a `_Static_assert` on `sizeof(depth) >= 4` fails the build if anyone narrows it again.

## The walking keyword matcher and its three defects

`read_keyword_ci` matched a keyword against the live lexer character by character. A walking
matcher stops at the first mismatching character **with the matched prefix already consumed**,
and there is no backtracking inside a scan, so the next branch starts mid-identifier. It
produced three separate live defects in one file, which is why the tool was deleted in 4.0.0
rather than documented:

- `read_keyword_ci("else") || read_keyword_ci("endif")` in `PREPROC_SPLIT_END` burned the `e`
  on the failed `else` and made the `endif` arm permanently unreachable.
- A per-keyword `begin` attempt ate the `b` of `b1 = 5;`, so `PROPERTY_NAME` then saw `1` and
  declined, while `x1 = 5;` in the same position parsed fine. Parse states 20 and 22 offered
  `property_name` and `begin_keyword` together, so the two were genuinely co-valid.
- **`#iendif` was accepted as `#endif`.** The `PREPROC_OPEN`/`PREPROC_CLOSE` dispatch chained
  `read_keyword_ci("if")` then `read_keyword_ci("endif")`; on `#iendif` the first matched the
  `i` before failing, the second read the *remaining* `endif` and returned **true**, yielding
  `(preproc_close)` over all seven bytes, decrementing `depth`, exit 0, no ERROR node.

Note what did **not** save the `#elif`/`#else` case: the two words differing at character 0 is
not the reason. `#elif` genuinely burns a character on the `endif` attempt. It was harmless
only because every path out of that block was a `return`, so the burn had no successor, a
guarantee that dies the instant a third arm is added, which is exactly how the `else`/`endif`
bug entered. Consuming `#` is likewise irreversible within one scan.

The replacement: every word (directive names, `begin`/`end`/`continue`, both split
lookaheads) is read ONCE into a buffer via `read_word_ci` and compared whole.
`read_identifier_word` returns `WORD_NOT_IDENTIFIER` when the lookahead cannot start an
identifier and `WORD_OTHER` when the word is longer than the longest word tested
(`promotedactioncategoriesml`, 26 chars, in a 32-byte buffer; it was `calcformula`, 11, until
B4, and `continue`, 8, before that).

A second shape of the same mistake: a scan that returns false **discards every advance and is
not re-entered at the same position**, so a block that reads text, fails and declines destroys
every later block's only chance to fire. That is why the eleven identifier-initial tokens are
decided in one scan over one read, with `mark_end` pinned to the word before any lookahead.

## A silent lookahead failure

A lookahead that stops on an extra does not always produce an ERROR node. `PREPROC_SPLIT_END`
failing on a trailing comment let the run reparse as a `call_statement` with a clean error
count, invisible to `parse-al-parallel.sh` and `validate-grammar.sh`. Every lookahead now
steps over everything `grammar.js` declares as `extras` (`skip_comment`,
`skip_whitespace_and_comments`, `peek_directive_ci_skip_extras`, and
`var_name_list_follows`'s own directive parsing), and a corpus fixture pins the node, not just
the error count.

## `VAR_ATTRIBUTE_OPEN` ran after the identifier tokens

Until 4.0.0 `VAR_ATTRIBUTE_OPEN` ran after the identifier dispatch, which is why a leading `b`
was absorbed into a following `[`, producing a two-column `[` token whose text was `b[`. It
now runs before.

## `#else`/`#elif` as external tokens: measured and rejected

`#elif`, `#else` and the five directive extras stay grammar regexes, and a regex cannot refuse
a prefix (`\b` and lookahead are rejected by the lexer compiler) or a trailing token. The `#`
dispatch therefore reads every `#` word once, calls `mark_end`, checks the rest of the line,
and either claims a malformed line as `MALFORMED_DIRECTIVE` or declines a well-formed
`#elif`/`#else`/extras line to its regex. Making `#else`/`#elif` external tokens instead was
measured: STATE_COUNT 15,870 → 25,301, parser.c 39.6 MB → 67.9 MB. The prefix mode the
lookaheads kept to agree with the old `#else`/`#elif` regexes is gone; every directive word is
compared whole (`word_in`).

## `SCANNER_HOOK`: why and what it costs

tree-sitter calls the scanner only in states where some external token is valid. Before the
hook, 3,937 of 15,870 states had none (77 of the 2,628 states where `#else` is valid, 71 of
2,602 for `#elif`), and `#elsebegin`, `#else /* c */` at NoSeriesSetupImpl.Codeunit.al:199, or
`x := Rec.` + `#regionX`, still parsed clean. `_scanner_hook` is an external listed in
`extras`, so it is valid in every state, and the scanner **never returns it**; after it, 0
states lack an external lex state. Counted from `src/parser.c`: a state calls the scanner iff
its `ts_lex_modes` entry has a non-zero `external_lex_state` (mind the
`.reserved_word_set_id` entries); a token is valid in a state iff the large or small parse
table has an action on it.

Cost: STATE_COUNT unchanged, parser.c +1.9%, fresh parses about 0-4% slower and incremental
parses about 5% slower. `tools.perf ab` over DC at 24 rounds, three runs on a busy machine
(time before / after): 0.978 (CI 0.964-0.985), 0.998 (CI 0.991-1.007), 0.960 (CI 0.931-1.009).
Incremental on DC: 0.1092 → 0.1147 ms per edit. **Why incremental pays:**
`ts_parser__can_reuse_first_leaf` (tree-sitter 0.26.13 `parser.c`) reuses a leaf lexed in a
different parse state only through its last fallback, `external_lex_state == 0 &&
is_reusable`, i.e. when the state calls no scanner. With the hook every state calls the
scanner, so that fallback is dead and a leaf (incremental node reuse and the token cache
alike) is reused only on an exact lex-mode match. Correct, just more re-lexing. Revisit with
roadmap D1/D2 (state reduction, performance) and deferred-work item 21 (the compiler).

## `DIRECTIVE_EOL`

The ONE `\n` ending an `#if`/`#elif` line, after skipping every extra-space character except
`\n` (`is_extra_space`: space, tab, `\r`, `\f`, `\v`, U+FEFF). Skipping only space and tab once
left `\f\n` and `\r\r\n` a hidden MISSING token that only `has_error` shows. A lexical
`/\r?\n/` is also a separator, and longest match took the LAST newline of a run of blank lines;
`token.immediate(/[ \t]*\r?\n/)` grew a following comment leftward over the space. It is valid
alone (or in error recovery), so it returns without trying other tokens. A second directive on
an `#if`/`#elif` line is caught by the dispatch at the opener (`opener_line_is_malformed`), not
at DIRECTIVE_EOL, which returns before the dispatch runs.

## `MALFORMED_DIRECTIVE` and wide error recovery

The token covers the line up to its last non-space character (for an incomplete condition
with no `//`, up to the newline, trailing spaces and `\r` included: that verdict is reached
only at the newline, too late to mark the last non-space character). When the verdict is only
known at the end of the line the dispatch calls `mark_end` there itself, because
`consume_line` marks only what it advances over and at the newline it advances over nothing.

Error recovery after a malformed line is wide, on purpose not narrowed. The whole line is one
invalid token, so the arm structure around it is lost, and in recovery the guard declines
every external, so the next `#endif`/`begin`/`end` lex as fragments and the following
procedure can be swallowed. The review's alternative (emit the valid word, set a serialized
"tail pending" flag, claim only the rest of the line on the next call) adds scanner state and a
second token boundary for input alc already rejects; not worth it while the ERROR is visible
and on the right line. A directive after code on the same line (AL0620) is NOT caught: the
scanner at a `#` cannot see what started its line (deferred-work item 26).

## `NEGATIVE_INTEGER` / `NEGATIVE_DECIMAL`

As lexical tokens they won by longest match and `Visible = -1 < X;` ERRORed (G7). As scanner
tokens they are emitted only when `;` `,` `#` or EOF follows (after whitespace and comments);
otherwise the scanner declines and `-` lexes as unary minus. Only a `-` commits the block
(issue #23).

## `var_name_list_follows` (B7b-1)

`VAR_ATTRIBUTE_OPEN`'s recognizer. After the attribute and any chained ones it reads a
conditional stream of names (bare or quoted), commas and `#if`/`#elif`/`#else`/`#endif`
lines, with whitespace, comments and the transparent directive extras anywhere, and accepts
only at a `:` reached at local depth 0 with at least one name seen and no comma just before
it. Between two directive lines the strict shape holds (a name never follows a name, a comma
never starts the list or follows a comma); a directive line resets it. It declines at anything
else: `(`, `;`, `{`, `}`, `[`, EOF, the word `procedure`, a `:` inside a group, an unterminated
quoted name, an unbalanced or malformed directive, so a procedure attribute before a
conditional header stays a procedure attribute. It parses directive lines itself:
`#if`/`#elif` through `skip_condition_line`, which declines on a block comment or a second `#`
on the line (AL0631) and on an empty condition (AL0629), and leaves a dangling `and`/`or`/`not`
to the `#` dispatch's `MALFORMED_DIRECTIVE`; `#else`/`#endif` through
`directive_rest_is_blank` (blank but for a `//` comment, AL0631 otherwise);
`#elif`/`#else`/`#endif` with no open `#if` and any word that is not a directive (AL0621)
decline. The nesting count is a local `uint32_t`; `ScannerState.depth` is never touched, and
every advance is non-marking (the caller called `mark_end` at the `[`). Words go through
`read_word_ci` into a 16-byte buffer: a truncated NAME is tolerated (it is still a name; only
an untruncated word is compared with `procedure`), a truncated DIRECTIVE word declines. Some
declines are on input alc accepts, pre-existing gaps recorded as `docs/deferred-work.md` item
45 (whole declarations in a group's arms, an attribute inside a group, an attribute alone in a
group with the name after `#endif`, an attribute after a directive line); they ERROR.
