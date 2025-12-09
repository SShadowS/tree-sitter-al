#!/bin/bash

# validate-grammar.sh - Comprehensive grammar validation script
# Runs all validation checks in sequence and reports results

set -e  # Exit on first error

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print section headers
print_header() {
    echo -e "\n${BLUE}===================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Track overall status
VALIDATION_FAILED=0

# Start validation
echo -e "${BLUE}Starting comprehensive grammar validation...${NC}"
START_TIME=$(date +%s)

# Step 1: Generate parser
print_header "Step 1: Generating Parser"
if tree-sitter generate; then
    print_success "Parser generated successfully"
else
    print_error "Parser generation failed"
    VALIDATION_FAILED=1
    exit 1
fi

# Step 2: Run test suite
print_header "Step 2: Running Test Suite"
TEST_OUTPUT=$(tree-sitter test 2>&1)
TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -eq 0 ]; then
    # Extract test statistics
    TOTAL_TESTS=$(echo "$TEST_OUTPUT" | grep -oE '[0-9]+ (of [0-9]+ )?parsed)' | grep -oE '[0-9]+' | tail -1)
    PASSED_TESTS=$(echo "$TEST_OUTPUT" | grep -cE '✓|passed' || true)
    
    if [ -n "$TOTAL_TESTS" ]; then
        print_success "All tests passed ($PASSED_TESTS/$TOTAL_TESTS)"
    else
        print_success "All tests passed"
    fi
else
    print_error "Some tests failed"
    # Show summary of failures
    echo "$TEST_OUTPUT" | grep -E "failures:|failed parses:" || true
    echo ""
    # Show which tests failed
    echo "Failed tests:"
    echo "$TEST_OUTPUT" | grep -B1 "✗" | head -20
    echo ""
    # Show the last line with statistics
    echo "$TEST_OUTPUT" | tail -1
    VALIDATION_FAILED=1
fi

# Step 3: Check for ERROR and MISSING nodes in tests
print_header "Step 3: Checking for ERROR/MISSING Nodes in Tests"
echo "Scanning test files for ERROR or MISSING nodes..."
ERROR_MISSING_FILES=()
TEST_FILE_COUNT=0

