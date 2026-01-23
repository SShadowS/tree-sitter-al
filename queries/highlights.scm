; highlights.scm for AL (Application Language) - Microsoft Dynamics 365 Business Central
; Tree-sitter syntax highlighting queries

; ============================================================================
; COMMENTS
; ============================================================================

(comment) @comment
(multiline_comment) @comment

; ============================================================================
; LITERALS
; ============================================================================

; Strings
(string_literal) @string
(duration_string) @string.special

; Numbers
(integer) @number
(decimal) @number.float
(biginteger) @number

; Date/Time literals
(date_literal) @number
(time_literal) @number
(datetime_literal) @number

; Booleans
(boolean) @boolean

; ============================================================================
; OPERATORS
; ============================================================================

; Assignment operators (matched in assignment statements)
; Note: These are part of the hidden _assignment_operator rule, so we capture them indirectly
(assignment_statement
  operator: _ @operator)

(assignment_expression
  operator: _ @operator)

; Comparison operators
(comparison_operator) @operator

; Arithmetic operators
[
  "+"
  "-"
  "*"
  "/"
] @operator

; Range operator
".." @operator

; Double colon (enum/qualified access)
"::" @punctuation.delimiter

; Ternary operator
"?" @operator

; Keyword operators (logical and arithmetic)
; Note: These are handled case-insensitively in AL
[
  "and"
  "AND"
  "And"
  "or"
  "OR"
  "Or"
  "xor"
  "XOR"
  "Xor"
  "not"
  "NOT"
  "Not"
  "div"
  "DIV"
  "Div"
  "mod"
  "MOD"
  "Mod"
] @keyword.operator

; 'in' operator
(in_operator) @keyword.operator

; ============================================================================
; PUNCTUATION
; ============================================================================

; Brackets
[
  "("
  ")"
  "["
  "]"
  "{"
  "}"
] @punctuation.bracket

; Delimiters
[
  ";"
  ","
  "."
  ":"
] @punctuation.delimiter

; ============================================================================
; KEYWORDS - Object Declarations
; ============================================================================

; Object declaration keywords (match the keyword token)
(table_declaration) @keyword
(tableextension_declaration) @keyword
(page_declaration) @keyword
(pageextension_declaration) @keyword
(pagecustomization_declaration) @keyword
(codeunit_declaration) @keyword
(report_declaration) @keyword
(reportextension_declaration) @keyword
(query_declaration) @keyword
(xmlport_declaration) @keyword
(enum_declaration) @keyword
(enumextension_declaration) @keyword
(interface_declaration) @keyword
(permissionset_declaration) @keyword
(permissionsetextension_declaration) @keyword
(profile_declaration) @keyword
(profileextension_declaration) @keyword
(dotnet_declaration) @keyword
(controladdin_declaration) @keyword
(entitlement_declaration) @keyword

; Extension keywords
(implements_clause) @keyword

; ============================================================================
; KEYWORDS - Sections and Structure
; ============================================================================

; Table sections
(fields) @keyword
(keys) @keyword
(fieldgroups_section) @keyword
(field_declaration) @keyword
(key_declaration) @keyword
(fieldgroup_declaration) @keyword

; Page sections
(layout_section) @keyword
(actions_section) @keyword
(views_section) @keyword
(area_section) @keyword
(group_section) @keyword
(repeater_section) @keyword
(grid_section) @keyword
(fixed_section) @keyword
(cuegroup_section) @keyword
(part_section) @keyword
(systempart_section) @keyword
(usercontrol_section) @keyword
(field_section) @keyword

; Action declarations
(action_declaration) @keyword
(separator_action) @keyword
(actionref_declaration) @keyword
(systemaction_declaration) @keyword
(fileuploadaction_declaration) @keyword
(customaction_declaration) @keyword

; Report sections
(dataset_section) @keyword
(requestpage_section) @keyword
(rendering_section) @keyword
(labels_section) @keyword
(report_dataitem_section) @keyword
(report_column_section) @keyword

