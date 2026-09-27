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


def triples(ds):
    return sorted({(d.check, d.kind, d.path) for d in ds})


ROOT = "statement_block.-@0-2"
IF_STMT = ROOT + "/if_statement.-@0-2"
THEN_BRANCH = IF_STMT + "/call_expression.then_branch@10-11"
ELSE_BRANCH = IF_STMT + "/call_expression.else_branch@17-18"
REF_SEMI = ROOT + "/;.-@19-20"


def test_clean_control_passes():
    assert compare.structure(sample(), sample()) == []


def test_delete_is_missing():
    low = sample(); del low.children[0].children[5]
    assert triples(compare.structure(sample(), low)) == [("structure", "missing", ELSE_BRANCH)]


def test_duplicate_new_offsets_is_extra():
    low = sample(); low.children.append(leaf(";", 21, 22))
    assert triples(compare.structure(sample(), low)) == [
        ("structure", "extra", ROOT + "/;.-@21-22")]


def test_duplicate_same_provenance_is_caught_by_both_checks():
    # A second copy of the SAME leaf (identical byte span) appended to the lowered tree.
    src = b"if c then a else b ;      "
    active = bytearray([1] * len(src))
    low_root = sample(); low_root.children.append(leaf(";", 19, 20))
    cov = compare.coverage(src, active, low_root, [], side="low")
    assert ("coverage", "double") in kinds(cov)

    ds = compare.structure(sample(), low_root)
    assert ds != []  # never silently equal
    # Documented behaviour: the tie-break ("earliest") keeps the original ";" as the
    # mutual match, so the duplicate is classified as `parent` (it overlaps the ref
    # ";" but isn't its mutual primary) -- see the fix report for the full trace.
    assert triples(ds) == [("structure", "parent", REF_SEMI)]


def test_reparent_keeping_type_and_span_is_parent():
    low = sample()
    call = low.children[0].children.pop(5)   # else_branch moved to statement_block
    low.children.insert(1, call)
    assert triples(compare.structure(sample(), low)) == [("structure", "parent", ELSE_BRANCH)]


def test_swapped_then_else_is_field():
    low = sample()
    t, e = low.children[0].children[3], low.children[0].children[5]
    t.field, e.field = e.field, t.field
    assert triples(compare.structure(sample(), low)) == sorted([
        ("structure", "field", THEN_BRANCH),
        ("structure", "field", ELSE_BRANCH),
    ])


def test_renamed_field_is_field():
    low = sample()
    low.children[0].children[3].field = "body"
    assert triples(compare.structure(sample(), low)) == [("structure", "field", THEN_BRANCH)]


def test_renamed_kind_is_kind():
    low = sample(); low.children[0].children[3].kind = "call_statement"
    assert triples(compare.structure(sample(), low)) == [("structure", "kind", THEN_BRANCH)]


def test_swapped_siblings_is_order():
    ref = node("statement_block", leaf("x", 0, 1, named=True), leaf("y", 2, 3, named=True))
    low = node("statement_block", leaf("y", 2, 3, named=True), leaf("x", 0, 1, named=True))
    assert triples(compare.structure(ref, low)) == [("structure", "order", "statement_block.-@0-1")]


def test_dropped_operator_is_missing_at_the_leaf():
    ref = node("binary_expr", leaf("left", 0, 1, named=True), leaf("op", 2, 3, named=False),
               leaf("right", 4, 5, named=True))
    low = node("binary_expr", leaf("left", 0, 1, named=True), leaf("right", 4, 5, named=True))
    assert triples(compare.structure(ref, low)) == [
        ("structure", "missing", "binary_expr.-@0-1/op.-@2-3")]


def test_identical_text_other_arm_provenance_is_detected_at_leaf_level():
    ref = node("statement_block", leaf("Foo", 10, 13, named=True))
    low = node("statement_block", leaf("Foo", 30, 33, named=True))   # same text, other arm
    root_path = "statement_block.-@10-13"
    assert triples(compare.structure(ref, low)) == [
        ("structure", "extra", root_path + "/Foo.-@30-33"),
        ("structure", "missing", root_path + "/Foo.-@10-13"),
    ]


def test_moved_subtree_with_inner_kind_change_realigns():
    # E moves from inside IF to being S's direct sibling; M inside it (moved along
    # with E) has its kind changed. The move must not swallow the inner defect.
    ref = node("S", node("IF", leaf("if", 0, 2),
                          node("E", node("M", leaf("x", 5, 6)))))
    low = node("S", node("IF", leaf("if", 0, 2)),
               node("E", node("ZZZ", leaf("x", 5, 6))))
    e_path = "S.-@0-2/IF.-@0-2/E.-@5-6"
    m_path = e_path + "/M.-@5-6"
    assert triples(compare.structure(ref, low)) == sorted([
        ("structure", "parent", e_path),
        ("structure", "kind", m_path),
    ])


