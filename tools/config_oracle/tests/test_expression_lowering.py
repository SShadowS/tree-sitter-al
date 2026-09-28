import pytest

from tools.config_oracle.tests import witness

TAIL_ASSIGN = b"codeunit 1 T\n{\n    trigger OnRun()\n    begin\n        r := 1\n#if X\n            + 2\n#endif\n            * 3;\n    end;\n}\n"
TAIL_ARG = b"codeunit 1 T\n{\n    trigger OnRun()\n    begin\n        F(2\n#if X\n            + 1\n#endif\n            , 3);\n    end;\n}\n"
TAIL_OPERAND = b"codeunit 1 T\n{\n    trigger OnRun()\n    begin\n        r := 1\n#if X\n            * 2 + 3\n#endif\n            ;\n    end;\n}\n"
PREFIX = b"codeunit 1 T\n{\n    trigger OnRun()\n    begin\n        r := 1 +\n#if X\n            2 *\n#else\n            4 -\n#endif\n            5;\n    end;\n}\n"


def _stmt(s):
    return (b"codeunit 1 T\n{\n    procedure P() r: Integer\n    var\n        i: Integer;\n"
            b"        a: array[10] of Integer;\n    begin\n" + s + b"\n    end;\n}\n")


# Every host position of the tail, each taken from the corpus fixture that pins it
# (grep -ln preproc_conditional_expression_tail test/corpus/*.txt), in a trigger/procedure
# the lowering reaches. The #elif and trailing-pair arms are exercised by TAIL_ELIF.
POSITIONS = {
    # preproc_exit_continuation_test.txt
    "exit": _stmt(b"        exit(1\n#if X\n            + 2\n#endif\n            );"),
    # preproc_cond_continuation_test.txt: the tail extends a comparison, so `+` must bind tighter
    "if-condition": _stmt(b"        if i = 1\n#if X\n            + 2\n#endif\n            then i := 0;"),
    # preproc_property_continuation_test.txt
    "property": b"table 1 D\n{\n    fields\n    {\n        field(1; F; Integer)\n        {\n"
                b"            MinValue = 1\n#if X\n                + 2\n#endif\n                ;\n"
                b"        }\n    }\n}\n",
    # preproc_forbound_continuation_test.txt
    "for-bound": _stmt(b"        for i := 1 to r\n#if X\n            + 2\n#endif\n            do r := 0;"),
    # preproc_whilec_continuation_test.txt
    "while-condition": _stmt(b"        while i < 1\n#if X\n            + 2\n#endif\n            do i := i + 1;"),
    # preproc_subscript_continuation_test.txt
    "subscript": _stmt(b"        i := a[1\n#if X\n            + 2\n#endif\n            ];"),
    "list-literal": _stmt(b"        if i in [1\n#if X\n            + 2\n#endif\n            ] then i := 0;"),
}
TAIL_ELIF = _stmt(b"        r := 1\n#if X\n            * 2\n#elif Y\n            - 4 * 5\n#else\n"
                  b"            or 6\n#endif\n            + 7 * 8;")


@pytest.mark.parametrize("src,kind", [(TAIL_ASSIGN, "preproc_conditional_expression_tail"),
                                      (TAIL_ARG, "preproc_conditional_expression_tail"),
                                      (PREFIX, "preproc_operand_prefix")])
def test_every_config_passes(al_parser, src, kind):
    witness.assert_produces(al_parser, src, kind)
    witness.assert_all_pass(al_parser, src)


# Grammar finding G5: a continued property value is property_expression(expr, tail),
# the wrapper flat `MinValue = 1 * 3 + 2;` gives. The "property" position above has
# a SIMPLE prefix, whose X=0 flat parse is a bare `integer` (property-expression-unwrap);
# this one has a BINARY prefix, wrapped in every configuration.
PROPERTY_BINARY_PREFIX = POSITIONS["property"].replace(b"MinValue = 1" + bytes([10]), b"MinValue = 1 * 3" + bytes([10]))
assert PROPERTY_BINARY_PREFIX != POSITIONS["property"]


