# Design: Expose Keywords as Named Nodes for Query Matching

**Date:** 2026-03-20
**Status:** Approved

## Problem

The AL grammar uses `kw()` (case-insensitive regex tokens) for all keywords. These produce invisible anonymous nodes in the parse tree that cannot be matched in tree-sitter queries. This prevents syntax highlighting of keywords like `begin`, `end`, `if`, `procedure`, `table`, etc.

## Solution

Convert all `kw()` keyword calls to named rules with `_keyword` suffix, following the Pascal grammar pattern. Each keyword becomes a visible named node in the parse tree, matchable in queries.

## Scope

~80 keywords across 3 tiers:

### Tier 1 — Control Flow & Declarations (22)

`begin`, `end`, `if`, `then`, `else`, `case`, `of`, `while`, `do`, `for`, `foreach`, `in`, `repeat`, `until`, `var`, `procedure`, `trigger`, `exit`, `break`, `continue`, `with`, `asserterror`

### Tier 2 — Object Types & Structure (25)

`table`, `tableextension`, `page`, `pageextension`, `codeunit`, `report`, `reportextension`, `query`, `xmlport`, `enum`, `enumextension`, `interface`, `controladdin`, `dotnet`, `profile`, `profileextension`, `permissionset`, `permissionsetextension`, `entitlement`, `pagecustomization`, `namespace`, `using`, `implements`, `extends`, `customizes`

### Tier 3 — Sections & Modifiers (33)

`fields`, `keys`, `key`, `fieldgroups`, `fieldgroup`, `actions`, `layout`, `area`, `group`, `repeater`, `cuegroup`, `fixed`, `grid`, `part`, `systempart`, `usercontrol`, `chartpart`, `dataset`, `elements`, `dataitem`, `column`, `filter`, `labels`, `rendering`, `requestpage`, `schema`, `views`, `view`, `local`, `internal`, `protected`, `event`, `temporary`

**Total: 80 keywords**

## Mechanical Change Pattern

### 1. Add Named Rule

```javascript
// Use kw() for most keywords
end_keyword: $ => kw('end'),

// Use kw_literal() for keywords that currently use it (word boundary protection)
// Currently only 'begin' uses kw_literal — preserves the word boundary
// enforcement that prevents 'BeginTotalAccNo' matching as 'begin'
begin_keyword: $ => kw_literal('begin'),
```

**Rule:** If the keyword currently uses `kw_literal()`, the named rule must also use `kw_literal()`. If it uses `kw()`, use `kw()`.

### 2. Precedence Handling

Many keywords carry precedence values: `kw('if', 10)`, `kw('begin', 10)`, etc.

**Convention:** Precedence stays at the **call site**, not in the named rule definition. The named rule is a bare token; precedence is applied where context demands it.

```javascript
// Named rule — no precedence
if_keyword: $ => kw('if'),
begin_keyword: $ => kw_literal('begin'),

// Call site — precedence applied in context
if_statement: $ => prec.right(seq(
  prec(10, $.if_keyword),    // precedence stays here
  field('condition', $._expression),
  prec(10, $.then_keyword),
  ...
)),

code_block: $ => prec.right(1, seq(
  prec(10, $.begin_keyword),  // precedence stays here
  ...
)),
```

This keeps named rules simple and reusable, while preserving the existing precedence behavior at each use site.

### 3. Replace Inline References

```javascript
// Before
code_block: $ => seq(kw_literal('begin', 10), repeat($._statement), kw('end'), ';'),

// After
code_block: $ => seq(prec(10, $.begin_keyword), repeat($._statement), $.end_keyword, ';'),
```

### Exclusions (Do NOT Convert)

- **`alias(kw('end'), $.identifier)`** — intentionally treats keyword as identifier
- **`'div'`/`'DIV'`/`'Div'` operator variants** — already matchable as anonymous string literals
- **`kw_with_eq()` calls** — property-context-specific, already matchable
- **`kw_with_coloncolon()` calls** — `kw_with_coloncolon('table')` etc. in `object_type_qualified_reference` stay as-is; these include `::` in the token and are a different token from `table_keyword`
- **Keywords inside `_contextual_keyword_aliases`** or similar identifier aliasing patterns

### Special Cases

#### `_enum_keyword` Rule

The `_enum_keyword` rule (line ~7561) lists many keywords as valid enum member values (e.g., `kw('If')`, `kw('Begin')`, etc.). These must be updated to use the named rules:

```javascript
// Before
_enum_keyword: $ => choice(kw('If'), kw('Then'), kw('Begin'), ...),

// After
_enum_keyword: $ => choice($.if_keyword, $.then_keyword, $.begin_keyword, ...),
```

#### `continue` Keyword

`continue` has a dedicated external scanner token (`CONTINUE_AS_IDENTIFIER`, index 16) that looks ahead for `:=` to determine if `continue` is a statement or a variable name. The `continue_keyword` named rule covers only the statement-keyword usage. The `continue_as_identifier` scanner token and its `alias()` to `$.identifier` remain unchanged.

