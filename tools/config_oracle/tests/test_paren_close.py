"""Issue #44 (F1): `preproc_split_paren_close`, a call's `)` (and the statement's `;`) in every arm.

The oracle lowers the node with registrations only (branch-select, list-run, terminator-hoist).
These tests show the pass is not vacuous: each covered shape is `pass` in every configuration,
and each mutant (no registration, no terminator hoist, the wrong arm, a dropped separator)
turns it into a refusal or a discrepancy.
"""
from pathlib import Path

import pytest

from tools.config_oracle import contracts, fixtures
from tools.config_oracle.tests import witness

KIND = "preproc_split_paren_close"
CORPUS = Path(__file__).resolve().parents[3] / "test" / "corpus"
FIXTURE = "issue44_f1_paren_close_test.txt"


def _cases():
    return [c for c in fixtures.extract(CORPUS) if c.file == FIXTURE]


def _src(fragment):
    return next(c.source for c in _cases() if fragment in c.name)


def test_fixture_has_every_case():
    assert len(_cases()) == 21


@pytest.mark.parametrize("name", [c.name for c in _cases()])
def test_each_shape_passes_in_every_configuration(al_parser, name):
    src = _src(name)
    witness.assert_produces(al_parser, src, KIND)
    witness.assert_all_pass(al_parser, src)


def test_unregistered_type_cannot_validate(al_parser, monkeypatch):
    src = _src("(repro 1)")
    monkeypatch.delitem(contracts.REGISTRY, KIND)
    v = witness.verdicts(al_parser, src)
    assert v and all(s == "cannot-validate" and any(i.startswith("lowering:unregistered-type") for i in items)
                     for s, items in v.values()), v


def test_terminator_left_in_the_list_is_a_discrepancy(al_parser, monkeypatch):
    from tools.config_oracle.lowering import select
    monkeypatch.setattr(select, "HOIST_TERMINATOR", False)
    v = witness.verdicts(al_parser, _src("(repro 1)"))
    assert v and all(s == "discrepancy" for s, _ in v.values()), v


def test_empty_statement_after_semicolon_arms_is_checked(al_parser, monkeypatch):
    # The `;` after #endif is an empty statement when every arm carries the call's `;`: dropping the hoisted
    # arm terminator (the call then ends without one) must not pass.
    from tools.config_oracle.lowering import select
    monkeypatch.setattr(select, "HOIST_TERMINATOR", False)
    v = witness.verdicts(al_parser, _src("an empty statement, then a second statement"))
    assert v and all(s != "pass" for s, _ in v.values()), v


def test_wrong_arm_is_refused(al_parser, monkeypatch):
    # The leaf accounting sees the swapped arm first (a kept leaf on a masked line); where it
    # does not, the comparison against the flat reference does.
    from tools.config_oracle.lowering import select
    real = select.chosen_arm

    def other_arm(node, arms, ctx):
        choice = real(node, arms, ctx)
        if node.kind == KIND:
            return next(d.start for d, _ in arms if d.start != choice)
        return choice
    monkeypatch.setattr(select, "chosen_arm", other_arm)
    for fragment in ("(repro 1)", "(repro 2)", "three arms"):
        v = witness.verdicts(al_parser, _src(fragment))
        assert v and all(s == "discrepancy" or any(i.startswith("lowering:accounting") for i in items)
                         for s, items in v.values()), (fragment, v)


def _stmt(s):
    return b"codeunit 1 T\n{\n    procedure P()\n    begin\n        " + s + b"\n    end;\n}\n"


# `V(1, )` at A=1 (tools/alc_probe/cases/issue44/f1/overaccept_empty_arm_after_comma.al): the
# rebuilt list ends at a separator. The flat parse errors first, so the lowering is asserted directly.
STRAY_COMMA = _stmt(b"V(1,\n#if A\n );\n#else\n 2);\n#endif")


def test_list_run_registration_checks_the_rebuilt_list(al_parser, monkeypatch):
    """engine.LIST_RUN_TYPES: a host list holding this group is checked for item / separator
    alternation once rebuilt. Mutation: the entry removed, the stray `,` goes unchecked."""
    from tools.config_oracle import ir
    from tools.config_oracle.directives import resolve
    from tools.config_oracle.lowering import engine, lower_tree
    from tools.config_oracle.lowering.engine import LoweringError

    def lower(src):
        root, extras, _ = ir.from_tree(al_parser.parse(src))
        lower_tree(root, extras, resolve(src, frozenset({"A"})))

    with pytest.raises(LoweringError) as e:
        lower(STRAY_COMMA)
    assert e.value.kind == "list-separator", e.value
    monkeypatch.setattr(engine, "LIST_RUN_TYPES", engine.LIST_RUN_TYPES - {KIND})
    lower(STRAY_COMMA)   # no check, no error: the registration is what refuses it


# `Foo( #if X #if Y 5 #endif ) #else 2) #endif;` at X=1,Y=0 is `Foo( );`: an operand group with no
# live arm as the arm's only item contributes no item (regions.EMPTY_LIST_ITEM).
EMPTY_ITEM = _stmt(b"Foo(\n#if X\n#if Y\n 5\n#endif\n )\n#else\n 2)\n#endif\n;")


def test_list_item_slot_registration(al_parser, monkeypatch):
    """regions.LIST_ITEM_SLOTS: an empty operand group inside an arm is no item, not contract-shape.
    Mutation: the slot removed, the valid configuration is refused as contract-shape."""
    from tools.config_oracle.lowering import regions
    v = witness.verdicts(al_parser, EMPTY_ITEM)
    assert all(s == "pass" for s, _ in v.values()), v
    assert any(i.startswith("normalised:empty-list-item") for i in v["X=1,Y=0"][1]), v
    monkeypatch.setattr(regions, "LIST_ITEM_SLOTS", regions.LIST_ITEM_SLOTS - {f"{KIND}:<children>"})
    v = witness.verdicts(al_parser, EMPTY_ITEM)
    assert v["X=1,Y=0"][0] == "cannot-validate" and v["X=1,Y=0"][1][0].startswith("lowering:contract-shape"), v


def test_dropped_separator_is_refused(al_parser, monkeypatch):
    from tools.config_oracle.lowering import select
    real = select._splice_arm
    monkeypatch.setattr(select, "_splice_arm", lambda items: [c for c in real(items) if c.kind != ","])
    for fragment in ("(repro 2)", "whole argument list"):
        v = witness.verdicts(al_parser, _src(fragment))
        assert any(s != "pass" for s, _ in v.values()), (fragment, v)
        assert all(s == "pass" or any(i.startswith(("lowering:list-separator", "lowering:accounting"))
                                      for i in items) or s == "discrepancy"
                   for s, items in v.values()), (fragment, v)
