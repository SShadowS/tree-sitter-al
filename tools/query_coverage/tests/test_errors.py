from tools.query_coverage.detectors import errors


def test_clean_source_has_no_findings(al_parser):
    source = b"codeunit 1 T { }"

    assert errors.detect(al_parser.parse(source), source, "t.al") == []


def test_error_node_is_reported(al_parser):
    source = b"codeunit 1 T { @@@ }"
    tree = al_parser.parse(source)
    assert tree.root_node.has_error

    findings = errors.detect(tree, source, "t.al")

    assert findings
    assert findings[0].category == "error-node"
    assert findings[0].fingerprint[1] == "ERROR"


def test_finding_carries_three_lines_of_context(al_parser):
    source = b"codeunit 1 T {\n  line2\n  @@@\n  line4\n  line5\n}"
    tree = al_parser.parse(source)

    findings = errors.detect(tree, source, "t.al")

    assert findings
    assert findings[0].snippet.count("\n") <= 4


def test_fingerprint_pairs_enclosing_construct_with_symbol(al_parser):
    source = b"codeunit 1 T { @@@ }"

    findings = errors.detect(al_parser.parse(source), source, "t.al")

    assert len(findings[0].fingerprint) == 2
    assert findings[0].fingerprint[1] in {"ERROR", "MISSING"}
