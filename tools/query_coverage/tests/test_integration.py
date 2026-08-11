"""The integration itself must be verifiable, not asserted in prose."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.query_coverage import baseline, loader

# The three tests below run `qc run`, which needs BC.History. That corpus is
# gitignored and absent on CI runners, where `qc run` exits 2 ("corpus broken:
# a manifest file is missing") — so the tests failed for a reason that has
# nothing to do with what they assert, and the job had been red on `main`
# without anyone acting on it.
#
# Skipped rather than made to pass: a corpus-dependent test without a corpus
# CANNOT RUN, and that is neither a pass nor a failure. pytest counts and
# prints skips separately, so the absence stays visible instead of being
# folded into the pass count — the same rule tools/gate_selftest.py applies to
# its own step5c case.
needs_corpus = pytest.mark.skipif(
    not (loader.REPO_ROOT / "BC.History").is_dir(),
    reason="needs the BC.History corpus; gitignored and absent in CI",
)


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


@needs_corpus
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


@needs_corpus
def test_a_seeded_regression_makes_run_exit_one(tmp_path: Path):
    """Prove the gate is non-vacuous: remove a cluster from the baseline and
    the observed count becomes a NEW cluster, which must fail."""
    real = baseline.load(loader.REPO_ROOT / "tools" / "query_coverage" / "baseline.json")
    assert real is not None and real.counts, "run `qc accept` before this test"

    dropped = dict(real.counts)
    # The victim MUST have a non-zero count. A cluster the grammar has since
    # fixed sits in the baseline at 0 until the next `accept`, and dropping a
    # zero-count cluster seeds nothing -- the detector no longer emits it, so
    # no NEW cluster appears and `run` exits 0. This test then passes its own
    # setup and asserts nothing, which is the exact failure it exists to catch.
    #
    # It happened: after 4.0.0 removed `access_keyword`, that ratcheted-to-0
    # cluster sorted FIRST alphabetically and this test went vacuous by
    # ordering alone.
    victim = next((k for k in sorted(dropped) if dropped[k] > 0), None)
    assert victim is not None, "baseline has no non-zero cluster to seed against"
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


@needs_corpus
def test_a_seeded_never_observed_regression_makes_run_exit_one(tmp_path: Path):
    """F3-specific non-vacuity proof: a named node type moving observed ->
    unobserved (e.g. a keyword rule losing its `alias()`, dropping the node
    type every `(x_keyword)` query matches on, while every byte stays
    covered) must fail the gate through the SAME mechanism as any other
    detector's regression -- not just appear in a gitignored report nobody
    diffs. Removing a `corpus|never-observed|*` cluster from a copy of the
    real baseline simulates exactly that: the type is unobserved either way,
    but the accepted baseline no longer expects it, so it reads as newly
    unobserved.
    """
    real = baseline.load(loader.REPO_ROOT / "tools" / "query_coverage" / "baseline.json")
    assert real is not None and real.counts, "run `qc accept` before this test"

    dropped = dict(real.counts)
    # Non-zero for the same reason as the test above: a ratcheted-to-0 cluster
    # seeds nothing, and this test would then pass while asserting nothing.
    victim = next(
        (k for k in sorted(dropped)
         if k.startswith("corpus|never-observed|") and dropped[k] > 0),
        None,
    )
    assert victim is not None, "baseline has no non-zero corpus|never-observed|* cluster"
    del dropped[victim]

    seeded = tmp_path / "seeded-baseline.json"
    baseline.save(seeded, baseline.Baseline(manifest_hash=real.manifest_hash, counts=dropped))

    result = subprocess.run(
        [sys.executable, "-m", "tools.query_coverage.qc", "run", "--baseline", str(seeded)],
        cwd=loader.REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == baseline.EXIT_REGRESSION
    assert victim in result.stdout
