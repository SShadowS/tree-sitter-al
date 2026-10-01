"""tools/session-cleanup.sh --procs: the dry run lists a leftover process and kills nothing."""
import shutil
import subprocess
import sys
from pathlib import Path

import psutil
import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from tools.gate_selftest import BASH  # noqa: E402  (Git bash, never the WSL launcher)


def test_dry_run_lists_and_kills_nothing():
    sleep = shutil.which("sleep")
    if not sleep:
        pytest.skip("no sleep executable on PATH")
    victim = subprocess.Popen([sleep, "120"])
    try:
        p = subprocess.run([BASH, "tools/session-cleanup.sh", "--procs", "--older-than", "0"],
                           cwd=REPO, capture_output=True, text=True, timeout=60)
        assert p.returncode == 0, p.stderr
        assert "DRY RUN" in p.stdout
        assert f"would kill  pid={victim.pid} " in p.stdout, p.stdout
        assert victim.poll() is None and psutil.pid_exists(victim.pid)
    finally:
        victim.kill()
        victim.wait()
