from pathlib import Path

from tools.query_coverage import corpus


def test_set_cover_picks_the_widest_file_first():
    vocab = {"a.al": {"x", "y", "z"}, "b.al": {"x"}, "c.al": {"w"}}

    picked = corpus.select(vocab)

    assert picked[0] == "a.al"
    assert set(picked) == {"a.al", "c.al"}


def test_set_cover_skips_files_that_add_nothing():
    vocab = {"a.al": {"x", "y"}, "b.al": {"x"}, "c.al": {"y"}}

    assert corpus.select(vocab) == ["a.al"]


def test_set_cover_ties_break_on_path_ascending():
    vocab = {"z.al": {"x"}, "a.al": {"x"}}

    assert corpus.select(vocab) == ["a.al"]


def test_set_cover_is_deterministic_across_input_orderings():
    forward = {"a.al": {"x", "y"}, "b.al": {"y", "z"}, "c.al": {"w"}}
    reverse = dict(reversed(list(forward.items())))

    assert corpus.select(forward) == corpus.select(reverse)


def test_object_types_come_from_the_tree_not_the_filename(al_parser):
    """BC.History suffixes are inconsistent: PermissionSet vs permissionset vs Permissionset."""
    source = b"codeunit 1 A { } table 2 B { }"

    types = corpus.object_types(al_parser.parse(source))

    assert types == ("codeunit_declaration", "table_declaration")


def test_object_types_excludes_namespace_declaration(al_parser):
    """A leading `namespace X;` is a directive, not an object -- it must not leak in."""
    source = b'namespace Foo.Bar; codeunit 1 A { }'

    types = corpus.object_types(al_parser.parse(source))

    assert types == ("codeunit_declaration",)


def test_object_types_descends_into_preproc_conditional_object(al_parser):
    """An object wrapped in a top-level #if/#endif must report its real type, not ()."""
    source = b'#if CLEAN24\ncodeunit 1 A { }\n#endif'

    types = corpus.object_types(al_parser.parse(source))

    assert types == ("codeunit_declaration",)


def test_object_types_reports_both_branches_when_types_differ(al_parser):
    """#if/#else with a different object type per branch: report both, in source order.

    There is no "active" branch without evaluating preprocessor symbols, which this
    tool never does -- it tracks grammar/query coverage over the source text, not
    compiled semantics. Reporting only one branch would silently hide whichever
    declaration shape wasn't picked; reporting both is the honest inventory of what
    the file's source actually contains.
    """
    source = b'#if A\ncodeunit 1 X { }\n#else\ntable 1 Y { }\n#endif'

    types = corpus.object_types(al_parser.parse(source))

    assert types == ("codeunit_declaration", "table_declaration")


def test_manifest_roundtrip(tmp_path: Path):
    path = tmp_path / "manifest.tsv"
    entries = [
        corpus.ManifestEntry(("table_declaration",), "BC.History/a.al", "aa" * 32, 100, "set-cover"),
        corpus.ManifestEntry(("codeunit_declaration", "table_declaration"), "BC.History/b.al", "bb" * 32, 200, "stress"),
    ]

    corpus.write_manifest(path, entries)

    assert corpus.read_manifest(path) == entries


def test_manifest_object_types_column_is_comma_separated(tmp_path: Path):
    path = tmp_path / "manifest.tsv"
    corpus.write_manifest(
        path, [corpus.ManifestEntry(("a", "b"), "x.al", "cc" * 32, 1, "set-cover")]
    )

    body = [ln for ln in path.read_text(encoding="utf-8").splitlines() if not ln.startswith("#")]

    assert body[0].split("\t")[0] == "a,b"


def test_manifest_hash_is_order_independent(tmp_path: Path):
    a = corpus.ManifestEntry(("t",), "a.al", "aa" * 32, 1, "r")
    b = corpus.ManifestEntry(("t",), "b.al", "bb" * 32, 2, "r")

    assert corpus.manifest_hash([a, b]) == corpus.manifest_hash([b, a])


def test_verify_reports_missing_file(tmp_path: Path):
    entry = corpus.ManifestEntry(("t",), "nope.al", "aa" * 32, 1, "r")

    problems = corpus.verify(tmp_path, [entry])

    assert len(problems) == 1
    assert "nope.al" in problems[0]


def test_verify_reports_drifted_hash(tmp_path: Path):
    target = tmp_path / "f.al"
    target.write_bytes(b"content")
    entry = corpus.ManifestEntry(("t",), "f.al", "00" * 32, 7, "r")

    problems = corpus.verify(tmp_path, [entry])

    assert len(problems) == 1
    assert "sha256" in problems[0]


def test_never_observed_lists_unseen_named_types():
    node_types = [
        {"type": "seen_node", "named": True},
        {"type": "unseen_node", "named": True},
        {"type": ";", "named": False},
    ]

    assert corpus.never_observed(node_types, {"seen_node"}) == ["unseen_node"]
