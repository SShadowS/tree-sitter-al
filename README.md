# tree-sitter-al

A [tree-sitter](https://tree-sitter.github.io/tree-sitter/) parser for the AL programming language used in Microsoft Dynamics 365 Business Central.

[![PyPI](https://img.shields.io/pypi/v/tree-sitter-al)](https://pypi.org/project/tree-sitter-al/)
[![crates.io](https://img.shields.io/crates/v/tree-sitter-al)](https://crates.io/crates/tree-sitter-al)
[![npm](https://img.shields.io/npm/v/tree-sitter-al)](https://www.npmjs.com/package/tree-sitter-al)

## Parser Status

Validated against **15,358 production AL files** from the Business Central codebase:

| Metric | Value |
|--------|-------|
| **Success rate** | **100%** (15,358 / 15,358 files) |
| Tests | 1,514 |
| parser.c size | ~26 MB |
| grammar.js | ~4,121 lines |
| Named keywords | 83 (81 grammar rules + 2 external; queryable via highlights/tags) |
| Scanner tokens | 9 (stateful, depth-tracking) |
| Query files | 6 (highlights, locals, tags, indents, folds, textobjects) |

## What's new in 3.0.0

**Breaking parse-tree change for editor textobjects and code navigation.** Every
scoped construct now exposes its content as a single node via a `body` field
(e.g. `(page_declaration body: (declaration_body …))`,
`(code_block (begin_keyword) body: (statement_block …) (end_keyword))`), instead of a
flat list of direct children. This powers Helix / nvim-treesitter textobjects
(`@class.inside`, `@function.inside`, `@parameter`) via the new
[`queries/textobjects.scm`](queries/textobjects.scm), plus a `parameters` field on
procedures/triggers/events.

Tree-walkers and structural queries must descend through the `body` field — see
[CHANGELOG.md](CHANGELOG.md) for the full migration guide.

## Installation

### Rust

```bash
cargo add tree-sitter-al
```

```rust
use tree_sitter::Parser;

let mut parser = Parser::new();
let language = tree_sitter_al::LANGUAGE;
parser.set_language(&language.into()).expect("Error loading AL grammar");
let tree = parser.parse("codeunit 50100 MyCodeunit { }", None).unwrap();
println!("{}", tree.root_node().to_sexp());
```

Query constants are also available:
```rust
use tree_sitter_al::{HIGHLIGHTS_QUERY, TAGS_QUERY, LOCALS_QUERY, FOLDS_QUERY, INDENTS_QUERY, TEXTOBJECTS_QUERY};
```

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

The grammar was rewritten from scratch in March 2026, achieving a **major reduction in parser size** while improving correctness.

### Before / After

| Metric | V1 | V2 (current) |
|--------|-----|-----|
| parser.c | 106 MB (can't push to GitHub) | **~26 MB** |
| Errors | 14 | **0** |
| Success rate | 99.91% | **100%** |
| Symbols | 2,249 | **~846** |
| States | 29,126 | **~12,545** |
| grammar.js | 8,500 lines | **~4,121 lines** |
| Tests | 1,225 | **1,514** |
| Keywords | invisible in queries | **83 named nodes** |
| Query files | 3 (partial) | **6 (comprehensive)** |

### Key design decisions

- **Stateful external scanner** — 9 scanner tokens handle property disambiguation, depth tracking (`#if`/`#endif` nesting), named `begin`/`end` keywords at every depth, and split-construct detection via lookahead.
- **Parse structure, don't validate** — Accept any `Name = Value ;` as a property. Semantic validation belongs in linters/LSP servers, not the parser.
- **Generic preprocessor** — One `preproc_conditional` rule + 20 dedicated rules for genuinely complex split constructs (begin/end, var/begin, brace-close across `#if`/`#else` branches).
- **83 named keyword nodes** — All keywords including `begin`/`end` are named nodes, enabling proper syntax highlighting and code navigation queries. Every grammar keyword rule has a uniform shape: one anonymous child typed as the canonical lowercase spelling, whatever the source casing.

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

For grammar refactors, the parse-tree diff harness proves a change is zero-behavior-change by re-parsing every production file and asserting byte-identical trees:

```bash
./tools/tree-harness.sh snapshot ./BC.History .snapshots/bc   # baseline
./tools/tree-harness.sh verify   ./BC.History .snapshots/bc   # verify after a change
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
| `src/scanner.c` | External scanner (9 tokens: property, depth tracking, named begin/end, split detection) |
| `test/corpus/` | Test suite (1,514 tests) |
| `queries/` | Syntax highlighting, code navigation, folding, indentation, textobjects |

## Contributing

See [CLAUDE.md](CLAUDE.md) for detailed development guidelines including architecture, debugging, and conventions.

---

**Author**: Torben Leth (sshadows@sshadows.dk)
**License**: MIT (see [LICENSE](LICENSE))
