"""Detector 3: fields declared in the grammar that vanish from the tree.

A `field('x', ...)` wrapping a hidden token is silently dropped. The live
instance that motivated this: assignment_statement declares
field('operator', $._assignment_operator), _assignment_operator is a
token(choice(...)), and the tree exposes only left and right.

CRITICAL: the check is per-owning-type. The field name 'operator' exists on
six other node types, so asking "does this name appear anywhere in
node-types.json" reports zero findings and the detector is dead on arrival.
"""

from __future__ import annotations

from typing import Any, Iterator

from ..model import Finding
from . import _tree

DETECTOR = "fields"

# Grammar node types whose "content" key wraps a single child node, walked
# through when resolving a field's content down to its underlying token shape.
_UNWRAP_TYPES = {
    "TOKEN",
    "IMMEDIATE_TOKEN",
    "PREC",
    "PREC_LEFT",
    "PREC_RIGHT",
    "PREC_DYNAMIC",
    "ALIAS",
}

# Stable reason slugs for skipped-scope findings. Each is a distinct
# fingerprint bucket ("skipped", <reason>), so baseline.diff() sees the real
# per-bucket population count instead of one Finding pinned at count=1
# regardless of how many declarations it summarizes. This matters beyond
# visibility: if a future change to the hidden/aliased scope logic
# accidentally widens and a real dropped-field finding migrates into a skip
# bucket, that bucket's count has to move for the ratchet to catch the
# migration as a regression rather than recording it as improvement.
REASON_HIDDEN_RULE = "hidden-rule"
REASON_ALIASED_AT_USE_SITE = "aliased-at-use-site"
REASON_RULE_ABSENT_FROM_NODE_TYPES = "rule-absent-from-node-types"


