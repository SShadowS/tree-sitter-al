from tools.query_coverage.detectors import _tree, gaps


def texts(findings):
    return sorted(f.detail["gap_text"] for f in findings)


def _uncovered_chunks(tree, source):
    """The raw [start, end) spans gaps.detect() reasons about, before error
    subtraction. Used below to assert a test's own precondition."""
    chunks = []
    cursor = 0
    for leaf in _tree.leaves(tree.root_node):
        if leaf.start_byte > cursor:
            chunks.append((cursor, leaf.start_byte))
        cursor = max(cursor, leaf.end_byte)
    if cursor < len(source):
        chunks.append((cursor, len(source)))
    return chunks


def _straddles_an_error(tree, source):
    """True if some uncovered chunk crosses an error range's edge.

    This is the precondition the 2- and 3-token cases below exist to exercise,
    and it is a property of the SOURCE, not of the detector: only a chunk that
    overlaps a recorded error range while also extending outside it can tell
    gaps._split_by_errors apart from blanket overlap suppression. Asserting it
    stops those two tests from quietly degrading into duplicates of the
    1-token case when a grammar change reshapes error recovery -- which is
    precisely what happened to their original ':=' sources once 37771f1 made
    the assignment operator a real node and the leaf layout around the error
    changed.
    """
    errors = _tree.error_ranges(tree.root_node)
    for start, end in _uncovered_chunks(tree, source):
        for lo, hi in errors:
            if lo < end and start < hi and (start < lo or hi < end):
                return True
    return False


def test_hidden_type_keywords_are_gaps(al_parser):
    """The worked example: a type keyword written as a bare kw() is lexed and
    then belongs to no node, so its bytes are covered by no leaf.

    This replaces the original ':=' example, which 37771f1 fixed (see
    test_assignment_operators_are_no_longer_gaps). Two gaps, asserted as an
    exact list rather than by membership, so a detector that over-reports
    fails here too -- membership alone would pass on a detector that flagged
    every token in the file.
    """
    source = b"codeunit 1 T { procedure P() var r: Record Customer; c: Code[20]; begin end; }"

    findings = gaps.detect(al_parser.parse(source), source, "t.al")

    assert texts(findings) == ["Code", "Record"]  # texts() sorts


def test_assignment_operators_are_no_longer_gaps(al_parser):
    """Ratchet on 37771f1, which was the defect this detector was built to find.

    `_assignment_operator` was a hidden rule over a single token, so ':=' and
    '+=' belonged to no node at all and `i := 1` / `i += 2` produced
    byte-identical trees. Renaming the rule to `assignment_operator` made it
    visible.

    Both halves are asserted. "No gap" alone would also pass on a detector
    that had stopped reporting anything, so the operators are additionally
    required to be present in the tree as real nodes carrying their own text
    -- which is what a revert of 37771f1 would remove.
    """
    source = b"codeunit 1 T { procedure P() var i: Integer; begin i := 1; i += 2; end; }"
    tree = al_parser.parse(source)

    assert gaps.detect(tree, source, "t.al") == []

    operators = [
        node.text.decode("utf-8")
        for node in _tree.walk(tree.root_node)
        if node.type == "assignment_operator"
    ]
    assert operators == [":=", "+="]


def test_tabledata_keyword_is_a_gap(al_parser):
    """_tabledata_keyword is a bare kw() used un-aliased."""
    source = b"permissionset 1 P { Permissions = tabledata Foo = rimd; }"

    findings = gaps.detect(al_parser.parse(source), source, "t.al")

    assert "tabledata" in texts(findings)


def test_clean_object_with_no_hidden_tokens_has_no_gaps(al_parser):
    source = b"codeunit 1 T { }"

    assert gaps.detect(al_parser.parse(source), source, "t.al") == []


def test_bom_is_not_a_gap(al_parser):
    """U+FEFF is an extra (grammar.js:137) but str.isspace() is False for it."""
    source = "\uFEFFcodeunit 1 T { }".encode("utf-8")

    assert gaps.detect(al_parser.parse(source), source, "t.al") == []


def test_comments_are_not_gaps(al_parser):
    source = b"codeunit 1 T { // a comment\n /* another */ }"

    assert gaps.detect(al_parser.parse(source), source, "t.al") == []


def test_gaps_inside_error_ranges_are_excluded(al_parser):
    """Error-recovery artifacts belong to detector 2."""
    source = b"codeunit 1 T { @@@ !!! }"
    tree = al_parser.parse(source)
    assert tree.root_node.has_error

    for finding in gaps.detect(tree, source, "t.al"):
        assert "@" not in finding.detail["gap_text"]
        assert "!" not in finding.detail["gap_text"]


def test_fingerprint_is_normalized_text_plus_enclosing_type(al_parser):
    """The gap text is lowercased into the fingerprint.

    The original ':=' example could not see that: it has no letters, so a
    fingerprint that skipped normalize_text entirely passed. 'Record' is
    source-cased, so this now fails against that mistake.
    """
    source = b"codeunit 1 T { procedure P() var r: Record Customer; begin end; }"

    findings = gaps.detect(al_parser.parse(source), source, "t.al")

    assert findings
    assert findings[0].detail["gap_text"] == "Record"
    assert findings[0].fingerprint[0] == "record"
    assert len(findings[0].fingerprint) == 2


