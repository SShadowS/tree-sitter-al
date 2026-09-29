"""The ONE implementation of "compile an AL project with alc and judge the result".

Used by `tools.alc_probe` (the split/flat matrix runner) and by
`tools.config_oracle.probe_alc` (the directive-semantics probes).

A verdict is judged from whether the `.app` was written, never from the log alone:
AL1021 ("package cache path has not been specified") appears in the log of
successful runs too, and a broken project (bad runtime, symbol packages missing)
exits 1 with no diagnostics at all -- which must not be read as a syntax rejection.
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


def is_project_code(code: str) -> bool:
    """AL1xxx is the project/manifest/package range, not the source text.

    AL1021 is printed on every run without /packagecachepath:, successful ones
    included. The rest of the range is how alc 18.0.41 reports a BROKEN project,
    measured 2026-09-29: AL1001 (project or app.json not found), AL1017 (app.json
    not JSON), AL1022 (empty package cache), AL1039 (bad runtime string), AL1040 and
    AL1053 (bad manifest id), AL1043 (unsupported runtime, e.g. 19.0). Counting
    those as a syntax REJECT is exactly the confusion this module exists to prevent.
    """
    return re.fullmatch(r"AL1\d{3}", code) is not None


GARBAGE = "GARBAGE!! ;;; }{"
VALID_CONTROL = "codeunit 50100 Probe\n{\n    trigger OnRun()\n    begin\n        Message('x');\n    end;\n}\n"
GARBAGE_CONTROL = f"codeunit 50100 Probe\n{{\n    trigger OnRun()\n    begin\n        {GARBAGE}\n    end;\n}}\n"


def default_runner(args: Sequence[str]) -> subprocess.CompletedProcess:
    return subprocess.run(list(args), capture_output=True, text=True)


@dataclass(frozen=True)
class Verdict:
    kind: str                      # ACCEPT | REJECT | BROKEN
    codes: tuple = ()              # every `error ALxxxx` code in the log, AL1xxx included
    detail: str = ""               # why BROKEN, when it is

    @property
    def syntax_codes(self) -> tuple:
        return tuple(c for c in self.codes if not is_project_code(c))


def app_json(symbols: Sequence[str], runtime: str = DEFAULT_RUNTIME) -> dict:
    # No `application`/`dependencies`: they pull in symbol packages that are not
    # present locally, and the project then fails with no diagnostics at all.
    return {
        "id": "11111111-2222-3333-4444-555555555555", "name": "Probe", "publisher": "Test",
        "version": "1.0.0.0", "platform": "1.0.0.0", "idRanges": [{"from": 50000, "to": 99999}],
        "runtime": runtime, "target": "OnPrem", "preprocessorSymbols": list(symbols),
    }


def classify(app_written: bool, log: str) -> Verdict:
    codes = tuple(sorted(set(re.findall(r"error (AL\d+)", log))))
    if app_written:
        return Verdict(ACCEPT, codes)
    if any(not is_project_code(c) for c in codes):
        return Verdict(REJECT, codes)
    return Verdict(BROKEN, codes, "no .app and no source diagnostic (only project-level AL1xxx codes, or none)")


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
        return Verdict(BROKEN, (), f"could not run al: {e}")
    return classify(out.is_file(), (result.stdout or "") + (result.stderr or ""))


@dataclass(frozen=True)
class Identity:
    version: str
    path: str
    sha256: str
    error: str = ""

    def as_dict(self) -> dict:
        return {"version": self.version, "path": self.path, "sha256": self.sha256, **({"error": self.error} if self.error else {})}


def compiler_identity(al: str = "al", runner: Runner = default_runner) -> Identity:
    """`al --version`, the resolved executable and its sha256. `error` is set when `al` cannot be run."""
    resolved = str(Path(al).resolve()) if Path(al).is_file() else shutil.which(al)
    if not resolved:
        return Identity("", "", "", f"{al!r} not found on PATH")
    digest = hashlib.sha256(Path(resolved).read_bytes()).hexdigest()
    try:
        r = runner([al, "--version"])
    except OSError as e:
        return Identity("", resolved, digest, f"could not run al: {e}")
    version = (r.stdout or "").strip()
    if r.returncode != 0 or not version:
        return Identity(version, resolved, digest, f"`al --version` exited {r.returncode}")
    return Identity(version, resolved, digest)
