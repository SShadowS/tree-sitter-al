"""python -m tools.perf baseline [--corpus LABEL ...] [--groups G,G] [--out DIR]
   python -m tools.perf native [--cc zig] [--corpus LABEL ...] [--out DIR]
   python -m tools.perf wasm|incremental [--corpus LABEL ...] [--out DIR]
   python -m tools.perf build [--out DIR]
   python -m tools.perf oracle [--corpus LABEL ...] [--no-full] [--out DIR]
   python -m tools.perf compare OLD.json NEW.json
   python -m tools.perf merge BASE.json NEW.json      # replace BASE's groups with NEW's
   python -m tools.perf render RESULT.json [--doc PATH]

Performance and resource baselines (roadmap A5). `baseline` over every group and corpus
writes docs/perf/baseline-<yyyy-mm-dd>.json and regenerates docs/performance-baselines.md
from it; a subset of groups or corpora needs --out, so it can never overwrite the committed
baseline. A single group writes tools/perf/reports/<group>-<timestamp>.json. Every group
records its own corpus set, times, a start snapshot and continuous outside-CPU sampling
(tools/perf/load.py). Exit: 0 done; 1 an incremental/fresh mismatch; 2 could not run."""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

from tools.perf import common, report
from tools.perf import load as loadmon

# `build` first: it runs `tree-sitter generate`, and a src/ it changed must be known before
# anything is measured against it.
GROUPS = ("build", "native", "wasm", "incremental", "oracle")
PARTIAL = common.REPO / "tools" / "perf" / "reports" / "partial.json"
BASELINE_DIR = common.REPO / "docs" / "perf"
DOC = common.REPO / "docs" / "performance-baselines.md"


