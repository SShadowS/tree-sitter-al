from pathlib import Path

from tools.b7_audit import census, grammar

MINI = Path(__file__).with_name("mini_grammar.json")


def occ(g):
    return {(o.rule, o.text, o.context) for o in census.occurrences(g)}


def test_contexts():
    got = occ(grammar.load(MINI))
    assert ("list", ",", "repeat") in got
    assert ("trail", ",", "repeat") in got and ("trail", ",", "optional") in got
    assert ("rec", ";", "recursive") in got
    assert ("_helper", ",", "caller-repeat") in got
    assert ("fixed", ";", "fixed") in got and ("member", ".", "fixed") in got
    assert ("tok", "::", "lexical") in got           # listed, never dropped


def test_visible_cycle_is_not_list_recursion():
    got = occ(grammar.load(MINI))
    assert ("fixed2", ";", "fixed") in got


def test_hidden_helper_right_recursion():
    assert ("hrec", ",", "recursive") in occ(grammar.load(MINI))


def test_caller_repeat_only_when_separator_joins():
    got = occ(grammar.load(MINI))
    assert ("hdr", ";", "fixed") in got                       # interior separator
    assert ("_trailer", ",", "caller-repeat") in got          # separator last
    assert ("_helper", ",", "caller-repeat") in got           # separator first


def test_brackets_are_not_boundaries():
    assert not any(o.text in "()" for o in census.occurrences(grammar.load(MINI)))


def test_cycle_terminates():
    census.occurrences(grammar.load(MINI))


def test_keys_stable_and_sorted():
    a = [census.key_of(o) for o in census.occurrences(grammar.load(MINI))]
    assert a == sorted(a) and len(a) == len(set(a))


def test_boundary_key():
    assert census.key_of(census.Boundary("r", "s", "end", (), False)) == "bnd:r:s:end"


def test_real_grammar_finds_item_30_trailing_comma():
    g = grammar.load(Path("src/grammar.json"))
    assert ("_link_value_run", ",", "optional") in occ(g)   # deferred item 30


def bnd(g):
    return {(b.rule, b.slot, b.edge): (b.mechanisms, b.required) for b in census.boundaries(g)}


def test_edges_and_mechanisms():
    b = bnd(grammar.load(MINI))
    assert b[("assign", "right", "end")] == (("tail", "tail-operator-only"), False)
    assert b[("loop", "end", "end")][0] == ("tail", "tail-operator-only")
    assert b[("loop", "start", "end")][0] == ()          # tail is after `end`, not `start`
    assert b[("idx", "index", "end")][0] != ()           # first index has the tail
    assert b[("idx", "index", "between")][0] == ()       # later indices do not
    assert b[("req", "value", "end")] == (("tail", "tail-operator-only"), True)
    assert b[("until", "condition", "end")][0] == ()
    assert ("operand-prefix",) == b[("binop", "right", "start")][0]


def test_real_grammar_until_has_no_mechanism():
    b = bnd(grammar.load(Path("src/grammar.json")))
    hits = [k for k, (m, _) in b.items() if k[0] == "repeat_statement" and k[2] == "end"]
    assert hits and all(b[k][0] == () for k in hits)     # deferred item 39, shape 1
