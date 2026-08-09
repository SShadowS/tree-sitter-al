"""Detector 6: audit of the queries this project ships. Informational only.

Two invariants, replacing the noisy "node types no query captures" list:
  * every *_keyword node and visible operator token gets a highlights capture
  * any pattern matching zero times is reported

Scope note: run dead-pattern tallies over the FULL corpus, not the manifest
subset. A manifest-only run false-flags patterns for rare constructs that
set-cover happened to satisfy from a single file.

This detector finds only FULLY dead patterns. queries/highlights.scm:155
(':=' @operator) is not one of them — it still matches the visible ':=' inside
for_statement, so it is mostly dead rather than dead. Detectors 1 and 3 catch
that case.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from ..model import Finding, normalize_text
from . import _tree

DETECTOR = "shipped_queries"

# Structural delimiters are not operators.
OPERATOR_EXCLUSIONS = frozenset({";", ",", "(", ")", "{", "}", "[", "]", ".", ":"})

_COMMENT_LINE = re.compile(r"^\s*;.*$", re.MULTILINE)


@dataclass(frozen=True)
class PatternUsage:
    query_file: str
    index: int
    text: str
    matches: int


def operator_tokens(node_types: list[dict]) -> list[str]:
    """Anonymous entries whose text is entirely punctuation, minus delimiters."""
    tokens = []
    for entry in node_types:
        if entry.get("named"):
            continue
        text = entry["type"]
        if not text or text in OPERATOR_EXCLUSIONS:
            continue
        if all(not ch.isalnum() and not ch.isspace() and ch != "_" for ch in text):
            tokens.append(text)
    return sorted(tokens)


def pattern_texts(query, source: str) -> list[str]:
    """Per-pattern source text, comments and blank lines stripped.

    end_byte_for_pattern runs to the start of the next pattern, so the raw slice
    carries trailing comments. Strip them or the fingerprint churns whenever a
    comment nearby is edited.
    """
    texts = []
    for index in range(query.pattern_count):
        raw = source[query.start_byte_for_pattern(index) : query.end_byte_for_pattern(index)]
        texts.append(normalize_text(_COMMENT_LINE.sub("", raw)))
    return texts


def tally(language, query_path: Path, trees_and_sources) -> list[PatternUsage]:
    import tree_sitter

    source = query_path.read_text(encoding="utf-8")
    query = tree_sitter.Query(language, source)
    texts = pattern_texts(query, source)
    counts = [0] * query.pattern_count

    for tree, _src in trees_and_sources:
        cursor = tree_sitter.QueryCursor(query)
        for index, _captures in cursor.matches(tree.root_node):
            counts[index] += 1

    return [
        PatternUsage(query_file=query_path.name, index=i, text=texts[i], matches=counts[i])
        for i in range(query.pattern_count)
    ]


def detect_dead(usages: list[PatternUsage]) -> list[Finding]:
    findings: list[Finding] = []
    for usage in usages:
        if usage.matches > 0 or not usage.text:
            continue
        digest = hashlib.sha256(usage.text.encode("utf-8")).hexdigest()
        findings.append(
            Finding(
                detector=DETECTOR,
                category="dead-query-pattern",
                fingerprint=(usage.query_file, digest),
                path=f"queries/{usage.query_file}",
                byte_offset=0,
                line=0,
                column=0,
                enclosing="query",
                snippet=usage.text[:160],
                detail={"pattern_text": usage.text, "query_file": usage.query_file},
            )
        )
    return findings


def detect_keyword_coverage(
    language, highlights_path: Path, node_types: list[dict], tree, source: bytes, path: str
) -> list[Finding]:
    import tree_sitter

    query = tree_sitter.Query(language, highlights_path.read_text(encoding="utf-8"))
    cursor = tree_sitter.QueryCursor(query)

    captured: set[int] = set()
    for _index, captures in cursor.matches(tree.root_node):
        for nodes in captures.values():
            for node in nodes:
                captured.add(node.id)

    findings: list[Finding] = []
    seen: set[str] = set()

    for node in _tree.walk(tree.root_node):
        is_keyword = node.is_named and node.type.endswith("_keyword")
        is_operator = not node.is_named and node.type in set(operator_tokens(node_types))
        if not (is_keyword or is_operator):
            continue
        if node.id in captured or node.type in seen:
            continue

        seen.add(node.type)
        findings.append(
            Finding(
                detector=DETECTOR,
                category="uncaptured-keyword",
                fingerprint=("uncaptured", node.type),
                path=path,
                byte_offset=node.start_byte,
                line=source[: node.start_byte].count(b"\n") + 1,
                column=node.start_point[1] + 1,
                enclosing=node.parent.type if node.parent else "source_file",
                snippet=node.text.decode("utf-8", errors="replace"),
                detail={"node_type": node.type},
            )
        )

    return findings
