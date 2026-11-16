# Parse Failure Debugging

## Quick Workflow

```bash
# 1. Isolate the construct and parse it alone: fields, has_error, every ERROR/MISSING/hidden
python tools/snip.py 'x := a + 1;'          # --object wraps it in an object; --sexp for a fixture

# 2. Parse the whole file with the CLI debug log
./tools/ts-lock.sh tree-sitter parse file.al -d > debug.log 2>&1
#    -D writes log.html (parse graph); the last states before the ERROR are the ones to read
```

Expected ERROR trees for a fixture come from the CLI, never from `snip` (py-tree-sitter 0.25
and the 0.27 CLI recover differently; `CLAUDE.md`, "Gates that catch what the obvious check misses").

## Error Research Agent

For systematic analysis of parse failures, use the `error-research` agent: it categorizes
error patterns across many files, identifies root causes and prioritizes fixes by impact.
`tree-sitter-pattern-investigator` is the deep single-pattern investigation.

## Batch Error Analysis

```bash
# Run full production parse
./parse-al-parallel.sh ./BC.History/ .

# Check error list
cat ./BC.History/errors.txt

# Parse specific error files
head -10 ./BC.History/errors.txt | while IFS= read -r f; do
  echo "=== $(basename "$f") ==="
  ./tools/ts-lock.sh tree-sitter parse "$f" 2>&1 | grep -E "ERROR|MISSING" | head -3
done

# A clean error count is not a clean file: hidden MISSING tokens need this
python tools/has_error_sweep.py --root ./BC.History/
```

## Debugging Process

1. Isolate the failing construct, test it in minimal context (`tools/snip.py`).
2. Check whether a rule for it exists in `grammar.js` (`grep`, `python tools/nodetypes.py who-has TYPE`).
3. Test with precedence if it is a parser-state issue; `tree-sitter generate --report-states-for-rule -` ranks rules by state cost.
4. For `#if` shapes, confirm what alc accepts first: `python -m tools.alc_probe run probe.al` (`CLAUDE.md`, "Validating AL Syntax Questions").
5. Update expectations (`-u`) only if no ERROR/MISSING nodes remain, and read the diff (`CLAUDE.md`, the five `-u` traps).

Traps that hide a misparse or a cause:

- **Optional separators absorb misparses.** `repeat(seq(X, optional(SEP)))` lets two adjacent `X` stand with no separator, so a wrong parse becomes an extra element instead of an error (live in `_case_pattern_item`, about 9 more comma sites share the shape). Suspect it when a misparse leaves a clean error count.
- **Rust regex has no zero-width assertions.** `kw()` and every `new RustRegex(...)` in `grammar.js` must avoid `\b` and lookahead (`tree-sitter generate` fails with `Unexpected rule ExpandRegex(Assertion)`): use a negated character class for a word boundary.
- **A site list derived by reading is usually short.** `grep -n` the whole file before calling a list complete.
- **A figure carries its source.** A tool-derived aggregate beside a hand-derived breakdown lends the breakdown its authority (`071fbd4` published `gaps=3895` right beside three invented per-category counts); take every number in a sentence from the tool, never derive a delta by subtracting from a remembered base, and state the scope (manifest or corpus).

Known limits and open items are in `docs/deferred-work.md`; check it before calling a pattern
impossible (`CLAUDE.md`, "Known limits are recorded, not denied").
