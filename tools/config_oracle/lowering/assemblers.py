"""Assemblers: construct configured nodes from pieces across arms (spec section 3).

Each function's docstring IS its contract, including every edge rewrite it is
allowed to make. Anything not named there is an error.
"""
from __future__ import annotations

from tools.config_oracle import contracts
from tools.config_oracle.ir import Node
from tools.config_oracle.lowering import expression
from tools.config_oracle.lowering.engine import (BlockCompletion, ElseAttachment, ExpressionContinuation,
                                                 Following, Lowered, LoweringError, RelationContinuation,
                                                 SiblingsAfter, Terminator, _span_from_children, lower)
from tools.config_oracle.lowering.select import chosen_arm, reading_active, split_arms


def _active(arms, endif, node, ctx):
    """Account directives and inactive arms; return the chosen arm's raw items."""
    choice = chosen_arm(node, arms, ctx)
    content = []
    for directive, items in arms:
        ctx.accounting.mark(directive, "directive")
        if directive.start == choice:
            content = items
        else:
            for c in items:
                ctx.accounting.mark(c, "inactive-arm")
    ctx.accounting.mark(endif, "directive")
    return content


def _lower_all(items, ctx, parent_kind):
    nodes = []
    for c in items:
        r = lower(c, ctx.child(parent_kind, c.field or "<children>"))
        if r.frags:
            raise LoweringError("unconsumed-fragment", c, "fragment inside an assembled run")
        nodes.extend(r.nodes)
    return nodes


def _terminator(tail, node, ctx, what):
    """An optional trailing `;` -> [Terminator]. Anything else is a shape error."""
    if not tail:
        return []
    if len(tail) != 1 or tail[0].kind != ";":
        raise LoweringError("contract-shape", node, f"{what} tail: {[t.kind for t in tail]}")
    return [Terminator(None, _lower_all(tail, ctx, node.kind)[0])]


def split_code_block_end(node, ctx) -> Lowered:
    """Contract split-code-block-end. Host: the last child of a `code_block`
    (policy `consumed`). Emits no nodes, only fragments. Rewrites allowed:

    A  arm `preproc_split_end [;]`:
       * `preproc_split_end` -> the code_block's `end_keyword` (BlockCompletion,
         no statements; token alias, same interval);
       * `;` -> Terminator, landing after the statement that owns the code_block
         in the nearest statement host.
    B  arm `stmts… end_keyword else_keyword begin_keyword stmts… end_keyword [;]`:
       * the leading statements, with their `;`, are appended to the code_block's
         `statement_block` (created as its `body` if the block had none);
       * the first `end_keyword` closes the code_block (BlockCompletion);
       * `else_keyword` + a NEW `code_block(begin_keyword [body: statement_block]
         end_keyword)` -> ElseAttachment, which only the `if_statement` whose
         `then_branch` is this code_block consumes: the else keyword and the new
         block (field `else_branch`) become that if_statement's last children.
         Any other owner leaves it unconsumed, which is an error;
       * the trailing `;` -> Terminator, as in A.
    No other edge changes. Every leaf of the chosen arm is kept; every leaf of
    the other arms is `inactive-arm`; directives are `directive`.
    """
    ctx.policy(contracts.REGISTRY[node.kind], node)
    arms, endif = split_arms(node)
    arm = _active(arms, endif, node, ctx)
    if not arm:
        raise LoweringError("contract-shape", node, "empty arm")
    if arm[0].kind == "preproc_split_end":
        end = _lower_all(arm[:1], ctx, node.kind)[0]
        return Lowered([], [BlockCompletion(None, [], end)] + _terminator(arm[1:], node, ctx, "shape A"))
    ends = [i for i, c in enumerate(arm) if c.kind == "end_keyword"]
    if len(ends) != 2 or arm[ends[0] + 1].kind != "else_keyword" or arm[ends[0] + 2].kind != "begin_keyword":
        raise LoweringError("contract-shape", node, "shape B: " + " ".join(c.kind for c in arm))
    first, second = ends
    lead = _lower_all(arm[:first], ctx, "statement_block")
    end1, else_kw, begin = _lower_all(arm[first:first + 3], ctx, "code_block")
    inner = _lower_all(arm[first + 3:second], ctx, "statement_block")
    end2 = _lower_all([arm[second]], ctx, "code_block")[0]
    kids = [begin]
    if inner:
        kids.append(_span_from_children(Node("statement_block", True, "body", 0, 0, inner)))
    kids.append(end2)
    branch = _span_from_children(Node("code_block", True, "else_branch", 0, 0, kids))
    return Lowered([], [BlockCompletion(None, lead, end1), ElseAttachment(None, else_kw, branch)]
                   + _terminator(arm[second + 1:], node, ctx, "shape B"))


