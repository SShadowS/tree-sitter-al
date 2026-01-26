#!/usr/bin/env bash
# ============================================================================
# AL Tree-sitter Indentation Test Suite (Simplified)
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="$SCRIPT_DIR/test/indents"
TEMP_DIR="$SCRIPT_DIR/.test-indent-temp"

# Colors
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    BOLD='\033[1m'
    RESET='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    BOLD=''
    RESET=''
fi

echo -e "${BOLD}========================================${RESET}"
echo -e "${BOLD}AL Tree-sitter Indentation Tests${RESET}"
echo -e "${BOLD}========================================${RESET}"
echo ""

# Setup
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

START_TIME=$(date +%s)
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
TOTAL_LINES=0
DIFF_LINES=0

# Test 1: Full Suite
echo -e "${BLUE}Test 1: Full Suite (921 lines)${RESET}"
cp "$TEST_DIR/indent_test_suite.al" "$TEMP_DIR/test1.al"
nvim --headless "$TEMP_DIR/test1.al" -c "set filetype=al" -c "normal! gg=G" -c "wq" 2>/dev/null

if diff -q "$TEST_DIR/indent_test_suite_unindented.al" "$TEMP_DIR/test1.al" >/dev/null 2>&1; then
    echo -e "  ${GREEN}[✓] PASS${RESET}"
    ((PASSED_TESTS++))
else
    diff_count=$(diff -u "$TEST_DIR/indent_test_suite_unindented.al" "$TEMP_DIR/test1.al" | grep "^[-+]" | wc -l)
    echo -e "  ${RED}[✗] FAIL - $diff_count line differences${RESET}"
    ((FAILED_TESTS++))
    DIFF_LINES=$((DIFF_LINES + diff_count))
    
    echo ""
    echo -e "${YELLOW}Differences:${RESET}"
    diff -u "$TEST_DIR/indent_test_suite_unindented.al" "$TEMP_DIR/test1.al" | head -20
fi
((TOTAL_TESTS++))
TOTAL_LINES=$((TOTAL_LINES + 921))

# Test 2: Quick Test
echo ""
echo -e "${BLUE}Test 2: Quick Test (144 lines)${RESET}"
cp "$TEST_DIR/quick_indent_test.al" "$TEMP_DIR/test2.al"
cp "$TEST_DIR/quick_indent_test.al" "$TEMP_DIR/test2_ref.al"
nvim --headless "$TEMP_DIR/test2.al" -c "set filetype=al" -c "normal! gg=G" -c "wq" 2>/dev/null

if diff -q "$TEMP_DIR/test2_ref.al" "$TEMP_DIR/test2.al" >/dev/null 2>&1; then
    echo -e "  ${GREEN}[✓] PASS${RESET}"
    ((PASSED_TESTS++))
else
    diff_count=$(diff -u "$TEMP_DIR/test2_ref.al" "$TEMP_DIR/test2.al" | grep "^[-+]" | wc -l)
    echo -e "  ${RED}[✗] FAIL - $diff_count line differences${RESET}"
    ((FAILED_TESTS++))
    DIFF_LINES=$((DIFF_LINES + diff_count))
fi
((TOTAL_TESTS++))
TOTAL_LINES=$((TOTAL_LINES + 144))

# Test 3: Idempotency
echo ""
echo -e "${BLUE}Test 3: Idempotency (921 lines)${RESET}"
cp "$TEST_DIR/indent_test_suite_unindented.al" "$TEMP_DIR/test3.al"
cp "$TEST_DIR/indent_test_suite_unindented.al" "$TEMP_DIR/test3_ref.al"
nvim --headless "$TEMP_DIR/test3.al" -c "set filetype=al" -c "normal! gg=G" -c "wq" 2>/dev/null

if diff -q "$TEMP_DIR/test3_ref.al" "$TEMP_DIR/test3.al" >/dev/null 2>&1; then
    echo -e "  ${GREEN}[✓] PASS${RESET}"
    ((PASSED_TESTS++))
else
    diff_count=$(diff -u "$TEMP_DIR/test3_ref.al" "$TEMP_DIR/test3.al" | grep "^[-+]" | wc -l)
    echo -e "  ${RED}[✗] FAIL - $diff_count line differences${RESET}"
    ((FAILED_TESTS++))
    DIFF_LINES=$((DIFF_LINES + diff_count))
fi
((TOTAL_TESTS++))
TOTAL_LINES=$((TOTAL_LINES + 921))

# Summary
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MATCHING_LINES=$((TOTAL_LINES - DIFF_LINES))
MATCH_RATE=0
if [[ $TOTAL_LINES -gt 0 ]]; then
    MATCH_RATE=$(awk "BEGIN {printf \"%.1f\", ($MATCHING_LINES / $TOTAL_LINES) * 100}")
fi

echo ""
echo -e "${BLUE}Results:${RESET}"
echo "  Total Tests: $TOTAL_TESTS"
echo -e "  Passed: ${GREEN}$PASSED_TESTS${RESET}"
if [[ $FAILED_TESTS -gt 0 ]]; then
    echo -e "  Failed: ${RED}$FAILED_TESTS${RESET}"
else
    echo "  Failed: $FAILED_TESTS"
fi
echo ""
echo "  Lines Tested: $TOTAL_LINES"
echo "  Lines Matching: $MATCHING_LINES"
if [[ $DIFF_LINES -gt 0 ]]; then
    echo -e "  Lines Differing: ${RED}$DIFF_LINES${RESET}"
fi
echo "  Match Rate: ${MATCH_RATE}%"
echo "  Duration: ${DURATION}s"

echo ""
echo -e "${BOLD}========================================${RESET}"
if [[ $FAILED_TESTS -eq 0 ]]; then
    echo -e "${GREEN}${BOLD}✅ ALL TESTS PASSED${RESET}"
    EXIT_CODE=0
else
    echo -e "${RED}${BOLD}❌ SOME TESTS FAILED${RESET}"
    EXIT_CODE=1
fi
echo -e "${BOLD}========================================${RESET}"

# Cleanup
rm -rf "$TEMP_DIR"

exit $EXIT_CODE
