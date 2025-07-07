# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a tree-sitter parser for the AL (Application Language) programming language used in Microsoft Dynamics 365 Business Central. The project provides grammar definitions to enable syntax highlighting, code analysis, and language tooling support.

**Current status**: 
- Production files: 97.3% success rate (14,946 out of 15,358 production AL files from BC.History parse successfully)
- Test suite: 851 tests passing (run `tree-sitter test` to verify)
- All tests pass including preprocessor patterns and edge cases
- Grammar improvements completed through 20+ iterations
- Recent major achievement: Comprehensive preprocessor support via external scanner
- Previous "known limitations" now fixed: preprocessor split procedures, conditional object declarations, mixed var/procedure sections

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
1. **Check documentation first**: Use the Business Central docs MCP server to verify if the property is universal or object-specific.
   - If used across multiple object types → Add to `_universal_properties`
   - If truly object-specific → Add to the appropriate object property list
2. Determine its primary semantic category (e.g., universal, display, validation, data, navigation, access). Some properties might be semantically tied to specific object types; these are still defined centrally but grouped into more specialized semantic categories.
3. Add property definition to individual property rules section.
4. Add the property rule to the appropriate semantic category list(s) (e.g., `_universal_properties`, `_page_properties`, `_table_properties`, `_action_properties`).
5. Property automatically available in composed groups (`_field_properties`, `_control_properties`, etc.) that use these semantic categories.
6. Create test cases covering the property in relevant object contexts.
7. Test with `tree-sitter generate && tree-sitter test`.

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

### Object-Specific Property Lists
When adding properties, follow this decision process:

1. **First, check if the property is universal/generic**:
   - Search the Business Central documentation to see if the property applies to multiple object types
   - If it's used across different objects (tables, pages, reports, etc.), add it to `_universal_properties`
   - This follows DRY principles and ensures the property is available everywhere it's needed

2. **Only if object-specific, add to the appropriate list**:
   - **XMLPort properties**: Add to `xmlport_table_property` choice list
   - **Query properties**: Add to `_query_properties` choice list
   - **Report properties**: Add to `_report_properties` choice list
   - Check for existing semantic categories before creating new ones

3. **Example decision process**:
   ```javascript
   // BAD: Adding Caption to query-specific properties
   _query_properties: $ => choice(
     $.caption_property,  // Don't do this - Caption is universal!
     ...
   )
   
   // GOOD: Caption is already in _universal_properties
   _universal_properties: $ => choice(
     $.caption_property,  // Defined once, used everywhere
     ...
   )
   ```

## External Scanner and Preprocessor Handling

The parser uses an external scanner (src/scanner.c) to handle complex preprocessor patterns that cannot be expressed in the JavaScript grammar alone.

### When to Use External Scanner
External scanners are needed when:
1. **Lexical lookahead is required** - Need to examine upcoming tokens to make parsing decisions
2. **State tracking across tokens** - Need to maintain state between different parts of the parse
3. **Complex token patterns** - Patterns that depend on context or preceding tokens

### Preprocessor Support Implementation
The external scanner implements comprehensive preprocessor support by:

1. **Tracking preprocessor state** - Maintains a stack of preprocessor contexts
2. **Detecting split constructs** - Identifies when preprocessor directives split AL language constructs
3. **Emitting special tokens** - Produces tokens like `PREPROC_SPLIT_MARKER` that the grammar uses

### Key Scanner Tokens
```c
enum TokenType {
    PREPROC_ACTIVE_REGION_START,    // Start of #if active region
    PREPROC_ACTIVE_REGION_END,      // End of active region
    PREPROC_INACTIVE_REGION_START,  // Start of inactive region
    PREPROC_INACTIVE_REGION_END,    // End of inactive region
    PREPROC_SPLIT_MARKER,           // Marks split constructs
    PREPROC_CONTINUATION_MARKER,    // Marks continuations
    ERROR_SENTINEL                  // Error handling
};
```

### Grammar Integration
The grammar uses these scanner tokens through:

