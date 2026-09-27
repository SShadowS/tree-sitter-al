"""Independent recognition and evaluation of AL conditional directives.

The semantics are the COMPILER's, recorded in docs/preproc-directive-semantics.md
and established by tools/config_oracle/probe_alc.py. Nothing here consults the
grammar or imports tree_sitter: a resolver that read the tree would let a
grammar bug hide itself (spec section 1).
"""
from __future__ import annotations

import re
from dataclasses import dataclass


class ResolveError(Exception):
    """A construct outside the probed semantics. Reported as cannot-validate."""

    def __init__(self, reason: str, offset: int, detail: str = ""):
        super().__init__(f"{reason} at byte {offset}{': ' + detail if detail else ''}")
        self.reason = reason
        self.offset = offset


@dataclass(frozen=True)
class Sym:
    name: str


@dataclass(frozen=True)
class Lit:
    value: bool


@dataclass(frozen=True)
class Not:
    operand: object


@dataclass(frozen=True)
class And:
    left: object
    right: object


@dataclass(frozen=True)
class Or:
    left: object
    right: object


@dataclass(frozen=True)
class Condition:
    expr: object
    start: int
    end: int
    symbols: frozenset


_TOKEN = re.compile(rb"[ \t]*(?:(?P<ident>[A-Za-z_][A-Za-z0-9_]*)|(?P<punct>[()])|(?P<comment>//.*)|(?P<block>/\*)|(?P<other>\S))")
_KEYWORDS = {b"and", b"or", b"not"}
_LITERALS = {b"true": True, b"false": False}


def _tokens(buf: bytes, start: int, end: int):
    pos = start
    out = []
    while pos < end:
        m = _TOKEN.match(buf, pos, end)
        if not m or m.end() == pos:
            break
        if m.group("comment") is not None:
            break
        if m.group("block") is not None:
            raise ResolveError("block-comment-on-directive", m.start("block"))
        if m.group("other") is not None:
            raise ResolveError("unsupported-condition-token", m.start("other"), m.group("other").decode("latin-1"))
        kind = "ident" if m.group("ident") is not None else "punct"
        out.append((kind, m.group(kind), m.start(kind), m.end(kind)))
        pos = m.end()
    return out


def parse_condition(buf: bytes, start: int, end: int) -> Condition:
    """Parse the condition occupying buf[start:end] (the text after `#if`/`#elif`)."""
    toks = _tokens(buf, start, end)
    if not toks:
        raise ResolveError("empty-condition", start)
    pos = 0
    symbols: set[str] = set()

    def peek_kw():
        if pos < len(toks) and toks[pos][0] == "ident":
            return toks[pos][1].lower()
        return None

    def primary():
        nonlocal pos
        if pos >= len(toks):
            raise ResolveError("unsupported-condition", end, "operand expected")
        kind, text, s, _ = toks[pos]
        if kind == "punct" and text == b"(":
            pos += 1
            inner = or_expr()
            if pos >= len(toks) or toks[pos][1] != b")":
                raise ResolveError("unsupported-condition", s, "unbalanced parenthesis")
            pos += 1
            return inner
        if kind == "ident" and text.lower() in _KEYWORDS:
            raise ResolveError("unsupported-condition", s, "operator where an operand is required")
        if kind == "ident":
            pos += 1
            if text.lower() in _LITERALS:
                return Lit(_LITERALS[text.lower()])
            symbols.add(text.decode("ascii"))
            return Sym(text.decode("ascii"))
        raise ResolveError("unsupported-condition", s)

    def unary():
        nonlocal pos
        if peek_kw() == b"not":
            pos += 1
            return Not(unary())
        return primary()

    def and_expr():
        nonlocal pos
        left = unary()
        while peek_kw() == b"and":
            pos += 1
            left = And(left, unary())
        return left

    def or_expr():
        nonlocal pos
        left = and_expr()
        while peek_kw() == b"or":
            pos += 1
            left = Or(left, and_expr())
        return left

    expr = or_expr()
    if pos != len(toks):
        raise ResolveError("unsupported-condition", toks[pos][2], "trailing token")
    return Condition(expr, toks[0][2], toks[-1][3], frozenset(symbols))


def evaluate(expr, env: frozenset) -> bool:
    if isinstance(expr, Sym):
        return expr.name in env
    if isinstance(expr, Lit):
        return expr.value
    if isinstance(expr, Not):
        return not evaluate(expr.operand, env)
    if isinstance(expr, And):
        return evaluate(expr.left, env) and evaluate(expr.right, env)
    if isinstance(expr, Or):
        return evaluate(expr.left, env) or evaluate(expr.right, env)
    raise TypeError(expr)
