# Reducing parser states: the method

This is the method for roadmap item D1, the state-reduction pass over the split and
whole-value rules added since 4.0.0
(`docs/superpowers/plans/2026-09-28-roadmap-remaining-work.md`). It collects what four
earlier passes and the BC 29 grammar work measured: what to measure, which factorings cut
states, which did not and why, and the gates a reduction must pass before it merges.

At `d34e04c`, `src/parser.c` has `STATE_COUNT 15870`, `SYMBOL_COUNT 1026` and is
39,556,063 bytes (37.7 MiB). The last reduction pass ended at 14,875 states (`97ee3f2`).

**Provenance.** Each claim cites a commit, a file in this repo, or the CHANGELOG. A claim
marked *(from the 4.0.0 session notes, unverified)* comes from private session notes and
has no other record in the repo. Treat it as a lead to re-measure, not as a fact.

## 1. What to measure

**The counts.** Read them from the generated parser, never from memory:

```bash
grep -E '#define (STATE_COUNT|LARGE_STATE_COUNT|SYMBOL_COUNT)' src/parser.c
wc -c < src/parser.c          # bytes; quote MiB and bytes together (CLAUDE.md)
```

**Which rules cost the most: stub them, do not read the report.**
`tree-sitter generate --report-states-for-rule -` prints a state count for every rule. Those
counts overlap: a state shared by several rules is counted under each of them. So the
report ranks rules badly, and its numbers do not add up to `STATE_COUNT`. Pass 4 ranked its
targets by **marginal cost** instead (`97ee3f2`: "ranked by MARGINAL cost (stub one rule
body, regenerate), not by --report-states-for-rule, whose per-rule counts overlap and rank
badly"):

1. Replace one rule's body with a dummy token, for example `R: $ => 'zzz_R'`.
2. Run `./tools/ts-lock.sh tree-sitter generate` and read `STATE_COUNT`.
3. The drop from the real count is what that rule costs. Restore the rule.

A stubbed rule can leave other rules unreachable, or remove a conflict the generator needs.
Either one shows up as a generate error, or as a drop that is too large to believe. Use the
report only to choose which rules to stub first.

*(From the 4.0.0 session notes, unverified:)* one stub-and-generate cycle took about 3 s. In
pass 4, the five most expensive rules by marginal cost were `case_statement_end` (1,017),
`split_procedure` (621), `option_members` (591), `if_else_statement` (571) and
`else_begin_over_endif` (253), which is not the report's order. Re-measure these before
using them: the grammar has gained about 1,000 states since then.

**Cost of a new arm.** The same stub measures a candidate rule or arm before it lands. The
BC 29 work did this for each `#if` family, and the results are below.

## 2. What worked: complete units shared as hidden rules

A hidden (`_`-prefixed) rule that two or more rules reference is built once, so its LR
states are shared. This works when the unit is **complete**, which means it ends at a hard
terminator such as `)`, `]`, `end`, `#endif` or a complete `code_block`. The parser then
reduces it with no lookahead question that depends on which rule it is in.

| Pass | Commits | STATE_COUNT | `parser.c` | Evidence |
|---|---|---|---|---|
| 1 | `200b1e6` | 18,290 → 15,525 (−15.1%) | 38.89 → 33.31 MiB | worklist plan |
| 2 | `200b1e6` → `18785e1` | 15,525 → 11,872 (−23.5%) | → 26.28 MiB | worklist plan |
| 3 | after `784bcef` | 11,872 → 10,825 (−8.8%) | → 23.82 MiB | worklist plan; every row tree-identical over BC.History |
| 4 | `97ee3f2` | 15,321 → 14,875 (−2.9%) | 36.45 → 35.46 MB (units as the commit gives them) | commit message; `node-types.json` byte-identical, BC.History trees byte-identical |

The worklist plan is `docs/superpowers/plans/2026-05-14-state-count-reduction-worklist.md`,
which has every step and its numbers. Passes 1 to 3 together went from 18,290 to 10,825 states
(−40.8%), and `parser.c` from 38.89 to 23.82 MiB (−38.7%). The grammar then grew again
through 4.0.0, which is why pass 4 starts higher.

Units that worked. Every one of them is still in `grammar.js`:

- Preprocessor bodies: `_preproc_branch_body` (`[var] begin stmts end [;]`, pass 1),
  `_else_begin_block`, `_preproc_split_then_begin_open` (it ends at `#endif`), and
  `_preproc_end_guard`.
- Routines: `_procedure_name_and_params` (it ends at `)`), `_routine_regular_body` (it ends
  in a `code_block`), and from pass 4 `_procedure_head` (−21), shared by `procedure`,
  `interface_procedure` and `_procedure_header`, and `_procedure_regular_tail` (−104).
  `_procedure_regular_tail` inherits `procedure`'s ambiguity with `interface_procedure`,
  so every existing `[$.procedure, ...]` conflict needs a counterpart for it. The generator
  requires each of them.
