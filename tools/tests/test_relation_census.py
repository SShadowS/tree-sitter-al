import os
from pathlib import Path

import pytest

from tools import relation_census as rc

BASE = os.environ.get("B5_BASE_LIB")
needs_base = pytest.mark.skipif(not BASE, reason="set B5_BASE_LIB to the pre-change library")


def _base():
    return rc.parser_for(Path(BASE))


def _value(src: bytes, parser):
    tree = parser.parse(src)
    props = [n for n in rc.walk(tree.root_node) if n.type == "property"]
    return props[0].child_by_field_name("value"), src


def _field(prop):
    return b"table 50100 T\n{\n    fields { field(1; F; Code[20])\n    {\n        " + prop + b"\n    }\n    }\n}\n"


@needs_base
@pytest.mark.parametrize("prop,want", [
    (b'TableRelation = Customer."No.";', [b"Customer", b'"No."']),
    (b'TableRelation = "Acc. Sched. Name".Name;', [b'"Acc. Sched. Name"', b"Name"]),
    (b"TableRelation = System.Environment.Company.Name;", [b"System", b"Environment", b"Company", b"Name"]),
])
def test_old_target_normalisation(prop, want):
    v, _ = _value(_field(prop), _base())
    tr = next(n for n in rc.walk(v) if n.type == "simple_table_relation")
    assert [t for _, _, t in rc.normalise_old_target(tr)] == want


@needs_base
def test_old_target_rejects_expression_base():
    v, _ = _value(_field(b"TableRelation = MakeCustomer().\"No.\";"), _base())
    tr = next(n for n in rc.walk(v) if n.type == "simple_table_relation")
    with pytest.raises(rc.Unclassifiable):
        rc.normalise_old_target(tr)


@needs_base
def test_check_flags_todays_contract_breaks(tmp_path):
    (tmp_path / "a.al").write_bytes(_field(b"TableRelation = Customer;"))
    (tmp_path / "b.al").write_bytes(_field(b'AutoFormatExpression = Rec."Currency Code";'))
    kinds = {f.kind for f in rc.check([tmp_path], _base())}
    assert "relation-shape" in kinds      # bare TableRelation is a leaf today
    assert "relation-outside" in kinds    # D2 is a relation today


@needs_base
def test_target_check_auto_off_before_b5_and_forceable():
    src = _field(b'TableRelation = Customer."No.";')
    tree = _base().parse(src)
    assert not [f for f in rc.check_tree("x", tree, src) if f.kind == "target"]
    assert [f for f in rc.check_tree("x", tree, src, target_check=True) if f.kind == "target"]


@needs_base
def test_classify_has_no_predicate_on_old_trees():
    # D3 needs a `target:` qualified_name in the new tree; today's trees have none (positive D3/D1/D2
    # cases are Task 6's mutation tests, on the post-B5 library).
    a, _ = _value(_field(b'TableRelation = Customer."No.";'), _base())
    with pytest.raises(rc.Unclassifiable):
        rc.classify("TableRelation", a, a)


@needs_base
def test_delta_today_is_empty_and_counts_relations(tmp_path):
    (tmp_path / "a.al").write_bytes(_field(b'TableRelation = Customer."No.";\n        TableRelation = A.B;'))
    r = rc.delta([tmp_path], _base(), _base())
    assert not r.findings and not r.rows and r.d3_old_relations == 2


def test_manifest_rows_and_unmapped_d2(tmp_path):
    src = _field(b'AutoFormatExpression = Rec."Currency Code";')
    rows = []
    fs = rc.check_tree("p", rc.parser_for(None).parse(src), src, rows=rows)
    assert rows and rows[0][4] == "autoformatexpression"
    assert rc.CONTEXT_HOSTS or any(f.kind == "d2-unmapped" for f in fs)


@needs_base
def test_utf16_bom_file_is_decoded_before_parsing(tmp_path):
    (tmp_path / "u.al").write_bytes(b"\xff\xfe" + _field(b"TableRelation = Customer;").decode().encode("utf-16-le"))
    rows = []
    fs = rc.check([tmp_path], _base(), rows=rows)
    assert not [f for f in fs if f.kind == "has-error"]
    assert [r[4] for r in rows] == ["tablerelation"]


def test_root_without_al_files_cannot_run(tmp_path):
    (tmp_path / "x.txt").write_text("hi")
    with pytest.raises(FileNotFoundError):
        rc.check([tmp_path], rc.parser_for(None))
    assert rc.main(["check", "--root", str(tmp_path)]) == 2


