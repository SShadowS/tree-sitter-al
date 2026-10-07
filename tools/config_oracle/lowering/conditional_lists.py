"""Family-schema registry for strict conditional lists (B7b-1 spec 2026-10-07 section 6).

A strict list family F is a host list written with the grammar's `strictListBody` and
the group node `preproc_conditional_F` (grammar.js `strictConditionalList`). The group's
own lowering is ordinary branch selection: `select.branch_select` under the host policy
`strict-list` splices the chosen arm's items AND separators into the host, in order
(contracts.py registers every family that way). This module owns the two checks that
make that splice sound, and nothing else:

  * `validate_split(root)` (section 6.1), BEFORE selection, on the multi-configuration
    tree. `representation.check` calls it, so a problem makes every configuration of the
    input a `representation-violation` (never classifiable). Each group sits only in a
    permitted parent (a host, or its own kind), is unfielded, lies inside the region of its
    nearest host and inside the arm that holds it; its arms hold only fielded items,
    separators and its own groups; the children of every group, and of every node holding
    a group, are in source order, disjoint and inside their parent.
  * `lower_region(host, kids, family)` (sections 6.3, 6.4), AFTER selection, on
    the host's lowered children: the complete region must read `item (sep item)*`. A
    selected arm may contribute a leading separator, a trailing one or a separator alone;
    only the reconstructed whole is judged. This replaces engine._check_alternation for
    these families (that one skips brackets anywhere, takes any non-comma as an item and
    drops a trailing `;`), which keeps its behaviour for the list-run families.
    **Empty policy (controller ruling, Task 5 fix round 1): an emptied region lowers by
    the FLAT GRAMMAR, never by alc's cardinality.** A configuration whose flat text does
    not parse never reaches lowering (the runner stops at reference-error, classified
    invalid-config). Otherwise the region is lowered structurally and the comparison with
    the flat parse decides: a host with other children (a keyword, its delimiters) keeps
    them with an empty region; a host that owns nothing besides the list is removed, `[]`
    is returned and engine._lower_ordinary records the named rewrite
    **optional-list-removed:<kind>** (a normalisation note, like removed-empty).

How a later task registers a family: see the comment above FAMILIES.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from tools.config_oracle.ir import Node
from tools.config_oracle.lowering.engine import LoweringError
from tools.config_oracle.lowering.select import DIRECTIVES

CARDINALITIES = frozenset({"empty-interior", "optional-wrapper", "empty-syntax-rejected",
                           "empty-semantic-rejected"})
_ARM_BOUNDS = (*DIRECTIVES, "preproc_endif")


@dataclass(frozen=True)
class Family:
    """`region(host) -> (start, end)`: the byte span of the host that is the list (the host
    may own delimiters or a keyword before it, which lie outside). `cardinality` is the
    alc evidence recorded in the manifest (`tools/b7_audit/b7b1-manifest.tsv`, column
    `cardinality`), in its vocabulary; it has NO effect on lowering, which follows the
    flat grammar (module docstring). Where a family's routes differ, the manifest holds
    the per-route values and this field the family's most common one."""
    name: str
    host_kinds: frozenset
    region: Callable[[Node], tuple]
    item_kinds: frozenset
    sep: str
    item_field: str | None
    cardinality: str

    def __post_init__(self):
        if self.cardinality not in CARDINALITIES:
            raise ValueError(f"family {self.name}: cardinality {self.cardinality!r} not in {sorted(CARDINALITIES)}")

    @property
    def group(self):
        return f"preproc_conditional_{self.name}"


def after_child(kind):
    """Region adapter: the host's span after its first child of `kind` (a keyword or an
    opening delimiter the host owns)."""
    def region(host):
        head = next((c for c in host.children if c.kind == kind), None)
        if head is None:
            raise LoweringError("contract-shape", host, f"no {kind} to start the list region")
        return head.end, host.end
    return region


