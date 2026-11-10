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


# Item 29: the four #if-inside-the-chain shapes (alc accepts every configuration,
# tools/alc_probe/cases/item29-relation-chain/).
def _field(relation):
    return b"""table 1 T
{
    fields
    {
        field(1; F; Code[20])
        {
            TableRelation = """ + relation + b"""
        }
    }
}
"""


SHARED_ELSE = _field(b"if (A = const(X)) Item\n#if X\n else if (A = const(Y)) Vendor\n#endif\n else Customer;")
WHERE_ARM = _field(b"if (A = const(X)) Item\n#if X\n where(A = const(1))\n#endif\n else Customer;")
SHARED_WHERE = _field(b"\n#if X\n Item\n#else\n Resource\n#endif\n where(A = const(1));")
THEN_ARM = _field(b"if (A = const(X))\n#if X\n Item\n#else\n Vendor\n#endif\n ;")


def test_item29_shapes_every_config(al_parser):
    witness.assert_produces(al_parser, WHERE_ARM, "preproc_conditional_table_relation")
    for src in (SHARED_ELSE, WHERE_ARM, SHARED_WHERE, THEN_ARM):
        assert len(witness.verdicts(al_parser, src)) == 2
        witness.assert_all_pass(al_parser, src)


def test_item29_where_join_is_load_bearing(al_parser, monkeypatch):
    from tools.config_oracle.lowering import engine
    monkeypatch.setattr(engine, "_join_relation_where", lambda value: None)
    for src in (WHERE_ARM, SHARED_WHERE):
        v = witness.verdicts(al_parser, src)
        assert any(s == "discrepancy" for s, _ in v.values()), v


# Item 75: a conditional head of if-relations, then a shared where AND a shared else
# (tools/alc_probe/cases/item29-relation-chain/s5-*: alc accepts both configurations).
# The where joins the arm's then target first, then the else joins the open if.
SHARED_WHERE_ELSE = _field(b"\n#if X\n if (A = const(1)) Item\n#else\n if (A = const(2)) Resource\n#endif\n"
                           b" where(A = const(1)) else Customer;")


def test_item75_shared_where_then_else_every_config(al_parser):
    witness.assert_produces(al_parser, SHARED_WHERE_ELSE, "else_table_relation_fragment")
    assert len(witness.verdicts(al_parser, SHARED_WHERE_ELSE)) == 2
    witness.assert_all_pass(al_parser, SHARED_WHERE_ELSE)


def test_item75_where_join_is_load_bearing(al_parser, monkeypatch):
    from tools.config_oracle.lowering import engine
    monkeypatch.setattr(engine, "_join_relation_where", lambda value: None)
    v = witness.verdicts(al_parser, SHARED_WHERE_ELSE)
    assert any(s == "discrepancy" for s, _ in v.values()), v


# Item 78: a conditional head of if-relations, an optional shared where, then a GROUP of
# else arms, the `;` inside the arms or after #endif (tools/alc_probe/cases/
# item29-relation-chain/s7*, s8*: alc accepts all four configurations of each).
_HEAD = b"\n#if X\n if (A = const(1)) Item\n#else\n if (A = const(2)) Resource\n#endif\n"
ELSE_GROUP = {
    "where-semi-inside": _field(_HEAD + b" where(A = const(1))\n#if Y\n else Customer;\n#else\n else Vendor;\n#endif\n"),
    "where-semi-after": _field(_HEAD + b" where(A = const(1))\n#if Y\n else Customer\n#else\n else Vendor\n#endif\n ;"),
    "semi-inside": _field(_HEAD + b"#if Y\n else Customer;\n#else\n else Vendor;\n#endif\n"),
    "semi-after": _field(_HEAD + b"#if Y\n else Customer\n#else\n else Vendor\n#endif\n ;"),
    # an arm that is itself a group of else arms (s11-*)
    "nested": _field(_HEAD + b"#if Y\n#if Z\n else Customer\n#else\n else Vendor\n#endif\n ;\n#else\n else Item;\n#endif\n"),
}


def test_item78_conditional_else_group_every_config(al_parser):
    for name, src in ELSE_GROUP.items():
        witness.assert_produces(al_parser, src, "else_table_relation_fragment")
        assert len(witness.verdicts(al_parser, src)) == (8 if name == "nested" else 4), name
        witness.assert_all_pass(al_parser, src)


def test_item78_where_join_is_load_bearing(al_parser, monkeypatch):
    from tools.config_oracle.lowering import engine
    monkeypatch.setattr(engine, "_join_relation_where", lambda value: None)
    for name in ("where-semi-inside", "where-semi-after"):
        v = witness.verdicts(al_parser, ELSE_GROUP[name])
        assert any(s == "discrepancy" for s, _ in v.values()), (name, v)
