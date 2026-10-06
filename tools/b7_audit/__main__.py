"""python -m tools.b7_audit census [--check|--list]"""
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


def main(argv=None):
    p = argparse.ArgumentParser(prog="tools.b7_audit")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("census")
    c.add_argument("--check", action="store_true")
    c.add_argument("--list", action="store_true")
    return cmd_census(p.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
