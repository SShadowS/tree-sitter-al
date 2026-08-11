# Tech stack

- **Grammar**: tree-sitter, `grammar.js` (JS DSL). CLI vendored under `.cache/tree-sitter-*`.
- **Scanner**: C11, `src/scanner.c` + generated `src/unicode_id.h`. No `<wctype.h>` —
  `iswalpha`/`iswalnum` were replaced by explicit Unicode range tables because their
  behaviour is locale- and platform-dependent and disagreed with the grammar per platform.
- **Regex**: `new RustRegex(...)` for anything beyond a plain JS literal. Rust regex
  supports **no zero-width assertions** — `\b` and lookahead make `tree-sitter generate`
  fail with `Unexpected rule ExpandRegex(Assertion)`. Use negated character classes for
  word boundaries.
- **Harness/tooling**: Python 3.13 (`tools/query_coverage/`, requirements.txt), pytest.
- **Bindings**: node (`binding.gyp`), Rust (`bindings/rust/build.rs`, `Cargo.toml`),
  Python (`setup.py`), C (`bindings/c/build.sh`), CMake, Swift (`Package.swift`), Go
  (`bindings/go/binding.go`), plus a `Makefile` using `wildcard src/*.c`.
  **Every source list must name `src/scanner.c`.** Swift and Go both shipped for a long
  time carrying the tree-sitter template's unedited placeholder comment and therefore
  could not link the five `tree_sitter_al_external_scanner_*` symbols.
  `go build` on a library package compiles without linking, so it passes while broken.
- **Ground truth for AL syntax**: `al compile` CLI (alc). Version at time of the 4.0.0
  measurements: 18.0.37.11445, BC 28.0.46665.47126 symbols.

## Version-sensitive facts

- Parser ABI: the committed `src/parser.c` is `LANGUAGE_VERSION 15`. `CMakeLists.txt`
  once pinned `--abi=14` *and* regenerated into the source tree, so building with CMake
  silently downgraded a tracked file.
- npm publishing needs npm >= 11.5.1 for trusted publishing; with an older npm the CLI
  silently falls back to token auth.
- The `#if` depth counter in the scanner is `uint32_t` with a `_Static_assert`. It was
  `uint8_t` and wrapped at 256 open blocks.
