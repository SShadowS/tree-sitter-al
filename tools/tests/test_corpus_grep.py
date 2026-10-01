"""tools/corpus-grep.sh: a missing root prints `missing`; a bad pattern exits 2."""
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from tools.gate_selftest import BASH  # noqa: E402  (Git bash, never the WSL launcher)


def run(*args, **env):
    return subprocess.run([BASH, "tools/corpus-grep.sh", *args], cwd=REPO, capture_output=True,
                          text=True, env={**os.environ, **env})


def test_missing_root_prints_missing_and_is_not_an_error(tmp_path):
    p = run("-c", "zz_no_such_text_qq", AL_BC28_ROOT=str(tmp_path / "nope"),
            AL_BCAPPS29_ROOT=str(tmp_path / "nope2"))
    assert p.returncode == 1, p.stderr  # no match, not a failure
    assert any(l.startswith("bc28.1") and " missing " in l for l in p.stdout.splitlines()), p.stdout
    assert p.stdout.splitlines()[-1].split()[:2] == ["total", "0"]


def test_bad_pattern_exits_2(tmp_path):
    p = run("-E", "a(", AL_BC28_ROOT=str(tmp_path), AL_BCAPPS29_ROOT=str(tmp_path))
    assert p.returncode == 2
    assert "bad pattern" in p.stderr
