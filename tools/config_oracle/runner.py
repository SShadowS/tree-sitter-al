"""Discovery, worker pool, per-(input, configuration) accounting (spec section 4).

Nothing is skipped silently: the parent predicts every (input, configuration)
with `discover` before dispatching, and a run whose records differ from that
prediction in any way raises `IncompleteRun` (exit 2).
"""
from __future__ import annotations

import collections
import ctypes
import json
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path

from tools.config_oracle import compare, directive_check, directives, ir, reference, representation
from tools.config_oracle.lowering import lower_tree
from tools.config_oracle.lowering.engine import LoweringError

INTERNAL = "internal-error"


class IncompleteRun(RuntimeError):
    pass


@dataclass
class Record:
    input_id: str
    config: str
    status: str
    items: list = field(default_factory=list)


@dataclass
class Summary:
    records: list
    no_directives: int
    elapsed_s: float
    peak_rss_bytes: int
    exit_code: int
    classified: int = 0


def peak_rss_bytes() -> int:
    if sys.platform == "win32":
        class PMC(ctypes.Structure):
            _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
        pmc = PMC()
        pmc.cb = ctypes.sizeof(PMC)
        k32 = ctypes.WinDLL("kernel32")
        k32.GetCurrentProcess.restype = ctypes.c_void_p
        ctypes.WinDLL("psapi").GetProcessMemoryInfo(ctypes.c_void_p(k32.GetCurrentProcess()),
                                                    ctypes.byref(pmc), pmc.cb)
        return int(pmc.PeakWorkingSetSize)
    import resource
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def first_zero_width_leaf(root):
    """Start of the first zero-width leaf BELOW the root, or None. The comparator is not
    sound for them. A childless root is not one: it is the empty file of a configuration
    whose whole text is inactive, and `leaves()` would report the root itself."""
    if not root.children:
        return None
    for leaf in root.leaves():
        if leaf.start == leaf.end:
            return leaf.start
    return None


def _internal(e):
    return f"{INTERNAL}:{type(e).__name__}:{e}\n{traceback.format_exc()}"


def _file_level(parser, input_id, source, disc):
    """The multi-configuration tree and the checks that need no configuration."""
    root, extras, problems = ir.from_tree(parser.parse(source))
    rep = [compare.discrepancy_id(input_id, "-", d) for d in representation.check(root)]
    if disc is None:
        return (root, extras, []), rep
    file_items = ["multi-config-parse:" + ",".join(problems)] if problems else []
    file_items += [compare.discrepancy_id(input_id, "-", d) for d in directive_check.check(root, disc)]
    return (root, extras, file_items), rep


def _check_config(parser, input_id, source, cid, env, mode, prep):
    """A file-level directive discrepancy does NOT short-circuit: the configuration is still
    resolved, lowered and compared, and the record is `directive-mismatch` carrying the
    directive items ahead of whatever that run produced (a pass contributes nothing).

    Never when the multi-configuration tree has errors: its directive items are then
    unreliable. That is decided on the FILE-level items, because a resolver or reference
    failure returns before the per-configuration record ever sees `multi-config-parse`."""
    rec = _check_config_inner(parser, input_id, source, cid, env, mode, prep)
    file_items = prep[2] if isinstance(prep, tuple) else []
    dir_items = [i for i in file_items if "|directive|" in i]
    if dir_items and not any(i.startswith("multi-config-parse") for i in file_items):
        return Record(input_id, cid, "directive-mismatch", dir_items + rec.items)
    return rec