; XMLport sections
(xmlport_schema_element) @keyword
(xmlport_table_element) @keyword
(xmlport_field_attribute) @keyword
(xmlport_text_attribute) @keyword

; Query sections
(elements_section) @keyword
(dataitem_section) @keyword
(column_section) @keyword
(filter_section) @keyword

; DotNet sections
(assembly_declaration) @keyword
(type_declaration) @keyword

; Var section
(var_section) @keyword

; View definition
(view_definition) @keyword

; ============================================================================
; KEYWORDS - Control Flow
; ============================================================================

; If statement
(if_statement) @keyword.control

; Case statement
(case_statement) @keyword.control
(case_branch) @keyword.control
(case_else_branch) @keyword.control

; For statement
(for_statement) @keyword.control
(to) @keyword.control
(downto) @keyword.control

; While statement
(while_statement) @keyword.control

; Repeat statement
(repeat_statement) @keyword.control

; Foreach statement
(foreach_statement) @keyword.control

; With statement
(with_statement) @keyword.control

; Exit statement
(exit_statement) @keyword.control

; Code block (begin/end)
(code_block) @keyword

; ============================================================================
; KEYWORDS - Other
; ============================================================================

; Namespace and using
(namespace_declaration) @keyword
(using_statement) @keyword

; Assert error
(asserterror_statement) @keyword

; Event keyword in control add-ins
(controladdin_event) @keyword

; Temporary keyword
(temporary) @keyword

; ============================================================================
; FUNCTIONS AND PROCEDURES
; ============================================================================

; Procedure definitions - procedure name
(procedure
  name: (name
    (identifier) @function))

(procedure_header
  name: (name
    (identifier) @function))

(preproc_conditional_procedure
  name: (name
    (identifier) @function))

(preproc_procedure_body_split
  name: (name
    (identifier) @function))

(controladdin_procedure
  name: (identifier) @function)

(interface_procedure
  name: (identifier) @function)

; Procedure modifiers
(procedure_modifier) @keyword.modifier

; Function calls
(call_expression
  function: (identifier) @function.call)

(call_expression
  function: (member_expression
    property: (identifier) @function.call))

(call_expression
  function: (field_access
    field: (_) @function.call))

; ============================================================================
; TRIGGERS
; ============================================================================

; Generic trigger declaration
(trigger_declaration
  name: (trigger_name
    (identifier) @function))

; Named triggers (OnInsert, OnModify, OnDelete, etc.)
(named_trigger) @function

; OnRun trigger
(onrun_trigger) @function

; Field triggers
(field_trigger_declaration
  type: (trigger_type) @function)

; ============================================================================
; TYPES
; ============================================================================

; Type specifications
(type_specification) @type

; Basic/built-in types
(basic_type) @type.builtin

; Specific type constructs
(text_type) @type.builtin
(code_type) @type.builtin
(record_type) @type.builtin
(codeunit_type) @type.builtin
(page_type) @type.builtin
(report_type) @type.builtin
(query_type) @type.builtin
(xmlport_type) @type.builtin
(enum_type) @type.builtin
(interface_type) @type.builtin
(list_type) @type.builtin
(dictionary_type) @type.builtin
(array_type) @type.builtin
(option_type) @type.builtin
(dotnet_type) @type.builtin
(testpage_type) @type.builtin
(testrequestpage_type) @type.builtin
(controladdin_type) @type.builtin

; Record type with table reference
(record_type
  reference: (_) @type)

; ============================================================================
; VARIABLES AND IDENTIFIERS
; ============================================================================

; Variable declarations
; Note: Variable names in declarations are captured through identifier rules below
; (variable_declaration name: field causes "Impossible pattern" error in tree-sitter 0.26.3)

; Parameter declarations
(parameter
  parameter_name: (name
    (identifier) @variable.parameter))

; Return value name
(return_value
  return_value: (identifier) @variable)

; Field declarations - field name
(field_declaration
  name: (_) @variable.member)

; Key declarations - key name
(key_declaration
  name: (name) @variable.member)

