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


# GRAMMAR FINDING, pinned rather than papered over (Task 8 report). With the #if
# group directly in `property:value`, the grammar takes table_relation_property
# (grammar.js:804-812), whose value is a bare table_relation_expression (or the
# conditional alone); the per-configuration parse wraps the same relation in
# table_relation_value (ELSE_JOIN) or reads it as a generic `value: identifier`
# (WHOLE). The lowering is exact apart from that one edge: each configuration
# carries ONLY the discrepancy at that node. When the grammar is fixed, these
# become assert_all_pass.
_WRAPPER = "/property.-@81-94/table_relation_value.value@97-99/table_relation_expression.-@97-99"
_GENERIC = "/property.-@81-94/identifier.value@"


def _only_finding(v, marker):
    assert v and all(s == "discrepancy" for s, _ in v.values()), v
    for cfg, (_, items) in v.items():
        assert items and all(marker in i for i in items), (cfg, items)


def test_else_relation_join_every_config(al_parser):
    witness.assert_produces(al_parser, ELSE_JOIN, "else_table_relation_fragment")
    _only_finding(witness.verdicts(al_parser, ELSE_JOIN), _WRAPPER)


def test_whole_relation_arm_every_config(al_parser):
    witness.assert_produces(al_parser, WHOLE, "preproc_conditional_table_relation")
    _only_finding(witness.verdicts(al_parser, WHOLE), _GENERIC)


def test_join_at_the_wrong_depth_is_caught(al_parser, monkeypatch):
    from tools.config_oracle.lowering import engine
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
