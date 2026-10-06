"""B11 groundwork (spec 2026-10-05-property-value-runs-design.md section 5.3): debt owners, ordered
standalone `;`, Implementation list-run lowering, list-value-empty, OptionMembers holes."""
import pytest

from tools.config_oracle import fixtures
from tools.config_oracle.tests import witness


@pytest.mark.parametrize("owner", ["B10", "B11", "B12", "B13"])
def test_roadmap_owners(owner):
    assert owner in fixtures.ROADMAP


IMPL = b"""interface IFoo { procedure Bar(); }
interface IBar { procedure Baz(); }
codeunit 50104 FooImpl implements IFoo { procedure Bar() begin end; }
codeunit 50106 BarImpl implements IBar { procedure Baz() begin end; }
enum 50105 E implements IFoo, IBar
{
    value(0; A)
    {
        Implementation =
#if X
            IFoo = FooImpl,
#endif
#if Y
            IBar = BarImpl
#endif
        ;
    }
}
"""


def test_impl_element_conditionals_lower(al_parser):
    witness.assert_produces(al_parser, IMPL, "preproc_conditional_impl_values")
    v = witness.verdicts(al_parser, IMPL)
    assert v["X=1,Y=1"][0] == "pass", v
    # X only: `IFoo = FooImpl, ;` -- the trailing `,` is refused by the strict check
    assert v["X=1,Y=0"][0] == "cannot-validate", v
    assert v["X=1,Y=0"][1][0].startswith("lowering:list-separator"), v
    assert v["X=0,Y=1"][0] == "pass", v
    assert v["X=0,Y=0"][0] == "pass", v      # list-value-empty: `Implementation = ;`
    assert any("list-value-empty:implementation_value_list" in i for i in v["X=0,Y=0"][1]), v


LINK_EMPTY = b"""table 50101 Cust { fields { field(1; A; Code[20]) { } field(2; B; Code[20]) { } } }
page 50103 L { PageType = ListPart; SourceTable = Cust; layout { area(Content) { repeater(R) { field(F; Rec.A) { } } } } }
page 50100 P
{
    SourceTable = Cust;
    layout { area(Content) { part(P; L) {
        SubPageLink =
#if X
            A = field(B)
#endif
#if Y
            B = field(A)
#endif
        ;
    } } }
}
"""


def test_link_list_emptied_is_removed(al_parser):
    witness.assert_produces(al_parser, LINK_EMPTY, "preproc_conditional_link_values")
    v = witness.verdicts(al_parser, LINK_EMPTY)
    assert v["X=0,Y=0"][0] == "pass", v
    assert any("list-value-empty:link_value_list" in i for i in v["X=0,Y=0"][1]), v


# Three Terminator fragments for ONE property (X=Y=Z=1): the arm `;` of each nesting level and
# the property's own `;`. Two reach the mixed-placement branch; before the fix each got its own
# SiblingsAfter and the second came out before the first.
SEMIS = b"""page 50100 P
{
    layout { area(Content) { field(F; X) {
        Caption =
#if X
#if Y
#if Z
            'a';
#endif
        ;
#endif
        ;
#endif
        ;
    } } }
}
"""


def test_three_semicolons_keep_source_order(al_parser):
    witness.assert_all_pass(al_parser, SEMIS)


OPTION_HOLES = b"""table 50100 T { fields { field(1; F; Option) {
    OptionMembers =
#if X
        A,
#endif
        B,,C;
} } }
"""


def test_option_members_holes_are_legal(al_parser):
    witness.assert_all_pass(al_parser, OPTION_HOLES)


# B11 Task 6 (spec 5.3, step 3): the entirely conditional OptionMembers run.
OPT_RUN = b"""table 50100 T { fields { field(1; F; Option) {
    OptionMembers =
#if X
        A,
#endif
#if Y
        B
#endif
    ;
} } }
"""


def test_option_entire_run_every_config(al_parser):
    witness.assert_produces(al_parser, OPT_RUN, "preproc_conditional_option_members")
    v = witness.verdicts(al_parser, OPT_RUN)
    assert all(s == "pass" for s, _ in v.values()), v
    # selects nothing: an emptied option list at the property site (alc rejects it, AL0153:
    # recorded structural over-acceptance, tools/alc_probe/cases/value-runs/optionmembers-selects-nothing.al)
    assert any("list-value-empty:option_member_list" in i for i in v["X=0,Y=0"][1]), v
    # one bare member left: the one-member unwrap
    assert any("option-member-list-unwrap" in i for i in v["X=0,Y=1"][1]), v


# Two members side by side, no separator (X undefined, Y defined: `A B`): the hole-aware check
# still refuses a missing separator. Holes are `,` without a member, never a member without `,`.
OPT_ADJACENT = b"""table 50100 T { fields { field(1; F; Option) {
    OptionMembers =
#if X
        A,
#else
        A
#endif
#if Y
        B
#endif
    ;
} } }
"""


def test_option_adjacent_members_raise_list_separator(al_parser, monkeypatch):
    witness.assert_produces(al_parser, OPT_ADJACENT, "preproc_conditional_option_members")
    v = witness.verdicts(al_parser, OPT_ADJACENT)
    assert v["X=1,Y=1"][0] == "pass", v
    # The reference parse of `A B` refuses first (reference-error) ...
    assert v["X=0,Y=1"][1][0].startswith("reference-error"), v
    # ... and with the reference's verdict suppressed, the hole-aware list check refuses it too.
    from tools.config_oracle import runner
    real = runner.reference.extract

    def no_problems(parser, text):
        r = real(parser, text)
        r.problems = []
        return r
    monkeypatch.setattr(runner.reference, "extract", no_problems)
    v = witness.verdicts(al_parser, OPT_ADJACENT)
    assert v["X=0,Y=1"][0] == "cannot-validate", v
    assert v["X=0,Y=1"][1][0].startswith("lowering:list-separator"), v


# list-value-empty at a whole-value ARM site: the option list is the value of an arm of a
# preproc_conditional_property_value (W defined), and X, Y undefined empty it.
OPT_ARM_EMPTY = b"""table 50100 T { fields { field(1; F; Option) {
    OptionMembers =
#if W
#if X
        A,
#endif
#if Y
        B
#endif
#else
        C
#endif
    ;
} } }
"""


def test_option_list_emptied_at_arm_site(al_parser):
    t = al_parser.parse(OPT_ARM_EMPTY).root_node
    stack = [t]; lists = []
    while stack:
        n = stack.pop()
        if n.type == "option_member_list":
            lists.append(n)
        stack.extend(n.children)
    assert [n.parent.type for n in lists] == ["preproc_conditional_property_value"], lists
    v = witness.verdicts(al_parser, OPT_ARM_EMPTY)
    hits = [c for c, (s, items) in v.items()
            if s == "pass" and any("list-value-empty:option_member_list" in i for i in items)]
    assert "W=1,X=0,Y=0" in hits, v
