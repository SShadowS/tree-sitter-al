"""Detector 2: ERROR and MISSING census.

Kept separate from detector 1 so error-recovery artifacts cannot destabilise
the gap clusters.
"""

from __future__ import annotations

from ..model import Finding
from . import _tree

DETECTOR = "errors"


def detect(tree, source: bytes, path: str) -> list[Finding]:
    findings: list[Finding] = []

    for node in _tree.walk(tree.root_node):
        if node.is_missing:
            symbol, category = "MISSING", "missing-node"
        elif node.type == "ERROR" or node.is_error:
            symbol, category = "ERROR", "error-node"
        else:
            continue

        enclosing = _tree.enclosing_named(node.parent, skip_error=True)
        line = source[: node.start_byte].count(b"\n") + 1
        column = node.start_byte - (source.rfind(b"\n", 0, node.start_byte) + 1) + 1

        findings.append(
            Finding(
                detector=DETECTOR,
                category=category,
                fingerprint=(enclosing, symbol),
                path=path,
                byte_offset=node.start_byte,
                line=line,
                column=column,
                enclosing=enclosing,
                snippet=_context(source, line),
                detail={"node_type": node.type},
            )
        )

    return findings


def _context(source: bytes, line: int, radius: int = 1) -> str:
    lines = source.decode("utf-8", errors="replace").splitlines()
    lo = max(0, line - 1 - radius)
    hi = min(len(lines), line + radius)
    return "\n".join(lines[lo:hi])
