# B7a: Separator and Continuation Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A reproducible audit tool (`python -m tools.b7_audit`) that censuses every separator and
expression boundary in `src/grammar.json`, generates `#if` placements per host route, judges each cell
with alc, the parser and the config oracle, and emits a committed evidence file, a generated matrix
and a ranked defect-family list for B7b+ — with no grammar change.

**Architecture:** A pure census (grammar.json → occurrences, boundaries, routes) gated against a
hand-maintained registry; a literal placement generator with per-configuration validity vectors; a
runner that records per-configuration evidence (alc split/flat + typed control, parser, oracle) into
`evidence.jsonl` with a cache; a pure judge/report stage that turns evidence into verdicts, families and
the matrix deterministically.

**Tech Stack:** Python 3 (stdlib only, plus the repo's py-tree-sitter loader), pytest,
`tools.alc_probe.core`, `tools.config_oracle.{directives,runner}`.

**Spec:** `docs/superpowers/specs/2026-10-06-b7a-separator-continuation-audit-design.md` (rev 2).
Section numbers §N refer to it. Read it fully before any task.

## Global Constraints

- B7a changes no grammar rule, no file under `src/`, and no existing expected tree (§1, §9).
- The goal is the CORRECT tree; an oracle `pass` proves CONSISTENT, not correct (§2).
- Every commit message ends with a MEASURED `[BC.History: N errors, X% success]` line
  (`./tools/ts-lock.sh ./parse-al-parallel.sh ./BC.History/ . 2>&1 | tail -3`).
- Wrap every command that builds or loads `al.dll` in `./tools/ts-lock.sh`.
- alc runs only through `tools.alc_probe.core.compile_project` (its BROKEN/REJECT classification by
  error location is the rule); `MSYS_NO_PATHCONV=1` for CLI runs under Git Bash.
- Never `find /`, never `2>nul`, never `tail -f | grep`; Git Bash with Windows paths.
- `SILENT` reproducers never go into `test/corpus/` (§8); `UNCHECKED` is never folded into
  `CONSISTENT` (§7.2); an oracle `internal-error` fails the run (§7.1).
- `report` output is byte-identical from the committed evidence on any machine (§8, §9).
- Budgets are guidelines, not caps (user, 2026-10-06).

## Review Focus

1. **A helper rule reached from two hosts** (`field_list` from keys and fieldgroups) must yield two
   routes, and the gate must fail when a new caller appears (Task 3 test `test_new_caller_fails_gate`).
2. **A generated input invalid in every configuration by construction** must be caught as a generator
   bug, not recorded as a verdict (Task 5 test `test_every_placement_meets_its_vector` and Task 7's
   `GeneratorBug` path).
3. **alc rejection that is semantic, not syntax** (type error from a mistyped operand) must not be
   reported as parser over-acceptance (Task 7 typed control; Task 8 test `test_semantic_reject_not_over`).
4. **Oracle crash** (`internal-error` item inside a `cannot-validate` record) must abort the run, never
   become `UNCHECKED` (Task 7 test `test_internal_error_aborts`).
5. **Stale structural assertion after a grammar change** must re-open (fingerprint mismatch → the cell is
   `UNCHECKED` again) (Task 8 test `test_fingerprint_mismatch_reopens`).

---

## File Structure

```
tools/b7_audit/
  __init__.py
  __main__.py          CLI: census [--check], run [--only X] [--check] [--accept-tool], report
  grammar.py           grammar.json walking helpers (rule refs, hidden/inline resolution, cycle-safe)
  census.py            occurrences (§3.1), boundaries (§3.2), routes (§3.3) -> dataclasses
  registry.py          load/validate registry.tsv; gate (§4)
  placements.py        literal expansions + validity vectors (§6)
  seeds.py             seed inventory loader + production tree walk (§5)
  evidence.py          runner: alc split/flat + typed control, parser, oracle; cache; evidence.jsonl (§7.1)
  judge.py             verdicts (§7.2), structural assertions + fingerprints (§7.3)
  report.py            families, ranking, matrix markdown (§8)
  registry.tsv         one row per (occurrence|boundary, route)
  assertions.tsv       structural assertions (§7.3)
  seeds/               seed AL files (§5)
  evidence.jsonl       committed canonical evidence (§8)
  tests/
    __init__.py
    conftest.py        re-exports al_parser from tools/config_oracle/tests/conftest.py
    mini_grammar.json  hand-written grammar for census tests
    test_census.py  test_registry.py  test_placements.py  test_evidence.py
    test_judge.py  test_report.py  test_silent.py
docs/b7-separator-continuation-matrix.md   generated
tools/alc_probe/cases/b7-audit/            committed probes for GAP / over-accepts cells
test/corpus/b7_gap_<family>_test.txt       pinned GAP / over-accepts fixtures
```

Shared data shapes (Task 1 defines them in `census.py`; every later task imports them):

```python
@dataclass(frozen=True)
class Occurrence:          # §3.1
    rule: str              # grammar rule name holding the token
    path: str              # dotted member-index path inside the rule, e.g. "1.0.2"
    text: str              # ',', ';', '..', '.', '::', ':'
    context: str           # 'repeat' | 'recursive' | 'caller-repeat' | 'optional' | 'fixed' | 'lexical'

@dataclass(frozen=True)
class Boundary:            # §3.2
    rule: str
    slot: str              # field name, else path
    edge: str              # 'start' | 'end' | 'between'
    mechanisms: tuple      # subset of ('tail', 'tail-operator-only', 'operand-prefix'), sorted
    required: bool         # a mechanism is required (not optional) at this edge

@dataclass(frozen=True)
class Route:               # §3.3
    host: str              # visible rule a user writes (no leading '_')
    chain: tuple           # rule names from host to the occurrence/boundary rule, inclusive

def key_of(x) -> str:      # 'occ:<rule>:<path>' | 'bnd:<rule>:<slot>:<edge>'
```

---

### Task 1: Grammar walker and boundary-occurrence census

**Files:**
- Create: `tools/b7_audit/__init__.py`, `tools/b7_audit/grammar.py`, `tools/b7_audit/census.py`
- Create: `tools/b7_audit/tests/__init__.py`, `tools/b7_audit/tests/conftest.py`,
  `tools/b7_audit/tests/mini_grammar.json`, `tools/b7_audit/tests/test_census.py`

**Interfaces:**
- Produces: `grammar.load(path) -> dict` (the `rules` mapping plus `inline`, `extras`);
  `grammar.iter_nodes(node, path='') -> Iterator[(path, node, ancestors)]`;
  `census.occurrences(g) -> list[Occurrence]` sorted by `key_of`; the dataclasses and `key_of` above.

- [ ] **Step 1: Mini grammar.** Write `tests/mini_grammar.json` (tree-sitter grammar.json format:
  `{"name":"mini","rules":{...},"inline":[...],"extras":[]}`) with rules exercising every context:
  - `list`: `SEQ[SYMBOL item, REPEAT(SEQ[STRING ",", SYMBOL item])]` → repeat
  - `trail`: `SEQ[SYMBOL item, REPEAT(SEQ[STRING ",", SYMBOL item]), CHOICE[STRING ",", BLANK]]` → repeat + optional
  - `rec`: `CHOICE[SYMBOL item, SEQ[SYMBOL item, STRING ";", SYMBOL rec]]` → recursive
  - `_helper`: `SEQ[STRING ",", SYMBOL item]`; `caller`: `REPEAT1(SYMBOL _helper)` → caller-repeat
  - `fixed`: `SEQ[STRING "(", SYMBOL item, STRING ";", SYMBOL item, STRING ")"]` → fixed
  - `tok`: `TOKEN(SEQ[PATTERN "[a-z]+", STRING "::", PATTERN "[a-z]+"])` → lexical
  - `member`: `SEQ[SYMBOL item, STRING ".", SYMBOL item]` → fixed (qualifier)
  - `cyc1`: `SEQ[SYMBOL cyc2]`, `cyc2`: `CHOICE[SYMBOL item, SYMBOL cyc1]` (cycle, no token)
  - `item`: `PATTERN "[a-z]+"`
  - wrap one occurrence in `FIELD`, one in `ALIAS`, one in `PREC_LEFT` to prove those are transparent.

- [ ] **Step 2: Failing tests** in `test_census.py`:
```python
import json
from pathlib import Path
from tools.b7_audit import census, grammar

MINI = Path(__file__).with_name("mini_grammar.json")

def occ(g):
    return {(o.rule, o.text, o.context) for o in census.occurrences(g)}

def test_contexts():
    g = grammar.load(MINI)
    got = occ(g)
    assert ("list", ",", "repeat") in got
    assert ("trail", ",", "repeat") in got and ("trail", ",", "optional") in got
    assert ("rec", ";", "recursive") in got
    assert ("_helper", ",", "caller-repeat") in got
    assert ("fixed", ";", "fixed") in got and ("member", ".", "fixed") in got
    assert ("tok", "::", "lexical") in got           # listed, never dropped

def test_brackets_are_not_boundaries():
    g = grammar.load(MINI)
    assert not any(o.text in "()" for o in census.occurrences(g))

def test_cycle_terminates():
    g = grammar.load(MINI)
    census.occurrences(g)                             # must return, not recurse forever

def test_keys_stable_and_sorted():
    g = grammar.load(MINI)
    a = [census.key_of(o) for o in census.occurrences(g)]
    assert a == sorted(a) and len(a) == len(set(a))

def test_real_grammar_finds_item_30_trailing_comma():
    g = grammar.load(Path("src/grammar.json"))
    got = {(o.rule, o.text, o.context) for o in census.occurrences(g)}
    assert ("_link_value_run", ",", "optional") in got   # deferred item 30, outside the REPEAT
```
  Run `./tools/ts-lock.sh python -m pytest tools/b7_audit/tests/test_census.py -q` → FAIL (no module).

- [ ] **Step 3: Implement.** `grammar.py`:
```python
"""Read-only helpers over tree-sitter's src/grammar.json."""
import json
from pathlib import Path

TRANSPARENT = {"FIELD", "ALIAS", "PREC", "PREC_LEFT", "PREC_RIGHT", "PREC_DYNAMIC", "RESERVED"}
LEXICAL = {"TOKEN", "IMMEDIATE_TOKEN"}

def load(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {"rules": data["rules"], "inline": set(data.get("inline", [])),
            "extras": data.get("extras", [])}

def children(node):
    if "members" in node:
        return list(enumerate(node["members"]))
    if "content" in node:
        return [(0, node["content"])]
    return []

def iter_nodes(node, path="", ancestors=()):
    yield path, node, ancestors
    for i, child in children(node):
        yield from iter_nodes(child, f"{path}.{i}" if path else str(i), ancestors + (node,))
```
  `census.py` — `occurrences(g)`: for each rule, `iter_nodes`; a `STRING` whose value is in
  `(",", ";", "..", ".", "::", ":")` is an occurrence. Context, first match wins:
  `lexical` if any ancestor type is in `LEXICAL`; `repeat` if any ancestor is `REPEAT`/`REPEAT1`;
  `optional` if the nearest non-transparent ancestor is a `CHOICE` with a `BLANK` member;
  `recursive` if the rule can reach itself through `SYMBOL` references (cycle-safe DFS over
  `SYMBOL` names, memoised) AND the STRING sits in a `SEQ` that also holds such a `SYMBOL`;
  `caller-repeat` if the rule is referenced by some other rule inside a `REPEAT`/`REPEAT1`;
  else `fixed`. Path is the dotted member index. Return sorted by `key_of`.

- [ ] **Step 4:** Run the tests → PASS. Also print the real-grammar count:
  `python -c "from tools.b7_audit import census,grammar; o=census.occurrences(grammar.load('src/grammar.json')); import collections; print(len(o), collections.Counter(x.context for x in o))"`
  and record it in the task report.

- [ ] **Step 5: Commit** `feat(b7a): census of boundary occurrences` (measured trailer).

---

### Task 2: Expression-boundary census (per edge, with mechanisms)

**Files:** Modify `tools/b7_audit/census.py`, `tools/b7_audit/tests/mini_grammar.json`,
`tools/b7_audit/tests/test_census.py`

**Interfaces:**
- Consumes: Task 1 walker.
- Produces: `census.boundaries(g) -> list[Boundary]` sorted by `key_of`.

- [ ] **Step 1: Extend the mini grammar** with `_expression` (CHOICE of `item`), a
  `preproc_conditional_expression_tail` rule (CHOICE of two SEQs: `SEQ[STRING "#if", ...]` for the
  suffix form and `SEQ[SYMBOL _preproc_operator_arms, FIELD operand _expression]` for the operator-only
  form), a `preproc_operand_prefix` rule, and hosts:
  - `assign`: `SEQ[FIELD left _expression, STRING ":=", FIELD right _expression, CHOICE[SYMBOL preproc_conditional_expression_tail, BLANK]]`
  - `loop`: `SEQ[STRING "for", FIELD start _expression, STRING "to", FIELD end _expression, CHOICE[SYMBOL preproc_conditional_expression_tail, BLANK], STRING "do"]`
  - `idx`: `SEQ[SYMBOL item, STRING "[", FIELD index _expression, CHOICE[SYMBOL preproc_conditional_expression_tail, BLANK], REPEAT(SEQ[STRING ",", FIELD index _expression]), STRING "]"]`
  - `req`: `SEQ[FIELD value _expression, SYMBOL preproc_conditional_expression_tail]` (required)
  - `until`: `SEQ[STRING "until", FIELD condition _expression]` (no mechanism)
  - `binop`: `SEQ[FIELD left _expression, STRING "or", CHOICE[SYMBOL preproc_operand_prefix, BLANK], FIELD right _expression]`

- [ ] **Step 2: Failing tests:**
```python
def bnd(g):
    return {(b.rule, b.slot, b.edge): (b.mechanisms, b.required) for b in census.boundaries(g)}

def test_edges_and_mechanisms():
    b = bnd(grammar.load(MINI))
    assert b[("assign", "right", "end")] == (("tail", "tail-operator-only"), False)
    assert b[("loop", "end", "end")][0] == ("tail", "tail-operator-only")
    assert b[("loop", "start", "end")][0] == ()          # tail is after `end`, not `start`
    assert b[("idx", "index", "end")][0] != ()           # first index has the tail
    assert b[("idx", "index", "between")][0] == ()       # later indices do not
    assert b[("req", "value", "end")] == (("tail", "tail-operator-only"), True)
    assert b[("until", "condition", "end")][0] == ()
    assert ("operand-prefix",) == b[("binop", "right", "start")][0]

def test_real_grammar_until_has_no_mechanism():
    b = bnd(grammar.load(Path("src/grammar.json")))
    hits = [k for k, (m, _) in b.items() if k[0] == "repeat_statement" and k[2] == "end"]
    assert hits and all(b[k][0] == () for k in hits)     # deferred item 39, shape 1
```
  Run → FAIL.

- [ ] **Step 3: Implement** `boundaries(g)`: for each rule, every `SYMBOL _expression` (or a SYMBOL to a
  hidden rule whose body is exactly `SYMBOL _expression` or a FIELD of it) yields `start` and `end`
  boundaries; the slot is the enclosing `FIELD` name or the path; a FIELD with the same name already seen
  earlier in the same rule inside a `REPEAT` makes the later one `between`. Mechanisms at `end`: the
  next sibling in the enclosing `SEQ` (skipping transparent wrappers) is `SYMBOL
  preproc_conditional_expression_tail` → `("tail", "tail-operator-only")` (the tail rule has both
  forms; read its CHOICE members to decide which of the two forms exist), `required` when it is not
  wrapped in `CHOICE[..., BLANK]`. Mechanism at `start`: the previous sibling is
  `CHOICE[SYMBOL preproc_operand_prefix, BLANK]` or `SYMBOL preproc_operand_prefix` → `("operand-prefix",)`.
- [ ] **Step 4:** Tests PASS; record the real-grammar boundary count and per-mechanism counts in the report.
- [ ] **Step 5: Commit** `feat(b7a): expression-boundary census per edge`.

---

### Task 3: Host routes and the registry gate

**Files:** Modify `census.py`; create `tools/b7_audit/registry.py`, `tools/b7_audit/__main__.py`,
`tools/b7_audit/tests/test_registry.py`; create `tools/b7_audit/registry.tsv` (header only for now).

**Interfaces:**
- Produces: `census.routes(g, target_rule) -> list[Route]` (all visible hosts reaching `target_rule`,
  cycle-safe, shortest chain per host, sorted); `census.census(g) -> list[tuple[str, Route]]` = every
  (key, route) pair for occurrences and boundaries; `registry.load(path) -> list[Row]` with
  `Row(key, route_host, role, family, template, equiv, reason)`; `registry.gate(pairs, rows) ->
  (missing: list, stale: list, invalid: list)`; CLI `python -m tools.b7_audit census --check` exits
  0 / 1 / 2 per §4.

- [ ] **Step 1: Failing tests:**
```python
from tools.b7_audit import census, grammar, registry

def test_helper_reached_from_two_hosts():
    g = grammar.load(MINI)
    g["rules"]["host_a"] = {"type": "SEQ", "members": [{"type": "STRING", "value": "a"}, {"type": "SYMBOL", "name": "caller"}]}
    g["rules"]["host_b"] = {"type": "SEQ", "members": [{"type": "STRING", "value": "b"}, {"type": "SYMBOL", "name": "caller"}]}
    hosts = {r.host for r in census.routes(g, "_helper")}
    assert {"host_a", "host_b"} <= hosts

def test_new_caller_fails_gate():
    g = grammar.load(MINI)
    rows = [registry.Row(k, r.host, "list-separator", "f", "x ⟨HOLE⟩", "", "") for k, r in census.census(g)]
    assert registry.gate(census.census(g), rows) == ([], [], [])
    g["rules"]["host_new"] = {"type": "SEQ", "members": [{"type": "STRING", "value": "n"}, {"type": "SYMBOL", "name": "list"}]}
    missing, stale, invalid = registry.gate(census.census(g), rows)
    assert any(r.host == "host_new" for _, r in missing)

def test_stale_row_fails_gate():
    g = grammar.load(MINI)
    rows = [registry.Row("occ:gone:0", "gone", "list-separator", "f", "x ⟨HOLE⟩", "", "")]
    _, stale, _ = registry.gate([], rows)
    assert stale

def test_na_requires_reason():
    rows = [registry.Row("occ:list:1.0.0", "list", "na", "", "", "", "")]
    _, _, invalid = registry.gate([("occ:list:1.0.0", census.Route("list", ("list",)))], rows)
    assert invalid
```
  (Rule: `na`, `lexical` and any non-empty `equiv` require a non-empty `reason`; a `list-separator`,
  `edge-separator`, `fixed-separator`, `terminator` or `continuation` row requires a `template`
  containing exactly one `⟨HOLE⟩` and a `family`.) Run → FAIL.

- [ ] **Step 2: Implement** `routes` (reverse SYMBOL index; BFS from `target_rule` upward to rules not
  starting with `_` and not in `inline`; a visible target is its own host), `census.census`,
  `registry.load` (TSV with a header line `key\troute\trole\tfamily\ttemplate\tequiv\treason`;
  `#`-comments allowed; templates use `\n` escapes for newlines), `registry.gate`, and the CLI
  (`argparse`, subcommand `census` with `--check` and `--list` printing every key/route one per line).
- [ ] **Step 3:** Tests PASS. Run `python -m tools.b7_audit census --list | wc -l` on the real grammar
  and record the pair count; `census --check` now exits 1 (registry empty) — expected until Task 4.
- [ ] **Step 4: Commit** `feat(b7a): host routes and registry gate`.

---

### Task 4: Populate the registry

**Files:** Modify `tools/b7_audit/registry.tsv`.

**Interfaces:** Consumes Task 3's `census --list`. Produces a complete registry (`census --check`
exit 0) that Tasks 5-10 read.

