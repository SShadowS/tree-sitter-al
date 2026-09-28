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
