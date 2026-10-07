import pytest

from tools.b7_audit import manifest

HEAD = "\t".join(manifest.HEAD)


def rec(cell, config, ok=True, flat=True):
    return {"cell": cell, "config": config, "intended_valid": ok, "host": "h", "placement": "p",
            "alc": "measured" if flat else "class-sampled",
            "alc_flat": {"verdict": "ACCEPT" if ok else "REJECT"} if flat else None}


def entry(cid="c1", disp="admitted", vec="X=0:A;X=1:A", exp="CONSISTENT", fam="key-fields"):
    return manifest.Entry(cid, fam, "h", "p", disp, "" if disp == "admitted" else "why", "o", "unknown", vec, exp)


RECS = [rec("c1", "X=0"), rec("c1", "X=1")]
VERD = {"c1": ("key-fields", "CONSISTENT")}


def test_clean():
    assert manifest.check([entry()], RECS, VERD) == []


def test_admitted_not_at_target():
    p = manifest.check([entry()], RECS, {"c1": ("key-fields", "GAP")})
    assert len(p) == 1 and "admitted cell not at its target" in p[0]


def test_excluded_change_needs_rerecord():
    e = entry(disp="excluded", exp="GAP")
    assert manifest.check([e], RECS, {"c1": ("key-fields", "CONSISTENT")})
    assert manifest.check([entry(disp="excluded", exp="CONSISTENT")], RECS, {"c1": ("key-fields", "CONSISTENT")}) == []


def test_vector_mismatch():
    p = manifest.check([entry(vec="X=0:A;X=1:R")], RECS, VERD)
    assert len(p) == 1 and p[0].startswith("vector")


def test_class_sampled_all_accepted_like_the_judge():
    r = [rec("c1", "X=0", flat=False), rec("c1", "X=1", ok=False, flat=False)]
    assert manifest.vector(r) == "X=0:A;X=1:A"


def test_missing_cell_of_candidate_family():
    v = dict(VERD, c2=("sorting", "GAP"), c3=("link-list", "GAP"))
    p = manifest.check([entry()], RECS, v)
    assert p == ["missing\tc2\tcell of candidate family sorting not in the manifest"]


def test_pseudo_entry_not_checked():
    assert manifest.check([entry(cid="route:x", vec="", exp="n/a")], [], {}) == []


def test_target_mixed_records_over_accept():
    r = [rec("c1", "X=0"), dict(rec("c1", "X=1", ok=False), control="typed", reject_class="syntax")]
    assert manifest.target(r) == "MIXED:X=0:CONSISTENT;X=1:REJECTED/syntax/over-accepts"


def test_verdict_str_keeps_consistent_detail():
    from tools.b7_audit.judge import Verdict
    assert manifest.verdict_str(Verdict("CONSISTENT", "assertion-closed: x")) == "CONSISTENT:assertion-closed: x"
    assert manifest.verdict_str(Verdict("CONSISTENT")) == "CONSISTENT"


def test_frozen_consistent_detail_swap_is_a_problem_but_admitted_ignores_it():
    cur = {"c1": ("key-fields", "CONSISTENT:assertion-closed: x")}
    assert manifest.check([entry(disp="excluded", exp="CONSISTENT")], RECS, cur)
    assert manifest.check([entry()], RECS, cur) == []


def test_identity_columns_checked():
    import dataclasses
    for ch in ({"family": "sorting"}, {"route_host": "z"}, {"placement": "q"}):
        p = manifest.check([dataclasses.replace(entry(), **ch)], RECS, VERD)
        assert len(p) == 1 and p[0].startswith("identity"), ch


def test_admitted_expected_must_equal_target():
    p = manifest.check([entry(exp="GAP")], RECS, {"c1": ("key-fields", "GAP")})
    assert any("target" in x for x in p)


def test_cardinality_vocabulary():
    assert manifest.CARDINALITIES == ("empty-interior", "optional-wrapper", "empty-syntax-rejected",
                                      "empty-semantic-rejected", "unknown")


def test_header_required(tmp_path):
    p = tmp_path / "m.tsv"
    p.write_text("c1\tx\n", encoding="utf-8")
    with pytest.raises(ValueError):
        manifest.load(p)
    manifest.dump([entry()], p)
    assert manifest.load(p) == [entry()]
    p.write_text(HEAD.replace("\towner", "") + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        manifest.load(p)
