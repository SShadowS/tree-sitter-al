"""B7b-1 family-schema registry for strict conditional lists (spec 2026-10-07 section 6).

Three layers, each with its own failure:
  * every configuration of every case of the focused fixture is LOWERED and agrees with
    its flat parse (status pass), except the configurations fixture-classes.tsv records
    as alc-rejected (invalid-config) or owned by C1 (preproc_split_declaration);
  * validate_split (section 6.1) on the multi-configuration tree: each mutation of a
    correct tree is a named problem, and representation.check reports it;
  * lower_region (sections 6.3, 6.4): the complete-region alternation and the empty policy,
    and lowering mutations that the comparison must catch.
"""
from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from tools.config_oracle import contracts, fixtures, ir, representation, runner
from tools.config_oracle.ir import Node
from tools.config_oracle.lowering import conditional_lists as cl
from tools.config_oracle.tests import witness

REPO = Path(__file__).resolve().parents[3]
FIXTURE = "strict_conditional_implements_test.txt"
GROUP = "preproc_conditional_implements"
# Classifications a fixture configuration may still carry once the family lowers: alc
# rejects it (MIXED shapes), or the enclosing preproc_split_declaration is C1's.
ALLOWED_CLASSES = ("invalid-config:", "debt(C1):")


def _cases():
    return [c for c in fixtures.extract(REPO / "test" / "corpus") if c.file == FIXTURE]


# --- layer 1: every configuration of the focused fixture -------------------------------

def test_fixture_has_the_task_4_cases():
    assert len(_cases()) == 28


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


def test_every_group_case_outside_a_split_declaration_passes_somewhere(al_parser):
    """The family is LOWERED, not classified away (spec section 6, tests): every case whose
    tree holds the group and no preproc_split_declaration has a passing configuration."""
    lowered = 0
    for case in _cases():
        root, _, problems = ir.from_tree(al_parser.parse(case.source))
        kinds = {n.kind for n, _ in _walk(root)}
        if GROUP not in kinds or "preproc_split_declaration" in kinds:
            continue
        statuses = [r.status for r in runner.check_input(al_parser, case.id, case.source)]
        assert "pass" in statuses, (case.name, statuses)
        lowered += 1
    assert lowered >= 20, lowered


# --- registry ----------------------------------------------------------------------------

def test_implements_family_schema():
    fam = cl.FAMILIES["implements"]
    assert fam.group == GROUP
    assert fam.host_kinds == frozenset({"implements_clause"})
    assert fam.item_kinds == frozenset({"identifier", "quoted_identifier"})
    assert (fam.sep, fam.item_field, fam.cardinality) == (",", "interface", "empty-syntax-rejected")


def test_contracts_entries_agree_with_the_families():
    for fam in cl.FAMILIES.values():
        e = contracts.REGISTRY[fam.group]
        assert e.kind == "branch-select" and e.handler == "tools.config_oracle.lowering.select.branch_select"
        want_hosts = {f"{h}:<children>" for h in fam.host_kinds} | {f"{fam.group}:<children>"}
        assert e.hosts == {h: "strict-list" for h in want_hosts}, fam.name
        assert e.arm == fam.item_kinds | {fam.sep, fam.group}, fam.name


def test_family_rejects_an_unknown_cardinality():
    with pytest.raises(ValueError):
        dataclasses.replace(cl.FAMILIES["implements"], cardinality="nonempty")


# --- layer 2: validate_split mutations ----------------------------------------------------

SEP_BEFORE = b"codeunit 50100 C implements IFoo\n#if X\n, IBar\n#endif\n, IBaz\n{\n}\n"
NESTED_ELSE = (b"codeunit 50100 C implements IFoo\n#if X\n, IBar\n#if Y\n, IBaz\n#endif\n"
               b"#else\n, IQux\n#endif\n{\n}\n")
TWO_HOSTS = (b"codeunit 50100 C implements IA\n#if X\n, IB\n#endif\n{\n}\n"
             b"codeunit 50101 D implements IC\n#if X\n, ID\n#endif\n{\n}\n")


def _walk(root):
    stack = [(root, None)]
    while stack:
        n, p = stack.pop()
        yield n, p
        stack.extend((c, n) for c in reversed(n.children))


