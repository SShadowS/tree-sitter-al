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


# --------------------------------------------------------------------------
# A grammar/node-types pair exhibiting the defect, built rather than borrowed.
#
# Detector 3's static half is a pure function of two JSON documents, so its
# positive control does not need a real grammar at all -- and must not use one.
# It used to point at whichever operator field happened to be dropped at the
# time: first `assignment_statement`, then, after 37771f1 fixed that, the
# `is_expression`/`as_expression` pair. The losslessness work fixed those too,
# and detect_static now reports ZERO dropped fields against the real grammar
# (asserted below), so there is no third defect to re-point at.
#
# That is the end of the pattern, not bad luck: a detector whose only proof of
# life is a live grammar defect goes dark exactly when the grammar is clean,
# which is when you most need to trust it.
# --------------------------------------------------------------------------


def _seq(*members):
    return {"type": "SEQ", "members": list(members)}


def _field(name, content):
    return {"type": "FIELD", "name": name, "content": content}


def _sym(name):
    return {"type": "SYMBOL", "name": name}


def _spec():
    return {"multiple": False, "required": True, "types": [{"type": "identifier", "named": True}]}


# `dropping_expression` declares an `operator` field over a HIDDEN rule, so the
# token is lexed and then belongs to no node -- the exact shape of the defect.
# `keeping_expression` declares the SAME field name and really owns it, which
# is what makes a set-level check answer "yes, `operator` exists somewhere" and
# report nothing at all.
SYNTHETIC_GRAMMAR = {
    "rules": {
        "dropping_expression": _seq(
            _field("left", _sym("identifier")),
            _field("operator", _sym("_hidden_operator")),
            _field("right", _sym("identifier")),
        ),
        "keeping_expression": _seq(_field("operator", _sym("visible_operator"))),
        "_hidden_operator": {
            "type": "TOKEN",
            "content": {
                "type": "CHOICE",
                "members": [
                    {"type": "STRING", "value": ":="},
                    {"type": "STRING", "value": "+="},
                ],
            },
        },
        "visible_operator": {"type": "STRING", "value": "+"},
        "identifier": {"type": "PATTERN", "value": "[a-z]+"},
    }
}

SYNTHETIC_NODE_TYPES = [
    # No "operator" key: that is the dropped field.
    {"type": "dropping_expression", "named": True,
     "fields": {"left": _spec(), "right": _spec()}},
    {"type": "keeping_expression", "named": True, "fields": {"operator": _spec()}},
    {"type": "visible_operator", "named": True, "fields": {}},
    {"type": "identifier", "named": True, "fields": {}},
]


def test_finds_a_dropped_field_that_shares_its_name_with_a_surviving_one():
    """The positive control. A set-level implementation returns zero here.

    Asserted as an exact list, not by membership: membership alone would pass
    on a detector that flagged every declared field, which is the
    over-reporting direction of the same mistake.

    `operator_collision` is asserted too. The hidden rule resolves to a CHOICE
    of two spellings, so dropping the field really does lose information --
    that flag is how a reader tells this apart from a field whose token has
    only one spelling, where the node type already carries everything.
    """
    findings = fields.detect_static(SYNTHETIC_GRAMMAR, SYNTHETIC_NODE_TYPES)

    dropped = [f for f in findings if f.category == "dropped-field"]

    assert [(f.detail["rule"], f.detail["field"]) for f in dropped] == [
        ("dropping_expression", "operator")
    ]
    assert dropped[0].detail["operator_collision"] is True
    assert dropped[0].fingerprint == ("dropping_expression", "operator")


def test_the_real_grammar_drops_no_fields_at_all(grammar, node_types):
    """Ratchet on the losslessness work, and on 37771f1 before it.

    Not "the four known ones are fixed" -- there is no dropped field anywhere
    in the grammar any more, so the whole category is asserted empty. Any
    reintroduction turns this red and names itself in the failure output,
    which a list of four specific pairs could not do.

    This is only safe to assert BECAUSE the test above proves the detector
    still finds one when there is one. Neither half is worth much alone: this
    one passes on a detector that reports nothing, and that one passes on a
    grammar full of defects.
    """
    dropped = [
        (f.detail["rule"], f.detail["field"])
        for f in fields.detect_static(grammar, node_types)
        if f.category == "dropped-field"
    ]

    assert dropped == []


def test_does_not_flag_a_field_that_survives(grammar, node_types):
    findings = fields.detect_static(grammar, node_types)

    dropped = {(f.detail["rule"], f.detail["field"]) for f in findings}

    assert ("assignment_statement", "left") not in dropped
    assert ("assignment_statement", "right") not in dropped


def _set_level_dropped_fields(grammar, node_types):
    """The mis-implementation, written out so it can be RUN rather than described.

    It asks "does this field NAME appear anywhere in node-types.json", which
    answers yes as soon as any single type owns it, and so reports nothing.
    Keeping it executable is the point: a comment asserting that a wrong
    implementation would return zero cannot itself be checked, and this can.
    """
    present = {name for entry in node_types for name in entry.get("fields", {})}
    return sorted(
        {
            rule
            for rule, field_name in fields.collect_declared_fields(grammar)
            if field_name not in present
        }
    )


def test_set_level_check_would_miss_the_dropped_field():
    """The check is per-OWNING-TYPE, not per name. `keeping_expression` owns an
    `operator` field, so the set-level version sees the name present and
    reports zero, while `dropping_expression` is dropping one right beside it.

    This used to be asserted against whichever real rules were dropping
    `operator` at the time -- `assignment_statement`, then the
    `is_expression`/`as_expression` pair. Each fix cost it its example, and
    with the grammar now clean the two implementations agree on zero: the
    comparison would be 0 == 0 and would pass on either one. The synthetic
    pair keeps the two answers apart permanently.
    """
    per_owner = sorted(
        {
            f.detail["rule"]
            for f in fields.detect_static(SYNTHETIC_GRAMMAR, SYNTHETIC_NODE_TYPES)
            if f.category == "dropped-field"
        }
    )

    assert _set_level_dropped_fields(SYNTHETIC_GRAMMAR, SYNTHETIC_NODE_TYPES) == []
    assert per_owner == ["dropping_expression"]


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
