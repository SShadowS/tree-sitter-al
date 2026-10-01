"""condition_check (roadmap B1): the tree's #if/#elif grouping against the resolver's."""
from tools.config_oracle import condition_check, directives, runner
from tools.config_oracle.tests.conftest import leaf, node

SRC = b"#if not A and B\n#endif\n"


def _ident(s, e):
    return leaf("identifier", s, e, named=True)


def _tree(cond, at=0):
    cond.field = "condition"
    return node("source_file", node("preproc_if", leaf("preproc_open", at, at + 3, named=True), cond))


def test_head_parser_reads_not_a_and_b_as_the_resolver_does(al_parser):
    recs = runner.check_input(al_parser, "t", SRC)
    assert len(recs) == 4                      # A x B
    assert all(r.cond_checked == 1 for r in recs), [(r.config, r.cond_checked) for r in recs]
    assert not any("|condition-structure|" in i for r in recs for i in r.items), recs


def test_resolve_tier_runs_the_check_too(al_parser):
    recs = runner.check_input(al_parser, "t", SRC, mode="resolve")
    assert [r.cond_checked for r in recs] == [1, 1, 1, 1]


def test_pre_b1_grouping_is_a_condition_structure_discrepancy():
    """The pre-B1 tree: not(and(A, B)). It differs from (not A) and B exactly where B=0."""
    bad = _tree(node("preproc_not_expression", leaf("not", 4, 7),
                     node("preproc_and_expression", _ident(8, 9), leaf("and", 10, 13), _ident(14, 15))))
    trees = condition_check.tree_conditions(bad, SRC)
    differ = {}
    for env in (frozenset(), {"A"}, {"B"}, {"A", "B"}):
        ds, n = condition_check.check(trees, directives.resolve(SRC, frozenset(env)))
        assert n == 1
        differ[tuple(sorted(env))] = [d.path for d in ds]
    want = ["if@0: tree not(and(A,B))=True vs resolver and(not(A),B)=False"]
    assert differ == {(): want, ("A",): want, ("B",): [], ("A", "B"): []}


def test_define_above_the_directive_is_in_the_environment():
    src = b"#define A\n#if A\n#endif\n"
    good = _tree(_ident(14, 15), at=10)
    res = directives.resolve(src, frozenset())
    assert res.env_at[10] == frozenset({"A"})
    ds, n = condition_check.check(condition_check.tree_conditions(good, src), res)
    assert (ds, n) == ([], 1)


def test_unreadable_condition_is_reported():
    bad = _tree(node("ERROR", _ident(4, 5), _ident(14, 15)))
    trees = condition_check.tree_conditions(bad, SRC)
    ds, _ = condition_check.check(trees, directives.resolve(SRC, frozenset()))
    assert len(ds) == 1 and "unreadable:ERROR@4" in ds[0].path
