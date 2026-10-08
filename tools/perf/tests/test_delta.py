"""delta: the B7b-3 structural delta classifier (spec section 7.2), on hand-built row pairs.

Each pair mirrors what the current parser gives for the old side (`python tools/snip.py`)
and the section 7.2 edit for the new side. Rows use `incremental.rows`' format; points are
(0, byte) since every source here is one line unless a test says otherwise."""
import json
from pathlib import Path

import pytest

from tools.perf import ab_accept, delta


# ---- a tiny tree builder -------------------------------------------------------------

def n(type_, span, *kids, field=None, anon=False, extra=False, grammar=None, err=False):
    return {"t": type_, "g": grammar or type_, "named": not anon, "extra": extra, "f": field,
            "s": span[0], "e": span[1], "k": list(kids), "err": err}


def a(tok, span, **kw):
    """An anonymous token."""
    return n(tok, span, anon=True, **kw)


def rows_of(root):
    out = []

    def walk(x, d):
        out.append((d, x["t"], x["g"], x["named"], False, x["extra"], x["f"], x["s"], x["e"],
                    (0, x["s"]), (0, x["e"]), x["err"]))
        for k in x["k"]:
            walk(k, d + 1)
    walk(root, 0)
    return out


def at(src, text, nth=0):
    i = -1
    for _ in range(nth + 1):
        i = src.index(text, i + 1)
    return (i, i + len(text))


def explain(old, new, src):
    return delta.explain_rows(rows_of(old), rows_of(new), src.encode())


def ident(src, text, nth=0, **kw):
    return n("identifier", at(src, text, nth), **kw)


def kw(src, word, nth=0, **kw_):
    sp = at(src, word, nth)
    return n(f"{word}_keyword", sp, a(word, sp), **kw_)


def ok(ex, *kinds):
    assert ex.unexplained == [], ex.unexplained
    assert sorted(e.kind for e in ex.edits) == sorted(kinds), ex.edits


def bad(ex):
    assert ex.unexplained, "expected an unexplained remainder"


# ---- E1 ------------------------------------------------------------------------------

def test_identical_is_no_edit():
    src = "Bar;"
    t = n("statement_block", (0, 4), n("call_statement", (0, 4), ident(src, "Bar", field="function"), a(";", (3, 4))))
    ok(explain(t, t, src))


def test_e1_statement_block():
    src = "Bar;"
    old = n("statement_block", (0, 4),
            n("call_statement", (0, 4), ident(src, "Bar", field="function"), a(";", (3, 4))))
    new = n("statement_block", (0, 4),
            n("call_statement", (0, 3), ident(src, "Bar", field="function")), a(";", (3, 4)))
    ok(explain(old, new, src), "E1")


def _if(src, then_node, end, else_=()):
    return n("if_statement", (0, end), kw(src, "if"), ident(src, "C", field="condition"),
             kw(src, "then"), then_node, *else_)


def test_e1_then_branch_ancestor_shrinks():
    src = "if C then Bar;"
    old = n("statement_block", (0, 14), _if(src, n("call_statement", (10, 14),
            ident(src, "Bar", field="function"), a(";", (13, 14)), field="then_branch"), 14))
    new = n("statement_block", (0, 14), _if(src, n("call_statement", (10, 13),
            ident(src, "Bar", field="function"), field="then_branch"), 13), a(";", (13, 14)))
    ok(explain(old, new, src), "E1")


def _case(src, branch_kids_old, branch_end_old, branch_kids_new, branch_end_new):
    def build(kids, bend):
        return n("statement_block", (0, len(src)), n("case_statement", (0, len(src) - 1),
                 kw(src, "case"), ident(src, "I", field="expression"), kw(src, "of"),
                 n("case_body", (10, bend), n("case_branch", (10, bend), *kids), field="body"),
                 kw(src, "end")), a(";", (len(src) - 1, len(src))))
    return build(branch_kids_old, branch_end_old), build(branch_kids_new, branch_end_new)


def test_e1_case_branch_owns_semicolon():
    src = "case I of 1: Bar; end;"
    pat = lambda: [n("integer", (10, 11), field="pattern"), a(":", (11, 12))]
    old, new = _case(
        src,
        pat() + [n("call_statement", (13, 17), ident(src, "Bar", field="function"), a(";", (16, 17)), field="body")], 17,
        pat() + [n("call_statement", (13, 16), ident(src, "Bar", field="function"), field="body"), a(";", (16, 17))], 17)
    ok(explain(old, new, src), "E1")


