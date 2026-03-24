# Stateful Scanner: Named begin/end + Split Detection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a stateful external scanner that tracks `#if`/`#endif` nesting depth, exposing `begin`/`end` as named keyword nodes at depth 0 (for query support) and fixing 3 of the 7 remaining BC.History parse errors via `PREPROC_SPLIT_BEGIN`.

**Architecture:** A 1-byte serialized `ScannerState` (depth counter) is maintained across the scan function. Five new external tokens are appended to the existing two: `PREPROC_OPEN` and `PREPROC_CLOSE` track depth, `BEGIN_KEYWORD` and `END_KEYWORD` are emitted only at depth 0, and `PREPROC_SPLIT_BEGIN` is emitted when `begin` at depth > 0 immediately precedes `#endif`.

**Tech Stack:** C (scanner), JavaScript (grammar.js), tree-sitter CLI, bash (benchmark/validate)

---

## File Structure

| File | Change |
|------|--------|
| `src/scanner.c` | Major: add `ScannerState`, 4 lifecycle functions, 5 new token cases |
| `grammar.js` | Moderate: extend `externals` (5 new tokens), update `preproc_if`, `preproc_endif`, `code_block`, `preproc_split_if_then_begin`, `preproc_fragmented_else_tail` |
| `queries/highlights.scm` | Minor: add `(begin_keyword)` and `(end_keyword)` captures |
| `queries/indents.scm` | Minor: add token-level `(begin_keyword)` and `(end_keyword)` entries |
| `queries/folds.scm` | Minor: add token-level `(begin_keyword)` and `(end_keyword)` entries |
| `test/corpus/` | Auto-updated: run `tree-sitter test -u` to propagate new node names |
| `benchmark-results.txt` | Auto-updated by `benchmark.sh` runs |

---

## Task 1: Save baseline benchmark

**Files:**
- Run: `benchmark.sh`
- Output: `benchmark-results.txt`

- [ ] **Step 1: Run baseline benchmark (200 files)**

```bash
bash benchmark.sh "baseline-before-scanner" 200
```

Expected output includes `Errors:` count and `Per file:` timing. Note these numbers — they are the comparison target.

- [ ] **Step 2: Commit benchmark script if not already committed**

```bash
git status benchmark.sh
# If untracked or modified:
git add benchmark.sh
git commit -m "chore: add benchmark.sh for parse performance measurement"
```

---

## Task 2: Stage 1a — Scanner lifecycle functions + PREPROC_OPEN/CLOSE

**Files:**
- Modify: `src/scanner.c`
- Modify: `grammar.js` (externals array, preproc_if, preproc_endif rules)

### Step 1: Add ScannerState and lifecycle functions to scanner.c

- [ ] **Step 1: Replace the no-op lifecycle functions in `src/scanner.c`**

The current file (line 5-13) has:
```c
enum TokenType {
  PROPERTY_NAME,
  CONTINUE_AS_IDENTIFIER,
};

void *tree_sitter_al_external_scanner_create() { return NULL; }
void tree_sitter_al_external_scanner_destroy(void *payload) {}
unsigned tree_sitter_al_external_scanner_serialize(void *payload, char *buffer) { return 0; }
void tree_sitter_al_external_scanner_deserialize(void *payload, const char *buffer, unsigned length) {}
```

Replace with:
```c
enum TokenType {
  PROPERTY_NAME = 0,
  CONTINUE_AS_IDENTIFIER = 1,
  PREPROC_OPEN = 2,
  PREPROC_CLOSE = 3,
  BEGIN_KEYWORD = 4,
  END_KEYWORD = 5,
  PREPROC_SPLIT_BEGIN = 6,
};

typedef struct {
  uint8_t depth;  // current #if/#endif nesting depth (max 255)
} ScannerState;

void *tree_sitter_al_external_scanner_create() {
  ScannerState *state = calloc(1, sizeof(ScannerState));
  return state;
}

void tree_sitter_al_external_scanner_destroy(void *payload) {
  free(payload);
}

unsigned tree_sitter_al_external_scanner_serialize(void *payload, char *buffer) {
  ScannerState *state = (ScannerState *)payload;
  buffer[0] = (char)state->depth;
  return 1;
}

void tree_sitter_al_external_scanner_deserialize(
  void *payload, const char *buffer, unsigned length
) {
  ScannerState *state = (ScannerState *)payload;
  state->depth = (length > 0) ? (uint8_t)buffer[0] : 0;
}
```

