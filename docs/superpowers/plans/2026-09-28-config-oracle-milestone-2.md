# Config Oracle Milestone 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The oracle lowers every frequent production conditional and the base spec's hard shapes, declares a reading for one-reading rules, and runs over production for the first time with every finding triaged.

**Architecture:** Extend the existing lowering engine (`tools/config_oracle/lowering/`) instead of adding a new layer. Branch-select entries gain declared `arm` content. A `list-run` policy and a `reading` attribute are added. Fragments that bind to a *neighbouring* sibling become a `ToPrevious` fragment class, consumed where it is lowered. The hard shapes are assemblers in `assemblers.py`, plus one new module, `lowering/expression.py`, for precedence-correct recomposition.

**Tech Stack:** Python 3.12+, py-tree-sitter via `tools/query_coverage/loader.py`, pytest, and the repo's `tree-sitter` CLI through `./tools/ts-lock.sh`.

**Spec:** `docs/superpowers/specs/2026-09-28-config-oracle-milestone-2-design.md`, which amends `docs/superpowers/specs/2026-09-27-config-consistency-oracle-design.md` (the base spec). Read both.

## Global Constraints

- Shell: Git Bash on Windows. Use Windows paths where a tool needs them (`cygpath -w`). Never write `2>nul`.
- Run every `tree-sitter` command through `./tools/ts-lock.sh` (one shared `al.dll`).
- Run tests with `python -m pytest tools/config_oracle/tests -q` from the repo root. `slow` tests run only with `-m slow`.
- Registry rule (base §3): hand-written and authoritative. `node-types.json` is a census input, never the source of an expectation. **There is no default handler.**
- Every handler returns accounting for every leaf. `Accounting.check_complete` and `check_emitted` must hold.
- Every contract that rewrites a parent/field edge **names** the rewrite in its docstring. Any other edge change is an error.
- Lowering never reparses source and never imports `reference.py`, `tree_sitter` or the loader (`tests/test_isolation.py`).
- Precedence comes from `test/corpus/operator_precedence_test.txt`'s header, never from `grammar.js` `prec()` values.
- A handler tested only on inactive content has not been tested (base §5).
- Commit per task. Oracle-only commits need no BC.History trailer. Grammar fixes found in Task 18 follow CLAUDE.md: fixture, alc probe, tree-harness, and `[BC.History: N errors, X% success]`.
- `tools/config_oracle/**/*.py` is tracked despite the blanket `*.py` ignore. New `.py` files there need no `.gitignore` change. Check with `git status`.

## Review Focus

1. **A conditional whose arm is empty in the selected configuration.** The host must lose nothing and gain nothing, and `EMPTY_REMOVABLE` must not hide a real loss. Pinned in Task 4 (`test_empty_arm_*`).
2. **Nested conditionals of the same type** (fields inside fields, keys inside keys). The engine's recursion must select the inner arm under the outer. Pinned in Task 5 (`test_nested_fields_and_keys_every_config`).
3. **A list-run arm that begins with a separator** (`A #if X , B #endif`) against one that ends with one (`A, #if X B, #endif C`). Both placements pass, per deferred-work item 2. Pinned in Task 7 (`test_both_comma_placements`).
4. **An expression continuation whose operand is itself a binary expression** (`1 #if X * 2 + 3 #endif`). Recomposition must regroup across the operand boundary. Pinned in Task 11 (`test_operand_is_regrouped`).
5. **A one-reading type in a configuration that looks lowerable.** It must report `lowering:one-reading`, never `pass`. Pinned in Task 9 (`test_one_reading_is_never_a_pass`).

---

### Task 1: The BOM is trivia at any offset

**Files:**
- Modify: `tools/config_oracle/compare.py` (function `coverage`, around lines 40-65)
- Test: `tools/config_oracle/tests/test_compare.py`

**Interfaces:**
- Consumes: `compare.coverage(source, active, root, extras, side) -> list[Discrepancy]` (unchanged signature)
- Produces: the same function, which ignores every U+FEFF byte triple (`EF BB BF`) for the `uncovered` check

- [ ] **Step 1: Write the failing test**

Append to `tools/config_oracle/tests/test_compare.py`:

```python
def test_mid_file_bom_is_trivia_not_uncovered():
    # A BOM between two tokens: grammar.js declares U+FEFF an extra, so neither
    # tree covers it, and it must not be reported (milestone-1 follow-up 1).
    src = b"ab\xef\xbb\xbfcd"
    root = node("r", leaf("x", 0, 2, named=True), leaf("y", 5, 7, named=True))
    active = bytearray([1]) * len(src)
    assert compare.coverage(src, active, root, [], "low") == []


def test_leading_bom_still_trivia():
    src = b"\xef\xbb\xbfab"
    root = node("r", leaf("x", 3, 5, named=True))
    active = bytearray([1]) * len(src)
    assert compare.coverage(src, active, root, [], "low") == []
```

If `leaf`/`node` are not already imported in that file, add `from tools.config_oracle.tests.conftest import leaf, node`.

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tools/config_oracle/tests/test_compare.py -q -k bom`
Expected: `test_mid_file_bom_is_trivia_not_uncovered` FAILS with an `uncovered` discrepancy at `low@2`.

- [ ] **Step 3: Implement**

In `coverage`, replace the `lead = ...` line and the `significant = ...` line:

```python
    bom = set()
    at = source.find(_BOM)
    while at != -1:
        bom.update(range(at, at + len(_BOM)))
        at = source.find(_BOM, at + len(_BOM))
```

```python
        significant = active[k] and b not in _WS and k not in bom
```

- [ ] **Step 4: Verify**

Run: `python -m pytest tools/config_oracle/tests -q`
Expected: all pass.

Run: `python -m tools.config_oracle run --tier quick 2>&1 | grep -E "discrepancy|pass:"`
Expected: `- discrepancy: 0`. It was 1, from `scanner_single_read_dispatch_test.txt#3`.

- [ ] **Step 5: Commit**

```bash
git add tools/config_oracle/compare.py tools/config_oracle/tests/test_compare.py
git commit -m "fix(oracle): a BOM is trivia at any offset, not only the first"
```

---

### Task 2: A witness helper and `run --tier full`

**Files:**
- Create: `tools/config_oracle/tests/witness.py`
- Modify: `tools/config_oracle/__main__.py` (argument parser, and the `_run` corpus branch)
- Test: `tools/config_oracle/tests/test_witness.py`, `tools/config_oracle/tests/test_runner.py`

**Interfaces:**
- Consumes: `runner.check_input(parser, input_id, source, mode="full") -> list[Record]`, where each `Record` has `.config`, `.status` and `.items`
- Produces:
  - `witness.verdicts(parser, src) -> dict[str, tuple[str, list[str]]]` (config → (status, items))
  - `witness.assert_all_pass(parser, src)`
  - `witness.assert_produces(parser, src, kind)`
  - `witness.statuses_with(parser, src, prefix) -> list[str]`, the configs whose items include one starting with `prefix`
  - CLI `run --tier full --root DIR...`

- [ ] **Step 1: Write the helper**

```python
"""Witness helpers: run the whole oracle over one AL source in every configuration."""
from __future__ import annotations

from tools.config_oracle import runner


def verdicts(parser, src, input_id="witness"):
    return {r.config: (r.status, list(r.items)) for r in runner.check_input(parser, input_id, src)}


def assert_all_pass(parser, src):
    v = verdicts(parser, src)
    bad = {c: s for c, s in v.items() if s[0] != "pass"}
    assert v, "no configuration was checked"
    assert not bad, bad


def statuses_with(parser, src, prefix):
    return sorted(c for c, (_, items) in verdicts(parser, src).items()
                  if any(i.startswith(prefix) for i in items))


def assert_produces(parser, src, kind):
    """The witness must actually produce the special type it claims to test (base §5)."""
    stack = [parser.parse(src).root_node]
    while stack:
        n = stack.pop()
        if n.type == kind:
            return
        stack.extend(n.children)
    raise AssertionError(f"source does not produce {kind}")
```

- [ ] **Step 2: Write the failing tests**

`tools/config_oracle/tests/test_witness.py`:

```python
from tools.config_oracle.tests import witness

SRC = b"codeunit 1 T\n{\n    trigger OnRun()\n    begin\n#if A\n        x := 1;\n#endif\n    end;\n}\n"


def test_assert_all_pass_on_a_supported_shape(al_parser):
    witness.assert_produces(al_parser, SRC, "preproc_conditional_statement")
    witness.assert_all_pass(al_parser, SRC)
```

Append to `tools/config_oracle/tests/test_runner.py`:

```python
def test_cli_full_tier_over_a_root(tmp_path):
    from tools.config_oracle.__main__ import main
    (tmp_path / "a.al").write_bytes(b"codeunit 1 T\n{\n    trigger OnRun()\n    begin\n#if A\n        x := 1;\n#endif\n    end;\n}\n")
    rc = main(["run", "--tier", "full", "--root", str(tmp_path), "--workers", "1",
               "--report", str(tmp_path / "rep")])
    assert rc == 0
    assert "pass: 2" in (tmp_path / "rep" / "summary.md").read_text(encoding="utf-8")
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `python -m pytest tools/config_oracle/tests/test_runner.py -q -k full_tier`
Expected: FAIL. argparse rejects `full`.

- [ ] **Step 4: Implement the CLI**

In `__main__.py`:
- change `choices=["quick", "resolve"]` to `choices=["quick", "resolve", "full"]`;
- in `_run`, change the `else:` corpus branch to set `mode = args.tier` (so `resolve` stays `resolve` and `full` gives `full`);
- change the error message to `f"--tier {args.tier} needs at least one --root"`;
- update the module docstring's usage line to `run --tier quick|resolve|full`.

- [ ] **Step 5: Verify**

Run: `python -m pytest tools/config_oracle/tests -q`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add tools/config_oracle/tests/witness.py tools/config_oracle/tests/test_witness.py tools/config_oracle/__main__.py tools/config_oracle/tests/test_runner.py
git commit -m "feat(oracle): witness helpers and run --tier full over corpus roots"
```

---

### Task 3: Registry attributes `arm` and `reading`, the arm-content check, and resolver group lookup

**Files:**
- Modify: `tools/config_oracle/contracts.py` (`Entry`, `register`, `census`, and the comments on the BC 29 registrations)
- Modify: `tools/config_oracle/lowering/select.py` (`branch_select`)
- Modify: `tools/config_oracle/directives.py` (`Resolution`, `resolve`)
- Test: `tools/config_oracle/tests/test_contracts.py`, `tools/config_oracle/tests/test_lowering_select.py`, `tools/config_oracle/tests/test_resolve.py`

**Interfaces:**
- Produces:
  - `Entry.arm: frozenset | None`, the child kinds an arm may contain
  - `Entry.reading: str | None`, one of `"arm:if"`, `"arm:else"`, `"arm:inactive"` or `"arm:not-else-led"`
  - `register(type_, kind, handler=None, hosts=None, alias_to=None, arm=None, reading=None)`
  - `contracts.ARM_EXEMPT: frozenset`, the milestone-1 branch-select entries that predate `arm`
  - `LoweringError("arm-content", ...)` from `branch_select` for an undeclared child kind
  - `Resolution.group_of: dict[int, int]`, which maps every `#elif`/`#else`/`#endif` directive offset to its `#if` offset
  - `select.reading_active(node, entry, ctx) -> bool`, the shared test later handlers use

- [ ] **Step 1: Write the failing tests**

Append to `test_contracts.py`:

