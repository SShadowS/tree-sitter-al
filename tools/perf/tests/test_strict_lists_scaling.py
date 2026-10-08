"""strict_lists_scaling: the generators build the documented shapes, and the fitted ratio reads linear as 2."""
from tools.perf import strict_lists_scaling as s


def test_length_source_has_one_group_per_item_after_the_first():
    src = s.length_source("implements", 4)
    assert src.count(b"#if X") == 3 and src.count(b"#endif") == 3 and b"implements I0\n#if X\n, I1\n#endif" in src


def test_depth_source_nests_d_deep_copies_times():
    src = s.depth_source("var-names", 3)
    assert src.count(b"#if X") == 3 * s.DEPTH_COPIES and b"#endif\n#endif\n#endif" in src


def test_empty_run_source():
    assert s.empty_run_source(2).count(b"#if X\n#endif\n") == 2


def test_fitted_ratio():
    linear = [(x, 0, 3e-6 * x) for x in s.LENGTHS]
    quadratic = [(x, 0, 1e-9 * x * x) for x in s.LENGTHS]
    assert abs(s.fitted(linear) - 2) < 1e-9 and abs(s.fitted(quadratic) - 4) < 1e-9
    assert s.ratios(linear)[-1] == (5120, 2.0)


# --- B7b-3 series (spec 2026-10-08 section 8.2) ---------------------------------------------------------------------
def test_b7b3_series_use_the_unchanged_grid():
    for _, axis, xs, _ in s.b7b3_series():
        assert xs == (s.LENGTHS if axis == "length" else s.DEPTHS)
    assert {f for f, _, _, _ in s.b7b3_series()} == {"case-lone-semi", "case-decoration", "case-mixed-arms",
                                                     "move-spanning", "move-nested"}


def test_b7b3_generators():
    assert s.case_lone_semi(3).count(b"#if X\n;\n#endif\n") == 2 and b"3: Bar;\nend;" in s.case_lone_semi(3)
    nested = s.case_lone_semi_nested(2)
    assert nested.count(b"#if X\n#if X\n;\n#else\n;\n#endif\n#else\n;\n#endif\n") == s.DEPTH_COPIES - 1
    assert s.case_decoration(2).count(b"#if X\n#endif\n;\n") == 2
    assert s.case_decoration_nested(3).count(b"#if X\n#if X\n#if X\n#endif\n#endif\n#endif\n;\n") == s.DEPTH_COPIES
    assert s.case_mixed_arms(2).count(b"#if X\n;\n") == 2 and not s.case_mixed_arms(2).endswith(b";\nend;\n    end;\n}\n")
    assert b"A0; A1, A2\n#else\nB0; A1, A2\n#endif" in s.move_spanning(2)
    assert s.move_nested(1).count(b"moveafter(") == s.DEPTH_COPIES


def _sleeper(lib, src, out):
    """A worker that really runs past any small ceiling (spawn needs a module-level target)."""
    import time
    time.sleep(60)
    out.put(("ok", 0.0, False, 0, 0))


def test_isolated_worker_past_its_ceiling_is_killed_and_fails_the_series():
    import time
    t0 = time.perf_counter()
    rows, grown, err, peak = s.measure_isolated("unused", [10, 20], lambda x: b"x", ceiling=3, target=_sleeper)
    assert rows == [] and err == 10 and time.perf_counter() - t0 < 30     # killed, not waited out


def test_isolated_worker_that_cannot_load_fails_the_series():
    rows, _, err, _ = s.measure_isolated("no-such.dll", [10], lambda x: b"x")
    assert rows == [] and err == 10
