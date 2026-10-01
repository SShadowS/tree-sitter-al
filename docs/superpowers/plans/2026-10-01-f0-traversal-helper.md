# F0: Classified Traversal Helper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One hand-maintained traversal policy and one `walk`/`SplitInfo`/`bind_arm` helper in Python, JavaScript (native and WASM) and Rust, so every consumer can step through every `#if` arm of the all-branches tree and recognise split constructs, with the three runtimes proven identical on shared fixtures.

**Architecture:** `traversal/policy.json` classifies every special node type into one of the seven classes of spec §6.1, with host policies, the source of each arm boundary and a reason. It ships in every package the way `queries/*.scm` do. Each runtime reads it; there is no code generation. Arm boundaries come from the P1 tree's own `#if`/`#elif`/`#else`/`#endif` nodes (spec §5.1 layers 1 and 3), never from a resolver or a configuration. `tools/traversal_census.py` gates the policy against `src/node-types.json` and `tools/config_oracle/contracts.py`; witnesses, canaries and per-runtime parity tests run against `tests/traversal/`.

**Tech Stack:** Python 3.12+ stdlib (py-tree-sitter 0.25 objects, duck-typed); plain CommonJS for native `tree-sitter` ^0.25.0 and `web-tree-sitter` ^0.27.0; Rust 2021 with optional `tree-sitter` `>=0.25, <0.27` and `serde_json` 1 behind a `traversal` feature; pytest 9, `node --test`, `cargo test`.

**Spec:** `docs/superpowers/specs/2026-10-01-configuration-aware-parse-design.md` (§5.1 layers 1 and 3, §6, §7.1, §9 row F0). Consumer evidence: `.superpowers/sdd/a7/consumers.md`; LethAL `U:/Git/LethAL/docs/roadmap/R214.md`.

**Verified while planning.** Every code block in this plan was run against `git archive` of `main` at 0a8e220, in a scratch directory. The numbers quoted as "Expected" (test counts, byte offsets, sha256s) are what those runs printed: Python 244 tests, JS 34 under both runtimes, Rust 5 plus a doc test on tree-sitter 0.25.10 and 0.26.13, clippy clean, a Python sdist and an npm tarball installed clean outside the checkout. If a number differs when you run it, stop and find out why before going on; do not adjust the expectation.

## Global Constraints

- The policy is data: ONE file, `traversal/policy.json`, schema `1`, shipped in every package. No per-runtime codegen (D1).
- Exactly seven classes: `ordinary`, `branch-container`, `assembler`, `fragment`, `token-alias`, `directive`, `trivia` (spec §6.1).
- "Name prefixes are **never** used as a classification rule" (spec §6.1). No walker source names a node type; the census detects special types from structure and the registry (D2).
- F0 uses §5.1 layers 1 and 3 only: "no configuration and no resolver". Arm boundaries come from the P1 tree's own directive nodes (D3).
- Every position a helper reports is a canonical UTF-8 byte offset, in every runtime (spec "Terms", §4.2).
- `src/` is not touched and no grammar rule changes (D9). `src/node-types.json` stays the canonical file at its existing location, "always generated from the full grammar" (spec §7.1). At the end, `git diff --stat 0a8e220 -- src grammar.js` is empty.
- Rust: the helper is `tree_sitter_al::traversal`, behind a cargo feature `traversal`, **off by default**, adding `tree-sitter` at `>=0.25, <0.27` and `serde_json` `1` (D6, spec §7.1). The plain `LANGUAGE` export is unchanged.
- Python: `requires-python >=3.12`; py-tree-sitter at the ranges `tools/check-runtime-ranges.py` accepts (`~=0.25`, tools pin `0.25.2`). The module imports nothing outside the stdlib.
- Node: ONE pure-JS implementation for both runtimes; it never requires the native addon, so it is browser-safe (D5, spec §7.1). Declared runtimes: native `tree-sitter` `^0.25.0`, `web-tree-sitter` `^0.27.0`, Node 18 and 24 in CI.
- F0 ships additively in the next major release with a CHANGELOG `[Unreleased]` entry; no backport to 4.x (spec §9, D9).
- Anything that builds or loads the shared compiled parser runs under `./tools/ts-lock.sh` (CLAUDE.md).
- `.gitignore` ignores `*.py` and `*.al` globally: every new tracked `.py`/`.al` needs a negation, and every task that adds files checks `git ls-files` against `find` (CLAUDE.md "A corpus file can also be invisible to git").
- Generated files cannot fail a contract (CLAUDE.md): the `*.visits.json` files only make the runtimes agree with Python; hand-written assertions (Tasks 2–4) are what say Python is right. Regenerating them is a `-u`: read every hunk.
- Stage files by name, never `git add -A`. Commits touch no grammar, so they carry no BC.History count; the last task runs the validators and records the result.

## Review Focus

1. **Non-ASCII text before or inside a group.** Both JS runtimes index UTF-16; a fixture with `Æ`, `ø`, `å` and `😀` ahead of every group must give the same UTF-8 offsets as Python and Rust. Pinned by `containers.al` in Task 2 (hand-written offsets) and Tasks 6–7 (parity), plus the `byteTable` surrogate test in Task 6.
2. **CRLF line endings and a leading BOM.** An arm starts after `\r\n`; the BOM is three bytes; `.gitattributes` must keep the fixture CRLF in every checkout. Pinned by `crlf_bom.al` in Task 2, a `git check-attr` step in Task 2, and parity in Tasks 6–7.
3. **Directives that do not pair up in a real tree.** An `#if` under an ERROR node never closed, and a stray `#endif` that parses CLEAN as `preproc_split_block_close_after_endif`: no crash, the open group runs to end of file, the stray one is `unpaired`, and the assembler holding only it gets no `SplitInfo`. Pinned by `unbalanced.al` and `stray_endif.al` in Task 2 and parity.
4. **A descriptor used against another document** (another file, or the same file after an edit). `bind_arm` must refuse it in all three runtimes. Pinned in Task 3 (Python), Task 6 (JS), Task 7 (Rust).
5. **Large and deep input.** Thousands of groups in one body made the first version quadratic (4.4 s for 2,000 groups, measured); deep expression nesting must not hit a recursion limit. Pinned by a timed test in Task 2 (2,000 groups under 3 s, 5,000 nested parentheses).

---

## File Structure

| Path | Responsibility | Task |
|---|---|---|
| `traversal/policy.json` | the hand-maintained policy, shipped in every package | 1 |
| `tools/traversal_census.py` | gate: policy vs `src/node-types.json` vs `contracts.REGISTRY` | 1 |
| `tests/traversal/support.py`, `conftest.py` | paths, loading the module by path, the parser, fixtures | 1 |
| `tests/traversal/test_census.py` | census tests, including the D2 mutation and the no-prefix proofs | 1 |
| `bindings/python/tree_sitter_al/traversal.py` | Python walker: policy, group index, `walk`, `SplitInfo`, `bind_arm` | 2, 3, 5 |
| `tests/traversal/fixtures/*.al` | the twelve shared fixtures | 2 |
| `tests/traversal/test_walk.py`, `test_split.py` | hand-written walker and `SplitInfo` assertions | 2, 3 |
| `tests/traversal/witnesses.tsv`, `test_witnesses.py` | one witness per policy entry, the named exceptions, each with a mutant | 4 |
| `tests/traversal/fixtures/*.visits.json`, `regen_expected.py`, `test_parity.py` | the shared expected visits (D4) | 5 |
| `traversal/index.js`, `traversal/index.d.ts` | the ONE JS implementation and its types | 6 |
| `tests/traversal/js/parity.test.js` | JS under native `tree-sitter` and `web-tree-sitter` | 6 |
| `bindings/rust/traversal.rs` | Rust walker and its tests | 7 |
| `tests/traversal/test_canaries.py`, `tests/traversal/js/canaries.test.js` | consumer canaries (D7) | 8 |
| `MANIFEST.in`, `setup.py`, `package.json`, `.github/workflows/ci.yml` | packaging and CI | 9 |
| `docs/traversal.md`, `CHANGELOG.md`, `CLAUDE.md` | docs (D10) | 10 |

Modified, not created: `.gitignore`, `.gitattributes`, `validate-grammar.sh` (new Step 5f), `tools/gate_selftest.py`, `Cargo.toml`, `bindings/rust/lib.rs`, `tools/check-runtime-ranges.py`, `tools/tests/test_check_runtime_ranges.py`, `package-lock.json`.

### Shared interfaces (all tasks)

Python (`tree_sitter_al.traversal`; tests load it by path as `tree_sitter_al_traversal`):

```text
SCHEMA = 1; CLASSES: tuple[str, ...]; SPLIT_CLASSES = ("branch-container", "assembler", "fragment")
class PolicyError(ValueError); class WrongDocument(ValueError)
@dataclass Policy(types: dict): cls(type) -> str ("ordinary" when unlisted); role(type) -> str|None;
                                host_policy(container, parent, field) -> str|None
load_policy(path=None) -> Policy        # None: the packaged tree_sitter_al/traversal_policy.json
fnv1a64(data: bytes) -> str             # 16 lowercase hex digits: the document revision
@dataclass Directive(role, start, end, node)
@dataclass ArmDescriptor(group_id: (revision, if_offset), arm_id, directive_offsets: tuple, raw_range: (start, end))
@dataclass Group(if_offset, directives: tuple[Directive], arms: tuple[ArmDescriptor])
@dataclass Fragment(field, node) + .type; ArmFragments(descriptor, fragments); GroupArms(group_id, arms)
@dataclass SplitInfo(groups: tuple[GroupArms], shared: tuple[Fragment])
@dataclass Visit(node, cls, type, field, start, end, arms: tuple[(if_offset, arm_id)], host, split)
class Document(tree, source: bytes, policy): .tree .source .revision .groups .unpaired; descriptors()
groups_of(node, document) -> list[Group]
bind_arm(descriptor, document, policy) -> ArmFragments      # raises WrongDocument
split_info(node, document, policy) -> SplitInfo | None
walk(document, policy, *, root=None, include_directives=False, include_trivia=False) -> list[Visit]
split_to_json(SplitInfo) -> dict; visits_to_json(visits) -> list[dict]; dump_expected(document, visits) -> str
```

JavaScript (`@sshadows/tree-sitter-al/traversal`): the same names in camelCase — `loadPolicy(data?)`, `Policy#cls/role/hostPolicy`, `new Document(tree, text, policy)` with `.revision .groups .unpaired .start(node) .end(node) .index(byte) .descriptors()`, `groupsOf`, `bindArm`, `splitInfo`, `walk(doc, policy, {root, includeDirectives, includeTrivia})`, `visitsToJson(visits, doc)`, `fnv1a64(bytes)`, `byteTable(text)`. Objects: descriptor `{groupId: [rev, off], armId, directiveOffsets, rawRange: [s, e]}`, group `{ifOffset, directives, arms}`, fragment `{field, node}`, visit `{node, cls, type, field, start, end, arms: [[off, arm]], host, split}`.

Rust (`tree_sitter_al::traversal`, feature `traversal`): `Policy::{from_json, bundled, class, role, host_policy}`, `POLICY_JSON`, `fnv1a64`, `Document::new(&Tree, &[u8], &Policy)`, `groups_of`, `bind_arm -> Result<ArmFragments, WrongDocument>`, `split_info`, `walk(&Document, &Policy, Option<Node>, WalkOptions) -> Vec<Visit>`, `visits_to_json(&[Visit]) -> serde_json::Value`.

The parity form, one object per visit, identical in all three: `{"class", "type", "field", "start", "end", "arms": [[if_offset, arm_id], ...], "host", "split": null | {"groups": [{"if": off, "arms": [{"arm": i, "range": [s, e], "fragments": [[field, type, named, start, end], ...]}]}], "shared": [[field, type, named, start, end], ...]}}`.

---

### Task 1: The policy file and its census gate

**Files:**
- Create: `traversal/policy.json`, `tools/traversal_census.py`, `tests/traversal/support.py`, `tests/traversal/conftest.py`, `tests/traversal/test_census.py`
- Modify: `.gitignore` (append), `validate-grammar.sh` (new Step 5f between Step 5e and Step 6, around line 573), `tools/gate_selftest.py:92` (`COPY_DIRS`) and its `CASES` list (after the `step5e-oracle-discrepancy` case, around line 735)

**Interfaces:**
- Consumes: `tools.config_oracle.contracts.REGISTRY` (`Entry.kind`, `.hosts`, `.alias_to`) and `contracts.host_slots(node_types, type_name) -> set[str]`; `tools.config_oracle.fixtures.extract(root) -> list[Case]` (`Case.id`, `Case.source`); `tools.query_coverage.loader` (`ensure_library`, `load_language`, `make_parser`, `REPO_ROOT`).
- Produces: `traversal/policy.json` (schema above, 89 entries); `traversal_census.census(policy: dict, node_types: list, registry: dict, host_slots) -> list[str]`; CLI `python tools/traversal_census.py [--root DIR]` exiting 0 clean, 1 finding, 2 cannot run; pytest fixtures `T`, `policy`, `al_parser`, `parse(name) -> Document`, `corpus`, `doc_of(spec) -> Document` (the `T`-based ones resolve once Task 2 exists); `support.REPO`, `support.FIXTURES`, `support.MODULE`, `support.POLICY`, `support.load_traversal()`, `support.make_parser()`.

- [ ] **Step 1: Let git see the new Python and AL files**

Append to `.gitignore`:

```gitignore

# The traversal helper (roadmap F0). `*.py` and `*.al` above would swallow its Python
# module, its tests and the AL fixtures every runtime's tests share -- silently, and
# only in a fresh clone (CLAUDE.md: "A corpus file can also be invisible to git").
!bindings/python/tree_sitter_al/*.py
!tests/traversal/*.py
!tests/traversal/fixtures/*.al
tests/traversal/__pycache__/
```

Run: `git check-ignore -q tests/traversal/conftest.py; echo $?; git check-ignore -q tests/traversal/fixtures/x.al; echo $?; git check-ignore -q bindings/python/tree_sitter_al/traversal.py; echo $?`
Expected: `1` three times (1 = not ignored).

- [ ] **Step 2: Write the test support and the failing census tests**

`tests/traversal/support.py`:

```python
"""Shared by conftest.py and regen_expected.py: paths, the module under test, a parser.

The traversal module is loaded BY PATH, not imported as tree_sitter_al.traversal:
importing the package runs tree_sitter_al/__init__.py, which needs the compiled
_binding extension, and these tests use the repo's own parser library instead
(tools/query_coverage/loader.py, the same one every other Python gate uses).
"""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
FIXTURES = HERE / "fixtures"
MODULE = REPO / "bindings" / "python" / "tree_sitter_al" / "traversal.py"
POLICY = REPO / "traversal" / "policy.json"

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def load_traversal():
    name = "tree_sitter_al_traversal"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, MODULE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module          # dataclasses resolve annotations through sys.modules
    spec.loader.exec_module(module)
    return module


def make_parser():
    from tools.query_coverage import loader
    return loader.make_parser(loader.load_language(loader.ensure_library(loader.REPO_ROOT)))
```

`tests/traversal/conftest.py`:

```python
import pytest

import support


@pytest.fixture(scope="session")
def T():
    return support.load_traversal()


@pytest.fixture(scope="session")
def policy(T):
    return T.load_policy(support.POLICY)


@pytest.fixture(scope="session")
def al_parser():
    return support.make_parser()


@pytest.fixture(scope="session")
def parse(T, policy, al_parser):
    """A fixture file under tests/traversal/fixtures -> Document."""
    def _parse(name):
        src = (support.FIXTURES / name).read_bytes()
        return T.Document(al_parser.parse(src), src, policy)
    return _parse


@pytest.fixture(scope="session")
def corpus():
    from tools.config_oracle import fixtures
    return {c.id: c for c in fixtures.extract(support.REPO / "test" / "corpus")}


@pytest.fixture(scope="session")
def doc_of(T, policy, al_parser, corpus):
    """`corpus:<Case.id>` or `fixture:<file>` -> Document. A witness must parse clean."""
    def _doc(spec):
        kind, _, ref = spec.partition(":")
        src = corpus[ref].source if kind == "corpus" else (support.FIXTURES / ref).read_bytes()
        tree = al_parser.parse(src)
        assert not tree.root_node.has_error, f"witness {spec} has an ERROR or MISSING node"
        return T.Document(tree, src, policy)
    return _doc
```

`tests/traversal/test_census.py`:

```python
"""tools/traversal_census.py (F0, D2): the policy against node-types.json and the registry."""
import copy
import importlib.util
import json
import re
import subprocess
import sys

import pytest

import support
from tools.config_oracle import contracts

SCRIPT = support.REPO / "tools" / "traversal_census.py"
_spec = importlib.util.spec_from_file_location("traversal_census", SCRIPT)
census_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(census_mod)


def policy():
    return json.loads(support.POLICY.read_text(encoding="utf-8"))


def node_types():
    return json.loads((support.REPO / "src" / "node-types.json").read_text(encoding="utf-8"))


def run(pol=None, nt=None, registry=None):
    return census_mod.census(pol or policy(), nt or node_types(), registry or contracts.REGISTRY,
                             contracts.host_slots)


def test_census_is_clean_against_the_shipped_grammar():
    assert run() == []


def test_cli_exits_0_and_reports_the_entry_count():
    p = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr
    assert re.search(r"traversal census: \d+ entries, 0 problem\(s\)", p.stdout)


def test_cli_exits_2_when_the_policy_is_missing(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "node-types.json").write_text("[]")
    p = subprocess.run([sys.executable, str(SCRIPT), "--root", str(tmp_path)], capture_output=True, text=True)
    assert p.returncode == 2, p.stdout + p.stderr


def test_expression_tail_misclassified_as_a_container_fails():
    """The D2 mutation: the spec's first-named exception, given the wrong class."""
    pol = policy()
    pol["types"]["preproc_conditional_expression_tail"]["class"] = "branch-container"
    problems = run(pol)
    assert ("class disagrees with the registry: preproc_conditional_expression_tail is branch-container, "
            "registry kind assembler means assembler") in problems


def test_an_unprefixed_type_holding_a_directive_is_detected():
    """Detection is structural: no name rule could find this type."""
    nt = node_types() + [{"type": "brand_new_split", "named": True, "children": {
        "multiple": True, "required": True,
        "types": [{"type": "preproc_if", "named": True}, {"type": "preproc_endif", "named": True}]}}]
    assert run(nt=nt) == ["unclassified: brand_new_split (holds a conditional directive)"]


def test_a_preproc_named_type_with_no_signal_is_not_flagged():
    """The converse: a `preproc_` name alone classifies nothing. (Its registry entry is
    contracts.census's job, which is prefix-based by design; this gate is not.)"""
    nt = copy.deepcopy(node_types()) + [{"type": "preproc_lookalike", "named": True}]
    for t in nt:
        if t["type"] == "statement_block":
            t["children"]["types"].append({"type": "preproc_lookalike", "named": True})
    assert run(nt=nt) == []


def test_an_unregistered_unprefixed_fragment_is_detected_through_its_parents():
    pol = policy()
    del pol["types"]["else_table_relation_fragment"]
    registry = {k: v for k, v in contracts.REGISTRY.items() if k != "else_table_relation_fragment"}
    assert run(pol, registry=registry) == [
        "unclassified: else_table_relation_fragment (only ever a child of special types)"]


def test_a_stale_entry_fails():
    pol = policy()
    pol["types"]["gone_type"] = {"class": "assembler", "arm_boundary": "none", "reason": "gone"}
    assert "stale entry, type no longer declared: gone_type" in run(pol)


def test_a_host_policy_that_disagrees_with_the_registry_fails():
    pol = policy()
    pol["types"]["preproc_conditional_permissions"]["hosts"]["tabledata_permission_list:<children>"] = "splice-repeat"
    assert run(pol) == ["host policy disagrees with the registry: preproc_conditional_permissions in "
                        "tabledata_permission_list:<children>: splice-repeat vs list-run"]


def test_a_hand_classified_container_host_slot_is_checked_against_node_types():
    """case_patterns is registry-unsupported, so its hosts come from the policy alone."""
    pol = policy()
    del pol["types"]["preproc_conditional_case_patterns"]["hosts"]["case_branch:<children>"]
    assert run(pol) == ["host slot not classified: preproc_conditional_case_patterns in case_branch:<children>"]


def test_an_unsupported_registry_type_may_not_be_ordinary():
    pol = policy()
    pol["types"]["preproc_split_key"]["class"] = "ordinary"
    assert "registry-unsupported type classified ordinary: preproc_split_key" in run(pol)


def test_arm_boundary_is_checked_against_the_declared_children():
    pol = policy()
    pol["types"]["preproc_split_block_end_in_else"]["arm_boundary"] = "own-directives"
    assert run(pol) == ["arm_boundary of preproc_split_block_end_in_else is own-directives, "
                        "its declared children say cross-node"]


@pytest.mark.parametrize("field, value", [("reason", " "), ("class", "special")])
def test_entry_shape_is_enforced(field, value):
    pol = policy()
    pol["types"]["pragma"][field] = value
    assert run(pol)


def test_no_traversal_source_classifies_by_name():
    """D2: classification is never by prefix. The walkers name no node type at all."""
    sources = [support.MODULE, support.REPO / "traversal" / "index.js",
               support.REPO / "bindings" / "rust" / "traversal.rs", SCRIPT]
    for path in sources:
        if not path.exists():
            continue                     # the JS and Rust walkers arrive in later tasks
        text = path.read_text(encoding="utf-8").split("#[cfg(test)]")[0]   # Rust: not its tests
        assert not re.search(r"(startswith|startsWith|starts_with)\(\s*['\"]preproc", text), path
        if path != SCRIPT:
            assert "preproc" not in text, f"{path.name} names a node type"
```

- [ ] **Step 3: Run the tests to see them fail**

Run: `./tools/ts-lock.sh python -m pytest tests/traversal/test_census.py -q`
Expected: a collection ERROR, `FileNotFoundError: [Errno 2] No such file or directory: '...tools/traversal_census.py'`.

- [ ] **Step 4: Write the policy**

Create `traversal/policy.json` with exactly this content (2-space indent, LF, final newline). The 27 registry-`unsupported` types are classified by hand here: 25 as `assembler` (their arms are pieces of one construct) and `preproc_conditional_case_patterns` / `preproc_conditional_impl_values` as `branch-container` with `list-run` hosts. `comment` and `multiline_comment` are extras the census detects, classified `ordinary` because comment consumers need them in every arm.

