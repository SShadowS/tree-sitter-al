"""B7b-1 Task 6: the field_list_items family (key, fieldgroup, addlast/addfirst, split key
field lists) in the strict conditional list registry (spec 2026-10-07 section 6).

field_list is a visible host that owns nothing but the list, and its items are UNFIELDED
(item_field None), unlike implements. The layers mirror test_conditional_lists.py:
the focused fixture LOWERED in every configuration (bar the alc-rejected MIXED
configurations and C1's preproc_split_key), validate_split mutations, lowering mutations,
and the empty policy on the two route kinds (addlast optional, key required).
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
FIXTURE = "strict_conditional_field_list_items_test.txt"
GROUP = "preproc_conditional_field_list_items"
ALLOWED_CLASSES = ("invalid-config:", "debt(C1):")


def _cases():
    return [c for c in fixtures.extract(REPO / "test" / "corpus") if c.file == FIXTURE]


# --- layer 1: the focused fixture -------------------------------------------------------------

def test_fixture_has_the_task_6_cases():
    assert len(_cases()) == 48      # 47 of Task 6 + the fieldgroup-header trail over-accept witness (Task 13)


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
    """Every group case on a lowered host that alc accepts in every configuration."""
    return [c for c in _cases() if " MIXED" not in c.name and "split key" not in c.name
            and "preservation" not in c.name]


@pytest.mark.parametrize("case", _placement_cases(), ids=lambda c: c.name)
def test_placement_case_passes_in_every_configuration(al_parser, case):
    """Spec section 6, tests: the family is LOWERED, not classified away. Each placement on
    key, fieldgroup, addlast (and the addfirst witness, whose flat text parses too) passes
    in ALL its configurations."""
    statuses = {r.config: (r.status, r.items) for r in runner.check_input(al_parser, case.id, case.source)}
    assert all(s == "pass" for s, _ in statuses.values()), statuses


def test_enough_lowered_group_cases(al_parser):
    lowered = 0
    for case in _cases():
        root, _, _ = ir.from_tree(al_parser.parse(case.source))
        kinds = {n.kind for n, _ in _walk(root)}
        if GROUP not in kinds or "preproc_split_key" in kinds:
            continue
        assert "pass" in [r.status for r in runner.check_input(al_parser, case.id, case.source)], case.name
        lowered += 1
    assert lowered >= 38, lowered


@pytest.mark.parametrize("case", _cases(), ids=lambda c: c.name)
def test_validate_split_is_clean_on_the_fixture(al_parser, case):
    assert cl.validate_split(_tree(al_parser, case.source)) == []


# --- registry ------------------------------------------------------------------------------------

def test_field_list_family_schema():
    fam = cl.FAMILIES["field_list_items"]
    assert fam.group == GROUP
    assert fam.host_kinds == frozenset({"field_list"})
    assert fam.item_kinds == frozenset({"identifier", "quoted_identifier"})
    assert (fam.sep, fam.item_field, fam.cardinality) == (",", None, "empty-semantic-rejected")
    assert contracts.REGISTRY[GROUP].hosts == {"field_list:<children>": "strict-list",
                                               f"{GROUP}:<children>": "strict-list"}


# --- layer 2: validate_split mutations -------------------------------------------------------------

def _key(lst, name=b"PK"):
    return b"table 50100 T\n{\n    keys\n    {\n        key(" + name + b";\n" + lst + b"\n) { }\n    }\n}\n"


SEP_BEFORE = _key(b"K\n#if X\n, N\n#endif\n, B")
NESTED_ELSE = _key(b"K\n#if X\n, N\n#if Y\n, B\n#endif\n#else\n, O\n#endif\n")
ELSE_SEPS = _key(b"K\n#if X\n, N\n#else\n, B\n#endif\n")
TWO_KEYS = (b"table 50100 T\n{\n    keys\n    {\n        key(PK; K\n#if X\n, N\n#endif\n) { }\n"
            b"        key(SK; B\n#if X\n, O\n#endif\n) { }\n    }\n}\n")


def test_mutation_attachment_group_moved_outside_the_region(al_parser):
    root = _tree(al_parser, SEP_BEFORE)
    g, host = _find(root, GROUP)
    g.start = host.start - 3            # the group now takes in the `; ` before the list
    assert any("outside the list region" in p for p in _problems(root))


def test_mutation_group_with_a_field(al_parser):
    root = _tree(al_parser, SEP_BEFORE)
    g, _ = _find(root, GROUP)
    g.field = "fields"
    assert any("fielded" in p for p in _problems(root))


def test_mutation_arm_item_with_a_field(al_parser):
    """The family is unfielded: an arm item carrying a field is not one of its items."""
    root = _tree(al_parser, SEP_BEFORE)
    g, _ = _find(root, GROUP)
    item = next(c for c in g.children if c.kind == "identifier")
    item.field = "fields"
    assert any("arm content" in p for p in _problems(root))


def test_mutation_group_in_a_parent_that_is_not_its_slot(al_parser):
    root = _tree(al_parser, SEP_BEFORE)
    g, host = _find(root, GROUP)
    decl, _ = _find(root, "key_declaration")
    host.children.remove(g)
    decl.children.insert(decl.children.index(host) + 1, g)
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


def test_mutation_neighbouring_same_family_region(al_parser):
    root = _tree(al_parser, TWO_KEYS)
    _, first = _find(root, GROUP, 0)
    g2, second = _find(root, GROUP, 1)
    assert first is not second
    second.children.remove(g2)
    first.children.append(g2)
    assert any("outside the list region" in p for p in _problems(root))


# --- layer 3: lowering mutations and the empty policy ---------------------------------------------

def test_mutation_wrong_separator_count(al_parser, monkeypatch):
    from tools.config_oracle.lowering import select
    real = select._splice_arm
    monkeypatch.setattr(select, "_splice_arm", lambda items: [c for c in real(items) if c.kind != ","])
    assert witness.statuses_with(al_parser, SEP_BEFORE, "lowering:list-separator") == ["X=1"]


def test_mutation_swapped_order_in_the_lowered_arm(al_parser, monkeypatch):
    from tools.config_oracle.lowering import select
    src = _key(b"#if X\nK , N\n#else\nK\n#endif\n")
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
    """An empty group's directives must stay accounted for: removing the group from the
    multi-configuration tree is caught (its directive lines no longer have a node)."""
    src = _key(b"K ,\n#if X\n#endif\nN")
    root = _tree(al_parser, src)
    g, host = _find(root, GROUP)
    host.children.remove(g)
    assert runner_status_of_mutated(al_parser, src, root) == "directive-mismatch"


ADDLAST_EMPTY = (b"tableextension 50110 TE extends T\n{\n    fieldgroups\n    {\n"
                 b"        addlast(DropDown;\n#if X\nN , B\n#endif\n) { }\n    }\n}\n")


def test_emptied_addlast_list_removes_field_list(al_parser):
    """addlast's field list is optional (alc accepts `addlast(DropDown; )`): the emptied
    configuration lowers by removing field_list and agrees with the flat parse."""
    v = witness.verdicts(al_parser, ADDLAST_EMPTY)
    assert v["X=1"] == ("pass", []), v
    status, items = v["X=0"]
    assert status == "pass", items
    assert [i.split("@")[0] for i in items] == ["normalised:optional-list-removed:field_list"], items


def test_emptied_key_list_stays_reference_error(al_parser):
    """`key(PK; )` does not parse flat (AL0306 empty key, a semantic reject): reference-error."""
    v = witness.verdicts(al_parser, _key(b"\n#if X\nK , N\n#endif\n"))
    assert v["X=0"][0] == "cannot-validate" and v["X=0"][1][0].startswith("reference-error:"), v
    assert v["X=1"] == ("pass", []), v


def test_alternation_is_not_the_list_run_validator(al_parser, monkeypatch):
    from tools.config_oracle.lowering import engine

    def boom(new):
        raise AssertionError("strict list checked by _check_alternation")
    monkeypatch.setattr(engine, "_check_alternation", boom)
    witness.assert_all_pass(al_parser, SEP_BEFORE)
