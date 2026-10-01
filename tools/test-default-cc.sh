#!/bin/bash
#
# Checks tools/default-cc.sh (the rule is stated there). Runs anywhere: `uname`
# and `clang-cl` are stubs on a private PATH, so the Windows cases run on Linux
# CI too. Exit 0 all pass, 1 a case failed.
#
#   bash tools/test-default-cc.sh

set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
STUBS=$(mktemp -d)
cleanup() { rm -r -f -- "$STUBS"; }
trap cleanup EXIT
mkdir -p "$STUBS/win" "$STUBS/linux" "$STUBS/llvm"
printf '#!/bin/sh\necho MINGW64_NT-10.0\n' > "$STUBS/win/uname"
printf '#!/bin/sh\necho Linux\n' > "$STUBS/linux/uname"
printf '#!/bin/sh\nexit 0\n' > "$STUBS/llvm/clang-cl"
touch "$STUBS/clang-cl.exe"
chmod +x "$STUBS"/*/uname "$STUBS/llvm/clang-cl"
BASE="$(dirname "$(command -v cat)")"   # bash, cat, cygpath -- and no clang-cl

fails=0
# case_ <name> <expected CC suffix, or "-" for unset> <PATH> [VAR=value ...]
case_() {
    local name=$1 want=$2 path=$3; shift 3
    local got
    got=$(env -u CC -u TS_AL_DEFAULT_CC -u TS_AL_NO_CLANG "$@" \
          _TS_AL_LLVM_CLANG_CL="${LLVM:-$STUBS/none.exe}" PATH="$path" \
          bash -c '. "$1" 2>/dev/null; echo "${CC-"-"}"' _ "$HERE/default-cc.sh")
    if { [ "$want" = "-" ] && [ "$got" = "-" ]; } || { [ "$want" != "-" ] && [[ "$got" == *"$want" ]]; }; then
        echo "ok   $name"
    else
        echo "FAIL $name: CC=[$got], want [$want]"
        fails=1
    fi
}

case_ "unset, clang-cl on PATH"     clang-cl     "$STUBS/win:$STUBS/llvm:$BASE"
LLVM="$STUBS/clang-cl.exe" \
case_ "unset, clang-cl in LLVM dir" clang-cl.exe "$STUBS/win:$BASE"
case_ "explicit CC wins"            cl           "$STUBS/win:$STUBS/llvm:$BASE" CC=cl
case_ "opt-out"                     -            "$STUBS/win:$STUBS/llvm:$BASE" TS_AL_NO_CLANG=1
case_ "inherited default, opt-out"  -            "$STUBS/win:$STUBS/llvm:$BASE" TS_AL_NO_CLANG=1 \
                                                 CC=/x/clang-cl TS_AL_DEFAULT_CC=/x/clang-cl
case_ "not Windows"                 -            "$STUBS/linux:$STUBS/llvm:$BASE"
case_ "clang-cl absent"             -            "$STUBS/win:$BASE"

if [ "$fails" -eq 0 ]; then echo "test-default-cc: PASS"; else echo "test-default-cc: FAIL"; fi
exit "$fails"
