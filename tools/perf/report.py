"""`compare` and `merge` result files, and render one into docs/performance-baselines.md."""
from __future__ import annotations

MiB = 2 ** 20
# Lists, descriptive strings and provenance are not metrics; `runs` is inside a timed metric.
SKIP = {"env", "sample", "slowest", "mismatch_details", "has_error_files", "runs", "roots",
        "invalid_utf8_files", "has_error_disagreements", "warnings", "meta", "checks",
        "quota_shortfalls"}
# Groups whose numbers do not depend on the corpus set.
CORPUS_FREE = {"build"}
# Groups timed with the native library, whose compiler must match to compare them.
NATIVE_GROUPS = ("native", "native_zig", "incremental", "oracle", "build")


def is_timed(v):
    return isinstance(v, dict) and {"median", "min", "max"} <= set(v)


def flatten(result, prefix=""):
    """{dotted path: timed dict | number} over every metric of a result file."""
    out = {}
    for k, v in (result.items() if isinstance(result, dict) else ()):
        if k in SKIP:
            continue
        path = f"{prefix}{k}"
        if is_timed(v):
            out[path] = v
        elif isinstance(v, dict):
            out |= flatten(v, path + ".")
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            out[path] = v
    return out


def corpus_set(result, group):
    """The corpora a group measured: its own meta, else (an older file) the run's env."""
    meta = result.get("groups", {}).get(group, {}).get("meta") or {}
    return tuple(sorted(meta.get("corpora") or result.get("env", {}).get("corpora", {})))


def library(result, group):
    """The native library's build identity -- (compiler name, version, compile flags, link
    flags) -- or None if unrecorded. The compiler is keyed by its file name, not its full path,
    so moving between VS editions or toolset directories with the same compiler is not a change."""
    lib = (result.get("groups", {}).get(group, {}).get("meta") or {}).get("library")
    if not isinstance(lib, dict):
        lib = result.get("env", {}).get("native_library")
    if not isinstance(lib, dict):
        return None
    name = lib["compiler"].replace("\\", "/").rsplit("/", 1)[-1].lower()
    return name, lib["compiler_version"], tuple(lib["flags"]), tuple(lib.get("link_flags", ()))


def placement(result, group):
    """(CPU model, pinned CPU set) of a single-threaded group; the set is None when unpinned
    (every file before fix round 2)."""
    g = result.get("groups", {}).get(group, {})
    pin = g.get("single_pin") or g.get("pin")
    return result.get("env", {}).get("cpu"), tuple(pin["pinned_to"]) if isinstance(pin, dict) else None


def session(result, group):
    return (result.get("groups", {}).get(group, {}).get("meta") or {}).get("started") or result.get("started")


# Noise floors for `!`, as a fraction of the old median (fix round 2): same-session re-runs
# agree to ~0.3%, but sessions drifted ~30% single-threaded, so no within-run spread is a
# sufficient error bar on its own.
FLOOR_SINGLE, FLOOR_PARALLEL = 0.05, 0.10


def comparable(path, sets_equal):
    """A per-corpus entry (`<group>.corpora.<label>.`, not `combined`) means the same thing in
    any run; every other figure of a corpus-dependent group is an aggregate over the run's
    corpus set, and comparing it across two sets is comparing different inputs."""
    group, *rest = path.split(".")
    if group in CORPUS_FREE or sets_equal:
        return True
    return len(rest) >= 2 and rest[0] == "corpora" and rest[1] != "combined"


