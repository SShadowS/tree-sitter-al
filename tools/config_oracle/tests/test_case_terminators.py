"""Case-branch separators (B7b-3 spec 6.2, amended by the Task 6/7 rulings).

A case branch's `;` alone in an `#if` arm is an empty_statement inside a sibling
preproc_conditional_case (spec 4.1). Where the arm is selected, the flat reading gives that `;`
to the immediately preceding unterminated branch: lowering appends it (outside `body`, or into a
body that owns an optional trailing `;`). Directive-only empty groups before a branch's own `;`
are decorations, deleted by selection after every arm is validated. Mutation tests at the end:
each applies one defect and shows the oracle (or the unit check) catches it.
"""
import json
from pathlib import Path

import pytest

from tools.config_oracle import contracts, ir
from tools.config_oracle.ir import Node
from tools.config_oracle.lowering import case_terminators as ct
from tools.config_oracle.lowering import engine
from tools.config_oracle.lowering.engine import ARM_SEMI, Lowered
from tools.config_oracle.tests import witness

REPO = Path(__file__).resolve().parents[3]
W = "codeunit 1 T\n{\n    procedure P()\n    begin\n%s\n    end;\n}\n"


def src(body):
    return (W % body).encode()


def notes(v, config):
    return [i for i in v[config][1] if i.startswith("normalised:case-terminator-attach@")]


def items(v, config):
    return v[config][1]


TRAIL_END = src("case I of\n1: Bar()\n#if X\n;\n#endif\nend;")
SEP_ONLY = src("case I of\n1: Bar()\n#if X\n;\n#else\n;\n#endif\n2: Baz();\nend;")
# The body owns a `;` (inside the block): it does not terminate the branch.
BLOCK_BODY = src("case I of\n1: begin Bar(); end\n#if X\n;\n#else\n;\n#endif\n2: Baz();\nend;")
# A mixed arm: a `;` and a branch in one arm.
MIXED = src("case I of\n1: Bar\n#if X\n;\n2: Baz;\n#endif\nend;")
NESTED = src("case I of\n1: Bar\n#if X\n#if Y\n;\n#endif\n#endif\nend;")
# Two consecutive marked `;`s: the second sees the first's attachment and stays a lone `;`.
TWO_GROUPS = src("case I of\n1: Bar()\n#if S1\n;\n#endif\n#if S2\n;\n#endif\nend;")
# Review Focus 3: a call, a `;` group, then the case else.
BEFORE_ELSE = src("case I of\n1: X\n#if A\n;\n#endif\nelse Y;\nend;")
DECORATION = src("case I of\n1: Bar\n#if X\n#endif\n;\nend;")
DECORATION_ELSE = src("case I of\n1: Bar\n#if X\n#else\n#endif\n;\n2: Baz;\nend;")
DECORATION_NESTED = src("case I of\n1: Bar\n#if X\n#if Y\n#endif\n#endif\n;\nend;")
DECORATION_IN_ARM = src("case I of\n#if A\n1: Bar\n#if X\n#endif\n;\n2: Bar;\n#endif\nend;")
DECORATION_END_BRANCH = src("case I of\n1: Bar;\n2:\n#if X\nBaz\n#if Y\n#endif\n;\nend;\nBar;\n"
                            "#else\nBaz;\nend;\nBar;\n#endif")
ASSERTERROR_EMPTY_BODY = src("case I of\n1: asserterror\n#if X\n#endif\n;\nend;")
# Spec 4.4: with X the `;` ends the branch and the else is the case's; without X the flat
# reading gives the else to the if. The tree holds the X reading.
ELSE_OWNERSHIP = src("case I of\n1: if C then Baz\n#if X\n;\n#endif\nelse Bar;\nend;")
NESTEDIF_ELSE = src("case I of\n1: if C then Bar\n#if S1\n;\n#endif\n#if S2\n;\n#endif\nelse\nif C then Baz;\nend;")


