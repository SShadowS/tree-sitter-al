from tools.query_coverage.detectors import gaps


def texts(findings):
    return sorted(f.detail["gap_text"] for f in findings)


def test_assignment_operator_is_a_gap(al_parser):
    """The worked example: field('operator', ...) wraps a hidden token."""
    source = b"codeunit 1 T { procedure P() var i: Integer; begin i := 1; i += 2; end; }"

    findings = gaps.detect(al_parser.parse(source), source, "t.al")

    assert texts(findings) == ["+=", ":="]  # texts() sorts


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
    source = b"codeunit 1 T { procedure P() begin i := 1; end; }"

    findings = gaps.detect(al_parser.parse(source), source, "t.al")

    assert findings
    assert findings[0].fingerprint[0] == ":="
    assert len(findings[0].fingerprint) == 2


def test_semicolon_counts_as_coverage(al_parser):
    """Anonymous string tokens are visible leaves; walking named children breaks this."""
    source = b"codeunit 1 T { var i: Integer; }"

    for finding in gaps.detect(al_parser.parse(source), source, "t.al"):
        assert finding.detail["gap_text"] != ";"
