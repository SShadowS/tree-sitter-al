"""Read-only helpers over tree-sitter's src/grammar.json."""
import json
from pathlib import Path

TRANSPARENT = {"FIELD", "ALIAS", "PREC", "PREC_LEFT", "PREC_RIGHT", "PREC_DYNAMIC", "RESERVED"}
LEXICAL = {"TOKEN", "IMMEDIATE_TOKEN"}


def load(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {"rules": data["rules"], "inline": set(data.get("inline", [])),
            "extras": data.get("extras", [])}


def children(node):
    if "members" in node:
        return list(enumerate(node["members"]))
    if "content" in node:
        return [(0, node["content"])]
    return []


def iter_nodes(node, path="", ancestors=()):
    yield path, node, ancestors
    for i, child in children(node):
        yield from iter_nodes(child, f"{path}.{i}" if path else str(i), ancestors + (node,))
