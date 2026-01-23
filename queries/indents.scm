; indents.scm for AL (Application Language) - Microsoft Dynamics 365 Business Central
; Defines automatic indentation rules for editors
;
; This enables smart indentation when:
; - Pressing Enter after certain keywords
; - Inside braces, brackets, or begin...end blocks
; - After control flow keywords (if, for, while, etc.)

; ============================================================================
; INDENT INCREASE (nodes that increase indentation for children)
; ============================================================================

; Object declarations - indent contents
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
] @indent

; Procedures and triggers - indent body
[
  (procedure)
  (preproc_conditional_procedure)
  (preproc_split_procedure)
  (interface_procedure)
  (controladdin_procedure)
  (trigger_declaration)
  (named_trigger)
  (onrun_trigger)
  (field_trigger_declaration)
] @indent

; Code blocks (begin...end) - indent contents
(code_block) @indent

; Var sections - indent variable declarations
(var_section) @indent

; Control flow - indent body
[
  (if_statement)
  (case_statement)
  (case_branch)
  (case_else_branch)
  (for_statement)
  (while_statement)
  (repeat_statement)
  (foreach_statement)
  (with_statement)
] @indent

; Table sections - indent contents
[
  (fields)
  (keys)
  (fieldgroups_section)
  (field_declaration)
  (key_declaration)
  (fieldgroup_declaration)
] @indent

; Page sections - indent contents
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
] @indent

; Report sections - indent contents
[
  (dataset_section)
  (report_dataitem_section)
  (report_column_section)
  (requestpage_section)
  (rendering_section)
  (labels_section)
] @indent

; XMLport sections - indent contents
[
  (xmlport_schema_element)
  (xmlport_table_element)
  (xmlport_field_attribute)
  (xmlport_text_attribute)
] @indent

; Query sections - indent contents
[
  (elements_section)
  (dataitem_section)
  (column_section)
  (filter_section)
] @indent

; DotNet sections - indent contents
[
  (assembly_declaration)
  (type_declaration)
] @indent

; Enum values with properties - indent contents
(enum_value_declaration) @indent

; Modification sections (extensions) - indent contents
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
] @indent

; Attribute items - indent arguments
(attribute_item) @indent

; Argument lists and parameter lists - indent contents
[
  (argument_list)
  (parameter_list)
] @indent

; List literals - indent contents
(list_literal) @indent

; ============================================================================
; INDENT END (nodes/tokens that signal end of indented block)
; ============================================================================

; Closing braces reduce indentation
"}" @indent_end

; 'end' keyword is part of code_block structure, not a separate queryable node
; Dedenting is handled by "}" and structure-based rules

; ============================================================================
; BRANCH POINTS (same indent level as parent, like 'else')
; ============================================================================

; 'else' keyword is part of if_statement structure, not a separate queryable node
; Branch alignment is handled by else_branch field structure
; (if_statement "else" @branch)

; 'else' in case statements
(case_else_branch) @branch

; 'until' keyword is part of repeat_statement structure, not a separate node
; (repeat_statement "until" @branch)

; ============================================================================
; DEDENT (explicit dedent markers)
; ============================================================================

; Closing brace always dedents
"}" @dedent

; 'end' keyword is part of code_block structure, not a separate queryable node
; (code_block "end" @dedent)

; ============================================================================
; ALIGNED NODES (nodes that should align with siblings)
; ============================================================================

; Case branches should align with each other
(case_branch) @align

; Parameters in a list should align
(parameter) @align

; Arguments in a list should align  
(argument_list (_) @align)

; Variable declarations in var section should align
(var_section (variable_declaration) @align)

; Field declarations should align
(fields (field_declaration) @align)

; ============================================================================
; SPECIAL INDENT RULES
; ============================================================================

; Opening brace starts indent
"{" @indent

; Closing brace ends indent
"}" @outdent

; 'begin' starts indent (captured via code_block)
; 'end' ends indent (captured via code_block)

; Preprocessor directives should not affect indentation
[
  (preproc_if)
  (preproc_else)
  (preproc_elif)
  (preproc_endif)
  (preproc_region)
  (preproc_endregion)
  (pragma)
] @ignore

; ============================================================================
; ZERO INDENT (nodes that should have no indentation)
; ============================================================================

; Top-level declarations should not be indented
(source_file (_) @zero_indent)

; Namespace and using at root level
(namespace_declaration) @zero_indent
(using_statement) @zero_indent
