"""Witnesses (spec 6.1/6.2 item 2, D8): one per policy entry, then the named exceptions.

Every witness runs twice: against the real policy (must pass) and against a mutant
(must FAIL). A witness that cannot fail is not a witness.
"""
import csv
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROWS = [r for r in csv.DictReader((line for line in (HERE / "witnesses.tsv").read_text(encoding="utf-8").splitlines()
                                   if not line.startswith("#")), delimiter="\t")]

# The mutant each class must reject. "transparent" (ordinary) is the spec's named
# mutant for expression_tail (6.2 item 2); ordinary itself is mutated to trivia.
MUTANT = {"branch-container": "ordinary", "assembler": "ordinary", "fragment": "ordinary",
          "token-alias": "ordinary", "directive": "ordinary", "trivia": "ordinary", "ordinary": "trivia"}


def mutate(T, policy, type_, **changes):
    return T.Policy({**policy.types, type_: {**policy.types[type_], **changes}})


def check_witness(T, policy, doc, type_, expected):
    default = [v for v in T.walk(doc, policy) if v.type == type_]
    every = [v for v in T.walk(doc, policy, include_directives=True, include_trivia=True) if v.type == type_]
    assert every, f"the witness does not produce {type_}"
    if expected in ("directive", "trivia"):
        assert default == [], f"{type_} must be skipped unless requested"
        assert {v.cls for v in every} == {expected}
        return
    assert default and {v.cls for v in default} == {expected}
    for v in default:
        if expected == "branch-container":
            assert v.split and v.split.groups and v.host is not None
        elif expected == "assembler":
            assert v.split and v.split.groups
        elif expected == "fragment":
            if v.split is None:
                assert v.arms, "a fragment without its own directives sits in an arm of its consumer"
        elif expected == "token-alias":
            assert v.split is None and v.node.child_count == 0
        else:
            assert v.split is None


@pytest.mark.parametrize("row", ROWS, ids=[r["type"] for r in ROWS])
def test_every_policy_entry_has_a_passing_witness(T, policy, doc_of, row):
    check_witness(T, policy, doc_of(row["source"]), row["type"], row["class"])


@pytest.mark.parametrize("row", ROWS, ids=[r["type"] for r in ROWS])
def test_every_witness_fails_its_mutant(T, policy, doc_of, row):
    bad = mutate(T, policy, row["type"], **{"class": MUTANT[row["class"]]})
    with pytest.raises(AssertionError):
        check_witness(T, bad, doc_of(row["source"]), row["type"], row["class"])


def test_witness_rows_cover_the_policy_exactly(policy):
    assert sorted(r["type"] for r in ROWS) == sorted(policy.types)


# --- the named exceptions of spec 6.1, each with its own assertion and mutant ----------

def frags(arm, doc):
    return [(f.field, f.type, doc.source[f.node.start_byte:f.node.end_byte].decode()) for f in arm.fragments]


def one(T, policy, doc, type_):
    found = [v for v in T.walk(doc, policy) if v.type == type_]
    assert len(found) == 1, f"{len(found)} visits of {type_}"
    return found[0]


def expression_tail(T, policy, doc):
    v = one(T, policy, doc, "preproc_conditional_expression_tail")
    assert v.cls == "assembler" and v.split is not None
    (group,) = v.split.groups
    assert [frags(a, doc) for a in group.arms] == [[("operator", "+", "+"), ("operand", "integer", "1")]]
    # The continuation sits AFTER the expression it extends: `right` is the bare X.
    parent = v.node.parent
    assert parent.type == "assignment_statement"
    assert doc.source[parent.child_by_field_name("right").start_byte:
                      parent.child_by_field_name("right").end_byte] == b"X"


def table_relation(T, policy, doc):
    v = one(T, policy, doc, "preproc_conditional_table_relation")
    assert v.cls == "assembler"
    (group,) = v.split.groups
    assert [[(f, t) for f, t, _ in frags(a, doc)] for a in group.arms] == \
        [[(None, "else_table_relation_fragment"), (None, ";")]] * 2
    fragments = [x for x in T.walk(doc, policy) if x.type == "else_table_relation_fragment"]
    assert [x.cls for x in fragments] == ["fragment", "fragment"]
    assert [x.arms[-1][1] for x in fragments] == [0, 1]


def property_value(T, policy, doc):
    v = one(T, policy, doc, "preproc_conditional_property_value")
    assert v.cls == "assembler" and v.field == "value"
    (group,) = v.split.groups
    assert [frags(a, doc) for a in group.arms] == [[("value", "identifier", "CustomerContent"), (None, ";", ";")],
                                                   [("value", "identifier", "SystemMetadata"), (None, ";", ";")]]


def case_end_branch(T, policy, doc):
    owner = one(T, policy, doc, "preproc_split_case_statement_end")
    (group,) = owner.split.groups
    assert [[t for _, t, _ in frags(a, doc)] for a in group.arms] == [["preproc_split_case_end_branch"]] * 2
    branches = [x for x in T.walk(doc, policy) if x.type == "preproc_split_case_end_branch"]
    assert [(x.cls, x.split, x.arms[-1][1]) for x in branches] == [("fragment", None, 0), ("fragment", None, 1)]


