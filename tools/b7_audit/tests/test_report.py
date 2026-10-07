import hashlib
import random
from pathlib import Path

from tools.b7_audit import evidence, judge, registry, report
from tools.b7_audit.registry import Row

SHA = "c" * 64


def cell(cid, host, placement="sep-after", alc="ACCEPT", err=False, oracle="pass", key=None, reject_class=None):
    """Real-shape evidence records of one cell (one configuration)."""
    codes = {"syntax": ["AL0104"], "semantic": ["AL0175"]}.get(reject_class, [])
    return [{"cell": cid, "key": key or cid.split("@")[0], "host": host, "placement": placement,
             "config": "-", "source_sha256": SHA, "intended_valid": alc == "ACCEPT", "control": "typed",
             "parser_has_error": err, "error_in_hole": err, "oracle": {"status": oracle, "reasons": []},
             "alc": "measured", "alc_split": None,
             "alc_flat": {"verdict": alc, "codes": codes if alc == "REJECT" else []},
             "alc_control": {"verdict": "ACCEPT", "codes": []}, "reject_class": reject_class}]


def row(key, host, family, role="list-separator", reason=""):
    return Row(key, host, role, family, "x ⟨HOLE⟩", "", reason, "p")


HEADER = {"alc": {"version": "fake 1"}, "runtime": "15.0", "corpora": {},
          "production_shapes": {"shapes": [
              {"host": "hA", "class": "sep-after", "count": 5},
              {"host": "hB", "class": "sep-after", "count": 50},
              {"host": "hB", "class": "terminated-unit", "count": 9000},
              {"host": "hC", "class": "sep-after", "count": 7}]}}
ROWS = [row("k1", "hA", "fa"), row("k2", "hB", "fb"), row("k3", "hC", "fc"), row("k4", "hD", "fd"),
        row("q", "hQ", "fq", role="qualifier", reason="not a separator")]


def own_tree(records):
    """A stand-in for the cell's own split tree: its group is the evidence host, its class the placement shape."""
    m = {r["cell"]: (r["host"], report.shape_id(r["placement"])) for r in records}
    return lambda cid, sha: m.get(cid)


def build(records, rows=ROWS, deps=None, classify=None):
    a = report.analyse(records, HEADER, rows, classify=classify or own_tree(records))
    return a, report.render(a, HEADER)


def two_configs(cid, host, **kw):
    r = cell(cid, host, **kw)[0]
    return [r, {**r, "config": "X", "oracle": {"status": "pass", "reasons": []}}]


def test_report_deterministic(tmp_path):
    recs = cell("k1@hA#p1", "hA", err=True) + cell("k2@hB#p1", "hB", oracle="discrepancy") + \
        two_configs("k3@hC#p2", "hC", oracle="cannot-validate") + two_configs("k4@hD#p1", "hD") + \
        two_configs("k1@hA#p9", "hA", placement="p9", err=True)
    out = []
    for i in range(6):
        shuffled = recs[:]
        random.Random(i).shuffle(shuffled)
        out.append(report.render(report.analyse(shuffled, HEADER, ROWS), HEADER))
        p = tmp_path / f"e{i}.jsonl"
        evidence.write(shuffled, HEADER, p)
        q = tmp_path / f"m{i}.md"
        report.write(q, evidence_path=p, registry_path=REG)
        out.append(q.read_text(encoding="utf-8"))
    assert len(set(out[::2])) == 1 and len(set(out[1::2])) == 1 and chr(13) not in out[0]


def test_families_dedupe():
    recs = cell("k1@hA#p1", "hA", err=True) + cell("k1@hA#p2", "hA", placement="trail", err=True)
    a, _ = build(recs)
    assert list(a["families"]) == [("fa", "GAP")]
    assert a["families"][("fa", "GAP")]["cells"] == ["k1@hA#p1", "k1@hA#p2"]
    assert a["families"][("fa", "GAP")]["sites"] == 5


