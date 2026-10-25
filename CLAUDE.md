# CLAUDE.md

GOAL: A parser which parses AL code CORRECT, not just without errors. That is the first and foremost goal.

Guidance for Claude Code when working on this tree-sitter parser for AL (Microsoft Dynamics 365
Business Central). The `.claude/rules/*.md` files are loaded with this one; they own scanner,
keyword, attribute, debugging and test-failure detail and are not repeated here. One home per
fact: a rule lives here or in a rules file with its one-line why; its history and measurements
live in `docs/` or in the comment at the rule in `grammar.js` / `src/scanner.c`.

**Current numbers (tests, states, parser.c size, success rate) are NOT in this file.** They drift
every branch. Measure them: `./tools/metrics.sh` and `./parse-al-parallel.sh ./BC.History/ .`.
Three different test counts circulated during 4.0.0 and two were arithmetic from a stale copy.

## Git Commit Guidelines

**Always include the error count in commit messages** so a regression is visible in the log:
```
Fix XYZ pattern

[BC.History: 7 errors, 99.95% success]
```
Run the full parse before committing: `./parse-al-parallel.sh ./BC.History/ .`

**Commit all generated files together**: `tree-sitter generate` writes `src/parser.c`,
`src/grammar.json` and `src/node-types.json`, all tracked. Stage them as a set or `grammar.json`
silently drifts.

Subagent briefs link `docs/agent-brief-rules.md` (blocked commands, process, environment, editing rules).

## Quick Reference

```bash
# Validation (run before completing any task)
./validate-grammar.sh        # generation, tests, orphan/duplicate detection, field invariants, oracle quick tier, censuses
./validate-grammar.sh --full # plus production AL parsing and the has_error sweep over it

# Zero-behavior-change gate for refactors (byte-identical parse trees). Take a FRESH baseline,
# named for the change: a stale snapshot reports a huge delta that has nothing to do with your edit.
./tools/tree-harness.sh snapshot ./BC.History .snapshots/baseline-<change>  # ~16s
./tools/tree-harness.sh verify   ./BC.History .snapshots/baseline-<change>  # ~11s

# Query-coverage harness: the CST is lossless and values are queryable
python -m tools.query_coverage.qc run          # regression gate, exits 1 on a new cluster
python -m tools.query_coverage.qc run --all    # full picture
python -m tools.query_coverage.qc accept       # freeze the current state as the baseline

# has_error gate: the ONLY thing that sees a MISSING node for a HIDDEN token (see below)
python tools/has_error_sweep.py --root ./BC.History/   # exit 0 clean, 1 errors, 2 cannot run
python tools/has_error_sweep.py --corpus-fixtures      # every corpus case

# Config oracle (validate-grammar.sh Step 5e, CI job `config-oracle`): exit 0 clean, 1 finding, 2 cannot run
python -m tools.config_oracle run --tier quick  # ~2-3 s
./tools/ts-lock.sh python -m tools.config_oracle run --tier full|resolve --root ./BC.History --root ./DC ...  # full ~22 min
python -m tools.config_oracle replay            # historical-defect replays
# Exit-code gates, root labelling, the two classification tsvs, lowering modules: tools/config_oracle/README.md

# Traversal helper (roadmap F0, docs/traversal.md); Step 5f is the census
python tools/traversal_census.py
./tools/ts-lock.sh python -m pytest tests/traversal -q
python tests/traversal/regen_expected.py      # a -u: review every hunk of the diff

# Separator/continuation audit (B7a, docs/b7-separator-continuation-matrix.md); Step 5g is the census
python -m tools.b7_audit census --check
./tools/ts-lock.sh python -m tools.b7_audit run [--only X] [--check]   # full ~3 h cold; NOT in validate
python -m tools.b7_audit report                 # must be byte-identical to the committed matrix
./tools/ts-lock.sh python -m tools.b7_audit assert --refresh
./tools/ts-lock.sh python -m pytest tools/b7_audit/tests -q   # Step 5h
# After ANY change to src/parser.c, src/scanner.c or tools/config_oracle: `assert --refresh` per fix; a full `run`,
# then `report`, once per batch before merging (docs/agent-brief-rules.md, "Gate tiers").

# Perf (docs/performance-baselines.md). Speed DECISIONS come from `ab`, same session, ABBA; baselines are context.
python -m tools.perf ab --lib-a OLD --lib-b NEW --corpus dc
python -m tools.perf delta                      # structural production delta (B7b-3), tools/perf/delta-reviewed.tsv

# Workflow tools: use these, not ad-hoc versions
python tools/snip.py 'x := a + 1;'                 # cursor tree with fields, has_error, ERROR/MISSING/hidden; --sexp
python tools/snip.py --census --root ./BC.History   # two-shape detector for node types; exit 1 if any flagged
./tools/metrics.sh [--vs REV] [--tests]            # STATE/LARGE_STATE/SYMBOL_COUNT, parser.c size, grammar.js lines, tests
python tools/nodetypes.py show|who-has TYPE        # node-types.json questions; `diff REV`
./tools/corpus-grep.sh [-E|-P] [-i] [-l|-c] PAT    # sites over the four corpora (*.al only)
./tools/session-cleanup.sh --procs [--yes]         # leftover processes older than 30 min

# Development cycle. Always through the lock: `./tools/ts-lock.sh tree-sitter ...`
tree-sitter generate
tree-sitter generate --report-states-for-rule -  # rank rules by parser-state cost
tree-sitter test [-i PAT] [-e PAT] [--file-name F] [-d]
tree-sitter test -u                              # see the traps below
tree-sitter parse file.al -d > debug.log 2>&1    # .claude/rules/debugging.md
```

