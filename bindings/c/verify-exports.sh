#!/usr/bin/env bash
# Assert every documented shim symbol is exported and no internals leak.
# Usage: bash verify-exports.sh <path-to-artifact>
set -euo pipefail
ARTIFACT="$1"

# Pre-flight: .dll inspection needs llvm-objdump or objdump.
case "$ARTIFACT" in
  *.dll)
    if ! command -v llvm-objdump >/dev/null 2>&1 && ! command -v objdump >/dev/null 2>&1; then
      echo "verify-exports: neither llvm-objdump nor objdump available — install MinGW binutils or LLVM" >&2
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

case "$ARTIFACT" in
  *.so)    EXPORTS=$(nm -D --defined-only "$ARTIFACT" | awk '{print $3}') ;;
  *.dylib) EXPORTS=$(nm -gU "$ARTIFACT" | awk '{print $3}' | sed 's/^_//') ;;
  *.dll)   EXPORTS=$(
             if command -v llvm-objdump > /dev/null 2>&1; then
               llvm-objdump -p "$ARTIFACT" 2>/dev/null \
                 | awk '/\[Ordinal\/Name Pointer\] Table/{p=1;next} p && /^\t\[/{print $NF} p && /^[^\t]/{p=0}'
             else
               objdump -p "$ARTIFACT" \
                 | awk '/\[Ordinal\/Name Pointer\] Table/{p=1;next} p && /^\t\[/{print $NF} p && /^[^\t]/{p=0}'
             fi
           ) ;;
  *) echo "verify-exports: unknown artifact type: $ARTIFACT" >&2; exit 1 ;;
esac

if [ -z "$EXPORTS" ]; then
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

LEAKED=$(echo "$EXPORTS" | grep -E '^(ts_|tree_sitter_al_external_)' || true)
if [ -n "$LEAKED" ]; then
  echo "LEAKED internals (must not be exported):" >&2
  echo "$LEAKED" >&2
  MISSING=1
fi

if [ "$MISSING" -ne 0 ]; then
  exit 1
fi
echo "verify-exports: OK (${#REQUIRED[@]} symbols, no leaks)"