def report_brace_close(T, policy, doc):
    v = one(T, policy, doc, "preproc_split_report_brace_close")
    assert v.cls == "fragment" and v.node.parent.type == "report_dataitem"
    (group,) = v.split.groups
    assert [[t for _, t, _ in frags(a, doc)] for a in group.arms] == [["report_body", "}"], ["report_body"]]


def _split_token(T, policy, doc, type_, alias):
    visits = [x for x in T.walk(doc, policy) if x.type == type_]
    assert visits and {(x.cls, x.split) for x in visits} == {("token-alias", None)}
    assert policy.types[type_]["alias_to"] == alias


def split_begin_token(T, policy, doc):
    _split_token(T, policy, doc, "preproc_split_begin", "begin_keyword")


def split_end_token(T, policy, doc):
    _split_token(T, policy, doc, "preproc_split_end", "end_keyword")


def pragma_in_arm(T, policy, doc):
    assert not [x for x in T.walk(doc, policy) if x.type == "pragma"]
    assert {x.cls for x in T.walk(doc, policy, include_trivia=True) if x.type == "pragma"} == {"trivia"}
    decl = one(T, policy, doc, "preproc_split_declaration")
    first = [t for _, t, _ in frags(decl.split.groups[0].arms[0], doc)]
    assert first[0] == "pragma" and first[-1] == "pragma", "trivia inside an arm stays one of its fragments"


def list_run_separator(T, policy, doc):
    v = one(T, policy, doc, "preproc_conditional_permissions")
    assert v.host == "list-run"
    assert (None, ",", ",") in frags(v.split.groups[0].arms[1], doc)


def list_run_terminator(T, policy, doc):
    v = one(T, policy, doc, "preproc_conditional_permissions")
    assert v.host == "list-run"
    # The PROPERTY's own ';' sits inside each arm (terminator-hoist): the last fragment.
    assert [frags(a, doc)[-1] for a in v.split.groups[0].arms] == [(None, ";", ";")] * 2


NAMED = [  # (check, fixture, policy type to mutate, mutation)
    (expression_tail, "assemblers.al", "preproc_conditional_expression_tail", {"class": "ordinary"}),
    (table_relation, "assemblers.al", "preproc_conditional_table_relation", {"class": "ordinary"}),
    (table_relation, "assemblers.al", "else_table_relation_fragment", {"class": "ordinary"}),
    (property_value, "assemblers.al", "preproc_conditional_property_value", {"class": "ordinary"}),
    (case_end_branch, "assemblers.al", "preproc_split_case_end_branch", {"class": "ordinary"}),
    (report_brace_close, "corpus:preproc_split_brace_and_case_test.txt#A report dataitem whose closing brace is inside a branch#0",
     "preproc_split_report_brace_close", {"class": "ordinary"}),
    (split_end_token, "corpus:preproc_split_code_block_end_elif_test.txt#split code block end: %23elif branch, both branches bare end;#0",
     "preproc_split_end", {"class": "ordinary"}),
    (split_begin_token, "corpus:preproc_begin_end_named_test.txt#PRIORITY GUARD: begin immediately before %23endif stays preproc_split_begin#0",
     "preproc_split_begin", {"class": "ordinary"}),
    (pragma_in_arm, "split_declaration.al", "pragma", {"class": "ordinary"}),
    (list_run_separator, "assemblers.al", "preproc_conditional_permissions",
     {"hosts": {"declaration_body:<children>": "list-run"}}),
    (list_run_terminator, "assemblers.al", "preproc_conditional_permissions",
     {"hosts": {"declaration_body:<children>": "list-run"}}),
]


@pytest.mark.parametrize("check,source,type_,change", NAMED, ids=[f"{c.__name__}-{t}" for c, _, t, _ in NAMED])
def test_named_exception(T, policy, doc_of, check, source, type_, change):
    src = source if source.startswith("corpus:") else "fixture:" + source
    check(T, policy, doc_of(src))
    with pytest.raises(AssertionError):
        check(T, mutate(T, policy, type_, **change), doc_of(src))


@pytest.mark.parametrize("check", [list_run_separator, list_run_terminator])
def test_list_run_witnesses_fail_when_anonymous_tokens_are_dropped(T, policy, doc_of, monkeypatch, check):
    """A code mutant, not a policy one: bind_arm keeping named nodes only."""
    doc = doc_of("fixture:assemblers.al")
    check(T, policy, doc)
    real = T.bind_arm

    def named_only(descriptor, document, pol):
        arm = real(descriptor, document, pol)
        return T.ArmFragments(arm.descriptor, tuple(f for f in arm.fragments if f.node.is_named))

    monkeypatch.setattr(T, "bind_arm", named_only)
    with pytest.raises(AssertionError):
        check(T, policy, doc)
