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
    # BAD's multi-config tree has an error (a MISSING #endif), so its unmatched-tree
    # directive item is unreliable and must NOT promote the resolver failure.
    s = runner.run([("bad", BAD), ("ok", STMT)], None, workers=1, mode="full")
    by = {(r.input_id, r.status) for r in s.records}
    assert by == {("bad", "cannot-validate"), ("ok", "pass")}
    assert s.exit_code == 1


@pytest.mark.parametrize("first_failure", ["resolver", "reference", "none"])
def test_multi_config_parse_error_is_never_promoted_to_directive_mismatch(al_parser, monkeypatch, first_failure):
    from dataclasses import replace
    from tools.config_oracle import compare, directive_check, directives, reference
    # Only the MULTI-configuration tree gets the error (reference.extract also uses ir.from_tree,
    # so patching that would turn every variant into a reference failure).
    real_file_level, real_extract = runner._file_level, reference.extract

    def file_level(parser, input_id, source, disc):
        (root, extras, items), rep = real_file_level(parser, input_id, source, disc)
        return (root, extras, ["multi-config-parse:error@0"] + items), rep
    monkeypatch.setattr(runner, "_file_level", file_level)
    monkeypatch.setattr(directive_check, "check",
                        lambda root, disc: [compare.Discrepancy("directive", "condition-extent", "preproc_if@0", "x")])
    if first_failure == "resolver":
        def boom(source, env):
            raise directives.ResolveError("seed", 1)
        monkeypatch.setattr(directives, "resolve", boom)
    elif first_failure == "reference":
        monkeypatch.setattr(reference, "extract", lambda p, m: replace(real_extract(p, m), problems=["error@1"]))
    recs = runner.check_input(al_parser, "stmt", STMT)
    assert [r.status for r in recs] == ["cannot-validate", "cannot-validate"]


def test_directive_mismatch_reasons_are_counted_as_not_validated(tmp_path):
    recs = [runner.Record("a", "X=0", "directive-mismatch", ["a|-|directive|end-extent|p", "lowering:unsupported-type:t@3"]),
            runner.Record("a", "X=1", "directive-mismatch", ["a|-|directive|end-extent|p"])]
    runner.write_report(runner.Summary(recs, 0, 0.0, 0, 1), tmp_path, {})
    text = (tmp_path / "summary.md").read_text()
    assert "directive-mismatch configurations also not validated: 1 (lowering:unsupported-type 1)" in text


def test_directive_mismatch_does_not_short_circuit_the_comparison(al_parser, monkeypatch):
    from tools.config_oracle import compare, directive_check
    monkeypatch.setattr(directive_check, "check",
                        lambda root, disc: [compare.Discrepancy("directive", "condition-extent", "preproc_if@0", "x")])
    monkeypatch.setattr(compare, "structure",
                        lambda ref, low: [compare.Discrepancy("structure", "missing", "p", "y")])
    recs = runner.check_input(al_parser, "stmt", STMT)
    assert [r.status for r in recs] == ["directive-mismatch", "directive-mismatch"]
    for r in recs:
        assert r.items[0] == "stmt|-|directive|condition-extent|preproc_if@0"
        assert f"stmt|{r.config}|structure|missing|p" in r.items


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


# ---- fix round 1 ----

WHOLE_FILE_IN_IF = b"#if A\ncodeunit 1 T { }\n#endif\n"
EMPTY_BODY = b"codeunit 1 T\n{\n    trigger OnRun()\n    begin\n#if A\n        x := 1;\n#endif\n    end;\n}\n"


def test_empty_configuration_is_not_a_zero_width_leaf(al_parser):
    recs = {r.config: r for r in runner.check_input(al_parser, "w", WHOLE_FILE_IN_IF)}
    assert not any(i.startswith("zero-width-leaf") for i in recs["A=0"].items), recs["A=0"]


def test_childless_root_is_not_a_zero_width_leaf():
    assert runner.first_zero_width_leaf(Node("source_file", True, None, 0, 0, [])) is None
    deep = Node("source_file", True, None, 0, 0, [Node("x", True, None, 0, 0, [])])
    assert runner.first_zero_width_leaf(deep) == 0


