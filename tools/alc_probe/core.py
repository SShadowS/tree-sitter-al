"""The shared implementation of "compile an AL project with alc and judge the result".

Used by `tools.alc_probe` (the split/flat matrix runner) and by
`tools.config_oracle.probe_alc` (the directive-semantics probes).
`tools/precedence/probe.sh` is still a separate bash path (docs/deferred-work.md item 7).

A verdict is judged from whether the `.app` was written, and a rejection from WHERE
the errors are located: only an error located in a `.al` file is about the source.
AL1021 ("package cache path has not been specified") appears, unlocated, in the log
of successful runs too, and a broken project reports errors located in app.json
(AL1043, AL1040, ...) or unlocated (AL1001, AL1028, ...). Neither is a rejection.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

Runner = Callable[[Sequence[str]], subprocess.CompletedProcess]

ACCEPT, REJECT, BROKEN = "ACCEPT", "REJECT", "BROKEN"
DEFAULT_RUNTIME = "15.0"


# One diagnostic line as alc 18.0.41 prints it. The location prefix is optional:
#   C:\...\Test.al(7,15): error AL1073: The procedure with name OnRun ...
#   C:\...\app.json(1,175): error AL1043: The runtime version '19.0' is not supported ...
#   error AL1021: The package cache path has not been specified.
_DIAG = re.compile(r"^\s*(?:(?P<file>.+?)\((?P<line>\d+),(?P<col>\d+)\)\s*:\s*)?error (?P<code>AL\d+)", re.M)


GARBAGE = "GARBAGE!! ;;; }{"
VALID_CONTROL = "codeunit 50100 Probe\n{\n    trigger OnRun()\n    begin\n        Message('x');\n    end;\n}\n"
GARBAGE_CONTROL = f"codeunit 50100 Probe\n{{\n    trigger OnRun()\n    begin\n        {GARBAGE}\n    end;\n}}\n"


def default_runner(args: Sequence[str]) -> subprocess.CompletedProcess:
    return subprocess.run(list(args), capture_output=True, text=True)


@dataclass(frozen=True)
class Verdict:
    kind: str                      # ACCEPT | REJECT | BROKEN
    codes: tuple = ()              # every `error ALxxxx` code in the log, wherever located
    source_codes: tuple = ()       # the codes of errors located in a .al file
    detail: str = ""               # why BROKEN, when it is


def app_json(symbols: Sequence[str], runtime: str = DEFAULT_RUNTIME) -> dict:
    # No `application`/`dependencies`. alc 18.0.41 accepts them for a self-contained
    # probe, but a reference to a Base/System object without the symbol packages
    # then fails with a .al-located AL0185, which reads as a genuine REJECT.
    return {
        "id": "11111111-2222-3333-4444-555555555555", "name": "Probe", "publisher": "Test",
        "version": "1.0.0.0", "platform": "1.0.0.0", "idRanges": [{"from": 50000, "to": 99999}],
        "runtime": runtime, "target": "OnPrem", "preprocessorSymbols": list(symbols),
    }


def classify(app_written: bool, log: str) -> Verdict:
    diags = [(m.group("file"), m.group("code")) for m in _DIAG.finditer(log)]
    codes = tuple(sorted({c for _, c in diags}))
    source = tuple(sorted({c for f, c in diags if f and f.strip().lower().endswith(".al")}))
    if app_written:
        return Verdict(ACCEPT, codes, source)
    if source:
        return Verdict(REJECT, codes, source)
    return Verdict(BROKEN, codes, (), "no .app and no error located in a .al file")


def compile_project(project: Path, source: str, symbols: Sequence[str] = (), *,
                    runtime: str = DEFAULT_RUNTIME, packagecachepath: str | None = None,
                    app_extra: dict | None = None, al: str = "al",
                    runner: Runner = default_runner) -> Verdict:
    """Compile `source` as the only file of a fresh project at `project`.

    The directory is deleted and recreated, and the output `.app` is removed
    before the compile, so an `.app` left by an earlier run can never count.
    `app_extra` merges keys into app.json (tests use it to build a broken project).
    """
    project = Path(project).resolve()           # alc exits 1 silently on relative paths
    shutil.rmtree(project, ignore_errors=True)
    project.mkdir(parents=True)
    (project / "Test.al").write_text(source, encoding="utf-8", newline="\n")
    (project / "app.json").write_text(json.dumps({**app_json(symbols, runtime), **(app_extra or {})}),
                                      encoding="utf-8")
    out = project / "test.app"
    out.unlink(missing_ok=True)
    args = [al, "compile", f"/project:{project}", f"/out:{out}"]
    if packagecachepath:
        args.append(f"/packagecachepath:{Path(packagecachepath).resolve()}")
    try:
        result = runner(args)
    except OSError as e:
        return Verdict(BROKEN, (), (), f"could not run al: {e}")
    return classify(out.is_file(), (result.stdout or "") + (result.stderr or ""))


@dataclass(frozen=True)
class Identity:
    version: str
    path: str                     # the resolved executable; compiles run exactly this
    launcher_sha256: str          # a dotnet tool's al.exe is a small apphost shim
    code_analysis: tuple = ()     # (path, sha256) of every Microsoft.Dynamics.Nav.CodeAnalysis.dll of that version
    error: str = ""

    def as_dict(self) -> dict:
        return {"version": self.version, "path": self.path, "launcher_sha256": self.launcher_sha256,
                "code_analysis": [{"path": p, "sha256": h} for p, h in self.code_analysis],
                **({"error": self.error} if self.error else {})}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _code_analysis(resolved: Path, version: str) -> tuple:
    """The compiler proper. A dotnet global tool keeps it under <tools>/.store/<pkg>/<version>/."""
    ver = version.split("+")[0]
    found = sorted(resolved.parent.glob(f".store/*/{ver}/**/Microsoft.Dynamics.Nav.CodeAnalysis.dll"))
    found = found or sorted(resolved.parent.glob("Microsoft.Dynamics.Nav.CodeAnalysis.dll"))
    return tuple((str(p), _sha256(p)) for p in found)


def compiler_identity(al: str = "al", runner: Runner = default_runner) -> Identity:
    """`al --version`, the resolved executable and the hashes of what it runs.

    `error` is set when `al` cannot be run. Callers compile with `Identity.path`, so
    the identity and the compiles cannot resolve `al` to two different executables.
    """
    resolved = str(Path(al).resolve()) if Path(al).is_file() else shutil.which(al)
    if not resolved:
        return Identity("", "", "", (), f"{al!r} not found on PATH")
    digest = _sha256(Path(resolved))
    try:
        r = runner([resolved, "--version"])
    except OSError as e:
        return Identity("", resolved, digest, (), f"could not run al: {e}")
    version = (r.stdout or "").strip()
    if r.returncode != 0 or not version:
        return Identity(version, resolved, digest, (), f"`al --version` exited {r.returncode}")
    return Identity(version, resolved, digest, _code_analysis(Path(resolved), version))
