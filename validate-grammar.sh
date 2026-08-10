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

# THE CAPTURE IDIOM, stated once — every step below that runs a tool and reads
# its exit status must use it.
#
#   OUT=$(cmd 2>&1) && STATUS=0 || STATUS=$?      # correct
#   OUT=$(cmd 2>&1); STATUS=$?                    # WRONG under `set -e`
#
# A bare `OUT=$(cmd)` assignment takes the exit status of the command
# substitution, so `set -e` (line 6) aborts the script *at the assignment* the
# moment the tool fails. The next line that reads `$?` never runs, the step's
# own tailored error message never prints, and every later step is skipped — so
# one failure hides all the others and the run tells you nothing about what
# broke. The script still exits non-zero, so this is not a false pass; it is a
# gate that cannot report. Five steps had this shape (2, 4, 5, 5b, 5c) and all
# five are fixed; Step 8 was fixed earlier and Step 5d uses the `if cmd; then`
# variant of the same thing. Do not add a sixth.

# `--full` is honoured wherever it appears, not only as $1.
RUN_FULL=0
for arg in "$@"; do
    case "$arg" in
        --full) RUN_FULL=1 ;;
    esac
done

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
TEST_OUTPUT=$(tree-sitter test 2>&1) && TEST_EXIT_CODE=0 || TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -eq 0 ]; then
    # Report the denominator, and fail if it cannot be read.
    #
    # The old extraction was `grep -oE '[0-9]+ (of [0-9]+ )?parsed)'`, which
    # hunts for the substring `parsed)`. `tree-sitter test` has never printed
    # that, so TOTAL_TESTS was always empty and this step printed a bare
    # "All tests passed" with no number — a pass over an unknown amount of work.
    # The real summary line is:
    #   Total parses: 1550; successful parses: 1550; failed parses: 0; …
    # An unreadable summary fails: without it there is no evidence that any test
    # ran, and "0 tests passed" must never look like "all tests passed".
    TOTAL_TESTS=$(echo "$TEST_OUTPUT" | sed -n 's/.*Total parses: *\([0-9][0-9]*\);.*/\1/p' | tail -1)
    FAILED_TESTS=$(echo "$TEST_OUTPUT" | sed -n 's/.*failed parses: *\([0-9][0-9]*\);.*/\1/p' | tail -1)

    if [ -z "$TOTAL_TESTS" ]; then
        print_error "Test suite exited 0 but its summary line could not be read — cannot confirm any test ran"
        echo "$TEST_OUTPUT" | tail -3
        VALIDATION_FAILED=1
    elif [ "$TOTAL_TESTS" -eq 0 ]; then
        print_error "Test suite ran 0 parses — the corpus is missing or was not discovered"
        VALIDATION_FAILED=1
    elif [ -n "$FAILED_TESTS" ] && [ "$FAILED_TESTS" -ne 0 ]; then
        print_error "Test suite exited 0 but reports $FAILED_TESTS failed parse(s) of $TOTAL_TESTS"
        VALIDATION_FAILED=1
    else
        print_success "All tests passed ($TOTAL_TESTS parses)"
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

# The census prints its denominator, so the denominator must be asserted. With
# no glob match the loop body still runs once on the literal string
# `test/corpus/*.txt`, `[ -f ]` is false, and the counter stays 0 — a renamed,
# moved or unmounted corpus directory then printed
# "No unexpected ERROR or MISSING nodes in 0 test files" and passed.
if [ "$TEST_FILE_COUNT" -eq 0 ]; then
    print_error "No test corpus files found — test/corpus/*.txt matched nothing, so nothing was censused"
    VALIDATION_FAILED=1
