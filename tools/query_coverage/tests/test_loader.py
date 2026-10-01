import hashlib
import subprocess
from pathlib import Path

import pytest

from tools.query_coverage import loader


def _stampable(root: Path) -> None:
    """Write every file compute_stamp hashes, each with its own contents."""
    (root / "src").mkdir(exist_ok=True)
    for relative in loader.STAMPED_FILES:
        (root / relative).write_bytes(relative.name.encode("utf-8"))


def test_compute_stamp_is_sha256_of_every_stamped_file_in_order(tmp_path: Path):
    _stampable(tmp_path)

    expected = hashlib.sha256(
        b"".join(relative.name.encode("utf-8") for relative in loader.STAMPED_FILES)
    ).hexdigest()

    assert loader.compute_stamp(tmp_path) == expected


@pytest.mark.parametrize("relative", loader.STAMPED_FILES, ids=lambda p: p.name)
def test_compute_stamp_changes_when_any_stamped_file_changes(tmp_path: Path, relative: Path):
    """Every one of them, not just the two hand-written sources.

    src/node-types.json and src/grammar.json are read DIRECTLY by detectors 3
    and 7. While the stamp covered only grammar.js and src/scanner.c, a stale
    or hand-edited generated artifact passed the freshness check silently and
    the run reported findings derived from it.
    """
    _stampable(tmp_path)
    first = loader.compute_stamp(tmp_path)

    (tmp_path / relative).write_bytes(b"changed")

    assert loader.compute_stamp(tmp_path) != first


def test_stamp_roundtrip(tmp_path: Path):
    assert loader.read_stamp(tmp_path) is None

    loader.write_stamp(tmp_path, "deadbeef")

    assert loader.read_stamp(tmp_path) == "deadbeef"


def test_ensure_library_runs_generate_before_build_when_stamp_differs(
    tmp_path: Path, monkeypatch
):
    """`tree-sitter build` does not regenerate src/parser.c from grammar.js
    (verified directly against an isolated scratch grammar under tree-sitter
    0.26.12: editing grammar.js and running `build` left the compiled
    grammar.json unchanged). Skipping `generate` here recompiles the stale
    parser.c and then stamps it with the NEW grammar.js hash anyway, so every
    later run believes the parser is current when it never was. Mocked, not a
    real build -- a real `tree-sitter generate` + `build` here would make this
    test take minutes.
    """
    _stampable(tmp_path)

    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(loader.subprocess, "run", fake_run)

    lib_path = loader.ensure_library(tmp_path)

    assert lib_path == tmp_path / loader.LIB_NAME
    assert len(calls) == 2
    assert calls[0][:2] == ["tree-sitter", "generate"]
    assert calls[1][:2] == ["tree-sitter", "build"]
    # generate must run BEFORE build reads the sources it regenerates from.
    assert calls.index(calls[0]) < calls.index(calls[1])
    assert loader.read_stamp(tmp_path) == loader.library_stamp(tmp_path)


def test_ensure_library_raises_and_leaves_stamp_unwritten_when_generate_fails(
    tmp_path: Path, monkeypatch
):
    """A `generate` failure must surface as StaleParserError -- the same
    exception a `build` failure raises -- and must not reach `build` at all,
    since building against sources `generate` just rejected would only
    compile something equally suspect.
    """
    _stampable(tmp_path)

    def fake_run(cmd, **kwargs):
        assert cmd[:2] == ["tree-sitter", "generate"], "build must not run when generate failed"
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="boom")

    monkeypatch.setattr(loader.subprocess, "run", fake_run)

    with pytest.raises(loader.StaleParserError, match="generate failed"):
        loader.ensure_library(tmp_path)

    assert loader.read_stamp(tmp_path) is None


