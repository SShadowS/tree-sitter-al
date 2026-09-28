"""Relation CONTINUATIONS: preproc_conditional_table_relation, contract
else-relation-join (assemblers.table_relation_select). A whole property value
that is a #if is preproc_conditional_property_value since G6; its witnesses are
in test_property_value_conditional.py."""
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


def test_else_relation_join_every_config(al_parser):
    witness.assert_produces(al_parser, ELSE_JOIN, "else_table_relation_fragment")
    witness.assert_all_pass(al_parser, ELSE_JOIN)


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


# Item 19 (G11): the continuation's arms carry no `;`; the property's own `;`
# follows #endif. It used to become an empty_statement sibling of the property.
SEMI_AFTER = b"""table 1 T
{
    fields
    {
        field(1; F; Code[20])
        {
            TableRelation = if (Type = const(Item)) Item
#if X
                else Resource
#else
                else Customer
#endif
                ;
        }
    }
}
"""


def test_else_join_with_semicolon_after_endif_every_config(al_parser):
    witness.assert_produces(al_parser, SEMI_AFTER, "else_table_relation_fragment")
    v = witness.verdicts(al_parser, SEMI_AFTER)
    assert len(v) == 2, v
    witness.assert_all_pass(al_parser, SEMI_AFTER)
