from dataclasses import replace

import pytest

from tools.b7_audit import judge
from tools.b7_audit.registry import Row

SHA = "c" * 64
UNCHECKED_REP = judge.UNCHECKED_REP


def rec(config="-", alc="ACCEPT", err=False, oracle="pass", reject_class=None, control="typed",
        intended=True, cell="c", sampled_by=None, hole=False):
    """One real-shape evidence record."""
    r = {"cell": cell, "config": config, "source_sha256": SHA, "intended_valid": intended,
         "control": control, "parser_has_error": err, "error_in_hole": hole,
         "oracle": {"status": oracle, "reasons": []},
         "alc": "class-sampled" if sampled_by else "measured",
         "alc_split": None, "alc_flat": None, "alc_control": None, "reject_class": reject_class}
    if sampled_by:
        r["alc_representative"] = sampled_by
    else:
        codes = {"syntax": ["AL0104"], "semantic": ["AL0175"]}.get(reject_class, [])
        r["alc_flat"] = {"verdict": alc, "codes": codes if alc == "REJECT" else []}
    return [r]


def holds(sha=SHA, ok=True, fps=None, cell="c"):
    return judge.Assertion(cell, "(x)", fps or judge.fingerprints(sha), "r", holds=ok)


def test_gap():
    assert judge.verdict(rec(err=True), None).name == "GAP"


def test_silent_from_oracle():
    assert judge.verdict(rec(oracle="discrepancy"), None).name == "SILENT"
    assert judge.verdict(rec(oracle="representation-violation"), None).name == "SILENT"


def cv(reasons=("one-reading",), **kw):
    r = rec(oracle="cannot-validate", **kw)
    r[0]["oracle"]["reasons"] = list(reasons)
    return r


def test_cannot_validate_no_assertion_unchecked():
    assert judge.verdict(cv(), None).name == "UNCHECKED"


def test_cannot_validate_closed_by_holding_assertion():
    v = judge.verdict(cv(), holds())
    assert (v.name, v.detail) == ("CONSISTENT", "assertion-closed: one-reading")


def test_cannot_validate_failing_assertion_is_silent():
    assert judge.verdict(cv(), holds(ok=False)).name == "SILENT"


def test_cannot_validate_stale_assertion_unchecked():
    assert judge.verdict(cv(), holds(fps=("old",) * 4)).name == "UNCHECKED"


def test_directive_mismatch_is_silent():
    assert judge.verdict(rec(oracle="directive-mismatch"), None).name == "SILENT"


def test_mixed_with_gap_and_silent_accepted_configs():
    recs = rec("X=0", alc="REJECT", reject_class="syntax") + rec("X=1", err=True)
    assert judge.verdict(recs, None).detail == "X=0:REJECTED/syntax/over-accepts;X=1:GAP"
    recs = rec("X=0", alc="REJECT", reject_class="syntax") + rec("X=1", oracle="discrepancy")
    assert judge.verdict(recs, None).detail == "X=0:REJECTED/syntax/over-accepts;X=1:SILENT"


def test_all_accepted_priority_order():
    def mk(*pairs):
        return [r for c, o, e in pairs for r in rec(c, oracle=o, err=e)]
    a = holds()
    assert judge.verdict(mk(("a", "pass", False), ("b", "cannot-validate", False)), a).name == "CONSISTENT"
    assert judge.verdict(mk(("a", "pass", False), ("b", "cannot-validate", False)), None).name == "UNCHECKED"
    assert judge.verdict(mk(("a", "pass", False), ("b", "discrepancy", False)), a).name == "SILENT"
    assert judge.verdict(mk(("a", "discrepancy", False), ("b", "pass", True)), a).name == "GAP"


def test_reject_class_none_is_unverified():
    r = rec(alc="REJECT", reject_class=None)
    assert judge.verdict(r, None).detail == "unverified/over-accepts"


def test_representative_without_alc_is_vector_mismatch():
    bad = rec(cell="rep")
    bad[0]["alc_flat"] = None
    v = judge.verdict(sampled(), holds(cell='s'), lookup={"rep": bad}.get)
    assert (v.name, v.detail) == ("UNCHECKED", UNCHECKED_REP)


