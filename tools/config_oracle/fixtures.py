"""test/corpus cases as oracle INPUT (their expected trees play no part in the verdict).

A line-based reader, deliberately not count_corpus_cases' regex: two readers
of the corpus format must agree (spec section 4), which is only a check if
they are different implementations.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_EQ = re.compile(rb"^={3,}[ \t]*\r?$")
_DASH = re.compile(rb"^-{3,}[ \t]*\r?$")
_ATTR = re.compile(rb"^:")


@dataclass(frozen=True)
class Case:
    file: str
    name: str
    index: int
    source: bytes

    @property
    def id(self):
        return f"{self.file}#{self.index}"


def extract(root: Path) -> list:
    out = []
    for path in sorted(root.rglob("*.txt")):
        rel = str(path.relative_to(root)).replace("\\", "/")
        lines = path.read_bytes().split(b"\n")
        i, index = 0, 0
        while i < len(lines):
            if _EQ.match(lines[i]) and i + 1 < len(lines) and lines[i + 1].strip() and not _EQ.match(lines[i + 1]):
                j = i + 1
                name_lines = []
                while j < len(lines) and not _EQ.match(lines[j]):
                    if not lines[j].strip():
                        name_lines = None     # blank line inside a header: tree-sitter drops the case
                        break
                    name_lines.append(lines[j])
                    j += 1
                if name_lines is None or j >= len(lines):
                    i += 1
                    continue
                k = j + 1
                while k < len(lines) and not _DASH.match(lines[k]) and not _EQ.match(lines[k]):
                    k += 1
                skip = any(_ATTR.match(l) and l.strip().startswith(b":skip") for l in name_lines)
                if k < len(lines) and _DASH.match(lines[k]) and not skip:
                    body = b"\n".join(lines[j + 1:k]).rstrip(b"\r\n") + b"\n"
                    out.append(Case(rel, name_lines[0].strip().decode("utf8", "replace"), index, body))
                    index += 1
                i = k
            else:
                i += 1
    return out


def load_classes(path: Path) -> dict:
    classes = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        case_id, config, expected, reason = line.split("\t")
        if (case_id, config) in classes:
            raise ValueError(f"duplicate classification: {case_id} {config}")
        classes[(case_id, config)] = (expected, reason)
    return classes
