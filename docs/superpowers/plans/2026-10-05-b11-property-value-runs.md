# B11 property values made of a run of `#if` groups: implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task by task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** a property value written as a run of `#if … #endif` groups parses to the tree
§3 of the spec prescribes:
- directive-only empty groups are decorations;
- 2+ core-bearing groups with `;` inside every arm are a
  `preproc_conditional_property_value_sequence` in every family;
- `;`-after runs are element conditionals (link, Implementation, `OptionMembers`) or a sequence
  (CalcFormula, TableRelation, ML, Namespaces);
- everything else stays a visible ERROR owned by B13.

No silent split remains, and every previously correct production tree is byte-identical.

**Architecture:**
- **Grammar.** One shared recursive rule for the directive-only empty group, plus a JS
  generator that emits each family's run rules (terminated / non-terminated groups, the
  sequence). The family arms of `property`, `_property_with_terminator_in_if` and
  `_property_whole_value_in_if` use them.
- **Oracle.**
  - a new selector, `whole_value_select`;
  - a sequence assembler, contract `whole-value-run`;
  - an engine fix for ordered standalone `;`;
  - Implementation list-run lowering;
  - a `list-value-empty` rewrite;
  - a hole-aware `OptionMembers` check.
- **Spike gate.** Three spikes (generic, link, ML) gate the remaining families: the grammar is
  generated, the oracle lowers the trees, and every tree is checked before Task 6 starts.

**Tech stack:**
- tree-sitter 0.27 grammar DSL (`grammar.js`) and its generated `src/parser.c`;
- corpus fixtures;
- pytest;
- the config oracle (`tools/config_oracle`);
- `tools.alc_probe`;
- `tools/tree-harness.sh`;
- `tools/relation_census.py`;
- the traversal helper (`traversal/policy.json`, Python/JS/Rust bindings).

**Spec:** `docs/superpowers/specs/2026-10-05-property-value-runs-design.md`, revision 7,
approved 2026-10-05. Read it before any task. § references below are to it. §9 records six review
rounds and why each rule is the way it is.

## Global constraints

- **Rules files bind every task:** CLAUDE.md, `.claude/rules/*.md` and
  `docs/agent-brief-rules.md`.
- **Git Bash with Windows paths.** Never `2>nul`. Run `tree-sitter` only through
  `./tools/ts-lock.sh`. `python -m tools.perf ab` takes the lock itself.
- **Branch:** `fix/b11-value-runs`, which already carries the spec commits. Do not push.
- **Forbidden commands:**
  - `git stash`, `git reset --hard`, `git checkout --`, `git restore`, `git clean -f`;
  - `git worktree remove --force` (a safety hook blocks it; leave scratch worktrees and list
    them);
  - `find /`;
  - `tail -f | grep`.
- **Generated files:** commit `grammar.js`, `src/parser.c`, `src/grammar.json` and
  `src/node-types.json` together.
- **Commit messages:** every message ends with a measured `[BC.History: N errors, X% success]`.
- **Never commit:**
  - `__pycache__` / `.pyc` (check `git status` before every commit);
  - census manifests or other report output.
- **Corpora:** `./BC.History`, `./DC`, `H:/Git/BC28.1`, `H:/Git/BCApps-29.0`.
- **Hard limits:**
  - **Previously correct trees do not change.** Per-corpus tree-harness reports 0 changed
    files. In the corpus fixtures, only the cases §3.4 names may change (Task 8).
  - **STATE_COUNT** is measured and reported against the +2% guideline (base 17,918; guideline
    18,276). It is not a cap (spec §4.5), but every task that changes the grammar reports it.
  - **Declared conflicts:** every new declared conflict carries a comment naming its readings.
  - **No silent trees for step 5 shapes:** they must ERROR (spec §3.1).
- **Terms are the spec's:** core-bearing, value-contributing, directive-only empty,
  terminated. Do not introduce synonyms in code comments.
- **`-u` traps:** after any `tree-sitter test -u`, run `git diff --stat test/corpus`. Restore
  an untargeted file with `git show HEAD:path > path`. Prefer generating expectations from
  `python tools/snip.py --raw --sexp -f FILE` (fields labelled).
- **File locks.** A file write that fails with "Permission denied", Errno 22 or
  "user-mapped section open" is a transient lock on this machine. Retry it in a loop with
  `sleep 1`. The same goes for `tree-sitter generate`. Never treat it as permission to skip.
- **Scratchpad** (`$SCRATCH`):
  `C:/Users/SShadowS/AppData/Local/Temp/claude/U--Git-tree-sitter-al/7735bcff-35e6-47ee-87b9-879d6fed9fe1/scratchpad`.
  The 24 scratch probes of spec §2.1 are in `$SCRATCH/ss/probes/`, and their generator is
  `$SCRATCH/ss/gen_probes.py`.

## Review focus

1. **A conditional property block after a terminated group is absorbed into the value.**
   Example: `Visible = #if X true; #else false; #endif #if Y Caption = 'c'; #endif ;` must stay
   three nodes: `Visible`, a `preproc_conditional`, and an `empty_statement`. Task 3 adds the
   fixture, and Task 8's zero-delta gates cover production.
2. **A single-group tree that is correct today changes shape.** Every existing whole-value
   fixture must be byte-identical. Task 3, Step 6 diffs `test/corpus`, and Task 8 runs four
   corpora.
3. **A trailing `;` directly after an all-terminated run.** It is the property's own, as
   `Caption = #if X 'a'; #else 'b'; #endif ;` gives today. Task 3 adds the fixture, and Task 4
   adds the oracle case.
4. **An empty-value terminated arm** (`DataItemLink = #if X #if Y #endif ; #endif #if not X
   A = field(B); #endif`) keeps its `;` and lowers to "no value plus terminator". Task 5 adds
   the fixture and the oracle case.
5. **An incremental edit that changes the run's kind** (one group to two, terminated to
   non-terminated, `;` inside to `;` after). The incremental tree must equal a fresh parse.
   Task 7 adds the test.

---

### Task 1: baselines, compiler evidence, production rediscovery

**Files:**
- Create: `tools/alc_probe/cases/value-runs/*.al`
- Create: `tools/alc_probe/cases/value-runs/README-verdicts.txt`

**Interfaces:**
- Produces:
  - four tree-harness snapshots, `.snapshots/baseline-b11-{bc,dc,bc28,bcapps}`;
  - `$SCRATCH/al_base11.dll`, the pre-change library (Tasks 7 and 9);
  - the test total at the base (`T0`), recorded in the Task 1 commit message;
  - committed probes whose verdicts every fixture task cites.

- [ ] **Step 1: Baselines and base library**

```bash
cd U:/Git/tree-sitter-al
git status -sb | head -1        # expect: ## fix/b11-value-runs
./tools/ts-lock.sh ./tools/tree-harness.sh snapshot ./BC.History .snapshots/baseline-b11-bc
./tools/ts-lock.sh ./tools/tree-harness.sh snapshot ./DC .snapshots/baseline-b11-dc
./tools/ts-lock.sh ./tools/tree-harness.sh snapshot H:/Git/BC28.1 .snapshots/baseline-b11-bc28
./tools/ts-lock.sh ./tools/tree-harness.sh snapshot H:/Git/BCApps-29.0 .snapshots/baseline-b11-bcapps
./tools/metrics.sh | tail -3
./tools/ts-lock.sh tree-sitter build -o "$SCRATCH/al_base11.dll"
./tools/ts-lock.sh tree-sitter test > "$SCRATCH/t0.log" 2>&1; grep -c "✓" "$SCRATCH/t0.log"; grep -c "✗" "$SCRATCH/t0.log"
```

Expected:
- four snapshots;
- STATE_COUNT=17918;
- 2040 passing, 0 failing.

Record T0 = the passing count.

- [ ] **Step 2: Promote the 24 scratch probes and write the rest of spec §5.1**

**The 24 scratch probes.** Copy `$SCRATCH/ss/probes/*.al` to
`tools/alc_probe/cases/value-runs/`. Rewrite each header in `tools/alc_probe/README.md`'s format,
for example:

```al
// B11: CaptionML, run with `;` inside the arms (spec §2.1, §3.1 step 2).
// source: docs/superpowers/specs/2026-10-05-property-value-runs-design.md §5.1
// expect: * accept
```

