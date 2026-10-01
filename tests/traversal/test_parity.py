"""The shared expected-visit files (D4): one per fixture, current with the Python walker.

JS (tests/traversal/js/parity.test.js) and Rust (bindings/rust/traversal.rs) compare
their own walks against the same files, so the three runtimes agree byte for byte
on class, type, field, offsets, arm identity, host policy and SplitInfo.
"""
import json

import pytest

import support

ALS = sorted(support.FIXTURES.glob("*.al"))


def test_every_fixture_has_an_expected_file_and_no_file_is_orphaned():
    assert len(ALS) == 13
    assert sorted(p.stem for p in support.FIXTURES.glob("*.visits.json")) == \
        sorted(p.stem + ".visits" for p in ALS)


@pytest.mark.parametrize("path", ALS, ids=[p.name for p in ALS])
def test_expected_visits_are_current(T, policy, al_parser, path):
    source = path.read_bytes()
    doc = T.Document(al_parser.parse(source), source, policy)
    want = path.with_suffix(".visits.json").read_text(encoding="utf-8")
    got = T.dump_expected(doc, T.walk(doc, policy))
    assert got == want, f"{path.name}: run tests/traversal/regen_expected.py, then review the diff"
    assert json.loads(want)["revision"] == doc.revision


def test_arm_pieces_file_is_current(T, policy, al_parser):
    path = support.FIXTURES / "assemblers.al"
    source = path.read_bytes()
    doc = T.Document(al_parser.parse(source), source, policy)
    want = path.with_suffix(".arm_pieces.json").read_text(encoding="utf-8")
    assert T.arm_pieces_to_json(doc, T.walk(doc, policy), policy) == want, \
        "run tests/traversal/regen_expected.py, then review the diff"


def test_arm_pieces_reach_statements_inside_a_fragment(T, policy, parse):
    """Hand-checked offsets from the LF fixture: Message('two') 927-941, Message('deux') 1014-1029.
    Unexpanded, each sits inside a preproc_split_case_end_branch fragment and is no piece."""
    doc = parse("assemblers.al")
    case = next(v for v in T.walk(doc, policy) if v.start == 827 and v.split)
    arms = case.split.groups[0].arms
    assert [(f.field, f.type, f.node.start_byte, f.node.end_byte) for f in T.arm_pieces(arms[0], doc, policy)][0] == \
        ("body", "call_expression", 927, 941)
    assert [(f.field, f.type, f.node.start_byte, f.node.end_byte) for f in T.arm_pieces(arms[1], doc, policy)][0] == \
        ("body", "call_expression", 1014, 1029)
    assert all(f.node.start_byte != 927 or f.node.end_byte != 941 for f in arms[0].fragments)


def test_arm_pieces_expands_a_fragment_inside_a_fragment(T, policy, al_parser):
    """No fragment type can hold another in today's grammar (node-types.json), so recursion
    is proved under a policy that also classes statement_block as a fragment: the
    `following` statement_block inside preproc_split_case_end_branch then opens up too."""
    nested = T.Policy({**policy.types, "statement_block": {"class": "fragment"}})
    source = (support.FIXTURES / "assemblers.al").read_bytes()
    doc = T.Document(al_parser.parse(source), source, nested)
    case = next(v for v in T.walk(doc, nested) if v.start == 827 and v.split)
    got = [(f.field, f.type, f.node.start_byte, f.node.end_byte)
           for f in T.arm_pieces(case.split.groups[0].arms[0], doc, nested)]
    assert got == [("body", "call_expression", 927, 941), (None, ";", 941, 942),
                   (None, "end_keyword", 955, 958), (None, ";", 958, 959),
                   (None, "call_expression", 972, 990), (None, ";", 990, 991)]
