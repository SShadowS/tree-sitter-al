import pytest

from tools.config_oracle import compare, ir, reference
from tools.config_oracle.directives import configurations, discover, resolve
from tools.config_oracle.lowering import lower_tree

SPLIT_END = b"""codeunit 1 T
{
    procedure X()
    var
        x: Integer;
    begin
        if x = 1 then begin
            x := 9;
#if not CLEAN22
        end; // note
#else
        x := 2;
        end else begin x := 3; end;
#endif
    end;
}
"""

NESTED = b"""codeunit 1 T
{
    procedure X()
    begin
#if OUTER
        if x = 1 then begin
            x := 9;
#if not CLEAN22
        end;
#else
        end else begin x := 3; end;
#endif
#endif
    end;
}
"""

SPLIT_PROC = b"""codeunit 50100 Probe
{
#if FOO
    [Scope('OnPrem')]
    procedure Foo(a: Integer)
#else
    procedure Foo(a: Integer; b: Integer)
#endif
    var
        i: Integer;
    begin
        i := a;
    end;
}
"""

# A single-slot arm holding [statement, ';']: the enclosing statement's terminator
# sits inside the #if arm (real site: BC.History AOAIAuthorization.Codeunit.al).
SLOT_TERMINATOR = b"""codeunit 1 T
{
    trigger OnRun()
    begin
        if c then
#if A
            x := 1;
#else
            x := 2;
#endif
        y := 3;
    end;
}
"""

# A split signature followed by a split BODY (preproc_split_complete_body) is a
# milestone-2 type and deliberately not here; replay 5's HEAD positive control
# covers the pragma-only tail.


def all_configs(parser, src):
    root, extras, problems = ir.from_tree(parser.parse(src))
    assert problems == []
    for env in configurations(discover(src)):
        res = resolve(src, env)
        low, low_extras, _ = lower_tree(root, extras, res)
        ref = reference.extract(parser, res.masked)
        assert ref.problems == [], (env, ref.problems)
        yield env, (compare.structure(ref.root, low)
                    + compare.coverage(src, res.active, low, low_extras, "low")
                    + compare.trivia(res.extras, ref.extras, low_extras))


@pytest.mark.parametrize("src", [SPLIT_END, NESTED, SPLIT_PROC, SLOT_TERMINATOR],
                         ids=["split_end", "nested", "split_proc", "slot_terminator"])
def test_every_configuration_matches(al_parser, src):
    n = 0
    for env, ds in all_configs(al_parser, src):
        n += 1
        assert ds == [], (sorted(env), ds)
    assert n >= 2


def test_fixtures_exercise_the_intended_types(al_parser):
    """Guard against a fixture that silently parses to some other construct."""
    def kinds(src):
        root, _, _ = ir.from_tree(al_parser.parse(src))
        out, stack = set(), [root]
        while stack:
            n = stack.pop()
            out.add(n.kind)
            stack.extend(n.children)
        return out
    assert "preproc_split_code_block_end" in kinds(SPLIT_END)
    assert "preproc_split_code_block_end" in kinds(NESTED)
    assert "preproc_split_procedure" in kinds(SPLIT_PROC)
    assert "preproc_conditional_statement" in kinds(SLOT_TERMINATOR)


def test_else_attachment_needs_an_if_owner(al_parser):
    """False-positive control's mirror: an else-arm that cannot attach must fail loudly, not pass."""
    from tools.config_oracle.lowering.engine import LoweringError
    src = b"codeunit 1 T { trigger OnRun() begin begin x := 9;\n#if A\n end;\n#else\n end else begin x := 3; end;\n#endif\n end; }"
    root, extras, problems = ir.from_tree(al_parser.parse(src))
    if problems:
        pytest.skip("grammar does not produce preproc_split_code_block_end for a bare block; nothing to lower")
    with pytest.raises(LoweringError) as err:
        lower_tree(root, extras, resolve(src, frozenset()))
    assert err.value.kind == "unconsumed-fragment"
