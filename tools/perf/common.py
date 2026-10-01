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
    if not (lib.is_file() and loader.read_stamp(REPO) == loader.library_stamp(REPO)):
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
    """-> ([(label, relpath, bytes)], read info). The oracle's enumeration: sorted
    rglob("*.al") per root. Reading (and `source`'s transcoding) is timed on its own, so no
    parse time includes I/O. read info: {seconds, per_corpus: {label: seconds}, utf16: [ids
    of the transcoded files]} -- per corpus because the roots sit on different drives."""
    files, info, t0 = [], {"per_corpus": {}, "utf16": []}, time.perf_counter_ns()
    for label in labels:
        root, t1 = oracle.CORPORA[label], time.perf_counter_ns()
        paths = sorted(root.rglob("*.al"))
        if not paths:
            raise SystemExit(f"perf: corpus {label} ({root}) has no .al files")
        for p in paths:
            raw = p.read_bytes()
            rel = p.relative_to(root).as_posix()
            if raw[:2] in (UTF16LE_BOM, UTF16BE_BOM):
                info["utf16"].append(f"{label}:{rel}")
            files.append((label, rel, source(raw)))
        info["per_corpus"][label] = (time.perf_counter_ns() - t1) / 1e9
    info["seconds"] = (time.perf_counter_ns() - t0) / 1e9
    return files, info


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
    """A 2 s reading with the top 5 processes, the CPU clock and the power plan. `busy` keeps
    the old 20% rule for the start warning; the per-group judgement is tools/perf/load.py's
    continuous outside-CPU sampling."""
    from tools.perf import load
    snap = load.snapshot()
    return snap | {"busy": snap["cpu_percent_2s"] > BUSY_PERCENT}


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
        # The CCD map (which logical CPUs share which L3, and the SMT pairs), the CPU the
        # single-threaded groups are pinned to and why, and the AMD 3D V-Cache driver state.
        "cpu_topology": _pin().topology(),
        "single_thread_pin": dict(zip(("cpu", "why"), _pin().pin_cpu())),
        "amd_3d_vcache_driver": _pin().amd_vcache_driver(),
        "repo_dirty": _out("git", "status", "--porcelain", "--untracked-files=no") not in ("", "?"),
        "cpu_affinity": _affinity(),
        "corpora": {l: {"root": str(oracle.CORPORA[l]), "head": oracle._git_head(oracle.CORPORA[l], short=False),
                        "drive": oracle.CORPORA[l].resolve().drive or "/"}
                    for l in labels},
        "load_at_start": machine_load(),
    }
    if env["load_at_start"]["busy"]:
        warn(f"machine is busy at start: CPU {env['load_at_start']['cpu_percent_2s']}% over 2 s "
             f"(> {BUSY_PERCENT}%); numbers may be inflated")
    return env


def _pin():
    from tools.perf import pin
    return pin


def _affinity():
    import psutil
    try:
        cpus = psutil.Process().cpu_affinity()
    except (AttributeError, psutil.Error):
        return "n/a"
    return "all" if len(cpus) == psutil.cpu_count() else cpus


def warn(msg):
    print(f"perf: WARNING: {msg}", file=sys.stderr, flush=True)


def log(msg):
    print(f"perf: {msg}", file=sys.stderr, flush=True)