def test_moved_subtree_with_inner_field_change_realigns():
    ref = node("S", node("IF", leaf("if", 0, 2),
                          node("E", node("M", leaf("x", 5, 6)))))
    low = node("S", node("IF", leaf("if", 0, 2)),
               node("E", node("M", leaf("x", 5, 6), field="renamed")))
    e_path = "S.-@0-2/IF.-@0-2/E.-@5-6"
    m_path = e_path + "/M.-@5-6"
    assert triples(compare.structure(ref, low)) == sorted([
        ("structure", "parent", e_path),
        ("structure", "field", m_path),
    ])


def test_chain_move_reports_moved_node_and_the_abandoned_wrapper():
    # E moves out from inside W (which itself was inside IF); W is left holding
    # nothing and must be reported missing, not silently folded into E's move.
    ref = node("S", node("IF", leaf("if", 0, 2),
                          node("W", node("E", leaf("x", 5, 6)))))
    low = node("S", node("IF", leaf("if", 0, 2)),
               node("E", leaf("x", 5, 6)))
    e_path = "S.-@0-2/IF.-@0-2/W.-@5-6/E.-@5-6"
    w_path = "S.-@0-2/IF.-@0-2/W.-@5-6"
    assert triples(compare.structure(ref, low)) == sorted([
        ("structure", "parent", e_path),
        ("structure", "missing", w_path),
    ])


def test_big_moved_child_is_a_single_parent_not_a_cascade():
    # E (which itself has 2 children, M(x) and y) moves whole out of IF. The
    # move must be recognized directly -- not misfire as IF-vs-E overlap pairing
    # cascading into 8 unrelated discrepancies.
    ref = node("S", node("IF", leaf("if", 0, 2),
                          node("E", node("M", leaf("x", 5, 6)), leaf("y", 7, 8))))
    low = node("S", node("IF", leaf("if", 0, 2)),
               node("E", node("M", leaf("x", 5, 6)), leaf("y", 7, 8)))
    e_path = "S.-@0-2/IF.-@0-2/E.-@5-6"
    assert triples(compare.structure(ref, low)) == [("structure", "parent", e_path)]


def test_coverage_uncovered_double_masked():
    src = b"ab cd"
    active = bytearray([1, 1, 1, 1, 0])
    root = node("x", leaf("a", 0, 1), leaf("a", 0, 1), leaf("d", 4, 5))
    ks = kinds(compare.coverage(src, active, root, [], side="low"))
    assert ks == [("coverage", "double"), ("coverage", "masked"), ("coverage", "uncovered")]


def test_coverage_masked_flags_masked_whitespace():
    # Only \r and \n survive masking unmasked; a leaf/extra covering any OTHER masked
    # byte -- including plain whitespace -- must be reported, not silently excused.
    src = b"a b"
    active = bytearray([1, 0, 1])
    root = node("x", leaf("a", 0, 1), leaf("b", 2, 3))
    ks = kinds(compare.coverage(src, active, root, [Extra("ws", 1, 2)], side="low"))
    assert ks == [("coverage", "masked")]


def test_trivia_missing_event():
    events = [Extra("comment", 0, 4)]
    ks = kinds(compare.trivia(events, [Extra("comment", 0, 4)], []))
    assert ks == [("trivia", "missing")]


def test_trivia_duplicated_extra():
    events = [Extra("comment", 0, 4)]
    ref_extras = [Extra("comment", 0, 4)]
    low_extras = [Extra("comment", 0, 4), Extra("comment", 0, 4)]
    ks = kinds(compare.trivia(events, ref_extras, low_extras))
    assert ks == [("trivia", "extra")]


def test_ids_are_stable_and_distinct():
    a = compare.Discrepancy("structure", "missing", "if_statement.-@0", "")
    b = compare.Discrepancy("structure", "missing", "if_statement.-@9", "")
    assert compare.discrepancy_id("f#1", "A=1", a) != compare.discrepancy_id("f#1", "A=1", b)
    assert compare.discrepancy_id("f#1", "A=1", a) == compare.discrepancy_id("f#1", "A=1", copy.copy(a))


def test_ids_escape_pipe_to_avoid_shifted_split_collision():
    d = compare.Discrepancy("structure", "kind", "p", "")
    a = compare.discrepancy_id("a|b", "c", d)
    b = compare.discrepancy_id("a", "b|c", d)
    assert a != b


def test_leaf_boundaries_on_a_split_token():
    ref = node("x", leaf("tok", 0, 4))
    low = node("x", leaf("tok", 0, 2), leaf("tok2", 2, 4))
    ds = compare.leaf_boundaries(ref, low)
    assert kinds(ds) == [("structure", "boundary")]
    assert len(ds) == 1


def test_leaf_boundaries_clean_control():
    assert compare.leaf_boundaries(sample(), sample()) == []
