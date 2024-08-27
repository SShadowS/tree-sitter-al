module.exports = grammar({
  name: 'al',

  rules: {
    source_file: $ => repeat($._declaration),

    _declaration: $ => choice(
      $.table_definition
      // Other object types can be added here in the future
    ),

    table_definition: $ => seq(
      'table',
      field('id', $.object_id),
      field('name', $.object_name),
      '{',
      repeat($._table_element),
      '}'
    ),

    _table_element: $ => choice(
      $.caption_property,
      $.property,
      $.field_definition,
      $.key_definition,
      $.variable_declaration,
      $.trigger_definition,
      $.procedure_definition
      // Other table elements can be added here
    ),

    caption_property: $ => seq(
      'Caption',
      '=',
      field('value', $.string),
      ';'
    ),

    property: $ => seq(
      field('name', $.property_name),
      '=',
      field('value', $.property_value),
      ';'
    ),

    field_definition: $ => prec.right(1, seq(
      'field',
      '(',
      field('id', $.field_id),
      ';',
      field('name', $.field_name),
      ')',
      field('type', $.field_type),
      ';',
      repeat(choice($.caption_property, $.property))
    )),

    key_definition: $ => seq(
      'key',
      '(',
      repeat1($.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    variable_declaration: $ => seq(
      'var',
      field('name', $.identifier),
      ':',
      field('type', $.type),
      ';'
    ),

    trigger_definition: $ => seq(
      'trigger',
      field('name', $.trigger_name),
      '()',
      $.procedure_body
    ),

    procedure_definition: $ => seq(
      'procedure',
      field('name', $.procedure_name),
      '(',
      optional($.parameter_list),
      ')',
      optional(seq(':', $.type)),
      $.procedure_body
    ),

    parameter_list: $ => seq(
      $.parameter,
      repeat(seq(';', $.parameter))
    ),

    parameter: $ => seq(
      field('name', $.identifier),
      ':',
      field('type', $.type)
    ),

    procedure_body: $ => seq(
      'begin',
      repeat($._statement),
      'end;'
    ),

    _statement: $ => choice(
      $.procedure_call,
      $.if_statement,
      $.exit_statement
      // Add more statement types as needed
    ),

    procedure_call: $ => seq(
      field('name', $.identifier),
      '(',
      optional($._expression),
      ')',
      ';'
    ),

    if_statement: $ => seq(
      'if',
      $._expression,
      'then',
      repeat($._statement),
      optional(seq('else', repeat($._statement))),
      ';'
    ),

    exit_statement: $ => seq(
      'exit',
      '(',
      $._expression,
      ')',
      ';'
    ),

    _expression: $ => choice(
      $.binary_expression,
      $.identifier,
      $.string,
      $.number,
      $.boolean
    ),

    binary_expression: $ => prec.left(1, seq(
      $._expression,
      choice('=', '<>', '<', '<=', '>', '>=', 'in', 'and', 'or'),
      $._expression
    )),

    object_id: $ => /[0-9]+/,
    object_name: $ => /"[^"]*"/,
    field_id: $ => /[0-9]+/,
    field_name: $ => /"[^"]*"/,
    field_type: $ => $.identifier,
    property_name: $ => $.identifier,
    property_value: $ => choice($.string, $.number, $.boolean, $.identifier),
    trigger_name: $ => $.identifier,
    procedure_name: $ => $.identifier,
    type: $ => $.identifier,
    identifier: $ => /[a-zA-Z_][a-zA-Z0-9_]*/,
    string: $ => /"[^"]*"/,
    number: $ => /[0-9]+(\.[0-9]+)?/,
    boolean: $ => choice('true', 'false')
  }
});
