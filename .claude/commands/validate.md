# Grammar Validation Agent

You are a grammar validation agent for tree-sitter-al. Run comprehensive validation and report results clearly.

## Validation Steps

Run these steps in order, collecting results:

### Step 1: Generate Parser
```bash
tree-sitter generate 2>&1
```
- Check for warnings about unnecessary conflicts
- Report any generation errors

### Step 2: Run Test Suite
```bash
tree-sitter test 2>&1
```
- Count passed and failed tests
- List any failing test names

### Step 3: Health Check (Regression Detection)
```bash
python3 tools/check_grammar_health.py 2>&1
```
- Compare current state to baseline
- Report any regressions or improvements

### Step 4: Unused Definitions
```bash
python3 tools/find_unused_definitions.py 2>&1
```
- Report unused rules (potential dead code)
- Report low-usage rules that may need review

### Step 5: Duplicate Rule Keys
```bash
python3 tools/analyze_duplicates.py 2>&1
```
- Report grammar.js rule keys defined more than once in `rules: { ... }`
- Distinguishes byte-identical duplicates (dead weight) from differing ones
  (a live bug: JavaScript silently discards the earlier definition)

### Step 6: ERROR/MISSING Nodes in Tests
```bash
grep -r -l "^\s*(ERROR\|^\s*(MISSING" test/corpus/*.txt 2>/dev/null || echo "None found"
```
- List test files containing ERROR or MISSING nodes
- These indicate parsing issues

## Output Format

Provide a clear summary in this format:

```
## Grammar Validation Report

### Generation: ✅/❌
- [details]

### Tests: ✅/⚠️/❌
- Passed: X
- Failed: Y
- [list failing tests if any]

### Health Check: ✅/⚠️/❌
- [regressions or improvements]

### Code Quality: ✅/⚠️
- Unused rules: X
- Duplicate rule keys: Y

### Action Items
1. [prioritized list of issues to fix]
```

## After Validation

If all checks pass, suggest:
- Running `python3 tools/check_grammar_health.py --save-baseline` if changes were made

If checks fail, prioritize:
1. Fix test failures first
2. Then address health check regressions
3. Finally clean up unused rules
