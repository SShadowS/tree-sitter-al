"""The parts of tools/perf that can go wrong silently."""
import random
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
    named_field = next(i for i, r in enumerate(rows) if r[5] is not None)
    anon = next(i for i, r in enumerate(rows) if not r[2] and r[1] == ";")

    def altered(i, col, value):
        out = list(rows)
        out[i] = out[i][:col] + (value,) + out[i][col + 1:]
        return out

    for alt in (altered(named_field, 5, "bogus"), altered(named_field, 7, rows[named_field][7] + 1),
                altered(anon, 10, True), rows[:anon] + rows[anon + 1:]):
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
