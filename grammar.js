/**
 * @file AL for Business Central (V2)
 * @author Torben Leth <sshadows@sshadows.dk>
 * @license MIT
 */

/// <reference types="tree-sitter-cli/dsl" />
// @ts-check

// Case-insensitive keyword via regex
function kw(word, precedence = null) {
  const regex = new RustRegex(`(?i)${word}`);
  return precedence !== null ? token(prec(precedence, regex)) : token(regex);
}

// Object declaration helper — with object ID
function _object_with_id(keyword_name) {
  return $ => seq(
    $[keyword_name + '_keyword'],
    field('object_id', $.integer),
    field('object_name', $._identifier_or_quoted),
    '{',
    repeat($._body_element),
    '}'
  );
}

// Object declaration helper — without object ID
function _object_without_id(keyword_name) {
  return $ => seq(
    $[keyword_name + '_keyword'],
    field('object_name', $._identifier_or_quoted),
    '{',
    repeat($._body_element),
    '}'
  );
}

// Extension declaration helper — with object ID
function _extension_with_id(keyword_name) {
  return $ => seq(
    $[keyword_name + '_keyword'],
    field('object_id', $.integer),
    field('object_name', $._identifier_or_quoted),
    $.extends_keyword,
    field('base_object', $._identifier_or_quoted),
    '{',
    repeat($._body_element),
    '}'
  );
}

// Extension declaration helper — without object ID
function _extension_without_id(keyword_name) {
  return $ => seq(
    $[keyword_name + '_keyword'],
    field('object_name', $._identifier_or_quoted),
    $.extends_keyword,
    field('base_object', $._identifier_or_quoted),
    '{',
    repeat($._body_element),
    '}'
  );
}

// Section template: keyword(name) { content* }
function _named_section(keyword_rule, content_rule) {
  return $ => seq(
    keyword_rule,
    '(',
    field('name', $._identifier_or_quoted),
    ')',
    '{',
    repeat(content_rule($)),
    '}'
  );
}

