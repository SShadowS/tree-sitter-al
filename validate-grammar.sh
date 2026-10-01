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

# clang-cl as CC on Windows when LLVM is installed and CC is unset; see the file.
. "$(dirname "$0")/tools/default-cc.sh"

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

# Step 2b: Every declared corpus case must actually RUN, and every corpus file
# must be visible to git.
#
# Both of these are silent. Nothing else in this script, in CI, or in
# release.md compares the number of cases the corpus DECLARES with the number
# tree-sitter RUNS, or the files on disk with the files in the index. Each has
# already shipped a defect:
#
#   * test/corpus/built_in_functions_al.txt had a well-formed ==== header and
#     110 lines of AL and NO `---` divider. tree-sitter parses the header and
#     discards the case without a word. It had never run once since the day it
#     was added. The only symptom was a raw header count sitting +1 above the
#     suite total, at every revision.
#   * test/corpus/property_comment_parameters_extended_test.txt was matched by
#     an unanchored `property_*.txt` in .gitignore. Ignored files do not appear
#     in `git status`, so the suite ran 3 extra cases for whoever had the file
#     on disk and skipped them in every fresh worktree — which is how one
#     branch measured 1562 while two others measured 1559 at the same commit.
#
# tools/count_corpus_cases.py is a SECOND implementation of tree-sitter's
# header/divider parsing on purpose. A count derived from the code that does
# the dropping cannot detect the dropping.
print_header "Step 2b: Corpus Case and File Census"
CASE_CENSUS=$(python tools/count_corpus_cases.py test/corpus 2>&1) && CENSUS_EXIT=0 || CENSUS_EXIT=$?

if [ "$CENSUS_EXIT" -eq 2 ] || [ -z "$CASE_CENSUS" ]; then
    print_error "Corpus census could not run — test/corpus missing or the counter failed"
    echo "$CASE_CENSUS" | head -5
    VALIDATION_FAILED=1
