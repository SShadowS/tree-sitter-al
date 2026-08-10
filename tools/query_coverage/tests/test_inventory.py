import json

import pytest

from tools.query_coverage import inventory, loader


@pytest.fixture(scope="module")
def node_types():
    return json.loads((loader.REPO_ROOT / "src" / "node-types.json").read_text(encoding="utf-8"))


def test_extracts_a_field_caption_matching_the_source(al_language, al_parser):
    source = b"table 50000 Foo { fields { field(1; Name; Text[50]) { Caption = 'Hello'; } } }"

    result = inventory.extract(al_language, al_parser.parse(source), source)

    captions = [
        prop["value"]
        for field in result["fields"]
        for prop in field["properties"]
        if prop["name"].lower() == "caption"
    ]
    assert captions == ["'Hello'"]


def test_extracts_object_identity(al_language, al_parser):
    source = b"table 50000 Foo { }"

    result = inventory.extract(al_language, al_parser.parse(source), source)

    assert result["objects"] == [
        {"type": "table_declaration", "id": "50000", "name": "Foo"}
    ]


def test_extracts_procedures_with_parameters(al_language, al_parser):
    source = b"codeunit 1 T { procedure Add(a: Integer; b: Integer): Integer begin end; }"

    result = inventory.extract(al_language, al_parser.parse(source), source)

    assert result["procedures"][0]["name"] == "Add"
    assert len(result["procedures"][0]["parameters"]) == 2


def test_property_value_types_are_enumerable(node_types):
    types = inventory.property_value_types(node_types)

    assert len(types) > 10
    assert "string_literal" in types


def test_meta_check_reports_a_value_type_with_no_inventory_pattern(al_language):
    """Inject a value type the .scm provably does not mention.

    Running against the real node-types.json passes vacuously while the generic
    (property ...) pattern covers everything, so it proves nothing.
    """
    synthetic = [
        {
            "type": "property",
            "named": True,
            "fields": {
                "value": {
                    "multiple": False,
                    "required": True,
                    "types": [{"type": "zzz_nonexistent_value_type", "named": True}],
                }
            },
        }
    ]

    findings = inventory.meta_check(al_language, synthetic, generic_covers_all=False)

    assert len(findings) == 1
    assert findings[0].category == "inventory-stale"
    assert findings[0].detail["value_type"] == "zzz_nonexistent_value_type"


def test_meta_check_is_silent_when_the_generic_pattern_covers_everything(al_language, node_types):
    assert inventory.meta_check(al_language, node_types) == []
