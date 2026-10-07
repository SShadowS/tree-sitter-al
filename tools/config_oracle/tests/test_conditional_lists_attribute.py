"""B7b-1 Task 10: the attribute_args family (the argument list of `[Attr(a, b)]`) in the strict
conditional list registry (spec 2026-10-07 section 6).

The host attribute_argument_list is visible and unfielded and owns nothing but the list, so the
region is its whole span. Its parent attribute_arguments keeps `(`, `)` and its
`optional(attribute_argument_list)` wrapper: an emptied configuration flat-parses as `[A()]` with no
attribute_argument_list, and lowering removes the host (optional-list-removed:attribute_argument_list,
spec 4.2 case 2). Layers as test_conditional_lists_array.py: the focused fixture LOWERED in every
configuration (bar the alc-rejected MIXED ones whose flat parse errors), validate_split mutations,
lowering mutations, and the empty policy.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tools.config_oracle import contracts, fixtures, ir, runner
from tools.config_oracle.lowering import conditional_lists as cl
from tools.config_oracle.tests import witness
from tools.config_oracle.tests.test_conditional_lists import (
    _find, _problems, _tree, _walk, runner_status_of_mutated)

REPO = Path(__file__).resolve().parents[3]
FIXTURE = "strict_conditional_attribute_args_test.txt"
CASES = 39
GROUP = "preproc_conditional_attribute_args"
HOST = "attribute_argument_list"
ITEMS = frozenset({"boolean", "integer", "string_literal", "identifier", "quoted_identifier",
                   "qualified_enum_value", "database_reference", "member_expression"})
ALLOWED_CLASSES = ("invalid-config:",)


def _cases():
    return [c for c in fixtures.extract(REPO / "test" / "corpus") if c.file == FIXTURE]


def _attr(args, name=b"A"):
    return b"codeunit 50100 C\n{\n    [" + name + b"(" + args + b")]\n    procedure P()\n    begin\n    end;\n}\n"


def _items(verdict):
    return [i.split("@")[0] for i in verdict[1]]


# --- layer 1: the focused fixture ---------------------------------------------------------------

def test_fixture_has_the_task_10_cases():
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
    """Every group case alc accepts in every configuration."""
    return [c for c in _cases() if " MIXED" not in c.name and "preservation" not in c.name]


@pytest.mark.parametrize("case", _placement_cases(), ids=lambda c: c.name)
def test_placement_case_passes_in_every_configuration(al_parser, case):
    """Spec section 6, tests: the family is LOWERED, not classified away."""
    statuses = {r.config: (r.status, r.items) for r in runner.check_input(al_parser, case.id, case.source)}
    assert all(s == "pass" for s, _ in statuses.values()), statuses


def test_enough_lowered_group_cases(al_parser):
    lowered = 0
    for case in _cases():
        root, _, _ = ir.from_tree(al_parser.parse(case.source))
        if not any(n.kind == GROUP for n, _ in _walk(root)):
            continue
        assert "pass" in [r.status for r in runner.check_input(al_parser, case.id, case.source)], case.name
        lowered += 1
    assert lowered >= 30, lowered


@pytest.mark.parametrize("case", _cases(), ids=lambda c: c.name)
def test_validate_split_is_clean_on_the_fixture(al_parser, case):
    assert cl.validate_split(_tree(al_parser, case.source)) == []


# --- registry ------------------------------------------------------------------------------------

def test_family_schema():
    fam = cl.FAMILIES["attribute_args"]
    assert fam.group == GROUP
    assert fam.host_kinds == frozenset({HOST})
    assert fam.item_kinds == ITEMS
    assert (fam.sep, fam.item_field, fam.cardinality) == (",", None, "optional-wrapper")
    assert contracts.REGISTRY[GROUP].hosts == {f"{HOST}:<children>": "strict-list",
                                               f"{GROUP}:<children>": "strict-list"}


SEP_BEFORE = _attr(b"'a'\n#if X\n, 'b'\n#endif\n, 'c'")
NESTED_ELSE = _attr(b"'a'\n#if X\n, 'b'\n#if Y\n, 'c'\n#endif\n#else\n, 'd'\n#endif\n")
ELSE_SEPS = _attr(b"'a'\n#if X\n, 'b'\n#else\n, 'c'\n#endif\n")
ONLY_ITEM = _attr(b"\n#if X\n1\n#endif\n")


def test_region_is_the_whole_host(al_parser):
    """The host owns nothing but the list; `(` and `)` belong to attribute_arguments."""
    root = _tree(al_parser, _attr(b"1, 2"))
    host, parent = _find(root, HOST)
    assert parent.kind == "attribute_arguments"
    assert cl.FAMILIES["attribute_args"].region(host) == (host.start, host.end)
    assert [c.kind for c in parent.children] == ["(", HOST, ")"]


# --- layer 2: validate_split mutations -------------------------------------------------------------

def test_mutation_attachment_group_outside_the_host_span(al_parser):
    """A group moved before the host's start (onto the `(`) lies outside the region."""
    root = _tree(al_parser, SEP_BEFORE)
    g, host = _find(root, GROUP)
    host.children.remove(g)
    host.children.insert(0, g)
    g.start, g.end = host.start - 1, host.start
    assert any("outside the list region" in p for p in _problems(root))
    assert runner_status_of_mutated(al_parser, SEP_BEFORE, root) == "representation-violation"


