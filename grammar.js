// AL (Application Language) grammar for tree-sitter
// This grammar defines the structure and syntax for AL, 
// the programming language used in Microsoft Dynamics 365 Business Central

module.exports = grammar({
  name: 'al',

  // Define what should be treated as extra (ignored) in the parsing process
  extras: $ => [
    $.comment,  // Comments are ignored during parsing
    /\s/        // Whitespace is ignored
  ],

  rules: {
    // The root node of the AST (Abstract Syntax Tree)
    // A source file in AL consists of one or more object definitions
    source_file: $ => repeat($._definition),

    // Definitions for various AL object types
    // This rule defines all the possible top-level objects in an AL file
    _definition: $ => choice(
      $.table,              // Table object definition
      $.tableextension,     // Table extension object definition
      $.page,               // Page object definition
      $.pageextension,      // Page extension object definition
      $.codeunit,           // Codeunit object definition
      $.report,             // Report object definition
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

// AL (Application Language) grammar for tree-sitter
// This grammar defines the structure and syntax for AL, 
// the programming language used in Microsoft Dynamics 365 Business Central

module.exports = grammar({
  name: 'al',

  // Define what should be treated as extra (ignored) in the parsing process
  extras: $ => [
    $.comment,  // Comments are ignored during parsing
    /\s/        // Whitespace is ignored
  ],

  rules: {
    // The root node of the AST (Abstract Syntax Tree)
    // A source file in AL consists of one or more object definitions
    source_file: $ => repeat($._definition),

    // Definitions for various AL object types
    // This rule defines all the possible top-level objects in an AL file
    _definition: $ => choice(
      $.table,              // Table object definition
      $.tableextension,     // Table extension object definition
      $.page,               // Page object definition
      $.pageextension,      // Page extension object definition
      $.codeunit,           // Codeunit object definition
      $.report,             // Report object definition
      $.query,              // Query object definition
      $.xmlport,            // XMLport object definition
      $.enum,               // Enum object definition
      $.dotnet,             // DotNet object definition
      $.controladdin,       // Control Add-in object definition
      $.profile,            // Profile object definition
      $.permissionset,      // Permission Set object definition
      $.permissionsetextension, // Permission Set Extension object definition
      $.entitlement         // Entitlement object definition
    ),

    // Table object definition
    // A table in AL represents a database table
    table: $ => seq(
      'table',
      field('table_id', $.integer),
      field('table_name', choice($.string, $.identifier)),
      optional($.extends_clause),
      '{',
      repeat($._table_element),
      '}'
    ),

    // Elements that can appear within a table definition
    // This includes fields, keys, fieldgroups, triggers, procedures, and various properties
    _table_element: $ => choice(
      $.fields,
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

    // Caption property definition
    caption_property: $ => seq(
      'Caption',
      '=',
      field('caption_value', $.string),
      ';'
    ),

    // LookupPageID property definition
    lookup_page_id_property: $ => seq(
      'LookupPageID',
      '=',
      field('page_id', choice($.integer, $.identifier)),
      ';'
    ),

    // DrillDownPageID property definition
    drill_down_page_id_property: $ => seq(
      'DrillDownPageID',
      '=',
      field('page_id', choice($.integer, $.identifier)),
      ';'
    ),

    // DataPerCompany property definition
    data_per_company_property: $ => seq(
      'DataPerCompany',
      '=',
      field('value', $.boolean),
      ';'
    ),

    // LookupPageID property definition (alternative syntax)
    lookup_page_property: $ => seq(
      'LookupPageID',
      '=',
      field('page_name', $.identifier),
      ';'
    ),

    // DrillDownPageID property definition (alternative syntax)
    drill_down_page_property: $ => seq(
      'DrillDownPageID',
      '=',
      field('page_name', $.identifier),
      ';'
    ),

    // Permissions property definition
    permissions_property: $ => seq(
      'Permissions',
      '=',
      field('permissions', $.identifier_list),
      ';'
    ),

    // Permission item definition
    permission_item: $ => seq(
      field('permission_type', $.identifier),
      '=',
      field('permission_value', $.identifier)
    ),

    // Access property definition
    access_property: $ => seq(
      'Access',
      '=',
      field('access_value', $.identifier),
      ';'
    ),

    // PasteIsValid property definition
    paste_is_valid_property: $ => seq(
      'PasteIsValid',
      '=',
      field('value', $.boolean),
      ';'
    ),

    // Extensible property definition
    extensible_property: $ => seq(
      'Extensible',
      '=',
      field('value', $.boolean),
      ';'
    ),

    // DataClassification property definition
    data_classification_property: $ => seq(
      'DataClassification',
      '=',
      field('classification', $.identifier),
      ';'
    ),

    // DataCaptionFields property definition
    data_caption_fields_property: $ => seq(
      'DataCaptionFields',
      '=',
      field('fields', $.identifier_list),
      ';'
    ),

    // ObsoleteState property definition
    obsolete_state_property: $ => seq(
      'ObsoleteState',
      '=',
      field('state', $.identifier),
      ';'
    ),

    // LookupPageID property definition (string version)
    lookup_page_id: $ => seq(
      'LookupPageID',
      '=',
      field('page_name', $.string),
      ';'
    ),

    // DrillDownPageID property definition (string version)
    drill_down_page_id: $ => seq(
      'DrillDownPageID',
      '=',
      field('page_name', $.string),
      ';'
    ),

    // Caption property definition (alternative syntax)
    caption: $ => seq(
      'Caption',
      '=',
      field('caption_value', $.string),
      ';'
    ),

    // Table property definition
    table_property: $ => prec(12, seq(
      field('property_name', $.identifier),
      '=',
      field('property_value', choice($.literal, $.identifier, $.property_option, $.boolean, $.property_list, $.page_reference)),
      optional(';')
    )),

    // Page reference definition
    page_reference: $ => seq(
      'Page',
      '::',
      field('page_name', $.identifier)
    ),

    // Generic property definition
    property: $ => prec(11, seq(
      field('property_name', $.identifier),
      '=',
      field('property_value', choice($.literal, $.identifier, $.property_option, $.boolean, $.property_list, $.page_reference)),
      optional(';')
    )),

    // Fields block definition
    fields: $ => seq(
      'fields',
      '{',
      repeat($.field),
      '}'
    ),

    // Keys block definition
    keys_block: $ => seq(
      'keys',
      '{',
      repeat($.key),
      '}'
    ),

    // Fieldgroups block definition
    fieldgroups_block: $ => seq(
      'fieldgroups',
      '{',
      repeat($.fieldgroup),
      '}'
    ),

    // Fieldgroup definition
    fieldgroup: $ => seq(
      field('fieldgroup_name', $.identifier),
      '{',
      field('fields', $.identifier_list),
      '}'
    ),

    // Property option definition
    property_option: $ => prec.left(8, seq(
      field('option_name', $.identifier),
      optional(seq(':', field('option_value', choice($.literal, $.boolean, $.identifier))))
    )),

    // Property list definition
    property_list: $ => seq(
      '[',
      repeat(seq($.property_option, optional(','))),
      ']'
    ),

    // Field definition within a table
    // Each field represents a column in the database table
    field: $ => seq(
      'field',
      '(',
      field('field_id', $.integer),  // Unique identifier for the field
      ';',
      field('field_name', $.string), // Name of the field
      ')',
      field('data_type', $.data_type), // Data type of the field
      '{',
      repeat($.field_property),  // Field properties
      '}'
    ),

    // Properties that can be applied to a field
    // This includes various attributes and behaviors that can be set for a field
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
      $.validate_table_relation_property,
      $.assist_edit_property,
      $.auto_format_type_property,
      $.auto_format_expression_property,
      $.auto_format_preserve_property,
      $.blob_type_property,
      $.access_property,
      $.advanced_property,
      $.application_area_property,
      $.auto_format_property,
      $.automatic_caption_property
    ),

    // Access property definition for fields
    access_property: $ => seq(
      'Access',
      '=',
      field('value', $.identifier),
      ';'
    ),

    // Advanced property definition
    advanced_property: $ => seq(
      'Advanced',
      '=',
      field('value', $.boolean),
      ';'
    ),

    // ApplicationArea property definition
    application_area_property: $ => seq(
      'ApplicationArea',
      '=',
      field('value', $.identifier_list),
      ';'
    ),

    // AutoFormat property definition
    auto_format_property: $ => seq(
      'AutoFormat',
      '=',
      field('value', $.identifier),
      ';'
    ),

    // AutomaticCaption property definition
    automatic_caption_property: $ => seq(
      'AutomaticCaption',
      '=',
      field('value', $.boolean),
      ';'
    ),

    // AssistEdit property definition
    assist_edit_property: $ => seq(
      'AssistEdit',
      '=',
      field('value', $.boolean),
      ';'
    ),

    // AutoFormatType property definition
    auto_format_type_property: $ => seq(
      'AutoFormatType',
      '=',
      field('value', $.identifier),
      ';'
    ),

    // AutoFormatExpression property definition
    auto_format_expression_property: $ => seq(
      'AutoFormatExpression',
      '=',
      field('value', $.string),
      ';'
    ),

    // AutoFormatPreserveDecimals property definition
    auto_format_preserve_property: $ => seq(
      'AutoFormatPreserveDecimals',
      '=',
      field('value', $.boolean),
      ';'
    ),

    // Blob property definition
    blob_type_property: $ => seq(
      'Blob',
      '=',
      field('value', $.identifier),
      ';'
    ),

    // OptionCaption property definition
    option_caption_property: $ => seq(
      'OptionCaption',
      '=',
      field('captions', $.string),
      ';'
    ),

    // OptionString property definition
    option_string_property: $ => seq(
      'OptionString',
      '=',
      field('option_string', $.string),
      ';'
    ),

    // TableRelation property definition
    table_relation_property: $ => prec(2, seq(
      'TableRelation',
      '=',
      field('table_name', choice($.identifier, $.table_relation_expression)),
      ';'
    )),

    // TableRelation expression definition
    table_relation_expression: $ => seq(
      field('table_name', $.identifier),
      optional(seq('.', field('field_name', $.identifier))),
      optional(seq(
        'WHERE',
        '(',
        seq(
          seq(
            field('field_name', $.identifier),
            '=',
            field('field_value', choice($.identifier, $.literal, $.field_reference))
          ),
          repeat(seq(
            ',',
            field('field_name', $.identifier),
            '=',
            field('field_value', choice($.identifier, $.literal, $.field_reference))
          ))
        ),
        ')'
      ))
    ),

    // Field reference definition
    field_reference: $ => seq(
      'FIELD',
      '(',
      field('field_name', $.identifier),
      ')'
    ),

    // Width property definition
    width_property: $ => seq(
      'Width',
      '=',
      field('width', $.integer),
      ';'
    ),

    // Editable property definition
    editable_property: $ => seq(
      'Editable',
      '=',
      field('editable', $.boolean),
      ';'
    ),

    // NotifyOnValidate property definition
    notify_on_validate_property: $ => seq(
      'NotifyOnValidate',
      '=',
      field('notify', $.boolean),
      ';'
    ),

    // ValidateOnValidate property definition
    validate_on_validate_property: $ => seq(
      'ValidateOnValidate',
      '=',
      field('validate', $.boolean),
      ';'
    ),

    // InitValue property definition
    init_value_property: $ => seq(
      'InitValue',
      '=',
      field('init_value', choice($.literal, $.identifier)),
      ';'
    ),

    // TestTableRelation property definition
    test_table_relation_property: $ => seq(
      'TestTableRelation',
      '=',
      field('test', $.boolean),
      ';'
    ),

    // ValidateTableRelation property definition
    validate_table_relation_property: $ => prec(2, seq(
      'ValidateTableRelation',
      '=',
      field('validate', $.boolean),
      ';'
    )),

    // SubType property definition for BLOB fields
    blob_sub_type_property: $ => seq(
      'SubType',
      '=',
      field('sub_type', $.identifier),
      ';'
    ),

    // FieldClass property definition
    field_class_property: $ => seq(
      'FieldClass',
      '=',
      field('field_class', $.identifier),
      ';'
    ),

    // AutoIncrement property definition
    auto_increment_property: $ => seq(
      'AutoIncrement',
      '=',
      field('auto_increment', $.boolean),
      ';'
    ),

    // Validate property definition
    validate_property: $ => seq(
      'ValidateTableRelation',
      '=',
      field('validate', $.boolean),
      ';'
    ),

    // Description property definition
    description_property: $ => seq(
      'Description',
      '=',
      field('description', $.string),
      ';'
    ),

    // OptionCaption property definition (alternative syntax)
    option_caption: $ => seq(
      'OptionCaption',
      '=',
      field('captions', $.string),
      ';'
    ),

    // OptionString property definition (alternative syntax)
    option_string: $ => seq(
      'OptionString',
      '=',
      field('options', $.string),
      ';'
    ),

    // AccessByPermission property definition
    access_by_permission_property: $ => seq(
      'AccessByPermission',
      '=',
      field('permission', $.string),
      ';'
    ),

    // Enabled property definition
    enabled_property: $ => seq(
      'Enabled',
      '=',
      field('enabled', $.boolean),
      ';'
    ),

    // Visible property definition
    visible_property: $ => seq(
      'Visible',
      '=',
      field('visible', $.boolean),
      ';'
    ),

    // TableRelation property definition (alternative syntax)
    table_relation: $ => seq(
      'TableRelation',
      '=',
      field('table_name', $.string),
      ';'
    ),

    // DataClassification property definition (alternative syntax)
    data_classification: $ => seq(
      'DataClassification',
      '=',
      field('classification', $.identifier),
      ';'
    ),

    // Layout definition for pages
    layout: $ => seq(
      'layout',
      '{',
      repeat($.layout_element),
      '}'
    ),

    // Layout element definition
    layout_element: $ => choice(
      $.area,
      $.group,
      $.field,
      $.part,
      $.systempart,
      $.chartpart
    ),

    // Part definition in page layout
    part: $ => seq(
      'part',
      '(',
      field('part_name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    // SystemPart definition in page layout
    systempart: $ => seq(
      'systempart',
      '(',
      field('systempart_name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    // ChartPart definition in page layout
    chartpart: $ => seq(
      'chartpart',
      '(',
      field('chartpart_name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    // Group definition in page layout
    group: $ => seq(
      'group',
      '(',
      field('group_name', $.identifier),
      ')',
      '{',
      repeat($.layout_element),
      '}'
    ),

    // Area definition in page layout
    area: $ => seq(
      'area',
      '(',
      field('area_name', $.identifier),
      ')',
      '{',
      repeat($.layout_element),
      '}'
    ),

    // Key definition in table
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

    // Fieldgroup definition
    fieldgroup: $ => seq(
      'fieldgroup',
      '(',
      field('fieldgroup_name', $.identifier),
      ')',
      '{',
      field('fields', $.identifier_list),
      '}'
    ),

    // TableExtension object definition
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

    // Page object definition
    page: $ => seq(
      'page',
      field('page_id', $.integer),
      field('page_name', $.identifier),
      '{',
      repeat($._page_body_element),
      '}'
    ),

    // PageExtension object definition
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

    // Codeunit object definition
    codeunit: $ => seq(
      'codeunit',
      field('codeunit_id', $.integer),
      field('codeunit_name', $.identifier),
      optional($.implements_clause),
      '{',
      repeat($._codeunit_body_element),
      '}'
    ),

    // Report object definition
    report: $ => seq(
      'report',
      field('report_id', $.integer),
      field('report_name', $.identifier),
      '{',
      repeat($._report_body_element),
      '}'
    ),

    // Query object definition
    query: $ => seq(
      'query',
      field('query_id', $.integer),
      field('query_name', $.identifier),
      '{',
      repeat($._query_body_element),
      '}'
    ),

    // XMLport object definition
    xmlport: $ => seq(
      'xmlport',
      field('xmlport_id', $.integer),
      field('xmlport_name', $.identifier),
      '{',
      repeat($._xmlport_body_element),
      '}'
    ),

    // Enum object definition
    enum: $ => seq(
      'enum',
      field('enum_id', $.integer),
      field('enum_name', $.identifier),
      optional($.implements_clause),
      '{',
      repeat($.enum_value),
      '}'
    ),

    // DotNet object definition
    dotnet: $ => seq(
      'dotnet',
      field('dotnet_name', $.identifier),
      '{',
      repeat($.assembly),
      '}'
    ),

    // Control Add-in object definition
    controladdin: $ => seq(
      'controladdin',
      field('controladdin_name', $.identifier),
      '{',
      repeat($._controladdin_body_element),
      '}'
    ),

    // Profile object definition
    profile: $ => seq(
      'profile',
      field('profile_name', $.identifier),
      '{',
      repeat($.profile_element),
      '}'
    ),

    // Permission Set object definition
    permissionset: $ => seq(
      'permissionset',
      field('permissionset_id', $.integer),
      field('permissionset_name', $.identifier),
      '{',
      repeat($.permission),
      '}'
    ),

    // Permission Set Extension object definition
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

    // Entitlement object definition
    entitlement: $ => seq(
      'entitlement',
      field('entitlement_name', $.identifier),
      '{',
      repeat($.entitlement_element),
      '}'
    ),

    // Common Elements

    // Elements that can appear within a table body
    _table_body_element: $ => choice(
      $.field,
      $.key,
      $.fieldgroup,
      $.trigger,
      $.procedure,
      $.property,
      $.var_section
    ),

    // Elements that can appear within a page body
    _page_body_element: $ => choice(
      $.layout,
      $.actions,
      $.trigger,
      $.procedure,
      $.property,
      $.var_section
    ),

    // Elements that can appear within a codeunit body
    _codeunit_body_element: $ => choice(
      $.trigger,
      $.procedure,
      $.property,
      $.var_section
    ),

    // Elements that can appear within a report body
    _report_body_element: $ => choice(
      $.dataset,
      $.requestpage,
      $.trigger,
      $.procedure,
      $.property,
      $.var_section
    ),

    // Elements that can appear within a query body
    _query_body_element: $ => choice(
      $.elements,
      $.filter,
      $.column,
      $.trigger,
      $.property
    ),

    // Elements that can appear within an XMLport body
    _xmlport_body_element: $ => choice(
      $.schema,
      $.requestpage,
      $.trigger,
      $.procedure,
      $.property,
      $.var_section
    ),

    // Elements that can appear within a control add-in body
    _controladdin_body_element: $ => choice(
      $.property,
      $.event,
      $.procedure
    ),

    // Trigger definition
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

    // Procedure definition
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

    // Variable section definition
    var_section: $ => prec.right(seq(
      'var',
      repeat1($.var_declaration),
      optional(';')
    )),

    // Procedure attribute definition
    procedure_attribute: $ => seq(
      '[',
      choice('IntegrationEvent', 'BusinessEvent', 'InternalEvent'),
      ']'
    ),

    // Variable declaration
    var_declaration: $ => seq(
      field('var_name', $.identifier),
      ':',
      field('var_type', $.data_type),
      optional(seq('temporary')),
      ';'
    ),

    // Actions block definition for pages
    actions: $ => seq(
      'actions',
      '{',
      repeat($.action),
      '}'
    ),

    // Action definition
    action: $ => seq(
      'action',
      '(',
      field('action_name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    // Dataset definition for reports
    dataset: $ => seq(
      'dataset',
      '{',
      repeat($.dataitem),
      '}'
    ),

    // Dataitem definition
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

    // Request page definition
    requestpage: $ => seq(
      'requestpage',
      '{',
      repeat($.requestpage_element),
      '}'
    ),

    // Request page element definition
    requestpage_element: $ => choice(
      $.layout,
      $.actions,
      $.trigger,
      $.property
    ),

    // Elements block definition for queries
    elements: $ => seq(
      'elements',
      '{',
      repeat($.query_element),
      '}'
    ),

    // Query element definition
    query_element: $ => choice(
      $.dataitem,
      $.column,
      $.filter
    ),

    // Filter block definition
    filter: $ => seq(
      'filter',
      '{',
      repeat($.filter_element),
      '}'
    ),

    // Filter element definition
    filter_element: $ => seq(
      field('field', $.identifier),
      '=',
      field('value', $.expression),
      ';'
    ),

    // Column definition
    column: $ => seq(
      'column',
      '(',
      field('column_name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    // Schema definition for XMLports
    schema: $ => seq(
      'schema',
      '{',
      repeat($.schema_element),
      '}'
    ),

    // Schema element definition
    schema_element: $ => choice(
      $.textelement,
      $.fieldelement,
      $.tableelement
    ),

    // Text element definition
    textelement: $ => seq(
      'textelement',
      '(',
      field('element_name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    // Field element definition
    fieldelement: $ => seq(
      'fieldelement',
      '(',
      field('element_name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    // Table element definition
    tableelement: $ => seq(
      'tableelement',
      '(',
      field('element_name', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    // Event definition
    event: $ => seq(
      'event',
      field('event_name', $.identifier),
      '(',
      optional($.parameter_list),
      ')',
      ';'
    ),

    // Enum value definition
    enum_value: $ => seq(
      field('value_name', $.identifier),
      optional(seq('=', field('value', $.integer))),
      ';'
    ),

    // Assembly definition for DotNet objects
    assembly: $ => seq(
      'assembly',
      '(',
      field('assembly_name', $.string),
      ')',
      ';'
    ),

    // Extends clause definition
    extends_clause: $ => seq(
      'extends',
      field('base_object', $.identifier)
    ),

    // Implements clause definition
    implements_clause: $ => seq(
      'implements',
      $.identifier,
      repeat(seq(',', $.identifier))
    ),

    // Profile element definition
    profile_element: $ => choice(
      $.profile_customization,
      $.profile_apparea
    ),

    // Profile customization definition
    profile_customization: $ => seq(
      'customizations',
      '=',
      $.string,
      ';'
    ),

    // Profile app area definition
    profile_apparea: $ => seq(
      'area',
      '(',
      field('area_name', $.identifier),
      ')',
      '{',
      repeat($.profile_apparea_element),
      '}'
    ),

    // Profile app area element definition
    profile_apparea_element: $ => choice(
      $.profile_rolecenters,
      $.profile_sections
    ),

    // Profile role centers definition
    profile_rolecenters: $ => seq(
      'rolecenters',
      '=',
      '[',
      $.integer,
      repeat(seq(',', $.integer)),
      ']',
      ';'
    ),

    // Profile sections definition
    profile_sections: $ => seq(
      'sections',
      '=',
      '[',
      $.string,
      repeat(seq(',', $.string)),
      ']',
      ';'
    ),

    // Permission definition
    permission: $ => seq(
      field('object_type', $.identifier),
      field('object_name', $.string),
      '=',
      field('permission_type', $.identifier),
      ';'
    ),

    // Entitlement element definition
    entitlement_element: $ => choice(
      $.entitlement_object_entitlements,
      $.entitlement_custom_entitlements
    ),

    // Entitlement object entitlements definition
    entitlement_object_entitlements: $ => seq(
      'ObjectEntitlements',
      '=',
      '[',
      $.entitlement_object,
      repeat(seq(',', $.entitlement_object)),
      ']',
      ';'
    ),

    // Entitlement object definition
    entitlement_object: $ => seq(
      'ObjectType',
      '=',
      field('object_type', $.identifier),
      ',',
      'ObjectId',
      '=',
      field('object_id', $.string)
    ),

    // Entitlement custom entitlements definition
    entitlement_custom_entitlements: $ => seq(
      'CustomEntitlements',
      '=',
      '[',
      $.string,
      repeat(seq(',', $.string)),
      ']',
      ';'
    ),

    // Statements
    // This rule defines all the possible statements in AL
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

    // FindLast statement: finds the last record in a table
    findlast_statement: $ => prec(2, seq(
      'FindLast',
      '(',
      ')',
      ';'
    )),

    // SetFilter statement: sets a filter on a table
    setfilter_statement: $ => seq(
      'SetFilter',
      '(',
      field('field_name', $.identifier),
      ',',
      field('filter_expression', $.string),
      ')',
      ';'
    ),

    // Find statement: finds records in a table
    find_statement: $ => prec(1, seq(
      choice('FindFirst', 'FindLast', 'Find', 'FindSet'),
      '(',
      optional($.boolean),
      ')',
      ';'
    )),

    // Init statement: initializes a record
    init_statement: $ => seq(
      'Init',
      '(',
      ')',
      ';'
    ),

    // Modify statement: modifies a record
    modify_statement: $ => seq(
      'Modify',
      '(',
      optional($.boolean),
      ')',
      ';'
    ),

    // Insert statement: inserts a new record
    insert_statement: $ => seq(
      'Insert',
      '(',
      optional($.boolean),
      ')',
      ';'
    ),

    // CalcFields statement: calculates fields in a record
    calcfields_statement: $ => seq(
      'CALCFIELDS',
      '(',
      field('field_name', $.identifier),
      ')',
      ';'
    ),

    // Assignment statement: assigns a value to a variable
    assignment_statement: $ => seq(
      field('left_hand_side', $.identifier),
      ':=',
      field('right_hand_side', $.expression),
      ';'
    ),

    // If statement: conditional execution
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

    // Case statement: multi-way branch
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

    // Case option: individual branch in a case statement
    case_option: $ => seq(
      field('option', $.expression),
      ':',
      '{',
      repeat($.statement),
      '}'
    ),

    // For statement: loop with a counter
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

    // Foreach statement: loop over elements in a collection
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

    // While statement: loop with a condition
    while_statement: $ => seq(
      'while',
      field('condition', $.expression),
      'do',
      '{',
      repeat($.statement),
      '}'
    ),

    // Repeat statement: loop that executes at least once
    repeat_statement: $ => seq(
      'repeat',
      '{',
      repeat($.statement),
      '}',
      'until',
      field('condition', $.expression),
      ';'
    ),

    // Call statement: calls a function or procedure
    call_statement: $ => seq(
      field('function_name', $.identifier),
      '(',
      optional($.argument_list),
      ')',
      ';'
    ),

    // Exit statement: exits from a loop or procedure
    exit_statement: $ => seq(
      'exit',
      ';'
    ),

    // With statement: sets a default record for field access
    with_statement: $ => seq(
      'with',
      field('record', $.identifier),
      'do',
      '{',
      repeat($.statement),
      '}'
    ),

    // Return statement: returns from a function or procedure
    return_statement: $ => seq(
      'return',
      optional(field('value', $.expression)),
      ';'
    ),

    // Try-catch statement: handles exceptions
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
    // This rule defines all the possible expressions in AL
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

    // Binary expression: expression with two operands and an operator
    binary_expression: $ => prec.left(1, seq(
      field('left', $.expression),
      field('operator', $.binary_operator),
      field('right', $.expression)
    )),

    // Unary expression: expression with one operand and an operator
    unary_expression: $ => prec(2, seq(
      field('operator', $.unary_operator),
      field('operand', $.expression)
    )),

    // Parenthesized expression: expression enclosed in parentheses
    parenthesized_expression: $ => seq(
      '(',
      $.expression,
      ')'
    ),

    // Function call expression
    function_call: $ => seq(
      field('function_name', $.identifier),
      '(',
      optional($.argument_list),
      ')'
    ),

    // RecordRef expression: used to open a table
    record_ref_expression: $ => seq(
      'RecordRef',
      '.',
      'Open',
      '(',
      field('table_id', $.expression),
      ')'
    ),

    // FieldRef expression: used to access a field in a record
    field_ref_expression: $ => seq(
      field('record', $.identifier),
      '.',
      'Field',
      '(',
      field('field_id', $.expression),
      ')'
    ),

    // Operators
    // Binary operators: operators that work on two operands
    binary_operator: $ => choice(
      '+', '-', '*', '/', 'div', 'mod',  // Arithmetic operators
      '=', '<>', '<', '<=', '>', '>=',   // Comparison operators
      'and', 'or', 'xor', 'in'           // Logical operators
    ),

    // Unary operators: operators that work on one operand
    unary_operator: $ => choice(
      '-', 'not'
    ),

    // Literals: constant values in the code
    literal: $ => prec(7, choice(
      $.integer,
      $.decimal,
      $.string,
      $.boolean,
      $.date,
      $.time,
      $.datetime
    )),

    // Basic types and constructs
    identifier: $ => /[a-zA-Z_][a-zA-Z0-9_]*/,  // Identifiers: names of variables, functions, etc.
    identifier_list: $ => seq($.identifier, repeat(seq(',', $.identifier))),  // List of identifiers
    argument_list: $ => seq($.expression, repeat(seq(',', $.expression))),  // List of arguments in a function call
    parameter_list: $ => seq($.parameter, repeat(seq(',', $.parameter))),  // List of parameters in a function definition

    // Parameter in a function definition
    parameter: $ => seq(
      optional('var'),  // 'var' keyword for reference parameters
      field('parameter_name', $.identifier),
      ':',
      field('parameter_type', $.data_type)
    ),

    // Data types in AL
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

    // Basic literal types
    boolean: $ => choice('true', 'false'),
    integer: $ => /\d+/,
    decimal: $ => /\d+\.\d+/,
    string: $ => /'[^']*'/,
    date: $ => /\d{2}\.\d{2}\.\d{4}/,
    time: $ => /\d{2}:\d{2}:\d{2}/,
    datetime: $ => seq($.date, $.time),

    // Comments in AL
    comment: $ => token(choice(
      seq('//', /.*/),  // Single-line comment
      seq(
        '/*',
        /[^*]*\*+([^/*][^*]*\*+)*/,
        '/'
      )  // Multi-line comment
    ))
  }
});

