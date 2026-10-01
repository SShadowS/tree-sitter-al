"""The tree's `#if`/`#elif` condition grouping against the resolver's (roadmap B1).

The resolver stays the only branch selector. This stage reads each condition node of the
multi-configuration tree into the resolver's own AST classes, evaluates it under the
environment the resolver had at that directive (`Resolution.env_at`), and reports a
`condition-structure` discrepancy wherever its truth differs from the resolver's
evaluation of `parse_condition`. Directives the resolver refuses never reach here, and a
condition whose extent differs is `directive_check`'s `condition-extent`, not this.
"""
from __future__ import annotations

from tools.config_oracle.compare import Discrepancy
from tools.config_oracle.directives import And, Lit, Not, Or, Sym, evaluate

_LITERALS = {b"true": True, b"false": False}   # as directives.parse_condition reads them


class Unreadable(Exception):
    """A node kind outside the five a condition is built from."""


def tree_conditions(root, source: bytes) -> dict:
    """{directive hash: (condition start, end, AST or Unreadable)} for every
    preproc_if / preproc_elif in the tree."""
    out, stack = {}, [root]
    while stack:
        n = stack.pop()
        if n.kind in ("preproc_if", "preproc_elif"):
            cond = next((c for c in n.children if c.field == "condition"), None)
            if cond is not None:
                try:
                    expr = _ast(cond, source)
                except Unreadable as e:
                    expr = e
                out[n.start] = (cond.start, cond.end, expr)
            continue
        stack.extend(n.children)
    return out


def _ast(n, source):
    named = [c for c in n.children if c.named]
    if n.kind == "identifier":
        text = source[n.start:n.end]
        lit = _LITERALS.get(text.lower())
        return Lit(lit) if lit is not None else Sym(text.decode("utf-8"))
    if n.kind == "preproc_parenthesized_expression" and len(named) == 1:
        return _ast(named[0], source)
    if n.kind == "preproc_not_expression" and len(named) == 1:
        return Not(_ast(named[0], source))
    if n.kind in ("preproc_and_expression", "preproc_or_expression") and len(named) == 2:
        op = And if n.kind == "preproc_and_expression" else Or
        return op(_ast(named[0], source), _ast(named[1], source))
    raise Unreadable(f"unreadable:{n.kind}@{n.start}")


def show(e) -> str:
    if isinstance(e, Unreadable):
        return str(e)
    if isinstance(e, Sym):
        return e.name
    if isinstance(e, Lit):
        return "true" if e.value else "false"
    if isinstance(e, Not):
        return f"not({show(e.operand)})"
    name = "and" if isinstance(e, And) else "or"
    return f"{name}({show(e.left)},{show(e.right)})"


def check(trees: dict, res) -> tuple:
    """-> (discrepancies, number of conditions compared) for one configuration."""
    out, checked = [], 0
    for d in res.directives:
        t = trees.get(d.hash)
        if d.cond is None or t is None or (t[0], t[1]) != (d.cond.start, d.cond.end):
            continue
        env, expr = res.env_at[d.hash], t[2]
        checked += 1
        want = evaluate(d.cond.expr, env)
        got = None if isinstance(expr, Unreadable) else evaluate(expr, env)
        if got != want:
            out.append(Discrepancy("directive", "condition-structure",
                                   f"{d.kind}@{d.hash}: tree {show(expr)}={got} "
                                   f"vs resolver {show(d.cond.expr)}={want}", ""))
    return out, checked
