"""B7b-1 Task 11: the var_names family (the name list of a variable declaration `A, B: T;`) in
the strict conditional list registry (spec 2026-10-07 section 6).

The host variable_declaration owns more than the list: the `:`, the `type`, a label's value and
attributes, a TextConst's ml_value_list and the `;`. The region is everything before the host's
first `:` (conditional_lists.before_child). Items are fielded `name`. Layers as
test_conditional_lists_array.py: the focused fixture LOWERED in every configuration (bar the
alc-rejected MIXED ones), validate_split mutations, lowering mutations, and the empty policy (alc
rejects an empty name list as syntax, AL0104/AL0198, and the flat grammar requires a name, so an
emptied configuration is a reference-error).
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
FIXTURE = "strict_conditional_var_names_test.txt"
CASES = 47
GROUP = "preproc_conditional_var_names"
HOST = "variable_declaration"
ALLOWED_CLASSES = ("invalid-config:",)


def _cases():
    return [c for c in fixtures.extract(REPO / "test" / "corpus") if c.file == FIXTURE]


def _var(decls):
    return b"codeunit 50100 C\n{\n    var\n" + decls + b"}\n"


# --- layer 1: the focused fixture ---------------------------------------------------------------

def test_fixture_has_the_task_11_cases():
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
    assert lowered >= 36, lowered


@pytest.mark.parametrize("case", _cases(), ids=lambda c: c.name)
def test_validate_split_is_clean_on_the_fixture(al_parser, case):
    assert cl.validate_split(_tree(al_parser, case.source)) == []


def test_only_comma_conditional(al_parser):
    """Review Focus 1: a declaration whose only comma is conditional is ONE variable_declaration
    holding both names (B inside the group) and passes in both configurations."""
    src = _var(b"        A\n#if X\n        , B\n#endif\n        : Integer;\n")
    root = _tree(al_parser, src)
    decls = [n for n, _ in _walk(root) if n.kind == HOST]
    assert len(decls) == 1
    g, host = _find(root, GROUP)
    assert host is decls[0]
    assert [c.kind for c in host.children if c.field == "name"] == ["identifier"]
    assert [c.kind for c in g.children if c.field == "name"] == ["identifier"]
    witness.assert_all_pass(al_parser, src)


def test_empty_group_before_a_declaration_stays_a_sibling(al_parser):
    """The two-reading input (grammar.js var_names conflicts): an empty group directly before a
    declaration in a var_body is a preproc_conditional_var beside it, not a name group in it."""
    root = _tree(al_parser, _var(b"#if X\n#endif\n        A, B: Integer;\n"))
    assert not any(n.kind == GROUP for n, _ in _walk(root))
    pcv, parent = _find(root, "preproc_conditional_var")
    assert parent.kind == "var_body"
    assert [c.kind for c in parent.children] == ["preproc_conditional_var", HOST]


# --- registry ------------------------------------------------------------------------------------

def test_family_schema():
    fam = cl.FAMILIES["var_names"]
    assert fam.group == GROUP
    assert fam.host_kinds == frozenset({HOST})
    assert fam.item_kinds == frozenset({"identifier", "quoted_identifier"})
    assert (fam.sep, fam.item_field, fam.cardinality) == (",", "name", "empty-syntax-rejected")
    assert contracts.REGISTRY[GROUP].hosts == {f"{HOST}:<children>": "strict-list",
                                               f"{GROUP}:<children>": "strict-list"}


SEP_BEFORE = _var(b"        A\n#if X\n        , B\n#endif\n        , C: Integer;\n")
NESTED_ELSE = _var(b"        A\n#if X\n        , B\n#if Y\n        , C\n#endif\n#else\n        , D\n#endif\n        : Integer;\n")
ELSE_SEPS = _var(b"        A\n#if X\n        , B\n#else\n        , C\n#endif\n        : Integer;\n")


@pytest.mark.parametrize("decl", [b"A, B: Integer;", b"L: Label 'a', Locked = true;", b"T: TextConst ENU = 'a';",
                                  b"Q: array[2, 3] of Integer;"])
def test_region_is_before_the_colon(al_parser, decl):
    """Everything from the declaration's start to its first `:`; the type (an array type's own
    `,` too), a label's value and a TextConst's list lie after it."""
    root = _tree(al_parser, _var(b"        " + decl + b"\n"))
    host, _ = _find(root, HOST)
    colon = next(c for c in host.children if c.kind == ":")
    assert cl.FAMILIES["var_names"].region(host) == (host.start, colon.start)
    assert all(c.end <= colon.start for c in host.children if c.field == "name")


def test_region_without_colon_is_refused():
    from tools.config_oracle.ir import Node
    from tools.config_oracle.lowering.engine import LoweringError
    host = Node(HOST, True, None, 0, 9, [Node("identifier", True, "name", 0, 1, [])])
    with pytest.raises(LoweringError):
        cl.FAMILIES["var_names"].region(host)


# --- layer 2: validate_split mutations -------------------------------------------------------------

def test_mutation_attachment_group_after_the_colon(al_parser):
    """A group moved between `:` and the type lies outside the region."""
    root = _tree(al_parser, SEP_BEFORE)
    g, host = _find(root, GROUP)
    colon = next(c for c in host.children if c.kind == ":")
    host.children.remove(g)
    host.children.insert(host.children.index(colon) + 1, g)
    g.start, g.end = colon.end, colon.end + 1
    assert any("outside the list region" in p for p in _problems(root))
    assert runner_status_of_mutated(al_parser, SEP_BEFORE, root) == "representation-violation"


def test_mutation_attachment_group_in_the_type_slot(al_parser):
    root = _tree(al_parser, SEP_BEFORE)
    g, host = _find(root, GROUP)
    typ = next(c for c in host.children if c.field == "type")
    host.children.remove(g)
    host.children[host.children.index(typ)] = g
    g.start, g.end = typ.start, typ.end
    assert any("outside the list region" in p for p in _problems(root))


def test_mutation_attachment_group_reaching_over_the_colon(al_parser):
    root = _tree(al_parser, _var(b"        A\n#if X\n        , B\n#endif\n        : Integer;\n"))
    g, host = _find(root, GROUP)
    g.end = next(c for c in host.children if c.kind == ":").end
    assert any("outside the list region" in p for p in _problems(root))


def test_mutation_group_with_a_field(al_parser):
    root = _tree(al_parser, SEP_BEFORE)
    g, _ = _find(root, GROUP)
    g.field = "name"
    assert any("fielded" in p for p in _problems(root))


@pytest.mark.parametrize("field", [None, "type", "element"])
def test_mutation_arm_item_with_the_wrong_field(al_parser, field):
    """Names are `name:` inside an arm too: none, the type's or another family's field is not one."""
    root = _tree(al_parser, SEP_BEFORE)
    g, _ = _find(root, GROUP)
    item = next(c for c in g.children if c.kind == "identifier")
    assert item.field == "name"
    item.field = field
    assert any("arm content" in p for p in _problems(root))


def test_mutation_arm_item_of_a_foreign_kind(al_parser):
    root = _tree(al_parser, SEP_BEFORE)
    g, _ = _find(root, GROUP)
    item = next(c for c in g.children if c.kind == "identifier")
    item.kind = "integer"
    assert any("arm content" in p for p in _problems(root))


def test_mutation_group_in_a_parent_that_is_not_its_slot(al_parser):
    """Moved up into var_body, beside the declaration: not a permitted parent."""
    root = _tree(al_parser, SEP_BEFORE)
    g, host = _find(root, GROUP)
    body, _ = _find(root, "var_body")
    host.children.remove(g)
    body.children.append(g)
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


def test_mutation_neighbouring_declaration_region(al_parser):
    """Two declarations side by side: a group moved into the other declaration's names is outside its region."""
    src = _var(b"        A\n#if X\n        , B\n#endif\n        : Integer;\n"
               b"        C\n#if X\n        , D\n#endif\n        : Integer;\n")
    root = _tree(al_parser, src)
    _, first = _find(root, GROUP, 0)
    g2, second = _find(root, GROUP, 1)
    assert first is not second and first.kind == second.kind == HOST
    second.children.remove(g2)
    first.children.insert(next(i for i, c in enumerate(first.children) if c.kind == ";"), g2)
    assert any("outside the list region" in p for p in _problems(root))


