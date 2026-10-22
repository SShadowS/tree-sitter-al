"""Route manifests: every audit cell of every candidate family with a disposition, and for each cell the frozen alc
configuration vector and the verdict expected after the fix. B7b-1 (spec 2026-10-07 section 2) wrote the first one;
B7b-3 (spec 2026-10-08 section 8.2) scoped them, so each manifest names its own family universe.

Line 1 (mandatory): `# families: <f1>,<f2>,...`, registry family names, no spaces, no duplicates. That scope decides
which cells must be present (`missing`) and which rows may be (`scope`); only an `excluded` row may pin a
cell of another family (B7b-1's B13 sorting/where seed is `property-value`). It replaces the old hard-coded universe.
TSV columns (header required, in this order):
  cell_id family route_host placement disposition reason owner cardinality frozen_vector expected_verdict [expected_oracle]

disposition   admitted | excluded | deferred. `reason` is empty for admitted, `owner` names who owns an excluded/deferred cell.
cardinality   empty-interior | optional-wrapper | empty-syntax-rejected | empty-semantic-rejected | unknown
              (spec 4.2; Task 1 writes `unknown`, Task 2 fills it).
frozen_vector alc's acceptance per configuration, sorted by configuration: `TPL=0,X=1:A;TPL=0,X=0:R` -> `config:A|R`
              joined by `;`. A = alc accepts, R = alc rejects. A class-sampled record counts as accepted in every
              configuration, exactly as judge.verdict does (its representative decides, not its own alc run). Empty for a pseudo entry.
expected_verdict  `verdict_str` of the verdict the cell must have: `CONSISTENT`, `GAP`, ... or `MIXED:<judge's detail>`
              (`cfg:CONSISTENT;cfg:REJECTED/<class>/over-accepts` for an admitted cell). Admitted cells carry the TARGET;
              excluded/deferred cells carry today's verdict, so a change there must be re-recorded on purpose.
expected_oracle   optional column (B7b-3, spec 6.4): the config oracle's status per alc-ACCEPTED configuration,
              `CFG:STATUS[,CFG:STATUS...]`, e.g. `X=0:pass,X=1:lowering:one-reading` or
              `TPL2=0,X=0:pass,TPL2=0,X=1:lowering:unsupported-type`; STATUS is `pass`, `lowering:<kind>` or another
              oracle status (oracle_status). Empty = the oracle is not compared (the verdict still is, for every
              disposition). Its configurations must be exactly
              the vector's accepted ones; with an oracle given, check compares it with a fresh run.
A `route:` cell id is a pseudo entry for a route that has no matrix cells (not probed); it is never checked against evidence.
B7b-2 (spec 2026-10-20 section 8.4): `check(final_owner_prefix=...)` fails every row a phase owner (`B7b-2/A`, ...) still
holds; `check(require_oracle=True)` fails an admitted row without expected_oracle; `rerecord` re-records named rows
of another manifest whose verdict a later sub-project changed, deliberately and listed in its report; `admit` admits
the rows a phase owner holds once they reach their target (verdict and oracle), the step that closes a phase.
"""
import csv
import re
from dataclasses import dataclass
from pathlib import Path

from tools.b7_audit import judge

HERE = Path(__file__).parent
MANIFEST = HERE / "b7b1-manifest.tsv"
MANIFEST_B7B3 = HERE / "b7b3-manifest.tsv"
SCOPE_PREFIX = "# families: "
HEAD = ["cell_id", "family", "route_host", "placement", "disposition", "reason", "owner", "cardinality",
        "frozen_vector", "expected_verdict"]
DISPOSITIONS = ("admitted", "excluded", "deferred")
CARDINALITIES = ("empty-interior", "optional-wrapper", "empty-syntax-rejected", "empty-semantic-rejected", "unknown")
FAMILIES = ("var-names", "implements", "move-modification", "key-fields", "sorting", "order-by",
            "array-dimensions", "attribute-arguments", "type-arguments")   # the B7b-1 scope (its header line)
