"""The tree's `#if`/`#elif` condition grouping against the resolver's (roadmap B1).

The resolver stays the only branch selector. This stage reads each condition node of the
multi-configuration tree into the resolver's own AST classes and makes two comparisons
against the resolver's `parse_condition` AST for the same directive, both reported as a
`directive|condition-structure` discrepancy naming both readings:

- `ast`: the two ASTs must be EQUAL. Normalisation: parentheses are dropped (the resolver
  keeps no paren node, so the tree's `preproc_parenthesized_expression` is read as its
  operand); `true`/`false` are literals on both sides; symbols keep their spelling (they
  are case-sensitive); operators are left-associative on both sides. Nothing else is
  normalised, so this is exact. It sees a wrong grouping that every reached configuration
  happens to evaluate alike (e.g. `#define B` above `#if not A and B`).
- `truth`: the tree's AST, evaluated under the environment the resolver had at that
  directive (`Resolution.env_at`, active `#define`/`#undef` included), must give the
  resolver's value. Redundant while `ast` holds; it is what a branch actually depends on.

Not compared, and counted as skipped: a directive with no tree node at its `#`, one whose
condition extent differs (directive_check's `condition-extent` in the full tier), and every
directive of a tree with errors. Directives the resolver refuses never reach here.
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


SKIP_NO_NODE, SKIP_EXTENT, SKIP_ERRORED_TREE = "no-node", "extent", "errored-tree"


def check(trees, res) -> tuple:
    """-> (discrepancies, number compared, {skip reason: count}) for one configuration.
    `trees` is `tree_conditions(...)`, or None when the multi-configuration tree has errors."""
    out, checked, skipped = [], 0, {}
    for d in res.directives:
        if d.cond is None:
            continue
        t = None if trees is None else trees.get(d.hash)
        why = (SKIP_ERRORED_TREE if trees is None else SKIP_NO_NODE if t is None
               else SKIP_EXTENT if (t[0], t[1]) != (d.cond.start, d.cond.end) else None)
        if why:
            skipped[why] = skipped.get(why, 0) + 1
            continue
        checked += 1
        expr, env = t[2], res.env_at[d.hash]
        if expr != d.cond.expr:
            out.append(Discrepancy("directive", "condition-structure",
                                   f"{d.kind}@{d.hash} ast: tree {show(expr)} vs resolver {show(d.cond.expr)}", ""))
        want = evaluate(d.cond.expr, env)
        got = None if isinstance(expr, Unreadable) else evaluate(expr, env)
        if got != want:
            out.append(Discrepancy("directive", "condition-structure",
                                   f"{d.kind}@{d.hash} truth: tree {show(expr)}={got} "
                                   f"vs resolver {show(d.cond.expr)}={want}", ""))
    return out, checked, skipped
