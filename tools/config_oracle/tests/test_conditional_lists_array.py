"""B7b-1 Task 9: the array_dimensions family (the dimension list of `array[...] of T`) in the
strict conditional list registry (spec 2026-10-07 section 6).

The host array_type owns more than the list: `array`, `[`, `]`, `of` and the `element_type`.
The region is what lies between the host's own `[` and `]` (conditional_lists.between_children);
an element type's own brackets (`Text[30]`) sit inside element_type, not as direct children.
Items are fielded `sizes`. Layers as test_conditional_lists_move.py: the focused fixture LOWERED
in every configuration (bar the alc-rejected MIXED ones), validate_split mutations, lowering
mutations, and the empty policy (alc rejects an empty dimension list, AL0367, and the flat grammar
requires a dimension, so an emptied configuration is a reference-error).
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
FIXTURE = "strict_conditional_array_dimensions_test.txt"
CASES = 31
GROUP = "preproc_conditional_array_dimensions"
HOST = "array_type"
ALLOWED_CLASSES = ("invalid-config:",)


def _cases():
    return [c for c in fixtures.extract(REPO / "test" / "corpus") if c.file == FIXTURE]


def _arr(dims, elem=b"Integer"):
    return b"codeunit 50100 C\n{\n    var\n        A: array[" + dims + b"] of " + elem + b";\n}\n"


# --- layer 1: the focused fixture ---------------------------------------------------------------

def test_fixture_has_the_task_9_cases():
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
    assert lowered >= 24, lowered


@pytest.mark.parametrize("case", _cases(), ids=lambda c: c.name)
def test_validate_split_is_clean_on_the_fixture(al_parser, case):
    assert cl.validate_split(_tree(al_parser, case.source)) == []


# --- registry ------------------------------------------------------------------------------------

def test_family_schema():
    fam = cl.FAMILIES["array_dimensions"]
    assert fam.group == GROUP
    assert fam.host_kinds == frozenset({HOST})
    assert fam.item_kinds == frozenset({"integer"})
    assert (fam.sep, fam.item_field, fam.cardinality) == (",", "sizes", "empty-semantic-rejected")
    assert contracts.REGISTRY[GROUP].hosts == {f"{HOST}:<children>": "strict-list",
                                               f"{GROUP}:<children>": "strict-list"}


SEP_BEFORE = _arr(b"2\n#if X\n, 3\n#endif\n, 4")
NESTED_ELSE = _arr(b"2\n#if X\n, 3\n#if Y\n, 4\n#endif\n#else\n, 5\n#endif\n")
ELSE_SEPS = _arr(b"2\n#if X\n, 3\n#else\n, 4\n#endif\n")


def test_region_is_between_the_brackets(al_parser):
    """`array` and `[` lie before the region; `]`, `of` and the element type after it -- and an
    element type with its own brackets does not move the region's end."""
    root = _tree(al_parser, _arr(b"2, 3", elem=b"Text[30]"))
    host, _ = _find(root, HOST)
    opener = next(c for c in host.children if c.kind == "[")
    closer = next(c for c in host.children if c.kind == "]")
    assert cl.FAMILIES["array_dimensions"].region(host) == (opener.end, closer.start)
    elem = next(c for c in host.children if c.field == "element_type")
    assert closer.end <= elem.start


def test_region_without_brackets_is_refused():
    from tools.config_oracle.ir import Node
    from tools.config_oracle.lowering.engine import LoweringError
    host = Node(HOST, True, None, 0, 9, [Node("array_keyword", True, None, 0, 5, []),
                                         Node("integer", True, "sizes", 6, 7, [])])
    with pytest.raises(LoweringError):
        cl.FAMILIES["array_dimensions"].region(host)


# --- layer 2: validate_split mutations -------------------------------------------------------------

def test_mutation_attachment_group_before_the_opening_bracket(al_parser):
    """A group moved between `array` and `[` lies outside the region."""
    root = _tree(al_parser, SEP_BEFORE)
    g, host = _find(root, GROUP)
    opener = next(c for c in host.children if c.kind == "[")
    host.children.remove(g)
    host.children.insert(host.children.index(opener), g)
    g.start, g.end = opener.start - 1, opener.start
    assert any("outside the list region" in p for p in _problems(root))
    assert runner_status_of_mutated(al_parser, SEP_BEFORE, root) == "representation-violation"


def test_mutation_attachment_group_in_the_element_type_slot(al_parser):
    """A group replacing the element type (after `of`) lies outside the region."""
    root = _tree(al_parser, SEP_BEFORE)
    g, host = _find(root, GROUP)
    elem = next(c for c in host.children if c.field == "element_type")
    host.children.remove(g)
    host.children[host.children.index(elem)] = g
    g.start, g.end = elem.start, elem.end
    assert any("outside the list region" in p for p in _problems(root))


