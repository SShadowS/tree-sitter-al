"""Recursive lowering of the multi-configuration IR to one configuration (spec section 3).

Rules that are load-bearing:
  * no default handler -- an unregistered special node fails;
  * every leaf of the ORIGINAL tree is accounted exactly once, and exactly the
    leaves accounted `kept` are emitted;
  * a fragment may only pass up through a node when the child it came from is
    that node's last original child, and must be consumed by a named consumer;
  * the normalisations are removing an EMPTY_REMOVABLE container that lowering
    emptied, and arm-terminator (absorb_arm_terminators). (Unwrapping a continued
    property value is not one: it is a named rewrite of contract
    expression-continuation, see ExpressionContinuation.)

Lowering only selects and relabels. It never sees the reference parse (this
package imports nothing from reference.py, tree_sitter, or the loader).
"""
from __future__ import annotations

import collections
from dataclasses import dataclass, field

from tools.config_oracle import contracts
from tools.config_oracle.compare import _run_with_deep_stack
from tools.config_oracle.ir import Node, recompute_span
from tools.config_oracle.lowering import expression

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
class ExpressionContinuation(ToPrevious):
    """Contract **expression-continuation** (produced by assemblers.expression_tail).
    The preceding sibling expression and every pair's operand are flattened, the
    `(operator, operand)` pairs appended in order, and the whole recomposed by the
    precedence table (expression.compose), keeping the preceding sibling's field.
    That regrouping is the named rewrite; no pairs leave the sibling untouched.

    Second named rewrite, **property-expression-unwrap**: a property value
    continued by a tail is `property_expression(expr, tail)` (grammar.js
    `_property_value`, finding G5), because flat `MinValue = 1 + 2;` wraps a
    binary value. Flat `MinValue = 1;` does not wrap a simple one, so when the
    lowered property_expression's only child is not one of its member kinds
    (PROPERTY_EXPRESSION_KINDS) the wrapper is replaced by that child, which
    takes the wrapper's field (`value`). Applied by engine._lower_ordinary, only
    to a property_expression that held a tail.

    One configuration class is **one-reading** (grammar finding G7, split form):
    a signed literal continued by a tail, `MinValue = -1 #if X + 2 #endif ;`. The
    scanner emits `-1` as one literal before `#`, which is the tail-inactive
    configuration's flat reading; where a pair is live the flat parse reads unary
    minus, a different tokenisation no tree can also hold. `masked` is that
    configuration's text, read only for the literal's first byte."""
    pairs: list = field(default_factory=list)
    masked: bytes = b""

    def apply(self, prev):
        if not self.pairs:
            return prev
        if (not prev.children and prev.kind in ("integer", "decimal")
                and self.masked[prev.start:prev.start + 1] == b"-"):
            raise LoweringError("one-reading", prev, "signed literal continued by a live tail")
        try:
            flat = expression.flatten(prev)
            for op, operand in self.pairs:
                flat += [op] + expression.flatten(operand)
        except ValueError as e:
            raise LoweringError("contract-shape", prev, str(e)) from None
        return expression.compose(flat, prev.field)


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


# property_expression's own members (grammar.js property_expression), hand-written.
PROPERTY_EXPRESSION_KINDS = frozenset({
    "call_expression", "member_expression", "qualified_enum_value", "database_reference",
    "unary_expression", "additive_expression", "multiplicative_expression", "comparison_expression",
    "logical_expression", "ternary_expression", "parenthesized_expression", "subscript_expression",
})
_TAIL = "preproc_conditional_expression_tail"

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
    """A marked empty_statement directly after a statement (a named node other than an
    empty_statement) is replaced by its `;`, the Terminator placement: right after its anchor.
    After a `;`, at the start of the run, or after an empty_statement it stays: the flat reading
    there is a standalone `;` (`I := 1; ;`). Done in one pass, so a later lone-`;` group sees the
    statement already terminated. Each rewrite is noted `arm-terminator@<offset of the ;>`."""
    out = []
    for n in kids:
        if getattr(n, ARM_SEMI, False) and out and out[-1].named and out[-1].kind != "empty_statement":
            semi = n.children[0]
            ctx.normalised.append(f"arm-terminator@{semi.start}")
            out.append(semi)
        else:
            out.append(n)
    return out


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

    def child(self, parent_kind, slot):
        return Ctx(self.resolution, self.accounting, parent_kind, slot, self.normalised)

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
    if node.kind in expression.BINARY_KINDS and _has_prefix(node, ctx):
        # The binary hook: a chain holding a prefix is lowered whole, from its
        # top node (contract operand-prefix, assemblers.operand_prefix).
        return contracts.resolve_handler(contracts.REGISTRY[expression.PREFIX])(node, ctx)
    return _lower_ordinary(node, ctx)


def _has_prefix(node, ctx):
    """True for the TOP node of a binary chain holding a preproc_operand_prefix.
    An inner node (a binary parent's left/right) was the top's to lower, so the
    chain is walked once, not once per level."""
    if ctx.parent_kind in expression.BINARY_KINDS and ctx.slot in ("left", "right"):
        return False
    try:
        return any(n.kind == expression.PREFIX for _, n in expression.chain(node))
    except ValueError:
        return False   # not a plain chain: _lower_ordinary lowers it, and any prefix in it refuses


def _lower_ordinary(node, ctx) -> Lowered:
    if not node.children:
        ctx.accounting.mark(node, "kept")
        return Lowered([node.copy(children=[])])
    kids, frags = [], []
    last_index = len(node.children) - 1
    for i, c in enumerate(node.children):
        r = lower(c, ctx.child(node.kind, c.field or "<children>"))
        for f in r.frags:
            f._from_last = (i == last_index)
        frags.extend(bind_previous(kids, r, c))
    new = Node(node.kind, node.named, node.field, node.start, node.end, kids)
    if any(c.kind in LIST_RUN_TYPES for c in node.children):
        if new.kind == "option_member_list":
            _check_option_holes(new)
        else:
            _check_alternation(new)
    # Read the selection before _consume places it: a Terminator from the last child (the
    # core, at a `;`-inside site) is a selected arm's `;`.
    selected_terminator = any(isinstance(f, Terminator) and getattr(f, "_from_last", False) for f in frags)
    frags = _consume(new, frags)
    if node.kind in STATEMENT_HOSTS:
        new.children = absorb_arm_terminators(new.children, ctx)
    elif node.kind == "code_block":
        # a BlockCompletion may have appended a statement run to the block's body
        body = next((c for c in new.children if c.field == "body" and c.kind == "statement_block"), None)
        if body is not None:
            body.children = absorb_arm_terminators(body.children, ctx)
    if node.kind == "property":
        _check_site_boundary(node, new, ctx, selected_terminator)
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
    if (node.kind == "property_expression" and any(c.kind == _TAIL for c in node.children)
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
    ctx = Ctx(resolution, acc)
    out = lower(root, ctx)
    if out.frags:
        raise LoweringError("unconsumed-fragment", root, ", ".join(type(f).__name__ for f in out.frags))
    low = out.nodes[0] if out.nodes else Node(root.kind, root.named, None, 0, 0, [])
    acc.check_complete(root)
    acc.check_emitted(low)
    kept = [e for e in extras if resolution.active[e.start]]
    return low, kept, list(ctx.normalised)


def lower_tree(root, extras, resolution):
    """-> (lowered root, kept extras, normalisations). Runs under the comparator's
    deep-stack helper: real trees reach depth ~1,400 and `lower` is recursive."""
    return _run_with_deep_stack(_lower_tree, root, extras, resolution)
