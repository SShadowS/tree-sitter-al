"""B7b-3 Task 4: an incremental re-parse after a call-terminator edit equals a fresh parse. `call_statement` owns
no `;` any more, so adding or removing the `;` after a parenless call (plain, and inside an `#if` arm) must give
the same tree as parsing the edited source from scratch. Comparison: the full cursor tree (every node, named and
anonymous, field, type, MISSING flag, byte span), as in test_strict_lists_incremental.py."""
import pytest

from tools.config_oracle.tests.test_strict_lists_incremental import _dump, _edit

HOST = b"codeunit 50100 C\n{\n    procedure M()\n    begin\n%s\n    end;\n}\n"

EDITS = [
    (b"        Bar", b"        Bar;"),                                              # `;` added
    (b"        Bar;", b"        Bar"),                                              # `;` removed
    (b"        Bar\n        Baz;", b"        Bar;\n        Baz;"),                  # before another call
    (b"        Bar;\n        Baz;", b"        Bar\n        Baz;"),
    (b"#if X\n        Bar\n#endif", b"#if X\n        Bar;\n#endif"),                  # inside an arm
    (b"#if X\n        Bar;\n#endif", b"#if X\n        Bar\n#endif"),
    (b"        if Ok then Bar\n#if X\n#endif", b"        if Ok then Bar\n#if X\n;\n#endif"),   # into the arm
    (b"        if Ok then Bar\n#if X\n;\n#endif", b"        if Ok then Bar\n#if X\n#endif\n;"),  # out of it
    (b"        if Ok then Bar\n#if X\n#endif\n;", b"        if Ok then Bar;\n#if X\n#endif"),
]


@pytest.mark.parametrize("before,after", EDITS)
def test_incremental_call_terminator_edits(al_parser, before, after):
    old_src, new_src = HOST % before, HOST % after
    fresh = al_parser.parse(new_src)
    assert not fresh.root_node.has_error, new_src.decode()
    incremental = _edit(al_parser, old_src, new_src)
    assert _dump(incremental.root_node) == _dump(fresh.root_node)
    assert "call_statement" in {t for _, t, *_ in _dump(fresh.root_node)}
