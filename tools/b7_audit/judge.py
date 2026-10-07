"""Verdicts (spec 7.2) and structural assertions (7.3) over evidence records.

A record is what `evidence.measure` writes. Verdicts use alc's ACTUAL acceptance (`alc_flat`); the
intended vector only drives the class-sampled rule and the `vector_mismatch` flag.
"""
import csv
import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from tools.b7_audit import evidence

HERE = Path(__file__).parent
ASSERTIONS = HERE / "assertions.tsv"
SILENT_ORACLE = frozenset({"discrepancy", "representation-violation", "directive-mismatch"})
UNCHECKED_REP = "representative vector mismatch"
# The named node types of grammar.js `extras` (keep in sync): they may sit between any two children.
EXTRAS = frozenset({"comment", "multiline_comment", "pragma", "preproc_region", "preproc_endregion",
                    "preproc_define", "preproc_undef"})


@dataclass(frozen=True)
class Verdict:
    name: str
    detail: str = ""
    vector_mismatch: bool = False


@dataclass(frozen=True)
class Assertion:
    cell_or_class: str
    expect: str
    fingerprints: tuple      # (cell source, src/parser.c, src/scanner.c, oracle package) sha256
    reason: str
    holds: object = None     # set by the caller from check_assertion(); None = not evaluated
    recorded: str = ""       # the row's truth at its fingerprints: true / false / mixed:N/M (class row) / none


# --- fingerprints and loading ---------------------------------------------------------------------
def fingerprints(cell_sha256):
    return (cell_sha256, evidence._sha(evidence.REPO / "src" / "parser.c"),
            evidence._sha(evidence.REPO / "src" / "scanner.c"), evidence.oracle_sha256())


def _fresh(a, cell_sha, current):
    """A class row has `*` for the cell-source fingerprint (it covers many sources); the three
    grammar/oracle hashes still apply."""
    want = tuple(a.fingerprints)
    cur = current if current is not None else fingerprints(cell_sha)
    if len(want) != 4:
        return False
    return want[1:] == cur[1:] and want[0] in ("*", cur[0])


HEAD = ["cell_or_class", "expect", "fingerprints", "reason", "holds"]


