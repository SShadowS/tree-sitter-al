"""The CLI as a gate (roadmap A3): quick-tier stages, per-root accounting, exit codes."""
from __future__ import annotations

import pytest

from tools.config_oracle import __main__ as cli
from tools.config_oracle import contracts, fixtures, runner
from tools.config_oracle.tests.test_lowering_select import STMT

FLAT = b"codeunit 2 U { }\n"


@pytest.fixture
def tiny_quick(monkeypatch, tmp_path):
    """The quick tier over one small fixture case, with stage (b) stubbed (it is a pytest
    run of its own, and nesting one here would re-run the suite inside the suite)."""
    monkeypatch.setattr(fixtures, "extract", lambda root: [fixtures.Case("t.txt", "n", 0, STMT, 0)])
    classes = tmp_path / "classes.tsv"
    classes.write_text("# none\n", encoding="utf-8")
    monkeypatch.setattr(cli, "CLASSES", classes)
    monkeypatch.setattr(cli, "_stage_selftests", lambda: (0, "PASS (stubbed)", []))
    return ["run", "--tier", "quick", "--workers", "1", "--report", str(tmp_path / "rep")]


def _stage_lines(out):
    return [line for line in out.splitlines() if line.startswith("- stage ")]


def test_quick_reports_one_line_per_stage_in_order(tiny_quick, capsys):
    assert cli.main(tiny_quick) == 0
    assert _stage_lines(capsys.readouterr().out) == [
        "- stage (a) registry census: PASS",
        "- stage (b) self-tests: PASS (stubbed)",
        "- stage (c) fixture differential: PASS",
    ]


def test_census_failure_exits_1_names_the_problem_and_later_stages_still_run(tiny_quick, capsys, monkeypatch):
    monkeypatch.setattr(contracts, "census", lambda nt: ["unregistered: preproc_zz_selftest"])
    assert cli.main(tiny_quick) == 1
    out = capsys.readouterr().out
    assert _stage_lines(out) == [
        "- stage (a) registry census: FAIL (1 problems)",
        "- stage (b) self-tests: PASS (stubbed)",
        "- stage (c) fixture differential: PASS",
    ]
    assert "  unregistered: preproc_zz_selftest" in out
    assert "- quick tier exit code: 1" in out


def test_a_stage_that_crashes_is_could_not_run_and_the_run_exits_2(tiny_quick, capsys, monkeypatch):
    def boom(nt):
        raise RuntimeError("census exploded")
    monkeypatch.setattr(contracts, "census", boom)
    monkeypatch.setattr(cli, "_stage_selftests", lambda: (1, "FAIL (pytest exit 1)", ["1 failed"]))
    assert cli.main(tiny_quick) == 2
    out = capsys.readouterr().out
    assert _stage_lines(out)[0] == "- stage (a) registry census: COULD NOT RUN"
    assert _stage_lines(out)[1] == "- stage (b) self-tests: FAIL (pytest exit 1)"
    assert "census exploded" in out


def test_a_fixture_discrepancy_fails_stage_c(tiny_quick, capsys, monkeypatch):
    real = runner.check_input

    def planted(parser, input_id, source, mode="full"):
        recs = real(parser, input_id, source, mode)
        recs[0].status, recs[0].items = "discrepancy", ["planted|structure|missing|x"]
        return recs
    monkeypatch.setattr(runner, "check_input", planted)
    assert cli.main(tiny_quick) == 1
    out = capsys.readouterr().out
    assert _stage_lines(out)[2].startswith("- stage (c) fixture differential: FAIL (exit 1")
    assert "- discrepancy: 1" in out


def test_a_missing_pytest_is_could_not_run_not_a_finding(monkeypatch):
    import importlib.util
    real = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, "find_spec", lambda n, *a: None if n == "pytest" else real(n, *a))
    code, status, _ = cli._stage_selftests()
    assert (code, status) == (2, "COULD NOT RUN (pytest is not installed)")


def test_a_build_failure_leaves_no_stale_summary(tiny_quick, tmp_path, monkeypatch):
    from tools.query_coverage import loader
    rep = tmp_path / "rep"
    rep.mkdir()
    (rep / "summary.md").write_text("an earlier green run\n", encoding="utf-8")

    def broken(root):
        raise loader.StaleParserError("tree-sitter build failed")
    monkeypatch.setattr(loader, "ensure_library", broken)
    assert cli.main(tiny_quick) == 2
    assert "could not run (exit 2)" in (rep / "summary.md").read_text(encoding="utf-8")


