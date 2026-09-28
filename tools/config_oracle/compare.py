"""The three checks of spec section 2. Nodes are matched by PROVENANCE, never by text."""
from __future__ import annotations

import collections
import sys
import threading
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


def _tokens(root):
    """The root's leaves; none for a childless root. That root is the empty file of a
    configuration whose whole text is inactive, and `leaves()` would report the root
    itself -- as one leaf spanning every byte, extras included (runner.first_zero_width_leaf
    and Accounting.check_emitted make the same exception)."""
    return root.leaves() if root.children else []


def coverage(source, active, root, extras, side):
    count = [0] * len(source)
    spans = [(l.start, l.end) for l in _tokens(root) if l.end > l.start] + [(e.start, e.end) for e in extras]
    for s, e in spans:
        for k in range(s, e):
            count[k] += 1
    bom = set()
    at = source.find(_BOM)
    while at != -1:
        bom.update(range(at, at + len(_BOM)))
        at = source.find(_BOM, at + len(_BOM))
    uncovered, double, masked = [], [], []
    for k, b in enumerate(source):
        significant = active[k] and b not in _WS and k not in bom
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


def _memoize_leaf_sets(root, leafsets, firsts):
    """Bottom-up, iterative (depth-safe, no Python recursion) precomputation of
    every node's leaf-set and first-leaf-span in root's subtree, keyed by
    id() into the two dicts passed in.

    `Node.leaves()` re-walks a whole subtree from scratch on every call, and
    the alignment below asks for a node's leaf set once per recursion level --
    on a long chain that is an O(depth) walk repeated at O(depth) levels,
    O(depth^2) total (a 10,000-deep synthetic chain took the whole test file
    from under a second to about a minute before this). Building each node's
    leaf set from its own (already-built) children's sets, once, bottom-up,
    is O(nodes) total instead.

    Leaf-set values are SPAN only (start, end), never (span, leaf kind): a
    leaf's own kind can change in place (round 1's rename-kind test; a
    10,000-deep chain with the bottom leaf's kind changed) without moving a
    single byte, and alignment must still match every ancestor up the chain
    on span so the ONE real difference surfaces as a single `kind`
    discrepancy at the leaf, not as every ancestor's leaf set going fully
    disjoint and the whole subtree reading as unrelated missing+extra. The
    outer node's own kind is still compared independently and exactly, by
    `align()`'s own kind check and by `find_move_target`'s explicit `kind`
    parameter -- this only changes what counts as "the same material", not
    whether a kind difference is reported.

    `firsts` separately recovers "the first leaf in document order" for
    `path_elem`, which a frozenset can't give back once leaf identity (and
    order) is discarded.
    """
    stack = [(root, False)]
    while stack:
        n, processed = stack.pop()
        if not processed:
            stack.append((n, True))
            for c in n.children:
                stack.append((c, False))
            continue
        if not n.children:
            leafsets[id(n)] = frozenset({(n.start, n.end)})
            firsts[id(n)] = (n.start, n.end)
        else:
            s = set()
            for c in n.children:
                s |= leafsets[id(c)]
            leafsets[id(n)] = frozenset(s)
            firsts[id(n)] = firsts[id(n.children[0])]


def _primary_match(candidate_leafsets, target):
    """Index of the candidate with the largest overlap with `target`; ties go to
    the earliest (first) candidate. None if every overlap is 0."""
    best_i, best_overlap = None, 0
    for i, ls in enumerate(candidate_leafsets):
        overlap = len(ls & target)
        if overlap > best_overlap:
            best_i, best_overlap = i, overlap
    return best_i


def _run_with_deep_stack(fn, *args):
    """Run fn(*args) on a worker thread with a large C stack and a raised
    recursion limit, so a deeply left-nested tree -- BC.History has real AL
    files with a chain of thousands of binary operators -- doesn't blow
    Python's default recursion limit or the platform's default thread stack.
    The recursive implementation is otherwise untouched: same code, same
    results, just given room to run. Propagates the return value or any
    raised exception back to the calling thread unchanged.

    ponytail: a thread per call is the simplest thing that is provably
    identical to running inline (same functions, same arguments, no shared
    mutable state to race on since each call gets its own `out`/`claimed`).
    If this shows up in a profile, the next step is turning `align()` into an
    explicit worklist instead of raising the limit further.
    """
    result: list = []
    error: list = []

    def runner():
        try:
            result.append(fn(*args))
        except BaseException as exc:   # re-raised on the caller's thread below
            error.append(exc)

    old_limit = sys.getrecursionlimit()
    old_stack = threading.stack_size()
    sys.setrecursionlimit(max(old_limit, 200_000))
    # 64 MiB: comfortably more than 10,000 stacked `align()` frames need, and
    # (unlike 256 MiB) a value `threading.stack_size` actually accepts on Windows.
    threading.stack_size(64 * 1024 * 1024)
    try:
        t = threading.Thread(target=runner)
        t.start()
        t.join()
    finally:
        sys.setrecursionlimit(old_limit)
        threading.stack_size(old_stack)

    if error:
        raise error[0]
    return result[0]


