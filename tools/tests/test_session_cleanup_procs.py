"""tools/session-cleanup.sh --procs: lists without killing, tells live from orphaned, and
needs psutil. Never runs --yes: that would kill other sessions' orphans."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import psutil
import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from tools.gate_selftest import BASH  # noqa: E402  (Git bash, never the WSL launcher)


def procs(*args, env=None):
    return subprocess.run([BASH, "tools/session-cleanup.sh", "--procs", "--older-than", "0", *args],
                          cwd=REPO, capture_output=True, text=True, timeout=60,
                          env={**os.environ, **(env or {})})


@pytest.fixture
def live_sleep():
    sleep = shutil.which("sleep")
    if not sleep:
        pytest.skip("no sleep executable on PATH")
    victim = subprocess.Popen([sleep, "120"])  # its parent, this pytest, is alive
    yield victim
    victim.kill()
    victim.wait()


def test_dry_run_lists_a_live_process_as_kept_and_kills_nothing(live_sleep):
    p = procs()
    assert p.returncode == 0, p.stderr
    assert "DRY RUN" in p.stdout
    assert f"would keep   pid={live_sleep.pid} " in p.stdout, p.stdout
    assert live_sleep.poll() is None and psutil.pid_exists(live_sleep.pid)


def test_orphans_only_leaves_out_a_live_process(live_sleep):
    p = procs("--orphans-only")
    assert p.returncode == 0, p.stderr
    assert f"pid={live_sleep.pid} " not in p.stdout, p.stdout


def test_without_psutil_exits_2(tmp_path):
    (tmp_path / "psutil.py").write_text("raise ImportError('hidden for the test')\n")
    p = procs(env={"PYTHONPATH": str(tmp_path)})
    assert p.returncode == 2
    assert "needs psutil" in p.stderr
