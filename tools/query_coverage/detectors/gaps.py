"""Detector 1: every non-extra source byte must be covered by some leaf node.

A hidden token (an anonymous `kw()` pattern, rendered by tree-sitter as an
invisible aux_sym_* symbol) is lexed and then dropped from the tree. Its bytes
belong to no leaf, so they show up here as a gap. This is the only gate that
sees that class of bug: `tree-sitter parse` output contains named nodes only,
so no tree hash can change when a hidden token disappears.
"""

from __future__ import annotations

from ..model import Finding, normalize_text
from . import _tree

DETECTOR = "gaps"
BOM = "\uFEFF"


def _is_ignorable(text: str) -> bool:
    """Whitespace per the grammar's extras array: /\s/ and /\uFEFF/."""
    return all(ch.isspace() or ch == BOM for ch in text)


def _inside(ranges, start: int, end: int) -> bool:
    """True if [start, end) overlaps any error range at all.

    Full containment is not enough: a gap chunk can straddle an error range's
    boundary (real whitespace immediately followed by error-recovery bytes,
    merged into one uncovered span by leaf traversal). Any overlap means the
    chunk is entangled with error recovery and belongs to detector 2, not here.
    """
    return any(lo < end and start < hi for lo, hi in ranges)


def detect(tree, source: bytes, path: str) -> list[Finding]:
    errors = _tree.error_ranges(tree.root_node)

    findings: list[Finding] = []
    cursor = 0
    root = tree.root_node

    for leaf in _tree.leaves(root):
        if leaf.start_byte > cursor:
            _emit(findings, source, path, cursor, leaf.start_byte, leaf, errors)
        cursor = max(cursor, leaf.end_byte)

    if cursor < len(source):
        _emit(findings, source, path, cursor, len(source), root, errors)

    return findings


def _emit(findings, source, path, start, end, node, errors) -> None:
    raw = source[start:end].decode("utf-8", errors="replace")
    if _is_ignorable(raw):
        return
    if _inside(errors, start, end):
        return

    stripped = raw.strip()
    offset = start + raw.index(stripped[0]) if stripped else start
    line = source[:offset].count(b"\n") + 1
    column = offset - (source.rfind(b"\n", 0, offset) + 1) + 1
    enclosing = _tree.enclosing_named(node)

    findings.append(
        Finding(
            detector=DETECTOR,
            category="byte-gap",
            fingerprint=(normalize_text(stripped), enclosing),
            path=path,
            byte_offset=offset,
            line=line,
            column=column,
            enclosing=enclosing,
            snippet=_snippet(source, offset),
            detail={"gap_text": stripped},
        )
    )


def _snippet(source: bytes, offset: int, radius: int = 60) -> str:
    lo = max(0, offset - radius)
    hi = min(len(source), offset + radius)
    return source[lo:hi].decode("utf-8", errors="replace").replace("\n", "\n")