Also add `#include <stdlib.h>` after line 1 (`#include "tree_sitter/parser.h"`).

- [ ] **Step 2: Add helper functions for keyword matching**

Add before `tree_sitter_al_external_scanner_scan`:

```c
// Skip whitespace and newlines (advance without marking)
static void skip_whitespace(TSLexer *lexer) {
  while (lexer->lookahead == ' ' || lexer->lookahead == '\t' ||
         lexer->lookahead == '\r' || lexer->lookahead == '\n' ||
         lexer->lookahead == '\f') {
    lexer->advance(lexer, true);
  }
}

// Read a keyword case-insensitively. Returns true if matched and lookahead is
// not an identifier character after the keyword (i.e., whole word matched).
// Advances the lexer past the keyword on success.
static bool read_keyword_ci(TSLexer *lexer, const char *keyword) {
  for (int i = 0; keyword[i] != '\0'; i++) {
    if (towlower(lexer->lookahead) != keyword[i]) return false;
    lexer->advance(lexer, false);
  }
  // Ensure it's a whole-word match (not followed by identifier chars)
  // For '#if' this means space/newline follows; for 'begin'/'end' same.
  if (is_identifier_char(lexer->lookahead)) return false;
  return true;
}

// Peek (without advancing) whether the keyword follows at current position.
// Skips whitespace first. Returns true if the keyword is found as a whole word.
static bool peek_keyword_ci(TSLexer *lexer, const char *keyword) {
  // We can't actually peek without advancing in the tree-sitter API.
  // This function is used after mark_end() — further advancing does not
  // affect the already-marked token boundary. So we advance freely here.
  skip_whitespace(lexer);
  for (int i = 0; keyword[i] != '\0'; i++) {
    if (towlower(lexer->lookahead) != keyword[i]) return false;
    lexer->advance(lexer, false);
  }
  if (is_identifier_char(lexer->lookahead)) return false;
  return true;
}
```

- [ ] **Step 3: Add PREPROC_OPEN and PREPROC_CLOSE handling in scan function**

The scan function signature changes to use `ScannerState *state`:

```c
bool tree_sitter_al_external_scanner_scan(
  void *payload,
  TSLexer *lexer,
  const bool *valid_symbols
) {
  ScannerState *state = (ScannerState *)payload;

  // PREPROC_OPEN: #if — increment depth
  // Must check before CONTINUE_AS_IDENTIFIER to handle #if at beginning of line
  if (valid_symbols[PREPROC_OPEN]) {
    skip_whitespace(lexer);
    if (lexer->lookahead == '#') {
      lexer->advance(lexer, false);
      if (read_keyword_ci(lexer, "if")) {
        state->depth++;
        lexer->result_symbol = PREPROC_OPEN;
        return true;
      }
    }
  }

  // PREPROC_CLOSE: #endif — decrement depth
  if (valid_symbols[PREPROC_CLOSE]) {
    skip_whitespace(lexer);
    if (lexer->lookahead == '#') {
      lexer->advance(lexer, false);
      if (read_keyword_ci(lexer, "endif")) {
        if (state->depth > 0) state->depth--;
        lexer->result_symbol = PREPROC_CLOSE;
        return true;
      }
    }
  }

  // ... rest of existing CONTINUE_AS_IDENTIFIER and PROPERTY_NAME handling
```

**IMPORTANT:** The existing `CONTINUE_AS_IDENTIFIER` and `PROPERTY_NAME` blocks remain unchanged after the new blocks. The full function structure is:

```
PREPROC_OPEN check
PREPROC_CLOSE check
BEGIN_KEYWORD check      ← Task 3
END_KEYWORD check        ← Task 3
PREPROC_SPLIT_BEGIN check ← Task 5
CONTINUE_AS_IDENTIFIER check  (unchanged)
PROPERTY_NAME check           (unchanged)
return false;
```

