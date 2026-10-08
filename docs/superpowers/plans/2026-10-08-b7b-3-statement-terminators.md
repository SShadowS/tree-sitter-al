# B7b-3: Statement Terminators, Case Separators and the Move Header — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A parenless call has one tree shape wherever its `;` is (owned by the host, absent, or in an
`#if` arm); a case branch's `;` may come from an `#if` group; the move header's target and fixed `;` may
come from `#if` groups — each with a correct, oracle-verified tree and a fully classified production delta.

**Architecture:** Phase 0 records alc verdicts first. A scoped route manifest and a structural delta
classifier freeze the targets and the permitted production changes before any grammar change. Then
three grammar phases (calls, case separators, move header), each with its oracle side, then the audit
re-run and close-out.

**Tech Stack:** tree-sitter 0.27 grammar DSL (`grammar.js`), Python tools (`tools/b7_audit`,
`tools/config_oracle`, `tools/perf`), alc 18.0.41 via `tools/alc_probe`, query files in `queries/`.

**Spec:** `docs/superpowers/specs/2026-10-08-b7b-3-statement-terminators-design.md` (rev 3, approved).
§N refers to it. Read the whole spec before your task; it is the binding authority.

## Global Constraints

- **Phase 0 rule (§2):** an alc verdict that contradicts §3-§5 stops the work and goes back to the user
  as a spec amendment before any grammar change. §4.2 rule 3 is provisional until the case verdicts.
- **Expected trees are HAND-WRITTEN** from the intended structure, then compared with the 0.27 CLI
  (`tree-sitter parse` / `tree-sitter test`); never generated, never `tree-sitter test -u` (§3.6). Each
  field-pinned fixture is proven able to fail by renaming one field to `bogus:`. Expected ERROR trees
  come from the CLI, never from `tools/snip.py` (CLAUDE.md); prefer the corpus `:error` attribute.
- **Production delta (§7):** previously clean production trees may change only by E1 / E2 / E3; the
  classifier (Task 3) gates every grammar task over all four corpora. BC.History is expected to show 0
  changes.
- **Oracle (§6.4):** repair fixtures pass in every alc-accepted configuration (only `lowering:one-reading`
  for §4.4 may refuse); representation fixtures keep today's refusals, each frozen by name in
  `tools/config_oracle/fixture-classes.tsv`.
- Commit `src/parser.c`, `src/grammar.json`, `src/node-types.json` together. Every commit ends with a
  measured trailer from `./tools/ts-lock.sh ./parse-al-parallel.sh ./BC.History/ . 2>&1 | tail -8`, as
  `[BC.History: N errors, X% success]`.
- Wrap every al.dll user in `./tools/ts-lock.sh`, EXCEPT `python -m tools.perf ab` (it takes the lock
  itself; wrapping it deadlocks). Run alc only via `MSYS_NO_PATHCONV=1 python -m tools.alc_probe`. Git Bash
  with Windows paths; never `2>nul`, never `find /`, never `tail -f | grep`; never `git checkout --`,
  `reset --hard`, stash drop/pop/clear, force.
- After any change to `src/parser.c`, `src/scanner.c` or `tools/config_oracle`: `assert --refresh`, a full
  `run`, then `report` before relying on the B7a matrix (CLAUDE.md).
- Budgets: STATE_COUNT +3% over the branch base (over: stop and report to the user); `ab` ratio >= 0.97.
- Every grammar task (4, 6, 8) also runs: `python tools/nodetypes.py diff main` (read line by line, each
  change traced to the task), `python tools/traversal_census.py` exit 0, `python tools/check-field-types.py`,
  and `python -m tools.query_coverage.qc run` exit 0 (or a justified `qc accept` recorded in the report).
- After every `tree-sitter test -u` (only for files you target, and only to refresh trees you then read
  hunk by hunk): `git diff --stat test/corpus` and restore anything you did not target (CLAUDE.md trap 5).
  After adding fixtures, the suite total moves by exactly the cases added.
- The main-branch library for comparisons: build once in Task 3 from `main` (a throwaway
  `git worktree add` OUTSIDE the repo, `./tools/ts-lock.sh tree-sitter build --output <scratch>/al-main.dll .`
  in it, remove the worktree). Record its path in the ledger.

## Review Focus

1. **A comment between a parenless call and its `;`** (`Bar // c` newline `;`, and `Bar /* c */ ;`) must
   give `call_statement` and the `;` with the comment in one of E1's two permitted places (Task 4 fixture
   `call terminator with comment`, Task 3 classifier pair `extras-before-semi`).
2. **A parenless call as the last statement inside an `#if` arm** (`begin #if X Bar #endif end`) must be a
   `call_statement` with no `;` (Task 4 fixture `call alone in an arm`).
