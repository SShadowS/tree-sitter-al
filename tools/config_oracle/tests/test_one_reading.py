import pytest

from tools.config_oracle.tests import witness

REOPEN = b"page 1 P\n{\n    layout\n    {\n        area(Content)\n        {\n            group(G)\n            {\n                field(A; Rec.A) { }\n#if not C28\n            }\n            group(R)\n            {\n                Caption = 'R';\n                field(B; Rec.B) { }\n#endif\n                field(C; Rec.C) { }\n            }\n        }\n    }\n}\n"
BOUNDARY = b"codeunit 1 T\n{\n    procedure P()\n    begin\n        Message('a');\n#if not C28\n        Message('b');\n#else\n        Message('c');\n    end;\n\n    local procedure Q(T: Text): Text\n    begin\n        exit(T);\n#endif\n    end;\n}\n"
ELSE_LED = b"codeunit 1 T\n{\n    procedure P(N: Integer)\n    begin\n        if N < 1 then\n            Message('a')\n#if not C28\n        else begin\n#else\n        else\n#endif\n            Message('b');\n#if not C28\n            Message('c');\n        end;\n#endif\n    end;\n}\n"


@pytest.mark.parametrize("src,kind,reading_config", [
    (REOPEN, "preproc_split_container_reopen", "C28=0"),
    (BOUNDARY, "preproc_split_block_end_in_else", "C28=1"),
    (BOUNDARY, "preproc_split_block_close_after_endif", "C28=1"),
])
def test_reading_passes_other_is_one_reading(al_parser, src, kind, reading_config):
    witness.assert_produces(al_parser, src, kind)
    v = witness.verdicts(al_parser, src)
    assert v[reading_config][0] == "pass", v[reading_config]
    others = [c for c in v if c != reading_config]
    assert others and all(any(i.startswith("lowering:one-reading") for i in v[c][1]) for c in others), v


def test_one_reading_is_never_a_pass(al_parser):
    witness.assert_produces(al_parser, ELSE_LED, "preproc_split_open_statement")
    v = witness.verdicts(al_parser, ELSE_LED)
    assert all(any(i.startswith("lowering:one-reading") for i in items) for _, items in v.values()), v


def test_wrong_reading_declared_turns_pass_into_discrepancy(al_parser, monkeypatch):
    from tools.config_oracle import contracts
    e = contracts.REGISTRY["preproc_split_container_reopen"]
    monkeypatch.setitem(contracts.REGISTRY, e.type, contracts.Entry(
        e.type, e.kind, e.handler, e.hosts, e.alias_to, e.arm, "arm:inactive"))
    v = witness.verdicts(al_parser, REOPEN)
    assert v["C28=1"][0] != "pass", v


@pytest.mark.parametrize("env,active", [(frozenset(), False), (frozenset({"C28"}), True)])
def test_block_close_after_endif_decides_its_reading_on_its_own(al_parser, env, active):
    """In C28=0 the whole-input run stops at block_end_in_else first, so this
    handler's own decision is only visible when it is called directly."""
    from tools.config_oracle import ir
    from tools.config_oracle.directives import resolve
    from tools.config_oracle.lowering import assemblers
    from tools.config_oracle.lowering.engine import Accounting, BlockCompletion, Ctx, LoweringError
    root, _, _ = ir.from_tree(al_parser.parse(BOUNDARY))
    stack, node = [root], None
    while stack:
        n = stack.pop()
        if n.kind == "preproc_split_block_close_after_endif":
            node = n
        stack.extend(n.children)
    res = resolve(BOUNDARY, env)
    ctx = Ctx(res, Accounting(res), "code_block", "<children>")
    if not active:
        with pytest.raises(LoweringError) as e:
            assemblers.block_close_after_endif(node, ctx)
        assert e.value.kind == "one-reading"
        return
    out = assemblers.block_close_after_endif(node, ctx)
    [f] = out.frags
    assert not out.nodes and isinstance(f, BlockCompletion)
    assert f.statements == [] and f.end.kind == "end_keyword"   # exit(T); is in Q's statement_block
