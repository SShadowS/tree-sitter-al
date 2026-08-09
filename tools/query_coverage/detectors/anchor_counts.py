"""Detector 5: lexical anchor counts versus node counts.

Counting carries no nesting state, so unlike a construct extractor it cannot
desynchronise on preproc_split_* files.
"""

from __future__ import annotations

import re

from .. import anchors as anchor_table
from .. import lexer
from ..model import Finding
from . import _tree

DETECTOR = "anchors"


def count_lexical(source: str, anchor: anchor_table.Anchor) -> int:
    spans = lexer.scan(source)
    pattern = re.compile(anchor.pattern, re.IGNORECASE)
    return sum(1 for m in pattern.finditer(source) if lexer.is_code(spans, m.start()))


def count_nodes(tree, anchor: anchor_table.Anchor) -> int:
    wanted = set(anchor.node_types)
    return sum(1 for node in _tree.walk(tree.root_node) if node.type in wanted)


def detect(tree, source: bytes, path: str) -> list[Finding]:
    text = source.decode("utf-8", errors="replace")
    findings: list[Finding] = []

    for anchor in anchor_table.ANCHORS:
        lexical = count_lexical(text, anchor)
        nodes = count_nodes(tree, anchor)
        if lexical == nodes:
            continue

        findings.append(
            Finding(
                detector=DETECTOR,
                category="anchor-count-mismatch",
                fingerprint=(anchor.name, path),
                path=path,
                byte_offset=0,
                line=0,
                column=0,
                enclosing="source_file",
                snippet=f"{anchor.name}: {lexical} lexical vs {nodes} nodes",
                detail={
                    "anchor": anchor.name,
                    "lexical": lexical,
                    "nodes": nodes,
                    "node_types": list(anchor.node_types),
                },
            )
        )

    return findings