def test_unchecked_listed_separately():
    recs = cell("k3@hC#p1", "hC", oracle="cannot-validate")
    a, text = build(recs)
    assert a["families"] == {} and report.rank(a["families"]) == []
    ranked = text.split("## Ranked fix list")[1].split("## UNCHECKED")[0]
    assert "k3@hC#p1" not in ranked and "k3@hC#p1" in text.split("## UNCHECKED")[1]


def test_rank_order():
    recs = cell("k1@hA#p1", "hA", err=True) + cell("k1@hA#p2", "hA", placement="trail", err=True) + \
        cell("k2@hB#p1", "hB", err=True) + cell("k3@hC#p1", "hC", oracle="discrepancy")
    a, _ = build(recs)
    assert report.rank(a["families"]) == [("fc", "SILENT"), ("fb", "GAP"), ("fa", "GAP")]   # silent first; 50 > 5 sites
    deps = {"fb": ("fa",)}
    assert report.rank(a["families"], deps) == [("fc", "SILENT"), ("fa", "GAP"), ("fb", "GAP")]


def test_terminated_unit_unweighted_and_vector_mismatch():
    a, text = build(cell("k2@hB#p1", "hB", err=True))
    assert a["families"][("fb", "GAP")]["sites"] == 50 and a["families"][("fb", "GAP")]["unweighted"] == 9000
    recs = cell("k2@hB#p1", "hB", alc="REJECT", reject_class="syntax", err=True)
    recs[0]["intended_valid"] = True          # the generator expected alc to accept
    a, text = build(recs)
    assert "k2@hB#p1" in text.split("## Generator imprecisions")[1].split("## Families")[0]


def test_qualifier_not_probed_and_seed_and_blocked():
    seed = cell("seed:value-runs__x", "hA", key="seed:value-runs__x", placement="seed:value-runs__x", err=True)
    a, text = build(seed + cell("k1@hA#p1", "hA", oracle="discrepancy"))
    assert "not a separator" in text.split("## Not probed")[1]
    assert a["families"][("fa", "GAP")]["owner"] == "B12"
    assert "seed:value-runs__x" in text.split("## Seeds")[1].split("## Generator")[0]
    link = [row("kl", "hL", "link-list")]
    a = report.analyse(cell("kl@hL#sep-before+comments", "hL", placement="sep-before+comments", key="kl", err=True),
                       HEADER, link)
    assert list(a["families"]) == [("link-list-comma-leading", "GAP")]
    assert report.rank(a["families"]) == [("link-list-comma-leading", "GAP")]
    a = report.analyse(cell("kl@hL#holes-lead", "hL", placement="holes-lead", key="kl", err=True), HEADER, link)
    assert list(a["families"]) == [("link-list-comma-leading", "GAP")]
    for p in ("lead-optional", "sep-after", "first-replace+not", "holes-trail", "holes-mid"):
        a = report.analyse(cell(f"kl@hL#{p}", "hL", placement=p, key="kl", err=True), HEADER, link)
        assert list(a["families"]) == [("link-list", "GAP")], p


def test_external_dependency_sorts_to_tier_end():
    recs = cell("k1@hA#p1", "hA", err=True) + cell("k2@hB#p1", "hB", err=True)
    a = report.analyse(recs, HEADER, ROWS, classify=own_tree(recs))
    assert report.rank(a["families"]) == [("fb", "GAP"), ("fa", "GAP")]                      # sites 50 > 5
    assert report.rank(a["families"], {"fb": ("elsewhere",)}) == [("fa", "GAP"), ("fb", "GAP")]


REG = Path(__file__).parent / "empty-registry.tsv"


