"""Unit tests for detector 1.

A NOTE ON WHY HALF OF THESE USE SYNTHETIC TREES.

These tests were originally written against `:=`, which was a real dropped
token. 37771f1 made it a node, so they were re-pointed at `Record`, `tabledata`
and the `is` operator -- the defects still open at the time. The losslessness
work closed those too, and the corpus now reports ZERO byte gaps across all
15,358 files, so there is no longer any AL source that produces one.

Re-pointing has therefore run out of defects, and that is the end of a pattern
rather than an accident: a detector whose only proof of life is a live grammar
defect has no way to prove it still works once the grammar is clean, which is
exactly when you most need to trust it.

So the tests that need a gap now BUILD one, with a synthetic tree over real
bytes. That is stricter than the source-driven form it replaces -- error
nesting and leaf layout are stated outright instead of being hoped for from the
parser -- and it cannot be invalidated by a future grammar fix. What it no
longer proves is that tree-sitter still produces these shapes from AL source;
that was already only incidentally true, and `_straddles_an_error` below
exists because the 2- and 3-token cases had silently stopped reproducing their
own precondition once before.

The real-parser tests that remain assert the invariant that now holds: named
keywords and operators are nodes, and a clean object has no gaps at all.
"""

from tools.query_coverage.detectors import _tree, gaps


def texts(findings):
    return sorted(f.detail["gap_text"] for f in findings)


class FakeNode:
    """The subset of tree_sitter.Node that detector 1 and _tree actually touch.

    Deliberately minimal: if the detector starts using an attribute this does
    not define, these tests fail with AttributeError rather than passing on a
    stub that quietly returns None.
    """

    def __init__(self, type_, start, end, *children, named=True, error=False):
        self.type = type_
        self.start_byte = start
        self.end_byte = end
        self.children = list(children)
        self.is_named = named
        self.is_error = error
        self.parent = None
        for child in self.children:
            child.parent = self

    @property
    def child_count(self):
        return len(self.children)


class FakeTree:
    def __init__(self, root):
        self.root_node = root


def leaf(type_, start, end, named=False):
    return FakeNode(type_, start, end, named=named)


# A variable declaration whose type keyword is covered by no leaf: the exact
# shape a bare kw() used to produce, built rather than parsed.
#
#   r: Record Customer;
#   0  3    9 10     18      <- "Record" is [3,9) and belongs to no leaf
GAP_SOURCE = b"r: Record Customer;"


def gap_tree(source=GAP_SOURCE, name_type="identifier", name_span=(10, 18)):
    """`r: <no leaf>Record</no leaf> <name>;` — the leaf after the gap is swappable."""
    end = len(source)
    return FakeTree(
        FakeNode(
            "variable_declaration", 0, end,
            leaf("identifier", 0, 1, named=True),
            leaf(":", 1, 2),
            leaf(name_type, name_span[0], name_span[1], named=True),
            leaf(";", end - 1, end),
        )
    )


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


def test_type_keywords_are_no_longer_gaps(al_parser):
    """Ratchet on the losslessness work, and the successor to this test's own
    earlier form -- which asserted `Record` and `Code` WERE gaps, because at the
    time they were bare kw() tokens belonging to no node.

    Both halves are asserted, for the same reason
    test_assignment_operators_are_no_longer_gaps asserts both: "no gap" alone
    would also pass on a detector that had stopped reporting anything, so the
    keywords are additionally required to be present as real nodes carrying
    their own text. Reverting the keyword rules to bare kw() turns this red on
    the second half even if the first half still passes.
    """
    source = b"codeunit 1 T { procedure P() var r: Record Customer; c: Code[20]; begin end; }"
    tree = al_parser.parse(source)

    assert gaps.detect(tree, source, "t.al") == []

    keywords = {
        node.type: node.text.decode("utf-8")
        for node in _tree.walk(tree.root_node)
        if node.type in {"record_keyword", "code_keyword"}
    }
    assert keywords == {"record_keyword": "Record", "code_keyword": "Code"}


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


def test_tabledata_keyword_is_no_longer_a_gap(al_parser):
    """Ratchet. `_tabledata_keyword` was a HIDDEN rule over a bare kw(), which
    is why it survived the first round of keyword naming: a hidden rule
    produces no node, so aliasing the token inside it changed nothing visible.
    It is now `tabledata_keyword`, visible, and shared with `option_member`
    (where it is aliased to $.identifier) so that one terminal keeps one rule.

    Same two halves as above: no gap, AND the keyword is a real node.
    """
    source = b"permissionset 1 P { Permissions = tabledata Foo = rimd; }"
    tree = al_parser.parse(source)

    assert gaps.detect(tree, source, "t.al") == []

    assert [
        node.text.decode("utf-8")
        for node in _tree.walk(tree.root_node)
        if node.type == "tabledata_keyword"
    ] == ["tabledata"]


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


