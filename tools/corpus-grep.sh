#!/bin/bash
#
# corpus-grep.sh — count a pattern's sites over the four production corpora, *.al only.
#
#   ./tools/corpus-grep.sh [-E|-P] [-i] [-l|-c] PATTERN
#
#   (default)  every matching line (path:line:text), then per-corpus counts and a total
#   -l         the matching files, then the counts
#   -c         the counts only: matching lines and files per corpus, and a total
#   -E / -P    extended / Perl regex (default: grep's basic regex); -i ignores case
#
# The roots are tools/config_oracle's CORPORA (one place; set AL_BC28_ROOT /
# AL_BCAPPS29_ROOT to move the two external ones): ./BC.History, ./DC, H:/Git/BC28.1,
# H:/Git/BCApps-29.0. A root that does not exist prints `missing` and is not an error.
# Nothing outside these roots is ever searched. grep, not rg: rg's regex dialect is not
# grep's, and one count should not depend on what is on PATH.
#
# Exit: 0 some match, 1 no match, 2 bad pattern or usage.
set -uo pipefail
cd "$(dirname "$0")/.."

FLAGS=(); MODE=lines
while [ $# -gt 0 ]; do
  case "$1" in
    -E|-P|-i) FLAGS+=("$1") ;;
    -l) MODE=files ;;
    -c) MODE=counts ;;
    -h|--help) sed -n '2,18p' "$0"; exit 0 ;;
    --) shift; break ;;
    -*) echo "unknown option: $1" >&2; exit 2 ;;
    *) break ;;
  esac
  shift
done
[ $# -eq 1 ] || { echo "usage: $0 [-E|-P] [-i] [-l|-c] PATTERN" >&2; exit 2; }
PAT="$1"

# A bad pattern is exit 2 from grep on any input; test it once, on nothing.
echo | grep -q "${FLAGS[@]}" -e "$PAT"
[ $? -eq 2 ] && { echo "corpus-grep: bad pattern: $PAT" >&2; exit 2; }

ROOTS="$(python -c 'from tools.config_oracle.__main__ import CORPORA
for k, v in CORPORA.items():
    if k != "selftest": print(f"{k}\t{v.as_posix()}")' | tr -d '\r')" || { echo "corpus-grep: cannot read the roots" >&2; exit 2; }

INC=(--include='*.al' --include='*.AL')
total_l=0; total_f=0
while IFS=$'\t' read -r label root; do
  if [ ! -d "$root" ]; then
    printf '%-12s missing  (%s)\n' "$label" "$root"
    continue
  fi
  case "$MODE" in
    lines) grep -rnH "${FLAGS[@]}" "${INC[@]}" -e "$PAT" "$root" ;;
    files) grep -rl "${FLAGS[@]}" "${INC[@]}" -e "$PAT" "$root" ;;
  esac
  # grep -c prints path:count per file; a Windows path holds ':', so take the last field.
  read -r l f < <(grep -rc "${FLAGS[@]}" "${INC[@]}" -e "$PAT" "$root" |
                  awk -F: '$NF > 0 { l += $NF; f++ } END { print l + 0, f + 0 }')
  printf '%-12s %8d lines %7d files  (%s)\n' "$label" "$l" "$f" "$root"
  total_l=$((total_l + l)); total_f=$((total_f + f))
done <<<"$ROOTS"
printf '%-12s %8d lines %7d files\n' total "$total_l" "$total_f"
[ "$total_l" -gt 0 ] && exit 0 || exit 1