For now (Stage 1a), only add the first two blocks and keep the rest as-is.

- [ ] **Step 4: Update `externals` array in grammar.js (lines 94-97)**

Current:
```javascript
externals: ($) => [
  $.property_name,            // identifier followed by = (not :=)
  $.continue_as_identifier,   // 'continue' followed by ':=' (used as variable)
],
```

Replace with:
```javascript
externals: ($) => [
  $.property_name,            // [0] identifier followed by = (not :=)
  $.continue_as_identifier,   // [1] 'continue' followed by ':=' (used as variable)
  $.preproc_open,             // [2] #if — depth++
  $.preproc_close,            // [3] #endif — depth--
  $.begin_keyword,            // [4] 'begin' at depth 0
  $.end_keyword,              // [5] 'end' at depth 0
  $.preproc_split_begin,      // [6] 'begin' at depth > 0, immediately before #endif
],
```

- [ ] **Step 5: Update `preproc_if` rule (line 2441) to use `$.preproc_open`**

Current:
```javascript
preproc_if: $ => seq(
  choice('#if', '#IF', '#If'),
  field('condition', choice(
    $.identifier,
    $.preproc_not_expression,
  ))
),
```

Replace with:
```javascript
preproc_if: $ => seq(
  $.preproc_open,
  field('condition', choice(
    $.identifier,
    $.preproc_not_expression,
  ))
),
```

- [ ] **Step 6: Update `preproc_endif` rule (line 2464) to use `$.preproc_close`**

Current:
```javascript
preproc_endif: $ => choice('#endif', '#ENDIF', '#Endif'),
```

Replace with:
```javascript
preproc_endif: $ => $.preproc_close,
```

- [ ] **Step 7: Generate and test**

```bash
tree-sitter generate && tree-sitter test 2>&1 | tail -20
```

Expected: all 1404 tests pass. If preproc_if/endif tests fail with structural changes (node type changed to `preproc_open`/`preproc_close`), that means the grammar change was correct — update tests next.

> If tests fail with ERROR or MISSING nodes: DO NOT run `-u`. Diagnose the failure with `tree-sitter parse <failing-file.al> -d`.

- [ ] **Step 8: Update test expectations**

```bash
tree-sitter test -u
```

Only run this if zero ERROR/MISSING nodes were seen in step 7. Corpus tests that mention `#if`/`#endif` will now show `(preproc_open)`/`(preproc_close)` in the tree.

- [ ] **Step 9: Commit Stage 1a**

```bash
git add src/scanner.c grammar.js test/corpus/
git commit -m "feat: Stage 1a — stateful scanner lifecycle + PREPROC_OPEN/CLOSE

Adds ScannerState with 1-byte depth counter. PREPROC_OPEN (#if) increments
depth; PREPROC_CLOSE (#endif) decrements. Lifecycle functions now allocate,
serialize, and deserialize state. preproc_if and preproc_endif rules updated
to use external tokens.

[BC.History: 7 errors, 99.95% success]"
```

---

## Task 3: Stage 1b — BEGIN_KEYWORD / END_KEYWORD + code_block update

**Files:**
- Modify: `src/scanner.c` (add BEGIN_KEYWORD and END_KEYWORD cases)
- Modify: `grammar.js` (update `code_block` rule)

- [ ] **Step 1: Add BEGIN_KEYWORD and END_KEYWORD cases to scan function**

Insert after the PREPROC_CLOSE block and before the CONTINUE_AS_IDENTIFIER block:

```c
// BEGIN_KEYWORD: 'begin' at depth 0 only — decline at depth > 0
if (valid_symbols[BEGIN_KEYWORD] && state->depth == 0) {
  skip_whitespace(lexer);
  if (read_keyword_ci(lexer, "begin")) {
    lexer->result_symbol = BEGIN_KEYWORD;
    return true;
  }
}

// END_KEYWORD: 'end' at depth 0 only — decline at depth > 0
if (valid_symbols[END_KEYWORD] && state->depth == 0) {
  skip_whitespace(lexer);
  if (read_keyword_ci(lexer, "end")) {
    lexer->result_symbol = END_KEYWORD;
    return true;
  }
}
```

