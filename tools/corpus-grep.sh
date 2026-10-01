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
# Exit: 0 some match, 1 no match, 2 bad pattern, usage, or a grep I/O error on a root
# (reported, with that root's counts marked incomplete).
set -uo pipefail
cd "$(dirname "$0")/.."

FLAGS=(); MODE=lines
while [ $# -gt 0 ]; do
  case "$1" in
    -E|-P|-i) FLAGS+=("$1") ;;
    -l) MODE=files ;;
    -c) MODE=counts ;;
    -h|--help) sed -n '2,19p' "$0"; exit 0 ;;
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

INC=(--include='*.[aA][lL]')   # .al in any case: .AL and .Al exist
TMP="$(mktemp -d)"; trap 'rm -rf "${TMP:?}"' EXIT
total_l=0; total_f=0; io_error=0
while IFS=$'\t' read -r label root; do
  if [ ! -d "$root" ]; then
    printf '%-12s missing  (%s)\n' "$label" "$root"
    continue
  fi
  # ONE grep per root. -Z ends the path with a NUL, because a Windows path holds ':'.
  # awk prints what the mode asks for and leaves the counts in $TMP/counts.
  grep -rnHZ "${FLAGS[@]}" "${INC[@]}" -e "$PAT" "$root" 2>"$TMP/err" |
    awk -v mode="$MODE" -v out="$TMP/counts" '{
      i = index($0, "\0"); path = substr($0, 1, i - 1); n++
      if (!(path in seen)) { seen[path] = 1; f++; if (mode == "files") print path }
      if (mode == "lines") print path ":" substr($0, i + 1)
    } END { print n + 0, f + 0 > out }'
  rc=${PIPESTATUS[0]}
  read -r l f < "$TMP/counts"
  if [ "$rc" -eq 2 ]; then  # the pattern was checked above, so this is I/O
    io_error=1
    echo "corpus-grep: grep error under $root:" >&2
    head -5 "$TMP/err" >&2
    printf '%-12s %8d lines %7d files  (%s)  GREP ERROR, counts incomplete\n' "$label" "$l" "$f" "$root"
  else
    printf '%-12s %8d lines %7d files  (%s)\n' "$label" "$l" "$f" "$root"
  fi
  total_l=$((total_l + l)); total_f=$((total_f + f))
done <<<"$ROOTS"
printf '%-12s %8d lines %7d files\n' total "$total_l" "$total_f"
[ "$io_error" -eq 1 ] && exit 2
[ "$total_l" -gt 0 ] && exit 0 || exit 1