```json
{
  "schema": 1,
  "types": {
    "comment": {
      "class": "ordinary",
      "arm_boundary": "none",
      "reason": "Extra, but source content: comment consumers need it in every arm."
    },
    "else_table_relation_fragment": {
      "class": "fragment",
      "arm_boundary": "assembler",
      "reason": "Exception (spec 6.1): a fragment with no prefix; completes the relation before the #if it sits in."
    },
    "multiline_comment": {
      "class": "ordinary",
      "arm_boundary": "none",
      "reason": "Extra, but source content: comment consumers need it in every arm."
    },
    "pragma": {
      "class": "trivia",
      "arm_boundary": "none",
      "reason": "Exception (spec 6.1): not in the contracts registry; an extra, so it can sit inside any arm. Skipped by walk unless include_trivia."
    },
    "preproc_and_expression": {
      "class": "directive",
      "arm_boundary": "none",
      "reason": "Conditional-directive line or a piece of one; walk skips it unless include_directives."
    },
    "preproc_close": {
      "class": "directive",
      "arm_boundary": "none",
      "reason": "Conditional-directive line or a piece of one; walk skips it unless include_directives."
    },
    "preproc_conditional": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "action_group_body:<children>": "splice-repeat",
        "controladdin_body:<children>": "splice-repeat",
        "dataset_mod_body:<children>": "splice-repeat",
        "declaration_body:<children>": "splice-repeat",
        "interface_body:<children>": "splice-repeat",
        "layout_container_body:<children>": "splice-repeat",
        "preproc_conditional:<children>": "splice-repeat",
        "preproc_conditional_controladdin:<children>": "splice-repeat",
        "preproc_conditional_layout_mixed:<children>": "splice-repeat",
        "preproc_conditional_query:<children>": "splice-repeat",
        "preproc_conditional_report:<children>": "splice-repeat",
        "preproc_conditional_xmlport:<children>": "splice-repeat",
        "preproc_split_var_section_tail:<children>": "splice-repeat",
        "query_body:<children>": "splice-repeat",
        "report_body:<children>": "splice-repeat",
        "xmlport_body:<children>": "splice-repeat"
      },
      "reason": "Registry branch-select: arms are alternatives in one host slot."
    },
    "preproc_conditional_actions": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "action_body:<children>": "splice-repeat",
        "action_group_body:<children>": "splice-repeat",
        "preproc_conditional_actions:<children>": "splice-repeat"
      },
      "reason": "Registry branch-select: arms are alternatives in one host slot."
    },
    "preproc_conditional_arguments": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "argument_list:<children>": "list-run"
      },
      "reason": "Registry branch-select: arms are alternatives in one host slot."
    },
    "preproc_conditional_case": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "case_body:<children>": "splice-repeat"
      },
      "reason": "Registry branch-select: arms are alternatives in one host slot."
    },
    "preproc_conditional_case_patterns": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "case_branch:<children>": "list-run",
        "preproc_conditional_case_patterns:<children>": "list-run",
        "preproc_split_case_branch:<children>": "list-run",
        "preproc_split_case_extended:<children>": "list-run",
        "preproc_split_case_statement_end:<children>": "list-run"
      },
      "reason": "Arms are alternative case-pattern runs in one pattern list; registry unsupported (milestone 3), classified here by hand."
    },
    "preproc_conditional_controladdin": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "controladdin_body:<children>": "splice-repeat",
        "preproc_conditional_controladdin:<children>": "splice-repeat"
      },
      "reason": "Registry branch-select: arms are alternatives in one host slot."
    },
    "preproc_conditional_dataset": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "dataset_body:<children>": "splice-repeat"
      },
      "reason": "Registry branch-select: arms are alternatives in one host slot."
    },
    "preproc_conditional_expression_tail": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Exception (spec 6.1): an assembler whose continuation comes after #endif; the tail extends the expression BEFORE it, so its arms are not complete expressions."
    },
    "preproc_conditional_fieldgroups": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "fieldgroups_body:<children>": "splice-repeat",
        "preproc_conditional_fieldgroups:<children>": "splice-repeat"
      },
      "reason": "Registry branch-select: arms are alternatives in one host slot."
    },
    "preproc_conditional_fields": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "fields_body:<children>": "splice-repeat",
        "preproc_conditional_fields:<children>": "splice-repeat",
        "preproc_split_table_field_open:<children>": "splice-repeat"
      },
      "reason": "Registry branch-select: arms are alternatives in one host slot."
    },
    "preproc_conditional_impl_values": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "implementation_value_list:<children>": "list-run",
        "preproc_conditional_impl_values:<children>": "list-run"
      },
      "reason": "Arms are alternative runs of implementation values in one list; registry unsupported (milestone 3), classified here by hand."
    },
    "preproc_conditional_keys": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "keys_body:<children>": "splice-repeat",
        "preproc_conditional_keys:<children>": "splice-repeat",
        "preproc_split_key:<children>": "splice-repeat"
      },
      "reason": "Registry branch-select: arms are alternatives in one host slot."
    },
    "preproc_conditional_labels": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "labels_body:<children>": "splice-repeat"
      },
      "reason": "Registry branch-select: arms are alternatives in one host slot."
    },
    "preproc_conditional_layout": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "layout_body:<children>": "splice-repeat",
        "layout_container_body:<children>": "splice-repeat",
        "preproc_conditional_layout:<children>": "splice-repeat",
        "preproc_conditional_layout_mixed:<children>": "splice-repeat",
        "preproc_split_brace_close:<children>": "splice-repeat",
        "preproc_split_brace_close_if_only:<children>": "splice-repeat"
      },
      "reason": "Registry branch-select: arms are alternatives in one host slot."
    },
    "preproc_conditional_layout_mixed": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "layout_container_body:<children>": "splice-repeat"
      },
      "reason": "Registry branch-select: arms are alternatives in one host slot."
    },
    "preproc_conditional_link_values": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "link_value_list:<children>": "list-run",
        "preproc_conditional_link_values:<children>": "list-run"
      },
      "reason": "Registry branch-select: arms are alternatives in one host slot."
    },
    "preproc_conditional_list_elements": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "list_literal:<children>": "list-run"
      },
      "reason": "Registry branch-select: arms are alternatives in one host slot."
    },
    "preproc_conditional_object": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "preproc_conditional_object:<children>": "splice-repeat",
        "source_file:<children>": "splice-repeat"
      },
      "reason": "Registry branch-select: arms are alternatives in one host slot."
    },
    "preproc_conditional_option_members": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "option_member_list:<children>": "list-run"
      },
      "reason": "Registry branch-select: arms are alternatives in one host slot."
    },
    "preproc_conditional_permissions": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "preproc_conditional_permissions:<children>": "list-run",
        "tabledata_permission_list:<children>": "list-run"
      },
      "reason": "Registry branch-select: arms are alternatives in one host slot."
    },
    "preproc_conditional_property_value": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Exception (spec 6.1): an assembler; each arm is the whole property value and the arm may carry the property's own ';' (contract whole-value-select)."
    },
    "preproc_conditional_query": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "preproc_conditional_query:<children>": "splice-repeat",
        "query_body:<children>": "splice-repeat"
      },
      "reason": "Registry branch-select: arms are alternatives in one host slot."
    },
    "preproc_conditional_rendering": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "rendering_body:<children>": "splice-repeat"
      },
      "reason": "Registry branch-select: arms are alternatives in one host slot."
    },
    "preproc_conditional_report": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "preproc_conditional_report:<children>": "splice-repeat",
        "report_body:<children>": "splice-repeat"
      },
      "reason": "Registry branch-select: arms are alternatives in one host slot."
    },
    "preproc_conditional_statement": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "asserterror_statement:body": "optional-slot",
        "case_branch:body": "single-slot",
        "for_statement:body": "single-slot",
        "foreach_statement:body": "single-slot",
        "if_statement:else_branch": "single-slot",
        "if_statement:then_branch": "single-slot",
        "preproc_conditional_statement:<children>": "splice-repeat",
        "preproc_fragmented_else_tail:<children>": "splice-repeat",
        "preproc_guarded_statement:then_branch": "single-slot",
        "preproc_split_block_close_after_endif:<children>": "splice-repeat",
        "preproc_split_block_end_in_else:<children>": "splice-repeat",
        "preproc_split_case_branch:body": "single-slot",
        "preproc_split_case_end_branch:body": "single-slot",
        "preproc_split_case_extended:body": "single-slot",
        "preproc_split_code_block_end:<children>": "splice-repeat",
        "preproc_split_code_block_over_endif:<children>": "splice-repeat",
        "preproc_split_else_begin_over_endif:<children>": "splice-repeat",
        "preproc_split_if_begin_asymmetric:<children>": "splice-repeat",
        "preproc_split_if_begin_else:<children>": "splice-repeat",
        "preproc_split_if_else_statement:else_branch": "single-slot",
        "preproc_split_if_else_statement:then_branch": "single-slot",
        "preproc_split_if_statement:else_branch": "single-slot",
        "preproc_split_if_statement:then_branch": "single-slot",
        "preproc_split_if_then_begin:<children>": "splice-repeat",
        "preproc_split_if_then_begin_else_shared:<children>": "splice-repeat",
        "preproc_split_open_statement:<children>": "splice-repeat",
        "preproc_split_open_statement:continuation": "single-slot",
        "preproc_split_open_statement:then_branch": "single-slot",
        "statement_block:<children>": "splice-repeat",
        "while_statement:body": "single-slot",
        "with_statement:body": "single-slot"
      },
      "reason": "Registry branch-select: arms are alternatives in one host slot."
    },
    "preproc_conditional_table_relation": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Exception (spec 6.1): an assembler; each arm continues the relation before it (contract else-relation-join)."
    },
    "preproc_conditional_var": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "var_body:<children>": "splice-repeat"
      },
      "reason": "Registry branch-select: arms are alternatives in one host slot."
    },
    "preproc_conditional_var_block": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "preproc_split_procedure:<children>": "optional-slot",
        "preproc_split_procedure_preamble:<children>": "optional-slot",
        "procedure:<children>": "optional-slot",
        "trigger_declaration:<children>": "optional-slot"
      },
      "reason": "Registry branch-select: arms are alternatives in one host slot."
    },
    "preproc_conditional_where": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "preproc_conditional_where:<children>": "list-run",
        "where_conditions:<children>": "list-run"
      },
      "reason": "Registry branch-select: arms are alternatives in one host slot."
    },
    "preproc_conditional_xmlport": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "preproc_conditional_xmlport:<children>": "splice-repeat",
        "xmlport_body:<children>": "splice-repeat"
      },
      "reason": "Registry branch-select: arms are alternatives in one host slot."
    },
    "preproc_define": {
      "class": "trivia",
      "arm_boundary": "none",
      "reason": "Line-level directive that is an extra; walk skips it unless include_trivia."
    },
    "preproc_elif": {
      "class": "directive",
      "arm_boundary": "none",
      "role": "elif",
      "reason": "Conditional-directive line or a piece of one; walk skips it unless include_directives."
    },
    "preproc_else": {
      "class": "directive",
      "arm_boundary": "none",
      "role": "else",
      "reason": "Conditional-directive line or a piece of one; walk skips it unless include_directives."
    },
    "preproc_endif": {
      "class": "directive",
      "arm_boundary": "none",
      "role": "endif",
      "reason": "Conditional-directive line or a piece of one; walk skips it unless include_directives."
    },
    "preproc_endregion": {
      "class": "trivia",
      "arm_boundary": "none",
      "reason": "Line-level directive that is an extra; walk skips it unless include_trivia."
    },
    "preproc_fragmented_else_tail": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry unsupported (milestone 3); classified by hand: arms are pieces of one construct, not complete units."
    },
    "preproc_guarded_statement": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry unsupported (milestone 3); classified by hand: arms are pieces of one construct, not complete units."
    },
    "preproc_if": {
      "class": "directive",
      "arm_boundary": "none",
      "role": "if",
      "reason": "Conditional-directive line or a piece of one; walk skips it unless include_directives."
    },
    "preproc_not_expression": {
      "class": "directive",
      "arm_boundary": "none",
      "reason": "Conditional-directive line or a piece of one; walk skips it unless include_directives."
    },
    "preproc_open": {
      "class": "directive",
      "arm_boundary": "none",
      "reason": "Conditional-directive line or a piece of one; walk skips it unless include_directives."
    },
    "preproc_operand_prefix": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry assembler: one construct built from arm fragments plus shared parts."
    },
    "preproc_or_expression": {
      "class": "directive",
      "arm_boundary": "none",
      "reason": "Conditional-directive line or a piece of one; walk skips it unless include_directives."
    },
    "preproc_parenthesized_expression": {
      "class": "directive",
      "arm_boundary": "none",
      "reason": "Conditional-directive line or a piece of one; walk skips it unless include_directives."
    },
    "preproc_pragma_only": {
      "class": "branch-container",
      "arm_boundary": "own-directives",
      "hosts": {
        "field_declaration:<children>": "splice-repeat",
        "preproc_split_procedure:<children>": "splice-repeat",
        "procedure:<children>": "splice-repeat",
        "source_file:<children>": "splice-repeat",
        "trigger_declaration:<children>": "splice-repeat"
      },
      "reason": "Registry branch-select whose arms hold only extras (pragmas, comments); every arm is empty of structure."
    },
    "preproc_region": {
      "class": "trivia",
      "arm_boundary": "none",
      "reason": "Line-level directive that is an extra; walk skips it unless include_trivia."
    },
    "preproc_split_begin": {
      "class": "token-alias",
      "arm_boundary": "none",
      "alias_to": "begin_keyword",
      "reason": "Exception (spec 6.1): a token alias; a 'begin' lexed at #if depth > 0 just before #endif. Treat as begin_keyword."
    },
    "preproc_split_block_close_after_endif": {
      "class": "assembler",
      "arm_boundary": "cross-node",
      "reason": "A group that crosses a node boundary: only the #endif is here; the #if is in the previous procedure's preproc_split_block_end_in_else."
    },
    "preproc_split_block_end_in_else": {
      "class": "assembler",
      "arm_boundary": "cross-node",
      "reason": "A group that crosses a node boundary: #if/#else here, #endif inside the NEXT procedure's preproc_split_block_close_after_endif."
    },
    "preproc_split_brace_close": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry unsupported (milestone 3); classified by hand: arms are pieces of one construct, not complete units."
    },
    "preproc_split_brace_close_if_only": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry unsupported (milestone 3); classified by hand: arms are pieces of one construct, not complete units."
    },
    "preproc_split_call_statement": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry unsupported (milestone 3); classified by hand: arms are pieces of one construct, not complete units."
    },
    "preproc_split_case_branch": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry unsupported (milestone 3); classified by hand: arms are pieces of one construct, not complete units."
    },
    "preproc_split_case_end_branch": {
      "class": "fragment",
      "arm_boundary": "assembler",
      "reason": "Exception (spec 6.1): a fragment; one arm of preproc_split_case_statement_end (the case's own end plus the statements after it)."
    },
    "preproc_split_case_extended": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry unsupported (milestone 3); classified by hand: arms are pieces of one construct, not complete units."
    },
    "preproc_split_case_statement_end": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry assembler: one construct built from arm fragments plus shared parts."
    },
    "preproc_split_code_block_end": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry assembler: one construct built from arm fragments plus shared parts."
    },
    "preproc_split_code_block_over_endif": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry unsupported (milestone 3); classified by hand: arms are pieces of one construct, not complete units."
    },
    "preproc_split_complete_body": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry unsupported (milestone 3); classified by hand: arms are pieces of one construct, not complete units."
    },
    "preproc_split_container_reopen": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry assembler: one construct built from arm fragments plus shared parts."
    },
    "preproc_split_declaration": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry unsupported (milestone 3); classified by hand: arms are pieces of one construct, not complete units."
    },
    "preproc_split_else_begin_over_endif": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry assembler: one construct built from arm fragments plus shared parts."
    },
    "preproc_split_end": {
      "class": "token-alias",
      "arm_boundary": "none",
      "alias_to": "end_keyword",
      "reason": "Exception (spec 6.1): a token alias; an 'end' lexed at #if depth > 0 before ';' and a directive. Treat as end_keyword."
    },
    "preproc_split_field": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry unsupported (milestone 3); classified by hand: arms are pieces of one construct, not complete units."
    },
    "preproc_split_if_begin_asymmetric": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry unsupported (milestone 3); classified by hand: arms are pieces of one construct, not complete units."
    },
    "preproc_split_if_begin_else": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry unsupported (milestone 3); classified by hand: arms are pieces of one construct, not complete units."
    },
    "preproc_split_if_else_statement": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry unsupported (milestone 3); classified by hand: arms are pieces of one construct, not complete units."
    },
    "preproc_split_if_statement": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry unsupported (milestone 3); classified by hand: arms are pieces of one construct, not complete units."
    },
    "preproc_split_if_then_begin": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry unsupported (milestone 3); classified by hand: arms are pieces of one construct, not complete units."
    },
    "preproc_split_if_then_begin_else_shared": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry unsupported (milestone 3); classified by hand: arms are pieces of one construct, not complete units."
    },
    "preproc_split_key": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry unsupported (milestone 3); classified by hand: arms are pieces of one construct, not complete units."
    },
    "preproc_split_modify": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry unsupported (milestone 3); classified by hand: arms are pieces of one construct, not complete units."
    },
    "preproc_split_open_statement": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry assembler: one construct built from arm fragments plus shared parts."
    },
    "preproc_split_permissions_property": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry unsupported (milestone 3); classified by hand: arms are pieces of one construct, not complete units."
    },
    "preproc_split_procedure": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry assembler: one construct built from arm fragments plus shared parts."
    },
    "preproc_split_procedure_body": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry unsupported (milestone 3); classified by hand: arms are pieces of one construct, not complete units."
    },
    "preproc_split_procedure_preamble": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry unsupported (milestone 3); classified by hand: arms are pieces of one construct, not complete units."
    },
    "preproc_split_report_brace_close": {
      "class": "fragment",
      "arm_boundary": "own-directives",
      "reason": "Exception (spec 6.1): a fragment; a report_dataitem's closing brace that sits inside one arm. It carries its own #if group."
    },
    "preproc_split_report_dataitem_header": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry unsupported (milestone 3); classified by hand: arms are pieces of one construct, not complete units."
    },
    "preproc_split_report_dataitem_open_over_endif": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry assembler: one construct built from arm fragments plus shared parts."
    },
    "preproc_split_table_field": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry unsupported (milestone 3); classified by hand: arms are pieces of one construct, not complete units."
    },
    "preproc_split_table_field_open": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry unsupported (milestone 3); classified by hand: arms are pieces of one construct, not complete units."
    },
    "preproc_split_var_section_tail": {
      "class": "assembler",
      "arm_boundary": "own-directives",
      "reason": "Registry assembler: one construct built from arm fragments plus shared parts."
    },
    "preproc_undef": {
      "class": "trivia",
      "arm_boundary": "none",
      "reason": "Line-level directive that is an extra; walk skips it unless include_trivia."
    }
  }
}
```

Run: `sha256sum traversal/policy.json`
Expected: `37a2583143bf10059101d05d16834f833343a919ae22ec356ec9402d86997313  traversal/policy.json`

- [ ] **Step 5: Write the census**

`tools/traversal_census.py`:

```python
#!/usr/bin/env python3
"""traversal_census.py -- the traversal policy against the grammar and the registry (F0, D2).

traversal/policy.json is hand-maintained and ships in every package. This gate fails
when the grammar or the contracts registry has moved and the policy has not:

  * a named type in src/node-types.json that is not ordinary has no entry;
  * an entry names a type the grammar no longer declares;
  * the policy and tools/config_oracle/contracts.py disagree where the registry has
    an opinion (kind -> class, token-alias target, branch-container host policies).

"Not ordinary" is DETECTED from structure and from the registry -- a type that holds a
conditional directive, an extra, a registry entry, or a type only ever found under
special types -- and never from a name. A detected type may still be classified
`ordinary` (comment is); what it may not be is unclassified.

Exit: 0 clean; 1 a finding; 2 cannot run (a file missing or unreadable).

    python tools/traversal_census.py [--root DIR]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CLASSES = ("ordinary", "branch-container", "assembler", "fragment", "token-alias", "directive", "trivia")
BOUNDARIES = ("own-directives", "cross-node", "assembler", "none")
ROLES = ("if", "elif", "else", "endif")
KIND_TO_CLASS = {"directive": "directive", "trivia": "trivia", "token-alias": "token-alias",
                 "branch-select": "branch-container", "assembler": "assembler", "fragment": "fragment"}


def _children(t: dict) -> set:
    specs = list(t.get("fields", {}).values()) + ([t["children"]] if "children" in t else [])
    return {x["type"] for spec in specs for x in spec.get("types", [])}


def census(policy: dict, node_types: list, registry: dict, host_slots) -> list:
    """Every problem, as one line each. `registry` is contracts.REGISTRY, `host_slots`
    is contracts.host_slots: passed in so a test can hand over a modified copy."""
    problems = []
    if policy.get("schema") != 1:
        problems.append(f"policy schema {policy.get('schema')!r}, expected 1")
    types = policy.get("types", {})
    named = {t["type"] for t in node_types if t.get("named")}
    kids = {t["type"]: _children(t) for t in node_types if t.get("named")}

    roles = {}
    for name, e in sorted(types.items()):
        cls = e.get("class")
        if cls not in CLASSES:
            problems.append(f"unknown class {cls!r}: {name}")
            continue
        if e.get("arm_boundary") not in BOUNDARIES:
            problems.append(f"unknown arm_boundary {e.get('arm_boundary')!r}: {name}")
        if not str(e.get("reason", "")).strip():
            problems.append(f"no reason: {name}")
        if ("hosts" in e) != (cls == "branch-container") or (cls == "branch-container" and not e["hosts"]):
            problems.append(f"hosts belong on every branch container and nothing else: {name}")
        if ("alias_to" in e) != (cls == "token-alias"):
            problems.append(f"alias_to belongs on every token alias and nothing else: {name}")
        elif cls == "token-alias" and e["alias_to"] not in named:
            problems.append(f"alias_to names no declared type: {name} -> {e['alias_to']}")
        if "role" in e:
            if cls != "directive" or e["role"] not in ROLES:
                problems.append(f"a role belongs on a directive and is one of {ROLES}: {name}")
            roles.setdefault(e["role"], []).append(name)
    for r in ROLES:
        if len(roles.get(r, [])) != 1:
            problems.append(f"role {r} must name exactly one type, names {roles.get(r, [])}")

    for name in sorted(set(types) - named):
        problems.append(f"stale entry, type no longer declared: {name}")

    role_types = {n for n, e in types.items() if "role" in e}
    candidates = {}
    for t in sorted(named):
        if kids[t] & role_types:
            candidates.setdefault(t, "holds a conditional directive")
    for t in node_types:
        if t.get("named") and t.get("extra"):
            candidates.setdefault(t["type"], "an extra")
    for t, e in registry.items():
        if t in named:
            candidates.setdefault(t, f"registry kind {e.kind}")
    parents = {}
    for p, ks in kids.items():
        for k in ks:
            parents.setdefault(k, set()).add(p)
    special = {n for n, e in types.items() if e.get("class") not in (None, "ordinary")}
    special |= {t for t in candidates if t not in types}
    grew = True
    while grew:
        grew = False
        for t in sorted(named - special - set(candidates)):
            if parents.get(t) and parents[t] <= special:
                candidates[t] = "only ever a child of special types"
                special.add(t)
                grew = True
    for t in sorted(candidates):
        if t not in types:
            problems.append(f"unclassified: {t} ({candidates[t]})")

    for t, e in sorted(registry.items()):
        p = types.get(t)
        if p is None:
            continue
        want = KIND_TO_CLASS.get(e.kind)
        if want and p.get("class") != want:
            problems.append(f"class disagrees with the registry: {t} is {p.get('class')}, "
                            f"registry kind {e.kind} means {want}")
        if e.kind == "unsupported" and p.get("class") == "ordinary":
            problems.append(f"registry-unsupported type classified ordinary: {t}")
        if e.kind == "token-alias" and p.get("alias_to") != e.alias_to:
            problems.append(f"alias_to disagrees with the registry: {t} -> {p.get('alias_to')}, registry {e.alias_to}")
        if p.get("class") == "branch-container" and e.hosts and p.get("hosts") != e.hosts:
            mine, theirs = p.get("hosts") or {}, e.hosts
            for slot in sorted(set(mine) | set(theirs)):
                if mine.get(slot) != theirs.get(slot):
                    problems.append(f"host policy disagrees with the registry: {t} in {slot}: "
                                    f"{mine.get(slot)} vs {theirs.get(slot)}")

    for t, p in sorted(types.items()):
        if p.get("class") != "branch-container" or (t in registry and registry[t].hosts) or t not in named:
            continue
        real, declared = host_slots(node_types, t), set(p.get("hosts") or {})
        problems += [f"host slot not classified: {t} in {s}" for s in sorted(real - declared)]
        problems += [f"stale host slot: {t} in {s}" for s in sorted(declared - real)]

    opener, closer = (roles.get("if") or [None])[0], (roles.get("endif") or [None])[0]
    for t, p in sorted(types.items()):
        if t not in kids or p.get("class") not in CLASSES:
            continue
        d = kids[t] & role_types
        want = ("own-directives" if {opener, closer} <= d else "cross-node" if d
                else "assembler" if p["class"] == "fragment" else "none")
        if p.get("arm_boundary") != want:
            problems.append(f"arm_boundary of {t} is {p.get('arm_boundary')}, its declared children say {want}")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args(argv)
    try:
        policy = json.loads((args.root / "traversal" / "policy.json").read_text(encoding="utf-8"))
        node_types = json.loads((args.root / "src" / "node-types.json").read_text(encoding="utf-8"))
        sys.path.insert(0, str(args.root))
        from tools.config_oracle import contracts
    except (OSError, ValueError, ImportError) as exc:
        print(f"traversal census: cannot run: {exc}", file=sys.stderr)
        return 2
    problems = census(policy, node_types, contracts.REGISTRY, contracts.host_slots)
    for p in problems:
        print(p)
    print(f"traversal census: {len(policy.get('types', {}))} entries, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6: Run the census and its tests**

Run: `python tools/traversal_census.py; echo "exit $?"`
Expected:
```text
traversal census: 89 entries, 0 problem(s)
exit 0
```

Run: `./tools/ts-lock.sh python -m pytest tests/traversal/test_census.py -q`
Expected: `15 passed`.

- [ ] **Step 7: Wire the census into validate-grammar.sh as Step 5f**

In `validate-grammar.sh`, insert after the Step 5e block (after its closing `fi`, before the `# Step 6: Parse a real AL corpus (opt-in, --full)` comment):

```bash
# Step 5f: Traversal-policy census (roadmap F0)
#
# traversal/policy.json classifies every node type that is not ordinary, for the
# traversal helpers in every binding (docs/traversal.md). tools/traversal_census.py
# fails when the grammar or the contracts registry moved and the policy did not.
# Needs no parser, so it never skips. Exit 1 is a finding, 2 could not run; both
# fail validation.
print_header "Step 5f: Traversal Policy Census"
if CENSUS_OUTPUT=$(python tools/traversal_census.py 2>&1); then
    print_success "traversal policy census: clean"
else
    census_status=$?
    print_error "traversal census failed (exit $census_status)"
    echo "$CENSUS_OUTPUT"
    VALIDATION_FAILED=1
fi
```

- [ ] **Step 8: Prove the step can fail, through the gate self-test**

In `tools/gate_selftest.py`, change line 92 so the scratch copy carries the policy:

```python
COPY_DIRS = ["tools", "test", "queries", "src", "traversal"]
```

and add this case directly after the `step5e-oracle-discrepancy` case:

```python
    # ---- Step 5f: traversal-policy census (roadmap F0) -------------------------
    Case(
        id="step5f-traversal-census-unclassified",
        gate=VALIDATE,
        why="the policy entry for else_table_relation_fragment, the unprefixed fragment "
            "of spec 6.1, deleted: a special type the registry knows with no traversal class",
        mutations=[sub("traversal/policy.json",
                       r'    "else_table_relation_fragment": \{\n(?:      .*\n)+?    \},\n', "", count=1)],
        must_contain=["traversal census failed (exit 1)",
                      "unclassified: else_table_relation_fragment (registry kind fragment)"],
        must_not_contain=["All validation checks passed"],
    ),
```

Run: `python tools/gate_selftest.py --sweep`
Expected: `gate-selftest: sweep examined 3 gate scripts, found 25 degradation guard(s), inventory has 25`, exit 0 (Step 5f adds no guard).

Run: `./tools/ts-lock.sh python tools/gate_selftest.py -k step5f`
Expected (about 50 s; it runs the whole validator in a scratch copy):
```text
  PASS  step5f-traversal-census-unclassified  ...  exit 1, named the defect
gate-selftest: 1 passed, 0 failed, 0 skipped, of 1 selected
```

- [ ] **Step 9: Check git sees every new file, then commit**

Run: `git add .gitignore traversal/policy.json tools/traversal_census.py tests/traversal/support.py tests/traversal/conftest.py tests/traversal/test_census.py validate-grammar.sh tools/gate_selftest.py && git ls-files tests/traversal traversal tools/traversal_census.py | wc -l`
Expected: `5`.

```bash
git commit -m "feat(traversal): policy file and its census gate (roadmap F0)

traversal/policy.json classifies all 89 special node types into the seven
classes of spec 6.1, with host policies, arm-boundary source and a reason.
tools/traversal_census.py (validate-grammar.sh Step 5f) detects special types
from structure and the contracts registry, never from a name, and fails on an
unclassified type, a stale entry or a registry disagreement."
```

---

### Task 2: Python walker — policy loading, the directive group index, `walk`

**Files:**
- Create: `bindings/python/tree_sitter_al/traversal.py`, `tests/traversal/test_walk.py`, the twelve `tests/traversal/fixtures/*.al`
- Modify: `.gitattributes` (append)

