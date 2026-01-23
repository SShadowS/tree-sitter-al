; locals.scm for AL (Application Language) - Microsoft Dynamics 365 Business Central
; Defines scopes and references for scope-aware highlighting
;
; This enables:
; - Distinguishing local vs global variables
; - Highlighting references to the same variable
; - "Go to definition" within the same file
; - Understanding variable shadowing

; ============================================================================
; SCOPE DEFINITIONS
; ============================================================================

; Object declarations create a scope
(table_declaration) @local.scope
(tableextension_declaration) @local.scope
(page_declaration) @local.scope
(pageextension_declaration) @local.scope
(pagecustomization_declaration) @local.scope
(codeunit_declaration) @local.scope
(report_declaration) @local.scope
(reportextension_declaration) @local.scope
(query_declaration) @local.scope
(xmlport_declaration) @local.scope
(enum_declaration) @local.scope
(enumextension_declaration) @local.scope
(interface_declaration) @local.scope
(permissionset_declaration) @local.scope
(permissionsetextension_declaration) @local.scope
(profile_declaration) @local.scope
(profileextension_declaration) @local.scope
(controladdin_declaration) @local.scope
(entitlement_declaration) @local.scope

; Procedures create a new scope
(procedure) @local.scope
(procedure_header) @local.scope
(preproc_conditional_procedure) @local.scope
(preproc_split_procedure) @local.scope
(preproc_procedure_body_split) @local.scope
(interface_procedure) @local.scope
(controladdin_procedure) @local.scope

; Triggers create a new scope
(trigger_declaration) @local.scope
(named_trigger) @local.scope
(onrun_trigger) @local.scope
(field_trigger_declaration) @local.scope

; Code blocks create a scope (begin...end)
(code_block) @local.scope

; Control flow structures create scopes
(if_statement) @local.scope
(case_statement) @local.scope
(case_branch) @local.scope
(case_else_branch) @local.scope
(for_statement) @local.scope
(while_statement) @local.scope
(repeat_statement) @local.scope
(foreach_statement) @local.scope
(with_statement) @local.scope

; ============================================================================
; DEFINITION SITES
; ============================================================================

; Variable declarations define variables
(variable_declaration
  (identifier) @local.definition)

; Parameters define variables in procedure scope
(parameter
  parameter_name: (name
    (identifier) @local.definition))

; Return value defines a variable
(return_value
  return_value: (identifier) @local.definition)

; For loop variable is a definition
(for_statement
  variable: (identifier) @local.definition)

; Foreach loop variable is a definition
(foreach_statement
  variable: (identifier) @local.definition)
(foreach_statement
  variable: (quoted_identifier) @local.definition)

; Field declarations define field names (in table scope)
(field_declaration
  name: (identifier) @local.definition)
(field_declaration
  name: (quoted_identifier) @local.definition)

; Key declarations define key names
(key_declaration
  name: (name) @local.definition)

; Enum value declarations define enum values
(enum_value_declaration
  value_name: (identifier) @local.definition)
(enum_value_declaration
  value_name: (quoted_identifier) @local.definition)

; Procedure names are definitions
(procedure
  name: (name
    (identifier) @local.definition))

(procedure
  name: (name
    (quoted_identifier) @local.definition))

; Trigger names are definitions  
(trigger_declaration
  name: (trigger_name
    (identifier) @local.definition))

; ============================================================================
; REFERENCE SITES
; ============================================================================

; Identifiers used in expressions are references
(identifier) @local.reference

; Quoted identifiers used in expressions are references
(quoted_identifier) @local.reference

; Member expression - the object is a reference
(member_expression
  object: (identifier) @local.reference)

; Field access - the record is a reference
(field_access
  record: (identifier) @local.reference)

; Assignment left-hand side is a reference
(assignment_statement
  left: (identifier) @local.reference)

(assignment_expression
  left: (identifier) @local.reference)

; Function calls - function name is a reference
(call_expression
  function: (identifier) @local.reference)

; Subscript expression - the array/list is a reference
(subscript_expression
  array: (identifier) @local.reference)
