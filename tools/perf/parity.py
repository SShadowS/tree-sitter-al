"""Tree-only parity of two native grammar libraries over whole corpora (B7b-1 gate).

    python -m tools.perf parity --lib-a A.dll --lib-b B.dll [--corpus all|LABEL ...] [--workers N]

Every `*.al` file of every requested corpus is parsed by both libraries and the complete
cursor-derived trees must be identical (`ab.trees_identical`, i.e. `incremental.rows`: every
node, type, symbol, fields, spans, has_error). No timing. Prints `files, differing` per corpus
and the differing paths. Exit 0 none differ; 1 some differ; 2 a library or corpus is missing.
Run it under `./tools/ts-lock.sh` like every parser user.

Base library (main's grammar, built without touching the working tree):

    git worktree add <TMP>/al-main main            # OUTSIDE the repo
    cd <TMP>/al-main && CC=clang-cl tree-sitter build --output <LIBS>/al-main.dll .
        # the loader's command (tools/query_coverage/loader.ensure_library): CC from
        # loader.build_env() (clang-cl when installed); parser.c + scanner.c are what it compiles
    git worktree remove <TMP>/al-main              # no --force
"""
from __future__ import annotations

import concurrent.futures as cf
import sys
from pathlib import Path

from tools.perf import ab, common

CHUNK = 200


class ParityError(RuntimeError):
    """The run could not be completed (empty corpus, worker failure): exit 2, never "differs"."""

_P = {}


def _parsers(a, b):
    if (a, b) not in _P:
        from tools.query_coverage import loader
        _P.clear()
        _P[(a, b)] = tuple(loader.make_parser(loader.load_language(Path(p))) for p in (a, b))
    return _P[(a, b)]


def _chunk(job):
    """-> [differing ids]; runs in a worker process (also called in-process for workers=1)."""
    a, b, label, root, rels = job
    pa, pb = _parsers(a, b)
    files = []
    for r in rels:
        try:
            files.append((label, r, common.source((Path(root) / r).read_bytes())))
        except Exception as e:  # noqa: BLE001
            raise ParityError(f"cannot read {label}:{r}: {e!r}") from e
    return ab.trees_identical(pa, pb, files)


def run(lib_a, lib_b, labels, workers=None, roots=None, chunk_fn=_chunk):
    """-> ({label: (files, [differing])}); raises FileNotFoundError for a missing lib/corpus, ParityError for an empty corpus or a worker failure."""
    roots = roots or common.oracle.CORPORA
    for p in (lib_a, lib_b):
        if not Path(p).is_file():
            raise FileNotFoundError(f"library {p}")
    jobs, counts = [], {}
    for label in labels:
        root = Path(roots[label])
        if not root.is_dir():
            raise FileNotFoundError(f"corpus {label}: {root}")
        rels = sorted(p.relative_to(root).as_posix() for p in root.rglob("*.al"))
        if not rels:
            raise ParityError(f"corpus {label} ({root}) has no .al files")
        counts[label] = len(rels)
        jobs += [(str(lib_a), str(lib_b), label, str(root), rels[i:i + CHUNK])
                 for i in range(0, len(rels), CHUNK)]
    workers = workers or common.DEFAULT_WORKERS
    out = {l: (counts[l], []) for l in labels}
    ex = cf.ProcessPoolExecutor(workers) if workers > 1 and chunk_fn is _chunk else None
    try:
        results = ex.map(chunk_fn, jobs) if ex else map(chunk_fn, jobs)
        it = iter(results)
        for job in jobs:
            try:
                bad = next(it)
            except ParityError:
                raise
            except Exception as e:  # noqa: BLE001 -- a broken run is not "trees differ"
                raise ParityError(f"corpus {job[2]}: {type(e).__name__}: {e}") from e
            out[job[2]][1].extend(bad)
    finally:
        if ex:
            ex.shutdown(wait=True, cancel_futures=True)
    return out


def report(out, file=None):
    """Print per-corpus counts and differing paths; -> exit code."""
    file = file or sys.stdout
    for label, (n, bad) in out.items():
        print(f"parity: {label}: {n} files, {len(bad)} differing", file=file)
        for b in bad:
            print(f"  {b}", file=file)
    return 1 if any(bad for _, bad in out.values()) else 0


def main(lib_a, lib_b, corpus, workers=None):
    labels = common.LABELS if not corpus or "all" in corpus else tuple(corpus)
    try:
        return report(run(lib_a, lib_b, labels, workers))
    except (FileNotFoundError, ParityError) as e:
        print(f"parity: cannot run: {e}", file=sys.stderr)
        return 2