def test_mutation_neighbouring_region_in_an_enclosing_conditional(al_parser):
    """Inside an enclosing preproc_conditional_var arm: the declaration's own group, moved into
    the enclosing conditional (not a permitted parent), is caught."""
    src = _var(b"        I: Integer;\n#if TPL\n        A\n#if X\n        , B\n#endif\n        : Integer;\n#endif\n")
    root = _tree(al_parser, src)
    g, host = _find(root, GROUP)
    outer, _ = _find(root, "preproc_conditional_var")
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
    src = _var(b"#if X\n        A , B\n#else\n        A\n#endif\n        : Integer;\n")
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
    src = _var(b"        A ,\n#if X\n#endif\n        B: Integer;\n")
    root = _tree(al_parser, src)
    g, host = _find(root, GROUP)
    host.children.remove(g)
    assert runner_status_of_mutated(al_parser, src, root) == "directive-mismatch"


def test_emptied_name_list_is_a_reference_error(al_parser):
    """alc rejects `: Integer;` with no name (AL0104/AL0198, manifest empty-syntax-rejected) and
    the flat grammar requires a name, so the emptied configuration never reaches lowering."""
    v = witness.verdicts(al_parser, _var(b"#if X\n        A , B\n#endif\n        : Integer;\n"))
    assert v["X=0"][0] == "cannot-validate" and v["X=0"][1][0].startswith("reference-error:"), v
    assert v["X=1"] == ("pass", []), v


def test_alternation_is_not_the_list_run_validator(al_parser, monkeypatch):
    from tools.config_oracle.lowering import engine

    def boom(new):
        raise AssertionError("strict list checked by _check_alternation")
    monkeypatch.setattr(engine, "_check_alternation", boom)
    witness.assert_all_pass(al_parser, SEP_BEFORE)