**Interfaces:**
- Consumes: Task 1's fixtures `T`, `policy`, `al_parser`, `parse`; `traversal/policy.json` roles `if`/`elif`/`else`/`endif` on `preproc_if`/`preproc_elif`/`preproc_else`/`preproc_endif`.
- Produces: everything in "Shared interfaces" for Python except `groups_of`, `bind_arm`, `split_info`, `split_to_json`, `visits_to_json`, `dump_expected`. `Visit.split` is `None` in this task.

- [ ] **Step 1: Write the fixtures**

These twelve files are shared by every runtime's tests; byte offsets in later tasks depend on their exact bytes. Write the ten LF files below verbatim (UTF-8, final newline). `containers.al` line 1 deliberately holds multi-byte text.

`tests/traversal/fixtures/containers.al`:

```al
// Non-ASCII before every group: Ærø, 😀. JS offsets are UTF-16; visits are UTF-8 bytes.
#if CLEAN25
codeunit 50100 "Containers Æ"
{
}
#else
codeunit 50100 "Containers Ø"
{
#if CLEAN24
    procedure A()
    begin
        Message('å');
    end;
#elif CLEAN23
    procedure B()
    begin
    end;
#else
    procedure C()
    begin
    end;
#endif

    procedure Stmts()
    var
        X: Integer;
    begin
        Message('control');
#if CLEAN24
        DoThing(X);
        X := 1;
#if CLEAN26
        X := 3;
#endif
#elif CLEAN23
        X := 4;
#else
        X := 2;
#endif
    end;
}
#endif
```

`tests/traversal/fixtures/assemblers.al`:

```al
codeunit 50101 "Assemblers"
{
    Permissions = tabledata Customer = r,
#if CLEAN25
                  tabledata Vendor = r;
#else
                  tabledata Item = r,
                  tabledata Resource = r;
#endif

    procedure First()
    begin
    end;

#if CLEAN25
    procedure Split(A: Integer)
#else
    procedure Split(A: Integer; B: Integer)
#endif
    begin
        Message('x');
    end;

    procedure Tail(X: Integer): Integer
    begin
        X := X
#if CLEAN25
            + 1
#endif
            ;
        if X > 0 then
#if CLEAN25
            if X > 1 then begin
                Message('a');
#endif
                Message('b');
#if CLEAN25
            end;
#endif
#pragma warning disable AL0432
        exit(X);
#pragma warning restore AL0432
    end;

    procedure CaseEnd(K: Integer)
    begin
        case K of
            1:
                Message('one');
            2:
#if CLEAN25
                Message('two');
            end;
            Message('after a');
#else
                Message('deux');
            end;
            Message('after b');
#endif
    end;
}

table 50102 "Relations"
{
    fields
    {
        field(1; F; Code[20])
        {
            TableRelation = if (Type = const(Item)) Item
#if CLEAN25
                else if (Type = const(Resource)) Resource;
#else
                else if (Type = const(Resource)) "G/L Account";
#endif
        }
        field(2; G; Code[20])
        {
            DataClassification =
#if CLEAN25
                CustomerContent;
#else
                SystemMetadata;
#endif
        }
    }
}
```

`tests/traversal/fixtures/cross_node.al` (from `test/corpus/split_procedure_boundary_test.txt`):

```al
codeunit 50100 T
{
    procedure P()
    begin
        Message('a');
#if not C28
        Message('b');
#else
        Message(Q('c'));
    end;

    local procedure Q(T: Text): Text
    begin
        exit(T);
#endif
    end;

    procedure R()
    begin
    end;
}
```

`tests/traversal/fixtures/elif_chain.al`:

```al
codeunit 50105 "Elif Chain"
{
#if CLEAN24
    procedure A()
    begin
    end;
#elif CLEAN23
    procedure B()
    begin
    end;
#else
    procedure C()
    begin
    end;
#endif

    procedure Stmts()
    var
        X: Integer;
    begin
#if CLEAN24
        X := 1;
#if CLEAN26
        X := 3;
#endif
#elif CLEAN23
        X := 4;
#else
        X := 2;
#endif
    end;
}
```

`tests/traversal/fixtures/split_declaration.al` (from `test/corpus/preproc_split_declarations.txt`):

```al
#if CONDITION
#pragma warning disable AL0432
codeunit 50100 "Test Impl" implements Interface1, Interface2
#pragma warning restore AL0432
#else
codeunit 50100 "Test Impl" implements Interface2
#endif
{
    Access = Internal;

    procedure TestMethod()
    begin
    end;
}
```

`tests/traversal/fixtures/unbalanced.al` (an `#if` never closed: the tree has an ERROR node):

```al
codeunit 50104 "Unbalanced"
{
    procedure P()
    begin
#if CLEAN25
        Message('never closed');
    end;
}
```

The next four exist because no clean corpus case produces their type (Task 4 uses them as witnesses).

`tests/traversal/fixtures/impl_values.al` (`preproc_conditional_impl_values`):

```al
enum 50100 "Probe Kind" implements "IProbe", "IOther"
{
    Extensible = true;
    DefaultImplementation = "IProbe" = "Probe Default",
#if CLEAN25
        "IOther" = "Other New"
#else
        "IOther" = "Other Old"
#endif
        ;

    value(0; None) { }
}
```

`tests/traversal/fixtures/query_conditional.al` (`preproc_conditional_query`):

```al
query 50100 "Probe Query"
{
    elements
    {
        dataitem(Item; Item)
        {
            column(No; "No.") { }
#if CLEAN25
            column(Description; Description) { }
#else
            column(Desc2; "Description 2") { }
#endif
        }
    }
}
```

`tests/traversal/fixtures/split_brace_close.al` (`preproc_split_brace_close`):

```al
pageextension 50100 "Probe Ext" extends "Customer Card"
{
    layout
    {
        addlast(General)
        {
            field(A; Rec.Name) { }
#if CLEAN25
            field(B; Rec.Address) { }
        }
#else
            field(C; Rec.City) { }
        }
#endif
    }
}
```

`tests/traversal/fixtures/split_case_branch.al` (`preproc_split_case_branch`):

```al
codeunit 50100 Probe
{
    procedure P(K: Integer)
    begin
        case K of
#if CLEAN25
            3,
#endif
            1, 2:
                Message('x');
        end;
    end;
}
```

The last two need bytes an editor would normalise, so write them with Python:

```bash
python - <<'EOF'
from pathlib import Path
d = Path("tests/traversal/fixtures")
d.joinpath("crlf_bom.al").write_bytes(
    b'\xef\xbb\xbfcodeunit 50106 "CRLF BOM"\r\n{\r\n#if CLEAN25\r\n    procedure A()\r\n    begin\r\n    end;\r\n'
    b'#else\r\n    procedure B()\r\n    begin\r\n    end;\r\n#endif\r\n}\r\n')
d.joinpath("stray_endif.al").write_bytes(
    b"codeunit 50107 \"Stray\"\n{\n    procedure P()\n    begin\n        Message('x');\n#endif\n    end;\n}\n")
EOF
```

Append to `.gitattributes` so the CRLF fixture survives `* text=auto eol=lf`:

```gitattributes

# The CRLF + BOM traversal fixture must keep its CRLF line endings in every checkout:
# under `text=auto eol=lf` it would silently become an LF fixture.
tests/traversal/fixtures/crlf_bom.al -text
```

Run: `sha256sum tests/traversal/fixtures/*.al; git check-attr text -- tests/traversal/fixtures/crlf_bom.al`
Expected:
```text
8eec5e7e565ab8194953468f1bbe7c7072a0d477ff9497c25bd64062b7b7a838  tests/traversal/fixtures/assemblers.al
029c731623125facda8067c5e5cd4b6186512201d0043d4cf88c04b5886befaf  tests/traversal/fixtures/containers.al
b7ee083c506ee80bfa21e1a212a0a92c13d9e8bc4722144a29b43b42b2540193  tests/traversal/fixtures/crlf_bom.al
74da657d210a17feb0e306746396841173c312432972384eaa3e91b45639e3d0  tests/traversal/fixtures/cross_node.al
cf313cfee126ae912ae853713a344b9d8fda5063981ed57c285bcd0275d7a5fc  tests/traversal/fixtures/elif_chain.al
23775875b370fe8b5bfc4bd08f49f6882436810cbde0ff39332004aa3eb5c94f  tests/traversal/fixtures/impl_values.al
b209c3da3ed92cfd0a3392bd3aef214ee6773ed3fb54878601830096d74d86de  tests/traversal/fixtures/query_conditional.al
4c3d9b5cc26eaaf0b51dc0bce9cf5de44e4e9feb1039db13ee6b3093eeb998ec  tests/traversal/fixtures/split_brace_close.al
d3c73655b73916550b22c5c54f3350dc25dd3e971a2f87ed4a318930dff61cc5  tests/traversal/fixtures/split_case_branch.al
c30b81d07f33dedbb0a530a494bb41d108206bec09e27965f4f2175e817dec3c  tests/traversal/fixtures/split_declaration.al
c381a8a7217d93d5a3f29f8e5f599b096684e7bd64bb671f6d2c788319f1fcf6  tests/traversal/fixtures/stray_endif.al
d8942ac1e43e690e2d5e03ace03e95e0f2f0ba105328a0f38b650e08def3a7ec  tests/traversal/fixtures/unbalanced.al
tests/traversal/fixtures/crlf_bom.al: text: unset
```

Every fixture except `unbalanced.al` parses without ERROR or MISSING: `./tools/ts-lock.sh tree-sitter parse -q tests/traversal/fixtures/*.al` prints exactly one line, for `unbalanced.al`, ending `(ERROR [2, 4] - [6, 8])`, and exits 1.

- [ ] **Step 2: Write the failing walker tests**

`tests/traversal/test_walk.py`:

```python
"""The Python walker: policy loading, the directive group index, walk (F0, spec 5.1 layer 1, 6.1).

Every expected value here is written by hand from the fixture text, never read back
from the walker: these are what make the generated .visits.json files trustworthy.
"""
import json
import time

import pytest


def test_load_policy_rejects_an_unknown_schema(T, tmp_path):
    p = tmp_path / "policy.json"
    p.write_text(json.dumps({"schema": 2, "types": {}}))
    with pytest.raises(T.PolicyError):
        T.load_policy(p)


def test_load_policy_rejects_an_unknown_class(T, tmp_path):
    p = tmp_path / "policy.json"
    p.write_text(json.dumps({"schema": 1, "types": {"x": {"class": "special"}}}))
    with pytest.raises(T.PolicyError):
        T.load_policy(p)


def test_an_unlisted_type_is_ordinary(policy):
    assert policy.cls("identifier") == "ordinary"
    assert policy.cls("preproc_conditional") == "branch-container"


def test_fnv1a64_reference_vectors(T):
    assert T.fnv1a64(b"") == "cbf29ce484222325"
    assert T.fnv1a64(b"a") == "af63dc4c8601ec8c"


def test_groups_and_arms_come_from_the_trees_own_directives(parse):
    doc = parse("containers.al")
    # Line 1 holds multi-byte text, so every offset below is a UTF-8 byte offset.
    assert doc.source[93:96] == b"#if"
    assert [(g.if_offset, [a.raw_range for a in g.arms]) for g in doc.groups] == [
        (93, [(105, 140), (145, 594)]),               # #if CLEAN25 / #else, around both objects
        (179, [(191, 251), (265, 302), (307, 345)]),  # #if CLEAN24 / #elif / #else, members
        (441, [(453, 524), (538, 554), (559, 576)]),  # the same, statements
        (489, [(501, 517)]),                          # #if CLEAN26, nested in arm 0 of 441
    ]
    assert doc.groups[1].arms[1].directive_offsets == (251, 302)
    assert [d.role for d in doc.groups[1].directives] == ["if", "elif", "else", "endif"]
    assert doc.unpaired == ()


def test_walk_skips_directives_and_trivia_unless_asked(T, policy, parse):
    doc = parse("assemblers.al")
    default = {v.type for v in T.walk(doc, policy)}
    assert not default & {"preproc_if", "preproc_else", "preproc_endif", "preproc_open", "pragma"}
    everything = {v.type for v in T.walk(doc, policy, include_directives=True, include_trivia=True)}
    assert {"preproc_if", "preproc_else", "preproc_endif", "preproc_open", "pragma"} <= everything


def test_arm_paths_are_outermost_first(T, policy, parse):
    doc = parse("containers.al")
    arms = {doc.source[v.start:v.end].decode(): v.arms for v in T.walk(doc, policy)
            if v.type == "assignment_statement"}
    assert arms == {"X := 1": ((93, 1), (441, 0)), "X := 3": ((93, 1), (441, 0), (489, 0)),
                    "X := 4": ((93, 1), (441, 1)), "X := 2": ((93, 1), (441, 2))}


def test_a_branch_container_reports_its_host_policy(T, policy, parse):
    doc = parse("containers.al")
    hosts = [(v.type, v.host) for v in T.walk(doc, policy) if v.cls == "branch-container"]
    assert hosts == [("preproc_conditional_object", "splice-repeat"), ("preproc_conditional", "splice-repeat"),
                     ("preproc_conditional_statement", "splice-repeat"),
                     ("preproc_conditional_statement", "splice-repeat")]
    assert all(v.host is None for v in T.walk(doc, policy) if v.cls != "branch-container")


def test_a_node_straddling_an_arm_boundary_is_in_no_arm(T, policy, parse):
    """cross_node.al: procedure Q starts inside the #else arm and ends after #endif."""
    doc = parse("cross_node.al")
    q = next(v for v in T.walk(doc, policy) if v.type == "procedure"
             and doc.source[v.start:v.end].startswith(b"local procedure Q"))
    assert q.arms == ()
    body = next(v for v in T.walk(doc, policy, root=q.node) if v.type == "exit_statement")
    assert body.arms == ((69, 1),)


def test_walk_from_a_subtree_keeps_document_arm_paths(T, policy, parse):
    doc = parse("containers.al")
    stmts = next(v for v in T.walk(doc, policy) if v.type == "procedure"
                 and doc.source[v.start:v.end].startswith(b"procedure Stmts"))
    sub = T.walk(doc, policy, root=stmts.node)
    assert sub[0].node == stmts.node and sub[0].arms == ((93, 1),)
    assert [v.arms for v in sub if v.type == "assignment_statement"][1] == ((93, 1), (441, 0), (489, 0))


def test_an_unclosed_group_runs_to_end_of_file(parse):
    doc = parse("unbalanced.al")
    assert doc.tree.root_node.has_error
    (group,) = doc.groups
    assert group.arms[0].raw_range[1] == len(doc.source)
    assert group.arms[0].directive_offsets == (group.if_offset,)


def test_a_stray_endif_is_unpaired_and_opens_no_group(parse):
    doc = parse("stray_endif.al")
    assert doc.groups == ()
    assert [(d.role, d.start) for d in doc.unpaired] == [("endif", 75)]


def test_crlf_and_a_leading_bom_keep_byte_offsets(parse):
    doc = parse("crlf_bom.al")
    assert doc.source.startswith(b"\xef\xbb\xbf") and b"\r\n" in doc.source
    (group,) = doc.groups
    assert group.if_offset == doc.source.index(b"#if")
    assert doc.source[group.arms[0].raw_range[0] - 2:group.arms[0].raw_range[0]] == b"\r\n"
    assert [a.raw_range for a in group.arms] == [(46, 86), (91, 133)]


def test_walk_is_iterative_and_fast_on_large_and_deep_input(T, policy, al_parser):
    groups = "".join(f"#if C{i}\n    procedure P{i}()\n    begin\n        X := {i};\n    end;\n#else\n"
                     f"    procedure Q{i}()\n    begin\n    end;\n#endif\n" for i in range(2000))
    src = f"codeunit 50100 Big\n{{\n{groups}}}\n".encode()
    doc = T.Document(al_parser.parse(src), src, policy)
    start = time.perf_counter()
    visits = T.walk(doc, policy)
    assert time.perf_counter() - start < 3, "walk is quadratic in the number of groups again (measured: 0.16 s linear, 4.4 s quadratic)"
    assert len(doc.groups) == 2000 and sum(v.type == "procedure" for v in visits) == 4000
    deep = ("codeunit 1 D\n{\n procedure P()\n begin\n  X := " + "(" * 5000 + "1" + ")" * 5000
            + ";\n end;\n}\n").encode()
    doc = T.Document(al_parser.parse(deep), deep, policy)
    assert len(T.walk(doc, policy)) > 5000          # no RecursionError
```

- [ ] **Step 3: Run them to see them fail**

Run: `./tools/ts-lock.sh python -m pytest tests/traversal/test_walk.py -q`
Expected: 14 errors, `FileNotFoundError: ... bindings/python/tree_sitter_al/traversal.py` from the `T` fixture.

- [ ] **Step 4: Write the walker**

`bindings/python/tree_sitter_al/traversal.py` (Task 3 adds `SplitInfo`; until then `Visit.split` is `None`):

```python
"""Classified traversal over the all-branches AL tree (roadmap F0, spec 5.1 and 6).

Stdlib only, no relative imports: tests load this file by path, and the
installed package imports it as ``tree_sitter_al.traversal``. Works on any
py-tree-sitter >= 0.25 ``Tree``; nothing here imports ``tree_sitter``.

Every position is a canonical UTF-8 byte offset. Node classes come from the
hand-maintained policy (``traversal/policy.json``), never from a type name.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

SCHEMA = 1
CLASSES = ("ordinary", "branch-container", "assembler", "fragment", "token-alias", "directive", "trivia")
# Only these get a SplitInfo on their visit. An ordinary node that holds directives
# (an ERROR node, say) is walked normally; its arms still reach every visit's `arms`.
SPLIT_CLASSES = ("branch-container", "assembler", "fragment")


class PolicyError(ValueError):
    """The policy file is not one this module can read."""


class WrongDocument(ValueError):
    """An ArmDescriptor from another source revision was handed to bind_arm."""


@dataclass(frozen=True)
class Policy:
    types: dict

    def cls(self, type_: str) -> str:
        entry = self.types.get(type_)
        return entry["class"] if entry else "ordinary"

    def role(self, type_: str):
        entry = self.types.get(type_)
        return entry.get("role") if entry else None

    def host_policy(self, container: str, parent: str, field):
        hosts = (self.types.get(container) or {}).get("hosts") or {}
        return hosts.get(f"{parent}:{field or '<children>'}")


def load_policy(path=None) -> Policy:
    if path is None:
        text = (resources.files("tree_sitter_al") / "traversal_policy.json").read_text(encoding="utf-8")
    else:
        text = Path(path).read_text(encoding="utf-8")
    data = json.loads(text)
    if data.get("schema") != SCHEMA:
        raise PolicyError(f"policy schema {data.get('schema')!r}, expected {SCHEMA}")
    for type_, entry in data["types"].items():
        if entry.get("class") not in CLASSES:
            raise PolicyError(f"{type_}: unknown class {entry.get('class')!r}")
    return Policy(data["types"])


def fnv1a64(data: bytes) -> str:
    h = 0xCBF29CE484222325
    for b in data:
        h = ((h ^ b) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return f"{h:016x}"


@dataclass(frozen=True)
class Directive:
    role: str
    start: int   # the '#' offset
    end: int
    node: object


@dataclass(frozen=True)
class ArmDescriptor:
    group_id: tuple          # (revision, '#if' byte offset)
    arm_id: int
    directive_offsets: tuple  # '#' of the arm's opening directive, then of its closing one if any
    raw_range: tuple         # (start, end) of the arm body, before masking


@dataclass(frozen=True)
class Group:
    if_offset: int
    directives: tuple        # Directive, in source order: if, elif*, else?, endif?
    arms: tuple              # ArmDescriptor


@dataclass(frozen=True)
class Fragment:
    field: object            # str | None
    node: object             # a named node or an anonymous token

    @property
    def type(self):
        return self.node.type


@dataclass(frozen=True)
class ArmFragments:
    descriptor: ArmDescriptor
    fragments: tuple         # Fragment, in source order


@dataclass(frozen=True)
class GroupArms:
    group_id: tuple
    arms: tuple              # ArmFragments, one per arm, every arm present


@dataclass(frozen=True)
class SplitInfo:
    groups: tuple            # GroupArms, in source order
    shared: tuple            # Fragment: the node's own children outside every arm, directives excluded


@dataclass(frozen=True)
class Visit:
    node: object
    cls: str
    type: str
    field: object
    start: int
    end: int
    arms: tuple              # ((if_offset, arm_id), ...), outermost first
    host: object             # host policy, for a branch container in a known slot
    split: object            # SplitInfo | None


class Document:
    """A P1 tree paired with its source bytes and revision; owns the group index."""

    def __init__(self, tree, source: bytes, policy: Policy):
        self.tree = tree
        self.source = source
        self.revision = fnv1a64(source)
        self.groups, self.unpaired, self._by_parent = _pair(tree.root_node, policy, self.revision, len(source))

    def descriptors(self):
        return [a for g in self.groups for a in g.arms]


def _pair(root, policy, revision, eof):
    open_, done, unpaired, by_parent = [], [], [], {}
    stack = [root]
    while stack:
        node = stack.pop()
        role = policy.role(node.type) if node.is_named else None
        if role is None:
            stack.extend(reversed(node.children))
            continue
        d = Directive(role, node.start_byte, node.end_byte, node)
        if role == "if":
            open_.append([d])
        elif not open_:
            unpaired.append(d)
            continue
        else:
            open_[-1].append(d)
        group = open_[-1]
        parent_ids = by_parent.setdefault(node.parent.id, [])
        if group[0].start not in parent_ids:
            parent_ids.append(group[0].start)
        if role == "endif":
            done.append(open_.pop())
    done.extend(open_)                    # unclosed at EOF
    groups = {}
    for ds in sorted(done, key=lambda g: g[0].start):
        arms = []
        for idx, d in enumerate(ds):
            if d.role == "endif":
                continue
            closer = ds[idx + 1] if idx + 1 < len(ds) else None
            offsets = (d.start, closer.start) if closer else (d.start,)
            arms.append(ArmDescriptor((revision, ds[0].start), len(arms), offsets,
                                      (d.end, closer.start if closer else eof)))
        groups[ds[0].start] = Group(ds[0].start, tuple(ds), tuple(arms))
    return tuple(groups.values()), tuple(unpaired), {k: [groups[o] for o in v] for k, v in by_parent.items()}


def _kids(node):
    """(child, field name) pairs, the children list read once."""
    return [(c, node.field_name_for_child(i)) for i, c in enumerate(node.children)]


def walk(document: Document, policy: Policy, *, root=None, include_directives=False, include_trivia=False):
    arms = sorted(document.descriptors(), key=lambda a: (a.raw_range[0], -a.raw_range[1]))
    active, k, out = [], 0, []
    stack = [(root if root is not None else document.tree.root_node, None, None)]
    while stack:
        node, field, parent = stack.pop()
        if not node.is_named:
            continue
        cls = policy.cls(node.type)
        if (cls == "directive" and not include_directives) or (cls == "trivia" and not include_trivia):
            continue
        start, end = node.start_byte, node.end_byte
        while k < len(arms) and arms[k].raw_range[0] <= start:
            active.append(arms[k])
            k += 1
        active = [a for a in active if a.raw_range[1] > start]
        path = tuple((a.group_id[1], a.arm_id) for a in active if a.raw_range[1] >= end)
        host = policy.host_policy(node.type, parent.type, field) if cls == "branch-container" and parent else None
        split = None                     # SplitInfo arrives with split_info (Task 3)
        out.append(Visit(node, cls, node.type, field, start, end, path, host, split))
        stack.extend((child, f, node) for child, f in reversed(_kids(node)))
    return out
```

Why each choice: the module is stdlib-only and duck-typed, so it works on any py-tree-sitter `Tree` without importing `tree_sitter`. `_pair` reads directive roles from the policy, never from type names. A group with no `#endif` closes at end of file; an `#elif`/`#else`/`#endif` with no open group goes to `unpaired`. `walk` is an explicit stack (no recursion limit) and keeps the arms containing the current byte in a sliding window, so the arm path is linear in the file, not in nodes times arms. A node is in an arm only if the arm **wholly** contains it.

- [ ] **Step 5: Run the tests to see them pass**

Run: `./tools/ts-lock.sh python -m pytest tests/traversal -q`
Expected: `29 passed` (14 here, 15 from Task 1).

- [ ] **Step 6: Commit**

Run: `git add .gitattributes bindings/python/tree_sitter_al/traversal.py tests/traversal/test_walk.py tests/traversal/fixtures/*.al && git ls-files tests/traversal/fixtures | wc -l`
Expected: `12`.

```bash
git commit -m "feat(traversal): Python walker and the shared fixtures (roadmap F0)

Policy loading, the #if group index built from the tree's own directive
nodes (spec 5.1 layer 1), and walk: class, field, UTF-8 span, arm path and
host policy per visit. Twelve fixtures cover non-ASCII text, CRLF + BOM, an
unclosed #if, a stray #endif and a group crossing a procedure boundary."
```

---

### Task 3: `SplitInfo`, `groups_of` and `bind_arm` → `ArmFragments`

**Files:**
- Modify: `bindings/python/tree_sitter_al/traversal.py`
- Create: `tests/traversal/test_split.py`

**Interfaces:**
- Consumes: Task 2's `Document` (`_by_parent` index of group start offsets per parent node id), `ArmDescriptor`, `_kids`.
- Produces: `groups_of(node, document) -> list[Group]`; `bind_arm(descriptor, document, policy) -> ArmFragments` (raises `WrongDocument` when `descriptor.group_id[0] != document.revision`); `split_info(node, document, policy) -> SplitInfo | None`; `Visit.split` populated for classes in `SPLIT_CLASSES`; `split_to_json`, `visits_to_json` (the parity form).

- [ ] **Step 1: Write the failing tests**

`tests/traversal/test_split.py`:

