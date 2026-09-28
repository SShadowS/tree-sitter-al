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
    # preproc_conditional_fields is registered (Task 5); preproc_conditional_where
    # (a #if inside a CalcFormula where-clause) stays unsupported through milestone 2.
    src = (b"table 1 T { fields { field(1; A; Integer) { "
           b"CalcFormula = count(A where(B = filter(0),\n#if X\nC = filter(0),\n#endif\nD = filter(0))); "
           b"} } }")
    root, extras, _ = ir.from_tree(al_parser.parse(src))
    with pytest.raises(LoweringError) as err:
        lower_tree(root, extras, resolve(src, frozenset({"X"})))
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


# --- fix round 1 -------------------------------------------------------------

EMPTY_THEN = b"codeunit 1 T { trigger OnRun() begin if c then\n#if A\n x := 1\n#endif\n ; end; }"
VAR_BLOCK = b"codeunit 1 T { procedure P()\n#if A\nvar\n x: Integer;\n#endif\nbegin end; }"
EMPTY_ASSERTERROR = b"codeunit 1 T { trigger OnRun() begin asserterror\n#if A\n x := 1\n#endif\n ; end; }"


def _lower(parser, src, env):
    root, extras, problems = ir.from_tree(parser.parse(src))
    assert problems == []
    return lower_tree(root, extras, resolve(src, frozenset(env)))


def test_mandatory_single_slot_with_empty_arm_is_policy(al_parser):
    with pytest.raises(LoweringError) as err:
        _lower(al_parser, EMPTY_THEN, [])
    assert err.value.kind == "policy"
    _lower(al_parser, EMPTY_THEN, ["A"])          # one node: fine


@pytest.mark.parametrize("src", [VAR_BLOCK, EMPTY_ASSERTERROR])
def test_optional_slot_with_empty_arm_lowers(al_parser, src):
    for env, ds in run_all(al_parser, src).items():
        assert ds == [], (env, ds)


def test_accounting_rejects_inactive_leaf_marked_kept(al_parser, monkeypatch):
    from tools.config_oracle.lowering import select

    def lower_every_arm(node, ctx):
        arms, endif = select.split_arms(node)
        out = select.Lowered([])
        for directive, content in arms:
            ctx.accounting.mark(directive, "directive")
            for c in content:
                out.nodes.extend(select.lower(c, ctx.child(node.kind, "<children>")).nodes)
        ctx.accounting.mark(endif, "directive")
        return out

    monkeypatch.setattr(select, "branch_select", lower_every_arm)
    with pytest.raises(LoweringError) as err:
        _lower(al_parser, STMT, [])
    assert err.value.kind == "accounting"


def test_fragment_dataclass_fields_are_required():
    from tools.config_oracle.lowering import engine
    with pytest.raises(TypeError):
        engine.Terminator(anchor=None)
    with pytest.raises(TypeError):
        engine.BlockCompletion(anchor=None, statements=[])
    with pytest.raises(TypeError):
        engine.ElseAttachment(anchor=None, else_kw=ir.Node("x", False, None, 0, 1, []))


def test_check_emitted_names_a_duplicated_interval():
    from tools.config_oracle.lowering.engine import Accounting
    acc = Accounting(resolve(b"xy", frozenset()))
    lf = ir.Node("x", False, None, 0, 1, [])
    acc.mark(lf, "kept")
    low = ir.Node("source_file", True, None, 0, 1, [lf.copy(), lf.copy()])
    with pytest.raises(LoweringError) as err:
        acc.check_emitted(low)
    assert "(0, 1)" in str(err.value)


def test_fragment_anchor_survives_single_slot_selection(al_parser, monkeypatch):
    """The arm's `;` is turned into a Terminator anchored to the arm statement; the
    real branch_select must hand back that SAME node (field set in place), and the
    statement_block must consume the Terminator after the if_statement."""
    from tools.config_oracle.lowering import engine, select
    src = b"codeunit 1 T { trigger OnRun() begin if c then\n#if A\n x := 1;\n#endif\n end; }"
    real_lower, real_select = select.lower, select.branch_select
    last, seen = [], []

    def lower_semicolon_as_terminator(node, ctx):
        if ctx.parent_kind == "preproc_conditional_statement" and node.kind == ";":
            ctx.accounting.mark(node, "kept")
            return engine.Lowered([], [engine.Terminator(anchor=last[-1], leaf=node.copy())])
        r = real_lower(node, ctx)
        last.extend(r.nodes)
        return r

    def checked_select(node, ctx):
        out = real_select(node, ctx)
        seen.append(out.frags[0].anchor is out.nodes[0] and out.nodes[0].field == "then_branch")
        return out

    monkeypatch.setattr(select, "lower", lower_semicolon_as_terminator)
    monkeypatch.setattr(select, "branch_select", checked_select)
    root, extras, _ = ir.from_tree(al_parser.parse(src))
    res = resolve(src, frozenset({"A"}))
    low, low_extras, _ = lower_tree(root, extras, res)
    assert seen == [True]
    ref = reference.extract(al_parser, res.masked)
    assert compare.structure(ref.root, low) == []


def test_arm_content_outside_the_declaration_is_an_error(al_parser, monkeypatch):
    from tools.config_oracle import contracts
    e = contracts.REGISTRY["preproc_conditional_statement"]
    monkeypatch.setitem(contracts.REGISTRY, "preproc_conditional_statement",
                        contracts.Entry(e.type, e.kind, e.handler, e.hosts, e.alias_to,
                                        frozenset({"no_such_kind"}), None))
    root, extras, _ = ir.from_tree(al_parser.parse(STMT))
    res = resolve(STMT, frozenset({"A"}))
    with pytest.raises(LoweringError) as err:
        lower_tree(root, extras, res)
    assert err.value.kind == "arm-content"


def test_case_else_branch_inside_conditional_fails_closed(al_parser):
    """preproc_conditional_case's arm deliberately excludes case_else_branch (Task 6):
    it is case_body's child only in the multi-config tree; every single-configuration
    parse carries it as case_statement's OWN field, a sibling of case_body, never
    nested inside it. Splicing it into case_body like an ordinary arm member produced
    a genuine structural discrepancy over BC.History (case_preprocessor_else.txt,
    config CLEAN25=0) before this exclusion. Pinned as arm-content, not a discrepancy."""
    src = (b"codeunit 1 T { procedure P() begin case 1 of 1: ProcessCustomer();\n"
           b"#if not CLEAN25\nelse ProcessExtension();\n#endif\nend; end; }")
    root, extras, _ = ir.from_tree(al_parser.parse(src))
    with pytest.raises(LoweringError) as err:
        lower_tree(root, extras, resolve(src, frozenset()))
    assert err.value.kind == "arm-content"


def test_reading_active_reports_whether_the_if_arm_is_taken(al_parser, monkeypatch):
    from tools.config_oracle import contracts
    from tools.config_oracle.lowering import select
    e = contracts.REGISTRY["preproc_conditional_statement"]
    fake_entry = contracts.Entry(e.type, e.kind, e.handler, e.hosts, e.alias_to, e.arm, "arm:if")
    real_select = select.branch_select
    seen = []

    def capturing(node, ctx):
        seen.append(select.reading_active(node, fake_entry, ctx))
        return real_select(node, ctx)

    monkeypatch.setattr(select, "branch_select", capturing)
    root, extras, _ = ir.from_tree(al_parser.parse(STMT))
    lower_tree(root, extras, resolve(STMT, frozenset({"A"})))   # #if arm taken
    lower_tree(root, extras, resolve(STMT, frozenset()))        # #else arm taken
    assert seen == [True, False]
