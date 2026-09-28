import pytest

from tools.config_oracle import directive_check, ir
from tools.config_oracle.directives import discover

CASES = [
    b"codeunit 1 T { trigger OnRun() begin\n#if A\nx := 1;\n#else\nx := 2;\n#endif\nend; }\n",
    b"codeunit 1 T { trigger OnRun() begin\r\n#if A // c\r\nx := 1;\r\n#endif\r\nend; }\r\n",
    b"codeunit 1 T { trigger OnRun() begin\n# if not (A or B)\nx := 1;\n#elif C\nx := 3;\n#endif\nend; }",
    # Task 18 (the first production run, 128 end-extent items over 34 files): the
    # directive's newline terminator skipped blank lines as whitespace and matched
    # the LAST newline, so preproc_if/preproc_elif ran on over following blank lines.
    b"codeunit 1 T { trigger OnRun() begin\n#if A\n\n\nx := 1;\n#elif B\n\nx := 2;\n#endif\nend; }\n",
    b"codeunit 1 T { trigger OnRun() begin\r\n#if not A  \r\n\r\n  \r\nx := 1;\r\n#endif\r\nend; }\r\n",
    b"codeunit 1 T { trigger OnRun() begin\n#if A // c\n\nx := 1;\n#endif\nend; }\n",
]


@pytest.mark.parametrize("src", CASES)
def test_positive_controls_match(al_parser, src):
    root, _, problems = ir.from_tree(al_parser.parse(src))
    assert problems == []
    assert directive_check.check(root, discover(src)) == []


def test_condition_swallowing_next_line_is_condition_extent():
    """Replay 4's shape, built as a tree: condition extends into the next line."""
    src = b"#if FOO\n and b\n#endif\n"
    disc = discover(src)
    cond = ir.Node("identifier", True, "condition", 4, 14, [])   # swallowed ' and b'
    pif = ir.Node("preproc_if", True, None, 0, 15, [ir.Node("preproc_open", True, None, 0, 3, []), cond])
    pend = ir.Node("preproc_endif", True, None, 15, 21, [])
    root = ir.Node("source_file", True, None, 0, 22, [pif, pend])
    kinds = {d.kind for d in directive_check.check(root, disc)}
    assert "condition-extent" in kinds


def test_tree_directive_without_source_directive():
    src = b"x;\n"
    root = ir.Node("source_file", True, None, 0, 3, [ir.Node("preproc_else", True, None, 0, 1, [])])
    assert {d.kind for d in directive_check.check(root, discover(src))} == {"unmatched-tree"}


def test_wrong_end_on_preproc_if_is_end_extent_only():
    """preproc_if's own end (which must land on d.next_line) is wrong; its
    condition extent is correct, so nothing else should fire."""
    src = b"#if A\nx;\n#endif\n"
    disc = discover(src)  # if@0 (next_line=6), endif@9 (keyword_end=15)
    cond = ir.Node("identifier", True, "condition", 4, 5, [])
    pif = ir.Node("preproc_if", True, None, 0, 5, [ir.Node("preproc_open", True, None, 0, 3, []), cond])  # end=5, should be 6
    pend = ir.Node("preproc_endif", True, None, 9, 15, [])
    root = ir.Node("source_file", True, None, 0, 16, [pif, pend])
    assert {d.kind for d in directive_check.check(root, disc)} == {"end-extent"}


def test_wrong_end_on_preproc_endif_is_end_extent_only():
    """preproc_endif's end (which must land on d.keyword_end) is wrong."""
    src = b"#if A\nx;\n#endif\n"
    disc = discover(src)  # endif@9 keyword_end=15
    cond = ir.Node("identifier", True, "condition", 4, 5, [])
    pif = ir.Node("preproc_if", True, None, 0, 6, [ir.Node("preproc_open", True, None, 0, 3, []), cond])
    pend = ir.Node("preproc_endif", True, None, 9, 14, [])  # end=14, should be 15
    root = ir.Node("source_file", True, None, 0, 16, [pif, pend])
    assert {d.kind for d in directive_check.check(root, disc)} == {"end-extent"}


def test_source_directive_without_tree_node_is_unmatched_source():
    """The tree is missing the #else node entirely -- discover() still finds
    it in the source, so it must be reported as unmatched-source."""
    src = b"#if A\nx;\n#else\ny;\n#endif\n"
    disc = discover(src)  # if@0 (next_line=6), else@9 (keyword_end=14), endif@18 (keyword_end=24)
    cond = ir.Node("identifier", True, "condition", 4, 5, [])
    pif = ir.Node("preproc_if", True, None, 0, 6, [ir.Node("preproc_open", True, None, 0, 3, []), cond])
    pend = ir.Node("preproc_endif", True, None, 18, 24, [])
    root = ir.Node("source_file", True, None, 0, 25, [pif, pend])
    discs = directive_check.check(root, disc)
    assert {d.kind for d in discs} == {"unmatched-source"}
    assert [d.path for d in discs] == ["else@9"]
