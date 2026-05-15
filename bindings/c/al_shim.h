/* bindings/c/al_shim.h
 *
 * Public ABI for al-sem and other Bun consumers. Single declaration site.
 * Bumping AL_SHIM_ABI_VERSION_MAJOR is a breaking change; MINOR is additive only.
 * Every public function MUST be annotated with AL_SHIM_EXPORT.
 */
#ifndef AL_SHIM_H
#define AL_SHIM_H

#include <stdint.h>

#if defined(_WIN32)
  #define AL_SHIM_EXPORT __declspec(dllexport)
#else
  #define AL_SHIM_EXPORT __attribute__((visibility("default")))
#endif

#define AL_SHIM_ABI_VERSION_MAJOR 1
#define AL_SHIM_ABI_VERSION_MINOR 0

#ifdef __cplusplus
extern "C" {
#endif

AL_SHIM_EXPORT uint32_t al_shim_abi_version(void);

/* Parser lifecycle */
AL_SHIM_EXPORT void *al_shim_parser_new(void);
AL_SHIM_EXPORT void  al_shim_parser_delete(void *parser);
AL_SHIM_EXPORT const void *al_shim_language(void);
AL_SHIM_EXPORT uint32_t al_shim_parser_set_language(void *parser, const void *language);

/* Parse */
AL_SHIM_EXPORT void *al_shim_parse_utf8(void *parser, const char *source, uint32_t length);
AL_SHIM_EXPORT void  al_shim_tree_delete(void *tree);

/* Node access (opaque buffer of al_shim_node_size() bytes) */
AL_SHIM_EXPORT uint32_t al_shim_node_size(void);
AL_SHIM_EXPORT void al_shim_tree_root_node(const void *tree, void *out_node);

AL_SHIM_EXPORT const char *al_shim_node_type(const void *node);
AL_SHIM_EXPORT uint32_t al_shim_node_start_byte(const void *node);
AL_SHIM_EXPORT uint32_t al_shim_node_end_byte(const void *node);
AL_SHIM_EXPORT uint32_t al_shim_node_start_row(const void *node);
AL_SHIM_EXPORT uint32_t al_shim_node_start_column(const void *node);
AL_SHIM_EXPORT uint32_t al_shim_node_end_row(const void *node);
AL_SHIM_EXPORT uint32_t al_shim_node_end_column(const void *node);

AL_SHIM_EXPORT uint32_t al_shim_node_child_count(const void *node);
AL_SHIM_EXPORT uint32_t al_shim_node_named_child_count(const void *node);
AL_SHIM_EXPORT void al_shim_node_child(const void *node, uint32_t i, void *out_child);
AL_SHIM_EXPORT void al_shim_node_named_child(const void *node, uint32_t i, void *out_child);
AL_SHIM_EXPORT void al_shim_node_child_by_field_name(
  const void *node,
  const char *field_name,
  uint32_t field_name_len,
  void *out_child
);
AL_SHIM_EXPORT void al_shim_node_parent(const void *node, void *out_parent);
AL_SHIM_EXPORT void al_shim_node_previous_sibling(const void *node, void *out_sibling);
AL_SHIM_EXPORT void al_shim_node_next_sibling(const void *node, void *out_sibling);

AL_SHIM_EXPORT uint32_t al_shim_node_is_null(const void *node);
AL_SHIM_EXPORT uint32_t al_shim_node_is_named(const void *node);
AL_SHIM_EXPORT uint32_t al_shim_node_eq(const void *a, const void *b);
AL_SHIM_EXPORT uint32_t al_shim_node_has_error(const void *node);

/* Tree cursor */
AL_SHIM_EXPORT void *al_shim_cursor_new(const void *node);
AL_SHIM_EXPORT void  al_shim_cursor_delete(void *cursor);
AL_SHIM_EXPORT uint32_t al_shim_cursor_goto_first_child(void *cursor);
AL_SHIM_EXPORT uint32_t al_shim_cursor_goto_next_sibling(void *cursor);
AL_SHIM_EXPORT uint32_t al_shim_cursor_goto_parent(void *cursor);
AL_SHIM_EXPORT void al_shim_cursor_current_node(void *cursor, void *out_node);
AL_SHIM_EXPORT const char *al_shim_cursor_current_field_name(void *cursor);

/* Diagnostic version getters */
AL_SHIM_EXPORT uint32_t al_shim_tree_sitter_language_version(void);
AL_SHIM_EXPORT uint32_t al_shim_tree_sitter_min_compatible_language_version(void);

#ifdef __cplusplus
}
#endif
#endif /* AL_SHIM_H */