elif [ ${#ERROR_MISSING_FILES[@]} -eq 0 ]; then
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
    ORPHAN_OUTPUT=$(python3 tools/find_unused_definitions.py 2>&1) && ORPHAN_EXIT_CODE=0 || ORPHAN_EXIT_CODE=$?

    if [ $ORPHAN_EXIT_CODE -eq 0 ]; then
        # find_unused_definitions.py always exits 0 on a successful run, so the
        # verdict rests entirely on reading its report — which makes the read
        # itself the gate. Both numbers must be present and the denominator must
        # be non-zero. Previously a missing `Unused rules:` label fell through to
        # a bare `print_success`, so any drift in the tool's output format
        # silently turned this step into a pass.
        RULE_TOTAL=$(echo "$ORPHAN_OUTPUT" | sed -n 's/^ *Total rule definitions: *\([0-9][0-9]*\).*/\1/p' | head -1)
        UNUSED_COUNT=$(echo "$ORPHAN_OUTPUT" | sed -n 's/^ *Unused rules: *\([0-9][0-9]*\).*/\1/p' | head -1)

        if [ -z "$RULE_TOTAL" ] || [ -z "$UNUSED_COUNT" ]; then
            print_error "Orphan report unreadable — expected 'Total rule definitions: N' and 'Unused rules: N'"
            echo "$ORPHAN_OUTPUT" | head -15
            VALIDATION_FAILED=1
        elif [ "$RULE_TOTAL" -eq 0 ]; then
            print_error "Orphan detection examined 0 rule definitions — it cannot have checked anything"
            VALIDATION_FAILED=1
        elif [ "$UNUSED_COUNT" -ne 0 ]; then
            print_error "Found $UNUSED_COUNT orphaned rule(s) among $RULE_TOTAL rule definitions"
            echo "$ORPHAN_OUTPUT" | grep -A20 "Unused rules:" | head -20
            VALIDATION_FAILED=1
        else
            print_success "No orphaned rules among $RULE_TOTAL rule definitions"
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
    DUPLICATE_OUTPUT=$(python3 tools/analyze_duplicates.py 2>&1) && DUPLICATE_EXIT_CODE=0 || DUPLICATE_EXIT_CODE=$?

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
    FIELD_TYPES_OUTPUT=$(python3 tools/check-field-types.py 2>&1) && FIELD_TYPES_EXIT_CODE=0 || FIELD_TYPES_EXIT_CODE=$?

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
    # Two bugs stacked here: the bare assignment aborted the script under
    # `set -e` on a compile failure, and even without that, `if [ $? -eq 0 ]`
    # on the NEXT line read the status of the assignment rather than of the
    # compiler. Either way the "failed to compile" branch below was dead.
    FIELDWALK_OUTPUT=$("$FIELDWALK_CC" -O0 -o "$FIELDWALK_BIN" \
        tools/fieldwalk.c src/parser.c src/scanner.c "$FIELDWALK_TS_DIR/src/lib.c" \
        -I"$FIELDWALK_TS_DIR/include" -I"$FIELDWALK_TS_DIR/src" -Isrc 2>&1) \
        && FIELDWALK_EXIT_CODE=0 || FIELDWALK_EXIT_CODE=$?
    if [ "$FIELDWALK_EXIT_CODE" -eq 0 ]; then
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

# Step 6: Parse a real AL corpus (opt-in, --full)
#
# THIS STEP NEVER PARSED A FILE. Five independent defects, each of which alone
# makes it unable to fail — recorded so none of them comes back:
#
#   1. It invoked `./parse-al-parallel.sh` with NO ARGUMENTS. That script treats
#      a zero-argument call as a help request: it printed usage and exited 0.
#      So the whole step ran against usage text, never against AL.
#   2. `$( … | tail -5 )` — a pipeline's status is the LAST command's, so the
#      captured status was always `tail`'s 0. A crashed run was invisible.
#   3. `grep -q "Success rate:"` had NO `else`. When the string was absent —
#      which, per (1), was always — the check was skipped in silence and the
#      step passed.
#   4. A rate at or below the threshold called `print_warning`, which does not
#      set VALIDATION_FAILED. A *detected* 50% success rate still passed.
#   5. The threshold was 90% on a project that holds 100%: 1,382 broken files
#      out of 15,358 would have gone green.
#
# Now: real arguments, the script's own exit status, every number read and
# reconciled, and any shortfall fails. The rate is compared in tenths of a
# percent so there is no `bc` dependency (parse-al-parallel.sh deliberately
# avoids one, and prints exactly one decimal place).
#
# TRAILING SLASH ON THE CORPUS PATH IS LOAD-BEARING. BC.History is frequently a
# symlink or an NTFS junction, and `find BC.History -name '*.al'` does not
# descend into one — it yields 0 files — while `find BC.History/ …` yields all
# 15,358. Measured in this worktree, where BC.History is a junction.
#
# A corpus that is absent is an explicit, loud skip: BC.History is gitignored
# and a fresh clone does not have it. A corpus that is PRESENT and parses badly
# now fails the run.
print_header "Step 6: AL File Parsing Test (--full only)"
AL_PARSE_CORPUS="${AL_PARSE_CORPUS:-./BC.History/}"
AL_PARSE_MIN_TENTHS="${AL_PARSE_MIN_TENTHS:-1000}"   # 1000 = 100.0%, the project's recorded state

if [ "$RUN_FULL" -ne 1 ]; then
    echo "Skipping AL file parsing test (use --full to include)"
elif [ ! -f "parse-al-parallel.sh" ]; then
    print_error "parse-al-parallel.sh not found — --full was requested and cannot be honoured"
    VALIDATION_FAILED=1
elif [ ! -d "$AL_PARSE_CORPUS" ]; then
    print_warning "AL corpus not present ($AL_PARSE_CORPUS) — skipping; set AL_PARSE_CORPUS to point at one"
else
    echo "Parsing $AL_PARSE_CORPUS ..."
    PARSE_OUTPUT=$(./parse-al-parallel.sh "$AL_PARSE_CORPUS" . 2>&1) && PARSE_EXIT_CODE=0 || PARSE_EXIT_CODE=$?
    echo "$PARSE_OUTPUT" | tail -12

    PARSE_TOTAL=$(echo "$PARSE_OUTPUT" | sed -n 's/^Total files *: *\([0-9][0-9]*\).*/\1/p' | tail -1)
    PARSE_OK=$(echo "$PARSE_OUTPUT"    | sed -n 's/^Parsed OK *: *\([0-9][0-9]*\).*/\1/p'   | tail -1)
    PARSE_ERR=$(echo "$PARSE_OUTPUT"   | sed -n 's/^Errors *: *\([0-9][0-9]*\).*/\1/p'      | tail -1)
    # Tenths: "100.0%" -> 1000. A summary without the decimal place does not
    # match and lands in the unreadable branch below rather than yielding an
    # empty string that a later comparison would have swallowed.
    PARSE_RATE=$(echo "$PARSE_OUTPUT" | sed -n 's/^Success rate *: *\([0-9][0-9]*\)\.\([0-9]\)%.*/\1\2/p' | tail -1)

    if [ -z "$PARSE_TOTAL" ] || [ -z "$PARSE_OK" ] || [ -z "$PARSE_ERR" ] || [ -z "$PARSE_RATE" ]; then
        print_error "AL parse run produced no readable summary (exit $PARSE_EXIT_CODE) — it did not parse the corpus"
        echo "$PARSE_OUTPUT" | tail -20
        VALIDATION_FAILED=1
    elif [ "$PARSE_TOTAL" -eq 0 ]; then
        print_error "AL parse run examined 0 files under $AL_PARSE_CORPUS (symlinked corpus needs a trailing slash)"
        VALIDATION_FAILED=1
    elif [ $(( PARSE_OK + PARSE_ERR )) -ne "$PARSE_TOTAL" ]; then
        print_error "AL parse counts do not reconcile: $PARSE_OK parsed + $PARSE_ERR errors != $PARSE_TOTAL files"
        VALIDATION_FAILED=1
    elif [ "$PARSE_EXIT_CODE" -ne 0 ] || [ "$PARSE_ERR" -ne 0 ]; then
        print_error "AL parsing failed: $PARSE_ERR error file(s) of $PARSE_TOTAL (parse-al-parallel.sh exit $PARSE_EXIT_CODE)"
        VALIDATION_FAILED=1
    elif [ "$PARSE_RATE" -lt "$AL_PARSE_MIN_TENTHS" ]; then
        print_error "AL parsing success rate ${PARSE_RATE%?}.${PARSE_RATE: -1}% is below the ${AL_PARSE_MIN_TENTHS%?}.${AL_PARSE_MIN_TENTHS: -1}% floor"
        VALIDATION_FAILED=1
    else
        print_success "AL parsing: $PARSE_OK/$PARSE_TOTAL files parsed, 0 errors (${PARSE_RATE%?}.${PARSE_RATE: -1}%)"
    fi
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