def test_assertion_closes_and_fails_cell(al_parser, tmp_path):
    src = b"codeunit 50100 P { trigger OnRun() begin Foo(1); end; }"
    sha = hashlib.sha256(src).hexdigest()
    recs = cell("k1@hA#p1", "hA", oracle="cannot-validate")
    recs[0]["source_sha256"] = sha
    recs[0]["oracle"]["reasons"] = ["one-reading"]
    ev = tmp_path / "e.jsonl"
    evidence.write(recs, HEADER, ev)
    reg = tmp_path / "r.tsv"
    reg.write_text(registry.HEADER + "\nk1\thA\tlist-separator\tfa\tx ⟨HOLE⟩\t\t\tp\n", encoding="utf-8")

    def asr(expect, fp=None):
        p = tmp_path / "a.tsv"
        fp = fp or ",".join(judge.fingerprints(sha))
        p.write_text(f"cell_or_class\texpect\tfingerprints\treason\tholds\nk1@hA#p1\t{expect}\t{fp}\tr\ttrue\n",
                     encoding="utf-8")
        return p

    src_map = {"k1@hA#p1": src}
    ok = report.build(ev, reg, asr("(call_expression function: (identifier))"), sources=src_map, parser=al_parser)
    assert "| CONSISTENT | C | 1 |" in ok
    bad = report.build(ev, reg, asr("(call_expression function: (bogus))"), sources=src_map, parser=al_parser)
    assert "| SILENT | S | 1 |" in bad
    stale = report.build(ev, reg, asr("(x)", ",".join(["0" * 64] * 4)), sources={}, parser=al_parser)
    assert "| UNCHECKED | U | 1 |" in stale


def test_assertion_needs_the_measured_source(al_parser, tmp_path):
    src = b"codeunit 50100 P { trigger OnRun() begin Foo(1); end; }"
    sha = hashlib.sha256(src).hexdigest()
    recs = cell("k1@hA#p1", "hA", oracle="cannot-validate")
    recs[0]["source_sha256"] = sha
    ev = tmp_path / "e.jsonl"
    evidence.write(recs, HEADER, ev)
    reg = tmp_path / "r.tsv"
    reg.write_text(registry.HEADER + "\nk1\thA\tlist-separator\tfa\tx \u27e8HOLE\u27e9\t\t\tp\n", encoding="utf-8")
    asr = tmp_path / "a.tsv"
    asr.write_text("cell_or_class\texpect\tfingerprints\treason\tholds\nk1@hA#p1\t(call_expression)\t"
                   + ",".join(judge.fingerprints(sha)) + "\tr\ttrue\n", encoding="utf-8")
    for srcs, why in (({"k1@hA#p1": src + b" "}, "source changed since evidence"),
                      ({}, "not in the regenerated universe")):
        text = report.build(ev, reg, asr, sources=srcs, parser=al_parser)
        assert "| UNCHECKED | U | 1 |" in text and why in text.split("## UNCHECKED")[1]


def test_groups_per_family_base_placement_kind():
    def c(i, fam, pl, kind):
        return {"id": i, "family": fam, "placement": pl, "kind": kind}
    cells = [c("b", "f", "sep-after+comments", "GAP"), c("a", "f", "sep-after@X", "GAP"),
             c("z", "f", "sep-after", "SILENT"), c("y", "g", "trail", None),
             c("d", "f", "suffix/xor+not", "GAP"), c("c", "f", "suffix/arithmetic", "GAP")]
    assert report.groups(cells) == {("f", "sep-after", "GAP"): ["a", "b"], ("f", "sep-after", "SILENT"): ["z"],
                                    ("f", "suffix", "GAP"): ["c", "d"]}
    assert report.slug("f", "seed:x:y", "GAP") == "f__seed-x-y__gap"
    assert report.witness("f", "x", "SILENT").endswith("test_silent.py")


