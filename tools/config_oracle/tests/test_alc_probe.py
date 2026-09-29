"""tools/alc_probe: the shared alc compile core and the split/flat matrix runner.

Fast tests fake `al` through the injected runner, printing diagnostic lines in the
exact shapes alc 18.0.41 prints. The `slow` tests need the real compiler and skip
where `al` is not on PATH (it is not in CI).
"""
import hashlib
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

# Diagnostic lines captured from alc 18.0.41 on 2026-09-29 (the paths shortened).
L_AL1021 = "error AL1021: The package cache path has not been specified."
L_AL0104 = r"C:\t\k00001\Test.al(5,23): error AL0104: Syntax error, 'end' expected"
L_AL0198 = (r"C:\t\k00001\Test.al(5,24): error AL0198: Expected one of the application object keywords "
            "(table, tableextension, page, pageextension, pagecustomization, profile, profileextension, codeunit, "
            "report, reportextension, xmlport, query, controladdin, dotnet, enum, enumextension, interface, "
            "permissionset, permissionsetextension, entitlement)")
L_AL1073 = r"C:\t\al1073\Test.al(7,15): error AL1073: The procedure with name OnRun has the same name as a declared trigger."
L_AL1043 = r"C:\t\rt19\app.json(1,175): error AL1043: The runtime version '19.0' is not supported by the AL compiler."
L_AL1040 = (r"C:\t\badjson\app.json(1,2): error AL1040: The guid number 'nope' does not match the expected pattern: "
            '"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$".')
L_AL1053 = (r"C:\t\badjson\app.json(1,2): error AL1053: The value '00000000-0000-0000-0000-000000000000' "
            "is not valid for the manifest property 'id'.")
L_AL1028 = (r"error AL1028: An IO exception has happened when trying to write to output file 'C:\t\true_literal\test.app' "
            r"-- 'The process cannot access the file 'C:\t\true_literal\test.app' because it is being used by another process.'.")
L_AL1001 = r"error AL1001: Source file 'C:\t\noappjson\app.json' could not be found"
L_REL = r"bad\T.al(10,27): error AL0104: Syntax error, ';' expected"
HEAD = "Microsoft (R) AL Compiler version 18.0.41.62505\nCopyright (C) Microsoft Corporation. All rights reserved\n\n"


