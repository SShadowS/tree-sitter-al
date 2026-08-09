"""The anchor table: lexical occurrence -> the node types that must account for it.

This is data, deliberately committed and reviewable, because "compare against
the corresponding node counts" diverges the moment anyone implements it.
`field(` in AL source is not only field_declaration: it is also the field
reference inside link properties (SubPageLink = X = field(Y)) and inside
CalcFormula/TableRelation (where(X = field(Y))). A naive comparison mismatches
on every page with a link property, and the tempting fix is to subtract fudge
factors until it balances.

Prefer 1:1 mappings against visible keyword nodes wherever one exists — those
are exact and self-explaining. The multi-type sums are only for the anchors
whose keyword is hidden.

Validate each sum once at `accept` time, then treat any drift as a finding.
"""

from __future__ import annotations

from dataclasses import dataclass

# Not preceded by '.', so member access (x.Procedure) is excluded.
_NO_DOT = r"(?<![.\w])"


@dataclass(frozen=True)
class Anchor:
    name: str
    pattern: str
    node_types: tuple[str, ...]


ANCHORS: tuple[Anchor, ...] = (
    Anchor("procedure", _NO_DOT + r"procedure\b", ("procedure_keyword",)),
    Anchor("trigger", _NO_DOT + r"trigger\b", ("trigger_keyword",)),
    Anchor("key(", _NO_DOT + r"key\s*\(", ("key_declaration",)),
    Anchor("value(", _NO_DOT + r"value\s*\(", ("enum_value_declaration",)),
    Anchor("action(", _NO_DOT + r"action\s*\(", ("action_declaration",)),
)

# `field(` is deliberately absent — see the note below. Report it, never
# silently drop it: the no-silent-caps rule applies.
EXCLUDED_ANCHORS: dict[str, str] = {
    "field(": (
        "a field reference inside a where() clause produces no node, so the "
        "lexical and structural counts cannot be reconciled by any node-type sum"
    ),
}