1. **externals array** - Declares scanner tokens in grammar.js
2. **Special rules** - Rules like `preproc_split_procedure` that handle split constructs
3. **Conditional parsing** - Different parse paths based on preprocessor context

### Common Preprocessor Patterns Fixed

1. **Split procedure headers**:
   ```al
   #if not CLEAN26
       procedure Test() Result: Integer
   #else
       procedure Test(): Integer
   #endif
   ```
   - Uses `preproc_split_procedure` rule
   - Scanner detects the split pattern
   - Grammar handles both branches

2. **Conditional object declarations**:
   ```al
   #if CLEAN26
   table 50000 MyTable
   #else
   table 50000 "My Table"
   #endif
   {
       // fields...
   }
   ```
   - Uses `preproc_conditional_object_declaration` rule
   - Allows different object headers in branches

3. **Mixed var/procedure sections**:
   ```al
   #if not CLEAN25
       var
           Item: Record Item;
       
       procedure CalcPrice()
       begin
       end;
   #endif
   ```
   - Uses `preproc_conditional_mixed_content` rule
   - Handles mixed content types in preprocessor blocks

4. **Split if-else statements**:
   ```al
   #if not CLEAN24
       if condition then
           statement1
       else
   #endif
       statement2
   ```
   - Uses `preproc_split_if_else` rule
   - Handles else keyword inside preprocessor with body outside
   - Common pattern in Business Central codebase for version compatibility

### Adding New Scanner Features
When adding scanner features:
1. Update `src/scanner.c` with new token types and detection logic
2. Add tokens to `externals` array in grammar.js
3. Create grammar rules that use the new tokens
4. Update build files (binding.gyp, bindings/rust/build.rs) if needed
5. Test thoroughly with edge cases

## Known Limitations
- Standalone semicolons in object properties cause parsing failures
- Multi-line permission declarations not fully supported
- Some report-specific constructs and advanced codeunit patterns
- Error propagation can cascade from single syntax errors
- **Qualified enum values with quoted enum type names**: Due to tree-sitter's lexing behavior, patterns like `"Enum Type Name"::EnumValue` cannot be parsed correctly. The quoted string is lexed as a single token before the parser can recognize the `::` pattern. Use unquoted enum type names instead (e.g., `EnumTypeName::EnumValue`).
- **WHERE clauses in deeply nested preprocessor contexts**: WHERE clauses within table relations that are inside preprocessor conditionals may not parse correctly in certain complex nesting scenarios
- **Interface return types with length specifications**: Due to tree-sitter's LR parser limitations, interface procedures with return types that include length specifications (e.g., `Code[50]`, `Text[100]`) create ERROR nodes. The parser reduces the type early before seeing the length specification. This works correctly in regular procedures and parameters but fails specifically for interface return types. Use type definitions without length specifications in interface return types as a workaround.
- **Property names as variable names in page var sections**: Due to parsing ambiguity, certain property names (particularly `Width`) cannot be used as variable names in var sections within pages. The parser incorrectly tries to parse them as page properties instead of variable identifiers. This works correctly in other object types (tables, codeunits). Workaround: Use quoted identifiers (e.g., `"Width": Decimal;`) or different variable names.
- **Complex preprocessor patterns with fragmented if-else**: Patterns where preprocessor directives create fragmented if-else structures with additional code following the fragmented block can cause parsing errors. The `preproc_fragmented_if_else` rule can interfere with normal preprocessor nesting in these cases.

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
If it fails, use the Microsoft.docs.mcp instead to get information on documentation.

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

### Standard Pattern (Default)
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

### Contextual Property Pattern (Exceptions)
Some property names conflict with common variable names and cannot be resolved using the standard kw() pattern due to lexer-level tokenization. For these specific cases ONLY:

**Current contextual properties:**
- `TableType` - Used as enum variable in Opportunities.Page.al
- `Style`/`StyleExpr` - Common variable names for UI styling  
- `IsPreview` - Used for preview state tracking
- `Filters` - Used as variable name in MyNotifications.Page.al

**Pattern:**
1. Property definition uses literal strings with all case variations
2. _unquoted_variable_name includes all case variations as aliases

