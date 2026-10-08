"""B7b-3 Task 8 (spec 5.1-5.2): #if groups in the move header (routes 2-3, preproc_conditional_move_args).

1. An incremental re-parse after an edit equals a fresh parse (full cursor tree: every node, named and
   anonymous, field, type, MISSING flag, byte span): the fixed `;` moves between the host and an arm, a
   header group is inserted and removed, and route 1 turns into route 2 and back.
2. Fields per instance, which node-types.json cannot show (spec 5.2): route 2 fields only its first raw
   name (`target`), route 3 fields nothing, route 1 keeps target/element."""
import pytest

from tools.config_oracle.tests.test_strict_lists_incremental import _dump, _edit

HOST = b"pageextension 50113 PE extends PG\n{\n    actions\n    {\n        moveafter(%s)\n    }\n}\n"

SHAPES = {
    "flat": b"A1; A2",
    "semi-in-host": b"A1 ;\n#if X\nA2\n#endif\n",               # route 1: `;` in the host
    "semi-in-arm": b"A1\n#if X\n; A2\n#endif\n",                # route 2: `;` in the arm
    "route2-empty": b"A1\n#if X\n;\n#endif\nA2",                # route 2: `;`-only group
    "header-group": b"\n#if X\nA1\n#else\nA3\n#endif\n; A2",    # route 3: group replaces the target
    "spanning": b"\n#if X\nA1; A2\n#else\nA3; A4\n#endif\n, A5",  # route 3 with a comma tail
}

EDITS = [
    ("semi-in-host", "semi-in-arm"),    # the fixed `;` moves from the host into an arm
    ("semi-in-arm", "semi-in-host"),    # and back
    ("flat", "header-group"),           # a header group is inserted
    ("header-group", "flat"),           # and removed
    ("flat", "route2-empty"),           # route 1 turns into route 2
    ("route2-empty", "flat"),           # and back
    ("flat", "spanning"),               # route 1 turns into route 3 with a tail
    ("spanning", "flat"),               # and back
]


@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_every_shape_parses_clean(al_parser, shape):
    root = al_parser.parse(HOST % SHAPES[shape]).root_node
    assert not root.has_error, SHAPES[shape].decode()


@pytest.mark.parametrize("before,after", EDITS)
def test_incremental_move_args_edits(al_parser, before, after):
    old_src, new_src = HOST % SHAPES[before], HOST % SHAPES[after]
    incremental = _edit(al_parser, old_src, new_src)
    fresh = al_parser.parse(new_src)
    assert _dump(incremental.root_node) == _dump(fresh.root_node)
    assert incremental.root_node.has_error == fresh.root_node.has_error


def _move(al_parser, shape):
    root = al_parser.parse(HOST % SHAPES[shape]).root_node
    stack = [root]
    while stack:
        n = stack.pop()
        if n.type == "moveafter_modification":
            return n
        stack.extend(n.children)
    raise AssertionError("no moveafter_modification")


def _kids(node):
    return [(c.type, node.field_name_for_child(i)) for i, c in enumerate(node.children)]


def test_route1_keeps_its_fields(al_parser):
    m = _move(al_parser, "semi-in-host")
    assert _kids(m)[1:] == [("(", None), ("identifier", "target"), (";", None),
                            ("preproc_conditional_move_elements", None), (")", None)]


def test_route2_fields_only_its_first_name(al_parser):
    m = _move(al_parser, "route2-empty")
    assert _kids(m)[1:] == [("(", None), ("identifier", "target"),
                            ("preproc_conditional_move_args", None), ("identifier", None), (")", None)]
    group = m.children[3]
    assert [c.type for c in group.children] == ["preproc_if", ";", "preproc_endif"]


def test_route3_fields_nothing(al_parser):
    m = _move(al_parser, "spanning")
    assert _kids(m)[1:] == [("(", None), ("preproc_conditional_move_args", None), (",", None),
                            ("identifier", None), (")", None)]
    group = m.children[2]
    assert all(group.field_name_for_child(i) in (None, "condition") for i in range(group.child_count))
