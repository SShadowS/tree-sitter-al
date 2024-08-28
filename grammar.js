module.exports = grammar({
  name: 'al',

  extras: $ => [
    /\s/
  ],

  rules: {
    source_file: $ => repeat1(choice(
      $._declaration,
      $.comment
    )),

    comment: $ => choice(
      seq('//', /.*/),
      seq(
        '/*',
        /[^*]*\*+([^/*][^*]*\*+)*/,
        '/'
      )
    ),

    _declaration: $ => choice(
      $.table_object,
      $.table_extension_object,
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
      $.report_extension_object,
      $.report_object,
      $.enum_object,
      $.xmlport_object
      // Other object types can be added here in the future
    ),

    xmlport_object: $ => seq(
      'xmlport',
      field('id', $.integer),
      field('name', choice($.identifier, $.string)),
      '{',
      repeat($._xmlport_element),
      '}'
    ),

    _xmlport_element: $ => choice(
      $.property,
      $.schema,
      $.requestpage
    ),

    schema: $ => seq(
      'schema',
      '{',
      repeat($._schema_element),
      '}'
    ),

    _schema_element: $ => choice(
      $.textelement,
      $.tableelement,
      $.fieldelement,
      $.fieldattribute
    ),

    textelement: $ => seq(
      'textelement',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($._schema_element),
      '}'
    ),

    tableelement: $ => seq(
      'tableelement',
      '(',
      field('variable', $.identifier),
      ';',
      field('table', $.identifier),
      ')',
      '{',
      repeat($._schema_element),
      '}'
    ),

    fieldelement: $ => seq(
      'fieldelement',
      '(',
      field('name', $.identifier),
      ';',
      field('field', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    fieldattribute: $ => seq(
      'fieldattribute',
      '(',
      field('name', $.identifier),
      ';',
      field('field', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    enum_object: $ => seq(
      'enum',
      field('id', $.integer),
      field('name', choice($.identifier, $.string)),
      '{',
      repeat($._enum_element),
      '}'
    ),

    _enum_element: $ => choice(
      $.property,
      $.value
    ),

    value: $ => seq(
      'value',
      '(',
      field('id', $.integer),
      ';',
      field('name', $.string),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    table_extension_object: $ => seq(
      'tableextension',
      field('id', $.integer),
      field('name', choice($.identifier, $.string)),
      'extends',
      field('base_table', choice($.identifier, $.string)),
      '{',
      repeat($._table_extension_element),
      '}'
    ),

    _table_extension_element: $ => choice(
      $.fields,
      $.property,
      $.procedure,
      $.trigger
    ),

    fields: $ => seq(
      'fields',
      '{',
      repeat($.field),
      '}'
    ),

    report_object: $ => seq(
      'report',
      field('id', $.integer),
      field('name', choice($.identifier, $.string)),
      '{',
      repeat($._report_element),
      '}'
    ),

    _report_element: $ => choice(
      $.property,
      $.dataset,
      $.requestpage,
      $.rendering,
      $.labels,
      $.trigger
    ),

    report_extension_object: $ => seq(
      'reportextension',
      field('id', $.integer),
      field('name', choice($.identifier, $.string)),
      'extends',
      field('base_report', choice($.identifier, $.string)),
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
      field('name', choice($.identifier, $.string)),
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
      field('name', choice($.identifier, $.string)),
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
      field('name', choice($.identifier, $.string)),
      'extends',
      field('base_permission_set', choice($.identifier, $.string)),
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
      field('name', choice($.identifier, $.string)),
      '{',
      repeat($._page_element),
      '}'
    ),

    _page_element: $ => choice(
      $.property,
      $.layout,
      $.actions,
      $.views,
      $.onaftergetcurrrecord_trigger
    ),

    // OnAfterGetCurrRecord trigger for pages
    // This trigger runs after the current record is retrieved from the table
    // It's called once when the page is opened, and again whenever the current record changes
    // It's commonly used for updating page controls or performing actions based on the current record
    onaftergetcurrrecord_trigger: $ => seq(
      'trigger',
      'OnAfterGetCurrRecord',
      '(',
      ')',
      field('body', $.code_block)
    ),

    page_extension_object: $ => seq(
      'pageextension',
      field('id', $.integer),
      field('name', choice($.identifier, $.string)),
      'extends',
      field('base_page', choice($.identifier, $.string)),
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

    // OnAfterGetCurrRecord trigger for pages
    // This trigger runs after the current record is retrieved from the table
    // It's called once when the page is opened, and again whenever the current record changes
    // It's commonly used for updating page controls or performing actions based on the current record
    onaftergetcurrrecord_trigger: $ => seq(
      'trigger',
      'OnAfterGetCurrRecord',
      '(',
      ')',
      field('body', $.code_block)
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
      field('name', choice($.identifier, $.string)),
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
      field('name', choice($.identifier, $.string)),
      '{',
      repeat($._codeunit_element),
      '}'
    ),

    _codeunit_element: $ => choice(
      $.property,
      $.trigger,
      $.procedure,
      $.onaftertestrun_trigger,
      $.onbeforetestrun_trigger,
      $.oncheckpreconditionspercompany_trigger,
      $.oncheckpreconditionsperdatabase_trigger,
      $.oninstallapppercompany_trigger,
      $.oninstallappperdatabase_trigger,
      $.onrun_trigger,
      $.onupgradepercompany_trigger,
      $.onupgradeperdatabase_trigger,
      $.onvalidateupgradepercompany_trigger,
      $.onvalidateupgradeperdatabase_trigger
      // Other codeunit elements can be added here
    ),

    // OnValidateUpgradePerDatabase trigger for upgrade codeunits
    // This trigger runs after an extension upgrade, once for the entire database
    // It is used to check that the upgrade was successful
    // If an error occurs during runtime, the extension upgrade is canceled
    onvalidateupgradeperdatabase_trigger: $ => seq(
      'trigger',
      'OnValidateUpgradePerDatabase',
      '(',
      ')',
      field('body', $.code_block)
    ),

    // OnValidateUpgradePerCompany trigger for upgrade codeunits
    // This trigger runs after an extension upgrade, once for each company in the database
    // It is used to check that the upgrade was successful
    // If an error occurs during runtime, the extension upgrade is canceled
    onvalidateupgradepercompany_trigger: $ => seq(
      'trigger',
      'OnValidateUpgradePerCompany',
      '(',
      ')',
      field('body', $.code_block)
    ),

    // OnUpgradePerDatabase trigger for upgrade codeunits
    // This trigger runs during the upgrade of an extension
    // It is executed once for the entire database
    onupgradeperdatabase_trigger: $ => seq(
      'trigger',
      'OnUpgradePerDatabase',
      '(',
      ')',
      field('body', $.code_block)
    ),

    // OnUpgradePerCompany trigger for upgrade codeunits
    // This trigger runs during the upgrade of an extension
    // It is executed once for each company in the database
    onupgradepercompany_trigger: $ => seq(
      'trigger',
      'OnUpgradePerCompany',
      '(',
      ')',
      field('body', $.code_block)
    ),

    // OnRun trigger for codeunits
    // This trigger runs when a codeunit is executed
    // It's the entry point for the codeunit's main logic
    onrun_trigger: $ => seq(
      'trigger',
      'OnRun',
      '(',
      ')',
      field('body', $.code_block)
    ),

    // OnInstallAppPerDatabase trigger for install codeunits
    // This trigger runs during the installation or reinstallation of an extension
    // It is executed once for the entire database
    oninstallappperdatabase_trigger: $ => seq(
      'trigger',
      'OnInstallAppPerDatabase',
      '(',
      ')',
      field('body', $.code_block)
    ),

    // OnInstallAppPerCompany trigger for install codeunits
    // This trigger runs during the installation or reinstallation of an extension
    // It is executed once for each company in the database
    oninstallapppercompany_trigger: $ => seq(
      'trigger',
      'OnInstallAppPerCompany',
      '(',
      ')',
      field('body', $.code_block)
    ),

    // OnCheckPreconditionsPerDatabase trigger for upgrade codeunits
    // This trigger runs before an extension upgrade, once for the entire database
    // It's used to check if certain requirements are met before running the upgrade
    oncheckpreconditionsperdatabase_trigger: $ => seq(
      'trigger',
      'OnCheckPreconditionsPerDatabase',
      '(',
      ')',
      field('body', $.code_block)
    ),

    // OnCheckPreconditionsPerCompany trigger for upgrade codeunits
    // This trigger runs before an extension upgrade, once for each company in the database
    // It's used to check if certain requirements are met before running the upgrade
    oncheckpreconditionspercompany_trigger: $ => seq(
      'trigger',
      'OnCheckPreconditionsPerCompany',
      '(',
      ')',
      field('body', $.code_block)
    ),

    // OnAfterTestRun trigger for test runner codeunits
    // This trigger runs after each test in a test codeunit has been executed
    onaftertestrun_trigger: $ => seq(
      'trigger',
      'OnAfterTestRun',
      '(',
      'CodeunitId',
      ':',
      'Integer',
      ';',
      'CodeunitName',
      ':',
      'Text',
      ';',
      'FunctionName',
      ':',
      'Text',
      ';',
      'Permissions',
      ':',
      'TestPermissions',
      ';',
      'Success',
      ':',
      'Boolean',
      ')',
      field('body', $.code_block)
    ),

    // OnBeforeTestRun trigger for test runner codeunits
    // This trigger runs before each test in a test codeunit is executed
    onbeforetestrun_trigger: $ => seq(
      'trigger',
      'OnBeforeTestRun',
      '(',
      'CodeunitId',
      ':',
      'Integer',
      ';',
      'CodeunitName',
      ':',
      'Text',
      ';',
      'FunctionName',
      ':',
      'Text',
      ';',
      'Permissions',
      ':',
      'TestPermissions',
      ')',
      ':',
      'Boolean',
      field('body', $.code_block)
    ),

    dataset: $ => seq(
      'dataset',
      '{',
      repeat($._dataset_element),
      '}'
    ),

    _dataset_element: $ => choice(
      $.dataitem
    ),

    requestpage: $ => seq(
      'requestpage',
      '{',
      repeat($._requestpage_element),
      '}'
    ),

    _requestpage_element: $ => choice(
      $.layout,
      $.actions
    ),

    rendering: $ => seq(
      'rendering',
      '{',
      repeat($.layout),
      '}'
    ),

    labels: $ => seq(
      'labels',
      '{',
      repeat($.label),
      '}'
    ),

    label: $ => seq(
      field('name', $.identifier),
      '=',
      field('value', $.string),
      optional(seq(',', $.label_properties)),
      ';'
    ),

    label_properties: $ => repeat1(
      seq(
        field('property', $.identifier),
        '=',
        field('value', choice($.string, $.boolean, $.integer)),
        optional(',')
      )
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
      $.assignment_statement,
      $.if_statement,
      $.case_statement,
      $.for_statement,
      $.while_statement,
      $.repeat_statement,
      $.procedure_call_statement,
      $.exit_statement,
      $.with_statement
    ),

    assignment_statement: $ => seq(
      field('variable', $.identifier),
      ':=',
      field('value', $._expression),
      ';'
    ),

    if_statement: $ => seq(
      'if',
      field('condition', $._expression),
      'then',
      field('then_body', $.code_block),
      optional(seq('else', field('else_body', $.code_block)))
    ),

    case_statement: $ => seq(
      'case',
      field('expression', $._expression),
      'of',
      repeat1($.case_option),
      optional(seq('else', field('else_body', $.code_block))),
      'end'
    ),

    case_option: $ => seq(
      field('value', $._literal),
      ':',
      field('body', $.code_block),
      ';'
    ),

    for_statement: $ => seq(
      'for',
      field('variable', $.identifier),
      ':=',
      field('start', $._expression),
      'to',
      field('end', $._expression),
      optional(seq('step', field('step', $._expression))),
      'do',
      field('body', $.code_block)
    ),

    while_statement: $ => seq(
      'while',
      field('condition', $._expression),
      'do',
      field('body', $.code_block)
    ),

    repeat_statement: $ => seq(
      'repeat',
      field('body', $.code_block),
      'until',
      field('condition', $._expression),
      ';'
    ),

    procedure_call_statement: $ => seq(
      field('procedure', $.identifier),
      '(',
      optional($._argument_list),
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
      field('body', $.code_block)
    ),

    _argument_list: $ => seq(
      $._expression,
      repeat(seq(',', $._expression))
    ),

    _expression: $ => choice(
      $._literal,
      $.identifier,
      $.binary_expression,
      $.unary_expression,
      $.parenthesized_expression,
      $.function_call_expression,
      $.member_access_expression,
      $.array_access_expression,
      $.ternary_expression
    ),

    binary_expression: $ => prec.left(1, seq(
      field('left', $._expression),
      field('operator', $._operator),
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

    function_call_expression: $ => prec(3, seq(
      field('function', $.identifier),
      '(',
      optional($._argument_list),
      ')'
    )),

    member_access_expression: $ => prec(4, seq(
      field('object', $._expression),
      '.',
      field('member', $.identifier)
    )),

    array_access_expression: $ => prec(4, seq(
      field('array', $._expression),
      '[',
      field('index', $._expression),
      ']'
    )),

    ternary_expression: $ => prec.right(0, seq(
      field('condition', $._expression),
      '?',
      field('true_expression', $._expression),
      ':',
      field('false_expression', $._expression)
    )),

    table_object: $ => seq(
      'table',
      field('id', $.integer),
      field('name', choice($.identifier, $.string)),
      '{',
      repeat($._table_element),
      '}'
    ),

    _table_element: $ => choice(
      $.field,
      $.property,
      $.ondelete_trigger,
      $.oninsert_trigger,
      $.onmodify_trigger,
      $.onrename_trigger
      // Other table elements can be added here
    ),

    // OnDelete trigger for tables
    // This trigger runs when a user tries to delete a record from the table
    // It can be used to perform custom actions before the deletion occurs
    // or to prevent the deletion under certain conditions
    ondelete_trigger: $ => seq(
      'trigger',
      'OnDelete',
      '(',
      ')',
      field('body', $.code_block)
    ),

    // OnInsert trigger for tables
    // This trigger runs when a user inserts a new record into the table
    // It can be used to perform custom actions or validations before the insertion occurs
    // For example, initializing fields with default values or checking data integrity
    oninsert_trigger: $ => seq(
      'trigger',
      'OnInsert',
      '(',
      ')',
      field('body', $.code_block)
    ),

    // OnModify trigger for tables
    // This trigger runs when a user modifies an existing record in the table
    // It's executed before the default modify behavior, which checks field validity
    // It can be used for custom actions or validations before the modification is committed
    // Note: This trigger only runs automatically in the Web Client or when explicitly set to run in AL code
    onmodify_trigger: $ => seq(
      'trigger',
      'OnModify',
      '(',
      ')',
      field('body', $.code_block)
    ),

    // OnRename trigger for tables
    // This trigger runs when a user tries to rename a record in the table
    // It's executed after field validation and before the default renaming behavior
    // It can be used to perform custom actions or validations before the rename occurs
    // The record is not renamed if an error occurs in the trigger code
    // Note: This trigger runs automatically when the user changes a record's primary key field in a page from the Web Client
    onrename_trigger: $ => seq(
      'trigger',
      'OnRename',
      '(',
      ')',
      field('body', $.code_block)
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
      $._literal,
      $.identifier
    ),

    string: $ => /"[^"]*"/,
    integer: $ => /\d+/,
    boolean: $ => choice('true', 'false'),
    // Identifiers
    identifier: $ => /[a-zA-Z_][a-zA-Z0-9_]*/,

    // Literals
    _literal: $ => choice(
      $.number_literal,
      $.string_literal,
      $.boolean_literal,
      $.date_literal,
      $.time_literal,
      $.datetime_literal
    ),

    number_literal: $ => choice(
      /\d+/,
      /\d+\.\d+/
    ),

    string_literal: $ => /'[^']*'/,

    boolean_literal: $ => choice('true', 'false'),

    date_literal: $ => /\d{2}\.\d{2}\.\d{4}/,

    time_literal: $ => /\d{2}:\d{2}:\d{2}/,

    datetime_literal: $ => seq($.date_literal, $.time_literal),

    // Operators
    _operator: $ => choice(
      $.arithmetic_operator,
      $.comparison_operator,
      $.logical_operator,
      $.assignment_operator
    ),

    arithmetic_operator: $ => choice('+', '-', '*', '/', 'div', 'mod'),

    comparison_operator: $ => choice('=', '<>', '<', '>', '<=', '>='),

    logical_operator: $ => choice('and', 'or', 'not', 'xor'),

    assignment_operator: $ => ':='
  }
});
