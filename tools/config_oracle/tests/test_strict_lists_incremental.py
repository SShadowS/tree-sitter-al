"""B7b-1 (spec 2026-10-07 section 7): an incremental re-parse after an edit equals a fresh parse, for every strict
conditional list family. Edits: move a separator into and out of an arm, delete an `#else` arm, add and remove a
group, and (attributed var names) edit the names after an unchanged `[NonDebuggable]` prefix. The comparison is the
full cursor tree: every node, named and anonymous, with its field, type, MISSING flag and byte span."""
import pytest

# family -> (host template with one %s for the list interior, three atoms, the node a group in this list becomes)
FAMILIES = {
    "implements": (b"codeunit 50100 C implements %s\n{\n}\n", (b"IFoo", b"IBar", b"IBaz"), "preproc_conditional_implements"),
    "key_field_list": (b"table 50100 T\n{\n    fields\n    {\n        field(1; K; Code[20]) { }\n    }\n"
                       b"    keys\n    {\n        key(PK; %s) { }\n    }\n}\n", (b"K", b"N", b"B"), "preproc_conditional_field_list_items"),
    "fieldgroup_field_list": (b"table 50100 T\n{\n    fieldgroups\n    {\n        fieldgroup(DropDown; %s) { }\n"
                              b"    }\n}\n", (b"K", b"N", b"B"), "preproc_conditional_field_list_items"),
    "addlast_field_list": (b"tableextension 50110 TE extends T\n{\n    fieldgroups\n    {\n"
                           b"        addlast(DropDown; %s) { }\n    }\n}\n", (b"K", b"N", b"B"), "preproc_conditional_field_list_items"),
    "sorting": (b"page 50100 P\n{\n    SourceTableView = sorting(%s);\n}\n", (b"K", b"N", b"B"), "preproc_conditional_sorting_fields"),
    "order_by": (b"query 50105 Qy\n{\n    OrderBy = ascending(%s);\n}\n", (b"K", b"N", b"B"), "preproc_conditional_order_by_fields"),
    "move": (b"pageextension 50113 PE extends PG\n{\n    actions\n    {\n        moveafter(A1; %s)\n    }\n}\n",
             (b"A2", b"A3", b"A4"), "preproc_conditional_move_elements"),
    "array_dimensions": (b"codeunit 50100 C\n{\n    var\n        A: array[%s] of Integer;\n}\n", (b"2", b"3", b"4"), "preproc_conditional_array_dimensions"),
    "attribute_args": (b"codeunit 50100 C\n{\n    [IntegrationEvent(%s)]\n    procedure P()\n    begin\n    end;\n}\n",
                       (b"false", b"true", b"false"), "preproc_conditional_attribute_args"),
    "var_names": (b"codeunit 50100 C\n{\n    var\n        %s: Integer;\n}\n", (b"A", b"B", b"C"), "preproc_conditional_var_names"),
    "var_names_attributed": (b"codeunit 50100 C\n{\n    var\n        [NonDebuggable]\n        %s: Integer;\n"
                             b"        D: Text;\n}\n", (b"A", b"B", b"C"), "preproc_conditional_var_names"),
}


def interiors(a, b, c):
    """-> {name: list interior}; every one is a list shape the strict list parses clean."""
    return {
        "sep-in-arm": a + b"\n#if X\n, " + b + b"\n#endif\n",
        "sep-out-of-arm": a + b" ,\n#if X\n" + b + b"\n#endif\n, " + c,
        "sep-in-arm-tail": a + b"\n#if X\n, " + b + b"\n#endif\n, " + c,
        "else": a + b"\n#if X\n, " + b + b"\n#else\n, " + c + b"\n#endif\n",
        "plain": a + b", " + b,
        "grouped": a + b"\n#if X\n, " + c + b"\n#endif\n, " + b,
        "two-groups": a + b"\n#if X\n, " + b + b"\n#endif\n#if Y\n, " + c + b"\n#endif\n",
        "nested": a + b"\n#if X\n, " + b + b"\n#if Y\n, " + c + b"\n#endif\n#endif\n",
    }


EDITS = [
    ("sep-out-of-arm", "sep-in-arm-tail"),  # separator moves into the arm
    ("sep-in-arm-tail", "sep-out-of-arm"),  # separator moves out of the arm
    ("else", "sep-in-arm"),                 # the #else arm is deleted
    ("sep-in-arm", "else"),                 # an #else arm is added
    ("plain", "grouped"),                   # a group is added
    ("grouped", "plain"),                   # the group is removed
    ("sep-in-arm", "two-groups"),           # a second, independent group is added
    ("two-groups", "nested"),               # the second group moves inside the first
    ("nested", "sep-in-arm"),               # the inner group is removed
]


def _point(src, off):
    return (src.count(b"\n", 0, off), off - (src.rfind(b"\n", 0, off) + 1))


def _edit(parser, old_src, new_src):
    tree = parser.parse(old_src)
    n = min(len(old_src), len(new_src))
    start = next((i for i in range(n) if old_src[i] != new_src[i]), n)
    tail = 0
    while tail < n - start and old_src[-1 - tail] == new_src[-1 - tail]:
        tail += 1
    old_end, new_end = len(old_src) - tail, len(new_src) - tail
    tree.edit(start_byte=start, old_end_byte=old_end, new_end_byte=new_end, start_point=_point(old_src, start),
              old_end_point=_point(old_src, old_end), new_end_point=_point(new_src, new_end))
    return parser.parse(new_src, tree)


