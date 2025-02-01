/**
 * @file AL for Business Central
 * @author Torben Leth <sshadows@sshadows.dk>
 * @license MIT
 */

/// <reference types="tree-sitter-cli/dsl" />
// @ts-check

module.exports = grammar({
  name: "al",

  word: $ => $.identifier,
  extras: $ => [/\s/],

  conflicts: $ => [
    [$.simple_field_ref, $._referenced_field]
  ],

  rules: {
    source_file: $ => repeat($._object),

    _object: $ => choice(
      $.table_declaration,
      $.codeunit_declaration
    ),

    _assignment_operator: $ => ':=',
    _double__colon: $ => token(prec(1, '::')),
    _colon: $ => ':',


    object_id: $ => seq($.integer),
    object_name: $ => field('name', choice(
      $._quoted_identifier,
      $.identifier
    )),

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
      /[iI][nN][sS][tT][aA][lL][lL]/,
      /[uU][pP][gG][rR][aA][dD][eE]/,
      /[tT][eE][sS][tT]/
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
      /[nN][oO][rR][mM][aA][lL]/,
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

    extended_datatype_value: $ => choice(
      /[pP][hH][oO][nN][eE][nN][oO]/,
      /[uU][rR][lL]/, 
      /[eE][mM][aA][iI][lL]/,
      /[rR][aA][tT][iI][oO]/,
      /[dD][uU][rR][aA][tT][iI][oO][nN]/,
      /[mM][aA][sS][kK][eE][dD]/
    ),

    table_type_value: $ => choice(
      /[nN][oO][rR][mM][aA][lL]/,
      /[tT][eE][mM][pP][oO][rR][aA][rR][yY]/,
      /[eE][xX][tT][eE][rR][nN][aA][lL]/,
      /[sS][yY][sS][tT][eE][mM]/
    ),

    closing_dates_value: $ => $.boolean,
    char_allowed_value: $ => $.boolean,
    compressed_value: $ => $.boolean,
    date_formula_value: $ => $.string_literal,
    description_value: $ => $.string_literal,
    external_access_value: $ => choice(
      /[eE][xX][tT][eE][rR][nN][aA][lL]/,
      /[iI][nN][tT][eE][rR][nN][aA][lL]/,
      /[lL][oO][cC][aA][lL]/
    ),
    external_name_value: $ => $.string_literal,
    external_type_value: $ => $.string_literal,
    init_value_value: $ => $._expression,
    max_value_value: $ => $._expression, 
    min_value_value: $ => $._expression,
    not_blank_value: $ => $.boolean,
    numeric_value: $ => $.boolean,
    obsolete_reason_value: $ => $.string_literal,
    obsolete_state_value: $ => choice(
      /[pP][eE][nN][dD][iI][nN][gG]/,
      /[rR][eE][mM][oO][vV][eE][dD]/
    ),
    obsolete_tag_value: $ => $.string_literal,
    option_ordinal_values_value: $ => $.string_literal,
    paste_is_valid_value: $ => $.boolean,
    sign_displacement_value: $ => $.boolean,
    sql_data_type_value: $ => $.string_literal,
    sql_timestamp_value: $ => $.boolean,
    test_table_relation_value: $ => $.boolean,
    tool_tip_value: $ => $.string_literal,
    unique_value: $ => $.boolean,
    validate_table_relation_value: $ => $.boolean,
    values_allowed_value: $ => seq(
      $.string_literal,
      repeat(seq(',', $.string_literal))
    ),

    access_value: $ => choice(
      /[pP][uU][bB][lL][iI][cC]/,
      /[iI][nN][tT][eE][rR][nN][aA][lL]/,
      /[pP][rR][iI][vV][aA][tT][eE]/
    ),

    access_by_permission_value: $ => seq(
      /[tT][aA][bB][lL][eE][dD][aA][tT][aA]/,
      field('table_name', $._table_reference),
      '=',
      field('permission', $.permission_type)
    ),

    auto_format_expression_value: $ => $.string_literal,

    auto_format_type_value: $ => choice(
      '0', // None
      '1', // Phone Number
      '2', // Currency
      '3', // Date
      '4', // Time
      '5', // Date and Time
      '6', // Amount
      '7', // Quantity
      '8', // Percentage
      '9', // Custom
      '10' // Custom with Format Expression
    ),

    auto_increment_value: $ => $.boolean,

    blank_numbers_value: $ => $.boolean,

    table_type_property: $ => seq(
      'TableType',
      '=',
      $.table_type_value,
      ';'
    ),

    access_by_permission_property: $ => seq(
      'AccessByPermission',
      '=',
      $.access_by_permission_value,
      ';'
    ),

    allow_in_customizations_property: $ => prec(1, seq(
      'AllowInCustomizations', 
      '=',
      $.boolean,
      ';'
    )),

    auto_format_expression_property: $ => seq(
      'AutoFormatExpression',
      '=',
      $.auto_format_expression_value,
      ';'
    ),

    auto_format_type_property: $ => seq(
      'AutoFormatType',
      '=',
      $.auto_format_type_value,
      ';'
    ),

    auto_increment_property: $ => seq(
      'AutoIncrement',
      '=',
      $.auto_increment_value,
      ';'
    ),

    blank_numbers_property: $ => seq(
      'BlankNumbers',
      '=',
      $.blank_numbers_value,
      ';'
    ),

    access_property: $ => seq(
      'Access',
      '=',
      $.access_value,
      ';'
    ),

    closing_dates_property: $ => seq(
      'ClosingDates',
      '=',
      $.closing_dates_value,
      ';'
    ),

    char_allowed_property: $ => seq(
      'CharAllowed',
      '=',
      $.char_allowed_value,
      ';'
    ),

    compressed_property: $ => seq(
      'Compressed', 
      '=',
      $.compressed_value,
      ';'
    ),

    date_formula_property: $ => seq(
      'DateFormula',
      '=',
      $.date_formula_value,
      ';'
    ),

    description_property: $ => seq(
      'Description',
      '=',
      $.description_value,
      ';'
    ),

    external_access_property: $ => seq(
      'ExternalAccess',
      '=',
      $.external_access_value,
      ';'
    ),

    external_name_property: $ => seq(
      'ExternalName',
      '=',
      $.external_name_value,
      ';'
    ),

    external_type_property: $ => seq(
      'ExternalType',
      '=',
      $.external_type_value,
      ';'
    ),

    init_value_property: $ => seq(
      'InitValue',
      '=',
      $.init_value_value,
      ';'
    ),

    max_value_property: $ => seq(
      'MaxValue',
      '=',
      $.max_value_value,
      ';'
    ),

    min_value_property: $ => seq(
      'MinValue',
      '=',
      $.min_value_value,
      ';'
    ),

    not_blank_property: $ => seq(
      'NotBlank',
      '=',
      $.not_blank_value,
      ';'
    ),

    numeric_property: $ => seq(
      'Numeric',
      '=',
      $.numeric_value,
      ';'
    ),

    obsolete_reason_property: $ => seq(
      'ObsoleteReason',
      '=',
      $.obsolete_reason_value,
      ';'
    ),

    obsolete_state_property: $ => seq(
      'ObsoleteState',
      '=',
      $.obsolete_state_value,
      ';'
    ),

    obsolete_tag_property: $ => seq(
      'ObsoleteTag',
      '=',
      $.obsolete_tag_value,
      ';'
    ),

    option_ordinal_values_property: $ => seq(
      'OptionOrdinalValues',
      '=',
      $.option_ordinal_values_value,
      ';'
    ),

    paste_is_valid_property: $ => seq(
      'PasteIsValid',
      '=',
      $.paste_is_valid_value,
      ';'
    ),

    sign_displacement_property: $ => seq(
      'SignDisplacement',
      '=',
      $.sign_displacement_value,
      ';'
    ),

    sql_data_type_property: $ => seq(
      'SqlDataType',
      '=',
      $.sql_data_type_value,
      ';'
    ),

    sql_timestamp_property: $ => seq(
      'SqlTimestamp',
      '=',
      $.sql_timestamp_value,
      ';'
    ),

    test_table_relation_property: $ => seq(
      'TestTableRelation',
      '=',
      $.test_table_relation_value,
      ';'
    ),

    tool_tip_property: $ => seq(
      'ToolTip',
      '=',
      $.tool_tip_value,
      ';'
    ),

    unique_property: $ => seq(
      'Unique',
      '=',
      $.unique_value,
      ';'
    ),

    validate_table_relation_property: $ => seq(
      'ValidateTableRelation',
      '=',
      $.validate_table_relation_value,
      ';'
    ),

    values_allowed_property: $ => seq(
      'ValuesAllowed',
      '=',
      $.values_allowed_value,
      ';'
    ),

    extended_datatype_property: $ => seq(
      'ExtendedDatatype',
      '=',
      $.extended_datatype_value,
      ';'
    ),

    caption_ml_property: $ => seq(
      'CaptionML',
      '=',
      $.ml_value_list,
      ';'
    ),

    option_caption_ml_property: $ => seq(
      'OptionCaptionML',
      '=',
      $.ml_value_list,
      ';'
    ),

    tool_tip_ml_property: $ => seq(
      'ToolTipML',
      '=',
      $.ml_value_list,
      ';'
    ),

    ml_value_list: $ => seq(
      '[',
      repeat1($.ml_value_pair),
      ']'
    ),

    ml_value_pair: $ => seq(
      field('language', $.identifier),
      '=',
      field('value', $.string_literal)
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
      $.table_type_property,
      $.access_property
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

    property_list: $ => prec(3, repeat1($.property)),

    property: $ => prec(2, choice(
      $.access_by_permission_property,
      $.allow_in_customizations_property,
      $.auto_format_expression_property,
      $.calc_fields_property,
      $.caption_class_property,
      seq(
        field('property_name', 'AutoFormatExpression'),
        '=',
        field('property_value', $.string_literal),
        ';'
      ),
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
      ),
      seq(
        field('property_name', 'ExtendedDatatype'),
        '=',
        field('property_value', $.identifier),
        ';'
      )
    )),

    caption_property: $ => seq(
      'Caption',
      '=',
      $.string_literal,
      ';'
    ),

    caption_class_property: $ => seq(
      'CaptionClass',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    calc_fields_property: $ => seq(
      'CalcFields',
      '=',
      field('fields', $.calc_fields_list),
      ';'
    ),

    calc_fields_list: $ => seq(
      $.calc_field,
      repeat(seq(',', $.calc_field))
    ),

    calc_field: $ => choice(
      $.identifier,
      $._quoted_identifier
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
      $.code_type,
      $.record_type,
      $.codeunit_type, 
      $.query_type,
      $.dotnet_type,
      $.list_type,
      $.dictionary_type
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

    field_declaration: $ => prec(2, seq(
      'field',
      '(',
      field('id', $.integer),
      token(';'),  // Make semi_colon an explicit token
      field('name', choice(
        $._quoted_identifier,
        $.identifier
      )),
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
          $.access_by_permission_property,
          $.allow_in_customizations_property,
          $.auto_format_expression_property,
          $.auto_format_type_property,
          $.auto_increment_property,
          $.blank_numbers_property,
          $.auto_format_expression_property,
          $.table_relation_property,
          $.field_class_property,
          $.calc_formula_property,
          $.blank_zero_property,
          $.editable_property,
          $.option_members_property,
          $.option_caption_property,
          $.closing_dates_property,
          $.char_allowed_property,
          $.compressed_property,
          $.date_formula_property,
          $.description_property,
          $.external_access_property,
          $.external_name_property,
          $.external_type_property,
          $.init_value_property,
          $.max_value_property,
          $.min_value_property,
          $.not_blank_property,
          $.numeric_property,
          $.obsolete_reason_property,
          $.obsolete_state_property,
          $.obsolete_tag_property,
          $.option_ordinal_values_property,
          $.paste_is_valid_property,
          $.sign_displacement_property,
          $.sql_data_type_property,
          $.sql_timestamp_property,
          $.test_table_relation_property,
          $.tool_tip_property,
          $.unique_property,
          $.validate_table_relation_property,
          $.values_allowed_property,
          $.extended_datatype_property,
          $.caption_ml_property,
          $.option_caption_ml_property,
          $.tool_tip_ml_property
        )),
        '}'
      ))
    )),

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
      field('condition', $.where_conditions),
      ')',
      field('then_relation', $._simple_table_relation),
      optional(seq(
        choice('ELSE', 'else', 'Else'),
        field('else_relation', $.table_relation_expression)
      ))
    )),

    _simple_table_relation: $ => seq(
      field('table', $._table_reference),
      optional(seq($._double__colon, field('field', $.field_ref))),
      optional($.where_clause)
    ),



    const_filter: $ => seq(
      field('field', $.field_ref),
      '=',
      choice('CONST', 'const', 'Const'),
      '(',
      optional(field('value', choice(
        $.string_literal,
        $.identifier,
        $._quoted_identifier,
        $.integer,
        $.boolean
      ))),
      ')'
    ),

    field_filter: $ => seq(
      field('field', $.field_ref),
      '=',
      choice('FIELD', 'field', 'Field'),
      '(',
      field('value', $.field_ref),
      ')'
    ),

    filter_condition: $ => seq(
      field('field', $.field_ref),
      '=',
      choice('FILTER', 'filter', 'Filter'),
      '(',
      field('value', $.filter_criteria),
      ')'
    ),

    where_condition: $ => choice(
      $.const_filter,
      $.field_filter,
      $.filter_condition
    ),

    where_conditions: $ => seq(
      $.where_condition,
      repeat(seq(',', $.where_condition))
    ),

    filter_criteria: $ => /[^)]+/,

    simple_field_ref: $ => alias($._chained_expression, $.field_ref),

    explicit_field_ref: $ => prec(12, seq(
      choice('field', 'FIELD', 'Field'),
      '(',
      field('field', $._chained_expression),
      ')'
    )),

    field_ref: $ => prec(2, choice(
      $.explicit_field_ref,
      $.simple_field_ref
    )),

    where_clause: $ => seq(
      choice('where', 'WHERE', 'Where'),
      '(',
      field('conditions', $.where_conditions),
      ')'
    ),


    field_class_property: $ => seq(
      'FieldClass',
      '=',
      optional('"'),
      $.field_class_value,
      optional('"'),
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
      field('field', $.field_ref),
      '=',
      choice(
        seq(
          choice('field', 'FIELD', 'Field'),
          '(',
          field('value', $.field_ref),
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

    field_reference: $ => $._chained_expression,

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
      optional($.var_section),
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

    key_field_list: $ => seq(
      choice($._quoted_identifier, $.identifier),
      repeat(seq(',', choice($._quoted_identifier, $.identifier)))
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

    _quoted_identifier: $ => alias(
      token(prec(2, seq('"', /[^"\n\\]+/, '"'))),
      $.quoted_identifier
    ),

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
      seq(/[cC][oO][dD][eE]/, '[', field('size', $.integer), ']'),
      seq(/[tT][eE][xX][tT]/, '[', field('size', $.integer), ']'),
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
      seq(/[eE][nN][uU][mM]/, field('enum_type', $.identifier))
    ),

    // Define code blocks with explicit keyword handling
    code_block: $ => prec.right(1, seq(
      choice('begin', 'BEGIN', 'Begin'),
      optional(repeat($._statement)),
      choice('end', 'END', 'End'),
      optional(token(';')) // Explicit token
    )),

    _statement: $ => prec.right(seq(
      choice(
        $.assignment_statement,
        $.procedure_call,
        $.if_statement,
        $.repeat_statement,
        $.case_statement
      ),
      optional(';')
    )),

    procedure_call: $ => prec.left(8, seq(
      field('function', choice(
        $.identifier,
        $.member_expression
      )),
      field('arguments', $.argument_list)
    )),


    repeat_statement: $ => seq(
      choice('repeat', 'REPEAT', 'Repeat'),
      repeat1($._statement),
      choice('until', 'UNTIL', 'Until'),
      field('condition', $._expression)
    ),

    assignment_statement: $ => seq(
      field('left', $._assignable_expression),
      field('operator', $._assignment_operator),
      field('right', $._expression)
    ),

    _assignable_expression: $ => $._expression,

    call_expression: $ => prec(11, seq(
      field('function', $._expression),
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

    _literal_argument: $ => prec(1, choice(
      alias($._quoted_identifier, $.quoted_identifier),
      $.string_literal,
      $.integer,
      $.decimal,
      $.boolean
    )),

    _primary_expression: $ => choice(
      $._literal_value,
      $.identifier,
      $.parenthesized_expression,
      $.unary_expression,
      $.call_expression,
      $.member_expression
    ),

    _base_expression: $ => prec(1, choice(
      $._primary_expression,
      $._chained_expression
    )),

    _chained_expression: $ => prec(3, choice(
      $.member_expression,
      $.call_expression,
      $.qualified_enum_value_tail,
      $._quoted_identifier
    )),


    qualified_enum_value_tail: $ => seq(
      '::',
      choice($.identifier, $._quoted_identifier)
    ),

    unary_expression: $ => prec.right(7, seq( // Keep at 7 but verify context
      '-',
      $._expression
    )),

    _expression: $ => choice(
      $.field_access,  // Check quoted first 
      $.member_expression, // Then regular members
      $.call_expression,
      $.identifier,
      $._literal_value,
      $.parenthesized_expression,
      $.unary_expression,
      $.binary_expression
    ),

    member_expression: $ => prec.left(8, seq( // Increased from 6 to 8
      field('object', $._expression),
      '.',
      field('property', $.identifier) // Only non-quoted identifiers
    )),

    field_access: $ => prec.left(11, seq( // Higher precedence than member_expression
      field('record', $._expression),
      '.',
      field('field', $._quoted_identifier)
    )),



    // Individual method definitions
    // Common base pattern for record operations
    _record_operation: $ => prec(3, seq(
      field('record', alias($.identifier, $.record)),
      '.'
    )),

    binary_expression: $ => choice(
      prec.left(6, seq(
        field('left', $._expression),
        field('operator', $.comparison_operator),
        field('right', $._expression)
      )),
      prec.left(4, seq(
        field('left', $._expression),
        field('operator', $.arithmetic_operator),
        field('right', $._expression)
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

    // New rule for case expressions with explicit handling of identifiers
    _case_expression: $ => prec(10, choice(
      $.call_expression,
      $._expression
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

    _case_pattern: $ => prec(5, choice(
      $._literal_value,
      $.qualified_enum_value,
      $._chained_expression,
      $.identifier,
      $._quoted_identifier,
      $.string_literal,
      $.call_expression,
      seq(
        field('enum_type', $._enum_type_reference),
        field('operator', $._double__colon),
        field('value', $._enum_value_reference)
      ),
      $.multi_pattern
    )),

    multi_pattern: $ => seq(
      $._single_pattern,
      repeat1(seq(',', $._single_pattern))
    ),

    _single_pattern: $ => choice(
      $._literal_value,
      $.qualified_enum_value,
      $._chained_expression,
      $.identifier,
      $._quoted_identifier
    ),


    decimal: $ => token(seq(
      optional('-'),  // Only allow negative sign
      seq(/\d+/, '.', /\d+/)
    )),

    integer: $ => token(seq(
      optional('-'),  // Only allow negative sign
      /\d+/
    )),

    _literal_value: $ => choice(
      $.integer,
      $.decimal,
      $.string_literal,
      $.boolean
    ),

    parenthesized_expression: $ => seq(
      '(',
      $._expression,
      ')'
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
        $._chained_expression
      )),
      field('operator', $._double__colon),
      field('value', choice(
        $._enum_value_reference,
        $._quoted_identifier,
        $.identifier,
        $.string_literal,
        $._chained_expression
      ))
    )),

    _enum_type_reference: $ => prec.left(2, choice(
      $._quoted_identifier,
      $.identifier,
      $._chained_expression
    )),

    _enum_value_reference: $ => prec.left(2, choice(
      $._quoted_identifier,
      $.identifier,
      $._chained_expression,
      $.string_literal
    )),

    _branch_statements: $ => choice(
      $._statement,
      $.code_block
    ),

  },

});
