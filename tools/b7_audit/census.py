"""Census of boundary-punctuation occurrences (spec 3.1) and shared audit shapes."""
from dataclasses import dataclass

from .grammar import LEXICAL, TRANSPARENT, iter_nodes

PUNCT = (",", ";", "..", ".", "::", ":")


@dataclass(frozen=True)
class Occurrence:          # 3.1
    rule: str
    path: str              # dotted member-index path inside the rule
    text: str
    context: str           # repeat | recursive | caller-repeat | optional | fixed | lexical


@dataclass(frozen=True)
class Boundary:            # 3.2
    rule: str
    slot: str              # field name, else path
    edge: str              # start | end | between
    mechanisms: tuple      # subset of ('tail', 'tail-operator-only', 'operand-prefix'), sorted
    required: bool


@dataclass(frozen=True)
class Route:               # 3.3
    host: str
    chain: tuple


def key_of(x) -> str:
    if isinstance(x, Occurrence):
        return f"occ:{x.rule}:{x.path}"
    if isinstance(x, Boundary):
        return f"bnd:{x.rule}:{x.slot}:{x.edge}"
    raise TypeError(x)


def _symbols(node):
    return {n["name"] for _, n, _ in iter_nodes(node) if n["type"] == "SYMBOL"}


def _reaches_via_hidden(rules, inline, start, target):
    """True if `start` is `target`, or a hidden/inline rule whose body reaches it the same way."""
    seen, stack = set(), [start]
    while stack:
        s = stack.pop()
        if s == target:
            return True
        if s in seen or s not in rules or not (s.startswith("_") or s in inline):
            continue
        seen.add(s)
        stack.extend(_symbols(rules[s]))
    return False


def _list_recursive(rules, inline, rule, seq, child):
    """Spec 3.1: a SYMBOL AFTER the separator reaches the rule directly or via hidden/inline rules."""
    members = seq["members"]
    k = next(i for i, m in enumerate(members) if m is child)
    return any(_reaches_via_hidden(rules, inline, s, rule)
               for m in members[k + 1:] for s in _symbols(m))


def _caller_repeat(rules):
    out = set()
    for body in rules.values():
        for _, n, anc in iter_nodes(body):
            if n["type"] == "SYMBOL" and any(a["type"] in ("REPEAT", "REPEAT1") for a in anc):
                out.add(n["name"])
    return out


def occurrences(g):
    rules = g["rules"]
    crep = _caller_repeat(rules)
    out = []
    for rule, body in rules.items():
        for path, n, anc in iter_nodes(body):
            if n["type"] != "STRING" or n["value"] not in PUNCT:
                continue
            types = [a["type"] for a in anc]
            nearest = next((a for a in reversed(anc) if a["type"] not in TRANSPARENT), None)
            si = next((i for i in range(len(anc) - 1, -1, -1) if anc[i]["type"] == "SEQ"), None)
            if any(t in LEXICAL for t in types):
                ctx = "lexical"
            elif "REPEAT" in types or "REPEAT1" in types:
                ctx = "repeat"
            elif (nearest is not None and nearest["type"] == "CHOICE"
                  and any(m["type"] == "BLANK" for m in nearest["members"])):
                ctx = "optional"
            elif si is not None and _list_recursive(
                    rules, g["inline"], rule, anc[si], anc[si + 1] if si + 1 < len(anc) else n):
                ctx = "recursive"
            elif rule in crep:
                ctx = "caller-repeat"
            else:
                ctx = "fixed"
            out.append(Occurrence(rule, path, n["value"], ctx))
    return sorted(out, key=key_of)
