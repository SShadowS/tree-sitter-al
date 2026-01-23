; folds.scm for AL (Application Language) - Microsoft Dynamics 365 Business Central
; Defines code folding regions for editors
;
; This enables collapsing/expanding:
; - Object declarations
; - Procedures and triggers
; - Code blocks (begin...end)
; - Control flow structures
; - Sections (fields, keys, layout, actions, etc.)

; ============================================================================
; OBJECT DECLARATIONS
; ============================================================================

; All object types can be folded
(table_declaration) @fold
(tableextension_declaration) @fold
(page_declaration) @fold
(pageextension_declaration) @fold
(pagecustomization_declaration) @fold
(codeunit_declaration) @fold
(report_declaration) @fold
(reportextension_declaration) @fold
(query_declaration) @fold
(xmlport_declaration) @fold
(enum_declaration) @fold
(enumextension_declaration) @fold
(interface_declaration) @fold
(permissionset_declaration) @fold
(permissionsetextension_declaration) @fold
(profile_declaration) @fold
(profileextension_declaration) @fold
(dotnet_declaration) @fold
(controladdin_declaration) @fold
(entitlement_declaration) @fold

; ============================================================================
; PROCEDURES AND TRIGGERS
; ============================================================================

; Procedures
(procedure) @fold
(preproc_conditional_procedure) @fold
(preproc_split_procedure) @fold
(preproc_procedure_body_split) @fold
(interface_procedure) @fold
(controladdin_procedure) @fold

; Triggers
(trigger_declaration) @fold
(named_trigger) @fold
(onrun_trigger) @fold
(field_trigger_declaration) @fold

; ============================================================================
; CODE BLOCKS
; ============================================================================

; Begin...end blocks
(code_block) @fold

; ============================================================================
; CONTROL FLOW STRUCTURES
; ============================================================================

; If statements (fold the entire if including else)
(if_statement) @fold

; Case statements
(case_statement) @fold
(case_branch) @fold
(case_else_branch) @fold

; Loops
(for_statement) @fold
(while_statement) @fold
(repeat_statement) @fold
(foreach_statement) @fold

; With statement
(with_statement) @fold

; ============================================================================
; TABLE SECTIONS
; ============================================================================

; Fields section
(fields) @fold

; Individual field declarations with properties
(field_declaration) @fold

; Keys section
(keys) @fold

; Individual key declarations
(key_declaration) @fold

; Field groups section
(fieldgroups_section) @fold

; Individual fieldgroup declarations
(fieldgroup_declaration) @fold

; ============================================================================
; PAGE SECTIONS
; ============================================================================

; Layout section
(layout_section) @fold

; Area sections (content, factboxes, etc.)
(area_section) @fold

; Group sections
(group_section) @fold

; Repeater sections
(repeater_section) @fold

; Grid sections
(grid_section) @fold

; Fixed sections
(fixed_section) @fold

; Cuegroup sections
(cuegroup_section) @fold

; Part sections
(part_section) @fold

; Systempart sections
(systempart_section) @fold

; Usercontrol sections
(usercontrol_section) @fold

; Field sections (page fields)
(field_section) @fold

; Actions section
(actions_section) @fold

; Action declarations
(action_declaration) @fold

; Action groups
(action_group_section) @fold

; Views section
(views_section) @fold

; View definitions
(view_definition) @fold

; ============================================================================
; REPORT SECTIONS
; ============================================================================

; Dataset section
(dataset_section) @fold

; Dataitem sections
(report_dataitem_section) @fold

; Column sections
(report_column_section) @fold

; Request page section
(requestpage_section) @fold

; Rendering section
(rendering_section) @fold

; Labels section
(labels_section) @fold

; ============================================================================
; XMLPORT SECTIONS
; ============================================================================

; Schema element
(xmlport_schema_element) @fold

; Table elements
(xmlport_table_element) @fold

; Field/text attributes
(xmlport_field_attribute) @fold
(xmlport_text_attribute) @fold

; ============================================================================
; QUERY SECTIONS
; ============================================================================

; Elements section
(elements_section) @fold

; Dataitem sections (query)
(dataitem_section) @fold

; Column sections (query)
(column_section) @fold

; Filter sections
(filter_section) @fold

; ============================================================================
; DOTNET SECTIONS
; ============================================================================

; Assembly declarations
(assembly_declaration) @fold

; Type declarations
(type_declaration) @fold

; ============================================================================
; VAR SECTIONS
; ============================================================================

; Variable sections
(var_section) @fold

; ============================================================================
; ENUM VALUES
; ============================================================================

; Enum value declarations with properties
(enum_value_declaration) @fold

; ============================================================================
; PREPROCESSOR BLOCKS
; ============================================================================

; Preprocessor conditional blocks can be folded
(preproc_conditional_procedures) @fold
(preproc_conditional_var_sections) @fold
(preproc_conditional_mixed_content) @fold
(preproc_conditional_statements) @fold
(preproc_conditional_fields) @fold
(preproc_conditional_actions) @fold
(preproc_conditional_layout) @fold
(preproc_conditional_properties) @fold

; ============================================================================
; COMMENTS
; ============================================================================

; Multi-line comments can be folded
(multiline_comment) @fold

; ============================================================================
; ATTRIBUTES
; ============================================================================

; Attribute items (when they have multiple lines)
(attribute_item) @fold

; ============================================================================
; MODIFICATION SECTIONS (Extensions)
; ============================================================================

; Layout modifications
(addfirst_layout_modification) @fold
(addlast_layout_modification) @fold
(addafter_layout_modification) @fold
(addbefore_layout_modification) @fold
(movefirst_layout_modification) @fold
(movelast_layout_modification) @fold
(moveafter_layout_modification) @fold
(movebefore_layout_modification) @fold

; Field modifications
(modify_field_declaration) @fold

; Action modifications
(modify_action) @fold