**Why the scanner declines at depth > 0:** When `valid_symbols[BEGIN_KEYWORD]` is true but `state->depth > 0`, the `if` guard fails and we fall through. The grammar's `kw('begin')` regex then handles it via the anonymous token path. This is NOT the scanner choosing between tokens — it is the scanner declining one alternative so the grammar's other alternative can fire.

- [ ] **Step 2: Update `code_block` rule in grammar.js (line 2267)**

Current:
```javascript
code_block: $ => prec.right(seq(
  kw('begin'),
  repeat($._statement),
  kw('end'),
  optional(';'),
)),
```

Replace with:
```javascript
code_block: $ => prec.right(seq(
  choice($.begin_keyword, kw('begin')),
  repeat($._statement),
  choice($.end_keyword, kw('end')),
  optional(';'),
)),
```

At depth 0: scanner emits `BEGIN_KEYWORD`; parse tree shows `(begin_keyword)`.
At depth > 0: scanner declines; `kw('begin')` matches anonymously; parse tree shows `"begin"`.

- [ ] **Step 3: Generate and test (zero errors required)**

```bash
tree-sitter generate && tree-sitter test 2>&1 | tail -30
```

Expected: all tests pass. Any test with `code_block` at depth 0 will now show `(begin_keyword)` and `(end_keyword)` instead of `"begin"`/`"end"`. Count the failures before running `-u` to confirm the change is purely structural.

> If you see CONFLICT warnings during generate: they indicate the grammar has ambiguity. The scanner decline mechanism should prevent this, but if conflicts appear, add `prec(1, $.begin_keyword)` inside the `choice()` to resolve.

- [ ] **Step 4: Update all test expectations**

```bash
tree-sitter test -u
```

This will update ~400+ test cases. Confirm with:
```bash
tree-sitter test 2>&1 | grep -E "^  [0-9]+ tests"
```
Expected: `1404 tests passed, 0 failed`.

- [ ] **Step 5: Spot-check the update correctness**

```bash
# Check that begin_keyword appears in updated tests
grep -l "begin_keyword" test/corpus/*.txt | head -5 | while read f; do
  echo "=== $f ==="; grep -c "begin_keyword" "$f"; done
```

Also verify that preproc_split tests (which use `begin` inside `#if`) still show anonymous `"begin"`:
```bash
grep -A5 "preproc_split_if_then_begin" test/corpus/preprocessor_split.txt | head -20
```

- [ ] **Step 6: Commit Stage 1b**

```bash
git add src/scanner.c grammar.js test/corpus/
git commit -m "feat: Stage 1b — BEGIN_KEYWORD/END_KEYWORD + named code_block tokens

code_block now uses choice(begin_keyword, kw('begin')) so scanner emits
named tokens at depth 0. At depth > 0, scanner declines and anonymous
kw() tokens handle preproc_split contexts unchanged.

~400+ test expectations updated to show (begin_keyword)/(end_keyword).

[BC.History: 7 errors, 99.95% success]"
```

---

## Task 4: Stage 1c — Query updates

**Files:**
- Modify: `queries/highlights.scm`
- Modify: `queries/indents.scm`
- Modify: `queries/folds.scm`

- [ ] **Step 1: Update highlights.scm**

Find the comment near line 5:
```scheme
; Keywords are exposed as named nodes (e.g., if_keyword, table_keyword) for
; precise highlighting. Note: begin/end use kw() regex tokens and cannot be
; matched in queries.
```

Update the comment and add captures in the keyword list:
```scheme
; Keywords are exposed as named nodes (e.g., if_keyword, table_keyword) for
; precise highlighting. begin/end are named at depth 0 via external scanner.
```

Then add to the keyword capture list (find the `@keyword` section that lists named keyword nodes):
```scheme
(begin_keyword) @keyword
(end_keyword) @keyword
```

