from tools.config_oracle.tests import witness

SRC = b"""report 1 R
{
    dataset
    {
        dataitem(H; Integer)
        {
            dataitem(Total; Integer)
            {
            }
#if not CLEAN28
            dataitem(Outer; Integer)
            {
                DataItemTableView = sorting(Number);
#endif
                dataitem(Total2; Integer)
                {
                    column(A; 1) { }
#if not CLEAN28
                    column(B; 2) { }
                }
#else
                    column(C; 3) { }
#endif
                trigger OnPreDataItem()
                begin
                end;
            }
            dataitem(Next; Integer) { }
        }
    }
}
"""


def test_both_configs(al_parser):
    witness.assert_produces(al_parser, SRC, "preproc_split_report_dataitem_open_over_endif")
    witness.assert_produces(al_parser, SRC, "preproc_split_report_brace_close")
    witness.assert_all_pass(al_parser, SRC)


def test_trigger_left_in_outer_is_caught(al_parser, monkeypatch):
    from tools.config_oracle.lowering import assemblers
    monkeypatch.setattr(assemblers, "_RB_MOVE_AFTER", False)  # labelled hand-built bad lowering
    v = witness.verdicts(al_parser, SRC)
    assert any(s == "discrepancy" for s, _ in v.values()), v


def test_inner_not_closed_at_arm_brace_is_caught(al_parser, monkeypatch):
    """Mutation control for the ACTIVE configuration: the trigger after the inner
    dataitem is moved into it, i.e. the inner dataitem does not close at the arm's
    `}`. Every leaf is still kept once, so only the comparator can catch it."""
    from tools.config_oracle.lowering import assemblers
    orig = assemblers.report_brace_owner

    def mutated(node, ctx):
        out = orig(node, ctx)
        body = next(c for c in out.nodes[0].children if c.field == "body")
        trig = next(c for c in body.children if c.kind == "trigger_declaration")
        inner = body.children[body.children.index(trig) - 1]
        if inner.kind == "report_dataitem":   # the open arm is selected: Outer holds the trigger
            inner_body = next(c for c in inner.children if c.field == "body")
            body.children.remove(trig)
            inner_body.children.append(trig)
        return out
    monkeypatch.setattr(assemblers, "report_brace_owner", mutated)
    v = witness.verdicts(al_parser, SRC)
    assert v["CLEAN28=0"][0] == "discrepancy", v
    assert v["CLEAN28=1"][0] == "pass", v


def test_after_items_mutation_hits_the_inactive_config(al_parser, monkeypatch):
    from tools.config_oracle.lowering import assemblers
    monkeypatch.setattr(assemblers, "_RB_MOVE_AFTER", False)
    v = witness.verdicts(al_parser, SRC)
    assert v["CLEAN28=1"][0] == "discrepancy", v
    assert v["CLEAN28=0"][0] == "pass", v


# The grammar has no #elif in either rule (grammar.js: the open node has one #if
# arm, the brace close `#if … } [#else …] #endif`), so the no-arm-selected case
# stands in for it: a brace close with no #else, open arm inactive.
NO_ELSE = SRC.replace(b"#else\n                    column(C; 3) { }\n", b"")
EMPTY_ELSE = SRC.replace(b"                    column(C; 3) { }\n", b"")


def test_no_else_arm_both_configs(al_parser):
    witness.assert_produces(al_parser, NO_ELSE, "preproc_split_report_brace_close")
    assert b"#else" not in NO_ELSE
    witness.assert_all_pass(al_parser, NO_ELSE)


def test_empty_else_arm_both_configs(al_parser):
    witness.assert_produces(al_parser, EMPTY_ELSE, "preproc_split_report_brace_close")
    witness.assert_all_pass(al_parser, EMPTY_ELSE)


def _lower(al_parser, src, env):
    from tools.config_oracle import ir
    from tools.config_oracle.directives import resolve
    from tools.config_oracle.lowering import lower_tree
    root, extras, problems = ir.from_tree(al_parser.parse(src))
    assert not problems, problems
    return lower_tree(root, extras, resolve(src, frozenset(env)))


def test_brace_arm_disagreeing_with_open_arm_is_contract_shape(al_parser):
    """Different conditions: CLEAN28 undefined opens Outer, CLEAN29 defined skips
    the brace. (The witness reports reference-error first for this config, so the
    contract is checked on lower_tree directly.)"""
    import pytest
    from tools.config_oracle.lowering.engine import LoweringError
    src = SRC.replace(b"#if not CLEAN28\n                    column(B", b"#if not CLEAN29\n                    column(B")
    for env in ({"CLEAN29"}, {"CLEAN28"}):
        with pytest.raises(LoweringError) as err:
            _lower(al_parser, src, env)
        assert err.value.kind == "contract-shape", env
        assert err.value.node.kind == "preproc_split_report_brace_close"


def test_brace_close_outside_its_open_node_is_unconsumed(al_parser):
    import pytest
    from tools.config_oracle.lowering.engine import LoweringError
    src = b"report 1 R\n{\n    dataset\n    {\n        dataitem(A; Integer)\n        {\n" \
          b"            dataitem(B; Integer)\n            {\n#if X\n            }\n#endif\n        }\n    }\n}\n"
    witness.assert_produces(al_parser, src, "preproc_split_report_brace_close")
    with pytest.raises(LoweringError) as err:
        _lower(al_parser, src, {"X"})
    assert err.value.kind == "unconsumed-fragment"
    assert err.value.node.kind == "preproc_split_report_brace_close"