def test_fingerprint_is_normalized_text_plus_enclosing_type():
    """The gap text is lowercased into the fingerprint but kept source-cased in
    the detail.

    The original ':=' example could not see this: it has no letters, so a
    fingerprint that skipped normalize_text entirely passed. The gap text here
    is deliberately mixed-case for the same reason.
    """
    findings = gaps.detect(gap_tree(), GAP_SOURCE, "t.al")

    assert len(findings) == 1
    assert findings[0].detail["gap_text"] == "Record"
    assert findings[0].fingerprint[0] == "record"
    assert len(findings[0].fingerprint) == 2


def test_fingerprint_keys_on_the_node_containing_the_gap_not_the_next_token():
    """F5: the fingerprint's second component must be the construct the gap
    sits inside (here "variable_declaration"), not the type of whichever token
    happens to follow it. Before the fix, the two sources below keyed on
    "identifier" and "quoted_identifier" respectively -- two clusters for one
    grammar defect, and a routine change to which node types can follow the
    gap would silently drop one cluster and open a new one, reading as a false
    regression for a defect that never changed.

    The original pair was `i := 1` / `i := 'x'`, keying on "integer" and
    "string_literal"; 37771f1 made ':=' a real node. The pair after that was
    `Record Customer` / `Record "My Table"`, which the losslessness work then
    closed. The discriminating property was never the specific construct -- it
    is that the leaf FOLLOWING the gap differs while the gap's own container
    does not -- so it is now stated directly instead of being borrowed from
    whichever defect happened to be open.
    """
    bare = GAP_SOURCE
    quoted = b'r: Record "My Table";'

    bare_findings = gaps.detect(gap_tree(), bare, "t.al")
    quoted_findings = gaps.detect(
        gap_tree(quoted, name_type="quoted_identifier", name_span=(10, 20)),
        quoted, "t.al",
    )

    assert [f.detail["gap_text"] for f in bare_findings] == ["Record"]
    assert [f.detail["gap_text"] for f in quoted_findings] == ["Record"]
    assert [f.fingerprint for f in bare_findings] == [("record", "variable_declaration")]
    assert [f.fingerprint for f in quoted_findings] == [("record", "variable_declaration")]


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


def test_offset_measures_leading_whitespace_in_bytes_not_characters(al_parser):
    """The reported offset must advance past the gap's leading whitespace by
    BYTES. `start` is a byte offset, so adding a character index to it -- which
    `start + raw.index(stripped[0])` did -- is short by one byte per multi-byte
    character in that whitespace, and the reported line/column then points into
    the middle of a character. Same class as the byte-vs-character bug 376b8f0
    fixed in pattern_texts().

    Driven through _emit rather than detect() on purpose. tree-sitter's `/\\s/`
    extra is ASCII-only, so the AL grammar lexes a literal NBSP as an ERROR
    leaf, which covers those bytes and then gets subtracted -- no real parse
    produces a segment whose leading whitespace is non-ASCII today. The
    arithmetic is wrong regardless of whether this grammar can reach it, and
    the extras array is one edit away from making it reachable. The tree is
    real so `enclosing` resolves against genuine nodes.
    """
    source = "codeunit 1 T { procedure P() var r:\u00a0Record Customer; begin end; }".encode(
        "utf-8"
    )
    tree = al_parser.parse(source)
    start = source.index(b":") + 1
    end = source.index(b"Customer")
    assert source[start:end].decode("utf-8") == "\u00a0Record "

    findings = []
    gaps._emit(findings, source, "t.al", start, end, tree.root_node, [])

    assert len(findings) == 1
    assert findings[0].detail["gap_text"] == "Record"
    # NBSP is two bytes but one character: pre-fix this was one byte short.
    assert findings[0].byte_offset == source.index(b"Record")
    assert findings[0].line == 1
    assert findings[0].column == source.index(b"Record") + 1


def test_bom_between_leaves_is_not_part_of_the_gap_text(al_parser):
    """U+FEFF is an extra (grammar.js:137), so it is not part of a dropped
    token and must not reach the gap text or the cluster fingerprint.

    The detector already treated a BOM-only segment as ignorable, but
    str.strip() does not strip U+FEFF -- so the old `raw.strip()` produced the
    gap text "\\ufeffRecord", fingerprinted under a key no other site could
    ever share.
    """
    source = "codeunit 1 T { procedure P() var r: \uFEFFRecord Customer; begin end; }".encode(
        "utf-8"
    )
    tree = al_parser.parse(source)
    assert not tree.root_node.has_error  # the BOM really is an extra here

    findings = gaps.detect(tree, source, "t.al")

    assert texts(findings) == ["Record"]
    assert findings[0].byte_offset == source.index(b"Record")
    assert findings[0].fingerprint == ("record", "variable_declaration")


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
