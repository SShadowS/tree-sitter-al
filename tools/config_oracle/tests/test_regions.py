"""The region assembler (B7b-2 spec 3.1-3.2, section 7): one owner per transparent region.

Every grouping witness is asserted twice per configuration: against a hand-written tree
(`_render`, written from the spec's ladder, never from parser output) and against the
oracle's own comparison with the flat parse (`witness.assert_all_pass`).
"""
from __future__ import annotations

import pytest

from tools.config_oracle import ir
from tools.config_oracle.directives import config_id, configurations, discover, resolve
from tools.config_oracle.lowering import engine, expression, lower_tree, regions
from tools.config_oracle.lowering.engine import LoweringError
from tools.config_oracle.tests import witness
from tools.config_oracle.tests.conftest import leaf, node


def _stmt(s):
    return b"codeunit 1 T\n{\n    procedure P()\n    begin\n        " + s + b"\n    end;\n}\n"


def _render(n, src):
    """A compact tree: `(op left right)`, `(op operand)`, `(? c t e)`, `(.. l r)`, `[e, ...]`,
    `(paren e)`, `obj[i, ...]`, `f(a, ...)`, an atom as its text. A missing field renders as `?`,
    so a mutation that drops a field fails the tree comparison, never the renderer."""
    r = lambda c: "?" if c is None else _render(c, src)  # noqa: E731
    f = {c.field: c for c in n.children if c.field}
    op = lambda: "?" if "operator" not in f else src[f["operator"].start:f["operator"].end].decode()  # noqa: E731
    named = [c for c in n.children if c.named]
    if n.kind == "parenthesized_expression":
        return f"(paren {r(named[0])})"
    if n.kind == "subscript_expression":
        return f"{r(f.get('object'))}[" + ", ".join(r(c) for c in named[1:]) + "]"
    if n.kind == "call_expression":
        args = [c for c in f["arguments"].children if c.named] if "arguments" in f else []
        return f"{r(f.get('function'))}(" + ", ".join(r(c) for c in args) + ")"
    if n.kind in expression.BINARY_KINDS:
        return f"({op()} {r(f.get('left'))} {r(f.get('right'))})"
    if n.kind == "unary_expression":
        return f"({op()} {r(f.get('operand'))})"
    if n.kind == "ternary_expression":
        return f"(? {r(f.get('condition'))} {r(f.get('then_value'))} {r(f.get('else_value'))})"
    if n.kind == "range_expression":
        return f"(.. {r(f.get('left'))} {r(f.get('right'))})"
    if n.kind == "list_literal":
        return "[" + ", ".join(r(c) for c in n.children if c.named) + "]"
    if n.kind == "member_expression":
        return f"{r(f.get('object'))}.{r(f.get('member'))}"
    return src[n.start:n.end].decode()


def _find(n, kind):
    stack = [n]
    while stack:
        x = stack.pop()
        if x.kind == kind:
            return x
        stack.extend(reversed(x.children))
    return None


def _lowered(parser, src, kind="assignment_statement", slot="right"):
    """{config id: rendered `slot` of the first lowered `kind` node} over every configuration;
    `slot` is a field name or an index into the node's named children (an unfielded root).
    A refused configuration renders as `refused:<kind>`, a missing slot as `?`."""
    root, extras, problems = ir.from_tree(parser.parse(src))
    assert problems == [], problems
    disc = discover(src)
    out = {}
    for env in configurations(disc):
        cid = config_id(env, disc.free_symbols)
        try:
            low, _, _ = lower_tree(root, extras, resolve(src, env))
        except LoweringError as e:
            out[cid] = f"refused:{e.kind}"
            continue
        host = _find(low, kind)
        named = [c for c in host.children if c.named]
        child = named[slot] if isinstance(slot, int) else next((c for c in named if c.field == slot), None)
        out[cid] = "?" if child is None else _render(child, src)
    return out


def _check(parser, src, want, kind="assignment_statement", slot="right"):
    assert _lowered(parser, src, kind, slot) == want
    witness.assert_all_pass(parser, src)


# --- 3.1 region edges --------------------------------------------------------------------

_TAIL, _PREFIX, _OPERAND = regions.TAIL, regions.PREFIX, regions.OPERAND_GROUP
EDGES = [
    # (parent kind, child kind, field, region edge?)
    *[(k, "identifier", f, True) for k in ("multiplicative_expression", "additive_expression",
                                            "comparison_expression", "logical_expression")
      for f in ("left", "right")],
    *[(k, "identifier", "left", True) for k in ("in_expression", "is_expression", "as_expression")],
    ("in_expression", "list_literal", "right", False),
    ("is_expression", "type_specification", "right", False),
    ("as_expression", "type_specification", "right", False),
    ("unary_expression", "identifier", "operand", True),
    ("additive_expression", "+", "operator", True),
    ("in_expression", "in_keyword", "operator", True),
    ("additive_expression", _PREFIX, None, True),
    ("in_expression", _PREFIX, None, True),
    ("assignment_statement", _TAIL, None, True),          # the tail beside a root's expression
    ("ternary_expression", _TAIL, None, True),
    (_TAIL, "identifier", "operand", True),
    (_TAIL, "+", "operator", True),
    (_TAIL, _TAIL, None, True),
    (_PREFIX, "identifier", "operand", True),
    (_PREFIX, _TAIL, None, True),
    (_OPERAND, "identifier", "operand", True),
    # boundaries
    ("assignment_statement", "additive_expression", "right", False),
    ("argument_list", "additive_expression", None, False),
    ("call_expression", "argument_list", "arguments", False),
    ("member_expression", "additive_expression", "object", False),
    ("subscript_expression", "identifier", "object", False),
    ("subscript_expression", "additive_expression", "index", False),
    ("parenthesized_expression", "additive_expression", None, False),
    ("list_literal", "additive_expression", None, False),
    ("ternary_expression", "additive_expression", "condition", False),
    ("ternary_expression", "additive_expression", "then_value", False),
    ("ternary_expression", "additive_expression", "else_value", False),
    ("range_expression", "additive_expression", "left", False),
    ("range_expression", "additive_expression", "right", False),
]


