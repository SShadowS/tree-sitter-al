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


# Items 81 and 84: the `;` of an else-group arm spread over a group, an arm that is only
# the property's `;`, and the same `;` placements after a plain relation, at a whole-value
# arm site and in a relation arm (tools/alc_probe/cases/item29-relation-chain/s12-*, s13-*,
# tools/alc_probe/cases/item81/; alc accepts these in every configuration below).
_HEAD_WHERE = _HEAD + b" where(A = const(1))\n"
_Y = b"#if Y\n else Customer\n"
_ELSE_V = b"#else\n else Vendor;\n#endif\n"
ITEM81 = {
    "else-arm-empty": _field(_HEAD_WHERE + _Y + b"#if Z\n#endif\n ;\n" + _ELSE_V),
    "else-arm-sep-only": _field(_HEAD_WHERE + _Y + b"#if Z\n ;\n#else\n ;\n#endif\n" + _ELSE_V),
    "else-arm-elif": _field(_HEAD_WHERE + _Y + b"#if Z\n ;\n#elif W\n ;\n#else\n ;\n#endif\n" + _ELSE_V),
    "else-arm-nested": _field(_HEAD_WHERE + _Y + b"#if Z\n#if W\n ;\n#else\n ;\n#endif\n#else\n ;\n#endif\n" + _ELSE_V),
    "item84": _field(_HEAD_WHERE + b"#if Y\n else Customer;\n#else\n ;\n#endif\n"),
    "item84-mirror": _field(_HEAD_WHERE + b"#if Y\n ;\n#else\n else Customer;\n#endif\n"),
    "plain-sep-only": _field(b"Item\n#if X\n ;\n#else\n ;\n#endif\n"),
    "plain-elif": _field(b"Item\n#if X\n ;\n#elif Y\n ;\n#else\n ;\n#endif\n"),
    "plain-nested": _field(b"Item\n#if X\n#if Y\n ;\n#else\n ;\n#endif\n#else\n ;\n#endif\n"),
    "arm-sep-only": _field(b"\n#if TPL\n Item\n#if X\n ;\n#else\n ;\n#endif\n#else\n Resource;\n#endif\n"),
    # second review: what follows a complete group is the body's (an empty_statement, the
    # body's conditional), in every configuration
    "plain-then-semi": _field(b"Item\n#if X\n ;\n#else\n ;\n#endif\n ;\n"),
    "plain-then-group": _field(b"Item\n#if X\n ;\n#else\n ;\n#endif\n#if Y\n ;\n#else\n ;\n#endif\n"),
    "item84-then-semi": _field(_HEAD_WHERE + b"#if Y\n ;\n#else\n else Customer;\n#endif\n ;\n"),
}
# Deferred item 99: a group that supplies the `;` in only some configurations has no one
# correct tree when anything follows it, so it ERRORs (alc accepts each of these in every
# configuration; tools/alc_probe/cases/item81/).
ITEM99 = {
    "plain-adjacent": _field(b"Item\n#if X\n ;\n#endif\n#if not X\n ;\n#endif\n"),
    "arm-adjacent": _field(b"\n#if TPL\n Item\n#if X\n ;\n#endif\n#if not X\n ;\n#endif\n#else\n Resource;\n#endif\n"),
    "else-arm-adjacent": _field(_HEAD_WHERE + _Y + b"#if Z\n ;\n#endif\n#if not Z\n ;\n#endif\n" + _ELSE_V),
    "one-arm-then-semi": _field(b"Item\n#if X\n ;\n#endif\n ;\n"),
    "empty-else-then-semi": _field(b"Item\n#if X\n ;\n#else\n#endif\n ;\n"),
    "item84-open-arm-then-semi": _field(_HEAD_WHERE + b"#if Y\n ;\n#else\n else Customer\n#endif\n ;\n"),
    "item84-no-where": _field(_HEAD + b"#if Y\n ;\n#else\n else Customer;\n#endif\n"),
}


def test_item81_semicolon_placements_every_config(al_parser):
    for name, src in ITEM81.items():
        witness.assert_produces(al_parser, src, "preproc_conditional_table_relation")
        witness.assert_all_pass(al_parser, src)


def test_item99_partial_semicolon_groups_error(al_parser):
    for name, src in ITEM99.items():
        assert al_parser.parse(src).root_node.has_error, name


def test_item81_terminator_is_load_bearing(al_parser, monkeypatch):
    """Dropping the groups' `;` must fail the configuration, not pass silently."""
    from tools.config_oracle.lowering import assemblers
    real = assemblers._select_arm
    def no_group_terminator(node, ctx):
        items, frags = real(node, ctx)
        return items, [f for f in frags if not isinstance(f, assemblers.Terminator)]
    monkeypatch.setattr(assemblers, "_select_arm", no_group_terminator)
    v = witness.verdicts(al_parser, ITEM81["plain-sep-only"])
    assert all(s != "pass" for s, _ in v.values()), v   # the source accounting catches it
