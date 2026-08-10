"""Semantic inventory extraction, and the meta-check that keeps it honest."""

from __future__ import annotations

from pathlib import Path

from .model import Finding

DETECTOR = "inventory"
SCM_PATH = Path(__file__).with_name("inventory.scm")

# Nested inside field/key/control/action declarations to pull properties that
# live below the top-level (property ...) match (e.g. a page field's Caption).
_PROPERTIES_QUERY_SOURCE = "(property name: (property_name) @n value: (_) @v)"


def _text(node, source: bytes) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def extract(language, tree, source: bytes) -> dict:
    """Produce the artifact a human or an LLM reads when writing corrections.

    Not an assertion: comparing a capture's text to the source bytes at that
    capture's own range always passes.
    """
    import tree_sitter

    query = tree_sitter.Query(language, SCM_PATH.read_text(encoding="utf-8"))
    cursor = tree_sitter.QueryCursor(query)
    # Compiled once and reused by every _properties_within() call below,
    # rather than recompiling this tiny query per field/key/control/action —
    # those nest arbitrarily many times inside one object.
    properties_query = tree_sitter.Query(language, _PROPERTIES_QUERY_SOURCE)

    result: dict = {
        "objects": [],
        "fields": [],
        "procedures": [],
        "properties": [],
        "triggers": [],
        "enum_values": [],
        "keys": [],
        "variables": [],
        "controls": [],
        "actions": [],
    }

    for _index, captures in cursor.matches(tree.root_node):
        if "object" in captures:
            node = captures["object"][0]
            result["objects"].append(
                {
                    "type": node.type,
                    "id": _text(captures["object.id"][0], source),
                    "name": _text(captures["object.name"][0], source),
                }
            )
        elif "field" in captures:
            node = captures["field"][0]
            result["fields"].append(
                {
                    "id": _text(captures["field.id"][0], source),
                    "name": _text(captures["field.name"][0], source),
                    "byte_range": [node.start_byte, node.end_byte],
                    "properties": _properties_within(properties_query, node, source),
                }
            )
        elif "procedure" in captures:
            node = captures["procedure"][0]
            result["procedures"].append(
                {
                    "name": _text(captures["procedure.name"][0], source),
                    "byte_range": [node.start_byte, node.end_byte],
                    "parameters": _parameters_within(node, source),
                }
            )
        elif "property" in captures:
            node = captures["property"][0]
            result["properties"].append(
                {
                    "name": _text(captures["property.name"][0], source),
                    "value": _text(captures["property.value"][0], source),
                    "byte_range": [node.start_byte, node.end_byte],
                }
            )
        elif "trigger" in captures:
            node = captures["trigger"][0]
            result["triggers"].append(
                {
                    "name": _text(captures["trigger.name"][0], source),
                    "byte_range": [node.start_byte, node.end_byte],
                    "parameters": _parameters_within(node, source),
                }
            )
        elif "enum" in captures:
            node = captures["enum"][0]
            result["enum_values"].append(
                {
                    "id": _text(captures["enum.id"][0], source),
                    "name": _text(captures["enum.name"][0], source),
                    "byte_range": [node.start_byte, node.end_byte],
                }
            )
        elif "key" in captures:
            node = captures["key"][0]
            result["keys"].append(
                {
                    "name": _text(captures["key.name"][0], source),
                    "fields": _text(captures["key.fields"][0], source),
                    "byte_range": [node.start_byte, node.end_byte],
                    "properties": _properties_within(properties_query, node, source),
                }
            )
        elif "variable" in captures:
            node = captures["variable"][0]
            result["variables"].append(
                {
                    "name": [_text(n, source) for n in captures["variable.name"]],
                    "type": _text(captures["variable.type"][0], source),
                    "byte_range": [node.start_byte, node.end_byte],
                }
            )
        elif "control" in captures:
            node = captures["control"][0]
            result["controls"].append(
                {
                    "type": node.type,
                    "name": _text(captures["control.name"][0], source),
                    "byte_range": [node.start_byte, node.end_byte],
                    "properties": _properties_within(properties_query, node, source),
                }
            )
        elif "action" in captures:
            node = captures["action"][0]
            entry: dict = {
                "type": node.type,
                "byte_range": [node.start_byte, node.end_byte],
                "properties": _properties_within(properties_query, node, source),
            }
            if "action.name" in captures:
                entry["name"] = _text(captures["action.name"][0], source)
            if "action.action_name" in captures:
                entry["action_name"] = _text(captures["action.action_name"][0], source)
            if "action.promoted_name" in captures:
                entry["promoted_name"] = _text(captures["action.promoted_name"][0], source)
            result["actions"].append(entry)

    return result


def _properties_within(properties_query, node, source: bytes) -> list[dict]:
    import tree_sitter

    cursor = tree_sitter.QueryCursor(properties_query)
    out = []
    for _index, captures in cursor.matches(node):
        out.append(
            {
                "name": _text(captures["n"][0], source),
                "value": _text(captures["v"][0], source),
            }
        )
    return out


def _parameters_within(node, source: bytes) -> list[dict]:
    out = []
    stack = list(node.children)
    while stack:
        current = stack.pop()
        if current.type == "parameter":
            name = current.child_by_field_name("name")
            out.append({"name": _text(name, source) if name else ""})
        stack.extend(current.children)
    return out


def property_value_types(node_types: list[dict]) -> list[str]:
    for entry in node_types:
        if entry["type"] != "property":
            continue
        return sorted(t["type"] for t in entry.get("fields", {}).get("value", {}).get("types", []))
    return []


def meta_check(
    language, node_types: list[dict], generic_covers_all: bool | None = None
) -> list[Finding]:
    """Fail when a property value type has no inventory pattern.

    Complex properties follow no naming convention — only two rules match
    *_property, the rest are value-shape rules like ml_value_list and
    table_relation_value — so a new one slips in silently without this.

    generic_covers_all=None derives coverage from the .scm. Pass False to force
    per-value-type checking; without that the check cannot be tested
    non-vacuously while the generic (property ...) pattern matches everything.
    """
    scm = SCM_PATH.read_text(encoding="utf-8")
    findings: list[Finding] = []

    if generic_covers_all is None:
        covered_generically = "(property name: (property_name)" in scm
    else:
        covered_generically = generic_covers_all

    for value_type in property_value_types(node_types):
        if covered_generically or f"({value_type}" in scm:
            continue
        findings.append(
            Finding(
                detector=DETECTOR,
                category="inventory-stale",
                fingerprint=("uncovered-value-type", value_type),
                path="tools/query_coverage/inventory.scm",
                byte_offset=0,
                line=0,
                column=0,
                enclosing="property",
                snippet=f"property value type {value_type} has no inventory pattern",
                detail={"value_type": value_type},
            )
        )

    return findings
