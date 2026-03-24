#!/bin/bash
# benchmark.sh — measure parse performance for pre/post comparison
#
# Usage:
#   ./benchmark.sh [LABEL] [NUM_FILES]
#
# Examples:
#   ./benchmark.sh "baseline"        # run full BC.History sample
#   ./benchmark.sh "after-scanner" 500  # run 500 file sample

LABEL="${1:-unlabeled}"
NUM_FILES="${2:-0}"  # 0 = all files
DIR="./BC.History"
RESULTS_FILE="./benchmark-results.txt"

if [ ! -d "$DIR" ]; then
  echo "Error: $DIR not found"
  exit 1
fi

echo "Generating parser..."
tree-sitter generate > /dev/null 2>&1 || { echo "Generate failed"; exit 1; }

# Gather files
ALL_FILES=$(find "$DIR" -name "*.al" -type f | sort)
TOTAL=$(echo "$ALL_FILES" | wc -l)

if [ "$NUM_FILES" -gt 0 ] && [ "$NUM_FILES" -lt "$TOTAL" ]; then
  FILES=$(echo "$ALL_FILES" | head -"$NUM_FILES")
  SAMPLE=$NUM_FILES
else
  FILES="$ALL_FILES"
  SAMPLE=$TOTAL
fi

echo "Benchmarking '$LABEL': $SAMPLE files..."

# Time the parse
START=$(date +%s%N)
ERRORS=0
PARSED=0

while IFS= read -r f; do
  if tree-sitter parse -q "$f" > /dev/null 2>&1; then
    PARSED=$((PARSED + 1))
  else
    ERRORS=$((ERRORS + 1))
  fi
done <<< "$FILES"

END=$(date +%s%N)
ELAPSED_MS=$(( (END - START) / 1000000 ))
ELAPSED_S=$(awk "BEGIN {printf \"%.2f\", $ELAPSED_MS / 1000}")
PER_FILE_MS=$(awk "BEGIN {printf \"%.2f\", $ELAPSED_MS / $SAMPLE}")
SUCCESS_RATE=$(awk "BEGIN {printf \"%.2f\", $PARSED * 100 / $SAMPLE}")

echo ""
echo "===== BENCHMARK: $LABEL ====="
echo "Files        : $SAMPLE"
echo "Parsed OK    : $PARSED"
echo "Errors       : $ERRORS"
echo "Success rate : ${SUCCESS_RATE}%"
echo "Total time   : ${ELAPSED_S}s"
echo "Per file     : ${PER_FILE_MS}ms"
echo ""

# Append to results file
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
echo "$TIMESTAMP | $LABEL | files=$SAMPLE | parsed=$PARSED | errors=$ERRORS | success=${SUCCESS_RATE}% | total=${ELAPSED_S}s | per_file=${PER_FILE_MS}ms" >> "$RESULTS_FILE"
echo "Result saved to $RESULTS_FILE"