**The rest of §5.1,** one file each, self-contained. Copy the prelude from
`$SCRATCH/ss/gen_probes.py` (`PRE` plus the host functions). Write decide-by-probe cases as
`// expect: * accept`, run them, then set the header to the real verdict.

Generic, run shapes:
- `generic-elif-run-inside.al`: `Caption = #if X 'a'; #elif Y 'b'; #endif #if not X 'c'; #endif` (`;` in every arm);
- `generic-three-group-run-inside.al`: three groups, `;` inside;
- `generic-nested-empty-prefix.al`: `Caption = #if X #if Y #endif #endif 'a';`;
- `generic-empty-between-groups-inside.al` and `generic-empty-after-last-inside.al`;
- `generic-trailing-semi-after-terminated-run.al`:
  `SourceTableView = #if X where(A = const(1)); #endif #if not X where(A = const(2)); #endif ;`;
- `generic-terminated-then-property.al`: the §4.2 `Visible`/`Caption` example;

Configuration-dependent boundaries (§3.4):
- `boundary-visible-caption.al`: the §3.4 example;
- `boundary-mixed-after.al`: `Visible = #if X true; #else false #endif #if X Caption = 'x' #endif ;`;
- `boundary-complementary-three.al`:
  `Caption = #if X 'a'; #endif #if not X 'b'; #endif #if Y Visible = true; #endif`.

  Record per-configuration verdicts with `// expect: X Y accept`-style lines.

All-empty sites and bare `;`:
- `all-empty-<family>.al`, one per family: `N = #if X #endif ;` (§4.1);
- `bare-semi-arm-<family>.al`, one per family: `N = #if X ; #else v; #endif`;
- `nested-empty-semi-arm-link.al`: the review-focus-4 `DataItemLink` example, in a report
  dataitem host.

List families:
- `optionmembers-entire-run.al`: `OptionMembers = #if X A, #else B, #endif #if Y C #else D #endif ;`;
- `optionmembers-blank-slots.al`: leading, consecutive and trailing `,` across groups;
- `optionmembers-selects-nothing.al`: `OptionMembers = #if X A, #endif #if Y B #endif ;`;
- `link-entire-run-separators.al`, `impl-entire-run-separators.al`: missing, leading and
  trailing separators, and no member selected;
- `link-comma-concat.al`: the §3.1 two-entry `SubPageLink` example;
- `link-nested-joining-comma.al`: the round-4 nested example (spec §9 round 4, finding 3).

Step 5 shapes (B13), each with its verdict:
- `b13-runobject-page-p.al`;
- `b13-call-f-paren.al` (`F` then `(1)`);
- `b13-decimal-range.al` (`0 :` then `5`);
- `b13-sorting-where.al`;
- `b13-ml-pairs-comma.al`, `b13-namespaces-pairs-comma.al`;
- `b13-caption-locked.al`.

Hosts:
- `host-action-area-generic-run-inside.al`;
- `host-assembly-generic-run-inside.al`;
- the same two hosts for ML and Namespaces.

- [ ] **Step 3: Run and pin**

Run: `python -m tools.alc_probe run tools/alc_probe/cases/value-runs --check`
Expected: exit 0.

A drift on a non-decide case is a STOP: report it, do not edit `expect`.

Write `README-verdicts.txt` with one line per decide case and its verdict. **What the verdicts
change:**

| verdict | effect |
|---|---|
| a §2.1 shape now rejected | STOP: the spec's ground truth changed; report before Task 3 |
| `all-empty-<f>` rejected for an optional family | the all-empty site still parses (structure, not validation); record it as over-acceptance in the verdicts file |
| `bare-semi-arm-<f>` accepted | record it; the grammar still does not admit a bare `;` arm (spec §3); add a B13 note in Task 9 |
| a host tuple rejected | that tuple gets no fixture; record it |
| a b13 shape rejected | it is not B13 debt: it becomes an ordinary negative in Task 7 |

- [ ] **Step 4: Production rediscovery (spec §2.3; discovery, not proof)**

Write `$SCRATCH/ss/prod_runs2.py`. It walks every parsed `property` in the four corpora,
iteratively (a recursive walk overflows on deep files). It reports:
- every `property` whose children, after skipping `comment` extras, hold a
  `preproc_conditional*` immediately after `=`;
- every `property` with a `preproc_conditional*` child after its value and before `;` (the
  empty-suffix discovery).

Start from `$SCRATCH/ss/prod_runs.py`.

Expected: only `permissions_property` sites (9). Paste the summary into the commit message.

- [ ] **Step 5: Commit**

```bash
git add tools/alc_probe/cases/value-runs
git status --short | grep -v '^??'
git commit -m "test(alc): B11 value-run evidence -- alc 18.0.41

<N> cases, <M> compiles. Decide-by-probe: <one line per verdict>.
Production rediscovery: <summary>. T0=<n> tests.

[BC.History: 0 errors, 100% success]"
```

---

### Task 2: oracle groundwork that needs no grammar change

