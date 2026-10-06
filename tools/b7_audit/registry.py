"""registry.tsv loader and completeness gate (spec 4)."""
from dataclasses import dataclass

ROLES = {"list-separator", "edge-separator", "fixed-separator", "terminator", "qualifier",
         "continuation", "lexical", "na"}
NEEDS_TEMPLATE = {"list-separator", "edge-separator", "fixed-separator", "terminator", "continuation"}
HOLE = "⟨HOLE⟩"
HEADER = "key\troute\trole\tfamily\ttemplate\tequiv\treason\tplain"


@dataclass(frozen=True)
class Row:
    key: str
    route_host: str
    role: str
    family: str
    template: str
    equiv: str
    reason: str
    plain: str = ""          # the directive-free valid filling of the hole (required with a template)

    @property
    def hosts(self):
        return tuple(h.strip() for h in self.route_host.split(",") if h.strip())

    @property
    def witness(self):
        return self.hosts[0] if self.hosts else ""


def load(path):
    rows = []
    with open(path, encoding="utf-8", newline="") as f:
        lines = [l.rstrip("\r\n") for l in f]
    body = [(i, l) for i, l in enumerate(lines) if l.strip() and not l.startswith("#")]
    if not body or body[0][1] != HEADER:
        raise ValueError(f"{path}: missing or wrong header line")
    for i, line in body[1:]:
        cols = line.split("\t")
        if len(cols) > 8:
            raise ValueError(f"{path}:{i + 1}: {len(cols)} columns")
        cols += [""] * (8 - len(cols))
        cols[4] = cols[4].replace("\\n", "\n")
        cols[7] = cols[7].replace("\\n", "\n")
        rows.append(Row(*cols))
    return rows


def _problem(r):
    if r.role not in ROLES:
        return f"unknown role {r.role!r}"
    if (r.role in ("na", "lexical") or r.equiv or len(r.hosts) > 1) and not r.reason.strip():
        return "reason required (na, lexical, equiv or multi-host)"
    if r.role in NEEDS_TEMPLATE:
        if r.template.count(HOLE) != 1:
            return f"template needs exactly one {HOLE}"
        if not r.family.strip():
            return "family required"
        if not r.plain.strip():
            return "plain filling required for a templated row"
    return None


def gate(pairs, rows):
    """A row's route column is an explicit comma-separated host list (first = witness).
    -> (missing: [(key, Route)], stale: [Row], invalid: [(Row, why)])"""
    want = {(k, r.host) for k, r in pairs}
    cover = {}
    for r in rows:
        for h in r.hosts:
            cover.setdefault((r.key, h), []).append(r)
    missing = [(k, r) for k, r in pairs if (k, r.host) not in cover]
    stale = [r for r in rows if not r.hosts or any((r.key, h) not in want for h in r.hosts)]
    invalid, seen = [], set()
    for r in rows:
        if r in stale:
            continue
        p = _problem(r)
        if p:
            invalid.append((r, p))
    for (k, h), rs in cover.items():
        if len(rs) > 1 and (k, h) in want:
            invalid.append((rs[1], f"duplicate cover of {h}"))
    return missing, stale, invalid
