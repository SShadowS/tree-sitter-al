import json
import random
import subprocess
from pathlib import Path

import pytest

from tools.alc_probe import core
from tools.b7_audit import evidence
from tools.b7_audit.placements import Cell
from tools.config_oracle.directives import resolve

PRE = "codeunit 50100 P\n{\n    trigger OnRun()\n    var\n        I: Integer;\n    begin\n"
HOLE = "#if X\n        I := Foo;\n#endif\n"
POST = "        I := 2;\n    end;\n}\n"
SRC = PRE + HOLE + POST
A = len(PRE.encode())
CELL = Cell(id="k@h#sep-only", key="k", host="h", placement="sep-only", source=SRC, symbols=("X",),
            intended_valid=frozenset({frozenset(), frozenset({"X"})}), hole=(A, A + len(HOLE.encode())),
            plain=PRE + "        I := 1;\n" + POST)
SEED = Cell(id="seed:s", key="seed:s", host="h", placement="seed:s", source=SRC, symbols=("X",),
            intended_valid=frozenset(), hole=(0, len(SRC.encode())), plain=None)
IDENT = core.Identity("fake 1.0", "", "abc")


def fake(rule):
    """A fake alc: preprocesses Test.al with app.json's symbols and asks `rule(masked)` for
    (kind, codes). Counts its compiles in `.calls`."""
    def run(args):
        run.calls += 1
        project = Path(args[2].split(":", 1)[1])
        syms = json.loads((project / "app.json").read_text())["preprocessorSymbols"]
        raw = (project / "Test.al").read_bytes()
        kind, codes = rule(resolve(raw, frozenset(syms)).masked.decode(), raw.decode())
        if kind == core.ACCEPT:
            (project / "test.app").write_bytes(b"app")
            return subprocess.CompletedProcess(args, 0, "", "")
        if kind == core.REJECT:
            out = "".join(f"{project}\\Test.al(1,1): error {c}: x\n" for c in codes)
        else:
            out = "error AL1028: broken\n"
        return subprocess.CompletedProcess(args, 1, out, "")
    run.calls = 0
    return run


def alc(rule, tmp_path, cache=None):
    return evidence.Alc(IDENT, runner=fake(rule), cache_dir=cache, workdir=tmp_path / "work")


ACCEPT = lambda t, raw: (core.ACCEPT, ())
TYPE_ERROR = lambda t, raw: (core.REJECT, ("AL0175",)) if "Foo" in t else (core.ACCEPT, ())
SYNTAX_ERROR = lambda t, raw: (core.REJECT, ("AL0104",)) if "Foo" in t else (core.ACCEPT, ())
CONTROL_FAILS = lambda t, raw: (core.REJECT, ("AL0104",)) if "I := 1;" in t else (core.ACCEPT, ())


def test_internal_error_aborts(monkeypatch, al_parser, tmp_path):
    from tools.config_oracle.runner import Record
    monkeypatch.setattr("tools.config_oracle.runner.check_input",
                        lambda *a, **k: [Record("k", "X=1", "cannot-validate", ["internal-error:boom"])])
    with pytest.raises(evidence.OracleCrash):
        evidence.measure(CELL, al_parser, alc(ACCEPT, tmp_path))


def test_broken_project_aborts(al_parser, tmp_path):
    with pytest.raises(evidence.ProbeBroken):
        evidence.measure(CELL, al_parser, alc(lambda t, raw: (core.BROKEN, ()), tmp_path))


def test_split_flat_mismatch_aborts(al_parser, tmp_path):
    # rejects anything still holding the directive text: only the split compile does
    with pytest.raises(evidence.ProbeBroken):
        evidence.measure(CELL, al_parser, alc(lambda t, raw: (core.REJECT, ("AL0621",)) if "#if" in raw
                                              else (core.ACCEPT, ()), tmp_path))


def test_reject_class_from_control(al_parser, tmp_path):
    recs = evidence.measure(CELL, al_parser, alc(TYPE_ERROR, tmp_path))
    assert [r["config"] for r in recs] == ["X=0", "X=1"]
    assert {r["reject_class"] for r in recs if r["alc_flat"]["verdict"] == "REJECT"} == {"semantic"}
    assert recs[0]["reject_class"] is None and recs[1]["alc_flat"]["codes"] == ["AL0175"]
    assert all(r["alc_control"]["verdict"] == "ACCEPT" and r["control"] == "typed" for r in recs)
    recs = evidence.measure(CELL, al_parser, alc(SYNTAX_ERROR, tmp_path))
    assert recs[1]["reject_class"] == "syntax"


def test_control_failure_is_generator_bug(al_parser, tmp_path):
    with pytest.raises(evidence.GeneratorBug):
        evidence.measure(CELL, al_parser, alc(CONTROL_FAILS, tmp_path))


