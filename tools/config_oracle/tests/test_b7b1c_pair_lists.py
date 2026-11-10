"""B7b-1c (deferred item 46): #if groups in an ML / Namespaces pair list lower by branch selection;
a TextConst list emptied by its groups leaves the flat `T: TextConst;` shape."""
from tools.config_oracle.tests import witness

TEXTCONST_EMPTY = b"""codeunit 50100 C
{
    var
        T: TextConst
#if X
            ENU = 'a', DAN = 'b'
#endif
            ;
}
"""

ML_GROUPS = b"""page 50100 P
{
    CaptionML = ENU = 'a'
#if X
        , DAN = 'b'
#elif Y
        , FRA = 'c'
#endif
        , DEU = 'd';
}
"""


def test_textconst_emptied_list_is_a_plain_textconst(al_parser):
    witness.assert_produces(al_parser, TEXTCONST_EMPTY, "preproc_conditional_ml_pairs")
    v = witness.verdicts(al_parser, TEXTCONST_EMPTY)
    assert v["X=0"][0] == "pass", v
    assert any("textconst-list-removed" in i for i in v["X=0"][1]), v
    assert v["X=1"][0] == "pass" and not any("textconst-list-removed" in i for i in v["X=1"][1]), v


def test_ml_groups_lower_every_config(al_parser):
    witness.assert_produces(al_parser, ML_GROUPS, "preproc_conditional_ml_pairs")
    v = witness.verdicts(al_parser, ML_GROUPS)
    assert all(s == "pass" for s, _ in v.values()), v
