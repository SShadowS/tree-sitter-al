# Configuration-Consistency Oracle — Milestone 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first working slice of the configuration-consistency oracle. It must resolve `#if` configurations exactly as `alc` does, lower the multi-configuration tree for the milestone-1 special types, compare it against the single-configuration parse, and demonstrably catch replays 2, 3, 4 and 5.

**Architecture:** A Python package `tools/config_oracle/`, in the same style as `tools/query_coverage/`, with these stages:
- a byte-level directive resolver that never consults the grammar;
- an IR (ordered, field-labelled nodes with leaf provenance) extracted from both trees;
- a lowering engine driven by a hand-written, fail-closed registry, with typed fragments and per-leaf accounting;
- a comparator with three checks (byte coverage, structure, trivia);
- representation contracts on the multi-configuration tree;
- a runner that accounts for every (input, configuration).

**Tech Stack:** Python 3.13, py-tree-sitter 0.25.2, pytest ≥ 9, the `tree-sitter` CLI (0.26.x), and `alc` (`al compile`) for the probe task only.

**Spec:** `docs/superpowers/specs/2026-09-27-config-consistency-oracle-design.md`. Read it before starting any task: every design rule below comes from it.

## Global Constraints

- Python only, no new dependencies beyond `tools/query_coverage/requirements.txt` (`tree-sitter==0.25.2`, `pytest>=9.0`).
- Byte offsets everywhere. Never character offsets.
- The resolver (`directives.py`) must not import `tree_sitter` or anything under `tools/config_oracle/ir.py`, `reference.py` or `lowering/`.
- `lowering/` must not import `reference.py` and must not call any parser.
- No default handler: an unregistered special node type is `cannot-validate: unregistered-type`.
- Only one normalisation is allowed: removing an empty content-only container listed in `EMPTY_REMOVABLE`. Nothing else is flattened, re-sorted or merged.
- `cannot-validate` is never a pass and never skipped silently. Every (input, configuration) produces exactly one record.
- Directive semantics are exactly those recorded in `docs/preproc-directive-semantics.md` (Task 1). Nothing may be assumed beyond that table.
- Wrap every command that builds or runs the shared parser in `./tools/ts-lock.sh` when its output will be quoted (CLAUDE.md, *worktree and lock hazards*).
- Commit messages end with `[BC.History: 0 errors, 100.0% success]` after running `./parse-al-parallel.sh ./BC.History/ .`. This plan changes no grammar, so the number must stay unchanged.
- Run from the repo root `U:\Git\tree-sitter-al` in Git Bash. Tests: `python -m pytest tools/config_oracle/tests -q`.

## Review Focus

1. **A directive line that carries a trailing `// comment`.** `alc` accepts it. The resolver must mask the comment together with the line, and the comment must not appear in the trivia check or the coverage check on either side. The test belongs to Task 4.
2. **CRLF files.** The mask must keep every `\r`. Directive extents must end where the tree's `preproc_if` ends, which is after `\n`, and the `\r` must not be counted as significant. Tested in Tasks 4 and 9.
3. **A file whose only directives are `#region`/`#pragma` (no conditional).** It is not an oracle input. It must be counted as `no-directives`, not validated vacuously, and not crash. Tested in Task 15.
4. **A symbol that appears only in a `#define`, never in a condition.** It is not a free symbol, and must not double the number of configurations. Tested in Task 5.
5. **A split construct nested inside the active arm of another conditional.** Lowering must recurse through a selected arm into the special node, and accounting must still cover every leaf exactly once. Tested in Task 12, where `split_code_block_end` sits inside a `preproc_conditional_statement` arm.

---

## File structure

| File | Responsibility |
|---|---|
| `docs/preproc-directive-semantics.md` | Compiler-verified directive semantics, the source of every resolver control |
| `tools/config_oracle/__init__.py` | Package marker |
| `tools/config_oracle/__main__.py` | CLI entry: `run`, `replay` |
| `tools/config_oracle/probe_alc.py` | Re-runnable `alc` probe matrix with recorded expectations (`--check`) |
| `tools/config_oracle/directives.py` | Condition parser/evaluator, line scanner, per-configuration resolution and masking, enumeration of configurations |
| `tools/config_oracle/ir.py` | `Node`, `Extra`, and extraction of the IR from a tree-sitter tree |
| `tools/config_oracle/reference.py` | Single-configuration parse → IR, with `reference-error` / `resolver-leak` detection |
| `tools/config_oracle/compare.py` | Coverage, structure and trivia checks; `Discrepancy` |
| `tools/config_oracle/contracts.py` | The registry: every special type, its kind, handler, host slots and policies |
| `tools/config_oracle/directive_check.py` | `directive-mismatch`: tree directive extents against source directive extents |
| `tools/config_oracle/representation.py` | Representation contracts on the multi-configuration tree |
| `tools/config_oracle/lowering/__init__.py` | Re-exports `lower_tree` |
| `tools/config_oracle/lowering/engine.py` | `Lowered`, the fragments, `Accounting`, `LoweringError`, the recursive `lower`, the consumers |
| `tools/config_oracle/lowering/select.py` | `split_arms`, the branch-select handler, token aliases, pragma-only |
| `tools/config_oracle/lowering/assemblers.py` | `split_code_block_end`, `split_case_statement_end`, `split_procedure` |
| `tools/config_oracle/fixtures.py` | Extract cases from `test/corpus` |
| `tools/config_oracle/fixture-classes.tsv` | Classification of deliberate-negative cases for each configuration |
| `tools/config_oracle/runner.py` | Discovery, worker pool, per-(input, configuration) accounting, reports, exit codes, peak memory |
| `tools/config_oracle/replay.py` | Building a parser from a historical commit or a grammar mutant; the replay table |
| `tools/config_oracle/tests/conftest.py` | `al_parser` fixture, IR builders |
| `tools/config_oracle/tests/test_*.py` | One test module per source module |
| `tools/count_corpus_cases.py` | Modify: add `cases(root)` that yields the runnable case names for each file |
| `tools/query_coverage/loader.py` | Modify: stamp `src/**/*.h`; serialise builds across processes |

---

### Task 0: Correct two spec statements found while planning

**Files:**
- Modify: `docs/superpowers/specs/2026-09-27-config-consistency-oracle-design.md`

The var-block contract in the spec is self-contradictory. It requires each arm without a `var_section` to hold "another structural child", yet `preproc_conditional_var_block` admits only `optional(var_section)` per arm (`grammar.js`, rule `preproc_conditional_var_block`), and a `var`/pragma group is declared legitimate. Replay 5 also needs `preproc_split_procedure` lowered in milestone 1.

- [ ] **Step 1: Replace the var-block contract bullet.** Find the bullet starting ``- `preproc_conditional_var_block`, **in the slot between a routine signature and its body**`` and replace the whole bullet with:

```markdown
- `preproc_conditional_var_block`, **in the slot between a routine signature and its body** (parents `procedure`, `trigger_declaration`, `preproc_split_procedure`, `preproc_split_procedure_preamble`): **at least one arm holds a `var_section`**. The grammar admits nothing else in an arm, so a group with no `var_section` in any arm is a `preproc_pragma_only` misread and is a violation. A group with `var` in its `#if` arm and only a pragma in its `#else` arm is legitimate, and a named positive control. The contract is host-scoped: it applies only in the slots listed, and a new host slot fails the registry census until it is classified.
```

- [ ] **Step 2: Move split procedure into milestone 1.** In the Milestones section, in item 1's first `Scope:` bullet, append `; the `split-procedure` assembler (any tail), which replay 5 needs so that its structure check can pass` before the final period. In item 2's `Scope:` bullet, change `split procedure with every tail form; ` to `split procedure's witness matrix over every tail form; `.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-09-27-config-consistency-oracle-design.md
git commit -m "docs(spec): fix self-contradictory var-block contract; split-procedure into milestone 1

[BC.History: 0 errors, 100.0% success]"
```

---

### Task 1: Probe tool and the directive-semantics table

**Files:**
- Create: `tools/config_oracle/__init__.py`
- Create: `tools/config_oracle/probe_alc.py`
- Create: `docs/preproc-directive-semantics.md`

These probes were run during planning (65 compiles, `alc` as installed on 2026-09-27). This task turns them into a committed, re-runnable instrument whose expectations are the recorded results. `--check` exits 1 if any outcome differs. It needs `alc`, so it is not part of pytest or CI.

- [ ] **Step 1: Create the package marker**

```python
# tools/config_oracle/__init__.py
"""Configuration-consistency oracle. See docs/superpowers/specs/2026-09-27-config-consistency-oracle-design.md."""
```

- [ ] **Step 2: Write `tools/config_oracle/probe_alc.py`**

```python
"""Re-runnable alc probes for AL conditional-directive semantics.

Each probe is a tiny project. Text that must be INACTIVE is `GARBAGE!! ;;; }{`:
alc does not parse inactive text, so a probe compiles iff the compiler selected
exactly the arms predicted. Every expectation below was recorded from alc on
2026-09-27 and is the source of truth for docs/preproc-directive-semantics.md.

    python -m tools.config_oracle.probe_alc --check     # exit 1 on any change
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

G = "GARBAGE!! ;;; }{"


def unit(trigger: str, top: str = "") -> str:
    return f"{top}codeunit 50100 Probe\n{{\n    trigger OnRun()\n    begin\n{trigger}\n    end;\n}}\n"


def cond(c: str) -> str:
    return unit(f"#if {c}\n        Message('t');\n#else\n        {G}\n#endif")


# (name, source, symbols, expected_accept)
PROBES: list[tuple[str, str, list[str], bool]] = [
    ("sanity", unit("        Message('x');"), [], True),
    ("garbage_active_control", unit(f"        {G}"), [], False),
    ("symbol_case_lower_src_upper_defined", cond("foo"), ["FOO"], False),
    ("symbol_case_exact", cond("FOO"), ["FOO"], True),
    ("and_true", cond("A and B"), ["A", "B"], True),
    ("and_false", cond("A and B"), ["A"], False),
    ("AND_upper_true", cond("A AND B"), ["A", "B"], True),
    ("ampamp_rejected", cond("A && B"), ["A", "B"], False),
    ("or_true", cond("A or B"), ["B"], True),
    ("or_false", cond("A or B"), [], False),
    ("pipepipe_rejected", cond("A || B"), ["B"], False),
    ("not_true", cond("not A"), [], True),
    ("NOT_upper_true", cond("NOT A"), [], True),
    ("not_false", cond("not A"), ["A"], False),
    ("bang_rejected", cond("!A"), [], False),
    ("paren_true", cond("(A)"), ["A"], True),
    ("xor_rejected", cond("A xor B"), ["A"], False),
    ("eqeq_rejected", cond("A == B"), [], False),
    ("true_literal", cond("true"), [], True),
    ("TRUE_literal", cond("TRUE"), [], True),
    ("false_literal", cond("false"), [], False),
    ("prec_or_and", cond("A or B and C"), ["A"], True),
    ("prec_and_or", cond("A and B or C"), ["C"], True),
    ("prec_not_and", cond("not A and B"), [], False),
    ("not_not", cond("not not A"), ["A"], True),
    ("not_paren", cond("not (A or B)"), [], True),
    ("two_words_rejected", cond("A B"), ["A"], False),
    ("empty_condition_rejected", cond(""), [], False),
    ("digit_symbol", cond("CLEAN25"), ["CLEAN25"], True),
    ("underscore_symbol", cond("_X1"), ["_X1"], True),
    ("elif_first_match", unit(f"#if A\n        Message('1');\n#elif A\n        {G}\n#else\n        {G}\n#endif"), ["A"], True),
    ("elif_second_arm", unit(f"#if B\n        {G}\n#elif A\n        Message('2');\n#elif A\n        {G}\n#else\n        {G}\n#endif"), ["A"], True),
    ("elif_trailing_line_comment", unit(f"#if B\n        {G}\n#elif A // c\n        Message('t');\n#endif"), ["A"], True),
    ("elif_without_condition_rejected", unit(f"#if B\n        {G}\n#elif\n        Message('t');\n#endif"), ["A"], False),
    ("if_after_code_rejected", unit("        Message('a'); #if A\n        Message('b');\n#endif"), ["A"], False),
    ("endif_after_code_rejected", unit("#if A\n        Message('b'); #endif"), ["A"], False),
    ("line_comment_on_if_else_endif", unit(f"#if A // c\n        Message('t');\n#else // c\n        {G}\n#endif // c"), ["A"], True),
    ("block_comment_on_if_rejected", unit("#if A /* c */\n        Message('t');\n#endif"), ["A"], False),
    ("block_comment_on_else_rejected", unit(f"#if A\n        Message('t');\n#else /* c */\n        {G}\n#endif"), ["A"], False),
    ("block_comment_on_endif_rejected", unit("#if A\n        Message('t');\n#endif /* c */"), ["A"], False),
    ("else_trailing_word_rejected", unit(f"#if A\n        Message('t');\n#else B\n        {G}\n#endif"), ["A"], False),
    ("unterminated_quote_inactive", unit("#if A\n        Message('t');\n#else\n        Message('abc\n#endif\n        Message('u');"), ["A"], True),
    ("unterminated_block_comment_inactive", unit("#if A\n        Message('t');\n#else\n        /* open\n#endif\n        Message('u');"), ["A"], True),
    ("unterminated_quote_active_control", unit("#if A\n        Message('abc\n#else\n        Message('t');\n#endif"), ["A"], False),
    ("if_inside_block_comment", unit("        /*\n#if A\n        */\n        Message('t');"), ["A"], True),
    ("if_inside_line_comment", unit("        // #if A\n        Message('t');"), ["A"], True),
    ("if_inside_verbatim_string", unit("        Message(@'line1\n#if A\nline2');"), ["A"], True),
    ("define_in_inactive_arm_no_effect", f"#if A\n#define B\n#endif\n#if B\n{G}\n#endif\n" + unit("        Message('t');"), [], True),
    ("define_in_active_arm_effect", f"#if A\n#define B\n#endif\n#if B\n{G}\n#endif\n" + unit("        Message('t');"), ["A"], False),
    ("undef_removes_assigned_symbol", f"#undef B\n#if B\n{G}\n#endif\n" + unit("        Message('t');"), ["B"], True),
    ("defined_symbol_case_sensitive", f"#define BAR\n#if bar\n{G}\n#endif\n" + unit("        Message('t');"), [], True),
    ("space_after_hash", unit(f"# if A\n        Message('t');\n# else\n        {G}\n# endif"), ["A"], True),
    ("tab_after_hash", unit(f"#\tif A\n        Message('t');\n#\telse\n        {G}\n#\tendif"), ["A"], True),
    ("upper_directive_words", unit(f"#IF A\n        Message('t');\n#ELSE\n        {G}\n#ENDIF"), ["A"], True),
    ("indented_directives", unit(f"        #if A\n        Message('t');\n        #else\n        {G}\n        #endif"), ["A"], True),
    ("nested_unreachable_arm", unit(f"#if A\n#if not A\n        {G}\n#endif\n        Message('t');\n#endif"), ["A"], True),
]


def compile_probe(workdir: Path, name: str, source: str, symbols: list[str]) -> tuple[str, bool, list[str]]:
    project = workdir / name
    shutil.rmtree(project, ignore_errors=True)
    project.mkdir(parents=True)
    (project / "Test.al").write_text(source, encoding="utf-8", newline="\n")
    (project / "app.json").write_text(json.dumps({
        "id": "11111111-2222-3333-4444-555555555555", "name": "Probe", "publisher": "Test",
        "version": "1.0.0.0", "platform": "1.0.0.0", "idRanges": [{"from": 50000, "to": 99999}],
        "runtime": "15.0", "target": "OnPrem", "preprocessorSymbols": symbols,
    }), encoding="utf-8")
    out = project / "test.app"
    result = subprocess.run(["al", "compile", f"/project:{project}", f"/out:{out}"],
                            capture_output=True, text=True)
    codes = sorted({c for c in re.findall(r"error (AL\d+)", result.stdout + result.stderr) if c != "AL1021"})
    return name, out.is_file(), codes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="exit 1 if any outcome differs from its recorded expectation")
    args = parser.parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="alc-probe-") as tmp:
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(lambda p: compile_probe(Path(tmp), p[0], p[1], p[2]), PROBES))
    expected = {name: exp for name, _, _, exp in PROBES}
    failures = 0
    for name, accepted, codes in results:
        ok = accepted == expected[name]
        failures += not ok
        print(f"{'ok  ' if ok else 'DIFF'} {name:42} {'ACCEPT' if accepted else 'REJECT'} {','.join(codes)}")
    if not results[0][1] or results[1][1]:
        print("probe project is broken: the sanity/garbage controls did not behave", file=sys.stderr)
        return 2
    return 1 if (args.check and failures) else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Run it**

Run: `python -m tools.config_oracle.probe_alc --check`
Expected: every line starts with `ok`, exit 0. If any line says `DIFF`, stop: the compiler's semantics differ from the planning run, and Task 3 must follow the new result, not this plan.

- [ ] **Step 4: Write `docs/preproc-directive-semantics.md`**

```markdown
# AL conditional-directive semantics (compiler-verified)

Established with `alc` on 2026-09-27 by `python -m tools.config_oracle.probe_alc --check`.
Every row is one or more probes in `PROBES`. Re-run the probe before relying on a row
after a compiler upgrade. The configuration-consistency oracle's resolver
(`tools/config_oracle/directives.py`) implements exactly this table; its tests are
derived from it, never from its own output.

Method: text that must be inactive is `GARBAGE!!`. alc does not parse inactive
text, so a probe compiles iff the compiler chose exactly the predicted arms. Each
positive probe has a control that must fail.

## Conditions

| Question | Answer | Probes |
|---|---|---|
| Are symbols case-sensitive? | **Yes**, both `preprocessorSymbols` and `#define`d symbols | `symbol_case_*`, `defined_symbol_case_sensitive` |
| Operators | `and`, `or`, `not`, parentheses. Keywords are case-insensitive (`AND`, `NOT`) | `and_*`, `or_*`, `not_*`, `paren_true` |
| Rejected operators | `&&`, `\|\|`, `xor` (AL0631); `!`, `==` (AL0629) | `*_rejected` |
| Precedence | `not` > `and` > `or` | `prec_*` |
| Literals | `true`, `false`, case-insensitive | `*_literal` |
| Malformed | empty condition, two operands with no operator, `#elif` with no condition: rejected | `two_words_rejected`, `empty_condition_rejected`, `elif_without_condition_rejected` |
| Symbol shape | `[A-Za-z_][A-Za-z0-9_]*` (digits and `_` allowed) | `digit_symbol`, `underscore_symbol` |
| A symbol spelled like an operator (`and`) | **Not established**: the probe did not discriminate. The resolver fails closed | — |

## Arms

| Question | Answer | Probes |
|---|---|---|
| `#elif` | First true arm wins; later true arms are inactive | `elif_*` |
| Nested arm no assignment selects | Legal; simply never active | `nested_unreachable_arm` |

## Directive lines

| Question | Answer | Probes |
|---|---|---|
| Directive after code on the same line | Rejected (AL0620): a directive must be the first token on its line | `*_after_code_rejected` |
| Whitespace | Leading indentation and spaces/tabs between `#` and the word are allowed | `space_after_hash`, `tab_after_hash`, `indented_directives` |
| Directive word case | Case-insensitive (`#IF`, `#ELSE`, `#ENDIF`) | `upper_directive_words` |
| Trailing `//` comment on `#if`, `#elif`, `#else`, `#endif` | Allowed | `line_comment_on_if_else_endif`, `elif_trailing_line_comment` |
| Trailing `/* */` comment on a directive | Rejected (AL0631) | `block_comment_on_*_rejected` |
| Extra token after `#else` | Rejected (AL0631) | `else_trailing_word_rejected` |

## Lexing

| Question | Answer | Probes |
|---|---|---|
| Inactive text | **Not lexed.** An unterminated `'` or `/*` in an inactive arm does not hide the next directive | `unterminated_*_inactive` |
| Active text | Lexed normally; an unterminated `'` in active text is an error | `unterminated_quote_active_control` |
| `#if` inside an active block comment, line comment, or multi-line verbatim string `@'…'` | Not a directive | `if_inside_*` |

## Symbol definition

| Question | Answer | Probes |
|---|---|---|
| `#define` inside an inactive arm | No effect | `define_in_inactive_arm_no_effect` |
| `#define` inside an active arm | Takes effect for later directives | `define_in_active_arm_effect` |
| `#undef` of a symbol set by `preprocessorSymbols` | Removes it | `undef_removes_assigned_symbol` |

Placement rules for `#define`/`#undef` (before the first token) are in
`docs/preproc-define-undef.md`; they are a linter concern, not the resolver's.
```

- [ ] **Step 5: Commit**

```bash
git add tools/config_oracle/__init__.py tools/config_oracle/probe_alc.py docs/preproc-directive-semantics.md
git commit -m "feat(oracle): alc directive-semantics probes and their recorded table

[BC.History: 0 errors, 100.0% success]"
```

---

### Task 2: Loader freshness and cross-process build lock; oracle test scaffolding

**Files:**
- Modify: `tools/query_coverage/loader.py` (`STAMPED_FILES`, `ensure_library`)
- Create: `tools/config_oracle/tests/__init__.py`, `tools/config_oracle/tests/conftest.py`
- Test: `tools/config_oracle/tests/test_loader_contract.py`

**Interfaces:**
- Produces: `loader.stamped_files(repo_root) -> list[Path]` (static list plus every `src/**/*.h`, sorted); `loader.build_lock(repo_root)` (context manager); conftest fixtures `al_parser`, `al_language`, and the IR builders `leaf(kind, start, end, named=False, field=None)` and `node(kind, *children, field=None, named=True)`.

- [ ] **Step 1: Write the failing test**

```python
# tools/config_oracle/tests/test_loader_contract.py
from pathlib import Path

from tools.query_coverage import loader


def test_every_header_under_src_is_stamped():
    stamped = {p.as_posix() for p in loader.stamped_files(loader.REPO_ROOT)}
    headers = {p.relative_to(loader.REPO_ROOT).as_posix() for p in (loader.REPO_ROOT / "src").rglob("*.h")}
    assert headers, "src/ has no headers? the glob is wrong"
    assert headers <= stamped
    assert "src/unicode_id.h" in stamped


def test_build_lock_is_exclusive(tmp_path):
    with loader.build_lock(tmp_path):
        assert (tmp_path / ".oracle-build.lock").is_dir()
        try:
            with loader.build_lock(tmp_path, timeout=0.2):
                raise AssertionError("second holder acquired the lock")
        except TimeoutError:
            pass
    assert not (tmp_path / ".oracle-build.lock").exists()
```

Also create:

```python
# tools/config_oracle/tests/__init__.py
```

```python
# tools/config_oracle/tests/conftest.py
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture(scope="session")
def al_language():
    from tools.query_coverage import loader
    return loader.load_language(loader.ensure_library(loader.REPO_ROOT))


@pytest.fixture(scope="session")
def al_parser(al_language):
    from tools.query_coverage import loader
    return loader.make_parser(al_language)
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tools/config_oracle/tests/test_loader_contract.py -q`
Expected: FAIL with `AttributeError: module 'tools.query_coverage.loader' has no attribute 'stamped_files'`.

- [ ] **Step 3: Implement in `loader.py`**

Add after `STAMPED_FILES`:

```python
def stamped_files(repo_root: Path) -> list[Path]:
    """STAMPED_FILES plus every header under src/, sorted.

    The C build includes src/unicode_id.h and src/tree_sitter/*.h; an edit to
    any of them changes the compiled parser without touching a stamped file,
    so the stamp must cover them too (spec section 4, "Runner").
    """
    headers = sorted(p.relative_to(repo_root) for p in (repo_root / "src").rglob("*.h"))
    return list(STAMPED_FILES) + [h for h in headers if h not in STAMPED_FILES]


@contextlib.contextmanager
def build_lock(repo_root: Path, timeout: float = 600.0):
    """Serialise ensure_library across processes (the oracle's worker pool).

    A directory, because mkdir is atomic on NTFS and POSIX alike (the same
    choice as tools/ts-lock.sh). Deliberately NOT ts-lock's directory: callers
    are often already running inside ts-lock, and re-acquiring it would deadlock.
    """
    lock = repo_root / ".oracle-build.lock"
    deadline = time.monotonic() + timeout
    while True:
        try:
            lock.mkdir()
            break
        except FileExistsError:
            if time.monotonic() > deadline:
                raise TimeoutError(f"build lock held: {lock}")
            time.sleep(0.1)
    try:
        yield
    finally:
        lock.rmdir()
```

Add `import contextlib` and `import time` to the imports. In `compute_stamp`, replace `for relative in STAMPED_FILES:` with `for relative in stamped_files(repo_root):`. Wrap the body of `ensure_library` after its fast-path check:

```python
    if not force and lib_path.is_file() and read_stamp(repo_root) == before_generate:
        return lib_path

    with build_lock(repo_root):
        # Another process may have finished the build while we waited.
        if not force and lib_path.is_file() and read_stamp(repo_root) == compute_stamp(repo_root):
            return lib_path
        ...  # the existing generate / build / write_stamp code, unchanged, indented one level
    return lib_path
```

Add `.oracle-build.lock/` to `.gitignore`.

- [ ] **Step 4: Run the new test and the whole existing qc suite**

Run: `python -m pytest tools/config_oracle/tests/test_loader_contract.py tools/query_coverage/tests -q`
Expected: all pass. The first run rebuilds `al.dll` once, because the stamp changed.

- [ ] **Step 5: Commit**

```bash
git add tools/query_coverage/loader.py tools/config_oracle/tests .gitignore
git commit -m "feat(oracle): stamp src headers, serialise library builds across processes

[BC.History: 0 errors, 100.0% success]"
```

---

### Task 3: Condition parser and evaluator

**Files:**
- Create: `tools/config_oracle/directives.py` (condition part)
- Test: `tools/config_oracle/tests/test_conditions.py`

**Interfaces:**
- Produces: `class ResolveError(Exception)` with `.reason: str`, `.offset: int`; `parse_condition(line: bytes, start: int, end: int) -> Condition`, where `Condition` has `.expr`, `.start`, `.end` (byte extent of the condition in the file, excluding whitespace and a trailing `//` comment) and `.symbols: frozenset[str]`; `evaluate(expr, env: frozenset[str]) -> bool`. The expression classes are `Sym(name)`, `Lit(value)`, `Not(operand)`, `And(left, right)` and `Or(left, right)`.

- [ ] **Step 1: Write the failing tests (all from the semantics table)**

```python
# tools/config_oracle/tests/test_conditions.py
import pytest

from tools.config_oracle.directives import ResolveError, evaluate, parse_condition


def cond(text: str):
    b = text.encode()
    return parse_condition(b, 0, len(b))


@pytest.mark.parametrize("text,env,expected", [
    ("A and B", {"A", "B"}, True),
    ("A and B", {"A"}, False),
    ("A AND B", {"A", "B"}, True),
    ("A or B", {"B"}, True),
    ("A or B", set(), False),
    ("not A", set(), True),
    ("NOT A", set(), True),
    ("not A", {"A"}, False),
    ("(A)", {"A"}, True),
    ("true", set(), True),
    ("TRUE", set(), True),
    ("false", set(), False),
    ("A or B and C", {"A"}, True),       # prec_or_and
    ("A and B or C", {"C"}, True),       # prec_and_or: and binds tighter
    ("not A and B", set(), False),       # prec_not_and: (not A) and B
    ("not not A", {"A"}, True),
    ("not (A or B)", set(), True),
    ("CLEAN25", {"CLEAN25"}, True),
    ("_X1", {"_X1"}, True),
])
def test_semantics_table(text, env, expected):
    assert evaluate(cond(text).expr, frozenset(env)) is expected


def test_symbols_are_case_sensitive():
    assert evaluate(cond("foo").expr, frozenset({"FOO"})) is False


@pytest.mark.parametrize("text,reason", [
    ("A && B", "unsupported-condition-token"),
    ("A || B", "unsupported-condition-token"),
    ("!A", "unsupported-condition-token"),
    ("A == B", "unsupported-condition-token"),
    ("A xor B", "unsupported-condition"),
    ("A B", "unsupported-condition"),
    ("", "empty-condition"),
    ("   // only a comment", "empty-condition"),
    ("A /* c */", "block-comment-on-directive"),
    ("and", "unsupported-condition"),   # a symbol spelled like an operator: not established, fail closed
])
def test_rejections_fail_closed(text, reason):
    with pytest.raises(ResolveError) as err:
        cond(text)
    assert err.value.reason == reason


