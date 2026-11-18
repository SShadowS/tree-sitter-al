"""Issue #45: a lone CR ends a line, as it does for alc 18.0.41.

`_directive_eol` is hidden, so a MISSING one is invisible to `tree-sitter parse` and
parse-al-parallel.sh; `has_error` sees it. Before the fix the scanner ended a directive
line only at `\\n`, so in a CR-only file an `#if` line never ended, and a `//` comment
ran to the end of the file (no error at all for a header comment: the file was one
comment). alc compiles every positive case below with CR-only line ends.
"""
import pytest

BODY_IF = (b"codeunit 50299 \"C288 CR\"\r{\r    procedure P()\r    begin\r#if X288\r"
           b"        exit;\r#endif\r        Q();\r    end;\r\r    procedure Q()\r    begin\r    end;\r}\r")

POSITIVE = {
    "if": BODY_IF,
    "if_else": b"codeunit 1 T\r{\r trigger OnRun()\r begin\r#if A\r x := 1;\r#else\r x := 2;\r#endif\r end;\r}\r",
    "if_elif_else": (b"codeunit 1 T\r{\r trigger OnRun()\r begin\r#if A\r x := 1;\r#elif B\r x := 2;\r"
                     b"#else\r x := 3;\r#endif\r end;\r}\r"),
    "if_trailing_comment": b"codeunit 1 T\r{\r trigger OnRun()\r begin\r#if A // c\r x := 1;\r#endif // d\r end;\r}\r",
    "elif_trailing_comment": b"codeunit 1 T\r{\r trigger OnRun()\r begin\r#if A\r x := 1;\r#elif B // c\r x := 2;\r#endif\r end;\r}\r",
    "mixed_cr_crlf": b"codeunit 1 T\r\n{\r trigger OnRun()\r\n begin\r#if A\r x := 1;\r\n#elif B\r\n x := 2;\r#else\r\n x := 2;\r#endif\r\n end;\r}\r\n",
    "header_comment": b"// header\rcodeunit 50298 \"C CR\"\r{\r    procedure P()\r    begin\r    end;\r}\r",
    "body_comment": b"codeunit 1 T\r{\r procedure P()\r begin\r // note\r end;\r}\r",
    "region_pragma": b"#pragma warning disable AL0432\rcodeunit 1 T\r{\r#region R\r procedure P()\r begin\r end;\r#endregion\r}\r",
    "var_attribute_group": (b"codeunit 1 T\r{\r procedure P()\r var\r [NonDebuggable]\r#if A\r V\r#else\r W\r#endif\r"
                            b" : Integer;\r begin\r end;\r}\r"),
}

# Malformed directive lines alc rejects (AL0631 / AL0629 / AL0621); on a CR-only line
# the gatekeeper must still claim them.
NEGATIVE = {
    "else_trailing_code": b"codeunit 1 T\r{\r trigger OnRun()\r begin\r#if A\r x := 1;\r#else x := 2;\r#endif\r end;\r}\r",
    "if_dangling_and": b"codeunit 1 T\r{\r trigger OnRun()\r begin\r#if A and\r B\r x := 1;\r#endif\r end;\r}\r",
    "if_block_comment": b"codeunit 1 T\r{\r trigger OnRun()\r begin\r#if A /* c */\r x := 1;\r#endif\r end;\r}\r",
    "if_dangling_or": b"codeunit 1 T\r{\r trigger OnRun()\r begin\r#if A or\r x := 1;\r#endif\r end;\r}\r",
    "if_empty": b"codeunit 1 T\r{\r trigger OnRun()\r begin\r#if\r x := 1;\r#endif\r end;\r}\r",
    "if_empty_trailing_space": b"codeunit 1 T\r{\r trigger OnRun()\r begin\r#if \r x := 1;\r#endif\r end;\r}\r",
    "else_trailing_word": b"codeunit 1 T\r{\r trigger OnRun()\r begin\r#if A\r x := 1;\r#else x\r x := 2;\r#endif\r end;\r}\r",
}

