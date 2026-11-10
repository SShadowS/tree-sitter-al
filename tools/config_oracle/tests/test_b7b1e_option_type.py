"""B7b-1e (deferred item 46): #if groups in an Option TYPE's member list lower like the keyed
OptionMembers list; a configuration that selects no member leaves a bare `Option`."""
from tools.config_oracle.tests import witness

OPT_TYPE = b"""codeunit 50100 P
{
    var
        V: Option A
#if X
            , B
#elif Y
            , C
#endif
            , D;
        W: Option
#if X
            A, B
#endif
            ;

    procedure F(Q: Option A
#if X
        , B
#endif
        ; R: Integer)
    begin
    end;
}
"""


def test_option_type_groups_lower_every_config(al_parser):
    witness.assert_produces(al_parser, OPT_TYPE, "preproc_conditional_option_members")
    v = witness.verdicts(al_parser, OPT_TYPE)
    assert all(s == "pass" for s, _ in v.values()), v
    # X undefined: `W: Option;`, the emptied list is removed, not refused as an empty node
    assert any("list-value-empty:option_member_list" in i for i in v["X=0,Y=0"][1]), v
    assert not any("list-value-empty" in i for i in v["X=1,Y=0"][1]), v


# Two members side by side in one configuration (X=1: `A B C`, X=0: `A C`): refused per
# configuration, never a silent pass (item 44: the parse itself over-accepts).
OPT_TYPE_ADJACENT = b"""codeunit 50100 P
{
    var
        V: Option A
#if X
            B
#endif
            C;
}
"""


def test_option_type_adjacent_members_never_pass(al_parser):
    v = witness.verdicts(al_parser, OPT_TYPE_ADJACENT)
    assert v and all(s != "pass" for s, _ in v.values()), v