def test_extent_excludes_whitespace_and_line_comment():
    line = b"  not (A or B)   // note"
    c = parse_condition(line, 0, len(line))
    assert line[c.start:c.end] == b"not (A or B)"
    assert c.symbols == frozenset({"A", "B"})
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tools/config_oracle/tests/test_conditions.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'tools.config_oracle.directives'`.

- [ ] **Step 3: Implement the condition half of `directives.py`**

```python
# tools/config_oracle/directives.py
"""Independent recognition and evaluation of AL conditional directives.

The semantics are the COMPILER's, recorded in docs/preproc-directive-semantics.md
and established by tools/config_oracle/probe_alc.py. Nothing here consults the
grammar or imports tree_sitter: a resolver that read the tree would let a
grammar bug hide itself (spec section 1).
"""
from __future__ import annotations

import re
from dataclasses import dataclass


class ResolveError(Exception):
    """A construct outside the probed semantics. Reported as cannot-validate."""

    def __init__(self, reason: str, offset: int, detail: str = ""):
        super().__init__(f"{reason} at byte {offset}{': ' + detail if detail else ''}")
        self.reason = reason
        self.offset = offset


@dataclass(frozen=True)
class Sym:
    name: str


@dataclass(frozen=True)
class Lit:
    value: bool


@dataclass(frozen=True)
class Not:
    operand: object


@dataclass(frozen=True)
class And:
    left: object
    right: object


@dataclass(frozen=True)
class Or:
    left: object
    right: object


@dataclass(frozen=True)
class Condition:
    expr: object
    start: int
    end: int
    symbols: frozenset


_TOKEN = re.compile(rb"[ \t]*(?:(?P<ident>[A-Za-z_][A-Za-z0-9_]*)|(?P<punct>[()])|(?P<comment>//.*)|(?P<block>/\*)|(?P<other>\S))")
_KEYWORDS = {b"and", b"or", b"not"}
_LITERALS = {b"true": True, b"false": False}


def _tokens(buf: bytes, start: int, end: int):
    pos = start
    out = []
    while pos < end:
        m = _TOKEN.match(buf, pos, end)
        if not m or m.end() == pos:
            break
        if m.group("comment") is not None:
            break
        if m.group("block") is not None:
            raise ResolveError("block-comment-on-directive", m.start("block"))
        if m.group("other") is not None:
            raise ResolveError("unsupported-condition-token", m.start("other"), m.group("other").decode("latin-1"))
        kind = "ident" if m.group("ident") is not None else "punct"
        out.append((kind, m.group(kind), m.start(kind), m.end(kind)))
        pos = m.end()
    return out


def parse_condition(buf: bytes, start: int, end: int) -> Condition:
    """Parse the condition occupying buf[start:end] (the text after `#if`/`#elif`)."""
    toks = _tokens(buf, start, end)
    if not toks:
        raise ResolveError("empty-condition", start)
    pos = 0
    symbols: set[str] = set()

    def peek_kw():
        if pos < len(toks) and toks[pos][0] == "ident":
            return toks[pos][1].lower()
        return None

    def primary():
        nonlocal pos
        if pos >= len(toks):
            raise ResolveError("unsupported-condition", end, "operand expected")
        kind, text, s, _ = toks[pos]
        if kind == "punct" and text == b"(":
            pos += 1
            inner = or_expr()
            if pos >= len(toks) or toks[pos][1] != b")":
                raise ResolveError("unsupported-condition", s, "unbalanced parenthesis")
            pos += 1
            return inner
        if kind == "ident" and text.lower() in _KEYWORDS:
            raise ResolveError("unsupported-condition", s, "operator where an operand is required")
        if kind == "ident":
            pos += 1
            if text.lower() in _LITERALS:
                return Lit(_LITERALS[text.lower()])
            symbols.add(text.decode("ascii"))
            return Sym(text.decode("ascii"))
        raise ResolveError("unsupported-condition", s)

    def unary():
        nonlocal pos
        if peek_kw() == b"not":
            pos += 1
            return Not(unary())
        return primary()

    def and_expr():
        nonlocal pos
        left = unary()
        while peek_kw() == b"and":
            pos += 1
            left = And(left, unary())
        return left

    def or_expr():
        nonlocal pos
        left = and_expr()
        while peek_kw() == b"or":
            pos += 1
            left = Or(left, and_expr())
        return left

    expr = or_expr()
    if pos != len(toks):
        raise ResolveError("unsupported-condition", toks[pos][2], "trailing token")
    return Condition(expr, toks[0][2], toks[-1][3], frozenset(symbols))


def evaluate(expr, env: frozenset) -> bool:
    if isinstance(expr, Sym):
        return expr.name in env
    if isinstance(expr, Lit):
        return expr.value
    if isinstance(expr, Not):
        return not evaluate(expr.operand, env)
    if isinstance(expr, And):
        return evaluate(expr.left, env) and evaluate(expr.right, env)
    if isinstance(expr, Or):
        return evaluate(expr.left, env) or evaluate(expr.right, env)
    raise TypeError(expr)
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tools/config_oracle/tests/test_conditions.py -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add tools/config_oracle/directives.py tools/config_oracle/tests/test_conditions.py
git commit -m "feat(oracle): condition parser/evaluator with compiler-verified semantics

[BC.History: 0 errors, 100.0% success]"
```

---

### Task 4: Line scanner, per-configuration resolution, and masking

**Files:**
- Modify: `tools/config_oracle/directives.py` (append)
- Test: `tools/config_oracle/tests/test_resolve.py`

**Interfaces:**
- Consumes: `parse_condition`, `evaluate`, `ResolveError` (Task 3).
- Produces:
  - `@dataclass(frozen=True) class Directive`: `kind` (`if|elif|else|endif|define|undef|pragma|region|endregion`), `hash` (offset of `#`), `line_start`, `keyword_end`, `cond: Condition | None`, `symbol: str | None`, `line_end` (offset of the `\r`/`\n` ending the line, or EOF), `next_line` (offset just after the `\n`, or EOF).
  - `@dataclass(frozen=True) class ExtraEvent`: `kind` (`comment|multiline_comment|pragma|preproc_region|preproc_endregion|preproc_define|preproc_undef`), `start`, `end`.
  - `@dataclass class Resolution`:
    - `env0: frozenset`, the assignment;
    - `masked: bytes`;
    - `active: bytearray` (1 = byte survives);
    - `directives: list[Directive]`, every conditional directive reached, active or not;
    - `arm_choice: dict[int, int | None]`, mapping each reached group's `#if` hash to the hash of the chosen arm directive, or None;
    - `extras: list[ExtraEvent]`, extras in active text, excluding directive lines consumed by masking;
    - `trace: list[str]`.
  - `resolve(source: bytes, env0: frozenset) -> Resolution`.

- [ ] **Step 1: Write the failing tests, with handwritten masks**

```python
# tools/config_oracle/tests/test_resolve.py
import pytest

from tools.config_oracle.directives import ResolveError, resolve

SRC = (b"a;\n"
       b"#if A // note\n"
       b"b;\n"
       b"#elif A\n"
       b"c;\n"
       b"#else\n"
       b"d;\n"
       b"#endif\n"
       b"e;\n")


def mask_of(src, env):
    return resolve(src, frozenset(env)).masked


def test_if_arm_selected_and_directive_lines_fully_masked_including_comment():
    assert mask_of(SRC, {"A"}) == (b"a;\n" + b" " * 13 + b"\n" + b"b;\n" + b" " * 7 + b"\n"
                                   + b"  \n" + b" " * 5 + b"\n" + b"  \n" + b" " * 6 + b"\n" + b"e;\n")


def test_elif_is_first_match_so_else_taken_when_A_unset():
    assert mask_of(SRC, set()) == (b"a;\n" + b" " * 13 + b"\n" + b"  \n" + b" " * 7 + b"\n"
                                   + b"  \n" + b" " * 5 + b"\n" + b"d;\n" + b" " * 6 + b"\n" + b"e;\n")


def test_offsets_are_preserved():
    for env in (set(), {"A"}):
        assert len(mask_of(SRC, env)) == len(SRC)


def test_crlf_is_kept_byte_for_byte():
    src = b"#if A\r\nx;\r\n#endif\r\n"
    assert mask_of(src, set()) == b"     \r\n  \r\n      \r\n"


def test_arm_choice_and_extents():
    r = resolve(SRC, frozenset({"A"}))
    first = r.directives[0]
    assert (first.kind, SRC[first.cond.start:first.cond.end]) == ("if", b"A")
    assert SRC[first.line_end:first.next_line] == b"\n"
    assert r.arm_choice == {first.hash: first.hash}


def test_nested_groups_inside_inactive_arm_are_not_reached():
    src = b"#if A\n#if B\nx;\n#endif\n#endif\n"
    r = resolve(src, frozenset())
    assert list(r.arm_choice) == [0]


def test_inactive_text_is_not_lexed():
    src = b"#if A\ny;\n#else\n  Message('abc\n  /* open\n#endif\nz;\n"
    r = resolve(src, frozenset({"A"}))
    assert r.masked.endswith(b"z;\n")


@pytest.mark.parametrize("src", [
    b"x;\n/*\n#if A\n*/\ny;\n",          # directive inside a block comment
    b"x;\n// #if A\ny;\n",               # inside a line comment
    b"M(@'l1\n#if A\nl2');\n",           # inside a multi-line verbatim string
])
def test_hash_inside_active_comment_or_verbatim_string_is_not_a_directive(src):
    r = resolve(src, frozenset({"A"}))
    assert r.directives == [] and r.masked == src


def test_directive_after_code_is_not_a_directive_and_fails_closed_only_if_unbalanced():
    r = resolve(b"x; #if A\ny;\n", frozenset({"A"}))
    assert r.directives == []


@pytest.mark.parametrize("src,reason", [
    (b"#if A\nx;\n", "unbalanced-if"),
    (b"#endif\n", "unbalanced-endif"),
    (b"#if A\n#else B\n#endif\n", "trailing-token"),
    (b"#if A\n#endif /* c */\n", "block-comment-on-directive"),
    (b"#ifx A\n#endif\n", "unknown-directive"),
    (b"#if A\n#else\n#elif B\n#endif\n", "elif-after-else"),
])
def test_malformed_fails_closed(src, reason):
    with pytest.raises(ResolveError) as err:
        resolve(src, frozenset())
    assert err.value.reason == reason


def test_define_only_takes_effect_when_active():
    src = b"#if A\n#define B\n#endif\n#if B\nx;\n#endif\n"
    assert resolve(src, frozenset()).masked.count(b"x;") == 0
    assert resolve(src, frozenset({"A"})).masked.count(b"x;") == 1


def test_undef_removes_assigned_symbol():
    src = b"#undef B\n#if B\nx;\n#endif\n"
    assert resolve(src, frozenset({"B"})).masked.count(b"x;") == 0


def test_extras_exclude_masked_directive_lines_and_inactive_text():
    src = b"// top\n#if A // on-directive\n/* in-arm */\n#else\n// inactive\n#endif\n#pragma warning disable X\n"
    r = resolve(src, frozenset({"A"}))
    assert [(e.kind, src[e.start:e.end]) for e in r.extras] == [
        ("comment", b"// top"), ("multiline_comment", b"/* in-arm */"), ("pragma", b"#pragma warning disable X"),
    ]


def test_leading_bom_is_kept():
    src = b"\xef\xbb\xbf#if A\nx;\n#endif\n"
    assert resolve(src, frozenset()).masked.startswith(b"\xef\xbb\xbf")
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tools/config_oracle/tests/test_resolve.py -q`
Expected: FAIL with `ImportError: cannot import name 'resolve'`.

