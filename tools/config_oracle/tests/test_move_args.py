"""B7b-3 Task 9: the move-interior adapter (lowering/move_args.py, spec 2026-10-08 section 6.3).

Layers:
  * the focused fixture `b7b3_move_args_test.txt` LOWERED: a repair case passes in every
    configuration, a MIXED case in every configuration alc accepts (the rest are classified
    invalid-config / negative in fixture-classes.tsv, reference-errors all);
  * route identification and the pre-selection checks (`check_host` / `validate_split`, carried by
    representation.check, so a problem is a representation-violation in every configuration);
  * the post-selection shape `name ; name (, name)*` and role assignment, on constructed nodes;
  * the section 6.3 mutation list, each a defect the oracle or the adapter must catch.
Route 1 (B7b-1's `T ; E (, E)*`) is pinned unchanged by test_conditional_lists_move.py.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tools.config_oracle import fixtures, ir, representation, runner
from tools.config_oracle.ir import Node
from tools.config_oracle.lowering import move_args
from tools.config_oracle.lowering.engine import LoweringError
from tools.config_oracle.tests import witness
from tools.config_oracle.tests.test_conditional_lists import _find, _tree, _walk, runner_status_of_mutated

REPO = Path(__file__).resolve().parents[3]
FIXTURE = "b7b3_move_args_test.txt"
GROUP = move_args.GROUP


def _cases():
    return [c for c in fixtures.extract(REPO / "test" / "corpus") if c.file == FIXTURE]


def _move(args, kw=b"moveafter"):
    return b"pageextension 50113 PE extends PG\n{\n    actions\n    {\n        " + kw + b"(" + args + b")\n    }\n}\n"


ROUTE1 = _move(b"T; A\n#if X\n, B\n#endif\n")
ROUTE2 = _move(b"T\n#if X\n; A\n#else\n; B\n#endif\n, C")
ROUTE3 = _move(b"\n#if X\nT; A\n#else\nU; A\n#endif\n, B")
CROSS = next(c.source for c in _cases() if "(cross-group-roles)" in c.name) if _cases() else b""
NESTED = _move(b"T\n#if X\n; A\n#if Y\n, B\n#endif\n#else\n; C\n#endif\n")


def _problems(root):
    out = move_args.validate_split(root)
    rep = [d for d in representation.check(root) if d.kind == "move-header"]
    assert len(rep) == len(out), (out, rep)    # representation.check carries every one
    return out


# --- layer 1: the focused fixture ---------------------------------------------------------------

def test_fixture_has_the_task_8_cases():
    assert len(_cases()) == 25


@pytest.mark.parametrize("case", _cases(), ids=lambda c: c.name)
def test_fixture_case_lowers_where_alc_accepts(al_parser, case):
    records = runner.check_input(al_parser, case.id, case.source)
    classes = fixtures.load_classes(REPO / "tools" / "config_oracle" / "fixture-classes.tsv")
    mine = {k: v for k, v in classes.items() if k[0] == case.id}
    expanded, stale = runner.expand_classes(mine, {case.id: [r.config for r in records]})
    assert not stale, stale
    for r in records:
        if r.status == "pass":
            continue
        entry = expanded.get((r.input_id, r.config))
        assert entry is not None and entry[1].startswith(("invalid-config:", "negative:")), (r.config, r.items)
        assert r.items and all(i.startswith("reference-error:") for i in r.items), (r.config, r.items)


@pytest.mark.parametrize("case", [c for c in _cases() if " MIXED" not in c.name and "OVERACCEPT" not in c.name],
                         ids=lambda c: c.name)
def test_repair_case_passes_in_every_configuration(al_parser, case):
    """Spec 6.4: a repair fixture passes in every configuration; no refusal is permitted."""
    witness.assert_all_pass(al_parser, case.source)


@pytest.mark.parametrize("case", _cases(), ids=lambda c: c.name)
def test_validate_split_is_clean_on_the_fixture(al_parser, case):
    assert move_args.validate_split(_tree(al_parser, case.source)) == []


def test_validate_split_is_clean_on_route_1(al_parser):
    for case in fixtures.extract(REPO / "test" / "corpus"):
        if case.file == "strict_conditional_move_elements_test.txt":
            assert move_args.validate_split(_tree(al_parser, case.source)) == [], case.name


def test_move_quoted_target_comment(al_parser):
    """Review Focus 5: a quoted target, then a block comment on its own line before the `;` in the
    arm. alc: X accepts, !X rejects (AL0104; tools/alc_probe/cases/b7b3/move/quoted-target-comment.al)."""
    src = _move(b'\n"A B"\n#if X\n/* c */ ;\n#endif\nC\n')
    v = witness.verdicts(al_parser, src)
    assert v["X=1"] == ("pass", []), v
    assert v["X=0"][0] == "cannot-validate" and v["X=0"][1][0].startswith("reference-error:"), v
    assert move_args.validate_split(_tree(al_parser, src)) == []


@pytest.mark.parametrize("args", [
    b"\n#if X\nT; A\n#else\nT;\n#endif\n",          # route 3
    b"T\n#if X\n; A\n#else\n;\n#endif\n",            # route 2
])
def test_empty_element_region_stays_a_reference_error(al_parser, args):
    """Flat `moveafter(T;)` is an ERROR (alc: AL0319, semantic), so the emptied configuration never
    reaches lowering; the other one lowers."""
    v = witness.verdicts(al_parser, _move(args))
    assert v["X=0"][0] == "cannot-validate" and v["X=0"][1][0].startswith("reference-error:"), v
    assert v["X=1"] == ("pass", []), v


@pytest.mark.parametrize("kw", [b"movefirst", b"movelast", b"moveafter", b"movebefore"])
@pytest.mark.parametrize("src", [ROUTE1, ROUTE2, ROUTE3, NESTED], ids=["r1", "r2", "r3", "nested"])
def test_every_host_and_route_passes(al_parser, kw, src):
    witness.assert_all_pass(al_parser, src.replace(b"moveafter", kw))


# --- route identification and the pre-selection checks -------------------------------------------

@pytest.mark.parametrize("src,want", [(ROUTE1, 1), (ROUTE2, 2), (ROUTE3, 3), (CROSS, 3), (NESTED, 2)])
def test_route(al_parser, src, want):
    body, _ = _find(_tree(al_parser, src), "action_body")
    assert move_args.route(body.children[0]) == want


def _host(*inner):
    kids = [Node("moveafter_keyword", True, None, 0, 9, []), Node("(", False, None, 9, 10, []), *inner,
            Node(")", False, None, 90, 91, [])]
    return Node("moveafter_modification", True, None, 0, 91, kids)


def _name(at, field=None, kind="identifier"):
    return Node(kind, True, field, at, at + 1, [])


def _tok(kind, at):
    return Node(kind, False, None, at, at + 1, [])


@pytest.mark.parametrize("inner", [[], [_name(10, "target")], [_name(10, "target"), _tok(",", 12), _name(14)],
                                   [_tok(";", 10), _name(12)]])
def test_route_refuses_an_interior_of_no_route(inner):
    with pytest.raises(LoweringError):
        move_args.route(_host(*inner))
    assert move_args.check_host(_host(*inner))


def test_host_without_parentheses_is_refused():
    host = _host(_name(10, "target"), _tok(";", 12), _name(14, "element"))
    host.children.pop(1)
    assert any("keyword ( ... )" in p for p in move_args.check_host(host))


def test_mutation_route_2_target_unfielded(al_parser):
    root = _tree(al_parser, ROUTE2)
    _, host = _find(root, GROUP)
    next(c for c in host.children if c.field == "target").field = None
    assert any("not target" in p for p in _problems(root))
    assert runner_status_of_mutated(al_parser, ROUTE2, root) == "representation-violation"


@pytest.mark.parametrize("field", ["target", "element", "interface"])
def test_mutation_group_name_fielded(al_parser, field):
    """Spec 5.2: every name in a move_args group is unfielded; a field there is refused, not corrected."""
    root = _tree(al_parser, ROUTE2)
    g, _ = _find(root, GROUP)
    next(c for c in g.children if c.kind == "identifier").field = field
    assert any("arm content" in p for p in _problems(root))
    assert runner_status_of_mutated(al_parser, ROUTE2, root) == "representation-violation"


@pytest.mark.parametrize("field", ["target", "element"])
def test_mutation_route_3_or_tail_name_fielded(al_parser, field):
    root = _tree(al_parser, ROUTE3)
    _, host = _find(root, GROUP)
    tail = [c for c in host.children if c.kind == "identifier"][-1]
    tail.field = field
    assert any("does not allow" in p for p in _problems(root))


def test_mutation_group_fielded(al_parser):
    root = _tree(al_parser, ROUTE2)
    g, _ = _find(root, GROUP)
    g.field = "element"
    assert any("fielded" in p for p in _problems(root))


def test_mutation_route_1_holding_a_move_args_group(al_parser):
    root = _tree(al_parser, ROUTE1)
    g, host = _find(root, "preproc_conditional_move_elements")
    g.kind = GROUP
    assert any("route 1 does not allow" in p for p in _problems(root))


def test_mutation_route_2_holding_a_move_elements_group(al_parser):
    root = _tree(al_parser, _move(b"T\n#if X\n; A\n#endif\n#if Y\n, B\n#endif\n"))
    g, _ = _find(root, GROUP, 1)
    g.kind = "preproc_conditional_move_elements"
    assert any("route 2 does not allow" in p for p in _problems(root))


def test_mutation_swapped_order(al_parser):
    root = _tree(al_parser, ROUTE2)
    g, host = _find(root, GROUP)
    i = host.children.index(g)
    host.children[i], host.children[i + 1] = host.children[i + 1], host.children[i]
    assert any("source order" in p for p in _problems(root))


def test_mutation_separator_moved_to_the_other_arm(al_parser):
    root = _tree(al_parser, ROUTE2)
    g, _ = _find(root, GROUP)
    semi = next(c for c in g.children if c.kind == ";")
    g.children.remove(semi)
    g.children.insert(next(i for i, c in enumerate(g.children) if c.kind == "preproc_else") + 1, semi)
    assert any("outside its arm" in p or "source order" in p for p in _problems(root))
    assert runner_status_of_mutated(al_parser, ROUTE2, root) == "representation-violation"


def test_mutation_nesting_in_the_wrong_arm(al_parser):
    """Arm containment: the nested group moved (by position) to the #else arm keeps its #if-arm span."""
    root = _tree(al_parser, NESTED)
    outer, _ = _find(root, GROUP, 0)
    inner, parent = _find(root, GROUP, 1)
    assert parent is outer
    outer.children.remove(inner)
    outer.children.insert(next(i for i, c in enumerate(outer.children) if c.kind == "preproc_else") + 1, inner)
    assert any("outside its arm" in p for p in _problems(root))