module.exports = grammar({
  name: "al",

  word: $ => $.identifier,

  extras: $ => [
    /\s/,
    $.comment,
    $.multiline_comment,
    $.pragma,
    $.preproc_region,
    $.preproc_endregion,
    /\uFEFF/,  // BOM
  ],

  externals: $ => [
    $.property_name,            // [0] identifier followed by = (not :=)
    $.continue_as_identifier,   // [1] 'continue' followed by ':=' (used as variable)
    $.preproc_open,             // [2] #if — depth++
    $.preproc_close,            // [3] #endif — depth--
    $.begin_keyword,            // [4] 'begin' at depth 0
    $.end_keyword,              // [5] 'end' at depth 0
    $.preproc_split_begin,      // [6] 'begin' at depth > 0, immediately before #endif
  ],

  conflicts: $ => [
    [$._property_value, $.option_member],
    [$._property_value, $.option_member, $._identifier_or_quoted],
    [$.caption_value, $.option_member],
    [$.assignment_statement, $.assignment_expression],
    [$.preproc_conditional, $.preproc_conditional_layout],
    [$.preproc_conditional, $.preproc_conditional_actions],
    [$._expression, $._identifier_or_quoted],
    [$._body_element, $.preproc_conditional_var],
    [$.filter_value, $._literal_value],
    [$.filter_value, $._expression],
    [$._body_element, $._action_element],
    [$._body_element, $._layout_element],
    [$.modify_modification, $.modify_action_modification],
    [$._signed_integer, $.option_member],
    [$.option_member, $._literal_value],
    [$._body_element, $._procedure_header],
    [$._body_element, $._action_element, $._procedure_header],
    [$._field_source, $._field_header],
    [$._property_value, $.option_member, $._namespaced_or_simple_ref],
    [$.addafter_modification, $.addafter_views_modification],
    [$.addbefore_modification, $.addbefore_views_modification],
    [$._report_body_element, $.preproc_conditional],
    [$._query_body_element, $.preproc_conditional],
    [$.preproc_conditional_report, $.preproc_conditional],
    [$.preproc_conditional_query, $.preproc_conditional],
    [$._xmlport_body_element, $.preproc_conditional],
    [$.preproc_conditional_xmlport, $.preproc_conditional],
    [$._body_element, $._procedure_header, $.preproc_conditional_var],
    [$._body_element],
    [$.calc_field_reference, $._expression],
    [$.option_member, $._identifier_or_quoted],
    [$._single_pattern, $._expression],
    [$.preproc_conditional_link_values, $.preproc_conditional_permissions, $.preproc_conditional_impl_values, $.preproc_conditional_table_relation],
    [$.preproc_conditional_permissions, $.preproc_conditional_table_relation],
    [$.preproc_conditional_link_values, $.preproc_conditional_permissions, $.preproc_conditional_impl_values],
    [$.preproc_conditional_link_values, $.preproc_conditional_impl_values],
    [$.preproc_conditional_controladdin, $.preproc_conditional],
    [$.procedure, $.interface_procedure_suffix],
    [$.procedure, $._procedure_header, $.interface_procedure_suffix],
    [$._procedure_header, $.interface_procedure_suffix],
    [$.preproc_conditional_case, $.preproc_split_case_branch, $.preproc_conditional_case_patterns],
    [$.case_branch, $.preproc_split_case_branch, $.preproc_conditional_case_patterns],
    [$._preproc_guard_block, $._statement],
  ],

  rules: {
    source_file: $ => seq(
      optional($.namespace_declaration),
      repeat(choice(
        $.using_statement,
        $._object,
        $.preproc_conditional_object,
      )),
    ),

    // Preprocessor conditional wrapping entire objects or using statements
    preproc_conditional_object: $ => seq(
      $.preproc_if,
      optional($.namespace_declaration),
      repeat(choice($.using_statement, $._object, $.preproc_conditional_object)),
      repeat(seq(
        $.preproc_elif,
        optional($.namespace_declaration),
        repeat(choice($.using_statement, $._object, $.preproc_conditional_object)),
      )),
      optional(seq(
        $.preproc_else,
        optional($.namespace_declaration),
        repeat(choice($.using_statement, $._object, $.preproc_conditional_object)),
      )),
      $.preproc_endif,
    ),

    // --- Namespace / Using ---

    namespace_declaration: $ => seq(
      $.namespace_keyword,
      field('name', $.namespace_name),
      ';'
    ),

    using_statement: $ => seq(
      $.using_keyword,
      field('namespace', $.namespace_name),
      ';'
    ),

    namespace_name: $ => prec.right(seq(
      $.identifier,
      repeat(seq('.', $.identifier))
    )),

    // --- Object types ---

    _object: $ => choice(
      $.table_declaration,
      $.tableextension_declaration,
      $.page_declaration,
      $.pageextension_declaration,
      $.pagecustomization_declaration,
      $.codeunit_declaration,
      $.report_declaration,
      $.reportextension_declaration,
      $.query_declaration,
      $.xmlport_declaration,
      $.enum_declaration,
      $.enumextension_declaration,
      $.interface_declaration,
      $.controladdin_declaration,
      $.dotnet_declaration,
      $.profile_declaration,
      $.profileextension_declaration,
      $.permissionset_declaration,
      $.permissionsetextension_declaration,
      $.entitlement_declaration,
      $.preproc_split_declaration,
    ),

    // Preprocessor-split object declaration:
    // #if ... codeunit 1 "Name" implements A #else codeunit 1 "Name" implements B #endif { body }
    // Also handles nested: #if A header1 #else #if B header2 #else header3 #endif #endif { body }
    preproc_split_declaration: $ => prec(25, seq(
      $.preproc_if,
      $._object_header,
      repeat(seq($.preproc_elif, $._object_header)),
      optional(seq($.preproc_else, choice(
        $._object_header,
        // Nested: #else #if ... #endif
        seq(
          $.preproc_if,
          $._object_header,
          repeat(seq($.preproc_elif, $._object_header)),
          optional(seq($.preproc_else, $._object_header)),
          $.preproc_endif,
        ),
      ))),
      $.preproc_endif,
      '{',
      repeat($._body_element),
      '}'
    )),

    // Object header without body (used in preproc split declarations)
    _object_header: $ => choice(
      seq($.codeunit_keyword, field('object_id', $.integer), field('object_name', $._identifier_or_quoted), optional($.implements_clause)),
      seq($.enum_keyword, field('object_id', $.integer), field('object_name', $._identifier_or_quoted), optional($.implements_clause)),
      seq(choice($.table_keyword, $.page_keyword, $.report_keyword, $.query_keyword, $.xmlport_keyword, $.permissionset_keyword),
        field('object_id', $.integer), field('object_name', $._identifier_or_quoted)),
      seq(choice($.tableextension_keyword, $.pageextension_keyword, $.reportextension_keyword, $.enumextension_keyword, $.permissionsetextension_keyword),
        field('object_id', $.integer), field('object_name', $._identifier_or_quoted), $.extends_keyword, field('base_object', $._identifier_or_quoted)),
      seq($.interface_keyword, field('object_name', $._identifier_or_quoted)),
    ),

    // --- With ID, no extends ---

    table_declaration: _object_with_id('table'),
    page_declaration: _object_with_id('page'),
    report_declaration: _object_with_id('report'),
    query_declaration: _object_with_id('query'),
    xmlport_declaration: _object_with_id('xmlport'),
    permissionset_declaration: _object_with_id('permissionset'),

    // --- With ID + optional implements ---

    codeunit_declaration: $ => seq(
      $.codeunit_keyword,
      field('object_id', $.integer),
      field('object_name', $._identifier_or_quoted),
      optional($.implements_clause),
      '{',
      repeat($._body_element),
      '}'
    ),

    enum_declaration: $ => seq(
      $.enum_keyword,
      field('object_id', $.integer),
      field('object_name', $._identifier_or_quoted),
      optional($.implements_clause),
      '{',
      repeat($._body_element),
      '}'
    ),

    // --- With ID + extends ---

    tableextension_declaration: _extension_with_id('tableextension'),
    pageextension_declaration: _extension_with_id('pageextension'),
    reportextension_declaration: _extension_with_id('reportextension'),
    enumextension_declaration: _extension_with_id('enumextension'),
    permissionsetextension_declaration: _extension_with_id('permissionsetextension'),

    // --- Without ID ---

    controladdin_declaration: $ => seq(
      $.controladdin_keyword,
      field('object_name', $._identifier_or_quoted),
      '{',
      repeat(choice($._body_element, $.interface_procedure, $.preproc_conditional_controladdin)),
      '}'
    ),

    // Preprocessor conditional inside controladdin bodies (needs interface_procedure support)
    preproc_conditional_controladdin: $ => seq(
      $.preproc_if,
      repeat(choice($._body_element, $.interface_procedure, $.preproc_conditional_controladdin)),
      repeat(seq(
        $.preproc_elif,
        repeat(choice($._body_element, $.interface_procedure, $.preproc_conditional_controladdin)),
      )),
      optional(seq(
        $.preproc_else,
        repeat(choice($._body_element, $.interface_procedure, $.preproc_conditional_controladdin)),
      )),
      $.preproc_endif,
    ),
    profile_declaration: _object_without_id('profile'),
    entitlement_declaration: _object_without_id('entitlement'),

    // --- Without ID + extends ---

    profileextension_declaration: _extension_without_id('profileextension'),

    // --- Interface (without ID, optional extends) ---

    interface_declaration: $ => seq(
      $.interface_keyword,
      field('object_name', $._identifier_or_quoted),
      optional(seq(
        $.extends_keyword,
        field('extends_interface', $._identifier_or_quoted)
      )),
      optional(seq(
        kw('access'),
        '=',
        field('access_value', choice(
          $.internal_keyword,
          kw('public'),
          $.identifier
        ))
      )),
      '{',
      repeat(choice($._body_element, $.interface_procedure)),
      '}'
    ),

    // --- Pagecustomization (without ID, uses customizes) ---

    pagecustomization_declaration: $ => seq(
      $.pagecustomization_keyword,
      field('object_name', $._identifier_or_quoted),
      $.customizes_keyword,
      field('target_page', $._identifier_or_quoted),
      '{',
      repeat($._body_element),
      '}'
    ),

    // --- Dotnet (no ID, no name) ---

    dotnet_declaration: $ => seq(
      $.dotnet_keyword,
      '{',
      repeat($.assembly_declaration),
      '}'
    ),

    // --- Implements clause ---

    implements_clause: $ => seq(
      $.implements_keyword,
      field('interface', $._identifier_or_quoted),
      repeat(seq(',', field('interface', $._identifier_or_quoted)))
    ),

    // =====================================================================
    // Body elements — all sections/declarations that can appear in object bodies
    // =====================================================================

    _body_element: $ => choice(
      $.property,
      $.empty_statement,
      // Table internals
      $.fields_section,
      $.keys_section,
      $.fieldgroups_section,
      // Enum values
      $.enum_value_declaration,
      // Labels
      $.labels_section,
      // Page layout & actions
      $.layout_section,
      $.actions_section,
      $.views_section,
      // Report sections
      $.dataset_section,
      $.requestpage_section,
      $.rendering_section,
      // Query sections
      $.elements_section,
      // XMLport sections
      $.schema_section,
      // DotNet internals
      $.assembly_declaration,
      // Code structure
      $.procedure,
      $.trigger_declaration,
      $.var_section,
      $.attribute_item,
      // ControlAddIn event declarations
      $.event_declaration,
      // Preprocessor-split procedure: header variants in #if/#else, shared body
      $.preproc_split_procedure,
      // Preprocessor conditionals
      $.preproc_conditional,
      // Extension modifications (table/page extensions)
      $.modify_modification,
    ),

    empty_statement: $ => ';',

    // =====================================================================
    // Properties
    // =====================================================================

    // --- Generic property: Name = Value ; ---
    // The scanner's PROPERTY_NAME token disambiguates from variables (Name : Type)
    // All properties share this structure; complex value types are part of _property_value.
    property: $ => seq(
      field('name', $.property_name),   // Scanner token: identifier followed by =
      '=',
      optional(field('value', $._property_value)),
      ';'
    ),

    _property_value: $ => choice(
      // Simple values
      $.boolean,
      $.integer,
      $.decimal,
      $.string_literal,
      $.identifier,
      $.quoted_identifier,
      // Complex value types
      $.caption_value,              // 'Text', Locked = true, Comment = '...'
      $.ml_value_list,              // ENU='English', DEU='German'
      $._calc_formula_expression,   // sum("Table".Field where(...))
      $.tabledata_permission_list,  // tabledata X = R, tabledata Y = RIMD
      $.order_by_list,              // ascending("No.", Name)
      $.implementation_value_list,  // "IFace" = "Impl", ...
      $.option_member_list,         // Option1, Option2, "Option 3"
      $.table_relation_value,       // Customer where(...) or if(...) Item else Resource
      $.sorting_value,              // sorting("Starting Date")
      $.link_value_list,            // "Field" = field(Other), ...
      $.property_expression,        // Expressions used as property values
      $.keyword_identifier,         // Keywords used as simple property values (TestIsolation = Codeunit)
      $.where_clause,               // SourceTableView/SubPageView = where(...)
      $.object_reference_value,     // RunObject = Codeunit "BOM-Explode BOM"
      $.decimal_range_value,        // DecimalPlaces = 0 : 5
      $.signed_integer_list,        // OptionOrdinalValues = -1, 0, 1
      $.time_literal,               // InitValue = 000000T
      $.date_literal,               // InitValue = 0D
      $.datetime_literal,           // InitValue = 0DT
    ),

    // Decimal range: N : M (used by DecimalPlaces property)
    decimal_range_value: $ => prec(5, seq(
      field('min', $.integer),
      ':',
      optional(field('max', $.integer))
    )),

    // Signed integer list: -1, 0, 1, 2 (used by OptionOrdinalValues)
    signed_integer_list: $ => prec.left(5, seq(
      $._signed_integer,
      repeat1(seq(',', $._signed_integer))
    )),

    _signed_integer: $ => choice(
      $.integer,
      seq('-', $.integer),
    ),

    // Object reference as property value: Codeunit "BOM-Explode BOM"
    // Also supports namespace: Page Microsoft.Sales."Sales Order"
    object_reference_value: $ => prec(3, seq(
      choice(
        $.codeunit_keyword,
        $.page_keyword,
        $.report_keyword,
        $.query_keyword,
        $.xmlport_keyword,
        $.table_keyword,
      ),
      $._namespaced_or_simple_ref,
    )),

    // Expressions that can appear as property values (member access, function calls, etc.)
    property_expression: $ => prec(-2, choice(
      $.call_expression,
      $.member_expression,
      $.qualified_enum_value,
      $.database_reference,
      $.unary_expression,
      $.additive_expression,
      $.multiplicative_expression,
      $.comparison_expression,
      $.logical_expression,
      $.parenthesized_expression,
      $.subscript_expression,
    )),

    boolean: $ => choice(kw('true'), kw('false')),

    decimal: $ => token(seq(/\d+/, '.', /\d+/)),

    // --- Caption value with sub-fields (Locked, Comment, MaxLength) ---
    // 'My Caption', Locked = true, Comment = 'text', MaxLength = 100
    // Also handles trailing comma: Caption = 'text',;
    // Uses property_name (scanner token) since the sub-fields follow Name = Value pattern
    caption_value: $ => prec.right(seq(
      $.string_literal,
      choice(
        seq(
          repeat1(seq(
            ',',
            $.property_name,
            '=',
            choice($.boolean, $.string_literal, $.integer),
          )),
          optional(','),  // Trailing comma after sub-fields
        ),
        ',',  // Trailing comma only (no sub-fields): Caption = 'text',;
      ),
    )),

    // --- ML (Multilingual) value list ---
    // ENU='English', DEU='German'
    ml_value_list: $ => prec.right(seq(
      $.ml_value_pair,
      repeat(seq(',', $.ml_value_pair)),
      optional(seq(',', kw('locked'), '=', $.boolean))
    )),

    ml_value_pair: $ => seq(
      field('language', $._identifier_or_quoted),
      '=',
      field('value', $.string_literal)
    ),

    // --- CalcFormula values ---
    // sum("Ledger Entry".Amount where("No." = field("No.")))
    _calc_formula_expression: $ => choice(
      $.lookup_formula,
      $.aggregate_formula,
      seq('-', $.aggregate_formula),  // Negated formulas
    ),

    lookup_formula: $ => seq(
      kw('lookup'),
      '(',
      field('target', $.calc_field_reference),
      optional($.where_clause),
      ')'
    ),

    aggregate_formula: $ => prec(15, seq(
      field('function', alias($.identifier, $.aggregate_function)),
      '(',
      field('target', $.calc_field_reference),
      optional($.where_clause),
      ')'
    )),

    // Table.Field or "Table"."Field" or Namespace.Table."Field" reference used in CalcFormula
    calc_field_reference: $ => prec.left(seq(
      choice($._identifier_or_quoted, $.keyword_identifier),
      repeat(seq('.', choice($._identifier_or_quoted, $.keyword_identifier)))
    )),

    // WHERE(conditions) clause — shared by CalcFormula, TableRelation, etc.
    where_clause: $ => seq(
      kw('where', 15),
      '(',
      $.where_conditions,
      ')'
    ),

    where_conditions: $ => repeat1(choice(
      seq($.where_condition, optional(',')),
      $.preproc_conditional_where,
    )),

    preproc_conditional_where: $ => seq(
      $.preproc_if,
      repeat(seq($.where_condition, optional(','))),
      repeat(seq(
        $.preproc_elif,
        repeat(seq($.where_condition, optional(','))),
      )),
      optional(seq(
        $.preproc_else,
        repeat(seq($.where_condition, optional(','))),
      )),
      $.preproc_endif,
    ),

    where_condition: $ => seq(
      field('field', $._identifier_or_quoted),
      '=',
      choice(
        // field("No.") or field(upperlimit("Date Filter")) or field(filter(Totaling))
        seq(
          choice(kw('field'), kw('upperlimit')),
          '(',
          choice(
            field('value', $._identifier_or_quoted),
            // field(filter(...)) — field with filter applied
            seq($.filter_keyword, '(', field('value', $._identifier_or_quoted), ')'),
            // field(upperlimit(...)) — field with upperlimit
            seq(kw('upperlimit'), '(', choice(
              field('value', $._identifier_or_quoted),
              // upperlimit(filter(...)) — upperlimit with filter
              seq($.filter_keyword, '(', field('value', $._identifier_or_quoted), ')'),
            ), ')'),
          ),
          ')'
        ),
        // const(value) — also accepts keyword identifiers like Report, Page, Codeunit, Action
        seq(kw('const'), '(', optional(field('value', choice(
          $.string_literal, $.identifier, $.quoted_identifier, $.integer, $.boolean,
          $.database_reference, $.qualified_enum_value, $.keyword_identifier,
        ))), ')'),
        // filter(expression)
        seq($.filter_keyword, '(', field('value', $.filter_value), ')'),
      )
    ),

    // Filter values — simplified, allows comparison operators, ranges, etc.
    filter_value: $ => repeat1(choice(
      $.string_literal,
      $.identifier,
      $.quoted_identifier,
      $.integer,
      $.decimal,
      $.boolean,               // true/false in filters
      $.date_literal,          // 0D, 20200101D
      $.time_literal,          // 0T, 120000T
      $.datetime_literal,      // 0DT
      $.biginteger_literal,    // 1000L
      $.qualified_enum_value,  // Enum::Value references
      $.database_reference,    // Report::"Name", Page::"Name", etc.
      $.keyword_identifier,    // Keywords used as filter values (Page, Codeunit, etc.)
      '..',  // Range operator
      seq('-', $.integer),     // Negative integer: -1, -100
      '-',   // Negation sign (standalone)
      token(prec(-1, /[<>=|&@*%]+/)),  // Filter operators like <>, |, =, >, etc.
    )),

    // --- Sorting/SourceTableView value ---
    // sorting("Starting Date") order(ascending) where("Status" = const(Active))
    sorting_value: $ => prec(5, seq(
      kw('sorting'),
      '(',
      $._identifier_or_quoted,
      repeat(seq(',', $._identifier_or_quoted)),
      ')',
      optional(seq(
        kw('order'),
        '(',
        choice(kw('ascending'), kw('descending')),
        ')',
      )),
      optional($.where_clause),
    )),

    // --- Link value list ---
    // "Field" = field(OtherField), "Field2" = const(Value)
    // Used by SubPageLink, SubPageView, DataItemLink, etc.
    link_value_list: $ => prec.left(6, repeat1(choice(
      seq($.link_value, optional(',')),
      $.preproc_conditional_link_values,
    ))),

    preproc_conditional_link_values: $ => seq(
      $.preproc_if,
      repeat(seq($.link_value, optional(','))),
      repeat(seq(
        $.preproc_elif,
        repeat(seq($.link_value, optional(','))),
      )),
      optional(seq(
        $.preproc_else,
        repeat(seq($.link_value, optional(','))),
      )),
      $.preproc_endif,
    ),

    link_value: $ => seq(
      field('field', $._identifier_or_quoted),
      '=',
      choice(
        seq(
          choice(kw('field'), kw('upperlimit')),
          '(',
          choice(
            field('value', $._identifier_or_quoted),
            seq($.filter_keyword, '(', field('value', $._identifier_or_quoted), ')'),
            seq(kw('upperlimit'), '(', choice(
              field('value', $._identifier_or_quoted),
              seq($.filter_keyword, '(', field('value', $._identifier_or_quoted), ')'),
            ), ')'),
          ),
          ')'
        ),
        seq(kw('const'), '(', optional(field('value', choice(
          $.string_literal, $.identifier, $.quoted_identifier, $.integer, $.boolean,
          $.database_reference, $.qualified_enum_value, $.keyword_identifier,
        ))), ')'),
        seq($.filter_keyword, '(', field('value', $.filter_value), ')'),
        // Direct reference: DataItem.FieldName (used in query DataItemLink)
        field('value', prec(3, seq(
          $._identifier_or_quoted,
          '.', $._identifier_or_quoted
        ))),
      )
    ),

    // --- TableRelation value ---
    // Customer where("No." = field("Customer No."))
    // if("Type" = const(Item)) Item else Resource
    table_relation_value: $ => prec.right(5, choice(
      $.table_relation_expression,
      $.preproc_conditional_table_relation,
    )),

    // Preprocessor conditionals inside TableRelation value
    preproc_conditional_table_relation: $ => seq(
      $.preproc_if,
      optional(seq($.table_relation_expression, optional(';'))),
      repeat(seq(
        $.preproc_elif,
        optional(seq($.table_relation_expression, optional(';'))),
      )),
      optional(seq(
        $.preproc_else,
        optional(seq($.table_relation_expression, optional(';'))),
      )),
      $.preproc_endif,
    ),

    table_relation_expression: $ => choice(
      $.simple_table_relation,
      $.if_table_relation,
      $.preproc_conditional_table_relation,
    ),

    if_table_relation: $ => prec.right(15, seq(
      kw('if'),
      '(',
      $.where_conditions,
      ')',
      field('then_relation', $.simple_table_relation),
      optional(seq(
        kw('else'),
        field('else_relation', $.table_relation_expression)
      ))
    )),

    simple_table_relation: $ => prec.right(20, seq(
      field('table', choice($._namespaced_or_simple_ref, $.member_expression)),
      optional(prec(25, $.where_clause))
    )),

    // --- Permissions value list ---
    // tabledata Customer = R, tabledata "Sales Header" = RIMD
    // Permission list that allows preprocessor conditionals between items
    // Items separated by commas, with preproc blocks interleaved
    tabledata_permission_list: $ => prec.left(repeat1(choice(
      seq($.tabledata_permission, optional(',')),
      $.preproc_conditional_permissions,
    ))),

    // Preprocessor conditionals inside permission lists
    preproc_conditional_permissions: $ => seq(
      $.preproc_if,
      repeat(choice(
        seq($.tabledata_permission, optional(',')),
        $.preproc_conditional_permissions,
      )),
      repeat(seq(
        $.preproc_elif,
        repeat(choice(
          seq($.tabledata_permission, optional(',')),
          $.preproc_conditional_permissions,
        )),
      )),
      optional(seq(
        $.preproc_else,
        repeat(choice(
          seq($.tabledata_permission, optional(',')),
          $.preproc_conditional_permissions,
        )),
      )),
      $.preproc_endif,
    ),

    tabledata_permission: $ => seq(
      choice(
        kw('tabledata'),
        $.table_keyword,
        $.codeunit_keyword,
        $.page_keyword,
        $.report_keyword,
        $.query_keyword,
        $.xmlport_keyword,
        kw('system'),
      ),
      field('table_name', choice($._namespaced_or_simple_ref, '*')),
      '=',
      field('permission', $.permission_type)
    ),

    permission_type: $ => token(prec(-1, new RustRegex('[rRiImMdDxX]+'))),

    // --- OrderBy value list ---
    // ascending("No.", Name)
    order_by_list: $ => prec.left(5, seq(
      $.order_by_item,
      repeat(seq(',', $.order_by_item))
    )),

    order_by_item: $ => seq(
      choice(kw('ascending', 5), kw('descending', 5)),
      '(',
      $._identifier_or_quoted,
      repeat(seq(',', $._identifier_or_quoted)),
      ')'
    ),

    // --- Implementation value list ---
    // "My Interface" = "My Codeunit"
    implementation_value_list: $ => prec.left(repeat1(choice(
      seq($.implementation_value, optional(',')),
      $.preproc_conditional_impl_values,
    ))),

    preproc_conditional_impl_values: $ => seq(
      $.preproc_if,
      repeat(seq($.implementation_value, optional(','))),
      repeat(seq(
        $.preproc_elif,
        repeat(seq($.implementation_value, optional(','))),
      )),
      optional(seq(
        $.preproc_else,
        repeat(seq($.implementation_value, optional(','))),
      )),
      $.preproc_endif,
    ),

    implementation_value: $ => seq(
      field('interface', $._identifier_or_quoted),
      '=',
      field('implementation', $._identifier_or_quoted)
    ),

    // --- OptionMembers value list ---
    // Option1, Option2, "Option 3"
    // Also supports leading/trailing commas for blank entries: ,Sale,"Total Sale"
    option_member_list: $ => prec.right(choice(
      // Standard: Member, Member, ... (also supports empty slots: Member,,Member)
      seq(
        $.option_member,
        repeat(seq(',', optional($.option_member)))
      ),
      // With leading commas (blank entries): ,,,Member,Member
      // Used by OptionMembers property and Option type: ,Sale,"Total Sale"
      seq(
        repeat1(','),
        optional(seq(
          $.option_member,
          repeat(seq(',', optional($.option_member)))
        ))
      ),
    )),

    option_member: $ => choice(
      $.identifier,
      $.quoted_identifier,
      $.string_literal,
      $.integer,             // Numeric option members (ValuesAllowed = 0, None, Partial)
      seq('-', $.integer),   // Negative integer option members (ValuesAllowed = -1)
      $.keyword_identifier,  // System, Action, etc.
      alias($.keyword_as_identifier, $.identifier),  // Type, Field, etc.
      $.local_keyword,       // 'Local' as option member
      $.internal_keyword,    // 'Internal' as option member
      $.protected_keyword,   // 'Protected' as option member
      $.boolean,             // true/false as option member
    ),

    // =====================================================================
    // Table internals
    // =====================================================================

    // --- Fields section ---
    // fields { field(1; "No."; Code[20]) { } }
    fields_section: $ => seq(
      $.fields_keyword,
      '{',
      repeat(choice(
        $.field_declaration,
        $.attribute_item,
        $.preproc_conditional_fields,
        // Extension modifications inside fields section
        $.modify_modification,
      )),
      '}'
    ),

    preproc_conditional_fields: $ => seq(
      $.preproc_if,
      repeat(choice($.field_declaration, $.attribute_item, $.modify_modification)),
      repeat(seq(
        $.preproc_elif,
        repeat(choice($.field_declaration, $.attribute_item, $.modify_modification)),
      )),
      optional(seq(
        $.preproc_else,
        repeat(choice($.field_declaration, $.attribute_item, $.modify_modification)),
      )),
      $.preproc_endif,
    ),

    field_declaration: $ => seq(
      kw('field'),
      '(',
      field('id', $.integer),
      ';',
      field('name', $._identifier_or_quoted),
      ';',
      field('type', $.type_specification),
      ')',
      optional(seq(
        '{',
        repeat($._body_element),
        '}'
      ))
    ),

    // --- Keys section ---
    // keys { key(PK; "No.") { Clustered = true; } }
    keys_section: $ => seq(
      $.keys_keyword,
      '{',
      repeat(choice(
        $.key_declaration,
        $.attribute_item,
        $.preproc_conditional_keys,
      )),
      '}'
    ),

    preproc_conditional_keys: $ => seq(
      $.preproc_if,
      repeat(choice($.key_declaration, $.attribute_item)),
      repeat(seq($.preproc_elif, repeat(choice($.key_declaration, $.attribute_item)))),
      optional(seq($.preproc_else, repeat(choice($.key_declaration, $.attribute_item)))),
      $.preproc_endif,
    ),

    key_declaration: $ => seq(
      $.key_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ';',
      field('fields', $.field_list),
      ')',
      optional(seq(
        '{',
        repeat($._body_element),
        '}'
      ))
    ),

    // Comma-separated list of field names
    field_list: $ => seq(
      $._identifier_or_quoted,
      repeat(seq(',', $._identifier_or_quoted))
    ),

    // --- Fieldgroups section ---
    // fieldgroups { fieldgroup(DropDown; "No.", Name) { } }
    fieldgroups_section: $ => seq(
      $.fieldgroups_keyword,
      '{',
      repeat(choice(
        $.fieldgroup_declaration,
        $.preproc_conditional_fieldgroups,
        // Extension modifications for fieldgroups
        $.addlast_fieldgroup_modification,
        $.addfirst_fieldgroup_modification,
      )),
      '}'
    ),

    addlast_fieldgroup_modification: $ => seq(
      kw('addlast'), '(', field('target', $._identifier_or_quoted), ';',
      field('fields', $.field_list), ')',
      optional(seq('{', '}'))
    ),

    addfirst_fieldgroup_modification: $ => seq(
      kw('addfirst'), '(', field('target', $._identifier_or_quoted), ';',
      field('fields', $.field_list), ')',
      optional(seq('{', '}'))
    ),

    preproc_conditional_fieldgroups: $ => seq(
      $.preproc_if,
      repeat(choice($.fieldgroup_declaration, $.preproc_conditional_fieldgroups)),
      repeat(seq($.preproc_elif, repeat(choice($.fieldgroup_declaration, $.preproc_conditional_fieldgroups)))),
      optional(seq($.preproc_else, repeat(choice($.fieldgroup_declaration, $.preproc_conditional_fieldgroups)))),
      $.preproc_endif,
    ),

    fieldgroup_declaration: $ => seq(
      $.fieldgroup_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ';',
      field('fields', $.field_list),
      ')',
      optional(seq(
        '{',
        repeat($._body_element),
        '}'
      ))
    ),

    // =====================================================================
    // Type system
    // =====================================================================

    type_specification: $ => choice(
      prec(2, $.array_type),
      prec(2, $.list_type),
      prec(2, $.dictionary_type),
      prec(1, $.text_type),
      prec(1, $.code_type),
      $.option_type,
      $.record_type,
      $.dotnet_type,
      $.object_reference_type,  // Codeunit, Page, Report, Query, Xmlport, Enum, Interface
      $.basic_type,
      $.identifier,             // Fallback for unknown types (HttpClient, DotNet, etc.)
      $.quoted_identifier,      // Quoted type references
    ),

    // Text[100] or plain Text
    text_type: $ => choice(
      prec(11, seq(kw('text'), '[', field('length', $.integer), ']')),
      prec(10, kw('text'))
    ),

    // Code[20] or plain Code
    code_type: $ => choice(
      prec(11, seq(kw('code'), '[', field('length', $.integer), ']')),
      prec(10, kw('code'))
    ),

    // Option with optional member list: Option OptionA, OptionB
    // Supports leading commas: Option ,,,,"Page","Query"
    option_type: $ => prec.right(1, seq(
      kw('option'),
      optional($.option_member_list)
    )),

    // Record "Customer" or Record Customer or Record 2000000041 [temporary]
    // Also: Record System.Reflection.Field temporary
    record_type: $ => prec.right(seq(
      prec(1, kw('record')),
      field('reference', $._namespaced_or_simple_ref),
      optional($.temporary_keyword)
    )),

    // DotNet "System.Text.StringBuilder" or DotNet System.DateTime type reference
    dotnet_type: $ => prec.right(seq(
      $.dotnet_keyword,
      field('reference', choice(
        $.string_literal,
        $._namespaced_or_simple_ref,
      ))
    )),

    // Object reference types: Codeunit "Sales-Post", Page "Customer Card", etc.
    // Also supports namespaced: Codeunit System.Environment."Client Type Management"
    object_reference_type: $ => prec.right(seq(
      field('object_type', choice(
        $.codeunit_keyword,
        $.page_keyword,
        $.report_keyword,
        $.query_keyword,
        $.xmlport_keyword,
        $.enum_keyword,
        $.interface_keyword,
        kw('testpage'),
        kw('testrequestpage'),
        $.controladdin_keyword,
      )),
      field('reference', $._namespaced_or_simple_ref)
    )),

    // Handles: "Name", Name, Namespace.Name, Namespace."Name", etc.
    _namespaced_or_simple_ref: $ => choice(
      $.integer,
      prec.right(seq(
        $._identifier_or_quoted,
        repeat(seq('.', $._identifier_or_quoted))
      )),
    ),

    // array[10] of Integer, array[10,20] of Text[100]
    array_type: $ => seq(
      prec(1, kw('array')),
      '[',
      field('sizes', seq($.integer, repeat(seq(',', $.integer)))),
      ']',
      kw('of'),
      field('element_type', $.type_specification)
    ),

    // List of [Integer]
    list_type: $ => seq(
      kw('list'),
      kw('of'),
      '[',
      field('element_type', $.type_specification),
      ']'
    ),

    // Dictionary of [Text, Integer]
    dictionary_type: $ => seq(
      kw('dictionary'),
      kw('of'),
      '[',
      field('key_type', $.type_specification),
      ',',
      field('value_type', $.type_specification),
      ']'
    ),

    // Common built-in types
    basic_type: $ => choice(
      // Numeric
      prec(1, kw('integer')),
      prec(1, kw('biginteger')),
      prec(1, kw('decimal')),
      prec(1, kw('byte')),
      // Text
      prec(1, kw('char')),
      prec(10, kw('label')),
      prec(1, kw('textbuilder')),
      prec(1, kw('textconst')),
      // Date/Time
      prec(1, kw('date')),
      prec(1, kw('time')),
      prec(1, kw('datetime')),
      prec(1, kw('duration')),
      kw('dateformula'),
      // Core
      prec(1, kw('boolean')),
      prec(1, kw('guid')),
      prec(1, kw('blob')),
      prec(1, kw('recordid')),
      prec(1, kw('recordref')),
      prec(1, kw('fieldref')),
      prec(1, kw('variant')),
      prec(1, kw('dialog')),
      prec(1, kw('action')),
      prec(1, kw('secrettext')),
      // JSON
      prec(1, kw('jsontoken')),
      prec(1, kw('jsonvalue')),
      prec(1, kw('jsonarray')),
      prec(1, kw('jsonobject')),
      // Media
      prec(1, kw('media')),
      prec(1, kw('mediaset')),
      // Stream
      prec(1, kw('instream')),
      prec(1, kw('outstream')),
      // HTTP
      prec(1, kw('httpclient')),
      prec(1, kw('httpcontent')),
      prec(1, kw('httpheaders')),
      prec(1, kw('httprequestmessage')),
      prec(1, kw('httpresponsemessage')),
      // Notification
      prec(1, kw('notification')),
      // Filter/Table
      prec(1, kw('filterpagebuilder')),
      prec(1, kw('tablefilter')),
      prec(1, kw('tableconnectiontype')),
      // XML
      prec(1, kw('xmldocument')),
      prec(1, kw('xmlelement')),
      prec(1, kw('xmlnode')),
      prec(1, kw('xmlnodelist')),
      prec(1, kw('xmlattribute')),
      // Error/Session
      prec(1, kw('errorinfo')),
      prec(1, kw('sessionsettings')),
      // File
      prec(1, kw('file')),
      prec(1, kw('fileupload')),
      // Other common types
      prec(1, kw('moduleinfo')),
      prec(1, kw('verbosity')),
      prec(1, kw('datatransfer')),
      prec(1, kw('version')),
      // Web
      prec(1, kw('webserviceactioncontext')),
    ),

    // =====================================================================
    // Enum values
    // =====================================================================

    // value(0; "None") { Caption = 'None'; }
    enum_value_declaration: $ => seq(
      kw('value'),
      '(',
      field('value_id', $.integer),
      ';',
      field('value_name', choice($._identifier_or_quoted, $.string_literal)),
      ')',
      '{',
      repeat($._body_element),
      '}'
    ),

    // =====================================================================
    // Labels section (report labels)
    // =====================================================================

    labels_section: $ => seq(
      $.labels_keyword,
      '{',
      repeat($.label_declaration),
      '}'
    ),

    // name = 'value', Locked = true, Comment = 'text';
    label_declaration: $ => seq(
      field('name', $.identifier),
      '=',
      field('value', $.string_literal),
      repeat(seq(
        ',',
        choice(
          seq(kw('comment'), '=', field('comment', $.string_literal)),
          seq(kw('locked'), '=', field('locked', $.boolean)),
          seq(kw('maxlength'), '=', field('maxlength', $.integer)),
        )
      )),
      ';'
    ),

    // =====================================================================
    // Page layout structure
    // =====================================================================

    layout_section: $ => seq(
      $.layout_keyword,
      '{',
      repeat($._layout_element),
      '}'
    ),

    _layout_element: $ => choice(
      $.area_section,
      $.group_section,
      $.repeater_section,
      $.cuegroup_section,
      $.fixed_section,
      $.grid_section,
      $.page_field,
      $.part_section,
      $.systempart_section,
      $.usercontrol_section,
      $.label_section,
      // Preprocessor in layout
      $.preproc_conditional_layout,
      $.preproc_split_field,
      // Extension layout modifications
      $.addfirst_modification,
      $.addlast_modification,
      $.addafter_modification,
      $.addbefore_modification,
      $.modify_modification,
      $.movefirst_modification,
      $.movelast_modification,
      $.moveafter_modification,
      $.movebefore_modification,
    ),

    // area(Content) { ... }
    area_section: $ => seq(
      $.area_keyword,
      '(',
      field('type', choice(
        kw('content'),
        kw('factboxes'),
        kw('processing'),
        kw('rolecenter'),
        kw('prompting'),
        kw('prompt'),
        kw('promptoptions'),
        kw('systemactions'),
        $.identifier,  // Fallback for future area types
      )),
      ')',
      '{',
      repeat($._layout_element),
      '}'
    ),

    // group(General) { ... }
    group_section: $ => seq(
      $.group_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      repeat(choice(
        $._body_element,
        $._layout_element,
      )),
      '}'
    ),

    // repeater(Lines) { ... }
    repeater_section: $ => seq(
      $.repeater_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      repeat(choice(
        $._body_element,
        $._layout_element,
      )),
      '}'
    ),

    // cuegroup(Cues) { ... }
    cuegroup_section: $ => seq(
      $.cuegroup_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      repeat(choice(
        $._body_element,
        $._layout_element,
      )),
      '}'
    ),

    // fixed(Fixed) { ... }
    fixed_section: $ => seq(
      $.fixed_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      repeat(choice(
        $._body_element,
        $._layout_element,
      )),
      '}'
    ),

    // grid(Grid) { ... }
    grid_section: $ => seq(
      $.grid_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      repeat(choice(
        $._body_element,
        $._layout_element,
      )),
      '}'
    ),

    // Page field: field(Name; SourceExpr) { }
    // Different from table field — no ID, no type, uses source expression
    page_field: $ => seq(
      kw('field'),
      '(',
      field('name', $._identifier_or_quoted),
      ';',
      field('source', $._field_source),
      ')',
      optional(seq(
        '{',
        repeat($._body_element),
        '}'
      ))
    ),

    // Source expression for page fields — uses full expression grammar
    _field_source: $ => $._expression,

    // part(PartName; PageName) { }
    part_section: $ => seq(
      $.part_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ';',
      field('source', $._identifier_or_quoted),
      ')',
      '{',
      repeat($._body_element),
      '}'
    ),

    // systempart(Links; "Record Link") { }
    systempart_section: $ => seq(
      $.systempart_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ';',
      field('source', $._identifier_or_quoted),
      ')',
      '{',
      repeat($._body_element),
      '}'
    ),

    // usercontrol(ControlName; ControlAddinName) { }
    usercontrol_section: $ => seq(
      $.usercontrol_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ';',
      field('source', $._identifier_or_quoted),
      ')',
      '{',
      repeat($._body_element),
      '}'
    ),

    // Preprocessor-split page field: #if field(...) #else field(...) #endif { props }
    preproc_split_field: $ => prec(25, seq(
      $.preproc_if,
      $._field_header,
      repeat(seq($.preproc_elif, $._field_header)),
      optional(seq($.preproc_else, $._field_header)),
      $.preproc_endif,
      optional(seq('{', repeat($._body_element), '}'))
    )),

    _field_header: $ => seq(
      kw('field'),
      '(',
      $._identifier_or_quoted,
      ';',
      $._expression,
      ')',
    ),

    // label(LabelName) { ... } — page label (not report label)
    label_section: $ => seq(
      kw('label'),
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      repeat($._body_element),
      '}'
    ),

    // =====================================================================
    // Extension layout modifications
    // =====================================================================

    // addfirst(AreaName) { field(...) { } }
    addfirst_modification: $ => seq(
      kw('addfirst'),
      '(',
      field('target', $._identifier_or_quoted),
      ')',
      '{',
      repeat($._layout_element),
      '}'
    ),

    addlast_modification: $ => seq(
      kw('addlast'),
      '(',
      field('target', $._identifier_or_quoted),
      ')',
      '{',
      repeat($._layout_element),
      '}'
    ),

    addafter_modification: $ => seq(
      kw('addafter'),
      '(',
      field('target', $._identifier_or_quoted),
      ')',
      '{',
      repeat($._layout_element),
      '}'
    ),

    addbefore_modification: $ => seq(
      kw('addbefore'),
      '(',
      field('target', $._identifier_or_quoted),
      ')',
      '{',
      repeat($._layout_element),
      '}'
    ),

    // modify("Name") { Visible = false; }
    modify_modification: $ => prec(2, seq(
      kw('modify'),
      '(',
      field('target', $._identifier_or_quoted),
      ')',
      '{',
      repeat($._body_element),
      '}'
    )),

    // movefirst(Content; "No.")
    movefirst_modification: $ => seq(
      kw('movefirst'),
      '(',
      field('target', $._identifier_or_quoted),
      ';',
      field('element', $._identifier_or_quoted),
      ')'
    ),

    movelast_modification: $ => seq(
      kw('movelast'),
      '(',
      field('target', $._identifier_or_quoted),
      ';',
      field('element', $._identifier_or_quoted),
      ')'
    ),

    moveafter_modification: $ => seq(
      kw('moveafter'),
      '(',
      field('target', $._identifier_or_quoted),
      ';',
      field('element', $._identifier_or_quoted),
      ')'
    ),

    movebefore_modification: $ => seq(
      kw('movebefore'),
      '(',
      field('target', $._identifier_or_quoted),
      ';',
      field('element', $._identifier_or_quoted),
      ')'
    ),

    // =====================================================================
    // Actions structure
    // =====================================================================

    actions_section: $ => seq(
      $.actions_keyword,
      '{',
      repeat($._action_element),
      '}'
    ),

    _action_element: $ => choice(
      $.action_area_section,
      $.action_group_section,
      $.action_declaration,
      $.separator_action,
      $.actionref_declaration,
      $.systemaction_declaration,
      $.fileuploadaction_declaration,
      $.customaction_declaration,
      // Properties/triggers directly in action areas
      $.property,
      $.trigger_declaration,
      $.attribute_item,
      // Extension action modifications
      $.addfirst_action_modification,
      $.addlast_action_modification,
      $.addafter_action_modification,
      $.addbefore_action_modification,
      $.modify_action_modification,
      // Preprocessor in actions
      $.preproc_conditional_actions,
    ),

    // area(Processing) { ... }
    action_area_section: $ => seq(
      $.area_keyword,
      '(',
      field('type', choice(
        kw('processing'),
        kw('reporting'),
        kw('navigation'),
        kw('creation'),
        kw('promoted'),
        kw('systemactions'),
        kw('sections'),
        kw('embedding'),
        kw('promptguide'),
        kw('prompting'),
        $.identifier,  // Fallback
      )),
      ')',
      '{',
      repeat($._action_element),
      '}'
    ),

    // group(ActionGroup) { ... }
    action_group_section: $ => seq(
      $.group_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      repeat(choice(
        $._action_element,
        $._body_element,
      )),
      '}'
    ),

    // action(MyAction) { ... }
    action_declaration: $ => seq(
      kw('action'),
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      repeat($._body_element),
      '}'
    ),

    // separator { } or separator(Name) { Caption = ''; IsHeader = true; }
    separator_action: $ => seq(
      kw('separator'),
      optional(seq('(', field('name', $._identifier_or_quoted), ')')),
      '{',
      repeat($._body_element),
      '}'
    ),

    // actionref(RefName; ActionName) { }
    actionref_declaration: $ => seq(
      kw('actionref'),
      '(',
      field('promoted_name', $._identifier_or_quoted),
      ';',
      field('action_name', $._identifier_or_quoted),
      ')',
      '{',
      repeat($._body_element),
      '}'
    ),

    // systemaction(Name) { }
    systemaction_declaration: $ => seq(
      kw('systemaction'),
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      repeat($._body_element),
      '}'
    ),

    // fileuploadaction(Name) { }
    fileuploadaction_declaration: $ => seq(
      kw('fileuploadaction'),
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      repeat($._body_element),
      '}'
    ),

    // customaction(Name) { }
    customaction_declaration: $ => seq(
      kw('customaction'),
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      repeat($._body_element),
      '}'
    ),

    // =====================================================================
    // Extension action modifications
    // =====================================================================

    addfirst_action_modification: $ => seq(
      kw('addfirst'),
      '(',
      field('target', $._identifier_or_quoted),
      ')',
      '{',
      repeat($._action_element),
      '}'
    ),

    addlast_action_modification: $ => seq(
      kw('addlast'),
      '(',
      field('target', $._identifier_or_quoted),
      ')',
      '{',
      repeat($._action_element),
      '}'
    ),

    addafter_action_modification: $ => seq(
      kw('addafter'),
      '(',
      field('target', $._identifier_or_quoted),
      ')',
      '{',
      repeat($._action_element),
      '}'
    ),

    addbefore_action_modification: $ => seq(
      kw('addbefore'),
      '(',
      field('target', $._identifier_or_quoted),
      ')',
      '{',
      repeat($._action_element),
      '}'
    ),

    modify_action_modification: $ => prec(2, seq(
      kw('modify'),
      '(',
      field('target', $._identifier_or_quoted),
      ')',
      '{',
      repeat($._body_element),
      '}'
    )),

    // =====================================================================
    // Views section
    // =====================================================================

    views_section: $ => seq(
      $.views_keyword,
      '{',
      repeat(choice(
        $.view_definition,
        // Extension modifications for views (with or without target)
        $.addfirst_modification,
        $.addlast_modification,
        $.addafter_modification,
        $.addbefore_modification,
        $.modify_modification,
        $.addfirst_views_modification,
        $.addlast_views_modification,
        $.addafter_views_modification,
        $.addbefore_views_modification,
      )),
      '}'
    ),

    // Views extensions without target: addfirst { view(...) { } }
    addfirst_views_modification: $ => seq(
      kw('addfirst'),
      '{',
      repeat($.view_definition),
      '}'
    ),

    addlast_views_modification: $ => seq(
      kw('addlast'),
      '{',
      repeat($.view_definition),
      '}'
    ),

    // Views extensions with target: addafter(ViewName) { view(...) { } }
    addafter_views_modification: $ => seq(
      kw('addafter'),
      '(', field('target', $._identifier_or_quoted), ')',
      '{',
      repeat($.view_definition),
      '}'
    ),

    addbefore_views_modification: $ => seq(
      kw('addbefore'),
      '(', field('target', $._identifier_or_quoted), ')',
      '{',
      repeat($.view_definition),
      '}'
    ),

    view_definition: $ => seq(
      $.view_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      repeat($._body_element),
      '}'
    ),

    // =====================================================================
    // Report sections
    // =====================================================================

    // dataset { dataitem(...) { column(...) { } } }
    dataset_section: $ => seq(
      $.dataset_keyword,
      '{',
      repeat(choice(
        $.report_dataitem,
        $.attribute_item,
        $.preproc_conditional_dataset,
        // Extension modifications for dataset
        $.addfirst_dataset_modification,
        $.addlast_dataset_modification,
        $.addafter_dataset_modification,
        $.addbefore_dataset_modification,
        $.add_dataset_modification,
        $.modify_modification,
      )),
      '}'
    ),

    // Preprocessor conditionals at dataset section level (around dataitems)
    preproc_conditional_dataset: $ => seq(
      $.preproc_if,
      repeat(choice($.report_dataitem, $.attribute_item)),
      repeat(seq($.preproc_elif, repeat(choice($.report_dataitem, $.attribute_item)))),
      optional(seq($.preproc_else, repeat(choice($.report_dataitem, $.attribute_item)))),
      $.preproc_endif,
    ),

    report_dataitem: $ => seq(
      $.dataitem_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ';',
      field('table_name', $._namespaced_or_simple_ref),
      ')',
      '{',
      repeat($._report_body_element),
      '}'
    ),

    _report_body_element: $ => choice(
      $.report_column,
      $.report_dataitem,  // Nested dataitems
      $._body_element,
      $.preproc_conditional_report,
    ),

    preproc_conditional_report: $ => seq(
      $.preproc_if,
      repeat($._report_body_element),
      repeat(seq($.preproc_elif, repeat($._report_body_element))),
      optional(seq($.preproc_else, repeat($._report_body_element))),
      $.preproc_endif,
    ),

    report_column: $ => seq(
      $.column_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ';',
      field('source', $._field_source),
      ')',
      '{',
      repeat($._body_element),
      '}'
    ),

    // Extension dataset modifications
    add_dataset_modification: $ => seq(
      kw('add'), '(', field('target', $._identifier_or_quoted), ')',
      '{', repeat(choice($.report_dataitem, $.report_column, $._body_element)), '}'
    ),
    addfirst_dataset_modification: $ => seq(
      kw('addfirst'),
      optional(seq('(', field('target', $._identifier_or_quoted), ')')),
      '{', repeat(choice($.report_dataitem, $.report_column, $._body_element)), '}'
    ),
    addlast_dataset_modification: $ => seq(
      kw('addlast'), '(', field('target', $._identifier_or_quoted), ')',
      '{', repeat(choice($.report_dataitem, $.report_column, $._body_element)), '}'
    ),
    addafter_dataset_modification: $ => seq(
      kw('addafter'), '(', field('target', $._identifier_or_quoted), ')',
      '{', repeat(choice($.report_dataitem, $.report_column, $._body_element)), '}'
    ),
    addbefore_dataset_modification: $ => seq(
      kw('addbefore'), '(', field('target', $._identifier_or_quoted), ')',
      '{', repeat(choice($.report_dataitem, $.report_column, $._body_element)), '}'
    ),

    // requestpage { layout { ... } actions { ... } }
    requestpage_section: $ => seq(
      $.requestpage_keyword,
      '{',
      repeat($._body_element),
      '}'
    ),

    // rendering { layout(Name) { ... } }
    rendering_section: $ => seq(
      $.rendering_keyword,
      '{',
      repeat($.rendering_layout),
      '}'
    ),

    rendering_layout: $ => seq(
      $.layout_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      repeat($._body_element),
      '}'
    ),

    // =====================================================================
    // Query sections
    // =====================================================================

    // elements { dataitem(...) { column(...) { } filter(...) { } } }
    elements_section: $ => seq(
      $.elements_keyword,
      '{',
      repeat($.query_dataitem),
      '}'
    ),

    query_dataitem: $ => seq(
      $.dataitem_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ';',
      field('table_name', $._namespaced_or_simple_ref),
      ')',
      '{',
      repeat($._query_body_element),
      '}'
    ),

    _query_body_element: $ => choice(
      $.query_column,
      $.query_filter,
      $.query_dataitem,  // Nested dataitems
      $._body_element,
      $.preproc_conditional_query,
    ),

    preproc_conditional_query: $ => seq(
      $.preproc_if,
      repeat($._query_body_element),
      repeat(seq($.preproc_elif, repeat($._query_body_element))),
      optional(seq($.preproc_else, repeat($._query_body_element))),
      $.preproc_endif,
    ),

    query_column: $ => seq(
      $.column_keyword,
      '(',
      choice(
        // Standard: column(Name; FieldName)
        seq(
          field('name', $._identifier_or_quoted),
          ';',
          field('field_name', $._identifier_or_quoted)
        ),
        // Computed: column(Name)
        field('name', $._identifier_or_quoted)
      ),
      ')',
      '{',
      repeat($._body_element),
      '}'
    ),

    query_filter: $ => seq(
      $.filter_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ';',
      field('field_name', $._identifier_or_quoted),
      ')',
      '{',
      repeat($._body_element),
      '}'
    ),

    // =====================================================================
    // XMLport sections
    // =====================================================================

    // schema { tableelement(...) { fieldelement(...) { } } }
    schema_section: $ => seq(
      $.schema_keyword,
      '{',
      repeat($.xmlport_element),
      '}'
    ),

    // tableelement/fieldelement/textelement(Name; Source) { ... }
    xmlport_element: $ => seq(
      field('element_type', choice(
        kw('tableelement'),
        kw('fieldelement'),
        kw('textelement'),
      )),
      '(',
      field('name', $._identifier_or_quoted),
      optional(seq(
        ';',
        field('source', $._field_source)
      )),
      ')',
      '{',
      repeat($._xmlport_body_element),
      '}'
    ),

    _xmlport_body_element: $ => choice(
      $.xmlport_element,
      $.xmlport_attribute,
      $._body_element,
      $.preproc_conditional_xmlport,
    ),

    preproc_conditional_xmlport: $ => seq(
      $.preproc_if,
      repeat($._xmlport_body_element),
      repeat(seq($.preproc_elif, repeat($._xmlport_body_element))),
      optional(seq($.preproc_else, repeat($._xmlport_body_element))),
      $.preproc_endif,
    ),

    // fieldattribute/textattribute(Name; Source) { ... }
    xmlport_attribute: $ => seq(
      field('attribute_type', choice(
        kw('fieldattribute'),
        kw('textattribute'),
      )),
      '(',
      field('name', $._identifier_or_quoted),
      optional(seq(
        ';',
        field('source', $._field_source)
      )),
      ')',
      '{',
      repeat($._body_element),
      '}'
    ),

    // =====================================================================
    // DotNet internals
    // =====================================================================

    assembly_declaration: $ => seq(
      kw('assembly'),
      '(',
      field('name', choice(
        $.string_literal,
        $.quoted_identifier,
        $.dotnet_assembly_name
      )),
      ')',
      '{',
      repeat(choice(
        $.type_declaration,
        $.property,
        $.empty_statement,
      )),
      '}'
    ),

    dotnet_assembly_name: $ => token(seq(
      /[\p{L}_][\p{L}\p{N}_]*/u,
      repeat(seq('.', /[\p{L}_][\p{L}\p{N}_]*/u))
    )),

    type_declaration: $ => seq(
      kw('type'),
      '(',
      field('dotnet_type', choice(
        $.string_literal,
        $.quoted_identifier,
        $.dotnet_assembly_name
      )),
      ';',
      field('al_name', choice(
        $.string_literal,
        $.quoted_identifier,
        $.identifier
      )),
      ')',
      '{',
      repeat($._body_element),
      '}'
    ),

    // =====================================================================
    // ControlAddIn event declarations
    // =====================================================================

    // event OnReady();
    event_declaration: $ => prec.right(seq(
      $.event_keyword,
      field('name', $._identifier_or_quoted),
      '(',
      optional($.parameter_list),
      ')',
      optional(';')
    )),

    // =====================================================================
    // Procedures
    // =====================================================================

    procedure: $ => prec.right(seq(
      optional(field('modifier', $.procedure_modifier)),
      $.procedure_keyword,
      field('name', $._identifier_or_quoted),
      '(',
      optional($.parameter_list),
      ')',
      optional(choice(
        seq(
          choice(
            $._procedure_return_specification,
            $._procedure_named_return,
          ),
          optional(';')
        )
      )),
      optional(';'),
      optional(choice(
        $.var_section,
        $.preproc_conditional_var_block,
      )),
      $.code_block
    )),

    // Preprocessor-split procedure: header variants in #if/#else, shared body
    preproc_split_procedure: $ => prec(25, seq(
      $.preproc_if,
      $._procedure_header,
      repeat(seq($.preproc_elif, $._procedure_header)),
      optional(seq($.preproc_else, $._procedure_header)),
      $.preproc_endif,
      optional(';'),
      optional(choice(
        $.var_section,
        $.preproc_conditional_var_block,
      )),
      $.code_block,
    )),

    // Procedure header without body (used in preproc split procedures)
    _procedure_header: $ => seq(
      repeat($.attribute_item),
      optional(field('modifier', $.procedure_modifier)),
      $.procedure_keyword,
      field('name', $._identifier_or_quoted),
      '(',
      optional($.parameter_list),
      ')',
      optional(choice(
        seq(
          choice(
            $._procedure_return_specification,
            $._procedure_named_return,
          ),
          optional(';')
        )
      )),
    ),

    // Interface procedure declaration (no body, just signature)
    // Uses prec.dynamic to prefer full procedure when body follows
    interface_procedure: $ => prec.dynamic(-1, prec.right(-5, seq(
      $.procedure_keyword,
      field('name', $._identifier_or_quoted),
      '(',
      optional($.parameter_list),
      ')',
      optional($.interface_procedure_suffix),
    ))),

    // Suffix for interface_procedure: return type and/or semicolon
    // Separated as a named rule to avoid state-sharing with _procedure_header
    interface_procedure_suffix: $ => choice(
      seq($._procedure_return_specification, optional(';')),
      seq($._procedure_named_return, optional(';')),
      ';',
    ),

    procedure_modifier: $ => choice(
      $.local_keyword,
      $.internal_keyword,
      $.protected_keyword,
    ),

    // Return type: `: TypeSpec`
    _procedure_return_specification: $ => seq(
      ':',
      field('return_type', $.type_specification),
    ),

    // Named return: `result: TypeSpec`
    _procedure_named_return: $ => prec(15, seq(
      field('return_value', $._identifier_or_quoted),
      $._procedure_return_specification,
    )),

    // Parameter list: semicolon-separated parameters
    parameter_list: $ => seq(
      optional(repeat1($.attribute_item)),
      $.parameter,
      repeat(seq(';', optional(repeat1($.attribute_item)), $.parameter)),
    ),

    parameter: $ => seq(
      optional(field('modifier', $.var_keyword)),
      field('name', $._identifier_or_quoted),
      ':',
      field('type', $.type_specification),
    ),

    // code_block: begin ... end;
    // At depth 0: scanner emits begin_keyword/end_keyword (named tokens)
    // At depth > 0: scanner declines, kw() anonymous regex handles it
    code_block: $ => prec.right(seq(
      choice($.begin_keyword, kw('begin')),
      repeat($._statement),
      choice($.end_keyword, kw('end')),
      optional(';'),
    )),

    // =====================================================================
    // Triggers
    // =====================================================================

    trigger_declaration: $ => seq(
      $.trigger_keyword,
      field('name', $._trigger_name),
      '(',
      optional($.parameter_list),
      ')',
      optional(choice(
        $._procedure_return_specification,
        $._procedure_named_return,
      )),
      optional(';'),
      optional(choice(
        $.var_section,
        $.preproc_conditional_var_block,
      )),
      $.code_block
    ),

    // Preprocessor conditional wrapping a var section before begin
    preproc_conditional_var_block: $ => seq(
      $.preproc_if,
      optional($.var_section),
      repeat(seq(
        $.preproc_elif,
        optional($.var_section),
      )),
      optional(seq(
        $.preproc_else,
        optional($.var_section),
      )),
      $.preproc_endif,
    ),

    // Trigger name: simple name or scoped name (UserTours::ShowTourWizard)
    _trigger_name: $ => choice(
      seq($._identifier_or_quoted, '::', $._identifier_or_quoted),
      $._identifier_or_quoted,
    ),

    // =====================================================================
    // Variable declarations
    // =====================================================================

    var_section: $ => prec.right(seq(
      optional(choice($.protected_keyword, $.local_keyword)),
      $.var_keyword,
      repeat(choice(
        $.variable_declaration,
        $.attribute_item,
        $.preproc_conditional_var,
        $.preproc_split_procedure,
      )),
    )),

    preproc_conditional_var: $ => seq(
      $.preproc_if,
      repeat(choice($.variable_declaration, $.attribute_item, $._body_element)),
      repeat(seq(
        $.preproc_elif,
        repeat(choice($.variable_declaration, $.attribute_item, $._body_element)),
      )),
      optional(seq(
        $.preproc_else,
        repeat(choice($.variable_declaration, $.attribute_item, $._body_element)),
      )),
      $.preproc_endif,
    ),

    variable_declaration: $ => choice(
      // Label variable: Name: Label 'text', Locked = true;
      prec(5, seq(
        field('name', $._identifier_or_quoted),
        ':',
        field('type', $.basic_type),  // Must be Label type
        field('value', $.string_literal),
        optional(seq(
          ',',
          optional(seq(
            $.label_attribute,
            repeat(seq(',', $.label_attribute))
          ))
        )),
        ';'
      )),
      // Multi-name variable: Name1, Name2, Name3 : Type;
      prec(3, seq(
        field('name', $._identifier_or_quoted),
        repeat1(seq(',', field('name', $._identifier_or_quoted))),
        ':',
        field('type', $.type_specification),
        ';'
      )),
      // Regular variable: Name: Type;
      prec(1, seq(
        field('name', $._identifier_or_quoted),
        ':',
        field('type', $.type_specification),
        ';'
      )),
    ),

    label_attribute: $ => seq(
      field('name', $.identifier),
      '=',
      field('value', choice($.boolean, $.string_literal, $.integer))
    ),

    // =====================================================================
    // Attributes
    // =====================================================================

    attribute_item: $ => seq(
      '[',
      field('attribute', $.attribute_content),
      ']'
    ),

    attribute_content: $ => seq(
      field('name', $.identifier),
      optional(field('arguments', $.attribute_arguments)),
    ),

    attribute_arguments: $ => seq(
      '(',
      optional($.attribute_argument_list),
      ')'
    ),

    attribute_argument_list: $ => seq(
      $._attribute_argument,
      repeat(seq(',', $._attribute_argument)),
    ),

    _attribute_argument: $ => choice(
      $.boolean,
      $.integer,
      $.string_literal,
      $.identifier,
      $.quoted_identifier,
      $.qualified_enum_value,
      $.database_reference,
      $.member_expression,
    ),

    // =====================================================================
    // Preprocessor directives
    // =====================================================================

    // Structural preprocessor conditionals: #if/#elif/#else/#endif
    preproc_conditional: $ => seq(
      $.preproc_if,
      repeat($._body_element),
      repeat(seq(
        $.preproc_elif,
        repeat($._body_element),
      )),
      optional(seq(
        $.preproc_else,
        repeat($._body_element),
      )),
      $.preproc_endif,
    ),

    preproc_if: $ => seq(
      choice($.preproc_open, '#if', '#IF', '#If'),
      field('condition', choice(
        $.identifier,
        $.preproc_not_expression,
      ))
    ),

    preproc_not_expression: $ => seq(
      choice('not', 'NOT', 'Not'),
      $.identifier
    ),

    preproc_elif: $ => seq(
      choice('#elif', '#ELIF', '#Elif'),
      field('condition', choice(
        $.identifier,
        $.preproc_not_expression,
      ))
    ),

    preproc_else: $ => choice('#else', '#ELSE', '#Else'),

    preproc_endif: $ => choice($.preproc_close, '#endif', '#ENDIF', '#Endif'),

    // Preprocessor-split if statement: if header varies across #if/#else, body is shared
    // Pattern 1: #if COND / if (expr) then / #else / if (expr) then / #endif / body;
    // Pattern 2: #if COND / if (expr) then / #endif / body;  (no #else)
    preproc_split_if_statement: $ => prec.right(seq(
      $.preproc_if,
      $._preproc_if_header,
      repeat(seq($.preproc_elif, $._preproc_if_header)),
      optional(seq($.preproc_else, $._preproc_if_header)),
      $.preproc_endif,
      field('then_branch', choice(
        $.code_block,
        $._statement,
      )),
      optional(seq(
        $.else_keyword,
        field('else_branch', choice(
          $.code_block,
          prec(1, $.if_statement),
          $._statement,
        ))
      ))
    )),

    // If-then header (condition only, no body) — used in preproc split if statements
    _preproc_if_header: $ => seq(
      $.if_keyword,
      field('condition', $._expression),
      $.then_keyword,
    ),

    // Preprocessor-guarded statement: guard statements + split if-then before shared code
    // #if COND / guard_stmts; if X then / #endif / shared_statement;
    // In COND mode: guard_stmts; if X then shared_statement;
    // Otherwise: just shared_statement;
    preproc_guarded_statement: $ => prec.right(seq(
      $.preproc_if,
      $._preproc_guard_block,
      $.preproc_endif,
      field('then_branch', choice(
        $.code_block,
        $._statement,
      )),
    )),

    // Guard block: one or more expression statements followed by an if-then header
    // Uses _expression_statement to avoid consuming if-statements that could
    // be mistaken for _preproc_if_header
    _preproc_guard_block: $ => seq(
      repeat1(seq(prec(2, $._expression_statement), ';')),
      $._preproc_if_header,
    ),

    // Preprocessor-split if-else: full if-then-X-else inside #if, Y outside
    // #if COND / if X then Y else / #endif / Z;
    preproc_split_if_else_statement: $ => prec.right(seq(
      $.preproc_if,
      $.if_keyword,
      field('condition', $._expression),
      $.then_keyword,
      field('then_branch', choice(
        $.code_block,
        $._statement,
      )),
      $.else_keyword,
      choice(
        // Fragmented: else begin #endif stmts #if end; #endif
        // The if-then-begin-...-end-else-begin pattern where begin opens shared body
        $.preproc_fragmented_else_tail,
        // Normal: else followed by #elif/#else/#endif variants, then shared else body
        seq(
          repeat(seq($.preproc_elif,
            $.if_keyword,
            field('condition', $._expression),
            $.then_keyword,
            field('then_branch', choice(
              $.code_block,
              $._statement,
            )),
            $.else_keyword,
          )),
          optional(seq($.preproc_else,
            $.if_keyword,
            field('condition', $._expression),
            $.then_keyword,
            field('then_branch', choice(
              $.code_block,
              $._statement,
            )),
            $.else_keyword,
          )),
          $.preproc_endif,
          field('else_branch', choice(
            $.code_block,
            $._statement,
          )),
        ),
      ),
    )),

    // Preprocessor split if-then-begin:
    // #if COND / if EXPR then begin / #endif / statements / #if COND / end; / #endif
    preproc_split_if_then_begin: $ => prec(26, seq(
      $.preproc_if,
      repeat($._statement),           // allow preamble statements before if
      $.if_keyword,
      field('condition', $._expression),
      $.then_keyword,
      $.preproc_split_begin,          // 'begin' at depth > 0, before #endif
      $.preproc_endif,
      repeat($._statement),
      $.preproc_if,
      repeat($._statement),           // allow preamble before end
      kw('end'),
      optional(';'),
      $.preproc_endif,
    )),

    // Fragmented else tail: begin #endif stmts #if end; #endif
    // Used after else_keyword when the else branch's begin/end is split across preprocessor blocks
    preproc_fragmented_else_tail: $ => prec(25, seq(
      $.preproc_split_begin,          // 'begin' at depth > 0, before #endif
      $.preproc_endif,
      repeat($._statement),
      $.preproc_if,
      kw('end'),
      optional(';'),
      $.preproc_endif,
    )),

    // Preprocessor conditionals in statements context
    preproc_conditional_statement: $ => prec.right(seq(
      $.preproc_if,
      repeat($._statement),
      repeat(seq(
        $.preproc_elif,
        repeat($._statement),
      )),
      optional(seq(
        $.preproc_else,
        repeat($._statement),
      )),
      $.preproc_endif,
    )),

    // Preprocessor conditionals in actions context
    preproc_conditional_actions: $ => seq(
      $.preproc_if,
      repeat($._action_element),
      repeat(seq(
        $.preproc_elif,
        repeat($._action_element),
      )),
      optional(seq(
        $.preproc_else,
        repeat($._action_element),
      )),
      $.preproc_endif,
    ),

    // Preprocessor conditionals in layout context
    preproc_conditional_layout: $ => seq(
      $.preproc_if,
      repeat($._layout_element),
      repeat(seq(
        $.preproc_elif,
        repeat($._layout_element),
      )),
      optional(seq(
        $.preproc_else,
        repeat($._layout_element),
      )),
      $.preproc_endif,
    ),

    // Pragma and region directives (extras — can appear anywhere)
    pragma: $ => new RustRegex('#pragma[^\\n\\r]*'),

    preproc_region: $ => new RustRegex('(?i)#\\s*region[^\\n\\r]*'),

    preproc_endregion: $ => new RustRegex('(?i)#\\s*endregion[^\\n\\r]*'),

    // =====================================================================
    // Statements
    // =====================================================================

    _statement: $ => prec.right(seq(
      choice(
        $.assignment_statement,
        $.asserterror_statement,
        $.if_statement,
        $.exit_statement,
        $.continue_statement,
        $.break_statement,
        $.case_statement,
        $.for_statement,
        $.repeat_statement,
        $.while_statement,
        $.foreach_statement,
        $.with_statement,
        $._expression_statement,
        $.empty_statement,
        $.preproc_conditional_statement,
        $.preproc_split_if_statement,
        $.preproc_split_if_else_statement,
        $.preproc_split_if_then_begin,
        $.preproc_guarded_statement,
      ),
      optional(';')
    )),

    _expression_statement: $ => $._expression,

    empty_statement: $ => ';',

    // --- Assignment ---

    assignment_statement: $ => prec.dynamic(10, seq(
      field('left', $._expression),
      field('operator', $._assignment_operator),
      field('right', $._expression)
    )),

    assignment_expression: $ => prec.dynamic(1, prec.right(seq(
      field('left', $._expression),
      field('operator', $._assignment_operator),
      field('right', $._expression)
    ))),

    _assignment_operator: $ => token(choice(':=', '+=', '-=', '*=', '/=')),

    // --- If/Then/Else ---

    if_statement: $ => prec.right(seq(
      $.if_keyword,
      field('condition', $._expression),
      $.then_keyword,
      field('then_branch', choice(
        $.code_block,
        $._statement,
      )),
      optional(seq(
        $.else_keyword,
        field('else_branch', choice(
          $.code_block,
          prec(1, $.if_statement),
          $._statement,
        ))
      ))
    )),

    // --- Case ---

    case_statement: $ => prec(2, seq(
      $.case_keyword,
      field('expression', $._expression),
      $.of_keyword,
      repeat(choice(
        $.case_branch,
        $.preproc_conditional_case,
      )),
      optional($.case_else_branch),
      kw('end')
    )),

    // Preprocessor conditionals inside case statements
    preproc_conditional_case: $ => seq(
      $.preproc_if,
      repeat($.case_branch),
      optional($.case_else_branch),
      repeat(seq($.preproc_elif, repeat($.case_branch), optional($.case_else_branch))),
      optional(seq($.preproc_else, repeat($.case_branch), optional($.case_else_branch))),
      $.preproc_endif,
    ),

    case_branch: $ => choice(
      seq(
        field('pattern', $._case_pattern),
        ':',
        field('body', choice(
          $.code_block,
          $._statement,
        ))
      ),
      // Preprocessor-split case branch: #if wraps extra patterns before the main pattern
      // #if COND  pattern1,  #endif  pattern2: body;
      $.preproc_split_case_branch,
    ),

    // Case branch where some patterns are conditionally included via preprocessor
    preproc_split_case_branch: $ => prec(25, seq(
      $.preproc_if,
      repeat(seq($._single_pattern, optional(','))),
      repeat(seq(
        $.preproc_elif,
        repeat(seq($._single_pattern, optional(','))),
      )),
      optional(seq(
        $.preproc_else,
        repeat(seq($._single_pattern, optional(','))),
      )),
      $.preproc_endif,
      // Pattern(s) after the preprocessor block, ending with ':'
      field('pattern', $._case_pattern),
      ':',
      field('body', choice(
        $.code_block,
        $._statement,
      ))
    )),

    // Case pattern list: supports preprocessor conditionals interleaved with patterns
    _case_pattern: $ => repeat1(choice(
      seq($._single_pattern, optional(',')),
      $.preproc_conditional_case_patterns,
    )),

    // Preprocessor conditional wrapping case pattern entries mid-list
    preproc_conditional_case_patterns: $ => seq(
      $.preproc_if,
      repeat(seq($._single_pattern, optional(','))),
      repeat(seq(
        $.preproc_elif,
        repeat(seq($._single_pattern, optional(','))),
      )),
      optional(seq(
        $.preproc_else,
        repeat(seq($._single_pattern, optional(','))),
      )),
      $.preproc_endif,
    ),

    _single_pattern: $ => choice(
      $._literal_value,
      $.qualified_enum_value,
      $.database_reference,
      $.range_expression,
      $.call_expression,
      $.identifier,
      $.quoted_identifier,
      $.member_expression,
      $.unary_expression,
      $.parenthesized_expression,
      $.keyword_identifier,
      // Expressions as case patterns (case true of: X > 0: ...)
      $.comparison_expression,
      $.logical_expression,
      $.additive_expression,
      $.multiplicative_expression,
      $.subscript_expression,
      // In expression as case pattern (case true of: X in [...]: ...)
      prec.left(5, seq(
        field('left', $._expression),
        field('operator', $.in_keyword),
        field('right', $.list_literal)
      )),
    ),

    case_else_branch: $ => prec.left(seq(
      $.else_keyword,
      choice(
        $.code_block,
        repeat($._statement),
      )
    )),

    // --- For loop ---

    for_statement: $ => prec.right(seq(
      $.for_keyword,
      field('variable', choice(
        $.identifier,
        $.quoted_identifier,
        $.member_expression,
      )),
      ':=',
      field('start', $._expression),
      field('direction', choice(
        $.to_keyword,
        $.downto_keyword,
      )),
      field('end', $._expression),
      $.do_keyword,
      field('body', choice(
        $._statement,
        $.code_block,
      ))
    )),

    // --- Foreach ---

    foreach_statement: $ => prec.right(seq(
      $.foreach_keyword,
      field('variable', choice($.identifier, $.quoted_identifier)),
      $.in_keyword,
      field('iterable', $._expression),
      $.do_keyword,
      field('body', choice(
        $._statement,
        $.code_block,
      ))
    )),

    // --- While ---

    while_statement: $ => prec.right(seq(
      $.while_keyword,
      field('condition', $._expression),
      $.do_keyword,
      field('body', choice(
        $._statement,
        $.code_block,
      ))
    )),

    // --- Repeat/Until ---

    repeat_statement: $ => seq(
      $.repeat_keyword,
      repeat($._statement),
      $.until_keyword,
      field('condition', $._expression)
    ),

    // --- With ---

    with_statement: $ => prec.right(seq(
      $.with_keyword,
      field('record', $._expression),
      $.do_keyword,
      field('body', choice(
        $._statement,
        $.code_block,
      ))
    )),

    // --- Exit ---

    exit_statement: $ => prec(13, seq(
      $.exit_keyword,
      optional(seq(
        token.immediate('('),
        optional(field('return_value', $._expression)),
        ')'
      ))
    )),

    // --- Continue / Break ---

    continue_statement: $ => prec(13, $.continue_keyword),
    break_statement: $ => prec(13, $.break_keyword),

    // --- Asserterror ---

    asserterror_statement: $ => prec.right(14, seq(
      $.asserterror_keyword,
      optional(field('body', choice(
        $._expression,
        $.code_block,
      )))
    )),

    // =====================================================================
    // Expressions
    // =====================================================================

    _expression: $ => choice(
      // Binary operators
      $.range_expression,
      $.multiplicative_expression,
      $.additive_expression,
      $.comparison_expression,
      $.logical_expression,
      // In expression
      prec.left(5, seq(
        field('left', $._expression),
        field('operator', $.in_keyword),
        field('right', $.list_literal)
      )),
      // Is expression (type checking)
      prec.left(5, seq(
        field('left', $._expression),
        field('operator', kw('is', 5)),
        field('right', $.type_specification)
      )),
      // As expression (type casting)
      prec.left(5, seq(
        field('left', $._expression),
        field('operator', kw('as', 5)),
        field('right', $.type_specification)
      )),
      // Other expression forms
      $.qualified_enum_value,
      $.database_reference,
      $.call_expression,
      $.member_expression,
      $.subscript_expression,
      $.identifier,
      $.quoted_identifier,
      $._literal_value,
      $.parenthesized_expression,
      $.unary_expression,
      $.list_literal,
      // Keywords that can be used as identifiers in expressions
      $.keyword_identifier,
      // 'continue' as identifier when followed by ':='
      alias($.continue_as_identifier, $.identifier),
      // Ternary expression: condition ? then_value : else_value
      $.ternary_expression,
      // Assignment as expression (for asserterror and other contexts)
      prec.left(1, $.assignment_expression),
    ),

    // Keywords that can appear as identifiers in expressions (e.g., Codeunit.Run())
    keyword_identifier: $ => prec(-5, choice(
      $.codeunit_keyword,
      $.page_keyword,
      $.report_keyword,
      $.query_keyword,
      $.xmlport_keyword,
      kw('record'),
      $.enum_keyword,
      kw('system'),
      kw('session'),
      kw('dialog'),
      kw('database'),
      kw('file'),
      kw('action'),
    )),

    // --- Binary expressions ---

    range_expression: $ => prec.left(8, seq(
      field('left', $._expression),
      '..',
      field('right', $._expression)
    )),

    multiplicative_expression: $ => prec.left(7, seq(
      field('left', $._expression),
      field('operator', choice('*', '/', choice('div', 'DIV', 'Div'), choice('mod', 'MOD', 'Mod'))),
      field('right', $._expression)
    )),

    additive_expression: $ => prec.left(6, seq(
      field('left', $._expression),
      field('operator', choice('+', '-')),
      field('right', $._expression)
    )),

    comparison_expression: $ => prec.left(4, seq(
      field('left', $._expression),
      field('operator', $.comparison_operator),
      field('right', $._expression)
    )),

    comparison_operator: $ => choice(
      '>=',
      '<=',
      '>',
      '<',
      '<>',
      '='
    ),

    logical_expression: $ => choice(
      // AND (prec 3)
      prec.left(3, seq(
        field('left', $._expression),
        field('operator', choice('and', 'AND', 'And')),
        field('right', $._expression)
      )),
      // OR (prec 2)
      prec.left(2, seq(
        field('left', $._expression),
        field('operator', choice('or', 'OR', 'Or')),
        field('right', $._expression)
      )),
      // XOR (prec 2)
      prec.left(2, seq(
        field('left', $._expression),
        field('operator', choice('xor', 'XOR', 'Xor')),
        field('right', $._expression)
      )),
    ),

    // --- Ternary expression ---
    // condition ? then_value : else_value
    ternary_expression: $ => prec.right(1, seq(
      field('condition', $._expression),
      '?',
      field('then_value', $._expression),
      ':',
      field('else_value', $._expression)
    )),

    // --- Unary expression ---

    unary_expression: $ => prec.right(7, seq(
      field('operator', choice('+', '-', choice('not', 'NOT', 'Not'))),
      field('operand', $._expression)
    )),

    // --- Postfix expressions ---

    call_expression: $ => prec(12, seq(
      field('function', choice(
        $.identifier,
        $.member_expression,
        $.qualified_enum_value,
        $.keyword_identifier,     // System(), Dialog(), etc.
        $.subscript_expression,   // X[1]()
      )),
      field('arguments', $.argument_list)
    )),

    argument_list: $ => seq(
      '(',
      optional(seq(
        $._expression,
        repeat(seq(',', $._expression))
      )),
      ')'
    ),

    member_expression: $ => prec.left(11, seq(
      field('object', $._expression),
      '.',
      field('member', $._identifier_or_quoted)
    )),

    subscript_expression: $ => prec.left(9, seq(
      field('object', $._expression),
      '[',
      field('index', $._expression),
      repeat(seq(',', $._expression)),
      ']'
    )),

    parenthesized_expression: $ => seq(
      '(',
      $._expression,
      ')'
    ),

    // --- List literal ---

    list_literal: $ => seq(
      '[',
      optional(seq(
        $._expression,
        repeat(seq(',', $._expression))
      )),
      ']'
    ),

    // --- Qualified enum value ---
    // Status::Active, Enum::"Sales Line Type"::Item

    qualified_enum_value: $ => prec.left(50, seq(
      field('enum_type', choice(
        $.identifier,
        $.quoted_identifier,
        $.member_expression,
        $.subscript_expression,  // Allow X[1]::Value
        $.call_expression,       // Allow Func()::Value
        $.qualified_enum_value,  // Chained: Enum::"Type"::"Value"
        $.keyword_identifier,    // Allow Enum::, Record::, etc.
      )),
      '::',
      field('value', $._identifier_or_quoted)
    )),

    // --- Database reference ---
    // DATABASE::"Customer"

    database_reference: $ => prec(300, seq(
      field('keyword', alias(
        choice(
          kw('database'),
          $.page_keyword,
          $.report_keyword,
          $.codeunit_keyword,
          $.xmlport_keyword,
          $.query_keyword,
        ),
        $.object_type_keyword
      )),
      '::',
      field('table_name', $._identifier_or_quoted)
    )),

    // --- Literal values ---

    _literal_value: $ => choice(
      $.integer,
      $.decimal,
      $.boolean,
      $.string_literal,
      $.datetime_literal,
      $.date_literal,
      $.time_literal,
      $.biginteger_literal,
    ),

    // DateTime: 0DT or YYYYMMDDTHHmmssZ
    datetime_literal: $ => token(prec(2, choice(
      /\d+DT/,
      new RustRegex('\\d{8}T\\d{6}[A-Z]?'),
    ))),

    // Date: 0D or YYYYMMDD
    date_literal: $ => token(prec(1, /\d+D/)),

    // Time: 0T or HHmmssT or HHmmss.mmmT
    time_literal: $ => token(prec(2, choice(
      /\d+\.\d+T/,  // Decimal time: 235959.999T
      /\d+T/,        // Integer time: 000000T, 0T
    ))),

    // BigInteger: 1000L
    biginteger_literal: $ => token(prec(1, /\d+L/)),

    // =====================================================================
    // Named keyword rules
    // =====================================================================

    // --- Tier 1: Control flow ---

    if_keyword: $ => prec(10, choice('if', 'IF', 'If')),
    then_keyword: $ => prec(10, choice('then', 'THEN', 'Then')),
    else_keyword: $ => prec(10, choice('else', 'ELSE', 'Else')),
    case_keyword: $ => prec(10, choice('case', 'CASE', 'Case')),
    of_keyword: $ => prec(10, choice('of', 'OF', 'Of')),
    for_keyword: $ => prec(10, choice('for', 'FOR', 'For')),
    foreach_keyword: $ => prec(10, choice('foreach', 'FOREACH', 'Foreach')),
    while_keyword: $ => prec(10, choice('while', 'WHILE', 'While')),
    do_keyword: $ => prec(10, choice('do', 'DO', 'Do')),
    repeat_keyword: $ => prec(10, choice('repeat', 'REPEAT', 'Repeat')),
    until_keyword: $ => prec(10, choice('until', 'UNTIL', 'Until')),
    exit_keyword: $ => prec(10, choice('exit', 'EXIT', 'Exit')),
    continue_keyword: $ => prec(10, choice('continue', 'CONTINUE', 'Continue')),
    break_keyword: $ => prec(10, choice('break', 'BREAK', 'Break')),
    with_keyword: $ => prec(10, choice('with', 'WITH', 'With')),
    asserterror_keyword: $ => kw('asserterror', 10),
    in_keyword: $ => prec(10, choice('in', 'IN', 'In')),
    to_keyword: $ => prec(10, choice('to', 'TO', 'To')),
    downto_keyword: $ => prec(10, choice('downto', 'DOWNTO', 'Downto')),

    // --- Tier 2: Object types ---

    table_keyword: $ => kw('table'),
    tableextension_keyword: $ => prec(10, choice('tableextension', 'TABLEEXTENSION', 'Tableextension', 'TableExtension', 'tableExtension')),
    page_keyword: $ => kw('page'),
    pageextension_keyword: $ => prec(10, choice('pageextension', 'PAGEEXTENSION', 'Pageextension', 'PageExtension', 'pageExtension')),
    codeunit_keyword: $ => prec(10, choice('codeunit', 'CODEUNIT', 'Codeunit', 'CodeUnit', 'COdeunit', 'codeUnit')),
    report_keyword: $ => kw('report'),
    reportextension_keyword: $ => prec(10, choice('reportextension', 'REPORTEXTENSION', 'Reportextension', 'ReportExtension', 'reportExtension')),
    query_keyword: $ => kw('query'),
    xmlport_keyword: $ => prec(10, choice('xmlport', 'XMLPORT', 'Xmlport', 'XMLport', 'XMLPort', 'XmlPort')),
    enum_keyword: $ => prec(10, choice('enum', 'ENUM', 'Enum', 'eNUM', 'eNum', 'ENum')),
    enumextension_keyword: $ => prec(10, choice('enumextension', 'ENUMEXTENSION', 'Enumextension', 'EnumExtension', 'enumExtension')),
    interface_keyword: $ => kw('interface'),
    controladdin_keyword: $ => prec(10, choice('controladdin', 'CONTROLADDIN', 'Controladdin', 'ControlAddIn', 'ControlAddin', 'controlAddIn', 'controlAddin')),
    dotnet_keyword: $ => prec(10, choice('dotnet', 'DOTNET', 'Dotnet', 'DotNet', 'dotNet')),
    profile_keyword: $ => kw('profile'),
    profileextension_keyword: $ => prec(10, choice('profileextension', 'PROFILEEXTENSION', 'Profileextension', 'ProfileExtension', 'profileExtension')),
    permissionset_keyword: $ => prec(10, choice('permissionset', 'PERMISSIONSET', 'Permissionset', 'PermissionSet', 'permissionSet')),
    permissionsetextension_keyword: $ => prec(10, choice('permissionsetextension', 'PERMISSIONSETEXTENSION', 'Permissionsetextension', 'PermissionSetExtension', 'permissionSetExtension')),
    entitlement_keyword: $ => kw('entitlement'),
    pagecustomization_keyword: $ => prec(10, choice('pagecustomization', 'PAGECUSTOMIZATION', 'Pagecustomization', 'PageCustomization', 'pageCustomization')),
    namespace_keyword: $ => kw('namespace'),
    using_keyword: $ => kw('using'),
    implements_keyword: $ => kw('implements'),
    extends_keyword: $ => kw('extends'),
    customizes_keyword: $ => kw('customizes'),

    // --- Tier 3: Declarations & modifiers ---

    procedure_keyword: $ => kw('procedure'),
    trigger_keyword: $ => kw('trigger'),
    var_keyword: $ => kw('var'),
    local_keyword: $ => kw('local'),
    internal_keyword: $ => kw('internal'),
    protected_keyword: $ => kw('protected'),
    event_keyword: $ => kw('event'),
    temporary_keyword: $ => kw('temporary'),

    // --- Tier 3: Sections ---

    fields_keyword: $ => kw('fields'),
    keys_keyword: $ => kw('keys'),
    key_keyword: $ => kw('key'),
    fieldgroups_keyword: $ => kw('fieldgroups'),
    fieldgroup_keyword: $ => kw('fieldgroup'),
    actions_keyword: $ => kw('actions'),
    layout_keyword: $ => kw('layout'),
    area_keyword: $ => kw('area'),
    group_keyword: $ => kw('group'),
    repeater_keyword: $ => kw('repeater'),
    cuegroup_keyword: $ => kw('cuegroup'),
    fixed_keyword: $ => kw('fixed'),
    grid_keyword: $ => kw('grid'),
    part_keyword: $ => kw('part'),
    systempart_keyword: $ => kw('systempart'),
    usercontrol_keyword: $ => kw('usercontrol'),
    chartpart_keyword: $ => kw('chartpart'),
    dataset_keyword: $ => kw('dataset'),
    elements_keyword: $ => kw('elements'),
    dataitem_keyword: $ => kw('dataitem'),
    column_keyword: $ => kw('column'),
    filter_keyword: $ => kw('filter'),
    labels_keyword: $ => kw('labels'),
    rendering_keyword: $ => kw('rendering'),
    requestpage_keyword: $ => kw('requestpage'),
    schema_keyword: $ => kw('schema'),
    views_keyword: $ => kw('views'),
    view_keyword: $ => kw('view'),

    // =====================================================================
    // Shared rules
    // =====================================================================

    _identifier_or_quoted: $ => choice(
      $.identifier,
      $.quoted_identifier,
      // Contextual keywords that can also be used as identifiers
      alias($.keyword_as_identifier, $.identifier),
    ),

    // Keywords that need to be usable as identifiers (variable names, parameter names, etc.)
    keyword_as_identifier: $ => prec(-10, choice(
      kw('field'),
      $.key_keyword,
      kw('value'),
      kw('separator'),
      $.dataset_keyword,
      kw('type'),
      kw('version'),
      kw('action'),
    )),

    // Identifiers — Unicode-aware
    identifier: $ => token(/[\p{L}_][\p{L}\p{N}_]*/u),

    quoted_identifier: $ => token(prec(10, seq(
      '"',
      repeat(choice(
        new RustRegex('[^"\\n]+'),
        '""'  // Escaped double quote
      )),
      '"'
    ))),

    // Comments (including XML doc comments /// ...)
    comment: $ => token(seq('//', /[^\n]*/)),
    multiline_comment: $ => token(seq('/*', /[^*]*\*+([^/*][^*]*\*+)*/, '/')),

    // Literals
    string_literal: $ => token(
      choice(
        seq("'", "'"),
        seq(
          "'",
          repeat1(choice(
            new RustRegex("[^'\\n]+"),
            "''"
          )),
          "'"
        )
      )
    ),

    integer: $ => token(/\d+/),
  },
});
