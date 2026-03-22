#!/bin/bash
# Validate v2 grammar against BC.History, compare with v1
set -e

echo "=== V2 Grammar Validation ==="
cd "$(dirname "$0")"

echo "Generating parser..."
tree-sitter generate

echo "Running tests..."
tree-sitter test

echo "Parsing BC.History..."
../parse-al-parallel.sh ../BC.History/ .

echo ""
echo "=== V1 Baseline ==="
echo "V1 errors: 14 (99.91% success)"
