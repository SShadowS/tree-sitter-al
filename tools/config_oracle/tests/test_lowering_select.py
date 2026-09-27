import pytest

from tools.config_oracle import compare, ir, reference
from tools.config_oracle.directives import configurations, discover, resolve
from tools.config_oracle.lowering import lower_tree
from tools.config_oracle.lowering.engine import LoweringError

STMT = b"""codeunit 1 T
{
    trigger OnRun()
    begin
        x := 0;
#if A
        x := 1;
#else
        x := 2;
        x := 3;
#endif
        x := 4;
    end;
}
"""

BODY = b"""codeunit 1 T
{
#if A
    procedure P() begin end;
#endif
    procedure Q() begin end;
}
"""


def run_all(parser, src):
    root, extras, problems = ir.from_tree(parser.parse(src))
    assert problems == []
    disc = discover(src)
    results = {}
    for env in configurations(disc):
        res = resolve(src, env)
        low, low_extras, _ = lower_tree(root, extras, res)
        ref = reference.extract(parser, res.masked)
        assert ref.problems == []
        results[env] = (compare.structure(ref.root, low)
                        + compare.coverage(src, res.active, low, low_extras, "low"))
    return results


@pytest.mark.parametrize("src", [STMT, BODY])
def test_branch_select_matches_reference_in_every_configuration(al_parser, src):
    for env, ds in run_all(al_parser, src).items():
        assert ds == [], (env, ds)


def test_single_slot_with_two_statements_is_policy(al_parser):
    src = b"codeunit 1 T { trigger OnRun() begin if c then\n#if A\n x := 1; y := 2;\n#endif\n ; end; }"
    root, extras, _ = ir.from_tree(al_parser.parse(src))
    res = resolve(src, frozenset({"A"}))
    with pytest.raises(LoweringError) as err:
        lower_tree(root, extras, res)
    assert err.value.kind in ("policy", "contract-shape")


def test_unsupported_type_fails_closed(al_parser):
    src = b"table 1 T { fields {\n#if A\n field(1; F; Integer) { }\n#endif\n } }"
    root, extras, _ = ir.from_tree(al_parser.parse(src))
    with pytest.raises(LoweringError) as err:
        lower_tree(root, extras, resolve(src, frozenset({"A"})))
    assert err.value.kind == "unsupported-type"


def test_unregistered_special_type_fails_closed():
    n = ir.Node("preproc_split_invented", True, None, 0, 1, [ir.Node("x", False, None, 0, 1, [])])
    root = ir.Node("source_file", True, None, 0, 1, [n])
    with pytest.raises(LoweringError) as err:
        lower_tree(root, [], resolve(b"x", frozenset()))
    assert err.value.kind == "unregistered-type"


def test_accounting_catches_a_dropped_leaf(al_parser, monkeypatch):
    from tools.config_oracle.lowering import select
    real = select.branch_select

    def lossy(node, ctx):
        out = real(node, ctx)
        out.nodes = out.nodes[:-1]           # drop the arm's last statement without accounting
        return out

    monkeypatch.setattr(select, "branch_select", lossy)
    root, extras, _ = ir.from_tree(al_parser.parse(STMT))
    with pytest.raises(LoweringError) as err:
        lower_tree(root, extras, resolve(STMT, frozenset()))
    assert err.value.kind == "accounting"


def test_deep_ordinary_tree_lowers():
    depth = 5000
    n = ir.Node("x", False, None, 0, 1, [])
    for _ in range(depth):
        n = ir.Node("binary_expression", True, None, 0, 1, [n])
    root = ir.Node("source_file", True, None, 0, 1, [n])
    low, _, _ = lower_tree(root, [], resolve(b"x", frozenset()))
    assert low.leaf_intervals() == ((0, 1),)
