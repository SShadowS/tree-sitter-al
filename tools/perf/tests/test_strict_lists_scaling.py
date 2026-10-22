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
    rows, grown, err, peak, kind = s.measure_isolated("unused", [10, 20], lambda x: b"x", ceiling=3, target=_sleeper)
    assert rows == [] and err == 10 and kind == "timeout" and time.perf_counter() - t0 < 30   # killed, not waited out


def test_isolated_worker_that_cannot_load_fails_the_series():
    rows, _, err, _, kind = s.measure_isolated("no-such.dll", [10], lambda x: b"x")
    assert rows == [] and err == 10 and kind == "error"


def _erroring(lib, src, out):
    """A worker whose parse has an error (has_error True)."""
    out.put(("ok", 0.001, True, 0, 0))


def test_excepted_series_with_a_parse_error_fails():
    """Fix round 1 (Task 6 review): the item-52 exception waives the limits and the timeout, never a parse error."""
    _, _, err, _, kind = s.measure_isolated("unused", [10], lambda x: b"x", target=_erroring)
    exc = s.SCALING_EXCEPTIONS[("root_tails", "length")]
    assert err == 10 and kind == "error" and not s.series_ok(False, exc, kind)
    assert s.series_ok(False, exc, "timeout") and s.series_ok(False, exc, None)    # limits / timeout: waived
    assert not s.series_ok(False, None, "timeout")                                  # no exception: fails


# --- B7b-2 series (spec 2026-10-20 section 8.5) ---------------------------------------------------------------------
def test_b7b2_series_use_the_unchanged_grid():
    for _, axis, xs, _ in s.b7b2_series():
        assert xs == (s.LENGTHS if axis == "length" else s.DEPTHS)
    assert {f for f, _, _, _ in s.b7b2_series()} == {"argument_tails", "root_tails", "nested_tails", "ternary_parts", "ternary_condition_consecutive",
                                                    "operand_groups", "nested_operand_groups", "mixed"} | {
        f"root_slots/{r}" for r in s.ROOT_SLOTS}


def test_phase_c_generators():
    g = s.operand_groups(3)
    assert g.count(b"#if X") == 3 and b"r :=\n#if X\n1\n#else\n1\n#endif\n+\n#if X\n2\n#else\n2\n#endif\n+\n#if X\n3" in g
    nested = s.nested_operand_groups(2)
    assert nested.count(b"r := 1 +\n#if X\n#if X\n1\n#else\n2\n#endif\n#else\n2\n#endif\n;\n") == s.DEPTH_COPIES
    m = s.mixed(2)
    assert m.count(b"#if X") == 6
    assert b"r := 1\n+\n#if X\n1 *\n#endif\n#if X\n1\n#else\n1\n#endif\n#if X\n- 1\n#endif\n+\n#if X\n2 *" in m


def test_b7b2_generators():
    assert b"r := Foo(1\n#if X\n+2\n#endif\n#if X\n+3\n#endif\n);" in s.argument_tails(3)
    assert s.argument_tails(3).count(b"#if X") == 2
    assert s.root_tails(3).count(b"#if X") == 3 and b"r := 1\n#if X\n+1\n#endif" in s.root_tails(3)
    nested = s.nested_tails(2)
    assert nested.count(b"r := 1\n#if X\n+ 1\n#if X\n+ 1\n#endif\n#endif\n;\n") == s.DEPTH_COPIES


def test_root_slot_and_ternary_generators():
    src = s.root_slot("repeat_until")(3)
    assert src.count(b"#if X") == 3 and b"until C\n#if X\n+1\n#endif\n#if X\n+2\n#endif" in src
    assert all(s.root_slot(r)(2).count(b"#if X") == 2 for r in s.ROOT_SLOTS)
    t = s.ternary_parts(2)
    assert b"x := C1\n#if X\nand D1\n#endif\n? 1\n#if X\n+ 1\n#endif\n: C2" in t and t.count(b"#if X") == 4
    c = s.ternary_condition_consecutive(3)
    assert c.count(b"#if X") == 3 and b"x := C\n#if X\nand D1\n#endif" in c and b"\n? 1 : 0;\n" in c


# --- D1 series (spec 2026-10-22, Review Focus 4) --------------------------------------------------------------------
def test_d1_series_use_the_unchanged_grid():
    for _, axis, xs, _ in s.d1_series():
        assert xs == (s.LENGTHS if axis == "length" else s.DEPTHS)
    assert {f for f, _, _, _ in s.d1_series()} == {"split-if-begin-else", "split-if-then-begin",
                                                    "split-if-then-begin-else-shared", "else-begin-over-endif",
                                                    "code-block-over-endif", "fragmented-else-tail"}


def test_d1_units_parse_as_the_split_constructs(al_parser):
    """R9: one generated unit of each series parses clean as the construct it is meant to exercise."""
    def types(src):
        tree = al_parser.parse(src)
        out, stack = set(), [tree.root_node]
        while stack:
            n = stack.pop()
            out.add(n.type)
            stack.extend(n.children)
        return tree.root_node.has_error, out
    wants = ("preproc_split_if_begin_else", "preproc_split_else_begin_over_endif",
             "preproc_split_code_block_over_endif", "preproc_fragmented_else_tail", "preproc_fragmented_else_tail",
             "preproc_split_if_then_begin", "preproc_split_if_then_begin_else_shared", "preproc_split_if_begin_else")
    assert len(wants) == len(s.d1_series())
    for (family, axis, _, make), want in zip(s.d1_series(), wants):
        err, seen = types(make(1))
        assert not err and want in seen, (family, axis)


def test_scaling_exceptions_are_exactly_items_52_and_53():
    """User decisions (deferred-work items 52 and 53): only consecutive groups at a root after which a host group can
    start (item 52: the assignment and argument roots, Task 6; four Phase B roots and one ternary condition with
    consecutive groups, Task 9; the Phase C `mixed` series, whose tails chain one inside the next, Task 12) and tails
    on the conditions of a chained ternary (item 53) may fail the limits without
    failing the run. A new entry needs a decision of its own, not an edit here."""
    assert s.SCALING_EXCEPTIONS == {
        **{(f, "length"): "deferred-work item 52" for f in (
            "argument_tails", "root_tails", "root_slots/repeat_until", "root_slots/range_left",
            "root_slots/list_element", "root_slots/split_call_argument", "ternary_condition_consecutive",
            "mixed")},
        ("ternary_parts", "length"): "deferred-work item 53"}
