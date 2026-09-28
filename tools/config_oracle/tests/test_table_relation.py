import pytest

from tools.config_oracle.tests import witness

ELSE_JOIN = b"""table 1 T
{
    fields
    {
        field(1; F; Code[20])
        {
            TableRelation = if (Type = const(Item)) Item
                else if (Type = const(Resource)) Resource
#if BC24
                else if (Type = const("Alloc")) "Alloc Account" where("Account Type" = const(Fixed));
#else
                ELSE IF (Type = CONST("Alloc")) "G/L Account";
#endif
        }
    }
}
"""

WHOLE = b"""table 1 T
{
    fields
    {
        field(1; F; Code[20])
        {
            TableRelation =
#if BC24
                Item;
#else
                Resource;
#endif
        }
    }
}
"""


def test_else_relation_join_every_config(al_parser):
    witness.assert_produces(al_parser, ELSE_JOIN, "else_table_relation_fragment")
    witness.assert_all_pass(al_parser, ELSE_JOIN)


def test_whole_relation_arm_every_config(al_parser):
    witness.assert_produces(al_parser, WHOLE, "preproc_conditional_table_relation")
    witness.assert_all_pass(al_parser, WHOLE)


def test_join_at_the_wrong_depth_is_caught(al_parser, monkeypatch):
    from tools.config_oracle.lowering import engine
    # Unmutated, every configuration passes (test_else_relation_join_every_config).
    monkeypatch.setattr(engine, "_deepest_open_if", lambda expr: expr.children[0])  # the SHALLOWEST if
    v = witness.verdicts(al_parser, ELSE_JOIN)
    assert any(s == "discrepancy" for s, _ in v.values()), v


NESTED = b"""table 1 T
{
    fields
    {
        field(1; F; Code[20])
        {
            TableRelation = if (Type = const(Item)) Item
                else
#if BC24
                if (Type = const("Alloc")) "Alloc Account";
#else
                IF (Type = CONST("Alloc")) "G/L Account";
#endif
        }
    }
}
"""


def test_nested_host_is_refused_not_lowered(al_parser):
    # table_relation_expression:<children> is registered `unsupported`: the arm's
    # relation would have to merge into the enclosing else_relation, unnamed here.
    witness.assert_produces(al_parser, NESTED, "preproc_conditional_table_relation")
    v = witness.verdicts(al_parser, NESTED)
    assert v and all(i[0].startswith("lowering:unsupported-type") and "host table_relation_expression" in i[0]
                     for _, i in v.values()), v


# Grammar finding G4: a whole-value #if on any property, arms not names. Each arm
# holds the literal leaf its flat parse gives (`Caption = 'a';` -> string_literal).
def _whole(prop, a, b, semi_after=False):
    arm = (lambda v: v) if semi_after else (lambda v: v + ";")
    tail = "\n                ;" if semi_after else ""
    return (f"table 1 T\n{{\n    fields\n    {{\n        field(1; F; Integer)\n        {{\n"
            f"            {prop} =\n#if X\n                {arm(a)}\n#else\n                {arm(b)}\n#endif{tail}\n"
            f"        }}\n    }}\n}}\n").encode()


G4_WHOLE = {
    "string": _whole("Caption", "'a'", "'b'"),
    "string-semi-after": _whole("Caption", "'a'", "'b'", semi_after=True),
    "boolean": _whole("Editable", "true", "false"),
    "integer": _whole("MinValue", "1", "-2"),
}


@pytest.mark.parametrize("name", sorted(G4_WHOLE))
def test_g4_whole_value_literal_arms_every_config(al_parser, name):
    witness.assert_produces(al_parser, G4_WHOLE[name], "preproc_conditional_table_relation")
    witness.assert_all_pass(al_parser, G4_WHOLE[name])
