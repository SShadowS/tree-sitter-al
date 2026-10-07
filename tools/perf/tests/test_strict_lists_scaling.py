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
