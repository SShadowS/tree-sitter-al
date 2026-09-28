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
    note: str = ""
    source: bytes | None = None   # a labelled hand-built INPUT, used instead of fixture cases


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


# Hand-built input, labelled: no pre-fix fixture exists (the current fixture postdates
# c6b8107, and the c6b8107^ grammar cannot parse it at all). At c6b8107^ this parses with
# no ERROR and the #if condition swallows the next line: `X or C`.
REPLAY_4_INPUT = (b"codeunit 50000 T { procedure P() var A: Boolean; C: Boolean; B: Boolean; begin\n"
                  b"B := A\n#if X\n  or C\n#endif\n  ;\nend; }\n")


def _has_error_backstop(rec):
    return any(i.startswith("multi-config-parse:") and "has-error" in i for i in rec.items)


REPLAYS = [
    Replay(2, "bad36e4^", "case_else_preprocessor_test.txt", lambda c: True,
           lambda recs: any(_has(r, "|structure|missing|", "|structure|parent|") for r in recs)),
    Replay(3, "f47350d^", "scanner_lookahead_extras_test.txt",
           lambda c: c.name.startswith("Comment between a split end and its #else"),
           lambda recs: any(r.config == "CLEAN22=0" and _has_error_backstop(r) for r in recs),
           note="the old defect was CLI-silent (hidden MISSING token), not API-silent; "
                "detected by the has_error backstop, not by structure"),
    Replay(4, "c6b8107^", "hand-built", None,
           lambda recs: any(r.status == "directive-mismatch" and _has(r, "|directive|condition-extent|")
                            for r in recs),
           note="hand-built input, labelled: no pre-fix fixture exists (the current fixture postdates c6b8107)",
           source=REPLAY_4_INPUT),
    Replay(5, "04ff498^", "preproc_split_procedure_tail_test.txt",
           lambda c: c.name.startswith("Split signature followed by a pragma-only"),
           _replay5),
]


CACHE = Path(tempfile.gettempdir()) / "tree-sitter-al-replay"


def _sha(commit: str) -> str:
    r = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--verify", commit + "^{commit}"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git rev-parse {commit} failed: {r.stderr}")
    return r.stdout.strip()


def cached_parser_at(commit: str):
    """The parser for `commit`, built once into CACHE/<full sha>/ and reused afterwards.

    A fixed per-commit directory rather than a fresh temp dir: Windows cannot delete a
    loaded DLL, so per-run temp dirs were left behind on every run. The key is the
    RESOLVED sha, so the content is immutable; a directory without its DLL (an
    interrupted build) is simply rebuilt.
    """
    sha = _sha(commit)
    work = CACHE / sha
    lib = work / f"al-replay-{sha[:12]}.dll"
    if lib.is_file():
        return loader.make_parser(loader.load_language(lib))
    return build_parser_at(sha, work)


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
    safe = "".join(ch if ch.isalnum() else "_" for ch in commit)[:12]
    lib = work / f"al-replay-{safe}.dll"
    with loader.build_lock(REPO):
        r = subprocess.run(["tree-sitter", "build", "--output", str(lib), str(work)], cwd=work,
                           capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"tree-sitter build at {commit} failed:\n{r.stdout}\n{r.stderr}")
    return loader.make_parser(loader.load_language(lib))


def run_replay(r: Replay, work):
    """`work=None` runs the same cases against the CURRENT parser (positive control);
    `work="cache"` uses the per-commit cache; a Path builds fresh into that directory."""
    t0 = time.perf_counter()
    if work is None:
        parser = loader.make_parser(loader.load_language(loader.ensure_library(REPO)))
    elif work == "cache":
        parser = cached_parser_at(r.commit)
    else:
        parser = build_parser_at(r.commit, Path(work))
    build_s = time.perf_counter() - t0
    if r.source is not None:
        inputs = [(f"hand-built:replay-{r.number}", r.source)]
    else:
        inputs = [(c.id, c.source) for c in fixtures.extract(REPO / "test" / "corpus")
                  if c.file == r.file and r.select(c)]
    if not inputs:
        raise AssertionError(f"replay {r.number}: selector matched no case in {r.file}")
    recs = [rec for i, src in inputs for rec in runner.check_input(parser, i, src)]
    detected = r.detect(recs)
    # Masked: nothing but cannot-validate, and none of it is the replay's own detection
    # (replay 3's detection IS a cannot-validate record carrying the has_error item).
    masked = all(x.status == "cannot-validate" for x in recs) and not detected
    return ReplayResult(detected, masked,
                        [(x.input_id, x.config, x.status, x.items[:3]) for x in recs], recs, build_s)


def main() -> int:
    failed = 0
    for r in REPLAYS:
        res = run_replay(r, "cache")
        verdict = ("MASKED" if res.masked_by_cannot_validate
                   else "CAUGHT" if res.detected else "NOT CAUGHT")
        failed += verdict != "CAUGHT"
        print(f"replay {r.number} ({r.commit}, {r.file}): {verdict}  build {res.build_s:.1f}s")
        if r.note:
            print(f"  note: {r.note}")
        for rec in res.records:
            print(f"  {rec.input_id} [{rec.config}] {rec.status}")
            for i in rec.items:
                print(f"      {i.splitlines()[0] if i else i}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
