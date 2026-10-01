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
    # Step 9 (WASM freshness, added in 4.0.1) verifies these two against
    # src/parser.c and src/scanner.c. Without them the scratch copy fails Step 9
    # with "missing tree-sitter-al.wasm", so the control case
    # step6-clean-corpus-passes could never exit 0 -- and nobody saw it, because
    # the job was already red for a different reason (exec bits, see
    # tools/check-exec-bits.sh). A gate the self-test cannot run clean is a gate
    # it cannot mutation-test either; step9-wasm-stale below needs these.
    "tree-sitter-al.wasm",
    "tree-sitter-al.wasm.inputs.sha256",
    # Step 11 (A6) reads every manifest that declares a tree-sitter runtime. A
    # missing one makes it exit 2, which failed the step6-clean-corpus-passes
    # control and let every expect-nonzero validate case pass for that reason.
    "pyproject.toml",
    "setup.py",
    "Cargo.toml",
    "go.mod",
    "Package.swift",
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


def git_corpus(dirname: str, label: str) -> Mutation:
    """Make a materialised corpus its own committed git repo and record its HEAD in the
    scratch production-classes.tsv, so the oracle's corpus identity check applies to it."""

    def _apply(root: Path) -> None:
        dest = root / dirname
        git = ["git", "-C", str(dest), "-c", "user.name=selftest", "-c", "user.email=selftest@invalid",
               "-c", "core.autocrlf=false"]
        for args in (["init", "-q"], ["add", "."], ["commit", "-q", "-m", "selftest corpus"]):
            if subprocess.run(git + args, capture_output=True).returncode:
                raise SelfTestError(f"cannot make {dirname} a git repo: git {' '.join(args)} failed")
        head = subprocess.run(git + ["rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        with (root / "tools/config_oracle/production-classes.tsv").open("a", encoding="utf-8") as fh:
            fh.write(f"# corpus-head {label} {head}\n")

    return Mutation(f"commit {dirname} as a git repo, record its head as {label}", _apply)


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
    expect_exit: str = "nonzero"     # "nonzero" | "zero" | an exact code, e.g. "2"
    slow: bool = True                # runs the full validate-grammar.sh
    needs: Sequence[str] = ()        # environment prerequisites, see PREREQS
    # A Python gate: run as `python -m <module> *args`. `gate` still names its file,
    # so the does-the-gate-exist guard applies to it the same as to a script.
    module: str | None = None


VALIDATE = "./validate-grammar.sh"
PAP = "./parse-al-parallel.sh"
HARNESS = "./tools/tree-harness.sh"

ORACLE = "tools/config_oracle/__main__.py"
ORACLE_MODULE = "tools.config_oracle"
# The first `for c in content:` in select.py is branch_select's loop over the CHOSEN
# arm (the second marks inactive-arm content). Reversing it keeps every node and
# byte, so only the comparator's structure check can see it.
ORACLE_REVERSED_ARM = sub("tools/config_oracle/lowering/select.py",
                          r"(?m)^            for c in content:$",
                          "            for c in reversed(content):", count=1)
ORACLE_STALE_ENTRY = ("preproc_define_undef_test.txt#Defined symbol used in a later %23if#0\tDEBUG=1"
                      "\tcannot-validate:reference-error\tdebt(C1): gate self-test, an entry left "
                      "behind after its record was fixed\n")

# A production refusal for the A4 cases: an unterminated #if, which the resolver refuses
# in both configurations. Stable on purpose: no handler or grammar fix can make it pass.
ORACLE_REFUSED = "Refused.Codeunit.al"
ORACLE_REFUSED_AL = "codeunit 50190 Refused\n{\n#if SELFTEST\n    procedure P()\n    begin\n    end;\n}\n"
ORACLE_REFUSED_ENTRY = ("selftest:Refused.Codeunit.al\t*\tcannot-validate:resolver:unbalanced-if"
                        "\tother: gate self-test, an unterminated #if\n")

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

# Steps 3b and 6b share one defect: 673528e (the `_directive_eol` whitespace fix)
# reverted, so an `#if A` line ending in `\f\n` leaves a HIDDEN MISSING
# `_directive_eol`. `tree-sitter parse` prints no MISSING for it and
# `--json-summary` says successful, so Step 6 (parse-al-parallel.sh) passes.
# `tree-sitter test` is NOT blind to it: its tree does print
# `(MISSING _directive_eol)`, so a fixture holding the input fails Step 2 too.
# Measured, not assumed: the first version of the 3b case asserted that Step 2
# passed, and it did not.
DIRECTIVE_EOL_FIX = (re.escape(r"while (lexer->lookahead != '\n' && is_extra_space(lexer->lookahead)) {")
                     + r"(\n\s*lexer->advance\(lexer, true\);\n\s*\}\n)")
# A re.sub replacement, so `\\t` is the two C characters `\t`. The pre-fix loop
# plus its separate `\r` step, exactly as 673528e^ had them.
DIRECTIVE_EOL_PRE_FIX = (r"while (lexer->lookahead == ' ' || lexer->lookahead == '\\t') {\1"
                         r"    if (lexer->lookahead == '\\r') {" "\n"
                         r"      lexer->advance(lexer, false);" "\n"
                         r"    }" "\n")
HIDDEN_MISSING_AL = "codeunit 1 T { trigger OnRun() begin\n#if A\f\nx := 1;\n#endif\nend; }\n"
HIDDEN_MISSING_FIXTURE = """\
================================================================================
Form feed before a directive's newline (gate self-test)
================================================================================
codeunit 1 T { trigger OnRun() begin
#if A\f
x := 1;
#endif
end; }
--------------------------------------------------------------------------------

(source_file
  (codeunit_declaration
    (codeunit_keyword)
    object_id: (integer)
    object_name: (identifier)
    body: (declaration_body
      (trigger_declaration
        (trigger_keyword)
        name: (identifier)
        body: (code_block
          (begin_keyword)
          body: (statement_block
            (preproc_conditional_statement
              (preproc_if
                (preproc_open)
                condition: (identifier))
              (assignment_statement
                left: (identifier)
                operator: (assignment_operator)
                right: (integer))
              (preproc_endif
                (preproc_close))))
          (end_keyword))))))
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
        id="step3b-hidden-missing-token",
        gate=VALIDATE,
        why="the _directive_eol whitespace fix (673528e) reverted, with a fixture "
            "whose #if line ends in a form feed: a hidden MISSING token",
        mutations=[
            sub("src/scanner.c", DIRECTIVE_EOL_FIX, DIRECTIVE_EOL_PRE_FIX, count=1),
            create("test/corpus/zz_selftest_hidden_missing.txt", HIDDEN_MISSING_FIXTURE),
        ],
        must_contain=[
            "has_error sweep found parse errors in the corpus fixtures",
            "hidden-only",
            "zz_selftest_hidden_missing.txt",
        ],
        must_not_contain=["All validation checks passed"],
        blind_spot="has_error is a yes/no per tree. A defect that builds a WRONG tree "
                   "with no ERROR and no MISSING token, hidden or not, passes it",
    ),
    Case(
        id="step3b-sweep-drops-a-case",
        gate=VALIDATE,
        why="the sweep silently reads one corpus case fewer than Step 2b declares; "
            "it still reports every input it DID read as clean",
        mutations=[sub(
            "tools/has_error_sweep.py",
            re.escape("for c in cases]"), "for c in cases[1:]]", count=1,
        )],
        must_contain=["has_error sweep over the corpus fixtures examined", "expected"],
        must_not_contain=["All validation checks passed"],
        blind_spot="reconciles the COUNT against Step 2b's independent reader. A sweep "
                   "that reads the right number of the wrong inputs passes",
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
        # Injected AFTER `source_file`, not before it. The FIRST entry in `rules`
        # is tree-sitter's start symbol, so prepending made the orphan the start
        # rule: every other rule became unreachable, the whole suite failed, and
        # validate-grammar.sh never reached Step 4 to report the orphan at all.
        # The case was then failing for a reason with nothing to do with orphan
        # detection -- it was testing start-rule displacement. `generate` still
        # succeeded, which is why it looked like a gate regression rather than a
        # miscalibrated mutation.
        mutations=[sub(
            "grammar.js", r"\n  rules: \{\n    source_file: ",
            "\n  rules: {\n    zz_selftest_orphan_rule: $ => 'zzselftestorphan',\n    source_file: ",
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
    # ---- the config oracle (roadmap A3) ----------------------------------------
    # Run as `python -m tools.config_oracle`, the command Step 5e and CI run, so each
    # case is fast; step5e-oracle-discrepancy proves the Step 5e wiring itself. Every
    # case builds the scratch tree's parser once (al.dll is not copied). Exit codes
    # are asserted exactly: 1 is a finding, 2 is could-not-run, and a case that
    # expects one must not pass on the other.
    Case(
        id="oracle-quick-planted-discrepancy",
        gate=ORACLE,
        module=ORACLE_MODULE,
        args=["run", "--tier", "quick"],
        why="branch selection lowers the chosen arm's children in reverse: a wrong "
            "lowered tree, which the comparator must report as a discrepancy",
        mutations=[ORACLE_REVERSED_ARM],
        expect_exit="1",
        must_contain=["- stage (c) fixture differential: FAIL (exit 1", "- discrepancy: ",
                      "- stage (a) registry census: PASS"],
        blind_spot="the fixture differential compares only configurations it can lower; "
                   "the ones classified cannot-validate in "
                   "tools/config_oracle/fixture-classes.tsv are compared for nothing",
        slow=False,
    ),
    Case(
        id="oracle-quick-unregistered-type",
        gate=ORACLE,
        module=ORACLE_MODULE,
        args=["run", "--tier", "quick"],
        why="a new named preproc_* type in the grammar that the oracle's registry does "
            "not know; the census reads the node-types.json the scratch build generated",
        mutations=[
            sub("grammar.js", r"(\n    \$\.preproc_undef,\n)",
                r"\1    $.preproc_zz_gate_selftest,\n", count=1),
            sub("grammar.js", r"(\n    preproc_region: \$ => )",
                r"\n    preproc_zz_gate_selftest: $ => '#zz-gate-selftest',\1", count=1),
        ],
        expect_exit="1",
        must_contain=["- stage (a) registry census: FAIL (1 problems)",
                      "unregistered: preproc_zz_gate_selftest",
                      "- stage (c) fixture differential: PASS"],
        blind_spot="the census keys on the `preproc` name prefix (plus "
                   "contracts.SPECIAL_NON_PREFIXED); a special type named otherwise is "
                   "invisible to it",
        slow=False,
    ),
    Case(
        id="oracle-quick-stale-classification",
        gate=ORACLE,
        module=ORACLE_MODULE,
        args=["run", "--tier", "quick"],
        why="a fixture-classes.tsv entry left behind for a configuration that passes",
        mutations=[append("tools/config_oracle/fixture-classes.tsv", ORACLE_STALE_ENTRY)],
        expect_exit="1",
        must_contain=["- stage (c) fixture differential: FAIL (exit 1",
                      "- stale classifications: 1",
                      "Defined symbol used in a later %23if#0\tDEBUG=1"],
        slow=False,
    ),
    Case(
        id="oracle-quick-dropped-configuration",
        gate=ORACLE,
        module=ORACLE_MODULE,
        args=["run", "--tier", "quick"],
        why="a worker loses the first configuration of every input: the runner must "
            "call that incomplete (exit 2), never count what is left as a clean run",
        mutations=[sub("tools/config_oracle/runner.py",
                       re.escape("return check_input(_PARSER, input_id, source, mode), peak_rss_bytes()"),
                       "return check_input(_PARSER, input_id, source, mode)[1:], peak_rss_bytes()",
                       count=1)],
        expect_exit="2",
        must_contain=["- stage (c) fixture differential: COULD NOT RUN", "IncompleteRun",
                      "- quick tier exit code: 2"],
        must_not_contain=["- stage (c) fixture differential: PASS"],
        slow=False,
    ),
    Case(
        id="oracle-quick-clean-passes",
        gate=ORACLE,
        module=ORACLE_MODULE,
        args=["run", "--tier", "quick"],
        why="the control: an unmodified tree passes every stage, so the RED cases "
            "above are red for their mutation and not for the environment",
        expect_exit="0",
        must_contain=["- stage (a) registry census: PASS", "- stage (b) self-tests: PASS (",
                      "- stage (c) fixture differential: PASS", "- quick tier exit code: 0"],
        slow=False,
    ),
    Case(
        id="oracle-resolve-empty-root",
        gate=ORACLE,
        module=ORACLE_MODULE,
        args=["run", "--tier", "resolve", "--root", "selftest-corpus", "--root", "selftest-empty"],
        why="an empty corpus root beside a healthy one; the healthy root alone passes",
        setup=[make_al_corpus("selftest-corpus"), make_al_corpus("selftest-empty", empty=True)],
        expect_exit="2",
        must_contain=["corpus root has no .al files: selftest-empty"],
        must_not_contain=["Per root"],
        slow=False,
    ),
    Case(
        id="oracle-resolve-healthy-root-passes",
        gate=ORACLE,
        module=ORACLE_MODULE,
        args=["run", "--tier", "resolve", "--root", "selftest-corpus"],
        why="the control for the empty-root case: the same healthy root on its own "
            "passes, and the per-root table accounts for every file",
        setup=[make_al_corpus("selftest-corpus")],
        expect_exit="0",
        must_contain=["| selftest-corpus | 6 | 2 | 2 | 0 | 0 | 0 | 0 |", "- exit code: 0"],
        slow=False,
    ),
    # ---- production classifications (roadmap A4) ----
    # The corpus sits at selftest-corpus, the one TEST-ONLY label in
    # tools/config_oracle/__main__.py's CORPORA, so these run the production path as it is.
    # The real production-classes.tsv entries name other corpora: never applied, never stale.
    Case(
        id="oracle-full-classified-refusal-passes",
        gate=ORACLE,
        module=ORACLE_MODULE,
        args=["run", "--tier", "full", "--root", "selftest-corpus"],
        why="a production corpus whose one refusal is classified exits 0, and the "
            "classified configurations still count as not validated",
        setup=[make_al_corpus("selftest-corpus"), create("selftest-corpus/" + ORACLE_REFUSED, ORACLE_REFUSED_AL)],
        mutations=[append("tools/config_oracle/production-classes.tsv", ORACLE_REFUSED_ENTRY)],
        expect_exit="0",
        must_contain=["- validated (pass): 2\n", "- not validated, classified by category: 2 (other 2)",
                      "  - `selftest:Refused.Codeunit.al SELFTEST=0`: other: gate self-test",
                      "- not validated, unclassified: 0", "- stale classifications: 0",
                      "- exit code: 0"],
        slow=False,
    ),
    Case(
        id="oracle-full-unclassified-refusal",
        gate=ORACLE,
        module=ORACLE_MODULE,
        args=["run", "--tier", "full", "--root", "selftest-corpus"],
        why="the same corpus without its classification: a new production refusal exits 1",
        setup=[make_al_corpus("selftest-corpus")],
        mutations=[create("selftest-corpus/" + ORACLE_REFUSED, ORACLE_REFUSED_AL)],
        expect_exit="1",
        must_contain=["- not validated, unclassified: 2", "- exit code: 1"],
        slow=False,
    ),
    Case(
        id="oracle-full-stale-production-entry",
        gate=ORACLE,
        module=ORACLE_MODULE,
        args=["run", "--tier", "full", "--root", "selftest-corpus"],
        why="a production-classes.tsv entry for a configuration that passes is stale",
        setup=[make_al_corpus("selftest-corpus"), create("selftest-corpus/" + ORACLE_REFUSED, ORACLE_REFUSED_AL)],
        mutations=[append("tools/config_oracle/production-classes.tsv", ORACLE_REFUSED_ENTRY
                          + "selftest:Guarded.Codeunit.al\tCLEAN25=0\tcannot-validate:resolver"
                            "\tother: gate self-test, an entry left behind\n")],
        expect_exit="1",
        must_contain=["- stale classifications: 1", "selftest:Guarded.Codeunit.al\tCLEAN25=0",
                      "- exit code: 1"],
        slow=False,
    ),
    Case(
        id="oracle-resolve-dirty-tracked-al",
        gate=ORACLE,
        module=ORACLE_MODULE,
        args=["run", "--tier", "resolve", "--root", "selftest-corpus"],
        why="a tracked .al edited under an unchanged, recorded HEAD: the oracle reads the "
            "working tree, so its content-free keys could keep classifying a changed file",
        setup=[make_al_corpus("selftest-corpus"), git_corpus("selftest-corpus", "selftest")],
        mutations=[append("selftest-corpus/Runner.Codeunit.al", "// edited after the commit\n")],
        expect_exit="1",
        must_contain=["tracked .al changed in the working tree (M Runner.Codeunit.al)",
                      "## Corpus identity mismatch (exit 1)"],
        blind_spot="files inside a submodule of the corpus: the check runs git in the corpus "
                   "repo only",
        slow=False,
    ),
    Case(
        id="step5e-oracle-discrepancy",
        gate=VALIDATE,
        why="the planted discrepancy of oracle-quick-planted-discrepancy, through "
            "validate-grammar.sh: Step 5e must fail the run",
        mutations=[ORACLE_REVERSED_ARM],
        must_contain=["config oracle quick tier failed (exit 1)",
                      "- stage (c) fixture differential: FAIL (exit 1"],
        must_not_contain=["All validation checks passed"],
    ),
    # ---- Step 9: wasm freshness -----------------------------------------------
    # The release workflow ships the committed wasm verbatim, so a source edit
    # without a rebuild is a stale parser for every web-tree-sitter consumer.
    # That happened between 4.0.0 and the next grammar fix with every other
    # gate green. The mutation edits src/scanner.c rather than src/parser.c
    # because Step 1 regenerates parser.c and would undo the edit; the stamp is
    # left alone because the defect is "sources moved, wasm did not", and the
    # stamp is the record of the wasm that exists.
    Case(
        id="step9-wasm-stale",
        gate=VALIDATE,
        why="src/scanner.c changed after the committed wasm was built; the shipped 4.0.0 wasm went stale this way with every gate green",
        mutations=[append("src/scanner.c", "\n// gate-selftest: scanner edit without a wasm rebuild\n")],
        must_contain=["Committed wasm is stale", "tree-sitter-al.wasm is stale"],
        must_not_contain=["All validation checks passed"],
        blind_spot="compares a stamp of the sources against the recorded one. A wasm "
                   "rebuilt from the right sources by a broken toolchain stamps clean",
    ),
    # ---- Step 11: declared runtime ranges against the grammar's ABI ----------
    Case(
        id="step11-stale-runtime-range",
        gate=VALIDATE,
        why="pyproject's core extra back at ~=0.24, the range A6 fixed: it admits "
            "py-tree-sitter 0.24.0 (ABI 13..14) for an ABI 15 grammar, so `pip install "
            "tree-sitter-al[core]` could resolve to a runtime that cannot load it",
        mutations=[sub("pyproject.toml", r'"tree-sitter~=0\.25"', '"tree-sitter~=0.24"', count=1)],
        must_contain=["Step 11: Runtime Ranges vs. Grammar ABI",
                      "Declared runtime range check failed (exit 1)",
                      "FAIL python     pyproject.toml [core]: tree-sitter~=0.24",
                      "admits 0.24.0..<0.25.0, which loads ABI 13..14, not 15"],
        must_not_contain=["All validation checks passed"],
        blind_spot="the runtime -> ABI table is hand-maintained: a future runtime release "
                   "that drops ABI 15 passes until someone adds it to the table",
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
        id="step6b-hidden-missing-token",
        gate=VALIDATE,
        args=["--full"],
        why="the same reverted scanner over an AL corpus file: Step 6 "
            "(parse-al-parallel.sh, --json-summary) reports 0 errors, only 6b sees it",
        mutations=[
            make_al_corpus("selftest-corpus"),
            create("selftest-corpus/zz_hidden_missing.al", HIDDEN_MISSING_AL),
            sub("src/scanner.c", DIRECTIVE_EOL_FIX, DIRECTIVE_EOL_PRE_FIX, count=1),
        ],
        env={"AL_PARSE_CORPUS": "./selftest-corpus", "PARSE_OUT_DIR": "."},
        # Step 6 passing is asserted, not tolerated: it is the blindness 6b closes.
        must_contain=[
            "AL parsing:", "0 errors",
            "has_error sweep found parse errors in ./selftest-corpus",
            "hidden-only", "zz_hidden_missing.al",
        ],
        must_not_contain=["AL parsing failed", "All validation checks passed"],
        blind_spot="has_error is a yes/no per tree. A defect that builds a WRONG tree "
                   "with no ERROR and no MISSING token, hidden or not, passes it",
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


def failing_steps(out: str) -> list[str]:
    """Every ✗ line of a gate's output, prefixed with the step header it sits under.

    The output tail is only the summary ("Some validation checks failed!"), which
    left a red control's cause to be guessed (step6-clean-corpus-passes: the
    stale wasm at Step 9, inferred for a round before anyone looked).
    """
    step, found = "", []
    for line in out.splitlines():
        s = line.strip()
        if s.startswith("Step "):
            step = s
        elif s.startswith("✗") and "Some validation checks failed" not in s:
            found.append(f"[{step}] {s[1:].strip()}" if step else s[1:].strip())
    return found


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

    cmd = ([sys.executable, "-m", case.module, *case.args] if case.module
           else [BASH, case.gate, *case.args])
    try:
        proc = _run_tree(cmd, cwd=workdir, env=env, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, f"timed out after {timeout}s (process tree killed)", ""

    # Python's text-mode stdout writes CRLF on Windows, so a `must_contain` that pins a
    # line end ("...: 2\n") matched on ubuntu and never here. Compare on LF.
    out = ANSI.sub("", proc.stdout.decode("utf-8", errors="replace")).replace("\r\n", "\n")

    problems = []
    if case.expect_exit == "nonzero" and proc.returncode == 0:
        problems.append("exited 0; expected non-zero")
    if case.expect_exit == "zero" and proc.returncode != 0:
        problems.append(f"exited {proc.returncode}; expected 0")
    if case.expect_exit.isdigit() and proc.returncode != int(case.expect_exit):
        problems.append(f"exited {proc.returncode}; expected {case.expect_exit}")
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
    verdict = (f"exit {proc.returncode}, clean as required"
               if case.expect_exit in ("zero", "0")
               else f"exit {proc.returncode}, named the defect")
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
                # The tail is only the summary; the failing steps are what say WHY.
                for line in failing_steps(out):
                    print(_safe(f"        ✗ {line}"))
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
