import random

from tools.b7_audit import evidence, report
from tools.b7_audit.registry import Row

SHA = "c" * 64


def cell(cid, host, placement="p1", alc="ACCEPT", err=False, oracle="pass", key=None, reject_class=None):
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


def build(records, rows=ROWS, deps=None):
    a = report.analyse(records, HEADER, rows)
    return a, report.render(a, HEADER)


def test_report_deterministic(tmp_path):
    recs = cell("k1@hA#p1", "hA", err=True) + cell("k2@hB#p1", "hB", oracle="discrepancy") + \
        cell("k3@hC#p2", "hC", oracle="cannot-validate") + cell("k4@hD#p1", "hD")
    out = []
    for i in range(3):
        shuffled = recs[:]
        random.Random(i).shuffle(shuffled)
        p = tmp_path / f"e{i}.jsonl"
        evidence.write(shuffled, HEADER, p)
        rp = tmp_path / "r.tsv"
        rp.write_text("", encoding="utf-8")
        h, r = evidence.read(p)
        out.append(report.render(report.analyse(r, h, ROWS), h))
    assert out[0] == out[1] == out[2] and "\r" not in out[0]


def test_families_dedupe():
    recs = cell("k1@hA#p1", "hA", err=True) + cell("k1@hA#p2", "hA", placement="p2", err=True)
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
    recs = cell("k1@hA#p1", "hA", err=True) + cell("k1@hA#p2", "hA", placement="p2", err=True) + \
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
    a = report.analyse(cell("kl@hL#lead-optional", "hL", placement="lead-optional", key="kl", err=True), HEADER, link)
    assert list(a["families"]) == [("link-list-comma-leading", "GAP")]
    assert report.rank(a["families"]) == [("link-list-comma-leading", "GAP")]
