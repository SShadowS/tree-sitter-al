"""B7b-1 Task 7: the sorting_fields and order_by_fields families (the inner field lists of
sorting( ... ) in a view value and of ascending( ... ) / descending( ... ) in OrderBy) in the
strict conditional list registry (spec 2026-10-07 section 6).

Both hosts own more than the list: a keyword and both parentheses, and sorting_value also
its order( ) / where( ) suffixes, so the region is the interior of the first parentheses
(conditional_lists.paren_after). Items are UNFIELDED. Layers as test_conditional_lists_field_list.py:
the focused fixtures LOWERED in every configuration (bar the alc-rejected MIXED ones),
validate_split mutations, lowering mutations, and the empty policy (alc and the flat
grammar both accept `sorting()` and `ascending()`).
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
FIXTURES = {"strict_conditional_sorting_fields_test.txt": 31,
            "strict_conditional_order_by_fields_test.txt": 30}
SG = "preproc_conditional_sorting_fields"
OG = "preproc_conditional_order_by_fields"
ALLOWED_CLASSES = ("invalid-config:",)


def _cases(name=None):
    return [c for c in fixtures.extract(REPO / "test" / "corpus")
            if c.file in FIXTURES and (name is None or c.file == name)]


# --- layer 1: the focused fixtures --------------------------------------------------------------

@pytest.mark.parametrize("name", sorted(FIXTURES))
def test_fixture_has_the_task_7_cases(name):
    assert len(_cases(name)) == FIXTURES[name]


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
    """Spec section 6, tests: the families are LOWERED, not classified away. Each placement
    passes in ALL its configurations, the emptied interiors (`sorting()`, `ascending()`) included."""
    statuses = {r.config: (r.status, r.items) for r in runner.check_input(al_parser, case.id, case.source)}
    assert all(s == "pass" for s, _ in statuses.values()), statuses


@pytest.mark.parametrize("group,minimum", [(SG, 24), (OG, 24)])
def test_enough_lowered_group_cases(al_parser, group, minimum):
    lowered = 0
    for case in _cases():
        root, _, _ = ir.from_tree(al_parser.parse(case.source))
        if group not in {n.kind for n, _ in _walk(root)}:
            continue
        assert "pass" in [r.status for r in runner.check_input(al_parser, case.id, case.source)], case.name
        lowered += 1
    assert lowered >= minimum, lowered


@pytest.mark.parametrize("case", _cases(), ids=lambda c: c.name)
def test_validate_split_is_clean_on_the_fixture(al_parser, case):
    assert cl.validate_split(_tree(al_parser, case.source)) == []


# --- registry ------------------------------------------------------------------------------------

@pytest.mark.parametrize("name,host,group", [("sorting_fields", "sorting_value", SG),
                                             ("order_by_fields", "order_by_item", OG)])
def test_family_schema(name, host, group):
    fam = cl.FAMILIES[name]
    assert fam.group == group
    assert fam.host_kinds == frozenset({host})
    assert fam.item_kinds == frozenset({"identifier", "quoted_identifier"})
    assert (fam.sep, fam.item_field, fam.cardinality) == (",", None, "empty-interior")
    assert contracts.REGISTRY[group].hosts == {f"{host}:<children>": "strict-list",
                                               f"{group}:<children>": "strict-list"}


def _view(lst, suffix=b""):
    return b"page 50102 PG\n{\n    SourceTableView = sorting(\n" + lst + b"\n)" + suffix + b";\n}\n"


def _order(lst, kw=b"ascending"):
    return b"query 50105 Qy\n{\n    OrderBy = " + kw + b"(\n" + lst + b"\n);\n}\n"


SORT_SUFFIX = _view(b"K\n#if X\n, N\n#endif", b" order(descending) where(B = const(true))")


def test_region_is_the_sorting_interior_only(al_parser):
    """The region ends at the first `)`: the order( ) and where( ) suffixes lie outside."""
    root = _tree(al_parser, SORT_SUFFIX)
    _, host = _find(root, SG)
    lo, hi = cl.FAMILIES["sorting_fields"].region(host)
    close = next(c for c in host.children if c.kind == ")")
    assert hi == close.start and SORT_SUFFIX[lo:hi].strip().startswith(b"K")
    assert SORT_SUFFIX[hi:host.end].startswith(b") order(descending)")


def test_region_of_the_order_first_view_is_refused():
    """`order(descending)` has no sorting( ): the adapter must not take order's parentheses."""
    from tools.config_oracle.ir import Node
    from tools.config_oracle.lowering.engine import LoweringError
    host = Node("sorting_value", True, None, 0, 17, [
        Node("order_keyword", True, None, 0, 5, []), Node("(", False, None, 5, 6, []),
        Node("descending_keyword", True, None, 6, 16, []), Node(")", False, None, 16, 17, [])])
    with pytest.raises(LoweringError):
        cl.FAMILIES["sorting_fields"].region(host)


