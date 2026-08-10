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


# The node types that account for a lexical `field(`, if the excluded anchor
# were ever reinstated. Not in anchors.ANCHORS — see EXCLUDED_ANCHORS.
_FIELD_ANCHOR = anchors.Anchor(
    name="field(",
    pattern=anchors._NO_DOT + r"field\s*\(",
    node_types=("field_declaration", "page_field", "field_keyword", "preproc_split_field"),
)


def test_field_anchor_reconciles_outside_preproc_splits(al_parser):
    """The three plain shapes of `field(` each produce exactly one node.

    Declaration, page control, and the where()/link marker. The marker only
    became countable at 5a39bcf, which named it `field_keyword`; before that
    it produced no node at all, and that was the stated reason `field(` is in
    EXCLUDED_ANCHORS. This test is what stops that reason from silently
    reverting to true — a `field_keyword` that stopped being emitted would
    fail here rather than quietly restoring the old excuse.

    Written against a constructed Anchor because `field(` is NOT in
    anchors.ANCHORS: asserting "no findings for field(" through detect()
    passes whether or not the counts reconcile, since detect() only ever
    iterates ANCHORS. That is how the previous version of this test could not
    fail.
    """
    source = (
        b"table 1 T { fields { field(1; N; Code[10]) { } "
        b"field(2; M; Code[10]) { TableRelation = Other.Code where(X = field(N)); } } }"
    )
    tree = al_parser.parse(source)
    assert not tree.root_node.has_error

    lexical = anchor_counts.count_lexical(source.decode("utf-8"), _FIELD_ANCHOR)
    nodes = anchor_counts.count_nodes(tree, _FIELD_ANCHOR)

    assert lexical == 3
    assert lexical == nodes


def test_field_anchor_cannot_reconcile_a_preproc_split_field(al_parser):
    """The live reason `field(` stays excluded, as printed into summary.md.

    A field header split across #if branches spells `field(` once per branch
    and produces ONE preproc_split_field node for all of them. The mismatch is
    (branches - 1), so no node-type sum reconciles it — that is a 1:N mapping,
    not a missing node type. Corpus-wide this is 1 file of 15,358 (measured);
    every other `field(` site is accounted for exactly.
    """
    source = (
        b"page 1 P { layout { area(content) {\n"
        b"#if CLEAN\n"
        b"field(N; Rec.A)\n"
        b"#else\n"
        b"field(N; Rec.B)\n"
        b"#endif\n"
        b"{ }\n"
        b"} } }"
    )
    tree = al_parser.parse(source)
    assert not tree.root_node.has_error
    # Pin the mechanism, not just the arithmetic: one node for both spellings.
    assert (
        anchor_counts.count_nodes(
            tree, anchors.Anchor("x", "x", ("preproc_split_field",))
        )
        == 1
    )

    lexical = anchor_counts.count_lexical(source.decode("utf-8"), _FIELD_ANCHOR)
    nodes = anchor_counts.count_nodes(tree, _FIELD_ANCHOR)

    assert lexical == 2
    assert nodes == 1


def test_excluded_field_anchor_reason_names_the_current_cause(al_parser):
    """EXCLUDED_ANCHORS text is printed verbatim into summary.md, so a stale
    reason is published to every reader. The pre-5a39bcf reason ("a field
    reference inside a where() clause produces no node") is now false.
    """
    reason = anchors.EXCLUDED_ANCHORS["field("]

    assert "preproc_split_field" in reason
    assert "produces no node" not in reason


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
