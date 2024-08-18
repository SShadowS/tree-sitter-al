module.exports = grammar({
  name: 'al',

  rules: {
    source_file: $ => repeat($._definition),

    _definition: $ => choice(
      $.table,
      $.codeunit
    ),

    // Table Definition
    table: $ => seq(
      'table',
      field('table_id', $.integer),
      field('table_name', $.identifier),
      '{',
      repeat($._table_body_element),
      '}'
    ),

    _table_body_element: $ => choice(
      $.field,
      $.key,
      $.trigger,
      $.property
    ),

    field: $ => seq(
      'field',
      field('field_id', $.integer),
      field('field_name', $.identifier),
      field('data_type', $.data_type),
      '{',
      repeat($.property),
      '}'
    ),

    key: $ => seq(
      'keys',
      '{',
      repeat1($.key_item),
      '}'
    ),

    key_item: $ => seq(
      'key',
      field('fields', $.identifier_list),
      '{',
      repeat($.property),
      '}'
    ),

    trigger: $ => seq(
      'trigger',
      field('trigger_name', $.identifier),
      '{',
      repeat($.statement),
      '}'
    ),

    // Codeunit Definition
    codeunit: $ => seq(
      'codeunit',
      field('codeunit_id', $.integer),
      field('codeunit_name', $.identifier),
      '{',
      repeat($._codeunit_body_element),
      '}'
    ),

    _codeunit_body_element: $ => choice(
      $.procedure,
      $.trigger,
      $.property
    ),

    procedure: $ => seq(
      'procedure',
      field('procedure_name', $.identifier),
      '(',
      optional($.parameter_list),
      ')',
      '{',
      repeat($.statement),
      '}'
    ),

    parameter_list: $ => sepBy1(',', $.parameter),

    parameter: $ => seq(
      field('parameter_name', $.identifier),
      field('parameter_type', $.data_type)
    ),

    // Properties
    property: $ => seq(
      field('property_name', $.identifier),
      '=',
      field('property_value', $._property_value),
      ';'
    ),

    _property_value: $ => choice(
      $.string,
      $.integer,
      $.boolean,
      $.identifier
    ),

    // Statements
    statement: $ => choice(
      $.assignment_statement,
      $.if_statement,
      $.call_statement
    ),

    assignment_statement: $ => seq(
      field('left_hand_side', $.identifier),
      ':=',
      field('right_hand_side', $.expression),
      ';'
    ),

    if_statement: $ => seq(
      'if',
      '(',
      field('condition', $.expression),
      ')',
      'then',
      '{',
      repeat($.statement),
      '}',
      optional(seq(
        'else',
        '{',
        repeat($.statement),
        '}'
      ))
    ),

    call_statement: $ => seq(
      field('function_name', $.identifier),
      '(',
      optional($.argument_list),
      ')',
      ';'
    ),

    argument_list: $ => sepBy1(',', $.expression),

    // Expressions
    expression: $ => choice(
      $.identifier,
      $.integer,
      $.string,
      $.boolean
    ),

    identifier: $ => /[a-zA-Z_][a-zA-Z0-9_]*/,
    identifier_list: $ => sepBy1(',', $.identifier),

    data_type: $ => choice(
      'Integer',
      'Decimal',
      'Text',
      'Code',
      'Boolean',
      'Date',
      'Time',
      'DateTime',
      'Option',
      'Record',
      'Blob',
      'GUID'
    ),

    boolean: $ => choice(
      'true',
      'false'
    ),

    integer: $ => /\d+/,
    string: $ => /".*?"/
  }
});

// Helper function to handle repeated elements separated by a delimiter
function sepBy1(delimiter, rule) {
  return seq(rule, repeat(seq(delimiter, rule)));
}
