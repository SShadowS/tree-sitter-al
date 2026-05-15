/* bindings/c/al_shim.c
 *
 * Implementation of the ABI declared in al_shim.h. Every public function:
 *   - is annotated AL_SHIM_EXPORT (matches the header)
 *   - reads/writes TSNode buffers via memcpy (never *(TSNode *), to avoid
 *     alignment + strict-aliasing UB on ARM64)
 *   - returns uint32_t for booleans (cross-compiler FFI stable)
 */
#include <stdlib.h>
#include <string.h>
#include <tree_sitter/api.h>
#include "al_shim.h"

extern TSLanguage *tree_sitter_al(void);

static TSNode read_node(const void *buf) {
  TSNode n;
  memcpy(&n, buf, sizeof n);
  return n;
}

static void write_node(void *out, TSNode n) {
  memcpy(out, &n, sizeof n);
}

AL_SHIM_EXPORT uint32_t al_shim_abi_version(void) {
  return ((uint32_t)AL_SHIM_ABI_VERSION_MAJOR << 16) | (uint32_t)AL_SHIM_ABI_VERSION_MINOR;
}

AL_SHIM_EXPORT void *al_shim_parser_new(void) { return ts_parser_new(); }
AL_SHIM_EXPORT void  al_shim_parser_delete(void *parser) { ts_parser_delete((TSParser *)parser); }

AL_SHIM_EXPORT const void *al_shim_language(void) { return tree_sitter_al(); }

AL_SHIM_EXPORT uint32_t al_shim_parser_set_language(void *parser, const void *language) {
  return ts_parser_set_language((TSParser *)parser, (const TSLanguage *)language) ? 1u : 0u;
}

AL_SHIM_EXPORT void *al_shim_parse_utf8(void *parser, const char *source, uint32_t length) {
  return ts_parser_parse_string((TSParser *)parser, NULL, source, length);
}

AL_SHIM_EXPORT void al_shim_tree_delete(void *tree) { ts_tree_delete((TSTree *)tree); }

AL_SHIM_EXPORT uint32_t al_shim_node_size(void) { return (uint32_t)sizeof(TSNode); }

AL_SHIM_EXPORT void al_shim_tree_root_node(const void *tree, void *out_node) {
  write_node(out_node, ts_tree_root_node((const TSTree *)tree));
}

AL_SHIM_EXPORT const char *al_shim_node_type(const void *node) {
  return ts_node_type(read_node(node));
}
AL_SHIM_EXPORT uint32_t al_shim_node_start_byte(const void *node) { return ts_node_start_byte(read_node(node)); }
AL_SHIM_EXPORT uint32_t al_shim_node_end_byte(const void *node)   { return ts_node_end_byte(read_node(node)); }
AL_SHIM_EXPORT uint32_t al_shim_node_start_row(const void *node)  { return ts_node_start_point(read_node(node)).row; }
AL_SHIM_EXPORT uint32_t al_shim_node_start_column(const void *node){ return ts_node_start_point(read_node(node)).column; }
AL_SHIM_EXPORT uint32_t al_shim_node_end_row(const void *node)    { return ts_node_end_point(read_node(node)).row; }
AL_SHIM_EXPORT uint32_t al_shim_node_end_column(const void *node) { return ts_node_end_point(read_node(node)).column; }

AL_SHIM_EXPORT uint32_t al_shim_node_child_count(const void *node) { return ts_node_child_count(read_node(node)); }
AL_SHIM_EXPORT uint32_t al_shim_node_named_child_count(const void *node) { return ts_node_named_child_count(read_node(node)); }

AL_SHIM_EXPORT void al_shim_node_child(const void *node, uint32_t i, void *out_child) {
  write_node(out_child, ts_node_child(read_node(node), i));
}
AL_SHIM_EXPORT void al_shim_node_named_child(const void *node, uint32_t i, void *out_child) {
  write_node(out_child, ts_node_named_child(read_node(node), i));
}
AL_SHIM_EXPORT void al_shim_node_child_by_field_name(
  const void *node, const char *field_name, uint32_t field_name_len, void *out_child
) {
  write_node(out_child, ts_node_child_by_field_name(read_node(node), field_name, field_name_len));
}
AL_SHIM_EXPORT void al_shim_node_parent(const void *node, void *out_parent) {
  write_node(out_parent, ts_node_parent(read_node(node)));
}
AL_SHIM_EXPORT void al_shim_node_previous_sibling(const void *node, void *out_sibling) {
  write_node(out_sibling, ts_node_prev_sibling(read_node(node)));
}
AL_SHIM_EXPORT void al_shim_node_next_sibling(const void *node, void *out_sibling) {
  write_node(out_sibling, ts_node_next_sibling(read_node(node)));
}

AL_SHIM_EXPORT uint32_t al_shim_node_is_null(const void *node) { return ts_node_is_null(read_node(node)) ? 1u : 0u; }
AL_SHIM_EXPORT uint32_t al_shim_node_is_named(const void *node) { return ts_node_is_named(read_node(node)) ? 1u : 0u; }
AL_SHIM_EXPORT uint32_t al_shim_node_eq(const void *a, const void *b) {
  return ts_node_eq(read_node(a), read_node(b)) ? 1u : 0u;
}
AL_SHIM_EXPORT uint32_t al_shim_node_has_error(const void *node) {
  return ts_node_has_error(read_node(node)) ? 1u : 0u;
}

AL_SHIM_EXPORT void *al_shim_cursor_new(const void *node) {
  TSTreeCursor *c = (TSTreeCursor *)malloc(sizeof(TSTreeCursor));
  if (!c) return NULL;
  *c = ts_tree_cursor_new(read_node(node));
  return c;
}
AL_SHIM_EXPORT void al_shim_cursor_delete(void *cursor) {
  if (!cursor) return;
  ts_tree_cursor_delete((TSTreeCursor *)cursor);
  free(cursor);
}
AL_SHIM_EXPORT uint32_t al_shim_cursor_goto_first_child(void *c) {
  return ts_tree_cursor_goto_first_child((TSTreeCursor *)c) ? 1u : 0u;
}
AL_SHIM_EXPORT uint32_t al_shim_cursor_goto_next_sibling(void *c) {
  return ts_tree_cursor_goto_next_sibling((TSTreeCursor *)c) ? 1u : 0u;
}
AL_SHIM_EXPORT uint32_t al_shim_cursor_goto_parent(void *c) {
  return ts_tree_cursor_goto_parent((TSTreeCursor *)c) ? 1u : 0u;
}
AL_SHIM_EXPORT void al_shim_cursor_current_node(void *c, void *out_node) {
  write_node(out_node, ts_tree_cursor_current_node((const TSTreeCursor *)c));
}
AL_SHIM_EXPORT const char *al_shim_cursor_current_field_name(void *c) {
  return ts_tree_cursor_current_field_name((const TSTreeCursor *)c);
}

AL_SHIM_EXPORT uint32_t al_shim_tree_sitter_language_version(void) {
  return ts_language_version(tree_sitter_al());
}
AL_SHIM_EXPORT uint32_t al_shim_tree_sitter_min_compatible_language_version(void) {
  /* libtree-sitter exports a constant in api.h; mirror it explicitly */
  return TREE_SITTER_MIN_COMPATIBLE_LANGUAGE_VERSION;
}
