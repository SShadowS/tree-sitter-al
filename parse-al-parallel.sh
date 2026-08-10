#!/bin/bash

# parse-al-parallel.sh
# Multithreaded batch-parse every .al file in a directory tree with tree-sitter, recording passes and failures.
#
# Description:
# * Executes `tree-sitter generate` once (in GRAMMAR_DIR, default = ROOT_DIR).
# * Recursively enumerates *.al files under ROOT_DIR.
# * Splits the file list into chunks and parses each chunk with a SINGLE
#   `tree-sitter parse --paths` invocation, run in parallel across chunks.
#   This loads the parser once per chunk instead of once per file, which is
#   ~1-2 orders of magnitude faster than spawning a process per file.
# * Adds the full file path to parsed.txt if the parse succeeded, otherwise to errors.txt.
# * Writes parsed.txt and errors.txt, and prints a summary.
#
# Usage:
#   ./parse-al-parallel.sh <ROOT_DIR> [GRAMMAR_DIR] [NUM_THREADS] [CHUNK_SIZE]
#
# Parameters:
#   ROOT_DIR    - Root folder that contains the AL test files (required)
#   GRAMMAR_DIR - Folder that contains the grammar (optional, defaults to ROOT_DIR)
#   NUM_THREADS - Number of parallel threads (optional, defaults to number of CPU cores)
#   CHUNK_SIZE  - Files per tree-sitter invocation (optional, default 500)
#
# Environment:
#   PARSE_OUT_DIR - where parsed.txt/errors.txt are written (default: ROOT_DIR).
#                   Set it when ROOT_DIR is read-only, or is a symlink/junction
#                   into someone else's checkout.
#
# "PARSED OK" IS A COUNT OF WORK DONE, NOT A SUBTRACTION.
#
# It used to be `comm -23 all_files errors` — the total minus the files that
# *reported* an error. A file that was never parsed emits no error line, so it
# was indistinguishable from a file that parsed cleanly, and it counted as a
# success. Measured with tools/gate-fixtures/chunk-parse-failure/: 100 of 280
# files never opened, and this script still printed
# "Parsed OK: 280, Errors: 0, Success rate: 100.0%", exit 0. Every
# "15,358/15,358, 0 errors" produced before this change establishes only that no
# file reported an error — not that every file was read.
#
# The counts now come from `tree-sitter parse --json-summary`, which emits one
# record per file it actually parsed, each with its own `successful` verdict
# (false for MISSING-only files as well as ERROR ones, so nothing is lost
# relative to the old `\tParse:` text scrape). Each chunk must yield exactly one
# record per file it listed, or the run dies naming that chunk. This is the same
# per-chunk reconciliation tools/tree-harness.sh does, one script over.
#
# Do not "simplify" any of the assertions below back into a subtraction.

set -e

