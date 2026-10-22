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
SCOPE = manifest.FAMILIES


def test_clean():
    assert manifest.check(SCOPE, [entry()], RECS, VERD) == []


def test_admitted_not_at_target():
    p = manifest.check(SCOPE, [entry()], RECS, {"c1": ("key-fields", "GAP")})
    assert len(p) == 1 and "admitted cell not at its target" in p[0]


def test_excluded_change_needs_rerecord():
    e = entry(disp="excluded", exp="GAP")
    assert manifest.check(SCOPE, [e], RECS, {"c1": ("key-fields", "CONSISTENT")})
    assert manifest.check(SCOPE, [entry(disp="excluded", exp="CONSISTENT")], RECS, {"c1": ("key-fields", "CONSISTENT")}) == []


def test_vector_mismatch():
    p = manifest.check(SCOPE, [entry(vec="X=0:A;X=1:R")], RECS, VERD)
    assert len(p) == 1 and p[0].startswith("vector")


def test_class_sampled_all_accepted_like_the_judge():
    r = [rec("c1", "X=0", flat=False), rec("c1", "X=1", ok=False, flat=False)]
    assert manifest.vector(r) == "X=0:A;X=1:A"


def test_missing_cell_of_candidate_family():
    v = dict(VERD, c2=("sorting", "GAP"), c3=("link-list", "GAP"))
    p = manifest.check(SCOPE, [entry()], RECS, v)
    assert p == ["missing\tc2\tcell of candidate family sorting not in the manifest"]


def test_pseudo_entry_not_checked():
    assert manifest.check(SCOPE, [entry(cid="route:x", vec="", exp="n/a")], [], {}) == []


def test_target_mixed_records_over_accept():
    r = [rec("c1", "X=0"), dict(rec("c1", "X=1", ok=False), control="typed", reject_class="syntax")]
    assert manifest.target(r) == "MIXED:X=0:CONSISTENT;X=1:REJECTED/syntax/over-accepts"


def test_verdict_str_keeps_consistent_detail():
    from tools.b7_audit.judge import Verdict
    assert manifest.verdict_str(Verdict("CONSISTENT", "assertion-closed: x")) == "CONSISTENT:assertion-closed: x"
    assert manifest.verdict_str(Verdict("CONSISTENT")) == "CONSISTENT"


def test_frozen_consistent_detail_swap_is_a_problem_but_admitted_ignores_it():
    cur = {"c1": ("key-fields", "CONSISTENT:assertion-closed: x")}
    assert manifest.check(SCOPE, [entry(disp="excluded", exp="CONSISTENT")], RECS, cur)
    assert manifest.check(SCOPE, [entry()], RECS, cur) == []


def test_identity_columns_checked():
    import dataclasses
    for ch in ({"family": "sorting"}, {"route_host": "z"}, {"placement": "q"}):
        p = manifest.check(SCOPE, [dataclasses.replace(entry(), **ch)], RECS, VERD)
        assert len(p) == 1 and p[0].startswith("identity"), ch


def test_admitted_expected_must_equal_target():
    p = manifest.check(SCOPE, [entry(exp="GAP")], RECS, {"c1": ("key-fields", "GAP")})
    assert any("target" in x for x in p)


def test_cardinality_vocabulary():
    assert manifest.CARDINALITIES == ("empty-interior", "optional-wrapper", "empty-syntax-rejected",
                                      "empty-semantic-rejected", "unknown")


