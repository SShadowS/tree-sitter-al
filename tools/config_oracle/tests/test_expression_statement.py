"""B6: a statement expression is an invocation; operator words are not names in code.

Spec docs/superpowers/specs/2026-10-06-expression-statement-narrowing-design.md; alc evidence
tools/alc_probe/cases/expression-statement. has_error, not the ERROR count, is the contract:
it is the only view that also sees a MISSING hidden token (CLAUDE.md).
"""
import pytest

HOST = (b"codeunit 50101 P {\n"
        b"  procedure Main()\n"
        b"  var Rec: Record T; X: Integer; Arr: array[3] of Integer; C: Boolean;\n"
        b"  begin\n%s\n  end;\n}\n")

# Valid AL (alc ACCEPT) or symbol-dependent (alc AL0117 only with symbols): must parse clean.
ACCEPT = [
    b"Foo();",
    b"Rec.Get();",
    b"Rec.Reset;",
    b"Bar",                                   # parenless, no `;`, before end
    b"if C then Bar else Foo();",             # parenless before else
    b'"My Proc";',
    b'"My Proc"',
    b"Order;",
    b"Table",
    b"if C then Order else Table;",
    b"Continue(X);",
    b'"and"(C);',
    b"is(C);",
    b"as(C);",
    b"Rec.is;",
    b"this.Foo();",
    b"Codeunit.Run(Codeunit::\"X\");",
    b"Arr[1].Reset;",
    b"X;",                                    # AL0117 needs symbols: parser accepts
    b"Rec.Name;",                             # likewise
    b"X := 1\n#if A\n  + 2\n#endif\n  ;",
    b"X := 1\n#if A\n  and (C)\n#else\n  or (C)\n#endif\n  ;",
    b"X := 1\n#if A\n  +\n#else\n  -\n#endif\n  2;",
    b"#if A\n  Foo();\n#else\n  Bar;\n#endif",
    b"X := 1;\n#if A\n  Foo();\n#endif\n  Bar();",
]

# Invalid AL (alc AL0104 / AL0117 decidable without symbols / AL0224): must ERROR.
REJECT = [
    b"1;", b"'abc';", b"1 + 2;", b"+ 3;", b"-Foo();", b"not Foo();", b"(Foo());",
    b"Rec.Get() = true;", b"Arr[1];", b"Foo()[1];",
    b"and(C);", b"or(C);", b"xor(C);", b"div(C);", b"mod(C);", b"in(C);", b"not(C);",
    b"and := true;", b"C := and;",
    b"Foo()\n#if A\n  + 2\n#endif\n  ;",
    b"Foo()\n#if A\n  or (2 = 2)\n#endif\n  ;",
    b"exit(1)\n#if A\n  + 2\n#endif\n  ;",
]

# Valid AL in every configuration that B6 makes LOUD and B7 must parse (spec §7).
B7_GAP = [
    b"repeat Foo(); until C\n#if A\n  and (C)\n#endif\n  ;",
    # alc accepts it in both configurations; needs a `;`-inside-arms assignment continuation.
    b"B := A\n#if A\n  + 1;\n  Foo();\n#else\n  ;\n#endif",
]


@pytest.mark.parametrize("stmt", ACCEPT, ids=repr)
def test_accepted_statement_parses_clean(al_parser, stmt):
    assert al_parser.parse(HOST % stmt).root_node.has_error is False


@pytest.mark.parametrize("stmt", REJECT, ids=repr)
def test_rejected_statement_errors(al_parser, stmt):
    assert al_parser.parse(HOST % stmt).root_node.has_error is True


@pytest.mark.parametrize("stmt", B7_GAP, ids=repr)
def test_b7_gap_is_loud_not_silent(al_parser, stmt):
    assert al_parser.parse(HOST % stmt).root_node.has_error is True


DECLARATIONS = [
    b"enum 50100 E { value(0; and) { } value(1; or) { } value(2; in) { } value(3; mod) { } }\n",
    b"table 50100 T { fields { field(1; div; Integer) { } field(2; K; Option) { OptionMembers = and,or,is; } } }\n",
    b"codeunit 50102 Q { procedure and(X: Boolean) begin end; var \"and\": Boolean; }\n",
]


@pytest.mark.parametrize("src", DECLARATIONS, ids=repr)
def test_operator_words_still_declare(al_parser, src):
    assert al_parser.parse(src).root_node.has_error is False