@needs_base
def test_delta_flags_new_has_error(tmp_path):
    (tmp_path / "a.al").write_bytes(_field(b"TableRelation = A.B;"))
    base = _base()

    class Broken:
        def parse(self, src):
            return base.parse(b"table table table {{ ;;; )")

    kinds = {f.kind for f in rc.delta([tmp_path], base, Broken()).findings}
    assert "has-error-new" in kinds


@needs_base
def test_sexp_sees_spans_and_stray_fields():
    p = _base()
    a, _ = _value(_field(b"TableRelation = A.B where(X = const(1));"), p)
    b, _ = _value(_field(b"TableRelation = A.B where(X  =  const(1));"), p)
    assert rc._sexp(a, ("table",)) != rc._sexp(b, ("table",))       # a re-spanned node outside the target
    assert rc._sexp(a, ("table",)) != rc._sexp(a, ("target",))      # a stray `table:` beside `target:` stays visible


def test_chains_are_the_decompiled_ones():
    assert rc._CTRL_CHAIN == ("PageField", "PageGroup", "PagePart", "PageArea")
    assert rc._ACT_CHAIN == ("PageAction", "PageActionRef", "PageActionGroup", "PageActionArea")


# --- §5.5 mutation proofs: each edits a tree or source in memory and asserts the finding kind ---

class _P:
    """Read-only proxy over a tree-sitter Node; `over` maps (type, text) -> {attr: value} overrides."""

    def __init__(self, n, over):
        self._n, self._o = n, over

    def _wrap(self, x):
        if isinstance(x, list):
            return [self._wrap(i) for i in x]
        if callable(x):
            return lambda *a, **k: self._wrap(x(*a, **k))
        return _P(x, self._o) if hasattr(x, "children") else x

    def __getattr__(self, a):
        ov = self._o.get((self._n.type, self._n.text), {})
        if a in ov:
            return ov[a]
        return self._wrap(getattr(self._n, a))


class _T:
    def __init__(self, tree, over):
        self.language, self.root_node = tree.language, _P(tree.root_node, over)


class _Fake:  # a bare node for an override value
    def __init__(self, type_):
        self.type, self.text, self.children, self.named_children = type_, b"", [], []
        self.start_byte = self.end_byte = 0
        self.is_named, self.child_count = True, 0
        self.parent = None


def _check_fake(prop, over):
    src = _field(prop)
    tree = rc.parser_for(None).parse(src)
    return rc.check_tree("x", _T(tree, over), src, target_check=True)


def test_mutation_dropped_property(tmp_path):
    (tmp_path / "a.al").write_bytes(_field(b"TableRelation = A.B;"))
    real = rc.parser_for(None)

    class Dropped:
        def parse(self, src):
            return real.parse(src.replace(b"TableRelation = A.B;", b" " * 20))

    assert "site-dropped" in {f.kind for f in rc.delta([tmp_path], real, Dropped()).findings}


@needs_base
def test_mutation_reordered_segments(tmp_path):
    (tmp_path / "a.al").write_bytes(_field(b"TableRelation = Aa.Bb;"))
    cur = rc.parser_for(None)

    class Swapped:
        def parse(self, src):
            return cur.parse(src.replace(b"Aa.Bb", b"Bb.Aa"))

    fs = rc.delta([tmp_path], _base(), Swapped()).findings
    assert {f.kind for f in fs} == {"unclassified"}


def test_mutation_non_leaf_segment():
    fs = _check_fake(b"TableRelation = Aa.Bb;", {("identifier", b"Bb"): {"child_count": 1}})
    assert any(f.kind == "target" and "children=1" in f.detail for f in fs)


def test_mutation_conditional_moved_to_root():
    kinds = {f.kind for f in _check_fake(
        b"TableRelation = Aa;",
        {("table_relation_value", b"Aa"): {"named_children": [_Fake("preproc_conditional_table_relation")]}})}
    assert "relation-shape" in kinds


def test_conditional_head_with_else_tail_is_legal():
    src = _field(b"TableRelation =\n#if X\n if (Y = const(1)) A\n#endif\n else B;")
    fs = rc.check_tree("x", rc.parser_for(None).parse(src), src)
    assert not [f for f in fs if f.kind in ("relation-shape", "relation-outside", "target")], fs


