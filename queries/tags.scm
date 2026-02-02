; AL Language - Tree-sitter Tags for Code Navigation
; See: https://tree-sitter.github.io/tree-sitter/4-code-navigation.html

; =============================================================================
; Object Definitions (tables, pages, codeunits, etc.)
; =============================================================================

; Table definitions
(table_declaration
  object_name: [(identifier) (quoted_identifier)] @name) @definition.class

; Page definitions
(page_declaration
  object_name: [(identifier) (quoted_identifier)] @name) @definition.class

; Codeunit definitions
(codeunit_declaration
  object_name: [(identifier) (quoted_identifier)] @name) @definition.class

; Report definitions
(report_declaration
  object_name: [(identifier) (quoted_identifier)] @name) @definition.class

; Query definitions
(query_declaration
  object_name: [(identifier) (quoted_identifier)] @name) @definition.class

; XMLport definitions
(xmlport_declaration
  object_name: [(identifier) (quoted_identifier)] @name) @definition.class

; Enum definitions
(enum_declaration
  object_name: [(identifier) (quoted_identifier)] @name) @definition.class

; Interface definitions
(interface_declaration
  object_name: [(identifier) (quoted_identifier)] @name) @definition.interface

; ControlAddIn definitions
(controladdin_declaration
  object_name: [(identifier) (quoted_identifier)] @name) @definition.class

; =============================================================================
; Extension Definitions
; =============================================================================

; Table extensions
(tableextension_declaration
  object_name: [(identifier) (quoted_identifier)] @name) @definition.class

; Page extensions
(pageextension_declaration
  object_name: [(identifier) (quoted_identifier)] @name) @definition.class

; Enum extensions
(enumextension_declaration
  object_name: [(identifier) (quoted_identifier)] @name) @definition.class

; Report extensions
(reportextension_declaration
  object_name: [(identifier) (quoted_identifier)] @name) @definition.class

; Profile extensions
(profileextension_declaration
  object_name: [(identifier) (quoted_identifier)] @name) @definition.class

; Permission set extensions
(permissionsetextension_declaration
  object_name: [(identifier) (quoted_identifier)] @name) @definition.class

; =============================================================================
; Other Object Types
; =============================================================================

; Profile definitions
(profile_declaration
  object_name: [(identifier) (quoted_identifier)] @name) @definition.class

; Permission set definitions
(permissionset_declaration
  object_name: [(identifier) (quoted_identifier)] @name) @definition.class

; Entitlement definitions
(entitlement_declaration
  object_name: [(identifier) (quoted_identifier)] @name) @definition.class

; Page customization definitions
(pagecustomization_declaration
  object_name: [(identifier) (quoted_identifier)] @name) @definition.class

; =============================================================================
; Procedure and Trigger Definitions
; =============================================================================

; Procedure definitions (methods)
(procedure
  name: (name) @name) @definition.method

; Trigger declarations (user-defined triggers)
(trigger_declaration
  name: (trigger_name) @name) @definition.method

; =============================================================================
; Parameter Definitions
; =============================================================================

; Function parameters
(parameter
  parameter_name: (name
    (identifier) @name)) @definition.parameter

(parameter
  parameter_name: (name
    (quoted_identifier) @name)) @definition.parameter

; =============================================================================
; Field Definitions
; =============================================================================

; Table field definitions
(field_declaration
  name: [(identifier) (quoted_identifier)] @name) @definition.field

; Enum value definitions
(enum_value_declaration
  value_name: [(identifier) (quoted_identifier)] @name) @definition.constant

; Key definitions
(key_declaration
  name: (name) @name) @definition.field

; Fieldgroup definitions
(fieldgroup_declaration
  group_type: (identifier) @name) @definition.field

; =============================================================================
; Variable and Label Definitions
; =============================================================================

; Variable declarations
(variable_declaration
  name: (identifier) @name) @definition.variable

(variable_declaration
  name: (quoted_identifier) @name) @definition.variable

; Label declarations
(label_declaration
  name: (identifier) @name) @definition.constant

; =============================================================================
; Action Definitions (page actions)
; =============================================================================

; Action declarations
(action_declaration
  name: [(identifier) (quoted_identifier)] @name) @definition.function

; Custom action declarations
(customaction_declaration
  name: [(identifier) (quoted_identifier)] @name) @definition.function

; System action declarations
(systemaction_declaration
  name: [(identifier) (quoted_identifier)] @name) @definition.function

; File upload action declarations
(fileuploadaction_declaration
  name: [(identifier) (quoted_identifier)] @name) @definition.function

; =============================================================================
; Module/Namespace Definitions
; =============================================================================

; Namespace declarations
(namespace_declaration
  name: (namespace_name) @name) @definition.module

; =============================================================================
; Function/Method References
; =============================================================================

; Direct function calls
(call_expression
  function: (identifier) @name) @reference.call

; Method calls on objects (e.g., Rec.Insert())
(call_expression
  function: (member_expression
    property: (identifier) @name)) @reference.call

; Method calls via field access (e.g., Rec."Field Name"())
(call_expression
  function: (field_access
    field: (quoted_identifier) @name)) @reference.call

; =============================================================================
; Type References
; =============================================================================

; Record type references
(record_type
  reference: [(identifier) (quoted_identifier)] @name) @reference.type

; Codeunit type references
(codeunit_type
  reference: [(identifier) (quoted_identifier) (integer)] @name) @reference.type

; Enum type in type specifications
(enum_type_reference
  enum_type: [(identifier) (quoted_identifier)] @name) @reference.type

; Database references (Database::"Table Name")
(database_reference
  table_name: [(identifier) (quoted_identifier)] @name) @reference.class

; =============================================================================
; Interface Implementation References
; =============================================================================

; Implements clause references
(implements_clause
  interface: [(identifier) (quoted_identifier)] @name) @reference.implementation

; Qualified interface references
(qualified_interface_reference) @reference.type

; =============================================================================
; Enum Value References
; =============================================================================

; Qualified enum values (Enum::Value)
(qualified_enum_value
  enum_type: [(identifier) (quoted_identifier)] @name) @reference.class

(qualified_enum_value
  value: [(identifier) (quoted_identifier)] @name) @reference.constant
