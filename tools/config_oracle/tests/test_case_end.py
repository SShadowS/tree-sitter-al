import pytest

from tools.config_oracle import compare, ir, reference
from tools.config_oracle.directives import configurations, discover, resolve
from tools.config_oracle.lowering import lower_tree
from tools.config_oracle.lowering.engine import LoweringError

# Shape of the former BC.History site Check.Report.al:844 (the current corpus copy
# no longer carries the #if).
CASE_END = b"""codeunit 50000 T
{
    procedure P()
    begin
        case BalancingType of
            BalancingType::Vendor:
                begin
                    Vendor.Get(BalancingNo);
                end;
            BalancingType::Employee:
#if not CLEAN27
                ApplyBalancingTypeOfEmployee();
            end;

            CheckToAddr[1] := PadStr(CheckToAddr[1], 10, '*');
            CheckDateText := UpperCase(CheckDateText);
#else
                begin
                    Employee.Get(BalancingNo);
                end
            end;

            CheckDateText := Format("Posting Date", 0, 4);
#endif
    end;
}
"""

# No case_body before the #if: the final branch is the only one, so the
# case_body must be created. Two patterns, and an #elif arm.
CASE_END_NO_BODY = b"""codeunit 50000 T
{
    procedure P()
    begin
        case X of
            1, 2:
#if A
                y := 1;
            end;
            z := 1;
#elif B
                y := 2
            end;
            z := 2;
            z := 3;
#else
                y := 3;
            end;
            z := 4;
#endif
    end;
}
"""

# A conditional pattern in the final branch's pattern run is milestone 2.
CASE_END_COND_PATTERN = b"""codeunit 50000 T
{
    procedure P()
    begin
        case X of
            1,
#if C
            3,
#endif
            2:
#if A
                y := 1;
            end;
            z := 1;
#else
                y := 3;
            end;
            z := 4;
#endif
    end;
}
"""


def kinds(parser, src):
    root, _, _ = ir.from_tree(parser.parse(src))
    out, stack = set(), [root]
    while stack:
        n = stack.pop()
        out.add(n.kind)
        stack.extend(n.children)
    return out


def first_statement_block(root):
    stack = [root]
    while stack:
        n = stack.pop(0)
        if n.kind == "statement_block":
            return n
        stack.extend(n.children)
    raise AssertionError("no statement_block")


def lowered_and_ref(parser, src, env):
    root, extras, problems = ir.from_tree(parser.parse(src))
    assert problems == []
    res = resolve(src, env)
    low, low_extras, _ = lower_tree(root, extras, res)
    ref = reference.extract(parser, res.masked)
    assert ref.problems == []
    return low, ref, res, low_extras


def test_fixtures_exercise_the_intended_types(al_parser):
    for src in (CASE_END, CASE_END_NO_BODY, CASE_END_COND_PATTERN):
        assert "preproc_split_case_statement_end" in kinds(al_parser, src)
    assert "preproc_conditional_case_patterns" in kinds(al_parser, CASE_END_COND_PATTERN)


@pytest.mark.parametrize("src", [CASE_END, CASE_END_NO_BODY], ids=["with_body", "no_body_elif"])
def test_positive_control_every_configuration(al_parser, src):
    n = 0
    for env in configurations(discover(src)):
        n += 1
        low, ref, res, low_extras = lowered_and_ref(al_parser, src, env)
        ds = (compare.structure(ref.root, low)
              + compare.coverage(src, res.active, low, low_extras, "low")
              + compare.trivia(res.extras, ref.extras, low_extras))
        assert ds == [], (sorted(env), ds)
    assert n >= 2


def test_following_are_siblings_after_the_terminator(al_parser):
    low, _, _, _ = lowered_and_ref(al_parser, CASE_END, frozenset())
    block = first_statement_block(low)
    assert [c.kind for c in block.children] == ["case_statement", ";", "assignment_statement", ";",
                                                  "assignment_statement", ";"]
    case = block.children[0]
    assert case.children[-1].kind == "end_keyword"
    assert not any(c.kind == "assignment_statement" for c in case.children)


def test_following_inside_case_is_detected(al_parser):
    """Hand-built BAD lowered tree (not lowering output): the Following statements
    moved INSIDE the case_statement. The comparator must report it."""
    low, ref, _, _ = lowered_and_ref(al_parser, CASE_END, frozenset())
    block = first_statement_block(low)
    case = next(c for c in block.children if c.kind == "case_statement")
    after = block.children[block.children.index(case) + 2:]      # past the ';' Terminator
    assert [s.kind for s in after] == ["assignment_statement", ";", "assignment_statement", ";"]
    for s in after:
        block.children.remove(s)
    case.children[-1:-1] = after                                 # before case's end_keyword
    ds = compare.structure(ref.root, low)
    # Reported as missing from the host block and extra inside the case, naming
    # each moved statement (the comparator does not use `parent` for this move).
    moved = {(d.kind, d.path.split("/")[-2].split(".")[0], d.detail) for d in ds}
    assert moved == {("missing", "statement_block", "assignment_statement"), ("missing", "statement_block", ";"),
                     ("extra", "case_statement", "assignment_statement"), ("extra", "case_statement", ";")}, ds
    assert sum(d.detail == "assignment_statement" for d in ds) == 4


def test_missing_following_field_fails_closed(al_parser):
    """Simulates the grammar mutant that drops `following`: the contract shape is gone."""
    root, extras, _ = ir.from_tree(al_parser.parse(CASE_END))
    stack = [root]
    while stack:
        n = stack.pop()
        if n.field == "following":
            n.field = None
        stack.extend(n.children)
    with pytest.raises(LoweringError) as err:
        lower_tree(root, extras, resolve(CASE_END, frozenset()))
    assert err.value.kind == "contract-shape"


def test_conditional_pattern_run_is_unsupported(al_parser):
    """preproc_conditional_case_patterns is milestone 2: it must raise, never be skipped."""
    root, extras, problems = ir.from_tree(al_parser.parse(CASE_END_COND_PATTERN))
    assert problems == []
    for env in configurations(discover(CASE_END_COND_PATTERN)):
        with pytest.raises(LoweringError) as err:
            lower_tree(root, extras, resolve(CASE_END_COND_PATTERN, env))
        assert err.value.kind == "unsupported-type"
        assert err.value.node.kind == "preproc_conditional_case_patterns"
