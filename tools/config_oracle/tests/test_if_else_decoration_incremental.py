"""Issue #39: a directive-only #if group before an if's `else` is a decoration inside the if_statement.

The scanner decides it (PREPROC_OPEN_BEFORE_ELSE) by looking PAST the group's #endif for `else`, so an
edit after the group must invalidate the `#if` token. Each edit below changes only the text after #endif,
or the group itself, and the incremental re-parse must equal a fresh parse (full cursor tree)."""
import pytest

from tools.config_oracle.tests.test_strict_lists_incremental import _dump, _edit

HOST = b"codeunit 1 P\n{\n    procedure M(R: Boolean)\n    begin\nif R then\nA()\n%s\n    end;\n}\n"

SHAPES = {
    "no-else": b"#if X\n#endif\n;\nB();",          # the group is a sibling statement
    "else": b"#if X\n#endif\nelse\nB();",          # the group is the if's decoration
    "nested": b"#if X\n#if Y\n#endif\n#endif\nelse\nB();",
    "two-groups": b"#if X\n#endif\n#if Y\n#endif\nelse\nB();",
    "else-prefix": b"#if X\n#endif\n;\nelsewhere();",  # `else` must be a whole word
}

EDITS = [
    ("no-else", "else"), ("else", "no-else"),
    ("else", "nested"), ("nested", "else"),
    ("else", "two-groups"), ("two-groups", "else"),
    ("else-prefix", "else"), ("else", "else-prefix"),
]


@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_every_shape_parses_clean(al_parser, shape):
    root = al_parser.parse(HOST % SHAPES[shape]).root_node
    assert not root.has_error, SHAPES[shape].decode()


@pytest.mark.parametrize("before,after", EDITS)
def test_incremental_else_decoration_edits(al_parser, before, after):
    old_src, new_src = HOST % SHAPES[before], HOST % SHAPES[after]
    incremental = _edit(al_parser, old_src, new_src)
    fresh = al_parser.parse(new_src)
    assert _dump(incremental.root_node) == _dump(fresh.root_node)
    assert incremental.root_node.has_error == fresh.root_node.has_error


def _if(root):
    stack = [root]
    while stack:
        n = stack.pop()
        if n.type == "if_statement":
            return n
        stack.extend(reversed(n.children))
    return None


@pytest.mark.parametrize("shape,inside", [("else", True), ("two-groups", True), ("no-else", False)])
def test_group_ownership(al_parser, shape, inside):
    node = _if(al_parser.parse(HOST % SHAPES[shape]).root_node)
    kinds = [c.type for c in node.children]
    assert ("preproc_conditional_statement" in kinds) is inside, kinds
    assert ("else_keyword" in kinds) is inside, kinds
