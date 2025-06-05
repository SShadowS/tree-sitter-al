# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a tree-sitter parser for the AL (Application Language) programming language used in Microsoft Dynamics 365 Business Central. The project provides grammar definitions to enable syntax highlighting, code analysis, and language tooling support.

**Current status**: 91.7% success rate (363 out of 396 production AL files parse successfully)

## Development Commands

### Core Grammar Development
```bash
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

### Property Development Workflow
**Adding New Properties** (follow centralized architecture):
1. Determine semantic category: universal, display, validation, data, navigation, access, or object-specific
2. Add property definition to individual property rules section
3. Add property to appropriate semantic category (`_universal_properties`, etc.)
4. Property automatically available in composed groups (`_field_properties`, `_page_properties`, etc.)
5. Create test cases covering the property in relevant object contexts
6. Test with `tree-sitter generate && tree-sitter test`

**DO NOT** add properties directly to object-specific choice lists - use centralized categories

### General Development Workflow
1. Study AL construct syntax and semantics
2. Check existing patterns in grammar.js for reuse
3. Add grammar rules to appropriate section
4. Create comprehensive test cases
5. Test with `tree-sitter generate && tree-sitter test`
6. Debug with `tree-sitter parse --debug`

## Known Limitations
- Standalone semicolons in object properties cause parsing failures
- Multi-line permission declarations not fully supported
- Some report-specific constructs and advanced codeunit patterns
- Error propagation can cascade from single syntax errors

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

## Memories
- At the end always run this before saying a change is complete: `tree-sitter generate && tree-sitter test`