def split_procedure(node, ctx) -> Lowered:
    """Contract split-procedure. Host: a declaration-body repeat slot (policy
    per registry). Rewrites allowed:
      * the chosen arm's `_procedure_header` pieces followed by every piece after
        `#endif` (the shared `_procedure_tail`, lowered in place with host
        `procedure:<children>`) become ONE `procedure` node carrying this node's
        field, pieces keeping their own fields and order;
      * the chosen arm's `attribute_item`s are lifted out and become PRECEDING
        SIBLINGS of that procedure, in source order, as in the reference.
    A chosen arm with no header (an #if without #else, inactive) is a shape
    error: there is no procedure to build. Fragments are refused.
    """
    ctx.policy(contracts.REGISTRY[node.kind], node)
    cut = next((i for i, c in enumerate(node.children) if c.kind == "preproc_endif"), None)
    if cut is None:
        raise LoweringError("contract-shape", node, "no #endif")
    arms, endif = split_arms(node.copy(children=node.children[:cut + 1]))
    header = _active(arms, endif, node, ctx)
    if not any(h.kind == "procedure_keyword" for h in header):
        raise LoweringError("contract-shape", node, "chosen arm has no procedure header")
    attrs = _lower_all([h for h in header if h.kind == "attribute_item"], ctx, node.kind)
    parts = _lower_all([h for h in header if h.kind != "attribute_item"] + node.children[cut + 1:],
                       ctx, "procedure")
    proc = _span_from_children(Node("procedure", True, node.field, 0, 0, parts))
    return Lowered(attrs + [proc])


