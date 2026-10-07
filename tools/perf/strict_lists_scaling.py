"""B7b-1 candidate-only scaling benchmark (spec 2026-10-07 section 7).

    python -m tools.perf.strict_lists_scaling --lib PATH.dll [--quick] [--md]

Repaired inputs have no main-branch tree to compare with (`tools.perf ab` refuses differing trees), so this checks
the branch library alone: per strict conditional list family it generates synthetic files growing in
  * list length: a list of N items, each after the first in its own `#if X ... #endif` group, N = 10 ... 10,240;
  * nesting depth: 200 nests of depth D (`#if X , b #if X , b ... #endif ... #endif`) in one list, D = 1 ... 20;
and, for var names, the empty-group run before a declaration that forks GLR (Task 11 review), N = 10 ... 10,240.
Every input must parse without an error. Pass criteria, per series:
  * near-linear time: the time ratio per doubling (x = N or D) stays under RATIO_LIMIT = 2.5, measured two ways:
    fitted, 2 ** (least-squares slope of log2 t over log2 x, every point), and at the LAST doubling step, the largest
    and least noisy inputs, where pathological GLR growth would show first. The worst single step is reported but
    does not gate: on this shared machine (load drift ~30%) a sub-millisecond step can exceed 2.5 by noise alone.
    Each time is the per-parse time of the fastest of REPEATS timed batches, a batch repeating the input for about
    BATCH_SECONDS;
  * memory: the resident-set growth while the largest tree of the series is alive stays under MEMORY_LIMIT, and the
    process peak working set (Windows) or max RSS stays under PEAK_LIMIT at the end.
Exit 0 all pass, 1 a criterion failed, 2 could not run. --quick stops the length series at 1,280 (a smoke run).
--md prints the result table as Markdown."""
import argparse
import math
import statistics
import sys
import time
from pathlib import Path

RATIO_LIMIT = 2.5
MEMORY_LIMIT = 256 * 2**20     # resident growth with the largest tree of one series alive
PEAK_LIMIT = 1024 * 2**20      # whole-process peak at the end of the run
REPEATS = 5
BATCH_SECONDS = 0.02           # a timed batch repeats a small input until it lasts about this long
LENGTHS = [10 * 2**k for k in range(11)]          # 10 ... 10,240
DEPTHS = [1, 2, 4, 8, 16, 20]
DEPTH_COPIES = 200

# family -> (host template, list interior head, atom generator); %s is the list interior
FAMILIES = {
    "implements": (b"codeunit 50100 C implements %s\n{\n}\n", b"I0", lambda i: b"I%d" % i),
    "key-fields": (b"table 50100 T\n{\n    keys\n    {\n        key(PK; %s) { }\n    }\n}\n", b"F0", lambda i: b"F%d" % i),
    "fieldgroup-fields": (b"table 50100 T\n{\n    fieldgroups\n    {\n        fieldgroup(DropDown; %s) { }\n    }\n}\n",
                          b"F0", lambda i: b"F%d" % i),
    "addlast-fields": (b"tableextension 50110 TE extends T\n{\n    fieldgroups\n    {\n        addlast(DropDown; %s) { }\n"
                       b"    }\n}\n", b"F0", lambda i: b"F%d" % i),
    "sorting": (b"page 50100 P\n{\n    SourceTableView = sorting(%s);\n}\n", b"F0", lambda i: b"F%d" % i),
    "order-by": (b"query 50105 Q\n{\n    OrderBy = ascending(%s);\n}\n", b"F0", lambda i: b"F%d" % i),
    "move": (b"pageextension 50113 PE extends PG\n{\n    actions\n    {\n        moveafter(A0; %s)\n    }\n}\n",
             b"A1", lambda i: b"A%d" % (i + 1)),
    "array-dimensions": (b"codeunit 50100 C\n{\n    var\n        A: array[%s] of Integer;\n}\n", b"1",
                         lambda i: b"%d" % (i + 1)),
    "attribute-arguments": (b"codeunit 50100 C\n{\n    [Foo(%s)]\n    procedure P()\n    begin\n    end;\n}\n", b"0",
                            lambda i: b"%d" % i),
    "var-names": (b"codeunit 50100 C\n{\n    var\n        %s: Integer;\n}\n", b"V0", lambda i: b"V%d" % i),
    "var-names-attributed": (b"codeunit 50100 C\n{\n    var\n        [NonDebuggable]\n        %s: Integer;\n}\n", b"V0",
                             lambda i: b"V%d" % i),
}


def length_source(family, n):
    host, head, atom = FAMILIES[family]
    return host % (head + b"".join(b"\n#if X\n, " + atom(i) + b"\n#endif" for i in range(1, n)) + b"\n")


def depth_source(family, d):
    host, head, atom = FAMILIES[family]
    nest = b"".join(b"\n#if X\n, " + atom(k) for k in range(1, d + 1)) + b"\n#endif" * d
    return host % (head + nest * DEPTH_COPIES + b"\n")


