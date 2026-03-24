# Stateful Scanner: Named begin/end + Split Detection

**Date:** 2026-03-24
**Status:** Approved
**Goal:** Named `begin_keyword`/`end_keyword` nodes for query support (Stage 1); fix 7 remaining parse errors via `PREPROC_SPLIT_BEGIN` (Stage 2)

---

## Problem

`begin` and `end` are the only keywords among AL's 80+ named keyword nodes that remain anonymous. They cannot be named via grammar rules or `alias()` because any naming mechanism produces a different token type that breaks GLR backtracking in `preproc_split_*` rules.

The root cause: before the parser commits to `code_block` vs `preproc_split_*`, there exist combined parse states where both alternatives are active. If `begin` is a named token, the lexer emits it and collapses the GLR fork prematurely — killing the preproc branch.

The stateful scanner sidesteps this by using the preprocessor depth (computed from already-lexed input) to deterministically pick the correct token type at each position. The scanner's decision is based on its own serialized state, not on parser state.

---

## Approach: Stateful Scanner with Split Detection (Approach C)

### Scanner State

```c
typedef struct {
    uint8_t depth;  // current #if/#endif nesting depth
} ScannerState;
```

Serialized as 1 byte. Max nesting depth: 255 (more than sufficient for any real AL file).

### External Tokens (5 total)

| Token | Grammar role | Scanner behavior | Depth effect |
|-------|-------------|-----------------|--------------|
| `PREPROC_OPEN` | Replaces `#if`/`#ifdef`/`#ifndef` in `preproc_if` | Reads `#if`/`#ifdef`/`#ifndef`, depth++ | +1 |
| `PREPROC_CLOSE` | Replaces `#endif` in `preproc_endif` | Reads `#endif`, depth-- | -1 |
| `BEGIN_KEYWORD` | Used in `code_block` and non-split rules | Emitted when `depth == 0` | none |
| `END_KEYWORD` | Used in `code_block` and non-split rules | Emitted when `depth == 0` | none |
| `PREPROC_SPLIT_BEGIN` | Used in `preproc_split_*` rules | Emitted when `depth > 0` AND lookahead finds `#endif` after `begin` | none |

`#else` and `#elif` do **not** change depth — they are alternative branches within an existing `#if...#endif` block and are handled by the internal lexer as before.

### Scanner Logic

```c
// PREPROC_OPEN: #if / #ifdef / #ifndef — increment depth
if (valid_symbols[PREPROC_OPEN]) {
    if (read_preproc_open(lexer)) {  // reads '#if', '#ifdef', or '#ifndef'
        state->depth++;
        lexer->result_symbol = PREPROC_OPEN;
        return true;
    }
}

// PREPROC_CLOSE: #endif — decrement depth
if (valid_symbols[PREPROC_CLOSE]) {
    if (read_keyword(lexer, "#endif")) {
        if (state->depth > 0) state->depth--;
        lexer->result_symbol = PREPROC_CLOSE;
        return true;
    }
}

// BEGIN_KEYWORD: 'begin' at depth 0 only
if (valid_symbols[BEGIN_KEYWORD] && state->depth == 0) {
    if (read_keyword_ci(lexer, "begin")) {
        lexer->result_symbol = BEGIN_KEYWORD;
        return true;
    }
}

// END_KEYWORD: 'end' at depth 0 only
if (valid_symbols[END_KEYWORD] && state->depth == 0) {
    if (read_keyword_ci(lexer, "end")) {
        lexer->result_symbol = END_KEYWORD;
        return true;
    }
}

// PREPROC_SPLIT_BEGIN: 'begin' at depth > 0, immediately before #endif
if (valid_symbols[PREPROC_SPLIT_BEGIN] && state->depth > 0) {
    if (read_keyword_ci(lexer, "begin")) {
        lexer->mark_end(lexer);
        skip_whitespace(lexer);
        if (peek_preproc_endif(lexer)) {  // lookahead: '#endif' follows?
            lexer->result_symbol = PREPROC_SPLIT_BEGIN;
            return true;
        }
    }
}
```

### Why This Is Correct

- `begin`/`end` at `depth == 0` can **never** be part of a `preproc_split_*` rule. Split constructs, by definition, have `begin`/`end` inside `#if` blocks (depth > 0).
- `begin`/`end` at `depth > 0` can be either a normal `code_block` inside a `#if` block OR a preproc split. The `PREPROC_SPLIT_BEGIN` lookahead (checking for `#endif` immediately after) distinguishes them without ambiguity.
- The scanner's `depth` is computed from already-lexed input via the serialized state — it is deterministic at any given position and does not depend on parser state.
- At depth > 0, `BEGIN_KEYWORD`/`END_KEYWORD` are not emitted. The internal lexer handles `begin`/`end` as anonymous tokens, and existing `preproc_split_*` rules (which use `kw('begin')`/`kw('end')`) continue to work unchanged.

---

## Stage 1: Named begin/end Nodes

### Grammar Changes

**1. Add external tokens:**
```javascript
externals: ($) => [
    $.preproc_open,
    $.preproc_close,
    $.begin_keyword,
    $.end_keyword,
    $.preproc_split_begin,
    // ... existing tokens
],
```