def test_ensure_library_stamps_the_post_generate_state(tmp_path: Path, monkeypatch):
    """The stamp must record what `generate` LEFT on disk, not what preceded it.

    The stamp covers the generated artifacts, so `generate` rewriting them is
    the normal case, not the exception. Stamping the pre-generate hashes would
    record a state that no longer exists, and the very next run would see a
    mismatch and regenerate + rebuild — every single time, forever.
    """
    _stampable(tmp_path)
    pre_generate = loader.library_stamp(tmp_path)

    def fake_run(cmd, **kwargs):
        if cmd[:2] == ["tree-sitter", "generate"]:
            # What a real `generate` does: rewrite the generated artifacts.
            (tmp_path / "src" / "node-types.json").write_bytes(b"regenerated")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(loader.subprocess, "run", fake_run)

    loader.ensure_library(tmp_path)

    assert loader.read_stamp(tmp_path) != pre_generate
    assert loader.read_stamp(tmp_path) == loader.library_stamp(tmp_path)

    # ...and a second call is therefore a no-op rather than another rebuild.
    calls: list[list[str]] = []
    monkeypatch.setattr(
        loader.subprocess,
        "run",
        lambda cmd, **kw: calls.append(cmd) or subprocess.CompletedProcess(cmd, 0, "", ""),
    )
    (tmp_path / loader.LIB_NAME).write_bytes(b"library")

    loader.ensure_library(tmp_path)

    assert calls == []


# ---- build_env: the Python twin of tools/default-cc.sh -------------------------

CLANG = r"C:\LLVM\bin\clang-cl.EXE"


def _env(environ, *, windows=True, on_path=CLANG, llvm_file=False):
    return loader.build_env(environ, is_windows=windows, which=lambda _name: on_path,
                            isfile=lambda _path: llvm_file)


def test_build_env_defaults_cc_to_clang_cl_when_unset():
    env = _env({"PATH": "x"})
    assert env["CC"] == CLANG and env["TS_AL_DEFAULT_CC"] == CLANG and env["PATH"] == "x"


def test_build_env_falls_back_to_the_llvm_install_dir():
    assert _env({}, on_path=None, llvm_file=True)["CC"] == loader.LLVM_CLANG_CL


@pytest.mark.parametrize("cc", ["cl", "gcc", CLANG])
def test_build_env_explicit_cc_wins(cc):
    assert _env({"CC": cc})["CC"] == cc


def test_build_env_opt_out():
    assert "CC" not in _env({"TS_AL_NO_CLANG": "1"})


def test_build_env_not_windows_is_a_no_op():
    assert _env({}, windows=False) == {}


def test_build_env_clang_cl_absent_changes_nothing():
    assert _env({}, on_path=None, llvm_file=False) == {}


def test_build_env_reapplies_the_rule_to_an_inherited_default():
    """ts-lock.sh exported CC=TS_AL_DEFAULT_CC; that is not an explicit CC, so the opt-out
    still applies to it."""
    inherited = {"CC": CLANG, "TS_AL_DEFAULT_CC": CLANG, "TS_AL_NO_CLANG": "1"}
    assert "CC" not in _env(inherited)


def test_build_env_never_touches_os_environ(monkeypatch):
    monkeypatch.delenv("CC", raising=False)
    loader.build_env(is_windows=True, which=lambda _name: CLANG)
    assert "CC" not in loader.os.environ


def test_library_stamp_keys_the_compiler_by_name(tmp_path: Path):
    _stampable(tmp_path)
    base = loader.compute_stamp(tmp_path)
    assert loader.library_stamp(tmp_path, {"CC": CLANG}) == f"{base} cc=clang-cl"
    assert loader.library_stamp(tmp_path, {"CC": "C:/Program Files/LLVM/bin/clang-cl.exe"}) == f"{base} cc=clang-cl"
    assert loader.library_stamp(tmp_path, {}) == f"{base} cc="


def test_ensure_library_builds_with_build_env_and_rebuilds_on_compiler_change(tmp_path: Path, monkeypatch):
    _stampable(tmp_path)
    envs = []

    def fake_run(cmd, **kwargs):
        if cmd[:2] == ["tree-sitter", "build"]:
            envs.append(kwargs.get("env"))
            (tmp_path / loader.LIB_NAME).write_bytes(b"library")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(loader.subprocess, "run", fake_run)
    monkeypatch.setattr(loader, "build_env", lambda: {"CC": CLANG})
    loader.ensure_library(tmp_path)
    loader.ensure_library(tmp_path)
    assert [e["CC"] for e in envs] == [CLANG]       # second call: fresh, no rebuild

    monkeypatch.setattr(loader, "build_env", lambda: {"CC": "cl"})
    loader.ensure_library(tmp_path)
    assert [e["CC"] for e in envs] == [CLANG, "cl"]  # compiler changed: rebuilt
