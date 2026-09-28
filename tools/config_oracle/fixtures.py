"""test/corpus cases as oracle INPUT (their expected trees play no part in the verdict).

A line-based reader, deliberately not count_corpus_cases' regex: two readers
of the corpus format must agree (spec section 4), which is only a check if
they are different implementations.

Source-byte extraction mirrors tree-sitter's own corpus reader (vendored at
`.cache/tree-sitter-0.25.10/cli/src/test.rs`; header/divider regexes around
line 28-48, the slicing logic around line 883-911):

  * The divider for a case is the LONGEST `-{3,}` line between the end of its
    header and the start of the next header (or EOF), ties won by the LAST
    one -- not the first `-{3,}` line encountered. A short `----` inside a
    block comment must not pre-empt the real divider below it.
  * `source` is the RAW byte slice from the end of the header's closing `===`
    line to the start of that divider line, then exactly one trailing byte is
    popped unconditionally (mirrors Rust's `Vec::pop`, which does not check
    it is actually `\n`), and one more trailing `\r` is popped if present
    (`#[cfg(target_os = "windows")]` in test.rs; this project's platform).
    No blank-line assumption, no re-appended `\n` -- a case with no blank
    line before its divider has NO trailing newline in `source`.
  * A `===`/`---` marker line tolerates no trailing content at all, not even
    trailing whitespace. Real tree-sitter ties this to a file-wide "first
    suffix" convention (test.rs's `first_suffix`); every header/divider line
    in this corpus uses none (verified: zero lines here carry anything after
    the marker run), so requiring a bare marker line reproduces the real
    behaviour without modelling that convention. Verified against the
    installed tree-sitter 0.27.0 CLI: a `---` line with trailing spaces is
    REJECTED (its case silently dropped), the same as a missing divider.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_EQ = re.compile(rb"^={3,}\r?$")
_DASH = re.compile(rb"^-{3,}\r?$")


@dataclass(frozen=True)
class Case:
    file: str
    name: str
    index: int
    source: bytes
    offset: int  # byte offset in the file where `source` (pre-strip) begins

    @property
    def id(self):
        return f"{self.file}#{self.index}"


def _is_skip_line(line: bytes) -> bool:
    """Mirrors test.rs: trim the line, split on the first '(', exact-match ':skip'."""
    return line.strip().split(b"(", 1)[0] == b":skip"


def _line_offsets(data: bytes):
    lines = data.split(b"\n")
    offsets = []
    pos = 0
    for line in lines:
        offsets.append(pos)
        pos += len(line) + 1
    return lines, offsets


def _headers(lines):
    """[(name, skip, open_idx, close_idx), ...] in file order.

    open_idx/close_idx are line indices of the opening and closing '=' lines.
    A blank line inside the name block aborts that header attempt entirely
    (mechanism 1); scanning resumes one line past the failed opener, exactly
    like a regex engine retrying at the next position.
    """
    out = []
    i, n = 0, len(lines)
    while i < n:
        if _EQ.match(lines[i]) and i + 1 < n and lines[i + 1].strip() and not _EQ.match(lines[i + 1]):
            open_idx = i
            j = i + 1
            name_lines = []
            broken = False
            while j < n and not _EQ.match(lines[j]):
                if not lines[j].strip():
                    broken = True
                    break
                name_lines.append(lines[j])
                j += 1
            if broken or j >= n:
                i += 1
                continue
            skip = any(_is_skip_line(l) for l in name_lines)
            name = name_lines[0].strip().decode("utf8", "replace")
            out.append((name, skip, open_idx, j))
            i = j + 1
        else:
            i += 1
    return out


def _best_divider(lines, lo, hi):
    """Index of the longest '-{3,}' line in lines[lo:hi]; ties keep the LAST
    one (mirrors Rust's Iterator::max_by_key). None if no candidate."""
    best = None
    for idx in range(lo, hi):
        if _DASH.match(lines[idx]):
            length = len(lines[idx].rstrip(b"\r"))
            if best is None or length >= best[0]:
                best = (length, idx)
    return best[1] if best else None


def _strip_trailing_newline(raw: bytes) -> bytes:
    if raw:
        raw = raw[:-1]          # unconditional pop, mirrors Rust's Vec::pop()
    if raw[-1:] == b"\r":
        raw = raw[:-1]          # Windows-only in tree-sitter; this project's platform
    return raw


def extract(root: Path) -> list:
    out = []
    for path in sorted(root.rglob("*.txt")):
        rel = str(path.relative_to(root)).replace("\\", "/")
        data = path.read_bytes()
        lines, offsets = _line_offsets(data)
        headers = _headers(lines)
        index = 0
        for k, (name, skip, open_idx, close_idx) in enumerate(headers):
            body_lo = close_idx + 1
            body_hi = headers[k + 1][2] if k + 1 < len(headers) else len(lines)
            div_idx = _best_divider(lines, body_lo, body_hi)
            if div_idx is None or skip:
                continue
            start_off = offsets[body_lo] if body_lo < len(offsets) else len(data)
            end_off = offsets[div_idx]
            source = _strip_trailing_newline(data[start_off:end_off])
            out.append(Case(rel, name, index, source, start_off))
            index += 1
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