@pytest.mark.parametrize("parent,child,fld,want", EDGES, ids=lambda x: str(x))
def test_region_edges_match_spec(parent, child, fld, want):
    c = leaf(child, 0, 1, named=True, field=fld)
    assert regions.is_region_edge(node(parent, c), c, fld) is want


def _ir(parser, src):
    root, _, problems = ir.from_tree(parser.parse(src))
    assert problems == []
    return root


def test_prefix_edge_is_region_edge(al_parser):
    src = _stmt(b"x := a *\n#if X\n b +\n#endif\n c;")
    top = _find(_ir(al_parser, src), "multiplicative_expression")
    assert [m.kind for m in regions.collect(top)] == ["identifier", "*", _PREFIX, "identifier"]
    _check(al_parser, src, {"X=0": "(* a c)", "X=1": "(+ (* a b) c)"})


def test_outer_region_without_local_group(al_parser, monkeypatch):
    src = _stmt(b"x := a * b + Foo(1\n#if X\n + 2\n#endif\n);")
    top = _find(_ir(al_parser, src), "additive_expression")
    assert not any(m.kind in regions.GROUPS for m in regions.collect(top))
    roots = []
    real, real_tail = regions.assemble, regions.assemble_with_tail
    monkeypatch.setattr(regions, "assemble", lambda r, ctx: roots.append(r.kind) or real(r, ctx))
    monkeypatch.setattr(regions, "assemble_with_tail",
                        lambda e, t, ec, tc, **kw: roots.append(f"{e.kind}+tail") or real_tail(e, t, ec, tc, **kw))
    _check(al_parser, src, {"X=0": "(+ (* a b) Foo(1))", "X=1": "(+ (* a b) Foo((+ 1 2)))"})
    assert roots and set(roots) == {"integer+tail"}, roots     # only the argument's own region


# --- 4.3 grouping witnesses available after Phase A ---------------------------------------

def test_unary_absorption(al_parser):
    _check(al_parser, _stmt(b"x := not a\n#if X\n and c\n#endif\n;"),
           {"X=0": "(not a)", "X=1": "(and (not a) c)"})


def test_unary_operand_inside_an_arm(al_parser):
    _check(al_parser, _stmt(b"x := a\n#if X\n * -b + c\n#endif\n;"),
           {"X=0": "a", "X=1": "(+ (* a (- b)) c)"})


def test_tighter_left_before_tail(al_parser):
    _check(al_parser, _stmt(b"x := a * b\n#if X\n + c\n#endif\n;"),
           {"X=0": "(* a b)", "X=1": "(+ (* a b) c)"})


def test_tail_binds_into_the_root_expression(al_parser):
    # The root's expression is not an atom of its region: `*` binds tighter than its `+`.
    _check(al_parser, _stmt(b"x := a + b\n#if X\n * c\n#endif\n;"),
           {"X=0": "(+ a b)", "X=1": "(+ a (* b c))"})


def test_subtraction_stays_left_associative(al_parser):
    _check(al_parser, _stmt(b"x := a - b\n#if X\n - c\n#endif\n;"),
           {"X=0": "(- a b)", "X=1": "(- (- a b) c)"})


def test_tail_in_the_else_root(al_parser):
    _check(al_parser, _stmt(b"x := Ok ? 1 : 2\n#if X\n + 3\n#endif\n;"),
           {"X=0": "(? Ok 1 2)", "X=1": "(? Ok 1 (+ 2 3))"})


def test_tail_in_the_range_right_root(al_parser):
    _check(al_parser, _stmt(b"x := [1..5\n#if X\n + 2\n#endif\n];"),
           {"X=0": "[(.. 1 5)]", "X=1": "[(.. 1 (+ 5 2))]"})


def test_tail_in_the_condition_root(al_parser):
    _check(al_parser, _stmt(b"x := Ok or true\n#if X\n and false\n#endif\n or Ok ? 1 : 2;"),
           {"X=0": "(? (or (or Ok true) Ok) 1 2)", "X=1": "(? (or (or Ok (and true false)) Ok) 1 2)"})


def test_tail_before_in(al_parser):
    _check(al_parser, _stmt(b"b := i\n#if X\n + 1\n#endif\n in [1, 2] and Ok;"),
           {"X=0": "(and (in i [1, 2]) Ok)", "X=1": "(and (in (+ i 1) [1, 2]) Ok)"})


def test_prefix_operator_escapes_its_node(al_parser):
    # The prefix form of 4.3's `true and #if X a = c #else d #endif` (the #else form is Task 11).
    _check(al_parser, _stmt(b"x := true and\n#if X\n a =\n#endif\n c;"),
           {"X=0": "(and true c)", "X=1": "(= (and true a) c)"})


def test_nested_and_consecutive_tails(al_parser):
    _check(al_parser, _stmt(b"x := a + b\n#if X\n + c\n#if Y\n * d\n#endif\n#endif\n;"),
           {"X=0,Y=0": "(+ a b)", "X=0,Y=1": "(+ a b)", "X=1,Y=0": "(+ (+ a b) c)",
            "X=1,Y=1": "(+ (+ a b) (* c d))"})
    _check(al_parser, _stmt(b"x := 1\n#if X\n + 2\n#endif\n#if Y\n * 3\n#endif\n;"),
           {"X=0,Y=0": "1", "X=0,Y=1": "(* 1 3)", "X=1,Y=0": "(+ 1 2)", "X=1,Y=1": "(+ 1 (* 2 3))"})


def test_tail_inside_a_prefix_arm(al_parser):
    _check(al_parser, _stmt(b"x := a +\n#if X\n b\n#if Y\n * c\n#endif\n +\n#endif\n d;"),
           {"X=0,Y=0": "(+ a d)", "X=0,Y=1": "(+ a d)", "X=1,Y=0": "(+ (+ a b) d)",
            "X=1,Y=1": "(+ (+ a (* b c)) d)"})


