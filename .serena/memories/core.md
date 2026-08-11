# tree-sitter-al — core

Tree-sitter grammar for AL (Microsoft Dynamics 365 Business Central).

**`CLAUDE.md` at the repo root is the authoritative project document** and is loaded
into every session automatically. `.claude/rules/*.md` (attributes, contextual-keywords,
debugging, scanner, test-failures) extend it. Do not duplicate their content into these
memories — these cover what those files do *not*.

Prime directive: parse AL **correctly**, not merely without errors. A tree with zero
ERROR nodes can still be completely wrong; most defects found in 4.0.0 looked exactly
like that.

## Source map

| path | role |
|---|---|
| `grammar.js` | the grammar (~4.5k lines). Never edit `src/parser.c` |
| `src/scanner.c` | external scanner: property/variable disambiguation, `#if` depth, `begin`/`end` |
| `src/unicode_id.h` | generated identifier range tables; regenerate with `tools/gen-unicode-id-table.py` |
| `test/corpus/*.txt` | ~570 files of AL + expected trees |
| `queries/*.scm` | 6 query files (highlights, locals, tags, indents, folds, textobjects) |
| `tools/query_coverage/` | the qc harness — see `mem:query_coverage` |
| `tools/` | gates and instruments — see `mem:suggested_commands` |
| `BC.History/` | 15,358 production AL files, gitignored, the real validation gate |

`src/parser.c`, `src/grammar.json`, `src/node-types.json` are all generated and all
tracked. Stage them as a set or `grammar.json` silently drifts.

## Project-wide invariants

- **A generated artifact can never fail a contract**, because it is re-derived from the
  thing being tested. `src/node-types.json` says what the grammar *does*;
  `tools/check-field-types.py` is hand-maintained and is the only thing that says what
  the grammar is *supposed* to do. Verifying a field shape in `node-types.json` is
  necessary and not sufficient.
- **Parse structure, don't validate.** Accepting input alc rejects is a deliberate
  choice; narrowing the grammar to reproduce a compiler error is not a fix.
- **`alc` is ground truth** for any question about what AL accepts — never LLM recall,
  never web search. Probe recipe and its four silent-failure traps are in `CLAUDE.md`.
- Every gate must be able to *fail*. See `mem:verification_traps` — this is the single
  highest-value memory in the project.

## Further memories

- `mem:tech_stack` — toolchain and version pins
- `mem:suggested_commands` — what to run, and the shared-parser lock that serialises it
- `mem:conventions` — grammar/scanner idioms specific to this codebase
- `mem:task_completion` — the gate sequence before calling anything done
- `mem:verification_traps` — checks in this repo that have passed while wrong
- `mem:query_coverage` — the qc harness: scopes, detectors, baseline semantics