# --- B5b: link keying (spec 2026-10-05 §4.1, §4.2, §5.5) --------------------------------

B5B_BASE = os.environ.get("B5B_BASE_LIB")
needs_b5b_base = pytest.mark.skipif(not B5B_BASE, reason="set B5B_BASE_LIB to the pre-B5b library")


def _b5b():
    return rc.parser_for(Path(B5B_BASE))


def _page_action(prop: bytes) -> bytes:
    return (b"page 50100 P\n{\n    actions { area(Processing) { action(A)\n    {\n        "
            + prop + b"\n    }\n    }\n    }\n}\n")


def test_link_names_are_the_six():
    assert rc.LINK_NAMES == {"subpagelink", "runpagelink", "linkfields",
                             "dataitemtablefilter", "columnfilter", "dataitemlink"}


@needs_b5b_base
def test_link_outside_flags_todays_leak(tmp_path):
    p = rc.parser_for(Path(B5B_BASE))
    (tmp_path / "a.al").write_bytes(_page_action(b"Visible = Flag = Rec.OtherFlag;"))
    kinds = {f.kind for f in rc.check([tmp_path], p)}
    assert "link-outside" in kinds


@needs_b5b_base
def test_link_shape_clean_on_a_real_link(tmp_path):
    p = rc.parser_for(Path(B5B_BASE))
    (tmp_path / "a.al").write_bytes(_page_action(b'RunPageLink = "No." = field("No.");'))
    kinds = {f.kind for f in rc.check([tmp_path], p)}
    assert "link-shape" not in kinds and "link-outside" not in kinds


def test_expect_no_rows_exits_1_on_a_row(tmp_path, monkeypatch):
    # a fake delta that returns one classified row and no findings; parser_for is faked too,
    # because main loads --base-lib before it calls delta
    monkeypatch.setattr(rc, "delta", lambda *a, **k: rc.DeltaResult([], [("x", 0, 1, "h", "n", "L1", "a", "b")], 0))
    monkeypatch.setattr(rc, "parser_for", lambda lib: None)
    (tmp_path / "a.al").write_bytes(b"codeunit 1 C { }")
    assert rc.main(["delta", "--root", str(tmp_path), "--base-lib", "x", "--expect-no-rows"]) == 1
    assert rc.main(["delta", "--root", str(tmp_path), "--base-lib", "x"]) == 0  # the flag is what changes it


@needs_b5b_base
def test_link_outside_reports_the_outermost_node_once(tmp_path):
    (tmp_path / "a.al").write_bytes(_page_action(b"Visible = A = field(B), C = const(1);"))
    fs = [f for f in rc.check([tmp_path], _b5b()) if f.kind == "link-outside"]
    assert [f.detail for f in fs] == ["link_value_list"]


def test_mutation_link_value_not_a_list():
    src = _page_action(b'RunPageLink = "No." = field("No.");')
    tree = rc.parser_for(None).parse(src)
    prop = next(n for n in rc.walk(tree.root_node) if n.type == "property")
    over = {("property", prop.text): {"child_by_field_name":
            lambda f: _Fake("property_expression") if f == "value" else prop.child_by_field_name(f)}}
    kinds = {f.kind for f in rc.check_tree("x", _T(tree, over), src)}
    assert "link-shape" in kinds


# Leaf rewrites. Pre-Task-3 there is no post-B5b library, so each NEW side is the base library's
# parse of a same-length substitute source (every span is kept), with _P overrides where a node
# type must differ. `field` -> `Xield` turns a link pair into a comparison; `1.5` -> `155` turns
# a comparison into a link pair.

L1_OLD = b"Visible =\n#if A\n F = field(G);\n#else\n F = filter(G);\n#endif"
L3_OLD = b"RunPageLink =\n#if A\n X = const(1.5);\n#else\n Y = const(2.5);\n#endif"
L3_NEW = L3_OLD.replace(b"1.5", b"155").replace(b"2.5", b"255")
_AS_DECIMAL = {("integer", b"155"): {"type": "decimal"}, ("integer", b"255"): {"type": "decimal"}}


def _pv(prop, over=None):
    v, _ = _value(_page_action(prop), _b5b())
    return _P(v, over) if over else v


def _recs(name, old, new):
    return rc.rewrite_records(name, old, new, approved_const_forms=rc.APPROVED_CONST_FORMS)


