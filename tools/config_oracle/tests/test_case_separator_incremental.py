"""B7b-3 Task 6 (spec 4.1-4.2): case-branch separators from #if groups.

1. An incremental re-parse after an edit equals a fresh parse (full cursor tree: every node, named and
   anonymous, field, type, MISSING flag, byte span): a lone-`;` group after a branch, a decoration before a
   branch's `;`, and a nested decoration are each inserted and removed.
2. Ownership of the anonymous `;`, which corpus expectations cannot show: a decoration's `;` is the branch's
   own direct child, after the decoration; an arm's `;` is an empty_statement, never the branch's."""
import pytest

from tools.config_oracle.tests.test_strict_lists_incremental import _dump, _edit

HOST = b"codeunit 1 P\n{\n    procedure M()\n    begin\ncase I of\n%s\nend;\n    end;\n}\n"

SHAPES = {
    "plain": b"1: Bar;\n2: Baz;",
    "unterminated": b"1: Bar\n2: Baz;",
    "lone-group": b"1: Bar\n#if X\n;\n#endif\n2: Baz;",
    "decoration": b"1: Bar\n#if X\n#endif\n;\n2: Baz;",
    "nested-decoration": b"1: Bar\n#if X\n#if Y\n#endif\n#endif\n;\n2: Baz;",
}

EDITS = [
    ("unterminated", "lone-group"),         # a lone-`;` group is inserted after a branch
    ("lone-group", "unterminated"),         # and removed
    ("plain", "decoration"),                # a decoration is inserted before a branch's `;`
    ("decoration", "plain"),                # and removed
    ("decoration", "nested-decoration"),    # the decoration gains a nested decoration
    ("nested-decoration", "decoration"),    # and loses it
    ("plain", "nested-decoration"),         # a nested decoration is inserted at once
    ("nested-decoration", "plain"),         # and removed
    ("lone-group", "decoration"),           # the `;` moves out of the group: sibling -> decoration
    ("decoration", "lone-group"),           # and back in
]


@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_every_shape_parses_clean(al_parser, shape):
    root = al_parser.parse(HOST % SHAPES[shape]).root_node
    assert not root.has_error, SHAPES[shape].decode()


@pytest.mark.parametrize("before,after", EDITS)
def test_incremental_case_separator_edits(al_parser, before, after):
    old_src, new_src = HOST % SHAPES[before], HOST % SHAPES[after]
    incremental = _edit(al_parser, old_src, new_src)
    fresh = al_parser.parse(new_src)
    assert _dump(incremental.root_node) == _dump(fresh.root_node)
    assert incremental.root_node.has_error == fresh.root_node.has_error


def _first(node, kind):
    if node.type == kind:
        return node
    for c in node.children:
        r = _first(c, kind)
        if r is not None:
            return r
    return None


def _kids(node):
    return [(c.type, node.field_name_for_child(i)) for i, c in enumerate(node.children)]


def test_decoration_semicolon_is_the_branch_own(al_parser):
    root = al_parser.parse(HOST % SHAPES["nested-decoration"]).root_node
    branch = _first(root, "case_branch")
    assert branch is not None
    assert _kids(branch) == [("integer", "pattern"), (":", None), ("call_statement", "body"),
                             ("preproc_conditional_case", None), (";", None)]
    outer = branch.children[3]
    inner = [c for c in outer.children if c.type == "preproc_conditional_case"]
    assert len(inner) == 1 and inner[0].id != outer.id     # distinct outer and inner nodes


def test_arm_semicolon_is_an_empty_statement_not_the_branch(al_parser):
    root = al_parser.parse(HOST % SHAPES["lone-group"]).root_node
    body = _first(root, "case_body")
    assert body is not None
    assert [c.type for c in body.children] == ["case_branch", "preproc_conditional_case", "case_branch"]
    first = body.children[0]
    assert ";" not in [c.type for c in first.children]     # the first branch has no `;` of its own
    group = body.children[1]
    assert [c.type for c in group.children] == ["preproc_if", "empty_statement", "preproc_endif"]
