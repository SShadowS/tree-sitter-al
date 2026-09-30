"""The parts of tools/perf that can go wrong silently."""
import random
import time
import subprocess
import sys

import pytest

from tools.perf import incremental as inc
from tools.perf import report, stats
from tools.perf.procs import TreeSampler

# ---- percentile maths -----------------------------------------------------------------


def test_percentile_is_linear_interpolation():
    xs = [4, 1, 3, 2]                       # unsorted on purpose
    assert stats.percentile(xs, 0) == 1
    assert stats.percentile(xs, 100) == 4
    assert stats.percentile(xs, 50) == 2.5
    assert stats.percentile(xs, 95) == pytest.approx(3.85)   # numpy.percentile([1,2,3,4], 95)
    assert stats.percentile(list(range(1, 101)), 99) == pytest.approx(99.01)
    assert stats.percentile([7], 99) == 7


def test_percentile_rejects_bad_input():
    with pytest.raises(ValueError):
        stats.percentile([], 50)
    with pytest.raises(ValueError):
        stats.percentile([1], 101)


def test_spread_and_latency():
    assert stats.spread([3, 1, 2]) == {"median": 2, "min": 1, "max": 3, "runs": [3, 1, 2]}
    lt = stats.latency([1.0, 2.0, 3.0, 10.0])
    assert lt["max"] == 10.0 and lt["mean"] == 4.0 and lt["p50"] == 2.5


# ---- compare --------------------------------------------------------------------------

def _result(median, lo, hi, count=5):
    return {"env": {"cpu": "x"}, "groups": {"native": {"corpora": {"dc": {
        "files": count, "single": {"seconds": {"median": median, "min": lo, "max": hi, "runs": [lo, median, hi]}},
        "slowest": [{"file": "ignored", "ms": 1.0}]}}}}}


def _rows(lines):
    return {l.split()[0]: l for l in lines[1:] if not l.startswith("env ")}


def test_compare_self_is_all_zero():
    lines = report.compare(_result(10.0, 9.0, 11.0), _result(10.0, 9.0, 11.0))
    rows = _rows(lines)
    assert set(rows) == {"native.corpora.dc.files", "native.corpora.dc.single.seconds"}
    for line in rows.values():
        parts = line.split()
        assert parts[3] in ("0", "0.0") and parts[4] == "+0.00%" and len(parts) == 5   # no flag


def test_compare_flags_beyond_spread_only():
    within = _rows(report.compare(_result(10.0, 9.0, 11.0), _result(11.5, 11.0, 12.0)))
    assert not within["native.corpora.dc.single.seconds"].rstrip().endswith("!")   # 1.5 <= spread 2
    beyond = _rows(report.compare(_result(10.0, 9.5, 10.5), _result(12.0, 11.8, 12.2)))
    line = beyond["native.corpora.dc.single.seconds"]
    assert line.rstrip().endswith("!") and line.split()[3:5] == ["2", "+20.00%"]


def test_compare_marks_unspread_changes_and_missing_metrics():
    new = _result(10.0, 9.0, 11.0, count=6)
    new["groups"]["wasm"] = {"wasm_bytes": 3}
    new["env"]["cpu"] = "y"
    lines = report.compare(_result(10.0, 9.0, 11.0), new)
    rows = _rows(lines)
    assert rows["native.corpora.dc.files"].rstrip().endswith("?")
    assert rows["wasm.wasm_bytes"].rstrip().endswith("+")
    assert "env cpu: 'x' -> 'y'" in lines


# ---- edit application: offsets and points ---------------------------------------------

def test_point_counts_bytes_and_rows_on_newline_only():
    src = "ab\r\næø x\n".encode("utf-8")        # CRLF, then two 2-byte characters
    assert inc.point_at(src, 0) == (0, 0)
    assert inc.point_at(src, 3) == (0, 3)         # the \n itself: \r is an ordinary column
    assert inc.point_at(src, 4) == (1, 0)
    assert inc.point_at(src, src.index(b"x")) == (1, 5)   # 5 bytes, 3 characters
    assert inc.point_at(src, len(src)) == (2, 0)