**Build compiler.** On Windows `tools/default-cc.sh` (sourced by `ts-lock.sh`, `validate-grammar.sh`,
`loader.build_env`) picks clang-cl when LLVM is installed: ~2x faster parsing, identical trees.
`TS_AL_NO_CLANG=1` forces MSVC; an explicit `CC` wins (`CC=cl` only inside a VS developer shell).
Linux/macOS: no change. Details: `docs/deferred-work.md` item 21.

## Gates that catch what the obvious check misses

**A MISSING node for a HIDDEN (`_`-prefixed) token is invisible to `tree-sitter parse`,
`--json-summary` and `parse-al-parallel.sh`**: the file counts as parsed OK. Only
py-tree-sitter's `root_node.has_error` sees it; `tools/has_error_sweep.py` reports such files
as `hidden-only` (validate Step 3b over fixtures, Step 6b under `--full`, CI). **A fix that
touches a hidden token needs this gate over a production corpus, or a `has_error` pytest**
(`tools/config_oracle/tests/test_directive_eol.py` is the model). `tree-sitter test` does print
`(MISSING _hidden)`, so a fixture catches it only if it holds the triggering input. The
deliberate-negative fixture list lives in ONE file, `tools/deliberate-negatives.txt`, read by
validate Step 3, the sweep and the release command.

**Five traps in `tree-sitter test -u`. Each produces a test that passes whether the grammar is right or wrong.**

1. **"No ERRORs" is not a sufficient check.** A tree can be completely wrong without an ERROR
   node; every defect found in 4.0.0 looked like that, and five shipped fixtures asserted a
   defect as correct. Read the whole diff of every file `-u` touched and trace each hunk to
   your change. A hunk you cannot explain is drift being blessed.
2. **`-u` writes NO field labels if the old expectation had none**, and an unlabelled tree
   asserts nothing about fields (comparison is all-or-nothing per file, so adding one label to
   an unlabelled tree fails, which is why the weak form degrades silently). If fields are the
   point, generate the expectation from `tree-sitter parse` and prove the fixture can fail by
   renaming a field to `bogus:`.
3. **A blank line inside a `====` test header drops the case silently.** The name block must be contiguous.
4. **No `---` divider after the header drops the case silently** (`built_in_functions_al.txt`
   had never run once). After adding fixtures, check the suite total moved by exactly the
   number of cases you wrote; counting `=` lines reports the declared count, which is the
   number that disagrees with reality. validate Step 2b is the census.
