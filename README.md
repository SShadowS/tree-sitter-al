# tree-sitter-al

A [tree-sitter](https://tree-sitter.github.io/tree-sitter/) parser for the AL programming language used in Microsoft Dynamics 365 Business Central.

## Overview

This project provides a complete grammar definition for parsing AL (Application Language) source code, enabling syntax highlighting, code analysis, and language tooling support for Business Central development.

### Known Issues & Limitations

Based on analysis of 396 AL files from production codebases, **363 files (91.7%) parse successfully**. The remaining 33 files reveal these known issues:

#### Critical Parsing Issues
- **Standalone semicolons**: Empty statements with just `;` in object properties cause parsing failures
- **Multi-line Permissions property**: Complex tabledata permission lists spanning multiple lines not fully supported
- **Property placement**: Some property ordering combinations cause unexpected parsing behavior

#### Feature Gaps
- **Report-specific constructs**: Some report objects with complex dataset structures
- **Advanced Codeunit patterns**: Complex permission declarations in codeunit headers
- **Legacy .NET integration**: Some OnPrem-specific .NET/DLL related constructs
- **Control Add-in definitions**: Partial support for custom control add-in declarations

#### Expression Limitations  
- **Complex macro definitions**: Advanced preprocessor patterns not fully supported
- **Nested IF expressions**: Some deeply nested conditional expressions in property values
- **Advanced method chaining**: Complex fluent API patterns may need refinement

#### Recovery & Robustness
- **Error propagation**: Single syntax errors can cascade and affect subsequent parsing
- **Whitespace sensitivity**: Some edge cases with unusual spacing/formatting
- **Comment placement**: Complex comment patterns between properties occasionally problematic

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