def structure(ref, low):
    """Public entry point for `_structure_impl` (see its docstring for the
    algorithm): runs it on a worker thread with a large stack, so a very deep
    tree can't blow Python's recursion limit. Behaviour is identical to
    calling `_structure_impl` directly."""
    return _run_with_deep_stack(_structure_impl, ref, low)


def _structure_impl(ref, low):
    """Top-down alignment by leaf-interval overlap (never by kind/field/text).

    Each level aligns r.children against l.children in two phases:

    1. MOVE DETECTION. For every low child, search the subtree of any ref child
       it overlaps (excluding that ref child itself) for a descendant with the
       IDENTICAL leaf set and kind. A hit is a move: report `parent` at the
       found node's real path and immediately recurse `align()` on the pair, so
       defects *inside* a moved subtree (a renamed or re-fielded descendant) are
       still reported, not hidden behind the single `parent` finding. The moved
       node's leaves are then subtracted from its (former) ref parent's leaf set
       before overlap pairing runs, and that ref parent is never itself reported
       `missing` for content that demonstrably moved rather than vanished.
    2. Ordinary mutual-primary overlap pairing over whatever is left (as round 1),
       using those leaf-set-reduced ref children. A low child that overlaps a ref
       child without being its mutual partner (true regrouping, not a clean move
       -- e.g. a tied duplicate) still gets `parent` at the same path round 1
       used, but is now also recursed into so inner defects surface there too.

    `claimed` records the identity (never just the leaf set -- two differently-
    kinded wrappers around the same leaves, like a dropped `W(E(x))`, must not
    share a suppression) of every ref node phase 1 already reported and
    re-aligned, so a deeper recursion never re-reports the same move as `missing`
    at its old position.
    """
    out = []
    claimed = set()   # id() of ref nodes already reported+re-aligned as `parent` moves

    leafsets: dict = {}
    firsts: dict = {}
    _memoize_leaf_sets(ref, leafsets, firsts)
    _memoize_leaf_sets(low, leafsets, firsts)

    def path_elem(n):
        s, e = firsts[id(n)]
        return f"{n.kind}.{n.field or '-'}@{s}-{e}"

    def find_matching(node, target, path):
        """DFS for the first node in `node`'s own subtree (INCLUDING itself)
        whose leaf set equals `target`, ignoring kind. Used only for the
        true-regrouping fallback (rule 4): by the time it runs, move
        detection has already exhausted every exact (leaf set, kind) match,
        so this only ever finds a kind-mismatched hit or the overlapped node
        itself (e.g. two low siblings tied for the same ref leaf span -- the
        loser here, never a spot move detection would have claimed)."""
        if leafsets[id(node)] == target:
            return node, path
        for c in node.children:
            found = find_matching(c, target, f"{path}/{path_elem(c)}")
            if found is not None:
                return found
        return None

    def find_move_target(node, target, kind, path):
        """DFS strictly INSIDE `node`'s subtree (never `node` itself -- an
        equal-leafset ref child would already be found as a mutual match by
        ordinary overlap pairing, so excluding it keeps a same-position,
        unmoved node from being misread as a move) for a descendant whose own
        leaf set equals `target` and whose kind equals `kind`. Preorder: a
        wrapper with the right leaf set but the wrong kind (e.g. a dropped
        intermediate node) is walked past, not accepted, so the search keeps
        going to whatever is really behind it."""
        for c in node.children:
            c_path = f"{path}/{path_elem(c)}"
            if c.kind == kind and leafsets[id(c)] == target:
                return c, c_path
            found = find_move_target(c, target, kind, c_path)
            if found is not None:
                return found
        return None

    def align(r, l, path):
        if r.kind != l.kind or r.named != l.named:
            out.append(Discrepancy("structure", "kind", path, f"{r.kind} vs {l.kind}"))
        if r.field != l.field:
            out.append(Discrepancy("structure", "field", path, f"{r.field} vs {l.field}"))

        r_children, l_children = r.children, l.children
        r_full = [leafsets[id(c)] for c in r_children]
        l_leafsets = [leafsets[id(c)] for c in l_children]

        # PHASE 1: move detection.
        moved = {}            # li -> consumed
        moved_leaves = set()  # union of leaves claimed by every move found at this level
        for li, lc in enumerate(l_children):
            target = l_leafsets[li]
            if not target:
                continue
            # An exact (kind, leaf set) match among r's OWN children at this
            # SAME level is lc's unmoved, same-position partner -- never go
            # looking inside it (or a sibling) for a "move". Without this, a
            # node that wraps a same-kind descendant covering the identical
            # leaves (e.g. a self-referential `E(E(x))`) makes an identical
            # tree compare unequal to itself: the inner E gets misread as a
            # move target for the outer, unmoved E.
            if any(rc2.kind == lc.kind and r_full[ri2] == target
                   for ri2, rc2 in enumerate(r_children)):
                continue
            found = None
            for ri, rc in enumerate(r_children):
                if not (r_full[ri] & target):
                    continue
                found = find_move_target(rc, target, lc.kind, f"{path}/{path_elem(rc)}")
                if found is not None:
                    break
            if found is None:
                continue
            rn, rn_path = found
            moved[li] = True   # consumed either way below -- excluded from phase 2
            if id(rn) in claimed:
                # A second low child matching an already-claimed move target:
                # not a second move, a duplicate of the first.
                out.append(Discrepancy("structure", "extra", f"{path}/{path_elem(lc)}", lc.kind))
                continue
            moved_leaves |= target
            claimed.add(id(rn))
            out.append(Discrepancy("structure", "parent", rn_path, rn.kind))
            align(rn, lc, rn_path)

        # PHASE 2: mutual-primary overlap pairing over what's left, ref leaf sets
        # reduced by whatever moved out of them in phase 1.
        r_reduced = [ls - moved_leaves for ls in r_full]
        remaining = [li for li in range(len(l_children)) if li not in moved]
        rem_leafsets = [l_leafsets[li] for li in remaining]

        r_primary = [remaining[i] if (i := _primary_match(rem_leafsets, ls)) is not None else None
                     for ls in r_reduced]
        l_primary: list[int | None] = [None] * len(l_children)
        for li in remaining:
            l_primary[li] = _primary_match(r_reduced, l_leafsets[li])

        mutual_r, mutual_l = {}, {}
        for ri, li in enumerate(r_primary):
            if li is not None and l_primary[li] == ri:
                mutual_r[ri] = li
                mutual_l[li] = ri

        for ri, rc in enumerate(r_children):
            if ri in mutual_r:
                continue
            if not r_reduced[ri]:          # all its content moved out and was reported
                continue
            if id(rc) in claimed:
                continue
            out.append(Discrepancy("structure", "missing", f"{path}/{path_elem(rc)}", rc.kind))

        for li, lc in enumerate(l_children):
            if li in moved or li in mutual_l:
                continue
            ref_i = l_primary[li]
            if ref_i is None:
                out.append(Discrepancy("structure", "extra", f"{path}/{path_elem(lc)}", lc.kind))
                continue
            # True regrouping: overlaps a ref child, isn't a move, isn't mutual
            # (e.g. a tied duplicate that lost the "earliest" tie-break).
            overlapped = r_children[ref_i]
            overlapped_path = f"{path}/{path_elem(overlapped)}"
            found = find_matching(overlapped, l_leafsets[li], overlapped_path)
            if found is not None:
                found_node, found_path = found
                out.append(Discrepancy("structure", "parent", found_path, found_node.kind))
            else:
                out.append(Discrepancy("structure", "parent", f"{path}/{path_elem(lc)}", lc.kind))
            align(overlapped, lc, overlapped_path)

        r_order = list(mutual_r.keys())                                    # r.children order
        l_order = sorted(r_order, key=lambda ri: mutual_r[ri])             # same pairs, by l position
        if r_order != l_order:
            out.append(Discrepancy("structure", "order", path, r.kind))

        for ri, li in mutual_r.items():
            rc, lc = r_children[ri], l_children[li]
            align(rc, lc, f"{path}/{path_elem(rc)}")

    align(ref, low, path_elem(ref))
    return out


def leaf_boundaries(ref, low):
    """The two trees must tokenize the source identically -- same leaf (start, end)
    intervals -- independent of what kind/field/nesting a check disagrees about."""
    r = sorted((l.start, l.end) for l in _tokens(ref))
    l = sorted((l.start, l.end) for l in _tokens(low))
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
    # Ends are checked against the RESOLVER on each side, not only tree against tree: an
    # extra that swallows the same code in both parses agrees with itself and is still wrong.
    ends = {(x.kind, x.start): x.end for x in events}
    for name, xs in (("reference", ref_extras), ("lowered", low_extras)):
        for x in xs:
            if (x.kind, x.start) in ends and ends[(x.kind, x.start)] != x.end:
                out.append(Discrepancy("trivia", "extent", f"{name}@{x.start}", x.kind))
    return out
