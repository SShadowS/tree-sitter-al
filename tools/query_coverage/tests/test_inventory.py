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


def _synthetic_property(value_type: str) -> list[dict]:
    return [
        {
            "type": "property",
            "named": True,
            "fields": {
                "value": {
                    "multiple": False,
                    "required": True,
                    "types": [{"type": value_type, "named": True}],
                }
            },
        }
    ]


def test_meta_check_reports_a_value_type_with_no_inventory_pattern():
    """Inject a value type the .scm provably does not mention.

    Running against the real node-types.json passes vacuously while the generic
    (property ...) pattern covers everything, so it proves nothing.
    """
    findings = inventory.meta_check(
        _synthetic_property("zzz_nonexistent_value_type"), generic_covers_all=False
    )

    assert len(findings) == 1
    assert findings[0].category == "inventory-stale"
    assert findings[0].detail["value_type"] == "zzz_nonexistent_value_type"


def test_meta_check_is_silent_when_the_generic_pattern_covers_everything(node_types):
    assert inventory.meta_check(node_types) == []


def test_a_value_type_named_only_in_a_comment_is_not_coverage():
    """The per-type fallback is a text search over the .scm, so a type
    mentioned in a `;` comment used to satisfy it. A comment is documentation,
    not extraction.
    """
    assert inventory.scm_mentions("(ml_value_list) @v", "ml_value_list")
    assert not inventory.scm_mentions("; see (ml_value_list) for details", "ml_value_list")


def test_a_longer_pattern_name_does_not_satisfy_a_shorter_type():
    """`(caption_value_list ...)` must not stand in for `caption_value`.

    No such collision exists in inventory.scm today — the point is that adding
    one must not silently mark a distinct type as covered, and the bare
    substring test it replaces would have.
    """
    assert not inventory.scm_mentions("(caption_value_list) @v", "caption_value")
    assert inventory.scm_mentions("(caption_value) @v", "caption_value")
    assert inventory.scm_mentions("(caption_value someField: (_)) @v", "caption_value")


def test_meta_check_flags_a_declared_value_type_with_no_pattern():
    """End to end through meta_check, not just the helper. `property_expression`
    is a real declared property value type and inventory.scm has no pattern for
    it — only the generic `(property …)` one, which the wildcard makes
    sufficient in practice and which `generic_covers_all=False` takes away.
    """
    assert not inventory.scm_mentions(
        inventory.SCM_PATH.read_text(encoding="utf-8"), "property_expression"
    )

    findings = inventory.meta_check(
        _synthetic_property("property_expression"), generic_covers_all=False
    )

    assert [f.detail["value_type"] for f in findings] == ["property_expression"]


def test_meta_check_is_reported_as_vacuous_while_the_wildcard_stands(node_types):
    """The check runs, skips all 30 declared value types, and emits nothing.

    That is correct behaviour, but silence is indistinguishable from a broken
    detector, so it must be REPORTED. qc.write_summary prints this list.
    """
    reported = inventory.inert_checks(node_types)

    assert [name for name, _reason in reported] == ["inventory.meta_check"]
    assert str(len(inventory.property_value_types(node_types))) in reported[0][1]


def test_narrowing_the_value_wildcard_makes_the_check_live_again():
    """The vacuity report is derived from the .scm, not written down.

    `value: (_)` is what makes every property value type covered. Narrow it
    and inert_checks() must empty itself while meta_check starts gating --
    with no second edit to keep the two consistent.
    """
    assert inventory.generic_property_pattern_covers_all(
        "(property name: (property_name) @property.name value: (_) @property.value) @property"
    )
    assert not inventory.generic_property_pattern_covers_all(
        "(property name: (property_name) @property.name "
        "value: (property_expression) @property.value) @property"
    )


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


def test_preproc_split_declaration_is_a_single_object_entry(al_language, al_parser):
    """Same bug class as the multi-name variable case, found while fixing it:
    preproc_split_declaration's object_name field is also `multiple: true`
    (one occurrence per #if/#elif/#else branch — grammar.js:323-353), so it
    hit the identical one-match-per-occurrence behavior. Unlike variables,
    an object's name is a scalar in this schema, so the fix here dedupes to
    the first branch rather than merging into a list.
    """
    source = b"""
#if CONDITION
codeunit 50100 "Test Impl" implements Interface1, Interface2
#else
codeunit 50100 "Test Impl" implements Interface2
#endif
{
    procedure TestMethod()
    begin
    end;
}
"""

    result = inventory.extract(al_language, al_parser.parse(source), source)

    assert result["objects"] == [
        {"type": "preproc_split_declaration", "id": "50100", "name": '"Test Impl"'}
    ]