- [ ] **Step 1:** `python -m tools.b7_audit census --list > <scratchpad>/pairs.txt`. For every pair
  write one row. Role from §4; `family` names the grammar construct a fix would touch (e.g.
  `link-list`, `option-members`, `parameter-list`, `implements`, `key-fields`, `ml-pairs`,
  `namespace-pairs`, `case-patterns`, `where-filter`, `repeat-until`, `foreach-in`, `with`,
  `assignment`, `if-condition`, ...). `lexical` and `na` rows carry a reason a reviewer can check.
  `equiv` only with an argument naming the shared rule AND why host context does not change parse
  states or conditional attachment (cite the rule and the scanner token involved, if any).
- [ ] **Step 2: Templates.** Each template is a complete self-contained AL object compilable by alc
  (no Base App symbols; use a local table `T` with fields `K: Code[20]`, `N: Integer`,
  `B: Boolean`, local procedures). The `⟨HOLE⟩` stands where the list or the expression goes. Typed:
  Boolean slots (`if`, `while`, `until` conditions) take Boolean expressions; lvalue slots take an lvalue.
  For every template, compile it once with a known-valid plain filling via
  `MSYS_NO_PATHCONV=1 python -c "from tools.alc_probe import core; ..."` (or a throwaway alc_probe case
  in the scratchpad) and record ACCEPT in the task report — a template that does not compile plain is
  a bug that would poison every cell.
