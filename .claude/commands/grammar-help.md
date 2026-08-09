# Grammar Development Help

Available validation commands:

| Command | Description |
|---------|-------------|
| `/validate` | Full validation (generate, test, health check, analysis) |
| `/quick-validate` | Fast validation (generate + test only) |
| `/save-baseline` | Save current state as baseline for regression detection |
| `/debug-test <pattern>` | Debug a specific failing test |

## Manual Commands

```bash
# Generate parser
tree-sitter generate

# Run all tests
tree-sitter test

# Run specific test
tree-sitter test -i "test name pattern"

# Health check
python3 tools/check_grammar_health.py

# Find unused rules
python3 tools/find_unused_definitions.py

# Find duplicate rule keys in grammar.js's rules object
python3 tools/analyze_duplicates.py

# Full validation script
./validate-grammar.sh
```

## Common Workflows

### After making grammar changes:
1. `/quick-validate` - fast feedback
2. If passing: `/validate` - full check
3. If all good: `/save-baseline` - update baseline

### Debugging a test failure:
1. `/debug-test "test name"` - get detailed analysis
2. Read the test file in `test/corpus/`
3. Check grammar.js for the relevant rules

### Before committing:
1. `/validate` - ensure no regressions
2. Check for any warnings or issues
