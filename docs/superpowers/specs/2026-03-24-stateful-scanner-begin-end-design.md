# Stateful Scanner: Named begin/end + Split Detection

**Date:** 2026-03-24
**Status:** Approved (Stage 1 + Stage 2 Pattern 1 only; Pattern 2 requires follow-on spec)
**Goal:** Named `begin_keyword`/`end_keyword` nodes for query support (Stage 1); fix Pattern 1 of 7 remaining parse errors via `PREPROC_SPLIT_BEGIN` (Stage 2)

---

## Problem

`begin` and `end` are the only keywords among AL's 80+ named keyword nodes that remain anonymous. They cannot be named via grammar rules or `alias()` because any naming mechanism produces a different token type that breaks GLR backtracking in `preproc_split_*` rules.

The root cause: before the parser commits to `code_block` vs `preproc_split_*`, there exist combined parse states where both alternatives are active. If `begin` is a named token, the lexer emits it and collapses the GLR fork prematurely — killing the preproc branch.

The stateful scanner sidesteps this by using the preprocessor depth (computed from already-lexed input) to deterministically decline or emit the named tokens at each position. The scanner's decision is based on its own serialized state, not on parser state.

---

## Approach: Stateful Scanner with Split Detection (Approach C)

### Scanner State

```c
typedef struct {
    uint8_t depth;  // current #if/#endif nesting depth (max 255)
} ScannerState;
```

Serialized as 1 byte via the 4 lifecycle functions (see Scanner Lifecycle below).

### External Tokens (5 new, appended after existing 2)

**IMPORTANT:** New tokens must be **appended** to the end of both the C `TokenType` enum and the `externals` array in `grammar.js`. The existing `PROPERTY_NAME=0` and `CONTINUE_AS_IDENTIFIER=1` must keep their positions or the scanner breaks silently.

```c
enum TokenType {
    PROPERTY_NAME = 0,         // existing
    CONTINUE_AS_IDENTIFIER = 1, // existing
    PREPROC_OPEN = 2,           // new
    PREPROC_CLOSE = 3,          // new
    BEGIN_KEYWORD = 4,          // new
    END_KEYWORD = 5,            // new
    PREPROC_SPLIT_BEGIN = 6,    // new
};
```

| Token | Grammar role | Scanner behavior | Depth effect |
|-------|-------------|-----------------|--------------|
| `PREPROC_OPEN` | Replaces `#if` in `preproc_if` rule | Reads the three casing variants of `#if` that `preproc_if` accepts; depth++ | +1 |
| `PREPROC_CLOSE` | Replaces `#endif` in `preproc_endif` rule | Reads `#endif`; depth-- | -1 |
| `BEGIN_KEYWORD` | Used in `code_block` and non-split rules | Declines (returns false) when `depth > 0`; emitted when `depth == 0` | none |
| `END_KEYWORD` | Used in `code_block` and non-split rules | Declines (returns false) when `depth > 0`; emitted when `depth == 0` | none |
| `PREPROC_SPLIT_BEGIN` | Used in `preproc_split_*` rules (Stage 2) | Emitted when `depth > 0` AND lookahead finds `#endif` after `begin` | none |

Note: The AL grammar does not support `#ifdef`/`#ifndef` directives. `PREPROC_OPEN` only needs to match the `#if` casing variants already accepted by `preproc_if`. `#else`/`#elif` do **not** change depth and are handled by the internal lexer as before.

### Scanner Logic (pseudocode)

```c
// PREPROC_OPEN: #if — increment depth
if (valid_symbols[PREPROC_OPEN]) {
    if (read_keyword_ci(lexer, "#if")) {  // matches '#if', '#IF', '#If' etc.
        state->depth++;
        lexer->result_symbol = PREPROC_OPEN;
        return true;
    }
}

// PREPROC_CLOSE: #endif — decrement depth
if (valid_symbols[PREPROC_CLOSE]) {
    if (read_keyword_ci(lexer, "#endif")) {
        if (state->depth > 0) state->depth--;
        lexer->result_symbol = PREPROC_CLOSE;
        return true;
    }
}

// BEGIN_KEYWORD: 'begin' at depth 0 only — decline at depth > 0
if (valid_symbols[BEGIN_KEYWORD] && state->depth == 0) {
    if (read_keyword_ci(lexer, "begin")) {
        lexer->result_symbol = BEGIN_KEYWORD;
        return true;
    }
}

// END_KEYWORD: 'end' at depth 0 only — decline at depth > 0
if (valid_symbols[END_KEYWORD] && state->depth == 0) {
    if (read_keyword_ci(lexer, "end")) {
        lexer->result_symbol = END_KEYWORD;
        return true;
    }
}

// PREPROC_SPLIT_BEGIN: 'begin' at depth > 0, immediately before #endif
// When this returns false, mark_end ensures the lexer position is restored
// to after 'begin', and the grammar's anonymous kw('begin') handles it.
if (valid_symbols[PREPROC_SPLIT_BEGIN] && state->depth > 0) {
    if (read_keyword_ci(lexer, "begin")) {
        lexer->mark_end(lexer);       // save position after 'begin'
        skip_whitespace_newlines(lexer);
        if (peek_keyword_ci(lexer, "#endif")) {
            lexer->result_symbol = PREPROC_SPLIT_BEGIN;
            return true;
        }
    }
    return false;  // 'begin' not immediately before #endif; anonymous fallback
}

return false;
```

