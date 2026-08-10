import sys

from tools.query_coverage.detectors import _tree


def test_walk_and_leaves_survive_deep_nesting_without_recursionerror(al_parser):
    """A deeply nested source must not blow Python's default recursion limit.

    Task 7's reviewer hit RecursionError partway through a 15,358-file
    BC.History run because walk()/leaves() were plain-recursive. Thousands of
    nested parenthesized expressions build a parse tree deeper than
    sys.getrecursionlimit() (1000 by default), so this reproduces the failure
    mode without needing the real corpus.

    error_ranges() is exercised here too: a real --full-corpus run (Task 14)
    hit RecursionError inside it on a deeply nested BC.History file even
    after walk()/leaves() were converted, because it was a separate
    plain-recursive traversal (_collect_errors) over the same kind of tree.
    """
    depth = 4000
    source = (
        b"codeunit 1 T { procedure P() var x: Integer; begin x := "
        + b"(" * depth
        + b"1"
        + b")" * depth
        + b"; end; }"
    )
    assert depth > sys.getrecursionlimit()

    tree = al_parser.parse(source)
    assert not tree.root_node.has_error

    nodes = list(_tree.walk(tree.root_node))
    assert len(nodes) > depth

    leaves = list(_tree.leaves(tree.root_node))
    offsets = [leaf.start_byte for leaf in leaves]
    assert offsets == sorted(offsets)

    assert _tree.error_ranges(tree.root_node) == []


def test_leaves_are_in_byte_order(al_parser):
    source = b"codeunit 1 T { var i: Integer; }"

    offsets = [leaf.start_byte for leaf in _tree.leaves(al_parser.parse(source).root_node)]

    assert offsets == sorted(offsets)


def test_leaves_include_anonymous_string_tokens(al_parser):
    source = b"codeunit 1 T { var i: Integer; }"

    texts = [leaf.text.decode() for leaf in _tree.leaves(al_parser.parse(source).root_node)]

    assert ";" in texts


def test_walk_yields_self_first(al_parser):
    root = al_parser.parse(b"codeunit 1 T { }").root_node

    assert next(iter(_tree.walk(root))) is root


def test_enclosing_named_returns_self_when_named(al_parser):
    root = al_parser.parse(b"codeunit 1 T { }").root_node

    assert _tree.enclosing_named(root) == "source_file"


def test_enclosing_named_covering_returns_the_containing_construct_not_the_next_leaf(al_parser):
    """This is detector 1's F5 fingerprint bug, pinned directly:
    enclosing_named(leaf), called on the leaf immediately AFTER a gap, returns
    that leaf's own type the moment it is itself named -- here "integer", the
    literal that happens to sit next to the dropped ':='. That is the type of
    a neighbouring token, not of the construct the gap sits inside.
    enclosing_named_covering climbs past it to the nearest ancestor whose span
    actually starts at or before the gap, which is what the gap detector
    needs for its fingerprint (spec:154 -- "enclosing named node type").
    """
    source = b"codeunit 1 T { procedure P() var i: Integer; begin i := 1; end; }"
    tree = al_parser.parse(source)
    assignment = next(
        node for node in _tree.walk(tree.root_node) if node.type == "assignment_statement"
    )
    integer_leaf = assignment.child_by_field_name("right")
    identifier_leaf = assignment.child_by_field_name("left")
    assert integer_leaf.type == "integer"
    assert identifier_leaf.type == "identifier"
    gap_start = identifier_leaf.end_byte  # end of 'i', start of the dropped ' := '

    assert _tree.enclosing_named(integer_leaf) == "integer"
    assert _tree.enclosing_named_covering(integer_leaf, gap_start) == "assignment_statement"


def test_error_ranges_covers_the_error_and_does_not_descend(al_parser):
    source = b"codeunit 1 T { @@@ }"
    tree = al_parser.parse(source)
    assert tree.root_node.has_error

    ranges = _tree.error_ranges(tree.root_node)

    assert ranges
    assert all(lo < hi for lo, hi in ranges)


def test_error_ranges_is_empty_on_a_clean_tree(al_parser):
    assert _tree.error_ranges(al_parser.parse(b"codeunit 1 T { }").root_node) == []


def test_previous_meaningful_sibling_skips_a_comment(al_parser):
    source = b"codeunit 1 T { procedure P() var x: DotNet Foo; begin x./*c*/End(); end; }"
    tree = al_parser.parse(source)

    member = next(
        node
        for node in _tree.walk(tree.root_node)
        if node.type == "member_expression"
    )
    end_identifier = member.child_by_field_name("member")

    previous = _tree.previous_meaningful_sibling(end_identifier)

    assert previous is not None
    assert previous.type == "."


def test_previous_meaningful_sibling_returns_the_immediate_sibling_when_no_extra(al_parser):
    source = b"codeunit 1 T { procedure P() var x: DotNet Foo; begin x.End(); end; }"
    tree = al_parser.parse(source)

    member = next(
        node
        for node in _tree.walk(tree.root_node)
        if node.type == "member_expression"
    )
    end_identifier = member.child_by_field_name("member")

    # tree-sitter's Python bindings mint a fresh wrapper Node per access, so
    # compare by position rather than `is`.
    expected = end_identifier.prev_sibling
    actual = _tree.previous_meaningful_sibling(end_identifier)
    assert actual is not None
    assert (actual.type, actual.start_byte, actual.end_byte) == (
        expected.type,
        expected.start_byte,
        expected.end_byte,
    )