- [ ] **Step 3:** `python -m tools.b7_audit census --check` → exit 0.
- [ ] **Step 4: Commit** `feat(b7a): registry for every census pair` with the row count per role and
  the template-compile summary in the body.

---

### Task 5: Placement generator with validity vectors

**Files:** Create `tools/b7_audit/placements.py`, `tools/b7_audit/tests/test_placements.py`.

**Interfaces:**
- Consumes: `registry.Row`.
- Produces: `placements.Cell(id: str, key: str, host: str, placement: str, source: str, symbols:
  tuple[str, ...], intended_valid: frozenset[frozenset[str]], hole: tuple[int, int], plain: str)`
  (an assignment = frozenset of defined symbols; `hole` = byte range of the filled hole in `source`;
  `plain` = the template filled with a plain, directive-free valid filling, used by Task 7's control);
  `placements.assignments(symbols) -> list[frozenset[str]]` (every subset, sorted);
  `placements.well_formed_list(text, sep) -> bool`; `placements.cells_for(row) -> list[Cell]` (empty for `na`/`lexical`/`equiv` rows, with the
  skipped placements and reasons available as `placements.skipped_for(row) -> list[(placement, reason)]`).

- [ ] **Step 1: Failing tests:**
```python
from tools.config_oracle.directives import resolve
from tools.b7_audit import placements, registry

ROW = registry.Row("occ:x:0", "x", "list-separator", "f", "codeunit 50100 P { procedure Q() var A, B, C, D: Integer; begin Foo(⟨HOLE⟩); end; procedure Foo(A: Integer; B: Integer; C: Integer) begin end; }", "", "")

def flat(cell, env):
    return resolve(cell.source.encode(), env).masked.decode()

def test_sep_before_shape():
    c = {c.placement: c for c in placements.cells_for(ROW)}["sep-before"]
    assert "#if X" in c.source and c.symbols == ("X",)
    assert "A" in flat(c, frozenset()) and "B" not in flat(c, frozenset()).split("Foo(")[1]

def test_every_placement_meets_its_vector():
    # by construction: every intended-valid assignment flattens to a list with no doubled,
    # leading or trailing separator (unless the host allows holes), every other assignment does not
    for c in placements.cells_for(ROW):
        for env in placements.assignments(c.symbols):
            text = flat(c, env).split("Foo(", 1)[1].split(")", 1)[0]
            well_formed = placements.well_formed_list(text, ",")
            assert well_formed == (env in c.intended_valid), (c.placement, sorted(env), text)

def test_semi_in_arms_only_for_statement_hosts():
    cont = registry.Row("bnd:if_statement:condition:end", "if_statement", "continuation", "if-condition", "codeunit 50100 P { procedure Q() var B: Boolean; begin if ⟨HOLE⟩ then; end; }", "", "")
    assert "semi-in-arms" not in {c.placement for c in placements.cells_for(cont)}
    assert ("semi-in-arms", "host is not a statement whose expression may end it") in placements.skipped_for(cont)
```
  Run → FAIL.
- [ ] **Step 2: Implement** every placement of §6.1 and §6.2 literally, as format strings over element
  samples, each with its `intended_valid` computed from the placement's declared vector ("all",
  "X only", "per host" via the row's role). `assignments(symbols)` returns every subset. Element samples
  per role come from the row's template context: list elements `A B C D` (or the host-specific
  `elements` derived from the template: e.g. `K = field(K)` for link lists — define a small
  per-family sample table in `placements.py`), operators per §6.2 families with typed operands
  (Boolean operands for logical, Integer for arithmetic/comparison, a Record/Interface for `is`/`as`,
  a list literal for `in`). `semi-in-arms` only for roles whose family is `assignment`, `call`, or
  `exit` (item 39 shape kept literally: `#if X op F; Foo(); #else ; #endif`).
  `well_formed_list(text, sep)`: tokens split on top-level `sep`, no empty token unless the host allows
  holes.
