# Changelog

All notable changes to `tree-sitter-al` are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/); the project
uses [Semantic Versioning](https://semver.org/) where the parse-tree shape is the
public API — a change to node structure or field names is a **major** bump.

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