def split_case_statement_end(node, ctx) -> Lowered:
    """Contract split-case-end. Host: a statement position (policy per registry).
    Children: `case_keyword expression of_keyword [body: case_body] pattern-run ':'`
    then an #if/#elif/#else group whose every arm is ONE
    `preproc_split_case_end_branch` = `body [;] end_keyword ; following: statement_block`.
    Rewrites allowed:
      * the pieces before `#if` plus the chosen branch assemble ONE `case_statement`
        carrying this node's field, children in the reference's order:
        `case_keyword expression of_keyword body: case_body end_keyword`;
      * the pattern run (fields `pattern`, `,`) and `:`, followed by the branch's
        `body` statement and its optional `;`, form a NEW final `case_branch`
        appended to the `case_body` (created, field `body`, if the node had none);
        a Terminator the body slot emits is consumed by that case_branch;
      * the branch's `end_keyword` is the case_statement's `end_keyword`;
      * the `;` after it -> Terminator anchored to the case_statement;
      * the `following` statement_block is dissolved: its statements -> Following
        anchored to the case_statement, i.e. SIBLINGS after it (and after its `;`)
        in the host, never inside it.
    Every piece is lowered through `lower()`, so a `preproc_conditional_case_patterns`
    in the pattern run raises unsupported-type (milestone 2). Anything else in the
    shape is contract-shape; a fragment escaping the case or `following` is refused.
    """
    ctx.policy(contracts.REGISTRY[node.kind], node)
    cut = next((i for i, c in enumerate(node.children) if c.kind == "preproc_if"), None)
    of = next((i for i, c in enumerate(node.children) if c.kind == "of_keyword"), None)
    if cut is None or of is None or of > cut:
        raise LoweringError("contract-shape", node, "expected `case … of` before #if")
    lead, rest = node.children[:of + 1], node.children[of + 1:cut]
    body = rest[0] if rest and rest[0].kind == "case_body" and rest[0].field == "body" else None
    patterns = rest[1:] if body is not None else rest
    if len(patterns) < 2 or patterns[-1].kind != ":":
        raise LoweringError("contract-shape", node, "no `pattern… :` before #if")
    arms, endif = split_arms(node.copy(children=node.children[cut:]))
    arm = _active(arms, endif, node, ctx)
    if len(arm) != 1 or arm[0].kind != "preproc_split_case_end_branch":
        raise LoweringError("contract-shape", node, "chosen arm is not one case_end_branch")
    br = arm[0]
    ctx.child(node.kind, "<children>").policy(contracts.REGISTRY[br.kind], br)
    ends = [i for i, c in enumerate(br.children) if c.kind == "end_keyword"]
    tail = br.children[ends[0]:] if len(ends) == 1 else []
    if len(tail) != 3 or tail[1].kind != ";" or tail[2].field != "following"             or tail[2].kind != "statement_block" or ends[0] == 0:
        raise LoweringError("contract-shape", br, "expected `body [;] end ; following:` "
                            + " ".join(f"{c.field}:{c.kind}" if c.field else c.kind for c in br.children))
    end_kw, semi, following = tail
    branch = Node("case_branch", True, None, patterns[0].start, br.children[ends[0] - 1].end,
                  patterns + br.children[:ends[0]])
    case_body = body.copy(children=body.children + [branch]) if body is not None         else Node("case_body", True, "body", branch.start, branch.end, [branch])
    raw = Node("case_statement", True, node.field, node.start, end_kw.end, lead + [case_body, end_kw])
    r = lower(raw, ctx)
    f = lower(following, ctx.child(br.kind, "following"))
    if r.frags or f.frags:
        raise LoweringError("unconsumed-fragment", node, "fragment escaping the case or `following`")
    case = r.nodes[0]
    stmts = f.nodes[0].children if f.nodes else []
    term = _lower_all([semi], ctx, "statement_block")[0]
    # Order matters: the host inserts each fragment right after the anchor, so the
    # Terminator (inserted last) lands between the case and the Following statements.
    return Lowered([case], [Following(case, stmts), Terminator(case, term)])


def table_relation_select(node, ctx) -> Lowered:
    """Contract else-relation-join (see engine.RelationContinuation). Hosts: a
    `property:value` slot (the whole value is the #if) and a
    `table_relation_value:<children>` slot (the #if continues the relation before
    it). The chosen arm is ONE of: an `else_table_relation_fragment`
    (-> RelationContinuation), or a complete relation value (-> a node taking the
    conditional's own field); then an optional `;` (-> Terminator, terminator-hoist).
    An empty or unselected arm contributes nothing. An arm kind outside the
    registered `arm` set, or anything else, is contract-shape. Any other host
    (policy `unsupported`) is unsupported-type. An arm that is itself a
    whole-value conditional (G3) is lowered by this same contract and its
    nodes and fragments pass through, its nodes taking this conditional's field."""
    if ctx.policy(contracts.REGISTRY[node.kind], node) == "unsupported":
        raise LoweringError("unsupported-type", node, f"host {ctx.parent_kind}:{ctx.slot}")
    arms, endif = split_arms(node)
    arm = _active(arms, endif, node, ctx)
    frags, nodes = [], []
    items = list(arm)
    semi = items.pop() if items and items[-1].kind == ";" else None
    if len(items) > 1 or (items and items[0].kind not in contracts.REGISTRY[node.kind].arm):
        raise LoweringError("contract-shape", node, "arm: " + " ".join(c.kind for c in items))
    if items and items[0].kind == "else_table_relation_fragment":
        frag = items[0]
        if len(frag.children) != 2 or frag.children[0].kind != "else_keyword":
            raise LoweringError("contract-shape", frag, "expected `else else_relation:`")
        else_kw = _lower_all(frag.children[:1], ctx, frag.kind)[0]   # an ordinary node: marked kept once
        rel = _lower_all(frag.children[1:], ctx, frag.kind)[0]
        frags.append(RelationContinuation(None, else_kw, rel))
    elif items and items[0].kind == node.kind:
        r = lower(items[0], ctx.child(node.kind, "<children>"))
        nodes = [n.copy(field=node.field) for n in r.nodes]
        frags += r.frags
    elif items:
        nodes = [n.copy(field=node.field) for n in _lower_all(items, ctx, node.kind)]
    if semi is not None:
        frags.append(Terminator(None, _lower_all([semi], ctx, node.kind)[0]))
    return Lowered(nodes, frags)


