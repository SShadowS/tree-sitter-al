from pathlib import Path

import pytest

from tools.b7_audit import seeds
from tools.b7_audit.placements import Cell

LINKS = ("SubPageLink", "RunPageLink", "LinkFields", "DataItemTableFilter", "ColumnFilter", "DataItemLink")


def test_expand_valid_patterns():
    syms = ("X", "Y")
    f = frozenset
    assert seeds.expand_valid("*", syms) == {f(), f({"X"}), f({"Y"}), f({"X", "Y"})}
    assert seeds.expand_valid("none", syms) == set()
    assert seeds.expand_valid("X", syms) == {f({"X"}), f({"X", "Y"})}
    assert seeds.expand_valid("X,!Y; !X,Y", syms) == {f({"X"}), f({"Y"})}
    with pytest.raises(ValueError):
        seeds.expand_valid("Z", syms)


def test_load_cells_follow_the_ruling():
    cells = seeds.load()
    assert len(cells) > 200 and len({c.id for c in cells}) == len(cells)
    for c in cells:
        assert isinstance(c, Cell) and c.key == c.id and c.id.startswith("seed:")
        assert c.placement.startswith("seed:") and c.plain is None and c.check == ()
        assert c.hole == (0, len(c.source.encode("utf-8"))) and c.host
        assert all(v <= frozenset(c.symbols) for v in c.intended_valid)


def test_known_seeds():
    by = {c.key: c for c in seeds.load()}
    item1 = by["seed:g11-item1-link-comma-leading__comma_leading_link"]
    assert item1.symbols == ("X",) and item1.intended_valid == {frozenset(), frozenset({"X"})}
    assert by["seed:task4-addfirst-fieldgroups"].intended_valid == set()
    assert by["seed:task4-implementation-arm-comma-after-endif"].intended_valid == {frozenset({"X"})}


def test_required_seeds_present():
    keys = {c.key for c in seeds.load()}
    for k in ("item2-option-member-trailing", "item2-option-member-leading", "task4-permission-arm-bare-semicolon"):
        assert f"seed:{k}" in keys
    texts = {c.key: c.source for c in seeds.load()}
    blob = "\n".join(texts.values())
    for s in ("item 30", "item 38", "item 39 point 1", "item 39 point 2", "property_value_run_b13_gap_test.txt case 10"):
        assert s in blob
    assert "Foo();" in next(v for k, v in texts.items() if k.endswith("b7-gap-assign-semicolon-in-arms"))


def test_link_name_coverage_lists_all_six():
    cov = seeds.link_coverage()
    assert set(cov) == set(LINKS)
    assert cov["RunPageLink"] and cov["ColumnFilter"]


def _write(d, name, text):
    (d / name).write_text(text, encoding="utf-8", newline="\n")


def test_production_walk_on_known_shapes(tmp_path, al_parser):
    _write(tmp_path, "a.al", "codeunit 50100 P { procedure Q() begin\n"
           "Foo(a,\n#if X\nb,\n#endif\nc);\n"
           "#if X\nx := 1;\n#endif\n"
           "end; procedure Foo(A: Integer) begin end; }\n")
    _write(tmp_path, "b.al", "codeunit 50101 P { procedure Q() begin\n"
           "x := 1 +\n#if X\n2 +\n#endif\n3;\n"
           "Foo(a\n#if X\n, b\n#endif\n);\n"
           "Foo(a,\n#if X\nb\n#endif\n);\n"
           "end; }\n")
    _write(tmp_path, "c.al", "codeunit 50102 P { }\n")           # no #if: skipped
    counts, ex = seeds.walk([tmp_path], parser=al_parser)
    # a statement group ending in its own `;` is a terminated unit, not a separator site
    assert counts == {("preproc_conditional_arguments", "sep-after"): 1,
                      ("preproc_conditional_statement", "terminated-unit"): 1,
                      ("preproc_operand_prefix", "prefix"): 1,
                      ("preproc_conditional_arguments", "sep-before"): 1,
                      ("preproc_conditional_arguments", "trail"): 1}, counts
    assert all(len(v) <= 3 and ":" in v[0] for v in ex.values())
    assert seeds.production_shapes([tmp_path], parser=al_parser) == counts


def _counts(tmp_path, al_parser, body):
    _write(tmp_path, "t.al", body)
    return seeds.walk([tmp_path], parser=al_parser)[0]


def test_permission_arm_semicolon_is_terminated_unit(tmp_path, al_parser):
    src = ("permissionset 50100 PS { Permissions = tabledata T = R,\n#if X\ntabledata T2 = R;\n#endif\n}\n"
           "table 50101 T { } table 50102 T2 { }\n")
    c = _counts(tmp_path, al_parser, src)
    assert ("preproc_conditional_permissions", "terminated-unit") in c, c
    assert not any(k[1] == "sep-after" and "permission" in k[0] for k in c), c


def test_semicolon_stays_a_separator_where_it_joins_values(tmp_path, al_parser):
    src = ("page 50101 P { SourceTable = T; layout { area(Content) { part(L; S) { SubPageLink = B = field(A),\n"
           "#if X\nD = field(C),\n#endif\nF = field(E); } } } }\n")
    c = _counts(tmp_path, al_parser, src)
    assert ("preproc_conditional_link_values", "sep-after") in c, c


def test_property_equals_is_not_an_expression_edge():
    class N:
        def __init__(self, t):
            self.type = t
    assert not seeds._edge(N("="))
    assert seeds._edge(N("+")) and seeds._edge(N("and")) and seeds._edge(N("additive_expression"))


def test_split_host_end_semicolon_is_terminated_unit(tmp_path, al_parser):
    """Task 6 deferred minor: `end;` closing a split `begin` ends a statement (BC.History CustContUpdate.Codeunit.al),
    not a separator site."""
    src = ("codeunit 50100 P { procedure Q() begin\nif A then\n#if X\nbegin\n#endif\nx := 1;\n#if X\nend;\n#endif\n"
           "y := 2;\nend; }\n")
    c = _counts(tmp_path, al_parser, src)
    assert c == {("preproc_split_code_block_over_endif", "terminated-unit"): 1}, c
    assert seeds._terminates("preproc_split_if_then_begin") and not seeds._terminates("preproc_split_field")