- [ ] **Step 3: Implement (append to `directives.py`)**

```python
from dataclasses import field

_DIRECTIVE = re.compile(rb"[ \t]*#[ \t]*(?P<word>[A-Za-z]+)")
_WORDS = {b"if", b"elif", b"else", b"endif", b"define", b"undef", b"pragma", b"region", b"endregion"}
_EXTRA_KIND = {"pragma": "pragma", "region": "preproc_region", "endregion": "preproc_endregion",
               "define": "preproc_define", "undef": "preproc_undef"}
_SYMBOL = re.compile(rb"[ \t]+(?P<sym>[A-Za-z_][A-Za-z0-9_]*)[ \t]*(?://.*)?$")
_REST_EMPTY = re.compile(rb"[ \t]*(?://.*)?$")
_BLOCK_ON_LINE = re.compile(rb"[ \t]*/\*")


@dataclass(frozen=True)
class Directive:
    kind: str
    hash: int
    line_start: int
    keyword_end: int
    cond: Condition | None
    symbol: str | None
    line_end: int
    next_line: int


@dataclass(frozen=True)
class ExtraEvent:
    kind: str
    start: int
    end: int


@dataclass
class Resolution:
    env0: frozenset
    masked: bytes
    active: bytearray
    directives: list = field(default_factory=list)
    arm_choice: dict = field(default_factory=dict)
    extras: list = field(default_factory=list)
    trace: list = field(default_factory=list)


def _lines(src: bytes):
    """(line_start, line_end, next_line) for every line; line_end excludes \\r\\n."""
    pos, n = 0, len(src)
    while pos < n:
        nl = src.find(b"\n", pos)
        nxt = n if nl < 0 else nl + 1
        end = n if nl < 0 else nl
        if end > pos and src[end - 1:end] == b"\r":
            end -= 1
        yield pos, end, nxt
        pos = nxt


def _parse_directive(src: bytes, ls: int, le: int, nxt: int) -> Directive | None:
    if ls == 0 and src.startswith(b"\xef\xbb\xbf"):
        ls = 3                      # a leading BOM precedes the first line's text
    m = _DIRECTIVE.match(src, ls, le)
    if not m:
        return None
    word = m.group("word")
    after = m.end("word")
    if word.lower() not in _WORDS:
        raise ResolveError("unknown-directive", m.start(), word.decode("latin-1"))
    kind = word.lower().decode()
    hash_ = src.index(b"#", ls, le)
    cond = sym = None
    if kind in ("if", "elif"):
        cond = parse_condition(src, after, le)
    elif kind in ("else", "endif"):
        if _BLOCK_ON_LINE.match(src, after, le):
            raise ResolveError("block-comment-on-directive", after)
        if not _REST_EMPTY.match(src, after, le):
            raise ResolveError("trailing-token", after)
    elif kind in ("define", "undef"):
        sm = _SYMBOL.match(src, after, le)
        if not sm:
            raise ResolveError("malformed-define", after)
        sym = sm.group("sym").decode("ascii")
    return Directive(kind, hash_, ls, after, cond, sym, le, nxt)


class _Lexer:
    """Active-text lexer: tracks the states that can span a line."""

    NORMAL, BLOCK, VERBATIM = range(3)

    def __init__(self, src: bytes, extras: list):
        self.src, self.extras, self.state, self.open_at = src, extras, self.NORMAL, 0

    def line(self, ls: int, le: int) -> None:
        s, i = self.src, ls
        while i < le:
            if self.state == self.BLOCK:
                j = s.find(b"*/", i, le)
                if j < 0:
                    return
                self.extras.append(ExtraEvent("multiline_comment", self.open_at, j + 2))
                self.state, i = self.NORMAL, j + 2
            elif self.state == self.VERBATIM:
                j = s.find(b"'", i, le)
                while j >= 0 and s[j + 1:j + 2] == b"'":
                    j = s.find(b"'", j + 2, le)
                if j < 0:
                    return
                self.state, i = self.NORMAL, j + 1
            else:
                c = s[i:i + 1]
                if s.startswith(b"//", i):
                    self.extras.append(ExtraEvent("comment", i, le))
                    return
                if s.startswith(b"/*", i):
                    self.state, self.open_at, i = self.BLOCK, i, i + 2
                elif s.startswith(b"@'", i):
                    self.state, i = self.VERBATIM, i + 2
                elif c in (b"'", b'"'):
                    j = s.find(c, i + 1, le)
                    while c == b"'" and j >= 0 and s[j + 1:j + 2] == b"'":
                        j = s.find(c, j + 2, le)
                    i = le if j < 0 else j + 1
                else:
                    i += 1


@dataclass
class _Frame:
    if_hash: int
    parent_active: bool
    taken: bool
    active: bool
    seen_else: bool


def resolve(source: bytes, env0: frozenset) -> Resolution:
    """Resolve one configuration. `env0` is the assignment of preprocessorSymbols."""
    env = set(env0)
    active = bytearray(len(source))
    masked = bytearray(source)
    res = Resolution(env0=env0, masked=b"", active=active)
    lexer = _Lexer(source, res.extras)
    stack: list[_Frame] = []

    def current_active() -> bool:
        return stack[-1].active if stack else True

    lead = 3 if source.startswith(b"\xef\xbb\xbf") else 0

    def blank(a: int, b: int) -> None:
        for k in range(max(a, lead), b):
            if masked[k] not in (0x0D, 0x0A):
                masked[k] = 0x20

    for ls, le, nxt in _lines(source):
        here = current_active()
        d = None
        if not here or lexer.state == _Lexer.NORMAL:
            d = _parse_directive(source, ls, le, nxt)
        if d is not None and d.kind in ("if", "elif", "else", "endif"):
            res.directives.append(d)
            if d.kind == "if":
                taken = here and evaluate(d.cond.expr, frozenset(env))
                stack.append(_Frame(d.hash, here, taken, taken, False))
                if here:
                    res.arm_choice[d.hash] = d.hash if taken else None
            else:
                if not stack:
                    raise ResolveError(f"unbalanced-{d.kind}", d.hash)
                f = stack[-1]
                if d.kind == "elif":
                    if f.seen_else:
                        raise ResolveError("elif-after-else", d.hash)
                    f.active = f.parent_active and not f.taken and evaluate(d.cond.expr, frozenset(env))
                elif d.kind == "else":
                    if f.seen_else:
                        raise ResolveError("duplicate-else", d.hash)
                    f.seen_else = True
                    f.active = f.parent_active and not f.taken
                else:
                    stack.pop()
                if d.kind in ("elif", "else") and f.active:
                    f.taken = True
                    res.arm_choice[f.if_hash] = d.hash
            blank(ls, nxt)
            continue
        if not here:
            blank(ls, nxt)
            continue
        for k in range(ls, nxt):
            active[k] = 1
        if d is not None:  # define/undef/pragma/region/endregion in active text
            if d.kind == "define":
                env.add(d.symbol)
            elif d.kind == "undef":
                env.discard(d.symbol)
            res.extras.append(ExtraEvent(_EXTRA_KIND[d.kind], d.hash, le))
            continue
        lexer.line(ls, le)
    if stack:
        raise ResolveError("unbalanced-if", stack[-1].if_hash)
    if lexer.state != _Lexer.NORMAL:
        raise ResolveError("unterminated-active-" + ("comment" if lexer.state == _Lexer.BLOCK else "verbatim"), len(source))
    res.masked = bytes(masked)
    res.extras.sort(key=lambda e: e.start)
    return res
```

Blanked bytes, including the `\r\n` of a masked line, keep `active[k] == 0`; only surviving lines are marked active. Coverage (Task 7) treats `\r`/`\n` as whitespace, never as significant.

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tools/config_oracle/tests/test_resolve.py tools/config_oracle/tests/test_conditions.py -q`
Expected: all pass. If `test_if_arm_selected_and_directive_lines_fully_masked_including_comment` fails on the `+ b"  \n"` segments, re-check the expectation by hand: the masked `c;\n` line is two spaces and a newline.

- [ ] **Step 5: Commit**

```bash
git add tools/config_oracle/directives.py tools/config_oracle/tests/test_resolve.py
git commit -m "feat(oracle): per-configuration directive resolution with offset-preserving masks

[BC.History: 0 errors, 100.0% success]"
```

---

### Task 5: Enumerating configurations, discovery, arm coverage, and the first-match mutation

**Files:**
- Modify: `tools/config_oracle/directives.py` (append)
- Test: `tools/config_oracle/tests/test_configs.py`

**Interfaces:**
- Consumes: `resolve`, `Directive`, `ResolveError` (Task 4).
- Produces:
  - `discover(source) -> Discovery`, where `@dataclass class Discovery` has `directives: list[Directive]` (every conditional directive line in the file, found by lexing all text as active), `free_symbols: tuple[str, ...]` (sorted; the condition symbols never `#define`d or `#undef`d), `has_conditionals: bool`;
  - `configurations(disc) -> list[frozenset]`, all 2^n assignments in a deterministic order;
  - `config_id(env, free) -> str`, e.g. `"A=1,B=0"`, or `"-"` when there are no free symbols;
  - `arm_coverage(source, disc) -> list[int]`, the hashes of arm directives that no configuration selects.

- [ ] **Step 1: Write the failing tests**

```python
# tools/config_oracle/tests/test_configs.py
import pytest

from tools.config_oracle import directives as d


def test_define_only_symbol_is_not_free():
    src = b"#define DEBUG\n#if A and DEBUG\nx;\n#endif\n"
    disc = d.discover(src)
    assert disc.free_symbols == ("A",)
    assert len(d.configurations(disc)) == 2


def test_enumeration_is_exhaustive_and_ordered():
    disc = d.discover(b"#if B\n#endif\n#if A\n#endif\n")
    assert [d.config_id(e, disc.free_symbols) for e in d.configurations(disc)] == [
        "A=0,B=0", "A=0,B=1", "A=1,B=0", "A=1,B=1"]


def test_no_conditionals():
    disc = d.discover(b"#region R\nx;\n#endregion\n")
    assert disc.has_conditionals is False
    assert d.config_id(frozenset(), disc.free_symbols) == "-"


def test_unreachable_arm_is_reported():
    src = b"#if A\n#if not A\nx;\n#endif\n#endif\n"
    disc = d.discover(src)
    unreached = d.arm_coverage(src, disc)
    assert unreached == [src.index(b"#if not A")]


def test_first_match_mutation_is_caught(monkeypatch):
    """Spec section 1 'Resolver self-test': switching #elif to independent
    evaluation must fail a named case. This test IS that named case run under
    the mutation; it asserts the mutant produces the wrong mask."""
    src = b"#if A\none;\n#elif A\ntwo;\n#endif\n"
    good = d.resolve(src, frozenset({"A"})).masked
    assert b"one;" in good and b"two;" not in good

    real = d.resolve

    def independent_elif(source, env0):
        # Mutant: evaluate each #elif as if no earlier arm had been taken.
        r = real(source.replace(b"#elif", b"#endif\n#if"), env0)
        return r

    monkeypatch.setattr(d, "resolve", independent_elif)
    mutant = d.resolve(src, frozenset({"A"})).masked
    assert b"two;" in mutant, "the mutation did not change behaviour, so the named case cannot detect it"
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tools/config_oracle/tests/test_configs.py -q`
Expected: FAIL with `AttributeError: module 'tools.config_oracle.directives' has no attribute 'discover'`.

- [ ] **Step 3: Implement (append to `directives.py`)**

```python
import itertools


@dataclass
class Discovery:
    directives: list
    free_symbols: tuple
    has_conditionals: bool


def discover(source: bytes) -> Discovery:
    """Find every conditional directive line by lexing ALL text as active.

    Used for the symbol universe and for directive-mismatch (the tree parses
    every arm, so it must be compared against every arm's directives).
    """
    directives, cond_syms, defined = [], set(), set()
    lexer = _Lexer(source, [])
    for ls, le, nxt in _lines(source):
        dir_ = _parse_directive(source, ls, le, nxt) if lexer.state == _Lexer.NORMAL else None
        if dir_ is None:
            lexer.line(ls, le)
            continue
        if dir_.kind in ("if", "elif", "else", "endif"):
            directives.append(dir_)
            if dir_.cond is not None:
                cond_syms |= dir_.cond.symbols
        elif dir_.kind in ("define", "undef"):
            defined.add(dir_.symbol)
    if lexer.state != _Lexer.NORMAL:
        raise ResolveError("lexing-crosses-directive", len(source))
    free = tuple(sorted(cond_syms - defined))
    return Discovery(directives, free, any(x.kind == "if" for x in directives))


def configurations(disc: Discovery) -> list:
    names = disc.free_symbols
    return [frozenset(n for n, bit in zip(names, bits) if bit)
            for bits in itertools.product((0, 1), repeat=len(names))]


def config_id(env: frozenset, free: tuple) -> str:
    if not free:
        return "-"
    return ",".join(f"{n}={1 if n in env else 0}" for n in free)


def arm_coverage(source: bytes, disc: Discovery) -> list:
    arms = {x.hash for x in disc.directives if x.kind in ("if", "elif", "else")}
    chosen = set()
    for env in configurations(disc):
        chosen |= {h for h in resolve(source, env).arm_choice.values() if h is not None}
    return sorted(arms - chosen)
```

`arm_coverage` counts an `#if` arm as chosen only when `arm_choice` maps to it. A group whose `#if` is false and which has no `#else` selects nothing, and its `#if` arm is correctly unreached.

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tools/config_oracle/tests/test_configs.py -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add tools/config_oracle/directives.py tools/config_oracle/tests/test_configs.py
git commit -m "feat(oracle): free-symbol enumeration, discovery, arm coverage, first-match mutation

[BC.History: 0 errors, 100.0% success]"
```

---

### Task 6: The IR and extraction of the single-configuration parse

**Files:**
- Create: `tools/config_oracle/ir.py`, `tools/config_oracle/reference.py`
- Modify: `tools/config_oracle/tests/conftest.py` (IR builders)
- Test: `tools/config_oracle/tests/test_ir.py`

**Interfaces:**
- Produces:
  - `@dataclass class Node`: `kind: str`, `named: bool`, `field: str | None`, `start: int`, `end: int`, `children: list[Node]`, with methods `leaves() -> list[Node]` (in order), `leaf_intervals() -> tuple[tuple[int, int], ...]` and `copy(**changes) -> Node`;
  - `@dataclass(frozen=True) class Extra`: `kind`, `start`, `end`;
  - `ir.from_tree(tree) -> tuple[Node, list[Extra], list[str]]`, where the problems list holds `f"error@{start}"` / `f"missing@{start}"`;
  - `ir.recompute_span(node) -> Node`, which sets start/end from the leaves;
  - `reference.extract(parser, masked: bytes) -> ReferenceResult(root, extras, problems)`, where problems also include `f"resolver-leak:{kind}@{start}"`.

- [ ] **Step 1: Add the builders to conftest and write the failing tests**

Append to `tools/config_oracle/tests/conftest.py`:

```python
from tools.config_oracle.ir import Node


def leaf(kind, start, end, named=False, field=None):
    return Node(kind, named, field, start, end, [])


def node(kind, *children, field=None, named=True):
    kids = list(children)
    return Node(kind, named, field, kids[0].start if kids else 0, kids[-1].end if kids else 0, kids)
```

```python
# tools/config_oracle/tests/test_ir.py
from tools.config_oracle import ir, reference


def test_keyword_node_has_its_anonymous_child_as_the_leaf(al_parser):
    src = b"codeunit 1 T { }"
    root, extras, problems = ir.from_tree(al_parser.parse(src))
    assert problems == [] and extras == []
    decl = root.children[0]
    kw = decl.children[0]
    assert (kw.kind, kw.named, [c.kind for c in kw.children]) == ("codeunit_keyword", True, ["codeunit"])
    assert kw.children[0].named is False
    assert src[kw.leaves()[0].start:kw.leaves()[0].end] == b"codeunit"


def test_fields_are_recorded_on_children(al_parser):
    root, _, _ = ir.from_tree(al_parser.parse(b"codeunit 1 T { }"))
    decl = root.children[0]
    assert [(c.kind, c.field) for c in decl.children][:3] == [
        ("codeunit_keyword", None), ("integer", "object_id"), ("identifier", "object_name")]


def test_extras_are_separated(al_parser):
    src = b"// hi\ncodeunit 1 T { }"
    root, extras, _ = ir.from_tree(al_parser.parse(src))
    assert [(e.kind, src[e.start:e.end]) for e in extras] == [("comment", b"// hi")]
    assert all(l.kind != "comment" for l in root.leaves())


def test_reference_flags_errors_and_resolver_leaks(al_parser):
    assert reference.extract(al_parser, b"codeunit 1 T { ").problems
    leak = reference.extract(al_parser, b"#if A\ncodeunit 1 T { }\n#endif\n").problems
    assert any(p.startswith("resolver-leak:preproc_") for p in leak)
    assert reference.extract(al_parser, b"#pragma warning disable X\ncodeunit 1 T { }\n").problems == []
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tools/config_oracle/tests/test_ir.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'tools.config_oracle.ir'`.

- [ ] **Step 3: Implement**

```python
# tools/config_oracle/ir.py
"""The comparable form: ordered, field-labelled nodes with leaf provenance (spec section 2)."""
from __future__ import annotations

from dataclasses import dataclass, field, replace


@dataclass
class Node:
    kind: str
    named: bool
    field: str | None
    start: int
    end: int
    children: list = field(default_factory=list)

    def leaves(self) -> list:
        if not self.children:
            return [self]
        out = []
        stack = [iter(self.children)]
        while stack:
            nxt = next(stack[-1], None)
            if nxt is None:
                stack.pop()
            elif nxt.children:
                stack.append(iter(nxt.children))
            else:
                out.append(nxt)
        return out

    def leaf_intervals(self) -> tuple:
        return tuple((l.start, l.end) for l in self.leaves())

    def copy(self, **changes) -> "Node":
        return replace(self, **changes)


@dataclass(frozen=True)
class Extra:
    kind: str
    start: int
    end: int


def recompute_span(node: Node) -> Node:
    if node.children:
        node.start = node.children[0].start
        node.end = node.children[-1].end
    return node


def from_tree(tree):
    """Walk with a TreeCursor so fields on anonymous children are captured (like tools/edge-census.c)."""
    extras, problems = [], []
    cursor = tree.walk()

    def visit(field_name):
        n = cursor.node
        if n.is_extra:
            extras.append(Extra(n.type, n.start_byte, n.end_byte))
            return None
        if n.is_error:
            problems.append(f"error@{n.start_byte}")
        if n.is_missing:
            problems.append(f"missing@{n.start_byte}")
        out = Node(n.type, n.is_named, field_name, n.start_byte, n.end_byte, [])
        if cursor.goto_first_child():
            while True:
                child = visit(cursor.field_name)
                if child is not None:
                    out.children.append(child)
                if not cursor.goto_next_sibling():
                    break
            cursor.goto_parent()
        return out

    root = visit(None)
    return root, sorted(extras, key=lambda e: e.start), problems
