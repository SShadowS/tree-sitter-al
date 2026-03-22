# Parse Failure Debugging

## Quick Workflow

```bash
# 1. Parse with debug output
tree-sitter parse file.al -d > debug.log 2>&1

# 2. Analyze with bug finder
python parse_bug_finder.py file.al debug.log
```

## Error Research Agent

For systematic analysis of parse failures, use the `error-research` agent:
- Analyzes failing files after validation reveals errors
- Categorizes error patterns across multiple files
- Identifies root causes and prioritizes fixes by impact

## Batch Error Analysis

```bash
# Run full production parse
./parse-al-parallel.sh ./BC.History/ .

# Check error list
cat ./BC.History/errors.txt

# Parse specific error files
head -10 ./BC.History/errors.txt | while IFS= read -r f; do
  echo "=== $(basename "$f") ==="
  tree-sitter parse "$f" 2>&1 | grep -E "ERROR|MISSING" | head -3
done
```

## Debugging Process

1. Isolate failing construct, test in minimal context
2. Check if rule exists in grammar.js
3. Test with precedence if parser state issues
4. Use `parse_bug_finder.py` to analyze debug output
5. Update expectations (`-u`) only if no ERROR/MISSING nodes

## Philosophy: No Known Limitations

**Never give up on a failing pattern:**
- Don't disable tests or mark issues as "known limitations"
- Research how other parsers handle similar constructs in `other-languages/`
- Use `error-research` agent for systematic failure analysis
- Every "impossible" pattern has been solved somewhere — find it and adapt it