ORACLE_COL = "expected_oracle"
# The B7b-1-excluded move header cells owned by B7b-3 (spec 8.2 transfer set), admitted in the B7b-3 manifest.
TRANSFER_B7B3 = frozenset(f"occ:{m}_modification:1.2@action_body#{p}{v}"
                          for m in ("moveafter", "movebefore", "movefirst", "movelast")
                          for p in ("adjacent-compl", "elif", "first-replace", "nested", "sep-before-end", "sep-only")
                          for v in ("", "+comments", "+not"))
_ORACLE_ITEM = re.compile(r"([A-Za-z_]\w*=[01](?:,[A-Za-z_]\w*=[01])*):([a-z-]+(?::[a-z-]+)?)(,|$)")


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
    expected_oracle: str = ""


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


def known_families():
    from tools.b7_audit import registry
    return {r.family for r in registry.load(HERE / "registry.tsv") if r.family} | {"seed"}


def scope_line(scope):
    return SCOPE_PREFIX + ",".join(scope)


def parse_scope(line, path: "str | Path" = "manifest"):
    """The `# families:` line -> tuple of families; a header that does not round-trip through scope_line fails."""
    if not line.startswith(SCOPE_PREFIX):
        raise ValueError(f"{path}: line 1 must be the scope header `{SCOPE_PREFIX}<family>,...`, got {line!r}")
    scope = tuple(line[len(SCOPE_PREFIX):].split(","))
    if not all(scope) or len(set(scope)) != len(scope) or scope_line(scope) != line:
        raise ValueError(f"{path}: malformed scope header (families, no spaces, no duplicates): {line!r}")
    unknown = sorted(set(scope) - known_families())
    if unknown:
        raise ValueError(f"{path}: unknown families in the scope header: {', '.join(unknown)}")
    return scope


def parse_oracle(value):
    """`CFG:STATUS[,CFG:STATUS...]` -> {config: status}; ValueError on anything else."""
    out, pos = {}, 0
    while pos < len(value):
        m = _ORACLE_ITEM.match(value, pos)
        if not m or (m.group(3) == "," and m.end() == len(value)):
            raise ValueError(f"expected_oracle value {value!r}: malformed at {value[pos:]!r}")
        if m.group(1) in out:
            raise ValueError(f"expected_oracle value {value!r}: duplicate configuration {m.group(1)}")
        out[m.group(1)] = m.group(2)
        pos = m.end()
    if not out:
        raise ValueError(f"expected_oracle value {value!r}: empty")
    return out


def load(path=MANIFEST):
    """-> (scope, entries)."""
    text = Path(path).read_text(encoding="utf-8").splitlines()
    scope = parse_scope(text[0] if text else "", path)
    lines = [l for l in text if l.strip() and not l.startswith("#")]
    rows = list(csv.reader(lines, delimiter="\t", quoting=csv.QUOTE_NONE))
    if not rows or rows[0] not in (HEAD, HEAD + [ORACLE_COL]):
        raise ValueError(f"{path}: header must be {HEAD} [+ {ORACLE_COL}], got {rows[0] if rows else 'nothing'}")
    width = len(rows[0])
    out = []
    for i, r in enumerate(rows[1:], 2):
        if len(r) != width:
            raise ValueError(f"{path} row {i}: {len(r)} columns, want {width}")
        e = Entry(*r)
        if e.disposition not in DISPOSITIONS:
            raise ValueError(f"{path} row {i}: disposition {e.disposition!r}")
        if e.cardinality not in CARDINALITIES:
            raise ValueError(f"{path} row {i}: cardinality {e.cardinality!r}")
        if e.expected_oracle:
            try:
                parse_oracle(e.expected_oracle)
            except ValueError as x:
                raise ValueError(f"{path} row {i}: {x}") from None
        out.append(e)
    return scope, out


def dump(scope, entries, path=MANIFEST, preface=""):
    head = HEAD + ([ORACLE_COL] if any(e.expected_oracle for e in entries) else [])
    lines = [scope_line(scope)] + ([preface.rstrip("\n")] if preface else [])
    lines.append("\t".join(head))
    lines += ["\t".join(getattr(e, c) for c in head) for e in entries]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def oracle_status(rec):
    """A config oracle record (status, items) -> the manifest's status string: `pass`, `lowering:<kind>` for a
    lowering refusal, otherwise the record's status (`discrepancy`, `cannot-validate`, ...)."""
    if rec.status == "pass":
        return "pass"
    first = str(rec.items[0]) if rec.items else ""
    if rec.status == "cannot-validate" and first.startswith("lowering:"):
        return ":".join(first.split(":")[:2])
    return rec.status


