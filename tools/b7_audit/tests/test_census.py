from pathlib import Path

import pytest

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


def test_real_grammar_until_is_a_region_root():
    # Deferred item 39 shape 1, closed by B7b-2 Phase B: the until condition is a region root
    # (_region_root_condition), so its end edge carries the optional tail and keeps its key.
    b = bnd(grammar.load(Path("src/grammar.json")))
    assert b[("repeat_statement", "condition", "end")] == b[("assignment_statement", "right", "end")]
    assert b[("repeat_statement", "condition", "end")][0] != ()


def test_region_root_wrappers_expand_into_their_callers():
    g = grammar.load(Path("src/grammar.json"))
    b = bnd(g)
    tail = (census._tail_mechanisms(g["rules"]), False)
    assert tail[0] and not any(k[0].startswith("_region_root") for k in b)
    for host in ("if_statement", "while_statement", "case_statement", "for_statement", "with_statement"):
        slot = {"case_statement": "expression", "for_statement": "start", "with_statement": "record"}.get(host, "condition")
        assert b[(host, slot, "end")] == tail, host
    assert b[("parenthesized_expression", "1", "end")] == tail
    bad = {"rules": {"_region_root_x": {"type": "SYMBOL", "name": "_expression"}, "_expression": {"type": "BLANK"}}}
    with pytest.raises(ValueError):
        census._region_roots(bad["rules"], {"_expression"})


def rows(g):
    return {(b.rule, b.slot, b.edge): b for b in census.boundaries(g)}


def test_between_by_separator_without_field():
    b = bnd(grammar.load(MINI))
    assert b[("lst", "1", "start")][0] == () and b[("lst", "1", "end")][0] == ()
    assert b[("lst", "2.0.1", "between")][0] == ()


def test_real_between_rows():
    # B7b-2 Phase B: the second and later index / element are region roots, so their between
    # edge carries the optional tail. Phase C (Task 10): the list's element-group items are region
    # roots too (_region_root_list_element), so their between edge carries it as well.
    g = grammar.load(Path("src/grammar.json"))
    b = bnd(g)
    tail = (census._tail_mechanisms(g["rules"]), False)
    assert tail[0] and b[("subscript_expression", "0.3.0.1", "between")] == tail
    assert b[("list_literal", "1.0.1.0.1", "between")] == tail
    group = [v for k, v in b.items() if k[0] == "preproc_conditional_list_elements" and k[2] == "between"]
    assert group and all(v == tail for v in group)


def test_wrappers_are_not_hosts_and_no_empty_slot():
    for g in (grammar.load(MINI), grammar.load(Path("src/grammar.json"))):
        ks = census.boundaries(g)
        assert all(x.slot for x in ks)
        assert not any(x.rule in ("_wrapper", "_field_source", "_list_element") for x in ks)


def test_differing_arms_get_one_row_each():
    b = bnd(grammar.load(MINI))
    ends = {k: v for k, v in b.items() if k[0] == "arms" and k[2] == "end"}
    assert len(ends) == 2 and all(k[1].startswith("cond@") for k in ends)
    assert sorted(v[0] for v in ends.values()) == [(), ("tail", "tail-operator-only")]
    assert ("arms", "cond", "start") in b            # arms agree on start: one row


def test_choice_climb():
    assert bnd(grammar.load(MINI))[("psplit", "0.0", "end")] == (("tail", "tail-operator-only"), True)
