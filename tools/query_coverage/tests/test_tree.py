from tools.query_coverage.detectors import _tree


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
