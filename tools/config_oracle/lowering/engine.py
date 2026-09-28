"""Recursive lowering of the multi-configuration IR to one configuration (spec section 3).

Rules that are load-bearing:
  * no default handler -- an unregistered special node fails;
  * every leaf of the ORIGINAL tree is accounted exactly once, and exactly the
    leaves accounted `kept` are emitted;
  * a fragment may only pass up through a node when the child it came from is
    that node's last original child, and must be consumed by a named consumer;
  * the only normalisation is removing an EMPTY_REMOVABLE container that
    lowering emptied.

Lowering only selects and relabels. It never sees the reference parse (this
package imports nothing from reference.py, tree_sitter, or the loader).
"""
from __future__ import annotations

import collections
from dataclasses import dataclass, field

from tools.config_oracle import contracts
from tools.config_oracle.compare import _run_with_deep_stack
from tools.config_oracle.ir import Node, recompute_span

# Content-only containers the grammar wraps in optional(field(...)) (spec section 2).
EMPTY_REMOVABLE = {
    "statement_block",   # code_block: optional(field('body', $.statement_block))
    "declaration_body",  # _declaration_body_block: optional(field('body', $.declaration_body))
    "var_body",          # var_section: optional(field('body', $.var_body))
    "case_body",         # case_statement: optional(field('body', $.case_body))
    # dataset_section: optional(field('body', $.dataset_body)) (grammar.js:2664).
    "dataset_body",
    # _layout_container_body_block, shared by group/repeater/cuegroup/fixed/grid_section,
    # and preproc_split_container_reopen (both branches): optional(field('body',
    # $.layout_container_body)) (grammar.js:4687, 4708, 4710).
    "layout_container_body",
}

STATEMENT_HOSTS = {"statement_block", "case_branch"}


class LoweringError(Exception):
    def __init__(self, kind, node, detail=""):
        super().__init__(f"{kind} at {node.kind}@{node.start}{': ' + detail if detail else ''}")
        self.kind, self.node, self.detail = kind, node, detail


@dataclass
class Frag:
    anchor: Node | None


@dataclass
class Terminator(Frag):
    leaf: Node


@dataclass
class Following(Frag):
    statements: list


@dataclass
class BlockCompletion(Frag):
    statements: list
    end: Node


@dataclass
class ElseAttachment(Frag):
    else_kw: Node
    branch: Node


@dataclass
class Lowered:
    nodes: list
    frags: list = field(default_factory=list)


class Accounting:
    def __init__(self, resolution):
        self.active = resolution.active
        self.leaf = {}

    def mark(self, node, reason):
        for lf in node.leaves():
            # A kept leaf must lie on a surviving line and an inactive-arm leaf on a
            # masked one. Zero-width leaves carry no bytes, so nothing to check.
            if lf.end > lf.start and reason in ("kept", "inactive-arm")                     and bool(self.active[lf.start]) != (reason == "kept"):
                raise LoweringError("accounting", lf, f"{reason} leaf on a line that is "
                                    f"{'masked' if reason == 'kept' else 'active'}")
            key = (lf.start, lf.end, lf.kind)
            if key in self.leaf:
                raise LoweringError("accounting", lf, f"leaf accounted twice: {self.leaf[key]} then {reason}")
            self.leaf[key] = reason

    def check_complete(self, root):
        for lf in root.leaves():
            if (lf.start, lf.end, lf.kind) not in self.leaf:
                raise LoweringError("accounting", lf, "leaf never accounted")

    def check_emitted(self, low):
        """Every leaf accounted as `kept` appears in the output exactly once, and
        nothing else does. Keyed by interval only: a token alias changes kind."""
        kept = collections.Counter((s, e) for (s, e, _), why in self.leaf.items() if why == "kept")
        emitted = collections.Counter((lf.start, lf.end) for lf in low.leaves()) if low.children             else collections.Counter()
        if kept != emitted:
            missing = sorted((kept - emitted).elements())[:3]
            extra = sorted((emitted - kept).elements())[:3]
            raise LoweringError("accounting", low, f"kept-but-not-emitted {missing}, emitted-but-not-kept {extra}")


