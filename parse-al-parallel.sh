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
parsed_path="$ROOT_DIR/parsed.txt"
error_path="$ROOT_DIR/errors.txt"

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
if [ "$file_count" -eq 0 ]; then
    echo "Warning: No .al files found under $ROOT_DIR"
    > "$parsed_path"
    > "$error_path"
    rm -f "$parsed_path" "$error_path"
    exit 0
fi
echo "Processing $file_count .al files..."

# --- 4. Split into chunks ----------------------------------------------------
split -l "$CHUNK_SIZE" -d -a 4 "$all_files" "$temp_dir/chunk_"

# --- 5. Parse each chunk in parallel (one tree-sitter process per chunk) ------
parse_chunk() {
    local chunk="$1"
    local temp_dir="$2"
    local name
    name=$(basename "$chunk")
    # In quiet mode tree-sitter only emits a line for files with ERROR/MISSING
    # nodes (or unreadable files). Capture stdout+stderr for post-processing.
    tree-sitter parse -q --paths "$chunk" > "$temp_dir/raw_$name.txt" 2>&1 || true
}
export -f parse_chunk

find "$temp_dir" -name 'chunk_*' -type f -print0 \
    | xargs -0 -P "$NUM_THREADS" -I {} bash -c 'parse_chunk "{}" "'"$temp_dir"'"'

# --- 6. Combine results ------------------------------------------------------
echo "Combining results..."

raw_all="$temp_dir/raw_all.txt"
cat "$temp_dir"/raw_*.txt 2>/dev/null > "$raw_all" || true

# Extract failing file paths:
#  - parse-error lines look like: "<path><padding>\tParse: ... (ERROR ...)"
#  - read-error lines look like:  'Error: Error reading "<path>"'
errors_unsorted="$temp_dir/errors_unsorted.txt"
{
    grep -F $'\tParse:' "$raw_all" 2>/dev/null | cut -f1 | sed 's/[[:space:]]*$//'
    grep -oE 'Error reading "[^"]+"' "$raw_all" 2>/dev/null | sed -E 's/^Error reading "(.*)"$/\1/'
} | sed '/^$/d' | sort -u > "$errors_unsorted"

cp "$errors_unsorted" "$error_path"
# parsed = all files that are not in the error set
comm -23 "$all_files" "$errors_unsorted" > "$parsed_path"

# --- 7. Report & persist -----------------------------------------------------
parsed_final=$(wc -l < "$parsed_path" 2>/dev/null || echo "0")
error_final=$(wc -l < "$error_path" 2>/dev/null || echo "0")
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
echo "Processed    : $total_processed"
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