def test_e1_semicolon_to_unapproved_owner():
    """Nearest owner is the case_branch; the `;` landing in the statement_block is refused."""
    src = "case I of 1: Bar; end;"
    pat = lambda: [n("integer", (10, 11), field="pattern"), a(":", (11, 12))]
    old, _ = _case(src, pat() + [n("call_statement", (13, 17), ident(src, "Bar", field="function"),
                                   a(";", (16, 17)), field="body")], 17, [], 0)
    new = n("statement_block", (0, 22), n("case_statement", (0, 21), kw(src, "case"),
            ident(src, "I", field="expression"), kw(src, "of"),
            n("case_body", (10, 16), n("case_branch", (10, 16), *pat(),
              n("call_statement", (13, 16), ident(src, "Bar", field="function"), field="body")), field="body"),
            a(";", (16, 17)), kw(src, "end")), a(";", (21, 22)))
    ex = explain(old, new, src)
    bad(ex)
    assert any("E1 refused" in u for u in ex.unexplained)


# ---- E2 ------------------------------------------------------------------------------

def _split(src, semi_inside, extra=None, extra_where=None):
    """`#if X\\nFoo(A,\\n#else\\nFoo(B,\\n#endif\\nC);` as preproc_split_call_statement."""
    kids = [n("preproc_if", at(src, "#if X"), n("preproc_open", at(src, "#if")), ident(src, "X", field="condition")),
            ident(src, "Foo"), a("(", at(src, "(")), ident(src, "A"), a(",", at(src, ",")),
            n("preproc_else", at(src, "#else")), ident(src, "Foo", 1), a("(", at(src, "(", 1)), ident(src, "B"),
            a(",", at(src, ",", 1)), n("preproc_endif", at(src, "#endif"), n("preproc_close", at(src, "#endif"))),
            ident(src, "C"), a(")", at(src, ")"))]
    semi = a(";", at(src, ";"))
    if extra is not None and extra_where == "call":
        kids.append(extra)
    end = kids[-1]["e"]
    if semi_inside:
        kids.append(semi)
        end = semi["e"]
    call = n("preproc_split_call_statement", (0, end), *kids)
    outer = [call]
    if extra is not None and extra_where == "owner":
        outer.append(extra)
    if not semi_inside:
        outer.append(semi)
    return n("statement_block", (0, semi["e"]), *outer)


SPLIT = "#if X\nFoo(A,\n#else\nFoo(B,\n#endif\nC);"


def test_e2_split_call():
    ok(explain(_split(SPLIT, True), _split(SPLIT, False), SPLIT), "E2")


# ---- extras under E1/E2 --------------------------------------------------------------

@pytest.mark.parametrize("comment", ["// c\n", "/* c */ "])
@pytest.mark.parametrize("placement", ["owner", "call"])
def test_e1_extras_before_semi(comment, placement):
    src = "Bar " + comment + ";"
    c_sp = at(src, comment.strip())
    semi = (len(src) - 1, len(src))
    com = lambda: n("comment", c_sp, extra=True)
    old = n("statement_block", (0, semi[1]),
            n("call_statement", (0, semi[1]), ident(src, "Bar", field="function"), com(), a(";", semi)))
    if placement == "owner":
        new = n("statement_block", (0, semi[1]),
                n("call_statement", (0, 3), ident(src, "Bar", field="function")), com(), a(";", semi))
    else:
        new = n("statement_block", (0, semi[1]),
                n("call_statement", (0, c_sp[1]), ident(src, "Bar", field="function"), com()), a(";", semi))
    ok(explain(old, new, src), "E1")


@pytest.mark.parametrize("comment", ["// c\n", "/* c */ "])
@pytest.mark.parametrize("placement", ["owner", "call"])
def test_e2_extras_before_semi(comment, placement):
    src = SPLIT[:-1] + " " + comment + ";"
    com = n("comment", at(src, comment.strip()), extra=True)
    ok(explain(_split(src, True, com, "call"), _split(src, False, com, placement), src), "E2")


