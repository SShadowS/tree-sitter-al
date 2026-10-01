"""tools/metrics.sh: `--vs HEAD` against an unmodified tree reports every delta as 0."""
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from tools.gate_selftest import BASH  # noqa: E402  (Git bash, never the WSL launcher)


def test_vs_head_deltas_are_zero():
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "src/parser.c", "grammar.js",
                            "test/corpus"], cwd=REPO, capture_output=True, text=True).stdout
    if dirty.strip():
        pytest.skip("parser.c, grammar.js or test/corpus differs from HEAD")
    p = subprocess.run([BASH, "tools/metrics.sh", "--vs", "HEAD"], cwd=REPO,
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    first, at_head, delta = p.stdout.splitlines()
    assert re.match(r"STATE_COUNT=\d+ LARGE_STATE_COUNT=\d+ SYMBOL_COUNT=\d+ parser\.c=\d+B "
                    r"\(\d+\.\d MiB\) grammar\.js=\d+ lines tests=\d+$", first)
    assert at_head.split(None, 2)[2] == first
    numbers = re.findall(r"[+-]?\d+(?:\.\d+)?", delta)
    assert numbers and all(float(n) == 0 for n in numbers), delta
