# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this tree-sitter parser for the AL (Application Language) programming language used in Microsoft Dynamics 365 Business Central.

**Current Status**: 100% production file success rate (15,358/15,358 files), 1451 tests passing, 0 errors

## Git Commit Guidelines

**Always include error count in commit messages** to detect regressions:
```
Fix XYZ pattern

[BC.History: 7 errors, 99.95% success]
```

Run full parse before committing: `./parse-al-parallel.sh ./BC.History/ .`

**Commit all generated files together** — `tree-sitter generate` writes `src/parser.c`, `src/grammar.json`, and `src/node-types.json`; all three are tracked. Stage them as a set or `grammar.json` silently drifts.

## Quick Reference

**Essential Commands:**
```bash
# Validation (run before completing any task)
./validate-grammar.sh        # Quick: generation, tests, orphan/duplicate detection
./validate-grammar.sh --full # Full: includes production AL file parsing

# Zero-behavior-change gate for grammar refactors (byte-identical parse trees)
./tools/tree-harness.sh snapshot ./BC.History .snapshots/bc   # baseline (~20s)
./tools/tree-harness.sh verify   ./BC.History .snapshots/bc   # verify (~11s, ~25s with a large delta)

# Standard development cycle
tree-sitter generate         # Generate parser from grammar.js
tree-sitter generate --report-states-for-rule -  # Rank rules by parser-state cost
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
- `grammar.js` - Main grammar definition (~4,121 lines). Never edit `src/parser.c` (auto-generated)
- `src/scanner.c` - External scanner for property disambiguation and preprocessor patterns
- `test/corpus/` - Test suite with AL code and expected parse trees (1,514 tests)
- `queries/` - 6 query files (highlights, locals, tags, indents, folds, textobjects)

**Key Design Principles (V2 architecture):**
- **Parse structure, don't validate** — Accept any `Name = Value ;` as a property. Semantic validation belongs in linters/LSP servers, not the parser
- **Scanner-based property disambiguation** — The `PROPERTY_NAME` scanner token distinguishes `identifier =` (property) from `identifier :` (variable) via 1-char lookahead
- **Generic property rule** — ONE `property` rule handles all simple properties (vs V1's 291 individual rules)
- **Generic preprocessor** — ONE `preproc_conditional` rule + ~12 dedicated split-construct rules (vs V1's 63)
- **Named keyword nodes** — 83 keywords exposed as named nodes for query matching (81 grammar rules + the external `begin_keyword`/`end_keyword`), all with a uniform shape: one anonymous child typed as the canonical lowercase spelling
- **Stateful scanner** — 1-byte depth counter tracks `#if`/`#endif` nesting; `begin`/`end` are named at every depth, and the depth counter decides only whether a `PREPROC_SPLIT_*` token gets first refusal

**Scanner Tokens:**

| Token | Purpose |
|-------|---------|
| `PROPERTY_NAME` | `identifier` followed by `=` (not `:=`) — property/variable disambiguation |
| `CONTINUE_AS_IDENTIFIER` | `continue` followed by `:=` — used as variable name |
| `PREPROC_OPEN` | `#if` — increments depth counter |
| `PREPROC_CLOSE` | `#endif` — decrements depth counter |
| `BEGIN_KEYWORD` | `begin` at any depth — named node for queries |
| `END_KEYWORD` | `end` at any depth — named node for queries |
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

83 keywords are named nodes for query matching — 81 grammar rules plus the two external tokens `begin_keyword`/`end_keyword`. **Every grammar keyword rule has the same shape: exactly one anonymous child, typed as the canonical lowercase spelling.**

```javascript
table_keyword: $ => alias(kw('table'), 'table'),          // anonymous "table" child
procedure_keyword: $ => alias(kw('procedure'), 'procedure'),
if_keyword: $ => prec(10, alias(kw('if'), 'if')),         // anonymous "if" child
```

Compound (CamelCase) keywords use `kwCases()` instead of `kw()`, because their case-spelling whitelist is load-bearing — see "CamelCase keywords" below — but they produce the identical shape:

```javascript
enum_keyword: $ => prec(10, kwCases('enum', 'enum', 'ENUM', 'Enum', 'eNUM', 'eNum', 'ENum')),
```

**begin/end are named via stateful scanner** — `begin_keyword` and `end_keyword` are emitted at **every** depth. `grammar.js` has no `kw('begin')`/`kw('end')` fallback: begin/end are scanner-exclusive, the same way `#if`/`#endif` became scanner-exclusive in 3.2.0, so there is no scanner/literal pair for GLR to fork on. Direct naming via grammar rules or `alias()` still breaks GLR backtracking — the stateful scanner is the correct approach.

The depth counter no longer decides whether the keyword is *named*; it decides only whether a `PREPROC_SPLIT_*` token gets first refusal. Both decisions happen in **one** scan: the scanner reads the keyword, calls `mark_end`, runs the split lookahead, and picks the symbol from the result. They cannot be two sequential blocks — a scan that returns false discards every advance and is not re-entered at the same position.

Until 4.0.0 the depth > 0 case handed off to an anonymous `kw('begin')`, which made a complete `begin … end` inside any `#if` block **vanish from the tree**: `kw()` builds a `token(PATTERN)`, and tree-sitter renders anonymous *pattern* tokens as hidden `aux_sym_*` symbols (`.visible = false`), unlike anonymous *string* tokens such as `";"`, which are visible. The keyword was lexed and then dropped, so the CST was not lossless over the source and both keywords were unhighlightable inside every `#if`.