def passing_transfer(candidates, entries, problems):
    """The transfer-set cells the B7b-1 check exempts from its verdict comparison: in `candidates`, present in the
    B7b-3 manifest (`entries`) and with no problem in that manifest's check (`problems`)."""
    present = {e.cell_id for e in entries}
    bad = {p.split("\t")[1] for p in problems if "\t" in p}
    return frozenset(c for c in candidates if c in present and c not in bad)


def transfer_for(path, entries, records, verdicts, b7b3=MANIFEST_B7B3, oracle_factory=None):
    """The transfer cells the check of manifest `path` may exempt: its non-admitted TRANSFER_B7B3 rows that are in the
    B7b-3 manifest and pass its check there, the expected_oracle comparison included (a fresh oracle run unless
    `oracle_factory`, cell ids -> {cell id: statuses}, is given). Empty for the B7b-3 manifest itself."""
    cand = TRANSFER_B7B3 & {e.cell_id for e in entries if e.disposition != "admitted"}
    if not cand or not Path(b7b3).exists() or Path(path).resolve() == Path(b7b3).resolve():
        return frozenset()
    s3, e3 = load(b7b3)
    e3 = [e for e in e3 if e.cell_id in cand]
    want = {e.cell_id for e in e3 if e.expected_oracle}
    oracle = (oracle_factory or fresh_oracle)(want).get if want else None
    return passing_transfer(cand, e3, check(s3, e3, records, verdicts, oracle=oracle))


def check(scope, entries, evidence_records, verdicts, transfer=frozenset(), oracle=None,
          final_owner_prefix: "str | None" = None, require_oracle: bool = False):
    """-> problems (strings). verdicts: {cell id: (family, current verdict_str)}, as the report computes them.
    scope: the manifest's families. transfer: excluded/deferred cells exempt from the verdict comparison only (see
    passing_transfer); their identity, vector and coverage are still checked. oracle: cell id -> {config: status}
    from a fresh config oracle run (fresh_oracle); None skips that comparison, the configurations of
    expected_oracle are checked either way. final_owner_prefix (B7b-2 spec 8.4, final mode): every row whose owner
    starts with it is a problem (a phase owner such as `B7b-2/B` still holds it). require_oracle: an admitted row
    without expected_oracle is a problem."""
    by_cell = {}
    for r in evidence_records:
        by_cell.setdefault(r["cell"], []).append(r)
    problems, seen = [], set()
    for e in entries:
        if e.cell_id in seen:
            problems.append(f"duplicate\t{e.cell_id}")
        seen.add(e.cell_id)
        if e.family not in scope and e.disposition != "excluded":   # an excluded row may pin a neighbour
            problems.append(f"scope\t{e.cell_id}\tfamily {e.family} is outside the manifest scope")
        if final_owner_prefix and e.owner.startswith(final_owner_prefix):
            problems.append(f"final\t{e.cell_id}\towner {e.owner} still holds the row ({e.disposition})")
        if e.cell_id.startswith("route:"):
            continue
        if require_oracle and e.disposition == "admitted" and not e.expected_oracle:
            problems.append(f"require-oracle\t{e.cell_id}\tadmitted row has no expected_oracle")
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
        if e.expected_oracle:
            want = parse_oracle(e.expected_oracle)
            acc = {r["config"] for r in recs if accepts(r)}
            if set(want) != acc:
                problems.append(f"oracle-cover\t{e.cell_id}\texpected_oracle configurations {sorted(want)} "
                                f"!= alc-accepted {sorted(acc)}")
            elif oracle is not None:
                got = oracle(e.cell_id)
                if got is None:
                    problems.append(f"oracle\t{e.cell_id}\tno source: the cell is not in evidence.universe()")
                    got = {}
                problems += [f"oracle\t{e.cell_id}\t{c}: {got.get(c)} != {w}" for c, w in sorted(want.items())
                             if got.get(c) != w]
        if e.cell_id in transfer and e.disposition != "admitted":
            continue
        if now != e.expected_verdict:
            what = "admitted cell not at its target" if e.disposition == "admitted" else \
                f"{e.disposition} cell changed (record the new verdict deliberately)"
            problems.append(f"verdict\t{e.cell_id}\t{what}: {now} != {e.expected_verdict}")
    for cid, (fam, _) in sorted(verdicts.items()):
        if fam in scope and cid not in seen:
            problems.append(f"missing\t{cid}\tcell of candidate family {fam} not in the manifest")
    return problems


