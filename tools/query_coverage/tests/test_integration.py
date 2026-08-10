"""The integration itself must be verifiable, not asserted in prose."""

import json
import subprocess
import sys
from pathlib import Path

from tools.query_coverage import baseline, loader


def test_validate_grammar_invokes_the_harness():
    script = (loader.REPO_ROOT / "validate-grammar.sh").read_text(encoding="utf-8")

    assert "tools.query_coverage.qc run" in script
    assert "tools/query_coverage/baseline.json" in script


def test_readme_documents_every_subcommand():
    readme = (loader.REPO_ROOT / "tools" / "query_coverage" / "README.md").read_text(
        encoding="utf-8"
    )

    for command in ("qc select", "qc run", "qc accept", "--full-query-scan"):
        assert command in readme


def test_run_all_exits_zero_and_writes_both_reports():
    result = subprocess.run(
        [sys.executable, "-m", "tools.query_coverage.qc", "run", "--all"],
        cwd=loader.REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == baseline.EXIT_OK, result.stderr
    reports = loader.REPO_ROOT / "tools" / "query_coverage" / "reports"
    assert (reports / "findings.jsonl").is_file()
    assert (reports / "summary.md").is_file()


def test_a_seeded_regression_makes_run_exit_one(tmp_path: Path):
    """Prove the gate is non-vacuous: remove a cluster from the baseline and
    the observed count becomes a NEW cluster, which must fail."""
    real = baseline.load(loader.REPO_ROOT / "tools" / "query_coverage" / "baseline.json")
    assert real is not None and real.counts, "run `qc accept` before this test"

    dropped = dict(real.counts)
    victim = sorted(dropped)[0]
    del dropped[victim]

    seeded = tmp_path / "seeded-baseline.json"
    baseline.save(seeded, baseline.Baseline(manifest_hash=real.manifest_hash, counts=dropped))

    # --baseline is a per-subcommand option (see qc.py's _add_common_args
    # docstring), so it must follow `run`, not precede it.
    result = subprocess.run(
        [sys.executable, "-m", "tools.query_coverage.qc", "run", "--baseline", str(seeded)],
        cwd=loader.REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == baseline.EXIT_REGRESSION
    assert victim in result.stdout