# Check for help or required parameter
if [ $# -lt 1 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 <ROOT_DIR> [GRAMMAR_DIR] [NUM_THREADS] [CHUNK_SIZE]"
    echo ""
    echo "  ROOT_DIR    - Root folder that contains the AL test files"
    echo "  GRAMMAR_DIR - Folder that contains the grammar (defaults to ROOT_DIR)"
    echo "  NUM_THREADS - Number of parallel threads (defaults to number of CPU cores)"
    echo "  CHUNK_SIZE  - Files per tree-sitter invocation (defaults to 500)"
    exit 0
fi

ROOT_DIR="$1"
GRAMMAR_DIR="${2:-$ROOT_DIR}"
NUM_THREADS="${3:-$(nproc)}"
CHUNK_SIZE="${4:-500}"

# Validate directories exist
if [ ! -d "$ROOT_DIR" ]; then
    echo "Error: Root directory '$ROOT_DIR' does not exist"
    exit 1
fi

if [ ! -d "$GRAMMAR_DIR" ]; then
    echo "Error: Grammar directory '$GRAMMAR_DIR' does not exist"
    exit 1
fi

echo "Using $NUM_THREADS threads, chunk size $CHUNK_SIZE"

# --- 1. (Re)generate the parser ---------------------------------------------
# `tree-sitter generate` takes ~20s. Skip it when src/parser.c is already
# newer than grammar.js (nothing to regenerate). Set FORCE_GENERATE=1 to override.
if [ "${FORCE_GENERATE:-0}" != "1" ] \
   && [ -f "$GRAMMAR_DIR/src/parser.c" ] \
   && [ -f "$GRAMMAR_DIR/grammar.js" ] \
   && [ "$GRAMMAR_DIR/src/parser.c" -nt "$GRAMMAR_DIR/grammar.js" ]; then
    echo "Parser up to date - skipping 'tree-sitter generate' (FORCE_GENERATE=1 to override)"
else
    echo "Running 'tree-sitter generate'..."
    cd "$GRAMMAR_DIR"
    if ! tree-sitter generate >/dev/null 2>&1; then
        echo "Error: tree-sitter generate failed"
        exit 1
    fi
    cd - > /dev/null
fi

# --- 2. Setup temp + output --------------------------------------------------
OUT_DIR="${PARSE_OUT_DIR:-$ROOT_DIR}"
if [ ! -d "$OUT_DIR" ]; then
    echo "Error: Output directory '$OUT_DIR' does not exist"
    exit 1
fi
parsed_path="$OUT_DIR/parsed.txt"
error_path="$OUT_DIR/errors.txt"

die() { echo "parse-al-parallel: $*" >&2; exit 1; }

temp_dir=$(mktemp -d)
trap 'rm -rf "$temp_dir"' EXIT

# --- 3. Gather *.al files ----------------------------------------------------
# IMPORTANT (Windows/MSYS): the native tree-sitter binary cannot read MSYS-style
# paths (/c/..., /u/...) listed in a --paths file. It fails with `Error reading`
# on the first such path, ABORTS the rest of that chunk, and every unparsed file
# in the chunk is then silently counted OK by default — yielding a meaningless
# "success" number. Convert to native Windows paths when cygpath is present so
# tree-sitter actually opens the files. No-op on Linux/macOS (no cygpath).
all_files="$temp_dir/all_files.txt"
find "$ROOT_DIR" -name "*.al" -type f | sort > "$temp_dir/all_files_native.txt"
if command -v cygpath >/dev/null 2>&1; then
    cygpath -w -f "$temp_dir/all_files_native.txt" | sort > "$all_files"
else
    cp "$temp_dir/all_files_native.txt" "$all_files"
fi

file_count=$(wc -l < "$all_files")
# A run that examined nothing is not a passing run. This used to print a warning
# and exit 0, so a mistyped root — or, far more easily, a SYMLINKED corpus given
# without a trailing slash — reported success over zero work. `find` does not
# descend into a symlink or NTFS junction named as a bare starting point:
# `find BC.History -name '*.al'` yields 0 files where `find BC.History/` yields
# 15,358. Measured; that is why every documented invocation has the slash.
if [ "$file_count" -eq 0 ]; then
    if [ -L "${ROOT_DIR%/}" ]; then
        die "no .al files under '$ROOT_DIR', which is a symlink/junction — retry as '${ROOT_DIR%/}/' (find does not descend into a bare symlink start point)"
    fi
    die "no .al files under '$ROOT_DIR' — refusing to report on an empty corpus"
fi
echo "Processing $file_count .al files..."

# --- 4. Split into chunks ----------------------------------------------------
split -l "$CHUNK_SIZE" -d -a 4 "$all_files" "$temp_dir/chunk_"

# --- 5. Parse each chunk in parallel (one tree-sitter process per chunk) ------
#
# stdout carries the `\tParse:` diagnostic lines (quiet mode emits one per file
# with ERROR/MISSING nodes) followed by the JSON summary; stderr carries read
# errors. They are kept in SEPARATE files: merging them with 2>&1 lets a stderr
# line land in the middle of the JSON and corrupt the record count.
parse_chunk() {
    local chunk="$1"
    local temp_dir="$2"
    local name rc=0
    name=$(basename "$chunk")

    tree-sitter parse -q --json-summary --paths "$chunk" \
        > "$temp_dir/raw_$name.txt" 2> "$temp_dir/err_$name.txt" || rc=$?

    # The JSON object starts at the first line that is exactly `{` — the only
    # unindented brace, since --json-summary pretty-prints and everything
    # nested is indented. The `\tParse:` lines all precede it.
    sed -n '/^{$/,$p' "$temp_dir/raw_$name.txt" > "$temp_dir/json_$name.txt"

    local expected records ok bad
    expected=$(wc -l < "$chunk")
    records=$(grep -c '"file":' "$temp_dir/json_$name.txt" || true)
    ok=$(grep -c '"successful": true' "$temp_dir/json_$name.txt" || true)
    bad=$(grep -c '"successful": false' "$temp_dir/json_$name.txt" || true)

    printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
        "$name" "$expected" "$records" "$ok" "$bad" "$rc" > "$temp_dir/stat_$name.txt"
}
export -f parse_chunk

chunk_count=$(find "$temp_dir" -name 'chunk_*' -type f | wc -l)
find "$temp_dir" -name 'chunk_*' -type f -print0 \
    | xargs -0 -P "$NUM_THREADS" -I {} bash -c 'parse_chunk "{}" "'"$temp_dir"'"'

# --- 5b. Reconcile every chunk before believing any number -------------------
#
# THIS LOOP IS THE GATE. A chunk that dies produces no JSON at all, so it fails
# here instead of contributing nothing and being counted as 500 clean files. A
# chunk aborted partway — which is what tree-sitter does on the FIRST unreadable
# path in a --paths list, discarding the rest of the chunk including files it
# had already parsed — fails here too.
stat_count=$(find "$temp_dir" -name 'stat_chunk_*' -type f | wc -l)
[ "$stat_count" -eq "$chunk_count" ] \
    || die "only $stat_count of $chunk_count chunks reported — a parse worker never ran"

total_ok=0
total_bad=0
bad_chunks=0
while IFS=$'\t' read -r name expected records ok bad rc; do
    if [ "$records" -ne "$expected" ] || [ $(( ok + bad )) -ne "$records" ]; then
        bad_chunks=$(( bad_chunks + 1 ))
        {
            echo "parse-al-parallel: chunk $name produced $records parse records for $expected files"
            echo "parse-al-parallel:   successful=$ok failed=$bad tree-sitter exit=$rc"
            if [ "$records" -lt "$expected" ]; then
                echo "parse-al-parallel:   $(( expected - records )) file(s) in this chunk were never parsed"
            elif [ "$records" -gt "$expected" ]; then
                echo "parse-al-parallel:   $(( records - expected )) more record(s) than files — records are duplicated or misattributed"
            else
                echo "parse-al-parallel:   record count is right but successful+failed does not sum to it — JSON format drift"
            fi
            echo "parse-al-parallel:   stderr:"
            head -n 5 "$temp_dir/err_$name.txt" 2>&1 | sed 's/^/parse-al-parallel:     /'
            echo "parse-al-parallel:   stdout (first lines):"
            head -n 3 "$temp_dir/raw_$name.txt" 2>&1 | sed 's/^/parse-al-parallel:     /'
        } >&2
        continue
    fi
    total_ok=$(( total_ok + ok ))
    total_bad=$(( total_bad + bad ))
done < <(cat "$temp_dir"/stat_chunk_*.txt)

[ "$bad_chunks" -eq 0 ] \
    || die "$bad_chunks of $chunk_count chunks did not parse every file they listed — refusing to report a success rate over an incomplete run"

[ $(( total_ok + total_bad )) -eq "$file_count" ] \
    || die "parser reported $(( total_ok + total_bad )) files but $file_count were enumerated"

# --- 6. Combine results ------------------------------------------------------
echo "Combining results..."

# Both streams, because which one carries the `\tParse:` diagnostic is
# tree-sitter's business and not something this script should depend on. The
# JSON count is the authority either way; this scrape only supplies names.
raw_all="$temp_dir/raw_all.txt"
cat "$temp_dir"/raw_*.txt "$temp_dir"/err_*.txt > "$raw_all"

# Which files failed. The COUNT is already known from the JSON above; this
# scrape only supplies the PATHS, and is cross-checked against that count below,
# so the two can never quietly disagree. Read errors are not handled here: they
# abort their whole chunk, which step 5b has already turned into a hard failure.
#  - parse-error lines look like: "<path><padding>\tParse: ... (ERROR ...)"
errors_unsorted="$temp_dir/errors_unsorted.txt"
grep -F $'\tParse:' "$raw_all" | cut -f1 | sed 's/[[:space:]]*$//' \
    | sed '/^$/d' | sort -u > "$errors_unsorted"

error_final=$(wc -l < "$errors_unsorted")
[ "$error_final" -eq "$total_bad" ] \
    || die "the parser reported $total_bad failing file(s) but $error_final path(s) could be named — the diagnostic scrape and the JSON summary disagree"

cp "$errors_unsorted" "$error_path"
# The LIST of clean files is still a set difference — that is all a list can be
# — but every count below comes from the parser, and the two are reconciled.
comm -23 "$all_files" "$errors_unsorted" > "$parsed_path"

# --- 7. Report & persist -----------------------------------------------------
parsed_final=$total_ok
parsed_listed=$(wc -l < "$parsed_path")
[ "$parsed_listed" -eq "$parsed_final" ] \
    || die "parsed.txt lists $parsed_listed file(s) but the parser reported $parsed_final successes"
total_processed=$((parsed_final + error_final))
# Integer math (no `bc` dependency): one decimal place.
if [ "$total_processed" -gt 0 ]; then
    rate_tenths=$(( parsed_final * 1000 / total_processed ))
    success_rate="${rate_tenths%?}.${rate_tenths: -1}"
else
    success_rate="0.0"
fi

# Remove empty files
if [ "$parsed_final" -eq 0 ]; then
    rm -f "$parsed_path"
fi
if [ "$error_final" -eq 0 ]; then
    rm -f "$error_path"
fi

echo ""
echo "===== SUMMARY ====="
echo "Total files  : $file_count"
# "Processed" used to be parsed+errors where parsed was total−errors, so it was
# algebraically equal to "Total files" no matter what happened — it looked like
# a reconciliation and carried no information. It is now the number of records
# the parser emitted, counted independently and asserted equal to the total.
echo "Processed    : $total_processed  (parse records from --json-summary)"
echo "Parsed OK    : $parsed_final"
echo "Errors       : $error_final"
echo "Success rate : ${success_rate}%"
echo ""

if [ "$parsed_final" -gt 0 ]; then
    echo "✓ Parsed list saved to $parsed_path"
fi

if [ "$error_final" -gt 0 ]; then
    echo "✗ Error list saved to $error_path"
fi

# Exit with appropriate code
if [ "$error_final" -gt 0 ]; then
    exit 1
else
    exit 0
fi
