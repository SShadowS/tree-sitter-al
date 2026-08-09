import json
from pathlib import Path

import pytest

from tools.query_coverage import loader
from tools.query_coverage.detectors import shipped_queries


@pytest.fixture(scope="module")
def node_types():
    return json.loads((loader.REPO_ROOT / "src" / "node-types.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def highlights_path():
    return loader.REPO_ROOT / "queries" / "highlights.scm"


def test_assignment_operator_pattern_is_not_dead(al_language, al_parser, highlights_path):
    """Regression guard on the spec: ':=' @operator still matches via for_statement.

    A 'zero matches corpus-wide' check therefore cannot find that bug. Detectors
    1 and 3 find it instead.
    """
    source = b"codeunit 1 T { procedure P() begin for i := 1 to 5 do x := i; end; }"
    tree = al_parser.parse(source)

    usages = shipped_queries.tally(al_language, highlights_path, [(tree, source)])
    by_text = {u.text: u for u in usages if '":="' in u.text}

    assert by_text
    assert any(u.matches > 0 for u in by_text.values())


def test_dead_pattern_is_reported(al_language, al_parser, tmp_path: Path):
    query_file = tmp_path / "probe.scm"
    query_file.write_text('(codeunit_keyword) @a\n(xmlport_keyword) @b\n', encoding="utf-8", newline="\n")
    source = b"codeunit 1 T { }"

    usages = shipped_queries.tally(al_language, query_file, [(al_parser.parse(source), source)])
    findings = shipped_queries.detect_dead(usages)

    assert len(findings) == 1
    assert "xmlport_keyword" in findings[0].detail["pattern_text"]


def test_dead_pattern_fingerprint_uses_text_hash_not_index(al_language, al_parser, tmp_path: Path):
    query_file = tmp_path / "probe.scm"
    query_file.write_text('(xmlport_keyword) @b\n', encoding="utf-8", newline="\n")
    source = b"codeunit 1 T { }"

    findings = shipped_queries.detect_dead(
        shipped_queries.tally(al_language, query_file, [(al_parser.parse(source), source)])
    )

    assert findings
    assert len(findings[0].fingerprint) == 2
    assert len(findings[0].fingerprint[1]) == 64  # sha256 hex


def test_operator_tokens_excludes_structural_delimiters(node_types):
    tokens = set(shipped_queries.operator_tokens(node_types))

    assert ";" not in tokens
    assert "(" not in tokens
    assert ":=" in tokens or "+" in tokens


def test_keyword_coverage_flags_an_uncaptured_keyword(al_language, al_parser, node_types, tmp_path: Path):
    sparse = tmp_path / "sparse.scm"
    sparse.write_text("(codeunit_keyword) @keyword\n", encoding="utf-8", newline="\n")
    source = b"table 1 T { }"

    findings = shipped_queries.detect_keyword_coverage(
        al_language, sparse, node_types, al_parser.parse(source), source, "t.al"
    )

    assert any(f.detail.get("node_type") == "table_keyword" for f in findings)
