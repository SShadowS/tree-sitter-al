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


def detect_static(grammar: dict, node_types: list[dict]) -> list[Finding]:
    """v1 scope: visible, un-aliased rules only. Everything else is reported skipped."""
    aliased = alias_targets(grammar)
    by_type = {entry["type"]: entry for entry in node_types}
    rules = grammar["rules"]

    findings: list[Finding] = []
    skipped: list[str] = []

    for rule, field_name in collect_declared_fields(grammar):
        if rule.startswith("_"):
            skipped.append(f"{rule}.{field_name} (hidden rule)")
            continue
        if rule in aliased:
            skipped.append(f"{rule}.{field_name} (aliased at use site)")
            continue

        entry = by_type.get(rule)
        if entry is None:
            skipped.append(f"{rule}.{field_name} (rule absent from node-types.json)")
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

    if skipped:
        findings.append(
            Finding(
                detector=DETECTOR,
                category="skipped-scope",
                fingerprint=("skipped", "hidden-or-aliased"),
                path="grammar.js",
                byte_offset=0,
                line=0,
                column=0,
                enclosing="grammar",
                snippet=f"{len(skipped)} field declarations outside v1 scope",
                # "rule"/"field" are dummy placeholders, not a real dropped field:
                # every test in test_fields.py reads finding.detail["rule"] on
                # every returned Finding unconditionally (see
                # test_hidden_rules_are_skipped_not_flagged and
                # test_aliased_rules_are_skipped), so this entry must carry the
                # same keys as a dropped-field finding or it KeyErrors there.
                # category="skipped-scope" is how a consumer tells it apart
                # from a real dropped-field finding.
                detail={
                    "rule": "<skipped>",
                    "field": "<summary>",
                    "skipped": sorted(skipped),
                },
            )
        )

    return findings
