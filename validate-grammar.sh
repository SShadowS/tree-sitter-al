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

# Deliberate-negative fixtures: their expected trees contain ERROR nodes ON
# PURPOSE — the ERROR *is* the assertion, so they are exempt from this step. A
# hit in any other corpus file still fails it.
#
# Keep this list in sync with pre-flight check #3 in .claude/commands/release.md,
# which greps for the same thing before a release. Both gates must exempt exactly
# the same set: this one compares the file's basename for equality, and that one
# anchors its grep to `(^|/)<name>.txt:` so it exempts the same basenames and
# nothing else.
DELIBERATE_ERROR_FIXTURES=(
    # A `TableData Customer = R` fragment misplaced under OptionMembers is shaped
    # exactly like a valid tabledata_permission. Asserts recovery surfaces the
    # dangling remainder as an ERROR instead of silently accepting the whole
    # thing as a well-formed construct.
    "option_members_tabledata_keyword_test.txt"
    # Asserts `#` + newline + `pragma` stays an ERROR: whitespace tolerance after
    # `#` is horizontal-only (`[ \t]*`), so a directive may not straddle a line
    # break and swallow the following source.
    "pragma_whitespace_tolerance_test.txt"
    # Same horizontal-only rule for `#if`/`#elif`, plus `# ifx` — an identifier
    # that merely starts with "if" — must not lex as `#if`.
    "preproc_if_elif_whitespace_tolerance_test.txt"
    # Same horizontal-only rule for `#region`/`#endregion`.
    "preproc_region_whitespace_audit_test.txt"
    # A stray identifier before a var attribute must surface as its own node
    # rather than being absorbed into the '[' token. The input is not valid AL,
    # so the error is correct; what is asserted is that no byte disappears from
    # the tree. It lives in its own file rather than joining the clean scanner
    # fixtures so that those stay subject to this step.
    "scanner_var_attribute_token_span_test.txt"
)

is_deliberate_error_fixture() {
    local name allowed
    name=$(basename "$1")
    for allowed in "${DELIBERATE_ERROR_FIXTURES[@]}"; do
        if [ "$name" = "$allowed" ]; then
            return 0
        fi
    done
    return 1
}