def load_assertions(path=ASSERTIONS):
    lines = [l for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    rows = list(csv.reader(lines, delimiter="\t", quoting=csv.QUOTE_NONE))
    assert rows[0] == HEAD, rows[0]
    return [Assertion(c, e, tuple(f.split(",")), r, recorded=h) for c, e, f, r, h in rows[1:]]


def evaluate(assertions, entries, parse):
    """-> the truth of each row on the current parser, in row order. A cell row is judged on its cell's tree; a
    class row on every cell of its class that has no cell row of its own (report.analyse's rule): `true` / `false`
    when they agree, `mixed:<holding>/<cells>` when they do not, `none` when the row covers no cell. parse(bytes) -> root node."""
    by_id = {e.cell.id: e for e in entries}
    own = {a.cell_or_class for a in assertions if a.cell_or_class in by_id}
    members = defaultdict(list)
    for e in entries:
        if e.cell.id not in own:
            members["/".join(e.cls)].append(e.cell.id)
    todo = defaultdict(list)                              # cell id -> rows judged on its tree
    for i, a in enumerate(assertions):
        for cid in ([a.cell_or_class] if a.cell_or_class in by_id else members.get(a.cell_or_class, [])):
            todo[cid].append(i)
    seen = defaultdict(list)
    for cid, idx in todo.items():
        root = parse(by_id[cid].cell.source.encode("utf-8"))
        for i in idx:
            seen[i].append(check_assertion(root, assertions[i]))

    def truth(v):
        if not v:
            return "none"
        return "true" if all(v) else "false" if not any(v) else f"mixed:{sum(v)}/{len(v)}"
    return [truth(seen[i]) for i in range(len(assertions))]


def refresh(path, entries, parse, base=None):
    """`assert --refresh`: re-evaluate every row on the current parser; a row whose truth equals its recorded
    `holds` gets the current fingerprints (cell source, parser.c, scanner.c, oracle), a row whose truth flipped or
    whose cell source changed is listed and left alone. -> (rewritten, [problem lines]); the file is rewritten in
    place (comments and row order kept)."""
    rows = load_assertions(path)
    base = tuple(base) if base is not None else fingerprints("")[1:]
    by_id = {e.cell.id: e for e in entries}
    truth = evaluate(rows, entries, parse)
    new_fp, problems = {}, []
    for i, (a, t) in enumerate(zip(rows, truth)):
        cell = a.cell_or_class in by_id
        sha = hashlib.sha256(by_id[a.cell_or_class].cell.source.encode("utf-8")).hexdigest() if cell else "*"
        if cell and a.fingerprints[0] != sha:
            problems.append(f"source changed\t{a.cell_or_class}")
        elif t != a.recorded:
            problems.append(f"flipped {a.recorded} -> {t}\t{a.cell_or_class}")
        else:
            new_fp[i] = ",".join((sha,) + base)
    out, i = [], -2                       # -1 is the column header, 0.. the rows
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            i += 1
            if i in new_fp:
                f = line.split("\t")
                f[2] = new_fp[i]
                line = "\t".join(f)
        out.append(line)
    Path(path).write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    return len(new_fp), problems


def template_gap(row):
    """A registry row whose reason starts `TEMPLATE-GAP:` collapses all its cells into one verdict."""
    return Verdict("GAP", "template") if row.reason.startswith("TEMPLATE-GAP:") else None


# --- verdicts -------------------------------------------------------------------------------------
def _accepts(r):
    """alc's acceptance of this configuration; None when the record carries no alc verdict."""
    return None if r["alc_flat"] is None else r["alc_flat"]["verdict"] == "ACCEPT"


def _accepted(rec, assertion, cell_sha, current):
    """(verdict name, detail) for one alc-accepted configuration judged alone.

    NOTE `parser_has_error` is the split source's single parse result, shared by every configuration
    of the cell, so GAP and the REJECTED agrees/over-accepts split are identical across its configs.
    A `pass` oracle needs a fresh, holding assertion for CONSISTENT. A `cannot-validate` oracle is
    closed by a fresh assertion alone: holding -> CONSISTENT `assertion-closed: <refusal reasons>`,
    failing -> SILENT, none or stale -> UNCHECKED (controller ruling)."""
    if rec["parser_has_error"]:
        return "GAP", ""
    status = rec["oracle"]["status"]
    if status in SILENT_ORACLE:
        return "SILENT", ""
    fresh = assertion is not None and _fresh(assertion, cell_sha, current)
    if fresh and assertion.holds is False:
        return "SILENT", ""
    if fresh and assertion.holds:
        if status == "pass":
            return "CONSISTENT", ""
        if status == "cannot-validate":
            return "CONSISTENT", "assertion-closed: " + "; ".join(rec["oracle"].get("reasons") or ["?"])
    return "UNCHECKED", ""


def _rejected(rec):
    cls = rec["reject_class"]
    if rec["control"] == "none" and cls != "syntax" or cls is None:
        cls = "unverified"          # no typed control: only a syntax code decides
    return f"{cls}/{'agrees' if rec['parser_has_error'] else 'over-accepts'}"


def verdict(records, assertion, lookup=None, current=None, cls=None):
    """records: every configuration record of ONE cell. lookup(cell id) -> that cell's records (needed
    for class-sampled cells). current: the fingerprints to compare against (default: measured now).
    cls: the cell's "role/family/placement" string, which a class assertion row may name.

    All configs accepted: the worst per-config verdict wins, order GAP > SILENT > UNCHECKED > CONSISTENT.
    MIXED `detail` is the machine-readable per-config record (any GAP/SILENT inside it included)."""
    records = sorted(records, key=lambda r: r["config"])
    sha = records[0]["source_sha256"]
    if assertion is not None and assertion.cell_or_class not in (records[0]["cell"], cls):
        raise ValueError(f"assertion for {assertion.cell_or_class!r} given to cell {records[0]['cell']!r}")
    if records[0]["alc"] == "class-sampled":
        rep = (lookup or (lambda _: None))(records[0]["alc_representative"])
        if not rep or any(_accepts(r) is None for r in rep) or \
                {r["config"] for r in rep if _accepts(r)} != {r["config"] for r in rep if r["intended_valid"]}:
            return Verdict("UNCHECKED", UNCHECKED_REP)
        acc = {r["config"]: True for r in records}      # alc acceptance := intended vector (all valid)
        mismatch = False
    else:
        acc = {r["config"]: _accepts(r) for r in records}
        mismatch = any(acc[r["config"]] != r["intended_valid"] for r in records)
    subs = {r["config"]: _accepted(r, assertion, sha, current) if acc[r["config"]] else None
            for r in records}
    if all(subs.values()):
        names = {n for n, _ in subs.values()}
        for n in ("GAP", "SILENT", "UNCHECKED"):
            if n in names:
                return Verdict(n, "", mismatch)
        return Verdict("CONSISTENT", "; ".join(sorted({d for _, d in subs.values() if d})), mismatch)
    rej = {r["config"]: _rejected(r) for r in records if not acc[r["config"]]}
    if not any(subs.values()):
        kinds = sorted(set(rej.values()))
        return Verdict("REJECTED", kinds[0] if len(kinds) == 1 else ";".join(f"{c}:{k}" for c, k in sorted(rej.items())), mismatch)
    parts = [f"{c}:{subs[c][0]}" if subs[c] else f"{c}:REJECTED/{rej[c]}" for c in sorted(subs)]
    return Verdict("MIXED", ";".join(parts), mismatch)


# --- structural assertions ------------------------------------------------------------------------
def _read(text):
    """Minimal s-expression reader: `(type [field:] (child ...) ... [...])` -> (type, [(field, node)]). A type written
    `type!` keeps its `!`: the node's named children must be exactly the pattern children (no others)."""
    toks = re.findall(r"\(|\)|\.\.\.|[\w]+:|[\w]+!?", text)
    pos = 0

    def node():
        nonlocal pos
        assert toks[pos] == "(", f"expected ( in {text!r}"
        typ, kids, field = toks[pos + 1], [], None
        pos += 2
        while toks[pos] != ")":
            t = toks[pos]
            if t == "...":
                if typ.endswith("!"):
                    raise ValueError(f"`...` inside the exact pattern ({typ} ...) in {text!r}: `!` means exactly "
                                     f"these children, so nothing may be elided")
                pos += 1
            elif t.endswith(":"):
                field = t[:-1]
                pos += 1
            else:
                kids.append((field, node()))
                field = None
        pos += 1
        return typ, kids

    out = node()
    assert pos == len(toks), f"trailing tokens in {text!r}"
    return out


def _match(n, pat):
    typ, kids = pat
    exact = typ.endswith("!")                # `type!`: no named child beyond the pattern's
    typ = typ.rstrip("!")
    if typ != "_" and n.type != typ:         # `_`: any node type (a class row spanning hosts)
        return False
    have = [(n.field_name_for_child(i), c) for i, c in enumerate(n.children) if c.is_named]
    if exact:                                # extras never count against `!`
        have = [(f, c) for f, c in have if c.type not in EXTRAS]
        if len(have) != len(kids):
            return False

    def go(i, k):                       # pattern children match an in-order subsequence
        if k == len(kids):
            return True
        for j in range(i, len(have)):
            f, c = have[j]
            if kids[k][0] in (None, f) and _match(c, kids[k][1]) and go(j + 1, k + 1):
                return True
        return False
    return go(0, 0)


def check_assertion(tree_root, assertion):
    """True when some node of the split tree matches the expected fragment (type, named children in
    order, field labels where given; the type `_` matches any node)."""
    pat = _read(assertion.expect)
    stack = [tree_root]
    while stack:
        n = stack.pop()
        if _match(n, pat):
            return True
        stack.extend(n.children)
    return False