def test_extra_moved_to_unapproved_parent():
    """The comment lands in the shrinking if_statement, not the `;`'s owner."""
    src = "if C then Bar // c\n;"
    c_sp, semi = at(src, "// c"), (len(src) - 1, len(src))
    com = lambda: n("comment", c_sp, extra=True)
    old = n("statement_block", (0, semi[1]), _if(src, n("call_statement", (10, semi[1]),
            ident(src, "Bar", field="function"), com(), a(";", semi), field="then_branch"), semi[1]))
    new = n("statement_block", (0, semi[1]), _if(src, n("call_statement", (10, 13),
            ident(src, "Bar", field="function"), field="then_branch"), c_sp[1], (com(),)), a(";", semi))
    bad(explain(old, new, src))


# ---- E3 ------------------------------------------------------------------------------

def _wrap(parent, slot, src="Bar", name="identifier"):
    span = (0, len(src))
    leaf = n(name, span, field=slot)
    call = n("call_statement", span, n(name, span, field="function"), field=slot)
    return n(parent, span, leaf), n(parent, span, call)


SLOTS = sorted(delta.E3_SLOTS, key=str)


def test_tables_match_grammar_routes():
    """Every (host, field) the grammar routes into _statement / _statement_inner /
    _expression_statement is E3-eligible or listed as never-eligible; every `_statement`
    host owns E1's `;`. Names each missing or stale entry."""
    walk = delta.statement_positions()
    pos = {(h, f) for h, f, _ in walk}
    tables = delta.E3_SLOTS | set(delta.NEVER_ELIGIBLE)
    assert not delta.E3_SLOTS & set(delta.NEVER_ELIGIBLE)
    assert pos - tables == set(), f"missing from E3_SLOTS / NEVER_ELIGIBLE: {sorted(pos - tables, key=str)}"
    assert tables - pos == set(), f"stale (no grammar route): {sorted(tables - pos, key=str)}"
    hosts = {h for h, _, t in walk if t == "_statement"}
    assert hosts == delta.STATEMENT_HOSTS, (sorted(hosts - delta.STATEMENT_HOSTS), sorted(delta.STATEMENT_HOSTS - hosts))
    assert delta.CASE_OWNERS <= {h for h, f in pos if f == "body"}


def test_walk_follows_hidden_rules_fields_and_aliases():
    sym = lambda n: {"type": "SYMBOL", "name": n}
    g = {"inline": ["inl"], "rules": {
        "host": {"type": "SEQ", "members": [{"type": "FIELD", "name": "f", "content": sym("_h")}, sym("inl"),
                                             {"type": "ALIAS", "named": True, "value": "renamed", "content": sym("_a")}]},
        "_h": {"type": "CHOICE", "members": [sym("_statement_inner"), sym("other")]},
        "inl": {"type": "REPEAT", "content": sym("_statement")},
        "_a": sym("_expression_statement"), "other": sym("_statement"),
        "_statement": {"type": "BLANK"}, "_statement_inner": {"type": "BLANK"},
        "_expression_statement": {"type": "BLANK"}}}
    assert delta.statement_positions(g) == {("host", "f", "_statement_inner"), ("host", None, "_statement"),
                                            ("renamed", None, "_expression_statement"),
                                            ("other", None, "_statement")}


@pytest.mark.parametrize("parent,slot", SLOTS)
def test_e3_each_slot(parent, slot):
    ok(explain(*_wrap(parent, slot), "Bar"), "E3")


@pytest.mark.parametrize("text", ["Order", "TABLE", "is", "as"])
def test_e3_admitted_names(text):
    ok(explain(*_wrap("statement_block", None, text), text), "E3")


def test_e3_quoted_identifier():
    src = '"Q R"'
    ok(explain(*_wrap("statement_block", None, src, "quoted_identifier"), src), "E3")


def test_e3_order_real_shape():
    """`Order;` today: identifier and `;` both statement_block children (snip)."""
    src = "Order;"
    old = n("statement_block", (0, 6), ident(src, "Order"), a(";", (5, 6)))
    new = n("statement_block", (0, 6), n("call_statement", (0, 5), ident(src, "Order", field="function")),
            a(";", (5, 6)))
    ok(explain(old, new, src), "E3")