# --- 3.2 inactive groups contribute nothing; validity after composition --------------------

def test_inactive_tail_is_valid(al_parser):
    _check(al_parser, _stmt(b"x := 1\n#if X\n + 2\n#endif\n;"), {"X=0": "1", "X=1": "(+ 1 2)"})


def test_inactive_prefix_is_valid(al_parser):
    _check(al_parser, _stmt(b"x := a +\n#if X\n b +\n#endif\n c;"),
           {"X=0": "(+ a c)", "X=1": "(+ (+ a b) c)"})


def test_operator_only_arm_inactive_is_invalid(al_parser):
    """`i := 1 2;` at X=0: two operands with no operator in the composed run. The runner sees
    the reference error first, so the lowering verdict is asserted directly."""
    src = _stmt(b"i := 1\n#if X\n +\n#endif\n 2;")
    assert witness.verdicts(al_parser, src)["X=1"][0] == "pass"
    root, extras, _ = ir.from_tree(al_parser.parse(src))
    with pytest.raises(LoweringError) as e:
        lower_tree(root, extras, resolve(src, frozenset()))
    assert e.value.kind == "contract-shape", e.value


# --- 7: double ownership -------------------------------------------------------------------

def test_double_ownership(al_parser, monkeypatch):
    src = _stmt(b"x := a *\n#if X\n b +\n#endif\n c\n#if Y\n + d\n#endif\n;")
    composed = []
    real = regions._compose
    monkeypatch.setattr(regions, "_compose", lambda run, f, at: composed.append(at.kind) or real(run, f, at))
    for env in configurations(discover(src)):
        root, extras, _ = ir.from_tree(al_parser.parse(src))
        composed.clear()
        low, _, _ = lower_tree(root, extras, resolve(src, env))
        # spec 7 step 1, literal: the region (prefix chain + the root tail beside it) is composed
        # by exactly ONE invocation per configuration, never once by the root and again by the tail.
        assert composed == ["multiplicative_expression"], (sorted(env), composed)
    monkeypatch.setattr(regions, "_compose", real)
    _check(al_parser, src, {"X=0,Y=0": "(* a c)", "X=0,Y=1": "(+ (* a c) d)",
                            "X=1,Y=0": "(+ (* a b) c)", "X=1,Y=1": "(+ (+ (* a b) c) d)"})


# --- 7 step 5: property compatibility (inputs from test_expression_lowering) ----------------

PROPERTY = (b"table 1 D\n{\n    fields\n    {\n        field(1; F; Integer)\n        {\n"
            b"            MinValue = 1\n#if X\n                + 2\n#endif\n                ;\n"
            b"        }\n    }\n}\n")
SIGNED_TAIL = PROPERTY.replace(b"MinValue = 1", b"MinValue = -1")


def test_property_compat_unwrap(al_parser):
    witness.assert_all_pass(al_parser, PROPERTY)
    v = witness.verdicts(al_parser, PROPERTY)
    assert any(i.startswith("normalised:property-expression-unwrap") for i in v["X=0"][1]), v
    assert not any("property-expression-unwrap" in i for i in v["X=1"][1]), v


def test_property_signed_literal_one_reading(al_parser):
    v = witness.verdicts(al_parser, SIGNED_TAIL)
    assert v["X=0"][0] == "pass", v
    assert v["X=1"][0] == "cannot-validate" and v["X=1"][1][0].startswith("lowering:one-reading"), v


# --- 5.3 in / is / as ------------------------------------------------------------------------

@pytest.mark.parametrize("text,want0,want1", [
    (b"i2 := i\n#if X\n as IFoo\n#endif\n;", "i", "(as i IFoo)"),
    (b"i2 := i\n#if X\n is IFoo\n#endif\n;", "i", "(is i IFoo)"),
    (b"i2 := i\n#if X\n in [1, 2]\n#endif\n;", "i", "(in i [1, 2])"),
    (b"i2 := i + 1\n#if X\n in [1, 2] and Ok\n#endif\n;", "(+ i 1)", "(and (in (+ i 1) [1, 2]) Ok)"),
    (b"i2 := Ok and i\n#if X\n in [1, 2]\n#endif\n;", "(and Ok i)", "(and Ok (in i [1, 2]))"),
], ids=["as", "is", "in", "in-between-levels", "in-above-and"])
def test_keyword_operator_tail_lowers_flat(al_parser, text, want0, want1):
    _check(al_parser, _stmt(text), {"X=0": want0, "X=1": want1})


# Spec 3.1: the right of in/is/as is one typed atom; a following operator never regroups into it.
def test_typed_right_is_an_atom_after_a_tail(al_parser):
    _check(al_parser, _stmt(b"b := i in [1] + 2\n#if X\n + 3\n#endif\n;"),
           {"X=0": "(+ (in i [1]) 2)", "X=1": "(+ (+ (in i [1]) 2) 3)"})


def test_typed_right_is_an_atom_with_prefix_and_tail(al_parser):
    _check(al_parser, _stmt(b"b := i in [1] +\n#if X\n 2 +\n#endif\n 3\n#if Y\n * 4\n#endif\n;"),
           {"X=0,Y=0": "(+ (in i [1]) 3)", "X=0,Y=1": "(+ (in i [1]) (* 3 4))",
            "X=1,Y=0": "(+ (+ (in i [1]) 2) 3)", "X=1,Y=1": "(+ (+ (in i [1]) 2) (* 3 4))"})


def test_typed_prefix(al_parser):
    _check(al_parser, _stmt(b"b := Ok in\n#if X\n [true] in\n#endif\n [false];"),
           {"X=0": "(in Ok [false])", "X=1": "(in (in Ok [true]) [false])"})


