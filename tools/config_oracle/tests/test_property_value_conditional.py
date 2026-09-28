"""Whole property values that are a #if: preproc_conditional_property_value,
contract whole-value-select (assemblers.property_value_select). Until G6 these
shared preproc_conditional_table_relation with the relation continuations, whose
witnesses stay in test_table_relation.py."""
import pytest

from tools.config_oracle.tests import witness

NODE = "preproc_conditional_property_value"

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


def test_whole_relation_arm_every_config(al_parser):
    witness.assert_produces(al_parser, WHOLE, NODE)
    witness.assert_all_pass(al_parser, WHOLE)


def test_dropped_terminator_is_caught(al_parser, monkeypatch):
    # Unmutated, every configuration passes (above). The arm's `;` is the
    # property's own terminator: a selection that discards it must not pass.
    from tools.config_oracle.lowering import assemblers, engine
    real = assemblers.property_value_select

    def no_terminator(node, ctx):
        r = real(node, ctx)
        return engine.Lowered(r.nodes, [f for f in r.frags if not isinstance(f, engine.Terminator)])
    monkeypatch.setattr(assemblers, "property_value_select", no_terminator)
    v = witness.verdicts(al_parser, WHOLE)
    assert v and all(s != "pass" for s, _ in v.values()), v


def test_arm_value_without_its_field_is_contract_shape(al_parser, monkeypatch):
    # Unmutated, every configuration passes (test_whole_relation_arm_every_config).
    # An arm value outside field `value` is not the contract's shape: strip the
    # field from every arm item and the selection must refuse, not lower it.
    from tools.config_oracle.lowering import assemblers
    real = assemblers.split_arms

    def unfielded(node):
        arms, endif = real(node)
        if node.kind != NODE:
            return arms, endif
        return [(d, [c.copy(field=None) if c.field == "value" else c for c in items])
                for d, items in arms], endif
    monkeypatch.setattr(assemblers, "split_arms", unfielded)
    v = witness.verdicts(al_parser, WHOLE)
    assert v and all(s != "pass" and any(i.startswith("lowering:contract-shape") and "not 'value'" in i
                                         for i in items)
                     for s, items in v.values()), v


# Grammar finding G4: a whole-value #if on any property, arms not names. Each arm
# holds the literal leaf its flat parse gives (`Caption = 'a';` -> string_literal).
def _whole_field(prop, a, b, semi_after=False):
    arm = (lambda v: v) if semi_after else (lambda v: v + ";")
    tail = "\n                ;" if semi_after else ""
    return (f"table 1 T\n{{\n    fields\n    {{\n        field(1; F; Integer)\n        {{\n"
            f"            {prop} =\n#if X\n                {arm(a)}\n#else\n                {arm(b)}\n#endif{tail}\n"
            f"        }}\n    }}\n}}\n").encode()


G4_WHOLE = {
    "string": _whole_field("Caption", "'a'", "'b'"),
    "string-semi-after": _whole_field("Caption", "'a'", "'b'", semi_after=True),
    "boolean": _whole_field("Editable", "true", "false"),
    "integer": _whole_field("MinValue", "1", "-2"),
}


@pytest.mark.parametrize("name", sorted(G4_WHOLE))
def test_g4_whole_value_literal_arms_every_config(al_parser, name):
    witness.assert_produces(al_parser, G4_WHOLE[name], NODE)
    witness.assert_all_pass(al_parser, G4_WHOLE[name])


# Grammar finding G3: a whole-value #if nested in a whole-value arm. Its arms are
# flat shapes too (`Item;` -> identifier), in all four configurations.
G3_NESTED = WHOLE.replace(b"#if BC24\n                Item;\n#else\n                Resource;\n#endif\n",
                          b"#if X\n#if Y\n                Item;\n#else\n                Resource;\n#endif\n"
                          b"#else\n                Customer;\n#endif\n")
assert G3_NESTED != WHOLE


def test_g3_nested_whole_value_every_config(al_parser):
    witness.assert_produces(al_parser, G3_NESTED, NODE)
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
    witness.assert_produces(al_parser, src, NODE)
    v = witness.verdicts(al_parser, src)
    assert len(v) == 4, v
    witness.assert_all_pass(al_parser, src)


# G8 (Task 18): a whole-value arm is any property value. Each shape in both `;`
# placements (inside every arm, and once after #endif), both configurations.
def _whole_page(name, a, b, semi_inside):
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
    src = _whole_page(name, a, b, semi_inside)
    witness.assert_produces(al_parser, src, NODE)
    witness.assert_all_pass(al_parser, src)


@pytest.mark.xfail(strict=True, reason="G9: flat `CaptionML = ENU='c';` is property_expression(comparison), "
                                       "the arm before #endif is ml_value_list (docs/deferred-work.md item 11)")
def test_single_pair_ml_arm_before_endif(al_parser):
    witness.assert_all_pass(al_parser, _whole_page("CaptionML", "ENU='a', DAN='b'", "ENU='c'", semi_inside=False))