else
    DECLARED_CASES=$(echo "$CASE_CENSUS" | sed -n 's/^runnable_cases=\([0-9][0-9]*\)$/\1/p')
    DROPPED_CASES=$(echo "$CASE_CENSUS" | sed -n 's/^dropped_cases=\([0-9][0-9]*\)$/\1/p')
    SKIPPED_CASES=$(echo "$CASE_CENSUS" | sed -n 's/^skipped_cases=\([0-9][0-9]*\)$/\1/p')

    if [ "$CENSUS_EXIT" -ne 0 ]; then
        if [ "${DROPPED_CASES:-0}" -gt 0 ] || echo "$CASE_CENSUS" | grep -q '^DROPPED'; then
            print_error "Corpus case(s) declared but unable to run:"
            echo "$CASE_CENSUS" | grep '^DROPPED' | sed 's/^DROPPED\t/    /' | sed 's/\t/ — /g'
            echo -e "${YELLOW}A case with no '---' divider, or a blank line inside its ==== header,${NC}"
            echo -e "${YELLOW}is dropped silently. Fix the fixture; do not adjust this check.${NC}"
        fi
        if [ "${SKIPPED_CASES:-0}" -gt 0 ]; then
            print_error "$SKIPPED_CASES corpus case(s) carry :skip — a disabled test:"
            echo "$CASE_CENSUS" | grep '^SKIPPED' | sed 's/^SKIPPED\t/    /' | sed 's/\t/ — /g'
            # This is NOT a counter bug. `:skip` is a real tree-sitter feature and
            # the arithmetic below is correct without it. It fails here because
            # CLAUDE.md's "no known limitations" rule forbids disabling a test
            # instead of fixing what it caught. Delete the `:skip`, do not teach
            # this step to tolerate it.
            echo -e "${YELLOW}CLAUDE.md forbids disabling tests — fix the underlying issue instead.${NC}"
        fi
        VALIDATION_FAILED=1
    # Only meaningful when Step 2 produced a total to compare against.
    elif [ -n "$TOTAL_TESTS" ] && [ -n "$DECLARED_CASES" ] && [ "$TOTAL_TESTS" -ne "$DECLARED_CASES" ]; then
        print_error "Corpus declares $DECLARED_CASES runnable case(s) but the suite ran $TOTAL_TESTS"
        echo -e "${YELLOW}These must agree. A shortfall means cases are being dropped by a${NC}"
        echo -e "${YELLOW}mechanism this counter does not model yet — find it, do not paper over it.${NC}"
        VALIDATION_FAILED=1
    else
        print_success "Declared cases match cases run ($DECLARED_CASES)"
    fi

    # Files on disk vs files in the index. A single-digit gap is the whole bug.
    #
    # This needs a git work tree. tools/gate_selftest.py copies the files a gate
    # reads into a bare temp directory WITHOUT .git, on purpose, so a case
    # cannot reach the real repo — `git ls-files` there reports nothing and
    # every file would look untracked. That must not fail the run, and it must
    # not silently pass either: an unrunnable check reports as a WARNING so it
    # can never be mistaken for a census that found nothing wrong.
    CORPUS_ON_DISK=$(find test/corpus -name '*.txt' | wc -l | tr -d ' ')
    if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        print_warning "Corpus file census SKIPPED — not a git work tree (expected under gate_selftest); $CORPUS_ON_DISK file(s) on disk"
        CORPUS_TRACKED="$CORPUS_ON_DISK"
    else
        CORPUS_TRACKED=$(git ls-files test/corpus | grep -c '\.txt$' || true)
        # A scratch COPY of the repo can sit inside the real work tree — which is
        # exactly where gate_selftest.py puts one on a CI runner. `git rev-parse`
        # then says yes while `git ls-files` resolves against the copy's path and
        # returns NOTHING, so a perfectly good corpus reads as 0 tracked and this
        # step fails for a reason that is not a defect. Zero tracked beside a
        # non-empty disk means "not the real checkout", never "every file is
        # untracked": no clone of this repo has ever had an empty index here.
        if [ "$CORPUS_TRACKED" -eq 0 ] && [ "$CORPUS_ON_DISK" -gt 0 ]; then
            print_warning "Corpus file census SKIPPED — 0 tracked beside $CORPUS_ON_DISK on disk, so this is a copy outside the index (expected under gate_selftest)"
            CORPUS_TRACKED="$CORPUS_ON_DISK"
        fi
    fi
    if [ "$CORPUS_ON_DISK" -ne "$CORPUS_TRACKED" ]; then
        print_error "test/corpus has $CORPUS_ON_DISK .txt file(s) on disk but $CORPUS_TRACKED tracked by git"
        git ls-files --others --exclude-standard test/corpus/ | sed 's/^/    untracked: /'
        git ls-files --others --ignored --exclude-standard test/corpus/ | sed 's/^/    IGNORED:   /'
        echo -e "${YELLOW}An ignored corpus file runs for whoever has it and for nobody else.${NC}"
        VALIDATION_FAILED=1
    else
        print_success "All $CORPUS_ON_DISK corpus file(s) on disk are tracked by git"
    fi
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
# The list lives in ONE file, tools/deliberate-negatives.txt, with a reason per
# entry. This step, tools/has_error_sweep.py (Step 3b) and the pre-flight grep
# in .claude/commands/release.md all read it, so they cannot exempt different
# sets. Matching is on exact basename. An unreadable or empty list fails: an
# empty exemption set would be read as "every negative fixture is a defect",
# and a missing file is a broken checkout.
DELIBERATE_NEGATIVES_FILE="tools/deliberate-negatives.txt"
DELIBERATE_ERROR_FIXTURES=()
if [ -f "$DELIBERATE_NEGATIVES_FILE" ]; then
    while IFS= read -r line; do
        line="${line%$'\r'}"
        case "$line" in ''|'#'*) continue ;; esac
        DELIBERATE_ERROR_FIXTURES+=("$line")
    done < "$DELIBERATE_NEGATIVES_FILE"