# --- 5.1: every region root (Phase B) ----------------------------------------------------
# (id, statement, CST host of the tail, lowered host kind, slot, {config: hand-written tree}).
# The CST host pins WHERE the tail attaches (the root's own host, not an enclosing one); the
# lowered tree pins the composition at every configuration. The ternary condition / else and
# the range right roots are the 4.3 witnesses above.
_X01 = lambda a, b: {"X=0": a, "X=1": b}  # noqa: E731
ROOTS = [
    ("repeat-until (item 39 shape 1)",
     b"repeat\n Foo();\n until C\n#if X\n and D\n#endif\n#if Y\n or E\n#endif\n;",
     "repeat_statement", "repeat_statement", "condition",
     {"X=0,Y=0": "C", "X=0,Y=1": "(or C E)", "X=1,Y=0": "(and C D)", "X=1,Y=1": "(or (and C D) E)"}),
    ("case expression",
     b"case i\n#if X\n + 1\n#endif\n#if Y\n * 2\n#endif\n of\n 1:\n Foo();\n end;",
     "case_statement", "case_statement", "expression",
     {"X=0,Y=0": "i", "X=0,Y=1": "(* i 2)", "X=1,Y=0": "(+ i 1)", "X=1,Y=1": "(+ i (* 1 2))"}),
    ("split case-end expression",
     b"case i\n#if X\n + 1\n#endif\n of\n 1:\n Foo();\n 2:\n#if Y\n Foo();\n end;\n Bar();\n"
     b"#else\n Bar();\n end;\n Foo();\n#endif",
     "preproc_split_case_statement_end", "case_statement", "expression",
     {"X=0,Y=0": "i", "X=0,Y=1": "i", "X=1,Y=0": "(+ i 1)", "X=1,Y=1": "(+ i 1)"}),
    ("ternary then", b"x := Ok ? 1\n#if X\n + 2\n#endif\n : 3;",
     "ternary_expression", "assignment_statement", "right", _X01("(? Ok 1 3)", "(? Ok (+ 1 2) 3)")),
    ("parenthesized inner", b"x := (1\n#if X\n + 2\n#endif\n) * 3;",
     "parenthesized_expression", "assignment_statement", "right",
     _X01("(* (paren 1) 3)", "(* (paren (+ 1 2)) 3)")),
    ("range left", b"Ok := i in [1 * 2\n#if X\n + 1\n#endif\n .. 5];",
     "range_expression", "assignment_statement", "right",
     _X01("(in i [(.. (* 1 2) 5)])", "(in i [(.. (+ (* 1 2) 1) 5)])")),
    ("for start", b"for i := 1\n#if X\n + 1\n#endif\n to 5 do\n Foo();",
     "for_statement", "for_statement", "start", _X01("1", "(+ 1 1)")),
    ("for end", b"for i := 1 to 5\n#if X\n - 1\n#endif\n do\n Foo();",
     "for_statement", "for_statement", "end", _X01("5", "(- 5 1)")),
    ("subscript first index", b"x := Arr2[1\n#if X\n + 1\n#endif\n, 2];",
     "subscript_expression", "assignment_statement", "right", _X01("Arr2[1, 2]", "Arr2[(+ 1 1), 2]")),
    ("subscript second index", b"x := Arr2[1, 2\n#if X\n - 1\n#endif\n];",
     "subscript_expression", "assignment_statement", "right", _X01("Arr2[1, 2]", "Arr2[1, (- 2 1)]")),
    ("list first element", b"Ok := i in [1\n#if X\n + 1\n#endif\n, 2];",
     "list_literal", "assignment_statement", "right", _X01("(in i [1, 2])", "(in i [(+ 1 1), 2])")),
    ("list second element", b"Ok := i in [1, 2\n#if X\n + 1\n#endif\n];",
     "list_literal", "assignment_statement", "right", _X01("(in i [1, 2])", "(in i [1, (+ 2 1)])")),
    ("with record", b"with Recs[1]\n#if X\n + 1\n#endif\n do\n Foo();",
     "with_statement", "with_statement", "record", _X01("Recs[1]", "(+ Recs[1] 1)")),
    ("foreach iterable", b"foreach i in L\n#if X\n + 1\n#endif\n do\n Foo();",
     "foreach_statement", "foreach_statement", "iterable", _X01("L", "(+ L 1)")),
    ("if condition", b"if a\n#if X\n and b\n#endif\n then\n Foo();",
     "if_statement", "if_statement", "condition", _X01("a", "(and a b)")),
    ("while condition", b"while a\n#if X\n or b\n#endif\n do\n Foo();",
     "while_statement", "while_statement", "condition", _X01("a", "(or a b)")),
    ("exit value", b"exit(1\n#if X\n + 2\n#endif\n);",
     "exit_statement", "exit_statement", "return_value", _X01("1", "(+ 1 2)")),
    ("call argument", b"Foo(1\n#if X\n + 2\n#endif\n, 3);",
     "argument_list", "argument_list", 0, _X01("1", "(+ 1 2)")),
    ("assignment right", b"x := 1\n#if X\n + 2\n#endif\n * 3;",
     "assignment_statement", "assignment_statement", "right", _X01("(* 1 3)", "(+ 1 (* 2 3))")),
]


def _tail_host(parser, src):
    """The CST type of the first (outermost) tail's parent."""
    stack = [parser.parse(src).root_node]
    while stack:
        n = stack.pop()
        if n.type == regions.TAIL:
            return n.parent.type
        stack.extend(reversed(n.children))
    raise AssertionError("no tail")


@pytest.mark.parametrize("text,cst_host,kind,slot,want", [r[1:] for r in ROOTS], ids=[r[0] for r in ROOTS])
def test_region_root_hosts(al_parser, text, cst_host, kind, slot, want):
    src = _stmt(text)
    assert _tail_host(al_parser, src) == cst_host
    _check(al_parser, src, want, kind, slot)


