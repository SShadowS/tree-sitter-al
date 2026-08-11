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
from dataclasses import dataclass, field
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


def pattern_texts(query, source: bytes) -> list[str]:
    """Per-pattern source text, comments and blank lines stripped.

    end_byte_for_pattern runs to the start of the next pattern, so the raw slice
    carries trailing comments. Strip them or the fingerprint churns whenever a
    comment nearby is edited.

    start_byte_for_pattern/end_byte_for_pattern return BYTE offsets, not
    character offsets. `source` must be bytes and stay bytes through the
    slice — slicing a decoded str with a byte offset desyncs after the first
    multi-byte UTF-8 character anywhere earlier in the file (a non-ASCII
    comment, an arrow, a curly quote), corrupting every pattern that follows
    it. Decode only the per-pattern slice, after slicing.
    """
    texts = []
    for index in range(query.pattern_count):
        raw = source[query.start_byte_for_pattern(index) : query.end_byte_for_pattern(index)]
        text = raw.decode("utf-8")
        texts.append(normalize_text(_COMMENT_LINE.sub("", text)))
    return texts


class QueryTally:
    """One shipped query file: compiled once, fed trees one at a time.

    The batch shape ("hand tally() every tree at the end of the run") was what
    forced qc.cmd_run to keep all 15,358 parsed trees alive simultaneously
    (~2.8 GB RSS, measured). Streaming inverts that: cmd_run constructs one
    QueryTally per .scm up front, calls add() inside its per-file loop, and
    reads usages() after — no tree outlives its own loop iteration. The
    per-pattern counts are plain sums, so feeding trees one at a time is
    arithmetically identical to the old single pass over an accumulated list.
    """

    def __init__(self, language, query_path: Path):
        import tree_sitter

        source = query_path.read_bytes()
        self.query = tree_sitter.Query(language, source.decode("utf-8"))
        self._file_name = query_path.name
        self._texts = pattern_texts(self.query, source)
        self._counts = [0] * self.query.pattern_count

    def add(self, tree) -> None:
        import tree_sitter

        cursor = tree_sitter.QueryCursor(self.query)
        for index, _captures in cursor.matches(tree.root_node):
            self._counts[index] += 1

    def usages(self) -> list[PatternUsage]:
        return [
            PatternUsage(
                query_file=self._file_name,
                index=i,
                text=self._texts[i],
                matches=self._counts[i],
            )
            for i in range(self.query.pattern_count)
        ]


def tally(language, query_path: Path, trees_and_sources) -> list[PatternUsage]:
    """Batch wrapper over QueryTally for callers that already hold every tree."""
    accumulator = QueryTally(language, query_path)
    for tree, _src in trees_and_sources:
        accumulator.add(tree)
    return accumulator.usages()


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


@dataclass(frozen=True)
class KeywordCoverageContext:
    """Run-level state for detect_keyword_coverage.

    Both members are pure functions of run-level inputs, so recomputing them
    per file was pure waste — and measured waste, not estimated: compiling
    highlights.scm costs 32.9 ms, which times 15,358 files was ~8.4 minutes
    of a ~31-minute full-corpus run, and `set(operator_tokens(node_types))`
    was rebuilt not merely per file but per anonymous NODE inside the walk
    (~6 more minutes corpus-wide). One context per run replaces both.

    `query` is a tree_sitter.Query; typed loosely because this module imports
    tree_sitter lazily inside functions, never at module level.

    `reported` is deliberately mutable state living on a frozen dataclass:
    frozen forbids rebinding the attribute, not mutating the set it names, and
    the set is what has to be shared. See its own note below.
    """

    query: object
    operators: frozenset
    # Node types already reported, for the WHOLE run. The invariant this
    # detector enforces is "no *_keyword node type anywhere in the corpus goes
    # uncaptured", which is a property of the run, not of a file -- so one
    # uncaptured type is one finding, not one per file that contains it.
    # Deduping per call instead put up to 15,358 identical findings (one per
    # corpus file) into findings.jsonl for a single uncaptured type: same
    # cluster, same fingerprint, ~260x the rows.
    reported: set = field(default_factory=set)


def keyword_coverage_context(
    language, highlights_path: Path, node_types: list[dict]
) -> KeywordCoverageContext:
    import tree_sitter

    return KeywordCoverageContext(
        query=tree_sitter.Query(language, highlights_path.read_text(encoding="utf-8")),
        operators=frozenset(operator_tokens(node_types)),
    )


def detect_keyword_coverage(
    context: KeywordCoverageContext, tree, source: bytes, path: str
) -> list[Finding]:
    import tree_sitter

    cursor = tree_sitter.QueryCursor(context.query)

    captured: set[int] = set()
    for _index, captures in cursor.matches(tree.root_node):
        for nodes in captures.values():
            for node in nodes:
                captured.add(node.id)

    findings: list[Finding] = []

    for node in _tree.walk(tree.root_node):
        is_keyword = node.is_named and node.type.endswith("_keyword")
        is_operator = not node.is_named and node.type in context.operators
        if not (is_keyword or is_operator):
            continue
        if node.id in captured or node.type in context.reported:
            continue

        context.reported.add(node.type)
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
