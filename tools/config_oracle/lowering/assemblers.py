"""Assemblers: construct configured nodes from pieces across arms (spec section 3).

Each function's docstring IS its contract, including every edge rewrite it is
allowed to make. Anything not named there is an error.
"""
from __future__ import annotations

from tools.config_oracle import contracts
from tools.config_oracle.ir import Node
from tools.config_oracle.lowering.engine import (BlockCompletion, ElseAttachment, Following, Lowered,
                                                 LoweringError, RelationContinuation, Terminator,
                                                 _span_from_children, lower)
from tools.config_oracle.lowering.select import chosen_arm, split_arms


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
    """Contract else-relation-join (see engine.RelationContinuation). Host: a
    `property:value` slot. The chosen arm is ONE of: an `else_table_relation_fragment`
    (-> RelationContinuation), or a complete relation value (-> a node with field
    `value`); then an optional `;` (-> Terminator, terminator-hoist). An empty or
    unselected arm contributes nothing. Anything else is contract-shape. Any
    other host (policy `unsupported`) is unsupported-type."""
    if ctx.policy(contracts.REGISTRY[node.kind], node) == "unsupported":
        raise LoweringError("unsupported-type", node, f"host {ctx.parent_kind}:{ctx.slot}")
    arms, endif = split_arms(node)
    arm = _active(arms, endif, node, ctx)
    frags, nodes = [], []
    items = list(arm)
    semi = items.pop() if items and items[-1].kind == ";" else None
    if len(items) > 1:
        raise LoweringError("contract-shape", node, "arm: " + " ".join(c.kind for c in items))
    if items and items[0].kind == "else_table_relation_fragment":
        frag = items[0]
        if len(frag.children) != 2 or frag.children[0].kind != "else_keyword":
            raise LoweringError("contract-shape", frag, "expected `else else_relation:`")
        else_kw = _lower_all(frag.children[:1], ctx, frag.kind)[0]   # an ordinary node: marked kept once
        rel = _lower_all(frag.children[1:], ctx, frag.kind)[0]
        frags.append(RelationContinuation(None, else_kw, rel))
    elif items:
        nodes = [n.copy(field="value") for n in _lower_all(items, ctx, node.kind)]
    if semi is not None:
        frags.append(Terminator(None, _lower_all([semi], ctx, node.kind)[0]))
    return Lowered(nodes, frags)