def _check_config_inner(parser, input_id, source, cid, env, mode, prep):
    try:
        res = directives.resolve(source, env)
    except directives.ResolveError as e:
        return Record(input_id, cid, "cannot-validate", [f"resolver:{e.reason}@{e.offset}"])
    ref = reference.extract(parser, res.masked)
    if ref.problems:
        return Record(input_id, cid, "cannot-validate", ["reference-error:" + ",".join(ref.problems)])
    if mode == "resolve":
        return Record(input_id, cid, "pass")
    root, extras, file_items = prep
    if any(i.startswith("multi-config-parse") for i in file_items):
        return Record(input_id, cid, "cannot-validate", file_items)
    z = first_zero_width_leaf(ref.root)
    if z is not None:
        return Record(input_id, cid, "cannot-validate", [f"zero-width-leaf@{z}"])
    try:
        low, low_extras, normalised = lower_tree(root, extras, res)
    except LoweringError as e:
        return Record(input_id, cid, "cannot-validate", [f"lowering:{e.kind}:{e}"])
    z = first_zero_width_leaf(low)
    if z is not None:
        return Record(input_id, cid, "cannot-validate", [f"zero-width-leaf@{z}"])
    # Coverage is measured against the ORIGINAL bytes on both sides, never the masked text.
    ds = (compare.coverage(source, res.active, ref.root, ref.extras, "ref")
          + compare.coverage(source, res.active, low, low_extras, "low")
          + compare.structure(ref.root, low)
          + compare.leaf_boundaries(ref.root, low)
          + compare.trivia(res.extras, ref.extras, low_extras))
    items = [compare.discrepancy_id(input_id, cid, d) for d in ds]
    # Each empty-container removal is reported (spec section 2); it never changes the status.
    notes = [f"normalised:{n}" for n in normalised]
    return Record(input_id, cid, "discrepancy" if items else "pass", items + notes)


def check_input(parser, input_id, source, mode="full"):
    """One record per configuration `discover` predicts; one `-` record if discovery fails.

    `mode="full"` lowers and runs every check; `mode="resolve"` runs the resolver and the
    reference parse only. An exception inside the oracle itself becomes an `internal-error`
    record for that configuration (never a dropped one), and makes the run exit 2.

    Representation contracts are checked FIRST, on the multi-configuration tree: when any
    is violated, every record of the input is `representation-violation`, carrying those
    items ahead of whatever else applied, so no earlier cannot-validate can hide one.
    """
    try:
        disc = directives.discover(source)
    except directives.ResolveError as e:
        disc, records = None, [Record(input_id, "-", "cannot-validate", [f"resolver:{e.reason}@{e.offset}"])]
    prep, rep = None, []
    if mode == "full":
        try:
            prep, rep = _file_level(parser, input_id, source, disc)
        except Exception as e:  # noqa: BLE001 -- recorded, not swallowed
            prep = _internal(e)
    if disc is not None:
        records = []
        for env in directives.configurations(disc):
            cid = directives.config_id(env, disc.free_symbols)
            if isinstance(prep, str):
                records.append(Record(input_id, cid, "cannot-validate", [prep]))
                continue
            try:
                records.append(_check_config(parser, input_id, source, cid, env, mode, prep))
            except Exception as e:  # noqa: BLE001 -- recorded, not swallowed
                records.append(Record(input_id, cid, "cannot-validate", [_internal(e)]))
    if disc is None and isinstance(prep, str):
        records[0].items.append(prep)
    if rep:
        for r in records:
            r.status, r.items = "representation-violation", rep + r.items
    return records


_PARSER = None


def _init(lib_path):
    global _PARSER
    from tools.query_coverage import loader
    lib = Path(lib_path) if lib_path else loader.ensure_library(loader.REPO_ROOT)
    _PARSER = loader.make_parser(loader.load_language(lib))


def _work(args):
    input_id, source, mode = args
    return check_input(_PARSER, input_id, source, mode), peak_rss_bytes()


def _expected(inputs):
    """-> ({input_id: [config ids]}, no-directives count, dispatch list)."""
    expected, no_dir, todo = {}, 0, []
    for input_id, source in inputs:
        if input_id in expected:
            raise ValueError(f"duplicate input id: {input_id}")
        try:
            disc = directives.discover(source)
        except directives.ResolveError:
            expected[input_id] = ["-"]
        else:
            if not disc.has_conditionals:
                no_dir += 1
                continue
            expected[input_id] = [directives.config_id(e, disc.free_symbols)
                                  for e in directives.configurations(disc)]
        todo.append(input_id)
    return expected, no_dir, todo


def is_classified(record, classes):
    """A representation violation is never classified: fixture-classes cannot excuse one."""
    if record.status == "representation-violation":
        return False
    for key in ((record.input_id, record.config), (record.input_id, "*")):
        if key in classes and classes[key][0] == record.status:
            return True
    return False


