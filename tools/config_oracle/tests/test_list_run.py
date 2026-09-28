"""P3 list-run witnesses (spec P3)."""
import pytest

from tools.config_oracle.tests import witness

PERMS_TERMINATOR = b"codeunit 50100 T\n{\n    Permissions = tabledata A = R,\n#if X\n                  tabledata B = R;\n#else\n                  tabledata C = R;\n#endif\n\n    trigger OnRun() begin end;\n}\n"
PERMS_INTERNAL = b"codeunit 50100 T\n{\n    Permissions = tabledata A = R,\n#if X\n                  tabledata B = R,\n#endif\n                  tabledata C = R;\n\n    trigger OnRun() begin end;\n}\n"
ARGS_LEAD = b"codeunit 1 T\n{\n    trigger OnRun()\n    begin\n        F(1,\n#if X\n            2,\n#endif\n            3);\n    end;\n}\n"
ARGS_TRAIL = b"codeunit 1 T\n{\n    trigger OnRun()\n    begin\n        F(1\n#if X\n            , 2\n#endif\n            , 3);\n    end;\n}\n"
LIST_ELEMENTS = b"codeunit 1 T\n{\n    trigger OnRun()\n    begin\n        L := [1\n#if X\n            , 2\n#endif\n        ];\n    end;\n}\n"
OPTIONS = b"table 1 T\n{\n    fields\n    {\n        field(1; F; Option)\n        {\n            OptionMembers = A,\n#if X\n            B,\n#endif\n            C;\n        }\n    }\n}\n"
WHERE = b"table 1 T\n{\n    fields\n    {\n        field(1; F; Integer)\n        {\n            FieldClass = FlowField;\n            CalcFormula = count(T where(A = const(1)\n#if X\n                , B = const(2)\n#endif\n                ));\n        }\n    }\n}\n"
LINK = b"page 1 P\n{\n    layout\n    {\n        area(Content)\n        {\n            part(S; Sub)\n            {\n                SubPageLink = A = field(A)\n#if X\n                    , B = field(B)\n#endif\n                    ;\n            }\n        }\n    }\n}\n"

CASES = {
    "preproc_conditional_permissions": [PERMS_TERMINATOR, PERMS_INTERNAL],
    "preproc_conditional_arguments": [ARGS_LEAD, ARGS_TRAIL],
    "preproc_conditional_list_elements": [LIST_ELEMENTS],
    "preproc_conditional_option_members": [OPTIONS],
    "preproc_conditional_where": [WHERE],
    "preproc_conditional_link_values": [LINK],
}


@pytest.mark.parametrize("kind,src", [(k, s) for k, v in CASES.items() for s in v])
def test_list_run_witness(al_parser, kind, src):
    witness.assert_produces(al_parser, src, kind)
    witness.assert_all_pass(al_parser, src)


def test_both_comma_placements(al_parser):
    for src in (ARGS_LEAD, ARGS_TRAIL):
        witness.assert_all_pass(al_parser, src)


def test_dropped_separator_trips_list_separator(al_parser, monkeypatch):
    from tools.config_oracle.lowering import select
    real = select._splice_arm
    def drop_commas(items):
        return [c for c in real(items) if c.kind != ","]
    monkeypatch.setattr(select, "_splice_arm", drop_commas)
    assert witness.statuses_with(al_parser, ARGS_LEAD, "lowering:list-separator")


def test_terminator_left_in_list_trips_structure(al_parser, monkeypatch):
    from tools.config_oracle.lowering import select
    monkeypatch.setattr(select, "HOIST_TERMINATOR", False)
    v = witness.verdicts(al_parser, PERMS_TERMINATOR)
    assert any(s == "discrepancy" and any("structure" in i for i in items) for s, items in v.values()), v
