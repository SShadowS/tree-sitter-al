"""Recursive lowering of the multi-configuration IR to one configuration (spec section 3).

Rules that are load-bearing:
  * no default handler -- an unregistered special node fails;
  * every leaf of the ORIGINAL tree is accounted exactly once, and exactly the
    leaves accounted `kept` are emitted;
  * a fragment may only pass up through a node when the child it came from is
    that node's last original child, and must be consumed by a named consumer;
  * the normalisations are removing an EMPTY_REMOVABLE container that lowering
    emptied, arm-terminator, empty-body-terminator and orphan-terminator
    (absorb_arm_terminators, statement runs; B7b-3 Task 10 added the last two) and
    case-terminator-attach (case_terminators.attach, case bodies). (Unwrapping a continued
    property value is not one: it is a named rewrite of contract
    expression-continuation, see regions.assemble_with_tail.)

Lowering only selects and relabels. It never sees the reference parse (this
package imports nothing from reference.py, tree_sitter, or the loader).
"""
from __future__ import annotations

import collections
from dataclasses import dataclass, field

from tools.config_oracle import contracts
from tools.config_oracle.compare import _run_with_deep_stack
from tools.config_oracle.ir import Node, recompute_span

# Content-only containers the grammar wraps in optional(field(...)) (spec section 2).
EMPTY_REMOVABLE = {
    "statement_block",   # code_block: optional(field('body', $.statement_block))
    "declaration_body",  # _declaration_body_block: optional(field('body', $.declaration_body))
    "var_body",          # var_section: optional(field('body', $.var_body))
    "case_body",         # case_statement: optional(field('body', $.case_body))
    # dataset_section: optional(field('body', $.dataset_body)) (grammar.js:2664).
    "dataset_body",
    # _layout_container_body_block, shared by group/repeater/cuegroup/fixed/grid_section,
    # and preproc_split_container_reopen (both branches): optional(field('body',
    # $.layout_container_body)) (grammar.js:4687, 4708, 4710).
    "layout_container_body",
    # Added with Task 5's fields/keys/fieldgroups branch-select: each section
    # wraps its body the same single-site way, and a config that empties the
    # whole section (BC.History-shaped: nested_preproc_fields_keys_test.txt,
    # keys_body left empty by C28=0,S31=1 / C28=1,S31=1) hit the same
    # false-negative empty-node gap dataset_body/layout_container_body did.
    "fields_body",        # fields_section: optional(field('body', $.fields_body)) (grammar.js:1646-1651)
    "keys_body",          # keys_section: optional(field('body', $.keys_body)) (grammar.js:1718-1723)
    "fieldgroups_body",   # fieldgroups_section: optional(field('body', $.fieldgroups_body)) (grammar.js:1780-1785)
    # Added with Task 6's query branch-select: same single-site shape, found the
    # same way (a witness config emptying the dataitem's body raised empty-node).
    "query_body",         # query_dataitem: optional(field('body', $.query_body)) (grammar.js:2860-2870)
    # Added with Task 18's production run (22 + 3 configurations): an area whose
    # only actions, or a layout whose only elements, sit inside the #if. Every
    # site is optional(field('body', ...)): _action_body_block (the sole
    # action_body site), and layout_section, area_section and the four
    # add*_modification rules for layout_body.
    "action_body",
    "layout_body",
    # xmlport element: optional(field('body', $.xmlport_body)), its only site; the
    # quick tier's xmlport_preprocessor_elements_test.txt empties one.
    "xmlport_body",
}

STATEMENT_HOSTS = {"statement_block", "case_branch"}
LAYOUT_HOSTS = {"layout_body", "layout_container_body"}

# Special types lowered under the list-run policy (select.branch_select): their
# host list is checked for item/separator alternation once it is rebuilt.
LIST_RUN_TYPES = frozenset({"preproc_conditional_permissions", "preproc_conditional_arguments",
                            "preproc_conditional_list_elements", "preproc_conditional_option_members",
                            "preproc_conditional_where", "preproc_conditional_link_values",
                            "preproc_conditional_impl_values"})
# Lists a list family can leave empty at an optional value site (B11 spec 5.3).
LIST_VALUE_EMPTY_KINDS = frozenset({"link_value_list", "implementation_value_list", "option_member_list"})
_BRACKETS = {"(", ")", "[", "]"}


class LoweringError(Exception):
    def __init__(self, kind, node, detail=""):
        super().__init__(f"{kind} at {node.kind}@{node.start}{': ' + detail if detail else ''}")
        self.kind, self.node, self.detail = kind, node, detail


@dataclass
class Frag:
    anchor: Node | None


@dataclass
class Terminator(Frag):
    leaf: Node


@dataclass
class Following(Frag):
    statements: list


@dataclass
class BlockCompletion(Frag):
    statements: list
    end: Node


