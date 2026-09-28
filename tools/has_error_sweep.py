#!/usr/bin/env python3
"""has_error_sweep.py -- fail on any parse error, including the ones nothing prints.

A MISSING node for a HIDDEN (`_`-prefixed) token is never printed: `tree-sitter
parse`, `--json-summary`, parse-al-parallel.sh and the corpus tests all report
success while py-tree-sitter's `root_node.has_error` is True. The
`_directive_eol` whitespace regression (fixed in 673528e) lived through every
gate that way (docs/deferred-work.md item 12). This sweep reads `has_error`.

Each input is one of:
  clean        has_error is False
  visible      an ERROR node or a visible MISSING node exists
  hidden-only  has_error is True and no visible ERROR/MISSING node exists. The
               tree API never exposes hidden nodes, so the reported node is the
               deepest visible node carrying has_error: the hidden token is
               inside it.

Exit: 0 all clean; 1 any visible or hidden-only; 2 the sweep cannot run (a
missing or empty root, no fixtures, a build failure, a library that will not
load). A missing input never passes.

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
from pathlib import Path

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


def corpus_fixture_inputs_cases():
    skip = deliberate_negatives()
    return [c for c in fixtures.extract(CORPUS) if c.file not in skip]


def _where(n) -> str:
    (r0, c0), (r1, c1) = n.start_point, n.end_point
    return f"{n.type}@{n.start_byte}-{n.end_byte} ({r0 + 1}:{c0 + 1}-{r1 + 1}:{c1 + 1})"


def classify(tree):
    """(category, first offending node or None)."""
    root = tree.root_node
    if not root.has_error:
        return "clean", None
    if root.is_error or root.is_missing:
        return "visible", root
    # Pre-order over the has_error subtrees only; the first ERROR/MISSING wins.
    cursor = tree.walk()
    while True:
        n = cursor.node
        if n.is_error or n.is_missing:
            return "visible", n
        if n.has_error and cursor.goto_first_child():
            continue
        while not cursor.goto_next_sibling():
            if not cursor.goto_parent():
                break
        else:
            continue
        break  # climbed past the root: no visible error anywhere
    n = root
    while (child := next((c for c in n.children if c.has_error), None)) is not None:
        n = child
    return "hidden-only", n


def _inputs(roots, corpus_fixtures):
    out = []
    for r in roots:
        root = Path(r)
        if not root.is_dir():
            raise CannotRun(f"root does not exist or is not a directory: {r}")
        files = sorted(p for p in root.rglob("*") if p.suffix.lower() == ".al" and p.is_file())
        if not files:
            raise CannotRun(f"root holds no .al files: {r}")
        out += [(str(p), p) for p in files]
    if corpus_fixtures:
        cases = corpus_fixture_inputs_cases()
        if not cases:
            raise CannotRun(f"no corpus fixtures under {CORPUS}")
        out += [(c.id, c.source) for c in cases]
    return out


def _parser(lib):
    try:
        path = Path(lib) if lib else loader.ensure_library(REPO)
        return path, loader.make_parser(loader.load_language(path))
    except Exception as e:  # a build failure or a library that will not load
        raise CannotRun(f"cannot load the parser: {type(e).__name__}: {e}") from e


_PARSER = None


def _init(parser_or_lib):
    global _PARSER
    _PARSER = (parser_or_lib if not isinstance(parser_or_lib, Path)
               else loader.make_parser(loader.load_language(parser_or_lib)))


def _check(item):
    label, src = item
    data = src.read_bytes() if isinstance(src, Path) else src
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        # UTF-16 with a BOM, which `tree-sitter parse` detects. BCApps ships 19 such
        # files (HybridGP GP tables); read as UTF-8, each is one whole-file ERROR.
        data = data.decode("utf-16").encode("utf-8")
    category, node = classify(_PARSER.parse(data))
    return label, category, node and _where(node)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", action="append", default=[], help="recurse into *.al (repeatable)")
    ap.add_argument("--corpus-fixtures", action="store_true",
                    help="every test/corpus case except tools/deliberate-negatives.txt")
    ap.add_argument("--lib", help="use this compiled parser instead of building al.dll")
    ap.add_argument("--jobs", type=int, help="worker processes (default: CPU count, but "
                    "inputs under 500 run in-process)")
    args = ap.parse_args(argv)
    if not args.root and not args.corpus_fixtures:
        ap.error("give --root DIR and/or --corpus-fixtures")

    t0 = time.perf_counter()
    try:
        inputs = _inputs(args.root, args.corpus_fixtures)
        lib_path, parser = _parser(args.lib)
    except CannotRun as e:
        print(f"has_error_sweep: CANNOT RUN: {e}", file=sys.stderr)
        return 2

    counts = {"clean": 0, "visible": 0, "hidden-only": 0}
    jobs = args.jobs or (1 if len(inputs) < 500 else os.cpu_count() or 1)
    _init(parser)
    # Workers load the same library the parent just built or was given.
    with (ProcessPoolExecutor(jobs, initializer=_init, initargs=(lib_path,)) if jobs > 1
          else contextlib.nullcontext()) as pool:
        results = pool.map(_check, inputs, chunksize=64) if pool else map(_check, inputs)
        for label, category, where in results:
            counts[category] += 1
            if where:
                print(f"{category}\t{label}\t{where}")

    print(f"has_error_sweep: files={len(inputs)} clean={counts['clean']} "
          f"visible={counts['visible']} hidden-only={counts['hidden-only']} "
          f"({time.perf_counter() - t0:.1f}s)")
    return 0 if counts["clean"] == len(inputs) else 1


if __name__ == "__main__":
    sys.exit(main())
