"""The matrix report (spec 7.2, 8): committed evidence -> matrix, defect families, ranked fix list.

Reads only committed artifacts (evidence.jsonl, registry.tsv, assertions.tsv, the production shapes
inside the evidence header): it never runs alc, the parser or the oracle. Output is sorted everywhere,
LF, with no timestamps, so it is byte-identical for the same evidence in any record order.

Family = (registry family, defect kind); two cells with the same family and the same kind are ONE row.
Defect kinds: GAP, SILENT, OVERACCEPT (REJECTED syntax/over-accepts; a MIXED cell contributes its worst
per-configuration kind). Defective production sites = weighted shape counts over the distinct hosts of
the family's defective cells (`terminated-unit` shapes are shown, never weighted).
Ranking (spec 8): SILENT first; then GAP and OVERACCEPT by defective production sites; ties by name. A
family blocked by an external dependency goes to the end of its tier, and a family always follows the
in-list families it depends on.
Owner: B13 when a member seed is a `b13` twin or the family is `option-members` (items 37/38); B12 when a
member seed is a `value-runs__` seed or the family is `property-value` (item 36); else B7b+.

The one thing the report parses (parser only, never alc or the oracle): the source of each cell that
has a FRESH assertion row (fingerprints match the current cell source, parser.c, scanner.c and oracle),
regenerated from the registry, then judge.check_assertion on its tree decides whether the row holds. A
cell without an assertion row, or with a stale one, is not parsed: the committed evidence is enough.
"""
import dataclasses
import json
from collections import defaultdict
from pathlib import Path

from tools.b7_audit import evidence, judge, registry

HERE = Path(__file__).parent
DEFAULT_OUT = HERE.parent.parent / "docs" / "b7-separator-continuation-matrix.md"
# family -> families / external roadmap items it must wait for (roadmap B7: the comma-leading link list
# is ambiguous with the link/property boundary, so it follows that matrix).
DEPENDENCIES = {"link-list-comma-leading": ("link-property-ambiguity",)}
UNWEIGHTED = {"terminated-unit"}
SEVERITY = ("GAP", "SILENT", "MIXED", "REJECTED/over-accepts", "UNCHECKED", "REJECTED", "CONSISTENT")
ABBREV = {"GAP": "G", "SILENT": "S", "MIXED": "M", "REJECTED/over-accepts": "R!", "UNCHECKED": "U",
          "REJECTED": "R", "CONSISTENT": "C"}
TIER = {"SILENT": 0, "GAP": 1, "OVERACCEPT": 1}
NOT_PROBED = {"qualifier", "na", "lexical"}


# Shapes of placements.LIST_SHAPES whose #if arm OPENS with the separator (checked against the shape
# strings; `lead-optional`, `first-replace`, `sep-after`, `trail`, `empty`, `one-elem` and `empty-list`
# open with an element). holes-* arms hold only the separator, so they open with it too.
SEP_OPENING = frozenset({"sep-before", "sep-before-end", "count-differs", "both-in-arm", "sep-only",
                         "adjacent-indep", "adjacent-compl", "elif", "nested",
                         "holes-lead", "holes-mid", "holes-trail"})


def shape_id(placement):
    """`sep-before+comments@Name` -> `sep-before`."""
    return placement.split("+")[0].split("@")[0]


def subfamily(family, placement):
    """The comma-leading link list is its own family (it alone depends on the link/property matrix)."""
    return "link-list-comma-leading" if family == "link-list" and shape_id(placement) in SEP_OPENING         else family


def display(v):
    """Severity bucket of a Verdict."""
    if v.name == "REJECTED":
        return "REJECTED/over-accepts" if v.detail == "syntax/over-accepts" else "REJECTED"
    return v.name


