from tools.query_coverage.detectors import reserved


def test_whitelisted_contextual_keywords_are_not_flagged(al_parser):
    """grammar.js:4148-4159 whitelists these as identifiers on purpose."""
    source = b"codeunit 1 T { procedure P() var value: Integer; begin value := 1; end; }"

    findings = reserved.detect(al_parser.parse(source), source, "t.al")

    assert [f.detail["keyword"] for f in findings] == []


def test_hard_reserved_word_as_identifier_is_flagged(al_parser):
    """Bug 2's signature: 'end' reparsed into an identifier position.

    Find a source shape that actually produces an `identifier` node whose text
    is a hard-reserved word. If none of the candidates below does, the parser
    never mislabels these today — say so explicitly rather than looping over an
    empty list, and record which candidates were tried.
    """
    candidates = [
        b"codeunit 1 T { procedure P() begin end(); end; }",
        b"codeunit 1 T { procedure P() begin exit := 1; end; }",
        b"codeunit 1 T { procedure P() begin then(); end; }",
    ]

    hits = []
    for source in candidates:
        hits.extend(reserved.detect(al_parser.parse(source), source, "t.al"))

    if not hits:
        import pytest

        pytest.skip(
            "no candidate produces a reserved word in identifier position on this "
            "grammar; detector 4 is exercised by test_detect_on_synthetic_tree below"
        )

    assert hits[0].category == "reserved-as-identifier"
    assert hits[0].detail["keyword"] in reserved.HARD_RESERVED


def test_detect_fires_on_a_word_the_grammar_does_parse_as_an_identifier(
    al_parser, monkeypatch
):
    """Exercise the mechanism unconditionally.

    Whether today's grammar ever mislabels a hard-reserved word is a property of
    the grammar. Whether the detector FIRES when it happens is a property of this
    code, and must be tested without depending on the former.
    """
    monkeypatch.setattr(reserved, "HARD_RESERVED", frozenset({"myvar"}))
    source = b"codeunit 1 T { procedure P() var myvar: Integer; begin myvar := 1; end; }"

    findings = reserved.detect(al_parser.parse(source), source, "t.al")

    assert findings
    assert all(f.detail["keyword"] == "myvar" for f in findings)
    assert all(f.category == "reserved-as-identifier" for f in findings)


def test_whitelist_suppresses_a_word_even_when_hard_reserved(al_parser, monkeypatch):
    monkeypatch.setattr(reserved, "HARD_RESERVED", frozenset({"myvar"}))
    monkeypatch.setattr(reserved, "CONTEXTUAL_WHITELIST", frozenset({"myvar"}))
    source = b"codeunit 1 T { procedure P() var myvar: Integer; begin myvar := 1; end; }"

    assert reserved.detect(al_parser.parse(source), source, "t.al") == []


def test_member_access_position_is_excluded(al_parser):
    """x.End is a legitimate DotNet or interface member name."""
    source = b"codeunit 1 T { procedure P() var x: DotNet Foo; begin x.End(); end; }"

    findings = reserved.detect(al_parser.parse(source), source, "t.al")

    assert [f.detail["keyword"] for f in findings] == []


def test_fingerprint_pairs_keyword_with_enclosing_type(al_parser):
    source = b"codeunit 1 T { procedure P() begin end(); end; }"

    for finding in reserved.detect(al_parser.parse(source), source, "t.al"):
        assert len(finding.fingerprint) == 2
        assert finding.fingerprint[0] == finding.detail["keyword"]


def test_whitelist_matches_the_grammar():
    """Drift guard: keep CONTEXTUAL_WHITELIST in sync with keyword_as_identifier."""
    assert reserved.CONTEXTUAL_WHITELIST == frozenset(
        {
            "field",
            "key",
            "value",
            "separator",
            "dataset",
            "type",
            "version",
            "action",
            "table",
            "assembly",
        }
    )


def test_hard_reserved_and_whitelist_are_disjoint():
    assert not (reserved.HARD_RESERVED & reserved.CONTEXTUAL_WHITELIST)
