# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this tree-sitter parser for the AL (Application Language) programming language used in Microsoft Dynamics 365 Business Central.

**Current Status**: 97.3% production file success rate (14,946/15,358), 851 tests passing, comprehensive preprocessor support

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
tree-sitter playground      # Interactive web-based testing
```

**Common Test Options:**
- `-i "pattern"` - Include tests matching pattern
- `-e "pattern"` - Exclude tests matching pattern
- `--file-name "test.txt"` - Run specific test file
- `-d` - Show debug log
- `-D` - Generate debug graphs (log.html)

## Architecture

**Core Files:**
- `grammar.js` - Main grammar definition (never edit `src/parser.c`, auto-generated)
- `src/scanner.c` - External scanner for complex preprocessor patterns
- `test/corpus/` - Test suite with AL code and expected parse trees

**DRY Architecture:**
- **Properties**: Defined once, organized into semantic categories (`_universal_properties`, `_page_properties`, etc.)
- **Templates**: Reusable patterns for modifications, properties, etc.
- **Composition**: Property groups composed from semantic categories

## Attribute Handling

**Architecture:** Attributes are first-class statements (Rust/C# pattern).

**How it works:**
- Attributes appear as `attribute_item` nodes in the parse tree
- They are siblings to declarations, not nested within them
- Preprocessor directives can appear between attributes and declarations
- Semantic analysis (post-parse) associates attributes with following declarations

**Valid patterns:**

```al
// Multiple attributes before a procedure
[Scope('OnPrem')]
[IntegrationEvent(false, false)]
procedure MyEvent() begin end;

// Attribute before preprocessor directive (✅ NOW WORKS!)
[Obsolete('Use NewVersion', '24.0')]
#if not CLEAN24
procedure OldVersion() begin end;
#endif

// Attributes on table fields
table 50100 MyTable
{
    fields
    {
        [ExternalName('ID')]
        field(1; "No."; Code[20]) { }
    }
}

// Attributes on parameters
procedure Test([Mandatory] Param: Integer) begin end;

// Attributes on enum values
enum 50100 Status
{
    [Caption('Active')]
    value(0; Active) { }
}
```

**Migration for Tooling:**

OLD parse tree structure:
```
(attributed_procedure
  (attribute_list
    (attribute ...))
  (procedure ...))
```

NEW parse tree structure:
```
(object_body
  (attribute_item
    attribute: (attribute_content ...))
  (procedure ...))
