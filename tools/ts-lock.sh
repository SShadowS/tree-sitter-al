#!/bin/bash
#
# ts-lock.sh — serialise anything that touches the shared compiled parser.
#
#   ./tools/ts-lock.sh tree-sitter test
#   ./tools/ts-lock.sh ./validate-grammar.sh
#   ./tools/ts-lock.sh python -m tools.query_coverage.qc run --full-corpus --all
#
# WHY THIS EXISTS
#
# tree-sitter caches the compiled library by GRAMMAR NAME, not by path:
#
#     ~/AppData/Local/tree-sitter/lib/al.dll        (Windows)
#     ~/.cache/tree-sitter/lib/al.so                (Linux)
#
# `name: "al"` in grammar.js means EVERY checkout, worktree and scratch copy of
# this repo shares that one file. TREE_SITTER_DIR does not redirect it — tested,
# it moves the config directory only. So two agents running `tree-sitter test`,
# `tree-sitter parse` or validate-grammar.sh at the same time, in different
# worktrees, silently overwrite each other's parser mid-run.
#
# This is not theoretical. In one day it produced:
#   * a phantom test failure in a clean tree (a reviewer's mutated scanner)
#   * a corrupted headline count in a review (1536 vs the real 1539)
#   * a stale build that made a PASS look real, which is the dangerous direction
#
# Neither run errors. Both print plausible numbers. That is what makes it worth
# a lock rather than a convention.
#
# WHAT THIS DOES AND DOES NOT GIVE YOU
#
# It serialises callers that opt in. It cannot stop a bare `tree-sitter test`
# run outside the lock, so it is a discipline aid, not an enforcement boundary.
# Wrap every build/test/parse you intend to QUOTE.
#
set -euo pipefail

if [ $# -eq 0 ]; then sed -n '2,12p' "$0"; exit 2; fi

LOCK_DIR="${TS_LOCK_DIR:-${TMPDIR:-/tmp}/tree-sitter-al.buildlock}"
TIMEOUT="${TS_LOCK_TIMEOUT:-3600}"   # seconds; a full-corpus qc run is ~31 min
STALE_AFTER="${TS_LOCK_STALE:-5400}" # a lock older than this is presumed dead

waited=0
while true; do
  # mkdir is atomic on every filesystem this repo is used on, including NTFS.
  if mkdir "$LOCK_DIR" 2>/dev/null; then
    break
  fi

  # Existing lock — is it alive?
  owner="$(cat "$LOCK_DIR/owner" 2>/dev/null || echo 'unknown')"
  started="$(cat "$LOCK_DIR/started" 2>/dev/null || echo 0)"
  now="$(date +%s)"
  age=$(( now - started ))

  if [ "$started" -gt 0 ] && [ "$age" -gt "$STALE_AFTER" ]; then
    echo "ts-lock: breaking a stale lock (${age}s old, held by ${owner})" >&2
    rm -rf "$LOCK_DIR"
    continue
  fi

  if [ "$waited" -eq 0 ]; then
    echo "ts-lock: waiting for the shared parser lock — held by ${owner}, ${age}s so far" >&2
    echo "ts-lock: (this is the one al.dll every worktree shares; concurrent builds corrupt it)" >&2
  elif [ $(( waited % 60 )) -eq 0 ]; then
    echo "ts-lock: still waiting (${waited}s), holder ${owner} has had it ${age}s" >&2
  fi

  if [ "$waited" -ge "$TIMEOUT" ]; then
    echo "ts-lock: TIMED OUT after ${TIMEOUT}s waiting for ${owner}." >&2
    echo "ts-lock: refusing to run rather than race the holder. Raise TS_LOCK_TIMEOUT," >&2
    echo "ts-lock: or remove $LOCK_DIR if you are certain nothing is running." >&2
    exit 75   # EX_TEMPFAIL
  fi

  sleep 2
  waited=$(( waited + 2 ))
done

printf '%s' "${TS_LOCK_OWNER:-$(whoami)@$(pwd)}" > "$LOCK_DIR/owner"
date +%s > "$LOCK_DIR/started"
trap 'rm -rf "$LOCK_DIR"' EXIT INT TERM

[ "$waited" -gt 0 ] && echo "ts-lock: acquired after ${waited}s" >&2

# The whole point: whoever last held the lock may have left a library built from
# a different tree. Force a rebuild from THIS checkout before running.
touch src/scanner.c src/parser.c 2>/dev/null || true

"$@"