```javascript
// Property definition
table_type_property: $ => seq(
  field('name', alias(
    choice('TableType', 'tabletype', 'TABLETYPE', 'Tabletype'),
    'TableType'
  )),
  '=',
  field('value', alias($.table_type_value, $.value)),
  ';'
),

// In _unquoted_variable_name
alias('TableType', $.identifier),
alias('tabletype', $.identifier),
alias('TABLETYPE', $.identifier),
alias('Tabletype', $.identifier),
```

**When to apply this pattern:**
1. Only when actual parsing failures occur in production files
2. Property name is a common English word likely to be used as variable
3. Standard kw() pattern causes unresolvable conflicts
4. Document the specific file/context where the conflict occurred

**DO NOT** apply this pattern preemptively. It violates DRY principles and should only be used when necessary.

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

### 7. XMLPort Element Field References
**Symptom**: Parser fails on fieldelement with member expressions
```
// Fails: fieldelement(Nm; CompanyInformation.Name)
(ERROR
  (member_expression ...)
)
```

**Root Cause**: XMLPort elements expect field_access (Table."Field") but actual code uses member_expression (Table.Field)

**Fix Pattern**:
1. Add `$.member_expression` to the source_table choices in `xmlport_table_element`
2. This allows both quoted and unquoted field references

### 9. Preprocessor Split Constructs
**Symptom**: Parser fails when preprocessor directives split language constructs
```
// Fails: else keyword inside #if but body outside
#if not CLEAN24
    if condition then
        statement1
    else
#endif
    statement2
```

**Root Cause**: Standard grammar rules don't handle constructs split by preprocessor directives

**Fix Pattern**:
1. Create specialized rule for the split pattern (e.g., `preproc_split_if_else`)
2. Add to appropriate choice lists where the construct appears
3. External scanner handles detection of split patterns
4. See "Common Preprocessor Patterns Fixed" section for examples

### 8. Missing Property Values in Enums
**Symptom**: Property accepts limited values but actual code uses additional valid values
```
// Example: MaxOccurs = Once; fails when only 'unbounded' and integers are supported
```

**Root Cause**: Incomplete enumeration of valid property values

**Fix Pattern**:
1. Check documentation for all valid values
2. Add missing values to the property's value choice list using `kw()`:
```javascript
max_occurs_value: $ => choice(
  $.integer,
  kw('unbounded'),
  kw('once')  // Add missing value
),
```

### 9. Object-Specific Properties That Should Be Universal
**Symptom**: Properties with object-specific prefixes (e.g., `page_about_text_ml_property`) that are actually used across multiple object types
```
// BAD: Separate definitions for same property
page_about_text_ml_property: $ => seq(...)
report_about_text_ml_property: $ => seq(...)
```

**Root Cause**: Properties were initially added for specific objects but are actually universal