```python
"""SplitInfo, ArmDescriptor and bind_arm -> ArmFragments (spec 5.1 layers 1 and 3, 6.1)."""
import pytest


def text(doc, node):
    return doc.source[node.start_byte:node.end_byte].decode()


def shape(arm):
    return [(f.field, f.type) for f in arm.fragments]


def visit(T, policy, doc, type_):
    (v,) = [x for x in T.walk(doc, policy) if x.type == type_]
    return v


def test_split_procedure_arms_carry_the_header_and_the_body_is_shared(T, policy, parse):
    doc = parse("assemblers.al")
    v = visit(T, policy, doc, "preproc_split_procedure")
    header = [(None, "procedure_keyword"), ("name", "identifier"), (None, "("),
              ("parameters", "parameter_list"), (None, ")")]
    (group,) = v.split.groups
    assert group.group_id == (doc.revision, 274)
    assert [shape(a) for a in group.arms] == [header, header]
    assert [(f.field, f.type) for f in v.split.shared] == [("body", "code_block"), (None, ";")]
    assert [text(doc, a.fragments[3].node) for a in group.arms] == ["A: Integer", "A: Integer; B: Integer"]


def test_one_node_can_hold_two_groups_in_source_order(T, policy, parse):
    doc = parse("assemblers.al")
    v = visit(T, policy, doc, "preproc_split_if_then_begin")
    assert [g.group_id[1] for g in v.split.groups] == [570, 686]
    assert [g.if_offset for g in T.groups_of(v.node, doc)] == [570, 686]
    assert [shape(g.arms[0]) for g in v.split.groups] == [
        [(None, "if_keyword"), ("condition", "comparison_expression"), (None, "then_keyword"),
         (None, "begin_keyword"), (None, "call_expression"), (None, ";")],
        [(None, "end_keyword"), (None, ";")]]
    assert [(f.field, f.type) for f in v.split.shared] == [(None, "call_expression"), (None, ";")]


def test_a_cross_node_arm_binds_pieces_beyond_the_node(T, policy, parse):
    """cross_node.al: the #else arm closes P and opens Q; its #endif is inside Q."""
    doc = parse("cross_node.al")
    opener = visit(T, policy, doc, "preproc_split_block_end_in_else")
    closer = visit(T, policy, doc, "preproc_split_block_close_after_endif")
    assert [g.group_id for g in opener.split.groups] == [g.group_id for g in closer.split.groups]
    else_arm = opener.split.groups[0].arms[1]
    assert [text(doc, f.node) for f in else_arm.fragments][:6] == [
        "Message(Q('c'))", ";", "end", ";", "local", "procedure"]
    assert [(f.field, f.type) for f in closer.split.shared] == [(None, "end_keyword")]


def test_anonymous_tokens_stay_tokens_and_directives_are_never_fragments(T, policy, parse):
    doc = parse("assemblers.al")
    v = visit(T, policy, doc, "preproc_conditional_permissions")
    arms = v.split.groups[0].arms
    assert [(f.type, f.node.is_named) for f in arms[1].fragments] == [
        ("tabledata_permission", True), (",", False), ("tabledata_permission", True), (";", False)]
    every = [f for g in v.split.groups for a in g.arms for f in a.fragments]
    assert not [f for f in every if policy.cls(f.type) == "directive"]


def test_trivia_inside_an_arm_is_one_of_its_fragments(T, policy, parse):
    doc = parse("split_declaration.al")
    v = visit(T, policy, doc, "preproc_split_declaration")
    assert [f.type for f in v.split.groups[0].arms[0].fragments] == [
        "pragma", "codeunit_keyword", "integer", "quoted_identifier", "implements_clause", "pragma"]


def test_bind_arm_rejects_a_descriptor_from_another_document(T, policy, parse):
    a = parse("containers.al")
    b = parse("elif_chain.al")
    with pytest.raises(T.WrongDocument):
        T.bind_arm(a.descriptors()[0], b, policy)


def test_only_containers_assemblers_and_fragments_carry_a_split(T, policy, parse):
    doc = parse("unbalanced.al")            # its #if sits under an ERROR node
    error = [v for v in T.walk(doc, policy) if v.type == "ERROR"]
    assert error and all(v.cls == "ordinary" and v.split is None for v in error)
    assert T.groups_of(error[0].node, doc)  # the ERROR node does hold the group
    doc = parse("assemblers.al")
    assert {v.cls for v in T.walk(doc, policy) if v.split} == {"branch-container", "assembler"}
```

- [ ] **Step 2: Run them to see them fail**

Run: `./tools/ts-lock.sh python -m pytest tests/traversal/test_split.py -q`
Expected: 7 failures, `AttributeError: 'NoneType' object has no attribute 'groups'` or `module 'tree_sitter_al_traversal' has no attribute 'groups_of'`.

- [ ] **Step 3: Add the three functions**

In `bindings/python/tree_sitter_al/traversal.py`, insert between `_kids` and `walk`:

```python
def groups_of(node, document: Document):
    return list(document._by_parent.get(node.id, ()))


def bind_arm(descriptor: ArmDescriptor, document: Document, policy: Policy) -> ArmFragments:
    if descriptor.group_id[0] != document.revision:
        raise WrongDocument(f"descriptor revision {descriptor.group_id[0]} != document {document.revision}")
    lo, hi = descriptor.raw_range
    out = []
    # Start at the smallest node holding the whole arm, one level up if the arm IS
    # that node, so its field name is known: walking from the root is O(siblings)
    # per arm, quadratic in a body of thousands of groups.
    top = document.tree.root_node.descendant_for_byte_range(lo, hi) or document.tree.root_node
    while top.parent is not None and lo <= top.start_byte and top.end_byte <= hi:
        top = top.parent
    stack = [(top, None)]
    while stack:
        node, field = stack.pop()
        if node.end_byte <= lo or node.start_byte >= hi:
            continue
        if lo <= node.start_byte and node.end_byte <= hi:
            if not (node.is_named and policy.cls(node.type) == "directive"):
                out.append(Fragment(field, node))
            continue
        stack.extend(reversed(_kids(node)))
    return ArmFragments(descriptor, tuple(out))


def split_info(node, document: Document, policy: Policy):
    groups = groups_of(node, document)
    if not groups:
        return None
    ranges = [a.raw_range for g in groups for a in g.arms]
    shared = []
    for child, field in _kids(node):
        if child.is_named and policy.cls(child.type) == "directive":
            continue
        if any(lo <= child.start_byte and child.end_byte <= hi for lo, hi in ranges):
            continue
        shared.append(Fragment(field, child))
    return SplitInfo(tuple(GroupArms((document.revision, g.if_offset),
                                     tuple(bind_arm(a, document, policy) for a in g.arms)) for g in groups),
                     tuple(shared))
```

`bind_arm` is the "cover" of the arm's byte range: every node wholly inside it, taken whole, with its field name; a node straddling a boundary is opened and its children are tried. Hidden rules therefore show up as their children (spec §5.1), anonymous tokens stay tokens, and an arm that crosses into the next procedure binds pieces of that procedure. It starts from the smallest node holding the range, one level up if the arm is exactly that node so its field is known; starting at the root made a 2,000-group body take 4.4 s.

- [ ] **Step 4: Fill `Visit.split`**

In `walk`, replace

```python
        split = None                     # SplitInfo arrives with split_info (Task 3)
```

with

```python
        split = split_info(node, document, policy) if cls in SPLIT_CLASSES else None
```

An ordinary node holding directives (an ERROR node) gets no `SplitInfo`; its arms still reach every visit's `arms`.

- [ ] **Step 5: Add the parity serialisation**

Append to the end of the module:

```python
def _frag_json(f: Fragment):
    return [f.field, f.node.type, f.node.is_named, f.node.start_byte, f.node.end_byte]


def split_to_json(s: SplitInfo):
    return {"groups": [{"if": g.group_id[1],
                        "arms": [{"arm": a.descriptor.arm_id, "range": list(a.descriptor.raw_range),
                                  "fragments": [_frag_json(f) for f in a.fragments]} for a in g.arms]}
                       for g in s.groups],
            "shared": [_frag_json(f) for f in s.shared]}


def visits_to_json(visits):
    """The parity form: what every runtime must produce for the same fixture."""
    return [{"class": v.cls, "type": v.type, "field": v.field, "start": v.start, "end": v.end,
             "arms": [list(a) for a in v.arms], "host": v.host,
             "split": split_to_json(v.split) if v.split else None} for v in visits]
```

- [ ] **Step 6: Run the tests to see them pass**

Run: `./tools/ts-lock.sh python -m pytest tests/traversal -q`
Expected: `36 passed`.

- [ ] **Step 7: Commit**

```bash
git add bindings/python/tree_sitter_al/traversal.py tests/traversal/test_split.py
git commit -m "feat(traversal): SplitInfo and bind_arm -> ArmFragments (roadmap F0)

Spec 5.1 layer 3, unconfigured: every arm of every group a node holds, as
the P1 pieces inside the arm's byte range with field names, anonymous tokens
kept; the node's shared parts beside them. A descriptor from another
revision is refused."
```

---

### Task 4: Witnesses — every policy entry, every named exception, each with a mutant

**Files:**
- Create: `tests/traversal/witnesses.tsv`, `tests/traversal/test_witnesses.py`

**Interfaces:**
- Consumes: `doc_of("corpus:<Case.id>" | "fixture:<file>")` (Task 1), `T.walk`, `T.Policy`, `T.ArmFragments`, `T.bind_arm` (Tasks 2–3).
- Produces: nothing other tasks call. The `class` column of `witnesses.tsv` is a second, hand-written statement of every entry's class, independent of the policy.

- [ ] **Step 1: Write the witness table**

`tests/traversal/witnesses.tsv` — the columns are separated by a single TAB (check with the command below); `corpus:` sources are `tools.config_oracle.fixtures` `Case.id`s, so `#` in a case name is `%23`:

```text
# One witness per traversal-policy entry (spec 6.1, D8). Hand-maintained.
# `class` is a second, independent statement of what the policy must say: a policy
# edit that flips a class passes the census (which reads the policy) and fails here.
# source: corpus:<tools.config_oracle.fixtures Case.id> | fixture:<file in fixtures/>
type	class	source
comment	ordinary	corpus:al_built_in_functions.txt#AL Built-in Functions#0
else_table_relation_fragment	fragment	corpus:preproc_split_table_relation_branch.txt#TableRelation with semicolon inside %23if branch (Pattern 1: else if in preproc)#0
multiline_comment	ordinary	corpus:multiline_comment_test.txt#Multiline comment in codeunit#0
pragma	trivia	corpus:action_group_preprocessor_test.txt#Action group with preprocessor conditional actionref#0
preproc_and_expression	directive	corpus:preproc_compound_conditions.txt#Preprocessor with AND condition#0
preproc_close	directive	corpus:action_group_preprocessor_test.txt#Action group with preprocessor conditional actionref#0
preproc_conditional	branch-container	corpus:conditional_procedure_test.txt#Procedures inside conditional compilation blocks test#0
preproc_conditional_actions	branch-container	corpus:action_group_preprocessor_test.txt#Action group with preprocessor conditional actionref#0
preproc_conditional_arguments	branch-container	corpus:split_comma_lists_test.txt#A %23if at an argument separator, on either side of the comma#0
preproc_conditional_case	branch-container	corpus:case_preprocessor_else.txt#Case statement with preprocessor conditional else branch#0
preproc_conditional_case_patterns	branch-container	corpus:case_statement.txt#Case statement with preprocessor conditional in pattern list#0
preproc_conditional_controladdin	branch-container	corpus:controladdin_attributed_procedure_test.txt#ControlAddin with preprocessor conditional attributes#0
preproc_conditional_dataset	branch-container	corpus:preprocessor.txt#Preprocessor conditional in dataset section (around dataitems)#0
preproc_conditional_expression_tail	assembler	corpus:preproc_arg_continuation_test.txt#A call argument continued across a %23if boundary#0
preproc_conditional_fieldgroups	branch-container	corpus:fieldgroups_preproc.txt#Fieldgroups with preprocessor conditionals#0
preproc_conditional_fields	branch-container	corpus:nested_preproc_fields_keys_test.txt#Nested %23if among table fields and keys#0
preproc_conditional_impl_values	branch-container	fixture:impl_values.al
preproc_conditional_keys	branch-container	corpus:key_preprocessor_test.txt#Key with nested preprocessor conditionals#0
preproc_conditional_labels	branch-container	corpus:preproc_conditional_labels.txt#%23if/%23endif wrapping a label inside report labels (BC CLEANxx pattern)#0
preproc_conditional_layout	branch-container	corpus:page_preproc_trigger_var_test.txt#Page with preprocessor containing trigger with var section and variable#0
preproc_conditional_layout_mixed	branch-container	corpus:preprocessor_layout_properties_test.txt#Mixed preprocessor conditional content in grid section#0
preproc_conditional_link_values	branch-container	corpus:link_list_opening_conditional_test.txt#G11: a %23if opening a link list, unquoted names, is list-internal#0
preproc_conditional_list_elements	branch-container	corpus:preproc_inlist_continuation_test.txt#A list literal whose %23if supplies further ELEMENTS#0
preproc_conditional_object	branch-container	corpus:enum_empty_value_test.txt#Enum wrapped in preprocessor conditional with empty value#0
preproc_conditional_option_members	branch-container	corpus:option_list_opening_conditional_test.txt#G11: a %23if opening an option list, members continued after %23endif#0
preproc_conditional_permissions	branch-container	corpus:permissions_with_preprocessor_test.txt#Table with Permissions property containing preprocessor conditionals#0
preproc_conditional_property_value	assembler	corpus:link_list_opening_conditional_test.txt#G11: whole-value link list, `;` inside the arms, is unchanged#0
preproc_conditional_query	branch-container	fixture:query_conditional.al
preproc_conditional_rendering	branch-container	corpus:preproc_conditional_rendering_layout.txt#%23if/%23endif wrapping a layout inside report rendering (BC CLEANxx pattern)#0
preproc_conditional_report	branch-container	corpus:preprocessor_in_dataitem.txt#Preprocessor directives in dataitem column declarations#0
preproc_conditional_statement	branch-container	corpus:case_else_preprocessor_test.txt#Case statement with preprocessor conditional in else branch#0
preproc_conditional_table_relation	assembler	corpus:preproc_split_table_relation_branch.txt#TableRelation with semicolon inside %23if branch (Pattern 1: else if in preproc)#0
preproc_conditional_var	branch-container	corpus:case_else_preprocessor_test.txt#Case statement with preprocessor conditional in else branch#0
preproc_conditional_var_block	branch-container	corpus:procedure_preproc_var_test.txt#Procedure with preprocessor conditional var section#0
preproc_conditional_where	branch-container	corpus:calc_formula_preprocessor.txt#CalcFormula with preprocessor directives in where clause#0
preproc_conditional_xmlport	branch-container	corpus:xmlport_preprocessor_elements_test.txt#XMLPort with preprocessor conditionals in table elements#0
preproc_define	trivia	corpus:preproc_define_undef_test.txt#%23define at the top of a file, followed by an object declaration#0
preproc_elif	directive	corpus:case_else_preprocessor_test.txt#Nested case with multiple preprocessor conditions#0
preproc_else	directive	corpus:action_group_preprocessor_test.txt#Nested action groups with preprocessor conditionals#0
preproc_endif	directive	corpus:action_group_preprocessor_test.txt#Action group with preprocessor conditional actionref#0
preproc_endregion	trivia	corpus:malformed_region_directive_test.txt#Correct region directive syntax#0
preproc_fragmented_else_tail	assembler	corpus:preproc_fragmented_if_else_in_repeat.txt#Preprocessor fragmented if-else inside repeat-until loop#0
preproc_guarded_statement	assembler	corpus:preprocessor.txt#Preprocessor split if-statement with guard statements#0
preproc_if	directive	corpus:action_group_preprocessor_test.txt#Action group with preprocessor conditional actionref#0
preproc_not_expression	directive	corpus:action_group_preprocessor_test.txt#Action group with preprocessor conditional actionref#0
preproc_open	directive	corpus:action_group_preprocessor_test.txt#Action group with preprocessor conditional actionref#0
preproc_operand_prefix	assembler	corpus:preproc_dangling_operator_continuation_test.txt#An expression whose operator dangles before %23if keeps one binary expression#0
preproc_or_expression	directive	corpus:preproc_compound_conditions.txt#Preprocessor with OR condition#0
preproc_parenthesized_expression	directive	corpus:preproc_expression_parens_test.txt#Parenthesized preprocessor condition#0
preproc_pragma_only	branch-container	corpus:pragma_if_between_field_header_and_body.txt#Pragma-only %23if/%23endif between field header and body (BC CLEANxx pattern)#0
preproc_region	trivia	corpus:malformed_region_directive_test.txt#Correct region directive syntax#0
preproc_split_begin	token-alias	corpus:preproc_begin_end_named_test.txt#PRIORITY GUARD: begin immediately before %23endif stays preproc_split_begin#0
preproc_split_block_close_after_endif	assembler	corpus:split_procedure_boundary_test.txt#An %23else branch ends the procedure and opens the next one#0
preproc_split_block_end_in_else	assembler	corpus:split_procedure_boundary_test.txt#An %23else branch ends the procedure and opens the next one#0
preproc_split_brace_close	assembler	fixture:split_brace_close.al
preproc_split_brace_close_if_only	assembler	corpus:preproc_split_layout_closing.txt#Layout addlast modification with closing brace inside %23if (no %23else)#0
preproc_split_call_statement	assembler	corpus:preproc_split_call_argument.txt#Split call statement: function call with first argument in %23if/%23else#0
preproc_split_case_branch	assembler	fixture:split_case_branch.al
preproc_split_case_end_branch	fragment	corpus:preproc_split_brace_and_case_test.txt#A case statement whose own end lives inside each branch#0
preproc_split_case_extended	assembler	corpus:preproc_split_case_extra_branches.txt#Case with extra branches in %23if and modified pattern#0
preproc_split_case_statement_end	assembler	corpus:preproc_split_brace_and_case_test.txt#A case statement whose own end lives inside each branch#0
preproc_split_code_block_end	assembler	corpus:preproc_split_code_block_end_elif_test.txt#split code block end: %23elif branch, both branches bare end;#0
preproc_split_code_block_over_endif	assembler	corpus:preproc_block_over_conditional_test.txt#Shape A: begin opens in one %23if, shared code follows, end; closes in a later %23if#0
preproc_split_complete_body	assembler	corpus:preproc_split_complete_body.txt#Trigger with complete body split across %23if/%23else (Pattern 1)#0
preproc_split_container_reopen	assembler	corpus:split_container_reopen_test.txt#A %23if branch closes a layout group and opens a sibling group#0
preproc_split_declaration	assembler	corpus:declared_but_unexercised_fields_test.txt#preproc_split_declaration.base_object -- an extension object split across %23if#0
preproc_split_else_begin_over_endif	assembler	corpus:preproc_block_over_conditional_test.txt#Shape C: end else begin inside a %23if, with the else block's end; outside it#0
preproc_split_end	token-alias	corpus:preproc_split_code_block_end_elif_test.txt#split code block end: %23elif branch, both branches bare end;#0
preproc_split_field	assembler	corpus:preproc_split_declarations.txt#Preprocessor-split field section with different names#0
preproc_split_if_begin_asymmetric	assembler	corpus:preproc_begin_end_named_test.txt#PRIORITY GUARD: begin immediately before %23endif stays preproc_split_begin#0
preproc_split_if_begin_else	assembler	corpus:preproc_split_if_begin_else.txt#Preprocessor split if-then-begin with else alternative#0
preproc_split_if_else_statement	assembler	corpus:preproc_fragmented_if_else_in_repeat.txt#Preprocessor fragmented if-else inside repeat-until loop#0
preproc_split_if_statement	assembler	corpus:declared_but_unexercised_fields_test.txt#preproc_split_if_statement.else_branch -- the shared tail carries an else#0
preproc_split_if_then_begin	assembler	corpus:preproc_split_block_over_endif_test.txt#A split block nested as the then-branch of an ordinary if#0
preproc_split_if_then_begin_else_shared	assembler	corpus:preproc_split_block_over_endif_test.txt#Both %23if and %23else open a block, one shared end else begin follows#0
preproc_split_key	assembler	corpus:split_key_modify_header_test.txt#Split key and modify headers with a shared body after %23endif#0
preproc_split_modify	assembler	corpus:split_key_modify_header_test.txt#Split key and modify headers with a shared body after %23endif#0
preproc_split_open_statement	assembler	corpus:split_open_statement_test.txt#Branches ending in an open statement prefix, completed after %23endif#0
preproc_split_permissions_property	assembler	corpus:split_comma_lists_test.txt#Permissions head repeated per %23if branch, shared tail after %23endif#0
preproc_split_procedure	assembler	corpus:attribute_preproc_procedure.txt#Var section followed by attributed procedure in preprocessor#0
preproc_split_procedure_body	assembler	corpus:preproc_split_procedure_tail_test.txt#Split signature followed by a split procedure body#0
preproc_split_procedure_preamble	assembler	corpus:preproc_split_procedure_preamble_test.txt#Procedure with header and var both split across %23if/%23else, shared body after %23endif#0
preproc_split_report_brace_close	fragment	corpus:preproc_split_brace_and_case_test.txt#A report dataitem whose closing brace is inside a branch#0
preproc_split_report_dataitem_header	assembler	corpus:preproc_split_brace_and_case_test.txt#A report dataitem header that differs between branches, shared body#0
preproc_split_report_dataitem_open_over_endif	assembler	corpus:preproc_split_brace_and_case_test.txt#A report dataitem opened inside a branch and closed after %23endif#0
preproc_split_table_field	assembler	corpus:preproc_split_field_type.txt#Field header type split across preprocessor branches#0
preproc_split_table_field_open	assembler	corpus:split_table_field_open_test.txt#Field body opened inside %23if, closed after %23endif (one valid configuration)#0
preproc_split_var_section_tail	assembler	corpus:var_section_does_not_swallow_procedures_test.txt#A branch that continues the var section and then starts procedures#0
preproc_undef	trivia	corpus:preproc_define_undef_test.txt#%23define followed by %23undef#0
```

Run: `awk -F'\t' '!/^#/ && NF != 3' tests/traversal/witnesses.tsv | wc -l; sha256sum tests/traversal/witnesses.tsv`
Expected: `0`, then `437ef01e199b542d8d522bc3a3b8564bb7f605e66cb6575124b9d8a710cf0fde  tests/traversal/witnesses.tsv`.

- [ ] **Step 2: Write the witness tests**

`tests/traversal/test_witnesses.py`:

