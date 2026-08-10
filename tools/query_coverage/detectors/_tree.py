"""Tree traversal shared by every detector.

One implementation, because two hand-copied versions of enclosing_named with
different skip rules drift apart silently — the exact class of quiet wrongness
this harness exists to catch.
"""

from __future__ import annotations

from typing import Iterator


def walk(node) -> Iterator:
    """Every node in the subtree, self first.

    Explicit-stack, not recursive: a deeply nested AL file (long chains of
    binary expressions, deeply nested #if blocks) can exceed Python's default
    recursion limit long before it exceeds the C stack. Children are pushed in
    reverse so the stack still pops them left-to-right, preserving the
    self-then-children, left-to-right order the recursive version produced.
    """
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        stack.extend(reversed(current.children))


def leaves(node) -> Iterator:
    """Childless nodes in byte order.

    Walks ALL children, not named_children: anonymous string tokens such as
    ';' are visible leaves and legitimately provide byte coverage.

    Explicit-stack for the same reason as walk(): reversed() on push is what
    keeps pop() order left-to-right, i.e. byte order.
    """
    stack = [node]
    while stack:
        current = stack.pop()
        if current.child_count == 0:
            yield current
            continue
        stack.extend(reversed(current.children))


# grammar.js:128-138's `extras` array, named entries only — `/\s/` and the
# BOM pattern are anonymous tokens and never appear as sibling nodes at all.
EXTRA_NODE_TYPES = frozenset(
    {
        "comment",
        "multiline_comment",
        "pragma",
        "preproc_region",
        "preproc_endregion",
        "preproc_define",
        "preproc_undef",
    }
)


def previous_meaningful_sibling(node):
    """Nearest previous sibling that is not a grammar extra, or None.

    A raw `node.prev_sibling` lookup is fooled by a comment or line-level
    preprocessor directive sitting between two real tokens — extras can
    appear anywhere, not just between statements (`x./*c*/End()` is legal
    AL). This is the tree-level counterpart of the scanner's own rule that
    every lookahead must step over extras (see .claude/rules/scanner.md).
    """
    current = node.prev_sibling
    while current is not None and current.type in EXTRA_NODE_TYPES:
        current = current.prev_sibling
    return current


def enclosing_named(node, skip_error: bool = False) -> str:
    """Nearest named ancestor's type, self included. Falls back to source_file."""
    current = node
    while current is not None:
        if current.is_named and not (skip_error and current.type == "ERROR"):
            return current.type
        current = current.parent
    return "source_file"


def enclosing_named_covering(node, start: int) -> str:
    """Nearest named ancestor (self included) whose span starts at or before
    `start`. Falls back to source_file.

    For a gap detector, `node` is the leaf immediately AFTER the gap (or the
    root, for a trailing gap) -- it does not itself contain the gap's bytes,
    only touch their far edge. `enclosing_named(node)` returns as soon as
    `node` itself is named, which for e.g. an `integer` literal following a
    dropped `:=` returns "integer": the type of the token next to the gap,
    not the construct the gap sits inside. Every ancestor of `node` ends at
    or after `node` does, so once an ancestor's own start_byte <= start is
    true, that ancestor's span covers [start, node.end_byte) too -- the whole
    gap, not just its trailing edge.
    """
    current = node
    while current is not None:
        if current.is_named and current.start_byte <= start:
            return current.type
        current = current.parent
    return "source_file"


def error_ranges(node) -> list[tuple[int, int]]:
    """Byte ranges of ERROR subtrees. Does not descend into an ERROR.

    Explicit-stack, same hazard as walk()/leaves(): a real full-corpus run
    (detector 1 calls this) hit RecursionError here on a deeply nested file
    even after walk()/leaves() were converted, because this was a separate
    plain-recursive traversal over the same kind of tree.
    """
    found: list[tuple[int, int]] = []
    stack = [node]
    while stack:
        current = stack.pop()
        if current.type == "ERROR" or current.is_error:
            found.append((current.start_byte, current.end_byte))
            continue
        stack.extend(reversed(current.children))
    return found