3. **A lone-`;` case group directly before the case `else`** (`1: X #if A ; #endif else Y;`) must attach
   the `;` to branch `1` in configuration A and leave `else` to the case in both (Task 7 test
   `test_case_semi_before_case_else`).
4. **An incremental edit that adds or removes a parenless call's `;`** (`Bar` -> `Bar;`, `Bar;` -> `Bar`, and
   the same inside an `#if` arm) must give the fresh tree (Task 4 test
   `test_incremental_call_terminator_edits`).
5. **A quoted move target with a comment inside a header group** (`moveafter("A B" #if X /* c */ ; #endif C)`)
   must parse on route 2 with `target: (quoted_identifier)` and validate in the oracle (Task 8 fixture,
   Task 9 lowering test `test_move_quoted_target_comment`).

---

## File Structure

- `tools/alc_probe/cases/b7b3/` — Phase 0 probes (Task 1).
- `tools/b7_audit/manifest.py`, `tools/b7_audit/__main__.py`, `tools/b7_audit/b7b1-manifest.tsv` (scope
  header), `tools/b7_audit/b7b3-manifest.tsv`, `tools/b7_audit/tests/test_manifest.py` (Task 2).
- `tools/perf/delta.py`, `tools/perf/__main__.py` (`delta` subcommand), `tools/perf/tests/test_delta.py`,
  `tools/perf/ab_accept.py` (Task 3).
- `grammar.js` — calls (Task 4), case (Task 6), move (Task 8).
- `queries/highlights.scm`, `queries/tags.scm` + query fixtures (Task 4).
- `tools/config_oracle/contracts.py`, `lowering/engine.py`, `lowering/select.py`, new
  `lowering/case_terminators.py` (Task 7), new `lowering/move_args.py` replacing the move part of
  `lowering/conditional_lists.py` (Task 9), tests under `tools/config_oracle/tests/`.
- `tools/check-field-types.py`, `traversal/policy.json` (Tasks 4, 6, 8).
- `test/corpus/b7b3_call_terminator_test.txt`, `b7b3_case_separator_test.txt`, `b7b3_move_args_test.txt`
  (+ `_negative_test.txt` siblings), `expression_statement_test.txt` (item 40 pin).
- `tools/perf/strict_lists_scaling.py` (case and move series, Task 10).
- Docs: CHANGELOG, CLAUDE.md, `docs/deferred-work.md` (items 40, 46), roadmap B7 row, matrix (Task 11).

---

### Task 1: Phase 0 — alc evidence

**Files:** Create `tools/alc_probe/cases/b7b3/{calls,case,move}/*.al` (one probe per file; read
`tools/alc_probe/README.md` for the header format).

**Interfaces:** Produces the recorded verdicts the later tasks cite by file name, and a verdict table in
the task report: per probe, per configuration, `split` and `flat` verdict with the error code.

- [ ] **Step 1: Predict, then write** one probe per §2 bullet item, each with a self-contained object
  (no Base Application symbols; CLAUDE.md "Missing symbols" trap) and a `// expect:` line per symbol
  assignment holding YOUR prediction, and `// source: B7b-3 Phase 0, 2026-10-08`. Calls: every item of
  §2's Calls bullet. Case: every item of the Case bullet, each body kind (assignment, parenless call,
  parenful call, block, nested if, `asserterror`) for the separator-count items. Move: every item of the
  Move bullet; reuse the declarations of `tools/alc_probe/cases/b7-audit/move-modification__sep-only__gap.al`.
- [ ] **Step 2: Run** `MSYS_NO_PATHCONV=1 python -m tools.alc_probe run tools/alc_probe/cases/b7b3`
  (no `--check`): it reports measured verdicts, a valid and a garbage control first. A `BROKEN` (exit 2)
  is a project problem, not a verdict: fix the probe.
- [ ] **Step 3: Correct the `// expect:` lines** to the measured verdicts, then
  `MSYS_NO_PATHCONV=1 python -m tools.alc_probe run tools/alc_probe/cases/b7b3 --check` exits 0 with
  0 MISMATCH (split vs flat).
- [ ] **Step 4: Compare with the spec.** In the report, one row per spec claim that depends on alc:
  §4.2 rule 3 (`case I of ; end`, `1: X;;` rejected?), §4.4 (else ownership: both configurations
  accepted?), §5.1 (the spanning group and both comma continuations accepted?), §5.4 (`T #if X , A #endif`
  rejected in every configuration?), §3 (`Bar end`, `Order;` accepted). Any contradiction: report
  `NEEDS_CONTEXT` with the probe and verdict; do NOT continue.
- [ ] **Step 5: Commit** `test(alc): B7b-3 Phase 0 evidence (calls, case separators, move header)`.

### Task 2: Scoped route manifests

