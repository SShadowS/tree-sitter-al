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
    """The pre-B1 tree: not(and(A, B)). Its AST differs in every configuration; its truth
    differs from (not A) and B exactly where B=0."""
    bad = _tree(node("preproc_not_expression", leaf("not", 4, 7),
                     node("preproc_and_expression", _ident(8, 9), leaf("and", 10, 13), _ident(14, 15))))
    trees = condition_check.tree_conditions(bad, SRC)
    differ = {}
    for env in (frozenset(), {"A"}, {"B"}, {"A", "B"}):
        ds, n, skipped = condition_check.check(trees, directives.resolve(SRC, frozenset(env)))
        assert (n, skipped) == (1, {})
        differ[tuple(sorted(env))] = [d.path for d in ds]
    ast = "if@0 ast: tree not(and(A,B)) vs resolver and(not(A),B)"
    truth = "if@0 truth: tree not(and(A,B))=True vs resolver and(not(A),B)=False"
    assert differ == {(): [ast, truth], ("A",): [ast, truth], ("B",): [ast], ("A", "B"): [ast]}


DEFINED = b"#define B\n#if not A and B\n#endif\n"


def test_in_file_define_cannot_hide_a_wrong_grouping():
    """Review I1: with `#define B` above it, B is in every reached environment, and the
    pre-B1 reading not(A and B) evaluates like (not A) and B in every configuration. Only
    the AST comparison sees it, in both configurations."""
    bad = _tree(node("preproc_not_expression", leaf("not", 14, 17),
                     node("preproc_and_expression", _ident(18, 19), leaf("and", 20, 23), _ident(24, 25))),
                at=10)
    trees = condition_check.tree_conditions(bad, DEFINED)
    for env in (frozenset(), frozenset({"A"})):
        ds, n, _ = condition_check.check(trees, directives.resolve(DEFINED, env))
        assert n == 1
        assert [d.path for d in ds] == ["if@10 ast: tree not(and(A,B)) vs resolver and(not(A),B)"]


def test_parentheses_are_normalised_away(al_parser):
    src = b"#if not (A and B) or ((C))\n#endif\n"
    recs = runner.check_input(al_parser, "t", src)
    assert len(recs) == 8 and all(r.cond_checked == 1 and r.status == "pass" for r in recs), recs


def test_skips_are_counted():
    trees = condition_check.tree_conditions(_tree(_ident(4, 5)), SRC)   # extent 4-5, source 4-15
    res = directives.resolve(SRC, frozenset())
    assert condition_check.check(trees, res) == ([], 0, {"extent": 1})
    assert condition_check.check({}, res) == ([], 0, {"no-node": 1})
    assert condition_check.check(None, res) == ([], 0, {"errored-tree": 1})


def test_define_above_the_directive_is_in_the_environment():
    src = b"#define A\n#if A\n#endif\n"
    good = _tree(_ident(14, 15), at=10)
    res = directives.resolve(src, frozenset())
    assert res.env_at[10] == frozenset({"A"})
    assert condition_check.check(condition_check.tree_conditions(good, src), res) == ([], 1, {})


def test_unreadable_condition_is_reported():
    bad = _tree(node("ERROR", _ident(4, 5), _ident(14, 15)))
    trees = condition_check.tree_conditions(bad, SRC)
    ds, _, _ = condition_check.check(trees, directives.resolve(SRC, frozenset()))
    assert len(ds) == 2 and all("unreadable:ERROR@4" in d.path for d in ds), ds
