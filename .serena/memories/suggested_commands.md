# Commands

Shell is **Git Bash on Windows with Windows paths**. Never `2>nul` — it creates
undeletable files. Use `2>/dev/null`.

## The shared-parser lock — read this before running anything

tree-sitter caches the compiled library **by grammar name**, not by path:
`~/AppData/Local/tree-sitter/lib/al.dll`. `name: "al"` means every checkout, worktree
and scratch copy shares that one file, and `TREE_SITTER_DIR` does **not** redirect it
(tested — it moves the config directory only). Two concurrent `tree-sitter
test`/`parse`/`build` runs in different worktrees silently overwrite each other's
parser. Neither errors; both print plausible numbers.

Wrap every build/test/parse whose result you intend to quote:

```bash
./tools/ts-lock.sh tree-sitter test
./tools/ts-lock.sh ./validate-grammar.sh
./tools/ts-lock.sh ./parse-al-parallel.sh ./BC.History/ .
```

It is opt-in, so it is a discipline aid, not an enforcement boundary. Known hazard: an
agent harness that kills a command on timeout defeats the EXIT trap, so the lock
survives its owner for the full stale window (default 5400s) and later invocations pile
up as waiters.

Anything that **statically links** the parser needs no lock — `tools/fieldwalk.c`, the
edge-census binary, plain `gcc` builds, and every `alc` probe.

## Core cycle

```bash
tree-sitter generate                              # after any grammar.js change
tree-sitter test                                  # -i / -e to filter, --file-name for one file
tree-sitter test -u                               # see mem:verification_traps first
tree-sitter parse file.al -d > debug.log 2>&1
python parse_bug_finder.py file.al debug.log
tree-sitter generate --report-states-for-rule -   # rank rules by parser-state cost
```

## Gates

```bash
./validate-grammar.sh          # generation, tests, orphan/duplicate detection, qc
./validate-grammar.sh --full   # adds production AL parsing
./parse-al-parallel.sh ./BC.History/ .          # 15,358 files, the real gate
python -m pytest tools/query_coverage/tests -q  # NOT run by validate-grammar.sh
python tools/gate_selftest.py                   # mutation-tests the gates themselves
python -m tools.query_coverage.qc run           # see mem:query_coverage
```

## Zero-behaviour-change proof for refactors

```bash
./tools/tree-harness.sh snapshot ./BC.History .snapshots/baseline-<change>   # ~16s
./tools/tree-harness.sh verify   ./BC.History .snapshots/baseline-<change>   # ~11s
```

Take the baseline **fresh and named for the change**. A stale snapshot reports a huge
delta unrelated to your edit; one left for two months had 15,349 of 15,358 rows drifted.

## Other

- `tools/session-cleanup.sh` — dry-run by default; refuses on a dirty tree, never
  deletes tracked files, keeps `.cache/tree-sitter-*/`.
- `tools/precedence/probe.sh` — the alc precedence rig; runs four controls first and
  refuses to continue if they fail, because a rig with missing symbols rejects
  everything while emitting no diagnostics.
- `docs/al-operator-precedence.md` — the measured operator ladder, alc-version stamped.