```python
"""Witnesses (spec 6.1/6.2 item 2, D8): one per policy entry, then the named exceptions.

Every witness runs twice: against the real policy (must pass) and against a mutant
(must FAIL). A witness that cannot fail is not a witness.
"""
import csv
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROWS = [r for r in csv.DictReader((line for line in (HERE / "witnesses.tsv").read_text(encoding="utf-8").splitlines()
                                   if not line.startswith("#")), delimiter="\t")]

# The mutant each class must reject. "transparent" (ordinary) is the spec's named
# mutant for expression_tail (6.2 item 2); ordinary itself is mutated to trivia.
MUTANT = {"branch-container": "ordinary", "assembler": "ordinary", "fragment": "ordinary",
          "token-alias": "ordinary", "directive": "ordinary", "trivia": "ordinary", "ordinary": "trivia"}


def mutate(T, policy, type_, **changes):
    return T.Policy({**policy.types, type_: {**policy.types[type_], **changes}})


def check_witness(T, policy, doc, type_, expected):
    default = [v for v in T.walk(doc, policy) if v.type == type_]
    every = [v for v in T.walk(doc, policy, include_directives=True, include_trivia=True) if v.type == type_]
    assert every, f"the witness does not produce {type_}"
    if expected in ("directive", "trivia"):
        assert default == [], f"{type_} must be skipped unless requested"
        assert {v.cls for v in every} == {expected}
        return
    assert default and {v.cls for v in default} == {expected}
    for v in default:
        if expected == "branch-container":
            assert v.split and v.split.groups and v.host is not None
        elif expected == "assembler":
            assert v.split and v.split.groups
        elif expected == "fragment":
            if v.split is None:
                assert v.arms, "a fragment without its own directives sits in an arm of its consumer"
        elif expected == "token-alias":
            assert v.split is None and v.node.child_count == 0
        else:
            assert v.split is None


@pytest.mark.parametrize("row", ROWS, ids=[r["type"] for r in ROWS])
def test_every_policy_entry_has_a_passing_witness(T, policy, doc_of, row):
    check_witness(T, policy, doc_of(row["source"]), row["type"], row["class"])


@pytest.mark.parametrize("row", ROWS, ids=[r["type"] for r in ROWS])
def test_every_witness_fails_its_mutant(T, policy, doc_of, row):
    bad = mutate(T, policy, row["type"], **{"class": MUTANT[row["class"]]})
    with pytest.raises(AssertionError):
        check_witness(T, bad, doc_of(row["source"]), row["type"], row["class"])


def test_witness_rows_cover_the_policy_exactly(policy):
    assert sorted(r["type"] for r in ROWS) == sorted(policy.types)


# --- the named exceptions of spec 6.1, each with its own assertion and mutant ----------

def frags(arm, doc):
    return [(f.field, f.type, doc.source[f.node.start_byte:f.node.end_byte].decode()) for f in arm.fragments]


def one(T, policy, doc, type_):
    found = [v for v in T.walk(doc, policy) if v.type == type_]
    assert len(found) == 1, f"{len(found)} visits of {type_}"
    return found[0]


def expression_tail(T, policy, doc):
    v = one(T, policy, doc, "preproc_conditional_expression_tail")
    assert v.cls == "assembler" and v.split is not None
    (group,) = v.split.groups
    assert [frags(a, doc) for a in group.arms] == [[("operator", "+", "+"), ("operand", "integer", "1")]]
    # The continuation sits AFTER the expression it extends: `right` is the bare X.
    parent = v.node.parent
    assert parent.type == "assignment_statement"
    assert doc.source[parent.child_by_field_name("right").start_byte:
                      parent.child_by_field_name("right").end_byte] == b"X"


def table_relation(T, policy, doc):
    v = one(T, policy, doc, "preproc_conditional_table_relation")
    assert v.cls == "assembler"
    (group,) = v.split.groups
    assert [[(f, t) for f, t, _ in frags(a, doc)] for a in group.arms] == \
        [[(None, "else_table_relation_fragment"), (None, ";")]] * 2
    fragments = [x for x in T.walk(doc, policy) if x.type == "else_table_relation_fragment"]
    assert [x.cls for x in fragments] == ["fragment", "fragment"]
    assert [x.arms[-1][1] for x in fragments] == [0, 1]


def property_value(T, policy, doc):
    v = one(T, policy, doc, "preproc_conditional_property_value")
    assert v.cls == "assembler" and v.field == "value"
    (group,) = v.split.groups
    assert [frags(a, doc) for a in group.arms] == [[("value", "identifier", "CustomerContent"), (None, ";", ";")],
                                                   [("value", "identifier", "SystemMetadata"), (None, ";", ";")]]


def case_end_branch(T, policy, doc):
    owner = one(T, policy, doc, "preproc_split_case_statement_end")
    (group,) = owner.split.groups
    assert [[t for _, t, _ in frags(a, doc)] for a in group.arms] == [["preproc_split_case_end_branch"]] * 2
    branches = [x for x in T.walk(doc, policy) if x.type == "preproc_split_case_end_branch"]
    assert [(x.cls, x.split, x.arms[-1][1]) for x in branches] == [("fragment", None, 0), ("fragment", None, 1)]


def report_brace_close(T, policy, doc):
    v = one(T, policy, doc, "preproc_split_report_brace_close")
    assert v.cls == "fragment" and v.node.parent.type == "report_dataitem"
    (group,) = v.split.groups
    assert [[t for _, t, _ in frags(a, doc)] for a in group.arms] == [["report_body", "}"], ["report_body"]]


def _split_token(T, policy, doc, type_, alias):
    visits = [x for x in T.walk(doc, policy) if x.type == type_]
    assert visits and {(x.cls, x.split) for x in visits} == {("token-alias", None)}
    assert policy.types[type_]["alias_to"] == alias


def split_begin_token(T, policy, doc):
    _split_token(T, policy, doc, "preproc_split_begin", "begin_keyword")


def split_end_token(T, policy, doc):
    _split_token(T, policy, doc, "preproc_split_end", "end_keyword")


def pragma_in_arm(T, policy, doc):
    assert not [x for x in T.walk(doc, policy) if x.type == "pragma"]
    assert {x.cls for x in T.walk(doc, policy, include_trivia=True) if x.type == "pragma"} == {"trivia"}
    decl = one(T, policy, doc, "preproc_split_declaration")
    first = [t for _, t, _ in frags(decl.split.groups[0].arms[0], doc)]
    assert first[0] == "pragma" and first[-1] == "pragma", "trivia inside an arm stays one of its fragments"


def list_run_separator(T, policy, doc):
    v = one(T, policy, doc, "preproc_conditional_permissions")
    assert v.host == "list-run"
    assert (None, ",", ",") in frags(v.split.groups[0].arms[1], doc)


def list_run_terminator(T, policy, doc):
    v = one(T, policy, doc, "preproc_conditional_permissions")
    assert v.host == "list-run"
    # The PROPERTY's own ';' sits inside each arm (terminator-hoist): the last fragment.
    assert [frags(a, doc)[-1] for a in v.split.groups[0].arms] == [(None, ";", ";")] * 2


NAMED = [  # (check, fixture, policy type to mutate, mutation)
    (expression_tail, "assemblers.al", "preproc_conditional_expression_tail", {"class": "ordinary"}),
    (table_relation, "assemblers.al", "preproc_conditional_table_relation", {"class": "ordinary"}),
    (table_relation, "assemblers.al", "else_table_relation_fragment", {"class": "ordinary"}),
    (property_value, "assemblers.al", "preproc_conditional_property_value", {"class": "ordinary"}),
    (case_end_branch, "assemblers.al", "preproc_split_case_end_branch", {"class": "ordinary"}),
    (report_brace_close, "corpus:preproc_split_brace_and_case_test.txt#A report dataitem whose closing brace is inside a branch#0",
     "preproc_split_report_brace_close", {"class": "ordinary"}),
    (split_end_token, "corpus:preproc_split_code_block_end_elif_test.txt#split code block end: %23elif branch, both branches bare end;#0",
     "preproc_split_end", {"class": "ordinary"}),
    (split_begin_token, "corpus:preproc_begin_end_named_test.txt#PRIORITY GUARD: begin immediately before %23endif stays preproc_split_begin#0",
     "preproc_split_begin", {"class": "ordinary"}),
    (pragma_in_arm, "split_declaration.al", "pragma", {"class": "ordinary"}),
    (list_run_separator, "assemblers.al", "preproc_conditional_permissions",
     {"hosts": {"declaration_body:<children>": "list-run"}}),
    (list_run_terminator, "assemblers.al", "preproc_conditional_permissions",
     {"hosts": {"declaration_body:<children>": "list-run"}}),
]


@pytest.mark.parametrize("check,source,type_,change", NAMED, ids=[f"{c.__name__}-{t}" for c, _, t, _ in NAMED])
def test_named_exception(T, policy, doc_of, check, source, type_, change):
    src = source if source.startswith("corpus:") else "fixture:" + source
    check(T, policy, doc_of(src))
    with pytest.raises(AssertionError):
        check(T, mutate(T, policy, type_, **change), doc_of(src))


@pytest.mark.parametrize("check", [list_run_separator, list_run_terminator])
def test_list_run_witnesses_fail_when_anonymous_tokens_are_dropped(T, policy, doc_of, monkeypatch, check):
    """A code mutant, not a policy one: bind_arm keeping named nodes only."""
    doc = doc_of("fixture:assemblers.al")
    check(T, policy, doc)
    real = T.bind_arm

    def named_only(descriptor, document, pol):
        arm = real(descriptor, document, pol)
        return T.ArmFragments(arm.descriptor, tuple(f for f in arm.fragments if f.node.is_named))

    monkeypatch.setattr(T, "bind_arm", named_only)
    with pytest.raises(AssertionError):
        check(T, policy, doc)
```

The named list is spec §6.1's exceptions one by one: `expression_tail` (continuation after `#endif`), `table_relation` and `property_value` (assemblers), `else_table_relation_fragment` (no prefix), `preproc_split_begin`/`preproc_split_end` (token aliases), `preproc_split_case_end_branch` and `preproc_split_report_brace_close` (fragments), `pragma` (not in the registry), and the two `list-run` cases (a separator, and the property's own `;` terminator inside an arm). The 27 registry-`unsupported` types are covered by the per-entry rows, so their set comes from the policy, never from a count.

- [ ] **Step 3: Run them**

Run: `./tools/ts-lock.sh python -m pytest tests/traversal/test_witnesses.py -q`
Expected: `192 passed` (89 witnesses, 89 mutants that fail them, 1 coverage check, 11 named exceptions with their mutants, 2 code mutants).

- [ ] **Step 4: Prove the mutants are load-bearing**

Temporarily change `MUTANT["assembler"]` to `"assembler"` (a mutant identical to the truth) and run `./tools/ts-lock.sh python -m pytest tests/traversal/test_witnesses.py -q -k mutant`.
Expected: the 39 assembler mutant cases FAIL with `DID NOT RAISE <class 'AssertionError'>`. Revert the change and rerun: all pass.

- [ ] **Step 5: Commit**

```bash
git add tests/traversal/witnesses.tsv tests/traversal/test_witnesses.py
git commit -m "test(traversal): a witness per policy entry and per spec 6.1 exception (roadmap F0)

Each runs against the real policy and against a mutant that must fail it,
including the spec's transparent expression_tail; the list-run separator and
terminator witnesses also fail when bind_arm drops anonymous tokens."
```

---

### Task 5: The shared expected visits (D4)

**Files:**
- Modify: `bindings/python/tree_sitter_al/traversal.py` (append `dump_expected`)
- Create: `tests/traversal/regen_expected.py`, `tests/traversal/test_parity.py`, twelve `tests/traversal/fixtures/*.visits.json` (generated)

**Interfaces:**
- Consumes: `T.walk`, `T.visits_to_json` (Task 3).
- Produces: `dump_expected(document, visits) -> str` — `{"revision": "<fnv1a64>", "visits": [` then one parity-form visit per line `]}`; the twelve `*.visits.json` files Tasks 6 and 7 compare against.

- [ ] **Step 1: Write the failing parity test**

`tests/traversal/test_parity.py`:

```python
"""The shared expected-visit files (D4): one per fixture, current with the Python walker.

JS (tests/traversal/js/parity.test.js) and Rust (bindings/rust/traversal.rs) compare
their own walks against the same files, so the three runtimes agree byte for byte
on class, type, field, offsets, arm identity, host policy and SplitInfo.
"""
import json

import pytest

import support

ALS = sorted(support.FIXTURES.glob("*.al"))


def test_every_fixture_has_an_expected_file_and_no_file_is_orphaned():
    assert len(ALS) == 12
    assert sorted(p.stem for p in support.FIXTURES.glob("*.visits.json")) == \
        sorted(p.stem + ".visits" for p in ALS)


@pytest.mark.parametrize("path", ALS, ids=[p.name for p in ALS])
def test_expected_visits_are_current(T, policy, al_parser, path):
    source = path.read_bytes()
    doc = T.Document(al_parser.parse(source), source, policy)
    want = path.with_suffix(".visits.json").read_text(encoding="utf-8")
    got = T.dump_expected(doc, T.walk(doc, policy))
    assert got == want, f"{path.name}: run tests/traversal/regen_expected.py, then review the diff"
    assert json.loads(want)["revision"] == doc.revision
```

Run: `./tools/ts-lock.sh python -m pytest tests/traversal/test_parity.py -q`
Expected: 13 failures (no `.visits.json` files, no `dump_expected`).

- [ ] **Step 2: Add `dump_expected`**

Append to `bindings/python/tree_sitter_al/traversal.py`:

```python
def dump_expected(document: Document, visits) -> str:
    """A fixture's expected-visits file: one visit per line, so a review reads a diff."""
    lines = [json.dumps(v, ensure_ascii=False) for v in visits_to_json(visits)]
    return '{"revision": "%s", "visits": [\n%s\n]}\n' % (document.revision, ",\n".join(lines))
```

- [ ] **Step 3: Write the regeneration script**

`tests/traversal/regen_expected.py`:

```python
#!/usr/bin/env python3
"""Rewrite tests/traversal/fixtures/*.visits.json from the Python walker.

The same trap as `tree-sitter test -u`: this blesses whatever the walker does today.
Run it only after a deliberate change, then read `git diff tests/traversal/fixtures`
hunk by hunk and trace each one to that change. The hand-written tests in
test_walk.py, test_split.py and test_witnesses.py are what say the walker is RIGHT;
these files only make the three runtimes agree with it.

    python tests/traversal/regen_expected.py
"""
import support

T = support.load_traversal()
policy = T.load_policy(support.POLICY)
parser = support.make_parser()
for path in sorted(support.FIXTURES.glob("*.al")):
    source = path.read_bytes()
    doc = T.Document(parser.parse(source), source, policy)
    out = path.with_suffix(".visits.json")
    out.write_text(T.dump_expected(doc, T.walk(doc, policy)), encoding="utf-8", newline="\n")
    print(f"wrote {out.relative_to(support.REPO).as_posix()}")
```

- [ ] **Step 4: Generate, then review every file**

Run: `./tools/ts-lock.sh python tests/traversal/regen_expected.py`
Expected: twelve `wrote tests/traversal/fixtures/<name>.visits.json` lines.

Read each file against its `.al`. Spot checks that must hold: in `containers.visits.json` the `preproc_conditional_object` visit has `"start": 93`, `"host": "splice-repeat"`; the visit for `X := 3` has `"arms": [[93, 1], [441, 0], [489, 0]]`; in `assemblers.visits.json` the `preproc_split_procedure` visit's `split.shared` is `[["body", "code_block", true, 384, 421], [null, ";", false, 421, 422]]`; `unbalanced.visits.json` has an `ERROR` visit with `"split": null`.

Run: `sha256sum tests/traversal/fixtures/*.visits.json`
Expected:
```text
ce36ee34ef546557aeb2a19b568fcc924fc4ffff9a1f2b8a0280d799dd59c33d  tests/traversal/fixtures/assemblers.visits.json
6f08beef083378a85344238ddf3275e98b90f1b3878e2e1510d04310031cc8e1  tests/traversal/fixtures/containers.visits.json
f851ac0a7e72ef16c1d08bb87bfe965d8821f4f37835df33fe644306aee2eb8b  tests/traversal/fixtures/crlf_bom.visits.json
6b9e4ed70aae7437671da6b04705c4da5163f601b5c344eb239aaa4dda48059a  tests/traversal/fixtures/cross_node.visits.json
67ff578547e93544765148be3cba593687689a40f5d107eecded3b3e35bfa34d  tests/traversal/fixtures/elif_chain.visits.json
490d5ef455336022e3b40100b72617c3bfddc1ec286302af6cc74ca3b34f476c  tests/traversal/fixtures/impl_values.visits.json
7caeb769b9d07da2d355754a9f57bbac6b4b0da4f7191bea624a2cea4a0d7ef4  tests/traversal/fixtures/query_conditional.visits.json
4ea444d2204d469a352b499d738b84814be6ab7746d54688f244623f1750259b  tests/traversal/fixtures/split_brace_close.visits.json
4b7ac9ddf2baeded9f68c703801a72f50c51b67148b7e3bedda825c5dda7f3de  tests/traversal/fixtures/split_case_branch.visits.json
84ddbc962ef95544a1663b55ed00e185804496979cbc64154a957c5a925723d9  tests/traversal/fixtures/split_declaration.visits.json
0e79e4377efde44c9bfc96b9e1f36294a63f91af733a85f48500ce9bdb6d3c00  tests/traversal/fixtures/stray_endif.visits.json
5165a76fbcc8bebff1bb47d002f3f366b641b0b61b09de0a723f1c8d09edd497  tests/traversal/fixtures/unbalanced.visits.json
```

- [ ] **Step 5: Run the whole Python suite**

Run: `./tools/ts-lock.sh python -m pytest tests/traversal -q`
Expected: `241 passed`.

- [ ] **Step 6: Commit**

```bash
git add bindings/python/tree_sitter_al/traversal.py tests/traversal/regen_expected.py tests/traversal/test_parity.py tests/traversal/fixtures/*.visits.json
git commit -m "test(traversal): shared expected visits for every runtime (roadmap F0, D4)

One .visits.json per fixture, written by the Python walker and checked
current; JS and Rust compare against the same files. Regenerating is a -u:
review every hunk."
```

---

### Task 6: The JavaScript implementation, under native `tree-sitter` and `web-tree-sitter`

**Files:**
- Create: `traversal/index.js`, `traversal/index.d.ts`, `tests/traversal/js/parity.test.js`
- Modify: `package.json` (`devDependencies`), `package-lock.json` (by npm)

**Interfaces:**
- Consumes: `traversal/policy.json` (bundled with `require('./policy.json')`), the `*.visits.json` files (Task 5).
- Produces: the JS API in "Shared interfaces", the `require('@sshadows/tree-sitter-al/traversal')` entry point (a directory with `index.js`, so no `exports` map is needed and every existing deep import keeps working).

- [ ] **Step 1: Install the native runtime and rebuild the native binding**

Run: `npm install --save-dev tree-sitter@^0.25.0`
Expected: `package.json` `devDependencies` gains `"tree-sitter": "^0.25.0"`; it installs from prebuilds.

Run: `npx node-gyp rebuild`
Expected: `gyp info ok`. This matters: the repo's `build/Release` binding is not rebuilt by `tree-sitter generate`, and a stale one parses older trees (measured while planning: the native leg failed every fixture until rebuilt; web-tree-sitter, which loads the committed and freshness-gated `tree-sitter-al.wasm`, passed).

- [ ] **Step 2: Write the failing parity test**

`tests/traversal/js/parity.test.js`:

```js
'use strict';
// The ONE JS implementation (traversal/index.js) under BOTH JS runtimes, against the
// expected-visit files the Python walker wrote (D4, D5). Run: node --test tests/traversal/js/
const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const REPO = path.resolve(__dirname, '..', '..', '..');
const FIX = path.join(REPO, 'tests', 'traversal', 'fixtures');
const T = require(path.join(REPO, 'traversal'));
const req = require('node:module').createRequire(path.join(REPO, 'package.json'));

const FIXTURES = fs.readdirSync(FIX).filter((f) => f.endsWith('.al')).sort();
const policy = T.loadPolicy();
const parsers = {};

test.before(async () => {
  const { Parser, Language } = req('web-tree-sitter');
  await Parser.init();
  const web = new Parser();
  web.setLanguage(await Language.load(path.join(REPO, 'tree-sitter-al.wasm')));
  parsers['web-tree-sitter'] = web;
  const Native = req('tree-sitter');
  const native = new Native();
  native.setLanguage(require(path.join(REPO, 'bindings', 'node')));
  parsers['native tree-sitter'] = native;
});

test('there are twelve fixtures, each with an expected-visits file', () => {
  assert.strictEqual(FIXTURES.length, 12);
  for (const f of FIXTURES) assert.ok(fs.existsSync(path.join(FIX, f.replace(/\.al$/, '.visits.json'))), f);
});

for (const runtime of ['web-tree-sitter', 'native tree-sitter']) {
  for (const f of FIXTURES) {
    test(`${runtime}: ${f} matches its expected visits`, () => {
      const text = fs.readFileSync(path.join(FIX, f), 'utf8');
      const want = JSON.parse(fs.readFileSync(path.join(FIX, f.replace(/\.al$/, '.visits.json')), 'utf8'));
      const doc = new T.Document(parsers[runtime].parse(text), text, policy);
      const got = { revision: doc.revision, visits: T.visitsToJson(T.walk(doc, policy), doc) };
      // A native mismatch with a clean web run is almost always a STALE native build
      // (build/Release predates src/): rebuild with `npx node-gyp rebuild`.
      assert.deepStrictEqual(got, want);
    });
  }
}

test('fnv1a64 reference vectors', () => {
  assert.strictEqual(T.fnv1a64(new Uint8Array([])), 'cbf29ce484222325');
  assert.strictEqual(T.fnv1a64(new TextEncoder().encode('a')), 'af63dc4c8601ec8c');
});

test('byteTable maps UTF-16 indexes to UTF-8 byte offsets, surrogate pairs included', () => {
  assert.deepStrictEqual(Array.from(T.byteTable('a\u{1F600}é')), [0, 1, 1, 5, 7]);
  assert.deepStrictEqual(Array.from(T.byteTable('\ud800a')), [0, 3, 4]); // lone surrogate = U+FFFD, 3 bytes
});

test('loadPolicy rejects an unknown schema or class', () => {
  assert.throws(() => T.loadPolicy({ schema: 2, types: {} }), T.PolicyError);
  assert.throws(() => T.loadPolicy({ schema: 1, types: { x: { class: 'special' } } }), T.PolicyError);
});

test('bindArm rejects a descriptor from another document', () => {
  const p = parsers['web-tree-sitter'];
  const read = (f) => fs.readFileSync(path.join(FIX, f), 'utf8');
  const a = new T.Document(p.parse(read('containers.al')), read('containers.al'), policy);
  const b = new T.Document(p.parse(read('elif_chain.al')), read('elif_chain.al'), policy);
  assert.throws(() => T.bindArm(a.descriptors()[0], b, policy), T.WrongDocument);
});

test('the traversal module never loads the native addon', () => {
  const src = fs.readFileSync(path.join(REPO, 'traversal', 'index.js'), 'utf8');
  assert.deepStrictEqual(src.match(/require\([^)]*\)/g), ["require('./policy.json')"]);
});
```

Run: `node --test tests/traversal/js/parity.test.js`
Expected: FAIL, `Cannot find module '.../traversal'`.

- [ ] **Step 3: Write the implementation**

`traversal/index.js`:

```js
'use strict';
// Classified traversal over the all-branches AL tree (roadmap F0, spec 5.1 and 6).
//
// ONE implementation for both JS runtimes: it touches only the SyntaxNode API
// that the native `tree-sitter` binding and `web-tree-sitter` share (type,
// isNamed, startIndex, endIndex, childCount, child(i), fieldNameForChild(i),
// parent, id). It never requires the native addon, so it is browser-safe.
//
// Both runtimes index the source as UTF-16 code units. Every position this
// module reports is a canonical UTF-8 byte offset, converted from the text.
// Node classes come from the hand-maintained policy.json, never from a name.

const BUNDLED = require('./policy.json');

const SCHEMA = 1;
const CLASSES = ['ordinary', 'branch-container', 'assembler', 'fragment', 'token-alias', 'directive', 'trivia'];
// Only these get a SplitInfo on their visit (see the Python module).
const SPLIT_CLASSES = ['branch-container', 'assembler', 'fragment'];

class PolicyError extends Error {}
class WrongDocument extends Error {}

class Policy {
  constructor(types) { this.types = types; }
  cls(type) { const e = this.types[type]; return e ? e.class : 'ordinary'; }
  role(type) { const e = this.types[type]; return (e && e.role) || null; }
  hostPolicy(container, parent, field) {
    const e = this.types[container];
    const hosts = (e && e.hosts) || {};
    const p = hosts[`${parent}:${field || '<children>'}`];
    return p === undefined ? null : p;
  }
}

function loadPolicy(data = BUNDLED) {
  if (data.schema !== SCHEMA) throw new PolicyError(`policy schema ${data.schema}, expected ${SCHEMA}`);
  for (const [type, entry] of Object.entries(data.types)) {
    if (!CLASSES.includes(entry.class)) throw new PolicyError(`${type}: unknown class ${entry.class}`);
  }
  return new Policy(data.types);
}

function fnv1a64(bytes) {
  let h = 0xcbf29ce484222325n;
  for (const b of bytes) h = ((h ^ BigInt(b)) * 0x100000001b3n) & 0xffffffffffffffffn;
  return h.toString(16).padStart(16, '0');
}

// UTF-16 index -> UTF-8 byte offset, for every index 0..text.length.
function byteTable(text) {
  const t = new Uint32Array(text.length + 1);
  let b = 0;
  let i = 0;
  while (i < text.length) {
    t[i] = b;
    const c = text.charCodeAt(i);
    if (c >= 0xd800 && c <= 0xdbff && i + 1 < text.length) {
      const d = text.charCodeAt(i + 1);
      if (d >= 0xdc00 && d <= 0xdfff) { t[i + 1] = b; b += 4; i += 2; continue; }
    }
    b += c < 0x80 ? 1 : c < 0x800 ? 2 : 3;
    i += 1;
  }
  t[text.length] = b;
  return t;
}

function kids(node) {
  const out = [];
  for (let i = 0; i < node.childCount; i++) out.push([node.fieldNameForChild(i) || null, node.child(i)]);
  return out;
}

class Document {
  constructor(tree, text, policy) {
    this.tree = tree;
    this.text = text;
    this.bytes = byteTable(text);
    this.revision = fnv1a64(new TextEncoder().encode(text));
    const { groups, unpaired, byParent } = pair(this, policy);
    this.groups = groups;
    this.unpaired = unpaired;
    this.byParent = byParent;
  }
  start(node) { return this.bytes[node.startIndex]; }
  // UTF-8 byte offset -> the first UTF-16 index at or after it (binary search).
  index(byte) {
    let lo = 0;
    let hi = this.text.length;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (this.bytes[mid] < byte) lo = mid + 1; else hi = mid;
    }
    return lo;
  }
  end(node) { return this.bytes[node.endIndex]; }
  descriptors() { return this.groups.flatMap((g) => g.arms); }
}

function pair(doc, policy) {
  const open = [];
  const done = [];
  const unpaired = [];
  const byParentOffsets = new Map();
  const stack = [doc.tree.rootNode];
  while (stack.length) {
    const node = stack.pop();
    const role = node.isNamed ? policy.role(node.type) : null;
    if (role === null) {
      for (let i = node.childCount - 1; i >= 0; i--) stack.push(node.child(i));
      continue;
    }
    const d = { role, start: doc.start(node), end: doc.end(node), node };
    if (role === 'if') open.push([d]);
    else if (!open.length) { unpaired.push(d); continue; } else open[open.length - 1].push(d);
    const group = open[open.length - 1];
    const pid = node.parent.id;
    if (!byParentOffsets.has(pid)) byParentOffsets.set(pid, []);
    const offs = byParentOffsets.get(pid);
    if (!offs.includes(group[0].start)) offs.push(group[0].start);
    if (role === 'endif') done.push(open.pop());
  }
  done.push(...open);
  done.sort((a, b) => a[0].start - b[0].start);
  const eof = doc.bytes[doc.text.length];
  const byIf = new Map();
  for (const ds of done) {
    const arms = [];
    ds.forEach((d, idx) => {
      if (d.role === 'endif') return;
      const closer = idx + 1 < ds.length ? ds[idx + 1] : null;
      arms.push({
        groupId: [doc.revision, ds[0].start],
        armId: arms.length,
        directiveOffsets: closer ? [d.start, closer.start] : [d.start],
        rawRange: [d.end, closer ? closer.start : eof],
      });
    });
    byIf.set(ds[0].start, { ifOffset: ds[0].start, directives: ds, arms });
  }
  const byParent = new Map();
  for (const [pid, offs] of byParentOffsets) byParent.set(pid, offs.map((o) => byIf.get(o)));
  return { groups: [...byIf.values()], unpaired, byParent };
}

function groupsOf(node, doc) { return doc.byParent.get(node.id) || []; }

function bindArm(descriptor, doc, policy) {
  if (descriptor.groupId[0] !== doc.revision) {
    throw new WrongDocument(`descriptor revision ${descriptor.groupId[0]} != document ${doc.revision}`);
  }
  const [lo, hi] = descriptor.rawRange;
  const out = [];
  // Start at the smallest node holding the whole arm (see the Python module).
  let top = doc.tree.rootNode.descendantForIndex(doc.index(lo), doc.index(hi)) || doc.tree.rootNode;
  while (top.parent && lo <= doc.start(top) && doc.end(top) <= hi) top = top.parent;
  const stack = [[top, null]];
  while (stack.length) {
    const [node, field] = stack.pop();
    const s = doc.start(node);
    const e = doc.end(node);
    if (e <= lo || s >= hi) continue;
    if (lo <= s && e <= hi) {
      if (!(node.isNamed && policy.cls(node.type) === 'directive')) out.push({ field, node });
      continue;
    }
    const ks = kids(node);
    for (let i = ks.length - 1; i >= 0; i--) stack.push([ks[i][1], ks[i][0]]);
  }
  return { descriptor, fragments: out };
}

function splitInfo(node, doc, policy) {
  const groups = groupsOf(node, doc);
  if (!groups.length) return null;
  const ranges = groups.flatMap((g) => g.arms.map((a) => a.rawRange));
  const shared = [];
  for (const [field, child] of kids(node)) {
    if (child.isNamed && policy.cls(child.type) === 'directive') continue;
    const s = doc.start(child);
    const e = doc.end(child);
    if (ranges.some(([lo, hi]) => lo <= s && e <= hi)) continue;
    shared.push({ field, node: child });
  }
  return {
    groups: groups.map((g) => ({ groupId: [doc.revision, g.ifOffset], arms: g.arms.map((a) => bindArm(a, doc, policy)) })),
    shared,
  };
}

function walk(doc, policy, { root = null, includeDirectives = false, includeTrivia = false } = {}) {
  const arms = doc.descriptors().slice().sort((a, b) => (a.rawRange[0] - b.rawRange[0]) || (b.rawRange[1] - a.rawRange[1]));
  let active = [];
  let k = 0;
  const out = [];
  const stack = [[root || doc.tree.rootNode, null, null]];
  while (stack.length) {
    const [node, field, parent] = stack.pop();
    if (!node.isNamed) continue;
    const cls = policy.cls(node.type);
    if ((cls === 'directive' && !includeDirectives) || (cls === 'trivia' && !includeTrivia)) continue;
    const start = doc.start(node);
    const end = doc.end(node);
    while (k < arms.length && arms[k].rawRange[0] <= start) active.push(arms[k++]);
    active = active.filter((a) => a.rawRange[1] > start);
    const path = active.filter((a) => a.rawRange[1] >= end).map((a) => [a.groupId[1], a.armId]);
    const host = cls === 'branch-container' && parent ? policy.hostPolicy(node.type, parent.type, field) : null;
    out.push({ node, cls, type: node.type, field, start, end, arms: path, host, split: SPLIT_CLASSES.includes(cls) ? splitInfo(node, doc, policy) : null });
    const ks = kids(node);
    for (let i = ks.length - 1; i >= 0; i--) stack.push([ks[i][1], ks[i][0], node]);
  }
  return out;
}

function fragJson(f, doc) { return [f.field, f.node.type, f.node.isNamed, doc.start(f.node), doc.end(f.node)]; }

function splitToJson(s, doc) {
  return {
    groups: s.groups.map((g) => ({
      if: g.groupId[1],
      arms: g.arms.map((a) => ({ arm: a.descriptor.armId, range: [...a.descriptor.rawRange], fragments: a.fragments.map((f) => fragJson(f, doc)) })),
    })),
    shared: s.shared.map((f) => fragJson(f, doc)),
  };
}

function visitsToJson(visits, doc) {
  return visits.map((v) => ({
    class: v.cls, type: v.type, field: v.field, start: v.start, end: v.end,
    arms: v.arms, host: v.host, split: v.split ? splitToJson(v.split, doc) : null,
  }));
}

module.exports = {
  SCHEMA, CLASSES, SPLIT_CLASSES, PolicyError, WrongDocument, Policy, loadPolicy, fnv1a64, byteTable,
  Document, groupsOf, bindArm, splitInfo, walk, visitsToJson,
};
```

