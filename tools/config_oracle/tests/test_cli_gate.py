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

@pytest.fixture(autouse=True)
def _labels(monkeypatch, tmp_path):
    """A private copy of the root -> label map, which `_root` extends (each root is
    labelled by its directory name), and an empty production classification file."""
    monkeypatch.setattr(cli, "CORPORA", dict(cli.CORPORA))
    classes = tmp_path / "production-classes.tsv"
    classes.write_text("# none\n", encoding="utf-8")
    monkeypatch.setattr(cli, "PRODUCTION_CLASSES", classes)


def _root(tmp_path, name, files, label=True):
    d = tmp_path / name
    d.mkdir()
    for fname, src in files.items():
        (d / fname).parent.mkdir(parents=True, exist_ok=True)
        (d / fname).write_bytes(src)
    if label:
        cli.CORPORA[name] = d
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


# ---- production classifications (roadmap A4) ---------------------------------------

BAD = b"#if A\ncodeunit 1 T { }\n"          # unterminated #if: A=0 and A=1 cannot-validate
SRC_PROBE = "tools/alc_probe/cases/production-invalid/fixed-asset-shift.al"
SRC_ID = "bcapps-29.0:src/Apps/IN/INFADepreciation/app/src/table/FixedAssetShift.Table.al"


def _classify(tmp_path, *lines):
    cli.PRODUCTION_CLASSES.write_text("# test\n" + "".join(l + "\n" for l in lines), encoding="utf-8")


def _entry(case, cfg="*", prefix="resolver:unbalanced-if", reason="other: synthetic, unterminated #if"):
    return f"{case}\t{cfg}\tcannot-validate:{prefix}\t{reason}"


def test_input_ids_are_label_and_posix_relative_path(tmp_path, capsys):
    a = _root(tmp_path, "a", {"s.al": STMT, "sub/bad.al": BAD})   # all-refused would be exit 2
    assert _resolve(a, tmp_path=tmp_path) == 1
    ids = {r["input_id"] for r in map(__import__("json").loads,
                                       (tmp_path / "rep" / "findings.jsonl").read_text().splitlines())}
    assert ids == {"a:s.al", "a:sub/bad.al"}


def test_a_root_with_no_label_exits_2(tmp_path, capsys):
    a = _root(tmp_path, "a", {"s.al": STMT}, label=False)
    assert _resolve(a, tmp_path=tmp_path) == 2
    assert f"corpus root has no label: {a}" in capsys.readouterr().err


def test_the_same_root_spelled_two_ways_gets_one_label(tmp_path):
    a = _root(tmp_path, "a", {"s.al": STMT})
    assert cli.corpus_label(a) == cli.corpus_label(a / "." / ".." / "a") == "a"


def test_a_clean_classified_production_run_exits_0(tmp_path, capsys):
    a = _root(tmp_path, "a", {"s.al": STMT, "bad.al": BAD})
    _classify(tmp_path, _entry("a:bad.al"))
    assert _resolve(a, tmp_path=tmp_path) == 0
    out = capsys.readouterr().out
    assert "- stale classifications: 0" in out and "- exit code: 0" in out


def test_a_classified_record_still_counts_as_not_validated(tmp_path, capsys):
    a = _root(tmp_path, "a", {"s.al": STMT, "bad.al": BAD})
    _classify(tmp_path, _entry("a:bad.al"))
    assert _resolve(a, tmp_path=tmp_path) == 0
    out = capsys.readouterr().out
    assert "- validated (pass): 2\n" in out                        # s.al's two, nothing else
    assert "- not validated, classified by category: 2 (other 2)\n" in out
    assert "- not validated, unclassified: 0\n" in out
    # every matched `other` entry is printed
    assert "  - `a:bad.al A=0`: other: synthetic" in out
    assert "  - `a:bad.al A=1`: other: synthetic" in out


def test_an_unclassified_refusal_exits_1(tmp_path, capsys):
    a = _root(tmp_path, "a", {"s.al": STMT, "bad.al": BAD, "bad2.al": BAD})
    _classify(tmp_path, _entry("a:bad.al"))
    assert _resolve(a, tmp_path=tmp_path) == 1
    assert "- not validated, unclassified: 2\n" in capsys.readouterr().out


def test_a_stale_production_entry_exits_1(tmp_path, capsys):
    a = _root(tmp_path, "a", {"s.al": STMT, "bad.al": BAD})
    _classify(tmp_path, _entry("a:bad.al"), _entry("a:s.al", "A=0"))
    assert _resolve(a, tmp_path=tmp_path) == 1
    out = capsys.readouterr().out
    assert "- stale classifications: 1" in out and "a:s.al\tA=0" in out


