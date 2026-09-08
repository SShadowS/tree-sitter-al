#!/bin/bash
#
# probe.sh — re-measure AL operator precedence against the compiler.
#
#   ./tools/precedence/probe.sh <packagecachepath> [outfile]
#
# Compiles every case in cases/ with `al compile`, ONE AT A TIME, and writes
# name<TAB>ACCEPT|REJECT<TAB>first-error to outfile (default alc-results.tsv).
# Diff that against the committed alc-results.tsv to see whether the compiler's
# answers have changed under a newer alc.
#
# WHY ONE AT A TIME: `al compile` compiles every .al in the project directory, so
# a leftover probe file fails the run you are reading. The loop copies exactly one
# case in and deletes it again.
#
# WHAT YOU NEED
#
# A directory of BC symbol packages (Microsoft_Application, Base Application,
# System Application, System, Business Foundation). Without them the project
# fails to load and emits NO diagnostics at all — for valid and invalid code
# alike — so the probe silently loses all discriminating power. That failure
# looks exactly like a rejection.
#
# SANITY-CHECK BEFORE TRUSTING ANY REJECTION. The script runs the four control
# cases first and refuses to continue if they do not come out as recorded:
# a rig that rejects everything proves nothing.
#
# The alc version these results were taken with is stamped in
# docs/al-operator-precedence.md. Record the new one if you re-run.
set -euo pipefail

if [ $# -lt 1 ]; then sed -n '2,12p' "$0"; exit 2; fi

PKG="$1"
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${2:-$HERE/alc-results.tsv}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

mkdir -p "$WORK/proj" "$WORK/logs"
cat > "$WORK/proj/app.json" <<'JSON'
{"id":"11111111-2222-3333-4444-555555555555","name":"Probe","publisher":"Test",
 "version":"1.0.0.0","platform":"1.0.0.0",
 "idRanges":[{"from":50000,"to":99999}],"runtime":"15.0","target":"OnPrem"}
JSON

# Deliberately no `application` or `dependencies` key: those pull in symbol
# packages by name and fail the project load when they are not resolvable.

run_one() {
    local case_file="$1" name verdict msg
    name="$(basename "$case_file" .al)"
    rm -f "$WORK/proj"/*.al "$WORK/proj/out.app"
    cp "$case_file" "$WORK/proj/Test.al"
    al compile "/project:$WORK/proj" "/out:$WORK/proj/out.app" \
        "/packagecachepath:$PKG" > "$WORK/logs/$name.log" 2>&1 || true
    if [ -f "$WORK/proj/out.app" ]; then verdict=ACCEPT; else verdict=REJECT; fi
    msg="$(grep -oE 'error AL[0-9]+: .*' "$WORK/logs/$name.log" | head -1 \
           | sed 's/error //; s/ Use an explicit conversion.*//; s/ Remove the invalid.*//; s/ Add a semicolon.*//')"
    printf '%s\t%s\t%s\n' "$name" "$verdict" "$msg"
}

# --- controls first: the rig must discriminate before its answers mean anything
echo "checking controls..." >&2
declare -A EXPECTED=(
    [ctl_zero_direct]=REJECT      # 1 div 0                -> AL0370
    [ctl_zero_computed]=REJECT    # 1 div (2 - 2)          -> folds, AL0370
    [ctl_nonzero]=ACCEPT          # 1 div (2 - 1)
    [ctl_ovf]=REJECT              # 2147483647 + 1         -> AL0371
)
for name in "${!EXPECTED[@]}"; do
    got="$(run_one "$HERE/cases/$name.al" | cut -f2)"
    if [ "$got" != "${EXPECTED[$name]}" ]; then
        echo "CONTROL FAILED: $name expected ${EXPECTED[$name]}, got $got." >&2
        echo "The probe rig is broken (symbols missing?), not the compiler." >&2
        echo "Every result from a rig in this state is meaningless. Refusing." >&2
        exit 1
    fi
done
echo "controls pass; measuring $(ls "$HERE/cases"/*.al | wc -l) cases" >&2

: > "$OUT"
for case_file in "$HERE"/cases/*.al; do
    run_one "$case_file" >> "$OUT"
done
sort -o "$OUT" "$OUT"
echo "wrote $(wc -l < "$OUT") results -> $OUT" >&2
