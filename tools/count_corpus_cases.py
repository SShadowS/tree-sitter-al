#!/usr/bin/env python3
"""Count the corpus cases tree-sitter will actually RUN, independently of it.

WHY THIS EXISTS

A corpus case can exist in a file and never run, silently. There is no warning
and no error: the suite total simply comes out lower than the files declare, and
nothing compares those two numbers. Two separate mechanisms do it:

  1. A blank line inside the `====` header block. tree-sitter's header regex
     wants one-or-more name lines that are non-empty and do not start with '=';
     a blank line ends the match early and the header stops being a header.

  2. No `---` divider after the header. The header parses, the body has no
     input/expected split, and the case is discarded.

Mechanism 2 hid `test/corpus/built_in_functions_al.txt` -- a well-formed header
and 110 lines of AL -- for the entire life of the file. It was never run once.
It surfaced only because a raw header count ran a consistent +1 high against
what the suite reported, across every revision anyone checked.

This is deliberately a SECOND implementation of tree-sitter's corpus parsing
rather than a call into it. A count derived from the same code that does the
dropping cannot detect the dropping; that is the whole point. Keep it
independent even if it means duplicating a regex.

USAGE
    python tools/count_corpus_cases.py [corpus_dir]

Prints machine-readable `key=value` lines plus a DROPPED line per lost case.
Exit 0 if every declared case is runnable, 1 if any case would be dropped.
"""
import re
import sys
import pathlib

# tree-sitter cli/src/test.rs, in effect. The name block is one or more lines
# that are non-empty AND do not begin with '='.
HEADER = re.compile(
    rb"(?m)^(?P<equals>={3,})\r?\n(?P<name>(?:[^=\r\n][^\r\n]*\r?\n)+)(?P=equals)\r?\n"
)
DIVIDER = re.compile(rb"(?m)^-{3,}[ \t]*\r?$")
# tree-sitter test attributes sit on their own line inside the header's name
# block. `:skip` makes tree-sitter parse the header and then NOT run the case,
# so it lands in the same declared-but-not-run gap as a missing divider and
# would otherwise show up as an unexplained off-by-N. It is reported separately
# because it is not a corpus-format defect -- it is a DISABLED TEST, which
# CLAUDE.md's "no known limitations" rule forbids in this repo, so the right
# response is to say so rather than to quietly subtract it.
# `:error` and `:fail-fast` still run and need no handling. `:platform(...)`
# runs conditionally and is flagged as unmodelled rather than guessed at.
SKIP_ATTR = re.compile(rb"(?m)^:skip[ \t]*\r?$")
PLATFORM_ATTR = re.compile(rb"(?m)^:platform\b")
# A run of '=' on its own line, whether or not it forms a valid header. The gap
# between this and HEADER is how mechanism 1 shows up.
EQ_LINE = re.compile(rb"(?m)^={3,}[ \t]*\r?$")


def scan(root: pathlib.Path):
    runnable, headers, eq_lines = 0, 0, 0
    dropped = []
    skipped = []
    unmodelled = []
    for path in sorted(root.rglob("*.txt")):
        data = path.read_bytes()
        eq_lines += len(EQ_LINE.findall(data))
        hits = list(HEADER.finditer(data))
        headers += len(hits)
        rel = str(path.relative_to(root)).replace("\\", "/")
        for i, m in enumerate(hits):
            end = hits[i + 1].start() if i + 1 < len(hits) else len(data)
            name = m.group("name").split(b"\n")[0].strip().decode("utf8", "replace")
            attrs = m.group("name")
            if not DIVIDER.search(data[m.end():end]):
                dropped.append((rel, name, "no '---' divider after the header"))
            elif SKIP_ATTR.search(attrs):
                skipped.append((rel, name))
            else:
                runnable += 1
                if PLATFORM_ATTR.search(attrs):
                    unmodelled.append((rel, name))
    # An '=' line that is not part of a matched header is mechanism 1: the pair
    # is there, the header is not. Reported as a count because the malformed
    # block has no parseable name to report.
    orphan_eq = eq_lines - headers * 2
    return runnable, headers, orphan_eq, dropped, skipped, unmodelled


def main() -> int:
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "test/corpus")
    if not root.is_dir():
        print(f"count_corpus_cases: no such directory: {root}", file=sys.stderr)
        return 2
    runnable, headers, orphan_eq, dropped, skipped, unmodelled = scan(root)
    print(f"runnable_cases={runnable}")
    print(f"declared_headers={headers}")
    print(f"orphan_equals_lines={orphan_eq}")
    print(f"dropped_cases={len(dropped)}")
    print(f"skipped_cases={len(skipped)}")
    for rel, name, why in dropped:
        print(f"DROPPED\t{rel}\t{name}\t{why}")
    if orphan_eq:
        print(
            f"DROPPED\t(unknown file)\t(unparseable header)\t{orphan_eq} stray "
            f"'=' line(s) form no valid header — most likely a blank line inside one"
        )
    for rel, name in skipped:
        print(f"SKIPPED\t{rel}\t{name}\t:skip disables this case")
    for rel, name in unmodelled:
        print(f"UNMODELLED\t{rel}\t{name}\t:platform runs conditionally")
    return 1 if (dropped or orphan_eq or skipped) else 0


if __name__ == "__main__":
    sys.exit(main())