```

```python
# tools/config_oracle/reference.py
"""The single-configuration parse, extracted as the comparator (spec section 2)."""
from __future__ import annotations

from dataclasses import dataclass

from tools.config_oracle import ir

_EXTRA_PREPROC = {"preproc_region", "preproc_endregion", "preproc_define", "preproc_undef"}


@dataclass
class ReferenceResult:
    root: ir.Node
    extras: list
    problems: list


def extract(parser, masked: bytes) -> ReferenceResult:
    root, extras, problems = ir.from_tree(parser.parse(masked))
    stack = [root]
    while stack:
        n = stack.pop()
        if n.kind.startswith("preproc") and n.kind not in _EXTRA_PREPROC:
            problems.append(f"resolver-leak:{n.kind}@{n.start}")
        stack.extend(n.children)
    return ReferenceResult(root, extras, problems)
```

Implementation note: `from_tree` recurses once per tree level. BC files nest to a depth of about 60, which is well under Python's default recursion limit. Leave it recursive.

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tools/config_oracle/tests/test_ir.py -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add tools/config_oracle/ir.py tools/config_oracle/reference.py tools/config_oracle/tests/conftest.py tools/config_oracle/tests/test_ir.py
git commit -m "feat(oracle): IR with leaf provenance; single-configuration reference extraction

[BC.History: 0 errors, 100.0% success]"
```

---

### Task 7: The comparator (coverage, structure, trivia) and its mutation self-test

**Files:**
- Create: `tools/config_oracle/compare.py`
- Test: `tools/config_oracle/tests/test_compare.py`

**Interfaces:**
- Consumes: `Node`, `Extra` (Task 6); `Resolution.active`, `Resolution.extras` (Task 4).
- Produces:
  - `@dataclass(frozen=True) class Discrepancy`: `check` (`coverage|structure|trivia`), `kind`, `path: str`, `detail: str`;
  - `coverage(source: bytes, active: bytearray, root: Node, extras: list[Extra], side: str) -> list[Discrepancy]`. `source` is the **original** file, never the masked text. On masked text an inactive byte is a space, so a lowered leaf wrongly covering inactive text would go unseen;
  - `structure(ref: Node, low: Node) -> list[Discrepancy]`;
  - `trivia(events, ref_extras, low_extras) -> list[Discrepancy]`;
  - `discrepancy_id(input_id, config, d) -> str`.

- [ ] **Step 1: Write the failing tests, one named kind per mutation**

```python
# tools/config_oracle/tests/test_compare.py
import copy

from tools.config_oracle import compare
from tools.config_oracle.tests.conftest import leaf, node
from tools.config_oracle.ir import Extra


def sample():
    # if_statement over "if c then a else b ;" at invented offsets
    return node("statement_block",
                node("if_statement",
                     leaf("if", 0, 2),
                     node("identifier", leaf("c", 3, 4, named=False), field="condition"),
                     leaf("then", 5, 9),
                     node("call_expression", leaf("a", 10, 11, named=True), field="then_branch"),
                     leaf("else", 12, 16),
                     node("call_expression", leaf("b", 17, 18, named=True), field="else_branch")),
                leaf(";", 19, 20))


def kinds(ds):
    return sorted({(d.check, d.kind) for d in ds})


def test_clean_control_passes():
    assert compare.structure(sample(), sample()) == []


def test_delete_is_missing():
    low = sample(); del low.children[0].children[5]
    assert ("structure", "missing") in kinds(compare.structure(sample(), low))


def test_duplicate_is_extra():
    low = sample(); low.children.append(leaf(";", 21, 22))
    assert ("structure", "extra") in kinds(compare.structure(sample(), low))


def test_reparent_keeping_type_and_span_is_parent():
    low = sample()
    call = low.children[0].children.pop(5)   # else_branch moved to statement_block
    low.children.insert(1, call)
    assert ("structure", "parent") in kinds(compare.structure(sample(), low))


def test_swapped_then_else_is_field():
    low = sample()
    t, e = low.children[0].children[3], low.children[0].children[5]
    t.field, e.field = e.field, t.field
    assert ("structure", "field") in kinds(compare.structure(sample(), low))


def test_renamed_kind_is_kind():
    low = sample(); low.children[0].children[3].kind = "call_statement"
    assert ("structure", "kind") in kinds(compare.structure(sample(), low))


def test_swapped_siblings_is_order():
    ref = node("statement_block", leaf("x", 0, 1, named=True), leaf("y", 2, 3, named=True))
    low = node("statement_block", leaf("y", 2, 3, named=True), leaf("x", 0, 1, named=True))
    assert kinds(compare.structure(ref, low)) == [("structure", "order")]


def test_identical_text_other_arm_provenance_is_detected():
    ref = node("statement_block", leaf("Foo", 10, 13, named=True))
    low = node("statement_block", leaf("Foo", 30, 33, named=True))   # same text, other arm
    assert ("structure", "missing") in kinds(compare.structure(ref, low))


def test_coverage_uncovered_double_masked():
    src = b"ab cd"
    active = bytearray([1, 1, 1, 1, 0])
    root = node("x", leaf("a", 0, 1), leaf("a", 0, 1), leaf("d", 4, 5))
    ks = kinds(compare.coverage(src, active, root, [], side="low"))
    assert ks == [("coverage", "double"), ("coverage", "masked"), ("coverage", "uncovered")]


def test_trivia_missing_event():
    events = [Extra("comment", 0, 4)]
    ks = kinds(compare.trivia(events, [Extra("comment", 0, 4)], []))
    assert ks == [("trivia", "missing")]


def test_ids_are_stable_and_distinct():
    a = compare.Discrepancy("structure", "missing", "if_statement.-@0", "")
    b = compare.Discrepancy("structure", "missing", "if_statement.-@9", "")
    assert compare.discrepancy_id("f#1", "A=1", a) != compare.discrepancy_id("f#1", "A=1", b)
    assert compare.discrepancy_id("f#1", "A=1", a) == compare.discrepancy_id("f#1", "A=1", copy.copy(a))
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tools/config_oracle/tests/test_compare.py -q`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

```python
# tools/config_oracle/compare.py
"""The three checks of spec section 2. Nodes are matched by PROVENANCE, never by text."""
from __future__ import annotations

from dataclasses import dataclass

_WS = frozenset(b" \t\r\n\f\v")
_BOM = b"\xef\xbb\xbf"


@dataclass(frozen=True)
class Discrepancy:
    check: str
    kind: str
    path: str
    detail: str


def discrepancy_id(input_id: str, config: str, d: Discrepancy) -> str:
    return f"{input_id}|{config}|{d.check}|{d.kind}|{d.path}"


def _runs(offsets):
    out, prev, start = [], None, None
    for o in offsets:
        if prev is None or o != prev + 1:
            if start is not None:
                out.append((start, prev + 1))
            start = o
        prev = o
    if start is not None:
        out.append((start, prev + 1))
    return out


def coverage(source, active, root, extras, side):
    count = [0] * len(source)
    spans = [(l.start, l.end) for l in root.leaves() if l.end > l.start] + [(e.start, e.end) for e in extras]
    for s, e in spans:
        for k in range(s, e):
            count[k] += 1
    lead = len(_BOM) if source.startswith(_BOM) else 0
    uncovered, double, masked = [], [], []
    for k, b in enumerate(source):
        significant = active[k] and b not in _WS and k >= lead
        if significant and count[k] == 0:
            uncovered.append(k)
        if count[k] > 1 and b not in _WS:
            double.append(k)
        if not active[k] and count[k] and b not in _WS:
            masked.append(k)
    out = []
    for kind, offs in (("uncovered", uncovered), ("double", double), ("masked", masked)):
        for s, e in _runs(offs):
            out.append(Discrepancy("coverage", kind, f"{side}@{s}", f"bytes {s}..{e}"))
    return sorted(out, key=lambda d: (d.kind, d.path))


def _index(root):
    idx = {}
    order = {}

    def walk(n, parent_key, path, same_chain):
        # SORTED leaf intervals: a node is identified by the material it covers,
        # so reordering its children is reported as `order`, not missing+extra.
        leafs = tuple(sorted(n.leaf_intervals()))
        first = leafs[0][0] if leafs else n.start
        depth = same_chain.get(leafs, 0)
        key = (first, leafs, depth)
        p = f"{path}/{n.kind}.{n.field or '-'}@{first}" if path else f"{n.kind}.{n.field or '-'}@{first}"
        idx[key] = (n, parent_key, p)
        chain = {leafs: depth + 1}
        order[key] = [walk(c, key, p, chain if tuple(sorted(c.leaf_intervals())) == leafs else {})
                      for c in n.children]
        return key

    walk(root, None, "", {})
    return idx, order


def structure(ref, low):
    ri, ro = _index(ref)
    li, lo = _index(low)
    out = []
    for key, (n, parent, path) in ri.items():
        if key not in li:
            if parent is None or parent in li:          # report the topmost missing node only
                out.append(Discrepancy("structure", "missing", path, n.kind))
            continue
        m, lparent, _ = li[key]
        if n.kind != m.kind or n.named != m.named:
            out.append(Discrepancy("structure", "kind", path, f"{n.kind} vs {m.kind}"))
        if n.field != m.field:
            out.append(Discrepancy("structure", "field", path, f"{n.field} vs {m.field}"))
        if parent != lparent:
            out.append(Discrepancy("structure", "parent", path, n.kind))
    for key, (m, parent, path) in li.items():
        if key not in ri and (parent is None or parent in ri):
            out.append(Discrepancy("structure", "extra", path, m.kind))
    for key, kids in ro.items():
        if key in lo:
            a = [k for k in kids if k in lo[key]]
            b = [k for k in lo[key] if k in kids]
            if a != b:
                out.append(Discrepancy("structure", "order", ri[key][2], ri[key][0].kind))
    return out


def trivia(events, ref_extras, low_extras):
    def keyed(xs):
        return sorted((x.kind, x.start) for x in xs)
    ev, rf, lw = keyed(events), keyed(ref_extras), keyed(low_extras)
    out = []
    for name, side in (("reference", rf), ("lowered", lw)):
        for item in sorted(set(ev) - set(side)):
            out.append(Discrepancy("trivia", "missing", f"{name}@{item[1]}", item[0]))
        for item in sorted(set(side) - set(ev)):
            out.append(Discrepancy("trivia", "extra", f"{name}@{item[1]}", item[0]))
    ends_ref = {(x.kind, x.start): x.end for x in ref_extras}
    for x in low_extras:
        if (x.kind, x.start) in ends_ref and ends_ref[(x.kind, x.start)] != x.end:
            out.append(Discrepancy("trivia", "extent", f"lowered@{x.start}", x.kind))
    return out
```

The trivia check compares against the resolver by `(kind, start)`. The resolver does not know the grammar's token extents, so ends are compared only between the two trees, which is spec check 3 made implementable.

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tools/config_oracle/tests/test_compare.py -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add tools/config_oracle/compare.py tools/config_oracle/tests/test_compare.py
git commit -m "feat(oracle): provenance-matched comparator with a named kind per mutation

[BC.History: 0 errors, 100.0% success]"
```

---

### Task 8: The registry and its census

**Files:**
- Create: `tools/config_oracle/contracts.py`
- Test: `tools/config_oracle/tests/test_contracts.py`

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) class Entry`: `type`, `kind` (`directive|trivia|token-alias|branch-select|assembler|fragment|representation|unsupported`), `handler: str | None` (a dotted name resolved lazily), `hosts: dict[str, str]` (mapping `"parent:slot"` to a policy: `splice-repeat|single-slot|consumed|any`), `alias_to: str | None`;
  - `REGISTRY: dict[str, Entry]`;
  - `register(...)`, which raises `ValueError` on a duplicate;
  - `census(node_types: list[dict]) -> list[str]`, returning problems, an empty list when clean;
  - `host_slots(node_types, type_name) -> set[str]`.

- [ ] **Step 1: Write the failing test**

```python
# tools/config_oracle/tests/test_contracts.py
import json

import pytest

from tools.config_oracle import contracts
from tools.query_coverage import loader


def node_types():
    return json.loads((loader.REPO_ROOT / "src" / "node-types.json").read_text(encoding="utf-8"))


def test_census_is_clean_against_the_shipped_grammar():
    assert contracts.census(node_types()) == []


def test_duplicate_registration_raises():
    with pytest.raises(ValueError):
        contracts.register("preproc_conditional", "branch-select")


def test_census_catches_an_unregistered_type():
    nt = node_types() + [{"type": "preproc_split_new_shape", "named": True}]
    assert any("unregistered" in p for p in contracts.census(nt))


def test_census_catches_a_new_host_slot():
    nt = node_types()
    for t in nt:
        if t["type"] == "while_statement":
            t["fields"]["body"]["types"].append({"type": "preproc_conditional_var_block", "named": True})
    assert any("host" in p for p in contracts.census(nt))


def test_every_handler_resolves():
    for e in contracts.REGISTRY.values():
        if e.handler:
            assert contracts.resolve_handler(e) is not None, e.type
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tools/config_oracle/tests/test_contracts.py -q`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement `contracts.py`**

```python
# tools/config_oracle/contracts.py
"""The authoritative, hand-maintained registry of special node types (spec section 3).

node-types.json is a CENSUS input, never the source of this list: checking a
hand-written expectation against a generated declaration can fail; deriving the
expectation from the declaration cannot (tools/check-field-types.py pattern).
"""
from __future__ import annotations

import importlib
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Entry:
    type: str
    kind: str
    handler: str | None = None
    hosts: dict = field(default_factory=dict)
    alias_to: str | None = None


REGISTRY: dict[str, Entry] = {}


def register(type_, kind, handler=None, hosts=None, alias_to=None):
    if type_ in REGISTRY:
        raise ValueError(f"duplicate registry entry: {type_}")
    REGISTRY[type_] = Entry(type_, kind, handler, dict(hosts or {}), alias_to)


def resolve_handler(entry):
    mod, _, name = entry.handler.rpartition(".")
    return getattr(importlib.import_module(mod), name)


# --- statement-position hosts, shared by every node that fills a _statement slot
_STATEMENT_HOSTS = {
    "statement_block:<children>": "splice-repeat",
    "preproc_conditional_statement:<children>": "splice-repeat",
    "asserterror_statement:body": "single-slot", "case_branch:body": "single-slot",
    "for_statement:body": "single-slot", "foreach_statement:body": "single-slot",
    "if_statement:else_branch": "single-slot", "if_statement:then_branch": "single-slot",
    "while_statement:body": "single-slot", "with_statement:body": "single-slot",
    "preproc_guarded_statement:then_branch": "single-slot",
    "preproc_split_case_branch:body": "single-slot", "preproc_split_case_end_branch:body": "single-slot",
    "preproc_split_case_extended:body": "single-slot",
    "preproc_split_if_else_statement:else_branch": "single-slot",
    "preproc_split_if_else_statement:then_branch": "single-slot",
    "preproc_split_if_statement:else_branch": "single-slot",
    "preproc_split_if_statement:then_branch": "single-slot",
    "preproc_fragmented_else_tail:<children>": "splice-repeat",
    "preproc_split_code_block_end:<children>": "splice-repeat",
    "preproc_split_code_block_over_endif:<children>": "splice-repeat",
    "preproc_split_else_begin_over_endif:<children>": "splice-repeat",
    "preproc_split_if_begin_asymmetric:<children>": "splice-repeat",
    "preproc_split_if_begin_else:<children>": "splice-repeat",
    "preproc_split_if_then_begin:<children>": "splice-repeat",
    "preproc_split_if_then_begin_else_shared:<children>": "splice-repeat",
}

_BODY_HOSTS = {f"{p}:<children>": "splice-repeat" for p in (
    "action_group_body", "controladdin_body", "dataset_mod_body", "declaration_body", "interface_body",
    "layout_container_body", "preproc_conditional", "preproc_conditional_controladdin",
    "preproc_conditional_layout_mixed", "preproc_conditional_query", "preproc_conditional_report",
    "preproc_conditional_var", "preproc_conditional_xmlport", "query_body", "report_body", "xmlport_body")}

_ROUTINE_TAIL_HOSTS = {f"{p}:<children>": "single-slot" for p in (
    "preproc_split_procedure", "preproc_split_procedure_preamble", "procedure", "trigger_declaration")}

# --- directive plumbing: consumed by whichever owner contains it
for t in ("preproc_if", "preproc_elif", "preproc_else", "preproc_endif", "preproc_open", "preproc_close",
          "preproc_and_expression", "preproc_or_expression", "preproc_not_expression",
          "preproc_parenthesized_expression"):
    register(t, "directive")

# --- extras
for t in ("preproc_region", "preproc_endregion", "preproc_define", "preproc_undef"):
    register(t, "trivia")

# --- milestone-1 implemented handlers
register("preproc_split_begin", "token-alias", "tools.config_oracle.lowering.select.token_alias",
         hosts={h: "any" for h in ("preproc_fragmented_else_tail:<children>",
                                   "preproc_split_if_begin_asymmetric:<children>",
                                   "preproc_split_if_then_begin:<children>",
                                   "preproc_split_if_then_begin_else_shared:<children>")},
         alias_to="begin_keyword")
register("preproc_split_end", "token-alias", "tools.config_oracle.lowering.select.token_alias",
         hosts={"preproc_split_code_block_end:<children>": "any"}, alias_to="end_keyword")
register("preproc_conditional", "branch-select", "tools.config_oracle.lowering.select.branch_select",
         hosts=_BODY_HOSTS)
register("preproc_conditional_statement", "branch-select", "tools.config_oracle.lowering.select.branch_select",
         hosts=_STATEMENT_HOSTS)
register("preproc_conditional_var_block", "branch-select", "tools.config_oracle.lowering.select.branch_select",
         hosts=_ROUTINE_TAIL_HOSTS)
register("preproc_pragma_only", "branch-select", "tools.config_oracle.lowering.select.branch_select",
         hosts={"field_declaration:<children>": "single-slot", "preproc_split_procedure:<children>": "single-slot",
                "procedure:<children>": "single-slot", "source_file:<children>": "splice-repeat"})
register("preproc_split_code_block_end", "assembler",
         "tools.config_oracle.lowering.assemblers.split_code_block_end",
         hosts={"code_block:<children>": "consumed"})
register("preproc_split_case_statement_end", "assembler",
         "tools.config_oracle.lowering.assemblers.split_case_statement_end", hosts=_STATEMENT_HOSTS)
register("preproc_split_case_end_branch", "fragment", None,
         hosts={"preproc_split_case_statement_end:<children>": "consumed"})
register("preproc_split_procedure", "assembler", "tools.config_oracle.lowering.assemblers.split_procedure",
         hosts=dict(_BODY_HOSTS))

# --- registered, not yet lowered (milestones 2-3). Unsupported is explicit, never a default.
for t in ("preproc_conditional_actions", "preproc_conditional_case", "preproc_conditional_case_patterns",
          "preproc_conditional_controladdin", "preproc_conditional_dataset", "preproc_conditional_expression_tail",
          "preproc_conditional_fieldgroups", "preproc_conditional_fields", "preproc_conditional_impl_values",
          "preproc_conditional_keys", "preproc_conditional_labels", "preproc_conditional_layout",
          "preproc_conditional_layout_mixed", "preproc_conditional_link_values",
          "preproc_conditional_list_elements", "preproc_conditional_object", "preproc_conditional_option_members",
          "preproc_conditional_permissions", "preproc_conditional_query", "preproc_conditional_rendering",
          "preproc_conditional_report", "preproc_conditional_table_relation", "preproc_conditional_var",
          "preproc_conditional_where", "preproc_conditional_xmlport", "preproc_fragmented_else_tail",
          "preproc_guarded_statement", "preproc_operand_prefix", "preproc_split_brace_close",
          "preproc_split_brace_close_if_only", "preproc_split_call_statement", "preproc_split_case_branch",
          "preproc_split_case_extended", "preproc_split_code_block_over_endif", "preproc_split_complete_body",
          "preproc_split_declaration", "preproc_split_else_begin_over_endif", "preproc_split_field",
          "preproc_split_if_begin_asymmetric", "preproc_split_if_begin_else", "preproc_split_if_else_statement",
          "preproc_split_if_statement", "preproc_split_if_then_begin", "preproc_split_if_then_begin_else_shared",
          "preproc_split_procedure_body", "preproc_split_procedure_preamble", "preproc_split_report_brace_close",
          "preproc_split_report_dataitem_header", "preproc_split_report_dataitem_open_over_endif",
          "preproc_split_table_field"):
    register(t, "unsupported")

# Non-prefixed special type: completes an earlier table relation (spec section 3).
register("else_table_relation_fragment", "unsupported")

SPECIAL_NON_PREFIXED = {"else_table_relation_fragment"}


def host_slots(node_types, type_name):
    subtypes = {t["type"]: [s["type"] for s in t.get("subtypes", [])] for t in node_types if "subtypes" in t}

    def expand(ts):
        out = set()
        for t in ts:
            out |= expand(subtypes[t]) if t in subtypes else {t}
        return out

    slots = set()
    for t in node_types:
        specs = list(t.get("fields", {}).items())
        if "children" in t:
            specs.append(("<children>", t["children"]))
        for name, spec in specs:
            if type_name in expand(x["type"] for x in spec.get("types", [])):
                slots.add(f"{t['type']}:{name}")
    return slots


def census(node_types):
    problems = []
    declared = {t["type"] for t in node_types if t.get("named") and t["type"].startswith("preproc")}
    for t in sorted(declared - REGISTRY.keys()):
        problems.append(f"unregistered: {t}")
    for t in sorted(REGISTRY.keys() - declared - SPECIAL_NON_PREFIXED):
        problems.append(f"stale entry, type no longer declared: {t}")
    for e in REGISTRY.values():
        if e.kind in ("directive", "trivia", "unsupported") or not e.hosts:
            continue
        for slot in sorted(host_slots(node_types, e.type) - e.hosts.keys()):
            problems.append(f"host slot not classified: {e.type} in {slot}")
    return problems
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tools/config_oracle/tests/test_contracts.py -q`
Expected: `test_every_handler_resolves` FAILS with `ModuleNotFoundError: tools.config_oracle.lowering` until Tasks 10 and 12 exist. Every other test passes. Mark that one test `@pytest.mark.xfail(reason="handlers land in Tasks 10 and 12", strict=True)` now. Task 12 Step 5 removes the marker. `strict=True` makes the suite fail if the test starts passing while the marker is still there.