# --- layer 2: validate_split mutations -------------------------------------------------------------

SEP_BEFORE = {SG: _view(b"K\n#if X\n, N\n#endif\n, B"), OG: _order(b"K\n#if X\n, N\n#endif\n, B")}
NESTED_ELSE = {SG: _view(b"K\n#if X\n, N\n#if Y\n, B\n#endif\n#else\n, O\n#endif"),
               OG: _order(b"K\n#if X\n, N\n#if Y\n, B\n#endif\n#else\n, O\n#endif")}
ELSE_SEPS = {SG: _view(b"K\n#if X\n, N\n#else\n, B\n#endif"), OG: _order(b"K\n#if X\n, N\n#else\n, B\n#endif")}
BOTH = pytest.mark.parametrize("group", [SG, OG])


@BOTH
def test_mutation_attachment_group_moved_outside_the_region(al_parser, group):
    root = _tree(al_parser, SEP_BEFORE[group])
    g, host = _find(root, group)
    g.start = host.start            # the group now takes in the keyword and the `(`
    assert any("outside the list region" in p for p in _problems(root))


def test_mutation_group_reaching_into_the_sorting_suffix(al_parser):
    """A group that runs past the list's `)` into order( ) is outside the region."""
    root = _tree(al_parser, SORT_SUFFIX)
    g, host = _find(root, SG)
    g.end = next(c for c in host.children if c.kind == "order_keyword").end
    assert any("outside the list region" in p for p in _problems(root))


@BOTH
def test_mutation_group_with_a_field(al_parser, group):
    root = _tree(al_parser, SEP_BEFORE[group])
    g, _ = _find(root, group)
    g.field = "value"
    assert any("fielded" in p for p in _problems(root))


@BOTH
def test_mutation_arm_item_with_a_field(al_parser, group):
    """The families are unfielded: an arm item carrying a field is not one of their items."""
    root = _tree(al_parser, SEP_BEFORE[group])
    g, _ = _find(root, group)
    next(c for c in g.children if c.kind == "identifier").field = "field"
    assert any("arm content" in p for p in _problems(root))


@BOTH
def test_mutation_group_in_a_parent_that_is_not_its_slot(al_parser, group):
    root = _tree(al_parser, SEP_BEFORE[group])
    g, host = _find(root, group)
    prop, _ = _find(root, "property")
    host.children.remove(g)
    prop.children.append(g)
    assert any("not a permitted parent" in p for p in _problems(root))


@BOTH
def test_mutation_swapped_order(al_parser, group):
    root = _tree(al_parser, SEP_BEFORE[group])
    g, host = _find(root, group)
    i = host.children.index(g)
    host.children[i], host.children[i + 1] = host.children[i + 1], host.children[i]
    assert any("source order" in p for p in _problems(root))


@BOTH
def test_mutation_nesting_in_the_wrong_arm(al_parser, group):
    root = _tree(al_parser, NESTED_ELSE[group])
    outer, _ = _find(root, group, 0)
    inner, parent = _find(root, group, 1)
    assert parent is outer
    outer.children.remove(inner)
    at = next(i for i, c in enumerate(outer.children) if c.kind == "preproc_else") + 1
    outer.children.insert(at, inner)
    assert any("outside its arm" in p for p in _problems(root))


@BOTH
def test_mutation_wrong_outer_arm_ownership(al_parser, group):
    """Detected through the order check: the host's children then overlap."""
    root = _tree(al_parser, NESTED_ELSE[group])
    outer, host = _find(root, group, 0)
    inner, _ = _find(root, group, 1)
    outer.children.remove(inner)
    host.children.insert(host.children.index(outer) + 1, inner)
    assert any("source order" in p for p in _problems(root))


@BOTH
def test_mutation_separator_moved_to_the_other_arm(al_parser, group):
    src = ELSE_SEPS[group]
    root = _tree(al_parser, src)
    g, _ = _find(root, group)
    comma = next(c for c in g.children if c.kind == ",")
    g.children.remove(comma)
    g.children.insert(next(i for i, c in enumerate(g.children) if c.kind == "preproc_else") + 1, comma)
    assert any("source order" in p for p in _problems(root))
    assert runner_status_of_mutated(al_parser, src, root) == "representation-violation"