def compare(old, new, floor=None):
    """-> lines: one per metric present in either file.
    `!`   |delta median| > max(old spread, new spread, floor x old median), the floor being
          FLOOR_PARALLEL for `.parallel.` figures and FLOOR_SINGLE otherwise, or `floor` for all;
    `?`   an exact count changed (both values integers: files, has_error, STATE_COUNT...);
          a float without a spread (a percentile, a single run) is shown without a flag;
    `n/c` not comparable: an aggregate over two different corpus sets. No delta is printed;
    `+`/`-` only in the new/old file."""
    ga, gb = old.get("groups", {}), new.get("groups", {})
    a, b = flatten(ga), flatten(gb)
    lines = [f"{'metric':<70} {'old':>14} {'new':>14} {'delta':>14} {'rel':>9}  flag"]
    head, same = [], {}
    for g in sorted(set(ga) & set(gb)):
        sa, sb = corpus_set(old, g), corpus_set(new, g)
        same[g] = sa == sb
        if not same[g] and g not in CORPUS_FREE:
            head.append(f"NOTE {g}: corpus sets differ ({'+'.join(sa)} vs {'+'.join(sb)}): only its "
                        "per-corpus entries are compared; every aggregate is n/c")
        ta, tb = session(old, g), session(new, g)
        if ta != tb:
            head.append(f"CROSS-SESSION {g}: measured {ta} vs {tb}. Single-threaded figures have "
                        "drifted up to ~30% between sessions on this machine: informational only, not "
                        "decision-grade. Decide with `python -m tools.perf ab` (same session, interleaved)")
        pa, pb = placement(old, g), placement(new, g)
        if (g in ("native", "native_zig", "wasm", "incremental")) and pa != pb:
            head.append(f"WARNING {g}: CPU or pin differs ({pa} vs {pb}): placement alone moved a DC "
                        "pass ~12%; the single-threaded figures are not comparable")
        if g in NATIVE_GROUPS:
            la, lb = library(old, g), library(new, g)
            if la is None or lb is None:
                if la != lb:
                    head.append(f"WARNING {g}: the {'old' if la is None else 'new'} file does not record "
                                "the native library's compiler and flags, so the same build cannot be confirmed")
            elif la != lb:
                head.append(f"WARNING {g}: the native library was built differently: {la} vs {lb}. "
                            "A compiler or flag change moves these numbers without any grammar change")
    for path in sorted(set(a) | set(b)):
        if path not in a or path not in b:
            lines.append(f"{path:<70} {'-' if path not in a else _num(a[path]):>14} "
                         f"{'-' if path not in b else _num(b[path]):>14} {'':>14} {'':>9}  "
                         + ("+" if path not in a else "-"))
            continue
        x, y = a[path], b[path]
        if not comparable(path, same.get(path.split(".")[0], True)):
            lines.append(f"{path:<70} {_num(x):>14} {_num(y):>14} {'n/c':>14} {'':>9}  n/c")
            continue
        timed = is_timed(x) and is_timed(y)
        xv, yv = (x["median"], y["median"]) if timed else (_val(x), _val(y))
        delta = yv - xv
        rel = f"{delta / xv * 100:+.2f}%" if xv else ("+0.00%" if not delta else "n/a")
        if timed:
            f = floor if floor is not None else (FLOOR_PARALLEL if ".parallel." in path else FLOOR_SINGLE)
            flag = "!" if abs(delta) > max(x["max"] - x["min"], y["max"] - y["min"], f * abs(xv)) else ""
        else:
            flag = "?" if delta and isinstance(xv, int) and isinstance(yv, int) else ""
        lines.append(f"{path:<70} {_num(xv):>14} {_num(yv):>14} {_num(delta):>14} {rel:>9}  {flag}")
    envs = old.get("env", {}), new.get("env", {})
    for k in sorted(set(envs[0]) | set(envs[1])):
        if k not in ("load_at_start", "load_at_end", "load_before_group") and envs[0].get(k) != envs[1].get(k):
            lines.append(f"env {k}: {envs[0].get(k)!r} -> {envs[1].get(k)!r}")
    return head + lines


def _val(v):
    return v["median"] if is_timed(v) else v


def _num(v):
    v = _val(v)
    return f"{v:.4g}" if isinstance(v, float) else str(v)


# ---- merge ----------------------------------------------------------------------------

def merge(base, new, source):
    """Replace base's groups with new's, keeping provenance. Refuses a different parser
    (grammar sha), a different corpus HEAD, or a different corpus set for a replaced group.
    A base group measured before per-group metadata existed gets meta that says what was and
    was not recorded -- never an invented load figure."""
    eb, en = base["env"], new["env"]
    if eb["grammar_sha"] != en["grammar_sha"]:
        raise ValueError(f"grammar differs: {eb['grammar_sha']} vs {en['grammar_sha']}")
    for label in set(eb["corpora"]) & set(en["corpora"]):
        if eb["corpora"][label]["head"] != en["corpora"][label]["head"]:
            raise ValueError(f"corpus {label} HEAD differs")
    for name, grp in base["groups"].items():
        if "meta" not in grp:
            pre = eb.get("load_before_group", {}).get(name)
            grp["meta"] = {
                "corpora": sorted(eb["corpora"]), "command": base["command"],
                "started": base["started"], "finished": base["finished"],
                "times": "the whole run's window; the group's own start and end were not recorded",
                "load": {"sampled": False, "note": "not sampled: measured before continuous load "
                         "sampling existed" + (f"; the 2 s reading before the group was "
                                               f"{pre['cpu_percent_2s']}% CPU" if pre else "")},
                "library": "not recorded (compiler identity was not captured by that run)"}
    for name, grp in new["groups"].items():
        if name in base["groups"] and corpus_set(base, name) != corpus_set(new, name):
            raise ValueError(f"group {name}: corpus set differs ({corpus_set(base, name)} vs {corpus_set(new, name)})")
        base["groups"][name] = grp
    base.setdefault("merges", []).append({
        "from": source, "groups": sorted(new["groups"]), "command": new["command"],
        "started": new["started"], "finished": new["finished"],
        "env_differences": {k: en[k] for k in en if k not in ("load_at_start", "load_at_end") and eb.get(k) != en.get(k)},
        "warnings": new.get("warnings", [])})
    return base


