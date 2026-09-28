"""split-procedure over every _procedure_tail form (spec P5.1)."""
import pytest

from tools.config_oracle.tests import witness

HEAD = b"codeunit 1 T\n{\n#if A\n    procedure P(x: Integer)\n#else\n    procedure P(x: Integer; y: Integer)\n#endif\n"
TAILS = {
    "regular": b"    begin\n    end;\n}\n",
    "var-and-body": b"    var\n        i: Integer;\n    begin\n    end;\n}\n",
    "pragma-only": b"#if B\n#pragma warning disable AL0432\n#endif\n    begin\n    end;\n}\n",
    "split-body": b"#if B\n    var\n        i: Integer;\n    begin\n        i := 1;\n#else\n    begin\n#endif\n        Message('x');\n    end;\n}\n",
    "split-body-else-stmts": b"#if B\n    var\n        i: Integer;\n    begin\n        i := 1;\n#else\n    begin\n        Message('e');\n#endif\n    end;\n}\n",
    "complete-body": b"#if B\n    begin\n        Message('a');\n    end;\n#else\n    begin\n        Message('b');\n    end;\n#endif\n}\n",
}


# Tails whose own special type is already lowered end-to-end (milestone 2):
# these must pass every configuration outright, not just avoid a discrepancy.
_FULLY_SUPPORTED = {"regular", "var-and-body", "pragma-only"}


@pytest.mark.parametrize("tail", sorted(TAILS))
def test_split_procedure_tail(al_parser, tail):
    src = HEAD + TAILS[tail]
    witness.assert_produces(al_parser, src, "preproc_split_procedure")
    v = witness.verdicts(al_parser, src)
    # The tail's own special type may still be milestone-3 (split body). What
    # must never happen is a discrepancy, or a lowering error from split_procedure.
    for c, (s, items) in v.items():
        assert s != "discrepancy", (c, items)
        assert not any(i.startswith("lowering:contract-shape") for i in items), (c, items)
    if tail in _FULLY_SUPPORTED:
        witness.assert_all_pass(al_parser, src)


def test_trigger_host_takes_the_same_tails(al_parser):
    src = b"codeunit 1 T\n{\n    trigger OnRun()\n#if B\n#pragma warning disable AL0432\n#endif\n    begin\n    end;\n}\n"
    witness.assert_all_pass(al_parser, src)
