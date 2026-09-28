"""The precedence table recomposes every compiler-verified grouping (base §3, spec P5.3)."""
from __future__ import annotations

import sys

import pytest

from tools.config_oracle import fixtures, ir
from tools.config_oracle.ir import Node
from tools.config_oracle.lowering import expression
from tools.query_coverage import loader

CASES = [c for c in fixtures.extract(loader.REPO_ROOT / "test" / "corpus")
         if c.file == "operator_precedence_test.txt"]


def _chains(root):
    """Maximal binary chains: binary nodes whose parent is not a binary node."""
    out, stack = [], [(root, None)]
    while stack:
        n, parent = stack.pop()
        if n.kind in expression.BINARY_KINDS and (parent is None or parent.kind not in expression.BINARY_KINDS):
            out.append(n)
        for c in n.children:
            stack.append((c, n))
    return out


def _shape(n):
    return (n.kind, n.field, n.start, n.end, tuple(_shape(c) for c in n.children))


def _same_shape(a, b) -> bool:
    """Iterative equivalent of `_shape(a) == _shape(b)`, safe on a tree deep
    enough that building `_shape`'s nested tuple would itself recurse past
    the limit (used only by the deep-chain test below)."""
    stack = [(a, b)]
    while stack:
        x, y = stack.pop()
        if (x.kind, x.field, x.start, x.end) != (y.kind, y.field, y.start, y.end):
            return False
        if len(x.children) != len(y.children):
            return False
        stack.extend(zip(x.children, y.children))
    return True


def test_there_are_9_cases():
    # The brief's brief.md draft named 18, carried over from an earlier
    # version of the fixture file; `test/corpus/operator_precedence_test.txt`
    # has 9 `====`-delimited cases today (verified: 9 name blocks, each with
    # its own `----` divider -- `grep -c` on the header marker and a direct
    # `fixtures.extract` count agree). Reported per task-10 ruling 5 rather
    # than silently kept at the stale number.
    assert len(CASES) == 9


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name[:60])
def test_recompose_matches_fixture(al_parser, case):
    root, _, problems = ir.from_tree(al_parser.parse(case.source))
    assert problems == []
    chains = _chains(root)
    # Checked case by case (see task-10-report.md): every one of the 9 cases
    # carries at least one binary chain -- including the two case titles that
    # mention "range" or a case pattern, because the chain sits *beside* the
    # non-binary `range_expression`/`case_branch` container, not inside a
    # binary node itself. So the requirement is unconditional here.
    assert chains, case.name
    for ch in chains:
        rebuilt = expression.compose(expression.flatten(ch), ch.field)
        assert _shape(rebuilt) == _shape(ch), case.name


def _deep_chain(depth, kind="additive_expression", op_kind="+"):
    """A left-deep binary chain `depth` operators tall: ((...((a op a) op a) op a...) op a)."""
    node = Node("identifier", True, "left", 0, 1, [])
    pos = 1
    for _ in range(depth):
        rhs = Node("identifier", True, "right", pos, pos + 1, [])
        op = Node(op_kind, False, "operator", pos, pos + 1, [])
        node = Node(kind, True, node.field, node.start, pos + 1,
                    [node.copy(field="left"), op, rhs])
        pos += 1
    return node


def test_flatten_iterative_matches_recursive_contract_on_a_small_chain():
    """Pins the iterative flatten() against the recursive contract stated in
    the brief, on a chain small enough to run the recursive version too."""
    def recursive_flatten(node):
        if node.kind not in expression.BINARY_KINDS:
            return [node]
        left, op, right = expression._parts(node)
        return recursive_flatten(left) + [op] + recursive_flatten(right)

    chain = _deep_chain(50)
    assert expression.flatten(chain) == recursive_flatten(chain)


def test_flatten_handles_a_chain_deeper_than_the_recursion_limit():
    """Real BC.History chains run thousands of operators deep. Build one well
    beyond sys.getrecursionlimit() and prove the iterative flatten() does not
    recurse: a recursive implementation would raise RecursionError here."""
    depth = sys.getrecursionlimit() * 3
    chain = _deep_chain(depth)
    flat = expression.flatten(chain)
    assert len(flat) == 2 * depth + 1
    # alternates operand, operator, operand, ...
    assert all(n.kind == "identifier" for n in flat[0::2])
    assert all(n.kind == "+" for n in flat[1::2])
    # and it really does recompose back to the same shape (compared
    # iteratively -- see _same_shape's docstring)
    rebuilt = expression.compose(flat, chain.field)
    assert _same_shape(rebuilt, chain)


def test_in_is_as_are_plain_binary_nodes_with_keyword_wrapped_operators(al_parser):
    """Pins ruling 1: in_expression/is_expression/as_expression stay in
    BINARY_KINDS (they are plain left/operator/right nodes), but their
    operator field is a named `*_keyword` node, not a bare anonymous token."""
    src = b"""interface IProbe
{
}

codeunit 50100 Prec
{
    procedure P(X: Interface IProbe)
    var
        Flag: Boolean;
    begin
        Flag := X as IProbe is IProbe;
    end;
}
"""
    root, _, problems = ir.from_tree(al_parser.parse(src))
    assert problems == []
    chains = _chains(root)
    assert len(chains) == 1
    flat = expression.flatten(chains[0])
    ops = flat[1::2]
    assert [op.kind for op in ops] == ["as_keyword", "is_keyword"]
    assert [expression.op_text(op) for op in ops] == ["as", "is"]