# --- termination, marking, attachment (end to end) ------------------------------------------

def test_lone_group_after_an_unterminated_branch(al_parser):
    witness.assert_produces(al_parser, TRAIL_END, "preproc_conditional_case")
    witness.assert_all_pass(al_parser, TRAIL_END)
    v = witness.verdicts(al_parser, TRAIL_END)
    assert notes(v, "X=1") and not notes(v, "X=0"), v


def test_rewrite_log_names_the_semicolon_offset(al_parser):
    v = witness.verdicts(al_parser, TRAIL_END)
    off = TRAIL_END.index(b"\n;\n") + 1
    assert notes(v, "X=1") == [f"normalised:case-terminator-attach@{off}"], v


def test_semicolon_from_if_else(al_parser):
    witness.assert_all_pass(al_parser, SEP_ONLY)
    v = witness.verdicts(al_parser, SEP_ONLY)
    assert notes(v, "X=0") and notes(v, "X=1"), v


def test_a_semicolon_inside_the_body_does_not_terminate(al_parser):
    witness.assert_all_pass(al_parser, BLOCK_BODY)
    v = witness.verdicts(al_parser, BLOCK_BODY)
    assert notes(v, "X=0") and notes(v, "X=1"), v


def test_mixed_arm_semicolon_is_marked(al_parser):
    witness.assert_all_pass(al_parser, MIXED)
    assert notes(witness.verdicts(al_parser, MIXED), "X=1")


def test_nested_arm_semicolon_is_marked(al_parser):
    witness.assert_all_pass(al_parser, NESTED)
    v = witness.verdicts(al_parser, NESTED)
    assert notes(v, "X=1,Y=1") and not notes(v, "X=1,Y=0"), v


def test_second_marked_semicolon_sees_the_first(al_parser):
    v = witness.verdicts(al_parser, TWO_GROUPS)
    for c in ("S1=0,S2=1", "S1=1,S2=0"):
        assert v[c][0] == "pass" and len(notes(v, c)) == 1, v
    # `1: Bar();;` (alc rejects it, classified invalid-config): one attachment only.
    assert len(notes(v, "S1=1,S2=1")) == 1 or v["S1=1,S2=1"][0] != "pass", v


def test_case_semi_before_case_else(al_parser):
    """Review Focus 3: the `;` attaches to the branch, the else stays the case's."""
    witness.assert_all_pass(al_parser, BEFORE_ELSE)
    v = witness.verdicts(al_parser, BEFORE_ELSE)
    assert notes(v, "A=1") and not notes(v, "A=0"), v


# --- decorations ------------------------------------------------------------------------------

@pytest.mark.parametrize("source", [DECORATION, DECORATION_ELSE, DECORATION_NESTED, DECORATION_IN_ARM],
                         ids=["plain", "else", "nested", "in-arm"])
def test_decoration_is_deleted(al_parser, source):
    witness.assert_all_pass(al_parser, source)


def test_decoration_in_split_case_end_branch(al_parser):
    witness.assert_produces(al_parser, DECORATION_END_BRANCH, "preproc_split_case_end_branch")
    witness.assert_all_pass(al_parser, DECORATION_END_BRANCH)


def test_asserterror_with_an_empty_group_body_lowers_bodyless(al_parser):
    witness.assert_all_pass(al_parser, ASSERTERROR_EMPTY_BODY)