def test_sites_count_only_matching_shapes():
    """A family's sites are the production (group type, class) counts matching the (group type, class) its defective
    cells' OWN split trees give (report.cell_shape): hB's 50 sep-after sites count for a cell whose group is an hB
    sep-after, not for an hB trail; the group type, not the registry host, is the key."""
    recs = cell("k2@hB#p", "hB", err=True)
    for got, sites in ((("hB", "sep-after"), 50), (("hB", "trail"), 0), (("hA", "sep-after"), 5)):
        a, _ = build(recs, classify=lambda cid, sha: got)
        assert a["families"][("fb", "GAP")]["sites"] == sites, got
    assert "| fb | GAP | 1 | hB | 50 | hB/sep-after | 9000 |" in build(cell("k2@hB#x", "hB", err=True))[1]


def test_unclassified_cell_is_listed_not_zeroed():
    """A defective cell whose own tree gives no class is named in the families section's unclassified line."""
    recs = cell("k2@hB#p", "hB", err=True) + cell("k1@hA#p", "hA", oracle="discrepancy")
    a, text = build(recs, classify=lambda cid, sha: None if cid.startswith("k2") else ("hA", "sep-after"))
    assert a["families"][("fb", "GAP")]["sites"] == 0 and a["families"][("fb", "GAP")]["unclassified"] == ["k2@hB#p"]
    fams = text.split("## Families")[1].split("## Defect groups")[0]
    assert "Unclassified defective cells: 1" in fams and "| fb | GAP | 1 | no class 1 | k2@hB#p |" in fams
    assert "k1@hA#p" not in fams.split("Unclassified defective cells")[1]


def test_cell_shape_reads_the_cells_own_tree(al_parser):
    """The B7a reviewer's counterexample: the placement `1: #if X Bar #else Bar #endif ;` in a case branch is a
    preproc_conditional_statement group whose previous sibling is the branch's `:`, which seeds.classify (the
    production walk's classifier) calls trail; the old placement table could not say so."""
    cid = "occ:call_statement:0.1@case_branch#first-replace"
    e = next(x for x in evidence.universe() if x.cell.id == cid)
    src = e.cell.source.encode("utf-8")
    assert report.cell_shape(al_parser.parse(src).root_node, src, e.cell.hole) == \
        ("preproc_conditional_statement", "trail")
    plain = b"codeunit 50100 P { trigger OnRun() begin Foo(1); end; }"
    assert report.cell_shape(al_parser.parse(plain).root_node, plain, (0, len(plain))) is None


def test_cell_shape_refuses_an_error_recovered_tree(al_parser):
    """Controller ruling (B7b-0 fix round 1): a split tree with has_error is unclassified, reason
    `error-recovered tree`, even where the group at the placement offset is itself clean."""
    clean = b"codeunit 50100 P\n{\n    trigger OnRun()\n    begin\n        Foo(1)\n#if X\n        ;\n#endif\n    end;\n}\n"
    broken = clean.replace(b"    end;\n}", b"        Foo(1 +;\n    end;\n}")
    assert broken != clean
    assert report.cell_shape(al_parser.parse(clean).root_node, clean) == ("preproc_conditional_statement", "other")
    root = al_parser.parse(broken).root_node
    assert root.has_error
    assert report.cell_shape(root, broken) == report.ERROR_RECOVERED == "error-recovered tree"


def test_unclassified_reasons_are_shown():
    recs = cell("k2@hB#p", "hB", err=True) + cell("k2@hB#q", "hB", placement="q", err=True)
    a, text = build(recs, classify=lambda cid, sha: report.ERROR_RECOVERED if cid.endswith("p") else None)
    assert a["families"][("fb", "GAP")]["unclassified"] == ["k2@hB#p", "k2@hB#q"]
    fams = text.split("## Families")[1].split("## Defect groups")[0]
    assert "| fb | GAP | 2 | error-recovered tree 1; no class 1 | k2@hB#p, k2@hB#q |" in fams


def test_not_probed_prints_the_real_skip_reason():
    """A registry row without evidence shows placements.skipped_for's reason, not a generic line."""
    _, text = build(cell("k1@hA#p1", "hA", err=True))
    probed = text.split("## Not probed")[1]
    assert "no top-level separator in plain" in probed and "no evidence record for this row" not in probed
