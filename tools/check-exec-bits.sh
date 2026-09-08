#!/usr/bin/env sh
#
# Every tracked shell script, and every gate-fixture `tree-sitter` shim, must be
# mode 100755 in the git INDEX.
#
# WHY THIS EXISTS. This repository is developed on Windows with
# core.fileMode=false, so the mode a file carries in the index is invisible in
# the working tree and `git status` never mentions it. It matters on Linux,
# which is where CI runs: a 100644 script that another script execs directly
# (`./parse-al-parallel.sh`, `"$HERE/../ts-lock.sh"`) fails there with
# "Permission denied" (exit 126), and a 100644 shim placed on PATH is simply not
# found, so the real binary runs and the fixture injects nothing.
#
# That is what kept the gate self-test job red on every CI run from the day it
# was added: parse-al-parallel.sh, tools/ts-lock.sh, ts-lock-release-guard.sh
# and json-offsetting-loss/tree-sitter were all 100644, all five failing cases
# traced to those four files, and none of it reproduced on the machine the code
# was written on. tools/check-wasm-fresh.sh had already hit the same wall once
# (bed960a, "failed at exit 126, having never run") and was fixed alone.
#
# This reads the index, not the filesystem, so it gives the same answer on
# every platform. Fix an offender with:  git update-index --chmod=+x <file>
#
# Usage:
#   tools/check-exec-bits.sh      exit 0 all good; exit 1 offenders listed;
#                                 exit 2 not a git checkout
set -eu
cd "$(dirname "$0")/.."
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "check-exec-bits: not a git checkout -- nothing to read the modes from" >&2
  exit 2
fi
# git pathspec `*` crosses directory boundaries, so '*.sh' is every tracked
# script at any depth. The shim pattern is spelled out because those files have
# no extension.
listed=$(git ls-files -s -- '*.sh' 'tools/gate-fixtures/*/tree-sitter')
total=$(printf '%s\n' "$listed" | grep -c . || true)
if [ "$total" -eq 0 ]; then
  echo "check-exec-bits: matched 0 tracked scripts -- the pathspec cannot be right" >&2
  exit 1
fi
bad=$(printf '%s\n' "$listed" | awk '$1 != "100755" { print $1 "  " $4 }')
if [ -n "$bad" ]; then
  echo "check-exec-bits: FAIL - $(printf '%s\n' "$bad" | grep -c .) of $total tracked script(s) lack the executable bit in the index:"
  printf '%s\n' "$bad" | sed 's/^/  /'
  echo "check-exec-bits: fix with  git update-index --chmod=+x <file>  and commit; the working tree on Windows will not show the change"
  exit 1
fi
echo "check-exec-bits: OK - all $total tracked script(s) are 100755 in the index"
exit 0
