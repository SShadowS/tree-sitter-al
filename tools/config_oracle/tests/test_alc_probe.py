"""tools/alc_probe: the shared alc compile core and the split/flat matrix runner.

Fast tests fake `al` through the injected runner. The `slow` tests need the real
compiler and skip where `al` is not on PATH (it is not in CI).
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from tools.alc_probe import core
from tools.alc_probe.matrix import CaseError, main, parse_case
from tools.config_oracle.directives import resolve

REPO = Path(__file__).resolve().parents[3]
CASES = REPO / "tools" / "alc_probe" / "cases"

GOOD = "codeunit 50100 T { trigger OnRun() begin Message('x'); end; }\n"


def fake_al(split_sees_raw_text=False):
    """A fake `al`: rejects any source whose ACTIVE text contains GARBAGE or BAD.

    The active text is computed with the oracle resolver, so split and flat agree,
    unless `split_sees_raw_text`: then a split compile judges the raw file, which
    is how a real disagreement between alc and the resolver would look.
    """
    calls = []

    def runner(args):
        calls.append(list(args))
        if args[1] == "--version":
            return subprocess.CompletedProcess(args, 0, "9.9.9-fake\n", "")
        project = Path(args[2].split(":", 1)[1])
        out = Path(args[3].split(":", 1)[1])
        src = (project / "Test.al").read_text(encoding="utf-8")
        syms = json.loads((project / "app.json").read_text(encoding="utf-8"))["preprocessorSymbols"]
        text = src if split_sees_raw_text and "#if" in src else resolve(src.encode(), frozenset(syms)).masked.decode()
        log = "error AL1021: The package cache path has not been specified.\n"
        if "GARBAGE" in text or "BAD" in text:
            return subprocess.CompletedProcess(args, 1, log + "Test.al(1,1): error AL0104: Syntax error\n", "")
        out.write_bytes(b"app")
        return subprocess.CompletedProcess(args, 0, log, "")

    runner.calls = calls
    return runner


@pytest.fixture
def fake_exe(tmp_path):
    exe = tmp_path / "al-fake.exe"
    exe.write_bytes(b"not really al")
    return str(exe)


def write(dirpath: Path, name: str, text: str) -> Path:
    p = dirpath / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def run(tmp_path, fake_exe, runner, *extra, cases=None):
    return main(["run", str(cases or tmp_path / "cases"), *extra], runner=runner, al=fake_exe)


# --- header parsing ---------------------------------------------------------

SPLIT = "#if not S31\nMessage('a');\n#else\nBAD\n#endif\n"


def test_header_fields_and_last_matching_expect_wins():
    text = ("// Valid only with S31 undefined.\n// expect: * accept\n// expect: S31 reject\n"
            "// runtime: 17.0\n// source: somewhere, commit abc\n// expect-mismatch: S31\n") + SPLIT
    c = parse_case(Path("x.al"), "x.al", text, check=True)
    assert c.runtime == "17.0" and c.sources == ["somewhere, commit abc"]
    assert c.symbols == ("S31",)
    assert c.expected(frozenset()) == "ACCEPT"
    assert c.expected(frozenset({"S31"})) == "REJECT"
    assert c.mismatch_expected(frozenset({"S31"})) and not c.mismatch_expected(frozenset())


def test_negated_literal_and_conjunction():
    text = ("// expect: !A accept\n// expect: A !B reject\n// expect: A B accept\n// source: s\n"
            "#if A\n#if B\nx\n#endif\n#endif\n")
    c = parse_case(Path("x.al"), "x.al", text, check=True)
    got = {tuple(sorted(e)): c.expected(e) for e in c.envs}
    assert got == {(): "ACCEPT", ("B",): "ACCEPT", ("A",): "REJECT", ("A", "B"): "ACCEPT"}


@pytest.mark.parametrize("header, why", [
    ("// expect: * maybe\n// source: s\n", "verdict word"),
    ("// expect: accept\n// source: s\n", "no assignment"),
    ("// expect: NOPE accept\n// source: s\n", "symbol not in the conditions"),
    ("// expect: A-B accept\n// source: s\n", "not a literal"),
    ("// expected: * accept\n// source: s\n", "misspelt key"),
    ("// runtime: fifteen\n// expect: * accept\n// source: s\n", "bad runtime"),
    ("// expect: A accept\n// source: s\n", "!A not covered under --check"),
    ("// expect: * accept\n", "no source under --check"),
    ("// expect: * accept\n// source:\n", "empty source"),
])
def test_malformed_header_exits_2(tmp_path, fake_exe, header, why):
    write(tmp_path / "cases", "c.al", header + "#if A\nMessage('a');\n#endif\n")
    runner = fake_al()
    assert run(tmp_path, fake_exe, runner, "--check") == 2, why
    assert not [c for c in runner.calls if c[1] == "compile"], "nothing may compile when a header is malformed"


def test_unresolvable_directives_exit_2(tmp_path, fake_exe):
    write(tmp_path / "cases", "c.al", "// expect: * accept\n// source: s\n#if A\nx\n")
    assert run(tmp_path, fake_exe, fake_al(), "--check") == 2


def test_without_check_expect_and_source_are_optional(tmp_path, fake_exe):
    write(tmp_path / "cases", "c.al", "#if A\nMessage('a');\n#endif\n")
    assert run(tmp_path, fake_exe, fake_al()) == 0


# --- symbol discovery -------------------------------------------------------

@pytest.mark.parametrize("body, symbols", [
    (GOOD, ()),
    ("#if A\nx\n#elif B\ny\n#else\nz\n#endif\n", ("A", "B")),
    ("#if A\n#if not C\nx\n#endif\n#endif\n", ("A", "C")),
    ("#if (A or B) and not D\nx\n#endif\n", ("A", "B", "D")),
    ("// #if COMMENTED\nx\n", ()),
])
def test_symbol_discovery(body, symbols):
    c = parse_case(Path("x.al"), "x.al", body, check=False)
    assert c.symbols == symbols
    assert len(c.envs) == 2 ** len(symbols)


def test_zero_symbol_case_compiles_once_split_once_flat(tmp_path, fake_exe):
    write(tmp_path / "cases", "c.al", "// expect: * accept\n// source: s\n" + GOOD)
    runner = fake_al()
    assert run(tmp_path, fake_exe, runner, "--check") == 0
    assert len([c for c in runner.calls if c[1] == "compile"]) == 2 + 2   # two controls + split + flat


def test_every_assignment_compiled_split_with_symbols_and_flat_without(tmp_path, fake_exe):
    write(tmp_path / "cases", "c.al", "// expect: * accept\n// source: s\n#if A\nx\n#elif B\ny\n#endif\n")
    runner = fake_al()
    assert run(tmp_path, fake_exe, runner, "--check") == 0
    projects = [Path(c[2].split(":", 1)[1]) for c in runner.calls if c[1] == "compile"][2:]
    assert len(projects) == 8
    assert len(set(projects)) == 8, "each compile needs its own directory"


# --- classification ---------------------------------------------------------

@pytest.mark.parametrize("app, log, kind", [
    (True, "error AL1021: x", core.ACCEPT),
    (True, "", core.ACCEPT),
    (False, "error AL1021: x\nT.al(1,1): error AL0104: y", core.REJECT),
    (False, "error AL1021: The package cache path has not been specified.", core.BROKEN),
    (False, "", core.BROKEN),
    # project-level codes alc 18.0.41 gives for a broken project are not a rejection
    (False, "error AL1021: x\nerror AL1043: runtime 19.0 not supported", core.BROKEN),
    (False, "error AL1001: Source file '...\\app.json' could not be found", core.BROKEN),
    (False, "error AL1017: The manifest file is not valid.", core.BROKEN),
    (False, "error AL1043: x\nT.al(1,1): error AL0104: y", core.REJECT),
])
def test_classify(app, log, kind):
    v = core.classify(app, log)
    assert v.kind == kind
    assert "AL1021" in v.codes or "AL1021" not in log


def test_runner_that_cannot_start_is_broken(tmp_path):
    def runner(args):
        raise FileNotFoundError("al")
    assert core.compile_project(tmp_path / "p", GOOD, runner=runner).kind == core.BROKEN


def test_stale_app_never_counts_as_accept(tmp_path):
    project = tmp_path / "p"
    project.mkdir()
    (project / "test.app").write_bytes(b"left over from an earlier run")

    def runner(args):                                  # writes no .app and no diagnostics
        return subprocess.CompletedProcess(args, 1, "", "")
    assert core.compile_project(project, GOOD, runner=runner).kind == core.BROKEN

    (project / "test.app").write_bytes(b"left over again")

    def rejecting(args):
        return subprocess.CompletedProcess(args, 1, "error AL0104: x", "")
    assert core.compile_project(project, GOOD, runner=rejecting).kind == core.REJECT


def test_project_paths_are_absolute_and_app_json_has_no_dependencies(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    seen = []

    def runner(args):
        seen.append(args)
        return subprocess.CompletedProcess(args, 1, "error AL0104: x", "")
    core.compile_project(Path("rel"), GOOD, ["A"], runtime="16.0", runner=runner)
    assert Path(seen[0][2].split(":", 1)[1]).is_absolute() and Path(seen[0][3].split(":", 1)[1]).is_absolute()
    app = json.loads((tmp_path / "rel" / "app.json").read_text())
    assert app["runtime"] == "16.0" and app["preprocessorSymbols"] == ["A"]
    assert "application" not in app and "dependencies" not in app
    assert not any(a.startswith("/packagecachepath:") for a in seen[0])


# --- MISMATCH ---------------------------------------------------------------

def test_mismatch_is_a_failure_under_check(tmp_path, fake_exe):
    write(tmp_path / "cases", "c.al", "// expect: * reject\n// source: s\n" + SPLIT)
    report = tmp_path / "r.json"
    assert run(tmp_path, fake_exe, fake_al(split_sees_raw_text=True), "--check", "--json", str(report)) == 1
    rows = json.loads(report.read_text())["cases"][0]["results"]
    # S31=0: split sees the inactive BAD arm and rejects, flat accepts. S31=1: both take the BAD arm.
    assert {r["config"]: r["status"] for r in rows} == {"S31=0": "MISMATCH", "S31=1": "ok"}


def test_mismatch_does_not_fail_without_check(tmp_path, fake_exe):
    write(tmp_path / "cases", "c.al", SPLIT)
    assert run(tmp_path, fake_exe, fake_al(split_sees_raw_text=True)) == 0


def test_expected_mismatch_passes_and_a_missing_one_is_drift(tmp_path, fake_exe):
    write(tmp_path / "cases", "c.al",
          "// expect: * reject\n// expect-mismatch: !S31\n// source: s\n" + SPLIT)
    assert run(tmp_path, fake_exe, fake_al(split_sees_raw_text=True), "--check") == 0
    # every split verdict matches its expect, but split and flat now agree: the expected mismatch is gone
    write(tmp_path / "cases", "c.al",
          "// expect: * reject\n// expect: !S31 accept\n// expect-mismatch: !S31\n// source: s\n" + SPLIT)
    assert run(tmp_path, fake_exe, fake_al(), "--check") == 1


def test_verdict_drift_exits_1(tmp_path, fake_exe):
    write(tmp_path / "cases", "c.al", "// expect: * accept\n// source: s\n" + SPLIT)
    assert run(tmp_path, fake_exe, fake_al(), "--check") == 1       # S31=1 takes the BAD arm


# --- controls and a broken environment ---------------------------------------

def test_control_failure_exits_2_with_no_verdicts(tmp_path, fake_exe, capsys):
    write(tmp_path / "cases", "c.al", "// expect: * accept\n// source: s\n" + GOOD)

    def accepts_everything(args):
        if args[1] == "--version":
            return subprocess.CompletedProcess(args, 0, "1\n", "")
        Path(args[3].split(":", 1)[1]).write_bytes(b"app")
        return subprocess.CompletedProcess(args, 0, "", "")
    assert run(tmp_path, fake_exe, accepts_everything, "--check") == 2
    assert "c.al" not in capsys.readouterr().out


def test_controls_run_for_every_runtime_a_case_uses(tmp_path, fake_exe):
    write(tmp_path / "cases", "a.al", "// expect: * accept\n// source: s\n" + GOOD)
    write(tmp_path / "cases", "b.al", "// runtime: 17.0\n// expect: * accept\n// source: s\n" + GOOD)
    inner, runtimes = fake_al(), []

    def runner(args):
        if args[1] == "compile":
            app = json.loads((Path(args[2].split(":", 1)[1]) / "app.json").read_text())
            runtimes.append((app["runtime"], (Path(args[2].split(":", 1)[1]) / "Test.al").read_text()))
        return inner(args)
    assert run(tmp_path, fake_exe, runner, "--check") == 0
    controls = sorted(rt for rt, src in runtimes if src in (core.VALID_CONTROL, core.GARBAGE_CONTROL))
    assert controls == ["15.0", "15.0", "17.0", "17.0"]
    assert sorted(rt for rt, src in runtimes if "// source" in src) == ["15.0", "15.0", "17.0", "17.0"]


def test_a_broken_case_compile_exits_2_with_no_verdicts(tmp_path, fake_exe, capsys):
    write(tmp_path / "cases", "c.al", "// expect: * reject\n// source: s\nEMPTYLOG\n")
    inner = fake_al()

    def runner(args):
        if args[1] == "compile" and "EMPTYLOG" in (Path(args[2].split(":", 1)[1]) / "Test.al").read_text():
            return subprocess.CompletedProcess(args, 1, "", "")
        return inner(args)
    assert run(tmp_path, fake_exe, runner, "--check") == 2
    out = capsys.readouterr()
    assert "BROKEN" in out.err and "reject" not in out.out


def test_no_cases_found_exits_2(tmp_path, fake_exe):
    (tmp_path / "cases").mkdir()
    assert run(tmp_path, fake_exe, fake_al()) == 2


def test_missing_compiler_exits_2(tmp_path):
    write(tmp_path / "cases", "c.al", GOOD)
    assert main(["run", str(tmp_path / "cases")], runner=fake_al(), al="no-such-al-compiler-xyz") == 2


def test_identity_is_recorded(tmp_path, fake_exe):
    write(tmp_path / "cases", "c.al", "// expect: * accept\n// source: s\n" + GOOD)
    report = tmp_path / "r.json"
    assert run(tmp_path, fake_exe, fake_al(), "--check", "--json", str(report)) == 0
    data = json.loads(report.read_text())
    import hashlib
    assert data["compiler"] == {"version": "9.9.9-fake", "path": str(Path(fake_exe).resolve()),
                                "sha256": hashlib.sha256(b"not really al").hexdigest()}
    assert data["exit"] == 0 and data["cases"][0]["source"] == ["s"]


def test_committed_cases_all_parse_under_check():
    files = sorted(CASES.rglob("*.al"))
    assert len(files) >= 40
    for f in files:
        parse_case(f, f.name, f.read_text(encoding="utf-8"), check=True)


# --- real alc ---------------------------------------------------------------

needs_al = pytest.mark.skipif(shutil.which("al") is None, reason="al compiler not on PATH")


@pytest.mark.slow
@needs_al
def test_committed_cases_reproduce_their_recorded_verdicts():
    assert main(["run", str(CASES), "--check"]) == 0


@pytest.mark.slow
@needs_al
@pytest.mark.parametrize("app_extra", [
    {"runtime": "19.0"},      # AL1043: not supported by alc 18.0.41
    {"runtime": "abc"},       # AL1039
    {"id": "not-a-guid"},     # AL1040, AL1053
])
def test_broken_project_is_broken_not_a_rejection(tmp_path, app_extra):
    for name, src in (("valid", core.VALID_CONTROL), ("garbage", core.GARBAGE_CONTROL)):
        v = core.compile_project(tmp_path / name, src, app_extra=app_extra)
        assert v.kind == core.BROKEN, (name, v)


@pytest.mark.slow
@needs_al
def test_unsupported_runtime_case_exits_2(tmp_path, capsys):
    """A case on a runtime alc cannot build: its controls come back BROKEN and no verdict is given."""
    write(tmp_path / "cases", "c.al", "// runtime: 19.0\n// expect: * reject\n// source: s\n" + GOOD)
    assert main(["run", str(tmp_path / "cases"), "--check"]) == 2
    out = capsys.readouterr().out
    assert "FAIL control runtime=19.0 expect=ACCEPT got=BROKEN" in out
    assert "c.al" not in out
