"""B7b-1 Task 8: the move_elements family (the element list of moveafter / movebefore /
movefirst / movelast after the fixed `;`) in the strict conditional list registry (spec
2026-10-07 section 6).

The four hosts own more than the list: a keyword, `(`, the `target`, the fixed `;` and `)`.
The region is what lies between the fixed `;` and `)` (conditional_lists.between_children),
so a group in the target slot or around the `;` is outside it (spec rev 2: B7b-3). Items are
fielded `element`. Layers as test_conditional_lists_sorting_order_by.py: the focused fixture
LOWERED in every configuration (bar the alc-rejected MIXED ones), validate_split mutations,
lowering mutations, and the empty policy (alc rejects an empty element list, AL0319, and the
flat grammar requires an element, so an emptied configuration is a reference-error).
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
FIXTURE = "strict_conditional_move_elements_test.txt"
CASES = 33
GROUP = "preproc_conditional_move_elements"
HOSTS = frozenset({"moveafter_modification", "movebefore_modification",
                   "movefirst_modification", "movelast_modification"})
ALLOWED_CLASSES = ("invalid-config:",)


def _cases():
    return [c for c in fixtures.extract(REPO / "test" / "corpus") if c.file == FIXTURE]


def _move(args, kw=b"moveafter", section=b"actions"):
    return (b"pageextension 50113 PE extends PG\n{\n    " + section + b"\n    {\n        " + kw + b"(" + args
            + b")\n    }\n}\n")


# --- layer 1: the focused fixture ---------------------------------------------------------------

def test_fixture_has_the_task_8_cases():
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
    lowered, hosts = 0, set()
    for case in _cases():
        root, _, _ = ir.from_tree(al_parser.parse(case.source))
        kinds = {n.kind: p for n, p in _walk(root) if n.kind == GROUP}
        if not kinds:
            continue
        assert "pass" in [r.status for r in runner.check_input(al_parser, case.id, case.source)], case.name
        lowered += 1
        hosts |= {p.kind for n, p in _walk(root) if n.kind == GROUP and p.kind in HOSTS}
    assert lowered >= 24, lowered
    assert hosts == HOSTS, hosts          # every move* host carries a lowered group


@pytest.mark.parametrize("case", _cases(), ids=lambda c: c.name)
def test_validate_split_is_clean_on_the_fixture(al_parser, case):
    assert cl.validate_split(_tree(al_parser, case.source)) == []


# --- registry ------------------------------------------------------------------------------------

def test_family_schema():
    fam = cl.FAMILIES["move_elements"]
    assert fam.group == GROUP
    assert fam.host_kinds == HOSTS
    assert fam.item_kinds == frozenset({"identifier", "quoted_identifier"})
    assert (fam.sep, fam.item_field, fam.cardinality) == (",", "element", "empty-semantic-rejected")
    assert contracts.REGISTRY[GROUP].hosts == {**{f"{h}:<children>": "strict-list" for h in HOSTS},
                                               f"{GROUP}:<children>": "strict-list"}


SEP_BEFORE = _move(b"A1; A2\n#if X\n, A3\n#endif\n, A4")
NESTED_ELSE = _move(b"A1; A2\n#if X\n, A3\n#if Y\n, A4\n#endif\n#else\n, A5\n#endif\n")
ELSE_SEPS = _move(b"A1; A2\n#if X\n, A3\n#else\n, A4\n#endif\n")


def test_region_is_between_the_fixed_separator_and_the_close():
    """The target and the fixed `;` lie before the region, `)` after it."""
    from tools.config_oracle.ir import Node
    kids = [Node("moveafter_keyword", True, None, 0, 9, []), Node("(", False, None, 9, 10, []),
            Node("identifier", True, "target", 10, 12, []), Node(";", False, None, 12, 13, []),
            Node("identifier", True, "element", 14, 16, []), Node(")", False, None, 16, 17, [])]
    host = Node("moveafter_modification", True, None, 0, 17, kids)
    assert cl.FAMILIES["move_elements"].region(host) == (13, 16)


def test_region_without_the_fixed_separator_is_refused():
    from tools.config_oracle.ir import Node
    from tools.config_oracle.lowering.engine import LoweringError
    host = Node("moveafter_modification", True, None, 0, 13, [
        Node("moveafter_keyword", True, None, 0, 9, []), Node("(", False, None, 9, 10, []),
        Node("identifier", True, "target", 10, 12, []), Node(")", False, None, 12, 13, [])])
    with pytest.raises(LoweringError):
        cl.FAMILIES["move_elements"].region(host)


# --- layer 2: validate_split mutations -------------------------------------------------------------

def test_mutation_attachment_group_in_the_target_slot(al_parser):
    """The brief's attachment test, first variant: a group inserted just before the target (the
    target stays in place), so the group lies before the fixed `;`, outside the region."""
    root = _tree(al_parser, SEP_BEFORE)
    g, host = _find(root, GROUP)
    target = next(c for c in host.children if c.field == "target")
    host.children.remove(g)
    host.children.insert(host.children.index(target), g)
    g.start, g.end = target.start - 1, target.start
    assert any("outside the list region" in p for p in _problems(root))


def test_mutation_attachment_group_replacing_the_target(al_parser):
    """Second variant: the target node is removed and the group takes its slot and span (a group
    supplying the target, B7b-3 territory). validate_split rejects it, so every configuration of
    the input is a representation-violation."""
    root = _tree(al_parser, SEP_BEFORE)
    g, host = _find(root, GROUP)
    target = next(c for c in host.children if c.field == "target")
    host.children.remove(g)
    at = host.children.index(target)
    host.children[at] = g
    g.start, g.end = target.start, target.end
    assert not any(c.field == "target" for c in host.children)
    assert any("outside the list region" in p for p in _problems(root))
    assert runner_status_of_mutated(al_parser, SEP_BEFORE, root) == "representation-violation"


def test_mutation_attachment_group_reaching_over_the_fixed_separator(al_parser):
    root = _tree(al_parser, SEP_BEFORE)
    g, host = _find(root, GROUP)
    g.start = next(c for c in host.children if c.kind == ";").start
    assert any("outside the list region" in p for p in _problems(root))


def test_mutation_group_with_a_field(al_parser):
    root = _tree(al_parser, SEP_BEFORE)
    g, _ = _find(root, GROUP)
    g.field = "element"
    assert any("fielded" in p for p in _problems(root))


@pytest.mark.parametrize("field", [None, "target", "interface"])
def test_mutation_arm_item_with_the_wrong_field(al_parser, field):
    """Items are `element:` inside an arm too: none, the target's or another family's field is not one."""
    root = _tree(al_parser, SEP_BEFORE)
    g, _ = _find(root, GROUP)
    item = next(c for c in g.children if c.kind == "identifier")
    assert item.field == "element"
    item.field = field
    assert any("arm content" in p for p in _problems(root))


def test_mutation_group_in_a_parent_that_is_not_its_slot(al_parser):
    root = _tree(al_parser, SEP_BEFORE)
    g, host = _find(root, GROUP)
    body, _ = _find(root, "action_body")
    host.children.remove(g)
    body.children.insert(body.children.index(host) + 1, g)
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


def test_mutation_neighbouring_move_region(al_parser):
    """Two move* hosts side by side: a group moved into the other host's list is outside its region."""
    src = (b"pageextension 50113 PE extends PG\n{\n    actions\n    {\n        moveafter(A1; A2\n#if X\n, A3\n#endif\n)\n"
           b"        movebefore(A4; A5\n#if X\n, A6\n#endif\n)\n    }\n}\n")
    root = _tree(al_parser, src)
    _, first = _find(root, GROUP, 0)
    g2, second = _find(root, GROUP, 1)
    assert (first.kind, second.kind) == ("moveafter_modification", "movebefore_modification")
    second.children.remove(g2)
    first.children.insert(len(first.children) - 1, g2)
    assert any("outside the list region" in p for p in _problems(root))