```python
def test_branch_select_entries_declare_arm_unless_exempt():
    for e in contracts.REGISTRY.values():
        if e.kind == "branch-select" and e.type not in contracts.ARM_EXEMPT:
            assert e.arm, f"{e.type} has no declared arm content"


def test_census_rejects_an_arm_kind_that_does_not_exist():
    contracts.REGISTRY["preproc_conditional_rendering"] = contracts.Entry(
        "preproc_conditional_rendering", "branch-select", "tools.config_oracle.lowering.select.branch_select",
        {}, None, frozenset({"no_such_kind"}), None)
    try:
        assert any("arm kind" in p for p in contracts.census(node_types()))
    finally:
        contracts.REGISTRY.pop("preproc_conditional_rendering")
        contracts.register("preproc_conditional_rendering", "unsupported")
```

This test is rewritten in Task 4, once rendering is registered for real. Its `finally` then restores that registration instead.

Append to `test_resolve.py`:

```python
def test_group_of_maps_every_later_directive_to_its_if():
    src = b"#if A\nx\n#elif B\ny\n#else\nz\n#endif\n"
    res = resolve(src, frozenset())
    if_at = src.index(b"#if")
    for d in (b"#elif", b"#else", b"#endif"):
        assert res.group_of[src.index(d)] == if_at
```

Append to `test_lowering_select.py`:

```python
def test_arm_content_outside_the_declaration_is_an_error(al_parser, monkeypatch):
    from tools.config_oracle import contracts
    e = contracts.REGISTRY["preproc_conditional_statement"]
    monkeypatch.setitem(contracts.REGISTRY, "preproc_conditional_statement",
                        contracts.Entry(e.type, e.kind, e.handler, e.hosts, e.alias_to,
                                        frozenset({"no_such_kind"}), None))
    root, extras, _ = ir.from_tree(al_parser.parse(STMT))
    res = resolve(STMT, frozenset({"A"}))
    with pytest.raises(LoweringError) as err:
        lower_tree(root, extras, res)
    assert err.value.kind == "arm-content"
```

- [ ] **Step 2: Run them to verify they fail**

Run: `python -m pytest tools/config_oracle/tests -q -k "arm or group_of"`
Expected: FAIL. `Entry` has no `arm`, and `Resolution` has no `group_of`.

- [ ] **Step 3: Implement the registry**

In `contracts.py`:

```python
@dataclass(frozen=True)
class Entry:
    type: str
    kind: str
    handler: str | None = None
    hosts: dict = field(default_factory=dict)
    alias_to: str | None = None
    arm: frozenset | None = None
    reading: str | None = None


READINGS = frozenset({"arm:if", "arm:else", "arm:inactive", "arm:not-else-led"})

# Registered in milestone 1, before `arm` existed. Their arms admit a whole
# statement or body-element set; declaring it would restate _statement and
# _body_element. Milestone 3 decides whether to.
ARM_EXEMPT = frozenset({"preproc_conditional", "preproc_conditional_statement",
                        "preproc_conditional_var_block", "preproc_pragma_only"})


def register(type_, kind, handler=None, hosts=None, alias_to=None, arm=None, reading=None):
    if type_ in REGISTRY:
        raise ValueError(f"duplicate registry entry: {type_}")
    if kind == "token-alias" and not alias_to:
        raise ValueError(f"token-alias entry without alias_to: {type_}")
    if reading is not None and reading not in READINGS:
        raise ValueError(f"unknown reading {reading!r} for {type_}")
    REGISTRY[type_] = Entry(type_, kind, handler, dict(hosts or {}), alias_to,
                            frozenset(arm) if arm else None, reading)
```

In `census`, before `return problems`:

```python
    known = {t["type"] for t in node_types}
    for e in REGISTRY.values():
        for k in sorted(e.arm or ()):
            if k not in known:
                problems.append(f"arm kind does not exist: {k} in {e.type}")
```

Anonymous tokens such as `,` and `;` appear in `node-types.json` as `{"type": ",", "named": false}`, so they count as known.

On each BC 29 registration made on 2026-09-28, add a one-line comment naming its milestone, as the spec's "Registry state at exit" assigns them:
- milestone 2 (this plan): `preproc_conditional_arguments`, `preproc_split_container_reopen`, `preproc_split_block_end_in_else`, `preproc_split_block_close_after_endif`, and `preproc_split_open_statement`'s `else`-led arms;
- milestone 3: every other one.

- [ ] **Step 4: Implement the resolver group map**

In `directives.py`, add `group_of: dict = field(default_factory=dict)` to `Resolution`. In `resolve`, in the `else:` branch after `f = stack[-1]` (before the `if d.kind == "elif"`), add:

```python
                res.group_of[d.hash] = f.if_hash
```

This line runs for every directive handled by that branch, active or not, so `group_of` covers masked groups too.

- [ ] **Step 5: Implement the arm check and `reading_active` in `select.py`**

In `branch_select`, inside the `if directive.start == choice:` loop, before lowering each `c`:

```python
                if entry.arm is not None and c.kind not in entry.arm:
                    raise LoweringError("arm-content", c, f"{c.kind} not declared for {node.kind}")
```

Add at module level:

```python
def reading_active(node, entry, ctx):
    """True when the resolved configuration is the one the tree shows (spec P4)."""
    arms, _ = split_arms(node)
    choice = chosen_arm(node, arms, ctx)
    first = arms[0][0].start
    if entry.reading == "arm:if":
        return choice == first
    if entry.reading == "arm:else":
        return choice is not None and choice != first and arms[-1][0].kind == "preproc_else" \
            and choice == arms[-1][0].start
    if entry.reading == "arm:inactive":
        return choice is None
    raise LoweringError("contract-shape", node, f"reading {entry.reading!r} needs its own test")
```

- [ ] **Step 6: Verify**

Run: `python -m pytest tools/config_oracle/tests -q`
Expected: all pass.

Run: `python -c "import json; from tools.config_oracle import contracts as c; print(c.census(json.load(open('src/node-types.json'))))"`
Expected: `[]`.

- [ ] **Step 7: Commit**

```bash
git add tools/config_oracle/contracts.py tools/config_oracle/lowering/select.py tools/config_oracle/directives.py tools/config_oracle/tests/
git commit -m "feat(oracle): arm and reading registry attributes, arm-content check, resolver group map"
```

---

### Task 4: Branch-select, part A: object, actions, layout, layout_mixed, report, rendering, dataset

**Files:**
- Modify: `tools/config_oracle/contracts.py`
- Create: `tools/config_oracle/tests/test_branch_families.py`

**Interfaces:**
- Consumes: `register(..., arm=...)`, `witness.*`, `select.branch_select`
- Produces: `test_branch_families.P2_WITNESSES: dict[str, list[bytes]]`, which Tasks 5 and 6 extend

**How to derive each entry.** Read the rule in `grammar.js` (`grep -n "^    <type>: " grammar.js`) and list the kinds an arm may hold. Expand hidden choices such as `_action_element` and `_layout_element` into their visible members, in the same way `host_slots` expands supertypes. Then run the census. It prints `host slot not classified: <type> in <slot>` for each real host. Classify every one as `splice-repeat`, because every one is a repeat slot. Confirm that by reading the host rule; do not assume it.

- [ ] **Step 1: Write the witnesses and tests**

`tools/config_oracle/tests/test_branch_families.py`:

```python
"""P2 witness matrix: every branch-select family, every configuration (spec P2, base §5)."""
import pytest

from tools.config_oracle import contracts
from tools.config_oracle.tests import witness

P2_WITNESSES = {
    "preproc_conditional_object": [
        # first arm, #elif, #else, no arm (A and B both undefined -> #else)
        b"#if A\ncodeunit 1 X { }\n#elif B\ncodeunit 2 Y { }\n#else\ncodeunit 3 Z { }\n#endif\ncodeunit 4 W { }\n",
        # namespace + using inside the arms, identical content in two arms
        b"#if A\nnamespace N.A;\n#else\nnamespace N.A;\n#endif\nusing System;\ncodeunit 1 X { }\n",
    ],
    "preproc_conditional_actions": [
        b"page 1 P\n{\n    actions\n    {\n        area(Processing)\n        {\n#if A\n            action(X) { }\n#else\n            action(Y) { }\n            action(Z) { }\n#endif\n        }\n    }\n}\n",
    ],
    "preproc_conditional_layout": [
        b"page 1 P\n{\n    layout\n    {\n        area(Content)\n        {\n#if A\n            field(X; Rec.X) { }\n#endif\n            field(Y; Rec.Y) { }\n        }\n    }\n}\n",
    ],
    "preproc_conditional_layout_mixed": [
        b"page 1 P\n{\n    layout\n    {\n        area(Content)\n        {\n            group(G)\n            {\n#if A\n                Caption = 'a';\n                field(X; Rec.X) { }\n#endif\n            }\n        }\n    }\n}\n",
    ],
    "preproc_conditional_report": [
        b"report 1 R\n{\n    dataset\n    {\n        dataitem(D; Integer)\n        {\n#if A\n            column(C1; 1) { }\n#else\n            column(C2; 2) { }\n#endif\n        }\n    }\n}\n",
    ],
    "preproc_conditional_rendering": [
        b"report 1 R\n{\n    rendering\n    {\n#if A\n        layout(L1) { Type = RDLC; }\n#endif\n        layout(L2) { Type = Word; }\n    }\n}\n",
    ],
    "preproc_conditional_dataset": [
        b"report 1 R\n{\n    dataset\n    {\n#if A\n        dataitem(D; Integer) { }\n#else\n#endif\n    }\n}\n",
    ],
}

# A witness whose arm is EMPTY in some configuration (Review Focus 1).
EMPTY_ARM = {
    "preproc_conditional_dataset": P2_WITNESSES["preproc_conditional_dataset"][0],
}


def _cases():
    return [(t, s) for t, srcs in P2_WITNESSES.items() for s in srcs]


@pytest.mark.parametrize("kind,src", _cases())
def test_witness_produces_its_type(al_parser, kind, src):
    witness.assert_produces(al_parser, src, kind)


@pytest.mark.parametrize("kind,src", _cases())
def test_every_configuration_passes(al_parser, kind, src):
    witness.assert_all_pass(al_parser, src)


@pytest.mark.parametrize("kind,src", _cases())
def test_policy_swap_trips_policy(al_parser, monkeypatch, kind, src):
    e = contracts.REGISTRY[kind]
    monkeypatch.setitem(contracts.REGISTRY, kind, contracts.Entry(
        e.type, e.kind, e.handler, {h: "single-slot" for h in e.hosts}, e.alias_to, e.arm, e.reading))
    assert witness.statuses_with(al_parser, src, "lowering:policy"), "the mutation tripped nothing"


@pytest.mark.parametrize("kind,src", list(EMPTY_ARM.items()))
def test_empty_arm_loses_and_gains_nothing(al_parser, kind, src):
    witness.assert_all_pass(al_parser, src)
```

The policy-swap mutation needs a configuration that selects at least two nodes, or two nodes' worth of content. If a witness selects a single node in every configuration, `single-slot` accepts it, the mutation trips nothing, and this test catches that. Add a second element to that witness's arm.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tools/config_oracle/tests/test_branch_families.py -q`
Expected: `test_every_configuration_passes` FAILS with `lowering:unsupported-type` for every type. If any `test_witness_produces_its_type` fails, fix the witness source until it produces its type. Record the change in the commit message.

- [ ] **Step 3: Register the seven types**

In `contracts.py`, remove the seven types from the `unsupported` loop and register each one. Example for actions; the arm set shown is what `_action_element` expands to at HEAD, so verify it against `grammar.js`:

```python
register("preproc_conditional_actions", "branch-select", "tools.config_oracle.lowering.select.branch_select",
         hosts={"action_body:<children>": "splice-repeat"},
         arm={"action_area_section", "action_group_section", "action_declaration", "separator_action",
              "actionref_declaration", "systemaction_declaration", "fileuploadaction_declaration",
              "customaction_declaration", "property", "trigger_declaration", "attribute_item",
              "addfirst_action_modification", "addlast_action_modification",
              "addafter_action_modification", "addbefore_action_modification",
              "modify_action_modification", "preproc_split_modify", "movefirst_modification",
              "movelast_modification", "moveafter_modification", "movebefore_modification",
              "preproc_conditional_actions"})
