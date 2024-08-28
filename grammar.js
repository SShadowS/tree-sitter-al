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
      $.xmlport_object,
      $.interface_object,
      $.dotnet_package_object,
      $.enum_extension_object,
      $.query_extension_object,
      $.report_layout_object,
      $.workflow_object,
      $.api_page_object,
      $.api_query_object
    ),

    interface_object: $ => seq(
      'interface',
      field('name', choice($.identifier, $.string)),
      '{',
      repeat($._interface_element),
      '}'
    ),

    _interface_element: $ => choice(
      $.method,
      $.property
    ),

    method: $ => seq(
      optional('local'),
      'procedure',
      field('name', $.identifier),
      '(',
      optional($._parameter_list),
      ')',
      field('return_type', optional(seq(':', $._type))),
      ';'
    ),

    xmlport_object: $ => seq(
      'xmlport',
      field('id', $.integer),
      field('name', choice($.identifier, $.string)),
      '{',
      repeat($._xmlport_element),
      '}'
    ),

    interface_object: $ => seq(
      'interface',
      field('name', choice($.identifier, $.string)),
      '{',
      repeat($._interface_element),
      '}'
    ),

    _interface_element: $ => choice(
      $.method
    ),

    method: $ => seq(
      'method',
      field('name', $.identifier),
      '(',
      optional($._parameter_list),
      ')',
      field('return_type', optional(seq(':', $._type))),
      ';'
    ),

    dotnet_package_object: $ => seq(
      'dotnetpackage',
      field('name', choice($.identifier, $.string)),
      '{',
      repeat($._dotnet_package_element),
      '}'
    ),

    _dotnet_package_element: $ => choice(
      $.assembly
    ),

    assembly: $ => seq(
      'assembly',
      '(',
      field('name', $.string),
      ')',
      ';'
    ),

    enum_extension_object: $ => seq(
      'enumextension',
      field('id', $.integer),
      field('name', choice($.identifier, $.string)),
      'extends',
      field('base_enum', choice($.identifier, $.string)),
      '{',
      repeat($._enum_extension_element),
      '}'
    ),

    _enum_extension_element: $ => choice(
      $.value
    ),

    query_extension_object: $ => seq(
      'queryextension',
      field('id', $.integer),
      field('name', choice($.identifier, $.string)),
      'extends',
      field('base_query', choice($.identifier, $.string)),
      '{',
      repeat($._query_extension_element),
      '}'
    ),

    _query_extension_element: $ => choice(
      $.elements,
      $.property
    ),

    report_layout_object: $ => seq(
      'reportlayout',
      field('id', $.integer),
      field('name', choice($.identifier, $.string)),
      '{',
      repeat($._report_layout_element),
      '}'
    ),

    _report_layout_element: $ => choice(
      $.property,
      $.layout
    ),

    workflow_object: $ => seq(
      'workflow',
      field('name', choice($.identifier, $.string)),
      '{',
      repeat($._workflow_element),
      '}'
    ),

    _workflow_element: $ => choice(
      $.property,
      $.step
    ),

    step: $ => seq(
      'step',
      '(',
      field('id', $.integer),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    api_page_object: $ => seq(
      'page',
      field('id', $.integer),
      field('name', choice($.identifier, $.string)),
      'API',
      '{',
      repeat($._api_page_element),
      '}'
    ),

    _api_page_element: $ => choice(
      $.property,
      $.layout,
      $.actions
    ),

    api_query_object: $ => seq(
      'query',
      field('id', $.integer),
      field('name', choice($.identifier, $.string)),
      'API',
      '{',
      repeat($._api_query_element),
      '}'
    ),

    _api_query_element: $ => choice(
      $.property,
      $.elements
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
      $.onaftergetcurrrecord_trigger,
      $.onclosepage_trigger,
      $.ondeleterecord_trigger,
      $.onfindrecord_trigger,
      $.oninit_trigger,
      $.oninsertrecord_trigger,
      $.onmodifyrecord_trigger,
      $.onnewrecord_trigger,
      $.onnextrecord_trigger,
      $.onopenpage_trigger,
      $.onpagebackgroundtaskcompleted_trigger,
      $.onpagebackgroundtaskerror_trigger,
      $.onqueryclosepage_trigger
    ),

    // OnQueryClosePage trigger for pages
    // This trigger runs when a page closes and before the OnClosePage trigger executes
    // It can be used to perform actions or validations before the page is closed
    // If the trigger returns false, the page closing is canceled
    onqueryclosepage_trigger: $ => seq(
      'trigger',
      'OnQueryClosePage',
      '(',
      'CloseAction',
      ':',
      'Action',
      ')',
      ':',
      'Boolean',
      field('body', $.code_block)
    ),

    // OnPageBackgroundTaskError trigger for pages
    // This trigger runs when an error occurs in a page background task
    // It's used to handle errors that occur during asynchronous operations on pages
    // The trigger receives the task ID, error code, error text, error call stack, and a boolean to indicate if the error has been handled
    onpagebackgroundtaskerror_trigger: $ => seq(
      'trigger',
      'OnPageBackgroundTaskError',
      '(',
      'TaskId',
      ':',
      'Integer',
      ';',
      'ErrorCode',
      ':',
      'Text',
      ';',
      'ErrorText',
      ':',
      'Text',
      ';',
      'ErrorCallStack',
      ':',
      'Text',
      ';',
      'var',
      'IsHandled',
      ':',
      $.Boolean,
      ')',
      field('body', $.code_block)
    ),

    // OnPageBackgroundTaskCompleted trigger for pages
    // This trigger runs after a page background task has successfully completed
    // It's used to handle the results of asynchronous operations on pages
    // The trigger receives the task ID and a dictionary of results from the completed task
    onpagebackgroundtaskcompleted_trigger: $ => seq(
      'trigger',
      'OnPageBackgroundTaskCompleted',
      '(',
      'TaskId',
      ':',
      'Integer',
      ';',
      'Results',
      ':',
      'Dictionary of [Text,Text]',
      ')',
      field('body', $.code_block)
    ),

    // OnOpenPage trigger for pages
    // This trigger runs after a page is initialized and opened
    // It's commonly used to set up initial values, change dynamic properties,
    // or perform actions before the page is displayed to the user
    onopenpage_trigger: $ => seq(
      'trigger',
      'OnOpenPage',
      '(',
      ')',
      field('body', $.code_block)
    ),

    // OnNextRecord trigger for pages
    // This trigger determines the next record to be displayed on a page
    // It's called when the user navigates between records (e.g., using Next or Previous)
    // The trigger can be used to implement custom navigation logic
    onnextrecord_trigger: $ => seq(
      'trigger',
      'OnNextRecord',
      '(',
      'Steps',
      ':',
      'Integer',
      ')',
      ':',
      'Integer',
      field('body', $.code_block)
    ),

    // OnNewRecord trigger for pages
    // This trigger runs after a new record is initialized, but before it is inserted as a record in the table
    // It's used to initialize a new record or other variables on the page before users enter any data
    onnewrecord_trigger: $ => seq(
      'trigger',
      'OnNewRecord',
      '(',
      'BelowxRec',
      ':',
      'Boolean',
      ')',
      field('body', $.code_block)
    ),

    // OnModifyRecord trigger for pages
    // This trigger runs before a record is modified in the table
    // It can be used to perform custom actions or validations before the modification occurs
    // The modification is canceled if the trigger returns false
    onmodifyrecord_trigger: $ => seq(
      'trigger',
      'OnModifyRecord',
      '(',
      ')',
      ':',
      'Boolean',
      field('body', $.code_block)
    ),

    // OnInsertRecord trigger for pages
    // This trigger runs before a new record is inserted into the table
    // It can be used to perform custom actions or validations before the insertion occurs
    // The insertion is canceled if the trigger returns false
    oninsertrecord_trigger: $ => seq(
      'trigger',
      'OnInsertRecord',
      '(',
      'BelowxRec',
      ':',
      'Boolean',
      ')',
      ':',
      'Boolean',
      field('body', $.code_block)
    ),

    // OnInit trigger for pages
    // This trigger runs immediately after the page variables are initialized and the page is loaded
    // It's used to set up initial values or perform actions before the page is displayed to the user
    // The trigger cannot be used to access controls on the page
    oninit_trigger: $ => seq(
      'trigger',
      'OnInit',
      '(',
      ')',
      field('body', $.code_block)
    ),

    // OnFindRecord trigger for pages
    // This trigger overrides the default page behavior and enables you to specify which record
    // you want to display when the page opens.
    // It's called when the page is opened and when the user navigates between records.
    onfindrecord_trigger: $ => seq(
      'trigger',
      'OnFindRecord',
      '(',
      'Which',
      ':',
      'Text',
      ')',
      ':',
      'Boolean',
      field('body', $.code_block)
    ),

    // OnDeleteRecord trigger for pages
    // This trigger runs before a record is deleted from the table
    // It can be used to perform custom actions or validations before the deletion occurs
    // The deletion is canceled if the trigger returns false
    ondeleterecord_trigger: $ => seq(
      'trigger',
      'OnDeleteRecord',
      '(',
      ')',
      ':',
      'Boolean',
      field('body', $.code_block)
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

    // OnClosePage trigger for pages
    // This trigger runs when a page is about to close
    // It's called after the OnQueryClosePage trigger (if it exists)
    // It can be used to perform cleanup operations or final checks before the page is closed
    onclosepage_trigger: $ => seq(
      'trigger',
      'OnClosePage',
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
      $.Boolean,
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
      $.Boolean,
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
        field('value', choice($.string, $.boolean_literal, $.integer)),
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
      $.fields,
      $.keys,
      $.table_property,
      $.procedure,
      $.trigger,
      $.ondelete_trigger,
      $.oninsert_trigger,
      $.onmodify_trigger,
      $.onrename_trigger
    ),

    fields: $ => seq(
      'fields',
      '{',
      repeat($.field),
      '}'
    ),

    keys: $ => seq(
      'keys',
      '{',
      repeat($.key),
      '}'
    ),

    key: $ => seq(
      'key',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($.key_field),
      '}'
    ),

    key_field: $ => $.identifier,

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

    // Generic property structure
    property: $ => seq(
      field('name', $.identifier),
      '=',
      field('value', $._value),
      ';'
    ),

    // Object-specific property rules
    table_property: $ => choice(
      // Table-specific properties will be added here
      $.access_property
    ),

    field_property: $ => choice(
      // Field-specific properties will be added here
      $.access_property,
      $.access_by_permission_property
    ),

    page_property: $ => choice(
      // Page-specific properties will be added here
      $.about_text_property,
      $.about_text_ml_property,
      $.about_title_property,
      $.about_title_ml_property,
      $.access_by_permission_property,
      $.additional_search_terms_property,
      $.additional_search_terms_ml_property,
      $.allowed_file_extensions_property
    ),

    // AllowedFileExtensions Property
    // Specifies the list of allowed file extensions for Page File Upload Actions.
    // This property restricts the types of files that can be uploaded.
    allowed_file_extensions_property: $ => seq(
      'AllowedFileExtensions',
      '=',
      field('value', $.array_value),
      ';'
    ),

    // AdditionalSearchTermsML Property
    // Specifies search terms (words and phrases) for the page in different languages.
    // These terms are used by the search feature in the Web client and mobile apps.
    additional_search_terms_ml_property: $ => seq(
      'AdditionalSearchTermsML',
      '=',
      field('value', $.multilanguage_string_literal),
      ';'
    ),

    // AdditionalSearchTerms Property
    // Specifies search terms (words and phrases) for the page.
    // These terms are used by the search feature in the Web client and mobile apps.
    additional_search_terms_property: $ => seq(
      'AdditionalSearchTerms',
      '=',
      field('value', $.string_literal),
      optional(seq(
        ',',
        choice(
          seq('Locked', '=', field('locked', $.boolean_literal)),
          seq('Comment', '=', field('comment', $.string_literal)),
          seq('MaxLength', '=', field('max_length', $.integer))
        )
      )),
      ';'
    ),

    // AccessByPermission Property
    // Sets a value for a table field or UI element that determines the permission mask for an object
    // that a user must have to see and access the related page fields or UI element in the client.
    access_by_permission_property: $ => seq(
      'AccessByPermission',
      '=',
      field('value', $.access_by_permission_value),
      ';'
    ),

    access_by_permission_value: $ => seq(
      field('object_type', $.identifier),
      field('object_name', $.identifier),
      '=',
      field('permission_type', $.access_by_permission_type)
    ),

    access_by_permission_type: $ => choice('R', 'I', 'M', 'D', 'X'),

    // Access Property
    // Sets the object accessibility level, which controls whether the object can be used from other code in the same module or other modules
    access_property: $ => seq(
      'Access',
      '=',
      field('value', choice('Public', 'Internal', 'Protected', 'Local')),
      ';'
    ),

    // AboutTitle Property
    // Sets the large-font title that appears in a teaching tip in the UI
    // Used on Page objects and their controls (actions, fields, parts, etc.)
    about_title_property: $ => seq(
      'AboutTitle',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // AboutTitleML Property
    // Sets the large-font title that appears in a teaching tip in the UI, supporting multiple languages
    // Used on Page objects and their controls (actions, fields, parts, etc.)
    about_title_ml_property: $ => seq(
      'AboutTitleML',
      '=',
      field('value', $.multilanguage_string_literal),
      ';'
    ),

    // AboutText Property
    // Sets the body of text that appears in a teaching tip in the UI
    // Used on Page objects and their controls (actions, fields, parts, etc.)
    about_text_property: $ => seq(
      'AboutText',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // AboutTextML Property
    // Sets the body of text that appears in a teaching tip in the UI, supporting multiple languages
    // Used on Page objects and their controls (actions, fields, parts, etc.)
    about_text_ml_property: $ => seq(
      'AboutTextML',
      '=',
      field('value', $.multilanguage_string_literal),
      ';'
    ),

    // Multi-language string literal
    multilanguage_string_literal: $ => seq(
      repeat1(seq(
        field('language_code', $.identifier),
        '=',
        field('text', $.string_literal),
        optional(',')
      ))
    ),

    report_property: $ => choice(
      // Report-specific properties will be added here
      $.additional_search_terms_property,
      $.additional_search_terms_ml_property
    ),

    xmlport_property: $ => choice(
      // XMLport-specific properties will be added here
    ),

    query_property: $ => choice(
      // Query-specific properties will be added here
    ),

    codeunit_property: $ => choice(
      // Codeunit-specific properties will be added here
      $.access_property,
      $.subtype_property
    ),

    // Subtype Property for codeunits
    subtype_property: $ => seq(
      'Subtype',
      '=',
      field('value', choice('Install', 'Upgrade', 'Test')),
      ';'
    ),

    enum_property: $ => choice(
      // Enum-specific properties will be added here
      $.access_property
    ),

    enum_value_property: $ => choice(
      // Enum value-specific properties will be added here
    ),

    permission_set_property: $ => choice(
      // Permission set-specific properties will be added here
      $.access_property
    ),

    query_property: $ => choice(
      // Query-specific properties will be added here
      $.access_property
    ),

    interface_property: $ => choice(
      // Interface-specific properties will be added here
      $.access_property
    ),

    permission_set_property: $ => choice(
      // Permission set-specific properties will be added here
    ),

    profile_property: $ => choice(
      // Profile-specific properties will be added here
    ),

    page_customization_property: $ => choice(
      // Page customization-specific properties will be added here
      $.about_text_property,
      $.about_text_ml_property,
      $.about_title_property,
      $.about_title_ml_property
    ),

    page_extension_property: $ => choice(
      // Page extension-specific properties will be added here
      $.about_text_property,
      $.about_text_ml_property,
      $.about_title_property
    ),

    table_extension_property: $ => choice(
      // Table extension-specific properties will be added here
    ),

    report_extension_property: $ => choice(
      // Report extension-specific properties will be added here
    ),

    query_extension_property: $ => choice(
      // Query extension-specific properties will be added here
    ),

    enum_extension_property: $ => choice(
      // Enum extension-specific properties will be added here
    ),

    control_addin_property: $ => choice(
      // Control add-in-specific properties will be added here
    ),

    entitlement_property: $ => choice(
      // Entitlement-specific properties will be added here
    ),

    report_layout_property: $ => choice(
      // Report layout-specific properties will be added here
    ),

    workflow_property: $ => choice(
      // Workflow-specific properties will be added here
    ),

    _value: $ => choice(
      $._literal,
      $.identifier,
      $.array_value,
      $.object_value
    ),

    array_value: $ => seq(
      '[',
      optional(seq(
        $._value,
        repeat(seq(',', $._value))
      )),
      ']'
    ),

    object_value: $ => seq(
      '{',
      optional(seq(
        $.key_value_pair,
        repeat(seq(',', $.key_value_pair))
      )),
      '}'
    ),

    key_value_pair: $ => seq(
      field('key', choice($.string, $.identifier)),
      ':',
      field('value', $._value)
    ),

    string: $ => /"[^"]*"/,
    integer: $ => /\d+/,
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

    // Types
    _type: $ => choice(
      $.identifier,
      $.record_type,
      $.Boolean
    ),

    Boolean: $ => 'Boolean',

    // Action type for OnQueryClosePage trigger
    Action: $ => choice(
      'OK',
      'Cancel',
      'Yes',
      'No',
      'LookupOK',
      'LookupCancel'
    ),

    // TestPermissions enum
    TestPermissions: $ => choice(
      'Disabled',
      'Restrictive',
      'NonRestrictive',
      'InheritFromTestCodunit'
    ),

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