def test_mutation_neighbouring_order_by_item(al_parser):
    """Two items of one OrderBy list: a group moved into the other item's list is outside its region."""
    src = b"query 50105 Qy\n{\n    OrderBy = ascending(K\n#if X\n, N\n#endif\n), descending(B\n#if X\n, O\n#endif\n);\n}\n"
    root = _tree(al_parser, src)
    _, first = _find(root, OG, 0)
    g2, second = _find(root, OG, 1)
    assert first is not second
    second.children.remove(g2)
    first.children.insert(len(first.children) - 1, g2)
    assert any("outside the list region" in p for p in _problems(root))


def test_mutation_neighbouring_sorting_value(al_parser):
    src = (b"page 50102 PG\n{\n    SourceTableView = sorting(K\n#if X\n, N\n#endif\n);\n"
           b"    SourceTableView = sorting(B\n#if X\n, O\n#endif\n);\n}\n")
    root = _tree(al_parser, src)
    _, first = _find(root, SG, 0)
    g2, second = _find(root, SG, 1)
    second.children.remove(g2)
    first.children.insert(len(first.children) - 1, g2)
    assert any("outside the list region" in p for p in _problems(root))


# --- layer 3: lowering mutations and the empty policy ---------------------------------------------

@BOTH
def test_mutation_wrong_separator_count(al_parser, monkeypatch, group):
    from tools.config_oracle.lowering import select
    real = select._splice_arm
    monkeypatch.setattr(select, "_splice_arm", lambda items: [c for c in real(items) if c.kind != ","])
    assert witness.statuses_with(al_parser, SEP_BEFORE[group], "lowering:list-separator") == ["X=1"]


@BOTH
def test_mutation_swapped_order_in_the_lowered_arm(al_parser, monkeypatch, group):
    from tools.config_oracle.lowering import select
    src = (_view if group == SG else _order)(b"#if X\nK , N\n#else\nK\n#endif")
    real = select._splice_arm
    monkeypatch.setattr(select, "_splice_arm", lambda items: list(reversed(real(items))))
    v = witness.verdicts(al_parser, src)
    assert v["X=1"][0] == "discrepancy" and any("structure" in i for i in v["X=1"][1]), v


@BOTH
def test_mutation_selected_arm_emptied(al_parser, monkeypatch, group):
    from tools.config_oracle.lowering import select
    monkeypatch.setattr(select, "_splice_arm", lambda items: [])
    assert witness.statuses_with(al_parser, SEP_BEFORE[group], "lowering:accounting") == ["X=1"]


@BOTH
def test_mutation_unselected_arm_content_leaks(al_parser, monkeypatch, group):
    import dataclasses
    entry = contracts.REGISTRY[group]
    monkeypatch.setitem(contracts.REGISTRY, group, dataclasses.replace(
        entry, handler="tools.config_oracle.tests.test_conditional_lists.leaky_select"))
    assert witness.statuses_with(al_parser, NESTED_ELSE[group], "lowering:accounting")


@BOTH
def test_mutation_empty_group_dropped_from_the_split_tree(al_parser, group):
    src = (_view if group == SG else _order)(b"K ,\n#if X\n#endif\nN")
    root = _tree(al_parser, src)
    g, host = _find(root, group)
    host.children.remove(g)
    assert runner_status_of_mutated(al_parser, src, root) == "directive-mismatch"


@pytest.mark.parametrize("src", [
    _view(b"#if X\nK , N\n#endif"),
    _view(b"#if X\nK , N\n#endif", b" where(B = const(true))"),
    _order(b"#if X\nK , N\n#endif"),
    _order(b"#if X\nK , N\n#endif", kw=b"descending"),
], ids=["sorting", "sorting+where", "ascending", "descending"])
def test_emptied_interior_keeps_the_host(al_parser, src):
    """alc accepts `sorting()` and `ascending()` (manifest empty-interior), and the flat grammar
    parses them: the emptied configuration keeps the keyword and both parentheses, no rewrite."""
    v = witness.verdicts(al_parser, src)
    assert v == {"X=0": ("pass", []), "X=1": ("pass", [])}, v


@BOTH
def test_alternation_is_not_the_list_run_validator(al_parser, monkeypatch, group):
    from tools.config_oracle.lowering import engine

    def boom(new):
        raise AssertionError("strict list checked by _check_alternation")
    monkeypatch.setattr(engine, "_check_alternation", boom)
    witness.assert_all_pass(al_parser, SEP_BEFORE[group])