def fake_al(split_sees_raw_text=False):
    """A fake `al`: rejects any source whose ACTIVE text contains GARBAGE or BAD (AL0104)
    or OTHER (AL0198), with alc's real line shapes.

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
        log = HEAD + L_AL1021 + "\n"
        errors = ([L_AL0104] if "GARBAGE" in text or "BAD" in text else []) + ([L_AL0198] if "OTHER" in text else [])
        if errors:
            return subprocess.CompletedProcess(args, 1, log + "\n".join(errors) + "\n", "")
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


def compiles(runner):
    return [c for c in runner.calls if c[1] == "compile"]


# --- header parsing ---------------------------------------------------------

SPLIT = "#if not S31\nMessage('a');\n#else\nBAD\n#endif\n"


def test_header_fields_and_last_matching_expect_wins():
    text = ("// Valid only with S31 undefined.\n// expect: * accept\n// expect: S31 reject(AL0198,AL0104)\n"
            "// runtime: 17.0\n// source: somewhere, commit abc\n// expect-mismatch: S31\n") + SPLIT
    c = parse_case(Path("x.al"), "x.al", text, check=True)
    assert c.runtimes == ("17.0",) and c.sources == ["somewhere, commit abc"]
    assert c.symbols == ("S31",)
    assert str(c.expected(frozenset())) == "accept"
    assert c.expected(frozenset({"S31"})).codes == ("AL0104", "AL0198")     # sorted
    assert c.mismatch_expected(frozenset({"S31"})) and not c.mismatch_expected(frozenset())


def test_runtime_list():
    c = parse_case(Path("x.al"), "x.al", "// runtime: 15.0 17.0, 18.0\n" + GOOD, check=False)
    assert c.runtimes == ("15.0", "17.0", "18.0")


def test_negated_literal_and_conjunction():
    text = ("// expect: !A accept\n// expect: A !B reject(AL0104)\n// expect: A B accept\n// source: s\n"
            "#if A\n#if B\nx\n#endif\n#endif\n")
    c = parse_case(Path("x.al"), "x.al", text, check=True)
    got = {tuple(sorted(e)): str(c.expected(e)) for e in c.envs}
    assert got == {(): "accept", ("B",): "accept", ("A",): "reject(AL0104)", ("A", "B"): "accept"}


@pytest.mark.parametrize("header, why", [
    ("// expect: * maybe\n// source: s\n", "verdict word"),
    ("// expect: * reject\n// source: s\n", "reject without its codes"),
    ("// expect: * reject()\n// source: s\n", "empty code list"),
    ("// expect: * reject(AL01)\n// source: s\n", "short code"),
    ("// expect: * reject(AL0104, AL0198)\n// source: s\n", "space inside the list"),
    ("// expect: * reject(AL0104,AL0104)\n// source: s\n", "duplicate code"),
    ("// expect: * accept(AL0104)\n// source: s\n", "codes on an accept"),
    ("// expect: accept\n// source: s\n", "no assignment"),
    ("// expect: NOPE accept\n// source: s\n", "symbol not in the conditions"),
    ("// expect: A-B accept\n// source: s\n", "not a literal"),
    ("// expected: * accept\n// source: s\n", "misspelt key"),
    ("// runtime: fifteen\n// expect: * accept\n// source: s\n", "bad runtime"),
    ("// runtime: 15.0 15.0\n// expect: * accept\n// source: s\n", "duplicate runtime"),
    ("// expect: A accept\n// source: s\n", "!A not covered under --check"),
    ("// expect: * accept\n", "no source under --check"),
    ("// expect: * accept\n// source:\n", "empty source"),
])
def test_malformed_header_exits_2(tmp_path, fake_exe, header, why):
    write(tmp_path / "cases", "c.al", header + "#if A\nMessage('a');\n#endif\n")
    runner = fake_al()
    assert run(tmp_path, fake_exe, runner, "--check") == 2, why
    assert not compiles(runner), "nothing may compile when a header is malformed"


def test_unresolvable_directives_exit_2(tmp_path, fake_exe):
    write(tmp_path / "cases", "c.al", "// expect: * accept\n// source: s\n#if A\nx\n")
    assert run(tmp_path, fake_exe, fake_al(), "--check") == 2


def test_without_check_expect_and_source_are_optional(tmp_path, fake_exe):
    write(tmp_path / "cases", "c.al", "#if A\nMessage('a');\n#endif\n")
    assert run(tmp_path, fake_exe, fake_al()) == 0


# --- case discovery and identity --------------------------------------------

def test_same_file_name_in_two_directories_are_two_cases(tmp_path, fake_exe, capsys):
    write(tmp_path / "a", "x.al", "// expect: * accept\n// source: s\nBAD\n")      # fails its expect
    write(tmp_path / "b", "x.al", "// expect: * accept\n// source: s\n" + GOOD)    # passes
    assert main(["run", str(tmp_path / "a"), str(tmp_path / "b"), "--check"], runner=fake_al(), al=fake_exe) == 1
    out = capsys.readouterr().out
    assert "DIFF     a/x.al" in out and "ok       b/x.al" in out


def test_the_same_case_named_twice_exits_2(tmp_path, fake_exe):
    write(tmp_path / "cases", "c.al", "// expect: * accept\n// source: s\n" + GOOD)
    assert main(["run", str(tmp_path / "cases"), str(tmp_path / "cases" / "c.al")],
                runner=fake_al(), al=fake_exe) == 2


def test_a_path_that_does_not_exist_exits_2(tmp_path, fake_exe):
    write(tmp_path / "cases", "c.al", "// expect: * accept\n// source: s\n" + GOOD)
    assert main(["run", str(tmp_path / "cases"), str(tmp_path / "casez"), "--check"],
                runner=fake_al(), al=fake_exe) == 2


def test_no_cases_found_exits_2(tmp_path, fake_exe):
    (tmp_path / "cases").mkdir()
    assert run(tmp_path, fake_exe, fake_al()) == 2


# --- symbol discovery and the matrix ----------------------------------------

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
    assert len(compiles(runner)) == 2 + 2   # two controls + split + flat


def test_every_assignment_compiled_split_with_symbols_and_flat_without(tmp_path, fake_exe):
    write(tmp_path / "cases", "c.al", "// expect: * accept\n// source: s\n#if A\nx\n#elif B\ny\n#endif\n")
    runner = fake_al()
    assert run(tmp_path, fake_exe, runner, "--check") == 0
    projects = [Path(c[2].split(":", 1)[1]) for c in compiles(runner)][2:]
    assert len(projects) == 8
    assert len(set(projects)) == 8, "each compile needs its own directory"


def test_every_assignment_runs_once_per_runtime(tmp_path, fake_exe):
    write(tmp_path / "cases", "c.al",
          "// runtime: 15.0 17.0 18.0\n// expect: * accept\n// source: s\n#if A\nx\n#endif\n")
    inner, seen = fake_al(), []

    def runner(args):
        if args[1] == "compile":
            project = Path(args[2].split(":", 1)[1])
            app = json.loads((project / "app.json").read_text())
            seen.append((app["runtime"], "// source" in (project / "Test.al").read_text(),
                         tuple(app["preprocessorSymbols"])))
        return inner(args)
    report = tmp_path / "r.json"
    assert run(tmp_path, fake_exe, runner, "--check", "--json", str(report)) == 0
    case_compiles = sorted(s for s in seen if s[1])
    assert len(case_compiles) == 2 * 2 * 3                       # 2 assignments x split/flat x 3 runtimes
    assert sorted({rt for rt, _, _ in case_compiles}) == ["15.0", "17.0", "18.0"]
    assert sorted(rt for rt, is_case, _ in seen if not is_case) == ["15.0", "15.0", "17.0", "17.0", "18.0", "18.0"]
    rows = json.loads(report.read_text())["cases"][0]["results"]
    assert sorted((r["config"], r["runtime"]) for r in rows) == sorted(
        (c, rt) for c in ("A=0", "A=1") for rt in ("15.0", "17.0", "18.0"))


# --- classification -----------------------------------------------------------

@pytest.mark.parametrize("app, lines, kind, source", [
    (True, [L_AL1021], core.ACCEPT, ()),
    (True, [], core.ACCEPT, ()),
    (True, [L_AL1021, L_AL1028], core.ACCEPT, ()),               # the IO clash, with an .app from the other compile
    (False, [L_AL1021, L_AL0104, L_AL0198], core.REJECT, ("AL0104", "AL0198")),
    (False, [L_REL], core.REJECT, ("AL0104",)),                  # a relative source path
    (False, [L_AL1021, L_AL1073], core.REJECT, ("AL1073",)),     # an AL1xxx code located in a .al file
    (False, [L_AL1021], core.BROKEN, ()),                        # unlocated only
    (False, [], core.BROKEN, ()),                                # nothing at all
    (False, [L_AL1043], core.BROKEN, ()),                        # located in app.json
    (False, [L_AL1040, L_AL1053], core.BROKEN, ()),
    (False, [L_AL1021, L_AL1028], core.BROKEN, ()),              # unlocated IO failure
    (False, [L_AL1001], core.BROKEN, ()),
    (False, [L_AL1043, L_AL0104], core.REJECT, ("AL0104",)),
])
def test_classify_by_location(app, lines, kind, source):
    v = core.classify(app, HEAD + "\n".join(lines) + "\n")
    assert (v.kind, v.source_codes) == (kind, source)
    assert set(v.source_codes) <= set(v.codes)


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
        return subprocess.CompletedProcess(args, 1, L_AL0104, "")
    assert core.compile_project(project, GOOD, runner=rejecting).kind == core.REJECT


def test_project_paths_are_absolute_and_app_json_has_no_dependencies(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    seen = []

    def runner(args):
        seen.append(args)
        return subprocess.CompletedProcess(args, 1, L_AL0104, "")
    core.compile_project(Path("rel"), GOOD, ["A"], runtime="16.0", runner=runner)
    assert Path(seen[0][2].split(":", 1)[1]).is_absolute() and Path(seen[0][3].split(":", 1)[1]).is_absolute()
    app = json.loads((tmp_path / "rel" / "app.json").read_text())
    assert app["runtime"] == "16.0" and app["preprocessorSymbols"] == ["A"]
    assert "application" not in app and "dependencies" not in app
    assert not any(a.startswith("/packagecachepath:") for a in seen[0])


# --- MISMATCH ---------------------------------------------------------------

def test_mismatch_is_a_failure_under_check(tmp_path, fake_exe):
    write(tmp_path / "cases", "c.al", "// expect: * reject(AL0104)\n// source: s\n" + SPLIT)
    report = tmp_path / "r.json"
    assert run(tmp_path, fake_exe, fake_al(split_sees_raw_text=True), "--check", "--json", str(report)) == 1
    rows = json.loads(report.read_text())["cases"][0]["results"]
    # S31=0: split sees the inactive BAD arm and rejects, flat accepts. S31=1: both take the BAD arm.
    assert {r["config"]: r["status"] for r in rows} == {"S31=0": "MISMATCH", "S31=1": "ok"}


def test_mismatch_fails_without_check_too(tmp_path, fake_exe):
    write(tmp_path / "cases", "c.al", SPLIT)
    assert run(tmp_path, fake_exe, fake_al(split_sees_raw_text=True)) == 1


def test_two_rejections_with_different_codes_are_a_mismatch(tmp_path, fake_exe):
    # split sees both arms (AL0104 + AL0198); flat sees only the active BAD arm (AL0104)
    write(tmp_path / "cases", "c.al", "#if A\nBAD\n#else\nOTHER BAD\n#endif\n")
    report = tmp_path / "r.json"
    assert run(tmp_path, fake_exe, fake_al(split_sees_raw_text=True), "--json", str(report)) == 1
    rows = json.loads(report.read_text())["cases"][0]["results"]
    assert all(r["split"]["verdict"] == r["flat"]["verdict"] == "REJECT" for r in rows)
    assert [r["status"] for r in rows] == ["ok", "MISMATCH"]     # A=0: flat takes the OTHER BAD arm too


def test_expected_mismatch_passes_and_a_missing_one_is_drift(tmp_path, fake_exe):
    write(tmp_path / "cases", "c.al",
          "// expect: * reject(AL0104)\n// expect-mismatch: !S31\n// source: s\n" + SPLIT)
    assert run(tmp_path, fake_exe, fake_al(split_sees_raw_text=True), "--check") == 0
    # every split verdict matches its expect, but split and flat now agree: the expected mismatch is gone
    write(tmp_path / "cases", "c.al",
          "// expect: * reject(AL0104)\n// expect: !S31 accept\n// expect-mismatch: !S31\n// source: s\n" + SPLIT)
    assert run(tmp_path, fake_exe, fake_al(), "--check") == 1


def test_verdict_drift_exits_1(tmp_path, fake_exe):
    write(tmp_path / "cases", "c.al", "// expect: * accept\n// source: s\n" + SPLIT)
    assert run(tmp_path, fake_exe, fake_al(), "--check") == 1       # S31=1 takes the BAD arm


def test_rejection_code_drift_exits_1(tmp_path, fake_exe):
    body = "// expect: * reject(AL0104)\n// source: s\n"
    write(tmp_path / "cases", "c.al", body + "BAD\n")
    assert run(tmp_path, fake_exe, fake_al(), "--check") == 0
    write(tmp_path / "cases", "c.al", body + "BAD OTHER\n")         # rejects, but also for another reason
    assert run(tmp_path, fake_exe, fake_al(), "--check") == 1


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
    write(tmp_path / "cases", "c.al", "// expect: * reject(AL0104)\n// source: s\nAPPJSON\n")
    inner = fake_al()

    def runner(args):
        if args[1] == "compile" and "APPJSON" in (Path(args[2].split(":", 1)[1]) / "Test.al").read_text():
            return subprocess.CompletedProcess(args, 1, HEAD + L_AL1043 + "\n", "")
        return inner(args)
    assert run(tmp_path, fake_exe, runner, "--check") == 2
    out = capsys.readouterr()
    assert "BROKEN" in out.err and "AL1043" in out.err and "reject" not in out.out


def test_a_crash_exits_2_not_1(tmp_path, fake_exe):
    write(tmp_path / "cases", "c.al", "// expect: * accept\n// source: s\n" + GOOD)
    inner = fake_al()

    def runner(args):
        if args[1] == "compile" and "// source" in (Path(args[2].split(":", 1)[1]) / "Test.al").read_text():
            raise RuntimeError("boom")
        return inner(args)
    assert run(tmp_path, fake_exe, runner, "--check") == 2


def test_missing_compiler_exits_2(tmp_path):
    write(tmp_path / "cases", "c.al", GOOD)
    assert main(["run", str(tmp_path / "cases")], runner=fake_al(), al="no-such-al-compiler-xyz") == 2


def test_identity_is_recorded_and_used_for_the_compiles(tmp_path, fake_exe):
    write(tmp_path / "cases", "c.al", "// expect: * accept\n// source: s\n" + GOOD)
    report = tmp_path / "r.json"
    runner = fake_al()
    assert run(tmp_path, fake_exe, runner, "--check", "--json", str(report)) == 0
    data = json.loads(report.read_text())
    resolved = str(Path(fake_exe).resolve())
    assert data["compiler"] == {"version": "9.9.9-fake", "path": resolved,
                                "launcher_sha256": hashlib.sha256(b"not really al").hexdigest(),
                                "code_analysis": []}
    assert {c[0] for c in runner.calls} == {resolved}
    assert data["exit"] == 0 and data["cases"][0]["source"] == ["s"]


def test_code_analysis_dll_is_hashed(tmp_path):
    exe = tmp_path / "al.exe"
    exe.write_bytes(b"shim")
    dll = tmp_path / ".store" / "pkg" / "1.2.3" / "pkg" / "1.2.3" / "tools" / "net8.0" / "any" / \
        "Microsoft.Dynamics.Nav.CodeAnalysis.dll"
    dll.parent.mkdir(parents=True)
    dll.write_bytes(b"compiler")
    ident = core.compiler_identity(str(exe), lambda a: subprocess.CompletedProcess(a, 0, "1.2.3+abc\n", ""))
    assert ident.code_analysis == ((str(dll), hashlib.sha256(b"compiler").hexdigest()),)


def test_committed_cases_all_parse_under_check():
    files = sorted(CASES.rglob("*.al"))
    assert len(files) >= 50
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
def test_al1073_name_clash_is_a_rejection(tmp_path):
    src = "codeunit 50100 P\n{\n    trigger OnRun()\n    begin\n    end;\n\n    procedure OnRun()\n    begin\n    end;\n}\n"
    v = core.compile_project(tmp_path / "p", src)
    assert (v.kind, v.source_codes) == (core.REJECT, ("AL1073",))


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
    write(tmp_path / "cases", "c.al", "// runtime: 19.0\n// expect: * reject(AL0104)\n// source: s\n" + GOOD)
    assert main(["run", str(tmp_path / "cases"), "--check"]) == 2
    out = capsys.readouterr().out
    assert "FAIL control runtime=19.0 expect=ACCEPT got=BROKEN(AL1043)" in out
    assert "c.al" not in out
