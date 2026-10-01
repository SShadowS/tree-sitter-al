#!/usr/bin/env python3
"""snip.py -- parse an AL snippet and show what matters: fields, has_error, every error.

    python tools/snip.py 'i := 1 #if X\\n + #endif\\n 2;'   # statement(s) in a procedure body
    python tools/snip.py --object 'procedure Q() begin end;'  # members of a codeunit body
    python tools/snip.py --raw -f file.al                     # the text is the whole file
    echo 'x := 1;' | python tools/snip.py -                   # stdin
    python tools/snip.py --sexp 'x := 1;'                     # tree-sitter test format
    python tools/snip.py --census --root ./BC.History/        # two-shape detector

A literal `\\n` in the ARGUMENT is a newline (directives need their own lines). That also
rewrites a `\\n` inside an AL string, so for text holding backslashes use -f or stdin,
which are taken as is: read as bytes (no CR/LF translation), UTF-8 with a BOM stripped,
or UTF-16 with a BOM (has_error_sweep.read_al).

Default output is the tree from a TREE CURSOR, so fields on anonymous children show
(`operator: "+"`; `tree-sitter parse` hides them, see tools/edge-census.c), with the
text of every leaf and of any node under 40 characters. Then `has_error`, then every
ERROR and MISSING node, plus every HIDDEN error site: a MISSING `_hidden` token that
`tree-sitter parse` does not print (CLAUDE.md, "A MISSING node for a HIDDEN token").
The node holding it is reported, since the API never exposes the hidden node itself.
Positions are line:col, 1-based, in the SNIPPET; a position in the wrapper's head or tail
is labelled `wrapper` and given in the wrapped text. Columns count BYTES, not characters
(tree-sitter's points do), so a non-ASCII character before it moves a column by 2 or more.

--sexp pretty-prints ts_node_string (py-tree-sitter's str(root_node)), which is exactly
the string `tree-sitter test` compares, with field labels, MISSING and UNEXPECTED; it
pastes into a corpus fixture and asserts fields (CLAUDE.md -u trap 2).

--census counts nodes by (type, named children, anonymous children) over every .al under
the roots, and flags a leaf-like type (`*_keyword`, `*identifier`) with more than one
shape: the two-shape defect class no other gate sees (.claude/rules/contextual-keywords.md).
For the (parent, field, child) EDGE census use tools/edge-census.c, not this.

Locking: none needed. The library is the repo-local ./al.dll that loader.ensure_library
rebuilds under its own build lock when a grammar source changed. That is not the shared
tree-sitter CLI cache that tools/ts-lock.sh guards. Do not wrap this in ts-lock.

Exit: 0 clean tree / nothing flagged; 1 has_error / a type flagged; 2 cannot run.
"""
from __future__ import annotations

import argparse
import contextlib
import os
import re
import sys
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import has_error_sweep  # noqa: E402
from tools.query_coverage import loader  # noqa: E402

STATEMENT_HEAD = "codeunit 50100 T\n{\n    procedure P()\n    begin\n"
STATEMENT_TAIL = "\n    end;\n}\n"
OBJECT_HEAD = "codeunit 50100 T\n{\n"
OBJECT_TAIL = "\n}\n"
SHORT = 40


def wrap(text: str, mode: str) -> tuple[str, tuple[int, int], tuple[int, int]]:
    """(source, snippet start point, snippet end point); points are (row, byte column)."""
    head, tail = {"statement": (STATEMENT_HEAD, STATEMENT_TAIL),
                  "object": (OBJECT_HEAD, OBJECT_TAIL), "raw": ("", "")}[mode]
    row0, lines = head.count("\n"), text.split("\n")
    end = (row0 + len(lines) - 1, len(lines[-1].encode("utf-8", "surrogateescape")))
    return head + text + tail, (row0, 0), end


def _pos(node, start, end, at_end=False) -> str:
    r, c = node.end_point if at_end else node.start_point
    if start <= (r, c) <= end:
        return f"{r - start[0] + 1}:{c + 1}"
    return f"wrapper {r + 1}:{c + 1}"


