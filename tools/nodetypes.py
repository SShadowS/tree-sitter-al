#!/usr/bin/env python3
"""nodetypes.py -- answer questions about src/node-types.json.

    python tools/nodetypes.py show TYPE        # fields (multiple/required/types), children
    python tools/nodetypes.py who-has TYPE     # every (parent, field) that can hold TYPE
    python tools/nodetypes.py diff REV         # vs `git show REV:src/node-types.json`

node-types.json is GENERATED: it tells you what the grammar DOES, never what it should do.
tools/check-field-types.py is the contract (CLAUDE.md, "Two rules about verification").
It also lists anonymous children only inside fields, so every keyword node looks
childless here whatever its real shape: use `tools/snip.py` for the runtime tree.

Anonymous types print quoted ("+"); TYPE matches named and anonymous alike. Exit 0; 1 if `show`/`who-has` finds nothing or
`diff` finds a difference; 2 if it cannot run.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
NODE_TYPES = "src/node-types.json"


def load(rev: str | None = None) -> list[dict]:
    if rev is None:
        return json.loads((REPO / NODE_TYPES).read_text(encoding="utf-8"))
    out = subprocess.run(["git", "show", f"{rev}:{NODE_TYPES}"], cwd=REPO,
                         capture_output=True, text=True, encoding="utf-8")
    if out.returncode:
        raise RuntimeError(out.stderr.strip())
    return json.loads(out.stdout)


def name(t: dict) -> str:
    return t["type"] if t["named"] else f'"{t["type"]}"'


def slots(entry: dict) -> dict[str, dict]:
    """{field name, or '(children)': {"multiple", "required", "types": set of names}}."""
    out = {f: s for f, s in entry.get("fields", {}).items()}
    if "children" in entry:
        out["(children)"] = entry["children"]
    return {f: {"multiple": s["multiple"], "required": s["required"],
                "types": {name(t) for t in s["types"]}} for f, s in out.items()}


def show(types, wanted: str) -> int:
    hits = [e for e in types if e["type"] == wanted.strip('"')]
    for e in hits:
        print(name(e) + ("  (extra)" if e.get("extra") else "") + ("  (root)" if e.get("root") else ""))
        for f, s in slots(e).items():
            print(f"  {f}: multiple={s['multiple']} required={s['required']}")
            for t in sorted(s["types"]):
                print(f"    {t}")
        if not slots(e):
            print("  (no fields, no named children listed)")
    return 0 if hits else 1


def who_has(types, wanted: str) -> int:
    found = 0
    for e in types:
        for f, s in slots(e).items():
            if wanted in s["types"] or f'"{wanted}"' in s["types"]:
                print(f"{name(e)}\t{f}\tmultiple={s['multiple']} required={s['required']}")
                found += 1
    return 0 if found else 1


def diff(old_types, new_types) -> int:
    old = {name(e): slots(e) for e in old_types}
    new = {name(e): slots(e) for e in new_types}
    lines = [f"+ type {t}" for t in sorted(new.keys() - old.keys())]
    lines += [f"- type {t}" for t in sorted(old.keys() - new.keys())]
    for t in sorted(old.keys() & new.keys()):
        o, n = old[t], new[t]
        lines += [f"+ field {t}.{f}" for f in sorted(n.keys() - o.keys())]
        lines += [f"- field {t}.{f}" for f in sorted(o.keys() - n.keys())]
        for f in sorted(o.keys() & n.keys()):
            for k in ("multiple", "required"):
                if o[f][k] != n[f][k]:
                    lines.append(f"~ {t}.{f} {k}: {o[f][k]} -> {n[f][k]}")
            lines += [f"~ {t}.{f} +{x}" for x in sorted(n[f]["types"] - o[f]["types"])]
            lines += [f"~ {t}.{f} -{x}" for x in sorted(o[f]["types"] - n[f]["types"])]
    print("\n".join(lines) if lines else "no difference")
    return 1 if lines else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split("\n", 2)[2])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show").add_argument("type")
    sub.add_parser("who-has").add_argument("type")
    sub.add_parser("diff").add_argument("rev")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "show":
            return show(load(), args.type)
        if args.cmd == "who-has":
            return who_has(load(), args.type)
        return diff(load(args.rev), load())
    except Exception as e:
        print(f"nodetypes: CANNOT RUN: {type(e).__name__}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
