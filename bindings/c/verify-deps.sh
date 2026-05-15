#!/usr/bin/env bash
# Assert the shim doesn't dynamically link against libtree-sitter (would mean
# we accidentally dynamic-linked the runtime instead of statically bundling) or
# C++ runtimes (libstdc++ / libc++abi — our shim is pure C; no C++ runtime
# should appear). libgcc_s is allowed (MinGW Windows builds depend on
# libgcc_s_seh-1.dll for unwind support — acceptable baseline).
# Usage: bash verify-deps.sh <path-to-artifact>
set -euo pipefail
ARTIFACT="$1"

FORBIDDEN_PATTERNS=("libtree-sitter" "libstdc\+\+" "libc\+\+abi")

case "$ARTIFACT" in
  *.so)
    DEPS=$( { ldd "$ARTIFACT" || objdump -p "$ARTIFACT" | grep NEEDED; } 2>&1 )
    ;;
  *.dylib)
    DEPS=$(otool -L "$ARTIFACT")
    ;;
  *.dll)
    DEPS=$(objdump -p "$ARTIFACT" | grep -i "DLL Name")
    ;;
  *) echo "verify-deps: unknown artifact type: $ARTIFACT" >&2; exit 1 ;;
esac

echo "$DEPS"

FAIL=0
for pat in "${FORBIDDEN_PATTERNS[@]}"; do
  if echo "$DEPS" | grep -qE "$pat"; then
    echo "FORBIDDEN dependency match: $pat" >&2
    FAIL=1
  fi
done
[ "$FAIL" -eq 0 ] && echo "verify-deps: OK"
exit $FAIL