@dataclass
class ElseAttachment(Frag):
    else_kw: Node
    branch: Node


@dataclass
class SiblingsAfter(Frag):
    """Nodes that become SIBLINGS right after the anchor in its layout body
    (produced by assemblers.container_reopen, named rewrite container-reopen)."""
    nodes: list


@dataclass
class RelationContinuation(Frag):
    """Contract **else-relation-join** (produced by assemblers.table_relation_select).
    The owning `table_relation_value` consumes it: in its preceding `table_relation_expression`
    child (the conditional is that child's next sibling, grammar finding G1), follow `if_table_relation` -> `else_relation: table_relation_expression` ->
    `if_table_relation` down to the deepest `if_table_relation` with no `else_keyword`,
    append `else_kw` and `relation` (field `else_relation`) as its last two children,
    and recompute the span of every node on that path. No other edge changes."""
    else_kw: Node
    relation: Node


@dataclass
class ToPrevious(Frag):
    """Binds to the IMMEDIATELY PRECEDING lowered sibling, wherever it is lowered.
    A fragment that also emits nodes sets `_skip` to their count, so it binds to
    the sibling before them (`bind_previous`)."""

    def apply(self, prev):
        raise NotImplementedError


@dataclass
class VarTailMerge(ToPrevious):
    """Contract **var-tail-merge** (produced by assemblers.split_var_section_tail).
    The preceding lowered sibling must be a `var_section` (grammar.js comment on
    `preproc_split_var_section_tail`: this node is always its sibling); anything
    else is `contract-shape`, checked even when there is nothing to merge. The
    chosen arm's `variables` declarations (already lowered) APPEND to that
    section's `var_body`, created with field `body` if the section had none yet.
    That is the named rewrite: only the var_body's children list grows, and its
    (and the var_section's) span is recomputed from its children. No other edge
    changes. An arm with no `variables`, or no arm chosen, carries `decls == []`
    and this is a no-op."""
    decls: list = field(default_factory=list)

    def apply(self, prev):
        if prev.kind != "var_section":
            raise LoweringError("contract-shape", prev, "var-tail-merge needs a preceding var_section")
        if not self.decls:
            return prev
        body = next((c for c in prev.children if c.field == "body"), None)
        kids = list(prev.children)
        if body is None:
            body = Node("var_body", True, "body", 0, 0, [])
            kids.append(body)
        new_body = _span_from_children(body.copy(children=body.children + self.decls))
        kids = [new_body if c is body else c for c in kids]
        return _span_from_children(prev.copy(children=kids))


# Named rewrite **property-expression-unwrap** (contract expression-continuation,
# regions.assemble_with_tail): a property value continued by a tail is
# `property_expression(expr, tail)` (grammar.js `_property_value`, finding G5), because flat
# `MinValue = 1 + 2;` wraps a binary value. Flat `MinValue = 1;` does not wrap a simple one,
# so when the lowered property_expression's only child is not one of its member kinds the
# wrapper is replaced by that child, which takes the wrapper's field (`value`). Applied by
# _lower_ordinary, only to a property_expression that held a group as a child: a tail, a
# leading prefix or an operand group (B7b-2 Phase C).
# property_expression's own members (grammar.js property_expression), hand-written.
PROPERTY_EXPRESSION_KINDS = frozenset({
    "call_expression", "member_expression", "qualified_enum_value", "database_reference",
    "unary_expression", "additive_expression", "multiplicative_expression", "comparison_expression",
    "logical_expression", "ternary_expression", "parenthesized_expression", "subscript_expression",
})

# Named rewrite **option-member-list-unwrap** (G11). An option-member list may
# be opened by a #if (`OptionMembers = #if X A, #endif B;`), so a configuration
# can leave it ONE member. Flat `OptionMembers = B;` is not a list: B reaches
# _property_value directly, as a bare leaf of one of these kinds (grammar.js
# `_property_value`, hand-written). So a property `value` option_member_list
# that held a preproc_conditional_option_members, lowered to exactly one
# option_member whose only child is one of these kinds, is replaced by that
# child, which takes the list's field. Keyword members (`Local`, `Internal`,
# ...) stay a list flat and are not unwrapped. Applied by _lower_ordinary.
OPTION_MEMBER_BARE_KINDS = frozenset({
    "identifier", "quoted_identifier", "string_literal", "integer", "boolean", "keyword_identifier",
})
_OPTION_COND = "preproc_conditional_option_members"


