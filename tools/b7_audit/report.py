"""The matrix report (spec 7.2, 8): committed evidence -> matrix, defect families, ranked fix list.

Inputs: the committed evidence.jsonl.gz (its header carries the production shapes), registry.tsv and
assertions.tsv. It never runs alc or the oracle. It runs the parser on exactly one thing: the source of each cell
that has a FRESH assertion row (fingerprints match the current cell source, parser.c, scanner.c and oracle),
regenerated from the registry and seeds, so that judge.check_assertion decides on today's tree whether the row
holds. A cell without an assertion row, or with a stale one, is not parsed. The "Not probed" reasons are
regenerated from the registry by placements.skipped_for (no parser). Output is sorted everywhere, LF, with no
timestamps, so it is byte-identical for the same inputs in any record order.

Family = (registry family, defect kind); two cells with the same family and the same kind are ONE row.
Defect kinds: GAP, SILENT, OVERACCEPT (REJECTED syntax/over-accepts; a MIXED cell contributes its worst
per-configuration kind).
Production sites (matching shapes) = the production walk's (host, class) counts that match a (group type, class)
pair of the family's defective cells, each read off the cell's OWN split tree by cell_shape (the conditional group
spanning its placement offset, classified by seeds.classify, the walk's own classifier). A defective cell with no
such pair is listed as unclassified, never silently zeroed. A template GAP has no source of its own and matches
every weighted class of its host. `terminated-unit` shapes are shown per host, never weighted. For this the report
also parses every defective cell's source (parser only; the evidence's parser hash pins the trees).
Ranking (spec 8): SILENT first; then GAP and OVERACCEPT by matching production sites; ties by name. A
family blocked by an external dependency goes to the end of its tier, and a family always follows the
in-list families it depends on.
Owner: B13 when a member seed is a `b13` twin or the family is `option-members` (items 37/38); B12 when a
member seed is a `value-runs__` seed or the family is `property-value` (item 36); else B7b+.
"""
import dataclasses
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

from tools.b7_audit import evidence, judge, placements, registry, seeds

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
NOTES = {}

def cell_shape(root, src, hole=None):
    """-> (group type, class) for a cell's OWN split tree: the innermost conditional group (seeds._is_group) that
    spans the cell's placement offset, the first `#if` line in its hole (the whole source for a seed), classified by
    seeds.classify, the production walk's classifier. None when no group spans it (an `#if` inside an ERROR, no
    `#if` in the hole) or the walk gives that group no class."""
    lo, hi = hole or (0, len(src))
    m = re.search(rb"(?m)^[ \t]*(#if)\b", src[lo:hi])
    if m is None:
        return None
    n = root.descendant_for_byte_range(lo + m.start(1), lo + m.start(1) + 1)
    while n is not None and not (n.is_named and seeds._is_group(n.type)):
        n = n.parent
    cls = seeds.classify(n) if n is not None else None
    return (n.type, cls) if cls else None


# Shapes of placements.LIST_SHAPES whose #if arm OPENS with the separator (checked against the shape
# strings; `lead-optional`, `first-replace`, `sep-after`, `trail`, `empty`, `one-elem` and `empty-list`
# open with an element). `holes-lead` reaches link-list too (_plan_list generates holes-* for every list
# family): its arm is the separator alone, before the first element. `holes-trail` (after the last
# element) and `holes-mid` (a doubled-separator probe) are not leading and stay out.
SEP_OPENING = frozenset({"sep-before", "sep-before-end", "count-differs", "both-in-arm", "sep-only",
                         "adjacent-indep", "adjacent-compl", "elif", "nested",
                         "holes-lead"})


def shape_id(placement):
    """`sep-before+comments@Name` -> `sep-before`."""
    return placement.split("+")[0].split("@")[0]


def subfamily(family, placement):
    """The comma-leading link list is its own family (it alone depends on the link/property matrix)."""
    return "link-list-comma-leading" if family == "link-list" and shape_id(placement) in SEP_OPENING \
        else family


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


