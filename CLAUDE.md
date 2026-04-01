# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this tree-sitter parser for the AL (Application Language) programming language used in Microsoft Dynamics 365 Business Central.

**Current Status**: 100% production file success rate (15,358/15,358 files), 1404 tests passing, 0 errors

## Git Commit Guidelines

**Always include error count in commit messages** to detect regressions:
```
Fix XYZ pattern

[BC.History: 7 errors, 99.95% success]
```

Run full parse before committing: `./parse-al-parallel.sh ./BC.History/ .`

## Quick Reference

**Essential Commands:**
```bash
# Validation (run before completing any task)
./validate-grammar.sh        # Quick: generation, tests, orphan/duplicate detection
./validate-grammar.sh --full # Full: includes production AL file parsing

# Standard development cycle
tree-sitter generate         # Generate parser from grammar.js
tree-sitter test            # Run test suite
tree-sitter test -u         # Update test expectations (only if no ERRORs)
tree-sitter parse file.al -d > debug.log 2>&1  # Debug specific files
python parse_bug_finder.py file.al debug.log   # Analyze parsing bugs
```

**Common Test Options:**
- `-i "pattern"` - Include tests matching pattern
- `-e "pattern"` - Exclude tests matching pattern
- `--file-name "test.txt"` - Run specific test file
- `-d` - Show debug log
- `-D` - Generate debug graphs (log.html)

## Architecture

**Core Files:**
- `grammar.js` - Main grammar definition (~3,400 lines). Never edit `src/parser.c` (auto-generated)
- `src/scanner.c` - External scanner for property disambiguation and preprocessor patterns
- `test/corpus/` - Test suite with AL code and expected parse trees (1,404 tests)
- `queries/` - 5 query files (highlights, locals, tags, indents, folds)

**Key Design Principles (V2 architecture):**
- **Parse structure, don't validate** — Accept any `Name = Value ;` as a property. Semantic validation belongs in linters/LSP servers, not the parser
- **Scanner-based property disambiguation** — The `PROPERTY_NAME` scanner token distinguishes `identifier =` (property) from `identifier :` (variable) via 1-char lookahead
- **Generic property rule** — ONE `property` rule handles all simple properties (vs V1's 291 individual rules)
- **Generic preprocessor** — ONE `preproc_conditional` rule + ~12 dedicated split-construct rules (vs V1's 63)
- **Named keyword nodes** — 82 keywords exposed as named nodes for query matching (including `begin_keyword`, `end_keyword`)
- **Stateful scanner** — 1-byte depth counter tracks `#if`/`#endif` nesting; `begin`/`end` named at depth 0, anonymous at depth > 0

**Scanner Tokens:**

| Token | Purpose |
|-------|---------|
| `PROPERTY_NAME` | `identifier` followed by `=` (not `:=`) — property/variable disambiguation |
| `CONTINUE_AS_IDENTIFIER` | `continue` followed by `:=` — used as variable name |
| `PREPROC_OPEN` | `#if` — increments depth counter |
| `PREPROC_CLOSE` | `#endif` — decrements depth counter |
| `BEGIN_KEYWORD` | `begin` at depth 0 — named node for queries |
| `END_KEYWORD` | `end` at depth 0 — named node for queries |
| `PREPROC_SPLIT_BEGIN` | `begin` at depth > 0, immediately before `#endif` — split detection |
| `PREPROC_SPLIT_END` | `end` at depth > 0, followed by `;` then `#else`/`#endif` — split detection |

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

## Keyword Architecture

80 keywords are named rules for query matching:

```javascript
if_keyword: $ => kw('if'),
table_keyword: $ => kw('table'),
procedure_keyword: $ => kw('procedure'),
```

**begin/end are named via stateful scanner** — `begin_keyword` and `end_keyword` are emitted at depth 0 (outside `#if` blocks). At depth > 0, the scanner declines and anonymous `kw('begin')`/`kw('end')` tokens handle preprocessor-split contexts. Direct naming via grammar rules or `alias()` still breaks GLR backtracking — the stateful scanner is the correct approach.

**Named keyword node structure** — Named keyword rules (e.g., `exit_keyword`) wrap anonymous string children (`"exit"`). When tree-walking into children, you hit the anonymous string — this is expected tree-sitter behavior, not a grammar bug. The named node is the parent; the literal text is an anonymous child.

**CamelCase keywords** use explicit case alternatives:
```javascript
controladdin_keyword: $ => prec(10, choice('controladdin', 'CONTROLADDIN', 'Controladdin', 'ControlAddIn')),
```

## Attribute Handling

Attributes are first-class statements (Rust/C# pattern) — siblings to declarations, not nested.

```al
[Scope('OnPrem')]
[IntegrationEvent(false, false)]
procedure MyEvent() begin end;
```

Parse tree: `(attribute_item ...) (procedure ...)`  — separate nodes at the same level.

## Preprocessor Handling

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
| **Keyword as identifier** | Variable name conflicts | Add to `keyword_as_identifier` choice list |

## Parser Metrics

**Note:** These metrics are approximate and may drift as the grammar evolves. Verify with `wc -c src/parser.c` and `grep -E 'SYMBOL_COUNT|STATE_COUNT' src/parser.c` if precision matters.

| Metric | Value |
|--------|-------|
| parser.c size | 23.5 MB |
| SYMBOL_COUNT | ~762 |
| STATE_COUNT | ~11,705 |
| grammar.js lines | ~3,400 |
| Tests | 1,404 |
| Production success | 100% (0 errors) |
| Named keywords | 82 |
| Query files | 5 (highlights, locals, tags, indents, folds) |

## Documentation Resources

**Available via MCP:**
- **business-central** — AL Language syntax, objects, properties
- **tree-sitter** — Grammar development guide, API reference

**Project docs:**
- `docs/v2-blog-post-notes.md` — V2 rewrite narrative and data
- `docs/superpowers/specs/` — Design specs for major changes

## Philosophy: No Known Limitations

**Never give up on a failing pattern:**
- Don't disable tests or mark issues as "known limitations"
- Research how other parsers handle similar constructs in `other-languages/`
- Use `error-research` agent for systematic failure analysis
- Every "impossible" pattern has been solved somewhere — find it and adapt it