def paren_after(*kinds):
    """Region adapter: the interior of the `( ... )` that directly follows the host's first
    child of one of `kinds` (a keyword), up to the first `)` after it. For hosts whose
    parentheses are followed by more of the host (sorting_value's order( )/where( )
    suffixes), which after_child would take in."""
    def region(host):
        kids = host.children
        i = next((k for k, c in enumerate(kids) if c.kind in kinds), None)
        if i is None or i + 1 >= len(kids) or kids[i + 1].kind != "(":
            raise LoweringError("contract-shape", host, f"no {'/'.join(kinds)} ( to start the list region")
        close = next((c for c in kids[i + 2:] if c.kind == ")"), None)
        if close is None:
            raise LoweringError("contract-shape", host, "no ) to end the list region")
        return kids[i + 1].end, close.start
    return region


def between_children(open_kind, close_kind):
    """Region adapter: from the end of the host's first direct child of `open_kind` to the
    start of its last direct child of `close_kind`. For move*: the element list lies
    between the fixed `;` and the closing `)`, with the target before it outside."""
    def region(host):
        opener = next((c for c in host.children if c.kind == open_kind), None)
        closer = next((c for c in reversed(host.children) if c.kind == close_kind), None)
        if opener is None or closer is None or closer.start < opener.end:
            raise LoweringError("contract-shape", host, f"no {open_kind} ... {close_kind} list region")
        return opener.end, closer.start
    return region


def before_child(kind):
    """Region adapter: from the host's start to the start of its first direct child of
    `kind`. For variable_declaration: the name list is everything before the `:`."""
    def region(host):
        closer = next((c for c in host.children if c.kind == kind), None)
        if closer is None:
            raise LoweringError("contract-shape", host, f"no {kind} to end the list region")
        return host.start, closer.start
    return region