- [ ] **Step 2: Update indents.scm**

Current (line 32-33):
```scheme
; Code blocks (begin ... end)
(code_block) @indent.begin
```

The current node-level capture already works for indentation. However, for editors that want token-level anchoring, add the named token captures. Find the `@indent.end` section (after line 177 `; Indent End`) and add:

```scheme
; Code block begin/end tokens (at depth 0 — named nodes)
(code_block (begin_keyword) @indent.begin)
(code_block (end_keyword) @indent.end)
```

Note: Keep the existing `(code_block) @indent.begin` — the token-level captures are additive and give editors more precise anchoring.

- [ ] **Step 3: Update folds.scm**

Current (line 45):
```scheme
(code_block) @fold
```

This node-level fold already works. Optionally add token-level fold markers for editors that need them:
```scheme
; Named begin/end tokens for precise fold boundaries
(code_block (begin_keyword) @fold.start)
(code_block (end_keyword) @fold.end)
```

Note: Only add if the fold spec format supports `@fold.start`/`@fold.end`. If the editor convention is `@fold` on the node, leave as-is.

- [ ] **Step 4: Validate query files**

```bash
tree-sitter generate
# Test highlights query
tree-sitter highlight test/corpus/codeunit.txt 2>&1 | head -20
```

If `tree-sitter highlight` reports unknown capture names, remove the unsupported captures.

- [ ] **Step 5: Run full benchmark after Stage 1**

```bash
bash benchmark.sh "after-stage1" 200
```

Compare `Per file:` time against baseline from Task 1. Expected: < 2% slower.

- [ ] **Step 6: Commit Stage 1c**

```bash
git add queries/highlights.scm queries/indents.scm queries/folds.scm
git commit -m "feat: Stage 1c — query files updated for named begin/end keywords

highlights.scm: (begin_keyword)/(end_keyword) @keyword captures
indents.scm: token-level anchors for code_block begin/end
folds.scm: token-level fold markers for code_block

[BC.History: 7 errors, 99.95% success]"
```

---

## Task 5: Stage 2 — PREPROC_SPLIT_BEGIN + fix Pattern 1 (3 files)

**Files:**
- Modify: `src/scanner.c` (add PREPROC_SPLIT_BEGIN case)
- Modify: `grammar.js` (`preproc_split_if_then_begin` and `preproc_fragmented_else_tail` rules)

### Background

Pattern 1 root cause: `preproc_split_if_then_begin` expects `begin` to appear immediately after `then`, but failing files have preamble statements before the `if`:

```al
#if not CLEAN24
    NoSeriesMgt.RaiseObsoleteOnBeforeInitSeries(...);  // preamble statement
    if not IsHandled then begin                         // the split begin
#endif
```

`PREPROC_SPLIT_BEGIN` allows the grammar to distinguish this `begin` (at depth > 0, immediately before `#endif`) from all other `begin` tokens.

- [ ] **Step 1: Add PREPROC_SPLIT_BEGIN case to scan function**

Insert after the `END_KEYWORD` block and before `CONTINUE_AS_IDENTIFIER`:

```c
// PREPROC_SPLIT_BEGIN: 'begin' at depth > 0, immediately before #endif
//
// '#' handling: peek_keyword_ci is called with "#endif" (the full string
// including '#'). PREPROC_OPEN/CLOSE manually advance past '#' before calling
// read_keyword_ci("if"/"endif"). These are DIFFERENT conventions — do not mix.
//
// mark_end note: The design spec pseudocode calls mark_end() before return false,
// describing it as the mechanism that "preserves consumed begin." This is inaccurate.
// tree-sitter resets the lexer to its pre-scan() position when false is returned —
// mark_end has no effect on false returns. This implementation correctly omits it.
// The outcome is identical: anonymous kw('begin') re-scans from the original position.
if (valid_symbols[PREPROC_SPLIT_BEGIN] && state->depth > 0) {
  skip_whitespace(lexer);
  if (read_keyword_ci(lexer, "begin")) {
    if (peek_keyword_ci(lexer, "#endif")) {
      lexer->result_symbol = PREPROC_SPLIT_BEGIN;
      return true;
    }
    // 'begin' found but #endif not next — return false.
    // tree-sitter resets lexer to pre-scan position; anonymous kw('begin') fires.
    return false;
  }
  return false;
}
```

