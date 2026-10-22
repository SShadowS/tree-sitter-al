"""The region assembler: transparent expression regions (B7b-2 spec 3.1-3.2, section 7).

A region is an expression reached by a boundary edge plus everything reachable from it by
region edges (`is_region_edge`). When it contains a group (a tail, an operand prefix or an
operand group), the nesting of its binary and unary nodes is no grouping claim: in one
configuration each group is replaced by its active arm's content, or by nothing (fragment
splicing, recursively), and the flat run of atoms, unary and binary operators is regrouped
by the alc-measured ladder (`expression.compose`). A malformed run (a missing operand, a
dangling operator) is `contract-shape`: that configuration is invalid AL.

Ownership (spec 7 step 1, literal): each region is composed by exactly one invocation.
A root tail is the root expression's SIBLING in the CST (the slot is `expr, tail`), so the
host's item loop (`engine.lower_items`) hands the pair to `assemble_with_tail`, which splices
the raw root expression and the tail into one run and composes it once. Leading prefixes (spec
6.3) are the root expression's earlier siblings in the same slot and join that one item.
A root expression with no tail beside it, holding a group, is composed by `assemble` from
`engine.lower`'s root dispatch; so is an operand group that is itself the root's expression
(its registry handler). A tail with no root expression before it is contract-shape.
Every atom (a node reached by a boundary edge) is lowered by the ordinary engine first,
which assembles any inner region at its own root. Every leaf is accounted exactly once:
atoms and operators `kept` through the engine, directives `directive`, other arms
`inactive-arm`.
"""
from __future__ import annotations

from tools.config_oracle import contracts
from tools.config_oracle.lowering import expression
from tools.config_oracle.lowering.assemblers import active_arm
from tools.config_oracle.lowering.engine import Lowered, LoweringError, lower
from tools.config_oracle.lowering.select import split_arms

TAIL = "preproc_conditional_expression_tail"
PREFIX = "preproc_operand_prefix"
OPERAND_GROUP = "preproc_conditional_operand"   # Phase C (spec 6.1), with its receiver and typed variants
GROUPS = frozenset({TAIL, PREFIX, OPERAND_GROUP})
NODES = expression.BINARY_KINDS | {"unary_expression"}     # region nodes: walked, never atoms
_TYPED = frozenset({"in_expression", "is_expression", "as_expression"})


def is_region_edge(parent, child, field) -> bool:
    """Spec 3.1, exactly. Region edges: binary `left`/`right` (only `left` of in/is/as),
    `operand` of a unary, an operator child of a region node, every edge into a group (a
    prefix in its binary node, the tail beside a root's expression) and every child of a
    group. Everything else is a boundary: the typed right of in/is/as explicitly, and by this
    default every edge out of a non-region node (ternary parts, range ends, a parenthesized
    inner, list elements, call arguments, member and subscript parts), so those nodes are
    atoms of the enclosing region and their own roots (spec 5.1) assemble the inside."""
    return region_edge(parent.kind, child.kind, field)


def region_edge(parent_kind, child_kind, field) -> bool:
    if child_kind in GROUPS or parent_kind in GROUPS:
        return True
    if parent_kind in expression.BINARY_KINDS:
        return field in ("left", "operator") or (field == "right" and parent_kind not in _TYPED)
    return parent_kind == "unary_expression" and field in ("operand", "operator")


def _walk(root, parent_kind):
    """(parent kind, member, reached by region edges) for every region member under `root`,
    in source order: atoms, operator children and groups (not entered). Only a region edge
    enters a region node or makes a group the region's; behind a boundary either is an atom.
    Iterative: real chains are thousands deep."""
    out, stack = [], [(parent_kind, root, True)]
    while stack:
        pk, n, inside = stack.pop()
        if inside and n.kind in NODES:
            stack.extend((n.kind, c, is_region_edge(n, c, c.field)) for c in reversed(n.children))
        else:
            out.append((pk, n, inside))
    return out


def collect(root) -> list:
    """Region members in source order, stopping at boundaries (an atom) and at groups."""
    return [n for _, n, _ in _walk(root, None)]


def has_group(root) -> bool:
    return any(inside and n.kind in GROUPS for _, n, inside in _walk(root, None))


def _splice(members, ctx):
    """Lower a member list into the configuration's flat run."""
    run = []
    for pk, n, inside in members:
        if not n.named and n.field != "operator":
            # review N1: an anonymous token that is not an operator (`,` `;` `)` `..` `then` ...)
            # is no region atom; compose would take it as an operand (a group absorbing the
            # list's separator after its #endif composed to the bare `,` and passed).
            raise LoweringError("contract-shape", n, f"{n.kind!r} is not a region atom")
        if n.kind not in GROUPS or not inside:
            r = lower(n, ctx.child(pk, n.field or "<children>"))
            if r.frags or len(r.nodes) != 1:
                raise LoweringError("contract-shape", n, "a region atom must lower to one node")
            run += r.nodes
            continue
        ctx.child(pk, n.field or "<children>").policy(contracts.REGISTRY[n.kind], n)
        run += _group_run(n, ctx)
    return run


