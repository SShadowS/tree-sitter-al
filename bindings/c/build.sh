#!/usr/bin/env bash
# bindings/c/build.sh — produce the fat shim shared library.
# Env knobs:
#   TS_VERSION   tree-sitter runtime tag (default 0.25.10)
#   OUT          output dir (default <repo>/dist)
#   CC           compiler (default cc)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$SCRIPT_DIR/../.."
TS_VERSION="${TS_VERSION:-0.25.10}"
OUT="${OUT:-$ROOT/dist}"
mkdir -p "$OUT" "$ROOT/.cache"

TS_DIR="$ROOT/.cache/tree-sitter-${TS_VERSION}"
if [ ! -d "$TS_DIR" ]; then
  echo "Fetching tree-sitter v${TS_VERSION}..."
  curl -sSL "https://github.com/tree-sitter/tree-sitter/archive/refs/tags/v${TS_VERSION}.tar.gz" \
    | tar -xz -C "$ROOT/.cache"
fi

CC="${CC:-cc}"
EXT=".so"
SO_FLAGS="-shared -fPIC -fvisibility=hidden"
case "$(uname -s)" in
  Darwin)
    EXT=".dylib"
    SO_FLAGS="-dynamiclib -fPIC -fvisibility=hidden"
    ;;
  MINGW*|MSYS*|CYGWIN*)
    EXT=".dll"
    SO_FLAGS="-shared"   # __declspec on functions handles exports on Windows
    ;;
esac

ARTIFACT="$OUT/tree-sitter-al${EXT}"
echo "Building $ARTIFACT with $CC..."
"$CC" -O2 $SO_FLAGS \
  -I"$TS_DIR/lib/include" -I"$TS_DIR/lib/src" \
  -I"$ROOT/src" \
  "$TS_DIR/lib/src/lib.c" \
  "$ROOT/src/parser.c" \
  "$ROOT/src/scanner.c" \
  "$SCRIPT_DIR/al_shim.c" \
  -o "$ARTIFACT"

# Post-build hardening
case "$(uname -s)" in
  Linux)
    strip --strip-unneeded "$ARTIFACT"
    ;;
  Darwin)
    strip -x "$ARTIFACT"
    codesign --force --sign - "$ARTIFACT"
    codesign --verify --verbose "$ARTIFACT"
    ;;
esac

ls -la "$ARTIFACT"
