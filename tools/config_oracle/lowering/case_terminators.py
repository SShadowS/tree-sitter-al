"""Case-branch separators (B7b-3 spec section 6.2, as amended by the Task 6/7 rulings).

A case branch's `;` that sits alone in an `#if` arm of a `preproc_conditional_case` is an
`empty_statement` in the split tree (spec 4.1). A configuration that selects it reads that `;` as
the preceding branch's separator. Three pieces:

  * **marking** (select.branch_select): every `empty_statement` that is a direct arm child of a
    `preproc_conditional_case` is marked CASE_SEMI, mixed and nested arms included. The mark lives
    on the lowered node, so it survives splicing through enclosing arms. It is never the
    statement-block ARM_SEMI.
  * **attachment** (`attach`, run by the engine on a `case_body` once its whole run is selected):
    a marked `;` goes to the IMMEDIATELY preceding item only, and only when that is an
    unterminated `case_branch` (a lowered split-case wrapper is a case_branch by then). Where the
    flat grammar puts it: into the branch's body when that body is a node owning an optional
    trailing `;` it lacks (SEMI_OWNING_BODIES), otherwise onto the branch, outside `body`.
    Anything else before it (a terminated branch, an empty_statement, the run start) leaves the
    `empty_statement` in place, never a search further back. Logged `case-terminator-attach@<;>`.
  * **decorations** (`case_group` under a DECORATION_HOSTS slot): a directive-only empty group
    before a branch's own `;` is deleted by selection. Every arm, inactive ones included, is first
    validated as recursively directive-only; anything else is refused, never discarded.

Else ownership (spec 4.4) is `check_else_ownership`, decided from the lowered (selected) case run,
never from the reference parse.
"""
from __future__ import annotations

from tools.config_oracle import contracts
from tools.config_oracle.ir import Node
from tools.config_oracle.lowering.engine import Lowered, LoweringError, _span_from_children

CASE_SEMI = "_case_semi"
GROUP = "preproc_conditional_case"

# The hosts whose own `;` may be preceded by decorations (grammar caseEmptyGroup; spec 4.2.2 plus
# the fourth host from the Task 6 fix-round-1 ruling). The registry gives each slot policy
# "decoration"; this tuple is what the tests compare that registry with.
DECORATION_HOSTS = ("case_branch", "preproc_split_case_branch", "preproc_split_case_extended",
                    "preproc_split_case_end_branch")

# Statement rules that END in optional(';') (Task 6 report, "For Task 7"), so the flat grammar
# puts a following `;` INSIDE them. Hand-written; test_case_terminators derives the same set from
# src/grammar.json, so a grammar change that adds or drops one fails the test.
SEMI_OWNING_BODIES = ("preproc_split_if_begin_asymmetric", "preproc_split_if_then_begin_else_shared")


def _is_semi(n):
    return n.kind == ";" and not n.children and n.field is None


def terminated(node):
    """Termination is the node's OWN direct `;`, outside any field. A `;` inside the body never counts."""
    return any(_is_semi(c) for c in node.children)


def _target(out):
    """Index of the item a marked `;` attaches to, or None. Only the immediately preceding one."""
    if out and out[-1].kind == "case_branch" and not terminated(out[-1]):
        return len(out) - 1
    return None


def _append(branch, semi, ctx):
    body = next((c for c in branch.children if c.field == "body"), None)
    if body is None:     # its whole body was removed by selection: the `;` is the body (flat `1: ;`)
        ctx.normalised.append(f"empty-body-terminator@{semi.start}")
        return _span_from_children(branch.copy(children=branch.children + [_body_semi(semi)]))
    ctx.normalised.append(f"case-terminator-attach@{semi.start}")
    if body.kind in SEMI_OWNING_BODIES and not terminated(body):
        new_body = _span_from_children(body.copy(children=body.children + [semi]))
        kids = [new_body if c is body else c for c in branch.children]
    else:
        kids = branch.children + [semi]
    return _span_from_children(branch.copy(children=kids))


