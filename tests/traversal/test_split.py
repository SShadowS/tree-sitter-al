"""SplitInfo, ArmDescriptor and bind_arm -> ArmFragments (spec 5.1 layers 1 and 3, 6.1)."""
import pytest


def text(doc, node):
    return doc.source[node.start_byte:node.end_byte].decode()


def shape(arm):
    return [(f.field, f.type) for f in arm.fragments]


def visit(T, policy, doc, type_):
    (v,) = [x for x in T.walk(doc, policy) if x.type == type_]
    return v


def test_split_procedure_arms_carry_the_header_and_the_body_is_shared(T, policy, parse):
    doc = parse("assemblers.al")
    v = visit(T, policy, doc, "preproc_split_procedure")
    header = [(None, "procedure_keyword"), ("name", "identifier"), (None, "("),
              ("parameters", "parameter_list"), (None, ")")]
    (group,) = v.split.groups
    assert group.group_id == (doc.revision, 260)
    assert [shape(a) for a in group.arms] == [header, header]
    assert [(f.field, f.type) for f in v.split.shared] == [("body", "code_block"), (None, ";")]
    assert [text(doc, a.fragments[3].node) for a in group.arms] == ["A: Integer", "A: Integer; B: Integer"]


def test_one_node_can_hold_two_groups_in_source_order(T, policy, parse):
    doc = parse("assemblers.al")
    v = visit(T, policy, doc, "preproc_split_if_then_begin")
    assert [g.group_id[1] for g in v.split.groups] == [539, 650]
    assert [g.if_offset for g in T.groups_of(v.node, doc)] == [539, 650]
    assert [shape(g.arms[0]) for g in v.split.groups] == [
        [(None, "if_keyword"), ("condition", "comparison_expression"), (None, "then_keyword"),
         (None, "begin_keyword"), (None, "call_expression"), (None, ";")],
        [(None, "end_keyword"), (None, ";")]]
    assert [(f.field, f.type) for f in v.split.shared] == [(None, "call_expression"), (None, ";")]


def test_a_cross_node_arm_binds_pieces_beyond_the_node(T, policy, parse):
    """cross_node.al: the #else arm closes P and opens Q; its #endif is inside Q."""
    doc = parse("cross_node.al")
    opener = visit(T, policy, doc, "preproc_split_block_end_in_else")
    closer = visit(T, policy, doc, "preproc_split_block_close_after_endif")
    assert [g.group_id for g in opener.split.groups] == [g.group_id for g in closer.split.groups]
    else_arm = opener.split.groups[0].arms[1]
    assert [text(doc, f.node) for f in else_arm.fragments][:6] == [
        "Message(Q('c'))", ";", "end", ";", "local", "procedure"]
    assert [(f.field, f.type) for f in closer.split.shared] == [(None, "end_keyword")]


def test_anonymous_tokens_stay_tokens_and_directives_are_never_fragments(T, policy, parse):
    doc = parse("assemblers.al")
    v = visit(T, policy, doc, "preproc_conditional_permissions")
    arms = v.split.groups[0].arms
    assert [(f.type, f.node.is_named) for f in arms[1].fragments] == [
        ("tabledata_permission", True), (",", False), ("tabledata_permission", True), (";", False)]
    every = [f for g in v.split.groups for a in g.arms for f in a.fragments]
    assert not [f for f in every if policy.cls(f.type) == "directive"]


def test_trivia_inside_an_arm_is_one_of_its_fragments(T, policy, parse):
    doc = parse("split_declaration.al")
    v = visit(T, policy, doc, "preproc_split_declaration")
    assert [f.type for f in v.split.groups[0].arms[0].fragments] == [
        "pragma", "codeunit_keyword", "integer", "quoted_identifier", "implements_clause", "pragma"]


def test_bind_arm_rejects_a_descriptor_from_another_document(T, policy, parse):
    a = parse("containers.al")
    b = parse("elif_chain.al")
    with pytest.raises(T.WrongDocument):
        T.bind_arm(a.descriptors()[0], b, policy)


def test_only_containers_assemblers_and_fragments_carry_a_split(T, policy, parse):
    doc = parse("unbalanced.al")            # its #if sits under an ERROR node
    error = [v for v in T.walk(doc, policy) if v.type == "ERROR"]
    assert error and all(v.cls == "ordinary" and v.split is None for v in error)
    assert T.groups_of(error[0].node, doc)  # the ERROR node does hold the group
    doc = parse("assemblers.al")
    assert {v.cls for v in T.walk(doc, policy) if v.split} == {"branch-container", "assembler"}


def test_walk_visits_an_assemblers_arm_pieces_too(T, policy, parse):
    """I2: walk descends into every assembler, so each arm piece of a split procedure is
    ALSO an ordinary visit, with its arm path. A consumer that reads both SplitInfo and
    walk must dedupe by node id (or take statements from one source only)."""
    doc = parse("assemblers.al")
    v = visit(T, policy, doc, "preproc_split_procedure")
    visits = {x.node.id: x for x in T.walk(doc, policy)}
    for g in v.split.groups:
        for a in g.arms:
            named = [f.node for f in a.fragments if f.node.is_named]
            assert named and all(n.id in visits for n in named)
            assert all(visits[n.id].arms[-1] == (g.group_id[1], a.descriptor.arm_id) for n in named)
    assert all(f.node.id in visits for f in v.split.shared if f.node.is_named)


def test_arm_pieces_never_keeps_a_directive_from_an_expanded_fragment(T, policy, parse):
    """M1. In today's grammar no fragment that holds its own directives can be an arm
    piece, so an overriding policy makes the nested statement conditional of
    containers.al (#if CLEAN26 at 489, inside arm 0 of 441) a fragment: expanding it
    must give its statements, never its #if/#endif nodes."""
    doc = parse("containers.al")
    over = T.Policy({**policy.types, "preproc_conditional_statement": {"class": "fragment"}})
    (outer,) = [g for g in doc.groups if g.if_offset == 441]
    arm = T.bind_arm(outer.arms[0], doc, over)
    assert any(f.node.start_byte == 489 for f in arm.fragments)       # the nested group is one piece
    pieces = T.arm_pieces(arm, doc, over)
    assert not [f.type for f in pieces if f.node.is_named and over.cls(f.type) == "directive"]
    assert [doc.source[f.node.start_byte:f.node.end_byte] for f in pieces if f.type == "assignment_statement"] ==         [b"X := 1", b"X := 3"]
