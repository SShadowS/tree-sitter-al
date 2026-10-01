"""Re-runnable alc probes for AL conditional-directive semantics.

Each probe is a tiny project. Text that must be INACTIVE is `GARBAGE!! ;;; }{`:
alc does not parse inactive text, so a probe compiles iff the compiler selected
exactly the arms predicted. Every expectation below was recorded from alc on
2026-09-27 and is the source of truth for docs/preproc-directive-semantics.md.

    python -m tools.config_oracle.probe_alc --check     # exit 1 on any change
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from tools.alc_probe import core

G = core.GARBAGE


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
    # B2 (2026-10-01): directive words are whole words, and nothing but a `//` comment may
    # follow `#endif`/`#else`. Every text outside the probed line is valid ACTIVE code, so a
    # REJECT is the directive line itself; `{G}` sits only where a prefix-as-`#else`
    # reading would make it inactive and so turn that reading into an ACCEPT.
    ("prefix_ifx_rejected", unit("#ifx A\n        Message('t');\n#endif"), ["A"], False),
    ("prefix_endifx_rejected", unit("#if A\n        Message('t');\n#endifx"), ["A"], False),
    ("prefix_elsex_rejected", unit(f"#if A\n        Message('t');\n#elsex\n        {G}\n#endif"), ["A"], False),
    ("prefix_elsewhere_rejected", unit(f"#if A\n        Message('t');\n#elsewhere\n        {G}\n#endif"), ["A"], False),
    ("prefix_elifx_rejected", unit(f"#if A\n        Message('t');\n#elifx A\n        {G}\n#endif"), ["A"], False),
    ("prefix_regionx_rejected", unit("#regionx\n        Message('t');\n#endregion"), [], False),
    ("prefix_endregionx_rejected", unit("#region\n        Message('t');\n#endregionx"), [], False),
    ("prefix_pragmax_rejected", unit("#pragmax warning disable AL0001\n        Message('t');"), [], False),
    ("prefix_definex_rejected", "#definex A\n" + unit("        Message('t');"), [], False),
    ("prefix_undefx_rejected", "#undefx A\n" + unit("        Message('t');"), [], False),
    ("endif_semicolon_rejected", unit("#if A\n        Message('t');\n#endif;"), ["A"], False),
    ("endif_trailing_word_rejected", unit("#if A\n        Message('t');\n#endif X"), ["A"], False),
    ("else_line_comment_only", unit(f"#if A\n        Message('t');\n#else // c\n        {G}\n#endif"), ["A"], True),
    ("else_semicolon_rejected", unit(f"#if A\n        Message('t');\n#else;\n        {G}\n#endif"), ["A"], False),
    ("block_comment_on_elif_rejected", unit(f"#if B\n        {G}\n#elif A /* c */\n        Message('t');\n#endif"), ["A"], False),
    ("endregion_semicolon_accepted", unit("#region R\n        Message('t');\n#endregion;"), [], True),
    ("cap_Else_word", unit(f"#if A\n        Message('t');\n#Else\n        {G}\n#endif"), ["A"], True),
    ("endif_at_eof_no_newline", unit("        Message('t');") + "#if A\n#endif", ["A"], True),
]


def compile_probe(workdir: Path, name: str, source: str, symbols: list[str]) -> tuple[str, bool, list[str]]:
    """(name, accepted, source codes) through the shared core, tools/alc_probe/core.py.

    The directory name carries a hash of `name`, so two probes whose names differ only
    in case (`true_literal`, `TRUE_literal`) never share a directory on a
    case-insensitive filesystem.
    """
    tag = hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]
    v = core.compile_project(workdir / f"{name}-{tag}", source, symbols)
    return name, v.kind == core.ACCEPT, list(v.source_codes)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="exit 1 if any outcome differs from its recorded expectation")
    args = parser.parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="alc-probe-") as tmp:
        with ThreadPoolExecutor(max_workers=6) as pool:
            # One directory per probe, keyed by index: `true_literal` and `TRUE_literal` are the
            # same directory on a case-insensitive filesystem, and shared it until A2 (AL1028).
            verdicts = list(pool.map(lambda ip: core.compile_project(Path(tmp) / f"{ip[0]:03d}", ip[1][1], ip[1][2]),
                                     enumerate(PROBES)))
    failures = 0
    for (name, _, _, expected), v in zip(PROBES, verdicts):
        accepted = v.kind == core.ACCEPT
        ok = accepted == expected
        failures += not ok
        print(f"{'ok  ' if ok else 'DIFF'} {name:42} {'ACCEPT' if accepted else 'REJECT'} {','.join(v.source_codes)}")
    broken = [name for (name, *_), v in zip(PROBES, verdicts) if v.kind == core.BROKEN]
    if broken or verdicts[0].kind != core.ACCEPT or verdicts[1].kind != core.REJECT:
        print(f"probe project is broken: the sanity/garbage controls did not behave, or BROKEN: {broken}", file=sys.stderr)
        return 2
    return 1 if (args.check and failures) else 0


if __name__ == "__main__":
    sys.exit(main())
