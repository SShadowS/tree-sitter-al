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
