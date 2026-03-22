# Test Failure Patterns

## Common Patterns

| Pattern | Symptom | Fix |
|---------|---------|-----|
| **Missing construct** | ERROR nodes | Add rule to `_body_element` or relevant choice list |
| **Case-sensitivity** | Keywords not matching | Use `kw()` or explicit `choice()` with case variants |
| **Preprocessor splits** | MISSING tokens in #if contexts | Add dedicated `preproc_split_*` rule |
| **Complex property syntax** | Property value fails to parse | Add dedicated complex property rule |
| **Keyword as identifier** | Variable name conflicts with keyword | Add to `keyword_as_identifier` choice list |
| **Structural mismatch** | Different node structure in tests | Update tests with `-u` if parsing is correct (no ERRORs) |

## When to Update vs Fix

| Action | Condition |
|--------|-----------|
| **Update tests** (`-u`) | Grammar correct, tree structure evolved, no ERROR/MISSING nodes |
| **Fix grammar** | ERROR or MISSING nodes present in parse output |

## Test Guidelines

- **Never delete or disable test files** — fix the underlying issue
- Use `tree-sitter test -u` only if no ERROR/MISSING nodes exist
- **BC.History (15,358 files) is the real validation gate** — tests are a development aid
- When stuck, study similar patterns in `other-languages/` parsers

## Debugging

```bash
# Parse with debug output
tree-sitter parse file.al -d > debug.log 2>&1

# Analyze with bug finder
python parse_bug_finder.py file.al debug.log
```
