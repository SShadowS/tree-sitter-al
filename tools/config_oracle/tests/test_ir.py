from tools.config_oracle import ir, reference


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
