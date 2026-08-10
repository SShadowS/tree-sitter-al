# Scanner and Grammar Defect Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the six already-fixed external-scanner defects as 3.3.1, then fix the ten remaining defects — nine in `grammar.js` and one in `src/scanner.c` — plus four minor cleanups and two tooling false-positives, as 3.4.0.

**Architecture:** Every defect was found by review, not by the corpus: BC.History (15,358 files) and DO.Support-Agents (20,596 files) contain zero instances of any of them, so 100% parse success never flagged them. Three of the grammar defects produce a *wrong tree with no ERROR node*, which the project's error-count gates (`parse-al-parallel.sh`, `validate-grammar.sh`) structurally cannot detect. Every task therefore pins the corrected **node structure** in a `test/corpus/*.txt` fixture, not just an error count, and uses `tools/tree-harness.sh` to enumerate exactly which production trees change.

**Tech Stack:** tree-sitter CLI 0.26.12, C external scanner, JavaScript grammar DSL, `al compile` (alc 18.0.37) as syntax ground truth.

## Global Constraints

- **tree-sitter CLI must be exactly 0.26.12.** CI resolves this via `tree-sitter/setup-action/cli@v2`; a different local version regenerates a different `src/parser.c` and fails CI's `git diff --exit-code` on all three platforms. Check with `tree-sitter --version`; install with `cargo binstall tree-sitter-cli@0.26.12 -y`.
- **Commit generated files as a set.** `tree-sitter generate` writes `src/parser.c`, `src/grammar.json` and `src/node-types.json`; all three are tracked. Staging a subset makes `grammar.json` drift.
- **Every commit message ends with the error-count trailer**, e.g. `[BC.History: 0 errors, 100% success]` — version-bump commits included. Task 1's Step 6 originally omitted it and was corrected; do not repeat that in Task 14.
- **The CI fuzz job only runs when the pushed HEAD's own diff touches `src/scanner.c`.** `.github/workflows/ci.yml:53-56` gates on `git diff --quiet HEAD^ -- src/scanner.c`. A task that commits a scanner change and then a second commit on top ships with the fuzzer skipped. When a task changes `src/scanner.c`, push the scanner commit **alone** first, let CI fuzz it, then push the rest.
- **NEVER rewrite history on this branch. A second Claude session is committing to `fix/3.4.0-grammar-defects` concurrently.** No `git commit --amend`, no `rebase`, no `reset --hard`, no force-push, no `git checkout --` over their paths. Their commits interleave with ours — `a9547d6`'s git parent is one of theirs — so an amend that was safe an hour ago can now rewrite history underneath work we do not own and cannot recover. Corrections go in as **new commits**, always. This overrides any earlier instruction in this plan that said to amend.
  - Their files, hands off: `docs/superpowers/specs/2026-08-09-query-coverage-harness-design.md`, `docs/superpowers/plans/2026-08-09-query-coverage-harness.md`.
  - Their commits so far: `ccbc9f7`, `919226a`, `cb347b0`, `a5b3fed`. All four verified present and ancestors of HEAD.
  - Scope every review to **explicit SHAs, never a commit range** — a range sweeps in their work and puts unreviewed commits inside our review package.
  - Git authorship cannot distinguish us: every commit in this repo is "Goose Assistant". Attribute by which files a commit touches, not by author.
- **Never delete or disable a test file.** Fix the underlying issue.
- **Parse structure, don't validate.** Do not add semantic validation. Over-permissiveness is only a defect when it produces a *wrong* tree.
- **`al compile` is ground truth** for whether AL accepts a construct. It only works with ABSOLUTE paths — `al compile /project:. …` exits 1 with an empty error log. Working probe lives in the scratchpad; see "Compiler probe" below.
- **`tree-sitter parse` needs the repo as cwd and an absolute path to the `.al` file**, else it fails with "No language found".

### Compiler probe

A working probe project exists. To recreate it:

```bash
P="$SCRATCH/al-probe"
mkdir -p "$P/.alpackages"
cp /c/Users/SShadowS/.claude/jobs/1dc081f2/tmp/scopecompile/.alpackages/System.app "$P/.alpackages/"
cat > "$P/app.json" <<'EOF'
{"id":"11111111-2222-3333-4444-555555555555","name":"Probe","publisher":"Test",
 "version":"1.0.0.0","platform":"1.0.0.0",
 "idRanges":[{"from":50000,"to":99999}],"runtime":"15.0","target":"OnPrem"}
EOF
```

Run one case at a time (the compiler compiles every `.al` in the project dir):

```bash
cp case.al "$P/Test.al"
al compile "/project:$P" "/out:$P/out.app" "/packagecachepath:$P/.alpackages"
```

Exit 0 plus `out.app` written means the compiler accepts it. Note the `app.json` above omits `"application"` — including it requires the Microsoft Application symbol package and fails with `AL1022`.

### Current harness baseline

**`.snapshots/baseline-task16`** — manifest `208ff0658b5fe590`, taken after Task 16 routed single-entry link properties through `link_value` (880 files changed). Earlier baselines left in place: `baseline-task12` (`f6583378f002124c`, post-Task-12), `baseline-task9` (`28c72f6a554a479f`, post-Task-9).

Any task text below that names `.snapshots/baseline-3.3.1`, `.snapshots/baseline-3.4.0-wip` or `<current-baseline>` means whatever this line currently points at. Update it whenever a task legitimately moves production trees and you re-snapshot.

**Harness cost, measured at `671e313`** so you know what you are committing to before running it: `snapshot` 46.7s; `verify` with no changes 26.0s; `verify` with a 757-file delta 3m 03s (it was 25m 52s before Task 13a). Run at `NUM_THREADS` between 6 and 16 — at 32 it desyncs and aborts with "tree count mismatch". Redirect output to a file; the harness emits everything at the end and a backgrounded pipeline loses it.

### The three validation gates

```bash
# 1. Test suite
tree-sitter test

# 2. Production corpora (error count)
./parse-al-parallel.sh ./BC.History/ .
./parse-al-parallel.sh "U:/Git/DO.Support-Agents/" .

# 3. Tree diff — enumerates every production tree whose shape or span changed
NUM_THREADS=16 ./tools/tree-harness.sh verify ./BC.History .snapshots/baseline-3.3.1
```

Gate 3 is the one that catches silent changes. Run it at **`NUM_THREADS` between 6 and 16** — at 32 it desyncs and aborts with "tree count mismatch". Redirect its output to a file (`> out.txt 2>&1`) rather than piping to `tail`; the harness emits everything at the end and a backgrounded pipeline loses it.

After any task that intentionally changes production trees, **re-snapshot** so the next task starts from a clean baseline:

```bash
NUM_THREADS=16 ./tools/tree-harness.sh snapshot ./BC.History .snapshots/baseline-<version>
```

---

## File Structure

| File | Responsibility | Tasks |
|---|---|---|
| `src/scanner.c` | External scanner. Already carries the six 3.3.1 fixes. Task 12 adds depth>0 named begin/end. | 1, 12 |
| `grammar.js` | All nine grammar defects and three of the four minors. | 3–11 |
| `test/corpus/exit_statement_spacing_test.txt` | New. Pins `exit (42)`. | 3 |
| `test/corpus/quoted_identifier_call_test.txt` | New. Pins `"My Proc"(42)`. | 4 |
| `test/corpus/preproc_expression_parens_test.txt` | New. Pins `#if (FOO)` and multi-space `#  elif`. | 5, 6 |
| `test/corpus/field_shape_audit_test.txt` | New. Pins the three field-shape fixes. | 7, 8, 9 |
| `test/corpus/keyword_case_insensitivity_test.txt` | New. Pins mixed-case keywords and operators. | 11 |
| `test/corpus/preproc_begin_end_named_test.txt` | New. Pins named begin/end inside `#if`. | 12 |
| `validate-grammar.sh` | Two false-positive checks. | 13 |
| `.claude/commands/release.md` | Pre-flight check #3 can never pass. | 13 |
| `CHANGELOG.md` | Entry per task. | all |

---

## Task 1: Ship 3.3.1 — the six scanner fixes

The scanner work is complete in the working tree and all three gates are green (1489/1489 tests; 15358/15358 and 20596/20596 at 0 errors; harness delta is 53 files, span-only, enumerated below). This task commits and releases it.

**Files:**
- Modify: `src/scanner.c` (already edited — do not re-edit)
- Modify: `CHANGELOG.md` (already has the `[Unreleased]` entry — retitle only)
- Modify: `package.json`, `Cargo.toml`, `tree-sitter.json`, `package-lock.json`, `Cargo.lock`
- Modify: `tree-sitter-al.wasm`
- Test: `test/corpus/scanner_lookahead_extras_test.txt` (already written, 7 tests passing)

**Interfaces:**
- Consumes: nothing.
- Produces: `.snapshots/baseline-3.3.1` — the harness baseline every later task verifies against. Also `skip_comment(TSLexer*) -> bool`, `skip_whitespace_nomark(TSLexer*) -> void`, `skip_whitespace_and_comments(TSLexer*) -> bool`, and `peek_directive_ci_skip_extras(TSLexer*, const char *const *targets) -> bool`, all in `src/scanner.c`, used by Task 12.

**The harness delta this release carries** (it is NOT byte-identical, deliberately): 53 files, 75 `preproc_split_begin` nodes and 24 `preproc_fragmented_else_tail` parents, all span-only. Every old `preproc_split_begin` span was zero-width; they now cover the 5-byte `begin`. Zero other changed lines. Cause: `lexer->advance(lexer, true)` unconditionally resets the token's *start* offset, so a marking skip that runs after the token text has been consumed drags the start past the end.

- [ ] **Step 1: Confirm the three gates are still green**

```bash
tree-sitter --version                       # must print 0.26.12
tree-sitter generate && git diff --exit-code --stat src/   # must be clean
tree-sitter test                            # 1489/1489
./parse-al-parallel.sh ./BC.History/ .      # 15358/15358, 0 errors
```

- [ ] **Step 2: Commit the scanner work**

```bash
git add src/scanner.c src/parser.c src/grammar.json src/node-types.json \
        test/corpus/scanner_lookahead_extras_test.txt CHANGELOG.md \
        docs/preproc-define-undef.md
git add -f .claude/rules/scanner.md
git commit -F- <<'EOF'
fix(scanner): step lookaheads over comments, and stop marking after mark_end

Six defects, all pre-existing, none reachable from BC.History or
DO.Support-Agents — which is why 100% parse success never flagged them.

Comments are `extras` exactly like #pragma/#region, but every hand-rolled
lookahead treated only directives as transparent. PREPROC_SPLIT_BEGIN declined
on a trailing comment (4 ERROR nodes where the same file without the comment
parsed clean). PREPROC_SPLIT_END skipped nothing at all, and failed SILENTLY:
`end; // note` before #else dropped the token and reparsed the run as a
call_statement with ZERO error nodes, invisible to both error-count gates.

PREPROC_SPLIT_END's #endif arm was unreachable — `read_keyword_ci("else") ||
read_keyword_ci("endif")` burns the shared 'e' on the failed else attempt. The
rewritten helper takes a target set and tests all of them against one buffered
read of the directive word.

VAR_ATTRIBUTE_OPEN declined a quoted name leading a multi-name declaration and
was blind to a ']' inside a comment. PROPERTY_NAME rejected a newline before
'=' (its skip listed '\r' but not '\n' while the leading skip included it);
alc accepts that form.

Also fixes a token-span bug the above exposed: advance(lexer, true) resets the
token START offset, so a marking skip after mark_end collapses the node to zero
width. preproc_split_begin was rendering zero-width in all 75 BC.History
occurrences and now covers the 5-byte `begin`. This is the release's only
production tree change: 53 files, span-only, no structural difference.

Removed: peek_keyword_ci (never called), paren_depth (write-only), and a
comment claiming the scanner is re-entered for the same position after a false
return (it is not).

[BC.History: 0 errors, 100% success]
EOF
```

- [ ] **Step 3: Retitle the changelog entry**

In `CHANGELOG.md`, change `## [Unreleased]` to `## [3.3.1] — 2026-08-09`.

- [ ] **Step 4: Bump the version in all three files plus both lockfiles**

```bash
sed -i 's/"version": "3.3.0"/"version": "3.3.1"/' package.json tree-sitter.json
sed -i '0,/^version = "3.3.0"/s//version = "3.3.1"/' Cargo.toml
npm install --package-lock-only
cargo check
```

- [ ] **Step 5: Regenerate — the version is embedded in parser.c**

```bash
tree-sitter generate
git diff --stat src/parser.c    # expect the metadata minor/patch lines to change
```

`src/parser.c` carries `.minor_version` / `.patch_version` from `tree-sitter.json`. Skipping this fails CI.

- [ ] **Step 6: Rebuild the WASM and commit the release prep**

```bash
tree-sitter build --wasm
git add package.json tree-sitter.json Cargo.toml package-lock.json Cargo.lock \
        CHANGELOG.md src/parser.c tree-sitter-al.wasm
git commit -m "chore: bump version to 3.3.1"
```

- [ ] **Step 7: Push and wait for CI**

```bash
git push
gh run list --workflow ci.yml --limit 1
gh run watch <RUN_ID> --exit-status
```

All five jobs must be green: Validate queries, Fuzz scanner, Test parser on ubuntu/macos/windows.

- [ ] **Step 8: Tag — this is what publishes**

```bash
git tag v3.3.1
git push origin v3.3.1
```

The tag must be pushed from a developer machine. A CI-created tag uses `GITHUB_TOKEN` and GitHub suppresses its workflow triggers, so nothing would fire.

- [ ] **Step 9: Watch all three publish workflows, then dispatch the release binaries**

```bash
gh run list --limit 3          # Publish npm / Python / Rust, all triggered by the tag
gh workflow run "Build and release artifacts" --ref main
```

- [ ] **Step 10: Verify all four channels**

```bash
gh release view v3.3.1 --json tagName,assets
npm view @sshadows/tree-sitter-al version
curl -s -H "User-Agent: release-check" https://crates.io/api/v1/crates/tree-sitter-al/versions
curl -s https://pypi.org/pypi/tree-sitter-al/json
```

npm and PyPI sit behind a CDN. A stale read is not a failed publish — re-check after a minute.

- [ ] **Step 11: Snapshot the new baseline**

```bash
NUM_THREADS=16 ./tools/tree-harness.sh snapshot ./BC.History .snapshots/baseline-3.3.1
```

---

## Task 2: Open the 3.4.0 changelog section

**Files:**
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: Task 1's released `3.3.1` heading.
- Produces: an `## [Unreleased]` section that Tasks 3–13 each append a bullet to.

- [ ] **Step 1: Insert the section**

