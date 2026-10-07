# CLAUDE.md

GOAL: A parser which parses AL code CORRECT, not just without errors. That is the first and foremost goal. 

This file provides guidance to Claude Code (claude.ai/code) when working with this tree-sitter parser for the AL (Application Language) programming language used in Microsoft Dynamics 365 Business Central.

**Current Status**: 100% production file success rate (15,358/15,358 files), 3,305 tests passing, 0 errors (measured 2026-10-07 on main after the B7b-1 merge)

## Git Commit Guidelines

**Always include error count in commit messages** to detect regressions:
```
Fix XYZ pattern

[BC.History: 7 errors, 99.95% success]
```

Run full parse before committing: `./parse-al-parallel.sh ./BC.History/ .`

**Commit all generated files together** — `tree-sitter generate` writes `src/parser.c`, `src/grammar.json`, and `src/node-types.json`; all three are tracked. Stage them as a set or `grammar.json` silently drifts.

## Quick Reference

**Essential Commands:**
```bash
# Validation (run before completing any task)
./validate-grammar.sh        # Quick: generation, tests, orphan/duplicate detection
./validate-grammar.sh --full # Full: includes production AL file parsing

# Zero-behavior-change gate for grammar refactors (byte-identical parse trees)
# Take a FRESH baseline before you change anything, and name it for the change.
# Never verify against a snapshot you did not just take: a stale one reports a
# huge delta that has nothing to do with your edit. `.snapshots/bc` was left
# behind for two months and 15,349 of its 15,358 rows had drifted.
./tools/tree-harness.sh snapshot ./BC.History .snapshots/baseline-<change>  # ~16s
./tools/tree-harness.sh verify   ./BC.History .snapshots/baseline-<change>  # ~11s, ~22s with a large delta

# Query-coverage harness — proves the CST is lossless and values are queryable
python -m tools.query_coverage.qc run          # regression gate, exits 1 on a new cluster
python -m tools.query_coverage.qc run --all    # full picture
python -m tools.query_coverage.qc accept       # freeze the current state as the baseline

# has_error gate — the only thing that sees a MISSING node for a HIDDEN token
python tools/has_error_sweep.py --root ./BC.History/   # exit 0 clean, 1 errors, 2 cannot run
python tools/has_error_sweep.py --corpus-fixtures      # every corpus case; negatives may be visible, never hidden

# Config oracle (validate-grammar.sh Step 5e, CI job `config-oracle`) — exit 0 clean, 1 finding, 2 cannot run
python -m tools.config_oracle run --tier quick # (a) registry census, (b) self-tests, (c) fixture differential, (d) condition structure (tree condition vs the resolver: ast + truth table); ~2-3 s (docs/performance-baselines.md)
./tools/ts-lock.sh python -m tools.config_oracle run --tier full|resolve --root ./BC.History --root ./DC --root H:/Git/BC28.1 --root H:/Git/BCApps-29.0  # full ~22 min, resolve ~8 min
#   gates: 0 = every refusal is in production-classes.tsv (still NOT validated); 1 = unclassified refusal, stale entry, discrepancy, corpus HEAD not the one the tsv records, a modified/deleted/renamed tracked `.al`, an untracked `.al` not recorded (`# corpus-untracked`) or with another sha256, a recorded one gone; 2 = unlabelled/empty/overlapping root, malformed tsv (e.g. `: host` without `:<slot>`)
python -m tools.config_oracle replay           # historical-defect replays; ~80s cold, ~10s warm
# A fixture cannot-validate record must be classified in tools/config_oracle/fixture-classes.tsv
# (negative / invalid-config need alc evidence; debt(<owner>)); an entry matching no record is stale and fails.

# Traversal helper (roadmap F0, docs/traversal.md) -- validate-grammar.sh Step 5f is the census
python tools/traversal_census.py               # exit 0 clean, 1 finding, 2 cannot run
./tools/ts-lock.sh python -m pytest tests/traversal -q
npm test                                       # the traversal JS tests (after `npx node-gyp rebuild`)
cargo test --features traversal
python tests/traversal/regen_expected.py      # a -u: review every hunk of the diff

# Separator/continuation audit (B7a, docs/b7-separator-continuation-matrix.md) -- validate-grammar.sh Step 5g is the census
python -m tools.b7_audit census --check       # exit 0 clean: registry covers every separator/continuation site of the grammar; no parser, no alc
./tools/ts-lock.sh python -m tools.b7_audit run [--only X] [--check]  # evidence vs alc and the oracle; full ~3 h cold, minutes warm; --only X re-observes every cell, compiles only X; --check replays from .cache/b7_audit; NOT in validate
python -m tools.b7_audit report               # regenerate the matrix from evidence.jsonl.gz; must be byte-identical to the committed file
./tools/ts-lock.sh python -m tools.b7_audit assert --refresh  # re-fingerprint assertions.tsv; exit 1 lists rows whose truth flipped
./tools/ts-lock.sh python -m pytest tools/b7_audit/tests -q   # validate-grammar.sh Step 5h, CI config-oracle job (SILENT witnesses)
# After ANY change to src/parser.c, src/scanner.c or tools/config_oracle: `assert --refresh`, a full `run`, then `report`.
# The committed matrix is valid only at the parser/oracle hashes its evidence header and assertions.tsv record.

# Perf baselines (docs/performance-baselines.md): baseline ~35 min; one group: native [--cc zig]|wasm|incremental|build|oracle; merge BASE NEW
python -m tools.perf ab --lib-a OLD.dll --lib-b NEW.dll --corpus dc   # speed DECISIONS: same session, pinned, ABBA; baselines/compare are context (sessions drift ~30%)

# Workflow tools -- use these, not ad-hoc versions
python tools/snip.py 'x := a + 1;'                 # cursor tree with fields, has_error, ERROR/MISSING/hidden; --object, --raw, -f, --sexp
python tools/snip.py --census --root ./BC.History   # two-shape detector for *_keyword/*identifier types; exit 1 if any flagged
./tools/metrics.sh [--vs REV] [--tests]            # STATE/LARGE_STATE/SYMBOL_COUNT, parser.c size, grammar.js lines, tests, deltas vs REV
python tools/nodetypes.py show|who-has TYPE        # node-types.json questions; `diff REV` for added/removed types and changed fields
./tools/corpus-grep.sh [-E|-P] [-i] [-l|-c] PAT    # sites over BC.History, DC, BC28.1, BCApps-29.0 (*.al only)
./tools/session-cleanup.sh --procs [--yes]         # leftover find/tail/grep/head/sleep older than 30 min; dry run by default