5. **`-u` rewrites files you did not name** (it stripped trailing blank lines and leading `;`
   rationale blocks from untargeted fixtures). Run `git diff --stat test/corpus` after every
   `-u` and restore what you did not target with `git show HEAD:path > path`.

**Expected ERROR trees come from the CLI, never from `snip`.** py-tree-sitter 0.25 (`snip.py`,
`has_error_sweep.py`, the loader) and the 0.27 CLI recover from errors differently, so the same
bad input gives different ERROR/MISSING shapes. A deliberate-negative witness that only needs
"an error exists" uses the corpus `:error` attribute instead of pinning a recovery tree that
churns on every grammar change (the `test/corpus/b7_gap_*_test.txt` witnesses do this).

**A corpus file can be invisible to git.** An unanchored `.gitignore` pattern once swallowed a
fixture, so the suite count differed between checkouts at the same commit. Check
`git ls-files test/corpus | wc -l` against `find test/corpus -name '*.txt' | wc -l`.

**Executable bits are invisible on Windows** (`core.fileMode=false`): a 100644 script runs
locally and fails on a Linux runner with exit 126 (that kept a CI job red from its first run to
4.1.0). `git ls-files -s` is the only view; `git update-index --chmod=+x <file>` is the fix;
`tools/check-exec-bits.sh` (validate Step 10, and CI) gates every tracked `*.sh` and gate shim.

**A generated artifact can never fail a contract, because it is re-derived from the thing being
tested.** `src/node-types.json` says what the grammar *currently does*; hand-maintained
`tools/check-field-types.py` says what it is *supposed* to do, and it is what gates (Step 5b).
Reading a generated file and calling an invariant verified is necessary, not sufficient.

**"I tried it and it forced N conflicts" measures one edit, not the grammar.** Record which edit
was tried, or a half-finished attempt gets filed as an inherent limit and nobody revisits it.
(`code_block` in `_statement_inner` was recorded as forcing a GLR fork on every `begin`; with
the seven host arms that duplicated it deleted, it had zero conflicts and a smaller parser.)

## Architecture

- `grammar.js`: the grammar. Never edit `src/parser.c` (generated).
- `src/scanner.c`: the external scanner (`.claude/rules/scanner.md` is the token table and the rules).
- `test/corpus/`: AL + expected trees. `queries/`: highlights, locals, tags, indents, folds, textobjects.
- `docs/deferred-work.md`: every open item and measured known limit, tagged with how it was
  established. **Read it before concluding something is unexplored.**

**Design principles (V2).** The comment at the rule in `grammar.js` is the source of truth;
the design record with its measurements is `docs/property-families.md`. This list is the index.

- **Parse structure, don't validate.** Any `Name = Value ;` is a property. Semantic validation
  is a linter's job.
- **Scanner-keyed names.** `PROPERTY_NAME` tells `identifier =` (property) from `identifier :`
  (variable) by lookahead. Five property families are keyed by NAME because the compiler parses
  their value with its own grammar and ours cannot tell it from an expression: `CalcFormula`,
  the 13 ML names, `Namespaces`, `TableRelation`, the six link names (the lists are in
  `src/scanner.c`). **Key a name only from the compiler's tables, never from a naming pattern**
  (`FooML` stays generic; fixtures pin it). Each keyed value may be a whole-value `#if`.
- **One generic `property` rule plus the complex-property rules** (CalcFormula, TableRelation,
  Permissions, link family, view properties, ML, lists, DecimalPlaces, OrderBy, Implementation).
  Add a dedicated rule only when the syntax is beyond `Name = Expression ;`.
- **Property value runs (B11)**: several consecutive `#if` groups at one value site. Generators
  `valueRunRules`, `afterGroupRules`, `afterSequenceRules`, `listOpenerRules` in `grammar.js`;
  read their comments before touching one. Spec
  `docs/superpowers/specs/2026-10-05-property-value-runs-design.md`; witnesses `docs/b11-precedence-audit.md`.
