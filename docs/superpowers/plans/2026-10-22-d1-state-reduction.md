# D1: The State-Reduction Pass — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cut the parse table to STATE ≤ 27,300 and LARGE ≤ 9,700 by tree-preserving factorings of the split-if
(and, only if needed, split-case) rules, with every valid input's tree byte-identical and no speed regression.

**Architecture:** Each candidate (C1, C2, C3; C4/C5 only by the stop-or-search rule) extracts a complete unit that
two or more rules spell out into one hidden rule, so its LR states are built once. Each candidate is one commit
that passes the per-candidate gates against its predecessor's library. A final gate task runs every gate for the
batch against `960ed31`; a close-out task documents the numbers.

**Tech Stack:** tree-sitter 0.27 grammar DSL (`grammar.js`), py-tree-sitter 0.25 (scratch parity scripts), Python
gate tools (`tools/perf`, `tools/b7_audit`, `tools/config_oracle`, `tools/has_error_sweep.py`), Linux host.

**Spec:** `docs/superpowers/specs/2026-10-22-d1-state-reduction-design.md` (approved, HEAD `808b75d`). §N refers
to it. It is the binding authority. Where a measurement forces a deviation, add it to an "Execution amendments"
section at the end of the spec (create it on first use) and report it; never deviate silently.

## Global Constraints

**The four USER DECISIONs, verbatim:**
- §1: "the goal is that al-sem has the best parsed ast for its analysis. I would prefer the parser doesn't get
  slower or bigger, but correctness is our goal." Priority: **correctness first, then size and speed.** No
  reduction may change a valid input's tree.
- §2: **speed is a gate, not a goal.** No candidate may regress (section 7). Any gain is reported but not
  required. The dedicated speed pass stays in D2.
- §2/§4 (C2 exception): the error-recovery tree of an input that already ERRORs may change, provided it is
  classified and recorded under gate G7. The only such change allowed so far is C2's, in the deliberate-negative
  fixture `b7_gap_split_if_begin_test.txt`. The exception covers recovery trees only. Every valid input keeps a
  byte-identical tree. C2's case ("B7a GAP: split-if-begin / first-replace") must still fail as an `:error`.
- §8.3: directives-as-extras was considered and rejected: "as alsem needs the correct picture and not just an okay
  one, I think we are on the correct track". D1 reduces states **within** the structural design.

**Target (§6, verbatim):** **STATE ≤ 27,300 and LARGE ≤ 9,700. `parser.c` is reported but has no target of its own.**

**Ceilings (§1):** STATE 28,770, LARGE 10,723, `parser.c` 80 MiB. They are strong preferences, not hard limits:
crossing one is reported, never a reason to leave a tree wrong. They do not move.

**Anti-goals (§2):** any change to a tree (node, anonymous token, field, span, `has_error`, `is_missing`) on any of
the four corpora or any corpus fixture (except the C2 exception); any change to `src/node-types.json`; a parse-speed
or incremental-parse regression; fewer states bought with a slower parser; widening the accepted language,
including family merging (§3.3).

**Gates (§5, verbatim):**

