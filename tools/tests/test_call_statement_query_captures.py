"""B7b-3 spec 3.5: a parenless call is highlighted as @function.call and tagged as @reference.call, plain and
quoted, with and without its `;`."""
from pathlib import Path

import tree_sitter

from tools import relation_census as rc

SRC = (b"codeunit 50100 P\n{\n    procedure M()\n    begin\n"
       b"        Bar;\n"
       b'        "My Proc";\n'
       b"        if Ok then Baz else Qux\n"
       b"    end;\n}\n")


def _captures(scm_name):
    parser = rc.parser_for(None)
    tree = parser.parse(SRC)
    q = tree_sitter.Query(parser.language, Path("queries", scm_name).read_text(encoding="utf-8"))
    caps = tree_sitter.QueryCursor(q).captures(tree.root_node)
    return {(name, SRC[n.start_byte:n.end_byte]) for name, nodes in caps.items() for n in nodes}


NAMES = [b"Bar", b'"My Proc"', b"Baz", b"Qux"]


def test_highlights_capture_parenless_calls():
    caps = _captures("highlights.scm")
    for name in NAMES:
        assert ("function.call", name) in caps, name


def test_tags_reference_parenless_calls():
    caps = _captures("tags.scm")
    for name in NAMES:
        assert ("name", name) in caps, name
        assert ("reference.call", name) in caps, name
