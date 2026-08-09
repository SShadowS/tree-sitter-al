# Changelog

All notable changes to `tree-sitter-al` are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/); the project
uses [Semantic Versioning](https://semver.org/) where the parse-tree shape is the
public API — a change to node structure or field names is a **major** bump.

## [Unreleased]

### Changed

- **`case … else` bodies now parse into a single `statement_block` node
  instead of a flat, individually-fielded run of statements.**
  **This changes the parse tree** for every `case … else` branch whose body
  is a bare statement list (one or more statements not already wrapped in
  `begin/end`) — it is the only change in this release that moves parse trees
  *at scale*, and consumers that walk `case_else_branch.body` must update.
  For the release as a whole: this change moves 757 of the 15,358 BC.History
  files, the `exit` fix below moves exactly one
  (`Sales/Document/SalesLineReserve.Codeunit.al`, the file that bullet cites),
  and the two declared-type corrections (`array_type.sizes`,
  `link_value.value`) move none.
  `case_else_branch` used `field('body', repeat($._statement))`, which fields
  *each* statement in the repeat individually, so `body` was `multiple: true`
  — the one scoped construct not honouring the single-node `body` invariant
  every other construct (and the textobject queries, issue #19) rely on.
  `repeat_statement` already wraps its repeat in `$.statement_block`;
  `case_else_branch` now does the same, matching `if_statement.then_branch`
  and friends: `body: (statement_block ...)` instead of one or more
  `body: (...)` siblings. An `else` immediately followed by `end` with no
  statements at all is unaffected — `body` is simply absent, exactly as
  before. Measured against the 15,358-file BC.History corpus: 757 files
  change shape, adding 1,316 `statement_block` nodes; no node type other
  than `statement_block` is added or removed anywhere in the corpus, and
  the `case_branch` count is identical (22,047 before and after). Guarded by
  a new row in `tools/check-field-types.py`.

### Fixed

- **Control-flow keywords and word operators are now genuinely
  case-insensitive.** AL is a fully case-insensitive language, but the Tier-1
  keyword rules and the word-operator rules spelled out exactly three casings
  (`'if'`, `'IF'`, `'If'`). Every other casing failed, and because `_statement`
  carries `optional(';')` the failure was **silent**:
  `iF x = 0 tHEN x := 1 eLSe x := 2;` compiles under alc, but parsed into a
  flat run of `(identifier)` and `(assignment_statement)` nodes with the entire
  if-structure gone and **zero ERROR or MISSING nodes** — a consumer had no way
  to detect that it had been handed the wrong tree. The 19 Tier-1 keywords
  (`if`, `then`, `else`, `case`, `of`, `for`, `foreach`, `while`, `do`,
  `repeat`, `until`, `exit`, `continue`, `break`, `with`, `asserterror`, `in`,
  `to`, `downto`), the word operators (`and`, `or`, `xor`, `not`, `div`, `mod`)
  and the preprocessor `not` now use the case-insensitive `kw()` regex form
  that most of the grammar already used.
  The **named** parse tree is unchanged: all 15,358 BC.History trees are
  byte-identical to the pre-change snapshot. The parser also got *smaller*
  (`STATE_COUNT` 11,879 → 11,796, `parser.c` 23.5 → 22.2 MB), since one regex
  token replaces three string literals per keyword.

  **Anonymous node types removed — action required for some queries.** Each
  keyword and word operator previously contributed one anonymous node type per
  spelled-out casing; it now contributes exactly one, lowercase, whatever the
  source casing. **48 anonymous node types are removed and none are added:**
  the 36 upper- and title-case Tier-1 keyword forms (`"IF"`, `"If"`, `"THEN"`,
  `"Then"`, … for all 18 of `if`, `then`, `else`, `case`, `of`, `for`,
  `foreach`, `while`, `do`, `repeat`, `until`, `exit`, `continue`, `break`,
  `with`, `in`, `to`, `downto`) and the 12 upper- and title-case operator forms
  (`"AND"`, `"And"`, `"OR"`, `"Or"`, `"XOR"`, `"Xor"`, `"NOT"`, `"Not"`,
  `"DIV"`, `"Div"`, `"MOD"`, `"Mod"`). **Every lowercase name is retained** —
  `"if"`, `"then"`, `"exit"`, `"and"`, `"div"` and the rest all still exist and
  now match every casing. A query referencing a lowercase name keeps working
  unchanged and gains coverage; a query referencing an uppercase or title-case
  name **fails to compile** with `Invalid node type` and must drop it.
  `queries/highlights.scm` is updated accordingly. `in` is additionally
  matchable via the named `(in_keyword)` node.

  For a consumer reading the full CST, the anonymous child under a keyword node
  is now normalised to lowercase: source `IF` yields `(if_keyword "if")` where
  it previously yielded `(if_keyword "IF")`. The node text is untouched — only
  the type name normalises — and the named tree is unaffected, which is why the
  harness reports no change. As an upper bound, 3,072 of 15,358 BC.History
  files (20%) contain a non-lowercase spelling of one of these words somewhere
  in the file; the true figure is lower, since that count also matches comments,
  string literals and identifiers such as `IfBlank`.
  - The `10` precedence on the Tier-1 keywords stays *outside* `kw()`, so it
    remains parse precedence. Moving it inside `token()` would make it
    lexical, where it outranks the prec-0 `integer` token in the keyword lexer
    and stops `Integer` from ever matching past `In` — silently demoting
    `basic_type` to `identifier`. Identifiers that merely begin with a keyword
    (`ifCondition`, `Then`, `NotFlag`, `Divisor`, `Order`, `Modify`) are
    unaffected and covered by a regression test.

- **`exit` followed by whitespace before its `(...)` no longer silently drops
  the return value.** `exit_statement` used `token.immediate('(')`, so any
  whitespace — a space, or the parenthesis on the next source line — split the
  statement into a bare `(exit_statement (exit_keyword))` plus a detached
  sibling `(parenthesized_expression ...)`. **No ERROR node.** alc accepts the
  whitespace freely; AL tokenization is whitespace-insensitive between tokens.
  Confirmed against real shipped Microsoft code, not just a synthetic case:
  `BaseApp/Source/Base Application/Sales/Document/SalesLineReserve.Codeunit.al`,
  `VerifyPickedQtyReservToInventory`, has `exit` with its parenthesised
  three-line boolean condition starting on the *next* source line — every
  release through v3.3.1 silently dropped that entire return condition from
  the parse tree with zero ERROR nodes. `'('` is now a plain literal, and
  `exit_statement` is a `choice` of two `prec`-differentiated alternatives
  (parenthesised form higher) rather than one `seq` with an optional trailing
  group, because `exit` followed by `(` is a genuine shift/reduce ambiguity —
  continue the exit vs. reduce and start a new parenthesized-expression
  statement — that a `prec` nested inside `optional()` does not resolve.

- **A call to a quoted-identifier procedure, e.g. `"My Proc"(42);`, no longer
  splits silently.** `call_expression`'s `function` field choice omitted
  `quoted_identifier`, even though the parenless `call_statement` already
  accepted it. With an argument, the call split into a bare
  `(quoted_identifier)` sibling followed by a detached
  `(parenthesized_expression (integer))` — **no ERROR node**. With no
  arguments, `"My Proc"();` produced a `(MISSING identifier)` inside the
  parenthesized expression. alc accepts both forms; `quoted_identifier` is
  now a valid `call_expression` function alongside `identifier`,
  `member_expression`, `qualified_enum_value`, `keyword_identifier`, and
  `subscript_expression`.

- **Parenthesized preprocessor conditions no longer produce an ERROR node.**
  `#if (FOO)` and `#if not (FOO and BAR)` both compile under alc, but
  `_preproc_expression` only accepted a bare `identifier` as an atom — the
  `(` became an `ERROR` node, the condition fell back to reading whatever
  identifier followed, and the trailing `)` leaked into the branch body as a
  detached expression statement. Added `preproc_parenthesized_expression`
  (`'(' _preproc_expression ')'`) as a new alternative in
  `_preproc_expression`, alongside `identifier`, `preproc_not_expression`,
  `preproc_or_expression`, and `preproc_and_expression`.

- **`#elif`/`#else` now tolerate any amount of horizontal whitespace after the
  `#`, not just zero or one space.** `preproc_elif`/`preproc_else` spelled out
  literal zero-space and one-space alternatives, while scanner-owned
  `#if`/`#endif` already accept `[ \t]*`. `#  elif BAR` (two spaces) and
  `#\telse` (a tab) are legal AL — alc accepts both — but were an ERROR.
  Replaced the literal-choice lists with `(?i)#[ \t]*elif` /
  `(?i)#[ \t]*else` regexes; `elif`/`else` carry no external-scanner token and
  touch no `#if`/`#endif` depth state, so this is a plain literal-vs-regex
  swap with no scanner interaction.

- **`node-types.json` no longer declares that `array_type.sizes` can contain a
  comma.** A multi-dimensional declaration like `array[10,20] of Integer`
  wrapped its whole comma-separated size list in one `field('sizes',
  seq($.integer, repeat(seq(',', $.integer))))`. That single `field()` call
  made the generated `node-types.json` record `sizes` as `multiple: true` with
  type set `[',', 'integer']` — declaring the anonymous `,` as a possible
  member of the field, even though the compiled parser's actual field
  assignment never produces that: at runtime each integer already carried its
  own `sizes` label and the comma carried none, in both the old and new
  grammar (confirmed with `tree-sitter parse -c`, and the parse-tree harness
  shows 0 of 15,358 BC.History production trees changed). The bug was a lie
  about the tree in the grammar's own declared API surface, not a corrupted
  parse — but it matters because typed bindings (Rust, TypeScript) and other
  tooling generate their `sizes` accessor type from `node-types.json`, not
  from a live parse, and would have exposed a `sizes` accessor typed to
  include a comma token that can never actually appear. Each size dimension
  now carries its own `field('sizes', $.integer)`; the declared `sizes` type
  set is `['integer']` only, matching what the parser actually produces.
  Guarded by `tools/check-field-types.py`, run as part of
  `./validate-grammar.sh`.

- **`node-types.json` no longer declares that `link_value.value` can contain a
  `.`.** The `DataItem.FieldName` dotted reference form of `link_value`
  (used by `DataItemLink`, `SubPageLink`, etc.) wrapped both identifiers and
  the `.` between them in one `field('value', seq(id, '.', id))`. That single
  `field()` call made the generated `node-types.json` record `value` with
  type set including `.`, even though the compiled parser's actual field
  assignment never produces that: at runtime each identifier already carried
  its own `value` label and the `.` carried none, in both the old and new
  grammar (confirmed with `tree-sitter parse -c`, and the parse-tree harness
  shows 0 of 15,358 BC.History production trees changed). Same class of bug
  as the `array_type.sizes` fix above — a lie about the tree in the
  grammar's declared API surface, not a corrupted parse — and it matters for
  the same reason: typed bindings and tooling generate their `value`
  accessor type from `node-types.json`, not from a live parse. Each
  identifier now carries its own `field('value', $._identifier_or_quoted)`;
  the declared `value` type set no longer includes `.`. Guarded by a new row
  in `tools/check-field-types.py`.

### Removed

- **Dead code cleanup: no parse tree changes.** Dropped `chartpart_keyword`
  (referenced nowhere but its own definition and absent from
  `node-types.json`, so it could never appear in a tree), the `_named_section`
  helper function (never called), and the first of two identical
  `empty_statement` definitions (the second silently shadowed it, so the rule
  itself was unaffected). Also corrected a misleading comment on
  `variable_declaration`'s Label arm: it said the type "must be" `Label`, but
  the rule accepts any `basic_type` — parse structure, don't validate; the
  "must" is a linter's job. Confirmed via `tools/tree-harness.sh verify`: all
  15,358 BC.History parse trees byte-identical before and after.

## [3.3.1] — 2026-08-09

Six external-scanner defects, all pre-existing and all found by a review of
`src/scanner.c` rather than by the corpus — BC.History and DO.Support-Agents
contain no instance of any of them, which is why 100% parse success never
flagged them.

### Fixed

- **Lookaheads now step over comments, not just directives.** Comments are
  `extras` exactly like `#pragma`/`#region`, but every hand-rolled lookahead in
  the scanner treated only directives as transparent. Two concrete failures:

  - `PREPROC_SPLIT_BEGIN` declined on a trailing comment, so
    `if not Ok then begin // note` before `#endif` produced 4 ERROR nodes where
    the identical file without the comment parsed as
    `preproc_split_if_begin_asymmetric`.
  - `PREPROC_SPLIT_END` skipped nothing at all — neither comments nor
    `#pragma`. **This one failed silently**: `end; // note` before `#else`
    dropped the token and reparsed the run as `(call_statement (identifier))`
    with **zero** ERROR nodes, so neither `parse-al-parallel.sh` nor
    `validate-grammar.sh` could see it. Both gates are error-count based and
    structurally cannot catch this class.

  New `skip_comment` and `skip_whitespace_and_comments` helpers handle `//` and
  `/* */`, and both split lookaheads now route through
  `peek_directive_ci_skip_extras`.

- **`PREPROC_SPLIT_END`'s `#endif` arm was unreachable** (no observable change
  today — see below). `read_keyword_ci(lexer, "else") || read_keyword_ci(lexer,
  "endif")` consumes the shared `e` on the failed `else` attempt, so the `endif`
  attempt started at `n` and could never match. `scanner.c`, `grammar.js` and
  the docs all describe `end; #endif` as producing the token; it could not.
  Nothing depends on that today — the only consumer,
  `preproc_split_code_block_end`, requires a `#else` after the token, and
  `end; #endif` is served by `_preproc_end_guard` — so parse trees are identical
  before and after. The value is that the branch is no longer silently dead: the
  rewritten helper takes a target *set* and tests all of them against one
  buffered read of the directive word, so a future rule relying on the
  `end; #endif` form will actually work. This is the same shared-prefix hazard
  documented for the `#endif`/`#endregion` pair in 3.3.0, which was sitting live
  twenty lines away.

- **`VAR_ATTRIBUTE_OPEN` declined a quoted name leading a multi-name
  declaration.** `[InDataSet]` followed by `"My Var", Other: Boolean;` gave 4
  ERROR/MISSING nodes; `Other, "My Var": Boolean;` was fine. The quoted branch
  checked only for `:` and had no `,` continuation. Quoted and bare names are
  now handled by one loop, so either may appear in any position.

- **`VAR_ATTRIBUTE_OPEN`'s bracket scan was comment-blind.** A `]` inside a
  comment within an attribute closed the scan early and declined the token.

- **`PROPERTY_NAME` rejected a newline before `=`.** The identifier-to-`=`
  whitespace skip listed `' '`, `'\t'`, `'\r'` and `'\f'` but not `'\n'`, while
  the leading skip did include it. `Caption` with `= 'Test';` on the next line
  produced 2 ERROR nodes; **alc accepts it** (verified). Comments between the
  name and the `=` are skipped too.

### Removed

- `peek_keyword_ci` — defined, never called.
- `paren_depth` in `VAR_ATTRIBUTE_OPEN` — incremented and decremented, never
  read, with a comment claiming it mattered.
- A comment in `CONTINUE_AS_IDENTIFIER` claiming "the scanner will be called
  again for the same position if we return false". It is not: tree-sitter
  discards the advances and runs the internal lexer. Replaced with the actual
  invariant that makes the early return safe.

## [3.3.0] — 2026-08-09

Additive-only — no previously-valid parse tree changes shape (verified via
`tools/tree-harness.sh`: all 15,358 BC.History `.al` files byte-identical to
the pre-change baseline; `parse-al-parallel.sh` re-confirms 15358/15358, 0
errors, 100%; `tree-sitter test` 1482/1482).

### Added

- **`#define` and `#undef` are now recognized**, as the new node types
  `preproc_define` and `preproc_undef`. Both are single-line regex tokens in
  `extras`, alongside `pragma`/`preproc_region`/`preproc_endregion`: they are
  line-level, take a single symbol name, and never touch the external scanner's
  `#if`/`#endif` depth counter. Case-insensitive, and tolerant of horizontal
  whitespace between `#` and the keyword (`# define`), matching the other
  directives.

  Microsoft documents both directives, and Microsoft's own Highlight.js AL
  grammar lists them, but BC.History contains zero occurrences — the base
  application declares its symbols via `preprocessorSymbols` in `app.json`
  rather than in source — so the gap went unnoticed and the fixtures in
  `test/corpus/preproc_define_undef_test.txt` are synthetic.

  The `extras` placement is deliberately more permissive than the compiler,
  which accepts these directives ONLY before the first real token of a file
  (`error AL0625`); comments, `#pragma`, `#region` and whole `#if`/`#endif`
  blocks may still precede or wrap them. Per "parse structure, don't validate",
  that positional rule belongs in a linter. `docs/preproc-define-undef.md`
  records the full compiler-verified accept/reject matrix (alc 18.0.37).

  `queries/highlights.scm` captures both as `@keyword.directive`. They are not
  added to `queries/folds.scm` — single-line directives that open nothing.

### Changed

- **The external scanner's `#endif` lookahead now steps over every transparent
  directive, not just `#pragma`.** `peek_keyword_ci_skip_pragma` is renamed
  `peek_keyword_ci_skip_extras` and skips `#pragma`, `#region`, `#endregion`,
  `#define` and `#undef` (`TRANSPARENT_DIRECTIVES`, kept in sync with the
  `extras` array). It now reads the directive word after `#` once into a buffer
  and classifies it, rather than trying candidate keywords in sequence —
  consuming `#` is irreversible within one scan, and so is consuming the `end`
  prefix shared by `endif` and `endregion`.

  Beyond the new directives this fixes `#region`/`#endregion` between a split
  `begin` and its `#endif`, which previously blocked `PREPROC_SPLIT_BEGIN`. No
  BC.History file relied on the old behaviour (tree harness: byte-identical).

## [3.2.0] — 2026-07-05

Additive-only — no previously-valid parse tree changes shape (verified via
`tools/tree-harness.sh` before/after on the full BC.History corpus [16,898
`.al` files], run TWICE from a clean `tree-sitter` build cache, manifest
sha256 identical both times: byte-identical to the pre-change baseline;
`parse-al-parallel.sh` re-confirms 16898/16898, 0 errors, 100% both runs;
`tree-sitter test` 1469/1469, confirmed byte-stable across 5 repeated
clean-cache runs).

### Fixed

- **`# if` / `# endif` (a single horizontal space between `#` and the
  keyword) is now recognized** — closing the limitation 3.1.0 documented and
  reviewed-and-rejected (see that entry's "Not supported" note below, now
  resolved). The external scanner's `PREPROC_OPEN`/`PREPROC_CLOSE` consume
  `#`, then optional horizontal whitespace (`' '`/`'\t'` only, via
  `lexer->advance(lexer, false)` so it counts as part of the token — never
  skipped as an extra, never a bare `isspace()`/`\s` test that could span a
  newline), then the case-insensitive keyword, as ONE token — so a spaced
  open/close increments/decrements the scanner's depth counter exactly like
  the unspaced form. **Scanner-exclusive ownership**: the grammar's
  `preproc_if`/`preproc_endif` rules now carry ONLY `$.preproc_open`/
  `$.preproc_close` — every grammar-literal fallback (`'#if'`, `'#IF'`,
  `'#If'`, `'#endif'`, `'#ENDIF'`, `'#Endif'`, `'# endif'`, `'# ENDIF'`,
  `'# Endif'`) is REMOVED. This retires a latent bug the old `'# endif'`
  literal fallback carried since its introduction (commit `500c1eb`): matching
  a spaced close via the grammar literal bypassed the scanner entirely, so the
  depth counter never decremented for it — a `# endif` anywhere in a real file
  would have silently corrupted `begin`/`end` keyword naming for the rest of
  the file. No corpus instance of this ever fired (BC.History has zero spaced
  `#endif` occurrences), so nothing was silently wrong in production, but the
  bug was real and is now closed at the root by making the scanner the sole,
  depth-correct route.
- **`# elif` (a single horizontal space)** is now recognized too — added as a
  plain grammar-literal variant (`'# elif'`, `'# ELIF'`, `'# Elif'`), mirroring
  the pre-existing, long-safe `preproc_else` spaced-literal pattern. `elif`
  carries no external-scanner token and touches no depth state (unlike
  `if`/`endif`), so this is a literal-vs-literal addition, not a
  scanner/literal split — there is no scanner token for elif to fork against.

### Why this is safe (the reverted 3.1.0 attempt was not)

The 3.1.0 attempt added `# if`/`# elif` as NEW grammar-literal alternatives
running ALONGSIDE the existing (already scanner-owned, for `if`) or
literal-only (for `elif`) routes — a genuine scanner/literal split for `if`,
which is a categorical GLR trap (two token-production routes for overlapping
text let the parser's conflict resolution fork non-deterministically across
process states). This time, `if`/`endif` are made **scanner-exclusive** (the
literal alternatives are REMOVED, not added-to) — there is only ONE route to
either token, spaced or not, so there is nothing for GLR to fork on. `elif`
(and `else`) never had a scanner token to fork against in the first place, so
adding their spaced literal is the same safe shape as the pre-existing,
long-working `preproc_else` variants.

Validation:
- `tree-sitter test`: 1469/1469 (1459 pre-existing + 10 new/updated: 9 in
  `test/corpus/preproc_if_elif_whitespace_tolerance_test.txt` [renamed from
  `..._not_recognized_test.txt` — the honest-rejection fixtures flip to
  positives, including the depth-correctness nesting proof, a
  case-insensitivity check, an unspaced regression control, a `# ifx`
  non-directive negative, and the cross-line negatives which STAY errors] + 1
  new GLR-stability repro appended to
  `preproc_split_if_then_begin_else_shared.txt` [the exact reviewer repro
  construct from 3.1.0, now with a spaced open] + 1 pre-existing test in
  `preproc_compound_conditions.txt` ("Preprocessor with spaced endif")
  corrected from the old buggy depth-bypassing shape to the new depth-correct
  one). Confirmed byte-stable across 5 repeated clean-cache
  `tree-sitter test` runs (identical 1469/1469 every time) and 5 repeated
  clean-cache parses of the GLR-stability repro and the nesting-depth-proof
  repro (md5-identical tree output every time — the non-determinism class
  from 3.1.0 does not reproduce).
- `tools/tree-harness.sh`: BC.History (16,898 `.al` files) manifest sha256 is
  IDENTICAL before/after this change
  (`d96393c178907dcc405b0e5b410fe4d86b82a86122af726e585c094fda72d60b`),
  confirmed on 2 separate clean-cache runs — proves zero shape change to any
  previously-valid tree and zero spaced-directive corpus hits (expected: BC
  source doesn't use this spacing style).
- `parse-al-parallel.sh`: 16898/16898, 0 errors, 100.0% success, both before
  and after (2 clean-cache runs post-change).
- Serialization untouched: the scanner's `ScannerState` (a 1-byte `depth`
  counter) and its `serialize`/`deserialize` lifecycle functions are
  byte-for-byte unchanged — only the token-matching body of
  `tree_sitter_al_external_scanner_scan` gained the whitespace-consuming loop.

Version 3.1.0 -> 3.2.0 (additive-only, minor bump per the v2.5.2->v2.6.0 /
v3.0.1->v3.1.0 precedent).

## [3.1.0] — 2026-07-04

Additive-only — no previously-valid parse tree changes shape (verified via
`tools/tree-harness.sh` before/after on the CDO source corpus + zero
divergence in the consuming engine's `cargo test --workspace` and the full
CDO resolution harness; `tree-sitter test` 1463/1463, confirmed byte-stable
across 5 repeated clean-cache runs — see the review note at the end of this
entry).

### Fixed

- **`OptionMembers = TableData,...` first-position collision.** Bare, unquoted
  `TableData` as the FIRST `OptionMembers` member case-insensitively collided
  with the `tabledata` keyword that starts `tabledata_permission` — GLR chose
  the keyword read, so the option list restarted from the second member and
  the first was dropped as an ERROR (a real production hit: MS `System`'s
  `Object.Table.al`, `NAVAppObjectPrerequisites.Table.al`,
  `DatabaseLocks.Table.al` all define an `Option` field whose first member is
  `TableData`). Fixed via a hidden `_tabledata_keyword` rule shared between
  `tabledata_permission` (unchanged shape — the token was already anonymous)
  and a new `alias($._tabledata_keyword, $.identifier)` arm in `option_member`
  (mirrors the existing `table_keyword`-via-`keyword_as_identifier` route for
  the same class of keyword-as-option-member). No new visible node kind; after
  the spaced-if revert `node-types.json` is byte-identical to the previous
  release (the `# pragma`/`# region` fixes are regex-value changes with no
  node-types entry).
- **`# pragma` (a space between `#` and `pragma`) not recognized at all.**
  `pragma` was `#pragma[^\n\r]*` with zero whitespace tolerance (a real
  production hit: Continia System Application's `Http.Codeunit.al`). Now
  `#[ \t]*pragma[^\n\r]*` — HORIZONTAL whitespace only (never `\s*`, which
  would let the extras token span a newline and silently swallow the next
  line's real source — see the region audit below, which found exactly that
  latent bug already present elsewhere in the grammar). Negative tests
  confirm `#\npragma` still does not match.
- **`preproc_region`/`preproc_endregion` cross-line hazard (audit).** Both used
  `#\s*region[^\n\r]*` / `#\s*endregion[^\n\r]*` — the regex crate's `\s`
  matches `\n`/`\r`, so `#` at the end of one line followed by `region`/
  `endregion` on the NEXT line was silently accepted as a single directive
  spanning both lines, swallowing whatever the `#` actually belonged to.
  Confirmed pre-fix via a scratch fixture. Tightened to `[ \t]*`
  (horizontal-only) alongside the pragma fix, closing the same bug class in
  the one other place it existed. The already-accepted single-horizontal-space
  form (`# region`, `# endregion`) is unaffected.

### Not supported (reviewed and explicitly rejected)

- **`# if` / `# elif`** (single horizontal space) — a preventive literal-variant
  fix (mirroring the pre-existing `# else`/`# endif` variants) was drafted and
  then DROPPED after empirical review found it introduced (a) genuine GLR
  non-determinism: the pre-existing `preproc_split_if_then_begin_else_shared`
  construct, fed a spaced `#if`-equivalent open, produced two mutually-
  exclusive stable parses across process states for byte-identical input (a
  small localized `ERROR` vs. a giant procedure-swallowing `ERROR`) — even
  `tree-sitter test`'s own pass count flapped (1453 ↔ 1463) with zero source
  change; and (b) a silent no-`ERROR` shape defect under `#if`-nesting: the
  literal-variant token doesn't participate in the external scanner's depth
  counter (the same trade-off `# else`/`# endif` already accept, which is
  fine for THEM since they carry no nesting-sensitive payload), so a spaced
  `# if` nested inside a real `#if` undercounted depth and the enclosing
  `code_block` silently lost its `begin_keyword`/`end_keyword` naming. The
  feature had zero corpus instances (purely preventive), so removing it costs
  nothing real. **Current, intentional behavior:** a spaced `# if`/`# elif` is
  NOT recognized as a preprocessor directive at all — the file `Recover`s
  (parses with an honest `ERROR` node) rather than silently producing a wrong
  or non-deterministic tree. The consuming engine's `ParseStatus::Recovered`
  diagnostic is the designed detection path: if a real corpus instance ever
  surfaces, it will be flagged for triage instead of passing silently. See
  `test/corpus/preproc_if_elif_whitespace_not_recognized_test.txt` for the
  documented-non-support fixtures (including the honest recovery shape). A
  future fix, if warranted by a real corpus hit, belongs in the external
  scanner (so it participates in the depth counter) — NOT another literal
  variant.

  **RESOLVED in 3.2.0** (2026-07-05): the external-scanner route this note
  called for has landed — `PREPROC_OPEN`/`PREPROC_CLOSE` now consume optional
  horizontal whitespace as part of the token, participating in the depth
  counter exactly as this note anticipated. Scanner-exclusive ownership (the
  grammar-literal fallback for `if`/`endif` is REMOVED, not extended)
  eliminates the scanner/literal split that caused the GLR non-determinism
  described above. See the [3.2.0] entry. The renamed fixture file is
  `test/corpus/preproc_if_elif_whitespace_tolerance_test.txt`.

## [3.0.1] — 2026-06-17

### Added

- Rust binding now exports `TEXTOBJECTS_QUERY` (alongside `HIGHLIGHTS_QUERY`,
  `LOCALS_QUERY`, `TAGS_QUERY`, `FOLDS_QUERY`, `INDENTS_QUERY`) so Rust consumers can
  load `queries/textobjects.scm` directly. The query file shipped in 3.0.0 but was not
  exposed as a crate constant.

No grammar or parse-tree changes — parser is byte-identical to 3.0.0.

## [3.0.0] — 2026-06-17

**Breaking parse-tree restructure.** Every scoped construct now exposes its content
as a single node via a `body` field, instead of as a flat list of direct children.
This enables editor textobjects (Helix / nvim-treesitter `@class.inside` etc.) and
cleaner code-navigation queries (GitHub issue #19), but it changes the tree shape, so
any consumer that walks the tree or writes structural queries must update.

Pure highlighting that matches node *types* (not child relationships) is unaffected.

### Migrating

#### 1. Bodies moved under a `body` field (the big one)

Content that used to be direct children of objects, sections, declarations, code
blocks, loops, `case`, and `var` is now nested under a `body` field.

Before:
```scheme
(page_declaration (layout_section) (actions_section))
(code_block (begin_keyword) (assignment_statement) (end_keyword))
(case_statement (case_branch) (case_branch))
(var_section (variable_declaration) (variable_declaration))
```
After:
```scheme
(page_declaration body: (declaration_body (layout_section) (actions_section)))
(code_block (begin_keyword) body: (statement_block (assignment_statement)) (end_keyword))
(case_statement body: (case_body (case_branch) (case_branch)))
(var_section body: (var_body (variable_declaration) (variable_declaration)))
```

- **Tree-walkers:** descend through `body` (one level) before reading members.
- **Queries:** replace child-anchored patterns like `(code_block (assignment_statement) @s)`
  with field-based ones: `(code_block body: (statement_block (assignment_statement) @s))`,
  or use the universal `(_ body: (_) @inside)`.

#### 2. New named node types (handle in exhaustive switches / regenerate bindings)

`declaration_body`, `statement_block`, `case_body`, `var_body`, `fields_body`,
`keys_body`, `fieldgroups_body`, `labels_body`, `layout_body`, `layout_container_body`,
`action_body`, `action_group_body`, `views_body`, `views_mod_body`, `dataset_body`,
`dataset_mod_body`, `report_body`, `rendering_body`, `analysisviews_body`,
`elements_body`, `query_body`, `schema_body`, `xmlport_body`, `assembly_body`,
`dotnet_body`, `controladdin_body`, `interface_body`.

Rust / TypeScript typed bindings: regenerate against the new `src/node-types.json` and
add the new kinds (or a default arm) to any exhaustive `match`/`switch`.

#### 3. New fields

- `parameters` on `procedure`, `trigger`, and `event_declaration` (previously an
  unnamed `parameter_list` child). Positional access still finds the same node;
  `parameters: (parameter_list)` now also works.
- `body` on every scoped construct, the loop statements, and `code_block`.

#### 4. `case` closing `end` is now a named node

The closing `end` of a `case … of … end` is now `(end_keyword)` at preprocessor
depth 0 (it was an anonymous `"end"` token), matching `code_block`. Update queries /
walkers that keyed on the anonymous string.

#### 5. Empty bodies emit no node

`{ }`, `begin end`, and an empty `var` produce **no** `body` node (tree-sitter forbids
a rule that matches the empty string). Never assume `body` is present — guard for its
absence. `(_ body: (_))` simply does not match empty constructs, which is correct.

#### 6. `repeat` body always wraps; other loops do not

`repeat_statement` body is always `(statement_block)`. `for` / `foreach` / `while` /
`with` bodies remain `choice(<single statement>, code_block)` — a single-statement body
has no wrapper. Do not assume symmetry across loop kinds.

### Added

- `queries/textobjects.scm` — Helix / nvim-treesitter textobject queries
  (`@class.inside/around`, `@function.inside/around`, `@parameter`, generic
  `@block.inside/around`). Query files: 5 → 6.
- `body` field across all scoped constructs; `parameters` field on procedure/trigger/event.
- Content-only `statement_block` node inside `code_block`, reused by `repeat_statement`
  and the preprocessor-split routine bodies.
- `case_body`, `var_body`, and the per-construct `*_body` nodes listed above.

### Changed

- Renamed the shared `_body_element` wrapper node `object_body` → `declaration_body`
  (it is reused well beyond objects — fields, keys, enum values, etc.).
- `case` closing `end` exposed as `end_keyword` (see migration §4).

### Unchanged / not affected

- In-repo queries `highlights.scm`, `locals.scm`, `tags.scm`, `indents.scm`,
  `folds.scm` (they match node types, not the now-nested children).
- Production parse coverage: **15,358 / 15,358 BC.History files, 0 errors (100%)**.
- 1,451 corpus tests passing; external scanner ABI unchanged.

### Decisions / known limitations

- **Attributes remain siblings**, not children/fields of their target declaration
  (preprocessor directives can sit between an attribute and its declaration; the
  first-class-statement model is deliberate — see `.claude/rules/attributes.md`).
  Associating attributes with targets is a post-parse / LSP concern.
- Empty bodies and single-statement loop bodies have no wrapper node — by design
  (see migration §5 and §6).
- See `docs/superpowers/specs/2026-06-17-body-field-textobjects-design.md` for the
  full design and rationale.
