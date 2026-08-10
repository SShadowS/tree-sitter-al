#!/usr/bin/env python3
"""gate_selftest.py — mutation testing for this repo's validation gates.

WHY THIS EXISTS

Every gate here is trusted to say "no" when something is wrong. Five times in
one release cycle a tool said "yes" for work it had not done, and every one was
caught by a human reading code rather than by any gate:

  * tools/fieldwalk.c printed nothing on a miss, indistinguishable from "the
    field has no members"
  * validate-grammar.sh Step 8 reported success when no baseline file existed
  * tools/analyze_duplicates.py returned zero extracted rules as a pass
  * tools/tree-harness.sh swallowed failed chunks with `|| true` and checked
    only the global total, so offsetting losses cancelled out
  * three helper scripts were untracked, so a fresh clone degraded the orphan,
    duplicate and health steps to "script not found" warnings

The shape is always the same: PASSING LOOKS IDENTICAL WHETHER THE CHECK RAN OR
NOT. A gate whose failure path has never been executed is not a gate.

So: for each (gate, injected defect, expected complaint) triple below, copy the
repo to scratch, inject the defect, run the real gate end to end, and require
that it exits non-zero AND that its output names the thing that was injected.
A gate that fails for the wrong reason does not pass.

ANTI-RECURSION

This harness is a gate, so it is subject to its own thesis. It must never
report a clean run it did not perform. It therefore aborts — rather than
skipping, warning, or counting a pass — when it cannot find a gate, when a
mutation changes nothing, or when it would otherwise run zero cases. Those
three guards are themselves tested: `--prove-guards` deliberately trips each
one and fails if the harness stays quiet.

USAGE

    python tools/gate_selftest.py --list
    python tools/gate_selftest.py --prove-guards
    python tools/gate_selftest.py                     # every case
    python tools/gate_selftest.py -k step6            # cases matching a substring
    python tools/gate_selftest.py --quick             # cases that skip the slow gates

Wrap it in ./tools/ts-lock.sh: nearly every case runs `tree-sitter`, and the
compiled parser is shared by grammar NAME across every worktree on the machine.
The harness takes the lock once for the whole run rather than per case.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Sequence

REPO = Path(__file__).resolve().parent.parent
ANSI = re.compile(r"\x1b\[[0-9;]*m")

# Everything a gate reads. Copied per case; nothing else is visible to the gate,
# which is deliberate — a case must not be able to reach the real repo.
COPY_FILES = [
    "grammar.js",
    "validate-grammar.sh",
    "parse-al-parallel.sh",
    "package.json",
    "tree-sitter.json",
    ".grammar_baseline.json",
]
COPY_DIRS = ["tools", "test", "queries", "src"]


class SelfTestError(RuntimeError):
    """The harness could not do its job. Never a case failure — always fatal."""


# --------------------------------------------------------------------------
# Mutations. Each one VERIFIES it changed something; a mutation that silently
# matches nothing would turn its case into a test of an unmodified repo, which
# is precisely the vacuous pass this file exists to prevent.
# --------------------------------------------------------------------------


@dataclass
class Mutation:
    describe: str
    apply: Callable[[Path], None]


def sub(relpath: str, pattern: str, repl: str, count: int = 0) -> Mutation:
    def _apply(root: Path) -> None:
        target = root / relpath
        if not target.exists():
            raise SelfTestError(f"mutation target '{relpath}' does not exist")
        text = target.read_text(encoding="utf-8", errors="surrogateescape")
        new, n = re.subn(pattern, repl, text, count=count)
        if n == 0:
            raise SelfTestError(
                f"mutation matched nothing: /{pattern}/ in '{relpath}' -- the case "
                f"would have run against an unmodified file"
            )
        target.write_text(new, encoding="utf-8", errors="surrogateescape")

    return Mutation(f"s/{pattern}/{repl}/ in {relpath}", _apply)


def prepend(relpath: str, text: str) -> Mutation:
    def _apply(root: Path) -> None:
        target = root / relpath
        if not target.exists():
            raise SelfTestError(f"mutation target '{relpath}' does not exist")
        target.write_text(
            text + target.read_text(encoding="utf-8", errors="surrogateescape"),
            encoding="utf-8",
        )

    return Mutation(f"prepend {text.strip()!r} to {relpath}", _apply)


def insert_after_line(relpath: str, lineno: int, text: str) -> Mutation:
    def _apply(root: Path) -> None:
        target = root / relpath
        if not target.exists():
            raise SelfTestError(f"mutation target '{relpath}' does not exist")
        lines = target.read_text(encoding="utf-8").splitlines(keepends=True)
        if lineno > len(lines):
            raise SelfTestError(
                f"cannot insert after line {lineno} of '{relpath}': it has {len(lines)}"
            )
        lines.insert(lineno, text if text.endswith("\n") else text + "\n")
        target.write_text("".join(lines), encoding="utf-8")

    return Mutation(f"insert at {relpath}:{lineno}", _apply)


def create(relpath: str, text: str) -> Mutation:
    def _apply(root: Path) -> None:
        target = root / relpath
        if target.exists():
            raise SelfTestError(f"'{relpath}' already exists -- refusing to overwrite")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    return Mutation(f"create {relpath}", _apply)


def append(relpath: str, text: str) -> Mutation:
    def _apply(root: Path) -> None:
        target = root / relpath
        if not target.exists():
            raise SelfTestError(f"mutation target '{relpath}' does not exist")
        with target.open("a", encoding="utf-8") as fh:
            fh.write(text)

    return Mutation(f"append to {relpath}", _apply)


def rename(src: str, dst: str) -> Mutation:
    def _apply(root: Path) -> None:
        source = root / src
        if not source.exists():
            raise SelfTestError(f"cannot rename '{src}': it does not exist")
        source.rename(root / dst)

    return Mutation(f"rename {src} -> {dst}", _apply)


def remove(relpath: str) -> Mutation:
    def _apply(root: Path) -> None:
        target = root / relpath
        if not target.exists():
            raise SelfTestError(f"cannot remove '{relpath}': it does not exist")
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()

    return Mutation(f"remove {relpath}", _apply)


def make_al_corpus(dirname: str, *, broken: bool = False, empty: bool = False) -> Mutation:
    """Materialise an AL corpus inside the scratch tree.

    Built from tools/gate-fixtures/al-corpus (hand-written, tiny, committed) so
    the harness runs in CI where BC.History does not exist.
    """

    def _apply(root: Path) -> None:
        dest = root / dirname
        dest.mkdir(parents=True, exist_ok=True)
        if empty:
            return
        src = root / "tools" / "gate-fixtures" / "al-corpus"
        files = sorted(src.glob("*.al"))
        if not files:
            raise SelfTestError(
                "tools/gate-fixtures/al-corpus holds no .al files -- the corpus "
                "fixture is missing, so this case would parse nothing"
            )
        for path in files:
            shutil.copy2(path, dest / path.name)
        if broken:
            (dest / "zz_selftest_broken.al").write_text(
                "codeunit 50999 SelfTestBroken\n"
                "{\n"
                "    procedure P()\n"
                "    begin\n"
                "        @@@ this is not AL @@@\n"
                "    end;\n"
                "}\n",
                encoding="utf-8",
            )

    kind = "empty" if empty else ("broken" if broken else "clean")
    return Mutation(f"materialise {kind} AL corpus at {dirname}", _apply)


# --------------------------------------------------------------------------
# Cases
# --------------------------------------------------------------------------


@dataclass
class Case:
    id: str
    gate: str                       # path, relative to the scratch root
    why: str                        # what defect this proves the gate catches
    setup: Sequence[Mutation] = ()  # prepare the world (corpus, etc.)
    pre: Sequence[Sequence[str]] = ()   # commands run after setup, before the defect
    mutations: Sequence[Mutation] = ()  # the defect itself
    args: Sequence[str] = ()
    env: dict = field(default_factory=dict)
    path_prepend: str | None = None  # a gate-fixture dir to shadow `tree-sitter`
    must_contain: Sequence[str] = ()
    must_not_contain: Sequence[str] = ()
    # Assertions on a file the gate WROTE, keyed by path relative to the scratch
    # tree. A count is a weak expectation: "193 files changed, all the right node
    # types, counts consistent with a clean win" once described a wrong tree, and
    # a case asserting only that N moved would have passed it. Where a gate names
    # what it found, assert the NAME.
    must_contain_in: dict = field(default_factory=dict)
    # What this gate CANNOT see of the defect class, where that is knowable. A
    # detector that catches 5% of instances and reports nothing on the rest looks
    # identical to a complete one in a green run; this is where that gets said.
    blind_spot: str = ""
    expect_exit: str = "nonzero"     # "nonzero" | "zero"
    slow: bool = True                # runs the full validate-grammar.sh
    needs: Sequence[str] = ()        # environment prerequisites, see PREREQS


VALIDATE = "./validate-grammar.sh"
PAP = "./parse-al-parallel.sh"
HARNESS = "./tools/tree-harness.sh"

# A byte-identical duplicate of an existing key — the shape Task 10 found by
# hand. Line 382 is `declaration_body: $ => repeat1($._body_element),`; the
# mutation asserts that text is there rather than trusting the line number.
DUP_RULE_LINE = "    declaration_body: $ => repeat1($._body_element),"

SMUGGLED_ERROR_FIXTURE = """\
================================================================================
Smuggled ERROR fixture (gate self-test)
================================================================================
codeunit 50100 Broken { procedure P() begin @@@ end; }
--------------------------------------------------------------------------------

