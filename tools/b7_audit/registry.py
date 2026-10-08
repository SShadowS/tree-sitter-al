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


ALIAS_HEADER = "retired_key\tlive_key\trole\tfamily\treason\tcommit"


@dataclass(frozen=True)
class Alias:
    """A census key whose grammar path moved or whose owner changed (B7b-3 Task 4 ruling): the registry rows
    and every frozen cell id stay under `retired`; the separator they measure is now `live`."""
    retired: str
    live: str
    role: str
    family: str
    reason: str
    commit: str


def load_aliases(path):
    try:
        with open(path, encoding="utf-8", newline="") as f:
            lines = [l.rstrip("\r\n") for l in f]
    except FileNotFoundError:
        return []
    body = [(i, l) for i, l in enumerate(lines) if l.strip() and not l.startswith("#")]
    if not body or body[0][1] != ALIAS_HEADER:
        raise ValueError(f"{path}: missing or wrong header line")
    out = []
    for i, l in body[1:]:
        cols = l.split("\t")
        if len(cols) != 6 or not all(c.strip() for c in cols):
            raise ValueError(f"{path}:{i + 1}: an alias needs 6 non-empty columns")
        out.append(Alias(*cols))
    return out


def _alias_problem(a, rows, live_keys):
    """None when `a` may stand in for its retired rows: the retired key is gone from the grammar, the live key is
    present; the alias's role and family are the retired rows' (`na` rows exempt from the role, but at least one
    retired row has the role); the live key's
    registry rows have the same role (or `na`) and
    cover only hosts the retired rows covered (so every live host has frozen cells). The live rows' family is not
    compared: an owner change moves a `;` into another family (the split call's `;` is now a statement terminator)."""
    if a.retired in live_keys:
        return f"retired key {a.retired} is still in the grammar"
    if a.live not in live_keys:
        return f"live key {a.live} is not in the grammar"
    old = [r for r in rows if r.key == a.retired]
    new = [r for r in rows if r.key == a.live]
    if not old:
        return f"no registry row under {a.retired}"
    # An `na` row (a host where no valid AL places the construct) carries no role of the separator, so it is
    # exempt from the role comparison on both sides (B7b-3 Task 8: the move keys have na rows); its family is not.
    if any((r.role != a.role and r.role != "na") or r.family != a.family for r in old):
        return f"role/family of {a.retired}'s rows differ from the alias ({a.role}/{a.family})"
    if not any(r.role == a.role for r in old):     # mirrors the live side: na rows alone carry no role
        return f"{a.retired} has no registry row with role {a.role}"
    if not any(r.role == a.role for r in new) or any(r.role not in (a.role, "na") for r in new):
        return f"{a.live} has no registry row with role {a.role}"
    extra = {h for r in new for h in r.hosts} - {h for r in old for h in r.hosts}
    if extra:
        return f"{a.live} covers hosts {sorted(extra)} that {a.retired} never covered"
    return None


def gate(pairs, rows, aliases=()):
    """A row's route column is an explicit comma-separated host list (first = witness).
    A row under a retired key is not stale when a valid alias (key-aliases.tsv) maps it to a live key.
    -> (missing: [(key, Route)], stale: [Row], invalid: [(Row, why)])"""
    want = {(k, r.host) for k, r in pairs}
    cover = {}
    for r in rows:
        for h in r.hosts:
            cover.setdefault((r.key, h), []).append(r)
    missing = [(k, r) for k, r in pairs if (k, r.host) not in cover]
    stale = [r for r in rows if not r.hosts or any((r.key, h) not in want for h in r.hosts)]
    live_keys = {k for k, _ in pairs}
    alias_invalid = []
    for a in aliases:
        why = _alias_problem(a, rows, live_keys)
        if why is None:
            stale = [r for r in stale if r.key != a.retired]
        else:
            alias_invalid.append((Row(a.retired, "", a.role, a.family, "", a.live, a.reason), "alias: " + why))
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
    return missing, stale, invalid + alias_invalid
