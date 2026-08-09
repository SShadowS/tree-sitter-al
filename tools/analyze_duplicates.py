#!/usr/bin/env python3
"""
analyze_duplicates.py - Detect duplicate top-level rule keys in grammar.js.

grammar.js's `rules: { ... }` is one big JavaScript object literal. If the
same key is written twice, JavaScript silently keeps the LAST value and
discards the first -- a repeated key in an object literal is valid syntax,
so nothing about `tree-sitter generate`, ESLint, or a normal diff review
flags it. Task 10 (see CHANGELOG.md, "Removed") found exactly this:
`empty_statement` was defined twice, identically, in two different places in
the file, and no tool caught it -- a human reading the file did.

This script parses `rules: { ... }` well enough to recover every top-level
`key: value` entry (a small hand-rolled scanner, not a full JS parser -- see
`_skip_noncode` for what it does and does not handle) and reports any key
that appears more than once. Two different entries can matter in very
different ways:

  * IDENTICAL duplicate -- both definitions are byte-for-byte the same after
    trimming surrounding whitespace. Harmless in the sense that the grammar
    behaves as written (there is only one distinct definition to discard),
    but it is dead weight: a copy-paste leftover, and a trap for the next
    person who edits only one of the two copies.
  * DIFFERING duplicate -- the definitions disagree. This is a live bug: the
    earlier definition is silently discarded by JavaScript's last-write-wins
    object literal semantics, so the grammar does not do what the *first*
    definition says, and nothing before this script said so.

Both kinds fail this check -- see validate-grammar.sh's Step 5 for why an
"identical, so it's harmless" duplicate still fails the build: it is exactly
the kind of thing that goes unnoticed and then bit-rots into a differing one
the next time someone edits only one of the copies.

Run from the repository root -- grammar.js is read relative to the working
directory.

Usage:
    python tools/analyze_duplicates.py           # Human-readable report
    python tools/analyze_duplicates.py --json     # Machine-readable report

--strict is still accepted (a no-op) for compatibility with existing
`.claude/commands/*.md` references -- there is no "loose" mode left to
distinguish it from: this script only ever reports actual duplicate keys,
never speculative consolidation candidates.
"""

import argparse
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

# Characters after which a '/' starts a regex literal rather than division.
# grammar.js contains exactly two raw regex literals in the rules object
# (`token(/\d+/)`, `token(/[\p{L}_][\p{L}\p{N}_]*/u)`); both are immediately
# preceded by one of these. The set errs toward "regex is legal here" for any
# JS operator/punctuator token, which is the standard lexer heuristic and safe
# for a DSL file that contains no division.
_REGEX_ALLOWED_AFTER = set('([{,:;=!&|?~^%<>+-*') | {None}

_IDENT_RE = re.compile(r'[A-Za-z_$][A-Za-z0-9_$]*')


def _skip_noncode(text, i, n, prev):
    """If `text[i]` starts a `//` or `/* */` comment, a `'`/`"`/`` ` `` string,
    or (when `prev` says a value is expected, not a division operator) a `/
    .../` regex literal, return the index just past it and the new `prev`
    token to report to the caller. Otherwise return None -- the caller should
    treat `text[i]` as ordinary, structurally significant source.

    This is deliberately not a full JS lexer: it exists only to keep brace/
    paren/bracket depth-counting from being confused by a `{`, `(`, `[`, `:`,
    or `,` that merely *appears* inside a comment, string, or regex literal
    (e.g. the `[...]` character class in `/[\\p{L}_].../u`). Nothing here
    needs to know what the skipped text *means* -- only where it ends.
    """
    c = text[i]

    if c == '/' and i + 1 < n and text[i + 1] == '/':
        j = text.find('\n', i)
        return (n if j == -1 else j), prev

    if c == '/' and i + 1 < n and text[i + 1] == '*':
        j = text.find('*/', i + 2)
        return (n if j == -1 else j + 2), prev

    if c in ("'", '"', '`'):
        quote = c
        j = i + 1
        while j < n:
            if text[j] == '\\':
                j += 2
                continue
            if text[j] == quote:
                j += 1
                break
            j += 1
        return j, quote

    if c == '/' and prev in _REGEX_ALLOWED_AFTER:
        j = i + 1
        in_class = False
        while j < n:
            ch = text[j]
            if ch == '\\':
                j += 2
                continue
            if ch == '\n':
                break  # malformed/unterminated -- bail, treat '/' as itself
            if ch == '[':
                in_class = True
            elif ch == ']':
                in_class = False
            elif ch == '/' and not in_class:
                j += 1
                break
            j += 1
        while j < n and text[j].isalpha():
            j += 1
        return j, '/'

    return None


def _find_rules_object(text):
    """Return (body_start, body_end) spanning the inside of `rules: { ... }`
    (exclusive of the braces)."""
    m = re.search(r'\brules\s*:\s*\{', text)
    if not m:
        raise ValueError("no 'rules: {' object found in grammar.js")

    i = m.end()  # just past the opening '{'
    depth = 1
    n = len(text)
    prev = '{'

    while i < n and depth > 0:
        skip = _skip_noncode(text, i, n, prev)
        if skip is not None:
            i, prev = skip
            continue

        c = text[i]
        if c in '([{':
            depth += 1
        elif c in ')]}':
            depth -= 1
            if depth == 0:
                return m.end(), i

        if not c.isspace():
            prev = c
        i += 1

    raise ValueError("unbalanced braces while scanning 'rules: { ... }'")