def test_edit_args_new_end_point_is_in_the_new_source():
    src = b"a\r\nb"
    e = inc.Edit("t", 1, 3, "\r\næ\r\n".encode())   # replace CRLF with CRLF, 2-byte char, CRLF
    args = inc.edit_args(src, e)
    assert e.apply(src) == "a\r\næ\r\nb".encode()
    assert (args["start_byte"], args["old_end_byte"], args["new_end_byte"]) == (1, 3, 7)
    assert args["start_point"] == (0, 1) and args["old_end_point"] == (1, 0)
    assert args["new_end_point"] == (2, 0)


MULTI = ("﻿codeunit 50100 \"Tést\"\r\n{\r\n    var\r\n        Æble: Integer; // kommentär ø\r\n"
         "    /* blök ü */\r\n    trigger OnRun()\r\n    begin\r\n#if CLEAN24\r\n        Æble := 1;\r\n"
         "#else\r\n        Message('smørrebrød');\r\n#endif\r\n    end;\r\n}\r\n").encode("utf-8")


def test_sites_are_utf8_safe_and_incremental_equals_fresh(al_parser):
    tree = al_parser.parse(MULTI)
    edits = inc.sites(MULTI, tree, random.Random(1))
    kinds = {e.kind for e in edits}
    assert {"ident_insert", "ident_delete", "if_eol_formfeed", "endif_newline", "line_comment_insert",
            "block_comment_insert", "string_insert", "else_line_delete"} <= kinds
    for e in edits:
        e.apply(MULTI).decode("utf-8")               # never splits a character
        mismatches, timings = [], []
        inc.check(al_parser, "t", MULTI, e, tree.copy(), mismatches, timings, "independent")
        assert mismatches == [], e
    assert [e for e in edits if e.kind == "endif_newline"][0].new == b"\r\n"   # the file's EOL


def test_pipeline_detects_a_missing_tree_edit(al_parser):
    """The check can fail: reparse with an old tree that was NOT told about the edit."""
    src = b"codeunit 1 A { trigger OnRun() begin X := 1; end; }"
    new = src.replace(b"X := 1;", b"Xyz := 1; Y := 2;")
    stale = al_parser.parse(src)
    assert inc.diff(inc.rows(al_parser.parse(new, stale)), inc.rows(al_parser.parse(new))) is not None


# ---- the tree comparator --------------------------------------------------------------

def test_comparator_detects_field_span_and_anonymous_changes(al_parser):
    rows = inc.rows(al_parser.parse(MULTI))
    assert inc.diff(rows, list(rows)) is None
    col = inc.ROW_FIELDS.index
    named_field = next(i for i, r in enumerate(rows) if r[col("field")] is not None)
    anon = next(i for i, r in enumerate(rows) if not r[col("named")] and r[col("type")] == ";")

    def altered(i, col, value):
        out = list(rows)
        out[i] = out[i][:col] + (value,) + out[i][col + 1:]
        return out

    for alt in (altered(named_field, col("field"), "bogus"),
                altered(named_field, col("end_byte"), rows[named_field][col("end_byte")] + 1),
                altered(named_field, col("grammar_name"), "keyword_as_identifier"),
                altered(anon, col("has_error"), True), rows[:anon] + rows[anon + 1:]):
        d = inc.diff(rows, alt)
        assert d is not None and d["index"] <= max(named_field, anon)
    assert inc.diff(rows, rows[:-1])["fresh"] is None


# ---- the process-tree sampler ---------------------------------------------------------

CHILD = "import time; b = bytearray(b'\\x01') * (150 * 2**20); time.sleep(3)"
PARENT = (f"import subprocess, sys, time; a = bytearray(b'\\x01') * (100 * 2**20); "
          f"subprocess.run([sys.executable, '-c', {CHILD!r}])")


def test_sampler_sums_over_a_spawned_child():
    proc = subprocess.Popen([sys.executable, "-c", PARENT])
    s = TreeSampler(proc.pid, interval=0.05)
    s.start()
    proc.wait()
    s.stop()
    MiB = 2 ** 20
    assert s.samples > 5 and s.peak_processes >= 2
    assert s.peak_single >= 150 * MiB                      # the child alone
    assert s.peak_sum >= 250 * MiB                         # parent + child together
    assert s.peak_sum > s.peak_single


