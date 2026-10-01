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


def _replay1(recs):
    """CLEAN25=0 (arm selected): the old tree flattens `end else begin B();` into the
    then-block, so the reference's then_branch code_block has no lowered partner. The
    spec's table says `parent`; alignment pairs the flattened block with the reference's
    else_branch (more shared leaves), so the defect surfaces as the then_branch `missing`."""
    return any(r.config == "CLEAN25=0" and structure_ran(r)
               and any("|structure|missing|" in i and i.rsplit("/", 1)[-1].startswith("code_block.then_branch@")
                       for i in r.items)
               for r in recs)


def _has_error_backstop(rec):
    """The multi-config tree was rejected (`multi-config-parse:...`) before the structure
    check ever ran -- whether `ir.from_tree` found the MISSING/ERROR node directly
    (`missing@`/`error@`, replay 6's shape: the old grammar's MISSING `end_keyword` is a
    plain visible node) or only through its own has_error fallback (`has-error@`, replay
    3's shape: the MISSING token there is hidden inside an alias). Both are the same
    backstop from the runner's point of view -- `_check_config_inner` short-circuits to
    `cannot-validate` on any `multi-config-parse:` item, regardless of which reason it carries.
    Only those three reason shapes count: any other `multi-config-parse:` payload is not
    this backstop."""
    return any(i.startswith("multi-config-parse:")
               and any(p.startswith(_BACKSTOP_REASONS) for p in i[len("multi-config-parse:"):].split(","))
               for i in rec.items)


_BACKSTOP_REASONS = ("has-error@", "missing@", "error@")


REPLAYS = [
    Replay(1, "bad36e4^", "preproc_block_over_conditional_test.txt",
           lambda c: c.name.startswith("Shape C"), _replay1,
           note="spec expected structure `parent`; the comparator reports the lost then-block as "
                "`missing` (the flattened then-branch pairs with the reference's larger else-branch)"),
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
    Replay(6, "bc1a366^", "preproc_split_code_block_end_elif_test.txt", lambda c: True,
           lambda recs: any(_has_error_backstop(r) for r in recs),
           note="probed (base spec §5, step 1): every case in this file has has_error=True on "
                "the bc1a366^ parser -- the missing #elif branch leaves a MISSING end_keyword, "
                "so the multi-configuration parse is rejected before the structure check runs, "
                "same as replay 3. Detected by the has_error backstop, not by structure; base "
                "spec row 6 amended to match"),
    Replay(7, "81076bf^", "preproc_condition_precedence_test.txt", lambda c: True,
           lambda recs: any(_has(r, "|directive|condition-structure|") for r in recs),
           note="B1: `not` had no precedence, so `not A and B` was not (A and B) -- a silent "
                "wrong tree with no ERROR. Caught by condition_check, never by structure: "
                "the resolver masks the text, so the reference never sees a condition"),
]


REPLAY_3_WITNESS_LABEL = "hand-built tree witness (spec §5)"
# Kinds whose (kind, field, span) the witness must share with the old parser's tree: the
# nodes the defect regroups. Everything else keeps HEAD's shape, so a structure item can
# only come from the regrouping, not from unrelated grammar drift since f47350d^.
_R3_KINDS = {"code_block", "statement_block", "if_statement", "preproc_conditional_statement",
             "call_statement", "begin_keyword", "end_keyword", "preproc_split_code_block_end"}


def _r3_signature(root):
    out, stack = [], [root]
    while stack:
        n = stack.pop()
        if n.kind in _R3_KINDS:
            out.append((n.kind, n.field, n.start, n.end))
        stack.extend(n.children)
    return sorted(out)


def replay3_tree_witness(old_parser=None):
    """REPLAY_3_WITNESS_LABEL: replay 3's STRUCTURAL detection, shown on a labelled hand-built tree.

    On the real old parser replay 3 is caught only by the has_error backstop: the defect
    was CLI-silent (its MISSING `end` is hidden), not API-silent. This builds the tree the
    old parser produced, minus that hidden MISSING token -- the API-silent variant a
    backstop cannot see -- and requires `structure` to report it for CLEAN22=0.

    The pre-fix reading is taken from the old parser (f47350d^) itself: the HEAD
    multi-configuration tree is rewritten so that the `end;` under `#if not CLEAN22` is a
    `call_statement` inside a `preproc_conditional_statement` (transplanted from the old
    tree) appended to the then-block's statements; the then-block takes the procedure's
    closing `end` and `;`, and the outer block has no `end`. The rewrite is checked against
    the old tree on every node kind it touches.

    -> (structure discrepancies, witness signature, old-tree signature)."""
    from tools.config_oracle import compare, directives, ir, reference
    from tools.config_oracle.lowering import lower_tree
    r = next(x for x in REPLAYS if x.number == 3)
    [case] = [c for c in fixtures.extract(REPO / "test" / "corpus") if c.file == r.file and r.select(c)]
    src = case.source
    head = loader.make_parser(loader.load_language(loader.ensure_library(REPO)))
    old = old_parser or cached_parser_at(r.commit)
    root, extras, problems = ir.from_tree(head.parse(src))
    old_root, _, old_problems = ir.from_tree(old.parse(src))
    assert not problems and old_problems, (problems, old_problems)   # HEAD clean; old has_error

    def find(n, pred, parent=None):
        if pred(n):
            return n, parent
        for c in n.children:
            hit = find(c, pred, n)
            if hit:
                return hit
        return None

    outer, proc = find(root, lambda n: n.kind == "code_block" and n.field == "body")
    then_cb, _ = find(outer, lambda n: n.field == "then_branch")
    begin, stmts, split = then_cb.children
    assert split.kind == "preproc_split_code_block_end", split.kind
    old_cond, _ = find(old_root, lambda n: n.kind == "preproc_conditional_statement")
    outer_end, semi = outer.children[-1], proc.children[-1]
    assert (outer_end.kind, semi.kind) == ("end_keyword", ";")
    stmts.children.append(old_cond)
    then_cb.children = [begin, stmts, outer_end, semi]
    outer.children.remove(outer_end)
    proc.children.remove(semi)

    def respan(n):
        for c in n.children:
            respan(c)
        ir.recompute_span(n)
    respan(root)
    witness_sig = _r3_signature(find(root, lambda n: n.kind == "procedure")[0])
    old_sig = _r3_signature(find(old_root, lambda n: n.kind == "procedure")[0])

    res = directives.resolve(src, frozenset())                       # CLEAN22=0
    ref = reference.extract(head, res.masked)
    assert not ref.problems, ref.problems
    low, _low_extras, _ = lower_tree(root, extras, res)
    return compare.structure(ref.root, low), witness_sig, old_sig


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
                           capture_output=True, text=True, env=loader.build_env())
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
    ds, witness, old = replay3_tree_witness()
    ok = witness == old and any(d.check == "structure" and d.path.endswith("call_statement.-@143-146") for d in ds)
    failed += not ok
    print(f"replay 3 structure, {REPLAY_3_WITNESS_LABEL}: {'CAUGHT' if ok else 'NOT CAUGHT'}"
          f"  (faithful to f47350d^ tree: {witness == old})")
    for d in ds:
        print(f"      structure|{d.kind}|{d.path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
