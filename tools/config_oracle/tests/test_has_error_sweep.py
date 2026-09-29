"""tools/has_error_sweep.py: the gate for errors no command-line tool prints.

A MISSING node for a HIDDEN token is not printed by `tree-sitter parse`, its
`--json-summary` or parse-al-parallel.sh; only py-tree-sitter's `has_error` sees it
(docs/deferred-work.md item 12). `tree-sitter test` does print `(MISSING _x)`, but
only for a fixture that holds the triggering input. The key case is the mutation:
the parser from before the `_directive_eol` whitespace fix (673528e^) must make the
sweep report hidden-only and exit 1.
"""
import re

import pytest

from tools import has_error_sweep as sweep
from tools.config_oracle import fixtures, replay
from tools.config_oracle.tests.test_directive_eol import EOLS
from tools.query_coverage import loader

REPO = loader.REPO_ROOT
CLEAN = b"codeunit 50100 T { trigger OnRun() begin end; }\n"
VISIBLE = b"codeunit 50100 T { procedure P() begin @@@ end; }\n"


def eol_source(eol):
    return b"codeunit 1 T { trigger OnRun() begin\n#if A" + eol + b"x := 1;\n#endif\nend; }\n"


def write(root, files):
    root.mkdir(parents=True, exist_ok=True)
    for name, src in files.items():
        (root / name).write_bytes(src)
    return root


def run(capsys, *argv):
    code = sweep.main(list(map(str, argv)))
    return code, capsys.readouterr().out


def test_clean_source_exits_0(tmp_path, capsys):
    code, out = run(capsys, "--root", write(tmp_path / "c", {"a.al": CLEAN}))
    assert code == 0, out
    assert "clean=1" in out and "hidden-only=0" in out and "visible=0" in out


def test_error_source_is_visible_and_exits_1(tmp_path, capsys):
    code, out = run(capsys, "--root", write(tmp_path / "v", {"a.al": CLEAN, "b.al": VISIBLE}))
    assert code == 1, out
    assert re.search(r"^visible\t.*b\.al\tERROR@\d+-\d+", out, re.M), out
    assert "visible=1" in out and "hidden-only=0" in out


def test_missing_root_exits_2(tmp_path, capsys):
    code, out = run(capsys, "--root", tmp_path / "does-not-exist")
    assert code == 2


def test_empty_root_exits_2(tmp_path, capsys):
    (tmp_path / "empty").mkdir()
    (tmp_path / "empty" / "not-al.txt").write_text("x")
    code, out = run(capsys, "--root", tmp_path / "empty")
    assert code == 2


def test_one_missing_root_among_good_ones_exits_2(tmp_path, capsys):
    good = write(tmp_path / "g", {"a.al": CLEAN})
    code, out = run(capsys, "--root", good, "--root", tmp_path / "nope")
    assert code == 2


def test_no_input_exits_2(capsys):
    with pytest.raises(SystemExit) as e:
        sweep.main([])
    assert e.value.code == 2


def test_broken_build_exits_2(tmp_path, capsys, monkeypatch):
    def broken(_root, force=False):
        raise loader.StaleParserError("tree-sitter build failed (exit 1): injected")
    monkeypatch.setattr(loader, "ensure_library", broken)
    code, out = run(capsys, "--root", write(tmp_path / "c", {"a.al": CLEAN}))
    assert code == 2


def test_unloadable_lib_exits_2(tmp_path, capsys):
    code, out = run(capsys, "--root", write(tmp_path / "c", {"a.al": CLEAN}),
                    "--lib", tmp_path / "no-such.dll")
    assert code == 2


def test_eol_inputs_are_clean_at_head(tmp_path, capsys):
    """Positive control for the mutation below: the same files, the current parser."""
    root = write(tmp_path / "eol", {f"eol{i}.al": eol_source(e) for i, e in enumerate(EOLS)})
    code, out = run(capsys, "--root", root)
    assert code == 0, out
    assert f"clean={len(EOLS)}" in out


@pytest.mark.slow
def test_pre_fix_parser_reports_hidden_only(tmp_path, capsys):
    """The mutation: 673528e^ skipped only space and tab before `_directive_eol`, so 5
    of the 8 inputs leave a hidden MISSING token. The sweep must call them hidden-only
    and exit 1, while `tree-sitter parse --json-summary` reported all 8 successful."""
    sha = replay._sha("673528e^")
    replay.cached_parser_at(sha)
    lib = replay.CACHE / sha / f"al-replay-{sha[:12]}.dll"
    assert lib.is_file()
    root = write(tmp_path / "eol", {f"eol{i}.al": eol_source(e) for i, e in enumerate(EOLS)})
    code, out = run(capsys, "--root", root, "--lib", lib)
    assert code == 1, out
    assert "hidden-only=5" in out and "visible=0" in out, out
    assert len(re.findall(r"^hidden-only\t", out, re.M)) == 5, out

    # M4: a file with a visible ERROR AND the hidden MISSING reports both.
    both = b"codeunit 1 T { trigger OnRun() begin\n#if A\f\nx := 1;\n#endif\nend;\n" \
           b"procedure P() begin @@@ end; }\n"
    root2 = write(tmp_path / "both", {"both.al": both})
    code, out = run(capsys, "--root", root2, "--lib", lib)
    assert code == 1, out
    assert re.search(r"^visible\t.*both\.al\tERROR@.*\thidden: preproc_if@", out, re.M), out
    assert "visible=1" in out and "with-hidden=1" in out, out