def test_utf16_sources_are_transcoded_like_the_sweep():
    from tools.perf.common import source
    text = "codeunit 1 \"Æ\" { }"
    assert source(("\ufeff" + text).encode("utf-16-le")) == text.encode("utf-8")
    assert source(("\ufeff" + text).encode("utf-16-be")) == text.encode("utf-8")
    assert source(b"\xef\xbb\xbfx") == b"\xef\xbb\xbfx"             # a UTF-8 BOM is kept


# ---- the outside-CPU load monitor -----------------------------------------------------

SPIN = "import time\nt = time.time() + {s}\nwhile time.time() < t: pass"
PARENT_OF_SPINNER = ("import subprocess, sys, time; subprocess.run([sys.executable, '-c', {spin!r}])")


def test_load_monitor_counts_outside_and_excludes_our_tree():
    """Two monitors over the same window see the same idle noise. One is rooted at a process
    whose CHILD spins, the other at an unrelated sleeper: the spin is outside only for the
    second, so their means differ by about one core."""
    from tools.perf.load import LoadMonitor
    sleeper = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(6)"])
    ours = subprocess.Popen([sys.executable, "-c", PARENT_OF_SPINNER.format(spin=SPIN.format(s=4))])
    time.sleep(0.5)
    inside, outside = LoadMonitor(0.5, root_pid=ours.pid), LoadMonitor(0.5, root_pid=sleeper.pid)
    inside.start(), outside.start()
    time.sleep(3.0)
    a, b = inside.stop(), outside.stop()
    ours.wait(), sleeper.kill()
    assert a["sampled"] and a["samples"] >= 4
    assert 0.6 < b["outside_cores_mean"] - a["outside_cores_mean"] < 1.6


def test_edit_points_check_catches_wrong_points(al_parser):
    """The tree comparison cannot see a wrong edit POINT (tree-sitter re-lexes and recomputes
    from bytes); the shifted-node check on the edited old tree can: columns counted in
    characters, and a new_end_point one row off."""
    src = "codeunit 1 A { trigger OnRun() begin Æble := 'ø'; X := 1; end; }".encode("utf-8")
    at = src.index(b"X := 1")
    e = inc.Edit("t", at, at, b"Y := 2; ")
    good = inc.edit_args(src, e)
    fresh_rows = inc.rows(al_parser.parse(e.apply(src)))
    chars = len(src[:at].decode("utf-8"))
    wrong = dict(good, start_point=(0, chars), old_end_point=(0, chars),
                 new_end_point=(0, chars + len(e.new)))
    row_off = dict(good, new_end_point=(1, good["new_end_point"][1]))
    assert chars != at                              # the line really has multi-byte text
    for args, bad in ((good, False), (wrong, True), (row_off, True)):
        old = al_parser.parse(src)
        old.edit(**args)
        assert (inc.shifted_points(old, fresh_rows, args["new_end_byte"]) is not None) is bad


def test_sample_takes_utf16_files_and_reports_shortfalls(al_parser):
    files = [("a", f"f{i}.al", b"codeunit 1 A { }") for i in range(20)]
    chosen, short = inc.sample(files, ["a"], al_parser, size=10, utf16=["a:f3.al", "a:f7.al"])
    cats = dict((files[i][1], c) for i, c in chosen)
    assert cats["f3.al"] == "utf16" and cats["f7.al"] == "utf16"
    assert short["a"]["utf16"] == 3 and short["a"]["split"] == 20
    assert len(chosen) == 10


# ---- compare across corpus sets and compilers; merge ----------------------------------

LABELS4 = ("bc-history", "dc", "bc28.1", "bcapps-29.0")


def _run(labels, corpora, lib_flags=("-O2",)):
    """A result shaped like `native` over `labels`: {name: (median, lo, hi)} per corpus entry."""
    def entry(m, lo, hi):
        return {"files": 10, "single": {"files_per_s": {"median": m, "min": lo, "max": hi, "runs": []}},
                "latency_ms": {"p50": m / 100, "p99": m / 10}}
    lib = {"compiler": "cl.exe", "compiler_version": "19.44", "flags": list(lib_flags)}
    return {"env": {"corpora": {l: {"head": "h"} for l in labels}, "grammar_sha": "g", "native_library": lib},
            "groups": {"native": {"read_seconds": 10.0, "corpora": {k: entry(*v) for k, v in corpora.items()},
                                  "meta": {"corpora": list(labels), "library": lib}},
                       "build": {"STATE_COUNT": 15870, "meta": {"corpora": list(labels)}}}}


