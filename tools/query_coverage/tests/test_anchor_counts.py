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


# The live `field(` anchor, taken from the table rather than reconstructed, so
# these tests cannot pass against a definition the harness does not use. It was
# EXCLUDED until 4.0.0; see the note at its definition in anchors.py for both
# reasons and why each stopped being true.
#
# Its node_types is `("field_keyword",)` alone. The old value summed
# field_declaration + page_field + field_keyword + preproc_split_field, which
# was right while only the where()/link marker produced a `field_keyword`. The
# losslessness work gives every `field(` site one, so a declaration now yields
# BOTH a field_declaration and a nested field_keyword and the sum double-counts
# — 5 nodes for 3 spellings in the first fixture below, and 6,371 of 15,358
# corpus files. The keyword alone is exact on 15,358 of 15,358.
_FIELD_ANCHOR = next(a for a in anchors.ANCHORS if a.name == "field(")


def test_field_anchor_reconciles_on_the_keyword_alone(al_parser):
    """One `field_keyword` per lexical `field(`, in all three plain shapes:
    declaration, page control, and the where()/link marker.

    The marker only became countable at 5a39bcf, which named it
    `field_keyword`; before that it produced no node and that was the original
    reason `field(` is excluded. This test is what stops that reason from
    silently reverting to true — a `field_keyword` that stopped being emitted
    fails here rather than quietly restoring the old excuse.

    Counted directly rather than through detect(). `field(` is in ANCHORS as of
    4.0.0, so "no findings for field(" would now be a legal way to write this
    -- and a bad one: it was how an earlier version of this test could not
    fail, back when detect() did not iterate this anchor at all and the
    assertion was vacuous. Comparing the two counts fails for a stated reason
    either way.

    The declaration count is asserted separately so the failure distinguishes
    the two directions: `nodes` too high means the node-type list started
    double-counting again, too low means the keyword stopped being emitted.
    """
    source = (
        b"table 1 T { fields { field(1; N; Code[10]) { } "
        b"field(2; M; Code[10]) { TableRelation = Other.Code where(X = field(N)); } } }"
        b"page 2 P { layout { area(content) { field(F; Rec.N) { } } } }"
    )
    tree = al_parser.parse(source)
    assert not tree.root_node.has_error

    lexical = anchor_counts.count_lexical(source.decode("utf-8"), _FIELD_ANCHOR)
    nodes = anchor_counts.count_nodes(tree, _FIELD_ANCHOR)

    assert lexical == 4
    assert nodes == 4
    # All three shapes are really present, asserted rather than assumed. The
    # page control was MISSING from this fixture while the docstring claimed
    # it: the source was a lone `table`, so `page_field` went uncovered and
    # aliasing its keyword away left this test green. Found by mutation, which
    # is the only thing that would have found it.
    for node_type, expected in (
        ("field_declaration", 2),
        ("page_field", 1),
    ):
        assert (
            anchor_counts.count_nodes(tree, anchors.Anchor("x", "x", (node_type,)))
            == expected
        ), node_type


def test_field_anchor_reconciles_across_a_preproc_split(al_parser):
    """The obstruction that justified excluding this anchor is gone.

    A field header split across #if branches spells `field(` once per branch
    and still produces exactly ONE `preproc_split_field` for all of them — the
    1:N mapping is real and is pinned below. But each branch now carries its
    own `field_keyword`, so counting the keyword reconciles anyway: the 1:N
    node is simply not what is being counted.

    This is the successor to `test_field_anchor_cannot_reconcile_a_preproc_
    split_field`, which asserted `nodes == 1` against `lexical == 2` and was
    the encoded form of the exclusion's stated reason. That reason is what this
    test now falsifies, which is why `field(` is no longer excluded --
    see the note at its definition in anchors.py.
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
    # The 1:N mapping still exists — one node for both spellings.
    assert (
        anchor_counts.count_nodes(
            tree, anchors.Anchor("x", "x", ("preproc_split_field",))
        )
        == 1
    )

    lexical = anchor_counts.count_lexical(source.decode("utf-8"), _FIELD_ANCHOR)
    nodes = anchor_counts.count_nodes(tree, _FIELD_ANCHOR)

    assert lexical == 2
    assert nodes == 2


def test_field_anchor_is_checked_and_not_excluded():
    """Successor to test_excluded_field_anchor_reason_names_the_current_cause,
    which asserted that EXCLUDED_ANCHORS["field("] named its CURRENT cause.

    That test was right and the config drifted out from under it: its reason
    was the 1:N preproc_split_field mapping, which the test above now shows
    reconciling, so the repo was publishing a false reason verbatim into
    summary.md. The honest repair was to remove the exclusion, not to write a
    better excuse for it -- so the assertion inverts rather than disappearing.

    The failure mode it was written for is unchanged: config drifting away from
    published prose. Excluding `field(` again, or quietly dropping it from
    ANCHORS instead of excluding it (which would publish nothing at all), turns
    this red.
    """
    assert "field(" not in anchors.EXCLUDED_ANCHORS
    assert _FIELD_ANCHOR in anchors.ANCHORS
    assert _FIELD_ANCHOR.node_types == ("field_keyword",)


def test_every_exclusion_is_published_with_a_reason():
    """EXCLUDED_ANCHORS text is printed verbatim into summary.md, so an entry
    without a real reason publishes nothing useful to every reader.

    Vacuous today -- the dict is empty as of 4.0.0 -- and deliberately kept:
    it is the guard on the next entry anyone adds, and the empty case is
    asserted separately below so "no exclusions" cannot be mistaken for "the
    check stopped running".
    """
    for name, reason in anchors.EXCLUDED_ANCHORS.items():
        assert reason.strip(), f"{name} is excluded with an empty reason"
        assert len(reason) > 40, f"{name}'s reason is too short to be one"


def test_no_anchor_is_currently_excluded():
    """Pins the 4.0.0 state: every anchor in the table is actually checked.

    Separate from the test above because the two fail for opposite reasons --
    that one on a bad new exclusion, this one on any new exclusion at all. A
    reader adding one should have to change this line deliberately.
    """
    assert anchors.EXCLUDED_ANCHORS == {}


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