@needs_b5b_base
def test_l1_inside_a_whole_value_arm_envelope_unchanged():
    assert _recs("Visible", _pv(L1_OLD), _pv(L1_OLD.replace(b"field(G)", b"Xield(G)"))) == [((1,), "L1")]


@needs_b5b_base
def test_two_l3_rewrites_in_one_envelope():
    assert _recs("RunPageLink", _pv(L3_OLD), _pv(L3_NEW, _AS_DECIMAL)) == [((1,), "L3"), ((4,), "L3")]


@needs_b5b_base
def test_l3_const_argument_outside_the_approved_forms():
    with pytest.raises(rc.Unclassifiable, match="const argument"):
        _recs("RunPageLink", _pv(L3_OLD), _pv(L3_NEW))  # integer is no approved form


@needs_b5b_base
def test_l3_under_a_non_family_name_is_unclassifiable():
    with pytest.raises(rc.Unclassifiable):
        _recs("Visible", _pv(L3_OLD), _pv(L3_NEW, _AS_DECIMAL))


@needs_b5b_base
def test_envelope_whose_else_moved():
    new = _pv(L1_OLD.replace(b"field(G)", b"Xield(G)"), {("preproc_else", b"#else"): {"start_byte": 0}})
    with pytest.raises(rc.Unclassifiable, match="envelope"):
        _recs("Visible", _pv(L1_OLD), new)


@needs_b5b_base
def test_l1_whose_right_span_differs():
    new = _pv(L1_OLD.replace(b"field(G)", b"Xield(G)"), {("call_expression", b"Xield(G)"): {"end_byte": 999}})
    with pytest.raises(rc.Unclassifiable, match="right"):
        _recs("Visible", _pv(L1_OLD), new)


@needs_b5b_base
def test_delta_emits_one_row_per_rewrite(tmp_path):
    (tmp_path / "a.al").write_bytes(_page_action(L1_OLD.replace(b"filter(G)", b"field(H)")))
    base = _b5b()

    class Alt:
        def parse(self, src):
            return base.parse(src.replace(b"field(", b"Xield("))

    r = rc.delta([tmp_path], base, Alt())
    assert not r.findings
    assert [(row[5], row[8]) for row in r.rows] == [("L1", "1"), ("L1", "4")]


# L3 const-argument STRUCTURE, not just type (review fix round 1). The new side is the base
# library's link pair for `const(155)`; its integer is proxied into a node with the given type
# and the children of a real old-side argument of the same span.

def _l3_pair(arg: bytes, keep=None, type_="unary_expression"):
    old = _pv(b"RunPageLink = X = const(" + arg + b");")
    u = next(n for n in rc.walk(old) if n.type == "argument_list").named_children[0]
    idx = range(u.child_count) if keep is None else keep
    kids, names = [u.children[i] for i in idx], [u.field_name_for_child(i) for i in idx]
    new = _pv(b"RunPageLink = X = const(155);", {("integer", b"155"): {
        "type": type_, "children": kids, "child_count": len(kids), "field_name_for_child": names.__getitem__}})
    return old, new


def _l3_unary(arg, keep=None, type_="unary_expression"):
    return _recs("RunPageLink", *_l3_pair(arg, keep, type_))


@needs_b5b_base
def test_l3_signed_number_is_approved():
    assert _l3_unary(b"-15") == [((), "L3")]


@needs_b5b_base
@pytest.mark.parametrize("arg", [b"-Ab", b"+15"])  # an identifier operand; unary plus (alc rejects it, Task 1)
def test_l3_unary_argument_that_is_not_a_signed_number(arg):
    with pytest.raises(rc.Unclassifiable, match="const argument"):
        _l3_unary(arg)


@needs_b5b_base
@pytest.mark.parametrize("keep", [[0], []])  # the operator without an operand; a bare node (the reviewer's probe)
def test_l3_unary_without_operand_is_no_approved_form(keep):
    _, new = _l3_pair(b"-15", keep)
    v = next(n for n in rc.walk(new) if n.type == "unary_expression")
    assert not rc._const_form_ok(v, rc.APPROVED_CONST_FORMS)
    with pytest.raises(rc.Unclassifiable):  # through rewrite_records too (its token check fires first)
        _l3_unary(b"-15", keep)


@needs_b5b_base
def test_l3_decimal_must_be_a_leaf():
    with pytest.raises(rc.Unclassifiable, match="const argument"):
        _l3_unary(b"-15", None, type_="decimal")