def test_mutation_group_in_a_parent_that_is_not_its_slot(al_parser):
    """Wrong ownership: the group re-parented into the enclosing action_body."""
    root = _tree(al_parser, ROUTE2)
    g, host = _find(root, GROUP)
    body, _ = _find(root, "action_body")
    host.children.remove(g)
    body.children.insert(body.children.index(host) + 1, g)
    assert any("not a permitted parent" in p for p in _problems(root))


def test_mutation_group_moved_into_the_neighbouring_host(al_parser):
    src = (b"pageextension 50113 PE extends PG\n{\n    actions\n    {\n        moveafter(T\n#if X\n; A\n#endif\n)\n"
           b"        movebefore(U\n#if X\n; B\n#endif\n)\n    }\n}\n")
    root = _tree(al_parser, src)
    _, first = _find(root, GROUP, 0)
    g2, second = _find(root, GROUP, 1)
    second.children.remove(g2)
    first.children.insert(len(first.children) - 1, g2)
    assert any("outside its parent" in p or "source order" in p for p in _problems(root))
    assert runner_status_of_mutated(al_parser, src, root) == "representation-violation"


def test_mutation_group_only_host_with_a_bad_group_is_refused(al_parser):
    """A route-3 host holds only a move_args group: the adapter still validates it (dispatch by kind)."""
    root = _tree(al_parser, ROUTE3)
    g, _ = _find(root, GROUP)
    g.children.pop()                  # no #endif
    assert any("not an #if ... #endif group" in p for p in _problems(root))


