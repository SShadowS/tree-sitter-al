import hashlib
import subprocess
from pathlib import Path

import pytest

from tools.query_coverage import loader


def test_compute_stamp_is_sha256_of_grammar_and_scanner(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "grammar.js").write_bytes(b"grammar-contents")
    (tmp_path / "src" / "scanner.c").write_bytes(b"scanner-contents")

    expected = hashlib.sha256(b"grammar-contents" + b"scanner-contents").hexdigest()

    assert loader.compute_stamp(tmp_path) == expected


def test_compute_stamp_changes_when_scanner_changes(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "grammar.js").write_bytes(b"same")
    (tmp_path / "src" / "scanner.c").write_bytes(b"before")
    first = loader.compute_stamp(tmp_path)

    (tmp_path / "src" / "scanner.c").write_bytes(b"after")

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
    (tmp_path / "src").mkdir()
    (tmp_path / "grammar.js").write_bytes(b"grammar")
    (tmp_path / "src" / "scanner.c").write_bytes(b"scanner")

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
    assert loader.read_stamp(tmp_path) == loader.compute_stamp(tmp_path)


def test_ensure_library_raises_and_leaves_stamp_unwritten_when_generate_fails(
    tmp_path: Path, monkeypatch
):
    """A `generate` failure must surface as StaleParserError -- the same
    exception a `build` failure raises -- and must not reach `build` at all,
    since building against sources `generate` just rejected would only
    compile something equally suspect.
    """
    (tmp_path / "src").mkdir()
    (tmp_path / "grammar.js").write_bytes(b"grammar")
    (tmp_path / "src" / "scanner.c").write_bytes(b"scanner")

    def fake_run(cmd, **kwargs):
        assert cmd[:2] == ["tree-sitter", "generate"], "build must not run when generate failed"
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="boom")

    monkeypatch.setattr(loader.subprocess, "run", fake_run)

    with pytest.raises(loader.StaleParserError, match="generate failed"):
        loader.ensure_library(tmp_path)

    assert loader.read_stamp(tmp_path) is None