def test_assertion_for_another_cell_rejected():
    other = judge.Assertion("zzz", "(x)", judge.fingerprints(SHA), "r", holds=True)
    with pytest.raises(ValueError):
        judge.verdict(rec(), other)
    assert judge.verdict(rec(), other, cls="zzz").name == "CONSISTENT"


def test_load_assertions_keeps_quotes(tmp_path):
    T, N = chr(9), chr(10)
    fp = ','.join(judge.fingerprints(SHA))
    p = tmp_path / 'a.tsv'
    p.write_text(T.join(['cell_or_class', 'expect', 'fingerprints', 'reason', 'holds']) + N +
                 T.join(['c', '(a "x" (b))', fp, '"why"', 'true']) + N, encoding='utf-8')
    [a] = judge.load_assertions(p)
    assert a.expect == '(a "x" (b))' and a.reason == '"why"'


def test_consistent_needs_assertion():
    assert judge.verdict(rec(), None).name == "UNCHECKED"
    assert judge.verdict(rec(), holds()).name == "CONSISTENT"


def test_failing_assertion_is_silent():
    assert judge.verdict(rec(), holds(ok=False)).name == "SILENT"


def test_mixed():
    recs = rec("X=0", alc="REJECT", reject_class="syntax", err=True) + rec("X=1")
    v = judge.verdict(recs, None)
    assert v.name == "MIXED"
    assert v.detail == "X=0:REJECTED/syntax/agrees;X=1:UNCHECKED"


def test_semantic_reject_not_over():
    v = judge.verdict(rec(alc="REJECT", reject_class="semantic"), None)
    assert (v.name, v.detail) == ("REJECTED", "semantic/over-accepts")


def test_syntax_reject_agrees_and_over():
    assert judge.verdict(rec(alc="REJECT", reject_class="syntax", err=True), None).detail == "syntax/agrees"
    assert judge.verdict(rec(alc="REJECT", reject_class="syntax"), None).detail == "syntax/over-accepts"
    assert judge.verdict(rec(alc="REJECT", reject_class="semantic", err=True), None).detail == "semantic/agrees"


def test_seed_without_control_is_unverified():
    v = judge.verdict(rec(alc="REJECT", reject_class="semantic", control="none"), None)
    assert v.detail == "unverified/over-accepts"
    v = judge.verdict(rec(alc="REJECT", reject_class="semantic", control="none", err=True), None)
    assert v.detail == "unverified/agrees"
    v = judge.verdict(rec(alc="REJECT", reject_class="syntax", control="none"), None)
    assert v.detail == "syntax/over-accepts"


def test_fingerprint_mismatch_reopens():
    a = holds(fps=("old",) * 4)
    assert judge.verdict(rec(), a).name == "UNCHECKED"
    assert judge.verdict(rec(), holds(sha="d" * 64)).name == "UNCHECKED"     # cell source changed


def test_class_assertion_skips_source_fingerprint():
    fps = ("*",) + judge.fingerprints(SHA)[1:]
    assert judge.verdict(rec(), holds(fps=fps)).name == "CONSISTENT"


def test_vector_mismatch_recorded():
    v = judge.verdict(rec(intended=False), None)
    assert v.name == "UNCHECKED" and v.vector_mismatch


def sampled(cfgs=("-",)):
    return [r for c in cfgs for r in rec(c, cell="s", sampled_by="rep", intended=True)]


def test_class_sampled_takes_representative_when_vector_matches():
    lookup = {"rep": rec(cell="rep")}.get
    assert judge.verdict(sampled(), holds(cell='s'), lookup=lookup).name == "CONSISTENT"
    assert judge.verdict(sampled(), None, lookup=lookup).name == "UNCHECKED"


def test_class_sampled_representative_vector_mismatch():
    lookup = {"rep": rec(cell="rep", alc="REJECT", reject_class="syntax", err=True)}.get
    v = judge.verdict(sampled(), holds(cell='s'), lookup=lookup)
    assert (v.name, v.detail) == ("UNCHECKED", "representative vector mismatch")


