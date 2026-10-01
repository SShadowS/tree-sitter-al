"""python -m tools.config_oracle run --tier quick|resolve|full [--root PATH ...] [--workers N] [--report DIR]
   python -m tools.config_oracle replay

Exit codes (spec section 4): 0 clean; 1 a discrepancy, representation violation, stale
entry, unclassified refusal, census problem or corpus identity mismatch (HEAD, dirty or
unrecorded `.al`); 2 could not run or incomplete. The quick
tier classifies refusals from fixture-classes.tsv, resolve and full from
production-classes.tsv (only the requested corpora's entries)."""
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
PRODUCTION_CLASSES = REPO / "tools" / "config_oracle" / "production-classes.tsv"

# The one root -> label map. A production record's id is `<label>:<posix path relative to
# the root>`, the same on every machine, and production-classes.tsv is keyed by it. A
# requested root that is none of these exits 2 (compared after resolve()).
CORPORA = {
    "bc-history": REPO / "BC.History",
    "dc": REPO / "DC",
    "bc28.1": Path(os.environ.get("AL_BC28_ROOT", "H:/Git/BC28.1")),
    "bcapps-29.0": Path(os.environ.get("AL_BCAPPS29_ROOT", "H:/Git/BCApps-29.0")),
    # TEST-ONLY: tools/gate_selftest.py's oracle cases build their corpus at this path in
    # the scratch copy of the repo (REPO is that copy). A label, rather than a CLI option
    # to relabel roots or swap the classification file, keeps the gate case on exactly the
    # production code path, and gives no production run a way around the map.
    "selftest": REPO / "selftest-corpus",
}
# The resolve tier runs only these stages, so only entries for their reasons apply there.
RESOLVE_REASONS = ("resolver", "reference-error")

# The oracle's own self-tests (spec sections 1-3), corpus-free and about a second: the
# resolver self-test and its #elif first-match mutation, the comparator's mutations, the
# precedence table's recomposition, the representation contracts' controls, and the check
# that lowering never imports a parser (test_isolation.py), and the fixture-classes
# loader with its evidence rules (test_fixtures.py: added in B3 fix round 1, after a
# fixture rename broke its hard-coded case id and nothing local ran it; it reads only
# test/corpus and tmp files and imports no parser). They
# exist only as pytest modules, so the quick tier runs those modules rather than a copy.
SELFTESTS = ("test_resolve.py", "test_configs.py", "test_compare.py",
             "test_precedence.py", "test_representation.py", "test_isolation.py",
             "test_fixtures.py")

PASS, FAIL = "PASS", "FAIL"


def _sha(paths):
    h = hashlib.sha256()
    for p in paths:
        h.update(p.read_bytes())
    return h.hexdigest()[:16]


def _git_head(path, short=True):
    r = subprocess.run(["git", "-C", str(path), "rev-parse", *(["--short"] if short else []), "HEAD"],
                       capture_output=True, text=True)
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
    """(a) registry census, (b) self-tests, (c) fixture differential, (d) condition structure
    (B1: the tree's #if/#elif grouping against the resolver's). Every stage runs and
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
        stages.append(("(d) condition structure", *runner.condition_stage(summary)))
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

def corpus_label(root):
    r = Path(root).resolve()
    return next((label for label, p in CORPORA.items() if p.resolve() == r), None)


def production_classes(labels, tier):
    """The production-classes.tsv entries for the requested corpora (and, in the resolve
    tier, for the stages it runs). An entry for another corpus is neither applied nor
    stale-checked; one whose label is in no map is a typo that would never apply."""
    classes = fixtures.load_classes(PRODUCTION_CLASSES, "production")
    unknown = sorted({c.split(":", 1)[0] for c, _ in classes} - set(CORPORA))
    if unknown:
        raise ValueError(f"production-classes.tsv names unknown corpus labels: {unknown}")
    out = {k: v for k, v in classes.items() if k[0].split(":", 1)[0] in labels}
    if tier == "resolve":
        out = {k: v for k, v in out.items()
               if v[0].split(":")[1] in RESOLVE_REASONS}
    return out, len(classes)


def recorded_heads():
    """`# corpus-head <label> <sha>` header lines of production-classes.tsv: the corpus
    commit each label's entries were generated from."""
    heads = {}
    for line in PRODUCTION_CLASSES.read_text(encoding="utf-8").splitlines():
        if line.startswith("# corpus-head "):
            label, sha = line.split()[2:4]
            heads[label] = sha
    return heads


def recorded_untracked():
    """`# corpus-untracked <label> <sha256> <path>` header lines: the untracked `.al` files
    in a corpus's working tree when its entries were generated -> {label: {path: sha256}}."""
    out = {}
    for line in PRODUCTION_CLASSES.read_text(encoding="utf-8").splitlines():
        if line.startswith("# corpus-untracked "):
            label, sha, path = line.split(" ", 4)[2:]
            out.setdefault(label, {})[path] = sha
    return out