def empty_run_source(n):
    """n empty groups before a declaration in a var section: each could open a name list or stand alone (GLR)."""
    return b"codeunit 50100 C\n{\n    var\n" + b"#if X\n#endif\n" * n + b"        A: Integer;\n}\n"


def series():
    """-> [(family, axis, [x], source(x))]"""
    out = []
    for f in FAMILIES:
        out.append((f, "length", LENGTHS, lambda n, f=f: length_source(f, n)))
        out.append((f, "depth", DEPTHS, lambda d, f=f: depth_source(f, d)))
    out.append(("var-names", "empty-run", LENGTHS, empty_run_source))
    return out


def _rss():
    import psutil
    return psutil.Process().memory_info().rss


def _peak():
    import psutil
    m = psutil.Process().memory_info()
    return getattr(m, "peak_wset", None) or m.rss


def measure(parser, xs, make):
    """-> ([(x, bytes, seconds)], resident growth with the largest tree alive, error x or None)"""
    rows, keep, base = [], None, _rss()
    for x in xs:
        src = make(x)
        t0 = time.perf_counter()
        tree = parser.parse(src)
        k = max(1, int(BATCH_SECONDS / max(time.perf_counter() - t0, 1e-6)))   # parses per timed batch
        best = None
        for _ in range(REPEATS):
            t0 = time.perf_counter()
            for _ in range(k):
                tree = parser.parse(src)
            dt = (time.perf_counter() - t0) / k
            best = dt if best is None else min(best, dt)
        if tree.root_node.has_error:
            return rows, 0, x
        rows.append((x, len(src), best))
        keep = tree
    grown = _rss() - base
    del keep
    return rows, grown, None


def ratios(rows):
    """-> [(x, t(2x)/t(x))] over the doubling steps of a series."""
    t = {x: s for x, _, s in rows}
    return [(x, t[2 * x] / t[x]) for x in t if 2 * x in t]


def fitted(rows):
    """-> 2 ** the least-squares slope of log2 t over log2 x: the time ratio per doubling over the whole series."""
    if len(rows) < 2:
        return 0.0
    slope, _ = statistics.linear_regression([math.log2(x) for x, _, _ in rows], [math.log2(s) for _, _, s in rows])
    return 2 ** slope


def run(lib, quick=False):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.query_coverage import loader
    parser = loader.make_parser(loader.load_language(Path(lib)))
    results, ok = [], True
    for family, axis, xs, make in series():
        if quick and axis != "depth":
            xs = [x for x in xs if x <= 1280]
        rows, grown, err = measure(parser, xs, make)
        rs = ratios(rows)
        worst = max((r for _, r in rs), default=0.0)
        fit, last = fitted(rows), (rs[-1][1] if rs else 0.0)
        passed = err is None and fit < RATIO_LIMIT and last < RATIO_LIMIT and grown < MEMORY_LIMIT
        ok &= passed
        results.append({"family": family, "axis": axis, "rows": rows, "ratios": rs, "worst": worst, "fit": fit, "last": last,
                        "grown": grown, "error_at": err, "pass": passed})
    peak = _peak()
    ok &= peak < PEAK_LIMIT
    return results, peak, ok


def render(results, peak, md):
    lines = []
    if md:
        lines += ["| family | axis | largest x | bytes | time (ms) | fitted ratio per doubling | last step | worst step "
                  "(info) | RSS growth (MiB) | pass |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        x, nbytes, s = r["rows"][-1] if r["rows"] else (r["error_at"], 0, 0)
        cells = [r["family"], r["axis"], x, nbytes, f"{s * 1000:.2f}", f"{r['fit']:.2f}", f"{r['last']:.2f}",
                 f"{r['worst']:.2f}",
                 f"{r['grown'] / 2**20:.1f}",
                 "yes" if r["pass"] else ("ERROR at %s" % r["error_at"] if r["error_at"] else "NO")]
        lines.append("| " + " | ".join(map(str, cells)) + " |" if md else "\t".join(map(str, cells)))
    lines.append(f"process peak {peak / 2**20:.0f} MiB (limit {PEAK_LIMIT // 2**20} MiB); ratio limit {RATIO_LIMIT}, "
                 f"RSS growth limit {MEMORY_LIMIT // 2**20} MiB per series")
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(prog="tools.perf.strict_lists_scaling")
    p.add_argument("--lib", required=True, help="the branch library (a tree-sitter build --output DLL)")
    p.add_argument("--quick", action="store_true")
    p.add_argument("--md", action="store_true")
    a = p.parse_args(argv)
    if not Path(a.lib).is_file():
        print(f"cannot run: no library {a.lib}", file=sys.stderr)
        return 2
    results, peak, ok = run(a.lib, a.quick)
    print(render(results, peak, a.md))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