- [ ] **Step 3:** Tests PASS. Print the cell count per role on the real registry; record it.
- [ ] **Step 4: Commit** `feat(b7a): placement generator with validity vectors`.

---

### Task 6: Seed inventory

**Files:** Create `tools/b7_audit/seeds.py`, `tools/b7_audit/seeds/*.al`,
`tools/b7_audit/tests/test_seeds.py` (in `test_placements.py` if small).

**Interfaces:** Produces `seeds.load() -> list[Cell]` (placement `seed:<name>`, intended_valid from the
seed file's `// valid:` header listing assignments, e.g. `// valid: X, !X`) and
`seeds.production_shapes(roots) -> dict[(host, placement_class), int]` (tree walk).

- [ ] **Step 1:** Copy verbatim, one file each, with a `// source:` line: the reproducers of deferred
  items 1 (the link reproducer), 2 (both placements), 30, 39 (both, item 39's assignment WITH the
  following `Foo();`); every case of `test/corpus/property_value_run_b13_gap_test.txt`; item 38's shape;
  and every committed alc case under `tools/alc_probe/cases/{g11-item1-link-comma-leading,g11-item17-hosts,g11-item18-link,g11-item18-option,g11-item19-relation,link-keying,pair-list-keying,value-runs,expression-statement}`
  whose source holds a `#if` next to a separator or an expression edge (a seed keeps the case's own
  `// expect:` verdicts as its `// valid:` line).
- [ ] **Step 2: Production walk.** `production_shapes(roots)`: parse every `.al` under each root with
  the repo loader; for every `preproc_*` node whose previous or next named sibling is a separator token
  or an expression edge of a census route, classify the placement class (`sep-before`, `sep-after`,
  `lead-optional`, `trail`, `suffix`, `prefix`, other) and count by (host, class). Test on a two-file
  temp directory with known shapes.
- [ ] **Step 3:** Run over `./BC.History ./DC H:/Git/BC28.1 H:/Git/BCApps-29.0`; write the counts to
  the task report (they feed Task 9's ranking via the evidence header).
- [ ] **Step 4: Commit** `feat(b7a): seed inventory and production shape walk`.

---

### Task 7: Evidence runner

**Files:** Create `tools/b7_audit/evidence.py`, `tools/b7_audit/tests/test_evidence.py`; extend
`__main__.py` with `run [--only FAMILY|KEY] [--check] [--accept-tool] [--jobs N]`.

**Interfaces:**
- Consumes: `Cell` (Tasks 5, 6), `tools.alc_probe.core.compile_project`, `core.compiler_identity`,
  `tools.config_oracle.directives.resolve`, `tools.config_oracle.runner.check_input`, the repo loader.
- Produces: `evidence.measure(cell, parser, alc) -> list[dict]` (one record per assignment):
```python
{"cell": cell.id, "key": cell.key, "host": cell.host, "placement": cell.placement,
 "config": "X" | "!X" | "X,!Y" ...,        # config_id
 "source_sha256": "...", "intended_valid": True|False,
 "alc_split": {"verdict": "ACCEPT|REJECT", "codes": [...]},
 "alc_flat":  {"verdict": ..., "codes": [...]},
 "alc_control": {"verdict": ..., "codes": [...]},   # typed control: same config, hole filled plain
 "reject_class": "syntax" | "semantic" | None,
 "parser_has_error": bool, "error_in_hole": bool,
 "oracle": {"status": "pass|discrepancy|representation-violation|directive-mismatch|cannot-validate", "items": [...]}}
```
  plus `evidence.write(records, header, path)` (header line first: `{"header": {alc identity, runtime,
  corpus manifests, parser sha256s}}`, then records sorted by (cell, config), LF, keys sorted) and
  `evidence.read(path)`. Exceptions: `GeneratorBug` (an intended-valid assignment that alc rejects with a
  syntax code AND whose plain control also fails, i.e. the template, not the placement, is invalid;
  or an intended-invalid assignment that alc accepts where the vector is "all invalid"), `OracleCrash`
  (any oracle item starting `internal-error`), `ProbeBroken` (any BROKEN verdict or split/flat MISMATCH).

- [ ] **Step 1: Failing tests** with a fake alc runner (`core.compile_project` accepts `runner=`):
```python
def fake(verdicts):          # map flat text substring -> (kind, codes)
    ...
def test_internal_error_aborts(monkeypatch, al_parser):
    monkeypatch.setattr("tools.config_oracle.runner.check_input",
        lambda *a, **k: [type("R", (), {"config_id": "X", "status": "cannot-validate", "items": ["internal-error:boom"]})()])
    with pytest.raises(evidence.OracleCrash):
        evidence.measure(CELL, al_parser, alc=FAKE_ACCEPT)

def test_broken_project_aborts(al_parser):
    with pytest.raises(evidence.ProbeBroken):
        evidence.measure(CELL, al_parser, alc=FAKE_BROKEN)

def test_reject_class_from_control(al_parser):
    recs = evidence.measure(CELL, al_parser, alc=FAKE_TYPE_ERROR)   # split/flat reject AL0175, control accepts
    assert {r["reject_class"] for r in recs if r["alc_flat"]["verdict"] == "REJECT"} == {"semantic"}

def test_cache_hit_skips_compile(tmp_path, al_parser):
    ...  # second measure() with the same cache dir performs 0 compiles (count calls on the fake)

def test_records_sorted_and_deterministic(tmp_path):
    ...  # write() twice with shuffled input -> identical bytes
```
  (Read `tools/config_oracle/runner.py` `Record` for the real attribute names before writing the
  monkeypatch: use its actual field names.) Run → FAIL.
- [ ] **Step 2: Implement.** Per cell: `assignments(cell.symbols)`; flat text per assignment with
  `resolve(...).masked`; split compile with `symbols=sorted(env)`; flat compile with no symbols; control
  = the flat text with the hole region replaced by the row's plain filling (store the plain filling on
  the Cell as `plain: str`, set by Task 5 from the template); syntax codes = `{AL0104, AL0107, AL0111,
  AL0224, AL0125}` (document the set at the top of the module); `reject_class` = `syntax` if any flat
  code is in the set and the control ACCEPTs, `semantic` if the flat rejects with no syntax code and the
  control ACCEPTs, else raise `GeneratorBug`. Parser: `has_error` and whether an ERROR/MISSING node's
  byte range intersects the hole's byte range. Oracle: `runner.check_input(parser, cell.id,
  cell.source.encode())`, map each record to its config. Cache key = sha256(source + config + runtime +
  alc identity) → JSON file under `.cache/b7_audit/`. Parallelism: a `ThreadPoolExecutor(jobs)` over
  compile calls (alc_probe's default 6).
- [ ] **Step 3:** Tests PASS.
- [ ] **Step 4: Commit** `feat(b7a): evidence runner (alc split/flat/control, parser, oracle, cache)`.

---

### Task 8: Judge and structural assertions

**Files:** Create `tools/b7_audit/judge.py`, `tools/b7_audit/assertions.tsv` (header),
`tools/b7_audit/tests/test_judge.py`.

**Interfaces:**
- Consumes: evidence records (Task 7).
- Produces: `judge.verdict(records_of_cell, assertion) -> Verdict(name, detail)` with names from §7.2
  (`CONSISTENT GAP SILENT MIXED REJECTED UNCHECKED`) and REJECTED sub-verdicts `syntax/agrees`,
  `syntax/over-accepts`, `semantic/agrees`, `semantic/over-accepts`; `judge.load_assertions(path)`;
  `judge.check_assertion(tree_root, source, assertion) -> bool`; fingerprints
  `(cell_sha256, parser_c_sha256, scanner_c_sha256, oracle_sha256)`.
  `assertions.tsv` columns: `cell_or_class`, `expect` (an s-expression fragment with fields, matched as
  a subtree of the split tree, e.g. `(argument_list (preproc_conditional_arguments ...))`), `fingerprints`,
  `reason`.

- [ ] **Step 1: Failing tests:**
```python
def test_gap():
    assert judge.verdict(recs(alc="ACCEPT", err=True), None).name == "GAP"