If `test_census_is_clean_against_the_shipped_grammar` reports host slots not classified, add the slot to the matching host dict, with its policy taken from the grammar rule, **not** from the census output alone. Read the parent rule and decide whether the slot is a repeat (`splice-repeat`) or a single statement or element (`single-slot`).

- [ ] **Step 5: Commit**

```bash
git add tools/config_oracle/contracts.py tools/config_oracle/tests/test_contracts.py
git commit -m "feat(oracle): hand-maintained special-type registry with a node-types census

[BC.History: 0 errors, 100.0% success]"
```

---

### Task 9: `directive-mismatch`, tree directive extents against source extents

**Files:**
- Create: `tools/config_oracle/directive_check.py`
- Test: `tools/config_oracle/tests/test_directive_check.py`

**Interfaces:**
- Consumes: `Discovery.directives` (Task 5), IR (Task 6).
- Produces: `check(root: Node, disc: Discovery) -> list[Discrepancy]`, with check `directive` and kinds `unmatched-tree`, `unmatched-source`, `condition-extent`, `end-extent`.

Expected tree extents: `preproc_if`/`preproc_elif` start at the `#`. The `condition` field node must equal the resolver's condition extent, and the node ends at `next_line` because the hidden `/\r?\n/` terminator is inside it. `preproc_else` and `preproc_endif` start at the `#` and end at `keyword_end`.

- [ ] **Step 1: Write the failing tests**

```python
# tools/config_oracle/tests/test_directive_check.py
import pytest

from tools.config_oracle import directive_check, ir
from tools.config_oracle.directives import discover

CASES = [
    b"codeunit 1 T { trigger OnRun() begin\n#if A\nx := 1;\n#else\nx := 2;\n#endif\nend; }\n",
    b"codeunit 1 T { trigger OnRun() begin\r\n#if A // c\r\nx := 1;\r\n#endif\r\nend; }\r\n",
    b"codeunit 1 T { trigger OnRun() begin\n# if not (A or B)\nx := 1;\n#elif C\nx := 3;\n#endif\nend; }",
]


@pytest.mark.parametrize("src", CASES)
def test_positive_controls_match(al_parser, src):
    root, _, problems = ir.from_tree(al_parser.parse(src))
    assert problems == []
    assert directive_check.check(root, discover(src)) == []


def test_condition_swallowing_next_line_is_condition_extent():
    """Replay 4's shape, built as a tree: condition extends into the next line."""
    src = b"#if FOO\n and b\n#endif\n"
    disc = discover(src)
    cond = ir.Node("identifier", True, "condition", 4, 14, [])   # swallowed ' and b'
    pif = ir.Node("preproc_if", True, None, 0, 15, [ir.Node("preproc_open", True, None, 0, 3, []), cond])
    pend = ir.Node("preproc_endif", True, None, 15, 21, [])
    root = ir.Node("source_file", True, None, 0, 22, [pif, pend])
    kinds = {d.kind for d in directive_check.check(root, disc)}
    assert "condition-extent" in kinds


def test_tree_directive_without_source_directive():
    src = b"x;\n"
    root = ir.Node("source_file", True, None, 0, 3, [ir.Node("preproc_else", True, None, 0, 1, [])])
    assert {d.kind for d in directive_check.check(root, discover(src))} == {"unmatched-tree"}
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tools/config_oracle/tests/test_directive_check.py -q`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

```python
# tools/config_oracle/directive_check.py
"""Tree directives against source directives, by EXTENT (spec section 3, "Branch selection")."""
from __future__ import annotations

from tools.config_oracle.compare import Discrepancy

_TREE_KIND = {"preproc_if": "if", "preproc_elif": "elif", "preproc_else": "else", "preproc_endif": "endif"}


def _tree_directives(root):
    out, stack = [], [root]
    while stack:
        n = stack.pop()
        if n.kind in _TREE_KIND:
            out.append(n)
            continue
        stack.extend(n.children)
    return sorted(out, key=lambda n: n.start)


def check(root, disc):
    src = {d.hash: d for d in disc.directives}
    out, seen = [], set()
    for n in _tree_directives(root):
        d = src.get(n.start)
        path = f"{n.kind}@{n.start}"
        if d is None or d.kind != _TREE_KIND[n.kind]:
            out.append(Discrepancy("directive", "unmatched-tree", path, n.kind))
            continue
        seen.add(d.hash)
        if d.kind in ("if", "elif"):
            cond = next((c for c in n.children if c.field == "condition"), None)
            if cond is None or (cond.start, cond.end) != (d.cond.start, d.cond.end):
                got = None if cond is None else (cond.start, cond.end)
                out.append(Discrepancy("directive", "condition-extent", path,
                                       f"tree {got} vs source {(d.cond.start, d.cond.end)}"))
            if n.end != d.next_line:
                out.append(Discrepancy("directive", "end-extent", path, f"tree {n.end} vs source {d.next_line}"))
        elif n.end != d.keyword_end:
            out.append(Discrepancy("directive", "end-extent", path, f"tree {n.end} vs source {d.keyword_end}"))
    for h, d in sorted(src.items()):
        if h not in seen:
            out.append(Discrepancy("directive", "unmatched-source", f"{d.kind}@{h}", d.kind))
    return out
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tools/config_oracle/tests/test_directive_check.py -q`
Expected: all pass. If a positive control fails with `end-extent` on `preproc_if` at EOF without a trailing newline, check that `next_line == len(src)` for the last line (Task 4 `_lines`). If it fails on `preproc_endif`, print the node's end and the source there: the scanner's `preproc_close` must end right after the word. **Do not change the check to pass.** A real mismatch here is a grammar finding: report it and stop.

- [ ] **Step 5: Commit**

```bash
git add tools/config_oracle/directive_check.py tools/config_oracle/tests/test_directive_check.py
git commit -m "feat(oracle): directive-mismatch by extent, including condition extent

[BC.History: 0 errors, 100.0% success]"
```

---

### Task 10: The lowering engine, branch selection, token aliases, and accounting

**Files:**
- Create: `tools/config_oracle/lowering/__init__.py`, `tools/config_oracle/lowering/engine.py`, `tools/config_oracle/lowering/select.py`
- Test: `tools/config_oracle/tests/test_lowering_select.py`, `tools/config_oracle/tests/test_isolation.py`

**Interfaces:**
- Consumes: `REGISTRY` and `resolve_handler` (Task 8); `Resolution` (Task 4); `Node`, `Extra`, `recompute_span` (Task 6).
- Produces:
  - `class LoweringError(Exception)` with `.kind` (`unregistered-type|unsupported-type|policy|policy-host|unconsumed-fragment|accounting|contract-shape|empty-node|directive-unknown`) and `.node`;
  - the fragments `Terminator(anchor, leaf)`, `Following(anchor, statements)`, `BlockCompletion(anchor, statements, end)`, `ElseAttachment(anchor, else_kw, branch)`;
  - `Lowered(nodes: list[Node], frags: list)`;
  - `Ctx(resolution, accounting, parent_kind, slot)` with `child(parent_kind, slot)`;
  - `Accounting.mark(node, reason)`, `Accounting.check_complete(root)`;
  - `lower_tree(root, extras, resolution) -> tuple[Node, list[Extra], list[str]]`, returning the lowered root, the kept extras, and the normalisations (`"removed-empty:<kind>@<start>"`);
  - in `select.py`: `split_arms(node) -> (list[(directive_node, content_nodes)], endif_node)`, `branch_select(node, ctx) -> Lowered`, `token_alias(node, ctx) -> Lowered`.

- [ ] **Step 1: Write the failing tests**

```python
# tools/config_oracle/tests/test_lowering_select.py
import pytest

from tools.config_oracle import compare, ir, reference
from tools.config_oracle.directives import configurations, discover, resolve
from tools.config_oracle.lowering import lower_tree
from tools.config_oracle.lowering.engine import LoweringError

STMT = b"""codeunit 1 T
{
    trigger OnRun()
    begin
        x := 0;
#if A
        x := 1;
#else
        x := 2;
        x := 3;
#endif
        x := 4;
    end;
}
"""

BODY = b"""codeunit 1 T
{
#if A
    procedure P() begin end;
#endif
    procedure Q() begin end;
}
"""


def run_all(parser, src):
    root, extras, problems = ir.from_tree(parser.parse(src))
    assert problems == []
    disc = discover(src)
    results = {}
    for env in configurations(disc):
        res = resolve(src, env)
        low, low_extras, _ = lower_tree(root, extras, res)
        ref = reference.extract(parser, res.masked)
        assert ref.problems == []
        results[env] = (compare.structure(ref.root, low)
                        + compare.coverage(src, res.active, low, low_extras, "low"))
    return results


@pytest.mark.parametrize("src", [STMT, BODY])
def test_branch_select_matches_reference_in_every_configuration(al_parser, src):
    for env, ds in run_all(al_parser, src).items():
        assert ds == [], (env, ds)


def test_single_slot_with_two_statements_is_policy(al_parser):
    src = b"codeunit 1 T { trigger OnRun() begin if c then\n#if A\n x := 1; y := 2;\n#endif\n ; end; }"
    root, extras, _ = ir.from_tree(al_parser.parse(src))
    res = resolve(src, frozenset({"A"}))
    with pytest.raises(LoweringError) as err:
        lower_tree(root, extras, res)
    assert err.value.kind in ("policy", "contract-shape")


def test_unsupported_type_fails_closed(al_parser):
    src = b"table 1 T { fields {\n#if A\n field(1; F; Integer) { }\n#endif\n } }"
    root, extras, _ = ir.from_tree(al_parser.parse(src))
    with pytest.raises(LoweringError) as err:
        lower_tree(root, extras, resolve(src, frozenset({"A"})))
    assert err.value.kind == "unsupported-type"


def test_unregistered_special_type_fails_closed():
    n = ir.Node("preproc_split_invented", True, None, 0, 1, [ir.Node("x", False, None, 0, 1, [])])
    root = ir.Node("source_file", True, None, 0, 1, [n])
    with pytest.raises(LoweringError) as err:
        lower_tree(root, [], resolve(b"x", frozenset()))
    assert err.value.kind == "unregistered-type"


def test_accounting_catches_a_dropped_leaf(al_parser, monkeypatch):
    from tools.config_oracle.lowering import select
    real = select.branch_select

    def lossy(node, ctx):
        out = real(node, ctx)
        out.nodes = out.nodes[:-1]           # drop the arm's last statement without accounting
        return out

    monkeypatch.setattr(select, "branch_select", lossy)
    root, extras, _ = ir.from_tree(al_parser.parse(STMT))
    with pytest.raises(LoweringError) as err:
        lower_tree(root, extras, resolve(STMT, frozenset()))
    assert err.value.kind == "accounting"
```

```python
# tools/config_oracle/tests/test_isolation.py
import ast
from pathlib import Path

import pytest

LOWERING = Path(__file__).resolve().parents[1] / "lowering"


def test_lowering_never_imports_reference_or_a_parser():
    for py in LOWERING.glob("*.py"):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            names = []
            if isinstance(n, ast.Import):
                names = [a.name for a in n.names]
            elif isinstance(n, ast.ImportFrom):
                names = [n.module or ""] + [f"{n.module}.{a.name}" for a in n.names]
            for name in names:
                assert "reference" not in name and "tree_sitter" not in name and "loader" not in name, (py, name)


def test_lowering_runs_with_parsers_disabled(al_parser, monkeypatch):
    """Spec: isolation is necessary-not-sufficient; this proves no parse call happens at runtime."""
    import tree_sitter

    from tools.config_oracle import ir
    from tools.config_oracle.directives import resolve
    from tools.config_oracle.lowering import lower_tree
    from tools.config_oracle.tests.test_lowering_select import STMT

    root, extras, _ = ir.from_tree(al_parser.parse(STMT))

    def boom(*a, **k):
        raise AssertionError("lowering invoked a parser")

    monkeypatch.setattr(tree_sitter.Parser, "parse", boom)
    lower_tree(root, extras, resolve(STMT, frozenset({"A"})))
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tools/config_oracle/tests/test_lowering_select.py tools/config_oracle/tests/test_isolation.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'tools.config_oracle.lowering'`.

- [ ] **Step 3: Implement `engine.py`**

```python
# tools/config_oracle/lowering/engine.py
"""Recursive lowering of the multi-configuration IR to one configuration (spec section 3).

Rules that are load-bearing:
  * no default handler -- an unregistered special node fails;
  * every leaf and extra of the ORIGINAL tree is accounted exactly once;
  * a fragment may only pass up through a node when the child it came from is
    that node's last original child, and must be consumed by a named consumer;
  * the only normalisation is removing an EMPTY_REMOVABLE container that
    lowering emptied.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from tools.config_oracle import contracts
from tools.config_oracle.ir import Node, recompute_span

# Content-only containers the grammar wraps in optional(field(...)) (spec section 2).
EMPTY_REMOVABLE = {
    "statement_block",   # code_block: optional(field('body', $.statement_block))
    "declaration_body",  # _declaration_body_block: optional(field('body', $.declaration_body))
    "var_body",          # var_section: optional(field('body', $.var_body))
    "case_body",         # case_statement: optional(field('body', $.case_body))
}

STATEMENT_HOSTS = {"statement_block", "case_branch"}


class LoweringError(Exception):
    def __init__(self, kind, node, detail=""):
        super().__init__(f"{kind} at {node.kind}@{node.start}{': ' + detail if detail else ''}")
        self.kind, self.node, self.detail = kind, node, detail


@dataclass
class Frag:
    anchor: Node | None


@dataclass
class Terminator(Frag):
    leaf: Node = None


@dataclass
class Following(Frag):
    statements: list = field(default_factory=list)


@dataclass
class BlockCompletion(Frag):
    statements: list = field(default_factory=list)
    end: Node = None


@dataclass
class ElseAttachment(Frag):
    else_kw: Node = None
    branch: Node = None


@dataclass
class Lowered:
    nodes: list
    frags: list = field(default_factory=list)


class Accounting:
    def __init__(self):
        self.leaf = {}

    def mark(self, node, reason):
        for lf in node.leaves():
            key = (lf.start, lf.end, lf.kind)
            if key in self.leaf:
                raise LoweringError("accounting", lf, f"leaf accounted twice: {self.leaf[key]} then {reason}")
            self.leaf[key] = reason

    def check_complete(self, root):
        for lf in root.leaves():
            if (lf.start, lf.end, lf.kind) not in self.leaf:
                raise LoweringError("accounting", lf, "leaf never accounted")

    def check_emitted(self, low):
        """Every leaf accounted as `kept` appears in the output exactly once, and
        nothing else does. Keyed by interval only: a token alias changes kind."""
        kept = sorted((s, e) for (s, e, _), why in self.leaf.items() if why == "kept")
        emitted = sorted((lf.start, lf.end) for lf in low.leaves()) if low.children else []
        if kept != emitted:
            missing = sorted(set(kept) - set(emitted))[:3]
            extra = sorted(set(emitted) - set(kept))[:3]
            raise LoweringError("accounting", low, f"kept-but-not-emitted {missing}, emitted-but-not-kept {extra}")


@dataclass
class Ctx:
    resolution: object
    accounting: Accounting
    parent_kind: str | None = None
    slot: str | None = None
    normalised: list = field(default_factory=list)

    def child(self, parent_kind, slot):
        return Ctx(self.resolution, self.accounting, parent_kind, slot, self.normalised)

    def policy(self, entry, node):
        host = f"{self.parent_kind}:{self.slot}"
        if host not in entry.hosts:
            raise LoweringError("policy-host", node, f"{entry.type} not registered in {host}")
        return entry.hosts[host]


def _is_special(kind):
    return kind.startswith("preproc") or kind in contracts.SPECIAL_NON_PREFIXED


def lower(node, ctx) -> Lowered:
    if _is_special(node.kind):
        entry = contracts.REGISTRY.get(node.kind)
        if entry is None:
            raise LoweringError("unregistered-type", node)
        if entry.kind == "unsupported" or entry.handler is None:
            raise LoweringError("unsupported-type", node)
        return contracts.resolve_handler(entry)(node, ctx)
    return _lower_ordinary(node, ctx)


def _lower_ordinary(node, ctx) -> Lowered:
    if not node.children:
        ctx.accounting.mark(node, "kept")
        return Lowered([node.copy(children=[])])
    kids, frags = [], []
    last_index = len(node.children) - 1
    for i, c in enumerate(node.children):
        r = lower(c, ctx.child(node.kind, c.field or "<children>"))
        for f in r.frags:
            f._from_last = (i == last_index)
        kids.extend(r.nodes)
        frags.extend(r.frags)
    new = Node(node.kind, node.named, node.field, node.start, node.end, kids)
    frags = _consume(new, frags)
    for f in frags:
        if not getattr(f, "_from_last", False):
            raise LoweringError("unconsumed-fragment", node, f"{type(f).__name__} not from the last child")
        f.anchor = new
    if not new.children:
        if node.kind in EMPTY_REMOVABLE:
            ctx.normalised.append(f"removed-empty:{node.kind}@{node.start}")
            return Lowered([], frags)
        raise LoweringError("empty-node", node)
    return Lowered([recompute_span(new)], frags)


def _consume(new, frags):
    rest = []
    for f in frags:
        if isinstance(f, BlockCompletion) and new.kind == "code_block":
            body = next((c for c in new.children if c.field == "body"), None)
            if f.statements:
                if body is None:
                    body = Node("statement_block", True, "body", 0, 0, [])
                    new.children.insert(1, body)
                body.children.extend(f.statements)
                recompute_span(body)
            new.children.append(f.end)
        elif isinstance(f, ElseAttachment) and new.kind == "if_statement" and f.anchor is not None \
                and f.anchor.field == "then_branch" and any(c is f.anchor for c in new.children):
            new.children.append(f.else_kw)
            new.children.append(f.branch.copy(field="else_branch"))
        elif isinstance(f, (Terminator, Following)) and new.kind in STATEMENT_HOSTS \
                and any(c is f.anchor for c in new.children):
            at = next(i for i, c in enumerate(new.children) if c is f.anchor) + 1
            insert = [f.leaf] if isinstance(f, Terminator) else list(f.statements)
            new.children[at:at] = insert
        else:
            rest.append(f)
    return rest


def lower_tree(root, extras, resolution):
    acc = Accounting()
    ctx = Ctx(resolution, acc)
    out = lower(root, ctx)
    if out.frags:
        raise LoweringError("unconsumed-fragment", root, ", ".join(type(f).__name__ for f in out.frags))
    low = out.nodes[0] if out.nodes else Node(root.kind, root.named, None, 0, 0, [])
    acc.check_complete(root)
    acc.check_emitted(low)
    kept = [e for e in extras if resolution.active[e.start]]
    return low, kept, list(ctx.normalised)
```