def _rep_violation(monkeypatch):
    from tools.config_oracle.compare import Discrepancy
    from tools.config_oracle.lowering.engine import LoweringError
    monkeypatch.setattr(runner.representation, "check",
                        lambda root: [Discrepancy("representation", "var-block-without-var", "p@1", "procedure")])

    def fail(root, extras, res):
        raise LoweringError("unsupported-type", root)
    monkeypatch.setattr(runner, "lower_tree", fail)


def test_representation_violation_is_never_hidden_by_cannot_validate(monkeypatch, al_parser):
    _rep_violation(monkeypatch)
    recs = runner.check_input(al_parser, "stmt", STMT)
    assert {r.status for r in recs} == {"representation-violation"}
    for r in recs:
        assert r.items[0] == "stmt|-|representation|var-block-without-var|p@1"
        assert r.items[1].startswith("lowering:unsupported-type")


def test_representation_violation_is_never_classified(monkeypatch):
    _rep_violation(monkeypatch)
    classes = {("stmt", "*"): ("cannot-validate", "x"), ("stmt", "A=0"): ("representation-violation", "x")}
    s = runner.run([("stmt", STMT)], None, workers=1, mode="full", classes=classes)
    assert s.classified == 0 and s.exit_code == 1


def test_build_failure_exits_2(monkeypatch, tmp_path, capsys):
    from tools.config_oracle.__main__ import main
    from tools.query_coverage import loader

    def broken(*a, **k):
        raise RuntimeError("build failed")
    monkeypatch.setattr(loader, "ensure_library", broken)
    assert main(["run", "--tier", "quick", "--workers", "1", "--report", str(tmp_path)]) == 2
    assert "build failed" in capsys.readouterr().err


def test_normalisations_are_recorded_without_changing_status(al_parser):
    recs = {r.config: r for r in runner.check_input(al_parser, "e", EMPTY_BODY)}
    assert recs["A=0"].status == "pass"
    assert recs["A=0"].items == ["normalised:removed-empty:statement_block@45"]


def test_internal_error_carries_traceback(monkeypatch, al_parser):
    def crash(*a):
        raise KeyError("bug")
    monkeypatch.setattr(runner.compare, "structure", crash)
    recs = runner.check_input(al_parser, "stmt", STMT)
    assert "Traceback" in recs[0].items[0]


@pytest.mark.parametrize("mutate", [
    lambda recs: recs + [runner.Record(recs[0].input_id, "A=2", "pass")],              # extra config
    lambda recs: recs + [recs[0]],                                                      # duplicate config
    lambda recs: recs + [runner.Record("foreign", "-", "pass")],                        # foreign input
])
def test_any_record_mismatch_is_incomplete(monkeypatch, mutate):
    real = runner.check_input
    monkeypatch.setattr(runner, "check_input", lambda *a, **k: mutate(real(*a, **k)))
    with pytest.raises(runner.IncompleteRun):
        runner.run([("stmt", STMT)], None, workers=1, mode="full")


def test_workers_2_matches_workers_1(tmp_path):
    inputs = [("bad", BAD), ("ok", STMT), ("w", WHOLE_FILE_IN_IF), ("e", EMPTY_BODY)] * 1
    out = {}
    for w in (1, 2):
        runner.write_report(runner.run(inputs, None, workers=w, mode="full"), tmp_path / str(w), {})
        out[w] = (tmp_path / str(w) / "findings.jsonl").read_bytes()
    assert out[1] == out[2]


# ---- final review, finding 1: a stray #endif/#else/#elif is a conditional directive ----

@pytest.mark.parametrize("stray", [b"#endif", b"#else", b"#elif A"])
def test_lone_stray_conditional_is_an_input_not_no_directives(stray):
    src = b"codeunit 1 X {\n" + stray + b"\n}"
    expected, no_dir, todo = runner._expected([("s", src)])
    assert no_dir == 0 and todo == ["s"] and expected["s"]
    s = runner.run([("s", src)], None, workers=1, mode="full")
    assert s.no_directives == 0 and s.records
    assert {r.status for r in s.records} == {"cannot-validate"}
    assert all(r.items[0].startswith("resolver:") for r in s.records)
