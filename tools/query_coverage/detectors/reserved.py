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


def reportable() -> frozenset[str]:
    """The words detect() will actually flag.

    KEPT, not deleted: the whitelist guards a future edit to HARD_RESERVED.
    Adding a contextual keyword there — `field`, say — would otherwise flag
    every `field(` in the corpus, and the whole point of CONTEXTUAL_WHITELIST
    is that those words are legitimately identifiers.

    Expressed as set subtraction rather than as a second membership test
    inside detect()'s loop, which is where it used to live: written that way
    the test could never be true, because the two sets are disjoint today, so
    a reader could not tell a live guard from dead code. Subtraction says
    "these words are excluded by construction" instead of "this branch is
    never taken". Read from the module attributes on every call so a test can
    monkeypatch either set — test_whitelist_suppresses_a_word_even_when_hard_
    reserved does exactly that, and is what keeps this non-vacuous.
    """
    return frozenset(HARD_RESERVED) - frozenset(CONTEXTUAL_WHITELIST)


def _is_member_access(node) -> bool:
    """x.End — the member name is not a free identifier.

    Skips extras (comments, line-level preprocessor directives) between the
    '.' and the member name via _tree.previous_meaningful_sibling — a raw
    prev_sibling lookup is fooled by `x./*c*/End()`, the same class of bug
    this whole detector exists to catch (see .claude/rules/scanner.md).
    """
    parent = node.parent
    if parent is None or parent.type != "member_expression":
        return False
    previous = _tree.previous_meaningful_sibling(node)
    return previous is not None and previous.type == "."


def detect(tree, source: bytes, path: str) -> list[Finding]:
    findings: list[Finding] = []
    words = reportable()

    for node in _tree.walk(tree.root_node):
        if node.type != "identifier":
            continue

        word = node.text.decode("utf-8", errors="replace").lower()
        if word not in words:
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
