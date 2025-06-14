# tree-sitter-al

A [tree-sitter](https://tree-sitter.github.io/tree-sitter/) parser for the AL programming language used in Microsoft Dynamics 365 Business Central.

## Overview

This project provides a complete grammar definition for parsing AL (Application Language) source code, enabling syntax highlighting, code analysis, and language tooling support for Business Central development.

### Parser Status

Based on analysis of 1,331 AL files from a comprehensive Business Central production codebase, **1,250 files (93.9%) parse successfully**.

Recent improvements include:
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