**Fix Pattern**:
1. Create generic property without object prefix:
```javascript
// GOOD: Single universal definition
about_text_ml_property: $ => seq(
  kw('AboutTextML'),
  $._ml_property_template
),
```
2. Add to `_universal_properties` list
3. Remove object-specific versions from property lists (they'll inherit from universal)
4. Update test expectations to use generic node names
5. Delete deprecated object-specific rules if no longer referenced

### 10. Operators Parsed as Identifiers
**Symptom**: Mathematical operators like `div` and `mod` parsed as identifiers instead of operators
```
// Fails: A := 10 div 2;
(assignment_expression
  left: (identifier)  // A
  right: (integer))   // 10
(identifier)          // div - parsed as separate identifier!
(integer)             // 2
```

**Root Cause**: Using `kw()` for operators creates tokens that conflict with identifier tokens

**Fix Pattern**:
1. Check if logical operators have similar issues and use same pattern:
```javascript
// BAD: Using kw() for operators
field('operator', choice('*', '/', kw('div'), kw('mod'))),

// GOOD: Using choice() for case variations
field('operator', choice('*', '/', 
  choice('div', 'DIV', 'Div'), 
  choice('mod', 'MOD', 'Mod')
)),
```
2. Look for comments warning about this pattern (e.g., "logical operators must use choice()")
3. Test with expressions in various contexts (assignments, case statements)

### 11. Preprocessor Conditionals in Property Blocks
**Symptom**: Parser reports MISSING "}" when preprocessor directives appear inside property blocks
```
// Fails: Key with conditional obsolete properties
key(Key1; Field)
{
    Clustered = false;
#if CLEAN26
    ObsoleteState = Removed;
#else
    ObsoleteState = Pending;
#endif
}  // MISSING "}" error here
```

**Root Cause**: Property block rules don't include preprocessor conditional choices

**Fix Pattern**:
1. Create a preprocessor conditional rule for the specific property context:
```javascript
preproc_conditional_key_properties: _preproc_conditional_block_template($ => choice(
  $.clustered_property,
  $.enabled_property,
  $.obsolete_reason_property,
  $.obsolete_state_property,
  $.obsolete_tag_property,
  // ... other properties
  $.preproc_conditional_key_properties  // Allow nesting
)),
```
2. Add the new rule to the property block's choice list:
```javascript
repeat(choice(
  $.clustered_property,
  $.enabled_property,
  // ... other properties
  $.preproc_conditional_key_properties,  // Add this
  $.property
)),
```
3. Test with nested preprocessor blocks and mixed property types

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

# Using Gemini CLI for Large Codebase Analysis

When analyzing large codebases or multiple files that might exceed context limits, use the Gemini CLI with its massive
context window. Use `gemini -p` to leverage Google Gemini's large context capacity.

## File and Directory Inclusion Syntax

Use the `@` syntax to include files and directories in your Gemini prompts. The paths should be relative to WHERE you run the
  gemini command:

### Examples:

**Single file analysis:**
gemini -p "@src/main.py Explain this file's purpose and structure"

Multiple files:
gemini -p "@package.json @src/index.js Analyze the dependencies used in the code"

Entire directory:
gemini -p "@src/ Summarize the architecture of this codebase"

Multiple directories:
gemini -p "@src/ @tests/ Analyze test coverage for the source code"

Current directory and subdirectories:
gemini -p "@./ Give me an overview of this entire project"

# Or use --all_files flag:
gemini --all_files -p "Analyze the project structure and dependencies"

Implementation Verification Examples

Check if a feature is implemented:
gemini -p "@src/ @lib/ Has dark mode been implemented in this codebase? Show me the relevant files and functions"

Verify authentication implementation:
gemini -p "@src/ @middleware/ Is JWT authentication implemented? List all auth-related endpoints and middleware"

Check for specific patterns:
gemini -p "@src/ Are there any React hooks that handle WebSocket connections? List them with file paths"

Verify error handling:
gemini -p "@src/ @api/ Is proper error handling implemented for all API endpoints? Show examples of try-catch blocks"

Check for rate limiting:
gemini -p "@backend/ @middleware/ Is rate limiting implemented for the API? Show the implementation details"

Verify caching strategy:
gemini -p "@src/ @lib/ @services/ Is Redis caching implemented? List all cache-related functions and their usage"

Check for specific security measures:
gemini -p "@src/ @api/ Are SQL injection protections implemented? Show how user inputs are sanitized"

Verify test coverage for features:
gemini -p "@src/payment/ @tests/ Is the payment processing module fully tested? List all test cases"

When to Use Gemini CLI

Use gemini -p when:
- Analyzing entire codebases or large directories
- Comparing multiple large files
- Need to understand project-wide patterns or architecture
- Current context window is insufficient for the task
- Working with files totaling more than 100KB
- Verifying if specific features, patterns, or security measures are implemented
- Checking for the presence of certain coding patterns across the entire codebase

Important Notes

- Paths in @ syntax are relative to your current working directory when invoking gemini
- The CLI will include file contents directly in the context
- No need for --yolo flag for read-only analysis
- Gemini's context window can handle entire codebases that would overflow Claude's context
- When checking implementations, be specific about what you're looking for to get accurate results