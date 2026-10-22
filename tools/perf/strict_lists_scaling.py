"""B7b-1 candidate-only scaling benchmark (spec 2026-10-07 section 7).

    python -m tools.perf.strict_lists_scaling --lib PATH.dll [--quick] [--md]

Repaired inputs have no main-branch tree to compare with (`tools.perf ab` refuses differing trees), so this checks
the branch library alone: per strict conditional list family it generates synthetic files growing in
  * list length: a list of N items, each after the first in its own `#if X ... #endif` group, N = 10 ... 10,240;
  * nesting depth: 200 nests of depth D (`#if X , b #if X , b ... #endif ... #endif`) in one list, D = 1 ... 20;
and, for var names, the empty-group run before a declaration that forks GLR (Task 11 review), N = 10 ... 10,240.
B7b-3 (spec 2026-10-08 section 8.2) adds case-group series (lone `;` groups, nested empty decorations, mixed arms)
and move-group series (spanning, nested) on the same grid and criteria; each of their inputs runs in its own
killable worker process with a WORKER_SECONDS = 10 ceiling, and the worker's peak is held to PEAK_LIMIT too.
B7b-2 (spec 2026-10-20 section 8.5) adds expression-tail series (argument_tails, root_tails, nested_tails) the same
way, and Phase B root_slots/<root> (N consecutive groups at each new region root) and ternary_parts (an else-chained
ternary of N parts, a tail on each condition and then value) and ternary_condition_consecutive (one condition, N
consecutive groups), and Phase C operand_groups, nested_operand_groups and mixed (prefix, operand group and tail per
part); SCALING_EXCEPTIONS names the series that are measured and reported but cannot fail the run
(deferred items 52 and 53).
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


# --- B7b-3 (spec 2026-10-08 section 8.2): case groups and move groups, same grid and limits ----------------------
# Each input of these series runs in its own killable worker process with a WORKER_SECONDS ceiling.
WORKER_SECONDS = 10
CASE_HOST = b"codeunit 50100 C\n{\n    procedure M()\n    begin\ncase I of\n%send;\n    end;\n}\n"
MOVE_HOST = b"pageextension 50113 PE extends PG\n{\n    actions\n    {\n%s    }\n}\n"


def _nest(d, inner, arm_else=None):
    """d nested `#if X` groups around `inner`; with arm_else every level also gets an `#else` arm holding it."""
    if d == 0:
        return inner
    return (b"#if X\n" + _nest(d - 1, inner, arm_else) + (b"#else\n" + arm_else if arm_else is not None else b"")
            + b"#endif\n")


def case_lone_semi(n):
    """n branches, each but the last followed by a lone-`;` group (spec 4.1: the group's `;` is the separator)."""
    return CASE_HOST % (b"".join(b"%d: Bar\n#if X\n;\n#endif\n" % i for i in range(1, n)) + b"%d: Bar;\n" % n)


def case_lone_semi_nested(d):
    """DEPTH_COPIES branches separated by `;` groups nested d deep, every level with a `;` #else arm."""
    sep = _nest(d, b";\n", b";\n")
    return CASE_HOST % (b"".join(b"%d: Bar\n" % i + sep for i in range(1, DEPTH_COPIES)) + b"%d: Bar;\n" % DEPTH_COPIES)


def case_decoration(n):
    """n branches, each with an empty group between its body and its own `;` (decoration, spec 4.2.2)."""
    return CASE_HOST % b"".join(b"%d: Bar\n#if X\n#endif\n;\n" % i for i in range(1, n + 1))


def case_decoration_nested(d):
    """DEPTH_COPIES branches, each with an empty decoration nested d deep before its `;`."""
    return CASE_HOST % b"".join(b"%d: Bar\n" % i + _nest(d, b"") + b";\n" for i in range(1, DEPTH_COPIES + 1))


def case_mixed_arms(n):
    """n groups whose arms each hold a `;` and a branch (Phase 0 group-semi-and-branch-else), after one branch; each
    group's `;` closes the branch before it, and the last group's branch ends the run unterminated."""
    return CASE_HOST % (b"0: Bar\n" + b"".join(b"#if X\n;\n%d: Bar\n#else\n;\n%d: Foo\n#endif\n" % (i, i)
                                                for i in range(1, n + 1)))


def move_spanning(n):
    """One move whose route-3 group spans the header: target, `;` and n elements in every arm."""
    els = b", ".join(b"A%d" % i for i in range(1, n + 1))
    return MOVE_HOST % (b"        moveafter(\n#if X\nA0; " + els + b"\n#else\nB0; " + els + b"\n#endif\n)\n")


def move_nested(d):
    """DEPTH_COPIES moves, each taking its `;` from route-2 groups nested d deep, every level with a `;` #else arm."""
    one = b"        moveafter(\nA0\n" + _nest(d, b";\n", b";\n") + b"A1\n)\n"
    return MOVE_HOST % (one * DEPTH_COPIES)


def b7b3_series():
    """-> [(family, axis, [x], source(x))], each input measured in a worker (measure_isolated)."""
    return [("case-lone-semi", "length", LENGTHS, case_lone_semi),
            ("case-lone-semi", "depth", DEPTHS, case_lone_semi_nested),
            ("case-decoration", "length", LENGTHS, case_decoration),
            ("case-decoration", "depth", DEPTHS, case_decoration_nested),
            ("case-mixed-arms", "length", LENGTHS, case_mixed_arms),
            ("move-spanning", "length", LENGTHS, move_spanning),
            ("move-nested", "depth", DEPTHS, move_nested)]


# --- B7b-2 (spec 2026-10-20 section 8.5): expression tails, same grid and limits, each input in a worker ---------
CODE_HOST = b"codeunit 50100 C\n{\n    procedure M()\n    begin\n%s    end;\n}\n"
# Measured and reported, but a failure does not fail the run: N consecutive groups at a root after which a host group
# can start (a statement, argument or list-elements group) parse in quadratic time, a known limit by user decision
# (docs/deferred-work.md item 52; the corpora's longest back-to-back #if run is 3). Pinned by
# tests/test_strict_lists_scaling.py so the list cannot grow silently.
SCALING_EXCEPTIONS = {(f, "length"): "deferred-work item 52"
                      for f in ("argument_tails", "root_tails", "root_slots/repeat_until", "root_slots/range_left",
                                "root_slots/list_element", "root_slots/split_call_argument",
                                "ternary_condition_consecutive", "mixed")}
# A tail on a nested ternary's condition re-reduces the open ternary chain: quadratic in the chain length, a different
# cause, known limit (docs/deferred-work.md item 53; no chained ternary in the four corpora).
SCALING_EXCEPTIONS[("ternary_parts", "length")] = "deferred-work item 53"


def argument_tails(n):
    """`Foo(1 #if X +2 #endif ... #if X +N #endif)`: N-1 consecutive tail groups continuing one argument."""
    return CODE_HOST % (b"r := Foo(1" + b"".join(b"\n#if X\n+%d\n#endif" % i for i in range(2, n + 1)) + b"\n);\n")


def root_tails(n):
    """`r := 1` followed by N consecutive tail groups."""
    return CODE_HOST % (b"r := 1" + b"".join(b"\n#if X\n+%d\n#endif" % i for i in range(1, n + 1)) + b"\n;\n")


def nested_tails(d):
    """DEPTH_COPIES assignments, each with tails nested d deep (`r := 1 #if X + 1 #if X + 1 ... #endif #endif;`)."""
    one = b"r := 1\n" + b"#if X\n+ 1\n" * d + b"#endif\n" * d + b";\n"
    return CODE_HOST % (one * DEPTH_COPIES)


# Phase B (spec 5.1 table): each new region root as a statement template; %s takes N consecutive tail groups.
ROOT_SLOTS = {
    "repeat_until": b"repeat\nFoo();\nuntil C%s\n;\n",
    "case_expression": b"case i%s\nof\n1:\nFoo();\nend;\n",
    "split_case_end": b"case i%s\nof\n1:\nFoo();\n2:\n#if Y\nFoo();\nend;\nBar();\n#else\nBar();\nend;\nFoo();\n#endif\n",
    "ternary_then": b"x := Ok ? 1%s\n: 3;\n",
    "parenthesized": b"x := (1%s\n) * 3;\n",
    "range_left": b"Ok := i in [1%s\n.. 5];\n",
    "for_start": b"for i := 1%s\nto 5 do\nFoo();\n",
    "subscript_index": b"x := Arr2[1, 2%s\n];\n",
    "list_element": b"Ok := i in [1, 2%s\n];\n",
    "with_record": b"with Recs[1]%s\ndo\nFoo();\n",
    "foreach_iterable": b"foreach i in L%s\ndo\nFoo();\n",
    "split_if_head": b"#if A\nif C%s\nthen\n#else\nif E\nthen\n#endif\nFoo();\n",
    "split_call_argument": b"#if A\nFoo(1%s\n,\n#else\nFoo(3,\n#endif\n4);\n",
}


def root_slot(name):
    """-> source(n): the root `name` of ROOT_SLOTS followed by n consecutive tail groups."""
    return lambda n: CODE_HOST % (ROOT_SLOTS[name] % b"".join(b"\n#if X\n+%d\n#endif" % i for i in range(1, n + 1)))


def ternary_parts(n):
    """An else-chained ternary of n parts, each condition and then value with its own tail (`C1 #if X and D1 #endif
    ? 1 #if X + 1 #endif : C2 ... : 0`)."""
    part = b"C%d\n#if X\nand D%d\n#endif\n? %d\n#if X\n+ %d\n#endif\n: "
    return CODE_HOST % (b"x := " + b"".join(part % (i, i, i, i) for i in range(1, n + 1)) + b"0;\n")


def ternary_condition_consecutive(n):
    """One ternary whose condition carries n consecutive tail groups (`x := C #if X and D1 #endif ... ? 1 : 0;`)."""
    return CODE_HOST % (b"x := C" + b"".join(b"\n#if X\nand D%d\n#endif" % i for i in range(1, n + 1)) + b"\n? 1 : 0;\n")


# Phase C (spec 6): operand groups, nested operand groups, and prefixes + operand groups + tails mixed in one chain.
OPERAND_GROUP = b"\n#if X\n%d\n#else\n%d\n#endif\n"


def operand_groups(n):
    """`r := G1 + G2 + ... + GN;`, each Gi a whole-operand group (`#if X i #else i #endif`)."""
    return CODE_HOST % (b"r :=" + b"+".join(OPERAND_GROUP % (i, i) for i in range(1, n + 1)) + b";\n")


def nested_operand_groups(d):
    """DEPTH_COPIES assignments, each `r := 1 + G;` with G an operand group whose #if arm nests d deep."""
    one = b"r := 1 +\n" + b"#if X\n" * d + b"1\n" + b"#else\n2\n#endif\n" * d + b";\n"
    return CODE_HOST % (one * DEPTH_COPIES)


def mixed(n):
    """`r := 1` then N parts `+ #if X i * #endif #if X i #else i #endif #if X - i #endif`: an operand prefix, an
    operand group and a tail per part."""
    part = b"+\n#if X\n%d *\n#endif\n#if X\n%d\n#else\n%d\n#endif\n#if X\n- %d\n#endif\n"
    return CODE_HOST % (b"r := 1\n" + b"".join(part % (i, i, i, i) for i in range(1, n + 1)) + b";\n")


def series_ok(passed, exception, error_kind):
    """An excepted series (SCALING_EXCEPTIONS) is waived only for the time/memory limits and the worker timeout; a parse
    error or a crash fails it like any other series."""
    return passed or (exception is not None and error_kind != "error")


def b7b2_series():
    """-> [(family, axis, [x], source(x))], each input measured in a worker (measure_isolated)."""
    return [("argument_tails", "length", LENGTHS, argument_tails),
            ("root_tails", "length", LENGTHS, root_tails),
            ("nested_tails", "depth", DEPTHS, nested_tails)] + \
        [(f"root_slots/{name}", "length", LENGTHS, root_slot(name)) for name in ROOT_SLOTS] + \
        [("ternary_parts", "length", LENGTHS, ternary_parts),
         ("ternary_condition_consecutive", "length", LENGTHS, ternary_condition_consecutive),
         ("operand_groups", "length", LENGTHS, operand_groups),
         ("nested_operand_groups", "depth", DEPTHS, nested_operand_groups),
         ("mixed", "length", LENGTHS, mixed)]


def _worker(lib, src, out):
    """One input in a fresh process: measure()'s timing protocol, the RSS growth with the tree alive, the peak."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        from tools.query_coverage import loader
        parser = loader.make_parser(loader.load_language(Path(lib)))
        base = _rss()
        t0 = time.perf_counter()
        tree = parser.parse(src)
        k = max(1, int(BATCH_SECONDS / max(time.perf_counter() - t0, 1e-6)))
        best = None
        for _ in range(REPEATS):
            t0 = time.perf_counter()
            for _ in range(k):
                tree = parser.parse(src)
            dt = (time.perf_counter() - t0) / k
            best = dt if best is None else min(best, dt)
        out.put(("ok", best, tree.root_node.has_error, _rss() - base, _peak()))
    except BaseException as e:      # reported as the series' error, never a pass
        out.put(("fail", repr(e)))


def measure_isolated(lib, xs, make, ceiling=WORKER_SECONDS, target=None):
    """-> ([(x, bytes, seconds)], max RSS growth, error x or None, max worker peak, error kind). An input that has a
    parse error or crashes (kind "error") or outlives `ceiling` seconds (its worker is killed, kind "timeout") ends
    the series at that x."""
    import multiprocessing as mp
    import queue
    ctx = mp.get_context("spawn")
    rows, grown, peak = [], 0, 0
    for x in xs:
        src = make(x)
        q = ctx.Queue()
        p = ctx.Process(target=target or _worker, args=(str(lib), src, q), daemon=True)
        p.start()
        try:
            res = q.get(timeout=ceiling)
        except queue.Empty:
            res = ("timeout",)
        p.join(1)
        if p.is_alive():
            p.kill()
            p.join()
        if res[0] != "ok" or res[2]:
            return rows, grown, x, peak, "timeout" if res[0] == "timeout" else "error"
        rows.append((x, len(src), res[1]))
        grown, peak = max(grown, res[3]), max(peak, res[4])
    return rows, grown, None, peak, None


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
    for family, axis, xs, make in b7b3_series() + b7b2_series():
        if quick and axis != "depth":
            xs = [x for x in xs if x <= 1280]
        rows, grown, err, wpeak, kind = measure_isolated(lib, xs, make)
        rs = ratios(rows)
        worst = max((r for _, r in rs), default=0.0)
        fit, last = fitted(rows), (rs[-1][1] if rs else 0.0)
        passed = (err is None and fit < RATIO_LIMIT and last < RATIO_LIMIT and grown < MEMORY_LIMIT
                  and wpeak < PEAK_LIMIT)
        exception = SCALING_EXCEPTIONS.get((family, axis))
        ok &= series_ok(passed, exception, kind)
        results.append({"family": family, "axis": axis, "rows": rows, "ratios": rs, "worst": worst, "fit": fit, "last": last,
                        "grown": grown, "error_at": err, "error_kind": kind, "pass": passed, "exception": exception})
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
                 "yes" if r["pass"] else ("%s at %s" % ("timeout" if r.get("error_kind") == "timeout" else "ERROR",
                                                       r["error_at"]) if r["error_at"] else "NO")
                 + (f" (exception: {r['exception']})" if r.get("exception") else "")]
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