def test_compare_subset_run_against_the_four_corpus_baseline_has_no_false_flag():
    base = _run(LABELS4, {"dc": (850.8, 848, 860), "bc-history": (682.6, 682, 684), "combined": (596.9, 595, 597)})
    dc_only = _run(("dc",), {"dc": (853.7, 850, 856), "combined": (853.7, 850, 856)})
    lines = report.compare(base, dc_only)
    rows = _rows([l for l in lines if not l.startswith(("NOTE", "WARNING"))])
    comb = rows["native.corpora.combined.single.files_per_s"].split()
    assert comb[-1] == "n/c" and comb[3] == "n/c" and "%" not in rows["native.corpora.combined.single.files_per_s"]
    assert rows["native.read_seconds"].split()[-1] == "n/c"
    assert rows["native.corpora.combined.latency_ms.p99"].split()[-1] == "n/c"
    dc = rows["native.corpora.dc.single.files_per_s"].split()
    assert dc[4] == "+0.34%" and len(dc) == 5                     # compared, inside the spread: no flag
    assert rows["native.corpora.dc.latency_ms.p99"].split()[-1] != "?"   # a float without a spread
    assert rows["native.corpora.bc-history.single.files_per_s"].split()[-1] == "-"
    assert rows["build.STATE_COUNT"].split()[3] == "0"            # corpus-free group still compared
    assert not [l for l in lines if l.rstrip().endswith("!")]
    assert any(l.startswith("NOTE native: corpus sets differ") for l in lines)


def test_compare_warns_on_a_different_compiler():
    a = _run(LABELS4, {"dc": (850, 848, 860)})
    b = _run(LABELS4, {"dc": (850, 848, 860)}, lib_flags=("-O2", "/GL"))
    lines = report.compare(a, b)
    assert any(l.startswith("WARNING native: the native library was built differently") for l in lines)
    assert not any(l.startswith("WARNING") for l in report.compare(a, a))


def test_merge_marks_old_groups_not_sampled_and_refuses_another_parser():
    import copy
    old = {"command": "c", "started": "s", "finished": "f", "warnings": [],
           "env": {"grammar_sha": "g", "corpora": {"dc": {"head": "h"}},
                   "load_before_group": {"wasm": {"cpu_percent_2s": 12.3}}},
           "groups": {"wasm": {"x": 1}, "native": {"x": 1}}}
    new = _run(("dc",), {"dc": (1, 1, 1)})
    new |= {"command": "n", "started": "s2", "finished": "f2", "warnings": ["w"]}
    merged = report.merge(copy.deepcopy(old), new, "new.json")
    assert merged["groups"]["native"] is new["groups"]["native"]
    assert merged["groups"]["wasm"]["meta"]["load"]["sampled"] is False
    assert "12.3% CPU" in merged["groups"]["wasm"]["meta"]["load"]["note"]
    assert merged["merges"][0]["groups"] == ["build", "native"] and merged["merges"][0]["warnings"] == ["w"]
    assert merged["warnings"] == []                      # the base run's own warnings only
    other = copy.deepcopy(new)
    other["env"]["grammar_sha"] = "different"
    with pytest.raises(ValueError):
        report.merge(copy.deepcopy(old), other, "x")


# ---- fix round 2: ab, noise floor, cross-session, placement, exited workers ------------

def test_ab_schedule_is_abba():
    from tools.perf import ab
    assert ab.schedule(4) == list("ABBAABBA")
    assert ab.schedule(1) == ["A", "B"]


def test_ab_ratios_pair_each_round_whatever_the_order():
    from tools.perf import ab
    order = ab.schedule(3)                       # A B B A A B
    secs = [2.0, 1.0, 1.1, 2.2, 1.8, 0.9]        # A is 2x B in every round
    assert ab.ratios(order, secs) == pytest.approx([2.0, 2.0, 2.0])
    with pytest.raises(ValueError):
        ab.ratios(order, secs[:-1])


def test_ab_bootstrap_ci_brackets_the_median_and_is_deterministic():
    from tools.perf import ab
    r = [1.98, 2.01, 2.03, 2.00, 1.99, 2.05, 2.02, 2.00]
    lo, hi = ab.bootstrap_ci(r)
    assert lo <= stats.median(r) <= hi and hi - lo < 0.06
    assert ab.bootstrap_ci(r) == (lo, hi)
    assert ab.bootstrap_ci([2.0] * 5) == (2.0, 2.0)