def attach(kids, ctx):
    out = []
    for n in kids:
        if getattr(n, CASE_SEMI, False):
            at = _target(out)
            if at is not None:
                out[at] = _append(out[at], n.children[0], ctx)
                continue
        out.append(n)
    for b in out:
        if b.kind == "case_branch" and not any(c.field == "body" for c in b.children):
            raise LoweringError("policy", b, "case_branch body removed and no `;` to take its place")
    return out


def _body_semi(semi):
    return Node("empty_statement", True, "body", semi.start, semi.end, [semi])


def empty_body(orig, new, ctx):
    """Named rewrite **empty-body-terminator**. Selection removed the WHOLE body of a case branch
    (its body was an `#if` group that lowers to nothing): the flat text is `1: ;`, which the
    grammar reads as `body: empty_statement(;)`. So the branch's own `;` becomes that body, logged
    `empty-body-terminator@<offset>`. With no own `;`, a selected case-group `;` right after the
    branch takes that place (`attach`); a branch left with no body at all is refused there."""
    if not any(c.field == "body" for c in orig.children) or any(c.field == "body" for c in new.children):
        return
    at = next((i for i, c in enumerate(new.children) if _is_semi(c)), None)
    if at is not None:
        ctx.normalised.append(f"empty-body-terminator@{new.children[at].start}")
        new.children[at] = _body_semi(new.children[at])


# --- decorations ----------------------------------------------------------------------------

def _validate_decoration(node):
    """Every arm of `node`, inactive ones included, holds only nested decorations."""
    from tools.config_oracle.lowering.select import split_arms
    arms, _ = split_arms(node)
    for _, content in arms:
        for c in content:
            if c.kind != GROUP:
                raise LoweringError("contract-shape", c, f"{c.kind} in a case decoration (directive-only)")
            _validate_decoration(c)


def _delete_decoration(node, ctx):
    from tools.config_oracle.lowering.select import chosen_arm, split_arms
    arms, endif = split_arms(node)
    choice = chosen_arm(node, arms, ctx)
    for directive, content in arms:
        ctx.accounting.mark(directive, "directive")
        for c in content:
            if directive.start == choice:
                _delete_decoration(c, ctx)
            else:
                ctx.accounting.mark(c, "inactive-arm")
    ctx.accounting.mark(endif, "directive")


def decoration(node, ctx) -> Lowered:
    _validate_decoration(node)
    _delete_decoration(node, ctx)
    return Lowered([])


def case_group(node, ctx) -> Lowered:
    """The one handler of preproc_conditional_case, dispatched by the host slot's policy."""
    from tools.config_oracle.lowering.select import branch_select
    if ctx.policy(contracts.REGISTRY[node.kind], node) == "decoration":
        return decoration(node, ctx)
    return branch_select(node, ctx)


# --- else ownership (spec 4.4) ----------------------------------------------------------------

_BODY_FIELDS = {"if_statement": "else_branch", "while_statement": "body", "for_statement": "body",
                "foreach_statement": "body", "with_statement": "body", "asserterror_statement": "body"}


def _takes_else(stmt):
    """True when a following `else` would bind inside `stmt`: an if with no else, at the end of it."""
    while stmt is not None:
        if stmt.kind == "if_statement" and not any(c.field == "else_branch" for c in stmt.children):
            return True
        f = _BODY_FIELDS.get(stmt.kind)
        if f is None:
            return False
        stmt = next((c for c in stmt.children if c.field == f), None)
    return False


def check_else_ownership(case, ctx):
    """The tree gives a `case_else_branch` to the case. Where the selected run leaves the last
    branch unterminated and its body ends in an if with no else, the flat reading gives that
    `else` to the if instead (`1: if C then Foo else Bar;`). No tree holds both readings, so that
    configuration is refused as one-reading (debt B12), never passed."""
    if not any(c.kind == "case_else_branch" for c in case.children):
        return
    body = next((c for c in case.children if c.field == "body" and c.kind == "case_body"), None)
    last = body.children[-1] if body is not None and body.children else None
    if last is None or last.kind != "case_branch" or terminated(last):
        return
    stmt = next((c for c in last.children if c.field == "body"), None)
    if _takes_else(stmt):
        els = next(c for c in case.children if c.kind == "case_else_branch")
        raise LoweringError("one-reading", els, "host case_statement:<children>")