# --- One-reading contracts (spec P4). The node's text nests across the #if
# ranges, so its tree shows ONE configuration's nesting, the entry's `reading`.
# That configuration lowers normally; every other one raises `one-reading`,
# which is never a pass.

def _one_reading(node):
    return LoweringError("one-reading", node, node.kind)


def _cut_at_endif(node):
    cut = next((i for i, c in enumerate(node.children) if c.kind == "preproc_endif"), None)
    if cut is None or node.children[0].kind != "preproc_if":
        raise LoweringError("contract-shape", node, "expected `#if ... #endif ...`")
    return cut


def open_statement_reading(node, ctx) -> Lowered:
    """Contract open-statement (reading arm:not-else-led). Host: a statement
    position (policy per registry). If the chosen arm's first item is
    `else_keyword`, raise one-reading: the tree shows that `else` as a SIBLING of
    an if/case already complete before the #if, which no configuration's parse
    has. Otherwise (a complete-prefix arm, or no arm chosen) raise
    unsupported-type: milestone 3. Emits nothing; makes no edge rewrite."""
    ctx.policy(contracts.REGISTRY[node.kind], node)
    cut = _cut_at_endif(node)
    arms, _ = split_arms(node.copy(children=node.children[:cut + 1]))
    choice = chosen_arm(node, arms, ctx)
    arm = next((items for d, items in arms if d.start == choice), [])
    if arm and arm[0].kind == "else_keyword":
        raise _one_reading(node)
    raise LoweringError("unsupported-type", node, "complete-prefix arm (milestone 3)")


def block_end_in_else(node, ctx) -> Lowered:
    """Contract block-end-in-else (reading arm:else). Host: the last child of a
    `code_block` (policy `consumed`). Children: `#if stmts* (#elif stmts*)* #else
    stmts* end_keyword`; the group's #endif is in the NEXT procedure's block
    (preproc_split_block_close_after_endif). In the #else configuration: the #else
    arm's statements, with their `;`, are appended to the code_block's
    `statement_block` and the node's `end_keyword` closes the code_block
    (BlockCompletion). No other edge changes. Directives are `directive`, other
    arms `inactive-arm`. Any other configuration raises one-reading."""
    entry = contracts.REGISTRY[node.kind]
    ctx.policy(entry, node)
    end = node.children[-1]
    if end.kind != "end_keyword" or node.children[0].kind != "preproc_if":
        raise LoweringError("contract-shape", node, "expected `#if ... end`")
    # No #endif of its own: split the arms by position, not via split_arms.
    arms = []
    for c in node.children[:-1]:
        if c.kind in ("preproc_if", "preproc_elif", "preproc_else"):
            arms.append((c, []))
        else:
            arms[-1][1].append(c)
    if not reading_active(node, entry, ctx, arms):
        raise _one_reading(node)
    choice = chosen_arm(node, arms, ctx)
    for d, items in arms:
        ctx.accounting.mark(d, "directive")
        if d.start != choice:
            for c in items:
                ctx.accounting.mark(c, "inactive-arm")
    stmts = _lower_all(arms[-1][1], ctx, "statement_block")
    end_l = _lower_all([end], ctx, "code_block")[0]
    return Lowered([], [BlockCompletion(None, stmts, end_l)])