def test_class_sampled_missing_representative_is_unchecked():
    v = judge.verdict(sampled(), holds(cell='s'), lookup={}.get)
    assert (v.name, v.detail) == ("UNCHECKED", "representative vector mismatch")


def test_class_sampled_still_judges_parser():
    lookup = {"rep": rec(cell="rep")}.get
    s = [dict(sampled()[0], parser_has_error=True)]
    assert judge.verdict(s, None, lookup=lookup).name == "GAP"


def test_template_gap():
    row = Row("k", "h", "role", "fam", "t", "", "TEMPLATE-GAP: no valid filling", "p")
    v = judge.template_gap(row)
    assert (v.name, v.detail) == ("GAP", "template")
    assert judge.template_gap(replace(row, reason="ordinary")) is None


def test_assertions_roundtrip(tmp_path):
    p = tmp_path / "a.tsv"
    p.write_text("# c\ncell_or_class\texpect\tfingerprints\treason\tholds\n"
                 "c\t(a (b))\t" + ",".join(judge.fingerprints(SHA)) + "\twhy\tfalse\n", encoding="utf-8")
    [a] = judge.load_assertions(p)
    assert (a.cell_or_class, a.expect, a.fingerprints, a.reason, a.recorded) == \
        ("c", "(a (b))", judge.fingerprints(SHA), "why", "false")
    committed = judge.load_assertions(judge.HERE / "assertions.tsv")      # the committed rows load
    assert all(len(x.fingerprints) == 4 for x in committed)


SRC = b"codeunit 50100 P { trigger OnRun() begin Foo(1, 2); end; }"


def test_assertion_mutation_can_fail(al_parser):
    root = al_parser.parse(SRC).root_node
    good = judge.Assertion("c", "(call_expression function: (identifier) arguments: (argument_list (integer)))",
                           (), "")
    # the same, one field renamed
    bad = replace(good, expect=good.expect.replace("arguments:", "bogus:"))
    # and one with an element dropped from the middle of the order
    wrong_type = replace(good, expect="(call_expression (argument_list (string_literal)))")
    assert judge.check_assertion(root, good)
    assert not judge.check_assertion(root, bad)
    assert not judge.check_assertion(root, wrong_type)


def test_assertion_wildcard_type(al_parser):
    root = al_parser.parse(SRC).root_node
    a = judge.Assertion("c", "(_ function: (identifier) arguments: (argument_list (integer) (integer)))", (), "")
    assert judge.check_assertion(root, a)
    assert not judge.check_assertion(root, replace(a, expect="(_ function: (identifier) arguments: (argument_list (integer) (integer) (integer)))"))


def _mutate(expect):
    """One mutation that must break any fragment: the first field label renamed `bogus`, else the first
    node type after the root renamed."""
    import re as _re
    m = _re.search(r"\b(\w+):", expect)
    if m:
        return expect[:m.start()] + "bogus:" + expect[m.end():]
    m = _re.search(r"\((\w+)", expect[1:])
    return expect[:m.start() + 1] + "(bogus_" + m.group(1) + expect[m.end() + 1:]


def test_committed_assertion_rows_can_fail(al_parser):
    """Spec 7.3 mutation check over the committed rows: every row that holds on (the first cell of) its cell or
    class stops holding under one mutation, so no committed fragment is vacuous."""
    from tools.b7_audit import evidence
    rows = judge.load_assertions()
    by_target = {}
    for e in evidence.universe():
        by_target.setdefault(e.cell.id, e)
        by_target.setdefault("/".join(e.cls), e)
    checked = 0
    for a in rows:
        root = al_parser.parse(by_target[a.cell_or_class].cell.source.encode("utf-8")).root_node
        if not judge.check_assertion(root, a):
            continue                    # a SILENT row: it fails already (tests/test_silent.py pins those)
        assert not judge.check_assertion(root, replace(a, expect=_mutate(a.expect))), a.cell_or_class
        checked += 1
    assert checked > len(rows) // 2


