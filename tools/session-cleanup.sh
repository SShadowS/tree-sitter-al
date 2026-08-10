#!/bin/bash
#
# session-cleanup.sh — remove the disposable artifacts an agent session leaves behind.
#
# DRY RUN BY DEFAULT. Nothing is deleted unless you pass --yes.
#
#   ./tools/session-cleanup.sh              # show what would go, delete nothing
#   ./tools/session-cleanup.sh --yes        # actually delete
#   ./tools/session-cleanup.sh --yes --keep-snapshots 4
#   ./tools/session-cleanup.sh --yes --all-snapshots     # delete every baseline
#
# Design notes, because this script deletes things:
#
#   * It refuses to run if tracked files are modified. Uncommitted work and bulk
#     deletion do not belong in the same minute.
#   * It never deletes a tracked file. Every candidate is checked against
#     `git ls-files` and skipped if tracked, regardless of what the lists below say.
#   * .cache/ is NOT wiped wholesale. `.cache/tree-sitter-<version>/` is the vendored
#     runtime that validate-grammar.sh Step 5c compiles tools/fieldwalk.c against;
#     removing it downgrades that step to a warning that still exits 0. That is the
#     failure mode this repo has spent a release eliminating, so the runtime is on an
#     explicit keep-list and everything else under .cache/ is scratch.
#   * It reports what it examined, not just what it removed. A cleanup that finds
#     nothing and a cleanup that silently skipped everything must not look alike.
#
set -euo pipefail

cd "$(dirname "$0")/.."
REPO="$(pwd)"

DRY=1
KEEP_SNAPSHOTS=2
ALL_SNAPSHOTS=0

while [ $# -gt 0 ]; do
  case "$1" in
    --yes|-y)            DRY=0 ;;
    --keep-snapshots)    KEEP_SNAPSHOTS="${2:?--keep-snapshots needs a number}"; shift ;;
    --all-snapshots)     ALL_SNAPSHOTS=1 ;;
    -h|--help)           sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done

case "$KEEP_SNAPSHOTS" in
  ''|*[!0-9]*) echo "--keep-snapshots must be a non-negative integer" >&2; exit 2 ;;
esac

# --- refuse to run over uncommitted work -------------------------------------
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "not a git repository: $REPO" >&2; exit 2
fi
DIRTY="$(git status --porcelain --untracked-files=no)"
if [ -n "$DIRTY" ]; then
  echo "REFUSING TO RUN — tracked files are modified:"
  echo "$DIRTY"
  echo
  echo "Commit or stash first. This script deletes things; it will not do that"
  echo "while there is uncommitted work to confuse the picture."
  exit 1
fi

# Tracked-file index, so nothing tracked is ever a candidate.
TRACKED="$(mktemp)"; trap 'rm -f "$TRACKED"' EXIT
git ls-files > "$TRACKED"

examined=0; removed=0; skipped_tracked=0; absent=0
freed_kb=0

is_tracked() { grep -qxF "$1" "$TRACKED"; }

size_kb() { du -sk "$1" 2>/dev/null | cut -f1 || echo 0; }

drop() {  # drop <path> <reason>
  local p="$1" why="$2" kb
  examined=$((examined + 1))
  if [ ! -e "$p" ]; then absent=$((absent + 1)); return 0; fi
  if is_tracked "$p"; then
    printf '  SKIP (tracked)  %-46s %s\n' "$p" "$why"
    skipped_tracked=$((skipped_tracked + 1))
    return 0
  fi
  kb="$(size_kb "$p")"
  if [ "$DRY" -eq 1 ]; then
    printf '  would remove    %-46s %6s MB  %s\n' "$p" "$((kb / 1024))" "$why"
  else
    rm -rf -- "$p"
    if [ -e "$p" ]; then echo "  FAILED to remove $p" >&2; exit 1; fi
    printf '  removed         %-46s %6s MB  %s\n' "$p" "$((kb / 1024))" "$why"
  fi
  removed=$((removed + 1)); freed_kb=$((freed_kb + kb))
}

