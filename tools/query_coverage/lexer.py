"""An independent lexer for AL strings, comments, and directives.

Deliberately written from the AL language rules rather than transliterated
from grammar.js. Sharing an implementation with the parser would mean sharing
its bugs, and this is the only component in the harness that can catch a
parser tokenisation error.

Scope is strings, comments, and directive lines. It does not track braces,
begin/end, or any nesting: a nesting tracker desynchronises on preproc_split_*
files, where begin, end and the terminating semicolon are split across #if
branches — exactly where this project's bugs live.
"""

from __future__ import annotations

from dataclasses import dataclass

STRING = "string"
COMMENT = "comment"
DIRECTIVE = "directive"


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    kind: str


def scan(source: str) -> list[Span]:
    spans: list[Span] = []
    i = 0
    length = len(source)
    at_line_start = True

    while i < length:
        ch = source[i]

        if ch in ("'", '"'):
            spans.append(_read_quoted(source, i, ch))
            i = spans[-1].end
            at_line_start = False
            continue

        if ch == "/" and i + 1 < length:
            nxt = source[i + 1]
            if nxt == "/":
                end = source.find("\n", i)
                end = length if end == -1 else end
                spans.append(Span(i, end, COMMENT))
                i = end
                continue
            if nxt == "*":
                end = source.find("*/", i + 2)
                end = length if end == -1 else end + 2
                spans.append(Span(i, end, COMMENT))
                i = end
                at_line_start = False
                continue

        if ch == "#" and at_line_start:
            end = source.find("\n", i)
            end = length if end == -1 else end
            spans.append(Span(i, end, DIRECTIVE))
            i = end
            continue

        if ch == "\n":
            at_line_start = True
        elif not ch.isspace():
            at_line_start = False

        i += 1

    return spans


def _read_quoted(source: str, start: int, quote: str) -> Span:
    """A doubled quote is an escape, not a terminator."""
    i = start + 1
    length = len(source)
    while i < length:
        if source[i] == quote:
            if i + 1 < length and source[i + 1] == quote:
                i += 2
                continue
            return Span(start, i + 1, STRING)
        i += 1
    return Span(start, length, STRING)


def is_code(spans: list[Span], offset: int) -> bool:
    return not any(span.start <= offset < span.end for span in spans)