#### `procedure_modifier` and `modifier` Rules

`procedure_modifier` wraps `choice(kw('local'), kw('internal'), kw('protected'))`. After conversion, this becomes `choice($.local_keyword, $.internal_keyword, $.protected_keyword)`. The `procedure_modifier` named node is preserved as a wrapper — queries can match either the group (`procedure_modifier`) or individual keywords (`local_keyword`).

Similarly, `modifier: $ => kw('var')` becomes `modifier: $ => $.var_keyword`.

#### Object Type Keywords with `kw_with_coloncolon`

Six Tier 2 keywords (`table`, `report`, `page`, `codeunit`, `xmlport`, `query`) also appear as `kw_with_coloncolon(...)` in `object_type_qualified_reference`. These `kw_with_coloncolon` calls are **separate tokens** (they include `::`) and are NOT converted. The named rules (e.g., `table_keyword`) cover only standalone keyword usage.

## Parse Tree Impact

Before:
```
(code_block
  (if_statement
    condition: (boolean)
    then_branch: (exit_statement)))
```

After:
```
(code_block
  (begin_keyword)
  (if_statement
    (if_keyword)
    condition: (boolean)
    (then_keyword)
    then_branch: (exit_statement
      (exit_keyword)))
  (end_keyword))
```

## Query File Updates

After grammar change, update `queries/highlights.scm`:

```scheme
; Control flow
[
  (if_keyword) (then_keyword) (else_keyword)
  (case_keyword) (of_keyword)
  (while_keyword) (do_keyword)
  (for_keyword) (foreach_keyword) (in_keyword)
  (repeat_keyword) (until_keyword)
  (exit_keyword) (break_keyword) (continue_keyword)
  (with_keyword) (asserterror_keyword)
] @keyword.control

; Block delimiters
[(begin_keyword) (end_keyword)] @keyword

; Declarations
[(procedure_keyword) (trigger_keyword) (var_keyword) (event_keyword)] @keyword.declaration

; Object types
[
  (table_keyword) (page_keyword) (codeunit_keyword)
  (report_keyword) (query_keyword) (xmlport_keyword)
  (enum_keyword) (interface_keyword) (controladdin_keyword)
  (dotnet_keyword) (profile_keyword) (permissionset_keyword)
  (entitlement_keyword) (pagecustomization_keyword)
  ; extension variants...
] @keyword.type

; Structural
[
  (namespace_keyword) (using_keyword)
  (extends_keyword) (implements_keyword) (customizes_keyword)
] @keyword.import

; Sections
[
  (fields_keyword) (keys_keyword) (key_keyword)
  (actions_keyword) (layout_keyword) (area_keyword)
  (group_keyword) (repeater_keyword) (dataset_keyword)
  (elements_keyword) (views_keyword) (rendering_keyword)
  ; ... etc
] @keyword.structure

; Access modifiers (already partially covered by procedure_modifier)
[(local_keyword) (internal_keyword) (protected_keyword)] @keyword.modifier
```

Also update `indents.scm` and `folds.scm` where keyword nodes can improve precision.

## Naming Convention

`<keyword>_keyword` suffix, matching existing AL patterns (`tabledata_keyword`, `zeroorone_keyword`).

One named rule per keyword. Context-specific highlighting is handled by parent node matching in queries, not by having multiple rules for the same keyword.

## Validation Sequence

1. `tree-sitter generate` — must succeed
2. Spot-check a sample of tests for ERROR/MISSING nodes before bulk update
3. `tree-sitter test -u` — update all test expectations (only after confirming no ERROR/MISSING)
4. `tree-sitter test` — all tests pass with updated expectations
5. Full production parse — maintain 99.91% rate (15,344/15,358 files)
6. Record new state count and compare to baseline (~29,345 states)
7. Update all query files to use new keyword nodes

## Risk & Mitigation

**Parser state explosion:** Adding ~81 named rules will increase the state table. Current baseline is ~29,345 states. Mitigation triggers:
- If state count exceeds 2x baseline (~59,000): reduce scope by dropping tier 3 section keywords
- If full-corpus parse time increases by more than 50%: add low-impact keywords to `inline: $ => [...]`
- If `tree-sitter generate` fails: reduce scope incrementally

**Precedence regressions:** Moving precedence from `kw('x', 10)` to `prec(10, $.x_keyword)` at call sites must be done carefully. If tests show ERROR/MISSING nodes after generation, compare the precedence values at each use site against the original.

**Rollback:** Single commit, single `git revert`.

**Not a risk:** Case-insensitivity is preserved. Named rules wrap `kw()` which still uses `(?i)` regex matching.

## Prior Art

- **Pascal grammar:** Individual named keyword nodes (`kBegin`, `kEnd`, `kIf`) — ~80 keywords, same pattern
- **AL grammar (existing):** `zeroorone_keyword`, `zeroormany_keyword`, `one_keyword`, `many_keyword` — standalone named keyword rules that prove the pattern works. (`tabledata_keyword` exists but is created via `alias()`, not a standalone rule.)
