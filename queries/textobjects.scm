; AL Language (v2) - Tree-sitter Textobject Queries
; Powers editor "select inside / around" commands (Helix, nvim-treesitter).
;
; Every scoped AL construct exposes its content via a `body` field whose value is
; a single node (object_body, fields_body, action_body, code_block, ...). That
; lets `@*.inside` capture the content as ONE node, with `@*.around` capturing the
; whole construct. See docs/superpowers/specs/2026-06-17-body-field-textobjects-design.md
; and GitHub issue #19.
;
; Note: the `body` field is absent for an empty construct (`{ }` / `begin end`),
; so an empty body simply yields no `.inside` match — the correct behaviour.

; =============================================================================
; Objects / types  ->  class.inside / class.around
; =============================================================================

[
  (table_declaration)
  (tableextension_declaration)
  (page_declaration)
  (pageextension_declaration)
  (pagecustomization_declaration)
  (codeunit_declaration)
  (report_declaration)
  (reportextension_declaration)
  (query_declaration)
  (xmlport_declaration)
  (enum_declaration)
  (enumextension_declaration)
  (interface_declaration)
  (controladdin_declaration)
  (dotnet_declaration)
  (permissionset_declaration)
  (permissionsetextension_declaration)
] @class.around

(table_declaration body: (_) @class.inside)
(tableextension_declaration body: (_) @class.inside)
(page_declaration body: (_) @class.inside)
(pageextension_declaration body: (_) @class.inside)
(pagecustomization_declaration body: (_) @class.inside)
(codeunit_declaration body: (_) @class.inside)
(report_declaration body: (_) @class.inside)
(reportextension_declaration body: (_) @class.inside)
(query_declaration body: (_) @class.inside)
(xmlport_declaration body: (_) @class.inside)
(enum_declaration body: (_) @class.inside)
(enumextension_declaration body: (_) @class.inside)
(interface_declaration body: (_) @class.inside)
(controladdin_declaration body: (_) @class.inside)
(dotnet_declaration body: (_) @class.inside)
(permissionset_declaration body: (_) @class.inside)
(permissionsetextension_declaration body: (_) @class.inside)

; =============================================================================
; Procedures / triggers  ->  function.inside / function.around
; (code blocks keep begin/end inside the body node, Rust `block` model)
; =============================================================================

(procedure) @function.around
(trigger_declaration) @function.around
(interface_procedure) @function.around

(procedure body: (code_block) @function.inside)
(trigger_declaration body: (code_block) @function.inside)

; Parameters
(parameter_list) @parameter.inside

; =============================================================================
; Sections, fields, actions  ->  generic body capture
; A single rule covers every construct that exposes a `body` field, so any new
; body-bearing construct works without editing this query.
; =============================================================================

(_ body: (_) @block.inside) @block.around

; =============================================================================
; Comments
; =============================================================================

(comment) @comment.inside
(multiline_comment) @comment.inside

[
  (comment)
  (multiline_comment)
] @comment.around