```

Write the other six the same way. Take each arm set from its rule, and each host set from the census output.

- [ ] **Step 4: Verify**

Run: `python -m pytest tools/config_oracle/tests -q`
Expected: all pass, and the census test is clean.

Rewrite `test_census_rejects_an_arm_kind_that_does_not_exist` (Task 3) so its `finally` restores the real rendering entry instead of the `unsupported` one. Simplest: save `old = contracts.REGISTRY["preproc_conditional_rendering"]` first and put it back afterwards.

Run: `python -m tools.config_oracle run --tier quick 2>&1 | grep -E "discrepancy|pass:"`
Expected: `discrepancy: 0`. Record the new `pass` count in the commit message. It must be higher than before the task.

- [ ] **Step 5: Commit**

```bash
git add tools/config_oracle/contracts.py tools/config_oracle/tests/
git commit -m "feat(oracle): branch-select for object, actions, layout, layout_mixed, report, rendering, dataset"
```

---

### Task 5: Branch-select, part B: fields, keys, fieldgroups, var

**Files:**
- Modify: `tools/config_oracle/contracts.py`
- Modify: `tools/config_oracle/tests/test_branch_families.py`

**Interfaces:**
- Consumes: `P2_WITNESSES`, from Task 4

- [ ] **Step 1: Add the witnesses**

Add these entries to `P2_WITNESSES`:

```python
    "preproc_conditional_fields": [
        # nested #if among fields (BC 29 family C), #else with a different field
        b"table 1 T\n{\n    fields\n    {\n        field(1; A; Integer) { }\n#if A\n#if B\n        field(2; B; Integer) { }\n#endif\n        field(3; C; Integer) { }\n#else\n        field(4; D; Integer) { }\n#endif\n    }\n}\n",
    ],
    "preproc_conditional_keys": [
        b"table 1 T\n{\n    fields { field(1; A; Integer) { } field(2; B; Integer) { } }\n    keys\n    {\n        key(PK; A) { }\n#if A\n#if B\n        key(K1; B) { }\n#endif\n        key(K2; A, B) { }\n#endif\n    }\n}\n",
    ],
    "preproc_conditional_fieldgroups": [
        b"table 1 T\n{\n    fields { field(1; A; Integer) { } }\n    fieldgroups\n    {\n#if A\n        fieldgroup(DropDown; A) { }\n#else\n        fieldgroup(Brick; A) { }\n#endif\n    }\n}\n",
    ],
    "preproc_conditional_var": [
        b"codeunit 1 T\n{\n    var\n        X: Integer;\n#if A\n        Y: Integer;\n#else\n        Z: Integer;\n#endif\n\n    procedure P()\n    var\n        L: Integer;\n#if B\n        M: Integer;\n#endif\n    begin\n    end;\n}\n",
    ],
```

Add this test for Review Focus 2:

```python
def test_nested_fields_and_keys_every_config(al_parser):
    for kind in ("preproc_conditional_fields", "preproc_conditional_keys"):
        src = P2_WITNESSES[kind][0]
        v = witness.verdicts(al_parser, src)
        assert set(v) >= {"A=0,B=0", "A=1,B=0", "A=1,B=1"} or len(v) >= 3, v
        witness.assert_all_pass(al_parser, src)
```

The config-name format is whatever `runner` emits: print `witness.verdicts(...)` once and match the assertion to it. The requirement is that the three distinguishable configurations are all checked.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tools/config_oracle/tests/test_branch_families.py -q`
Expected: the four new types fail with `lowering:unsupported-type`.

- [ ] **Step 3: Register the four types**

The arm sets:
- **fields:** `{"field_declaration", "attribute_item", "modify_modification", "preproc_conditional_fields"}` (via `_field_branch_items`).
- **keys:** `{"key_declaration", "attribute_item", "preproc_conditional_keys"}` (via `_key_branch_items`).
- **fieldgroups:** read the rule.
- **var:** `{"variable_declaration", "var_attribute_item"}` (after the item-8 fix, `preproc_conditional_var` admits nothing else).

Hosts come from the census. `preproc_conditional_var` sits in `var_body:<children>`.

Remove `preproc_conditional_var` from the paragraph in `contracts.py` that explains why it is not a body host, and update that comment to say it is now registered here.

- [ ] **Step 4: Verify**

Run: `python -m pytest tools/config_oracle/tests -q`, then `python -m tools.config_oracle run --tier quick 2>&1 | grep -E "discrepancy|pass:"`.
Expected: all pass, and `discrepancy: 0`.

- [ ] **Step 5: Commit**

```bash
git add tools/config_oracle/contracts.py tools/config_oracle/tests/test_branch_families.py
git commit -m "feat(oracle): branch-select for fields, keys, fieldgroups, var"
```

---

### Task 6: Branch-select, part C: case, labels, query, xmlport, controladdin

**Files:**
- Modify: `tools/config_oracle/contracts.py`
- Modify: `tools/config_oracle/tests/test_branch_families.py`

- [ ] **Step 1: Add the witnesses**

```python
    "preproc_conditional_case": [
        b"codeunit 1 T\n{\n    procedure P(i: Integer)\n    begin\n        case i of\n            1:\n                i := 1;\n#if A\n            2:\n                i := 2;\n#endif\n            3:\n                i := 3;\n        end;\n    end;\n}\n",
    ],
    "preproc_conditional_labels": [
        b"report 1 R\n{\n    labels\n    {\n#if A\n        L1 = 'x';\n#endif\n        L2 = 'y';\n    }\n}\n",
    ],
    "preproc_conditional_query": [
        b"query 1 Q\n{\n    elements\n    {\n        dataitem(D; Integer)\n        {\n#if A\n            column(C; Number) { }\n#endif\n        }\n    }\n}\n",
    ],
    "preproc_conditional_xmlport": [
        b"xmlport 1 X\n{\n    schema\n    {\n        textelement(Root)\n        {\n#if A\n            textelement(E1) { }\n#else\n            textelement(E2) { }\n#endif\n        }\n    }\n}\n",
    ],
    "preproc_conditional_controladdin": [
        b"controladdin C\n{\n#if A\n    Scripts = 'a.js';\n#endif\n    RequestedHeight = 1;\n}\n",
    ],
```

These five are rare, and several of their rules have unusual containers. If `test_witness_produces_its_type` fails, find the host by `grep -n "preproc_conditional_<x>" grammar.js` and read the rule that references it. Rewrite the source until the type is produced. Record each rewrite in the commit message.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tools/config_oracle/tests/test_branch_families.py -q`
Expected: the five new types fail with `lowering:unsupported-type`.

- [ ] **Step 3: Register the five types**

Same method as Task 4. `preproc_conditional_case` sits in `case_body:<children>`. Its arm holds `case_branch` and nested `preproc_conditional_case`; read the rule for anything else.

- [ ] **Step 4: Verify**

Run: `python -m pytest tools/config_oracle/tests -q`, then `python -m tools.config_oracle run --tier quick 2>&1 | grep -E "discrepancy|pass:"`.
Expected: all pass, and `discrepancy: 0`.

- [ ] **Step 5: Commit**

```bash
git add tools/config_oracle/contracts.py tools/config_oracle/tests/test_branch_families.py
git commit -m "feat(oracle): branch-select for case, labels, query, xmlport, controladdin"
```

---

### Task 7: The list-run policy and `terminator-hoist`

**Files:**
- Modify: `tools/config_oracle/lowering/select.py` (`branch_select`)
- Modify: `tools/config_oracle/lowering/engine.py` (`_lower_ordinary`, `_consume`)
- Modify: `tools/config_oracle/contracts.py`
- Create: `tools/config_oracle/tests/test_list_run.py`

**Interfaces:**
- Produces:
  - policy `"list-run"`, accepted by `branch_select`
  - `engine.LIST_RUN_TYPES: frozenset` (the list-run special types)
  - `LoweringError("list-separator", ...)`
  - a `Terminator` whose anchor is a list node, which the owning `property` consumes by appending the `;` last

Contract, written into `branch_select`'s docstring:

> **list-run.** The chosen arm's items AND separators splice into the host list in order. A trailing `;` in the arm is not spliced: it becomes a `Terminator` (named rewrite **terminator-hoist**), which passes up through the list and is appended as the last child of the owning `property`. After the host list is built, it must read `item (, item)*`, ignoring bracket tokens (`(`, `)`, `[`, `]`) at its ends. Anything else is `list-separator`.

- [ ] **Step 1: Write the failing tests**

```python
"""P3 list-run witnesses (spec P3)."""
import pytest

from tools.config_oracle.tests import witness

PERMS_TERMINATOR = b"codeunit 50100 T\n{\n    Permissions = tabledata A = R,\n#if X\n                  tabledata B = R;\n#else\n                  tabledata C = R;\n#endif\n\n    trigger OnRun() begin end;\n}\n"
PERMS_INTERNAL = b"codeunit 50100 T\n{\n    Permissions = tabledata A = R,\n#if X\n                  tabledata B = R,\n#endif\n                  tabledata C = R;\n\n    trigger OnRun() begin end;\n}\n"
ARGS_LEAD = b"codeunit 1 T\n{\n    trigger OnRun()\n    begin\n        F(1,\n#if X\n            2,\n#endif\n            3);\n    end;\n}\n"
ARGS_TRAIL = b"codeunit 1 T\n{\n    trigger OnRun()\n    begin\n        F(1\n#if X\n            , 2\n#endif\n            , 3);\n    end;\n}\n"
LIST_ELEMENTS = b"codeunit 1 T\n{\n    trigger OnRun()\n    begin\n        L := [1\n#if X\n            , 2\n#endif\n        ];\n    end;\n}\n"
OPTIONS = b"table 1 T\n{\n    fields\n    {\n        field(1; F; Option)\n        {\n            OptionMembers = A,\n#if X\n            B,\n#endif\n            C;\n        }\n    }\n}\n"
WHERE = b"table 1 T\n{\n    fields\n    {\n        field(1; F; Integer)\n        {\n            FieldClass = FlowField;\n            CalcFormula = count(T where(A = const(1)\n#if X\n                , B = const(2)\n#endif\n                ));\n        }\n    }\n}\n"
LINK = b"page 1 P\n{\n    layout\n    {\n        area(Content)\n        {\n            part(S; Sub)\n            {\n                SubPageLink = A = field(A)\n#if X\n                    , B = field(B)\n#endif\n                    ;\n            }\n        }\n    }\n}\n"

CASES = {
    "preproc_conditional_permissions": [PERMS_TERMINATOR, PERMS_INTERNAL],
    "preproc_conditional_arguments": [ARGS_LEAD, ARGS_TRAIL],
    "preproc_conditional_list_elements": [LIST_ELEMENTS],
    "preproc_conditional_option_members": [OPTIONS],
    "preproc_conditional_where": [WHERE],
    "preproc_conditional_link_values": [LINK],
}


@pytest.mark.parametrize("kind,src", [(k, s) for k, v in CASES.items() for s in v])
def test_list_run_witness(al_parser, kind, src):
    witness.assert_produces(al_parser, src, kind)
    witness.assert_all_pass(al_parser, src)