# Standard development cycle
tree-sitter generate         # Generate parser from grammar.js
tree-sitter generate --report-states-for-rule -  # Rank rules by parser-state cost
tree-sitter test            # Run test suite
tree-sitter test -u         # Update test expectations — see the two traps below
tree-sitter parse file.al -d > debug.log 2>&1  # Debug specific files
python parse_bug_finder.py file.al debug.log   # Analyze parsing bugs
```

**On Windows, local builds use clang-cl when LLVM is installed.** `tools/ts-lock.sh` and
`validate-grammar.sh` source `tools/default-cc.sh`, and `loader.ensure_library` applies the same
rule (`loader.build_env`): if `CC` is unset and clang-cl is on PATH or in
`C:/Program Files/LLVM/bin`, it becomes `CC`. The library parses ~2.05x faster with identical
trees and compiles in ~3 s instead of ~11 s (`docs/deferred-work.md` item 21). **To force MSVC,
set `TS_AL_NO_CLANG=1`.** An explicit `CC` always wins, but `CC=cl` works only inside a VS developer
shell: from Git Bash or plain PowerShell `cl` is not on PATH and the build fails with "program not
found". Linux/macOS: no change.

**A MISSING node for a HIDDEN (`_`-prefixed) token is invisible to `tree-sitter parse`,
its `--json-summary` and therefore `parse-al-parallel.sh`**: no `MISSING` is printed and the
file counts as parsed OK. Only py-tree-sitter's `root_node.has_error` sees it.
`tools/has_error_sweep.py` reads it and reports such files as `hidden-only`
(validate-grammar.sh Step 3b over the corpus fixtures, Step 6b under `--full`, and CI).
**A fix that touches a hidden token needs this gate over a production corpus, or a
`has_error` pytest** (`tools/config_oracle/tests/test_directive_eol.py` is the model) — a
clean `parse-al-parallel.sh` run proves nothing about it. `tree-sitter test` does print
`(MISSING _hidden)` in its actual tree, so a corpus fixture catches the defect only if it
holds the triggering input. The deliberate-negative fixture list lives in ONE file,
`tools/deliberate-negatives.txt`, read by Step 3, the sweep and `release.md`.

**Two traps in `tree-sitter test -u`. Both produce a test that passes whether the grammar is right or wrong.**

1. **"Only if no ERRORs" is not a sufficient check.** A tree can be completely wrong without
   containing a single ERROR node — that is what every defect found in 4.0.0 looked like.
   Five shipped fixtures were found asserting a defect as correct behaviour, and each had a
   clean error count. Before accepting a `-u` rewrite, read the whole diff of every file it
   touched and trace each hunk to your change. A hunk you cannot explain is drift being
   blessed.
2. **`-u` writes NO field labels if the expectation it replaces had none**, and an
   unlabelled expected tree asserts *nothing* about fields. Field comparison is
   all-or-nothing per file, so adding one label to an otherwise-unlabelled tree fails —
   which is why the weak form degrades silently instead of erroring. If the fields are the
   point of your test, generate the expectation from `tree-sitter parse` output instead, and
   prove the fixture can fail by renaming a field to `bogus:`.

**Expected ERROR trees come from the CLI, never from `snip`.** py-tree-sitter 0.25 (`tools/snip.py`,
`has_error_sweep.py`, the loader) and the 0.27 CLI recover from errors DIFFERENTLY, so the same bad input gives
different ERROR/MISSING shapes. A corpus expectation that contains an ERROR must be generated by the CLI
(`tree-sitter parse`) or web-tree-sitter 0.27, not copied from `snip`. A deliberate-negative witness that only needs
"an error exists" should use the corpus `:error` attribute instead of pinning a recovery tree that churns on every
grammar change (the 792 `test/corpus/b7_gap_*_test.txt` witnesses do this).

**Two more traps live in the corpus format itself, and both drop a case SILENTLY** — no
warning, no error; the case is simply not run and the suite total moves by less than you
added:

3. **A blank line inside a `====` test header.** The name block must be contiguous. Caught
   by adding a 5-case fixture and noticing the suite count had not changed.
4. **No `---` divider after the header.** `test/corpus/built_in_functions_al.txt` had a
   well-formed header and 110 lines of AL and had never run once since it was added;
   `tree-sitter` parsed the header and discarded the case. Caught by diffing the cases the
   files *declare* against the numbered list a run actually *prints*.

5. **`-u` rewrites files you did not name.** Seven runs of
   `tree-sitter test -u --file-name X` also rewrote six *untargeted* fixtures: it stripped the
   trailing blank line from four and the leading `;` documentation block from
   `operator_precedence_test.txt` and `range_not_an_expression_negative_test.txt` (23 and 9
   lines of compiler-verified rationale, gone with no failing case to point at them). Run
   `git diff --stat test/corpus` after every `-u` and restore whatever you did not target.

After adding fixtures, check the total moved by exactly the number of cases you wrote.
Counting `=` lines and halving does not detect either one — that reports the declared
count, which is precisely the number that disagrees with reality.

**A corpus file can also be invisible to git.** `.gitignore`'s `property_*.txt` was
unanchored and swallowed `test/corpus/property_comment_parameters_extended_test.txt`;
`git status` says nothing about ignored files, so the suite ran 3 extra cases for whoever
had the file on disk and 3 fewer in every fresh worktree — which is how one branch measured
1562 and two others measured 1559 at the same commit. The check is
`git ls-files test/corpus | wc -l` against `find test/corpus -name '*.txt' | wc -l`.

**Executable bits are invisible on this machine.** The repo is developed on Windows with
`core.fileMode=false`, so a script's mode lives only in the git index: `ls -l` shows `rwx` for
everything, `git status` says nothing, and the file runs fine here. On Linux a 100644 script
exec'd by another script fails with `Permission denied` (exit 126), and a 100644 shim on PATH
is not found. That kept the "Gate self-test" CI job red from its first run to 4.1.0 (five
cases, one cause, four files), after the same class had already hit `check-wasm-fresh.sh`
once. The only view is `git ls-files -s`; the fix is `git update-index --chmod=+x <file>`;
`tools/check-exec-bits.sh` (validate-grammar.sh Step 10, and a CI step) gates every tracked
`*.sh` and gate-fixture shim.

**Common Test Options:**
- `-i "pattern"` - Include tests matching pattern
- `-e "pattern"` - Exclude tests matching pattern
- `--file-name "test.txt"` - Run specific test file
- `-d` - Show debug log
- `-D` - Generate debug graphs (log.html)

## Architecture

**Core Files:**
- `grammar.js` - Main grammar definition (~4,781 lines). Never edit `src/parser.c` (auto-generated)
- `src/scanner.c` - External scanner for property disambiguation and preprocessor patterns
- `test/corpus/` - Test suite with AL code and expected parse trees (723 files, 3,305 cases, measured after B7b-1)
- `queries/` - 6 query files (highlights, locals, tags, indents, folds, textobjects)

**Key Design Principles (V2 architecture):**
- **Parse structure, don't validate** — Accept any `Name = Value ;` as a property. Semantic validation belongs in linters/LSP servers, not the parser
- **Scanner-based property disambiguation** — The `PROPERTY_NAME` scanner token distinguishes `identifier =` (property) from `identifier :` (variable) via 1-char lookahead
- **Generic property rule** — ONE `property` rule handles all simple properties (vs V1's 291 individual rules)
- **Generic preprocessor** — ONE `preproc_conditional` rule + ~12 dedicated split-construct rules (vs V1's 63)
- **Named keyword nodes** — 154 keywords exposed as named nodes for query matching (152 grammar rules + the external `begin_keyword`/`end_keyword`), all with a uniform shape: one anonymous child typed as the canonical lowercase spelling
- **Stateful scanner** — a `uint32_t` depth counter tracks `#if`/`#endif` nesting (it was a `uint8_t` until 4.0.0 and wrapped at 256); `begin`/`end` are named at every depth, and the depth counter decides only whether a `PREPROC_SPLIT_*` token gets first refusal
- **Reserved-word sets, three contextual sets** — `reserved: { global: [], implementation_names: [...], relation_target_names: [...], code_names: [...] }` (tree-sitter ≥ 0.25). `global` is empty on purpose; `implementation_names` reserves `true`/`false` inside `implementation_value`'s two names, which is what lets `prec.dynamic` favour the mapping reading of `A = B` without stealing `Visible = HideActions = false;`. Two rules the docs do not state, both measured while fixing issue #20: an entry must be a rule **symbol** (`$._true_token`), not a fresh `kw()`; and a parse state takes the largest set among items whose **next step is `identifier` itself**, so the set must sit on a rule that names `$.identifier` directly (`_implementation_name`) — wrapping a reference to `_identifier_or_quoted` reserves nothing. `relation_target_names` (B5) reserves `if`, `else` and `where` on `_qualified_name_segment`, which alc rejects as relation-target segments, at 0 extra states. `code_names` (B6) reserves `and`, `or`, `xor`, `div`, `mod`, `in` and `not` in code (alc: AL0104 at a statement start, AL0224 read in an expression; `is`/`as` stay names, declarations are unaffected) on `_expression`, `call_expression`'s `function` choice and `_expression_statement`; because a first option member shares the generic property value's first state, `option_member` takes the seven words back as identifiers (alc accepts them there), STATE_COUNT +2
- **Single-read identifier dispatch** — all eleven identifier-initial scanner tokens are decided in one scan over one read of the word. Nothing matches a keyword against the live lexer: a walking matcher leaves its matched prefix consumed on failure, so sequential per-token reads start mid-identifier. That shape caused three separate defects and was deleted in 4.0.0