```

Attributes are now separate nodes at the same level as declarations, requiring semantic binding in post-parse analysis.

## Testing

**Test Format** (`test/corpus/*.txt`):
```
========================================================================
Test Description
========================================================================
[AL source code]
------------------------------------------------------------------------
(expected_parse_tree)  // No comments allowed in parse trees
```

**Guidelines:**
- Never delete test files - fix the underlying issue instead
- Use `tree-sitter test -u` only if no ERROR/MISSING nodes exist
- Create tests for each new grammar feature

## Grammar Development

### Core Principles
- **DRY**: Always check for existing patterns before creating new ones
- **snake_case** for rule names
- Use `prec.left/right/prec` for precedence; avoid left recursion
- Leverage `choice`, `seq`, `optional`, `repeat` combinators

### Key Functions
- **`kw('word', precedence?)`** - Case-insensitive keywords (e.g., `kw('table')` matches Table/TABLE/table)
  - **Exception**: Don't use for logical operators (not/and/or/xor) - they conflict with expressions
  - Use explicit choice variants for operators: `choice('div', 'DIV', 'Div')`

### Property Development Workflow
1. **Check documentation** - Verify if property is universal or object-specific
2. **Define property rule** - Add to individual property rules section
3. **Add to semantic category** - `_universal_properties`, `_page_properties`, `_action_properties`, etc.
4. **Create tests** - Cover property in relevant contexts
5. **Validate** - Run `./validate-grammar.sh`

**Critical**: Never add property definitions directly to object-specific choice lists. Define centrally, then add to semantic categories.

### Development Workflow
1. Study AL construct (use Business Central docs MCP)
2. Check for existing patterns in grammar.js
3. Add/modify rules (update `src/scanner.c` if needed for preprocessor patterns)
4. Create tests
5. Run `./validate-grammar.sh`

## Common Issues

**Most frequent failures:**
1. **Property not accessible in context** - Defined but not added to appropriate semantic category list
2. **Case-sensitivity** - Missing `kw()` wrapper or precedence
3. **Missing value types** - Rule doesn't accept all valid value types

**Standard fix pattern:**
1. Verify property exists in grammar.js
2. Use `kw('PropertyName', precedence?)` for case-insensitivity
3. Wrap value: `field('value', $.property_value)`
4. Add to semantic category: `_universal_properties`, `_page_properties`, etc.
5. Run `./validate-grammar.sh`

## Known Limitations

~~**Preprocessor + Attributed Procedures**~~ **✅ FIXED in v2.0 (Rust-Style Attribute Refactor)**

The main limitation where attributes before preprocessor directives caused parse failures has been **RESOLVED**.

**Now supported:**
```al
[Attribute]
#if CONDITION
procedure Proc()
#endif
begin
end;
```

This pattern now parses correctly! Attributes are treated as first-class statements that can appear before preprocessor directives.

**Historical context:** This limitation affected 8 tests and was caused by Tree-sitter's literal tokens taking precedence over scanner tokens. The Rust-style refactor (treating attributes as statements rather than embedded modifiers) completely solved this issue.

**Unsupported patterns after refactor:**

Attributes INSIDE preprocessor branches with different attributes per branch are no longer supported:
```al
// ❌ NO LONGER SUPPORTED
#if CONDITION
[Attr1]
procedure Proc()
#else
[Attr2]
procedure Proc()
#endif
```

**Migration:** Place attributes outside preprocessor blocks:
```al
// ✅ SUPPORTED
[Attribute]
#if CONDITION
procedure Proc()
#endif
```

See `PHASE4_UNSUPPORTED_PATTERNS.md` for details on intentionally unsupported patterns.

## Debugging Parse Failures

When tests fail with ERROR/MISSING nodes and the issue isn't obvious, use the parsing debug tools to identify the exact problem.

**Quick Usage:**
```bash
# 1. Extract failing test to a file
cat test/corpus/failing_test.txt | sed -n '5,19p' > /tmp/test.al

# 2. Parse with debug output
tree-sitter parse /tmp/test.al -d > /tmp/debug.log 2>&1

# 3. Analyze with bug finder (shows exact issues with source context)
python parse_bug_finder.py /tmp/test.al /tmp/debug.log
```

**What you get:**
- Exact line/column of parsing bugs
- Source code context (5 lines around each issue)
- Bug types: ERROR nodes, error recovery, skipped tokens
- Parser state and recovery depth
- Specific recommendations for fixes

**Example output:**
```
BUG #1: error_recovery
Location: Line 6, Column 34
Description: Parser needed error recovery at depth 2

Source context:
       4 |         Config: Record "Config";
       5 |
>>>    6 |     [BusinessEvent(false, false)]
                                           ^
       7 | #if CLEAN25
Parser state: 2854
Recovery depth: 2
```

**When to use:**
- Test has ERROR or MISSING nodes in output
- `tree-sitter test -u` refuses to update due to errors
- Grammar changes cause unexpected test failures
- Need to understand why parser takes wrong path

**Available tools:**
- `parse_bug_finder.py` - Recommended: Correlates bugs with source code
- `parse_debug_analyzer.py` - Advanced: Full parse flow analysis
- See `PARSING_DEBUG_TOOLS.md` for complete documentation

## External Scanner (Preprocessor Support)

The external scanner (`src/scanner.c`) handles complex preprocessor patterns that can't be expressed in JavaScript grammar alone.

**Use cases:** Lexical lookahead, state tracking, context-dependent patterns

**Scanner tokens:** `PREPROC_ACTIVE/INACTIVE_REGION_START/END`, `PREPROC_SPLIT_MARKER`, `PREPROC_CONTINUATION_MARKER`

**Common patterns handled:**
- Split procedure headers (return type in different #if branches)
- Conditional object declarations (name variations across branches)
- Mixed var/procedure sections in preprocessor blocks
- Split if-else statements (else inside #if, body outside)
- Preprocessor conditionals in property blocks

**Adding scanner features:**
1. Update `src/scanner.c` with new token types/logic
2. Add tokens to `externals` array in grammar.js
3. Create grammar rules using the tokens
4. Test with edge cases

**CRITICAL - Scanner Token Integration:**
When integrating scanner tokens to resolve ambiguities, placement in grammar is crucial:
- ✅ **DO**: Place tokens as alternatives in `choice()` where parser needs to decide
- ❌ **DON'T**: Place tokens in `optional()` after `repeat()` - corrupts parser decisions
- **Rule**: Token should be at the decision point, not after structural boundaries

See `SCANNER_TOKEN_INTEGRATION_LESSONS.md` for detailed case study, debugging techniques, and common pitfalls when integrating external scanner tokens. Essential reading before modifying scanner or adding new scanner tokens.

## Documentation Resources

**Available via MCP:**
- **business-central** - AL Language syntax, objects, properties
- **tree-sitter** - Grammar development guide, API reference

**Usage:** Use `search_docs` tool with library name and concise query (max 3 words):
- `{library: "business-central", query: "page properties"}`
- `{library: "tree-sitter", query: "grammar syntax"}`

**Best practices:**
- Always verify property/type definitions in documentation before adding to grammar
- Common fix: Adding properties to `_universal_properties` list
- Always run `./validate-grammar.sh` before completing any task
- Use `rg` instead of `grep` for faster codebase searches

## Contextual Keywords

Keywords that can be both properties and variables require special handling:

**Standard pattern (preferred):**
```javascript
// Property: Use kw()
subtype_property: $ => _value_property_template(kw('subtype'), $.value),
// Variable: Also use kw()
alias(kw('subtype'), $.identifier),
```

**Exception pattern (only when kw() causes conflicts):**

Apply only when production files fail due to lexer conflicts. Current exceptions:
- `TableType`, `Style`/`StyleExpr`, `IsPreview`, `Filters`

```javascript
// Property: All case variations
choice('TableType', 'tabletype', 'TABLETYPE', 'Tabletype')
// Variable: All case variations as aliases
alias('TableType', $.identifier), alias('tabletype', $.identifier), ...
```

**Use exception pattern only when:**
- Actual parsing failures occur in production
- Property name is common variable name
- Standard kw() causes unresolvable conflicts
- Document specific file/context

## Test Failure Patterns (Quick Reference)

**Debugging process:**
1. Isolate failing construct, test in minimal context
2. Check if property/rule exists in grammar.js
3. Verify inclusion in relevant semantic categories
4. Test with precedence if parser state issues
5. **If still unclear, use `parse_bug_finder.py` to analyze debug output** (see "Debugging Parse Failures" section)
6. Update expectations (`-u`) only if no ERROR/MISSING nodes

**Common patterns:**

| Pattern | Symptom | Fix |
|---------|---------|-----|
| **Property not accessible** | ERROR nodes for property | Add property to semantic category list (`_action_properties`, etc.) |
| **Case-sensitivity** | Works alone, fails after other properties | Add `kw('Property', precedence)` + contextual keyword alias |
| **Structural mismatch** | Different node structure | Update tests with `-u` if parsing is correct (no ERRORs) |
| **Missing value types** | Complex expressions fail | Add missing types to rule's choice list (e.g., `$.subscript_expression`) |
| **Malformed syntax** | Invalid syntax crashes parser | Add catch-all rule, include in `extras` array |
| **Hidden rules** | Expected nodes missing | Remove `_` prefix to make rule visible |
| **XMLPort field refs** | Member expressions fail | Add `$.member_expression` to source_table choices |
| **Preprocessor splits** | Constructs split by #if fail | Create `preproc_split_*` rule, add to choice lists |
| **Missing enum values** | Valid values rejected | Add missing values using `kw()` |
| **Object-specific duplicates** | Same property with prefixes | Create generic property, add to `_universal_properties` |
| **Operators as identifiers** | `div`/`mod` parsed as identifiers | Use `choice('div', 'DIV', 'Div')` not `kw('div')` |
| **Preprocessor in blocks** | MISSING "}" with #if in blocks | Create `preproc_conditional_*_properties` rule |

**When to update vs fix:**
- **Update tests**: Grammar correct, tree structure evolved
- **Fix grammar**: ERROR/MISSING nodes present
