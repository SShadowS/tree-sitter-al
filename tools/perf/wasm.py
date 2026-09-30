"""WASM (web-tree-sitter under Node) full-parse throughput, single-threaded, plus a per-file
has_error agreement check against the native parser."""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from tools.perf import common, native, stats

WASM = common.REPO / "tree-sitter-al.wasm"
SCRIPT = Path(__file__).with_name("wasm_bench.mjs")


def check_fresh():
    r = common.bash("tools/check-wasm-fresh.sh", capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("perf: tree-sitter-al.wasm is stale -- rebuild it in its own commit first:\n"
                         "  ./tools/ts-lock.sh tree-sitter build --wasm -o tree-sitter-al.wasm\n"
                         "  tools/check-wasm-fresh.sh --update\n" + r.stderr)


def measure(labels, native_error_ids=None):
    """`native_error_ids`: the native run's has_error file ids, when this run follows one;
    otherwise the native flags are computed here (one untimed pass)."""
    check_fresh()
    files, _ = common.load(labels)
    if native_error_ids is None:
        p = common.parser()
        native_error_ids = {f"{l}:{r}" for l, r, s in files if p.parse(s).root_node.has_error}
    ids = [f"{l}:{r}" for l, r, _ in files]
    paths = [str(common.oracle.CORPORA[l] / r) for l, r, _ in files]
    with tempfile.TemporaryDirectory() as tmp:
        manifest, out = Path(tmp) / "manifest.json", Path(tmp) / "out.json"
        manifest.write_text(json.dumps({"wasm": str(WASM), "repeats": native.REPEATS, "files": paths}))
        common.log(f"wasm: {len(files)} files")
        # The whole node process is pinned to the native runs' CPU, right after it starts:
        # it reads every file and loads the wasm before its first timed parse.
        from tools.perf import pin
        cpu = pin.pin_cpu()[0]
        node = subprocess.Popen(["node", str(SCRIPT), str(manifest), str(out)], cwd=common.REPO)
        pin.pin_process(node.pid, (cpu,))
        if node.wait():
            raise subprocess.CalledProcessError(node.returncode, "node wasm_bench.mjs")
        raw = json.loads(out.read_text())
    wasm_errors = {ids[i] for i, e in enumerate(raw["has_error"]) if e}
    per_file_ms = [stats.median([run[i] for run in raw["ns"]]) / 1e6 for i in range(len(files))]
    result = {"web_tree_sitter": raw["web_tree_sitter"], "wasm_bytes": WASM.stat().st_size,
              "read_seconds": raw["read_seconds"], "repeats": native.REPEATS,
              "invalid_utf8_files": [ids[i] for i in raw["invalid_utf8"]],
              "pin": {"pinned_to": [cpu], "ran_on": "not observable from node: the whole process's "
                      "affinity is the one CPU, so it can run nowhere else"},
              "has_error_disagreements": {"wasm_only": sorted(wasm_errors - set(native_error_ids)),
                                          "native_only": sorted(set(native_error_ids) - wasm_errors)},
              "corpora": {}}
    for name in [*labels, "combined"]:
        idx = range(len(files)) if name == "combined" else [i for i in range(len(files)) if files[i][0] == name]
        nbytes = sum(len(files[i][2]) for i in idx)
        slow = sorted(idx, key=lambda k: -per_file_ms[k])[:native.SLOWEST]
        result["corpora"][name] = {
            "files": len(idx), "bytes": nbytes, "has_error": sum(ids[i] in wasm_errors for i in idx),
            "single": native._throughput([sum(run[i] for i in idx) / 1e9 for run in raw["ns"]], len(idx), nbytes),
            "latency_ms": stats.latency([per_file_ms[i] for i in idx]),
            "slowest": [{"file": ids[k], "bytes": len(files[k][2]), "ms": round(per_file_ms[k], 3)} for k in slow],
        }
    d = result["has_error_disagreements"]
    if d["wasm_only"] or d["native_only"]:
        common.warn(f"wasm/native has_error disagreement: {len(d['wasm_only'])} wasm-only, "
                    f"{len(d['native_only'])} native-only")
    return result