@dataclass
class Ctx:
    resolution: object
    accounting: Accounting
    parent_kind: str | None = None
    slot: str | None = None
    normalised: list = field(default_factory=list)

    def child(self, parent_kind, slot):
        return Ctx(self.resolution, self.accounting, parent_kind, slot, self.normalised)

    def policy(self, entry, node):
        host = f"{self.parent_kind}:{self.slot}"
        if host not in entry.hosts:
            raise LoweringError("policy-host", node, f"{entry.type} not registered in {host}")
        return entry.hosts[host]


def _is_special(kind):
    return kind.startswith("preproc") or kind in contracts.SPECIAL_NON_PREFIXED


def lower(node, ctx) -> Lowered:
    if _is_special(node.kind):
        entry = contracts.REGISTRY.get(node.kind)
        if entry is None:
            raise LoweringError("unregistered-type", node)
        if entry.kind == "unsupported" or entry.handler is None:
            raise LoweringError("unsupported-type", node)
        return contracts.resolve_handler(entry)(node, ctx)
    return _lower_ordinary(node, ctx)


def _lower_ordinary(node, ctx) -> Lowered:
    if not node.children:
        ctx.accounting.mark(node, "kept")
        return Lowered([node.copy(children=[])])
    kids, frags = [], []
    last_index = len(node.children) - 1
    for i, c in enumerate(node.children):
        r = lower(c, ctx.child(node.kind, c.field or "<children>"))
        for f in r.frags:
            f._from_last = (i == last_index)
        kids.extend(r.nodes)
        frags.extend(r.frags)
    new = Node(node.kind, node.named, node.field, node.start, node.end, kids)
    frags = _consume(new, frags)
    for f in frags:
        if not getattr(f, "_from_last", False):
            raise LoweringError("unconsumed-fragment", node, f"{type(f).__name__} not from the last child")
        f.anchor = new
    if not new.children:
        if node.kind in EMPTY_REMOVABLE:
            ctx.normalised.append(f"removed-empty:{node.kind}@{node.start}")
            return Lowered([], frags)
        raise LoweringError("empty-node", node)
    return Lowered([_span_from_children(new)], frags)


def _span_from_children(node):
    # Every child is already lowered with its span set from its own leaves, so
    # the first child's start / last child's end ARE the first/last leaf's.
    # O(1), where recompute_span is O(subtree) -- O(depth^2) on a deep chain.
    node.start, node.end = node.children[0].start, node.children[-1].end
    return node


def _consume(new, frags):
    rest = []
    for f in frags:
        if isinstance(f, BlockCompletion) and new.kind == "code_block":
            body = next((c for c in new.children if c.field == "body"), None)
            if f.statements:
                if body is None:
                    body = Node("statement_block", True, "body", 0, 0, [])
                    new.children.insert(1, body)
                body.children.extend(f.statements)
                recompute_span(body)
            new.children.append(f.end)
        elif isinstance(f, ElseAttachment) and new.kind == "if_statement" and f.anchor is not None \
                and f.anchor.field == "then_branch" and any(c is f.anchor for c in new.children):
            new.children.append(f.else_kw)
            new.children.append(f.branch.copy(field="else_branch"))
        elif isinstance(f, (Terminator, Following)) and new.kind in STATEMENT_HOSTS \
                and any(c is f.anchor for c in new.children):
            at = next(i for i, c in enumerate(new.children) if c is f.anchor) + 1
            insert = [f.leaf] if isinstance(f, Terminator) else list(f.statements)
            new.children[at:at] = insert
        else:
            rest.append(f)
    return rest


def _lower_tree(root, extras, resolution):
    acc = Accounting(resolution)
    ctx = Ctx(resolution, acc)
    out = lower(root, ctx)
    if out.frags:
        raise LoweringError("unconsumed-fragment", root, ", ".join(type(f).__name__ for f in out.frags))
    low = out.nodes[0] if out.nodes else Node(root.kind, root.named, None, 0, 0, [])
    acc.check_complete(root)
    acc.check_emitted(low)
    kept = [e for e in extras if resolution.active[e.start]]
    return low, kept, list(ctx.normalised)


def lower_tree(root, extras, resolution):
    """-> (lowered root, kept extras, normalisations). Runs under the comparator's
    deep-stack helper: real trees reach depth ~1,400 and `lower` is recursive."""
    return _run_with_deep_stack(_lower_tree, root, extras, resolution)
