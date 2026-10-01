#!/bin/bash
#
# Checks tools/default-cc.sh (the rule is stated there). Runs anywhere: `uname`
# and `clang-cl` are stubs on a private PATH, so the Windows cases run on Linux
# CI too. Exit 0 all pass, 1 a case failed.
#
#   bash tools/test-default-cc.sh
#
# Every case compares EXACTLY: CC, TS_AL_DEFAULT_CC and the number of stderr
# lines. A suffix match once let "explicit CC wins" pass with want=cl while the
# rule had replaced CC with clang-cl -- which also ends in "cl".
#
# The helper is tested through a copy whose LLVM install path points into the
# stub directory, so "absent" can be tested on a machine that has LLVM. Only
# that one literal differs; the copy is checked to have changed.

set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
STUBS=$(mktemp -d)
cleanup() { rm -r -f -- "$STUBS"; }
trap cleanup EXIT
mkdir -p "$STUBS/win" "$STUBS/linux" "$STUBS/llvm" "$STUBS/llvmdir"
printf '#!/bin/sh\necho MINGW64_NT-10.0\n' > "$STUBS/win/uname"
printf '#!/bin/sh\necho Linux\n' > "$STUBS/linux/uname"
printf '#!/bin/sh\nexit 0\n' > "$STUBS/llvm/clang-cl"
chmod +x "$STUBS"/*/uname "$STUBS/llvm/clang-cl"
BASE="$(dirname "$(command -v cat)")"   # bash, cat, cygpath -- and no clang-cl

LLVM_REAL="C:/Program Files/LLVM/bin/clang-cl.exe"
LLVM_STUB="$STUBS/llvmdir/clang-cl.exe"
HELPER="$STUBS/default-cc.sh"
sed "s#$LLVM_REAL#$LLVM_STUB#" "$HERE/default-cc.sh" > "$HELPER"
if cmp -s "$HELPER" "$HERE/default-cc.sh" || ! grep -qF "$LLVM_STUB" "$HELPER"; then
    echo "test-default-cc: FAIL - could not retarget the LLVM install path in the copy"
    exit 1
fi

# What the helper hands tree-sitter for the PATH stub: C:/... on Windows, as is elsewhere.
ON_PATH="$STUBS/llvm/clang-cl"
command -v cygpath >/dev/null 2>&1 && ON_PATH="$(cygpath -m "$ON_PATH")"

fails=0
# case_ <name> <want "CC|TS_AL_DEFAULT_CC|stderr-lines"> <PATH> [VAR=value ...]
# An unset variable reads as "-".
case_() {
    local name=$1 want=$2 path=$3; shift 3
    local got
    got=$(env -u CC -u TS_AL_DEFAULT_CC -u TS_AL_DEFAULT_CC_SAID -u TS_AL_NO_CLANG "$@" PATH="$path" \
          bash -c '. "$1" 2>"$2"; echo "${CC-"-"}|${TS_AL_DEFAULT_CC-"-"}|$(cat "$2" | wc -l | tr -d " ")"' \
          _ "$HELPER" "$STUBS/stderr")
    if [ "$got" = "$want" ]; then
        echo "ok   $name"
    else
        echo "FAIL $name: got [$got], want [$want]"
        fails=1
    fi
}

W="$STUBS/win"
# $LLVM_STUB does not exist until S8 creates it.
case_ "S1 unset, clang-cl on PATH"     "$ON_PATH|$ON_PATH|1"  "$W:$STUBS/llvm:$BASE"
case_ "S2 explicit CC wins"            "sentinel-cc-xyz|-|1"  "$W:$STUBS/llvm:$BASE" CC=sentinel-cc-xyz
case_ "S3 opt-out"                     "-|-|1"                "$W:$STUBS/llvm:$BASE" TS_AL_NO_CLANG=1
case_ "S4 inherited default, opt-out"  "-|-|1"                "$W:$STUBS/llvm:$BASE" TS_AL_NO_CLANG=1 \
                                                              CC=/x/clang-cl TS_AL_DEFAULT_CC=/x/clang-cl
case_ "S5 not Windows"                 "-|-|0"                "$STUBS/linux:$STUBS/llvm:$BASE"
case_ "S6 clang-cl absent"             "-|-|1"                "$W:$BASE"
case_ "S7 nested, same verdict, quiet" "$ON_PATH|$ON_PATH|0"  "$W:$STUBS/llvm:$BASE" \
      CC="$ON_PATH" TS_AL_DEFAULT_CC="$ON_PATH" \
      TS_AL_DEFAULT_CC_SAID="clang-cl (CC was unset; TS_AL_NO_CLANG=1 for MSVC)"
touch "$LLVM_STUB"
case_ "S8 unset, clang-cl in LLVM dir" "$LLVM_STUB|$LLVM_STUB|1" "$W:$BASE"

if [ "$fails" -eq 0 ]; then echo "test-default-cc: PASS"; else echo "test-default-cc: FAIL"; fi
exit "$fails"