def test_a_refused_resolve_run_leaves_no_stale_summary(tmp_path):
    rep = tmp_path / "rep"
    rep.mkdir()
    (rep / "summary.md").write_text("an earlier green run\n", encoding="utf-8")
    assert _resolve(tmp_path / "missing", tmp_path=tmp_path) == 2
    assert "could not run (exit 2)" in (rep / "summary.md").read_text(encoding="utf-8")


def test_selftest_stage_runs_the_named_modules():
    code, status, lines = cli._stage_selftests()
    assert (code, lines) == (0, []) and status.startswith("PASS (") and " passed" in status


# ---- per-root accounting -----------------------------------------------------------

def _root(tmp_path, name, files):
    d = tmp_path / name
    d.mkdir()
    for fname, src in files.items():
        (d / fname).write_bytes(src)
    return d


def _resolve(*roots, tmp_path):
    args = ["run", "--tier", "resolve", "--workers", "1", "--report", str(tmp_path / "rep")]
    for r in roots:
        args += ["--root", str(r)]
    return cli.main(args)


def test_per_root_table_adds_up(tmp_path, capsys):
    a = _root(tmp_path, "a", {"s.al": STMT, "f.al": FLAT})
    b = _root(tmp_path, "b", {"s1.al": STMT, "s2.al": STMT, "f.al": FLAT})
    assert _resolve(a, b, tmp_path=tmp_path) == 0
    out = capsys.readouterr().out
    assert f"| {a} | 2 | 2 | 2 | 0 | 0 | 0 | 0 |" in out
    assert f"| {b} | 3 | 4 | 4 | 0 | 0 | 0 | 0 |" in out
    assert "| **total** | 5 | 6 | 6 | 0 | 0 | 0 | 0 |" in out


def test_cannot_validate_reasons_are_per_root(tmp_path, capsys):
    a = _root(tmp_path, "a", {"s.al": STMT})
    b = _root(tmp_path, "b", {"bad.al": b"#if A\ncodeunit 1 T { }\n"})    # unterminated #if
    assert _resolve(a, b, tmp_path=tmp_path) == 1
    assert f"| {b} | 1 | 2 | 0 | 0 | 0 | 0 | 2 (resolver:unbalanced-if 2) |" in capsys.readouterr().out


def test_an_empty_root_beside_a_healthy_one_exits_2_naming_it(tmp_path, capsys):
    a = _root(tmp_path, "a", {"s.al": STMT})
    empty = _root(tmp_path, "empty", {"notes.txt": b"no AL here"})
    assert _resolve(a, empty, tmp_path=tmp_path) == 2
    assert f"corpus root has no .al files: {empty}" in capsys.readouterr().err


@pytest.mark.parametrize("second", ["same", "nested", "parent"])
def test_overlapping_roots_are_rejected_with_exit_2(tmp_path, capsys, second):
    a = _root(tmp_path, "a", {"s.al": STMT})
    sub = _root(a, "sub", {"t.al": STMT})
    roots = {"same": (a, a), "nested": (a, sub), "parent": (sub, a)}[second]
    assert _resolve(*roots, tmp_path=tmp_path) == 2
    assert "corpus roots overlap" in capsys.readouterr().err


def _summary(records, expected):
    return runner.Summary(records, 0, 0.0, 0, 0, expected=expected)


def test_per_root_rejects_a_record_from_no_requested_root():
    recs = [runner.Record("x", "-", "pass")]
    with pytest.raises(runner.IncompleteRun, match="no requested root"):
        runner.per_root(_summary(recs, {"x": ["-"]}), {}, {"r": 1})


def test_per_root_rejects_a_root_missing_a_predicted_record():
    recs = [runner.Record("x", "A=0", "pass")]
    with pytest.raises(runner.IncompleteRun, match="expected"):
        runner.per_root(_summary(recs, {"x": ["A=0", "A=1"]}), {"x": "r"}, {"r": 1})


# ---- replay ------------------------------------------------------------------------

def test_replay_exits_2_when_a_historical_parser_cannot_be_built(monkeypatch, capsys):
    from tools.config_oracle import replay

    def unavailable(commit):
        raise RuntimeError(f"git rev-parse {commit} failed: unknown revision")
    monkeypatch.setattr(replay, "cached_parser_at", unavailable)
    assert cli.main(["replay"]) == 2
    assert "could not run" in capsys.readouterr().err
