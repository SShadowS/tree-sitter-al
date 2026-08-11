# Checks in this repo that have passed while being wrong

The dominant fault class here is **a check that returns the same answer whether the code
is right or wrong**. Every item below actually happened. When adding any gate, detector,
or fixture, first ask how it would look if it were broken — if the answer is "the same",
it is not a check.

## Test-suite traps

- **`tree-sitter test -u` writes NO field labels if the expectation it replaces had
  none.** Field comparison is all-or-nothing per file, so an unlabelled expected tree
  asserts *nothing* about fields and degrades silently. Generate expectations from
  `tree-sitter parse` output instead, and prove the fixture can fail by renaming a field
  to `bogus:`.
- **"No ERROR nodes" is not sufficient to accept a `-u` rewrite.** Read the whole diff
  and trace every hunk to your change. Five shipped fixtures were found asserting a
  defect as correct behaviour, all with clean error counts.
- **A blank line inside a `====` test header makes tree-sitter drop that case
  silently.** No warning. After adding fixtures, check the total moved by exactly the
  number written. Header blocks must be contiguous.
- **Detector unit tests that use the grammar's own defects as fixtures fail the moment
  someone fixes the grammar**, and cannot prove the detector works afterwards. Assert
  detector behaviour against synthetic input; keep one genuine end-to-end case.

## Gate traps

- **`validate-grammar.sh` does not run pytest.** "validate-grammar green" ≠ "repo green".
  CI's `query-coverage-selftest` job runs `python -m pytest tools/query_coverage/tests -q`
  and will fail on what the local gate never looked at.
- **The two ERROR/MISSING gates must exempt exactly the same set** —
  `validate-grammar.sh`'s `DELIBERATE_ERROR_FIXTURES` and the grep in
  `.claude/commands/release.md`. They have also drifted in *pattern*, not just in
  membership: one matched a bare word at line start and fired on a prose line beginning
  "ERROR", the other required `(ERROR`. An allow-list entry for a file that does not
  exist yet is inert, so carrying one early across branches is correct and free.
- `parse-al-parallel.sh` once reported `36/40 parsed, 90%` having opened **zero** files
  (broken path conversion). It now refuses to report a rate over an incomplete run.
- `validate-grammar.sh` once printed "All tests passed" and "0 test files" together.
- A release step once invoked `parse-al-parallel.sh` with **no arguments** — usage,
  exit 0, never parsed anything.

## Measurement traps

- **Always state the scope of a figure.** The qc manifest is 59 files chosen by
  set-cover and is far denser per file than real code; its counts do not scale. A
  published "3,895 byte gaps" was 574,694 at corpus scope, ~147x.
- **Two implementations of one census will disagree** and both can be right. The C
  binary and `detectors/edges.py` differ by 8 kinds on identical input purely in how an
  anonymous child is keyed. Never mix the two numbers in one comparison.
- **Redirecting stderr into a data file** produced a spurious census difference. A
  corrupted baseline that reports a *difference* is the benign direction; the same
  mistake on the other side reads as confirmation.
- **`grep -c '\r'` piped from `git show` matches every line** and once produced a false
  CRLF release-blocker. Use `tr -dc '\r' | wc -c`.
- Deriving a delta by subtraction from a remembered base propagates a stale base into a
  check that then cannot fail. Take the measurement.

### One sentence, two provenances

In the same statement the aggregate can come from the tool while the breakdown is
hand-derived — and the breakdown is the part a reader quotes. `071fbd4` published
`gaps=3895 clusters=112` exactly right, beside `record=2220 field=473 code=372`,
none of which matched **any** revision of `baseline.json` in its entire history
(all ten checked). The correct total lends its authority to the invented detail
sitting next to it, which is why it survived a release. Check every number in a
sentence against the tool, not the sentence's most checkable number.

### A merge can create a defect that exists on neither branch

Two branches independently added `record_keyword`, `system_keyword` and
`action_keyword` in **different regions** of `grammar.js`. Git saw no conflict, and
a rule table is a JS object literal where duplicate keys are silently accepted with
the last winning. `tree-sitter generate` succeeded, the parser was correct, 1594
tests passed, 0 corpus errors. Measured: 480/480 unique on one parent, 474/474 on
the other, 518 defs vs 515 unique merged. No check on either branch could have
found it at any point, because it did not exist until the merge. **Derive counts
EARLY in a merge, not at the end.**

### "Gate green" is not "commit green" when a tool writes the working tree

`qc accept` writes `baseline.json`; the gates *read* the working tree. Staging the
resolved baseline, then running `accept`, then committing without re-staging left
every gate passing on something other than what was committed — `qc run` at that
commit exits 1. Same shape as a docstring describing coverage the fixture does not
have: the thing verified was not the thing shipped.

### A second corpus finds what the first cannot

`byte-roundtrip` was clean across BC.History's 15,358 files and looked
trustworthy. On a second 20,643-file estate it flagged **3,268 files (16%)** for
three dropped bytes — all false, all a UTF-8 BOM, because `bytes.strip()` removes
ASCII whitespace only. BC.History contains no BOMs. A check validated against one
corpus is validated against that corpus's habits, not against the language.


## Reasoning traps

- **"I tried it and it forced N conflicts" measures one edit, not the grammar.** Record
  which edit was tried. A recorded limitation about `code_block` in `_statement_inner`
  survived a whole release and was an artifact of a half-finished attempt.
- Do not assert two scanner symbols are never co-valid without reading
  `ts_external_scanner_states` in `src/parser.c`. That table is the exhaustive universe
  of `valid_symbols` combinations and reasoning instead has been wrong every time.
- A site list derived by reading is usually short. `grep -n` over the whole file.
