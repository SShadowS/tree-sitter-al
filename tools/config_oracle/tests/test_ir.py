from tools.config_oracle import ir, reference
from tools.config_oracle.tests.conftest import leaf, node


def test_keyword_node_has_its_anonymous_child_as_the_leaf(al_parser):
    src = b"codeunit 1 T { }"
    root, extras, problems = ir.from_tree(al_parser.parse(src))
    assert problems == [] and extras == []
    decl = root.children[0]
    kw = decl.children[0]
    assert (kw.kind, kw.named, [c.kind for c in kw.children]) == ("codeunit_keyword", True, ["codeunit"])
    assert kw.children[0].named is False
    assert src[kw.leaves()[0].start:kw.leaves()[0].end] == b"codeunit"


def test_fields_are_recorded_on_children(al_parser):
    root, _, _ = ir.from_tree(al_parser.parse(b"codeunit 1 T { }"))
    decl = root.children[0]
    assert [(c.kind, c.field) for c in decl.children][:3] == [
        ("codeunit_keyword", None), ("integer", "object_id"), ("identifier", "object_name")]


def test_extras_are_separated(al_parser):
    src = b"// hi\ncodeunit 1 T { }"
    root, extras, _ = ir.from_tree(al_parser.parse(src))
    assert [(e.kind, src[e.start:e.end]) for e in extras] == [("comment", b"// hi")]
    assert all(l.kind != "comment" for l in root.leaves())


def test_reference_flags_errors_and_resolver_leaks(al_parser):
    assert reference.extract(al_parser, b"codeunit 1 T { ").problems
    leak = reference.extract(al_parser, b"#if A\ncodeunit 1 T { }\n#endif\n").problems
    assert any(p.startswith("resolver-leak:preproc_") for p in leak)
    assert reference.extract(al_parser, b"#pragma warning disable X\ncodeunit 1 T { }\n").problems == []


def test_error_node_that_is_also_an_extra_is_still_recorded(al_parser):
    # An unterminated block comment lexes as an ERROR that is itself `is_extra`
    # (the scanner's error recovery and its extras handling overlap here).
    unterminated_comment = b"codeunit 1 T { } /* unterminated"
    problems = reference.extract(al_parser, unterminated_comment).problems
    assert any(p.startswith("error@") for p in problems)

    # Garbage tokens inside a code_block lex as nested ERROR-as-extra nodes
    # around further, non-extra ERROR nodes -- both must be recorded, and the
    # subtree must still be walked so the inner one is not lost.
    garbage_in_body = (
        b"codeunit 1 T { trigger OnRun()\n"
        b"begin\n"
        b"@@@!!!garbage!!!@@@\n"
        b"Message('x');\n"
        b"end;\n"
        b"}\n"
    )
    problems = reference.extract(al_parser, garbage_in_body).problems
    assert any(p.startswith("error@") for p in problems)


def test_missing_object_name_is_caught_by_the_has_error_backstop(al_parser):
    # The MISSING token here is folded into the aliased `identifier` node
    # (child_count 0, is_missing False on that node itself), so nothing in the
    # ordinary error/missing walk sees it directly -- only the has_error
    # backstop catches it.
    problems = reference.extract(al_parser, b"codeunit 1 { }").problems
    assert any(p.startswith("has-error@") or p.startswith("missing@") for p in problems)


def test_clean_sources_have_no_problems(al_parser):
    assert reference.extract(al_parser, b"codeunit 1 T { }").problems == []
    clean_with_comment_in_body = (
        b"codeunit 1 T { trigger OnRun()\n"
        b"begin\n"
        b"// a comment\n"
        b"end;\n"
        b"}\n"
    )
    assert reference.extract(al_parser, clean_with_comment_in_body).problems == []


def test_from_tree_is_depth_safe_on_a_long_expression_chain(al_parser):
    # A real BC.History file can chain thousands of binary operators, which
    # parses into a tree thousands of levels deep -- deep enough to blow
    # Python's default recursion limit if `from_tree` recursed. 3,000 terms is
    # comfortably past the ~1000-frame default limit.
    terms = " + ".join(["1"] * 3000)
    src = ("codeunit 1 T { trigger OnRun()\nbegin\n"
           f"  X := {terms};\n"
           "end;\n}\n").encode()
    root, extras, problems = ir.from_tree(al_parser.parse(src))
    assert problems == []
    assert root is not None


def test_recompute_span_uses_leaves_not_cached_child_spans():
    inner = node("wrapper", leaf("a", 5, 10), leaf("b", 12, 20))
    # Simulate stale cached spans on the child that are wider than its real leaves.
    inner.start, inner.end = 0, 100
    outer = node("outer", inner)
    assert (outer.start, outer.end) == (0, 100)  # built from the stale child span

    ir.recompute_span(outer)
    assert (outer.start, outer.end) == (5, 20)  # recomputed from the actual leaves