@pytest.mark.parametrize("text", [r[1] for r in ROOTS], ids=[r[0] for r in ROOTS])
def test_region_root_single_ownership(al_parser, monkeypatch, text):
    """Spec 7.1 at every root: no region is composed twice in one configuration, and a live
    tail is composed (never dropped)."""
    src = _stmt(text)
    composed = []
    real = regions._compose
    monkeypatch.setattr(regions, "_compose", lambda run, f, at: composed.append(at) or real(run, f, at))
    disc = discover(src)
    root, extras, _ = ir.from_tree(al_parser.parse(src))
    for env in configurations(disc):
        composed.clear()
        lower_tree(root, extras, resolve(src, env))
        keys = [(a.kind, a.start) for a in composed]
        assert len(keys) == len(set(keys)), (sorted(env), keys)
        if env == frozenset(disc.free_symbols):   # every group live
            assert keys, sorted(env)


# --- 3.1 boundaries: a group behind a boundary belongs to the inner region -----------------

def test_parenthesized_pair(al_parser):
    _check(al_parser, _stmt(b"x := (-a\n#if X\n + b\n#endif\n);"),
           {"X=0": "(paren (- a))", "X=1": "(paren (+ (- a) b))"})


def test_unary_over_a_parenthesized_root(al_parser):
    _check(al_parser, _stmt(b"x := -(a\n#if X\n + b\n#endif\n);"),
           {"X=0": "(- (paren a))", "X=1": "(- (paren (+ a b)))"})


def test_parenthesized_inner_beside_an_outer_tail(al_parser):
    # Two regions: the inner `1 + 2` and the outer `2 * (...) + 4`; neither regroups the other.
    _check(al_parser, _stmt(b"x := 2 * (1\n#if X\n + 2\n#endif\n)\n#if Y\n + 4\n#endif\n;"),
           {"X=0,Y=0": "(* 2 (paren 1))", "X=0,Y=1": "(+ (* 2 (paren 1)) 4)",
            "X=1,Y=0": "(* 2 (paren (+ 1 2)))", "X=1,Y=1": "(+ (* 2 (paren (+ 1 2))) 4)"})


def test_ternary_then_is_a_boundary(al_parser):
    # `* 3` after the then part stays in the then root; the condition's `or` never sees it.
    _check(al_parser, _stmt(b"x := a or b ? 1 + 2\n#if X\n * 3\n#endif\n : 4;"),
           {"X=0": "(? (or a b) (+ 1 2) 4)", "X=1": "(? (or a b) (+ 1 (* 2 3)) 4)"})


def test_range_ends_are_boundaries(al_parser):
    _check(al_parser, _stmt(b"Ok := i in [1\n#if X\n + 1\n#endif\n .. 5\n#if Y\n * 2\n#endif\n];"),
           {"X=0,Y=0": "(in i [(.. 1 5)])", "X=0,Y=1": "(in i [(.. 1 (* 5 2))])",
            "X=1,Y=0": "(in i [(.. (+ 1 1) 5)])", "X=1,Y=1": "(in i [(.. (+ 1 1) (* 5 2))])"})


def test_typed_right_holds_its_own_region(al_parser):
    # The tail is inside the list (its first element's root); `and Ok` stays outside the list.
    _check(al_parser, _stmt(b"b := i in [1\n#if X\n + 1\n#endif\n] and Ok;"),
           {"X=0": "(and (in i [1]) Ok)", "X=1": "(and (in i [(+ 1 1)]) Ok)"})


# --- 5.1 C1: split-if and split-call roots stay unsupported --------------------------------

SPLIT_IF = (b"#if A\n        if C\n#if X\n            and D\n#endif\n            then\n#else\n"
            b"        if E\n#if X\n            and D\n#endif\n            then\n#endif\n            Foo();")
SPLIT_CALL = (b"#if A\n        Foo(1\n#if X\n            + 2\n#endif\n            ,\n#else\n"
              b"        Foo(3,\n#endif\n            4\n#if Y\n            + 5\n#endif\n            );")
SPLIT_OPEN = (b"case K of\n 1:\n#if A\n if C then begin\n x := 1;\n end else\n#else\n"
              b" if E\n#if X\n and D\n#endif\n then\n#endif\n x := 2;\n 2:\n x := 3;\nend;")


@pytest.mark.parametrize("text,kind", [(SPLIT_IF, "preproc_split_if_statement"),
                                       (SPLIT_CALL, "preproc_split_call_statement"),
                                       (SPLIT_OPEN, "preproc_split_open_statement")],
                         ids=["split-if", "split-call", "split-open-if-head"])
def test_split_roots_stay_unsupported(al_parser, text, kind):
    src = _stmt(text)
    assert _tail_host(al_parser, src) == kind
    v = witness.verdicts(al_parser, src)
    assert v and all(s == "cannot-validate" and items[0].startswith("lowering:unsupported-type")
                     and kind in items[0] for s, items in v.values()), v


# --- Phase C (spec 6, Task 11): operand groups and leading prefixes ------------------------
# Each case is (statement, lowered kind, slot, {config: hand-written tree}); every one has a
# mutation in PHASE_C_MUTATIONS that it must kill (test_phase_c_mutations_are_killed).

