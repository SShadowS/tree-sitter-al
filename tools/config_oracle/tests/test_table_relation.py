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


# Grammar finding G3: a whole-value #if nested in a whole-value arm. Its arms are
# flat shapes too (`Item;` -> identifier), in all four configurations.
G3_NESTED = WHOLE.replace(b"#if BC24\n                Item;\n#else\n                Resource;\n#endif\n",
                          b"#if X\n#if Y\n                Item;\n#else\n                Resource;\n#endif\n"
                          b"#else\n                Customer;\n#endif\n")
assert G3_NESTED != WHOLE


def test_g3_nested_whole_value_every_config(al_parser):
    witness.assert_produces(al_parser, G3_NESTED, "preproc_conditional_table_relation")
    v = witness.verdicts(al_parser, G3_NESTED)
    assert len(v) == 4, v
    witness.assert_all_pass(al_parser, G3_NESTED)


# Fix round 1 for G3: the inner `;` after the inner #endif (the nested arm's
# optional `;`). Parsed clean at 7f48453 and must stay clean, for name and literal arms.
G3_SEMI_AFTER = WHOLE.replace(b"#if BC24\n                Item;\n#else\n                Resource;\n#endif\n",
                              b"#if X\n#if Y\n                Item\n#else\n                Resource\n#endif\n"
                              b"                ;\n#else\n                Customer;\n#endif\n")
G3_SEMI_AFTER_LITERAL = (G3_SEMI_AFTER.replace(b"Item\n", b"1\n").replace(b"Resource\n", b"2\n")
                         .replace(b"Customer;", b"3;").replace(b"Code[20]", b"Integer")
                         .replace(b"TableRelation", b"MinValue"))
assert G3_SEMI_AFTER != WHOLE and b"Item" not in G3_SEMI_AFTER_LITERAL


@pytest.mark.parametrize("src", [G3_SEMI_AFTER, G3_SEMI_AFTER_LITERAL], ids=["name", "literal"])
def test_g3_nested_semicolon_after_endif_every_config(al_parser, src):
    witness.assert_produces(al_parser, src, "preproc_conditional_table_relation")
    v = witness.verdicts(al_parser, src)
    assert len(v) == 4, v
    witness.assert_all_pass(al_parser, src)


# G8 (Task 18): a whole-value arm is any property value. Each shape in both `;`
# placements (inside every arm, and once after #endif), both configurations.
def _whole(name, a, b, semi_inside):
    arm = (f"        {a};\n#else\n        {b};\n#endif\n" if semi_inside
           else f"        {a}\n#else\n        {b}\n#endif\n    ;\n")
    return f"page 50100 P\n{{\n    {name} =\n#if X\n{arm}}}\n".encode()


G8_SHAPES = [("OptionMembers", "A,B", "C"), ("Caption", "'a', Comment = 'x'", "'b', Locked = true"),
             ("OptionOrdinalValues", "-1, 0", "1"), ("RunObject", "Page A", "Page B"),
             ("Visible", "A and B", "not C"), ("DecimalPlaces", "0 : 5", "2"),
             ("SourceTableView", "where(A = const(1))", "sorting(B)"),
             ("RunPageLink", "A = field(B)", "C = const(1)"), ("OrderBy", "ascending(A)", "descending(B)"),
             ("Image", "Order", "Page"), ("Implementation", "I = J", "I = K"),
             ("CaptionML", "ENU='a', DAN='b'", "ENU='c', DAN='d'")]


@pytest.mark.parametrize("semi_inside", [True, False])
@pytest.mark.parametrize("name,a,b", G8_SHAPES)
def test_whole_value_arm_is_any_property_value(al_parser, name, a, b, semi_inside):
    src = _whole(name, a, b, semi_inside)
    witness.assert_produces(al_parser, src, "preproc_conditional_table_relation")
    witness.assert_all_pass(al_parser, src)


@pytest.mark.xfail(strict=True, reason="G9: flat `CaptionML = ENU='c';` is property_expression(comparison), "
                                       "the arm before #endif is ml_value_list (docs/deferred-work.md item 11)")
def test_single_pair_ml_arm_before_endif(al_parser):
    witness.assert_all_pass(al_parser, _whole("CaptionML", "ENU='a', DAN='b'", "ENU='c'", False))