**Named keyword node structure — uniform since 4.0.0.** A named rule whose entire body is a single token collapses *into* that token, so the node's shape is decided by that token's visibility, which is the same `.visible` rule as above. A bare `kw('word')` builds a `token(PATTERN)` and therefore yields a **childless leaf**; wrapping it in `alias(…, 'word')` makes the token a visible STRING and yields **one anonymous child**. Before 4.0.0 the grammar mixed both, so a consumer could not predict a keyword's shape.

> **Every grammar keyword rule is now `alias(kw('word'), 'word')` (or `kwCases(...)` for compound keywords) and has exactly one anonymous child typed as the canonical lowercase spelling. The 2 external tokens cannot take a child and remain childless leaves.**

| body | child | count |
|---|---|---|
| `alias(kw('word'), 'word')` → STRING | one anonymous child typed `"word"` | 68 |
| `kwCases('word', …)` → STRING, each spelling aliased to `'word'` | one anonymous child typed `"word"` | 13 |
| external scanner token (`begin_keyword`, `end_keyword`) | none — cannot take a child | 2 |

The child's type is always the canonical lowercase spelling regardless of how the source spelled the keyword: `XmlPort` yields `(xmlport_keyword "xmlport")`, and the node's own text is still `XmlPort`.

**`node-types.json` cannot confirm this for you.** It lists anonymous children only when they sit inside a field, and none of these do, so all 83 keyword nodes look childless there regardless of their real shape. **Read a keyword's text from the node itself, never by descending into a child** — that stays correct for the external tokens too, and it survives any future change to the anonymous layer.

`_tabledata_keyword` is deliberately excluded: it is a *hidden* (`_`-prefixed) token helper, not a keyword node, and one of its two uses re-aliases it to `$.identifier`.

**CamelCase keywords** use `kwCases()` — an explicit case-spelling whitelist, each spelling aliased to the canonical lowercase form:
```javascript
controladdin_keyword: $ => prec(10, kwCases('controladdin',
  'controladdin', 'CONTROLADDIN', 'Controladdin', 'ControlAddIn', 'ControlAddin', 'controlAddIn', 'controlAddin')),
```

**The whitelist is load-bearing — never "simplify" these to `kw()`.** `kw()` compiles to a case-*insensitive* regex, which would claim every case permutation and steal spellings that AL code legitimately uses as identifiers. Real AL declares `eNuM: Decimal;` as a variable; `eNuM` is absent from `enum_keyword`'s whitelist precisely so it stays an `identifier`. Converting the 13 compound keywords to `kw()` fails `test/corpus/enum_as_identifier_test.txt`.

## Attribute Handling

Attributes are first-class statements (Rust/C# pattern) — siblings to declarations, not nested.

```al
[Scope('OnPrem')]
[IntegrationEvent(false, false)]
procedure MyEvent() begin end;
```

Parse tree: `(attribute_item ...) (procedure ...)`  — separate nodes at the same level.

## Preprocessor Handling

**Line-level directives** are `extras` (reachable anywhere): `pragma`,
`preproc_region`, `preproc_endregion`, `preproc_define`, `preproc_undef`. They
never touch the scanner's `#if`/`#endif` depth counter. The AL compiler only
accepts `#define`/`#undef` before the first real token of a file — that
positional rule is a linter's job, not the parser's. See
`docs/preproc-define-undef.md`.

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
| parser.c size | 26.0 MB |
| SYMBOL_COUNT | ~846 |
| STATE_COUNT | ~12,545 |
| grammar.js lines | ~4,121 |
| Tests | 1,514 |
| Production success | 100% (0 errors) |
| Named keywords | 83 (81 rules + 2 external), uniform shape |
| Query files | 6 (highlights, locals, tags, indents, folds, textobjects) |

## Validating AL Syntax Questions

When uncertain whether the AL compiler accepts a construct (esp. niche or undocumented forms), use the **`al compile`** CLI to test directly — it's the ground truth, not LLM recall or web search.

```bash
# Minimal probe project
mkdir -p /tmp/al-probe && cd /tmp/al-probe
cat > app.json <<'EOF'
{"id":"11111111-2222-3333-4444-555555555555","name":"Probe","publisher":"Test",
 "version":"1.0.0.0","platform":"1.0.0.0","application":"1.0.0.0",
 "idRanges":[{"from":50000,"to":99999}],"runtime":"12.0","target":"OnPrem"}
EOF
cat > Test.al <<'EOF'
codeunit 50100 Probe { trigger OnRun() begin Codeunit.Run(Codeunit::80); end; }
EOF
al compile /project:. /out:test.app; echo "EXIT=$?"
```

Exit `0` + `test.app` written = compiler accepts. Exit `1` with no `test.app` = rejected (errors may be silent — re-run capturing stderr or trim the file to isolate). Example: confirmed `Codeunit::<integer>` is valid AL (old-school soft cross-extension reference) when both LLMs claimed otherwise.

## Documentation Resources

**Available via MCP:**
- **business-central** — AL Language syntax, objects, properties
- **tree-sitter** — Grammar development guide, API reference

**Project docs:**
- `docs/v2-blog-post-notes.md` — V2 rewrite narrative and data
- `docs/superpowers/specs/` — Design specs for major changes
- `docs/database-reference-numeric-id-fix.md` — `Codeunit::N` / `Page::N` numeric ID support
- `docs/preproc-define-undef.md` — `#define`/`#undef` support, compiler-verified accept/reject matrix

## Philosophy: No Known Limitations

**Never give up on a failing pattern:**
- Don't disable tests or mark issues as "known limitations"
- Research how other parsers handle similar constructs in `other-languages/`
- Use `error-research` agent for systematic failure analysis
- Every "impossible" pattern has been solved somewhere — find it and adapt it