def test_mutation_attachment_group_reaching_over_the_closing_bracket(al_parser):
    root = _tree(al_parser, _arr(b"2\n#if X\n, 3\n#endif\n"))
    g, host = _find(root, GROUP)
    g.end = next(c for c in host.children if c.kind == "]").end
    assert any("outside the list region" in p for p in _problems(root))


def test_mutation_group_with_a_field(al_parser):
    root = _tree(al_parser, SEP_BEFORE)
    g, _ = _find(root, GROUP)
    g.field = "sizes"
    assert any("fielded" in p for p in _problems(root))


@pytest.mark.parametrize("field", [None, "element_type", "element"])
def test_mutation_arm_item_with_the_wrong_field(al_parser, field):
    """Dimensions are `sizes:` inside an arm too: none, the element type's or another family's field is not one."""
    root = _tree(al_parser, SEP_BEFORE)
    g, _ = _find(root, GROUP)
    item = next(c for c in g.children if c.kind == "integer")
    assert item.field == "sizes"
    item.field = field
    assert any("arm content" in p for p in _problems(root))


def test_mutation_group_in_a_parent_that_is_not_its_slot(al_parser):
    root = _tree(al_parser, SEP_BEFORE)
    g, host = _find(root, GROUP)
    spec, _ = _find(root, "variable_declaration")
    host.children.remove(g)
    spec.children.append(g)
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


def test_mutation_neighbouring_array_region(al_parser):
    """Two array declarations side by side: a group moved into the other array's list is outside its region."""
    src = (b"codeunit 50100 C\n{\n    var\n        A: array[2\n#if X\n, 3\n#endif\n] of Integer;\n"
           b"        B: array[4\n#if X\n, 5\n#endif\n] of Integer;\n}\n")
    root = _tree(al_parser, src)
    _, first = _find(root, GROUP, 0)
    g2, second = _find(root, GROUP, 1)
    assert first is not second and first.kind == second.kind == HOST
    second.children.remove(g2)
    first.children.insert(next(i for i, c in enumerate(first.children) if c.kind == "]"), g2)
    assert any("outside the list region" in p for p in _problems(root))


def test_mutation_neighbouring_region_in_an_enclosing_conditional(al_parser):
    """Inside an enclosing preproc_conditional_var arm: the nested array's own group, moved into
    the enclosing conditional (not a permitted parent), is caught."""
    src = (b"codeunit 50100 C\n{\n    var\n        I: Integer;\n#if TPL\n        A: array[2\n#if X\n, 3\n#endif\n"
           b"] of Integer;\n#endif\n}\n")
    root = _tree(al_parser, src)
    g, host = _find(root, GROUP)
    outer, _ = _find(root, "preproc_conditional_var")
    decl = next(c for c in outer.children if c.kind == "variable_declaration")
    host.children.remove(g)
    outer.children.insert(outer.children.index(decl) + 1, g)
    assert any("not a permitted parent" in p for p in _problems(root))


# --- layer 3: lowering mutations and the empty policy ---------------------------------------------

def test_mutation_wrong_separator_count(al_parser, monkeypatch):
    from tools.config_oracle.lowering import select
    real = select._splice_arm
    monkeypatch.setattr(select, "_splice_arm", lambda items: [c for c in real(items) if c.kind != ","])
    assert witness.statuses_with(al_parser, SEP_BEFORE, "lowering:list-separator") == ["X=1"]


def test_mutation_swapped_order_in_the_lowered_arm(al_parser, monkeypatch):
    from tools.config_oracle.lowering import select
    src = _arr(b"\n#if X\n2 , 3\n#else\n2\n#endif\n")
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
    src = _arr(b"2 ,\n#if X\n#endif\n3")
    root = _tree(al_parser, src)
    g, host = _find(root, GROUP)
    host.children.remove(g)
    assert runner_status_of_mutated(al_parser, src, root) == "directive-mismatch"


def test_emptied_dimension_list_is_a_reference_error(al_parser):
    """alc rejects `array[] of Integer` (AL0367, manifest empty-semantic-rejected) and the flat
    grammar requires a dimension, so the emptied configuration never reaches lowering."""
    v = witness.verdicts(al_parser, _arr(b"\n#if X\n2 , 3\n#endif\n"))
    assert v["X=0"][0] == "cannot-validate" and v["X=0"][1][0].startswith("reference-error:"), v
    assert v["X=1"] == ("pass", []), v


def test_alternation_is_not_the_list_run_validator(al_parser, monkeypatch):
    from tools.config_oracle.lowering import engine

    def boom(new):
        raise AssertionError("strict list checked by _check_alternation")
    monkeypatch.setattr(engine, "_check_alternation", boom)
    witness.assert_all_pass(al_parser, SEP_BEFORE)