def test_all_invalid_vector_accepted_is_generator_bug(al_parser, tmp_path):
    cell = Cell(**{**CELL.__dict__, "intended_valid": frozenset()})
    with pytest.raises(evidence.GeneratorBug):
        evidence.measure(cell, al_parser, alc(ACCEPT, tmp_path))


def test_seed_has_no_control_and_never_generator_bug(al_parser, tmp_path):
    recs = evidence.measure(SEED, al_parser, alc(SYNTAX_ERROR, tmp_path))
    assert all(r["control"] == "none" and r["alc_control"] is None for r in recs)
    assert [r["reject_class"] for r in recs] == [None, "syntax"]
    assert [r["intended_valid"] for r in recs] == [False, False]


def test_parser_and_oracle_fields(al_parser, tmp_path):
    recs = evidence.measure(CELL, al_parser, alc(ACCEPT, tmp_path))
    assert all(r["parser_has_error"] is False and r["error_in_hole"] is False for r in recs)
    assert all(r["oracle"]["status"] == "pass" for r in recs)
    bad = Cell(**{**CELL.__dict__, "source": PRE + "#if X\n        I := ;\n#endif\n" + POST})
    obs = evidence.observe(bad, al_parser)
    assert obs.has_error and obs.error_in_hole and not obs.clean


def test_cache_hit_skips_compile(tmp_path, al_parser):
    first = alc(TYPE_ERROR, tmp_path, cache=tmp_path / "cache")
    a = evidence.measure(CELL, al_parser, first)
    assert first.runner.calls > 0
    second = alc(TYPE_ERROR, tmp_path, cache=tmp_path / "cache")
    assert evidence.measure(CELL, al_parser, second) == a and second.runner.calls == 0
    other = evidence.Alc(core.Identity("fake 2.0", "", "abc"), runner=fake(TYPE_ERROR),
                         cache_dir=tmp_path / "cache", workdir=tmp_path / "w2")
    evidence.measure(CELL, al_parser, other)
    assert other.runner.calls > 0             # another compiler identity never reads the cache


def test_dedup_compiles_each_distinct_source_once(tmp_path, al_parser):
    a = alc(ACCEPT, tmp_path)
    a.prefetch(evidence.alc_jobs(CELL) + evidence.alc_jobs(CELL), jobs=3)
    # split x2, flat x2, control x1 (the plain filling holds no X: same text in both configurations)
    assert a.runner.calls == 5 and a.stats["requested"] == 12
    evidence.measure(CELL, al_parser, a)
    assert a.runner.calls == 5


def test_class_sampled_cell_compiles_nothing(tmp_path, al_parser):
    a = alc(ACCEPT, tmp_path)
    recs = evidence.measure(CELL, al_parser, a, sampled_by="k@h#rep")
    assert a.runner.calls == 0
    assert all(r["alc"] == "class-sampled" and r["alc_representative"] == "k@h#rep"
               and r["alc_split"] is None for r in recs)


def test_tier_selection():
    cls = ("list-separator", "var-names", "sep-only")
    infos = [  # (id, class, clean+pass, all intended valid, seed)
        evidence.TierInfo("c2", cls, True, True, False),
        evidence.TierInfo("c1", cls, True, True, False),
        evidence.TierInfo("c3", cls, False, True, False),
        evidence.TierInfo("c4", cls, True, False, False),
        evidence.TierInfo("seed:a", ("seed", "seed", "seed:a"), True, True, True),
        evidence.TierInfo("c5", ("terminator", "x", "trail"), True, True, False),
    ]
    reps = evidence.representatives((i.id, i.cls) for i in infos)
    assert reps[cls] == "c1"
    assert evidence.tiers(infos, reps) == {"c1": None, "c2": "c1", "c3": None, "c4": None,
                                           "seed:a": None, "c5": None}


def test_records_sorted_and_deterministic(tmp_path):
    header = {"alc": {"version": "v"}, "runtime": "15.0"}
    recs = [{"cell": c, "config": k, "z": 1, "a": [2]} for c in ("b", "a", "c") for k in ("X=1", "X=0")]
    p1, p2 = tmp_path / "1.jsonl", tmp_path / "2.jsonl"
    evidence.write(recs, header, p1)
    random.Random(1).shuffle(recs)
    evidence.write(recs, header, p2)
    assert p1.read_bytes() == p2.read_bytes() and b"\r\n" not in p1.read_bytes()
    h, rs = evidence.read(p1)
    assert h == header and [(r["cell"], r["config"]) for r in rs] == sorted((r["cell"], r["config"]) for r in recs)


def test_diff_records():
    old = [{"cell": "a", "config": "-", "v": 1}, {"cell": "b", "config": "-", "v": 1}]
    new = [{"cell": "a", "config": "-", "v": 2}, {"cell": "c", "config": "-", "v": 1}]
    assert evidence.diff_records(old, new, {"a", "b", "c"}) == [
        "changed a - v: 1 -> 2", "missing b -", "new c -"]
    assert evidence.diff_records(old, new, {"a"}) == ["changed a - v: 1 -> 2"]