# Registering family F (Tasks 6-11):
#   1. FAMILIES: Family(name F, host_kinds = every rule that inlines strictListBody(F),
#      region adapter, item_kinds = the visible kinds of the atom, sep, item_field = the
#      atom's field (None when the host is unfielded), cardinality = the manifest's
#      `cardinality` evidence (no effect on lowering)). An emptied region needs nothing:
#      lowering follows the flat grammar (the host keeps its other children, or is
#      removed with optional-list-removed:<kind> when it owns nothing else), and a
#      configuration whose flat parse errors stays on the reference-error path.
#   2. contracts.py: register(preproc_conditional_F, "branch-select", select.branch_select,
#      hosts = "<host>:<children>" -> "strict-list" for every host plus the group itself,
#      arm = item_kinds | {sep, group}). test_contracts_entries_agree_with_the_families
#      fails when the two disagree, and contracts.census when a host slot is missing.
#   3. A LOWERED test over the family's focused fixture (test_conditional_lists.py layer 1),
#      and retire the family's debt(B7) rows in fixture-classes.tsv.
FAMILIES: dict[str, Family] = {f.name: f for f in (
    # implements_clause: `implements_keyword` then the list; alc rejects an empty list on
    # every route (AL0107, manifest), so an emptied configuration is a reference-error.
    Family("implements", frozenset({"implements_clause"}), after_child("implements_keyword"),
           frozenset({"identifier", "quoted_identifier"}), ",", "interface", "empty-syntax-rejected"),
    # field_list (keys, fieldgroups, addlast/addfirst, split key headers): a visible host that
    # owns nothing but the list, unfielded items. Routes differ in alc's empty verdict
    # (manifest): addlast is `empty-interior` (its field_list is optional, so an emptied
    # addlast configuration lowers by removing field_list: optional-list-removed:field_list);
    # key, fieldgroup and split key are `empty-semantic-rejected` (AL0306; flat `key(PK; )`
    # does not parse, so that configuration is a reference-error). Recorded here: the
    # value of three of the four routes. addfirst is excluded (alc has no addfirst in fieldgroups).
    Family("field_list_items", frozenset({"field_list"}), lambda h: (h.start, h.end),
           frozenset({"identifier", "quoted_identifier"}), ",", None, "empty-semantic-rejected"),
    # sorting_value: only the list inside `sorting( ... )`; the order( ) and where( )
    # suffixes lie outside the region. Unfielded items. alc accepts `sorting()` on all six
    # routes (manifest `empty-interior`), and so does the flat grammar (its own arm), so an
    # emptied configuration keeps the keyword and both parentheses.
    Family("sorting_fields", frozenset({"sorting_value"}), paren_after("sorting_keyword"),
           frozenset({"identifier", "quoted_identifier"}), ",", None, "empty-interior"),
    # order_by_item: the list inside `ascending( ... )` / `descending( ... )`; the outer
    # order_by_list is excluded (property-value routing). alc accepts `ascending()`
    # (manifest `empty-interior`), parsed flat as an order_by_item with an empty interior.
    Family("order_by_fields", frozenset({"order_by_item"}), paren_after("ascending_keyword", "descending_keyword"),
           frozenset({"identifier", "quoted_identifier"}), ",", None, "empty-interior"),
    # moveafter/movebefore/movefirst/movelast (grammar.js moveArgs): only the element list
    # after the fixed `;`; the target and the `;` lie outside (spec rev 2, a group there is
    # B7b-3). Items fielded `element`. alc rejects an empty element list semantically
    # (AL0319, manifest `empty-semantic-rejected` on every move route) and the flat grammar
    # requires an element, so an emptied configuration is a reference-error.
    Family("move_elements", frozenset({"moveafter_modification", "movebefore_modification",
                                       "movefirst_modification", "movelast_modification"}),
           between_children(";", ")"), frozenset({"identifier", "quoted_identifier"}), ",", "element",
           "empty-semantic-rejected"),
    # array_type (array[...] of T): the dimension list between the host's own `[` and `]`
    # (an element type's `Text[30]` brackets sit inside element_type, not as direct children).
    # Items fielded `sizes`. alc rejects an empty dimension list semantically (AL0367,
    # manifest `empty-semantic-rejected`) and the flat grammar requires a dimension, so an
    # emptied configuration is a reference-error.
    Family("array_dimensions", frozenset({"array_type"}), between_children("[", "]"),
           frozenset({"integer"}), ",", "sizes", "empty-semantic-rejected"),
    # attribute_argument_list ([Attr(a, b)]): a visible unfielded host that owns nothing but
    # the list; `(` and `)` belong to attribute_arguments, whose optional(...) wrapper means an
    # emptied configuration flat-parses as `[A()]` with no host, so lowering removes it
    # (optional-list-removed:attribute_argument_list, spec 4.2 case 2). Items are the visible
    # kinds of _attribute_argument (member_expression too: the grammar accepts it, alc rejects
    # it with AL0242). Cardinality = the manifest value on the only route; alc still rejects
    # some emptied configurations semantically (AL0238, wrong argument count for the attribute).
    Family("attribute_args", frozenset({"attribute_argument_list"}), lambda h: (h.start, h.end),
           frozenset({"boolean", "integer", "string_literal", "identifier", "quoted_identifier",
                      "qualified_enum_value", "database_reference", "member_expression"}),
           ",", None, "optional-wrapper"),
    # variable_declaration (A, B: T;): the names before the declaration's first `:`; the
    # type, a label's value and attributes, a TextConst's ml_value_list and the `;` lie
    # after it. Items fielded `name`. alc rejects an empty name list as syntax (AL0104/
    # AL0198, manifest `empty-syntax-rejected` on all three routes) and the flat grammar
    # requires a name, so an emptied configuration is a reference-error. The label and
    # TextConst arms take one plain name, never a group.
    Family("var_names", frozenset({"variable_declaration"}), before_child(":"),
           frozenset({"identifier", "quoted_identifier"}), ",", "name", "empty-syntax-rejected"),
)}

