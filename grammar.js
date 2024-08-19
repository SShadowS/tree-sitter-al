// AL (Application Language) grammar for tree-sitter
// This grammar defines the structure and syntax for AL, 
// the programming language used in Microsoft Dynamics 365 Business Central

module.exports = grammar({
  name: 'al',

  extras: $ => [
    $.comment,
    $.xml_comment,
    /\s/
  ],

  rules: {
    source_file: $ => repeat($._definition),

    _definition: $ => choice(
      $.table_definition,
      $.page_definition,
      $.report_definition,
      $.codeunit_definition,
      $.query_definition,
      $.xmlport_definition,
      $.enum_definition,
      $.tableextension,
      $.pageextension,
      $.dotnet,
      $.controladdin,
      $.profile,
      $.permissionset,
      $.permissionsetextension,
      $.entitlement
    ),

    codeunit_definition: $ => seq(
      'codeunit',
      field('id', $.object_id),
      field('name', $.object_name),
      '{',
      repeat(choice(
        $.var_section,
        $._codeunit_element,
        $.trigger_definition
      )),
      '}'
    ),

    // Variable section definition
    // This section declares variables used within an object
    var_section: $ => prec.right(seq(
      'var',                        // Keyword indicating variable declarations
      repeat1($.variable_declaration) // One or more variable declarations
    )),

    // Variable declaration definition
    // Defines the structure of a single variable declaration
    variable_declaration: $ => seq(
      'var',                                    // Keyword indicating a variable declaration
      field('name', $.identifier),              // Name of the variable
      ':',                                      // Separator between name and type
      field('type', $._variable_type),          // Type of the variable
      optional(seq(':', field('subtype', $.identifier))), // Optional subtype for certain variable types
      repeat(choice(
        'temporary',                            // Temporary variable (exists only for the duration of a function call)
        seq('array', '[', optional($.number), ']'), // Array declaration with optional size
        'protected',                            // Protected access modifier
        'locked',                               // Locked variable (cannot be modified after initial assignment)
        'withevents'                            // Variable that can respond to events
      )),
      optional($.label_properties),             // Optional label properties for multilingual support
      ';'                                       // Statement terminator
    ),

    // Label properties definition
    // Used for defining multilingual labels
    label_properties: $ => seq(
      'Label',                 // Keyword indicating a label definition
      choice(
        $.string,              // Single language label
        seq(
          '{',
          repeat1($.label_property), // Multiple language labels
          '}'
        )
      )
    ),

    // Individual label property definition
    label_property: $ => seq(
      field('language', $.identifier), // Language identifier
      '=',
      field('value', $.string),        // Label text
      optional(',')                    // Optional comma separator
    ),

    // Duplicate definitions removed

    // Variable type definition
    // This includes all the built-in types in AL and allows for custom types
    _variable_type: $ => choice(
      // Basic types
      'Action', 'Array', 'BigInteger', 'BigText', 'Binary', 'Boolean', 'Char', 'Code',
      // Complex types
      'Codeunit', 'CompanyProperty', 'Database', 'DataClassification',
      // Date and time types
      'Date', 'DateFormula', 'DateTime', 'Time',
      // Numeric types
      'Decimal', 'Integer',
      // UI and interaction types
      'Dialog', 'Notification', 'Page', 'Report', 'RequestPage',
      // Collection types
      'Dictionary', 'List',
      // File and stream types
      'File', 'InStream', 'OutStream',
      // Reference types
      'FieldRef', 'KeyRef', 'RecordRef',
      // Other types
      'Duration', 'Enum', 'ErrorInfo', 'FilterPageBuilder', 'Guid', 'HttpClient',
      'HttpContent', 'HttpHeaders', 'HttpRequestMessage', 'HttpResponseMessage',
      'Interface', 'JsonArray', 'JsonObject', 'JsonToken', 'JsonValue', 'Label',
      'ModuleDependencyInfo', 'ModuleInfo', 'Option', 'Query', 'Record', 'RecordId',
      'System', 'TableConnectionType', 'TableFilter', 'TestAction', 'TestField',
      'TestFilterField', 'TestPage', 'TestPermissions', 'TestRequestPage', 'Text',
      'TextBuilder', 'TextConst', 'TransactionModel', 'Variant', 'Verbosity',
      'Version', 'XmlPort',
      $.identifier  // For custom types
    ),

    // Elements that can appear within a codeunit
    _codeunit_element: $ => choice(
      $.procedure_definition,   // Function definitions
      $.trigger_definition,     // Event trigger definitions
      $.variable_declaration,   // Variable declarations
      $.textconst_definition    // Text constant definitions
    ),

    // Definition of a local procedure
    // Local procedures are only accessible within the codeunit
    local_procedure_definition: $ => seq(
      'local',                  // Keyword indicating a local procedure
      $.procedure_definition    // The actual procedure definition
    ),

    // Parameter definition for procedures and triggers

    // Procedure definition

    // Procedure description (XML documentation)
    procedure_description: $ => seq(
      '@',
      field('language', $.identifier),
      ':',
      field('description', $.string)
    ),

    // Parameter list definition

    // Parameter definition
    parameter: $ => seq(
      optional(choice('var', 'out')),        // Parameter passing method
      optional('temporary'),                 // Temporary parameter
      field('name', $.identifier),
      ':',
      field('type', $.type),
      optional($.procedure_description)      // Parameter description
    ),

    // Procedure overload definition
    procedure_overload: $ => seq(
      'procedure',
      field('name', $.identifier),
      '(',
      optional($.parameter_list),
      ')',
      optional(seq(':', field('return_type', $.type))),
      optional($.var_section),
      $.procedure_body
    ),

    // Access modifiers for procedures
    procedure_access_modifier: $ => choice(
      'internal',
      'protected',
      'public'
    ),

    // Procedure body definition
    procedure_body: $ => seq(
      'begin',
      repeat(choice($._statement, $.preprocessor_directive, $.variable_declaration)),
      optional($.on_error_section),
      'end;'
    ),

    // Pragma directive for compiler instructions
    pragma_directive: $ => prec.left(seq(
      '#PRAGMA',
      field('name', $.pragma_name),
      optional($.pragma_arguments)
    )),

    // Preprocessor directives for conditional compilation
    preprocessor_directive: $ => choice(
      $.if_directive,
      $.endif_directive,
      $.else_directive,
      $.elif_directive,
      $.pragma_directive
    ),

    if_directive: $ => seq('#IF', $.identifier),
    elif_directive: $ => seq('#ELIF', $.identifier),
    else_directive: $ => '#ELSE',
    endif_directive: $ => '#ENDIF',

    // Pragma names and arguments
    pragma_name: $ => choice(
      'warning',
      'error',
      'implicitwith',
      'inline'
    ),
    pragma_arguments: $ => seq(
      $.pragma_argument,
      repeat(seq(',', $.pragma_argument))
    ),
    pragma_argument: $ => choice(
      $.string,
      $.number,
      $.identifier
    ),

    // Statement definition
    // This rule defines all the possible statements in AL
    _statement: $ => choice(
      $.assignment_statement,
      $.procedure_call,
      $.if_statement,
      $.while_statement,
      $.repeat_statement,
      $.case_statement,
      $.with_statement,
      $.temporary_statement,
      $.for_statement,
      $.foreach_statement,
      $.break_statement,
      $.exit_statement,
      $.try_function,
      $.preprocessor_directive,
      $.error_statement
    ),

    // Procedure call definition
    procedure_call: $ => seq(
      field('name', $.identifier),
      '(',
      optional(commaSep1($._expression)),
      ')',
      ';'
    ),

    // Comment definition
    comment: $ => token(choice(
      seq('//', /.*/),  // Single-line comment
      seq(
        '/*',
        /[^*]*\*+([^/*][^*]*\*+)*/,
        '/'
      )  // Multi-line comment
    )),

    // XML comment definition (for documentation)
    xml_comment: $ => seq(
      '///',
      repeat(choice(
        $.xml_comment_text,
        $.xml_comment_tag
      )),
      /\r?\n/
    ),

    xml_comment_text: $ => /[^<\r\n]+/,

    xml_comment_tag: $ => seq(
      '<',
      $.xml_tag_name,
      optional($.xml_attributes),
      choice('>', '/>')
    ),

    xml_tag_name: $ => /[a-zA-Z][a-zA-Z0-9]*/,

    xml_attributes: $ => repeat1($.xml_attribute),

    xml_attribute: $ => seq(
      $.xml_attribute_name,
      '=',
      choice(
        seq('"', optional($.xml_attribute_value), '"'),
        seq("'", optional($.xml_attribute_value), "'")
      )
    ),

    xml_attribute_name: $ => /[a-zA-Z][a-zA-Z0-9]*/,
    xml_attribute_value: $ => /[^"']*/,


    _object_header: $ => seq(
      field('id', $.object_id),
      field('name', $.object_name)
    ),

    object_id: $ => /\d+/,

    object_name: $ => /"[^"]*"/,

    table_definition: $ => seq(
      'table',
      $._object_header,
      '{',
      repeat($._table_body_element),
      '}'
    ),

    _object_body: $ => seq(
      '{',
      repeat($._object_member),
      '}'
    ),

    _object_member: $ => choice(
      $.field_definition,
      $.procedure_definition,
      $.variable_declaration,
      $.trigger_definition,
      $.layout,
      $.actions,
      $.dataitem,
      $.column,
      $.textelement,
      $.enum_value,
      $.permission,
      $.profile_setting,
      $.assembly_declaration
    ),

    trigger_definition: $ => seq(
      'trigger',
      field('name', $.trigger_name),
      '()',
      $.procedure_body
    ),

    trigger_name: $ => choice(
      // Table triggers
      'OnInsert', 'OnModify', 'OnDelete', 'OnRename', 'OnValidate', 'OnLookup',
      // Keep other trigger names as they were...
      'OnInit', 'OnOpenPage', 'OnClosePage', 'OnFindRecord', 'OnNextRecord',
      'OnAfterGetRecord', 'OnNewRecord', 'OnInsertRecord', 'OnModifyRecord',
      'OnDeleteRecord', 'OnQueryClosePage', 'OnAfterGetCurrRecord',
      'OnPageBackgroundTaskCompleted', 'OnAfterGetRecord', 'OnBeforeInsertRecord',
      'OnBeforeValidate', 'OnValidate', 'OnAfterValidate',
      'OnInitReport', 'OnPreReport', 'OnPostReport',
      'OnInitXMLport', 'OnPreXMLport', 'OnPostXMLport',
      'OnBeforeOpen', 'OnAfterOpen',
      'OnRun',
      'OnAfterAssignVariable', 'OnBeforePassVariable',
      'OnBeforeValidate', 'OnAfterValidate',
      'OnAction', 'OnDrillDown', 'OnAssistEdit', 'OnControlAddIn',
      'OnAfterGetRecordEvent', 'OnBeforeGetRecordEvent', 'OnOpenPageEvent',
      'OnClosePageEvent', 'OnQueryClosePageEvent', 'OnDeleteRecordEvent',
      'OnInsertRecordEvent', 'OnModifyRecordEvent', 'OnNewRecordEvent',
      'OnFindRecordEvent', 'OnNextRecordEvent', 'OnAfterGetCurrRecordEvent',
      'OnDocumentReady', 'OnAfterInitRecord', 'OnBeforeAction',
      'OnAfterAction', 'OnBeforeInsertRecord', 'OnBeforeModifyRecord',
      'OnBeforeDeleteRecord', 'OnBeforeOnRun', 'OnAfterOnRun'
    ),

    table_definition: $ => seq(
      'table',
      $._object_header,
      '{',
      repeat($._table_body_element),
      '}'
    ),


    page_definition: $ => seq(
      'page',
      $._object_header,
      '{',
      repeat($._page_element),
      optional($.promoted_action_categories),
      '}'
    ),

    promoted_action_categories: $ => seq(
      'PromotedActionCategories',
      '=',
      '{',
      repeat($.promoted_action_category),
      '}'
    ),

    promoted_action_category: $ => seq(
      field('id', $.string),
      ':',
      field('caption', $.string),
      ';'
    ),

    _page_element: $ => choice(
      $.layout,
      $.actions,
      $.procedure_definition,
      $.variable_declaration
    ),

    layout: $ => seq(
      'layout',
      '{',
      repeat($._layout_element),
      '}'
    ),

    _layout_element: $ => choice(
      $.group,
      $.field
    ),

    group: $ => seq(
      'group',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($._layout_element),
      '}'
    ),

    field: $ => seq(
      'field',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      repeat($._field_property),
      '}'
    ),

    _field_property: $ => choice(
      $.caption_property,
      $.property
    ),

    field_property: $ => seq(
      field('name', $.identifier),
      '=',
      field('value', $._property_value),
      ';'
    ),

    field_property_name: $ => $.identifier,

    report_definition: $ => seq(
      'report',
      $._object_header,
      $._object_body
    ),

    codeunit_definition: $ => seq(
      'codeunit',
      $.object_id,
      $.object_name,
      '{',
      optional($.var_section),
      repeat($._codeunit_element),
      '}'
    ),

    query_definition: $ => seq(
      'query',
      $._object_header,
      $._object_body
    ),

    xmlport_definition: $ => seq(
      'xmlport',
      $._object_header,
      $._object_body
    ),

    enum_definition: $ => seq(
      'enum',
      $._object_header,
      '{',
      repeat($.enum_value),
      '}'
    ),

    interface_definition: $ => seq(
      'interface',
      $._object_header,
      '{',
      repeat($.procedure_prototype),
      '}'
    ),

    permissionset_definition: $ => seq(
      'permissionset',
      $._object_header,
      '{',
      repeat($.permission),
      '}'
    ),

    permissionsetextension_definition: $ => seq(
      'permissionsetextension',
      $._object_header,
      '{',
      repeat($.permission),
      '}'
    ),

    profile_definition: $ => seq(
      'profile',
      $._object_header,
      '{',
      repeat($.profile_setting),
      '}'
    ),

    dotnet_package_definition: $ => seq(
      'dotnet',
      '{',
      repeat($.assembly_declaration),
      '}'
    ),


    key_definition: $ => seq(
      'key',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      commaSep1($.identifier),
      '}',
      optional(seq(
        '{',
        repeat($.key_property),
        '}'
      )),
      ';'
    ),

    key_property: $ => choice(
      $.enabled_property,
      $.clustered_property,
      $.unique_property,
      $.property
    ),

    clustered_property: $ => seq(
      'Clustered',
      '=',
      field('value', $.boolean),
      ';'
    ),

    enabled_property: $ => seq(
      'Enabled',
      '=',
      field('value', $.boolean),
      ';'
    ),

    clustered_property: $ => seq(
      'Clustered',
      '=',
      field('value', $.boolean),
      ';'
    ),

    unique_property: $ => seq(
      'Unique',
      '=',
      field('value', $.boolean),
      ';'
    ),


    procedure_body: $ => seq(
      'begin',
      repeat($._statement),
      'end;'
    ),



    field_definition: $ => seq(
      'field',
      '(',
      field('id', $.field_id),
      ';',
      field('name', $.field_name),
      ';',
      field('type', $.field_type),
      ')',
      optional(seq(
        '{',
        repeat($._field_property),
        '}'
      ))
    ),

    _field_property: $ => choice(
      $.caption_property,
      $.property,
      $.option_members
    ),

    field_id: $ => /\d+/,
    field_name: $ => /"[^"]*"/,
    field_type: $ => choice(
      $.identifier,
      'Option'
    ),

    option_members: $ => seq(
      'OptionMembers',
      '=',
      commaSep1($.string),
      ';'
    ),

    property: $ => prec.dynamic(-1, seq(
      field('name', $.property_name),
      '=',
      field('value', $._property_value),
      ';'
    )),

    property_name: $ => choice(
      'PasteIsValid',
      'LookupPageID',
      'DrillDownPageID',
      'SqlDataType',
      'SqlTimestamp',
      'SubstitutionAllowed',
      'TableRelation',
      'TestTableRelation',
      'ValidateTableRelation',
      'ValuesAllowed',
      'Width',
      'DataClassification',
      $.identifier
    ),

    _property_value: $ => choice(
      $.string,
      $.number,
      $.boolean,
      $.identifier,
      $.property_value_list
    ),

    property_value_list: $ => seq(
      '[',
      commaSep1($._property_value),
      ']'
    ),

    option_members: $ => seq(
      'OptionMembers',
      '=',
      commaSep1($.string),
      ';'
    ),

    data_classification_property: $ => seq(
      'DataClassification',
      '=',
      field('classification', $.data_classification_value),
      ';'
    ),

    data_classification_value: $ => choice(
      'ToBeClassified',
      'CustomerContent',
      'EndUserIdentifiableInformation',
      'AccountData',
      'EndUserPseudonymousIdentifiers',
      'OrganizationIdentifiableInformation',
      'SystemMetadata'
    ),

    access_level_property: $ => seq(
      'AccessLevel',
      '=',
      field('level', choice('Public', 'Internal', 'Private')),
      ';'
    ),

    data_captionfields_property: $ => seq(
      'DataCaptionFields',
      '=',
      '[',
      commaSep1($.identifier),
      ']',
      ';'
    ),

    field_id: $ => /\d+/,
    field_name: $ => /"[^"]*"/,
    field_type: $ => choice(
      'Action',
      'BigInteger',
      'Binary',
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
      'Time'
    ),

    variable_declaration: $ => seq(
      'var',
      field('name', $.identifier),
      ':',
      field('type', $.type),
      ';'
    ),


    parameter_list: $ => seq(
      $.parameter,
      repeat(seq(';', $.parameter))
    ),


    parameter_attribute: $ => seq(
      '[',
      choice('FromSet', 'RunOnClient'),
      optional(seq('(', commaSep1($._expression), ')')),
      ']'
    ),

    procedure_body: $ => seq(
      'begin',
      repeat(choice($._statement, $.preprocessor_directive)),
      'end;'
    ),


    _statement: $ => choice(
      $.assignment_statement,
      $.procedure_call,
      $.exit_statement,
      $.if_statement,
      $.error_statement
      // Add more statement types as needed
    ),

    exit_statement: $ => seq(
      'exit',
      optional($._expression),
      ';'
    ),

    if_statement: $ => seq(
      'if',
      $._expression,
      'then',
      repeat($._statement),
      optional(seq('else', repeat($._statement))),
      'end'
    ),

    error_statement: $ => seq(
      'error',
      '(',
      $._expression,
      ')',
      ';'
    ),

    assignment_statement: $ => seq(
      field('left', $.identifier),
      ':=',
      field('right', $._expression),
      ';'
    ),

    procedure_call: $ => seq(
      field('name', $.identifier),
      '(',
      optional(commaSep1(choice($._expression, $.named_argument))),
      ')',
      ';'
    ),

    named_argument: $ => seq(
      field('name', $.identifier),
      ':',
      $._expression
    ),

    _expression: $ => choice(
      $.identifier,
      $.literal,
      $.system_variable,
      $.parenthesized_expression,
      $.field_access
      // Add more expression types as needed
    ),

    parenthesized_expression: $ => seq(
      '(',
      $._expression,
      ')'
    ),

    field_access: $ => seq(
      $._expression,
      '.',
      $.identifier
    ),

    identifier: $ => choice(
      /[a-zA-Z_][a-zA-Z0-9_]*/,
      /"[^"]+"/
    ),

    system_variable: $ => choice(
      'CurrPage',
      'Rec',
      'xRec',
      'CurrReport',
      'CurrFieldNo',
      'RequestOptionsPage',
      'ReportFormatting',
      'CurrXMLport',
      'CurrQuery',
      'ActiveSession',
      'Session',
      'Database',
      'CompanyProperty',
      'ApplicationPath',
      'EncryptionEnabled',
      'HybridDeployment',
      'IsServiceTier',
      'Printer',
      'ReportManagement',
      'TaskScheduler',
      'VersionManagement',
      'WebServiceManagement'
    ),

    type: $ => choice(
      'Text',
      'Code',
      'Decimal',
      'Integer',
      'Boolean',
      'Date',
      'Time',
      'DateTime',
      'Blob',
      'Guid',
      'RecordId',
      'TableFilter',
      'BigInteger',
      'Duration',
      'DateFormula',
      'ErrorInfo',
      $.identifier  // Allow custom types
    ),

    literal: $ => prec(1, choice(
      $.number,
      $.string,
      $.boolean
    )),

    number: $ => /\d+(\.\d+)?/,
    string: $ => /"[^"]*"/,
    boolean: $ => choice('true', 'false'),

    enum_value: $ => seq(
      field('name', $.identifier),
      '=',
      field('value', $.number),
      optional(';')
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
      $.action_name,
      ')',
      '{',
      repeat($.action_property),
      '}'
    ),

    action_name: $ => /"[^"]*"/,

    action_property: $ => seq(
      $.property_name,
      '=',
      $.property_value,
      ';'
    ),

    caption_property: $ => seq(
      'Caption',
      '=',
      field('caption_value', $.string),
      ';'
    ),

    init_value_property: $ => seq(
      'InitValue',
      '=',
      field('value', $._expression),
      ';'
    ),

    option_caption_property: $ => prec(2, seq(
      'OptionCaption',
      '=',
      field('captions', $.string),
      ';'
    )),

    property_name: $ => choice(
      // General properties
      'AccessByPermission',
      'ApplicationArea',
      'AutoCaption',
      'AutoFormatExpression',
      'AutoFormatType',
      'Caption',
      'CaptionClass',
      'CaptionML',
      'CardPageID',
      'DataCaptionFields',
      'Description',
      'DelayedInsert',
      'DeleteAllowed',
      'Editable',
      'Enabled',
      'Extensible',
      'HelpLink',
      'Image',
      'InherentEntitlements',
      'InherentPermissions',
      'InsertAllowed',
      'LinksAllowed',
      /LookupPageID/i,
      'ModifyAllowed',
      'MultipleNewLines',
      'NotifyOnDelete',
      'ObsoleteReason',
      'ObsoleteState',
      'PageType',
      'Permissions',
      'PopulateAllFields',
      'PromotedActionCategories',
      'RefreshOnActivate',
      'SaveValues',
      'ShowFilter',
      'SourceTable',
      'SourceTableTemporary',
      'SourceTableView',
      'UsageCategory',
      'Visible',

      // Layout properties
      'ColumnSpan',
      'GridLayout',
      'Group',
      'IndentationColumn',
      'IndentationControls',
      'Layout',
      'MoveBefore',
      'MoveAfter',
      'ShowCaption',

      // Action properties
      'AboutText',
      'AboutTitle',
      'Gesture',
      'Image',
      'InFooterBar',
      'Promoted',
      'PromotedCategory',
      'PromotedIsBig',
      'PromotedOnly',
      'RunObject',
      'RunPageMode',
      'ShortcutKey',
      'ToolTip',

      // Field properties
      'AssistEdit',
      'AutoOption',
      'BlankNumbers',
      'BlankZero',
      'CalcFormula',
      'CharAllowed',
      'ClosingDates',
      'DecimalPlaces',
      'DrillDown',
      'DrillDownPageID',
      'ExtendedDatatype',
      'FieldClass',
      'ImportanceLevel',
      'Lookup',
      'LookupPageID',
      'MaxValue',
      'MinValue',
      'NotBlank',
      'Numeric',
      'OptionCaptionML',
      'OptionMembers',
      'OptionOrdinalValues',
      'QuickEntry',
      'RelationTableField',
      'RowSpan',
      'ShowMandatory',
      'SignDisplacement',
      'Style',
      'StyleExpr',
      'TableRelation',
      'ValidateTableRelation',
      'ValuesAllowed',
      'Width',

      // Other properties
      'AllowInCustomizations',
      'AutoSplitKey',
      'DataCaptionExpr',
      'DateFormula',
      'DefaultFieldsValidation',
      'Dimensions',
      'ExternalType',
      'FreezeColumnID',
      'GroupName',
      'Importance',
      'InstructionalText',
      'IntegerType',
      'MultiLine',
      'ObsoleteTag',
      'PasteIsValid',
      'PrimaryKey',
      'SubPageLink',
      'SubPageView',
      'SubType',
      'TestPermissions',
      'TextType',
      'Validation',

      // Report-specific properties
      'AdditionalSearchTerms',
      'DefaultLayout',
      'EnableExternalAssemblies',
      'EnableHyperlinks',
      'PaperSourceDefaultPage',
      'PaperSourceFirstPage',
      'PaperSourceLastPage',
      'PreviewMode',
      'ProcessingOnly',
      'RDLCLayout',
      'RequestFilterFields',
      'RequestFilterHeading',
      'TransactionType',
      'UseRequestPage',
      'UseSystemPrinter',
      'WordLayout'
    ),
    property_value: $ => choice($.identifier, $.literal),

    report_definition: $ => seq(
      'report',
      $.object_id,
      $.object_name,
      '{',
      repeat($._report_element),
      '}'
    ),

    _report_element: $ => choice(
      $.dataset,
      $.requestpage,
      $.procedure_definition
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
      $.dataitem_name,
      ';',
      $.table_name,
      ')',
      '{',
      repeat($._dataitem_element),
      '}'
    ),

    dataitem_name: $ => /"[^"]*"/,
    table_name: $ => /"[^"]*"/,

    _dataitem_element: $ => choice(
      $.column,
      $.dataitem
    ),

    column: $ => seq(
      'column',
      '(',
      $.column_id,
      ';',
      $.column_name,
      ')',
      '{',
      '}'
    ),

    column_id: $ => /\d+/,
    column_name: $ => /"[^"]*"/,

    requestpage: $ => seq(
      'requestpage',
      '{',
      repeat($.control),
      '}'
    ),

    control: $ => seq(
      'field',
      '(',
      $.control_name,
      ';',
      $.control_type,
      ')',
      '{',
      repeat($.control_property),
      '}'
    ),

    control_name: $ => /"[^"]*"/,
    control_type: $ => /[A-Za-z]+/,

    control_property: $ => seq(
      $.property_name,
      '=',
      $.property_value,
      ';'
    ),

    query_definition: $ => seq(
      'query',
      $.object_id,
      $.object_name,
      '{',
      repeat($._query_element),
      '}'
    ),

    _query_element: $ => choice(
      $.elements,
      $.procedure_definition
    ),

    elements: $ => seq(
      'elements',
      '{',
      repeat($.dataitem),
      '}'
    ),

    xmlport_definition: $ => seq(
      'xmlport',
      $.object_id,
      $.object_name,
      '{',
      repeat($._xmlport_element),
      '}'
    ),

    _xmlport_element: $ => choice(
      $.schema,
      $.procedure_definition
    ),

    schema: $ => seq(
      'schema',
      '{',
      repeat($.textelement),
      '}'
    ),

    textelement: $ => seq(
      'textelement',
      '(',
      $.element_name,
      ')',
      '{',
      repeat($.element_property),
      '}'
    ),

    element_name: $ => /"[^"]*"/,

    element_property: $ => seq(
      $.property_name,
      '=',
      $.property_value,
      ';'
    ),

    enum_definition: $ => seq(
      'enum',
      $.object_id,
      $.object_name,
      optional($.implements_clause),
      '{',
      optional($.enum_properties),
      repeat($.enum_value),
      '}'
    ),

    property: $ => seq(
      field('name', $.property_name),
      '=',
      field('value', $._property_value),
      ';'
    ),

    property_name: $ => choice(
      'PasteIsValid',
      'LookupPageID',
      'DrillDownPageID',
      $.identifier
    ),

    _property_value: $ => choice(
      $.string,
      $.number,
      $.boolean,
      $.identifier
    ),

    _table_body_element: $ => choice(
      $.caption_property,
      $.data_classification_property,
      $.data_per_company_property,
      $.drill_down_page_id_property,
      $.lookup_page_id_property,
      $.extensible_property,
      $.external_name_property,
      $.external_schema_property,
      $.linked_object_property,
      $.obsolete_state_property,
      $.obsolete_reason_property,
      $.table_type_property,
      $.external_access_property,
      $.moved_from_property,
      $.moved_to_property,
      $.access_level_property,
      $.data_captionfields_property,
      $.description_property,
      $.primary_key_property,
      $.field_definition,
      $.key_definition,
      $.procedure_definition,
      $.variable_declaration,
      $.trigger_definition,
      $.field_group,
      prec(-1, $.property)
    ),

    field_group: $ => seq(
      'fieldgroup',
      '(',
      field('name', $.identifier),

    data_classification_property: $ => seq(
      'DataClassification',
      '=',
      field('classification', $.data_classification_value),
      ';'
    ),

    data_classification_value: $ => choice(
      'ToBeClassified',
      'CustomerContent',
      'EndUserIdentifiableInformation',
      'AccountData',
      'EndUserPseudonymousIdentifiers',
      'OrganizationIdentifiableInformation',
      'SystemMetadata'
    ),
      ')',
      '{',
      commaSep1($.identifier),
      '}',
      ';'
    ),

    field_definition: $ => seq(
      'field',
      '(',
      field('id', $.field_id),
      ';',
      field('name', $.field_name),
      ';',
      field('type', $.field_type),
      ')',
      optional(seq(
        '{',
        repeat(choice(
          $.caption_property,
          $.data_classification_property,
          $.option_members,
          $.table_relation_property,
          $.validate_property,
          $.access_level_property,
          $.description_property,
          $.property,
          $.field_class_property
        )),
        '}'
      ))
    ),

    field_id: $ => /\d+/,
    field_name: $ => /"[^"]*"/,
    field_type: $ => choice(
      'Text',
      'Code',
      'Decimal',
      'Integer',
      'Boolean',
      'Date',
      'Time',
      'DateTime',
      'Blob',
      'Guid',
      'RecordId',
      'TableFilter',
      'BigInteger',
      'Duration',
      'DateFormula',
      $.identifier
    ),

    field_class_property: $ => seq(
      'FieldClass',
      '=',
      field('class', choice('Normal', 'FlowField', 'FlowFilter')),
      ';'
    ),

    table_relation_property: $ => seq(
      'TableRelation',
      '=',
      field('relation', $.table_relation),
      ';'
    ),

    table_relation: $ => seq(
      $.identifier,
      optional(seq(
        '.',
        $.identifier,
        optional(seq('where', $.table_relation_filter))
      ))
    ),

    table_relation_filter: $ => seq(
      '(',
      commaSep1($.table_relation_filter_item),
      ')'
    ),

    table_relation_filter_item: $ => seq(
      $.identifier,
      '=',
      choice(
        $.identifier,
        seq('field', '(', $.identifier, ')')
      )
    ),

    validate_property: $ => seq(
      'ValidateTableRelation',
      '=',
      field('value', $.boolean),
      ';'
    ),

    field_id: $ => /\d+/,
    field_name: $ => /"[^"]*"/,
    field_type: $ => choice(
      'Text',
      'Code',
      'Decimal',
      'Integer',
      'Boolean',
      'Date',
      'Time',
      'DateTime',
      'Blob',
      'Guid',
      'RecordId',
      'TableFilter',
      'BigInteger',
      'Duration',
      'DateFormula',
      $.identifier
    ),

    data_classification: $ => seq(
      'DataClassification',
      '=',
      choice(
        'ToBeClassified',
        'CustomerContent',
        'EndUserIdentifiableInformation',
        'AccountData',
        'EndUserPseudonymousIdentifiers',
        'OrganizationIdentifiableInformation',
        'SystemMetadata'
      ),
      ';'
    ),

    key_definition: $ => seq(
      'key',
      '(',
      field('name', $.identifier),
      ')',
      '{',
      commaSep1($.identifier),
      '}',
      optional(seq(
        '{',
        repeat($.property),
        '}'
      )),
      ';'
    ),

    _page_body_element: $ => choice(
      $.layout,
      $.actions,
      $.procedure_definition,
      $.variable_declaration,
      $.trigger_definition,
      $.property
    ),

    tableextension: $ => seq(
      'tableextension',
      field('tableextension_id', $.number),
      field('tableextension_name', choice($.string, $.identifier)),
      'extends',
      field('base_table', choice($.string, $.identifier)),
      '{',
      repeat($._table_body_element),
      '}'
    ),

    pageextension: $ => seq(
      'pageextension',
      field('pageextension_id', $.number),
      field('pageextension_name', $.identifier),
      'extends',
      field('base_page', $.identifier),
      '{',
      repeat($._page_body_element),
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
      field('permissionset_id', $.number),
      field('permissionset_name', $.identifier),
      '{',
      repeat($.permission),
      '}'
    ),

    permissionsetextension: $ => seq(
      'permissionsetextension',
      field('permissionsetextension_id', $.number),
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

    implements_clause: $ => seq(
      'implements',
      $.identifier,
      repeat(seq(',', $.identifier))
    ),

    enum_properties: $ => repeat1($.enum_property),

    enum_property: $ => seq(
      field('name', $.identifier),
      '=',
      field('value', choice($.string, $.boolean)),
      ';'
    ),

    enum_value: $ => seq(
      'value',
      '(',
      $.enum_id,
      ';',
      $.enum_name,
      ')',
      optional(
        seq(
          '{',
          repeat($.enum_value_property),
          '}'
        )
      )
    ),

    enum_value_properties: $ => seq(
      '{',
      repeat($.enum_value_property),
      '}'
    ),

    enum_value_property: $ => seq(
      field('name', $.identifier),
      '=',
      field('value', $.string),
      optional(seq(',', field('locked', $.identifier), '=', $.boolean)),
      ';'
    ),

    enum_id: $ => /\d+/,
    enum_name: $ => choice(
      $.string,
      $.identifier,
      seq('"', $.identifier, $.identifier, '"')
    ),

    identifier: $ => /[a-zA-Z_][a-zA-Z0-9_]*/,
    string: $ => /"[^"]*"/,
    boolean: $ => choice('true', 'false'),

    procedure_prototype: $ => seq(
      'procedure',
      $.procedure_name,
      '(',
      optional($.parameter_list),
      ')',
      optional(seq(':', $.return_type)),
      ';'
    ),

    permission: $ => seq(
      $.permission_type,
      '=',
      $.permission_object,
      ';'
    ),

    permission_type: $ => choice(
      'TableData',
      'Table',
      'Report',
      'Codeunit',
      'XMLport',
      'Page',
      'Query',
      'System'
    ),

    permission_object: $ => seq(
      $.object_name,
      '=',
      commaSep1($.permission_level)
    ),

    permission_level: $ => choice(
      'R',
      'X',
      'I',
      'M',
      'D'
    ),

    caption_property: $ => prec(2, seq(
      'Caption',
      '=',
      field('caption_value', $.string),
      ';'
    )),

    data_per_company_property: $ => prec.dynamic(1, seq(
      'DataPerCompany',
      '=',
      field('value', $.boolean),
      ';'
    )),

    drill_down_page_id_property: $ => prec.dynamic(1, seq(
      'DrillDownPageId',
      '=',
      field('page_id', choice($.number, $.identifier)),
      ';'
    )),

    extensible_property: $ => prec.dynamic(1, seq(
      'Extensible',
      '=',
      field('value', $.boolean),
      ';'
    )),

    external_name_property: $ => prec.dynamic(1, seq(
      'ExternalName',
      '=',
      field('name', $.string),
      ';'
    )),

    external_schema_property: $ => prec.dynamic(1, seq(
      'ExternalSchema',
      '=',
      field('schema', $.string),
      ';'
    )),

    linked_object_property: $ => prec.dynamic(1, seq(
      'LinkedObject',
      '=',
      field('object', $.string),
      ';'
    )),

    lookup_page_id_property: $ => prec.dynamic(1, seq(
      'LookupPageId',
      '=',
      field('page_id', choice(
        $.number,
        $.identifier
      )),
      ';'
    )),

    obsolete_reason_property: $ => prec.dynamic(1, seq(
      'ObsoleteReason',
      '=',
      field('reason', $.string),
      ';'
    )),

    obsolete_state_property: $ => prec.dynamic(1, seq(
      'ObsoleteState',
      '=',
      field('state', $.identifier),
      ';'
    )),

    table_type_property: $ => seq(
      'TableType',
      '=',
      field('type', $.identifier),
      ';'
    ),

    external_access_property: $ => seq(
      'ExternalAccess',
      '=',
      field('access', $.identifier),
      ';'
    ),

    moved_from_property: $ => seq(
      'MovedFrom',
      '=',
      field('source', $.string),
      ';'
    ),

    moved_to_property: $ => seq(
      'MovedTo',
      '=',
      field('destination', $.string),
      ';'
    ),

    description_property: $ => seq(
      'Description',
      '=',
      field('description', $.string),
      ';'
    ),

    primary_key_property: $ => seq(
      'PrimaryKey',
      '(',
      commaSep1($.identifier),
      ')',
      ';'
    ),

    profile_setting: $ => seq(
      $.setting_name,
      '=',
      $.setting_value,
      ';'
    ),

    setting_name: $ => /[a-zA-Z_][a-zA-Z0-9_]*/,
    setting_value: $ => choice($.string, $.boolean, $.number),

    assembly_declaration: $ => seq(
      'assembly',
      '(',
      $.assembly_name,
      ')',
      '{',
      repeat($.type_declaration),
      '}'
    ),

    assembly_name: $ => /"[^"]*"/,

    type_declaration: $ => seq(
      'type',
      '(',
      $.type_name,
      ')',
      '{',
      repeat($.member_declaration),
      '}'
    ),

    type_name: $ => /"[^"]*"/,

    member_declaration: $ => seq(
      $.member_type,
      $.member_name,
      '(',
      optional($.parameter_list),
      ')',
      optional(seq(':', $.return_type)),
      ';'
    ),

    member_type: $ => choice('method', 'constructor'),
    member_name: $ => /"[^"]*"/,

    variable_declaration: $ => seq(
      'var',
      field('name', $.identifier),
      ':',
      field('type', $.type),
      ';'
    ),

    procedure_definition: $ => seq(
      optional($.access_modifier),
      optional(repeat($.attribute)),
      'procedure',
      field('name', $.procedure_name),
      '(',
      optional(commaSep1($.parameter)),
      ')',
      optional(seq(':', field('return_type', $.type))),
      optional($.var_section),
      $.procedure_body
    ),

    parameter: $ => seq(
      optional(choice('var', 'out')),
      optional('temporary'),
      field('name', $.identifier),
      ':',
      field('type', $.type)
    ),

    procedure_name: $ => prec(1, /[a-zA-Z_][a-zA-Z0-9_]*/),

    procedure_body: $ => seq(
      'begin',
      repeat(choice($._statement, $.preprocessor_directive)),
      'end;'
    ),

    _statement: $ => choice(
      $.assignment_statement,
      $.procedure_call,
      $.if_statement,
      $.while_statement,
      $.repeat_statement,
      $.case_statement,
      $.with_statement,
      $.temporary_statement,
      $.for_statement,
      $.foreach_statement,
      $.break_statement,
      $.exit_statement,
      $.try_function,
      $.preprocessor_directive,
      $.error_statement
    ),

    if_statement: $ => seq(
      'if',
      $._expression,
      'then',
      repeat($._statement),
      optional(seq('else', repeat($._statement))),
      'end'
    ),

    exit_statement: $ => seq(
      'exit',
      '(',
      optional($._expression),
      ')',
      ';'
    ),

    parameter_list: $ => commaSep1($.parameter),



    event_subscriber: $ => seq(
      '[EventSubscriber(',
      commaSep1($.event_parameter),
      ')]'
    ),

    event_parameter: $ => seq(
      $.event_parameter_name,
      '=',
      $.event_parameter_value
    ),

    event_parameter_name: $ => choice(
      'ObjectType',
      'ObjectId',
      'EventType',
      'EventPublisherObject',
      'EventFunction',
      'OnMissingLicense',
      'OnMissingPermission',
      'SkipOnMissingLicense',
      'SkipOnMissingPermission'
    ),

    event_parameter_value: $ => choice(
      $.string,
      $.number,
      $.boolean,
      $.identifier
    ),

    access_modifier: $ => choice(
      'internal',
      'protected',
      'public'
    ),

    attribute: $ => choice(
      seq(
        '[',
        $.attribute_name,
        optional(seq('(', commaSep1($.attribute_argument), ')')),
        ']'
      ),
      $.event_subscriber,
      $.try_function_attribute
    ),

    attribute_name: $ => choice(
      'NonDebuggable',
      'InDataSet',
      'Obsolete',
      'BusinessEvent',
      'IntegrationEvent',
      'Scope',
      'ErrorBehavior',
      'ExternalBusinessEvent',
      'ExternalSqlConnection',
      'EventSubscriber',
      'ServiceEnabled',
      'Test',
      'TransactionModel',
      'CommitBehavior',
      'HandlerFunctions',
      /[A-Za-z]+/  // For custom attributes
    ),

    try_function_attribute: $ => seq(
      '[',
      'TryFunction',
      ']'
    ),

    attribute_argument: $ => choice(
      $.string,
      $.number,
      $.boolean,
      $.identifier
    ),

    procedure_name: $ => prec(1, /[a-zA-Z_][a-zA-Z0-9_]*/),

    parameter_list: $ => commaSep1($.parameter),

    parameter: $ => seq(
      optional(choice('var', 'out')),
      optional('temporary'),
      field('name', $.identifier),
      ':',
      field('type', $.type),
      optional($.procedure_description)
    ),

    return_type: $ => /[A-Za-z]+/,

    procedure_body: $ => seq(
      'begin',
      repeat($._statement),
      'end;'
    ),

    _statement: $ => choice(
      $.assignment_statement,
      $.if_statement,
      $.while_statement,
      $.repeat_statement,
      $.case_statement,
      $.procedure_call,
      $.with_statement,
      $.temporary_statement,
      $.for_statement,
      $.foreach_statement,
      $.break_statement,
      $.exit_statement,
      $.try_function,
      $.preprocessor_directive,
      $.error_statement
    ),

    try_function: $ => seq(
      'if',
      choice(
        $.try_function_call,
        $.try_method_call
      ),
      'then',
      repeat($._statement),
      optional(seq('else', repeat($._statement))),
      'end;'
    ),

    try_function_call: $ => seq(
      field('function', $.identifier),
      '(',
      optional(commaSep1($._expression)),
      ')'
    ),

    try_method_call: $ => seq(
      field('object', $._expression),
      '.',
      field('method', $.identifier),
      '(',
      optional(commaSep1($._expression)),
      ')'
    ),

    with_statement: $ => seq(
      'with',
      field('record', $.identifier),
      'do',
      repeat($._statement),
      'end;'
    ),

    temporary_statement: $ => seq(
      'temporary',
      field('variable', $.identifier),
      ';'
    ),

    variable_name: $ => $.identifier,

    assignment_statement: $ => seq(
      $.variable_name,
      ':=',
      $._expression,
      ';'
    ),

    if_statement: $ => seq(
      'if',
      $._expression,
      'then',
      repeat($._statement),
      optional(seq('else', repeat($._statement))),
      'end;'
    ),

    while_statement: $ => seq(
      'while',
      $._expression,
      'do',
      repeat($._statement),
      'end;'
    ),

    repeat_statement: $ => seq(
      'repeat',
      repeat($._statement),
      'until',
      $._expression,
      ';'
    ),

    case_statement: $ => seq(
      'case',
      $._expression,
      'of',
      repeat($.case_option),
      optional(seq('else', repeat($._statement))),
      'end;'
    ),

    case_option: $ => seq(
      $.case_value,
      ':',
      repeat($._statement)
    ),

    case_value: $ => /[^:]+/,

    procedure_call: $ => seq(
      $.procedure_name,
      '(',
      optional(commaSep1($._expression)),
      ')',
      ';'
    ),

    for_statement: $ => seq(
      'for',
      $.variable_name,
      ':=',
      $._expression,
      'to',
      $._expression,
      optional(seq('step', $._expression)),
      'do',
      repeat($._statement),
      'end;'
    ),

    foreach_statement: $ => seq(
      'foreach',
      $.variable_name,
      'in',
      $._expression,
      'do',
      repeat($._statement),
      'end;'
    ),

    break_statement: $ => seq('break', ';'),

    exit_statement: $ => seq(
      'exit',
      '(',
      optional($._expression),
      ')',
      ';'
    ),

    _expression: $ => prec(2, choice(
      $.variable_name,
      $.literal,
      $.binary_expression,
      $.unary_expression,
      $.parenthesized_expression,
      $.library_function_call,
      $.client_type,
      $.commit_behavior,
      $.data_scope,
      $.default_layout,
      $.error_type,
      $.execution_context,
      $.procedure_call,
      $.field_access,
      $.ternary_expression,
      $.boolean
    )),

    field_access: $ => seq(
      $._expression,
      '.',
      $.identifier
    ),

    library_function_call: $ => seq(
      field('function', $.library_function),
      '(',
      optional(commaSep1($._expression)),
      ')'
    ),

    library_function: $ => choice(
      // Arithmetic functions
      'Abs', 'Power', 'Random', 'Round', 'Sqrt',
      // Array functions
      'ArrayLen',
      // Base64 functions
      'Base64Convert', 'Base64Length', 'Base64ToText',
      // Bit functions
      'BitAnd', 'BitNot', 'BitOr', 'BitXor',
      // Blob functions
      'Blob2Base64String',
      // Date and time functions
      'CalcDate', 'Date2DMY', 'Date2DWY', 'DT2Date', 'DT2Time', 'CreateDateTime',
      'CurrentDateTime', 'NormalDate', 'Time', 'Today', 'WorkDate',
      // File handling functions
      'CreateTempFile', 'DownloadFromStream', 'FileClose', 'FileCopy', 'FileDelete',
      'FileExists', 'FileLen', 'FileMode', 'FileMove', 'FileOpen', 'FilePos',
      'FileRead', 'FileSeek', 'FileWrite', 'UploadIntoStream',
      // Formatting and conversion functions
      'ConvertStr', 'DateFormula2Date', 'DateFormula2Text', 'DelChr', 'DelStr',
      'Format', 'GetLastErrorText', 'InsStr', 'LowerCase', 'PadLeft', 'PadRight',
      'SelectStr', 'StrCheckSum', 'StrLen', 'StrPos', 'StrSubstNo', 'TextEncoding',
      'ToText', 'UpperCase',
      // GUID functions
      'CreateGuid', 'IsNullGuid',
      // Math functions
      'Exp', 'Log', 'Log10', 'MaxStrLen', 'Randomize',
      // Record handling functions
      'CalcFields', 'ClearMarks', 'CopyFilter', 'CurrFieldNo', 'CurrentKey',
      'Delete', 'DeleteAll', 'FieldActive', 'FieldCaption', 'FieldError', 'FieldName',
      'FieldNo', 'FindFirst', 'FindLast', 'FindSet', 'Get', 'GetFilter', 'GetFilters',
      'GetPosition', 'GetRangeMax', 'GetRangeMin', 'HasFilter', 'Init', 'Insert',
      'IsEmpty', 'Mark', 'MarkedOnly', 'Modify', 'ModifyAll', 'Next', 'ReadConsistency',
      'ReadPermission', 'RecordId', 'RecordLevelLocking', 'Reset', 'SetAscending',
      'SetAutoCalcFields', 'SetCurrentKey', 'SetFilter', 'SetPermissionFilter',
      'SetPosition', 'SetRange', 'SetRecFilter', 'TableCaption', 'TableName',
      'TestField', 'TransferFields', 'Validate', 'WritePermission',
      // System functions
      'CompanyName', 'ComputerName', 'EncryptionEnabled', 'GetLastErrorObject',
      'GlobalLanguage', 'HasValue', 'SessionId', 'Sleep', 'TestFieldError',
      'UserSecurityId', 'WindowsLanguage',
      // UI and interaction functions
      'Confirm', 'Dialog', 'GetUrl', 'HyperLink', 'Message', 'Notification',
      'Page.Run', 'Report.Run', 'Report.SaveAs', 'Report.SaveAsExcel', 'Report.SaveAsPdf',
      'Report.SaveAsWord', 'StrMenu',
      // Variant handling functions
      'Evaluate', 'MaxStrLen',
      // XML handling functions
      'XmlAttribute', 'XmlAttributeValue', 'XmlCData', 'XmlComment', 'XmlDeclaration',
      'XmlDocument', 'XmlElement', 'XmlNamespace', 'XmlProcessingInstruction', 'XmlText',
      // Other functions
      'ClearAll', 'ClearLastError', 'Codeunit.Run', 'CommitTransaction',
      'CurrentClientType', 'CurrentExecutionMode', 'CurrentTransactionType', 'Error',
      'GetRecord', 'GuiAllowed', 'HasPermission', 'IsNullGuid', 'Millisecond',
      'ModifyAll', 'RollbackTransaction', 'Run', 'RunModal', 'SetSelectionFilter',
      'TextPos', 'Variant2Bool', 'Variant2Date', 'Variant2Time',
      // Array methods
      'AddRange', 'Any', 'AsArray', 'Clear', 'Contains', 'Copy', 'Count', 'Get',
      'GetRange', 'IndexOf', 'Insert', 'LastIndexOf', 'Remove', 'RemoveAt', 'RemoveRange',
      'Reverse', 'Set', 'SetRange', 'Sort',
      // Error Collection API methods
      'AddError', 'ClearErrors', 'GetErrors', 'HasErrors',
      // Progress Windows methods
      'Open', 'Update', 'Close',
      // Action Option methods
      'ActionOption',
      // Audit Category Option methods
      'AuditCategoryOption',
      // Client Type Option methods
      'ClientTypeOption',
      // Client Type Option methods
      'ClientType'
    ),

    client_type: $ => prec(3, choice(
      'Background',
      'Desktop',
      'Management',
      'OData',
      'Phone',
      'Tablet',
      'Web',
      'WebService',
      'Windows'
    )),

    commit_behavior: $ => choice(
      'Default',
      'Implicit',
      'Explicit'
    ),

    data_scope: $ => choice(
      'Company',
      'Global',
      'SystemId'
    ),

    default_layout: $ => choice(
      'RDLC',
      'Word'
    ),

    error_type: $ => choice(
      'AccountNotFound',
      'AccountTypeNotSupported',
      'AlreadyExists',
      'AppNotFound',
      'AppValidation',
      'Arithmetic',
      'ArrayBounds',
      'AssetFileNotFound',
      'Authorization',
      'BcptTestCodeunitNotFound',
      'BcptTestFunctionNotFound',
      'BusinessCentralUpgradeRequired',
      'CannotInsertRecord',
      'CannotModifyRecord',
      'CannotUpdateNonEmptyField',
      'ConcurrencyViolation',
      'ConfigPackageExists',
      'Conflict',
      'ConnectionAttemptFailed',
      'CustomDimNotFound',
      'CustomDimValueNotFound',
      'DataverseSyncError',
      'DelegatedAuthFailed',
      'DimensionValueNotFound',
      'DotNetClassNotFound',
      'DotNetMemberNotFound',
      'DotNetMethodNotFound',
      'DuplicateKey',
      'EndOfStream',
      'EnvironmentNotFound',
      'ExportToExcelFailed',
      'ExternalSqlError',
      'FeatureNotEnabled',
      'FieldNotFound',
      'FileNotFound',
      'FilterGroupNotFound',
      'FilterNotAllowed',
      'FilterNotValid',
      'FunctionNotAllowed',
      'GenericAuthFailed',
      'GraphAuthFailed',
      'ImportTenantEncryptionKeyFailed',
      'ImportTestAutomationFailed',
      'IndexOutOfBounds',
      'InsufficientReadPermission',
      'InsufficientWritePermission',
      'Internal',
      'InvalidArgument',
      'InvalidBindingType',
      'InvalidChar',
      'InvalidClient',
      'InvalidClientType',
      'InvalidCodeunit',
      'InvalidCompany',
      'InvalidCompanyInUserSettings',
      'InvalidCredentials',
      'InvalidCurrency',
      'InvalidDateTimeFormat',
      'InvalidDateTimeFormatSpecifier',
      'InvalidDimensionValueCode',
      'InvalidEmail',
      'InvalidExtension',
      'InvalidExtensionType',
      'InvalidFieldClass',
      'InvalidFieldName',
      'InvalidFieldNumber',
      'InvalidFieldValue',
      'InvalidFilter',
      'InvalidFilterString',
      'InvalidGlobalDimension',
      'InvalidGuid',
      'InvalidImageFormat',
      'InvalidIndex',
      'InvalidJsonObject',
      'InvalidJsonPropertyName',
      'InvalidJsonToken',
      'InvalidKeyFieldType',
      'InvalidKeysetType',
      'InvalidLanguageId',
      'InvalidMediaType',
      'InvalidMethod',
      'InvalidMethodCallOnView',
      'InvalidName',
      'InvalidNestedWriteAttempt',
      'InvalidPageType',
      'InvalidPeriodFormat',
      'InvalidPropertyType',
      'InvalidRecordId',
      'InvalidReportId',
      'InvalidSecurityFilter',
      'InvalidSessionMode',
      'InvalidTableRelation',
      'InvalidTestFunctionName',
      'InvalidTestMethodName',
      'InvalidTimeZone',
      'InvalidToken',
      'InvalidType',
      'InvalidUri',
      'InvalidUriTemplate',
      'InvalidUserName',
      'InvalidVariableName',
      'InvalidXmlPortId',
      'JsonParseError',
      'JsonPropertyAlreadyExists',
      'JsonPropertyDoesNotExist',
      'JsonTokenDoesNotMatchInfo',
      'LicenseError',
      'MalformedXml',
      'MaxConcurrencyReached',
      'MissingExchangeRates',
      'MissingLicensePermission',
      'MissingRequiredParameter',
      'NavAppFileDoesNotExist',
      'NavAppInstallationFailed',
      'NavAppInvalid',
      'NavAppSymbolConflict',
      'NavAppSymbolNotFound',
      'NavAppValidationFailed',
      'NoPermissions',
      'NotAReportInDesignMode',
      'NotFound',
      'NotSupported',
      'NullValue',
      'OAuthFailed',
      'ODataFilterLimitExceeded',
      'ODataOrderByLimitExceeded',
      'ODataSelectLimitExceeded',
      'ObjectDoesNotExist',
      'ObjectNotFound',
      'OnBeforeTestRunFailed',
      'OnPremiseProductTypeNotSupported',
      'OperationAborted',
      'OperationCanceled',
      'OperationOnViewNotSupported',
      'OptimisticConcurrency',
      'OutOfBoundsException',
      'PageNotFound',
      'PlatformVersionTooLow',
      'PowerBIApiNotEnabled',
      'PrinterNotFound',
      'RecordAlreadyExists',
      'RecordNotFound',
      'ReportNotFound',
      'RequiredFieldMissing',
      'ResourceNotFound',
      'RuntimeError',
      'SQLConstraintViolation',
      'SQLDuplicateKeyError',
      'SQLInvalidOperation',
      'SQLTimeout',
      'SecurityFiltering',
      'SerializationError',
      'ServiceNotFound',
      'SessionNotFound',
      'StringExceedsMaximumLength',
      'SubscriptionDoesNotExist',
      'SyncError',
      'TableNotFound',
      'TaskSchedulerError',
      'TestCodeunitNotFound',
      'TestFunctionNotFound',
      'TestIsolationError',
      'TestPermissionError',
      'Timeout',
      'TooManyNestedCalls',
      'TooManyRecords',
      'TypeMismatch',
      'UnexpectedError',
      'UnknownProperty',
      'UnsupportedFieldTypeForBinding',
      'UnsupportedFilterToken',
      'UpgradeRequired',
      'UploadExceedsAllowedSize',
      'UserNotFound',
      'UserNotLicensed',
      'ValidationError',
      'WebhookSubscriberNotFound',
      'WebserviceUriTooLong',
      'WorkflowWebhookHandlerNotFound',
      'WrongAccountType',
      'XmlPortNotFound'
    ),

    field_class: $ => choice(
      'Normal',
      'FlowField',
      'FlowFilter'
    ),

    execution_context: $ => prec(2, choice(
      'Normal',
      'Background',
      'Unspecified',
      'OnPrem',
      'WebService',
      'WebServiceToOnPrem',
      'WebServiceToSaaS',
      'SaaS',
      'Console',
      'MobileDevice',
      'Tablet',
      'Desktop'
    )),

    action_option: $ => choice(
      'Create',
      'CreateMultiple',
      'CreatePlusNew',
      'Delete',
      'DeleteSelected',
      'Edit',
      'Invoke',
      'LookupOnly',
      'None',
      'Print',
      'PrintSelected',
      'RunObject',
      'RunObjectOnRec',
      'RunReport',
      'View'
    ),

    literal: $ => choice(
      $.number,
      $.string,
      $.boolean
    ),

    number: $ => /\d+(\.\d+)?/,
    string: $ => /'[^']*'/,
    boolean: $ => choice('true', 'false'),

    binary_expression: $ => prec.left(1, seq(
      $._expression,
      choice(
        '+', '-', '*', '/', 'div', 'mod',
        '=', '<>', '<', '<=', '>', '>=',
        'and', 'or', 'xor',
        'in', 'like',
        '&'  // String concatenation
      ),
      $._expression
    )),

    unary_expression: $ => prec(2, seq(
      choice('-', 'not'),
      $._expression
    )),

    ternary_expression: $ => prec.right(seq(
      $._expression,
      'in',
      $._expression,
      '..',
      $._expression
    )),

    parenthesized_expression: $ => seq(
      '(',
      $._expression,
      ')'
    ),

    textconst_definition: $ => seq(
      'TextConst',
      field('language', $.identifier),
      '=',
      field('value', $.string),
      ';'
    ),

    event_definition: $ => seq(
      choice('InternalEvent', 'IntegrationEvent'),
      field('name', $.identifier),
      '(',
      optional($.parameter_list),
      ')',
      ';'
    ),

    label_definition: $ => seq(
      'label',
      field('id', $.number),
      '{',
      repeat($.label_property),
      '}'
    ),

    label_property: $ => seq(
      field('name', $.identifier),
      '=',
      field('value', $.string),
      ';'
    ),

    assembly: $ => seq(
      'assembly',
      '(',
      field('assembly_name', $.string),
      ')',
      ';'
    ),

    event: $ => seq(
      'event',
      field('name', $.identifier),
      '(',
      optional($.parameter_list),
      ')',
      ';'
    ),

    _controladdin_body_element: $ => choice(
      $.property,
      $.event,
      $.procedure_definition
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
      $.number,
      repeat(seq(',', $.number)),
      ']',
      ';'
    ),

    profile_sections: $ => seq(
      'sections',
      '=',
      '[',
      $.string,
      repeat(seq(',', $.string)),
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
      $.entitlement_object,
      repeat(seq(',', $.entitlement_object)),
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
      $.string,
      repeat(seq(',', $.string)),
      ']',
      ';'
    )
  },

  // Remove this line as it's not needed




});

function commaSep1(rule) {
  return seq(rule, repeat(seq(',', rule)));
}