def oracle_value(recs, statuses):
    """The expected_oracle string for a cell: `statuses` ({config: status}) restricted to its alc-accepted
    configurations, sorted by configuration; empty when alc accepts none."""
    acc = sorted(r["config"] for r in recs if accepts(r))
    return ",".join(f"{c}:{statuses.get(c)}" for c in acc)


def rerecord(path, cell_ids, records, verdicts, oracle=None):
    """Re-record exactly the rows `cell_ids` of manifest `path` at their current verdict (expected_verdict; an
    admitted row keeps its target) and, when `oracle` (cell id -> {config: status}, as fresh_oracle) is given and
    the file has the column, their current expected_oracle. Identity, vector, disposition, reason and owner are
    never touched, so check still compares them. Every other line of the file is kept byte for byte. -> the changed
    columns, `cell\\tcolumn\\told -> new`, for the phase report. ValueError, writing nothing, on a cell that is not a
    row of the manifest or has no current evidence or oracle source."""
    path = Path(path)
    load(path)                                                  # refuse a malformed manifest before touching it
    want = list(dict.fromkeys(cell_ids))
    by_cell = {}
    for r in records:
        by_cell.setdefault(r["cell"], []).append(r)
    lines = path.read_text(encoding="utf-8").split("\n")
    head_i = next(i for i, l in enumerate(lines) if l.strip() and not l.startswith("#"))
    cols = lines[head_i].split("\t")
    rows = {l.split("\t", 1)[0]: i for i, l in enumerate(lines) if i > head_i and l.strip() and not l.startswith("#")}
    unknown = [c for c in want if c not in rows]
    if unknown:
        raise ValueError(f"{path}: not a row of the manifest: {', '.join(unknown)}")
    stale = [c for c in want if c not in by_cell or c not in verdicts]
    if stale:
        raise ValueError(f"no current evidence for: {', '.join(stale)}")
    statuses = {}
    if oracle is not None and ORACLE_COL in cols:
        statuses = {c: oracle(c) for c in want}
        missing = [c for c, s in statuses.items() if s is None]
        if missing:
            raise ValueError(f"the oracle has no source for: {', '.join(missing)}")
    changed = []
    for cid in want:
        r = dict(zip(cols, lines[rows[cid]].split("\t")))
        new = dict(r)
        if r["disposition"] != "admitted":
            new["expected_verdict"] = verdicts[cid][1]
        if cid in statuses:
            new[ORACLE_COL] = oracle_value(by_cell[cid], statuses[cid])
        changed += [f"{cid}\t{c}\t{r[c]} -> {new[c]}" for c in cols if new[c] != r[c]]
        lines[rows[cid]] = "\t".join(new[c] for c in cols)
    if changed:
        path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return changed


# Oracle refusals an admitted row may carry, each closed by the cell's holding assertion row (judge: a cannot-validate
# configuration with a fresh holding assertion is CONSISTENT), with the reason text the Phase A gate wrote for them.
ADMIT_REFUSALS = {"lowering:unsupported-type": "C1: the split host's oracle refusal",
                  "lowering:one-reading": "B12 host limitation (one-reading)"}


