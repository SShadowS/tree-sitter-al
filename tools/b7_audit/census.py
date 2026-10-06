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


def _unwrap(node, path):
    while node["type"] in TRANSPARENT:
        node, path = node["content"], f"{path}.0" if path else "0"
    return node, path


def _joining_paths(body):
    """Paths of a helper rule's STRING when it is the body, or the first/last member of its top SEQ."""
    node, path = _unwrap(body, "")
    if node["type"] != "SEQ":
        return {path}
    out = set()
    for i in (0, len(node["members"]) - 1):
        out.add(_unwrap(node["members"][i], f"{path}.{i}" if path else str(i))[1])
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
            elif rule in crep and path in _joining_paths(body):
                ctx = "caller-repeat"
            else:
                ctx = "fixed"
            out.append(Occurrence(rule, path, n["value"], ctx))
    return sorted(out, key=key_of)


TAIL, PREFIX, EXPR = "preproc_conditional_expression_tail", "preproc_operand_prefix", "_expression"


def _first_leaf(node):
    node, _ = _unwrap(node, "")
    while node["type"] == "SEQ" and node["members"]:
        node, _ = _unwrap(node["members"][0], "")
    return node


def _tail_mechanisms(rules):
    """Read the tail rule's CHOICE: a form opening with #if is the suffix form, one opening
    with the operator-arms helper is the operator-only form."""
    body = rules.get(TAIL)
    if body is None:
        return ()
    body, _ = _unwrap(body, "")
    forms = body["members"] if body["type"] == "CHOICE" else [body]
    out = set()
    for f in forms:
        h = _first_leaf(f)
        if h["type"] == "STRING" and h["value"] == "#if" or h.get("name") == "preproc_if":
            out.add("tail")
        elif h.get("name") == "_preproc_operator_arms":
            out.add("tail-operator-only")
    return tuple(sorted(out))


def _expr_names(rules):
    """_expression plus hidden rules that are only a choice of symbols one of which is such a name
    (fixpoint), e.g. `_field_source`, `_list_element` (range_expression | _expression)."""
    names, grew = {EXPR}, True
    while grew:
        grew = False
        for n, body in rules.items():
            b, _ = _unwrap(body, "")
            ms = b["members"] if b["type"] == "CHOICE" else [b]
            ms = [_unwrap(m, "")[0] for m in ms]
            if (n.startswith("_") and n not in names and all(m["type"] == "SYMBOL" for m in ms)
                    and any(m["name"] in names for m in ms)):
                names.add(n)
                grew = True
    return names


def _sibling_sym(node, name):
    """(found, optional) for a sibling that is SYMBOL name, or CHOICE[SYMBOL name, BLANK]."""
    n, _ = _unwrap(node, "")
    if n["type"] == "SYMBOL" and n["name"] == name:
        return True, False
    if n["type"] == "CHOICE" and any(m["type"] == "BLANK" for m in n["members"]):
        if any(_unwrap(m, "")[0] == {"type": "SYMBOL", "name": name} for m in n["members"]):
            return True, True
    return False, False


def boundaries(g):
    rules = g["rules"]
    names, tail_m = _expr_names(rules), _tail_mechanisms(rules)
    acc = {}
    for rule, body in rules.items():
        seen = set()
        for path, n, anc in iter_nodes(body):
            if n["type"] != "SYMBOL" or n["name"] not in names:
                continue
            slot = next((a["name"] for a in reversed(anc) if a["type"] == "FIELD"), path)
            repeated = any(a["type"] in ("REPEAT", "REPEAT1") for a in anc)
            i, cur = len(anc), n
            while i > 0 and anc[i - 1]["type"] in TRANSPARENT | {"CHOICE"}:
                i -= 1
                cur = anc[i]
            sibs = anc[i - 1]["members"] if i > 0 and anc[i - 1]["type"] == "SEQ" else []
            k = next((j for j, m in enumerate(sibs) if m is cur), None)
            nxt = sibs[k + 1] if k is not None and k + 1 < len(sibs) else None
            prv = sibs[k - 1] if k else None
            edges = {}
            if slot in seen and repeated:
                edges["between"] = ((), False)
            else:
                edges["start"] = ((), False)
                edges["end"] = ((), False)
                if prv is not None and _sibling_sym(prv, PREFIX)[0]:
                    edges["start"] = (("operand-prefix",), not _sibling_sym(prv, PREFIX)[1])
            if nxt is not None and "end" in edges or nxt is not None and "between" in edges:
                found, opt = _sibling_sym(nxt, TAIL)
                if found and tail_m:
                    edges["end" if "end" in edges else "between"] = (tail_m, not opt)
            seen.add(slot)
            for e, (m, req) in edges.items():
                key = (rule, slot, e)
                if key in acc:           # same slot in several arms: union, required only if all are
                    pm, preq = acc[key]
                    acc[key] = (tuple(sorted(set(pm) | set(m))), preq and req)
                else:
                    acc[key] = (m, req)
    return sorted((Boundary(r, s, e, m, q) for (r, s, e), (m, q) in acc.items()), key=key_of)