def test_mutation_neighbouring_region_in_an_enclosing_conditional(al_parser):
    """Inside an enclosing preproc_conditional_actions arm: the nested move's own group, moved
    into the enclosing conditional (not a permitted parent), is caught."""
    src = (b"pageextension 50113 PE extends PG\n{\n    actions\n    {\n#if TPL\n        moveafter(A1; A2\n#if X\n, A3\n"
           b"#endif\n)\n#endif\n    }\n}\n")
    root = _tree(al_parser, src)
    g, host = _find(root, GROUP)
    outer, _ = _find(root, "preproc_conditional_actions")
    host.children.remove(g)
    outer.children.insert(outer.children.index(host) + 1, g)
    assert any("not a permitted parent" in p for p in _problems(root))


# --- layer 3: lowering mutations and the empty policy ---------------------------------------------

def test_mutation_wrong_separator_count(al_parser, monkeypatch):
    from tools.config_oracle.lowering import select
    real = select._splice_arm
    monkeypatch.setattr(select, "_splice_arm", lambda items: [c for c in real(items) if c.kind != ","])
    assert witness.statuses_with(al_parser, SEP_BEFORE, "lowering:list-separator") == ["X=1"]


def test_mutation_swapped_order_in_the_lowered_arm(al_parser, monkeypatch):
    from tools.config_oracle.lowering import select
    src = _move(b"A1;\n#if X\nA2 , A3\n#else\nA2\n#endif\n")
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
    src = _move(b"A1; A2 ,\n#if X\n#endif\nA3")
    root = _tree(al_parser, src)
    g, host = _find(root, GROUP)
    host.children.remove(g)
    assert runner_status_of_mutated(al_parser, src, root) == "directive-mismatch"


@pytest.mark.parametrize("kw", [b"moveafter", b"movebefore", b"movefirst", b"movelast"])
def test_emptied_element_list_is_a_reference_error(al_parser, kw):
    """alc rejects `moveafter(A1; )` (AL0319, manifest empty-semantic-rejected) and the flat
    grammar requires an element, so the emptied configuration never reaches lowering."""
    v = witness.verdicts(al_parser, _move(b"A1;\n#if X\nA2 , A3\n#endif\n", kw=kw))
    assert v["X=0"][0] == "cannot-validate" and v["X=0"][1][0].startswith("reference-error:"), v
    assert v["X=1"] == ("pass", []), v


def test_alternation_is_not_the_list_run_validator(al_parser, monkeypatch):
    from tools.config_oracle.lowering import engine

    def boom(new):
        raise AssertionError("strict list checked by _check_alternation")
    monkeypatch.setattr(engine, "_check_alternation", boom)
    witness.assert_all_pass(al_parser, SEP_BEFORE)
