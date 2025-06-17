#!/bin/bash

# parse-al.sh
# Batch-parse every .al file in a directory tree with tree-sitter, recording passes and failures.
#
# Description:
# * Executes `tree-sitter generate` once (in GRAMMAR_DIR, default = ROOT_DIR).
# * Recursively enumerates *.al files under ROOT_DIR and calls `tree-sitter parse`.
# * Adds the full file path to parsed.txt if the parse exit-code is 0, otherwise to errors.txt.
# * Writes parsed.txt and errors.txt, and prints a summary.
#
# Usage:
#   ./parse-al.sh <ROOT_DIR> [GRAMMAR_DIR]
#
# Parameters:
#   ROOT_DIR    - Root folder that contains the AL test files (required)
#   GRAMMAR_DIR - Folder that contains the grammar (optional, defaults to ROOT_DIR)

set -e

# Check for help or required parameter
if [ $# -lt 1 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 <ROOT_DIR> [GRAMMAR_DIR]"
    echo ""
    echo "  ROOT_DIR    - Root folder that contains the AL test files"
    echo "  GRAMMAR_DIR - Folder that contains the grammar (defaults to ROOT_DIR)"
    exit 0
fi

ROOT_DIR="$1"
GRAMMAR_DIR="${2:-$ROOT_DIR}"

# Validate directories exist
if [ ! -d "$ROOT_DIR" ]; then
    echo "Error: Root directory '$ROOT_DIR' does not exist"
    exit 1
fi

if [ ! -d "$GRAMMAR_DIR" ]; then
    echo "Error: Grammar directory '$GRAMMAR_DIR' does not exist"
    exit 1
fi

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

# --- 3. Parse each file -------------------------------------------------------
parsed_count=0
error_count=0
parsed_path="$ROOT_DIR/parsed.txt"
error_path="$ROOT_DIR/errors.txt"

# Clear output files
> "$parsed_path"
> "$error_path"

echo "$al_files" | while read -r file; do
    if [ -n "$file" ]; then
        if tree-sitter parse -q "$file" >/dev/null 2>&1; then
            echo "$file" >> "$parsed_path"
            parsed_count=$((parsed_count + 1))
        else
            echo "$file" >> "$error_path"
            error_count=$((error_count + 1))
        fi
    fi
done

# --- 4. Report & persist ------------------------------------------------------
# Count results from files
parsed_final=$(wc -l < "$parsed_path" 2>/dev/null || echo "0")
error_final=$(wc -l < "$error_path" 2>/dev/null || echo "0")

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
echo "Parsed OK : $parsed_final"
echo "Errors    : $error_final"
echo ""

if [ "$parsed_final" -gt 0 ]; then
    echo "✓ Parsed list saved to $parsed_path"
fi

if [ "$error_final" -gt 0 ]; then
    echo "✗ Error  list saved to $error_path"
fi

# Exit with appropriate code
if [ "$error_final" -gt 0 ]; then
    exit 1
else
    exit 0
fi