# ---- markdown -------------------------------------------------------------------------

def _t(v, fmt="{:.1f}"):
    return f"{fmt.format(v['median'])} ({fmt.format(v['min'])}-{fmt.format(v['max'])})"


def _mib(n):
    return f"{n / MiB:,.1f} MiB"


def _measured(grp):
    m = grp.get("meta")
    if not m:
        return "*Measured:* not recorded."
    ld = m.get("load", {})
    if ld.get("sampled"):
        load = (f"outside-CPU mean {ld['outside_cores_mean']:.2f}, p95 {ld['outside_cores_p95']:.2f}, "
                f"max {ld['outside_cores_max']:.2f} logical cores over {ld['samples']} samples"
                + (" -- **FLAGGED**" if ld["flagged"] else " (under both thresholds)"))
    else:
        load = f"load {ld.get('note', 'not sampled')}"
    lib = m.get("library")
    lib = (f"; library: `{lib['compiler_version']}` `{' '.join(lib['flags'])}`" if isinstance(lib, dict)
           else f"; library: {lib}" if lib else "")
    when = f"within the run of {m['started']} to {m['finished']}" if m.get("times") else f"{m['started']} to {m['finished']}"
    return f"*Measured* {when} over {'+'.join(m['corpora'])}; {load}{lib}."


