# Design: V2 Grammar — Ground-Up Rewrite

**Date:** 2026-03-20
**Status:** Approved

## Problem

The v1 AL grammar has 2,249 symbols, 29,126 parser states, and a 106 MB parser.c — exceeding GitHub's 100 MB limit. The bloat comes from 291 per-property validation rules, 63 specialized preprocessor rules, and ~80 exclusive value-type rules. Attempts to consolidate properties within v1 failed due to fundamental LR(1) disambiguation conflicts between `identifier =` (property) and `identifier :` (variable).

## Solution

Build a v2 grammar from scratch in `v2/` subdirectory, applying architectural lessons from v1. Target: same or better production success rate (99.91%+), parser.c under 100 MB.

## Project Structure

```
tree-sitter-al/
├── v2/
│   ├── grammar.js          # New grammar (~3000-4000 lines)
│   ├── src/scanner.c        # New scanner with PROPERTY_NAME token
│   ├── src/                 # Generated files
│   ├── test/corpus/          # Copied from v1 (source only)
│   ├── queries/              # New query files
│   └── validate.sh           # BC.History comparison script
├── grammar.js                # v1 (untouched until v2 is ready)
├── BC.History/               # Shared production files (15,358 files)
```

## Core Principle

**Parse structure, don't validate.** Accept syntactically plausible code. Leave semantic validation (property types, valid property names per context, etc.) to linters/LSP servers. This is how every other tree-sitter grammar works.

## Scanner Architecture

The v2 scanner handles disambiguation the grammar can't:

| Token | Purpose | Lookahead |
|-------|---------|-----------|
| `PROPERTY_NAME` | **NEW.** `identifier` followed by `=` (not `:=`) | Skip whitespace after identifier, check next char is `=` and char after is not `=` |
| `FOR_TO_KEYWORD` | `to` with word boundary | Reuse from v1 |
| `FOR_DOWNTO_KEYWORD` | `downto` with word boundary | Reuse from v1 |
| `CONTINUE_AS_IDENTIFIER` | `continue` followed by `:=` | Reuse from v1 |
| `PREPROC_SPLIT_MARKER` | Split constructs across `#if` | Reuse from v1 |
| `PREPROC_VAR_CONTINUATION` | Var section continues through `#if` | Reuse from v1 |
| `PREPROC_VAR_TERMINATOR` | Var section ends at `#if` | Reuse from v1 |

The `PROPERTY_NAME` token eliminates the need for 291 per-property rules. When the parser state allows both properties and variables, the scanner checks what follows the identifier to disambiguate.

**Critical scoping constraint:** The grammar MUST be structured so `PROPERTY_NAME` is never in `valid_symbols` inside `var_section` or statement contexts. The scanner only emits `PROPERTY_NAME` when `valid_symbols[PROPERTY_NAME]` is true AND the lookahead shows `=` (not `:=`). This means properties and variables exist in different parser states — which is naturally the case since properties appear in object/section bodies and variables appear in `var_section`.

Scanner is fully redesignable — any additional tokens needed for v2-specific patterns can be added.

## Grammar Architecture

### Rule Count Targets

| Category | V1 | V2 Target |
|----------|-----|-----------|
| Properties | 291 | 1 generic + ~20 complex |
| Preprocessor | 63 | ~15 (1 generic + ~12-15 split-construct rules) |
| Keywords | 83 named | 83 named |
| Object declarations | ~25 | ~25 |
| Statements/expressions | ~50 | ~50 |
| Sections | ~60 | ~30 |
| Value/enum rules | ~80 | ~5 |
| **Total rules** | **~800** | **~300-350** |
| **SYMBOL_COUNT** | **2,249** | **~400-500** |

### Generic Property Rule

```javascript
property: $ => seq(
  field('name', $.property_name),   // PROPERTY_NAME scanner token
  '=',
  field('value', $._expression),
  ';'
),
```

No per-property rules. No property category lists. `property` is valid in any object body. Invalid properties are a linter's problem.

### Complex Properties (~20 rules)

Properties with syntax beyond `Name = Expression ;`:

**Formula:** `calc_formula_property`, `table_relation_property`

**Permissions:** `permissions_property`, `access_by_permission_property`

**Links/Filters:** `data_item_link_property`, `run_page_link_property`, `sub_page_link_property`, `data_item_table_filter_property`, `column_filter_property`

**Views:** `source_table_view_property` (other view properties reuse the same value type)

**Generic templates (one rule each, replacing many v1 rules):**
- `ml_property` — ALL multilingual properties: `Name = ENU='English', DEU='German'` (replaces 10 v1 rules)
- `caption_property` — Properties with Locked/Comment sub-fields (replaces ~6 v1 rules)
- `list_property` — Comma-separated identifier lists (replaces ~15 v1 rules)

**Other:** `decimal_places_property`, `order_by_property`, `implementation_property` (has preprocessor directives embedded within value list), `option_members_property`, `option_caption_property`

### Preprocessor Strategy