def test_both_comma_placements(al_parser):
    for src in (ARGS_LEAD, ARGS_TRAIL):
        witness.assert_all_pass(al_parser, src)


def test_dropped_separator_trips_list_separator(al_parser, monkeypatch):
    from tools.config_oracle.lowering import select
    real = select._splice_arm
    def drop_commas(items):
        return [c for c in real(items) if c.kind != ","]
    monkeypatch.setattr(select, "_splice_arm", drop_commas)
    assert witness.statuses_with(al_parser, ARGS_LEAD, "lowering:list-separator")


def test_terminator_left_in_list_trips_structure(al_parser, monkeypatch):
    from tools.config_oracle.lowering import select
    monkeypatch.setattr(select, "HOIST_TERMINATOR", False)
    v = witness.verdicts(al_parser, PERMS_TERMINATOR)
    assert any(s == "discrepancy" and any("structure" in i for i in items) for s, items in v.values()), v
```

If a witness does not produce its type, adjust the source, as in Task 4.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tools/config_oracle/tests/test_list_run.py -q`
Expected: FAIL with `lowering:unsupported-type`, and the mutation tests fail with an `AttributeError`.

- [ ] **Step 3: Implement in `select.py`**

```python
HOIST_TERMINATOR = True   # mutation switch for the terminator-hoist contract test


def _splice_arm(items):
    """The chosen arm's lowered items, in order. A seam for the separator mutation test."""
    return items
```

In `branch_select`:
- accept `"list-run"` in the policy check;
- after the arm loop, when `policy == "list-run"`:

```python
    if policy == "list-run":
        out.nodes = _splice_arm(out.nodes)
        if HOIST_TERMINATOR and out.nodes and out.nodes[-1].kind == ";" and not out.nodes[-1].children:
            semi = out.nodes.pop()
            out.frags.append(Terminator(None, semi))
```

- [ ] **Step 4: Implement in `engine.py`**

```python
LIST_RUN_TYPES = frozenset({"preproc_conditional_permissions", "preproc_conditional_arguments",
                            "preproc_conditional_list_elements", "preproc_conditional_option_members",
                            "preproc_conditional_where", "preproc_conditional_link_values"})
_BRACKETS = {"(", ")", "[", "]"}


def _check_alternation(new):
    seq = [c for c in new.children if c.kind not in _BRACKETS]
    want_item = True
    for c in seq:
        is_sep = c.kind == "," and not c.children
        if is_sep == want_item:
            raise LoweringError("list-separator", new, "list does not alternate item, separator")
        want_item = not want_item
    if seq and want_item:
        raise LoweringError("list-separator", new, "list ends with a separator")
```

In `_lower_ordinary`, after `new = Node(...)` and before `frags = _consume(new, frags)`:

```python
    if any(c.kind in LIST_RUN_TYPES for c in node.children):
        _check_alternation(new)
```

In `_consume`, add a branch before `else: rest.append(f)`:

```python
        elif isinstance(f, Terminator) and new.kind == "property" and f.anchor is not None \
                and any(c is f.anchor for c in new.children):
            new.children.append(f.leaf)   # terminator-hoist: the property's own `;`
```

The `Terminator` produced in `branch_select` has `anchor=None`. On its way up, `_lower_ordinary` sets `f.anchor = new` (the list) because it came from the last child. So the property sees an anchor that is one of its children.

Check the argument-list host before relying on this. Its `(` and `)` are brackets, and the tail group may be followed by `)`, so the fragment is **not** from the last child. That is correct: an argument arm never carries the property `;`, so no `Terminator` is created there.

- [ ] **Step 5: Register the six types**

Each type is `branch-select` with `list-run` in every host slot the census reports. Arm sets: the item kind(s), plus `","`, plus `";"` for permissions. Read each rule's `_*_branch` and `_*_seq` helpers for the item kinds.

- [ ] **Step 6: Verify**

Run: `python -m pytest tools/config_oracle/tests -q`, then `python -m tools.config_oracle run --tier quick 2>&1 | grep -E "discrepancy|pass:"`.
Expected: all pass, and `discrepancy: 0`.

- [ ] **Step 7: Commit**

```bash
git add tools/config_oracle/lowering/ tools/config_oracle/contracts.py tools/config_oracle/tests/test_list_run.py
git commit -m "feat(oracle): list-run policy with separator alternation and terminator-hoist"
```

---

### Task 8: Table relation and `else-relation-join`

**Files:**
- Modify: `tools/config_oracle/lowering/assemblers.py` (new `table_relation_select`)
- Modify: `tools/config_oracle/lowering/engine.py` (new `RelationContinuation`, and a consumer in `_consume`)
- Modify: `tools/config_oracle/contracts.py`
- Test: `tools/config_oracle/tests/test_table_relation.py`

**The shape** (`test/corpus/preproc_split_table_relation_branch.txt`): the property has `value: table_relation_expression` and then `value: preproc_conditional_table_relation`. Each arm holds either an `else_table_relation_fragment(else_keyword, else_relation: table_relation_expression)` or a complete table relation value, followed by an optional `;`.

**Interfaces:**
- Produces:
  - `engine.RelationContinuation(Frag)` with fields `else_kw: Node` and `relation: Node`
  - `assemblers.table_relation_select(node, ctx) -> Lowered`

Contract, written into the docstring:

> **else-relation-join.** The chosen arm's `else_table_relation_fragment` becomes a `RelationContinuation`. The owning `property` consumes it: in the preceding `value: table_relation_expression`, follow `if_table_relation` → `else_relation: table_relation_expression` → `if_table_relation` down to the deepest `if_table_relation` with no `else_keyword`. Append `else_keyword` and the fragment's relation, with field `else_relation`, as its last two children, then recompute the span of every node on that path. A complete relation in the arm is emitted as a node with field `value`. A trailing `;` becomes a `Terminator` (terminator-hoist, as in Task 7). No other edge changes.

- [ ] **Step 1: Write the failing tests**

```python
from tools.config_oracle.tests import witness

ELSE_JOIN = b"""table 1 T
{
    fields
    {
        field(1; F; Code[20])
        {
            TableRelation = if (Type = const(Item)) Item
                else if (Type = const(Resource)) Resource
#if BC24
                else if (Type = const("Alloc")) "Alloc Account" where("Account Type" = const(Fixed));
#else
                ELSE IF (Type = CONST("Alloc")) "G/L Account";
#endif
        }
    }
}
"""

WHOLE = b"""table 1 T
{
    fields
    {
        field(1; F; Code[20])
        {
            TableRelation =
#if BC24
                Item;
#else
                Resource;
#endif
        }
    }
}
"""


def test_else_relation_join_every_config(al_parser):
    witness.assert_produces(al_parser, ELSE_JOIN, "else_table_relation_fragment")
    witness.assert_all_pass(al_parser, ELSE_JOIN)


def test_whole_relation_arm_every_config(al_parser):
    witness.assert_produces(al_parser, WHOLE, "preproc_conditional_table_relation")
    witness.assert_all_pass(al_parser, WHOLE)


def test_join_at_the_wrong_depth_is_caught(al_parser, monkeypatch):
    from tools.config_oracle.lowering import engine
    monkeypatch.setattr(engine, "_deepest_open_if", lambda expr: expr.children[0])  # the SHALLOWEST if
    v = witness.verdicts(al_parser, ELSE_JOIN)
    assert any(s == "discrepancy" for s, _ in v.values()), v
```

If `WHOLE` does not produce the type, find the rule's use sites with `grep -n "preproc_conditional_table_relation" grammar.js` and adjust the source.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tools/config_oracle/tests/test_table_relation.py -q`
Expected: FAIL with `lowering:unsupported-type`.

- [ ] **Step 3: Implement**

In `engine.py`:

```python
@dataclass
class RelationContinuation(Frag):
    else_kw: Node
    relation: Node


def _deepest_open_if(expr):
    """table_relation_expression -> the deepest if_table_relation on its else chain with no else."""
    cur = next((c for c in expr.children if c.kind == "if_table_relation"), None)
    if cur is None:
        raise LoweringError("contract-shape", expr, "no if_table_relation to continue")
    while True:
        nxt = next((c for c in cur.children if c.field == "else_relation"), None)
        if nxt is None:
            return cur
        inner = next((c for c in nxt.children if c.kind == "if_table_relation"), None)
        if inner is None:
            raise LoweringError("contract-shape", cur, "else chain already closed")
        cur = inner
```

In `_consume`, add this branch before the `Terminator`/`property` branch. `_consume` handles fragments in order, so the continuation attaches before the `;` is hoisted:

```python
        elif isinstance(f, RelationContinuation) and new.kind == "property":
            vals = [c for c in new.children if c.field == "value" and c.kind == "table_relation_expression"]
            if not vals:
                raise LoweringError("unconsumed-fragment", new, "no relation to continue")
            target = _deepest_open_if(vals[-1])
            target.children.append(f.else_kw)
            target.children.append(f.relation.copy(field="else_relation"))
            for n in _path(vals[-1], target):
                recompute_span(n)
```

Also add:

```python
def _path(top, target):
    """Nodes from `target` up to `top`, deepest first, for span recomputation."""
    stack = [(top, [top])]
    while stack:
        n, path = stack.pop()
        if n is target:
            return list(reversed(path))
        for c in n.children:
            stack.append((c, path + [c]))
    raise LoweringError("contract-shape", top, "target not under top")
```

In `assemblers.py`:

```python
def table_relation_select(node, ctx) -> Lowered:
    """Contract else-relation-join (see engine.RelationContinuation). Host: a
    `property:value` slot. The chosen arm is ONE of: an `else_table_relation_fragment`
    (-> RelationContinuation), or a complete relation value (-> a node with field
    `value`); then an optional `;` (-> Terminator, terminator-hoist). An empty or
    unselected arm contributes nothing. Anything else is contract-shape."""
    ctx.policy(contracts.REGISTRY[node.kind], node)
    arms, endif = split_arms(node)
    arm = _active(arms, endif, node, ctx)
    frags, nodes = [], []
    items = list(arm)
    semi = items.pop() if items and items[-1].kind == ";" else None
    if len(items) > 1:
        raise LoweringError("contract-shape", node, "arm: " + " ".join(c.kind for c in items))
    if items and items[0].kind == "else_table_relation_fragment":
        frag = items[0]
        if len(frag.children) != 2 or frag.children[0].kind != "else_keyword":
            raise LoweringError("contract-shape", frag, "expected `else else_relation:`")
        else_kw = _lower_all(frag.children[:1], ctx, frag.kind)[0]   # an ordinary node: marked kept once
        rel = _lower_all(frag.children[1:], ctx, frag.kind)[0]
        frags.append(RelationContinuation(None, else_kw, rel))
    elif items:
        nodes = [n.copy(field="value") for n in _lower_all(items, ctx, node.kind)]
    if semi is not None:
        frags.append(Terminator(None, _lower_all([semi], ctx, node.kind)[0]))
    return Lowered(nodes, frags)
```

Import `RelationContinuation` into `assemblers.py` from `engine`.

`else_keyword` is a named keyword node with one anonymous child, so `_lower_all` lowers it as an ordinary node and marks its leaf `kept` exactly once. Do not mark it separately.

- [ ] **Step 4: Register**

- `preproc_conditional_table_relation`: `assembler`, handler `tools.config_oracle.lowering.assemblers.table_relation_select`, hosts from the census.
- `else_table_relation_fragment`: `fragment`, handler `None`, hosts `{"preproc_conditional_table_relation:<children>": "consumed"}`. `SPECIAL_NON_PREFIXED` already covers it.

- [ ] **Step 5: Verify**

