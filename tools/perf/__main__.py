"""python -m tools.perf baseline [--corpus LABEL ...] [--out DIR]
   python -m tools.perf native|wasm|incremental [--corpus LABEL ...] [--out DIR]
   python -m tools.perf build [--out DIR]
   python -m tools.perf oracle [--corpus LABEL ...] [--no-full] [--out DIR]
   python -m tools.perf compare OLD.json NEW.json
   python -m tools.perf render RESULT.json [--doc PATH]

Performance and resource baselines (roadmap A5). `baseline` runs every group and, with the
default --out, writes docs/perf/baseline-<yyyy-mm-dd>.json and regenerates
docs/performance-baselines.md from it. A single group writes
tools/perf/reports/<group>-<timestamp>.json. Exit: 0 done; 1 an incremental/fresh mismatch;
2 could not run. See docs/performance-baselines.md."""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

from tools.perf import common, report

# `build` first: it runs `tree-sitter generate`, and a src/ it changed must be known before
# anything is measured against it.
GROUPS = ("build", "native", "wasm", "incremental", "oracle")
PARTIAL = common.REPO / "tools" / "perf" / "reports" / "partial.json"
BASELINE_DIR = common.REPO / "docs" / "perf"
DOC = common.REPO / "docs" / "performance-baselines.md"


def _now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def measure(groups, labels, full_oracle=True):
    warnings = []
    orig_warn = common.warn

    def warn(msg):
        warnings.append(msg)
        orig_warn(msg)
    common.warn = warn
    try:
        result = {"schema": 1, "command": "python -m tools.perf " + " ".join(sys.argv[1:]),
                  "started": _now(), "env": common.environment(labels), "groups": {}}
        g = result["groups"]
        for name in groups:
            common.log(f"=== {name} ===")
            # Per group, not only at the start: a disturbance mid-run shows up here (the first
            # baseline's native passes ran ~20% slow with a clean start reading).
            load = result["env"].setdefault("load_before_group", {})[name] = common.machine_load()
            if load["busy"]:
                common.warn(f"machine is busy before {name}: CPU {load['cpu_percent_2s']}% over 2 s")
            if name == "native":
                from tools.perf import native
                g[name] = native.measure(labels)
            elif name == "wasm":
                from tools.perf import wasm
                errs = ({f for c in labels for f in g["native"]["corpora"][c]["has_error_files"]}
                        if "native" in g else None)
                g[name] = wasm.measure(labels, errs)
            elif name == "incremental":
                from tools.perf import incremental
                g[name] = incremental.measure(labels, report_dir=common.REPO / "tools" / "perf" / "reports")
            elif name == "build":
                from tools.perf import procs
                g[name] = procs.build()
            elif name == "oracle":
                from tools.perf import procs
                g[name] = procs.oracle(labels, full_oracle)
            # A checkpoint only, so a late failure does not lose an hour. It is never a
            # result: the committed baseline comes from one complete run.
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
    c = sub.add_parser("compare")
    c.add_argument("old")
    c.add_argument("new")
    r = sub.add_parser("render")
    r.add_argument("result")
    r.add_argument("--doc", default=str(DOC))
    b = sub.add_parser("_build-inner")      # procs.build() runs this inside one ts-lock
    b.add_argument("out")
    args = ap.parse_args(argv)

    if args.cmd == "compare":
        old, new = (json.loads(Path(p).read_text(encoding="utf-8")) for p in (args.old, args.new))
        print("\n".join(report.compare(old, new)))
        return 0
    if args.cmd == "render":
        return _render(Path(args.result), Path(args.doc))
    if args.cmd == "_build-inner":
        from tools.perf import procs
        procs.build_inner(args.out)
        return 0

    labels = tuple(args.corpus or common.LABELS)
    groups = GROUPS if args.cmd == "baseline" else (args.cmd,)
    result = measure(groups, labels, not getattr(args, "no_full", False))
    stamp = datetime.date.today().isoformat()
    if args.cmd == "baseline":
        out = Path(args.out) if args.out else BASELINE_DIR
        path = out / f"baseline-{stamp}.json"
    else:
        out = Path(args.out) if args.out else common.REPO / "tools" / "perf" / "reports"
        path = out / f"{args.cmd}-{datetime.datetime.now():%Y-%m-%d-%H%M%S}.json"
    out.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8", newline="\n")
    common.log(f"wrote {path}")
    if args.cmd == "baseline" and not args.out:
        _render(path, DOC)
    mism = result["groups"].get("incremental", {}).get("mismatches", 0)
    if mism:
        print(f"perf: {mism} incremental/fresh mismatches (exit 1); see {path}", file=sys.stderr)
    return 1 if mism else 0


def _render(path, doc):
    result = json.loads(path.read_text(encoding="utf-8"))
    try:
        rel = path.resolve().relative_to(common.REPO).as_posix()
    except ValueError:
        rel = str(path)
    doc.write_text(report.render(result, rel), encoding="utf-8", newline="\n")
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
