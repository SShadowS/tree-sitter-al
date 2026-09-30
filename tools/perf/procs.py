"""Build/size measurements and the oracle's wall time with aggregate process-tree memory."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from tools.perf import common, native, stats

MiB = 2 ** 20
INTERVAL = 0.25


class TreeSampler(threading.Thread):
    """Samples a process and all its descendants every `interval` s. Records the peak of the
    SUM of RSS over the tree (aggregate), the largest single-process RSS (per-process max),
    and on Windows the peak sum of private bytes, which -- unlike RSS -- does not count a
    page shared by several processes (al.dll's code in every worker) once per process."""

    def __init__(self, pid, interval=INTERVAL):
        super().__init__(daemon=True)
        import psutil
        self.root, self.interval, self._stop = psutil.Process(pid), interval, threading.Event()
        self.peak_sum = self.peak_single = self.peak_private_sum = 0
        self.peak_processes = self.samples = 0

    def sample(self):
        import psutil
        try:
            procs = [self.root, *self.root.children(recursive=True)]
        except psutil.NoSuchProcess:
            return
        rss, private = [], 0
        for p in procs:
            try:
                mi = p.memory_info()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            rss.append(mi.rss)
            private += getattr(mi, "private", 0)
        if rss:
            self.samples += 1
            self.peak_sum = max(self.peak_sum, sum(rss))
            self.peak_single = max(self.peak_single, max(rss))
            self.peak_private_sum = max(self.peak_private_sum, private)
            self.peak_processes = max(self.peak_processes, len(rss))

    def run(self):
        while not self._stop.is_set():
            self.sample()
            self._stop.wait(self.interval)

    def stop(self):
        self._stop.set()
        self.join()


def run_sampled(cmd, **kw):
    """-> {exit_code, seconds, peak memory...} of `cmd`, sampled over its whole process tree."""
    t0 = time.perf_counter_ns()
    proc = subprocess.Popen(cmd, cwd=common.REPO, **kw)
    s = TreeSampler(proc.pid)
    s.start()
    code = proc.wait()
    seconds = (time.perf_counter_ns() - t0) / 1e9
    s.stop()
    return {"exit_code": code, "seconds": seconds, "peak_rss_sum_bytes": s.peak_sum,
            "peak_rss_single_process_bytes": s.peak_single, "peak_private_sum_bytes": s.peak_private_sum,
            "peak_processes": s.peak_processes, "samples": s.samples, "interval_s": INTERVAL}


# ---- oracle ---------------------------------------------------------------------------

def oracle(labels, full=True):
    """The quick tier: warm-up + native.REPEATS runs. The full tier over `labels`: ONE run
    (it takes 13-22 min), no warm-up. Both under ts-lock; the sampled tree is ts-lock's
    bash, the oracle and every worker."""
    reports = common.REPO / "tools" / "perf" / "reports"
    out = {"workers": common.DEFAULT_WORKERS}
    quick = [sys.executable, "-m", "tools.config_oracle", "run", "--tier", "quick",
             "--report", str(reports / "oracle-quick")]
    runs = []
    for r in range(native.REPEATS + 1):
        common.log(f"oracle quick tier run {r}/{native.REPEATS}" + (" (warm-up)" if r == 0 else ""))
        res = run_sampled([common.bash_exe(), "tools/ts-lock.sh", *quick], stdout=subprocess.DEVNULL)
        if res["exit_code"]:
            raise RuntimeError(f"oracle quick tier exited {res['exit_code']}")
        runs.append(res)
    runs = runs[1:]
    out["quick"] = {"seconds": stats.spread([r["seconds"] for r in runs]),
                    "peak_rss_sum_bytes": max(r["peak_rss_sum_bytes"] for r in runs),
                    "peak_rss_single_process_bytes": max(r["peak_rss_single_process_bytes"] for r in runs),
                    "peak_private_sum_bytes": max(r["peak_private_sum_bytes"] for r in runs),
                    "repeats": len(runs)}
    if full:
        roots = [str(common.oracle.CORPORA[l]) for l in labels]
        cmd = [sys.executable, "-m", "tools.config_oracle", "run", "--tier", "full",
               "--report", str(reports / "oracle-full"), *[a for r in roots for a in ("--root", r)]]
        common.log("oracle full tier (one run, 13-22 min)")
        res = run_sampled([common.bash_exe(), "tools/ts-lock.sh", *cmd], stdout=subprocess.DEVNULL)
        summary = reports / "oracle-full" / "summary.md"
        rss_line = next((l for l in summary.read_text(encoding="utf-8").splitlines()
                         if "peak RSS" in l), "") if summary.is_file() else ""
        out["full"] = {**res, "repeats": 1, "roots": roots, "oracle_own_peak_rss_line": rss_line.lstrip("- ")}
    return out


# ---- build and size -------------------------------------------------------------------

def _src_digest():
    h = hashlib.sha256()
    for p in sorted((common.REPO / "src").rglob("*")):
        if p.is_file():
            h.update(p.relative_to(common.REPO).as_posix().encode() + b"\0" + p.read_bytes())
    return h.hexdigest()


def parser_metrics():
    text = (common.REPO / "src" / "parser.c").read_text(encoding="utf-8", errors="replace")
    m = {k: int(re.search(rf"#define {k} (\d+)", text).group(1))
         for k in ("LANGUAGE_VERSION", "STATE_COUNT", "LARGE_STATE_COUNT", "SYMBOL_COUNT")}
    size = (common.REPO / "src" / "parser.c").stat().st_size
    return {"parser_c_bytes": size, "parser_c_mib": round(size / MiB, 2), **m,
            "wasm_bytes": (common.REPO / "tree-sitter-al.wasm").stat().st_size}


def build_inner(out_path):
    """Runs INSIDE one ts-lock acquisition (`python -m tools.perf _build-inner OUT`), so the
    lock wait is not timed. generate: warm-up + REPEATS; build: REPEATS, each to a fresh
    output file outside the repo so the shared al.dll is never touched."""
    before = _src_digest()
    res = {}
    for name in ("generate", "build"):
        secs = []
        with tempfile.TemporaryDirectory() as tmp:
            for r in range(native.REPEATS + (name == "generate")):
                lib = Path(tmp) / f"al-perf-{r}.dll"
                cmd = (["tree-sitter", "generate"] if name == "generate"
                       else ["tree-sitter", "build", "--output", str(lib), "."])
                t = time.perf_counter_ns()
                proc = subprocess.run(cmd, cwd=common.REPO, capture_output=True, text=True)
                secs.append((time.perf_counter_ns() - t) / 1e9)
                if proc.returncode:
                    raise RuntimeError(f"{' '.join(cmd)} exited {proc.returncode} (run {r + 1}):\n"
                                       f"{proc.stdout}{proc.stderr}")
        res[name] = stats.spread(secs[1:] if name == "generate" else secs)
    after = _src_digest()
    diffstat = subprocess.run(["git", "diff", "--stat", "--", "src"], cwd=common.REPO,
                              capture_output=True, text=True).stdout.strip()
    res["src_unchanged_by_generate"] = before == after and not diffstat
    res["git_diff_stat_src"] = diffstat
    res["build_command"] = "tree-sitter build --output <tmp>/al-perf-N.dll ."
    Path(out_path).write_text(json.dumps(res), encoding="utf-8")


def build():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "build.json"
        common.ts_lock(sys.executable, "-m", "tools.perf", "_build-inner", str(out), check=True)
        res = json.loads(out.read_text(encoding="utf-8"))
    if not res["src_unchanged_by_generate"]:
        common.warn(f"tree-sitter generate changed src/:\n{res['git_diff_stat_src']}")
    return {**res, **parser_metrics()}
