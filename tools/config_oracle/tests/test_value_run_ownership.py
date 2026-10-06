"""B11: which node owns each `;` of a value run (spec §3.2, §4.2). Corpus trees omit the
anonymous `;`, so ownership is pinned here by walking the tree."""
import pytest

GROUP = "preproc_conditional_property_value"
PAGE = "page 50100 P { layout { area(Content) { field(F; X) {\n%s\n} } } }\n"
REPORT = "report 50100 R { dataset { dataitem(D; Cust) {\n%s\n} } }\n"
TABLE = "table 50100 T { fields { field(1; F; Code[20]) {\n%s\n} } }\n"
XMLPORT = "xmlport 50100 XP {\n%s\nschema { } }\n"

# (source, [(line, owner type of the `;`)]) for every `;` after the host's first line.
CASES = {
    "step-2 trailing `;` directly after the run is the property's": (
        PAGE % "Caption =\n#if X\n 'a';\n#endif\n#if not X\n 'b';\n#endif\n;",
        [(3, GROUP), (6, GROUP), (8, "property")]),
    "arm `;` belongs to its group, no trailing `;`": (
        PAGE % "Caption =\n#if X\n 'a';\n#endif\n#if not X\n 'b';\n#endif",
        [(3, GROUP), (6, GROUP)]),
    "two-group DataItemLink empty-value arm: `;` inside the first group": (
        REPORT % "DataItemLink =\n#if X\n#if Y\n#endif\n ;\n#endif\n#if Z\n A = field(B);\n#endif",
        [(5, GROUP), (8, GROUP)]),
    "ruling 1: the property ends at the terminated group, the trailing `;` is an empty_statement": (
        PAGE % ("CaptionML =\n#if X\n ENU='a'\n#endif\n#if not X\n ENU='b';\n#else\n ENU='c';\n#endif\n"
                "#if Z\n#endif\n;"),
        [(6, GROUP), (8, GROUP), (12, "empty_statement")]),
    "b1: a NON-terminated `;`-inside group (no #else), then an empty group: the site ends at "
    "the group (spec 3.2), the trailing `;` is an empty_statement": (
        PAGE % "Caption =\n#if X\n 'a';\n#endif\n#if Y\n#endif\n;",
        [(3, GROUP), (7, "empty_statement")]),
    # Amendment 4 (spec 3.4): a `;`-after single group, a suffix decoration, then `;`: the
    # property owns the `;` (the base left it unterminated, the `;` an empty_statement).
    "amendment 4: TableRelation `;`-after group, suffix decoration, `;` is the property's": (
        TABLE % "TableRelation =\n#if X\n Cust.\"No.\"\n#endif\n#if Z\n#endif\n;",
        [(7, "property")]),
    "amendment 4: CalcFormula `;`-after group, suffix decoration, `;` is the property's": (
        TABLE % "CalcFormula =\n#if X\n count(Cust)\n#endif\n#if Z\n#endif\n;",
        [(7, "property")]),
    "amendment 4: Namespaces `;`-after group, suffix decoration, `;` is the property's": (
        XMLPORT % "Namespaces =\n#if X\n a = 'u'\n#endif\n#if Z\n#endif\n;",
        [(7, "property")]),
}


# Amendment 4's suffix decoration is an unfielded child of the property, not of the value.
@pytest.mark.parametrize("name", [n for n in CASES if n.startswith("amendment 4")])
def test_suffix_decoration_is_unfielded_property_child(al_parser, name):
    src, _ = CASES[name]
    stack = [al_parser.parse(src.encode()).root_node]
    while stack:
        n = stack.pop()
        if n.type == "property":
            kids = [(n.field_name_for_child(i), c.type) for i, c in enumerate(n.children)]
            assert kids[-3:] == [("value", GROUP), (None, GROUP), (None, ";")], kids
            return
        stack.extend(n.children)
    raise AssertionError("no property")


def _semicolons(parser, src):
    tree = parser.parse(src.encode())
    assert not tree.root_node.has_error
    found = []

    def go(node):
        for child in node.children:
            if child.type == ";" and child.start_point[0] > 0:
                found.append((child.start_point[0], node.type))
            go(child)
    go(tree.root_node)
    return found


@pytest.mark.parametrize("name", CASES)
def test_semicolon_owner(al_parser, name):
    src, expected = CASES[name]
    assert _semicolons(al_parser, src) == expected
