"""Named normalisation arm-terminator (B7b-0, user ruling Option A, 2026-10-07).

A statement's `;` alone in an `#if` arm (`I := 1` / `#if X` / `;` / `#endif`) is its own
`empty_statement` inside the conditional, and that tree is correct. Where the arm is selected
the flat reading gives the `;` as the preceding statement's separator, so the oracle lowers it
that way, in every statement host, top level and nested. A lone `;` arm with no statement right
before it stays an empty_statement.
"""
from tools.config_oracle.tests import witness

W = "codeunit 1 T\n{\n    procedure P(C: Boolean)\n    var\n        I: Integer;\n    begin\n%s\n    end;\n}\n"


def src(body):
    return (W % body).encode()


def notes(v, config):
    return [i for i in v[config][1] if i.startswith("normalised:arm-terminator@")]


TOP = src("        I := 1\n#if X\n        ;\n#endif\n        I := 2;")
NESTED_BLOCK = src("        if C then begin\n            I := 1\n#if X\n            ;\n#endif\n"
                   "            I := 2;\n        end;")
# The statement inside an outer arm, and the statement before an outer group (the lone-`;`
# group nested in it): both are a conditional-statement host.
IN_COND = src("#if Y\n        I := 1\n#if X\n        ;\n#endif\n#endif")
OUTER_COND = src("        I := 1\n#if Y\n#if X\n        ;\n#endif\n#endif")
# A supported split-if (preproc_split_else_begin_over_endif): the else block's statements.
SPLIT_IF = (b"codeunit 1 T\n{\n    procedure P(C: Boolean)\n    begin\n        if C then begin\n            A();\n"
            b"#if X\n        end else begin\n            B()\n#if Z\n            ;\n#endif\n#endif\n        end;\n"
            b"    end;\n}\n")
# The lone-`;` group after the split's #endif: with X=0 the tail is appended to the then block
# (BlockCompletion), after the statement `A()` already in its body.
SPLIT_IF_TAIL = (b"codeunit 1 T\n{\n    procedure P(C: Boolean)\n    begin\n        if C then begin\n            A()\n"
                 b"#if X\n        end else begin\n            B();\n#endif\n#if Z\n            ;\n#endif\n        end;\n"
                 b"    end;\n}\n")
ELSE_ARMS = src("        I := 1\n#if X\n        ;\n#else\n        ;\n#endif\n        I := 2;")
COMMENTS = src("        I := 1\n#if X\n        // c\n        ; // d\n#else\n        /* e */ ;\n#endif\n        I := 2;")
NO_STATEMENT = src("#if X\n        ;\n#endif\n        I := 2;")
AFTER_SEPARATOR = src("        I := 1;\n#if X\n        ;\n#endif\n        I := 2;")


def test_top_level(al_parser):
    witness.assert_produces(al_parser, TOP, "preproc_conditional_statement")
    witness.assert_all_pass(al_parser, TOP)
    v = witness.verdicts(al_parser, TOP)
    assert notes(v, "X=1") and not notes(v, "X=0"), v


def test_nested_statement_block(al_parser):
    witness.assert_all_pass(al_parser, NESTED_BLOCK)
    assert notes(witness.verdicts(al_parser, NESTED_BLOCK), "X=1")


def test_inside_a_conditional_statement(al_parser):
    witness.assert_all_pass(al_parser, IN_COND)
    assert notes(witness.verdicts(al_parser, IN_COND), "X=1,Y=1")


def test_group_nested_in_an_outer_group(al_parser):
    witness.assert_all_pass(al_parser, OUTER_COND)
    assert notes(witness.verdicts(al_parser, OUTER_COND), "X=1,Y=1")


def test_inside_a_split_if(al_parser):
    witness.assert_produces(al_parser, SPLIT_IF, "preproc_split_else_begin_over_endif")
    witness.assert_all_pass(al_parser, SPLIT_IF)
    assert notes(witness.verdicts(al_parser, SPLIT_IF), "X=1,Z=1")


def test_split_if_tail_completes_the_block(al_parser):
    witness.assert_produces(al_parser, SPLIT_IF_TAIL, "preproc_split_else_begin_over_endif")
    witness.assert_all_pass(al_parser, SPLIT_IF_TAIL)
    v = witness.verdicts(al_parser, SPLIT_IF_TAIL)
    assert notes(v, "X=0,Z=1") and not notes(v, "X=1,Z=1"), v


def test_else_arms(al_parser):
    witness.assert_all_pass(al_parser, ELSE_ARMS)
    v = witness.verdicts(al_parser, ELSE_ARMS)
    assert notes(v, "X=0") and notes(v, "X=1"), v


def test_comments_around_the_semicolon(al_parser):
    witness.assert_all_pass(al_parser, COMMENTS)
    v = witness.verdicts(al_parser, COMMENTS)
    assert notes(v, "X=0") and notes(v, "X=1"), v


def test_no_statement_before_stays_empty_statement(al_parser):
    """NEGATIVE: the flat reading is a lone `;`, an empty_statement; nothing absorbs it."""
    witness.assert_all_pass(al_parser, NO_STATEMENT)
    assert not notes(witness.verdicts(al_parser, NO_STATEMENT), "X=1")


def test_statement_already_terminated_stays_empty_statement(al_parser):
    """NEGATIVE: `I := 1; ;` flat: the second `;` is an empty_statement, not a separator."""
    witness.assert_all_pass(al_parser, AFTER_SEPARATOR)
    assert not notes(witness.verdicts(al_parser, AFTER_SEPARATOR), "X=1")