def _inject(monkeypatch, line_marker, source):
    """Put an empty_statement into the decoration's arm, at the comment line `line_marker`
    (its bytes are the injected `;` leaf, so the accounting sees a leaf of the tree)."""
    real = ir.from_tree
    at = source.index(line_marker)

    def from_tree(tree):
        root, extras, problems = real(tree)
        stack = [root]
        while stack:
            n = stack.pop()
            if n.kind == "case_branch":
                for c in n.children:
                    if c.kind == "preproc_conditional_case":
                        semi = Node(";", False, None, at, at + 1, [])
                        es = Node("empty_statement", True, None, at, at + 1, [semi])
                        endif = next(i for i, k in enumerate(c.children) if k.kind == "preproc_endif")
                        # before the #else (if any): the first arm; else before #endif
                        els = next((i for i, k in enumerate(c.children) if k.kind == "preproc_else"), endif)
                        pos = els if line_marker == b"// in-if" else endif
                        c.children.insert(pos, es)
                        return root, extras, problems
            stack.extend(n.children)
        return root, extras, problems   # the reference's flat parse: no decoration

    monkeypatch.setattr(ir, "from_tree", from_tree)


INACTIVE_ARM = src("case I of\n1: Bar\n#if X\n#else\n// in-else\n#endif\n;\nend;")
ACTIVE_ARM = src("case I of\n1: Bar\n#if X\n// in-if\n#else\n#endif\n;\nend;")


def test_a_semicolon_in_an_inactive_decoration_arm_is_refused(al_parser, monkeypatch):
    _inject(monkeypatch, b"// in-else", INACTIVE_ARM)
    v = witness.verdicts(al_parser, INACTIVE_ARM)
    for c in ("X=0", "X=1"):
        assert v[c][0] == "cannot-validate" and "case decoration" in " ".join(items(v, c)), v


def test_a_semicolon_in_the_active_decoration_arm_is_refused(al_parser, monkeypatch):
    _inject(monkeypatch, b"// in-if", ACTIVE_ARM)
    v = witness.verdicts(al_parser, ACTIVE_ARM)
    assert v["X=1"][0] == "cannot-validate" and "case decoration" in " ".join(items(v, "X=1")), v


# --- else ownership (spec 4.4) ----------------------------------------------------------------

def test_else_ownership_represented_configuration_passes(al_parser):
    v = witness.verdicts(al_parser, ELSE_OWNERSHIP)
    assert v["X=1"][0] == "pass", v


def test_else_ownership_alternate_configuration_is_refused(al_parser):
    v = witness.verdicts(al_parser, ELSE_OWNERSHIP)
    assert v["X=0"][0] == "cannot-validate", v
    assert items(v, "X=0")[0].startswith("lowering:one-reading:"), v


def test_nestedif_before_else_both_ways(al_parser):
    v = witness.verdicts(al_parser, NESTEDIF_ELSE)
    for c in ("S1=0,S2=1", "S1=1,S2=0"):
        assert v[c][0] == "pass", v
    assert items(v, "S1=0,S2=0")[0].startswith("lowering:one-reading:"), v


def test_else_ownership_is_decided_without_the_reference(al_parser):
    """Lowering alone refuses it: no reference parse exists in this call."""
    from tools.config_oracle import directives
    root, extras, _ = ir.from_tree(al_parser.parse(ELSE_OWNERSHIP))
    disc = directives.discover(ELSE_OWNERSHIP)
    for env in directives.configurations(disc):
        res = directives.resolve(ELSE_OWNERSHIP, env)
        if directives.config_id(env, disc.free_symbols) == "X=0":
            with pytest.raises(engine.LoweringError) as e:
                engine.lower_tree(root, extras, res)
            assert e.value.kind == "one-reading"
        else:
            engine.lower_tree(root, extras, res)


# --- unit: attach on synthetic runs -----------------------------------------------------------

class _Ctx:
    def __init__(self):
        self.normalised = []


def _branch(start, *, semi=False, body_kind="call_statement", body_semi=False):
    body_kids = [Node("identifier", True, None, start + 3, start + 4, [])]
    if body_semi:
        body_kids.append(Node(";", False, None, start + 4, start + 5, []))
    body = Node(body_kind, True, "body", start + 3, body_kids[-1].end, body_kids)
    kids = [Node("integer", True, "pattern", start, start + 1, []), Node(":", False, None, start + 1, start + 2, []), body]
    if semi:
        kids.append(Node(";", False, None, start + 6, start + 7, []))
    return Node("case_branch", True, None, start, kids[-1].end, kids)


