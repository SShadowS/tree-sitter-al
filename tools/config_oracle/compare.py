"""The three checks of spec section 2. Nodes are matched by PROVENANCE, never by text."""
from __future__ import annotations

import collections
from dataclasses import dataclass

_WS = frozenset(b" \t\r\n\f\v")
_CRLF = frozenset(b"\r\n")
_BOM = b"\xef\xbb\xbf"


@dataclass(frozen=True)
class Discrepancy:
    check: str
    kind: str
    path: str
    detail: str


def discrepancy_id(input_id: str, config: str, d: Discrepancy) -> str:
    def esc(s: str) -> str:
        return s.replace("|", "%7C")
    return "|".join(esc(s) for s in (input_id, config, d.check, d.kind, d.path))


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
        # Only \r/\n survive masking unmasked (directives.py's `blank()` leaves
        # them alone to keep line structure); every other masked byte a leaf or
        # extra covers -- whitespace included -- is a real discrepancy.
        if not active[k] and count[k] and b not in _CRLF:
            masked.append(k)
    out = []
    for kind, offs in (("uncovered", uncovered), ("double", double), ("masked", masked)):
        for s, e in _runs(offs):
            out.append(Discrepancy("coverage", kind, f"{side}@{s}", f"bytes {s}..{e}"))
    return sorted(out, key=lambda d: (d.kind, d.path))


def _leaf_set(node):
    """The node's provenance signature: every leaf it covers, including zero-width ones."""
    return frozenset((l.start, l.end, l.kind) for l in node.leaves())


def _path_elem(n):
    lv = n.leaves()
    s, e = (lv[0].start, lv[0].end) if lv else (n.start, n.start)
    return f"{n.kind}.{n.field or '-'}@{s}-{e}"


def _find_matching(node, target, path):
    """DFS for the first node in `node`'s own subtree whose leaf set equals `target`,
    returning (node, its real ref-tree path) so a moved subtree is reported at
    where it actually lives, not at the shallower path of the ref child it overlaps."""
    if _leaf_set(node) == target:
        return node, path
    for c in node.children:
        found = _find_matching(c, target, f"{path}/{_path_elem(c)}")
        if found is not None:
            return found
    return None


def _primary_match(candidate_leafsets, target):
    """Index of the candidate with the largest overlap with `target`; ties go to
    the earliest (first) candidate. None if every overlap is 0."""
    best_i, best_overlap = None, 0
    for i, ls in enumerate(candidate_leafsets):
        overlap = len(ls & target)
        if overlap > best_overlap:
            best_i, best_overlap = i, overlap
    return best_i


def structure(ref, low):
    """Top-down alignment by leaf-interval overlap (never by kind/field/text).

    Each level aligns r.children against l.children independently: a low child is
    "extra" only if it overlaps nothing in ref; a ref child is "missing" only if
    nothing in low overlaps it (and its leaf set was not already explained as a
    `parent` move discovered at a shallower level -- `claimed` carries that fact
    down through the recursion so a single reparented subtree is reported once,
    at its shallowest point of divergence, not again as `missing` where it used
    to live).
    """
    out = []
    claimed = set()

    def align(r, l, path):
        if r.kind != l.kind or r.named != l.named:
            out.append(Discrepancy("structure", "kind", path, f"{r.kind} vs {l.kind}"))
        if r.field != l.field:
            out.append(Discrepancy("structure", "field", path, f"{r.field} vs {l.field}"))

        r_leafsets = [_leaf_set(c) for c in r.children]
        l_leafsets = [_leaf_set(c) for c in l.children]
        r_primary = [_primary_match(l_leafsets, ls) for ls in r_leafsets]
        l_primary = [_primary_match(r_leafsets, ls) for ls in l_leafsets]

        mutual_r, mutual_l = {}, {}
        for ri, li in enumerate(r_primary):
            if li is not None and l_primary[li] == ri:
                mutual_r[ri] = li
                mutual_l[li] = ri

        for ri, rc in enumerate(r.children):
            if ri in mutual_r:
                continue
            if r_leafsets[ri] in claimed:
                continue
            out.append(Discrepancy("structure", "missing", f"{path}/{_path_elem(rc)}", rc.kind))

        for li, lc in enumerate(l.children):
            if li in mutual_l:
                continue
            ref_i = l_primary[li]
            if ref_i is None:
                out.append(Discrepancy("structure", "extra", f"{path}/{_path_elem(lc)}", lc.kind))
                continue
            # Overlaps some ref child but isn't its mutual match: regrouped/moved.
            overlapped = r.children[ref_i]
            found = _find_matching(overlapped, l_leafsets[li], f"{path}/{_path_elem(overlapped)}")
            if found is not None:
                found_node, found_path = found
                claimed.add(l_leafsets[li])
                out.append(Discrepancy("structure", "parent", found_path, found_node.kind))
            else:
                out.append(Discrepancy("structure", "parent", f"{path}/{_path_elem(lc)}", lc.kind))

        r_order = list(mutual_r.keys())                                    # r.children order
        l_order = sorted(r_order, key=lambda ri: mutual_r[ri])             # same pairs, by l position
        if r_order != l_order:
            out.append(Discrepancy("structure", "order", path, r.kind))

        for ri, li in mutual_r.items():
            rc, lc = r.children[ri], l.children[li]
            align(rc, lc, f"{path}/{_path_elem(rc)}")

    align(ref, low, _path_elem(ref))
    return out


def leaf_boundaries(ref, low):
    """The two trees must tokenize the source identically -- same leaf (start, end)
    intervals -- independent of what kind/field/nesting a check disagrees about."""
    r = sorted((l.start, l.end) for l in ref.leaves())
    l = sorted((l.start, l.end) for l in low.leaves())
    if r == l:
        return []
    for i, (a, b) in enumerate(zip(r, l)):
        if a != b:
            return [Discrepancy("structure", "boundary", "<root>", f"ref {a} vs low {b} at index {i}")]
    i = min(len(r), len(l))
    a = r[i] if i < len(r) else None
    b = l[i] if i < len(l) else None
    return [Discrepancy("structure", "boundary", "<root>", f"ref {a} vs low {b} at index {i}")]


def trivia(events, ref_extras, low_extras):
    def counted(xs):
        return collections.Counter((x.kind, x.start) for x in xs)
    ev, rf, lw = counted(events), counted(ref_extras), counted(low_extras)
    out = []
    for name, side in (("reference", rf), ("lowered", lw)):
        # Counter subtraction keeps only strictly-positive counts, so a side that
        # has MORE copies of the same (kind, start) than `events` does is flagged
        # -- a duplicated extra is reported, not hidden by a plain set difference.
        for (kind, start), _n in sorted((ev - side).items()):
            out.append(Discrepancy("trivia", "missing", f"{name}@{start}", kind))
        for (kind, start), _n in sorted((side - ev).items()):
            out.append(Discrepancy("trivia", "extra", f"{name}@{start}", kind))
    ends_ref = {(x.kind, x.start): x.end for x in ref_extras}
    for x in low_extras:
        if (x.kind, x.start) in ends_ref and ends_ref[(x.kind, x.start)] != x.end:
            out.append(Discrepancy("trivia", "extent", f"lowered@{x.start}", x.kind))
    return out
