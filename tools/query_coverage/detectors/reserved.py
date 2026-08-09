"""Detector 4: a hard-reserved word appearing as a plain identifier.

This is the signature of a silent misparse — the PREPROC_SPLIT_END bug
reparsed `end;` as a call_statement, which leaves every byte covered and
produces no ERROR. Detectors 1, 2 and 5 are all blind to it.

TUNING: validate HARD_RESERVED with `al compile` probes before trusting it,
`exit` and `var` especially. AL is lenient about contextual keywords and the
compiler is the only ground truth (see CLAUDE.md). False positives land in the
baseline, so this is tuning rather than a blocker.
"""

from __future__ import annotations

from ..model import Finding
from . import _tree

DETECTOR = "reserved"

HARD_RESERVED = frozenset(
    {
        "begin",
        "end",
        "then",
        "else",
        "until",
        "repeat",
        "case",
        "exit",
        "var",
        "procedure",
        "trigger",
    }
)

# grammar.js:4148-4159 — deliberately usable as identifiers.
CONTEXTUAL_WHITELIST = frozenset(
    {
        "field",
        "key",
        "value",
        "separator",
        "dataset",
        "type",
        "version",
        "action",
        "table",
        "assembly",
    }
)


def _is_member_access(node) -> bool:
    """x.End — the member name is not a free identifier."""
    parent = node.parent
    if parent is None or parent.type != "member_expression":
        return False
    previous = node.prev_sibling
    return previous is not None and previous.type == "."


def detect(tree, source: bytes, path: str) -> list[Finding]:
    findings: list[Finding] = []

    for node in _tree.walk(tree.root_node):
        if node.type != "identifier":
            continue

        word = node.text.decode("utf-8", errors="replace").lower()
        if word not in HARD_RESERVED or word in CONTEXTUAL_WHITELIST:
            continue
        if _is_member_access(node):
            continue

        enclosing = node.parent.type if node.parent is not None else "source_file"
        line = source[: node.start_byte].count(b"\n") + 1

        findings.append(
            Finding(
                detector=DETECTOR,
                category="reserved-as-identifier",
                fingerprint=(word, enclosing),
                path=path,
                byte_offset=node.start_byte,
                line=line,
                column=node.start_point[1] + 1,
                enclosing=enclosing,
                snippet=_line_text(source, line),
                detail={"keyword": word},
            )
        )

    return findings


def _line_text(source: bytes, line: int) -> str:
    lines = source.decode("utf-8", errors="replace").splitlines()
    return lines[line - 1] if 0 < line <= len(lines) else ""
