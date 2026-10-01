#!/bin/bash
#
# metrics.sh — the parser metrics in one line, optionally against another revision.
#
#   ./tools/metrics.sh              # STATE_COUNT, LARGE_STATE_COUNT, SYMBOL_COUNT,
#                                   # parser.c bytes + MiB, grammar.js lines, test cases
#   ./tools/metrics.sh --vs REV     # the same at REV (git show), and the deltas
#   ./tools/metrics.sh --tests      # take the test count from a real
#                                   # `./tools/ts-lock.sh tree-sitter test` run
#
# The test count comes from tools/count_corpus_cases.py by default: it counts the
# cases a run actually EXECUTES (not the declared headers), and validate-grammar.sh
# Step 3 fails if it ever disagrees with the suite's own total. So the default is the
# real number without the lock or the ~1 min run. --tests is the direct measurement.
# With --vs, REV's count is taken from REV's test/corpus by the same script.
#
# Reads src/parser.c as it is on disk: run `tree-sitter generate` first if grammar.js
# changed. Exit 0, or 2 if it cannot read a figure.
set -euo pipefail
cd "$(dirname "$0")/.."

VS=""; TESTS=0
while [ $# -gt 0 ]; do
  case "$1" in
    --vs)    VS="${2:?--vs needs a revision}"; shift ;;
    --tests) TESTS=1 ;;
    -h|--help) sed -n '2,19p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done

define() {  # define NAME < parser.c head
  sed -n "s/^#define $1 \([0-9][0-9]*\)\$/\1/p" | head -1
}

# show REV PATH: the file at REV, or on disk when REV is empty
show() { if [ -n "$1" ]; then git show "$1:$2"; else cat "$2"; fi; }

# figures REV CORPUS_DIR -> "states large symbols bytes lines cases"
figures() {
  local rev="$1" corpus="$2" head states large symbols bytes lines cases
  head="$(show "$rev" src/parser.c | sed -n '1,40p')"   # no early exit: no SIGPIPE
  states="$(define STATE_COUNT <<<"$head")"
  large="$(define LARGE_STATE_COUNT <<<"$head")"
  symbols="$(define SYMBOL_COUNT <<<"$head")"
  bytes="$(show "$rev" src/parser.c | wc -c | tr -d ' ')"
  lines="$(show "$rev" grammar.js | wc -l | tr -d ' ')"
  cases="$(python tools/count_corpus_cases.py "$corpus" | sed -n 's/^runnable_cases=//p' || true)"
  for v in "$states" "$large" "$symbols" "$cases"; do
    [ -n "$v" ] || { echo "metrics: cannot read a figure at ${rev:-the working tree}" >&2; exit 2; }
  done
  echo "$states $large $symbols $bytes $lines $cases"
}

mib() { awk -v b="$1" 'BEGIN { printf "%.1f", b / 1048576 }'; }

read -r S L Y B G T <<<"$(figures "" test/corpus)"
if [ "$TESTS" -eq 1 ]; then
  T="$(./tools/ts-lock.sh tree-sitter test 2>&1 | sed -n 's/^Total parses: \([0-9][0-9]*\);.*/\1/p' | tail -1)"
  [ -n "$T" ] || { echo "metrics: no 'Total parses' line from tree-sitter test" >&2; exit 2; }
fi
echo "STATE_COUNT=$S LARGE_STATE_COUNT=$L SYMBOL_COUNT=$Y parser.c=${B}B ($(mib "$B") MiB) grammar.js=${G} lines tests=$T"

if [ -n "$VS" ]; then
  git rev-parse --verify --quiet "$VS^{commit}" >/dev/null || { echo "metrics: no such revision: $VS" >&2; exit 2; }
  TMP="$(mktemp -d)"; trap 'rm -rf "${TMP:?}"' EXIT
  git archive "$VS" test/corpus | tar -x -C "$TMP"
  read -r S0 L0 Y0 B0 G0 T0 <<<"$(figures "$VS" "$TMP/test/corpus")"
  delta() {  # delta OLD NEW [UNIT [pct]]
    awk -v a="$1" -v b="$2" -v u="${3:-}" -v p="${4:-}" 'BEGIN {
    d = b - a; s = (d > 0 ? "+" : "") d u
    if (p && a) s = s sprintf(" (%+.2f%%)", 100 * d / a); printf "%s", s }'; }
  echo "at $VS:   STATE_COUNT=$S0 LARGE_STATE_COUNT=$L0 SYMBOL_COUNT=$Y0 parser.c=${B0}B ($(mib "$B0") MiB) grammar.js=${G0} lines tests=$T0"
  echo "delta:    STATE_COUNT $(delta "$S0" "$S" "" pct)  LARGE_STATE_COUNT $(delta "$L0" "$L")  SYMBOL_COUNT $(delta "$Y0" "$Y")  parser.c $(delta "$B0" "$B" B pct)  grammar.js $(delta "$G0" "$G" " lines")  tests $(delta "$T0" "$T")"
fi
