"""tools/check-runtime-ranges.py: a declared runtime range must load the grammar's ABI.

The case that matters is the one that shipped: pyproject's `core = ["tree-sitter~=0.24"]`
admitted py-tree-sitter 0.24.0, which loads ABI 13..14, while src/parser.c is ABI 15.
Each manifest is copied into tmp_path and one declaration is reverted at a time.
"""
import importlib.util
import shutil
import subprocess
import sys

import pytest

from tools.query_coverage import loader

REPO = loader.REPO_ROOT
SCRIPT = REPO / "tools" / "check-runtime-ranges.py"
MANIFESTS = ["pyproject.toml", "tools/query_coverage/requirements.txt", "package.json",
             "Cargo.toml", "go.mod", "Package.swift"]

spec = importlib.util.spec_from_file_location("check_runtime_ranges", SCRIPT)
crr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crr)


@pytest.fixture
def root(tmp_path):
    for rel in MANIFESTS:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / rel, tmp_path / rel)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "parser.c").write_text("#define LANGUAGE_VERSION 15\n")
    return tmp_path


def run(root):
    p = subprocess.run([sys.executable, str(SCRIPT), "--root", str(root)], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def edit(path, old, new):
    text = path.read_text(encoding="utf-8")
    assert old in text, f"{old!r} not in {path.name}: the fixture no longer matches the manifest"
    path.write_text(text.replace(old, new), encoding="utf-8")


def test_repo_is_clean():
    code, out = run(REPO)
    assert code == 0, out


def test_copied_manifests_are_clean(root):
    code, out = run(root)
    assert code == 0, out


def test_old_python_pin_fails(root):
    edit(root / "pyproject.toml", '"tree-sitter~=0.25"', '"tree-sitter~=0.24"')
    code, out = run(root)
    assert code == 1, out
    assert "FAIL python     pyproject.toml" in out
    assert "admits 0.24.0..<0.25.0, which loads ABI 13..14, not 15" in out


def test_tilde_equal_two_components_has_no_minor_ceiling():
    # ~=0.24 is >=0.24,==0.* -- it never excluded 0.25; it failed by admitting 0.24.
    assert crr.pep440("~=0.24") == ((0, 24, 0), (1, 0, 0))
    assert crr.pep440("~=0.24.0") == ((0, 24, 0), (0, 25, 0))


@pytest.mark.parametrize("rel, old, new, runtime", [
    ("go.mod", "go-tree-sitter v0.25.0", "go-tree-sitter v0.24.0", "go"),
    ("go.mod", "github.com/tree-sitter/go-tree-sitter v0.25.0",
     "github.com/smacker/go-tree-sitter v0.0.0-20240827094217-dd81d9e9be82", "go-smacker"),
    ("Package.swift", 'from: "0.10.0"', 'from: "0.8.0"', "swift"),
    ("Cargo.toml", 'tree-sitter = "0.25"', 'tree-sitter = "0.24"', "rust"),
    ("package.json", '"tree-sitter": "^0.25.0"', '"tree-sitter": ">=0.22.4"', "node"),
])
def test_other_old_floors_fail(root, rel, old, new, runtime):
    edit(root / rel, old, new)
    code, out = run(root)
    assert code == 1, out
    assert f"FAIL {runtime}" in out


def test_newer_abi_fails_everything_pinned_to_0_25(root):
    (root / "src" / "parser.c").write_text("#define LANGUAGE_VERSION 16\n")
    code, out = run(root)
    assert code == 1, out


@pytest.mark.parametrize("rel, old, new", [
    ("package.json", '"tree-sitter": "^0.25.0"', '"tree-sitter": "latest"'),  # a dist-tag, not a range
    ("pyproject.toml", '"tree-sitter~=0.25"', '"tree-sitter!=0.24"'),
    ("Package.swift", 'from: "0.10.0"', 'branch: "main"'),
])
def test_unreadable_range_exits_2(root, rel, old, new):
    edit(root / rel, old, new)
    code, out = run(root)
    assert code == 2, out


def test_missing_manifest_exits_2(root):
    (root / "go.mod").unlink()
    code, out = run(root)
    assert code == 2, out
