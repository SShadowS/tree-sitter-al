import json
from pathlib import Path

from tools.query_coverage import model


def make_finding(detector="gaps", parts=("record", "variable_declaration"), offset=0):
    return model.Finding(
        detector=detector,
        category="byte-gap",
        fingerprint=parts,
        path="a/b.al",
        byte_offset=offset,
        line=1,
        column=1,
        enclosing="variable_declaration",
        snippet="x: Record Foo;",
        detail={},
    )


def test_normalize_text_collapses_whitespace_and_lowercases():
    assert model.normalize_text("else\r\n            IF") == "else if"


def test_normalize_text_strips_edges():
    assert model.normalize_text("  Tabledata  ") == "tabledata"


def test_fingerprint_key_is_stable_and_detector_scoped():
    assert model.fingerprint_key("gaps", ("record", "x")) == "gaps|record|x"


def test_cluster_counts_and_caps_examples():
    findings = [make_finding(offset=i) for i in range(10)]

    clusters = model.cluster(findings, max_examples=3)

    assert len(clusters) == 1
    assert clusters[0].count == 10
    assert len(clusters[0].examples) == 3


def test_cluster_sorted_by_count_desc_then_key_asc():
    many = [make_finding(parts=("zzz",), offset=i) for i in range(5)]
    few_b = [make_finding(parts=("bbb",), offset=100)]
    few_a = [make_finding(parts=("aaa",), offset=200)]

    clusters = model.cluster(many + few_b + few_a)

    assert [c.key for c in clusters] == ["gaps|zzz", "gaps|aaa", "gaps|bbb"]


def test_clusters_never_key_on_byte_offset():
    a = make_finding(offset=17)
    b = make_finding(offset=9999)

    clusters = model.cluster([a, b])

    assert len(clusters) == 1


def test_write_jsonl_emits_provenance_header_first(tmp_path: Path):
    out = tmp_path / "findings.jsonl"
    prov = model.Provenance(
        build_stamp="abc",
        manifest_hash="def",
        tree_sitter_version="0.25.2",
        harness_version="1",
    )

    model.write_jsonl(out, prov, [make_finding()])

    lines = out.read_text(encoding="utf-8").splitlines()
    header = json.loads(lines[0])
    assert header["record"] == "provenance"
    assert header["build_stamp"] == "abc"
    assert header["manifest_hash"] == "def"
    assert json.loads(lines[1])["detector"] == "gaps"


def test_write_jsonl_is_stably_sorted(tmp_path: Path):
    out = tmp_path / "findings.jsonl"
    prov = model.Provenance("s", "m", "0.25.2", "1")
    unsorted = [make_finding(offset=50), make_finding(offset=10)]

    model.write_jsonl(out, prov, unsorted)

    offsets = [
        json.loads(line)["byte_offset"]
        for line in out.read_text(encoding="utf-8").splitlines()[1:]
    ]
    assert offsets == [10, 50]
