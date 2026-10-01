# Agent brief rules

Every subagent brief links here. Each rule is one the session transcripts show agents
breaking. **Use instead** is what to do.

## Blocked by the safety hook

These are refused outright (checked with `cc-safety-net explain`). Do not retry them in
another form.

- [ ] `git checkout -- f` and `git checkout HEAD -- f`. **Use instead:** `git show HEAD:f > f`.
- [ ] `git restore f`. **Use instead:** `git show HEAD:f > f`.
- [ ] `git clean -f`. **Use instead:** delete the named untracked files with `rm`, or `tools/session-cleanup.sh`.
- [ ] `git stash drop`. **Use instead:** nothing: only the user drops a stash (`! git stash drop`).
- [ ] `git worktree remove --force`. **Use instead:** run it without `--force`, and report a refusal.
- [ ] `git branch -D`. **Use instead:** `git branch -d`.
- [ ] `git reset --hard`. **Use instead:** a new commit, or `git show HEAD:path > path` for one file.
- [ ] `rm -rf` on an absolute path outside the working directory. **Use instead:** a path inside the repo or the scratchpad.

## Project rules

The hook does not stop these. Follow them anyway.

### Git and files

- [ ] No `git stash`. Do not use it to park the untargeted files a `tree-sitter test -u` rewrote (CLAUDE.md, trap 5). **Use instead:** `git show HEAD:path > path` for each one. The hook's block message suggests "git stash first": ignore it. A stash can only be dropped by the user (`! git stash drop`), so every stash you make is left for them.
- [ ] No `git reset --hard`, and no reset that moves HEAD. `git reset HEAD <file>` to unstage is fine.
- [ ] No `rm -rf $VAR`. **Use instead:** `rm -rf "${VAR:?}"`, and only inside the repo or the scratchpad.
- [ ] Do not push.

### Processes

- [ ] No `find /`, and no search outside the repo, the scratchpad or a named directory: Git Bash `/` spans every drive, the corpora on `H:` included. **Use instead:** a named root, or `tools/corpus-grep.sh` for the four corpora.
- [ ] Do not search for tree-sitter's own source. **Use instead:** CLAUDE.md, "Where tree-sitter's own source lives".
- [ ] No waiting with `tail -f | grep | head`: the pipeline outlives you. **Use instead:** an `until` loop that tests for completion.
- [ ] Kill your own background processes before you finish. `tools/session-cleanup.sh --procs` lists leftovers.
- [ ] Never end a turn while your own background work runs. **Use instead:** wait for it, or kill it.
- [ ] From Git Bash, `kill` does not reach a Windows process. **Use instead:** `taskkill //PID n //F`.

### Environment

- [ ] Git Bash with Windows paths (`U:/Git/...`).
- [ ] Never `2>nul`: it creates an undeletable file. **Use instead:** `2>/dev/null`.
- [ ] Never run a bare `tree-sitter`. **Use instead:** `./tools/ts-lock.sh tree-sitter ...`.
- [ ] Do not wrap `python -m tools.perf ab` in ts-lock: it takes the lock itself.
- [ ] Do not write report files: they are blocked. **Use instead:** return the report as text.
- [ ] Do not dispatch subagents.

### Editing

- [ ] No inline Python string replacement for an edit (used 997 times; it fails silently when the text does not match). **Use instead:** the Edit tool. For a bulk mechanical edit, a script file that asserts every match exists.

### The tools

- [ ] Do not write ad-hoc versions of these. **Use instead:**
  - `python tools/snip.py 'x := 1;'`: parse a snippet; fields, `has_error`, every ERROR/MISSING/hidden error; `--sexp` for a fixture; `--census --root DIR` for two-shape node types.
  - `./tools/metrics.sh [--vs REV]`: STATE_COUNT, LARGE_STATE_COUNT, SYMBOL_COUNT, parser.c size, grammar.js lines, test count, and the deltas.
  - `python tools/nodetypes.py show|who-has TYPE`, `diff REV`: node-types.json questions.
  - `./tools/corpus-grep.sh [-E|-P] [-i] [-l|-c] PATTERN`: sites over the four corpora.
- [ ] The gates are `tools/has_error_sweep.py`, `tools/tree-harness.sh`, `python -m tools.config_oracle`, `python -m tools.alc_probe` and `python -m tools.config_oracle.probe_alc`. Run the one your change needs; do not improvise a substitute.