def analyse(records, header, rows, assertions=(), check=None, classify=None):
    """-> {cells, families, rows, records} for the renderer.
    check(cell id, assertion, source sha) -> bool, or a str when the cell's source cannot be tied to the
    evidence (the cell then stays UNCHECKED); it is called only for a cell whose assertion row is fresh (see the module docstring).
    classify(cell id, source sha) -> the (group type, class) of the cell's own tree (cell_shape), None, or a str (why
    the source is not there); called for every defective cell. Without a classifier every defective cell is
    unclassified."""
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
    by_target = {}
    for x in assertions:
        by_target.setdefault(x.cell_or_class, x)
    # parser.c, scanner.c and the oracle package are hashed ONCE (a 30 MB parser.c per cell costs minutes)
    base = judge.fingerprints("")[1:] if assertions else ()
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
        a = by_target.get(cid) or by_target.get(clskey)
        cur = (r0["source_sha256"],) + base
        note = ""
        if a is not None and check is not None and judge._fresh(a, r0["source_sha256"], cur):
            res = check(cid, a, r0["source_sha256"])
            if isinstance(res, str):
                a, note = None, res               # the regenerated source is not the one measured
            else:
                a = dataclasses.replace(a, holds=res)
        v = judge.verdict(recs, a, lookup=by_cell.get, cls=clskey, current=cur if a is not None else None)
        fam = seed_family(cid, r0["host"], host_families) if seed else subfamily(cls[1], r0["placement"])
        shape = None
        if defect_kind(v) is not None:
            shape = classify(cid, r0["source_sha256"]) if classify is not None else "no classifier"
        cells.append({"id": cid, "key": r0["key"], "host": r0["host"], "placement": r0["placement"],
                      "role": cls[0], "family": fam, "v": v, "shown": display(v), "seed": seed,
                      "measured": r0["alc"] == "measured", "kind": defect_kind(v), "note": note,
                      "shapes": (shape,) if isinstance(shape, tuple) else (),
                      "unclassified": None if isinstance(shape, tuple) else shape or "no class"})
    weights, unweighted = defaultdict(int), defaultdict(int)
    for s in header.get("production_shapes", {}).get("shapes", []):
        if s["class"] in UNWEIGHTED:
            unweighted[s["host"]] += s["count"]
        else:
            weights[(s["host"], s["class"])] += s["count"]
    for (k, h), r in sorted(gap_rows.items()):
        cells.append({"id": f"template:{k}@{h}", "key": k, "host": h, "placement": "template",
                      "role": r.role, "family": subfamily(r.family, ""), "v": judge.template_gap(r),
                      "shown": "GAP", "seed": False, "measured": False, "kind": "GAP", "note": "",
                      "shapes": tuple(sorted(hk for hk in weights if hk[0] == h)), "unclassified": None})
    fams = {}
    for c in cells:
        if c["kind"] is None:
            continue
        f = fams.setdefault((c["family"], c["kind"]), {"cells": [], "hosts": set(), "seeds": [], "shapes": set(),
                                                         "unclassified": []})
        f["cells"].append(c["id"])
        f["hosts"].add(c["host"])
        f["shapes"].update(c["shapes"])
        if c["unclassified"] is not None:
            f["unclassified"].append(c["id"])
        if c["seed"]:
            f["seeds"].append(c["id"])
    for (name, kind), f in fams.items():
        f["cells"].sort()
        f["unclassified"].sort()
        f["hosts"] = sorted(f["hosts"])
        f["sites"] = sum(weights[hk] for hk in f["shapes"])
        f["shapes"] = sorted(hk for hk in f["shapes"] if weights[hk])
        f["unweighted"] = sum(unweighted[h] for h in f["hosts"])
        f["deps"] = DEPENDENCIES.get(name, ())
        f["owner"] = owner_of(name, f["seeds"])
        f["note"] = NOTES.get(name, "")
    return {"cells": cells, "families": fams, "rows": rows, "records": by_cell, "groups": groups(cells)}


def groups(cells):
    """{(family, base placement, kind): sorted cell ids} over the defective cells; the first id is
    the group's representative, the one cell its pinned witnesses are made from (controller ruling:
    artifacts per group, not per cell). The base placement is the shape without its variants: `+comments`,
    `+not`, `@Name` and the operator class `/arithmetic` (`suffix/xor+not` -> `suffix`)."""
    out = defaultdict(list)
    for c in cells:
        if c["kind"] is not None:
            out[(c["family"], shape_id(c["placement"]).split("/")[0], c["kind"])].append(c["id"])
    return {k: sorted(v) for k, v in sorted(out.items())}


def slug(family, base, kind):
    """File-name stem of a group's alc probe."""
    return "__".join(x.replace("/", "-").replace(":", "-") for x in (family, base, kind.lower()))