def extract_rule_entries(text):
    """Return an ordered list of (key, value_text, line_number) for every
    top-level `key: value,` entry directly inside grammar.js's `rules: {}`.

    A "top-level" entry is one whose `key:` appears at bracket depth 0
    relative to the rules object body -- i.e. not nested inside another
    rule's `seq(...)`/`choice(...)`/object argument. `value_text` is the
    exact source between the colon and the entry's trailing top-level comma
    (or the closing brace for the last entry), stripped of surrounding
    whitespace; it is NOT semantically normalized, so this compares what the
    file actually says, byte for byte.
    """
    body_start, body_end = _find_rules_object(text)
    body = text[body_start:body_end]
    line = text.count('\n', 0, body_start) + 1

    entries = []
    i = 0
    n = len(body)
    depth = 0
    prev = None

    current_key = None
    current_line = None
    value_start = None

    def flush(end):
        nonlocal current_key, current_line, value_start
        if current_key is not None:
            raw = body[value_start:end].rstrip()
            if raw.endswith(','):
                raw = raw[:-1]
            entries.append((current_key, raw.strip(), current_line))
        current_key = None
        current_line = None
        value_start = None

    while i < n:
        if body[i] == '\n':
            line += 1
            i += 1
            continue

        prev_i = i
        skip = _skip_noncode(body, i, n, prev)
        if skip is not None:
            i, prev = skip
            line += body.count('\n', prev_i, i)
            continue

        c = body[i]

        if c in '([{':
            depth += 1
            prev = c
            i += 1
            continue
        if c in ')]}':
            depth -= 1
            prev = c
            i += 1
            continue

        if depth == 0 and (c.isalpha() or c in '_$'):
            m = _IDENT_RE.match(body, i)
            after = m.end()
            k = after
            while k < n and body[k] in ' \t':
                k += 1
            if k < n and body[k] == ':' and (k + 1 >= n or body[k + 1] != ':'):
                flush(i)
                current_key = m.group(0)
                current_line = line
                value_start = k + 1
                i = k + 1
                prev = ':'
                continue
            prev = body[after - 1]
            i = after
            continue

        if not c.isspace():
            prev = c
        i += 1

    flush(n)
    return entries


def find_duplicates(entries):
    """Group entries by key; return an OrderedDict of key -> list of
    (value_text, line) for every key that appears more than once, in file
    order of first appearance."""
    by_key = OrderedDict()
    for key, value, line in entries:
        by_key.setdefault(key, []).append((value, line))
    return OrderedDict((k, v) for k, v in by_key.items() if len(v) > 1)


def classify(occurrences):
    """'identical' if every occurrence's value text matches byte for byte,
    else 'differing'."""
    values = {v for v, _ in occurrences}
    return 'identical' if len(values) == 1 else 'differing'


def analyze(text):
    entries = extract_rule_entries(text)
    duplicates = find_duplicates(entries)

    results = [
        {
            'key': key,
            'verdict': classify(occurrences),
            'lines': [line for _, line in occurrences],
        }
        for key, occurrences in duplicates.items()
    ]

    return {
        'total_rules': len(entries),
        'distinct_rules': len(set(k for k, _, _ in entries)),
        'duplicates': results,
    }


def print_report(results):
    dups = results['duplicates']
    total = results['total_rules']

    if not dups:
        print(f"PASSED: {total} rule key(s) checked in grammar.js, no duplicates found")
        return

    identical = [d for d in dups if d['verdict'] == 'identical']
    differing = [d for d in dups if d['verdict'] == 'differing']

    print(f"FAILED: {len(dups)} duplicate rule key(s) found in grammar.js "
          f"({len(differing)} differing, {len(identical)} identical) out of {total} rule entries")

    if differing:
        print()
        print("  DIFFERING -- live bug. JavaScript's last-write-wins object literal")
        print("  semantics silently discard every definition but the last; the grammar")
        print("  does not do what the earlier definition(s) say:")
        for d in differing:
            lines = ', '.join(f"line {n}" for n in d['lines'])
            print(f"    - '{d['key']}' defined {len(d['lines'])} times ({lines}) "
                  f"-- bodies differ, only the last is in effect")

    if identical:
        print()
        print("  IDENTICAL -- dead weight, not (yet) a behavioral bug. Byte-for-byte")
        print("  the same definition twice; safe to delete every copy but the last,")
        print("  and worth doing before someone edits only one of them:")
        for d in identical:
            lines = ', '.join(f"line {n}" for n in d['lines'])
            print(f"    - '{d['key']}' defined {len(d['lines'])} times ({lines}) "
                  f"-- byte-identical")


def main():
    parser = argparse.ArgumentParser(
        description='Detect duplicate top-level rule keys in grammar.js')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--strict', action='store_true',
                         help=argparse.SUPPRESS)  # accepted no-op, see module docstring
    args = parser.parse_args()

    grammar_path = Path('grammar.js')
    if not grammar_path.exists():
        print("Error: grammar.js not found", file=sys.stderr)
        return 1

    text = grammar_path.read_text(encoding='utf-8')
    results = analyze(text)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_report(results)

    return 1 if results['duplicates'] else 0


if __name__ == '__main__':
    sys.exit(main())
