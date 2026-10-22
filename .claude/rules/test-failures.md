# Test Failure Patterns

## Common Patterns

| Pattern | Symptom | Fix |
|---------|---------|-----|
| **Missing construct** | ERROR nodes | Add rule to `_body_element` or relevant choice list |
| **Case-sensitivity** | Keywords not matching | Use `kw()` (never `kwCases()` → `kw()`, see contextual-keywords.md) |
| **Preprocessor splits** | MISSING tokens in `#if` contexts | Add dedicated `preproc_split_*` rule; confirm alc accepts the shape with `tools.alc_probe` first |
| **Complex property syntax** | Property value fails to parse | Add dedicated complex property rule (`docs/property-families.md`) |
| **Keyword as identifier** | Variable name conflicts with keyword | Add to `keyword_as_identifier` choice list — as a bare `kw('x')`, never `$.x_keyword` |
| **Structural mismatch** | Different node structure in tests | Update tests with `-u` if parsing is correct (no ERRORs) and the diff is explained |

## When to Update vs Fix

| Action | Condition |
|--------|-----------|
| **Update tests** (`-u`) | Grammar correct, tree structure evolved, no ERROR/MISSING nodes, every hunk of the diff traced to your change (`CLAUDE.md`, the five `-u` traps) |
| **Fix grammar** | ERROR or MISSING nodes present in parse output, or `has_error` true |

## Test Guidelines

- **Never delete or disable test files**; fix the underlying issue. validate-grammar.sh refuses a disabled test.
- After adding fixtures, confirm the suite total moved by exactly the number of cases you wrote (two corpus-format traps drop a case silently).
- **BC.History (15,358 files) is the real validation gate**; tests are a development aid.
- A deliberate negative (input alc rejects) is listed in `tools/deliberate-negatives.txt` and uses the corpus `:error` attribute rather than a pinned recovery tree.
- When stuck, `docs/deferred-work.md` records what was tried and measured; `.claude/rules/debugging.md` has the workflow.
