# Definition of done

Run under `./tools/ts-lock.sh` (see `mem:suggested_commands`), in this order — cheapest
discriminating check first:

```bash
./tools/ts-lock.sh tree-sitter generate
./tools/ts-lock.sh tree-sitter test
./tools/ts-lock.sh python -m pytest tools/query_coverage/tests -q
./tools/ts-lock.sh python -m tools.query_coverage.qc run
./tools/ts-lock.sh ./parse-al-parallel.sh ./BC.History/ .
./tools/ts-lock.sh ./validate-grammar.sh
```

pytest is listed separately because **`validate-grammar.sh` does not run it** and CI does.

## Required of any grammar change

- **A corpus fixture pinning the SHAPE**, not an error count. BC.History has been at 0
  errors both before and after every silent-misparse defect found, so the corpus cannot
  see this class. Prove the fixture can fail by mutating the expectation.
- Confirm the suite total moved by **exactly** the number of cases written.
- If the change alters attachment without changing node types or byte spans, diff the
  `(parent, field, child)` edge census before and after — nothing else sees it.
- Stage `src/parser.c`, `src/grammar.json`, `src/node-types.json` **as a set**.
- Commit message carries the error count, e.g. `[BC.History: 0 errors, 100% success]`.

## Merging branches

Every pair of grammar branches conflicts in `src/parser.c` only. `src/grammar.json` and
`src/node-types.json` **auto-merge cleanly, and that is worse than a conflict** — git
splices two grammars' JSON into a file neither grammar produces. After every merge,
regenerate and take the **regenerated** copies of all three, never the merged ones.

`tools/query_coverage/baseline.json` needs deliberate resolution: all streams ratchet
it. Run `qc run` immediately after the final regenerate and **before** committing the
baseline — an inflated count committed without a run in between silently absorbs any
later regression that lands beneath it.

## Philosophy

No known limitations. Do not disable a test or file an issue as unsolvable. Study
`other-languages/` for how another parser handled the same construct.
