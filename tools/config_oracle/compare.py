"""The three checks of spec section 2. Nodes are matched by PROVENANCE, never by text."""
from __future__ import annotations

from dataclasses import dataclass

_WS = frozenset(b" \t\r\n\f\v")
_BOM = b"\xef\xbb\xbf"


@dataclass(frozen=True)
class Discrepancy:
    check: str
    kind: str
    path: str
    detail: str


def discrepancy_id(input_id: str, config: str, d: Discrepancy) -> str:
    return f"{input_id}|{config}|{d.check}|{d.kind}|{d.path}"


def _runs(offsets):
    out, prev, start = [], None, None
    for o in offsets:
        if prev is None or o != prev + 1:
            if start is not None:
                out.append((start, prev + 1))
            start = o
        prev = o
    if start is not None:
        out.append((start, prev + 1))
    return out


def coverage(source, active, root, extras, side):
    count = [0] * len(source)
    spans = [(l.start, l.end) for l in root.leaves() if l.end > l.start] + [(e.start, e.end) for e in extras]
    for s, e in spans:
        for k in range(s, e):
            count[k] += 1
    lead = len(_BOM) if source.startswith(_BOM) else 0
    uncovered, double, masked = [], [], []
    for k, b in enumerate(source):
        significant = active[k] and b not in _WS and k >= lead
        if significant and count[k] == 0:
            uncovered.append(k)
        if count[k] > 1 and b not in _WS:
            double.append(k)
        if not active[k] and count[k] and b not in _WS:
            masked.append(k)
    out = []
    for kind, offs in (("uncovered", uncovered), ("double", double), ("masked", masked)):
        for s, e in _runs(offs):
            out.append(Discrepancy("coverage", kind, f"{side}@{s}", f"bytes {s}..{e}"))
    return sorted(out, key=lambda d: (d.kind, d.path))


def _index(root):
    idx = {}
    order = {}

    def walk(n, parent_key, path, same_chain):
        # SORTED leaf intervals: a node is identified by the material it covers,
        # so reordering its children is reported as `order`, not missing+extra.
        leafs = tuple(sorted(n.leaf_intervals()))
        first = leafs[0][0] if leafs else n.start
        depth = same_chain.get(leafs, 0)
        key = (first, leafs, depth)
        p = f"{path}/{n.kind}.{n.field or '-'}@{first}" if path else f"{n.kind}.{n.field or '-'}@{first}"
        idx[key] = (n, parent_key, p)
        chain = {leafs: depth + 1}
        order[key] = [walk(c, key, p, chain if tuple(sorted(c.leaf_intervals())) == leafs else {})
                      for c in n.children]
        return key

    walk(root, None, "", {})
    return idx, order


def structure(ref, low):
    ri, ro = _index(ref)
    li, lo = _index(low)
    out = []
    for key, (n, parent, path) in ri.items():
        if key not in li:
            if parent is None or parent in li:          # report the topmost missing node only
                out.append(Discrepancy("structure", "missing", path, n.kind))
            continue
        m, lparent, _ = li[key]
        if n.kind != m.kind or n.named != m.named:
            out.append(Discrepancy("structure", "kind", path, f"{n.kind} vs {m.kind}"))
        if n.field != m.field:
            out.append(Discrepancy("structure", "field", path, f"{n.field} vs {m.field}"))
        if parent != lparent:
            out.append(Discrepancy("structure", "parent", path, n.kind))
    for key, (m, parent, path) in li.items():
        if key not in ri and (parent is None or parent in ri):
            out.append(Discrepancy("structure", "extra", path, m.kind))
    for key, kids in ro.items():
        if key in lo:
            a = [k for k in kids if k in lo[key]]
            b = [k for k in lo[key] if k in kids]
            if a != b:
                out.append(Discrepancy("structure", "order", ri[key][2], ri[key][0].kind))
    return out


def trivia(events, ref_extras, low_extras):
    def keyed(xs):
        return sorted((x.kind, x.start) for x in xs)
    ev, rf, lw = keyed(events), keyed(ref_extras), keyed(low_extras)
    out = []
    for name, side in (("reference", rf), ("lowered", lw)):
        for item in sorted(set(ev) - set(side)):
            out.append(Discrepancy("trivia", "missing", f"{name}@{item[1]}", item[0]))
        for item in sorted(set(side) - set(ev)):
            out.append(Discrepancy("trivia", "extra", f"{name}@{item[1]}", item[0]))
    ends_ref = {(x.kind, x.start): x.end for x in ref_extras}
    for x in low_extras:
        if (x.kind, x.start) in ends_ref and ends_ref[(x.kind, x.start)] != x.end:
            out.append(Discrepancy("trivia", "extent", f"lowered@{x.start}", x.kind))
    return out