# Search for ERROR or MISSING in test corpus files
# Look for ERROR or MISSING as parse tree nodes (not as AL code)
# Pattern: (ERROR at start of line or after spaces, but not ERROR( which is AL function call
for test_file in test/corpus/*.txt; do
    if [ -f "$test_file" ]; then
        TEST_FILE_COUNT=$((TEST_FILE_COUNT + 1))
        if is_deliberate_error_fixture "$test_file"; then
            continue
        fi
        # Check for (ERROR or (MISSING but not ERROR( which is AL function call
        if grep -qE '^\s*\((ERROR|MISSING)|^\s*(ERROR|MISSING)[^(]' "$test_file"; then
            ERROR_MISSING_FILES+=("$test_file")
        fi
    fi
done

if [ ${#ERROR_MISSING_FILES[@]} -eq 0 ]; then
    print_success "No unexpected ERROR or MISSING nodes in $TEST_FILE_COUNT test files (${#DELIBERATE_ERROR_FIXTURES[@]} deliberate-negative fixtures exempt)"
else
    print_error "Found unexpected ERROR/MISSING nodes in ${#ERROR_MISSING_FILES[@]} test files:"
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
if [ -f "tools/find_unused_definitions.py" ]; then
    ORPHAN_OUTPUT=$(python3 tools/find_unused_definitions.py 2>&1)
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
    print_warning "Orphan detection script not found (tools/find_unused_definitions.py)"
fi

# Step 5: Check for duplicate rule keys in grammar.js's rules object
#
# grammar.js's `rules: { ... }` is one JavaScript object literal. A repeated
# key is valid JS syntax -- the parser silently keeps the LAST value and
# discards the rest -- so `tree-sitter generate`, ESLint, and a normal diff
# review all pass it through unremarked. Task 10 found exactly this
# (`empty_statement` defined twice, identically) by a human reading the file;
# nothing else caught it. tools/analyze_duplicates.py distinguishes an
# IDENTICAL duplicate (dead weight: both definitions agree, so the grammar
# behaves as written, but it is a trap for whoever next edits only one copy)
# from a DIFFERING one (a live bug: the earlier definition is silently
# discarded and the grammar does not do what it says). Both fail this step --
# see the script's module docstring for why "identical, so it's harmless"
# still fails the build.
print_header "Step 5: Checking for Duplicate Rule Keys"
if [ -f "tools/analyze_duplicates.py" ]; then
    DUPLICATE_OUTPUT=$(python3 tools/analyze_duplicates.py 2>&1)
    DUPLICATE_EXIT_CODE=$?

    if [ $DUPLICATE_EXIT_CODE -eq 0 ]; then
        print_success "$DUPLICATE_OUTPUT"
    else
        print_error "Duplicate rule key(s) found in grammar.js:"
        echo "$DUPLICATE_OUTPUT"
        VALIDATION_FAILED=1
    fi
else
    print_warning "Duplicate detection script not found (tools/analyze_duplicates.py)"
fi

# Step 5b: Check field-shape invariants in node-types.json
print_header "Step 5b: Checking Field-Shape Invariants"
if [ -f "tools/check-field-types.py" ]; then
    FIELD_TYPES_OUTPUT=$(python3 tools/check-field-types.py 2>&1)
    FIELD_TYPES_EXIT_CODE=$?

    if [ $FIELD_TYPES_EXIT_CODE -eq 0 ]; then
        print_success "$FIELD_TYPES_OUTPUT"
    else
        print_error "Field-shape invariant violations found:"
        echo "$FIELD_TYPES_OUTPUT"
        VALIDATION_FAILED=1
    fi
else
    print_warning "Field-shape check script not found (tools/check-field-types.py)"
fi

# Step 5c: Compile-check tools/fieldwalk.c
#
# fieldwalk is the only instrument that can verify field membership at runtime
# (it walks a TSTreeCursor; `tree-sitter parse -c` cannot show fields on
# anonymous nodes). Nothing else builds it, so without this it could rot
# unnoticed and take the evidence base for the field-shape rows with it.
#
# Skipped, not failed, when its prerequisites are absent: the vendored runtime
# is fetched on demand by bindings/c/build.sh, and CI images may lack a C
# compiler. Only a genuine compile failure fails validation.
print_header "Step 5c: Compile-Checking tools/fieldwalk.c"
FIELDWALK_TS_DIR=$(ls -d .cache/tree-sitter-*/lib 2>/dev/null | head -1)
FIELDWALK_CC="${CC:-cc}"
command -v "$FIELDWALK_CC" >/dev/null 2>&1 || FIELDWALK_CC=gcc

if [ ! -f "tools/fieldwalk.c" ]; then
    print_warning "fieldwalk not found (tools/fieldwalk.c)"
elif ! command -v "$FIELDWALK_CC" >/dev/null 2>&1; then
    print_warning "No C compiler found - skipping fieldwalk compile check"
elif [ -z "$FIELDWALK_TS_DIR" ]; then
    print_warning "No vendored tree-sitter runtime in .cache/ - skipping fieldwalk compile check (run bindings/c/build.sh once to fetch it)"
else
    FIELDWALK_BIN=$(mktemp -u)
    FIELDWALK_OUTPUT=$("$FIELDWALK_CC" -O0 -o "$FIELDWALK_BIN" \
        tools/fieldwalk.c src/parser.c src/scanner.c "$FIELDWALK_TS_DIR/src/lib.c" \
        -I"$FIELDWALK_TS_DIR/include" -I"$FIELDWALK_TS_DIR/src" -Isrc 2>&1)
    if [ $? -eq 0 ]; then
        print_success "fieldwalk compiles against the current parser"
        rm -f "$FIELDWALK_BIN" "$FIELDWALK_BIN.exe"
    else
        print_error "fieldwalk failed to compile:"
        echo "$FIELDWALK_OUTPUT"
        VALIDATION_FAILED=1
    fi
fi

