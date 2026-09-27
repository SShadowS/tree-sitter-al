"""Branch selection, token aliases (spec section 3, "Branch selection")."""
from __future__ import annotations

from tools.config_oracle import contracts
from tools.config_oracle.ir import Node
from tools.config_oracle.lowering.engine import Lowered, LoweringError, lower

DIRECTIVES = ("preproc_if", "preproc_elif", "preproc_else")


def split_arms(node):
    arms, endif, current = [], None, None
    for c in node.children:
        if c.kind in DIRECTIVES:
            if endif is not None:
                raise LoweringError("contract-shape", node, f"{c.kind} after #endif")
            current = (c, [])
            arms.append(current)
        elif c.kind == "preproc_endif":
            if endif is not None:
                raise LoweringError("contract-shape", node, "two #endif")
            endif = c
        elif current is None or endif is not None:
            raise LoweringError("contract-shape", node, f"content outside the arms: {c.kind}")
        else:
            current[1].append(c)
    if not arms or arms[0][0].kind != "preproc_if" or endif is None:
        raise LoweringError("contract-shape", node, "not an #if ... #endif group")
    return arms, endif


def chosen_arm(node, arms, ctx):
    key = arms[0][0].start
    if key not in ctx.resolution.arm_choice:
        raise LoweringError("directive-unknown", node, f"no resolver group at {key}")
    choice = ctx.resolution.arm_choice[key]
    if choice is not None and all(d.start != choice for d, _ in arms):
        raise LoweringError("directive-unknown", node, f"resolver chose {choice}, not a directive of this group")
    return choice


def branch_select(node, ctx) -> Lowered:
    entry = contracts.REGISTRY[node.kind]
    policy = ctx.policy(entry, node)
    if policy not in ("splice-repeat", "single-slot"):
        raise LoweringError("policy", node, f"branch-select cannot apply policy {policy!r}")
    arms, endif = split_arms(node)
    choice = chosen_arm(node, arms, ctx)
    out = Lowered([])
    for directive, content in arms:
        ctx.accounting.mark(directive, "directive")
        if directive.start == choice:
            for c in content:
                r = lower(c, ctx.child(node.kind, c.field or "<children>"))
                out.nodes.extend(r.nodes)
                out.frags.extend(r.frags)
        else:
            for c in content:
                ctx.accounting.mark(c, "inactive-arm")
    ctx.accounting.mark(endif, "directive")
    if policy == "single-slot":
        if len(out.nodes) > 1:
            raise LoweringError("policy", node, f"{len(out.nodes)} nodes into a single slot")
        out.nodes = [n.copy(field=node.field) for n in out.nodes]
    return out


def token_alias(node, ctx) -> Lowered:
    entry = contracts.REGISTRY[node.kind]
    ctx.policy(entry, node)
    if node.children:
        raise LoweringError("contract-shape", node, "token alias with children")
    ctx.accounting.mark(node, "kept")
    return Lowered([Node(entry.alias_to, True, node.field, node.start, node.end, [])])
