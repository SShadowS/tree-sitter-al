# D1: the state-reduction pass (design)

**Status:** design, 2026-10-22, branch `feat/d1-state-reduction` cut from main `960ed31` (the B7b-2 merge).
The user said "do it" and skipped the design questions, so the controller made every open call. Each one is
marked **(controller's call)**. Four calls are the user's own and are marked **USER DECISION**: correctness first
(section 1), structural `#if` modelling stays (section 8.3), C2's recovery-tree exception (sections 2 and 4) and
speed as a gate (section 2).
The builder check's four questions were settled on 2026-10-22: stop or search (section 10), where the corpus-label
commands run (G8), the B7a cadence (G9) and the speed rule (section 7).

Every number below was measured on 2026-10-22 in scratch copies of the tree at `960ed31`, unless it is marked
*estimate* or *from another document*. Scratch work: `/tmp/claude-1000/-work-tsal-wt-main/97b0c583-7d25-4579-bc56-6dcc8d248d3a/scratchpad/d1/`.
Section 9 says how it was measured and what that does not prove.

## 1. Intent and why now

> **USER DECISION (2026-10-22):** "the goal is that al-sem has the best parsed ast for its analysis. I would prefer
> the parser doesn't get slower or bigger, but correctness is our goal."

The priority order is **correctness first, then size and speed**.
- D1 exists to make room for correctness fixes: items 61, 62 and 51 shape 3, and the typed `in` right (item 58).
  It must never trade correctness for states. No reduction may change a valid input's tree.
- Where a later correctness fix needs more than the room D1 makes, correctness wins. The STATE and LARGE ceilings
  and the speed gate are strong preferences. Crossing one is reported; it is never a reason to leave a tree wrong.

D1 makes room in the parse table without changing any valid input's tree, so that the B7b-2 follow-ups can land
under the user's ceilings.

B7b-2 (`#if` groups inside expressions) took the grammar from 23,737 to 28,742 STATE. The user's ceilings are
strong preferences, not hard limits (see above):

| metric | main before B7b-2 (`4d75846c`) | now (`960ed31`) | ceiling | room |
|---|---|---|---|---|
| STATE_COUNT | 23,737 | 28,742 | 28,770 | **28** |
| LARGE_STATE_COUNT | 7,482 | 10,562 | 10,723 | 161 |
| SYMBOL_COUNT | 1,279 | 1,325 | none | |
| declared conflicts | 230 | 272 | none | |
| `parser.c` | 53,974,023 B (51.5 MiB) | 68,647,284 B (65.5 MiB) | 80 MiB | 14.5 MiB |

(`./tools/metrics.sh --vs 4d75846c`; the conflict counts are from `src/grammar.json`.)

Four follow-ups are waiting for room. The user's agreed order is the D1 spec, then the fixes for items 61 and 62,
then a release.

| follow-up | `docs/deferred-work.md` | state cost |
|---|---|---|
| a `#if` arm that holds only `-` or `not` ERRORs | item 61 | **+6** STATE / +5 LARGE, a rough prototype: a `_dangling_arm` choice of `_dangling_operand` or a bare `-`/`not`. It needed one more conflict, `[option_member, _dangling_arm]`. The real design is open, so the budget is 150. |
| a property value with a leading prefix and a tail ERRORs | item 62 | **+5** STATE / +1 LARGE, measured: `optional(preproc_conditional_expression_tail)` on `property_expression`'s leading-prefix arm. node-types.json is unchanged. Whether it fixes the witness is not checked. |
| a typed `in` prefix arm with a continuation before its keyword | item 51 shape 3 | not measured; the Task 10 attempt was reverted with no recorded number. The budget is 300 (an *estimate*). |
| a typed `in` right (the aliased list-literal group) | item 58 | **+209** STATE, *from the B7b-2 spec* (28,951 measured against 28,742) |

Summed, the budget is about 665 STATE. Today there are 28.

There is a second reason. B7b-2 made DC about 4% slower (`ab` 0.957-0.964, item 54). The user accepted that.
D1 must not add to it, and the dedicated speed pass stays in D2 (section 2). The scratch timing in section 7
suggests the candidates do not slow the parser, and perhaps gain a little.

## 2. Goals, non-goals, anti-goals

**Goals**
1. Reach the target in section 6: STATE ≤ 27,300 and LARGE ≤ 9,700 **(controller's call)**.
2. Reduce states only by tree-preserving factorings, the method of `docs/state-reduction-method.md` section 2.
   Each factoring is a complete unit shared as a hidden rule.
3. Record every attempt with its edit and its number, whether it is kept or not (method doc section 5).
   Rejected attempts are written up as well.

**Non-goals**
- Recovering B7b-2's 4% on DC. **USER DECISION (2026-10-22): speed is a gate, not a goal.** No candidate may
  regress (section 7). Any gain is reported but not required. The dedicated speed pass stays in D2.
- The follow-up fixes themselves (items 61, 62, 51 shape 3 and 58). D1 only makes room for them.
- The MSVC code generation of item 21. Its owner is E3. Do not tune the grammar against MSVC numbers.
- The quadratic scaling of items 52 and 53. They are known limits, decided by the user.

**Anti-goals.** Each of these fails D1, even if the counts go down. The first is correctness and is absolute.
The rest protect size and speed. Within D1 they fail a candidate, because a reduction that costs speed buys
nothing:
- trading correctness for states: any change to a tree (node, anonymous token, field, span, `has_error` or
  `is_missing`) on any of the four corpora or any corpus fixture. **One documented exception, a USER DECISION (2026-10-22):** the error-recovery
  tree of an input that already ERRORs may change, provided it is classified and recorded under gate G7. The only
  such change allowed so far is C2's, in the deliberate-negative fixture `b7_gap_split_if_begin_test.txt`. The
  exception covers recovery trees only. Every valid input keeps a byte-identical tree;
- any change to `src/node-types.json`;
- a parse-speed or incremental-parse regression;
- fewer states bought with a slower parser. A factoring that adds a GLR fork on a common path (a self-conflict
  on every `case`, say) is suspect until `ab` clears it;
- widening the accepted language. That includes merging two keyed property families, which over-accepts and can
  change trees (section 3.3).

## 3. Where the states are

### 3.1 The per-rule report

`tree-sitter generate --report-states-for-rule -` was run on a scratch copy. These are its top rules. The counts
overlap, so they rank rules but do not add up to anything:

`preproc_split_if_then_begin_else_shared` 1,227 · `preproc_split_if_begin_else` 971 · `logical_expression` 685 ·
`in_expression` 679 · `is_expression`/`as_expression` 670 · `property` 634 · `_empty_value_conditional` 623 ·
`multiplicative_expression`/`comparison_expression`/`additive_expression` 612 ·
`preproc_split_block_close_after_endif_repeat1` 598 · `property_repeat1` 557 ·
`preproc_split_else_begin_over_endif` 488 · `if_statement` 474 · `preproc_conditional_option_members` 420.

### 3.2 Marginal cost by stubbing one rule

Each rule's body was replaced with a dummy token and dropped from every declared conflict set. Then the grammar
was regenerated. The saving is STATE / LARGE:

| rule | saving | | rule | saving |
|---|---|---|---|---|
| `preproc_split_case_statement_end` | 1,334 / 509 | | `array_type` | 411 / 99 |
| `option_member` | 1,245 / 1,314 | | `preproc_split_if_begin_else` | 405 / 305 |
| `preproc_split_if_else_statement` | 707 / 317 | | `preproc_conditional_option_members` | 387 / 256 |
| `preproc_split_if_then_begin_else_shared` | 641 / 372 | | `preproc_split_block_end_in_else` | 337 / 240 |
| `preproc_split_else_begin_over_endif` | 478 / 211 | | `preproc_split_case_branch` | 296 / 90 |
| `_type_operand_group` | 291 / 142 | | `preproc_split_if_then_begin` | 288 / 96 |
| `preproc_split_if_statement` | 255 / 140 | | `preproc_split_call_statement` | 196 / 84 |
| `preproc_conditional_statement` | 168 / 121 | | `_preproc_end_guard` | 112 / 168 |

Stubbing an operator rule makes the count go **up**: `multiplicative_expression` −600, `_ternary_condition` −469,
`logical_expression` −409, `additive_expression` −305 and `_postfix_operand` −146. Removing those rules removes
precedence structure that the generator uses to merge states. So the stub method does not rank the expression
core, and D1 does not target it. Several rules cannot be stubbed alone, because the generator then reports an
unresolved conflict: `in_expression`, `is_expression`, `as_expression`, `comparison_expression`,
`_empty_value_conditional`, `option_member_list`, `preproc_split_open_statement`, `preproc_conditional_operand`
and `preproc_conditional_expression_tail`.

### 3.3 Cost by family: the rule and everything only it reaches

`prune.py` removes whole families. It makes every matching rule the empty language and lets that propagate:
a `seq` with an empty member is empty, a `choice` drops its empty members, and `repeat(empty)` matches nothing.
It also adds any conflict the generator asks for. The saving is STATE / LARGE:

| family removed | saving |
|---|---|
| `preproc_split_if*`, `else_begin_over_endif`, `block_end_in_else`, `block_close_after_endif`, `code_block_*`, `_preproc_split_then_begin_open`, `preproc_fragmented_else_tail` (13 rules) | **3,687 / 2,139** |
| `preproc_split_case_*` (4) | 3,144 / 1,563 |
| `_empty_value_conditional`, `_property_value_conditional`, `preproc_conditional_option_members` | 2,712 / 661 |
| `preproc_conditional_case`, `preproc_conditional_case_patterns` | 1,715 / 1,048 |
| `preproc_split_open_statement`, `preproc_split_call_statement`, `preproc_guarded_statement` | 1,522 / 1,106 |
| the B11 run machinery, per keyed family: ML 1,214 / 109, Namespaces 1,159 / 111, TableRelation 964 / 110, CalcFormula 924 / 113, generic 848 / 284, link 645 / 74 | 5,754 / 801 together |
| `preproc_split_declaration`/`field`/`table_field*`/`key`/`modify`/`report_*`/`brace_*`/… (15) | 1,147 / 376 |
| the B7b-2 groups, one at a time: operand prefix 650 / 463, operand group 638 / 413, typed group 313 / 156, receiver 159 / 46, tail 126 / 231 | |

These are upper bounds on what restructuring a family could ever save, not proposals. They show that the
statement-level split families (split-if and split-case) are the largest pool of states. They are also where
section 4's measured candidates come from.

**Family merging was tried and rejected** **(controller's call)**. The edit gave the ML and Namespaces properties
one shared B11 run machinery, with the value `choice(ml_value_list, namespace_value_list, …)`. It fails at
generate: `ENU='x'` is both an `ml_value_pair` and a `namespace_pair`, so the shared machinery has two readings of
the same text. Merging families would also make one family's value parse under another family's name, which
over-accepts (an anti-goal). Do not retry it unless the value languages are disjoint and an `:error` fixture
proves that the over-acceptance is still refused.

## 4. Candidates, ranked

Every candidate was applied to a scratch `grammar.js` and regenerated. Unless noted, it was then built (gcc -O2)
and compared with the base library. The comparison covers every node: type, field, byte span, `has_error`,
`is_missing`, anonymous tokens included. It ran over all four corpora (DC 1,352 files, BC.History 15,358,
BC28.1 16,928, BCApps-29.0 36,716) and over the inputs of all 3,570 corpus cases. "Conflicts" means the declared
conflicts the generator asked for.

### C1. Share the head of the two split-if begin/else rules (the winner)

`preproc_split_if_then_begin_else_shared` and `preproc_split_if_begin_else` both start with the same twelve
symbols:

```
#if stmts* if C then begin stmts* #else stmts* if C then
```

Extract that prefix into a hidden rule:

```js
_split_if_begin_else_head: $ => prec(26, seq(
  $.preproc_if, repeat($._statement), $.if_keyword, $._region_root_condition, $.then_keyword,
  $.begin_keyword, repeat($._statement),
  $.preproc_else, repeat($._statement), $.if_keyword, $._region_root_condition, $.then_keyword,
)),
```

Each of the two rules then starts with `$._split_if_begin_else_head`. The prefix ends at the hard keyword `then`
(method doc section 2), and the head carries the rules' `prec(26)`.

- **28,742 → 27,511 STATE (−1,231), 10,562 → 9,704 LARGE (−858).** `parser.c` 68,647,284 → 63,750,805 B
  (60.8 MiB).
- Conflicts: two, demanded by the generator. They are the two existing sets that name both rules, with the head
  in place of the rules. Each old set should then become unnecessary; the builder confirms that and deletes them.
- node-types.json: identical. Four corpora: 0 files differ. Corpus fixtures: 0 of 3,570 differ.
- Without `prec(26)` on the head, the count is the same, but the generator also asks for
  `[_split_if_begin_else_head, if_statement]`, a new fork against every ordinary `if`. Keep the prec.
- A further step was tried and rejected: share `#if stmts* if C then` between the head and
  `_preproc_split_then_begin_open`. It saved only 20 more, and it needed two conflicts naming `if_statement` and
  `_if_statement_no_else`.

### C2. Share `#if stmts* end` (on top of C1)

`preproc_split_else_begin_over_endif`, `_preproc_end_guard` and the second `#if` of
`preproc_split_if_then_begin` all read `seq($.preproc_if, repeat($._statement), $.end_keyword)`. Make that a
hidden `_split_stmts_end` and use it in all three.

- Alone: −500 / −277, with 3 conflicts. On top of C1: **27,021 / 9,437 (−490 / −267)**, `parser.c` 61,993,440 B
  (59.1 MiB).
- node-types.json: identical. Four corpora: 0 differ.
- **One fixture recovery tree changes**: the `:error` witness in `b7_gap_split_if_begin_test.txt`
  ("B7a GAP: split-if-begin / first-replace"). It is a deliberate negative, so the change is in error recovery
  only. **USER DECISION (2026-10-22): allowed** as the classified exception of section 2. The builder records it
  under gate G7, and the case must still fail as an `:error`.
- Three new conflicts: `[_split_stmts_end, _preproc_end_branch]`,
  `[_split_stmts_end, _preproc_end_branch, _preproc_branch_statement]`, and the big preprocessor set extended with
  `_split_stmts_end`. These are forks inside `#if` statement arms only, never on `#if`-free code. Because C2 adds
  conflicts, it needs the fork probes (G11).

### C3. Share `#endif stmts* <end guard>`

Three rules end with `seq($.preproc_endif, repeat($._statement), $._preproc_end_guard)`:
`preproc_split_if_begin_else`, `preproc_split_code_block_over_endif` and `preproc_fragmented_else_tail`. Make that
a hidden `_endif_stmts_end_guard`. It ends at the guard's `#endif`.

- Alone: **−270 / −230 with no new conflict**; fixtures 0 differ. But it overlaps C1: on top of C1 + C2 it adds
  only −53 / −48. That gives **26,968 / 9,389**, `parser.c` 61,703,620 B (58.8 MiB).
- C1 + C2 + C3 together: node-types.json identical, four corpora 0 differ, fixtures the same single C2 recovery
  difference.

### C4. Share the case-branch tail

`seq($._case_body_branch, optional(seq(repeat(caseEmptyGroup($)), ';')))` appears in `case_branch`,
`preproc_split_case_branch` and `preproc_split_case_extended`. Make it a hidden `_case_branch_tail`.

- Alone: −141 / −12. node-types.json: identical. Four corpora: 0 differ. Fixtures: 0 differ.
- The generator asks for a self-conflict, `[_case_branch_tail]`. That is a GLR fork that can open at every case
  branch, which is common code. It lands only if the fork probes (G11) and the speed rule (section 7, both
  corpora) pass **(controller's call)**.
- Not measured on top of C1-C3. The two touch different rules, so it should be roughly additive, giving about
  26,830 (*estimate*).

### C5. Share the case head, and the case head with its body (low rank)

- `_case_head = seq(case_keyword, _region_root_expression, of_keyword)`, shared by `case_statement` and
  `preproc_split_case_statement_end`: −19 / −10, no conflict. Not worth a commit on its own.
- `_case_head_body`, the same plus `optional(field('body', case_body))`: −185 / −90, but with a self-conflict
  `[_case_head_body]` that forks at the end of every case body. Its parity was not checked. It ranks last, and it
  is tried only if the batch ends above 27,400, as one of the two extra candidates of section 10
  **(controller's call)**.

### Candidates that would change trees, out of scope

`option_member` costs 1,245 / 1,314. That cost is the ambiguity between an option-member list and an expression in
a generic property value: `Access = Internal;` is an `option_member_list`. Narrowing it changes trees, so it is
outside D1.

## 5. Constraints and gates

**The D1 exit criteria, verbatim from the roadmap** (`docs/superpowers/plans/2026-09-28-roadmap-remaining-work.md`,
row D1):

> Preservation across all four corpora: complete cursor-derived trees including anonymous tokens, fields and
> spans; `has_error`; full oracle results; and fresh-parse against incremental-parse equivalence.
> `node-types.json` is byte-identical. There is no material parse-speed or incremental regression, **decided with
> `python -m tools.perf ab`** (before and after libraries in one session, pinned, interleaved ABBA, trees checked
> identical; ratio with a confidence interval) on the same compiler and flags; the A5 baselines are context, since
> separate sessions on this machine drifted ~30%. `ab`'s measured resolution is about 5% at 8 rounds on DC (~2%
> only sometimes, 1% and under not at all), and its CI is within-run: a decision about a difference under 5% needs
> >= 24 rounds, or two independent `ab` runs that agree. Fewer states alone is not success.

**Gates.** Each candidate is a separate commit **(controller's call)**. Every candidate passes G1-G4, G7, the
G9 per-commit part, G11 if it adds a conflict, and G12 (speed) against its predecessor. The final batch passes
every gate against `960ed31`. "Before" means the predecessor's library for a candidate and the `960ed31` library
for the batch. Each is built fresh and copied aside before the next edit (method doc section 4).

**Where the corpus-label commands run** **(controller's call)**. G8 and every `tools.perf` command run in the D1
checkout itself, `/work/tsal-wt/main`. Its `BC.History` and `DC` symlinks, and the gitignored `H:` symlink tree,
satisfy the oracle's and `tools.perf`'s corpus root resolution; B7b-2's Task 12 ran the full tier there. The
method doc's main-worktree caveat (section 4) describes the Windows layout and does not apply on this Linux host.
Never switch `/work/tsal`, which other sessions share. The "before" oracle run uses a build of main `960ed31`,
made in a scratch `git worktree add` or taken from a saved library, against the same corpora.

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

`tools.perf ab`, `delta` and `incremental` take the lock themselves or load a given library. Never wrap them
in `ts-lock.sh` (wrapping `ab` deadlocked in B7b-2). `strict_lists_scaling.py` does not take the lock and ran
wrapped throughout B7b-2, so wrap it.

## 6. Target

**STATE ≤ 27,300 and LARGE ≤ 9,700. `parser.c` is reported but has no target of its own** **(controller's call)**.

Why that number: it leaves 1,470 STATE under the 28,770 ceiling and 1,023 LARGE under 10,723. The follow-ups are
budgeted at about 665 STATE (section 1). That leaves about 2.2x margin, which covers the two items whose design
is still open (61 and 51 shape 3), whose budgets are guesses. C1 alone (27,511) does not reach the target.
C1 + C2 + C3 (26,968 / 9,389) does, with 332 STATE to spare. If C2 fails G11 or G12, then C1 + C3 + C4 is the
fallback (*estimate*: about 27,320, short by about 20).

**Stop at the target** **(controller's call)**. The builder stops once the target is reached and does not search
for more. A batch that ends above 27,300 but at or below 27,400 is accepted, and the shortfall is reported. That
still leaves at least 1,370 STATE against the roughly 665 the follow-ups need. Only a batch above 27,400 allows a
further search, under the rules in section 10.

The ceilings themselves do not move. D1 makes room under them and does not ask for more. They remain strong
preferences, not hard limits (USER DECISION, section 1). If a later correctness fix needs more than the room D1
made, correctness wins: the fix lands, the crossing is reported with its measured cost, and no tree is left wrong
to stay under a ceiling.

## 7. Speed: how DC and BC.History are measured

Speed is a gate, not a goal (USER DECISION, section 2). No candidate may regress.

- **Same session, same compiler and flags.** BEFORE is the predecessor's library: `960ed31` for C1, and the
  previous candidate's for each later one. AFTER is the candidate's. Both are built by the same
  `tree-sitter build` path that `ab` loads (clang on this Linux host; the clang-cl default on Windows).
- **The rule, the same for both corpora** **(controller's call)**. Each candidate gets two 24-round `ab` runs per
  corpus, bc-history and dc:
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
  before reading a ratio below 1.00 as a regression (item 52, "The gate is noisy under host load").
- **Scratch indication only, not a decision.** These figures come from 6 interleaved passes over all 1,352 DC
  files, with gcc -O2, no pinning and load around 1. Each is the median time of the base over the median time of
  the candidate: C1 1.035, C1 + C2 1.008. The size reduction does not slow the parser here.
  `ab` decides.

## 8. Is `parser.c` this big because the grammar is structured wrong?

This section answers the user's question with measurements. The method is the family removal of section 3.3,
applied to whole layers of `#if` handling. Every row also removes whatever only that layer reaches. The
B7b-2 rows remove only the group nodes: the B7b-2 refactoring of the expression core (`_continuation_operand`,
`_postfix_operand`, `_assign_target`, the `_region_root*` rules) stays. The generator asked for no added
conflicts in any row.

### 8.1 Layer by layer

| layer removed | STATE | LARGE | SYMBOL | `parser.c` |
|---|---|---|---|---|
| nothing (`960ed31`) | 28,742 | 10,562 | 1,325 | 68,647,284 B (65.5 MiB) |
| **separately** | | | | |
| B7b-2 expression groups (tail, operand group, prefix, receiver, typed group) | 24,646 (−4,096) | 7,896 | 1,295 | 55,031,097 B (52.5 MiB) |
| B7b-1 strict conditional lists (9 families) | 28,178 (−564) | 10,483 | 1,278 | 67,618,235 B (64.5 MiB) |
| B11 property value runs (`valueRunRules`/`afterGroupRules`/`afterSequenceRules`) | 22,931 (−5,811) | 9,753 | 1,191 | 59,463,653 B (56.7 MiB) |
| `preproc_split_*` and `preproc_fragmented_else_tail` (36 rules) | 19,089 (−9,653) | 5,376 | 1,246 | 37,961,387 B (36.2 MiB) |
| **cumulatively** | | | | |
| B7b-2 + B7b-1 | 24,093 | 7,820 | 1,248 | 54,028,232 B (51.5 MiB) |
| + B11 | 18,105 | 7,014 | 1,114 | 44,703,826 B (42.6 MiB) |
| + splits | 9,949 | 2,981 | 1,035 | 20,210,034 B (19.3 MiB) |
| **all `#if` handling except the extras** (`preproc_if`/`elif`/`else`/`endif` made empty; the extras `#region`, `#pragma`, `#define`, `#undef` stay) | **3,517** | **967** | 879 | **6,875,231 B (6.6 MiB)** |

**Is the reduced grammar still AL?** The last row was built and compared with the full grammar on the 1,308 DC
files that contain no `#if`. Both give identical trees on all 1,308: node types, spans, `has_error` and anonymous
tokens. The parser built from that row parsed those files about **1.12x** as fast (best of 3, gcc -O2, a loaded
host: an indication, not an `ab` result). So the grammar without `#if` is complete AL, and about 88% of the
current states model `#if` structurally. That `#if` handling also costs files that never use `#if` roughly 10%
of their parse time.

### 8.2 Other public tree-sitter grammars

These are the `parser.c` headers on each repository's default (or generated-files) branch, fetched 2026-10-22.
The size is the HTTP content-length. Treat every row as approximate: the versions are not pinned, and
LANGUAGE_VERSION 14 and 15 lay out tables differently.

| grammar | STATE | LARGE | SYMBOL | `parser.c` |
|---|---|---|---|---|
| tree-sitter-c | 2,015 | 455 | 360 | 3.7 MiB |
| **AL without `#if`** (8.1) | **3,517** | **967** | **879** | **6.6 MiB** |
| tree-sitter-rust | 3,825 | 1,064 | 351 | 6.2 MiB |
| tree-sitter-typescript | 5,870 | 1,193 | 376 | 8.3 MiB |
| tree-sitter-c-sharp | 8,495 | 4,475 | 542 | 30.5 MiB |
| fwcd/tree-sitter-kotlin | 10,180 | 6,938 | 374 | 32.2 MiB |
| tree-sitter-grammars/tree-sitter-kotlin | 11,432 | 4,175 | 289 | 21.4 MiB |
| alex-pinkus/tree-sitter-swift | 11,522 | 2,332 | 574 | 22.1 MiB |
| tree-sitter-cpp | 11,734 | 3,826 | 570 | 24.7 MiB |
| tree-sitter-haskell | 12,862 | 2,378 | 537 | 18.9 MiB |
| tree-sitter-verilog | 20,534 | 6,920 | 1,202 | 44.2 MiB |
| gmlarumbe/tree-sitter-systemverilog | 21,567 | 7,829 | 1,356 | 62.1 MiB |
| **AL now** | **28,742** | **10,562** | **1,325** | **65.5 MiB** |
| DerekStride/tree-sitter-sql | 31,142 | 5,496 | 792 | 41.0 MiB |

Without its `#if` modelling, AL sits between C and Rust. With it, AL is the size of SystemVerilog and SQL, the
largest public grammars listed. *From memory, unverified:* the C and C++ grammars model `#if` structurally only
at a few positions: top level, field lists, enumerators and statement lists. Directives inside expressions or
inside a split construct give an ERROR or a flattened tree there. tree-sitter-c-sharp treats most directives as
extras. No grammar listed models `#if` in expressions, split headers or split statement heads the way this one
does.

### 8.3 The architectural alternative: directives as extras, structure rebuilt after parsing

The alternative makes `#if`/`#elif`/`#else`/`#endif` extras, like `#region` today. One tree is parsed per source,
and per-configuration structure comes from a separate step: a configured parse (roadmap F1b, P2), or a merge of
several configured trees (B12).

- **What it would save:** up to the last row of 8.1, about 25,200 STATE (−88%) and about 59 MiB of `parser.c`.
  Parsing would get faster, by roughly 10% on `#if`-free files and probably more on files that use `#if` (no
  split-construct GLR forks). The size is an upper bound. Rebuilding the structure costs code elsewhere, not
  states.
- **What it would cost, measured against the project's goal of correct, queryable trees for every
  configuration:**
  - With directives as extras, the native tree interleaves the arms. Every split construct (two headers, a
    `begin` in one arm and its `end` in another, an operand group) becomes either one wrong tree or an ERROR.
    The single native tree would no longer be correct for any configuration in which arms differ. Queries over
    it would see code from every arm at once.
  - Correct trees would exist only per configuration: N parses for N configurations, and a merge step that does
    not exist yet. The B7a matrix, the config oracle's lowering and the expression-region contract
    (`docs/expression-regions.md`) would all have to be rebuilt around configured trees.
  - Incremental parsing of the native tree stays cheap, but each configured tree has to be re-derived after an
    edit.

**Decision: considered and rejected. USER DECISION** (2026-10-22, relayed by the coordinator). The
user's words: "as alsem needs the correct picture and not just an okay one, I think we are on the correct track".
alsem, the downstream consumer, needs exact per-configuration trees from the one native tree. D1 therefore
reduces states **within** the structural design. The layer table stays here as information. It also shows where
D1's pool is: the split families, which section 4's candidates come from.

**Answer to the question.** The grammar is not structured wrongly. It is the size it is because it models `#if`
in more places than any public grammar listed, and that is the user's chosen design. Inside that design there is
duplication that factoring can remove: C1-C3 remove 1,774 STATE (6.2%) and 6.9 MiB with identical trees.
Measured removal costs (3.3) suggest more of the same kind in the split-if and split-case families
**(controller's call: the reading of the data)**.

## 9. How this was measured, and what it does not prove

- **Stubs** (`stub.sh`): one rule's body becomes a dummy token, and that rule is dropped from every conflict set,
  in `src/grammar.json`. Then `tree-sitter generate grammar.json` runs under `ts-lock.sh`.
- **Layer removal** (`prune.py`): emptiness propagates as described in 3.3, conflicts the generator demands are
  added automatically (up to 40 rounds), and the counts are approximate by that much. Applying it with no
  pattern regenerates exactly 28,742 / 10,562 / 1,325 / 68,647,284 B, so the round trip is faithful.
- **Candidates** (`exp.sh` with `e_*.py`): a Python edit of a scratch `grammar.js`, then generate. When the
  generator demanded conflicts, they were added to the generated `grammar.json` by the same loop. So the builder
  must write those conflicts into `grammar.js` by hand, and may find that some old sets become unnecessary.
- **Parity** (`parity.py`, `fixtures.py`): py-tree-sitter walks every node with a cursor, scratch libraries are
  built with gcc -O2, and the comparison covers type, field, span, `has_error` and `is_missing`. This is a
  pre-check. It is **not** gates G5-G13: `delta`, `has_error`, the oracle, B7a, incremental, the fork probes and
  `ab` were not run. The `tree-sitter test` suite was not run either, because it would rebuild the shared library.
- The other grammars' figures are not pinned to a commit (8.2).

## 10. What is left to the builder

- Apply C1, then C2, then C3, one commit each. Write the demanded conflicts into `grammar.js`, remove the sets
  the generator reports as unnecessary, and keep the existing rule comments next to the new hidden rules. Put the
  counts in each commit message, as CLAUDE.md asks.
- For each candidate commit, run the per-candidate gates of section 5:
  - G1-G4 and G7;
  - G9's `assert --refresh` and `census --check`;
  - G11 if the candidate adds a conflict (C1 and C2 do);
  - G12's two `ab` runs per corpus against its predecessor.

  Say in the commit message that the B7a evidence hashes are not yet refreshed.
- Record C2's recovery-tree change in `b7_gap_split_if_begin_test.txt` as the USER DECISION exception (G7). Check
  that the case still fails as an `:error` and that `tools/config_oracle/fixture-classes.tsv` needs no change.
- On the final batch, at the gate commit, run G5, G6, G8, the full G9 `run` plus `report`, G10, G12 against
  `960ed31`, and G13.
- **Stop or search** **(controller's call)**. This settles section 6 and this section:
  - At or below 27,300 STATE (and 9,700 LARGE): stop. Do not look for more.
  - Above 27,300 but at or below 27,400: stop, accept the batch and report the shortfall. This is the expected
    end if C2 fails and the C1 + C3 + C4 fallback (about 27,320) is taken.
  - Above 27,400: the builder may try **at most two** more candidates, taken from the split-if family (3,687) and
    the split-case family (3,144), and from nowhere else. The pattern is the same: a long prefix or tail that ends
    at a hard keyword (`then`, `end`, `#endif`), spelled out in two or more rules. C4 and C5 count toward the two.
    Each one passes the same per-candidate gates. There is no open-ended search, no reach into the expression
    core (3.2) and no family merging (3.3). If the batch still ends above 27,400, stop and report.
- Update `docs/state-reduction-method.md`: add a pass-5 row, put C1-C3 in section 2, and put the rejected
  attempts in section 3: the further if-open head (−20, with `if_statement` conflicts), family merging, and C5's
  self-conflict if it is dropped. Update the CLAUDE.md metrics table from a re-measure, not from this document.
- After D1 lands, the follow-ups (items 62, 61, then 51 shape 3 and 58) each measure their real cost against
  the D1 result and record it in `docs/deferred-work.md`.

## Execution amendments

1. **G9's census note does not cover a boundary that moves into a new hidden rule** (measured 2026-10-22 by
   running `census.census()` over the scratch grammars, confirmed by `census --check` on C1). A slot that moves
   inside the same rule keeps its hosts, as section 5 says. A boundary that moves into a new hidden rule changes
   its hosts: `routes()` climbs from the hidden rule to its visible callers, which are the rules it was factored
   out of. C1 moved these keys:
   - `occ:preproc_split_if_then_begin_else_shared:0.15.0.0` → `occ:preproc_split_if_then_begin_else_shared:0.4.0.0`
     (same rule, same 25 hosts);
   - `bnd:preproc_split_if_begin_else:condition:{start,end}` and
     `bnd:preproc_split_if_then_begin_else_shared:condition:{start,end}` (25 statement hosts each) →
     `bnd:_split_if_begin_else_head:condition:{start,end}`, whose hosts are `preproc_split_if_begin_else` and
     `preproc_split_if_then_begin_else_shared`.

   `registry._alias_problem` refused the second kind ("covers hosts ... that X never covered"). It now also
   accepts a live host that is the rule named by the retired key of any alias to the same live key, i.e. the
   rule the slot was factored out of (`fix(b7-audit)` commit, tests `test_alias_live_host_may_be_the_factored_rule`
   and the guard `test_alias_live_host_outside_factored_rules_fails`). Each retired row gets one live `equiv`
   row; for the two `bnd` retired keys of one live key, each live row covers the host its retired key was
   factored out of, since two rows over the same (key, host) are a duplicate cover. Frozen cell ids stay
   unchanged. C4 (`occ:_case_branch_tail:1.0.1`) and C5 (`bnd:_case_head_body:expression:*`) would rely on the
   same rule.
2. **C4 is reached only through the stop rule** (section 10), not only after a G11/G12 failure of C2. C1 + C2 +
   C3 measure 26,968, below the target, so the batch stops after C3. C4 (and C5) run only when the batch after
   C3 ends above 27,400, for example when C2 fails and C1 + C3 (an *estimate*, about 27,458) is measured above
   it.
3. **C1 changes recovery trees, and the USER DECISION recovery exception (section 2) is extended to it**
   (controller ruling, 2026-10-22). The spec measured no tree change for C1, and none exists on the four corpora
   or the 3,571 corpus fixtures (G4, G7: 0). Two instruments outside those found recovery-tree changes. Every
   affected input already ERRORs at `960ed31` and still ERRORs under C1. On the B7a cells C1's tree holds less
   ERROR (byte coverage, all 94 measured); on the truncated inputs it recovers equal or more structure.
   - **B7a cells** (`b7_audit run --check`: 872 changed records at C1, 0 at `960ed31`): 94 alc-accepted gap
     cells. By key:
     - `occ:preproc_split_if_then_begin_else_shared:0.15.0.0`: 45
     - `occ:preproc_split_if_then_begin:0.5.0.0`: 40
     - `occ:_preproc_end_guard:3.0`: 3
     - `occ:_else_begin_block:4.0`: 3
     - `bnd:assignment_statement:right:end`: 2
     - `occ:preproc_split_call_statement:0.7`: 1

     The fields that change are `error_in_hole` (True to False, 252 records) and the oracle's
     `directive|unmatched-source|*` reasons (620 records); the status stays `cannot-validate`.
   - **Truncated inputs** (Review Focus 5, `mutate_parity` class `truncate`): 22 prefixes, cut before the closing
     `}`, of `preproc_split_block_over_endif_test.txt` (8), `preproc_split_if_begin_else.txt` (6) and
     `preproc_split_if_then_begin_else_shared.txt` (8). 16 of them differ only in the root (`ERROR` becomes
     `source_file(ERROR)`, whose ERROR covers one byte less over an identical inner tree), 4 have small
     differences inside the ERROR as well, and 2 recover the split construct. None recovers less structure.

   Reason: the user's own, for C2. An error-recovery tree on input the parser already gets wrong is not a
   correctness change: no correct tree exists before or after.

   Condition: no B7a matrix verdict may move. Checked: every cell's verdict, defect kind, family, shapes and
   class are identical at `960ed31` and at C1 (24,355 cells, 11,862 defective, 592 groups; all 94 cells GAP
   before and after). The rendered matrix differs only in its parser hash and in the new `equiv` live rows
   listed as no-evidence.
4. **C2's recovery-tree changes, recorded under the USER DECISION 2026-10-22 (recovery)**: recovery trees of
   input that already ERRORs may change in every D1 reduction, provided no B7a verdict moves and every valid
   tree is identical. Valid trees: G4 15,358 identical, G7 3,571 cases with exactly the planned difference.
   - **Corpus fixture** (section 2, the planned exception): `b7_gap_split_if_begin_test.txt` "B7a GAP:
     split-if-begin / first-replace". Still `:error`, listed in `tools/deliberate-negatives.txt`, and visible
     to `has_error_sweep` (595 negative-visible, 0 hidden-only, as at `960ed31` and C1). CLI 0.27: C1 reads the
     arms as `preproc_split_if_then_begin` with a 3-byte ERROR over the first `end`; C2 reads
     `preproc_split_if_begin_asymmetric` with an ERROR over `#if X end #else` and a
     `preproc_split_block_close_after_endif` after it. Both keep the zero-width MISSING `end` at the close.
   - **B7a cells** (scratch evidence C1 vs C2): 153 alc-accepted gap cells, 1,180 records. By key:
     - `occ:preproc_split_if_then_begin:0.5.0.0`: 123 (102 hold less ERROR, 21 more)
     - `occ:preproc_split_if_begin_asymmetric:0.3.0`: 30 (3 less, 27 more)

     Of the 48 that hold more ERROR, 45 grow by 2-33 bytes (the ERROR moves from the `end` token to a span over
     `#if X end #else`/`#endif`, the fixture exception's shape). **The other 3 grow by 441 / 479 / 603 bytes:
     C2 turns the codeunit's whole `declaration_body` into one ERROR and the `procedure` node is lost**, where
     `960ed31` and C1 had 3-12 local ERRORs inside a `procedure` node. They are
     `occ:preproc_split_if_then_begin:0.5.0.0@preproc_conditional_statement#nested+not`,
     `occ:preproc_split_if_then_begin:0.5.0.0@preproc_split_block_end_in_else#empty+not` and
     `occ:preproc_split_if_then_begin:0.5.0.0@preproc_split_if_else_statement#empty+not`, all alc ACCEPT and
     GAP before and after. USER DECISION 2026-10-22 (C2): "Keep C2, record the 3".

     All 153 have `has_error` True under both. Only the oracle's reasons change: C2 adds
     `directive|unmatched-source|*` items, and the status stays `cannot-validate`. Twelve class assertion rows of
     `terminator/split-if-begin` flipped on `assert --refresh`: `first-replace` (+comments, +not) true →
     mixed:45/59; `empty` (+comments, +not) mixed:52/59 → 33/59; `adjacent-compl+not`, `elif+not`, `nested`,
     `nested+comments`, `sep-only+not`, `trail+not` mixed:25/31 → 4/31, the value their sibling variants
     already had. They were edited by hand to C2's truth and fingerprints. A GAP cell's verdict does not read its
     assertion (`judge._accepted` returns GAP on `parser_has_error` first).
   - **Mutation pairs** (`mutate_parity` c1 vs c2, `--base` a base-vs-base run for C2's five types): 20 new
     error-before pairs, all ERROR under both. 19 are mutations of the exception fixture itself (extras, crlf,
     case and truncate-35..50). The extras, crlf and case variants hold a larger ERROR, as the fixture does
     (outermost ERROR 33 → 79 / 47 / 45 bytes). 14 of the truncated ones keep the same outermost ERROR span, and two
     (truncate-47, -50) go from a whole-file ERROR to a recovered codeunit. One is
     `preproc_block_over_conditional_test.txt` "Shape C" truncate-10, a whole-file ERROR under both.

   Condition checked: all 24,355 cell verdicts dumped at C1 and at C2 from scratch evidence (shown verdict,
   kind, family, shapes, class, note) diff to 0 lines (11,862 defective, 592 groups both).

   Speed record: the two bc-history `ab` runs for C2 (0.999 / 0.999) ran under host load 87 → 61 → 1.2, not on
   a quiet host. They are ABBA and well above 0.97, so they were accepted; the dc tie-break run was quiet (1.06).
5. **There is no CLAUDE.md metrics table to update** (section 10; pre-flight ruling R1). The user removed the table in
   `9f5a439`, and `./tools/metrics.sh` is the source. The re-measured metrics are in the D1 entry of `CHANGELOG.md`
   instead.