def test_g5_property_binary_prefix_passes(al_parser):
    witness.assert_produces(al_parser, PROPERTY_BINARY_PREFIX, "preproc_conditional_expression_tail")
    witness.assert_all_pass(al_parser, PROPERTY_BINARY_PREFIX)


@pytest.mark.parametrize("name", sorted(POSITIONS))
def test_every_tail_position_passes(al_parser, name):
    witness.assert_produces(al_parser, POSITIONS[name], "preproc_conditional_expression_tail")
    witness.assert_all_pass(al_parser, POSITIONS[name])


def test_elif_arms_and_trailing_pairs(al_parser):
    witness.assert_produces(al_parser, TAIL_ELIF, "preproc_conditional_expression_tail")
    witness.assert_all_pass(al_parser, TAIL_ELIF)


def test_operand_is_regrouped(al_parser):
    witness.assert_all_pass(al_parser, TAIL_OPERAND)


def test_naive_append_is_caught(al_parser, monkeypatch):
    from tools.config_oracle.lowering import expression
    monkeypatch.setattr(expression, "LEVEL", {k: 1 for k in expression.LEVEL})  # no precedence
    v = witness.verdicts(al_parser, TAIL_ASSIGN)
    assert any(s == "discrepancy" for s, _ in v.values()), v


def test_prefix_without_precedence_is_caught(al_parser, monkeypatch):
    from tools.config_oracle.lowering import expression
    monkeypatch.setattr(expression, "LEVEL", {k: 1 for k in expression.LEVEL})
    v = witness.verdicts(al_parser, PREFIX)
    assert any(s == "discrepancy" for s, _ in v.values()), v


# The prefix's own binary node is `a * <prefix> c`, under an ORDINARY `... + d`. With X
# the text is `a * b or c + d` = `(a*b) or (c+d)`: the arm's `or` escapes both nodes, so
# regrouping only the prefix's node would give `((a*b) or c) + d`.
PREFIX_ESCAPES = b"codeunit 1 T\n{\n    trigger OnRun()\n    begin\n        r := a *\n#if X\n            b or\n#endif\n            c + d;\n    end;\n}\n"
# test/corpus/preproc_dangling_operator_continuation_test.txt: two prefixes in one chain.
PREFIX_TWICE = (b"codeunit 1 T\n{\n    procedure P() IsChanged: Boolean\n    begin\n"
                b"        IsChanged := (Rec.A <> xRec.A) or\n#if not CLEAN27\n          (Rec.B <> xRec.B) or\n"
                b"#endif\n          (Rec.C <> xRec.C) or\n#if not CLEAN27\n          (Rec.D <> xRec.D) or\n"
                b"          (Rec.E <> xRec.E) or\n#endif\n          (Rec.F <> xRec.F);\n    end;\n}\n")


@pytest.mark.parametrize("src", [PREFIX_ESCAPES, PREFIX_TWICE], ids=["escapes", "twice"])
def test_prefix_regroups_the_whole_chain(al_parser, src):
    witness.assert_produces(al_parser, src, "preproc_operand_prefix")
    witness.assert_all_pass(al_parser, src)


# The tail inside a preproc_conditional_arguments arm binds within that arm (select.branch_select).
TAIL_IN_ARGUMENTS = (b"codeunit 1 T\n{\n    trigger OnRun()\n    begin\n        F(1\n#if X\n            , 2\n"
                     b"#if Y\n            + 3\n#endif\n            , 4\n#endif\n            );\n    end;\n}\n")


def test_tail_inside_an_arguments_arm(al_parser):
    witness.assert_produces(al_parser, TAIL_IN_ARGUMENTS, "preproc_conditional_arguments")
    witness.assert_produces(al_parser, TAIL_IN_ARGUMENTS, "preproc_conditional_expression_tail")
    witness.assert_all_pass(al_parser, TAIL_IN_ARGUMENTS)
