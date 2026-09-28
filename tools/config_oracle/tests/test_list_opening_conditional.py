"""A #if that OPENS a list continued after #endif is list-internal (G11,
docs/deferred-work.md item 18). Since G8 the unquoted link form was a silent
misparse: a terminator-less whole-value property, then a second property named
after the next link's field. Every configuration must match its flat parse."""
import pytest

from tools.config_oracle.tests import witness


def _part(link):
    return (f"page 50100 P\n{{\n    layout\n    {{\n        area(Content)\n        {{\n"
            f"            part(L; Q)\n            {{\n                SubPageLink =\n{link}\n"
            f"            }}\n        }}\n    }}\n}}\n").encode()


def _action(link):
    return (f"page 50100 P\n{{\n    actions\n    {{\n        area(Processing)\n        {{\n"
            f"            action(A)\n            {{\n                RunObject = page Q;\n"
            f"                RunPageLink =\n{link}\n            }}\n        }}\n    }}\n}}\n").encode()


UNQUOTED = "#if X\n                    A = field(B),\n#endif\n                    B = field(A);"
QUOTED = "#if X\n                    \"A\" = field(B),\n#endif\n                    \"C\" = field(D);"

LINK_OPENING = {
    "unquoted": _part(UNQUOTED),
    "quoted": _part(QUOTED),
    "runpagelink": _action(UNQUOTED),
}


@pytest.mark.parametrize("name", sorted(LINK_OPENING))
def test_link_list_opened_by_if_every_config(al_parser, name):
    src = LINK_OPENING[name]
    witness.assert_produces(al_parser, src, "preproc_conditional_link_values")
    v = witness.verdicts(al_parser, src)
    assert len(v) == 2, v
    witness.assert_all_pass(al_parser, src)


def _options(members):
    return (f"table 50100 T\n{{\n    fields\n    {{\n        field(1; F; Option)\n        {{\n"
            f"            OptionMembers =\n{members}\n        }}\n    }}\n}}\n").encode()


# G11 item 2: an option-member list opened by a #if. It ERRORed until G11.
OPTION_OPENING = {
    "continued": _options("#if X\n                A,\n#endif\n                B, C;"),
    "both-arms": _options("#if X\n                A,\n#else\n                B,\n#endif\n                C;"),
    # X=0 leaves one member; its flat parse is a bare identifier
    # (engine.OPTION_MEMBER_BARE_KINDS, rewrite option-member-list-unwrap).
    "one-after": _options("#if X\n                A,\n#endif\n                B;"),
}


@pytest.mark.parametrize("name", sorted(OPTION_OPENING))
def test_option_list_opened_by_if_every_config(al_parser, name):
    src = OPTION_OPENING[name]
    witness.assert_produces(al_parser, src, "preproc_conditional_option_members")
    v = witness.verdicts(al_parser, src)
    assert len(v) == 2, v
    witness.assert_all_pass(al_parser, src)


def test_single_member_without_unwrap_is_caught(al_parser, monkeypatch):
    # Unmutated, every configuration passes (above). Without the rewrite the
    # one-member configuration keeps the list the flat parse does not have.
    from tools.config_oracle.lowering import engine
    monkeypatch.setattr(engine, "OPTION_MEMBER_BARE_KINDS", frozenset())
    v = witness.verdicts(al_parser, OPTION_OPENING["one-after"])
    assert v["X=0"][0] == "discrepancy" and v["X=1"][0] == "pass", v


def test_single_member_unwrap_is_recorded_only_where_it_fires(al_parser):
    v = witness.verdicts(al_parser, OPTION_OPENING["one-after"])
    unwrap = lambda items: [i for i in items if i.startswith("normalised:option-member-list-unwrap@")]
    assert v["X=0"][0] == "pass" and len(unwrap(v["X=0"][1])) == 1, v
    assert v["X=1"][0] == "pass" and not unwrap(v["X=1"][1]), v