# --- fix round 1 ----------------------------------------------------------------------------------
def test_oracle_reduced_to_reasons(al_parser, tmp_path, monkeypatch):
    from tools.config_oracle.runner import Record
    items = ["multi-config-parse:error@303,error@306", "multi-config-parse:error@41", "zero-width-leaf@7"]
    monkeypatch.setattr("tools.config_oracle.runner.check_input",
                        lambda *a, **k: [Record("k", "X=0", "cannot-validate", items),
                                         Record("k", "X=1", "pass", [])])
    recs = evidence.measure(CELL, al_parser, alc(ACCEPT, tmp_path))
    assert recs[0]["oracle"] == {"status": "cannot-validate", "reasons": ["multi-config-parse:error", "zero-width-leaf"]}
    assert recs[1]["oracle"] == {"status": "pass", "reasons": []}


def test_check_against_reduced_committed_is_clean():
    fresh = {"cell": "a", "config": "-", "oracle": {"status": "pass", "items": ["x@1", "x@2"]}}
    committed = {"cell": "a", "config": "-", "oracle": {"status": "pass", "reasons": ["x"]}}
    assert evidence.diff_records([committed], [fresh], {"a"}) == []


def test_no_project_dir_left(al_parser, tmp_path):
    a = alc(lambda t, raw: (core.REJECT, ("AL0104",)) if "GARBAGE" in t else (core.ACCEPT, ()),
            tmp_path, cache=tmp_path / "cache")
    a.check_controls()
    evidence.measure(CELL, al_parser, a)
    assert list((tmp_path / "work").iterdir()) == []
    owned = evidence.Alc(IDENT, runner=fake(ACCEPT))
    owned.verdict("x")
    wd = owned.workdir
    owned.close()
    assert not wd.exists()


def test_oracle_assignment_mismatch_is_its_own_error(al_parser, tmp_path, monkeypatch):
    from tools.config_oracle.runner import Record
    monkeypatch.setattr("tools.config_oracle.runner.check_input",
                        lambda *a, **k: [Record("k", "X=1", "pass", [])])
    with pytest.raises(evidence.DiscoverMismatch):
        evidence.measure(CELL, al_parser, alc(ACCEPT, tmp_path))


def test_cache_key_covers_project_template(monkeypatch, tmp_path):
    k1 = alc(ACCEPT, tmp_path).key("x", ())
    monkeypatch.setattr(evidence, "CORE_SHA256", "other")
    assert alc(ACCEPT, tmp_path).key("x", ()) != k1


def test_cache_write_leaves_no_temp(al_parser, tmp_path):
    evidence.measure(CELL, al_parser, alc(ACCEPT, tmp_path, cache=tmp_path / "cache"))
    files = [p.name for p in (tmp_path / "cache").rglob("*") if p.is_file()]
    assert files and all(f.endswith(".json") and len(f) == 69 for f in files)


def test_corpus_manifest_and_warnings(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "x.al").write_text("abc")
    (tmp_path / "b.txt").write_text("no")
    m = evidence.corpus_entry(tmp_path)
    assert m["present"] and m["head"] is None and m["manifest"]["al_files"] == 1
    (tmp_path / "y.al").write_text("d")
    m2 = evidence.corpus_entry(tmp_path)
    assert m2["manifest"]["sha256"] != m["manifest"]["sha256"]
    assert evidence.corpus_warnings({"C": m}, {"C": m2}) == ["WARNING: corpus C changed since the evidence was taken"]
    assert evidence.corpus_warnings({"C": m}, {"C": m}) == []


def test_header_records_production_shapes_sha():
    h = evidence.header(IDENT, "15.0", corpora={})
    assert h["production_shapes_sha256"] == evidence._sha(evidence.seeds.SHAPES_JSON)


def test_only_with_accept_tool_refuses_identity_merge(tmp_path):
    exe = tmp_path / "al.exe"
    exe.write_bytes(b"x")
    out = tmp_path / "e.jsonl"
    evidence.write([], {"alc": {"version": "old"}}, out)
    ver = lambda args: subprocess.CompletedProcess(args, 0, "new 1.0\n", "")
    msgs = []
    assert evidence.run(only="var-names", accept_tool=True, out=out, al=str(exe), runner=ver, log=msgs.append) == 2
    assert "identity" in msgs[-1]


def test_gz_evidence_is_deterministic(tmp_path):
    header = {"alc": {"version": "v"}, "runtime": "15.0"}
    recs = [{"cell": c, "config": "-", "z": 1} for c in ("b", "a")]
    p1, p2 = tmp_path / "1.jsonl.gz", tmp_path / "sub-2.jsonl.gz"
    evidence.write(recs, header, p1)
    evidence.write(list(reversed(recs)), header, p2)
    assert p1.read_bytes() == p2.read_bytes() and p1.read_bytes()[:2] == b"\x1f\x8b"
    h, rs = evidence.read(p1)
    assert h == header and [r["cell"] for r in rs] == ["a", "b"]