(source_file
  (ERROR))
"""

CASES: list[Case] = [
    # ---- validate-grammar.sh -------------------------------------------------
    Case(
        id="step2-broken-expectation",
        gate=VALIDATE,
        why="a corpus expectation that no longer matches the grammar",
        mutations=[sub(
            "test/corpus/namespace_case_insensitive_test.txt",
            r"\(codeunit_keyword\)", "(codeunit_keywordXX)",
        )],
        must_contain=["Some tests failed", "namespace_case_insensitive"],
        must_not_contain=["All validation checks passed"],
    ),
    Case(
        id="step2-3-corpus-vanished",
        gate=VALIDATE,
        why="the whole test corpus is gone; both steps used to report success over 0 files",
        mutations=[rename("test/corpus", "test/corpus-moved-away")],
        must_contain=[
            "Test suite ran 0 parses",
            "No test corpus files found",
        ],
        must_not_contain=["All tests passed", "in 0 test files"],
    ),
    Case(
        id="step3-smuggled-error-fixture",
        gate=VALIDATE,
        why="an ERROR fixture that is not on the deliberate-negative allow-list",
        mutations=[create(
            "test/corpus/zz_selftest_smuggled_error.txt", SMUGGLED_ERROR_FIXTURE,
        )],
        must_contain=[
            "Found unexpected ERROR/MISSING nodes",
            "zz_selftest_smuggled_error.txt",
        ],
        blind_spot="greps EXPECTED TREES for ERROR/MISSING text. It cannot see a "
                   "fixture that ought to error and does not, nor one whose "
                   "expected tree is simply wrong -- Tasks 7 and 8 shipped exactly "
                   "that, and both passed identically on the broken grammar",
    ),
    Case(
        id="step4-orphan-tool-fails",
        gate=VALIDATE,
        why="the orphan detector itself exits non-zero",
        mutations=[prepend("tools/find_unused_definitions.py", "raise SystemExit(3)\n")],
        must_contain=["Orphan detection script failed"],
        must_not_contain=["No orphaned rules"],
    ),
    Case(
        id="step4-label-drift",
        gate=VALIDATE,
        why="the label the shell greps for changes; this used to pass with exit 0",
        mutations=[sub(
            "tools/find_unused_definitions.py", r"Unused rules:", "Unreferenced rules:",
        )],
        must_contain=["Orphan report unreadable"],
        must_not_contain=["No orphaned rules", "All validation checks passed"],
    ),
    Case(
        id="step4-unreferenced-rule",
        gate=VALIDATE,
        why="a rule defined in grammar.js that nothing references",
        mutations=[sub(
            "grammar.js", r"\n  rules: \{\n",
            "\n  rules: {\n    zz_selftest_orphan_rule: $ => 'zzselftestorphan',\n",
            count=1,
        )],
        must_contain=["orphaned rule", "zz_selftest_orphan_rule"],
        must_not_contain=["No orphaned rules"],
        blind_spot="counts references by regex over grammar.js and test/, so a rule "
                   "reached only through a computed or aliased name reads as unused; "
                   "and the 24 'missing definitions' the tool also reports are not "
                   "wired into the gate at all",
    ),
    Case(
        id="step4-missing-helper",
        gate=VALIDATE,
        why="a helper script absent from the checkout must fail, not warn",
        mutations=[remove("tools/find_unused_definitions.py")],
        must_contain=["Orphan detection script not found"],
        must_not_contain=["All validation checks passed"],
    ),
    Case(
        id="step5-duplicate-rule-key",
        gate=VALIDATE,
        why="a repeated key in grammar.js's rules object (valid JS, silently kept last)",
        mutations=[sub(
            "grammar.js",
            re.escape(DUP_RULE_LINE) + r"\n",
            DUP_RULE_LINE + "\n" + DUP_RULE_LINE + "\n",
            count=1,
        )],
        must_contain=["Duplicate rule key(s) found", "declaration_body"],
    ),
    Case(
        id="step5b-field-shape-violated",
        gate=VALIDATE,
        why="a declared field shape that no longer matches node-types.json",
        # node-types.json is REGENERATED by Step 1, so mutating it cannot
        # survive to Step 5b. What the checker asserts is that the declared
        # shape and the generated one agree, so flipping the declared side
        # produces the same disagreement -- and a real, specific message.
        mutations=[sub(
            "tools/check-field-types.py",
            r"inv\('array_type', 'sizes', True,",
            "inv('array_type', 'sizes', False,",
            count=1,
        )],
        must_contain=["Field-shape invariant violations found", "array_type.sizes"],
    ),
    Case(
        id="step5c-fieldwalk-broken",
        gate=VALIDATE,
        why="fieldwalk.c stops compiling against the current parser",
        mutations=[prepend("tools/fieldwalk.c", "#error selftest-injected compile failure\n")],
        must_contain=["fieldwalk failed to compile", "selftest-injected compile failure"],
        needs=["fieldwalk"],
    ),
    Case(
        id="step8-baseline-missing",
        gate=VALIDATE,
        why="the grammar health baseline is absent; this reported success before Task 20",
        mutations=[remove(".grammar_baseline.json")],
        must_contain=["Grammar health baseline missing"],
        must_not_contain=["All validation checks passed"],
    ),
    Case(
        id="step6-broken-al-file",
        gate=VALIDATE,
        args=["--full"],
        why="one unparseable file in the AL corpus; Step 6 parsed nothing at all before",
        mutations=[make_al_corpus("selftest-corpus", broken=True)],
        env={"AL_PARSE_CORPUS": "./selftest-corpus", "PARSE_OUT_DIR": "."},
        must_contain=["AL parsing failed", "error file(s)"],
        must_not_contain=["All validation checks passed"],
    ),
    Case(
        id="step6-zero-file-corpus",
        gate=VALIDATE,
        args=["--full"],
        why="a corpus directory that exists but holds no .al files",
        mutations=[make_al_corpus("selftest-corpus", empty=True)],
        env={"AL_PARSE_CORPUS": "./selftest-corpus", "PARSE_OUT_DIR": "."},
        must_contain=["AL parse run"],
        must_not_contain=["All validation checks passed"],
    ),
    Case(
        id="step6-clean-corpus-passes",
        gate=VALIDATE,
        args=["--full"],
        why="the control: a clean corpus must PASS, so the failures above are not just noise",
        mutations=[make_al_corpus("selftest-corpus")],
        env={"AL_PARSE_CORPUS": "./selftest-corpus", "PARSE_OUT_DIR": "."},
        expect_exit="zero",
        must_contain=["AL parsing:", "0 errors", "All validation checks passed"],
        must_not_contain=["AL parsing failed"],
    ),
    # ---- parse-al-parallel.sh ------------------------------------------------
    Case(
        id="pap-syntax-error-file",
        gate=PAP,
        args=["./selftest-corpus", "."],
        why="a file with a syntax error must be reported as an error",
        mutations=[make_al_corpus("selftest-corpus", broken=True)],
        env={"PARSE_OUT_DIR": "."},
        must_contain=["Errors       : 1"],
        must_not_contain=["Success rate : 100.0%"],
        # The count alone is a weak assertion -- 1 error is 1 error whichever
        # file it came from. errors.txt has to name the file that is actually
        # broken, which is what a caller acts on.
        must_contain_in={"errors.txt": ["zz_selftest_broken.al"]},
        blind_spot="sees only what tree-sitter flags as ERROR/MISSING; AL that "
                   "parses cleanly but means the wrong thing is invisible here",
        slow=False,
    ),
    Case(
        id="pap-dead-chunk",
        gate=PAP,
        args=["./selftest-corpus", ".", "4", "2"],
        why="a chunk whose tree-sitter dies outright; reported 100% before the JSON count",
        mutations=[make_al_corpus("selftest-corpus")],
        env={"PARSE_OUT_DIR": "."},
        path_prepend="tools/gate-fixtures/chunk-parse-failure",
        must_contain=[
            "chunk chunk_0001 produced 0 parse records",
            "did not parse every file they listed",
        ],
        must_not_contain=["Success rate"],
        slow=False,
    ),
    Case(
        id="pap-offsetting-loss",
        gate=PAP,
        args=["./selftest-corpus", ".", "4", "2"],
        why="one chunk loses records and another gains them, so the GLOBAL total reconciles",
        mutations=[make_al_corpus("selftest-corpus")],
        env={"PARSE_OUT_DIR": ".", "FIXTURE_DELTA": "1"},
        path_prepend="tools/gate-fixtures/json-offsetting-loss",
        must_contain=["did not parse every file they listed"],
        must_not_contain=["Success rate"],
        slow=False,
    ),
    Case(
        id="pap-empty-corpus",
        gate=PAP,
        args=["./selftest-corpus", "."],
        why="zero files enumerated; this printed a warning and exited 0",
        mutations=[make_al_corpus("selftest-corpus", empty=True)],
        env={"PARSE_OUT_DIR": "."},
        must_contain=["refusing to report on an empty corpus"],
        must_not_contain=["Success rate"],
        slow=False,
    ),
    # ---- tools/tree-harness.sh ----------------------------------------------
    Case(
        id="harness-one-tree-changed",
        gate=HARNESS,
        args=["verify", "./selftest-corpus", ".snap"],
        why="exactly one file's parse tree changes after the snapshot was taken",
        setup=[make_al_corpus("selftest-corpus")],
        pre=[["bash", "tools/tree-harness.sh", "snapshot", "./selftest-corpus", ".snap"]],
        # The mutation has to change the TREE, not just the text. An
        # s-expression tree carries node types and positions and no token text,
        # so editing `value(1; Closed)` to `value(2; Closed)` leaves a
        # byte-identical tree -- the first version of this case asserted a
        # MISMATCH that correctly never came. Adding a comment adds a node.
        mutations=[append("selftest-corpus/Status.Enum.al", "\n// selftest edit\n")],
        must_contain=["MISMATCH", "1 file(s) changed", "Status.Enum.al"],
        must_not_contain=["VERIFIED"],
        blind_spot="compares node types and positions, NOT token text. An edit that "
                   "changes only a token's spelling leaves a byte-identical tree and "
                   "is invisible -- the first version of this case asserted a "
                   "MISMATCH that correctly never came",
        slow=False,
    ),
    Case(
        id="harness-dead-chunk",
        gate=HARNESS,
        args=["snapshot", "./selftest-corpus", ".snap"],
        why="one chunk's tree-sitter dies, so its files are never parsed",
        setup=[make_al_corpus("selftest-corpus")],
        env={"CHUNK_SIZE": "2"},
        path_prepend="tools/gate-fixtures/chunk-parse-failure",
        must_contain=["chunk_0001", "desynced"],
        must_not_contain=["snapshot of"],
        slow=False,
    ),
    Case(
        id="harness-error-corpus-is-stable",
        gate=HARNESS,
        args=["verify", "./selftest-corpus", ".snap"],
        why="an ERROR-containing corpus must VERIFY against its own fresh snapshot"
            " -- tree-sitter's per-file diagnostic carries a millisecond timing, and"
            " it used to land inside the preceding tree's hashed bytes, so this"
            " reported a MISMATCH for files nobody had touched (Task 26)",
        setup=[make_al_corpus("selftest-corpus", broken=True)],
        pre=[["bash", "tools/tree-harness.sh", "snapshot", "./selftest-corpus", ".snap"]],
        expect_exit="zero",
        must_contain=["VERIFIED"],
        must_not_contain=["MISMATCH"],
        slow=False,
    ),
    # ---- tools/ts-lock.sh ----------------------------------------------------
    # Mutual exclusion was violated once by the RELEASE path, not the acquire
    # path: an exiting zombie deleted a lock belonging to a different, running
    # holder. Fixed in a739586; these two rows are its only automated coverage.
    # The subject here is the lock and the "gate" is the detector, so both
    # directions are pinned -- otherwise a detector that always says PASS would
    # look exactly like a correct one.
    Case(
        id="tslock-release-guard-detects",
        gate="./tools/gate-fixtures/ts-lock-release-guard.sh",
        why="ts-lock reverted to releasing unconditionally, so an exiting holder "
            "deletes a lock that now belongs to someone else",
        mutations=[sub(
            "tools/ts-lock.sh",
            r"trap ts_lock_release EXIT INT TERM",
            'trap \'rm -rf "$LOCK_DIR"\' EXIT INT TERM',
            count=1,
        )],
        must_contain=["FAIL", "deleted a lock owned by someone else"],
        must_not_contain=["PASS"],
        slow=False,
    ),
    Case(
        id="tslock-release-guard-passes",
        gate="./tools/gate-fixtures/ts-lock-release-guard.sh",
        why="the control: with the ownership token in place the exiting holder "
            "must leave the new owner's lock alone",
        expect_exit="zero",
        must_contain=["PASS", "left the new owner's lock intact"],
        must_not_contain=["FAIL"],
        blind_spot="exercises one holder and one takeover. It does not cover the "
                   "stale-breaker path, nor a holder killed without running its "
                   "trap at all",
        slow=False,
    ),
]


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------


def build_pristine(dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for name in COPY_FILES:
        src = REPO / name
        if not src.exists():
            raise SelfTestError(f"cannot build a scratch repo: '{name}' is missing")
        shutil.copy2(src, dest / name)
    for name in COPY_DIRS:
        src = REPO / name
        if not src.is_dir():
            raise SelfTestError(f"cannot build a scratch repo: '{name}/' is missing")
        shutil.copytree(src, dest / name)
    # The vendored tree-sitter runtime that Step 5c compiles against. Linked,
    # not copied: it is large and read-only here.
    #
    # This used to be a bare `except OSError: pass`, which is the exact fault
    # this file exists to catch. os.symlink needs Developer Mode or admin on
    # Windows, so the link silently did not happen, the scratch copy had no
    # .cache, Step 5c skipped itself with a warning, validate-grammar.sh passed,
    # and step5c-fieldwalk-broken failed with "exited 0" -- a case reporting on
    # a step that never ran. The fallback below is a directory JUNCTION, which
    # needs no privileges, and the prerequisite is now evaluated against the
    # scratch tree rather than against the repo, so a link that does not happen
    # produces an honest SKIP instead of a bogus verdict.
    cache = REPO / ".cache"
    if cache.exists():
        _link_dir(cache.resolve(), dest / ".cache")


def _link_dir(target: Path, link: Path) -> bool:
    try:
        os.symlink(target, link, target_is_directory=True)
        return True
    except OSError:
        pass
    if os.name == "nt":
        done = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return done.returncode == 0 and link.exists()
    return False


def _find_bash() -> str:
    """Absolute path to a bash that can actually run the gates.

    `subprocess.run(["bash", ...])` on Windows must NOT be left to resolve the
    name itself: CreateProcess searches System32 BEFORE PATH, and
    C:\\Windows\\System32\\bash.exe is the WSL launcher -- a different operating
    system, with a different PATH, no tree-sitter, and no idea what a Windows
    drive letter is. Every case would then fail for an environmental reason
    that looks nothing like the reason. `shutil.which` searches PATH in order
    and finds Git bash, so resolve it here and pass the absolute path.
    """
    explicit = os.environ.get("GATE_SELFTEST_BASH")
    if explicit:
        return explicit
    found = shutil.which("bash")
    if found and "system32" not in found.lower():
        return found
    for cand in (r"C:\Program Files\Git\bin\bash.exe",
                 r"C:\Program Files\Git\usr\bin\bash.exe"):
        if os.path.isfile(cand):
            return cand
    return found or "bash"


BASH = _find_bash()


def check_lock() -> None:
    """This harness is the repo's biggest source of parser invocations.

    Every case runs a gate that shells out to `tree-sitter`, and tree-sitter
    caches its compiled library by grammar NAME -- one `al.dll` shared by every
    worktree on the machine. Running unlocked while another stream is building
    corrupts both directions, and neither side errors; it just produces wrong
    answers. Wrapping the visible command is not enough either, as one stream
    found by generating fixtures with an unlocked `tree-sitter parse` nested
    inside a Python subprocess.

    Refuse only when the conflict is real -- someone else is holding the lock
    right now. With no lock at all (CI, a single-user machine) warn and carry
    on, because there is nothing to race.
    """
    if os.environ.get("TS_LOCK_ACTIVE"):
        return
    lock_dir = Path(os.environ.get("TS_LOCK_DIR")
                    or (os.environ.get("TMPDIR", "/tmp") + "/tree-sitter-al.buildlock"))
    if lock_dir.exists():
        owner = "unknown"
        try:
            owner = (lock_dir / "owner").read_text(encoding="utf-8").strip() or owner
        except OSError:
            pass
        raise SelfTestError(
            f"another holder has the shared parser lock ({owner}) and this run is "
            f"not inside it. Every case would race their build of al.dll, in both "
            f"directions, silently. Re-run as:  ./tools/ts-lock.sh python "
            f"tools/gate_selftest.py"
        )
    print("gate-selftest: NOTE - not running under ./tools/ts-lock.sh, and nothing "
          "else holds the lock. Safe only if no other checkout is building the "
          "parser right now.", flush=True)


def preflight() -> None:
    """Refuse to run at all if the shell cannot reach the tools the gates need.

    Otherwise every case fails identically and the output reads like 21 broken
    gates rather than one broken environment.
    """
    probe = subprocess.run([BASH, "-c", "command -v tree-sitter"],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if probe.returncode != 0:
        raise SelfTestError(
            f"the shell used to run gates ({BASH}) cannot find `tree-sitter`; "
            f"every case would fail for that reason and none of them would be "
            f"testing anything. Set GATE_SELFTEST_BASH to a shell that can."
        )


def _run_tree(cmd, *, cwd, env, timeout):
    """Run a gate, and on timeout kill its WHOLE PROCESS TREE.

    `subprocess.run(timeout=...)` kills only the direct child. Every gate here
    is a bash script that spawns tree-sitter, python and xargs workers, so a
    timeout would leave those running -- and they would go on parsing inside a
    scratch tree this harness has already deleted and recreated for the next
    case, against a mutation that no longer applies. Surviving children are a
    false-result generator, and it would be this harness generating them.

    Same shape as the incident where a stopped background task left ts-lock
    shells alive in their wait loops.
    """
    proc = subprocess.Popen(cmd, cwd=cwd, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        out, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_tree(proc)
        proc.communicate()
        raise
    return subprocess.CompletedProcess(cmd, proc.returncode, out, None)


def _kill_tree(proc) -> None:
    if os.name == "nt":
        # /T is the whole point: without it taskkill kills one process and
        # orphans the rest, which is exactly the failure being avoided.
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    import signal
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except OSError:
        proc.kill()


def _posix_path(path: Path) -> str:
    if os.name != "nt" or shutil.which("cygpath") is None:
        return str(path)
    try:
        out = subprocess.run(["cygpath", "-u", str(path)],
                             stdout=subprocess.PIPE, timeout=30, check=True)
        return out.stdout.decode().strip() or str(path)
    except (OSError, subprocess.SubprocessError):
        return str(path)


def _have_cc() -> bool:
    return (shutil.which(os.environ.get("CC", "cc")) is not None
            or shutil.which("gcc") is not None)


def _have_ts_runtime(root: Path) -> bool:
    """Is the vendored runtime reachable FROM THE SCRATCH TREE the case will use?

    Asking the repo instead was the bug: the repo has .cache, the scratch copy
    might not, and the case then ran against a Step 5c that had skipped itself.
    """
    cache = root / ".cache"
    return cache.exists() and any(cache.glob("tree-sitter-*/lib"))


# A case whose prerequisite is absent is SKIPPED and counted as skipped -- never
# silently passed, and never folded into the pass total. Step 5c skips itself
# without these, so a case asserting its failure message would otherwise fail
# for a reason that has nothing to do with the gate.
PREREQS = {
    "fieldwalk": (
        lambda work: _have_cc() and _have_ts_runtime(work),
        "needs a C compiler and a vendored tree-sitter runtime reachable at "
        ".cache/ in the scratch tree (run bindings/c/build.sh once)",
    ),
}


def _safe(text: str) -> str:
    """Make text printable on this console.

    A gate's output contains the U+2713 tick that print_success emits. On a
    Windows cp1252 console that raised UnicodeEncodeError from inside the
    FAILURE REPORT and killed the run -- so a single failing case destroyed the
    results of every case after it.
    """
    enc = (sys.stdout.encoding or "utf-8")
    return text.encode(enc, errors="replace").decode(enc, errors="replace")


def run_case(case: Case, workdir: Path, timeout: int) -> tuple[bool, str, str]:
    """Returns (passed, verdict, combined_output)."""
    gate_path = workdir / case.gate
    if not gate_path.exists():
        raise SelfTestError(
            f"case '{case.id}' names gate '{case.gate}', which does not exist in the "
            f"scratch repo -- refusing to record a result for a gate that was never run"
        )

    for mutation in case.setup:
        mutation.apply(workdir)

    env = dict(os.environ)
    env.update(case.env)
    if case.path_prepend:
        shim = workdir / case.path_prepend
        if not shim.is_dir():
            raise SelfTestError(
                f"case '{case.id}' needs fixture '{case.path_prepend}', which is not "
                f"in the scratch repo -- the fault would not have been injected"
            )
        # The gate runs under bash. On Windows that is MSYS bash, which splits
        # PATH on ':' -- a native "C:\..." entry would be read as two nonsense
        # directories and the shim would never be found, so the fault would
        # silently not be injected. Hand it a POSIX path where cygpath exists.
        env["PATH"] = _posix_path(shim) + os.pathsep + env.get("PATH", "")

    # Setup commands must SUCCEED. Their failure is a harness fault, not a
    # gate verdict -- a case whose snapshot never got taken would otherwise
    # "detect" a change that was really just an absent baseline.
    for pre_cmd in case.pre:
        pre_cmd = [BASH if a == "bash" else a for a in pre_cmd]
        done = subprocess.run(pre_cmd, cwd=workdir, env=env, timeout=timeout,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if done.returncode != 0:
            raise SelfTestError(
                f"case '{case.id}': setup command {pre_cmd!r} exited "
                f"{done.returncode}; the case was never put in the state it tests\n"
                + ANSI.sub("", done.stdout.decode("utf-8", errors="replace"))[-800:]
            )

    for mutation in case.mutations:
        mutation.apply(workdir)

    cmd = [BASH, case.gate, *case.args]
    try:
        proc = _run_tree(cmd, cwd=workdir, env=env, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, f"timed out after {timeout}s (process tree killed)", ""

    out = ANSI.sub("", proc.stdout.decode("utf-8", errors="replace"))

    problems = []
    if case.expect_exit == "nonzero" and proc.returncode == 0:
        problems.append("exited 0; expected non-zero")
    if case.expect_exit == "zero" and proc.returncode != 0:
        problems.append(f"exited {proc.returncode}; expected 0")
    for needle in case.must_contain:
        if needle not in out:
            problems.append(f"output never said {needle!r}")
    for needle in case.must_not_contain:
        if needle in out:
            problems.append(f"output still said {needle!r}")
    for relpath, needles in case.must_contain_in.items():
        target = workdir / relpath
        if not target.exists():
            problems.append(f"expected the gate to write {relpath}, which does not exist")
            continue
        body = target.read_text(encoding="utf-8", errors="replace")
        for needle in needles:
            if needle not in body:
                problems.append(f"{relpath} never named {needle!r}")

    if problems:
        return False, "; ".join(problems), out
    verdict = (f"exit {proc.returncode}, named the defect"
               if case.expect_exit == "nonzero"
               else f"exit {proc.returncode}, clean as required")
    return True, verdict, out


# --------------------------------------------------------------------------
# Structural sweep
#
# The mutation cases above prove that the failure paths a gate HAS can fire.
# This proves nothing new gets added that quietly cannot. Every construct that
# lets a gate decline to fail -- `|| true`, a discarded stderr, a warning where
# an error belongs -- must be listed in tools/gate-guards.tsv with a reason.
# An unlisted one fails the sweep; a listed one that has disappeared fails too,
# so the inventory cannot rot into a rubber stamp.
# --------------------------------------------------------------------------

GUARD_FILES = ["validate-grammar.sh", "parse-al-parallel.sh", "tools/tree-harness.sh"]
GUARD_PATTERN = re.compile(r"\|\|\s*true|2>\s*/dev/null|\|\|\s*echo|print_warning ")
GUARD_INVENTORY = Path("tools/gate-guards.tsv")


def _norm(line: str) -> str:
    return " ".join(line.split())


def find_guards(root: Path) -> dict[tuple[str, str], int]:
    found: dict[tuple[str, str], int] = {}
    for rel in GUARD_FILES:
        path = root / rel
        if not path.exists():
            raise SelfTestError(
                f"sweep target '{rel}' does not exist -- cannot sweep a file that is "
                f"not there, and reporting 0 guards for it would be a false clean"
            )
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            if GUARD_PATTERN.search(line):
                found[(rel, _norm(line))] = lineno
    return found


def load_inventory(root: Path) -> dict[tuple[str, str], str]:
    path = root / GUARD_INVENTORY
    if not path.exists():
        raise SelfTestError(f"guard inventory '{GUARD_INVENTORY}' is missing")
    entries: dict[tuple[str, str], str] = {}
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            raise SelfTestError(
                f"{GUARD_INVENTORY}:{lineno}: expected 3 tab-separated fields, got {len(parts)}"
            )
        entries[(parts[0], parts[1])] = parts[2]
    return entries


def sweep(root: Path) -> int:
    found = find_guards(root)
    inventory = load_inventory(root)

    # The sweep's own denominator. If the patterns stopped matching anything at
    # all, the sweep would pass over every file while examining nothing.
    if not found:
        print("gate-selftest: sweep matched 0 guards across "
              f"{len(GUARD_FILES)} files -- the patterns cannot be right",
              file=sys.stderr)
        return 1

    unjustified = sorted(k for k in found if k not in inventory)
    stale = sorted(k for k in inventory if k not in found)

    print(f"gate-selftest: sweep examined {len(GUARD_FILES)} gate scripts, "
          f"found {len(found)} degradation guard(s), inventory has {len(inventory)}")

    for rel, text in unjustified:
        print(f"  UNJUSTIFIED  {rel}:{found[(rel, text)]}  {text}")
    for rel, text in stale:
        print(f"  STALE ENTRY  {rel}  {text}")

    if unjustified:
        print("\nEvery guard that lets a gate decline to fail must be listed in "
              f"{GUARD_INVENTORY} with a reason. Add the line above, or remove the guard.",
              file=sys.stderr)
    if stale:
        print(f"\n{GUARD_INVENTORY} lists guards that are no longer in the source. "
              "Delete those rows so the inventory stays a description of the code.",
              file=sys.stderr)
    return 1 if (unjustified or stale) else 0


def select(pattern: str | None, quick: bool) -> list[Case]:
    cases = CASES
    if pattern:
        cases = [c for c in cases if pattern in c.id]
    if quick:
        cases = [c for c in cases if not c.slow]
    return cases


def prove_guards(scratch: Path) -> int:
    """Trip each anti-recursion guard on purpose and require it to fire."""
    checks = []

    work = scratch / "guard-missing-gate"
    build_pristine(work)
    checks.append((
        "a case naming a gate that does not exist",
        lambda: run_case(
            Case(id="_guard", gate="./no-such-gate.sh", why="guard"), work, 60,
        ),
        "does not exist in the scratch repo",
    ))

    work2 = scratch / "guard-inert-mutation"
    build_pristine(work2)
    checks.append((
        "a mutation whose pattern matches nothing",
        lambda: run_case(
            Case(
                id="_guard",
                gate="./validate-grammar.sh",
                why="guard",
                mutations=[sub("grammar.js", r"ThisTextIsNotInGrammarJs_zzz", "x")],
            ),
            work2, 60,
        ),
        "mutation matched nothing",
    ))

    failures = 0
    for label, thunk, expected in checks:
        try:
            thunk()
        except SelfTestError as exc:
            if expected in str(exc):
                print(f"  PASS  {label}\n          -> {exc}")
                continue
            print(f"  FAIL  {label}\n          raised the wrong error: {exc}")
            failures += 1
            continue
        print(f"  FAIL  {label}\n          the harness did not object")
        failures += 1

    # Zero selected cases must be fatal, not a clean run.
    if select("no-such-case-id-zzz", False):
        print("  FAIL  an impossible selector still matched cases")
        failures += 1
    else:
        print("  PASS  an impossible selector selects nothing (main() turns that into exit 1)")

    return failures


def main() -> int:
    # `(__doc__ or "")`: python -OO strips docstrings, and indexing [0] of an
    # empty split would take the harness down before it ran a single case.
    ap = argparse.ArgumentParser(
        description=((__doc__ or "gate self-test").splitlines() or ["gate self-test"])[0])
    ap.add_argument("-k", dest="pattern", help="only cases whose id contains this")
    ap.add_argument("--quick", action="store_true",
                    help="skip cases that run the full validate-grammar.sh")
    ap.add_argument("--list", action="store_true", help="list cases and exit")
    ap.add_argument("--prove-guards", action="store_true",
                    help="trip the harness's own guards and require them to fire")
    ap.add_argument("--sweep", action="store_true",
                    help="check every degradation guard in the gate scripts is justified")
    ap.add_argument("--write-inventory", action="store_true",
                    help="print an inventory skeleton for the guards found (fill in reasons)")
    ap.add_argument("--scratch", default=os.environ.get("GATE_SELFTEST_SCRATCH", ""),
                    help="scratch directory (default: a temp dir)")
    ap.add_argument("--timeout", type=int, default=900, help="per-case timeout, seconds")
    ap.add_argument("--keep", action="store_true", help="keep scratch trees for inspection")
    args = ap.parse_args()

    if args.list:
        blind = 0
        for case in CASES:
            tag = "slow" if case.slow else "fast"
            print(f"{case.id:32s} [{tag}] {case.gate:24s} {case.why}")
            if case.blind_spot:
                blind += 1
                print(f"{'':32s}   BLIND SPOT: {case.blind_spot}")
        print(f"\n{len(CASES)} cases, {blind} with a recorded blind spot")
        return 0

    if args.write_inventory:
        try:
            for (rel, text), lineno in sorted(find_guards(REPO).items()):
                print(f"{rel}\t{text}\tTODO justify ({rel}:{lineno})")
        except SelfTestError as exc:
            print(f"gate-selftest: {exc}", file=sys.stderr)
            return 2
        return 0

    if args.sweep:
        try:
            return sweep(REPO)
        except SelfTestError as exc:
            print(f"gate-selftest: {exc}", file=sys.stderr)
            return 2

    scratch = Path(args.scratch) if args.scratch else Path(
        os.environ.get("TMPDIR", "/tmp")) / f"gate-selftest-{os.getpid()}"
    scratch.mkdir(parents=True, exist_ok=True)

    try:
        if args.prove_guards:
            print("Proving the harness's own guards fire:")
            failures = prove_guards(scratch)
            print()
            if failures:
                print(f"gate-selftest: {failures} guard(s) did not fire -- the harness "
                      f"cannot be trusted to report a real failure")
                return 1
            print("gate-selftest: all guards fired")
            return 0

        check_lock()
        preflight()
        cases = select(args.pattern, args.quick)
        if not cases:
            print("gate-selftest: 0 cases selected -- refusing to report a clean run "
                  "over an empty registry", file=sys.stderr)
            return 1

        print(f"gate-selftest: {len(cases)} case(s), scratch {scratch}", flush=True)
        passed = skipped = failed = 0
        for case in cases:
            # Build first, then test prerequisites AGAINST THE SCRATCH TREE --
            # the repo having a C toolchain says nothing about whether the copy
            # the gate will actually run in can see it.
            work = scratch / case.id
            build_pristine(work)
            unmet = [n for n in case.needs if not PREREQS[n][0](work)]
            if unmet:
                why = "; ".join(PREREQS[n][1] for n in unmet)
                print(f"  SKIP  {case.id:32s}        {why}", flush=True)
                skipped += 1
                shutil.rmtree(work, ignore_errors=True)
                continue
            started = time.time()
            ok, verdict, out = run_case(case, work, args.timeout)
            took = time.time() - started
            if ok:
                print(f"  PASS  {case.id:32s} {took:5.1f}s  {verdict}", flush=True)
                passed += 1
                if not args.keep:
                    shutil.rmtree(work, ignore_errors=True)
            else:
                print(_safe(f"  FAIL  {case.id:32s} {took:5.1f}s  {verdict}"), flush=True)
                print(_safe(f"        injected: {case.why}"))
                for line in out.splitlines()[-12:]:
                    print(_safe(f"        | {line}"))
                failed += 1

        print()
        # The denominator, asserted rather than merely printed.
        if passed + failed + skipped != len(cases):
            print("gate-selftest: case accounting does not add up -- refusing to report",
                  file=sys.stderr)
            return 1
        if passed + failed == 0:
            print("gate-selftest: every case was skipped -- that is not a pass",
                  file=sys.stderr)
            return 1
        print(f"gate-selftest: {passed} passed, {failed} failed, {skipped} skipped, "
              f"of {len(cases)} selected")
        return 1 if failed else 0
    except SelfTestError as exc:
        print(f"gate-selftest: {exc}", file=sys.stderr)
        print("gate-selftest: this is a harness fault, not a gate result -- no verdict "
              "is being reported for any case", file=sys.stderr)
        return 2
    finally:
        if not args.keep and not args.scratch:
            shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
