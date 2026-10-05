"""B5: incremental re-parse after an edit equals a fresh parse (spec 5.4)."""
import pytest

HOST = b"table 50100 T\n{\n    fields { field(1; F; Code[20])\n    {\n        %s\n    }\n    }\n}\n"

EDITS = [
    (b"TableRelation = Customer;", b"TableRelationX = Customer;"),
    (b"TableRelationX = Customer;", b"TableRelation = Customer;"),
    (b"TableRelation = Rec.A;", b"Visible = Rec.A;"),
    (b"Visible = Rec.A;", b"TableRelation = Rec.A;"),
    (b"TableRelation = Customer;", b"tablerelation = Customer;"),
    (b"TableRelation = Customer;", b'TableRelation = Customer where("No." = const(\'A\'));'),
    (b"TableRelation = Customer;", b"TableRelation = System.Customer;"),
    (b"TableRelation = Customer;", b'TableRelation = Customer."No.";'),
    (b"TableRelation = Customer;", b"TableRelation =\n#if X\n Customer\n#else\n Vendor\n#endif\n;"),
    (b"TableRelation = Customer;", b"TableRelation  = Customer;"),
]


def _edit(parser, old_src, new_src):
    tree = parser.parse(old_src)
    n = min(len(old_src), len(new_src))
    prefix = next((i for i in range(n) if old_src[i] != new_src[i]), n)
    suffix = 0
    while (suffix < n - prefix
           and old_src[len(old_src) - 1 - suffix] == new_src[len(new_src) - 1 - suffix]):
        suffix += 1
    start, old_end, new_end = prefix, len(old_src) - suffix, len(new_src) - suffix

    def point(src, off):
        line = src.count(b"\n", 0, off)
        return (line, off - (src.rfind(b"\n", 0, off) + 1))
    tree.edit(start_byte=start, old_end_byte=old_end, new_end_byte=new_end,
              start_point=point(old_src, start), old_end_point=point(old_src, old_end),
              new_end_point=point(new_src, new_end))
    return parser.parse(new_src, tree)


@pytest.mark.parametrize("before,after", EDITS)
def test_incremental_equals_fresh(al_parser, before, after):
    old_src, new_src = HOST % before, HOST % after
    incremental = _edit(al_parser, old_src, new_src)
    fresh = al_parser.parse(new_src)
    assert str(incremental.root_node) == str(fresh.root_node)
    assert incremental.root_node.has_error == fresh.root_node.has_error