# Normalisation **arm-terminator** (B7b-0, user ruling Option A, 2026-10-07). The tree keeps a
# statement's `;` that sits alone in an #if arm (`I := 1` / `#if X` / `;` / `#endif`) as its own
# empty_statement inside the conditional. A configuration that selects that arm reads `I := 1 ;`,
# whose `;` is the statement's separator: a bare `;` child of the statement host right after the
# statement, which is what a Terminator anchored to the statement lands as. select.branch_select
# marks the lowered empty_statement of a preproc_conditional_statement arm that holds nothing else
# (extras are not in the IR) with ARM_SEMI; the mark survives splicing through enclosing arms, so
# the decision is taken where the statement run is whole: absorb_arm_terminators, called by every
# builder of a statement run (statement hosts, a code_block's completed body, an else block).
ARM_SEMI = "_arm_semi"


def absorb_arm_terminators(kids, ctx):
    """One pass over a whole statement run, three rewrites, each where the flat grammar reads it:

    * **empty-body-terminator** (statement hosts, B7b-3 Task 10): a statement whose single-slot
      body selection removed (PENDING_BODY, see _mark_pending_body) at the END of the previous
      item takes the next `;` -- bare or a marked lone-`;` arm -- as `body: empty_statement`
      (flat `if C then ;`). Noted `empty-body-terminator@<offset>`.
      After a filled body, an unmarked empty_statement directly after the statement is its bare
      `;` (flat `if C then ; ;` gives the second `;` to the if). Noted `filled-terminator@<offset>`.
    * **arm-terminator**: a marked empty_statement directly after a statement (a named node other
      than an empty_statement) is replaced by its `;`, the Terminator placement: right after its
      anchor. After a `;`, at the start of the run, or after an empty_statement it stays: the flat
      reading there is a standalone `;` (`I := 1; ;`). Noted `arm-terminator@<offset of the ;>`.
    * **orphan-terminator** (B7b-3 Task 10, narrowed in fix round 1): the dual, ONLY where the
      split tree's reading of the `;` depends on the configuration. A bare `;` left where no
      statement precedes it (run start, after a `;` or an empty_statement) is an empty_statement,
      as the flat grammar reads it, when its original preceding sibling is a group with an arm
      that ENDS in a statement without its own `;` (`#if A x := 1 #endif ;`: A=1 the `;` is the
      separator, A=0 an empty statement; no single tree holds both). Those `;` offsets are found
      on the ORIGINAL tree (orphan_candidates) before lowering. A `;` after an empty group or a
      group of terminated statements (`begin #if X #endif ; end`, `#if A x := 1; #endif ;`) is a
      bare `;` in a tree where every configuration reads an empty_statement: that split tree is
      wrong, and it is left to fail (deferred, a grammar item), never normalised.
      This test is STRICTER than the rule it implements ("a group leaves a statement without
      its own `;` in some configuration"): it looks only at the `;`'s immediate preceding
      sibling and at each arm's LAST item. `#if A x := 1 #if B #endif #endif ;` (the arm ends in
      an empty nested group) and `#if A x := 1 #endif #if B #endif ;` (an empty group sits
      between) satisfy the rule but not the test, so they are not normalised and give a
      discrepancy at A=0. So do `x := 1 #if A ; #endif ;` and `if C then Bar #if X ; #endif ;`:
      the group follows an UNTERMINATED statement and its arm's last item is the lone `;`, so the
      arm does not end unterminated; at A=1 / X=1 the outer `;` is a flat empty_statement and the
      test misses it. All four fail loud, never mask (0 production sites; deferred-work item 48).
      Noted `orphan-terminator@<offset>`.

    Done in one pass, so a later `;` sees the statement already terminated."""
    out, filled = [], None
    for n in kids:
        marked = getattr(n, ARM_SEMI, False)
        semi = n.children[0] if marked else n if _bare_semi(n) else None
        owner = _pending_tail(out[-1]) if semi is not None and out else None
        if (filled is not None and out and out[-1] is filled and not marked
                and n.kind == "empty_statement" and n.field is None and len(n.children) == 1):
            ctx.normalised.append(f"filled-terminator@{n.children[0].start}")
            out.append(n.children[0])
        elif owner is not None:
            _fill_pending_body(out[-1], owner, semi)
            ctx.normalised.append(f"empty-body-terminator@{semi.start}")
            filled = out[-1]
            continue
        elif marked and out and out[-1].named and out[-1].kind != "empty_statement":
            ctx.normalised.append(f"arm-terminator@{semi.start}")
            out.append(semi)
        elif (ORPHANS and not marked and semi is not None and semi.start in getattr(ctx, "orphan_ok", ())
              and (not out or not out[-1].named or out[-1].kind == "empty_statement")):
            ctx.normalised.append(f"orphan-terminator@{semi.start}")
            out.append(Node("empty_statement", True, None, semi.start, semi.end, [semi]))
        else:
            out.append(n)
        filled = None
    return out


ORPHANS = True   # mutation switch for the orphan-terminator tests


