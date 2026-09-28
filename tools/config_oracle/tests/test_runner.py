import pytest

from tools.config_oracle import runner
from tools.config_oracle.ir import Node
from tools.config_oracle.tests.test_lowering_select import STMT

BAD = b"#if A\ncodeunit 1 T { }\n"          # unterminated #if: every configuration fails to resolve


def test_clean_input_passes_in_every_configuration(al_parser):
    recs = runner.check_input(al_parser, "stmt", STMT)
    assert [(r.config, r.status) for r in recs] == [("A=0", "pass"), ("A=1", "pass")]


def test_resolve_mode_checks_resolver_and_reference_only(al_parser):
    recs = runner.check_input(al_parser, "stmt", STMT, mode="resolve")
    assert [(r.config, r.status) for r in recs] == [("A=0", "pass"), ("A=1", "pass")]


def test_region_only_file_is_counted_not_validated():
    s = runner.run([("r", b"#region R\ncodeunit 1 T { }\n#endregion\n")], None, workers=1, mode="full")
    assert s.no_directives == 1 and s.exit_code == 2      # zero validated pairs


def test_resolver_failure_is_one_cannot_validate_record():
    s = runner.run([("bad", BAD), ("ok", STMT)], None, workers=1, mode="full")
    by = {(r.input_id, r.status) for r in s.records}
    assert ("bad", "cannot-validate") in by and ("ok", "pass") in by
    assert s.exit_code == 1


def test_discover_failure_is_exactly_one_dash_record(monkeypatch):
    from tools.config_oracle import directives

    def boom(source):
        raise directives.ResolveError("seed", 3)
    monkeypatch.setattr(directives, "discover", boom)
    s = runner.run([("x", STMT)], None, workers=1, mode="full")
    assert [(r.input_id, r.config, r.status) for r in s.records] == [("x", "-", "cannot-validate")]
    assert s.records[0].items == ["resolver:seed@3"]


def test_dropped_record_is_incomplete(monkeypatch, al_parser):
    real = runner.check_input
    monkeypatch.setattr(runner, "check_input", lambda *a, **k: real(*a, **k)[:-1])
    with pytest.raises(runner.IncompleteRun):
        runner.run([("stmt", STMT)], None, workers=1, mode="full")


def test_single_dash_record_does_not_excuse_predicted_configurations(monkeypatch):
    # The parent predicted A=0 and A=1; one "-" record in their place is a drop, not the discover-failure path.
    monkeypatch.setattr(runner, "check_input",
                        lambda parser, input_id, source, mode="full": [runner.Record(input_id, "-", "cannot-validate")])
    with pytest.raises(runner.IncompleteRun):
        runner.run([("stmt", STMT)], None, workers=1, mode="full")


def test_classified_record_does_not_fail_the_run():
    classes = {("bad", "*"): ("cannot-validate", "deliberately unterminated")}
    s = runner.run([("bad", BAD), ("ok", STMT)], None, workers=1, mode="full", classes=classes)
    assert s.exit_code == 0 and s.classified == 2


def test_classification_with_a_different_status_does_not_count():
    classes = {("bad", "A=0"): ("discrepancy", "wrong expectation")}
    s = runner.run([("bad", BAD), ("ok", STMT)], None, workers=1, mode="full", classes=classes)
    assert s.exit_code == 1 and s.classified == 0


def test_first_zero_width_leaf():
    ok = Node("a", True, None, 0, 2, [Node("b", False, None, 0, 2, [])])
    bad = Node("a", True, None, 0, 2, [Node("b", False, None, 0, 2, []), Node("c", True, None, 2, 2, [])])
    assert runner.first_zero_width_leaf(ok) is None
    assert runner.first_zero_width_leaf(bad) == 2


def test_zero_width_leaf_in_lowered_tree_cannot_validate(monkeypatch, al_parser):
    real = runner.lower_tree

    def lower_with_empty_leaf(root, extras, res):
        low, kept, norm = real(root, extras, res)
        low.children.append(Node("phantom", True, None, low.end, low.end, []))
        return low, kept, norm
    monkeypatch.setattr(runner, "lower_tree", lower_with_empty_leaf)
    recs = runner.check_input(al_parser, "stmt", STMT)
    assert {r.status for r in recs} == {"cannot-validate"}
    assert all(r.items[0].startswith("zero-width-leaf@") for r in recs)


def test_boundary_discrepancy_is_part_of_the_record(monkeypatch, al_parser):
    from tools.config_oracle.compare import Discrepancy
    monkeypatch.setattr(runner.compare, "leaf_boundaries",
                        lambda ref, low: [Discrepancy("structure", "boundary", "<root>", "x")])
    recs = runner.check_input(al_parser, "stmt", STMT)
    assert [r.status for r in recs] == ["discrepancy", "discrepancy"]
    assert recs[0].items == ["stmt|A=0|structure|boundary|<root>"]


def test_oracle_crash_is_recorded_and_exits_2(monkeypatch):
    def crash(*a):
        raise KeyError("bug")
    monkeypatch.setattr(runner.compare, "structure", crash)
    s = runner.run([("stmt", STMT)], None, workers=1, mode="full")
    assert {r.status for r in s.records} == {"cannot-validate"}
    assert s.records[0].items[0].startswith("internal-error:KeyError")
    assert s.exit_code == 2


def test_resolve_tier_needs_existing_roots(tmp_path):
    from tools.config_oracle.__main__ import main
    assert main(["run", "--tier", "resolve"]) == 2
    assert main(["run", "--tier", "resolve", "--root", str(tmp_path), "--root", str(tmp_path / "nope")]) == 2


def test_report_files(tmp_path):
    s = runner.run([("bad", BAD), ("ok", STMT)], None, workers=1, mode="full")
    runner.write_report(s, tmp_path, {"tier": "test"})
    assert len((tmp_path / "findings.jsonl").read_text().splitlines()) == len(s.records)
    text = (tmp_path / "summary.md").read_text()
    assert "configurations not validated" in text and "exit code: 1" in text


def test_peak_rss_is_positive():
    assert runner.peak_rss_bytes() > 0