Both JS runtimes report `startIndex`/`endIndex` in UTF-16 code units (measured on the native binding: `"Æ😀"` spans 5 units, not 8 bytes), so every position goes through `byteTable`, and `index()` maps back for `descendantForIndex`. The revision is FNV-1a 64 over `TextEncoder` bytes, which a browser has synchronously; `crypto.subtle` would be async.

`traversal/index.d.ts`:

```ts
// Types for @sshadows/tree-sitter-al/traversal (roadmap F0). The module works on the
// native `tree-sitter` SyntaxNode and on web-tree-sitter's Node: it uses only the
// members both share, listed in TSNode. Positions are UTF-8 byte offsets.

export interface TSNode {
  readonly type: string;
  readonly isNamed: boolean;
  readonly startIndex: number;
  readonly endIndex: number;
  readonly childCount: number;
  readonly parent: TSNode | null;
  readonly id: number;
  child(index: number): TSNode | null;
  fieldNameForChild(index: number): string | null;
  descendantForIndex(start: number, end?: number): TSNode | null;
}

export type TraversalClass =
  | 'ordinary' | 'branch-container' | 'assembler' | 'fragment' | 'token-alias' | 'directive' | 'trivia';

export interface PolicyEntry {
  class: TraversalClass;
  arm_boundary: 'own-directives' | 'cross-node' | 'assembler' | 'none';
  reason: string;
  role?: 'if' | 'elif' | 'else' | 'endif';
  alias_to?: string;
  hosts?: Record<string, string>;
}

export interface PolicyData {
  schema: 1;
  types: Record<string, PolicyEntry>;
}

export declare const SCHEMA: 1;
export declare const CLASSES: readonly TraversalClass[];
export declare const SPLIT_CLASSES: readonly TraversalClass[];
export declare class PolicyError extends Error {}
export declare class WrongDocument extends Error {}

export declare class Policy {
  readonly types: Record<string, PolicyEntry>;
  constructor(types: Record<string, PolicyEntry>);
  cls(type: string): TraversalClass;
  role(type: string): string | null;
  hostPolicy(container: string, parent: string, field: string | null): string | null;
}

/** The bundled policy.json, or the data given. */
export declare function loadPolicy(data?: PolicyData): Policy;

export interface Directive<N extends TSNode = TSNode> { role: string; start: number; end: number; node: N }
export interface ArmDescriptor {
  /** [revision, '#if' byte offset] */
  groupId: [string, number];
  armId: number;
  directiveOffsets: number[];
  rawRange: [number, number];
}
export interface Group<N extends TSNode = TSNode> { ifOffset: number; directives: Directive<N>[]; arms: ArmDescriptor[] }
export interface Fragment<N extends TSNode = TSNode> { field: string | null; node: N }
export interface ArmFragments<N extends TSNode = TSNode> { descriptor: ArmDescriptor; fragments: Fragment<N>[] }
export interface GroupArms<N extends TSNode = TSNode> { groupId: [string, number]; arms: ArmFragments<N>[] }
export interface SplitInfo<N extends TSNode = TSNode> { groups: GroupArms<N>[]; shared: Fragment<N>[] }

export interface Visit<N extends TSNode = TSNode> {
  node: N;
  cls: TraversalClass;
  type: string;
  field: string | null;
  start: number;
  end: number;
  /** [ifOffset, armId] pairs, outermost first. */
  arms: [number, number][];
  host: string | null;
  split: SplitInfo<N> | null;
}

export declare class Document<N extends TSNode = TSNode> {
  constructor(tree: { readonly rootNode: N }, text: string, policy: Policy);
  readonly text: string;
  readonly revision: string;
  readonly groups: Group<N>[];
  readonly unpaired: Directive<N>[];
  start(node: N): number;
  end(node: N): number;
  index(byte: number): number;
  descriptors(): ArmDescriptor[];
}

export interface WalkOptions<N extends TSNode = TSNode> {
  root?: N | null;
  includeDirectives?: boolean;
  includeTrivia?: boolean;
}

export declare function groupsOf<N extends TSNode>(node: N, doc: Document<N>): Group<N>[];
export declare function bindArm<N extends TSNode>(descriptor: ArmDescriptor, doc: Document<N>, policy: Policy): ArmFragments<N>;
export declare function splitInfo<N extends TSNode>(node: N, doc: Document<N>, policy: Policy): SplitInfo<N> | null;
export declare function walk<N extends TSNode>(doc: Document<N>, policy: Policy, options?: WalkOptions<N>): Visit<N>[];
export declare function visitsToJson<N extends TSNode>(visits: Visit<N>[], doc: Document<N>): unknown[];
export declare function fnv1a64(bytes: Uint8Array): string;
export declare function byteTable(text: string): Uint32Array;
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `node --test tests/traversal/js/parity.test.js`
Expected: `ℹ tests 30`, `ℹ pass 30`, `ℹ fail 0`.

If only the `native tree-sitter` cases fail, the native build is stale: rerun `npx node-gyp rebuild`, never edit an expectation.

- [ ] **Step 5: The Python static check now covers the JS source**

Run: `./tools/ts-lock.sh python -m pytest tests/traversal/test_census.py -q -k classifies_by_name`
Expected: `1 passed` (it now reads `traversal/index.js`).

- [ ] **Step 6: Commit**

```bash
git add traversal/index.js traversal/index.d.ts tests/traversal/js/parity.test.js package.json package-lock.json
git commit -m "feat(traversal): one JS implementation for native tree-sitter and WASM (roadmap F0, D5)

traversal/index.js uses only the SyntaxNode members both runtimes share and
never loads the native addon. Positions are converted from UTF-16 to UTF-8
bytes. Both runtimes match the shared expected visits on all twelve
fixtures; tree-sitter ^0.25.0 joins devDependencies for the native leg."
```

---

### Task 7: The Rust implementation behind the `traversal` feature

**Files:**
- Create: `bindings/rust/traversal.rs`
- Modify: `Cargo.toml` (`include`, `[features]`, `[dependencies]`, `[dev-dependencies]`), `bindings/rust/lib.rs` (module declaration), `tools/check-runtime-ranges.py:117-127` (`semver`), `tools/tests/test_check_runtime_ranges.py` (one row, three tests), `Cargo.lock` (by cargo)

**Interfaces:**
- Consumes: `crate::LANGUAGE`, `traversal/policy.json` via `include_str!`, the `*.visits.json` files.
- Produces: the Rust API in "Shared interfaces". Feature decision (D6): **a `traversal` feature, default off.** Without it the crate's only dependency stays `tree-sitter-language`; with it, `tree-sitter` (`>=0.25, <0.27`) and `serde_json` (`1`) join — and `serde_json` is already a dependency of tree-sitter 0.25 and 0.26, so a user who enables the feature gains no new crate. Children are read through a `TreeCursor`, whose calls are identical in 0.25 and 0.26 (`Node::child` changed its index type).

- [ ] **Step 1: Declare the feature**

In `Cargo.toml`, add `"traversal/policy.json",` as the last entry of `include`, then replace

```toml
[dependencies]
tree-sitter-language = "0.1"
```

with

```toml
[features]
default = []
# The classified traversal helper (roadmap F0). The only part of this crate that needs
# the tree-sitter runtime; serde_json is already a dependency of tree-sitter 0.25/0.26.
traversal = ["dep:tree-sitter", "dep:serde_json"]

[dependencies]
tree-sitter-language = "0.1"
tree-sitter = { version = ">=0.25, <0.27", optional = true }
serde_json = { version = "1", optional = true }
```

and replace

```toml
[dev-dependencies]
tree-sitter = "0.25"
```

with

```toml
[dev-dependencies]
tree-sitter = ">=0.25, <0.27"
serde_json = "1"
```

In `bindings/rust/lib.rs`, after the `TEXTOBJECTS_QUERY` line, add:

```rust

/// Classified traversal over the all-branches tree (roadmap F0): every `#if` arm,
/// with its group and arm identity, and `SplitInfo` for constructs built from arm
/// fragments. Off by default; enable the `traversal` feature. See docs/traversal.md.
#[cfg(feature = "traversal")]
pub mod traversal;
```

- [ ] **Step 2: Teach the runtime-range gate the new range form**

`python tools/check-runtime-ranges.py` now exits 2: `unsupported range '>=0.25, <0.27'`. Write its tests first. In `tools/tests/test_check_runtime_ranges.py`, change the Cargo row of `test_other_old_floors_fail` from

```python
    ("Cargo.toml", 'tree-sitter = "0.25"', 'tree-sitter = "0.24"', "rust"),
```

to

```python
    ("Cargo.toml", 'tree-sitter = ">=0.25, <0.27"', 'tree-sitter = "0.24"', "rust"),
```

and append:

```python
def test_cargo_compound_range_is_read():
    assert crr.semver(">=0.25, <0.27") == ((0, 25, 0), (0, 27, 0))
    assert crr.semver("<0.27, >=0.25.1") == ((0, 25, 1), (0, 27, 0))


def test_cargo_compound_range_with_an_old_floor_fails(root):
    edit(root / "Cargo.toml", 'tree-sitter = { version = ">=0.25, <0.27", optional = true }',
         'tree-sitter = { version = ">=0.24.7, <0.27", optional = true }')
    code, out = run(root)
    assert code == 1, out
    assert "admits 0.24.7..<0.25.0, which loads ABI 13..14, not 15" in out


@pytest.mark.parametrize("spec", [">=0.25, ^0.26", ">=0.25,"])
def test_cargo_compound_range_with_another_operator_exits_2(root, spec):
    edit(root / "Cargo.toml", '">=0.25, <0.27", optional = true', f'"{spec}", optional = true')
    code, out = run(root)
    assert code == 2, out
```

Run: `python -m pytest tools/tests -q`
Expected: most tests FAIL: the script exits 2 on every copy of `Cargo.toml` with `unsupported range '>=0.25, <0.27'`, and `test_cargo_compound_range_is_read` raises `Unreadable`.

Replace `semver` in `tools/check-runtime-ranges.py` with:

```python
def semver(spec: str) -> tuple:
    """npm range or Cargo requirement: ^X, ~X, >=X, =X, bare X, or a comma-joined
    Cargo pair of `>=X` and `<Y` (the traversal feature's `>=0.25, <0.27`)."""
    if "," in spec:
        lo, hi = (0, 0, 0), INF
        for part in spec.split(","):
            m = re.fullmatch(r"\s*(>=|<)\s*v?(\d+(?:\.\d+){0,2})\s*", part)
            if not m:
                raise Unreadable(f"unsupported range {spec!r}")
            v = ver(m.group(2))
            lo, hi = (max(lo, v), hi) if m.group(1) == ">=" else (lo, min(hi, v))
        return lo, hi
    m = re.fullmatch(r"\s*(\^|~|>=|=)?\s*v?(\d+(?:\.\d+){0,2})\s*", spec)
    if not m:
        raise Unreadable(f"unsupported range {spec!r}")
    op, raw = m.group(1), ver(m.group(2), raw=True)
    if op == ">=":
        return pad(raw), INF
    if op == "~":
        return pad(raw), bump(raw, min(1, len(raw) - 1))
    return pad(raw), caret(raw)
```

Run: `python -m pytest tools/tests -q && python tools/check-runtime-ranges.py`
Expected: `26 passed`; the script lists `ok   rust       Cargo.toml [dependencies]: tree-sitter = ">=0.25, <0.27"  [0.25.0, 0.27.0)` and ends `8 range(s), 0 admit a runtime that cannot load ABI 15`.

- [ ] **Step 3: Write the module with its tests**

`bindings/rust/traversal.rs`:

```rust
//! Classified traversal over the all-branches AL tree (roadmap F0, spec 5.1 and 6).
//!
//! Behind the `traversal` cargo feature, off by default: it is the only part of
//! this crate that needs the `tree-sitter` runtime and `serde_json`.
//!
//! Every position is a canonical UTF-8 byte offset. Node classes come from the
//! hand-maintained policy (`traversal/policy.json`, bundled below), never from a
//! node-type name.

use std::collections::HashMap;
use std::fmt;

use serde_json::{json, Map, Value};
use tree_sitter::{Node, Tree};

/// The policy file shipped in this crate, identical to the one in every other package.
pub const POLICY_JSON: &str = include_str!("../../traversal/policy.json");
pub const SCHEMA: u64 = 1;
pub const CLASSES: [&str; 7] = [
    "ordinary", "branch-container", "assembler", "fragment", "token-alias", "directive", "trivia",
];
/// Only these get a `SplitInfo` on their visit. An ordinary node that holds
/// directives (an ERROR node, say) is walked normally.
pub const SPLIT_CLASSES: [&str; 3] = ["branch-container", "assembler", "fragment"];

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PolicyError(pub String);

impl fmt::Display for PolicyError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "traversal policy: {}", self.0)
    }
}

impl std::error::Error for PolicyError {}

/// An `ArmDescriptor` from another source revision was handed to `bind_arm`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WrongDocument(pub String);

impl fmt::Display for WrongDocument {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "wrong document: {}", self.0)
    }
}

impl std::error::Error for WrongDocument {}

#[derive(Debug, Clone)]
pub struct Policy {
    types: Map<String, Value>,
}

impl Policy {
    pub fn from_json(text: &str) -> Result<Policy, PolicyError> {
        let data: Value = serde_json::from_str(text).map_err(|e| PolicyError(e.to_string()))?;
        if data.get("schema").and_then(Value::as_u64) != Some(SCHEMA) {
            return Err(PolicyError(format!("schema {:?}, expected {SCHEMA}", data.get("schema"))));
        }
        let types = data
            .get("types")
            .and_then(Value::as_object)
            .ok_or_else(|| PolicyError("no `types` object".into()))?
            .clone();
        for (ty, entry) in &types {
            let class = entry.get("class").and_then(Value::as_str).unwrap_or("");
            if !CLASSES.contains(&class) {
                return Err(PolicyError(format!("{ty}: unknown class {class:?}")));
            }
        }
        Ok(Policy { types })
    }

    pub fn bundled() -> Policy {
        Policy::from_json(POLICY_JSON).expect("the bundled policy is valid")
    }

    pub fn class(&self, ty: &str) -> &str {
        self.types
            .get(ty)
            .and_then(|e| e.get("class"))
            .and_then(Value::as_str)
            .unwrap_or("ordinary")
    }

    pub fn role(&self, ty: &str) -> Option<&str> {
        self.types.get(ty).and_then(|e| e.get("role")).and_then(Value::as_str)
    }

    pub fn host_policy(&self, container: &str, parent: &str, field: Option<&str>) -> Option<&str> {
        let key = format!("{parent}:{}", field.unwrap_or("<children>"));
        self.types
            .get(container)
            .and_then(|e| e.get("hosts"))
            .and_then(|h| h.get(&key))
            .and_then(Value::as_str)
    }
}

pub fn fnv1a64(data: &[u8]) -> String {
    let mut h: u64 = 0xcbf2_9ce4_8422_2325;
    for b in data {
        h = (h ^ u64::from(*b)).wrapping_mul(0x0100_0000_01b3);
    }
    format!("{h:016x}")
}

#[derive(Debug, Clone)]
pub struct Directive<'t> {
    pub role: String,
    pub start: usize,
    pub end: usize,
    pub node: Node<'t>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ArmDescriptor {
    /// (revision, '#if' byte offset)
    pub group_id: (String, usize),
    pub arm_id: usize,
    /// '#' of the arm's opening directive, then of its closing one if any.
    pub directive_offsets: Vec<usize>,
    /// The arm body, before any masking.
    pub raw_range: (usize, usize),
}

#[derive(Debug, Clone)]
pub struct Group<'t> {
    pub if_offset: usize,
    pub directives: Vec<Directive<'t>>,
    pub arms: Vec<ArmDescriptor>,
}

#[derive(Debug, Clone)]
pub struct Fragment<'t> {
    pub field: Option<&'static str>,
    pub node: Node<'t>,
}

#[derive(Debug, Clone)]
pub struct ArmFragments<'t> {
    pub descriptor: ArmDescriptor,
    pub fragments: Vec<Fragment<'t>>,
}

#[derive(Debug, Clone)]
pub struct GroupArms<'t> {
    pub group_id: (String, usize),
    pub arms: Vec<ArmFragments<'t>>,
}

#[derive(Debug, Clone)]
pub struct SplitInfo<'t> {
    pub groups: Vec<GroupArms<'t>>,
    /// The node's own children outside every arm, directives excluded.
    pub shared: Vec<Fragment<'t>>,
}

#[derive(Debug, Clone)]
pub struct Visit<'t> {
    pub node: Node<'t>,
    pub class: String,
    pub kind: &'static str,
    pub field: Option<&'static str>,
    pub start: usize,
    pub end: usize,
    /// (if_offset, arm_id), outermost first.
    pub arms: Vec<(usize, usize)>,
    pub host: Option<String>,
    pub split: Option<SplitInfo<'t>>,
}

#[derive(Debug, Clone, Copy, Default)]
pub struct WalkOptions {
    pub include_directives: bool,
    pub include_trivia: bool,
}

/// A P1 tree paired with its source bytes and revision; owns the group index.
pub struct Document<'t> {
    pub tree: &'t Tree,
    pub source: &'t [u8],
    pub revision: String,
    pub groups: Vec<Group<'t>>,
    pub unpaired: Vec<Directive<'t>>,
    by_parent: HashMap<usize, Vec<usize>>, // parent node id -> indexes into groups
}

/// A node's children with their field names, through a cursor: the same calls
/// on tree-sitter 0.25 and 0.26.
fn kids<'t>(node: Node<'t>) -> Vec<(Option<&'static str>, Node<'t>)> {
    let mut out = Vec::new();
    let mut c = node.walk();
    if c.goto_first_child() {
        loop {
            out.push((c.field_name(), c.node()));
            if !c.goto_next_sibling() {
                break;
            }
        }
    }
    out
}

impl<'t> Document<'t> {
    pub fn new(tree: &'t Tree, source: &'t [u8], policy: &Policy) -> Document<'t> {
        let revision = fnv1a64(source);
        let mut open: Vec<Vec<Directive<'t>>> = Vec::new();
        let mut done: Vec<Vec<Directive<'t>>> = Vec::new();
        let mut unpaired = Vec::new();
        let mut parent_ifs: Vec<(usize, Vec<usize>)> = Vec::new();
        let mut stack = vec![tree.root_node()];
        while let Some(node) = stack.pop() {
            let role = if node.is_named() { policy.role(node.kind()) } else { None };
            let Some(role) = role else {
                for (_, k) in kids(node).into_iter().rev() {
                    stack.push(k);
                }
                continue;
            };
            let d = Directive { role: role.to_string(), start: node.start_byte(), end: node.end_byte(), node };
            if role == "if" {
                open.push(vec![d]);
            } else if open.is_empty() {
                unpaired.push(d);
                continue;
            } else {
                open.last_mut().unwrap().push(d);
            }
            let if_offset = open.last().unwrap()[0].start;
            let pid = node.parent().map(|p| p.id()).unwrap_or(usize::MAX);
            match parent_ifs.iter_mut().find(|(id, _)| *id == pid) {
                Some((_, offs)) if !offs.contains(&if_offset) => offs.push(if_offset),
                Some(_) => {}
                None => parent_ifs.push((pid, vec![if_offset])),
            }
            if role == "endif" {
                done.push(open.pop().unwrap());
            }
        }
        done.extend(open);
        done.sort_by_key(|ds| ds[0].start);
        let eof = source.len();
        let mut groups = Vec::new();
        for ds in done {
            let if_offset = ds[0].start;
            let mut arms = Vec::new();
            for (idx, d) in ds.iter().enumerate() {
                if d.role == "endif" {
                    continue;
                }
                let closer = ds.get(idx + 1);
                arms.push(ArmDescriptor {
                    group_id: (revision.clone(), if_offset),
                    arm_id: arms.len(),
                    directive_offsets: match closer {
                        Some(c) => vec![d.start, c.start],
                        None => vec![d.start],
                    },
                    raw_range: (d.end, closer.map_or(eof, |c| c.start)),
                });
            }
            groups.push(Group { if_offset, directives: ds, arms });
        }
        let index: HashMap<usize, usize> = groups.iter().enumerate().map(|(i, g)| (g.if_offset, i)).collect();
        let by_parent = parent_ifs
            .into_iter()
            .map(|(pid, offs)| (pid, offs.iter().map(|o| index[o]).collect()))
            .collect();
        Document { tree, source, revision, groups, unpaired, by_parent }
    }

    pub fn descriptors(&self) -> Vec<&ArmDescriptor> {
        self.groups.iter().flat_map(|g| g.arms.iter()).collect()
    }
}

pub fn groups_of<'d, 't>(node: Node<'t>, doc: &'d Document<'t>) -> Vec<&'d Group<'t>> {
    doc.by_parent
        .get(&node.id())
        .map(|ix| ix.iter().map(|&i| &doc.groups[i]).collect())
        .unwrap_or_default()
}

pub fn bind_arm<'t>(d: &ArmDescriptor, doc: &Document<'t>, policy: &Policy) -> Result<ArmFragments<'t>, WrongDocument> {
    if d.group_id.0 != doc.revision {
        return Err(WrongDocument(format!("descriptor revision {} != document {}", d.group_id.0, doc.revision)));
    }
    let (lo, hi) = d.raw_range;
    let mut out = Vec::new();
    // Start at the smallest node holding the whole arm, one level up if the arm IS
    // that node, so its field name is known (walking from the root is quadratic).
    let root = doc.tree.root_node();
    let mut top = root.descendant_for_byte_range(lo, hi).unwrap_or(root);
    while let Some(p) = top.parent() {
        if !(lo <= top.start_byte() && top.end_byte() <= hi) {
            break;
        }
        top = p;
    }
    let mut stack = vec![(top, None)];
    while let Some((node, field)) = stack.pop() {
        if node.end_byte() <= lo || node.start_byte() >= hi {
            continue;
        }
        if lo <= node.start_byte() && node.end_byte() <= hi {
            if !(node.is_named() && policy.class(node.kind()) == "directive") {
                out.push(Fragment { field, node });
            }
            continue;
        }
        for (f, k) in kids(node).into_iter().rev() {
            stack.push((k, f));
        }
    }
    Ok(ArmFragments { descriptor: d.clone(), fragments: out })
}

pub fn split_info<'t>(node: Node<'t>, doc: &Document<'t>, policy: &Policy) -> Option<SplitInfo<'t>> {
    let groups = groups_of(node, doc);
    if groups.is_empty() {
        return None;
    }
    let ranges: Vec<(usize, usize)> = groups.iter().flat_map(|g| g.arms.iter().map(|a| a.raw_range)).collect();
    let shared = kids(node)
        .into_iter()
        .filter(|(_, c)| !(c.is_named() && policy.class(c.kind()) == "directive"))
        .filter(|(_, c)| !ranges.iter().any(|&(lo, hi)| lo <= c.start_byte() && c.end_byte() <= hi))
        .map(|(field, node)| Fragment { field, node })
        .collect();
    let groups = groups
        .iter()
        .map(|g| GroupArms {
            group_id: (doc.revision.clone(), g.if_offset),
            arms: g.arms.iter().map(|a| bind_arm(a, doc, policy).expect("same document")).collect(),
        })
        .collect();
    Some(SplitInfo { groups, shared })
}