def test_e1_split_host_owns_semicolon():
    """A `_statement` inside preproc_split_if_then_begin: the host is the `;`'s owner."""
    src = "#if X\nBar;"
    old = n("preproc_split_if_then_begin", (0, 10), n("preproc_if", (0, 5)),
            n("call_statement", (6, 10), ident(src, "Bar", field="function"), a(";", (9, 10))))
    new = n("preproc_split_if_then_begin", (0, 10), n("preproc_if", (0, 5)),
            n("call_statement", (6, 9), ident(src, "Bar", field="function")), a(";", (9, 10)))
    ok(explain(old, new, src), "E1")


def test_e3_asserterror_body():
    """`asserterror Bar;`: the body is a `_statement_inner` position."""
    src = "asserterror Bar"
    def tree(body):
        return n("asserterror_statement", (0, 15), kw(src, "asserterror"), body)
    old = tree(ident(src, "Bar", field="body"))
    new = tree(n("call_statement", (12, 15), ident(src, "Bar", field="function"), field="body"))
    ok(explain(old, new, src), "E3")


@pytest.mark.parametrize("parent", ["repeat_statement", "case_else_branch"])
def test_statement_block_bodies_not_eligible(parent):
    """Their body holds a statement_block, never a bare statement."""
    bad(explain(*_wrap(parent, "body"), "Bar"))


def test_e1_composed_inside_e3_host():
    """`if C then Bar else Baz;`: then_branch is a bare name today (E3), else_branch a call (E1)."""
    src = "if C then Bar else Baz;"
    end = len(src)
    def tree(then, else_call, if_end, outer_semi):
        return n("statement_block", (0, end), _if(src, then, if_end, (kw(src, "else"), else_call)), *outer_semi)
    old = tree(ident(src, "Bar", field="then_branch"),
               n("call_statement", (19, end), ident(src, "Baz", field="function"), a(";", (22, 23)), field="else_branch"),
               end, ())
    new = tree(n("call_statement", (10, 13), ident(src, "Bar", field="function"), field="then_branch"),
               n("call_statement", (19, 22), ident(src, "Baz", field="function"), field="else_branch"),
               22, (a(";", (22, 23)),))
    ok(explain(old, new, src), "E1", "E3")


# ---- forbidden -----------------------------------------------------------------------

def test_case_pattern_wrapped():
    bad(explain(*_wrap("case_branch", "pattern"), "Bar"))


def test_trigger_body_wrapped():
    bad(explain(*_wrap("trigger_declaration", "body"), "Bar"))


@pytest.mark.parametrize("slot", ["condition", "expression", "left", "right"])
def test_expression_slots_not_eligible(slot):
    bad(explain(*_wrap("if_statement", slot), "Bar"))


def test_else_wrapped():
    ex = explain(*_wrap("statement_block", None, "else"), "else")
    bad(ex)
    assert any("keyword" in u for u in ex.unexplained)


@pytest.mark.parametrize("word", ["and", "div", "begin", "exit", "true", "asserterror"])
def test_keyword_table_not_admitted(word):
    bad(explain(*_wrap("statement_block", None, word), word))


def test_callee_replaced():
    src = "Bar;"
    old = n("statement_block", (0, 4), n("call_statement", (0, 4), ident(src, "Bar", field="function"), a(";", (3, 4))))
    new = n("statement_block", (0, 4), n("call_statement", (0, 3),
            n("quoted_identifier", (0, 3), field="function")), a(";", (3, 4)))
    bad(explain(old, new, src))


def test_parent_field_reassigned():
    old, new = _wrap("if_statement", "then_branch")
    new["k"][0]["f"] = "else_branch"
    bad(explain(old, new, "Bar"))


def test_any_change_with_has_error():
    src = "Bar;"
    old = n("statement_block", (0, 4), n("call_statement", (0, 4), ident(src, "Bar", field="function"),
            a(";", (3, 4))), err=True)
    new = n("statement_block", (0, 4), n("call_statement", (0, 3), ident(src, "Bar", field="function")),
            a(";", (3, 4)), err=True)
    ex = explain(old, new, src)
    bad(ex)
    assert ex.edits == [] and "has_error" in ex.unexplained[0]


