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

If `tree-sitter generate` now reports a conflict between `exit_statement` and `parenthesized_expression` (a bare `exit` statement followed by a parenthesized expression statement is genuinely ambiguous without `token.immediate`), resolve it by raising the precedence on the optional group rather than by restoring `token.immediate`:

```javascript
      optional(prec(14, seq(
        '(',
        optional(field('return_value', $._expression)),
        ')'
      )))
```

- [ ] **Step 5: Run all three gates**

```bash
tree-sitter test
./parse-al-parallel.sh ./BC.History/ .
NUM_THREADS=16 ./tools/tree-harness.sh verify ./BC.History .snapshots/baseline-3.3.1 > /tmp/h.txt 2>&1
grep -c '=== CHANGED:' /tmp/h.txt
```

BC.History uses the unspaced `exit(x)` form throughout, so the harness should report VERIFIED. If any file changed, read the diff before proceeding — a spaced `exit` in production would have been silently losing its return value.

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

`_preproc_expression` (`grammar.js:2869-2874`) has only bare identifiers as atoms, so `#if (FOO)` and `#if not (FOO and BAR)` emit `(MISSING identifier)` as the condition and push the `(…)` into the branch as an expression statement. alc accepts both.

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

## Task 13: two tooling checks that can never pass

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

## Task 14: Release 3.4.0

**Files:**
- Modify: `CHANGELOG.md`, `package.json`, `Cargo.toml`, `tree-sitter.json`, `package-lock.json`, `Cargo.lock`, `tree-sitter-al.wasm`

**Interfaces:**
- Consumes: Tasks 3–13.
- Produces: published 3.4.0 on GitHub Releases, npm, PyPI, crates.io.

**Version:** 3.4.0, not 3.3.2. Tasks 7, 8 and 12 change node structure and field shapes, and this repo's semver treats the parse tree as the public API — structure changes are at least a minor bump. (A strict reading makes Task 12 a major; it only *adds* nodes and removes none, so minor is defensible, but call it out in the changelog under a **Breaking for consumers** heading.)

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

## Deferred — not in this plan

Five latent scanner issues were found and deliberately not fixed: no failing input can be constructed for any of them today. They are recorded here so a future change that breaks their invariant is recognisable.

1. `BEGIN_KEYWORD`/`END_KEYWORD` fall through on a failed match with characters already consumed. Harmless only because the grammar never makes both valid in the same state. Task 12 restructures this code — re-check afterwards.
2. `CONTINUE_AS_IDENTIFIER`'s unconditional `return false` would shadow `PROPERTY_NAME` if the two were ever co-valid. They never are.
3. Whole-word directive classification in the scanner diverges from the grammar's non-word-bounded regexes: the grammar accepts `#regionX foo` as a `preproc_region`, the scanner reads the word `regionX` and declines.
4. `towlower` truncation — `lookahead` is `int32_t`, `wint_t` is 16-bit on Windows, and the buffer stores a `char`. Only reachable with invalid AL; no memory-safety impact.
5. The depth counter wraps at 256 nested `#if`. The underflow guard coincidentally restores 0 after the matching `#endif`s.

One grammar item is also deferred, on purpose: `database_reference.table_name` (`grammar.js:3841`) also holds page, report, codeunit, query and xmlport names, so `Page::X` lands in a field called `table_name`. The name misleads anyone writing queries. Renaming it to `target_name` is the right fix but it is a **breaking field rename** — every downstream query using `table_name` stops matching silently, since tree-sitter queries do not error on an unknown field. That deserves its own major release with a migration note, not a slot in 3.4.0.