# --- post-selection: shape, fields, roles ----------------------------------------------------------

def _run(seq):
    """`seq`: names as 'T'/'A' (unfielded), seps as ';' / ','. -> (host, kids) for lower()."""
    inner, at = [], 10
    for s in seq:
        inner.append(_tok(s, at) if s in ";," else _name(at))
        at += 2
    return inner


@pytest.mark.parametrize("seq", ["T;A", "T;A,B", "T;A,B,C"])
def test_shape_accepts(seq):
    move_args.check_shape(_host(), _run(seq))


@pytest.mark.parametrize("seq,why", [
    ("T,U;A", "follow exactly one target"),     # an extra target
    ("T;A;B", "second `;`"),                    # a duplicate `;`
    ("T,A", "follow exactly one target"),       # a missing `;`
    ("T", "follow exactly one target"),
    ("T;", "ends with a separator"),            # the empty element region
    ("T;A,", "ends with a separator"),
    ("T;,A", "alternate"),                      # bad commas
    ("T;A,,B", "alternate"),
    (";A", "alternate"),
    ("", "alternate"),
])
def test_shape_refuses_never_repairs(seq, why):
    with pytest.raises(LoweringError) as e:
        move_args.check_shape(_host(), _run(seq))
    assert e.value.kind == "list-separator" and why in e.value.detail


