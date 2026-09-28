"""P2 witness matrix: every branch-select family, every configuration (spec P2, base §5)."""
import pytest

from tools.config_oracle import contracts
from tools.config_oracle.tests import witness

P2_WITNESSES = {
    "preproc_conditional_object": [
        # first arm, #elif (two declarations, so the policy-swap probe has a
        # config to trip on), #else, no arm (A and B both undefined -> #else)
        b"#if A\ncodeunit 1 X { }\n#elif B\ncodeunit 2 Y { }\ncodeunit 5 V { }\n#else\ncodeunit 3 Z { }\n#endif\ncodeunit 4 W { }\n",
        # namespace + using inside the arms, identical namespace in two arms,
        # a second element (using) in the #if arm for the policy-swap probe
        b"#if A\nnamespace N.A;\nusing System;\n#else\nnamespace N.A;\n#endif\nusing System.Text;\ncodeunit 1 X { }\n",
    ],
    "preproc_conditional_actions": [
        b"page 1 P\n{\n    actions\n    {\n        area(Processing)\n        {\n#if A\n            action(X) { }\n#else\n            action(Y) { }\n            action(Z) { }\n#endif\n        }\n    }\n}\n",
    ],
    "preproc_conditional_layout": [
        b"page 1 P\n{\n    layout\n    {\n        area(Content)\n        {\n#if A\n            field(X; Rec.X) { }\n#endif\n            field(Y; Rec.Y) { }\n        }\n    }\n}\n",
    ],
    "preproc_conditional_layout_mixed": [
        b"page 1 P\n{\n    layout\n    {\n        area(Content)\n        {\n            group(G)\n            {\n#if A\n                Caption = 'a';\n                field(X; Rec.X) { }\n#endif\n            }\n        }\n    }\n}\n",
    ],
    "preproc_conditional_report": [
        # two columns in the #if arm, so the policy-swap probe has a config to trip on
        b"report 1 R\n{\n    dataset\n    {\n        dataitem(D; Integer)\n        {\n#if A\n            column(C1; 1) { }\n            column(C1b; 2) { }\n#else\n            column(C2; 2) { }\n#endif\n        }\n    }\n}\n",
    ],
    "preproc_conditional_rendering": [
        b"report 1 R\n{\n    rendering\n    {\n#if A\n        layout(L1) { Type = RDLC; }\n#endif\n        layout(L2) { Type = Word; }\n    }\n}\n",
    ],
    "preproc_conditional_dataset": [
        b"report 1 R\n{\n    dataset\n    {\n#if A\n        dataitem(D; Integer) { }\n#else\n#endif\n    }\n}\n",
    ],
    "preproc_conditional_fields": [
        # nested #if among fields (BC 29 family C), #else with a different field
        b"table 1 T\n{\n    fields\n    {\n        field(1; A; Integer) { }\n#if A\n#if B\n        field(2; B; Integer) { }\n#endif\n        field(3; C; Integer) { }\n#else\n        field(4; D; Integer) { }\n#endif\n    }\n}\n",
    ],
    "preproc_conditional_keys": [
        b"table 1 T\n{\n    fields { field(1; A; Integer) { } field(2; B; Integer) { } }\n    keys\n    {\n        key(PK; A) { }\n#if A\n#if B\n        key(K1; B) { }\n#endif\n        key(K2; A, B) { }\n#endif\n    }\n}\n",
    ],
    "preproc_conditional_fieldgroups": [
        # a second fieldgroup in the #if arm, so the policy-swap probe has a
        # config (A=1) that selects two nodes, not one
        b"table 1 T\n{\n    fields { field(1; A; Integer) { } }\n    fieldgroups\n    {\n#if A\n        fieldgroup(DropDown; A) { }\n        fieldgroup(Brick2; A) { }\n#else\n        fieldgroup(Brick; A) { }\n#endif\n    }\n}\n",
    ],
    "preproc_conditional_var": [
        b"codeunit 1 T\n{\n    var\n        X: Integer;\n#if A\n        Y: Integer;\n#else\n        Z: Integer;\n#endif\n\n    procedure P()\n    var\n        L: Integer;\n#if B\n        M: Integer;\n#endif\n    begin\n    end;\n}\n",
    ],
}

# A witness whose arm is EMPTY in some configuration (Review Focus 1).
EMPTY_ARM = {
    "preproc_conditional_dataset": P2_WITNESSES["preproc_conditional_dataset"][0],
}


def _cases():
    return [(t, s) for t, srcs in P2_WITNESSES.items() for s in srcs]


@pytest.mark.parametrize("kind,src", _cases())
def test_witness_produces_its_type(al_parser, kind, src):
    witness.assert_produces(al_parser, src, kind)


@pytest.mark.parametrize("kind,src", _cases())
def test_every_configuration_passes(al_parser, kind, src):
    witness.assert_all_pass(al_parser, src)


@pytest.mark.parametrize("kind,src", _cases())
def test_policy_swap_trips_policy(al_parser, monkeypatch, kind, src):
    e = contracts.REGISTRY[kind]
    monkeypatch.setitem(contracts.REGISTRY, kind, contracts.Entry(
        e.type, e.kind, e.handler, {h: "single-slot" for h in e.hosts}, e.alias_to, e.arm, e.reading))
    assert witness.statuses_with(al_parser, src, "lowering:policy"), "the mutation tripped nothing"


@pytest.mark.parametrize("kind,src", list(EMPTY_ARM.items()))
def test_empty_arm_loses_and_gains_nothing(al_parser, kind, src):
    witness.assert_all_pass(al_parser, src)


def test_nested_fields_and_keys_every_config(al_parser):
    for kind in ("preproc_conditional_fields", "preproc_conditional_keys"):
        src = P2_WITNESSES[kind][0]
        v = witness.verdicts(al_parser, src)
        assert set(v) >= {"A=0,B=0", "A=1,B=0", "A=1,B=1"} or len(v) >= 3, v
        witness.assert_all_pass(al_parser, src)
