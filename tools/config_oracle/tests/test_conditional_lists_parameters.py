"""B7b-1b (deferred item 46): the parameters family (the `;`-separated list of a procedure, event,
interface procedure or trigger) in the strict conditional list registry (spec 2026-10-07 section 6).

The host parameter_list is visible and unfielded and owns nothing but the list, so the region is its
whole span; `(` and `)` belong to the procedure-like host, whose optional(parameter_list) wrapper
means an emptied configuration flat-parses as `()` with no parameter_list, and lowering removes the
host (optional-list-removed:parameter_list). An item is a parameter with the attribute_item bundle
before it (Family.prefix_kinds): a prefix belongs to the item after it and never stands alone.
Layers as test_conditional_lists_attribute.py.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tools.config_oracle import contracts, fixtures, ir, runner
from tools.config_oracle.ir import Node
from tools.config_oracle.lowering import conditional_lists as cl
from tools.config_oracle.lowering.engine import LoweringError
from tools.config_oracle.tests import witness
from tools.config_oracle.tests.test_conditional_lists import (
    _find, _problems, _tree, _walk, runner_status_of_mutated)

REPO = Path(__file__).resolve().parents[3]
FIXTURE = "strict_conditional_parameters_test.txt"
CASES = 22
GROUP = "preproc_conditional_parameters"
HOST = "parameter_list"
ALLOWED_CLASSES = ("invalid-config:", "debt(C1):")


def _cases():
    return [c for c in fixtures.extract(REPO / "test" / "corpus") if c.file == FIXTURE]


def _proc(params):
    return b"codeunit 50100 C\n{\n    procedure P(" + params + b")\n    begin\n    end;\n}\n"


def _items(verdict):
    return [i.split("@")[0] for i in verdict[1]]


# --- layer 1: the focused fixture ---------------------------------------------------------------

def test_fixture_has_the_cases():
    assert len(_cases()) == CASES


@pytest.mark.parametrize("case", _cases(), ids=lambda c: c.name)
def test_fixture_case_lowers_in_every_configuration(al_parser, case):
    records = runner.check_input(al_parser, case.id, case.source)
    classes = fixtures.load_classes(REPO / "tools" / "config_oracle" / "fixture-classes.tsv")
    mine = {k: v for k, v in classes.items() if k[0] == case.id}
    expanded, stale = runner.expand_classes(mine, {case.id: [r.config for r in records]})
    assert not stale, stale
    for r in records:
        if r.status == "pass":
            continue
        entry = expanded.get((r.input_id, r.config))
        assert entry is not None and entry[1].startswith(ALLOWED_CLASSES), (r.config, r.status, r.items)
        assert runner.is_classified(r, expanded), (r.config, r.items)


def _placement_cases():
    """Every group case alc accepts in every configuration whose host has a lowering."""
    return [c for c in _cases() if " MIXED" not in c.name and "preservation" not in c.name
            and "var section" not in c.name]


@pytest.mark.parametrize("case", _placement_cases(), ids=lambda c: c.name)
def test_placement_case_passes_in_every_configuration(al_parser, case):
    """Spec section 6, tests: the family is LOWERED, not classified away."""
    statuses = {r.config: (r.status, r.items) for r in runner.check_input(al_parser, case.id, case.source)}
    assert all(s == "pass" for s, _ in statuses.values()), statuses


@pytest.mark.parametrize("case", _cases(), ids=lambda c: c.name)
def test_validate_split_is_clean_on_the_fixture(al_parser, case):
    assert cl.validate_split(_tree(al_parser, case.source)) == []


# --- registry ------------------------------------------------------------------------------------

def test_family_schema():
    fam = cl.FAMILIES["parameters"]
    assert fam.group == GROUP
    assert fam.host_kinds == frozenset({HOST})
    assert fam.item_kinds == frozenset({"parameter"})
    assert fam.prefix_kinds == frozenset({"attribute_item"})
    assert (fam.sep, fam.item_field, fam.cardinality) == (";", None, "optional-wrapper")
    assert contracts.REGISTRY[GROUP].hosts == {f"{HOST}:<children>": "strict-list",
                                               f"{GROUP}:<children>": "strict-list"}


SEP_BEFORE = _proc(b"A: Integer\n#if X\n; B: Integer\n#endif\n; C: Integer")
NESTED_ELSE = _proc(b"A: Integer\n#if X\n; B: Integer\n#if Y\n; C: Integer\n#endif\n#else\n; D: Integer\n#endif\n")
ELSE_SEPS = _proc(b"A: Integer\n#if X\n; B: Integer\n#else\n; C: Integer\n#endif\n")
ONLY_ITEM = _proc(b"\n#if X\nA: Integer\n#endif\n")
ATTR_IN_ARM = _proc(b"A: Integer\n#if X\n; [Attr] var B: Integer\n#endif\n")


def test_region_is_the_whole_host(al_parser):
    root = _tree(al_parser, _proc(b"A: Integer; B: Integer"))
    host, parent = _find(root, HOST)
    assert parent.kind == "procedure"
    assert cl.FAMILIES["parameters"].region(host) == (host.start, host.end)


# --- layer 2: validate_split mutations -------------------------------------------------------------

def test_mutation_attachment_group_outside_the_host_span(al_parser):
    root = _tree(al_parser, SEP_BEFORE)
    g, host = _find(root, GROUP)
    g.end = host.end + 1
    assert any("outside the list region" in p for p in _problems(root))
    assert runner_status_of_mutated(al_parser, SEP_BEFORE, root) == "representation-violation"


def test_mutation_group_with_a_field(al_parser):
    root = _tree(al_parser, SEP_BEFORE)
    g, _ = _find(root, GROUP)
    g.field = "parameters"
    assert any("fielded" in p for p in _problems(root))


@pytest.mark.parametrize("kind", ["parameter", "attribute_item"])
def test_mutation_arm_item_with_a_field(al_parser, kind):
    """Parameters and their attributes are unfielded inside an arm too."""
    root = _tree(al_parser, ATTR_IN_ARM)
    g, _ = _find(root, GROUP)
    item = next(c for c in g.children if c.kind == kind)
    assert item.field is None
    item.field = "parameters"
    assert any("arm content" in p for p in _problems(root))


def test_attribute_prefix_in_an_arm_is_arm_content(al_parser):
    assert cl.validate_split(_tree(al_parser, ATTR_IN_ARM)) == []


def test_mutation_arm_item_of_a_foreign_kind(al_parser):
    root = _tree(al_parser, SEP_BEFORE)
    g, _ = _find(root, GROUP)
    item = next(c for c in g.children if c.kind == "parameter")
    item.kind = "variable_declaration"
    assert any("arm content" in p for p in _problems(root))


def test_mutation_group_in_a_parent_that_is_not_its_slot(al_parser):
    """Moved up into the procedure (beside the host, not in it)."""
    root = _tree(al_parser, SEP_BEFORE)
    g, host = _find(root, GROUP)
    _, proc = _find(root, HOST)
    host.children.remove(g)
    proc.children.insert(proc.children.index(host) + 1, g)
    assert any("not a permitted parent" in p for p in _problems(root))


def test_mutation_swapped_order(al_parser):
    root = _tree(al_parser, SEP_BEFORE)
    g, host = _find(root, GROUP)
    i = host.children.index(g)
    host.children[i], host.children[i + 1] = host.children[i + 1], host.children[i]
    assert any("source order" in p for p in _problems(root))


def test_mutation_nesting_in_the_wrong_arm(al_parser):
    root = _tree(al_parser, NESTED_ELSE)
    outer, _ = _find(root, GROUP, 0)
    inner, parent = _find(root, GROUP, 1)
    assert parent is outer
    outer.children.remove(inner)
    at = next(i for i, c in enumerate(outer.children) if c.kind == "preproc_else") + 1
    outer.children.insert(at, inner)
    assert any("outside its arm" in p for p in _problems(root))


def test_mutation_wrong_outer_arm_ownership(al_parser):
    root = _tree(al_parser, NESTED_ELSE)
    outer, host = _find(root, GROUP, 0)
    inner, _ = _find(root, GROUP, 1)
    outer.children.remove(inner)
    host.children.insert(host.children.index(outer) + 1, inner)
    assert any("source order" in p for p in _problems(root))


def test_mutation_separator_moved_to_the_other_arm(al_parser):
    root = _tree(al_parser, ELSE_SEPS)
    g, _ = _find(root, GROUP)
    semi = next(c for c in g.children if c.kind == ";")
    g.children.remove(semi)
    g.children.insert(next(i for i, c in enumerate(g.children) if c.kind == "preproc_else") + 1, semi)
    assert any("source order" in p for p in _problems(root))
    assert runner_status_of_mutated(al_parser, ELSE_SEPS, root) == "representation-violation"


def test_mutation_neighbouring_procedure_region(al_parser):
    """Two procedures: a group moved into the other procedure's list is outside its region."""
    src = (b"codeunit 50100 C\n{\n    procedure P(A: Integer\n#if X\n; B: Integer\n#endif\n)\n    begin\n    end;\n"
           b"    procedure Q(C: Integer\n#if X\n; D: Integer\n#endif\n)\n    begin\n    end;\n}\n")
    root = _tree(al_parser, src)
    _, first = _find(root, GROUP, 0)
    g2, second = _find(root, GROUP, 1)
    assert first is not second and first.kind == second.kind == HOST
    second.children.remove(g2)
    first.children.append(g2)
    assert any("outside the list region" in p for p in _problems(root))


