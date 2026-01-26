; indents.scm for AL (Application Language) - Microsoft Dynamics 365 Business Central
; Defines automatic indentation rules for Neovim 0.10+
;
; This file uses modern Tree-sitter indent query captures:
;   @indent.begin  - Start indenting child nodes
;   @indent.end    - Stop indenting at this token
;   @indent.branch - Align with parent (like 'else' with 'if')
;   @indent.dedent - Reduce indentation level
;   @indent.ignore - Skip indentation processing
;
; Refactored: 2026-01-23
; - Updated all captures to @indent.* namespace (Neovim 0.10+)
; - Removed conflicting token-level rules
; - Simplified structure (182 lines vs 247 lines)
; - Fixed else/end handling based on actual parse tree structure

; ============================================================================
; STRUCTURAL INDENTATION - Object & Section Declarations
; ============================================================================

; Top-level AL object declarations - indent everything inside the braces
; Note: No indent.immediate - object spans multiple lines with { on next line
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
  (permissionset_declaration)
  (permissionsetextension_declaration)
  (profile_declaration)
  (profileextension_declaration)
  (dotnet_declaration)
  (controladdin_declaration)
  (entitlement_declaration)
] @indent.begin

; Table structure sections
[
  (fields)
  (keys)
  (fieldgroups_section)
  (field_declaration)
  (key_declaration)
  (fieldgroup_declaration)
] @indent.begin

; Page structure sections
[
  (layout_section)
  (actions_section)
  (views_section)
  (area_section)
  (group_section)
  (repeater_section)
  (grid_section)
  (fixed_section)
  (cuegroup_section)
  (part_section)
  (systempart_section)
  (usercontrol_section)
  (field_section)
  (action_declaration)
  (action_group_section)
  (view_definition)
] @indent.begin

; Report structure sections
[
  (dataset_section)
  (report_dataitem_section)
  (report_column_section)
  (requestpage_section)
  (rendering_section)
  (labels_section)
] @indent.begin

; XMLport structure sections
[
  (xmlport_schema_element)
  (xmlport_table_element)
  (xmlport_field_attribute)
  (xmlport_text_attribute)
] @indent.begin

; Query structure sections
[
  (elements_section)
  (dataitem_section)
  (column_section)
  (filter_section)
] @indent.begin

; DotNet assembly sections
[
  (assembly_declaration)
  (type_declaration)
] @indent.begin

; Extension modification sections
[
  (addfirst_layout_modification)
  (addlast_layout_modification)
  (addafter_layout_modification)
  (addbefore_layout_modification)
  (movefirst_layout_modification)
  (movelast_layout_modification)
  (moveafter_layout_modification)
  (movebefore_layout_modification)
  (modify_field_declaration)
  (modify_action)
] @indent.begin

; ============================================================================
; CODE FLOW INDENTATION - Procedures, Triggers, Control Flow
; ============================================================================

; Code blocks (begin...end) - these handle indentation for procedure bodies
; Note: We don't indent on procedure/trigger nodes themselves because they
; contain code_block children which do the actual indenting
((code_block) @indent.begin
  (#set! indent.immediate 1))

; Control flow statements
((if_statement) @indent.begin
  (#set! indent.immediate 1))
((case_statement) @indent.begin
  (#set! indent.immediate 1))
((for_statement) @indent.begin
  (#set! indent.immediate 1))
((while_statement) @indent.begin
  (#set! indent.immediate 1))
((repeat_statement) @indent.begin
  (#set! indent.immediate 1))
((foreach_statement) @indent.begin
  (#set! indent.immediate 1))
((with_statement) @indent.begin
  (#set! indent.immediate 1))

; Case branches (each branch indents its body)
(case_branch) @indent.begin

; Variable declarations section
(var_section) @indent.begin

; ============================================================================
; BLOCK TERMINATORS - End indented blocks
; ============================================================================

; The 'end' keyword (block_end node) should align with 'begin'/'case'
; Use @indent.branch so it reduces indent on the same line the node starts
; (not subsequent lines like @indent.dedent would do)
(block_end) @indent.branch

; The 'until' keyword in repeat statements should align with 'repeat'
(until_keyword) @indent.branch

; Opening and closing braces align with the declaration line
[
  "{"
  "}"
] @indent.branch

; 'else' branches should align with the 'if' keyword
; In the parse tree, else_branch is a field of if_statement
(if_statement
  else_branch: (_) @indent.branch)

; 'else' in case statements aligns with case branches
(case_else_branch) @indent.branch

; Note: 'until' in repeat_statement is part of the structure,
; no special handling needed as it naturally aligns

; ============================================================================
; SPECIAL INDENTATION - Attributes, Lists, Properties
; ============================================================================

; Enum values with property blocks
(enum_value_declaration) @indent.begin

; Attributes (can span multiple lines with arguments)
(attribute_item) @indent.begin

; Multi-line argument and parameter lists
[
  (argument_list)
  (parameter_list)
] @indent.begin

; List literals
(list_literal) @indent.begin

; ============================================================================
; BLOCK TERMINATORS - End indented blocks
; ============================================================================

; ============================================================================
; IGNORED PATTERNS - No indentation effect
; ============================================================================

; Preprocessor directives don't affect indentation
; (Advanced preprocessor-aware indentation deferred to future enhancement)
[
  (preproc_if)
  (preproc_else)
  (preproc_elif)
  (preproc_endif)
  (preproc_region)
  (preproc_endregion)
  (pragma)
] @indent.ignore

; ============================================================================
; NOTES
; ============================================================================
;
; This query file is designed for Neovim 0.10+ with native Tree-sitter
; indentation support. It should be used with:
;
;   vim.bo.indentexpr = "v:lua.vim.treesitter.get_indent()"
;
; Key design decisions:
; 1. Structural nodes (not tokens) drive indentation
; 2. No token-level @indent.begin on "{" (conflicts with structural rules)
; 3. Removed @indent.align patterns (formatter's responsibility)
; 4. Removed @indent.zero on source_file children (blocks proper indentation)
; 5. Preprocessor support is basic (marked @indent.ignore)
;
; Future enhancements:
; - Advanced preprocessor handling (split procedures, conditional properties)
; - Fine-tuned case branch alignment
; - Multi-line expression handling (CalcFormula, DataItemLink)
; - Custom alignment with #set! directives for specific patterns
