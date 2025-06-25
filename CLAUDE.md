# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a tree-sitter parser for the AL (Application Language) programming language used in Microsoft Dynamics 365 Business Central. The project provides grammar definitions to enable syntax highlighting, code analysis, and language tooling support.

**Current status**: 
- Production files: 92.3% success rate (14,176 out of 15,358 production AL files from BC.History parse successfully)
- Test suite: Tests passing (run `tree-sitter test` to get exact count)
- All tests pass including contextual keyword tests and edge cases
- Grammar improvements completed through 20 additional iterations (12-20)
- Recent fixes include: qualified trigger names, case-insensitive SQL properties, CueGroupLayout property, negated exist formulas
- Known limitations: multiline page link properties with const() values, conditional object declarations

## Development Commands

### Core Grammar Development
```bash
# Comprehensive validation (recommended - runs all checks)
./validate-grammar.sh        # Quick validation
./validate-grammar.sh --full # Include AL file parsing test

# Individual commands:
# Generate parser from grammar.js changes
tree-sitter generate

# Build native parser
tree-sitter build

# Test grammar changes
tree-sitter test

# Test specific patterns
tree-sitter test -i "table"
tree-sitter test -i "page_action"

# Advanced testing options
tree-sitter test -i "regex_pattern"          # Include tests matching regex
tree-sitter test -e "regex_pattern"          # Exclude tests matching regex
tree-sitter test --file-name "filename.txt"  # Run tests from specific file
tree-sitter test -u                          # Update test expectations
tree-sitter test -d                          # Show parsing debug log
tree-sitter test --debug-build               # Compile parser in debug mode
tree-sitter test -D                          # Generate debug graphs (log.html)
tree-sitter test --wasm                      # Use WebAssembly parser
tree-sitter test --show-fields               # Force show fields in diffs
tree-sitter test --stat all                  # Show parsing statistics
tree-sitter test -r                          # Force rebuild parser
tree-sitter test --overview-only             # Show only pass-fail overview

# Combined development cycle
tree-sitter generate && tree-sitter test
```

### Grammar Validation Script
The `validate-grammar.sh` script provides comprehensive validation in a single command:

**Features:**
- **Parser generation and build** - Ensures grammar compiles correctly
- **Test suite execution** - Runs all tests and reports pass/fail statistics
- **Orphan rule detection** - Finds unused grammar rules using `find_unused_definitions.py`
- **Duplicate rule detection** - Identifies duplicate definitions using `analyze_duplicates.py`
- **AL file parsing test** (optional) - Tests against real Business Central files with `--full` flag
- **Common issue detection** - Checks for case-sensitive keywords and TODO comments
- **Colored output** - Clear visual feedback with success/warning/error indicators

**Usage:**
```bash
# Quick validation (recommended for regular development)
./validate-grammar.sh

# Full validation including AL file parsing test
./validate-grammar.sh --full
```

The script exits with status 0 if all checks pass, or 1 if any issues are found.

### Interactive Development
```bash
# Web-based playground for testing
tree-sitter playground

# Parse and debug specific AL code
tree-sitter parse path/to/file.al --debug
echo "table 123 Test {}" | tree-sitter parse --debug # Remember to always encapsulate AL code in a codeunit or table definition

# Advanced parsing options
tree-sitter parse file.al --paths paths_file.txt     # Parse files from paths file
tree-sitter parse file.al -d pretty                  # Debug with pretty output
tree-sitter parse file.al --debug-build              # Use debug build parser
tree-sitter parse file.al -D                         # Generate debug graphs
tree-sitter parse file.al --dot                      # Output as graphviz dot
tree-sitter parse file.al -x                         # Output as XML
tree-sitter parse file.al -c                         # Output as pretty CST
tree-sitter parse file.al -s                         # Show statistics
tree-sitter parse file.al -t                         # Measure execution time
tree-sitter parse file.al -j                         # JSON output
tree-sitter parse file.al -n 5                       # Parse specific test number
tree-sitter parse file.al -r                         # Force rebuild parser
tree-sitter parse file.al --no-ranges                # Omit ranges in output
```

### Building Language Bindings
```bash
# WebAssembly build
tree-sitter build --wasm

# Node.js bindings
npm run build
npm start  # Builds WASM and starts playground

# Language-specific builds
make all        # C static/shared libraries
cargo build     # Rust crate
python setup.py build  # Python extension
```

### Package Management
```bash
# Node.js dependencies
npm install
npm test  # Runs Node.js binding tests

# Alternative build systems
make test     # Run tests via Makefile
cmake --build build --target test  # CMake
```

## Architecture Overview

### Core Files Structure
- **`grammar.js`**: Main grammar definition file - the heart of the parser
- **`src/parser.c`**: Auto-generated C parser code (never edit manually)
- **`src/grammar.json`**: Compiled grammar representation
- **`test/corpus/`**: Comprehensive test suite with AL examples and expected parse trees

