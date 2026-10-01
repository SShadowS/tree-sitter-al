#!/usr/bin/env python3
"""traversal_census.py -- the traversal policy against the grammar and the registry (F0, D2).

traversal/policy.json is hand-maintained and ships in every package. This gate fails
when the grammar or the contracts registry has moved and the policy has not:

  * a named type in src/node-types.json that is not ordinary has no entry;
  * an entry names a type the grammar no longer declares;
  * the policy and tools/config_oracle/contracts.py disagree where the registry has
    an opinion (kind -> class, token-alias target, branch-container host policies).

"Not ordinary" is DETECTED from structure and from the registry -- a type that holds a
conditional directive, an extra, a registry entry, or a type only ever found under
special types -- and never from a name. A detected type may still be classified
`ordinary` (comment is); what it may not be is unclassified.

Exit: 0 clean; 1 a finding; 2 cannot run (a file missing or unreadable).

    python tools/traversal_census.py [--root DIR]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CLASSES = ("ordinary", "branch-container", "assembler", "fragment", "token-alias", "directive", "trivia")
BOUNDARIES = ("own-directives", "cross-node", "assembler", "none")
ROLES = ("if", "elif", "else", "endif")
KIND_TO_CLASS = {"directive": "directive", "trivia": "trivia", "token-alias": "token-alias",
                 "branch-select": "branch-container", "assembler": "assembler", "fragment": "fragment"}


def _children(t: dict) -> set:
    specs = list(t.get("fields", {}).values()) + ([t["children"]] if "children" in t else [])
    return {x["type"] for spec in specs for x in spec.get("types", [])}


def census(policy: dict, node_types: list, registry: dict, host_slots) -> list:
    """Every problem, as one line each. `registry` is contracts.REGISTRY, `host_slots`
    is contracts.host_slots: passed in so a test can hand over a modified copy."""
    problems = []
    if policy.get("schema") != 1:
        problems.append(f"policy schema {policy.get('schema')!r}, expected 1")
    types = policy.get("types", {})
    named = {t["type"] for t in node_types if t.get("named")}
    kids = {t["type"]: _children(t) for t in node_types if t.get("named")}

    roles = {}
    for name, e in sorted(types.items()):
        cls = e.get("class")
        if cls not in CLASSES:
            problems.append(f"unknown class {cls!r}: {name}")
            continue
        if e.get("arm_boundary") not in BOUNDARIES:
            problems.append(f"unknown arm_boundary {e.get('arm_boundary')!r}: {name}")
        if not str(e.get("reason", "")).strip():
            problems.append(f"no reason: {name}")
        if ("hosts" in e) != (cls == "branch-container") or (cls == "branch-container" and not e["hosts"]):
            problems.append(f"hosts belong on every branch container and nothing else: {name}")
        if ("alias_to" in e) != (cls == "token-alias"):
            problems.append(f"alias_to belongs on every token alias and nothing else: {name}")
        elif cls == "token-alias" and e["alias_to"] not in named:
            problems.append(f"alias_to names no declared type: {name} -> {e['alias_to']}")
        if "role" in e:
            if cls != "directive" or e["role"] not in ROLES:
                problems.append(f"a role belongs on a directive and is one of {ROLES}: {name}")
            roles.setdefault(e["role"], []).append(name)
    for r in ROLES:
        if len(roles.get(r, [])) != 1:
            problems.append(f"role {r} must name exactly one type, names {roles.get(r, [])}")

    for name in sorted(set(types) - named):
        problems.append(f"stale entry, type no longer declared: {name}")

    role_types = {n for n, e in types.items() if "role" in e}
    candidates = {}
    for t in sorted(named):
        if kids[t] & role_types:
            candidates.setdefault(t, "holds a conditional directive")
    for t in node_types:
        if t.get("named") and t.get("extra"):
            candidates.setdefault(t["type"], "an extra")
    for t, e in registry.items():
        if t in named:
            candidates.setdefault(t, f"registry kind {e.kind}")
    parents = {}
    for p, ks in kids.items():
        for k in ks:
            parents.setdefault(k, set()).add(p)
    special = {n for n, e in types.items() if e.get("class") not in (None, "ordinary")}
    special |= {t for t in candidates if t not in types}
    grew = True
    while grew:
        grew = False
        for t in sorted(named - special - set(candidates)):
            if parents.get(t) and parents[t] <= special:
                candidates[t] = "only ever a child of special types"
                special.add(t)
                grew = True
    for t in sorted(candidates):
        if t not in types:
            problems.append(f"unclassified: {t} ({candidates[t]})")

    for t, e in sorted(registry.items()):
        p = types.get(t)
        if p is None:
            continue
        want = KIND_TO_CLASS.get(e.kind)
        if want and p.get("class") != want:
            problems.append(f"class disagrees with the registry: {t} is {p.get('class')}, "
                            f"registry kind {e.kind} means {want}")
        if e.kind == "unsupported" and p.get("class") == "ordinary":
            problems.append(f"registry-unsupported type classified ordinary: {t}")
        if e.kind == "token-alias" and p.get("alias_to") != e.alias_to:
            problems.append(f"alias_to disagrees with the registry: {t} -> {p.get('alias_to')}, registry {e.alias_to}")
        if p.get("class") == "branch-container" and e.hosts and p.get("hosts") != e.hosts:
            mine, theirs = p.get("hosts") or {}, e.hosts
            for slot in sorted(set(mine) | set(theirs)):
                if mine.get(slot) != theirs.get(slot):
                    problems.append(f"host policy disagrees with the registry: {t} in {slot}: "
                                    f"{mine.get(slot)} vs {theirs.get(slot)}")

    for t, p in sorted(types.items()):
        if p.get("class") != "branch-container" or (t in registry and registry[t].hosts) or t not in named:
            continue
        real, declared = host_slots(node_types, t), set(p.get("hosts") or {})
        problems += [f"host slot not classified: {t} in {s}" for s in sorted(real - declared)]
        problems += [f"stale host slot: {t} in {s}" for s in sorted(declared - real)]

    opener, closer = (roles.get("if") or [None])[0], (roles.get("endif") or [None])[0]
    for t, p in sorted(types.items()):
        if t not in kids or p.get("class") not in CLASSES:
            continue
        d = kids[t] & role_types
        want = ("own-directives" if {opener, closer} <= d else "cross-node" if d
                else "assembler" if p["class"] == "fragment" else "none")
        if p.get("arm_boundary") != want:
            problems.append(f"arm_boundary of {t} is {p.get('arm_boundary')}, its declared children say {want}")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args(argv)
    try:
        policy = json.loads((args.root / "traversal" / "policy.json").read_text(encoding="utf-8"))
        node_types = json.loads((args.root / "src" / "node-types.json").read_text(encoding="utf-8"))
        sys.path.insert(0, str(args.root))
        from tools.config_oracle import contracts
    except (OSError, ValueError, ImportError) as exc:
        print(f"traversal census: cannot run: {exc}", file=sys.stderr)
        return 2
    problems = census(policy, node_types, contracts.REGISTRY, contracts.host_slots)
    for p in problems:
        print(p)
    print(f"traversal census: {len(policy.get('types', {}))} entries, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