def _marked(at):
    es = Node("empty_statement", True, None, at, at + 1, [Node(";", False, None, at, at + 1, [])])
    setattr(es, ct.CASE_SEMI, True)
    return es


def _kinds(n):
    return [c.kind for c in n.children]


def test_attach_outside_body():
    out = ct.attach([_branch(0), _marked(10)], _Ctx())
    assert len(out) == 1 and _kinds(out[0])[-1] == ";" and out[0].children[-1].field is None
    assert out[0].end == 11
    assert not any(c.kind == ";" for c in out[0].children[2].children)


def test_attach_into_a_semi_owning_body():
    out = ct.attach([_branch(0, body_kind="preproc_split_if_begin_asymmetric"), _marked(10)], _Ctx())
    body = out[0].children[2]
    assert _kinds(out[0])[-1] != ";" and body.children[-1].kind == ";" and body.end == 11 and out[0].end == 11


@pytest.mark.parametrize("before", ["terminated", "empty_statement", "start", "terminated-after-open"])
def test_no_attachment(before):
    run = {"terminated": [_branch(0, semi=True)],
           "empty_statement": [_branch(0), Node("empty_statement", True, None, 8, 9, [Node(";", False, None, 8, 9, [])])],
           "start": [],
           "terminated-after-open": [_branch(0), _branch(20, semi=True)]}[before]
    ctx = _Ctx()
    out = ct.attach(run + [_marked(40)], ctx)
    assert out[-1].kind == "empty_statement" and not ctx.normalised
    assert [n.children[-1].kind for n in out if n.kind == "case_branch"] == \
        [n.children[-1].kind for n in run if n.kind == "case_branch"]


def test_a_semicolon_inside_the_body_is_not_termination():
    ctx = _Ctx()
    out = ct.attach([_branch(0, body_semi=True), _marked(10)], ctx)
    assert len(out) == 1 and ctx.normalised


def test_consecutive_marks_second_sees_first():
    ctx = _Ctx()
    out = ct.attach([_branch(0), _marked(10), _marked(12)], ctx)
    assert [n.kind for n in out] == ["case_branch", "empty_statement"] and len(ctx.normalised) == 1


def test_case_semi_is_not_arm_semi():
    assert ct.CASE_SEMI != ARM_SEMI
    # The statement-block normalisation never takes a case-marked `;`.
    out = engine.absorb_arm_terminators([_branch(0), _marked(10)], _Ctx())
    assert out[-1].kind == "empty_statement"


# --- registry and grammar contracts -----------------------------------------------------------

def test_semi_owning_bodies_match_the_grammar():
    """The tuple is the set of statement rules (reachable from _statement_inner) whose rule ends
    in optional(';'), derived from src/grammar.json."""
    rules = json.loads((REPO / "src" / "grammar.json").read_text(encoding="utf-8"))["rules"]
    wrap = {"PREC", "PREC_LEFT", "PREC_RIGHT", "PREC_DYNAMIC", "FIELD", "ALIAS", "RESERVED"}

    def ends(r, seen=()):
        t = r["type"]
        if t == "SEQ":
            return ends(r["members"][-1], seen)
        if t == "CHOICE":
            m = r["members"]
            if any(x["type"] == "BLANK" for x in m) and any(x.get("value") == ";" for x in m):
                return True
            return any(ends(x, seen) for x in m if x["type"] != "BLANK")
        if t in wrap:
            return ends(r["content"], seen)
        n = r.get("name", "")
        if t == "SYMBOL" and n.startswith("_") and n in rules and n not in seen:
            return ends(rules[n], seen + (n,))
        return False

    def visible(r, acc, seen):
        if r["type"] == "SYMBOL":
            n = r["name"]
            if n.startswith("_") and n in rules:
                if n not in seen:
                    seen.add(n)
                    visible(rules[n], acc, seen)
            else:
                acc.add(n)
        for x in r.get("members", []):
            visible(x, acc, seen)
        if "content" in r:
            visible(r["content"], acc, seen)

    stmts = set()
    visible(rules["_statement_inner"], stmts, set())
    assert set(ct.SEMI_OWNING_BODIES) == {k for k in stmts if ends(rules[k])}