**How the fallback works:** When the scanner returns `false`, tree-sitter resets the lexer position to exactly where it was before `scan()` was called. All scanner advances are discarded. The internal regex lexer re-scans from that original position, and the anonymous `kw('begin')` regex matches `begin` from scratch.

- [ ] **Step 2: Update `preproc_split_if_then_begin` rule (line 2567)**

Current:
```javascript
preproc_split_if_then_begin: $ => prec(25, seq(
  $.preproc_if,
  $.if_keyword,
  field('condition', $._expression),
  $.then_keyword,
  kw('begin'),
  $.preproc_endif,
  repeat($._statement),
  $.preproc_if,
  kw('end'),
  optional(';'),
  $.preproc_endif,
)),
```

Replace with:
```javascript
preproc_split_if_then_begin: $ => prec(26, seq(
  $.preproc_if,
  repeat($._statement),           // allow preamble statements before if
  $.if_keyword,
  field('condition', $._expression),
  $.then_keyword,
  $.preproc_split_begin,          // 'begin' at depth > 0, before #endif
  $.preproc_endif,
  repeat($._statement),
  $.preproc_if,
  repeat($._statement),           // allow preamble before end
  kw('end'),
  optional(';'),
  $.preproc_endif,
)),
```

Note: Precedence bumped from 25 to 26 to ensure this rule wins over `preproc_conditional_statement` when preamble statements are present.

- [ ] **Step 3: Update `preproc_fragmented_else_tail` rule (line 2583)**

Current:
```javascript
preproc_fragmented_else_tail: $ => prec(25, seq(
  kw('begin'),
  $.preproc_endif,
  repeat($._statement),
  $.preproc_if,
  kw('end'),
  optional(';'),
  $.preproc_endif,
)),
```

Replace with:
```javascript
preproc_fragmented_else_tail: $ => prec(25, seq(
  $.preproc_split_begin,          // 'begin' at depth > 0, before #endif
  $.preproc_endif,
  repeat($._statement),
  $.preproc_if,
  kw('end'),
  optional(';'),
  $.preproc_endif,
)),
```

- [ ] **Step 4: Generate and test**

```bash
tree-sitter generate && tree-sitter test 2>&1 | tail -20
```

If existing preproc_split tests fail (they used `kw('begin')` before), update expectations:
```bash
tree-sitter test -u
```

Only run `-u` if failures are structural (no ERROR/MISSING nodes).

- [ ] **Step 5: Validate against BC.History to confirm error count drops**

```bash
./parse-al-parallel.sh ./BC.History/ .
```