| # | gate | how | pass |
|---|---|---|---|
| G1 | generate and metrics | `./tools/ts-lock.sh tree-sitter generate`; `./tools/metrics.sh --vs 960ed31` | counts as recorded in the commit message |
| G2 | node-types | `git diff --exit-code src/node-types.json` | no diff |
| G3 | suite | `./tools/ts-lock.sh tree-sitter test` | the case count is unchanged, all pass, and no `-u` |
| G4 | tree-harness | `./tools/tree-harness.sh snapshot/verify` against a fresh `.snapshots/baseline-d1-<candidate>` | 0 delta |
| G5 | complete trees, four corpora | `python -m tools.perf delta --lib-a BEFORE --lib-b AFTER --corpus all`, and `ab`'s own tree check | 0 files changed (BCApps-29.0's known recovery-only file stays as `delta-reviewed.tsv` records it) |
| G6 | `has_error` | `python tools/has_error_sweep.py --root <R>` for each corpus, and `--corpus-fixtures` | the same result as before |
| G7 | fixture recovery trees | the inputs of every corpus case parsed with both libraries (the scratch `fixtures.py` is the model) | 0 differ on valid inputs. A difference is allowed only in the error-recovery tree of an `:error` case listed in `tools/deliberate-negatives.txt` (the USER DECISION exception, section 2). Record it in the commit with the case name, and check that the case still fails as an `:error`. C2 has one: `b7_gap_split_if_begin_test.txt`. |
| G8 | config oracle, full tier | `./tools/ts-lock.sh python -m tools.config_oracle run --tier full --root ./BC.History --root ./DC --root $AL_BC28_ROOT --root $AL_BCAPPS29_ROOT`, in `/work/tsal-wt/main` (see above) | exit 0, and the same output as the `960ed31` run |
| G9 | B7a evidence | **every candidate commit:** `./tools/ts-lock.sh python -m tools.b7_audit assert --refresh` (0 flips), `python -m tools.b7_audit census --check` (a new hidden rule can move a census key: add `key-aliases.tsv` rows and leave frozen cell ids unchanged), and the fast gates. **Once, on the final batch at the gate commit:** a full `./tools/ts-lock.sh python -m tools.b7_audit run`, then `report` **(controller's call, B7b-2 precedent)**. A warm full run took about 5 minutes and a cold one about 3 hours. | every verdict is unchanged, and the matrix differs only in its hash header. Intermediate commits may carry evidence whose hashes do not match their parser, as B7b-2's grammar commits did. Their commit messages say so. |
| G10 | incremental equals fresh | `python -m tools.perf incremental --corpus <R>` for each corpus | exit 0 |
| G11 | fork probes (pathological GLR) | `./tools/ts-lock.sh python tools/perf/strict_lists_scaling.py --lib AFTER`, compared with the same run on BEFORE | **required for every candidate that adds a declared conflict** (C1, C2, C4, C5), not only for the self-conflict candidates **(controller's call)**. Exit 0, and `SCALING_EXCEPTIONS` unchanged (items 52 and 53). No series may move from linear to an exception. |
| G12 | speed | section 7 | the rules there |
| G13 | the usual | `./tools/ts-lock.sh ./validate-grammar.sh --full`, and `python -m tools.query_coverage.qc run` | green. qc skips fields in hidden rules, so a moved field shows up in `tools/check-field-types.py` (Step 5b), not in qc. |

`tools.perf ab`, `delta` and `incremental` take the lock themselves or load a given library. Never wrap them in
`ts-lock.sh` (wrapping `ab` deadlocked in B7b-2). `strict_lists_scaling.py` does not take the lock: wrap it.

**Per-candidate gate set (§5):** G1-G4, G7, the G9 per-commit part, G11 if the candidate adds a conflict, and G12
against its predecessor. The final batch passes every gate against `960ed31`.

**Speed rule (§7, verbatim):**
- **Same session, same compiler and flags.** BEFORE is the predecessor's library: `960ed31` for C1, and the
  previous candidate's for each later one. AFTER is the candidate's. Both are built by the same
  `tree-sitter build` path that `ab` loads.
- Each candidate gets two 24-round `ab` runs per corpus, bc-history and dc:
  `python -m tools.perf ab --lib-a BEFORE --lib-b AFTER --corpus dc --rounds 24 --out d1-<cand>-dc-1.json`,
  then the same into `-dc-2.json`, then `python -m tools.perf.ab_accept d1-<cand>-dc-1.json d1-<cand>-dc-2.json`,
  and the same three commands for `--corpus bc-history`.
  - Both runs must have median time(A)/time(B) ≥ 0.97 and identical trees, and `ab_accept` must exit 0.
  - If the two runs disagree around 0.99 (one above, one below), a third run decides. Two of three below 0.99
    fails the candidate.
  - The batch then gets the same two runs per corpus against `960ed31`, for the record.
- **Incremental**: `python -m tools.perf incremental --corpus dc` before and after, in one session. Report the
  ms per edit. A rise beyond the run-to-run spread fails.
- **Host load** decides whether a run can be read. Record `uptime` with each run, and re-run on a quiet host
  before reading a ratio below 1.00 as a regression.

**Stop or search (§10, verbatim):**
- At or below 27,300 STATE (and 9,700 LARGE): stop. Do not look for more.
- Above 27,300 but at or below 27,400: stop, accept the batch and report the shortfall. This is the expected
  end if C2 fails and the C1 + C3 + C4 fallback (about 27,320) is taken.
- Above 27,400: the builder may try **at most two** more candidates, taken from the split-if family (3,687) and
  the split-case family (3,144), and from nowhere else. The pattern is the same: a long prefix or tail that ends
  at a hard keyword (`then`, `end`, `#endif`), spelled out in two or more rules. C4 and C5 count toward the two.
  Each one passes the same per-candidate gates. There is no open-ended search, no reach into the expression
  core (3.2) and no family merging (3.3). If the batch still ends above 27,400, stop and report.

**Project rules:**
- `tree-sitter test -u` is forbidden. The fixture suite passes unchanged; `git diff --stat test/corpus` is empty
  after every run.
- Commit `src/parser.c`, `src/grammar.json`, `src/node-types.json` together. Every commit message carries the
  counts (STATE, LARGE, SYMBOL, conflicts, `parser.c` bytes and MiB) and ends with the trailer measured by
  `./tools/ts-lock.sh ./parse-al-parallel.sh ./BC.History/ . 2>&1 | tail -8`, as
  `[BC.History: N errors, X% success]`. Candidate commits also say "B7a evidence hashes not refreshed".
- Wrap every `tree-sitter` and every al.dll user in `./tools/ts-lock.sh`, except `tools.perf ab`/`delta`/
  `incremental`. Run the oracle and `tools.perf` from `/work/tsal-wt/main` (its `BC.History`, `DC` and `H:`
  symlinks resolve the corpus labels). Never switch `/work/tsal`. This host is Linux: Linux paths, `.so`.
- `docs/agent-brief-rules.md` applies: no `git stash`, no `reset --hard`, no `checkout --`, no push, no subagents,
  no `find /`, no inline Python edits (use Edit), kill your own background processes.
- Record every attempt, kept or not, with its edit and its number (§2 goal 3, method doc §5): in the commit
  message for a kept one, in Task 7's method-doc entry for a rejected one.
- If `generate` gives counts more than 5 STATE away from the spec's measured number for that candidate, the edit
  is not the measured one: diff it against the scratch edit script (copied in Task 1) before going on.

## Spec conflicts resolved by this plan

1. **G9's census note does not cover every moved key (measured 2026-10-22 by running `census.census()` over the
   scratch grammars).** A slot that moves inside the same rule keeps its hosts and aliases as the note says. But a
   boundary that moves into a new hidden rule changes its hosts: `routes()` climbs from the hidden rule to its
   visible callers, which are the rules it was factored out of. C1 moves `bnd:preproc_split_if_begin_else:condition:{start,end}`
   and `bnd:preproc_split_if_then_begin_else_shared:condition:{start,end}` (25 statement hosts each) to
   `bnd:_split_if_begin_else_head:condition:{start,end}` with hosts `{preproc_split_if_begin_else,
   preproc_split_if_then_begin_else_shared}`. `registry._alias_problem` refuses that ("covers hosts ... that X
   never covered"), so `census --check` cannot pass with alias rows alone. C4 (`occ:_case_branch_tail:1.0.1`) and
   C5 (`bnd:_case_head_body:expression:*`) hit the same refusal. **Resolution (Task 2, first commit):** extend
   `_alias_problem` so that a live host is also covered when it is the rule named by the retired key of any alias
   to the same live key, i.e. the rule the slot was factored out of. Frozen cell ids stay unchanged, which is what
   G9 asks. Record it as an execution amendment in the spec.
2. **C4 is conditional on the stop rule, not only on G11/G12.** C1 + C2 + C3 measure 26,968, below the target, so
   the stop rule ends the batch after C3 and C4 is not attempted. C4 (and C5) run only through Task 5, when the
   batch after C3 ends above 27,400 (for example, when C2 fails and C1 + C3 is 27,458).

## Review Focus

1. **Comments and transparent directives** (`// c`, `/* c */`, `#region R`/`#endregion`, `#pragma warning disable X`)
   between the tokens of a factored unit (inside C1's head, between C2's `#if` and `end`) must give the predecessor's
   tree. Test: `mutate_parity.py` class `extras`, every candidate task.
2. **CRLF line endings and mixed-case keywords and directives** (`IF … THEN BEGIN`, `#IF`, `#Else`, `End;`) in a
   factored construct must give the predecessor's tree. Test: classes `crlf` and `case`.
3. **An incremental edit that turns one factored construct into its sibling** (delete the `begin` after the first
   arm's `then`; delete the guard's `end`), so a reused hidden node now belongs to another parent, must give the
   fresh tree. Test: class `incremental` (each line deleted and re-inserted).
4. **Long runs and nesting of the factored constructs** (N consecutive split-if units in one procedure; units
   nested in `#if` arms) must stay linear: C1 and C2 add forks inside `#if` statement arms. Test: the
   `d1_series()` scaling series added in Task 2 Step 3, run under G11.
5. **Half-typed input in an editor** (each selected input truncated after every line) must give the
   predecessor's tree wherever the predecessor's tree is clean; recovery-tree differences are reported, not
   failed. Test: class `truncate`.

---

## File Structure

- `grammar.js`: the conflicts array (627-1140) and the split-if rules (4884-4894, 5411-5467, 5493-5542,
  5620-5636); case rules (6384-6614) only if Task 5 runs.
- `src/parser.c`, `src/grammar.json`, `src/node-types.json` (the last must stay byte-identical).
- `tools/b7_audit/registry.py`, `tools/b7_audit/tests/test_registry.py` (Task 2, conflict 1).
- `tools/b7_audit/key-aliases.tsv`, `tools/b7_audit/registry.tsv` (live rows, per candidate), `tools/b7_audit/assertions.tsv`
  (refresh), `tools/b7_audit/evidence.jsonl.gz` and `docs/b7-separator-continuation-matrix.md` (Task 6).
- `tools/perf/strict_lists_scaling.py`, `tools/perf/tests/test_strict_lists_scaling.py` (Task 2: `d1_series()`).
- Untracked scratch, never committed: `/work/tsal-wt/d1-base` (worktree of `960ed31`), `.cache/d1/libs/*.so`,
  `.cache/d1/tools/` (parity scripts), `.cache/d1/ab/*.json`, `.cache/d1/oracle-*`, `.snapshots/baseline-d1-*`.
- Docs (Task 7): `docs/state-reduction-method.md`, `CHANGELOG.md` (the re-measured metrics; CLAUDE.md has no metrics table since 9f5a439, by user decision),
  `docs/superpowers/plans/2026-09-28-roadmap-remaining-work.md` (D1 row), `docs/deferred-work.md` (items 51, 58,
  61, 62), the spec's execution amendments, `tree-sitter-al.wasm` and its stamp.

## The candidate procedure (CP)

Tasks 2-5 run this with `CAND` (`c1`, `c2`, …) and `PRED` (the last landed library name: `base`, `c1`, …).
"Selected types" are the visible rules the candidate touches (each task lists them).

- **CP1 (before the edit):** `./tools/tree-harness.sh snapshot ./BC.History .snapshots/baseline-d1-$CAND`.
  `.cache/d1/libs/$PRED.so` must exist.
- **CP2 (after the edit):** `./tools/ts-lock.sh tree-sitter generate 2>&1 | tee .cache/d1/gen-$CAND.log`. An
  "Unresolved conflict" error: add the set the task lists (in `grammar.js` `conflicts`, with a one-line comment
  naming D1 and the candidate); never a set the task does not list, never a `prec` change. A warning naming
  unnecessary conflicts: delete exactly those sets, regenerate. Then G1 `./tools/metrics.sh --vs 960ed31`; record
  STATE, LARGE, SYMBOL, conflicts (`jq '.conflicts|length' src/grammar.json`), `wc -c < src/parser.c`.
- **CP3:** G2 `git diff --exit-code src/node-types.json` → no output, exit 0.
- **CP4:** G3 `./tools/ts-lock.sh tree-sitter test 2>&1 | tail -3` → the Task 1 case count, 0 failures;
  `git diff --stat test/corpus` → empty.
- **CP5:** `./tools/ts-lock.sh tree-sitter build --output .cache/d1/libs/$CAND.so`.
- **CP6:** G4 `./tools/tree-harness.sh verify ./BC.History .snapshots/baseline-d1-$CAND` → 0 changed.
- **CP7:** G7 `python -I .cache/d1/tools/fixtures.py .cache/d1/libs/$PRED.so .cache/d1/libs/$CAND.so` → the Task 1
  case count, `0 differ` (C2: exactly one, see Task 3).
- **CP8:** Review Focus 1-3, 5: `python -I .cache/d1/tools/mutate_parity.py .cache/d1/libs/$PRED.so
  .cache/d1/libs/$CAND.so --types <selected types>` → exit 0; record each class's line in the commit message.
- **CP9:** G9 `./tools/ts-lock.sh python -m tools.b7_audit assert --refresh` → 0 rows flipped;
  `python -m tools.b7_audit census --check` → exit 0 after the task's alias and live rows (below);
  `./tools/ts-lock.sh ./validate-grammar.sh` → exit 0.
  **Alias and live rows**, per moved key, following B7b-2 Task 4 and B7b-3 Task 4: one `key-aliases.tsv` row
  (`retired_key, live_key, role, family, reason, commit`), and in `registry.tsv` one row per retired row with the
  key replaced by the live key, `equiv` = the retired key, the reason starting `Live key of the retired <key>
  (tools/b7_audit/key-aliases.tsv, D1 <Cn>):`, and the route set to the live key's hosts that `census --list`
  prints for it. The retired rows stay.
- **CP10 (only if the task added a conflict):** G11 `./tools/ts-lock.sh python tools/perf/strict_lists_scaling.py
  --lib .cache/d1/libs/$PRED.so --md > .cache/d1/scaling-$PRED.md` (reuse if present) and the same for `$CAND`
  → both exit 0, the same series in exceptions, no series moved from pass to exception.
- **CP11:** G12, the speed rule above, with BEFORE `.cache/d1/libs/$PRED.so`, AFTER `.cache/d1/libs/$CAND.so`,
  outputs `.cache/d1/ab/d1-$CAND-{dc,bc-history}-{1,2}.json`, `uptime` recorded beside each run.
- **CP12:** trailer: `./tools/ts-lock.sh ./parse-al-parallel.sh ./BC.History/ . 2>&1 | tail -8`.
- **CP13 (a gate fails):** do not commit. Restore `grammar.js` and the generated trio with
  `git show HEAD:<path> > <path>`, write the rejected attempt (edit, counts, failing gate and output) into
  `.cache/d1/rejected.md` for Task 7, and go to the next task. A G3/G4/G7 difference on valid input is a failure
  (no exception exists for it).

---

### Task 1: Baseline at `960ed31`

**Files:** none tracked. Creates `/work/tsal-wt/d1-base`, `.cache/d1/`.

**Interfaces:**
- Produces: `.cache/d1/libs/base.so`; `.cache/d1/tools/{parity.py,fixtures.py,mutate_parity.py}`;
  `.cache/d1/scratch-spec/` (copies of the spec's `e_*.py` edit scripts); `.cache/d1/baseline.md` holding the
  `960ed31` metrics, suite case count, fixture case count, has_error results and the oracle summary;
  `.cache/d1/oracle-base/`.
- `mutate_parity.py LIB_A LIB_B --types T[,T...]`: selects every corpus-case input (fixtures.py's splitter) whose
  LIB_A tree contains a node of a listed type; for each class `extras`, `crlf`, `case`, `truncate` builds the
  mutated inputs and compares `parity.rows()` under both libraries; class `incremental` deletes and re-inserts each
  line of each selected input with `tree.edit` + `parse(new, old_tree)` under LIB_B and compares with a fresh LIB_B
  parse. Prints `<class>: <inputs> inputs, <n> differ (clean before), <m> differ (error before, reported)`
  (`incremental: <edits> edits, <n> mismatch`). Exit 1 iff any clean-before difference or incremental mismatch, or
  0 inputs selected.

- [ ] **Step 1: Worktree and library.** `git worktree add /work/tsal-wt/d1-base 960ed31`; in it
  `ln -s /work/src/BC.History BC.History && ln -s /work/src/DC DC && ln -s /work/tsal-wt/main/H: H:`;
  `./tools/ts-lock.sh tree-sitter build --output /work/tsal-wt/main/.cache/d1/libs/base.so`. Check
  `cmp /work/tsal-wt/d1-base/src/parser.c /work/tsal-wt/main/src/parser.c` → identical (HEAD changed only docs).
- [ ] **Step 2: Scratch tools.** Copy `parity.py`, `fixtures.py` and `e_*.py` from
  `/tmp/claude-1000/-work-tsal-wt-main/97b0c583-7d25-4579-bc56-6dcc8d248d3a/scratchpad/d1/` into `.cache/d1/tools/`
  and `.cache/d1/scratch-spec/`. Write `mutate_parity.py` (interface above; it imports `load`, `rows` from
  `parity.py` and the splitter from `fixtures.py`, factoring that splitter into a function if needed).
  Mutations: `extras` inserts `// c` and `#region R` … `#endregion` lines after every directive line and `/* c */`
  before every `then`/`end`; `crlf` replaces `\n` by `\r\n`; `case` upper-cases every `if then begin end else`
  word and capitalises every directive word; `truncate` cuts after each line.
- [ ] **Step 3: Self-check the scripts.** `python -I .cache/d1/tools/fixtures.py .cache/d1/libs/base.so
  .cache/d1/libs/base.so` → `0 differ`; record its case count (the spec measured 3,570).
  `python -I .cache/d1/tools/mutate_parity.py .cache/d1/libs/base.so .cache/d1/libs/base.so --types
  preproc_split_if_begin_else,preproc_split_if_then_begin_else_shared` → exit 0, every class `0 differ`, inputs > 0.
- [ ] **Step 4: Base measurements** into `.cache/d1/baseline.md`: `./tools/metrics.sh` (expect 28,742 / 10,562 /
  1,325 / 68,647,284 B), `jq '.conflicts|length' src/grammar.json` (272), the suite count from
  `./tools/ts-lock.sh tree-sitter test 2>&1 | tail -3`, and G6 BEFORE:
  `python tools/has_error_sweep.py --lib .cache/d1/libs/base.so --root <R>` for `./BC.History`, `./DC`,
  `$AL_BC28_ROOT`, `$AL_BCAPPS29_ROOT`, and `--corpus-fixtures` (each exit code and its listed files).
- [ ] **Step 5: G8 BEFORE (about 22 min).** In `/work/tsal-wt/d1-base`:
  `./tools/ts-lock.sh python -m tools.config_oracle run --tier full --root ./BC.History --root ./DC --root
  $AL_BC28_ROOT --root $AL_BCAPPS29_ROOT --report /work/tsal-wt/main/.cache/d1/oracle-base 2>&1 | tee
  /work/tsal-wt/main/.cache/d1/oracle-base.log` → exit 0. If it exits 2 on a corpus label, report it: the before
  run needs the labels resolved there.
- [ ] **Step 6:** no commit (nothing tracked changed; `git status --short` shows only untracked paths).

### Task 2: C1 — share the split-if begin/else head (§4 C1)

**Files:** Modify `tools/b7_audit/registry.py` (`_alias_problem`, 97-123), `tools/b7_audit/tests/test_registry.py`,
`tools/perf/strict_lists_scaling.py`, `tools/perf/tests/test_strict_lists_scaling.py`, `grammar.js` (conflicts at
788 and 794-797; rules at 5493-5542), the generated trio, `tools/b7_audit/key-aliases.tsv`,
`tools/b7_audit/registry.tsv`, `tools/b7_audit/assertions.tsv`, the spec (execution amendment 1).

**Interfaces:**
- Consumes: Task 1's libraries and scripts.
- Produces: hidden rule `_split_if_begin_else_head` (Task 3's conflicts name it); `.cache/d1/libs/c1.so`;
  `d1_series()` in `strict_lists_scaling.py`; the extended alias rule (Tasks 3-5 rely on it).

- [ ] **Step 1: Failing alias test.** In `test_registry.py`, `test_alias_live_host_may_be_the_factored_rule`:
  using `_alias_world()`'s pattern, two aliases `bnd:r1:f:end → bnd:_h:f:end` and `bnd:r2:f:end → bnd:_h:f:end`,
  retired rows with hosts `{s1}` and `{s2}`, live key pairs and live rows on hosts `r1` and `r2`;
  `registry.gate(...)` → `stale == []` and no `invalid`. And `test_alias_live_host_outside_factored_rules_fails`:
  the same plus a live host `r3` → an `invalid` entry containing "never covered". Run
  `python -m pytest tools/b7_audit/tests/test_registry.py -q` → the first FAILS, the second passes.
- [ ] **Step 2: Extend `_alias_problem(a, rows, live_keys, aliases=())`.** Allowed hosts = hosts of the retired rows
  plus `{x.retired.split(":")[1] for x in aliases if x.live == a.live}`; `gate()` passes its `aliases`. Update the
  docstring. `python -m pytest tools/b7_audit/tests -q` → all pass; `python -m tools.b7_audit census --check` →
  exit 0 on the unchanged grammar. Commit `fix(b7-audit): an alias may move a slot into a hidden rule factored out
  of the retired rule (D1)`, with the trailer.
- [ ] **Step 3: Scaling series for Review Focus 4.** Add `d1_series()` beside `b7b2_series()` (same `LENGTHS`,
  `DEPTHS`, limits) and include it in the run loop at line 382: `split-if-begin-else` length (N units of
  `#if A\nif X then begin\nY();\n#else\nif X then\n#endif\nZ();\n#if A\nend;\n#endif\n` in `CODE_HOST`),
  `split-if-then-begin` length (N units of `#if A\nif X then begin\n#endif\nZ();\n#if A\nend;\n#endif\n`), and
  `split-if-begin-else` depth (the unit nested D deep in `#if B … #endif` arms). Confirm each unit with
  `python tools/snip.py` (the first gives `preproc_split_if_begin_else`, the second `preproc_split_if_then_begin`,
  `has_error` False). Test `test_d1_series_use_the_unchanged_grid` (grid equal to `LENGTHS`/`DEPTHS`, family set
  exactly the two names). `python -m pytest tools/perf/tests/test_strict_lists_scaling.py -q` → pass. Then
  `./tools/ts-lock.sh python tools/perf/strict_lists_scaling.py --lib .cache/d1/libs/base.so --md >
  .cache/d1/scaling-base.md` → exit 0 with the new series linear. If a new series is not linear on `base`, stop
  and report: that is a pre-existing limit, not D1's.
- [ ] **Step 4: CP1** (`CAND=c1`, `PRED=base`).
- [ ] **Step 5: Edit.** Add above `preproc_split_if_begin_else`, keeping both rules' comments:
  ```js
  _split_if_begin_else_head: $ => prec(26, seq(
    $.preproc_if, repeat($._statement), $.if_keyword, $._region_root_condition, $.then_keyword,
    $.begin_keyword, repeat($._statement),
    $.preproc_else, repeat($._statement), $.if_keyword, $._region_root_condition, $.then_keyword,
  )),
  ```
  and replace those twelve members at the start of `preproc_split_if_then_begin_else_shared` (5494-5505) and
  `preproc_split_if_begin_else` (5526-5537) with `$._split_if_begin_else_head,`. Both rules keep their own
  `prec.right(26`/`prec(26`. The head keeps `prec(26)`: without it the generator asks for
  `[_split_if_begin_else_head, if_statement]`, a fork on every `if` (§4 C1); that set is never added.
- [ ] **Step 6: CP2.** Conflicts to add (the two sets at 788 and 794-797 with the head in place of both rules):
  `[$._open_branch, $._preproc_split_then_begin_open, $._split_if_begin_else_head, $._preproc_branch_statement]`
  and `[$._preproc_branch_statement, $._preproc_split_then_begin_open, $._split_if_begin_else_head,
  $._preproc_end_branch, $._open_branch, $.preproc_split_else_begin_over_endif]`. Delete the old sets at 788 and
  794-797 if the generator reports them unnecessary. Expected: **27,511 STATE, 9,704 LARGE, 63,750,805 B**.
- [ ] **Step 7: CP3-CP8.** CP8 types: `preproc_split_if_begin_else,preproc_split_if_then_begin_else_shared`.
- [ ] **Step 8: CP9.** Moved keys (measured from the scratch grammar; confirm with `census --check`):
  `occ:preproc_split_if_then_begin_else_shared:0.15.0.0 → :0.4.0.0` (same 25 hosts);
  `bnd:preproc_split_if_begin_else:condition:start|end` and
  `bnd:preproc_split_if_then_begin_else_shared:condition:start|end → bnd:_split_if_begin_else_head:condition:start|end`
  (live hosts `preproc_split_if_begin_else`, `preproc_split_if_then_begin_else_shared`). Add the alias and live
  rows (CP9). A live host that is neither a retired host nor a factored rule is a failure (CP13).
- [ ] **Step 9: CP10-CP12.**
- [ ] **Step 10: Spec amendment.** Add "Execution amendments" to the spec: item 1 (conflict 1 above, with the
  measured key list and the `_alias_problem` rule) and item 2 (C4 is reached only through the stop rule).
- [ ] **Step 11: Commit** `grammar.js`, the trio, `strict_lists_scaling.py` and its test, the two B7a tsv files,
  `assertions.tsv`, the spec: `perf(d1): C1 share the split-if begin/else head` with the counts, conflicts
  before/after, G7 `0 of N`, CP8 lines, G11 and G12 ratios with `uptime`, "B7a evidence hashes not refreshed",
  the trailer.

### Task 3: C2 — share `#if stmts* end` (§4 C2)

**Files:** Modify `grammar.js` (conflicts at 770 and Task 2's sets; rules at 4884-4888, 5411-5416, 5459-5462), the
trio, `key-aliases.tsv`, `registry.tsv`, `assertions.tsv`.

**Interfaces:**
- Consumes: `_split_if_begin_else_head` (Task 2), `.cache/d1/libs/c1.so`, the extended alias rule.
- Produces: hidden rule `_split_stmts_end`; `.cache/d1/libs/c2.so`.

- [ ] **Step 1: CP1** (`CAND=c2`, `PRED=c1`).
- [ ] **Step 2: Edit.** Add above `_preproc_end_guard`:
  `_split_stmts_end: $ => seq($.preproc_if, repeat($._statement), $.end_keyword),` and replace
  `$.preproc_if, repeat($._statement), $.end_keyword,` with `$._split_stmts_end,` at exactly three sites: the start
  of `preproc_split_else_begin_over_endif` (4885-4887), the start of `_preproc_end_guard` (5460-5462), and the
  second `#if` of `preproc_split_if_then_begin` (5414-5416, the line with `// allow preamble before end`; keep
  that comment on the new line). No `prec` on the new rule.
- [ ] **Step 3: CP2.** Conflicts to add: `[$._split_stmts_end, $._preproc_end_branch]`,
  `[$._split_stmts_end, $._preproc_end_branch, $._preproc_branch_statement]`,
  `[$._open_branch, $._preproc_split_then_begin_open, $._split_stmts_end, $._split_if_begin_else_head,
  $._preproc_end_branch, $._preproc_branch_statement]`. Delete what the generator reports unnecessary (expected:
  Task 2's six-member set and the set at 770). Expected: **27,021 STATE, 9,437 LARGE, 61,993,440 B**.
- [ ] **Step 4: CP3-CP6.**
- [ ] **Step 5: CP7, the classified exception.** Expected output: exactly one differing case,
  `b7_gap_split_if_begin_test.txt` "B7a GAP: split-if-begin / first-replace". Any other differing case → CP13.
  Check it is still a failure: it carries `:error`, `./tools/ts-lock.sh tree-sitter test --file-name
  b7_gap_split_if_begin_test.txt` passes, it is listed in `tools/deliberate-negatives.txt` (line 195), and
  `python tools/has_error_sweep.py --lib .cache/d1/libs/c2.so --corpus-fixtures` lists it as a visible negative as
  it did on `base`. `python -m tools.config_oracle run --tier quick` → exit 0, so
  `tools/config_oracle/fixture-classes.tsv` needs no change. Save `tree-sitter parse` output of that case's input
  under both libraries to `.cache/d1/c2-exception-{c1,c2}.txt` for the commit message.
- [ ] **Step 6: CP8.** Types: `preproc_split_else_begin_over_endif,preproc_split_if_then_begin,preproc_split_if_begin_else,preproc_split_code_block_over_endif,preproc_fragmented_else_tail`.
  A clean-before difference fails; a reported error-before difference is listed in the commit message.
- [ ] **Step 7: CP9.** Moved keys, all same-rule and same-host: `occ:_preproc_end_guard:3.0 → :1.0`,
  `occ:preproc_split_else_begin_over_endif:0.3.0.0.0 → :0.1.0.0.0`,
  `occ:preproc_split_if_then_begin:0.5.0.0 → :0.3.0.0`.
- [ ] **Step 8: CP10-CP12.** CP10 is required: C2's three conflicts fork inside `#if` statement arms.
- [ ] **Step 9: Commit** `perf(d1): C2 share #if stmts* end` with the CP2 counts, the G7 exception record
  ("USER DECISION 2026-10-22, spec §2: recovery tree of b7_gap_split_if_begin_test.txt 'B7a GAP: split-if-begin /
  first-replace' changed; still :error; old/new top lines"), G11, G12, "B7a evidence hashes not refreshed", the
  trailer. If C2 fails G11 or G12 (CP13), Task 4 runs on top of C1 with `PRED=c1`.

### Task 4: C3 — share `#endif stmts* <end guard>` (§4 C3)

**Files:** Modify `grammar.js` (the three sites ending in `$._preproc_end_guard,` after `$.preproc_endif,
repeat($._statement),`: in `preproc_split_if_begin_else`, `preproc_split_code_block_over_endif` 5623-5626,
`preproc_fragmented_else_tail` 5633-5635; not line 5355), the trio, `assertions.tsv`.

**Interfaces:**
- Consumes: `.cache/d1/libs/$PRED.so` (`c2`, or `c1` if C2 was dropped).
- Produces: hidden rule `_endif_stmts_end_guard`; `.cache/d1/libs/c3.so`.

- [ ] **Step 1: CP1** (`CAND=c3`).
- [ ] **Step 2: Edit.** Add above `_preproc_end_guard`:
  `_endif_stmts_end_guard: $ => seq($.preproc_endif, repeat($._statement), $._preproc_end_guard),` and replace
  the three-member tail with `$._endif_stmts_end_guard,` at the three sites (comments on the replaced lines move
  to the new rule).
- [ ] **Step 3: CP2.** No conflict expected; if the generator asks for one, CP13 (C3 was measured conflict-free).
  Expected on C1 + C2: **26,968 STATE, 9,389 LARGE, 61,703,620 B**. On C1 alone: **27,458 / 9,656**.
- [ ] **Step 4: CP3-CP8.** CP7 → `0 differ` against `$PRED`. CP8 types:
  `preproc_split_if_begin_else,preproc_split_code_block_over_endif,preproc_fragmented_else_tail`.
- [ ] **Step 5: CP9.** No key moves expected (`census --check` exit 0 with no new rows).
- [ ] **Step 6: CP11-CP12** (no CP10: no conflict).
- [ ] **Step 7: Commit** `perf(d1): C3 share #endif stmts* end-guard` with counts, G12, the note, the trailer.

### Task 5: Stop or search; C4 and at most one more candidate

**Files:** only if a candidate runs: `grammar.js` (case rules 6384-6614 and conflicts), the trio, B7a tsv files.

**Interfaces:**
- Consumes: the last landed library and STATE/LARGE from `./tools/metrics.sh`.
- Produces: the final batch commit (`FINAL`), recorded in `.cache/d1/baseline.md` as `final: <lib name> <sha>`.

- [ ] **Step 1: Decide** with the stop rule (Global Constraints). STATE ≤ 27,400: stop; record the decision in
  `.cache/d1/baseline.md` with any shortfall against 27,300 STATE or 9,700 LARGE, and go to Task 6. Expected after
  Tasks 2-4: 26,968 / 9,389, stop with no shortfall.
- [ ] **Step 2 (only above 27,400): C4.** CP1 (`CAND=c4`). Add before `_case_group_item`:
  `_case_branch_tail: $ => seq($._case_body_branch, optional(seq(repeat(caseEmptyGroup($)), ';'))),` and use it
  in `case_branch` (6562-6563), `preproc_split_case_branch` (6580-6581) and `preproc_split_case_extended`
  (6612-6613); not in `preproc_split_case_end_branch`. CP2: conflict `[$._case_branch_tail]` (self-conflict);
  expected −141 / −12 against its predecessor. CP3-CP8 (types `case_branch,preproc_split_case_branch,preproc_split_case_extended`),
  CP9 (moved: `occ:case_branch:0.3.0.1`, `occ:preproc_split_case_branch:0.8.0.1`,
  `occ:preproc_split_case_extended:0.8.0.1 → occ:_case_branch_tail:1.0.1`), CP10 (the existing `case-*` series
  cover it), CP11 on **both** corpora, CP12. Lands only if G11 and G12 pass. Commit
  `perf(d1): C4 share the case-branch tail`. Re-run Step 1.
- [ ] **Step 3 (only if still above 27,400): one more candidate.** Either C5's `_case_head_body` (§4 C5: `seq(case_keyword,
  _region_root_expression, of_keyword, optional(field('body', case_body)))` in `case_statement` and
  `preproc_split_case_statement_end`, conflict `[$._case_head_body]`, −185 / −90, parity unchecked), or one
  split-if/split-case prefix or tail ending at `then`, `end` or `#endif` spelled out in two or more rules, measured
  first by the scratch method (`.cache/d1/scratch-spec/`). Same CP. No third candidate.
- [ ] **Step 4:** If still above 27,400: stop and report the batch and the shortfall to the controller.

### Task 6: Final gate against `960ed31`

**Files:** `tools/b7_audit/evidence.jsonl.gz`, `tools/b7_audit/assertions.tsv`,
`docs/b7-separator-continuation-matrix.md`.

**Interfaces:**
- Consumes: `.cache/d1/libs/base.so`, `.cache/d1/libs/$FINAL.so`, Task 1's baseline file and oracle report.
- Produces: the gate commit and the numbers Task 7 documents (`.cache/d1/final.md`).

- [ ] **Step 1: G1.** `./tools/metrics.sh --vs 960ed31`; conflicts count; STATE ≤ 27,300 and LARGE ≤ 9,700, or the
  Task 5 shortfall.
- [ ] **Step 2: G5.** `python -m tools.perf delta --lib-a .cache/d1/libs/base.so --lib-b .cache/d1/libs/$FINAL.so
  --corpus all --out .cache/d1/delta.json` → 0 files changed; BCApps-29.0's one file only as `tools/perf/delta-reviewed.tsv` records it.
- [ ] **Step 3: G6.** `python tools/has_error_sweep.py --lib .cache/d1/libs/$FINAL.so --root <R>` for the four
  corpora, and `--corpus-fixtures` → exit codes and file lists equal to Task 1 Step 4.
- [ ] **Step 4: G8 (about 22 min).** In `/work/tsal-wt/main`: the G8 command with `--report .cache/d1/oracle-final
  2>&1 | tee .cache/d1/oracle-final.log` → exit 0; `diff .cache/d1/oracle-base.log .cache/d1/oracle-final.log`
  differs only in timing, parser-hash and checkout-path lines; any other line → stop and report.
- [ ] **Step 5: G9 full.** `./tools/ts-lock.sh python -m tools.b7_audit assert --refresh` (0 flips),
  `./tools/ts-lock.sh python -m tools.b7_audit run` (full; warm ~5 min, cold ~3 h), `python -m tools.b7_audit report`,
  `python -m tools.b7_audit census --check` → 0; `git diff docs/b7-separator-continuation-matrix.md` touches only
  the hash header; `python -m tools.b7_audit manifest --check --manifest tools/b7_audit/b7b1-manifest.tsv` and the
  same for `b7b2-` and `b7b3-manifest.tsv` → exit 0.
- [ ] **Step 6: G10.** `python -m tools.perf incremental --corpus <R>` for `bc-history`, `dc`, `bc28.1`,
  `bcapps-29.0` → exit 0 each. Speed: in one session, `python -m tools.perf incremental --corpus dc --out
  /work/tsal-wt/main/.cache/d1/inc-base-1.json` run in `/work/tsal-wt/d1-base`, then the same in
  `/work/tsal-wt/main` to `inc-final.json`, then base again to `inc-base-2.json`; report ms per edit; a final
  value above both base runs by more than their spread fails.
- [ ] **Step 7: G11.** CP10 with `base` and `$FINAL`.
- [ ] **Step 8: G12 for the record.** The speed rule's two runs per corpus, `base` vs `$FINAL`, outputs
  `.cache/d1/ab/d1-batch-{dc,bc-history}-{1,2}.json`, `ab_accept` on each pair, `uptime` recorded.
- [ ] **Step 9: G13.** `./tools/ts-lock.sh ./validate-grammar.sh --full` → green;
  `python -m tools.query_coverage.qc run` → exit 0; `python tools/check-field-types.py` → pass (node-types is
  unchanged, so no row changes).
- [ ] **Step 10: Commit** the three B7a files: `feat(b7-audit): D1 gate, evidence refreshed at the batch parser`
  with every number from Steps 1-8 and the trailer.

### Task 7: Docs and close-out

**Files:** `docs/state-reduction-method.md`, `CHANGELOG.md` (`## [Unreleased]`, `### Changed` at line 42),
`docs/superpowers/plans/2026-09-28-roadmap-remaining-work.md` (D1 row, line
115), `docs/deferred-work.md` (items 51, 58, 61, 62), `tree-sitter-al.wasm`, `tree-sitter-al.wasm.inputs.sha256`.

**Interfaces:**
- Consumes: `.cache/d1/baseline.md`, `.cache/d1/final.md`, `.cache/d1/rejected.md`, the commit messages.

- [ ] **Step 1: Method doc.** §2: a pass-5 row (`960ed31` → final commit, STATE 28,742 → final, `parser.c`
  65.5 MiB → final MiB, evidence "four-corpus `delta` 0 files, `node-types.json` byte-identical") and C1-C3 (and
  any Task 5 unit) in the units list with their numbers. §3: the rejected attempts with edit and number: the
  further if-open head `_split_if_open_head` (−20, needed conflicts naming `if_statement` and
  `_if_statement_no_else`), the head without `prec(26)` (same count, adds `[_split_if_begin_else_head,
  if_statement]`), family merging of ML and Namespaces (fails at generate: `ENU='x'` is both pairs), C5's
  self-conflict if not landed, and every CP13 entry. §4: on Linux the corpus labels resolve in the D1 checkout
  (spec §5), and the alias rule of amendment 1.
- [ ] **Step 2: CHANGELOG.** Under `### Changed`: one entry "Parser tables reduced (roadmap D1), no tree change":
  STATE, LARGE, conflicts, `parser.c` bytes/MiB before and after, the four-corpus delta and `ab` ratios, and the
  one recovery-tree change in a deliberate-negative fixture.
- [ ] **Step 3: Metrics in the CHANGELOG entry,** re-measured, not copied: `wc -c src/parser.c`,
  `grep -E 'SYMBOL_COUNT|STATE_COUNT' src/parser.c`, `wc -l grammar.js`, the suite count. Do NOT re-add a metrics
  table to CLAUDE.md (removed in 9f5a439 by user decision; `./tools/metrics.sh` is the source).
- [ ] **Step 4: Roadmap D1 row:** **DONE <date>**, spec and plan paths, the counts, the gate results, the commits.
- [ ] **Step 5: deferred-work.** Items 61, 62, 51 (shape 3) and 58: one line each, "Room after D1: <28,770 −
  final> STATE / <10,723 − final LARGE> LARGE under the ceilings; measure this item's real cost against
  <final commit> (spec §10)."
- [ ] **Step 6: WASM.** `./tools/ts-lock.sh tree-sitter build --wasm -o tree-sitter-al.wasm`,
  `tools/check-wasm-fresh.sh --update`, then `tools/check-wasm-fresh.sh` → exit 0.
- [ ] **Step 7: Commit** `docs(d1): method doc pass 5, CHANGELOG, metrics, roadmap, deferred items; wasm` with the
  trailer.
- [ ] **Step 8: Clean up.** `git worktree remove /work/tsal-wt/d1-base` (no `--force`; report a refusal);
  `rm -rf .snapshots/baseline-d1-*`; `tools/session-cleanup.sh --procs`. Keep `.cache/d1/` for the review.
