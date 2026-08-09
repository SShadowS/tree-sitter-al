import json
from pathlib import Path

from tools.query_coverage import baseline, model


def cl(key: str, count: int) -> model.Cluster:
    return model.Cluster(detector=key.split("|")[0], key=key, count=count, examples=())


def test_new_cluster_is_a_regression():
    base = baseline.Baseline(manifest_hash="m", counts={})

    diff = baseline.diff(base, [cl("gaps|record", 5)])

    assert [c.key for c in diff.new] == ["gaps|record"]
    assert baseline.exit_code(diff) == baseline.EXIT_REGRESSION


def test_count_growth_is_a_regression():
    base = baseline.Baseline(manifest_hash="m", counts={"gaps|record": 5})

    diff = baseline.diff(base, [cl("gaps|record", 6)])

    assert diff.regressed == [(cl("gaps|record", 6), 5)]
    assert baseline.exit_code(diff) == baseline.EXIT_REGRESSION


def test_equal_count_passes():
    base = baseline.Baseline(manifest_hash="m", counts={"gaps|record": 5})

    diff = baseline.diff(base, [cl("gaps|record", 5)])

    assert baseline.exit_code(diff) == baseline.EXIT_OK


def test_lower_count_ratchets_and_passes():
    base = baseline.Baseline(manifest_hash="m", counts={"gaps|record": 5})

    diff = baseline.diff(base, [cl("gaps|record", 2)])

    assert diff.ratcheted == [("gaps|record", 5, 2)]
    assert baseline.exit_code(diff) == baseline.EXIT_OK
    assert baseline.apply_ratchet(base, diff).counts["gaps|record"] == 2


def test_cluster_gone_is_fixed_and_ratchets_to_zero():
    base = baseline.Baseline(manifest_hash="m", counts={"gaps|record": 5})

    diff = baseline.diff(base, [])

    assert diff.fixed == ["gaps|record"]
    assert baseline.apply_ratchet(base, diff).counts["gaps|record"] == 0


def test_the_regression_hole_the_ratchet_closes():
    """A cluster fixed to 0 then regressed below its accepted count must fail."""
    accepted = baseline.Baseline(manifest_hash="m", counts={"gaps|record": 100})

    fixed_run = baseline.diff(accepted, [])
    assert baseline.exit_code(fixed_run) == baseline.EXIT_OK
    ratcheted = baseline.apply_ratchet(accepted, fixed_run)

    regressed_run = baseline.diff(ratcheted, [cl("gaps|record", 80)])

    assert baseline.exit_code(regressed_run) == baseline.EXIT_REGRESSION


def test_roundtrip(tmp_path: Path):
    path = tmp_path / "baseline.json"
    original = baseline.Baseline(manifest_hash="abc", counts={"gaps|x": 3})

    baseline.save(path, original)

    assert baseline.load(path) == original
    assert json.loads(path.read_text(encoding="utf-8"))["manifest_hash"] == "abc"


def test_load_missing_returns_none(tmp_path: Path):
    assert baseline.load(tmp_path / "nope.json") is None