def test_registry_dispatch():
    e = contracts.REGISTRY["preproc_conditional_case"]
    assert e.handler == "tools.config_oracle.lowering.case_terminators.case_group"
    assert {h.split(":")[0] for h, p in e.hosts.items() if p == "decoration"} == set(ct.DECORATION_HOSTS)
    assert e.hosts["case_body:<children>"] == "splice-repeat"
    assert e.hosts["preproc_conditional_case:<children>"] == "splice-repeat"
    assert {"case_branch", "empty_statement", "preproc_conditional_case"} == set(e.arm)
    assert "case_else_branch" not in e.arm   # conditional case else stays cannot-validate debt


# --- mutation tests: each defect must be caught -----------------------------------------------

def _not_all_pass(al_parser, source):
    v = witness.verdicts(al_parser, source)
    return any(s != "pass" for s, _ in v.values())


def test_mutation_semicolon_left_beside_the_branch(al_parser, monkeypatch):
    monkeypatch.setattr(ct, "attach", lambda kids, ctx: kids)
    assert _not_all_pass(al_parser, TRAIL_END)


def test_mutation_attached_across_a_terminated_branch(monkeypatch):
    def search_back(out):
        return next((i for i in range(len(out) - 1, -1, -1)
                     if out[i].kind == "case_branch" and not ct.terminated(out[i])), None)
    monkeypatch.setattr(ct, "_target", search_back)
    with pytest.raises(AssertionError):
        test_no_attachment("terminated-after-open")


def test_mutation_semicolon_placed_inside_body(al_parser, monkeypatch):
    monkeypatch.setattr(ct, "SEMI_OWNING_BODIES", ("call_statement", "call_expression", "identifier"))
    assert _not_all_pass(al_parser, TRAIL_END)


def test_mutation_semicolon_inside_body_counts_as_termination(al_parser, monkeypatch):
    monkeypatch.setattr(ct, "terminated", lambda n: any(lf.kind == ";" for lf in n.leaves()))
    assert _not_all_pass(al_parser, BLOCK_BODY)


def test_mutation_nested_provenance_lost(al_parser, monkeypatch):
    real = ct.case_group

    def strip(node, ctx):
        out = real(node, ctx)
        if ctx.parent_kind == "preproc_conditional_case":
            for n in out.nodes:
                if hasattr(n, ct.CASE_SEMI):
                    delattr(n, ct.CASE_SEMI)
        return out
    monkeypatch.setattr(ct, "case_group", strip)
    assert _not_all_pass(al_parser, NESTED)


def test_mutation_decoration_provenance_lost(al_parser, monkeypatch):
    from tools.config_oracle.lowering import select
    monkeypatch.setattr(ct, "case_group", lambda node, ctx: select.branch_select(node, ctx))
    assert _not_all_pass(al_parser, DECORATION)


def test_mutation_decoration_emits_a_semicolon(al_parser, monkeypatch):
    def emitting(node, ctx):
        ct._delete_decoration(node, ctx)
        return Lowered([Node(";", False, None, node.start, node.start + 1, [])])
    monkeypatch.setattr(ct, "decoration", emitting)
    assert _not_all_pass(al_parser, DECORATION)


def test_mutation_inactive_decoration_arm_dropped(al_parser, monkeypatch):
    monkeypatch.setattr(ct, "_validate_decoration", lambda node: None)
    _inject(monkeypatch, b"// in-else", INACTIVE_ARM)
    v = witness.verdicts(al_parser, INACTIVE_ARM)
    assert v["X=1"][0] == "pass", "the mutation should drop the injected `;` silently"
    with pytest.raises(AssertionError):
        assert v["X=1"][0] == "cannot-validate"   # what test_a_semicolon_in_an_inactive... asserts


