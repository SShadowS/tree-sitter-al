"""Build and load the local AL grammar, refusing to run against a stale parser."""

from __future__ import annotations

import ctypes
import hashlib
import subprocess
import warnings
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LIB_NAME = "al.dll"
STAMP_RELPATH = Path("tools/query_coverage/reports/.build-stamp")


class StaleParserError(RuntimeError):
    """The built library does not match the current grammar sources."""


def compute_stamp(repo_root: Path) -> str:
    """sha256 over grammar.js and src/scanner.c.

    mtime is deliberately not used: git rewrites mtimes in arbitrary order
    during checkouts and branch switches on Windows, producing both false
    alarms and false all-clears.
    """
    digest = hashlib.sha256()
    digest.update((repo_root / "grammar.js").read_bytes())
    digest.update((repo_root / "src" / "scanner.c").read_bytes())
    return digest.hexdigest()


def _stamp_path(repo_root: Path) -> Path:
    return repo_root / STAMP_RELPATH


def read_stamp(repo_root: Path) -> str | None:
    path = _stamp_path(repo_root)
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8").strip()


def write_stamp(repo_root: Path, stamp: str) -> None:
    path = _stamp_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(stamp + "\n")


def ensure_library(repo_root: Path, force: bool = False) -> Path:
    """Build al.dll only when the grammar sources changed. Returns its path.

    `tree-sitter build` does NOT regenerate src/parser.c from grammar.js --
    verified directly (isolated scratch grammar, tree-sitter 0.26.12: edited
    grammar.js, ran `build`, and the compiled grammar.json still reflected the
    old rule). Skipping `generate` here would recompile the stale parser.c,
    then write_stamp still records the NEW grammar.js hash below, so every
    later run believes the parser is current when it never was -- exactly the
    silent-staleness EXIT_STALE_PARSER exists to catch. `generate` is
    idempotent and is the project's own documented cycle (see CLAUDE.md's
    "Standard development cycle"), so running it unconditionally whenever the
    stamp differs costs nothing when the sources didn't actually change the
    generated output.
    """
    lib_path = repo_root / LIB_NAME
    current = compute_stamp(repo_root)

    if not force and lib_path.is_file() and read_stamp(repo_root) == current:
        return lib_path

    generate_result = subprocess.run(
        ["tree-sitter", "generate"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if generate_result.returncode != 0:
        raise StaleParserError(
            f"tree-sitter generate failed (exit {generate_result.returncode}):\n"
            f"{generate_result.stderr}"
        )

    result = subprocess.run(
        ["tree-sitter", "build", "--output", str(lib_path), str(repo_root)],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise StaleParserError(
            f"tree-sitter build failed (exit {result.returncode}):\n{result.stderr}"
        )

    write_stamp(repo_root, current)
    return lib_path


def load_language(lib_path: Path):
    import tree_sitter

    lib = ctypes.cdll.LoadLibrary(str(lib_path.resolve()))
    lib.tree_sitter_al.restype = ctypes.c_void_p
    pointer = lib.tree_sitter_al()

    # py-tree-sitter 0.25.2 accepts an int pointer but deprecates it. This is
    # the single sanctioned call site; do not suppress this warning elsewhere.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return tree_sitter.Language(pointer)


def make_parser(language):
    import tree_sitter

    return tree_sitter.Parser(language)
