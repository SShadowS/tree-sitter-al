from tools.config_oracle.tests import witness

BASE = b"codeunit 1 T\n{\n    procedure P(C: Boolean)\n    begin\n        if C then begin\n            A();\n#if X\n        end else begin\n            B();\n#endif\n            D();\n        end;\n    end;\n}\n"
# test/corpus/split_else_begin_reopen_chain_test.txt's source.
WIDENED = b"codeunit 1 T\n{\n    procedure P(A: Boolean; B: Boolean; L: Boolean; S: Boolean)\n    var\n        C: Integer;\n    begin\n        if A then begin\n            C := 1;\n            if B then begin\n                C := 2;\n#if not C28\n                C := 3;\n            end;\n        end else\n            if L then begin\n                C := 4;\n                if S then begin\n                    C := 5;\n#endif\n                end;\n            end;\n        C := 6;\n    end;\n}\n"


def test_base_shape_both_configs(al_parser):
    witness.assert_produces(al_parser, BASE, "preproc_split_else_begin_over_endif")
    witness.assert_all_pass(al_parser, BASE)


def test_widened_shape_one_reading(al_parser):
    witness.assert_produces(al_parser, WIDENED, "preproc_split_else_begin_over_endif")
    v = witness.verdicts(al_parser, WIDENED)
    assert v["C28=1"][0] == "pass", v
    assert any(i.startswith("lowering:one-reading") for i in v["C28=0"][1]), v


def test_else_statements_on_host_block_is_a_discrepancy(al_parser, monkeypatch):
    """Mutation control: the else block's statements go to the host block
    instead. Every leaf is kept once, so only the comparator can catch it."""
    from tools.config_oracle.lowering import assemblers
    from tools.config_oracle.lowering.engine import BlockCompletion, ElseAttachment
    orig = assemblers.else_begin_over_endif

    def mutated(node, ctx):
        out = orig(node, ctx)
        [bc, ea] = out.frags
        assert isinstance(bc, BlockCompletion) and isinstance(ea, ElseAttachment)
        body = next(c for c in ea.branch.children if c.field == "body")
        bc.statements = bc.statements + body.children
        ea.branch.children.remove(body)
        return out
    monkeypatch.setattr(assemblers, "else_begin_over_endif", mutated)
    v = witness.verdicts(al_parser, BASE)
    assert v["X=1"][0] == "discrepancy", v
