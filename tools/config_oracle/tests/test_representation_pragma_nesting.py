"""Item 102: a preproc_pragma_only arm may hold nested pragma-only groups and nothing else.

The `pragma-only-with-structure` contract exempts exactly a nested `preproc_pragma_only` (which is checked on
its own as the walk reaches it). Any other node in an arm, including another `preproc_*` group, is still
structure: these tests fail if the exemption is widened (say to every `preproc_*` kind, or dropped).
"""
import pytest

from tools.config_oracle import ir, representation


def group(kind, start, content, end):
    """`#if` <content> `#endif` as an IR node of `kind` spanning [start, end)."""
    return ir.Node(kind, True, None, start, end,
                   [ir.Node("preproc_if", True, None, start, start + 5, [])] + content
                   + [ir.Node("preproc_endif", True, None, end - 6, end, [])])


def kinds(root):
    return [(d.kind, d.path) for d in representation.check(root)]


def test_nested_pragma_only_is_not_structure():
    inner = group("preproc_pragma_only", 10, [], 30)
    outer = group("preproc_pragma_only", 0, [inner], 40)
    assert kinds(ir.Node("procedure", True, None, 0, 40, [outer])) == []


NESTED_BEFORE_BODY = b"""codeunit 1 T {
    procedure P()
#if A
#if B
#endif
#endif
    begin
    end;
}"""


def test_parsed_nested_empty_group_is_legitimate(al_parser):
    root, _, problems = ir.from_tree(al_parser.parse(NESTED_BEFORE_BODY))
    assert problems == []
    assert representation.check(root) == []


@pytest.mark.parametrize("stray", [
    "procedure",                      # a declaration
    "assignment_statement",           # a statement
    "var_section",                    # a var section
    "preproc_conditional_statement",  # another #if group: still structure
    "preproc_conditional_var_block",
])
def test_structure_in_a_pragma_only_arm_is_a_violation(stray):
    outer = group("preproc_pragma_only", 0, [ir.Node(stray, True, None, 6, 9, [])], 40)
    assert kinds(ir.Node("procedure", True, None, 0, 40, [outer])) == [
        ("pragma-only-with-structure", "preproc_pragma_only@0")]


@pytest.mark.parametrize("stray", ["procedure", "assignment_statement", "var_section",
                                   "preproc_conditional_statement"])
def test_structure_in_a_nested_pragma_only_is_reported_on_the_inner_group(stray):
    inner = group("preproc_pragma_only", 10, [ir.Node(stray, True, None, 16, 19, [])], 30)
    outer = group("preproc_pragma_only", 0, [inner], 40)
    assert kinds(ir.Node("procedure", True, None, 0, 40, [outer])) == [
        ("pragma-only-with-structure", "preproc_pragma_only@10")]


def test_nested_pragma_only_next_to_structure_still_flags_the_outer_group():
    inner = group("preproc_pragma_only", 10, [], 30)
    stray = ir.Node("identifier", True, None, 31, 32, [])
    outer = group("preproc_pragma_only", 0, [inner, stray], 40)
    assert kinds(ir.Node("procedure", True, None, 0, 40, [outer])) == [
        ("pragma-only-with-structure", "preproc_pragma_only@0")]