def witness(family, base, kind):
    """Where a group's pinned witness lives. A probe that says `No corpus case` (its representative has an oracle
    discrepancy in a configuration alc rejects, which the quick tier cannot classify) is pinned in test_silent.py."""
    if kind == "SILENT":
        return "tools/b7_audit/tests/test_silent.py"
    probe = f"tools/alc_probe/cases/b7-audit/{slug(family, base, kind)}.al"
    p = HERE.parent.parent / probe
    if p.is_file() and "// No corpus case" in p.read_text(encoding="utf-8"):
        return f"{probe}, tools/b7_audit/tests/test_silent.py"
    return f"{probe}, test/corpus/b7_gap_{family.replace('-', '_')}_test.txt"


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
           "Generated by `python -m tools.b7_audit report` from `tools/b7_audit/evidence.jsonl.gz`. "
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
    out += ["Production sites (matching shapes): the production walk's (host, class) counts that match a (host, "
            "class) pair of the family's defective cells, each read off the cell's own split tree (`report.cell_shape`: "
            "the conditional group spanning its placement offset, classified by `seeds.classify`, the walk's own "
            "classifier; a template GAP matches every weighted class of its host); the matching pairs are listed. A "
            "family's cell ids are in the evidence; its defect groups below name one representative each.", ""]
    out += _table(["family", "kind", "cells", "hosts", "production sites (matching shapes)", "matching shapes",
                   "terminated-unit sites (unweighted)", "dependencies", "owner", "representative"],
                  [(n, k, len(f["cells"]), ", ".join(f["hosts"]), f["sites"],
                    ", ".join(f"{h}/{c}" for h, c in f["shapes"]) or "-", f["unweighted"],
                    ", ".join(f["deps"]) or "-", f["owner"] + (f" ({f['note']})" if f["note"] else ""), f["cells"][0])
                   for (n, k), f in sorted(fams.items())])
    uncl = [(n, k, f["unclassified"]) for (n, k), f in sorted(fams.items()) if f["unclassified"]]
    out += ["", f"Unclassified defective cells: {sum(len(u) for _, _, u in uncl)} (their own tree gives no (group "
            "type, class): no conditional group spans the placement offset, or `seeds.classify` gives none; they "
            "add no production sites). Per family, with the first cell ids:", ""]
    out += _table(["family", "kind", "unclassified cells", "first cells"],
                  [(n, k, len(u), ", ".join(u[:3])) for n, k, u in uncl]) if uncl else ["none"]
    out += ["", "## Defect groups and their witnesses", "",
            "One group per (family, base placement, kind); its representative is its lexicographically first "
            "cell, and the group's alc probe, corpus case or SILENT test is made from that cell alone.", ""]
    out += _table(["family", "base placement", "kind", "cells", "representative", "witness"],
                  [(f, b, k, len(ids), ids[0], witness(f, b, k)) for (f, b, k), ids in a["groups"].items()]) \
        if a["groups"] else ["none"]
    out += ["", "Owner rule: B13 when a member seed is a `b13` twin or the family is `option-members` "
            "(deferred items 37, 38); B12 when a member seed is a `value-runs__` seed or the family is "
            "`property-value` (item 36); otherwise B7b+.", "", "## Ranked fix list (B7b+)", "",
            "SILENT families first, then GAP and syntax over-accepting families by production sites (matching "
            "shapes), then dependency order. UNCHECKED cells are never ranked.", ""]
    out += _table(["#", "family", "kind", "production sites (matching shapes)", "dependencies", "owner", "note"],
                  [(i, n, k, fams[(n, k)]["sites"], ", ".join(fams[(n, k)]["deps"]) or "-",
                    fams[(n, k)]["owner"], fams[(n, k)]["note"] or "-") for i, (n, k) in enumerate(rank(fams), 1)])
    out += ["", "## UNCHECKED (not ranked, not clean)", ""]
    un = sorted((c for c in cells if c["shown"] == "UNCHECKED"), key=lambda c: c["id"])
    recs = a["records"]

    def why(c):
        rs = sorted({x for r in recs[c["id"]] for x in (r["oracle"].get("reasons") or [])
                     if r["oracle"]["status"] == "cannot-validate"})
        return c["note"] or c["v"].detail or "; ".join(rs) or "no structural assertion"
    out += _table(["cell", "refusal reasons"], [(c["id"], why(c)) for c in un]) if un else ["none"]
    out += ["", "## Not probed", ""]
    have = {(c["key"], c["host"]) for c in cells}
    groups = defaultdict(list)
    for r in a["rows"]:
        if r.role in NOT_PROBED:
            groups[(r.role, r.reason or "no placement defined")].append(r.key)
        elif r.hosts and (r.key, r.witness) not in have and not judge.template_gap(r):
            why_ = "; ".join(sorted({w if p == "*" else f"{p}: {w}" for p, w in placements.skipped_for(r)}))
            groups[("no-evidence", why_ or "no evidence record for this row")].append(r.key)
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

    def tree(cid, sha):
        """-> (root, source, hole), or a str when the cell's source cannot be tied to the evidence."""
        if "parser" not in state:
            from tools.query_coverage import loader
            state["parser"] = parser or loader.make_parser(
                loader.load_language(loader.ensure_library(loader.REPO_ROOT)))
            cells = {} if sources is not None else {e.cell.id: e.cell for e in evidence.universe(registry_path)}
            state["sources"] = sources if sources is not None else {
                i: c.source.encode("utf-8") for i, c in cells.items()}
            state["holes"] = {i: c.hole for i, c in cells.items()}
        src = state["sources"].get(cid)
        if src is None:
            return "cell not in the regenerated universe"
        if hashlib.sha256(src).hexdigest() != sha:
            return "source changed since evidence"
        return state["parser"].parse(src).root_node, src, state["holes"].get(cid)

    def check(cid, a, sha):
        t = tree(cid, sha)
        return t if isinstance(t, str) else judge.check_assertion(t[0], a)

    def classify(cid, sha):
        t = tree(cid, sha)
        return t if isinstance(t, str) else cell_shape(*t)
    return render(analyse(records, header, rows, judge.load_assertions(assertions_path), check, classify), header)


def write(path=DEFAULT_OUT, **kw):
    Path(path).write_text(build(**kw), encoding="utf-8", newline="\n")
