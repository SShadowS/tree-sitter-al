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


def _is_ignorable_char(ch: str) -> bool:
    """Whitespace per the grammar's extras array: /\\s/ and /\\uFEFF/."""
    return ch.isspace() or ch == BOM


def _lead_length(text: str) -> int:
    """Characters of leading ignorable text.

    Deliberately not `len(text) - len(text.lstrip())`: str.strip() does not
    strip U+FEFF, so the two disagree exactly where _is_ignorable_char says the
    character carries no meaning. That disagreement would put a BOM into the
    reported gap text and into the cluster fingerprint.

    A whole segment that is ignorable makes this return len(text), which is how
    _emit_segment drops it — no separate all-ignorable predicate, which would
    be a second scan with a second chance to disagree with this one.
    """
    index = 0
    while index < len(text) and _is_ignorable_char(text[index]):
        index += 1
    return index


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

    lead = _lead_length(raw)
    tail = len(raw)
    while tail > lead and _is_ignorable_char(raw[tail - 1]):
        tail -= 1
    stripped = raw[lead:tail]
    if not stripped:
        return

    # `start` is a BYTE offset, so the ignorable prefix must be measured in
    # BYTES too. The previous form added `raw.index(stripped[0])` -- a
    # CHARACTER index -- which is short by one byte per multi-byte character
    # in that prefix, and then reports a line/column that points into the
    # middle of a character. Same class as the bug 376b8f0 fixed in
    # pattern_texts(); there the offsets came from tree-sitter, here from a
    # str method, and both desync against a byte offset the same way.
    #
    # Re-encoding is exact: every character in the prefix is whitespace or a
    # BOM, and decode(errors="replace") can only have produced U+FFFD, which
    # is neither -- so no replacement character is ever inside the slice.
    offset = start + len(raw[:lead].encode("utf-8"))
    line = source[:offset].count(b"\n") + 1
    column = offset - (source.rfind(b"\n", 0, offset) + 1) + 1
    enclosing = _tree.enclosing_named_covering(node, start)

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
