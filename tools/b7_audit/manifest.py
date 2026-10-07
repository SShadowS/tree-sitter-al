"""The B7b-1 route manifest (spec 2026-10-07 section 2): every audit cell of every candidate family with a
disposition, and for each cell the frozen alc configuration vector and the verdict expected after the fix.

TSV columns (header required, in this order):
  cell_id family route_host placement disposition reason owner cardinality frozen_vector expected_verdict

disposition   admitted | excluded | deferred. `reason` is empty for admitted, `owner` names who owns an excluded/deferred cell.
cardinality   empty-interior | optional-wrapper | empty-syntax-rejected | empty-semantic-rejected | unknown
              (spec 4.2; Task 1 writes `unknown`, Task 2 fills it).
frozen_vector alc's acceptance per configuration, sorted by configuration: `TPL=0,X=1:A;TPL=0,X=0:R` -> `config:A|R`
              joined by `;`. A = alc accepts, R = alc rejects. A class-sampled record counts as accepted in every
              configuration, exactly as judge.verdict does (its representative decides, not its own alc run). Empty for a pseudo entry.
expected_verdict  `verdict_str` of the verdict the cell must have: `CONSISTENT`, `GAP`, ... or `MIXED:<judge's detail>`
              (`cfg:CONSISTENT;cfg:REJECTED/<class>/over-accepts` for an admitted cell). Admitted cells carry the TARGET;
              excluded/deferred cells carry today's verdict, so a change there must be re-recorded on purpose.
A `route:` cell id is a pseudo entry for a route that has no matrix cells (not probed); it is never checked against evidence.
"""
import csv
from dataclasses import dataclass
from pathlib import Path

from tools.b7_audit import judge

HERE = Path(__file__).parent
MANIFEST = HERE / "b7b1-manifest.tsv"
HEAD = ["cell_id", "family", "route_host", "placement", "disposition", "reason", "owner", "cardinality",
        "frozen_vector", "expected_verdict"]
DISPOSITIONS = ("admitted", "excluded", "deferred")
CARDINALITIES = ("empty-interior", "optional-wrapper", "empty-syntax-rejected", "empty-semantic-rejected", "unknown")
FAMILIES = ("var-names", "implements", "move-modification", "key-fields", "sorting", "order-by",
            "array-dimensions", "attribute-arguments", "type-arguments")


@dataclass(frozen=True)
class Entry:
    cell_id: str
    family: str
    route_host: str
    placement: str
    disposition: str
    reason: str
    owner: str
    cardinality: str
    frozen_vector: str
    expected_verdict: str


def accepts(r):
    """alc's acceptance of one record's configuration; judge.verdict treats a class-sampled record as accepted."""
    return r["alc"] == "class-sampled" or r["alc_flat"]["verdict"] == "ACCEPT"


def vector(records):
    return ";".join(f"{r['config']}:{'A' if accepts(r) else 'R'}" for r in sorted(records, key=lambda r: r["config"]))


def verdict_str(v):
    return v.name + (f":{v.detail}" if v.detail else "")


def _plain(vs):
    """An admitted cell is gated on the verdict name, not on how CONSISTENT was reached (that detail is only frozen on
    excluded/deferred cells, where a swap pass <-> assertion-closed must stay visible)."""
    return "CONSISTENT" if vs.startswith("CONSISTENT:") else vs


def target(records):
    """The verdict an admitted cell must reach: CONSISTENT, or MIXED where alc rejects some configurations (the split
    tree then parses clean, so those configurations are over-accepts)."""
    recs = sorted(records, key=lambda r: r["config"])
    if all(accepts(r) for r in recs):
        return "CONSISTENT"
    parts = [f"{r['config']}:CONSISTENT" if accepts(r)
             else f"{r['config']}:REJECTED/{judge._rejected({**r, 'parser_has_error': False})}" for r in recs]
    return "MIXED:" + ";".join(parts)


def load(path=MANIFEST):
    lines = [l for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    rows = list(csv.reader(lines, delimiter="\t", quoting=csv.QUOTE_NONE))
    if not rows or rows[0] != HEAD:
        raise ValueError(f"{path}: header must be {HEAD}, got {rows[0] if rows else 'nothing'}")
    out = []
    for i, r in enumerate(rows[1:], 2):
        if len(r) != len(HEAD):
            raise ValueError(f"{path} row {i}: {len(r)} columns, want {len(HEAD)}")
        e = Entry(*r)
        if e.disposition not in DISPOSITIONS:
            raise ValueError(f"{path} row {i}: disposition {e.disposition!r}")
        if e.cardinality not in CARDINALITIES:
            raise ValueError(f"{path} row {i}: cardinality {e.cardinality!r}")
        out.append(e)
    return out


def dump(entries, path=MANIFEST, preface=""):
    lines = [preface.rstrip("\n")] if preface else []
    lines.append("\t".join(HEAD))
    lines += ["\t".join(getattr(e, c) for c in HEAD) for e in entries]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def check(entries, evidence_records, verdicts):
    """-> problems (strings). verdicts: {cell id: (family, current verdict_str)}, as the report computes them."""
    by_cell = {}
    for r in evidence_records:
        by_cell.setdefault(r["cell"], []).append(r)
    problems, seen = [], set()
    for e in entries:
        if e.cell_id in seen:
            problems.append(f"duplicate\t{e.cell_id}")
        seen.add(e.cell_id)
        if e.cell_id.startswith("route:"):
            continue
        recs = by_cell.get(e.cell_id)
        if not recs or e.cell_id not in verdicts:
            problems.append(f"no evidence\t{e.cell_id}")
            continue
        r0 = recs[0]
        for col, want, got in (("family", e.family, verdicts[e.cell_id][0]), ("route_host", e.route_host, r0["host"]),
                               ("placement", e.placement, r0["placement"])):
            if want != got:
                problems.append(f"identity	{e.cell_id}	{col} {want!r} != evidence {got!r}")
        vec = vector(recs)
        if vec != e.frozen_vector:
            problems.append(f"vector\t{e.cell_id}\tfrozen {e.frozen_vector} != evidence {vec}")
        now = verdicts[e.cell_id][1]
        if e.disposition == "admitted":
            now = _plain(now)
            if e.expected_verdict != target(recs):
                problems.append(f"target	{e.cell_id}	expected_verdict {e.expected_verdict} is not the target {target(recs)}")
        if now != e.expected_verdict:
            what = "admitted cell not at its target" if e.disposition == "admitted" else \
                f"{e.disposition} cell changed (record the new verdict deliberately)"
            problems.append(f"verdict\t{e.cell_id}\t{what}: {now} != {e.expected_verdict}")
    for cid, (fam, _) in sorted(verdicts.items()):
        if fam in FAMILIES and cid not in seen:
            problems.append(f"missing\t{cid}\tcell of candidate family {fam} not in the manifest")
    return problems


def current(evidence_path=None):
    """-> (evidence records, {cell id: (family, verdict_str)}) from the committed evidence."""
    from tools.b7_audit import evidence, report
    path = evidence_path or evidence.EVIDENCE
    analysis, _ = report.analysed(evidence_path=path)
    _, records = evidence.read(path)
    return records, {c["id"]: (c["family"], verdict_str(c["v"])) for c in analysis["cells"]}