def test_fingerprint_keys_on_the_node_containing_the_gap_not_the_next_token(al_parser):
    """F5: the fingerprint's second component must be the construct the gap
    sits inside (here "variable_declaration"), not the type of whichever token
    happens to follow it. Before the fix, the two sources below keyed on
    "identifier" and "quoted_identifier" respectively -- two clusters for one
    grammar defect, and a routine change to which node types can follow the
    gap would silently drop one cluster and open a new one, reading as a false
    regression for a defect that never changed.

    The original pair was `i := 1` / `i := 'x'`, keying on "integer" and
    "string_literal"; 37771f1 made ':=' a real node, so it is no longer a gap
    and no longer discriminates. The `Record` gap does: its following leaf is
    an `identifier` in one source and a `quoted_identifier` in the other,
    which is the same two-clusters-for-one-defect shape.
    """
    bare_name = b"codeunit 1 T { procedure P() var r: Record Customer; begin end; }"
    quoted_name = b'codeunit 1 T { procedure P() var r: Record "My Table"; begin end; }'

    bare_findings = gaps.detect(al_parser.parse(bare_name), bare_name, "t.al")
    quoted_findings = gaps.detect(al_parser.parse(quoted_name), quoted_name, "t.al")

    assert [f.fingerprint for f in bare_findings if f.detail["gap_text"] == "Record"] == [
        ("record", "variable_declaration")
    ]
    assert [f.fingerprint for f in quoted_findings if f.detail["gap_text"] == "Record"] == [
        ("record", "variable_declaration")
    ]


def test_semicolon_counts_as_coverage(al_parser):
    """Anonymous string tokens are visible leaves; walking named children breaks this."""
    source = b"codeunit 1 T { var i: Integer; }"

    for finding in gaps.detect(al_parser.parse(source), source, "t.al"):
        assert finding.detail["gap_text"] != ";"


def _assert_only_the_dropped_is(findings):
    assert "is" in texts(findings)
    for finding in findings:
        assert "@" not in finding.detail["gap_text"]
        assert "!" not in finding.detail["gap_text"]


def test_dropped_token_survives_1_token_error_region(al_parser):
    """A dropped 'is' immediately before a single-token ERROR must still be
    reported -- it sits wholly outside the recorded error range.

    The dropped token used to be ':='; 37771f1 made that a real node, so the
    is_expression operator (still a gap, still in the qc baseline as
    gaps|is|is_expression) stands in for it here and in the two cases below.
    """
    source = b"codeunit 1 T { procedure P() begin x := i is @@@ end; }"
    tree = al_parser.parse(source)
    assert tree.root_node.has_error

    _assert_only_the_dropped_is(gaps.detect(tree, source, "t.al"))


def test_dropped_token_survives_2_token_error_region(al_parser):
    """Regression for the reviewed bug: tree-sitter nests one ERROR inside
    another here, so _tree.leaves() never yields the outer ERROR itself --
    only its inner leaf. The uncovered chunk between the last clean leaf and
    that inner leaf runs straight through the dropped 'is' and into the
    error's own un-leafed lead-in, so the chunk overlaps the recorded error
    range even though 'is' itself sits outside it. Blanket overlap
    suppression discarded 'is' along with the error text; interval
    subtraction (gaps._split_by_errors) must keep it.

    The two garbage tokens are deliberately DIFFERENT ('@@@ !!!'). The
    original source used ':= @@@ @@@' and the identical-token pair reproduced
    the nesting then; after 37771f1 it no longer does -- '@@@ @@@' now yields
    a first leaf flush with the error's start, which blanket suppression
    would also survive. _straddles_an_error asserts the shape rather than
    trusting it.
    """
    source = b"codeunit 1 T { procedure P() begin x := i is @@@ !!! end; }"
    tree = al_parser.parse(source)
    assert tree.root_node.has_error
    assert _straddles_an_error(tree, source)

    _assert_only_the_dropped_is(gaps.detect(tree, source, "t.al"))


def test_dropped_token_survives_3_token_error_region(al_parser):
    source = b"codeunit 1 T { procedure P() begin x := i is @@@ @@@ !!! end; }"
    tree = al_parser.parse(source)
    assert tree.root_node.has_error
    assert _straddles_an_error(tree, source)

    _assert_only_the_dropped_is(gaps.detect(tree, source, "t.al"))


def test_snippet_flattens_embedded_newlines(al_parser):
    """_snippet must escape a real newline to the literal 2-character
    sequence backslash-n for display; a no-op .replace("\\n", "\\n") defeats
    this and is silently invisible in every other test."""
    source = b"codeunit 1 T {\n  procedure P() var r: Record Customer;\n  begin end;\n}"

    findings = gaps.detect(al_parser.parse(source), source, "t.al")

    assert findings
    snippet = findings[0].snippet
    assert "\n" not in snippet
    assert "\\n" in snippet
