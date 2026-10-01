#!/bin/bash
#
# default-cc.sh -- SOURCED, not run. Makes clang-cl the default C compiler for
# local builds on Windows when LLVM is installed.
#
#   . "$(dirname "$0")/tools/default-cc.sh"
#
# WHY: an MSVC-built al.dll parses about 2.05x slower than a clang-cl one, and
# MSVC takes 11.3 s to compile parser.c+scanner.c against clang-cl's 2.8 s. The
# trees are identical on all four corpora (70,355 files). docs/deferred-work.md
# item 21 has the evidence. `tree-sitter build` and `tree-sitter test` honour CC.
#
# THE RULE (tools/query_coverage/loader.build_env is the Python twin -- keep
# the two identical, and do not add a third copy):
#   - Windows only (MSYS / Git Bash). Elsewhere this file does nothing at all.
#   - Only when CC is unset or empty. An explicit CC always wins: CC=cl forces MSVC.
#   - Not when TS_AL_NO_CLANG=1.
#   - clang-cl on PATH, otherwise "C:/Program Files/LLVM/bin/clang-cl.exe".
#     Found: export CC as that path. Not found: change nothing (MSVC, as before).
#   - TS_AL_DEFAULT_CC records the value this rule chose, so a nested source
#     (validate-grammar.sh under ts-lock.sh) re-applies the rule instead of
#     mistaking the inherited default for an explicit CC.
#
# It prints one line naming the compiler, to STDERR: ts-lock.sh wraps commands
# whose stdout is parsed (`--json-summary`, tools/perf's probe). The line never
# puts a path separator before a compiler name, so tools/perf/procs.py's
# parse_invocation cannot mistake it for the compiler command line.
#
# The shared al.dll (see tools/ts-lock.sh) is rebuilt by whichever compiler
# builds next. That is harmless: the trees are identical either way.

ts_al_default_cc() {
    case "$(uname -s 2>/dev/null)" in
        MINGW*|MSYS*|CYGWIN*) ;;
        *) return 0 ;;
    esac

    if [ -n "${TS_AL_DEFAULT_CC:-}" ] && [ "${CC:-}" = "$TS_AL_DEFAULT_CC" ]; then
        unset CC
    fi
    unset TS_AL_DEFAULT_CC

    if [ -n "${CC:-}" ]; then
        echo "default-cc: ${CC##*[\\/]} (CC set by caller)" >&2
        return 0
    fi
    if [ "${TS_AL_NO_CLANG:-}" = "1" ]; then
        echo "default-cc: MSVC (TS_AL_NO_CLANG=1)" >&2
        return 0
    fi

    # _TS_AL_LLVM_CLANG_CL exists only so tools/test-default-cc.sh can test absence.
    local found llvm="${_TS_AL_LLVM_CLANG_CL:-C:/Program Files/LLVM/bin/clang-cl.exe}"
    found="$(command -v clang-cl 2>/dev/null || true)"
    # tree-sitter is a native exe: hand it C:/..., never an MSYS /c/... path.
    if [ -n "$found" ] && command -v cygpath >/dev/null 2>&1; then
        found="$(cygpath -m "$found")"
    fi
    if [ -z "$found" ] && [ -f "$llvm" ]; then
        found="$llvm"
    fi
    if [ -z "$found" ]; then
        echo "default-cc: MSVC (no clang-cl found)" >&2
        return 0
    fi

    export CC="$found" TS_AL_DEFAULT_CC="$found"
    echo "default-cc: clang-cl (CC was unset; TS_AL_NO_CLANG=1 or CC=cl for MSVC)" >&2
}
ts_al_default_cc
unset -f ts_al_default_cc