# --- layer 3: lowering mutations and the empty policy ---------------------------------------------

def test_mutation_wrong_separator_count(al_parser, monkeypatch):
    from tools.config_oracle.lowering import select
    real = select._splice_arm
    monkeypatch.setattr(select, "_splice_arm", lambda items: [c for c in real(items) if c.kind != ";"])
    assert witness.statuses_with(al_parser, SEP_BEFORE, "lowering:list-separator") == ["X=1"]


def test_mutation_swapped_order_in_the_lowered_arm(al_parser, monkeypatch):
    from tools.config_oracle.lowering import select
    src = _proc(b"\n#if X\nA: Integer ; B: Text\n#else\nA: Integer\n#endif\n")
    real = select._splice_arm
    monkeypatch.setattr(select, "_splice_arm", lambda items: list(reversed(real(items))))
    v = witness.verdicts(al_parser, src)
    assert v["X=1"][0] == "discrepancy" and any("structure" in i for i in v["X=1"][1]), v


def test_mutation_selected_arm_emptied(al_parser, monkeypatch):
    from tools.config_oracle.lowering import select
    monkeypatch.setattr(select, "_splice_arm", lambda items: [])
    assert witness.statuses_with(al_parser, SEP_BEFORE, "lowering:accounting") == ["X=1"]