PHASE_C = {
    # spec 4.3: the group is no grouping claim, the ladder regroups the spliced run
    "4.3 (2*3)+4": (b"x := 2 *\n#if X\n 3 + 4\n#else\n 5\n#endif\n;",
                    "assignment_statement", "right", _X01("(* 2 5)", "(+ (* 2 3) 4)")),
    "4.3 (-a)+b": (b"x := -\n#if X\n a + b\n#else\n c\n#endif\n;",
                   "assignment_statement", "right", _X01("(- c)", "(+ (- a) b)")),
    "4.3 (true and a) = c": (b"x := true and\n#if X\n a = c\n#else\n d\n#endif\n;",
                             "assignment_statement", "right", _X01("(and true d)", "(= (and true a) c)")),
    # spec 6.3: a leading prefix is owned by the root, with the root's tail in one composition
    "leading prefix": (b"x :=\n#if X\n 1 +\n#endif\n 2;",
                       "assignment_statement", "right", _X01("2", "(+ 1 2)")),
    "leading prefix and tail": (b"x :=\n#if X\n 1 +\n#endif\n 2\n#if Y\n * 3\n#endif\n;",
                                "assignment_statement", "right",
                                {"X=0,Y=0": "2", "X=0,Y=1": "(* 2 3)", "X=1,Y=0": "(+ 1 2)",
                                 "X=1,Y=1": "(+ 1 (* 2 3))"}),
    "whole root": (b"x :=\n#if X\n 1\n#else\n 2 * 3\n#endif\n;",
                   "assignment_statement", "right", _X01("(* 2 3)", "1")),
    # spec 3.4 receiver variant: one postfix-safe atom per arm, the slot's field kept
    "receiver member object": (b"x :=\n#if X\n a\n#else\n b\n#endif\n .Foo;",
                               "assignment_statement", "right", _X01("b.Foo", "a.Foo")),
    "receiver call function": (b"x :=\n#if X\n Foo\n#else\n Bar\n#endif\n (1);",
                               "assignment_statement", "right", _X01("Bar(1)", "Foo(1)")),
    "receiver assignment target": (b"#if X\n a\n#else\n b\n#endif\n := 1;",
                                   "assignment_statement", "left", _X01("b", "a")),
    # spec 6.2 typed variant: one typed atom, nothing after it regroups into it
    "typed as": (b"j := i as\n#if X\n IFoo\n#else\n IBar\n#endif\n;",
                 "assignment_statement", "right", _X01("(as i IBar)", "(as i IFoo)")),
    "typed in": (b"b := i in\n#if X\n [1]\n#else\n [2, 3]\n#endif\n + 1;",
                 "assignment_statement", "right", _X01("(+ (in i [2, 3]) 1)", "(+ (in i [1]) 1)")),
}


def _as_group_claim(real):
    def run(group, ctx):
        r = real(group, ctx)
        return [regions._compose(r, None, group)] if group.kind == regions.OPERAND_GROUP and r else r
    return run


def _first_arm_fallback(real):
    """An #if with no #else and no live arm falls back to its first arm (it must contribute nothing)."""
    def pick(arms, endif, node, ctx):
        got = real(arms, endif, node, ctx)
        return got or (arms[0][1] if node.kind == regions.OPERAND_GROUP else got)
    return pick


def _fieldless(real):
    return lambda run, f, at: real(run, None, at)


PHASE_C_MUTATIONS = {   # case -> (module, attribute, wrapper of the real attribute)
    "4.3 (2*3)+4": (regions, "_group_run", _as_group_claim),
    "4.3 (-a)+b": (regions, "_group_run", _as_group_claim),
    "4.3 (true and a) = c": (regions, "_group_run", _as_group_claim),
    "leading prefix": (regions, "LEADING_PREFIXES", lambda real: False),
    "leading prefix and tail": (regions, "LEADING_PREFIXES", lambda real: False),
    "whole root": (regions, "_compose", _fieldless),
    "receiver member object": (regions, "_compose", _fieldless),
    "receiver call function": (regions, "_compose", _fieldless),
    "receiver assignment target": (regions, "_compose", _fieldless),
    "typed as": (regions, "_compose", _fieldless),
    "typed in": (expression, "TYPED_RIGHT", lambda real: frozenset()),
}


@pytest.mark.parametrize("case", PHASE_C, ids=list(PHASE_C))
def test_phase_c(al_parser, case):
    text, kind, slot, want = PHASE_C[case]
    _check(al_parser, _stmt(text), want, kind, slot)


@pytest.mark.parametrize("case", PHASE_C, ids=list(PHASE_C))
def test_phase_c_mutations_are_killed(al_parser, monkeypatch, case):
    mod, attr, wrap = PHASE_C_MUTATIONS[case]
    monkeypatch.setattr(mod, attr, wrap(getattr(mod, attr)))
    text, kind, slot, want = PHASE_C[case]
    got = _lowered(al_parser, _stmt(text), kind, slot)     # never raises: refusals and lost fields render
    assert got != want, f"mutation survived: {got}"


def test_phase_c_single_ownership(al_parser, monkeypatch):
    """Spec 7.1: a leading prefix, the root's operand group and the root tail are ONE composition."""
    src = _stmt(b"x :=\n#if X\n 1 +\n#endif\n#if Y\n 2\n#else\n 4\n#endif\n#if Z\n * 3\n#endif\n;")
    composed = []
    real = regions._compose
    monkeypatch.setattr(regions, "_compose", lambda run, f, at: composed.append(at) or real(run, f, at))
    disc = discover(src)
    root, extras, _ = ir.from_tree(al_parser.parse(src))
    for env in configurations(disc):
        composed.clear()
        lower_tree(root, extras, resolve(src, env))
        assert len(composed) == 1, (sorted(env), [a.kind for a in composed])
    monkeypatch.setattr(regions, "_compose", real)
    witness.assert_all_pass(al_parser, src)


@pytest.mark.parametrize("text", [b"x := 2 *\n#if X\n 3\n#endif\n;", b"x :=\n#if X\n 3\n#endif\n;"],
                         ids=["binary right", "whole root"])
def test_operand_group_without_else_at_no_arm_is_invalid(al_parser, monkeypatch, text):
    """`x := 2 *;` / `x := ;` at X=0: the composed run lacks an operand, contract-shape (spec 7
    step 3). The runner sees the reference error first, so the lowering verdict is asserted
    directly. Mutation: the group falls back to its first arm."""
    src = _stmt(text)
    assert witness.verdicts(al_parser, src)["X=1"][0] == "pass"
    root, extras, _ = ir.from_tree(al_parser.parse(src))

    def lowered_at_x0():
        lower_tree(root, extras, resolve(src, frozenset()))

    with pytest.raises(LoweringError) as e:
        lowered_at_x0()
    assert e.value.kind == "contract-shape", e.value
    monkeypatch.setattr(regions, "active_arm", _first_arm_fallback(regions.active_arm))
    with pytest.raises(LoweringError) as e:    # killed: no contract-shape any more
        lowered_at_x0()
    assert e.value.kind != "contract-shape", e.value


