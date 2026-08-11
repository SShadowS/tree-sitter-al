# tree-sitter-al

A [tree-sitter](https://tree-sitter.github.io/tree-sitter/) parser for the AL programming language used in Microsoft Dynamics 365 Business Central.

[![PyPI](https://img.shields.io/pypi/v/tree-sitter-al)](https://pypi.org/project/tree-sitter-al/)
[![crates.io](https://img.shields.io/crates/v/tree-sitter-al)](https://crates.io/crates/tree-sitter-al)
[![npm](https://img.shields.io/npm/v/tree-sitter-al)](https://www.npmjs.com/package/tree-sitter-al)

## Parser Status

Validated against **36,001 production AL files** from two independent codebases —
15,358 from Business Central and 20,643 from a separate production estate:

| Metric | Value |
|--------|-------|
| **Success rate** | **100%** (36,001 / 36,001 files, 0 errors) |
| **Byte coverage** | **100%** — every source byte belongs to a node, both corpora |
| Tests | 1,615 |
| parser.c size | 30.9 MiB (32,445,756 bytes) |
| grammar.js | 5,303 lines |
| Named node types | 467 |
| Named keywords | 153 (151 grammar rules + 2 external; queryable via highlights/tags) |
| Scanner tokens | 9 (stateful, depth-tracking) |
| Query files | 6 (highlights, locals, tags, indents, folds, textobjects) |

Every figure above was measured on the released tree. Three different test counts
circulated during 4.0.0 development and two were arithmetic from a stale copy of
this table — re-measure, never recall. `parser.c` is quoted in MiB with the byte
count beside it because both conventions have been wrong here in opposite
directions.

**"0 errors" is the weakest claim on this page**, and 4.0.0 exists because the
project learned that the hard way. Every defect fixed in this release parsed with
zero `ERROR` nodes: 574,694 source bytes that belonged to no node, three inverted
operator precedence levels, a preprocessor condition that swallowed the following
line, an omitted list separator silently absorbed as an extra element. The byte
coverage row is the one that would have caught most of them, and the corpus row
would not have caught any.

Since 4.0.0 the success rate is a count of files actually read, reconciled per
chunk — it used to be the total minus the files that reported an error, which
counted a file that was never opened as a pass.

## What's new in 4.0.0

**This is a breaking release — the parse tree moves.** Every defect below parsed
with **zero `ERROR` nodes** before it was fixed. None was visible to anything the
project had: the corpus was green, the tree hashes were stable, the tests passed.

### The CST is now lossless

**574,694 source bytes belonged to no node.** They were lexed and thrown away —
unhighlightable, unmatchable by any query, invisible to every gate. Now 0, across
both corpora. Most were bare keyword tokens: `record`, `field`, `code`,
`tabledata` and 13 type/action keywords are nodes for the first time.

### Operator precedence was wrong in three places

AL is Pascal-derived, so `and`/`or`/`xor` bind **tighter** than comparison — the
inverse of what the grammar declared. `b := 1 = 1 and 2 = 2` was grouped
`(1=1) and (2=2)`; alc's own error message proves it is `1 = (1 and 2) = 2`.
Unary bound too tightly: `-a * b` was `-(a * b)`, wrong at **629 sites in 193
files**. And `..` was an expression operator, which it is not.

Each is pinned by a fixture carrying the `alc` probe that established it; the full
ladder is in [`docs/al-operator-precedence.md`](docs/al-operator-precedence.md)
with 196 probe cases.

### The statement terminator moved

A `begin … end;` now ends at its `end`; the `;` re-parents to whatever encloses
the construct. That re-spans **402,192 nodes** without changing a single node
type, field or count. A consumer that expected the `;` inside a body or branch's
byte range must adjust.

### Preprocessor directives are line-scoped

`#if FOO` followed by a line beginning ` and b` produced
`condition: (preproc_and_expression FOO b)`. The source condition is `FOO`, so
every consumer evaluating that directive computed the **wrong value**. Conditions
now stop at end of line, and an expression continued across a `#if` boundary stays
attached to its host in nine positions.

### One node type, one shape

`object_type_keyword` shipped childless for `DATABASE::` (22,988 nodes) and with a
child for its five siblings. A variable named `Table` was captured as both
`@variable.parameter` and `@keyword.type`, **2,151 times**. Identifier
classification disagreed between scanner and grammar *per platform*, and the
identifier class rejected five kinds of valid AL.

### Queries reach everything

**33,051 uncaptured-keyword findings → 0** across 28 node types. `"<>" @operator`
now matches: operators were wrapped, and a wrapper capture does not capture the
token inside it, so the obvious consumer pattern silently matched nothing.

### Also

`interface_declaration.access_value` removed (alc rejects it, 0 corpus
occurrences); `Access = Public;` no longer degrades to a bare `identifier`; an
omitted list separator is an error instead of being absorbed as an extra element,
which deleted three declared GLR conflicts; the Swift and Go bindings never linked
the external scanner and now do; CMake silently rewrote the committed `parser.c`
to ABI 14 on every build.

Found by gates built during this release —
[`tools/query_coverage/`](tools/query_coverage/README.md), a corpus-wide
`(parent, field, child)` edge census, and
[`tools/validate_al_file.py`](tools/validate_al_file.py), which answers
completeness and soundness separately for one file.

**Known limitation.** An expression continued across a `#if` boundary in four
shapes — after a grammatically complete construct, a second split in one
expression, an `else` clause under a flag, and an `and`/comparison continuation —
still parses to a wrong tree with no error. The class occurs in neither corpus
(0 of 36,001 files). It is recorded at the rule in `grammar.js` with every
measured attempt, and detected by `orphan-operator-expr` in the per-file
validator.

See [CHANGELOG.md](CHANGELOG.md) for the full list, each with its measured blast
radius.

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
| parser.c | 106 MB (can't push to GitHub) | **30.9 MiB** |
| Errors | 14 | **0** |
| Success rate | 99.91% | **100%** |
| Symbols | 2,249 | **954** |
| States | 29,126 | **14,442** |
| grammar.js | 8,500 lines | **5,303 lines** |
| Tests | 1,225 | **1,615** |
| Keywords | invisible in queries | **153 named nodes** |
| Query files | 3 (partial) | **6 (comprehensive)** |

### Key design decisions

- **Stateful external scanner** — 9 scanner tokens handle property disambiguation, depth tracking (`#if`/`#endif` nesting), named `begin`/`end` keywords at every depth, and split-construct detection via lookahead.
- **Parse structure, don't validate** — Accept any `Name = Value ;` as a property. Semantic validation belongs in linters/LSP servers, not the parser.
- **Generic preprocessor** — One `preproc_conditional` rule + 20 dedicated rules for genuinely complex split constructs (begin/end, var/begin, brace-close across `#if`/`#else` branches).
- **153 named keyword nodes** (151 grammar rules + 2 external scanner tokens) — All keywords including `begin`/`end` are named nodes, enabling proper syntax highlighting and code navigation queries. Every grammar keyword rule has a uniform shape: one anonymous child typed as the canonical lowercase spelling, whatever the source casing. Read a keyword's text from the node itself, never by descending into a child.

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

The query-coverage harness measures whether the tree is lossless over the source and whether values stay reachable through queries — the class of defect an error count cannot see, because a token that is lexed and then dropped changes no tree hash. It reports **0 byte gaps in 0 clusters** over the full 15,358-file corpus, down from 574,694 in 164 during 4.0.0 — every keyword that was lexed and dropped now has a node. `baseline.json` is the 59-file manifest scope the gate runs against, not the corpus; both read zero, but the distinction still applies to the other detectors:

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
| `test/corpus/` | Test suite (1,615 tests) |
| `queries/` | Syntax highlighting, code navigation, folding, indentation, textobjects |
| `tools/query_coverage/` | Query-coverage harness — measures CST losslessness and query reach |
| `tools/gate_selftest.py` | Mutation testing for the validation gates |

## Contributing

See [CLAUDE.md](CLAUDE.md) for detailed development guidelines including architecture, debugging, and conventions.

---

**Author**: Torben Leth (sshadows@sshadows.dk)
**License**: MIT (see [LICENSE](LICENSE))