`check_complete` proves every original leaf got a reason. `check_emitted` proves the leaves marked `kept` are exactly the leaves in the output. Together they catch both a leaf that is never accounted and a leaf that is accounted and then dropped. The dropped-leaf test below exercises the second case.

Extras: kept iff `resolution.active[e.start]`. The resolver blanks consumed directive lines, and a trailing comment on a directive line lies inside that line, so it is not active. This makes the extras rule a source fact, not a tree decision, as spec section 2 requires.

- [ ] **Step 4: Implement `select.py` and `lowering/__init__.py`**

```python
# tools/config_oracle/lowering/select.py
"""Branch selection, token aliases (spec section 3, "Branch selection")."""
from __future__ import annotations

from tools.config_oracle import contracts
from tools.config_oracle.ir import Node
from tools.config_oracle.lowering.engine import Lowered, LoweringError, lower

DIRECTIVES = ("preproc_if", "preproc_elif", "preproc_else")


def split_arms(node):
    arms, endif, current = [], None, None
    for c in node.children:
        if c.kind in DIRECTIVES:
            current = (c, [])
            arms.append(current)
        elif c.kind == "preproc_endif":
            endif = c
        elif current is None:
            raise LoweringError("contract-shape", node, f"content before the first directive: {c.kind}")
        else:
            current[1].append(c)
    if not arms or arms[0][0].kind != "preproc_if" or endif is None:
        raise LoweringError("contract-shape", node, "not an #if ... #endif group")
    return arms, endif


def chosen_arm(node, arms, ctx):
    key = arms[0][0].start
    if key not in ctx.resolution.arm_choice:
        raise LoweringError("directive-unknown", node, f"no resolver group at {key}")
    return ctx.resolution.arm_choice[key]


def branch_select(node, ctx) -> Lowered:
    entry = contracts.REGISTRY[node.kind]
    policy = ctx.policy(entry, node)
    arms, endif = split_arms(node)
    choice = chosen_arm(node, arms, ctx)
    out = Lowered([])
    for directive, content in arms:
        ctx.accounting.mark(directive, "directive")
        if directive.start == choice:
            for c in content:
                r = lower(c, ctx.child(node.kind, c.field or "<children>"))
                out.nodes.extend(r.nodes)
                out.frags.extend(r.frags)
        else:
            for c in content:
                ctx.accounting.mark(c, "inactive-arm")
    ctx.accounting.mark(endif, "directive")
    if policy == "single-slot":
        if len(out.nodes) > 1:
            raise LoweringError("policy", node, f"{len(out.nodes)} nodes into a single slot")
        out.nodes = [n.copy(field=node.field) for n in out.nodes]
    return out


def token_alias(node, ctx) -> Lowered:
    entry = contracts.REGISTRY[node.kind]
    ctx.policy(entry, node)
    if node.children:
        raise LoweringError("contract-shape", node, "token alias with children")
    ctx.accounting.mark(node, "kept")
    return Lowered([Node(entry.alias_to, True, node.field, node.start, node.end, [])])
```

```python
# tools/config_oracle/lowering/__init__.py
from tools.config_oracle.lowering.engine import lower_tree  # noqa: F401
```

- [ ] **Step 5: Run to verify it passes**

Run: `python -m pytest tools/config_oracle/tests/test_lowering_select.py tools/config_oracle/tests/test_isolation.py -q`
Expected: all pass. If `test_branch_select_matches_reference_in_every_configuration` reports a structure discrepancy, print both IR trees (`ir.Node` has a dataclass repr) and find the first divergence. **A difference can be a real grammar finding.** Record it; do not change the comparator to hide it.

- [ ] **Step 6: Commit**

```bash
git add tools/config_oracle/lowering tools/config_oracle/tests/test_lowering_select.py tools/config_oracle/tests/test_isolation.py
git commit -m "feat(oracle): lowering engine, branch selection, token aliases, per-leaf accounting

[BC.History: 0 errors, 100.0% success]"
```

---

### Task 11: Representation contracts

**Files:**
- Create: `tools/config_oracle/representation.py`
- Test: `tools/config_oracle/tests/test_representation.py`

**Interfaces:**
- Consumes: IR (Task 6); `split_arms` (Task 10).
- Produces: `check(root: Node) -> list[Discrepancy]` with check `representation` and kinds `var-block-without-var`, `pragma-only-with-structure`.

- [ ] **Step 1: Write the failing tests, positive controls first**

```python
# tools/config_oracle/tests/test_representation.py
from tools.config_oracle import ir, representation


def reps(parser, src):
    root, _, problems = ir.from_tree(parser.parse(src))
    assert problems == []
    return [(d.kind, d.path.split("@")[0]) for d in representation.check(root)]


VAR_THEN_PRAGMA = b"""codeunit 1 T {
    procedure P()
#if A
    var
        i: Integer;
#else
#pragma warning disable AA0005
#endif
    begin
    end;
}"""

PRAGMA_ONLY_COMMENT = b"""codeunit 1 T {
    procedure P()
#if A
    // just a note
#endif
    begin
    end;
}"""

PRAGMA_ONLY_EMPTY = b"""codeunit 1 T {
    procedure P()
#if A
#else
#endif
    begin
    end;
}"""


def test_var_in_one_arm_pragma_in_other_is_legitimate(al_parser):
    assert reps(al_parser, VAR_THEN_PRAGMA) == []


def test_comment_only_and_empty_pragma_only_are_legitimate(al_parser):
    assert reps(al_parser, PRAGMA_ONLY_COMMENT) == []
    assert reps(al_parser, PRAGMA_ONLY_EMPTY) == []


def test_var_block_with_no_var_in_any_arm_is_a_violation():
    arm = ir.Node("preproc_if", True, None, 0, 5, [])
    end = ir.Node("preproc_endif", True, None, 10, 16, [])
    vb = ir.Node("preproc_conditional_var_block", True, None, 0, 16, [arm, end])
    root = ir.Node("procedure", True, None, 0, 16, [vb])
    assert [d.kind for d in representation.check(root)] == ["var-block-without-var"]


def test_pragma_only_with_a_structural_child_is_a_violation():
    arm = ir.Node("preproc_if", True, None, 0, 5, [])
    stray = ir.Node("identifier", True, None, 6, 7, [])
    end = ir.Node("preproc_endif", True, None, 10, 16, [])
    root = ir.Node("procedure", True, None, 0, 16,
                   [ir.Node("preproc_pragma_only", True, None, 0, 16, [arm, stray, end])])
    assert [d.kind for d in representation.check(root)] == ["pragma-only-with-structure"]
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tools/config_oracle/tests/test_representation.py -q`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement**

```python
# tools/config_oracle/representation.py
"""Contracts on the multi-configuration tree, BEFORE lowering (spec section 3).

These catch defects that configuration equivalence cannot see: two different
wrappers that lower to the same configured program (defect 5).
"""
from __future__ import annotations

from tools.config_oracle.compare import Discrepancy
from tools.config_oracle.lowering.select import split_arms

VAR_BLOCK_HOSTS = {"procedure", "trigger_declaration", "preproc_split_procedure", "preproc_split_procedure_preamble"}


def check(root):
    out = []
    stack = [(root, None)]
    while stack:
        n, parent = stack.pop()
        if n.kind == "preproc_conditional_var_block" and parent in VAR_BLOCK_HOSTS:
            arms, _ = split_arms(n)
            if not any(c.kind == "var_section" for _, content in arms for c in content):
                out.append(Discrepancy("representation", "var-block-without-var", f"{n.kind}@{n.start}", parent))
        if n.kind == "preproc_pragma_only":
            arms, _ = split_arms(n)
            if any(content for _, content in arms):
                out.append(Discrepancy("representation", "pragma-only-with-structure", f"{n.kind}@{n.start}", parent))
        stack.extend((c, n.kind) for c in n.children)
    return out
```

Extras are not IR children (Task 6), so "only extras" is exactly "no content children".

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tools/config_oracle/tests/test_representation.py -q`
Expected: all pass. If `test_comment_only_and_empty_pragma_only_are_legitimate` fails because the grammar produces `preproc_conditional_var_block` for either control, **that is a finding**: the grammar misreads a comment-only group as a var block. Record the tree and stop. Do not weaken the contract.

- [ ] **Step 5: Commit**

```bash
git add tools/config_oracle/representation.py tools/config_oracle/tests/test_representation.py
git commit -m "feat(oracle): host-scoped representation contracts with positive controls

[BC.History: 0 errors, 100.0% success]"
```

---

### Task 12: Assemblers for `split-code-block-end` and `split-procedure`

**Files:**
- Create: `tools/config_oracle/lowering/assemblers.py`
- Test: `tools/config_oracle/tests/test_assemblers.py`

**Interfaces:**
- Consumes: `split_arms`, `chosen_arm`, `lower`, `Lowered`, the fragments, `LoweringError` (Task 10).
- Produces: `split_code_block_end(node, ctx) -> Lowered`, `split_procedure(node, ctx) -> Lowered`. `split_case_statement_end` is added in Task 13.

The contract for `split-code-block-end` (named edge rewrites):
- **Arm shape A** is `preproc_split_end [;]`. The alias becomes the `code_block`'s `end_keyword`, and the `;` becomes a `Terminator` of the statement that owns the `code_block`.
- **Arm shape B** is `stmts… end_keyword else_keyword begin_keyword stmts… end_keyword [;]`:
  - the first statements, with their `;`, are appended to the `code_block`'s `statement_block`;
  - the first `end_keyword` closes the `code_block`;
  - `else begin … end` becomes a new `code_block` attached to the owning `if_statement` as `else_branch`, an `ElseAttachment` that the `if_statement` consumes only when the `code_block` is its `then_branch`;
  - the trailing `;` becomes a `Terminator`.

The contract for `split-procedure`:
- The active arm supplies the header pieces. Its `attribute_item`s become **preceding siblings** of the `procedure`, as in the reference, where attributes are siblings.
- The pieces after `#endif` are the procedure's tail, lowered in place.
- The result is one `procedure` node, with the split node's field.

- [ ] **Step 1: Write the failing tests** (every fixture configuration against its reference; Review Focus 5 included)

```python
# tools/config_oracle/tests/test_assemblers.py
import pytest

from tools.config_oracle import compare, ir, reference
from tools.config_oracle.directives import configurations, discover, resolve
from tools.config_oracle.lowering import lower_tree

SPLIT_END = b"""codeunit 1 T
{
    procedure X()
    var
        x: Integer;
    begin
        if x = 1 then begin
            x := 9;
#if not CLEAN22
        end; // note
#else
        x := 2;
        end else begin x := 3; end;
#endif
    end;
}
"""

NESTED = b"""codeunit 1 T
{
    procedure X()
    begin
#if OUTER
        if x = 1 then begin
            x := 9;
#if not CLEAN22
        end;
#else
        end else begin x := 3; end;
#endif
#endif
    end;
}
"""

SPLIT_PROC = b"""codeunit 50100 Probe
{
#if FOO
    [Scope('OnPrem')]
    procedure Foo(a: Integer)
#else
    procedure Foo(a: Integer; b: Integer)
#endif
    var
        i: Integer;
    begin
        i := a;
    end;
}
"""

# A split signature followed by a split BODY (preproc_split_complete_body) is a
# milestone-2 type and deliberately not here; replay 5's HEAD positive control
# covers the pragma-only tail.


def all_configs(parser, src):
    root, extras, problems = ir.from_tree(parser.parse(src))
    assert problems == []
    for env in configurations(discover(src)):
        res = resolve(src, env)
        low, low_extras, _ = lower_tree(root, extras, res)
        ref = reference.extract(parser, res.masked)
        assert ref.problems == [], (env, ref.problems)
        yield env, (compare.structure(ref.root, low)
                    + compare.coverage(src, res.active, low, low_extras, "low")
                    + compare.trivia(res.extras, ref.extras, low_extras))


@pytest.mark.parametrize("src", [SPLIT_END, NESTED, SPLIT_PROC])
def test_every_configuration_matches(al_parser, src):
    for env, ds in all_configs(al_parser, src):
        assert ds == [], (sorted(env), ds)


def test_else_attachment_needs_an_if_owner(al_parser):
    """False-positive control's mirror: an else-arm that cannot attach must fail loudly, not pass."""
    from tools.config_oracle.lowering.engine import LoweringError
    src = b"codeunit 1 T { trigger OnRun() begin begin x := 9;\n#if A\n end;\n#else\n end else begin x := 3; end;\n#endif\n end; }"
    root, extras, problems = ir.from_tree(al_parser.parse(src))
    if problems:
        pytest.skip("grammar does not produce preproc_split_code_block_end for a bare block; nothing to lower")
    with pytest.raises(LoweringError) as err:
        lower_tree(root, extras, resolve(src, frozenset()))
    assert err.value.kind == "unconsumed-fragment"
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tools/config_oracle/tests/test_assemblers.py -q`
Expected: FAIL with `unsupported-type` or `ModuleNotFoundError: ...assemblers`.

- [ ] **Step 3: Implement `assemblers.py`**

```python
# tools/config_oracle/lowering/assemblers.py
"""Assemblers: construct configured nodes from pieces across arms (spec section 3).

Each function's docstring IS its contract, including every edge rewrite it is
allowed to make. Anything not named there is an error.
"""
from __future__ import annotations

from tools.config_oracle import contracts
from tools.config_oracle.ir import Node, recompute_span
from tools.config_oracle.lowering.engine import (BlockCompletion, ElseAttachment, Following, Lowered,
                                                 LoweringError, Terminator, lower)
from tools.config_oracle.lowering.select import chosen_arm, split_arms


def _active(node, ctx):
    arms, endif = split_arms(node)
    choice = chosen_arm(node, arms, ctx)
    content = []
    for directive, items in arms:
        ctx.accounting.mark(directive, "directive")
        if directive.start == choice:
            content = items
        else:
            for c in items:
                ctx.accounting.mark(c, "inactive-arm")
    ctx.accounting.mark(endif, "directive")
    return content


def _lower_all(items, ctx, parent_kind):
    nodes = []
    for c in items:
        r = lower(c, ctx.child(parent_kind, c.field or "<children>"))
        if r.frags:
            raise LoweringError("unconsumed-fragment", c, "fragment inside an assembled run")
        nodes.extend(r.nodes)
    return nodes


def split_code_block_end(node, ctx) -> Lowered:
    """Contract split-code-block-end. Rewrites allowed:
    A  `preproc_split_end [;]`: alias -> the code_block's end_keyword; `;` -> Terminator.
    B  `stmts end else begin stmts end [;]`: leading stmts -> the code_block's
       statement_block; first end -> the code_block's end; `else begin .. end`
       -> new code_block, ElseAttachment to the if_statement whose then_branch
       this code_block is; `;` -> Terminator.
    """
    ctx.policy(contracts.REGISTRY[node.kind], node)
    arm = _active(node, ctx)
    if not arm:
        raise LoweringError("contract-shape", node, "empty arm")
    if arm[0].kind == "preproc_split_end":
        ctx.accounting.mark(arm[0], "kept")
        end = Node("end_keyword", True, None, arm[0].start, arm[0].end, [])
        rest = arm[1:]
        frags = [BlockCompletion(None, [], end)]
        if rest:
            if len(rest) != 1 or rest[0].kind != ";":
                raise LoweringError("contract-shape", node, "shape A tail")
            ctx.accounting.mark(rest[0], "kept")
            frags.append(Terminator(None, rest[0].copy()))
        return Lowered([], frags)
    ends = [i for i, c in enumerate(arm) if c.kind == "end_keyword"]
    if len(ends) != 2 or arm[ends[0] + 1].kind != "else_keyword" or arm[ends[0] + 2].kind != "begin_keyword":
        raise LoweringError("contract-shape", node, "shape B")
    first, second = ends
    lead = _lower_all(arm[:first], ctx, "statement_block")
    for piece in (arm[first], arm[first + 1], arm[first + 2], arm[second]):
        ctx.accounting.mark(piece, "kept")
    inner = _lower_all(arm[first + 3:second], ctx, "statement_block")
    kids = [arm[first + 2].copy()]
    if inner:
        kids.append(recompute_span(Node("statement_block", True, "body", 0, 0, inner)))
    kids.append(arm[second].copy())
    branch = recompute_span(Node("code_block", True, "else_branch", 0, 0, kids))
    frags = [BlockCompletion(None, lead, arm[first].copy()), ElseAttachment(None, arm[first + 1].copy(), branch)]
    tail = arm[second + 1:]
    if tail:
        if len(tail) != 1 or tail[0].kind != ";":
            raise LoweringError("contract-shape", node, "shape B tail")
        ctx.accounting.mark(tail[0], "kept")
        frags.append(Terminator(None, tail[0].copy()))
    return Lowered([], frags)


def split_procedure(node, ctx) -> Lowered:
    """Contract split-procedure. Rewrites allowed: the active arm's header pieces
    and the pieces after #endif become one `procedure` with this node's field;
    the arm's attribute_items become preceding siblings of that procedure."""
    arms, endif = split_arms_with_tail(node)
    choice = chosen_arm(node, arms, ctx)
    header = []
    for directive, items in arms:
        ctx.accounting.mark(directive, "directive")
        if directive.start == choice:
            header = items
        else:
            for c in items:
                ctx.accounting.mark(c, "inactive-arm")
    ctx.accounting.mark(endif, "directive")
    attrs = [h for h in header if h.kind == "attribute_item"]
    rest = [h for h in header if h.kind != "attribute_item"]
    tail = node.children[node.children.index(endif) + 1:]
    lowered_attrs = _lower_all(attrs, ctx, node.kind)
    parts = _lower_all(rest, ctx, "procedure") + _lower_all(tail, ctx, "procedure")
    proc = recompute_span(Node("procedure", True, node.field, 0, 0, parts))
    return Lowered(lowered_attrs + [proc])


def split_arms_with_tail(node):
    """split_arms over the prefix up to the FIRST #endif; the tail follows it."""
    first_endif = next(i for i, c in enumerate(node.children) if c.kind == "preproc_endif")
    head = Node(node.kind, node.named, node.field, node.start, node.end, node.children[:first_endif + 1])
    return split_arms(head)
```

