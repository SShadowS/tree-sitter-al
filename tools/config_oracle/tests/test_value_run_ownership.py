"""B11: which node owns each `;` of a value run (spec §3.2, §4.2). Corpus trees omit the
anonymous `;`, so ownership is pinned here by walking the tree."""
import pytest

GROUP = "preproc_conditional_property_value"
PAGE = "page 50100 P { layout { area(Content) { field(F; X) {\n%s\n} } } }\n"
REPORT = "report 50100 R { dataset { dataitem(D; Cust) {\n%s\n} } }\n"

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
    "spec 4.2: terminated group then a property-less `;` is an empty_statement": (
        PAGE % "Caption =\n#if X\n 'a';\n#endif\n#if Y\n#endif\n;",
        [(3, GROUP), (7, "empty_statement")]),
}


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
