from tools.config_oracle import ir, representation


def reps(parser, src):
    root, _, problems = ir.from_tree(parser.parse(src))
    assert problems == []
    return [(d.kind, d.path.split("@")[0]) for d in representation.check(root)]


VAR_THEN_PRAGMA = b"""codeunit 1 T {
    procedure P()
#if A
    var
        i: Integer;
#else
#pragma warning disable AA0005
#endif
    begin
    end;
}"""

PRAGMA_ONLY_COMMENT = b"""codeunit 1 T {
    procedure P()
#if A
    // just a note
#endif
    begin
    end;
}"""

PRAGMA_ONLY_EMPTY = b"""codeunit 1 T {
    procedure P()
#if A
#else
#endif
    begin
    end;
}"""


def test_var_in_one_arm_pragma_in_other_is_legitimate(al_parser):
    assert reps(al_parser, VAR_THEN_PRAGMA) == []


def test_comment_only_and_empty_pragma_only_are_legitimate(al_parser):
    assert reps(al_parser, PRAGMA_ONLY_COMMENT) == []
    assert reps(al_parser, PRAGMA_ONLY_EMPTY) == []


def test_var_block_with_no_var_in_any_arm_is_a_violation():
    arm = ir.Node("preproc_if", True, None, 0, 5, [])
    end = ir.Node("preproc_endif", True, None, 10, 16, [])
    vb = ir.Node("preproc_conditional_var_block", True, None, 0, 16, [arm, end])
    root = ir.Node("procedure", True, None, 0, 16, [vb])
    assert [d.kind for d in representation.check(root)] == ["var-block-without-var"]


def test_pragma_only_with_a_structural_child_is_a_violation():
    arm = ir.Node("preproc_if", True, None, 0, 5, [])
    stray = ir.Node("identifier", True, None, 6, 7, [])
    end = ir.Node("preproc_endif", True, None, 10, 16, [])
    root = ir.Node("procedure", True, None, 0, 16,
                   [ir.Node("preproc_pragma_only", True, None, 0, 16, [arm, stray, end])])
    assert [d.kind for d in representation.check(root)] == ["pragma-only-with-structure"]


def test_var_block_is_not_flagged_outside_a_registered_host_slot():
    """The contract is host-scoped (spec section 3): a var-block-shaped node
    sitting under a host that is not one of the routine-tail slots is not this
    contract's business (some other check, or none) -- never a false positive
    here."""
    arm = ir.Node("preproc_if", True, None, 0, 5, [])
    end = ir.Node("preproc_endif", True, None, 10, 16, [])
    vb = ir.Node("preproc_conditional_var_block", True, None, 0, 16, [arm, end])
    root = ir.Node("some_other_host", True, None, 0, 16, [vb])
    assert representation.check(root) == []


def test_malformed_group_is_reported_and_the_walk_continues():
    """split_arms raising for one node must not crash the whole check (task 11
    decision): report it as its own kind and keep checking siblings."""
    stray = ir.Node("identifier", True, None, 0, 1, [])
    bad_vb = ir.Node("preproc_conditional_var_block", True, None, 0, 1, [stray])
    good_arm = ir.Node("preproc_if", True, None, 2, 5, [])
    good_end = ir.Node("preproc_endif", True, None, 15, 20, [])
    another_vb = ir.Node("preproc_conditional_var_block", True, None, 2, 20, [good_arm, good_end])
    root = ir.Node("procedure", True, None, 0, 20, [bad_vb, another_vb])
    assert [d.kind for d in representation.check(root)] == ["malformed-group", "var-block-without-var"]
