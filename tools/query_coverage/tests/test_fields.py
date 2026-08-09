import json
from pathlib import Path

import pytest

from tools.query_coverage import loader
from tools.query_coverage.detectors import fields


@pytest.fixture(scope="module")
def grammar():
    return json.loads((loader.REPO_ROOT / "src" / "grammar.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def node_types():
    return json.loads((loader.REPO_ROOT / "src" / "node-types.json").read_text(encoding="utf-8"))


def test_finds_the_four_known_dropped_operator_fields(grammar, node_types):
    """Self-test. A set-level implementation returns zero here."""
    findings = fields.detect_static(grammar, node_types)

    dropped = {(f.detail["rule"], f.detail["field"]) for f in findings}

    assert ("assignment_statement", "operator") in dropped
    assert ("assignment_expression", "operator") in dropped
    assert ("is_expression", "operator") in dropped
    assert ("as_expression", "operator") in dropped


def test_does_not_flag_a_field_that_survives(grammar, node_types):
    findings = fields.detect_static(grammar, node_types)

    dropped = {(f.detail["rule"], f.detail["field"]) for f in findings}

    assert ("assignment_statement", "left") not in dropped
    assert ("assignment_statement", "right") not in dropped


def test_set_level_check_would_miss_operator(node_types):
    """Guards against the mis-implementation: 'operator' exists on other types."""
    owners = [n["type"] for n in node_types if "operator" in n.get("fields", {})]

    assert len(owners) >= 6
    assert "assignment_statement" not in owners


def test_hidden_rules_are_skipped_not_flagged(grammar, node_types):
    findings = fields.detect_static(grammar, node_types)

    for finding in findings:
        assert not finding.detail["rule"].startswith("_")


def test_aliased_rules_are_skipped(grammar, node_types):
    aliased = fields.alias_targets(grammar)
    findings = fields.detect_static(grammar, node_types)

    assert "permissions_property" in aliased
    for finding in findings:
        assert finding.detail["rule"] not in aliased


def test_collect_declared_fields_finds_nested_fields():
    grammar = {
        "rules": {
            "r": {
                "type": "SEQ",
                "members": [
                    {"type": "FIELD", "name": "a", "content": {"type": "SYMBOL", "name": "x"}},
                    {
                        "type": "CHOICE",
                        "members": [
                            {"type": "FIELD", "name": "b", "content": {"type": "SYMBOL", "name": "y"}}
                        ],
                    },
                ],
            }
        }
    }

    assert sorted(fields.collect_declared_fields(grammar)) == [("r", "a"), ("r", "b")]