**Scanner Tokens:**

| Token | Purpose |
|-------|---------|
| `PROPERTY_NAME` | `identifier` followed by `=` (not `:=`) — property/variable disambiguation |
| `CONTINUE_AS_IDENTIFIER` | `continue` followed by `:=` `(` `.` `[` `::` or a compound assignment — used as a name, not the statement |
| `VAR_ATTRIBUTE_OPEN` | the `[` of a variable attribute, emitted only when a variable name list follows the attribute(s), possibly with `#if` groups, ending at its `:` (`var_name_list_follows`, B7b-1); otherwise the `[` opens a procedure `attribute_item` |
| `PREPROC_OPEN` | `#if` — increments depth counter |
| `PREPROC_CLOSE` | `#endif` — decrements depth counter |
| `BEGIN_KEYWORD` | `begin` at any depth — named node for queries |
| `END_KEYWORD` | `end` at any depth — named node for queries |
| `PREPROC_SPLIT_BEGIN` | `begin` at depth > 0, immediately before `#endif` — split detection |
| `PREPROC_SPLIT_END` | `end` at depth > 0, followed by `;` then `#elif`/`#else`/`#endif` — split detection |
| `CALC_FORMULA_PROPERTY_NAME` | `CalcFormula` followed by `=` — keyed by NAME; its value has its own grammar (see below) |
| `ML_PROPERTY_NAME` | one of the compiler's 13 ML names followed by `=` — keyed by NAME, value `ml_value_list` (B4) |
| `NAMESPACES_PROPERTY_NAME` | `Namespaces` followed by `=` — keyed by NAME, value `namespace_value_list` (B4) |
| `TABLE_RELATION_PROPERTY_NAME` | `TableRelation` followed by `=` — keyed by NAME, value `table_relation_value` with one `target: (qualified_name)` (B5) |
| `LINK_PROPERTY_NAME` | one of the compiler's six link names (`SubPageLink`, `RunPageLink`, `LinkFields`, `DataItemTableFilter`, `ColumnFilter`, `DataItemLink`) followed by `=` — keyed by NAME, value `link_value_list` (B5b) |
| `DIRECTIVE_EOL` | the ONE newline ending an `#if`/`#elif` line (hidden `_directive_eol`); a lexical `/\r?\n/` took the last of a run of blank lines |
| `NEGATIVE_INTEGER` / `NEGATIVE_DECIMAL` | `-1` / `-1.5` as one signed literal (issue #23), emitted only before `;` `,` `#` or EOF; otherwise `-` is unary minus (G7: `Visible = -1 < X;` ERRORed) |
| `MALFORMED_DIRECTIVE` | a `#` line alc rejects (`#elsewhere`, `#regionX`, `#endif;`, `#else B`, a block comment on `#if`/`#elif`), as hidden `_malformed_directive`, which no rule takes: the line becomes an ERROR (B2). `#else`/`#elif` stay regexes; the `#` dispatch is their gatekeeper |
| `SCANNER_HOOK` | never emitted; in `extras` so that every parse state calls the scanner (and so the `#` gatekeeper). Do not return it, ever |

## Property Handling

Properties use a generic rule — no per-property validation:

```javascript
property: $ => seq(
  field('name', $.property_name),   // PROPERTY_NAME scanner token
  '=',
  field('value', $._property_value),
  ';'
),
```

**Complex properties** (~36 rules) have unique syntax and remain as individual rules:
- CalcFormula, TableRelation, Permissions, AccessByPermission
- DataItemLink, RunPageLink, SubPageLink, ColumnFilter
- SourceTableView (and related view properties)
- Caption/ToolTip (with Locked/Comment sub-fields)
- ML properties (multilingual key=value lists)
- List properties (comma-separated identifiers)
- DecimalPlaces, OrderBy, Implementation

**Adding new property support:** Most properties work automatically via the generic rule. Only add a dedicated rule if the property has syntax beyond `Name = Expression ;`.

**Name-keyed properties: five families, and the scanner keys them.** `PROPERTY_NAME`'s lookahead reads the word once and emits a keyed token instead, falling back to `PROPERTY_NAME` where the parse state does not offer it (order: CalcFormula → ML → Namespaces → TableRelation → Link → generic → decline). `property` has one arm per family, whose value has that family's grammar only.

- **`CalcFormula`** → `CALC_FORMULA_PROPERTY_NAME`. Its value (`sum/count/exist/min/max/average/lookup(Table.Field [where(...)])`) is also a complete call expression when there is no `where()`, and only the name separates `CalcFormula = Count(X)` from `DataCaptionExpression = Caption(Rec)`. Before issue #21 the GLR tiebreak gave 22 no-`where` aggregates in BC.History to `property_expression`.
- **The compiler's 13 ML names** (`CaptionML`, `ToolTipML`, `OptionCaptionML`, `PromotedActionCategoriesML`, …; the list is in `src/scanner.c`) → `ML_PROPERTY_NAME`, value `ml_value_list`. A one-pair `ENU='x'` is also a complete comparison, so before B4 every one-pair ML value was a `comparison_expression` (G9).
- **`Namespaces`** → `NAMESPACES_PROPERTY_NAME`, value `namespace_value_list` / `namespace_pair` (`prefix:`, `uri:`).
- **`TableRelation`** → `TABLE_RELATION_PROPERTY_NAME`, value `table_relation_value` (B5). The compiler reaches `ParseTableRelationPropertyValue` through that one name and reads the target with `ParseQualifiedName`, one qualified name, so the target is `target: (qualified_name)` and never a member expression. Before B5 every property's dotted value was offered as a relation (14,011 production sites), and G10 (`#if X and B #endif` after a dotted value) ERRORed. Other properties' dotted values are expressions.
- **The link family** (`SubPageLink`, `RunPageLink`, `LinkFields`, `DataItemTableFilter`, `ColumnFilter`, `DataItemLink`) → `LINK_PROPERTY_NAME`, value `link_value_list` (B5b). The compiler has three value grammars behind these names (TableFilter, ReportDataItemLink, QueryDataItemLink); ours is one neutral union, so the three delegates deliberately over-accept (`DataItemLink = A = const(1)`, `RunPageLink = A = B.C` parse clean though alc rejects them, a validation matter). Link syntax appears only under these six names: `Visible = Flag = Rec.OtherFlag;` and `Enabled = Status = const(Open);` are ordinary expressions, and a `const` argument may be signed, decimal or `L`-suffixed. The keyed value is optional: an empty `DataItemLink` value is rejected only semantically (AL0171), so the parser accepts it; the same shared arm structurally over-accepts `RunPageLink = ;`, which alc rejects as syntax (AL0104/AL0107).

Each keyed value may also be a whole-value `#if` whose arms are that family's list again, with the `;` after `#endif` or inside every arm (`preproc_conditional_property_value`). The rule for adding a family:

> Key a name only when the compiler parses that name's value with its own grammar *and* that grammar cannot be told apart from an expression in ours. The keyed list comes from the compiler's tables, never from a naming pattern such as "ends in ML".

`FooML` and `CaptionMLX` stay generic, and fixtures pin that.

**Property value runs (B11).** A value may be several consecutive `#if ... #endif` groups at one value site (the property, or an arm). Routing (spec `docs/superpowers/specs/2026-10-05-property-value-runs-design.md` 3.1), in order: (1) at most one core-bearing group, so that group is the core and empty groups around it are decorations; (2) `;` inside every arm: `value: (preproc_conditional_property_value_sequence ...)`; (3) `;` after in a list family (link, Implementation, `OptionMembers`, and Permissions, which behaves as one): the family's element conditionals; (4) `;` after in CalcFormula, TableRelation, ML or Namespaces: a sequence; (5) anything else, a generic `;`-after run, stays a visible ERROR (B13). The sequence's only field is `value` (multiple, each a `preproc_conditional_property_value`); `property.value` stays single (`tools/check-field-types.py`). Directive-only empty groups are unfielded decorations, never wrapped, and carry no `value:`, with three suffix exceptions (an empty group after a plain value, before the property's `;`, spec 3.2/4.2 execution amendment): in link (`listValue`), Implementation and Permissions it stays the list's element conditional, and in TableRelation it stays inside `table_relation_value` (all base trees); `OptionMembers = A,B #if X #endif ;` makes it a property decoration (base ERROR). Rules come from the generators `valueRunRules`, `afterGroupRules`, `afterSequenceRules` and `listOpenerRules`; read their comments before touching one. Boundaries: a sequence is a one-reading construct, so a property boundary that depends on the configuration is refused by the oracle (B12, item 36); this includes continuation absorption, where a conditional block after a non-terminated `;`-inside group whose arm also parses as a property (`Caption = #if X 'a'; #endif #if Y Editable = false; #endif`) is read as part of the value, wrong where the earlier group already ended the property (spec 3.4 amendment 7); and fragment runs are B13 (item 37, gap file `test/corpus/property_value_run_b13_gap_test.txt`). Precedence decisions and their witnesses: `docs/b11-precedence-audit.md`.

**Strict conditional lists (B7b-1).** A homogeneous delimited list in which an `#if` group may stand at any separator (implements, field lists, sorting / order-by inner lists, move elements, array dimensions, attribute arguments, var names) is generated by two helpers in `grammar.js`: `...strictConditionalList('<family>', $ => <atom>, '<sep>'[, groupDynamic])` spread into `rules` (hidden seam helpers `_<family>_e/_t/_b/_r` plus the visible group `preproc_conditional_<family>`), and `...strictListBody($, '<family>', '<sep>')` written into the host in place of `item, repeat(seq(sep, item))`. The body is inlined, never a hidden `_F_list` rule, because the B7a census keys a separator by its rule path and a hidden rule would orphan the frozen manifest's cell ids. Field the atom as the host fields its items (the field then reaches the group too, `multiple`, `required: false`); unfielded hosts stay unfielded. The oracle side is the family-schema registry `FAMILIES` in `tools/config_oracle/lowering/conditional_lists.py` (region adapter, item kinds, separator, alc cardinality; split-tree validation and per-configuration `item (sep item)*`). Adding a host: the "Host Conversion Procedure" in `docs/superpowers/plans/2026-10-07-b7b-1-strict-conditional-lists.md` (hand-written RED fixture, the two helpers, field invariants in `tools/check-field-types.py`, `traversal/policy.json`, a `FAMILIES` entry and the oracle's `contracts.py`, four-corpus `python -m tools.perf parity` 0), the three arm-separator rows per family in `tools/b7_audit/registry.tsv` (keys `occ:_<family>_b:0.0`, `occ:_<family>_r:1.0.0`, `occ:_<family>_r:2.0`, each with `equiv occ:<host>:<path>`, no new cells), the family's `GROUP` entry in `tools/b7_audit/strict_list_assertions.py`, plus a manifest or matrix re-run (`python -m tools.b7_audit`). One scanner change came with it: a variable attribute's `[` (`VAR_ATTRIBUTE_OPEN`) is now decided by `var_name_list_follows` in `src/scanner.c`, which accepts a conditional name list ending at `:` (`.claude/rules/scanner.md`). A group whose arms supply no separator still parses (no per-arm separator tracking): those all-configurations-invalid forms are classified over-acceptances, `docs/deferred-work.md` item 44.

## Keyword Architecture

154 keywords are named nodes for query matching — 152 grammar rules plus the two external tokens `begin_keyword`/`end_keyword`. **Every grammar keyword rule has the same shape: exactly one anonymous child, typed as the canonical lowercase spelling.**

```javascript
table_keyword: $ => alias(kw('table'), 'table'),          // anonymous "table" child
procedure_keyword: $ => alias(kw('procedure'), 'procedure'),
if_keyword: $ => prec(10, alias(kw('if'), 'if')),         // anonymous "if" child
```

Compound (CamelCase) keywords use `kwCases()` instead of `kw()`, because their case-spelling whitelist is load-bearing — see "CamelCase keywords" below — but they produce the identical shape:

```javascript
enum_keyword: $ => prec(10, kwCases('enum', 'enum', 'ENUM', 'Enum', 'eNUM', 'eNum', 'ENum')),
```

**begin/end are named via stateful scanner** — `begin_keyword` and `end_keyword` are emitted at **every** depth. `grammar.js` has no `kw('begin')`/`kw('end')` fallback: begin/end are scanner-exclusive, the same way `#if`/`#endif` became scanner-exclusive in 3.2.0, so there is no scanner/literal pair for GLR to fork on. Direct naming via grammar rules or `alias()` still breaks GLR backtracking — the stateful scanner is the correct approach.

The depth counter no longer decides whether the keyword is *named*; it decides only whether a `PREPROC_SPLIT_*` token gets first refusal. Both decisions happen in **one** scan: the scanner reads the keyword, calls `mark_end`, runs the split lookahead, and picks the symbol from the result. They cannot be two sequential blocks — a scan that returns false discards every advance and is not re-entered at the same position.

Until 4.0.0 the depth > 0 case handed off to an anonymous `kw('begin')`, which made a complete `begin … end` inside any `#if` block **vanish from the tree**: `kw()` builds a `token(PATTERN)`, and tree-sitter renders anonymous *pattern* tokens as hidden `aux_sym_*` symbols (`.visible = false`), unlike anonymous *string* tokens such as `";"`, which are visible. The keyword was lexed and then dropped, so the CST was not lossless over the source and both keywords were unhighlightable inside every `#if`.

**Named keyword node structure — uniform since 4.0.0.** A named rule whose entire body is a single token collapses *into* that token, so the node's shape is decided by that token's visibility, which is the same `.visible` rule as above. A bare `kw('word')` builds a `token(PATTERN)` and therefore yields a **childless leaf**; wrapping it in `alias(…, 'word')` makes the token a visible STRING and yields **one anonymous child**. Before 4.0.0 the grammar mixed both, so a consumer could not predict a keyword's shape.

> **Every grammar keyword rule is now `alias(kw('word'), 'word')` (or `kwCases(...)` for compound keywords) and has exactly one anonymous child typed as the canonical lowercase spelling. The 2 external tokens cannot take a child and remain childless leaves.**

| body | child | count |
|---|---|---|
| `alias(kw('word'), 'word')` → STRING | one anonymous child typed `"word"` | 139 |
| `kwCases('word', …)` → STRING, each spelling aliased to `'word'` | one anonymous child typed `"word"` | 13 |
| external scanner token (`begin_keyword`, `end_keyword`) | none — cannot take a child | 2 |

The child's type is always the canonical lowercase spelling regardless of how the source spelled the keyword: `XmlPort` yields `(xmlport_keyword "xmlport")`, and the node's own text is still `XmlPort`.

**`node-types.json` cannot confirm this for you.** It lists anonymous children only when they sit inside a field, and none of these do, so all 154 keyword nodes look childless there regardless of their real shape. **Read a keyword's text from the node itself, never by descending into a child** — that stays correct for the two external tokens, which really are childless, and it survives any future change to the anonymous layer.

**`object_type_keyword` used to be the counter-example to the contract. It is not any more — and the fix is worth knowing, because the mechanism recurs.** `node-types.json` contains **155** named `*_keyword` types, not 154: `object_type_keyword` has no rule of its own. `database_reference` builds it by aliasing a `choice` of six alternatives (`grep -n "object_type_keyword" grammar.js`). Five were named `$.*_keyword` rules carrying visible aliased STRING tokens while the sixth was a bare `kw('database')` — a hidden pattern token — so one node type shipped two shapes decided purely by which word the source used:

```
(object_type_keyword text='Page')      children=[("page", anonymous)]
(object_type_keyword text='DATABASE')  children=[]                     <- childless
```

Measured over BC.History: **22,988 of 40,674 `object_type_keyword` nodes were the childless kind** — every `DATABASE::` in the corpus answering differently from its siblings. Fixed by giving `database` a real `database_keyword` rule like the other five. All 40,674 now have exactly one anonymous child.

**The nested form does not work, and the fixture pins that.** `alias(alias(kw('database'), 'database'), $.object_type_keyword)` looks equivalent and is not: the two aliases do not compose, the DATABASE case loses its `object_type_keyword` node entirely, and the `keyword` field points straight at an anonymous token. `test/corpus/object_type_keyword_uniform_shape_test.txt` fails on exactly that.

**Neither this nor the `keyword_identifier` defect below was a byte gap, and `qc` reported nothing for either.** The outer node covered the bytes in both cases, so the CST stayed lossless and both survived the losslessness work that drove gap clusters to zero. They were *shape* inconsistencies. Do not expect an existing gate to catch this class — the instrument that shows it is a tree-cursor walk (`tools/fieldwalk.c`), and the corpus-wide form is a census keyed by `(type, child count)`.

**`keyword_identifier` had the same defect one level up, and is also fixed.** It accepts thirteen words; six were named `*_keyword` rules and seven were bare `kw()`, so `Codeunit.Run()` gave `(keyword_identifier (codeunit_keyword))` while `Record.Get()` gave a childless `(keyword_identifier)`. All thirteen are now named rules — see `test/corpus/keyword_identifier_uniform_shape_test.txt`, which unlike the `object_type_keyword` fixture really does pin the shape, because these children are *named* and corpus expected trees show named children.

**Converting a bare `kw()` to `alias(kw(w), w)` cannot steal a spelling.** `kw(w)` is `token(RustRegex('(?i)w'))` and `alias()` wraps that same token, so matching is unchanged. Verified over BC.History rather than argued: the `identifier` node count was 5,908,480 before and after, and the full `(parent, field, child)` edge census was byte-identical (13,339,003 fielded edges, 911 kinds). The `kwCases()` whitelist argument does **not** apply to such a conversion — `kwCases()` exists to stop `kw()` from *widening* a compound keyword over spellings AL uses as identifiers, and an alias widens nothing.

`_tabledata_keyword` is deliberately excluded: it is a *hidden* (`_`-prefixed) token helper, not a keyword node, and one of its two uses re-aliases it to `$.identifier`.

**CamelCase keywords** use `kwCases()` — an explicit case-spelling whitelist, each spelling aliased to the canonical lowercase form:
```javascript
controladdin_keyword: $ => prec(10, kwCases('controladdin',
  'controladdin', 'CONTROLADDIN', 'Controladdin', 'ControlAddIn', 'ControlAddin', 'controlAddIn', 'controlAddin')),
```

**The whitelist is load-bearing — never "simplify" these to `kw()`.** `kw()` compiles to a case-*insensitive* regex, which would claim every case permutation and steal spellings that AL code legitimately uses as identifiers. Real AL declares `eNuM: Decimal;` as a variable; `eNuM` is absent from `enum_keyword`'s whitelist precisely so it stays an `identifier`. Converting the 13 compound keywords to `kw()` fails `test/corpus/enum_as_identifier_test.txt`.

**The 13 `kwCases()` rules are exactly the object-declaration keywords, and nothing else:** `codeunit`, `controladdin`, `dotnet`, `enum`, `enumextension`, `pagecustomization`, `pageextension`, `permissionset`, `permissionsetextension`, `profileextension`, `reportextension`, `tableextension`, `xmlport`. That membership rule is a stronger check than the count, because it is falsifiable by inspection rather than by re-running a classifier. **A 14th entry that is not an object-declaration keyword is almost certainly a mistake** — `view_keyword` was miscounted into this set once precisely because it is not one.

## Attribute Handling

Attributes are first-class statements (Rust/C# pattern) — siblings to declarations, not nested.

```al
[Scope('OnPrem')]
[IntegrationEvent(false, false)]
procedure MyEvent() begin end;
```

Parse tree: `(attribute_item ...) (procedure ...)`  — separate nodes at the same level.

## Preprocessor Handling

**Line-level directives** are `extras` (reachable anywhere): `pragma`,
`preproc_region`, `preproc_endregion`, `preproc_define`, `preproc_undef`. They
never touch the scanner's `#if`/`#endif` depth counter. The AL compiler only
accepts `#define`/`#undef` before the first real token of a file — that
positional rule is a linter's job, not the parser's. See
`docs/preproc-define-undef.md`.

**Generic conditionals** (most cases):
```javascript
preproc_conditional: $ => seq($.preproc_if, repeat($._any_content), ...)
```

**Dedicated split-construct rules** (~12, for cross-branch fragments):
- `preproc_split_procedure` — procedure header variants in `#if`/`#else`
- `preproc_split_if_statement` — if-then header varies across branches
- `preproc_split_if_then_begin` — `begin` inside `#if`, `end` in second `#if`
- `preproc_fragmented_else_tail` — end-else-begin fragmented across `#if` blocks
- `preproc_split_declaration` — object declaration split across branches
- And others for case statements, fields, datasets, etc.

## Testing

**Test Format** (`test/corpus/*.txt`):
```
========================================================================
Test Description
========================================================================
[AL source code]
------------------------------------------------------------------------
(expected_parse_tree)
```

**Guidelines:**
- Never delete test files — fix the underlying issue
- Use `tree-sitter test -u` only if no ERROR/MISSING nodes exist
- Create tests for each new grammar feature
- **BC.History (15,358 production files) is the real validation gate** — tests are a development aid

## Debugging Parse Failures

```bash
# 1. Parse with debug output
tree-sitter parse file.al -d > debug.log 2>&1

# 2. Analyze with bug finder
python parse_bug_finder.py file.al debug.log
```

**Available tools:**
- `parse_bug_finder.py` — Correlates bugs with source code (recommended)
- `parse_debug_analyzer.py` — Full parse flow analysis (advanced)

## Grammar Development

### Core Principles
- **Parse structure, don't validate** — Accept syntactically plausible code
- **snake_case** for rule names
- **`kw('word')`** for case-insensitive keywords (regex-based)
- Use `prec.left/right/prec` for precedence; avoid left recursion

### Adding New Constructs
1. Study AL construct (use Business Central docs MCP)
2. Check for existing patterns in grammar.js
3. Add/modify rules (update `src/scanner.c` if needed)
4. Create tests
5. Run `./validate-grammar.sh`
6. Validate against BC.History

### Common Issues

| Pattern | Symptom | Fix |
|---------|---------|-----|
| **Missing construct** | ERROR nodes | Add rule to `_body_element` or relevant choice list |
| **Case-sensitivity** | Keywords not matching | Use `kw()` or explicit `choice()` with case variants |
| **Preprocessor splits** | MISSING tokens in #if contexts | Add dedicated `preproc_split_*` rule |
| **Property syntax** | Complex property fails | Add dedicated complex property rule |
| **Keyword as identifier** | Variable name conflicts | Add to `keyword_as_identifier` choice list — as a bare `kw('x')`, never `$.x_keyword` |

## Two rules about verification, learned the hard way in 4.0.0

**A generated artifact can never fail a contract, because it is re-derived from the thing
being tested.** `src/node-types.json` tells you what the grammar *currently does*.
`tools/check-field-types.py` is hand-maintained, so it is the only thing that can tell you
what the grammar is *supposed to do* — and it is what gates. Checking a field's shape in
`node-types.json` and calling the invariant verified is necessary and not sufficient: a
narrowing that `node-types.json` reports happily still fails Step 5b, which is the gate
working. The same distinction applies to any generated file you are tempted to read as a
check.

**"I tried it and it forced N conflicts" measures one edit, not the grammar.** Record which
edit was tried, or a half-finished attempt gets filed as an inherent limit and nobody
revisits it. This happened: adding `code_block` to `_statement_inner` was recorded as
forcing a conflict per host and a GLR fork on every `begin`. It does — until you also delete
the seven host arms that already carried their own `field(X, $.code_block)` beside
`fieldedStatement($, X)`, which were giving each host a second derivation of the same
string. With those removed there are zero conflicts and the parser gets *smaller*. The
limitation was an artifact of the attempt, and it sat unchallenged for a release.

## Parser Metrics

**Note:** These metrics drift constantly. Verify before quoting — `wc -c src/parser.c`,
`grep -E 'SYMBOL_COUNT|STATE_COUNT' src/parser.c`, `wc -l grammar.js`, and the last line of
`./tools/ts-lock.sh tree-sitter test`. **Do not take the test count from this table**: it was
1,562 here while the suite really ran 1,559, and a session used the stale figure as the base of
a "the delta is exactly what I added" check, which therefore could not fail.

| Metric | Value | as of |
|--------|-------|-------|
| parser.c size | 51.3 MiB (53,778,268 bytes) | B7b-1 (2026-10-07) |
| SYMBOL_COUNT | 1,268 | B7b-1 (2026-10-07) |
| STATE_COUNT | 23,579 (LARGE_STATE_COUNT 7,521) | B7b-1 (2026-10-07) |
| grammar.js lines | 7,549 | B7b-1 (2026-10-07) |
| Tests | 3,305 | B7b-1, main (2026-10-07) |
| Production success | 100% (0 ERROR and 0 MISSING nodes over 15,358 files) | 4.0.0 |
| Named keywords | 153 (151 rules + 2 external), uniform shape | 4.0.0 |
| Query files | 6 (highlights, locals, tags, indents, folds, textobjects) | 4.0.0 |

The 4.0.0 rows were measured on the merged tree, not carried from a branch; the B7b-1 rows were re-measured
on main after the squash merge of `feat/b7b-1-strict-lists` (d6d946a).
Three different test counts (1,562 / 1,574 / 1,580) circulated during 4.0.0 and
two were arithmetic from a stale copy of this table. Re-measure; do not recall.

**parser.c size is MiB, not decimal MB.** 31,515,082 bytes is 30.1 MiB *and* 31.5 MB; quoting
the two against each other looks like a 5% regression and is not one. Both conventions have
been wrong here before, in opposite directions, which is why the byte count is given too.

`node-types.json` declares **154** named `*_keyword` types against 153 named keywords: the
extra is `object_type_keyword`, which has no rule of its own.

The two silent corpus-drop traps and the gitignore hazard that make the test count disagree
between checkouts are documented under **Quick Reference**, with the `-u` traps.

## Validating AL Syntax Questions

When uncertain whether the AL compiler accepts a construct (esp. niche or undocumented forms), use the **`al compile`** CLI to test directly — it's the ground truth, not LLM recall or web search.

**For anything with `#if`, run the four-way probe with the tool, not by hand:**

```bash
python -m tools.alc_probe run my_probe.al                    # every symbol assignment, split AND flat
python -m tools.alc_probe run tools/alc_probe/cases --check  # the committed, recorded verdicts
```

It compiles each symbol assignment twice (the file as written, and the oracle resolver's
flat text), runs a valid and a garbage control first, and reports a broken project as
`BROKEN` (exit 2) instead of a rejection. A flat/split disagreement is `MISMATCH`. Commit a
probe whose verdict matters under `tools/alc_probe/cases/<family>/` with an `// expect:` and
a `// source:` header (`tools/alc_probe/README.md`). The manual recipe below is what it
automates, and the traps are why it exists.

```bash
# Minimal probe project
mkdir -p /tmp/al-probe && cd /tmp/al-probe
cat > app.json <<'EOF'
{"id":"11111111-2222-3333-4444-555555555555","name":"Probe","publisher":"Test",
 "version":"1.0.0.0","platform":"1.0.0.0",
 "idRanges":[{"from":50000,"to":99999}],"runtime":"15.0","target":"OnPrem"}
EOF
cat > Test.al <<'EOF'
codeunit 50100 Probe { trigger OnRun() begin Codeunit.Run(Codeunit::80); end; }
EOF
al compile /project:"$PWD" /out:"$PWD/test.app"; echo "EXIT=$?"
```

Exit `0` + `test.app` written = compiler accepts. No `test.app` is a rejection only if an error is located in the `.al` file; otherwise the project is broken (see below).

**Traps that make a working probe look like a rejection, or a broken one look like a verdict** (alc 18.0.41, re-verified 2026-09-29). Judge by *where* an error is located: an error located in a `.al` file (`...\Test.al(7,15): error AL1073`) is about the source; one located in `app.json` (`...\app.json(1,175): error AL1043`) or unlocated (`error AL1021`, `error AL1028`) is about the project. `tools/alc_probe` classifies exactly that way.
- **Missing symbols read as a real rejection.** An `application` or `dependencies` key is harmless for a self-contained probe (it compiles). But any reference to a Base/System Application object without the symbol packages fails with a `.al`-located **AL0185**, which looks exactly like a genuine REJECT. Keep probes self-contained, or supply real packages via `/packagecachepath:`.
- **Relative paths under Git Bash.** `/project:.` exits `1` with an empty log, but that is MSYS path conversion, not alc: Git Bash rewrites the argument to `C:\Program Files\Git\project;.`. PowerShell, `MSYS_NO_PATHCONV=1`, or absolute Windows paths all work.
- **Runtime.** alc 18.0.41 builds runtimes `12.0` through `18.0`; `19.0` gives `AL1043`, located in `app.json`.
- **`/packagecachepath:` cuts both ways.** Pointed at an EMPTY directory it fails with `AL1022` — omit it and the compiler finds its default cache. But when you have real symbol packages (a 28.0 cache, say), it is REQUIRED: without it alc emits `AL1021`. Check which situation you are in rather than copying either form.
- **One case file at a time.** `al compile` compiles *every* `.al` in the project directory, so a leftover probe file fails the run you are reading.

Sanity-check the probe before trusting a rejection: compile a form you know is valid and confirm exit `0` + `test.app`. If that fails too, the project is broken, not the syntax. Example: confirmed `Codeunit::<integer>` is valid AL (old-school soft cross-extension reference) when both LLMs claimed otherwise.

## Documentation Resources

**Available via MCP:**
- **business-central** — AL Language syntax, objects, properties
- **tree-sitter** — Grammar development guide, API reference

**Project docs:**
- `docs/agent-brief-rules.md` — the checklist every subagent brief links: blocked commands, process, environment and editing rules, and the tools above
- `docs/deferred-work.md` — **open items carried past 4.0.0**, each tagged with how it
  was established. Read this before concluding something is unexplored; it also holds
  the four-way `alc` probe rule that every `#if` question depends on
- `docs/v2-blog-post-notes.md` — V2 rewrite narrative and data
- `docs/superpowers/specs/` — Design specs for major changes
- `docs/database-reference-numeric-id-fix.md` — `Codeunit::N` / `Page::N` numeric ID support
- `docs/preproc-define-undef.md` — `#define`/`#undef` support, compiler-verified accept/reject matrix
- `docs/state-reduction-method.md` — how to cut parser states: measure by stubbing, what
  factorings worked and failed (with numbers), and the preservation gates for roadmap D1

## Where tree-sitter's own source lives

When you need tree-sitter internals (how `valid_symbols` is built, when the external scanner is
called, lex-mode reuse, `test -u` behaviour), read a local copy. **Never search for it with
`find /`**: in Git Bash `/` spans every mounted drive, including the corpora on `H:`, and such
searches have run for hours as orphans after the agent that started them finished.

- `U:/Git/tree-sitter-upstream`: a read-only shallow clone at tag `v0.27.0`, matching the
  installed CLI.
  - `lib/src/` holds the runtime C (`parser.c`, `lexer.c`, `subtree.c`, `language.c`).
  - `crates/cli/src/` holds the CLI (`parse.rs`, the test runner).
  - `crates/generate/` holds the generator (lex modes, conflicts, precedence).
  - `lib/binding_web/` holds web-tree-sitter.
- The runtime crate versions the bindings build against are at
  `~/.cargo/registry/src/index.crates.io-*/tree-sitter-<version>/src`.
- The web-tree-sitter JS is at `node_modules/web-tree-sitter/`.

After a CLI upgrade, move the clone to the new tag:
`git -C U:/Git/tree-sitter-upstream fetch --depth 1 origin tag vX && git -C U:/Git/tree-sitter-upstream checkout vX`.

## Philosophy: No Known Limitations

**Never give up on a failing pattern:**
- Don't disable tests or mark issues as "known limitations"
- Research how other parsers handle similar constructs in `other-languages/`
- Use `error-research` agent for systematic failure analysis
- Every "impossible" pattern has been solved somewhere — find it and adapt it
