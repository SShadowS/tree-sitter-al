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
      $.assembly,
      $.culture_property
    ),

    assembly: $ => seq(
      'assembly',
      '(',
      field('name', $.string),
      ')',
      ';'
    ),

    // Culture Property
    // Specifies the culture of the .NET assembly.
    // This property is used on Dot Net Assembly objects.
    culture_property: $ => seq(
      'Culture',
      '=',
      field('value', $.string_literal),
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
      $.requestpage,
      $.auto_calc_field_property,
      $.calc_fields_property
    ),

    // CalcFields Property
    // Sets a list of FlowFields to automatically calculate.
    // This property is used on XMLport Table Elements.
    calc_fields_property: $ => seq(
      'CalcFields',
      '=',
      field('value', $.identifier_list),
      ';'
    ),

    // Helper rule for a list of identifiers
    identifier_list: $ => seq(
      $.identifier,
      repeat(seq(',', $.identifier))
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
      $.value,
      $.enum_type
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

    enum_type: $ => seq(
      'type',
      field('name', $.identifier),
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
      $.trigger,
      $.auto_calc_field_property,
      $.data_item_link_property,
      $.report_column,
      $.report_layout
    ),

    report_column: $ => seq(
      'column',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    report_layout: $ => seq(
      'layout',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
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

    dataitem: $ => seq(
      'dataitem',
      '(',
      field('name', $.identifier),
      ';',
      field('table', $.identifier),
      ')',
      '{',
      repeat(choice($._dataitem_element, $.data_item_link_property)),
      '}'
    ),

    _dataitem_element: $ => choice(
      $.property,
      $.calc_fields_property,
      $.data_item_link_property,
      $.data_item_link_reference_property,
      $.data_item_table_view_property
    ),

    // DataItemLinkReference Property
    // Sets the parent data item to which a child (indented) data item is linked.
    // This property is used on Report DataItems and Query DataItems.
    data_item_link_reference_property: $ => seq(
      'DataItemLinkReference',
      '=',
      field('value', $.identifier),
      ';'
    ),

    // DataItemLink Property
    // Sets the link between two dataitems in a report or query.
    // This property is used on Report DataItems and Query DataItems.
    data_item_link_property: $ => seq(
      'DataItemLink',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // DataItemTableView Property
    // Sets the key on which to sort, the sort order, and the filters for the data item.
    // This property is used on Report Data Items.
    data_item_table_view_property: $ => seq(
      'DataItemTableView',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // CalcFields Property
    // Sets a list of FlowFields to automatically calculate.
    // This property is used on Report Data Items.
    calc_fields_property: $ => seq(
      'CalcFields',
      '=',
      field('value', $.identifier_list),
      ';'
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
      $.elements,
      $.query_type_property,
      $.about_title_property,
      $.about_text_property,
      $.context_sensitive_help_page_property,
      $.usage_category_property,
      $.data_access_intent_property,
      $.query_column,
      $.query_filter
    ),

    elements: $ => seq(
      'elements',
      '{',
      repeat($._query_data_item),
      '}'
    ),

    _query_data_item: $ => choice(
      $.dataitem,
      $.data_item_link_property,
      $.query_column,
      $.query_filter
    ),

    query_column: $ => seq(
      'column',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    query_filter: $ => seq(
      'filter',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    // New properties
    query_type_property: $ => seq(
      'QueryType',
      '=',
      field('value', choice('Normal', 'API')),
      ';'
    ),

    usage_category_property: $ => seq(
      'UsageCategory',
      '=',
      field('value', $.identifier),
      ';'
    ),

    data_access_intent_property: $ => seq(
      'DataAccessIntent',
      '=',
      field('value', choice('ReadOnly', 'ReadWrite')),
      ';'
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
      $.property,
      $.data_item_link_property,
      $.data_item_table_filter_property
    ),

    // DataItemTableFilter Property
    // Sets filters on fields of the underlying table of a query.
    // This property is used on Query Data Items.
    data_item_table_filter_property: $ => seq(
      'DataItemTableFilter',
      '=',
      field('value', $.string_literal),
      ';'
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

    data_item_link_property: $ => seq(
      'DataItemLink',
      '=',
      field('value', $.string_literal),
      ';'
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
      $.customizations,
      $.caption_ml_property
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
      $.permissions,
      $.caption_ml_property
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
      optional('API'),
      '{',
      repeat($._page_element),
      '}'
    ),

    _page_element: $ => choice(
      $.property,
      $.layout,
      $.actions,
      $.views,
      $.area,
      $.field_group,
      $.page_label,
      $.page_group,
      $.page_part,
      $.page_system_part,
      $.page_action,
      $.page_action_separator,
      $.page_action_group,
      $.page_custom_action,
      $.page_system_action,
      $.page_file_upload_action,
      $.page_view,
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

    field_group: $ => seq(
      'fieldgroup',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($.field),
      '}'
    ),

    page_label: $ => seq(
      'label',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    page_group: $ => seq(
      'group',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($._page_element),
      '}'
    ),

    page_part: $ => seq(
      'part',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    page_system_part: $ => seq(
      'systempart',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    page_action: $ => seq(
      'action',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    page_action_separator: $ => seq(
      'separator',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    page_action_group: $ => seq(
      'actiongroup',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($._page_element),
      '}'
    ),

    page_custom_action: $ => seq(
      'customaction',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    page_system_action: $ => seq(
      'systemaction',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    page_file_upload_action: $ => seq(
      'fileuploadaction',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    page_view: $ => seq(
      'view',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    area: $ => seq(
      'area',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($._area_element),
      '}'
    ),

    _area_element: $ => choice(
      $.group,
      $.part,
      $.systempart
    ),

    group: $ => seq(
      'group',
      '(',
      field('name', choice($.identifier, $.string)),
      ')',
      '{',
      repeat($._group_element),
      '}'
    ),

    _group_element: $ => choice(
      $.part,
      $.group
    ),

    part: $ => seq(
      'part',
      '(',
      field('name', choice($.identifier, $.string)),
      ';',
      field('part_name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    systempart: $ => seq(
      'systempart',
      '(',
      field('name', choice($.identifier, $.string)),
      ';',
      field('system_part_name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
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
      repeat(choice($.key_field, $.clustered_property)),
      '}'
    ),

    key_field: $ => $.identifier,

    // Clustered Property
    // Sets a value that indicates whether the key also defines the clustered index in the database.
    // This property is used on Table Keys.
    clustered_property: $ => seq(
      'Clustered',
      '=',
      field('value', $.boolean_literal),
      ';'
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
      $.access_property,
      $.caption_property,
      $.caption_ml_property,
      $.column_store_index_property,
      $.compression_type_property,
      $.data_caption_fields_property,
      $.data_classification_property,
      $.data_per_company_property,
      $.enabled_property,
      $.extensible_property,
      $.external_name_property
    ),

    // Enabled Property
    // Sets a value that indicates whether a table is enabled or disabled.
    // When disabled, the table cannot be accessed or modified.
    enabled_property: $ => seq(
      'Enabled',
      '=',
      field('value', choice($.boolean_literal, $.identifier)),
      ';'
    ),

    // ExtendedDatatype Property
    // Sets the extended data type of a control.
    // This property is used on Table Fields and Page Fields.
    extended_datatype_property: $ => seq(
      'ExtendedDatatype',
      '=',
      field('value', choice(
        'None',
        'PhoneNo',
        'URL',
        'EMail',
        'Ratio',
        'Masked',
        'Person',
        'Barcode',
        'RichContent'
      )),
      ';'
    ),

    // CaptionML Property
    // Sets the string that displays with the object, control, or other element in the user interface for multiple languages.
    // This property is used on various AL objects including Tables, Table Fields, Pages, Page Fields, and more.
    caption_ml_property: $ => seq(
      'CaptionML',
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

    // CompressionType Property
    // Specifies the compression type used for the table in SQL Server.
    // This property is only applicable to tables with TableType set to Normal.
    compression_type_property: $ => seq(
      'CompressionType',
      '=',
      field('value', choice('None', 'Row', 'Page', 'Unspecified')),
      ';'
    ),

    // ColumnStoreIndex Property
    // Sets the fields that are added to the ColumnStore index inside SQL Server.
    // This property is used on Table objects to improve performance for analytical queries on large tables.
    column_store_index_property: $ => seq(
      'ColumnStoreIndex',
      '=',
      field('value', $.identifier_list),
      ';'
    ),

    field_property: $ => choice(
      // Field-specific properties will be added here
      $.access_property,
      $.access_by_permission_property,
      $.allow_in_customizations_property,
      $.assist_edit_property,
      $.auto_format_expression_property,
      $.auto_format_type_property,
      $.auto_increment_property,
      $.blank_numbers_property,
      $.blank_zero_property,
      $.calc_formula_property,
      $.caption_property,
      $.caption_class_property,
      $.caption_ml_property,
      $.char_allowed_property,
      $.closing_dates_property,
      $.column_span_property,
      $.compressed_property,
      $.data_classification_property,
      $.date_formula_property,
      $.decimal_places_property,
      $.editable_property,
      $.enabled_property,
      $.extended_datatype_property,
      $.external_access_property,
      $.external_name_property
    ),

    // ExternalAccess Property
    // Specifies the type of access to the original table field in the external database.
    // This property is used on Table Fields.
    external_access_property: $ => seq(
      'ExternalAccess',
      '=',
      field('value', choice('Full', 'Insert', 'Modify', 'Read')),
      ';'
    ),

    // ExternalName Property
    // Specifies the name of the original table or field in the external database.
    // This property is used on Tables and Table Fields.
    external_name_property: $ => seq(
      'ExternalName',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // ColumnSpan Property
    // Sets the number of columns that a field spans in a Grid control.
    // This property is used on Page Labels and Page Fields.
    column_span_property: $ => seq(
      'ColumnSpan',
      '=',
      field('value', $.integer),
      ';'
    ),

    // Compressed Property
    // Sets a value that specifies whether a BLOB is compressed.
    // This property is used on Table Fields of BLOB Data Type.
    compressed_property: $ => seq(
      'Compressed',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // ClosingDates Property
    // Sets a value that determines whether users can enter a closing date in this field.
    // This property is used on Table Fields and Page Fields.
    closing_dates_property: $ => seq(
      'ClosingDates',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // CharAllowed Property
    // Sets the range of characters the user can enter into this field or control.
    // This property is used on Table Fields and Page Fields.
    char_allowed_property: $ => seq(
      'CharAllowed',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // Caption Property
    // Sets the string that is used to identify a control or other object in the user interface.
    // This property is used on various AL objects including Table Fields, Page Fields, and more.
    caption_property: $ => seq(
      'Caption',
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

    // CaptionML Property
    // Sets the string that displays with the object, control, or other element in the user interface for multiple languages.
    // This property is used on various AL objects including Tables, Table Fields, Pages, Page Fields, and more.
    caption_ml_property: $ => seq(
      'CaptionML',
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

    // CaptionML Property
    // Sets the string that displays with the object, control, or other element in the user interface for multiple languages.
    // This property is used on various AL objects including Tables, Table Fields, Pages, Page Fields, and more.
    caption_ml_property: $ => seq(
      'CaptionML',
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

    // CaptionML Property
    // Sets the string that displays with the object, control, or other element in the user interface for multiple languages.
    // This property is used on various AL objects including Tables, Table Fields, Pages, Page Fields, and more.
    caption_ml_property: $ => seq(
      'CaptionML',
      '=',
      field('value', $.multilanguage_string_literal),
      ';'
    ),

    // CaptionClass Property
    // Controls the caption that is used in the label of a field in a database table or in the label of a control on a page.
    // This property is used on Table Fields, Page Labels, and Page Fields.
    caption_class_property: $ => seq(
      'CaptionClass',
      '=',
      field('value', choice($.string_literal, $.identifier)),
      ';'
    ),

    // CalcFormula Property
    // Sets the Calculation formula for a FlowField.
    // This property is used on Table Fields to define how FlowFields are calculated.
    calc_formula_property: $ => seq(
      'CalcFormula',
      '=',
      field('value', $.calc_formula_value),
      ';'
    ),

    calc_formula_value: $ => choice(
      $.exist_formula,
      $.count_formula,
      $.sum_formula,
      $.average_formula,
      $.min_formula,
      $.max_formula,
      $.lookup_formula
    ),

    exist_formula: $ => seq(
      optional('-'),
      'Exist',
      '(',
      field('destination_table', $.identifier),
      optional($.where_clause),
      ')'
    ),

    count_formula: $ => seq(
      'Count',
      '(',
      field('destination_table', $.identifier),
      optional($.where_clause),
      ')'
    ),

    sum_formula: $ => seq(
      optional('-'),
      'Sum',
      '(',
      field('destination_table', $.identifier),
      '.',
      field('destination_field', $.identifier),
      optional($.where_clause),
      ')'
    ),

    average_formula: $ => seq(
      optional('-'),
      'Average',
      '(',
      field('destination_table', $.identifier),
      '.',
      field('destination_field', $.identifier),
      optional($.where_clause),
      ')'
    ),

    min_formula: $ => seq(
      'Min',
      '(',
      field('destination_table', $.identifier),
      '.',
      field('destination_field', $.identifier),
      optional($.where_clause),
      ')'
    ),

    max_formula: $ => seq(
      'Max',
      '(',
      field('destination_table', $.identifier),
      '.',
      field('destination_field', $.identifier),
      optional($.where_clause),
      ')'
    ),

    lookup_formula: $ => seq(
      'Lookup',
      '(',
      field('destination_table', $.identifier),
      '.',
      field('destination_field', $.identifier),
      optional($.where_clause),
      ')'
    ),

    where_clause: $ => seq(
      'WHERE',
      '(',
      $.table_filters,
      ')'
    ),

    table_filters: $ => seq(
      $.table_filter,
      repeat(seq(',', $.table_filter))
    ),

    table_filter: $ => seq(
      field('destination_field', $.identifier),
      '=',
      choice(
        $.const_filter,
        $.filter_filter,
        $.field_filter,
        $.upperlimit_field_filter,
        $.upperlimit_filter_field_filter
      )
    ),

    const_filter: $ => seq(
      'CONST',
      '(',
      field('value', $._literal),
      ')'
    ),

    filter_filter: $ => seq(
      'FILTER',
      '(',
      field('filter', $.string_literal),
      ')'
    ),

    field_filter: $ => seq(
      'FIELD',
      '(',
      field('source_field', $.identifier),
      ')'
    ),

    upperlimit_field_filter: $ => seq(
      'FIELD',
      '(',
      'UPPERLIMIT',
      '(',
      field('source_field', $.identifier),
      ')',
      ')'
    ),

    upperlimit_filter_field_filter: $ => seq(
      'FIELD',
      '(',
      'UPPERLIMIT',
      '(',
      'FILTER',
      '(',
      field('source_field', $.identifier),
      ')',
      ')',
      ')'
    ),

    // BlankZero Property
    // Indicates whether the system displays zeros (0) and No.
    // This property is used on Table Fields and Page Fields.
    blank_zero_property: $ => seq(
      'BlankZero',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // BlankNumbers Property
    // Sets whether the system will clear a range of numbers as it formats them.
    // This property is used on Table Fields and Page Fields.
    blank_numbers_property: $ => seq(
      'BlankNumbers',
      '=',
      field('value', choice('DontBlank', 'BlankNeg', 'BlankNegAndZero', 'BlankZero', 'BlankZeroAndPos', 'BlankPos')),
      ';'
    ),

    // AutoIncrement Property
    // Sets whether the field value should be automatically incremented.
    // This property is only applicable to Integer and BigInteger data types.
    auto_increment_property: $ => seq(
      'AutoIncrement',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // AutoFormatType Property
    // Sets a value that determines how data is formatted, together with the AL expression in the AutoFormatExpression Property.
    // Used on Table Fields, Page Fields, and Report Columns.
    auto_format_type_property: $ => seq(
      'AutoFormatType',
      '=',
      field('value', choice('1', '2', '3', '10', '11')),
      ';'
    ),

    // AutoFormatExpression Property
    // Sets an AL expression that specifies how to format data.
    // This property is used in conjunction with the AutoFormatType property
    // to determine how decimal data types are formatted.
    auto_format_expression_property: $ => seq(
      'AutoFormatExpression',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // AssistEdit Property
    // Sets assist-edit capabilities for a text box on a page field.
    // When set to true, it provides assist-edit capabilities and an AssistEdit button.
    assist_edit_property: $ => seq(
      'AssistEdit',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // AllowInCustomizations Property
    // Specifies whether this table field can be used as source expression for new page fields in page customizations.
    allow_in_customizations_property: $ => seq(
      'AllowInCustomizations',
      '=',
      field('value', choice('Always', 'Never')),
      ';'
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
      $.allowed_file_extensions_property,
      $.allow_multiple_files_property,
      $.analysis_mode_enabled_property,
      $.apigroup_property,
      $.apipublisher_property,
      $.apiversion_property,
      $.application_area_property,
      $.auto_split_key_property,
      $.caption_property,
      $.caption_class_property,
      $.caption_ml_property,
      $.card_page_id_property,
      $.change_tracking_allowed_property,
      $.context_sensitive_help_page_property,
      $.cuegroup_layout_property,
      $.custom_action_type_property,
      $.data_access_intent_property,
      $.data_caption_expression_property,
      $.data_caption_fields_property,
      $.data_classification_property,
      $.delayed_insert_property,
      $.delete_allowed_property,
      $.description_property,
      $.drilldown_property,
      $.drilldown_page_id_property,
      $.editable_property,
      $.ellipsis_property,
      $.enabled_property,
      $.entity_caption_property,
      $.entity_caption_ml_property,
      $.entity_name_property,
      $.entity_set_caption_property,
      $.entity_set_caption_ml_property,
      $.entity_set_name_property,
      $.extensible_property
    ),

    // DrillDownPageId Property
    // Sets the ID of the page to use as a drill-down.
    // This property is used on Table objects and Page Fields.
    drilldown_page_id_property: $ => seq(
      'DrillDownPageID',
      '=',
      field('value', choice($.integer, $.identifier)),
      ';'
    ),

    // DrillDown Property
    // Sets a drill-down for a field on a page.
    // This property is used on Page Fields.
    drilldown_property: $ => seq(
      'DrillDown',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // Editable Property
    // Sets a value that indicates whether a field, page, or control can be edited through the UI.
    // This property is used on Table Fields, Pages, Request Pages, Page Labels, Page Fields, Page Groups, Page System Parts, Page Chart Parts, and Page Parts.
    editable_property: $ => prec(1, seq(
      'Editable',
      '=',
      field('value', choice($.boolean_literal, $.identifier, $._expression)),
      ';'
    )),

    // DataCaptionExpression Property
    // Sets an AL expression that is evaluated and displayed to the left of the page caption.
    // This property is used on Page and Request Page objects.
    data_caption_expression_property: $ => seq(
      'DataCaptionExpression',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // CustomActionType Property
    // Sets the type of the custom action for Page Custom Actions.
    // This property determines the behavior of the custom action, such as triggering a Power Automate Flow.
    custom_action_type_property: $ => seq(
      'CustomActionType',
      '=',
      field('value', choice('Flow', 'FlowTemplate', 'FlowTemplateGallery')),
      ';'
    ),

    // ContextSensitiveHelpPage Property
    // Specifies the help topic to show when the user presses Help in the UI.
    // This property is used on Page, Request Page, and Query objects.
    context_sensitive_help_page_property: $ => seq(
      'ContextSensitiveHelpPage',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // CuegroupLayout Property
    // Specifies if the layout is wide for a Page Group.
    // This property is used on Page Group objects.
    cuegroup_layout_property: $ => seq(
      'CuegroupLayout',
      '=',
      field('value', choice('Wide')),
      ';'
    ),

    // ChangeTrackingAllowed Property
    // Sets a value that indicates whether the entity exposed through the OData API supports change tracking.
    // This property is used on Page objects.
    change_tracking_allowed_property: $ => seq(
      'ChangeTrackingAllowed',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // CardPageId Property
    // Sets the card page that is associated with items in the current list page.
    // This property is used on Page and Request Page objects.
    card_page_id_property: $ => seq(
      'CardPageID',
      '=',
      field('value', choice($.integer, $.identifier, $.string_literal)),
      ';'
    ),

    // ApplicationArea Property
    // Specifies which application areas the page is designed for.
    // This property determines the visibility of the page based on the user's assigned application areas.
    application_area_property: $ => seq(
      'ApplicationArea',
      '=',
      field('value', choice($.identifier, $.array_value)),
      ';'
    ),

    // AutoSplitKey Property
    // Sets whether a key is automatically created for a new record placed between the current record and the previous record.
    // This property is applicable to Page and Request Page objects.
    auto_split_key_property: $ => seq(
      'AutoSplitKey',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // APIVersion Property
    // Sets the version(s) of the API endpoint the page is exposed in.
    // This property can only be set if the PageType is set to API.
    apiversion_property: $ => seq(
      'APIVersion',
      '=',
      field('value', $.string_literal),
      optional(seq(',', $.string_literal)),
      ';'
    ),

    // APIVersion Property
    // Sets the version of the API endpoint that the page is exposed in.
    // This property can only be set if the PageType is set to API.
    apiversion_property: $ => seq(
      'APIVersion',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // APIPublisher Property
    // Sets the publisher of the API endpoint that the page is exposed in.
    // This property can only be set if the PageType is set to API.
    apipublisher_property: $ => seq(
      'APIPublisher',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // APIGroup Property
    // Sets the group of the API endpoint that the page is exposed in.
    // This property can only be set if the PageType is set to API.
    apigroup_property: $ => seq(
      'APIGroup',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // AnalysisModeEnabled Property
    // Sets a value that specifies whether analysis mode on the page is allowed.
    // When set to true, the Analyze switch is available at the top of the page.
    analysis_mode_enabled_property: $ => seq(
      'AnalysisModeEnabled',
      '=',
      field('value', $.boolean_literal),
      ';'
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

    // AllowMultipleFiles Property
    // Specifies if the action accepts multiple files for Page File Upload Actions.
    // When set to true, the action allows uploading multiple files at once.
    allow_multiple_files_property: $ => seq(
      'AllowMultipleFiles',
      '=',
      field('value', $.boolean_literal),
      ';'
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
      $.additional_search_terms_ml_property,
      $.allow_scheduling_property,
      $.auto_format_expression_property,
      $.auto_format_type_property,
      $.caption_property,
      $.caption_ml_property,
      $.data_access_intent_property,
      $.decimal_places_property,
      $.default_layout_property,
      $.default_rendering_layout_property,
      $.enable_external_assemblies_property,
      $.enable_external_images_property,
      $.enable_hyperlinks_property,
      $.excel_layout_property,
      $.excel_layout_multiple_data_sheets_property,
      $.execution_timeout_property,
      $.extensible_property
    ),

    // ExcelLayoutMultipleDataSheets Property
    // Sets whether an Excel layout will render to multiple data sheets or in a single sheet named Data.
    // This property is used on Report objects.
    excel_layout_multiple_data_sheets_property: $ => seq(
      'ExcelLayoutMultipleDataSheets',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // ExecutionTimeout Property
    // Sets the maximum time the report will run after which it is automatically terminated.
    // This property is used on Report objects.
    execution_timeout_property: $ => seq(
      'ExecutionTimeout',
      '=',
      field('value', $.time_literal),
      ';'
    ),

    // ExcelLayout Property
    // Sets the Excel layout that is used on a report and returns it as a data stream.
    // This property is used on Report objects and Report Extension objects.
    excel_layout_property: $ => seq(
      'ExcelLayout',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // EnableHyperlinks Property
    // Sets whether hyperlinks to URLs are allowed on reports.
    // This property is used on Report objects.
    enable_hyperlinks_property: $ => seq(
      'EnableHyperlinks',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // EnableExternalImages Property
    // Sets whether external images are allowed on a report.
    // This property is used on Report objects.
    enable_external_images_property: $ => seq(
      'EnableExternalImages',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // EnableExternalAssemblies Property
    // Sets whether external Microsoft .NET assemblies can be used on a report.
    // This property is used on Report objects.
    enable_external_assemblies_property: $ => seq(
      'EnableExternalAssemblies',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // DefaultRenderingLayout Property
    // Sets the default layout that should be used for this report.
    // This property is used on Report objects.
    default_rendering_layout_property: $ => seq(
      'DefaultRenderingLayout',
      '=',
      field('value', $.identifier),
      ';'
    ),

    // DefaultLayout Property
    // Specifies whether the report uses the built-in RDL, Word, or Excel report layout by default.
    // This property is used on Report objects.
    default_layout_property: $ => seq(
      'DefaultLayout',
      '=',
      field('value', choice('RDLC', 'Word', 'Excel')),
      ';'
    ),

    // AllowScheduling Property
    // Sets whether a report can be scheduled to run in the background.
    // When set to true, users can schedule the report to run at a specific time.
    allow_scheduling_property: $ => seq(
      'AllowScheduling',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    xmlport_property: $ => choice(
      // XMLport-specific properties will be added here
      $.auto_replace_property,
      $.auto_save_property,
      $.auto_update_property,
      $.caption_property,
      $.caption_ml_property,
      $.default_fields_validation_property,
      $.direction_property,
      $.encoding_property
    ),

    // Encoding Property
    // Sets a value that specifies which system is applied to the XMLport for character encoding.
    // This property is used on XMLport objects.
    encoding_property: $ => seq(
      'Encoding',
      '=',
      field('value', choice('UTF8', 'UTF16', 'ISO88592')),
      ';'
    ),

    // Direction Property
    // Sets the XMLport to import, export, or import and export data in XML format.
    // This property is used on XMLport objects.
    direction_property: $ => seq(
      'Direction',
      '=',
      field('value', choice('Import', 'Export', 'Both')),
      ';'
    ),

    // DefaultFieldsValidation Property
    // Sets a value that indicates whether fields are validated in an XMLport.
    // This property affects the default behavior of field validation for all fields in the XMLport.
    default_fields_validation_property: $ => seq(
      'DefaultFieldsValidation',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // AutoUpdate Property
    // Sets whether a record in the database with the same primary key as the record in the imported XMLport
    // is updated with values from the imported record.
    // This property is used on XMLport Table Elements.
    auto_update_property: $ => seq(
      'AutoUpdate',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // AutoSave Property
    // Sets whether imported records are automatically written to the table.
    // This property applies to new records that are inserted into the table and existing records that are modified.
    auto_save_property: $ => seq(
      'AutoSave',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // AutoReplace Property
    // Sets whether imported records automatically replace existing records with the same primary key.
    // This property is used on XMLport Table Elements.
    auto_replace_property: $ => seq(
      'AutoReplace',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    query_property: $ => choice(
      // Query-specific properties will be added here
    ),

    codeunit_property: $ => choice(
      // Codeunit-specific properties will be added here
      $.access_property,
      $.subtype_property,
      $.event_subscriber_instance_property
    ),

    // EventSubscriberInstance Property
    // Sets whether event subscriber methods in a codeunit are bound to a specific codeunit instance.
    // This property is used on Codeunit objects.
    event_subscriber_instance_property: $ => seq(
      'EventSubscriberInstance',
      '=',
      field('value', choice('Manual', 'StaticAutomatic')),
      ';'
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
      $.access_property,
      $.assignment_compatibility_property,
      $.assignment_compatibility_reason_property,
      $.default_implementation_property,
      $.extensible_property
    ),

    // Extensible Property
    // Sets whether the object can be extended.
    // This property is used on Table, Page, Report, and Enum objects.
    extensible_property: $ => seq(
      'Extensible',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // Extensible Property
    // Sets whether the enum can be extended by enum extensions.
    // This property is used on Enum objects.
    extensible_property: $ => seq(
      'Extensible',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // DefaultImplementation Property
    // Specifies the default implementer for the enum value if there is no explicit implementer set for the value.
    // This property is used on Enum objects.
    default_implementation_property: $ => seq(
      'DefaultImplementation',
      '=',
      field('interface', $.identifier),
      '=',
      field('implementation', $.identifier),
      ';'
    ),

    // AssignmentCompatibility Property
    // Sets whether an Enum can be assigned to from another Enum type.
    // This is intended for backwards compatibility when splitting existing Options into multiple Enums.
    assignment_compatibility_property: $ => seq(
      'AssignmentCompatibility',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // AssignmentCompatibilityReason Property
    // Sets a warning text that is shown when the Assignment Compatibility is used.
    // This property provides an explanation for why assignment compatibility is necessary.
    assignment_compatibility_reason_property: $ => seq(
      'AssignmentCompatibilityReason',
      '=',
      field('value', $.string_literal),
      ';'
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
      $.access_property,
      $.apigroup_property,
      $.apiversion_property,
      $.apipublisher_property,
      $.caption_property,
      $.caption_ml_property,
      $.column_filter_property,
      $.data_access_intent_property,
      $.data_item_link_property,
      $.entity_caption_property,
      $.entity_caption_ml_property,
      $.entity_name_property,
      $.entity_set_caption_property,
      $.entity_set_caption_ml_property,
      $.entity_set_name_property
    ),

    // DataItemLink Property
    // Sets the corresponding fields from two data items that are linked by the DataItemLinkReference Property.
    // This property is used on Report DataItems and Query DataItems.
    data_item_link_property: $ => seq(
      'DataItemLink',
      '=',
      field('value', $.data_item_link_value),
      ';'
    ),

    data_item_link_value: $ => seq(
      field('field', $.identifier),
      '=',
      'FIELD',
      '(',
      field('reference_field', $.identifier),
      ')'
    ),

    // ColumnFilter Property
    // Sets a filter on the column filter row of a query.
    // This property is used on Query Columns and Query Filters.
    column_filter_property: $ => seq(
      'ColumnFilter',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // APIVersion Property for queries
    // Sets the version(s) of the API endpoint the query is exposed in.
    // This property can only be set if the QueryType is set to API.
    // If not specified, the default value is 'beta'.
    apiversion_property: $ => seq(
      'APIVersion',
      '=',
      field('value', $.string_literal),
      optional(seq(',', $.string_literal)),
      ';'
    ),

    // APIPublisher Property for queries
    // Sets the publisher of the API endpoint that the query is exposed in.
    // This property can only be set if the QueryType is set to API.
    apipublisher_property: $ => seq(
      'APIPublisher',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // APIGroup Property for queries
    // Sets the group of the API endpoint that the query is exposed in.
    // This property can only be set if the QueryType is set to API.
    apigroup_property: $ => seq(
      'APIGroup',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // APIVersion Property for queries
    // Sets the version of the API endpoint that the query is exposed in.
    // This property can only be set if the QueryType is set to API.
    apiversion_property: $ => seq(
      'APIVersion',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    interface_property: $ => choice(
      // Interface-specific properties will be added here
      $.access_property
    ),

    permission_set_property: $ => choice(
      // Permission set-specific properties will be added here
      $.assignable_property,
      $.excluded_permission_sets_property
    ),

    // ExcludedPermissionSets Property
    // Sets the lists of other permission sets that are excluded in this permission set.
    // This property is used on Permission Set objects.
    excluded_permission_sets_property: $ => seq(
      'ExcludedPermissionSets',
      '=',
      field('value', $.identifier_list),
      ';'
    ),

    // Assignable Property
    // Sets whether the permission set can be assigned to a user.
    assignable_property: $ => seq(
      'Assignable',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // AutoCalcField Property
    // Sets whether FlowFields should be automatically calculated.
    // Used on XMLport Field Attributes, XMLport Field Elements, and Report Columns.
    auto_calc_field_property: $ => seq(
      'AutoCalcField',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    profile_property: $ => choice(
      // Profile-specific properties will be added here
      $.customizations_property,
      $.enabled_property
    ),

    // Enabled Property for profiles
    // Specifies whether the profile can be used by users or not.
    // This property is used on Profile objects.
    enabled_property: $ => seq(
      'Enabled',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // Customizations Property
    // Specifies the Page Customizations which are applied with this profile.
    // This property is used on Profile objects.
    customizations_property: $ => seq(
      'Customizations',
      '=',
      field('value', $.identifier_list),
      ';'
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
      $.excel_layout_property
    ),

    query_extension_property: $ => choice(
      // Query extension-specific properties will be added here
    ),

    enum_extension_property: $ => choice(
      // Enum extension-specific properties will be added here
    ),

    control_addin_property: $ => choice(
      // Control add-in-specific properties will be added here
      $.vertical_shrink_property,
      $.horizontal_shrink_property,
      $.minimum_height_property,
      $.minimum_width_property,
      $.maximum_height_property,
      $.maximum_width_property,
      $.vertical_stretch_property,
      $.horizontal_stretch_property,
      $.requested_height_property,
      $.requested_width_property
    ),

    // VerticalShrink Property
    // Sets whether the control add-in can shrink vertically.
    vertical_shrink_property: $ => seq(
      'VerticalShrink',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // HorizontalShrink Property
    // Sets whether the control add-in can shrink horizontally.
    horizontal_shrink_property: $ => seq(
      'HorizontalShrink',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // MinimumHeight Property
    // Sets the minimum height of the control add-in.
    minimum_height_property: $ => seq(
      'MinimumHeight',
      '=',
      field('value', $.integer),
      ';'
    ),

    // MinimumWidth Property
    // Sets the minimum width of the control add-in.
    minimum_width_property: $ => seq(
      'MinimumWidth',
      '=',
      field('value', $.integer),
      ';'
    ),

    // MaximumHeight Property
    // Sets the maximum height of the control add-in.
    maximum_height_property: $ => seq(
      'MaximumHeight',
      '=',
      field('value', $.integer),
      ';'
    ),

    // MaximumWidth Property
    // Sets the maximum width of the control add-in.
    maximum_width_property: $ => seq(
      'MaximumWidth',
      '=',
      field('value', $.integer),
      ';'
    ),

    // VerticalStretch Property
    // Sets whether the control add-in can stretch vertically.
    vertical_stretch_property: $ => seq(
      'VerticalStretch',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // HorizontalStretch Property
    // Sets whether the control add-in can stretch horizontally.
    horizontal_stretch_property: $ => seq(
      'HorizontalStretch',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // RequestedHeight Property
    // Sets the requested height of the control add-in.
    requested_height_property: $ => seq(
      'RequestedHeight',
      '=',
      field('value', $.integer),
      ';'
    ),

    // RequestedWidth Property
    // Sets the requested width of the control add-in.
    requested_width_property: $ => seq(
      'RequestedWidth',
      '=',
      field('value', $.integer),
      ';'
    ),

    // DataCaptionFields Property
    // Sets the fields that appear to the left of the caption on pages that display the contents of this table.
    // This property is used on Tables, Pages, and Request Pages.
    data_caption_fields_property: $ => seq(
      'DataCaptionFields',
      '=',
      field('value', $.identifier_list),
      ';'
    ),

    // DataAccessIntent Property
    // Sets the data access intent of the page, report, or query.
    // This property is used on Page, Report, and Query objects.
    data_access_intent_property: $ => seq(
      'DataAccessIntent',
      '=',
      field('value', choice('ReadOnly', 'ReadWrite')),
      ';'
    ),

    // DataClassification Property
    // Sets the data classification level for fields in a table.
    // This property is used on Table Fields.
    data_classification_property: $ => seq(
      'DataClassification',
      '=',
      field('value', choice(
        'CustomerContent',
        'EndUserIdentifiableInformation',
        'EndUserPseudonymousIdentifiers',
        'OrganizationIdentifiableInformation',
        'AccountData',
        'ToBeClassified'
      )),
      ';'
    ),

    // DelayedInsert Property
    // Sets a value that specifies whether a user must leave a record before it is inserted into the database.
    // This property is used on Page objects.
    delayed_insert_property: $ => seq(
      'DelayedInsert',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // DeleteAllowed Property
    // Sets a value that specifies whether users can delete records while using the page.
    // This property is used on Page and Request Page objects.
    delete_allowed_property: $ => seq(
      'DeleteAllowed',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // Description Property
    // Sets the description for internal use. This description does not appear to end-users.
    // This property is used on various AL objects including Codeunits, Tables, Pages, and more.
    description_property: $ => seq(
      'Description',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // DateFormula Property
    // Sets a date formula used to verify that the date the user enters is correct.
    // This property is used on Table Fields and Page Fields.
    // Note: This property is deprecated and it's recommended to use the DateFormula Data Type instead.
    date_formula_property: $ => seq(
      'DateFormula',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // DecimalPlaces Property
    // Sets display and storage requirements for the Decimal Data Type.
    // This property is used on Table Fields, Page Fields, and Report Columns.
    decimal_places_property: $ => seq(
      'DecimalPlaces',
      '=',
      field('value', $.decimal_places_value),
      ';'
    ),

    decimal_places_value: $ => choice(
      $.integer,
      seq($.integer, ':', $.integer)
    ),

    // Ellipsis Property
    // Sets a value that specifies whether an ellipsis (...) is appended to the caption on a command button or menu item.
    // This property is used on Page Actions and Page Custom Actions.
    ellipsis_property: $ => seq(
      'Ellipsis',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // EntityCaption Property
    // Sets the caption of the entity.
    // This property is used on Page and Query objects.
    entity_caption_property: $ => seq(
      'EntityCaption',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // EntityCaptionML Property
    // Sets the caption of the entity in multiple languages.
    // This property is used on Page and Query objects.
    entity_caption_ml_property: $ => seq(
      'EntityCaptionML',
      '=',
      field('value', $.multilanguage_string_literal),
      ';'
    ),

    // EntityName Property
    // Sets the singular entity name with which the page is exposed in the API endpoint.
    // This property is used on Page and Query objects.
    entity_name_property: $ => seq(
      'EntityName',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // EntitySetCaption Property
    // Sets the caption of a set of entities.
    // This property is used on Page and Query objects.
    entity_set_caption_property: $ => seq(
      'EntitySetCaption',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // EntitySetCaptionML Property
    // Sets the caption of a set of entities in multiple languages.
    // This property is used on Page and Query objects.
    entity_set_caption_ml_property: $ => seq(
      'EntitySetCaptionML',
      '=',
      field('value', $.multilanguage_string_literal),
      ';'
    ),

    // EntitySetName Property
    // Sets the plural entity name with which the page or query is exposed in the API endpoint.
    // This property is used on Page and Query objects.
    entity_set_name_property: $ => seq(
      'EntitySetName',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // DataPerCompany Property
    // Sets a value that indicates whether the table data applies to all companies in the database or only the current company.
    // This property is used on Table objects.
    data_per_company_property: $ => seq(
      'DataPerCompany',
      '=',
      field('value', $.boolean_literal),
      ';'
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

    // Helper rule for a list of identifiers
    identifier_list: $ => seq(
      $.identifier,
      repeat(seq(',', $.identifier))
    ),

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