def test_mutation_unselected_arm_content_leaks(al_parser, monkeypatch):
    import dataclasses
    entry = contracts.REGISTRY[GROUP]
    monkeypatch.setitem(contracts.REGISTRY, GROUP, dataclasses.replace(
        entry, handler="tools.config_oracle.tests.test_conditional_lists.leaky_select"))
    assert witness.statuses_with(al_parser, NESTED_ELSE, "lowering:accounting")


def test_mutation_empty_group_dropped_from_the_split_tree(al_parser):
    src = _proc(b"A: Integer ;\n#if X\n#endif\nB: Integer")
    root = _tree(al_parser, src)
    g, host = _find(root, GROUP)
    host.children.remove(g)
    assert runner_status_of_mutated(al_parser, src, root) == "directive-mismatch"


def test_attribute_prefix_in_an_arm_lowers(al_parser):
    witness.assert_all_pass(al_parser, ATTR_IN_ARM)


def _leaf(kind, start, named=True):
    return Node(kind, named, None, start, start + 1, [])


@pytest.mark.parametrize("kinds", [
    ["attribute_item"],                                  # a prefix alone
    ["attribute_item", ";", "parameter"],                # a prefix before a separator
    ["parameter", "attribute_item", ";", "parameter"],   # a prefix after an item
    ["parameter", ";", "attribute_item"],                # a prefix at the end
])
def test_lower_region_rejects_a_dangling_prefix(kinds):
    kids = [_leaf(k, i, named=(k != ";")) for i, k in enumerate(kinds)]
    host = Node(HOST, True, None, 0, len(kinds), kids)
    with pytest.raises(LoweringError):
        cl.lower_region(host, kids, cl.FAMILIES["parameters"])


def test_lower_region_accepts_prefixed_items():
    kinds = ["attribute_item", "attribute_item", "parameter", ";", "attribute_item", "parameter"]
    kids = [_leaf(k, i, named=(k != ";")) for i, k in enumerate(kinds)]
    host = Node(HOST, True, None, 0, len(kinds), kids)
    assert cl.lower_region(host, kids, cl.FAMILIES["parameters"]) == kids


def test_emptied_parameter_list_removes_the_host(al_parser):
    """`P(#if X A: Integer #endif)` under X undefined flat-parses as `P()`, which has no
    parameter_list: lowering removes the host and the configuration agrees with the flat parse."""
    v = witness.verdicts(al_parser, ONLY_ITEM)
    assert v["X=1"] == ("pass", []), v
    assert v["X=0"][0] == "pass", v
    assert _items(v["X=0"]) == ["normalised:optional-list-removed:parameter_list"], v


def test_emptied_parameter_list_without_the_removal_is_caught(al_parser, monkeypatch):
    real = cl.lower_region

    def keep_empty(host, kids, family):
        out = real(host, kids, family)
        return out if out else [ir.Node(";", False, None, host.start, host.start, [])]
    monkeypatch.setattr(cl, "lower_region", keep_empty)
    v = witness.verdicts(al_parser, ONLY_ITEM)
    assert v["X=0"][0] != "pass", v


def test_alternation_is_not_the_list_run_validator(al_parser, monkeypatch):
    from tools.config_oracle.lowering import engine

    def boom(new):
        raise AssertionError("strict list checked by _check_alternation")
    monkeypatch.setattr(engine, "_check_alternation", boom)
    witness.assert_all_pass(al_parser, SEP_BEFORE)
