"""The move-interior adapter (B7b-3 spec 2026-10-08 section 6.3): one lowering for the interior
`( ... )` of movefirst / movelast / moveafter / movebefore, whichever of the three routes of spec
5.1 the split tree took.

  route 1  `T ; E (, E)*`   target fielded `target`, elements `element`, element groups are
                            B7b-1's preproc_conditional_move_elements (unchanged);
  route 2  `T G ...`        the raw first name fielded `target`; every other name, inside or
                            outside a preproc_conditional_move_args group, unfielded;
  route 3  `G ...`          a group first; every name unfielded.

`lower` runs for EVERY move host (engine dispatches by host kind, never by group presence), so
a host holding only move_args groups cannot pass unvalidated. Its steps, in order:

  1. before selection, on the ORIGINAL host (`check_host`; representation.check also runs it over
     the whole tree through `validate_split`): the `( ... )` shape, the route, which node types
     and which fields each route allows (spec 5.2, checked as they stand, never relabelled),
     every move_args group's field, arms, arm containment and source order, at any depth;
  2. after selection, on the lowered children (groups spliced in source order): the interior
     must read `name ; name (, name)*`. An extra target, a duplicate `;`, a missing `;` or a bad
     comma is refused (`list-separator`), never repaired;
  3. the names' fields as they stand must be the route's (route 1 target + elements, route 2
     target + unfielded, route 3 unfielded), then and only then the configured roles are
     assigned: the first name `target`, the rest `element` (spec 5.3: on routes 2-3 a role is
     known only per configuration).

The empty element region (`T ;` after selection) never reaches step 2 in a run: flat
`moveafter(T;)` is an ERROR, so that configuration stays on the reference-error path (B7b-1
rev 2 amendment, Task 1 ruling); called directly, step 2 refuses it.
"""
from __future__ import annotations

from tools.config_oracle.lowering.engine import LoweringError

MOVE_HOSTS = ("movefirst_modification", "movelast_modification", "moveafter_modification",
              "movebefore_modification")
GROUP = "preproc_conditional_move_args"          # routes 2-3
ELEMENTS = "preproc_conditional_move_elements"   # route 1 (B7b-1; its arms: conditional_lists)
NAMES = frozenset({"identifier", "quoted_identifier"})
_DIRECTIVES = ("preproc_if", "preproc_elif", "preproc_else")


def dispatches(node):
    """The engine's dispatch predicate: by host kind. A seam for the bypass mutation test."""
    return node.kind in MOVE_HOSTS


def _tok(n, kind):
    return n.kind == kind and not n.children and n.field is None


def _sep(n):
    return _tok(n, ";") or _tok(n, ",")


def _interior(host):
    """-> the children between the host's `(` and its closing `)`, or raise contract-shape."""
    kids = host.children
    if len(kids) < 3 or not kids[0].kind.endswith("_keyword") or not _tok(kids[1], "(") \
            or not _tok(kids[-1], ")"):
        raise LoweringError("contract-shape", host, "not `keyword ( ... )`")
    return kids[2:-1]


def route(host):
    """1, 2 or 3 (spec 5.1), from the ORIGINAL host's first two interior children."""
    inner = _interior(host)
    if inner and inner[0].kind == GROUP:
        return 3
    if len(inner) >= 2 and inner[0].kind in NAMES:
        if _tok(inner[1], ";"):
            return 1
        if inner[1].kind == GROUP:
            return 2
    raise LoweringError("contract-shape", host, "interior is not `T ;`, `T #if` or `#if`")


def _order(n):
    for a, b in zip(n.children, n.children[1:]):
        if b.start < a.end:
            yield f"children out of source order or overlapping at {b.kind}@{b.start}"
    for c in n.children:
        if c.start < n.start or c.end > n.end:
            yield f"child {c.kind}@{c.start} outside its parent"


def _check_group(g):
    """A move_args group: unfielded, `#if ... #endif` arms holding unfielded names, `;`, `,` and
    nested groups only, each inside the span of its own arm, all in source order."""
    if g.field is not None:
        yield f"{g.kind}@{g.start}: fielded ({g.field})"
    yield from (f"{g.kind}@{g.start}: {p}" for p in _order(g))
    kids = g.children
    if not kids or kids[0].kind != "preproc_if" or kids[-1].kind != "preproc_endif":
        yield f"{g.kind}@{g.start}: not an #if ... #endif group"
        return
    bounds = [i for i, c in enumerate(kids) if c.kind in _DIRECTIVES or c.kind == "preproc_endif"]
    if [kids[i].kind for i in bounds].count("preproc_endif") != 1:
        yield f"{g.kind}@{g.start}: not one #endif"
    for lo, hi in zip(bounds, bounds[1:]):
        for c in kids[lo + 1:hi]:
            if c.start < kids[lo].end or c.end > kids[hi].start:
                yield f"{g.kind}@{g.start}: {c.kind}@{c.start} outside its arm"
            if c.kind == GROUP:
                yield from _check_group(c)
            elif not ((c.kind in NAMES and c.field is None) or _sep(c)):
                yield f"{g.kind}@{g.start}: arm content {c.kind}@{c.start} (field {c.field})"