pub fn walk<'t>(doc: &Document<'t>, policy: &Policy, root: Option<Node<'t>>, opts: WalkOptions) -> Vec<Visit<'t>> {
    let mut arms = doc.descriptors();
    arms.sort_by_key(|a| (a.raw_range.0, std::cmp::Reverse(a.raw_range.1)));
    let mut active: Vec<&ArmDescriptor> = Vec::new();
    let mut k = 0;
    let mut out = Vec::new();
    let mut stack = vec![(root.unwrap_or_else(|| doc.tree.root_node()), None, None::<Node<'t>>)];
    while let Some((node, field, parent)) = stack.pop() {
        if !node.is_named() {
            continue;
        }
        let class = policy.class(node.kind());
        if (class == "directive" && !opts.include_directives) || (class == "trivia" && !opts.include_trivia) {
            continue;
        }
        let (start, end) = (node.start_byte(), node.end_byte());
        while k < arms.len() && arms[k].raw_range.0 <= start {
            active.push(arms[k]);
            k += 1;
        }
        active.retain(|a| a.raw_range.1 > start);
        let path = active.iter().filter(|a| a.raw_range.1 >= end).map(|a| (a.group_id.1, a.arm_id)).collect();
        let host = match (class, parent) {
            ("branch-container", Some(p)) => policy.host_policy(node.kind(), p.kind(), field).map(str::to_string),
            _ => None,
        };
        out.push(Visit {
            node,
            class: class.to_string(),
            kind: node.kind(),
            field,
            start,
            end,
            arms: path,
            host,
            split: if SPLIT_CLASSES.contains(&class) { split_info(node, doc, policy) } else { None },
        });
        for (f, c) in kids(node).into_iter().rev() {
            stack.push((c, f, Some(node)));
        }
    }
    out
}

fn frag_json(f: &Fragment) -> Value {
    json!([f.field, f.node.kind(), f.node.is_named(), f.node.start_byte(), f.node.end_byte()])
}

fn split_json(s: &SplitInfo) -> Value {
    json!({
        "groups": s.groups.iter().map(|g| json!({
            "if": g.group_id.1,
            "arms": g.arms.iter().map(|a| json!({
                "arm": a.descriptor.arm_id,
                "range": [a.descriptor.raw_range.0, a.descriptor.raw_range.1],
                "fragments": a.fragments.iter().map(frag_json).collect::<Vec<_>>(),
            })).collect::<Vec<_>>(),
        })).collect::<Vec<_>>(),
        "shared": s.shared.iter().map(frag_json).collect::<Vec<_>>(),
    })
}

/// The parity form: what every runtime must produce for the same fixture.
pub fn visits_to_json(visits: &[Visit]) -> Value {
    Value::Array(
        visits
            .iter()
            .map(|v| {
                json!({
                    "class": v.class, "type": v.kind, "field": v.field, "start": v.start, "end": v.end,
                    "arms": v.arms.iter().map(|&(i, a)| json!([i, a])).collect::<Vec<_>>(),
                    "host": v.host,
                    "split": v.split.as_ref().map(split_json),
                })
            })
            .collect(),
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::{Path, PathBuf};

    fn fixtures() -> Vec<PathBuf> {
        let dir = Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/traversal/fixtures");
        let mut out: Vec<PathBuf> = std::fs::read_dir(&dir)
            .expect("tests/traversal/fixtures")
            .map(|e| e.expect("dir entry").path())
            .filter(|p| p.extension().is_some_and(|x| x == "al"))
            .collect();
        out.sort();
        out
    }

    fn parser() -> tree_sitter::Parser {
        let mut parser = tree_sitter::Parser::new();
        parser.set_language(&crate::LANGUAGE.into()).expect("load AL");
        parser
    }

    #[test]
    fn every_fixture_matches_its_expected_visits() {
        let policy = Policy::bundled();
        let mut parser = parser();
        let paths = fixtures();
        assert_eq!(paths.len(), 12);
        for path in paths {
            let source = std::fs::read(&path).unwrap();
            let tree = parser.parse(&source, None).unwrap();
            let doc = Document::new(&tree, &source, &policy);
            let got = json!({
                "revision": doc.revision,
                "visits": visits_to_json(&walk(&doc, &policy, None, WalkOptions::default())),
            });
            let want: Value =
                serde_json::from_str(&std::fs::read_to_string(path.with_extension("visits.json")).unwrap()).unwrap();
            assert_eq!(got, want, "{}", path.display());
        }
    }

    #[test]
    fn fnv1a64_reference_vectors() {
        assert_eq!(fnv1a64(b""), "cbf29ce484222325");
        assert_eq!(fnv1a64(b"a"), "af63dc4c8601ec8c");
    }

    #[test]
    fn policy_rejects_an_unknown_schema_or_class() {
        assert!(Policy::from_json(r#"{"schema": 2, "types": {}}"#).is_err());
        assert!(Policy::from_json(r#"{"schema": 1, "types": {"x": {"class": "special"}}}"#).is_err());
        let p = Policy::bundled();
        assert_eq!(p.class("preproc_conditional_expression_tail"), "assembler");
        assert_eq!(p.class("identifier"), "ordinary");
    }

    #[test]
    fn bind_arm_rejects_a_descriptor_from_another_document() {
        let policy = Policy::bundled();
        let mut parser = parser();
        let dir = Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/traversal/fixtures");
        let (a_src, b_src) = (std::fs::read(dir.join("containers.al")).unwrap(),
                              std::fs::read(dir.join("elif_chain.al")).unwrap());
        let (a_tree, b_tree) = (parser.parse(&a_src, None).unwrap(), parser.parse(&b_src, None).unwrap());
        let a = Document::new(&a_tree, &a_src, &policy);
        let b = Document::new(&b_tree, &b_src, &policy);
        assert!(bind_arm(a.descriptors()[0], &b, &policy).is_err());
    }
}
```

- [ ] **Step 4: Run it on both runtime versions**

Run: `cargo test --features traversal`
Expected: `test result: ok. 5 passed` (four traversal tests and the existing `test_can_load_grammar`), then the doc test `ok. 1 passed`. `Cargo.lock` resolves `tree-sitter 0.25.10`.

Run: `cargo update -p tree-sitter --precise 0.26.13 && cargo test --features traversal && cargo update -p tree-sitter --precise 0.25.10`
Expected: the same two `ok` lines on 0.26.13; the lock is back on 0.25.10.

Run: `cargo clippy --features traversal --all-targets && cargo test`
Expected: clippy prints no warning; the default-feature `cargo test` reports `ok. 1 passed` (only `test_can_load_grammar`: the traversal module is not compiled without the feature).

- [ ] **Step 5: The static check now covers the Rust source**

Run: `./tools/ts-lock.sh python -m pytest tests/traversal -q`
Expected: `241 passed`.

- [ ] **Step 6: Commit**

```bash
git add Cargo.toml Cargo.lock bindings/rust/lib.rs bindings/rust/traversal.rs tools/check-runtime-ranges.py tools/tests/test_check_runtime_ranges.py
git commit -m "feat(traversal): Rust walker behind the traversal feature (roadmap F0, D6)

tree_sitter_al::traversal, off by default; the feature adds tree-sitter
>=0.25, <0.27 and serde_json. Matches the shared expected visits on
tree-sitter 0.25.10 and 0.26.13. check-runtime-ranges reads the compound
Cargo range."
```

---

### Task 8: Consumer canaries (D7)

**Files:**
- Create: `tests/traversal/test_canaries.py`, `tests/traversal/js/canaries.test.js`

**Interfaces:**
- Consumes: Python `walk`, `Document.groups`, `SplitInfo` (Tasks 2–3); JS `walk`, `loadPolicy`, `Document` (Task 6); fixtures `containers.al`, `assemblers.al`, `split_declaration.al`, `elif_chain.al`.
- Produces: nothing other tasks call. Each canary reproduces the consumer's own rule, cited by file:line and commit, shows the failure on the naive walk (`before`), and answers the same question on F0 (`after`). F0 enables the fixes; it does not edit the consumers' repositories.

| Canary | Consumer rule (consumers.md evidence) | Before | After |
|---|---|---|---|
| DevOpsWorker | `scripts/al-symbol/resolver.ts:86-97` (aceea15), matches `type === 'procedure'` only | `Split` missing | `Split` found through `SplitInfo` |
| al-differ | `src/engine/walker.ts:10-61, 63-136, 185-195, 288, 423` (5590605) | nothing inside `#if` | every arm's object and procedure, and `TestMethod` through `preproc_split_declaration` |
| code-graph-rag | `parsers/al/object_extractor.py:21, 119-121`, `procedure_extractor.py:15-22, 115-118`, `utils.py:77-78` (81398cae) | no object in `containers.al` or `split_declaration.al`, no `Split` | all of them, owned by the right object |
| graphify | `graphify/extract.py:3097-3127` (6647b56) | member-level `#if` untagged; `#else` after `#elif` tagged `!CLEAN23` | every kind tagged; any path through an `#elif`/`#else` arm reported `unsupported` |
| LethAL R214 part 1 | `packages/engine/src/ast/tree-walks.ts:33-37, 47-62, 81-86` (19b70fc5) | every call and assignment directly under `#if` lost | all five found with arm identity; the two under a split construct found through `SplitInfo` |

- [ ] **Step 1: Write the Python canaries**

`tests/traversal/test_canaries.py`:

```python
"""Consumer canaries in Python (spec 6.2 item 3). Each reproduces the consumer's own
rule, cited by file:line (.superpowers/sdd/a7/consumers.md), shows the failure on the
naive walk, and answers the same question on F0. The JS canaries (DevOpsWorker,
al-differ, LethAL R214 part 1) are in tests/traversal/js/canaries.test.js."""


def _text(doc, node):
    return doc.source[node.start_byte:node.end_byte].decode("utf-8")


def _split_names(split, keyword, name_field, doc):
    """A split construct that is a `keyword` construct in every arm, read from SplitInfo."""
    names = []
    for g in split.groups:
        for arm in g.arms:
            name = next((f for f in arm.fragments if f.field == name_field), None)
            if name is None or not any(f.type == keyword for f in arm.fragments):
                return None
            names.append(_text(doc, name.node))
    return names or None


# --- code-graph-rag (81398cae) ------------------------------------------------
# codebase_rag/parsers/al/object_extractor.py:21-.. OBJECT_TYPE_TO_LABELS keys (the
# subset this fixture set reaches); procedure_extractor.py:15-22 PROCEDURE_NODE_TYPES.
OBJECT_TYPES = {"codeunit_declaration", "table_declaration", "page_declaration", "enum_declaration"}
PROCEDURE_NODE_TYPES = {"procedure", "trigger_declaration", "event_declaration", "interface_procedure"}


def cgr_before(doc):
    """object_extractor.py:119-121 (root_node.children only), procedure_extractor.py:115-118
    (object_body(node).children only; utils.py:77-78 object_body = field `body` or node)."""
    out = []
    for obj in doc.tree.root_node.children:
        if obj.type not in OBJECT_TYPES:
            continue
        body = obj.child_by_field_name("body") or obj
        out += [(_text(doc, obj.child_by_field_name("object_name")), _text(doc, p.child_by_field_name("name")))
                for p in body.children if p.type in PROCEDURE_NODE_TYPES]
    return out


def cgr_after(doc, policy, T):
    """Every definition in every arm, owned by the innermost object around it, where a
    split declaration names its object from its arms' `object_name` fragments."""
    visits = T.walk(doc, policy)
    owners = []
    for v in visits:
        if v.type in OBJECT_TYPES:
            owners.append((v.start, v.end, _text(doc, v.node.child_by_field_name("object_name"))))
        elif v.cls == "assembler" and v.split:
            names = _split_names(v.split, "codeunit_keyword", "object_name", doc)
            if names:
                owners.append((v.start, v.end, "|".join(sorted(set(names)))))
    out = []
    for v in visits:
        names = None
        if v.type in PROCEDURE_NODE_TYPES:
            names = [_text(doc, v.node.child_by_field_name("name"))]
        elif v.cls == "assembler" and v.split:
            names = sorted(set(_split_names(v.split, "procedure_keyword", "name", doc) or [])) or None
        if names:
            owner = max((o for o in owners if o[0] <= v.start and v.end <= o[1]), key=lambda o: o[0])
            out += [(owner[2], n) for n in names]
    return out


def test_code_graph_rag_definitions_in_every_arm(T, policy, parse):
    doc = parse("containers.al")
    assert cgr_before(doc) == []
    assert cgr_after(doc, policy, T) == [('"Containers Ø"', "A"), ('"Containers Ø"', "B"),
                                         ('"Containers Ø"', "C"), ('"Containers Ø"', "Stmts")]


def test_code_graph_rag_split_procedure_and_split_declaration(T, policy, parse):
    doc = parse("assemblers.al")
    assert ("\"Assemblers\"", "Split") not in cgr_before(doc)
    assert ("\"Assemblers\"", "Split") in cgr_after(doc, policy, T)
    doc = parse("split_declaration.al")
    assert cgr_before(doc) == []
    assert cgr_after(doc, policy, T) == [('"Test Impl"', "TestMethod")]


# --- graphify (6647b56) --------------------------------------------------------
def graphify_before_ranges(doc):
    """graphify/extract.py:3097-3127, verbatim: only preproc_conditional_statement, and
    `#else` negates only the LAST condition. Returns (start_line, end_line, label)."""
    ranges = []

    def collect(node):
        if node.type == "preproc_conditional_statement":
            label = start = None
            for child in node.children:
                if child.type == "preproc_if":
                    cond = child.child_by_field_name("condition")
                    label, start = (_text(doc, cond).strip() if cond else "?"), child.end_point[0] + 1
                elif child.type == "preproc_elif":
                    if label is not None and start is not None:
                        ranges.append((start, child.start_point[0], label))
                    cond = child.child_by_field_name("condition")
                    label, start = (_text(doc, cond).strip() if cond else "?"), child.end_point[0] + 1
                elif child.type == "preproc_else":
                    if label is not None and start is not None:
                        ranges.append((start, child.start_point[0], label))
                    label, start = "!" + (label or "?"), child.end_point[0] + 1
                elif child.type == "preproc_endif":
                    if label is not None and start is not None:
                        ranges.append((start, child.start_point[0], label))
                    label = start = None
        for c in node.children:
            collect(c)

    collect(doc.tree.root_node)
    return ranges


def graphify_before_tag(ranges, node):
    """Innermost range holding the node's first line (graphify tags by source line)."""
    line = node.start_point[0]
    hits = [r for r in ranges if r[0] <= line <= r[1]]
    return min(hits, key=lambda r: r[1] - r[0])[2] if hits else None


def graphify_after_tag(doc, visit):
    """F0 gives every arm of every kind. Without the symbolic API (spec 3.5) only a
    path of arm-0 arms has an exact condition: the conjunction of their #if
    conditions. An #elif/#else arm's real condition negates every earlier arm, so
    any path through one is reported `unsupported`, never guessed."""
    if not visit.arms:
        return None
    if any(arm_id for _, arm_id in visit.arms):
        return "unsupported"
    conds = []
    for if_offset, _ in visit.arms:
        group = next(g for g in doc.groups if g.if_offset == if_offset)
        conds.append(_text(doc, group.directives[0].node.child_by_field_name("condition")))
    return " and ".join(conds)


def test_graphify_elif_else_condition(T, policy, parse):
    doc = parse("elif_chain.al")
    visits = {(_text(doc, v.node) if v.type == "assignment_statement" else
               _text(doc, v.node.child_by_field_name("name"))): v
              for v in T.walk(doc, policy) if v.type in ("assignment_statement", "procedure")}
    ranges = graphify_before_ranges(doc)
    before = {k: graphify_before_tag(ranges, v.node) for k, v in visits.items()}
    assert before["A"] is None             # member-level #if: only preproc_conditional_statement is read
    assert before["X := 2"] == "!CLEAN23"  # wrong: the #else arm is (not CLEAN24) and (not CLEAN23)
    # Version drift, not the #elif rule: preproc_if ends AFTER its newline since
    # DIRECTIVE_EOL, so `end_point[0] + 1` starts every #if/#elif range one line late.
    assert before["X := 1"] is None
    after = {k: graphify_after_tag(doc, v) for k, v in visits.items()}
    assert after == {"A": "CLEAN24", "B": "unsupported", "C": "unsupported", "Stmts": None,
                     "X := 1": "CLEAN24", "X := 3": "CLEAN24 and CLEAN26",
                     "X := 4": "unsupported", "X := 2": "unsupported"}
```

- [ ] **Step 2: Write the JS canaries**

`tests/traversal/js/canaries.test.js`:

```js
'use strict';
// Consumer canaries (spec 6.2 item 3, roadmap F0). Each one reproduces a consumer's
// ACTUAL rule, cited by file:line (.superpowers/sdd/a7/consumers.md), shows the
// failure on the naive walk (`before`), and the same question answered on F0 (`after`).
// F0 enables the fixes; it does not perform them in the consumers' repos.
const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const REPO = path.resolve(__dirname, '..', '..', '..');
const FIX = path.join(REPO, 'tests', 'traversal', 'fixtures');
const T = require(path.join(REPO, 'traversal'));
const { Parser, Language } = require('module').createRequire(path.join(REPO, 'package.json'))('web-tree-sitter');

let parser;
const policy = T.loadPolicy();

test.before(async () => {
  await Parser.init();
  parser = new Parser();
  parser.setLanguage(await Language.load(path.join(REPO, 'tree-sitter-al.wasm')));
});

function load(name) {
  const text = fs.readFileSync(path.join(FIX, name), 'utf8');
  const tree = parser.parse(text);
  return { text, tree, doc: new T.Document(tree, text, policy) };
}

const textOf = (doc, n) => doc.text.slice(n.startIndex, n.endIndex);

// A split construct that is a procedure in every arm: each arm carries a
// procedure_keyword fragment and a `name` fragment. Consumer-side recognition
// over SplitInfo, not an F0 API: F0 hands over the arms, the consumer decides.
function splitNames(split, keyword, nameField, doc) {
  const names = [];
  for (const g of split.groups) {
    for (const a of g.arms) {
      const kw = a.fragments.some((f) => f.node.type === keyword);
      const name = a.fragments.find((f) => f.field === nameField);
      if (!kw || !name) return null;
      names.push(textOf(doc, name.node));
    }
  }
  return names.length ? names : null;
}

// ---------------------------------------------------------------------------
// DevOpsWorker: scripts/al-symbol/resolver.ts:86-97 (aceea15), verbatim.
function procedureNodes(root) {
  const result = [];
  function recurse(n) {
    if (n.type === 'procedure') { result.push(n); return; }
    for (let i = 0; i < n.namedChildCount; i++) recurse(n.namedChild(i));
  }
  recurse(root);
  return result;
}

test('DevOpsWorker: a split procedure is invisible to findDefinition before F0', () => {
  const { tree, doc } = load('assemblers.al');
  const before = procedureNodes(tree.rootNode).map((n) => textOf(doc, n.childForFieldName('name')));
  assert.deepStrictEqual(before, ['First', 'Tail', 'CaseEnd']);

  const after = [];
  for (const v of T.walk(doc, policy)) {
    if (v.type === 'procedure') after.push(textOf(doc, v.node.childForFieldName('name')));
    else if (v.cls === 'assembler' && v.split) {
      const names = splitNames(v.split, 'procedure_keyword', 'name', doc);
      if (names) after.push(...new Set(names));
    }
  }
  assert.deepStrictEqual(after, ['First', 'Split', 'Tail', 'CaseEnd']);
});

// ---------------------------------------------------------------------------
// al-differ: src/engine/walker.ts (5590605). MATCHABLE_TYPES :10-61 and
// CONTAINER_TYPES :63-136 are the subsets this fixture can reach; collectMatchable
// :185-195 is verbatim; callers :288 and :423 recurse into each matched node.
const MATCHABLE_TYPES = new Set(['codeunit_declaration', 'procedure', 'trigger_declaration', 'property',
  'variable_declaration', 'field_declaration']);
const CONTAINER_TYPES = new Set(['fields_section', 'var_section', 'declaration_body', 'fields_body', 'var_body']);

function collectMatchable(parent) {
  const results = [];
  for (const child of parent.namedChildren) {
    if (MATCHABLE_TYPES.has(child.type)) results.push(child);
    else if (CONTAINER_TYPES.has(child.type)) results.push(...collectMatchable(child));
  }
  return results;
}

function allMatchable(root) {
  const out = [];
  for (const m of collectMatchable(root)) out.push(m, ...allMatchable(m));
  return out;
}

const nameOf = (doc, n) => {
  const f = n.childForFieldName('name') || n.childForFieldName('object_name');
  return f ? textOf(doc, f) : null;
};

test('al-differ: definitions in every conditional arm, and through split declarations', () => {
  const c = load('containers.al');
  assert.deepStrictEqual(allMatchable(c.tree.rootNode), [], 'before: #if content is absent from the diff');

  const after = T.walk(c.doc, policy).filter((v) => MATCHABLE_TYPES.has(v.type) && v.type !== 'variable_declaration')
    .map((v) => [v.type, nameOf(c.doc, v.node), v.arms.map(([g, a]) => `${g}/${a}`).join(' ')]);
  assert.deepStrictEqual(after, [
    ['codeunit_declaration', '"Containers Æ"', '93/0'],
    ['codeunit_declaration', '"Containers Ø"', '93/1'],
    ['procedure', 'A', '93/1 179/0'],
    ['procedure', 'B', '93/1 179/1'],
    ['procedure', 'C', '93/1 179/2'],
    ['procedure', 'Stmts', '93/1'],
  ]);

  const s = load('split_declaration.al');
  assert.deepStrictEqual(allMatchable(s.tree.rootNode), [], 'before: a split declaration hides its object');
  const decl = T.walk(s.doc, policy).find((v) => v.type === 'preproc_split_declaration');
  assert.deepStrictEqual(splitNames(decl.split, 'codeunit_keyword', 'object_name', s.doc), ['"Test Impl"', '"Test Impl"']);
  const body = decl.split.shared.find((f) => f.field === 'body').node;
  assert.deepStrictEqual(T.walk(s.doc, policy, { root: body }).filter((v) => v.type === 'procedure')
    .map((v) => nameOf(s.doc, v.node)), ['TestMethod']);
});

// ---------------------------------------------------------------------------
// LethAL R214 part 1: packages/engine/src/ast/tree-walks.ts (19b70fc5).
// isStatementPosition :33-37, SINGLE_STATEMENT_SLOTS :47-62, isStatementSlot :81-86.
const SINGLE_STATEMENT_SLOTS = new Set(['if_statement.then_branch', 'if_statement.else_branch', 'case_branch.body',
  'while_statement.body', 'for_statement.body', 'foreach_statement.body',
  'preproc_split_if_statement.then_branch', 'preproc_split_if_statement.else_branch',
  'preproc_split_if_else_statement.then_branch', 'preproc_split_if_else_statement.else_branch',
  'preproc_split_case_extended.body']);

function fieldOf(node) {
  const p = node.parent;
  if (!p) return null;
  for (let i = 0; i < p.childCount; i++) if (p.child(i).id === node.id) return p.fieldNameForChild(i) || null;
  return null;
}

function isStatementSlot(node, field) {
  const parent = node.parent;
  if (parent === null) return false;
  if (parent.type === 'statement_block' || parent.type === 'block') return true;
  if (field === null) return false;
  return SINGLE_STATEMENT_SLOTS.has(`${parent.type}.${field}`);
}

// The rewrite on F0: a branch container splices its arm into its OWN host slot,
// so the slot question is asked of the container, climbing nested containers.
function isStatementSlotF0(visit) {
  let node = visit.node;
  let field = visit.field;
  while (node.parent && policy.cls(node.parent.type) === 'branch-container') {
    node = node.parent;
    field = fieldOf(node);
  }
  return isStatementSlot(node, field);
}

const SITE_TYPES = new Set(['call_expression', 'assignment_statement']);

test('LethAL R214 part 1: statements under conditional parents pass site selection', () => {
  const { tree, doc } = load('containers.al');
  const stmts = T.walk(doc, policy).find((v) => v.type === 'procedure' && nameOf(doc, v.node) === 'Stmts');
  const visits = T.walk(doc, policy, { root: stmts.node }).filter((v) => SITE_TYPES.has(v.type));

  const before = visits.filter((v) => isStatementSlot(v.node, fieldOf(v.node))).map((v) => textOf(doc, v.node));
  assert.deepStrictEqual(before, ["Message('control')"], 'before: every site inside #if is lost');

  const after = visits.filter(isStatementSlotF0).map((v) => [textOf(doc, v.node), v.arms.map(([g, a]) => `${g}/${a}`).join(' ')]);
  assert.deepStrictEqual(after, [
    ["Message('control')", '93/1'],
    ['DoThing(X)', '93/1 441/0'],
    ['X := 1', '93/1 441/0'],
    ['X := 3', '93/1 441/0 489/0'],
    ['X := 4', '93/1 441/1'],
    ['X := 2', '93/1 441/2'],
  ]);
  assert.ok(tree.rootNode, 'tree kept alive for the visits above');
});

// Statements an assembler holds directly -- an arm piece or a shared part -- are
// statements when the assembler itself fills a statement slot. SplitInfo says which
// pieces those are; the parent-type check never could.
function assemblerStatementSites(v) {
  if (v.cls !== 'assembler' || !v.split || !isStatementSlotF0(v)) return [];
  const pieces = [...v.split.groups.flatMap((g) => g.arms.flatMap((a) => a.fragments)), ...v.split.shared];
  return pieces.filter((f) => f.field === null && SITE_TYPES.has(f.node.type)).map((f) => f.node);
}

test('LethAL R214 part 1: statements held by a split construct are found through SplitInfo', () => {
  const { doc } = load('assemblers.al');
  const visits = T.walk(doc, policy);
  const held = visits.filter((v) => SITE_TYPES.has(v.type) && policy.cls(v.node.parent.type) === 'assembler');
  assert.deepStrictEqual(held.map((v) => textOf(doc, v.node)), ["Message('a')", "Message('b')"]);
  assert.deepStrictEqual(held.filter((v) => isStatementSlot(v.node, v.field)), [], 'before: both are lost');
  const after = visits.flatMap(assemblerStatementSites).map((n) => textOf(doc, n));
  assert.deepStrictEqual(after, ["Message('a')", "Message('b')"]);
});
```

- [ ] **Step 3: Run them**

Run: `./tools/ts-lock.sh python -m pytest tests/traversal/test_canaries.py -q`
Expected: `3 passed`.

Run: `node --test tests/traversal/js/parity.test.js tests/traversal/js/canaries.test.js`
Expected: `ℹ tests 34`, `ℹ pass 34`.

- [ ] **Step 4: Prove each `before` fails for the stated reason**

Temporarily change `policy.cls(node.parent.type) === 'branch-container'` in `isStatementSlotF0` to `=== 'nothing'` and rerun the JS canaries: the first LethAL test must fail with an `after` that equals the `before` (only `Message('control')`). Revert. Temporarily make Python `_split_names` return `None` and rerun the Python canaries: `test_code_graph_rag_split_procedure_and_split_declaration` must fail (no `Split`, no owner for `TestMethod`), while `test_code_graph_rag_definitions_in_every_arm` still passes, since it needs no `SplitInfo`. Revert.

- [ ] **Step 5: Commit**

```bash
git add tests/traversal/test_canaries.py tests/traversal/js/canaries.test.js
git commit -m "test(traversal): consumer canaries, before and after F0 (roadmap F0, D7)

DevOpsWorker, al-differ, code-graph-rag, graphify and LethAL R214 part 1,
each reproducing the consumer's own rule from consumers.md. graphify's
#elif/#else conditions are reported unsupported until the symbolic API."
```

---

### Task 9: Packaging and CI

**Files:**
- Create: `MANIFEST.in`
- Modify: `setup.py` (`Build.run`, `package_data`, import line), `package.json` (`files`), `.github/workflows/ci.yml` (paths, three jobs)

**Interfaces:**
- Consumes: everything above.
- Produces: the policy inside each artifact — npm `traversal/policy.json` beside `traversal/index.js`; PyPI `tree_sitter_al/traversal_policy.json` (what `load_policy()` reads by default); crates.io `traversal/policy.json` (`include_str!`, Task 7).

- [ ] **Step 1: Ship the policy in the Python package**

In `setup.py`, change the first import line to `from os.path import isdir, isfile, join`, and in `Build.run` add after the `queries` block (before `super().run()`):

```python
        # The traversal policy (roadmap F0): one data file shared by every binding.
        if isfile(join("traversal", "policy.json")):
            self.mkpath(join(self.build_lib, "tree_sitter_al"))
            self.copy_file(join("traversal", "policy.json"),
                           join(self.build_lib, "tree_sitter_al", "traversal_policy.json"))
```

and change `"tree_sitter_al": ["*.pyi", "py.typed"],` to `"tree_sitter_al": ["*.pyi", "py.typed", "traversal_policy.json"],`.

Create `MANIFEST.in`:

```text
# The traversal policy lives at the repo root, outside the package; setup.py's Build
# copies it into tree_sitter_al/. Without this line an sdist install has no policy.
include traversal/policy.json
# Found while adding the line above: the sdist carried neither of these, so it could not
# compile (parser.c and scanner.c include headers from src/) and shipped no queries.
include src/*.h src/tree_sitter/*.h
recursive-include queries *.scm
```

The last two lines fix a defect found while testing this one: the published sdist carried no `src/*.h`, `src/tree_sitter/*.h` or `queries/*.scm`, so `pip install` from it failed at `src/parser.c(3): fatal error C1083: Cannot open include file: 'tree_sitter/parser.h'` (measured; wheels are built from the tree and were unaffected).

- [ ] **Step 2: Ship the JS module and policy in the npm package**

In `package.json` `files`, after `"src/**",` add:

```json
    "traversal/*.js",
    "traversal/*.d.ts",
    "traversal/*.json",
```

Run: `npm pack --dry-run 2>&1 | grep traversal`
Expected: `traversal/index.d.ts`, `traversal/index.js`, `traversal/policy.json`.

- [ ] **Step 3: Clean-install checks, locally**

Python, from an sdist, outside the checkout (`python -m build` must not run from the repo root once `npm`/`node-gyp` has created `build/`, which shadows the `build` module):

```bash
T=$(mktemp -d) && python -m venv "$T/venv" && "$T/venv/Scripts/python" -m pip install -q build "tree-sitter~=0.25"
(cd "$T" && "$T/venv/Scripts/python" -m build --sdist --outdir "$T/dist" "$OLDPWD")
"$T/venv/Scripts/python" -m pip install -q "$T"/dist/*.tar.gz
(cd "$T" && "$T/venv/Scripts/python" - <<'EOF'
from tree_sitter import Language, Parser
import tree_sitter_al
from tree_sitter_al import traversal
policy = traversal.load_policy()
src = b"codeunit 1 C\n{\n#if A\n    procedure P()\n    begin\n    end;\n#endif\n}\n"
tree = Parser(Language(tree_sitter_al.language())).parse(src)
doc = traversal.Document(tree, src, policy)
v = next(x for x in traversal.walk(doc, policy) if x.type == "preproc_conditional")
assert (v.cls, v.host) == ("branch-container", "splice-repeat"), v
assert tree_sitter_al.HIGHLIGHTS_QUERY, "the sdist shipped no queries"
print("python sdist clean install: ok")
EOF
)
```

(`venv/bin/python` on Linux.) Expected: `python sdist clean install: ok`.

npm, from the packed tarball, with install scripts off (proves the module never needs the native addon):

```bash
T=$(mktemp -d) && npm pack --pack-destination "$T"
(cd "$T" && npm init -y >/dev/null && npm install --ignore-scripts "$T"/sshadows-tree-sitter-al-*.tgz web-tree-sitter@0.27.0)
cat > "$T/check.js" <<'EOF'
const T = require('@sshadows/tree-sitter-al/traversal');
const { Parser, Language } = require('web-tree-sitter');
(async () => {
  await Parser.init();
  const p = new Parser();
  p.setLanguage(await Language.load(require.resolve('@sshadows/tree-sitter-al/tree-sitter-al.wasm')));
  const text = 'codeunit 1 C\n{\n#if A\n    procedure P()\n    begin\n    end;\n#endif\n}\n';
  const policy = T.loadPolicy();
  const doc = new T.Document(p.parse(text), text, policy);
  const v = T.walk(doc, policy).find((x) => x.type === 'preproc_conditional');
  if (!v || v.cls !== 'branch-container' || v.host !== 'splice-repeat') throw new Error('traversal from the packed tarball is broken');
  console.log('npm clean install: ok');
})().catch((e) => { console.error(e); process.exit(1); });
EOF
(cd "$T" && node check.js)
```

Expected: `npm clean install: ok`.

Rust:

Run: `cargo package --allow-dirty --list | grep -E -x 'traversal[/\]policy.json' && cargo package --allow-dirty --features traversal`
Expected: `traversal/policy.json` (`traversal\policy.json` on Windows), then `Packaged 23 files`, `Verifying tree-sitter-al v4.4.1`, `Finished`.

- [ ] **Step 4: CI**

In `.github/workflows/ci.yml`, add to BOTH the `push.paths` and `pull_request.paths` lists:

```yaml
      - traversal/**
      - tests/**
      - package.json
      - Cargo.toml
      - setup.py
      - MANIFEST.in
```

and add these jobs after `config-oracle`:

```yaml
  traversal:
    # Roadmap F0: the classified traversal helper. One policy (traversal/policy.json),
    # one set of fixtures (tests/traversal/fixtures) whose expected visits the Python
    # walker writes; Rust (here) and Node (traversal-node) must match them.
    name: Traversal helper (Python, Rust)
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Set up tree-sitter
        uses: tree-sitter/setup-action/cli@v2

      - name: Install dependencies
        run: pip install -r tools/query_coverage/requirements.txt

      - name: Policy census (validate-grammar.sh Step 5f)
        run: python tools/traversal_census.py

      - name: Walker, SplitInfo, witnesses, canaries, expected visits
        run: python -m pytest tests/traversal -q

      # The feature declares tree-sitter >=0.25, <0.27: test both ends.
      - name: Rust on tree-sitter 0.25
        run: cargo update -p tree-sitter --precise 0.25.10 && cargo test --features traversal

      - name: Rust on tree-sitter 0.26
        run: cargo update -p tree-sitter --precise 0.26.13 && cargo test --features traversal

  traversal-node:
    name: Traversal helper (Node ${{ matrix.node }}, native and WASM)
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        node: [18, 24]
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6

      - name: Set up Node
        uses: actions/setup-node@v6
        with:
          node-version: ${{ matrix.node }}

      # The install script builds the native binding from src/ (there are no prebuilds
      # in the repo), so the native leg tests the committed grammar, never a stale build.
      - name: Install
        run: npm ci

      - name: Parity and canaries under both JS runtimes
        run: node --test tests/traversal/js/parity.test.js tests/traversal/js/canaries.test.js

  traversal-packages:
    # Each published artifact, installed clean outside the checkout, must carry the
    # policy and walk a tree. npm installs with --ignore-scripts: the traversal module
    # must work without the native addon.
    name: Traversal helper in the packaged artifacts
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Set up Node
        uses: actions/setup-node@v6
        with:
          node-version: '24'

      - name: Python sdist, installed into a clean venv
        run: |
          python -m pip install build
          python -m build --sdist --outdir "$RUNNER_TEMP/dist"
          python -m venv "$RUNNER_TEMP/venv"
          "$RUNNER_TEMP/venv/bin/pip" install "$RUNNER_TEMP"/dist/*.tar.gz "tree-sitter~=0.25"
          cd "$RUNNER_TEMP"
          cat > check.py <<'EOF'
          from tree_sitter import Language, Parser
          import tree_sitter_al
          from tree_sitter_al import traversal
          policy = traversal.load_policy()
          src = b"codeunit 1 C\n{\n#if A\n    procedure P()\n    begin\n    end;\n#endif\n}\n"
          tree = Parser(Language(tree_sitter_al.language())).parse(src)
          doc = traversal.Document(tree, src, policy)
          v = next(x for x in traversal.walk(doc, policy) if x.type == "preproc_conditional")
          assert (v.cls, v.host) == ("branch-container", "splice-repeat"), v
          assert tree_sitter_al.HIGHLIGHTS_QUERY, "the sdist shipped no queries"
          print("python sdist clean install: ok")
          EOF
          "$RUNNER_TEMP/venv/bin/python" check.py

      - name: npm tarball, installed with scripts off
        run: |
          npm pack --pack-destination "$RUNNER_TEMP"
          mkdir "$RUNNER_TEMP/npm-clean" && cd "$RUNNER_TEMP/npm-clean"
          npm init -y >/dev/null
          npm install --ignore-scripts "$RUNNER_TEMP"/sshadows-tree-sitter-al-*.tgz web-tree-sitter@0.27.0
          cat > check.js <<'EOF'
          const T = require('@sshadows/tree-sitter-al/traversal');
          const { Parser, Language } = require('web-tree-sitter');
          (async () => {
            await Parser.init();
            const p = new Parser();
            p.setLanguage(await Language.load(require.resolve('@sshadows/tree-sitter-al/tree-sitter-al.wasm')));
            const text = 'codeunit 1 C\n{\n#if A\n    procedure P()\n    begin\n    end;\n#endif\n}\n';
            const policy = T.loadPolicy();
            const doc = new T.Document(p.parse(text), text, policy);
            const v = T.walk(doc, policy).find((x) => x.type === 'preproc_conditional');
            if (!v || v.cls !== 'branch-container' || v.host !== 'splice-repeat') throw new Error('traversal from the packed tarball is broken');
            console.log('npm clean install: ok');
          })().catch((e) => { console.error(e); process.exit(1); });
          EOF
          node check.js

      - name: Crate carries the policy and builds with the feature
        run: |
          cargo package --allow-dirty --list | grep -qx 'traversal/policy.json'
          cargo package --allow-dirty --features traversal
```

Run: `python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml'))" && bash tools/check-exec-bits.sh`
Expected: no output from the YAML load; the exec-bit check passes (no new `.sh`).

- [ ] **Step 5: Commit**

```bash
git add MANIFEST.in setup.py package.json .github/workflows/ci.yml
git commit -m "build(traversal): ship the policy in every package, CI jobs (roadmap F0)

PyPI carries tree_sitter_al/traversal_policy.json, npm traversal/, crates.io
traversal/policy.json. CI runs the census, the Python suite, Rust on
tree-sitter 0.25 and 0.26, Node 18 and 24 on both JS runtimes, and clean
installs of all three artifacts. MANIFEST.in also fixes the sdist, which
lacked src/*.h and queries/ and could not build."
```

---

### Task 10: Documentation, CHANGELOG, final validation

**Files:**
- Create: `docs/traversal.md`
- Modify: `CHANGELOG.md` (`## [Unreleased]`), `CLAUDE.md` (Quick Reference)

**Interfaces:**
- Consumes: the finished helper.
- Produces: the migration page D9/D10 require.

- [ ] **Step 1: The docs page**

`docs/traversal.md`:

````markdown
# Walking `#if` code: the classified traversal helper

tree-sitter-al parses **every** branch of every `#if` into one tree. That is what
editors, diff tools and analysers need, but it means the tree holds nodes that are
not ordinary code: conditional containers, constructs assembled from pieces in
different branches, fragments of those constructs, and the directive lines
themselves. A walker that does not know which is which either drops `#if` content or
misreads it.

The traversal helper (roadmap F0) gives every runtime the same answer: one policy
file that classifies every special node type, and one `walk` that reports each node
with its class, its field, its byte span, the `#if` arms it sits in and, for split
constructs, a `SplitInfo` that lists every arm's pieces.

It does **not** pick a configuration. Every arm is reported; which one a given set
of preprocessor symbols selects is the job of the configured API (roadmap F1).

## Recursion alone does not fix node-kind recognition

Descending into every child finds the procedures inside a `preproc_conditional`.
It does not make a `preproc_split_procedure` look like a procedure: that node has
no `procedure` type, its header is spread over two arms, and its body is shared
after `#endif`. A consumer that matches `type === 'procedure'` misses it however
deep it recurses. **Use `SplitInfo`**: it hands you each arm's header pieces with
their field names, and the shared body, so you can recognise the construct and
read every variant of it.

## The classes

| Class | What it is | What `walk` does |
|---|---|---|
| ordinary | not a configuration node | descends normally |
| branch-container | a `#if` whose arms are alternatives in one host slot | visits it with its host policy and a `SplitInfo`, then every arm |
| assembler | one construct built from arm pieces plus shared parts, possibly crossing `#endif` | visits it with a `SplitInfo`; never presents its children as a flat list |
| fragment | a piece that only makes sense inside an assembler | visits it with class `fragment`; its assembler's `SplitInfo` lists it |
| token-alias | a keyword emitted by a split token (`preproc_split_begin` is a `begin`) | visits it like any token |
| directive | `#if` / `#elif` / `#else` / `#endif` and their parts | skipped unless `include_directives` |
| trivia | `#pragma`, `#region`, `#endregion`, `#define`, `#undef` | skipped unless `include_trivia` |

A **host policy** says how a container's arm fits its slot: `splice-repeat` (the
arm's items join a repeated list), `single-slot` / `optional-slot` (the arm fills
one slot), `list-run` (the arm carries items **and** separators, and for
permissions the property's own `;` terminator).

The classes live in `traversal/policy.json`, shipped in every package. Nothing is
classified by its name: a type is special because the policy says so, and
`tools/traversal_census.py` fails the build when the grammar gains a special type
the policy does not cover.

## What a visit carries

| Field | Meaning |
|---|---|
| `class` | one of the seven classes |
| `type`, `field` | the node type and the field it fills in its parent |
| `start`, `end` | UTF-8 byte offsets into the source, in every runtime (JS converts from UTF-16) |
| `arms` | `(if_offset, arm_id)` for every arm that wholly contains the node, outermost first |
| `host` | a branch container's host policy |
| `split` | for containers, assemblers and fragments that hold directives: `SplitInfo` |

`SplitInfo.groups` lists each `#if` group the node holds (a node can hold several),
each with **every** arm as `ArmFragments`: the descriptor (group id, arm id,
directive offsets, raw byte range) and the pieces inside that range in source order,
with field names, anonymous tokens kept as tokens. `SplitInfo.shared` lists the
node's own children outside every arm.

An arm can cross node boundaries: in `preproc_split_block_end_in_else` the `#else`
arm closes one procedure and opens the next, and its pieces say so.

## Python

```python
from tree_sitter import Language, Parser
import tree_sitter_al
from tree_sitter_al import traversal

policy = traversal.load_policy()
source = open("MyCodeunit.Codeunit.al", "rb").read()
tree = Parser(Language(tree_sitter_al.language())).parse(source)
doc = traversal.Document(tree, source, policy)

for v in traversal.walk(doc, policy):
    if v.type == "procedure":
        print("procedure", v.node.child_by_field_name("name").text.decode(), "arms", v.arms)
    elif v.cls == "assembler" and v.split:
        for group in v.split.groups:
            for arm in group.arms:
                name = next((f for f in arm.fragments if f.field == "name"), None)
                if name and any(f.type == "procedure_keyword" for f in arm.fragments):
                    print("split procedure", name.node.text.decode(), "arm", arm.descriptor.arm_id)
```

## JavaScript (native `tree-sitter` or `web-tree-sitter`)

One implementation serves both runtimes and never loads the native addon, so it is
safe in a browser bundle.

```js
const T = require('@sshadows/tree-sitter-al/traversal');
const policy = T.loadPolicy();
const doc = new T.Document(parser.parse(text), text, policy);   // pass the same text you parsed
for (const v of T.walk(doc, policy)) {
  if (v.cls === 'branch-container') console.log(v.type, v.host, v.split.groups.length, 'group(s)');
}
```

`v.start` / `v.end` are UTF-8 byte offsets. For a JS string index use the node's own
`startIndex`, or `doc.index(byteOffset)`.

## Rust

```toml
tree-sitter-al = { version = "5", features = ["traversal"] }
```

```rust
use tree_sitter_al::traversal::{walk, Document, Policy, WalkOptions};

let policy = Policy::bundled();
let doc = Document::new(&tree, source.as_bytes(), &policy);
for v in walk(&doc, &policy, None, WalkOptions::default()) {
    if v.class == "assembler" { /* v.split: Option<SplitInfo> */ }
}
```

The feature adds the `tree-sitter` runtime (`>=0.25, <0.27`) and `serde_json`; without
it the crate is unchanged.

## Migrating the patterns we have seen

**"Find every procedure"** (a recursion that stops at `type === 'procedure'`). Walk
instead, keep `type === 'procedure'`, and add split procedures from `SplitInfo` as in
the Python example. Each definition then carries `arms`, so a reviewer can tell the
`#if` and `#else` variants apart.

**"Collect members of known container types"** (a fixed list of section and body
types). Every `#if` container is a `branch-container` in the policy; treat any visit
of that class as transparent and its arms as members of its host. For a split object
declaration (`preproc_split_declaration`), the object's name is in each arm's
`object_name` fragment and its body is the shared `body`.

**"Is this statement in statement position?"** (a check on the parent's type). A
branch container splices its arm into its own host slot, so climb through
`branch-container` parents before asking: a call directly inside a
`preproc_conditional_statement` in a `statement_block` is a statement.

**"Tag nodes with their `#if` condition."** `arms` gives every arm of every kind, not
only statement-level ones. Only a path of arm-0 arms has an exact condition (the
`and` of the `#if` conditions); an `#elif` or `#else` arm's real condition negates
every arm before it, and needs the symbolic API (not in F0). Report those as
unsupported rather than guessing `!last-condition`.

## Keeping it correct

- `python tools/traversal_census.py` (validate-grammar.sh Step 5f): every special
  type classified, every entry still declared, the policy agreeing with
  `tools/config_oracle/contracts.py`.
- `python -m pytest tests/traversal`: the walker, `SplitInfo`, a witness per policy
  entry (each with a mutant that must fail), the consumer canaries, and the shared
  expected visits.
- `node --test tests/traversal/js/parity.test.js tests/traversal/js/canaries.test.js`
  and `cargo test --features traversal`: the other runtimes against the same files.
- After a deliberate walker change, `python tests/traversal/regen_expected.py`, then
  read the diff: those files only make the runtimes agree with Python; the
  hand-written tests say whether Python is right.

Tested runtimes: Python >= 3.12 with py-tree-sitter 0.25; Node 18 and 24 with
`tree-sitter` 0.25 and `web-tree-sitter` 0.27; Rust with `tree-sitter` 0.25 and 0.26.
````

It must say, as it does in its second section: "**Recursion alone does not fix node-kind recognition** … **Use `SplitInfo`**" (D10).

- [ ] **Step 2: CHANGELOG**

Under `## [Unreleased]`, add the `### Added` section above the existing `### Fixed` heading, and add the `### Fixed` bullet below as the FIRST bullet under that existing heading (do not add a second `### Fixed`):

```markdown
### Added

- **A classified traversal helper for `#if` code, in every binding (roadmap F0).**
  The tree parses every `#if` branch, so it holds conditional containers, constructs
  assembled from pieces in different branches, their fragments and the directive
  lines. `traversal/policy.json` classifies every such node type into seven classes
  (never by its name), ships in the npm, PyPI and crates.io packages, and is gated
  against `src/node-types.json` and the oracle registry by
  `tools/traversal_census.py` (validate-grammar.sh Step 5f). `walk` reports each node
  with its class, field, UTF-8 byte span and the `#if` arms around it; split
  constructs carry a `SplitInfo` listing every arm's pieces and the shared parts.
  Python `tree_sitter_al.traversal`; JavaScript `@sshadows/tree-sitter-al/traversal`,
  one implementation for the native binding and web-tree-sitter that never loads the
  addon; Rust `tree_sitter_al::traversal` behind the new `traversal` feature (off by
  default; adds `tree-sitter >=0.25, <0.27` and `serde_json`). All three give the same
  visits on the same fixtures. Additive: no parse tree changes. See
  `docs/traversal.md`, which also shows how to migrate the walk patterns that lose
  `#if` content today. Recursion alone does not fix node-kind recognition: use
  `SplitInfo`.

### Fixed

- **The Python sdist can be built.** It shipped neither `src/*.h` nor
  `src/tree_sitter/*.h`, so `pip install` from it stopped at
  `fatal error: tree_sitter/parser.h: No such file or directory`, and it carried no
  `queries/*.scm`. Wheels were unaffected. `MANIFEST.in` now includes them, and the
  traversal policy.
```

- [ ] **Step 3: CLAUDE.md quick reference**

In `CLAUDE.md`, inside the Quick Reference code block, after the `# Config oracle` lines, add:

```bash
# Traversal helper (roadmap F0, docs/traversal.md) -- validate-grammar.sh Step 5f is the census
python tools/traversal_census.py               # exit 0 clean, 1 finding, 2 cannot run
./tools/ts-lock.sh python -m pytest tests/traversal -q
node --test tests/traversal/js/parity.test.js tests/traversal/js/canaries.test.js   # after `npx node-gyp rebuild`
cargo test --features traversal
python tests/traversal/regen_expected.py      # a -u: review every hunk of the diff
```

- [ ] **Step 4: Final validation**

Run: `git diff --stat 0a8e220 -- src grammar.js`
Expected: no output.

Run: `./tools/ts-lock.sh ./validate-grammar.sh`
Expected: `Step 5f: Traversal Policy Census` reports `traversal policy census: clean`, and `All validation checks passed!`.

Run: `./tools/ts-lock.sh python -m pytest tests/traversal tools/tests -q && node --test tests/traversal/js/parity.test.js tests/traversal/js/canaries.test.js && cargo test --features traversal`
Expected: `270 passed` (244 traversal + 26 tool tests), `ℹ pass 34`, `test result: ok. 5 passed`.

Run: `git ls-files tests/traversal | wc -l; find tests/traversal -type f -not -path '*/__pycache__/*' | wc -l`
Expected: the same number twice (`36`).

- [ ] **Step 5: Commit**

```bash
git add docs/traversal.md CHANGELOG.md CLAUDE.md
git commit -m "docs(traversal): the F0 helper, its classes and migration examples (roadmap F0)

docs/traversal.md: the seven classes, what a visit carries, Python/JS/Rust
examples, and how to migrate the four walk patterns that lose #if content
today. Recursion alone does not fix node-kind recognition: use SplitInfo."
```

---

## Self-review

1. **Spec coverage.** §5.1 layer 1 (`ArmDescriptor` from the tree's own directives): Task 2. Layer 3 (`bind_arm` → `ArmFragments`, `groups_of`, wrong-revision rejection): Task 3. §6.1 policy, seven classes, host policies, never by prefix: Task 1 (file, census, no-prefix proofs), Task 2 (walk behaviour per class). `SplitInfo` (groups, every arm, shared parts with fields, anonymous tokens as tokens): Task 3. Census of prefixed and unprefixed, registered and unregistered types: Task 1. §6.2 item 1 parity: Tasks 5–7. Item 2 witnesses for every exception, the transparent `expression_tail` mutant, separator and terminator: Task 4. Item 3 canaries incl. LethAL R214 part 1: Task 8. Item 4 docs: Task 10. §7.1 packaging (Rust feature and range, Python module, browser-safe Node subpath, `node-types.json` untouched): Tasks 7, 9 and the Global Constraints. §9 release boundary: Task 10 CHANGELOG.
2. **Placeholders.** None: every step carries its content or an exact command and expected output.
3. **Type consistency.** Python `Visit.cls` is serialised as `"class"`; JS uses `cls` on the object and `class` in the parity form; Rust `Visit.class`. `group_id`/`groupId` is `(revision, if_offset)` everywhere; parity carries only the offset. `bind_arm` raises `WrongDocument` in Python and JS and returns `Err(WrongDocument)` in Rust.
4. **Review Focus.** Each of the five has its pinned test in the task named beside it.