def test_mutation_missing_refusal(al_parser, monkeypatch):
    monkeypatch.setattr(ct, "check_else_ownership", lambda case, ctx: None)
    v = witness.verdicts(al_parser, ELSE_OWNERSHIP)
    assert not items(v, "X=0") or not items(v, "X=0")[0].startswith("lowering:one-reading:"), v
    assert v["X=0"][0] != "pass", "without the refusal the alternate reading must not pass silently"


# --- empty-body-terminator (controller ruling 1) ----------------------------------------------

EMPTY_BODY = src("case I of\n1:\n#if X\n#endif\n;\nend;")
EMPTY_BODY_ARM = src("case I of\n1:\n#if X\nBar()\n#endif\n;\nend;")


def _body_notes(v, config):
    return [i for i in v[config][1] if i.startswith("normalised:empty-body-terminator@")]


def test_empty_body_becomes_the_branch_semicolon(al_parser):
    witness.assert_all_pass(al_parser, EMPTY_BODY)
    v = witness.verdicts(al_parser, EMPTY_BODY)
    off = EMPTY_BODY.index(b"\n;\n") + 1
    assert _body_notes(v, "X=0") == _body_notes(v, "X=1") == [f"normalised:empty-body-terminator@{off}"], v


def test_body_removed_only_where_the_arm_is_inactive(al_parser):
    witness.assert_all_pass(al_parser, EMPTY_BODY_ARM)
    v = witness.verdicts(al_parser, EMPTY_BODY_ARM)
    assert _body_notes(v, "X=0") and not _body_notes(v, "X=1"), v


def test_empty_body_unit():
    orig = _branch(0, semi=True)
    new = orig.copy(children=[c for c in orig.children if c.field != "body"])
    ctx = _Ctx()
    ct.empty_body(orig, new, ctx)
    body = [c for c in new.children if c.field == "body"]
    assert len(body) == 1 and body[0].kind == "empty_statement" and body[0].children[0].kind == ";"
    assert not any(ct._is_semi(c) for c in new.children) and ctx.normalised == ["empty-body-terminator@6"]


def test_empty_body_without_a_semicolon_is_refused():
    orig = _branch(0)
    new = orig.copy(children=[c for c in orig.children if c.field != "body"])
    ct.empty_body(orig, new, _Ctx())
    with pytest.raises(engine.LoweringError) as e:
        ct.attach([new], _Ctx())
    assert e.value.kind == "policy"


def test_empty_body_filled_by_a_following_case_group_semicolon():
    orig = _branch(0)
    new = orig.copy(children=[c for c in orig.children if c.field != "body"])
    ctx = _Ctx()
    ct.empty_body(orig, new, ctx)
    out = ct.attach([new, _marked(10)], ctx)
    body = [c for c in out[0].children if c.field == "body"]
    assert len(out) == 1 and body[0].kind == "empty_statement" and ctx.normalised == ["empty-body-terminator@10"]


# `1: #if X ; #endif #if not X ; #endif`: with X=0 the body group goes and the case group's `;` is the body.
EMPTY_BODY_THEN_GROUP = src("case I of\n1:\n#if X\n;\n#endif\n#if not X\n;\n#endif\nend;")


def test_empty_body_then_case_group(al_parser):
    witness.assert_all_pass(al_parser, EMPTY_BODY_THEN_GROUP)
    assert _body_notes(witness.verdicts(al_parser, EMPTY_BODY_THEN_GROUP), "X=0")


def test_mutation_empty_body_rewrite_disabled(al_parser, monkeypatch):
    monkeypatch.setattr(ct, "empty_body", lambda orig, new, ctx: None)
    assert _not_all_pass(al_parser, EMPTY_BODY)
