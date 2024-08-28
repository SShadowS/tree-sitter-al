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
      optional(field('al', $.string)), // AL property for table alias
      optional(prec(2, seq(
        '{',
        repeat($.table_level_property),
        '}'
      ))),
      '{',
      repeat($._table_element),
      '}'
    ),

    _table_element: $ => choice(
      $.field_definition,
      $.key_definition,
      $.variable_declaration,
      $.trigger_definition,
      $.procedure_definition,
      prec(1, $.property)
      // Other table elements can be added here
    ),

    table_level_property: $ => $.property,

    property: $ => seq(
      field('name', $.property_name),
      '=',
      field('value', $.property_value),
      optional(';')
    ),

    field_definition: $ => prec.right(1, seq(
      'field',
      '(',
      field('id', $.field_id),
      ';',
      field('name', $.field_name),
      ')',
      field('type', $.field_type),
      optional(field('al', $.string)), // AL property for field alias
      optional(seq(
        '{',
        repeat($.property),
        '}'
      )),
      optional(';')
    )),

    key_definition: $ => seq(
      'key',
      '(',
      commaSep1($.identifier),
      ')',
      optional(field('al', $.string)), // AL property for key alias
      optional(seq(
        '{',
        repeat($.property),
        '}'
      )),
      optional(';')
    ),

    property_name: $ => choice(
      $.identifier,
      'Caption',
      'DataCaptionFields',
      'DataClassification',
      'Description',
      'DrillDownPageId',
      'LookupPageId',
      'PasteIsValid',
      'Permissions',
      'TableType'
      // Add more table properties as needed
    ),

    property_value: $ => choice(
      $.string,
      $.number,
      $.boolean,
      $.identifier
    ),

    key_definition: $ => seq(
      'key',
      '(',
      commaSep1($.identifier),
      ')',
      optional(seq(
        '{',
        repeat($.property),
        '}'
      ))
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
      optional(field('al', $.string)), // AL property for procedure alias
      $.procedure_body
    ),

    parameter_list: $ => commaSep1($.parameter),

    parameter: $ => seq(
      optional(choice('var', 'out')),
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
      $.exit_statement,
      $.assignment_statement
      // Add more statement types as needed
    ),

    procedure_call: $ => seq(
      field('name', $.identifier),
      '(',
      optional(commaSep($._expression)),
      ')',
      ';'
    ),

    if_statement: $ => prec.right(1, seq(
      'if',
      $._expression,
      'then',
      repeat($._statement),
      optional(seq('else', repeat($._statement))),
      optional(';')
    )),

    exit_statement: $ => seq(
      'exit',
      '(',
      optional($._expression),
      ')',
      ';'
    ),

    assignment_statement: $ => seq(
      field('left', $._assignable),
      ':=',
      field('right', $._expression),
      ';'
    ),

    _assignable: $ => choice(
      $.identifier,
      $.field_access
    ),

    field_access: $ => seq(
      field('record', $.identifier),
      '.',
      field('field', $.identifier)
    ),

    _expression: $ => choice(
      $.binary_expression,
      $.unary_expression,
      $.parenthesized_expression,
      $.identifier,
      $.field_access,
      $.string,
      $.number,
      $.boolean
    ),

    binary_expression: $ => prec.left(1, seq(
      field('left', $._expression),
      field('operator', choice('=', '<>', '<', '<=', '>', '>=', 'in', 'and', 'or', '+', '-', '*', '/')),
      field('right', $._expression)
    )),

    unary_expression: $ => prec(2, seq(
      field('operator', choice('-', 'not')),
      field('operand', $._expression)
    )),

    parenthesized_expression: $ => seq(
      '(',
      $._expression,
      ')'
    ),

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

function commaSep(rule) {
  return optional(commaSep1(rule));
}

function commaSep1(rule) {
  return seq(rule, repeat(seq(',', rule)));
}