; Object identifiers (names in declarations)
(table_declaration
  object_name: (_) @type.definition)

(tableextension_declaration
  object_name: (_) @type.definition)
(tableextension_declaration
  base_object: (_) @type)

(page_declaration
  object_name: (_) @type.definition)

(pageextension_declaration
  object_name: (_) @type.definition)
(pageextension_declaration
  base_object: (_) @type)

(pagecustomization_declaration
  object_name: (_) @type.definition)
(pagecustomization_declaration
  target_page: (_) @type)

(codeunit_declaration
  object_name: (_) @type.definition)

(report_declaration
  object_name: (_) @type.definition)

(reportextension_declaration
  object_name: (_) @type.definition)
(reportextension_declaration
  base_object: (_) @type)

(query_declaration
  object_name: (_) @type.definition)

(xmlport_declaration
  object_name: (_) @type.definition)

(enum_declaration
  object_name: (_) @type.definition)

(enumextension_declaration
  object_name: (_) @type.definition)
(enumextension_declaration
  base_object: (_) @type)

(interface_declaration
  object_name: (_) @type.definition)

(permissionset_declaration
  object_name: (_) @type.definition)

(permissionsetextension_declaration
  object_name: (_) @type.definition)
(permissionsetextension_declaration
  extends_target: (_) @type)

(profile_declaration
  object_name: (_) @type.definition)

(profileextension_declaration
  object_name: (_) @type.definition)
(profileextension_declaration
  base_object: (_) @type)

(controladdin_declaration
  object_name: (_) @type.definition)

(entitlement_declaration
  object_name: (_) @type.definition)

; DotNet declarations don't have object_name field
; (dotnet_declaration
;   object_name: (_) @type.definition)

; Identifiers (general fallback)
(identifier) @variable

; Quoted identifiers
(quoted_identifier) @variable

; Member access - object and member
(member_expression
  object: (identifier) @variable)
(member_expression
  property: (identifier) @variable.member)

; Field access - the record and field being accessed
(field_access
  record: (identifier) @variable)
(field_access
  field: (_) @variable.member)

; ============================================================================
; ATTRIBUTES
; ============================================================================

; Attribute items [...]
(attribute_item
  "[" @punctuation.bracket
  "]" @punctuation.bracket)

; Attribute content - the attribute name
(attribute_content
  name: (identifier) @attribute)

; Legacy attribute support (DISABLED - not used in actual parse trees)
; The grammar has migrated to attribute_item + attribute_content structure
; (attribute
;   attribute_name: (identifier) @attribute)

; ============================================================================
; PREPROCESSOR DIRECTIVES
; ============================================================================

; #if, #else, #elif, #endif
(preproc_if) @keyword.directive
(preproc_else) @keyword.directive
(preproc_elif) @keyword.directive
(preproc_endif) @keyword.directive

; #region, #endregion
(preproc_region) @keyword.directive
(preproc_endregion) @keyword.directive

; #pragma
(pragma) @keyword.directive

; Preprocessor condition identifier
(preproc_if
  condition: (identifier) @constant)

(preproc_elif
  condition: (identifier) @constant)

; Preprocessor NOT expression
(preproc_not_expression) @keyword.directive

; ============================================================================
; NAMESPACES
; ============================================================================

; Namespace name
(namespace_declaration
  name: (namespace_name) @namespace)

; Using statement namespace
(using_statement
  namespace: (namespace_name) @namespace)

; Namespace qualified references
(namespace_qualified_reference) @namespace

; ============================================================================
; CONSTANTS AND ENUM VALUES
; ============================================================================

; Enum value declarations
(enum_value_declaration
  value_name: (_) @constant)

; Qualified enum values (Type::Value)
(qualified_enum_value
  value: (_) @constant)

; Enum keyword qualified values (Enum::"Type"::Value)
(enum_keyword_qualified_value
  value: (_) @constant)

; Database references (DATABASE::"Table")
(database_reference) @type.builtin

; Object type qualified references (Report::"Name", Page::"Name", etc.)
(object_type_qualified_reference) @type