**Files:** Modify `tools/b7_audit/manifest.py` (scope header, transfer set, `expected_oracle`),
`tools/b7_audit/__main__.py`, `tools/b7_audit/b7b1-manifest.tsv` (add the scope header line only);
create `tools/b7_audit/b7b3-manifest.tsv`; modify `tools/b7_audit/tests/test_manifest.py`.

**Interfaces:**
- Consumes: `manifest.load(path)`, `manifest.current(evidence)`, `manifest.check(entries, records, verdicts)`
  (`tools/b7_audit/manifest.py`), `tools.config_oracle.runner.check_input(parser, cid, src)` (as used in
  `tools/b7_audit/tests/test_silent.py`).
- Produces: a mandatory first line `# families: <comma-separated>` in every manifest; `manifest.load`
  returns `(scope: tuple[str, ...], entries)`; `manifest.check(scope, entries, records, verdicts,
  transfer=frozenset(), oracle=None)`; an optional `expected_oracle` column (B7b-3 manifest only) with the
  syntax `CFG:STATUS[,CFG:STATUS...]`, e.g. `X=0:pass,X=1:lowering:one-reading`; CLI
  `python -m tools.b7_audit manifest --check --manifest PATH` exit 0/1/2; module constant
  `TRANSFER_B7B3` = the B7b-1 manifest's `move-modification` cells whose `owner` is `B7b-3`.

- [ ] **Step 1: Tests (RED)** in `test_manifest.py`: (a) a manifest without the scope header is a load
  error (exit 2); (b) a row whose family is outside the scope is a problem; (c) an unknown family in the
  header is a load error; (d) the header round-trips (load, write, load gives the same scope); (e) a
  candidate-family cell missing from the manifest is a problem only for families in ITS scope; (f) a
  B7b-1 `excluded` cell whose verdict changed is a problem unless it is in the transfer set AND present
  in the B7b-3 manifest AND passing there; (g) a transferred cell's identity, vector and coverage are
  still checked; (h) an `expected_oracle` mismatch against a stub oracle is a problem; (i) a malformed
  `expected_oracle` value is a load error. Run
  `./tools/ts-lock.sh python -m pytest tools/b7_audit/tests/test_manifest.py -q` → the new cases FAIL.
- [ ] **Step 2: Implement.** Replace the hard-coded `FAMILIES` with the header scope; keep
  `FAMILIES` as the B7b-1 scope constant only for writing the header into `b7b1-manifest.tsv`. Add the
  header line to `b7b1-manifest.tsv` (no other change to that file). `__main__.py`: `--manifest` keeps
  defaulting to `b7b1-manifest.tsv`; `--check` loads the scope from the file.
