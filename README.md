# tree-sitter-al

A [tree-sitter](https://tree-sitter.github.io/tree-sitter/) parser for the AL programming language used in Microsoft Dynamics 365 Business Central.

[![PyPI](https://img.shields.io/pypi/v/tree-sitter-al)](https://pypi.org/project/tree-sitter-al/)

## Parser Status

Validated against **15,358 production AL files** from the Business Central codebase:

| Metric | Value |
|--------|-------|
| **Success rate** | **99.95%** (15,351 / 15,358 files) |
| Tests | 1,404 |
| parser.c size | 10.6 MB |
| grammar.js | ~3,000 lines |
| Named keywords | 80 (queryable via highlights/tags) |
| Query files | 5 (highlights, locals, tags, indents, folds) |

## Installation

### Python (tree-sitter 0.24+)

```bash
pip install tree-sitter-al
```

```python
import tree_sitter
import tree_sitter_al

lang = tree_sitter.Language(tree_sitter_al.language())
parser = tree_sitter.Parser(lang)
tree = parser.parse(b'codeunit 50100 MyCodeunit { }')
print(tree.root_node.sexp())
```

### Node.js

```bash
npm install tree-sitter-al
```

### Pre-built binaries

Download from [GitHub Releases](https://github.com/SShadowS/tree-sitter-al/releases):

| File | Platform | Use case |
|------|----------|----------|
| `tree-sitter-al.wasm` | All | web-tree-sitter |
| `tree-sitter-al.so` | Linux x86_64 | ast-grep, native bindings |
| `tree-sitter-al.dll` | Windows x86_64 | ast-grep, native bindings |
| `tree-sitter-al.dylib` | macOS ARM64 | ast-grep, native bindings |

## V2 Architecture

The grammar was rewritten from scratch in March 2026, achieving a **10x reduction in parser size** while improving correctness.

### Before / After

| Metric | V1 | V2 |
|--------|-----|-----|
| parser.c | 106 MB (can't push to GitHub) | **10.6 MB** |
| Errors | 14 | **7** |
| Success rate | 99.91% | **99.95%** |
| Symbols | 2,249 | **724** |
| States | 29,126 | **5,179** |
| grammar.js | 8,500 lines | **~3,000 lines** |
| Tests | 1,225 | **1,404** |
| Keywords | invisible in queries | **80 named nodes** |
| Query files | 3 (partial) | **5 (comprehensive)** |

### Key design decisions

- **Scanner-based property disambiguation** — One `PROPERTY_NAME` scanner token replaces 291 individual property rules. The scanner checks if `identifier` is followed by `=` (not `:=`) with a single-character lookahead.
- **Parse structure, don't validate** — Accept any `Name = Value ;` as a property. Semantic validation belongs in linters/LSP servers, not the parser.
- **Generic preprocessor** — One `preproc_conditional` rule + ~12 dedicated rules for genuinely complex split constructs, replacing 63 specialized rules.
- **80 named keyword nodes** — All keywords except `begin`/`end` are named nodes, enabling proper syntax highlighting and code navigation queries.

See [docs/v2-blog-post-notes.md](docs/v2-blog-post-notes.md) for the full rewrite narrative.

## Development

### Prerequisites

- Node.js (v16+)
- tree-sitter CLI: `npm install -g tree-sitter-cli`

### Building

```bash
tree-sitter generate    # Generate parser from grammar.js
tree-sitter test        # Run test suite
```

### Validation

```bash
./validate-grammar.sh        # Quick: generation, tests, orphan/duplicate detection
./validate-grammar.sh --full # Full: includes production AL file parsing
```

### Parsing AL files

```bash
tree-sitter parse path/to/file.al
tree-sitter parse path/to/file.al -d    # Debug output
tree-sitter parse path/to/file.al -q    # Quiet (errors only)
```

### Key files

| File | Purpose |
|------|---------|
| `grammar.js` | Main grammar definition |
| `src/scanner.c` | External scanner (property disambiguation, preprocessor) |
| `test/corpus/` | Test suite (1,404 tests) |
| `queries/` | Syntax highlighting, code navigation, folding, indentation |

## Contributing

See [CLAUDE.md](CLAUDE.md) for detailed development guidelines including architecture, debugging, and conventions.

---

**Author**: Torben Leth (sshadows@sshadows.dk)
**License**: MIT (see [LICENSE](LICENSE))