**PREPROC_SPLIT_BEGIN fallback behavior:** `lexer->mark_end(lexer)` is called after consuming `begin` characters. If `#endif` is not found ahead, `return false` is reached. The tree-sitter runtime uses the marked-end position as the token boundary, leaving `begin` to be matched by the grammar's anonymous `kw('begin')` regex. This is the correct fallback — preproc_split_* rules that do NOT use `PREPROC_SPLIT_BEGIN` continue to use `kw('begin')` unchanged.

### Scanner Lifecycle Functions

All 4 lifecycle functions need updating from the current no-op stubs:

```c
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

### Why This Is Correct

- `begin`/`end` at `depth == 0` can **never** be part of a `preproc_split_*` rule. Split constructs, by definition, have `begin`/`end` inside `#if` blocks (depth > 0).
- At `depth > 0`, `BEGIN_KEYWORD`/`END_KEYWORD` are not emitted (scanner returns false). The internal lexer handles `begin`/`end` as anonymous tokens. Existing `preproc_split_*` rules using `kw('begin')`/`kw('end')` continue to work unchanged.
- When `choice($.begin_keyword, kw('begin'))` is in a parse state, tree-sitter passes `BEGIN_KEYWORD` in `valid_symbols`. The scanner either emits it (depth 0) or declines (depth > 0). When the scanner declines, the grammar's `kw('begin')` regex fires for the `code_block` branch. This is not "the scanner picks a token" — it is the scanner declining one alternative and the grammar handling the other.
- Depth is computed from already-lexed input via serialized state. It does not depend on parser state, making it deterministic across all GLR branches at a given position.
- `PREPROC_SPLIT_BEGIN` is only emitted when `depth > 0` AND `#endif` follows immediately. This precisely identifies a split-begin without ambiguity. All other `begin` tokens at depth > 0 fall back to anonymous via the `mark_end`/`return false` mechanism.

### Nested Context Correctness

When `preproc_split_if_then_begin` is used as a `_statement` inside a `code_block` that is itself inside a `#if` block, depth is already ≥ 1. The rule's two `$.preproc_if` tokens will increment depth further (+1 each), and the two `$.preproc_endif` tokens will decrement it back. Net depth change across the entire rule is zero, so outer depth state is preserved correctly.

---

## Stage 1: Named begin/end Nodes

### Grammar Changes

**1. Append external tokens to `externals` array (order must match enum above):**
```javascript
externals: ($) => [
    $.property_name,           // existing [0]
    $.continue_as_identifier,  // existing [1]
    $.preproc_open,            // new [2]
    $.preproc_close,           // new [3]
    $.begin_keyword,           // new [4]
    $.end_keyword,             // new [5]
    $.preproc_split_begin,     // new [6]
],
```

**2. Update `preproc_if` to use `$.preproc_open`** (replaces the `#if` regex token):
```javascript
// Before: preproc_if: $ => seq(token(prec(11, /#if\b/i)), field('condition', ...), ...)
// After:
preproc_if: $ => seq($.preproc_open, field('condition', ...), ...)
```

**3. Update `preproc_endif` to use `$.preproc_close`** (replaces the `#endif` regex token):
```javascript
// Before: preproc_endif: $ => token(prec(11, /#endif\b/i))
// After:
preproc_endif: $ => $.preproc_close
```

**4. Update `code_block` to accept both named (depth 0) and anonymous (depth > 0):**
```javascript
code_block: $ => prec.right(seq(
    choice($.begin_keyword, kw('begin')),  // scanner declines BEGIN_KEYWORD at depth > 0
    repeat($._statement),
    choice($.end_keyword, kw('end')),
    optional(';'),
)),
```

At depth 0: scanner emits `BEGIN_KEYWORD`; `code_block` parse tree shows `(begin_keyword)`.
At depth > 0: scanner declines; `kw('begin')` matches anonymously; parse tree shows `"begin"`.

### Parse Tree Result

```
// Normal code (depth 0):
(code_block
  (begin_keyword)     ← named, queryable
  ...statements...
  (end_keyword))      ← named, queryable

// Inside #if block (depth > 0):
(code_block
  "begin"             ← anonymous (preproc_split rules work unchanged)
  ...statements...
  "end")              ← anonymous
```

### Test Corpus Update

After Stage 1, **all test cases containing `code_block`** will show `(begin_keyword)` and `(end_keyword)` instead of bare `"begin"`/`"end"`. Run:

```bash
tree-sitter generate && tree-sitter test -u
```