; ============================================================================
; PROPERTIES
; ============================================================================

; Property declarations - highlight property values
(caption_property
  (string_literal) @string)

(caption_ml_property) @property

(description_property
  value: (string_literal) @string)

(application_area_property
  value: (_) @constant)

(tool_tip_property
  (tool_tip_value) @string)

(tool_tip_ml_property) @property

(source_table_property
  value: (_) @type)

(page_type_property) @property

(table_type_property) @property

(data_classification_property) @property
(data_classification_value) @constant

; Run object properties
(run_object_property) @property

; Image property
(image_property) @property

; Promoted properties
(promoted_property) @property
(promoted_category_property) @property

; Table relation
(table_relation_property) @property

; CalcFormula
(calc_formula_property) @property

; Access properties
(access_property) @property
; Note: access_value is aliased as (value) in parse tree, captured by generic value rules

; Extensible property
(extensible_property) @property

; Obsolete properties
(obsolete_state_property) @property
(obsolete_reason_property) @property
(obsolete_tag_property) @property

; Permission properties
(inherent_permissions_property) @property
(inherent_entitlements_property) @property
(permission_type) @constant

; Generic property node is a choice type, not a container with name field
; Individual property types are captured by their specific rules above
; (property
;   name: (_) @property)

; ============================================================================
; LABELS
; ============================================================================

; Label declarations
(label_declaration
  name: (_) @label)

; Label attributes
(label_attribute
  name: (_) @property)

; ============================================================================
; FORMULA KEYWORDS (CalcFormula)
; ============================================================================

(lookup_formula) @function.builtin
(count_formula) @function.builtin
(sum_formula) @function.builtin
(average_formula) @function.builtin
(min_formula) @function.builtin
(max_formula) @function.builtin
(exist_formula) @function.builtin

; WHERE clause in formulas
(where_clause) @keyword

; CONST and FIELD in filter conditions
(const_filter) @function.builtin
(field_filter) @function.builtin
(filter_expression_function) @function.builtin

; ============================================================================
; SPECIAL CONSTRUCTS
; ============================================================================

; List literals
(list_literal
  "[" @punctuation.bracket
  "]" @punctuation.bracket)

; Object header - object ID
(table_declaration
  object_id: (integer) @number)

(page_declaration
  object_id: (integer) @number)

(codeunit_declaration
  object_id: (integer) @number)

(report_declaration
  object_id: (integer) @number)

(query_declaration
  object_id: (integer) @number)

(xmlport_declaration
  object_id: (integer) @number)

(enum_declaration
  object_id: (integer) @number)

(permissionset_declaration
  object_id: (integer) @number)

; Permission set permissions
(permissionset_permissions) @keyword

; ============================================================================
; SUBSCRIPT/ARRAY ACCESS
; ============================================================================

; Array/list indexing
(subscript_expression
  "[" @punctuation.bracket
  "]" @punctuation.bracket)

; ============================================================================
; EXPRESSIONS
; ============================================================================

; Unary operators
(unary_expression
  operator: (_) @operator)

; Range expressions
(range_expression
  operator: ".." @operator)

; Conditional (ternary) expression
(conditional_expression
  "?" @operator
  ":" @operator)

; ============================================================================
; IMPLEMENTS CLAUSE
; ============================================================================

; Interface in implements clause
(implements_clause
  interface: (_) @type)

; ============================================================================
; MODIFICATIONS (Page/Table Extensions)
; ============================================================================

; Modification targets
(modify_field_declaration) @keyword
(modify_action) @keyword

; Modification methods
(addfirst_layout_modification) @keyword
(addlast_layout_modification) @keyword
(addafter_layout_modification) @keyword
(addbefore_layout_modification) @keyword
(movefirst_layout_modification) @keyword
(movelast_layout_modification) @keyword
(moveafter_layout_modification) @keyword
(movebefore_layout_modification) @keyword

; ============================================================================
; ERROR HANDLING
; ============================================================================

; Error sentinel (from external scanner)
(error_sentinel) @error
