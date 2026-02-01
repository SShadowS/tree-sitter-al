; AL Language - Tree-sitter Syntax Highlighting Queries
; See: https://tree-sitter.github.io/tree-sitter/syntax-highlighting

; =============================================================================
; Comments
; =============================================================================

(comment) @comment.line
(multiline_comment) @comment.block

; =============================================================================
; Preprocessor Directives
; =============================================================================

[
  (preproc_if)
  (preproc_else)
  (preproc_elif)
  (preproc_endif)
  (pragma)
  (preproc_region)
  (preproc_endregion)
] @keyword.directive

; =============================================================================
; Keywords (via named nodes)
; =============================================================================

; Control flow keywords
(to) @keyword.control
(downto) @keyword.control

; =============================================================================
; Punctuation (anonymous nodes)
; =============================================================================

";" @punctuation.delimiter
":" @punctuation.delimiter
"," @punctuation.delimiter

"(" @punctuation.bracket
")" @punctuation.bracket
"[" @punctuation.bracket
"]" @punctuation.bracket
"{" @punctuation.bracket
"}" @punctuation.bracket

".." @operator

; =============================================================================
; Types
; =============================================================================

(basic_type) @type.builtin

(record_type
  reference: [(identifier) (quoted_identifier)] @type)

(codeunit_type
  reference: [(identifier) (quoted_identifier) (integer)] @type)

(enum_type_reference
  enum_type: [(identifier) (quoted_identifier)] @type)

(qualified_interface_reference) @type

; =============================================================================
; Literals
; =============================================================================

(string_literal) @string
(integer) @number
(decimal) @number.float
(biginteger) @number
(boolean) @constant.builtin
(date_literal) @string.special
(time_literal) @string.special
(datetime_literal) @string.special

; =============================================================================
; Object Declarations
; =============================================================================

(table_declaration
  object_name: [(identifier) (quoted_identifier)] @type.definition)
(table_declaration
  object_id: (integer) @constant)

(page_declaration
  object_name: [(identifier) (quoted_identifier)] @type.definition)
(page_declaration
  object_id: (integer) @constant)

(codeunit_declaration
  object_name: [(identifier) (quoted_identifier)] @type.definition)
(codeunit_declaration
  object_id: (integer) @constant)

(report_declaration
  object_name: [(identifier) (quoted_identifier)] @type.definition)
(report_declaration
  object_id: (integer) @constant)

(query_declaration
  object_name: [(identifier) (quoted_identifier)] @type.definition)
(query_declaration
  object_id: (integer) @constant)

(xmlport_declaration
  object_name: [(identifier) (quoted_identifier)] @type.definition)
(xmlport_declaration
  object_id: (integer) @constant)

(enum_declaration
  object_name: [(identifier) (quoted_identifier)] @type.definition)
(enum_declaration
  object_id: (integer) @constant)

(interface_declaration
  object_name: [(identifier) (quoted_identifier)] @type.definition)

; =============================================================================
; Procedures and Triggers
; =============================================================================

(procedure
  name: (name) @function.definition)

(trigger_declaration
  name: (trigger_name) @function.definition)

; =============================================================================
; Fields and Variables
; =============================================================================

(field_declaration
  id: (integer) @constant)
(field_declaration
  name: [(identifier) (quoted_identifier)] @property.definition)

(variable_declaration
  name: [(identifier) (quoted_identifier)] @variable.definition)

(parameter
  parameter_name: (name) @variable.parameter)

(label_declaration
  name: (identifier) @constant.definition)

; =============================================================================
; Expressions
; =============================================================================

(call_expression
  function: (identifier) @function.call)

(call_expression
  function: (member_expression
    property: (identifier) @function.method.call))

(member_expression
  object: (identifier) @variable)

(member_expression
  property: (identifier) @property)

(field_access
  field: (quoted_identifier) @property)

(database_reference
  table_name: [(identifier) (quoted_identifier)] @type)

(qualified_enum_value
  value: [(identifier) (quoted_identifier)] @constant)

; =============================================================================
; Attributes
; =============================================================================

(attribute_item) @attribute

(attribute_content
  name: (identifier) @attribute)

; =============================================================================
; Errors
; =============================================================================

(ERROR) @error