def test_silent_from_oracle():
    assert judge.verdict(recs(alc="ACCEPT", err=False, oracle="discrepancy"), None).name == "SILENT"
def test_unchecked_never_consistent():
    assert judge.verdict(recs(alc="ACCEPT", err=False, oracle="cannot-validate"), None).name == "UNCHECKED"
def test_consistent_needs_assertion():
    assert judge.verdict(recs(alc="ACCEPT", err=False, oracle="pass"), None).name == "UNCHECKED"
    assert judge.verdict(recs(alc="ACCEPT", err=False, oracle="pass"), HOLDS).name == "CONSISTENT"
def test_mixed():
    assert judge.verdict(recs_mixed(), None).name == "MIXED"
def test_semantic_reject_not_over():
    v = judge.verdict(recs(alc="REJECT", reject_class="semantic", err=False), None)
    assert (v.name, v.detail) == ("REJECTED", "semantic/over-accepts")   # out of scope, not a defect
def test_fingerprint_mismatch_reopens():
    a = assertion(fingerprints=("old", "old", "old", "old"))
    assert judge.verdict(recs(alc="ACCEPT", err=False, oracle="pass"), a).name == "UNCHECKED"
def test_assertion_mutation_can_fail(al_parser):
    # a correct assertion holds; the same with a field renamed to `bogus` does not
    ...
