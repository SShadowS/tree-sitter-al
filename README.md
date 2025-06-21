# tree-sitter-al

A [tree-sitter](https://tree-sitter.github.io/tree-sitter/) parser for the AL programming language used in Microsoft Dynamics 365 Business Central.

## Overview

This project provides a complete grammar definition for parsing AL (Application Language) source code, enabling syntax highlighting, code analysis, and language tooling support for Business Central development.

### Parser Status

Based on analysis of 15,358 AL files from the comprehensive Business Central production codebase, **13,371 files (87.0%) parse successfully**.

Recent improvements include:
- **OptimizeForTextSearch field property** - Added support for OptimizeForTextSearch property in table field declarations, enabling text search optimization at the field level
- **Preprocessor conditionals in using statements** - Added support for `#if not`, `#else`, and `#endif` directives within using statement sections for conditional compilation
- **Report column properties** - Created specialized property group for report columns with IncludeCaption, AutoFormatExpression, AutoFormatType, DecimalPlaces, and OptionCaption properties
- **Escaped double quotes in identifiers** - Added support for escaped double quotes (`""`) within quoted identifiers, enabling complex field names like `"BankAccReconLine.""Statement Amount"""`
- **ToolTip in area sections** - Added support for ToolTip property directly in action area sections for role center pages
- **SqlJoinType property** - Added support for SqlJoinType property in query and report dataitems with values InnerJoin, LeftOuterJoin, and CrossJoin
- **APIGroup and APIPublisher properties** - Extended APIGroup and APIPublisher properties from queries to page objects
- **RoleType property** - Added RoleType property support for entitlement objects with values Delegated and Local
- **Preprocessor in actions** - Added support for preprocessor directives (#if, #else, #endif) with 'not' operator in action sections
- **DefaultLayout property** - Added support for report DefaultLayout property with values like RDLC, Word, Excel
- **PermissionSetExtension objects** - Added support for permissionsetextension declarations with extends syntax
- **Entitlement objects** - Added support for entitlement declarations with ApplicationScope, PerUserServicePlan, and Role types
- **Query API properties** - Added support for EntityCaption, EntityName, EntitySetName, APIGroup, APIPublisher, APIVersion properties
- **Standalone semicolons in property contexts** - Added support for standalone semicolons in part sections, action blocks, and modify actions, significantly improving parsing compatibility
- **Empty option members** - Enhanced option types to support consecutive commas for empty members (e.g., `Option = 'Value1,,Value3';`)
- **ShowMandatory property expressions** - Enhanced ShowMandatory property to accept complex expressions like `NOT IsSaaSProd` instead of just boolean literals
- **RecordID case variation** - Added support for `RecordID` type with uppercase ID, complementing existing case variations
- **Preprocessor conditionals in table relations** - Enhanced table relations to support preprocessor conditionals with semicolons in conditional branches (e.g., `#if BC24 IF (...) Table1; #else IF (...) Table2; #endif`)
- **Pragma directive support in code blocks** - Added support for `#pragma warning disable/restore` directives within procedure code blocks
- **Namespace-qualified record types** - Added support for namespace-qualified table references in record variable declarations (e.g., `Record Microsoft.Foundation.UOM."Unit of Measure"`)
- **Unary plus operator** - Added support for unary `+` operator in expressions (e.g., `SignFactor := +1;`)
- **FOR...DOWNTO loops** - Added support for `DOWNTO` keyword in FOR statements (e.g., `FOR i := 10 DOWNTO 1 DO`)
- **StyleExpr comparison expressions** - Enhanced StyleExpr property to support comparison expressions with enum values (e.g., `StyleExpr = "Field" = "Field"::EnumValue;`)
- **ValuesAllowed mixed types** - Enhanced ValuesAllowed property to support both string literals and identifiers in comma-separated lists
- **String literal backslash support** - Fixed parsing of string literals containing backslash characters in function arguments
- **SubPageView table view syntax** - Enhanced SubPageView property to support full `sorting(...) where(...)` syntax
- **Report dataitem properties** - Added comprehensive support for DataItemTableView, RequestFilterFields, and RequestFilterHeading properties
- **StyleExpr boolean support** - Added boolean literal support to StyleExpr properties enabling `StyleExpr = TRUE;` syntax
- **AttentionAccent style value** - Enhanced style_value grammar to support AttentionAccent case-insensitive pattern
- **Complex property syntax** - Support for Caption and ToolTip properties with Comment parameters for multilingual applications
- **Page customization objects** - Full support for `pagecustomization` declarations with view modifications
- **Complete built-in function coverage** - All AL built-in functions across database, math, string, date/time categories
- **Advanced language constructs** - Interface operators, multi-dimensional arrays, range expressions
- **Extension objects** - Full support for page/table extensions and control add-ins

The parser successfully handles:
- All core AL object types (table, page, codeunit, enum, etc.)
- Page customizations with view filters and modifications
- Complex property declarations and configurations  
- Interface implementations and 'is'/'as' operators
- Comprehensive built-in function patterns
- Advanced triggers, procedures, and expression patterns

### Key Files

- **`grammar.js`**: The heart of the project - defines all AL language grammar rules
- **`test/corpus/`**: Comprehensive test suite with AL code examples and expected parse trees
- **`src/`**: Auto-generated C code for the parser (don't edit manually)

## Development Setup

### Prerequisites
- Node.js (v16+)
- tree-sitter CLI: `npm install -g tree-sitter-cli`

### Building the Parser
```bash
tree-sitter generate    # Generate parser from grammar.js
tree-sitter build      # Build native parser
```

## Usage

### Parsing AL Files
```bash
# Basic parsing
tree-sitter parse path/to/file.al

# Debug mode (shows detailed parse tree)
tree-sitter parse path/to/file.al --debug

# Quiet mode (only shows errors)
tree-sitter parse path/to/file.al --quiet
```

### Running Tests
```bash
# Run all grammar tests
tree-sitter test

# Test specific file patterns
tree-sitter test -f "table"
tree-sitter test -f "page_action"
```

### Interactive Development
```bash
# Start web-based playground
tree-sitter playground

# Watch mode for grammar development
tree-sitter generate --watch
```

## Testing

### Test Structure
Tests are located in `test/corpus/` with the format:
```
================================================================================
Test Description
================================================================================

[AL code to test]

--------------------------------------------------------------------------------

(expected_parse_tree)
```

### Adding Tests
1. Create new `.txt` file in `test/corpus/`
2. Follow the standard test format
3. Run `tree-sitter test` to validate
4. Use `tree-sitter parse` to generate expected parse tree

### Test Categories
- **Basic Objects**: `table.txt`, `codeunit.txt`, `page_type_variable.txt`
- **Advanced Features**: `page_action_groups.txt`, `enum_variables.txt`
- **Expressions**: `method_calls.txt`, `case_statements.txt`
- **Language Constructs**: `procedure_return_types.txt`, `exit_statements.txt`

## Contributing

### Grammar Development Guidelines
See [CONVENTIONS.md](CONVENTIONS.md) for detailed best practices including:
- Rule naming conventions (snake_case)
- Precedence handling
- Error recovery strategies
- Testing requirements

### Adding New Language Features
1. **Study the AL construct** - Understand syntax and semantics
2. **Check existing patterns** - Reuse similar grammar rules when possible
3. **Define grammar rules** - Add to appropriate section in `grammar.js`
4. **Create tests** - Add comprehensive test cases
5. **Test thoroughly** - Ensure no regressions in existing functionality

### Common Development Tasks
```bash
# Test changes
tree-sitter generate && tree-sitter test

# Debug specific AL code
echo "your AL code" | tree-sitter parse --debug

# Generate bindings
tree-sitter build --wasm  # WebAssembly
npm run build            # Native bindings
```

---

**Author**: Torben Leth (sshadows@sshadows.dk)  
**License**: MIT
