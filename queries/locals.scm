; AL Language - Tree-sitter Scope and Local Variable Tracking
; See: https://tree-sitter.github.io/tree-sitter/syntax-highlighting#local-variables

; =============================================================================
; Scope Definitions
; =============================================================================

; Object declarations create scopes
(table_declaration) @local.scope
(tableextension_declaration) @local.scope
(page_declaration) @local.scope
(pageextension_declaration) @local.scope
(codeunit_declaration) @local.scope
(report_declaration) @local.scope
(reportextension_declaration) @local.scope
(query_declaration) @local.scope
(xmlport_declaration) @local.scope
(enum_declaration) @local.scope
(enumextension_declaration) @local.scope
(interface_declaration) @local.scope
(controladdin_declaration) @local.scope
(profile_declaration) @local.scope
(permissionset_declaration) @local.scope
(entitlement_declaration) @local.scope
(pagecustomization_declaration) @local.scope

; Procedures create scopes
(procedure) @local.scope

; Triggers create scopes
(trigger_declaration) @local.scope
(onrun_trigger) @local.scope
(field_trigger_declaration) @local.scope

; Code blocks create scopes
(code_block) @local.scope

; =============================================================================
; Local Definitions
; =============================================================================

; Variable declarations define local variables
(variable_declaration
  name: (identifier) @local.definition)
(variable_declaration
  name: (quoted_identifier) @local.definition)

; Parameters define local variables
(parameter
  parameter_name: (name
    (identifier) @local.definition))

; Label declarations
(label_declaration
  name: (identifier) @local.definition)

; Field declarations (in tables)
(field_declaration
  name: [(identifier) (quoted_identifier)] @local.definition)

; Enum value declarations
(enum_value_declaration
  value_name: [(identifier) (quoted_identifier)] @local.definition)

; Key declarations
(key_declaration
  name: (name
    (identifier) @local.definition))

; For loop variables
(for_statement
  variable: (identifier) @local.definition)

; Foreach loop variables
(foreach_statement
  element: (identifier) @local.definition)

; =============================================================================
; References
; =============================================================================

; Identifiers are references
(identifier) @local.reference

; Quoted identifiers are references
(quoted_identifier) @local.reference