```
  Run → FAIL.
- [ ] **Step 2: Implement** per §7.2 (MIXED cells: judge each accepted configuration as if alone and
  record the per-config sub-verdicts in `detail`). `check_assertion`: parse the expected fragment
  (minimal s-expression reader: `(type field: (type ...) ...)`), and search the split tree for a node
  matching it (type, named children in order, fields where given). Fingerprint mismatch ⇒ assertion
  ignored.
- [ ] **Step 3:** Tests PASS. **Step 4: Commit** `feat(b7a): verdicts and structural assertions`.

---

### Task 9: Report, families and ranking

**Files:** Create `tools/b7_audit/report.py`, `tools/b7_audit/tests/test_report.py`; extend
`__main__.py` with `report [--out PATH]`.

**Interfaces:** Consumes evidence (Task 7), registry (Task 4), assertions (Task 8), production counts
(evidence header, Task 6). Produces `docs/b7-separator-continuation-matrix.md` (default `--out`).

- [ ] **Step 1: Failing tests:** `test_report_deterministic` (same evidence → byte-identical output,
  run twice, and with records shuffled); `test_families_dedupe` (two cells, same family and same
  verdict → one family row listing both); `test_unchecked_listed_separately` (an UNCHECKED cell never
  appears in the ranked list); `test_rank_order` (a SILENT family ranks above a GAP family with more
  cells; among GAP families, more defective production sites rank first; a family with an unmet
  dependency ranks after the family it depends on).
- [ ] **Step 2: Implement** the matrix: header (tool identity and corpus manifests from the evidence
  header), totals per verdict, one table per role (rows = host route, columns = placements, cell =
  verdict abbreviation), a families section (per family: cells, hosts, defective production sites,
  dependencies from a small `DEPENDENCIES` dict in `report.py` — at least `link-list-comma-leading`
  → `link-property-ambiguity` per roadmap B7 —, owner: `B7b+` or `B12`/`B13` for cells whose seed or
  family is one of deferred items 36, 37, 38), the ranked fix list (§8 order), and the UNCHECKED list
  with refusal reasons. Deterministic: sort everything, no timestamps, LF.
- [ ] **Step 3:** Tests PASS. **Step 4: Commit** `feat(b7a): matrix report, families, ranking`.

---

### Task 10: The full run and its artifacts

**Files:** Create `tools/b7_audit/evidence.jsonl`, `docs/b7-separator-continuation-matrix.md`,
`tools/alc_probe/cases/b7-audit/*.al`, `test/corpus/b7_gap_<family>_test.txt`,
`tools/b7_audit/tests/test_silent.py`; modify `tools/b7_audit/assertions.tsv`,
`tools/deliberate-negatives.txt`, `tools/config_oracle/fixture-classes.tsv`.

- [ ] **Step 1: Run.** `MSYS_NO_PATHCONV=1 ./tools/ts-lock.sh python -m tools.b7_audit run --jobs 6`
  (hours cold; use `--only` per family to iterate). Fix every `GeneratorBug`/`ProbeBroken` at its source
  (template or placement), never by editing evidence. `OracleCrash` stops the task: report it.
- [ ] **Step 2: Close UNCHECKED cells.** For each UNCHECKED cell or uniform class, read the split
  tree against the flat reading of each configuration and add an assertion row with fingerprints
  (`python -m tools.b7_audit assert --cell <id>` may print the current tree and the fingerprints to
  copy; implement that helper here if useful). A tree that is wrong becomes `SILENT` (add the
  assertion that fails and say why in `reason`). A cell left UNCHECKED stays listed with its refusal.
- [ ] **Step 3: Artifacts per cell.**
  - `GAP` and `REJECTED syntax/over-accepts`: one alc probe in `tools/alc_probe/cases/b7-audit/`
    (`// expect:` per assignment, measured) and one case in `test/corpus/b7_gap_<family>_test.txt`
    (expected tree from `python tools/snip.py --raw --sexp -f`, read; header names the verdict and the
    defect); add each new corpus file to `tools/deliberate-negatives.txt`; run the oracle quick tier and
    classify its new records (`debt(B7)` for GAP; `negative:` with alc evidence for over-accepts cells
    whose configurations alc rejects).
  - `SILENT`: a parametrized case in `tools/b7_audit/tests/test_silent.py` asserting the cell's current
    oracle finding or failing assertion (the fix flips it to require pass). Nothing in `test/corpus/`.
- [ ] **Step 4:** `python -m tools.b7_audit report` and commit the evidence, matrix, assertions,
  probes, fixtures and bookkeeping together (measured trailer; body: totals per verdict and the top of
  the ranked list).

---

### Task 11: Gates, deferred-work and docs

**Files:** Modify `validate-grammar.sh` (new step after 5f: `census --check`),
`.github/workflows/*.yml` (the job that runs the quick gates — find it with `grep -l traversal_census
.github/workflows/*`), `docs/deferred-work.md` (items 1, 2 rewritten from the matrix; 30, 39
cross-referenced), `docs/superpowers/plans/2026-09-28-roadmap-remaining-work.md` (row B7: B7a DONE,
the ranked list as B7b+), `CLAUDE.md` (Quick Reference: the three `tools.b7_audit` commands, one line
each), `CHANGELOG.md` (`### Added`: the audit tool and gate).

- [ ] **Step 1:** Add the validate step (exit-code handling like Step 5f) and the CI step; run
  `./validate-grammar.sh` → the new step ✓.
- [ ] **Step 2:** Docs as listed; deferred items keep their old record "as written" below the rewrite.
- [ ] **Step 3: Final gates:** `census --check` 0; `report` byte-identical to the committed matrix
  (`git diff --exit-code docs/b7-separator-continuation-matrix.md` after regenerating); `run --check`
  0 (slow); alc_probe `--check` over `cases/b7-audit` clean; `tree-sitter test` total = previous +
  cases added; has_error sweep `--corpus-fixtures` clean; oracle quick tier 0;
  `./validate-grammar.sh --full` green; `git diff main -- grammar.js src/` empty.
- [ ] **Step 4: Commit** `docs(b7a): audit gate, matrix-driven deferred items, roadmap`.