def test_header_required(tmp_path):
    p = tmp_path / "m.tsv"
    p.write_text("c1\tx\n", encoding="utf-8")
    with pytest.raises(ValueError):
        manifest.load(p)
    manifest.dump(SCOPE, [entry()], p)
    assert manifest.load(p) == (SCOPE, [entry()])
    p.write_text("# families: key-fields\n" + HEAD.replace("\towner", "") + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        manifest.load(p)


# --- scoped manifests (B7b-3 spec 8.2) -------------------------------------------------------------------------
def _write(tmp_path, text):
    p = tmp_path / "m.tsv"
    p.write_text(text, encoding="utf-8")
    return p


def test_scope_header_mandatory(tmp_path):
    with pytest.raises(ValueError, match="families"):
        manifest.load(_write(tmp_path, HEAD + "\n"))
    with pytest.raises(ValueError, match="families"):   # must be the FIRST line
        manifest.load(_write(tmp_path, "# a comment\n# families: key-fields\n" + HEAD + "\n"))


def test_scope_header_cli_exit_2(tmp_path):
    from tools.b7_audit import __main__ as cli
    p = _write(tmp_path, HEAD + "\n")
    assert cli.main(["manifest", "--check", "--manifest", str(p)]) == 2


def test_row_outside_scope_is_a_problem():
    p = manifest.check(("sorting",), [entry()], RECS, VERD)
    assert any(x.startswith("scope\tc1") for x in p), p
    # an excluded row may pin a neighbouring cell of another family (the B7b-1 manifest's B13 seed)
    assert manifest.check(("sorting",), [entry(disp="excluded")], RECS, VERD) == []
    p = manifest.check(("sorting",), [entry(disp="deferred")], RECS, VERD)   # only `excluded` may
    assert any(x.startswith("scope	c1") for x in p), p


def test_unknown_family_in_header(tmp_path):
    with pytest.raises(ValueError, match="no-such-family"):
        manifest.load(_write(tmp_path, "# families: key-fields,no-such-family\n" + HEAD + "\n"))


@pytest.mark.parametrize("hdr", ["# families: key-fields, sorting", "# families: key-fields,key-fields",
                                 "# families: ", "# families: key-fields,"])
def test_header_must_round_trip(tmp_path, hdr):
    with pytest.raises(ValueError):
        manifest.load(_write(tmp_path, hdr + "\n" + HEAD + "\n"))


def test_header_round_trips(tmp_path):
    p = _write(tmp_path, "# families: statement-terminator,move-modification\n# note\n" + HEAD + "\n")
    scope, entries = manifest.load(p)
    assert scope == ("statement-terminator", "move-modification") and entries == []
    manifest.dump(scope, entries, p)
    assert manifest.load(p) == (scope, entries)
    assert p.read_text(encoding="utf-8").splitlines()[0] == "# families: statement-terminator,move-modification"


def test_missing_only_within_own_scope():
    v = dict(VERD, c2=("sorting", "GAP"), c3=("statement-terminator", "GAP"))
    assert manifest.check(("key-fields",), [entry()], RECS, v) == []
    p = manifest.check(("key-fields", "statement-terminator"), [entry()], RECS, v)
    assert p == ["missing\tc3\tcell of candidate family statement-terminator not in the manifest"]


def _excluded_changed():
    return entry(disp="excluded", exp="GAP", fam="move-modification"), {"c1": ("move-modification", "CONSISTENT")}


def test_transfer_exempts_only_a_passing_b7b3_cell():
    e, cur = _excluded_changed()
    scope = ("move-modification",)
    assert any(x.startswith("verdict\tc1") for x in manifest.check(scope, [e], RECS, cur))
    assert manifest.check(scope, [e], RECS, cur, transfer=frozenset({"c1"})) == []
    b3 = [entry(fam="move-modification")]                     # admitted, target CONSISTENT
    ok = manifest.check(scope, b3, RECS, cur)
    assert manifest.passing_transfer(frozenset({"c1"}), b3, ok) == frozenset({"c1"})
    assert manifest.passing_transfer(frozenset(), b3, ok) == frozenset()            # not in the transfer set
    assert manifest.passing_transfer(frozenset({"c1"}), [], []) == frozenset()     # not in the B7b-3 manifest
    bad = manifest.check(scope, b3, RECS, {"c1": ("move-modification", "GAP")})
    assert bad and manifest.passing_transfer(frozenset({"c1"}), b3, bad) == frozenset()   # not passing there


def test_transfer_still_checks_identity_vector_coverage():
    import dataclasses
    e, cur = _excluded_changed()
    scope, t = ("move-modification",), frozenset({"c1"})
    p = manifest.check(scope, [dataclasses.replace(e, route_host="z")], RECS, cur, transfer=t)
    assert [x.split("\t")[0] for x in p] == ["identity"]
    p = manifest.check(scope, [dataclasses.replace(e, frozen_vector="X=0:A;X=1:R")], RECS, cur, transfer=t)
    assert [x.split("\t")[0] for x in p] == ["vector"]
    p = manifest.check(scope, [e], RECS, dict(cur, c9=("move-modification", "GAP")), transfer=t)
    assert [x.split("\t")[:2] for x in p] == [["missing", "c9"]]


def test_transfer_constant_is_the_b7b1_move_cells_owned_by_b7b3():
    scope, entries = manifest.load(manifest.MANIFEST)
    want = {e.cell_id for e in entries if e.family == "move-modification" and e.owner == "B7b-3"}
    assert manifest.TRANSFER_B7B3 == want and len(want) == 72
    assert all(e.disposition == "excluded" for e in entries if e.cell_id in want)


def _oentry(eo="X=0:pass,X=1:lowering:one-reading"):
    import dataclasses
    return dataclasses.replace(entry(), expected_oracle=eo)


def test_expected_oracle_mismatch_is_a_problem():
    def oracle(cid):
        return {"X=0": "pass", "X=1": "lowering:one-reading"}
    assert manifest.check(SCOPE, [_oentry()], RECS, VERD, oracle=oracle) == []
    p = manifest.check(SCOPE, [_oentry()], RECS, VERD, oracle=lambda cid: {"X=0": "discrepancy", "X=1": "lowering:one-reading"})
    assert len(p) == 1 and p[0].startswith("oracle\tc1\tX=0"), p
    assert manifest.check(SCOPE, [_oentry()], RECS, VERD) == []      # no oracle given: the run-based check is off


def test_expected_oracle_covers_exactly_the_accepted_configurations():
    p = manifest.check(SCOPE, [_oentry("X=0:pass")], RECS, VERD)
    assert len(p) == 1 and p[0].startswith("oracle-cover\tc1"), p


def test_oracle_status_string():
    from tools.config_oracle.runner import Record
    assert manifest.oracle_status(Record("i", "X=0", "pass", [])) == "pass"
    assert manifest.oracle_status(Record("i", "X=0", "cannot-validate",
                                         ["lowering:one-reading:one-reading at x@12"])) == "lowering:one-reading"
    assert manifest.oracle_status(Record("i", "X=0", "discrepancy", ["a"])) == "discrepancy"


@pytest.mark.parametrize("bad", ["X=0", "X=0:", "X=0:pass,", "X=0:pass;X=1:pass", "X=2:pass", "X=0:Pass",
                                 "X=0:pass,X=0:pass", ":pass"])
def test_malformed_expected_oracle_is_a_load_error(tmp_path, bad):
    row = "\t".join(["c1", "key-fields", "h", "p", "admitted", "", "o", "unknown", "X=0:A;X=1:A", "CONSISTENT", bad])
    with pytest.raises(ValueError, match="expected_oracle value"):
        manifest.load(_write(tmp_path, f"# families: key-fields\n{HEAD}\texpected_oracle\n{row}\n"))


def test_expected_oracle_parses_multi_symbol_configs(tmp_path):
    v = "TPL2=0,X=0:pass,TPL2=0,X=1:lowering:unsupported-type"
    assert manifest.parse_oracle(v) == {"TPL2=0,X=0": "pass", "TPL2=0,X=1": "lowering:unsupported-type"}
    row = "\t".join(["c1", "key-fields", "h", "p", "admitted", "", "o", "unknown", "X=0:A;X=1:A", "CONSISTENT", v])
    p = _write(tmp_path, f"# families: key-fields\n{HEAD}\texpected_oracle\n{row}\n")
    scope, entries = manifest.load(p)
    assert entries[0].expected_oracle == v
    manifest.dump(scope, entries, p)
    assert manifest.load(p) == (scope, entries)


def test_oracle_missing_source_is_a_problem():
    p = manifest.check(SCOPE, [_oentry()], RECS, VERD, oracle={}.get)
    assert p and p[0] == "oracle\tc1\tno source: the cell is not in evidence.universe()", p


def _b7b3_file(tmp_path, cid, eo):
    row = "\t".join([cid, "move-modification", "h", "p", "admitted", "", "B7b-3", "unknown", "X=0:A;X=1:A",
                     "CONSISTENT", eo])
    p = tmp_path / "b3.tsv"
    p.write_text(f"# families: move-modification\n{HEAD}\texpected_oracle\n{row}\n", encoding="utf-8")
    return p


def test_transfer_for_cli_wiring(tmp_path):
    import dataclasses
    cid = sorted(manifest.TRANSFER_B7B3)[0]
    recs = [dict(r, cell=cid) for r in RECS]
    verd = {cid: ("move-modification", "CONSISTENT")}
    b1 = tmp_path / "b1.tsv"
    excl = entry(cid=cid, disp="excluded", exp="GAP", fam="move-modification")
    b3 = _b7b3_file(tmp_path, cid, "X=0:pass,X=1:pass")
    ok = lambda ids: {i: {"X=0": "pass", "X=1": "pass"} for i in ids}
    assert manifest.transfer_for(b1, [excl], recs, verd, b3, ok) == frozenset({cid})
    # the B7b-3 oracle expectation is part of "passing there"
    bad = lambda ids: {i: {"X=0": "discrepancy", "X=1": "pass"} for i in ids}
    assert manifest.transfer_for(b1, [excl], recs, verd, b3, bad) == frozenset()
    # only non-admitted transfer rows are candidates; a non-transfer id never is
    assert manifest.transfer_for(b1, [dataclasses.replace(excl, disposition="admitted")], recs, verd, b3, ok) == frozenset()
    assert manifest.transfer_for(b1, [dataclasses.replace(excl, cell_id="c1")], RECS, VERD, b3, ok) == frozenset()
    # the B7b-3 manifest itself never exempts, and a missing B7b-3 file exempts nothing
    assert manifest.transfer_for(b3, [excl], recs, verd, b3, ok) == frozenset()
    assert manifest.transfer_for(b1, [excl], recs, verd, tmp_path / "none.tsv", ok) == frozenset()


# --- B7b-2 (spec 2026-10-20 section 8.4): final mode, require-oracle, rerecord -----------------------------------
def _owned(owner, disp="deferred", exp="CONSISTENT"):
    import dataclasses
    return dataclasses.replace(entry(disp=disp, exp=exp), owner=owner)


def test_final_rejects_phase_owner():
    e = _owned("B7b-2/B")
    assert manifest.check(SCOPE, [e], RECS, VERD) == []                      # not final: a phase owner is fine
    p = manifest.check(SCOPE, [e], RECS, VERD, final_owner_prefix="B7b-2/")
    assert len(p) == 1 and p[0].startswith("final\tc1"), p
    # the finished owner and other owners pass the final check
    assert manifest.check(SCOPE, [_owned("B7b-2", disp="admitted")], RECS, VERD, final_owner_prefix="B7b-2/") == []
    assert manifest.check(SCOPE, [_owned("B7b-1h", disp="excluded")], RECS, VERD, final_owner_prefix="B7b-2/") == []
    # a pseudo route entry is no exception
    p = manifest.check(SCOPE, [manifest.Entry("route:x", "key-fields", "h", "p", "deferred", "why", "B7b-2/C",
                                              "unknown", "", "n/a")], [], {}, final_owner_prefix="B7b-2/")
    assert [x.split("\t")[:2] for x in p] == [["final", "route:x"]]


def test_require_oracle_on_admitted():
    import dataclasses
    p = manifest.check(SCOPE, [entry()], RECS, VERD, require_oracle=True)
    assert len(p) == 1 and p[0].startswith("require-oracle\tc1"), p
    assert manifest.check(SCOPE, [entry()], RECS, VERD) == []                 # off by default
    assert manifest.check(SCOPE, [_oentry()], RECS, VERD, require_oracle=True) == []
    # only admitted rows need it
    assert manifest.check(SCOPE, [dataclasses.replace(entry(disp="deferred"))], RECS, VERD, require_oracle=True) == []


_PREFACE = "# a reviewed preface line\n"


def _rr_file(tmp_path, rows, oracle_col=True):
    head = HEAD + ("\texpected_oracle" if oracle_col else "")
    body = "".join("\t".join(r) + "\n" for r in rows)
    p = tmp_path / "other.tsv"
    p.write_text(f"# families: key-fields\n{_PREFACE}{head}\n{body}", encoding="utf-8")
    return p


def _row(cid, disp="deferred", exp="GAP", vec="X=0:A;X=1:A", eo="X=0:discrepancy,X=1:discrepancy"):
    return [cid, "key-fields", "h", "p", disp, "" if disp == "admitted" else "why", "C1", "unknown", vec, exp, eo]


def _rr_recs(*cids):
    return [rec(c, cfg) for c in cids for cfg in ("X=0", "X=1")]


def test_rerecord_changes_only_named_cells(tmp_path):
    p = _rr_file(tmp_path, [_row("c1"), _row("c2")])
    before = p.read_text(encoding="utf-8").splitlines()
    verd = {"c1": ("key-fields", "CONSISTENT"), "c2": ("key-fields", "CONSISTENT")}
    orc = {"c1": {"X=0": "pass", "X=1": "pass"}, "c2": {"X=0": "pass", "X=1": "pass"}}.get
    changed = manifest.rerecord(p, ["c1"], _rr_recs("c1", "c2"), verd, oracle=orc)
    after = p.read_text(encoding="utf-8").splitlines()
    assert [l.split("\t")[0] for l in changed] == ["c1", "c1"], changed
    assert any("GAP -> CONSISTENT" in l for l in changed) and any("X=0:pass,X=1:pass" in l for l in changed)
    diff = [(a, b) for a, b in zip(before, after) if a != b]
    assert len(before) == len(after) and len(diff) == 1 and diff[0][0].startswith("c1\t"), diff
    assert after[1] == _PREFACE.rstrip("\n")                                   # comments survive
    scope, entries = manifest.load(p)
    c1 = next(e for e in entries if e.cell_id == "c1")
    assert (c1.expected_verdict, c1.expected_oracle) == ("CONSISTENT", "X=0:pass,X=1:pass")
    p2 = manifest.check(scope, entries, _rr_recs("c1", "c2"), verd, oracle=orc)
    assert {x.split("\t")[1] for x in p2} == {"c2"} and len(p2) == 3, p2       # c1 is clean, c2 still flagged
    # an unchanged cell is named and reported as nothing
    assert manifest.rerecord(p, ["c1"], _rr_recs("c1", "c2"), verd, oracle=orc) == []


def test_rerecord_keeps_identity_and_vector(tmp_path):
    p = _rr_file(tmp_path, [_row("c1", vec="X=0:A;X=1:R")])                    # frozen vector disagrees with evidence
    verd = {"c1": ("key-fields", "CONSISTENT")}
    manifest.rerecord(p, ["c1"], _rr_recs("c1"), verd)                         # no oracle: expected_oracle kept
    scope, [e] = manifest.load(p)
    assert (e.family, e.route_host, e.placement, e.disposition, e.reason, e.owner, e.cardinality, e.frozen_vector,
            e.expected_oracle) == ("key-fields", "h", "p", "deferred", "why", "C1", "unknown", "X=0:A;X=1:R",
                                   "X=0:discrepancy,X=1:discrepancy")
    assert e.expected_verdict == "CONSISTENT"
    p2 = manifest.check(scope, [e], _rr_recs("c1"), verd)
    assert [x.split("\t")[0] for x in p2] == ["vector"], p2                   # the vector check still bites


def test_rerecord_admitted_keeps_target_updates_oracle(tmp_path):
    p = _rr_file(tmp_path, [_row("c1", disp="admitted", exp="CONSISTENT")])
    verd = {"c1": ("key-fields", "CONSISTENT:assertion-closed: x")}
    changed = manifest.rerecord(p, ["c1"], _rr_recs("c1"), verd, oracle={"c1": {"X=0": "pass", "X=1": "pass"}}.get)
    _, [e] = manifest.load(p)
    assert e.expected_verdict == "CONSISTENT" and e.expected_oracle == "X=0:pass,X=1:pass"
    assert len(changed) == 1 and "expected_oracle" in changed[0]


def test_rerecord_refuses_unknown_cell(tmp_path):
    p = _rr_file(tmp_path, [_row("c1")])
    text = p.read_text(encoding="utf-8")
    verd = {"c1": ("key-fields", "CONSISTENT")}
    with pytest.raises(ValueError, match="c9"):
        manifest.rerecord(p, ["c1", "c9"], _rr_recs("c1"), verd)              # not a row of the manifest
    with pytest.raises(ValueError, match="c1"):
        manifest.rerecord(p, ["c1"], [], {})                                    # no current evidence for it
    with pytest.raises(ValueError, match="c1"):
        manifest.rerecord(p, ["c1"], _rr_recs("c1"), verd, oracle={}.get)      # oracle has no source for it
    assert p.read_text(encoding="utf-8") == text                               # nothing written on refusal


def _admit_row(cid, owner="B7b-2/B"):
    r = _row(cid)
    r[6] = owner
    return r


def test_admit_admits_only_owned_rows_at_target(tmp_path):
    """Fix round 1 (Task 9 review): each guard keeps exactly its own row, and every row reaching a guard passes every
    earlier one (c2 has an all-pass oracle, so only the verdict guard keeps it)."""
    done = _row("c8", disp="admitted", exp="GAP")                               # already admitted, by phase B
    done[6] = "B7b-2/B"
    stale = _row("c9", vec="X=0:A;X=1:R")                                      # c9: frozen vector != evidence
    stale[6] = "B7b-2/B"
    p = _rr_file(tmp_path, [_admit_row("c1"), _admit_row("c2"), _admit_row("c3", owner="B7b-2/C"),
                            _admit_row("c4"), _admit_row("c5"), _admit_row("c6"), _admit_row("c7"), done,
                            _admit_row("route:r1"), stale])
    before = p.read_text(encoding="utf-8").splitlines()
    cells = ("c1", "c2", "c3", "c4", "c5", "c6", "c8", "route:r1", "c9")      # c7: no evidence at all
    verd = {c: ("key-fields", "CONSISTENT") for c in cells}
    verd["c2"] = ("key-fields", "UNCHECKED")                                     # not at its target
    verd["c4"] = ("key-fields", "CONSISTENT:assertion-closed: lowering:unsupported-type")
    allpass = {"X=0": "pass", "X=1": "pass"}
    orc = {"c1": allpass, "c2": allpass, "c3": allpass, "c4": {"X=0": "pass", "X=1": "lowering:unsupported-type"},
           "c5": {"X=0": "pass", "X=1": "discrepancy"}, "c7": allpass, "c8": allpass, "route:r1": allpass,
           "c9": allpass}.get                                                    # c6: the oracle has no source
    changed, kept = manifest.admit(p, "B7b-2/B", _rr_recs(*cells), verd, orc)
    scope, entries = manifest.load(p)
    by = {e.cell_id: e for e in entries}
    assert (by["c1"].disposition, by["c1"].owner, by["c1"].reason, by["c1"].expected_verdict,
            by["c1"].expected_oracle) == ("admitted", "B7b-2", "", "CONSISTENT", "X=0:pass,X=1:pass")
    assert (by["c4"].disposition, by["c4"].reason, by["c4"].expected_oracle) == (
        "admitted", "C1: the split host's oracle refusal, assertion-closed in 1 configuration(s)",
        "X=0:pass,X=1:lowering:unsupported-type")
    assert {k.split("\t")[0]: k.split("\t")[1] for k in kept} == {
        "c2": "verdict UNCHECKED is not the target CONSISTENT",
        "c5": "oracle outcome discrepancy is neither pass nor a closed refusal",
        "c6": "the oracle has no source",
        "c7": "no current evidence",
        "c9": "identity or vector ('key-fields', 'h', 'p', 'X=0:A;X=1:R') != evidence "
              "('key-fields', 'h', 'p', 'X=0:A;X=1:A')"}, kept
    assert {c.split("\t")[0] for c in changed} == {"c1", "c4"}                  # not c3 (owner), c8, route:r1
    after = p.read_text(encoding="utf-8").splitlines()
    assert [a for a, b in zip(before, after) if a != b] == [before[3], before[6]]   # only the c1 and c4 lines
    assert manifest.check(scope, [by["c1"], by["c4"]], _rr_recs("c1", "c4"), {c: verd[c] for c in ("c1", "c4")},
                          oracle=orc, require_oracle=True) == []                 # admitted rows check clean
    assert manifest.admit(p, "B7b-2/B", _rr_recs(*cells), verd, orc)[0] == []  # idempotent


def test_admit_mixed_target_and_refusals(tmp_path):
    mixed = _row("c1", vec="X=0:R;X=1:A")                                      # alc rejects X=0
    mixed[6] = "X"
    p = _rr_file(tmp_path, [mixed, _admit_row("c2", owner="X")])
    recs = [{**rec("c1", "X=0", ok=False), "reject_class": None, "control": "none"}, rec("c1", "X=1"),
            rec("c2", "X=0"), rec("c2", "X=1")]
    verd = {"c1": ("key-fields", "MIXED:X=0:REJECTED/unverified/over-accepts;X=1:CONSISTENT"),
            "c2": ("key-fields", "CONSISTENT")}
    # c1's alc-REJECTED X=0 is cannot-validate: only the accepted configurations are judged (and recorded)
    orc = {"c1": {"X=0": "cannot-validate", "X=1": "pass"}, "c2": {"X=0": "lowering:one-reading", "X=1": "pass"}}.get
    changed, kept = manifest.admit(p, "X", recs, verd, orc, new_owner="Y")
    _, entries = manifest.load(p)
    by = {e.cell_id: e for e in entries}
    assert kept == [] and by["c1"].owner == by["c2"].owner == "Y"
    assert by["c1"].expected_verdict == manifest.target([r for r in recs if r["cell"] == "c1"])
    assert by["c1"].expected_oracle == "X=1:pass"                                # only the alc-accepted configuration
    assert by["c2"].reason == "B12 host limitation (one-reading), assertion-closed in 1 configuration(s)"


def test_admit_refuses_a_manifest_without_oracle_column(tmp_path):
    p = _rr_file(tmp_path, [_admit_row("c1")[:-1]], oracle_col=False)
    text = p.read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="expected_oracle"):
        manifest.admit(p, "B7b-2/B", _rr_recs("c1"), {"c1": ("key-fields", "CONSISTENT")}, {}.get)
    assert p.read_text(encoding="utf-8") == text


def test_cli_admit_flags():
    from tools.b7_audit import __main__ as cli
    a = cli.parser().parse_args(["manifest", "--admit", "--manifest", "m.tsv", "--owner", "B7b-2/B"])
    assert a.admit and a.owner == "B7b-2/B" and a.new_owner == "B7b-2"
    assert cli.main(["manifest", "--admit", "--manifest", "m.tsv"]) == 2         # --owner is required


def test_cli_final_and_rerecord_flags():
    from tools.b7_audit import __main__ as cli
    a = cli.parser().parse_args(["manifest", "--check", "--manifest", "m.tsv", "--final", "B7b-2/",
                                 "--require-oracle"])
    assert (a.final, a.require_oracle, a.check) == ("B7b-2/", True, True)
    a = cli.parser().parse_args(["manifest", "--rerecord", "--manifest", "m.tsv", "--cells", "a,b"])
    assert a.rerecord and a.cells == "a,b"
    with pytest.raises(SystemExit):
        cli.parser().parse_args(["manifest", "--check", "--rerecord", "--manifest", "m.tsv"])
    assert cli.main(["manifest", "--rerecord", "--manifest", "m.tsv"]) == 2     # --cells is required
