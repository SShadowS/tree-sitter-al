"""python -m tools.config_oracle run --tier quick|resolve|full [--root PATH ...] [--workers N] [--report DIR]
   python -m tools.config_oracle replay"""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import traceback
from pathlib import Path

from tools.config_oracle import fixtures, runner

REPO = Path(__file__).resolve().parents[2]
CLASSES = REPO / "tools" / "config_oracle" / "fixture-classes.tsv"


def _sha(paths):
    h = hashlib.sha256()
    for p in paths:
        h.update(p.read_bytes())
    return h.hexdigest()[:16]


def _git_head(path):
    r = subprocess.run(["git", "-C", str(path), "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
    return r.stdout.strip() or "not-a-git-repo"


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m tools.config_oracle")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--tier", choices=["quick", "resolve", "full"], required=True)
    r.add_argument("--root", action="append", default=[])
    r.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    r.add_argument("--report", default=str(REPO / "tools" / "config_oracle" / "reports"))
    sub.add_parser("replay", help="historical-defect replays (spec section 5)")
    args = ap.parse_args(argv)
    if args.cmd == "replay":
        from tools.config_oracle import replay
        return replay.main()
    try:
        return _run(args)
    except Exception:  # noqa: BLE001 -- anything short of a completed run is "could not run"
        traceback.print_exc()
        return 2


def _run(args):
    grammar = [REPO / "grammar.js", REPO / "src" / "scanner.c", REPO / "src" / "parser.c",
               *sorted((REPO / "src").rglob("*.h"))]
    header = {"grammar": _sha(grammar),
              "tier": args.tier}
    classes = {}
    if args.tier == "quick":
        inputs = [(c.id, c.source) for c in fixtures.extract(REPO / "test" / "corpus")]
        classes = fixtures.load_classes(CLASSES)
        mode = "full"
    else:
        if not args.root:
            print(f"--tier {args.tier} needs at least one --root", file=sys.stderr)
            return 2
        roots = [Path(p) for p in args.root]
        missing = [p for p in roots if not p.is_dir()]
        if missing:
            print("corpus missing: " + ", ".join(map(str, missing)), file=sys.stderr)
            return 2
        inputs = []
        for root in roots:
            header[f"corpus {root}"] = _git_head(root)
            inputs += [(str(p), p.read_bytes()) for p in sorted(root.rglob("*.al"))]
        mode = args.tier
    summary = runner.run(inputs, None, args.workers, mode, classes)
    runner.write_report(summary, Path(args.report), header)
    print((Path(args.report) / "summary.md").read_text(encoding="utf-8"))
    return summary.exit_code


if __name__ == "__main__":
    sys.exit(main())