def _dump(node, field=None, out=None):
    out = [] if out is None else out
    out.append((field, node.type, node.is_named, node.is_missing, node.start_byte, node.end_byte))
    cursor = node.walk()
    if cursor.goto_first_child():
        while True:
            _dump(cursor.node, cursor.field_name, out)
            if not cursor.goto_next_sibling():
                break
    return out


def _types(node):
    return {t for _, t, *_ in _dump(node)}


@pytest.mark.parametrize("family", sorted(FAMILIES))
@pytest.mark.parametrize("shape", sorted(interiors(b"a", b"b", b"c")))
def test_every_shape_parses_clean_into_the_family_group(al_parser, family, shape):
    """The edits below compare trees of real strict-list parses, not of error recovery."""
    host, atoms, group = FAMILIES[family]
    src = host % interiors(*atoms)[shape]
    root = al_parser.parse(src).root_node
    assert not root.has_error, src.decode()
    if shape != "plain":
        assert group in _types(root), src.decode()


@pytest.mark.parametrize("family", sorted(FAMILIES))
@pytest.mark.parametrize("before,after", EDITS)
def test_incremental_equals_fresh(al_parser, family, before, after):
    host, atoms, group = FAMILIES[family]
    shapes = interiors(*atoms)
    old_src, new_src = host % shapes[before], host % shapes[after]
    incremental = _edit(al_parser, old_src, new_src)
    fresh = al_parser.parse(new_src)
    assert _dump(incremental.root_node) == _dump(fresh.root_node)
    assert incremental.root_node.has_error == fresh.root_node.has_error


ATTRIBUTED_TAIL_EDITS = [
    # the edit lies after the unchanged `[NonDebuggable]` prefix: the scanner's lookahead read past it before
    (b"A\n#if X\n, B\n#endif\n", b"A\n#if X\n, B\n#endif\n#if Y\n, C\n#endif\n"),
    (b"A\n#if X\n, B\n#endif\n", b"A, Z\n#if X\n, B\n#endif\n"),
    (b"A\n#if X\n, B\n#else\n, C\n#endif\n", b"A\n#if X\n, B\n#elif Y\n, C\n#endif\n"),
    (b"A\n#if X\n, B\n#endif\n", b"A\n#if X\n, B\n#endifx\n"),   # accepted stream -> declined
    (b"A\n#if X\n, B\n#endifx\n", b"A\n#if X\n, B\n#endif\n"),   # and back
]


@pytest.mark.parametrize("before,after", ATTRIBUTED_TAIL_EDITS)
def test_incremental_after_unchanged_attribute(al_parser, before, after):
    host = FAMILIES["var_names_attributed"][0]
    incremental = _edit(al_parser, host % before, host % after)
    fresh = al_parser.parse(host % after)
    assert _dump(incremental.root_node) == _dump(fresh.root_node)
    assert incremental.root_node.has_error == fresh.root_node.has_error


EMPTY_RUN_EDITS = [
    # the GLR fork shape (Task 11, groupDynamic -1): an empty group before a declaration may stand alone as a
    # sibling preproc_conditional_var at var_body top level, or open the declaration's name list
    (b"", b"#if X\n#endif\n"),                                   # an empty group is added before the declaration
    (b"#if X\n#endif\n", b""),                                   # and removed
    (b"#if X\n#endif\n", b"#if X\n#endif\n#if Y\n#endif\n"),     # the empty run grows
    (b"#if X\n#endif\n#if Y\n#endif\n", b"#if X\n#endif\n"),     # and shrinks
    (b"#if X\n#endif\n", b"#if X\nZ,\n#endif\n"),                # the empty group gains a name: it now opens the list
    (b"#if X\nZ,\n#endif\n", b"#if X\n#endif\n"),                # and loses it
    (b"#if X\n#endif\n", b"#if X\n#else\n#endif\n"),             # an empty #else arm is added
]


@pytest.mark.parametrize("before,after", EMPTY_RUN_EDITS)
@pytest.mark.parametrize("names", [b"A", b"A, B"])
def test_incremental_empty_group_run_before_declaration(al_parser, before, after, names):
    host = b"codeunit 50100 C\n{\n    var\n%s        %s: Integer;\n        D: Text;\n}\n"
    old_src, new_src = host % (before, names), host % (after, names)
    fresh = al_parser.parse(new_src)
    assert not fresh.root_node.has_error, new_src.decode()
    incremental = _edit(al_parser, old_src, new_src)
    assert _dump(incremental.root_node) == _dump(fresh.root_node)


@pytest.mark.parametrize("before,after", EMPTY_RUN_EDITS)
def test_incremental_empty_group_run_after_attribute(al_parser, before, after):
    # the same fork after a variable attribute: at var_body top level the empty group stays a sibling
    host = b"codeunit 50100 C\n{\n    var\n        [NonDebuggable]\n%s        A: Integer;\n        D: Text;\n}\n"
    old_src, new_src = host % before, host % after
    fresh = al_parser.parse(new_src)
    assert not fresh.root_node.has_error, new_src.decode()
    incremental = _edit(al_parser, old_src, new_src)
    assert _dump(incremental.root_node) == _dump(fresh.root_node)
