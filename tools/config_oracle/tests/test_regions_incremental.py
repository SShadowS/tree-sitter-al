"""B7b-2 Phase A (plan Task 4 Step 5, Review Focus 4): an incremental re-parse after an edit equals a fresh parse
for tails. Edits: turn an argument tail into a comma-led argument group and back (insert / delete `,` right after
`#if X` in `Foo(1 #if X + 2 #endif)`), add and remove a second consecutive group, move a group into an arm, and turn
`+` into `as`. The comparison is the full cursor tree (every node, named and anonymous, with its field, type,
MISSING flag and byte span), the helpers of test_strict_lists_incremental.py."""
import pytest

from tools.config_oracle.tests.test_strict_lists_incremental import _dump, _edit, _types

HOST = b"codeunit 50100 P\n{\n    procedure Q()\n    begin\n        %s\n    end;\n}\n"

ARGUMENT_SHAPES = {
    "tail": b"I := Foo(1\n#if X\n+ 2\n#endif\n);",
    "comma": b"I := Foo(1\n#if X\n, + 2\n#endif\n);",
    "tail-then-comma": b"I := Foo(1\n#if X\n+ 2\n#endif\n#if Y\n, 3\n#endif\n);",
    "two-tails": b"I := Foo(1\n#if X\n+ 2\n#endif\n#if Y\n+ 3\n#endif\n, 2);",
}

GROUP_SHAPES = {
    "one": b"I := 1\n#if X\n+ 2\n#endif\n;",
    "consecutive": b"I := 1\n#if X\n+ 2\n#endif\n#if Y\n+ 3\n#endif\n;",
    "nested": b"I := 1\n#if X\n+ 2\n#if Y\n+ 3\n#endif\n#endif\n;",
    "plus": b"F := F\n#if X\n+ IFoo\n#endif\n;",
    "as": b"F := F\n#if X\nas IFoo\n#endif\n;",
    "as-consecutive": b"F := F\n#if X\nas IFoo\n#endif\n#if Y\nas IBar\n#endif\n;",
}

ARGUMENT_EDITS = [
    ("tail", "comma"),                      # `,` inserted right after `#if X`: the tail becomes an argument group
    ("comma", "tail"),                      # and deleted again
    ("tail", "tail-then-comma"),            # a comma-led group is added after the tail
    ("tail-then-comma", "two-tails"),       # it becomes a consecutive tail
    ("two-tails", "tail"),                  # and is removed
]

GROUP_EDITS = [
    ("one", "consecutive"),                 # a second consecutive group is added
    ("consecutive", "one"),                 # and removed
    ("consecutive", "nested"),              # the second group moves into the first arm
    ("nested", "consecutive"),              # and out again
    ("plus", "as"),                         # `+` turns into `as`
    ("as", "plus"),                         # and back
    ("as", "as-consecutive"),               # a second `as` group is added
]


def _check(parser, old_src, new_src):
    incremental = _edit(parser, old_src, new_src)
    fresh = parser.parse(new_src)
    assert _dump(incremental.root_node) == _dump(fresh.root_node)
    assert incremental.root_node.has_error == fresh.root_node.has_error


@pytest.mark.parametrize("shapes", [ARGUMENT_SHAPES, GROUP_SHAPES], ids=["arguments", "groups"])
def test_every_shape_parses_clean(al_parser, shapes):
    """The edits compare trees of clean parses, not of error recovery."""
    for name, stmt in shapes.items():
        root = al_parser.parse(HOST % stmt).root_node
        assert not root.has_error, name
        assert "preproc_conditional_expression_tail" in _types(root) or name == "comma", name


@pytest.mark.parametrize("before,after", ARGUMENT_EDITS)
def test_incremental_tail_argument_edits(al_parser, before, after):
    _check(al_parser, HOST % ARGUMENT_SHAPES[before], HOST % ARGUMENT_SHAPES[after])


@pytest.mark.parametrize("before,after", GROUP_EDITS)
def test_incremental_tail_group_edits(al_parser, before, after):
    _check(al_parser, HOST % GROUP_SHAPES[before], HOST % GROUP_SHAPES[after])


# B7b-2 Phase C (plan Task 10 Step 6): operand groups. Insert / delete the operator after `#endif` (the group
# becomes the left of `+`, or stands alone), add / remove `#else`, and the receiver / leading-prefix neighbours.
OPERAND_SHAPES = {
    "alone": b"I := 1 +\n#if X\n2\n#else\n3\n#endif\n;",
    "then-op": b"I := 1 +\n#if X\n2\n#else\n3\n#endif\n+ 4;",
    "no-else": b"I := 1 +\n#if X\n2\n#endif\n;",
    "arg-alone": b"Foo(\n#if X\n1\n#else\n2\n#endif\n);",
    "arg-then-op": b"Foo(\n#if X\n1\n#else\n2\n#endif\n+ 3);",
    "receiver": b"I :=\n#if X\nT1\n#else\nT2\n#endif\n.IndexOf('a');",
    "leading-prefix": b"I :=\n#if X\nT1 +\n#endif\nT2;",
}

OPERAND_EDITS = [
    ("alone", "then-op"),                   # `+ 4` inserted after `#endif`
    ("then-op", "alone"),                   # and deleted
    ("alone", "no-else"),                   # `#else` removed
    ("no-else", "alone"),                   # and added back
    ("arg-alone", "arg-then-op"),           # an argument group becomes an operand group (row P' -> 6a)
    ("arg-then-op", "arg-alone"),           # and back
    ("receiver", "leading-prefix"),         # a receiver group becomes a leading prefix
    ("leading-prefix", "receiver"),         # and back
]


def test_every_operand_shape_parses_clean(al_parser):
    for name, stmt in OPERAND_SHAPES.items():
        root = al_parser.parse(HOST % stmt).root_node
        assert not root.has_error, name
        want = "preproc_operand_prefix" if name == "leading-prefix" else (
            "preproc_conditional_arguments" if name == "arg-alone" else "preproc_conditional_operand")
        assert want in _types(root), name


@pytest.mark.parametrize("before,after", OPERAND_EDITS)
def test_incremental_operand_group_edits(al_parser, before, after):
    _check(al_parser, HOST % OPERAND_SHAPES[before], HOST % OPERAND_SHAPES[after])