### Grammar Organization
The grammar is monolithic in `grammar.js` but logically organized into sections:
- Object definitions (table, page, codeunit, enum, etc.)
- Extension objects (tableextension, pageextension)
- Statements and expressions
- Built-in functions and operators
- Property definitions
- Trigger and procedure handling

### DRY (Don't Repeat Yourself) Principle
The grammar follows DRY principles extensively to minimize duplication and improve maintainability:
- **Centralized Property Definitions**: Properties are defined once and reused across all relevant contexts through semantic category lists
- **Template Functions**: Common patterns like modifications use template functions to avoid repetition
- **Semantic Categories**: Properties are organized into logical groups (`_universal_properties`, `_display_properties`, `_validation_properties`, etc.) that can be composed for different object types
- **Reusable Patterns**: Common constructs are defined as separate rules and referenced wherever needed
This approach ensures consistency, reduces errors, and makes the grammar easier to maintain and extend.

### Language Bindings
Multi-language support via dedicated binding directories:
- `bindings/c/` - C headers and pkg-config
- `bindings/node/` - Node.js native addon
- `bindings/python/` - Python extension module
- `bindings/rust/` - Rust crate
- `bindings/go/` - Go module
- `bindings/swift/` - Swift package

## Testing Approach

### Test File Format
Tests in `test/corpus/` follow tree-sitter standard format:
```
================================================================================
Test Description
================================================================================

[AL source code to test]

--------------------------------------------------------------------------------

(expected_parse_tree)
```
Dont put comments in the parse tree, as they are not supported by tree-sitter.

### Test Categories
- **Object types**: `table.txt`, `codeunit.txt`, `page_*.txt`
- **Language features**: `procedure_*.txt`, `case_statements*.txt`
- **Built-in functions**: `built_in_functions_*.txt` (comprehensive coverage)
- **Advanced constructs**: `interface_test.txt`, `controladdin_test.txt`

### Adding New Tests
1. Create `.txt` file in `test/corpus/`
2. Use `tree-sitter parse` to generate expected parse tree
3. Run `tree-sitter test` to validate

### Test Management Guidelines
- **Never delete a test file** - correct the issue affecting the test instead
- **Updating multiple tests**: Use `tree-sitter test -u` if all files parse WITHOUT errors and you need to update many test expectations after parser output changes

## Grammar Development Guidelines

### Naming Conventions
- Use snake_case for grammar rule names
- Keep rule definitions simple and readable
- Comment complex or non-obvious rules