echo "session-cleanup — $REPO"
[ "$DRY" -eq 1 ] && echo "DRY RUN. Nothing will be deleted. Pass --yes to act." || echo "DELETING."
echo

# --- 1. generated reports and caches -----------------------------------------
echo "generated / regenerable:"
drop "grammar_analysis.json"                "rewritten by validate-grammar.sh Step 4"
drop "tools/query_coverage/reports"         "rewritten by every qc run"
drop "log.html"                             "tree-sitter test -D output"
drop "tools/__pycache__"                    "python bytecode"
drop "tools/query_coverage/__pycache__"     "python bytecode"
drop "tools/query_coverage/tests/__pycache__" "python bytecode"

# --- 2. agent scratch under .cache/, preserving the vendored runtime ----------
echo
echo ".cache/ scratch (the vendored tree-sitter runtime is KEPT — Step 5c needs it):"
if [ -d .cache ]; then
  kept_runtime=0
  for entry in .cache/*; do
    [ -e "$entry" ] || continue
    case "$(basename "$entry")" in
      tree-sitter-*)
        printf '  KEEP            %-46s validate-grammar.sh Step 5c compiles against this\n' "$entry"
        kept_runtime=1
        ;;
      *) drop "$entry" "session scratch" ;;
    esac
  done
  if [ "$kept_runtime" -eq 0 ]; then
    echo "  NOTE: no .cache/tree-sitter-*/ runtime present. Step 5c is currently"
    echo "        skipping with a warning. Run bindings/c/build.sh once to fetch it."
  fi
else
  echo "  .cache/ absent"
fi

# --- 3. one-off analysis dumps ------------------------------------------------
echo
echo "analysis dumps:"
for f in error_files.txt benchmark-results.txt wasm-build-results.txt \
         do_support_parse_errors.txt do_support_error_clusters.txt \
         parse_errors.txt debug.log queries/bad_delete.scm.v1; do
  drop "$f" "one-off output"
done

# --- 4. tree-harness baselines ------------------------------------------------
echo
echo "tree-harness baselines (~154 MB each):"
if [ -d .snapshots ]; then
  # newest first by mtime
  mapfile -t SNAPS < <(ls -1dt .snapshots/*/ 2>/dev/null | sed 's:/*$::')
  total="${#SNAPS[@]}"
  if [ "$total" -eq 0 ]; then
    echo "  none present"
  elif [ "$ALL_SNAPSHOTS" -eq 1 ]; then
    for s in "${SNAPS[@]}"; do drop "$s" "--all-snapshots"; done
  else
    idx=0
    for s in "${SNAPS[@]}"; do
      if [ "$idx" -lt "$KEEP_SNAPSHOTS" ]; then
        printf '  KEEP            %-46s newest %s\n' "$s" "$((idx + 1))"
      else
        drop "$s" "older than the newest $KEEP_SNAPSHOTS"
      fi
      idx=$((idx + 1))
    done
  fi
  echo "  ($total present, keeping $([ "$ALL_SNAPSHOTS" -eq 1 ] && echo 0 || echo "$KEEP_SNAPSHOTS"))"
else
  echo "  .snapshots/ absent"
fi

# --- summary ------------------------------------------------------------------
echo
echo "-----------------------------------------------------------------"
printf 'examined %d candidates: %d actioned, %d already absent, %d skipped as tracked\n' \
  "$examined" "$removed" "$absent" "$skipped_tracked"
printf '%s %d MB\n' "$([ "$DRY" -eq 1 ] && echo 'would free' || echo 'freed')" "$((freed_kb / 1024))"
if [ "$skipped_tracked" -gt 0 ]; then
  echo
  echo "NOTE: $skipped_tracked candidate(s) are tracked in git and were left alone."
  echo "      That is a bug in this script's lists, not in your working copy —"
  echo "      a tracked file should never have been a candidate. Please report it."
fi
[ "$DRY" -eq 1 ] && echo && echo "Nothing was deleted. Re-run with --yes to act."
exit 0
