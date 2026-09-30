"""Shared plumbing: corpora, the parser, `ts-lock`, and the run environment."""
from __future__ import annotations

import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

from tools.config_oracle import __main__ as oracle
from tools.query_coverage import loader

REPO = loader.REPO_ROOT
# The oracle's label map is the one root -> label map (tools/config_oracle/__main__.CORPORA).
LABELS = tuple(k for k in oracle.CORPORA if k != "selftest")
DEFAULT_WORKERS = max(1, (os.cpu_count() or 2) - 1)   # the oracle's `--workers` default
BUSY_PERCENT = 20.0


def bash_exe():
    """Git Bash's bash, never WSL's: C:\\Windows\\System32\\bash.exe would run the script
    on another machine."""
    exe = shutil.which("bash")
    if sys.platform == "win32" and (exe is None or "system32" in exe.lower()):
        raise RuntimeError(f"no Git Bash on PATH (found {exe}); run from Git Bash")
    return exe


def bash(*cmd, **kw):
    return subprocess.run([bash_exe(), *cmd], cwd=REPO, **kw)


def ts_lock(*cmd, **kw):
    """Run `cmd` under ./tools/ts-lock.sh, as every tree-sitter call must be."""
    return bash("tools/ts-lock.sh", *cmd, **kw)


def library() -> Path:
    """The built al.dll, rebuilt under ts-lock first if its stamp is stale."""
    lib = REPO / loader.LIB_NAME
    if not (lib.is_file() and loader.read_stamp(REPO) == loader.compute_stamp(REPO)):
        ts_lock(sys.executable, "-c", "from tools.query_coverage import loader; "
                "loader.ensure_library(loader.REPO_ROOT)", check=True)
    return lib


def parser():
    return loader.make_parser(loader.load_language(library()))


UTF16LE_BOM, UTF16BE_BOM = bytes([0xFF, 0xFE]), bytes([0xFE, 0xFF])


def source(data: bytes) -> bytes:
    """UTF-16 with a BOM becomes UTF-8, as tools/has_error_sweep.py and `tree-sitter parse`
    do: BCApps ships 19 such files (HybridGP GP tables), and read as UTF-8 each is one
    whole-file ERROR, which would count as 19 spurious has_error files and time garbage."""
    return data.decode("utf-16").encode("utf-8") if data[:2] in (UTF16LE_BOM, UTF16BE_BOM) else data


def load(labels):
    """-> ([(label, relpath, bytes)], read seconds). The oracle's enumeration: sorted
    rglob("*.al") per root. Reading (and `source`'s transcoding) is timed on its own, so no
    parse time includes I/O."""
    files, t0 = [], time.perf_counter_ns()
    for label in labels:
        root = oracle.CORPORA[label]
        paths = sorted(root.rglob("*.al"))
        if not paths:
            raise SystemExit(f"perf: corpus {label} ({root}) has no .al files")
        files += [(label, p.relative_to(root).as_posix(), source(p.read_bytes())) for p in paths]
    return files, (time.perf_counter_ns() - t0) / 1e9


def _cpu_model():
    if sys.platform == "win32":
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as k:
            return winreg.QueryValueEx(k, "ProcessorNameString")[0].strip()
    for line in Path("/proc/cpuinfo").read_text().splitlines():
        if line.startswith("model name"):
            return line.split(":", 1)[1].strip()
    return platform.processor()


def _out(*cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, cwd=REPO).stdout.strip() or "?"
    except OSError:
        return "not installed"


def machine_load():
    import psutil
    cpu = psutil.cpu_percent(interval=2)
    return {"cpu_percent_2s": cpu, "ram_available_bytes": psutil.virtual_memory().available,
            "busy": cpu > BUSY_PERCENT}


def environment(labels):
    import psutil
    wts = REPO / "node_modules" / "web-tree-sitter" / "package.json"
    env = {
        "cpu": _cpu_model(),
        "cores_logical": psutil.cpu_count(),
        "cores_physical": psutil.cpu_count(logical=False),
        "ram_bytes": psutil.virtual_memory().total,
        "os": platform.platform(),
        "python": platform.python_version(),
        "py_tree_sitter": importlib.metadata.version("tree-sitter"),
        "psutil": psutil.__version__,
        "tree_sitter_cli": _out("tree-sitter", "--version"),
        "node": _out("node", "--version"),
        "web_tree_sitter": json.loads(wts.read_text())["version"] if wts.is_file() else "not installed",
        # The inputs the oracle hashes (grammar.js, scanner.c, parser.c, src/**/*.h).
        "grammar_sha": oracle._header("perf")["grammar"],
        "repo_head": oracle._git_head(REPO, short=False),
        "corpora": {l: {"root": str(oracle.CORPORA[l]), "head": oracle._git_head(oracle.CORPORA[l], short=False)}
                    for l in labels},
        "load_at_start": machine_load(),
    }
    if env["load_at_start"]["busy"]:
        warn(f"machine is busy at start: CPU {env['load_at_start']['cpu_percent_2s']}% over 2 s "
             f"(> {BUSY_PERCENT}%); numbers may be inflated")
    return env


def warn(msg):
    print(f"perf: WARNING: {msg}", file=sys.stderr, flush=True)


def log(msg):
    print(f"perf: {msg}", file=sys.stderr, flush=True)