def _tree(parser, src):
    root, _, problems = ir.from_tree(parser.parse(src))
    assert not problems, problems
    return root


def _find(root, kind, nth=0):
    found = [(n, p) for n, p in _walk(root) if n.kind == kind]
    return found[nth]


def _problems(root):
    out = cl.validate_split(root)
    rep = representation.check(root)
    # representation.check carries every validate_split problem, so the run reports it.
    assert len([d for d in rep if d.kind == "strict-list"]) == len(out), (out, rep)
    return out


@pytest.mark.parametrize("case", _cases(), ids=lambda c: c.name)
def test_validate_split_is_clean_on_the_fixture(al_parser, case):
    assert cl.validate_split(_tree(al_parser, case.source)) == []


def test_mutation_group_moved_outside_the_region(al_parser):
    root = _tree(al_parser, SEP_BEFORE)
    g, host = _find(root, GROUP)
    g.start = host.start                # the group's span now takes in implements_keyword
    assert any("outside the list region" in p for p in _problems(root))


def test_mutation_group_with_a_field(al_parser):
    root = _tree(al_parser, SEP_BEFORE)
    g, _ = _find(root, GROUP)
    g.field = "interface"
    assert any("fielded" in p for p in _problems(root))


def test_mutation_group_in_a_parent_that_is_not_its_slot(al_parser):
    root = _tree(al_parser, SEP_BEFORE)
    g, host = _find(root, GROUP)
    decl, _ = _find(root, "codeunit_declaration")
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
    outer.children.insert(at, inner)    # the #else arm, though its bytes are in the #if arm
    assert any("outside its arm" in p for p in _problems(root))


def test_mutation_wrong_outer_arm_ownership(al_parser):
    """The inner group re-parented to the host while its bytes stay inside the outer group's
    arm. Detected through the ORDER check: the host's children then overlap."""
    root = _tree(al_parser, NESTED_ELSE)
    outer, host = _find(root, GROUP, 0)
    inner, _ = _find(root, GROUP, 1)
    outer.children.remove(inner)        # owned by the host, though it lies inside outer's arm
    host.children.insert(host.children.index(outer) + 1, inner)
    assert any("source order" in p for p in _problems(root))


ELSE_SEPS = b"codeunit 50100 C implements IFoo\n#if X\n, IBar\n#else\n, IBaz\n#endif\n{\n}\n"


def test_mutation_separator_moved_to_the_other_arm(al_parser):
    """M1 (review I1): the #if arm's `,` moved into the #else arm, child list only. A leaf
    group (no nested group) has its own children checked for source order."""
    root = _tree(al_parser, ELSE_SEPS)
    g, _ = _find(root, GROUP)
    comma = next(c for c in g.children if c.kind == ",")
    g.children.remove(comma)
    g.children.insert(next(i for i, c in enumerate(g.children) if c.kind == "preproc_else") + 1, comma)
    assert any("source order" in p for p in _problems(root))
    assert runner_status_of_mutated(al_parser, ELSE_SEPS, root) == "representation-violation"


def test_mutation_item_and_separator_swapped_in_one_arm(al_parser):
    """M3 (review I1): item and `,` swapped inside the #if arm."""
    root = _tree(al_parser, ELSE_SEPS)
    g, _ = _find(root, GROUP)
    i = next(k for k, c in enumerate(g.children) if c.kind == ",")
    g.children[i], g.children[i + 1] = g.children[i + 1], g.children[i]
    assert any("source order" in p for p in _problems(root))
    assert runner_status_of_mutated(al_parser, ELSE_SEPS, root) == "representation-violation"


def runner_status_of_mutated(parser, src, root):
    """Every record's status when the runner reads the MUTATED multi-configuration tree."""
    import unittest.mock
    real = ir.from_tree
    first = [True]

    def from_tree(tree):
        out = real(tree)
        if first[0]:            # the file-level (multi-configuration) parse comes first
            first[0] = False
            return (root,) + out[1:]
        return out
    with unittest.mock.patch.object(ir, "from_tree", from_tree):
        statuses = {r.status for r in runner.check_input(parser, "m", src)}
    assert len(statuses) == 1, statuses
    return statuses.pop()


