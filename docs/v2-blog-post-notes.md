# V2 Grammar Rewrite — Blog Post Notes

Raw data and narrative beats from the V2 rewrite session (2026-03-20).

## The Trigger

User's friend said "you're missing queries." Investigation revealed that tree-sitter query files (highlights.scm, etc.) couldn't highlight most AL keywords because `kw()` (regex tokens) are invisible in the parse tree.

## The Journey

### Act 1: Adding Queries to V1

- Created 5 query files: highlights.scm, locals.scm, tags.scm, indents.scm (new), folds.scm (new)
- Discovered keywords created with `kw()` are invisible — can't match `procedure`, `if`, `begin` etc. in queries

### Act 2: Exposing Keywords in V1

- Investigated how other parsers handle this (Pascal, C#, Rust, Ruby — none had our exact problem)
- Added 83 named keyword rules (Pascal pattern: `if_keyword: $ => kw('if')`)
- Discovered `begin`/`end` can NEVER be named nodes — not as named rules, not with alias (named OR anonymous). Any naming mechanism changes the token type and breaks GLR backtracking in preprocessor-split constructs
- Successfully exposed 80 keywords (all except begin/end) with 0 regressions
- parser.c grew from 95 MB to 106 MB — exceeding GitHub's 100 MB limit

### Act 3: The Property Problem

- Investigated why parser.c was so large: **2,249 symbols** (C# has 524)
- Root cause: **291 individual property rules** (`caption_property`, `editable_property`, etc.)
- Each property validates value types at parse time — no other tree-sitter grammar does this
- Attempted to consolidate into a generic `property` rule — **FAILED**:
  - LR(1) conflict: `identifier =` (property) vs `identifier :` (variable) — parser can't distinguish with 1-token lookahead
  - Adding generic_property to all lists caused state explosion (29K→38K+ states)
  - The grammar was at tree-sitter's practical limits

### Act 4: V2 — Ground-Up Rewrite

- Decision: build from scratch in `v2/` subdirectory
- Key architectural insight: use external scanner to emit `PROPERTY_NAME` token when identifier is followed by `=` (not `:=`)
- Built incrementally in 8 phases, validating against 15,358 production files after each

## Phase-by-Phase Progress

| Phase | What | Success Rate | parser.c | Symbols | Time* |
|-------|------|-------------|----------|---------|-------|
| 1 | Scaffold + 19 object types | ~0% | 203 KB | 71 | — |
| 2 | Generic property + complex properties | ~5% | 289 KB | 135 | — |
| 3 | Fields, keys, sections, types | ~10% | 917 KB | 317 | — |
| 4 | Procedures, triggers, variables | ~15% | 1.2 MB | 344 | — |
| 5 | Statements & expressions | 33.4% (5,122 files) | 2.4 MB | 490 | — |
| 6 | Preprocessor, extensions, views, dotnet | 87.1% (13,377 files) | 4.6 MB | 594 | — |
| 7 | Edge cases, property values | 97.9% (15,039 files) | 5.4 MB | 636 | — |
| 8a | More edge cases, preproc splits | 99.67% (15,308 files) | 7.3 MB | 719 | — |
| 8b | Fragmented if-else, split constructs | 99.95% (15,351 files) | 9.4 MB | 724 | — |
| Keywords | 80 named keyword rules | 99.95% (15,351 files) | 10.3 MB | ~750 | — |

*Times not recorded — all phases completed in a single session.

## Final Comparison

| Metric | V1 | V2 | Improvement |
|--------|-----|-----|-------------|
| parser.c size | 106 MB | 10.6 MB | **10x smaller** |
| GitHub pushable | No (>100 MB limit) | Yes | — |
| Production errors | 14 | 7 | **2x fewer errors** |
| Success rate | 99.91% | 99.95% | Better |
| SYMBOL_COUNT | 2,249 | 724 | **3.1x fewer** |
| STATE_COUNT | 29,126 | 5,179 | **5.6x fewer** |
| grammar.js lines | ~8,500 | ~3,000 | **2.8x smaller** |
| Property rules | 291 | 1 generic + ~20 complex | **93% reduction** |
| Preprocessor rules | 63 | ~15 | **76% reduction** |
| Named keyword nodes | 80 | 80 | Same |
| Query files | 5 | 5 | Same |
| Tests | 1,225 | 1,404 | 15% more |

## Key Architectural Differences

### 1. Scanner-Based Property Disambiguation (biggest win)

V1: 291 individual property rules, each with a unique keyword token (`kw('Caption')`, `kw('Editable')`, etc.). This was needed because a generic `identifier = value ;` property rule conflicts with `identifier : type ;` variable declarations — the LR(1) parser can't distinguish them with 1-token lookahead.

V2: External scanner emits a `PROPERTY_NAME` token when it sees `identifier` followed by `=` (not `:=`). One generic property rule handles everything. The scanner does a simple 1-character lookahead past the identifier — trivial C code, massive architectural impact.

### 2. Parse Structure, Don't Validate

V1 validated property types at parse time: `Caption` only accepts strings, `Editable` only accepts booleans. No other tree-sitter grammar does this. It's the compiler/linter's job.

V2 accepts any `Name = Expression ;` as a property. Invalid values parse fine — semantic validation happens downstream.

### 3. Generic Preprocessor

V1: 63 specialized preprocessor rules (`preproc_conditional_page_properties`, `preproc_conditional_actions`, etc.) — each one a copy of the content rule wrapped in `#if/#endif`.

V2: 1 generic `preproc_conditional` rule + ~12 dedicated rules for genuinely complex split constructs (procedure headers split across branches, begin/end across branches, etc.).

### 4. begin/end Cannot Be Named

This is a fundamental tree-sitter limitation, not a grammar design issue. When `begin`/`end` are named nodes (by ANY mechanism — named rules, named alias, anonymous alias), the GLR parser's error recovery inserts MISSING tokens instead of backtracking to try preprocessor-split alternatives. The token type change is what triggers different error recovery behavior.

## Remaining 7 Errors

All 7 files have cross-branch `begin`/`end` preprocessor patterns where `begin` is inside one `#if` branch and the matching `end` is elsewhere. Same files fail in V1 (which has 7 additional failures V2 handles). Would require major scanner work — scanning ahead through entire `#if` blocks to match begin/end pairs.

## What Made It Possible

- **Production file corpus**: 15,358 real AL files from BC.History as the validation gate — far more comprehensive than handcrafted tests
- **Incremental validation**: Parse corpus after each phase, see success rate climb
- **V1 as reference**: Every AL construct had a working implementation to study
- **Scanner pattern**: The PROPERTY_NAME token is a simple, elegant solution to the property/variable disambiguation that stumped V1 consolidation attempts
- **Aggressive simplification**: Dropping per-property validation, flattening preprocessor rules, eliminating property category hierarchies — each decision removed hundreds of grammar rules

## Downstream Impact

V2 changes parse tree structure. Two dependent repos need updates:
- `al-call-hierarchy` (Rust) — 10 issues, 5 breaking (field renames, node removals, query restructuring)
- `al-perf` (TypeScript) — 14 issues, all in `indexer.ts` (property nodes, formula nodes, trigger nodes)

Migration guides written for each repo.