def block_close_after_endif(node, ctx) -> Lowered:
    """Contract block-close-after-endif (reading arm:else). Host: the last child
    of a `code_block` (policy `consumed`). Children: `#endif stmts* end_keyword`,
    no #if of its own. Its group is `group_of[#endif]`, the same group as the
    preceding preproc_split_block_end_in_else, so both decide the same reading.
    The #else reading is active when `arm_choice[group]` is that group's one
    `#else` directive (found by kind in `resolution.directives`, so an #elif in
    the group cannot be mistaken for it). In it: the #endif is `directive`, the
    statements (with their `;`) are appended to the code_block's
    `statement_block` and the `end` closes it (BlockCompletion). No other edge
    changes. Any other configuration raises one-reading."""
    entry = contracts.REGISTRY[node.kind]
    ctx.policy(entry, node)
    endif, end = node.children[0], node.children[-1]
    if endif.kind != "preproc_endif" or end.kind != "end_keyword" or entry.reading != "arm:else":
        raise LoweringError("contract-shape", node, "expected `#endif ... end`, reading arm:else")
    res = ctx.resolution
    group = res.group_of.get(endif.start)
    if group is None or group not in res.arm_choice:
        raise LoweringError("directive-unknown", node, f"no resolver group for #endif at {endif.start}")
    elses = [d.hash for d in res.directives if d.kind == "else" and res.group_of.get(d.hash) == group]
    if len(elses) != 1 or res.arm_choice[group] != elses[0]:
        raise _one_reading(node)
    ctx.accounting.mark(endif, "directive")
    stmts = _lower_all(node.children[1:-1], ctx, "statement_block")
    end_l = _lower_all([end], ctx, "code_block")[0]
    return Lowered([], [BlockCompletion(None, stmts, end_l)])


_REOPEN_KIND = {"group_keyword": "group_section", "repeater_keyword": "repeater_section",
                "cuegroup_keyword": "cuegroup_section", "fixed_keyword": "fixed_section",
                "grid_keyword": "grid_section"}


def container_reopen(node, ctx) -> Lowered:
    """Contract container-reopen (reading arm:if). Host: the closing position of
    a layout container's body block (`<kind>_section:<children>`, policy
    `consumed`). Children: `#if } <kw> ( name ) { [body] #endif [body] }`. In the
    #if configuration, the named rewrite **container-reopen**:
      * the arm's `}` closes the host container: returned as a node, at the
        position a plain `}` takes;
      * the header (`<kw>`, `(`, `name`, `)`), `{`, both body halves merged into
        ONE `layout_container_body` (field `body`) and the final `}` build a NEW
        container of the matching kind (group_keyword -> group_section, ...),
        returned as SiblingsAfter: inserted right after the host container in its
        layout body.
    No other edge changes. Directives are `directive`. Any other configuration
    raises one-reading."""
    entry = contracts.REGISTRY[node.kind]
    ctx.policy(entry, node)
    cut = _cut_at_endif(node)
    head, tail = node.children[1:cut], node.children[cut + 1:]
    if not reading_active(node, entry, ctx, [(node.children[0], head)]):
        raise _one_reading(node)
    header = [c for c in head[1:] if c.field != "body"]
    if not head or head[0].kind != "}" or not header or header[0].kind not in _REOPEN_KIND \
            or header[-1].kind != "{" or not tail or tail[-1].kind != "}":
        raise LoweringError("contract-shape", node, " ".join(c.kind for c in node.children))
    ctx.accounting.mark(node.children[0], "directive")
    ctx.accounting.mark(node.children[cut], "directive")
    close = _lower_all(head[:1], ctx, node.kind)[0]
    halves = [c for c in head[1:] + tail[:-1] if c.field == "body"]
    body = [Node("layout_container_body", True, "body", halves[0].start, halves[-1].end,
                 [k for h in halves for k in h.children])] if halves else []
    kind = _REOPEN_KIND[header[0].kind]
    raw = Node(kind, True, None, header[0].start, tail[-1].end, header + body + tail[-1:])
    r = lower(raw, ctx.child(ctx.parent_kind, ctx.slot))
    if r.frags:
        raise LoweringError("unconsumed-fragment", node, "fragment escaping the reopened container")
    return Lowered([close], [SiblingsAfter(None, r.nodes)])


