"""Assemblers: construct configured nodes from pieces across arms (spec section 3).

Each function's docstring IS its contract, including every edge rewrite it is
allowed to make. Anything not named there is an error.
"""
from __future__ import annotations

from tools.config_oracle import contracts
from tools.config_oracle.ir import Node
from tools.config_oracle.lowering.engine import (BlockCompletion, ElseAttachment, Lowered, LoweringError,
                                                 Terminator, _span_from_children, lower)
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