def _ends_unterminated(group):
    """True when some arm of the statement group ends in a statement without its own `;`
    (recursively through a nested group that ends an arm)."""
    from tools.config_oracle.lowering.select import split_arms
    try:
        arms, _ = split_arms(group)
    except LoweringError:     # a malformed group: selection refuses it when (if) it is reached
        return False
    for _, content in arms:
        last = content[-1] if content else None
        if last is None:
            continue
        if last.kind == "preproc_conditional_statement":
            if _ends_unterminated(last):
                return True
        elif last.named and last.kind != "empty_statement":
            return True
    return False


def orphan_candidates(root):
    """Offsets of the bare `;` whose original preceding sibling is a statement group with an arm
    ending in an unterminated statement: the only `;` orphan-terminator may rewrite."""
    out, stack = set(), [root]
    while stack:
        n = stack.pop()
        for prev, c in zip(n.children, n.children[1:]):
            if _bare_semi(c) and prev.kind == "preproc_conditional_statement" and _ends_unterminated(prev):
                out.add(c.start)
        stack.extend(n.children)
    return frozenset(out)


# Statement bodies (single-slot) that selection may remove WHOLE: an `#if` group that lowers to
# nothing as the body (`if C then #if X #endif ;`). select.branch_select lets such a group lower
# to 0 nodes, _mark_pending_body records it on the statement, absorb_arm_terminators fills it
# from the next `;`, and _lower_tree refuses one still pending, exactly as select refused it
# before (policy, same node and detail), so existing classifications keep matching.
EMPTY_BODY_SLOTS = frozenset({("if_statement", "then_branch"), ("if_statement", "else_branch"),
                              ("while_statement", "body"), ("for_statement", "body"),
                              ("foreach_statement", "body"), ("with_statement", "body")})
_BODY_SLOT_FIELDS = frozenset(f for _, f in EMPTY_BODY_SLOTS)
PENDING_BODY = "_pending_body"


def _bare_semi(n):
    return n.kind == ";" and not n.children and n.field is None


def _mark_pending_body(orig, new):
    """Record the one emptied body. Two emptied slots (an if whose then AND else groups both
    lower to nothing) are refused at the first one, with the pre-rewrite policy refusal: one
    `;` can fill at most one, and dropping the other would lose a field silently."""
    for c in orig.children:
        if (c.kind == "preproc_conditional_statement" and (orig.kind, c.field) in EMPTY_BODY_SLOTS
                and not any(k.field == c.field for k in new.children)):
            first = getattr(new, PENDING_BODY, None)
            if first is not None:
                raise LoweringError("policy", first, "0 nodes into a single-slot")
            setattr(new, PENDING_BODY, c)


def _pending_tail(item):
    """The statement at the very END of `item` (down its trailing body chain) whose body is
    pending, or None. A pending body is at the end only when nothing fielded follows it."""
    while item is not None and item.children:
        if getattr(item, PENDING_BODY, None) is not None and item.children[-1].field is None:
            return item
        last = item.children[-1]
        item = last if last.field in _BODY_SLOT_FIELDS else None
    return None


def _fill_pending_body(top, owner, semi):
    group = getattr(owner, PENDING_BODY)
    owner.children = owner.children + [Node("empty_statement", True, group.field, semi.start, semi.end, [semi])]
    delattr(owner, PENDING_BODY)
    path, n = [], top        # spans grow at the tail: recompute owner .. top, innermost first
    while n is not owner:
        path.append(n)
        n = n.children[-1]
    for n in [owner] + path[::-1]:
        _span_from_children(n)


def _refuse_pending(node):
    stack = [node]
    while stack:
        n = stack.pop()
        group = getattr(n, PENDING_BODY, None)
        if group is not None:
            raise LoweringError("policy", group, "0 nodes into a single-slot")
        stack.extend(n.children)


def bind_previous(kids, r, c):
    """Append `r.nodes` to `kids`, apply every ToPrevious fragment of `r` to its
    target sibling in `kids`, and return the other fragments."""
    kids.extend(r.nodes)
    rest = []
    for f in r.frags:
        if isinstance(f, ToPrevious):
            target = len(kids) - 1 - getattr(f, "_skip", 0)
            if target < 0 or not kids[target].named:
                raise LoweringError("unconsumed-fragment", c, f"{type(f).__name__} with no preceding sibling")
            kids[target] = f.apply(kids[target])
        else:
            rest.append(f)
    return rest


@dataclass
class Lowered:
    nodes: list
    frags: list = field(default_factory=list)