def test_mutation_neighbouring_same_family_region(al_parser):
    root = _tree(al_parser, TWO_HOSTS)
    _, first = _find(root, GROUP, 0)
    g2, second = _find(root, GROUP, 1)
    assert first is not second
    second.children.remove(g2)
    first.children.append(g2)           # the second declaration's group, in the first's list
    assert any("outside the list region" in p for p in _problems(root))


def test_mutation_arm_item_without_the_family_field(al_parser):
    root = _tree(al_parser, SEP_BEFORE)
    g, _ = _find(root, GROUP)
    item = next(c for c in g.children if c.kind == "identifier" and c.field == "interface")
    item.field = None
    assert any("arm content" in p for p in _problems(root))


# --- layer 3: lower_region and lowering mutations -----------------------------------------

def _leaf(kind, start, field=None, named=True):
    return Node(kind, named, field, start, start + 1, [])


def _host(*kids):
    kw = Node("implements_keyword", True, None, 0, 10, [])
    return Node("implements_clause", True, None, 0, 100, [kw, *kids]), kw


def _ident(start):
    return _leaf("identifier", start, "interface")


def _comma(start):
    return _leaf(",", start, named=False)


def test_lower_region_accepts_item_sep_item():
    host, kw = _host()
    kids = [kw, _ident(20), _comma(30), _ident(40)]
    assert cl.lower_region(host, kids, cl.FAMILIES["implements"]) == kids


@pytest.mark.parametrize("shape", [
    "two items",           # A B
    "leading separator",   # , A
    "trailing separator",  # A ,
    "two separators",      # A , , B
    "bracket in region",   # A ( B: _check_alternation would skip the bracket
    "unfielded item",      # an identifier without `interface`
])
def test_lower_region_rejects_a_broken_alternation(shape):
    host, kw = _host()
    run = {
        "two items": [_ident(20), _ident(40)],
        "leading separator": [_comma(15), _ident(20)],
        "trailing separator": [_ident(20), _comma(30)],
        "two separators": [_ident(20), _comma(30), _comma(35), _ident(40)],
        "bracket in region": [_ident(20), _leaf("(", 30, named=False), _ident(40)],
        "unfielded item": [_leaf("identifier", 20)],
    }[shape]
    with pytest.raises(cl.LoweringError) as e:
        cl.lower_region(host, [kw, *run], cl.FAMILIES["implements"])
    assert e.value.kind in ("list-separator", "list-item")


def test_empty_region_follows_the_flat_grammar():
    """Ruling (fix round 1): cardinality has no effect on lowering. An emptied region keeps
    the host's other children, or removes a host that owns nothing else ([])."""
    host, kw = _host()
    for card in sorted(cl.CARDINALITIES):
        fam = dataclasses.replace(cl.FAMILIES["implements"], cardinality=card)
        assert cl.lower_region(host, [kw], fam) == [kw], card
        whole = dataclasses.replace(fam, region=lambda h: (h.start, h.end))
        assert cl.lower_region(Node("implements_clause", True, None, 20, 40, []), [], whole) == [], card


# Synthetic families over EXISTING groups, for empty configurations whose flat parse is
# clean (no real strict family has one yet: implements' empty list is an alc syntax error).
ARGS_EMPTY = b"codeunit 1 T\n{\n    trigger OnRun()\n    begin\n        F(\n#if X\n            1\n#endif\n            );\n    end;\n}\n"


def _synthetic(monkeypatch, fam, policy_hosts):
    monkeypatch.setitem(cl.HOST_FAMILY, next(iter(fam.host_kinds)), fam)
    monkeypatch.setitem(cl.GROUP_FAMILY, fam.group, fam)
    entry = contracts.REGISTRY[fam.group]
    monkeypatch.setitem(contracts.REGISTRY, fam.group, dataclasses.replace(
        entry, hosts={**entry.hosts, **{h: "strict-list" for h in policy_hosts}}))


def test_clean_reference_empty_region_lowers_and_passes(al_parser, monkeypatch):
    """`F()`: the host keeps its delimiters, the region is empty, the comparison passes."""
    fam = cl.Family("arguments", frozenset({"argument_list"}),
                    lambda h: (h.children[0].end, h.children[-1].start),
                    frozenset({"integer"}), ",", None, "empty-interior")
    _synthetic(monkeypatch, fam, ["argument_list:<children>"])
    v = witness.verdicts(al_parser, ARGS_EMPTY)
    assert v == {"X=0": ("pass", []), "X=1": ("pass", [])}, v