def test_mutation_attachment_group_reaching_over_the_host_end(al_parser):
    root = _tree(al_parser, SEP_BEFORE)
    g, host = _find(root, GROUP)
    g.end = host.end + 1
    assert any("outside the list region" in p for p in _problems(root))


def test_mutation_group_with_a_field(al_parser):
    root = _tree(al_parser, SEP_BEFORE)
    g, _ = _find(root, GROUP)
    g.field = "arguments"
    assert any("fielded" in p for p in _problems(root))


@pytest.mark.parametrize("field", ["arguments", "name", "element"])
def test_mutation_arm_item_with_a_field(al_parser, field):
    """Arguments are unfielded inside an arm too: the parent's field, the attribute name's or another
    family's field is not one."""
    root = _tree(al_parser, SEP_BEFORE)
    g, _ = _find(root, GROUP)
    item = next(c for c in g.children if c.kind == "string_literal")
    assert item.field is None
    item.field = field
    assert any("arm content" in p for p in _problems(root))


def test_mutation_arm_item_of_a_foreign_kind(al_parser):
    root = _tree(al_parser, SEP_BEFORE)
    g, _ = _find(root, GROUP)
    item = next(c for c in g.children if c.kind == "string_literal")
    item.kind = "decimal"
    assert any("arm content" in p for p in _problems(root))


def test_mutation_group_in_a_parent_that_is_not_its_slot(al_parser):
    """Moved up into attribute_arguments (beside the host, not in it)."""
    root = _tree(al_parser, SEP_BEFORE)
    g, host = _find(root, GROUP)
    _, args = _find(root, HOST)
    host.children.remove(g)
    args.children.insert(args.children.index(host) + 1, g)
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
    """Detected through the order check: the host's children then overlap."""
    root = _tree(al_parser, NESTED_ELSE)
    outer, host = _find(root, GROUP, 0)
    inner, _ = _find(root, GROUP, 1)
    outer.children.remove(inner)
    host.children.insert(host.children.index(outer) + 1, inner)
    assert any("source order" in p for p in _problems(root))


def test_mutation_separator_moved_to_the_other_arm(al_parser):
    root = _tree(al_parser, ELSE_SEPS)
    g, _ = _find(root, GROUP)
    comma = next(c for c in g.children if c.kind == ",")
    g.children.remove(comma)
    g.children.insert(next(i for i, c in enumerate(g.children) if c.kind == "preproc_else") + 1, comma)
    assert any("source order" in p for p in _problems(root))
    assert runner_status_of_mutated(al_parser, ELSE_SEPS, root) == "representation-violation"