def _route3_host():
    g = Node(GROUP, True, None, 10, 80, [Node("preproc_if", True, None, 10, 15, []),
                                         Node("preproc_endif", True, None, 70, 80, [])])
    return _host(g)


def test_roles_are_assigned_only_after_validation(monkeypatch):
    calls = []
    monkeypatch.setattr(move_args, "roles", lambda names: calls.append(names) or ["target"] * len(names))
    host = _route3_host()
    bad = [host.children[0], host.children[1], *_run("T;A;B"), host.children[-1]]
    with pytest.raises(LoweringError):
        move_args.lower(host, bad, None)
    assert calls == []


def test_roles_assigned_on_route_3():
    host = _route3_host()
    kids = [host.children[0], host.children[1], *_run("T;A,B"), host.children[-1]]
    out = move_args.lower(host, kids, None)
    assert [c.field for c in out if c.kind == "identifier"] == ["target", "element", "element"]
    assert [c.field for c in kids if c.kind == "identifier"] == [None, None, None]   # copies, not in place


def test_route_1_children_come_back_as_they_stand(al_parser):
    """Route 1 is B7b-1's: its fields are checked, never relabelled, and nothing else changes."""
    root = _tree(al_parser, ROUTE1)
    _, host = _find(root, "preproc_conditional_move_elements")
    kids = [c for c in host.children if c.kind != "preproc_conditional_move_elements"]
    out = move_args.lower(host, kids, None)
    assert [(c.kind, c.field, c.start) for c in out] == [(c.kind, c.field, c.start) for c in kids]


@pytest.mark.parametrize("r,fields", [(1, ["target", None]), (2, ["target", "element"]), (3, ["target", None])])
def test_wrong_field_as_it_stands_is_refused_not_corrected(r, fields):
    names = [_name(10 + 2 * i, f) for i, f in enumerate(fields)]
    with pytest.raises(LoweringError) as e:
        move_args.check_fields(None, r, names)
    assert e.value.kind == "field-policy"


