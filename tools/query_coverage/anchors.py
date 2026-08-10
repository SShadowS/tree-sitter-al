"""The anchor table: lexical occurrence -> the node types that must account for it.

This is data, deliberately committed and reviewable, because "compare against
the corresponding node counts" diverges the moment anyone implements it.
`field(` in AL source is not only field_declaration: it is also a page control
(field(N; Source)), the field reference inside link properties (SubPageLink =
X = field(Y)) and inside CalcFormula/TableRelation (where(X = field(Y))). A
naive comparison mismatches on every page with a link property, and the
tempting fix is to subtract fudge factors until it balances.

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
#
# The original reason ("a field reference inside a where() clause produces no
# node") was true when this was written and is FALSE as of 5a39bcf, which named
# the where()/link markers: `field_keyword` accounts for every one of them.
# Censused on this branch over all 15,358 BC.History files: 96,729 lexical
# `field(` sites, of which page_field 47,738 + field_declaration 36,145 +
# field_keyword 12,844 + preproc_split_field 2, and ZERO owned by nothing. The
# reason below is what the same census left behind, and it is a different
# shape of problem: not a missing node, but one node standing for several
# occurrences.
EXCLUDED_ANCHORS: dict[str, str] = {
    "field(": (
        "a field header split across #if branches collapses one `field(` per "
        "branch into a single preproc_split_field node, so the counts differ "
        "by (branches - 1) and no node-type sum can express a 1:N mapping. "
        "Every other `field(` in BC.History is accounted for exactly, by "
        "field_declaration, page_field or field_keyword; corpus-wide this "
        "affects 1 file of 15,358"
    ),
}
