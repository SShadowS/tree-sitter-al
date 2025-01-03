/**
 * @file AL for Business Central
 * @author Torben Leth <sshadows@sshadows.dk>
 * @license MIT
 */

/// <reference types="tree-sitter-cli/dsl" />
// @ts-check

module.exports = grammar({
  name: "al",

  //word: $ => $.identifier,
  extras: $ => [/\s/],

  rules: {
    source_file: $ => repeat($._object),

    _object: $ => choice(
      $.table_declaration,
      $.codeunit_declaration
    ),

    _assignment_operator: $ => ':=',
    _double__colon: $ => token(prec(1, '::')),
    _colon: $ => ':',

    function_call: $ => seq(  // Increase precedence to 3
      field('function_name', $.identifier),
      field('arguments', optional($.argument_list))  // Make arguments optional
    ),

    object_id: $ => seq($.integer),
    object_name: $ => field('name', alias(choice(
      $.identifier,
      $._quoted_identifier
    ), $.name)),

    table_declaration: $ => seq(
      /[tT][aA][bB][lL][eE]/,
      field('object_id', $.object_id),
      field('object_name', $.object_name),
      '{',
      repeat($._table_element),
      '}'
    ),

    codeunit_declaration: $ => seq(
      /[cC][oO][dD][eE][uU][nN][iI][tT]/,
      field('object_id', $.object_id),
      field('object_name', $.object_name),
      '{',
      optional($.property_list),
      optional(repeat($._codeunit_element)),
      '}'
    ),

    // Property value types for specific properties
    table_no_value: $ => choice(
      $.integer,
      $.identifier
    ),

    subtype_value: $ => choice(
      'Install',
      'Upgrade',
      'Test'
    ),

    single_instance_value: $ => $.boolean,

    page_id_value: $ => choice(
      $.integer,
      $.identifier,
      prec(1, $._quoted_identifier)
    ),

    permissions_value: $ => $.tabledata_permission_list,

    field_class_value: $ => choice(
      /[fF][lL][oO][wW][fF][iI][eE][lL][dD]/,
      /[fF][lL][oO][wW][fF][iI][lL][tT][eE][rR]/,
      /[nN][oO][rR][mM][aA][lL]/
    ),

    calc_formula_value: $ => $._calc_formula_expression,

    blank_zero_value: $ => $.boolean,

    editable_value: $ => $.boolean,

    option_members_value: $ => choice(
      $.string_literal,
      seq(
        $.option_member,
        repeat(seq(',', $.option_member))
      )
    ),

    option_caption_value: $ => $.string_literal,

    table_type_value: $ => choice(
      /[nN][oO][rR][mM][aA][lL]/,
      /[tT][eE][mM][pP][oO][rR][aA][rR][yY]/,
      /[eE][xX][tT][eE][rR][nN][aA][lL]/,
      /[sS][yY][sS][tT][eE][mM]/
    ),

    table_type_property: $ => seq(
      'TableType',
      '=',
      $.table_type_value,
      ';'
    ),

    data_classification_value: $ => choice(
      /[cC][uU][sS][tT][oO][mM][eE][rR][cC][oO][nN][tT][eE][nN][tT]/,
      /[eE][nN][dD][uU][sS][eE][rR][iI][dD][eE][nN][tT][iI][fF][iI][aA][bB][lL][eE][iI][nN][fF][oO][rR][mM][aA][tT][iI][oO][nN]/,
      /[aA][cC][cC][oO][uU][nN][tT][dD][aA][tT][aA]/,
      /[eE][nN][dD][uU][sS][eE][rR][pP][sS][eE][uU][dD][oO][nN][yY][mM][oO][uU][sS][iI][dD][eE][nN][tT][iI][fF][iI][eE][rR][sS]/,
      /[oO][rR][gG][aA][nN][iI][zZ][aA][tT][iI][oO][nN][iI][dD][eE][nN][tT][iI][fF][iI][aA][bB][lL][eE][iI][nN][fF][oO][rR][mM][aA][tT][iI][oO][nN]/,
      /[sS][yY][sS][tT][eE][mM][mM][eE][tT][aA][dD][aA][tT][aA]/,
      /[tT][oO][bB][eE][cC][lL][aA][sS][sS][iI][fF][iI][eE][dD]/
    ),

    _codeunit_element: $ => prec(1, choice(
      $.procedure,
      $.onrun_trigger,
      $.var_section
    )),

    onrun_trigger: $ => seq(
      choice('trigger', 'TRIGGER', 'Trigger'),
      choice('OnRun', 'ONRUN', 'Onrun'),
      '()',
      $.code_block
    ),


    _table_element: $ => prec(1, choice(
      $.fields,  // Fields section should be primary
      $.oninsert_trigger,
      $.onmodify_trigger,
      $.ondelete_trigger,
      $.onrename_trigger,
      $.onvalidate_trigger,
      $.onaftergetrecord_trigger,
      $.onafterinsertevent_trigger,
      $.onaftermodifyevent_trigger,
      $.onafterdeleteevent_trigger,
      $.onbeforeinsertevent_trigger,
      $.onbeforemodifyevent_trigger,
      $.onbeforedeleteevent_trigger,
      $.keys,
      $.procedure,
      $.caption_property,
      $.data_classification_property,
      $.var_section,
      $.permissions_property,
      $.drilldown_pageid_property,
      $.lookup_pageid_property,
      $.table_type_property
    )),

    // For single table permission property
    permissions_property: $ => seq(
      'Permissions',
      '=',
      $.tabledata_permission_list,
      ';'
    ),

    permission_type: $ => token(
      prec(-1, /[rRiImMdDxX]+/)
    ),


    oninsert_trigger: $ => seq(
      choice('trigger', 'TRIGGER', 'Trigger'),
      choice('OnInsert', 'ONINSERT', 'Oninsert'),
      '()',
      $.code_block
    ),

    onmodify_trigger: $ => seq(
      choice('trigger', 'TRIGGER', 'Trigger'),
      choice('OnModify', 'ONMODIFY', 'Onmodify'),
      '()',
      $.code_block
    ),

    ondelete_trigger: $ => seq(
      choice('trigger', 'TRIGGER', 'Trigger'),
      choice('OnDelete', 'ONDELETE', 'Ondelete'),
      '()',
      $.code_block
    ),

    onrename_trigger: $ => seq(
      choice('trigger', 'TRIGGER', 'Trigger'),
      choice('OnRename', 'ONRENAME', 'Onrename'),
      '()',
      $.code_block
    ),

    onvalidate_trigger: $ => seq(
      choice('trigger', 'TRIGGER', 'Trigger'),
      choice('OnValidate', 'ONVALIDATE', 'Onvalidate'),
      '()',
      $.code_block
    ),

    onaftergetrecord_trigger: $ => seq(
      choice('trigger', 'TRIGGER', 'Trigger'),
      choice('OnAfterGetRecord', 'ONAFTERGETRECORD', 'Onaftergetrecord'),
      '()',
      $.code_block
    ),

    onafterinsertevent_trigger: $ => seq(
      choice('trigger', 'TRIGGER', 'Trigger'),
      choice('OnAfterInsertEvent', 'ONAFTERINSERTEVENT', 'Onafterinsertevent'),
      '()',
      $.code_block
    ),

    onaftermodifyevent_trigger: $ => seq(
      choice('trigger', 'TRIGGER', 'Trigger'),
      choice('OnAfterModifyEvent', 'ONAFTERMODIFYEVENT', 'Onaftermodifyevent'),
      '()',
      $.code_block
    ),

    onafterdeleteevent_trigger: $ => seq(
      choice('trigger', 'TRIGGER', 'Trigger'),
      choice('OnAfterDeleteEvent', 'ONAFTERDELETEEVENT', 'Onafterdeleteevent'),
      '()',
      $.code_block
    ),

    onbeforeinsertevent_trigger: $ => seq(
      'trigger',
      'OnBeforeInsertEvent',
      '()',
      $.code_block
    ),

    onbeforemodifyevent_trigger: $ => seq(
      'trigger',
      'OnBeforeModifyEvent',
      '()',
      $.code_block
    ),

    onbeforedeleteevent_trigger: $ => seq(
      'trigger',
      'OnBeforeDeleteEvent',
      '()',
      $.code_block
    ),
    
    member: $ => choice(
      $.identifier,
      $._quoted_identifier
    ),

    member_access: $ => prec.left(4, seq(
      field('object', choice(
        $._primary_expression,
        $.member_access
      )),
      field('operator', '.'),
      field('member', $.member)
    )),

    method_call: $ => prec.left(5, seq(
      field('object', $._primary_expression),
      field('operator', '.'),
      field('method', alias(choice($.identifier, $._quoted_identifier), $.method_name)),
      field('arguments', $.argument_list)
    )),

    property_list: $ => prec(3, repeat1($.property)),

    property: $ => choice(
      seq(
        field('property_name', 'TableNo'),
        '=',
        field('property_value', $.table_no_value),
        ';'
      ),
      seq(
        field('property_name', 'Subtype'),
        '=', 
        field('property_value', $.subtype_value),
        ';'
      ),
      seq(
        field('property_name', 'SingleInstance'),
        '=',
        field('property_value', $.single_instance_value),
        ';'
      ),
      seq(
        field('property_name', choice('DrillDownPageId', 'LookupPageId')),
        '=',
        field('property_value', $.page_id_value),
        ';'
      ),
      seq(
        field('property_name', 'Permissions'),
        '=',
        field('property_value', $.permissions_value),
        ';'
      ),
      seq(
        field('property_name', 'TableRelation'),
        '=',
        field('property_value', $.table_relation_expression),
        ';'
      ),
      seq(
        field('property_name', 'FieldClass'),
        '=',
        field('property_value', $.field_class_value),
        ';'
      ),
      seq(
        field('property_name', 'CalcFormula'),
        '=',
        field('property_value', $.calc_formula_value),
        ';'
      ),
      seq(
        field('property_name', 'BlankZero'),
        '=',
        field('property_value', $.blank_zero_value),
        ';'
      ),
      seq(
        field('property_name', 'Editable'),
        '=',
        field('property_value', $.editable_value),
        ';'
      ),
      seq(
        field('property_name', 'OptionMembers'),
        '=',
        field('property_value', $.option_members_value),
        ';'
      ),
      seq(
        field('property_name', 'OptionCaption'),
        '=',
        field('property_value', $.option_caption_value),
        ';'
      ),
      seq(
        field('property_name', 'DataClassification'),
        '=',
        field('property_value', $.data_classification_value),
        ';'
      )
    ),

    caption_property: $ => seq(
      'Caption',
      '=',
      $.string_literal,
      ';'
    ),

    data_classification_property: $ => seq(
      'DataClassification',
      '=',
      $.data_classification_value,
      ';'
    ),


    tabledata_permission_list: $ => seq(
      $.tabledata_permission,
      optional(seq(',', $.tabledata_permission))
    ),

    tabledata_permission: $ => seq(
      'tabledata', 
      field('table_name', $._table_identifier),
      '=',
      field('permission', $.permission_type)
    ),

    _table_identifier: $ => choice(
      $.identifier,
      $._quoted_identifier
    ),

    drilldown_pageid_property: $ => seq(
      'DrillDownPageId',
      '=',
      choice($.identifier, $._quoted_identifier, $.integer),
      ';'
    ),

    lookup_pageid_property: $ => seq(
      'LookupPageId',
      '=',
      choice($.identifier, $._quoted_identifier, $.integer),
      ';'
    ),

    decimal_places_property: $ => seq(
      'DecimalPlaces',
      '=',
      field('precision', $.integer),
      ':',
      field('scale', $.integer),
      ';'
    ),

    var_section: $ => seq(
      choice('var', 'VAR', 'Var'),
      repeat1($.variable_declaration)
    ),

    variable_declaration: $ => seq(
      field('name', $.identifier),
      ':',
      field('type', $.type_specification),
      optional(field('temporary', $.temporary)),
      ';'
    ),

    type_specification: $ => choice(
      $.array_type,
      $.basic_type,
      $.text_type,
      $.record_type,
      $.codeunit_type, 
      $.query_type,
      $.dotnet_type,
      $.list_type,
      $.dictionary_type,
      $.custom_data_type
    ),

    list_type: $ => seq(
      'List', 
      'of', 
      '[', 
      $.type_specification, 
      ']'
    ),

    dictionary_type: $ => seq(
      'Dictionary', 
      'of', 
      '[', 
      $.type_specification, 
      ',', 
      $.type_specification, 
      ']'
    ),

    basic_type: $ => choice(
      // Numeric Types
      choice('Integer', 'INTEGER', 'Integer'),
      choice('Decimal', 'DECIMAL', 'Decimal'),
      choice('Byte', 'BYTE', 'Byte'),
      
      // Text Types
      choice('Char', 'CHAR', 'Char'),
      
      // Date/Time Types
      choice('Date', 'DATE', 'Date'),
      choice('Time', 'TIME', 'Time'),
      choice('DateTime', 'DATETIME', 'Datetime'),
      choice('Duration', 'DURATION', 'Duration'),
      choice('DateFormula', 'DATEFORMULA', 'Dateformula'),
      
      // Other Types
      choice('Boolean', 'BOOLEAN', 'Boolean'),
      choice('Option', 'OPTION', 'Option'),
      choice('Guid', 'GUID', 'Guid'),
      choice('RecordId', 'RECORDID', 'Recordid'),
      choice('Variant', 'VARIANT', 'Variant'),
      choice('Dialog', 'DIALOG', 'Dialog'),
      choice('Action', 'ACTION', 'Action'),
      choice('BLOB', 'Blob', 'blob'),
      choice('FilterPageBuilder', 'FILTERPAGEBUILDER', 'Filterpagebuilder'),
      choice('JsonToken', 'JSONTOKEN', 'Jsontoken'),
      choice('JsonValue', 'JSONVALUE', 'Jsonvalue'),
      choice('JsonArray', 'JSONARRAY', 'Jsonarray'),
      choice('JsonObject', 'JSONOBJECT', 'Jsonobject'),
      choice('Media', 'MEDIA', 'Media'),
      choice('MediaSet', 'MEDIASET', 'Mediaset'),
      choice('OStream', 'OSTREAM', 'Ostream'),
      choice('InStream', 'INSTREAM', 'Instream'),
      choice('OutStream', 'OUTSTREAM', 'Outstream'),
      choice('SecretText', 'SECRETTEXT', 'Secrettext'),
      choice('Label', 'LABEL', 'Label')
    ),

    text_type: $ => seq(
      'Text',
      optional(seq(
        '[',
        field('length', $.integer),
        ']'
      ))
    ),

    code_type: $ => seq(
      'Code',
      optional(seq(
        '[',
        field('length', $.integer),
        ']'
      ))
    ),

    record_type: $ => prec.right(seq(
      'Record',
      field('reference', $._table_reference),
      optional('Temporary')
    )),

    // Use existing _table_reference rule that already handles both plain and quoted identifiers 
    _table_reference: $ => choice(
      $.integer,
      $.identifier,
      $._quoted_identifier  // Already has precedence 2
    ),

    codeunit_type: $ => seq(
      'Codeunit',
      field('reference', choice(
        $.integer,
        $._quoted_identifier,
        $.identifier
      ))
    ),

    query_type: $ => seq(
      'Query',
      field('reference', $.query_type_value)
    ),

    query_type_value: $ => choice(
      $.integer,
      $._quoted_identifier,
      $.identifier
    ),

    dotnet_type: $ => seq(
      'DotNet',
      field('reference', $.identifier)
    ),

    array_type: $ => seq(
      'array',
      '[',
      field('size', $.integer),
      ']',
      'of',
      $.type_specification
    ),

    fields: $ => seq(
      choice('fields', 'FIELDS', 'Fields'),
      '{',
      repeat($.field_declaration),
      '}'
    ),

    field_declaration: $ => seq(
      'field',
      '(',
      field('id', $.integer),
      token(';'),  // Make semi_colon an explicit token
      field('name', alias(choice(
        $._quoted_identifier,
        $.identifier
      ), $.name)),
      token(';'),  // Make semi_colon an explicit token
      field('type', $.data_type),
      ')',
      optional(seq(
        '{',
        repeat(choice(
          $.caption_property,
          $.data_classification_property,
          $.decimal_places_property,
          $.field_trigger_declaration,
          $.table_relation_property,
          $.field_class_property,
          $.calc_formula_property,
          $.blank_zero_property,
          $.editable_property,
          $.option_members_property,
          $.option_caption_property
        )),
        '}'
      ))
    ),

    table_relation_property: $ => seq(
      'TableRelation',
      '=',
      field('relation', $.table_relation_expression),
      ';'
    ),

    table_relation_expression: $ => choice(
      $._simple_table_relation,
      $.if_table_relation
    ),

    if_table_relation: $ => prec.right(seq(
      choice('IF', 'if', 'If'),
      '(',
      field('condition', $.table_filter),
      ')',
      field('then_relation', $._table_reference),
      optional(seq(
        choice('ELSE', 'else', 'Else'),
        field('else_relation', $.table_relation_expression)
      ))
    )),

    _simple_table_relation: $ => seq(
      field('table', $._table_reference),
      optional(seq($._double__colon, field('field', $._field_reference))),
      optional($.where_clause)
    ),



    table_filter: $ => choice(
      seq(
        field('filter_field', $._field_reference),
        '=',
        choice('CONST', 'const', 'Const'),
        '(',
        field('const_value', choice(
          $.string_literal,
          $.identifier,
          $._quoted_identifier,
          $.integer
        )),
        ')'
      ),
      seq(
        field('filter_field', $._field_reference),
        '=',
        choice('FIELD', 'field', 'Field'),
        '(',
        field('source_field', $._field_reference),
        ')'
      ),
      seq(
        field('filter_field', $._field_reference),
        '=',
        field('value', $.field_ref)
      )
    ),

    field_ref: $ => prec(2, seq(
      choice('field', 'FIELD', 'Field'),
      '(',
      field('referenced_field', $._field_reference),
      ')'
    )),

    where_clause: $ => seq(
      choice('where', 'WHERE', 'Where'),
      '(',
      field('conditions', $.where_conditions),
      ')'
    ),

    where_conditions: $ => seq(
      $.where_condition,
      repeat(seq(',', $.where_condition))
    ),

    where_condition: $ => seq(
      field('field', $._condition_field_reference),
      '=',
      field('value', $.field_ref)
    ),

    _field_reference: $ => choice(
      $._quoted_identifier,
      $.identifier
    ),

    _condition_field_reference: $ => alias(choice(
      $._quoted_identifier,
      $.identifier
    ), $.identifier),



    field_class_property: $ => seq(
      'FieldClass',
      '=',
      $.field_class_value,
      ';'
    ),

    calc_formula_property: $ => seq(
      'CalcFormula',
      '=',
      $._calc_formula_expression,
      ';'
    ),

    _calc_formula_expression: $ => choice(
      $.lookup_formula,
      $.count_formula,
      $.sum_formula, 
      $.average_formula,
      $.min_formula,
      $.max_formula
    ),

    lookup_formula: $ => seq(
      choice('lookup', 'LOOKUP', 'Lookup'),
      '(',
      field('target', $.field_reference),
      optional(seq(
        choice('where', 'WHERE', 'Where'),
        '(',
        $.lookup_where_conditions,
        ')'
      )),
      ')'
    ),

    lookup_where_conditions: $ => seq(
      $.lookup_where_condition,
      repeat(seq(',', $.lookup_where_condition))
    ),

    lookup_where_condition: $ => seq(
      field('field', $._condition_field_reference),
      '=',
      choice(
        seq(
          choice('field', 'FIELD', 'Field'),
          '(',
          field('value', alias(seq(
            $._condition_field_reference
          ), $.field_ref)),
          ')'
        ),
        seq(
          field('keyword', alias(choice('const', 'CONST', 'Const'), $.const)),
          '(',
          optional(field('value', $.string_literal)),
          ')'
        )
      )
    ),

    count_formula: $ => seq(
      choice('count', 'COUNT', 'Count'),
      '(',
      field('table', alias($._table_reference, $.table_reference)),
      optional($.where_clause),
      ')'
    ),

    sum_formula: $ => seq(
      choice('sum', 'SUM', 'Sum'),
      '(',
      field('target', $.field_reference),
      optional($.where_clause),
      ')'
    ),

    average_formula: $ => seq(
      choice('average', 'AVERAGE', 'Average'),
      '(',
      field('target', $.field_reference),
      optional($.where_clause),
      ')'
    ),

    min_formula: $ => seq(
      choice('min', 'MIN', 'Min'),
      '(',
      field('target', $.field_reference),
      optional($.where_clause),
      ')'
    ),

    max_formula: $ => seq(
      choice('max', 'MAX', 'Max'),
      '(',
      field('target', $.field_reference),
      optional($.where_clause),
      ')'
    ),

    field_reference: $ => seq(
      field('table', choice(
        alias($._quoted_identifier, $.table),
        alias($.identifier, $.table)
      )),
      '.',
      field('field', choice(
        alias($._quoted_identifier, $.field),
        alias($.identifier, $.field)
      ))
    ),






    blank_zero_property: $ => seq(
      'BlankZero',
      '=',
      $.blank_zero_value,
      ';'
    ),

    editable_property: $ => seq(
      'Editable',
      '=',
      $.editable_value,
      ';'
    ),

    option_members_property: $ => prec(1, seq(
      'OptionMembers',
      '=',
      choice(
        $.string_literal,  // Single string literal case
        seq(               // Multiple identifiers case
          $.option_member,
          repeat(seq(',', $.option_member))
        )
      ),
      ';'
    )),

    // New rule for option members
    option_member: $ => choice(
      $.identifier,
      $._quoted_identifier
    ),

    option_caption_property: $ => seq(
      'OptionCaption',
      '=',
      $.option_caption_value,
      ';'
    ),

    field_trigger_declaration: $ => seq(
      choice('trigger', 'TRIGGER', 'Trigger'),
      field('type', alias(choice(
        choice('OnValidate', 'ONVALIDATE', 'Onvalidate'),
        choice('OnLookup', 'ONLOOKUP', 'Onlookup'),
        choice('OnAssistEdit', 'ONASSISTEDIT', 'OnAssistEdit'),
        choice('OnDrillDown', 'ONDRILLDOWN', 'OnDrillDown')
      ), $.trigger_type)),
      '()',
      $.code_block
    ),

    keys: $ => seq(
      choice('keys', 'KEYS', 'Keys'),
      '{',
      repeat($.key_declaration),
      '}'
    ),

    key_declaration: $ => seq(
      'key',
      '(',
      field('name', alias($.identifier, $.name)),
      ';',
      field('fields', $.key_field_list),
      ')',
      optional(seq(
        '{',
        repeat(choice(
          $.clustered_property,
          $.property
        )),
        '}'
      ))
    ),

    key_field: $ => choice($._quoted_identifier, $.identifier),

    key_field_list: $ => seq(
      $.key_field,
      repeat(seq(',', $.key_field))
    ),

    attribute_list: $ => repeat1($.attribute),

    attribute: $ => seq(
      '[', 
      field('attribute_name', $.identifier), 
      optional($.attribute_arguments), 
      ']'
    ),

    attribute_arguments: $ => seq(
      '(', 
      field('arguments', $.expression_list), 
      ')'
    ),

    expression_list: $ => seq(
      $._expression,
      repeat(seq(',', $._expression))
    ),

    return_value: $ => field('return_value', $.identifier),

    _procedure_return_specification: $ => seq(
      optional($.return_value),
      ':',
      field('return_type', $.return_type)
    ),

    return_type: $ => choice(
      $.array_type,
      $.basic_type,
      $.text_type,
      $.record_type,
      $.codeunit_type,
      $.query_type,
      $.dotnet_type,
      $.list_type,
      $.dictionary_type,
      $.identifier  // Ensures custom types are recognized
    ),

    _procedure_name: $ => alias($.identifier, $.name),

    procedure_modifier: $ => choice('local', 'LOCAL', 'Local'),

    procedure: $ => seq(
      optional($.attribute_list),
      optional(field('modifier', $.procedure_modifier)), 
      choice('procedure', 'PROCEDURE', 'Procedure'),
      field('name', $._procedure_name),
      '(',
      optional($.parameter_list),
      ')',
      optional(';'),
      optional($._procedure_return_specification),
      optional($.var_section),
      $.code_block
    ),

    comparison_operator: $ => choice(
      '<>',
      '='
    ),

    arithmetic_operator: $ => choice(
      '+',
      '-',
      '*',
      '/'
    ),


    parameter_list: $ => seq(
      $.parameter,
      repeat(seq(';', $.parameter))
    ),

    modifier: $ => choice('var', 'VAR', 'Var'),

    parameter: $ => seq(
      optional(field('modifier', $.modifier)),
      field('parameter_name', alias($.identifier, $.name)),
      ':',
      field('parameter_type', choice(
        alias($.basic_type, $.type),
        alias($.text_type, $.type),
        alias($.code_type, $.type),
        alias($.record_type, $.type),
        alias($.array_type, $.type),
        alias($.identifier, $.type)
      ))
    ),

    identifier: $ => /[A-Za-z_][A-Za-z0-9_]*/,

    _quoted_identifier: $ => seq(
      '"',
      repeat1(choice(
        /[^":\n\\]/,  // Any character except quote, colon, newline or backslash
        /\\[\\'"]/,   // Escaped quotes or backslashes
        /\./,         // Allow dots in quoted identifiers
        /-/,          // Add hyphen support explicitly
        /\s/          // Allow spaces in quoted identifiers
      )),
      '"'
    ),

    integer: $ => /\d+/,


    string_literal: $ => token(seq(
      "'",
      repeat(choice(
        /[^'\\]/,      // Any char except quote or backslash
        /\\[\\'"]/     // Escaped quotes or backslashes
      )),
      "'"
    )),

    clustered_property: $ => seq(
      'Clustered',
      '=',
      field('value', $.boolean),
      ';'
    ),

    // Define boolean literals as tokens with precedence
    boolean: $ => choice(
      token(prec(1, 'true')),
      token(prec(1, 'false'))
    ),

    temporary: $ => choice('temporary', 'TEMPORARY', 'Temporary'),

    data_type: $ => choice(
      /[iI][nN][tT][eE][gG][eE][rR]/,
      /[tT][eE][xX][tT]/,
      /[dD][eE][cC][iI][mM][aA][lL]/,
      /[bB][oO][oO][lL][eE][aA][nN]/,
      /[oO][pP][tT][iI][oO][nN]/,
      /[rR][eE][cC][oO][rR][dD][iI][dD]/,
      /[dD][aA][tT][eE][tT][iI][mM][eE]/,
      /[dD][aA][tT][eE]/,
      /[tT][iI][mM][eE]/,
      /[bB][lL][oO][bB]/,
      /[dD][uU][rR][aA][tT][iI][oO][nN]/,
      /[bB][iI][gG][iI][nN][tT][eE][gG][eE][rR]/,
      /[gG][uU][iI][dD]/,
      seq(/[cC][oO][dD][eE]/, '[', field('size', $.integer), ']'),
      seq(/[tT][eE][xX][tT]/, '[', field('size', $.integer), ']'),
      seq(/[eE][nN][uU][mM]/, field('enum_type', $.identifier))
    ),

    custom_data_type: $ => seq(
      field('base_type', $.identifier),
      optional(seq(
        '[',
        field('size', $.integer),
        optional(seq(':', field('decimals', $.integer))),
        ']'
      ))
    ),

    // Define code blocks with explicit keyword handling
    code_block: $ => prec.right(1, seq(
      choice('begin', 'BEGIN', 'Begin'),
      optional(repeat($._statement)),
      choice('end', 'END', 'End'),
      optional(';')
    )),

    _statement: $ => prec.right(seq(
      choice(
        $.assignment_statement,
        $.if_statement,
        $.repeat_statement,
        $.case_statement,
        $.exit_statement,
        $.procedure_call,
        $.get_statement,
        $.find_set_statement,
        $.find_first_statement,
        $.find_last_statement,
        $.next_statement,
        $.insert_statement,
        $.modify_statement,
        $.delete_statement,
        $.set_range_statement,
        $.set_filter_statement,
        $.reset_statement
      ),
      optional(';')
    )),


    repeat_statement: $ => seq(
      choice('repeat', 'REPEAT', 'Repeat'),
      repeat1($._statement),
      choice('until', 'UNTIL', 'Until'),
      field('condition', $._expression)
    ),

    assignment_statement: $ => seq(
      field('left', $._assignable_expression),    // Can never be function call in AL
      field('operator', $._assignment_operator),  // Is defined as a token
      field('right', $._expression)               // Can be alot, but also contains a builtin function called Count
    ),

    assignable_member_access: $ => prec.left(4, seq(
      field('object', choice(
        $.identifier,
        $._quoted_identifier,
        $.assignable_member_access
      )),
      field('operator', '.'),
      field('member', $.member)
    )),

    _assignable_expression: $ => choice(
      $.identifier,
      alias($._quoted_identifier, $.quoted_identifier),
      $.assignable_member_access
    ),

    argument_list: $ => prec(2, seq(
      '(',
      optional(seq(
        $._argument,
        repeat(seq(',', $._argument))
      )),
      ')'
    )),

    _argument: $ => choice(
      $._literal_argument,
      $._expression
    ),

    _literal_argument: $ => prec(1, choice(
      alias($._quoted_identifier, $.quoted_identifier),
      $.string_literal,
      $.integer,
      $.boolean
    )),

    // Adjusting the _primary_expression to have clear precedence
    _primary_expression: $ => prec(1, choice(  // Lowered precedence to 1
      $._literal_argument,
      $.identifier,
      seq('(', $._expression, ')'),
      $.built_in_function
    )),

    built_in_function: $ => choice(
      // Date/Time Functions
      $.currentdatetime_function,
      $.currentdate_function,
      $.currenttime_function,
      $.today_function,
      $.workdate_function,
      $.createdatetime_function,
      $.time_function,

      // System Functions
      $.userid_function,
      $.companyname_function,
      $.serialnumber_function,
      $.sessionid_function,
      $.windowsloggedonuser_function,

      // Math Functions
      $.random_function,
      $.randomize_function,
      $.round_function,
      $.abs_function,
      $.power_function,

      // Database Functions
      $.count_function,
      $.getrangemin_function,
      $.getrangemax_function,
      $.getfilters_function,

      // String Functions
      $.strlen_function,
      $.copystr_function,
      $.lowercase_function,
      $.uppercase_function,
      $.format_function
    ),

    // Date/Time Functions
    currentdatetime_function: $ => choice(
      'CURRENTDATETIME', 'CurrentDateTime', 'Currentdatetime'
    ),

    currentdate_function: $ => choice(
      'CURRENTDATE', 'CurrentDate', 'Currentdate'
    ),

    currenttime_function: $ => choice(
      'CURRENTTIME', 'CurrentTime', 'Currenttime'
    ),

    today_function: $ => choice(
      'TODAY', 'Today', 'today'
    ),

    workdate_function: $ => choice(
      'WORKDATE', 'WorkDate', 'Workdate'
    ),

    createdatetime_function: $ => seq(
      choice('CREATEDATETIME', 'CreateDateTime', 'Createdatetime'),
      '(',
      field('date', $._expression),
      ',',
      field('time', $._expression),
      ')'
    ),

    time_function: $ => seq(
      choice('TIME', 'Time', 'time'),
      '(',
      field('hours', $._expression),
      ',',
      field('minutes', $._expression),
      ',',
      field('seconds', $._expression),
      ')'
    ),

    // System Functions
    userid_function: $ => choice(
      'USERID', 'UserId', 'Userid'
    ),

    companyname_function: $ => choice(
      'COMPANYNAME', 'CompanyName', 'Companyname'
    ),

    serialnumber_function: $ => choice(
      'SERIALNUMBER', 'SerialNumber', 'Serialnumber'
    ),

    sessionid_function: $ => choice(
      'SESSIONID', 'SessionId', 'Sessionid'
    ),

    windowsloggedonuser_function: $ => choice(
      'WINDOWSLOGGEDONUSER', 'WindowsLoggedOnUser', 'Windowsloggedonuser'
    ),

    // Math Functions
    random_function: $ => seq(
      choice('RANDOM', 'Random', 'random'),
      '(',
      field('range', $._expression),
      ')'
    ),

    randomize_function: $ => prec.left(2, choice(
      // With parameters version (try this first)
      seq(
        choice('RANDOMIZE', 'Randomize', 'randomize'),
        '(',
        field('seed', $._expression),
        ')'
      ),
      // No parameters version (try this second)
      choice('RANDOMIZE', 'Randomize', 'randomize')
    )),

    round_function: $ => seq(
      choice('ROUND', 'Round', 'round'),
      '(',
      field('number', $._expression),
      optional(seq(
        ',',
        field('precision', $._expression)
      )),
      ')'
    ),

    abs_function: $ => seq(
      choice('ABS', 'Abs', 'abs'),
      '(',
      field('number', $._expression),
      ')'
    ),

    power_function: $ => seq(
      choice('POWER', 'Power', 'power'),
      '(',
      field('base', $._expression),
      ',',
      field('exponent', $._expression),
      ')'
    ),

    // Database Functions
    count_function: $ => seq(
      choice('COUNT', 'Count', 'count'),
      '(',
      field('record', $._expression),
      ')'
    ),

    getrangemin_function: $ => seq(
      choice('GETRANGEMIN', 'GetRangeMin', 'Getrangemin'),
      '(',
      field('field', $._expression),
      ')'
    ),

    getrangemax_function: $ => seq(
      choice('GETRANGEMAX', 'GetRangeMax', 'Getrangemax'),
      '(',
      field('field', $._expression),
      ')'
    ),

    getfilters_function: $ => seq(
      choice('GETFILTERS', 'GetFilters', 'Getfilters'),
      '(',
      field('record', $._expression),
      ')'
    ),

    // String Functions
    strlen_function: $ => seq(
      choice('STRLEN', 'StrLen', 'Strlen'),
      '(',
      field('string', $._expression),
      ')'
    ),

    copystr_function: $ => seq(
      choice('COPYSTR', 'CopyStr', 'Copystr'),
      '(',
      field('string', $._expression),
      ',',
      field('position', $._expression),
      optional(seq(',', field('length', $._expression))),
      ')'
    ),

    lowercase_function: $ => seq(
      choice('LOWERCASE', 'LowerCase', 'Lowercase'),
      '(',
      field('string', $._expression),
      ')'
    ),

    uppercase_function: $ => seq(
      choice('UPPERCASE', 'UpperCase', 'Uppercase'),
      '(',
      field('string', $._expression),
      ')'
    ),

    format_function: $ => seq(
      choice('FORMAT', 'Format', 'format'),
      '(',
      field('value', $._expression),
      optional(seq(',', field('format_number', $._expression))),
      ')'
    ),

    _base_expression: $ => choice(
      $._primary_expression,
      $._chained_expression
    ),

    _chained_expression: $ => choice(
      $.member_access,
      $.method_call,
      $.qualified_enum_value
    ),

    _expression: $ => choice(
      $._base_expression,
      prec.left(1, $.binary_expression)  // Binary expressions have lowest precedence
    ),


    procedure_call: $ => choice(
      // Simple procedure call without arguments
      prec(1, alias($.identifier, $.function_name)),
      // Function call with arguments
      prec(2, seq(
        field('function_name', alias($.identifier, $.function_name)),
        field('arguments', $.argument_list)
      )),
      // Method call
      $.method_call
    ),

    // Individual method definitions
    // Common base pattern for record operations
    _record_operation: $ => prec(3, seq(
      field('record', alias($.identifier, $.record)),
      '.'
    )),

    get_method: $ => seq(
      $._record_operation,
      'Get',
      field('arguments', $.argument_list)
    ),

    find_set_method: $ => prec(3, seq(
      field('record', alias($.identifier, $.record)),
      '.',
      'FindSet',
      '(',
      optional(seq(
        field('forward_order', $.boolean),
        optional(seq(',', field('lock_record', $.boolean)))
      )),
      ')'
    )),

    insert_statement: $ => seq(
      $._record_operation,
      'Insert',
      '(',
      optional(seq(
        field('run_trigger', $.boolean),
        optional(seq(',', field('system_id', $.boolean)))
      )),
      ')'
    ),

    modify_statement: $ => seq(
      $._record_operation,
      'Modify',
      '(',
      optional(field('run_trigger', $.boolean)),
      ')'
    ),

    delete_statement: $ => seq(
      $._record_operation,
      'Delete',
      '(',
      optional(field('run_trigger', $.boolean)),
      ')'
    ),

    set_range_statement: $ => seq(
      $._record_operation,
      'SetRange',
      '(',
      field('field_name', choice($.identifier, $._quoted_identifier)),
      ',',
      field('from_value', choice($.string_literal, $.identifier, $.integer)),
      optional(seq(
        ',',
        field('to_value', choice($.string_literal, $.identifier, $.integer))
      )),
      ')'
    ),

    set_filter_statement: $ => seq(
      $._record_operation,
      'SetFilter',
      '(',
      field('field_name', choice($.identifier, $._quoted_identifier)),
      ',',
      field('filter_expression', $.string_literal),
      repeat(
        seq(
          ',',
          field('parameter', $._expression)
        )
      ),
      ')'
    ),

    reset_statement: $ => seq(
      $._record_operation,
      'Reset',
      '(',
      ')'
    ),

    binary_expression: $ => choice(
      // Comparison has higher precedence than arithmetic
      prec.left(6, seq(
        field('left', $._base_expression),
        field('operator', $.comparison_operator), 
        field('right', $._base_expression)
      )),
      prec.left(4, seq(
        field('left', $._base_expression),
        field('operator', $.arithmetic_operator),
        field('right', $._base_expression)
      ))
    ),

    if_statement: $ => prec.right(seq(
      choice('if', 'IF', 'If'),
      field('condition', $._expression),
      choice('then', 'THEN', 'Then'),
      field('then_branch', choice(
        $._statement,
        $.code_block
      )),
      optional(seq(
        choice('else', 'ELSE', 'Else'),
        field('else_branch', choice(
          $._statement,
          $.code_block
        ))
      ))
    )),

    get_statement: $ => seq(
      $.get_method
    ),

    find_set_statement: $ => seq(
      $.find_set_method
    ),

    find_first_statement: $ => seq(
      $._record_operation,
      'FindFirst',
      '(',
      ')'
    ),

    find_last_statement: $ => seq(
      $._record_operation,
      'FindLast',
      '(',
      ')'
    ),

    next_statement: $ => seq(
      $._record_operation,
      'Next',
      '(',
      optional(field('steps', $.integer)),
      ')'
    ),

    // New rule for case expressions with explicit handling of identifiers
    _case_expression: $ => prec(2, choice(
      $.member_access,
      $.qualified_enum_value,
      $.function_call,
      $.identifier
    )),

    case_statement: $ => prec(2, seq(
      choice('case', 'CASE', 'Case'),
      field('expression', $._case_expression),
      choice('of', 'OF', 'Of'),
      repeat1($.case_branch),
      optional($.else_branch),
      choice('end', 'END', 'End')
    )),

    case_branch: $ => seq(
      field('pattern', $._case_pattern),
      $._colon,
      field('statements', choice(
        $.code_block,
        $._statement
      ))
    ),

    _case_pattern: $ => prec(5, choice(  // Increased precedence to 5
      $._literal_value,
      $.qualified_enum_value,
      $.member_access,
      $.identifier,
      $._quoted_identifier,
      $.string_literal,
      $.function_call,
      seq(
        field('enum_type', $._enum_type_reference),
        field('operator', $._double__colon),
        field('value', $._enum_value_reference)
      ),
      $.multi_pattern,
      // Add explicit support for member access patterns
      seq(
        field('object', choice(
          $.identifier,
          $._quoted_identifier,
          $.member_access
        )),
        field('operator', '.'),
        field('member', choice(
          $.identifier,
          $._quoted_identifier
        ))
      )
    )),

    multi_pattern: $ => seq(
      $._single_pattern,
      repeat1(seq(',', $._single_pattern))
    ),

    _single_pattern: $ => choice(
      $._literal_value,
      $.qualified_enum_value,
      $.member_access,
      $.identifier,
      $._quoted_identifier
    ),


    _literal_value: $ => choice(
      $.integer,
      $.string_literal,
      $.boolean
    ),

    else_branch: $ => seq(
      'else',
      field('statements', $._branch_statements)
    ),

    qualified_enum_value: $ => prec.left(3, seq(
      field('enum_type', choice(
        $._enum_type_reference,
        $.identifier,
        $._quoted_identifier,
        $.member_access
      )),
      field('operator', $._double__colon),
      field('value', choice(
        $._enum_value_reference,
        $._quoted_identifier,
        $.identifier,
        $.string_literal,
        $.member_access
      ))
    )),

    _enum_type_reference: $ => prec.left(2, choice(
      $._quoted_identifier,
      $.identifier,
      $.member_access
    )),

    _enum_value_reference: $ => prec.left(2, choice(
      $._quoted_identifier,
      $.identifier,
      $.member_access,
      $.string_literal
    )),

    _branch_statements: $ => choice(
      $._statement,
      $.code_block
    ),

    exit_statement: $ => choice(
      prec(1, choice('exit', 'EXIT', 'Exit')),  // Simple exit has lower precedence
      prec(2, seq(      // Exit with expression has higher precedence
        choice('exit', 'EXIT', 'Exit'),
        '(',
        $._expression,
        ')'
      ))
    ),
  }
});