def _text(node) -> str | None:
    if node.is_missing:
        return None
    t = node.text.decode("utf-8", "replace")
    if (node.child_count == 0 or len(t) < SHORT) and "\n" not in t:
        return t
    return None


def walk(tree):
    """Pre-order (node, field, depth) over every visible node, from a cursor."""
    cursor, depth = tree.walk(), 0
    while True:
        yield cursor.node, cursor.field_name, depth
        if cursor.goto_first_child():
            depth += 1
            continue
        while not cursor.goto_next_sibling():
            if not cursor.goto_parent():
                return
            depth -= 1


def render_tree(tree) -> str:
    out = []
    for n, field, depth in walk(tree):
        label = f"{field}: " if field else ""
        kind = n.type if n.is_named else f'"{n.type}"'
        if n.is_missing:
            kind = f"MISSING {kind}"
        text = _text(n) if n.is_named else None
        out.append("  " * depth + label + kind + (f"  {text!r}" if text is not None else ""))
    return "\n".join(out)


# ts_node_string's tokens (tree-sitter lib/src/subtree.c, ts_subtree__write_to_string):
# a whole `(MISSING "x")` or `(UNEXPECTED 'c')` (their text may hold parentheses), an
# opening `(type` or `(MISSING type`, a `)`, or a `field:` label.
SEXP_TOKEN = re.compile(r"""\(MISSING ".*?"\)|\(UNEXPECTED (?:'(?:\\.|[^\\])'|INVALID|-?\d+)\)"""
                        r"""|\((?:MISSING )?[^\s()]+|\)|[^\s()]+:""")


def pretty_sexp(flat: str) -> str:
    """One node per line, indented by depth, a field label on its node's line. Only
    whitespace differs from `flat`, and tree-sitter test ignores whitespace."""
    out, depth, after_field = [], 0, False
    for t in SEXP_TOKEN.findall(flat):
        if t == ")":
            out.append(")")
            depth -= 1
            continue
        if not after_field and out:
            out.append("\n" + "  " * depth)
        out.append(t + (" " if t.endswith(":") else ""))
        after_field = t.endswith(":") and not t.startswith("(")
        if t.startswith("(") and not t.endswith(")"):
            depth += 1
    return "".join(out)


def sexp(tree) -> str:
    flat = str(tree.root_node)
    pretty = pretty_sexp(flat)
    if " ".join(pretty.split()) != flat:  # a token SEXP_TOKEN does not know: never guess
        print("snip: --sexp could not pretty-print this tree; printing it flat", file=sys.stderr)
        return flat
    return pretty


def problems(tree):
    """[(kind, node)]: every ERROR, every MISSING, and every hidden-error site outside an
    ERROR (has_error, not itself an error, no child with has_error; the classify() rule of
    has_error_sweep, applied to every site instead of the first)."""
    found, stack = [], [tree.root_node]
    while stack:
        n = stack.pop()
        if not n.has_error and not n.is_missing:
            continue
        if n.is_error:
            found.append(("ERROR", n))
            stack.extend(c for c in n.children if c.is_missing)  # still worth naming
            continue
        if n.is_missing:
            found.append(("MISSING", n))
            continue
        if not any(c.has_error for c in n.children):
            found.append(("HIDDEN", n))
        stack.extend(reversed(n.children))
    return sorted(found, key=lambda p: p[1].start_byte)


