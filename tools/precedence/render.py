"""Render each precedence probe case as a fully-parenthesised expression, exactly
as tree-sitter-al groups it.

    ./tools/ts-lock.sh python tools/precedence/render.py tools/precedence/cases

This is the PARSER half of the ladder; tools/precedence/probe.sh is the COMPILER
half. Compare the two: every row must group the same way, and
docs/al-operator-precedence.md records the reading for each.

Output is `name<TAB>ok|ERR<TAB>node type<TAB>grouping`, where the grouping uses
`( )` for a real node, `[ ]` for a parenthesised_expression the source wrote, and
`{ }` for a list literal — so a parenthesis in the output is never ambiguous
between "the source said so" and "the parser decided so".

NOTE: `is_expression` and `as_expression` render their operator as `..` because
their `operator` field holds a hidden token and comes back None. That is the
known dropped-operator finding recorded in the query-coverage baseline, not a
fault in this script.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from tools.query_coverage import loader  # noqa: E402

BINARY = {
    "multiplicative_expression": ("left", "operator", "right"),
    "additive_expression": ("left", "operator", "right"),
    "comparison_expression": ("left", "operator", "right"),
    "logical_expression": ("left", "operator", "right"),
    "range_expression": ("left", None, "right"),
    "in_expression": ("left", "operator", "right"),
    "is_expression": ("left", "operator", "right"),
    "as_expression": ("left", "operator", "right"),
}


def txt(node, src: bytes) -> str:
    return src[node.start_byte:node.end_byte].decode("utf-8", "replace")


def render(node, src: bytes) -> str:
    t = node.type
    if t in BINARY:
        lf, of, rf = BINARY[t]
        left = node.child_by_field_name(lf)
        right = node.child_by_field_name(rf)
        op = node.child_by_field_name(of) if of else None
        op_s = txt(op, src) if op is not None else ".."
        ls = render(left, src) if left is not None else "?"
        rs = render(right, src) if right is not None else "?"
        return f"({ls} {op_s} {rs})"
    if t == "unary_expression":
        op = node.child_by_field_name("operator")
        operand = node.child_by_field_name("operand")
        return f"({txt(op, src)} {render(operand, src)})"
    if t == "ternary_expression":
        c = node.child_by_field_name("condition")
        a = node.child_by_field_name("then_value")
        b = node.child_by_field_name("else_value")
        return f"({render(c, src)} ? {render(a, src)} : {render(b, src)})"
    if t == "parenthesized_expression":
        inner = [c for c in node.named_children]
        if len(inner) == 1:
            return "[" + render(inner[0], src) + "]"
        return "[" + " ".join(render(c, src) for c in inner) + "]"
    if t == "list_literal":
        return "{" + ", ".join(render(c, src) for c in node.named_children) + "}"
    if t == "ERROR":
        return "ERROR<" + txt(node, src) + ">"
    if node.named_child_count == 0 or t in (
        "identifier", "integer", "decimal", "string_literal", "boolean",
        "quoted_identifier", "type_specification",
    ):
        return txt(node, src).replace("\n", " ")
    # generic: descend if there is exactly one interesting child
    kids = [c for c in node.named_children]
    if len(kids) == 1:
        return render(kids[0], src)
    return txt(node, src).replace("\n", " ")


def find_rhs(root, src: bytes):
    """The right-hand side of the first assignment_statement, or the first
    case-label / condition expression when there is no assignment."""
    stack = [root]
    while stack:
        n = stack.pop(0)
        if n.type in ("assignment_statement", "assignment_expression"):
            r = n.child_by_field_name("right") or n.child_by_field_name("value")
            if r is not None:
                return r
        stack.extend(n.children)
    return None


def has_error(root) -> bool:
    if root.has_error:
        return True
    return False


def main(paths):
    lib = loader.ensure_library(REPO)
    lang = loader.load_language(lib)
    parser = loader.make_parser(lang)
    for p in paths:
        src = Path(p).read_bytes()
        tree = parser.parse(src)
        rhs = find_rhs(tree.root_node, src)
        name = Path(p).stem
        flag = "ERR" if has_error(tree.root_node) else "ok "
        if rhs is None:
            print(f"{name}\t{flag}\t<no assignment>\t{tree.root_node.type}")
        else:
            print(f"{name}\t{flag}\t{rhs.type}\t{render(rhs, src)}")


if __name__ == "__main__":
    args = sys.argv[1:]
    files = []
    for a in args:
        pa = Path(a)
        if pa.is_dir():
            files.extend(sorted(pa.glob("*.al")))
        else:
            files.append(pa)
    main(files)
