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
        {"record": "provenance", "manifest_hash": "deadbeef", "scope": "manifest"},
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


def _write_findings(reports_dir: Path, header_extra: dict, records: list[dict]) -> None:
    header = {"record": "provenance", "manifest_hash": "deadbeef", **header_extra}
    lines = [header, *records]
    (reports_dir / "findings.jsonl").write_text(
        "\n".join(json.dumps(r) for r in lines) + "\n", encoding="utf-8"
    )


def test_accept_succeeds_on_manifest_scope_report(tmp_path: Path):
    reports_dir = tmp_path / "tools" / "query_coverage" / "reports"
    reports_dir.mkdir(parents=True)
    _write_findings(
        reports_dir,
        {"scope": "manifest"},
        [{"cluster": "gaps|x|y", "detector": "gaps"}],
    )
    baseline_path = tmp_path / "baseline.json"

    code = qc.main(["accept", "--repo-root", str(tmp_path), "--baseline", str(baseline_path)])

    assert code == baseline.EXIT_OK
    saved = baseline.load(baseline_path)
    assert saved is not None
    assert saved.counts == {"gaps|x|y": 1}


def test_accept_refuses_full_corpus_scope_report(tmp_path: Path):
    """A full-corpus findings.jsonl must never be baselined under the
    manifest's hash: its counts are ~260x larger for reasons that have
    nothing to do with regressions (15,358 files vs. 59), and baselining
    them would make the next manifest-scope `run` read the difference as a
    flood of newly "fixed" clusters. Refusal must also leave baseline.json
    completely untouched, not just fail loudly -- a partial or corrupted
    write would be worse than doing nothing.
    """
    reports_dir = tmp_path / "tools" / "query_coverage" / "reports"
    reports_dir.mkdir(parents=True)
    _write_findings(
        reports_dir,
        {"scope": "full-corpus"},
        [{"cluster": "gaps|x|y", "detector": "gaps"}],
    )
    baseline_path = tmp_path / "baseline.json"
    original = '{\n  "manifest_hash": "untouched",\n  "counts": {}\n}\n'
    baseline_path.write_text(original, encoding="utf-8", newline="\n")

    code = qc.main(["accept", "--repo-root", str(tmp_path), "--baseline", str(baseline_path)])

    assert code == baseline.EXIT_CORPUS_BROKEN
    assert baseline_path.read_text(encoding="utf-8") == original


def test_accept_refuses_report_missing_scope_key(tmp_path: Path):
    """A findings.jsonl written before scope tracking existed has no 'scope'
    key at all. Treating that as manifest by default would silently accept
    exactly the contaminated-baseline scenario this whole check exists to
    catch (an old full-corpus report has the same missing key), so a missing
    scope is refused rather than assumed benign -- same exit code and the
    same "leave baseline.json alone" guarantee as an explicit non-manifest
    scope.
    """
    reports_dir = tmp_path / "tools" / "query_coverage" / "reports"
    reports_dir.mkdir(parents=True)
    _write_findings(reports_dir, {}, [{"cluster": "gaps|x|y", "detector": "gaps"}])
    baseline_path = tmp_path / "baseline.json"
    original = '{\n  "manifest_hash": "untouched",\n  "counts": {}\n}\n'
    baseline_path.write_text(original, encoding="utf-8", newline="\n")

    code = qc.main(["accept", "--repo-root", str(tmp_path), "--baseline", str(baseline_path)])

    assert code == baseline.EXIT_CORPUS_BROKEN
    assert baseline_path.read_text(encoding="utf-8") == original


def test_accept_run_roundtrip_stays_silent_for_manifest_scope(tmp_path: Path):
    """The accept -> run round trip must be silent: baselining a manifest
    report's gating clusters, then re-observing the same clusters (with the
    informational detector's cluster filtered out before diffing, exactly as
    cmd_run does), must produce a completely empty Diff. This is the
    mechanism-level proof behind the real end-to-end check (select -> run
    --all -> accept -> run prints nothing new); it does not spin up the real
    parser/corpus, since baseline.diff() is what actually decides silence.
    """
    reports_dir = tmp_path / "tools" / "query_coverage" / "reports"
    reports_dir.mkdir(parents=True)
    _write_findings(
        reports_dir,
        {"scope": "manifest"},
        [
            {"cluster": "gaps|x|y", "detector": "gaps"},
            {"cluster": "shipped_queries|uncaptured|=", "detector": "shipped_queries"},
        ],
    )
    baseline_path = tmp_path / "baseline.json"

    code = qc.main(["accept", "--repo-root", str(tmp_path), "--baseline", str(baseline_path)])
    assert code == baseline.EXIT_OK

    saved = baseline.load(baseline_path)
    assert saved is not None

    # What the next `run` would re-observe: the same gating cluster, with the
    # informational one already filtered out of `gating_clusters` before it
    # ever reaches diff() -- mirroring qc.cmd_run exactly.
    observed = [cl("gaps|x|y", 1)]
    diff = baseline.diff(saved, observed)

    assert diff == baseline.Diff()