def _now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def measure(groups, labels, full_oracle=True, cc=None, checkpoint=False, ab_args=None):
    from tools.perf import procs
    warnings = []
    orig_warn = common.warn

    def warn(msg):
        warnings.append(msg)
        orig_warn(msg)
    common.warn = warn
    try:
        result = {"schema": 2, "command": "python -m tools.perf " + " ".join(sys.argv[1:]),
                  "started": _now(), "env": common.environment(labels), "groups": {}}
        # The compiler and flags behind al.dll, from a real `tree-sitter build -v` (procs).
        result["env"]["native_library"] = procs.compiler_probe()
        g = result["groups"]
        for name in groups:
            common.log(f"=== {name} ===")
            meta = {"corpora": list(labels), "command": result["command"], "started": _now(),
                    "start_snapshot": loadmon.snapshot(), "library": result["env"]["native_library"]}
            # Sampled for the whole group, not read once at the start: the first baseline's
            # discarded run had a clean start reading and 20% slow native passes.
            monitor = loadmon.LoadMonitor()
            monitor.start()
            try:
                if name == "native":
                    from tools.perf import native
                    lib = None
                    if cc == "zig":
                        # Its own group key, so a merge puts it BESIDE the MSVC figures.
                        lib, meta["library"] = procs.zig_library()
                        name = "native_zig"
                    g[name] = native.measure(labels, lib=lib)
                elif name == "wasm":
                    from tools.perf import wasm
                    errs = ({f for c in labels for f in g["native"]["corpora"][c]["has_error_files"]}
                            if "native" in g else None)
                    g[name] = wasm.measure(labels, errs)
                    meta["library"] = "tree-sitter-al.wasm"
                elif name == "incremental":
                    from tools.perf import incremental
                    g[name] = incremental.measure(labels, report_dir=common.REPO / "tools" / "perf" / "reports")
                elif name == "build":
                    g[name] = procs.build()
                elif name == "oracle":
                    g[name] = procs.oracle(labels, full_oracle)
                elif name == "ab":
                    from tools.perf import ab
                    g[name] = ab.run(*ab_args[:2], labels, ab_args[2])
                    meta["library"] = "two libraries, see lib_a / lib_b"
            finally:
                meta["load"] = monitor.stop()
            meta["finished"] = _now()
            g[name]["meta"] = meta
            if meta["load"].get("flagged"):
                common.warn(f"{name}: outside CPU mean {meta['load']['outside_cores_mean']} / max "
                            f"{meta['load']['outside_cores_max']} cores exceeded a threshold "
                            f"({loadmon.OUTSIDE_MEAN_CORES} mean, {loadmon.OUTSIDE_MAX_CORES} max)")
            if checkpoint:
                # A checkpoint only, so a late failure does not lose an hour. It is never a
                # result: the committed baseline comes from one complete run. `baseline` only,
                # so a single-group run cannot overwrite a running baseline's checkpoint.
                PARTIAL.parent.mkdir(parents=True, exist_ok=True)
                PARTIAL.write_text(json.dumps(result, indent=1), encoding="utf-8")
        result["env"]["load_at_end"] = common.machine_load()
        result["finished"] = _now()
        result["warnings"] = warnings
        return result
    finally:
        common.warn = orig_warn


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m tools.perf")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("baseline", *GROUPS):
        p = sub.add_parser(name)
        p.add_argument("--corpus", action="append", choices=common.LABELS)
        p.add_argument("--out")
        if name in ("baseline", "oracle"):
            p.add_argument("--no-full", action="store_true", help="skip the oracle's full tier")
        if name == "baseline":
            p.add_argument("--groups", help="comma-separated subset of " + ",".join(GROUPS))
        if name == "native":
            p.add_argument("--cc", choices=["zig"], help="time a clang -O2 build (zig cc) instead of al.dll")
    ab = sub.add_parser("ab", help="same-session interleaved A/B of two native libraries")
    ab.add_argument("--lib-a", required=True)
    ab.add_argument("--lib-b", required=True)
    ab.add_argument("--corpus", action="append", choices=common.LABELS)
    ab.add_argument("--rounds", type=int, default=8)
    ab.add_argument("--out")
    c = sub.add_parser("compare")
    c.add_argument("old")
    c.add_argument("new")
    c.add_argument("--floor", type=float, help="noise floor for `!` as a fraction of the old median "
                   "(default 0.05 single-threaded, 0.10 parallel)")
    m = sub.add_parser("merge")
    m.add_argument("base")
    m.add_argument("new", nargs="?")
    m.add_argument("--drop", action="append", default=[], help="remove a group from BASE (recorded)")
    r = sub.add_parser("render")
    r.add_argument("result")
    r.add_argument("--doc", default=str(DOC))
    b = sub.add_parser("_build-inner")      # procs.build() runs this inside one ts-lock
    b.add_argument("out")
    args = ap.parse_args(argv)

    if args.cmd == "compare":
        old, new = (json.loads(Path(p).read_text(encoding="utf-8")) for p in (args.old, args.new))
        print("\n".join(report.compare(old, new, args.floor)))
        return 0
    if args.cmd == "render":
        return _render(Path(args.result), Path(args.doc))
    if args.cmd == "merge":
        base = json.loads(Path(args.base).read_text(encoding="utf-8"))
        for g in args.drop:
            base["groups"].pop(g)
            base.setdefault("merges", []).append({"dropped": g, "at": _now()})
            common.log(f"dropped {g} from {args.base}")
        if args.new:
            new = json.loads(Path(args.new).read_text(encoding="utf-8"))
            base = report.merge(base, new, Path(args.new).name)
            common.log(f"merged {', '.join(new['groups'])} from {args.new} into {args.base}")
        _write(Path(args.base), base)
        return 0
    if args.cmd == "_build-inner":
        from tools.perf import procs
        procs.build_inner(args.out)
        return 0

    if args.cmd == "ab":
        labels = tuple(args.corpus or ("dc",))
        result = measure(("ab",), labels, ab_args=(args.lib_a, args.lib_b, args.rounds))
        out = Path(args.out) if args.out else common.REPO / "tools" / "perf" / "reports"
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"ab-{datetime.datetime.now():%Y-%m-%d-%H%M%S}.json"
        _write(path, result)
        r = result["groups"]["ab"]
        if not r["trees_identical"]:
            print(f"perf: ab: the libraries build different trees ({len(r['differing_files'])}+ files); see {path}")
            return 1
        q = r["ratio_a_over_b"]
        print(f"perf: ab over {'+'.join(labels)}, {r['rounds']} rounds {r['order']}, pinned {r['pin']}:\n"
              f"  A {r['lib_a']['path']}: median {stats_median(r['seconds']['A']):.3f} s\n"
              f"  B {r['lib_b']['path']}: median {stats_median(r['seconds']['B']):.3f} s\n"
              f"  time A / time B: median {q['median']:.3f} (min {q['min']:.3f}, max {q['max']:.3f}; "
              f"95% CI of the median {q['ci95_median'][0]:.3f}-{q['ci95_median'][1]:.3f})\n  wrote {path}")
        return 0
    labels = tuple(args.corpus or common.LABELS)
    if args.cmd == "baseline":
        groups = tuple(x for x in (args.groups or ",".join(GROUPS)).split(",") if x)
        unknown = set(groups) - set(GROUPS)
        if unknown:
            ap.error(f"unknown groups: {', '.join(sorted(unknown))}")
        if (set(labels) != set(common.LABELS) or set(groups) != set(GROUPS)) and not args.out:
            ap.error("a baseline over a subset of corpora or groups needs --out: without it, it "
                     "would overwrite the committed docs/perf baseline and the doc")
    else:
        groups = (args.cmd,)
    result = measure(groups, labels, not getattr(args, "no_full", False), getattr(args, "cc", None),
                     checkpoint=args.cmd == "baseline")
    stamp = datetime.date.today().isoformat()
    if args.cmd == "baseline":
        out = Path(args.out) if args.out else BASELINE_DIR
        path = out / f"baseline-{stamp}.json"
    else:
        out = Path(args.out) if args.out else common.REPO / "tools" / "perf" / "reports"
        path = out / f"{args.cmd}-{datetime.datetime.now():%Y-%m-%d-%H%M%S}.json"
    out.mkdir(parents=True, exist_ok=True)
    _write(path, result)
    common.log(f"wrote {path}")
    if args.cmd == "baseline" and not args.out:
        _render(path, DOC)
    mism = result["groups"].get("incremental", {}).get("mismatches", 0)
    if mism:
        print(f"perf: {mism} incremental/fresh mismatches (exit 1); see {path}", file=sys.stderr)
    return 1 if mism else 0


def stats_median(xs):
    from tools.perf import stats
    return stats.median(xs)


def _write(path, result):
    path.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8", newline="\n")


def _render(path, doc):
    result = json.loads(path.read_text(encoding="utf-8"))
    try:
        rel = path.resolve().relative_to(common.REPO).as_posix()
    except ValueError:
        rel = str(path)
    notes = path.with_suffix(".notes.md")
    doc.write_text(report.render(result, rel, notes.read_text(encoding="utf-8") if notes.is_file() else None),
                   encoding="utf-8", newline="\n")
    common.log(f"rendered {doc}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001 -- anything short of a completed run is "could not run"
        import traceback
        traceback.print_exc()
        print("perf: could not run (exit 2)", file=sys.stderr)
        sys.exit(2)
