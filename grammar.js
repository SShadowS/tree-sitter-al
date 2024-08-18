module.exports = grammar({
  name: 'al',

  extras: $ => [
    $.comment,
    /\s/
  ],

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
      $.controladdin,
      $.profile,
      $.permissionset,
      $.permissionsetextension,
      $.entitlement
    ),

    // Object Definitions
    table: $ => seq(
      'table',
      field('table_id', $.integer),
      field('table_name', choice($.string, $.identifier)),
      optional($.extends_clause),
      '{',
      repeat($._table_element),
      '}'
    ),

    _table_element: $ => choice(
      $.fields_block,
      $.keys_block,
      $.fieldgroups_block,
      $.trigger,
      $.procedure,
      $.property,
      $.table_property,
      $.caption_property,
      $.lookup_page_id_property,
      $.drill_down_page_id_property,
      $.data_classification_property,
      $.data_caption_fields_property,
      $.obsolete_state_property,
      $.paste_is_valid_property,
      $.extensible_property,
      $.permissions_property,
      $.access_property,
      $.data_per_company_property
    ),

    caption_property: $ => seq(
      'Caption',
      '=',
      field('caption_value', $.string),
      ';'
    ),

    lookup_page_id_property: $ => seq(
      'LookupPageID',
      '=',
      field('page_id', choice($.integer, $.identifier)),
      ';'
    ),

    drill_down_page_id_property: $ => seq(
      'DrillDownPageID',
      '=',
      field('page_id', choice($.integer, $.identifier)),
      ';'
    ),

    data_per_company_property: $ => seq(
      'DataPerCompany',
      '=',
      field('value', $.boolean),
      ';'
    ),

    lookup_page_property: $ => seq(
      'LookupPageID',
      '=',
      field('page_name', $.identifier),
      ';'
    ),

    drill_down_page_property: $ => seq(
      'DrillDownPageID',
      '=',
      field('page_name', $.identifier),
      ';'
    ),

    permissions_property: $ => seq(
      'Permissions',
      '=',
      field('permissions', $.permission_list),
      ';'
    ),

    permission_list: $ => seq(
      '[',
      sepBy1(',', $.permission_item),
      ']'
    ),

    permission_item: $ => seq(
      field('permission_type', $.identifier),
      '=',
      field('permission_value', $.identifier)
    ),

    access_property: $ => seq(
      'Access',
      '=',
      field('access_value', $.identifier),
      ';'
    ),

    paste_is_valid_property: $ => seq(
      'PasteIsValid',
      '=',
      field('value', $.boolean),
      ';'
    ),

    extensible_property: $ => seq(
      'Extensible',
      '=',
      field('value', $.boolean),
      ';'
    ),

    data_classification_property: $ => seq(
      'DataClassification',
      '=',
      field('classification', $.identifier),
      ';'
    ),

    data_caption_fields_property: $ => seq(
      'DataCaptionFields',
      '=',
      field('fields', $.identifier_list),
      ';'
    ),

    obsolete_state_property: $ => seq(
      'ObsoleteState',
      '=',
      field('state', $.identifier),
      ';'
    ),

    lookup_page_id: $ => seq(
      'LookupPageID',
      '=',
      field('page_name', $.string),
      ';'
    ),

    drill_down_page_id: $ => seq(
      'DrillDownPageID',
      '=',
      field('page_name', $.string),
      ';'
    ),

    caption: $ => seq(
      'Caption',
      '=',
      field('caption_value', $.string),
      ';'
    ),

    table_property: $ => prec(12, seq(
      field('property_name', $.identifier),
      '=',
      field('property_value', choice($.literal, $.identifier, $.property_option, $.boolean, $.property_list, $.page_reference)),
      optional(';')
    )),

    page_reference: $ => seq(
      'Page',
      '::',
      field('page_name', $.identifier)
    ),

    property: $ => prec(11, seq(
      field('property_name', $.identifier),
      '=',
      field('property_value', choice($.literal, $.identifier, $.property_option, $.boolean, $.property_list, $.page_reference)),
      optional(';')
    )),

    fields_block: $ => seq(
      'fields',
      '{',
      repeat($.field),
      '}'
    ),

    keys_block: $ => seq(
      'keys',
      '{',
      repeat($.key),
      '}'
    ),

    fieldgroups_block: $ => seq(
      'fieldgroups',
      '{',
      repeat($.fieldgroup),
      '}'
    ),

    fieldgroup: $ => seq(
      field('fieldgroup_name', $.identifier),
      '{',
      field('fields', $.identifier_list),
      '}'
    ),

    page_reference: $ => seq(
      'Page',
      '::',
      field('page_name', $.identifier)
    ),

    property_option: $ => prec.left(8, seq(
      field('option_name', $.identifier),
      optional(seq(':', field('option_value', choice($.literal, $.boolean, $.identifier))))
    )),

    property_list: $ => seq(
      '[',
      sepBy1(',', $.property_option),
      ']'
    ),

    field: $ => seq(
      'field',
      '(',
      field('field_id', $.integer),
      ';',
      field('field_name', $.string),
      ')',
      field('data_type', $.data_type),
      '{',
      repeat($.field_property),
      '}'
    ),

    field_property: $ => choice(
      $.caption_property,
      $.data_classification_property,
      $.table_relation_property,
      $.option_caption_property,
      $.option_string_property,
      $.trigger,
      $.obsolete_state_property,
      $.access_by_permission_property,
      $.enabled_property,
      $.visible_property,
      $.field_class_property,
      $.auto_increment_property,
      $.validate_property,
      $.description_property,
      $.blob_sub_type_property,
      $.width_property,
      $.editable_property,
      $.notify_on_validate_property,
      $.validate_on_validate_property,
      $.init_value_property,
      $.test_table_relation_property,
      $.valid_ate_table_relation_property
    ),

    option_caption_property: $ => seq(
      'OptionCaption',
      '=',
      field('captions', $.string),
      ';'
    ),

    option_string_property: $ => seq(
      'OptionString',
      '=',
      field('option_string', $.string),
      ';'
    ),

    table_relation_property: $ => prec(2, seq(
      'TableRelation',
      '=',
      field('table_name', choice($.identifier, $.table_relation_expression)),
      ';'
    )),

    table_relation_expression: $ => seq(
      field('table_name', $.identifier),
      optional(seq('.', field('field_name', $.identifier))),
      optional(seq(
        'WHERE',
        '(',
        sepBy1(
          ',',
          seq(
            field('field_name', $.identifier),
            '=',
            field('field_value', choice($.identifier, $.literal, $.field_reference))
          )
        ),
        ')'
      ))
    ),

    field_reference: $ => seq(
      'FIELD',
      '(',
      field('field_name', $.identifier),
      ')'
    ),

    width_property: $ => seq(
      'Width',
      '=',
      field('width', $.integer),
      ';'
    ),

    editable_property: $ => seq(
      'Editable',
      '=',
      field('editable', $.boolean),
      ';'
    ),

    notify_on_validate_property: $ => seq(
      'NotifyOnValidate',
      '=',
      field('notify', $.boolean),
      ';'
    ),

    validate_on_validate_property: $ => seq(
      'ValidateOnValidate',
      '=',
      field('validate', $.boolean),
      ';'
    ),

    init_value_property: $ => seq(
      'InitValue',
      '=',
      field('init_value', choice($.literal, $.identifier)),
      ';'
    ),

    test_table_relation_property: $ => seq(
      'TestTableRelation',
      '=',
      field('test', $.boolean),
      ';'
    ),

    valid_ate_table_relation_property: $ => seq(
      'ValidateTableRelation',
      '=',
      field('validate', $.boolean),
      ';'
    ),

    blob_sub_type_property: $ => seq(
      'SubType',
      '=',
      field('sub_type', $.identifier),
      ';'
    ),

    field_class_property: $ => seq(
      'FieldClass',
      '=',
      field('field_class', $.identifier),
      ';'
    ),

    auto_increment_property: $ => seq(
      'AutoIncrement',
      '=',
      field('auto_increment', $.boolean),
      ';'
    ),

    validate_property: $ => seq(
      'ValidateTableRelation',
      '=',
      field('validate', $.boolean),
      ';'
    ),

    description_property: $ => seq(
      'Description',
      '=',
      field('description', $.string),
      ';'
    ),

    option_caption: $ => seq(
      'OptionCaption',
      '=',
      field('captions', $.string),
      ';'
    ),

    option_string: $ => seq(
      'OptionString',
      '=',
      field('options', $.string),
      ';'
    ),

    access_by_permission_property: $ => seq(
      'AccessByPermission',
      '=',
      field('permission', $.string),
      ';'
    ),

    enabled_property: $ => seq(
      'Enabled',
      '=',
      field('enabled', $.boolean),
      ';'
    ),

    visible_property: $ => seq(
      'Visible',
      '=',
      field('visible', $.boolean),
      ';'
    ),

    table_relation: $ => seq(
      'TableRelation',
      '=',
      field('table_name', $.string),
      ';'
    ),

    data_classification: $ => seq(
      'DataClassification',
      '=',
      field('classification', $.identifier),
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
      $.part,
      $.systempart,
      $.chartpart
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

    systempart: $ => seq(
      'systempart',
      '(',
      field('systempart_name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    chartpart: $ => seq(
      'chartpart',
      '(',
      field('chartpart_name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    group: $ => seq(
      'group',
      '(',
      field('group_name', $.identifier),
      ')',
      '{',
      repeat($.layout_element),
      '}'
    ),

    area: $ => seq(
      'area',
      '(',
      field('area_name', $.identifier),
      ')',
      '{',
      repeat($.layout_element),
      '}'
    ),

    key: $ => seq(
      'key',
      '(',
      field('key_name', $.identifier),
      ')',
      '{',
      field('fields', $.identifier_list),
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

    tableextension: $ => seq(
      'tableextension',
      field('tableextension_id', $.integer),
      field('tableextension_name', choice($.string, $.identifier)),
      'extends',
      field('base_table', choice($.string, $.identifier)),
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
      optional($.implements_clause),
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
      optional($.implements_clause),
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

    profile: $ => seq(
      'profile',
      field('profile_name', $.identifier),
      '{',
      repeat($.profile_element),
      '}'
    ),

    permissionset: $ => seq(
      'permissionset',
      field('permissionset_id', $.integer),
      field('permissionset_name', $.identifier),
      '{',
      repeat($.permission),
      '}'
    ),

    permissionsetextension: $ => seq(
      'permissionsetextension',
      field('permissionsetextension_id', $.integer),
      field('permissionsetextension_name', $.identifier),
      'extends',
      field('base_permissionset', $.identifier),
      '{',
      repeat($.permission),
      '}'
    ),

    entitlement: $ => seq(
      'entitlement',
      field('entitlement_name', $.identifier),
      '{',
      repeat($.entitlement_element),
      '}'
    ),

    // Common Elements
    _table_body_element: $ => choice(
      $.field,
      $.key,
      $.fieldgroup,
      $.trigger,
      $.procedure,
      $.property,
      $.var_section
    ),

    _page_body_element: $ => choice(
      $.layout,
      $.actions,
      $.trigger,
      $.procedure,
      $.property,
      $.var_section
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
      $.property,
      $.var_section
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
      $.property,
      $.var_section
    ),

    _controladdin_body_element: $ => choice(
      $.property,
      $.event,
      $.procedure
    ),

    trigger: $ => seq(
      'trigger',
      field('trigger_name', $.identifier),
      '(',
      ')',
      'var',
      repeat($.var_declaration),
      'begin',
      repeat($.statement),
      'end;'
    ),

    procedure: $ => seq(
      'procedure',
      field('procedure_name', $.identifier),
      '(',
      optional($.parameter_list),
      ')',
      optional(seq(':', field('return_type', $.data_type))),
      'var',
      repeat($.var_declaration),
      'begin',
      repeat($.statement),
      'end;'
    ),

    var_section: $ => prec.right(seq(
      'var',
      repeat1($.var_declaration),
      optional(';')
    )),

    procedure_attribute: $ => seq(
      '[',
      choice('IntegrationEvent', 'BusinessEvent', 'InternalEvent'),
      ']'
    ),

    var_declaration: $ => seq(
      field('var_name', $.identifier),
      ':',
      field('var_type', $.data_type),
      optional(seq('temporary')),
      ';'
    ),

    // Removed duplicate layout and layout_element definitions

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

    implements_clause: $ => seq(
      'implements',
      sepBy1(',', $.identifier)
    ),

    profile_element: $ => choice(
      $.profile_customization,
      $.profile_apparea
    ),

    profile_customization: $ => seq(
      'customizations',
      '=',
      $.string,
      ';'
    ),

    profile_apparea: $ => seq(
      'area',
      '(',
      field('area_name', $.identifier),
      ')',
      '{',
      repeat($.profile_apparea_element),
      '}'
    ),

    profile_apparea_element: $ => choice(
      $.profile_rolecenters,
      $.profile_sections
    ),

    profile_rolecenters: $ => seq(
      'rolecenters',
      '=',
      '[',
      sepBy1(',', $.integer),
      ']',
      ';'
    ),

    profile_sections: $ => seq(
      'sections',
      '=',
      '[',
      sepBy1(',', $.string),
      ']',
      ';'
    ),

    permission: $ => seq(
      field('object_type', $.identifier),
      field('object_name', $.string),
      '=',
      field('permission_type', $.identifier),
      ';'
    ),

    entitlement_element: $ => choice(
      $.entitlement_object_entitlements,
      $.entitlement_custom_entitlements
    ),

    entitlement_object_entitlements: $ => seq(
      'ObjectEntitlements',
      '=',
      '[',
      sepBy1(',', $.entitlement_object),
      ']',
      ';'
    ),

    entitlement_object: $ => seq(
      'ObjectType',
      '=',
      field('object_type', $.identifier),
      ',',
      'ObjectId',
      '=',
      field('object_id', $.string)
    ),

    entitlement_custom_entitlements: $ => seq(
      'CustomEntitlements',
      '=',
      '[',
      sepBy1(',', $.string),
      ']',
      ';'
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
      $.with_statement,
      $.return_statement,
      $.var_declaration,
      $.try_catch_statement,
      $.init_statement,
      $.modify_statement,
      $.insert_statement,
      $.calcfields_statement,
      $.find_statement,
      $.findlast_statement,
      $.setfilter_statement
    ),

    findlast_statement: $ => prec(2, seq(
      'FindLast',
      '(',
      ')',
      ';'
    )),

    setfilter_statement: $ => seq(
      'SetFilter',
      '(',
      field('field_name', $.identifier),
      ',',
      field('filter_expression', $.string),
      ')',
      ';'
    ),

    find_statement: $ => prec(1, seq(
      choice('FindFirst', 'FindLast', 'Find', 'FindSet'),
      '(',
      optional($.boolean),
      ')',
      ';'
    )),

    init_statement: $ => seq(
      'Init',
      '(',
      ')',
      ';'
    ),

    modify_statement: $ => seq(
      'Modify',
      '(',
      optional($.boolean),
      ')',
      ';'
    ),

    insert_statement: $ => seq(
      'Insert',
      '(',
      optional($.boolean),
      ')',
      ';'
    ),

    calcfields_statement: $ => seq(
      'CALCFIELDS',
      '(',
      field('field_name', $.identifier),
      ')',
      ';'
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
      optional(seq('step', field('step', $.expression))),
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

    return_statement: $ => seq(
      'return',
      optional(field('value', $.expression)),
      ';'
    ),

    try_catch_statement: $ => seq(
      'try',
      '{',
      repeat($.statement),
      '}',
      'catch',
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
      $.function_call,
      $.record_ref_expression,
      $.field_ref_expression
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

    record_ref_expression: $ => seq(
      'RecordRef',
      '.',
      'Open',
      '(',
      field('table_id', $.expression),
      ')'
    ),

    field_ref_expression: $ => seq(
      field('record', $.identifier),
      '.',
      'Field',
      '(',
      field('field_id', $.expression),
      ')'
    ),

    // Operators
    binary_operator: $ => choice(
      '+', '-', '*', '/', 'div', 'mod',
      '=', '<>', '<', '<=', '>', '>=',
      'and', 'or', 'xor', 'in'
    ),

    unary_operator: $ => choice(
      '-', 'not'
    ),

    // Literals
    literal: $ => prec(7, choice(
      $.integer,
      $.decimal,
      $.string,
      $.boolean,
      $.date,
      $.time,
      $.datetime
    )),

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
      'Record',
      'RecordId',
      'RecordRef',
      'FieldRef',
      'DateFormula',
      'Variant',
      'Blob',
      'Codeunit',
      'Page',
      'Report',
      'Query',
      'XmlPort',
      'GUID',
      'InStream',
      'OutStream',
      'Dialog',
      'File',
      'TextConst',
      'Label',
      'Action',
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
      seq('array', '[', ']', 'of', $.data_type),
      prec.left(2, 'Option'),
      prec.left(3, seq('Option', '[', $.integer, ']')),
      'BLOB'
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
    datetime: $ => seq($.date, $.time),

    comment: $ => token(choice(
      seq('//', /.*/),
      seq(
        '/*',
        /[^*]*\*+([^/*][^*]*\*+)*/,
        '/'
      )
    ))
  }
});

// Helper function to handle repeated elements separated by a delimiter
function sepBy1(delimiter, rule) {
  return seq(rule, repeat(seq(delimiter, rule)));
}
