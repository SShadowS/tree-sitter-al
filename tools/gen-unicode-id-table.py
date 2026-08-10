#!/usr/bin/env python3
"""Regenerate src/unicode_id.h — the scanner's copy of the grammar's own
identifier character classes.

WHY THIS EXISTS
---------------
`grammar.js` specifies identifiers as::

    identifier: $ => token(/[\\p{L}_][\\p{L}\\p{N}_]*/u)

`src/scanner.c` has to agree with that *exactly*, because the scanner decides
where a PROPERTY_NAME / BEGIN_KEYWORD / … token starts and ends before the
generated lexer ever sees the text. It used to ask the C library instead::

    static bool is_identifier_start(int32_t c) { return iswalpha(c) || c == '_'; }

which is wrong in both directions on Windows.  `wint_t` is 16 bits there
(measured: `sizeof(wint_t) == 2` under mingw-w64/UCRT), so `iswalpha` truncates
any codepoint above U+FFFF before testing it.  U+20000 (a plain CJK ideograph,
category Lo) folded to U+0000 and was *rejected*; U+E0041 (a Cf tag character,
not a letter) folded to 'A' and was *accepted*, so the scanner manufactured an
identifier `grammar.js` itself rejects.  `wint_t` is 32 bits on Linux, so the
same bytes took a different path there — the parser disagreed with itself
across platforms.  (`iswalpha` is LC_CTYPE-dependent by specification on top of
that, though on the runtime measured here "C", "" and "en_US.UTF-8" all agreed;
the truncation is the part that was actually observed.)

THE FIX, AND WHY IT IS GENERATED RATHER THAN WRITTEN
----------------------------------------------------
`tree-sitter generate` already compiles that regex into two sorted
`TSCharacterRange` tables inside `src/parser.c`.  Those tables *are* the
grammar's identifier classes — not an approximation of them.  This script
lifts them out verbatim, so the scanner and the generated lexer share one
definition and cannot drift.  No `wctype.h`, no locale, no `wchar_t` width.

IDENTIFICATION IS BY CONTENT, NOT BY NAME
-----------------------------------------
The generated table names are an accident of rule ordering: at the time of
writing, `[\\p{L}_]` is emitted as `sym_dotnet_assembly_name_character_set_1`
because `dotnet_assembly_name` happens to be the first rule that needs it.
Matching on that name would break silently the next time a rule is added.  So
this script computes the two target sets from `unicodedata` and locates them in
`parser.c` by content.

The two Unicode versions in play are usually *not* the same.  tree-sitter's
regex crate carries its own tables, and at the time of writing it is one
release ahead of this Python (which is 15.1.0): the compiled tables contain
4302 letters Python has never heard of, U+105C0 Todhri and friends.  So an
exact match is accepted, and so is a compiled table that is a strict superset
provided every codepoint it adds is *unassigned* in this Python — that is what
a forward version bump looks like, and it is the only relaxation allowed.  A
compiled table that is missing characters, or that adds a codepoint Python
classifies as something other than a letter, is a genuine disagreement and
fails loudly with a diff.  The emitted ranges always come from `parser.c`, so
the parser stays the authority either way.

USAGE
-----
    python tools/gen-unicode-id-table.py            # rewrite src/unicode_id.h
    python tools/gen-unicode-id-table.py --check    # exit 1 if it is stale

Run it after any `tree-sitter generate` that changes those tables — i.e. after
a tree-sitter CLI upgrade that carries a new Unicode version.  `--check` is the
regression gate; it is cheap and needs no build.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PARSER_C = REPO / "src" / "parser.c"
HEADER = REPO / "src" / "unicode_id.h"

MAX_CODEPOINT = 0x10FFFF

TABLE_RE = re.compile(
    r"static const TSCharacterRange (\w+)\[\] = \{(.*?)\n\};",
    re.DOTALL,
)
ENTRY_RE = re.compile(r"\{\s*('(?:\\.|[^'])'|0x[0-9a-fA-F]+)\s*,\s*('(?:\\.|[^'])'|0x[0-9a-fA-F]+)\s*\}")


C_ESCAPES = {
    "a": 0x07, "b": 0x08, "f": 0x0C, "n": 0x0A, "r": 0x0D, "t": 0x09,
    "v": 0x0B, "0": 0x00, "\\": 0x5C, "'": 0x27, '"': 0x22, "?": 0x3F,
}


def parse_bound(text: str) -> int:
    if text.startswith("'"):
        body = text[1:-1]
        if body.startswith("\\"):
            if body[1] not in C_ESCAPES:
                sys.exit(f"gen-unicode-id-table: unhandled C escape {text!r} in parser.c")
            return C_ESCAPES[body[1]]
        return ord(body)
    return int(text, 16)


def load_tables(source: str) -> dict[str, list[tuple[int, int]]]:
    tables: dict[str, list[tuple[int, int]]] = {}
    for name, body in TABLE_RE.findall(source):
        tables[name] = [
            (parse_bound(lo), parse_bound(hi)) for lo, hi in ENTRY_RE.findall(body)
        ]
    return tables


def ranges_to_set(ranges: list[tuple[int, int]]) -> set[int]:
    out: set[int] = set()
    for lo, hi in ranges:
        out.update(range(lo, hi + 1))
    return out


def unicode_category_set(prefix: str) -> set[int]:
    return {
        cp
        for cp in range(MAX_CODEPOINT + 1)
        if unicodedata.category(chr(cp)).startswith(prefix)
    }


def sample(s: set[int]) -> str:
    return ", ".join(f"U+{cp:04X}" for cp in sorted(s)[:12]) or "(none)"


def describe_diff(label: str, want: set[int], tables: dict[str, list[tuple[int, int]]]) -> str:
    """Best-effort explanation when no table matches, so the failure is actionable."""
    best_name, best_missing, best_extra = None, None, None
    for name, ranges in tables.items():
        got = ranges_to_set(ranges)
        missing = want - got
        extra = got - want
        if best_name is None or len(missing) + len(extra) < len(best_missing) + len(best_extra):
            best_name, best_missing, best_extra = name, missing, extra

    return (
        f"no table in {PARSER_C.name} matches {label}.\n"
        f"  closest: {best_name}\n"
        f"  in the regex but not in that table ({len(best_missing)}): {sample(best_missing)}\n"
        f"  in that table but not in the regex ({len(best_extra)}): {sample(best_extra)}\n"
        f"  python unicodedata is {unicodedata.unidata_version}."
    )


def find_table(
    label: str,
    want: set[int],
    tables: dict[str, list[tuple[int, int]]],
) -> tuple[str, list[tuple[int, int]], str]:
    """Locate the compiled table for `label` by CONTENT and report how it matched.

    Exact equality is the happy case. A *forward version bump* is also accepted:
    tree-sitter's regex crate carries its own Unicode tables and is routinely
    newer than the running Python's, and a newer Unicode only ever promotes
    previously-unassigned codepoints to letters — it does not reclassify an
    existing punctuation mark as one. So a table may be a strict superset of the
    Python set provided EVERY extra codepoint is unassigned (`Cn`) here. That
    condition is what keeps the acceptance narrow: a genuine disagreement, where
    the compiled table and the regex mean different things, still fails loudly,
    and so does a table that is merely missing characters.

    It also keeps identification unambiguous. `[\\p{L}\\p{N}_]` is a superset of
    `[\\p{L}_]` too, but the numbers it adds are not `Cn`, so the continue table
    can never be mistaken for the start table.
    """
    exact = [(n, r) for n, r in tables.items() if ranges_to_set(r) == want]
    if exact:
        return exact[0][0], exact[0][1], f"exact under Unicode {unicodedata.unidata_version}"

    newer: list[tuple[str, list[tuple[int, int]], set[int]]] = []
    for name, ranges in tables.items():
        got = ranges_to_set(ranges)
        if not got >= want:
            continue
        added = got - want
        if all(unicodedata.category(chr(cp)) == "Cn" for cp in added):
            newer.append((name, ranges, added))

    if not newer:
        sys.exit("gen-unicode-id-table: " + describe_diff(label, want, tables))

    distinct = {tuple(r) for _, r, _ in newer}
    if len(distinct) != 1:
        sys.exit(
            f"gen-unicode-id-table: {label} matched {len(distinct)} DIFFERENT tables "
            f"({', '.join(n for n, _, _ in newer)}); identification is ambiguous, "
            f"so the generator refuses to guess."
        )

    name, ranges, added = newer[0]
    short = (f"superset of Unicode {unicodedata.unidata_version} by {len(added)} "
             f"codepoints, all unassigned there")
    print(f"  {label}: {name} — {short} (e.g. {sample(added)})", file=sys.stderr)
    return name, ranges, short


def format_ranges(ranges: list[tuple[int, int]]) -> str:
    cells = [f"{{0x{lo:X}, 0x{hi:X}}}," for lo, hi in ranges]
    lines, row = [], []
    for cell in cells:
        row.append(cell)
        if len(row) == 6:
            lines.append("  " + " ".join(row))
            row = []
    if row:
        lines.append("  " + " ".join(row))
    return "\n".join(lines)


def format_ascii(ranges: list[tuple[int, int]]) -> str:
    """The same class restricted to ASCII, as a 128-entry membership table.

    Derived from `ranges`, never from a separate notion of what ASCII letters
    are — that is the whole point of generating it.
    """
    member = ranges_to_set(ranges)
    lines = []
    for base in range(0, 128, 16):
        row = " ".join(f"{1 if base + i in member else 0}," for i in range(16))
        lines.append(f"  {row}  // 0x{base:02X}")
    return "\n".join(lines)


HEADER_TEMPLATE = '''// GENERATED by tools/gen-unicode-id-table.py — do not edit by hand.
//
// The identifier character classes of grammar.js's own rule:
//
//     identifier: $ => token(/[\\p{{L}}_][\\p{{L}}\\p{{N}}_]*/u)
//
// lifted verbatim out of the tables `tree-sitter generate` compiled that regex
// into, so src/scanner.c and the generated lexer share ONE definition of what a
// letter is. Source tables in src/parser.c at generation time:
//
//     start      <- {start_name} ({start_count} ranges)
//                   {start_how}
//     continue   <- {cont_name} ({cont_count} ranges)
//                   {cont_how}
//
// Those names are an accident of rule ordering and are recorded for traceability
// only; the generator finds the tables by content, and re-verifies that content
// against Python's unicodedata on every run (--check).
//
// WHY NOT wctype.h: wint_t is 16 bits on Windows (measured: sizeof(wint_t) == 2
// under mingw-w64/UCRT), so an int32_t codepoint above U+FFFF is truncated
// before the test. U+20000 (category Lo, an ordinary identifier character)
// folded to U+0000 and was REJECTED; U+E0041 (category Cf, not a letter) folded
// to 'A' and was ACCEPTED, so the scanner manufactured an identifier grammar.js
// itself rejects. wint_t is 32 bits on Linux, so the same file took a different
// path there. iswalpha is LC_CTYPE-dependent by specification on top of that.
// Never reintroduce a ctype/wctype call here.

#ifndef TREE_SITTER_AL_UNICODE_ID_H_
#define TREE_SITTER_AL_UNICODE_ID_H_

#include <stdbool.h>
#include <stdint.h>

#include "tree_sitter/parser.h"

// [\\p{{L}}_] — what an identifier may START with.
static const TSCharacterRange al_id_start_ranges[] = {{
{start_body}
}};

// [\\p{{L}}\\p{{N}}_] — what an identifier may CONTINUE with.
static const TSCharacterRange al_id_continue_ranges[] = {{
{cont_body}
}};

// ASCII fast path. These are the SAME two classes restricted to U+0000..U+007F,
// derived from the range tables above by this generator rather than written out
// by hand — so there is still exactly one source of truth, and --check catches
// any divergence between the two forms.
//
// Not a premature optimization, and not an unmeasured one either.
// is_identifier_char runs once per character of every identifier the scanner
// reads, and a binary search over {cont_count} ranges is ~10 compares where the
// old iswalnum() was one libc table lookup. Timed over the same 3000 BC.History
// files, warm:
//
//   iswalpha/iswalnum (HEAD)       median 3777 ms   (7 runs)
//   ranges only, no fast path      median 3937 ms   (3 runs)  +3.2%
//   ranges + this table            median 3774 ms   (7 runs)  -0.1%
//
// So the binary search alone was a real regression, not noise, and the ASCII
// table removes it completely — nearly all AL is ASCII, and that path is back
// to one indexed load. Discard the FIRST run after any `tree-sitter generate`:
// it carries the parser rebuild and measured 17.4 s here.
static const unsigned char al_id_start_ascii[128] = {{
{start_ascii}
}};

static const unsigned char al_id_continue_ascii[128] = {{
{cont_ascii}
}};

// Beyond ASCII, set_contains() comes from tree_sitter/parser.h: the very binary
// search the generated lexer runs over these same ranges. Sharing it, rather
// than writing a second lookup, is deliberate.
static inline bool al_is_identifier_start(int32_t c) {{
  if ((uint32_t)c < 128u) return al_id_start_ascii[c] != 0;
  return c > 0 && set_contains(al_id_start_ranges,
                               (uint32_t)(sizeof(al_id_start_ranges) /
                                          sizeof(al_id_start_ranges[0])), c);
}}

static inline bool al_is_identifier_char(int32_t c) {{
  if ((uint32_t)c < 128u) return al_id_continue_ascii[c] != 0;
  return c > 0 && set_contains(al_id_continue_ranges,
                               (uint32_t)(sizeof(al_id_continue_ranges) /
                                          sizeof(al_id_continue_ranges[0])), c);
}}

#endif  // TREE_SITTER_AL_UNICODE_ID_H_
'''


def build_header() -> str:
    source = PARSER_C.read_text(encoding="utf-8")
    tables = load_tables(source)
    if not tables:
        sys.exit(f"gen-unicode-id-table: no TSCharacterRange tables found in {PARSER_C}")

    letters = unicode_category_set("L")
    numbers = unicode_category_set("N")
    underscore = {ord("_")}

    start_name, start_ranges, start_how = find_table(
        r"[\p{L}_]", letters | underscore, tables)
    cont_name, cont_ranges, cont_how = find_table(
        r"[\p{L}\p{N}_]", letters | numbers | underscore, tables)

    # Cross-check that the two tables really are start/continue of one class and
    # not two unrelated tables that each happened to pass: continue must contain
    # start, and everything it adds must be a number (or a codepoint this Python
    # has not heard of yet). A letter appearing only in the continue table would
    # mean one of the two is the wrong table.
    start_set, cont_set = ranges_to_set(start_ranges), ranges_to_set(cont_ranges)
    if not cont_set >= start_set:
        sys.exit(f"gen-unicode-id-table: {cont_name} does not contain {start_name}; "
                 f"missing {sample(start_set - cont_set)}")
    stray = {cp for cp in cont_set - start_set
             if not unicodedata.category(chr(cp)).startswith(("N", "C"))}
    if stray:
        sys.exit(f"gen-unicode-id-table: {cont_name} adds non-numbers over "
                 f"{start_name}: {sample(stray)}")

    return HEADER_TEMPLATE.format(
        start_name=start_name,
        start_count=len(start_ranges),
        start_how=start_how,
        cont_name=cont_name,
        cont_count=len(cont_ranges),
        cont_how=cont_how,
        start_body=format_ranges(start_ranges),
        cont_body=format_ranges(cont_ranges),
        start_ascii=format_ascii(start_ranges),
        cont_ascii=format_ascii(cont_ranges),
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if src/unicode_id.h differs from what would be generated")
    args = ap.parse_args()

    generated = build_header()

    if args.check:
        current = HEADER.read_text(encoding="utf-8") if HEADER.exists() else ""
        if current != generated:
            print(
                f"{HEADER.relative_to(REPO)} is stale relative to src/parser.c.\n"
                "Run: python tools/gen-unicode-id-table.py",
                file=sys.stderr,
            )
            return 1
        print(f"{HEADER.relative_to(REPO)} matches src/parser.c")
        return 0

    HEADER.write_text(generated, encoding="utf-8", newline="\n")
    print(f"wrote {HEADER.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
