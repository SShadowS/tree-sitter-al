"""Historical-defect replays (spec section 5): the oracle must catch defects that shipped.

Each replay builds the parser from the commit just before a fix, runs the oracle over
the fixture that fix pinned (taken from the CURRENT corpus), and requires the EXPECTED
check and kind -- not merely some failure, and not masked by cannot-validate.
"""
from __future__ import annotations

import io
import subprocess
import sys
import tarfile
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from tools.config_oracle import fixtures, runner
from tools.query_coverage import loader

REPO = loader.REPO_ROOT


@dataclass(frozen=True)
class Replay:
    number: int
    commit: str
    file: str
    select: object      # Case -> bool
    detect: object      # list[Record] -> bool


@dataclass
class ReplayResult:
    detected: bool
    masked_by_cannot_validate: bool
    statuses: list
    records: list = field(default_factory=list)
    build_s: float = 0.0


def _has(rec, *needles):
    return any(n in i for i in rec.items for n in needles)


def _structure(recs):
    return any(_has(r, "|structure|") for r in recs)


# A structure verdict is only meaningful for a configuration whose comparison RAN: no
# lowering / reference / resolver / zero-width reason among its items.
_NOT_RUN = ("lowering:", "reference-error:", "resolver:", "zero-width-leaf@", "multi-config-parse:",
            runner.INTERNAL)


def structure_ran(rec):
    return not any(i.startswith(_NOT_RUN) for i in rec.items)


def _replay5(recs):
    return (bool(recs)
            and all(r.status == "representation-violation" for r in recs)
            and any(_has(r, "|representation|var-block-without-var|") for r in recs)
            and all(structure_ran(r) for r in recs)
            and not _structure(recs))


REPLAYS = [
    Replay(2, "bad36e4^", "case_else_preprocessor_test.txt", lambda c: True,
           lambda recs: any(r.status == "discrepancy" and _has(r, "|structure|missing|", "|structure|parent|")
                            for r in recs)),
    Replay(3, "f47350d^", "scanner_lookahead_extras_test.txt",
           lambda c: c.name.startswith("Comment between a split end and its #else"),
           lambda recs: any(r.config == "CLEAN22=0" and r.status == "discrepancy" and _has(r, "|structure|")
                            for r in recs)),
    Replay(4, "c6b8107^", "preproc_expression_continuation_operators_test.txt",
           lambda c: b"#if X\n  or (2 = 2)" in c.source.replace(b"\r\n", b"\n"),
           lambda recs: any(r.status == "directive-mismatch" and _has(r, "|directive|condition-extent|")
                            for r in recs)),
    Replay(5, "04ff498^", "preproc_split_procedure_tail_test.txt",
           lambda c: c.name.startswith("Split signature followed by a pragma-only"),
           _replay5),
]


def build_parser_at(commit: str, work: Path):
    """git archive grammar.js + src at `commit` into `work` and build it there.

    Old commits track src/parser.c, so no `tree-sitter generate` is needed.
    """
    work.mkdir(parents=True, exist_ok=True)
    archive, err = b"", ""
    for paths in (["grammar.js", "src", "tree-sitter.json"], ["grammar.js", "src"]):
        r = subprocess.run(["git", "-C", str(REPO), "archive", commit, *paths], capture_output=True)
        if r.returncode == 0:
            archive = r.stdout
            break
        err = r.stderr.decode(errors="replace")
    if not archive:
        raise RuntimeError(f"git archive {commit} failed: {err}")
    with tarfile.open(fileobj=io.BytesIO(archive)) as tf:
        tf.extractall(work, filter="data")
    # A distinct name per commit: Windows will not unload a DLL, and a same-named one
    # already loaded in this process must not be mistaken for it.
    safe = "".join(ch if ch.isalnum() else "_" for ch in commit)
    lib = work / f"al-replay-{safe}.dll"
    with loader.build_lock(REPO):
        r = subprocess.run(["tree-sitter", "build", "--output", str(lib), str(work)], cwd=work,
                           capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"tree-sitter build at {commit} failed:\n{r.stdout}\n{r.stderr}")
    return loader.make_parser(loader.load_language(lib))


def run_replay(r: Replay, work):
    """`work=None` runs the same cases against the CURRENT parser (positive control)."""
    t0 = time.perf_counter()
    parser = (build_parser_at(r.commit, Path(work)) if work is not None
              else loader.make_parser(loader.load_language(loader.ensure_library(REPO))))
    build_s = time.perf_counter() - t0
    cases = [c for c in fixtures.extract(REPO / "test" / "corpus") if c.file == r.file and r.select(c)]
    if not cases:
        raise AssertionError(f"replay {r.number}: selector matched no case in {r.file}")
    recs = [rec for c in cases for rec in runner.check_input(parser, c.id, c.source)]
    return ReplayResult(r.detect(recs), all(x.status == "cannot-validate" for x in recs),
                        [(x.input_id, x.config, x.status, x.items[:3]) for x in recs], recs, build_s)


def main() -> int:
    failed = 0
    for r in REPLAYS:
        # The loaded DLL cannot be deleted on Windows while this process runs.
        with tempfile.TemporaryDirectory(prefix=f"replay{r.number}-", ignore_cleanup_errors=True) as tmp:
            res = run_replay(r, Path(tmp))
        verdict = ("MASKED" if res.masked_by_cannot_validate
                   else "CAUGHT" if res.detected else "NOT CAUGHT")
        failed += verdict != "CAUGHT"
        print(f"replay {r.number} ({r.commit}, {r.file}): {verdict}  build {res.build_s:.1f}s")
        for rec in res.records:
            print(f"  {rec.input_id} [{rec.config}] {rec.status}")
            for i in rec.items:
                print(f"      {i.splitlines()[0] if i else i}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
