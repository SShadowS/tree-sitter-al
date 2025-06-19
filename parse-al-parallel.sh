#!/bin/bash

# parse-al-parallel.sh
# Multithreaded batch-parse every .al file in a directory tree with tree-sitter, recording passes and failures.
#
# Description:
# * Executes `tree-sitter generate` once (in GRAMMAR_DIR, default = ROOT_DIR).
# * Recursively enumerates *.al files under ROOT_DIR and calls `tree-sitter parse` in parallel.
# * Adds the full file path to parsed.txt if the parse exit-code is 0, otherwise to errors.txt.
# * Writes parsed.txt and errors.txt, and prints a summary.
#
# Usage:
#   ./parse-al-parallel.sh <ROOT_DIR> [GRAMMAR_DIR] [NUM_THREADS]
#
# Parameters:
#   ROOT_DIR    - Root folder that contains the AL test files (required)
#   GRAMMAR_DIR - Folder that contains the grammar (optional, defaults to ROOT_DIR)
#   NUM_THREADS - Number of parallel threads (optional, defaults to number of CPU cores)

set -e

# Check for help or required parameter
if [ $# -lt 1 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 <ROOT_DIR> [GRAMMAR_DIR] [NUM_THREADS]"
    echo ""
    echo "  ROOT_DIR    - Root folder that contains the AL test files"
    echo "  GRAMMAR_DIR - Folder that contains the grammar (defaults to ROOT_DIR)"
    echo "  NUM_THREADS - Number of parallel threads (defaults to number of CPU cores)"
    exit 0
fi

ROOT_DIR="$1"
GRAMMAR_DIR="${2:-$ROOT_DIR}"
NUM_THREADS="${3:-$(nproc)}"

# Validate directories exist
if [ ! -d "$ROOT_DIR" ]; then
    echo "Error: Root directory '$ROOT_DIR' does not exist"
    exit 1
fi

if [ ! -d "$GRAMMAR_DIR" ]; then
    echo "Error: Grammar directory '$GRAMMAR_DIR' does not exist"
    exit 1
fi

echo "Using $NUM_THREADS threads for parallel processing"

# --- 1. (Re)generate the parser ---------------------------------------------
cd "$GRAMMAR_DIR"
if ! tree-sitter generate >/dev/null 2>&1; then
    echo "Error: tree-sitter generate failed"
    exit 1
fi
cd - > /dev/null

# --- 2. Gather *.al files -----------------------------------------------------
al_files=$(find "$ROOT_DIR" -name "*.al" -type f)

if [ -z "$al_files" ]; then
    echo "Warning: No .al files found under $ROOT_DIR"
    exit 0
fi

file_count=$(echo "$al_files" | wc -l)
echo "Processing $file_count .al files..."

# --- 3. Setup output files ---------------------------------------------------
parsed_path="$ROOT_DIR/parsed.txt"
error_path="$ROOT_DIR/errors.txt"

# Clear output files
> "$parsed_path"
> "$error_path"

# Create temporary directory for parallel processing
temp_dir=$(mktemp -d)
trap "rm -rf $temp_dir" EXIT

# --- 4. Parse each file in parallel ------------------------------------------
parse_file() {
    local file="$1"
    local temp_dir="$2"
    local thread_id="$$"
    
    if tree-sitter parse -q "$file" >/dev/null 2>&1; then
        echo "$file" >> "$temp_dir/parsed_$thread_id.txt"
    else
        echo "$file" >> "$temp_dir/errors_$thread_id.txt"
    fi
}

export -f parse_file

# Process files in parallel
echo "$al_files" | xargs -P "$NUM_THREADS" -I {} bash -c 'parse_file "{}" "'"$temp_dir"'"'

# --- 5. Combine results ------------------------------------------------------
echo "Combining results..."

# Combine parsed files
find "$temp_dir" -name "parsed_*.txt" -exec cat {} \; | sort > "$parsed_path"

# Combine error files
find "$temp_dir" -name "errors_*.txt" -exec cat {} \; | sort > "$error_path"

# --- 6. Report & persist -----------------------------------------------------
# Count results from files
parsed_final=$(wc -l < "$parsed_path" 2>/dev/null || echo "0")
error_final=$(wc -l < "$error_path" 2>/dev/null || echo "0")
total_processed=$((parsed_final + error_final))
success_rate=$(echo "scale=1; $parsed_final * 100 / $total_processed" | bc 2>/dev/null || echo "0")

# Remove empty files
if [ "$parsed_final" -eq 0 ]; then
    rm -f "$parsed_path"
fi
if [ "$error_final" -eq 0 ]; then
    rm -f "$error_path"
fi

# Print summary
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