# Search for ERROR or MISSING in test corpus files
# Look for ERROR or MISSING as parse tree nodes (not as AL code)
# Pattern: (ERROR at start of line or after spaces, but not ERROR( which is AL function call
for test_file in test/corpus/*.txt; do
    if [ -f "$test_file" ]; then
        TEST_FILE_COUNT=$((TEST_FILE_COUNT + 1))
        # Check for (ERROR or (MISSING but not ERROR( which is AL function call
        if grep -qE '^\s*\((ERROR|MISSING)|^\s*(ERROR|MISSING)[^(]' "$test_file"; then
            ERROR_MISSING_FILES+=("$test_file")
        fi
    fi
done

if [ ${#ERROR_MISSING_FILES[@]} -eq 0 ]; then
    print_success "No ERROR or MISSING nodes found in $TEST_FILE_COUNT test files"
else
    print_error "Found ERROR/MISSING nodes in ${#ERROR_MISSING_FILES[@]} test files:"
    for file in "${ERROR_MISSING_FILES[@]}"; do
        echo "  - $(basename "$file")"
        # Show the first occurrence of ERROR or MISSING in each file
        grep -n -m 1 -E '^\s*\((ERROR|MISSING)|^\s*(ERROR|MISSING)[^(]' "$file" | sed 's/^/    /'
    done
    VALIDATION_FAILED=1
    echo -e "\n${YELLOW}These test files contain ERROR or MISSING nodes, indicating incomplete parsing.${NC}"
    echo -e "${YELLOW}This is a serious issue that should be fixed.${NC}"
fi

# Step 4: Check for orphaned rules
print_header "Step 4: Checking for Orphaned Rules"
if [ -f "find_unused_definitions.py" ]; then
    ORPHAN_OUTPUT=$(python3 find_unused_definitions.py 2>&1)
    ORPHAN_EXIT_CODE=$?
    
    if [ $ORPHAN_EXIT_CODE -eq 0 ]; then
        # Check if there are any unused rules in the output
        if echo "$ORPHAN_OUTPUT" | grep -q "Unused rules:"; then
            UNUSED_COUNT=$(echo "$ORPHAN_OUTPUT" | grep -A1 "Unused rules:" | grep -oE '[0-9]+' | head -1)
            if [ "$UNUSED_COUNT" = "0" ]; then
                print_success "No orphaned rules found"
            else
                print_warning "Found $UNUSED_COUNT orphaned rules"
                echo "$ORPHAN_OUTPUT" | grep -A20 "Unused rules:" | head -20
                VALIDATION_FAILED=1
            fi
        else
            print_success "No orphaned rules found"
        fi
    else
        print_error "Orphan detection script failed"
        echo "$ORPHAN_OUTPUT" | head -10
        VALIDATION_FAILED=1
    fi
else
    print_warning "Orphan detection script not found (find_unused_definitions.py)"
fi

# Step 5: Check for duplicate rules
print_header "Step 5: Checking for Duplicate Rules"
if [ -f "analyze_duplicates.py" ]; then
    DUPLICATE_OUTPUT=$(python3 analyze_duplicates.py 2>&1)
    DUPLICATE_EXIT_CODE=$?
    
    if [ $DUPLICATE_EXIT_CODE -eq 0 ]; then
        # Check if there are any duplicates in the output
        if echo "$DUPLICATE_OUTPUT" | grep -q "Found [1-9][0-9]* duplicate"; then
            DUPLICATE_COUNT=$(echo "$DUPLICATE_OUTPUT" | grep -oE 'Found [0-9]+ duplicate' | grep -oE '[0-9]+')
            print_warning "Found $DUPLICATE_COUNT duplicate rule definitions"
            echo "$DUPLICATE_OUTPUT" | grep -A20 "Duplicate rule:" | head -20
            VALIDATION_FAILED=1
        else
            print_success "No duplicate rules found"
        fi
    else
        print_error "Duplicate detection script failed"
        echo "$DUPLICATE_OUTPUT" | head -10
        VALIDATION_FAILED=1
    fi
else
    print_warning "Duplicate detection script not found (analyze_duplicates.py)"
fi

# Step 6: Run parsing test on AL files (optional, can be slow)
print_header "Step 6: AL File Parsing Test (Optional)"
if [ -f "parse-al-parallel.sh" ] && [ "$1" = "--full" ]; then
    echo "Running full AL file parsing test..."
    PARSE_OUTPUT=$(./parse-al-parallel.sh 2>&1 | tail -5)
    echo "$PARSE_OUTPUT"
    
    # Extract success rate
    if echo "$PARSE_OUTPUT" | grep -q "Success rate:"; then
        SUCCESS_RATE=$(echo "$PARSE_OUTPUT" | grep "Success rate:" | grep -oE '[0-9]+\.[0-9]+')
        if (( $(echo "$SUCCESS_RATE > 90" | bc -l) )); then
            print_success "AL parsing success rate: $SUCCESS_RATE%"
        else
            print_warning "AL parsing success rate: $SUCCESS_RATE% (below 90%)"
        fi
    fi
else
    echo "Skipping AL file parsing test (use --full to include)"
fi

# Step 7: Check for common issues
print_header "Step 7: Checking for Common Issues"

# Check for rules without kw() wrapper (case sensitivity issues)
echo "Checking for potentially case-sensitive keywords..."
# Exclude field() function calls which are grammar metadata, not AL keywords
CASE_SENSITIVE=$(grep -n "'\(table\|page\|field\|procedure\|trigger\|var\|begin\|end\|if\|then\|else\)'" grammar.js | grep -v "kw(" | grep -v "field(" | head -5 || true)
if [ -n "$CASE_SENSITIVE" ]; then
    print_warning "Found potentially case-sensitive keywords (should use kw()):"
    echo "$CASE_SENSITIVE"
else
    print_success "No case-sensitive keyword issues found"
fi

# Check for TODO comments
echo "Checking for TODO comments..."
TODO_COUNT=$(grep -c "TODO" grammar.js || true)
if [ $TODO_COUNT -gt 0 ]; then
    print_warning "Found $TODO_COUNT TODO comments in grammar.js"
    grep -n "TODO" grammar.js | head -5
else
    print_success "No TODO comments found"
fi

# Step 8: Grammar health check (regression detection)
print_header "Step 8: Grammar Health Check"
if [ -f "check_grammar_health.py" ]; then
    HEALTH_OUTPUT=$(python3 check_grammar_health.py --ci 2>&1)
    HEALTH_EXIT_CODE=$?

    if [ $HEALTH_EXIT_CODE -eq 0 ]; then
        # Extract key metrics from output
        if echo "$HEALTH_OUTPUT" | grep -q "No changes from baseline"; then
            print_success "No regressions from baseline"
        elif echo "$HEALTH_OUTPUT" | grep -q "IMPROVEMENTS:"; then
            print_success "Health check passed with improvements"
        else
            print_success "Health check passed"
        fi
    else
        print_error "Grammar health check detected regressions"
        echo "$HEALTH_OUTPUT" | grep -A5 "REGRESSIONS:" | head -10
        VALIDATION_FAILED=1
    fi
else
    print_warning "Health check script not found (check_grammar_health.py)"
fi

# Final summary
print_header "Validation Summary"
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo "Total validation time: ${DURATION}s"

if [ $VALIDATION_FAILED -eq 0 ]; then
    print_success "All validation checks passed! ✨"
    exit 0
else
    print_error "Some validation checks failed!"
    echo -e "\n${YELLOW}Next steps:${NC}"
    echo "1. Fix any failing tests"
    echo "2. Remove ERROR and MISSING nodes from test files"
    echo "3. Remove or implement orphaned rules"
    echo "4. Consolidate duplicate rules"
    echo "5. Use kw() for case-insensitive keywords"
    exit 1
fi