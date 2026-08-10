from tools.query_coverage.detectors import edges


def census_of(al_parser, source: bytes, path: str = "t.al") -> edges.EdgeCensus:
    tree = al_parser.parse(source)
    c = edges.EdgeCensus()
    c.add(tree, source, path)
    return c


CODEUNIT = b"codeunit 50100 Probe { procedure P() var i: Integer; begin i := 1 + 2; end; }"


def test_a_fielded_child_is_an_edge(al_parser):
    c = census_of(al_parser, CODEUNIT)

    assert ("additive_expression", "left", "integer") in c.counts
    assert ("additive_expression", "right", "integer") in c.counts


def test_an_anonymous_child_inside_a_field_is_an_edge(al_parser):
    """`operator` holds a bare '+' token. It is exactly what a consumer reads
    out of the field, so it must be censused like any other child."""
    c = census_of(al_parser, CODEUNIT)

    assert ("additive_expression", "operator", "+") in c.counts


def test_a_child_with_no_field_is_not_an_edge(al_parser):
    """`code_block`'s begin/end keywords sit in no field, so they contribute no
    edge -- there is no attachment for this detector to be wrong about."""
    c = census_of(al_parser, CODEUNIT)

    assert not any(parent == "code_block" and child == "begin_keyword"
                   for parent, _field, child in c.counts)


def test_instances_are_counted_but_kinds_are_not_duplicated(al_parser):
    source = b"codeunit 50100 P { procedure Q() var i: Integer; begin i := 1 + 2 + 3 + 4; end; }"

    c = census_of(al_parser, source)

    assert c.counts[("additive_expression", "operator", "+")] == 3


def test_one_finding_per_kind_regardless_of_instance_count(al_parser, node_types):
    """The cardinality contract: a fingerprint SET, never per instance."""
    source = b"codeunit 50100 P { procedure Q() var i: Integer; begin i := 1 + 2 + 3 + 4; end; }"
    c = census_of(al_parser, source)

    found = [f for f in edges.detect(c, node_types) if f.category == "edge-kind"]
    operator_edges = [f for f in found if f.fingerprint[1:] == ("additive_expression", "operator", "+")]

    assert len(operator_edges) == 1
    assert operator_edges[0].detail["instances"] == 3


def test_the_fingerprint_carries_no_offset(al_parser, node_types):
    """The same edge kind at two different offsets must cluster as one."""
    near = b"codeunit 50100 P { procedure Q() var i: Integer; begin i := 1 + 2; end; }"
    far = b"// a comment that shifts every byte along\n" + near

    a = edges.detect(census_of(al_parser, near, "a.al"), node_types)
    b = edges.detect(census_of(al_parser, far, "b.al"), node_types)

    keys_a = {f.key() for f in a if f.category == "edge-kind"}
    keys_b = {f.key() for f in b if f.category == "edge-kind"}
    assert keys_a == keys_b


def test_declared_fields_skips_anonymous_types():
    node_types = [
        {"type": "real", "named": True, "fields": {"left": {"required": True, "types": []}}},
        {"type": "+", "named": False},
    ]

    assert list(edges.declared_fields(node_types)) == [("real", "left")]


def test_field_never_populated_fires_when_the_parent_type_is_observed(al_parser):
    c = census_of(al_parser, CODEUNIT)
    fake = [
        {
            "type": "additive_expression",
            "named": True,
            "fields": {"invented": {"required": False, "types": [{"type": "integer", "named": True}]}},
        }
    ]

    found = [f for f in edges.detect(c, fake) if f.category == "field-never-populated"]

    assert [f.detail["field"] for f in found] == ["invented"]
    assert found[0].fingerprint == ("field-never-populated", "additive_expression", "invented")
    assert found[0].detail["required"] is False
    assert found[0].detail["declared_children"] == ["integer"]


def test_field_never_populated_stays_quiet_when_the_parent_type_is_unobserved(al_parser):
    """That case is detector 7's finding. Repeating it here is duplicate noise:
    corpus-wide it would add 33 findings that never-observed already reports."""
    c = census_of(al_parser, CODEUNIT)
    fake = [
        {
            "type": "a_type_no_file_produces",
            "named": True,
            "fields": {"invented": {"required": False, "types": []}},
        }
    ]

    assert edges.detect(c, fake) == [
        f for f in edges.detect(c, fake) if f.category == "edge-kind"
    ]


def test_field_never_populated_stays_quiet_when_the_field_is_populated(al_parser):
    c = census_of(al_parser, CODEUNIT)
    fake = [
        {
            "type": "additive_expression",
            "named": True,
            "fields": {"left": {"required": True, "types": [{"type": "integer", "named": True}]}},
        }
    ]

    assert not [f for f in edges.detect(c, fake) if f.category == "field-never-populated"]


def test_the_real_grammar_produces_the_field_never_populated_signal(al_parser, node_types):
    """Non-vacuity against the SHIPPED node-types.json, not a fake one.

    Without this the whole second category could quietly stop firing -- a check
    that skips every case looks exactly like a check that passed.
    """
    c = census_of(al_parser, CODEUNIT)

    found = [f for f in edges.detect(c, node_types) if f.category == "field-never-populated"]

    assert found, "no declared field went unpopulated for a one-codeunit census"
    assert all(f.path == edges.DECLARATION_PATH for f in found)
    assert all(f.byte_offset == 0 and f.line == 0 for f in found)


def test_as_report_totals_match_the_counts(al_parser):
    c = census_of(al_parser, CODEUNIT)

    report = c.as_report()

    assert report["edge_kinds"] == len(c.counts)
    assert report["edge_total"] == sum(c.counts.values())
    assert report["edges"]["additive_expression|operator|+"] == 1


def test_a_reattachment_that_preserves_every_node_type_still_moves_edges(al_parser):
    """The premise of the whole detector, asserted rather than assumed.

    `1 + 2 * 3` and `(1 + 2) * 3` contain the identical multiset of node types
    apart from the parentheses, and identical byte coverage of the operands --
    yet the field graph differs. A node-type census cannot tell these apart in
    the way this one can.
    """
    flat = census_of(al_parser, b"codeunit 1 P { procedure Q() var i: Integer; begin i := 1 + 2 * 3; end; }")
    grouped = census_of(al_parser, b"codeunit 1 P { procedure Q() var i: Integer; begin i := 1 * 2 + 3; end; }")

    assert flat.node_types == grouped.node_types
    assert flat.counts != grouped.counts