def test_compare_noise_floor():
    a = _result(10.0, 9.95, 10.05)
    b = _result(10.4, 10.35, 10.45)               # +4%: beyond the spread, under the 5% floor
    line = _rows(report.compare(a, b))["native.corpora.dc.single.seconds"]
    assert not line.rstrip().endswith("!")
    assert _rows(report.compare(a, b, floor=0.0))["native.corpora.dc.single.seconds"].rstrip().endswith("!")
    c = _result(10.7, 10.65, 10.75)               # +7%: beyond the 5% floor
    assert _rows(report.compare(a, c))["native.corpora.dc.single.seconds"].rstrip().endswith("!")


def test_compare_cross_session_and_placement_headers():
    base = _run(LABELS4, {"dc": (850, 848, 860)})
    later = _run(LABELS4, {"dc": (850, 848, 860)})
    base["groups"]["native"]["meta"]["started"] = "t1"
    later["groups"]["native"]["meta"]["started"] = "t2"
    later["groups"]["native"]["single_pin"] = {"pinned_to": [2]}
    lines = report.compare(base, later)
    assert any(l.startswith("CROSS-SESSION native") and "not decision-grade" in l for l in lines)
    assert any(l.startswith("WARNING native: CPU or pin differs") for l in lines)
    same = report.compare(base, base)
    assert not [l for l in same if l.startswith(("CROSS-SESSION", "WARNING"))]


def test_compiler_identity_ignores_the_install_path_and_sees_link_flags():
    a = _run(LABELS4, {"dc": (1, 1, 1)})
    b = _run(LABELS4, {"dc": (1, 1, 1)})
    b["groups"]["native"]["meta"]["library"] = dict(a["groups"]["native"]["meta"]["library"],
                                                    compiler="C:/VS/Community/cl.exe")
    assert not any(l.startswith("WARNING") for l in report.compare(a, b))
    b["groups"]["native"]["meta"]["library"]["link_flags"] = ["/LTCG"]
    assert any(l.startswith("WARNING native: the native library") for l in report.compare(a, b))
    from tools.perf import procs
    exe, flags, link = procs.parse_invocation(
        r"[] C:\Program Files\VS\cl.exe -nologo -O2 -I U:\x\src -W4 U:\x\src\parser.c -link -out:C:\t\a.dll /LTCG")
    assert exe.endswith("cl.exe") and flags == ["-nologo", "-O2", "-W4"] and link == ["/LTCG"]


EXIT_WAVES = ("import subprocess, sys\n"
              "for _ in range(4):\n"
              "    ps = [subprocess.Popen([sys.executable, '-c', {spin!r}]) for _ in range(4)]\n"
              "    [p.wait() for p in ps]\n")


@pytest.mark.skipif(sys.platform != "win32", reason="the handle-keeping path is Windows-only")
def test_load_monitor_keeps_the_cpu_of_exited_workers():
    """Waves of 4 short-lived spinners, each exiting between two 1 s samples. Without the kept
    handles their last slice is lost and reads as OUTSIDE CPU (re-review: 9.8 vs 3.8 cores)."""
    from tools.perf.load import LoadMonitor
    sleeper = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(8)"])
    waves = subprocess.Popen([sys.executable, "-c", EXIT_WAVES.format(spin=SPIN.format(s=0.6))])
    inside, outside = LoadMonitor(1.0, root_pid=waves.pid), LoadMonitor(1.0, root_pid=sleeper.pid)
    inside.start(), outside.start()
    waves.wait()
    time.sleep(1.2)
    a, b = inside.stop(), outside.stop()
    sleeper.kill()
    # the spinners are ~4 cores for most of the window: outside for the sleeper's monitor only
    assert b["outside_cores_mean"] - a["outside_cores_mean"] > 1.5


def test_mean_rule_needs_enough_samples():
    from tools.perf import load
    short = load.summary([5.0] * 12)
    assert short["mean_rule_applies"] is False and short["flagged"] is False
    long = load.summary([5.0] * load.MEAN_MIN_SAMPLES)
    assert long["mean_rule_applies"] and long["flagged"]
    assert load.summary([12.0])["flagged"]                       # the max rule always applies
