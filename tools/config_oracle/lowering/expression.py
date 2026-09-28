"""Precedence-correct recomposition of flattened binary chains (base §3).

The table is taken from `test/corpus/operator_precedence_test.txt`'s header,
which was measured against the AL compiler (alc) -- NOT from `grammar.js`
`prec()` values. That independence is the point of the table: it lets this
module (and Task 11's recomposition of chains split across `#if` arms) be
checked against the same compiler-measured ladder the grammar itself is
checked against, instead of against the grammar's own numbers.

Header (tightest to loosest; all binary levels are left-associative):

    *  /  div  mod          6   multiplicative_expression
    +  -                    5   additive_expression
    in  is  as              4   in_expression / is_expression / as_expression
    and                     3   logical_expression
    or  xor                 2   logical_expression
    =  <>  <  >  <=  >=     1   comparison_expression (a comparison_operator node)

Unary, parenthesized, call, member and every other expression is an atom as
far as this table is concerned -- flatten/compose never look inside one.

`in` / `is` / `as` (grammar.js `in_expression`/`is_expression`/`as_expression`,
~line 5054): each one IS a plain `left`/`operator`/`right` binary node -- 3
children, exactly those fields, confirmed by grep and by parsing
`Flag := X as IProbeB is IProbeB;` and reading the IR. So they stay in
BINARY_KINDS at level 4, matching the header's `in is as` row. What is
different about them is the operator TOKEN's kind: `+ - * / div mod and or
xor` are anonymous leaves whose kind already equals their canonical lowercase
text, and `comparison_operator` is a named node recognised by kind outright
-- but `in_expression`/`is_expression`/`as_expression`'s `operator` field is
a NAMED KEYWORD node (`in_keyword` / `is_keyword` / `as_keyword`, each with
the usual one-anonymous-child keyword shape), never a bare `"in"`/`"is"`/
`"as"` token. `op_text` special-cases these three the same way it
special-cases `comparison_operator`.
"""
from __future__ import annotations

from tools.config_oracle.ir import Node

LEVEL = {
    "*": 6, "/": 6, "div": 6, "mod": 6,
    "+": 5, "-": 5,
    "in": 4, "is": 4, "as": 4,
    "and": 3,
    "or": 2, "xor": 2,
    "cmp": 1,
}
KIND_FOR = {
    "*": "multiplicative_expression", "/": "multiplicative_expression",
    "div": "multiplicative_expression", "mod": "multiplicative_expression",
    "+": "additive_expression", "-": "additive_expression",
    "in": "in_expression", "is": "is_expression", "as": "as_expression",
    "and": "logical_expression",
    "or": "logical_expression", "xor": "logical_expression",
    "cmp": "comparison_expression",
}
BINARY_KINDS = frozenset(KIND_FOR.values())

# The three keyword-wrapped operators: see the module docstring's `in`/`is`/`as` note.
_KEYWORD_OPERATOR = {"in_keyword": "in", "is_keyword": "is", "as_keyword": "as"}


def op_text(op: Node, source: bytes | None = None) -> str:
    """Operator text, lowercased, keyed the same as LEVEL/KIND_FOR.

    `source` is accepted for interface symmetry but unused: every operator
    kind this table handles already carries its canonical text in `kind` --
    an anonymous leaf's kind IS its (alias-canonicalised, lowercase) text,
    `comparison_operator` is recognised by kind, and the three
    keyword-wrapped operators resolve via `_KEYWORD_OPERATOR` -- so there is
    never a need to re-read the source bytes.
    """
    if op.kind == "comparison_operator":
        return "cmp"
    return _KEYWORD_OPERATOR.get(op.kind, op.kind.lower())


def _parts(node: Node):
    left = op = right = None
    for c in node.children:
        if c.field == "left":
            left = c
        elif c.field == "operator":
            op = c
        elif c.field == "right":
            right = c
    if left is None or op is None or right is None or len(node.children) != 3:
        raise ValueError(f"not a plain binary node: {node.kind}@{node.start}")
    return left, op, right


def flatten(node: Node) -> list:
    """Alternating `[operand, operator, operand, ...]`.

    Contract (recursive form): `flatten(node) = [node]` if `node.kind` is not
    in `BINARY_KINDS`, else `flatten(left) + [op] + flatten(right)`.

    Implemented iteratively with an explicit stack, not Python recursion: a
    real BC.History chain can be thousands of same-precedence operators deep,
    which parses into a tree thousands of levels deep on its left spine --
    deep enough to blow Python's default recursion limit. This is the
    standard explicit-stack in-order traversal of a binary tree: descend the
    left spine of the current node, pushing `(operator, right)` at every
    binary node passed on the way down; emit the atom found at the bottom;
    then pop back one level at a time, emitting the saved operator and
    resuming the descent from the saved right child. Both recursion and this
    traversal visit every node in the same left-to-right order, so the
    output lists are identical.
    """
    if node.kind not in BINARY_KINDS:
        return [node]
    out: list = []
    stack: list = []
    current = node
    while stack or current is not None:
        while current is not None and current.kind in BINARY_KINDS:
            left, op, right = _parts(current)
            stack.append((op, right))
            current = left
        out.append(current)
        if stack:
            op, right = stack.pop()
            out.append(op)
            current = right
        else:
            current = None
    return out


def compose(flat: list, field: str | None) -> Node:
    """Operator-precedence parse over an alternating [operand, op, operand, ...] list."""
    operands, ops = [flat[0].copy(field=None)], []

    def reduce_top():
        op = ops.pop()
        r, l = operands.pop(), operands.pop()
        kids = [l.copy(field="left"), op.copy(field="operator"), r.copy(field="right")]
        operands.append(Node(KIND_FOR[op_text(op)], True, None, kids[0].start, kids[-1].end, kids))

    for i in range(1, len(flat), 2):
        op, rhs = flat[i], flat[i + 1]
        while ops and LEVEL[op_text(ops[-1])] >= LEVEL[op_text(op)]:   # left-associative
            reduce_top()
        ops.append(op)
        operands.append(rhs.copy(field=None))
    while ops:
        reduce_top()
    return operands[0].copy(field=field)