def render(r, json_rel, notes=None):
    g, env = r["groups"], dict(r["env"])
    # Merged runs bring their own environment: show the latest value of every field (each
    # group's *Measured* line says which run it came from); the load readings stay the base run's.
    for m in r.get("merges", []):
        for k, v in m.get("env_differences", {}).items():
            # A subset run (ab over dc) records only its corpora: add, never replace the map.
            env[k] = {**env[k], **v} if k == "corpora" and isinstance(env.get(k), dict) else v
    L = ["# Performance baselines", "",
         f"Generated by `python -m tools.perf render {json_rel}` from **`{json_rel}`**, the committed "
         "result. Do not edit the numbers by hand: re-measure, or re-render. The hand-written history "
         f"below the numbers comes from `{json_rel.rsplit('.', 1)[0]}.notes.md`.", "",
         f"- recorded: {r['started']} to {r['finished']}",
         f"- command: `{r['command']}`"]
    for m in r.get("merges", []):
        if "dropped" in m:
            L.append(f"- group **{m['dropped']}** dropped at {m['at']} (`python -m tools.perf merge --drop`)")
            continue
        L.append(f"- groups **{', '.join(m['groups'])}** re-measured {m['started']} to {m['finished']} "
                 f"by `{m['command']}`"
                 + (f" at repo `{m['env_differences']['repo_head'][:7]}`" if "repo_head" in m["env_differences"] else "")
                 + f", merged from `{m['from']}` with `python -m tools.perf merge`")
        L += [f"  - warning: {w}" for w in m.get("warnings", [])]
    L.append("")
    if r.get("warnings"):
        L += ["**Warnings raised during the base run:**", "", *(f"- {w}" for w in r["warnings"]), ""]
    L += ["## Environment", "", "Latest value of each field across the base run and the merged runs; "
          "the load rows are the base run's.", "", "| | |", "|---|---|"]
    for k in ("cpu", "cores_logical", "cores_physical", "os", "python", "py_tree_sitter", "psutil",
              "tree_sitter_cli", "node", "web_tree_sitter", "grammar_sha", "repo_head", "repo_dirty",
              "cpu_affinity"):
        if k in env:
            L.append(f"| {k} | `{env[k]}` |")
    L.append(f"| RAM | {_mib(env['ram_bytes'])} |")
    for label, c in env["corpora"].items():
        L.append(f"| corpus {label} | `{c['root']}` at `{c['head']}` |")
    lib = env.get("native_library")
    if isinstance(lib, dict):
        L.append(f"| native library | `{lib['compiler_version']}`; flags `{' '.join(lib['flags'])}`; "
                 f"{lib['built_by']}; from `{lib['probe']}`; al.dll PE linker {lib['library_pe_linker_version']} |")
    for when in ("load_at_start", "load_at_end"):
        if when in env:
            ld = env[when]
            top = ld.get("top5_outside_our_tree") or ld.get("top5")
            extra = f"; top: {', '.join(top)}; {ld['cpu_mhz']:.0f} MHz (psutil's base-clock figure); plan {ld['power_plan']}" if top else ""
            L.append(f"| {when.replace('_', ' ')} | CPU {ld['cpu_percent_2s']}% over 2 s, "
                     f"{_mib(ld['ram_available_bytes'])} RAM free{extra} |")
    drv = env.get("amd_3d_vcache_driver")
    if drv:
        L.append(f"| AMD 3D V-Cache driver | {drv} |")
    topo = env.get("cpu_topology")
    if topo:
        L += ["", "## CPU topology and placement", "",
              f"Read from {topo['source']}:", "",
              "| CCD | L3 | logical CPUs | SMT pairs |", "|---|---:|---|---|"]
        for i, c in enumerate(topo["ccds"]):
            L.append(f"| {i} | {c['l3_bytes'] >> 20} MiB | {c['cpus'][0]}-{c['cpus'][-1]} | "
                     f"{' '.join('/'.join(map(str, p)) for p in c['smt_pairs'])} |")
        pin = env.get("single_thread_pin", {})
        L += ["", f"**Single-threaded groups (native, wasm's node process, incremental, ab) are pinned to "
              f"{pin.get('why', '?')}.** The parallel groups use every logical CPU, so they span both "
              "CCDs and carry the two CCDs' asymmetry (cache against clock) inside every figure. The "
              "measured difference between the CCDs is in the notes below."]
    L += ["", "`grammar_sha` is the oracle's hash (first 16 hex digits of sha256 over grammar.js, "
          "src/scanner.c, src/parser.c and src/**/*.h): the same inputs, so an oracle report and a "
          "perf result with equal hashes measured the same parser. Each group below says when it was "
          "measured, over which corpora, and the load outside the measuring process tree while it ran "
          "(tools/perf/load.py).", ""]

    if "native" in g:
        n = g["native"]
        per = n.get("read_seconds_per_corpus")
        L += ["## Native throughput (py-tree-sitter, in-process)", "", _measured(n), "",
              f"Files are read into memory first ({n['read_seconds']:.2f} s for all of them"
              + (" -- " + ", ".join(f"{k} {v:.2f} s" for k, v in per.items()) if per else "")
              + f", not included below). Then one discarded warm-up pass and {n['repeats']} timed passes; "
              f"each cell is the median with the (min-max) over the passes. *Single* times only "
              f"`parser.parse()`, one file at a time in one process. *Parallel* is wall time for "
              f"{n['workers']} worker processes (the oracle's default `--workers`, logical cores - 1) "
              f"reading the sources from one shared-memory block, {n['chunk']} files per task."
              + (f" Single-threaded passes spread {n['single_spread_percent']}% (warned above 2%)."
                 if "single_spread_percent" in n else "")
              + (f" The single-threaded thread was pinned to CPU {n['single_pin']['pinned_to']} and ran on "
                 f"{n['single_pin']['ran_on']} (CPU: parses)." if "single_pin" in n else
                 " The single-threaded run was **not pinned** (measured before fix round 2)."), "",
              "| corpus | files | size | has_error | single files/s | single MiB/s | parallel files/s | parallel MiB/s |",
              "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for name, c in n["corpora"].items():
            L.append(f"| {name} | {c['files']:,} | {_mib(c['bytes'])} | {c['has_error']} | "
                     f"{_t(c['single']['files_per_s'], '{:,.0f}')} | {_t(c['single']['mib_per_s'], '{:.2f}')} | "
                     f"{_t(c['parallel']['files_per_s'], '{:,.0f}')} | {_t(c['parallel']['mib_per_s'], '{:.1f}')} |")
        L += ["", "Per-file latency, ms (single-threaded; each file's median over the timed passes):", "",
              "| corpus | p50 | p95 | p99 | max | mean |", "|---|---:|---:|---:|---:|---:|"]
        for name, c in n["corpora"].items():
            lt = c["latency_ms"]
            L.append(f"| {name} | {lt['p50']:.2f} | {lt['p95']:.2f} | {lt['p99']:.2f} | {lt['max']:.1f} | {lt['mean']:.2f} |")
        L += ["", "Files with `has_error` (the sanity column; BCApps is known to have 2 visible-error files):", ""]
        L += [f"- `{f}`" for k, c in n["corpora"].items() if k != "combined" for f in c["has_error_files"]] or ["- none"]
        L += ["", "The 10 slowest files (all corpora):", "", "| file | bytes | ms |", "|---|---:|---:|"]
        L += [f"| `{s['file']}` | {s['bytes']:,} | {s['ms']:.1f} |" for s in n["corpora"]["combined"]["slowest"]]
        L.append("")

    if "native_zig" in g or "native" in g:
        L += _compiler_section(g)

    if "wasm" in g:
        w = g["wasm"]
        d = w["has_error_disagreements"]
        L += ["## WASM throughput (web-tree-sitter under Node, single-threaded)", "", _measured(w), "",
              f"`tree-sitter-al.wasm` ({w['wasm_bytes']:,} bytes, checked fresh with "
              f"`tools/check-wasm-fresh.sh`), web-tree-sitter {w['web_tree_sitter']}. Same file list, "
              f"read first ({w['read_seconds']:.2f} s); each file is decoded to a JS string outside "
              f"the timed region (a UTF-8 BOM kept; UTF-16 decoded as UTF-16, as natively), so only "
              f"`parser.parse()` is timed. Warm-up discarded, {w['repeats']} timed passes.", "",
              "| corpus | files | has_error | files/s | MiB/s | p50 ms | p95 ms | p99 ms | max ms |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for name, c in w["corpora"].items():
            lt = c["latency_ms"]
            L.append(f"| {name} | {c['files']:,} | {c['has_error']} | {_t(c['single']['files_per_s'], '{:,.0f}')} | "
                     f"{_t(c['single']['mib_per_s'], '{:.2f}')} | {lt['p50']:.2f} | {lt['p95']:.2f} | "
                     f"{lt['p99']:.2f} | {lt['max']:.1f} |")
        L += ["", f"**has_error agreement with native, per file:** "
              + ("every file agrees." if not (d["wasm_only"] or d["native_only"]) else
                 f"{len(d['wasm_only'])} files error only in WASM, {len(d['native_only'])} only natively "
                 "-- a finding, listed in the JSON."),
              f"Files that are not valid UTF-8 (decoded with U+FFFD replacement in WASM only): "
              f"{len(w['invalid_utf8_files'])}" + (f" (`{w['invalid_utf8_files'][0]}`)" if len(w['invalid_utf8_files']) == 1 else "") + ".", ""]

    if "incremental" in g:
        i = g["incremental"]
        short = i.get("quota_shortfalls") or {}
        L += ["## Fresh against incremental equivalence", "", _measured(i), "",
              f"Seed `{i['seed']}`, {i['sample_size']} files ({', '.join(f'{k} {v}' for k, v in i['categories'].items())}; "
              f"{i['files_with_if']} with `#if`, {i['bom_files']} with a UTF-8 BOM, {i['crlf_files']} with CRLF)"
              + ("; quotas a corpus could not fill: " + "; ".join(f"{lab} " + ", ".join(f"{c} short {k}" for c, k in cs.items())
                                                            for lab, cs in short.items()) if short else "")
              + ". Each file gets every applicable edit kind once from the original tree (*independent*), "
              "then the same kinds again one after another, each reusing the previous incremental tree "
              "(*chain*). Per edit: `Tree.edit()` with byte offsets and points, `parse(new, old)`, "
              "`parse(new)`, and two checks: the complete cursor-derived trees compared (every node, named "
              "and anonymous: type, grammar symbol, named/missing/extra, field, byte and point spans, "
              "`has_error`); and the **edit points** -- every node of the edited old tree wholly after "
              "the edit must carry the fresh tree's points, which is the only place a wrong point "
              "argument shows (tree-sitter recomputes positions from bytes when it reparses).", "",
              f"- edits checked: **{i['edits_checked']:,}**; mismatches: **{i['mismatches']}**",
              "- independent edits per kind: " + ", ".join(f"{k} {v}" for k, v in i["edits_per_kind_independent"].items()),
              f"- incremental parse, ms: p50 {i['incremental_ms']['p50']:.2f}, p95 {i['incremental_ms']['p95']:.2f}, "
              f"max {i['incremental_ms']['max']:.1f}",
              f"- fresh parse of the same text, ms: p50 {i['fresh_ms']['p50']:.2f}, p95 {i['fresh_ms']['p95']:.2f}, "
              f"max {i['fresh_ms']['max']:.1f}",
              f"- incremental / fresh time per edit: median **{i['speed_ratio_incremental_over_fresh']['median']:.3f}**, "
              f"p95 {i['speed_ratio_incremental_over_fresh']['p95']:.3f}", ""]
        if i["mismatches"]:
            L += ["Mismatches (see docs/deferred-work.md):", "",
                  *(f"- `{m['file']}` {m['mode']} {m['kind']} at byte {m['start']} ({m.get('check', 'tree')})"
                    for m in i["mismatch_details"]), ""]

    if "build" in g:
        b = g["build"]
        L += ["## Build and size", "", _measured(b), "",
              "| | |", "|---|---|",
              f"| `tree-sitter generate`, s | {_t(b['generate'])} (warm-up discarded, median of 3) |",
              f"| native build, s (`{b['build_command']}`) | {_t(b['build'])} (median of 3) |",
              f"| `generate` left src/ byte-identical | {'yes' if b['src_unchanged_by_generate'] else 'NO: ' + b['git_diff_stat_src']} |",
              f"| src/parser.c | {b['parser_c_mib']} MiB ({b['parser_c_bytes']:,} bytes) |",
              f"| STATE_COUNT / LARGE_STATE_COUNT / SYMBOL_COUNT | {b['STATE_COUNT']:,} / {b['LARGE_STATE_COUNT']:,} / {b['SYMBOL_COUNT']:,} |",
              f"| LANGUAGE_VERSION (ABI) | {b['LANGUAGE_VERSION']} |",
              f"| tree-sitter-al.wasm | {b['wasm_bytes']:,} bytes ({_mib(b['wasm_bytes'])}) |", ""]

    if "oracle" in g:
        o = g["oracle"]
        q = o["quick"]
        L += ["## Config oracle", "", _measured(o), "",
              "Wall time and memory of the whole process tree (ts-lock's bash, the oracle, and all "
              f"{o['workers']} workers), sampled every 250 ms. *Aggregate* is the peak of the SUM of RSS "
              "(Windows: working set) over the tree; *per-process max* is the largest single process, "
              "which is what the oracle's own `peak RSS (max over processes)` line reports. *Private sum* "
              "is the peak sum of private (committed) bytes: it never counts a shared page twice, but it "
              "counts memory committed and not resident, so it can exceed the RSS sum. The quick tier "
              "lasts ~2 s, so its memory rests on ~8 samples: a coarse figure.", "",
              "| tier | runs | wall, s | aggregate peak | per-process max | private sum |", "|---|---:|---:|---:|---:|---:|",
              f"| quick | {q['repeats']} (+1 warm-up) | {_t(q['seconds'])} | {_mib(q['peak_rss_sum_bytes'])} | "
              f"{_mib(q['peak_rss_single_process_bytes'])} | {_mib(q['peak_private_sum_bytes'])} |"]
        if "full" in o:
            f = o["full"]
            L += [f"| full, {len(f['roots'])} corpora | 1 (no warm-up) | {f['seconds']:.0f} | {_mib(f['peak_rss_sum_bytes'])} | "
                  f"{_mib(f['peak_rss_single_process_bytes'])} | {_mib(f['peak_private_sum_bytes'])} |", "",
                  f"Full tier over {', '.join(f'`{x}`' for x in f['roots'])}: exit code {f['exit_code']}, "
                  f"{f['samples']} samples, up to {f['peak_processes']} processes. The oracle's own line for "
                  f"the same run: `{f['oracle_own_peak_rss_line']}`."]
        L.append("")

    if notes:
        L += [notes.rstrip(), ""]
    L += CAVEATS
    return "\n".join(L) + "\n"


def _compiler_section(g):
    n, z, w, ab = g.get("native"), g.get("native_zig"), g.get("wasm"), g.get("ab")
    L = ["## Compiler sensitivity", "",
         "The native figures above are **`tree-sitter build`'s MSVC `-O2` library** -- what a user of "
         "the CLI, the loader and the Windows bindings gets on this machine (see the environment "
         "table for the exact compiler and flags). The grammar DLL's own code (the generated lexer "
         "and parse tables, and the scanner) is compiler-sensitive: the same `src/parser.c` and "
         "`src/scanner.c` built with clang `-O2` (`zig cc -shared -O2`, `native --cc zig`) parse "
         "identical trees about twice as fast. **Compare native with native built by the same "
         "compiler and flags**; `compare` warns when they differ. `docs/deferred-work.md` item 21.", ""]
    if ab and "ratio_a_over_b" in ab:
        q = ab["ratio_a_over_b"]
        L += ["The decision-grade figure is a same-session interleaved A/B run "
              f"(`python -m tools.perf ab`, {ab['rounds']} rounds `{ab['order']}`, pinned to CPU "
              f"{ab['pin']['pinned_to']}, over {'+'.join(ab['corpora'])}, {ab['files']:,} files, every tree "
              "checked identical first):", "", _measured(ab), "",
              "| library | median pass, s |", "|---|---:|",
              f"| A `{ab['lib_a']['path']}` | {stats_median(ab['seconds']['A']):.3f} |",
              f"| B `{ab['lib_b']['path']}` | {stats_median(ab['seconds']['B']):.3f} |", "",
              f"**time A / time B = {q['median']:.3f}** (per-round min {q['min']:.3f}, max {q['max']:.3f}; "
              f"95% CI of the median {q['ci95_median'][0]:.3f}-{q['ci95_median'][1]:.3f}).", ""]
    if z and n:
        L += ["Throughput with the clang build (a separate run, so not decision-grade against the "
              "MSVC table: see *Session drift* below):", "", _measured(z), "",
              "| corpus | clang -O2 files/s |", "|---|---:|"]
        L += [f"| {k} | {c['single']['files_per_s']['median']:,.0f} |" for k, c in z["corpora"].items()]
        L.append("")
    if w and n:
        nat, wa = (x["corpora"]["combined"]["single"]["seconds"]["median"] for x in (n, w))
        same = (w.get("meta") or {}).get("started") == (n.get("meta") or {}).get("started") or             (w.get("meta") or {}).get("command") == (n.get("meta") or {}).get("command")
        L += [f"WASM against MSVC native, single-threaded, all corpora: WASM takes {wa / nat:.2f}x the "
              "MSVC time" + (" (same session)" if same else " (different sessions)") + ". The only claim "
              "this supports is \"WASM is faster than the MSVC-built native library\"; nothing here "
              "compares WASM with a clang-built native library in one session.", ""]
    return L


def stats_median(xs):
    from tools.perf import stats
    return stats.median(xs)


CAVEATS = """## Reproducing and comparing

```bash
python -m tools.perf baseline                       # every group, all 4 corpora (~35 min); writes
                                                    # docs/perf/baseline-<date>.json and this file
python -m tools.perf baseline --groups native,build --out DIR   # a subset needs --out
python -m tools.perf native      [--corpus LABEL ...] [--out DIR]   # one group at a time; the
python -m tools.perf native --cc zig                                # (clang -O2 library)
python -m tools.perf wasm        [--corpus LABEL ...] [--out DIR]   # result goes to
python -m tools.perf incremental [--corpus LABEL ...] [--out DIR]   # tools/perf/reports/ unless
python -m tools.perf build                                          # --out says otherwise
python -m tools.perf oracle      [--no-full]
python -m tools.perf ab --lib-a A.dll --lib-b B.dll [--corpus LABEL] [--rounds N]  # DECISIONS
python -m tools.perf compare OLD.json NEW.json [--floor F]   # context: delta and relative change
python -m tools.perf merge BASE.json [NEW.json] [--drop GROUP]   # replace/drop BASE's groups
python -m tools.perf.pin [calibrate N]              # the CCD map, the pin, cache vs frequency CCD
python -m tools.perf render docs/perf/baseline-<date>.json          # re-render this file
python -m tools.perf.load 120                       # calibrate the idle outside-CPU floor
```

Corpus labels are the oracle's (`tools/config_oracle/__main__.CORPORA`): `bc-history`, `dc`,
`bc28.1` (`AL_BC28_ROOT`), `bcapps-29.0` (`AL_BCAPPS29_ROOT`). `incremental` exits 1 on any
mismatch; the others exit 0 when they complete.

`compare` flags `!` when a median moved by more than the larger of either run's spread
(max - min) and a noise floor (5% of the old median single-threaded, 10% parallel,
`--floor`), and `?` when an exact count changed (files, has_error, STATE_COUNT). A float with no
measured spread (a percentile, a single run) is printed without a flag: its noise is not known.
A group measured over a different corpus set compares only its per-corpus entries; every
aggregate (`combined`, the incremental sample, the oracle's full tier) prints `n/c`, never a
delta. A difference in the native library's compiler or flags is a `WARNING` line at the top.
No pass/fail thresholds: those are roadmap D2's.

## What the numbers mean, and caveats

- **Timing** is `time.perf_counter_ns` (Node: `process.hrtime.bigint`). A warm-up pass is
  discarded, then 3 passes; figures are the median and (min-max). Only the parse call is timed.
- **Reading** the files is timed on its own, per corpus (the roots sit on two drives), and is
  reported, never compared. Its cause of variation is **not known**: the same 70,355 files took
  11 s in one run and 298 s five minutes after another read them in 7 s, with ~44 GiB free.
  Candidates, none shown: on-access scanning, the H: drive's own caching, the file cache's
  standby-list policy.
- **Percentiles** are linear interpolation between closest ranks (numpy's default), over each
  file's median time across the passes. p99 over ~70k files is well sampled; `max` is one file.
- **Parallel** throughput is bounded by the slowest chunk at the end of the pass and by the
  machine's other load; it is the number to compare between runs on the same machine, not a
  scaling law. Its within-run spread under-states run-to-run noise: an independent re-run of
  `native` on the same idle machine moved `dc` (a 0.13 s pass) by 6% and `bc28.1` by 2.4%,
  beyond the recorded spread, while every single-threaded figure stayed inside it. Treat a
  parallel delta under ~5% (under ~10% for `dc`) as noise. The parallel groups run on both
  CCDs (96 MiB-L3 cache CCD and 32 MiB-L3 frequency CCD), so each figure mixes the two.
- **Session drift: cross-session comparisons are informational only.** On 2026-09-30 the same
  `al.dll`, with clean load, measured DC single-threaded at 1.527-1.589 s in some sessions and
  2.016-2.023 s in another (+31%; clang +29%), and the four corpora moved +3.3-3.6% between
  two runs 80 minutes apart. Placement is part of it: unpinned, which CCD the thread landed on
  moved a DC pass ~12%, and pinned calibrations still show machine-wide episodes where every
  CPU runs 15-20% slow for a few passes. Pinning (above) removes the placement term, not the
  episodes. So: a single-threaded delta between two runs made at different times is **never a
  decision**. `compare` prints `CROSS-SESSION ... not decision-grade` for such groups, applies a
  noise floor (5% single-threaded, 10% parallel, `--floor`), and warns when the CPU or the pin
  differs. **Decisions -- "is B faster than A" -- use `python -m tools.perf ab`**: both
  libraries in one process, on the pinned CPU, interleaved ABBA, trees checked identical, with a
  ratio and its confidence interval. The baselines are context, not the yardstick.
- **Load.** Each group is sampled every second for CPU used by processes **outside** the
  measuring process tree (system busy CPU minus the tree's), in logical cores. The idle
  workstation measured mean 2.9-3.4, p95 5.0-5.9 and max 6.0-10.3 cores (desktop apps only). A
  group is FLAGGED when the max exceeds 11.5 cores (idle max + one core: a burst beyond anything
  the idle machine does) or the mean exceeds 4.5 cores (idle mean + one core: one competing thread
  held for the whole group; applied only from 60 samples up, since a ~12-sample group read a
  clean mean of 4.6 once in three). A start-only 20% rule could not see one competing thread
  (3% of 32 threads) and passed a run that came out 20% slow. The native group also warns when
  its single-threaded passes spread more than 2%. The monitor sees load; it does **not** see
  the session drift above, which happened with clean readings.
- **Memory**: RSS sums count shared pages (the parser DLL mapped by every worker) once per
  process, so the aggregate over-states physical use. The private sum (Windows only) counts
  no shared page twice but is commit charge, not residency, so it can be the larger. Sums are
  sampled every 250 ms and can miss a shorter peak; the per-process max uses Windows' exact
  lifetime peak working set (`peak_wset`) where available.
- **Incremental equivalence** covers only the edit kinds listed, at one pseudo-random site per
  kind per file; it proves nothing about other edits. The seed is fixed so a later run edits
  the same sites while the corpora and the parser are unchanged.
- `benchmark.sh` (`tree-sitter parse` over BC.History, appending to the untracked
  `benchmark-results.txt`) measures CLI wall time including process start and I/O; it is kept,
  and is not comparable with these numbers.
""".splitlines()
