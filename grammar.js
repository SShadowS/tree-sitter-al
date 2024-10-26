
// Precedence constants
const PREC = {
  COMPOUND_IDENTIFIER: 1,
  CASE_BRANCH: 2,
  TERNARY: 1,
  UNARY: 3,
  MEMBER: 4,
  CALL: 5,
};

// Token definitions and helper constants
const colon = ':';

// Helper functions for property definitions
function ci(keyword) {
  if (typeof keyword !== 'string') {
    return keyword;
  }
  return new RegExp(
    keyword
      .split('')
      .map(c => `[${c.toLowerCase()}${c.toUpperCase()}]`)
      .join('')
  );
}

function makeSimpleProperty($, name, valueTypeFn) {
  const propName = name instanceof RegExp ? name : ci(name.toString());
  return seq(
    token(propName),
    '=',
    field('value', valueTypeFn($)),
    ';'
  );
}

function makeChoiceProperty($, name, choicesFn) {
  const propName = name instanceof RegExp ? name : ci(name);
  return seq(
    token(propName),
    '=',
    field('value', choicesFn($)),
    ';'
  );
}

function makeTrigger($, name, paramsFn) {
  const triggerName = name instanceof RegExp ? name : ci(name);
  return seq(
    token(ci('trigger')),
    token(triggerName),
    '(',
    paramsFn ? paramsFn($) : seq(),
    ')',
    optional($.variable_declaration),
    field('body', $.code_block)
  );
}

function makeObject($, type, elementsFn) {
  return seq(
    type,
    field('id', $.integer),
    field('name', $.identifier),
    '{',
    repeat(elementsFn($)),
    '}'
  );
}


// Common property groups
const commonProperties = $ => choice(
  $.access_property,
  $.caption_property, 
  $.caption_ml_property,
  $.obsolete_reason_property,
  $.obsolete_state_property,
  $.obsolete_tag_property
);

// Common property value types
const propertyValues = $ => choice(
  $.boolean_literal,
  $.string_literal,
  $.identifier,
  $.integer,
  $._expression
);