def defect_kind(v):
    if v.name in ("GAP", "SILENT"):
        return v.name
    if v.name == "REJECTED" and v.detail == "syntax/over-accepts":
        return "OVERACCEPT"
    if v.name == "MIXED":
        for k in ("SILENT", "GAP"):
            if f":{k}" in v.detail:
                return k
        if "syntax/over-accepts" in v.detail:
            return "OVERACCEPT"
    return None


def seed_family(name, host, host_families):
    """seed->family, only where unambiguous: the seed's `// host:` is in exactly one registry family;
    else a name rule; else unassigned."""
    fams = host_families.get(host, set())
    if len(fams) == 1:
        return next(iter(fams))
    n = name.removeprefix("seed:")
    if n.startswith("value-runs__"):
        return "property-value"
    if n.startswith("link-keying__") or "-link" in n or "link-" in n:
        return "link-list"
    if "option" in n:
        return "option-members"
    if "relation" in n:
        return "table-relation"
    return "unassigned"


def owner_of(family, seeds):
    if any("b13" in s for s in seeds) or family == "option-members":
        return "B13"
    if any(s.startswith("seed:value-runs__") for s in seeds) or family == "property-value":
        return "B12"
    return "B7b+"


def analyse(records, header, rows, assertions=(), check=None):
    """-> {cells, families, rows, records} for the renderer. check(cell id, assertion) -> bool is called
    only for a cell whose assertion row is fresh (see the module docstring)."""
    by_cell = defaultdict(list)
    for r in records:
        by_cell[r["cell"]].append(r)
    for rs in by_cell.values():
        rs.sort(key=lambda r: r["config"])            # recs[0] must not depend on record order
    index, host_families = {}, defaultdict(set)
    for r in rows:
        for h in r.hosts:
            index[(r.key, h)] = r
            if r.family and r.role not in NOT_PROBED:
                host_families[h].add(r.family)
    gap_rows = {(r.key, r.witness): r for r in rows if judge.template_gap(r)}
    cells = []
    for cid in sorted(by_cell):
        recs = by_cell[cid]
        r0 = recs[0]
        if (r0["key"], r0["host"]) in gap_rows:
            continue    # collapsed into one template-level GAP entry (cells are generated for the witness host)
        row = index.get((r0["key"], r0["host"]))
        seed = r0["key"].startswith("seed:")
        cls = ("seed", "seed", r0["placement"]) if seed else \
              (row.role, row.family, r0["placement"]) if row else ("unknown", "unknown", r0["placement"])
        clskey = "/".join(cls)
        a = next((x for x in assertions if x.cell_or_class == cid), None) or \
            next((x for x in assertions if x.cell_or_class == clskey), None)
        if a is not None and check is not None and judge._fresh(a, r0["source_sha256"], None):
            a = dataclasses.replace(a, holds=check(cid, a))
        v = judge.verdict(recs, a, lookup=by_cell.get, cls=clskey)
        fam = seed_family(cid, r0["host"], host_families) if seed else subfamily(cls[1], r0["placement"])
        cells.append({"id": cid, "key": r0["key"], "host": r0["host"], "placement": r0["placement"],
                      "role": cls[0], "family": fam, "v": v, "shown": display(v), "seed": seed,
                      "measured": r0["alc"] == "measured", "kind": defect_kind(v)})
    for (k, h), r in sorted(gap_rows.items()):
        cells.append({"id": f"template:{k}@{h}", "key": k, "host": h, "placement": "template",
                      "role": r.role, "family": subfamily(r.family, ""), "v": judge.template_gap(r),
                      "shown": "GAP", "seed": False, "measured": False, "kind": "GAP"})
    weights, unweighted = defaultdict(int), defaultdict(int)
    for s in header.get("production_shapes", {}).get("shapes", []):
        (unweighted if s["class"] in UNWEIGHTED else weights)[s["host"]] += s["count"]
    fams = {}
    for c in cells:
        if c["kind"] is None:
            continue
        f = fams.setdefault((c["family"], c["kind"]), {"cells": [], "hosts": set(), "seeds": []})
        f["cells"].append(c["id"])
        f["hosts"].add(c["host"])
        if c["seed"]:
            f["seeds"].append(c["id"])
    for (name, kind), f in fams.items():
        f["cells"].sort()
        f["hosts"] = sorted(f["hosts"])
        f["sites"] = sum(weights[h] for h in f["hosts"])
        f["unweighted"] = sum(unweighted[h] for h in f["hosts"])
        f["deps"] = DEPENDENCIES.get(name, ())
        f["owner"] = owner_of(name, f["seeds"])
    return {"cells": cells, "families": fams, "rows": rows, "records": by_cell}