Two details the implementer must check against the real trees printed by `tree-sitter parse`:
1. In `split_procedure`, the tail's `preproc_conditional_var_block` or `preproc_pragma_only` children are lowered with `parent_kind="procedure"`, so their host slot `procedure:<children>` (policy `single-slot`) applies. That is the host the reference tree has.
2. `_lower_all` refuses fragments inside a run. If a statement inside a shape-B arm is itself a split construct that emits a Terminator, the refusal fires and the task must add explicit handling. Do not relax the refusal.

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tools/config_oracle/tests/test_assemblers.py -q`
Expected: all pass. A failing configuration prints the discrepancy list. Compare it with `./tools/ts-lock.sh tree-sitter parse` of the masked text (write `res.masked` to a scratch file). If the reference shows a structure the contract docstring does not describe, the contract is incomplete: extend the docstring **and** the code together.

- [ ] **Step 5: Remove the xfail from `test_every_handler_resolves` (Task 8), then run the suite**

Run: `python -m pytest tools/config_oracle/tests -q`
Expected: all pass except `split_case_statement_end`'s handler, which Task 13 adds. Keep the xfail on that one handler only: change the test to skip `preproc_split_case_statement_end` with a comment `# Task 13`.

- [ ] **Step 6: Commit**

```bash
git add tools/config_oracle/lowering/assemblers.py tools/config_oracle/tests/test_assemblers.py tools/config_oracle/tests/test_contracts.py
git commit -m "feat(oracle): split-code-block-end (both arm shapes) and split-procedure assemblers

[BC.History: 0 errors, 100.0% success]"
```

---

### Task 13: The `split-case-end` assembler, with its negative and a grammar mutant

**Files:**
- Modify: `tools/config_oracle/lowering/assemblers.py`
- Test: `tools/config_oracle/tests/test_case_end.py`

**Interfaces:**
- Produces: `split_case_statement_end(node, ctx) -> Lowered`.

The contract for `split-case-end`, with its named edge rewrites:
- The pieces before `#if` (`case_keyword`, `expression`, `of_keyword`, optional `case_body`, the pattern run and `:`) and the active `preproc_split_case_end_branch` assemble into one `case_statement` carrying the node's field.
- The branch's `body` statement and its optional `;` complete a final `case_branch` appended to the `case_body`, which is created if absent.
- The branch's `end_keyword` closes the `case_statement`.
- The `;` after `end` becomes a `Terminator`.
- The `following` field's statements become a `Following`, **siblings** of the `case_statement` in the host `statement_block`.

- [ ] **Step 1: Write the failing tests**

```python
# tools/config_oracle/tests/test_case_end.py
import pytest

from tools.config_oracle import compare, ir, reference
from tools.config_oracle.directives import configurations, discover, resolve
from tools.config_oracle.lowering import lower_tree
from tools.config_oracle.lowering.engine import LoweringError

CASE_END = b"""codeunit 50000 T
{
    procedure P()
    begin
        case BalancingType of
            BalancingType::Vendor:
                begin
                    Vendor.Get(BalancingNo);
                end;
            BalancingType::Employee:
#if not CLEAN27
                ApplyBalancingTypeOfEmployee();
            end;

            CheckToAddr[1] := PadStr(CheckToAddr[1], 10, '*');
            CheckDateText := UpperCase(CheckDateText);
#else
                begin
                    Employee.Get(BalancingNo);
                end
            end;

            CheckDateText := Format("Posting Date", 0, 4);
#endif
    end;
}
"""


def lowered_and_ref(parser, src, env):
    root, extras, problems = ir.from_tree(parser.parse(src))
    assert problems == []
    res = resolve(src, env)
    low, low_extras, _ = lower_tree(root, extras, res)
    ref = reference.extract(parser, res.masked)
    assert ref.problems == []
    return low, ref, res, low_extras


def test_positive_control_every_configuration(al_parser):
    for env in configurations(discover(CASE_END)):
        low, ref, res, low_extras = lowered_and_ref(al_parser, CASE_END, env)
        ds = compare.structure(ref.root, low) + compare.coverage(CASE_END, res.active, low, low_extras, "low")
        assert ds == [], (sorted(env), ds)


def test_following_inside_case_is_detected(al_parser):
    """Hand-built bad tree (labelled as such): move the Following statements INSIDE the case_statement."""
    env = frozenset()
    low, ref, _, _ = lowered_and_ref(al_parser, CASE_END, env)
    block = low
    while block.kind != "statement_block":
        block = next(c for c in block.children if c.children)
    case = next(c for c in block.children if c.kind == "case_statement")
    after = block.children[block.children.index(case) + 2:]      # past the ';' Terminator
    for s in after:
        block.children.remove(s)
    case.children[-1:-1] = after                                 # before case's end_keyword
    kinds = {d.kind for d in compare.structure(ref.root, low)}
    assert "parent" in kinds


def test_missing_following_field_fails_closed(al_parser):
    """Simulates the grammar mutant that drops `following`: the contract shape is gone."""
    root, extras, _ = ir.from_tree(al_parser.parse(CASE_END))
    stack = [root]
    while stack:
        n = stack.pop()
        if n.field == "following":
            n.field = None
        stack.extend(n.children)
    with pytest.raises(LoweringError) as err:
        lower_tree(root, extras, resolve(CASE_END, frozenset()))
    assert err.value.kind == "contract-shape"
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tools/config_oracle/tests/test_case_end.py -q`
Expected: FAIL with `AttributeError: module ... has no attribute 'split_case_statement_end'`.

- [ ] **Step 3: Implement (append to `assemblers.py`)**

```python
def split_case_statement_end(node, ctx) -> Lowered:
    """Contract split-case-end. Rewrites allowed: pre-#if pieces plus the active
    preproc_split_case_end_branch assemble one case_statement (this node's field);
    the branch body [;] completes a final case_branch appended to case_body;
    the branch end_keyword closes the case; the `;` after it -> Terminator; the
    `following` statements -> Following, SIBLINGS of the case_statement."""
    ctx.policy(contracts.REGISTRY[node.kind], node)
    first_if = next(i for i, c in enumerate(node.children) if c.kind == "preproc_if")
    pre = node.children[:first_if]
    group = Node(node.kind, node.named, node.field, node.start, node.end, node.children[first_if:])
    branch_nodes = _active(group, ctx)
    if len(branch_nodes) != 1 or branch_nodes[0].kind != "preproc_split_case_end_branch":
        raise LoweringError("contract-shape", node, "active arm is not one case_end_branch")
    br = branch_nodes[0]
    following = [c for c in br.children if c.field == "following"]
    if len(following) != 1:
        raise LoweringError("contract-shape", br, "no `following` field")
    ends = [i for i, c in enumerate(br.children) if c.kind == "end_keyword"]
    if len(ends) != 1 or br.children[ends[0] + 1].kind != ";":
        raise LoweringError("contract-shape", br, "end ; expected")
    e = ends[0]
    body_part = br.children[:e]                    # body statement [;]
    colon = next((i for i, c in enumerate(pre) if c.kind == ":"), None)
    if colon is None:
        raise LoweringError("contract-shape", node, "no ':' before #if")
    body_field = next((c for c in pre if c.field == "body" and c.kind == "case_body"), None)
    head = [c for c in pre[:colon + 1] if c is not body_field]
    lead = [c for c in head if c.field != "pattern" and c.kind not in (",", ":")]
    pattern_run = [c for c in head if c.field == "pattern" or c.kind in (",", ":")]
    lead_nodes = _lower_all(lead, ctx, "case_statement")
    pattern_nodes = _lower_all(pattern_run, ctx, "case_branch")
    body_nodes = _lower_all(body_part, ctx, "case_branch")
    final_branch = recompute_span(Node("case_branch", True, None, 0, 0, pattern_nodes + body_nodes))
    if body_field is not None:
        existing = _lower_all([body_field], ctx, "case_statement")[0]
        existing.children.append(final_branch)
        case_body = recompute_span(existing)
    else:
        case_body = recompute_span(Node("case_body", True, "body", 0, 0, [final_branch]))
    end_kw, semi = br.children[e], br.children[e + 1]
    ctx.accounting.mark(end_kw, "kept")
    ctx.accounting.mark(semi, "kept")
    case = recompute_span(Node("case_statement", True, node.field, 0, 0,
                               lead_nodes[:3] + [case_body] + lead_nodes[3:] + [end_kw.copy()]))
    follow = _lower_all(following[0].children, ctx, "statement_block")
    return Lowered([case], [Terminator(case, semi.copy()), Following(case, follow)])
```

The `lead_nodes[:3]` split assumes the order `case_keyword, expression, of_keyword`. Verify it against the fixture's printed tree. If the reference `case_statement` orders children differently, follow the reference's order and state it in the docstring.

`Terminator(case, …)` and `Following(case, …)` are anchored on the new `case_statement`. The host `statement_block` consumes them directly, because `_consume` matches the anchor by identity. Set `_from_last` handling: these fragments are consumed at the direct parent, so the pass-through rule does not apply.

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tools/config_oracle/tests/test_case_end.py tools/config_oracle/tests -q`
Expected: all pass. Restore the full `test_every_handler_resolves` (drop the Task 12 skip).

- [ ] **Step 5: Commit**

```bash
git add tools/config_oracle/lowering/assemblers.py tools/config_oracle/tests/test_case_end.py tools/config_oracle/tests/test_contracts.py
git commit -m "feat(oracle): split-case-end assembler with following-as-siblings contract

[BC.History: 0 errors, 100.0% success]"
```

---

### Task 14: Fixture extraction, reconciled with `count_corpus_cases.py`

**Files:**
- Modify: `tools/count_corpus_cases.py` (add `cases(root)`)
- Create: `tools/config_oracle/fixtures.py`, `tools/config_oracle/fixture-classes.tsv`
- Test: `tools/config_oracle/tests/test_fixtures.py`

**Interfaces:**
- Produces:
  - `count_corpus_cases.cases(root) -> list[tuple[str, str]]`, the runnable (rel_path, case_name) pairs;
  - `@dataclass(frozen=True) class Case`: `file`, `name`, `index` (0-based within the file), `source: bytes`, `id` (`"file.txt#index"`);
  - `fixtures.extract(root: Path) -> list[Case]`;
  - `fixtures.load_classes(path) -> dict[tuple[str, str], tuple[str, str]]`, mapping (case id, config id or `*`) to (expected status, reason).

- [ ] **Step 1: Write the failing tests**

```python
# tools/config_oracle/tests/test_fixtures.py
from collections import Counter
from pathlib import Path

from tools import count_corpus_cases
from tools.config_oracle import fixtures

CORPUS = Path(__file__).resolve().parents[3] / "test" / "corpus"


def test_per_file_names_agree_with_the_independent_counter():
    ours = Counter((c.file, c.name) for c in fixtures.extract(CORPUS))
    theirs = Counter(count_corpus_cases.cases(CORPUS))
    assert ours == theirs


def test_source_is_the_input_block(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"=====\nName\n=====\nline1\nline2\n\n-----\n\n(tree)\n")
    [case] = fixtures.extract(tmp_path)
    assert case.source == b"line1\nline2\n"
    assert case.id == "a.txt#0"


def test_classes_file_parses():
    classes = fixtures.load_classes(Path(fixtures.__file__).with_name("fixture-classes.tsv"))
    assert isinstance(classes, dict)
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tools/config_oracle/tests/test_fixtures.py -q`
Expected: FAIL with `AttributeError: module 'tools.count_corpus_cases' has no attribute 'cases'`.

- [ ] **Step 3: Implement**

In `tools/count_corpus_cases.py`, add after `scan`:

```python
def cases(root: pathlib.Path):
    """(rel_path, case_name) for every RUNNABLE case -- the names scan() counts."""
    out = []
    for path in sorted(root.rglob("*.txt")):
        data = path.read_bytes()
        hits = list(HEADER.finditer(data))
        rel = str(path.relative_to(root)).replace("\\", "/")
        for i, m in enumerate(hits):
            end = hits[i + 1].start() if i + 1 < len(hits) else len(data)
            if DIVIDER.search(data[m.end():end]) and not SKIP_ATTR.search(m.group("name")):
                out.append((rel, m.group("name").split(b"\n")[0].strip().decode("utf8", "replace")))
    return out
