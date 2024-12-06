; Keywords
[
  "table"
  "TABLE"
  "Table"
  "codeunit"
  "CODEUNIT"
  "Codeunit"
  "procedure"
  "PROCEDURE"
  "Procedure"
  "begin"
  "BEGIN"
  "Begin"
  "end"
  "END"
  "End"
  "if"
  "IF"
  "If"
  "then"
  "THEN"
  "Then"
  "else"
  "ELSE"
  "Else"
  "case"
  "CASE"
  "Case"
  "repeat"
  "REPEAT"
  "Repeat"
  "until"
  "UNTIL"
  "Until"
  "var"
  "VAR"
  "Var"
  "temporary"
  "TEMPORARY"
  "Temporary"
  "trigger"
  "TRIGGER"
  "Trigger"
  "local"
  "LOCAL"
  "Local"
] @keyword

; Built-in types
[
  "Integer"
  "INTEGER"
  "Text"
  "TEXT"
  "Decimal"
  "DECIMAL"
  "Boolean"
  "BOOLEAN"
  "Option"
  "OPTION"
  "Code"
  "CODE"
  "Date"
  "DATE"
  "Time"
  "TIME"
  "DateTime"
  "DATETIME"
  "Blob"
  "BLOB"
  "Guid"
  "GUID"
  "RecordId"
  "RECORDID"
] @type.builtin

; Operators
[
  ":="
  "="
  "<"
  ">"
  "<="
  ">="
  "<>"
  "+"
  "-"
  "*"
  "/"
  "::"
] @operator

; Built-in functions
(built_in_function) @function.builtin

; Function definitions
(procedure name: (identifier) @function)

; Function calls
(procedure_call function_name: (identifier) @function.call)
(method_call method: (identifier) @function.method)

; Variables and parameters
(parameter parameter_name: (identifier) @variable.parameter)
(variable_declaration name: (identifier) @variable)

; Properties
(property_name) @property

; Field declarations
(field_declaration name: (_) @field)

; Object declarations
(table_declaration 
  object_name: (name) @type)
(codeunit_declaration 
  object_name: (name) @type)

; Numbers
(integer) @number

; Strings
(string_literal) @string

; Comments (if your grammar supports them)
(comment) @comment

; Boolean literals
(boolean) @constant.builtin

; Punctuation
["(" ")" "{" "}" "[" "]" ";" ","] @punctuation.delimiter

; Object IDs
(object_id) @number

; Triggers
(field_trigger_declaration type: (trigger_type) @keyword.control)
