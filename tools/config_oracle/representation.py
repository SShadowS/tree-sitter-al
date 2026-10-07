"""Contracts on the multi-configuration tree, BEFORE lowering (spec section 3).

These catch defects that configuration equivalence cannot see: two different
wrappers that lower to the same configured program (defect 5) -- e.g. a
pragma-only #if misparsed as an empty var block.
"""
from __future__ import annotations

from tools.config_oracle import contracts
from tools.config_oracle.compare import Discrepancy
from tools.config_oracle.lowering import conditional_lists
from tools.config_oracle.lowering.engine import LoweringError
from tools.config_oracle.lowering.select import split_arms

# The only parents preproc_conditional_var_block has in the grammar
# (grammar.js:3007, 3078: _routine_regular_body, _procedure_preamble, both
# hidden rules that inline straight into these four hosts). Derived from
# contracts.py's hand-maintained _ROUTINE_TAIL_HOSTS rather than duplicated,
# so the two can't drift apart.
VAR_BLOCK_HOSTS = {h.split(":", 1)[0] for h in contracts.REGISTRY["preproc_conditional_var_block"].hosts}


def check(root):
    """Walk the whole tree (iterative -- BC.History has real files thousands of
    levels deep) and report every representation-contract violation."""
    out = []
    stack = [(root, None)]
    while stack:
        n, parent = stack.pop()
        try:
            if n.kind == "preproc_conditional_var_block" and parent in VAR_BLOCK_HOSTS:
                arms, _ = split_arms(n)
                if not any(c.kind == "var_section" for _, content in arms for c in content):
                    out.append(Discrepancy("representation", "var-block-without-var",
                                            f"{n.kind}@{n.start}", parent))
            elif n.kind == "preproc_pragma_only":
                arms, _ = split_arms(n)
                if any(content for _, content in arms):
                    out.append(Discrepancy("representation", "pragma-only-with-structure",
                                            f"{n.kind}@{n.start}", parent))
        except LoweringError as err:
            out.append(Discrepancy("representation", "malformed-group",
                                    f"{n.kind}@{n.start}", err.detail or err.kind))
        for c in reversed(n.children):
            stack.append((c, n.kind))
    # B7b-1 strict conditional lists, spec 2026-10-07 section 6.1 (pre-selection attachment).
    for p in conditional_lists.validate_split(root):
        path, _, what = p.partition(": ")
        out.append(Discrepancy("representation", "strict-list", path, what))
    return out
