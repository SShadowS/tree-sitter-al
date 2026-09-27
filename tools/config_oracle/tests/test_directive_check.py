import pytest

from tools.config_oracle import directive_check, ir
from tools.config_oracle.directives import discover

CASES = [
    b"codeunit 1 T { trigger OnRun() begin\n#if A\nx := 1;\n#else\nx := 2;\n#endif\nend; }\n",
    b"codeunit 1 T { trigger OnRun() begin\r\n#if A // c\r\nx := 1;\r\n#endif\r\nend; }\r\n",
    b"codeunit 1 T { trigger OnRun() begin\n# if not (A or B)\nx := 1;\n#elif C\nx := 3;\n#endif\nend; }",
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
