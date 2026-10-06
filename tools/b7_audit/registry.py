"""registry.tsv loader and completeness gate (spec 4)."""
from dataclasses import dataclass

ROLES = {"list-separator", "edge-separator", "fixed-separator", "terminator", "qualifier",
         "continuation", "lexical", "na"}
NEEDS_TEMPLATE = {"list-separator", "edge-separator", "fixed-separator", "terminator", "continuation"}
HOLE = "⟨HOLE⟩"
HEADER = "key\troute\trole\tfamily\ttemplate\tequiv\treason"


@dataclass(frozen=True)
class Row:
    key: str
    route_host: str
    role: str
    family: str
    template: str
    equiv: str
    reason: str


def load(path):
    rows = []
    with open(path, encoding="utf-8", newline="") as f:
        lines = [l.rstrip("\r\n") for l in f]
    for i, line in enumerate(lines):
        if not line.strip() or line.startswith("#") or line == HEADER:
            continue
        cols = line.split("\t")
        if len(cols) > 7:
            raise ValueError(f"{path}:{i + 1}: {len(cols)} columns")
        cols += [""] * (7 - len(cols))
        cols[4] = cols[4].replace("\\n", "\n")
        rows.append(Row(*cols))
    return rows


def _problem(r):
    if r.role not in ROLES:
        return f"unknown role {r.role!r}"
    if (r.role in ("na", "lexical") or r.equiv) and not r.reason.strip():
        return "reason required (na, lexical or equiv)"
    if r.role in NEEDS_TEMPLATE:
        if r.template.count(HOLE) != 1:
            return f"template needs exactly one {HOLE}"
        if not r.family.strip():
            return "family required"
    return None


def gate(pairs, rows):
    """-> (missing: [(key, Route)], stale: [Row], invalid: [(Row, why)])"""
    want = {(k, r.host) for k, r in pairs}
    have = {}
    for r in rows:
        have.setdefault((r.key, r.route_host), []).append(r)
    missing = [(k, r) for k, r in pairs if (k, r.host) not in have]
    stale = [r for r in rows if (r.key, r.route_host) not in want]
    invalid = [(r, p) for r in rows if (r.key, r.route_host) in want and (p := _problem(r))]
    invalid += [(rs[1], "duplicate row") for rs in have.values() if len(rs) > 1]
    return missing, stale, invalid