module.exports = grammar({
  name: 'al',

  extras: $ => [
    /\s/,
    $.comment
  ],

  rules: {
    source_file: $ => seq(
      optional($.namespace_declaration),
      optional(repeat($.using_directive)),
      repeat1(choice(
        $._declaration,
        $.comment
      ))
    ),

    // Token definition for '::'
    double_colon: $ => '::',

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
    dotnet_assembly_object: $ => seq(
      'dotnetassembly',
      field('name', $.identifier),
      '{',
      repeat($._dotnet_assembly_element),
      '}'
    ),

    _dotnet_assembly_element: $ => choice(
      $.property,
      $.public_key_token_property,
      $.culture_property
    ),
    public_key_token_property: $ => seq(
      'PublicKeyToken',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    interface_object: $ => seq(
      'interface',
      field('name', $.identifier),
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

    dotnet_package_object: $ => seq(
      'dotnetpackage',
      field('name', $.identifier),
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
    culture_property: $ => seq(
      'Culture',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    enum_extension_object: $ => seq(
      'enumextension',
      field('id', $.integer),
      field('name', $.identifier),
      'extends',
      field('base_enum', $.identifier),
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
      field('name', $.identifier),
      'extends',
      field('base_query', $.identifier),
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
      field('name', $.identifier),
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
      field('name', $.identifier),
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
      field('name', $.identifier),
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

    calc_fields_property: $ => seq(
      'CalcFields',
      '=',
      field('value', $.identifier_list),
      ';'
    ),
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
      field('name', $.identifier),
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
      field('name', $.identifier),
      'extends',
      field('base_table', $.identifier),
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

    table_fields: $ => seq(
      'fields',
      '{',
      repeat($.table_field),
      '}'
    ),

    report_object: $ => seq(
      'report',
      field('id', $.integer),
      field('name', $.identifier),
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
      $.dataitem,
      $.add,
      $.modify
    ),

    dataitem: $ => prec.right(2, seq(
      'dataitem',
      '(',
      field('name', $.identifier),
      ';',
      field('table', $.identifier),
      ')',
      '{',
      repeat($._dataitem_element),
      optional($.data_item_link_property),
      '}'
    )),

    _dataitem_element: $ => prec.left(1, choice(
      $.property,
      $.calc_fields_property,
      $.data_item_link_reference_property,
      $.data_item_table_view_property
    )),
    data_item_link_reference_property: $ => seq(
      'DataItemLinkReference',
      '=',
      field('value', $.identifier),
      ';'
    ),
    data_item_table_view_property: $ => seq(
      'DataItemTableView',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    report_extension_object: $ => seq(
      'reportextension',
      field('id', $.integer),
      field('name', $.identifier),
      'extends',
      field('base_report', $.identifier),
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

    add: $ => seq(
      'add',
      '(',
      field('dataitem', $.identifier),
      ')',
      '{',
      repeat($.column),
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
      $.layout,
      $.actions,
      $.property,
      $.instructional_text_property,
      $.links_allowed_property,
      $.save_values_property,
      $.source_table_temporary_property
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
      field('name', $.identifier),
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

    _dataitem_element: $ => choice(
      $.column,
      $.dataitem,
      $.property,
      $.data_item_link_property,
      $.data_item_table_filter_property
    ),
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
      field('name', $.identifier),
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
      field('name', $.identifier),
      'extends',
      field('base_permission_set', $.identifier),
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
      ci('page'),
      field('id', $.integer),
      field('name', $.identifier),
      optional(ci('API')),
      '{',
      repeat($._page_element),
      '}'
    ),
    application_area_property: $ => seq(
      ci('ApplicationArea'),
      '=',
      field('value', choice($.identifier, $.array_value)),
      ';'
    ),
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
      ci('action'),
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat(choice($.page_action_property, $.trigger, $.var)),
      '}'
    ),

    page_action_separator: $ => seq(
      ci('separator'),
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
      ci('customaction'),
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat(choice($.property, $.trigger)),
      '}'
    ),

    page_system_action: $ => seq(
      ci('systemaction'),
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat(choice($.property, $.trigger)),
      '}'
    ),

    page_file_upload_action: $ => seq(
      ci('fileuploadaction'),
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat(choice($.property, $.trigger)),
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

    part: $ => seq(
      'part',
      '(',
      field('name', $.identifier),
      ';',
      field('part_name', $.identifier),
      ')',
      '{',
      repeat(choice($.property, $.part_property)),
      '}'
    ),

    systempart: $ => seq(
      'systempart',
      '(',
      field('name', choice($.identifier, $.string_literal)),
      ';',
      field('system_part_name', choice($.identifier, $.string_literal)),
      ')',
      '{',
      repeat($.property),
      '}'
    ),
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
    onopenpage_trigger: $ => seq(
      'trigger',
      'OnOpenPage',
      '(',
      ')',
      optional($.variable_declaration),
      field('body', $.code_block)
    ),
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
    oninit_trigger: $ => seq(
      'trigger',
      'OnInit',
      '(',
      ')',
      optional($.variable_declaration),
      field('body', $.code_block)
    ),
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
    onaftergetcurrrecord_trigger: $ => seq(
      'trigger',
      'OnAfterGetCurrRecord',
      '(',
      ')',
      optional($.variable_declaration),
      field('body', $.code_block)
    ),
    onaftergetrecord_trigger: $ => prec.right(seq(
      'trigger',
      'OnAfterGetRecord',
      '(',
      ')',
      optional($.var),
      field('body', $.code_block),
      optional(';')
    )),
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
      field('name', $.identifier),
      'extends',
      field('base_page', $.identifier),
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
      ci('area'),
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($._area_element),
      '}'
    ),

    _area_element: $ => choice(
      $.repeater,
      $.group,
      $.part,
      $.system_part,
      $.page_field,
      $.cue_group
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
      $.page_field,
      $.part,
      $.group,
      $.cue_group,
      $.system_part
    ),

    field: $ => seq(
      ci('field'),
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($.field_property),
      '}'
    ),

    system_part: $ => seq(
      'systempart',
      '(',
      field('name', choice($.identifier, $.string_literal)),
      ';',
      field('system_part_name', choice($.identifier, $.string_literal)),
      ')',
      '{',
      repeat($.property),
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
      $.page_field,
      $.part
    ),

    repeater: $ => seq(
      ci('repeater'),
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($._repeater_content),
      '}'
    ),

    _repeater_content: $ => choice(
      $.page_field,
      $.group
    ),

    actions: $ => seq(
      ci('actions'),
      '{',
      repeat($._action_element),
      '}'
    ),

    _action_element: $ => choice(
      $.action_area,
      $.action_group,
      $.page_action,
      $.page_action_separator,
      $.page_system_action,
      $.page_file_upload_action,
      $.page_custom_action,
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
    ),

    layout_property: $ => seq(
      'Layout',
      '=',
      field('value', $.string_literal),
      ';'
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

    action_area: $ => seq(
      ci('area'),
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($._action_element),
      '}'
    ),

    action_group: $ => seq(
      ci('group'),
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($._action_element),
      '}'
    ),

    _customization_content: $ => choice(
      $.field,
      $.group,
      $.action
    ),

    action: $ => seq(
      ci('action'),
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    entitlement_object: $ => seq(
      'entitlement',
      field('name', $.identifier),
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
      field('name', $.identifier),
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
    event_subscriber: $ => seq(
      '[EventSubscriber(',
      $.event_subscriber_params,
      ')]',
      $.procedure
    ),

    event_subscriber_params: $ => seq(
      field('object_type', $.object_type),
      ',',
      field('object_id', $.identifier),
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

    event_subscriber_params: $ => seq(
      field('object_type', $.object_type),
      ',',
      field('object_id', $.identifier),
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
        $.table_fields,
        $.keys,
        $.caption_property,
        $.table_data_classification_property,
        $.data_caption_fields_property,
        $.drilldown_page_id_property,
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
        $.event_subscriber,
        $.trigger,
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

    var: $ => prec.left(seq(
      ci('var'),
      repeat1($.variable_declaration)
    )),

    variable_declaration: $ => choice(
      seq(
        field('name', $.identifier),
        ':',
        field('type', $._type),
        ';'
      ),
      $.label_declaration
    ),

    label_declaration: $ => prec(2, seq(
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
    )),

    _page_element: $ => seq(
      choice(
        $.layout,
        $.actions,
        $.views,
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
        $.onaftergetrecord_trigger,
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
        $.var,
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
    onvalidateupgradeperdatabase_trigger: $ => seq(
      'trigger',
      'OnValidateUpgradePerDatabase',
      '(',
      ')',
      optional($.variable_declaration),
      field('body', $.code_block)
    ),
    onvalidateupgradepercompany_trigger: $ => seq(
      'trigger',
      'OnValidateUpgradePerCompany',
      '(',
      ')',
      optional($.variable_declaration),
      field('body', $.code_block)
    ),
    onupgradeperdatabase_trigger: $ => seq(
      'trigger',
      'OnUpgradePerDatabase',
      '(',
      ')',
      optional($.variable_declaration),
      field('body', $.code_block)
    ),
    onupgradepercompany_trigger: $ => seq(
      'trigger',
      'OnUpgradePerCompany',
      '(',
      ')',
      optional($.variable_declaration),
      field('body', $.code_block)
    ),
    onrun_trigger: $ => seq(
      'trigger',
      'OnRun',
      '(',
      ')',
      optional($.variable_declaration),
      field('body', $.code_block)
    ),
    oninstallappperdatabase_trigger: $ => seq(
      'trigger',
      'OnInstallAppPerDatabase',
      '(',
      ')',
      optional($.variable_declaration),
      field('body', $.code_block)
    ),
    oninstallapppercompany_trigger: $ => seq(
      'trigger',
      'OnInstallAppPerCompany',
      '(',
      ')',
      optional($.variable_declaration),
      field('body', $.code_block)
    ),
    oncheckpreconditionsperdatabase_trigger: $ => seq(
      'trigger',
      'OnCheckPreconditionsPerDatabase',
      '(',
      ')',
      optional($.variable_declaration),
      field('body', $.code_block)
    ),
    oncheckpreconditionspercompany_trigger: $ => seq(
      'trigger',
      'OnCheckPreconditionsPerCompany',
      '(',
      ')',
      optional($.variable_declaration),
      field('body', $.code_block)
    ),
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

    trigger: $ => prec.right(1, seq(
      repeat($.attribute),
      ci('trigger'),
      field('name', choice(
        ci('OnInsert'),
        ci('OnModify'), 
        ci('OnDelete'),
        ci('OnRename'),
        ci('OnValidate'),
        ci('OnLookup'),
        ci('OnAfterLookup'),
        $.identifier
      )),
      '(',
      optional($._parameter_list),
      ')',
      optional($.var),
      field('body', $.code_block),
      optional(';')
    )),

    named_type: $ => prec(3, seq(
      field('base_type', choice(
        'Table', 'Record', 'Page', 'Report', 'XmlPort', 'Query',
        'Enum', 'DotNet', 'Interface', 'Codeunit'
      )),
      field('subtype', choice($.identifier, $.string_literal))
    )),

    _type: $ => prec(2, choice(
      $._variable_data_type,
      $.sized_data_type,
      $.record_type,
      $.named_type,
      $.array_type
    )),

    array_type: $ => prec.right(2, seq(
      /[aA][rR][rR][aA][yY]/,
      '[',
      field('size', $.integer),
      ']',
      /[oO][fF]/,
      field('element_type', $._type)
    )),

    _variable_data_type: $ => prec(1, choice(
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
    )),

    // simple_type: $ => $.identifier,

    procedure: $ => prec(1, seq(
      repeat($.attribute),
      optional(ci('local')),
      ci('procedure'),
      field('name', $.identifier),
      '(',
      optional($._parameter_list),
      ')',
      optional(seq(
        field('return_var', optional($.identifier)),
        ':',
        field('return_type', $._type)
      )),
      optional(';'),
      optional($.var),
      field('body', $.code_block)
    )),

    attribute: $ => seq(
      '[',
      field('attribute_name', $.identifier),
      optional(seq(
        '(',
        optional(field('attribute_arguments', $.attribute_arguments)),
        ')'
      )),
      ']'
    ),

    attribute_arguments: $ => seq(
      $._attribute_argument,
      repeat(seq(',', $._attribute_argument))
    ),

    _attribute_argument: $ => choice(
      seq(
        field('argument_name', $.identifier),
        ':=',
        field('argument_value', $._expression)
      ),
      $._expression
    ),

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

    record_type: $ => prec(2, seq(
      'Record',
      field('table_reference', $.identifier )
    )),

    code_block: $ => prec.left(seq(
      ci('begin'),
      repeat($._statement),
      ci('end'),
      optional(';')
    )),

    _statement: $ => choice(
      $.assignment_statement,
      $.if_statement,
      $.case_statement,
      $.for_statement,
      $.while_statement,
      $.repeat_statement,
      $.exit_statement,
      $.with_statement,
      $.error_statement,
      $.message_statement,
      $.assert_error_statement,
      $.break_statement,
      $.continue_statement,
      $.expression_statement
    ),

    expression_statement: $ => seq(
      $._expression,
      optional(';')
    ),

    assignment_statement: $ => prec.left(0, seq(
      field('variable', $._lvalue_expression),
      ':=',
      field('value', $._expression),
      ';'
    )),

    if_statement: $ => prec.right(seq(
      ci('if'),
      field('condition', $._expression),
      ci('then'),
      field('then_body', choice($._statement, $.code_block)),
      optional(seq(
        ci('else'),
        field('else_body', choice($._statement, $.code_block))
      ))
    )),

    case_statement: $ => prec.left(1, seq(
      /[cC][aA][sS][eE]/,
      field('expression', choice(
        $.string,
        $.identifier, 
        $.enum_identifier,
        $._expression
      )),
      /[oO][fF]/,
      repeat1($.case_branch),
      optional(seq(
        /[eE][lL][sS][eE]/,
        field('else_body', choice(
          $._statement,
          $.code_block
        ))
      )),
      /[eE][nN][dD]/,
      optional(';')
    )),

    case_branch: $ => prec.left(PREC.CASE_BRANCH, seq(
      field('values', seq(
        choice($._literal, $.identifier),
        repeat(seq(',', choice($._literal, $.identifier)))
      )),
      colon,
      field('body', choice(
        $._statement,
        $.code_block
      ))
    )),
   
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
      field('body', $.repeat_code_block),
      /[uU][nN][tT][iI][lL]/,
      field('condition', $._expression),
      ';'
    ),

    repeat_code_block: $ => repeat1($._statement),

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

    exit_statement: $ => prec.left(seq(
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
    )),

    with_statement: $ => seq(
      /[wW][iI][tT][hH]/,
      field('record', $.identifier),
      /[dD][oO]/,
      field('body', $.code_block)
    ),

    error_statement: $ => seq(
      /[eE][rR][rR][oO][rR]/,
      '(',
      field('message', $._expression),
      ')',
      optional(';')
    ),

    message_statement: $ => seq(
      /[mM][eE][sS][sS][aA][gG][eE]/,
      '(',
      field('message', $._expression),
      ')',
      optional(';')
    ),

    assert_error_statement: $ => seq(
      /[aA][sS][sS][eE][rR][tT][eE][rR][rR][oO][rR]/,
      field('expression', $._expression),
      optional(';')
    ),

    break_statement: $ => seq(
      /[bB][rR][eE][aA][kK]/,
      optional(';')
    ),

    continue_statement: $ => seq(
      /[cC][oO][nN][tT][iI][nN][uU][eE]/,
      optional(';')
    ),

    _argument_list: $ => prec.left(seq(
      $._expression,
      repeat(seq(',', $._expression))
    )),

    _expression: $ => prec.right(2, choice(
      $._literal,
      $.identifier,
      $.enum_identifier,
      $.database_reference,
      $.parenthesized_expression, 
      $.unary_expression,
      $.call_expression,
      $.member_expression,
      $.array_access_expression,
      $.ternary_expression,
      $.binary_expression
    )),

    database_reference: $ => seq(
      'DATABASE',
      '::',
      $.identifier
    ),

    binary_expression: $ => {
      const table = [
        [6, choice('*', '/', ci('div'), ci('mod'))],
        [5, choice('+', '-')],
        [4, choice('=', '<>', '<', '>', '<=', '>=')],
        [3, ci('and')],
        [2, ci('or')]
      ];
      return choice(...table.map(([precedence, operator]) =>
        prec.left(precedence, seq(
          field('left', $._expression),
          field('operator', operator),
          field('right', $._expression)
        ))
      ));
    },


    call_expression: $ => prec.left(2, seq(
      field('function', $._expression),
      '(',
      optional($._argument_list),
      ')'
    )),

    member_expression: $ => prec.left(3, seq(
      field('object', $._expression),
      '.',
      field('member', seq(
        field('name', $.identifier)
      ))
    )),

    setrange_call: $ => seq(
      /[sS][eE][tT][rR][aA][nN][gG][eE]/,
      '(',
      field('field', $.identifier),
      ',',
      field('from_value', $._expression),
      optional(seq(',', field('to_value', $._expression))),
      ')'
    ),

    setfilter_call: $ => seq(
      /[sS][eE][tT][fF][iI][lL][tT][eE][rR]/,
      '(',
      field('field', $.identifier),
      ',',
      field('filter_string', choice($.string_literal, $._expression)),
      ')'
    ),

    ternary_expression: $ => prec.right(PREC.TERNARY, seq(
      field('condition', $._expression),
      '?', 
      field('true_expression', $._expression),
      colon,
      field('false_expression', $._expression)
    )),


    unary_expression: $ => prec(8, seq(
      field('operator', choice('-', ci('not'))),
      field('operand', $._expression)
    )),

    parenthesized_expression: $ => prec(10, seq(
      '(',
      $._expression,
      ')'
    )),


    member_access_expression: $ => prec.left(9, seq(
      field('object', $._expression),
      '.',
      field('member', $.identifier)
    )),

    array_access_expression: $ => prec(9, seq(
      field('array', $._expression),
      '[',
      field('index', $._expression),
      ']'
    )),

    _lvalue_expression: $ => choice(
      $.identifier,
      $.member_expression,
      $.array_access_expression
    ),

    ternary_expression: $ => prec.right(PREC.TERNARY, seq(
      field('condition', $._expression),
      '?',
      field('true_expression', $._expression),
      colon,
      field('false_expression', $._expression)
    )),

    table_object: $ => seq(
      'table',
      field('id', $.integer),
      field('name', $.identifier),
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
    key_field_list: $ => seq(
      $.key_field,
      repeat(seq(',', $.key_field))
    ),
    key_field: $ => choice(
      $.identifier,
      $.string
    ),
    clustered_property: $ => seq(
      'Clustered',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    unique_property: $ => seq(
      'Unique',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    included_fields_property: $ => seq(
      'IncludedFields',
      '=',
      field('value', $.identifier_list),
      ';'
    ),
    column_store_index_property: $ => seq(
      'ColumnStoreIndex',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    table_field: $ => seq(
      'field',
      '(',
      field('id', $.integer),
      ';',
      field('name', choice($.string, $.identifier)),
      ';',
      field('data_type', $._table_data_type),
      ')',
      '{',
      repeat(choice(
        $.field_property,
        $.field_trigger
      )),
      '}'
    ),

    field_trigger: $ => seq(
      repeat($.attribute),
      'trigger',
      field('name', choice(
        'OnValidate',
        'OnLookup',
        'OnAfterLookup'
      )),
      '(',
      ')',
      optional($.var),
      field('body', $.code_block),
      optional(';')
    ),

    page_field: $ => seq(
      'field',
      '(',
      field('name', choice($.identifier, $.string_literal)),
      ';',
      field('source_expression', $._expression),
      ')',
      '{',
      repeat(choice($.field_property, $.trigger)),
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
      ),
      seq(
        'Enum',
        field('enum_type', $.identifier)
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

    sized_data_type: $ => prec(2, seq(
      choice('Code', 'Text'),
      '[',
      $.integer,
      ']'
    )),
    property: $ => seq(
      field('name', $.identifier),
      '=',
      field('value', $._value),
      ';'
    ),
    table_property: $ => choice(
      $.access_property,
      $.caption_property,
      $.caption_ml_property,
      $.column_store_index_property,
      $.compression_type_property,
      $.data_caption_fields_property,
      $.table_data_classification_property,
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
    data_classification_fields_property: $ => seq(
      'DataClassificationFields',
      '=',
      field('value', $.identifier_list),
      ';'
    ),
    replicate_data_property: $ => seq(
      'ReplicateData',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    table_type_property: $ => seq(
      'TableType',
      '=',
      field('value', choice('Normal', 'CRM', 'ExternalSQL', 'MicrosoftGraph', 'Temporary')),
      ';'
    ),
    scope_property: $ => seq(
      'Scope',
      '=',
      field('value', choice('Cloud', 'OnPrem')),
      ';'
    ),
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
    about_title_property: $ => seq(
      'AboutTitle',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    lookup_page_id_property: $ => seq(
      'LookupPageId',
      '=',
      field('value', $.identifier),
      ';'
    ),
    paste_is_valid_property: $ => seq(
      'PasteIsValid',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
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
    obsolete_tag_property: $ => seq(
      'ObsoleteTag',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    odata_edm_type_property: $ => seq(
      'ODataEDMType',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    odata_key_fields_property: $ => seq(
      'ODataKeyFields',
      '=',
      field('value', $.identifier_list),
      ';'
    ),
    obsolete_reason_property: $ => seq(
      'ObsoleteReason',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    obsolete_state_property: $ => seq(
      'ObsoleteState',
      '=',
      field('value', choice('Pending', 'Removed')),
      ';'
    ),
    moved_to_property: $ => seq(
      'MovedTo',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    moved_from_property: $ => seq(
      'MovedFrom',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    linked_object_property: $ => seq(
      'LinkedObject',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    linked_in_transaction_property: $ => seq(
      'LinkedInTransaction',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    about_text_ml_property: $ => seq(
      'AboutTextML',
      '=',
      field('value', $.multilanguage_string_literal),
      ';'
    ),
    key_property: $ => seq(
      'Key',
      '(',
      field('fields', $.identifier_list),
      ')',
      ';'
    ),
    is_control_addin_property: $ => seq(
      'IsControlAddIn',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    enabled_property: $ => prec(2, makeSimpleProperty($, 'Enabled', $ => choice($.boolean_literal, $.identifier))),
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
    caption_ml_property: $ => seq(
      'CaptionML',
      '=',
      field('value', $.multilanguage_string_literal),
      ';'
    ),
    multilanguage_string_literal: $ => seq(
      repeat1(seq(
        field('language_code', $.identifier),
        '=',
        field('text', $.string_literal),
        optional(',')
      ))
    ),
    compression_type_property: $ => seq(
      'CompressionType',
      '=',
      field('value', choice('None', 'Row', 'Page', 'Unspecified')),
      ';'
    ),
    column_store_index_property: $ => seq(
      'ColumnStoreIndex',
      '=',
      field('value', $.identifier_list),
      ';'
    ),

    field_property: $ => choice(
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
      $.field_data_classification_property,
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
      $.sign_displacement_property,
      $.source_expr_property,
      $.table_relation_property,
      $.application_area_property,
      $.tooltip_property,
      $.lookup_page_id_property,
      $.visible_property  // Add this line
    ),

    source_expr_property: $ => seq(
      ci('SourceExpr'),
      '=',
      field('value', $._expression),
      ';'
    ),
    sign_displacement_property: $ => seq(
      'SignDisplacement',
      '=',
      field('value', $.integer),
      ';'
    ),
    quick_entry_property: $ => seq(
      'QuickEntry',
      '=',
      field('value', choice($.boolean_literal, $.identifier)),
      ';'
    ),
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
    option_caption_ml_property: $ => seq(
      'OptionCaptionML',
      '=',
      field('value', $.multilanguage_string_literal),
      ';'
    ),
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
    not_blank_property: $ => seq(
      'NotBlank',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    numeric_property: $ => seq(
      'Numeric',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    navigation_page_id_property: $ => seq(
      'NavigationPageId',
      '=',
      field('value', $.identifier),
      ';'
    ),
    min_value_property: $ => seq(
      'MinValue',
      '=',
      field('value', $._value),
      ';'
    ),
    external_access_property: $ => seq(
      'ExternalAccess',
      '=',
      field('value', choice('Full', 'Insert', 'Modify', 'Read')),
      ';'
    ),
    external_name_property: $ => seq(
      'ExternalName',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    external_type_property: $ => seq(
      'ExternalType',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    field_class_property: $ => seq(
      'FieldClass',
      '=',
      field('value', seq(optional('"'), choice('Normal', 'FlowField', 'FlowFilter'),optional('"'))),
      ';'
    ),
    external_schema_property: $ => seq(
      'ExternalSchema',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    inherent_entitlements_property: $ => seq(
      'InherentEntitlements',
      '=',
      field('value', $.inherent_entitlements_value),
      ';'
    ),

    inherent_entitlements_value: $ => repeat1(choice('R', 'I', 'M', 'D', 'X')),
    inherent_permissions_property: $ => seq(
      'InherentPermissions',
      '=',
      field('value', $.inherent_permissions_value),
      ';'
    ),

    inherent_permissions_value: $ => repeat1(choice('R', 'I', 'M', 'D', 'X')),
    column_span_property: $ => seq(
      'ColumnSpan',
      '=',
      field('value', $.integer),
      ';'
    ),
    compressed_property: $ => seq(
      'Compressed',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    closing_dates_property: $ => seq(
      'ClosingDates',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    char_allowed_property: $ => seq(
      'CharAllowed',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    caption_property: $ => seq(
      ci('Caption'),
      '=',
      field('value', $.string_literal),
      optional(seq(
        ',',
        choice(
          seq(ci('Locked'), '=', field('locked', $.boolean_literal)),
          seq(ci('Comment'), '=', field('comment', $.string_literal)),
          seq(ci('MaxLength'), '=', field('max_length', $.integer))
        )
      )),
      ';'
    ),
    caption_class_property: $ => seq(
      'CaptionClass',
      '=',
      field('value', choice($.string_literal, $.identifier)),
      ';'
    ),
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
      field('filter', $.filter_expression),
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

    filter_expression: $ => /[a-zA-Z0-9<>&|=\%'\s]+/,

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
    blank_zero_property: $ => seq(
      'BlankZero',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    blank_numbers_property: $ => seq(
      'BlankNumbers',
      '=',
      field('value', choice('DontBlank', 'BlankNeg', 'BlankNegAndZero', 'BlankZero', 'BlankZeroAndPos', 'BlankPos')),
      ';'
    ),
    auto_increment_property: $ => seq(
      'AutoIncrement',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    auto_format_type_property: $ => seq(
      'AutoFormatType',
      '=',
      field('value', choice('1', '2', '3', '10', '11')),
      ';'
    ),
    auto_format_expression_property: $ => seq(
      'AutoFormatExpression',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    assist_edit_property: $ => seq(
      'AssistEdit',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
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
      ci('action'),
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat(choice($.page_action_property, $.trigger)),
      '}'
    ),

    page_action_property: $ => choice(
      $.caption_property,
      $.caption_ml_property,
      $.enabled_property,
      $.image_property,
      $.promoted_property,
      $.promoted_category_property,
      $.promoted_is_big_property,
      $.promoted_only_property,
      $.scope_property,
      $.run_object_property,
      $.shortcut_key_property,
      $.tooltip_property,
      $.trigger_property,
      $.application_area_property,
      $.run_page_link_property,
      $.run_page_view_property,
      $.run_page_mode_property,
      $.visible_property
    ),

    run_object_property: $ => seq(
      ci('RunObject'),
      '=',
      field('value', $.run_object_value),
      ';'
    ),

    run_object_value: $ => seq(
      field('object_type', choice(ci('page'), ci('report'), ci('codeunit'), ci('query'))),
      field('object_id', choice($.integer, $.identifier, $.string_literal))
    ),

    run_page_link_property: $ => seq(
      'RunPageLink',
      '=',
      field('value', $.run_page_link_value),
      ';'
    ),

    run_page_view_property: $ => seq(
      'RunPageView',
      '=',
      field('value', $.run_page_view_value),
      ';'
    ),

    run_page_mode_property: $ => seq(
      'RunPageMode',
      '=',
      field('value', choice('View', 'Edit', 'Create')),
      ';'
    ),

    run_page_link_value: $ => seq(
      repeat1(seq(
        field('field', $.identifier),
        '=',
        choice(
          seq('CONST', '(', $._value, ')'),
          seq('FILTER', '(', $.string_literal, ')'),
          seq('FIELD', '(', $.identifier, ')'),
          seq('FIELD', '(', 'UPPERLIMIT', '(', $.identifier, ')', ')'),
          seq('FIELD', '(', 'FILTER', '(', $.identifier, ')', ')'),
          seq('FIELD', '(', 'UPPERLIMIT', '(', 'FILTER', '(', $.identifier, ')', ')', ')')
        ),
        optional(',')
      ))
    ),

    run_page_view_value: $ => choice(
      seq(
        ci('sorting'),
        '(',
        $.identifier_or_string_list,
        ')',
        optional(seq(
          ci('order'),
          '(',
          choice('Ascending', 'Descending'),
          ')'
        )),
        optional(seq(
          ci('where'),
          '(',
          $.table_filters,
          ')'
        ))
      ),
      seq(
        ci('order'),
        '(',
        choice('Ascending', 'Descending'),
        ')'
      ),
      seq(
        ci('where'),
        '(',
        $.table_filters,
        ')'
      )
    ),

    identifier_or_string: $ => choice($.fully_qualified_identifier, $.string_literal),

    identifier_or_string_list: $ => seq(
      $.identifier_or_string,
      repeat(seq(',', $.identifier_or_string))
    ),
    image_property: $ => seq(
      ci('Image'),
      '=',
      field('value', choice($.string_literal, $.identifier)),
      ';'
    ),
    tooltip_property: $ => seq(
      'Tooltip',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    lookup_page_id_property: $ => seq(
      'LookupPageId',
      '=',
      field('value', $.identifier),
      ';'
    ),

    visible_property: $ => prec(5, makeSimpleProperty($, 'Visible', $ => choice($.boolean_literal, $.identifier, $._expression))),
    trigger_property: $ => seq(
      'Trigger',
      '=',
      field('value', $.identifier),
      ';'
    ),
    source_table_property: $ => prec(1, seq(
      'SourceTable',
      '=',
      field('value', $.identifier),
      ';'
    )),
    table_relation_property: $ => seq(
      'TableRelation',
      '=',
      field('value', $.table_relation_value),
      ';'
    ),

    table_relation_value: $ => choice(
      $.simple_table_relation,
      $.conditional_table_relation,
      $.string
    ),

    simple_table_relation: $ => seq(
      $.table_relation_target,
      optional($.where_clause)
    ),

    conditional_table_relation: $ => seq(
      'IF',
      '(',
      $.conditions,
      ')',
      $.table_relation_target,
      optional($.where_clause),
      optional(seq(
        'ELSE',
        $.table_relation
      ))
    ),

    conditions: $ => seq(
      $.condition,
      repeat(seq(
        choice('&', '|'),
        $.condition
      ))
    ),

    condition: $ => seq(
      field('field', $.string),
      '=',
      field('value', choice(
        $.const_filter,
        $.filter_filter,
        $.field_filter,
        $.upperlimit_field_filter,
        $.upperlimit_filter_field_filter
      ))
    ),

    table_relation_target: $ => seq(
      field('table', $.identifier),
      optional(seq(
        '.',
        field('field', $.identifier)
      ))
    ),

    table_relation: $ => choice(
      $.simple_table_relation,
      $.conditional_table_relation
    ),

    const_filter: $ => seq(
      'CONST',
      '(',
      field('value', optional($.identifier)),
      ')'
    ),
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
    width_property: $ => seq(
      'Width',
      '=',
      field('value', $.integer),
      ';'
    ),
    shared_layout_property: $ => seq(
      'SharedLayout',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    shortcut_key_property: $ => seq(
      'ShortcutKey',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    show_caption_property: $ => seq(
      'ShowCaption',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    show_mandatory_property: $ => makeSimpleProperty($, 'ShowMandatory', $ => choice($.boolean_literal, $.identifier, $._expression)),
    show_as_tree_property: $ => seq(
      'ShowAsTree',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    scope_property: $ => seq(
      'Scope',
      '=',
      field('value', choice('Page', 'Group', 'Repeater')),
      ';'
    ),
    save_values_property: $ => seq(
      'SaveValues',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    refresh_on_activate_property: $ => seq(
      'RefreshOnActivate',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    run_object_value: $ => seq(
      field('object_type', choice(
        ci('Page'),
        ci('Report'),
        ci('Codeunit'),
        ci('Query')
      )),
      field('object_id', choice($.identifier, $.string_literal))
    ),
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
        field('link', choice(
          seq(ci('FIELD'), '(', $.identifier, ')'),
          $._expression
        )),
        optional(',')
      )
    ),
    run_page_mode_property: $ => seq(
      'RunPageMode',
      '=',
      field('value', choice('View', 'Edit', 'Create')),
      ';'
    ),
    run_page_on_rec_property: $ => seq(
      'RunPageOnRec',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    run_page_view_property: $ => seq(
      'RunPageView',
      '=',
      field('value', $.run_page_view_value),
      ';'
    ),

    query_category_property: $ => seq(
      'QueryCategory',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    provider_property: $ => seq(
      'Provider',
      '=',
      field('value', $.identifier),
      ';'
    ),
    about_title_ml_property: $ => seq(
      'AboutTitleML',
      '=',
      field('value', $.multilanguage_string_literal),
      ';'
    ),
    prompt_mode_property: $ => seq(
      'PromptMode',
      '=',
      field('value', choice('Prompt', 'Generate', 'Content')),
      ';'
    ),
    promoted_only_property: $ => seq(
      'PromotedOnly',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
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
    promoted_action_categories_ml_property: $ => seq(
      'PromotedActionCategoriesML',
      '=',
      field('value', $.multilanguage_string_literal),
      ';'
    ),
    preserve_whitespace_property: $ => seq(
      'PreserveWhiteSpace',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    promoted_property: $ => seq(
      'Promoted',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    promoted_is_big_property: $ => seq(
      'PromotedIsBig',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    populate_all_fields_property: $ => seq(
      'PopulateAllFields',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    links_allowed_property: $ => seq(
      'LinksAllowed',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    lookup_property: $ => seq(
      'Lookup',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    modify_allowed_property: $ => seq(
      'ModifyAllowed',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    multiline_property: $ => seq(
      'MultiLine',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    multiple_new_lines_property: $ => seq(
      'MultipleNewLines',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    is_preview_property: $ => seq(
      'IsPreview',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    importance_property: $ => seq(
      'Importance',
      '=',
      field('value', choice('Standard', 'Promoted', 'Additional')),
      ';'
    ),
    indentation_column_property: $ => seq(
      'IndentationColumn',
      '=',
      field('value', $.identifier),
      ';'
    ),
    insert_allowed_property: $ => seq(
      'InsertAllowed',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
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
    is_header_property: $ => seq(
      'IsHeader',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    images_property: $ => seq(
      'Images',
      '=',
      field('value', $.array_value),
      ';'
    ),
    vertical_shrink_property: $ => seq(
      'VerticalShrink',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    horizontal_shrink_property: $ => seq(
      'HorizontalShrink',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    drilldown_page_id_property: $ => seq(
      'DrillDownPageId',
      '=',
      field('value', $.identifier),
      ';'
    ),
    drilldown_property: $ => seq(
      'DrillDown',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    editable_property: $ => prec(2, makeSimpleProperty($, 'Editable', $ =>
      choice($.boolean_literal, $.identifier, $._expression)
    )),
    data_caption_expression_property: $ => prec(1, seq(
      'DataCaptionExpression',
      '=',
      field('value', choice($.string_literal, $._expression)),
      ';'
    )),
    custom_action_type_property: $ => seq(
      'CustomActionType',
      '=',
      field('value', choice('Flow', 'FlowTemplate', 'FlowTemplateGallery')),
      ';'
    ),
    context_sensitive_help_page_property: $ => seq(
      'ContextSensitiveHelpPage',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    cuegroup_layout_property: $ => seq(
      'CuegroupLayout',
      '=',
      field('value', choice('Wide')),
      ';'
    ),
    change_tracking_allowed_property: $ => seq(
      'ChangeTrackingAllowed',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    card_page_id_property: $ => seq(
      'CardPageId',
      '=',
      field('value', $.identifier),
      ';'
    ),
    auto_split_key_property: $ => seq(
      'AutoSplitKey',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    apiversion_property: $ => seq(
      'APIVersion',
      '=',
      field('value', $.string_literal),
      optional(seq(',', $.string_literal)),
      ';'
    ),
    apipublisher_property: $ => seq(
      'APIPublisher',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    apigroup_property: $ => seq(
      'APIGroup',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    analysis_mode_enabled_property: $ => seq(
      'AnalysisModeEnabled',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    allowed_file_extensions_property: $ => seq(
      'AllowedFileExtensions',
      '=',
      field('value', $.array_value),
      ';'
    ),
    allow_multiple_files_property: $ => seq(
      'AllowMultipleFiles',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    additional_search_terms_ml_property: $ => seq(
      'AdditionalSearchTermsML',
      '=',
      field('value', $.multilanguage_string_literal),
      ';'
    ),
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
    access_property: $ => seq(
      'Access',
      '=',
      field('value', choice('Public', 'Internal', 'Protected', 'Local')),
      ';'
    ),
    about_text_property: $ => seq(
      'AboutText',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    data_deletion_allowed_property: $ => seq(
      'DataDeletionAllowed',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    about_text_ml_property: $ => seq(
      'AboutTextML',
      '=',
      field('value', $.multilanguage_string_literal),
      ';'
    ),

    report_property: $ => choice(
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
      )),
      '}'
    ),
    request_filter_heading_ml_property: $ => seq(
      'RequestFilterHeadingML',
      '=',
      field('value', $.multilanguage_string_literal),
      ';'
    ),
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
    rdlc_layout_property: $ => seq(
      'RDLCLayout',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    request_page_property: $ => seq(
      'RequestPage',
      '=',
      field('value', $.identifier),
      ';'
    ),
    processing_only_property: $ => seq(
      'ProcessingOnly',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    print_only_if_detail_property: $ => seq(
      'PrintOnlyIfDetail',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    preview_mode_property: $ => seq(
      'PreviewMode',
      '=',
      field('value', choice('Normal', 'PrintLayout')),
      ';'
    ),
    pdf_font_embedding_property: $ => seq(
      'PdfFontEmbedding',
      '=',
      field('value', choice('Default', 'Yes', 'No')),
      ';'
    ),
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
    max_iteration_property: $ => seq(
      'MaxIteration',
      '=',
      field('value', $.integer),
      ';'
    ),
    maximum_document_count_property: $ => seq(
      'MaximumDocumentCount',
      '=',
      field('value', $.integer),
      ';'
    ),
    maximum_dataset_size_property: $ => seq(
      'MaximumDatasetSize',
      '=',
      field('value', $.integer),
      ';'
    ),
    excel_layout_multiple_data_sheets_property: $ => seq(
      'ExcelLayoutMultipleDataSheets',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    execution_timeout_property: $ => seq(
      'ExecutionTimeout',
      '=',
      field('value', $.time_literal),
      ';'
    ),
    excel_layout_property: $ => seq(
      'ExcelLayout',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    enable_hyperlinks_property: $ => seq(
      'EnableHyperlinks',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    enable_external_images_property: $ => seq(
      'EnableExternalImages',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    enable_external_assemblies_property: $ => seq(
      'EnableExternalAssemblies',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    default_rendering_layout_property: $ => seq(
      'DefaultRenderingLayout',
      '=',
      field('value', $.identifier),
      ';'
    ),
    default_layout_property: $ => seq(
      'DefaultLayout',
      '=',
      field('value', choice('RDLC', 'Word', 'Excel')),
      ';'
    ),
    allow_scheduling_property: $ => seq(
      'AllowScheduling',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    xmlport_property: $ => choice(
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
      field('name', $.identifier),
      '{',
      repeat($._xmlport_element),
      '}'
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
    occurrence_property: $ => seq(
      'Occurrence',
      '=',
      field('value', choice('Required', 'Optional')),
      ';'
    ),
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
    namespace_prefix_property: $ => seq(
      'NamespacePrefix',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    min_occurs_property: $ => seq(
      'MinOccurs',
      '=',
      field('value', choice('Zero', 'Once')),
      ';'
    ),
    max_occurs_property: $ => seq(
      'MaxOccurs',
      '=',
      field('value', choice('Once', 'Unbounded')),
      ';'
    ),
    link_table_force_insert_property: $ => seq(
      'LinkTableForceInsert',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    link_table_property: $ => seq(
      'LinkTable',
      '=',
      field('value', $.identifier),
      ';'
    ),
    format_evaluate_property: $ => seq(
      'FormatEvaluate',
      '=',
      field('value', choice('Legacy', 'Xml')),
      ';'
    ),
    file_name_property: $ => seq(
      'FileName',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    field_validate_property: $ => seq(
      'FieldValidate',
      '=',
      field('value', choice('Yes', 'No', 'Undefined')),
      ';'
    ),
    field_delimiter_property: $ => seq(
      'FieldDelimiter',
      '=',
      field('value', choice($.string_literal, "'<None>'")),
      ';'
    ),
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
    encoding_property: $ => seq(
      'Encoding',
      '=',
      field('value', choice('UTF8', 'UTF16', 'ISO88592')),
      ';'
    ),
    direction_property: $ => seq(
      'Direction',
      '=',
      field('value', choice('Import', 'Export', 'Both')),
      ';'
    ),
    default_fields_validation_property: $ => seq(
      'DefaultFieldsValidation',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    auto_update_property: $ => seq(
      'AutoUpdate',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    auto_save_property: $ => seq(
      'AutoSave',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    auto_replace_property: $ => seq(
      'AutoReplace',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    query_property: $ => choice(
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
    test_isolation_property: $ => seq(
      'TestIsolation',
      '=',
      field('value', choice('Implicit', 'Explicit', 'None')),
      ';'
    ),
    test_permission_property: $ => seq(
      'TestPermissions',
      '=',
      field('value', choice('Disabled', 'Restrictive', 'NonRestrictive', 'InheritFromTestCodunit')),
      ';'
    ),
    single_instance_property: $ => seq(
      'SingleInstance',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    event_subscriber_instance_property: $ => seq(
      'EventSubscriberInstance',
      '=',
      field('value', choice('Manual', 'StaticAutomatic', 'PerSession')),  // Add 'PerSession' option
      ';'
    ),
    subtype_property: $ => seq(
      'Subtype',
      '=',
      field('value', choice('Install', 'Upgrade', 'Test')),
      ';'
    ),

    enum_property: $ => choice(
      $.access_property,
      $.assignment_compatibility_property,
      $.assignment_compatibility_reason_property,
      $.default_implementation_property,
      $.extensible_property
    ),
    extensible_property: $ => seq(
      'Extensible',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    default_implementation_property: $ => seq(
      'DefaultImplementation',
      '=',
      field('interface', $.identifier),
      '=',
      field('implementation', $.identifier),
      ';'
    ),
    assignment_compatibility_property: $ => seq(
      'AssignmentCompatibility',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    assignment_compatibility_reason_property: $ => seq(
      'AssignmentCompatibilityReason',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    enum_value_property: $ => choice(
      $.implementation_property
    ),
    implementation_property: $ => seq(
      'Implementation',
      '=',
      field('interface', $.identifier),
      '=',
      field('implementation', $.identifier),
      ';'
    ),

    permission_set_property: $ => choice(
      $.access_property
    ),

    query_property: $ => choice(
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
    reverse_sign_property: $ => seq(
      'ReverseSign',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    read_state_property: $ => seq(
      'ReadState',
      '=',
      field('value', choice('ReadUncommitted', 'ReadShared', 'ReadExclusive')),
      ';'
    ),
    query_type_property: $ => seq(
      'QueryType',
      '=',
      field('value', choice('Normal', 'API')),
      ';'
    ),
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
    method_property: $ => seq(
      'Method',
      '=',
      field('value', choice('Day', 'Month', 'Year', 'Sum', 'Count', 'Average', 'Min', 'Max')),
      ';'
    ),
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
    column_filter_property: $ => seq(
      'ColumnFilter',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    apiversion_property: $ => seq(
      'APIVersion',
      '=',
      field('value', $.string_literal),
      optional(seq(',', $.string_literal)),
      ';'
    ),
    apipublisher_property: $ => seq(
      'APIPublisher',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    apigroup_property: $ => seq(
      'APIGroup',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    interface_property: $ => choice(
      $.access_property
    ),

    permission_set_property: $ => choice(
      $.assignable_property,
      $.excluded_permission_sets_property,
      $.included_permission_sets_property,
      $.permissions_property  // Added Permissions property
    ),
    included_permission_sets_property: $ => seq(
      'IncludedPermissionSets',
      '=',
      field('value', $.identifier_list),
      ';'
    ),
    excluded_permission_sets_property: $ => seq(
      'ExcludedPermissionSets',
      '=',
      field('value', $.identifier_list),
      ';'
    ),
    assignable_property: $ => seq(
      'Assignable',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    auto_calc_field_property: $ => seq(
      'AutoCalcField',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    profile_property: $ => choice(
      $.customizations_property,
      $.enabled_property,
      $.profile_description_property,  // Added ProfileDescription property
      $.role_center_property  // Added RoleCenter property
    ),
    role_center_property: $ => seq(
      'RoleCenter',
      '=',
      field('value', $.identifier),
      ';'
    ),
    profile_description_property: $ => seq(
      'ProfileDescription',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    customizations_property: $ => seq(
      'Customizations',
      '=',
      field('value', $.identifier_list),
      ';'
    ),

    page_customization_property: $ => choice(
      $.about_text_property,
      $.about_text_ml_property,
      $.about_title_property,
      $.about_title_ml_property
    ),

    page_extension_property: $ => choice(
      $.about_text_property,
      $.about_text_ml_property,
      $.about_title_property
    ),

    table_extension_property: $ => choice(
    ),

    report_extension_property: $ => choice(
      $.excel_layout_property
    ),

    query_extension_property: $ => choice(
    ),

    enum_extension_property: $ => choice(
    ),

    control_addin_property: $ => choice(
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
    scripts_property: $ => seq(
      'Scripts',
      '=',
      field('value', $.array_value),
      ';'
    ),
    requested_width_property: $ => seq(
      'RequestedWidth',
      '=',
      field('value', $.integer),
      ';'
    ),
    requested_height_property: $ => seq(
      'RequestedHeight',
      '=',
      field('value', $.integer),
      ';'
    ),
    refresh_script_property: $ => seq(
      'RefreshScript',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    minimum_width_property: $ => seq(
      'MinimumWidth',
      '=',
      field('value', $.integer),
      ';'
    ),
    minimum_height_property: $ => seq(
      'MinimumHeight',
      '=',
      field('value', $.integer),
      ';'
    ),
    maximum_height_property: $ => seq(
      'MaximumHeight',
      '=',
      field('value', $.integer),
      ';'
    ),
    maximum_width_property: $ => seq(
      'MaximumWidth',
      '=',
      field('value', $.integer),
      ';'
    ),
    vertical_stretch_property: $ => seq(
      'VerticalStretch',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    horizontal_stretch_property: $ => seq(
      'HorizontalStretch',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    option_caption_property: $ => seq(
      'OptionCaption',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    init_value_property: $ => seq(
      'InitValue',
      '=',
      field('value', $._value),
      ';'
    ),
    max_value_property: $ => seq(
      'MaxValue',
      '=',
      field('value', $._value),
      ';'
    ),
    data_caption_fields_property: $ => seq(
      'DataCaptionFields',
      '=',
      field('value', $.identifier_list),
      ';'
    ),
    data_access_intent_property: $ => seq(
      'DataAccessIntent',
      '=',
      field('value', choice('ReadOnly', 'ReadWrite')),
      ';'
    ),
    table_data_classification_property: $ => prec(2, seq(
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
    )),

    field_data_classification_property: $ => prec(1, seq(
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
    )),
    delayed_insert_property: $ => seq(
      'DelayedInsert',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    delete_allowed_property: $ => seq(
      'DeleteAllowed',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    description_property: $ => seq(
      'Description',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    date_formula_property: $ => seq(
      'DateFormula',
      '=',
      field('value', $.string_literal),
      ';'
    ),
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
    ellipsis_property: $ => seq(
      'Ellipsis',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    entity_caption_property: $ => seq(
      'EntityCaption',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    entity_caption_ml_property: $ => seq(
      'EntityCaptionML',
      '=',
      field('value', $.multilanguage_string_literal),
      ';'
    ),
    entity_name_property: $ => seq(
      'EntityName',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    entity_set_caption_property: $ => seq(
      'EntitySetCaption',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    entity_set_caption_ml_property: $ => seq(
      'EntitySetCaptionML',
      '=',
      field('value', $.multilanguage_string_literal),
      ';'
    ),
    entity_set_name_property: $ => seq(
      'EntitySetName',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    file_upload_row_action_property: $ => seq(
      'FileUploadRowAction',
      '=',
      field('value', $.identifier),
      ';'
    ),
    flow_caption_property: $ => seq(
      'FlowCaption',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    flow_id_property: $ => seq(
      'FlowId',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    flow_template_category_name_property: $ => seq(
      'FlowTemplateCategoryName',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    flow_template_id_property: $ => seq(
      'FlowTemplateId',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    freeze_column_property: $ => seq(
      'FreezeColumn',
      '=',
      field('value', $.identifier),
      ';'
    ),
    gesture_property: $ => seq(
      'Gesture',
      '=',
      field('value', choice('None', 'LeftSwipe', 'RightSwipe', 'ContextMenu')),
      ';'
    ),
    grid_layout_property: $ => seq(
      'GridLayout',
      '=',
      field('value', choice('Rows', 'Columns')),
      ';'
    ),
    help_link_property: $ => seq(
      'HelpLink',
      '=',
      field('value', $.string_literal),
      ';'
    ),
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
    page_type_property: $ => seq(
      'PageType',
      '=',
      field('value', choice(
        $.string_literal,
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

    part_property: $ => choice(
      $.page_id_property,
      $.provider_property,
      $.editable_property,
      $.sub_page_link_property,
    ),

    sub_page_link_property: $ => seq(
      'SubPageLink',
      '=',
      field('value', $.sub_page_link_value),
      ';'
    ),

    sub_page_link_value: $ => seq(
      $.sub_page_link_mapping,
      repeat(seq(',', $.sub_page_link_mapping))
    ),

    sub_page_link_mapping: $ => seq(
      field('table_field', choice($.identifier, $.string_literal)),
      '=',
      'FIELD',
      '(',
      field('page_field', choice($.identifier, $.string_literal)),
      ')'
    ),

    system_part_property: $ => choice(
      $.system_part_id_property,
    ),

    page_id_property: $ => seq(
      'PagePartId',
      '=',
      field('value', $.identifier),
      ';'
    ),

    system_part_id_property: $ => seq(
      'SystemPartId',
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

    visible_property: $ => makeSimpleProperty($, 'Visible', $ => 
      choice($.boolean_literal, $.identifier, $._expression)
    ),
    format_region_property: $ => seq(
      'FormatRegion',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    flow_environment_id_property: $ => seq(
      'FlowEnvironmentId',
      '=',
      field('value', $.string_literal),
      ';'
    ),
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
    data_per_company_property: $ => seq(
      'DataPerCompany',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),

    entitlement_property: $ => choice(
      $.object_entitlements_property,
      $.role_type_property
    ),
    role_type_property: $ => seq(
      'RoleType',
      '=',
      field('value', choice('Local', 'Delegated')),
      ';'
    ),
    object_entitlements_property: $ => seq(
      'ObjectEntitlements',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    report_layout_property: $ => choice(
      $.mime_type_property
    ),
    mime_type_property: $ => seq(
      'MimeType',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    workflow_property: $ => choice(
    ),

    _value: $ => prec.right(3, choice(
      $._expression,
      $._literal,
      $.identifier,
      $.array_value,
      $.object_value
    )),

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

    string: $ => prec(2, choice(
      /"(?:[^"\\]|\\.)*"/,
      /'(?:[^'\\]|\\.)*'/
    )),
    integer: $ => /\d+/,
    identifier: $ => choice(
      prec(2,$._simple_identifier),
      $._quoted_identifier,
      $._numeric_identifier,
      $._compound_identifier
    ),
    _simple_identifier: $ => /[a-zA-Z_][a-zA-Z0-9_]*/,

    _quoted_identifier: $ => /"[^"]*(?:\.[^"]*)*"/,

    _numeric_identifier: $ => /\d+/,

    _compound_identifier: $ => prec.left(1, seq(
      choice($._quoted_identifier, $._simple_identifier),
      optional(repeat(seq('.', choice($._quoted_identifier, $._simple_identifier))))
    )),

    _enum_identifier: $ => seq(
      choice($._simple_identifier, $._quoted_identifier),
      '::',
      choice($._simple_identifier, $._quoted_identifier)
    ),

    enum_identifier: $ => prec.left(seq(
      field('enum_type', choice($.identifier, $._quoted_identifier)),
      $.double_colon,
      field('enum_value', choice($.identifier, $._quoted_identifier))
    )),

    fully_qualified_identifier: $ => seq(
      optional(seq($.qualified_namespace, '.')),
      $.identifier
    ),
    identifier_list: $ => seq(
      $.fully_qualified_identifier,
      repeat(seq(',', $.fully_qualified_identifier))
    ),
    _literal: $ => prec(4, choice(
      $.number_literal,
      $.string_literal,
      $.boolean_literal,
      $.date_literal,
      $.time_literal,
      $.datetime_literal
    )),

    number_literal: $ => choice(
      /\d+\.\d+/,
      prec(-1, /\d+/)
    ),

    string_literal: $ => choice(
      '""',
      "''",
      seq('"', /(?:[^"\\]|\\.)+/, '"'),
      seq("'", /(?:[^'\\]|\\.)+/, "'")
    ),

    boolean_literal: $ => choice(/[tT][rR][uU][eE]/, /[fF][aA][lL][sS][eE]/),

    Boolean: $ => 'Boolean',
    Action: $ => choice(
      'OK',
      'Cancel',
      'Yes',
      'No',
      'LookupOK',
      'LookupCancel'
    ),
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
    _operator: $ => choice(
      $.arithmetic_operator,
      $.comparison_operator,
      $.logical_operator,
      $.assignment_operator
    ),

    arithmetic_operator: $ => choice('+', '-', '*', '/', /[dD][iI][vV]/, /[mM][oO][dD]/),

    comparison_operator: $ => token(choice('=', '<>', '<=', '>=', '<', '>')),

    logical_operator: $ => choice(/[aA][nN][dD]/, /[oO][rR]/, /[nN][oO][tT]/, /[xX][oO][rR]/),

    assignment_operator: $ => ':=',
    public_key_token_property: $ => seq(
      'PublicKeyToken',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    recreate_script_property: $ => seq(
      'RecreateScript',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    request_filter_fields_property: $ => seq(
      'RequestFilterFields',
      '=',
      field('value', $.identifier_list),
      ';'
    ),
    source_table_temporary_property: $ => seq(
      'SourceTableTemporary',
      '=',
      field('value', $.boolean_literal),
      ';'
    ),
    source_table_view_property: $ => seq(
      'SourceTableView',
      '=',
      field('value', $.string_literal),
      ';'
    ),
  }
});