### Key Patterns
- Handle operator precedence with `prec.left`, `prec.right`, `prec`
- Avoid left recursion (tree-sitter doesn't support it)
- Use error recovery strategies for graceful error handling
- Leverage `choice`, `seq`, `optional`, `repeat` combinators
- **Apply DRY Principle**: Always look for existing patterns before creating new ones. Properties should be defined once in semantic categories and reused everywhere appropriate

### Helper Functions
- **`kw(word, precedence = null)`**: Creates case-insensitive keywords using RustRegex
  - Example: `kw('table')` matches 'table', 'Table', 'TABLE', etc.
  - Optional precedence: `kw('dotnet', 100)` for high-precedence keywords
  - Use for most AL keywords to ensure case-insensitive parsing
  - **EXCEPTIONS**: Do NOT use kw() for logical operators (not, and, or, xor) as they conflict with expression parsing

### Template Functions
- **`_modification_with_target_template(keyword, content_repeater)`**: For patterns like `addafter(target) { content }`
- **`_modification_without_target_template(keyword, content_repeater)`**: For patterns like `addfirst { content }`
- These templates reduce duplication for modification patterns

### Property Development Workflow
**Adding New Properties** (follow centralized architecture):
1. Determine its primary semantic category (e.g., universal, display, validation, data, navigation, access). Some properties might be semantically tied to specific object types; these are still defined centrally but grouped into more specialized semantic categories.
2. Add property definition to individual property rules section.
3. Add the property rule to the appropriate semantic category list(s) (e.g., `_universal_properties`, `_page_properties`, `_table_properties`, `_action_properties`).
4. Property automatically available in composed groups (`_field_properties`, `_control_properties`, etc.) that use these semantic categories.
5. Create test cases covering the property in relevant object contexts.
6. Test with `tree-sitter generate && tree-sitter test`.

**DO NOT** add new property *definitions* directly into object-specific choice lists (e.g., within a `table_properties` rule). Always define the property rule centrally and add this rule to the appropriate semantic category list(s). These centralized lists are then used to compose property sets for different objects or contexts.

### General Development Workflow
1. Study AL construct syntax and semantics
2. Check existing patterns in grammar.js for reuse
3. Add grammar rules to appropriate section
4. Create comprehensive test cases
5. Test with `tree-sitter generate && tree-sitter test`
6. Debug with `tree-sitter parse --debug`

## Common Parsing Issues and Fixes

### Root Cause Patterns
The most frequent parsing failures occur when:
1. **Properties exist but aren't accessible in the right context**
   - Property is defined but not included in the appropriate property group (semantic category list).
   - Property needs to be added to relevant semantic property categories (e.g., `_page_properties` for page contexts, `_dataitem_properties` for dataitem contexts, or `_universal_properties` if broadly applicable).

2. **Properties need case variations and proper field wrappers**
   - AL is case-insensitive but parser needs explicit case variations
   - Properties should use `field('value', ...)` wrappers for consistency

### Fix Pattern
1. Check if property rule exists in grammar.js
2. Use `kw()` function for case-insensitive keywords: `kw('PropertyName')`
   - For high-precedence keywords: `kw('PropertyName', 10)`
   - Replaces old pattern: `choice('PropertyName', 'propertyname', 'PROPERTYNAME')`
3. Wrap value in field: `field('value', $.property_value)`
4. Add property to appropriate semantic category list(s) (e.g., `_universal_properties`, `_dataitem_properties`, `_page_properties`, etc.)
5. Property automatically becomes available in composed groups

## Known Limitations
- Standalone semicolons in object properties cause parsing failures
- Multi-line permission declarations not fully supported
- Some report-specific constructs and advanced codeunit patterns
- Error propagation can cascade from single syntax errors
- **Qualified enum values with quoted enum type names**: Due to tree-sitter's lexing behavior, patterns like `"Enum Type Name"::EnumValue` cannot be parsed correctly. The quoted string is lexed as a single token before the parser can recognize the `::` pattern. Use unquoted enum type names instead (e.g., `EnumTypeName::EnumValue`).
- **WHERE clauses in deeply nested preprocessor contexts**: WHERE clauses within table relations that are inside preprocessor conditionals may not parse correctly in certain complex nesting scenarios

## Build Systems
The project supports multiple build approaches:
- **tree-sitter CLI**: Primary development tool
- **Makefile**: Unix/Linux static and shared libraries
- **CMake**: Cross-platform with automatic parser generation
- **Node.js**: npm scripts with WebAssembly support
- **Language-specific**: Cargo, setup.py, etc.

## Development Tips
- Always run `tree-sitter generate` after grammar changes
- Use `tree-sitter playground` for interactive testing
- Test grammar changes with real AL code samples
- Check parsing success rate with production AL files
- Monitor for conflicts and ambiguities during development
- Use 'rg' instead of 'grep' for faster searching in large codebases

## Available Documentation
Claude has access to comprehensive documentation through docs-mcp:
- **Tree-sitter documentation**: Complete tree-sitter grammar development guide, API reference, and best practices
- **Business Central AL Language reference**: Official Microsoft documentation for AL syntax, objects, properties, and language constructs

### Using the `search_docs` Tool
You can use the `search_docs` tool to find specific information within these documentation sets. Here's how it works:

```
search_docs (docs-mcp) [read-only]

Full name: mcp__docs-mcp__search_docs

Description:
Search up-to-date documentation for a library or package. Examples:

- {library: "business-central", query: "page properties"} -> matches latest version of AL Language documentation
- {library: "business-central", version: "10.0", query: "report dataitem"} -> matches AL Language 10.0 or earlier
- {library: "tree-sitter", query: "grammar syntax"} -> matches latest Tree-sitter documentation
- {library: "tree-sitter", version: "0.20.x", query: "choice function"} -> any Tree-sitter 0.20.x version

NOTE: Keep number of search words low. Use very specific keywords to narrow results, like max 3 words.

Parameters:
  • library (required): string - Library name.
  • version: string - Library version (exact or X-Range, optional).
  • query (required): string - Documentation search query.
  • limit: number - Maximum number of results.
```

Use these resources to:
- Understand tree-sitter grammar patterns and capabilities
- Reference official AL language syntax and semantics
- Find examples of proper grammar construction
- Verify AL property names, types, and contexts

## Memories
- At the end always run this before saying a change is complete: `./validate-grammar.sh` (or `tree-sitter generate && tree-sitter test`)
- A common fix is adding properties to the $._universal_properties list
- When doing changes to grammar, lookup the property, type, field and so on in the documentation so you know what the given item is defined and supports
- Use `./validate-grammar.sh` for comprehensive validation including orphan and duplicate detection

## Contextual Keywords Pattern
When AL keywords can be used as both properties and variable names (contextual keywords), they must be handled consistently:

1. **In property definitions**: Use `kw('keyword')` for case-insensitive matching
2. **In _unquoted_variable_name**: Also use `alias(kw('keyword'), $.identifier)` 
3. **Never use case-sensitive patterns** like `alias('Keyword', $.identifier)`

Example of correct pattern:
```javascript
// In property definition
subtype_property: $ => _value_property_template(kw('subtype'), $.value),

// In _unquoted_variable_name
alias(kw('subtype'), $.identifier),  // Correct - case-insensitive
// NOT: alias('SubType', $.identifier), alias('subtype', $.identifier), etc.
```

This ensures keywords work correctly in both property and identifier contexts with any case variation.

## Common Test Failure Patterns and Fixes

When fixing failing tests, these patterns occur frequently and have established solutions:

### 1. Property Not Recognized in Context
**Symptom**: Parser creates ERROR nodes where a property should be recognized
```
(ERROR
  (identifier)  // Property name like "CustomActionType"
  (identifier)  // Property value
)
```

**Root Cause**: Property exists but isn't included in the appropriate property list for that context

**Fix Pattern**:
1. Find where the property is used (e.g., in `customaction_declaration`)
2. Identify which property list is used (e.g., `_action_properties`)
3. Add the property to that list:
```javascript
_action_properties: $ => choice(
  $._universal_properties,
  $.custom_action_type_property,  // Add this line
  // ... other properties
),
```

### 2. Case-Sensitive Keywords Causing Parser State Issues
**Symptom**: Property works in isolation but fails when other properties precede it
```
// Works: CustomActionType = Flow;
// Fails: Visible = true; CustomActionType = Flow;
```

**Root Cause**: Parser state conflict after certain properties, often due to case-sensitive token matching

**Fix Pattern**:
1. Ensure property uses `kw()` function with precedence if needed:
```javascript
custom_action_type_property: $ => seq(
  kw('CustomActionType', 10),  // Add precedence
  '=',
  field('value', $._identifier_choice),
  ';'
),
```
2. Add the keyword to `_unquoted_variable_name` as a contextual keyword:
```javascript
alias(kw('customactiontype'), $.identifier),
```

### 3. Structural Mismatches in Test Expectations
**Symptom**: Parser works correctly but test shows differences in node structure
```
// Actual: assignment_expression
// Expected: assignment_statement
```

**Root Cause**: Grammar evolution has changed the parse tree structure

**Fix Pattern**:
1. If the current parsing is semantically correct, update test expectations:
```bash
tree-sitter test --file-name "test_file.txt" -u
```
2. Only do this if there are no ERROR or MISSING nodes

### 4. Missing Value Type Support
**Symptom**: Complex expressions not parsing in specific contexts
```
// Example: SalesLineType[1]::Resource fails
(ERROR
  (qualified_enum_value_tail
    (identifier))
)
```

**Root Cause**: Grammar rule doesn't accept all valid value types

**Fix Pattern**:
1. Find the rule that should match (e.g., `qualified_enum_value`)
2. Add missing value types to choices:
```javascript
field('enum_type', choice(
  $._enum_type_reference,
  $.identifier,
  $._quoted_identifier,
  $.field_access,
  $.subscript_expression,  // Add this
  $._chained_expression
)),
```

### 5. Malformed Syntax Handling
**Symptom**: Invalid syntax causes complete parsing failure
```
// Example: "# Region" with space causes ERROR
```

**Root Cause**: Parser expects strict syntax and doesn't handle common mistakes

**Fix Pattern**:
1. Add a catch-all rule for malformed constructs:
```javascript
malformed_directive: $ => new RustRegex('# [A-Za-z][^\\n\\r]*'),
```
2. Include in extras to treat as ignorable:
```javascript
extras: $ => [..., $.malformed_directive, ...],
```

### 6. Hidden Rules Preventing Expected Structure
**Symptom**: Expected nodes don't appear in parse tree
```
// Missing: table_filter_value node
```

**Root Cause**: Using hidden rules (prefixed with `_`) that don't create nodes

**Fix Pattern**:
1. Change hidden rule to visible by removing underscore:
```javascript
// Change: _table_filter_value
// To: table_filter_value
```
2. Update references to use the visible rule
3. Create proper node hierarchy (e.g., add `filter_expression` nodes)

### Quick Debugging Process
1. **Isolate the failing construct**: Test just the problematic line
2. **Test in minimal context**: Wrap in simplest valid AL structure
3. **Check if property/rule exists**: Search grammar.js
4. **Verify accessibility**: Check if included in relevant property lists
5. **Test with precedence**: Add precedence if parser state issues
6. **Update test expectations**: Use `-u` flag if parsing is correct

### When to Update Tests vs Fix Grammar
- **Update tests**: When grammar correctly parses the construct but tree structure has evolved
- **Fix grammar**: When ERROR or MISSING nodes appear, or functionality is broken
- **Document as limitation**: Only for genuinely complex cases (e.g., preprocessor splitting constructs)