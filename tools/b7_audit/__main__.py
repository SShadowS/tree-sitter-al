"""python -m tools.b7_audit census [--check|--list]
   python -m tools.b7_audit report [--out PATH] [--evidence PATH]
   python -m tools.b7_audit run [--only FAMILY|KEY|PLACEMENT] [--jobs N] [--check] [--accept-tool]
   python -m tools.b7_audit assert --cell ID | --refresh
   python -m tools.b7_audit manifest --check [--manifest PATH] [--evidence PATH]"""
import argparse
import sys
from pathlib import Path

from . import census, grammar, registry

HERE = Path(__file__).parent
GRAMMAR = HERE.parent.parent / "src" / "grammar.json"
REGISTRY = HERE / "registry.tsv"


def cmd_census(a):
    try:
        g = grammar.load(GRAMMAR)
        rows = registry.load(REGISTRY) if a.check else []
    except (OSError, ValueError, KeyError) as e:
        print(f"cannot run: {e}", file=sys.stderr)
        return 2
    pairs = census.census(g)
    if a.list:
        for k, r in pairs:
            print(f"{k}\t{r.host}\t{' > '.join(r.chain)}")
        return 0
    if a.check:
        missing, stale, invalid = registry.gate(pairs, rows)
        for k, r in missing:
            print(f"missing\t{k}\t{r.host}")
        for r in stale:
            print(f"stale\t{r.key}\t{r.route_host}")
        for r, why in invalid:
            print(f"invalid\t{r.key}\t{r.route_host}\t{why}")
        print(f"{len(pairs)} pairs: {len(missing)} missing, {len(stale)} stale, {len(invalid)} invalid")
        return 1 if missing or stale or invalid else 0
    print(f"{len(pairs)} pairs")
    return 0


def cmd_assert(cid):
    """The split tree (corpus format, with fields), each configuration's flat text and the fingerprints
    to paste into assertions.tsv (spec 7.3: the expect fragment is written by hand from these)."""
    import hashlib
    sys.path.insert(0, str(HERE.parent))
    import snip
    from tools.config_oracle import directives
    from tools.query_coverage import loader
    from . import evidence, judge, placements
    e = next((x for x in evidence.universe() if x.cell.id == cid), None)
    if e is None:
        print(f"cannot run: no cell {cid!r}", file=sys.stderr)
        return 2
    src = e.cell.source.encode("utf-8")
    parser = loader.make_parser(loader.load_language(loader.ensure_library(loader.REPO_ROOT)))
    print("class\t" + "/".join(e.cls))
    print("--- source")
    print(e.cell.source)
    for env in placements.assignments(e.cell.symbols):
        flat = directives.resolve(src, env).masked.decode("utf-8")
        print(f"--- flat {sorted(env)}")
        print("\n".join(l for l in flat.splitlines() if l.strip()))
    print("--- split tree")
    print(snip.sexp(parser.parse(src)))
    fp = judge.fingerprints(hashlib.sha256(src).hexdigest())
    print("--- fingerprints (cell)")
    print(",".join(fp))
    print("--- fingerprints (class)")
    print(",".join(("*",) + fp[1:]))
    return 0


def cmd_refresh():
    """Re-evaluate every assertion row on the current parser; rewrite the fingerprints of unchanged rows, list the
    flipped ones (exit 1). The matrix stays valid only at the recorded hashes: follow with a full `run` and `report`."""
    from tools.query_coverage import loader
    from . import evidence, judge
    parser = loader.make_parser(loader.load_language(loader.ensure_library(loader.REPO_ROOT)))
    n, problems = judge.refresh(judge.ASSERTIONS, evidence.universe(), lambda b: parser.parse(b).root_node)
    for p in problems:
        print(p)
    print(f"{n} rows refreshed, {len(problems)} flipped or changed (left as they were)")
    return 1 if problems else 0


def cmd_manifest(a):
    from . import manifest
    try:
        entries = manifest.load(a.manifest or manifest.MANIFEST)
        records, verdicts = manifest.current(a.evidence)
    except (OSError, ValueError, KeyError) as e:
        print(f"cannot run: {e}", file=sys.stderr)
        return 2
    problems = manifest.check(entries, records, verdicts)
    for p in problems:
        print(p)
    adm = [e for e in entries if e.disposition == "admitted"]
    print(f"{len(entries)} entries ({len(adm)} admitted): {len(problems)} problems")
    return 1 if problems else 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="tools.b7_audit")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("census")
    m = c.add_mutually_exclusive_group()
    m.add_argument("--check", action="store_true")
    m.add_argument("--list", action="store_true")
    r = sub.add_parser("run")
    r.add_argument("--only")
    r.add_argument("--jobs", type=int, default=6)
    r.add_argument("--check", action="store_true")
    r.add_argument("--accept-tool", action="store_true")
    asr = sub.add_parser("assert", help="--cell: what an assertion row needs (tree, flat readings, "
                         "fingerprints); --refresh: re-fingerprint every row after a parser/oracle change")
    m = asr.add_mutually_exclusive_group(required=True)
    m.add_argument("--cell")
    m.add_argument("--refresh", action="store_true",
                   help="rewrite fingerprints of rows whose truth is unchanged; list flipped rows (exit 1)")
    mf = sub.add_parser("manifest", help="--check: the B7b-1 route manifest against the committed evidence")
    mf.add_argument("--check", action="store_true", required=True)
    mf.add_argument("--manifest")
    mf.add_argument("--evidence")
    rp = sub.add_parser("report")
    rp.add_argument("--out")
    rp.add_argument("--evidence")
    a = p.parse_args(argv)
    if a.cmd == "report":
        from . import evidence, report
        try:
            report.write(a.out or report.DEFAULT_OUT, evidence_path=a.evidence or evidence.EVIDENCE)
        except (OSError, ValueError, KeyError) as e:
            print(f"cannot run: {e}", file=sys.stderr)
            return 2
        return 0
    if a.cmd == "manifest":
        return cmd_manifest(a)
    if a.cmd == "assert":
        return cmd_refresh() if a.refresh else cmd_assert(a.cell)
    if a.cmd == "run":
        from . import evidence
        try:
            return evidence.run(only=a.only, jobs=a.jobs, check=a.check, accept_tool=a.accept_tool)
        except (evidence.ProbeBroken, evidence.OracleCrash, evidence.GeneratorBug, evidence.DiscoverMismatch) as e:
            print(f"{type(e).__name__}: {e}", file=sys.stderr)
            return 2
    return cmd_census(a)


if __name__ == "__main__":
    sys.exit(main())
