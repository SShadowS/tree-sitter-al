import json
from pathlib import Path

from tools.query_coverage import baseline, model, qc


def cl(key: str, count: int) -> model.Cluster:
    return model.Cluster(detector=key.split("|")[0], key=key, count=count, examples=())


def test_summary_lists_clusters_most_frequent_first(tmp_path: Path):
    out = tmp_path / "summary.md"
    clusters = [cl("gaps|a", 2), cl("gaps|b", 10)]
    diff = baseline.Diff()

    qc.write_summary(out, clusters, diff, never_seen=[])

    body = out.read_text(encoding="utf-8")
    assert body.index("gaps|b") < body.index("gaps|a")


def test_summary_reports_new_and_fixed(tmp_path: Path):
    out = tmp_path / "summary.md"
    diff = baseline.Diff(new=[cl("gaps|new", 1)], fixed=["gaps|old"])

    qc.write_summary(out, [cl("gaps|new", 1)], diff, never_seen=[])

    body = out.read_text(encoding="utf-8")
    assert "gaps|new" in body
    assert "gaps|old" in body


def test_summary_reports_never_observed_types(tmp_path: Path):
    out = tmp_path / "summary.md"

    qc.write_summary(out, [], baseline.Diff(), never_seen=["ghost_node"])

    assert "ghost_node" in out.read_text(encoding="utf-8")


def test_run_exits_corpus_broken_when_manifest_drifted(tmp_path: Path, monkeypatch):
    manifest = tmp_path / "manifest.tsv"
    manifest.write_text(
        "# object_types\tpath\tsha256\tbytes\treason\nt\tnope.al\t" + "aa" * 32 + "\t1\tr\n",
        encoding="utf-8",
        newline="\n",
    )

    code = qc.main(["run", "--repo-root", str(tmp_path), "--manifest", str(manifest)])

    assert code == baseline.EXIT_CORPUS_BROKEN


def test_all_flag_exits_zero_even_with_findings(tmp_path: Path):
    """--all is a reporting mode, not a gate."""
    assert qc.exit_for(baseline.Diff(new=[cl("gaps|x", 1)]), report_all=True) == baseline.EXIT_OK
    assert qc.exit_for(baseline.Diff(new=[cl("gaps|x", 1)]), report_all=False) == baseline.EXIT_REGRESSION


def test_accept_excludes_informational_detector_clusters(tmp_path: Path):
    """cmd_run filters INFORMATIONAL_DETECTORS out of gating_clusters before
    diffing. cmd_accept must mirror that filter when it bakes findings.jsonl
    into baseline.json, or the accepted baseline carries counts that `run`
    can never re-observe (having already excluded them) -- every later run
    would then see those clusters as freshly "fixed" and ratchet them to
    zero, over and over, instead of the final run being silent.
    """
    reports_dir = tmp_path / "tools" / "query_coverage" / "reports"
    reports_dir.mkdir(parents=True)
    records = [
        {"record": "provenance", "manifest_hash": "deadbeef"},
        {"cluster": "gaps|x|y", "detector": "gaps"},
        {"cluster": "shipped_queries|uncaptured|=", "detector": "shipped_queries"},
    ]
    (reports_dir / "findings.jsonl").write_text(
        "\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8"
    )
    baseline_path = tmp_path / "baseline.json"

    code = qc.main(["accept", "--repo-root", str(tmp_path), "--baseline", str(baseline_path)])

    assert code == baseline.EXIT_OK
    saved = baseline.load(baseline_path)
    assert saved is not None
    assert saved.counts.get("gaps|x|y") == 1
    assert "shipped_queries|uncaptured|=" not in saved.counts
