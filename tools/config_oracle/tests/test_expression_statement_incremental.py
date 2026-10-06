"""B6: incremental re-parse after an edit equals a fresh parse, across the new fork."""
import pytest

from tools.config_oracle.tests.test_link_incremental import _edit

HOST = (b"codeunit 50101 P {\n  procedure Main()\n  var X: Integer; C: Boolean;\n"
        b"  begin\n%s\n  end;\n}\n")

EDITS = [
    (b"Foo();", b"1 + Foo();"),
    (b"1 + Foo();", b"Foo();"),
    (b"Foo();", b"(Foo());"),
    (b"(Foo());", b"Foo();"),
    (b"Foo();\n  Bar();", b"Foo()\n  Bar();"),
    (b"Order();", b"Order;"),
    (b"Order;", b"Order();"),
    (b"X := 1;\n  Foo();", b"X := 1\n#if A\n  + 2\n#endif\n  ;\n  Foo();"),
    (b"X := 1\n#if A\n  + 2\n#endif\n  ;\n  Foo();", b"X := 1;\n  Foo();"),
    (b"X := 1\n#if A\n  + 2\n#endif\n  ;", b"X := 1;\n#if A\n  Foo();\n#endif"),
    (b"X := 1;\n#if A\n  Foo();\n#endif", b"X := 1\n#if A\n  + 2\n#endif\n  ;"),
    (b"Foo(C);", b"and(C);"),
    (b"and(C);", b"Foo(C);"),
]


@pytest.mark.parametrize("before,after", EDITS, ids=repr)
def test_incremental_equals_fresh(al_parser, before, after):
    incremental = _edit(al_parser, HOST % before, HOST % after)
    fresh = al_parser.parse(HOST % after)
    assert str(incremental.root_node) == str(fresh.root_node)
    assert incremental.root_node.has_error == fresh.root_node.has_error