- **Strict conditional lists (B7b-1)**: `strictConditionalList` + `strictListBody` in
  `grammar.js` (the body is inlined, never a hidden `_F_list` rule: the B7a census keys a
  separator by its rule path); oracle registry `FAMILIES` in
  `tools/config_oracle/lowering/conditional_lists.py`. Adding a host: "Host Conversion
  Procedure" in `docs/superpowers/plans/2026-10-07-b7b-1-strict-conditional-lists.md`.
- **A statement's `;` belongs to its host route, not to the statement** (B7b-3, spec
  `docs/superpowers/specs/2026-10-08-b7b-3-statement-terminators-design.md`). `call_statement`
  is a bare name in statement position reached only through `_expression_statement` (its B6
  `prec(-1)` was removed in B7b-2 Phase C; the comment above the rule has the history);
  `empty_statement` IS a `;`. Giving a statement rule its own `;` makes that `;` unreachable
  from an `#if` arm and gives a bare name two shapes.
- **`#if` inside expressions is a transparent region (B7b-2)**: tails, operand prefixes and
  `preproc_conditional_operand` groups at every expression slot. Inside a region that contains
  a group the binary/unary nesting is **not** a grouping claim: splice the active arm, regroup by
  the ladder. Contract, ladder and worked trees: `docs/expression-regions.md`.
- **Generic preprocessor**: ONE `preproc_conditional` plus the `preproc_split_*` rules for
  constructs torn across arms. Line directives (`pragma`, `region`, `define`, ...) are `extras`
  and never touch the scanner depth (`docs/preproc-define-undef.md`).
- **Named keywords, uniform shape**: every grammar keyword rule is `alias(kw('w'), 'w')`, or
  `kwCases(...)` for the 13 object-declaration keywords (its spelling whitelist is load-bearing);
  `begin`/`end` are scanner-exclusive. Rules: `.claude/rules/contextual-keywords.md`; the
  two-shape audit and its numbers: `docs/keyword-shape-audit.md`.
- **Reserved-word sets** (`reserved:` in `grammar.js`): `global` is empty on purpose;
  `implementation_names`, `relation_target_names`, `code_names` are contextual. Two rules the
  tree-sitter docs do not state, both measured while fixing issue #20: an entry must be a rule
  **symbol** (`$._true_token`), not a fresh `kw()`; and a parse state takes the largest set among
  items whose **next step is `identifier` itself**, so the set must sit on a rule that names
  `$.identifier` directly; wrapping a reference to `_identifier_or_quoted` reserves nothing.
- **Attributes are first-class siblings** of declarations (`.claude/rules/attributes.md`).
- **Stateful scanner, single-read identifier dispatch** (`.claude/rules/scanner.md`; the
  defects behind the rules: `docs/scanner-design-notes.md`).

## Testing

```
========================================================================
Test Description
========================================================================
[AL source code]
------------------------------------------------------------------------
(expected_parse_tree)
```

- Never delete or disable a test file; fix the underlying issue.
- `-u` only when there are no ERROR/MISSING nodes AND you have read the diff (traps above).
- Create a fixture for each new grammar feature; a deliberate negative goes in `tools/deliberate-negatives.txt`.
- **BC.History (15,358 production files) is the real validation gate**; tests are a development aid.
- Adding a construct: study it (business-central MCP, or `al compile` below), look for an existing
  pattern in `grammar.js`, add the rule (and scanner token if needed), fixture,
  `./validate-grammar.sh`, then BC.History.

## Validating AL Syntax Questions

When unsure whether the compiler accepts a construct, **`al compile` is the ground truth**, not
recall or web search. **For anything with `#if`, use the four-way probe tool, not a hand recipe:**

```bash
python -m tools.alc_probe run my_probe.al                    # every symbol assignment, split AND flat
python -m tools.alc_probe run tools/alc_probe/cases --check  # the committed, recorded verdicts
```

It compiles each symbol assignment twice (the file as written, and the oracle resolver's flat
text), runs a valid and a garbage control first, and reports a broken project as `BROKEN`
(exit 2) instead of a rejection, a flat/split disagreement as `MISMATCH`. Commit a probe whose
verdict matters under `tools/alc_probe/cases/<family>/` with `// expect:` and `// source:`
headers. `tools/alc_probe/README.md` has the manual project recipe the tool automates.

