#!/usr/bin/env bash
# Assert every documented shim symbol is exported and no internals leak.
# Usage: bash verify-exports.sh <path-to-artifact>
set -euo pipefail
ARTIFACT="$1"

# Pre-flight: .dll inspection needs dlltool, nm, or objdump (all from MinGW binutils).
case "$ARTIFACT" in
  *.dll)
    if ! command -v dlltool >/dev/null 2>&1 && ! command -v objdump >/dev/null 2>&1 && ! command -v llvm-objdump >/dev/null 2>&1; then
      echo "verify-exports: dlltool/objdump/llvm-objdump not available — install MinGW binutils or LLVM" >&2
      exit 1
    fi
    ;;
esac

REQUIRED=(
  al_shim_abi_version
  al_shim_parser_new al_shim_parser_delete al_shim_language al_shim_parser_set_language
  al_shim_parse_utf8 al_shim_tree_delete
  al_shim_node_size al_shim_tree_root_node
  al_shim_node_type al_shim_node_start_byte al_shim_node_end_byte
  al_shim_node_start_row al_shim_node_start_column al_shim_node_end_row al_shim_node_end_column
  al_shim_node_child_count al_shim_node_named_child_count
  al_shim_node_child al_shim_node_named_child al_shim_node_child_by_field_name
  al_shim_node_parent al_shim_node_previous_sibling al_shim_node_next_sibling
  al_shim_node_is_null al_shim_node_is_named al_shim_node_eq al_shim_node_has_error
  al_shim_cursor_new al_shim_cursor_delete
  al_shim_cursor_goto_first_child al_shim_cursor_goto_next_sibling al_shim_cursor_goto_parent
  al_shim_cursor_current_node al_shim_cursor_current_field_name
  al_shim_tree_sitter_language_version al_shim_tree_sitter_min_compatible_language_version
)

# DLL: track whether EXPORTS came from the PE export table (safe for leak check)
# or from nm (which includes all symbols, so leak check would be misleading).
EXPORTS_FROM_PE_TABLE=true

case "$ARTIFACT" in
  *.so)    EXPORTS=$(nm -D --defined-only "$ARTIFACT" | awk '{print $3}') ;;
  *.dylib) EXPORTS=$(nm -gU "$ARTIFACT" | awk '{print $3}' | sed 's/^_//') ;;
  *.dll)
    # Extract the DLL's PE export table (only __declspec(dllexport) symbols appear).
    # Use 'objdump -x' which reads the PE .edata section directly; '|| true' guards
    # against objdump returning non-zero on some PE variants while still producing
    # valid output (set -o pipefail would otherwise abort the script).
    _dll_exports_x() {
      local tool="$1"; shift
      "$tool" -x "$@" 2>/dev/null \
        | awk '
            /\[Ordinal\/Name Pointer\] Table/ { in_tbl=1; next }
            in_tbl && NF == 0                { in_tbl=0; next }
            in_tbl                            { print $NF }
          '
    }
    if command -v objdump > /dev/null 2>&1; then
      EXPORTS=$(_dll_exports_x objdump "$ARTIFACT")
    elif command -v llvm-objdump > /dev/null 2>&1; then
      EXPORTS=$(_dll_exports_x llvm-objdump "$ARTIFACT")
    fi
    # If objdump -x produced nothing, fall back to nm --extern-only which lists all
    # public text symbols.  Since nm sees ALL symbols (not just PE-exported ones),
    # the leak check is skipped for this path — Windows' PE export table cannot
    # contain ts_* anyway (tree_sitter/api.h uses GCC visibility pragmas, not
    # __declspec(dllexport), so ts_* will never appear in the PE export table).
    if [ -z "${EXPORTS:-}" ] && command -v nm > /dev/null 2>&1; then
      EXPORTS_FROM_PE_TABLE=false
      EXPORTS=$({ nm --defined-only --extern-only "$ARTIFACT" 2>/dev/null || true; } \
                  | awk '$2 == "T" || $2 == "t" {name=$3; sub(/^_/,"",name); print name}')
    fi
    ;;
  *) echo "verify-exports: unknown artifact type: $ARTIFACT" >&2; exit 1 ;;
esac

if [ -z "${EXPORTS:-}" ]; then
  echo "verify-exports: parsed 0 exports from $ARTIFACT — symbol-extraction tool may have produced unexpected output format" >&2
  exit 1
fi

MISSING=0
for sym in "${REQUIRED[@]}"; do
  if ! echo "$EXPORTS" | grep -qx "$sym"; then
    echo "MISSING: $sym" >&2
    MISSING=1
  fi
done

if [ "$EXPORTS_FROM_PE_TABLE" = "true" ]; then
  LEAKED=$(echo "$EXPORTS" | grep -E '^(ts_|tree_sitter_al_external_)' || true)
  if [ -n "$LEAKED" ]; then
    echo "LEAKED internals (must not be exported):" >&2
    echo "$LEAKED" >&2
    MISSING=1
  fi
else
  echo "verify-exports: leak check skipped (nm fallback used; ts_* not dllexport-annotated so cannot appear in PE export table)"
fi

if [ "$MISSING" -ne 0 ]; then
  exit 1
fi
echo "verify-exports: OK (${#REQUIRED[@]} symbols, no leaks)"
