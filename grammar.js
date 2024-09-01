module.exports = grammar({
  name: 'al',

  extras: $ => [
    /\s/,
    $.comment
  ],

  // Note: Scope resolution and the fact that all objects in a file belong to the declared namespace
  // are semantic concerns, not syntactic ones. These aspects should be handled during semantic analysis.

  rules: {
    source_file: $ => seq(
      optional($.namespace_declaration),
      optional(repeat($.using_directive)),
      repeat1(choice(
        $._declaration,
        $.comment
      ))
    ),

    namespace_declaration: $ => seq(
      'namespace',
      field('name', $.qualified_namespace),
      ';'
    ),

    using_directive: $ => seq(
      'using',
      field('name', $.qualified_namespace),
      ';'
    ),

    qualified_namespace: $ => prec.left(seq(
      $.identifier,
      repeat(seq('.', $.identifier))
    )),

    comment: _ => token(choice(
      seq('//', /[^\r\n\u2028\u2029]*/),
      seq(
        '/*',
        /[^*]*\*+([^/*][^*]*\*+)*/,
        '/',
      ),
    )),

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
      $.api_query_object,
      $.request_page_object,
      $.dotnet_assembly_object
    ),

    // Dot Net Assembly object definition
    dotnet_assembly_object: $ => seq(
      'dotnetassembly',
      field('name', choice($.identifier, $.string)),
      '{',
      repeat($._dotnet_assembly_element),
      '}'
    ),

    _dotnet_assembly_element: $ => choice(
      $.property,
      $.public_key_token_property,
      $.culture_property
    ),

    // PublicKeyToken Property
    // Specifies the public key token of the .NET assembly.
    // This property is used on Dot Net Assembly objects.
    public_key_token_property: $ => seq(
      'PublicKeyToken',
      '=',
      field('value', $.string_literal),
      ';'
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
      optional(';')
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

    request_page_object: $ => seq(
      'requestpage',
      '{',
      repeat($._request_page_element),
      '}'
    ),

    _request_page_element: $ => choice(
      $.layout,
      $.actions,
      $.property,
      $.instructional_text_property,
      $.links_allowed_property,  // Added LinksAllowed property
      $.save_values_property,  // Added SaveValues property
      $.source_table_temporary_property  // Added SourceTableTemporary property
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
      repeat(choice($.property, $.include_caption_property)),
      '}'
    ),

    // IncludeCaption Property
    // Sets whether to include the caption of a field in the data set of a report.
    // This property is used on Report Columns.
    include_caption_property: $ => seq(
      'IncludeCaption',
      '=',
      field('value', $.boolean_literal),
      ';'
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
      repeat(choice($.property, $.reverse_sign_property)),
      '}'
    ),

    // ReverseSign Property
    // Changes negative values into positive values and positive values into negative values in a column of a resulting query data set.
    // This property is used on Query Column objects.
    reverse_sign_property: $ => seq(
      'ReverseSign',
      '=',
      field('value', $.boolean_literal),
      ';'
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

    // ApplicationArea Property
    // Specifies which application areas the page is designed for.
    // This property determines the visibility of the page based on the user's assigned application areas.
    application_area_property: $ => seq(
      'ApplicationArea',
      '=',
      field('value', choice($.identifier, $.array_value)),
      ';'
    ),

    // UsageCategory Property
    // Specifies how the page can be used from the search feature.
    // This property is used on Page objects.
    usage_category_property: $ => seq(
      'UsageCategory',
      '=',
      field('value', choice(
        'Administration',
        'Documents',
        'History',
        'Lists',
        'None',
        'ReportsAndAnalysis',
        'Tasks'
      )),
      ';'
    ),

    _al_code: $ => choice(
      $.procedure,
      $.trigger,
      $.var
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
      repeat(prec(1, choice(
        $._page_element,
        $.instructional_text_property,
        $.caption_ml_property
      ))),
      '}'
    ),

    page_part: $ => seq(
      'part',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat(choice($.property, $.multiplicity_property)),
      '}'
    ),

    // Multiplicity Property
    // Specifies the multiplicity of the part on API pages.
    // This property is used on Page Part objects.
    multiplicity_property: $ => seq(
      'Multiplicity',
      '=',
      field('value', choice('ZeroOrOne', 'Many')),
      ';'
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
      optional($.variable_declaration),
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
      optional($.variable_declaration),
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
      optional($.variable_declaration),
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
      optional($.variable_declaration),
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
      optional($.variable_declaration),
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
      optional($.variable_declaration),
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
      optional($.variable_declaration),
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
      optional($.variable_declaration),
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
      optional($.variable_declaration),
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
      optional($.variable_declaration),
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
      optional($.variable_declaration),
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
      optional($.variable_declaration),
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
      optional($.variable_declaration),
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
      $.area,
      $.group,
      $.field,
      $.part,
      $.system_part,
      $.cue_group,
      $.repeater
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
      $.system_part,
      $.field,
      $.repeater,
      $.cue_group,
      $.fixed_layout,
      $.grid
    ),

    group: $ => seq(
      'group',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($._group_content),
      '}'
    ),

    _group_content: $ => choice(
      $.field,
      $.part,
      $.group,
      $.cue_group
    ),

    field: $ => seq(
      'field',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($.field_property),
      '}'
    ),

    part: $ => seq(
      'part',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($.part_property),
      '}'
    ),

    system_part: $ => seq(
      'systempart',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($.system_part_property),
      '}'
    ),

    cue_group: $ => seq(
      'cuegroup',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($._cue_group_content),
      '}'
    ),

    _cue_group_content: $ => choice(
      $.field,
      $.part
    ),

    repeater: $ => seq(
      'repeater',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($._repeater_content),
      '}'
    ),

    _repeater_content: $ => choice(
      $.field,
      $.group
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
      repeat($.view_property),
      '}'
    ),

    view_property: $ => choice(
      $.caption_property,
      $.filters_property,
      // ... other view properties
    ),

    layout_property: $ => seq(
      'Layout',
      '=',
      field('value', $.string_literal),
      ';'
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
      optional($.obsolete_attribute),
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

    _codeunit_element: $ => seq(
      choice(
        $.access_property,
        $.subtype_property,
        $.event_subscriber_instance_property,
        $.inherent_entitlements_property,
        $.inherent_permissions_property,
        $.obsolete_reason_property,
        $.obsolete_state_property,
        $.obsolete_tag_property,
        $.permissions_property,
        $.single_instance_property,
        $.test_isolation_property,
        $.test_permission_property,
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
        $.onvalidateupgradeperdatabase_trigger,
        $.trigger,
        $.var,
        $.event_subscriber  // Add this line to include event subscribers
      ),
      optional(';')
    ),

    // Add the event_subscriber rule
    event_subscriber: $ => seq(
      '[EventSubscriber(',
      $.event_subscriber_params,
      ')]',
      $.procedure
    ),

    event_subscriber_params: $ => seq(
      field('object_type', $.object_type),
      ',',
      field('object_id', choice($.integer, $.identifier)),
      ',',
      field('event_name', $.string_literal),
      ',',
      field('element_name', $.string_literal),
      optional(seq(
        ',',
        field('skip_on_missing_license', $.boolean_literal),
        optional(seq(
          ',',
          field('skip_on_missing_permission', $.boolean_literal)
        ))
      ))
    ),

    object_type: $ => seq(
      'ObjectType',
      '::',
      choice('Codeunit', 'Page', 'Report', 'Table', 'XMLPort')
    ),

    _table_element: $ => seq(
      choice(
        $.fields,
        $.keys,
        $.caption_property,
        $.data_classification_property,
        $.data_caption_fields_property,
        $.drill_down_page_id_property,
        $.lookup_page_id_property,
        $.paste_is_valid_property,
        $.permissions_property,
        $.data_per_company_property,
        $.extensible_property,
        $.table_type_property,
        $.compression_type_property,
        $.access_property,
        $.obsolete_state_property,
        $.obsolete_reason_property,
        $.obsolete_tag_property,
        $.replicate_data_property,
        $.linked_object_property,
        $.linked_in_transaction_property,
        $.caption_ml_property,
        $.about_title_property,
        $.about_text_property,
        $.fieldgroups,
        $.procedure,
        $.trigger,
        $.ondelete_trigger,
        $.oninsert_trigger,
        $.onmodify_trigger,
        $.onrename_trigger,
        $.var
      ),
      optional(';')
    ),

    fieldgroups: $ => seq(
      'fieldgroups',
      '{',
      repeat($.fieldgroup),
      '}'
    ),

    fieldgroup: $ => seq(
      'fieldgroup',
      '(',
      field('name', $.identifier),
      ';',
      field('fields', $.identifier_list),
      ')',
      '{',
      '}'
    ),

    var: $ => seq(
      'var',
      repeat($.variable_declaration)
    ),

    variable_declaration: $ => choice(
      seq(
        field('name', $.identifier),
        ':',
        field('type', $._type),
        ';'
      ),
      $.label_declaration
    ),

    label_declaration: $ => seq(
      field('name', $.identifier),
      ':',
      'Label',
      field('value', $.string_literal),
      optional(seq(
        ',',
        field('language', $.string_literal),
        optional(seq(
          ',',
          'Locked',
          '=',
          field('locked', $.boolean_literal)
        )),
        optional(seq(
          ',',
          'Comment',
          '=',
          field('comment', $.string_literal)
        ))
      )),
      ';'
    ),

    _page_element: $ => seq(
      choice(
        //$.property,
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
        $.onqueryclosepage_trigger,
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
        $.caption_ml_property,
        $.card_page_id_property,
        $.change_tracking_allowed_property,
        $.context_sensitive_help_page_property,
        $.data_access_intent_property,
        $.data_caption_expression_property,
        $.data_caption_fields_property,
        $.delayed_insert_property,
        $.delete_allowed_property,
        $.drilldown_page_id_property,
        $.editable_property,
        $.entity_caption_property,
        $.entity_caption_ml_property,
        $.entity_name_property,
        $.entity_set_caption_property,
        $.entity_set_caption_ml_property,
        $.entity_set_name_property,
        $.extensible_property,
        $.help_link_property,
        $.inherent_entitlements_property,
        $.inherent_permissions_property,
        $.insert_allowed_property,
        $.instructional_text_property,
        $.is_preview_property,
        $.links_allowed_property,
        $.modify_allowed_property,
        $.multiple_new_lines_property,
        $.odata_edm_type_property,
        $.odata_key_fields_property,
        $.obsolete_reason_property,
        $.obsolete_state_property,
        $.obsolete_tag_property,
        $.page_type_property,
        $.permissions_property,
        $.populate_all_fields_property,
        $.promoted_action_categories_property,
        $.promoted_action_categories_ml_property,
        $.query_category_property,
        $.refresh_on_activate_property,
        $.save_values_property,
        $.source_table_property,
        $.source_table_temporary_property,
        $.source_table_view_property,
        $.usage_category_property,
        $.var
      ),
      optional(';')
    ),

    _report_element: $ => seq(
      choice(
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
      optional(';')
    ),

    _xmlport_element: $ => seq(
      choice(
        $.property,
        $.schema,
        $.requestpage,
        $.auto_calc_field_property,
        $.calc_fields_property
      ),
      optional(';')
    ),

    _query_element: $ => seq(
      choice(
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
      optional(';')
    ),

    _enum_element: $ => seq(
      choice(
        $.property,
        $.value,
        $.enum_type
      ),
      optional(';')
    ),

    _permission_set_element: $ => seq(
      choice(
        $.property,
        $.permissions,
        $.caption_ml_property
      ),
      optional(';')
    ),

    _control_addin_element: $ => seq(
      choice(
        $.property,
        $.procedure,
        $.event
      ),
      optional(';')
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
      optional($.variable_declaration),
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
      optional($.variable_declaration),
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
      optional($.variable_declaration),
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
      optional($.variable_declaration),
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
      optional($.variable_declaration),
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
      optional($.variable_declaration),
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
      optional($.variable_declaration),
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
      optional($.variable_declaration),
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
      optional($.variable_declaration),
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
      optional($.variable_declaration),
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
      optional($.variable_declaration),
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
      optional($.variable_declaration),
      field('body', $.code_block)
    ),

    procedure: $ => prec(1, seq(
      optional($.obsolete_attribute),
      optional('local'),
      'procedure',
      field('name', $.identifier),
      '(',
      optional($._parameter_list),
      ')',
      optional(choice(
        seq(field('return_type', seq(':', $._type)),optional(';')),
        seq(
          field('return_value', $.identifier),
          ':',
          field('return_type', $._type),
          optional(';')
        ),
        ';'
      )),
      optional($.var),
      field('body', $.code_block)
    )),

    obsolete_attribute: $ => seq(
      '[',
      'Obsolete',
      '(',
      optional(seq(
        field('reason', $.string_literal),
        optional(seq(',', field('tag', $.string_literal)))
      )),
      ')',
      ']'
    ),

    _parameter_list: $ => seq(
      $.parameter,
      repeat(seq(';', $.parameter))
    ),

    parameter: $ => seq(
      optional(choice(/[vV][aA][rR]/, /[oO][uU][tT]/)),
      field('name', $.identifier),
      ':',
      field('type', $._type)
    ),

    _type: $ => choice(
      $._variable_data_type,
      $.record_type
    ),

    record_type: $ => prec(2, seq(
      'Record',
      field('table_reference', choice(
        $.identifier,
        $.integer,
        $.string
      ))
    )),

    code_block: $ => seq(
      /[bB][eE][gG][iI][nN]/,
      repeat(choice(
        $._statement,
        //$.comment
      )),
      /[eE][nN][dD]/
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
      $.with_statement,
      $.method_call_statement  // Add this line
    ),

    method_call_statement: $ => seq(
      $.method_call,
      optional(';')
    ),

    assignment_statement: $ => seq(
      field('variable', $.identifier),
      ':=',
      field('value', $._expression),
      ';'
    ),

    if_statement: $ => prec.right(seq(
      /[iI][fF]/,
      field('condition', $._expression),
      /[tT][hH][eE][nN]/,
      field('then_body', choice($._statement, $.code_block)),
      optional(seq(
        /[eE][lL][sS][eE]/,
        field('else_body', choice($._statement, $.code_block))
      ))
    )),

    case_statement: $ => seq(
      /[cC][aA][sS][eE]/,
      field('expression', $._expression),
      /[oO][fF]/,
      repeat1($.case_option),
      optional(seq(/[eE][lL][sS][eE]/, field('else_body', $.code_block))),
      /[eE][nN][dD]/
    ),

    case_option: $ => seq(
      field('value', $._literal),
      ':',
      field('body', $.code_block),
      ';'
    ),

    for_statement: $ => seq(
      /[fF][oO][rR]/,
      field('variable', $.identifier),
      ':=',
      field('start', $._expression),
      /[tT][oO]/,
      field('end', $._expression),
      optional(seq(/[sS][tT][eE][pP]/, field('step', $._expression))),
      /[dD][oO]/,
      field('body', $.code_block)
    ),

    while_statement: $ => seq(
      /[wW][hH][iI][lL][eE]/,
      field('condition', $._expression),
      /[dD][oO]/,
      field('body', $.code_block)
    ),

    repeat_statement: $ => seq(
      /[rR][eE][pP][eE][aA][tT]/,
      field('body', $.code_block),
      /[uU][nN][tT][iI][lL]/,
      field('condition', $._expression),
      ';'
    ),

    procedure_call_statement: $ => choice(
      seq(
        field('procedure', $.identifier),
        '(',
        optional($._argument_list),
        ')',
        ';'
      ),
      seq(
        field('procedure', $.identifier),
        ';'
      )
    ),

    exit_statement: $ => seq(
      /[eE][xX][iI][tT]/,
      optional(seq(
        '(',
        optional(seq(
          optional(/[nN][oO][tT]/),
          $._expression
        )),
        ')'
      )),
      optional(';')
    ),

    with_statement: $ => seq(
      /[wW][iI][tT][hH]/,
      field('record', $.identifier),
      /[dD][oO]/,
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
      $.ternary_expression,
      $.method_call  // Added this line
    ),

    method_call: $ => prec(5, seq(
      field('object', $.identifier),
      '.',
      field('method', $.identifier),
      '(',
      optional($._argument_list),
      ')'
    )),

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
      field('function', choice($.identifier, $.member_access_expression)),
      '(',
      optional($._argument_list),
      ')'
    )),

    member_access_expression: $ => prec.left(4, seq(
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
      field('name', choice($.fully_qualified_identifier, $.string)),
      '{',
      repeat($._table_element),
      '}'
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
      ';',
      field('fields', $.key_field_list),
      ')',
      '{',
      repeat(choice($.clustered_property, $.unique_property, $.included_fields_property, $.column_store_index_property, $.enabled_property)),
      '}'
    ),

    // Helper rule for a list of key fields
    key_field_list: $ => seq(
      $.key_field,
      repeat(seq(',', $.key_field))
    ),

    // Helper rule for a key field (can be quoted or unquoted)
    key_field: $ => choice(
      $.identifier,
      $.string
    ),

    // Clustered Property
    // Sets a value that indicates whether the key also defines the clustered index in the database.
    // This property is used on Table Keys.
    clustered_property: $ => seq(
      'Clustered',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // Unique Property
    // Creates a unique constraint on the table in SQL Server.
    // This property is used on Table Keys.
    unique_property: $ => seq(
      'Unique',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // IncludedFields Property
    // Sets the fields that are included as non-key columns in the index on SQL Server.
    // This property is used on Table Keys.
    included_fields_property: $ => seq(
      'IncludedFields',
      '=',
      field('value', $.identifier_list),
      ';'
    ),

    // ColumnStoreIndex Property
    // Sets the fields that are added to the ColumnStore index inside SQL Server.
    // This property is used on Table Keys.
    column_store_index_property: $ => seq(
      'ColumnStoreIndex',
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
      optional($.variable_declaration),
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
      optional($.var),
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
      optional($.var),
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
      optional($.variable_declaration),
      field('body', $.code_block)
    ),

    field: $ => seq(
      'field',
      '(',
      field('id', $.integer),
      ';',
      field('name', choice($.string, $.identifier)),
      ';',
      field('data_type', $._table_data_type),
      ')',
      '{',
      repeat($.field_property),
      '}'
    ),

    _data_type: $ => choice(
      $._table_data_type,
      $._variable_data_type
    ),

    _table_data_type: $ => choice(
      'BigInteger',
      'Blob',
      'Boolean',
      'Code',
      'Date',
      'DateFormula',
      'DateTime',
      'Decimal',
      'Duration',
      'Guid',
      'Integer',
      'Media',
      'MediaSet',
      'Option',
      'RecordId',
      'TableFilter',
      'Text',
      'Time',
      seq(
        choice('Code', 'Text'),
        '[',
        $.integer,
        ']'
      )
    ),

    _variable_data_type: $ => choice(
      'Action',
      'Any',
      'BigInteger',
      'BigText',
      'Binary',
      'Boolean',
      'Byte',
      'Char',
      'ClientType',
      'Codeunit',
      'Database',
      'DataClassification',
      'DataScope',
      'Date',
      'DateFormula',
      'DateTime',
      'Decimal',
      'Dialog',
      'Dictionary',
      'DotNet',
      'Duration',
      'Enum',
      'ErrorInfo',
      'ExecutionContext',
      'FieldRef',
      'File',
      'FilterPageBuilder',
      'Guid',
      'InStream',
      'Integer',
      'Interface',
      'IsolationLevel',
      'JsonArray',
      'JsonObject',
      'JsonToken',
      'JsonValue',
      'KeyRef',
      'Label',
      'List',
      'ModuleInfo',
      'Notification',
      'Option',
      'OutStream',
      'Page',
      'Query',
      'Record',
      'RecordId',
      'RecordRef',
      'Report',
      'RequestPage',
      'Session',
      'SessionSettings',
      'System',
      'TableConnectionType',
      'TestAction',
      'TestField',
      'TestFilterField',
      'TestPage',
      'TestPermissions',
      'TestRequestPage',
      'TextBuilder',
      'Time',
      'TransactionModel',
      'TransactionType',
      'Variant',
      'Verbosity',
      'Version',
      'XmlPort',
      $.sized_data_type,
      'Code',
      'Text'
    ),

    sized_data_type: $ => prec.dynamic(1, seq(
      choice('Code', 'Text'),
      '[',
      $.integer,
      ']'
    )),

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
      $.external_name_property,
      $.external_type_property,
      $.field_class_property,
      $.init_value_property,
      $.instructional_text_property,
      $.max_value_property,
      $.min_value_property,
      $.moved_from_property,
      $.moved_to_property,
      $.navigation_page_id_property,
      $.not_blank_property,
      $.numeric_property,
      $.obsolete_reason_property,
      $.obsolete_state_property,
      $.obsolete_tag_property,
      $.option_caption_property,
      $.option_caption_ml_property,
      $.option_members_property,
      $.option_ordinal_values_property,
      $.quick_entry_property,
      $.sign_displacement_property
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
      $.data_deletion_allowed_property,
      $.drilldown_page_id_property,
      $.enabled_property,
      $.extensible_property,
      $.external_name_property,
      $.external_schema_property,
      $.inherent_entitlements_property,
      $.inherent_permissions_property,
      $.key_property,
      $.linked_in_transaction_property,
      $.linked_object_property,
      $.lookup_page_id_property,
      $.moved_from_property,
      $.moved_to_property,
      $.obsolete_reason_property,
      $.obsolete_state_property,
      $.obsolete_tag_property,
      $.paste_is_valid_property,
      $.permissions_property,
      $.replicate_data_property,
      $.table_type_property,
      $.data_classification_fields_property,
      $.scope_property,
      $.fields_property,
      $.about_title_property,
      $.about_title_ml_property,
      $.about_text_property,
      $.about_text_ml_property
    ),

    // DataClassificationFields Property
    // Specifies the fields in the table that contain sensitive data.
    // This property is used on Table objects to define which fields contain sensitive information.
    data_classification_fields_property: $ => seq(
      'DataClassificationFields',
      '=',
      field('value', $.identifier_list),
      ';'
    ),

    // ReplicateData Property
    // Specifies if the table should be replicated.
    // This property is used on Table objects.
    replicate_data_property: $ => seq(
      'ReplicateData',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // TableType Property
    // Specifies the type of the table.
    // This property is used on Table objects.
    table_type_property: $ => seq(
      'TableType',
      '=',
      field('value', choice('Normal', 'CRM', 'ExternalSQL', 'MicrosoftGraph', 'Temporary')),
      ';'
    ),

    // Scope Property
    // Sets the scope of a table.
    // This property is used on Table objects to determine the availability of the table in different environments.
    scope_property: $ => seq(
      'Scope',
      '=',
      field('value', choice('Cloud', 'OnPrem')),
      ';'
    ),

    // Fields Property
    // Specifies the fields that are included in the table.
    // This property is used on Table objects to define the structure of the table.
    fields_property: $ => seq(
      'Fields',
      '=',
      field('value', $.fields_value),
      ';'
    ),

    fields_value: $ => seq(
      '{',
      repeat($.field_definition),
      '}'
    ),

    field_definition: $ => seq(
      field('field_name', $.identifier),
      ':',
      field('field_type', $.identifier),
      optional(seq(
        '(',
        field('field_properties', $.field_properties),
        ')'
      )),
      ';'
    ),

    field_properties: $ => repeat1(
      seq(
        field('property_name', $.identifier),
        '=',
        field('property_value', $._value),
        optional(',')
      )
    ),

    // AboutTitle Property
    // Sets the large-font title that appears in a teaching tip in the UI.
    // This property is used on Table objects.
    about_title_property: $ => seq(
      'AboutTitle',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // LookupPageId Property
    // Sets the ID of the page to use for lookups on this table.
    // This property is used on Table objects.
    lookup_page_id_property: $ => seq(
      'LookupPageId',
      '=',
      field('value', choice($.integer, $.identifier, $.string_literal)),
      ';'
    ),

    // DrillDownPageId Property
    // Sets the ID of the page to use for drill-downs on this table.
    // This property is used on Table objects.
    drill_down_page_id_property: $ => seq(
      'DrillDownPageID',
      '=',
      field('value', choice($.integer, $.identifier, $.string_literal)),
      ';'
    ),

    // PasteIsValid Property
    // Sets whether inserting records into this table using the paste command is enabled.
    // This property is used on Table objects.
    paste_is_valid_property: $ => seq(
      'PasteIsValid',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // Permissions Property
    // Sets whether an object has additional permission required to perform some operations on one or more tables.
    // This property is used on various AL objects including Codeunit, Table, Request Page, Page, Xml Port, Report, Query, Permission Set, and Permission Set Extension.
    permissions_property: $ => seq(
      'Permissions',
      '=',
      field('value', $.permissions_value),
      ';'
    ),

    permissions_value: $ => seq(
      repeat1(seq(
        'TableData',
        field('table_id', $.integer),
        '=',
        field('permissions', $.permissions_string),
        optional(',')
      ))
    ),

    permissions_string: $ => /[RrIiMmDdXx]+/,

    // ObsoleteTag Property
    // Specifies a free-form text to support tracking of where and when the object was marked as obsolete.
    // This property is used on various AL objects including Tables, Table Fields, Pages, and more.
    obsolete_tag_property: $ => seq(
      'ObsoleteTag',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // ODataEDMType Property
    // Specifies the Entity Data Model Type to be used for this node in the OData metadata.
    // This property is used on Page Field objects.
    odata_edm_type_property: $ => seq(
      'ODataEDMType',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // ODataKeyFields Property
    // Specifies the fields to select when using OData.
    // This property is used on Page objects.
    odata_key_fields_property: $ => seq(
      'ODataKeyFields',
      '=',
      field('value', $.identifier_list),
      ';'
    ),

    // ObsoleteReason Property
    // Specifies why the object has been marked as Pending in the ObsoleteState property.
    // This property is used on various AL objects including Tables, Table Fields, Pages, and more.
    obsolete_reason_property: $ => seq(
      'ObsoleteReason',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // ObsoleteState Property
    // Marks whether the object will be deprecated.
    // This property is used on various AL objects including Tables, Table Fields, Pages, and more.
    obsolete_state_property: $ => seq(
      'ObsoleteState',
      '=',
      field('value', choice('Pending', 'Removed')),
      ';'
    ),

    // MovedTo Property
    // Specifies the destination extension Id when a table is moved to another extension.
    // This property is used on Table objects.
    moved_to_property: $ => seq(
      'MovedTo',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // MovedFrom Property
    // Specifies the origin extension ID when a table is moved to a new extension.
    // This property is used on Table and Table Field objects.
    moved_from_property: $ => seq(
      'MovedFrom',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // LinkedObject Property
    // Specifies a link to SQL Server objects.
    // This property is used on Table objects.
    linked_object_property: $ => seq(
      'LinkedObject',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // LinkedInTransaction Property
    // Specifies whether the table is linked in a transaction.
    // This property is used on Table objects.
    linked_in_transaction_property: $ => seq(
      'LinkedInTransaction',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // AboutTextML Property
    // Sets the body of text that appears in a teaching tip in the UI, supporting multiple languages.
    // This property is used on Table objects.
    about_text_ml_property: $ => seq(
      'AboutTextML',
      '=',
      field('value', $.multilanguage_string_literal),
      ';'
    ),

    // Key Property
    // Sets the primary key for the table.
    // This property is used on Table objects.
    key_property: $ => seq(
      'Key',
      '(',
      field('fields', $.identifier_list),
      ')',
      ';'
    ),

    // IsControlAddIn Property
    // Sets a value that indicates whether the .NET type represents a control add-in.
    // This property is used on Dot Net Type Declaration objects.
    is_control_addin_property: $ => seq(
      'IsControlAddIn',
      '=',
      field('value', $.boolean_literal),
      ';'
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
      $.external_name_property,
      $.external_type_property,
      $.field_class_property,
      $.init_value_property,
      $.instructional_text_property,
      $.max_value_property,
      $.min_value_property,
      $.moved_from_property,
      $.moved_to_property,
      $.navigation_page_id_property,
      $.not_blank_property,
      $.numeric_property,
      $.obsolete_reason_property,
      $.obsolete_state_property,
      $.obsolete_tag_property,
      $.option_caption_property,
      $.option_caption_ml_property,
      $.option_members_property,
      $.option_ordinal_values_property,
      $.quick_entry_property,
      $.sign_displacement_property
    ),

    // SignDisplacement Property
    // Sets a value to shift negative values to the right for display purposes only.
    // This property is used on Table Fields and Page Fields.
    sign_displacement_property: $ => seq(
      'SignDisplacement',
      '=',
      field('value', $.integer),
      ';'
    ),

    // QuickEntry Property
    // Specifies if the page control should have input focus.
    // This property is used on Page Field objects.
    quick_entry_property: $ => seq(
      'QuickEntry',
      '=',
      field('value', choice($.boolean_literal, $.identifier)),
      ';'
    ),

    // OptionOrdinalValues Property
    // Specifies the list of option values. Can be set if the property ExternalType is set to Picklist.
    // This property is used on Table Fields.
    option_ordinal_values_property: $ => seq(
      'OptionOrdinalValues',
      '=',
      field('value', $.option_ordinal_values_value),
      ';'
    ),

    option_ordinal_values_value: $ => seq(
      repeat1(seq(
        $.integer,
        optional(',')
      ))
    ),

    // OptionCaptionML Property
    // Sets the strings that are displayed to the user for selecting an option in multiple languages.
    // This property is used on Table Fields, Page Fields, and Report Columns.
    option_caption_ml_property: $ => seq(
      'OptionCaptionML',
      '=',
      field('value', $.multilanguage_string_literal),
      ';'
    ),

    // OptionMembers Property
    // Sets the list of options that are available in the table field that is currently selected.
    // This property is used on Table Fields.
    option_members_property: $ => seq(
      'OptionMembers',
      '=',
      field('value', $.option_members_value),
      ';'
    ),

    option_members_value: $ => seq(
      repeat1(seq(
        $.string_literal,
        optional(',')
      ))
    ),

    // NotBlank Property
    // Sets a value that specifies whether users must enter a value in the selected field or text box.
    // This property is used on Table Fields and Page Fields.
    not_blank_property: $ => seq(
      'NotBlank',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // Numeric Property
    // Sets a value that requires users to enter only numbers in the field.
    // This property is used on Table Fields and Page Fields.
    numeric_property: $ => seq(
      'Numeric',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // NavigationPageId Property
    // Specifies which page the TableRelation should navigate to.
    // This property is used on Page Field objects.
    navigation_page_id_property: $ => seq(
      'NavigationPageId',
      '=',
      field('value', choice($.integer, $.identifier)),
      ';'
    ),

    // MinValue Property
    // Sets the minimum numeric value for a field.
    // This property is used on Table Fields and Page Fields.
    min_value_property: $ => seq(
      'MinValue',
      '=',
      field('value', $._value),
      ';'
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

    // ExternalType Property
    // Specifies the type of the original table field in the external database.
    // This property is used on Table Fields when working with external data sources.
    external_type_property: $ => seq(
      'ExternalType',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // FieldClass Property
    // Sets the class of the field in a table.
    // This property is used on Table Fields to define whether it's a Normal field, FlowField, or FlowFilter.
    field_class_property: $ => seq(
      'FieldClass',
      '=',
      field('value', choice('Normal', 'FlowField', 'FlowFilter')),
      ';'
    ),

    // ExternalSchema Property
    // Specifies the name of the database schema of the external database.
    // This property is used on Table objects.
    external_schema_property: $ => seq(
      'ExternalSchema',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // InherentEntitlements Property
    // Specifies the entitlement permissions that are inherently assigned to the given object.
    // This property is used on Query, Report, Xml Port, Table, Codeunit, and Page objects.
    inherent_entitlements_property: $ => seq(
      'InherentEntitlements',
      '=',
      field('value', $.inherent_entitlements_value),
      ';'
    ),

    inherent_entitlements_value: $ => repeat1(choice('R', 'I', 'M', 'D', 'X')),

    // InherentPermissions Property
    // Specifies the permissions that are inherently assigned to the given object.
    // This property is used on Query, Report, Xml Port, Table, Codeunit, and Page objects.
    inherent_permissions_property: $ => seq(
      'InherentPermissions',
      '=',
      field('value', $.inherent_permissions_value),
      ';'
    ),

    inherent_permissions_value: $ => repeat1(choice('R', 'I', 'M', 'D', 'X')),

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

    // Multi-language string literal
    multilanguage_string_literal: $ => seq(
      repeat1(seq(
        field('language_code', $.identifier),
        '=',
        field('text', $.string_literal),
        optional(',')
      ))
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


    page_view_property: $ => seq(
      'PageView',
      '=',
      field('value', $.page_view_value),
      ';'
    ),

    page_view_value: $ => seq(
      '{',
      repeat(choice(
        $.caption_ml_property,
        $.filters_property,
        $.shared_layout_property
      )),
      '}'
    ),

    page_action: $ => seq(
      'action',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($.page_action_property),
      '}'
    ),

    page_action_property: $ => choice(
      $.caption_property,
      $.caption_ml_property,
      $.enabled_property,
      $.image_property,
      $.promoted_property,
      $.promoted_category_property,
      $.run_object_property,
      $.shortcut_key_property,
      $.tooltip_property,
      $.trigger_property
    ),

    // Image Property
    // Sets the image to be displayed for the action.
    // This property is used on Page Action objects.
    image_property: $ => seq(
      'Image',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // Tooltip Property
    // Sets the tooltip text for the action.
    // This property is used on Page Action objects.
    tooltip_property: $ => seq(
      'Tooltip',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // Trigger Property
    // Sets the trigger for the action.
    // This property is used on Page Action objects.
    trigger_property: $ => seq(
      'Trigger',
      '=',
      field('value', $.identifier),
      ';'
    ),

    // SourceTable Property
    // Sets the ID or name of the table from which this page will display records.
    // This property is used on Page and Request Page objects.
    source_table_property: $ => prec(1, seq(
      'SourceTable',
      '=',
      field('value', choice(
        $.integer,
        $.fully_qualified_identifier,
        $.identifier,
        $.string
      )),
      ';'
    )),

    // TableRelation Property
    // Sets a table relation for a field.
    // This property is used on Table Fields and Page Fields.
    table_relation_property: $ => seq(
      'TableRelation',
      '=',
      field('value', $.table_relation_value),
      ';'
    ),

    table_relation_value: $ => seq(
      field('table', $.identifier),
      optional(seq(
        '.',
        field('field', $.identifier)
      )),
      optional(seq(
        'WHERE',
        '(',
        $.table_filters,
        ')'
      ))
    ),

    // ValuesAllowed Property
    // Sets a list of values that are allowed in the field.
    // This property is used on Table Fields and Page Fields.
    values_allowed_property: $ => seq(
      'ValuesAllowed',
      '=',
      field('value', $.values_allowed_value),
      ';'
    ),

    values_allowed_value: $ => seq(
      repeat1(seq(
        $._value,
        optional(',')
      ))
    ),

    // Width Property
    // Sets the width of a field on a page.
    // This property is used on Page Fields.
    width_property: $ => seq(
      'Width',
      '=',
      field('value', $.integer),
      ';'
    ),

    // SharedLayout Property
    // Specifies whether the view has the same layout as the default view 'All'.
    // This property is used on Page View objects.
    shared_layout_property: $ => seq(
      'SharedLayout',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // ShortcutKey Property
    // Sets a shortcut key for selecting a menu item.
    // This property is used on Page Action, Page Custom Action, and Page File Upload Action objects.
    shortcut_key_property: $ => seq(
      'ShortcutKey',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // ShowCaption Property
    // Sets whether the text that is specified by the Caption Property is displayed for the control.
    // This property is used on Page Label, Page Field, and Page Group objects.
    show_caption_property: $ => seq(
      'ShowCaption',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // ShowMandatory Property
    // Sets a value that specifies whether users must enter a value in the selected field or text box.
    // This property is used on Page Field objects.
    show_mandatory_property: $ => prec(1, seq(
      'ShowMandatory',
      '=',
      field('value', choice($.boolean_literal, $.identifier, $._expression)),
      ';'
    )),

    // ShowAsTree Property
    // Sets the indentation of rows on a List Page to Tree View.
    // This property is used on Page Group objects.
    show_as_tree_property: $ => seq(
      'ShowAsTree',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // Scope Property
    // Specifies the scope of the action to be either page-specific, or specific to a repeater control.
    // This property is used on Page Action objects.
    scope_property: $ => seq(
      'Scope',
      '=',
      field('value', choice('Page', 'Repeater')),
      ';'
    ),

    // SaveValues Property
    // Sets whether user-specific control values are saved for this page.
    // This property is used on Page and Request Page objects.
    save_values_property: $ => seq(
      'SaveValues',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // RefreshOnActivate Property
    // Set this property on pages where you want to refresh the data when the user navigates back from another page.
    // This property is used on Page objects.
    refresh_on_activate_property: $ => seq(
      'RefreshOnActivate',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // RunObject Property
    // Sets the object you want to run immediately when the action is activated.
    // This property is used on Page Action objects.
    run_object_property: $ => seq(
      'RunObject',
      '=',
      field('value', $.run_object_value),
      ';'
    ),

    run_object_value: $ => seq(
      field('object_type', choice('Page', 'Report', 'Codeunit', 'Query')),
      field('object_id', choice($.integer, $.identifier))
    ),

    // RunPageLink Property
    // Sets a link to a page that will be launched for this action.
    // This property is used on Page Action objects.
    run_page_link_property: $ => seq(
      'RunPageLink',
      '=',
      field('value', $.run_page_link_value),
      ';'
    ),

    run_page_link_value: $ => repeat1(
      seq(
        field('field', $.identifier),
        '=',
        field('filter', choice(
          seq('CONST', '(', $._value, ')'),
          seq('FILTER', '(', $.string_literal, ')'),
          seq('FIELD', '(', $.identifier, ')'),
          seq('FIELD', '(', 'UPPERLIMIT', '(', $.identifier, ')', ')'),
          seq('FIELD', '(', 'FILTER', '(', $.identifier, ')', ')'),
          seq('FIELD', '(', 'UPPERLIMIT', '(', 'FILTER', '(', $.identifier, ')', ')', ')')
        )),
        optional(',')
      )
    ),

    // RunPageMode Property
    // Sets the mode in which the page is run. Choose between View, Edit, or Create.
    // This property is used on Page Action objects.
    run_page_mode_property: $ => seq(
      'RunPageMode',
      '=',
      field('value', choice('View', 'Edit', 'Create')),
      ';'
    ),

    // RunPageOnRec Property
    // Sets whether the same record on the page you launch from this control is displayed as is already displayed on the current page.
    // This property is used on Page Action objects.
    run_page_on_rec_property: $ => seq(
      'RunPageOnRec',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // RunPageView Property
    // Sets a tableview for the page that will be launched for this action.
    // This property is used on Page Action objects.
    run_page_view_property: $ => seq(
      'RunPageView',
      '=',
      field('value', $.run_page_view_value),
      ';'
    ),

    run_page_view_value: $ => choice(
      seq('SORTING', '(', $.identifier_list, ')'),
      seq('ORDER', '(', choice('Ascending', 'Descending'), ')'),
      seq('WHERE', '(', $.table_filters, ')'),
      seq(
        'SORTING',
        '(',
        $.identifier_list,
        ')',
        optional(seq('ORDER', '(', choice('Ascending', 'Descending'), ')')),
        optional(seq('WHERE', '(', $.table_filters, ')'))
      ),
      seq(
        'SORTING',
        '(',
        $.identifier_list,
        ')',
        'WHERE',
        '(',
        $.table_filters,
        ')'
      )
    ),

    // QueryCategory Property
    // Specifies the query category that the page supports.
    // This property is used on Page objects.
    query_category_property: $ => seq(
      'QueryCategory',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // Provider Property
    // Sets the provider for a FactBox. This property enables you to create a link from a Repeater or any other type of control to a Factbox.
    // It could also be used to link two FactBoxes.
    // This property is used on Page Part, Page System Part, and Page Chart Part objects.
    provider_property: $ => seq(
      'Provider',
      '=',
      field('value', $.identifier),
      ';'
    ),

    // AboutTitleML Property
    // Sets the large-font title that appears in a teaching tip in the UI, supporting multiple languages.
    // This property is used on Page objects and their controls (actions, fields, parts, etc.).
    about_title_ml_property: $ => seq(
      'AboutTitleML',
      '=',
      field('value', $.multilanguage_string_literal),
      ';'
    ),

    // PromptMode Property
    // Specifies the current mode of a PromptDialog page.
    // This property is used on Page objects with PageType set to PromptDialog.
    prompt_mode_property: $ => seq(
      'PromptMode',
      '=',
      field('value', choice('Prompt', 'Generate', 'Content')),
      ';'
    ),

    // PromotedOnly Property
    // Specifies whether the selected action is promoted only, which means that it will appear only on the Home tab in the ribbon and not on the tab where it is defined.
    // This property is used on Page Action objects.
    promoted_only_property: $ => seq(
      'PromotedOnly',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // PromotedCategory Property
    // Sets a category for a promoted action.
    // This property is used on Page Action objects.
    promoted_category_property: $ => seq(
      'PromotedCategory',
      '=',
      field('value', choice(
        'New',
        'Process',
        'Report',
        'Category4',
        'Category5',
        'Category6',
        'Category7',
        'Category8',
        'Category9',
        'Category10',
        'Category11',
        'Category12',
        'Category13',
        'Category14',
        'Category15',
        'Category16',
        'Category17',
        'Category18',
        'Category19',
        'Category20'
      )),
      ';'
    ),

    // PromotedActionCategories Property
    // Sets categories for promoted actions.
    // This property is used on Page objects.
    promoted_action_categories_property: $ => seq(
      'PromotedActionCategories',
      '=',
      field('value', choice(
        $.string_literal,
        $.comma_separated_category_list
      )),
      optional(seq(
        ',',
        repeat1(seq(
          field('parameter', choice('Locked', 'Comment', 'MaxLength')),
          '=',
          field('parameter_value', choice($.boolean_literal, $.string_literal, $.integer)),
          optional(',')
        ))
      )),
      ';'
    ),

    comma_separated_category_list: $ => seq(
      "'",
      $.identifier,
      repeat(seq(',', $.identifier)),
      "'"
    ),

    // PromotedActionCategoriesML Property
    // Sets the caption of the group that you are promoting the action to in multiple languages.
    // This property is used on Page objects.
    promoted_action_categories_ml_property: $ => seq(
      'PromotedActionCategoriesML',
      '=',
      field('value', $.multilanguage_string_literal),
      ';'
    ),

    // PreserveWhiteSpace Property
    // Determines whether white space should be preserved in documents that are imported through an XmlPort.
    // This property is used on Xml Port objects.
    preserve_whitespace_property: $ => seq(
      'PreserveWhiteSpace',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // Promoted Property
    // Sets the value that indicates whether the selected action is elevated to a promoted category in the action bar.
    // This property is used on Page Actions.
    promoted_property: $ => seq(
      'Promoted',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // PromotedIsBig Property
    // Sets the action to appear before other promoted actions in the action bar, regardless of its position in the AL code of the page.
    // This property is used on Page Actions.
    promoted_is_big_property: $ => seq(
      'PromotedIsBig',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // PopulateAllFields Property
    // Sets whether fields are filled out automatically with a single filter value when a new record is inserted in a table.
    // This property is used on Page and Request Page objects.
    populate_all_fields_property: $ => seq(
      'PopulateAllFields',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // LinksAllowed Property
    // Sets whether links are allowed on a page or request page.
    // This property is used on Page and Request Page objects.
    links_allowed_property: $ => seq(
      'LinksAllowed',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // Lookup Property
    // Specifies if a page field has a lookup window.
    // This property is used on Page Field objects.
    lookup_property: $ => seq(
      'Lookup',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // ModifyAllowed Property
    // Sets the value to determine whether users can modify records while using this page.
    // This property is used on Page and Request Page objects.
    modify_allowed_property: $ => seq(
      'ModifyAllowed',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // MultiLine Property
    // Sets the value that indicates whether a field can display multiple lines of text.
    // This property is used on Page Labels and Page Fields.
    multiline_property: $ => seq(
      'MultiLine',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // MultipleNewLines Property
    // Sets a value that determines whether users can add multiple new lines between records.
    // This property is used on Page and Request Page objects.
    multiple_new_lines_property: $ => seq(
      'MultipleNewLines',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // IsPreview Property
    // Specifies if the page is available as part of a preview release.
    // This property is used on Page objects.
    is_preview_property: $ => seq(
      'IsPreview',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // Importance Property
    // Sets the amount of information that is visible in a window or dialog box.
    // This property is used on Page Labels and Page Fields.
    importance_property: $ => seq(
      'Importance',
      '=',
      field('value', choice('Standard', 'Promoted', 'Additional')),
      ';'
    ),

    // IndentationColumn Property
    // Sets the name of the hidden column that controls row indentation in a List page.
    // This property is used on Page Groups.
    indentation_column_property: $ => seq(
      'IndentationColumn',
      '=',
      field('value', $.identifier),
      ';'
    ),

    // InsertAllowed Property
    // Sets a value to specify whether users can add records while using a page.
    // This property is used on Page and Request Page objects.
    insert_allowed_property: $ => seq(
      'InsertAllowed',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // InstructionalText Property
    // Sets the string used for instructions in the UI.
    // This property is used on Page, Request Page, Page Field, and Page Group objects.
    instructional_text_property: $ => seq(
      'InstructionalText',
      '=',
      field('value', $.string_literal),
      optional(seq(
        ',',
        repeat1(seq(
          field('parameter', choice('Locked', 'Comment', 'MaxLength')),
          '=',
          field('parameter_value', choice($.boolean_literal, $.string_literal, $.integer)),
          optional(',')
        ))
      )),
      ';'
    ),

    // IsHeader Property
    // Specifies if the page action separator is a header.
    // This property is used on Page Action Separator objects.
    is_header_property: $ => seq(
      'IsHeader',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // Images Property
    // Specifies the list of images to include in the control add-in.
    // This property is used on Control Add In objects.
    images_property: $ => seq(
      'Images',
      '=',
      field('value', $.array_value),
      ';'
    ),

    // HorizontalShrink Property
    // Specifies that the control add-in can be made smaller horizontally.
    // This property is used on Control Add In objects.
    horizontal_shrink_property: $ => seq(
      'HorizontalShrink',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // DrillDownPageId Property
    // Sets the ID of the page to use as a drill-down.
    // This property is used on Table objects and Page Fields.
    drilldown_page_id_property: $ => seq(
      'DrillDownPageID',
      '=',
      field('value', choice($.integer, $.identifier, $.string)),
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
    data_caption_expression_property: $ => prec(1, seq(
      'DataCaptionExpression',
      '=',
      field('value', choice($.string_literal, $._expression)),
      ';'
    )),

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
      'CardPageId',
      '=',
      field('value', choice($.integer, $.identifier, $.string)),
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

    // AboutText Property
    // Sets the body of text that appears in a teaching tip in the UI
    // This property is used on Table objects
    about_text_property: $ => seq(
      'AboutText',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // DataDeletionAllowed Property
    // Sets whether data can be deleted from the table.
    // This property is used on Table objects.
    data_deletion_allowed_property: $ => seq(
      'DataDeletionAllowed',
      '=',
      field('value', $.boolean_literal),
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
      $.extensible_property,
      $.format_region_property,
      $.inherent_entitlements_property,
      $.inherent_permissions_property,
      $.maximum_dataset_size_property,
      $.maximum_document_count_property,
      $.max_iteration_property,
      $.obsolete_reason_property,
      $.obsolete_state_property,
      $.obsolete_tag_property,
      $.option_members_property,
      $.paper_source_default_page_property,
      $.paper_source_first_page_property,
      $.paper_source_last_page_property,
      $.pdf_font_embedding_property,
      $.permissions_property,
      $.preview_mode_property,
      $.print_only_if_detail_property,
      $.processing_only_property,
      $.rdlc_layout_property,
      $.request_page_property,
      $.request_filter_fields_property,
      $.request_filter_heading_property,
      $.request_filter_heading_ml_property,
      $.request_filter_fields_property,
      $.report_layout_property
    ),

    report_layout_property: $ => seq(
      'ReportLayout',
      '=',
      field('value', $.report_layout_value),
      ';'
    ),

    report_layout_value: $ => seq(
      '{',
      repeat(choice(
        $.caption_ml_property,
        // Add other properties specific to Report Layout here
      )),
      '}'
    ),

    // RequestFilterHeadingML Property
    // Sets the string used as a RequestFilterHeading Property for a request page tab in multiple languages.
    // This property is used on Report Data Items and XMLport Table Elements.
    request_filter_heading_ml_property: $ => seq(
      'RequestFilterHeadingML',
      '=',
      field('value', $.multilanguage_string_literal),
      ';'
    ),


    // RequestFilterHeading Property
    // Sets a caption for the request page tab that is related to this data item.
    // This property is used on Report Data Items and XMLport Table Elements.
    request_filter_heading_property: $ => seq(
      'RequestFilterHeading',
      '=',
      field('value', $.string_literal),
      optional(seq(
        ',',
        repeat1(seq(
          field('parameter', choice('Locked', 'Comment', 'MaxLength')),
          '=',
          field('parameter_value', choice($.boolean_literal, $.string_literal, $.integer)),
          optional(',')
        ))
      )),
      ';'
    ),

    // RDLCLayout Property
    // Sets the RDL layout that is used on a report and returns it as a data stream.
    // This property is used on Report objects and Report Extension objects.
    rdlc_layout_property: $ => seq(
      'RDLCLayout',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // RequestPage Property
    // Specifies the request page for the report.
    // This property is used on Report objects to define the page that collects user input before running the report.
    request_page_property: $ => seq(
      'RequestPage',
      '=',
      field('value', $.identifier),
      ';'
    ),

    // ProcessingOnly Property
    // Sets the value that indicates whether a report produces printed output or only processes data.
    // This property is used on Report objects.
    processing_only_property: $ => seq(
      'ProcessingOnly',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // PrintOnlyIfDetail Property
    // Specifies whether to print data in a report for the parent data item when the child data item does not generate any output.
    // This property is used on Report Data Items.
    print_only_if_detail_property: $ => seq(
      'PrintOnlyIfDetail',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // PreviewMode Property
    // Specifies how the report opens when you preview it.
    // This property is used on Report objects.
    preview_mode_property: $ => seq(
      'PreviewMode',
      '=',
      field('value', choice('Normal', 'PrintLayout')),
      ';'
    ),

    // PdfFontEmbedding Property
    // Specifies whether fonts are embedded in PDF files that are generated for reports.
    // This property is used on Report objects.
    pdf_font_embedding_property: $ => seq(
      'PdfFontEmbedding',
      '=',
      field('value', choice('Default', 'Yes', 'No')),
      ';'
    ),

    // PaperSourceFirstPage Property
    // Specifies which paper source to use when printing page one of the report.
    // This property is used on Report objects.
    paper_source_first_page_property: $ => seq(
      'PaperSourceFirstPage',
      '=',
      field('value', choice(
        'Upper', 'Lower', 'Middle', 'Manual', 'Envelope', 'ManualFeed',
        'AutomaticFeed', 'TractorFeed', 'SmallFormat', 'LargeFormat',
        'LargeCapacity', 'Cassette', 'FormSource',
        ...Array.from({length: 16}, (_, i) => `Custom${i+1}`)
      )),
      ';'
    ),

    // PaperSourceLastPage Property
    // Specifies which paper source to use when printing the last page of the report.
    // This property is used on Report objects.
    paper_source_last_page_property: $ => seq(
      'PaperSourceLastPage',
      '=',
      field('value', choice(
        'Upper', 'Lower', 'Middle', 'Manual', 'Envelope', 'ManualFeed',
        'AutomaticFeed', 'TractorFeed', 'SmallFormat', 'LargeFormat',
        'LargeCapacity', 'Cassette', 'FormSource',
        ...Array.from({length: 16}, (_, i) => `Custom${i+1}`)
      )),
      ';'
    ),

    // OptionMembers Property
    // Sets the list of options that are available in the report column that is currently selected.
    // This property is used on Report Columns.
    option_members_property: $ => seq(
      'OptionMembers',
      '=',
      field('value', $.option_members_value),
      ';'
    ),

    option_members_value: $ => seq(
      repeat1(seq(
        $.string_literal,
        optional(',')
      ))
    ),

    // PaperSourceDefaultPage Property
    // Specifies the default paper source to use when printing the report.
    // This property is used on Report objects.
    paper_source_default_page_property: $ => seq(
      'PaperSourceDefaultPage',
      '=',
      field('value', choice(
        'Upper', 'Lower', 'Middle', 'Manual', 'Envelope', 'ManualFeed',
        'AutomaticFeed', 'TractorFeed', 'SmallFormat', 'LargeFormat',
        'LargeCapacity', 'Cassette', 'FormSource',
        ...Array.from({length: 16}, (_, i) => `Custom${i+1}`)
      )),
      ';'
    ),

    // MaxIteration Property
    // Sets a limit on the number of times that a data item will be iterated when the report is run.
    // This property is used on Report Data Items.
    max_iteration_property: $ => seq(
      'MaxIteration',
      '=',
      field('value', $.integer),
      ';'
    ),

    // MaximumDocumentCount Property
    // Sets the maximum document count when generating a report by using WordMergerDataItem.
    // This property is used on Report objects.
    maximum_document_count_property: $ => seq(
      'MaximumDocumentCount',
      '=',
      field('value', $.integer),
      ';'
    ),

    // MaximumDatasetSize Property
    // Sets the maximum amount of rows to be included on the report.
    // This property is used on Report objects.
    maximum_dataset_size_property: $ => seq(
      'MaximumDatasetSize',
      '=',
      field('value', $.integer),
      ';'
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
      $.encoding_property,
      $.field_delimiter_property,
      $.file_name_property,
      $.field_separator_property,
      $.field_validate_property,
      $.format_evaluate_property,
      $.inherent_entitlements_property,
      $.inherent_permissions_property,
      $.link_table_property,
      $.link_table_force_insert_property,
      $.max_occurs_property,
      $.min_occurs_property,
      $.namespace_prefix_property,
      $.namespaces_property,
      $.obsolete_reason_property,
      $.obsolete_state_property,
      $.obsolete_tag_property,
      $.occurrence_property,
      $.permissions_property,
      $.record_separator_property,
      $.request_filter_heading_ml_property,
      $.source_table_view_property,
      $.preserve_whitespace_property
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
      $.xmlport_property,
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

    // RecordSeparator Property
    // Sets the string that is to be used to separate records in an XMLport.
    // This property is used on XMLport objects.
    record_separator_property: $ => seq(
      'RecordSeparator',
      '=',
      field('value', choice(
        "'<NewLine>'",
        "'<CR/LF>'",
        "'<CR>'",
        "'<LF>'",
        "'<TAB>'",
        $.string_literal
      )),
      ';'
    ),

    // Occurrence Property
    // Sets a value that specifies whether an attribute must occur in the data that is being imported or exported.
    // This property is used on XMLport Field Attributes and XMLport Text Attributes.
    occurrence_property: $ => seq(
      'Occurrence',
      '=',
      field('value', choice('Required', 'Optional')),
      ';'
    ),

    // Namespaces Property
    // Specifies namespaces on the XmlPort.
    // This property is used on XMLport objects to declare one or more namespaces.
    namespaces_property: $ => seq(
      'Namespaces',
      '=',
      field('value', $.namespaces_value),
      ';'
    ),

    namespaces_value: $ => repeat1(seq(
      field('prefix', $.identifier),
      '=',
      field('namespace', $.string_literal),
      optional(',')
    )),

    // NamespacePrefix Property
    // Specifies the namespace prefix on an XmlPort element.
    // This property is used on XMLport Text Elements, XMLport Field Elements, XMLport Table Elements, XMLport Field Attributes, and XMLport Text Attributes.
    namespace_prefix_property: $ => seq(
      'NamespacePrefix',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // MinOccurs Property
    // Sets the minimum number of times that an element can occur.
    // This property is used on XMLport Text Elements, XMLport Field Elements, and XMLport Table Elements.
    min_occurs_property: $ => seq(
      'MinOccurs',
      '=',
      field('value', choice('Zero', 'Once')),
      ';'
    ),

    // MaxOccurs Property
    // Sets a value that indicates the maximum number of times an element can occur.
    // This property is used on XMLport Text Elements, XMLport Table Elements, and XMLport Field Elements.
    max_occurs_property: $ => seq(
      'MaxOccurs',
      '=',
      field('value', choice('Once', 'Unbounded')),
      ';'
    ),

    // LinkTableForceInsert Property
    // Sets whether data from the linked table is forcibly modified or inserted into a table to prevent an error from being generated.
    // This property is used on XMLport Table Elements.
    link_table_force_insert_property: $ => seq(
      'LinkTableForceInsert',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // LinkTable Property
    // Sets the table that this XML item should be linked to.
    // This property is used on XMLport Table Elements.
    link_table_property: $ => seq(
      'LinkTable',
      '=',
      field('value', $.identifier),
      ';'
    ),

    // FormatEvaluate Property
    // Sets the data that is being imported or exported as XML data types or as the standard AL data types.
    // This property is used on XMLport objects.
    format_evaluate_property: $ => seq(
      'FormatEvaluate',
      '=',
      field('value', choice('Legacy', 'Xml')),
      ';'
    ),

    // FileName Property
    // Sets the name of the external file to read data from or write data to an XMLport.
    // This property is used on XMLport objects.
    file_name_property: $ => seq(
      'FileName',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // FieldValidate Property
    // Sets a value that specifies whether the values in the source field are validated by the OnValidate (Fields) trigger for the field.
    // This property is used on XMLport Field Attributes and XMLport Field Elements.
    field_validate_property: $ => seq(
      'FieldValidate',
      '=',
      field('value', choice('Yes', 'No', 'Undefined')),
      ';'
    ),

    // FieldDelimiter Property
    // Specifies the text delimiter for a field in an XMLport.
    // This property is used on XMLport objects.
    field_delimiter_property: $ => seq(
      'FieldDelimiter',
      '=',
      field('value', choice($.string_literal, "'<None>'")),
      ';'
    ),

    // FieldSeparator Property
    // Sets the string that is to be used to separate fields in an XMLport.
    // This property is used on XMLport objects.
    field_separator_property: $ => seq(
      'FieldSeparator',
      '=',
      field('value', choice(
        "'<None>'",
        "'<NewLine>'",
        "'<CR/LF>'",
        "'<CR>'",
        "'<LF>'",
        "'<TAB>'",
        $.string_literal
      )),
      ';'
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
      $.access_property,
      $.subtype_property,
      $.event_subscriber_instance_property,
      $.inherent_entitlements_property,
      $.inherent_permissions_property,
      $.obsolete_tag_property,
      $.permissions_property,
      $.single_instance_property,
      $.test_isolation_property,
      $.test_permission_property
    ),

    // TestIsolation Property
    // Specifies the test isolation level for test codeunits.
    // This property is used on Codeunit objects with Subtype = Test.
    test_isolation_property: $ => seq(
      'TestIsolation',
      '=',
      field('value', choice('Implicit', 'Explicit', 'None')),
      ';'
    ),

    // TestPermissions Property
    // Specifies the permission set that test methods in a test codeunit run under.
    // This property is used on Codeunit objects with Subtype = Test.
    test_permission_property: $ => seq(
      'TestPermissions',
      '=',
      field('value', choice('Disabled', 'Restrictive', 'NonRestrictive', 'InheritFromTestCodunit')),
      ';'
    ),

    // SingleInstance Property
    // Sets whether a single instance of the codeunit and codeunit variables are instantiated.
    // This property is used on Codeunit objects.
    single_instance_property: $ => seq(
      'SingleInstance',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // EventSubscriberInstance Property
    // Sets whether event subscriber methods in a codeunit are bound to a specific codeunit instance.
    // This property is used on Codeunit objects.
    event_subscriber_instance_property: $ => seq(
      'EventSubscriberInstance',
      '=',
      field('value', choice('Manual', 'StaticAutomatic', 'PerSession')),  // Add 'PerSession' option
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
      $.implementation_property
    ),

    // Implementation Property
    // Specifies the explicit interface implementer for an enum value.
    // This property is used on Enum Value objects.
    implementation_property: $ => seq(
      'Implementation',
      '=',
      field('interface', $.identifier),
      '=',
      field('implementation', $.identifier),
      ';'
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
      $.entity_set_name_property,
      $.help_link_property,  // Added HelpLink property
      $.inherent_entitlements_property,
      $.inherent_permissions_property,
      $.method_property,  // Added Method property
      $.order_by_property,  // Added OrderBy property
      $.permissions_property,  // Added Permissions property
      $.query_type_property,  // Added QueryType property
      $.query_category_property,  // Added QueryCategory property
      $.read_state_property,  // Added ReadState property
      $.reverse_sign_property  // Added ReverseSign property
    ),

    // ReverseSign Property
    // Changes negative values into positive values and positive values into negative values in a column of a resulting query data set.
    // This property is used on Query Column objects.
    reverse_sign_property: $ => seq(
      'ReverseSign',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // ReadState Property
    // Specifies which records are read and how they are locked when a query is executed.
    // This property is used on Query objects.
    read_state_property: $ => seq(
      'ReadState',
      '=',
      field('value', choice('ReadUncommitted', 'ReadShared', 'ReadExclusive')),
      ';'
    ),

    // QueryType Property
    // Sets the type of the query, which determines its behavior and usage.
    // This property is used on Query objects.
    query_type_property: $ => seq(
      'QueryType',
      '=',
      field('value', choice('Normal', 'API')),
      ';'
    ),

    // QueryCategory Property
    // Specifies one or more query categories that the query supports.
    // This property is used on Query objects.
    query_category_property: $ => seq(
      'QueryCategory',
      '=',
      field('value', $.query_category_value),
      ';'
    ),

    query_category_value: $ => choice(
      $.string_literal,
      seq(
        $.string_literal,
        repeat(seq(',', $.string_literal))
      )
    ),

    // Method Property
    // Sets either a date method for retrieving the year, month, or day from a date field
    // or a totals method for performing calculations on field values.
    // This property is used on Query Column objects.
    method_property: $ => seq(
      'Method',
      '=',
      field('value', choice('Day', 'Month', 'Year', 'Sum', 'Count', 'Average', 'Min', 'Max')),
      ';'
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

    interface_property: $ => choice(
      // Interface-specific properties will be added here
      $.access_property
    ),

    permission_set_property: $ => choice(
      // Permission set-specific properties will be added here
      $.assignable_property,
      $.excluded_permission_sets_property,
      $.included_permission_sets_property,
      $.permissions_property  // Added Permissions property
    ),

    // IncludedPermissionSets Property
    // Sets the lists of other permission sets that are included in this permission set.
    // This property is used on Permission Set objects.
    included_permission_sets_property: $ => seq(
      'IncludedPermissionSets',
      '=',
      field('value', $.identifier_list),
      ';'
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
      $.enabled_property,
      $.profile_description_property,  // Added ProfileDescription property
      $.role_center_property  // Added RoleCenter property
    ),

    // RoleCenter Property
    // Specifies the Role Center Page for this profile.
    // This property is used on Profile objects.
    role_center_property: $ => seq(
      'RoleCenter',
      '=',
      field('value', $.identifier),
      ';'
    ),

    // ProfileDescription Property
    // Sets the description of the profile that users will see in the UI.
    // This property is used on Profile objects.
    profile_description_property: $ => seq(
      'ProfileDescription',
      '=',
      field('value', $.string_literal),
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
      $.requested_width_property,
      $.recreate_script_property,  // Added RecreateScript property
      $.refresh_script_property,  // Added RefreshScript property
      $.scripts_property  // Added Scripts property
    ),

    // Scripts Property
    // Specifies the list of scripts to include in the control add-in.
    // This property is used on Control Add In objects.
    scripts_property: $ => seq(
      'Scripts',
      '=',
      field('value', $.array_value),
      ';'
    ),

    // RequestedWidth Property
    // Specifies the initial width of the control add-in.
    // This property is used on Control Add In objects.
    requested_width_property: $ => seq(
      'RequestedWidth',
      '=',
      field('value', $.integer),
      ';'
    ),

    // RequestedHeight Property
    // Specifies the initial height of the control add-in.
    // This property is used on Control Add In objects.
    requested_height_property: $ => seq(
      'RequestedHeight',
      '=',
      field('value', $.integer),
      ';'
    ),

    // RefreshScript Property
    // Specifies the script which is invoked when the control add-in is refreshed.
    // This property is used on Control Add In objects.
    refresh_script_property: $ => seq(
      'RefreshScript',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // MinimumWidth Property
    // Specifies the minimum width that the control add-in can be shrunk to.
    // This setting only applies if the HorizontalShrink setting is specified.
    minimum_width_property: $ => seq(
      'MinimumWidth',
      '=',
      field('value', $.integer),
      ';'
    ),

    // MinimumHeight Property
    // Specifies the minimum height that the control add-in can be shrunk to.
    // This property is used on Control Add In objects and only applies if VerticalShrink is set to true.
    minimum_height_property: $ => seq(
      'MinimumHeight',
      '=',
      field('value', $.integer),
      ';'
    ),

    // MaximumHeight Property
    // Specifies the maximum height that the control add-in can be stretched to.
    // This property is used on Control Add In objects.
    maximum_height_property: $ => seq(
      'MaximumHeight',
      '=',
      field('value', $.integer),
      ';'
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

    // OptionCaption Property
    // Sets the string options that are displayed to the user for Option type fields.
    // This property is used on Table Fields, Page Fields, and Report Columns.
    option_caption_property: $ => seq(
      'OptionCaption',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // InitValue Property
    // Sets the initial value of this field when a user creates a new record.
    // This property is used on Table Fields.
    init_value_property: $ => seq(
      'InitValue',
      '=',
      field('value', $._value),
      ';'
    ),

    // MaxValue Property
    // Sets the maximum numeric value for a field.
    // This property is used on Table Fields and Page Fields.
    max_value_property: $ => seq(
      'MaxValue',
      '=',
      field('value', $._value),
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

    // FileUploadRowAction Property
    // Specifies the File Upload Action to be invoked when a file is uploaded to the row.
    // This property is used on Page Groups.
    file_upload_row_action_property: $ => seq(
      'FileUploadRowAction',
      '=',
      field('value', $.identifier),
      ';'
    ),

    // FlowCaption Property
    // Sets the default caption of the new flow.
    // This property is used on Page Custom Actions.
    flow_caption_property: $ => seq(
      'FlowCaption',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // FlowId Property
    // Sets the ID of the Power Automate Flow triggered by this action.
    // This property is used on Page Custom Actions.
    flow_id_property: $ => seq(
      'FlowId',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // FlowTemplateCategoryName Property
    // Sets the category used to filter the list of Power Automate templates shown in the template gallery.
    // This property is used on Page Custom Actions.
    flow_template_category_name_property: $ => seq(
      'FlowTemplateCategoryName',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // FlowTemplateId Property
    // Sets the ID of the Power Automate template triggered by this action.
    // This property is used on Page Custom Actions.
    flow_template_id_property: $ => seq(
      'FlowTemplateId',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // FreezeColumn Property
    // Specifies the columns in a list that remain in view on a page, even when you scroll right.
    // This property is used on Page Groups.
    freeze_column_property: $ => seq(
      'FreezeColumn',
      '=',
      field('value', $.identifier),
      ';'
    ),

    // Gesture Property
    // Specifies a gesture that runs the action on a device with a touch interface, such as the phone client.
    // This property is used on Page Actions and Page File Upload Actions.
    gesture_property: $ => seq(
      'Gesture',
      '=',
      field('value', choice('None', 'LeftSwipe', 'RightSwipe', 'ContextMenu')),
      ';'
    ),

    // GridLayout Property
    // Specifies if the layout is rows or columns.
    // This property is used on Page Groups.
    grid_layout_property: $ => seq(
      'GridLayout',
      '=',
      field('value', choice('Rows', 'Columns')),
      ';'
    ),

    // HelpLink Property
    // Specifies the help link to show when the user presses Help in the UI.
    // This property is used on Page, Request Page, and Query objects.
    help_link_property: $ => seq(
      'HelpLink',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // OrderBy Property
    // Sorts table fields in the page view in ascending or descending order.
    // This property is used on Page View and Query objects.
    order_by_property: $ => seq(
      'OrderBy',
      '=',
      field('value', $.order_by_value),
      ';'
    ),

    order_by_value: $ => seq(
      repeat1(seq(
        field('direction', choice('Ascending', 'Descending')),
        '(',
        field('field', $.identifier),
        ')',
        optional(',')
      ))
    ),

    // PageType Property
    // Sets the type of the page, which determines its behavior and appearance.
    // This property is used on Page objects.
    page_type_property: $ => seq(
      'PageType',
      '=',
      field('value', choice(
        'Card',
        'List',
        'RoleCenter',
        'CardPart',
        'ListPart',
        'Document',
        'Worksheet',
        'ListPlus',
        'ConfirmationDialog',
        'NavigatePage',
        'StandardDialog',
        'API',
        'HeadlinePart',
        'PromptDialog'
      )),
      ';'
    ),

    field_property: $ => choice(
      $.caption_property,
      $.tooltip_property,
      $.visible_property,
      $.editable_property,
      // ... other field properties
    ),

    part_property: $ => choice(
      $.page_id_property,
      $.provider_property,
      $.editable_property,
      // ... other part properties
    ),

    system_part_property: $ => choice(
      $.system_part_id_property,
      // ... other system part properties
    ),

    page_id_property: $ => seq(
      'PagePartID',
      '=',
      field('value', choice($.integer, $.identifier)),
      ';'
    ),

    system_part_id_property: $ => seq(
      'SystemPartID',
      '=',
      field('value', $.identifier),
      ';'
    ),

    tooltip_property: $ => seq(
      'ToolTip',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    visible_property: $ => seq(
      'Visible',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // FormatRegion Property
    // Sets the format region that will be used when formatting numbers and date/time values.
    // This property is used on Report objects.
    format_region_property: $ => seq(
      'FormatRegion',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // FlowEnvironmentId Property
    // Sets the ID of the environment where the Power Automate Flow triggered by this action is located.
    // This property is used on Page Custom Actions.
    flow_environment_id_property: $ => seq(
      'FlowEnvironmentId',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // Filters Property
    // Sets a set of filters for the page that will be applied for this page view.
    // This property is used on Page Views.
    filters_property: $ => seq(
      'Filters',
      '=',
      field('value', $.filters_value),
      ';'
    ),

    filters_value: $ => seq(
      'WHERE',
      '(',
      $.table_filters,
      ')'
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
      $.object_entitlements_property,
      $.role_type_property
    ),

    // RoleType Property
    // Specifies whether the role is local or delegated when the entitlement type is Role.
    // This property is used on Entitlement objects.
    role_type_property: $ => seq(
      'RoleType',
      '=',
      field('value', choice('Local', 'Delegated')),
      ';'
    ),

    // ObjectEntitlements Property
    // Determines the object permissions that this entitlement object permits a user or application to use.
    // This property is used on Entitlement objects.
    object_entitlements_property: $ => seq(
      'ObjectEntitlements',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    report_layout_property: $ => choice(
      // Report layout-specific properties will be added here
      $.mime_type_property
    ),

    // MimeType Property
    // Sets the mimetype that is associated with this custom report layout.
    // This property is used on Report Layout objects.
    mime_type_property: $ => seq(
      'MimeType',
      '=',
      field('value', $.string_literal),
      ';'
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

    string: $ => /"(?:[^"\\]|\\.)*"/,
    integer: $ => /\d+/,
    // Identifiers
    identifier: $ => /[a-zA-Z_][a-zA-Z0-9_]*([A-Z][a-z0-9_]*)*(\.[a-zA-Z_][a-zA-Z0-9_]*([A-Z][a-z0-9_]*)*)?/,

    fully_qualified_identifier: $ => seq(
      optional(seq($.qualified_namespace, '.')),
      $.identifier
    ),

    // Helper rule for a list of identifiers
    identifier_list: $ => seq(
      $.fully_qualified_identifier,
      repeat(seq(',', $.fully_qualified_identifier))
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

    boolean_literal: $ => choice(/[tT][rR][uU][eE]/, /[fF][aA][lL][sS][eE]/),

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

    datetime_literal: $ => prec(1, choice(
      seq($.date_literal, $.time_literal),
      /\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}:\d{2}/,
      /0DT/
    )),

    // Operators
    _operator: $ => choice(
      $.arithmetic_operator,
      $.comparison_operator,
      $.logical_operator,
      $.assignment_operator
    ),

    arithmetic_operator: $ => choice('+', '-', '*', '/', /[dD][iI][vV]/, /[mM][oO][dD]/),

    comparison_operator: $ => choice('=', '<>', '<', '>', '<=', '>='),

    logical_operator: $ => choice(/[aA][nN][dD]/, /[oO][rR]/, /[nN][oO][tT]/, /[xX][oO][rR]/),

    assignment_operator: $ => ':=',

    // PublicKeyToken Property
    // Specifies the public key token of the .NET assembly.
    // This property is used on Dot Net Assembly objects.
    public_key_token_property: $ => seq(
      'PublicKeyToken',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // RecreateScript Property
    // Specifies the script which is invoked when the control add-in is recreated.
    // This property is used on Control Add In objects.
    recreate_script_property: $ => seq(
      'RecreateScript',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // RequestFilterFields Property
    // Sets which fields are automatically included on the tab of the request page that is related to this data item.
    // The user can set filters on these fields.
    // This property is used on Report Data Items and XMLport Table Elements.
    request_filter_fields_property: $ => seq(
      'RequestFilterFields',
      '=',
      field('value', $.identifier_list),
      ';'
    ),

    // SourceTableTemporary Property
    // Sets whether the source table is a temporary table.
    // This property is used on Page and Request Page objects.
    source_table_temporary_property: $ => seq(
      'SourceTableTemporary',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    // SourceTableView Property
    // Sets the key, sort order, and filter to determine the view of the source table presented to the user.
    // This property is used on Page objects and XMLport Table Elements.
    source_table_view_property: $ => seq(
      'SourceTableView',
      '=',
      field('value', $.string_literal),
      ';'
    ),
  }
});
