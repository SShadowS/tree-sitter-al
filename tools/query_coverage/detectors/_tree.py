"""Tree traversal shared by every detector.

One implementation, because two hand-copied versions of enclosing_named with
different skip rules drift apart silently — the exact class of quiet wrongness
this harness exists to catch.
"""

from __future__ import annotations

from typing import Iterator


def walk(node) -> Iterator:
    """Every node in the subtree, self first."""
    yield node
    for child in node.children:
        yield from walk(child)


def leaves(node) -> Iterator:
    """Childless nodes in byte order.

    Walks ALL children, not named_children: anonymous string tokens such as
    ';' are visible leaves and legitimately provide byte coverage.
    """
    if node.child_count == 0:
        yield node
        return
    for child in node.children:
        yield from leaves(child)


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


def error_ranges(node) -> list[tuple[int, int]]:
    """Byte ranges of ERROR subtrees. Does not descend into an ERROR."""
    found: list[tuple[int, int]] = []
    _collect_errors(node, found)
    return found


def _collect_errors(node, out: list[tuple[int, int]]) -> None:
    if node.type == "ERROR" or node.is_error:
        out.append((node.start_byte, node.end_byte))
        return
    for child in node.children:
        _collect_errors(child, out)
