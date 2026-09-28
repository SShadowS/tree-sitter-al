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


def test_wrong_reading_never_passes(al_parser, monkeypatch):
    """Declaring the wrong reading makes the wrongly-lowered configuration fail
    accounting (the #if arm's leaves are kept on masked lines) and the true
    reading configuration report one-reading. Neither is a pass."""
    from tools.config_oracle import contracts
    e = contracts.REGISTRY["preproc_split_container_reopen"]
    monkeypatch.setitem(contracts.REGISTRY, e.type, contracts.Entry(
        e.type, e.kind, e.handler, e.hosts, e.alias_to, e.arm, "arm:inactive"))
    v = witness.verdicts(al_parser, REOPEN)
    assert v["C28=1"][0] == "cannot-validate" and any(i.startswith("lowering:accounting") for i in v["C28=1"][1]), v
    assert v["C28=0"][0] == "cannot-validate" and any(i.startswith("lowering:one-reading") for i in v["C28=0"][1]), v


# --- Mutation controls (spec P4): for each one-reading member, a structural
# corruption of its lowering must turn the reading configuration's pass into a
# comparator discrepancy. Every corruption keeps each leaf exactly once, so
# accounting still holds and only the comparison can catch it.

# A procedure boundary whose second block closing carries statements after #endif.
TAIL = b"codeunit 1 T\n{\n    procedure P()\n    begin\n        Message('a');\n#if not C28\n        Message('b');\n#else\n        Message('c');\n    end;\n\n    local procedure Q(T: Text): Text\n    begin\n        exit(T);\n#endif\n        Message('t');\n    end;\n}\n"
# The same boundary in an #if / #elif / #else group.
ELIF = b"codeunit 1 T\n{\n    procedure P()\n    begin\n        Message('a');\n#if C27\n        Message('b');\n#elif not C28\n        Message('d');\n#else\n        Message('c');\n    end;\n\n    local procedure Q(T: Text): Text\n    begin\n        exit(T);\n#endif\n        Message('t');\n    end;\n}\n"


def _nest_statements(monkeypatch, name):
    """Mutate handler `name`: its BlockCompletion statements go into an extra,
    nested statement_block instead of the code_block's own."""
    from tools.config_oracle.ir import Node
    from tools.config_oracle.lowering import assemblers
    from tools.config_oracle.lowering.engine import BlockCompletion, _span_from_children
    orig = getattr(assemblers, name)

    def mutated(node, ctx):
        out = orig(node, ctx)
        for f in out.frags:
            if isinstance(f, BlockCompletion):
                assert f.statements, "mutation needs statements to move"
                f.statements = [_span_from_children(Node("statement_block", True, None, 0, 0, f.statements))]
        return out
    monkeypatch.setattr(assemblers, name, mutated)


@pytest.mark.parametrize("name,kind", [("block_end_in_else", "preproc_split_block_end_in_else"),
                                       ("block_close_after_endif", "preproc_split_block_close_after_endif")])
def test_block_mutation_is_a_discrepancy(al_parser, monkeypatch, name, kind):
    witness.assert_produces(al_parser, TAIL, kind)
    assert witness.verdicts(al_parser, TAIL)["C28=1"][0] == "pass"
    _nest_statements(monkeypatch, name)
    v = witness.verdicts(al_parser, TAIL)
    assert v["C28=1"][0] == "discrepancy", v


def test_container_reopen_unmerged_bodies_is_a_discrepancy(al_parser, monkeypatch):
    from tools.config_oracle.ir import Node
    from tools.config_oracle.lowering import assemblers
    orig = assemblers.container_reopen

    def mutated(node, ctx):
        out = orig(node, ctx)
        [sib] = out.frags
        for new in sib.nodes:
            kids = []
            for c in new.children:
                if c.kind == "layout_container_body" and len(c.children) > 1:
                    kids += [Node(c.kind, True, "body", k.start, k.end, [k]) for k in c.children]
                else:
                    kids.append(c)
            new.children = kids
        return out
    monkeypatch.setattr(assemblers, "container_reopen", mutated)
    v = witness.verdicts(al_parser, REOPEN)
    assert v["C28=0"][0] == "discrepancy", v


def test_container_reopen_sibling_before_anchor_is_a_discrepancy(al_parser, monkeypatch):
    from tools.config_oracle.lowering import engine
    orig = engine._consume

    def before(new, frags):
        rest = []
        for f in frags:
            if isinstance(f, engine.SiblingsAfter) and new.kind in engine.LAYOUT_HOSTS \
                    and any(c is f.anchor for c in new.children):
                at = next(i for i, c in enumerate(new.children) if c is f.anchor)
                new.children[at:at] = f.nodes
            else:
                rest.append(f)
        return orig(new, rest)
    monkeypatch.setattr(engine, "_consume", before)
    v = witness.verdicts(al_parser, REOPEN)
    assert v["C28=0"][0] == "discrepancy", v


def test_elif_group_boundary(al_parser):
    witness.assert_produces(al_parser, ELIF, "preproc_split_block_end_in_else")
    witness.assert_produces(al_parser, ELIF, "preproc_split_block_close_after_endif")
    v = witness.verdicts(al_parser, ELIF)
    assert v["C27=0,C28=1"][0] == "pass", v
    others = [c for c in v if c != "C27=0,C28=1"]
    assert len(others) == 3 and all(any(i.startswith("lowering:one-reading") for i in v[c][1]) for c in others), v


@pytest.mark.parametrize("env,active", [(frozenset(), False),            # #elif chosen
                                        (frozenset({"C28"}), True),      # #else chosen
                                        (frozenset({"C27"}), False),     # #if chosen
                                        (frozenset({"C27", "C28"}), False)])
def test_block_close_after_endif_finds_else_not_elif(al_parser, env, active):
    """Called directly: in a whole-input run block_end_in_else raises first."""
    _direct_close_after_endif(al_parser, ELIF, env, active, ["call_expression", ";"])


def _direct_close_after_endif(al_parser, src, env, active, stmt_kinds):
    from tools.config_oracle import ir
    from tools.config_oracle.directives import resolve
    from tools.config_oracle.lowering import assemblers
    from tools.config_oracle.lowering.engine import Accounting, BlockCompletion, Ctx, LoweringError
    root, _, _ = ir.from_tree(al_parser.parse(src))
    stack, node = [root], None
    while stack:
        n = stack.pop()
        if n.kind == "preproc_split_block_close_after_endif":
            node = n
        stack.extend(n.children)
    res = resolve(src, env)
    ctx = Ctx(res, Accounting(res), "code_block", "<children>")
    if not active:
        with pytest.raises(LoweringError) as e:
            assemblers.block_close_after_endif(node, ctx)
        assert e.value.kind == "one-reading"
        return
    out = assemblers.block_close_after_endif(node, ctx)
    [f] = out.frags
    assert not out.nodes and isinstance(f, BlockCompletion)
    assert [s.kind for s in f.statements] == stmt_kinds and f.end.kind == "end_keyword"


@pytest.mark.parametrize("env,active", [(frozenset(), False), (frozenset({"C28"}), True)])
def test_block_close_after_endif_decides_its_reading_on_its_own(al_parser, env, active):
    """In C28=0 the whole-input run stops at block_end_in_else first, so this
    handler's own decision is only visible when it is called directly.
    BOUNDARY's `exit(T);` is in Q's statement_block, so the node's run is empty."""
    _direct_close_after_endif(al_parser, BOUNDARY, env, active, [])
