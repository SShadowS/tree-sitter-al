"""B5 4.3: every queries/*.scm over a D1, a D2 and a D3 relation site; pins the captures."""
from pathlib import Path

import tree_sitter

from tools import relation_census as rc

SRC = (b'table 50101 Customer { fields { field(1; "No."; Code[20]) { } } }\n'
       b"table 50100 T\n{\n    fields {\n"
       b"        field(1; A; Code[20]) { TableRelation = Customer; }\n"                         # D1
       b'        field(2; B; Decimal) { AutoFormatExpression = Rec."Currency Code"; }\n'        # D2
       b'        field(3; C; Code[20]) { TableRelation = Customer."No." where("No." = const(\'A\')); }\n'  # D3
       b"    }\n}\n")


def _captures():
    parser = rc.parser_for(None)
    tree = parser.parse(SRC)
    out = set()
    for scm in sorted(Path("queries").glob("*.scm")):
        q = tree_sitter.Query(parser.language, scm.read_text(encoding="utf-8"))
        for name, nodes in tree_sitter.QueryCursor(q).captures(tree.root_node).items():
            out |= {(scm.name, name, n.start_byte, n.end_byte) for n in nodes}
    return out


def _span(text: bytes, after: bytes):
    i = SRC.index(after) + len(after)
    j = SRC.index(text, i)
    return j, j + len(text)


def _on(caps, span):
    return sorted((f, n) for f, n, s, e in caps if (s, e) == span)


def test_relation_segments_are_never_keyword_captures():
    caps = _captures()
    for text, after in [(b"Customer", b"TableRelation = "), (b'"No."', b"Customer.")]:
        assert not any("keyword" in n or n.startswith("type") for _, n in _on(caps, _span(text, after)))


PINNED = {
    # Checked against queries/highlights.scm and locals.scm: relation segments get only the generic
    # locals.scm reference captures (patterns at :128/:131); `Rec` of D2 is a plain member_expression
    # object, so highlights.scm :759 captures it as @variable. No keyword or type capture anywhere.
    (b"Customer", b"TableRelation = "): [("locals.scm", "local.reference")],
    (b"Rec", b"AutoFormatExpression = "): [("highlights.scm", "variable"), ("locals.scm", "local.reference")],
    (b'"Currency Code"', b"Rec."): [("locals.scm", "local.reference")],
    (b"Customer", b"C; Code[20]) { TableRelation = "): [("locals.scm", "local.reference")],
    (b'"No."', b"Customer."): [("locals.scm", "local.reference")],
}


def test_pinned_captures():
    caps = _captures()
    for (text, after), want in PINNED.items():
        assert _on(caps, _span(text, after)) == want
