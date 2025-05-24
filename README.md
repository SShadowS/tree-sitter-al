# tree-sitter-al

A [tree-sitter](https://tree-sitter.github.io/tree-sitter/) parser for the AL programming language used in Microsoft Dynamics 365 Business Central.

## Overview

This project provides a complete grammar definition for parsing AL (Application Language) source code, enabling syntax highlighting, code analysis, and language tooling support for Business Central development.

**Current Status:** Active development - Core language features are implemented with ongoing improvements for advanced constructs.

## Features

### Supported AL Constructs
- ✅ **Object Types**: Tables, Pages, Codeunits, Queries, Page Extensions, Enum Extensions
- ✅ **Data Types**: Record, Codeunit, Page, Query, Option, Enum, Text, Code, Integer, Boolean, etc.
- ✅ **Control Structures**: If/Else, Case, For, While, Repeat/Until
- ✅ **Procedures**: Local/Internal modifiers, parameters, return types, variable sections
- ✅ **Triggers**: Object triggers (OnRun, OnAction, etc.) and field triggers
- ✅ **Properties**: All major object and field properties with proper value types
- ✅ **Expressions**: Method calls, member access, arithmetic/logical operations
- ✅ **Action Groups**: Page action grouping and variable-driven properties
- ✅ **Complex Formulas**: CalcFormula expressions, table relations, filters

### Language Bindings
- Node.js/JavaScript
- Python
- Rust
- Go
- Swift
- C/C++

## Project Structure

```
tree-sitter-al/
├── grammar.js              # Main grammar definition
├── src/                   # Generated parser source code
├── test/corpus/           # Test cases for grammar validation
│   ├── table.txt         # Table object tests
│   ├── page_action_groups.txt # Page with action groups
│   ├── codeunit.txt      # Codeunit tests
│   ├── method_calls.txt  # Method call patterns
│   └── ...               # Additional test files
├── bindings/             # Language-specific bindings
│   ├── node/            # Node.js bindings
│   ├── python/          # Python bindings
│   ├── rust/            # Rust bindings
│   └── ...              # Other language bindings
├── CONVENTIONS.md        # Grammar development guidelines
├── TREERULES.md         # Tree-sitter rule reference
└── package.json         # Project configuration
```

### Key Files

- **`grammar.js`**: The heart of the project - defines all AL language grammar rules
- **`test/corpus/`**: Comprehensive test suite with AL code examples and expected parse trees
- **`CONVENTIONS.md`**: Best practices for grammar development and AL language handling
- **`src/`**: Auto-generated C code for the parser (don't edit manually)

## Development Setup

### Prerequisites
- Node.js (v16+)
- tree-sitter CLI: `npm install -g tree-sitter-cli`

### Installation
```bash
git clone https://github.com/[username]/tree-sitter-al
cd tree-sitter-al
npm install
```

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

## Language Support Status

### Object Types
| Object Type | Status | Notes |
|-------------|--------|-------|
| Table | ✅ Complete | Full property and trigger support |
| Page | ✅ Complete | Including action groups, layout sections |
| Codeunit | ✅ Complete | Procedures, triggers, variable sections |
| Query | ✅ Complete | Elements, data items, properties |
| Page Extension | ✅ Complete | Action modifications, field additions |
| Enum Extension | ✅ Complete | Value definitions with properties |

### Advanced Features
- ✅ **Variable-driven Properties**: `Enabled = MyVariable`
- ✅ **Complex Method Calls**: `Record.FIELDNO("Field Name")`
- ✅ **CalcFormula Expressions**: Lookup, Sum, Count, Average, Min, Max
- ✅ **Table Relations**: IF conditions, FIELD/CONST filters
- ✅ **Action Groups**: Nested action organization
- ✅ **Error Recovery**: Graceful handling of syntax errors

### Known Limitations
- Some advanced C/AL legacy constructs may need refinement
- Complex macro definitions are not fully supported
- Some edge cases in nested expressions may need improvement

## Technical Details

### Grammar Architecture
- **Modular Design**: Separate rules for each object type and construct
- **Precedence Handling**: Explicit operator precedence using `prec.left/right`
- **Error Recovery**: Strategic use of optional rules and error tokens
- **Performance**: Optimized for typical AL file sizes and complexity

### Precedence Levels
1. **Primary Expressions**: Identifiers, literals, parentheses
2. **Member Access**: `Record.Field`, `Object.Method()`
3. **Unary Operations**: `-`, `NOT`
4. **Multiplicative**: `*`, `/`, `DIV`, `MOD`
5. **Additive**: `+`, `-`
6. **Comparison**: `=`, `<>`, `<`, `>`, `<=`, `>=`
7. **Logical AND**: `AND`
8. **Logical OR**: `OR`

### Key Design Decisions
- **Case-insensitive keywords**: Using regex patterns for AL's case-insensitive nature
- **Field precedence**: Properties vs. procedures resolved through precedence
- **Expression parsing**: Left-associative for most operators
- **String handling**: Support for AL's single-quote strings with escape sequences

## References

- [AL Language Documentation](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/developer/devenv-dev-overview)
- [Tree-sitter Documentation](https://tree-sitter.github.io/tree-sitter/)
- [Tree-sitter Grammar DSL](https://tree-sitter.github.io/tree-sitter/creating-parsers#the-grammar-dsl)

---

**Author**: Torben Leth (sshadows@sshadows.dk)  
**License**: MIT
