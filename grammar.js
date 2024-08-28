module.exports = grammar({
  name: 'al',

  rules: {
    source_file: $ => repeat($._declaration),

    _declaration: $ => choice(
      $.table_object,
      $.codeunit_object,
      $.control_addin_object,
      $.entitlement_object,
      $.page_customization_object,
      $.page_extension_object,
      $.page_object,
      $.permission_set_extension_object,
      $.permission_set_object,
      $.profile_object,
      $.query_object,
      $.report_extension_object
      // Other object types can be added here in the future
    ),

    report_extension_object: $ => seq(
      'reportextension',
      field('id', $.integer),
      field('name', $.string),
      'extends',
      field('base_report', $.string),
      '{',
      repeat($._report_extension_element),
      '}'
    ),

    _report_extension_element: $ => choice(
      $.dataset,
      $.requestpage,
      $.rendering,
      $.trigger
    ),

    dataset: $ => seq(
      'dataset',
      '{',
      repeat($._dataset_element),
      '}'
    ),

    _dataset_element: $ => choice(
      $.add,
      $.modify
    ),

    add: $ => seq(
      'add',
      '(',
      field('dataitem', $.identifier),
      ')',
      '{',
      repeat($.column),
      '}'
    ),

    column: $ => seq(
      'column',
      '(',
      field('name', $.identifier),
      ';',
      field('source', $._column_source),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    _column_source: $ => choice(
      $.identifier,
      $.qualified_name
    ),

    qualified_name: $ => seq(
      $.identifier,
      '.',
      $.identifier
    ),

    requestpage: $ => seq(
      'requestpage',
      '{',
      repeat($._requestpage_element),
      '}'
    ),

    _requestpage_element: $ => choice(
      $.layout
    ),

    rendering: $ => seq(
      'rendering',
      '{',
      repeat($.layout),
      '}'
    ),

    query_object: $ => seq(
      'query',
      field('id', $.integer),
      field('name', $.string),
      '{',
      repeat($._query_element),
      '}'
    ),

    _query_element: $ => choice(
      $.property,
      $.elements
    ),

    elements: $ => seq(
      'elements',
      '{',
      repeat($.dataitem),
      '}'
    ),

    dataitem: $ => seq(
      'dataitem',
      '(',
      field('name', $.identifier),
      ';',
      field('table', $.identifier),
      ')',
      '{',
      repeat($._dataitem_element),
      '}'
    ),

    _dataitem_element: $ => choice(
      $.column,
      $.dataitem,
      $.property
    ),

    column: $ => seq(
      'column',
      '(',
      field('name', $.identifier),
      ';',
      field('field', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    profile_object: $ => seq(
      'profile',
      field('name', $.identifier),
      '{',
      repeat($._profile_element),
      '}'
    ),

    _profile_element: $ => choice(
      $.property,
      $.customizations
    ),

    customizations: $ => seq(
      'Customizations',
      '=',
      field('customization_name', $.identifier),
      ';'
    ),

    permission_set_object: $ => seq(
      'permissionset',
      field('id', $.integer),
      field('name', $.string),
      '{',
      repeat($._permission_set_element),
      '}'
    ),

    _permission_set_element: $ => choice(
      $.property,
      $.permissions
    ),

    permission_set_extension_object: $ => seq(
      'permissionsetextension',
      field('id', $.integer),
      field('name', $.string),
      'extends',
      field('base_permission_set', $.string),
      '{',
      repeat($._permission_set_extension_element),
      '}'
    ),

    _permission_set_extension_element: $ => choice(
      $.permissions
    ),

    permissions: $ => seq(
      'Permissions',
      '=',
      $.permission_list,
      ';'
    ),

    permission_list: $ => seq(
      repeat1($.permission_entry)
    ),

    permission_entry: $ => seq(
      field('object_type', $.identifier),
      field('object_name', choice($.string, $.identifier)),
      '=',
      field('permission_type', $.identifier)
    ),

    page_object: $ => seq(
      'page',
      field('id', $.integer),
      field('name', $.string),
      '{',
      repeat($._page_element),
      '}'
    ),

    _page_element: $ => choice(
      $.property,
      $.layout,
      $.actions,
      $.views
    ),

    page_extension_object: $ => seq(
      'pageextension',
      field('id', $.integer),
      field('name', $.string),
      'extends',
      field('base_page', $.string),
      '{',
      repeat($._page_extension_element),
      '}'
    ),

    _page_extension_element: $ => choice(
      $.layout,
      $.actions
    ),

    page_customization_object: $ => seq(
      'pagecustomization',
      field('name', $.identifier),
      'customizes',
      field('target_page', $.string),
      '{',
      repeat($._page_customization_element),
      '}'
    ),

    _page_customization_element: $ => choice(
      $.layout,
      $.actions
    ),

    layout: $ => seq(
      'layout',
      '{',
      repeat($._layout_element),
      '}'
    ),

    _layout_element: $ => choice(
      $.modify,
      $.add_first,
      $.add_last,
      $.add_after,
      $.add_before,
      $.move_after,
      $.move_before
    ),

    actions: $ => seq(
      'actions',
      '{',
      repeat($._action_element),
      '}'
    ),

    _action_element: $ => choice(
      $.modify,
      $.add_first,
      $.add_last,
      $.add_after,
      $.add_before,
      $.move_after,
      $.move_before
    ),

    views: $ => seq(
      'views',
      '{',
      repeat($.view),
      '}'
    ),

    view: $ => seq(
      field('name', $.identifier),
      '{',
      repeat($.property),
      '}'
    ),

    modify: $ => seq(
      'modify',
      '(',
      field('target', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    add_first: $ => seq(
      'addfirst',
      '(',
      field('target', $.identifier),
      ')',
      '{',
      repeat($._customization_content),
      '}'
    ),

    add_last: $ => seq(
      'addlast',
      '(',
      field('target', $.identifier),
      ')',
      '{',
      repeat($._customization_content),
      '}'
    ),

    add_after: $ => seq(
      'addafter',
      '(',
      field('target', $.identifier),
      ')',
      '{',
      repeat($._customization_content),
      '}'
    ),

    add_before: $ => seq(
      'addbefore',
      '(',
      field('target', $.identifier),
      ')',
      '{',
      repeat($._customization_content),
      '}'
    ),

    move_after: $ => seq(
      'moveafter',
      '(',
      field('target', $.identifier),
      ';',
      field('new_position', $.identifier),
      ')'
    ),

    move_before: $ => seq(
      'movebefore',
      '(',
      field('target', $.identifier),
      ';',
      field('new_position', $.identifier),
      ')'
    ),

    _customization_content: $ => choice(
      $.field,
      $.group,
      $.action
    ),

    group: $ => seq(
      'group',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($._customization_content),
      '}'
    ),

    action: $ => seq(
      'action',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    entitlement_object: $ => seq(
      'entitlement',
      field('name', $.string),
      '{',
      repeat($._entitlement_element),
      '}'
    ),

    _entitlement_element: $ => choice(
      $.entitlement_property
    ),

    entitlement_property: $ => seq(
      field('name', $.identifier),
      '=',
      field('value', $._value)
    ),

    control_addin_object: $ => seq(
      'controladdin',
      field('name', $.identifier),
      '{',
      repeat($._control_addin_element),
      '}'
    ),

    _control_addin_element: $ => choice(
      $.property,
      $.procedure,
      $.event
    ),

    event: $ => seq(
      'event',
      field('name', $.identifier),
      '(',
      optional($._parameter_list),
      ')'
    ),

    codeunit_object: $ => seq(
      'codeunit',
      field('id', $.integer),
      field('name', $.string),
      '{',
      repeat($._codeunit_element),
      '}'
    ),

    _codeunit_element: $ => choice(
      $.property,
      $.trigger,
      $.procedure
      // Other codeunit elements can be added here
    ),

    trigger: $ => seq(
      'trigger',
      field('name', $.identifier),
      '(',
      optional($._parameter_list),
      ')',
      field('body', $.code_block)
    ),

    procedure: $ => seq(
      optional('local'),
      'procedure',
      field('name', $.identifier),
      '(',
      optional($._parameter_list),
      ')',
      field('return_type', optional(seq(':', $._type))),
      field('body', $.code_block)
    ),

    _parameter_list: $ => seq(
      $.parameter,
      repeat(seq(';', $.parameter))
    ),

    parameter: $ => seq(
      optional(choice('var', 'out')),
      field('name', $.identifier),
      ':',
      field('type', $._type)
    ),

    _type: $ => choice(
      $.identifier,
      $.record_type
    ),

    record_type: $ => seq(
      'Record',
      field('table_name', $.identifier)
    ),

    code_block: $ => seq(
      'begin',
      repeat($._statement),
      'end'
    ),

    _statement: $ => choice(
      // Add various statement types here
      // For now, we'll just use a placeholder
      $.placeholder_statement
    ),

    placeholder_statement: $ => /[^;]+;/,

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
