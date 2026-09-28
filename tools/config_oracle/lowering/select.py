"""Branch selection, token aliases (spec section 3, "Branch selection")."""
from __future__ import annotations

from tools.config_oracle import contracts
from tools.config_oracle.ir import Node
from tools.config_oracle.lowering.engine import Lowered, LoweringError, Terminator, bind_previous, lower

DIRECTIVES = ("preproc_if", "preproc_elif", "preproc_else")

HOIST_TERMINATOR = True   # mutation switch for the terminator-hoist contract test


def _splice_arm(items):
    """The chosen arm's lowered items, in order. A seam for the separator mutation test."""
    return items


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
    """Lower an #if group to its chosen arm, under the host slot's policy.

    **list-run.** The chosen arm's items AND separators splice into the host list
    in order. A trailing `;` in the arm is not spliced: it becomes a `Terminator`
    (named rewrite **terminator-hoist**), which passes up through the list and is
    appended as the last child of the owning `property`. After the host list is
    built, it must read `item (, item)*`, ignoring bracket tokens (`(`, `)`, `[`,
    `]`) wherever they appear and one trailing `;` (`engine._check_alternation`).
    Anything else is `list-separator`.
    """
    entry = contracts.REGISTRY[node.kind]
    policy = ctx.policy(entry, node)
    if policy not in ("splice-repeat", "single-slot", "optional-slot", "list-run"):
        raise LoweringError("policy", node, f"branch-select cannot apply policy {policy!r}")
    arms, endif = split_arms(node)
    choice = chosen_arm(node, arms, ctx)
    out = Lowered([])
    for directive, content in arms:
        ctx.accounting.mark(directive, "directive")
        if directive.start == choice:
            for c in content:
                if entry.arm is not None and c.kind not in entry.arm:
                    raise LoweringError("arm-content", c, f"{c.kind} not declared for {node.kind}")
                r = lower(c, ctx.child(node.kind, c.field or "<children>"))
                out.frags.extend(bind_previous(out.nodes, r, c))
        else:
            for c in content:
                ctx.accounting.mark(c, "inactive-arm")
    ctx.accounting.mark(endif, "directive")
    if policy == "list-run":
        out.nodes = _splice_arm(out.nodes)
        if HOIST_TERMINATOR and out.nodes and out.nodes[-1].kind == ";" and not out.nodes[-1].children:
            semi = out.nodes.pop()
            out.frags.append(Terminator(None, semi))
    if policy in ("single-slot", "optional-slot"):
        # An arm of exactly [statement, ';']: the grammar put the ENCLOSING
        # statement's terminator inside the arm (BC.History
        # AOAIAuthorization.Codeunit.al). The `;` becomes a Terminator anchored to
        # the statement, so it lands after the enclosing statement in its host,
        # as in the reference. Nothing else is exempt from the count below.
        if len(out.nodes) == 2 and not out.frags and out.nodes[0].named \
                and out.nodes[1].kind == ";" and not out.nodes[1].children:
            stmt, semi = out.nodes
            out = Lowered([stmt], [Terminator(stmt, semi)])
        # single-slot: exactly one node; optional-slot: at most one (spec section 3).
        allowed = (1,) if policy == "single-slot" else (0, 1)
        if len(out.nodes) not in allowed:
            raise LoweringError("policy", node, f"{len(out.nodes)} nodes into a {policy}")
        for n in out.nodes:
            n.field = node.field   # in place: fresh lowered node, and fragment anchors keep identity
    return out


def reading_active(node, entry, ctx, arms=None):
    """True when the resolved configuration is the one the tree shows (spec P4).
    `arms` overrides split_arms for a node that is not a whole #if ... #endif group."""
    if arms is None:
        arms, _ = split_arms(node)
    choice = chosen_arm(node, arms, ctx)
    first = arms[0][0].start
    if entry.reading == "arm:if":
        return choice == first
    if entry.reading == "arm:else":
        return choice is not None and choice != first and arms[-1][0].kind == "preproc_else" \
            and choice == arms[-1][0].start
    if entry.reading == "arm:inactive":
        return choice is None
    raise LoweringError("contract-shape", node, f"reading {entry.reading!r} needs its own test")


def token_alias(node, ctx) -> Lowered:
    entry = contracts.REGISTRY[node.kind]
    ctx.policy(entry, node)
    if node.children:
        raise LoweringError("contract-shape", node, "token alias with children")
    ctx.accounting.mark(node, "kept")
    return Lowered([Node(entry.alias_to, True, node.field, node.start, node.end, [])])