# Step 5d: Query-coverage regression gate
#
# Proves the CST is lossless over the source and that values stay reachable
# through queries -- a token that was lexed and then dropped shows up here as
# a gap-detector finding, not as a test failure or a parse error.
#
# `baseline.json` is a tracked, committed file, so checking only for its
# existence is not a corpus check -- it is true on every clone. The real
# precondition is BC.History (the corpus the manifest was set-cover'd from),
# which is gitignored and absent on a fresh clone. `qc run` already tells the
# two situations apart: exit 2 means "corpus broken" (missing or drifted),
# exit 1 means "regression found". Skip-with-warning on 2, fail only on 1 (or
# anything else) -- a fresh clone without BC.History must still validate
# cleanly. See tools/query_coverage/README.md.
#
# Exit 2 is overloaded: `qc run` also returns it for a baseline accepted
# under a different manifest (stale `select` without a follow-up `accept`)
# and for `--full-corpus` without `--all`. Neither of those means "no corpus
# to check", so the skip-with-warning is gated on BC.History actually being
# absent -- when the directory exists, exit 2 fails validation the same as
# any other failure, whether the cause is a drifted file or a stale baseline.
print_header "Step 5d: Query-Coverage Harness"
if [ -f tools/query_coverage/baseline.json ]; then
    if python -m tools.query_coverage.qc run; then
        qc_status=0
    else
        qc_status=$?
    fi

    if [ "$qc_status" -eq 0 ]; then
        print_success "query-coverage: no regressions"
    elif [ "$qc_status" -eq 2 ] && [ ! -d BC.History ]; then
        print_warning "query-coverage: corpus not present (BC.History missing) — skipping, see tools/query_coverage/README.md"
    else
        print_error "query-coverage failed (exit $qc_status) — see tools/query_coverage/reports/summary.md"
        VALIDATION_FAILED=1
    fi
else
    echo "Skipping: no baseline yet (run 'python -m tools.query_coverage.qc accept' to create one)"
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
#
# .grammar_baseline.json's known_unused/known_missing entries are mostly
# regex-detector false positives, not real debt -- see its own "_note" field,
# or the BASELINE_NOTE comment in tools/check_grammar_health.py, for the four
# categories and why each was accepted into the baseline.
print_header "Step 8: Grammar Health Check"
if [ -f "tools/check_grammar_health.py" ]; then
    # `&& ... || ...` (not a bare assignment) because this step can now actually
    # fail: under `set -e`, `HEALTH_OUTPUT=$(cmd)` alone would abort the whole
    # script right here on a non-zero exit, before HEALTH_EXIT_CODE is even read
    # -- skipping the error message below and every step after it.
    HEALTH_OUTPUT=$(python3 tools/check_grammar_health.py --ci 2>&1) && HEALTH_EXIT_CODE=0 || HEALTH_EXIT_CODE=$?

    if [ $HEALTH_EXIT_CODE -eq 0 ]; then
        # Extract key metrics from output
        if echo "$HEALTH_OUTPUT" | grep -q "No changes from baseline"; then
            print_success "No regressions from baseline"
        elif echo "$HEALTH_OUTPUT" | grep -q "IMPROVEMENTS:"; then
            print_success "Health check passed with improvements"
        else
            print_success "Health check passed"
        fi
    elif echo "$HEALTH_OUTPUT" | grep -q "NO BASELINE FOUND"; then
        # .grammar_baseline.json is tracked in git (see .gitignore), so it should
        # exist in any real checkout. Its absence means a broken checkout or a
        # deliberate reset, not a routine first run -- never silently re-seed it,
        # that would bless whatever state happens to be on disk as "good".
        print_error "Grammar health baseline missing (.grammar_baseline.json not found)"
        echo "Restore it from git, or if this is a deliberate reset, review the current"
        echo "state and run: python3 tools/check_grammar_health.py --save-baseline"
        VALIDATION_FAILED=1
    else
        print_error "Grammar health check detected regressions"
        echo "$HEALTH_OUTPUT" | grep -A5 "REGRESSIONS:" | head -10
        VALIDATION_FAILED=1
    fi
else
    print_warning "Health check script not found (tools/check_grammar_health.py)"
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