**Category A — Context-typed conditionals (genericized):** V1 has ~30 rules like `preproc_conditional_page_properties`, `preproc_conditional_actions`, etc. that differ only in their content type. V2 replaces all with ONE generic rule:

```javascript
preproc_conditional: $ => seq(
  $.preproc_if,
  repeat($._any_content),
  repeat(seq($.preproc_elif, repeat($._any_content))),
  optional(seq($.preproc_else, repeat($._any_content))),
  $.preproc_endif,
),
```

`_any_content` is a context-appropriate union. May need 2-3 scoped variants (statement-level vs object-body-level) to limit ambiguity. Design exact scope during implementation.

**Category B — Structural split constructs (~12-15 dedicated rules):** These handle cases where a single syntactic construct is fragmented across `#if`/`#endif` boundaries. Each is a unique pattern from real BC.History files and CANNOT be genericized:

- `preproc_split_procedure` — procedure header in `#if`/`#else` branches
- `preproc_conditional_procedure` — return type split across branches
- `preproc_procedure_body_split` — `begin` in `#if`, second `begin` in `#else`
- `preproc_split_if_else` — `else` keyword inside `#if`, body outside
- `preproc_split_if` — if condition inside `#if`, body outside
- `preproc_split_if_then_begin` — `begin` inside `#if`, `end` inside second `#if`
- `preproc_fragmented_if_else` — end-else-begin fragmented across two `#if` blocks
- `preproc_wrapped_fragmented_if_else` — similar with leading `#if`
- `preproc_variant_condition_if` — shared body with different conditions per branch
- `preproc_split_codeunit_declaration` — codeunit implements clause in `#if`/`#else`
- `preproc_split_enum_declaration` — enum declaration split
- `preproc_split_field_section` — field section split in page layouts

These are ported from v1 with minimal changes.

### Keyword Architecture

Named keyword rules from day one using `kw()` (regex, truly case-insensitive):

```javascript
if_keyword: $ => kw('if'),
table_keyword: $ => kw('table'),
procedure_keyword: $ => kw('procedure'),
// ... all 83 keywords
```

`begin`/`end` stay as anonymous inline tokens. The split-begin/end patterns ARE handled by dedicated split-construct rules (Category B above), but the keywords themselves cannot be exposed as named nodes because any naming mechanism (named rules, alias) changes the token type and breaks GLR backtracking in those split contexts.

Keywords with CamelCase variants (ControlAddIn, PermissionSet, XMLport) use explicit case alternatives like v1.

### No Property Categories

V1 has 20+ nested property category lists controlling which properties appear in which context. V2 drops this entirely — `$.property` is valid in any object body. This alone eliminates ~20 hidden rules and massive choice-list nesting.

### Parse Tree Structure

V2 produces a new tree structure. Key differences from v1:

```
; V1 — individual property nodes
(property
  (editable_property
    value: (boolean)))

; V2 — generic property with name field
(property
  name: (property_name)
  value: (boolean))

; V1 — preproc_conditional_procedures
(preproc_conditional_procedures
  (preproc_if ...)
  (procedure ...)
  (preproc_endif ...))

; V2 — generic preproc_conditional
(preproc_conditional
  (preproc_if ...)
  (procedure ...)
  (preproc_endif ...))
```

All queries need rewriting for v2. This is accepted — the v1 queries are already written and can be adapted.

## Validation & Migration

### Validation Script

`v2/validate.sh` parses BC.History with both v1 and v2, comparing error counts.

### Incremental Development

Build by construct, validate after each:

1. Object shells — all object types with empty bodies
2. Properties — generic + complex
3. Fields, keys, fieldgroups
4. Procedures, triggers, var sections
5. Statements & expressions
6. Layout, actions, sections
7. Preprocessor — generic + split constructs
8. Edge cases from BC.History

### Test Strategy

- Copy v1 test source code (AL above `---` line) into `v2/test/corpus/`
- Run `tree-sitter test -u` to generate v2 expectations as constructs are built
- BC.History (15,358 files) is the real validation gate

### V2 Replaces V1 When

- 14 or fewer errors on BC.History (matching or beating v1)
- parser.c under 100 MB
- All query files working
- Then: move v2 files to root, delete v1, update CLAUDE.md, push

## Estimated Impact

| Metric | V1 | V2 (estimated) |
|--------|-----|----------------|
| grammar.js lines | 8,500 | 3,000-4,000 |
| SYMBOL_COUNT | 2,249 | 400-500 |
| STATE_COUNT | 29,126 | 8,000-12,000 |
| parser.c size | 106 MB | 15-30 MB |
| Production success | 99.91% (14 errors) | 99.91%+ |
| Test count | 1,225 | ~1,225 (same source, new expectations) |

## What Stays the Same

- Scanner architecture patterns (reuse v1's proven lookahead techniques)
- Named keyword approach (83 keywords, all except begin/end)
- Attribute handling (Rust-style, attributes as siblings)
- Object declaration structure (table, page, codeunit, etc.)
- The test corpus and production file validation approach