def _group_run(group, ctx):
    """The active arm's items, then the items after `#endif` (a root tail's trail, the B3
    form's operand), each spliced as region-reached; no arm active contributes nothing."""
    cut = next((i for i, c in enumerate(group.children) if c.kind == "preproc_endif"), None)
    if cut is None:
        raise LoweringError("contract-shape", group, "no #endif")
    arms, endif = split_arms(group.copy(children=group.children[:cut + 1]))
    run = []
    for item in list(active_arm(arms, endif, group, ctx)) + group.children[cut + 1:]:
        run += _splice(_walk(item, group.kind), ctx)
    return run


def _compose(run, field, at):
    try:
        return expression.compose(run, field)
    except ValueError as e:
        raise LoweringError("contract-shape", at, str(e)) from None


LEADING_PREFIXES = True   # mutation switch: engine.lower_items hands leading prefixes to the root


def assemble_with_tail(expr, tail, ectx, tctx, prefixes=()) -> Lowered:
    """Contract **expression-continuation**, one invocation for a root expression `expr`, the
    root tail beside it (None when there is none) and the leading prefixes before it (spec
    6.3; `tctx` is the host's `<children>` slot, where both sit). The prefixes' spliced run,
    the root's region members and the tail's spliced run are composed once by the ladder,
    keeping `expr`'s field. Groups contributing nothing leave the root lowered exactly as
    without them (the ordinary engine, or `assemble` when the root holds a group of its own).

    Property compatibility (7 step 5): **property-expression-unwrap** is applied by
    engine._lower_ordinary to the property_expression holding the tail; and **one-reading**:
    a signed literal continued by a live tail (`MinValue = -1 #if X + 2 #endif ;`). The
    scanner emits `-1` as one literal before `#`, the tail-inactive configuration's flat
    reading; where the tail is live the flat parse reads unary minus, a tokenisation no tree
    can also hold. The configuration's masked text is read only for the literal's first byte."""
    head = []
    for p in prefixes:
        tctx.policy(contracts.REGISTRY[PREFIX], p)
        head += _group_run(p, tctx)
    run = []
    if tail is not None:
        tctx.policy(contracts.REGISTRY[TAIL], tail)
        run = _group_run(tail, tctx)
    if not head and not run:
        return lower(expr, ectx)
    if (run and not expr.children and expr.kind in ("integer", "decimal")
            and ectx.resolution.masked[expr.start:expr.start + 1] == b"-"):
        raise LoweringError("one-reading", expr, "signed literal continued by a live tail")
    return Lowered([_compose(head + _splice(_walk(expr, ectx.parent_kind), ectx) + run, expr.field, expr)])


def assemble(root, ctx) -> Lowered:
    """Section 7. `root` is a region root's expression holding a group, with no tail beside
    it (engine.lower's root dispatch), or an operand group standing as the root's expression
    (the handler of `preproc_conditional_operand`, spec 6.1: also its receiver and typed
    variants, one atom per arm): the whole region is spliced and composed once, keeping the
    root's field. An operand group with no active arm leaves no operand: contract-shape, except
    as a list item (EMPTY_LIST_ITEM). A tail or a prefix reached on its own (a tail with no
    root expression before it, a prefix outside its region's root) is contract-shape."""
    if root.kind in GROUPS - {OPERAND_GROUP}:
        raise LoweringError("contract-shape", root, f"{root.kind} outside its region root ({ctx.host()})")
    run = _splice(_walk(root, ctx.parent_kind), ctx)
    if not run and EMPTY_LIST_ITEM and f"{ctx.parent_kind}:{ctx.slot}" in LIST_ITEM_SLOTS:
        ctx.normalised.append(f"empty-list-item@{root.start}")
        return Lowered([])
    return Lowered([_compose(run, root.field, root)])


# An operand group with no live arm as a list item (`Foo(1 #if X #if Y + 5 #endif , 3 #endif)` at
# X=1,Y=0) contributes no item rather than an invalid configuration: the list's own checks
# decide (engine._check_alternation refuses a stray separator, the comparison with the flat parse
# reports anything else). Contract-shape there would claim the configuration is invalid AL while
# its flat text (`Foo(1 , 3)`) is valid.
EMPTY_LIST_ITEM = True   # mutation switch for test_regions.test_empty_operand_group_list_item
LIST_ITEM_SLOTS = frozenset({"argument_list:<children>", "list_literal:<children>",
                             "preproc_conditional_arguments:<children>",
                             "preproc_conditional_list_elements:<children>"})