def run(inputs, lib_path, workers, mode, classes=None):
    t0 = time.perf_counter()
    classes = classes or {}
    expected, no_dir, todo = _expected(inputs)
    sources = dict(inputs)
    jobs = [(i, sources[i], mode) for i in todo]
    records, peak = [], peak_rss_bytes()
    if workers <= 1:
        _init(lib_path)
        results = map(_work, jobs)
        for recs, p in results:
            records.extend(recs)
            peak = max(peak, p)
    else:
        from tools.query_coverage import loader
        lib = str(lib_path or loader.ensure_library(loader.REPO_ROOT))   # built ONCE, before workers
        with ProcessPoolExecutor(workers, initializer=_init, initargs=(lib,)) as pool:
            for recs, p in pool.map(_work, jobs, chunksize=8):
                records.extend(recs)
                peak = max(peak, p)
    got = collections.defaultdict(list)
    for r in records:
        got[r.input_id].append(r.config)
    for input_id in sorted(set(expected) | set(got)):
        want, have = sorted(expected.get(input_id, [])), sorted(got.get(input_id, []))
        if want != have:
            raise IncompleteRun(f"{input_id}: expected {want}, got {have}")
    n_classified = sum(r.status != "pass" and is_classified(r, classes) for r in records)
    validated = sum(r.status != "cannot-validate" for r in records)
    if validated == 0 or any(i.startswith(INTERNAL) for r in records for i in r.items):
        code = 2
    else:
        code = 0 if all(r.status == "pass" or is_classified(r, classes) for r in records) else 1
    return Summary(records, no_dir, time.perf_counter() - t0, peak, code, n_classified)


def reason_of(record):
    """Coarse reason for grouping cannot-validate records: `lowering:unsupported-type`, `zero-width-leaf`."""
    head = record.items[0] if record.items else "unknown"
    return _coarse(head)


def _coarse(item):
    return ":".join(item.split("@", 1)[0].split(":")[:2])


_NOT_VALIDATED = ("resolver:", "reference-error:", "lowering:", "zero-width-leaf@", INTERNAL)


def unvalidated_reason(record):
    """For a directive-mismatch record: the coarse reason its comparison did not run, or None."""
    item = next((i for i in record.items if i.startswith(_NOT_VALIDATED)), None)
    return None if item is None else _coarse(item)


def write_report(summary, out_dir: Path, header: dict, classes=None):
    classes = classes or {}
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "findings.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for r in summary.records:
            f.write(json.dumps({**asdict(r), "classified": r.status != "pass" and is_classified(r, classes)}) + "\n")
    counts = collections.Counter(r.status for r in summary.records)
    reasons = collections.Counter(reason_of(r) for r in summary.records if r.status == "cannot-validate")
    unclassified = sum(r.status not in ("pass", "cannot-validate") and not is_classified(r, classes)
                       for r in summary.records)
    top = ", ".join(f"{k} {v}" for k, v in reasons.most_common(8)) or "none"
    # A directive-mismatch record still ran its configuration; when that run stopped early,
    # the configuration was not validated either, and must not drop out of the count.
    dm = collections.Counter(filter(None, (unvalidated_reason(r) for r in summary.records
                                           if r.status == "directive-mismatch")))
    dm_top = ", ".join(f"{k} {v}" for k, v in dm.most_common(8)) or "none"
    lines = ["# Config-oracle report", "", *(f"- {k}: {v}" for k, v in sorted(header.items())), "",
             f"**{unclassified} unclassified findings, {summary.classified} classified, "
             f"{counts['cannot-validate']} configurations not validated ({top})**", "",
             f"- configurations checked: {len(summary.records)}",
             f"- directive-mismatch configurations also not validated: {sum(dm.values())} ({dm_top})",
             *(f"- {k}: {v}" for k, v in sorted(counts.items())),
             f"- inputs without conditional directives: {summary.no_directives}",
             f"- elapsed: {summary.elapsed_s:.1f}s",
             f"- peak RSS (max over processes): {summary.peak_rss_bytes / 2**20:.0f} MiB",
             f"- exit code: {summary.exit_code}"]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