class Accounting:
    def __init__(self, resolution):
        self.active = resolution.active
        self.leaf = {}

    def mark(self, node, reason):
        for lf in node.leaves():
            # A kept leaf must lie on a surviving line and an inactive-arm leaf on a
            # masked one. Zero-width leaves carry no bytes, so nothing to check.
            if lf.end > lf.start and reason in ("kept", "inactive-arm")                     and bool(self.active[lf.start]) != (reason == "kept"):
                raise LoweringError("accounting", lf, f"{reason} leaf on a line that is "
                                    f"{'masked' if reason == 'kept' else 'active'}")
            key = (lf.start, lf.end, lf.kind)
            if key in self.leaf:
                raise LoweringError("accounting", lf, f"leaf accounted twice: {self.leaf[key]} then {reason}")
            self.leaf[key] = reason

    def check_complete(self, root):
        for lf in root.leaves():
            if (lf.start, lf.end, lf.kind) not in self.leaf:
                raise LoweringError("accounting", lf, "leaf never accounted")

    def check_emitted(self, low):
        """Every leaf accounted as `kept` appears in the output exactly once, and
        nothing else does. Keyed by interval only: a token alias changes kind."""
        kept = collections.Counter((s, e) for (s, e, _), why in self.leaf.items() if why == "kept")
        emitted = collections.Counter((lf.start, lf.end) for lf in low.leaves()) if low.children             else collections.Counter()
        if kept != emitted:
            missing = sorted((kept - emitted).elements())[:3]
            extra = sorted((emitted - kept).elements())[:3]
            raise LoweringError("accounting", low, f"kept-but-not-emitted {missing}, emitted-but-not-kept {extra}")


@dataclass
class Ctx:
    resolution: object
    accounting: Accounting
    parent_kind: str | None = None
    slot: str | None = None
    normalised: list = field(default_factory=list)
    orphan_ok: frozenset = frozenset()     # orphan_candidates of the original tree

    def child(self, parent_kind, slot):
        return Ctx(self.resolution, self.accounting, parent_kind, slot, self.normalised, self.orphan_ok)

    def host(self):
        """`host <parent>:<slot>`: the refusal detail that keys a classification to where
        the refused node sits, so a re-parented node no longer matches its entry."""
        return f"host {self.parent_kind}:{self.slot}"

    def policy(self, entry, node):
        host = f"{self.parent_kind}:{self.slot}"
        if host not in entry.hosts:
            raise LoweringError("policy-host", node, f"{entry.type} not registered in {host}")
        return entry.hosts[host]


def _is_special(kind):
    return kind.startswith("preproc") or kind in contracts.SPECIAL_NON_PREFIXED


def lower(node, ctx) -> Lowered:
    if _is_special(node.kind):
        entry = contracts.REGISTRY.get(node.kind)
        if entry is None:
            raise LoweringError("unregistered-type", node)
        if entry.kind == "fragment":
            # A fragment belongs to the assembler that owns its host; reaching it here
            # means that assembler did not (e.g. a brace close outside its open node).
            raise LoweringError("unconsumed-fragment", node, "fragment lowered on its own")
        if entry.kind == "unsupported" or entry.handler is None:
            raise LoweringError("unsupported-type", node, ctx.host())
        return contracts.resolve_handler(entry)(node, ctx)
    if (node.kind in regions.NODES and not regions.region_edge(ctx.parent_kind, node.kind, node.field)
            and regions.has_group(node)):
        # Root dispatch (B7b-2 spec 7 step 1): a region root holding a group is assembled
        # whole, once. A node reached by a region edge belongs to its root's invocation.
        return regions.assemble(node, ctx)
    return _lower_ordinary(node, ctx)


def lower_items(children, ctx, host_kind, lower_one=None):
    """(index of the last child consumed, first child, Lowered) for each item of a host's
    children. A named child followed by a root tail is ONE item: the region assembler lowers
    the expression and its tail in one invocation (B7b-2 spec 7 step 1); so are leading
    prefixes, the expression after them and its tail (spec 6.3). Every other child is
    lowered by `lower_one` (default `lower`)."""
    lower_one = lower_one or lower
    i = 0
    while i < len(children):
        c = children[i]
        cctx = ctx.child(host_kind, c.field or "<children>")
        j = i
        while regions.LEADING_PREFIXES and j < len(children) and children[j].kind == regions.PREFIX:
            j += 1
        if (j > i and j < len(children) and children[j].named
                and children[j].kind not in (regions.TAIL, regions.PREFIX)):
            # leading prefixes (spec 6.3): prefix+ expr [tail], one item owned by the root
            e = children[j]
            tail = children[j + 1] if j + 1 < len(children) and children[j + 1].kind == regions.TAIL else None
            yield j + (tail is not None), c, regions.assemble_with_tail(
                e, tail, ctx.child(host_kind, e.field or "<children>"), ctx.child(host_kind, "<children>"),
                prefixes=children[i:j])
            i = j + 1 + (tail is not None)
        elif c.named and i + 1 < len(children) and children[i + 1].kind == regions.TAIL:
            yield i + 1, c, regions.assemble_with_tail(c, children[i + 1], cctx, ctx.child(host_kind, "<children>"))
            i += 2
        else:
            yield i, c, lower_one(c, cctx)
            i += 1