Only run `-u` after confirming zero ERROR/MISSING nodes. With ~400+ test cases affected, this is expected and correct.

### Query Updates (after Stage 1)

```scheme
; highlights.scm
(begin_keyword) @keyword
(end_keyword) @keyword

; indents.scm
(code_block (begin_keyword) @indent.begin)
(code_block (end_keyword) @indent.end)

; folds.scm
(code_block (begin_keyword) @fold.start)
(code_block (end_keyword) @fold.end)
```

---

## Stage 2: Fix Parse Errors (Pattern 1 — 3 files)

### Scope

Stage 2 addresses 3 of the 7 errors using `PREPROC_SPLIT_BEGIN`. The remaining 4 errors (3 from Pattern 2 + 1 dangling-else) are tracked separately:
- Pattern 2 (procedure begin variants): follow-on spec required
- Dangling-else (IncomingDocument.Table.al): tracked in `docs/dangling-else-fix.md`

### Which preproc_split_* Rules Use PREPROC_SPLIT_BEGIN

`PREPROC_SPLIT_BEGIN` replaces `kw('begin')` in rules where `begin` appears immediately before `$.preproc_endif`. Two existing rules qualify:

| Rule | Change |
|------|--------|
| `preproc_split_if_then_begin` | Replace `kw('begin')` with `$.preproc_split_begin` |
| `preproc_fragmented_else_tail` | Replace first `kw('begin')` with `$.preproc_split_begin` |

`kw('end')` in these rules remains anonymous — the matching `end` appears after a second `#if` re-open (depth > 0), but is NOT immediately before `#endif`, so `PREPROC_SPLIT_BEGIN` does not apply.

### Pattern 1 Root Cause

Current `preproc_split_if_then_begin` expects:
```
#if → if → cond → then → begin → #endif
```
with no statements before the `if` inside the `#if` block. Failing files have preamble statements:
```al
#if not CLEAN24
    NoSeriesMgt.RaiseObsoleteOnBeforeInitSeries(...);  // preamble
    if not IsHandled then begin                         // the split begin
#endif
```

### Fix

```javascript
preproc_split_if_then_begin: $ => prec(26, seq(
    $.preproc_if,
    repeat($._statement),           // NEW: allow preamble statements
    $.if_keyword,
    field('condition', $._expression),
    $.then_keyword,
    $.preproc_split_begin,          // replaces kw('begin')
    $.preproc_endif,
    repeat($._statement),
    $.preproc_if,
    repeat($._statement),           // NEW: allow preamble before end
    kw('end'), optional(';'),
    $.preproc_endif,
)),
```

Similarly update `preproc_fragmented_else_tail` to use `$.preproc_split_begin`.

---

## Implementation Order

1. **Stage 1a** — add scanner state struct + lifecycle functions + PREPROC_OPEN/PREPROC_CLOSE
2. **Stage 1b** — add BEGIN_KEYWORD/END_KEYWORD + update `code_block` + update `externals`
3. **Run tests** — `tree-sitter generate && tree-sitter test -u` (confirm no ERRORs before `-u`)
4. **Benchmark** — `bash benchmark.sh "after-stage1" 200`
5. **Stage 1c** — update highlights.scm, indents.scm, folds.scm
6. **Stage 2a** — add PREPROC_SPLIT_BEGIN to scanner + update `preproc_split_if_then_begin` + `preproc_fragmented_else_tail`
7. **Run tests** — confirm error count drops from 7
8. **Benchmark** — `bash benchmark.sh "after-stage2" 200`
9. **Validate** — `./validate-grammar.sh --full`

---

## Performance Expectations

- **Scanner state**: 1 byte serialize/deserialize — negligible
- **PREPROC_OPEN/CLOSE**: called once per `#if`/`#endif` — O(directives), not O(tokens)
- **BEGIN_KEYWORD/END_KEYWORD**: one depth compare per `begin`/`end` token — negligible
- **PREPROC_SPLIT_BEGIN**: lookahead only on `begin` at depth > 0 — rare in practice
- **Expected overall impact**: < 2% slower; no new grammar states from scanner-only changes

Baseline: `77ms/file` sequential (200 files), `7m41s` parallel (15,358 files, 7 errors).

---

## Risks

| Risk | Mitigation |
|------|------------|
| `preproc_if` restructure breaks existing tests | Run full test suite after Stage 1a; roll back if failures appear |
| GLR conflicts from `choice($.begin_keyword, kw('begin'))` | If conflicts appear, wrap in `prec`; scanner decline mechanism handles most cases |
| `PREPROC_SPLIT_BEGIN` lookahead over-matches | Lookahead is constrained to `#endif` only; `mark_end`/`return false` prevents false positives |
| Stage 2 Pattern 1 `repeat($._statement)` preamble causes new ambiguity | Use `repeat1` to require at least one preamble statement if zero-statement case is already covered |
| Depth underflow on malformed input | Guard `if (state->depth > 0) state->depth--` in PREPROC_CLOSE (already in pseudocode) |
