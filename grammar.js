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
      $.key,
      $.fieldgroup
      // Other table elements can be added here
    ),

    field: $ => seq(
      'field',
      '(',
      field('id', $.integer),
      ';',
      field('name', $.string),
      ')',
      field('type', $.data_type),
      optional(';'),
      optional($.field_properties)
    ),

    key: $ => seq(
      'key',
      '(',
      field('name', $.string),
      ')',
      '{',
      repeat1($.field_reference),
      '}'
    ),

    fieldgroup: $ => seq(
      'fieldgroup',
      '(',
      field('name', $.string),
      ')',
      '{',
      repeat1($.field_reference),
      '}'
    ),

    field_reference: $ => seq(
      field('field', $.identifier),
      optional(';')
    ),

    data_type: $ => choice(
      'BigInteger',
      'Binary',
      'Boolean',
      'Char',
      'Code',
      'Date',
      'DateFormula',
      'DateTime',
      'Decimal',
      'Duration',
      'Guid',
      'Integer',
      'Option',
      'RecordId',
      'Text',
      'Time'
      // Add more data types as needed
    ),

    field_properties: $ => repeat1($.property),

    property: $ => seq(
      field('name', $.identifier),
      '=',
      field('value', $._property_value),
      ';'
    ),

    _property_value: $ => choice(
      $.string,
      $.number,
      $.boolean,
      $.identifier
    ),

    integer: $ => /[0-9]+/,
    string: $ => /"[^"]*"/,
    identifier: $ => /[a-zA-Z_][a-zA-Z0-9_]*/,
    number: $ => /[0-9]+(\.[0-9]+)?/,
    boolean: $ => choice('true', 'false')
  }
});
