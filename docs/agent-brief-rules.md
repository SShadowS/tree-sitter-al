# Agent brief rules

Every subagent brief links here. Each rule is one the session transcripts show agents
breaking. **Use instead** is what to do.

## Blocked by the safety hook

- [ ] No `rm -rf $VAR`. **Use instead:** `rm -rf "${VAR:?}"`, and only inside the repo or the scratchpad.
- [ ] No `git checkout -- f`. **Use instead:** `git show HEAD:f > f`.
- [ ] No `git worktree remove --force`. **Use instead:** run it without `--force`, and report a refusal.
- [ ] No `git stash` or `git stash drop`, ever (used 41 times against this rule). **Use instead:** restore an untargeted file with `git show HEAD:path > path`.
- [ ] No `git reset`. **Use instead:** a new commit, or `git show HEAD:path > path` for one file.
- [ ] No `git branch -D`. **Use instead:** `git branch -d`.

## Processes

- [ ] No `find /`, and no search outside the repo, the scratchpad or a named directory: Git Bash `/` spans every drive, the corpora on `H:` included. **Use instead:** a named root, or `tools/corpus-grep.sh` for the four corpora.
- [ ] Do not search for tree-sitter's own source. **Use instead:** CLAUDE.md, "Where tree-sitter's own source lives".
- [ ] No waiting with `tail -f | grep | head`: the pipeline outlives you. **Use instead:** an `until` loop that tests for completion.
- [ ] Kill your own background processes before you finish. **Use instead of guessing:** `tools/session-cleanup.sh --procs` lists the leftovers.
- [ ] Never end a turn while your own background work runs. **Use instead:** wait for it, or kill it.
- [ ] From Git Bash, `kill` does not reach a Windows process. **Use instead:** `taskkill //PID n //F`.

## Environment

- [ ] Git Bash with Windows paths (`U:/Git/...`).
- [ ] Never `2>nul`: it creates an undeletable file. **Use instead:** `2>/dev/null`.
- [ ] Never run a bare `tree-sitter`. **Use instead:** `./tools/ts-lock.sh tree-sitter ...`.
- [ ] Do not wrap `python -m tools.perf ab` in ts-lock: it takes the lock itself.
- [ ] Do not write report files: they are blocked. **Use instead:** return the report as text.
- [ ] Do not dispatch subagents.
- [ ] Do not push.

## Editing

- [ ] No inline Python string replacement for an edit (used 997 times; it fails silently when the text does not match). **Use instead:** the Edit tool. For a bulk mechanical edit, a script file that asserts every match exists.

## The tools

- [ ] Do not write ad-hoc versions of these. **Use instead:**
  - `python tools/snip.py 'x := 1;'`: parse a snippet; fields, `has_error`, every ERROR/MISSING/hidden error; `--sexp` for a fixture; `--census --root DIR` for two-shape node types.
  - `./tools/metrics.sh [--vs REV]`: STATE_COUNT, LARGE_STATE_COUNT, SYMBOL_COUNT, parser.c size, grammar.js lines, test count, and the deltas.
  - `python tools/nodetypes.py show|who-has TYPE`, `diff REV`: node-types.json questions.
  - `./tools/corpus-grep.sh [-E|-P] [-i] [-l|-c] PATTERN`: sites over the four corpora.
- [ ] The gates are `tools/has_error_sweep.py`, `tools/tree-harness.sh`, `python -m tools.config_oracle`, `python -m tools.alc_probe` and `python -m tools.config_oracle.probe_alc`. Run the one your change needs; do not improvise a substitute.
