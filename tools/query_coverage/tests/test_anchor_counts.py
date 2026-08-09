from tools.query_coverage import anchors
from tools.query_coverage.detectors import anchor_counts


def test_procedure_anchor_is_one_to_one(al_parser):
    source = b"codeunit 1 T { procedure A() begin end; procedure B() begin end; }"

    findings = anchor_counts.detect(al_parser.parse(source), source, "t.al")

    assert [f for f in findings if f.detail["anchor"] == "procedure"] == []


def test_procedure_in_a_comment_is_not_counted(al_parser):
    source = b"codeunit 1 T { // procedure Ghost()\n procedure A() begin end; }"

    findings = anchor_counts.detect(al_parser.parse(source), source, "t.al")

    assert [f for f in findings if f.detail["anchor"] == "procedure"] == []


def test_procedure_in_a_string_is_not_counted(al_parser):
    source = b"codeunit 1 T { procedure A() begin x := 'procedure'; end; }"

    findings = anchor_counts.detect(al_parser.parse(source), source, "t.al")

    assert [f for f in findings if f.detail["anchor"] == "procedure"] == []


def test_dot_prefixed_word_is_not_an_anchor(al_parser):
    source = b"codeunit 1 T { procedure A() begin x.Procedure(); end; }"

    findings = anchor_counts.detect(al_parser.parse(source), source, "t.al")

    assert [f for f in findings if f.detail["anchor"] == "procedure"] == []


def test_field_anchor_covers_declaration_and_reference(al_parser):
    """field( is not only field_declaration; link properties use it too."""
    source = (
        b"table 1 T { fields { field(1; N; Code[10]) { } "
        b"field(2; M; Code[10]) { TableRelation = Other.Code where(X = field(N)); } } }"
    )

    findings = anchor_counts.detect(al_parser.parse(source), source, "t.al")

    assert [f for f in findings if f.detail["anchor"] == "field("] == []


def test_mismatch_is_reported_with_both_counts(al_parser):
    fake = anchors.Anchor(name="procedure", pattern=r"\bprocedure\b", node_types=("nonexistent_node",))
    source = b"codeunit 1 T { procedure A() begin end; }"

    lexical = anchor_counts.count_lexical(source.decode("utf-8"), fake)
    nodes = anchor_counts.count_nodes(al_parser.parse(source), fake)

    assert lexical == 1
    assert nodes == 0


def test_fingerprint_is_anchor_and_path(al_parser, monkeypatch):
    """Force a mismatch so the assertion cannot pass vacuously."""
    impossible = anchors.Anchor(
        name="procedure", pattern=r"procedure", node_types=("nonexistent_node",)
    )
    monkeypatch.setattr(anchors, "ANCHORS", (impossible,))
    source = b"codeunit 1 T { procedure A() begin end; }"

    findings = anchor_counts.detect(al_parser.parse(source), source, "t.al")

    assert len(findings) == 1
    assert findings[0].fingerprint == ("procedure", "t.al")
    assert findings[0].detail["lexical"] == 1
    assert findings[0].detail["nodes"] == 0


def test_every_anchor_names_at_least_one_node_type():
    for anchor in anchors.ANCHORS:
        assert anchor.node_types
