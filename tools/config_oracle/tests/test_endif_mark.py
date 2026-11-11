"""`_endif_mark` must never be MISSING after a well-formed `#endif`.

`#endif` is a grammar regex since the state review (C1) and the depth decrement moved to the hidden
zero-width external `_endif_mark`, valid only right after the regex. A MISSING hidden token is not
printed by `tree-sitter parse` and leaves `--json-summary` (and so parse-al-parallel.sh) successful;
`has_error` shows it. Every spelling and every follower the regex and the scanner accept is here.
"""
import pytest

HEAD = b"codeunit 1 T { trigger OnRun() begin\n#if A\nx := 1;\n"

CASES = {
    "eof-no-newline": b"codeunit 1 T { }\n#if A\n#endif",
    "form-feed": HEAD + b"#endif\f\nend; }\n",
    "line-comment": HEAD + b"#endif // c\nend; }\n",
    "endif-endif": b"codeunit 1 T { trigger OnRun() begin\n#if A\n#if B\nx := 1;\n#endif\n#endif\nend; }\n",
    "endif-then-if": HEAD + b"#endif\n#if B\nx := 2;\n#endif\nend; }\n",
    "spaced": HEAD + b"# endif\nend; }\n",
    "tab-spaced": HEAD + b"#\tendif\nend; }\n",
    "upper": HEAD + b"#ENDIF\nend; }\n",
}


@pytest.mark.parametrize("src", CASES.values(), ids=CASES.keys())
def test_endif_mark_never_missing(al_parser, src):
    root = al_parser.parse(src).root_node
    assert root.has_error is False


# The '#' gatekeeper: a word that only contains or extends `endif` is never a preproc_close, and its
# line holds an ERROR. The corpus cases for these inputs (preproc_if_elif_whitespace_tolerance_test.txt,
# directive_line_rejected_negative_test.txt) are `:error` since state review C3 changed their recovery.
MALFORMED = ["#iendif", "#ifendif", "#xendif", "#endifx"]


@pytest.mark.parametrize("word", MALFORMED)
def test_malformed_endif_is_no_preproc_close(al_parser, word):
    src = HEAD + word.encode() + b"\nend; }\n"
    row = src.count(b"\n", 0, src.index(word.encode()))
    tree = al_parser.parse(src)
    nodes, cursor = [], tree.walk()
    while True:
        nodes.append(cursor.node)
        if cursor.goto_first_child() or cursor.goto_next_sibling():
            continue
        while cursor.goto_parent() and not cursor.goto_next_sibling():
            pass
        if cursor.node == tree.root_node:
            break
    assert tree.root_node.has_error
    assert not [n for n in nodes if n.type == "preproc_close" and n.start_point.row == row]
    assert [n for n in nodes if n.type == "ERROR" and n.start_point.row <= row <= n.end_point.row]