# --- Expressions split across #if arms (contracts expression-continuation and
# operand-prefix). Both regroup a binary chain by the alc-measured precedence
# table (lowering/expression.py), never by grammar.js prec() values.

def _pairs(nodes, first, second, node):
    """Lowered `first second first second ...` (by field) -> [(first, second)]."""
    if len(nodes) % 2 or any(n.field != (first, second)[i % 2] for i, n in enumerate(nodes)):
        raise LoweringError("contract-shape", node, "expected " + f"{first} {second} pairs: "
                            + " ".join(f"{n.field}:{n.kind}" for n in nodes))
    return list(zip(nodes[::2], nodes[1::2]))


def expression_tail(node, ctx) -> Lowered:
    """Contract expression-continuation. Host: the position right after the
    expression it continues (census hosts, policy `consumed`). Children:
    `#if (operator operand)+ (#elif ...)* [#else ...] #endif (operator operand)*`.
    The chosen arm's `(operator, operand)` pairs, then the pairs after `#endif`,
    extend the IMMEDIATELY PRECEDING lowered sibling (ExpressionContinuation, a
    ToPrevious fragment): that expression and every operand are flattened and
    recomposed by the precedence table, keeping the preceding sibling's field.
    The one other rewrite is **property-expression-unwrap** (see
    engine.ExpressionContinuation): a host property_expression whose lowered
    content is not one of its member kinds is replaced by that content. No
    other edge changes; emits no nodes. Directives are `directive`, other
    arms `inactive-arm`, every other leaf `kept`."""
    ctx.policy(contracts.REGISTRY[node.kind], node)
    cut = next((i for i, c in enumerate(node.children) if c.kind == "preproc_endif"), None)
    if cut is None:
        raise LoweringError("contract-shape", node, "no #endif")
    arms, endif = split_arms(node.copy(children=node.children[:cut + 1]))
    arm = _active(arms, endif, node, ctx)
    pieces = _lower_all(list(arm) + node.children[cut + 1:], ctx, node.kind)
    return Lowered([], [ExpressionContinuation(None, _pairs(pieces, "operator", "operand", node))])


def operand_prefix(top, ctx) -> Lowered:
    """Contract operand-prefix. Called only from engine.lower's binary hook, with
    the TOP binary node of a chain (expression.chain) holding at least one
    `preproc_operand_prefix`; a prefix sits between its binary node's operator
    and right operand. Each prefix's chosen arm is ONE `(operand, operator)`
    pair, which takes the prefix's place; no arm chosen contributes nothing,
    leaving `left op right`. The named rewrite: the WHOLE chain -- every atom,
    operator and chosen pair, in source order -- is flattened and recomposed by
    the precedence table, keeping the top node's field. The whole chain, not
    just the prefix's own binary node, because the arm's operator may bind
    looser than an enclosing one (`a * #if X b or #endif c + d` is
    `(a*b) or (c+d)` with X). Directives are `directive`, other arms
    `inactive-arm`, every other leaf `kept`."""
    if top.kind not in expression.BINARY_KINDS:
        raise LoweringError("contract-shape", top, "operand prefix outside a binary chain")
    try:
        items = expression.chain(top)
    except ValueError as e:
        raise LoweringError("contract-shape", top, str(e)) from None
    flat = []
    for parent, n in items:
        if n.kind == expression.PREFIX:
            ctx.child(parent, "<children>").policy(contracts.REGISTRY[n.kind], n)
            arms, endif = split_arms(n)
            pairs = _pairs(_lower_all(_active(arms, endif, n, ctx), ctx, n.kind), "operand", "operator", n)
            if len(pairs) > 1:
                raise LoweringError("contract-shape", n, f"{len(pairs)} operand/operator pairs in one arm")
            for operand, op in pairs:
                flat += _flatten(operand) + [op]
        else:
            flat += _flatten(_lower_all([n], ctx, parent)[0])
    return Lowered([expression.compose(flat, top.field)])


def _flatten(node):
    try:
        return expression.flatten(node)
    except ValueError as e:
        raise LoweringError("contract-shape", node, str(e)) from None