def test_every_corpus_case_is_swept():
    """No case is excluded, negatives included: a negative FILE holds clean cases too."""
    items = sweep._inputs([], True)
    assert len(items) == len(fixtures.extract(sweep.CORPUS))
    assert any(neg for _, _, neg in items)


def test_clean_case_inside_a_negative_file_is_swept(al_parser):
    """preproc_if_elif_whitespace_tolerance_test.txt is a negative file, and 6 of its
    12 cases are the positive `#if` whitespace cases: exactly where a hidden MISSING
    `_directive_eol` would appear. They must be parsed, and must be clean."""
    target = "preproc_if_elif_whitespace_tolerance_test.txt"
    assert target in sweep.deliberate_negatives()
    sweep._init(al_parser)
    mine = [it for it in sweep._inputs([], True) if it[0].startswith(target + "#")]
    assert mine and all(neg for _, _, neg in mine)
    verdicts = [sweep._check(it)[1] for it in mine]
    assert "clean" in verdicts, verdicts


def test_negative_accepts_visible_but_never_hidden():
    assert sweep.accepted("clean", False) and sweep.accepted("clean", True)
    assert sweep.accepted("visible", True)
    assert not sweep.accepted("visible", False)
    assert not sweep.accepted("hidden-only", True)
    assert not sweep.accepted("hidden-only", False)
    assert not sweep.accepted("visible+hidden", True)


def test_negatives_match_by_basename_like_step_3():
    """Step 3 compares `basename`; the sweep compares the case file's name. Both must
    exempt a negative wherever it sits under test/corpus/."""
    names = sweep.deliberate_negatives()
    assert names, "the deliberate-negative list is empty"
    on_disk = {p.name for p in sweep.CORPUS.rglob("*.txt")}
    for n in names:
        assert n in on_disk, f"listed but absent: {n}"
        assert sweep.is_negative(n) and sweep.is_negative(f"sub/dir/{n}")
    assert not sweep.is_negative("sub/" + "x" + next(iter(names)))
    vg = (REPO / "validate-grammar.sh").read_text(encoding="utf-8")
    assert 'name=$(basename "$1")' in vg


def test_undecodable_input_cannot_run_exits_2(tmp_path, capsys):
    """A truncated UTF-16 file is a crash after setup: `cannot run`, never exit 1."""
    root = write(tmp_path / "bad", {"a.al": CLEAN, "b.al": b"\xff\xfe\x41"})
    code, out = run(capsys, "--root", root)
    assert code == 2, out
    code, out = run(capsys, "--root", root, "--jobs", 2)
    assert code == 2, out


def test_gate_selftest_prints_failing_steps():
    import importlib.util
    spec = importlib.util.spec_from_file_location("gate_selftest", REPO / "tools" / "gate_selftest.py")
    gs = importlib.util.module_from_spec(spec)
    import sys
    sys.modules["gate_selftest"] = gs  # dataclasses resolves the module by name
    spec.loader.exec_module(gs)
    out = ("Step 3b: x\n✓ fine\nStep 9: WASM Freshness\n"
           "✗ Committed wasm is stale\n✗ Some validation checks failed!\n")
    assert gs.failing_steps(out) == ["[Step 9: WASM Freshness] Committed wasm is stale"]


def test_validate_grammar_reads_the_same_negatives_file():
    """One source of truth: Step 3 reads the file the tool reads, and no copy of
    the list survives inline in validate-grammar.sh or release.md."""
    rel = sweep.NEGATIVES_FILE.relative_to(REPO).as_posix()
    assert rel == "tools/deliberate-negatives.txt"
    vg = (REPO / "validate-grammar.sh").read_text(encoding="utf-8")
    release = (REPO / ".claude" / "commands" / "release.md").read_text(encoding="utf-8")
    assert rel in vg and rel in release
    greps = [line for line in release.splitlines() if "grep -vE" in line]
    assert greps
    for n in sweep.deliberate_negatives():
        assert f'"{n}"' not in vg, f"{n} still listed inline in validate-grammar.sh"
        assert not any(n[:-len(".txt")] in g for g in greps), f"{n} still inline in release.md"


def test_worker_pool_reports_the_same(tmp_path, capsys):
    code, out = run(capsys, "--root", write(tmp_path / "v", {"a.al": CLEAN, "b.al": VISIBLE}),
                    "--jobs", 2)
    assert code == 1, out
    assert "clean=1" in out and "visible=1" in out and "hidden-only=0" in out


def test_utf16_with_bom_is_decoded(tmp_path, capsys):
    """`tree-sitter parse` detects a UTF-16 BOM; BCApps ships 19 such files."""
    utf16 = CLEAN.decode().encode("utf-16")
    assert utf16[:2] in (b"\xff\xfe", b"\xfe\xff")
    code, out = run(capsys, "--root", write(tmp_path / "u", {"a.al": utf16}))
    assert code == 0, out
