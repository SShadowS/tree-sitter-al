"""B7b-1d (deferred item 46): #if groups in a report label's, a label variable's and a caption's
comma-led tail lower by ordinary splicing; a caption whose groups select nothing is a bare text."""
import pytest

from tools.config_oracle.tests import witness

CAPTION = b"""page 50100 P
{
    Caption = 'a'
#if X
        , Locked = true
#else
#endif
        ;
    layout { }
}
"""
REPORT_LABEL = b"""report 50100 R
{
    labels
    {
        L1 = 'a'
#if X
            , Locked = true
#else
            , Comment = 'c'
#endif
            , MaxLength = 10;
    }
}
"""
LABEL_VAR = b"""codeunit 50100 C
{
    var
        L: Label 'a',
#if X
            Locked = true,
#endif
            Comment = 'c';
}
"""
LABEL_VALUE_ARM = b"""report 50100 R
{
    labels
    {
        L1 =
#if X
            'a', Locked = true
#else
            'b'
#endif
            ;
    }
}
"""

# `'a',` then a group holding a lone `,`: a discrepancy in the alc-rejected configuration
# (X=1, a doubled comma, AL0107), so the corpus cannot hold it (a corpus case cannot carry
# a discrepancy). Pinned here: the tree, and the oracle verdict per configuration.
CAPTION_TRAIL_COMMA_GROUP = b"""page 50100 P
{
    Caption = 'a',
#if X
    ,
#endif
    ;
}
"""
CAPTION_TRAIL_COMMA_GROUP_THEN_EMPTY = b"""page 50100 P
{
    Caption = 'a',
#if X
    ,
#else
#endif
#if Y
#endif
    ;
}
"""
FIELD_CAPTION_TRAIL_COMMA_GROUP = b"""table 50100 T
{
    fields
    {
        field(1; K; Code[20])
        {
            Caption = 'a',
#if X
            ,
#endif
            ;
        }
    }
}
"""
# Item 88: a text-bearing group after a type that is not Label parses (X=0 is the flat
# `A: Integer;`, X=1 is AL0104/AL0107), with a tree that differs from flat (bare basic_type).
INT_VAR_TEXT_GROUP = b"""codeunit 50100 C
{
    var
        A: Integer
#if X
        'a', Locked = true
#endif
        ;
}
"""


@pytest.mark.parametrize("src,rejected", [
    (CAPTION_TRAIL_COMMA_GROUP, ("X=1",)),
    (CAPTION_TRAIL_COMMA_GROUP_THEN_EMPTY, ("X=1,Y=0", "X=1,Y=1")),
    (FIELD_CAPTION_TRAIL_COMMA_GROUP, ("X=1",)),
])
def test_caption_trailing_comma_lone_comma_group_shape(al_parser, src, rejected):
    root = al_parser.parse(src).root_node
    assert not root.has_error
    assert "value: (caption_value (string_literal) (preproc_conditional_caption_subfields " in str(root)
    v = witness.verdicts(al_parser, src)
    assert sorted(c for c, (s, _) in v.items() if s == "discrepancy") == sorted(rejected), v
    assert all(s == "pass" for c, (s, _) in v.items() if c not in rejected), v


def test_int_var_text_group_over_accepted_item_88(al_parser):
    root = al_parser.parse(INT_VAR_TEXT_GROUP).root_node
    assert not root.has_error
    assert ("(variable_declaration name: (identifier) type: (basic_type) "
            "(preproc_conditional_label_attributes ") in str(root)
    v = witness.verdicts(al_parser, INT_VAR_TEXT_GROUP)
    assert v["X=0"][0] == "discrepancy" and v["X=1"][0] == "pass", v


def test_caption_group_unwraps_to_a_bare_text_when_nothing_is_selected(al_parser):
    witness.assert_produces(al_parser, CAPTION, "preproc_conditional_caption_subfields")
    v = witness.verdicts(al_parser, CAPTION)
    assert all(s == "pass" for s, _ in v.values()), v
    assert any("caption-value-unwrap" in i for i in v["X=0"][1]), v
    assert not any("caption-value-unwrap" in i for i in v["X=1"][1]), v


@pytest.mark.parametrize("src,group", [
    (REPORT_LABEL, "preproc_conditional_report_label_attributes"),
    (LABEL_VAR, "preproc_conditional_label_attributes"),
    (LABEL_VALUE_ARM, "preproc_conditional_report_label_attributes"),
])
def test_label_tail_groups_lower_every_config(al_parser, src, group):
    witness.assert_produces(al_parser, src, group)
    v = witness.verdicts(al_parser, src)
    assert all(s == "pass" for s, _ in v.values()), v
