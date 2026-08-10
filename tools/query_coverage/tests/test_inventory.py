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


def test_extracts_object_identity_for_extension_and_interface_declarations(al_language, al_parser):
    """Regression for Important-A: `objects` was empty for every
    extension-style object type (pageextension, tableextension, ...) because
    inventory.scm's object-identity section only covered the 7 types in the
    brief's original skeleton. interface_declaration is the pick called out
    in the fix request as a representative id-less object kind.
    """
    cases = [
        (
            b'pageextension 50100 "My Ext" extends "Customer Card" { }',
            "pageextension_declaration",
            "50100",
            '"My Ext"',
        ),
        (
            b'tableextension 50100 "My Table Ext" extends "Customer" { }',
            "tableextension_declaration",
            "50100",
            '"My Table Ext"',
        ),
        (b"interface IMyInterface { }", "interface_declaration", None, "IMyInterface"),
    ]

    for source, expected_type, expected_id, expected_name in cases:
        result = inventory.extract(al_language, al_parser.parse(source), source)
        assert result["objects"] == [
            {"type": expected_type, "id": expected_id, "name": expected_name}
        ], source


def test_inventory_scm_covers_every_object_bearing_declaration_type(node_types):
    """Guards against Important-A-class regressions going forward: every
    node type node-types.json gives an `object_name` field must have a
    pattern in inventory.scm, or a newly introduced object kind (a new
    extension flavor, say) silently vanishes from `objects` again.
    """
    scm = inventory.SCM_PATH.read_text(encoding="utf-8")
    missing = [
        object_type
        for object_type in inventory.object_declaration_types(node_types)
        if f"({object_type} " not in scm
    ]
    assert missing == []


def test_multi_name_variable_declaration_is_a_single_entry(al_language, al_parser):
    """Regression for Important-B: `A, B, C: Integer;` produced three
    fragmented entries sharing one byte_range instead of one entry with
    three names, because captures["variable.name"] only ever held the first
    of the multiple `name` occurrences per match (see the task-13 fix
    report for why extract() now consolidates by byte range instead).
    """
    source = b"codeunit 1 T { procedure P() var A, B, C: Integer; begin end; }"

    result = inventory.extract(al_language, al_parser.parse(source), source)

    assert len(result["variables"]) == 1
    assert result["variables"][0]["name"] == ["A", "B", "C"]
    assert result["variables"][0]["type"] == "Integer"


def test_single_name_variable_declaration_still_yields_one_entry(al_language, al_parser):
    """The consolidation fix must not collapse distinct declarations that
    happen to share a type — each single-name `variable_declaration` node
    has its own byte range and must stay its own entry.
    """
    source = b"codeunit 1 T { procedure P() var A: Integer; B: Integer; begin end; }"

    result = inventory.extract(al_language, al_parser.parse(source), source)

    assert len(result["variables"]) == 2
    assert result["variables"][0]["name"] == ["A"]
    assert result["variables"][1]["name"] == ["B"]