**Files:**
- Modify: `tools/config_oracle/fixtures.py` (the `ROADMAP` constant)
- Modify: `tools/config_oracle/lowering/engine.py` (`_consume`'s mixed-placement branch, `LIST_RUN_TYPES`, `_check_alternation`, `_lower_ordinary`)
- Modify: `tools/config_oracle/contracts.py` (`preproc_conditional_impl_values`)
- Test: `tools/config_oracle/tests/test_b11_groundwork.py` (create)

**Interfaces:**
- Produces:
  - `fixtures.ROADMAP` containing `B10`, `B11`, `B12` and `B13`;
  - `engine.LIST_VALUE_EMPTY_KINDS = frozenset({"link_value_list", "implementation_value_list", "option_member_list"})`;
  - the normalisation note `list-value-empty:<kind>@<start>`;
  - `engine._check_option_holes(new)`, raising `LoweringError("list-separator", …)` only for
    two adjacent members with no separator;
  - `preproc_conditional_impl_values` registered `branch-select` / `_LIST_RUN`.

- [ ] **Step 1: Write the failing tests**

```python
"""B11 groundwork (spec 2026-10-05-property-value-runs-design.md §5.3): debt owners, ordered
standalone `;`, Implementation list-run lowering, list-value-empty, OptionMembers holes."""
import pytest

from tools.config_oracle import fixtures
from tools.config_oracle.tests import witness


@pytest.mark.parametrize("owner", ["B10", "B11", "B12", "B13"])
def test_roadmap_owners(owner):
    assert owner in fixtures.ROADMAP


IMPL = b"""interface IFoo { procedure Bar(); }
interface IBar { procedure Baz(); }
codeunit 50104 FooImpl implements IFoo { procedure Bar() begin end; }
codeunit 50106 BarImpl implements IBar { procedure Baz() begin end; }
enum 50105 E implements IFoo, IBar
{
    value(0; A)
    {
        Implementation =
#if X
            IFoo = FooImpl,
#endif
#if Y
            IBar = BarImpl
#endif
        ;
    }
}
"""


def test_impl_element_conditionals_lower(al_parser):
    # Until B11, preproc_conditional_impl_values was registered unsupported.
    witness.assert_produces(al_parser, IMPL, "preproc_conditional_impl_values")
    v = witness.verdicts(al_parser, IMPL)
    assert v["X=1,Y=1"][0] == "pass", v
    # X only: `IFoo = FooImpl, ;` -- the trailing `,` is refused by the strict check (spec §5.3)
    assert v["X=1,Y=0"][0] == "cannot-validate", v
    assert v["X=1,Y=0"][1][0].startswith("lowering:list-separator"), v
    assert v["X=0,Y=1"][0] == "pass", v
    assert v["X=0,Y=0"][0] == "pass", v      # list-value-empty: `Implementation = ;`


LINK_EMPTY = b"""table 50101 Cust { fields { field(1; A; Code[20]) { } field(2; B; Code[20]) { } } }
page 50103 L { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(F; Rec.A) { } } } } }
page 50100 P
{
    SourceTable = Cust;
    layout { area(Content) { part(P; L) {
        SubPageLink =
#if X
            A = field(B)
#endif
        ;
    } } }
}
"""


def test_link_list_emptied_is_removed(al_parser):
    v = witness.verdicts(al_parser, LINK_EMPTY)
    assert v["X=0"][0] == "pass", v
    assert any("list-value-empty:link_value_list" in i for i in v["X=0"][1]), v


SEMIS = b"""page 50100 P
{
    layout { area(Content) { field(F; X) {
        Caption =
#if X
            'a';
#else
            'b';
#endif
        ;
        ;
    } } }
}
"""


def test_three_semicolons_keep_source_order(al_parser):
    # Spec §5.3: later terminators of one property are ONE source-ordered SiblingsAfter.
    witness.assert_all_pass(al_parser, SEMIS)


OPTION_HOLES = b"""table 50100 T { fields { field(1; F; Option) {
    OptionMembers =
#if X
        A,,
#endif
        B,;
} } }
"""


def test_option_members_holes_are_legal(al_parser):
    witness.assert_all_pass(al_parser, OPTION_HOLES)
```

`witness.verdicts` returns `{config: (status, items)}`, keyed like `X=1,Y=0`
(`tools/config_oracle/tests/witness.py`).

- [ ] **Step 2: Run them to see them fail**

Run: `./tools/ts-lock.sh python -m pytest tools/config_oracle/tests/test_b11_groundwork.py -q`

Expected:

| test | fails with |
|---|---|
| roadmap owners | `B10`…`B13` not in ROADMAP |
| impl | `unsupported-type` |
| link empty | `empty-node` |
| three semicolons | a discrepancy on the order of the standalone `;` |
| option holes | `list-separator` |

- [ ] **Step 3: Implement**

`fixtures.py`:

```python
ROADMAP = frozenset({*(f"A{i}" for i in range(1, 8)), *(f"B{i}" for i in range(1, 14)),
                     "C1", "C2", "C3", "D1", "D2", "E1", "E2", "E3", "F1"})
```

`engine.py`:
- add `"preproc_conditional_impl_values"` to `LIST_RUN_TYPES`;
- add `LIST_VALUE_EMPTY_KINDS` beside `EMPTY_REMOVABLE`.

In `_lower_ordinary`, before `raise LoweringError("empty-node", node)`:

```python
        # list-value-empty (B11 spec §5.3): a list family's list emptied by its element
        # conditionals, at an optional value site. All three kinds reach only optional
        # families (generic and link), so the site check is the parent and the field.
        if (node.kind in LIST_VALUE_EMPTY_KINDS and node.field == "value"
                and ctx.parent_kind in ("property", "preproc_conditional_property_value")):
            ctx.normalised.append(f"list-value-empty:{node.kind}@{node.start}")
            return Lowered([], frags)
```

Replace the alternation call for option lists:

```python
    if any(c.kind in LIST_RUN_TYPES for c in node.children):
        if new.kind == "option_member_list":
            _check_option_holes(new)
        else:
            _check_alternation(new)
```

```python
def _check_option_holes(new):
    """OptionMembers keeps blank ordinals (B11 spec §5.3): leading, consecutive and trailing
    `,` are legal. Only two members side by side, with no separator, are refused."""
    prev_item = False
    for c in new.children:
        if c.kind == ";" and not c.children:
            continue
        is_sep = c.kind == "," and not c.children
        if not is_sep and prev_item:
            raise LoweringError("list-separator", new, "two members without a separator")
        prev_item = not is_sep
```

**The mixed-placement branch of `_consume`** (the `SiblingsAfter(None, [Node("empty_statement", …)])` creation). Today it builds one `SiblingsAfter` per later `;`. Change it so all of one property's later `;` share ONE fragment, kept in source order:

```python
                first, later = sorted((last, f.leaf), key=lambda n: n.start)
                new.children[-1] = first
                recompute_span(new)
                stmt = Node("empty_statement", True, None, later.start, later.end, [later])
                sib = next((r for r in rest if isinstance(r, SiblingsAfter)
                            and getattr(r, "_mixed_semis", False)), None)
                if sib is None:
                    sib = SiblingsAfter(None, [stmt])
                    sib._from_last = True
                    sib._mixed_semis = True
                    rest.append(sib)
                else:
                    sib.nodes.append(stmt)
                    sib.nodes.sort(key=lambda n: n.start)
```

**Registering Implementation in `contracts.py`.** Remove `"preproc_conditional_impl_values"`
from the `unsupported` loop. Register it beside the link entry:

```python
register("preproc_conditional_impl_values", "branch-select", _LIST_RUN,
         hosts={"implementation_value_list:<children>": "list-run",
                "preproc_conditional_impl_values:<children>": "list-run"},
         # _impl_value_seq / _impl_value_branch / _impl_value_run (grammar.js).
         arm={"implementation_value", "preproc_conditional_impl_values", ","})
```

Read the `_impl_value_*` rules in `grammar.js` first. Set `arm` to exactly the visible kinds
they produce. If a kind is missing, `registry census` stage (a) of the quick tier names it.

- [ ] **Step 4: Run tests and the quick tier**

```bash
./tools/ts-lock.sh python -m pytest tools/config_oracle/tests -q -x
python -m tools.config_oracle run --tier quick 2>&1 | grep -E "stage|unclassified:|stale|exit code"
```

**Pytest:** all pass.

**Quick tier:**
- exit 0;
- or exactly the new impl records. Classify those in `fixture-classes.tsv`:
  - **separator refusals:** `invalid-config` with alc evidence from Task 1's
    `impl-entire-run-separators.al`;
  - **any record that is not a separator refusal:** STOP and report.

No existing record may change status. `stale classifications: 0` and `unclassified: 0`
together prove it: a changed classified record turns stale, and a changed unclassified one is
listed.

- [ ] **Step 5: Commit**

```bash
git add tools/config_oracle/fixtures.py tools/config_oracle/lowering/engine.py \
        tools/config_oracle/contracts.py tools/config_oracle/fixture-classes.tsv \
        tools/config_oracle/tests/test_b11_groundwork.py
git commit -m "feat(oracle): B11 groundwork -- debt owners B10-B13, ordered standalone ;, Implementation list-run, list-value-empty, OptionMembers holes

[BC.History: 0 errors, 100% success]"
```

---

### Task 3: grammar spike 1 -- the shared empty group and the generic family

**Files:**
- Modify: `grammar.js`, then generate `src/parser.c`, `src/grammar.json` and `src/node-types.json`
- Create: `test/corpus/property_value_run_test.txt`
- Modify: `test/corpus/calcformula_conditional_test.txt` (only if the empty-prefix node shape changes; it must not)

**Interfaces:**
- Consumes: Task 1's probes.
- Produces (rule names later tasks use verbatim):
  - `_empty_value_conditional`, the directive-only empty group, recursive;
  - `_value_decoration`, i.e. `alias($._empty_value_conditional, $.preproc_conditional_property_value)`;
  - `valueRunRules(prefix, valueFn, optionalCore)`, a JS generator returning rule entries
    named `${prefix}_arm_t`, `${prefix}_arm_nt`, `${prefix}_group_t`, `${prefix}_group_nt`,
    `${prefix}_tail_gap`, `${prefix}_in_core` and `${prefix}_sequence_in`;
  - the visible node `preproc_conditional_property_value_sequence`.

- [ ] **Step 1: Write the generic fixture cases (RED)**

Create `test/corpus/property_value_run_test.txt`. Each case's source is a Task 1 probe body
with the `//` header lines dropped. Take the expected tree from
`python tools/snip.py --raw --sexp -f <file>` at HEAD, which records today's ERROR or split. Use
the B8 generator as the model (`$SCRATCH/b8_fixture.py`), copied to
`$SCRATCH/b11_fixture.py` with a case list.

Generic cases:
1. empty prefix, `Caption` and `Visible`;
2. nested empty prefix;
3. empty suffix (`;` after placement);
4. run with `;` inside, two groups;
5. the same with `#elif`;
6. three groups;
7. empty group between groups, and after the last (inside placement);
8. `SourceTableView` terminated `where` alternatives with a directly following `;`
   (review focus 3);
9. terminated group then a conditional property then `;` (review focus 1);
10. the §3.4 boundary example;
11. the complementary three-group residue;
12. the action-area and assembly hosts.

Run: `./tools/ts-lock.sh tree-sitter test --file-name property_value_run_test.txt`
Expected: passes with today's (wrong) trees. That is the RED record. Commit nothing yet.

- [ ] **Step 2: Add the shared empty group and the generator**

At the top of `grammar.js`, after `keyedValueConditional`:

```javascript
// B11 (spec 2026-10-05-property-value-runs-design.md §3, §4): a property value made of a
// run of #if groups, `;` inside every arm (§3.1 step 2). One generator per family keeps
// the six families from drifting. Rule shapes:
//   arm_t   -- a present arm that ends in `;` in every configuration
//   arm_nt  -- a present arm that may not (its core is a non-terminated nested run)
//   group_t -- #else present, every arm arm_t: every configuration has emitted `;`
//   group_nt-- every other core-bearing group; disjoint from group_t by construction:
//              no #else, or a gap (absent / directive-only / arm_nt) in some slot
//   sequence_in -- 2+ core-bearing groups; every non-last one is group_nt (§4.3)
function valueRunRules(p, value, optionalCore) {
  const n = s => `${p}_${s}`;
  const deco = $ => repeat($._value_decoration);
  const core = $ => choice(
    alias($[n('group_t')], $.preproc_conditional_property_value),
    alias($[n('group_nt')], $.preproc_conditional_property_value),
    alias($[n('sequence_in')], $.preproc_conditional_property_value_sequence),
  );
  return {
    [n('arm_t')]: $ => seq(deco($), choice(
      seq(field('value', value($)), ';'),
      // an empty-value terminated arm (§3 "Bare `;` arms"): only where the family value
      // is optional, and only after at least one decoration -- never a bare `;`
      ...(optionalCore ? [seq(repeat1($._value_decoration), ';')] : []),
      field('value', alias($[n('group_t')], $.preproc_conditional_property_value)),
    )),
    [n('arm_nt')]: $ => seq(deco($), field('value', choice(
      alias($[n('group_nt')], $.preproc_conditional_property_value),
      alias($[n('sequence_in')], $.preproc_conditional_property_value_sequence),
    ))),
    // a slot that is not arm_t: absent (decorations only) or a non-terminated nested core
    [n('gap')]: $ => choice(repeat1($._value_decoration), $[n('arm_nt')]),
    [n('group_t')]: $ => seq(
      $.preproc_if, $[n('arm_t')],
      repeat(seq($.preproc_elif, $[n('arm_t')])),
      $.preproc_else, $[n('arm_t')],
      $.preproc_endif,
    ),
    [n('group_nt')]: $ => choice(
      // no #else: never terminated. Witness: some slot holds an arm.
      seq($.preproc_if, choice($[n('arm_t')], $[n('arm_nt')]),
        repeat(seq($.preproc_elif, optional(choice($[n('arm_t')], $[n('arm_nt')], deco($))))),
        $.preproc_endif),
      seq($.preproc_if, optional(deco($)),
        repeat(seq($.preproc_elif, optional(deco($)))),
        $.preproc_elif, choice($[n('arm_t')], $[n('arm_nt')]),
        repeat(seq($.preproc_elif, optional(choice($[n('arm_t')], $[n('arm_nt')], deco($))))),
        $.preproc_endif),
      // #else present: some slot is a gap
      seq($.preproc_if, $[n('arm_t')], $[n('tail_gap')]),
      seq($.preproc_if, $[n('arm_nt')],
        repeat(seq($.preproc_elif, optional(choice($[n('arm_t')], $[n('arm_nt')], deco($))))),
        $.preproc_else, optional(choice($[n('arm_t')], $[n('arm_nt')], deco($))),
        $.preproc_endif),
      seq($.preproc_if, optional(deco($)),
        repeat(seq($.preproc_elif, optional(choice($[n('arm_t')], $[n('arm_nt')], deco($))))),
        $.preproc_else, choice($[n('arm_t')], $[n('arm_nt')]),
        $.preproc_endif),
    ),
    // after a full #if arm: an #elif/#else slot that is a gap, or more full slots then one
    [n('tail_gap')]: $ => choice(
      seq($.preproc_elif, $[n('gap')],
        repeat(seq($.preproc_elif, optional(choice($[n('arm_t')], $[n('arm_nt')], deco($))))),
        $.preproc_else, optional(choice($[n('arm_t')], $[n('arm_nt')], deco($))),
        $.preproc_endif),
      seq($.preproc_elif, $[n('arm_t')], $[n('tail_gap')]),
      seq($.preproc_else, optional($[n('gap')]), $.preproc_endif),
    ),
    // 2+ core-bearing groups; every non-last one non-terminated (§4.3)
    [n('sequence_in')]: $ => prec.dynamic(1, seq(
      field('value', alias($[n('group_nt')], $.preproc_conditional_property_value)),
      repeat(seq(deco($), field('value', alias($[n('group_nt')], $.preproc_conditional_property_value)))),
      deco($),
      field('value', choice(
        alias($[n('group_nt')], $.preproc_conditional_property_value),
        alias($[n('group_t')], $.preproc_conditional_property_value),
      )),
    )),
    [n('in_core')]: core,
  };
}
```

This is the spike's starting point, not a frozen form. Restructure freely as long as:
- the tree contract of spec §3 holds;
- `group_t` and `group_nt` stay disjoint;
- every decision is kept alive until its discriminating token (§4.3 "Delayed decisions").

Report every restructuring in the task report.

In `rules`:

```javascript
    _empty_value_conditional: $ => seq(
      $.preproc_if, repeat($._value_decoration),
      repeat(seq($.preproc_elif, repeat($._value_decoration))),
      optional(seq($.preproc_else, repeat($._value_decoration))),
      $.preproc_endif,
    ),
    _value_decoration: $ => alias($._empty_value_conditional, $.preproc_conditional_property_value),
    ...valueRunRules('_generic', $ => $._property_value, true),
```

**Replace B8's `_calc_formula_empty_conditional`** with `_value_decoration`, in the CalcFormula
`property` arm and in the declared conflict. Delete the old rule. Its node shape is identical
(`preproc_conditional_property_value` with only directives), so
`calcformula_conditional_test.txt` must not change.

- [ ] **Step 3: Wire the generic family**

**`property`'s generic arm (`;` after; §3.1 steps 1 and 5).** The value may carry decorations,
and stays one core:

```javascript
      seq(
        field('name', $.property_name),
        '=',
        repeat($._value_decoration),
        optional(field('value', $._property_value)),
        repeat($._value_decoration),
        ';'
      ),
```

**`_property_with_terminator_in_if` and `_property_whole_value_in_if`, generic arm (`;`
inside).** Replace `alias($._property_value_conditional_in_if, …)` with:

```javascript
      seq(
        field('name', $.property_name),
        '=',
        repeat($._value_decoration),
        field('value', $._generic_in_core),
      ),
```

`_property_value_conditional_in_if` and `_property_value_branch_in_if` become unreferenced.
Delete them (validate-grammar.sh's orphan check enforces this).

**Conflicts.** Add the conflicts the generator demands, each with a comment naming its
readings. The expected ones:
- `_empty_value_conditional` against each group rule (`#if X #endif` is empty until a value
  appears);
- `_generic_group_nt` against `_generic_group_t` at `#else`;
- the sequence against a following `preproc_conditional` body element after a non-terminated
  group (§4.3 continuation, preferred by `prec.dynamic`).

- [ ] **Step 4: Generate and measure**

```bash
./tools/ts-lock.sh tree-sitter generate 2>&1 | tail -30
grep -E '#define (STATE_COUNT|SYMBOL_COUNT)' src/parser.c
```

Record STATE_COUNT. An `Unresolved conflict` names two rules: add the conflict only when the two
readings genuinely differ after the run (comment them); otherwise restructure.

- [ ] **Step 5: Regenerate the fixture and check every tree by hand (GREEN)**

Rerun `$SCRATCH/b11_fixture.py`. Check each case against spec §3:

| case | required tree |
|---|---|
| 1-3 | ONE `property`, unfielded `preproc_conditional_property_value` decoration(s), `value:` the plain value |
| 4-7 | ONE `property`, `value: (preproc_conditional_property_value_sequence value: (...) value: (...))`; interior decorations unfielded inside the sequence; arms' `;` unfielded inside their groups |
| 8 | ONE `property`: `=`, the sequence, then the property's own `;` (review focus 3) |
| 9 | `property` (`Visible`, one group), then `preproc_conditional` holding `property` `Caption`, then `empty_statement` (review focus 1) |
| 10 | ONE `property` with a sequence (one-reading, §3.4) |
| 11 | ONE `property` with a three-group sequence |
| 12 | as 4, at the action-area and assembly hosts |

`has_error` must be False on every case. Fix the grammar until each holds. Do not accept a
tree that differs.

Prove the file can fail: rename one `value:` to `bogus:`, confirm exactly 1 failing case, and
restore it.

- [ ] **Step 6: Whole suite, existing fixtures unchanged**

```bash
./tools/ts-lock.sh tree-sitter test > "$SCRATCH/t3.log" 2>&1; grep -c "✓" "$SCRATCH/t3.log"; grep "✗" "$SCRATCH/t3.log" | head
git diff --stat test/corpus
```

**Expected passing count:** T0 + the number of cases you added.

**A failing existing case is a STOP.** Do not `-u` it. It means a previously correct tree
changed (review focus 2). The only exceptions are the §3.4 intended corrections, and the
generic empty prefix (`option_member_list`) is the only one in this family. Run
`grep -rl "option_member_list" test/corpus` against today's trees to find any fixture pinning
it, and change only that case's expectation, with the reason in the commit message.

- [ ] **Step 7: Spike report and commit**

Write `$SCRATCH/b11-spike-generic.md`:
- STATE_COUNT before and after;
- every declared conflict and its readings;
- the 12 trees, pasted;
- every restructuring of the Step 2 draft.

```bash
git add grammar.js src/parser.c src/grammar.json src/node-types.json test/corpus/property_value_run_test.txt
git commit -m "feat(b11): spike 1 -- shared empty group, generic value runs (;-inside sequences, decorations)

STATE_COUNT 17918 -> <n>. Conflicts: <list>.

[BC.History: <measured>]"
```

Measure BC.History with `./parse-al-parallel.sh ./BC.History/ .` before committing.

---

### Task 4: spike 2 -- oracle lowering of sequences and decorations

**Files:**
- Modify: `tools/config_oracle/lowering/assemblers.py` (add `whole_value_select`, `value_run_select`)
- Modify: `tools/config_oracle/contracts.py` (`preproc_conditional_property_value` entry; new sequence entry)
- Modify: `tools/config_oracle/tests/test_property_value_conditional.py` (mutation tests point at the new selector)
- Modify: `traversal/policy.json`
- Modify: `tools/check-field-types.py`
- Test: `tools/config_oracle/tests/test_value_runs.py` (create); `tests/traversal/` witnesses

**Interfaces:**
- Consumes: Task 3's node `preproc_conditional_property_value_sequence` (children:
  `value:` groups plus unfielded decorations), and Task 2's `LIST_VALUE_EMPTY_KINDS`.
- Produces:
  - `assemblers.whole_value_select(node, ctx) -> Lowered`, now the handler of
    `preproc_conditional_property_value`;
  - `assemblers.value_run_select(node, ctx) -> Lowered`, the handler of the sequence,
    contract `whole-value-run`;
  - the refusal `LoweringError("one-reading", sequence, ctx.host())`.

- [ ] **Step 1: Write the failing tests**

`tools/config_oracle/tests/test_value_runs.py`. Use the Task 3 fixture sources, which are the
same text as the probes:

```python
"""B11 sequences and decorations (spec §5.3, contract whole-value-run)."""
import pytest

from tools.config_oracle.tests import witness

SEQ = "preproc_conditional_property_value_sequence"


def _page_field(body: str) -> bytes:
    return ("page 50100 P { layout { area(Content) { field(F; X) {\n" + body + "\n} } } }\n").encode()


RUN_INSIDE = _page_field("Caption =\n#if X\n 'a';\n#endif\n#if not X\n 'b';\n#endif")
EMPTY_PREFIX = _page_field("Caption =\n#if X\n#endif\n 'a';")
NESTED_EMPTY = _page_field("Caption =\n#if X\n#if Y\n#endif\n#endif\n 'a';")
TRAILING = _page_field("Caption =\n#if X\n 'a';\n#endif\n#if not X\n 'b';\n#endif\n;")
BOUNDARY = _page_field("Visible =\n#if X\n true;\n#endif\n#if X\n Caption = 'x';\n#else\n false;\n#endif")


def test_run_inside_every_config_passes(al_parser):
    witness.assert_produces(al_parser, RUN_INSIDE, SEQ)
    witness.assert_all_pass(al_parser, RUN_INSIDE)


@pytest.mark.parametrize("src", [EMPTY_PREFIX, NESTED_EMPTY])
def test_decorations_lower_to_nothing(al_parser, src):
    witness.assert_all_pass(al_parser, src)


def test_directly_following_semicolon_is_the_propertys(al_parser):
    witness.assert_all_pass(al_parser, TRAILING)


def test_boundary_is_one_reading(al_parser):
    v = witness.verdicts(al_parser, BOUNDARY)
    statuses = {c: s for c, (s, _) in v.items()}
    assert statuses["X=0"] == "pass", v
    assert statuses["X=1"] == "cannot-validate", v
    assert v["X=1"][1][0].startswith("lowering:one-reading"), v


def test_second_value_is_refused_not_passed(al_parser, monkeypatch):
    # Mutation: without the one-reading refusal, X=1 lowers two values into one property.
    # That must surface as a discrepancy, never a pass -- the refusal is what keeps it honest.
    from tools.config_oracle.lowering import assemblers, engine

    def lenient(node, ctx):
        values, frags = [], []
        for c in node.children:
            r = engine.lower(c, ctx.child(node.kind, c.field or "<children>"))
            values.extend(n.copy(field=node.field) for n in r.nodes)
            frags.extend(r.frags)
        return engine.Lowered(values, frags)
    monkeypatch.setattr(assemblers, "value_run_select", lenient)
    v = witness.verdicts(al_parser, BOUNDARY)
    assert v["X=1"][0] == "discrepancy", v
```

In `test_property_value_conditional.py`, point the two mutation tests at
`assemblers.whole_value_select`, keeping their assertions.

- [ ] **Step 2: Run them to see them fail**

Run: `./tools/ts-lock.sh python -m pytest tools/config_oracle/tests/test_value_runs.py -q`
Expected: failures on `unsupported`, unregistered type or `contract-shape` (the sequence and
decorations are unknown to the oracle).

- [ ] **Step 3: Implement the selector and the assembler** (`assemblers.py`)

```python
PCPV = "preproc_conditional_property_value"
PCPV_SEQ = "preproc_conditional_property_value_sequence"


def _is_decoration(c):
    return c.kind == PCPV and c.field is None


def whole_value_select(node, ctx) -> Lowered:
    """Contract whole-value-select (G6), at every value site (B11 spec §5.3). An arm holds
    unfielded directive-only decorations (lowered to nothing), at most one core in field
    `value`, and the arm's `;` (a Terminator, terminator-hoist). A nested group or sequence
    in the core is lowered recursively; its fragments pass up in source order. More than one
    value node is contract-shape: a sequence, not an arm, is where several groups live."""
    entry = contracts.REGISTRY[node.kind]
    if ctx.policy(entry, node) == "unsupported":
        raise LoweringError("unsupported-type", node, ctx.host())
    arms, endif = split_arms(node)
    nodes, frags = [], []
    for c in _active(arms, endif, node, ctx):
        if c.kind == ";" and not c.children:
            frags.append(Terminator(None, _lower_all([c], ctx, node.kind)[0]))
        elif _is_decoration(c):
            r = lower(c, ctx.child(node.kind, "<children>"))
            if r.nodes:
                raise LoweringError("contract-shape", c, "decoration lowered to nodes")
            frags.extend(r.frags)
        elif c.field != "value" or c.kind not in entry.arm:
            raise LoweringError("contract-shape", node, "arm: " + c.kind)
        elif c.kind in (PCPV, PCPV_SEQ):
            r = lower(c, ctx.child(node.kind, "value"))
            nodes.extend(n.copy(field=node.field) for n in r.nodes)
            frags.extend(r.frags)
        else:
            nodes.extend(n.copy(field=node.field) for n in _lower_all([c], ctx, node.kind))
    if len(nodes) > 1:
        raise LoweringError("contract-shape", node, f"{len(nodes)} values in one arm")
    return Lowered(nodes, frags)


def value_run_select(node, ctx) -> Lowered:
    """Contract whole-value-run (B11 spec §5.3). The groups are walked in source order, each
    through whole_value_select. Zero or one value results: a second value, or any value
    after a selected terminator, is lowering:one-reading -- the property's boundary moves
    with the configuration there (spec §3.4, roadmap B12). The predicate is this
    sequence's own (reading=None), as ExpressionContinuation's is."""
    values, frags, terminated = [], [], False
    for c in node.children:
        if c.kind != PCPV:
            raise LoweringError("contract-shape", node, "child: " + c.kind)
        r = lower(c, ctx.child(node.kind, c.field or "<children>"))
        if c.field is None and r.nodes:
            raise LoweringError("contract-shape", c, "decoration lowered to nodes")
        for n in r.nodes:
            if values or terminated:
                raise LoweringError("one-reading", node, ctx.host())
            values.append(n.copy(field=node.field))
        for f in r.frags:
            terminated = terminated or isinstance(f, Terminator)
            frags.append(f)
    return Lowered(values, frags)
```

**`contracts.py`.** In the `preproc_conditional_property_value` registration:
- set the handler to `whole_value_select`;
- add `"preproc_conditional_property_value_sequence"` to `arm`;
- add the hosts:

```python
                "property:<children>": "optional-slot",
                "preproc_conditional_property_value:<children>": "optional-slot",
                "preproc_conditional_property_value_sequence:value": "optional-slot",
                "preproc_conditional_property_value_sequence:<children>": "optional-slot",
```

Then register the sequence:

```python
# B11 (spec 2026-10-05-property-value-runs-design.md §5.3): a run of 2+ core-bearing
# whole-value groups. Contract whole-value-run: zero or one value, enforced by the
# assembler (single-slot here is metadata); anything else is one-reading (debt B12).
register("preproc_conditional_property_value_sequence", "assembler",
         "tools.config_oracle.lowering.assemblers.value_run_select",
         hosts={"property:value": "single-slot",
                "preproc_conditional_property_value:value": "single-slot"})
```

- [ ] **Step 4: Traversal and field pins**

**`traversal/policy.json`.** Add
`"preproc_conditional_property_value_sequence": {"class": "assembler", "arm_boundary": "none",
"hosts": {...the two hosts above...}, "reason": "B11: a run of whole-value groups; its child
groups own the directives (spec §5.5)."}`. Mirror the shape of the existing entries.
- Add one witness per runtime. Take the Python one from `tests/traversal`, and the JS and Rust
  ones from their existing fixtures. Each walks `RUN_INSIDE` and asserts that every
  `preproc_conditional_property_value` child yields a `SplitInfo` with its arms.
- Regenerate the expected files with `python tests/traversal/regen_expected.py` and review
  every hunk.

**`tools/check-field-types.py`.** Add:

```python
    # B11: a run of whole-value groups. Several groups, one value per configuration
    # (spec §3.3). property.value stays single (its pin above is unchanged).
    inv('preproc_conditional_property_value_sequence', 'value', True, set(), 'FIXED',
        "a run of whole-value groups is one sequence node, never sibling property values",
        types={'preproc_conditional_property_value'}),
```

- [ ] **Step 5: Run everything oracle-side**

```bash
./tools/ts-lock.sh python -m pytest tools/config_oracle/tests -q
python -m tools.config_oracle run --tier quick 2>&1 | grep -E "stage|unclassified:|stale|exit code"
python tools/traversal_census.py; echo "exit=$?"
./tools/ts-lock.sh python -m pytest tests/traversal -q
python tools/check-field-types.py; echo "exit=$?"
```

**Expected:** pytest passes, traversal census exit 0, field types exit 0.

**Quick tier:** clean, except the Task 3 fixture's one-reading and B13-free records. Classify
those in `tools/config_oracle/fixture-classes.tsv`:

```text
property_value_run_test.txt#<case>#0	X=1	cannot-validate:lowering:one-reading:one-reading at preproc_conditional_property_value_sequence	debt(B12): the property's boundary moves with the configuration (spec §3.4); a multi-configuration representation removes it
```

Use the exact first item the runner prints. Every other unclassified record is a STOP.

- [ ] **Step 6: Spike gate 1 (generic: grammar plus lowering)**

Append to `$SCRATCH/b11-spike-generic.md` every Task 3 case's per-configuration verdicts.
**Gate:** every configuration is `pass`, a classified `debt(B12)` one-reading, or a classified
`invalid-config`. Anything else is a STOP: the design returns to review (spec §7).

- [ ] **Step 7: Commit**

```bash
git add tools/config_oracle traversal tests/traversal tools/check-field-types.py bindings
git status --short | grep -v '^??'
git commit -m "feat(oracle): B11 whole_value_select and the sequence assembler (whole-value-run); traversal, field pin

Spike gate 1 (generic): <verdict summary>.

[BC.History: <measured>]"
```

---

### Task 5: spike 3 -- link and ML

**Files:**
- Modify: `grammar.js` and the generated files
- Modify: `test/corpus/property_value_run_test.txt`
- Modify: `tools/config_oracle/fixture-classes.tsv`

**Interfaces:**
- Consumes: `valueRunRules` (Task 3), and the oracle (Task 4).
- Produces: `_link_in_core` and `_ml_in_core`, plus the ML `;`-after sequence rule
  `_ml_sequence_after`.

- [ ] **Step 1: Fixture cases (RED)** Add them from the Task 1 probes.

Link:
- the run with `;` inside: quoted, and the unquoted item 35 form;
- the same with a trailing `;` (review focus 3);
- the empty-value terminated arm (review focus 4), in a report dataitem host;
- the entirely conditional comma run (`;` after; element conditionals, unchanged);
- nested joining comma;
- an emptied list.

ML:
- the empty prefix;
- the run with `;` inside;
- the run with `;` after;
- the comma-edge arms (B13, which goes to the gap file in Task 7);
- the action-area host.

Generate the trees at HEAD and run the file.

- [ ] **Step 2: Wire link (`;` inside) and ML (both placements)**

```javascript
    ...valueRunRules('_link', $ => $._link_property_value, true),
    ...valueRunRules('_ml', $ => $._ml_property_value, true),
```

**Link in `_property_with_terminator_in_if`.** Replace
`alias($._link_whole_conditional_in_if, …)` with
`repeat($._value_decoration), field('value', $._link_in_core)`. Delete
`_link_whole_conditional_in_if`, `_link_in_if_arm` and `_link_in_if_tail` when they are
orphaned. Their witness is now `group_nt`'s.

**ML in `_property_with_terminator_in_if` and `_property_whole_value_in_if`.** Replace
`alias($._ml_value_conditional, …)` with the same decorated `_ml_in_core`.

**ML in `property` (`;` after, step 4).**

```javascript
      seq(
        field('name', alias($._ml_property_name, $.property_name)),
        '=',
        repeat($._value_decoration),
        optional(field('value', choice(
          $._ml_property_value,
          alias($._ml_sequence_after, $.preproc_conditional_property_value_sequence),
        ))),
        repeat($._value_decoration),
        ';'
      ),
```

```javascript
    // B11 §3.1 step 4: a `;`-after run of complete ML values. Complete ML pair lists cannot
    // concatenate without `,`, and a `,`-edge arm is not a complete value (step 5, B13).
    _ml_sequence_after: $ => seq(
      field('value', alias($._ml_value_conditional, $.preproc_conditional_property_value)),
      repeat1(seq(repeat($._value_decoration),
        field('value', alias($._ml_value_conditional, $.preproc_conditional_property_value)))),
    ),
```

**Link `;`-after placement.** Unchanged (element conditionals, step 3).

**Step 3 vs step 2 for link.** The `;`-inside link sequence and the element-conditional list
share a prefix up to the first arm's `;`. Keep both alive. The arm `;` (sequence) or its absence
(element list) decides, under link precedence 6. Report the conflicts declared.

- [ ] **Step 3: Generate, regenerate trees, check by hand**

Repeat Task 3 Steps 4-6 for these cases:
- the link `;`-inside runs are sequences;
- the item 35 unquoted case is ONE `SubPageLink` property (two today);
- the entirely conditional comma run stays two `preproc_conditional_link_values` inside
  `link_value_list` (unchanged);
- the empty-value terminated arm is a group whose arm holds an unfielded decoration and its
  `;`;
- ML: one property, with decorations or a sequence.

Every other existing fixture is unchanged.

- [ ] **Step 4: Oracle verdicts, spike gates 2 and 3**

Run the quick tier, then classify:
- **one-reading** records: `debt(B12)`;
- **separator refusals:** `invalid-config`, with Task 1 alc evidence;
- **the empty-value terminated arm:** must pass in every configuration (review focus 4).

Add the case to `test_value_runs.py`:

```python
DIL = (b"table 50101 Cust { fields { field(1; A; Code[20]) { } field(2; B; Code[20]) { } } }\n"
       b"report 50100 R { dataset { dataitem(D; Cust) { dataitem(E; Cust) {\n"
       b"DataItemLink =\n#if X\n#if Y\n#endif\n;\n#endif\n#if not X\nA = field(B);\n#endif\n"
       b"} } } }\n")


def test_empty_value_terminated_arm_keeps_its_terminator(al_parser):
    witness.assert_all_pass(al_parser, DIL)
```

Append the link and ML results to `$SCRATCH/b11-spike-generic.md` (rename it
`b11-spikes.md`).

**Gate:** as in Task 4, Step 6, for link and ML. A failure is a STOP: the design returns to
review.

- [ ] **Step 5: Commit**

```bash
git add grammar.js src/parser.c src/grammar.json src/node-types.json test/corpus/property_value_run_test.txt \
        tools/config_oracle/fixture-classes.tsv tools/config_oracle/tests/test_value_runs.py
git commit -m "feat(b11): spikes 2-3 -- link and ML value runs; item 35 split fixed

STATE_COUNT <before> -> <after>. Spike gates: generic/link/ML pass (<summary>).

[BC.History: <measured>]"
```

---

### Task 6: remaining families -- Namespaces, TableRelation, CalcFormula, OptionMembers

**Precondition:** the three spike gates passed (Tasks 4 and 5). Otherwise do not start.

**Files:**
- Modify: `grammar.js` and the generated files
- Modify: `test/corpus/property_value_run_test.txt`, `tools/config_oracle/fixture-classes.tsv`

**Interfaces:**
- Consumes: `valueRunRules`, `_value_decoration`, the oracle.
- Produces:
  - `_namespaces_in_core`, `_namespaces_sequence_after`;
  - `_table_relation_in_core`, `_table_relation_sequence_after`;
  - `_calc_formula_in_core`, `_calc_formula_sequence_after`;
  - the entirely conditional `OptionMembers` form.

- [ ] **Step 1: Fixture cases (RED)** from the Task 1 probes:
  - Namespaces, TableRelation and CalcFormula: each × {empty prefix, run with `;` inside, run
    with `;` after};
  - the all-empty TableRelation and CalcFormula sites, which must ERROR, as negatives;
  - **TableRelation preservation**, from the existing fixtures that pin
    `_table_relation_keyed_split`, `preproc_conditional_table_relation` +
    `else_table_relation_fragment`, and `_table_relation_open_if`. Copy one case of each
    shape, so this file pins them next to the runs;
  - **CalcFormula without `where`**: `CalcFormula = #if X sum(S.A); #endif #if not X
    count(S); #endif` (an `aggregate_formula` per arm, never a call; issue #21);
  - **`OptionMembers`:**
    - the entirely conditional run;
    - blank slots;
    - selects nothing;
    - one bare member, which unwraps;
    - one member plus blank slots, which does not.

- [ ] **Step 2: Wire them**

**The generators.**

```javascript
    ...valueRunRules('_namespaces', $ => $._namespaces_property_value, true),
    ...valueRunRules('_table_relation', $ => $._table_relation_property_value, false),
    ...valueRunRules('_calc_formula', $ => $._calc_formula_value, false),
```

**The `;`-inside arms of `_property_with_terminator_in_if`.**
- **Namespaces and CalcFormula:** take `repeat($._value_decoration),
  field('value', $._<f>_in_core)`. Namespaces also takes it in `_property_whole_value_in_if`.
- **TableRelation:** keep `alias($._table_relation_keyed_split, $.table_relation_value)` as a
  separate alternative of its value, beside the new core:

```javascript
        field('value', choice(
          $._table_relation_in_core,
          alias($._table_relation_keyed_split, $.table_relation_value),
        )),
```

**`property`'s `;`-after arms for these three.** Add
`alias($._<f>_sequence_after, $.preproc_conditional_property_value_sequence)` to the value
`choice`, with decorations around it, as Task 5 did for ML. Each `_<f>_sequence_after` follows
`_ml_sequence_after` with the family's existing whole-value conditional:
- `_namespaces_value_conditional`;
- `_table_relation_whole_conditional`;
- `_calc_formula_conditional`.

CalcFormula's existing `repeat(...decoration...)` stays where B8 put it, and is now the shared
rule.

**`OptionMembers`, entirely conditional (step 3).** Add to `option_member_list`, mirroring
`_link_value_seq`'s conditional-led form:

```javascript
      // B11 §3.1 step 3: an entirely conditional OptionMembers list. Element conditionals carry
      // their own `,`; blank slots stay (spec §5.3, hole-aware).
      seq(
        $.preproc_conditional_option_members,
        repeat(choice($.preproc_conditional_option_members, ',', $.option_member)),
      ),
```

Extend `_option_members_branch` so that an arm may end in `,` and hold blank slots:
`seq(repeat(','), optional(seq($.option_member, repeat(seq(',', optional($.option_member))))))`,
with at least one token. Keep the existing two alternatives' trees unchanged. The existing
option fixtures must not move.

- [ ] **Step 3: Generate, regenerate trees, check by hand, whole suite**

Repeat Task 3 Steps 4-6. In addition:
- every TableRelation preservation case is byte-identical to its source fixture's tree;
- the CalcFormula arms are `aggregate_formula`.

- [ ] **Step 4: Oracle and classification**

Run the quick tier. Classify as in Tasks 4 and 5.

The `OptionMembers` "selects nothing" configuration passes, with `list-value-empty`. Add the
option cases to `test_b11_groundwork.py`:

```python
OPT_RUN = b"""table 50100 T { fields { field(1; F; Option) {
    OptionMembers =
#if X
        A,
#endif
#if Y
        B
#endif
    ;
} } }
"""


def test_option_entire_run_every_config(al_parser):
    v = witness.verdicts(al_parser, OPT_RUN)
    assert all(s == "pass" for s, _ in v.values()), v
```

- [ ] **Step 5: Commit**

```bash
git add grammar.js src/parser.c src/grammar.json src/node-types.json test/corpus/property_value_run_test.txt \
        tools/config_oracle/fixture-classes.tsv tools/config_oracle/tests/test_b11_groundwork.py
git commit -m "feat(b11): Namespaces, TableRelation, CalcFormula value runs; entirely conditional OptionMembers

STATE_COUNT <before> -> <after>.

[BC.History: <measured>]"
```

---

### Task 7: fixture completion, the B13 gap file, incremental parse

**Files:**
- Create: `test/corpus/property_value_run_b13_gap_test.txt`
- Modify: `tools/deliberate-negatives.txt`, `tools/config_oracle/fixture-classes.tsv`, `test/corpus/property_value_run_test.txt`
- Create: `tools/config_oracle/tests/test_value_run_incremental.py`

**Interfaces:**
- Consumes: the `_edit` helper of `tools/config_oracle/tests/test_link_incremental.py`.

- [ ] **Step 1: The B13 gap file**

Every step 5 probe (Task 1, `b13-*.al`) goes in as a case titled
`B13 gap: <shape> -- valid AL, structure deferred (roadmap B13)`. Its expected tree is today's
ERROR tree. Add the basename to `tools/deliberate-negatives.txt` with the comment:

```text
# B11: valid AL whose run-of-#if structure is deferred to roadmap B13 (spec §3.1 step 5).
# Not invalid input. Cases leave this file as B13 gives them structure.
property_value_run_b13_gap_test.txt
```

Classify their oracle records `debt(B13)`, one per configuration, with the exact first item,
for example `cannot-validate:multi-config-parse:…`:

```text
property_value_run_b13_gap_test.txt#<case>#0	*	cannot-validate:multi-config-parse	debt(B13): a run that concatenates generic or pair-list values across groups (spec §3.1 step 5)
```

- [ ] **Step 2: Remaining positive cases**

Add every spec §5.1 and §5.2 shape not yet in `property_value_run_test.txt`:
- the bare-`;` arms as negatives in their own negative fixture, if alc rejects them, per Task
  1's verdicts;
- the all-empty optional sites;
- the action-area and assembly hosts for Namespaces;
- a following procedure after a run;
- nested-run cases at arm sites (an arm whose core is a nested sequence).

Prove the file can fail (`bogus:`). The suite total must equal T0 + every case added by
Tasks 3-7.

- [ ] **Step 3: Incremental parse**

```python
"""B11: incremental re-parse after an edit equals a fresh parse (spec §5.4)."""
import pytest

from tools.config_oracle.tests.test_link_incremental import _edit

HOST = b"page 50100 P { layout { area(Content) { field(F; X) {\n%s\n} } } }\n"
ONE = b"Caption =\n#if X\n 'a';\n#else\n 'b';\n#endif"
TWO = b"Caption =\n#if X\n 'a';\n#endif\n#if not X\n 'b';\n#endif"
TWO_SEMI = TWO + b"\n;"
AFTER_ML = b"CaptionML =\n#if X\n ENU='a'\n#endif\n#if not X\n ENU='b'\n#endif\n;"
INSIDE_ML = b"CaptionML =\n#if X\n ENU='a';\n#endif\n#if not X\n ENU='b';\n#endif"
EMPTY = b"Caption =\n#if X\n#endif\n 'a';"
FLAT = b"Caption = 'a';"

EDITS = [(ONE, TWO), (TWO, ONE), (TWO, TWO_SEMI), (TWO_SEMI, TWO), (INSIDE_ML, AFTER_ML),
         (AFTER_ML, INSIDE_ML), (FLAT, EMPTY), (EMPTY, FLAT), (ONE, ONE.replace(b"#else", b"#elif Y"))]


@pytest.mark.parametrize("before,after", EDITS)
def test_incremental_equals_fresh(al_parser, before, after):
    old_src, new_src = HOST % before, HOST % after
    incremental = _edit(al_parser, old_src, new_src)
    fresh = al_parser.parse(new_src)
    assert str(incremental.root_node) == str(fresh.root_node)
    assert incremental.root_node.has_error == fresh.root_node.has_error
```

Run: `./tools/ts-lock.sh python -m pytest tools/config_oracle/tests/test_value_run_incremental.py -q`
Expected: all pass.

- [ ] **Step 4: Gates and commit**

```bash
./tools/ts-lock.sh tree-sitter test > "$SCRATCH/t7.log" 2>&1; grep -c "✓" "$SCRATCH/t7.log"; grep -c "✗" "$SCRATCH/t7.log"
python tools/has_error_sweep.py --corpus-fixtures; echo "exit=$?"
python -m tools.config_oracle run --tier quick 2>&1 | grep -E "unclassified:|stale|exit code"
git diff --stat test/corpus
git add test/corpus tools/deliberate-negatives.txt tools/config_oracle
git commit -m "test(b11): fixture completion, B13 gap file, incremental parse

[BC.History: <measured>]"
```

**Expected:** 0 failing, sweep exit 0 (the positive file strict), quick tier exit 0.

---

### Task 8: zero-delta gates over four corpora, precedence audit

**Files:** none changed, unless a gate fails. A gate failure is a STOP and a report, not a
grammar edit inside this task.

- [ ] **Step 1: Full-tree zero delta**

```bash
./tools/ts-lock.sh ./tools/tree-harness.sh verify ./BC.History .snapshots/baseline-b11-bc
./tools/ts-lock.sh ./tools/tree-harness.sh verify ./DC .snapshots/baseline-b11-dc
./tools/ts-lock.sh ./tools/tree-harness.sh verify H:/Git/BC28.1 .snapshots/baseline-b11-bc28
./tools/ts-lock.sh ./tools/tree-harness.sh verify H:/Git/BCApps-29.0 .snapshots/baseline-b11-bcapps
```

Expected: `VERIFIED -- all N parse trees byte-identical` in all four (spec §2.3: production has
no target shape).

- [ ] **Step 2: relation_census and has_error**

```bash
./tools/ts-lock.sh python tools/relation_census.py delta --lib-a "$SCRATCH/al_base11.dll" --root ./BC.History --root ./DC --root H:/Git/BC28.1 --root H:/Git/BCApps-29.0 --expect-no-rows
for r in ./BC.History/ ./DC/ H:/Git/BC28.1/ H:/Git/BCApps-29.0/; do python tools/has_error_sweep.py --root "$r"; echo "exit=$?"; done
```

Check the exact `relation_census.py delta` flags with `--help` first. Expected: 0 rows and 0
findings; every sweep exit 0.

- [ ] **Step 3: Precedence audit (spec §4.4)**

For every `prec`, `prec.dynamic` and declared conflict touched or added since Task 1
(`git diff <task1-commit> -- grammar.js`), record in `$SCRATCH/b11-precedence-audit.md`:
- the rule;
- the readings it decides between;
- the fixture case that proves each reading survives.

A precedence with no witness fixture gets one added, in a follow-up commit, before Task 9.

- [ ] **Step 4: Oracle full tier**

```bash
./tools/ts-lock.sh python -m tools.config_oracle run --tier full --root ./BC.History --root ./DC --root H:/Git/BC28.1 --root H:/Git/BCApps-29.0
```

Expected: exit 0 (about 22 min). Run it in the background and poll the output file, not with
`tail -f`.

---

### Task 9: performance, WASM, queries, docs, final validation

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `docs/deferred-work.md`
- Modify: `docs/superpowers/plans/2026-09-28-roadmap-remaining-work.md`
- Modify: `CLAUDE.md`
- Modify: `.claude/rules/scanner.md` (only if a scanner token's description changes; it should not)
- Modify: `queries/*.scm` (only where Step 2 finds a gap)
- Modify: `tree-sitter-al.wasm`, `tree-sitter-al.wasm.inputs.sha256`
- Modify: `tools/query_coverage/baseline.json`

- [ ] **Step 1: Performance**

```bash
./tools/ts-lock.sh tree-sitter build -o "$SCRATCH/al_b11.dll"
python -m tools.perf ab --lib-a "$SCRATCH/al_base11.dll" --lib-b "$SCRATCH/al_b11.dll" --corpus dc
```

Record the ratio and CI for the CHANGELOG. A slowdown beyond 5% is reported, not blocked.

- [ ] **Step 2: Queries**

Run `grep -n "preproc_conditional_property_value" queries/*.scm`. For each hit, decide whether
the sequence needs the same capture. Folds and textobjects over a whole value want it. Add the
`preproc_conditional_property_value_sequence` pattern, and check it with
`./tools/ts-lock.sh tree-sitter query queries/<f>.scm <fixture-src>`.

- [ ] **Step 3: Docs**

**CHANGELOG `### Changed`.** Add a new entry:
- the new node type, `preproc_conditional_property_value_sequence`, and its fields;
- the intended corrections of spec §3.4: the generic empty prefix; the ML, Namespaces and
  Implementation splits; item 35;
- that a sequence is a one-reading construct (B12);
- the B13 gap;
- STATE_COUNT before and after;
- the perf ratio;
- "previously correct production trees byte-identical in all four corpora".

**`docs/deferred-work.md`:**
- item 33 RESOLVED, and item 35 RESOLVED (both with the commit hashes); item 35's quoted and
  unquoted measurements recorded;
- new items:
  - B12, configuration-dependent property boundaries, with the boundary probes and fixtures,
    the classified records, and the alternatives considered (condition text in the scanner; a
    multi-configuration tree);
  - B13, conditional value fragments, with the b13 probes and the gap file.

**Roadmap.** Rows B11 (DONE with summary), B12 and B13.

**CLAUDE.md.** In the property-handling section, a paragraph on value runs: the five routing
steps, the sequence node, the decorations, and the B12/B13 boundaries. Keep it to the facts a
grammar editor needs.

- [ ] **Step 4: Final validation, qc, WASM**

```bash
./validate-grammar.sh --full > "$SCRATCH/b11-validate.log" 2>&1; echo "EXIT=$?"; grep -E "✗|✓" "$SCRATCH/b11-validate.log" | tail -30
python -m tools.query_coverage.qc run 2>&1 | tail -3
```

Expected:
- every step ✓, except `Committed wasm is stale`;
- qc: any new cluster is a hidden-rule field skip of the new generator rules (the B4, B5, B5b
  and B8 class). Justify it in the commit message, then `qc accept`. Any other cluster is a
  STOP.

```bash
git add CHANGELOG.md docs CLAUDE.md queries tools/query_coverage/baseline.json
git commit -m "docs: B11 done -- property value runs; items 33 and 35 resolved; B12 and B13 recorded

[BC.History: <measured>]"
./tools/ts-lock.sh tree-sitter build --wasm -o tree-sitter-al.wasm
tools/check-wasm-fresh.sh --update
tools/check-wasm-fresh.sh
git add tree-sitter-al.wasm tree-sitter-al.wasm.inputs.sha256
git commit -m "build: rebuild tree-sitter-al.wasm for B11

[BC.History: <measured>]"
rm -rf .snapshots/baseline-b11-*
```
