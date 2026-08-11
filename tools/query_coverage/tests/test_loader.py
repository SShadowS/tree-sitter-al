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
    assert loader.read_stamp(tmp_path) == loader.compute_stamp(tmp_path)


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
    pre_generate = loader.compute_stamp(tmp_path)

    def fake_run(cmd, **kwargs):
        if cmd[:2] == ["tree-sitter", "generate"]:
            # What a real `generate` does: rewrite the generated artifacts.
            (tmp_path / "src" / "node-types.json").write_bytes(b"regenerated")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(loader.subprocess, "run", fake_run)

    loader.ensure_library(tmp_path)

    assert loader.read_stamp(tmp_path) != pre_generate
    assert loader.read_stamp(tmp_path) == loader.compute_stamp(tmp_path)

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