GROUP_FAMILY = {f.group: f for f in FAMILIES.values()}
HOST_FAMILY = {}
for _f in FAMILIES.values():
    for _h in _f.host_kinds:
        if _h in HOST_FAMILY:
            raise ValueError(f"host {_h} belongs to two families: {HOST_FAMILY[_h].name}, {_f.name}")
        HOST_FAMILY[_h] = _f


def _is_sep(node, fam):
    return node.kind == fam.sep and not node.children


def _is_item(node, fam):
    return node.kind in fam.item_kinds and node.field == fam.item_field


def lower_region(host, kids, family):
    """-> the host's new children: `kids` itself, or `[]` when the region is empty and the
    host owns nothing else (it is then removed, optional-list-removed:<kind>). `host` is
    the ORIGINAL host (its region), `kids` its lowered children with every group already
    spliced. Raises list-item, list-separator or contract-shape."""
    lo, hi = family.region(host)
    region = []
    for c in kids:
        if lo <= c.start and c.end <= hi:
            region.append(c)
        elif c.start < hi and c.end > lo:
            raise LoweringError("contract-shape", c, f"straddles the {family.name} list region")
    if not region:
        return kids     # the flat grammar's empty form; [] removes the host
    want_item = True
    for c in region:
        is_sep = _is_sep(c, family)
        if not is_sep and not _is_item(c, family):
            raise LoweringError("list-item", c, f"not a {family.name} item or separator")
        if is_sep == want_item:
            raise LoweringError("list-separator", host, "list does not alternate item, separator")
        want_item = not want_item
    if want_item:
        raise LoweringError("list-separator", host, "list ends with a separator")
    return kids


def validate_split(root):
    """-> problems, each `<kind>@<start>: <what>`. Iterative: real trees are deep."""
    out = []
    stack = [(root, None, ())]   # node, parent, enclosing host nodes (outermost first)
    while stack:
        n, parent, hosts = stack.pop()
        fam = GROUP_FAMILY.get(n.kind)
        if fam is not None:
            out += [f"{n.kind}@{n.start}: {p}" for p in _check_group(n, parent, hosts, fam)]
        if fam is not None or any(c.kind in GROUP_FAMILY for c in n.children):
            out += [f"{n.kind}@{n.start}: {p}" for p in _check_order(n)]
        inner = hosts + (n,) if n.kind in HOST_FAMILY else hosts
        stack.extend((c, n, inner) for c in reversed(n.children))
    return out


def _check_group(n, parent, hosts, fam):
    if n.field is not None:
        yield f"fielded ({n.field})"
    if parent is None or not (parent.kind in fam.host_kinds or parent.kind == fam.group):
        yield f"{getattr(parent, 'kind', None)} is not a permitted parent"
    host = next((h for h in reversed(hosts) if h.kind in fam.host_kinds), None)
    if host is None:
        yield f"no enclosing {fam.name} host"
    else:
        lo, hi = fam.region(host)
        if not (lo <= n.start and n.end <= hi):
            yield f"outside the list region of {host.kind}@{host.start}"
    if parent is not None and parent.kind == fam.group:
        i = next(k for k, c in enumerate(parent.children) if c is n)
        prev = next((c for c in reversed(parent.children[:i]) if c.kind in DIRECTIVES), None)
        nxt = next((c for c in parent.children[i + 1:] if c.kind in _ARM_BOUNDS), None)
        if prev is None or n.start < prev.end or (nxt is not None and n.end > nxt.start):
            yield f"outside its arm ({getattr(prev, 'kind', None)}@{getattr(prev, 'start', None)})"
    for c in n.children:
        if c.kind in _ARM_BOUNDS or _is_sep(c, fam) or _is_item(c, fam) or c.kind == fam.group:
            continue
        yield f"arm content {c.kind}@{c.start} (field {c.field})"


def _check_order(n):
    for a, b in zip(n.children, n.children[1:]):
        if b.start < a.end:
            yield f"children out of source order or overlapping at {b.kind}@{b.start}"
    for c in n.children:
        if c.start < n.start or c.end > n.end:
            yield f"child {c.kind}@{c.start} outside its parent"