Immediately above `## [3.3.1] — 2026-08-09`, insert:

```markdown
## [Unreleased]

### Fixed

### Removed

```

- [ ] **Step 2: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): open the 3.4.0 section"
```

---

## Task 3: `exit (42)` with a space silently drops the return value

`grammar.js:3589` uses `token.immediate('(')`, so a space between `exit` and `(` splits the statement into a bare `(exit_statement)` plus a detached sibling `(parenthesized_expression (integer))`. The return value falls off. **No ERROR node** — this is one of the three silent misparses. alc accepts the spaced form (verified: exit 0, `out.app` written).

**Files:**
- Modify: `grammar.js:3587-3594`
- Test: `test/corpus/exit_statement_spacing_test.txt` (create)

**Interfaces:**
- Consumes: `.snapshots/baseline-3.3.1` from Task 1.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Write the failing test**

Create `test/corpus/exit_statement_spacing_test.txt`:

```
================================================================================
exit with a space before the parenthesis keeps its return value
================================================================================
codeunit 1 T { procedure X() : Integer begin exit (42); end; }
--------------------------------------------------------------------------------

(source_file
  (codeunit_declaration
    (codeunit_keyword)
    object_id: (integer)
    object_name: (identifier)
    body: (declaration_body
      (procedure
        (procedure_keyword)
        name: (identifier)
        return_type: (type_specification
          (basic_type))
        body: (code_block
          (begin_keyword)
          body: (statement_block
            (exit_statement
              (exit_keyword)
              return_value: (integer)))
          (end_keyword))))))
```

- [ ] **Step 2: Run it and confirm it fails**

```bash
tree-sitter test --file-name "exit_statement_spacing_test.txt"
```

Expected: FAIL. Actual tree has `(exit_statement (exit_keyword))` followed by a sibling `(parenthesized_expression (integer))`.

- [ ] **Step 3: Replace `token.immediate` with a plain literal**

In `grammar.js`, change:

```javascript
    exit_statement: $ => prec(13, seq(
      $.exit_keyword,
      optional(seq(
        token.immediate('('),
        optional(field('return_value', $._expression)),
        ')'
      ))
    )),
```

to:

```javascript
    // The '(' is a PLAIN literal, never token.immediate. AL tokenization is
    // whitespace-insensitive between tokens and alc accepts `exit (42);`
    // (verified against alc 18.0.37). With token.immediate the spaced form
    // parsed SILENTLY as a bare exit_statement plus a detached sibling
    // parenthesized_expression — the return value fell off with no ERROR node.
    exit_statement: $ => prec(13, seq(
      $.exit_keyword,
      optional(seq(
        '(',
        optional(field('return_value', $._expression)),
        ')'
      ))
    )),
```

- [ ] **Step 4: Regenerate and re-run**

```bash
tree-sitter generate
tree-sitter test --file-name "exit_statement_spacing_test.txt"
```

Expected: PASS.

`tree-sitter generate` WILL report a conflict here — removing `token.immediate` makes `exit` followed by `(` genuinely ambiguous between continuing `exit_statement`'s optional group and reducing a bare `exit_statement` before a new parenthesized-expression statement:

```
Possible interpretations:
  1: ...(exit_statement exit_keyword • '(' ')') (precedence: 13)
  2: ...(exit_statement exit_keyword • '(' _expression ')') (precedence: 13)
  3: ...(exit_statement exit_keyword) • '(' … (precedence: 13)
```

**Raising the precedence on the nested `optional(...)` group does NOT work** — verified: `optional(prec(14, seq('(', …)))` produces the byte-identical conflict, still reporting precedence 13 on all three interpretations, because a `prec` buried inside an `optional` does not reach the conflicting item. Do not restore `token.immediate` either; that is the defect.

Resolve it by attaching the precedence to top-level `choice` alternatives, so the two parses carry genuinely different precedences:

```javascript
    // The '(' is a PLAIN literal, never token.immediate — alc accepts
    // `exit (42);` and with token.immediate the spaced form parsed SILENTLY as
    // a bare exit_statement plus a detached sibling parenthesized_expression,
    // dropping the return value with no ERROR node.
    //
    // The two forms are separate choice alternatives with DIFFERENT precedences
    // rather than one seq with an optional group. `exit` followed by `(` is
    // genuinely ambiguous (continue the exit vs. reduce and start a
    // parenthesized-expression statement); the parenthesised alternative must
    // win. prec() nested inside optional() does not reach the conflicting item
    // and leaves the conflict unresolved — attach it at the alternative.
    exit_statement: $ => choice(
      prec(14, seq(
        $.exit_keyword,
        '(',
        optional(field('return_value', $._expression)),
        ')'
      )),
      prec(13, $.exit_keyword)
    ),
```

- [ ] **Step 5: Run all three gates**

```bash
tree-sitter test
./parse-al-parallel.sh ./BC.History/ .
NUM_THREADS=16 ./tools/tree-harness.sh verify ./BC.History .snapshots/baseline-3.3.1 > /tmp/h.txt 2>&1
grep -c '=== CHANGED:' /tmp/h.txt
```

**The harness reports exactly ONE changed file, and that is the fix working.** `BaseApp/Source/Base Application/Sales/Document/SalesLineReserve.Codeunit.al` — `VerifyPickedQtyReservToInventory` writes `exit` with its parenthesised condition on the NEXT line. Verified against the baseline tree archive:

```
OLD:  (exit_statement [705,8]-[705,12])              <- the word "exit" alone
      (parenthesized_expression [706,12]-[708,145])  <- detached sibling
NEW:  (exit_statement [705,8]-[708,145]
        return_value: (logical_expression [706,13]-[708,144] ...))
```

Every release up to and including 3.3.1 dropped that function's entire three-line boolean return condition out of the `exit_statement`, with no ERROR node. Confirm the delta is that one file and that its diff has this shape, then re-snapshot. **If any OTHER file changed, stop and read it.**

- [ ] **Step 6: Commit**

```bash
git add grammar.js src/parser.c src/grammar.json src/node-types.json \
        test/corpus/exit_statement_spacing_test.txt CHANGELOG.md
git commit -m "fix(grammar): keep the return value on a spaced exit (…)

token.immediate('(') split \`exit (42);\` into a bare exit_statement and a
detached parenthesized_expression sibling — the return value silently fell off
with no ERROR node. alc accepts the spaced form.

[BC.History: 0 errors, 100% success]"
```

---

## Task 4: quoted-identifier calls are not recognised

`call_expression`'s `function` choice (`grammar.js:3757-3765`) omits `$.quoted_identifier`. `"My Proc"(42);` splits into `(quoted_identifier)` plus `(parenthesized_expression (integer))` with **no ERROR node**; `"My Proc"();` yields a MISSING identifier. alc accepts both. The parenless `call_statement` already accepts quoted identifiers, which is what makes this an omission rather than a design decision.

**Files:**
- Modify: `grammar.js:3757-3765`
- Test: `test/corpus/quoted_identifier_call_test.txt` (create)

**Interfaces:**
- Consumes: `.snapshots/baseline-3.3.1`.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Write the failing test**

Create `test/corpus/quoted_identifier_call_test.txt`:

```
================================================================================
Call to a quoted-identifier procedure with an argument
================================================================================
codeunit 1 T { procedure X() begin "My Proc"(42); end; }
--------------------------------------------------------------------------------

(source_file
  (codeunit_declaration
    (codeunit_keyword)
    object_id: (integer)
    object_name: (identifier)
    body: (declaration_body
      (procedure
        (procedure_keyword)
        name: (identifier)
        body: (code_block
          (begin_keyword)
          body: (statement_block
            (call_expression
              function: (quoted_identifier)
              arguments: (argument_list
                (integer))))
          (end_keyword))))))

================================================================================
Call to a quoted-identifier procedure with no arguments
================================================================================
codeunit 1 T { procedure X() begin "My Proc"(); end; }
--------------------------------------------------------------------------------

(source_file
  (codeunit_declaration
    (codeunit_keyword)
    object_id: (integer)
    object_name: (identifier)
    body: (declaration_body
      (procedure
        (procedure_keyword)
        name: (identifier)
        body: (code_block
          (begin_keyword)
          body: (statement_block
            (call_expression
              function: (quoted_identifier)
              arguments: (argument_list)))
          (end_keyword))))))
```

- [ ] **Step 2: Run it and confirm it fails**

```bash
tree-sitter test --file-name "quoted_identifier_call_test.txt"
```

Expected: FAIL on both — the first splits into two siblings, the second reports MISSING.

- [ ] **Step 3: Add `quoted_identifier` to the function choice**

```javascript
    call_expression: $ => prec(12, seq(
      field('function', choice(
        $.identifier,
        $.quoted_identifier,      // "My Proc"(42) — alc accepts; call_statement
                                  // already allowed this, call_expression did not
        $.member_expression,
        $.qualified_enum_value,
        $.keyword_identifier,     // System(), Dialog(), etc.
        $.subscript_expression,   // X[1]()
      )),
      field('arguments', $.argument_list)
    )),
```

- [ ] **Step 4: Regenerate and re-run**

```bash
tree-sitter generate
tree-sitter test --file-name "quoted_identifier_call_test.txt"
```

Expected: PASS.

- [ ] **Step 5: Run all three gates and re-baseline if trees changed**

```bash
tree-sitter test
./parse-al-parallel.sh ./BC.History/ .
NUM_THREADS=16 ./tools/tree-harness.sh verify ./BC.History .snapshots/baseline-3.3.1 > /tmp/h.txt 2>&1
grep -c '=== CHANGED:' /tmp/h.txt
```

If files changed, they are production sites that were silently misparsing. Read three of the diffs and confirm each old tree is the split `quoted_identifier` + `parenthesized_expression` shape and each new one is a `call_expression`. Then re-snapshot:

```bash
NUM_THREADS=16 ./tools/tree-harness.sh snapshot ./BC.History .snapshots/baseline-3.4.0-wip
```

and use `.snapshots/baseline-3.4.0-wip` for the remaining tasks.

- [ ] **Step 6: Commit**

```bash
git add grammar.js src/parser.c src/grammar.json src/node-types.json \
        test/corpus/quoted_identifier_call_test.txt CHANGELOG.md
git commit -m "fix(grammar): accept a quoted identifier as a call target

call_expression's function choice omitted quoted_identifier, so \"My Proc\"(42)
split silently into a quoted_identifier and a detached parenthesized_expression.
call_statement already accepted the form.

[BC.History: 0 errors, 100% success]"
```

---

## Task 5: parenthesized preprocessor conditions

`_preproc_expression` (`grammar.js:2869-2874`) has only bare identifiers as atoms, so `#if (FOO)` and `#if not (FOO and BAR)` fail to parse their condition and push the `(…)` into the branch as an expression statement. alc accepts both.

**Correction, established during implementation:** the pre-fix shape is ERROR nodes, not `(MISSING identifier)` — the `(` and `)` each become a detached ERROR and the condition falls back to the next identifier. The `MISSING` description came from the original grammar review and was wrong; three ERROR nodes is what the parser actually produces. This matters only for recognising the failing state, not for the fix.

**Files:**
- Modify: `grammar.js:2869-2874`
- Test: `test/corpus/preproc_expression_parens_test.txt` (create)

**Interfaces:**
- Consumes: the current baseline (`.snapshots/baseline-3.3.1` or `-3.4.0-wip`).
- Produces: `preproc_parenthesized_expression` node type, referenced by nothing else.

- [ ] **Step 1: Write the failing test**

Create `test/corpus/preproc_expression_parens_test.txt`:

```
================================================================================
Parenthesized preprocessor condition
================================================================================
#if (FOO)
codeunit 1 T { }
#endif
--------------------------------------------------------------------------------

(source_file
  (preproc_conditional_object
    (preproc_if
      (preproc_open)
      condition: (preproc_parenthesized_expression
        (identifier)))
    (codeunit_declaration
      (codeunit_keyword)
      object_id: (integer)
      object_name: (identifier))
    (preproc_endif
      (preproc_close))))

================================================================================
Parenthesized preprocessor condition under not
================================================================================
#if not (FOO and BAR)
codeunit 1 T { }
#endif
--------------------------------------------------------------------------------

(source_file
  (preproc_conditional_object
    (preproc_if
      (preproc_open)
      condition: (preproc_not_expression
        (preproc_parenthesized_expression
          (preproc_and_expression
            (identifier)
            (identifier)))))
    (codeunit_declaration
      (codeunit_keyword)
      object_id: (integer)
      object_name: (identifier))
    (preproc_endif
      (preproc_close))))
```

- [ ] **Step 2: Run it and confirm it fails**

```bash
tree-sitter test --file-name "preproc_expression_parens_test.txt"
```

Expected: FAIL with `(MISSING identifier)` in the condition.

- [ ] **Step 3: Add the parenthesized alternative**

```javascript
    _preproc_expression: $ => choice(
      $.identifier,
      $.preproc_parenthesized_expression,
      $.preproc_not_expression,
      $.preproc_or_expression,
      $.preproc_and_expression,
    ),

    // `#if (FOO)` and `#if not (FOO and BAR)` — alc accepts both. Without this
    // the condition was a MISSING identifier and the `(…)` leaked into the
    // branch body as an expression statement.
    preproc_parenthesized_expression: $ => seq(
      '(', $._preproc_expression, ')'
    ),
```

- [ ] **Step 4: Regenerate and re-run**

```bash
tree-sitter generate
tree-sitter test --file-name "preproc_expression_parens_test.txt"
```

Expected: PASS. If the expected trees differ from the actual in *nesting* (not in ERROR/MISSING), update the fixture with `tree-sitter test -u --file-name "preproc_expression_parens_test.txt"` — but only after confirming the actual output has no ERROR or MISSING node.

- [ ] **Step 5: Run all three gates**

```bash
tree-sitter test
./parse-al-parallel.sh ./BC.History/ .
NUM_THREADS=16 ./tools/tree-harness.sh verify ./BC.History .snapshots/<current-baseline> > /tmp/h.txt 2>&1
```

- [ ] **Step 6: Commit**

```bash
git add grammar.js src/parser.c src/grammar.json src/node-types.json \
        test/corpus/preproc_expression_parens_test.txt CHANGELOG.md
git commit -m "feat(preproc): accept parenthesized preprocessor conditions

#if (FOO) and #if not (FOO and BAR) both compile under alc but produced a
MISSING identifier condition and leaked the parenthesized group into the branch
body.

[BC.History: 0 errors, 100% success]"
```

---

## Task 6: `#  elif` with more than one space

`preproc_elif` and `preproc_else` (`grammar.js:2902-2909`) spell out only the zero-space and one-space variants, while scanner-owned `#if`/`#endif` accept `[ \t]*`. `#  elif BAR` is an ERROR; alc accepts it.

**Files:**
- Modify: `grammar.js:2902-2909`
- Test: `test/corpus/preproc_expression_parens_test.txt` (append)

**Interfaces:**
- Consumes: the current baseline.
- Produces: nothing.

- [ ] **Step 1: Append the failing tests**

Append to `test/corpus/preproc_expression_parens_test.txt`:

```
================================================================================
#elif and #else tolerate any horizontal whitespace after the #
================================================================================
codeunit 1 T
{
#if FOO
    procedure A() begin end;
#  elif BAR
    procedure B() begin end;
#	else
    procedure C() begin end;
#endif
}
--------------------------------------------------------------------------------

(source_file
  (codeunit_declaration
    (codeunit_keyword)
    object_id: (integer)
    object_name: (identifier)
    body: (declaration_body
      (preproc_conditional
        (preproc_if
          (preproc_open)
          condition: (identifier))
        (procedure
          (procedure_keyword)
          name: (identifier)
          body: (code_block))
        (preproc_elif
          condition: (identifier))
        (procedure
          (procedure_keyword)
          name: (identifier)
          body: (code_block))
        (preproc_else)
        (procedure
          (procedure_keyword)
          name: (identifier)
          body: (code_block))
        (preproc_endif
          (preproc_close))))))
```

- [ ] **Step 2: Run it and confirm it fails**

```bash
tree-sitter test --file-name "preproc_expression_parens_test.txt"
```

Expected: FAIL with ERROR nodes around `#  elif`.

- [ ] **Step 3: Replace the literal lists with horizontal-whitespace regexes**

```javascript
    // Horizontal whitespace after the '#' is tolerated the same way the
    // scanner tolerates it for #if/#endif. `[ \t]*` NEVER `\s*` — the regex
    // crate's `\s` matches '\n', which would let the token span a newline and
    // swallow the next line's source. `elif` and `else` carry no external
    // token and touch no depth state, so a regex here is a plain
    // literal-vs-regex swap with no scanner interaction.
    preproc_elif: $ => seq(
      new RustRegex('(?i)#[ \\t]*elif'),
      field('condition', $._preproc_expression)
    ),

    preproc_else: $ => new RustRegex('(?i)#[ \\t]*else'),
```

- [ ] **Step 4: Regenerate and re-run**

```bash
tree-sitter generate
tree-sitter test --file-name "preproc_expression_parens_test.txt"
```

Expected: PASS.

If generate reports that `#[ \t]*else` conflicts with `#[ \t]*elif` (both match the `#`+`el` prefix), that is expected lexer behaviour and tree-sitter resolves it by longest match — `#elif` is longer than `#else` only at the fourth character, and they differ there, so no conflict should arise. If one does, add `token()` around each regex.

- [ ] **Step 5: Verify the existing negative tests still hold**

```bash
tree-sitter test --file-name "preproc_if_elif_whitespace_tolerance_test.txt"
```

That file asserts `#` + newline + `elif` stays an ERROR. `[ \t]*` excludes `\n` by construction, so it must still pass. If it does not, the regex was written with `\s`.

- [ ] **Step 6: Run all three gates and commit**

```bash
tree-sitter test
./parse-al-parallel.sh ./BC.History/ .
NUM_THREADS=16 ./tools/tree-harness.sh verify ./BC.History .snapshots/<current-baseline> > /tmp/h.txt 2>&1
git add grammar.js src/parser.c src/grammar.json src/node-types.json \
        test/corpus/preproc_expression_parens_test.txt CHANGELOG.md
git commit -m "fix(preproc): tolerate any horizontal whitespace in #elif/#else

The literal lists covered only the zero- and one-space forms while
scanner-owned #if/#endif accept [ \\t]*. '#  elif' is legal AL and was an ERROR.

[BC.History: 0 errors, 100% success]"
```

---

## Task 7: `array_type.sizes` distributes over the commas

`grammar.js:1295-1302` wraps the whole `seq($.integer, repeat(seq(',', $.integer)))` in one `field('sizes', …)`, so `node-types.json` records `sizes` as `multiple: true` with an anonymous `","` in its type set. `children_by_field_name('sizes')` on `array[10,20] of Integer` returns `10`, `,`, `20`. This is the defect class already fixed for case patterns — see the comment at `grammar.js:3460-3465` about the owned-IR lowerer.

**Files:**
- Modify: `grammar.js:1295-1302`
- Test: `test/corpus/field_shape_audit_test.txt` (create)

**Interfaces:**
- Consumes: the current baseline.
- Produces: `array_type.sizes` becomes `multiple: true` with type set `['integer']` only.

- [ ] **Step 1: Write the failing test**

Create `test/corpus/field_shape_audit_test.txt`:

```
================================================================================
Multi-dimensional array sizes are individually fielded
================================================================================
codeunit 1 T
{
    procedure X()
    var
        A: array[10,20] of Integer;
    begin
    end;
}
--------------------------------------------------------------------------------

(source_file
  (codeunit_declaration
    (codeunit_keyword)
    object_id: (integer)
    object_name: (identifier)
    body: (declaration_body
      (procedure
        (procedure_keyword)
        name: (identifier)
        (var_section
          (var_keyword)
          body: (var_body
            (variable_declaration
              name: (identifier)
              type: (type_specification
                (array_type
                  sizes: (integer)
                  sizes: (integer)
                  element_type: (type_specification
                    (basic_type)))))))
        body: (code_block
          (begin_keyword)
          (end_keyword))))))
```

- [ ] **Step 2: Run it and confirm the current field shape is wrong**

```bash
tree-sitter test --file-name "field_shape_audit_test.txt"
python -c "
import json
d=json.load(open('src/node-types.json'))
n=[x for x in d if x['type']=='array_type'][0]
print(n['fields']['sizes'])
"
```

Expected: the `sizes` field type set contains `','`.

- [ ] **Step 3: Field each integer individually**

```javascript
    // array[10] of Integer, array[10,20] of Text[100]
    //
    // Each size carries its OWN field('sizes', …). Wrapping the whole
    // comma-separated seq in one field puts the anonymous ',' inside the field,
    // so children_by_field_name('sizes') yields 10, ',', 20 — the same shape
    // that made the owned-IR lowerer panic on case patterns.
    array_type: $ => seq(
      prec(1, kw('array')),
      '[',
      field('sizes', $.integer),
      repeat(seq(',', field('sizes', $.integer))),
      ']',
      kw('of'),
      field('element_type', $.type_specification)
    ),
```

- [ ] **Step 4: Regenerate and confirm both the test and the node type**

```bash
tree-sitter generate
tree-sitter test --file-name "field_shape_audit_test.txt"
python -c "
import json
d=json.load(open('src/node-types.json'))
n=[x for x in d if x['type']=='array_type'][0]
print(n['fields']['sizes'])
"
```

Expected: PASS, and the `sizes` type set is `[{'type': 'integer', 'named': True}]` with `multiple: True`.

- [ ] **Step 5: Run all three gates**

The harness WILL report changes here — every `array[a,b]` in BC.History changes field assignment. Confirm the diffs are field-label-only (`sizes:` appearing on each integer, `","` no longer inside the field) and no node was added or removed, then re-snapshot.

- [ ] **Step 6: Commit**

```bash
git add grammar.js src/parser.c src/grammar.json src/node-types.json \
        test/corpus/field_shape_audit_test.txt CHANGELOG.md
git commit -m "fix(grammar): field each array size individually

field('sizes', seq(int, repeat(',', int))) put the anonymous ',' inside the
field, so children_by_field_name('sizes') returned 10, ',', 20.

[BC.History: 0 errors, 100% success]"
```

---

### ⚠ Correction that applies to Tasks 8 and 9 as well

Task 7 was described as "`children_by_field_name('sizes')` returns `10`, `,`, `20`". **That is not what happens at runtime.** Verified by building the pre-fix grammar in a worktree and parsing with `tree-sitter parse -c` (CST mode, which shows field labels on anonymous nodes): the old grammar already emitted

```
sizes: integer `10`
","                  <- no field label
sizes: integer `20`
```

The anonymous token never carried the field. What was actually wrong was `node-types.json`'s **declared** type set, which listed `","` as a possible type for `sizes`. That still matters — `node-types.json` is what typed bindings (Rust/TypeScript) are generated from, so the declared type was a lie about the tree — but it is a narrower defect than "queries return commas", and the harness correctly reports 0 changed production trees.

**Tasks 8 and 9 rest on the same evidence (a `node-types.json` type set) from the same review, so treat their severity as unproven until checked the same way.** Before claiming the defect, build the pre-fix grammar and run `tree-sitter parse -c` to see whether the anonymous `"."` / `";"` actually carries the field at runtime. Describe the fix by what it really changes. The fixes themselves remain correct either way — a declared type that cannot occur should not be declared.

---

## Task 8: `link_value.value` swallows the dot

`grammar.js:822-826` fields the whole `seq(id, '.', id)` for the `DataItem.Field` form, so the anonymous `"."` lands inside the `value` field. Same class as Task 7. The `member_trigger_name` comment at `grammar.js:2685-2699` already explains why this shape is wrong.

**Files:**
- Modify: `grammar.js:822-826`
- Test: `test/corpus/field_shape_audit_test.txt` (append)

**Interfaces:**
- Consumes: the current baseline.
- Produces: `link_value.value` no longer lists `'.'` in its type set.

- [ ] **Step 1: Append the failing test**

Find an existing DataItemLink fixture for the exact surrounding shape:

```bash
grep -rln "DataItemLink" test/corpus/ | head -3
```

Append to `test/corpus/field_shape_audit_test.txt` a query DataItemLink using the dotted form, e.g.:

```
================================================================================
DataItemLink dotted reference does not put the dot inside the value field
================================================================================
query 50100 Q
{
    elements
    {
        dataitem(Cust; Customer)
        {
            dataitem(Entry; "Cust. Ledger Entry")
            {
                DataItemLink = "Customer No." = Cust."No.";
            }
        }
    }
}
--------------------------------------------------------------------------------
```

Generate the expected tree by running `tree-sitter parse` on the same source and pasting the output with spans stripped:

```bash
tree-sitter parse "$SCRATCH/link.al" | sed 's/ \[[0-9]*, [0-9]*\] - \[[0-9]*, [0-9]*\]//g'
```

Paste that as the expected tree, then hand-edit it to the shape you want — `value:` on each identifier, no bare `"."` inside the field.

- [ ] **Step 2: Run it and confirm it fails**

```bash
tree-sitter test --file-name "field_shape_audit_test.txt"
```

- [ ] **Step 3: Split the field across the two identifiers**

```javascript
        // Direct reference: DataItem.FieldName (used in query DataItemLink).
        // Each identifier carries its own field; wrapping the seq put the
        // anonymous '.' inside the value field.
        prec(3, seq(
          field('value', $._identifier_or_quoted),
          '.',
          field('value', $._identifier_or_quoted)
        )),
```

- [ ] **Step 4: Regenerate, re-run, and confirm the node type**

```bash
tree-sitter generate
tree-sitter test --file-name "field_shape_audit_test.txt"
python -c "
import json
d=json.load(open('src/node-types.json'))
n=[x for x in d if x['type']=='link_value'][0]
print([t['type'] for t in n['fields']['value']['types']])
"
```

Expected: no `'.'` in the printed list.

- [ ] **Step 5: Run all three gates, re-snapshot if trees changed, commit**

```bash
git add grammar.js src/parser.c src/grammar.json src/node-types.json \
        test/corpus/field_shape_audit_test.txt CHANGELOG.md
git commit -m "fix(grammar): keep the dot out of link_value's value field

[BC.History: 0 errors, 100% success]"
```

---

## Task 9: `case_else_branch.body` is a raw statement repeat

`grammar.js:3506-3512` fields `repeat($._statement)` directly, so `body` is `multiple: true` and includes anonymous `";"`. This breaks the single-node `body` invariant established for the textobject queries (issue #19). `statement_block` exists for exactly this and `repeat_statement` already uses it.

**Do Step 0 first, as Tasks 7 and 8 did** — parse a `case … else` with two statements using `tree-sitter parse -c` on the pre-fix grammar and record whether the anonymous `";"` actually carries the `body` label at runtime. In both previous tasks the answer was no, and the defect was only an over-broad declared type.

**But expect this one to differ, and say so precisely.** Tasks 7 and 8 were `field(name, seq(x, SEP, x))` — one field wrapping a sequence. This is `field('body', repeat($._statement))`, and `_statement` *owns its own terminating `;`*, so the `;` is genuinely inside each statement rather than a separator the field accidentally spans. Whatever Step 0 shows, the structural complaint stands on its own: `body` is `multiple: true` where every other scoped construct exposes a single node, and that is what the textobject queries rely on. Wrapping in `statement_block` is a real tree change and the harness will report moved files — unlike Tasks 7 and 8, which moved none.

Note also that fourteen other fields share this exact `;`-inside-`body` shape (`if_statement.then_branch`, `while_statement.body`, `for_statement.body`, and so on). This task fixes only `case_else_branch`, which is the one with a drop-in replacement. Do not widen it.

**Files:**
- Modify: `grammar.js:3506-3512`
- Test: `test/corpus/field_shape_audit_test.txt` (append)

**Interfaces:**
- Consumes: the current baseline.
- Produces: `case_else_branch.body` becomes `multiple: false`, type set `['code_block', 'statement_block']`.

- [ ] **Step 1: Read how repeat_statement wraps its body**

```bash
grep -n -B2 -A12 "repeat_statement:" grammar.js
grep -n -A6 "statement_block:" grammar.js
```

Match that shape exactly.

- [ ] **Step 2: Append the failing test**

```
================================================================================
case else branch body is a single statement_block, not a raw statement repeat
================================================================================
codeunit 1 T
{
    procedure X()
    var
        x: Integer;
    begin
        case x of
            1:
                x := 1;
            else
                x := 2;
                x := 3;
        end;
    end;
}
--------------------------------------------------------------------------------
```

Generate the expected tree with `tree-sitter parse`, strip spans, then edit `case_else_branch`'s children so `body:` labels a single `statement_block` wrapping both assignments.

- [ ] **Step 3: Run it and confirm it fails**

```bash
tree-sitter test --file-name "field_shape_audit_test.txt"
```

- [ ] **Step 4: Wrap the repeat in statement_block**

```javascript
    case_else_branch: $ => prec.left(seq(
      $.else_keyword,
      // body is ONE node, never a raw repeat — a fielded repeat($._statement)
      // makes body multiple:true and drags the anonymous ';' into the field,
      // breaking the single-node body invariant the textobject queries rely on
      // (issue #19). repeat_statement already uses statement_block this way.
      field('body', choice(
        $.code_block,
        $.statement_block,
      ))
    )),
```

- [ ] **Step 5: Regenerate and confirm**

```bash
tree-sitter generate
tree-sitter test --file-name "field_shape_audit_test.txt"
python -c "
import json
d=json.load(open('src/node-types.json'))
n=[x for x in d if x['type']=='case_else_branch'][0]
f=n['fields']['body']
print('multiple:', f['multiple'], 'types:', [t['type'] for t in f['types']])
"
```

Expected: `multiple: False`, types `['code_block', 'statement_block']`.

If generate reports a conflict between `case_else_branch` and `case_branch` (both can start a statement run after their delimiter), add `[$.case_else_branch, $.case_branch]` to the `conflicts` array with a comment naming the ambiguity.

- [ ] **Step 6: Verify the textobject query still matches**

```bash
tree-sitter query queries/textobjects.scm "$SCRATCH/case.al" | head -20
```

- [ ] **Step 7: Run all three gates, re-snapshot, commit**

Every `case … else` with more than one statement in BC.History changes shape here — this is a real tree change and the harness will list it. Confirm the delta is only the added `statement_block` layer.

```bash
git add grammar.js src/parser.c src/grammar.json src/node-types.json \
        test/corpus/field_shape_audit_test.txt CHANGELOG.md
git commit -m "fix(grammar): wrap case_else_branch body in a statement_block

body was a fielded repeat(\$._statement) — multiple:true, with the anonymous
';' inside the field. Breaks the single-node body invariant from issue #19.

[BC.History: 0 errors, 100% success]"
```

---

## Task 10: dead code and one misleading comment

Four cleanups with no behavioural effect, verified:
- `chartpart_keyword` (`grammar.js:3959`) — one occurrence in the file, its own definition. Absent from `node-types.json`, so it can never appear in a tree and its stated purpose (query matching) is unfulfillable.
- `_named_section` (`grammar.js:67-77`) — helper function, never called.
- `empty_statement` — defined twice, identically, at `grammar.js:489` and `grammar.js:3307`. The second JS object key silently overwrites the first.
- `variable_declaration`'s Label arm comment at `grammar.js:2746` says "Must be Label type", but the rule accepts any `basic_type` there. Under parse-don't-validate the rule is right and the comment is wrong.

**Files:**
- Modify: `grammar.js:67-77`, `grammar.js:489`, `grammar.js:2746`, `grammar.js:3959`

**Interfaces:**
- Consumes: the current baseline.
- Produces: nothing.

- [ ] **Step 1: Confirm each claim before deleting**

```bash
grep -n "chartpart_keyword" grammar.js          # expect 1 line (the definition)
grep -c '"chartpart_keyword"' src/node-types.json   # expect 0
grep -n "_named_section" grammar.js             # expect 1 line (the definition)
grep -n "empty_statement" grammar.js            # expect 2 definitions + 3 references
```

Note `break_keyword` is NOT an orphan despite what `validate-grammar.sh` reports — `break_statement` uses it at `grammar.js:3598`. Task 13 fixes that false positive.

- [ ] **Step 2: Delete the three, and correct the comment**

Remove the `_named_section` function (lines 67-77), the `chartpart_keyword` rule (line 3959), and the FIRST `empty_statement` definition (line 489, the one that is overwritten).

At `grammar.js:2746`, replace `// Must be Label type` with:

```javascript
      // Conventionally a Label, but the rule accepts any basic_type — the
      // "must" is a semantic rule for a linter, not something the grammar
      // enforces (parse structure, don't validate).
```

- [ ] **Step 3: Regenerate and confirm nothing moved**

```bash
tree-sitter generate
tree-sitter test
NUM_THREADS=16 ./tools/tree-harness.sh verify ./BC.History .snapshots/<current-baseline> > /tmp/h.txt 2>&1
tail -2 /tmp/h.txt
```

Expected: VERIFIED, byte-identical. Deleting an unreachable rule and a shadowed duplicate must not move a single tree. **If any file changed, revert and investigate** — it means one of the three was not actually dead.

- [ ] **Step 3b: Inherit Task 13's deferred acceptance — `./validate-grammar.sh` must now exit 0**

Task 13 fixed the orphan detector (13d) but could not reach exit 0, because `validate-grammar.sh` Step 4 sets `VALIDATION_FAILED=1` on a non-zero orphan count and `chartpart_keyword` — a genuine orphan — was still present. Deleting it is *this* task's job, so the acceptance lands here.

After the deletion, `./validate-grammar.sh` must exit **0**. The only thing that may differ from Task 13's recorded step-by-step results is Step 4 going from `UNUSED_COUNT=1` to `UNUSED_COUNT=0` and the overall exit going 1 → 0. Compare against `task-13-report.md`'s per-step evidence: **if anything else moved, something regressed between the two tasks** — investigate before committing.

Also confirm the detector still classifies `break_keyword` as USED. It is referenced only as `break_statement: $ => prec(13, $.break_keyword)`, which is the exact shape 13d taught the scanner to see; a regression there would silently return the false positive.

- [ ] **Step 4: Commit**

```bash
git add grammar.js src/parser.c src/grammar.json src/node-types.json CHANGELOG.md
git commit -m "chore(grammar): drop unreachable chartpart_keyword and two dead definitions

chartpart_keyword is referenced nowhere and absent from node-types.json, so it
can never appear in a tree. _named_section is never called. empty_statement was
defined twice; the second key silently overwrote the first.

[BC.History: 0 errors, 100% success]"
```

---

## Task 11: keyword and operator case-insensitivity

AL is fully case-insensitive. The Tier-1 keyword rules and the operator rules spell out exactly three casings (`if`/`IF`/`If`), so any other casing fails — and because `_statement` carries `optional(';')`, most of the failures are **silent**: `iF x = 0 tHEN x := 1 eLSe x := 2;` compiles under alc and parses here to a flat run of identifiers and assignments with the entire if-structure gone, zero ERROR nodes.

This is the riskiest task in the plan. `choice('if','IF','If')` is three string literals, which tree-sitter's keyword-extraction optimisation can fold into the `word` token; `kw('if')` is a regex token, which it cannot. Switching may raise `STATE_COUNT` or introduce identifier conflicts. `asserterror_keyword: $ => kw('asserterror', 10)` already uses the regex form at the same precedence, which is the precedent that makes this viable.

**Files:**
- Modify: `grammar.js:3882-3900` (Tier-1 keywords), `grammar.js:3690-3694` (div/mod), `grammar.js:3717-3736` (and/or/xor), `grammar.js:3751` (unary not), `grammar.js:2888-2891` (preproc not)
- Test: `test/corpus/keyword_case_insensitivity_test.txt` (create)

**Interfaces:**
- Consumes: the current baseline.
- Produces: nothing.

- [ ] **Step 1: Record the current parser size**

```bash
grep -E '^#define (SYMBOL_COUNT|STATE_COUNT|LARGE_STATE_COUNT)' src/parser.c
ls -l src/parser.c | awk '{printf "%.1f MB\n", $5/1048576}'
```

Write the numbers down. Step 6 compares against them.

- [ ] **Step 2: Write the failing test**

Create `test/corpus/keyword_case_insensitivity_test.txt`:

```
================================================================================
Mixed-case control-flow keywords
================================================================================
codeunit 1 T
{
    procedure X()
    var
        x: Integer;
    begin
        iF x = 0 tHEN x := 1 eLSe x := 2;
    end;
}
--------------------------------------------------------------------------------

(source_file
  (codeunit_declaration
    (codeunit_keyword)
    object_id: (integer)
    object_name: (identifier)
    body: (declaration_body
      (procedure
        (procedure_keyword)
        name: (identifier)
        (var_section
          (var_keyword)
          body: (var_body
            (variable_declaration
              name: (identifier)
              type: (type_specification
                (basic_type)))))
        body: (code_block
          (begin_keyword)
          body: (statement_block
            (if_statement
              (if_keyword)
              condition: (comparison_expression
                left: (identifier)
                operator: (comparison_operator)
                right: (integer))
              (then_keyword)
              then_branch: (assignment_statement
                left: (identifier)
                right: (integer))
              (else_keyword)
              else_branch: (assignment_statement
                left: (identifier)
                right: (integer))))
          (end_keyword))))))

================================================================================
Mixed-case operators
================================================================================
codeunit 1 T
{
    procedure X()
    var
        a: Boolean;
        b: Boolean;
        n: Integer;
    begin
        a := a aNd b;
        a := a oR b;
        a := nOt a;
        n := n dIv 2;
        n := n mOd 2;
    end;
}
--------------------------------------------------------------------------------
```

Generate the second expected tree with `tree-sitter parse` after the fix, once it produces no ERROR nodes.

```
================================================================================
Mixed-case preprocessor not
================================================================================
codeunit 1 T
{
#if nOT BAR
    procedure A() begin end;
#endif
    procedure C() begin end;
}
--------------------------------------------------------------------------------
```

Same — fill in from `tree-sitter parse` once clean.

- [ ] **Step 3: Run it and confirm it fails**

```bash
tree-sitter test --file-name "keyword_case_insensitivity_test.txt"
```

Expected: FAIL. The first case produces a flat statement run with **no ERROR node** — confirm that, since it is the silent-misparse evidence.

- [ ] **Step 4: Convert the Tier-1 keywords to `kw()`**

Replace `grammar.js:3882-3900` with:

```javascript
    // AL is fully case-insensitive. Spelling out three casings meant `iF`,
    // `tHEN`, `eLSe` — all legal AL, all accepted by alc — failed, and because
    // _statement carries optional(';') the failure was SILENT: the if-structure
    // collapsed into a flat statement run with no ERROR node. kw() is a
    // case-insensitive regex; asserterror_keyword already used this form.
    if_keyword: $ => kw('if', 10),
    then_keyword: $ => kw('then', 10),
    else_keyword: $ => kw('else', 10),
    case_keyword: $ => kw('case', 10),
    of_keyword: $ => kw('of', 10),
    for_keyword: $ => kw('for', 10),
    foreach_keyword: $ => kw('foreach', 10),
    while_keyword: $ => kw('while', 10),
    do_keyword: $ => kw('do', 10),
    repeat_keyword: $ => kw('repeat', 10),
    until_keyword: $ => kw('until', 10),
    exit_keyword: $ => kw('exit', 10),
    continue_keyword: $ => kw('continue', 10),
    break_keyword: $ => kw('break', 10),
    with_keyword: $ => kw('with', 10),
    asserterror_keyword: $ => kw('asserterror', 10),
    in_keyword: $ => kw('in', 10),
    to_keyword: $ => kw('to', 10),
    downto_keyword: $ => kw('downto', 10),
```

- [ ] **Step 5: Convert the operators**

`grammar.js:3690-3694`:

```javascript
    multiplicative_expression: $ => prec.left(7, seq(
      field('left', $._expression),
      field('operator', choice('*', '/', kw('div'), kw('mod'))),
      field('right', $._expression)
    )),
```

`grammar.js:3717-3736` — replace `choice('and','AND','And')` with `kw('and')`, `choice('or','OR','Or')` with `kw('or')`, `choice('xor','XOR','Xor')` with `kw('xor')`.

`grammar.js:3751`:

```javascript
    unary_expression: $ => prec.right(7, seq(
      field('operator', choice('+', '-', kw('not'))),
      field('operand', $._expression)
    )),
```

`grammar.js:2888-2891`:

```javascript
    preproc_not_expression: $ => seq(
      kw('not'),
      $._preproc_expression
    ),
```

- [ ] **Step 6: Regenerate and compare parser size — this is the go/no-go**

```bash
tree-sitter generate
grep -E '^#define (SYMBOL_COUNT|STATE_COUNT|LARGE_STATE_COUNT)' src/parser.c
ls -l src/parser.c | awk '{printf "%.1f MB\n", $5/1048576}'
```

Compare against Step 1. A rise under ~10% in `STATE_COUNT` is acceptable. If it explodes, or if generate reports unresolvable conflicts between the keyword tokens and `identifier`, **stop and split this task**: convert only the keywords that appear in the silent-misparse path (`if`, `then`, `else`, `and`, `or`, `not`) and leave the rest, then note the remainder in the changelog as still-casing-sensitive.

- [ ] **Step 7: Fill in the two remaining expected trees and re-run**

```bash
tree-sitter parse "$SCRATCH/ops.al" | sed 's/ \[[0-9]*, [0-9]*\] - \[[0-9]*, [0-9]*\]//g'
```

Confirm no ERROR/MISSING, paste into the fixture, then:

```bash
tree-sitter test --file-name "keyword_case_insensitivity_test.txt"
```

Expected: PASS.

- [ ] **Step 8: Run all three gates**

The harness must come back VERIFIED. BC.History uses conventional casing throughout, so recognising *additional* casings must not move any existing tree. **If any file changed, that is a regression, not a fix** — a `kw()` regex matching more than it should. Read the diff before going further.

```bash
tree-sitter test
./parse-al-parallel.sh ./BC.History/ .
./parse-al-parallel.sh "U:/Git/DO.Support-Agents/" .
NUM_THREADS=16 ./tools/tree-harness.sh verify ./BC.History .snapshots/<current-baseline> > /tmp/h.txt 2>&1
tail -2 /tmp/h.txt
```

- [ ] **Step 9: Commit**

```bash
git add grammar.js src/parser.c src/grammar.json src/node-types.json \
        test/corpus/keyword_case_insensitivity_test.txt CHANGELOG.md
git commit -m "fix(grammar): make control-flow keywords and operators case-insensitive

AL is fully case-insensitive but the keyword rules spelled out three casings.
\`iF x = 0 tHEN x := 1 eLSe x := 2;\` compiles under alc and parsed into a flat
statement run with the if-structure gone and ZERO error nodes.

STATE_COUNT <before> -> <after>.

[BC.History: 0 errors, 100% success]"
```

---

## Task 12: begin/end are dropped from the tree inside `#if` blocks

`src/scanner.c` declines `BEGIN_KEYWORD`/`END_KEYWORD` when `state->depth > 0`. For a *complete* (non-split) `begin … end` inside `#if … #endif`, nothing then claims the text: `code_block` spans it, but neither a named nor an anonymous node covers `begin` or `end`. The CST is not lossless over the source, and both keywords are unhighlightable inside every `#if` block.

Confirmed present in released v3.3.0 (built from the tag in a worktree) and in the current tree, so it predates all of this work.

**Files:**
- Modify: `src/scanner.c` (the `BEGIN_KEYWORD`, `END_KEYWORD`, `PREPROC_SPLIT_BEGIN`, `PREPROC_SPLIT_END` blocks)
- Modify: `grammar.js` (wherever anonymous `kw('begin')`/`kw('end')` appear in split rules)
- Test: `test/corpus/preproc_begin_end_named_test.txt` (create)

**Interfaces:**
- Consumes: `skip_whitespace_and_comments` and `peek_directive_ci_skip_extras` from Task 1.
- Produces: `begin_keyword` / `end_keyword` nodes inside preprocessor conditionals.

- [ ] **Step 1: Pin the mechanism before changing anything**

The bytes are consumed with no token emitted — an anonymous `kw('begin')` would show in `-c` output (the `";"`, `"("`, `"{"` all do), so the handoff-to-anonymous story is incomplete. Find out where they go:

```bash
cat > "$SCRATCH/t3.al" <<'EOF'
codeunit 50100 T
{
    procedure A()
    begin
        Message('a');
    end;
#if not CLEAN22
    procedure B()
    begin
        Message('b');
    end;
#endif
}
EOF
cd U:/Git/tree-sitter-al
tree-sitter parse -c "$SCRATCH/t3.al" | sed 's/\x1b\[[0-9;]*m//g'
```

Expected today: `body: code_block` at 8:4-10:8 whose only children are `body: statement_block` and `";"`.

Then enable scanner tracing — set `#define SCANNER_DEBUG 1` at the top of `src/scanner.c`, add the `valid_symbols` dump described in `.claude/rules/scanner.md`, `tree-sitter build`, and re-parse capturing stderr. Determine whether `BEGIN_KEYWORD` is even in `valid_symbols` at that position, and whether any external token fires there with zero width. **Revert the debug define before committing.**

- [ ] **Step 2: Write the failing test**

Create `test/corpus/preproc_begin_end_named_test.txt` with the `t3.al` source above, and an expected tree in which the second `code_block` has `(begin_keyword)` and `(end_keyword)` children exactly like the first.

- [ ] **Step 3: Run it and confirm it fails**

```bash
tree-sitter test --file-name "preproc_begin_end_named_test.txt"
```

- [ ] **Step 4: Make the depth>0 path emit named keywords when the split conditions do not hold**

The dispatch must decide within a single scan — a scan that returns false discards its advances and is not re-entered at the same position. So at depth > 0, read the keyword once, `mark_end`, run the split lookahead, and pick the symbol from the result:

```c
  // At depth > 0 the split tokens get first refusal, but a COMPLETE begin…end
  // inside #if must still produce named keywords. Deciding between them
  // requires ONE scan: a false return discards every advance and the scanner is
  // not re-entered here, so we read 'begin' once, fix the token end, then let
  // the lookahead choose the symbol.
  if (state->depth > 0 &&
      (valid_symbols[PREPROC_SPLIT_BEGIN] || valid_symbols[BEGIN_KEYWORD])) {
    skip_whitespace(lexer);
    if (read_keyword_ci(lexer, "begin")) {
      lexer->mark_end(lexer);
      if (valid_symbols[PREPROC_SPLIT_BEGIN] &&
          peek_directive_ci_skip_extras(lexer, DIRECTIVE_ENDIF)) {
        lexer->result_symbol = PREPROC_SPLIT_BEGIN;
        return true;
      }
      if (valid_symbols[BEGIN_KEYWORD]) {
        lexer->result_symbol = BEGIN_KEYWORD;
        return true;
      }
      return false;
    }
    return false;
  }
```

Apply the analogous change to the `end` side, with `DIRECTIVE_ELSE_ENDIF` and the `;` check guarding `PREPROC_SPLIT_END` before falling back to `END_KEYWORD`.

Then remove the `state->depth == 0` guards from the existing `BEGIN_KEYWORD`/`END_KEYWORD` blocks, which now only handle the depth-0 case, and delete the anonymous `kw('begin')`/`kw('end')` fallbacks from the grammar rules that no longer need them:

```bash
grep -n "kw('begin')\|kw('end')" grammar.js
```

- [ ] **Step 5: Regenerate, rebuild, re-run**

```bash
tree-sitter generate && tree-sitter build
tree-sitter test --file-name "preproc_begin_end_named_test.txt"
```

Expected: PASS, with `begin_keyword` and `end_keyword` present inside the `#if`.

- [ ] **Step 6: Run the full suite — the split fixtures are the risk**

```bash
tree-sitter test
```

The `preproc_split_*` fixtures encode anonymous `begin`/`end` in their expected trees. Where the new named nodes appear, update those fixtures with `tree-sitter test -u` — but **only after confirming the actual output contains no ERROR or MISSING node**, per `.claude/rules/test-failures.md`.

- [ ] **Step 7: Run the corpus gates**

```bash
./parse-al-parallel.sh ./BC.History/ .
./parse-al-parallel.sh "U:/Git/DO.Support-Agents/" .
NUM_THREADS=16 ./tools/tree-harness.sh verify ./BC.History .snapshots/<current-baseline> > /tmp/h.txt 2>&1
grep -c '=== CHANGED:' /tmp/h.txt
```

This WILL change many trees — every `#if`-wrapped `begin … end` in BC.History gains two named nodes. Confirm the delta is purely *added* `begin_keyword`/`end_keyword` nodes and nothing was removed or restructured:

```bash
grep '^>' /tmp/h.txt | sed 's/\[[0-9]*, [0-9]*\] - \[[0-9]*, [0-9]*\]//' | sort | uniq -c | sort -rn | head
grep '^<' /tmp/h.txt | sed 's/\[[0-9]*, [0-9]*\] - \[[0-9]*, [0-9]*\]//' | sort | uniq -c | sort -rn | head
```

Then re-snapshot.

- [ ] **Step 8: Confirm highlighting now works**

```bash
tree-sitter query queries/highlights.scm "$SCRATCH/t3.al" | grep -c keyword
```

Both `begin`s and both `end`s must be captured.

- [ ] **Step 9: Update the docs and commit**

Update `CLAUDE.md` ("begin/end are named via stateful scanner" — the depth-0-only claim is now wrong) and `.claude/rules/contextual-keywords.md` and `.claude/rules/scanner.md`.

```bash
git add src/scanner.c grammar.js src/parser.c src/grammar.json src/node-types.json \
        test/corpus/ CLAUDE.md CHANGELOG.md
git add -f .claude/rules/scanner.md .claude/rules/contextual-keywords.md
git commit -m "fix(scanner): name begin/end inside preprocessor conditionals

BEGIN_KEYWORD/END_KEYWORD declined at depth > 0 and handed off to the split
tokens. For a complete begin…end inside #if nothing claimed the text: the CST
was not lossless over the source and both keywords were unhighlightable in
every #if block. Present since before 3.3.0.

The depth>0 path now reads the keyword once, marks the token end, and lets the
split lookahead choose between PREPROC_SPLIT_BEGIN and BEGIN_KEYWORD within a
single scan.

[BC.History: 0 errors, 100% success]"
```

---

## Task 12b: close the VAR_ATTRIBUTE_OPEN skip class

Added after the Task 1 review. The 3.3.1 fix closed two of `VAR_ATTRIBUTE_OPEN`'s blind spots but not the rest: the post-`]` skip and the name-list skips are still comment-blind AND newline-blind, which is the same defect class the 3.3.1 commit is named after. The reviewer verified six failing shapes at 3 ERROR nodes each, identical before and after 3.3.1. It also makes 3.3.1's D4 fix partial — `"My Var",` newline `Other: Boolean;` still errors, while the grammar parses `Alpha,` newline `Beta: Boolean;` cleanly with no attribute, so the scanner is internally inconsistent with its own grammar.

**Files:**
- Modify: `src/scanner.c` — the `VAR_ATTRIBUTE_OPEN` block: the post-`]` skip, the inter-attribute skip in the chained-attribute loop, and both name-list skips
- Test: `test/corpus/var_attribute_whitespace_test.txt` (create)

**Interfaces:**
- Consumes: `skip_whitespace_and_comments` and `skip_whitespace_nomark` from Task 1.
- Produces: nothing.

- [ ] **Step 1: Write the failing tests — one per shape**

Create `test/corpus/var_attribute_whitespace_test.txt` with six cases inside a `codeunit 1 T { procedure X() var … begin end; }` wrapper: a comment after the `]`; a comment inside the name list; a comment before the `:`; a newline after the `,`; a newline before the `:`; and `[InDataSet]` then `"My Var",` newline `Other: Boolean;`. Generate each expected tree with `tree-sitter parse` **after** the fix and confirm no ERROR/MISSING before pasting.

- [ ] **Step 2: Run and confirm 3 ERROR nodes per shape**

```bash
tree-sitter test --file-name "var_attribute_whitespace_test.txt"
```

- [ ] **Step 3: Route every skip in the block through the shared helpers**

Replace each hand-rolled `while (lookahead == ' ' || lookahead == '\t' …)` inside `VAR_ATTRIBUTE_OPEN` with `skip_whitespace_and_comments(lexer)`, handling its `false` return (bare `/`) as a decline. The token start is fixed by the leading `skip_whitespace` and `mark_end` is called on the `[`, so every one of these is a post-`mark_end` skip and must be non-marking — that is what `skip_whitespace_and_comments` already guarantees via `skip_whitespace_nomark`.

- [ ] **Step 4: Regenerate, rebuild, re-run**

```bash
tree-sitter generate && tree-sitter build
tree-sitter test --file-name "var_attribute_whitespace_test.txt"
```

- [ ] **Step 5: Run all three gates**

The harness should report VERIFIED — these shapes produce ERRORs today, so no currently-clean BC.History tree can depend on them.

- [ ] **Step 6: Commit, pushing the scanner commit alone first**

Per the Global Constraints, a scanner change must be pushed by itself so CI's fuzz job actually runs.

```bash
git add src/scanner.c test/corpus/var_attribute_whitespace_test.txt CHANGELOG.md
git commit -m "fix(scanner): step VAR_ATTRIBUTE_OPEN's remaining skips over comments and newlines

The 3.3.1 fix closed the bracket scan and the name-loop structure but left the
post-] skip and the name-list skips comment- and newline-blind — the same class
the commit was named after. Six shapes gave 3 ERROR nodes each, and it made the
quoted-name fix partial.

[BC.History: 0 errors, 100% success]"
```

---

## Task 13: fix the tooling — five defects

**Pulled forward** from the end of the plan, on the release owner's instruction. Every one of these was found by *doing* the work, and three of them actively degrade the remaining tasks: the harness is unusable at the delta sizes Tasks 11 and 12 will produce, and `validate-grammar.sh` currently exits red for everyone regardless of what they change, which makes it worthless as a gate.

Do these as **five separate commits**, one per defect, so each can be reverted independently. None touches `grammar.js`, `src/`, or any corpus fixture — if any of those shows up in `git status`, something has gone wrong.

### 13a — `tools/tree-harness.sh` per-file reporting is O(n²)

The `verify` subcommand's mismatch-reporting loop re-decompresses the whole `trees.tar.gz` and linearly scans `master.txt` **once per changed file** (`tools/tree-harness.sh:135-144`: `grep -nxF "$path" "$SNAPDIR/master.txt"` and `tar -xzO -f "$SNAPDIR/trees.tar.gz" "trees/$idxp"` inside the loop). Measured at ~70 changed files/minute. Fine for the 0-1 file deltas most tasks produce; unusable at Task 9's 757, and Task 12 will be larger.

Fix: extract the archive **once** to a temp dir before the loop, and build a path→index map **once** (e.g. `awk 'NR==FNR{...}'` or a single `nl`/`join` pass) instead of grepping per file. Keep the output format byte-identical — the per-file `=== CHANGED:` header and the diff body are what every task's analysis greps for.

Verify: re-run `verify` against a snapshot known to differ (take a snapshot, make a trivial grammar change, regenerate, verify) and confirm the output is identical to the old implementation's for the same input, and that a large delta completes in a reasonable time. State the before/after timing.

### 13b — `validate-grammar.sh` Step 3 can never pass

Step 3 greps `test/corpus/` for ERROR/MISSING and fails on 8 hits across 4 files: `option_members_tabledata_keyword_test`, `pragma_whitespace_tolerance_test`, `preproc_if_elif_whitespace_tolerance_test`, `preproc_region_whitespace_audit_test` (ERROR counts 1, 1, 4, 2). All four are **deliberate negative fixtures** — they assert that `#` + newline + keyword stays an ERROR, that `# ifx` is not `#if`, and that a dangling `, Foo` after a tabledata permission surfaces. Those ERROR nodes are the assertion. The check has never passed, including at every released version.

Fix: allow-list those four files by name with a comment explaining what each asserts, so a hit anywhere else still fails the step. Do not delete or weaken the fixtures.

### 13c — three of `validate-grammar.sh`'s dependencies are untracked

`.gitignore:58` ignores `*.py` repo-wide, with exceptions only for `tools/keyword-sync/*.py` and `tools/check-field-types.py`. But the script calls four Python helpers and three are untracked:

```bash
for f in find_unused_definitions.py analyze_duplicates.py check_grammar_health.py; do
  printf "%-32s %s\n" "$f" "$(git ls-files --error-unmatch "$f" >/dev/null 2>&1 && echo TRACKED || echo UNTRACKED)"
done
```

On a fresh clone those steps silently degrade to "script not found" warnings, so orphan detection, duplicate detection and the health check do not run for anyone else. That is also why 13d's false positive survived — the script producing it cannot be reviewed by anyone who does not already have a copy.

Fix: read each script first for machine-specific paths or anything that should not be committed, then move all three under `tools/` and add a single `.gitignore` exception for `tools/*.py`, updating the call sites. Confirm afterwards that `git ls-files tools/` lists all four helpers.

### 13d — the orphan detector reports `break_keyword` falsely

`validate-grammar.sh` reports `break_keyword` as unused. It is not: `break_statement: $ => prec(13, $.break_keyword)` at `grammar.js:3598`. The reference scan misses `$.name` used as the **sole argument to `prec()`**, i.e. a rule whose entire right-hand side is one reference.

Fix: widen the reference pattern so a `$.name` anywhere on a rule's right-hand side counts. Verify against the known-good answer: after Task 10 removes `chartpart_keyword`, the correct orphan count is **zero**; before it, exactly one (`chartpart_keyword`). Both `break_keyword` and `chartpart_keyword` must be classified correctly, not just the count.

### 13e — the release pre-flight check can never pass

`.claude/commands/release.md` pre-flight #3 is the same grep as 13b and fails for the same four files. Fix it the same way, and cross-reference 13b so the two do not drift apart.

- [ ] **Step 1: 13a — make the harness reporting loop linear**
- [ ] **Step 2: 13b — allow-list the four deliberate-negative fixtures in `validate-grammar.sh`**
- [ ] **Step 3: 13c — track the three untracked Python helpers**
- [ ] **Step 4: 13d — fix the orphan detector's `prec()` blind spot**
- [ ] **Step 5: 13e — fix the release pre-flight check**
- [ ] **Step 6: confirm `./validate-grammar.sh` now exits 0 on a clean tree**

That last step is the real acceptance test for 13b/13c/13d together: the script must go green, and it must go **red** again if you temporarily introduce a genuine ERROR node in a fixture outside the allow-list. Prove both directions.

## Task 13 (original): two tooling checks that can never pass

`validate-grammar.sh` reports `break_keyword` as an orphan although `break_statement` uses it at `grammar.js:3598`. And `.claude/commands/release.md` pre-flight check #3 greps for ERROR/MISSING in `test/corpus/` — 8 hits across 4 files, all deliberate negative fixtures that assert malformed input *stays* malformed. Neither check has passed at any release, including v3.3.0.

**Files:**
- Modify: `validate-grammar.sh` (orphan detection)
- Modify: `.claude/commands/release.md` (pre-flight #3)

**Interfaces:**
- Consumes: nothing.
- Produces: nothing.

- [ ] **Step 1: Reproduce the false positive**

```bash
./validate-grammar.sh 2>&1 | grep -A4 "UNUSED RULES"
grep -n "break_keyword" grammar.js    # 2 hits: definition AND use at :3598
```

- [ ] **Step 2: Find and fix the reference scan**

```bash
grep -n "UNUSED RULES" -B30 validate-grammar.sh
```

The scan misses `$.break_keyword` when it is the sole argument to `prec(…)` — `break_statement: $ => prec(13, $.break_keyword)`. Widen the reference pattern so a `$.name` anywhere on a rule's right-hand side counts, not just inside a `seq`/`choice`.

- [ ] **Step 3: Verify only the true orphan remains**

```bash
./validate-grammar.sh 2>&1 | grep -A4 "UNUSED RULES"
```

Expected after Task 10: zero unused rules. Before Task 10: `chartpart_keyword` only.

- [ ] **Step 3b: Track the scripts `validate-grammar.sh` depends on**

`.gitignore` ignores `*.py` repo-wide, with exceptions only for `tools/keyword-sync/*.py` and (added in Task 7) `tools/check-field-types.py`. But `validate-grammar.sh` calls four Python scripts, and three of them are UNTRACKED:

```bash
for f in find_unused_definitions.py analyze_duplicates.py check_grammar_health.py; do
  printf "%-32s %s\n" "$f" "$(git ls-files --error-unmatch "$f" >/dev/null 2>&1 && echo TRACKED || echo UNTRACKED)"
done
```

On a fresh clone those three steps silently degrade to "script not found" warnings, so orphan detection, duplicate detection and the health check do not actually run for anyone else — including whoever inherits this repo. That is also why the `break_keyword` false positive in Step 1 went unnoticed: the script producing it cannot be reviewed by anyone who does not already have it.

Add `.gitignore` exceptions for all three and commit them, or move them under `tools/` and add one exception for that directory. Read each one first — if any contains machine-specific paths or secrets, fix that before tracking it. Then confirm a fresh checkout runs all four steps.

- [ ] **Step 4: Fix the release pre-flight check**

In `.claude/commands/release.md`, replace check #3 with one that excludes the deliberate-negative fixtures and says why:

```markdown
3. No UNEXPECTED ERROR/MISSING nodes in tests:
   ```bash
   grep -rn "(ERROR\b\|MISSING\b" test/corpus/ --include="*.txt" \
     | grep -v "ERROR(" \
     | grep -vE "option_members_tabledata_keyword_test|pragma_whitespace_tolerance_test|preproc_if_elif_whitespace_tolerance_test|preproc_region_whitespace_audit_test"
   ```
   Those four files are deliberate negatives: they pin that `#` + newline +
   keyword stays an ERROR (horizontal-only whitespace tolerance), that `# ifx`
   is not `#if`, and that a dangling `, Foo` after a tabledata permission
   surfaces. Their ERROR nodes are the assertion. Any hit OUTSIDE them is a
   real problem.
```

- [ ] **Step 5: Commit**

```bash
git add validate-grammar.sh CHANGELOG.md
git add -f .claude/commands/release.md
git commit -m "fix(tooling): stop reporting break_keyword as orphaned

The orphan scan missed \$.name used as the sole argument to prec(). Also scope
the release pre-flight ERROR grep to exclude the four deliberate-negative
fixtures, which made the check unpassable at every release including v3.3.0."
```

---

## Tasks 15–21: the deferred backlog

Added on the release owner's instruction — **nothing ships until these are done**, so 4.0.0 absorbs the whole backlog rather than leaving a second major's worth of work behind. Each is independently revertible; do them in the order listed, since 15 and 16 move trees and the rest are easier to verify against a settled baseline.

### Task 15 — unify keyword node shape across all 84 rules

Ruled by the release owner. Today: **51** childless leaves (bare `kw()` → hidden `token(PATTERN)`), **18** with a visible anonymous child via `alias()`, **13** via explicit case `choice()`, **2** external (`begin_keyword`/`end_keyword`). A consumer cannot predict which shape a given keyword has, and `node-types.json` cannot tell them — it lists anonymous children only inside fields, and none of these are.

Make it one shape. `alias(kw('word'), 'word')` is the form already proven on the 18 Tier-1 keywords in Task 11, and it is what restored `exit_keyword`'s `"exit"` child. The 2 external tokens cannot take a child and stay as they are — say so explicitly in the docs rather than leaving a reader to wonder.

**Do not touch `asserterror_keyword` blindly.** Task 11's re-review established it had **no** anonymous type before that task, so aliasing it would *add* a novel node type rather than preserve one. Check each of the 51 the same way — `git show <pre-task-commit>:src/node-types.json` — before assuming alias is a no-op for it.

This moves the anonymous layer of essentially every tree. The harness **cannot see it** (durable finding 3), so the acceptance is a `node-types.json` set-diff plus `tree-sitter parse -c` spot checks, not the harness. Expect the harness to report 0 changed and understand that this proves nothing here.

Rewrite the shape table in `CLAUDE.md` and `.claude/rules/contextual-keywords.md` to state the single rule, and keep the advice to read a keyword's text from the node itself — it stays correct and survives future drift.

### Task 16 — make `link_value` cover the single-entry `DataItemLink`

Ruled by the release owner. `DataItemLink = "Customer No." = Cust."No.";` never instantiates `link_value`; it parses as `property_expression`/`comparison_expression` with a `member_expression` on the right. Only two-or-more comma-separated entries produce `link_value_list` → `link_value`. The Task 8 reviewer judged single-entry plausibly the majority shape, so a query against `link_value` misses most real usage.

Route the single-entry form through `link_value_list`/`link_value` so one query finds every DataItemLink relationship. This **will** move production trees — enumerate the delta with a node-instance set-difference (identity = node type + exact byte range) as Task 12 did, and confirm the only change is single-entry sites gaining the `link_value_list`/`link_value` layer. Re-snapshot afterwards.

Both CST fragments are in Task 8's report. Check `RunPageLink`, `SubPageLink` and `ColumnFilter` too — they are listed as complex properties alongside `DataItemLink` in `CLAUDE.md` and may share the rule or the defect.

### Task 17 — audit all 24 mixed named/anonymous fields

Ruled by the release owner: audit all, fix what is wrong, encode every verdict.

```bash
python3 -c "
import json
d=json.load(open('src/node-types.json'))
for n in d:
    for f,v in (n.get('fields') or {}).items():
        a=[t['type'] for t in v['types'] if not t.get('named')]
        if a and [t for t in v['types'] if t.get('named')]:
            print(f\"{n['type']}.{f}: {a}\")
"
```

Correct by design: `operator` on `additive_expression`, `logical_expression`, `unary_expression`, `multiplicative_expression` — the operator token *is* the value. Suspicious: 14 `body`/`then_branch`/`else_branch` fields carrying `";"` (downstream of `_statement` owning its terminator — decide whether that is deliberate, and say why either way), plus `dotnet_type.reference`, `object_reference_type.reference`, `record_type.reference`, `query_dataitem.table_name`, `report_dataitem.table_name`, `simple_table_relation.table`, `tabledata_permission.table_name` carrying `"."`/`"*"`, and `property.value` carrying `"-"`.

**Every one of the 24 ends as a row in `tools/check-field-types.py`** — fixed ones asserting the corrected shape, deliberate ones asserting the current shape as intentional. A verdict that lives only in a report is a verdict that gets re-litigated. Prove at least one new row fails on a mutated `node-types.json`, per the standing rule that a check which cannot fail is worse than no check.

### Task 18 — repurpose `analyze_duplicates.py`

Ruled by the release owner. It inspects only `*_property` rules — 2 in V2 where V1 had 291 — so `validate-grammar.sh` Step 5 always passes without checking anything meaningful. Repurpose it to detect **duplicate rule definitions**: two entries with the same key in the grammar's rules object, where JavaScript silently keeps the last. Task 10 removed exactly such a duplicate (`empty_statement`, defined twice identically) and no tool caught it — a linter would not either, since it is a valid object literal.

Verify it fires by reintroducing a duplicate temporarily, and confirm it distinguishes byte-identical duplicates (harmless but wrong) from differing ones (a live bug, since the loser is silently discarded).

### Task 19 — harness performance and two latent traps

Measured at `671e313`: `snapshot` 46.7s, clean `verify` 26.0s, `verify` with a 757-file delta 3m 03s. `parse-al-parallel.sh` walks the same 15,358 files in **8.5s**.

1. **757 `diff` process spawns ≈ 2.5 min** — the dominant cost in the mismatch path. Batch the comparison into one process, or emit the changed-path list and let the caller diff on demand. Output must stay byte-identical: every task in this plan greps `=== CHANGED:` headers and reads the diff bodies, and two built whole-corpus censuses from them. Prove it with `cmp -s`, as Task 13a did.
2. **`build_trees` at 26–47s** — materialises 15,358 tree files (an `awk` `close()` per tree), hashes them in a second pass, tars them in a third.
3. **The 16-thread cap** — at 32 it desyncs with "tree count mismatch". The desync disappears when the parser build is warmed first, which is what `parse-al-parallel.sh` effectively does. One warm-up build in `build_trees` may unlock 32 threads.
4. **M1**: an empty `-T` list makes GNU tar extract the entire archive. Unreachable today (the loop runs only on mismatch, so ≥1 file) but a live trap for any future caller.
5. **M2**: a member missing from the archive aborts the whole extraction instead of degrading for that one file.

### Task 20 — `validate-grammar.sh` Step 8 is a no-op, plus two small ones

**Step 8 reports success without checking anything** when no baseline file is present, which is the current repo state. We made that script exit 0 for the first time in its history; one of its eight steps is green because it is not running. Either make it fail loudly when the baseline is absent, or have it create one on first run — but it must not report a pass for work it did not do. This is the same family as the untracked-helpers defect.

Also: `.grammar_baseline.json` is neither tracked nor ignored (same class as `grammar_analysis.json`, fixed in 13f), and `tools/find_unused_definitions.py` has no trailing newline.

### Task 21 — `#elif` silently degrades a preceding `end;`, and the Task 3 leftovers

`#elif` after an `end;` degrades it the way `#else` did before Task 1 fixed that path — deferred as a minor then, but it is the same **silent** class as the three misparses this release fixes, and it is the last known one.

Also close out Task 3's leftovers:
- The bare `exit;` followed by a genuine parenthesized-expression statement is verified only by an ad-hoc probe. Pin it in `test/corpus/exit_statement_spacing_test.txt` — it is the case the `prec(14)` choice could regress silently.
- `grammar.js`'s `exit_statement` comment implies the choice-split is the only working resolution; it is not, it is the one that works. Reword.
- The changelog should note that `exit (x + y) * 2;` now produces an ERROR where it previously produced a silent wrong tree. alc rejects that form ("'end' expected"), so the error is correct and matches both the compiler and the already-erroring unspaced form.

### Task 22 — re-check the five latent scanner items

Recorded in "Deferred" below as having no constructible failing input. **Item 1 must be re-checked rather than re-read**: it concerned `BEGIN_KEYWORD`/`END_KEYWORD` falling through with characters already consumed, and Task 12 restructured exactly that code into a single-scan dispatch. Task 12's review already found the related constraint at `scanner.c:303-312` and documented it; confirm item 1 is now dead, live, or moot, and say which.

Items 2–5 (the `CONTINUE_AS_IDENTIFIER` early return, whole-word directive classification vs the grammar's unbounded regexes, `towlower` truncation on Windows, the depth counter wrapping at 256) get a constructibility check each: either produce a failing input or record why none exists. Both outcomes are useful; a shrug is not.

### Task 27 — `validate-grammar.sh` cannot reliably report its own failures

Found during Task 20, which fixed the pattern for Step 8 only and correctly flagged the rest rather than widening its scope.

**Two independent defects.**

**1. `set -e` plus bare command substitution.** Line 6 sets `set -e`, and **five** steps assign with `VAR=$(cmd)` and then read `$?`:

```
 56  TEST_OUTPUT=$(tree-sitter test 2>&1)                              Step 2
159  ORPHAN_OUTPUT=$(python3 tools/find_unused_definitions.py 2>&1)    Step 4
201  DUPLICATE_OUTPUT=$(python3 tools/analyze_duplicates.py 2>&1)      Step 5
218  FIELD_TYPES_OUTPUT=$(python3 tools/check-field-types.py 2>&1)     Step 5b
255  FIELDWALK_OUTPUT=$("$FIELDWALK_CC" …)                             Step 5c
```

**Corrected by Task 20's review:** Step 5c belongs in this list and was missed in the original report, while **Step 6 does not belong** — it never reads `$?`, it greps the captured text instead. Step 6's problem is defect 2 below, which is worse and entirely separate.

Only Step 8 (line 319, fixed in Task 20) uses `cmd && VAR=0 || VAR=$?`. When any of the six fails, `set -e` aborts the script at that line: the step's own tailored error message never prints, and every later step is skipped, so one failure masks all subsequent ones. The script does exit non-zero, so this is not a false pass — but it is a gate that cannot tell you what went wrong, and it stops collecting evidence at the first problem. Task 20 hit exactly this: making `check_grammar_health.py --ci` return non-zero made Step 8's new error message unreachable until the idiom was fixed.

**2. Step 6 cannot fail at all — four ways over.** This one *is* a false pass:

- `PARSE_OUTPUT=$(./parse-al-parallel.sh 2>&1 | tail -5)` — a pipeline's exit status is `tail`'s, so it is always 0. A crashed or missing parse run is invisible.
- `if echo "$PARSE_OUTPUT" | grep -q "Success rate:"` has **no `else`**. If that string is absent — crash, changed output format, truncated by `tail -5` — the entire check is skipped silently and the step passes.
- A rate at or below the threshold calls `print_warning`, which does **not** set `VALIDATION_FAILED`. A detected 50% success rate still passes the gate.
- The threshold is **90%** on a project that holds 100%. 1,382 broken files out of 15,358 would go green.

It only runs under `--full`, which is why nobody noticed.

**Fix both.** Use the safe idiom everywhere so each step reports its own failure and the script collects all of them rather than aborting at the first. For Step 6: capture the exit status of `parse-al-parallel.sh` itself rather than a pipeline tail; fail when the expected output is absent instead of skipping; make a below-threshold rate a failure rather than a warning; and set the threshold to something meaningful for a project at 100%, or compare against a recorded baseline rather than a magic constant.

**Prove each step can fail.** Task 25's registry needs exactly these rows, and this task is where the idiom gets established. A step whose failure path has never been executed is not a step.

### Task 26 — `Parse:` diagnostic lines land inside the hashed tree bytes

Deferred out of Task 19 by its implementer, with reasoning I accepted. **Task 25 depends on this**, so do it first.

`tools/tree-harness.sh:122` invokes `tree-sitter parse` with `2>&1`, so diagnostic output joins the parse output that gets split into per-file trees. A `Parse:` line therefore lands inside a tree's byte range, and is both hashed and extracted. Consequences:

- Dormant on BC.History today: 0 errors means no `Parse:` lines, which is why every measurement in this plan is unaffected.
- False-dirty only — it cannot make a run look clean when it is not, which is why it was correctly ranked Minor.
- **But it makes an ERROR-injecting fixture flap**, and Task 25's registry needs exactly that fixture (`parse-al-parallel.sh` with a syntax-error file, and the ERROR-census row). A fixture whose hash changes run to run is not a fixture.

The implementer's warning about the wrong fix is the important part: stripping the line from the hash but not from the extracted payload would make hash and diff disagree — a far worse failure than the one being fixed, and it would break the byte-identical property proved repeatedly in Task 19. **Trim the diagnostic from the tree's byte range for both the hash and the payload, or not at all.**

Prove it the way Task 19 proved everything: `cmp -s` on a real delta before and after, plus a deliberately ERROR-containing corpus whose hash is now stable across runs. Task 19's implementer offered to take this and knows the code; that is the cheapest route.

### Task 25 — gate self-test harness (mutation testing for the validation suite)

Added on the release owner's instruction, and it is the most valuable task in this plan because it stops the rest of it recurring.

**The recurring fault.** Five times this session a tool reported success for work it had not done, and each was found by a human reading code rather than by any gate:

| Tool | How it silently passed |
|---|---|
| `tools/fieldwalk.c` | printed nothing on a miss — indistinguishable from "field has no members" |
| `validate-grammar.sh` Step 8 | reports success when no baseline file exists — **still true today, Task 20** |
| `tools/analyze_duplicates.py` | returned zero extracted rules as a pass |
| `tools/tree-harness.sh` | `\|\| true` swallowed failed chunks; only the *global* total was checked, so offsetting losses passed |
| `validate-grammar.sh` orphan/duplicate/health steps | three helper scripts were untracked, so a fresh clone degraded them to "script not found" warnings |

Two more were tests rather than tools: corpus fixtures in Tasks 7 and 8 that passed identically on the broken grammar. The shape is always the same — **passing looks identical whether the check ran or not.**

**Build `tools/gate-selftest.py`** (or `.sh`, match the repo): a registry of `(gate, injected defect, expected failure)` triples. For each, apply the defect to a scratch copy, run the gate, assert it exits non-zero **and** that its message names the injected problem, then restore. A gate that fails for the wrong reason is not passing this test.

Minimum registry — extend it, do not shrink it:

| Gate | Inject | Must |
|---|---|---|
| `validate-grammar.sh` Step 2 | break one corpus expectation | fail |
| Step 3 ERROR census | an ERROR fixture **outside** the allow-list | fail, naming the file |
| Step 4 orphans | an unreferenced rule | fail |
| Step 5 duplicates | a duplicate rule key | fail *(already proven, Task 18)* |
| Step 5b field types | mutate `node-types.json` | fail *(already proven, Task 17)* |
| Step 5c fieldwalk | break `fieldwalk.c` so it will not compile | fail |
| Step 8 health check | remove the baseline file | fail — **passes today; Task 20 fixes it, this proves the fix** |
| `parse-al-parallel.sh` | one `.al` file with a syntax error | report ≥ 1 error |
| `parse-al-parallel.sh` | **N files never parsed at all** | **must not report 100%** — it does today, see below |
| `tree-harness.sh verify` | mutate exactly one tree in the snapshot | report exactly 1 changed |
| `tree-harness.sh build_trees` | force one chunk to fail | fail loudly *(Task 19 adds the detection)* |

**`parse-al-parallel.sh` has this defect today and it is the gate quoted most often in this plan.** Its "Parsed OK" is set subtraction, not a count of work done:

```sh
file_count=$(wc -l < "$all_files")                      # total = list length
comm -23 "$all_files" "$errors_unsorted" > "$parsed_path"   # parsed = total MINUS files that errored
parsed_final=$(wc -l < "$parsed_path")
```

A file never parsed emits no error line, so it is absent from the error list, so it counts as OK. Demonstrated with `tools/gate-fixtures/chunk-parse-failure/`: **100 of 280 files never parsed, and it still reports 280/280, 0 errors, 100%.** Every "15,358/15,358, 0 errors" in this plan therefore proves that no file *reported* an error — not that every file was read. Fix it to count files actually parsed, and keep the fixture as the regression test.

**Plus a structural sweep, which is the half that generalises.** Every gate must report *how much it examined* — "442 rule keys", "552 test files", "15,358 files" — and that number must be asserted plausible, not merely printed. That is what would have caught the harness's global-total-only check and the untracked helpers. Also grep the gate scripts for `|| true`, `2>/dev/null`, and `if [ -f … ]` guards that degrade to a warning, and require each to be paired with an explicit check that the work happened.

**Do not let this harness become the sixth instance.** It must fail loudly if it cannot apply a mutation, cannot find a gate, or runs zero triples. Prove that: give it a registry entry pointing at a nonexistent gate and show it errors rather than reporting all-pass.

Wire it into CI, not just `validate-grammar.sh` — a self-test that only runs when someone remembers to run the validator inherits the problem it solves.

### Task 24 — seven fields declared in `grammar.js` that do not exist

Found during Task 17, partly by the implementer and partly by a follow-up scan. `grammar.js` writes `field('name', …)` in seven places where the field's only member is a **hidden** token or rule, so tree-sitter drops the field entirely rather than declaring it empty. A reader of `grammar.js` sees `field('operator', kw('is', 5))` and reasonably expects `operator` to be queryable. It is not — it appears in neither `node-types.json` nor the runtime tree.

```
as_expression.operator            field('operator', kw('is', 5))       -> hidden pattern token
is_expression.operator            field('operator', kw('as', 5))       -> hidden pattern token
assignment_statement.operator     field('operator', $._assignment_operator) -> hidden rule
assignment_expression.operator    same
procedure.modifier
xmlport_attribute.attribute_type
xmlport_element.element_type
```

Verified with `tools/fieldwalk.c`: `is_expression` reports the node with **no field members**, and `node-types.json` declares no `operator` on any of the four.

**Note what does and does not catch this.** `tools/check-field-types.py` cannot — it asserts on *declared* fields, and these were never declared. A scan for fields with an empty declared type set finds **zero**, because the field is dropped rather than emptied. The detector is a cross-reference: every `field('x', …)` in `grammar.js` against the field set in `node-types.json`; anything in the former and absent from the latter is dropped. That scan is four lines of Python and belongs in `tools/check-field-types.py` as a standing check, since this class will recur every time someone fields a `kw()`.

For each of the seven, decide: alias the token so the field has a visible member (the `kwCases`/`alias` pattern from Task 15), or delete the `field()` call because the field was never meaningful. Do not assume one answer fits all seven — `operator` on the four expression rules is plausibly worth keeping (consumers want to distinguish `is` from `as`), whereas the xmlport ones may be vestigial. Check each against what a consumer would query for.

### Task 23 — capture/completeness gates → **SUPERSEDED, see the query-coverage harness plan**

**This task's design is withdrawn in favour of `docs/superpowers/plans/2026-08-09-query-coverage-harness.md`**, on the release owner's decision. A second session designed the same gate independently and in far more depth: a 25 KB design spec (`docs/superpowers/specs/2026-08-09-query-coverage-harness-design.md`, already on a second review pass) and a 126 KB implementation plan of fifteen TDD tasks. Its problem statement reaches the same conclusion this plan reached — that all three existing gates are blind to a tree that fails to represent its source — and cites the same two bugs as evidence, plus a third found while designing it (the dropped-field class, now Task 24 here).

Its six detectors subsume the three layers sketched below: lossless coverage, ERROR/MISSING census, dropped-field audit (static and dynamic), reserved-keyword-as-identifier, anchor counting, and a shipped-query audit — with a baseline that ratchets downward, an independent mini-lexer as a cross-check, and `validate-grammar.sh` integration.

**Execute that plan, not this section.** What follows is kept only as the record of how the requirement was framed here, and because two details in it are worth carrying over: the leaf-coverage prototype result (24 of 25 sample files clean, the one hit a BOM column-arithmetic artifact — handle the BOM), and the caution that a detector with a high false-positive rate gets ignored, so a layer whose premise does not survive measurement should be dropped rather than shipped noisy.

**Coordination risk to manage:** that session is committing to `fix/3.4.0-grammar-defects` concurrently. Its four commits so far (`ccbc9f7`, `919226a`, `cb347b0`, `a5b3fed`) are docs-only and have been accepted as-is. Before executing, check whether it has already started implementing — two agents building the same fifteen tasks on one branch would be worse than either building it alone.

#### Original framing (superseded)

Proposed by the release owner, and the most valuable item in this backlog. **Every defect found this session was the tree silently failing to cover or attach source text, and every existing gate is error-count based, so none of them could see it.** `parse-al-parallel.sh` counts ERROR nodes. `validate-grammar.sh` counts ERROR nodes. The tree harness compares named trees against a baseline that was itself produced by the buggy parser. A grammar can drop a keyword, collapse a token to zero width, or attach a return value to the wrong parent, and all three report success.

Build the missing gate as three layers, in this order. Ship layer 1 even if 2 and 3 slip.

**Layer 1 — leaf coverage (losslessness). Prototype confirmed working; build it properly.**

Every non-whitespace byte of every source file must sit inside some **leaf** node. It must be *leaf* coverage, not node coverage: when `begin`/`end` vanished inside `#if`, the enclosing `code_block` still spanned them, so a range check against any node would have passed while a leaf check fails.

Implement over the C API or `tree-sitter parse -c` (the only mode that shows anonymous nodes — plain `parse` prints named nodes only and is blind to exactly what this is testing). Handle the BOM: a `﻿` at file start offsets column arithmetic and produced the single false positive in the prototype. Run it over BC.History and DO.Support-Agents; the expected result is **zero uncovered bytes in 35,954 files**. Wire it into `validate-grammar.sh` and make it fail loudly.

This catches: text in no node at all (Task 12's `begin`/`end`), zero-width token collapse (the `property_name` regression), and any future hidden-token drop. It does **not** catch text attached to the wrong parent.

**Layer 2 — field-population census with a baseline.**

For every node type, record the fraction of instances carrying each field declared in `node-types.json`, across the full corpus. Store it beside the tree snapshot. Fail when a field's population rate drops, and require an explicit baseline update to accept a drop — the same discipline `tools/check-field-types.py` uses for declared shapes, applied to actual population.

This is the layer that answers "are all properties actually captured". A single site losing a field will not trip it (`exit_statement.return_value` went from *n* to *n−1*), but a systematic loss will, and unlike layer 3 it needs no hand-enumerated list of bad shapes.

Take the first census as part of this task and **read it** — a field populated on a suspiciously small fraction of instances is a finding in itself, not just a baseline number.

**Layer 3 — suspicious-shape detectors.**

A small set of node shapes that are almost certainly misparses in AL, run as a corpus census. Candidates from this session: a standalone `parenthesized_expression` in statement position (what `exit (42)` produced), and a `quoted_identifier` immediately followed by a sibling `parenthesized_expression` (what `"My Proc"(42)` produced — currently **0** across all 15,358 trees, consistent with Task 4's fix).

**The premise is unproven.** A grep-level census could not distinguish statement position from nested first-child, so the 322 standalone-`parenthesized_expression` hits mean nothing as measured. Do a tree-aware pass first and find out whether these shapes are rare enough to be detectors. If they are not, say so and drop the layer rather than shipping a noisy check — a detector with a high false-positive rate gets ignored, and an ignored gate is worse than none.

---

## Task 14: Release 4.0.0

**Files:**
- Modify: `CHANGELOG.md`, `package.json`, `Cargo.toml`, `tree-sitter.json`, `package-lock.json`, `Cargo.lock`, `tree-sitter-al.wasm`

**Interfaces:**
- Consumes: Tasks 3–13.
- Produces: published 3.4.0 on GitHub Releases, npm, PyPI, crates.io.

**Version: 4.0.0.** Ruled by the release owner, following the policy stated in `CHANGELOG.md` itself — "the parse-tree shape is the public API — a change to node structure or field names is a **major** bump." Task 9 changed node structure in 757 BC.History files (1,316 added `statement_block` nodes) and Task 12 adds named `begin_keyword`/`end_keyword` inside every `#if` block. Those are exactly the changes that policy names. Shipping them as a minor would contradict the rule in the same file that states it.

Everywhere below that says 3.4.0, read 4.0.0. The `[Unreleased]` heading becomes `## [4.0.0] — <date>`.

**The migration note is part of this task, not optional.** A major bump obliges a consumer-facing account of every tree change, at the top of the 4.0.0 entry, each with the before/after shape:

- `case_else_branch.body` is now a single `statement_block` instead of a repeated statement list — a query taking the Nth child of `body` breaks; one matching `(case_else_branch)` does not.
- `begin_keyword` / `end_keyword` now appear inside `#if` blocks where previously no node covered that text at all (Task 12).
- `array_type.sizes` and `link_value.value` no longer *declare* an anonymous member — declared-type only, no tree moves, but typed bindings regenerate differently.
- `exit_statement` now attaches a `return_value` where a spaced or multi-line `exit (…)` previously dropped it into a detached sibling (Task 3) — the one case where a consumer was getting a *wrong* answer before.

Name the affected downstream work explicitly: the nvim-treesitter queries in flight and `U:\Git\sublime-al`.

- [ ] **Step −1: BLOCKING — review the other session's commits as one block**

A second Claude session executed its own fifteen-task query-coverage-harness plan on this same branch, in parallel, and its commits interleave with ours. **4.0.0 must not ship containing code this process never reviewed.** The release owner's ruling is to let them finish and review their work as a single unit before tagging.

Identify their commits by the files they touch, not by author — every commit in this repo is "Goose Assistant":

```bash
git log --format="%h %s" --name-only <plan-start>..HEAD \
  | grep -B1 -E 'tools/query_coverage/|query-coverage-harness'
```

Known at the time of writing: `ccbc9f7`, `919226a`, `cb347b0`, `a5b3fed`, `de78c9f` (docs), `e8c3f1a`, `2c0fd0e` (code — a `tools/query_coverage/` package, `tools/__init__.py`, a scoped `.gitignore` change). There will be more; their plan has fifteen tasks.

Dispatch one reviewer over the whole set with the same standards used for our own tasks. Things to look at specifically, since nobody in this process has seen any of it: whether `tools/__init__.py` making `tools/` a package affects our own scripts there (`check-field-types.py`, `analyze_duplicates.py`, the `fieldwalk.c` build), whether the `.gitignore` change can unignore anything unintended, and whether their harness's own gates actually fail when they should — the standing rule in this plan is that a check nobody has watched fail is not yet a check.

Confirmed working at the time of writing, so a regression is attributable: `check-field-types.py` 29/29, duplicate check 442 keys, `./validate-grammar.sh` exit 0.

- [ ] **Step 0: Refresh every metric in `CLAUDE.md`, prose included**

Three stale counts were found in that file during Tasks 11 and 12, each contradicting its own metrics table from a different part of the document. Two were fixed; **`CLAUDE.md:5` still says "1451 tests passing"** against the corrected 1,507, and it is the status line at the top — the first thing a reader sees.

Do not fix that one line in isolation. Sweep the whole file against the repo:

```bash
grep -E '^#define (SYMBOL_COUNT|STATE_COUNT)' src/parser.c
ls -l src/parser.c | awk '{printf "%.1f MB\n", $5/1048576}'
wc -l grammar.js
tree-sitter test 2>&1 | grep 'Total parses'
git ls-files queries/ | wc -l
```

and reconcile every figure that appears in prose as well as in the table. The drift pattern here is that the table gets updated and the prose does not, so grep for bare numbers rather than trusting the table.

**Two known items carried forward, both confirmed by Task 15's re-review:**

1. **`CLAUDE.md` lines 60 and 173 say "~12 dedicated split-construct rules". The real count is 20** — Task 15 corrected README to 20 but `CLAUDE.md` was outside its file scope, so the repo currently contradicts itself on the same fact in the same release. Count them yourself before writing the number: 20 distinct `preproc_split_*` / `preproc_fragmented_*` rule definitions, excluding the hidden `_preproc_split_then_begin_open` helper.
2. **README's "What's new in 3.0.0" section** is accurate about 3.0.0 and was deliberately left alone. Deciding whether 4.0.0 gets an equivalent section is this task's call, not a docs-sweep call.

Also re-check the counts Task 15 corrected, since this task changes the parser again: `parser.c` size, `SYMBOL_COUNT`, `STATE_COUNT`, `grammar.js` line count, test count, named keywords (83 = 81 grammar + 2 external), and scanner tokens (9 — `var_attribute_open` at index [8] was uncounted in the docs for its entire existence until Task 15).

- [ ] **Step 1: Confirm every gate one final time**

```bash
tree-sitter --version                          # 0.26.12
tree-sitter generate && git diff --exit-code --stat src/
tree-sitter test
./parse-al-parallel.sh ./BC.History/ .
./parse-al-parallel.sh "U:/Git/DO.Support-Agents/" .
./validate-grammar.sh
```

- [ ] **Step 2: Retitle the changelog section and add the consumer note**

Change `## [Unreleased]` to `## [3.4.0] — <date>` and add, at the top of that section, a list of every node-shape change a consumer must handle: `array_type.sizes` field split, `link_value.value` field split, `case_else_branch.body` now a single `statement_block`, and `begin_keyword`/`end_keyword` now appearing inside `#if` blocks.

- [ ] **Step 3: Bump, regenerate, rebuild, commit**

```bash
sed -i 's/"version": "3.3.1"/"version": "3.4.0"/' package.json tree-sitter.json
sed -i '0,/^version = "3.3.1"/s//version = "3.4.0"/' Cargo.toml
npm install --package-lock-only
cargo check
tree-sitter generate      # embeds the version in parser.c
tree-sitter build --wasm
git add package.json tree-sitter.json Cargo.toml package-lock.json Cargo.lock \
        CHANGELOG.md src/parser.c tree-sitter-al.wasm
git commit -m "chore: bump version to 3.4.0"
```

- [ ] **Step 4: Push, wait for CI, tag, dispatch, verify**

```bash
git push
gh run watch <RUN_ID> --exit-status
git tag v3.4.0 && git push origin v3.4.0
gh workflow run "Build and release artifacts" --ref main
gh release view v3.4.0 --json tagName,assets
npm view @sshadows/tree-sitter-al version
```

- [ ] **Step 5: Snapshot the release baseline**

```bash
NUM_THREADS=16 ./tools/tree-harness.sh snapshot ./BC.History .snapshots/baseline-3.4.0
```

- [ ] **Step 6: Tell the downstream consumers**

The nvim-treesitter work in flight and the `sublime-al` package both depend on node shapes changed by Tasks 7, 8 and 12. Point them at the changelog's consumer note.

---

## Found during execution — worth their own work later

These surfaced while implementing and are recorded here because the SDD workspace (`.superpowers/`) is gitignored scratch and will be deleted; this file is tracked.

1. **`link_value` only models the multi-entry `DataItemLink`.** A single entry — `DataItemLink = "Customer No." = Cust."No.";` — never instantiates `link_value` at all; it parses as `property_expression`/`comparison_expression` with a `member_expression` on the right. Only two-or-more comma-separated entries produce `link_value_list` → `link_value`. So a query written against `link_value` to find DataItemLink relationships silently misses every single-entry case, plausibly the more common shape. Both CST fragments are in Task 8's report. Decide whether `link_value` should cover the single-entry form, or whether the rule is misnamed for what it models.

2. **24 fields in `node-types.json` mix named and anonymous types.** Not all are defects: `operator` on `additive_expression`, `logical_expression`, `unary_expression` and `multiplicative_expression` holds anonymous tokens by design, because the operator token *is* the value. The suspicious ones are separators leaking into multi-value fields — fourteen `body`/`then_branch`/`else_branch` fields carrying `";"` (all downstream of `_statement` owning its own terminator, which may be deliberate), plus `dotnet_type.reference`, `object_reference_type.reference`, `record_type.reference`, `query_dataitem.table_name`, `report_dataitem.table_name`, `simple_table_relation.table` and `tabledata_permission.table_name` carrying `"."`/`"*"`, and `property.value` carrying `"-"`. The original review found three of these. Sorting deliberate from accidental across all 24 is its own piece of work. `tools/check-field-types.py` is the place to encode the verdicts.

3. **`tools/tree-harness.sh` is blind to anonymous-node changes.** It snapshots plain `tree-sitter parse` output (`tools/tree-harness.sh:72`), which prints **named nodes only**. So `VERIFIED — all 15,358 byte-identical` is a true and useful statement about the *named* tree, and it does rule out a token over-matching regression — but it cannot see a change to anonymous children. Task 11 deleted 66 anonymous node types from the public contract while the harness reported zero changed files, and the full CST of essentially every BC.History file containing an `if` had in fact changed. Any task that alters token shape rather than tree shape needs a `--cst`-based check or a `node-types.json` set-diff instead. Do not let "0 of 15,358" carry more weight than it can bear.

4. **A named-node corpus fixture cannot detect the field-shape defect class at all.** The corpus format never shows field labels on anonymous nodes, so a fixture asserting `sizes: (integer)` twice passes identically on the broken and fixed grammar. Anything asserting about *fields* must assert against `node-types.json` — that is why `tools/check-field-types.py` exists. Any future field-shape work must prove its check fails on the unfixed state, or it has added a test that cannot fail.

5. **SETTLED, AND THE ORIGINAL ENTRY WAS WRONG.** This previously said `array_type.sizes` and `link_value.value` were "materially overstated" defects — declared-type-only, with the anonymous token never carried at runtime. **Both were in fact reachable at runtime, and the fixes were more valuable than recorded.** Verified by building the pre-fix parsers at `9501c5c^` and `fcf4a11^` and walking them with `TSTreeCursor`: `array[10,20] of Integer` returned `sizes` = `[10, ',', 20]`, and a dotted `DataItemLink` returned `value` = `[Parent, '.', "No."]`. The comma and the dot both carried the field. Two false sentences had reached the public CHANGELOG and have been corrected in place, with a "Correction to two earlier entries" note recording what changed and why.

   The rest of this entry explains how the wrong conclusion was reached. **Both halves of the original claim were false.** Task 17 demonstrated with a positive control that `tree-sitter parse -c` (and `--xml`) **cannot show fields on anonymous nodes at all**: `additive_expression.operator` is a declared field over an anonymous `'+'`/`'-'`, and `--cst` prints it with no field prefix. The absence of a field prefix therefore proves nothing, which is exactly the evidence those two verdicts rested on. `tree-sitter query` is also unreliable here — `(record_type reference: _ @r)` returns only the first identifier, disagreeing with the cursor.

   **The only sound instrument is a `TSTreeCursor` walk reading `ts_tree_cursor_current_field_name` for every child including anonymous ones** — the mechanism `children_by_field_name` actually uses. Task 17 built one in C against the cached runtime and validated it with two positive controls. Task 17 is re-running the pre-fix commits (`4c56a37~1`, `fcf4a11~1`) with it; this entry and the corresponding CHANGELOG wording will be corrected from that result.

6. **Method rule that follows from the above:** never conclude anything about field membership from `tree-sitter parse`, `parse -c`, `--xml` or `tree-sitter query`. Use a cursor walk. This is why `tools/check-field-types.py` asserts against `node-types.json` rather than against parse output.

## Deferred — not in this plan

Five latent scanner issues were found and deliberately not fixed: no failing input can be constructed for any of them today. They are recorded here so a future change that breaks their invariant is recognisable.

1. `BEGIN_KEYWORD`/`END_KEYWORD` fall through on a failed match with characters already consumed. Harmless only because the grammar never makes both valid in the same state. Task 12 restructures this code — re-check afterwards.
2. `CONTINUE_AS_IDENTIFIER`'s unconditional `return false` would shadow `PROPERTY_NAME` if the two were ever co-valid. They never are.
3. Whole-word directive classification in the scanner diverges from the grammar's non-word-bounded regexes: the grammar accepts `#regionX foo` as a `preproc_region`, the scanner reads the word `regionX` and declines.
4. `towlower` truncation — `lookahead` is `int32_t`, `wint_t` is 16-bit on Windows, and the buffer stores a `char`. Only reachable with invalid AL; no memory-safety impact.
5. The depth counter wraps at 256 nested `#if`. The underflow guard coincidentally restores 0 after the matching `#endif`s.

One grammar item is also deferred, on purpose: `database_reference.table_name` (`grammar.js:3841`) also holds page, report, codeunit, query and xmlport names, so `Page::X` lands in a field called `table_name`. The name misleads anyone writing queries. Renaming it to `target_name` is the right fix but it is a **breaking field rename** — every downstream query using `table_name` stops matching silently, since tree-sitter queries do not error on an unknown field. That deserves its own major release with a migration note, not a slot in 3.4.0.

## The `ae90aea` dangling-else regression — analysis carried forward

Recorded here because `.superpowers/` is gitignored and will be deleted; the full write-up
is at `.superpowers/sdd/2026-08-09-scanner-and-grammar-defect-fixes/regression-wip-report.md`
while that directory survives. **Nothing is committed for this fix; the branch is clean and
at 0 production errors.** Three attempts were made and all had worse collateral than the
bug.

**Root cause.** `code_block`'s `optional(';')` is greedy under `prec.right`, so it consumes
the terminator before any downstream rule exists to inspect it. `ae90aea`'s guard —
`choice(seq(else_keyword, _else_branch), optional(';'))` — can only fire when the `;` is
still unconsumed, which for a block it never is; `prec.dynamic(20)` then lets the else arm
take the case's else. **Four** then-branch forms swallow the `;`, not three: `code_block`, a
nested `if_statement`, `empty_statement`, and `call_statement` (which owns its own).

**Ruled out, with reasons — do not re-attempt these blind:**

1. *Requiring an explicit `';'` on `_if_statement_no_else`.* Cannot work: the block has
   already eaten it, so the requirement finds nothing and that parse dies. Verified: the
   regression shape is unchanged. Works only for a simple-statement then-branch, which is
   why it looks plausible until tested.
2. *Removing `prec.dynamic(20)` and relying on a structural bar alone.* **Undoes defect 1** —
   measured, the original misparse returns.
3. *A `_code_block_no_semi` variant aliased to `code_block`, used only in the else arm.*
   The closest attempt: fixes the regression, keeps all six dangling-else shapes correct,
   corpus green — but **5 BC.History files fail** at `end; #else … #endif`, because giving
   GLR a second route into `preproc_split_code_block_end` mis-drives the split. Dropping the
   split enders from the variant is worse: 7 errors and 13 fixture failures.
4. *Excluding `empty_statement` from the else arm* (needs a real `_statement_inner` subset;
   a forwarding wrapper duplicates the rule and collides with the shared repeat symbol).
   Costs two `preproc_split_if_then_begin_else_shared` fixtures, which regress to
   `then_branch: (MISSING identifier)` — worse than the bug.

**The `unnecessary conflicts: if_statement, _if_statement_no_else` warning is not a valid
gate for this.** It is present at `60b434d` as well as `ae90aea`, so it does not
discriminate the regression — and it *cleared* in exactly the variant that undid defect 1.
On this grammar it tracks "the no-else variant contends at table level", which is precisely
what defect 1's fix removed on purpose.

**Where it lands.** Every workaround fights the same fact: `code_block` owns a `;` that no
downstream rule can see. The fix for the class is the already-queued terminator relocation —
move `optional(';')` out of `code_block` and the branch rules into the statement wrapper, so
terminators are uniformly external. Cost measured during defect 1: ~74,268 `if_statement`
nodes re-spanned plus every `begin … end;`. With that done, this regression is a two-line
fix. Recommendation: promote that task and fix on top of it, or revert `ae90aea` if 23 wrong
sites outweigh the ~156 it repaired.