def _lower_ordinary(node, ctx) -> Lowered:
    if not node.children:
        ctx.accounting.mark(node, "kept")
        return Lowered([node.copy(children=[])])
    kids, frags = [], []
    last_index = len(node.children) - 1
    for i, c, r in lower_items(node.children, ctx, node.kind):
        for f in r.frags:
            f._from_last = (i == last_index)
        frags.extend(bind_previous(kids, r, c))
    new = Node(node.kind, node.named, node.field, node.start, node.end, kids)
    fam = conditional_lists.HOST_FAMILY.get(node.kind)
    if move_args.dispatches(node):
        # B7b-3 spec 6.3: EVERY move host, group or not, through the one move-interior adapter
        # (routes 1-3), before the strict-list hook (it supersedes move_elements' lower_region).
        new.children = move_args.lower(node, new.children, ctx)
    elif fam is not None and any(c.kind == fam.group for c in node.children):
        # A strict-list host (B7b-1): its own complete-region validator and empty policy.
        new.children = conditional_lists.lower_region(node, new.children, fam)
        if not new.children:
            if frags:
                raise LoweringError("unconsumed-fragment", node, "fragment out of an emptied list")
            ctx.normalised.append(f"optional-list-removed:{node.kind}@{node.start}")
            return Lowered([], frags)
    elif any(c.kind in LIST_RUN_TYPES or (c.kind == regions.OPERAND_GROUP and node.kind in EXPRESSION_LISTS)
             for c in node.children):
        # an operand group item may contribute no item (regions.EMPTY_LIST_ITEM): check the list
        if new.kind == "option_member_list":
            _check_option_holes(new)
        else:
            _check_alternation(new)
    # Read the selection before _consume places it: a Terminator from the last child (the
    # core, at a `;`-inside site) is a selected arm's `;`.
    selected_terminator = any(isinstance(f, Terminator) and getattr(f, "_from_last", False) for f in frags)
    frags = _consume(new, frags)
    if (node.kind, "then_branch") in EMPTY_BODY_SLOTS or (node.kind, "body") in EMPTY_BODY_SLOTS:
        _mark_pending_body(node, new)
    if node.kind == "statement_block":
        new.children = absorb_arm_terminators(new.children, ctx)
    elif node.kind == "case_branch":
        case_terminators.empty_body(node, new, ctx)
    elif node.kind == "case_body":
        # case-terminator (B7b-3 spec 6.2): a case run's `;` groups, never ARM_SEMI.
        new.children = case_terminators.attach(new.children, ctx)
    elif node.kind == "code_block":
        # a BlockCompletion may have appended a statement run to the block's body
        body = next((c for c in new.children if c.field == "body" and c.kind == "statement_block"), None)
        if body is not None:
            body.children = absorb_arm_terminators(body.children, ctx)
    if node.kind == "property":
        _check_site_boundary(node, new, ctx, selected_terminator)
    elif node.kind == "case_statement":
        case_terminators.check_else_ownership(new, ctx)
    for f in frags:
        if not getattr(f, "_from_last", False):
            raise LoweringError("unconsumed-fragment", node, f"{type(f).__name__} not from the last child")
        f.anchor = new
    if not new.children:
        # The root emptied is an empty FILE (a whole object inside `#if not CLEANnn`):
        # it is not removed, _lower_tree turns it into a childless root, and the
        # comparison still runs against the reference's childless source_file.
        if ctx.parent_kind is None:
            return Lowered([], frags)
        if node.kind in EMPTY_REMOVABLE:
            ctx.normalised.append(f"removed-empty:{node.kind}@{node.start}")
            return Lowered([], frags)
        # list-value-empty (B11 spec 5.3): a list family's list emptied by its element
        # conditionals, at an optional value site.
        if (node.kind in LIST_VALUE_EMPTY_KINDS and node.field == "value"
                and ctx.parent_kind in ("property", "preproc_conditional_property_value")):
            ctx.normalised.append(f"list-value-empty:{node.kind}@{node.start}")
            return Lowered([], frags)
        raise LoweringError("empty-node", node)
    if (node.kind == "property_expression" and any(c.kind in regions.GROUPS for c in node.children)
            and len(kids) == 1 and kids[0].kind not in PROPERTY_EXPRESSION_KINDS):
        ctx.normalised.append(f"property-expression-unwrap@{node.start}")
        return Lowered([kids[0].copy(field=node.field)], frags)
    if (node.kind == "option_member_list" and node.field == "value"
            and any(c.kind == _OPTION_COND for c in node.children)
            and len(kids) == 1 and kids[0].kind == "option_member" and len(kids[0].children) == 1
            and kids[0].children[0].kind in OPTION_MEMBER_BARE_KINDS):
        ctx.normalised.append(f"option-member-list-unwrap@{node.start}")
        return Lowered([kids[0].children[0].copy(field=node.field)], frags)
    return Lowered([_span_from_children(new)], frags)