Run: `python -m pytest tools/config_oracle/tests -q`, then `python -m tools.config_oracle run --tier quick 2>&1 | grep -E "discrepancy|pass:"`.
Expected: all pass, and `discrepancy: 0`.

- [ ] **Step 6: Commit**

```bash
git add tools/config_oracle/lowering/ tools/config_oracle/contracts.py tools/config_oracle/tests/test_table_relation.py
git commit -m "feat(oracle): table-relation lowering with the else-relation-join contract"
```

---

### Task 9: One-reading contracts

**Files:**
- Modify: `tools/config_oracle/lowering/assemblers.py` (new: `open_statement_reading`, `block_end_in_else`, `block_close_after_endif`, `container_reopen`)
- Modify: `tools/config_oracle/lowering/engine.py` (new `SiblingsAfter` fragment, and a consumer in `_consume`)
- Modify: `tools/config_oracle/contracts.py`
- Create: `tools/config_oracle/tests/test_one_reading.py`

**Interfaces:**
- Consumes: `select.reading_active`, `Resolution.group_of`, `BlockCompletion`
- Produces:
  - `LoweringError("one-reading", node, <type>)`, which reaches records as `lowering:one-reading:...`
  - `engine.SiblingsAfter(Frag)` with field `nodes: list`, consumed by `layout_body` and `layout_container_body` (inserted right after the anchor)

Contracts, one per handler docstring:

- **`open_statement_reading`** (`preproc_split_open_statement`, reading `arm:not-else-led`). If the chosen arm's first item is `else_keyword`, raise `one-reading`: the tree shows that `else` as a sibling of a complete if/case. Otherwise raise `unsupported-type`: complete-prefix arms are milestone 3's.
- **`block_end_in_else`** (reading `arm:else`). Host: the last child of `code_block`. In the `#else` configuration, the `#else` arm's statements and the node's `end_keyword` become a `BlockCompletion`. Any other configuration raises `one-reading`.
- **`block_close_after_endif`** (reading `arm:else`). The node is `preproc_endif stmts* end_keyword` and has no `#if` of its own. Its group is `ctx.resolution.group_of[<#endif offset>]`. The `#else` reading is active when `ctx.resolution.arm_choice[group]` is the `#else` directive's offset. That offset is found as the key of `group_of` whose value is `group` and which is not the `#endif` (there is exactly one `#else` in this rule's group, by grammar). In that reading, the `#endif` is accounted as `directive`, and the statements plus `end` become a `BlockCompletion`. Any other configuration raises `one-reading`.
- **`container_reopen`** (reading `arm:if`). Host: the closing position of a layout container block. In the `#if` configuration, the named rewrite **container-reopen** applies:
  - the arm's `}` closes the host container (returned as a `BlockCompletion`-like closing: this handler returns the `}` as a node, because `_layout_container_body_block`'s `choice('}', …)` puts it at the same position a plain `}` would take);
  - the arm's header (`group_keyword`, etc., plus the `_paren_name` pieces), `{`, both body halves (merged into one `layout_container_body` with field `body`) and the final `}` build a NEW container node of the matching kind (`group_keyword` → `group_section`, `repeater_keyword` → `repeater_section`, and so on), returned as `SiblingsAfter(anchor=None, nodes=[new])`, inserted after the host container in its layout body.

  Any other configuration raises `one-reading`.

- [ ] **Step 1: Write the failing tests**

```python
import pytest

from tools.config_oracle.tests import witness

REOPEN = b"page 1 P\n{\n    layout\n    {\n        area(Content)\n        {\n            group(G)\n            {\n                field(A; Rec.A) { }\n#if not C28\n            }\n            group(R)\n            {\n                Caption = 'R';\n                field(B; Rec.B) { }\n#endif\n                field(C; Rec.C) { }\n            }\n        }\n    }\n}\n"
BOUNDARY = b"codeunit 1 T\n{\n    procedure P()\n    begin\n        Message('a');\n#if not C28\n        Message('b');\n#else\n        Message('c');\n    end;\n\n    local procedure Q(T: Text): Text\n    begin\n        exit(T);\n#endif\n    end;\n}\n"
ELSE_LED = b"codeunit 1 T\n{\n    procedure P(N: Integer)\n    begin\n        if N < 1 then\n            Message('a')\n#if not C28\n        else begin\n#else\n        else\n#endif\n            Message('b');\n#if not C28\n            Message('c');\n        end;\n#endif\n    end;\n}\n"


@pytest.mark.parametrize("src,kind,reading_config", [
    (REOPEN, "preproc_split_container_reopen", "C28=0"),
    (BOUNDARY, "preproc_split_block_end_in_else", "C28=1"),
])
def test_reading_passes_other_is_one_reading(al_parser, src, kind, reading_config):
    witness.assert_produces(al_parser, src, kind)
    v = witness.verdicts(al_parser, src)
    assert v[reading_config][0] == "pass", v[reading_config]
    others = [c for c in v if c != reading_config]
    assert others and all(any(i.startswith("lowering:one-reading") for i in v[c][1]) for c in others), v


def test_one_reading_is_never_a_pass(al_parser):
    v = witness.verdicts(al_parser, ELSE_LED)
    assert all(any(i.startswith("lowering:one-reading") for i in items) for _, items in v.values()), v


def test_wrong_reading_declared_turns_pass_into_discrepancy(al_parser, monkeypatch):
    from tools.config_oracle import contracts
    e = contracts.REGISTRY["preproc_split_container_reopen"]
    monkeypatch.setitem(contracts.REGISTRY, e.type, contracts.Entry(
        e.type, e.kind, e.handler, e.hosts, e.alias_to, e.arm, "arm:inactive"))
    v = witness.verdicts(al_parser, REOPEN)
    assert v["C28=1"][0] != "pass", v
```

The config labels (`C28=0`, `C28=1`) follow whatever format `runner` emits. Print `witness.verdicts` once and match it. `C28=0` means `not C28` holds, so the `#if` arm is taken.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tools/config_oracle/tests/test_one_reading.py -q`
Expected: FAIL with `lowering:unsupported-type`.

- [ ] **Step 3: Implement the four handlers**

Use `split_arms`, `_active` and `_lower_all` as the existing assemblers do. The skeleton for `block_end_in_else`:

```python
def block_end_in_else(node, ctx) -> Lowered:
    """Contract: see plan Task 9 / spec P4 (reading arm:else)."""
    entry = contracts.REGISTRY[node.kind]
    ctx.policy(entry, node)
    end = node.children[-1]
    if end.kind != "end_keyword":
        raise LoweringError("contract-shape", node, "no closing end")
    # The node has no #endif of its own: split its arms by position, not via split_arms.
    arms = []
    for c in node.children[:-1]:
        if c.kind in ("preproc_if", "preproc_elif", "preproc_else"):
            arms.append((c, []))
        else:
            arms[-1][1].append(c)
    choice = chosen_arm(node, arms, ctx)
    if not (arms[-1][0].kind == "preproc_else" and choice == arms[-1][0].start):
        raise LoweringError("one-reading", node, node.kind)
    for d, items in arms:
        ctx.accounting.mark(d, "directive")
        if d.start != choice:
            for c in items:
                ctx.accounting.mark(c, "inactive-arm")
    stmts = _lower_all(arms[-1][1], ctx, "statement_block")
    end_l = _lower_all([end], ctx, "code_block")[0]
    return Lowered([], [BlockCompletion(None, stmts, end_l)])
```

For `container_reopen`, build the new container with `_span_from_children(Node(kind, True, None, 0, 0, parts))`. Add the `SiblingsAfter` consumer in `_consume` for `new.kind in {"layout_body", "layout_container_body"}`, inserting after the anchor, as the `Following` branch does for statement hosts. The host container is the anchor: the fragment passes up from the container's last child, where `_lower_ordinary` sets `f.anchor` to it.

- [ ] **Step 4: Register**

Register the four types as `assembler` with their handlers and `reading=`. Hosts come from the census, and each block closing classifies as `consumed`.

- [ ] **Step 5: Verify**

Run: `python -m pytest tools/config_oracle/tests -q`, then `python -m tools.config_oracle run --tier quick 2>&1 | grep -E "discrepancy|pass:"`.
Expected: all pass, and `discrepancy: 0`.

- [ ] **Step 6: Commit**

```bash
git add tools/config_oracle/lowering/ tools/config_oracle/contracts.py tools/config_oracle/tests/test_one_reading.py
git commit -m "feat(oracle): one-reading contracts for container reopen, procedure boundary, else-led open statements"
```

---

### Task 10: The precedence table and its self-test

**Files:**
- Create: `tools/config_oracle/lowering/expression.py`
- Create: `tools/config_oracle/tests/test_precedence.py`

**Interfaces:**
- Produces:
  - `expression.LEVEL: dict[str, int]` (operator text, lowercased → level; higher binds tighter)
  - `expression.KIND_FOR: dict[str, str]` (operator text → node kind)
  - `expression.BINARY_KINDS: frozenset`
  - `expression.op_text(op_node, source=None) -> str`
  - `expression.flatten(node) -> list[Node]`, alternating operand, operator, operand
  - `expression.compose(flat, field) -> Node`

The table, from `test/corpus/operator_precedence_test.txt`'s header (never from `grammar.js`):

| level | operators | kind |
|---|---|---|
| 6 | `* / div mod` | `multiplicative_expression` |
| 5 | `+ -` | `additive_expression` |
| 4 | `in is as` | `in_expression`, `is_expression`, `as_expression` |
| 3 | `and` | `logical_expression` |
| 2 | `or xor` | `logical_expression` |
| 1 | `= <> < > <= >=` (a `comparison_operator` node) | `comparison_expression` |

All binary levels are left-associative. Unary, parenthesized, call, member and every other expression is an atom.

Operator text: an anonymous operator leaf has kind equal to its text (`+`, `div`, `and`). A `comparison_operator` node is recognised by kind. `op_text` returns `"cmp"` for it.

Check the kinds of `in`/`is`/`as` against `grammar.js` (`grep -n "in_expression\|is_expression\|as_expression" grammar.js`). If they do not use `left`/`operator`/`right` fields, they are atoms here: drop them from `BINARY_KINDS` and write down why in the module docstring.

- [ ] **Step 1: Write the self-test, which fails**

```python
"""The precedence table recomposes every compiler-verified grouping (base §3, spec P5.3)."""
import pytest

from tools.config_oracle import fixtures, ir
from tools.config_oracle.lowering import expression
from tools.query_coverage import loader

CASES = [c for c in fixtures.extract(loader.REPO_ROOT / "test" / "corpus")
         if c.file == "operator_precedence_test.txt"]


def _chains(root):
    """Maximal binary chains: binary nodes whose parent is not a binary node."""
    out, stack = [], [(root, None)]
    while stack:
        n, parent = stack.pop()
        if n.kind in expression.BINARY_KINDS and (parent is None or parent.kind not in expression.BINARY_KINDS):
            out.append(n)
        for c in n.children:
            stack.append((c, n))
    return out


def _shape(n):
    return (n.kind, n.field, n.start, n.end, tuple(_shape(c) for c in n.children))


def test_there_are_18_cases():
    assert len(CASES) == 18


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name[:60])
def test_recompose_matches_fixture(al_parser, case):
    root, _, problems = ir.from_tree(al_parser.parse(case.source))
    assert problems == []
    chains = _chains(root)
    for ch in chains:
        rebuilt = expression.compose(expression.flatten(ch), ch.field)
        assert _shape(rebuilt) == _shape(ch), case.name
