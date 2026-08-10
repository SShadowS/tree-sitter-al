import json
from pathlib import Path

import pytest

from tools.query_coverage import loader, model
from tools.query_coverage.detectors import fields


@pytest.fixture(scope="module")
def grammar():
    return json.loads((loader.REPO_ROOT / "src" / "grammar.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def node_types():
    return json.loads((loader.REPO_ROOT / "src" / "node-types.json").read_text(encoding="utf-8"))


def test_finds_the_known_dropped_operator_fields(grammar, node_types):
    """Self-test. A set-level implementation returns zero here.

    Four operator fields were dropped when this detector was written.
    37771f1 fixed two of them by making `_assignment_operator` a visible rule;
    the is_expression/as_expression pair is still dropped and still carried in
    tools/query_coverage/baseline.json as fields|is_expression|operator and
    fields|as_expression|operator.

    Both halves are asserted. The two that must still be found keep the
    detector honest against a set-level rewrite; the two that must NOT be
    found are the ratchet on 37771f1 -- a revert puts them back and turns this
    test red.
    """
    findings = fields.detect_static(grammar, node_types)

    dropped = {
        (f.detail["rule"], f.detail["field"])
        for f in findings
        if f.category == "dropped-field"
    }

    assert ("is_expression", "operator") in dropped
    assert ("as_expression", "operator") in dropped
    assert ("assignment_statement", "operator") not in dropped
    assert ("assignment_expression", "operator") not in dropped


def test_does_not_flag_a_field_that_survives(grammar, node_types):
    findings = fields.detect_static(grammar, node_types)

    dropped = {(f.detail["rule"], f.detail["field"]) for f in findings}

    assert ("assignment_statement", "left") not in dropped
    assert ("assignment_statement", "right") not in dropped


def test_set_level_check_would_miss_operator(grammar, node_types):
    """Guards against the mis-implementation: 'operator' exists on other types.

    Asking "does the name 'operator' appear anywhere in node-types.json"
    answers yes on eight types, so a set-level detector reports zero findings
    and is dead on arrival. The example is is_expression/as_expression: both
    declare field('operator', ...) in the grammar, neither owns it in
    node-types.json. It used to be assignment_statement, which 37771f1 fixed
    -- it now legitimately owns the field, so it can no longer play this role.

    Declaring the field is asserted too, not assumed: a rule absent from the
    left-hand list would make the right-hand list trivially true.
    """
    owners = [n["type"] for n in node_types if "operator" in n.get("fields", {})]
    declared = {rule for rule, field_name in fields.collect_declared_fields(grammar) if field_name == "operator"}

    assert len(owners) >= 6
    assert {"is_expression", "as_expression"} <= declared
    assert "is_expression" not in owners
    assert "as_expression" not in owners


def test_hidden_rules_are_skipped_not_flagged(grammar, node_types):
    """"Skipped, not flagged": a hidden rule's field may still surface as a
    skipped-scope Finding (one per declaration, bucketed by reason — see
    test_skipped_scope_count_moves_with_population), but it must never be
    reported as a dropped-field finding, which is what would make v1 scope
    look like a real defect.
    """
    findings = fields.detect_static(grammar, node_types)

    dropped = [f for f in findings if f.category == "dropped-field"]
    for finding in dropped:
        assert not finding.detail["rule"].startswith("_")


def test_aliased_rules_are_skipped(grammar, node_types):
    aliased = fields.alias_targets(grammar)
    findings = fields.detect_static(grammar, node_types)

    assert "permissions_property" in aliased
    dropped = [f for f in findings if f.category == "dropped-field"]
    for finding in dropped:
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


def test_named_and_anonymous_entries_of_the_same_type_do_not_shadow():
    """Regression: node-types.json can list two entries sharing a "type" when
    a rule name coincides with an anonymous keyword token of the same
    spelling (real instance: the "procedure" rule vs. the anonymous
    "procedure" keyword token). A naive {entry["type"]: entry} dict
    comprehension is last-wins; with the anonymous (fieldless) entry last,
    it shadows the real named entry and every field the rule declares is
    reported dropped. Only named entries may own fields.
    """
    grammar = {
        "rules": {
            "widget": {
                "type": "SEQ",
                "members": [
                    {"type": "FIELD", "name": "gadget", "content": {"type": "SYMBOL", "name": "x"}},
                ],
            }
        }
    }
    node_types = [
        {"type": "widget", "named": True, "fields": {"gadget": {}}},
        {"type": "widget", "named": False},
    ]

    findings = fields.detect_static(grammar, node_types)

    dropped = {(f.detail["rule"], f.detail["field"]) for f in findings if f.category == "dropped-field"}
    assert ("widget", "gadget") not in dropped


def _grammar_with_hidden_fields(count: int) -> dict:
    return {
        "rules": {
            "_hidden_rule": {
                "type": "SEQ",
                "members": [
                    {
                        "type": "FIELD",
                        "name": f"f{i}",
                        "content": {"type": "SYMBOL", "name": "x"},
                    }
                    for i in range(count)
                ],
            }
        }
    }


def test_skipped_scope_count_moves_with_population():
    """baseline.diff() acts on Cluster.count. A single summary Finding pins
    count at 1 no matter how many declarations it represents, so growth or
    shrinkage of the skipped population is invisible to the gate. One
    Finding per skipped declaration, bucketed by reason, makes the count
    track the real population: 2 hidden-rule fields -> count 2, adding a
    third -> count 3. Asserting "some skipped findings exist" would not
    prove this; only watching the count move across a population change does.
    """
    findings_two = fields.detect_static(_grammar_with_hidden_fields(2), [])
    cluster_two = model.cluster(findings_two)
    hidden_two = next(
        c for c in cluster_two if c.key == model.fingerprint_key(fields.DETECTOR, ("skipped", fields.REASON_HIDDEN_RULE))
    )
    assert hidden_two.count == 2

    findings_three = fields.detect_static(_grammar_with_hidden_fields(3), [])
    cluster_three = model.cluster(findings_three)
    hidden_three = next(
        c
        for c in cluster_three
        if c.key == model.fingerprint_key(fields.DETECTOR, ("skipped", fields.REASON_HIDDEN_RULE))
    )
    assert hidden_three.count == 3


def test_dynamic_flags_a_synthetic_required_field(al_parser):
    """Drive the detector with a node type we KNOW cannot satisfy the requirement.

    Asserting over the real node-types.json would pass vacuously on a healthy
    tree. Injecting an impossible requirement proves the detector fires.

    The requirement has to stay impossible, which is why it is no longer
    'operator': that was impossible on assignment_statement only until 37771f1
    made the operator a real field, after which this test silently stopped
    exercising the detector at all. 'condition' is a real field name in this
    grammar -- if_statement and thirteen other types own one -- and an
    assignment statement can never carry it, so the requirement cannot be
    satisfied by any parse of any source.
    """
    impossible = [
        {
            "type": "assignment_statement",
            "named": True,
            "fields": {"condition": {"multiple": False, "required": True, "types": []}},
        }
    ]
    source = b"codeunit 1 T { procedure P() begin i := 1; end; }"

    findings = fields.detect_dynamic(al_parser.parse(source), source, "t.al", impossible)

    assert len(findings) == 1
    assert findings[0].category == "required-field-missing"
    assert findings[0].fingerprint == ("assignment_statement", "condition")


def test_dynamic_is_silent_when_the_required_field_is_present(al_parser):
    satisfied = [
        {
            "type": "assignment_statement",
            "named": True,
            "fields": {"left": {"multiple": False, "required": True, "types": []}},
        }
    ]
    source = b"codeunit 1 T { procedure P() begin i := 1; end; }"

    assert fields.detect_dynamic(al_parser.parse(source), source, "t.al", satisfied) == []


def test_dynamic_is_quiet_on_a_clean_tree(al_parser, node_types):
    source = b"codeunit 1 T { }"

    assert fields.detect_dynamic(al_parser.parse(source), source, "t.al", node_types) == []
