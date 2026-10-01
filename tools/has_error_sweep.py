#!/usr/bin/env python3
"""has_error_sweep.py -- fail on any parse error, including the ones nothing prints.

A MISSING node for a HIDDEN (`_`-prefixed) token is not printed by `tree-sitter
parse` and leaves `--json-summary` saying successful, so parse-al-parallel.sh
counts the file as parsed OK. Only py-tree-sitter's `root_node.has_error` sees
it. (`tree-sitter test` does print `(MISSING _x)`, but only for a corpus case
that holds the triggering input -- it says nothing about production code.) The
`_directive_eol` whitespace regression (fixed in 673528e) lived through
parse-al-parallel.sh that way (docs/deferred-work.md item 12).

Each input is one of:
  clean        has_error is False
  visible      an ERROR node or a visible MISSING node exists. If a hidden error
               sits OUTSIDE every ERROR node as well, the line also names it
               (`hidden: ...`) and the summary counts it under with-hidden=
  hidden-only  has_error is True and no visible ERROR/MISSING node exists

The tree API never exposes hidden nodes, so a hidden error is located as the
first node (pre-order) whose has_error is True while it is neither an error
itself nor has any child with has_error: the hidden token is inside it. A hidden
error in a node that ALSO has an erroring child is not located separately; the
node's other error is reported instead. Nothing inside an ERROR node is examined
for hidden errors: that is recovery debris, not a separate defect.

--corpus-fixtures sweeps EVERY case of test/corpus. A case in a deliberate-
negative file (tools/deliberate-negatives.txt, matched by basename exactly as
validate-grammar.sh Step 3 does) may be `visible` -- its ERROR is the assertion
-- but hidden-only or visible-with-hidden still fails there.

Exit: 0 nothing failed; 1 any failure; 2 the sweep cannot run (a missing or
empty root, no fixtures, a build failure, a library that will not load, or any
crash while sweeping, e.g. an undecodable file or a dead worker). A missing
input never passes and a crash never reads as "parse errors found".

    python tools/has_error_sweep.py --root ./BC.History/ [--root DIR ...]
    python tools/has_error_sweep.py --corpus-fixtures
    python tools/has_error_sweep.py --root DIR --lib path/to/al.dll
"""
from __future__ import annotations

import argparse
import contextlib
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path, PurePosixPath

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.config_oracle import fixtures  # noqa: E402
from tools.query_coverage import loader  # noqa: E402

REPO = loader.REPO_ROOT
CORPUS = REPO / "test" / "corpus"
# The ONE list of corpus files whose ERROR nodes are the assertion. Read by
# validate-grammar.sh Step 3 and .claude/commands/release.md as well.
NEGATIVES_FILE = REPO / "tools" / "deliberate-negatives.txt"


class CannotRun(Exception):
    pass


def deliberate_negatives() -> set[str]:
    lines = NEGATIVES_FILE.read_text(encoding="utf-8").splitlines()
    return {s for s in (line.strip() for line in lines) if s and not s.startswith("#")}


def is_negative(corpus_relpath: str, names: set[str] | None = None) -> bool:
    """Basename match: the rule validate-grammar.sh Step 3 applies."""
    return PurePosixPath(corpus_relpath.replace("\\", "/")).name in (
        deliberate_negatives() if names is None else names)


def accepted(category: str, negative: bool) -> bool:
    return category == "clean" or (negative and category == "visible")


def _where(n) -> str:
    (r0, c0), (r1, c1) = n.start_point, n.end_point
    return f"{n.type}@{n.start_byte}-{n.end_byte} ({r0 + 1}:{c0 + 1}-{r1 + 1}:{c1 + 1})"


def classify(tree):
    """(category, first visible error node or None, first hidden-error site or None).

    category is clean, visible, visible+hidden or hidden-only.
    """
    root = tree.root_node
    if not root.has_error:
        return "clean", None, None
    visible = hidden = None
    # Pre-order over the has_error subtrees only.
    cursor = tree.walk()
    while True:
        n = cursor.node
        descend = False
        if n.is_error or n.is_missing:
            visible = visible or n
        elif n.has_error:
            if not any(c.has_error for c in n.children):
                hidden = hidden or n
            descend = True
        if visible is not None and hidden is not None:
            break
        if descend and cursor.goto_first_child():
            continue
        while not cursor.goto_next_sibling():
            if not cursor.goto_parent():
                break
        else:
            continue
        break  # climbed past the root
    if visible is not None:
        return ("visible+hidden" if hidden is not None else "visible"), visible, hidden
    if hidden is None:  # cannot happen: the deepest has_error node qualifies
        hidden = root
    return "hidden-only", None, hidden