def admit(path, owner, records, verdicts, oracle, new_owner="B7b-2"):
    """Admit every non-admitted row of manifest `path` owned by `owner` whose current verdict is its target and whose
    oracle outcome is `pass`, or a refusal of ADMIT_REFUSALS, in every alc-accepted configuration, and whose family,
    route_host, placement and frozen_vector agree with the evidence (else check would fail the row): disposition
    admitted, owner `new_owner`, expected_verdict the target, expected_oracle the current outcome, reason empty for an
    all-pass cell or `<refusal reason>, assertion-closed in N configuration(s)`. Identity, vector and cardinality are
    kept; every other line of the file is kept byte for byte. -> (changed columns `cell\\tcolumn\\told -> new`, rows
    left as they were `cell\\twhy`). ValueError, writing nothing, when the file has no expected_oracle column."""
    path = Path(path)
    load(path)
    by_cell = {}
    for r in records:
        by_cell.setdefault(r["cell"], []).append(r)
    lines = path.read_text(encoding="utf-8").split("\n")
    head_i = next(i for i, l in enumerate(lines) if l.strip() and not l.startswith("#"))
    cols = lines[head_i].split("\t")
    if ORACLE_COL not in cols:
        raise ValueError(f"{path}: no {ORACLE_COL} column; --admit records the oracle outcome")
    changed, kept = [], []
    for i in range(head_i + 1, len(lines)):
        if not lines[i].strip() or lines[i].startswith("#"):
            continue
        r = dict(zip(cols, lines[i].split("\t")))
        cid = r["cell_id"]
        if r["owner"] != owner or r["disposition"] == "admitted" or cid.startswith("route:"):
            continue
        recs = by_cell.get(cid)
        if not recs or cid not in verdicts:
            kept.append(f"{cid}\tno current evidence")
            continue
        got = (verdicts[cid][0], recs[0]["host"], recs[0]["placement"], vector(recs))
        want = (r["family"], r["route_host"], r["placement"], r["frozen_vector"])
        if got != want:     # what check reports as identity/vector: never admit a row that check would then fail
            kept.append(f"{cid}\tidentity or vector {want} != evidence {got}")
            continue
        tgt, now = target(recs), _plain(verdicts[cid][1])
        if now != tgt:
            kept.append(f"{cid}\tverdict {now} is not the target {tgt}")
            continue
        statuses = oracle(cid)
        if statuses is None:
            kept.append(f"{cid}\tthe oracle has no source")
            continue
        acc = [rr["config"] for rr in recs if accepts(rr)]
        bad = sorted({statuses.get(c) for c in acc} - {"pass"} - set(ADMIT_REFUSALS))
        if bad:
            kept.append(f"{cid}\toracle outcome {', '.join(map(str, bad))} is neither pass nor a closed refusal")
            continue
        refused = [statuses[c] for c in acc if statuses[c] != "pass"]
        reason = "; ".join(ADMIT_REFUSALS[k] for k in sorted(set(refused)))
        new = dict(r, disposition="admitted", owner=new_owner, expected_verdict=tgt,
                   reason=f"{reason}, assertion-closed in {len(refused)} configuration(s)" if refused else "")
        new[ORACLE_COL] = oracle_value(recs, statuses)
        changed += [f"{cid}\t{c}\t{r[c]} -> {new[c]}" for c in cols if new[c] != r[c]]
        lines[i] = "\t".join(new[c] for c in cols)
    if changed:
        path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return changed, kept


def current(evidence_path=None):
    """-> (evidence records, {cell id: (family, verdict_str)}) from the committed evidence."""
    from tools.b7_audit import evidence, report
    path = evidence_path or evidence.EVIDENCE
    analysis, _ = report.analysed(evidence_path=path)
    _, records = evidence.read(path)
    return records, {c["id"]: (c["family"], verdict_str(c["v"])) for c in analysis["cells"]}


def fresh_oracle(cell_ids):
    """-> {cell id: {config id: oracle_status} | None}, one config oracle run per cell on its universe source (the run
    evidence.observe makes, keyed by the same configuration ids as the evidence). None: the cell is not in the
    universe, which check reports as a problem."""
    from types import SimpleNamespace
    from tools.b7_audit import evidence
    from tools.config_oracle import directives
    from tools.query_coverage import loader
    parser = loader.make_parser(loader.load_language(loader.ensure_library(loader.REPO_ROOT)))
    cells = {u.cell.id: u.cell for u in evidence.universe() if u.cell.id in cell_ids}
    out = {}
    for cid in cell_ids:
        c = cells.get(cid)
        if c is None:
            out[cid] = None
            continue
        free = tuple(sorted(c.symbols))
        out[cid] = {directives.config_id(env, free): oracle_status(SimpleNamespace(**o))
                    for env, o in evidence.observe(c, parser).oracle.items()}
    return out
