"""The single-configuration parse, extracted as the comparator (spec section 2)."""
from __future__ import annotations

from dataclasses import dataclass

from tools.config_oracle import ir

_EXTRA_PREPROC = {"preproc_region", "preproc_endregion", "preproc_define", "preproc_undef"}


@dataclass
class ReferenceResult:
    root: ir.Node
    extras: list
    problems: list


def extract(parser, masked: bytes) -> ReferenceResult:
    root, extras, problems = ir.from_tree(parser.parse(masked))
    stack = [root]
    while stack:
        n = stack.pop()
        if n.kind.startswith("preproc") and n.kind not in _EXTRA_PREPROC:
            problems.append(f"resolver-leak:{n.kind}@{n.start}")
        stack.extend(n.children)
    return ReferenceResult(root, extras, problems)