def rank(families, deps=None):
    """-> [(family, kind)] in fix order (module docstring)."""
    deps = DEPENDENCIES if deps is None else deps
    names = {n for n, _ in families}

    def key(fk):
        n, k = fk
        blocked = any(d not in names for d in deps.get(n, ()))
        return (TIER[k], blocked, -families[fk]["sites"], n, k)
    order, done = [], set()

    def emit(fk, stack=()):
        if fk in done or fk in stack:
            return
        for d in sorted(deps.get(fk[0], ())):
            for dk in sorted(k for k in families if k[0] == d):
                emit(dk, stack + (fk,))
        done.add(fk)
        order.append(fk)
    for fk in sorted(families, key=key):
        emit(fk)
    return order


# --- rendering ------------------------------------------------------------------------------------
def _table(head, body):
    return ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] + \
           ["| " + " | ".join(str(x).replace("|", "\\|").replace("\n", " ") for x in r) + " |" for r in body]


def render(a, header):
    out = ["# B7a separator and continuation matrix", "",
           "Generated by `python -m tools.b7_audit report` from `tools/b7_audit/evidence.jsonl`. "
           "Do not edit.", "", "## Evidence header", ""]
    for k in sorted(header):
        if k != "production_shapes":
            out.append(f"- `{k}`: `{json.dumps(header[k], sort_keys=True, ensure_ascii=False)}`")
    cells = a["cells"]
    out += ["", "## Totals per verdict", ""]
    tot = defaultdict(lambda: [0, 0])
    for c in cells:
        t = tot[c["shown"]]
        t[0] += 1
        t[1] += c["measured"]
    out += _table(["verdict", "abbrev", "cells", "measured by alc", "class-sampled"],
                  [(v, ABBREV[v], tot[v][0], tot[v][1], tot[v][0] - tot[v][1]) for v in SEVERITY if v in tot])
    out += ["", f"{len(cells)} cells. Legend: G gap, S silent, M mixed, R! rejected and over-accepted "
            "(syntax), U unchecked, R rejected (agrees, or semantic), C consistent. A table cell shows the "
            "worst verdict among the cells of that host and placement. Class-sampled cells are judged via "
            "their class representative.", ""]
    for role in sorted({c["role"] for c in cells if not c["seed"]}):
        rc = [c for c in cells if c["role"] == role and not c["seed"]]
        pls = sorted({c["placement"] for c in rc})
        out += [f"## Role: {role}", ""]
        body = []
        for h in sorted({c["host"] for c in rc}):
            line = []
            for p in pls:
                vs = [c["shown"] for c in rc if c["host"] == h and c["placement"] == p]
                line.append(ABBREV[min(vs, key=SEVERITY.index)] if vs else "")
            body.append([h] + line)
        out += _table(["host"] + pls, body) + [""]
    seeds = sorted((c for c in cells if c["seed"]), key=lambda c: c["id"])
    out += ["## Seeds", "", "Seeds are not ranked by host; the family is derived from the seed's `// host:` "
            "and name where unambiguous.", ""]
    out += _table(["seed", "host", "verdict", "detail", "family"],
                  [(c["id"], c["host"], c["shown"], c["v"].detail, c["family"]) for c in seeds]) + [""]
    out += ["## Generator imprecisions (vector mismatch)", "",
            "alc disagreed with the generator's intended vector; not defects of the parser.", ""]
    out += [f"- `{i}`" for i in sorted(c["id"] for c in cells if c["v"].vector_mismatch)] or ["none"]
    out += ["", "## Families", ""]
    fams = a["families"]
    out += _table(["family", "kind", "cells", "hosts", "defective production sites (weighted)",
                   "terminated-unit sites (unweighted)", "dependencies", "owner", "cell ids"],
                  [(n, k, len(f["cells"]), ", ".join(f["hosts"]), f["sites"], f["unweighted"],
                    ", ".join(f["deps"]) or "-", f["owner"], "; ".join(f["cells"]))
                   for (n, k), f in sorted(fams.items())])
    out += ["", "Owner rule: B13 when a member seed is a `b13` twin or the family is `option-members` "
            "(deferred items 37, 38); B12 when a member seed is a `value-runs__` seed or the family is "
            "`property-value` (item 36); otherwise B7b+.", "", "## Ranked fix list (B7b+)", "",
            "SILENT families first, then GAP and syntax over-accepting families by defective production "
            "sites (weighted shapes only), then dependency order. UNCHECKED cells are never ranked.", ""]
    out += _table(["#", "family", "kind", "sites", "dependencies", "owner"],
                  [(i, n, k, fams[(n, k)]["sites"], ", ".join(fams[(n, k)]["deps"]) or "-",
                    fams[(n, k)]["owner"]) for i, (n, k) in enumerate(rank(fams), 1)])
    out += ["", "## UNCHECKED (not ranked, not clean)", ""]
    un = sorted((c for c in cells if c["shown"] == "UNCHECKED"), key=lambda c: c["id"])
    recs = a["records"]

    def why(c):
        rs = sorted({x for r in recs[c["id"]] for x in (r["oracle"].get("reasons") or [])
                     if r["oracle"]["status"] == "cannot-validate"})
        return c["v"].detail or "; ".join(rs) or "no structural assertion"
    out += _table(["cell", "refusal reasons"], [(c["id"], why(c)) for c in un]) if un else ["none"]
    out += ["", "## Not probed", ""]
    have = {(c["key"], c["host"]) for c in cells}
    groups = defaultdict(list)
    for r in a["rows"]:
        if r.role in NOT_PROBED:
            groups[(r.role, r.reason or "no placement defined")].append(r.key)
        elif r.hosts and (r.key, r.witness) not in have and not judge.template_gap(r):
            groups[("no-evidence", "no evidence record for this row")].append(r.key)
    out += _table(["role", "reason", "rows", "first keys"],
                  [(ro, why_, len(ks), ", ".join(sorted(ks)[:5])) for (ro, why_), ks in sorted(groups.items())]) \
        if groups else ["none"]
    return "\n".join(out) + "\n"


def build(evidence_path=evidence.EVIDENCE, registry_path=HERE / "registry.tsv",
          assertions_path=judge.ASSERTIONS, sources=None, parser=None):
    """sources {cell id: source bytes} and parser are injectable for tests; by default the sources are
    regenerated from the registry and seeds, and the parser is the repo's, both only when a fresh
    assertion row needs them."""
    header, records = evidence.read(evidence_path)
    rows = registry.load(registry_path)
    state = {}

    def check(cid, a):
        if "parser" not in state:
            from tools.query_coverage import loader
            state["parser"] = parser or loader.make_parser(
                loader.load_language(loader.ensure_library(loader.REPO_ROOT)))
            state["sources"] = sources if sources is not None else {
                e.cell.id: e.cell.source.encode("utf-8") for e in evidence.universe(registry_path)}
        return judge.check_assertion(state["parser"].parse(state["sources"][cid]).root_node, a)
    return render(analyse(records, header, rows, judge.load_assertions(assertions_path), check), header)


def write(path=DEFAULT_OUT, **kw):
    Path(path).write_text(build(**kw), encoding="utf-8", newline="\n")
