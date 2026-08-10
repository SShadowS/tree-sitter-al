"""Findings, clustering, and the JSONL report format."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

HARNESS_VERSION = "1"

_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class Finding:
    detector: str
    category: str
    fingerprint: tuple[str, ...]
    path: str
    byte_offset: int
    line: int
    column: int
    enclosing: str
    snippet: str
    detail: dict[str, Any] = field(default_factory=dict)

    def key(self) -> str:
        return fingerprint_key(self.detector, self.fingerprint)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cluster": self.key(),
            "detector": self.detector,
            "category": self.category,
            "path": self.path,
            "byte_offset": self.byte_offset,
            "line": self.line,
            "column": self.column,
            "enclosing": self.enclosing,
            "snippet": self.snippet,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class Cluster:
    detector: str
    key: str
    count: int
    examples: tuple[Finding, ...]


@dataclass(frozen=True)
class Provenance:
    build_stamp: str
    manifest_hash: str
    tree_sitter_version: str
    # Which file scope produced this report: "manifest" or "full-corpus".
    # Required, not defaulted -- a caller that forgets to pass it should get a
    # TypeError, not a report silently mislabeled as manifest scope. `accept`
    # relies on this to refuse baselining a full-corpus sweep under the
    # manifest's hash (see qc.cmd_accept): the two scopes' finding counts are
    # not comparable, and nothing else in this record distinguishes them.
    scope: str
    harness_version: str = HARNESS_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "record": "provenance",
            "build_stamp": self.build_stamp,
            "manifest_hash": self.manifest_hash,
            "tree_sitter_version": self.tree_sitter_version,
            "scope": self.scope,
            "harness_version": self.harness_version,
        }


def normalize_text(text: str) -> str:
    """Lowercase and collapse whitespace so indentation cannot leak into a key."""
    return _WHITESPACE.sub(" ", text).strip().lower()


def fingerprint_key(detector: str, parts: tuple[str, ...]) -> str:
    return "|".join((detector, *parts))


def cluster(findings: Iterable[Finding], max_examples: int = 3) -> list[Cluster]:
    grouped: dict[str, list[Finding]] = defaultdict(list)
    for finding in findings:
        grouped[finding.key()].append(finding)

    clusters = [
        Cluster(
            detector=items[0].detector,
            key=key,
            count=len(items),
            examples=tuple(_sorted(items)[:max_examples]),
        )
        for key, items in grouped.items()
    ]
    clusters.sort(key=lambda c: (-c.count, c.key))
    return clusters


def _sorted(findings: Iterable[Finding]) -> list[Finding]:
    return sorted(
        findings,
        key=lambda f: (
            f.detector,
            f.path,
            f.byte_offset,
            f.key(),
            f.category,
            f.line,
            f.column,
            f.enclosing,
            f.snippet,
            json.dumps(f.detail, sort_keys=True),
        ),
    )


def write_jsonl(path: Path, provenance: Provenance, findings: list[Finding]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(provenance.to_dict(), sort_keys=True) + "\n")
        for finding in _sorted(findings):
            handle.write(json.dumps(finding.to_dict(), sort_keys=True) + "\n")