def test_mutation_neighbouring_attribute_region(al_parser):
    """Two stacked attributes: a group moved into the other attribute's list is outside its region."""
    src = (b"codeunit 50100 C\n{\n    [A(1\n#if X\n, 2\n#endif\n)]\n    [B(3\n#if X\n, 4\n#endif\n)]\n"
           b"    procedure P()\n    begin\n    end;\n}\n")
    root = _tree(al_parser, src)
    _, first = _find(root, GROUP, 0)
    g2, second = _find(root, GROUP, 1)
    assert first is not second and first.kind == second.kind == HOST
    second.children.remove(g2)
    first.children.append(g2)
    assert any("outside the list region" in p for p in _problems(root))


def test_mutation_neighbouring_region_in_an_enclosing_conditional(al_parser):
    """Inside an enclosing preproc_conditional arm: the attribute's own group, moved into the
    enclosing conditional (not a permitted parent), is caught."""
    src = (b"codeunit 50100 C\n{\n#if TPL\n    [A('a'\n#if X\n, 'b'\n#endif\n)]\n    procedure P()\n"
           b"    begin\n    end;\n#endif\n}\n")
    root = _tree(al_parser, src)
    g, host = _find(root, GROUP)
    outer, _ = _find(root, "preproc_conditional")
    item = next(c for c in outer.children if c.kind == "attribute_item")
    host.children.remove(g)
    outer.children.insert(outer.children.index(item) + 1, g)
    assert any("not a permitted parent" in p for p in _problems(root))


# --- layer 3: lowering mutations and the empty policy ---------------------------------------------

def test_mutation_wrong_separator_count(al_parser, monkeypatch):
    from tools.config_oracle.lowering import select
    real = select._splice_arm
    monkeypatch.setattr(select, "_splice_arm", lambda items: [c for c in real(items) if c.kind != ","])
    assert witness.statuses_with(al_parser, SEP_BEFORE, "lowering:list-separator") == ["X=1"]


def test_mutation_swapped_order_in_the_lowered_arm(al_parser, monkeypatch):
    from tools.config_oracle.lowering import select
    src = _attr(b"\n#if X\n'a' , 'b'\n#else\n'a'\n#endif\n")
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
    src = _attr(b"1 ,\n#if X\n#endif\n2")
    root = _tree(al_parser, src)
    g, host = _find(root, GROUP)
    host.children.remove(g)
    assert runner_status_of_mutated(al_parser, src, root) == "directive-mismatch"


def test_emptied_argument_list_removes_the_host(al_parser):
    """`[A(#if X 1 #endif)]` under X undefined flat-parses as `[A()]`, which has no
    attribute_argument_list (optional wrapper, spec 4.2 case 2): lowering removes the host and the
    configuration agrees with the flat parse. Under X it passes with the list."""
    v = witness.verdicts(al_parser, ONLY_ITEM)
    assert v["X=1"] == ("pass", []), v
    assert v["X=0"][0] == "pass", v
    assert _items(v["X=0"]) == ["normalised:optional-list-removed:attribute_argument_list"], v


def test_empty_group_alone_removes_the_host_in_every_configuration(al_parser):
    v = witness.verdicts(al_parser, _attr(b"\n#if X\n#endif\n"))
    for config in ("X=0", "X=1"):
        assert v[config][0] == "pass", v
        assert _items(v[config]) == ["normalised:optional-list-removed:attribute_argument_list"], v


def test_emptied_argument_list_without_the_removal_is_caught(al_parser, monkeypatch):
    """The removal is load-bearing: a lowering that keeps the empty host disagrees with `[A()]`."""
    real = cl.lower_region

    def keep_empty(host, kids, family):
        out = real(host, kids, family)
        return out if out else [ir.Node(",", False, None, host.start, host.start, [])]
    monkeypatch.setattr(cl, "lower_region", keep_empty)
    v = witness.verdicts(al_parser, ONLY_ITEM)
    assert v["X=0"][0] != "pass", v


def test_alternation_is_not_the_list_run_validator(al_parser, monkeypatch):
    from tools.config_oracle.lowering import engine

    def boom(new):
        raise AssertionError("strict list checked by _check_alternation")
    monkeypatch.setattr(engine, "_check_alternation", boom)
    witness.assert_all_pass(al_parser, SEP_BEFORE)
