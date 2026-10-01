"""The Python walker: policy loading, the directive group index, walk (F0, spec 5.1 layer 1, 6.1).

Every expected value here is written by hand from the fixture text, never read back
from the walker: these are what make the generated .visits.json files trustworthy.
"""
import json
import time

import pytest


def test_load_policy_rejects_an_unknown_schema(T, tmp_path):
    p = tmp_path / "policy.json"
    p.write_text(json.dumps({"schema": 2, "types": {}}))
    with pytest.raises(T.PolicyError):
        T.load_policy(p)


def test_load_policy_rejects_an_unknown_class(T, tmp_path):
    p = tmp_path / "policy.json"
    p.write_text(json.dumps({"schema": 1, "types": {"x": {"class": "special"}}}))
    with pytest.raises(T.PolicyError):
        T.load_policy(p)


def test_an_unlisted_type_is_ordinary(policy):
    assert policy.cls("identifier") == "ordinary"
    assert policy.cls("preproc_conditional") == "branch-container"


def test_fnv1a64_reference_vectors(T):
    assert T.fnv1a64(b"") == "cbf29ce484222325"
    assert T.fnv1a64(b"a") == "af63dc4c8601ec8c"


def test_groups_and_arms_come_from_the_trees_own_directives(parse):
    doc = parse("containers.al")
    # Line 1 holds multi-byte text, so every offset below is a UTF-8 byte offset.
    assert doc.source[93:96] == b"#if"
    assert [(g.if_offset, [a.raw_range for a in g.arms]) for g in doc.groups] == [
        (93, [(105, 140), (145, 594)]),               # #if CLEAN25 / #else, around both objects
        (179, [(191, 251), (265, 302), (307, 345)]),  # #if CLEAN24 / #elif / #else, members
        (441, [(453, 524), (538, 554), (559, 576)]),  # the same, statements
        (489, [(501, 517)]),                          # #if CLEAN26, nested in arm 0 of 441
    ]
    assert doc.groups[1].arms[1].directive_offsets == (251, 302)
    assert [d.role for d in doc.groups[1].directives] == ["if", "elif", "else", "endif"]
    assert doc.unpaired == ()


def test_walk_skips_directives_and_trivia_unless_asked(T, policy, parse):
    doc = parse("assemblers.al")
    default = {v.type for v in T.walk(doc, policy)}
    assert not default & {"preproc_if", "preproc_else", "preproc_endif", "preproc_open", "pragma"}
    everything = {v.type for v in T.walk(doc, policy, include_directives=True, include_trivia=True)}
    assert {"preproc_if", "preproc_else", "preproc_endif", "preproc_open", "pragma"} <= everything


def test_arm_paths_are_outermost_first(T, policy, parse):
    doc = parse("containers.al")
    arms = {doc.source[v.start:v.end].decode(): v.arms for v in T.walk(doc, policy)
            if v.type == "assignment_statement"}
    assert arms == {"X := 1": ((93, 1), (441, 0)), "X := 3": ((93, 1), (441, 0), (489, 0)),
                    "X := 4": ((93, 1), (441, 1)), "X := 2": ((93, 1), (441, 2))}


def test_a_branch_container_reports_its_host_policy(T, policy, parse):
    doc = parse("containers.al")
    hosts = [(v.type, v.host) for v in T.walk(doc, policy) if v.cls == "branch-container"]
    assert hosts == [("preproc_conditional_object", "splice-repeat"), ("preproc_conditional", "splice-repeat"),
                     ("preproc_conditional_statement", "splice-repeat"),
                     ("preproc_conditional_statement", "splice-repeat")]
    assert all(v.host is None for v in T.walk(doc, policy) if v.cls != "branch-container")


def test_a_node_straddling_an_arm_boundary_is_in_no_arm(T, policy, parse):
    """cross_node.al: procedure Q starts inside the #else arm and ends after #endif."""
    doc = parse("cross_node.al")
    q = next(v for v in T.walk(doc, policy) if v.type == "procedure"
             and doc.source[v.start:v.end].startswith(b"local procedure Q"))
    assert q.arms == ()
    body = next(v for v in T.walk(doc, policy, root=q.node) if v.type == "exit_statement")
    assert body.arms == ((69, 1),)


def test_walk_from_a_subtree_keeps_document_arm_paths(T, policy, parse):
    doc = parse("containers.al")
    stmts = next(v for v in T.walk(doc, policy) if v.type == "procedure"
                 and doc.source[v.start:v.end].startswith(b"procedure Stmts"))
    sub = T.walk(doc, policy, root=stmts.node)
    assert sub[0].node == stmts.node and sub[0].arms == ((93, 1),)
    assert [v.arms for v in sub if v.type == "assignment_statement"][1] == ((93, 1), (441, 0), (489, 0))


def test_an_unclosed_group_runs_to_end_of_file(parse):
    doc = parse("unbalanced.al")
    assert doc.tree.root_node.has_error
    (group,) = doc.groups
    assert group.arms[0].raw_range[1] == len(doc.source)
    assert group.arms[0].directive_offsets == (group.if_offset,)


def test_a_stray_endif_is_unpaired_and_opens_no_group(parse):
    doc = parse("stray_endif.al")
    assert doc.groups == ()
    assert [(d.role, d.start) for d in doc.unpaired] == [("endif", 75)]


def test_crlf_and_a_leading_bom_keep_byte_offsets(parse):
    doc = parse("crlf_bom.al")
    assert doc.source.startswith(b"\xef\xbb\xbf") and b"\r\n" in doc.source
    (group,) = doc.groups
    assert group.if_offset == doc.source.index(b"#if")
    assert doc.source[group.arms[0].raw_range[0] - 2:group.arms[0].raw_range[0]] == b"\r\n"
    assert [a.raw_range for a in group.arms] == [(46, 86), (91, 133)]


def test_walk_is_iterative_and_fast_on_large_and_deep_input(T, policy, al_parser):
    groups = "".join(f"#if C{i}\n    procedure P{i}()\n    begin\n        X := {i};\n    end;\n#else\n"
                     f"    procedure Q{i}()\n    begin\n    end;\n#endif\n" for i in range(2000))
    src = f"codeunit 50100 Big\n{{\n{groups}}}\n".encode()
    doc = T.Document(al_parser.parse(src), src, policy)
    start = time.perf_counter()
    visits = T.walk(doc, policy)
    assert time.perf_counter() - start < 3, "walk is quadratic in the number of groups again (measured: 0.16 s linear, 4.4 s quadratic)"
    assert len(doc.groups) == 2000 and sum(v.type == "procedure" for v in visits) == 4000
    deep = ("codeunit 1 D\n{\n procedure P()\n begin\n  X := " + "(" * 5000 + "1" + ")" * 5000
            + ";\n end;\n}\n").encode()
    doc = T.Document(al_parser.parse(deep), deep, policy)
    assert len(T.walk(doc, policy)) > 5000          # no RecursionError
