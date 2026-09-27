"""The comparable form: ordered, field-labelled nodes with leaf provenance (spec section 2)."""
from __future__ import annotations

from dataclasses import dataclass, field, replace


@dataclass
class Node:
    kind: str
    named: bool
    field: str | None
    start: int
    end: int
    children: list = field(default_factory=list)

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
    if node.children:
        node.start = node.children[0].start
        node.end = node.children[-1].end
    return node


def from_tree(tree):
    """Walk with a TreeCursor so fields on anonymous children are captured (like tools/edge-census.c)."""
    extras, problems = [], []
    cursor = tree.walk()

    def visit(field_name):
        n = cursor.node
        if n.is_extra:
            extras.append(Extra(n.type, n.start_byte, n.end_byte))
            return None
        if n.is_error:
            problems.append(f"error@{n.start_byte}")
        if n.is_missing:
            problems.append(f"missing@{n.start_byte}")
        out = Node(n.type, n.is_named, field_name, n.start_byte, n.end_byte, [])
        if cursor.goto_first_child():
            while True:
                child = visit(cursor.field_name)
                if child is not None:
                    out.children.append(child)
                if not cursor.goto_next_sibling():
                    break
            cursor.goto_parent()
        return out

    root = visit(None)
    return root, sorted(extras, key=lambda e: e.start), problems