# --- the section 6.3 mutation list ---------------------------------------------------------------
# 1 "a second target silently turned into an element" and 2 "a duplicate `;` ignored" are
#   test_shape_refuses_never_repairs (T,U;A and T;A;B); their flat texts are ERRORs, so no run reaches them.
# 6 "wrong group ownership or arm containment": the tree mutations above (parent, neighbour host,
#   wrong arm, separator in the other arm).

def test_mutation_3_wrong_field_silently_corrected(al_parser, monkeypatch):
    """A lowering defect that pre-labels a spliced name: refused (field-policy), never relabelled."""
    from tools.config_oracle.lowering import select
    real = select._splice_arm
    monkeypatch.setattr(select, "_splice_arm",
                        lambda items: [c.copy(field="element") if c.kind == "identifier" else c for c in real(items)])
    assert witness.statuses_with(al_parser, ROUTE2, "lowering:field-policy") == ["X=0", "X=1"]


def test_mutation_4_group_only_host_bypassing_validation(al_parser, monkeypatch):
    """Dispatch on group presence (the B7b-1 HOST_FAMILY rule) instead of host kind: a route-3 host
    holding only move_args groups then gets no role assignment, which the comparison catches."""
    monkeypatch.setattr(move_args, "dispatches",
                        lambda n: n.kind in move_args.MOVE_HOSTS
                        and any(c.kind == "preproc_conditional_move_elements" for c in n.children))
    v = witness.verdicts(al_parser, ROUTE3)
    assert all(s == "discrepancy" for s, _ in v.values()), v


def test_group_only_host_goes_through_the_adapter(al_parser, monkeypatch):
    seen = []
    real = move_args.lower
    monkeypatch.setattr(move_args, "lower", lambda node, kids, ctx: seen.append(node.kind) or real(node, kids, ctx))
    witness.assert_all_pass(al_parser, ROUTE3)
    assert seen == ["moveafter_modification"] * 2


def test_mutation_5_old_direct_semicolon_region(al_parser, monkeypatch):
    """The B7b-1 move_elements region (between a DIRECT `;` and `)`) applied to a `;`-bearing group."""
    from tools.config_oracle.lowering import conditional_lists as cl
    monkeypatch.setattr(move_args, "lower",
                        lambda node, kids, ctx: cl.lower_region(node, kids, cl.FAMILIES["move_elements"]))
    assert witness.statuses_with(al_parser, ROUTE2, "lowering:contract-shape") == ["X=0", "X=1"]


def test_mutation_7_reordered_leaves(al_parser, monkeypatch):
    from tools.config_oracle.lowering import select
    real = select._splice_arm
    monkeypatch.setattr(select, "_splice_arm", lambda items: list(reversed(real(items))))
    v = witness.verdicts(al_parser, _move(b"T\n#if X\n; A, B\n#else\n; C\n#endif\n"))
    assert v["X=1"][0] != "pass", v


def test_mutation_7_lost_leaves(al_parser, monkeypatch):
    from tools.config_oracle.lowering import select
    real = select._splice_arm
    monkeypatch.setattr(select, "_splice_arm", lambda items: [c for c in real(items) if c.kind != ";"])
    v = witness.verdicts(al_parser, ROUTE3)
    assert v["X=0"][0] != "pass" and v["X=1"][0] != "pass", v


def test_mutation_8_configuration_dependent_role(al_parser, monkeypatch):
    """Spec 5.3: a static role (a name inside a group is an element) is wrong in the configuration
    where that name is the target."""
    root = _tree(al_parser, CROSS)
    spans = [(n.start, n.end) for n, _ in _walk(root) if n.kind == GROUP and n.children[0].kind == "preproc_if"]
    second = spans[1]
    monkeypatch.setattr(move_args, "roles", lambda names: [
        "element" if second[0] <= n.start < second[1] else ("target" if i == 0 else "element")
        for i, n in enumerate(names)])
    v = witness.verdicts(al_parser, CROSS)
    assert {c for c, (s, _) in v.items() if s != "pass"} == {"X=0,Y=0", "X=0,Y=1"}, v