def al_status(root):
    """-> (tracked `.al` changes, {untracked `.al` path: sha256}) of a git corpus, or None
    when `root` is not a git work tree. `_collect` reads the working tree, not HEAD, so both
    reach the oracle. `ls-files --others` without `--exclude-standard` lists ignored files
    too, one by one (the oracle reads them as well), and `:(icase)` matches `rglob`, which
    is case-insensitive on Windows. Paths are relative to `root`."""
    def git(*args):
        r = subprocess.run(["git", "-C", str(root), *args, "--", ":(icase)*.al"], capture_output=True)
        return None if r.returncode else [x for x in r.stdout.decode("utf-8").split("\0") if x]
    changed = git("diff", "-z", "--no-renames", "--relative", "--name-status", "HEAD")
    others = git("ls-files", "-z", "--others")
    if changed is None or others is None:
        return None
    tracked = [f"{st} {path}" for st, path in zip(changed[::2], changed[1::2])]
    return tracked, {path: hashlib.sha256((Path(root) / path).read_bytes()).hexdigest() for path in others}


def corpus_mismatches(roots):
    """A requested corpus that is not the one its entries were generated from. Keys like
    `reference-error:error` carry no content, and only a record's first item is keyed, so a
    changed corpus can keep matching its old entries. Each of these fails the run (exit 1):
    another HEAD; a modified, deleted or renamed tracked `.al`; an untracked `.al` that is
    not recorded, or whose sha256 differs; a recorded untracked `.al` that is gone (stale).
    A label with no recorded head is not checked; a root that is not a git work tree gets
    only the HEAD check, which it fails. Non-`.al` files are ignored."""
    heads, recorded, out = recorded_heads(), recorded_untracked(), []
    for root in roots:
        label = corpus_label(root)
        if label not in heads:
            continue
        head = _git_head(root, short=False)
        if head != heads[label]:
            out.append(f"corpus {label} ({root}) is at {head}, but "
                       f"{PRODUCTION_CLASSES.name} was generated at {heads[label]}: regenerate it")
        status = al_status(root)
        if status is None:
            continue
        tracked, untracked = status
        out += [f"corpus {label}: tracked .al changed in the working tree ({t}): "
                f"the oracle reads the working tree, not HEAD" for t in tracked]
        want = recorded.get(label, {})
        for path, sha in sorted(untracked.items()):
            if path not in want:
                out.append(f"corpus {label}: untracked .al is not recorded: {path} (sha256 {sha}); "
                           f"record `# corpus-untracked {label} {sha} {path}` or remove the file")
            elif want[path] != sha:
                out.append(f"corpus {label}: untracked .al {path} has sha256 {sha}, "
                           f"recorded {want[path]}")
        out += [f"corpus {label}: recorded untracked .al is gone (stale entry): {path}"
                for path in sorted(set(want) - set(untracked))]
    return out


def _collect(roots):
    """-> (inputs, {input id: root}, {root: .al count}), or an error message.
    An input id is `<corpus label>:<posix path relative to the root>`.

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
        label = corpus_label(root)
        if label is None:
            return None, (f"corpus root has no label: {root} (labels: "
                          + ", ".join(f"{k} = {v}" for k, v in CORPORA.items()) + ")")
        files[str(root)] = len(paths)
        for p in paths:
            input_id = f"{label}:{p.relative_to(root).as_posix()}"
            inputs.append((input_id, p.read_bytes()))
            root_of[input_id] = str(root)
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
    classes, total = production_classes({corpus_label(r) for r in roots}, args.tier)
    header = _header(args.tier)
    for root in roots:
        header[f"corpus {root}"] = f"{corpus_label(root)}, {_git_head(root)}"
    header["classifications"] = (f"{PRODUCTION_CLASSES.name}, {len(classes)} of {total} "
                                 f"entries apply to the requested corpora and tier")
    summary = runner.run(inputs, None, args.workers, args.tier, classes)
    stale_heads = corpus_mismatches(roots)
    cond_code, cond_status = runner.condition_stage(summary)
    # The stage's own code counts: "could not run" (2) fails the run like any other stage.
    summary.exit_code = max(summary.exit_code, cond_code)
    extra = ["## Per root", "", *runner.root_table(runner.per_root(summary, root_of, files)),
             "", f"- stage condition structure: {cond_status}"]
    if stale_heads:
        extra += ["", "## Corpus identity mismatch (exit 1)", "", *(f"- {m}" for m in stale_heads)]
        summary.exit_code = max(summary.exit_code, 1)
    runner.write_report(summary, Path(args.report), header, extra)
    print((Path(args.report) / "summary.md").read_text(encoding="utf-8"))
    for m in stale_heads:
        print(f"config-oracle: {m}", file=sys.stderr)
    return summary.exit_code


if __name__ == "__main__":
    sys.exit(main())