```

Some precedence cases may contain no binary chain, for example the range (`..`) and ternary cases. For those, the test passes vacuously. Add `assert chains or "range" in case.name.lower() or "ternary" in case.name.lower()` only after checking which cases those are. The requirement is that every case with a binary chain is recomposed.

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tools/config_oracle/tests/test_precedence.py -q`
Expected: FAIL with an import error (`expression` does not exist).

- [ ] **Step 3: Implement `expression.py`**

```python
"""Precedence-correct recomposition of flattened binary chains (base §3).

The table is taken from test/corpus/operator_precedence_test.txt's header,
which was measured with alc -- NOT from grammar.js prec() values. That keeps
the oracle independent of the grammar it checks.
"""
from __future__ import annotations

from tools.config_oracle.ir import Node

LEVEL = {"*": 6, "/": 6, "div": 6, "mod": 6, "+": 5, "-": 5, "in": 4, "is": 4, "as": 4,
         "and": 3, "or": 2, "xor": 2, "cmp": 1}
KIND_FOR = {"*": "multiplicative_expression", "/": "multiplicative_expression",
            "div": "multiplicative_expression", "mod": "multiplicative_expression",
            "+": "additive_expression", "-": "additive_expression",
            "in": "in_expression", "is": "is_expression", "as": "as_expression",
            "and": "logical_expression", "or": "logical_expression", "xor": "logical_expression",
            "cmp": "comparison_expression"}
BINARY_KINDS = frozenset(KIND_FOR.values())


def op_text(op):
    return "cmp" if op.kind == "comparison_operator" else op.kind.lower()


def _parts(node):
    left = next((c for c in node.children if c.field == "left"), None)
    op = next((c for c in node.children if c.field == "operator"), None)
    right = next((c for c in node.children if c.field == "right"), None)
    if left is None or op is None or right is None or len(node.children) != 3:
        raise ValueError(f"not a plain binary node: {node.kind}@{node.start}")
    return left, op, right


def flatten(node):
    if node.kind not in BINARY_KINDS:
        return [node]
    left, op, right = _parts(node)
    return flatten(left) + [op] + flatten(right)


def compose(flat, field):
    """Operator-precedence parse over an alternating [operand, op, operand, ...] list."""
    operands, ops = [flat[0].copy(field=None)], []

    def reduce_top():
        op = ops.pop()
        r, l = operands.pop(), operands.pop()
        kids = [l.copy(field="left"), op.copy(field="operator"), r.copy(field="right")]
        operands.append(Node(KIND_FOR[op_text(op)], True, None, kids[0].start, kids[-1].end, kids))

    for i in range(1, len(flat), 2):
        op, rhs = flat[i], flat[i + 1]
        while ops and LEVEL[op_text(ops[-1])] >= LEVEL[op_text(op)]:   # left-associative
            reduce_top()
        ops.append(op)
        operands.append(rhs.copy(field=None))
    while ops:
        reduce_top()
    return operands[0].copy(field=field)
```

`flatten` is recursive. Real chains can be thousands of operators deep. Make it iterative with an explicit stack before the task is done: the recursive version above states the contract, and the iterative one must return the same list.

- [ ] **Step 4: Verify**

Run: `python -m pytest tools/config_oracle/tests/test_precedence.py -q`
Expected: 18 recompose cases pass.

A failure means one of two things: the table disagrees with the fixture, so fix the table and cite the fixture line; or the fixture tree is a grammar defect. A grammar defect is a Task 18 finding. File it, and do not bend the table to the grammar.

- [ ] **Step 5: Commit**

```bash
git add tools/config_oracle/lowering/expression.py tools/config_oracle/tests/test_precedence.py
git commit -m "feat(oracle): alc-measured precedence table with recomposition self-test"
```

---

### Task 11: Expression continuation and operand prefix

**Files:**
- Modify: `tools/config_oracle/lowering/engine.py` (new `ToPrevious` / `ExpressionContinuation`; the `_lower_ordinary` loop; and a hook in `lower` for binary nodes with a prefix)
- Modify: `tools/config_oracle/lowering/assemblers.py` (new `expression_tail`, `operand_prefix`)
- Modify: `tools/config_oracle/contracts.py`
- Modify: `tools/config_oracle/tests/test_replay.py` (the replay-4 HEAD control stops being an xfail)
- Create: `tools/config_oracle/tests/test_expression_lowering.py`

**Shapes** (verified 2026-09-28):
- `r := 1 #if X + 2 #endif * 3;` gives `assignment_statement[left, operator, right: integer, preproc_conditional_expression_tail[#if, operator, operand, #endif, operator, operand]]`. The tail is the right operand's next sibling.
- In `F(2 #if X + 1 #endif, 3)`, the tail follows `2` inside `argument_list`.
- `r := 1 + #if X 2 * #else 4 - #endif 5;` gives `additive_expression[left, operator, preproc_operand_prefix[#if, operand, operator, #else, operand, operator, #endif], right]`.

**Interfaces:**
- Produces:
  - `engine.ToPrevious(Frag)`: base class with `apply(prev: Node) -> Node`, consumed in `_lower_ordinary` by the immediately preceding lowered sibling
  - `engine.ExpressionContinuation(ToPrevious)` with `pairs: list[tuple[Node, Node]]`
  - `assemblers.expression_tail(node, ctx)`
  - `assemblers.operand_prefix(node, ctx)`, called only from the binary hook

