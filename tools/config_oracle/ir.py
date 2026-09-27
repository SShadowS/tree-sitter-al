"""The comparable form: ordered, field-labelled nodes with leaf provenance (spec section 2)."""
from __future__ import annotations

from dataclasses import dataclass, field as _field, replace


@dataclass
class Node:
    kind: str
    named: bool
    field: str | None
    start: int
    end: int
    children: list = _field(default_factory=list)

    def leaves(self) -> list:
        if not self.children:
            return [self]
        out = []
        stack = [iter(self.children)]
        while stack:
            nxt = next(stack[-1], None)
            if nxt is None:
                stack.pop()
            elif nxt.children:
                stack.append(iter(nxt.children))
            else:
                out.append(nxt)
        return out

    def leaf_intervals(self) -> tuple:
        return tuple((l.start, l.end) for l in self.leaves())

    def copy(self, **changes) -> "Node":
        return replace(self, **changes)


@dataclass(frozen=True)
class Extra:
    kind: str
    start: int
    end: int


def recompute_span(node: Node) -> Node:
    """Set start/end from the node's leaves (its contract), not from children's cached spans.

    A no-op for a node with no children -- `leaves()` would return `[node]` itself
    for that case, which would be a no-op anyway, but the guard makes the "no
    children" case explicit rather than relying on that coincidence.
    """
    if node.children:
        leaves = node.leaves()
        node.start = leaves[0].start
        node.end = leaves[-1].end
    return node


def from_tree(tree):
    """Walk with a TreeCursor so fields on anonymous children are captured (like tools/edge-census.c).

    An ERROR node can itself be `is_extra` (e.g. an unterminated block comment, or
    a run of garbage tokens the scanner lexes as filler between real
    constructs) -- the grammar's error recovery and its extras handling
    overlap for these. Such a node's error/missing status is recorded as a
    problem BEFORE the extras check runs, for every node, so this case is never
    silently dropped. Its subtree is still walked afterwards so problems nested
    inside it (further errors, MISSING tokens) are not lost either. But the
    node itself is deliberately added to neither `extras` (it is not one of the
    grammar's real extras: comment/pragma/preproc_*) nor the structural tree
    (its content is malformed, not a well-formed child of its parent) --
    there is no sensible home for it in either list.

    Iterative (explicit stack, no Python recursion): a real BC.History file can
    carry a chain of thousands of left-associative binary operators, which
    parses into a tree thousands of levels deep -- deep enough to blow Python's
    default recursion limit. `stack` replaces the call stack a recursive
    `visit()` would use; `enter()` makes exactly the same per-node decision a
    recursive visit would (problems recorded before the extras check runs; a
    plain extra is never descended into -- `cursor.goto_first_child()` is
    never even called for it, so the cursor is left exactly where `visit()`
    would have left it; an error-that-is-extra IS descended into, for nested
    problems, but contributes nothing to the tree), just without recursing.
    """
    extras, problems = [], []
    cursor = tree.walk()

    def enter(field_name):
        """Handle the node currently under the cursor without moving it.
        Returns (out_or_None, descend): `out_or_None` is what this node
        contributes to its parent's children (None for anything that is not a
        real tree node -- either kind of extra); `descend` says whether the
        driver should even attempt `cursor.goto_first_child()` for it."""
        n = cursor.node
        if n.is_error:
            problems.append(f"error@{n.start_byte}")
        if n.is_missing:
            problems.append(f"missing@{n.start_byte}")
        if n.is_extra:
            if n.is_error:
                return None, True       # descend for nested problems; produces nothing
            extras.append(Extra(n.type, n.start_byte, n.end_byte))
            return None, False          # never descended into, same as `visit()`
        return Node(n.type, n.is_named, field_name, n.start_byte, n.end_byte, []), True

    root_out, root_descend = enter(None)
    if root_descend and cursor.goto_first_child():
        stack = [root_out]   # stack[-1] is the `out` (or None) finished children attach to
        reached_root = False
        while not reached_root:
            out, descend = enter(cursor.field_name)
            if descend and cursor.goto_first_child():
                stack.append(out)
                continue
            # Fully resolved right here (leaf, plain extra, or a childless
            # error-extra): hand it to its parent, then advance.
            done = out
            if stack[-1] is not None and done is not None:
                stack[-1].children.append(done)
            if cursor.goto_next_sibling():
                continue
            # Retrace upward through every exhausted ancestor.
            while True:
                if not cursor.goto_parent():
                    reached_root = True
                    break
                done = stack.pop()
                if stack:
                    if stack[-1] is not None and done is not None:
                        stack[-1].children.append(done)
                else:
                    root_out = done
                if cursor.goto_next_sibling():
                    break
    root = root_out

    # Backstop: some MISSING tokens are aliased into a named node (e.g. a
    # missing type name aliased into `identifier`) such that the node itself
    # reports is_missing=False and child_count==0 -- neither the ordinary walk
    # above nor a child-count-based descent can see the MISSING token directly.
    # `has_error` still propagates up from it, though, so when the walk found
    # no problems at all but the root disagrees, descend through has_error
    # children to the deepest one and record that as the problem site.
    if tree.root_node.has_error and not problems:
        n = tree.root_node
        while True:
            child = next((c for c in n.children if c.has_error), None)
            if child is None:
                break
            n = child
        problems.append(f"has-error@{n.start_byte}")

    return root, sorted(extras, key=lambda e: e.start), problems