def test_an_entry_for_a_corpus_not_requested_is_neither_stale_nor_applied(tmp_path, capsys):
    a = _root(tmp_path, "a", {"s.al": STMT, "bad.al": BAD})
    b = _root(tmp_path, "b", {"s.al": STMT, "bad.al": BAD})
    _classify(tmp_path, _entry("a:bad.al"), _entry("b:bad.al"), _entry("b:gone.al"))
    assert _resolve(a, tmp_path=tmp_path) == 0                     # b's entries: not stale
    out = capsys.readouterr().out
    assert "1 of 3 entries apply" in out and "- stale classifications: 0" in out
    _classify(tmp_path, _entry("a:bad.al"))
    assert _resolve(b, tmp_path=tmp_path) == 1                     # a's entry: not applied to b


def test_an_entry_naming_an_unknown_corpus_label_exits_2(tmp_path, capsys):
    a = _root(tmp_path, "a", {"s.al": STMT})
    _classify(tmp_path, _entry("nosuch:bad.al"))
    assert _resolve(a, tmp_path=tmp_path) == 2


def test_the_resolve_tier_applies_only_entries_for_its_stages(tmp_path, capsys):
    a = _root(tmp_path, "a", {"s.al": STMT})
    _classify(tmp_path, _entry("a:s.al", prefix="lowering:unsupported-type:unsupported-type at "
                               "preproc_x: host statement_block:<children>"))
    assert _resolve(a, tmp_path=tmp_path) == 0
    assert "0 of 1 entries apply" in capsys.readouterr().out


def test_a_discrepancy_is_never_classified():
    rec = runner.Record("a:x.al", "A=0", "discrepancy", ["resolver:x@1"])
    classes = {("a:x.al", "A=0"): ("cannot-validate:resolver", "other: x")}
    assert not runner.is_classified(rec, classes)


# ---- the production loader ----

def _load(tmp_path, line):
    p = tmp_path / "p.tsv"
    p.write_text(line + "\n", encoding="utf-8")
    return fixtures.load_classes(p, "production")


@pytest.mark.parametrize("reason", ["debt(C1, M3): no handler for preproc_x at y",
                                    "debt(F1, F1): needs the configuration-aware parse",
                                    "other: something"])
def test_production_categories_load(tmp_path, reason):
    assert _load(tmp_path, _entry("a:x.al", reason=reason))


@pytest.mark.parametrize("reason", ["debt(C1): no milestone", "debt(Z9, M3): unknown owner",
                                    "debt(C1, M9): unknown milestone", "debt(C1,M3): no space",
                                    "negative: a fixture category", "other:", "invalid-source x"])
def test_malformed_production_categories_are_rejected(tmp_path, reason):
    with pytest.raises(ValueError):
        _load(tmp_path, _entry("a:x.al", reason=reason))


def test_a_malformed_debt_owner_exits_2(tmp_path, capsys):
    a = _root(tmp_path, "a", {"s.al": STMT, "bad.al": BAD})
    _classify(tmp_path, _entry("a:bad.al", reason="debt(Z9, M3): nobody"))
    assert _resolve(a, tmp_path=tmp_path) == 2
    assert "debt owner Z9 is not a roadmap sub-project" in capsys.readouterr().err


def test_invalid_source_needs_its_own_probe(tmp_path):
    ok = f"invalid-source: CLEANSCHEMA26 defined; evidence: alc_probe {SRC_PROBE}"
    assert _load(tmp_path, _entry(SRC_ID, "CLEANSCHEMA26=1", "reference-error:error", ok))
    with pytest.raises(ValueError, match="evidence"):
        _load(tmp_path, _entry(SRC_ID, "CLEANSCHEMA26=1", "reference-error:error", "invalid-source: x"))
    with pytest.raises(ValueError, match="is the probe for"):      # `// Source` names another input
        _load(tmp_path, _entry(SRC_ID.replace("Shift", "Shift2"), "CLEANSCHEMA26=1", "reference-error:error", ok))
    with pytest.raises(ValueError, match="does not expect a reject"):   # alc accepts CLEANSCHEMA26=0
        _load(tmp_path, _entry(SRC_ID, "CLEANSCHEMA26=0", "reference-error:error", ok))
    with pytest.raises(ValueError, match="needs alc_probe evidence"):
        _load(tmp_path, _entry(SRC_ID, "*", "reference-error:error",
                               "invalid-source: x; evidence: alc manual, 2026-09-29"))


def test_the_real_production_file_loads():
    assert fixtures.load_classes(cli.REPO / "tools" / "config_oracle" / "production-classes.tsv",
                                 "production") is not None


ARM = "lowering:arm-content:arm-content at case_else_branch@9493: case_else_branch not declared for preproc_conditional_case"


def test_reason_key_drops_the_offset_and_keeps_the_host():
    assert runner.reason_key(ARM) == ("lowering:arm-content:arm-content at case_else_branch: "
                                      "case_else_branch not declared for preproc_conditional_case")
    assert runner.reason_key("reference-error:error@12,error@40") == "reference-error:error"
    assert runner.reason_key("lowering:unsupported-type:unsupported-type at x@5") == \
        "lowering:unsupported-type:unsupported-type at x"