fi
if [ ${#DELIBERATE_ERROR_FIXTURES[@]} -eq 0 ]; then
    print_error "$DELIBERATE_NEGATIVES_FILE is missing or lists nothing -- it is tracked in git, so this checkout is broken"
    VALIDATION_FAILED=1
fi

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

# Search for ERROR or MISSING in test corpus files as parse tree NODES, never as
# AL source text.
#
# BOTH alternatives require the opening paren, and the pattern is deliberately
# NOT anchored to the line start. This is the same search `.claude/commands/
# release.md` pre-flight #3 runs; the two gates must agree on what counts as a
# hit, so keep them identical.
#
# The previous pattern was `^\s*\((ERROR|MISSING)|^\s*(ERROR|MISSING)[^(]` and
# was wrong in both directions:
#
#   * The second alternative matched a BARE word at line start, so a prose line
#     reading "ERROR node and full byte coverage are separate claims" failed the
#     gate. Expected trees always write `(ERROR)` and `(MISSING xyz)`, so
#     requiring the paren removes that false-positive class outright.
#   * The line-start anchor missed a real nested node on a populated line:
#     `(source (statement) (ERROR))` was invisible to this gate while
#     release.md caught it. Dropping the anchor closes that false negative.
#
# `ERROR(` — the AL function call — still does not match, because the paren must
# come BEFORE the word, and the comparison is case-sensitive.
ERROR_NODE_PATTERN='\((ERROR|MISSING)\b'
for test_file in test/corpus/*.txt; do
    if [ -f "$test_file" ]; then
        TEST_FILE_COUNT=$((TEST_FILE_COUNT + 1))
        if is_deliberate_error_fixture "$test_file"; then
            continue
        fi
        if grep -qE "$ERROR_NODE_PATTERN" "$test_file"; then
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
        grep -n -m 1 -E "$ERROR_NODE_PATTERN" "$file" | sed 's/^/    /'
    done
    VALIDATION_FAILED=1
    echo -e "\n${YELLOW}These test files contain ERROR or MISSING nodes, indicating incomplete parsing.${NC}"
    echo -e "${YELLOW}This is a serious issue that should be fixed.${NC}"
fi

# Step 3b: has_error over every corpus case
#
# A MISSING node for a HIDDEN (`_`-prefixed) token is not printed by
# `tree-sitter parse`, and `--json-summary` reports the file successful, so
# parse-al-parallel.sh (Step 6) cannot see it. `tree-sitter test` (Step 2) does
# print `(MISSING _x)` -- but only for a case that holds the triggering input.
# py-tree-sitter's `root_node.has_error` sees it everywhere. The `_directive_eol`
# whitespace regression (fixed in 673528e; docs/deferred-work.md item 12) passed
# parse-al-parallel.sh that way. tools/has_error_sweep.py parses EVERY corpus
# case; a case in a deliberate-negative file may be `visible` (its ERROR is the
# assertion), but a hidden error fails everywhere. Exit 2 (it could not run -- a
# failed build, no fixtures, a crash) fails too.
#
# The count is reconciled, not just printed: the sweep's `files=` must equal the
# number the step above established independently (Step 2b's declared cases for
# 3b, Step 6's parsed files for 6b). A reader that silently drops inputs would
# otherwise report clean over fewer of them.
run_has_error_sweep() {
    local what="$1" expected="$2"; shift 2
    local out status swept
    out=$(python tools/has_error_sweep.py "$@" 2>&1) && status=0 || status=$?
    swept=$(echo "$out" | sed -n 's/^has_error_sweep: files=\([0-9][0-9]*\) .*/\1/p' | tail -1)
    if [ "$status" -eq 0 ] || [ "$status" -eq 1 ]; then
        if [ -z "$expected" ] || [ -z "$swept" ] || [ "$swept" -ne "$expected" ]; then
            print_error "has_error sweep over $what examined ${swept:-an unreadable number of} input(s), expected ${expected:-<no count to reconcile against>}"
            VALIDATION_FAILED=1
        fi
    fi
    if [ "$status" -eq 0 ]; then
        print_success "has_error: $(echo "$out" | tail -1 | sed 's/^has_error_sweep: //') in $what"
    elif [ "$status" -eq 1 ]; then
        print_error "has_error sweep found parse errors in $what"
        echo "$out" | grep -E '^(visible|hidden-only)'$'\t' | head -20 | sed 's/^/    /'
        echo "$out" | tail -1
        if echo "$out" | grep -qE '^hidden-only'$'\t''|'$'\t''hidden: '; then
            echo -e "${YELLOW}hidden: has_error is True under a node with no ERROR/MISSING a tree prints --${NC}"
            echo -e "${YELLOW}a MISSING hidden token inside it. tree-sitter parse and --json-summary cannot see it.${NC}"
        fi
        VALIDATION_FAILED=1
    else
        print_error "has_error sweep could not run over $what (exit $status)"
        echo "$out" | tail -5
        VALIDATION_FAILED=1
    fi
}

print_header "Step 3b: has_error Over Every Corpus Case"
run_has_error_sweep "the corpus fixtures" "$DECLARED_CASES" --corpus-fixtures

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
    # All five helper scripts are TRACKED in git. Their absence means a broken
    # checkout, not an environment without them -- and that is not hypothetical:
    # three of them were once untracked and a fresh clone degraded these steps to
    # exactly this warning, so the gates looked green while checking nothing. A
    # missing helper therefore FAILS. Genuine environment gaps (no C compiler, no
    # vendored runtime, no BC.History) stay warnings; a missing tracked file does not.
    print_error "Orphan detection script not found (tools/find_unused_definitions.py) -- it is tracked in git, so this checkout is broken"
    VALIDATION_FAILED=1
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
    print_error "Duplicate detection script not found (tools/analyze_duplicates.py) -- it is tracked in git, so this checkout is broken"
    VALIDATION_FAILED=1
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
    print_error "Field-shape check script not found (tools/check-field-types.py) -- it is tracked in git, so this checkout is broken"
    VALIDATION_FAILED=1
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
# gcc-style flags (-O0 -o) below, so a CC that tools/default-cc.sh chose
# (clang-cl) is ignored here; only a caller's explicit CC is honoured.
if [ -n "${TS_AL_DEFAULT_CC:-}" ] && [ "${CC:-}" = "$TS_AL_DEFAULT_CC" ]; then
    FIELDWALK_CC=cc
else
    FIELDWALK_CC="${CC:-cc}"
fi
command -v "$FIELDWALK_CC" >/dev/null 2>&1 || FIELDWALK_CC=gcc

if [ ! -f "tools/fieldwalk.c" ]; then
    print_error "fieldwalk not found (tools/fieldwalk.c) -- it is tracked in git, so this checkout is broken"
    VALIDATION_FAILED=1
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

# Step 5e: Config-oracle quick tier
#
# Needs no corpus, so it runs on every clone and never skips. Three stages, each
# reported on its own line: (a) the registry census over src/node-types.json,
# (b) the oracle's self-tests, (c) the fixture differential over test/corpus.
# Exit 1 is a finding (discrepancy, representation violation, stale
# fixture-classes.tsv entry, census problem); exit 2 means it could not run.
# Both fail validation. The full tier over the production corpora is NOT here
# yet (roadmap C3; docs/deferred-work.md item 14).
print_header "Step 5e: Config-Oracle Quick Tier"
if python -m tools.config_oracle run --tier quick; then
    oracle_status=0
else
    oracle_status=$?
fi
if [ "$oracle_status" -eq 0 ]; then
    print_success "config oracle quick tier: clean (census, self-tests, fixture differential)"
else
    print_error "config oracle quick tier failed (exit $oracle_status) — see tools/config_oracle/reports/summary.md"
    VALIDATION_FAILED=1
fi

# Step 5f: Traversal-policy census (roadmap F0)
#
# traversal/policy.json classifies every node type that is not ordinary, for the
# traversal helpers in every binding (docs/traversal.md). tools/traversal_census.py
# fails when the grammar or the contracts registry moved and the policy did not.
# Needs no parser, so it never skips. Exit 1 is a finding, 2 could not run; both
# fail validation.
print_header "Step 5f: Traversal Policy Census"
if CENSUS_OUTPUT=$(python tools/traversal_census.py 2>&1); then
    print_success "traversal policy census: clean"
else
    census_status=$?
    print_error "traversal census failed (exit $census_status)"
    echo "$CENSUS_OUTPUT"
    VALIDATION_FAILED=1
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
    # parse-al-parallel.sh writes parsed.txt/errors.txt into its CORPUS
    # directory by default, which is what `.claude/rules/debugging.md` and
    # /iterate expect of a direct invocation. It is the wrong place for this
    # step: in a worktree, BC.History is an NTFS junction into the main
    # checkout, so --full would drop two files into someone else's repo while
    # they are working in it. Send them somewhere disposable instead; the lists
    # are reproducible by running the script directly.
    AL_PARSE_OUT=$(mktemp -d)
    echo "Parsing $AL_PARSE_CORPUS ..."
    PARSE_OUTPUT=$(PARSE_OUT_DIR="$AL_PARSE_OUT" ./parse-al-parallel.sh "$AL_PARSE_CORPUS" . 2>&1) \
        && PARSE_EXIT_CODE=0 || PARSE_EXIT_CODE=$?
    rm -rf "$AL_PARSE_OUT"
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

    # Step 6b: the same corpus through has_error. parse-al-parallel.sh counts
    # `--json-summary` records, and a MISSING node for a HIDDEN token leaves
    # `successful: true` -- see Step 3b. Only has_error sees that file. Its
    # `files=` must equal Step 6's total.
    print_header "Step 6b: has_error Over the AL Corpus (--full only)"
    run_has_error_sweep "$AL_PARSE_CORPUS" "$PARSE_TOTAL" --root "$AL_PARSE_CORPUS"
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
    print_error "Health check script not found (tools/check_grammar_health.py) -- it is tracked in git, so this checkout is broken"
    VALIDATION_FAILED=1
fi

# Step 9: Is the committed wasm built from the committed sources?
#
# The release workflow ships tree-sitter-al.wasm verbatim (`cp` -- it never
# builds it), so a stale file here is a stale parser for every web-tree-sitter
# consumer. It went stale once already between v4.0.0 and the next grammar fix,
# and no other gate could see it because nothing in this suite loads the wasm.
print_header "Step 9: WASM Freshness"
if [ -x "tools/check-wasm-fresh.sh" ]; then
    if WASM_OUTPUT=$(./tools/check-wasm-fresh.sh 2>&1); then
        print_success "Committed wasm matches src/parser.c and src/scanner.c"
    else
        print_error "Committed wasm is stale"
        echo "$WASM_OUTPUT"
        VALIDATION_FAILED=1
    fi
else
    print_error "tools/check-wasm-fresh.sh not found or not executable -- it is tracked in git, so this checkout is broken"
    VALIDATION_FAILED=1
fi

# Step 10: Tracked scripts carry the executable bit
#
# Developed on Windows with core.fileMode=false, so a script's mode in the git
# index is invisible here and only bites on Linux -- where CI runs. A 100644
# script exec'd directly fails there with "Permission denied" (exit 126) and
# works here; a 100644 shim on PATH is not found at all. It happened to
# tools/check-wasm-fresh.sh (bed960a) and then to parse-al-parallel.sh,
# tools/ts-lock.sh and two gate fixtures, which is why the gate self-test job
# had never once passed in CI. tools/check-exec-bits.sh reads the INDEX, so it
# answers the same on every platform. Invoked through `bash` deliberately: the
# one file that must not be able to hide its own missing bit is this checker.
print_header "Step 10: Executable Bits"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    if EXEC_OUTPUT=$(bash tools/check-exec-bits.sh 2>&1); then
        print_success "Every tracked script is 100755 in the index"
    else
        print_error "Tracked script(s) without the executable bit in the index"
        echo "$EXEC_OUTPUT"
        VALIDATION_FAILED=1
    fi
else
    print_warning "Not a git checkout (a scratch copy) -- skipping the executable-bit check; it runs in the real repo and in CI"
fi

# Step 11: Declared tree-sitter runtime ranges can load the grammar's ABI
#
# src/parser.c is ABI 15, which needs a tree-sitter runtime >= 0.25 in every
# binding. pyproject's `core = ["tree-sitter~=0.24"]` admitted 0.24.0 (ABI 13..14),
# so `pip install tree-sitter-al[core]` could resolve to a runtime that refuses to
# load the grammar, and nothing here noticed. tools/check-runtime-ranges.py maps
# every declared range (every pyproject list, requirements files, the npm
# tree-sitter and web-tree-sitter entries, Cargo, go.mod, Package.swift) onto a
# hand-maintained runtime -> ABI table. Exit 1 is a range
# admitting an incompatible runtime; exit 2 is an unreadable range or manifest.
# Both fail validation.
print_header "Step 11: Runtime Ranges vs. Grammar ABI"
if RANGE_OUTPUT=$(python tools/check-runtime-ranges.py 2>&1); then
    print_success "Every declared runtime range loads the grammar's ABI"
else
    range_status=$?
    print_error "Declared runtime range check failed (exit $range_status)"
    echo "$RANGE_OUTPUT"
    VALIDATION_FAILED=1
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