```

```python
# tools/config_oracle/fixtures.py
"""test/corpus cases as oracle INPUT (their expected trees play no part in the verdict).

A line-based reader, deliberately not count_corpus_cases' regex: two readers
of the corpus format must agree (spec section 4), which is only a check if
they are different implementations.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_EQ = re.compile(rb"^={3,}[ \t]*\r?$")
_DASH = re.compile(rb"^-{3,}[ \t]*\r?$")
_ATTR = re.compile(rb"^:")


@dataclass(frozen=True)
class Case:
    file: str
    name: str
    index: int
    source: bytes

    @property
    def id(self):
        return f"{self.file}#{self.index}"


def extract(root: Path) -> list:
    out = []
    for path in sorted(root.rglob("*.txt")):
        rel = str(path.relative_to(root)).replace("\\", "/")
        lines = path.read_bytes().split(b"\n")
        i, index = 0, 0
        while i < len(lines):
            if _EQ.match(lines[i]) and i + 1 < len(lines) and lines[i + 1].strip() and not _EQ.match(lines[i + 1]):
                j = i + 1
                name_lines = []
                while j < len(lines) and not _EQ.match(lines[j]):
                    if not lines[j].strip():
                        name_lines = None     # blank line inside a header: tree-sitter drops the case
                        break
                    name_lines.append(lines[j])
                    j += 1
                if name_lines is None or j >= len(lines):
                    i += 1
                    continue
                k = j + 1
                while k < len(lines) and not _DASH.match(lines[k]) and not _EQ.match(lines[k]):
                    k += 1
                skip = any(_ATTR.match(l) and l.strip().startswith(b":skip") for l in name_lines)
                if k < len(lines) and _DASH.match(lines[k]) and not skip:
                    body = b"\n".join(lines[j + 1:k]).rstrip(b"\r\n") + b"\n"
                    out.append(Case(rel, name_lines[0].strip().decode("utf8", "replace"), index, body))
                    index += 1
                i = k
            else:
                i += 1
    return out


def load_classes(path: Path) -> dict:
    classes = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        case_id, config, expected, reason = line.split("\t")
        if (case_id, config) in classes:
            raise ValueError(f"duplicate classification: {case_id} {config}")
        classes[(case_id, config)] = (expected, reason)
    return classes
```

```text
# tools/config_oracle/fixture-classes.tsv
# case_id<TAB>config_id or *<TAB>expected status<TAB>reason
# Only deliberate negatives belong here. Milestone 1 starts empty; entries are
# added one at a time, each with the reason the case is expected not to pass.
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tools/config_oracle/tests/test_fixtures.py -q && python tools/count_corpus_cases.py`
Expected: pass, and the counter still exits 0. If the per-file comparison differs, print the symmetric difference. Each item is a case one reader sees and the other doesn't, which is a corpus-format finding (CLAUDE.md traps 3 and 4). Fix the reader that is wrong about tree-sitter's behaviour, never both.

- [ ] **Step 5: Commit**

```bash
git add tools/count_corpus_cases.py tools/config_oracle/fixtures.py tools/config_oracle/fixture-classes.tsv tools/config_oracle/tests/test_fixtures.py
git commit -m "feat(oracle): fixture extraction reconciled per file and name with count_corpus_cases

[BC.History: 0 errors, 100.0% success]"
```

---

### Task 15: The runner, with accounting, reports, exit codes and peak memory

**Files:**
- Create: `tools/config_oracle/runner.py`, `tools/config_oracle/__main__.py`
- Test: `tools/config_oracle/tests/test_runner.py`

**Interfaces:**
- Consumes: everything above.
- Produces:
  - `check_input(parser, input_id: str, source: bytes, lib_path=None) -> list[Record]` (also used by `replay.py`);
  - `@dataclass class Record`: `input_id`, `config`, `status` (`pass|discrepancy|representation-violation|directive-mismatch|cannot-validate`), `items: list[str]`;
  - `run(inputs: list[tuple[str, bytes]], lib_path, workers: int, mode: str) -> Summary`, where mode is `full`, meaning lowering plus every check, or `resolve`, meaning resolver plus reference parse only;
  - `@dataclass class Summary`: `records`, `no_directives: int`, `elapsed_s`, `peak_rss_bytes`, `exit_code`;
  - `peak_rss_bytes() -> int`;
  - the CLI `python -m tools.config_oracle run --tier quick|resolve [--root PATH ...] [--workers N] [--report DIR]`.

Rules:
- The parent computes each input's expected configuration list with `discover` before dispatching. An input whose `discover` raises produces one `cannot-validate` record with config `-`.
- The parent asserts one record per expected (input, configuration). Anything else raises `IncompleteRun`, exit 2.
- An input set with zero validated pairs gives exit 2.
- Exit 0 means no record other than `pass` beyond those classified in `fixture-classes.tsv`. Exit 1 is anything else. In milestone 1 the exit code is reported, not gated.

- [ ] **Step 1: Write the failing tests**

```python
# tools/config_oracle/tests/test_runner.py
import pytest

from tools.config_oracle import runner
from tools.config_oracle.tests.test_lowering_select import STMT


def test_clean_input_passes_in_every_configuration(al_parser):
    recs = runner.check_input(al_parser, "stmt", STMT)
    assert [(r.config, r.status) for r in recs] == [("A=0", "pass"), ("A=1", "pass")]


def test_region_only_file_is_counted_not_validated():
    s = runner.run([("r", b"#region R\ncodeunit 1 T { }\n#endregion\n")], None, workers=1, mode="full")
    assert s.no_directives == 1 and s.exit_code == 2      # zero validated pairs


def test_resolver_failure_is_one_cannot_validate_record():
    s = runner.run([("bad", b"#if A\ncodeunit 1 T { }\n"), ("ok", STMT)], None, workers=1, mode="full")
    by = {(r.input_id, r.status) for r in s.records}
    assert ("bad", "cannot-validate") in by and ("ok", "pass") in by


def test_dropped_record_is_incomplete(monkeypatch, al_parser):
    real = runner.check_input
    monkeypatch.setattr(runner, "check_input", lambda *a, **k: real(*a, **k)[:-1])
    with pytest.raises(runner.IncompleteRun):
        runner.run([("stmt", STMT)], None, workers=1, mode="full")


def test_peak_rss_is_positive():
    assert runner.peak_rss_bytes() > 0
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tools/config_oracle/tests/test_runner.py -q`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement `runner.py`**

```python
# tools/config_oracle/runner.py
"""Discovery, worker pool, per-(input, configuration) accounting (spec section 4)."""
from __future__ import annotations

import ctypes
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path

from tools.config_oracle import compare, directive_check, directives, ir, reference, representation
from tools.config_oracle.lowering import lower_tree
from tools.config_oracle.lowering.engine import LoweringError


class IncompleteRun(RuntimeError):
    pass


@dataclass
class Record:
    input_id: str
    config: str
    status: str
    items: list = field(default_factory=list)


@dataclass
class Summary:
    records: list
    no_directives: int
    elapsed_s: float
    peak_rss_bytes: int
    exit_code: int


def peak_rss_bytes() -> int:
    if sys.platform == "win32":
        class PMC(ctypes.Structure):
            _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
        pmc = PMC()
        pmc.cb = ctypes.sizeof(PMC)
        ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb)
        return int(pmc.PeakWorkingSetSize)
    import resource
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def check_input(parser, input_id, source, mode="full"):
    try:
        disc = directives.discover(source)
    except directives.ResolveError as e:
        return [Record(input_id, "-", "cannot-validate", [f"resolver:{e.reason}@{e.offset}"])]
    records = []
    root = extras = None
    file_items = []
    if mode == "full":
        root, extras, problems = ir.from_tree(parser.parse(source))
        if problems:
            file_items.append("multi-config-parse:" + ",".join(problems))
        file_items += [compare.discrepancy_id(input_id, "-", d) for d in directive_check.check(root, disc)]
        rep = [compare.discrepancy_id(input_id, "-", d) for d in representation.check(root)]
    for env in directives.configurations(disc):
        cid = directives.config_id(env, disc.free_symbols)
        try:
            res = directives.resolve(source, env)
        except directives.ResolveError as e:
            records.append(Record(input_id, cid, "cannot-validate", [f"resolver:{e.reason}@{e.offset}"]))
            continue
        ref = reference.extract(parser, res.masked)
        if ref.problems:
            records.append(Record(input_id, cid, "cannot-validate", ["reference-error:" + ",".join(ref.problems)]))
            continue
        if mode == "resolve":
            records.append(Record(input_id, cid, "pass"))
            continue
        if any(i.startswith("multi-config-parse") for i in file_items):
            records.append(Record(input_id, cid, "cannot-validate", file_items))
            continue
        if any("|directive|" in i for i in file_items):
            records.append(Record(input_id, cid, "directive-mismatch", file_items))
            continue
        try:
            low, low_extras, normalised = lower_tree(root, extras, res)
        except LoweringError as e:
            records.append(Record(input_id, cid, "cannot-validate", [f"lowering:{e.kind}:{e}"]))
            continue
        ds = (compare.coverage(source, res.active, ref.root, ref.extras, "ref")
              + compare.coverage(source, res.active, low, low_extras, "low")
              + compare.structure(ref.root, low)
              + compare.trivia(res.extras, ref.extras, low_extras))
        items = [compare.discrepancy_id(input_id, cid, d) for d in ds]
        if rep:
            records.append(Record(input_id, cid, "representation-violation", rep + items))
        else:
            records.append(Record(input_id, cid, "discrepancy" if items else "pass", items))
    return records


_PARSER = None


def _init(lib_path):
    global _PARSER
    from tools.query_coverage import loader
    lib = Path(lib_path) if lib_path else loader.ensure_library(loader.REPO_ROOT)
    _PARSER = loader.make_parser(loader.load_language(lib))


def _work(args):
    input_id, source, mode = args
    return check_input(_PARSER, input_id, source, mode), peak_rss_bytes()


def run(inputs, lib_path, workers, mode):
    t0 = time.perf_counter()
    expected, no_dir, todo = {}, 0, []
    for input_id, source in inputs:
        try:
            disc = directives.discover(source)
        except directives.ResolveError:
            expected[input_id] = {"-"}
            todo.append((input_id, source, mode))
            continue
        if not disc.has_conditionals:
            no_dir += 1
            continue
        expected[input_id] = {directives.config_id(e, disc.free_symbols) for e in directives.configurations(disc)}
        todo.append((input_id, source, mode))
    records, peak = [], peak_rss_bytes()
    if workers <= 1:
        _init(lib_path)
        for t in todo:
            recs, p = _work(t)
            records.extend(recs)
            peak = max(peak, p)
    else:
        from tools.query_coverage import loader
        lib = str(lib_path or loader.ensure_library(loader.REPO_ROOT))   # build ONCE, before workers
        with ProcessPoolExecutor(workers, initializer=_init, initargs=(lib,)) as pool:
            for recs, p in pool.map(_work, todo, chunksize=8):
                records.extend(recs)
                peak = max(peak, p)
    got = {}
    for r in records:
        got.setdefault(r.input_id, []).append(r.config)
    for input_id, cfgs in expected.items():
        have = got.get(input_id, [])
        if sorted(have) != sorted(cfgs) and not (have == ["-"]):
            raise IncompleteRun(f"{input_id}: expected {sorted(cfgs)}, got {sorted(have)}")
    validated = sum(r.status != "cannot-validate" for r in records)
    if validated == 0:
        code = 2
    else:
        code = 0 if all(r.status == "pass" for r in records) else 1
    return Summary(records, no_dir, time.perf_counter() - t0, peak, code)


def write_report(summary, out_dir: Path, header: dict):
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "findings.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for r in summary.records:
            f.write(json.dumps(asdict(r)) + "\n")
    counts = {}
    for r in summary.records:
        counts[r.status] = counts.get(r.status, 0) + 1
    lines = ["# Config-oracle report", "", *(f"- {k}: {v}" for k, v in sorted(header.items())), "",
             f"- configurations checked: {len(summary.records)}",
             *(f"- {k}: {v}" for k, v in sorted(counts.items())),
             f"- inputs without conditional directives: {summary.no_directives}",
             f"- elapsed: {summary.elapsed_s:.1f}s", f"- peak RSS (max over processes): {summary.peak_rss_bytes / 2**20:.0f} MiB",
             f"- exit code: {summary.exit_code}"]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
```

The expected-count check exempts an input whose single record is `-`, which is the `discover` failure path. The parent must have predicted `{"-"}` for that input, and the `except` branch in `run` does so.

- [ ] **Step 4: Implement `__main__.py`**

```python
# tools/config_oracle/__main__.py
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path

from tools.config_oracle import fixtures, runner

REPO = Path(__file__).resolve().parents[2]


def _sha(paths):
    h = hashlib.sha256()
    for p in paths:
        h.update(p.read_bytes())
    return h.hexdigest()[:16]


def _git_head(path):
    r = subprocess.run(["git", "-C", str(path), "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
    return r.stdout.strip() or "not-a-git-repo"


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m tools.config_oracle")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--tier", choices=["quick", "resolve"], required=True)
    r.add_argument("--root", action="append", default=[])
    r.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    r.add_argument("--report", default=str(REPO / "tools" / "config_oracle" / "reports"))
    sub.add_parser("replay")
    args = ap.parse_args(argv)
    if args.cmd == "replay":
        from tools.config_oracle import replay
        return replay.main()
    header = {"grammar": _sha([REPO / "grammar.js", REPO / "src" / "scanner.c", REPO / "src" / "parser.c"]),
              "tier": args.tier}
    if args.tier == "quick":
        inputs = [(c.id, c.source) for c in fixtures.extract(REPO / "test" / "corpus")]
        mode = "full"
    else:
        if not args.root:
            print("--tier resolve needs at least one --root", file=sys.stderr)
            return 2
        inputs = []
        for root in map(Path, args.root):
            if not root.is_dir():
                print(f"corpus missing: {root}", file=sys.stderr)
                return 2
            header[f"corpus {root}"] = _git_head(root)
            inputs += [(str(p), p.read_bytes()) for p in sorted(root.rglob("*.al"))]
        mode = "resolve"
    summary = runner.run(inputs, None, args.workers, mode)
    runner.write_report(summary, Path(args.report), header)
    print((Path(args.report) / "summary.md").read_text(encoding="utf-8"))
    return summary.exit_code


if __name__ == "__main__":
    sys.exit(main())
```

Add `tools/config_oracle/reports/` to `.gitignore`.

- [ ] **Step 5: Run the tests, then the quick tier for real**

Run: `python -m pytest tools/config_oracle/tests/test_runner.py -q`
Expected: all pass.

Run: `./tools/ts-lock.sh python -m tools.config_oracle run --tier quick`
Expected: it completes and prints the summary. It will contain many `cannot-validate: lowering:unsupported-type` records, because milestones 2 and 3 have not been built, plus possibly real discrepancies. **Record the summary in the commit message body.** This is the first measurement; it does not gate.

- [ ] **Step 6: Commit**

```bash
git add tools/config_oracle/runner.py tools/config_oracle/__main__.py tools/config_oracle/tests/test_runner.py .gitignore
git commit -m "feat(oracle): runner with per-(input, configuration) accounting and reports

<paste the quick-tier summary counts here>

[BC.History: 0 errors, 100.0% success]"
```

---

### Task 16: Replays 2, 3, 4 and 5, built from historical parsers

**Files:**
- Create: `tools/config_oracle/replay.py`
- Test: `tools/config_oracle/tests/test_replay.py` (marked `slow`; needs git and the tree-sitter CLI)

**Interfaces:**
- Consumes: `runner.check_input` (Task 15), `fixtures.extract` (Task 14), `loader.load_language`/`make_parser`, `loader.build_lock`.
- Produces: `build_parser_at(commit: str, work: Path) -> Parser`, `REPLAYS: list[Replay]`, `run_replay(replay, work) -> ReplayResult(detected: bool, masked_by_cannot_validate: bool, statuses)`, `main() -> int`.

The replay table, from the spec's section 5 numbering:

| # | pre-fix commit | fixture file | case selector | expected |
|---|---|---|---|---|
| 2 | `bad36e4^` | `case_else_preprocessor_test.txt` | every case in the file | ≥1 configuration `discrepancy` with a structure item of kind `missing` or `parent` |
| 3 | `f47350d^` | `scanner_lookahead_extras_test.txt` | name starts with `Comment between a split end and its #else` | configuration `CLEAN22=0` is `discrepancy` with a structure item |
| 4 | `c6b8107^` | `preproc_expression_continuation_operators_test.txt` | the case whose source contains `#if X\n  or (2 = 2)` | `directive-mismatch` with a `condition-extent` item |
| 5 | `04ff498^` | `preproc_split_procedure_tail_test.txt` | name starts with `Split signature followed by a pragma-only` | `representation-violation` whose items contain `var-block-without-var`, and **no** `|structure|` item in any configuration |

A replay is **masked** if the selected cases produce only `cannot-validate` records. That fails the milestone even if nothing else is wrong (spec section 5).

- [ ] **Step 1: Write the test**

```python
# tools/config_oracle/tests/test_replay.py
import pytest

from tools.config_oracle import replay

pytestmark = pytest.mark.slow


@pytest.mark.parametrize("r", replay.REPLAYS, ids=lambda r: f"replay-{r.number}")
def test_replay_is_detected_as_specified(r, tmp_path):
    result = replay.run_replay(r, tmp_path)
    assert not result.masked_by_cannot_validate, result.statuses
    assert result.detected, result.statuses


def test_current_parser_passes_the_same_cases():
    """Positive control: at HEAD these cases have no discrepancy of the replayed kind."""
    for r in replay.REPLAYS:
        result = replay.run_replay(r, None)
        assert not result.detected, (r.number, result.statuses)
```

Register the marker in `tools/config_oracle/tests/conftest.py`:

```python
def pytest_configure(config):
    config.addinivalue_line("markers", "slow: builds historical parsers; run with -m slow")
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tools/config_oracle/tests/test_replay.py -m slow -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'tools.config_oracle.replay'`.

- [ ] **Step 3: Implement**

```python
# tools/config_oracle/replay.py
"""Historical-defect replays (spec section 5): the oracle must catch defects that shipped."""
from __future__ import annotations

import io
import subprocess
import sys
import tarfile
from dataclasses import dataclass
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
    config: str | None = None


@dataclass
class ReplayResult:
    detected: bool
    masked_by_cannot_validate: bool
    statuses: list


def _structure(recs):
    return any("|structure|" in i for r in recs for i in r.items)


REPLAYS = [
    Replay(2, "bad36e4^", "case_else_preprocessor_test.txt", lambda c: True,
           lambda recs: any(r.status == "discrepancy" and any("|structure|missing|" in i or "|structure|parent|" in i
                                                              for i in r.items) for r in recs)),
    Replay(3, "f47350d^", "scanner_lookahead_extras_test.txt",
           lambda c: c.name.startswith("Comment between a split end and its #else"),
           lambda recs: any(r.config == "CLEAN22=0" and r.status == "discrepancy" and _structure([r]) for r in recs)),
    Replay(4, "c6b8107^", "preproc_expression_continuation_operators_test.txt",
           lambda c: b"#if X\n  or (2 = 2)" in c.source,
           lambda recs: any(r.status == "directive-mismatch" and any("|directive|condition-extent|" in i for i in r.items)
                            for r in recs)),
    Replay(5, "04ff498^", "preproc_split_procedure_tail_test.txt",
           lambda c: c.name.startswith("Split signature followed by a pragma-only"),
           lambda recs: all(r.status == "representation-violation" for r in recs)
           and any("var-block-without-var" in i for r in recs for i in r.items)
           and not _structure(recs)),
]


def build_parser_at(commit: str, work: Path):
    work.mkdir(parents=True, exist_ok=True)
    archive = b""
    for paths in (["grammar.js", "src", "tree-sitter.json"], ["grammar.js", "src"]):
        r = subprocess.run(["git", "-C", str(REPO), "archive", commit, *paths], capture_output=True)
        if r.returncode == 0:
            archive = r.stdout
            break
    if not archive:
        raise RuntimeError(f"git archive {commit} failed")
    with tarfile.open(fileobj=io.BytesIO(archive)) as tf:
        tf.extractall(work, filter="data")
    lib = work / "al-replay.dll"
    with loader.build_lock(REPO):
        subprocess.run(["tree-sitter", "build", "--output", str(lib), str(work)], cwd=work,
                       capture_output=True, text=True, check=True)
    return loader.make_parser(loader.load_language(lib))


def run_replay(r: Replay, work):
    parser = (build_parser_at(r.commit, Path(work)) if work is not None
              else loader.make_parser(loader.load_language(loader.ensure_library(REPO))))
    cases = [c for c in fixtures.extract(REPO / "test" / "corpus") if c.file == r.file and r.select(c)]
    if not cases:
        raise AssertionError(f"replay {r.number}: selector matched no case in {r.file}")
    recs = [rec for c in cases for rec in runner.check_input(parser, c.id, c.source)]
    return ReplayResult(r.detect(recs), all(x.status == "cannot-validate" for x in recs),
                        [(x.input_id, x.config, x.status, x.items[:3]) for x in recs])


def main() -> int:
    import tempfile
    failed = 0
    for r in REPLAYS:
        with tempfile.TemporaryDirectory(prefix=f"replay{r.number}-") as tmp:
            res = run_replay(r, Path(tmp))
        ok = res.detected and not res.masked_by_cannot_validate
        failed += not ok
        print(f"replay {r.number}: {'CAUGHT' if ok else 'NOT CAUGHT'}  {res.statuses[:4]}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
```

`build_parser_at` retries without `tree-sitter.json`, for commits that predate it.

- [ ] **Step 4: Run and iterate honestly**

Run: `./tools/ts-lock.sh python -m pytest tools/config_oracle/tests/test_replay.py -m slow -q`
Expected: all replays CAUGHT and the HEAD positive control passes.

Iterate under these rules:
- If a replay is **masked**, because every record is `cannot-validate` (usually `unsupported-type` for a node the old tree uses), the oracle cannot see that defect yet. Implement the lowering for that type under the spec's rules, with its own test, as a sub-task in this task. **Never** change the selector to avoid it.
- If a replay is **not detected** while unmasked, the oracle has a real blind spot. Stop and report it with the old and new trees. It is a design issue for the spec, not something to tune away.
- If the HEAD positive control fails, the current grammar is wrong on that case, or the oracle has a false positive. Investigate and classify it. Do not delete the control.

- [ ] **Step 5: Commit**

```bash
git add tools/config_oracle/replay.py tools/config_oracle/tests/test_replay.py tools/config_oracle/tests/conftest.py
git commit -m "feat(oracle): replays 2-5 against parsers built from pre-fix commits

[BC.History: 0 errors, 100.0% success]"
```

---

### Task 17: The resolver sweep over three corpora; recording the milestone-1 exit

**Files:**
- Create: `docs/superpowers/plans/2026-09-27-config-oracle-milestone-1-results.md`

- [ ] **Step 1: Run the resolve tier over all three corpora**

Run:

```bash
./tools/ts-lock.sh python -m tools.config_oracle run --tier resolve \
  --root ./BC.History --root ./DC --root "H:/Git/BC28.1" \
  --report tools/config_oracle/reports/resolve-sweep
```

Expected: completes. The summary lists `pass` and `cannot-validate` counts, elapsed time and peak RSS. The spec's exit condition is zero `cannot-validate: resolver-*` and zero `reference-error` over production flat AL, **or each one investigated and classified**.

- [ ] **Step 2: Classify every non-pass record**

Run: `python - <<'EOF'` with this body to group the findings:

```python
import json, collections
c = collections.Counter()
ex = {}
for line in open("tools/config_oracle/reports/resolve-sweep/findings.jsonl", encoding="utf-8"):
    r = json.loads(line)
    if r["status"] != "pass":
        key = r["items"][0].split("@")[0].split(",")[0]
        c[key] += 1
        ex.setdefault(key, (r["input_id"], r["config"], r["items"][0][:160]))
for k, v in c.most_common():
    print(v, k, ex[k])
EOF
```

For each group, decide which it is:
- **resolver defect**: fix `directives.py`, add a test, and rerun;
- **compiler-rejected construct**: confirm with `probe_alc`-style compilation of the minimal text;
- **grammar defect**: a reference-error on text `alc` accepts. Add it to `docs/deferred-work.md`, with the file and configuration, as a new item;
- **invalid configuration**: an assignment the product never ships. Record it; do not exclude it silently.

- [ ] **Step 3: Run the quick tier and the replays one final time, and record everything**

Run:

```bash
./tools/ts-lock.sh python -m tools.config_oracle run --tier quick --report tools/config_oracle/reports/quick
./tools/ts-lock.sh python -m tools.config_oracle replay
python -m pytest tools/config_oracle/tests -q
```

Write `docs/superpowers/plans/2026-09-27-config-oracle-milestone-1-results.md`:

```markdown
# Config oracle — milestone 1 results

Measured on <date>, grammar <sha from the report header>.

## Exit criteria (spec, Milestones item 1)

| Criterion | Result | Evidence |
|---|---|---|
| Replay 2 caught (structure) | <CAUGHT/NOT> | `python -m tools.config_oracle replay` line |
| Replay 3 caught (structure) | ... | ... |
| Replay 4 caught (directive-mismatch) | ... | ... |
| Replay 5 caught by representation, NOT structure | ... | ... |
| No replay masked by cannot-validate | ... | ... |
| Positive controls pass | ... | `pytest tools/config_oracle/tests` |
| Resolver sweep: resolver-* cannot-validate | <n>, each classified below | resolve-sweep summary |
| Resolver sweep: reference-error | <n>, each classified below | ... |
| Elapsed time, resolve sweep | <s> | summary |
| Peak memory, resolve sweep | <MiB> | summary |
| Elapsed time and peak memory, quick tier | <s>, <MiB> | quick summary |

## Classified findings

<one row per group from Step 2: group, count, example file/config, classification, action>

## Quick tier snapshot

<status counts; the unsupported-type counts per type, which order milestone 2-3 work>
```

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/plans/2026-09-27-config-oracle-milestone-1-results.md docs/deferred-work.md tools/config_oracle
git commit -m "docs(oracle): milestone 1 results — replays, resolver sweep, time and memory

[BC.History: 0 errors, 100.0% success]"
```

---

## Self-review notes (kept for the executor)

- **Deferred to milestone 2 and later, not missing:** the report-brace ownership assembler, expression continuation and the precedence table, the witness matrix, the deterministic transformations, gate wiring (Step 5e, CI, `gate_selftest`), the baseline file, and the `grammar.js` contract annotations.
- **One spec item is adapted, and says so:** the trivia check compares against the resolver by `(kind, start)` and compares ends only between the two trees (Task 7). The resolver cannot know token extents without the grammar.
- **Replay 1 (CRMSetupDefaults) and replay 6 remain in milestone 2,** as the spec orders them.