# B11 (spec 2026-10-05 5.3): a whole value that is a #if or a run of them.
_WHOLE_VALUE_KINDS = frozenset({"preproc_conditional_property_value", "preproc_conditional_property_value_sequence"})


def _check_site_boundary(node, new, ctx, selected_terminator):
    """A property that ends at its whole-value core (a `;`-inside site: no `;` of its own
    after the core) is terminated only by a selected arm's `;`. A configuration that
    selects none moves the property's boundary beyond the site (`Caption = #if X 'a';
    #endif #if Y #endif ;` at X=0 is `Caption = ;`), which the tree cannot hold:
    lowering:one-reading at the core, debt B12. The verdict comes from the selection, not
    from the lowered shape: when a terminator WAS selected and the property still does not
    end in it, that is a lowering defect, contract-shape, never absorbed as debt. A
    `;`-after site, where the property owns its `;`, never reaches this."""
    core = next((c for c in node.children if c.field == "value" and c.kind in _WHOLE_VALUE_KINDS), None)
    if core is None or node.children[-1] is not core:
        return
    if not selected_terminator:
        raise LoweringError("one-reading", core, ctx.child("property", "value").host())
    if not (new.children and new.children[-1].kind == ";" and not new.children[-1].children):
        raise LoweringError("contract-shape", core, "a selected terminator does not end the property")


def _check_option_holes(new):
    """OptionMembers keeps blank ordinals (B11 spec 5.3): leading, consecutive and trailing
    `,` are legal. Only two members side by side, with no separator, are refused."""
    prev_item = False
    for c in new.children:
        if c.kind == ";" and not c.children:
            continue
        is_sep = c.kind == "," and not c.children
        if not is_sep and prev_item:
            raise LoweringError("list-separator", new, "two members without a separator")
        prev_item = not is_sep


# B7b-2 (Task 10 finding): in an expression list, an item directly followed by another item
# is a tree claiming a list boundary where the configuration has no separator. The flat
# text then continues the first item's expression (an argument list or list literal of a
# clean parse always alternates), so the lowered list is left to the comparison: a
# discrepancy, never a refusal. Exception, spec 3.4 list spanning (deferred): the second item
# opens a group arm that also supplies a separator (`Foo(1 #if X + 2, 3 #endif)`); that
# pinned wrong tree keeps its refusal. select.branch_select sets LIST_SPAN on such an arm's
# first lowered node.
ADJACENT_DISCREPANCY = True   # mutation switch for test_regions.test_silent_wrong_tree_is_a_discrepancy
EXPRESSION_LISTS = frozenset({"argument_list", "list_literal"})
LIST_SPAN = "_list_span"


def _check_alternation(new):
    seq = [c for c in new.children if c.kind not in _BRACKETS]
    # A single trailing `;` is not an item: whether it belongs here (terminator
    # placement) is judged by the structure check against the reference.
    if seq and seq[-1].kind == ";" and not seq[-1].children:
        seq.pop()
    want_item = True
    for c in seq:
        is_sep = c.kind == "," and not c.children
        if is_sep == want_item:
            if not is_sep and new.kind in EXPRESSION_LISTS:
                if getattr(c, LIST_SPAN, False):
                    raise LoweringError("list-separator", new, "list spanning (spec 3.4): an item group "
                                        "that continues the item before it and supplies a separator")
                if ADJACENT_DISCREPANCY:
                    continue    # owed to the comparison; the rest of the list is still checked
            raise LoweringError("list-separator", new, "list does not alternate item, separator")
        want_item = not want_item
    if seq and want_item:
        raise LoweringError("list-separator", new, "list ends with a separator")


def _span_from_children(node):
    # Every child is already lowered with its span set from its own leaves, so
    # the first child's start / last child's end ARE the first/last leaf's.
    # O(1), where recompute_span is O(subtree) -- O(depth^2) on a deep chain.
    node.start, node.end = node.children[0].start, node.children[-1].end
    return node


def _deepest_open_if(expr):
    """table_relation_expression -> the deepest if_table_relation on its else chain with no else."""
    cur = next((c for c in expr.children if c.kind == "if_table_relation"), None)
    if cur is None:
        raise LoweringError("contract-shape", expr, "no if_table_relation to continue")
    while True:
        nxt = next((c for c in cur.children if c.field == "else_relation"), None)
        if nxt is None:
            return cur
        inner = next((c for c in nxt.children if c.kind == "if_table_relation"), None)
        if inner is None:
            raise LoweringError("contract-shape", cur, "else chain already closed")
        cur = inner


def _path(top, target):
    """Nodes from `target` up to `top`, deepest first, for span recomputation."""
    stack = [(top, [top])]
    while stack:
        n, path = stack.pop()
        if n is target:
            return list(reversed(path))
        for c in n.children:
            stack.append((c, path + [c]))
    raise LoweringError("contract-shape", top, "target not under top")


