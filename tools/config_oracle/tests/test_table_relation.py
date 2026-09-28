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


@pytest.mark.xfail(strict=True, reason="grammar finding G1 (table_relation_property lacks the "
                                        "table_relation_value wrapper)")
def test_else_relation_join_every_config(al_parser):
    witness.assert_produces(al_parser, ELSE_JOIN, "else_table_relation_fragment")
    witness.assert_all_pass(al_parser, ELSE_JOIN)


@pytest.mark.xfail(strict=True, reason="grammar finding G2 (a bare relation in a #if arm parses as "
                                        "table_relation_expression, flat as identifier)")
def test_whole_relation_arm_every_config(al_parser):
    witness.assert_produces(al_parser, WHOLE, "preproc_conditional_table_relation")
    witness.assert_all_pass(al_parser, WHOLE)


def test_join_at_the_wrong_depth_is_caught(al_parser, monkeypatch):
    from tools.config_oracle.lowering import engine
    # Compared with the unmutated run: G1 already makes ELSE_JOIN a discrepancy, so
    # only items the mutation ALONE adds prove it is caught.
    base = {c: set(i) for c, (_, i) in witness.verdicts(al_parser, ELSE_JOIN).items()}
    monkeypatch.setattr(engine, "_deepest_open_if", lambda expr: expr.children[0])  # the SHALLOWEST if
    v = witness.verdicts(al_parser, ELSE_JOIN)
    assert any(s == "discrepancy" and set(i) - base[c] for c, (s, i) in v.items()), v


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