# Issue #39 shapes (an empty group before `else`): the #if line's lookahead reads the
# group after its line end. Review of 28569aca: a line-end check that consumed a lone
# `\r` left that lookahead on the next line, so it skipped the group's `#endif` unread.
_IF = b"codeunit 1 T\r{\r procedure P()\r var\r x: Integer;\r begin\r if x = 1 then\r x := 2\r%s else\r x := 3;\r end;\r}\r"
EMPTY_GROUP_ELSE = {
    "empty_group": _IF % b"#if A\r#endif\r",
    "empty_group_trailing_space": _IF % b"#if A \r#endif\r",
    "nested_empty_groups": _IF % b"#if A\r#if B\r#endif\r#endif\r",
    "empty_group_trailing_comment": _IF % b"#if A // c\r#endif\r",
    "empty_group_elif_else": _IF % b"#if A\r#elif B\r#else\r#endif\r",
}


def _lf_twin(src):
    return src.replace(b"\r", b"\n")


def _shape(node):
    """Every node, anonymous ones included, with field, byte range and MISSING. A comment's
    end is taken before its `\\r`: the comment token takes the `\\r` ending it (as on CRLF)."""
    out, c, depth = [], node.walk(), 0
    while True:
        n = c.node
        end = n.start_byte + len(n.text.rstrip(b"\r")) if n.type == "comment" else n.end_byte
        out.append(f"{'  ' * depth}{c.field_name or ''}:{n.type}{' MISSING' if n.is_missing else ''}"
                   f"[{n.start_byte},{end}]")
        if c.goto_first_child():
            depth += 1
            continue
        while not c.goto_next_sibling():
            if not c.goto_parent():
                return out
            depth -= 1


@pytest.mark.parametrize("name", sorted(EMPTY_GROUP_ELSE))
def test_cr_empty_group_before_else_is_its_lf_twin(al_parser, name):
    src = EMPTY_GROUP_ELSE[name]
    cr = al_parser.parse(src).root_node
    assert cr.has_error is False
    assert _shape(cr) == _shape(al_parser.parse(_lf_twin(src)).root_node)


def test_cr_non_empty_group_before_else_is_its_lf_twin(al_parser):
    """A group holding a statement is not the #39 decoration on CR either (the line
    after `#if A` must be read, not skipped). Its LF tree is what it is; CR must match."""
    src = _IF % b"#if A\r ;\r#endif\r"
    assert _shape(al_parser.parse(src).root_node) == _shape(al_parser.parse(_lf_twin(src)).root_node)


@pytest.mark.parametrize("name", sorted(NEGATIVE))
def test_cr_malformed_recovery_is_its_lf_twin(al_parser, name):
    """The malformed line's recovery covers the same bytes as on LF: it neither runs
    over the next line nor loses the statement after it."""
    src = NEGATIVE[name]
    assert _shape(al_parser.parse(src).root_node) == _shape(al_parser.parse(_lf_twin(src)).root_node)


@pytest.mark.parametrize("name", sorted(POSITIVE))
def test_cr_only_parses_clean(al_parser, name):
    root = al_parser.parse(POSITIVE[name]).root_node
    assert root.has_error is False
    assert root.child_count >= 1 and any(c.type != "comment" for c in root.children)


@pytest.mark.parametrize("name", sorted(NEGATIVE))
def test_cr_only_malformed_directive_still_errors(al_parser, name):
    assert al_parser.parse(NEGATIVE[name]).root_node.has_error is True


def test_cr_comment_takes_its_cr_like_crlf(al_parser):
    """A comment's text includes the `\\r` that ends it, lone or before `\\n` (as before)."""
    for src in (b"// h\rcodeunit 1 T { }\r", b"// h\r\ncodeunit 1 T { }\r\n"):
        comment = al_parser.parse(src).root_node.children[0]
        assert comment.type == "comment" and comment.text == b"// h\r"


def test_if_line_ends_at_lone_cr(al_parser):
    """The condition is `X288` alone, and both procedures are in the tree."""
    root = al_parser.parse(BODY_IF).root_node
    assert root.has_error is False
    text = root.text.decode()
    names = []

    def walk(n):
        if n.type == "procedure" and n.is_named:
            names.append(n.child_by_field_name("name").text.decode())
        if n.type == "preproc_if":
            assert n.child_by_field_name("condition").text == b"X288"
        for c in n.children:
            walk(c)
    walk(root)
    assert names == ["P", "Q"], text
