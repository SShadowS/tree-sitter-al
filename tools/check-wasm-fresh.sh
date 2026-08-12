#!/usr/bin/env sh
#
# Is the committed tree-sitter-al.wasm built from the committed sources?
#
# WHY THIS EXISTS. .github/workflows/build-wasm.yml does not build the wasm --
# its release job runs `cp tree-sitter-al.wasm artifacts/`, so the file in git is
# shipped verbatim to every web-tree-sitter consumer. Nothing rebuilds it, and
# nothing noticed when it went stale: v4.0.0 shipped a fresh one, then a grammar
# fix landed and the wasm sat at the older parser while every other gate stayed
# green. Measured: the shipped 4.0.0 wasm parses
#
#     codeunit 80228 "T" { var Filter: Codeunit "Some Thing"; }
#
# with one ERROR; the rebuilt one parses it clean. That is a defect a consumer
# hits and no test here could see, because the test suite never loads the wasm.
#
# The stamp is over the two files the wasm is actually compiled from --
# src/parser.c and src/scanner.c -- not over grammar.js. A grammar.js edit that
# does not change generated output does not invalidate the wasm, and requiring a
# rebuild for one would train people to update the stamp by hand, which is the
# one action that makes this check lie.
#
# Usage:
#   tools/check-wasm-fresh.sh            # verify; exit 1 if stale
#   tools/check-wasm-fresh.sh --update   # re-stamp after an actual rebuild
#
# Rebuild with:  tree-sitter build --wasm -o tree-sitter-al.wasm
set -eu

STAMP=tree-sitter-al.wasm.inputs.sha256
INPUTS="src/parser.c src/scanner.c"

cd "$(dirname "$0")/.."

for f in $INPUTS tree-sitter-al.wasm; do
  [ -f "$f" ] || { echo "check-wasm-fresh: missing $f" >&2; exit 2; }
done

# Hash of the concatenated per-file hashes, so a swap between the two files is
# still a change. `cut` drops sha256sum's trailing filename, which would embed
# the checkout path on some platforms.
current=$(sha256sum $INPUTS | sha256sum | cut -d' ' -f1)

if [ "${1:-}" = "--update" ]; then
  printf '%s\n' "$current" > "$STAMP"
  echo "check-wasm-fresh: stamped $STAMP with $current"
  echo "check-wasm-fresh: this records that the CURRENT wasm was built from the CURRENT $INPUTS."
  echo "check-wasm-fresh: only run it immediately after a real rebuild -- running it to clear a"
  echo "check-wasm-fresh: failure without rebuilding converts this gate into a rubber stamp."
  exit 0
fi

if [ ! -f "$STAMP" ]; then
  echo "check-wasm-fresh: FAIL - $STAMP is missing, so nothing records which sources the committed wasm came from" >&2
  exit 1
fi

recorded=$(cat "$STAMP")

if [ "$current" != "$recorded" ]; then
  cat >&2 <<EOF
check-wasm-fresh: FAIL - tree-sitter-al.wasm is stale

  recorded (when the wasm was last built): $recorded
  current  ($INPUTS):                      $current

src/parser.c or src/scanner.c has changed since the wasm was built. The release
workflow copies the committed wasm verbatim, so publishing now ships a parser
that does not match this repository.

Fix:
  tree-sitter build --wasm -o tree-sitter-al.wasm
  tools/check-wasm-fresh.sh --update
  git add tree-sitter-al.wasm $STAMP
EOF
  exit 1
fi

echo "check-wasm-fresh: OK - wasm matches $INPUTS ($current)"