def test_assertion_exact_children(al_parser):
    root = al_parser.parse(SRC).root_node
    a = judge.Assertion("c", "(argument_list! (integer) (integer))", (), "")
    assert judge.check_assertion(root, a)
    assert judge.check_assertion(root, replace(a, expect="(argument_list (integer))"))          # subsequence
    assert not judge.check_assertion(root, replace(a, expect="(argument_list! (integer))"))    # an extra child


def test_assertion_exact_children_ignore_every_extra(al_parser):
    a = judge.Assertion("c", "(argument_list! (integer) (integer))", (), "")
    for src in (b"codeunit 50100 P { trigger OnRun() begin Foo(1 // c\n, 2); end; }",
                b"codeunit 50100 P { trigger OnRun() begin Foo(1 /* c */, 2); end; }",
                b"codeunit 50100 P { trigger OnRun() begin Foo(1,\n#pragma warning disable AL0001\n2); end; }"):
        root = al_parser.parse(src).root_node
        assert not root.has_error, src
        assert judge.check_assertion(root, a), src
    assert judge.EXTRAS >= {"comment", "multiline_comment", "pragma"}


def test_exact_pattern_refuses_ellipsis():
    with pytest.raises(ValueError, match="exact pattern"):
        judge._read("(argument_list! (integer) ...)")
    assert judge._read("(argument_list (integer) ...)") == ("argument_list", [(None, ("integer", []))])


def test_refresh_rewrites_unchanged_and_lists_flipped(al_parser, tmp_path):
    """A synthetic parser change (an old parser.c/scanner.c/oracle hash in every row): rows whose truth is unchanged
    get the current fingerprints; a flipped row and a row whose cell source changed keep theirs and are listed."""
    import hashlib
    from tools.b7_audit.evidence import Entry
    from tools.b7_audit.placements import Cell

    def entry(cid, src, placement="p"):
        return Entry(Cell(cid, "k", "h", placement, src, (), frozenset(), (0, 0), None), "list-separator", "f")
    one = "codeunit 50100 P { trigger OnRun() begin Foo(1); end; }"
    two = "codeunit 50100 P { trigger OnRun() begin Foo(1, 2); end; }"
    ents = [entry("a", one), entry("b", one), entry("c", two), entry("d", two, "q"), entry("e", one, "q")]
    sha = {e.cell.id: hashlib.sha256(e.cell.source.encode()).hexdigest() for e in ents}
    old, new = ("0" * 64, "1" * 64, "2" * 64), ("3" * 64, "4" * 64, "5" * 64)
    pat = "(argument_list! (integer))"
    rows = [("a", sha["a"], "true"),                  # holds, recorded holding: refreshed
            ("b", sha["b"], "false"),                 # holds, recorded failing: flipped
            ("c", "f" * 64, "false"),                 # its cell source changed since the row was written
            ("list-separator/f/q", "*", "mixed:1/2"),  # class row over d (fails) and e (holds): refreshed
            ("list-separator/f/p", "*", "true")]      # a, b, c have cell rows: covers nothing now
    T = "\t"
    p = tmp_path / "a.tsv"
    p.write_text("# comment kept\n" + T.join(judge.HEAD) + "\n" +
                 "".join(T.join([c, pat, ",".join((s,) + old), "why", h]) + "\n" for c, s, h in rows),
                 encoding="utf-8")
    n, problems = judge.refresh(p, ents, lambda b: al_parser.parse(b).root_node, base=new)
    assert n == 2
    assert problems == ["flipped false -> true\tb", "source changed\tc", "flipped true -> none\tlist-separator/f/p"]
    got = {a.cell_or_class: a.fingerprints for a in judge.load_assertions(p)}
    assert got["a"] == (sha["a"],) + new and got["list-separator/f/q"] == ("*",) + new
    assert got["b"] == (sha["b"],) + old and got["c"] == ("f" * 64,) + old
    assert p.read_text(encoding="utf-8").startswith("# comment kept\n")
