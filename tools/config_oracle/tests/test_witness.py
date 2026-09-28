from tools.config_oracle.tests import witness

SRC = b"codeunit 1 T\n{\n    trigger OnRun()\n    begin\n#if A\n        x := 1;\n#endif\n    end;\n}\n"


def test_assert_all_pass_on_a_supported_shape(al_parser):
    witness.assert_produces(al_parser, SRC, "preproc_conditional_statement")
    witness.assert_all_pass(al_parser, SRC)
