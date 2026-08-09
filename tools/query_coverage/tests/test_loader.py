import hashlib
from pathlib import Path

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