# --- Task 10 finding: a non-alternating expression list is a discrepancy -------------------
# 29a6eb2 read `Foo(1 #if TPL + 2 #if X +2 #endif #if Y +3 #endif #endif, 2)` as an argument
# group whose arm is a comma-less unary `+2` argument plus tails. At TPL=1 the flat text is one
# argument `1 + 2 ...`, and a clean flat argument list always alternates, so the tree is wrong:
# that must be a discrepancy, not a list-separator refusal. The wrong tree is rebuilt here from
# today's (a root tail beside `1`).
SILENT = _stmt(b"Foo(1\n#if TPL\n+ 2\n#if X\n+2\n#endif\n#if Y\n+3\n#endif\n#endif\n, 2);")


def _silent_wrong_tree(root):
    args = _find(root, "argument_list")
    found = [(i, c) for i, c in enumerate(args.children) if c.kind == regions.TAIL] if args else []
    if not found:      # the flat reference parse goes through ir.from_tree too
        return root
    i, tail = found[0]
    k = tail.children
    op, operand, tx, ty = k[1], k[2], k[3], k[4]
    unary = ir.Node("unary_expression", True, None, op.start, operand.end,
                    [op.copy(field="operator"), operand.copy(field="operand")])
    group = ir.Node("preproc_conditional_arguments", True, None, tail.start, tail.end,
                    [k[0], unary, tx.copy(children=tx.children + [ty]), k[-1]])
    args.children[i] = group
    return root


def _injected_verdicts(parser, monkeypatch, src, mutate):
    """The oracle's verdicts with `mutate` applied to the multi-configuration IR only (the flat
    reference parses go through ir.from_tree too, and hold no directive)."""
    from tools.config_oracle import runner
    real = runner.ir.from_tree

    def mutated(tree):
        root, extras, problems = real(tree)
        return (mutate(root) if _find(root, "preproc_if") else root), extras, problems

    monkeypatch.setattr(runner.ir, "from_tree", mutated)
    try:
        return witness.verdicts(parser, src)
    finally:
        monkeypatch.setattr(runner.ir, "from_tree", real)


def _silent_verdicts(parser, monkeypatch):
    return _injected_verdicts(parser, monkeypatch, SILENT, _silent_wrong_tree)


def _field(n, name):
    return next(c for c in n.children if c.field == name)


RECEIVER = _stmt(b"x := c +\n#if X\n a\n#else\n b\n#endif\n .Foo;")


def _receiver_misattached(root):
    """`(c + g).Foo`: the receiver group's postfix moved onto the whole binary (review W1)."""
    asg = _find(root, "assignment_statement")
    add = _field(asg, "right")
    mem = _field(add, "right")
    g, dot, member = mem.children
    left = ir.Node("additive_expression", True, "object", add.start, g.end,
                   [_field(add, "left"), _field(add, "operator"), g.copy(field="right")])
    asg.children[asg.children.index(add)] = ir.Node("member_expression", True, "right", add.start, mem.end,
                                                     [left, dot, member])
    return root


def test_receiver_attachment(al_parser, monkeypatch):
    """The postfix binds to the receiver group alone (spec 3.4): `c + g.Foo`. Mutation: the
    misattached tree `(c + g).Foo`, a discrepancy in both configurations."""
    _check(al_parser, RECEIVER, _X01("(+ c b.Foo)", "(+ c a.Foo)"))
    v = _injected_verdicts(al_parser, monkeypatch, RECEIVER, _receiver_misattached)
    assert {c: s for c, (s, _) in v.items()} == {"X=0": "discrepancy", "X=1": "discrepancy"}, v
    assert all(any("|structure|" in i for i in items) for _, items in v.values()), v


def test_silent_wrong_tree_is_a_discrepancy(al_parser, monkeypatch):
    witness.assert_all_pass(al_parser, SILENT)          # today's tree
    v = _silent_verdicts(al_parser, monkeypatch)
    assert {c: s for c, (s, _) in v.items() if c.startswith("TPL=1")} == {
        c: "discrepancy" for c in v if c.startswith("TPL=1")}, v
    assert all(s == "pass" for c, (s, _) in v.items() if c.startswith("TPL=0")), v
    # mutation: the pre-Task-11 refusal of every non-alternating list
    monkeypatch.setattr(engine, "ADJACENT_DISCREPANCY", False)
    v = _silent_verdicts(al_parser, monkeypatch)
    assert all(s == "cannot-validate" for c, (s, _) in v.items() if c.startswith("TPL=1")), v


def test_list_spanning_keeps_its_refusal(al_parser):
    """Spec 3.4 list spanning (`Foo(1 #if X + 2, 3 #endif)`), deferred: the group's arm continues
    the item before it AND supplies a separator, so the pinned wrong tree stays a refusal."""
    v = witness.verdicts(al_parser, _stmt(b"I := Foo(1\n#if X\n + 2, 3\n#endif\n);"))
    assert v["X=0"][0] == "pass", v
    assert v["X=1"][0] == "cannot-validate" and "list spanning" in v["X=1"][1][0], v


def test_alternation_checks_the_whole_list():
    """Review M4: an unflagged adjacency (owed to the comparison) must not end the check, so a
    later spanning adjacency or a trailing separator in the same list still refuses. The
    868f52a code returned at the first adjacency and accepted both lists."""
    n = lambda k, s: ir.Node(k, k != ",", None, s, s + 1, [])  # noqa: E731
    span = n("unary_expression", 5)
    setattr(span, engine.LIST_SPAN, True)
    two = ir.Node("argument_list", True, None, 0, 7,
                  [n("integer", 0), n("unary_expression", 1), n(",", 2), n("integer", 3), span, n(",", 6),
                   n("integer", 7)])
    with pytest.raises(LoweringError, match="list spanning"):
        engine._check_alternation(two)
    trailing = ir.Node("list_literal", True, None, 0, 3,
                       [n("integer", 0), n("unary_expression", 1), n(",", 2)])
    with pytest.raises(LoweringError, match="ends with a separator"):
        engine._check_alternation(trailing)
    engine._check_alternation(ir.Node("argument_list", True, None, 0, 4,         # adjacency alone: owed,
                                      [n("integer", 0), n("unary_expression", 1), n(",", 2),
                                       n("integer", 3)]))                         # no refusal