**Traps that make a working probe look like a rejection, or a broken one look like a verdict**
(alc 18.0.41, re-verified 2026-09-29). Judge by *where* an error is located: in a `.al` file
(`Test.al(7,15): error AL1073`) it is about the source; in `app.json` (`AL1043`) or unlocated
(`AL1021`, `AL1028`) the project is broken. `tools/alc_probe` classifies exactly that way.
- **Missing symbols read as a real rejection.** A reference to a Base/System object without
  the symbol packages fails with a `.al`-located **AL0185** that looks exactly like a REJECT.
  Keep probes self-contained, or supply real packages via `/packagecachepath:`.
- **Relative paths under Git Bash.** `/project:.` exits 1 with an empty log: MSYS path
  conversion, not alc. Use absolute Windows paths, PowerShell, or `MSYS_NO_PATHCONV=1`.
- **Runtime.** alc 18.0.41 builds `12.0` through `18.0`; `19.0` gives `AL1043`, located in `app.json`.
- **`/packagecachepath:` cuts both ways.** At an EMPTY directory it fails with `AL1022`; omit it
  and alc finds its default cache. With real symbol packages it is REQUIRED (`AL1021` without).
- **One case file at a time.** `al compile` compiles every `.al` in the project directory.
Sanity-check the probe with a form you know is valid before trusting a rejection (this is how
`Codeunit::<integer>` was confirmed valid when two LLMs claimed otherwise).

## Documentation Resources

MCP: **business-central** (AL syntax, objects, properties), **tree-sitter** (grammar guide, API).

- `docs/agent-brief-rules.md`: the checklist every subagent brief links.
- `docs/deferred-work.md`: open items and measured known limits, each tagged with its evidence,
  and the four-way `alc` probe rule every `#if` question depends on.
- `docs/property-families.md`: the V2 design record (keyed families, B11, B7b-1, B7b-3, preprocessor).
- `docs/keyword-shape-audit.md`, `docs/scanner-design-notes.md`: the histories behind the two rules files.
- `docs/superpowers/specs/`, `docs/superpowers/plans/`: design specs and plans for the B-phases.
- `docs/state-reduction-method.md`: how to cut parser states, with numbers.
- `docs/expression-regions.md`: the B7b-2 transparent-region contract for `#if` inside expressions.
- `docs/performance-baselines.md`, `docs/traversal.md`, `docs/b7-separator-continuation-matrix.md`,
  `docs/preproc-define-undef.md`, `docs/database-reference-numeric-id-fix.md`.
- `docs/v2-blog-post-notes.md`: the V2 rewrite narrative and data.

**tree-sitter's own source.** Read a local copy; **never `find /`** (in Git Bash `/` spans every
drive, and such searches ran for hours as orphans). On the Windows host:
`U:/Git/tree-sitter-upstream` is a read-only shallow clone at the installed CLI's tag
(`lib/src/` runtime C, `crates/cli/src/` the CLI and test runner, `crates/generate/` the
generator, `lib/binding_web/` web-tree-sitter); the runtime crates the bindings build against
are under `~/.cargo/registry/src/index.crates.io-*/tree-sitter-<version>/src`; the
web-tree-sitter JS is in `node_modules/web-tree-sitter/`. After a CLI upgrade:
`git -C U:/Git/tree-sitter-upstream fetch --depth 1 origin tag vX && git -C U:/Git/tree-sitter-upstream checkout vX`.
On a Linux container these may be absent; say so instead of searching.

## Known limits are recorded, not denied

Every failing pattern alc accepts is a defect to fix, and the bar is correctness, not a clean
error count. Never disable or delete a test to make a pattern "known"; use the
`tree-sitter-pattern-investigator` and `error-research` agents for systematic analysis before
calling anything impossible. A limit that has been MEASURED and accepted by the user (a
quadratic case, an over-acceptance alc would reject) is recorded as a numbered item in
`docs/deferred-work.md` with its evidence and a fixture or gate that pins it. An item there is a
decision, not a surrender, and it is where to look before concluding something is unexplored.
