# tree-sitter-al

A [tree-sitter](https://tree-sitter.github.io/tree-sitter/) parser for the AL programming language used in Microsoft Dynamics 365 Business Central.

[![PyPI](https://img.shields.io/pypi/v/tree-sitter-al)](https://pypi.org/project/tree-sitter-al/)
[![crates.io](https://img.shields.io/crates/v/tree-sitter-al)](https://crates.io/crates/tree-sitter-al)
[![npm](https://img.shields.io/npm/v/tree-sitter-al)](https://www.npmjs.com/package/tree-sitter-al)

## Parser Status

Validated against **15,358 production AL files** from the Business Central codebase:

| Metric | Value |
|--------|-------|
| **Success rate** | **100%** (15,358 / 15,358 files, 0 errors) |
| Tests | 1,562 |
| parser.c size | ~32.3 MB |
| grammar.js | 4,552 lines |
| Named keywords | 110 (108 grammar rules + 2 external; queryable via highlights/tags) |
| Scanner tokens | 9 (stateful, depth-tracking) |
| Query files | 6 (highlights, locals, tags, indents, folds, textobjects) |

Since 4.0.0 the success rate is a count of files actually read, reconciled per chunk —
it used to be the total minus the files that reported an error, which counted a file
that was never opened as a pass. See the 4.0.0 notes.

## What's new in 4.0.0

**This is a breaking release — the parse tree moves.** The headline change is that the
statement terminator left `code_block` and the branch rules: a `begin … end;` now ends
at its `end`, and the `;` re-parents to whatever encloses the construct. That re-spans
74,268 `if_statement` nodes and every `begin … end;` in the corpus, without changing a
single node type, field or count. A consumer that expected the `;` inside a body or
branch's byte range must adjust.

Alongside it: a dangling `else` in a case branch now binds to the inner `if` (it bound
to the `case`, which meant the tree said the program did something it did not do); `begin`
and `end` inside a `#if` block are nodes instead of being dropped from the tree entirely;
the assignment operator and the `where()` markers are nodes, so `i := 1` no longer parses
identically to `i += 2` and `where(X = const(N))` no longer parses identically to
`where(X = field(N))`; and queries naming a non-lowercase keyword spelling (`"IF"`,
`"Then"`, `"AND"`) must drop it.

Eight of the nine defects fixed here were found by a new gate built during the release,
[`tools/query_coverage/`](tools/query_coverage/README.md) — none was visible to anything
the project had before, because the files parsed with zero `ERROR` nodes and the tree
hashes were stable.

See [CHANGELOG.md](CHANGELOG.md) for the full list, each with its measured blast radius.

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
| parser.c | 106 MB (can't push to GitHub) | **~32.3 MB** |
| Errors | 14 | **0** |
| Success rate | 99.91% | **100%** |
| Symbols | 2,249 | **889** |
| States | 29,126 | **13,927** |
| grammar.js | 8,500 lines | **4,552 lines** |
| Tests | 1,225 | **1,562** |
| Keywords | invisible in queries | **110 named nodes** |
| Query files | 3 (partial) | **6 (comprehensive)** |

### Key design decisions

- **Stateful external scanner** — 9 scanner tokens handle property disambiguation, depth tracking (`#if`/`#endif` nesting), named `begin`/`end` keywords at every depth, and split-construct detection via lookahead.
- **Parse structure, don't validate** — Accept any `Name = Value ;` as a property. Semantic validation belongs in linters/LSP servers, not the parser.
- **Generic preprocessor** — One `preproc_conditional` rule + 20 dedicated rules for genuinely complex split constructs (begin/end, var/begin, brace-close across `#if`/`#else` branches).
- **110 named keyword nodes** (108 grammar rules + 2 external scanner tokens) — All keywords including `begin`/`end` are named nodes, enabling proper syntax highlighting and code navigation queries. Every grammar keyword rule has a uniform shape: one anonymous child typed as the canonical lowercase spelling, whatever the source casing. Read a keyword's text from the node itself, never by descending into a child.

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

For grammar refactors, the parse-tree diff harness proves a change is zero-behavior-change by re-parsing every production file and asserting byte-identical trees. Take a **fresh** baseline before you change anything and name it for the change — verifying against a snapshot you did not just take reports a delta that has nothing to do with your edit:

```bash
./tools/tree-harness.sh snapshot ./BC.History .snapshots/baseline-<change>   # ~16s
./tools/tree-harness.sh verify   ./BC.History .snapshots/baseline-<change>   # ~11s
```

The query-coverage harness measures whether the tree is lossless over the source and whether values stay reachable through queries — the class of defect an error count cannot see, because a token that is lexed and then dropped changes no tree hash. It currently reports 3,895 byte gaps in 112 clusters, dominated by bare inline keywords (`record`, `field`, `code`); 4.0.0 fixed the ones that also took a declared field down with them, not the rest:

```bash
python -m tools.query_coverage.qc run     # regression gate, exits 1 on a new cluster
python -m tools.query_coverage.qc run --all   # full picture, always exits 0
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
| `test/corpus/` | Test suite (1,562 tests) |
| `queries/` | Syntax highlighting, code navigation, folding, indentation, textobjects |
| `tools/query_coverage/` | Query-coverage harness — measures CST losslessness and query reach |
| `tools/gate_selftest.py` | Mutation testing for the validation gates |

## Contributing

See [CLAUDE.md](CLAUDE.md) for detailed development guidelines including architecture, debugging, and conventions.

---

**Author**: Torben Leth (sshadows@sshadows.dk)
**License**: MIT (see [LICENSE](LICENSE))
