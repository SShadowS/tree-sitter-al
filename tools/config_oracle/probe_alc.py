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
