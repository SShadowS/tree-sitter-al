"""Verdicts (spec 7.2) and structural assertions (7.3) over evidence records.

A record is what `evidence.measure` writes. Verdicts use alc's ACTUAL acceptance (`alc_flat`); the
intended vector only drives the class-sampled rule and the `vector_mismatch` flag.
"""
import csv
import re
from dataclasses import dataclass
from pathlib import Path

from tools.b7_audit import evidence

HERE = Path(__file__).parent
ASSERTIONS = HERE / "assertions.tsv"
SILENT_ORACLE = frozenset({"discrepancy", "representation-violation", "directive-mismatch"})
UNCHECKED_REP = "representative vector mismatch"


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


def load_assertions(path=ASSERTIONS):
    lines = [l for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    rows = list(csv.reader(lines, delimiter="\t"))
    assert rows[0] == ["cell_or_class", "expect", "fingerprints", "reason"], rows[0]
    return [Assertion(c, e, tuple(f.split(",")), r) for c, e, f, r in rows[1:]]


def template_gap(row):
    """A registry row whose reason starts `TEMPLATE-GAP:` collapses all its cells into one verdict."""
    return Verdict("GAP", "template") if row.reason.startswith("TEMPLATE-GAP:") else None


# --- verdicts -------------------------------------------------------------------------------------
def _accepts(r):
    return r["alc_flat"]["verdict"] == "ACCEPT"


def _accepted(rec, assertion, cell_sha, current):
    """Verdict name for one alc-accepted configuration judged alone."""
    if rec["parser_has_error"]:
        return "GAP"
    status = rec["oracle"]["status"]
    if status in SILENT_ORACLE:
        return "SILENT"
    ok = assertion is not None and _fresh(assertion, cell_sha, current)
    if ok and assertion.holds is False:
        return "SILENT"
    if status == "pass" and ok and assertion.holds:
        return "CONSISTENT"
    return "UNCHECKED"


def _rejected(rec):
    cls = rec["reject_class"]
    if rec["control"] == "none" and cls != "syntax":
        cls = "unverified"          # no typed control: only a syntax code decides
    return f"{cls}/{'agrees' if rec['parser_has_error'] else 'over-accepts'}"


def verdict(records, assertion, lookup=None, current=None):
    """records: every configuration record of ONE cell. lookup(cell id) -> that cell's records (needed
    for class-sampled cells). current: the fingerprints to compare against (default: measured now)."""
    records = sorted(records, key=lambda r: r["config"])
    sha = records[0]["source_sha256"]
    if records[0]["alc"] == "class-sampled":
        rep = (lookup or (lambda _: None))(records[0]["alc_representative"])
        if not rep or {r["config"] for r in rep if _accepts(r)} != {r["config"] for r in rep if r["intended_valid"]}:
            return Verdict("UNCHECKED", UNCHECKED_REP)
        acc = {r["config"]: True for r in records}      # alc acceptance := intended vector (all valid)
        mismatch = False
    else:
        acc = {r["config"]: _accepts(r) for r in records}
        mismatch = any(acc[r["config"]] != r["intended_valid"] for r in records)
    subs = {r["config"]: _accepted(r, assertion, sha, current) if acc[r["config"]] else None
            for r in records}
    if all(subs.values()):
        names = set(subs.values())
        for n in ("GAP", "SILENT", "UNCHECKED"):
            if n in names:
                return Verdict(n, "", mismatch)
        return Verdict("CONSISTENT", "", mismatch)
    rej = {r["config"]: _rejected(r) for r in records if not acc[r["config"]]}
    if not any(subs.values()):
        kinds = sorted(set(rej.values()))
        return Verdict("REJECTED", kinds[0] if len(kinds) == 1 else ";".join(f"{c}:{k}" for c, k in sorted(rej.items())), mismatch)
    parts = [f"{c}:{subs[c]}" if subs[c] else f"{c}:REJECTED/{rej[c]}" for c in sorted(subs)]
    return Verdict("MIXED", ";".join(parts), mismatch)


# --- structural assertions ------------------------------------------------------------------------
def _read(text):
    """Minimal s-expression reader: `(type [field:] (child ...) ... [...])` -> (type, [(field, node)])."""
    toks = re.findall(r"\(|\)|\.\.\.|[\w]+:|[\w]+", text)
    pos = 0

    def node():
        nonlocal pos
        assert toks[pos] == "(", f"expected ( in {text!r}"
        typ, kids, field = toks[pos + 1], [], None
        pos += 2
        while toks[pos] != ")":
            t = toks[pos]
            if t == "...":
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
    if n.type != typ:
        return False
    have = [(n.field_name_for_child(i), c) for i, c in enumerate(n.children) if c.is_named]

    def go(i, k):                       # pattern children match an in-order subsequence
        if k == len(kids):
            return True
        for j in range(i, len(have)):
            f, c = have[j]
            if kids[k][0] in (None, f) and _match(c, kids[k][1]) and go(j + 1, k + 1):
                return True
        return False
    return go(0, 0)


def check_assertion(tree_root, source, assertion):
    """True when some node of the split tree matches the expected fragment (type, named children in
    order, field labels where given)."""
    pat = _read(assertion.expect)
    stack = [tree_root]
    while stack:
        n = stack.pop()
        if _match(n, pat):
            return True
        stack.extend(n.children)
    return False
