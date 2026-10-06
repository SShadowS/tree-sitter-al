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
    wrappers = names - {EXPR}          # already expanded into their hosts
    acc = {}                           # (rule, slot, edge) -> [(expr path, mechanisms, required)]
    for rule, body in rules.items():
        if rule in wrappers:
            continue
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
            sep = (prv is not None and _unwrap(prv, "")[0]["type"] == "STRING"
                   and _unwrap(prv, "")[0]["value"] in (",", ";"))
            edges = {"between": ((), False)} if repeated and sep else                     {"start": ((), False), "end": ((), False)}
            if "start" in edges and prv is not None:
                found, opt = _sibling_sym(prv, PREFIX)
                if found:
                    edges["start"] = (("operand-prefix",), not opt)
            if nxt is not None and tail_m:
                found, opt = _sibling_sym(nxt, TAIL)
                if found:
                    edges["end" if "end" in edges else "between"] = (tail_m, not opt)
            for e, (m, req) in edges.items():
                acc.setdefault((rule, slot, e), []).append((path, m, req))
    out = []
    for (r, s, e), arms in acc.items():
        if len({(m, q) for _, m, q in arms}) == 1:     # arms agree: one row
            out.append(Boundary(r, s, e, arms[0][1], arms[0][2]))
        else:                                          # a union would hide an arm without a continuation
            out += [Boundary(r, f"{s}@{p}", e, m, q) for p, m, q in arms]
    return sorted(out, key=key_of)


def _reverse_index(rules):
    rev = {}
    for name, body in rules.items():
        for s in _symbols(body):
            rev.setdefault(s, set()).add(name)
    return rev


def routes(g, target_rule):
    """Visible hosts reaching target_rule through hidden/inline rules; shortest chain per host."""
    rules, inline = g["rules"], g["inline"]
    rev = _reverse_index(rules)

    def hidden(r):
        return r.startswith("_") or r in inline

    if not hidden(target_rule):
        return [Route(target_rule, (target_rule,))]
    best, seen, queue = {}, {target_rule}, [(target_rule,)]
    while queue:
        nxt = []
        for chain in queue:                      # chain is host-side first
            r = chain[0]
            if not hidden(r):
                best.setdefault(r, chain)
                continue
            for p in sorted(rev.get(r, ())):
                if p not in seen:
                    seen.add(p)
                    nxt.append((p,) + chain)
        queue = nxt
    return sorted((Route(h, c) for h, c in best.items()), key=lambda r: r.host)


def census(g):
    """Every (key, Route) pair for occurrences and boundaries."""
    pairs = []
    for x in list(occurrences(g)) + list(boundaries(g)):
        pairs += [(key_of(x), r) for r in routes(g, x.rule)]
    return sorted(pairs, key=lambda p: (p[0], p[1].host))