def snip(args) -> int:
    if args.file == "-" or (not args.file and args.snippet == "-"):
        text = has_error_sweep.decode_al(sys.stdin.buffer.read())
    elif args.file:
        text = has_error_sweep.read_al(args.file)
    elif args.snippet is not None:
        text = args.snippet.replace("\\n", "\n")
    else:
        print("snip: give a snippet, -f FILE, or - for stdin", file=sys.stderr)
        return 2
    mode = "raw" if args.raw else "object" if args.object else "statement"
    source, start, end = wrap(text, mode)
    parser = loader.make_parser(loader.load_language(loader.ensure_library(loader.REPO_ROOT)))
    tree = parser.parse(source.encode("utf-8", "surrogateescape"))
    if args.sexp:
        print(sexp(tree))
    else:
        print(render_tree(tree))
        print(f"\nhas_error: {tree.root_node.has_error}")
        for kind, n in problems(tree):
            what = n.type if kind != "HIDDEN" else f"inside {n.type} (a MISSING hidden token)"
            print(f"{kind}\t{_pos(n, start, end)}-{_pos(n, start, end, at_end=True)}\t{what}")
    return 1 if tree.root_node.has_error else 0


# --- shape census -------------------------------------------------------------------

def leaf_like(t: str) -> bool:
    return t.endswith("_keyword") or t.endswith("identifier")


def _shapes(item):
    _, src, _ = item
    data = has_error_sweep.read_al(src).encode("utf-8", "surrogateescape")
    counts = Counter()
    for n, _, _ in walk(has_error_sweep.PARSER.parse(data)):
        if n.is_named and not n.is_missing:
            named = n.named_child_count
            counts[(n.type, named, n.child_count - named)] += 1
    return counts


def flag(total: Counter):
    """({type: {(named, anon): count}}, sorted leaf-like types with more than one shape)."""
    by_type = defaultdict(dict)
    for (t, named, anon), n in total.items():
        by_type[t][(named, anon)] = n
    return by_type, sorted(t for t, shapes in by_type.items() if leaf_like(t) and len(shapes) > 1)


def census(roots, jobs=None) -> int:
    try:
        inputs = has_error_sweep.inputs(roots, False)
        lib_path, parser = has_error_sweep.load_parser(None)
    except has_error_sweep.CannotRun as e:
        print(f"snip --census: CANNOT RUN: {e}", file=sys.stderr)
        return 2
    has_error_sweep.init_worker(parser)
    jobs = jobs or (1 if len(inputs) < 500 else os.cpu_count() or 1)
    total = Counter()
    with (ProcessPoolExecutor(jobs, initializer=has_error_sweep.init_worker, initargs=(lib_path,))
          if jobs > 1 else contextlib.nullcontext()) as pool:
        for c in (pool.map(_shapes, inputs, chunksize=64) if pool else map(_shapes, inputs)):
            total.update(c)
    by_type, flagged = flag(total)
    for t in flagged:
        print(t)
        for (named, anon), n in sorted(by_type[t].items(), key=lambda kv: -kv[1]):
            print(f"  named={named} anon={anon}\t{n}")
    checked = sum(1 for t in by_type if leaf_like(t))
    print(f"snip --census: files={len(inputs)} nodes={sum(total.values())} types={len(by_type)} "
          f"leaf-like={checked} flagged={len(flagged)}")
    return 1 if flagged else 0


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):  # AL text is UTF-8; a cp1252 console is not
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    doc = __doc__ or ""
    ap = argparse.ArgumentParser(description=doc.split("\n")[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=doc.split("\n", 2)[2])
    ap.add_argument("snippet", nargs="?", help="AL text; '-' reads stdin")
    ap.add_argument("-f", dest="file", help="read the text from FILE ('-' is stdin)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--object", action="store_true", help="wrap as members of a codeunit body")
    g.add_argument("--raw", action="store_true", help="the text is a whole file")
    ap.add_argument("--sexp", action="store_true", help="print tree-sitter test format")
    ap.add_argument("--census", action="store_true", help="shape census over --root dirs")
    ap.add_argument("--root", action="append", default=[], help="census root (repeatable)")
    ap.add_argument("--jobs", type=int, help="census worker processes")
    args = ap.parse_args(argv)
    try:
        if args.census:
            if not args.root:
                ap.error("--census needs --root DIR")
            return census(args.root, args.jobs)
        return snip(args)
    except SystemExit:
        raise
    except Exception as e:
        print(f"snip: CANNOT RUN: {type(e).__name__}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
