"""Deferred item 27: an `identifier` is a leaf everywhere, a `TableData` option member too.

The defect was an anonymous `"tabledata"` child, which corpus expected trees and the
tree harness never show; `snip.py --census` and this test are what see it.
`Permissions = tabledata ...` must keep its `tabledata_keyword` with the one child.
"""
import pytest
from tools import relation_census as rc

SITES = [
    b"table 50100 T\n{\n    fields\n    {\n        field(1; F; Option) { OptionMembers = TableData,\"Table\"; }\n"
    b"        field(2; G; Option) { OptionMembers = TableData; }\n    }\n}\n",
    b"codeunit 50100 C\n{\n    var\n        X: Option TableData,\"Table\",Form;\n}\n",
    b"table 50100 T\n{\n    fields { field(1; F; Code[20]) { Description = TableData; } }\n}\n",
]


def _walk(n):
    yield n
    for c in n.children:
        yield from _walk(c)


@pytest.mark.parametrize("src", SITES)
def test_tabledata_option_member_is_leaf_identifier(src):
    root = rc.parser_for(None).parse(src).root_node
    assert not root.has_error
    ids = [n for n in _walk(root) if n.type == "identifier" and n.text.lower() == b"tabledata"]
    assert ids, src
    assert all(n.child_count == 0 for n in ids), src


def test_permissions_tabledata_keeps_keyword():
    src = b"codeunit 50100 C\n{\n    Permissions = tabledata Customer = R, table Customer = X;\n}\n"
    root = rc.parser_for(None).parse(src).root_node
    assert not root.has_error
    kws = [n for n in _walk(root) if n.type == "tabledata_keyword"]
    assert len(kws) == 1 and kws[0].child_count == 1 and kws[0].children[0].type == "tabledata"
