"""python -m tools.config_oracle run --tier quick|resolve|full [--root PATH ...] [--workers N] [--report DIR]
   python -m tools.config_oracle replay

Exit codes (spec section 4): 0 clean; 1 a discrepancy, representation violation, stale
entry or census problem; 2 could not run or incomplete."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import traceback
from pathlib import Path

from tools.config_oracle import fixtures, runner

REPO = Path(__file__).resolve().parents[2]
CLASSES = REPO / "tools" / "config_oracle" / "fixture-classes.tsv"

# The oracle's own self-tests (spec sections 1-3), corpus-free and about a second: the
# resolver self-test and its #elif first-match mutation, the comparator's mutations, the
# precedence table's recomposition, the representation contracts' controls, and the check
# that lowering never imports a parser (test_isolation.py). They
# exist only as pytest modules, so the quick tier runs those modules rather than a copy.
SELFTESTS = ("test_resolve.py", "test_configs.py", "test_compare.py",
             "test_precedence.py", "test_representation.py", "test_isolation.py")

PASS, FAIL = "PASS", "FAIL"


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
    try:
        if args.cmd == "replay":
            from tools.config_oracle import replay
            return replay.main()
        return _quick(args) if args.tier == "quick" else _run(args)
    except Exception:  # noqa: BLE001 -- anything short of a completed run is "could not run"
        traceback.print_exc()
        print("config-oracle: could not run (exit 2)", file=sys.stderr)
        return 2


def _header(tier):
    grammar = [REPO / "grammar.js", REPO / "src" / "scanner.c", REPO / "src" / "parser.c",
               *sorted((REPO / "src").rglob("*.h"))]
    return {"grammar": _sha(grammar), "tier": tier}


# ---- quick tier: every stage that needs no corpus ------------------------------------

def _stage_census():
    from tools.config_oracle import contracts
    node_types = json.loads((REPO / "src" / "node-types.json").read_text(encoding="utf-8"))
    problems = contracts.census(node_types)
    if problems:
        return 1, f"{FAIL} ({len(problems)} problems)", problems
    return 0, PASS, []


def _stage_selftests():
    import importlib.util
    if importlib.util.find_spec("pytest") is None:   # pytest's own exit 1 would read as a finding
        return 2, "COULD NOT RUN (pytest is not installed)", []
    tests = [str(REPO / "tools" / "config_oracle" / "tests" / t) for t in SELFTESTS]
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *tests],
                       cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace")
    tail = (r.stdout + r.stderr).strip().splitlines()
    if r.returncode == 0:
        return 0, f"{PASS} ({tail[-1].strip('= ') if tail else 'no output'})", []
    code = 1 if r.returncode == 1 else 2       # pytest: 1 = tests failed; anything else = could not run
    word = FAIL if code == 1 else "COULD NOT RUN"
    return code, f"{word} (pytest exit {r.returncode})", tail[-40:]


def _quick(args):
    """(a) registry census, (b) self-tests, (c) fixture differential. Every stage runs and
    reports whatever an earlier one found; the exit code is the worst stage's."""
    from tools.query_coverage import loader
    out = Path(args.report)
    _could_not_run(out, "quick", "the parser build, before any stage")   # replaced when a stage runs
    lib = loader.ensure_library(REPO)   # first: `generate` keeps node-types.json current for (a)
    header = _header("quick")
    stages, details = [], []
    for label, fn in (("(a) registry census", _stage_census), ("(b) self-tests", _stage_selftests)):
        try:
            code, status, lines = fn()
        except Exception:  # noqa: BLE001 -- the stage could not run; the later ones still do
            code, status, lines = 2, "COULD NOT RUN", traceback.format_exc().splitlines()
        stages.append((label, code, status))
        details += [f"{label}:", *(f"  {x}" for x in lines)] if lines else []
    summary = None
    try:
        inputs = [(c.id, c.source) for c in fixtures.extract(REPO / "test" / "corpus")]
        summary = runner.run(inputs, lib, args.workers, "full", fixtures.load_classes(CLASSES))
        c = summary.exit_code
        stages.append(("(c) fixture differential", c, PASS if c == 0 else
                       f"{FAIL if c == 1 else 'COULD NOT RUN'} (exit {c}; the counts below say why)"))
    except Exception:  # noqa: BLE001
        stages.append(("(c) fixture differential", 2, "COULD NOT RUN"))
        details += ["(c) fixture differential:", *(f"  {x}" for x in traceback.format_exc().splitlines())]
    code = 2 if any(c == 2 for _, c, _ in stages) else max(c for _, c, _ in stages)
    extra = ["## Stages", "", *(f"- stage {label}: {status}" for label, _, status in stages),
             f"- quick tier exit code: {code}", *([""] + details if details else [])]
    if summary is not None:
        runner.write_report(summary, out, header, extra)
    else:   # never leave an earlier run's summary.md in place to be read as this one's
        out.mkdir(parents=True, exist_ok=True)
        (out / "summary.md").write_text("\n".join(["# Config-oracle report", "", *extra]) + "\n",
                                        encoding="utf-8")
    print((out / "summary.md").read_text(encoding="utf-8"))
    return code


def _could_not_run(out, tier, why):
    """Overwrite summary.md first, so a run that stops early never leaves an earlier run's
    summary for Step 5e's "see summary.md" to point at."""
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.md").write_text(f"# Config-oracle report\n\n- tier: {tier}\n\n"
                                    f"**could not run (exit 2): {why}**\n", encoding="utf-8")


# ---- resolve / full tiers: per-corpus accounting --------------------------------------

def _collect(roots):
    """-> (inputs, {input id: root}, {root: .al count}), or an error message.

    Roots must not overlap: a file under two requested roots would be attributed to
    either, so equal or nested roots are rejected rather than de-duplicated."""
    res = [(r, r.resolve()) for r in roots]
    for i, (a, ra) in enumerate(res):
        for b, rb in res[i + 1:]:
            if ra == rb or ra in rb.parents or rb in ra.parents:
                return None, f"corpus roots overlap: {a} and {b} (a file would belong to both)"
    inputs, root_of, files = [], {}, {}
    for root in roots:
        paths = sorted(root.rglob("*.al"))
        if not paths:
            return None, f"corpus root has no .al files: {root}"
        files[str(root)] = len(paths)
        for p in paths:
            inputs.append((str(p), p.read_bytes()))
            root_of[str(p)] = str(root)
    return (inputs, root_of, files), None


def _run(args):
    _could_not_run(Path(args.report), args.tier, "stopped before the runner finished; see stderr")
    if not args.root:
        print(f"--tier {args.tier} needs at least one --root", file=sys.stderr)
        return 2
    roots = [Path(p) for p in args.root]
    missing = [p for p in roots if not p.is_dir()]
    if missing:
        print("corpus missing: " + ", ".join(map(str, missing)), file=sys.stderr)
        return 2
    collected, err = _collect(roots)
    if err:
        print(err, file=sys.stderr)
        return 2
    assert collected is not None      # _collect returns None only with an error message
    inputs, root_of, files = collected
    header = _header(args.tier)
    for root in roots:
        header[f"corpus {root}"] = _git_head(root)
    summary = runner.run(inputs, None, args.workers, args.tier, {})
    extra = ["## Per root", "", *runner.root_table(runner.per_root(summary, root_of, files))]
    runner.write_report(summary, Path(args.report), header, extra)
    print((Path(args.report) / "summary.md").read_text(encoding="utf-8"))
    return summary.exit_code


if __name__ == "__main__":
    sys.exit(main())