def _walk_field_decls(node: Any) -> Iterator[str]:
    if isinstance(node, dict):
        if node.get("type") == "FIELD":
            yield node["name"]
        for value in node.values():
            yield from _walk_field_decls(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_field_decls(item)


def _walk_alias_targets(node: Any) -> Iterator[str]:
    if isinstance(node, dict):
        if node.get("type") == "ALIAS":
            content = node.get("content") or {}
            name = content.get("name")
            if name:
                yield name
        for value in node.values():
            yield from _walk_alias_targets(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_alias_targets(item)


def _find_field_content(node: Any, field_name: str) -> dict | None:
    """First FIELD node matching `field_name` within `node`, or None."""
    if isinstance(node, dict):
        if node.get("type") == "FIELD" and node.get("name") == field_name:
            return node.get("content")
        for value in node.values():
            found = _find_field_content(value, field_name)
            if found is not None:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _find_field_content(item, field_name)
            if found is not None:
                return found
    return None


def _resolves_to_choice(content: Any, rules: dict, seen: set[str] | None = None) -> bool:
    """True if `content` unwraps (through TOKEN/PREC/... and hidden-rule
    SYMBOL references) to a CHOICE with more than one alternative.

    This is the structural test behind operator_collision: a field whose
    underlying token is a single PATTERN/STRING (e.g. is_expression's "is")
    carries no information beyond what the node type already encodes, so
    dropping it loses nothing. A field backed by a CHOICE of several distinct
    spellings (e.g. _assignment_operator's five operators) loses real
    information when dropped, because every alternative collapses onto the
    same node type.
    """
    if seen is None:
        seen = set()
    if not isinstance(content, dict):
        return False

    node_type = content.get("type")
    if node_type == "CHOICE":
        return len(content.get("members", [])) > 1
    if node_type == "SYMBOL":
        name = content.get("name")
        if name is None or name in seen:
            return False
        seen.add(name)
        target = rules.get(name)
        if target is None:
            return False
        return _resolves_to_choice(target, rules, seen)
    if node_type in _UNWRAP_TYPES:
        inner = content.get("content")
        if inner is None:
            return False
        return _resolves_to_choice(inner, rules, seen)
    return False


def alias_targets(grammar: dict) -> set[str]:
    """Rules aliased at a use site surface under the alias target, not their own name."""
    targets: set[str] = set()
    for body in grammar["rules"].values():
        targets.update(_walk_alias_targets(body))
    return targets


def collect_declared_fields(grammar: dict) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for rule_name, body in grammar["rules"].items():
        for field_name in _walk_field_decls(body):
            pairs.append((rule_name, field_name))
    return sorted(set(pairs))


def _skip_finding(rule: str, field_name: str, reason: str) -> Finding:
    """One Finding per skipped declaration, fingerprinted by reason bucket
    (not by rule/field — that would make every skip its own singleton
    cluster and defeat the point of bucketing). `detail` still carries the
    real rule/field so a report reader can see exactly what was skipped.
    """
    return Finding(
        detector=DETECTOR,
        category="skipped-scope",
        fingerprint=("skipped", reason),
        path="grammar.js",
        byte_offset=0,
        line=0,
        column=0,
        enclosing=rule,
        snippet=f"field('{field_name}', ...) in {rule} — skipped ({reason})",
        detail={"rule": rule, "field": field_name, "reason": reason},
    )


def detect_static(grammar: dict, node_types: list[dict]) -> list[Finding]:
    """v1 scope: visible, un-aliased rules only. Everything else is reported
    skipped, one Finding per declaration, bucketed by reason so the count
    moves with the population (see REASON_* for why that matters).
    """
    aliased = alias_targets(grammar)
    # named-only: node-types.json can list two entries sharing a "type" when a
    # rule name coincides with an anonymous keyword token spelled the same way
    # (e.g. the "procedure" rule vs. the anonymous "procedure" keyword token).
    # A grammar rule always produces a *named* node; the anonymous entry is
    # never the field owner. Keying on every entry is last-wins and lets the
    # fieldless anonymous entry shadow the real one, producing a false
    # positive for every field the rule declares.
    by_type = {entry["type"]: entry for entry in node_types if entry.get("named")}
    rules = grammar["rules"]

    findings: list[Finding] = []

    for rule, field_name in collect_declared_fields(grammar):
        if rule.startswith("_"):
            findings.append(_skip_finding(rule, field_name, REASON_HIDDEN_RULE))
            continue
        if rule in aliased:
            findings.append(_skip_finding(rule, field_name, REASON_ALIASED_AT_USE_SITE))
            continue

        entry = by_type.get(rule)
        if entry is None:
            findings.append(_skip_finding(rule, field_name, REASON_RULE_ABSENT_FROM_NODE_TYPES))
            continue

        if field_name in entry.get("fields", {}):
            continue

        content = _find_field_content(rules[rule], field_name)
        operator_collision = _resolves_to_choice(content, rules)

        findings.append(
            Finding(
                detector=DETECTOR,
                category="dropped-field",
                fingerprint=(rule, field_name),
                path="grammar.js",
                byte_offset=0,
                line=0,
                column=0,
                enclosing=rule,
                snippet=f"field('{field_name}', ...) in {rule}",
                detail={
                    "rule": rule,
                    "field": field_name,
                    "reason": "absent from node-types.json",
                    "operator_collision": operator_collision,
                },
            )
        )

    return findings


def _required_fields(node_types: list[dict]) -> dict[str, list[str]]:
    required: dict[str, list[str]] = {}
    for entry in node_types:
        names = [
            name
            for name, spec in entry.get("fields", {}).items()
            if spec.get("required")
        ]
        if names:
            required[entry["type"]] = names
    return required


def detect_dynamic(tree, source: bytes, path: str, node_types: list[dict]) -> list[Finding]:
    """Catch fields that node-types.json promises but a given instance lacks.

    Static analysis cannot see this: a field over a choice() mixing visible and
    hidden alternatives stays in node-types.json yet is absent on the instances
    that took the hidden alternative.
    """
    required = _required_fields(node_types)
    findings: list[Finding] = []

    for node in _tree.walk(tree.root_node):
        if node.has_error:
            continue
        if not node.is_named:
            # node-types.json can list an anonymous entry sharing a "type"
            # string with a named rule (e.g. the "procedure" declaration vs.
            # the anonymous "procedure" keyword-alias leaf inside
            # procedure_keyword — see the same collision guarded against in
            # detect_static). Fields only ever attach to named nodes; without
            # this guard the anonymous leaf is checked against the named
            # entry's requirements and — having no children at all — always
            # "fails" them, flooding every real file with false positives.
            continue
        for field_name in required.get(node.type, ()):
            if node.child_by_field_name(field_name) is not None:
                continue

            line = source[: node.start_byte].count(b"\n") + 1
            findings.append(
                Finding(
                    detector=DETECTOR,
                    category="required-field-missing",
                    fingerprint=(node.type, field_name),
                    path=path,
                    byte_offset=node.start_byte,
                    line=line,
                    column=node.start_point[1] + 1,
                    enclosing=node.type,
                    snippet=source[node.start_byte : node.end_byte][:120].decode(
                        "utf-8", errors="replace"
                    ),
                    detail={"rule": node.type, "field": field_name},
                )
            )

    return findings
