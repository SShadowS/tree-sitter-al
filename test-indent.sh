#!/usr/bin/env bash
# ============================================================================
# AL Tree-sitter Indentation Test Suite
# ============================================================================
# Runs comprehensive headless indentation tests using Neovim
#
# Usage:
#   ./test-indent.sh           # Run all tests with summary
#   ./test-indent.sh --verbose # Run with detailed output
#   ./test-indent.sh --ci      # CI mode (exit codes, no colors)

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="$SCRIPT_DIR/test/indents"
TEMP_DIR="$SCRIPT_DIR/.test-indent-temp"
NVIM_PARSER="$HOME/AppData/Local/nvim-data/site/parser/al.so"

# Test files
# NOTE: The file names are backwards - indent_test_suite.al is actually unindented (flush left)
# and indent_test_suite_unindented.al is actually the correctly indented reference
FULL_SUITE_INPUT="$TEST_DIR/indent_test_suite.al"  # Unindented input (flush left)
FULL_SUITE_REF="$TEST_DIR/indent_test_suite_unindented.al"  # Correctly indented reference
QUICK_TEST_INPUT="$TEST_DIR/quick_indent_test.al"

# Color codes (disabled in CI mode)
USE_COLOR=true
if [[ -t 1 ]] && command -v tput >/dev/null 2>&1; then
    RED=$(tput setaf 1)
    GREEN=$(tput setaf 2)
    YELLOW=$(tput setaf 3)
    BLUE=$(tput setaf 4)
    BOLD=$(tput bold)
    RESET=$(tput sgr0)
else
    RED=""
    GREEN=""
    YELLOW=""
    BLUE=""
    BOLD=""
    RESET=""
fi

# ============================================================================
# Parse Arguments
# ============================================================================

VERBOSE=false
CI_MODE=false

for arg in "$@"; do
    case $arg in
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --ci)
            CI_MODE=true
            USE_COLOR=false
            RED=""
            GREEN=""
            YELLOW=""
            BLUE=""
            BOLD=""
            RESET=""
            shift
            ;;
        --help|-h)
            echo "AL Tree-sitter Indentation Test Suite"
            echo ""
            echo "Usage:"
            echo "  $0              Run all tests with summary"
            echo "  $0 --verbose    Run with detailed output"
            echo "  $0 --ci         CI mode (exit codes, no colors)"
            echo "  $0 --help       Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo "${BLUE}${1}${RESET}"
}

log_success() {
    echo "${GREEN}${1}${RESET}"
}

log_warning() {
    echo "${YELLOW}${1}${RESET}"
}

log_error() {
    echo "${RED}${1}${RESET}"
}

log_bold() {
    echo "${BOLD}${1}${RESET}"
}

verbose_log() {
    if [[ "$VERBOSE" == true ]]; then
        echo "  $1"
    fi
}

# Check if nvim is available
check_nvim() {
    if ! command -v nvim >/dev/null 2>&1; then
        log_error "ERROR: nvim not found in PATH"
        exit 1
    fi
    verbose_log "Neovim: $(command -v nvim)"
}

# Check if parser is installed
check_parser() {
    if [[ ! -f "$NVIM_PARSER" ]]; then
        log_error "ERROR: Parser not found at $NVIM_PARSER"
        exit 1
    fi
    local parser_date=$(ls -l "$NVIM_PARSER" 2>/dev/null | awk '{print $6, $7, $8}' || echo "unknown")
    verbose_log "Parser: $NVIM_PARSER"
    verbose_log "Updated: $parser_date"
}

# Setup temp directory
setup_temp() {
    rm -rf "$TEMP_DIR"
    mkdir -p "$TEMP_DIR"
    verbose_log "Temp dir: $TEMP_DIR"
}

# Cleanup temp directory
cleanup_temp() {
    if [[ -d "$TEMP_DIR" ]]; then
        rm -rf "$TEMP_DIR"
    fi
}

# Run nvim headless indentation on a file
run_indent() {
    local input_file="$1"
    local output_file="$2"
    
    # Copy input to output location
    cp "$input_file" "$output_file"
    
    # Run nvim in headless mode to indent the file
    if ! nvim --headless "$output_file" \
        -c "set filetype=al" \
        -c "normal! gg=G" \
        -c "wq" 2>/dev/null; then
        return 1
    fi
    
    return 0
}

# Compare two files and return diff stats
compare_files() {
    local expected="$1"
    local actual="$2"
    local test_name="$3"
    
    if ! diff -q "$expected" "$actual" >/dev/null 2>&1; then
        # Files differ - count differences
        local diff_lines=$(diff -u "$expected" "$actual" | grep "^[-+]" | wc -l)
        local total_lines=$(wc -l < "$expected")
        
        echo "FAIL|$test_name|$diff_lines|$total_lines"
        
        if [[ "$VERBOSE" == true ]]; then
            echo ""
            log_warning "=== Diff for $test_name ==="
            diff -u "$expected" "$actual" | head -50
            echo ""
        fi
        
        return 1
    else
        local total_lines=$(wc -l < "$expected")
        echo "PASS|$test_name|0|$total_lines"
        return 0
    fi
}

# ============================================================================
# Test Functions
# ============================================================================