def check_host(host):
    """-> problems on the ORIGINAL (multi-configuration) host, each `<kind>@<start>: <what>`."""
    where = f"{host.kind}@{host.start}"
    out = [f"{where}: {p}" for p in _order(host)]
    try:
        r, inner = route(host), _interior(host)
    except LoweringError as err:
        return out + [f"{where}: {err.detail}"]
    if inner[0].kind in NAMES and inner[0].field != "target":
        out.append(f"{where}: route {r} first name fielded {inner[0].field}, not target")
    rest = inner[2:] if r == 1 else inner[1:] if r == 2 else inner
    for c in rest:
        if r == 1:
            ok = (c.kind in NAMES and c.field == "element") or _tok(c, ",") \
                or (c.kind == ELEMENTS and c.field is None)   # its arms: conditional_lists.validate_split
        else:
            ok = (c.kind in NAMES and c.field is None) or _sep(c) or c.kind == GROUP
        if not ok:
            out.append(f"{where}: route {r} does not allow {c.kind}@{c.start} (field {c.field})")
        if c.kind == GROUP and r != 1:
            out += list(_check_group(c))
    return out


def validate_split(root):
    """-> problems over the whole tree: every move host (`check_host`) and every move_args group
    whose parent is neither a move host nor a move_args group. Iterative: real trees are deep."""
    out, stack = [], [(root, None)]
    while stack:
        n, parent = stack.pop()
        if n.kind in MOVE_HOSTS:
            out += check_host(n)
        if n.kind == GROUP and getattr(parent, "kind", None) not in (*MOVE_HOSTS, GROUP):
            out.append(f"{n.kind}@{n.start}: {getattr(parent, 'kind', None)} is not a permitted parent")
        stack.extend((c, n) for c in reversed(n.children))
    return out


def check_shape(host, inner):
    """After selection: `name ; name (, name)*`. Refused, never repaired."""
    names, seps = inner[0::2], inner[1::2]
    if not inner or not all(n.kind in NAMES for n in names) or not all(_sep(s) for s in seps):
        raise LoweringError("list-separator", host, "interior does not alternate name, separator")
    if len(inner) % 2 == 0:
        raise LoweringError("list-separator", host, "interior ends with a separator")
    if not seps or not _tok(seps[0], ";"):
        raise LoweringError("list-separator", host, "the `;` does not follow exactly one target")
    if any(not _tok(s, ",") for s in seps[1:]):
        raise LoweringError("list-separator", host, "a second `;` among the elements")


# The fields a route's names carry BEFORE role assignment (spec 5.2), first name and the rest.
_FIELDS_AS_THEY_STAND = {1: ("target", "element"), 2: ("target", None), 3: (None, None)}


def check_fields(host, r, names):
    first, rest = _FIELDS_AS_THEY_STAND[r]
    for i, n in enumerate(names):
        want = first if i == 0 else rest
        if n.field != want:
            raise LoweringError("field-policy", n, f"route {r} name fielded {n.field}, not {want}")


def roles(names):
    """The configured roles: the selected run's first name is the target, every other an element."""
    return ["target"] + ["element"] * (len(names) - 1)


def lower(node, kids, ctx):
    """-> the host's new children. `node` is the ORIGINAL host, `kids` its lowered children with
    every group already spliced in source order."""
    problems = check_host(node)
    if problems:
        raise LoweringError("contract-shape", node, problems[0])
    r = route(node)
    if len(kids) < 3 or not _tok(kids[1], "(") or not _tok(kids[-1], ")"):
        raise LoweringError("contract-shape", node, "lowered host is not `keyword ( ... )`")
    inner = kids[2:-1]
    check_shape(node, inner)
    names = inner[0::2]
    check_fields(node, r, names)
    relabel = {id(n): n.copy(field=f) for n, f in zip(names, roles(names))}
    return [relabel.get(id(c), c) for c in kids]
