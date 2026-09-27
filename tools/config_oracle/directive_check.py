"""Tree directives against source directives, by EXTENT (spec section 3, "Branch selection")."""
from __future__ import annotations

from tools.config_oracle.compare import Discrepancy

_TREE_KIND = {"preproc_if": "if", "preproc_elif": "elif", "preproc_else": "else", "preproc_endif": "endif"}


def _tree_directives(root):
    out, stack = [], [root]
    while stack:
        n = stack.pop()
        if n.kind in _TREE_KIND:
            out.append(n)
            continue
        stack.extend(n.children)
    return sorted(out, key=lambda n: n.start)


def check(root, disc):
    src = {d.hash: d for d in disc.directives}
    out, seen = [], set()
    for n in _tree_directives(root):
        d = src.get(n.start)
        path = f"{n.kind}@{n.start}"
        if d is None or d.kind != _TREE_KIND[n.kind]:
            out.append(Discrepancy("directive", "unmatched-tree", path, n.kind))
            continue
        seen.add(d.hash)
        if d.kind in ("if", "elif"):
            cond = next((c for c in n.children if c.field == "condition"), None)
            if cond is None or (cond.start, cond.end) != (d.cond.start, d.cond.end):
                got = None if cond is None else (cond.start, cond.end)
                out.append(Discrepancy("directive", "condition-extent", path,
                                       f"tree {got} vs source {(d.cond.start, d.cond.end)}"))
            if n.end != d.next_line:
                out.append(Discrepancy("directive", "end-extent", path, f"tree {n.end} vs source {d.next_line}"))
        elif n.end != d.keyword_end:
            out.append(Discrepancy("directive", "end-extent", path, f"tree {n.end} vs source {d.keyword_end}"))
    for h, d in sorted(src.items()):
        if h not in seen:
            out.append(Discrepancy("directive", "unmatched-source", f"{d.kind}@{h}", d.kind))
    return out
