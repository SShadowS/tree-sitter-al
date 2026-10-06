from dataclasses import replace

import pytest

from tools.b7_audit import judge
from tools.b7_audit.registry import Row

SHA = "c" * 64


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


def holds(sha=SHA, ok=True, fps=None):
    return judge.Assertion("c", "(x)", fps or judge.fingerprints(sha), "r", holds=ok)


def test_gap():
    assert judge.verdict(rec(err=True), None).name == "GAP"


def test_silent_from_oracle():
    assert judge.verdict(rec(oracle="discrepancy"), None).name == "SILENT"
    assert judge.verdict(rec(oracle="representation-violation"), None).name == "SILENT"


def test_unchecked_never_consistent():
    assert judge.verdict(rec(oracle="cannot-validate"), None).name == "UNCHECKED"
    assert judge.verdict(rec(oracle="cannot-validate"), holds()).name == "UNCHECKED"


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
    assert judge.verdict(sampled(), holds(), lookup=lookup).name == "CONSISTENT"
    assert judge.verdict(sampled(), None, lookup=lookup).name == "UNCHECKED"


def test_class_sampled_representative_vector_mismatch():
    lookup = {"rep": rec(cell="rep", alc="REJECT", reject_class="syntax", err=True)}.get
    v = judge.verdict(sampled(), holds(), lookup=lookup)
    assert (v.name, v.detail) == ("UNCHECKED", "representative vector mismatch")


def test_class_sampled_missing_representative_is_unchecked():
    v = judge.verdict(sampled(), holds(), lookup={}.get)
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
    p.write_text("# c\ncell_or_class\texpect\tfingerprints\treason\n"
                 "c\t(a (b))\t" + ",".join(judge.fingerprints(SHA)) + "\twhy\n", encoding="utf-8")
    [a] = judge.load_assertions(p)
    assert (a.cell_or_class, a.expect, a.fingerprints, a.reason) == ("c", "(a (b))", judge.fingerprints(SHA), "why")
    assert judge.load_assertions(judge.HERE / "assertions.tsv") == []


SRC = b"codeunit 50100 P { trigger OnRun() begin Foo(1, 2); end; }"


def test_assertion_mutation_can_fail(al_parser):
    root = al_parser.parse(SRC).root_node
    good = judge.Assertion("c", "(call_expression function: (identifier) arguments: (argument_list (integer)))",
                           (), "")
    # the same, one field renamed
    bad = replace(good, expect=good.expect.replace("arguments:", "bogus:"))
    # and one with an element dropped from the middle of the order
    wrong_type = replace(good, expect="(call_expression (argument_list (string_literal)))")
    assert judge.check_assertion(root, SRC.decode(), good)
    assert not judge.check_assertion(root, SRC.decode(), bad)
    assert not judge.check_assertion(root, SRC.decode(), wrong_type)
