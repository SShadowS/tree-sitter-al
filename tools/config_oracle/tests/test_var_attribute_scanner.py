"""B7b-1 Task 12: the var_attribute_open lookahead over conditional name streams (src/scanner.c
var_name_list_follows, spec 5.2).

`has_error` is the gate here, not `tree-sitter parse`: a wrong scanner decision can leave a MISSING hidden
token that the CLI does not print. The corpus fixture pins the trees; this module checks every case of it
with has_error, that a declined shape never yields a var_attribute_open, and that an incremental reparse
after an unchanged `[A]` prefix equals a fresh parse (the lookahead reads far past its one-byte token).
"""
from pathlib import Path

import pytest

from tools.config_oracle import fixtures

REPO = Path(__file__).resolve().parents[3]
FIXTURE = "strict_conditional_var_names_attr_test.txt"


def _cases():
    return [c for c in fixtures.extract(REPO / "test" / "corpus") if c.file == FIXTURE]


def _kinds(node, out=None):
    out = [] if out is None else out
    out.append(node.type)
    for child in node.children:
        _kinds(child, out)
    return out


def _var(decls: bytes) -> bytes:
    return b"codeunit 50100 C\n{\n    var\n" + decls + b"\n    procedure Q()\n    begin\n    end;\n}\n"


def test_fixture_has_the_task_12_cases():
    assert len(_cases()) == 27


@pytest.mark.parametrize("case", _cases(), ids=lambda c: c.name)
def test_fixture_case_has_no_error(al_parser, case):
    root = al_parser.parse(case.source).root_node
    assert root.has_error is False
    kinds = _kinds(root)
    if "preservation" in case.name:
        assert "var_attribute_open" not in kinds and "attribute_item" in kinds
    else:
        assert "var_attribute_open" in kinds and "attribute_item" not in kinds


def test_attribute_escaped_quote_name(al_parser):
    root = al_parser.parse(_var(b'        [A]\n        "X""Y", Z: Integer;\n')).root_node
    assert root.has_error is False
    assert "var_attribute_open" in _kinds(root)


# Shapes the lookahead declines, so no `[` becomes var_attribute_open. Most are rejected by alc as
# syntax in every configuration (B7b-1 Task 2 report, measured table: AL0621 malformed directive, AL0623
# unterminated group; the others are directive-line or name-list syntax errors). ACCEPTED is the one alc
# accepts (probe tools/alc_probe/cases/b7b1/colon_in_group.al): whole declarations in the arms of a group
# after an attribute. It is a pre-existing gap owned by deferred work, not B7b-1, so the test pins only the
# recognizer's contract there (no var_attribute_open), never that the input errors.
ACCEPTED = {"colon inside the group"}
DECLINED = {
    "malformed directive": b"        [A]\n        A\n#if X\n        , B\n#elsewhere\n        , C\n#endif\n        : Integer;\n",
    "unterminated group": b"        [A]\n        A\n#if X\n        , B\n        : Integer;\n",
    "endif without if": b"        [A]\n        A\n#endif\n        : Integer;\n",
    "colon inside the group": b"        [A]\n#if X\n        A: Integer;\n#else\n        B: Integer;\n#endif\n",
    "block comment on the #if line": b"        [A]\n        A\n#if X /* c */\n        , B\n#endif\n        : Integer;\n",
    "text after #endif": b"        [A]\n        A\n#if X\n        , B\n#endif B\n        : Integer;\n",
    "empty condition": b"        [A]\n        A\n#if\n        , B\n#endif\n        : Integer;\n",
    "no name at all": b"        [A]\n#if X\n#else\n#endif\n        : Integer;\n",
    "leading comma": b"        [A]\n        , A: Integer;\n",
    "two names without a separator": b"        [A]\n        A B: Integer;\n",
    "unterminated quoted name": b'        [A]\n        "A\n        , B: Integer;\n',
}


@pytest.mark.parametrize("name", sorted(DECLINED))
def test_declined_shape_is_no_var_attribute(al_parser, name):
    root = al_parser.parse(_var(DECLINED[name])).root_node
    if name not in ACCEPTED:
        assert root.has_error is True
    assert "var_attribute_open" not in _kinds(root)


def _point(src: bytes, offset: int):
    line = src.count(b"\n", 0, offset)
    return (line, offset - (src.rfind(b"\n", 0, offset) + 1))


def _dump(node, field=None, out=None):
    out = [] if out is None else out
    out.append((field, node.type, node.is_named, node.is_missing, node.start_byte, node.end_byte))
    cursor = node.walk()
    if cursor.goto_first_child():
        while True:
            _dump(cursor.node, cursor.field_name, out)
            if not cursor.goto_next_sibling():
                break
    return out


PREFIX = b"        [NonDebuggable]\n"
# (before, after): every edit is after the unchanged `[NonDebuggable]` prefix, and several flip the
# lookahead's verdict, so the `[` token must be re-lexed.
EDITS = [
    (b"        A, B: Integer;\n", b"        A\n#if X\n        , B\n#endif\n        : Integer;\n"),
    (b"        A\n#if X\n        , B\n#endif\n        : Integer;\n", b"        A\n#if X\n        , B\n        : Integer;\n"),
    (b"        A\n#if X\n        , B\n        : Integer;\n", b"        A\n#if X\n        , B\n#endif\n        : Integer;\n"),
    (b"        A\n#if X\n        , B\n#endif\n        : Integer;\n", b"        A\n#if X\n        , Bee\n#else\n        , C\n#endif\n        : Integer;\n"),
    (b"#if X\n        A\n#else\n        B\n#endif\n        , C: Integer;\n", b"#if X\n        A\n#else\n        B\n#endif\n        , C(: Integer;\n"),
    (b"#if X\n    procedure Q2(A: Integer)\n#else\n    procedure Q2()\n#endif\n    begin\n    end;\n",
     b"#if X\n        A2,\n#endif\n        B2: Integer;\n"),
    (b"        A,\n#if X\n        B,\n#endif\n        C: Integer;\n", b"        A,\n#if X\n        B,\n#elsewhere\n#endif\n        C: Integer;\n"),
]


@pytest.mark.parametrize("before,after", EDITS, ids=[f"edit{i}" for i in range(len(EDITS))])
def test_incremental_names_after_attribute(al_parser, before, after):
    old_src, new_src = _var(PREFIX + before), _var(PREFIX + after)
    start = 0
    while old_src[start] == new_src[start]:
        start += 1
    tail = 0
    while tail < min(len(old_src), len(new_src)) - start and old_src[-1 - tail] == new_src[-1 - tail]:
        tail += 1
    old_end, new_end = len(old_src) - tail, len(new_src) - tail
    tree = al_parser.parse(old_src)
    tree.edit(start_byte=start, old_end_byte=old_end, new_end_byte=new_end,
              start_point=_point(old_src, start), old_end_point=_point(old_src, old_end),
              new_end_point=_point(new_src, new_end))
    incremental = al_parser.parse(new_src, tree)
    fresh = al_parser.parse(new_src)
    assert _dump(incremental.root_node) == _dump(fresh.root_node)
    assert incremental.root_node.has_error == fresh.root_node.has_error