Contracts:
- **expression-continuation.** The chosen arm's `(operator, operand)` pairs, then the pairs after `#endif`, extend the preceding sibling expression. That expression and every operand are flattened (`expression.flatten`) and recomposed (`expression.compose`), keeping the preceding sibling's field. No other edge changes.
- **operand-prefix.** In a binary node with a `preproc_operand_prefix` child, the chosen arm's `(operand, operator)` sits between the node's operator and its right operand. The WHOLE binary chain containing it (from the chain's top binary node, stopping at non-binary nodes and parenthesised atoms) is flattened with it and recomposed; regrouping only the prefix's own node is wrong for `a * #if X b or #endif c + d`. No arm selected leaves the chain's shape as parsed. *(Amended during execution, Task 11.)*

- [ ] **Step 1: Write the failing tests**

```python
import pytest

from tools.config_oracle.tests import witness

TAIL_ASSIGN = b"codeunit 1 T\n{\n    trigger OnRun()\n    begin\n        r := 1\n#if X\n            + 2\n#endif\n            * 3;\n    end;\n}\n"
TAIL_ARG = b"codeunit 1 T\n{\n    trigger OnRun()\n    begin\n        F(2\n#if X\n            + 1\n#endif\n            , 3);\n    end;\n}\n"
TAIL_OPERAND = b"codeunit 1 T\n{\n    trigger OnRun()\n    begin\n        r := 1\n#if X\n            * 2 + 3\n#endif\n            ;\n    end;\n}\n"
PREFIX = b"codeunit 1 T\n{\n    trigger OnRun()\n    begin\n        r := 1 +\n#if X\n            2 *\n#else\n            4 -\n#endif\n            5;\n    end;\n}\n"


@pytest.mark.parametrize("src,kind", [(TAIL_ASSIGN, "preproc_conditional_expression_tail"),
                                      (TAIL_ARG, "preproc_conditional_expression_tail"),
                                      (PREFIX, "preproc_operand_prefix")])
def test_every_config_passes(al_parser, src, kind):
    witness.assert_produces(al_parser, src, kind)
    witness.assert_all_pass(al_parser, src)


def test_operand_is_regrouped(al_parser):
    witness.assert_all_pass(al_parser, TAIL_OPERAND)


def test_naive_append_is_caught(al_parser, monkeypatch):
    from tools.config_oracle.lowering import expression
    monkeypatch.setattr(expression, "LEVEL", {k: 1 for k in expression.LEVEL})  # no precedence
    v = witness.verdicts(al_parser, TAIL_ASSIGN)
    assert any(s == "discrepancy" for s, _ in v.values()), v
```

Search all 5 fixture positions for the continuation from `grammar.js`'s comment (assignment RHS, exit value, argument, if condition, property value). Add every one that is not already covered as a witness here, taking it from the fixture that pins it: `grep -ln "preproc_conditional_expression_tail" test/corpus/*.txt`.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tools/config_oracle/tests/test_expression_lowering.py -q`
Expected: FAIL with `lowering:unsupported-type`.

- [ ] **Step 3: Implement the engine**

```python
@dataclass
class ToPrevious(Frag):
    """Binds to the IMMEDIATELY PRECEDING lowered sibling, wherever it is lowered."""
    def apply(self, prev):
        raise NotImplementedError


@dataclass
class ExpressionContinuation(ToPrevious):
    pairs: list = field(default_factory=list)

    def apply(self, prev):
        from tools.config_oracle.lowering import expression
        flat = expression.flatten(prev)
        for op, operand in self.pairs:
            flat += [op] + expression.flatten(operand)
        return expression.compose(flat, prev.field)
```

In the `_lower_ordinary` loop, replace the body after `r = lower(...)` with:

```python
        for f in r.frags:
            f._from_last = (i == last_index)
        kids.extend(r.nodes)
        for f in r.frags:
            if isinstance(f, ToPrevious):
                if not kids or not kids[-1].named:
                    raise LoweringError("unconsumed-fragment", c, f"{type(f).__name__} with no preceding sibling")
                kids[-1] = f.apply(kids[-1])
            else:
                frags.append(f)
```

The `ToPrevious` fragment is applied **after** `kids.extend(r.nodes)`. That is right for `ExpressionContinuation`, where the tail emits no nodes. Task 12's `VarTailMerge` emits nodes and must bind to the sibling before them. It therefore records how many nodes it emitted (`f._skip = len(r.nodes)`), and `apply` is called on `kids[-1 - f._skip]`. Write the loop with that index now: `target = len(kids) - 1 - getattr(f, "_skip", 0)`.

The binary hook in `lower`, before `_lower_ordinary`:

```python
    if node.kind in _binary_kinds() and any(c.kind == "preproc_operand_prefix" for c in node.children):
        from tools.config_oracle.lowering.assemblers import operand_prefix
        return operand_prefix(node, ctx)
```

Here `_binary_kinds()` returns `expression.BINARY_KINDS`, imported lazily to avoid a cycle.

- [ ] **Step 4: Implement the handlers**

`expression_tail`: split the node at its `preproc_endif`. `split_arms` on the head gives the arms. Collect `(operator, operand)` pairs from the chosen arm by `field`, then from the children after `#endif`. Lower every piece with `_lower_all`, so accounting stays exact. Return `Lowered([], [ExpressionContinuation(None, pairs)])`.

`operand_prefix(binary, ctx)`:
1. lower `left`, `operator` and `right`;
2. `split_arms` the prefix child, and collect the chosen arm's `(operand, operator)` pair;
3. `flat = flatten(left) + [op] + flatten(operand) + [op2] + flatten(right)`, or `flatten(left) + [op] + flatten(right)` with no arm;
4. return `Lowered([expression.compose(flat, binary.field)])`.

Account the prefix's directives and inactive arms as `_active` does.

- [ ] **Step 5: Register, then flip the replay-4 control**

Register both types as `assembler`, with hosts from the census. `preproc_operand_prefix` sits inside binary kinds, which the hook handles before a slot lookup. Its `hosts` still come from the census, so the census stays consistent, and each is `consumed`.

In `tests/test_replay.py`, remove the `xfail` marker on `test_current_parser_passes_the_same_cases[head-4]`.

- [ ] **Step 6: Verify**

Run: `python -m pytest tools/config_oracle/tests -q`, then `python -m tools.config_oracle run --tier quick 2>&1 | grep -E "discrepancy|pass:"`.
Expected: all pass, `head-4` passes, and `discrepancy: 0`.

- [ ] **Step 7: Commit**

```bash
git add tools/config_oracle/lowering/ tools/config_oracle/contracts.py tools/config_oracle/tests/
git commit -m "feat(oracle): expression continuation and operand prefix via the precedence table"
```

---

### Task 12: `var-tail-merge`

**Files:**
- Modify: `tools/config_oracle/lowering/engine.py` (new `VarTailMerge(ToPrevious)`)
- Modify: `tools/config_oracle/lowering/assemblers.py` (new `split_var_section_tail`)
- Modify: `tools/config_oracle/contracts.py`
- Create: `tools/config_oracle/tests/test_var_tail.py`

**Shape:** `preproc_split_var_section_tail[#if, variables: var_body, <body elements>…, (#elif|#else [variables: var_body] <body elements>…)*, #endif]` follows a `var_section` sibling in `declaration_body`.

Contract **var-tail-merge**: the chosen arm's `variables` children append to the preceding sibling `var_section`'s `var_body`, which is created with field `body` if absent. The arm's other items become nodes emitted in place, as siblings after that section. No arm selected emits nothing. The preceding sibling must be a `var_section`, or the result is `contract-shape`.

- [ ] **Step 1: Write the failing test**

```python
from tools.config_oracle.tests import witness

SRC = b"codeunit 1 T\n{\n    var\n        X: Integer;\n#if A\n        Y: Integer;\n\n    procedure P()\n    begin\n    end;\n#endif\n\n    procedure Q()\n    begin\n    end;\n}\n"


def test_var_tail_every_config(al_parser):
    witness.assert_produces(al_parser, SRC, "preproc_split_var_section_tail")
    witness.assert_all_pass(al_parser, SRC)


def test_merge_into_the_wrong_sibling_is_caught(al_parser, monkeypatch):
    from tools.config_oracle.lowering import engine
    monkeypatch.setattr(engine.VarTailMerge, "apply", lambda self, prev: prev)  # drop the variables
    assert any(s != "pass" for s, _ in witness.verdicts(al_parser, SRC).values())
```

If `SRC` does not produce the type, copy the shape from `test/corpus/var_section_does_not_swallow_procedures_test.txt`.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tools/config_oracle/tests/test_var_tail.py -q`
Expected: FAIL with `lowering:unsupported-type`.

- [ ] **Step 3: Implement**

```python
@dataclass
class VarTailMerge(ToPrevious):
    decls: list = field(default_factory=list)

    def apply(self, prev):
        if prev.kind != "var_section":
            raise LoweringError("contract-shape", prev, "var-tail-merge needs a preceding var_section")
        if not self.decls:
            return prev
        body = next((c for c in prev.children if c.field == "body"), None)
        kids = list(prev.children)
        if body is None:
            body = Node("var_body", True, "body", 0, 0, [])
            kids.append(body)
        new_body = body.copy(children=body.children + self.decls)
        _span_from_children(new_body)
        kids = [new_body if c is body else c for c in kids]
        return _span_from_children(prev.copy(children=kids))
```

`split_var_section_tail`: select the arm with `_active`. Lower the `variables` children's own children (the declarations) and the other items separately. Return `Lowered(others, [VarTailMerge(None, decls)])`, and set `frag._skip = len(others)` so it binds to the sibling before them (Task 11's loop index).

- [ ] **Step 4: Register, then verify**

Register it as `assembler`, hosts from the census (`declaration_body:<children>` and any others).

Run: `python -m pytest tools/config_oracle/tests -q`, then the quick tier.
Expected: all pass, and `discrepancy: 0`.

- [ ] **Step 5: Commit**

```bash
git add tools/config_oracle/lowering/ tools/config_oracle/contracts.py tools/config_oracle/tests/test_var_tail.py
git commit -m "feat(oracle): var-tail-merge for preproc_split_var_section_tail"
```

---

### Task 13: `else-begin-over-endif`, with replay 1

**Files:**
- Modify: `tools/config_oracle/lowering/assemblers.py` (new `else_begin_over_endif`)
- Modify: `tools/config_oracle/contracts.py` (register it with `reading="arm:inactive"`; the handler uses the reading only for widened shapes)
- Modify: `tools/config_oracle/replay.py` (add replay 1)
- Test: `tools/config_oracle/tests/test_else_begin.py`, `tools/config_oracle/tests/test_replay.py`

**Shape** (`grammar.js` `preproc_split_else_begin_over_endif`): `preproc_if stmts* end_keyword (; end_keyword)* else_keyword _reopen_block preproc_endif stmts* end_keyword`, where `_reopen_block = (if_keyword condition then_keyword)* begin_keyword stmts* [_reopen_block]`. It sits as the last child of a `code_block`.

The **base shape** has no statements before the first `end`, exactly one `end` before `else`, and a reopen block that is a bare `begin stmts*` (no `if` header, no nested reopen).

Contract **else-begin-over-endif**:
- **Arm not selected:** the tail statements and the final `end` form a `BlockCompletion`, and the host block's body continues with them.
- **Arm selected, base shape:** `BlockCompletion(statements=[], end=<arm's end>)`, plus `ElseAttachment(else_kw, code_block(begin, [body: statement_block(arm stmts + tail stmts)], <final end>))`. Only the `if_statement` whose `then_branch` is the host block consumes it (the engine already refuses any other owner).
- **Arm selected, widened shape:** `one-reading`.

- [ ] **Step 1: Write the failing tests**

```python
from tools.config_oracle.tests import witness

BASE = b"codeunit 1 T\n{\n    procedure P(C: Boolean)\n    begin\n        if C then begin\n            A();\n#if X\n        end else begin\n            B();\n#endif\n            D();\n        end;\n    end;\n}\n"
WIDENED = b"codeunit 1 T\n{\n    procedure P(A: Boolean; B: Boolean; L: Boolean; S: Boolean)\n    var\n        C: Integer;\n    begin\n        if A then begin\n            C := 1;\n            if B then begin\n                C := 2;\n#if not C28\n                C := 3;\n            end;\n        end else\n            if L then begin\n                C := 4;\n                if S then begin\n                    C := 5;\n#endif\n                end;\n            end;\n        C := 6;\n    end;\n}\n"


def test_base_shape_both_configs(al_parser):
    witness.assert_produces(al_parser, BASE, "preproc_split_else_begin_over_endif")
    witness.assert_all_pass(al_parser, BASE)


def test_widened_shape_one_reading(al_parser):
    v = witness.verdicts(al_parser, WIDENED)
    assert v["C28=1"][0] == "pass", v
    assert any(i.startswith("lowering:one-reading") for i in v["C28=0"][1]), v
```

`WIDENED` is `test/corpus/split_else_begin_reopen_chain_test.txt`'s source. Take it from there if it has drifted.

- [ ] **Step 2: Add replay 1 to `replay.py`**

```python
    Replay(1, "bad36e4^", "preproc_block_over_conditional_test.txt",
           lambda c: c.name.startswith("Shape C"),
           lambda recs: any(_has(r, "|structure|parent|") for r in recs)),
```

Put it first in `REPLAYS`. Append to `tests/test_replay.py`, following the existing pattern for replays 2 to 5 (read that file). One `slow` test requires `run_replay(REPLAYS[0], "cache").detected` and not `masked_by_cannot_validate`. The HEAD positive-control parametrisation gains a `head-1` case, which must pass.

- [ ] **Step 3: Run the tests to verify they fail**

Run: `python -m pytest tools/config_oracle/tests/test_else_begin.py -q`, then `python -m pytest tools/config_oracle/tests/test_replay.py -q -m slow -k "1"`.
Expected: the else-begin tests fail with `unsupported-type`. Replay 1 is MASKED, because its HEAD lowering is unsupported.

- [ ] **Step 4: Implement `else_begin_over_endif`**

Split the node at its first `preproc_endif`. The head gives one `#if` arm; the tail is `stmts* end`. With `_active`: if nothing is chosen, return `BlockCompletion(tail stmts, final end)`. If the arm is chosen, classify it:

```python
    ends = [i for i, c in enumerate(arm) if c.kind == "end_keyword"]
    base = (ends == [0] and len(arm) >= 3 and arm[1].kind == "else_keyword"
            and arm[2].kind == "begin_keyword"
            and not any(c.kind in ("if_keyword", "begin_keyword") for c in arm[3:]))
    if not base:
        raise LoweringError("one-reading", node, node.kind)
```

Then build it as `split_code_block_end` shape B does: `end1, else_kw, begin = _lower_all(arm[:3], …)`, `inner = _lower_all(arm[3:] + tail_stmts, …)`, and so on. Reuse that code's structure, and do not duplicate its accounting.

- [ ] **Step 5: Register, then verify**

Register it as `assembler`, host `code_block:<children>` `consumed`.

Run: `python -m pytest tools/config_oracle/tests -q`, then `python -m pytest tools/config_oracle/tests/test_replay.py -q -m slow`, then the quick tier.
Expected: all pass; replay 1 is CAUGHT and replays 2 to 5 are still CAUGHT; `discrepancy: 0`.

- [ ] **Step 6: Commit**

```bash
git add tools/config_oracle/lowering/assemblers.py tools/config_oracle/contracts.py tools/config_oracle/replay.py tools/config_oracle/tests/
git commit -m "feat(oracle): else-begin-over-endif assembler; replay 1 caught"
```

---

### Task 14: `report-brace-owner`

**Files:**
- Modify: `tools/config_oracle/lowering/assemblers.py` (new `report_brace_owner`)
- Modify: `tools/config_oracle/contracts.py`
- Create: `tools/config_oracle/tests/test_report_brace.py`

**Shapes** (`grammar.js`):
- `preproc_split_report_dataitem_open_over_endif` = `#if _report_dataitem_header '{' [conditional_body: report_body] #endif [shared_body: report_body] '}'`.
- Inside `shared_body` there is one `report_dataitem` whose last child is `preproc_split_report_brace_close` = `#if [report_body] '}' [#else [report_body]] #endif`.

The real site is BCApps 29.0 `Layers/GB/BaseApp/Sales/History/SalesShipment.Report.al:536-590`.

Contract **report-brace-owner** (spec P5.2):
- **Open arm active:** the result is one `report_dataitem` carrying the node's field: `header pieces, '{', body: report_body(conditional_body items + shared_body items), '}'`. Inside it, the inner dataitem's body gains the brace-close arm's `report_body` items and closes at the arm's `}`. The brace-close `#if` arm must be the chosen one, or the result is `contract-shape`.
- **Open arm inactive:** the outer dataitem dissolves. The nodes emitted are the `shared_body` items before the inner dataitem, then the inner dataitem with body = its own items + the brace-close `#else` items + the `shared_body` items after it, closed by the node's final `}`. The brace-close `#else` arm must be the chosen one (no `}` in it), or the result is `contract-shape`.
- **Accounting:** the brace-close node is handled here and never lowered on its own. Registered as a `fragment` with host `report_dataitem:<children>` `consumed`, and a `preproc_split_report_brace_close` reached through `lower()` is `unconsumed-fragment`.

- [ ] **Step 1: Write the failing tests**

```python
from tools.config_oracle.tests import witness

SRC = b"""report 1 R
{
    dataset
    {
        dataitem(H; Integer)
        {
            dataitem(Total; Integer)
            {
            }
#if not CLEAN28
            dataitem(Outer; Integer)
            {
                DataItemTableView = sorting(Number);
#endif
                dataitem(Total2; Integer)
                {
                    column(A; 1) { }
#if not CLEAN28
                    column(B; 2) { }
                }
#else
                    column(C; 3) { }
#endif
                trigger OnPreDataItem()
                begin
                end;
            }
            dataitem(Next; Integer) { }
        }
    }
}
"""


def test_both_configs(al_parser):
    witness.assert_produces(al_parser, SRC, "preproc_split_report_dataitem_open_over_endif")
    witness.assert_produces(al_parser, SRC, "preproc_split_report_brace_close")
    witness.assert_all_pass(al_parser, SRC)


def test_trigger_left_in_outer_is_caught(al_parser, monkeypatch):
    from tools.config_oracle.lowering import assemblers
    monkeypatch.setattr(assemblers, "_RB_MOVE_AFTER", False)  # labelled hand-built bad lowering
    v = witness.verdicts(al_parser, SRC)
    assert any(s == "discrepancy" for s, _ in v.values()), v
```

`_RB_MOVE_AFTER` is a module flag in `assemblers.py`, default `True`. When it is `False`, the inactive branch leaves the "after" items outside the inner dataitem. It exists only for this mutation.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tools/config_oracle/tests/test_report_brace.py -q`
Expected: FAIL with `unsupported-type`.

- [ ] **Step 3: Implement**

Follow the contract. Build each `report_body` with `_span_from_children(Node("report_body", True, "body", 0, 0, items))`, and skip it when `items` is empty. Build each `report_dataitem` with `_span_from_children(Node("report_dataitem", True, field, 0, 0, parts))`. Lower every original piece exactly once through `_lower_all`, and account the brace-close directives and inactive arms with `_active` on a `split_arms` of that node.

- [ ] **Step 4: Register, then verify**

Register the open node as `assembler` (hosts from the census) and the brace node as `fragment`, as above.

Run: `python -m pytest tools/config_oracle/tests -q`, then the quick tier.
Expected: all pass, and `discrepancy: 0`.

- [ ] **Step 5: Commit**

```bash
git add tools/config_oracle/lowering/assemblers.py tools/config_oracle/contracts.py tools/config_oracle/tests/test_report_brace.py
git commit -m "feat(oracle): report-brace-owner assembler for the report dataitem open/close pair"
```

---

### Task 15: Split-procedure witness matrix

**Files:**
- Create: `tools/config_oracle/tests/test_split_procedure_matrix.py`
- Modify: `tools/config_oracle/lowering/assemblers.py`, **only** if the matrix finds a defect

**Interfaces:**
- Consumes: `assemblers.split_procedure` (unchanged unless a case fails)

- [ ] **Step 1: Write the matrix**

```python
"""split-procedure over every _procedure_tail form (spec P5.1)."""
import pytest

from tools.config_oracle.tests import witness

HEAD = b"codeunit 1 T\n{\n#if A\n    procedure P(x: Integer)\n#else\n    procedure P(x: Integer; y: Integer)\n#endif\n"
TAILS = {
    "regular": b"    begin\n    end;\n}\n",
    "var-and-body": b"    var\n        i: Integer;\n    begin\n    end;\n}\n",
    "pragma-only": b"#if B\n#pragma warning disable AL0432\n#endif\n    begin\n    end;\n}\n",
    "split-body": b"#if B\n    var\n        i: Integer;\n    begin\n        i := 1;\n#else\n    begin\n#endif\n        Message('x');\n    end;\n}\n",
    "split-body-else-stmts": b"#if B\n    var\n        i: Integer;\n    begin\n        i := 1;\n#else\n    begin\n        Message('e');\n#endif\n    end;\n}\n",
    "complete-body": b"#if B\n    begin\n        Message('a');\n    end;\n#else\n    begin\n        Message('b');\n    end;\n#endif\n}\n",
}


@pytest.mark.parametrize("tail", sorted(TAILS))
def test_split_procedure_tail(al_parser, tail):
    src = HEAD + TAILS[tail]
    witness.assert_produces(al_parser, src, "preproc_split_procedure")
    v = witness.verdicts(al_parser, src)
    # The tail's own special type may still be milestone-3 (split body). What
    # must never happen is a discrepancy, or a lowering error from split_procedure.
    for c, (s, items) in v.items():
        assert s != "discrepancy", (c, items)
        assert not any(i.startswith("lowering:contract-shape") for i in items), (c, items)


def test_trigger_host_takes_the_same_tails(al_parser):
    src = b"codeunit 1 T\n{\n    trigger OnRun()\n#if B\n#pragma warning disable AL0432\n#endif\n    begin\n    end;\n}\n"
    witness.assert_all_pass(al_parser, src)
```

- [ ] **Step 2: Run the matrix**

Run: `python -m pytest tools/config_oracle/tests/test_split_procedure_matrix.py -q`

For the tails whose special types are supported (regular, var-and-body, pragma-only), also require `witness.assert_all_pass`. Add that assertion for exactly those three.

A failure is either an assembler defect (fix `split_procedure`, and keep its docstring contract true) or a grammar defect (file it for Task 18). Record which in the commit message.

- [ ] **Step 3: Commit**

```bash
git add tools/config_oracle/tests/test_split_procedure_matrix.py tools/config_oracle/lowering/assemblers.py
git commit -m "test(oracle): split-procedure witness matrix over every tail form"
```

---

### Task 16: Replay 6

**Files:**
- Modify: `tools/config_oracle/replay.py`
- Modify: `tools/config_oracle/tests/test_replay.py`
- Modify: `docs/superpowers/specs/2026-09-27-config-consistency-oracle-design.md` (replay table row 6, if Step 1 says so)

Replay 6 is `bc1a366^` over `preproc_split_code_block_end_elif_test.txt`. The base spec says its defect **left a MISSING `end_keyword`**. A MISSING node makes `has_error` true, so the multi-configuration parse is rejected before the structure check runs. That is the same situation as replay 3.

- [ ] **Step 1: Probe what the old parser produces**

```bash
python - <<'EOF'
from tools.config_oracle import replay, fixtures
from tools.query_coverage import loader
p = replay.cached_parser_at("bc1a366^")
for c in fixtures.extract(loader.REPO_ROOT / "test" / "corpus"):
    if c.file == "preproc_split_code_block_end_elif_test.txt":
        t = p.parse(c.source)
        print(c.name[:60], "has_error=", t.root_node.has_error)
EOF
```

- If any case prints `has_error= False` with a wrong tree, detection is `structure`. Add the replay with `detect=lambda recs: any(_has(r, "|structure|") for r in recs)` and a selector for those cases.
- If every case prints `has_error= True`, detection is the has_error backstop, as for replay 3. Add the replay with `detect=lambda recs: any(_has_error_backstop(r) for r in recs)` and a `note` saying so. Then change the base spec's row 6 "Expected detection" to: `on the real old parser: the has_error backstop (the defect left a MISSING end_keyword); not an example of the silent class`.

- [ ] **Step 2: Add the replay and its tests**

Add the replay entry to `REPLAYS` (number 6). Following the file's pattern, add a `slow` test requiring CAUGHT and not masked, and a `head-6` positive control.

- [ ] **Step 3: Verify**

Run: `python -m pytest tools/config_oracle/tests/test_replay.py -q -m slow`, then `python -m tools.config_oracle replay`.
Expected: replays 1 to 6 CAUGHT.

- [ ] **Step 4: Commit**

```bash
git add tools/config_oracle/replay.py tools/config_oracle/tests/test_replay.py docs/superpowers/specs/2026-09-27-config-consistency-oracle-design.md
git commit -m "feat(oracle): replay 6 (#elif in split code-block end)"
```

---

### Task 17: The resolve sweep over four corpora

**Files:**
- Create: `docs/superpowers/plans/2026-09-28-config-oracle-milestone-2-results.md`
- Modify: `tools/config_oracle/fixture-classes.tsv`, only if a sweep finding is a fixture-class matter

- [ ] **Step 1: Run the sweep**

```bash
./tools/ts-lock.sh python -m tools.config_oracle run --tier resolve \
  --root ./BC.History --root ./DC --root H:/Git/BC28.1 --root H:/Git/BCApps-29.0 \
  --report tools/config_oracle/reports/resolve-m2
```

- [ ] **Step 2: Classify every non-pass record**

The exit rule (base milestone 1, spec P1.2): zero `cannot-validate: resolver-*` and zero `reference-error` over flat production AL, or each one investigated. For each reason cluster, find a file and decide which of these it is:
- a resolver defect (fix it, with a regression test in `test_resolve.py`);
- a grammar defect (file it for Task 18);
- invalid source (APAC `ERMPurchaseReportsIII` is known-invalid; check the others with alc);
- an unsupported directive form (for example `&&`, deferred-work item 9).

- [ ] **Step 3: Write the results section**

In the results document, add a "Resolve sweep" section: the command, per corpus the `#if` file count and the records by reason, and the classification table.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/plans/2026-09-28-config-oracle-milestone-2-results.md tools/config_oracle/
git commit -m "docs(oracle): milestone 2 resolve sweep over BC.History, DC, BC28.1, BCApps 29.0"
```

---

### Task 18: First production run, triage, and the milestone record

**Files:**
- Modify: `docs/superpowers/plans/2026-09-28-config-oracle-milestone-2-results.md`
- Modify: `C:\Users\SShadowS\.claude-work\projects\U--Git-tree-sitter-al\memory\project_config_oracle.md`
- Grammar files (`grammar.js`, `src/*`, `test/corpus/*`), **only** for (a)-class findings, each in its own commit

- [ ] **Step 1: Run the full tier over production**

```bash
./tools/ts-lock.sh python -m tools.config_oracle run --tier full \
  --root ./BC.History --root ./DC --root H:/Git/BC28.1 --root H:/Git/BCApps-29.0 \
  --report tools/config_oracle/reports/full-m2
```

Record the elapsed time and peak RSS from the summary. There is no baseline and no gate (base milestone 5).

- [ ] **Step 2: Cluster the discrepancies**

Group the records by `(check, kind, first special type on the path)`. `summary.md` and the report's records file carry the items. Write a short script in the scratchpad, not in the repo. For each cluster, open one member and dump its multi-configuration tree and its reference tree side by side.

- [ ] **Step 3: Triage every cluster**

Classify each one:
- **(a) Grammar defect.** Confirm with an alc probe in every configuration. Fix it in `grammar.js` in its own commit, with a failing-first fixture (expected tree from parse output, plus a renamed-field check that it can fail), and a fresh tree-harness baseline and verify over BC.History and BC28.5. The commit message carries `[BC.History: N errors, X% success]`.
- **(b) Oracle defect.** Fix it in `tools/config_oracle/`, with a regression test.
- **(c) Accepted.** Record the reason, for example a declared one-reading type.

Re-run Step 1 after the fixes until every cluster is (a)-fixed, (b)-fixed or (c)-recorded.

- [ ] **Step 4: Write the milestone record**

The results document gains:
- an exit table with every exit item from the spec and its evidence (command and output line);
- the P6 numbers, per corpus: configurations, pass, discrepancy, and cannot-validate by reason, plus time and memory;
- the triage table;
- the registry state: which types remain `unsupported`, each with its milestone-3 note.

Update the memory file `project_config_oracle.md`: milestone 2 done, the production numbers, milestone 3's first items, and a link to the results document.

- [ ] **Step 5: Final verification**

```bash
python -m pytest tools/config_oracle/tests -q
python -m pytest tools/config_oracle/tests -q -m slow
python -m tools.config_oracle run --tier quick
python -m tools.config_oracle replay
./validate-grammar.sh
```

Expected:
- all tests pass;
- quick tier `discrepancy: 0`;
- replays 1 to 6 CAUGHT;
- validate-grammar green except the stale-WASM step.

- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/plans/2026-09-28-config-oracle-milestone-2-results.md
git commit -m "docs(oracle): milestone 2 results — first production run and triage"
```