- [ ] **Step 3: Generate `b7b3-manifest.tsv`** (scope `statement-terminator,move-modification` plus a
  pseudo-family `call-shape` for item 40's shapes, with seed cells `seed:b7b3__order_call`,
  `seed:b7b3__bar_end`, `seed:b7b3__then_bar_else`) from the committed evidence with a scratch script
  (not committed; the TSV is the artifact). Dispositions: every `statement-terminator` cell whose host is
  `case_branch`, `if_statement`, a statement block or a split case/if wrapper → `admitted`, target verdict
  CONSISTENT (MIXED where Task 1 shows alc rejecting a configuration, with that configuration's verdict);
  the 33 `empty_statement@case_branch#trail` OVERACCEPT cells → `admitted` with the Task 1 verdict;
  every `move-modification` header cell (the transfer set) → `admitted`; any cell owned by B12/B13 or a
  conditional `case_else_branch` → `excluded` with owner. `expected_oracle` from §6.4: `pass` in every
  alc-accepted configuration, `lowering:one-reading` only for §4.4's alternate reading.
- [ ] **Step 4:** tests GREEN. `python -m tools.b7_audit manifest --check` (B7b-1) exits 0 on the current
  tree. `python -m tools.b7_audit manifest --check --manifest tools/b7_audit/b7b3-manifest.tsv` exits 1
  and reports every admitted cell (they are SILENT/GAP today): record the count in the report — this
  proves the check can fail.
- [ ] **Step 5: Commit** `feat(b7-audit): scoped manifests, B7b-3 route manifest with expected oracle statuses`.

### Task 3: Structural delta classifier and the perf acceptance script

**Files:** Create `tools/perf/delta.py`, `tools/perf/tests/test_delta.py`, `tools/perf/ab_accept.py`;
modify `tools/perf/__main__.py` (`delta` subcommand beside `parity`, `tools/perf/__main__.py:130`).

**Interfaces:**
- Consumes: `tools.perf.incremental.rows(tree)` (`tools/perf/incremental.py:67`), `parity._parsers`,
  the corpus label map (`tools/perf/common.py` `LABELS`: `bc-history`, `dc`, `bc28.1`, `bcapps-29.0`).
- Produces: `delta.explain(old_tree, new_tree, src) -> Explanation(edits: list[Edit], unexplained: list[str])`
  where `Edit = (kind: "E1"|"E2"|"E3", start_byte: int, note: str)`; CLI
  `python -m tools.perf delta --lib-a A --lib-b B --corpus all|<label>... [--out OUT.json]` exit 0 (every
  change explained) / 1 (unexplained or forbidden) / 2 (cannot run); `ab_accept.py RUN1.json RUN2.json`
  (two `ab --out` results) exit 0 when both `ratio_a_over_b.median >= 0.97`.

- [ ] **Step 1: Read** spec §7 in full. The edit definitions there are binding: E1 (call terminator out,
  with its owner rule), E2 (split-call terminator out, ends at `)`), extras placement (unchanged parent, or
  immediately before the `;` in its new parent), E3 (the eligible-slot table and the keyword table,
  verbatim from §7.2).
- [ ] **Step 2: Tests (RED)** in `test_delta.py`, built from hand-made node rows (no parser needed for
  the unit tests; use the row format of `incremental.rows`): positive pairs E1 in a statement block, E1 in
  a then-branch (ancestor `if_statement` shrinks), E1 in a case branch (the `;` becomes the branch's own),
  E2, E3 in each table slot, E3 for `Order`, E1 composed inside E3's host, `extras-before-semi` (line and
  block comment, both permitted placements); forbidden pairs: a case pattern wrapped, a name in a trigger
  `body` wrapped, the callee replaced, a parent field reassigned, an `else` wrapped, an extra moved to an
  unapproved parent, any change in a file with `has_error`. Plus an integration test with the real
  library: main-vs-main over 20 BC.History files → exit 0, 0 edits.
- [ ] **Step 3: Implement** `delta.py`: parse each file with both libraries, compare row lists; when they
  differ, pair nodes by (start, type) walk and try the edits greedily, innermost first; report the
  remainder. Keep it a pure function over rows plus a thin corpus driver reusing `parity`'s worker pool.
- [ ] **Step 4: Implement** `ab_accept.py` (read two `ab --out` outputs; print both medians; exit 1 below
  0.97 or when either run has `trees_identical: false`).
- [ ] **Step 5: Build the main library** as in Global Constraints and run
  `./tools/ts-lock.sh python -m tools.perf delta --lib-a <al-main.dll> --lib-b <al-main.dll> --corpus all`
  → exit 0, 0 edits on all four corpora.
- [ ] **Step 6: Commit** `feat(perf): structural delta classifier (E1-E3) and ab acceptance script`.

### Task 4: Parenless calls

**Files:** Modify `grammar.js` (`call_statement` ~5652, `_expression_statement` ~5694, `_statement`
~5594-5615, `fieldedStatement` ~158-165, `if_statement` ~5919-5935, `preproc_split_call_statement`
~5380-5390, their comments), `queries/highlights.scm`, `queries/tags.scm`,
`test/corpus/expression_statement_test.txt`, `tools/check-field-types.py`,
`tools/config_oracle/tests/test_strict_lists_incremental.py` (or a new incremental test file beside it),
query fixtures (read how existing query fixtures are run in `validate-grammar.sh` and follow that);
create `test/corpus/b7b3_call_terminator_test.txt`.

**Interfaces:** Produces `call_statement` = `field('function', name)` with no `;` (§3.1). Tasks 6-9 rely
on it.

- [ ] **Step 1: RED fixtures** in `b7b3_call_terminator_test.txt`, hand-written, fields on, one case each
  for every §3.6 bullet, plus: `call alone in an arm` (`begin #if X Bar #endif end`), `call terminator
  in an arm` (`if Ok then Bar #if X ; #endif`), `call before empty group` (`if Ok then Bar #if X #endif ;`),
  `call terminator with comment` (`Bar // c` newline `;` and `Bar /* c */ ;`), `case 1: Bar;`, `Order;`,
  `Table;`. Run `./tools/ts-lock.sh tree-sitter test --file-name b7b3_call_terminator_test.txt` → the
  shapes that change FAIL; record which.
- [ ] **Step 2: Grammar** — exactly §3.1 and §3.2 (code verbatim from §3.1), and §3.3's split-call
  change (drop its final `';'`). Rewrite the ownership comments (the `_statement` note on `call_statement`,
  the `if_statement` note "Two then-branch forms are still SELF-TERMINATING", the `fieldedStatement`
  header) to describe ownership by host route as §1 does. `./tools/ts-lock.sh tree-sitter generate`;
  record STATE_COUNT, LARGE_STATE_COUNT, SYMBOL_COUNT, parser.c bytes, conflicts added.
- [ ] **Step 3: GREEN** — the fixture file passes; full `./tools/ts-lock.sh tree-sitter test` passes
  with the total moved by exactly the cases added. Update the item-40 pin in
  `expression_statement_test.txt` (hand-written: both `Order;` and `Bar end` now `call_statement`).
  Every other changed expectation must be explained by E1/E3; read every hunk.
- [ ] **Step 4: Reserved words** — confirm an operator word after a name still ERRORs (`Bar and;`,
  `Bar mod;`); if not, move `reserved('code_names', ...)` onto the choice inside `call_statement` and
  regenerate.
- [ ] **Step 5: Queries** — add to `queries/highlights.scm`
  `(call_statement function: (identifier) @function.call)` and
  `(call_statement function: (quoted_identifier) @function.call)` next to the `call_expression` captures
  (~750-756); to `queries/tags.scm` the matching `@reference.call` capture next to ~316-322. Add query
  fixtures proving both capture `Bar;` and `"My Proc";`.
- [ ] **Step 6: Incremental** — `test_incremental_call_terminator_edits`: `Bar` -> `Bar;`, `Bar;` ->
  `Bar`, and both inside an `#if` arm; each incremental tree equals the fresh tree (follow the existing
  pattern in `tools/config_oracle/tests/test_strict_lists_incremental.py`).
- [ ] **Step 7: Field contract** — `tools/check-field-types.py`: `call_statement.function` single,
  required; `python tools/check-field-types.py` passes.
- [ ] **Step 8: Gates** — `./tools/ts-lock.sh python -m tools.perf delta --lib-a <al-main.dll> --lib-b
  <branch.dll> --corpus all` exit 0, report the E1/E2/E3 counts per corpus (expected: BC.History 0 edits;
  E1 about 3,367 and E3 about 117 in the others); `python tools/has_error_sweep.py --corpus-fixtures` and
  `--root` each corpus clean; `./tools/ts-lock.sh python -m tools.config_oracle run --tier quick` exit 0;
  `./tools/ts-lock.sh python -m pytest tools/config_oracle/tests tools/b7_audit/tests -q` green except
  `test_silent.py` witnesses that now FAIL as designed: flip each one whose configured status now passes
  (the `if_statement` call witnesses) to require `pass`; a witness that still fails because it needs the
  case lowering (the `case_branch` ones) stays as it is for Task 7/10, noted in the report;
  `./validate-grammar.sh`.
- [ ] **Step 9: Commit** `feat(b7b-3): parenless calls have one shape; call_statement no longer owns its ;`.

### Task 5: Performance check after the call change

**Files:** none committed except the two `ab` JSON results under `.cache/` (not tracked).

- [ ] **Step 1:** `python -m tools.perf ab --lib-a <al-main.dll> --lib-b <branch.dll> --corpus bc-history
  --rounds 24 --out .cache/b7b3-ab-1.json`, then the same to `-2.json` (NOT wrapped in ts-lock).
- [ ] **Step 2:** `python tools/perf/ab_accept.py .cache/b7b3-ab-1.json .cache/b7b3-ab-2.json` exit 0.
  Below 0.97: stop and report the two medians and CIs. (A failure here is a design-level signal; the
  controller decides, not the implementer.)

### Task 6: Case-branch separators (grammar)

**Files:** Modify `grammar.js` (`preproc_conditional_case` ~6132-6139, `case_branch` ~6147-6153,
`preproc_split_case_branch` ~6160-6172, `preproc_split_case_extended` ~6176-6195; new helper function
`caseEmptyGroup` and hidden rule `_case_empty_group`, code verbatim from §4.2.2),
`tools/check-field-types.py`, `traversal/policy.json`; create `test/corpus/b7b3_case_separator_test.txt`
and `test/corpus/b7b3_case_separator_negative_test.txt`.

**Interfaces:** Produces the split tree of §4.1-§4.3: sibling `preproc_conditional_case` with
`empty_statement` arms; decorations = `preproc_conditional_case` (alias of `_case_empty_group`) as
unfielded children of the three hosts immediately before the host's own `;`. Task 7 lowers both.

- [ ] **Step 1: Spike (§4.3 optional bodies) FIRST.** Write the `1: asserterror #if X #endif ;` case with
  the REQUIRED tree of §4.3 hand-written. Implement rules 4.2.1 and 4.2.2, generate, run the case. If
  the required tree is produced with no new conflict: continue. Otherwise: report `NEEDS_CONTEXT` with the
  measured winner, the conflict generate asked for, and both trees; do not continue.
- [ ] **Step 2: RED/GREEN fixtures**, hand-written, fields on: every Phase 0 case shape alc accepts
  (Task 1 table) in its split tree; a nested decoration with distinct inner and outer nodes; decorations in
  `preproc_split_case_branch` and `preproc_split_case_extended`; the three §4.3 discriminating fixtures,
  each also with a nested empty group and with a `;` group just before the shared suffix; the §4.4 tree;
  the Review Focus 3 input (`1: X #if A ; #endif else Y;`). Negative file (`:error`): `case I of ; end` and
  flat `1: X;;` if Task 1 recorded alc rejecting them (§4.2.3), and an empty group then `;` at the start of
  `case_body`.
- [ ] **Step 3: Generate, test.** Record states/conflicts. Full suite: total moves by exactly the cases
  added. Remove the case-host GAP witnesses from `test/corpus/b7_gap_statement_terminator_test.txt` (move
  each shape to the positive fixture), their rows in `tools/deliberate-negatives.txt` and
  `tools/config_oracle/fixture-classes.tsv`, and repoint the `// Fixture` lines of their alc probes in
  `tools/alc_probe/cases/b7-audit/` (B7b-1 ruling, ledger line "each host task removes its family's
  `:error` witnesses").
- [ ] **Step 3b: Incremental** — `test_incremental_case_separator_edits`: insert and remove a lone-`;`
  group after a branch, a decoration before a branch's `;`, and a nested decoration; each incremental
  tree equals the fresh tree (pattern of `tools/config_oracle/tests/test_strict_lists_incremental.py`).
- [ ] **Step 4: Field contract and traversal** — `case_branch` gains no field; add an invariant that
  `preproc_conditional_case` children may include `empty_statement`; `traversal/policy.json` unchanged
  unless the census asks; `python tools/traversal_census.py` exit 0.
- [ ] **Step 5: Gates** as Task 4 Step 8 (delta: no case-change edit expected in production; any is a
  stop), plus `./tools/ts-lock.sh python -m tools.config_oracle run --tier quick`: new case fixtures may
  be `cannot-validate` until Task 7 — classify them `debt(B7b-3)` in `fixture-classes.tsv`; Task 7 must
  retire every such row (a stale row fails).
- [ ] **Step 6: Commit** `feat(b7b-3): case-branch separators from #if groups (split tree)`.

### Task 7: Case-branch separators (oracle)

**Files:** Create `tools/config_oracle/lowering/case_terminators.py`,
`tools/config_oracle/tests/test_case_terminators.py`; modify `lowering/select.py` (~80-100, marking),
`lowering/engine.py` (~240-260 and the `STATEMENT_HOSTS` dispatch ~395-405), `contracts.py` (~283-310),
`tools/config_oracle/fixture-classes.tsv`.

**Interfaces:**
- Consumes: `engine.ARM_SEMI`, `absorb_arm_terminators` (`engine.py:243-257`, statement blocks only from
  now on), `select.branch_select`.
- Produces: `case_terminators.CASE_SEMI = "_case_semi"`; `case_terminators.attach(kids, ctx) -> list` run
  on a `case_body` after its whole run is selected; a context-dispatched handler for
  `preproc_conditional_case` (`branch-select` under `case_body` / a group arm; `decoration` directly under
  `case_branch`, `preproc_split_case_branch`, `preproc_split_case_extended` before the host's `;`).

- [ ] **Step 1: Tests (RED)** — one test per §6.2 bullet: termination by the branch's own direct `;`
  (a `;` inside the body does not count); marking of every direct-arm `empty_statement` including
  mixed arms and nested arms (`CASE_SEMI`, never `ARM_SEMI`); attachment to the immediately preceding
  surviving unterminated branch only; no attachment after a terminated branch, an `empty_statement`, a
  `case_else_branch`, or at the run start; two consecutive marked `;`s (the second sees the first);
  rewrite log `case-terminator-attach@<offset>`; decoration deletion with every arm (inactive included)
  validated directive-only; split-case wrappers; `test_case_semi_before_case_else` (Review Focus 3); §4.4
  both ways (represented configuration passes; alternate valid configuration refused
  `lowering:one-reading`, decided from the selected separators, never from the reference parse). Mutation
  tests (§6.2 list, each must make a test fail): `;` beside the branch, across a terminated branch, inside
  `body`, a `;` in the body counted as termination, provenance lost, a decoration emitting a `;`, a branch
  or `;` injected into an INACTIVE decoration arm and dropped, missing refusal. Leaf accounting holds.
- [ ] **Step 2: Implement** `case_terminators.py`; marking in `select.py` (a case-specific branch beside
  the existing `preproc_conditional_statement` rule at ~91-93); `engine.py` stops passing `case_branch`
  through `absorb_arm_terminators` and runs `case_terminators.attach` on `case_body`; `contracts.py`:
  recursive host, `empty_statement` arm member, the three decoration hosts, keep the `case_else_branch`
  exclusion explicitly with its comment.
- [ ] **Step 3: GREEN**; retire every `debt(B7b-3)` case row added in Task 6; the representation
  fixtures' refusals frozen by name in `fixture-classes.tsv` (§6.4).
- [ ] **Step 4: Gates** — pytest `tools/config_oracle/tests` green; quick tier exit 0;
  `python -m tools.config_oracle replay` green; `./validate-grammar.sh`.
- [ ] **Step 5: Commit** `feat(config-oracle): case terminator attachment, decorations, one-reading refusal`.

### Task 8: Move header (grammar)

**Files:** Modify `grammar.js` (`moveArgs` ~96-103 replaced by §5.1's code verbatim; add
`...strictConditionalList('move_args', $ => $._identifier_or_quoted, choice(';', ','))` to `rules` beside
the existing `move_elements` spread), `tools/check-field-types.py`, `traversal/policy.json`,
`tools/b7_audit/registry.tsv`; create `test/corpus/b7b3_move_args_test.txt`,
`test/corpus/b7b3_move_args_negative_test.txt`.

**Interfaces:** Produces `preproc_conditional_move_args` and routes 1-3 (§5.1); fields per §5.2. Task 9
lowers them.

- [ ] **Step 1: RED fixtures**, hand-written, fields on: every §5.1 positive bullet (six placements,
  spanning group, both comma continuations, `G(T; A,) B`, `T G(;) A G(, B)`, `T G(; A,) B`, nested and
  `#elif`), the §5.3 example, Review Focus 5 (`moveafter("A B" #if X /* c */ ; #endif C)`), and route-1
  preservation (B7b-1's `preproc_conditional_move_elements` fixtures unchanged). Negative file (`:error`):
  `moveafter(T;)`, `moveafter(T, B)`, `moveafter(T; B; C)`, `moveafter(T)`, `moveafter()`.
- [ ] **Step 2: Grammar, generate, GREEN.** Record states/conflicts; measure that hidden partitions give
  one tree (generate reports no new conflict, or the conflict added is named in a comment with both
  readings and a fixture shows the winner).
- [ ] **Step 3: Witnesses** — remove the move GAP witnesses (`test/corpus/b7_gap_move_modification_test.txt`
  shapes now positive, `strict_conditional_move_elements_negative_test.txt`'s two `debt(B7b-3)` cases if
  they now parse) with their `deliberate-negatives.txt` and `fixture-classes.tsv` rows; repoint probe
  `// Fixture` lines.
- [ ] **Step 3b: Incremental** — `test_incremental_move_args_edits`: move a `;` between the host and an
  arm, insert and remove a header group, and turn route 1 into route 2 and back; each incremental tree
  equals the fresh tree.
- [ ] **Step 4: Fields** — `tools/check-field-types.py`: host `target` `required: false` on the four
  move rules (aggregate only, §5.2); `traversal/policy.json` class for `preproc_conditional_move_args`
  like `preproc_conditional_move_elements`; census exit 0.
- [ ] **Step 5: Registry** — the new separator occurrences in `_move_args_b`, `_move_args_r` and the
  route tails, the `;` and `,` branch of `sep` each with its own member path, get rows in
  `tools/b7_audit/registry.tsv` (`equiv occ:<host>:<path>` where the separator is the same alc separator,
  else a new-scope row); `python -m tools.b7_audit census --check` exit 0.
- [ ] **Step 6: Gates** as Task 6 Step 5 (move fixtures may be `debt(B7b-3)` until Task 9).
- [ ] **Step 7: Commit** `feat(b7b-3): move header from #if groups (routes 2-3, move_args group)`.

### Task 9: Move header (oracle)

**Files:** Create `tools/config_oracle/lowering/move_args.py`, `tools/config_oracle/tests/test_move_args.py`;
modify `lowering/conditional_lists.py` (remove the move-elements family from `FAMILIES`/`HOST_FAMILY`),
`lowering/engine.py` (~385-393, dispatch), `contracts.py`, `fixture-classes.tsv`.

**Interfaces:** Produces `move_args.MOVE_HOSTS = ("movefirst_modification", "movelast_modification",
"moveafter_modification", "movebefore_modification")`; `move_args.lower(node, kids, ctx) -> list` called
by `engine.py` for EVERY node whose kind is in `MOVE_HOSTS`, before the generic strict-list hook.

- [ ] **Step 1: Tests (RED)** — route identification (1, 2, 3); pre-selection validation (containment,
  order, node types per route, route 1/2 fields checked as they stand); post-selection flatten and
  `name ; name (, name)*`; field assignment only after validation; rejections (extra target, duplicate
  `;`, missing `;`, bad commas) never repaired; the empty element region stays on the reference-error
  path; route 1 still lowers exactly as B7b-1 did (its existing tests stay green unchanged);
  `test_move_quoted_target_comment` (Review Focus 5). Mutation tests, the §6.3 list (8 items), each
  must make a test fail.
- [ ] **Step 2: Implement**; dispatch by host kind; a host holding only `preproc_conditional_move_args`
  cannot bypass validation (test it).
- [ ] **Step 3: GREEN**; retire every `debt(B7b-3)` move row; representation refusals frozen by name.
- [ ] **Step 4: Gates** as Task 7 Step 4.
- [ ] **Step 5: Commit** `feat(config-oracle): unified move-interior adapter (routes 1-3)`.

### Task 10: Audit re-run, manifests, scaling, performance

**Files:** Modify `tools/b7_audit/evidence.jsonl.gz`, `tools/b7_audit/assertions.tsv`,
`docs/b7-separator-continuation-matrix.md` (regenerated), `tools/b7_audit/tests/test_silent.py`,
`tools/perf/strict_lists_scaling.py`, `tools/perf/tests/test_strict_lists_scaling.py`.

- [ ] **Step 1:** `./tools/ts-lock.sh python -m tools.b7_audit assert --refresh` (report flipped rows; each
  must be a cell this sub-project targets), full `./tools/ts-lock.sh python -m tools.b7_audit run`,
  `python -m tools.b7_audit report`.
- [ ] **Step 2:** both manifest checks exit 0:
  `python -m tools.b7_audit manifest --check` and
  `python -m tools.b7_audit manifest --check --manifest tools/b7_audit/b7b3-manifest.tsv`.
- [ ] **Step 3:** `test_silent.py`: every `statement-terminator` SILENT witness flipped to a passing
  configured status (or to its named §6.4 refusal); the group list updated to the matrix.
- [ ] **Step 4: Scaling** — add the §8.2 series to `strict_lists_scaling.py` using its existing grid and
  limits unchanged (`LENGTHS = [10 * 2**k for k in range(11)]`, `DEPTHS = [1, 2, 4, 8, 16, 20]`,
  `REPEATS = 5`, `RATIO_LIMIT = 2.5`, `MEMORY_LIMIT` 256 MiB, `PEAK_LIMIT` 1 GiB): case lone-`;` groups,
  nested empty decorations, mixed arms; move spanning and nested groups. Each input runs in a killable
  worker process with a 10 s ceiling. All series pass.
- [ ] **Step 5:** delta over four corpora exit 0; `ab` twice + `ab_accept.py` exit 0 (as Task 5);
  `python tools/has_error_sweep.py` on fixtures and the four corpora; oracle full tier
  `./tools/ts-lock.sh python -m tools.config_oracle run --tier full --root ./BC.History --root ./DC --root H:/Git/BC28.1 --root H:/Git/BCApps-29.0`
  exit 0 with 0 discrepancies; STATE_COUNT within +3% of the branch base (report it).
- [ ] **Step 6: Commit** `feat(b7-audit): B7b-3 audit re-run, manifests green, witnesses flipped, scaling`.

### Task 11: Docs, WASM, final gates

**Files:** `CHANGELOG.md`, `CLAUDE.md`, `docs/deferred-work.md` (item 40 closed, item 46's B7b-3 row
done, new items for anything deferred), `docs/superpowers/plans/2026-09-28-roadmap-remaining-work.md`
(B7 row), `tree-sitter-al.wasm` (rebuild as the repo's release docs say), the spec (execution
amendments, if any).

- [ ] **Step 1: CHANGELOG** — a migration section with old/new examples: `call_statement` no longer
  contains `;` and wraps every bare-name statement (incl. `Order`/`Table`); `preproc_split_call_statement`
  ends at `)`; case groups may hold `empty_statement`, decorations inside branches; move routes 2-3 with
  `preproc_conditional_move_args`, role fields only where structurally known; the error-tree caveat
  (a recovered identifier may become a `call_statement`); the new highlight/tag captures.
- [ ] **Step 2: CLAUDE.md** — the `call_statement` ownership text, a B7b-3 paragraph like B7b-1's, the
  metrics table re-measured (`wc -c src/parser.c`, `grep -E 'SYMBOL_COUNT|STATE_COUNT' src/parser.c`,
  `wc -l grammar.js`, the test count from the last line of `./tools/ts-lock.sh tree-sitter test`).
- [ ] **Step 3: WASM** rebuild; `tools/check-wasm-fresh.sh` passes.
- [ ] **Step 4: Final gates** — `./validate-grammar.sh --full`; the B7b-3 gate list of §8.2 once more;
  report every number.
- [ ] **Step 5: Commit** `docs(b7b-3): CHANGELOG migration, CLAUDE.md, deferred items, roadmap; wasm`.