- Expressions and branches: `_expression_list` (bounded by the caller's `)` or `]`),
  `_then_branch` and `_else_branch`.
- Pass 4: `_option_members_branch` (−251) and `_preproc_if_then_else_head` (−78), which is
  `if C then X else` and ends at the hard `else`. In the first of these, one branch was
  spelled three times. Identical `repeat()` calls are deduplicated by the generator, but a
  triplicated `repeat(seq(x, ','))` followed by `optional(x)` is not.
- Removing conflicts that the generator reports as unnecessary (pass 1 removed three).
- The `inline:` array, but only for trivial pass-through wrappers. `_field_source`
  (`$ => $._expression`) is inlined today (pass 2, item 10).

**Sharing also fixes conflicts.** Two nonterminals that read the same long prefix each get a
copy of the automaton for that prefix, and may meet in a reduce/reduce conflict. In the
BC 29 work, `key_declaration` and both modify rules came to share hidden `_key_header` and
`_modify_header` units with their split counterparts. That removed a reduce/reduce conflict
and saved 107 states (`42aaf7b`).

## 3. What failed, and why

Each entry names the edit that was tried, because the result belongs to that edit (§5).

- **Partial-prefix extraction into the `preproc_split_*` rules** (`_preproc_if_header` and
  `_preproc_var_begin`; also a full `_procedure_signature` that included the return clause,
  *from the 4.0.0 session notes, unverified*: the worklist plan names only the first two). This
  gave an unresolved conflict at generate. A hidden rule that ends in the middle of a
  construct, and that several sibling rules can reach, forces a reduce before the parser can
  know which sibling it is in. The fix is to extract a smaller piece that ends at a hard
  terminator (worklist plan, "Hard lesson from first pass").
- **One body shared by rules with different associativity.** `assignment_statement` and
  `assignment_expression` look identical, but `assignment_expression` is `prec.right`. A
  shared `_assignment_body` cannot carry associativity for each parent, and moving
  `prec.right` outside the shared `seq` gave an unresolved conflict on chained assignment.
  Reverted (worklist #8).
- **The `inline:` array to rescue partial prefixes.** Inlined rules are substituted before
  the automaton is built, so they did get around the conflict. But STATE_COUNT grew by 56,
  because inlining copies the rule into every call site. Reverted (worklist #5).
- **`token(choice('and', 'AND', 'And'))` for operators.** This cut 210 states but broke
  `queries/highlights.scm`, which matches operator literals such as `"and"` as node types.
  That is a behaviour change. Reverted (worklist #7).
- **A precedence cascade for expressions.** A 13-tier hidden-rule cascade replaced the flat
  `prec.left(N)` expression grammar, which is about 4,878 states (roughly 45% of the parser at
  the time). STATE_COUNT went **up** by 64 (10,825 → 10,889), and a corpus case
  (`arr[idx] in [...]` as a case pattern) became an ERROR. `_single_pattern`, `filter_value`
  and `calc_field_reference` overlap the cascade tiers, and each needs many exact two-way
  conflict declarations. *(From the 4.0.0 session notes, unverified: a three-way conflict
  `[A, B, C]` does not cover its two-way subsets. The worklist plan says only that the
  declarations had to be exact two-way ones.)* The conflicts cost more than the cascade saved. (Worklist plan, "P3-X".)
- **One `_if_head` shared by `if_statement` and every split rule.** STATE_COUNT went up by
  125 to 193. Narrowing the then-branch of the split if-else saved only 3 (`97ee3f2`).
- **`prec(25)` on a new split rule.** It silently resolved a shift/reduce conflict against an
  existing reading. A bodiless key before `#else` is also a complete `key_declaration`, so
  every plain `#if key(..) #else key(..) #endif` broke. `preproc_split_key` now has no prec
  and a declared conflict, and a fixture pins the plain form (`42aaf7b`).
- **Wide arms for crossing constructs.** A recursive `begin stmts* <prefix>` arm for
  `preproc_split_open_statement` cost +2,540 states and parsed no extra file. A narrow arm
  replaced it (`07758c6`; `docs/deferred-work.md` item 10). The narrow arm's own cost, 12
  states, comes from the 4.0.0 session notes and is unverified. A split `add*` layout-open
  rule cost +835 states in its cheapest form, so it was deferred (`docs/deferred-work.md`
  item 10, with the full table).

*(From the 4.0.0 session notes, unverified:)*

- When the tail was shared with the split bodies too, the saving was 322 states rather than
  104. It was held back because it widened `preproc_split_procedure` and changed
  `node-types.json` (its `body` field stopped being required). That is the user's decision.
- Much of the remaining cost is LR(1) follow-set cloning. For example, a statement followed by
  `else` inside a `#else` branch clones the expression and statement states, about 480 of
  them for the split if-else `#elif`/`#else` heads. Factoring does not remove that.
- A new rule that makes `end` a valid lookahead after statements split every nested
  statement state (+373). Sharing the repeat symbol did not help.
- On Windows, `tree-sitter generate` can fail with "user-mapped section open (os error 1224)"
  on `src/parser.c`. It is a transient lock: retry after a pause.

## 4. Preservation gates for D1

Fewer states alone is not success. Each reduction must pass all of these on the
**four corpora**: BC.History, DC, BC28.1 (`AL_BC28_ROOT`) and BCApps 29.0
(`AL_BCAPPS29_ROOT`). They are listed in roadmap row D1, and the corpus labels are those in
`tools/config_oracle/__main__.CORPORA`. Take every "before" measurement fresh, from the
commit just before the change.

**Worktree caveat.** `CORPORA` resolves `bc-history` and `dc` under the repo root
(`REPO / "BC.History"`, `REPO / "DC"`), and so do the `./BC.History` / `./DC` paths in the
commands below. Both corpora live only in the main worktree, so in a git worktree those
labels point at directories that do not exist. Do not symlink them in. The oracle and
`tools.perf` key every root by these labels: the oracle refuses a root that matches no
label (exit 2, "unlabelled"), so passing the main worktree's absolute `BC.History` path
from a worktree does not work. Run those two from the main worktree. The path-based
gates (`tree-harness.sh`, `has_error_sweep.py --root`) take the main worktree's absolute
paths fine. `bc28.1` and `bcapps-29.0` are absolute (`AL_BC28_ROOT`, `AL_BCAPPS29_ROOT`)
and work anywhere. All worktrees also share
one compiled `al.dll`, so wrap every build and every `tree-sitter` command in
`./tools/ts-lock.sh`.

| Gate | How |
|---|---|
| Trees byte-identical | `./tools/tree-harness.sh snapshot <ROOT> .snapshots/baseline-<change>` before the change, then `verify` after it, for each corpus. The harness compares `tree-sitter parse` output, which has named nodes, fields and spans but **no anonymous tokens**. D1 asks for complete cursor-derived trees, including anonymous tokens, so this gate is not enough alone. |
| Complete trees, anonymous tokens included | `python -m tools.perf ab --lib-a BEFORE.dll --lib-b AFTER.dll --corpus bc-history --corpus dc --corpus bc28.1 --corpus bcapps-29.0`. Before it times anything, `ab` parses every file with both libraries and compares the complete cursor-derived trees: every node, named and anonymous, with type, grammar symbol, field, spans and `has_error`. It exits 1 on any difference (`tools/perf/ab.py`). Copy `al.dll` to `BEFORE.dll` before the change. |
| `has_error` | `python tools/has_error_sweep.py --root <ROOT>` for each corpus, and `--corpus-fixtures`. This is the only gate that sees a MISSING hidden token. |
| Full oracle | `./tools/ts-lock.sh python -m tools.config_oracle run --tier full --root ./BC.History --root ./DC --root H:/Git/BC28.1 --root H:/Git/BCApps-29.0`. Exit 0, and the same result as before the change. |
| Fresh against incremental | `python -m tools.perf incremental`. It exits 1 on any mismatch between `parse(new, old)` and `parse(new)`. |
| `node-types.json` byte-identical | `git diff --exit-code src/node-types.json` after `generate`. A change here is a tree-shape change for every consumer, whatever the corpora say. |
| Speed | `python -m tools.perf ab`, the same command as above, before and after in one session. Do not compare against the A5 baselines, because separate sessions on this machine drifted by about 30%. At 8 rounds on DC, `ab` resolves a difference of about 5%, about 2% only sometimes, and 1% or less not at all. A decision about a difference under 5% needs at least 24 rounds (`--rounds 24`), or two independent `ab` runs that agree (`docs/performance-baselines.md`, "Resolution of `ab`"). Same compiler and flags on both sides. |
| The usual gates | `./tools/ts-lock.sh ./validate-grammar.sh`, and `tree-sitter test` with an unchanged case count. |

The loop for each change: stub to measure (§1), make the change,
`./tools/ts-lock.sh tree-sitter generate` (this catches conflicts in seconds), then
`tree-sitter test`, then the tree-harness `verify`, which is the cheapest corpus gate. Run
the rest of the table once for the batch, and again for any change that alters a tree.

## 5. A failed attempt measures one edit, not the grammar

From CLAUDE.md: "I tried it and it forced N conflicts" measures one edit, not the grammar.
Adding `code_block` to `_statement_inner` was recorded as forcing a conflict per host and a
GLR fork on every `begin`. It did, until the seven host arms that already carried their own
`field(X, $.code_block)` were deleted as well, because they were giving each host a second
derivation of the same string. With them gone there were zero conflicts and a smaller
parser. The limitation came from the attempt, and it went unchallenged for a release.

So every result in §3 is written as the edit that was tried, with its number. "The
expression cascade went up by 64" is a result about one 13-tier design whose tiers
overlapped three value rules. It is not a proof that no factoring of expressions can help.
Before you retry something listed in §3, say how your edit differs from the recorded one,
for example by removing the duplicate derivation first. If you abandon a new attempt,
record the edit, the number and the reason in the commit message or the worklist, so the
next person can tell it apart from a limit of the grammar.
