"""Deferred-work 31/32/34: incremental re-parse after an edit equals a fresh parse."""
import pytest

from tools.config_oracle.tests.test_link_incremental import _edit

TR = b'table 50106 T2 { fields { field(1; K; Code[20]) { TableRelation = Cust."No." where(%s); } } }\n'
PAGE = b'page 50100 P { layout { area(Content) { %s } } }\n'

EDITS = [
    (TR, b"Amount = const(1)", b"Amount = const(-1)"),
    (TR, b"Amount = const(-1)", b"Amount = const(1)"),
    (TR, b"Amount = const(1)", b"Amount = const(1.5)"),
    (TR, b"Amount = filter(1|2&3)", b"Amount = filter((1|2)&3)"),
    (TR, b"Amount = filter((1|2)&3)", b"Amount = filter(1|2&3)"),
    (TR, b"Amount = filter((1|2)&3)", b"Amount = filter(((1|2)&3)|4)"),
    (TR, b"Amount = filter((1|2)&3)", b"Amount = filter((1|2&3)"),
    (PAGE, b'part(C; "Sales Chart") { }', b'chartpart(C; "Sales Chart") { }'),
    (PAGE, b'chartpart(C; "Sales Chart") { }', b'part(C; "Sales Chart") { }'),
    (PAGE, b'chartpart(C; "Sales Chart") { }', b'chartpartx(C; "Sales Chart") { }'),
]


@pytest.mark.parametrize("host,before,after", EDITS)
def test_incremental_equals_fresh(al_parser, host, before, after):
    old_src, new_src = host % before, host % after
    incremental = _edit(al_parser, old_src, new_src)
    fresh = al_parser.parse(new_src)
    assert str(incremental.root_node) == str(fresh.root_node)
    assert incremental.root_node.has_error == fresh.root_node.has_error


def test_chartpart_keyword_has_one_anonymous_child(al_parser):
    # The uniform keyword contract (CLAUDE.md): exactly one anonymous child typed as the
    # canonical lowercase spelling, whatever the source spelling.
    for spelling in (b"chartpart", b"ChartPart", b"CHARTPART"):
        root = al_parser.parse(PAGE % (spelling + b'(C; "Sales Chart") { }')).root_node
        assert not root.has_error
        stack = [root]
        kw = None
        while stack:
            n = stack.pop()
            if n.type == "chartpart_keyword":
                kw = n
            stack.extend(n.children)
        assert kw is not None and kw.text == spelling
        assert [(c.type, c.is_named) for c in kw.children] == [("chartpart", False)]
