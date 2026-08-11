"""The anchor table: lexical occurrence -> the node types that must account for it.

This is data, deliberately committed and reviewable, because "compare against
the corresponding node counts" diverges the moment anyone implements it.
`field(` in AL source is not only field_declaration: it is also a page control
(field(N; Source)), the field reference inside link properties (SubPageLink =
X = field(Y)) and inside CalcFormula/TableRelation (where(X = field(Y))). A
naive comparison mismatches on every page with a link property, and the
tempting fix is to subtract fudge factors until it balances.

Prefer 1:1 mappings against visible keyword nodes wherever one exists — those
are exact and self-explaining. A multi-type sum is a last resort for an anchor
whose keyword is hidden, and 4.0.0 removed the last one: every anchor below now
maps to a single node type. `field(` is the worked example of why that rule is
worth following rather than a style preference — see its entry.

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
    # `field(` was EXCLUDED until 4.0.0, twice over, and the history matters
    # because both reasons look like permanent properties of AL and neither is.
    #
    #   1. Originally: "a field reference inside a where() clause produces no
    #      node". True when written; false as of 5a39bcf, which named the
    #      where()/link marker `field_keyword`.
    #   2. Then: a field header split across #if branches spells `field(` once
    #      per branch but yields ONE preproc_split_field for all of them, so no
    #      node-type SUM can express that 1:N mapping.
    #
    # Reason 2 was correct about the sum and wrong about the conclusion. The
    # 1:N node still exists — but `field_keyword` is emitted once per LEXICAL
    # spelling, including once per #if branch, so counting the keyword alone
    # sidesteps the collapsed node entirely rather than trying to reconcile it.
    #
    # Censused over all 15,358 BC.History files on the merged 4.0.0 grammar:
    # 96,729 lexical `field(` sites and 96,729 field_keyword nodes — exact, in
    # 0 mismatching files. The old four-type sum now DOUBLE-counts, because
    # every declaration carries a nested field_keyword of its own
    # (field_declaration 36,145 + page_field 47,738 + preproc_split_field 1
    # are all additional to the 96,729, not components of it); it mismatches on
    # 6,371 files. Do not restore the sum, and do not re-exclude this anchor
    # without first re-running that census — both prior reasons were true when
    # written and were falsified by a later grammar fix, not by an error.
    Anchor("field(", _NO_DOT + r"field\s*\(", ("field_keyword",)),
)

# Intentionally empty since 4.0.0: every anchor above is checked. The mechanism
# is kept, not removed — `qc.write_summary` still renders a "Coverage
# deliberately not checked" section from this dict, so re-excluding an anchor
# publishes the reason automatically. An exclusion belongs here ONLY with a
# reason that is falsifiable by measurement; see the `field(` note above for
# what happens to one that is merely plausible. Report it, never silently drop
# it: the no-silent-caps rule applies.
EXCLUDED_ANCHORS: dict[str, str] = {}
