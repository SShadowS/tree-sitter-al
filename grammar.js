module.exports = grammar({
  name: 'al',

  rules: {
    source_file: $ => repeat($._definition),

    _definition: $ => choice(
      $.table,
      $.tableextension,
      $.page,
      $.pageextension,
      $.codeunit,
      $.report,
      $.query,
      $.xmlport,
      $.enum,
      $.dotnet,
      $.controladdin
    ),

    // Object Definitions
    table: $ => seq(
      'table',
      field('table_id', $.integer),
      field('table_name', $.identifier),
      optional($.extends_clause),
      '{',
      repeat($._table_body_element),
      '}'
    ),

    tableextension: $ => seq(
      'tableextension',
      field('tableextension_id', $.integer),
      field('tableextension_name', $.identifier),
      'extends',
      field('base_table', $.identifier),
      '{',
      repeat($._table_body_element),
      '}'
    ),

    page: $ => seq(
      'page',
      field('page_id', $.integer),
      field('page_name', $.identifier),
      '{',
      repeat($._page_body_element),
      '}'
    ),

    pageextension: $ => seq(
      'pageextension',
      field('pageextension_id', $.integer),
      field('pageextension_name', $.identifier),
      'extends',
      field('base_page', $.identifier),
      '{',
      repeat($._page_body_element),
      '}'
    ),

    codeunit: $ => seq(
      'codeunit',
      field('codeunit_id', $.integer),
      field('codeunit_name', $.identifier),
      '{',
      repeat($._codeunit_body_element),
      '}'
    ),

    report: $ => seq(
      'report',
      field('report_id', $.integer),
      field('report_name', $.identifier),
      '{',
      repeat($._report_body_element),
      '}'
    ),

    query: $ => seq(
      'query',
      field('query_id', $.integer),
      field('query_name', $.identifier),
      '{',
      repeat($._query_body_element),
      '}'
    ),

    xmlport: $ => seq(
      'xmlport',
      field('xmlport_id', $.integer),
      field('xmlport_name', $.identifier),
      '{',
      repeat($._xmlport_body_element),
      '}'
    ),

    enum: $ => seq(
      'enum',
      field('enum_id', $.integer),
      field('enum_name', $.identifier),
      '{',
      repeat($.enum_value),
      '}'
    ),

    dotnet: $ => seq(
      'dotnet',
      field('dotnet_name', $.identifier),
      '{',
      repeat($.assembly),
      '}'
    ),

    controladdin: $ => seq(
      'controladdin',
      field('controladdin_name', $.identifier),
      '{',
      repeat($._controladdin_body_element),
      '}'
    ),

    // Common Elements
    _table_body_element: $ => choice(
      $.field,
      $.key,
      $.fieldgroup,
      $.trigger,
      $.procedure,
      $.property
    ),

    _page_body_element: $ => choice(
      $.layout,
      $.actions,
      $.trigger,
      $.procedure,
      $.property
    ),

    _codeunit_body_element: $ => choice(
      $.trigger,
      $.procedure,
      $.property,
      $.var_section
    ),

    _report_body_element: $ => choice(
      $.dataset,
      $.requestpage,
      $.trigger,
      $.procedure,
      $.property
    ),

    _query_body_element: $ => choice(
      $.elements,
      $.filter,
      $.column,
      $.trigger,
      $.property
    ),

    _xmlport_body_element: $ => choice(
      $.schema,
      $.requestpage,
      $.trigger,
      $.procedure,
      $.property
    ),

    _controladdin_body_element: $ => choice(
      $.property,
      $.event,
      $.procedure
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
      'key',
      '(',
      field('fields', $.identifier_list),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    fieldgroup: $ => seq(
      'fieldgroup',
      '(',
      field('fieldgroup_name', $.identifier),
      ')',
      '{',
      field('fields', $.identifier_list),
      '}'
    ),

    trigger: $ => seq(
      'trigger',
      field('trigger_name', $.identifier),
      '(',
      optional($.parameter_list),
      ')',
      '{',
      repeat($.statement),
      '}'
    ),

    procedure: $ => seq(
      optional('local'),
      'procedure',
      field('procedure_name', $.identifier),
      '(',
      optional($.parameter_list),
      ')',
      optional(seq(':', field('return_type', $.data_type))),
      '{',
      repeat($.statement),
      '}'
    ),

    property: $ => seq(
      field('property_name', $.identifier),
      '=',
      field('property_value', $._property_value),
      ';'
    ),

    var_section: $ => seq(
      'var',
      repeat1($.var_declaration)
    ),

    var_declaration: $ => seq(
      field('var_name', $.identifier),
      ':',
      field('var_type', $.data_type),
      ';'
    ),

    layout: $ => seq(
      'layout',
      '{',
      repeat($.layout_element),
      '}'
    ),

    layout_element: $ => choice(
      $.area,
      $.group,
      $.field,
      $.part
    ),

    area: $ => seq(
      'area',
      '(',
      field('area_type', $.identifier),
      ')',
      '{',
      repeat($.layout_element),
      '}'
    ),

    group: $ => seq(
      'group',
      '(',
      field('group_type', $.identifier),
      ')',
      '{',
      repeat($.layout_element),
      '}'
    ),

    part: $ => seq(
      'part',
      '(',
      field('part_name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    actions: $ => seq(
      'actions',
      '{',
      repeat($.action),
      '}'
    ),

    action: $ => seq(
      'action',
      '(',
      field('action_name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    dataset: $ => seq(
      'dataset',
      '{',
      repeat($.dataitem),
      '}'
    ),

    dataitem: $ => seq(
      'dataitem',
      '(',
      field('dataitem_name', $.identifier),
      ')',
      '{',
      repeat(choice(
        $.column,
        $.dataitem,
        $.trigger,
        $.property
      )),
      '}'
    ),

    requestpage: $ => seq(
      'requestpage',
      '{',
      repeat($.requestpage_element),
      '}'
    ),

    requestpage_element: $ => choice(
      $.layout,
      $.actions,
      $.trigger,
      $.property
    ),

    elements: $ => seq(
      'elements',
      '{',
      repeat($.query_element),
      '}'
    ),

    query_element: $ => choice(
      $.dataitem,
      $.column,
      $.filter
    ),

    filter: $ => seq(
      'filter',
      '{',
      repeat($.filter_element),
      '}'
    ),

    filter_element: $ => seq(
      field('field', $.identifier),
      '=',
      field('value', $.expression),
      ';'
    ),

    column: $ => seq(
      'column',
      '(',
      field('column_name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    schema: $ => seq(
      'schema',
      '{',
      repeat($.schema_element),
      '}'
    ),

    schema_element: $ => choice(
      $.textelement,
      $.fieldelement,
      $.tableelement
    ),

    textelement: $ => seq(
      'textelement',
      '(',
      field('element_name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    fieldelement: $ => seq(
      'fieldelement',
      '(',
      field('element_name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    tableelement: $ => seq(
      'tableelement',
      '(',
      field('element_name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    event: $ => seq(
      'event',
      field('event_name', $.identifier),
      '(',
      optional($.parameter_list),
      ')',
      ';'
    ),

    enum_value: $ => seq(
      field('value_name', $.identifier),
      optional(seq('=', field('value', $.integer))),
      ';'
    ),

    assembly: $ => seq(
      'assembly',
      '(',
      field('assembly_name', $.string),
      ')',
      ';'
    ),

    extends_clause: $ => seq(
      'extends',
      field('base_object', $.identifier)
    ),

    // Statements
    statement: $ => choice(
      $.assignment_statement,
      $.if_statement,
      $.case_statement,
      $.for_statement,
      $.foreach_statement,
      $.while_statement,
      $.repeat_statement,
      $.call_statement,
      $.exit_statement,
      $.with_statement
    ),

    assignment_statement: $ => seq(
      field('left_hand_side', $.identifier),
      ':=',
      field('right_hand_side', $.expression),
      ';'
    ),

    if_statement: $ => seq(
      'if',
      field('condition', $.expression),
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

    case_statement: $ => seq(
      'case',
      field('expression', $.expression),
      'of',
      repeat1($.case_option),
      optional(seq(
        'else',
        '{',
        repeat($.statement),
        '}'
      )),
      'end;'
    ),

    case_option: $ => seq(
      field('option', $.expression),
      ':',
      '{',
      repeat($.statement),
      '}'
    ),

    for_statement: $ => seq(
      'for',
      field('variable', $.identifier),
      ':=',
      field('start', $.expression),
      'to',
      field('end', $.expression),
      'do',
      '{',
      repeat($.statement),
      '}'
    ),

    foreach_statement: $ => seq(
      'foreach',
      field('variable', $.identifier),
      'in',
      field('collection', $.expression),
      'do',
      '{',
      repeat($.statement),
      '}'
    ),

    while_statement: $ => seq(
      'while',
      field('condition', $.expression),
      'do',
      '{',
      repeat($.statement),
      '}'
    ),

    repeat_statement: $ => seq(
      'repeat',
      '{',
      repeat($.statement),
      '}',
      'until',
      field('condition', $.expression),
      ';'
    ),

    call_statement: $ => seq(
      field('function_name', $.identifier),
      '(',
      optional($.argument_list),
      ')',
      ';'
    ),

    exit_statement: $ => seq(
      'exit',
      ';'
    ),

    with_statement: $ => seq(
      'with',
      field('record', $.identifier),
      'do',
      '{',
      repeat($.statement),
      '}'
    ),

    // Expressions
    expression: $ => choice(
      $.identifier,
      $.literal,
      $.binary_expression,
      $.unary_expression,
      $.parenthesized_expression,
      $.function_call
    ),

    binary_expression: $ => prec.left(1, seq(
      field('left', $.expression),
      field('operator', $.binary_operator),
      field('right', $.expression)
    )),

    unary_expression: $ => prec(2, seq(
      field('operator', $.unary_operator),
      field('operand', $.expression)
    )),

    parenthesized_expression: $ => seq(
      '(',
      $.expression,
      ')'
    ),

    function_call: $ => seq(
      field('function_name', $.identifier),
      '(',
      optional($.argument_list),
      ')'
    ),

    // Operators
    binary_operator: $ => choice(
      '+', '-', '*', '/', 'div', 'mod',
      '=', '<>', '<', '<=', '>', '>=',
      'and', 'or', 'xor'
    ),

    unary_operator: $ => choice(
      '-', 'not'
    ),

    // Literals
    literal: $ => choice(
      $.integer,
      $.decimal,
      $.string,
      $.boolean,
      $.date,
      $.time,
      $.datetime
    ),

    // Basic types
    identifier: $ => /[a-zA-Z_][a-zA-Z0-9_]*/,
    identifier_list: $ => sepBy1(',', $.identifier),
    argument_list: $ => sepBy1(',', $.expression),
    parameter_list: $ => sepBy1(',', $.parameter),

    parameter: $ => seq(
      optional('var'),
      field('parameter_name', $.identifier),
      ':',
      field('parameter_type', $.data_type)
    ),

    data_type: $ => choice(
      'Integer',
      'Decimal',
      'Text',
      'Code',
      'Boolean',
      'Date',
      'Time',
      'DateTime',
      'Duration',
      'BigInteger',
      'Char',
      'Option',
      'Record',
      'RecordRef',
      'FieldRef',
      'DateFormula',
      'Variant',
      'Blob',
      'GUID',
      'InStream',
      'OutStream',
      'Dialog',
      'File',
      'TextConst',
      'Label',
      'Action',
      'XmlPort',
      'HttpClient',
      'HttpContent',
      'HttpHeaders',
      'HttpRequestMessage',
      'HttpResponseMessage',
      'JsonToken',
      'JsonValue',
      'JsonArray',
      'JsonObject',
      'List',
      'Dictionary',
      'DotNet',
      seq('array', '[', ']', 'of', $.data_type)
    ),

    _property_value: $ => choice(
      $.literal,
      $.identifier
    ),

    boolean: $ => choice('true', 'false'),
    integer: $ => /\d+/,
    decimal: $ => /\d+\.\d+/,
    string: $ => /'[^']*'/,
    date: $ => /\d{2}\.\d{2}\.\d{4}/,
    time: $ => /\d{2}:\d{2}:\d{2}/,
    datetime: $ => seq($.date, $.time)
  }
});

// Helper function to handle repeated elements separated by a delimiter
function sepBy1(delimiter, rule) {
  return seq(rule, repeat(seq(delimiter, rule)));
}