@pytest.mark.parametrize("prefix, hit", [
    ("lowering:arm-content:arm-content at case_else_branch", True),
    ("lowering:arm-content:arm-content at case_else_branch: case_else_branch not declared "
     "for preproc_conditional_case", True),
    ("lowering:arm-content:arm-content at case_else_branch: case_else_branch not declared "
     "for some_other_host", False),
    ("lowering:arm-content:arm-content at case_else", False),        # whole segments only
])
def test_an_entry_can_pin_the_host(prefix, hit):
    rec = runner.Record("a:x.al", "A=0", "cannot-validate", [ARM])
    assert runner.is_classified(rec, {("a:x.al", "A=0"): (f"cannot-validate:{prefix}", "other: x")}) is hit


# ---- the host is part of the key (A4 fix 1, I1) ----
# One refused construct in two hosts. The oracle records the host of an unsupported-type
# and a one-reading refusal (`: host <parent>:<slot>`), so a grammar change that
# re-parents the node changes the key and its entry no longer classifies the record.

_SPLIT_THEN = ("        if not IsHandled then\n#if not C27\n            if Q <> 0 then begin\n"
               "                Message('a');\n#endif\n                Message('b');\n"
               "#if not C27\n            end;\n#endif\n        Message('c');\n")
_SPLIT_STMT = _SPLIT_THEN.replace("        if not IsHandled then\n", "", 1)
_ELSE_LED_IF = ("        if N < 1 then\n            Message('a')\n#if not C28\n        else begin\n"
                "#else\n        else\n#endif\n            Message('b');\n#if not C28\n"
                "            Message('c');\n        end;\n#endif\n")
_ELSE_LED_CASE = ("        case N of\n            1:\n                Message('a')\n" +
                  _ELSE_LED_IF.split("            Message('a')\n", 1)[1] + "        end;\n")


def _proc(body):
    return ("codeunit 1 T\n{\n    procedure P(N: Integer; Q: Integer; IsHandled: Boolean)\n"
            "    begin\n" + body + "    end;\n}\n").encode()


@pytest.mark.parametrize("a, b, kind, host_a, host_b", [
    (_SPLIT_STMT, _SPLIT_THEN, "unsupported-type at preproc_split_if_then_begin",
     "statement_block:<children>", "if_statement:then_branch"),
    (_ELSE_LED_IF, _ELSE_LED_CASE, "one-reading at preproc_split_open_statement",
     "statement_block:<children>", "case_body:<children>"),
])
def test_a_record_whose_host_differs_from_its_entry_is_not_classified(al_parser, a, b, kind, host_a, host_b):
    from tools.config_oracle.tests import witness
    recs = {}
    for name, src in (("a", a), ("b", b)):
        v = witness.verdicts(al_parser, _proc(src), "x:y.al")
        cfg, (status, items) = sorted(v.items())[0]
        assert status == "cannot-validate", v
        recs[name] = runner.Record("x:y.al", cfg, status, items)
    key_a, key_b = (runner.reason_key(recs[n].items[0]) for n in "ab")
    assert key_a == f"lowering:{kind.split(' ')[0]}:{kind}: host {host_a}", key_a
    assert key_b == f"lowering:{kind.split(' ')[0]}:{kind}: host {host_b}", key_b
    for n in "ab":
        entry = {("x:y.al", recs[n].config): (f"cannot-validate:{key_a}", "debt(C1, M3): x")}
        assert runner.is_classified(recs[n], entry) is (n == "a")


def test_a_production_lowering_entry_must_name_type_and_host(tmp_path):
    """M4: `cannot-validate:lowering` alone would absorb any refusal of that input and
    configuration; an unsupported-type or one-reading entry must also pin the host."""
    ok = "lowering:unsupported-type:unsupported-type at preproc_x: host statement_block:<children>"
    assert _load(tmp_path, _entry("a:x.al", prefix=ok, reason="debt(C1, M3): x"))
    assert _load(tmp_path, _entry("a:x.al", prefix="lowering:one-reading:one-reading at integer: "
                                  "signed literal continued by a live tail", reason="debt(C1, M3): x"))
    for short in ("lowering", "lowering:unsupported-type", "lowering:unsupported-type:unsupported-type",
                  "lowering:unsupported-type:unsupported-type at preproc_x",
                  "lowering:one-reading:one-reading at preproc_x"):
        with pytest.raises(ValueError, match="lowering"):
            _load(tmp_path, _entry("a:x.al", prefix=short, reason="debt(C1, M3): x"))


def test_the_real_production_file_has_no_selftest_entry():
    """M3: the test-only `selftest` label is never requested by a production run, so a
    committed entry for it would be neither applied nor stale-checked."""
    classes = fixtures.load_classes(cli.REPO / "tools" / "config_oracle" / "production-classes.tsv",
                                    "production")
    assert not [k for k, _ in classes if k.startswith("selftest:")]