def _consume(new, frags):
    rest = []
    for f in frags:
        if isinstance(f, BlockCompletion) and new.kind == "code_block":
            body = next((c for c in new.children if c.field == "body"), None)
            if f.statements:
                if body is None:
                    body = Node("statement_block", True, "body", 0, 0, [])
                    new.children.insert(1, body)
                body.children.extend(f.statements)
                recompute_span(body)
            new.children.append(f.end)
        elif isinstance(f, ElseAttachment) and new.kind == "if_statement" and f.anchor is not None \
                and f.anchor.field == "then_branch" and any(c is f.anchor for c in new.children):
            new.children.append(f.else_kw)
            new.children.append(f.branch.copy(field="else_branch"))
        elif isinstance(f, (Terminator, Following)) and new.kind in STATEMENT_HOSTS \
                and any(c is f.anchor for c in new.children):
            at = next(i for i, c in enumerate(new.children) if c is f.anchor) + 1
            insert = [f.leaf] if isinstance(f, Terminator) else list(f.statements)
            new.children[at:at] = insert
        elif isinstance(f, SiblingsAfter) and (new.kind in LAYOUT_HOSTS or getattr(f.anchor, "kind", None) == "property") \
                and any(c is f.anchor for c in new.children):
            at = next(i for i, c in enumerate(new.children) if c is f.anchor) + 1
            new.children[at:at] = list(f.nodes)
        elif isinstance(f, RelationContinuation) and new.kind == "table_relation_value" \
                and (f.anchor is None or any(c is f.anchor for c in new.children)):
            vals = [c for c in new.children if c.kind == "table_relation_expression"]
            if not vals:
                raise LoweringError("unconsumed-fragment", new, "no relation to continue")
            target = _deepest_open_if(vals[-1])
            target.children.append(f.else_kw)
            target.children.append(f.relation.copy(field="else_relation"))
            for n in _path(vals[-1], target):
                recompute_span(n)
        # anchor None: emitted by a special node that is itself a direct child of
        # the property (whole_value_select on a whole-value #if); otherwise it
        # passed up through the property's child: the list (list-run) or the
        # table_relation_value holding an else-relation-join conditional.
        elif isinstance(f, Terminator) and new.kind == "property"                 and (f.anchor is None or any(c is f.anchor for c in new.children)):
            last = new.children[-1] if f.anchor is None and new.children[-1:] \
                and new.children[-1].kind == ";" else None
            if last is None:
                new.children.append(f.leaf)   # terminator-hoist: the property's own `;`
            else:
                # Mixed placement (B5b): the property already ends in a `;` (its own after
                # #endif, or a nested arm's hoisted one). The EARLIER `;` ends it, and the
                # later one is a standalone `;`, which a flat parse gives as an
                # empty_statement sibling (`A = x; ;`). Valid AL: alc's property list
                # accepts it (spec 2026-10-05 §3.2 item 2).
                first, later = sorted((last, f.leaf), key=lambda n: n.start)
                new.children[-1] = first
                recompute_span(new)
                stmt = Node("empty_statement", True, None, later.start, later.end, [later])
                sib = next((r for r in rest if isinstance(r, SiblingsAfter)
                            and getattr(r, "_mixed_semis", False)), None)
                if sib is None:
                    sib = SiblingsAfter(None, [stmt])
                    sib._from_last = True
                    sib._mixed_semis = True
                    rest.append(sib)
                else:
                    sib.nodes.append(stmt)
                    sib.nodes.sort(key=lambda n: n.start)
        else:
            rest.append(f)
    return rest


def _lower_tree(root, extras, resolution):
    acc = Accounting(resolution)
    ctx = Ctx(resolution, acc, orphan_ok=orphan_candidates(root))
    out = lower(root, ctx)
    if out.frags:
        raise LoweringError("unconsumed-fragment", root, ", ".join(type(f).__name__ for f in out.frags))
    low = out.nodes[0] if out.nodes else Node(root.kind, root.named, None, 0, 0, [])
    _refuse_pending(low)
    acc.check_complete(root)
    acc.check_emitted(low)
    kept = [e for e in extras if resolution.active[e.start]]
    return low, kept, list(ctx.normalised)


# At the bottom: conditional_lists imports this module's names, and _lower_ordinary reads
# conditional_lists only at call time, so the cycle is safe in either import order.
from tools.config_oracle.lowering import case_terminators, conditional_lists, move_args, regions  # noqa: E402


def lower_tree(root, extras, resolution):
    """-> (lowered root, kept extras, normalisations). Runs under the comparator's
    deep-stack helper: real trees reach depth ~1,400 and `lower` is recursive."""
    return _run_with_deep_stack(_lower_tree, root, extras, resolution)