def test_clean_reference_emptied_host_is_removed(al_parser, monkeypatch):
    """`SubPageLink = ;`: link_value_list owns nothing besides the list, so it is removed
    with optional-list-removed:<kind>, and the comparison passes."""
    from tools.config_oracle.tests.test_b11_groundwork import LINK_EMPTY
    fam = cl.Family("link_values", frozenset({"link_value_list"}), lambda h: (h.start, h.end),
                    frozenset({"link_value"}), ",", None, "empty-interior")
    _synthetic(monkeypatch, fam, ["link_value_list:<children>"])
    status, items = witness.verdicts(al_parser, LINK_EMPTY)["X=0,Y=0"]
    assert status == "pass", items
    assert [i.split("@")[0] for i in items] == ["normalised:optional-list-removed:link_value_list"], items


def test_emptied_region_with_an_erroring_reference_stays_reference_error(al_parser):
    """implements, all items in one group: X=0 reads `implements {`, which does not parse."""
    src = b"codeunit 50100 C implements\n#if X\nIFoo\n#endif\n{\n}\n"
    v = witness.verdicts(al_parser, src)
    assert v["X=0"][0] == "cannot-validate" and v["X=0"][1][0].startswith("reference-error:"), v
    assert v["X=1"] == ("pass", []), v


def test_mutation_wrong_separator_count(al_parser, monkeypatch):
    from tools.config_oracle.lowering import select
    real = select._splice_arm
    monkeypatch.setattr(select, "_splice_arm", lambda items: [c for c in real(items) if c.kind != ","])
    assert witness.statuses_with(al_parser, SEP_BEFORE, "lowering:list-separator") == ["X=1"]


def test_mutation_swapped_order_in_the_lowered_arm(al_parser, monkeypatch):
    from tools.config_oracle.lowering import select
    src = b"codeunit 50100 C implements\n#if X\nIFoo , IBar\n#else\nIFoo\n#endif\n{\n}\n"
    real = select._splice_arm
    monkeypatch.setattr(select, "_splice_arm", lambda items: list(reversed(real(items))))
    v = witness.verdicts(al_parser, src)
    assert v["X=1"][0] == "discrepancy" and any("structure" in i for i in v["X=1"][1]), v


def test_mutation_selected_arm_emptied(al_parser, monkeypatch):
    from tools.config_oracle.lowering import select
    monkeypatch.setattr(select, "_splice_arm", lambda items: [])
    assert witness.statuses_with(al_parser, SEP_BEFORE, "lowering:accounting") == ["X=1"]


def leaky_select(node, ctx):
    """A WRONG lowering for the leak mutation: splices every arm, not only the chosen one."""
    from tools.config_oracle.lowering.engine import Lowered, lower
    from tools.config_oracle.lowering.select import split_arms
    arms, endif = split_arms(node)
    out = []
    for directive, content in arms:
        ctx.accounting.mark(directive, "directive")
        for c in content:
            out.extend(lower(c, ctx.child(node.kind, c.field or "<children>")).nodes)
    ctx.accounting.mark(endif, "directive")
    return Lowered(out)


def test_mutation_unselected_arm_content_leaks(al_parser, monkeypatch):
    entry = contracts.REGISTRY[GROUP]
    monkeypatch.setitem(contracts.REGISTRY, GROUP, dataclasses.replace(
        entry, handler="tools.config_oracle.tests.test_conditional_lists.leaky_select"))
    assert witness.statuses_with(al_parser, NESTED_ELSE, "lowering:accounting")


def test_alternation_is_not_the_list_run_validator(al_parser, monkeypatch):
    """The strict families never reach engine._check_alternation (spec 6.3)."""
    from tools.config_oracle.lowering import engine

    def boom(new):
        raise AssertionError("strict list checked by _check_alternation")
    monkeypatch.setattr(engine, "_check_alternation", boom)
    witness.assert_all_pass(al_parser, SEP_BEFORE)
