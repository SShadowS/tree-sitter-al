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
    """Whitespace per the grammar's extras array: /\\s/ and /\\uFEFF/."""
    return all(ch.isspace() or ch == BOM for ch in text)


def _split_by_errors(start: int, end: int, errors):
    """Subtract every error range from [start, end); return the remainders in order.

    A single gap chunk (the bytes between two adjacent leaves) can straddle an
    error range's edge: when tree-sitter nests one ERROR inside another,
    _tree.leaves() does not yield the outer, non-leaf ERROR at all -- only its
    leaf descendant -- so the chunk from the last clean leaf can run straight
    through a dropped token and into the error's own un-leafed lead-in.
    Blanket overlap suppression would then discard the dropped token along
    with the error text it happens to be glued to. Subtracting each error
    range keeps whatever part of the chunk is genuinely outside error
    recovery, which is where a real dropped-token finding lives.
    """
    segments = [(start, end)]
    for lo, hi in errors:
        next_segments = []
        for seg_start, seg_end in segments:
            if hi <= seg_start or lo >= seg_end:
                next_segments.append((seg_start, seg_end))
                continue
            if seg_start < lo:
                next_segments.append((seg_start, lo))
            if hi < seg_end:
                next_segments.append((hi, seg_end))
        segments = next_segments
    return segments


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
    for seg_start, seg_end in _split_by_errors(start, end, errors):
        _emit_segment(findings, source, path, seg_start, seg_end, node)


def _emit_segment(findings, source, path, start, end, node) -> None:
    raw = source[start:end].decode("utf-8", errors="replace")
    if _is_ignorable(raw):
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
    return source[lo:hi].decode("utf-8", errors="replace").replace("\n", "\\n")
