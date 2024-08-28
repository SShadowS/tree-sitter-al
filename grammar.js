module.exports = grammar({
  name: 'al',

  rules: {
    source_file: $ => repeat($._declaration),

    _declaration: $ => choice(
      $.table_object
      // Other object types can be added here in the future
    ),

    table_object: $ => seq(
      'table',
      field('id', $.integer),
      field('name', $.string),
      '{',
      repeat($._table_element),
      '}'
    ),

    _table_element: $ => choice(
      $.field,
      $.property
      // Other table elements can be added here
    ),

    field: $ => seq(
      'field',
      field('id', $.integer),
      field('name', $.string),
      '{',
      repeat($.field_property),
      '}'
    ),

    field_property: $ => seq(
      field('name', $.identifier),
      '=',
      field('value', $._value)
    ),

    property: $ => seq(
      'property',
      field('name', $.identifier),
      '{',
      field('value', $._value),
      '}'
    ),

    _value: $ => choice(
      $.string,
      $.integer,
      $.boolean,
      $.identifier
    ),

    string: $ => /"[^"]*"/,
    integer: $ => /\d+/,
    boolean: $ => choice('true', 'false'),
    identifier: $ => /[a-zA-Z_][a-zA-Z0-9_]*/
  }
});
