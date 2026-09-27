import copy

from tools.config_oracle import compare
from tools.config_oracle.tests.conftest import leaf, node
from tools.config_oracle.ir import Extra


def sample():
    # if_statement over "if c then a else b ;" at invented offsets
    return node("statement_block",
                node("if_statement",
                     leaf("if", 0, 2),
                     node("identifier", leaf("c", 3, 4, named=False), field="condition"),
                     leaf("then", 5, 9),
                     node("call_expression", leaf("a", 10, 11, named=True), field="then_branch"),
                     leaf("else", 12, 16),
                     node("call_expression", leaf("b", 17, 18, named=True), field="else_branch")),
                leaf(";", 19, 20))


def kinds(ds):
    return sorted({(d.check, d.kind) for d in ds})


def test_clean_control_passes():
    assert compare.structure(sample(), sample()) == []


def test_delete_is_missing():
    low = sample(); del low.children[0].children[5]
    assert ("structure", "missing") in kinds(compare.structure(sample(), low))


def test_duplicate_is_extra():
    low = sample(); low.children.append(leaf(";", 21, 22))
    assert ("structure", "extra") in kinds(compare.structure(sample(), low))


def test_reparent_keeping_type_and_span_is_parent():
    low = sample()
    call = low.children[0].children.pop(5)   # else_branch moved to statement_block
    low.children.insert(1, call)
    assert ("structure", "parent") in kinds(compare.structure(sample(), low))


def test_swapped_then_else_is_field():
    low = sample()
    t, e = low.children[0].children[3], low.children[0].children[5]
    t.field, e.field = e.field, t.field
    assert ("structure", "field") in kinds(compare.structure(sample(), low))


def test_renamed_kind_is_kind():
    low = sample(); low.children[0].children[3].kind = "call_statement"
    assert ("structure", "kind") in kinds(compare.structure(sample(), low))


def test_swapped_siblings_is_order():
    ref = node("statement_block", leaf("x", 0, 1, named=True), leaf("y", 2, 3, named=True))
    low = node("statement_block", leaf("y", 2, 3, named=True), leaf("x", 0, 1, named=True))
    assert kinds(compare.structure(ref, low)) == [("structure", "order")]


def test_identical_text_other_arm_provenance_is_detected():
    ref = node("statement_block", leaf("Foo", 10, 13, named=True))
    low = node("statement_block", leaf("Foo", 30, 33, named=True))   # same text, other arm
    assert ("structure", "missing") in kinds(compare.structure(ref, low))


def test_coverage_uncovered_double_masked():
    src = b"ab cd"
    active = bytearray([1, 1, 1, 1, 0])
    root = node("x", leaf("a", 0, 1), leaf("a", 0, 1), leaf("d", 4, 5))
    ks = kinds(compare.coverage(src, active, root, [], side="low"))
    assert ks == [("coverage", "double"), ("coverage", "masked"), ("coverage", "uncovered")]


def test_trivia_missing_event():
    events = [Extra("comment", 0, 4)]
    ks = kinds(compare.trivia(events, [Extra("comment", 0, 4)], []))
    assert ks == [("trivia", "missing")]


def test_ids_are_stable_and_distinct():
    a = compare.Discrepancy("structure", "missing", "if_statement.-@0", "")
    b = compare.Discrepancy("structure", "missing", "if_statement.-@9", "")
    assert compare.discrepancy_id("f#1", "A=1", a) != compare.discrepancy_id("f#1", "A=1", b)
    assert compare.discrepancy_id("f#1", "A=1", a) == compare.discrepancy_id("f#1", "A=1", copy.copy(a))