test_full_suite() {
    local test_name="Full Suite Test"
    local output="$TEMP_DIR/indent_test_suite_output.al"
    
    verbose_log "Running: $test_name (921 lines)"
    
    if ! run_indent "$FULL_SUITE_INPUT" "$output"; then
        echo "ERROR|$test_name|0|921"
        return 1
    fi
    
    compare_files "$FULL_SUITE_REF" "$output" "$test_name"
}

test_quick_suite() {
    local test_name="Quick Test"
    local output="$TEMP_DIR/quick_indent_test_output.al"
    local ref="$TEMP_DIR/quick_indent_test_ref.al"
    
    verbose_log "Running: $test_name (144 lines)"
    
    # For quick test, we use the input file as both input and reference
    # (it should be already correctly indented)
    cp "$QUICK_TEST_INPUT" "$ref"
    
    if ! run_indent "$QUICK_TEST_INPUT" "$output"; then
        echo "ERROR|$test_name|0|144"
        return 1
    fi
    
    compare_files "$ref" "$output" "$test_name"
}

test_idempotency() {
    local test_name="Idempotency Test"
    local output="$TEMP_DIR/idempotency_output.al"
    
    verbose_log "Running: $test_name (921 lines)"
    
    # Indent an already-indented file - should remain unchanged
    if ! run_indent "$FULL_SUITE_REF" "$output"; then
        echo "ERROR|$test_name|0|921"
        return 1
    fi
    
    compare_files "$FULL_SUITE_REF" "$output" "$test_name"
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    local start_time=$(date +%s)
    
    # Header
    log_bold "========================================"
    log_bold "AL Tree-sitter Indentation Tests"
    log_bold "========================================"
    echo ""
    
    # Environment check
    log_info "Environment:"
    check_nvim
    check_parser
    echo ""
    
    # Setup
    setup_temp
    trap cleanup_temp EXIT
    
    # Run tests
    log_info "Running Tests:"
    
    local results=()
    local failed_tests=()
    
    # Test 1: Full Suite
    result=$(test_full_suite)
    results+=("$result")
    if [[ "$result" =~ ^FAIL ]] || [[ "$result" =~ ^ERROR ]]; then
        failed_tests+=("Full Suite Test")
    fi
    
    # Test 2: Quick Test
    result=$(test_quick_suite)
    results+=("$result")
    if [[ "$result" =~ ^FAIL ]] || [[ "$result" =~ ^ERROR ]]; then
        failed_tests+=("Quick Test")
    fi
    
    # Test 3: Idempotency
    result=$(test_idempotency)
    results+=("$result")
    if [[ "$result" =~ ^FAIL ]] || [[ "$result" =~ ^ERROR ]]; then
        failed_tests+=("Idempotency Test")
    fi
    
    # Calculate statistics
    local total_tests=${#results[@]}
    local passed_tests=0
    local failed_tests_count=0
    local total_lines=0
    local total_diff_lines=0
    
    for result in "${results[@]}"; do
        IFS='|' read -r status name diff_lines lines <<< "$result"
        
        case $status in
            PASS)
                log_success "  [✓] $name ($lines lines)"
                ((passed_tests++))
                ;;
            FAIL)
                log_error "  [✗] $name ($diff_lines differences in $lines lines)"
                ((failed_tests_count++))
                total_diff_lines=$((total_diff_lines + diff_lines))
                ;;
            ERROR)
                log_error "  [✗] $name (ERROR: indent command failed)"
                ((failed_tests_count++))
                ;;
        esac
        
        total_lines=$((total_lines + lines))
    done
    
    # Calculate match rate
    local matching_lines=$((total_lines - total_diff_lines))
    local match_rate=0
    if [[ $total_lines -gt 0 ]]; then
        match_rate=$(awk "BEGIN {printf \"%.1f\", ($matching_lines / $total_lines) * 100}")
    fi
    
    # Summary
    echo ""
    log_info "Results:"
    echo "  Total Tests: $total_tests"
    echo "  Passed: ${GREEN}$passed_tests${RESET}"
    if [[ $failed_tests_count -gt 0 ]]; then
        echo "  Failed: ${RED}$failed_tests_count${RESET}"
    else
        echo "  Failed: $failed_tests_count"
    fi
    echo ""
    echo "  Lines Tested: $total_lines"
    echo "  Lines Matching: $matching_lines"
    if [[ $failed_tests_count -gt 0 ]]; then
        echo "  Lines Differing: ${RED}$total_diff_lines${RESET}"
    fi
    echo "  Match Rate: ${match_rate}%"
    
    # Timing
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    echo ""
    echo "  Duration: ${duration}s"
    
    # Final result
    echo ""
    log_bold "========================================"
    if [[ $failed_tests_count -eq 0 ]]; then
        log_success "✅ ALL TESTS PASSED"
        log_bold "========================================"
        exit 0
    else
        log_error "❌ SOME TESTS FAILED"
        log_bold "========================================"
        echo ""
        log_error "Failed tests:"
        for test in "${failed_tests[@]}"; do
            echo "  - $test"
        done
        echo ""
        log_info "Run with --verbose to see detailed diff output"
        exit 1
    fi
}

# Run main function
main