Expected: errors drop from 7 to ≤ 4 (fixing Pattern 1's 3 files). Check `./BC.History/errors.txt` to confirm the 3 Pattern 1 files are no longer in the list.

If errors do NOT drop:
```bash
# Parse one of the Pattern 1 files with debug output
tree-sitter parse <pattern1-file.al> -d > debug.log 2>&1
python parse_bug_finder.py <pattern1-file.al> debug.log
```

- [ ] **Step 6: Run post-Stage 2 benchmark**

```bash
bash benchmark.sh "after-stage2" 200
```

- [ ] **Step 7: Commit Stage 2**

```bash
git add src/scanner.c grammar.js test/corpus/
git commit -m "feat: Stage 2 — PREPROC_SPLIT_BEGIN fixes Pattern 1 parse errors

PREPROC_SPLIT_BEGIN is emitted when 'begin' appears at depth > 0 and is
immediately followed by #endif. preproc_split_if_then_begin now accepts
preamble statements before the 'if'. preproc_fragmented_else_tail updated.

3 of 7 BC.History errors fixed (Pattern 1 — preamble-before-split-begin).

[BC.History: 4 errors, 99.97% success]"
```

(Adjust error count in commit message based on actual results.)

---

## Task 6: Full validation and CLAUDE.md update

**Files:**
- Run: `validate-grammar.sh --full`
- Modify: `CLAUDE.md` (update metrics and begin/end limitation note)

- [ ] **Step 1: Run full validation**

```bash
./validate-grammar.sh --full
```

Expected: all tests pass, no orphan/duplicate rules, production parse succeeds.

- [ ] **Step 2: Update CLAUDE.md — remove begin/end limitation note**

Find in `CLAUDE.md`:
```markdown
**begin/end MUST stay anonymous** — Named nodes (by ANY mechanism: named rules, named alias, anonymous alias) break GLR backtracking in preprocessor-split constructs. This is a fundamental tree-sitter limitation.
```

Replace with:
```markdown
**begin/end are named via external scanner** — `begin_keyword` and `end_keyword` are emitted at depth 0 (outside `#if` blocks). At depth > 0, the scanner declines and anonymous `kw('begin')`/`kw('end')` tokens handle preprocessor-split contexts. Direct naming via grammar rules or `alias()` still breaks GLR backtracking — the stateful scanner is the correct approach.
```

Also update the scanner tokens table in `CLAUDE.md` to include the 5 new tokens.

Update the "Remaining 7 Errors" note to reflect the new count.

Update Parser Metrics table (named keywords now 82 including begin_keyword, end_keyword; errors reduced).

- [ ] **Step 3: Commit CLAUDE.md update**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with stateful scanner architecture and new error count"
```

---

## Task 7: Post-implementation verification checklist

- [ ] **Check query functionality**: Open a `.al` file in an editor with tree-sitter support and verify `begin`/`end` are highlighted as keywords.
- [ ] **Check no test regressions**: `tree-sitter test` passes all 1404 (or more if new tests added).
- [ ] **Check benchmark within tolerance**: `per file` time from `after-stage2` is within 2% of baseline.
- [ ] **Check error files list is shorter**: `wc -l ./BC.History/errors.txt` should show ≤ 4 files.
- [ ] **Verify depth tracking correctness**: Parse a file with nested `#if` inside a `code_block` and confirm `begin`/`end` inside the outer block (but outside inner `#if`) shows `(begin_keyword)`.

```bash
# Create a test file for nested depth
cat > /tmp/depth_test.al << 'EOF'
codeunit 50000 Test {
    procedure Foo()
    begin
        #if CONDITION
        x := 1;
        #endif
    end;
}
EOF
tree-sitter parse /tmp/depth_test.al
```

Expected output includes `(begin_keyword)` and `(end_keyword)` for the procedure body, confirming depth resets correctly across `#if`/`#endif` inside the block.

---

## Notes

### Token ordering constraint
The `TokenType` enum in `src/scanner.c` and the `externals` array in `grammar.js` must match by position. `PROPERTY_NAME=0` and `CONTINUE_AS_IDENTIFIER=1` must never move. New tokens at positions 2-6 are safe to append.

### PREPROC_SPLIT_BEGIN fallback mechanism
When `PREPROC_SPLIT_BEGIN` is in `valid_symbols` but `#endif` is not found after `begin`, the scanner returns `false`. Tree-sitter resets the lexer to its pre-`scan()` position on `false` returns — all advances are discarded. The internal regex lexer re-scans from the original position, and the anonymous `kw('begin')` matches from scratch. preproc_split_* rules that do NOT include `$.preproc_split_begin` continue to use anonymous `kw('begin')` unchanged.

**Spec divergence:** The spec pseudocode calls `lexer->mark_end(lexer)` before `return false`, describing it as preserving the consumed `begin`. This is inaccurate — `mark_end` has no effect on `false` returns. The plan omits `mark_end` here for correctness and clarity.

### Stage 2 Pattern 2 (deferred)
The remaining 3 errors after Stage 2 are Pattern 2 (procedure begin variants across `#if` branches). These require a follow-on spec — do NOT attempt to fix them in this implementation.

### Dangling-else fix (IncomingDocument.Table.al)
The 1 remaining error from Pattern 3 is documented separately in `docs/dangling-else-fix.md`.
