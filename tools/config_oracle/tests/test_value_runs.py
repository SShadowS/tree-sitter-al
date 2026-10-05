"""B11 sequences and decorations (spec §5.3, contract whole-value-run)."""
import pytest

from tools.config_oracle.tests import witness

SEQ = "preproc_conditional_property_value_sequence"


def _page_field(body: str) -> bytes:
    return ("page 50100 P { layout { area(Content) { field(F; X) {\n" + body + "\n} } } }\n").encode()


RUN_INSIDE = _page_field("Caption =\n#if X\n 'a';\n#endif\n#if not X\n 'b';\n#endif")
EMPTY_PREFIX = _page_field("Caption =\n#if X\n#endif\n 'a';")
NESTED_EMPTY = _page_field("Caption =\n#if X\n#if Y\n#endif\n#endif\n 'a';")
TRAILING = _page_field("Caption =\n#if X\n 'a';\n#endif\n#if not X\n 'b';\n#endif\n;")
BOUNDARY = _page_field("Visible =\n#if X\n true;\n#endif\n#if X\n Caption = 'x';\n#else\n false;\n#endif")
# Fixture case b1 (controller ruling): a `;`-inside group, then an empty group and a `;`
# that are body content. With X undefined the configured text is `Caption = ;`: the
# property's boundary lies beyond the site.
B1 = _page_field("Caption =\n#if X\n 'a';\n#endif\n#if Y\n#endif\n;")
# A `;`-after site: the property owns its `;`, so selecting no value is just `Caption = ;`.
SEMI_AFTER = _page_field("Caption =\n#if X\n 'a'\n#endif\n;")
# Suffix decorations at an arm site, before the arm's `;` and before #else.
ARM_SUFFIX = _page_field("Caption =\n#if X\n 'a'\n#if Y\n#endif\n ;\n#else\n 'b';\n#endif")


def test_run_inside_every_config_passes(al_parser):
    witness.assert_produces(al_parser, RUN_INSIDE, SEQ)
    witness.assert_all_pass(al_parser, RUN_INSIDE)


@pytest.mark.parametrize("src", [EMPTY_PREFIX, NESTED_EMPTY, ARM_SUFFIX])
def test_decorations_lower_to_nothing(al_parser, src):
    witness.assert_all_pass(al_parser, src)


def test_directly_following_semicolon_is_the_propertys(al_parser):
    witness.assert_all_pass(al_parser, TRAILING)


def test_boundary_is_one_reading(al_parser):
    v = witness.verdicts(al_parser, BOUNDARY)
    statuses = {c: s for c, (s, _) in v.items()}
    assert statuses["X=0"] == "pass", v
    assert statuses["X=1"] == "cannot-validate", v
    assert v["X=1"][1][0].startswith("lowering:one-reading"), v


def test_second_value_is_refused_not_passed(al_parser, monkeypatch):
    # Mutation: without the one-reading refusal, X=1 lowers two values into one property.
    # That must surface as a discrepancy, never a pass -- the refusal is what keeps it honest.
    from tools.config_oracle.lowering import assemblers, engine

    def lenient(node, ctx):
        values, frags = [], []
        for c in node.children:
            r = engine.lower(c, ctx.child(node.kind, c.field or "<children>"))
            values.extend(n.copy(field=node.field) for n in r.nodes)
            frags.extend(r.frags)
        return engine.Lowered(values, frags)
    monkeypatch.setattr(assemblers, "value_run_select", lenient)
    v = witness.verdicts(al_parser, BOUNDARY)
    assert v["X=1"][0] == "discrepancy", v


def test_semicolon_inside_site_without_terminator_is_one_reading(al_parser):
    v = witness.verdicts(al_parser, B1)
    for cid in ("X=0,Y=0", "X=0,Y=1"):
        status, items = v[cid]
        assert status == "cannot-validate", v
        assert items[0].startswith("lowering:one-reading:one-reading at preproc_conditional_property_value@"), v
        assert items[0].endswith(": host property:value"), v
    assert v["X=1,Y=0"][0] == v["X=1,Y=1"][0] == "pass", v


def test_semicolon_after_site_with_no_value_passes(al_parser):
    witness.assert_all_pass(al_parser, SEMI_AFTER)