EMPTY_ITEM = _stmt(b"I := Foo(1\n#if X\n#if Y\n + 5\n#endif\n , 3\n#endif\n);")


def test_empty_operand_group_list_item(al_parser, monkeypatch):
    """Review M2: at X=1,Y=0 the argument group's arm holds an operand group with no live arm,
    then `, 3`. The flat `Foo(1 , 3)` is valid, so the empty group is no item (not contract-shape,
    which claims invalid AL) and the comparison proves the configuration. X=1,Y=1 is spec 3.4
    list spanning. Mutation: EMPTY_LIST_ITEM off, the old contract-shape."""
    v = witness.verdicts(al_parser, EMPTY_ITEM)
    assert v["X=1,Y=0"][0] == "pass" and any(i.startswith("normalised:empty-list-item") for i in v["X=1,Y=0"][1]), v
    assert v["X=1,Y=1"][0] == "cannot-validate" and "list spanning" in v["X=1,Y=1"][1][0], v
    assert all(v[c][0] == "pass" for c in v if c.startswith("X=0")), v
    monkeypatch.setattr(regions, "EMPTY_LIST_ITEM", False)
    v = witness.verdicts(al_parser, EMPTY_ITEM)
    assert v["X=1,Y=0"][0] == "cannot-validate" and v["X=1,Y=0"][1][0].startswith("lowering:contract-shape"), v


def test_empty_operand_group_list_item_still_checked(al_parser):
    """An empty group item that leaves the list malformed is refused by the list's own check
    with its own reason, not contract-shape: `[1, #if X 2 #endif , 3]` at X=0 reads `[1, , 3]`
    (the runner sees the flat reference error first, so the lowering is asserted directly)."""
    src = _stmt(b"x := [1,\n#if X\n 2\n#endif\n , 3];")
    root, extras, _ = ir.from_tree(al_parser.parse(src))
    assert _find(root, regions.OPERAND_GROUP) is not None
    with pytest.raises(LoweringError) as e:
        lower_tree(root, extras, resolve(src, frozenset()))
    assert e.value.kind == "list-separator", e.value


# --- re-review N1: a non-expression token is never a region atom -------------------------
# Hand-built trees in which a group absorbs a list separator after its #endif. 71a772a spliced
# the `,` as an operand atom; for the operand group alone the composed "atom" was the `,`
# itself, which then served as the list's separator, and X=1,Y=0 PASSED.

def _move_after_endif(root, group_kind, token_kind):
    """Move the first `token_kind` sibling following the first `group_kind` node into it."""
    stack = [root]
    while stack:
        p = stack.pop()
        for i, c in enumerate(p.children):
            if c.kind == group_kind:
                j = next(k for k in range(i + 1, len(p.children)) if p.children[k].kind == token_kind)
                tok = p.children[j]
                p.children[i] = c.copy(children=c.children + [tok], end=tok.end)
                del p.children[j]
                return root
        stack.extend(p.children)
    return root


def _not_pass(v):
    return all(s != "pass" for s, _ in v.values())


def test_separator_absorbed_by_an_operand_group(al_parser, monkeypatch):
    """Review N1, the reviewer's tree: the arm's `,` moved inside the empty operand group, after
    its #endif. Fails at 71a772a (X=1,Y=0 pass)."""
    v = _injected_verdicts(al_parser, monkeypatch, EMPTY_ITEM,
                           lambda r: _move_after_endif(r, regions.OPERAND_GROUP, ","))
    assert v["X=1,Y=0"][0] == "cannot-validate" and "not a region atom" in v["X=1,Y=0"][1][0], v
    assert all(v[c][0] != "pass" for c in v if c.startswith("X=1")), v


def test_separator_absorbed_by_a_tail(al_parser, monkeypatch):
    """The tail path shares _group_run: `Foo(1 #if X + #endif 2, 3)` (B3 form) with the list's
    `,` moved into the tail's trail. Measured at 71a772a: already refused at both configurations
    (X=0 reference-error, the flat `Foo(1 2, 3)` is invalid; X=1 compose saw two operands), so
    no hole; the X=1 refusal now names the token."""
    src = _stmt(b"I := Foo(1\n#if X\n +\n#endif\n 2, 3);")
    v = _injected_verdicts(al_parser, monkeypatch, src, lambda r: _move_after_endif(r, regions.TAIL, ","))
    assert _not_pass(v) and "not a region atom" in v["X=1"][1][0], v


def test_separator_absorbed_by_a_leading_prefix(al_parser, monkeypatch):
    """The leading-prefix path: `Foo(#if X 1 + #endif 2, 3)` with the `,` moved into the prefix
    after its #endif (its run is then followed by the root's `2`). Measured at 71a772a: already
    refused at both configurations, no hole; the refusal now names the token."""
    src = _stmt(b"I := Foo(\n#if X\n 1 +\n#endif\n 2, 3);")

    def mutate(root):
        args = _find(root, "argument_list")
        if args is None or not any(c.kind == regions.PREFIX for c in args.children):
            return root
        i = next(k for k, c in enumerate(args.children) if c.kind == regions.PREFIX)
        j = next(k for k, c in enumerate(args.children) if c.kind == ",")
        tok = args.children.pop(j)
        args.children[i] = args.children[i].copy(children=args.children[i].children + [tok])
        return root

    v = _injected_verdicts(al_parser, monkeypatch, src, mutate)
    assert _not_pass(v) and all("not a region atom" in items[0] for _, items in v.values()), v