**2. Update `preproc_if` to use `$.preproc_open`:**
```javascript
// Before:
preproc_if: $ => seq(token(prec(11, /#if\b/i)), ...)
// After:
preproc_if: $ => seq($.preproc_open, ...)
```

**3. Update `preproc_endif` to use `$.preproc_close`:**
```javascript
// Before:
preproc_endif: $ => seq(token(prec(11, /#endif\b/i)), ...)
// After:
preproc_endif: $ => seq($.preproc_close, ...)
```

**4. Update `code_block` to use named tokens with anonymous fallback:**
```javascript
code_block: $ => prec.right(seq(
    choice($.begin_keyword, kw('begin')),  // scanner picks: depth 0 → named, depth > 0 → anonymous
    repeat($._statement),
    choice($.end_keyword, kw('end')),
    optional(';'),
)),
```

**5. Expose as named keyword rules:**
```javascript
begin_keyword: $ => $.begin_keyword,  // or via externals directly
end_keyword:   $ => $.end_keyword,
```

### Parse Tree Result

```
// Normal code (depth 0):
(code_block
  (begin_keyword)     ← named, queryable
  ...statements...
  (end_keyword))      ← named, queryable

// Inside #if block (depth > 0):
(code_block
  "begin"             ← anonymous (preproc_split rules work)
  ...statements...
  "end")              ← anonymous
```

### Query Support (after Stage 1)

```scheme
; highlights.scm — now works for begin/end
(begin_keyword) @keyword
(end_keyword) @keyword

; indents.scm
(code_block (begin_keyword) @indent.begin)
(code_block (end_keyword) @indent.end)
```

---

## Stage 2: Fix 7 Remaining Parse Errors

### Context

The 7 errors fall into 3 patterns. Stage 2 addresses the 6 begin/end preprocessor errors using `PREPROC_SPLIT_BEGIN`. The 1 dangling-else error (IncomingDocument.Table.al) is tracked separately in `docs/dangling-else-fix.md`.

### Pattern 1: Preamble Before Split Begin (3 files)

Current `preproc_split_if_then_begin` expects `#if → if → cond → then → begin → #endif` with no statements before the `if`. Failing files have statements inside the `#if` before the `if ... then begin`.

**Fix:** Allow preamble statements before the `if`, use `$.preproc_split_begin`:
```javascript
preproc_split_if_then_begin: $ => prec(26, seq(
    $.preproc_if,
    repeat($._statement),         // allow preamble
    $.if_keyword,
    field('condition', $._expression),
    $.then_keyword,
    $.preproc_split_begin,        // scanner-detected split begin
    $.preproc_endif,
    repeat($._statement),
    $.preproc_if,
    repeat($._statement),         // allow preamble before end
    kw('end'), optional(';'),
    $.preproc_endif,
)),
```

### Pattern 2: Procedure Begin Variants in #if/#else (3 files)

Procedure body has `var` section + `begin` in one branch, plain `begin` in the other. The existing `preproc_split_procedure` may need extension to handle begin variants. Exact grammar rule changes to be determined during implementation after analyzing the 3 specific files.

---

## Implementation Order

1. **Stage 1** — scanner state + PREPROC_OPEN/PREPROC_CLOSE + BEGIN_KEYWORD/END_KEYWORD
2. **Benchmark** — run `benchmark.sh "after-stage1" 200`, compare to baseline
3. **Stage 1 queries** — update highlights.scm, indents.scm, folds.scm
4. **Stage 2** — add PREPROC_SPLIT_BEGIN + new/updated preproc_split rules
5. **Benchmark** — run `benchmark.sh "after-stage2" 200`, compare

---

## Performance Expectations

- **Scanner state**: 1 byte serialize/deserialize — negligible
- **PREPROC_OPEN/CLOSE**: called once per `#if`/`#endif` directive — O(n) in number of preprocessor directives, not per-token
- **BEGIN_KEYWORD/END_KEYWORD**: one extra compare (`depth == 0`) per `begin`/`end` token — negligible
- **PREPROC_SPLIT_BEGIN**: lookahead on `begin` tokens at depth > 0 — only called in preprocessor-heavy code, very rare in practice
- **Expected overall impact**: < 2% slower; parser.c size increase minimal (no new grammar states from scanner-only changes)

Baseline: 77ms/file sequential (200 files), 7m41s parallel (15,358 files, 7 errors).

---

## Risks

| Risk | Mitigation |
|------|------------|
| `preproc_if` restructure breaks existing tests | Run full test suite after each change; roll back if > 0 new failures |
| GLR conflicts from `choice($.begin_keyword, kw('begin'))` | If conflicts appear, use `prec` to resolve; scanner priority handles most cases |
| `PREPROC_SPLIT_BEGIN` lookahead too aggressive | Narrow the lookahead to only match `#endif`/`#else` immediately after `begin` + whitespace |
| Stage 2 Pattern 2 requires major restructuring | Treat as separate task; Stage 1 + Pattern 1 fix is already a win |