def test_remainder_is_listed_not_dropped():
    src = "Bar;"
    old = n("statement_block", (0, 4), n("call_statement", (0, 4), ident(src, "Bar", field="function"), a(";", (3, 4))))
    new = n("statement_block", (0, 4), n("assignment_statement", (0, 4), ident(src, "Bar", field="left"), a(";", (3, 4))))
    ex = explain(old, new, src)
    assert any(u.startswith("-") for u in ex.unexplained) and any(u.startswith("+") for u in ex.unexplained)


# ---- ab_accept -----------------------------------------------------------------------

def _ab(tmp_path, name, median, identical=True, rounds=24, lib_b="b.dll", sha_b="2"):
    p = tmp_path / name
    g = {"trees_identical": identical, "lib_a": {"path": "a.dll", "sha256": "1"},
         "lib_b": {"path": lib_b, "sha256": sha_b}}
    if identical:
        g.update(rounds=rounds, ratio_a_over_b={"median": median})
    p.write_text(json.dumps({"groups": {"ab": g}}))
    return str(p)


@pytest.mark.parametrize("m1,m2,ident_,code", [(0.99, 0.97, True, 0), (0.99, 0.969, True, 1),
                                               (1.0, 1.0, False, 1)])
def test_ab_accept(tmp_path, capsys, m1, m2, ident_, code):
    assert ab_accept.main([_ab(tmp_path, "1.json", m1), _ab(tmp_path, "2.json", m2, ident_)]) == code


@pytest.mark.parametrize("kw2", [{"rounds": 8}, {"lib_b": "c.dll"}, {"sha_b": "3"}])
def test_ab_accept_same_libraries_and_enough_rounds(tmp_path, kw2):
    assert ab_accept.main([_ab(tmp_path, "1.json", 1.0), _ab(tmp_path, "2.json", 1.0, **kw2)]) == 1


def test_ab_accept_unreadable(tmp_path):
    assert ab_accept.main([str(tmp_path / "none.json"), str(tmp_path / "none.json")]) == 2


# ---- real library --------------------------------------------------------------------

BC = Path(__file__).resolve().parents[3] / "BC.History"


@pytest.mark.skipif(not BC.is_dir(), reason="BC.History not present")
def test_same_library_over_bc_history_sample(al_parser, tmp_path):
    """Same library on both sides over 20 BC.History files: exit 0, 0 changed files."""
    from tools.query_coverage import loader
    lib = loader.ensure_library(loader.REPO_ROOT)
    root = tmp_path / "c"
    root.mkdir()
    for p in sorted(BC.rglob("*.al"))[:20]:
        (root / p.name).write_bytes(p.read_bytes())
    out = delta.run(lib, lib, ["t"], workers=1, roots={"t": root})
    assert out == {"t": (20, [])}
    assert delta.report(out) == 0


# ---- reviewed exceptions (delta-reviewed.tsv, B7b-3 Task 4 ruling) --------------------

def _changed(sha="ab" * 32, has_error=(True, True)):
    return {"file": "c:x.al", "edits": [], "unexplained": ["has_error ..."], "sha256": sha,
            "has_error": list(has_error)}


@pytest.mark.parametrize("sha,has_error,code", [
    ("ab" * 32, (True, True), 0),      # listed, sha matches, errored: reviewed
    ("cd" * 32, (True, True), 1),      # the source changed since the review
    ("ab" * 32, (False, False), 1),    # listed, but a clean file is never a reviewed exception
])
def test_reviewed_exception(sha, has_error, code):
    out = {"c": (1, [_changed(sha, has_error)])}
    assert delta.report(out, reviewed={"c:x.al": ("ab" * 32, "recovery only")}) == code


def test_unlisted_unexplained_file_fails():
    assert delta.report({"c": (1, [_changed()])}, reviewed={}) == 1


def test_reviewed_file_loads(tmp_path):
    p = tmp_path / "r.tsv"
    p.write_text("# c\n" + delta.REVIEWED_HEADER + "\nc\tx.al\t" + "AB" * 32 + "\twhy\n", encoding="utf-8")
    assert delta.load_reviewed(p) == {"c:x.al": ("ab" * 32, "why")}
    p.write_text("corpus\tpath\n", encoding="utf-8")
    with pytest.raises(ValueError):
        delta.load_reviewed(p)
    assert delta.load_reviewed()          # the committed list parses and is not empty
