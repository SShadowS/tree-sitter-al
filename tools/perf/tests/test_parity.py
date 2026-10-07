"""parity: exit codes and differing-path listing, with the per-chunk check injected."""
from tools.perf import parity


def _setup(tmp_path):
    root = tmp_path / "c"
    root.mkdir()
    (root / "a.al").write_text("x")
    (root / "b.al").write_text("y")
    lib = tmp_path / "x.dll"
    lib.write_bytes(b"")
    return root, lib


def test_identical_exit_0(tmp_path, capsys):
    root, lib = _setup(tmp_path)
    out = parity.run(lib, lib, ["t"], roots={"t": root}, chunk_fn=lambda job: [])
    assert out == {"t": (2, [])} and parity.report(out) == 0
    assert "2 files, 0 differing" in capsys.readouterr().out


def test_planted_difference_exit_1_and_listed(tmp_path, capsys):
    root, lib = _setup(tmp_path)
    out = parity.run(lib, lib, ["t"], roots={"t": root},
                     chunk_fn=lambda job: [f"{job[2]}:{r}" for r in job[4] if r == "b.al"])
    assert parity.report(out) == 1
    o = capsys.readouterr().out
    assert "2 files, 1 differing" in o and "t:b.al" in o


def test_missing_corpus_or_lib(tmp_path):
    root, lib = _setup(tmp_path)
    for args in ((lib, lib, ["t"], None, {"t": tmp_path / "nope"}),
                 (tmp_path / "no.dll", lib, ["t"], None, {"t": root})):
        try:
            parity.run(*args, chunk_fn=lambda job: [])
            raise AssertionError("expected FileNotFoundError")
        except FileNotFoundError:
            pass


def test_empty_corpus_exit_2(tmp_path, capsys):
    _, lib = _setup(tmp_path)
    empty = tmp_path / "e"
    empty.mkdir()
    import pytest
    with pytest.raises(parity.ParityError, match="corpus t .*no .al files"):
        parity.run(lib, lib, ["t"], roots={"t": empty}, chunk_fn=lambda job: [])


def test_worker_failure_is_error_not_difference(tmp_path):
    import pytest
    root, lib = _setup(tmp_path)

    def boom(job):
        raise OSError("disk gone")
    with pytest.raises(parity.ParityError, match="corpus t: OSError"):
        parity.run(lib, lib, ["t"], roots={"t": root}, chunk_fn=boom)


def test_main_exit_2(tmp_path, monkeypatch):
    root, lib = _setup(tmp_path)
    monkeypatch.setattr(parity.common.oracle, "CORPORA", {"t": root, "e": tmp_path / "none"})
    monkeypatch.setattr(parity.common, "LABELS", ("t", "e"))
    assert parity.main(str(lib), str(lib), ["e"], workers=1) == 2


def test_real_chunk_with_fake_parsers(tmp_path, monkeypatch):
    from tools.perf import incremental
    root, lib = _setup(tmp_path)

    class P:
        def __init__(self, tag):
            self.tag = tag

        def parse(self, src):
            return (src, self.tag if src == b"y" else "")
    monkeypatch.setattr(parity, "_parsers", lambda a, b: (P("A"), P("B")))
    monkeypatch.setattr(incremental, "rows", lambda t: t)
    assert parity._chunk((str(lib), str(lib), "t", str(root), ["a.al", "b.al"])) == ["t:b.al"]