def decode_al(data: bytes) -> str:
    """AL source bytes as text. UTF-16 with a BOM is decoded as such, as `tree-sitter
    parse` does: BCApps ships 19 such files (HybridGP GP tables), and read as UTF-8 each
    is one whole-file ERROR. Anything else is UTF-8 with a BOM stripped (the scanner
    skips U+FEFF as an extra, so the tree is unchanged). Bytes that are not UTF-8
    survive as surrogates: encode with ("utf-8", "surrogateescape") to get them back."""
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return data.decode("utf-16")
    return data.decode("utf-8-sig", "surrogateescape")


def read_al(path) -> str:
    """decode_al of a file's bytes; read as bytes, so no CR/LF translation."""
    return decode_al(Path(path).read_bytes())


def inputs(roots, corpus_fixtures):
    """[(label, bytes-or-Path, is_negative)]."""
    out = []
    for r in roots:
        root = Path(r)
        if not root.is_dir():
            raise CannotRun(f"root does not exist or is not a directory: {r}")
        files = sorted(p for p in root.rglob("*") if p.suffix.lower() == ".al" and p.is_file())
        if not files:
            raise CannotRun(f"root holds no .al files: {r}")
        out += [(str(p), p, False) for p in files]
    if corpus_fixtures:
        cases = fixtures.extract(CORPUS)
        if not cases:
            raise CannotRun(f"no corpus fixtures under {CORPUS}")
        names = deliberate_negatives()
        if not names:
            raise CannotRun(f"{NEGATIVES_FILE} lists nothing")
        out += [(c.id, c.source, is_negative(c.file, names)) for c in cases]
    return out


def load_parser(lib):
    try:
        path = Path(lib) if lib else loader.ensure_library(REPO)
        return path, loader.make_parser(loader.load_language(path))
    except Exception as e:  # a build failure or a library that will not load
        raise CannotRun(f"cannot load the parser: {type(e).__name__}: {e}") from e


PARSER = None


def init_worker(parser_or_lib):
    global PARSER
    PARSER = (parser_or_lib if not isinstance(parser_or_lib, Path)
               else loader.make_parser(loader.load_language(parser_or_lib)))


def check(item):
    """(label, category, negative, visible-where, hidden-where)."""
    label, src, negative = item
    text = read_al(src) if isinstance(src, Path) else decode_al(src)
    category, vis, hid = classify(PARSER.parse(text.encode("utf-8", "surrogateescape")))
    return label, category, negative, vis and _where(vis), hid and _where(hid)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--root", action="append", default=[], help="recurse into *.al (repeatable)")
    ap.add_argument("--corpus-fixtures", action="store_true",
                    help="every test/corpus case; deliberate negatives may be visible")
    ap.add_argument("--lib", help="use this compiled parser instead of building al.dll")
    ap.add_argument("--jobs", type=int, help="worker processes (default: CPU count, but "
                    "inputs under 500 run in-process)")
    args = ap.parse_args(argv)
    if not args.root and not args.corpus_fixtures:
        ap.error("give --root DIR and/or --corpus-fixtures")

    t0 = time.perf_counter()
    counts = dict.fromkeys(("clean", "visible", "with-hidden", "hidden-only", "negative-visible"), 0)
    failed = 0
    try:
        items = inputs(args.root, args.corpus_fixtures)
        lib_path, parser = load_parser(args.lib)
        jobs = args.jobs or (1 if len(items) < 500 else os.cpu_count() or 1)
        init_worker(parser)
        # Workers load the same library the parent just built or was given.
        with (ProcessPoolExecutor(jobs, initializer=init_worker, initargs=(lib_path,)) if jobs > 1
              else contextlib.nullcontext()) as pool:
            results = pool.map(check, items, chunksize=64) if pool else map(check, items)
            for label, category, negative, vis, hid in results:
                if category == "clean":
                    counts["clean"] += 1
                    continue
                if category == "hidden-only":
                    counts["hidden-only"] += 1
                else:
                    counts["visible"] += 1
                    if category == "visible+hidden":
                        counts["with-hidden"] += 1
                    elif negative:
                        counts["negative-visible"] += 1
                if accepted(category, negative):
                    continue  # a deliberate negative's ERROR is its assertion
                failed += 1
                shown = "visible" if category.startswith("visible") else category
                print(f"{shown}\t{label}\t{vis or hid}" + (f"\thidden: {hid}" if vis and hid else ""))
    except CannotRun as e:
        print(f"has_error_sweep: CANNOT RUN: {e}", file=sys.stderr)
        return 2
    except Exception as e:  # a crash after setup is not a parse result
        print(f"has_error_sweep: CANNOT RUN: crashed while sweeping: {type(e).__name__}: {e}",
              file=sys.stderr)
        return 2

    print(f"has_error_sweep: files={len(items)} clean={counts['clean']} "
          f"visible={counts['visible']} with-hidden={counts['with-hidden']} "
          f"hidden-only={counts['hidden-only']} negative-visible={counts['negative-visible']} "
          f"failed={failed} ({time.perf_counter() - t0:.1f}s)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
