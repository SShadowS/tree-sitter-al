/**
 * @file AL for Business Central
 * @author Torben Leth <sshadows@sshadows.dk>
 * @license MIT
 */

/// <reference types="tree-sitter-cli/dsl" />
// @ts-check

// Helper function for explicit identifiers
// Supports Unicode letters for international identifiers (e.g., ñ, ö, etc.)
function ident() {
  return token(/[\p{L}_][\p{L}\p{N}_]*/u);
}

// Helper function for case-insensitive keywords using RustRegex
function kw(word, precedence = null) {
  const regex = new RustRegex(`(?i)${word}`);
  return precedence !== null ? token(prec(precedence, regex)) : token(regex);
}

// Helper for contextual keywords that match with '=' included
// This disambiguates property names from variable names at the lexer level
// Note: This does NOT allow comments between the keyword and '='
function kw_with_eq(word, precedence = null) {
  const regex = new RustRegex(`(?i)${word}[\\t\\f\\r ]*=`);
  return precedence !== null ? token(prec(precedence, regex)) : token(regex);
}

// Helper for object type keywords followed by :: (Table::, Report::, etc.)
// This prevents standalone 'Table' from matching as keyword when it should be identifier
function kw_with_coloncolon(word, precedence = null) {
  const regex = new RustRegex(`(?i)${word}[\\t\\f\\r ]*::`);
  return precedence !== null ? token(prec(precedence, regex)) : token(regex);
}

// Helper for properties that can also be used as variable names
// This pattern is used when a property name conflicts with variable usage
// Only apply to properties that cause actual parsing failures in production
// IMPORTANT: This violates the normal kw() pattern but is necessary for
// certain property names that are commonly used as variable names.
// 
// Current contextual properties:
// - TableType: Used as enum variable in Opportunities.Page.al
// - Style/StyleExpr: Common variable names for UI styling
// - IsPreview: Used for preview state tracking
// 
// When to add new ones:
// 1. Only when actual parsing failures occur in production files
// 2. Property name is a common English word likely to be used as variable
// 3. Document the specific file/context where the conflict occurred

// Template functions for modification patterns (addfirst/addlast/addafter/addbefore)
function _modification_with_target_template(keyword, content_repeater) {
  return $ => seq(
    kw(keyword),
    '(',
    field('target', $._identifier_choice),
    ')',
    '{',
    repeat(content_repeater),
    '}'
  );
}

function _modification_without_target_template(keyword, content_repeater) {
  return $ => seq(
    kw(keyword),
    '{',
    repeat(content_repeater),
    '}'
  );
}

// Generic template for property definitions (PropertyName = Value;)
function _value_property_template(name_rule, value_rule) {
  return $ => seq(
    typeof name_rule === 'string' ? name_rule : name_rule($),
    '=',
    field('value', value_rule($)),
    ';'
  );
}

// Template for comparison filter expressions
function _comparison_filter_template($, operator) {
  return seq(
    operator,
    field('value', choice(
      $.string_literal,
      $.integer,
      $.date_literal,
      $.time_literal,
      $.datetime_literal,
      $._quoted_identifier,
      $.identifier
    ))
  );
}

// Generic template for preprocessor conditional blocks
function _preproc_conditional_block_template(content_rule, use_repeat1 = false) {
  const repeater = use_repeat1 ? repeat1 : repeat;
  return $ => seq(
    $.preproc_if,
    repeater(content_rule($)),
    repeat(seq(
      $.preproc_elif,
      repeater(content_rule($))
    )),
    optional(seq(
      $.preproc_else,
      repeater(content_rule($))
    )),
    $.preproc_endif
  );
}

module.exports = grammar({
  name: "al",

  word: $ => $.identifier,

  conflicts: $ => [
    [$._source_content, $.preproc_conditional_using],
    [$._source_content],
    [$.assignment_expression, $._assignable_expression],
    [$.assignment_statement, $.assignment_expression],
    [$.preproc_conditional_enum_properties, $.preproc_conditional_enum_values],
    [$.source_file],
    [$.preproc_conditional_procedures, $.preproc_conditional_mixed_content],
    [$.preproc_conditional_var_sections, $.preproc_conditional_mixed_content],
    [$.preproc_conditional_layout, $.preproc_conditional_group_content],
    [$.preproc_conditional_group_content, $.preproc_conditional_properties],
    [$.preproc_conditional_if_statement, $._statement],
    [$.preproc_conditional_statements, $.preproc_conditional_if_statement],
    [$.attribute_content, $.attribute],  // Phase 2: Allow both Rust-style and legacy attributes during migration
    [$.preproc_conditional_procedures, $.preproc_conditional_mixed_content, $.preproc_split_procedure],  // Attributes in preproc branches
    [$.preproc_conditional_procedures, $.preproc_split_procedure],  // Attributes conflict - exact
    [$._expression, $._extended_value_choice],  // Filter expression range ambiguity
    [$._literal_value, $._extended_value_choice],  // Filter expression literal range ambiguity
  ],

  externals: $ => [
    $.preproc_active_region_start,
    $.preproc_active_region_end,
    $.preproc_inactive_region_start,
    $.preproc_inactive_region_end,
    $.preproc_split_marker,
    $.preproc_continuation_marker,
    $.error_sentinel,
    $.preproc_var_terminator,
    $.attribute_for_variable,
    $.attribute_for_procedure,
    $.preproc_var_continuation,  // Signals #if contains ONLY variables, forces var_section continuation
    $._pragma_var_continuation,  // Signals pragma followed by variable, continue var_section (hidden)
    $._attribute_var_continuation  // Signals attribute followed by variable, continue var_section (hidden)
  ],

  // Extras: whitespace, comments, and ignorable preprocessor directives
  // #if/#else/#elif/#endif are literals (structural)
  // #region/#pragma/#endregion are regex patterns (structurally insignificant)
  extras: $ => [new RustRegex('\\s'), $.comment, $.multiline_comment, $.pragma, $.preproc_region, $.preproc_endregion, new RustRegex('\\uFEFF')],

  rules: {
    source_file: $ => choice(
      // Preprocessor-wrapped source file with optional pragmas (higher precedence)
      prec(2, seq(
        repeat($.pragma),  // Allow pragmas before preprocessor
        $.preprocessor_file_conditional,
        repeat($.pragma)   // Allow pragmas after preprocessor
      )),
      // Standard source file structure
      seq(
        repeat($.pragma),  // Allow pragmas at the beginning
        optional($.namespace_declaration),
        repeat(choice($.using_statement, $.preproc_conditional_using)),
        repeat(choice($._object, $.pragma, $.preprocessor_file_conditional))
      )
    ),

    preprocessor_file_conditional: $ => seq(
      field('condition', $.preproc_if),
      field('consequence', $._source_content),
      optional(field('alternative', seq(
        $.preproc_else,
        $._source_content
      ))),
      $.preproc_endif
    ),

    _source_content: $ => choice(
      // Case 1: Has at least one object or pragma
      seq(
        repeat($.pragma),
        optional($.namespace_declaration),
        repeat(choice($.using_statement, $.preproc_conditional_using)),
        repeat1(choice($._object, $.pragma))
      ),
      // Case 2: Only has namespace declaration (no objects)
      seq(
        repeat($.pragma),
        $.namespace_declaration,
        repeat(choice($.using_statement, $.preproc_conditional_using))
      )
    ),

    _object: $ => choice(
      $.table_declaration,
      $.tableextension_declaration,
      $.codeunit_declaration,
      $.pageextension_declaration,
      $.page_declaration,
      $.pagecustomization_declaration,
      $.profile_declaration,
      $.profileextension_declaration,
      $.reportextension_declaration,
      $.query_declaration,
      $.enum_declaration,
      $.enumextension_declaration, 
      $.preproc_conditional_enum_declaration,
      $.preproc_conditional_codeunit_declaration,
      $.xmlport_declaration,
      $.interface_declaration,
      $.dotnet_declaration,
      $.report_declaration,
      $.permissionset_declaration,
      $.permissionsetextension_declaration,
      $.controladdin_declaration,
      $.entitlement_declaration,
      $.preproc_conditional_object_declaration
    ),

    // Handle object declarations split by preprocessor
    preproc_conditional_object_declaration: $ => seq(
      $.preproc_if,
      $._conditional_object_header,
      $.preproc_else,
      $._conditional_object_header,
      $.preproc_endif,
      '{',
      repeat($._object_body_element),
      '}'
    ),

    _conditional_object_header: $ => prec(2, seq(
      choice(
        kw('codeunit'),
        kw('table'),
        kw('page'),
        kw('report'),
        kw('query'),
        kw('xmlport')
      ),
      field('object_id', $.integer),
      field('object_name', $._identifier_choice),
      optional($.implements_clause)
    )),

    _object_body_element: $ => choice(
      $.attribute_item,
      $.var_section,
      $.preproc_conditional_var_sections,
      $.procedure,
      $.trigger_declaration,
      $.pragma,
      $.preproc_region,
      $.preproc_endregion,
      $.comment,
      $.multiline_comment
    ),

    namespace_declaration: $ => seq(
      kw('namespace'),
      field('name', $.namespace_name),
      ';'
    ),

    namespace_name: $ => prec.left(seq(
      $.identifier,
      repeat(seq('.', $.identifier))
    )),

    using_statement: $ => seq(
      kw('using'),
      field('namespace', $.namespace_name),
      ';'
    ),
    
    xmlport_declaration: $ => seq(
      kw('xmlport'),
      $._object_header_base,
      '{',
      repeat($._xmlport_element),
      '}'
    ),
    
    _xmlport_element: $ => choice(
      $.attribute_item,
      $.xmlport_schema_element,
      $.var_section,
      $.preproc_conditional_var_sections,
      $.procedure,
      $.preproc_split_procedure,
      $.preproc_procedure_body_split,
      $.trigger_declaration,
      $._xmlport_properties,
      $.preproc_conditional_xmlport_properties,
      $.requestpage_section  // Support requestpage in XMLports
    ),
    
    // XMLPort specific properties
    direction_value: $ => choice(
      kw('export'),
      kw('import'),
      kw('both')
    ),

    direction_property: _value_property_template($ => kw('Direction'), $ => $.direction_value),
    
    format_value: $ => choice(
      kw('xml', 1),
      kw('variable', 1),
      kw('variabletext', 1),
      kw('fixed', 1),
      kw('fixedtext', 1)
    ),

    format_property: _value_property_template($ => kw('Format', 10), $ => $.format_value),

    field_delimiter_property: _value_property_template($ => kw('FieldDelimiter'), $ => $.string_literal),
    
    field_separator_property: _value_property_template($ => kw('FieldSeparator'), $ => $.string_literal),

    default_fields_validation_property: $ => seq(kw('DefaultFieldsValidation'), $._boolean_property_template),

    
    xmlport_schema_element: $ => seq(
      kw('schema'),
      '{',
      repeat(choice(
        $.xmlport_table_element,
        $.preproc_conditional_xmlport_elements
      )),
      '}'
    ),
    
    xmlport_table_element: $ => seq(
      choice(
        kw('tableelement'),
        kw('fieldelement'),
        kw('textelement')
      ),
      '(',
      field('name', $._identifier_choice),
      optional(seq(
        ';',
        field('source_table', choice(
          $.identifier, 
          $._quoted_identifier,
          $.field_access,  // Support Table."Field" syntax
          $.member_expression  // Support Table.Field syntax (unquoted)
        ))
      )),
      ')',
      '{',
      repeat(choice(
        $.xmlport_table_property,
        $.xmlport_table_element,  // Allow nesting of elements
        $.xmlport_field_attribute,
        $.xmlport_text_attribute,
        $.named_trigger,  // Allow triggers in XMLport table elements
        $.trigger_declaration,  // Also support regular trigger declarations
        $.preproc_conditional_xmlport_elements  // Support preprocessor conditionals
      )),
      '}'
    ),
    
    xmlport_table_property: $ => choice(
      $._universal_properties,    // caption, application_area, tool_tip, tool_tip_ml
      
      // XMLPort table-specific properties
      $.auto_replace_property,
      $.auto_save_property, 
      $.auto_update_property,
      $.calc_fields_property,  // Add CalcFields property
      $.link_fields_property,
      $.external_schema_property,
      $.link_table_property,
      $.link_table_force_insert_property,
      $.occurrence_property,  // Add support for Occurrence property
      $.max_occurs_property,
      $.min_occurs_property,
      $.namespace_prefix_property,
      $.unbound_property,
      $.xml_name_property,
      $.request_filter_fields_property,
      $.request_filter_heading_property,
      $.request_filter_heading_ml_property,
      $.use_temporary_property,
      $.source_table_view_property,  // Add SourceTableView property
      $.field_validate_property,
      $.text_type_property,  // Add TextType property for textattribute
    ),
    
    xmlport_field_attribute: $ => seq(
      kw('fieldattribute'),
      '(',
      field('attribute_name', $._identifier_choice),
      ';',
      field('source_field', choice(
        $.identifier,
        $.field_access,  // Support Table."Field" syntax
        $.member_expression  // Support Table.Field syntax (unquoted)
      )),
      ')',
      '{',
      repeat(choice(
        $.xmlport_table_property,
        $.trigger_declaration  // Support triggers in fieldattribute
      )),
      '}'
    ),
    
    xmlport_text_attribute: $ => seq(
      kw('textattribute'),
      '(',
      field('attribute_name', $._identifier_choice),
      ')',
      '{',
      repeat(choice(
        $.xmlport_table_property,
        $.trigger_declaration  // Support triggers in textattribute
      )),
      '}'
    ),
    
    // 11. Unbound Property
    unbound_property: $ => seq(kw('Unbound'), $._boolean_property_template),
    
    // 12. XmlName Property
    xml_name_property: $ => seq(kw('XmlName'), $._string_property_template),
    
    // 13. MovedFrom Property
    moved_from_property: $ => seq(kw('MovedFrom'), $._string_property_template),
    
    // 14. MovedTo Property
    moved_to_property: $ => seq(kw('MovedTo'), $._string_property_template),
    
    // 15. LinkedInTransaction Property
    linked_in_transaction_property: $ => seq(kw('LinkedInTransaction'), $._boolean_property_template),
    
    // 16. LinkedObject Property
    linked_object_property: $ => seq(kw('LinkedObject'), $._string_property_template),
    
    // 17. RequestFilterFields Property
    request_filter_fields_value: $ => $._identifier_choice_list,
    
    request_filter_fields_property: _value_property_template(
      $ => kw('requestfilterfields'),
      $ => $.request_filter_fields_value
    ),
    
    // 18. RequestFilterHeading Property
    request_filter_heading_property: $ => seq(
      kw('requestfilterheading'),
      $._string_property_template
    ),
    
    // 19. RequestFilterHeadingML Property
    request_filter_heading_ml_property: $ => seq(
      'RequestFilterHeadingML',
      $._ml_property_template
    ),
    
    // 6. LinkTable Property
    link_table_property: $ => seq(
      kw('LinkTable'),
      $._identifier_property_template
    ),
    
    // 7. LinkTableForceInsert Property
    link_table_force_insert_property: $ => seq(kw('LinkTableForceInsert'), $._boolean_property_template),
    
    // 8. MaxOccurs Property
    max_occurs_value: $ => choice(
      $.integer,
      kw('unbounded'),
      kw('once')
    ),
    
    max_occurs_property: _value_property_template($ => kw('MaxOccurs'), $ => $.max_occurs_value),
    
    // 9. MinOccurs Property
    min_occurs_value: $ => choice(
      $.integer,
      kw('once'),
      kw('zero')
    ),
    
    min_occurs_property: _value_property_template($ => kw('MinOccurs'), $ => $.min_occurs_value),
    
    // 10. FieldValidate Property
    field_validate_property: $ => seq(
      kw('FieldValidate'),
      '=',
      field('value', choice(
        kw('yes'),
        kw('no'),
        $.boolean
      )),
      ';'
    ),
    
    // Occurrence Property (for XMLPort field attributes)
    occurrence_value: $ => choice(
      kw('Required'),
      kw('Optional')
    ),
    
    occurrence_property: _value_property_template($ => kw('Occurrence'), $ => $.occurrence_value),
    
    // TextType Property (for XMLPort text attributes)
    text_type_value: $ => choice(
      kw('Text'),
      kw('BigText')
    ),
    
    text_type_property: _value_property_template($ => kw('TextType'), $ => $.text_type_value),
    
    // 10. NamespacePrefix Property
    namespace_prefix_property: $ => seq(
      'NamespacePrefix',
      $._string_property_template
    ),
    
    // 5. ExternalSchema
    external_schema_property: $ => seq(
      'ExternalSchema',
      $._string_property_template
    ),
    
    // First 5 LOW PRIORITY properties
    
    // 1. AutoReplace
    auto_replace_property: $ => seq(
      kw('AutoReplace'),
      $._boolean_property_template
    ),
    
    // 2. AutoSave
    auto_save_property: $ => seq(
      kw('AutoSave'),
      $._boolean_property_template
    ),
    
    // 3. AutoUpdate
    auto_update_property: $ => seq(
      kw('AutoUpdate'),
      $._boolean_property_template
    ),
    
    // 4. LinkFields
    link_fields_property: $ => seq(
      kw('LinkFields'),
      '=',
      field('value', $.link_fields_value),
      ';'
    ),
    
    link_fields_value: $ => seq(
      $.field_mapping,
      repeat(seq(',', $.field_mapping))
    ),
    
    field_mapping: $ => seq(
      field('source_field', $._identifier_choice),
      '=',
      field('target_field', choice(
        $.identifier, 
        $._quoted_identifier,
        // Support FIELD("FieldName") syntax
        seq(
          $._field_keyword,
          '(',
          $._flexible_identifier_choice,
          ')'
        )
      ))
    ),

    enum_declaration: $ => seq(
      kw('enum'),
      $._object_header_base,
      optional($.implements_clause),
      '{',
      repeat(choice(
        $._enum_properties,
        seq(repeat($.attribute_item), $.enum_value_declaration),
        $.preproc_conditional_enum_content  // Support mixed content in conditional blocks (properties and/or values)
      )),
      '}'
    ),

    enumextension_declaration: $ => seq(
      kw('enumextension'),
      $._object_header_base,
      kw('extends'),
      field('base_object', $._identifier_choice),
      '{',
      repeat(choice(
        seq(repeat($.attribute_item), $.enum_value_declaration),
        $.preproc_if,
        $.preproc_else,
        $.preproc_endif,
        $.preproc_region,
        $.preproc_endregion
      )),
      '}'
    ),

    preproc_conditional_codeunit_declaration: $ => prec(1, seq(
      $.preproc_if,
      optional($.pragma),
      field('consequence', seq(
        kw('codeunit'),
        $._object_header_base,
        optional($.implements_clause)
      )),
      optional($.pragma),
      $.preproc_else,
      field('alternative', seq(
        kw('codeunit'),
        $._object_header_base,
        optional($.implements_clause)
      )),
      $.preproc_endif,
      '{',
      repeat(choice(
        $.attribute_item,
        prec(4, $._codeunit_properties),
        $.preproc_conditional_object_properties,
        $.var_section,
        $.preproc_conditional_var_sections,
        $.procedure,
        $.onrun_trigger,
        $.trigger_declaration,
        $.preproc_conditional_procedures,
        $.pragma,
        $.preproc_region,
        $.preproc_endregion
      )),
      '}'
    )),

    preproc_conditional_enum_declaration: $ => prec(1, seq(
      $.preproc_if,
      optional($.pragma),
      field('consequence', seq(
        kw('enum'),
        $._object_header_base,
        optional($.implements_clause)
      )),
      optional($.pragma),
      $.preproc_else,
      field('alternative', seq(
        kw('enum'),
        $._object_header_base,
        optional($.implements_clause)
      )),
      $.preproc_endif,
      '{',
      repeat(choice(
        $._enum_properties, 
        $.enum_value_declaration,
        $.preproc_conditional_enum_content  // Allow mixed content blocks (properties and values)
      )),
      '}'
    )),

    enum_value_declaration: $ => seq(
      kw('value'),
      '(',
      field('value_id', $.integer),
      ';',
      field('value_name', choice(
        token(prec(10, '""')),  // High precedence for empty string in enum context
        $._quoted_identifier, 
        $.identifier, 
        $.string_literal
      )), // Allow string literal for value name
      ')',
      '{',
      repeat(choice(
        $._enum_properties, // Use centralized enum properties
        $.preproc_conditional_enum_properties  // Allow preprocessor conditionals
      )),
      '}'
    ),

    query_declaration: $ => seq(
      kw('query'),
      $._object_header_base,
      '{',
      repeat($._query_element),
      '}'
    ),

    _query_element: $ => choice(
      $.attribute_item,
      $._universal_properties,       // caption, description, application_area, etc.
      $._query_properties,           // query-specific properties
      $.elements_section,            // dataitem and column definitions
      $.property_list,               // generic property container
      $.preproc_conditional_query_properties,
      $.trigger_declaration,         // triggers like OnBeforeOpen
      $.procedure,
      $.preproc_split_procedure,
      $.preproc_procedure_body_split,
      $.var_section,                 // var section for global variables
      $.preproc_conditional_var_sections,  // conditional var sections

      // Region directives for code organization
      $.preproc_region,
      $.preproc_endregion
    ),

    about_title_property: $ => seq(
      kw('abouttitle'),
      $._about_template
    ),

    about_text_property: $ => seq(
      kw('abouttext'),
      $._about_template
    ),

    // CONSOLIDATED: page_about_text_property → about_text_property

    // Generic multi-language version of AboutText
    about_text_ml_property: $ => seq(
      kw('AboutTextML'),
      $._ml_property_template
    ),

    // CONSOLIDATED: page_about_title_property → about_title_property

    // Generic multi-language version of AboutTitle
    about_title_ml_property: $ => seq(
      kw('AboutTitleML'),
      $._ml_property_template
    ),

    // Delete Allowed Property
    delete_allowed_property: $ => seq(kw('DeleteAllowed'), $._boolean_property_template),

    // Insert Allowed Property
    insert_allowed_property: $ => seq(kw('InsertAllowed'), $._boolean_property_template),

    // Modify Allowed Property
    modify_allowed_property: $ => seq(kw('ModifyAllowed'), $._boolean_property_template),

    // Source Table Temporary Property
    source_table_temporary_property: $ => seq(kw('SourceTableTemporary'), $._boolean_property_template),

    // Use Temporary Property
    use_temporary_property: $ => seq(kw('usetemporary'), $._boolean_property_template),

    // Phase 2A - Medium Priority Boolean Page Properties
    analysis_mode_enabled_property: $ => seq(kw('AnalysisModeEnabled'), $._boolean_property_template),

    auto_split_key_property: $ => seq('AutoSplitKey', $._boolean_property_template),

    change_tracking_allowed_property: $ => seq('ChangeTrackingAllowed', $._boolean_property_template),

    delayed_insert_property: $ => seq('DelayedInsert', $._boolean_property_template),

    links_allowed_property: $ => seq('LinksAllowed', $._boolean_property_template),

    multiple_new_lines_property: $ => seq(
      'MultipleNewLines',
      $._boolean_property_template
    ),

    populate_all_fields_property: $ => seq(
      'PopulateAllFields',
      $._boolean_property_template
    ),

    // Phase 2B - Medium Priority Complex Page Properties
    // Uses kw_with_eq to distinguish property from variable name
    data_caption_expression_property: $ => seq(
      alias(kw_with_eq('datacaptionexpression'), 'DataCaptionExpression'),
      field('value', $._expression),
      ';'
    ),

    instructional_text_property: $ => seq(
      'InstructionalText',
      '=',
      field('value', $.string_literal),
      repeat(seq(
        ',',
        choice(
          seq(
            kw('locked'),
            '=',
            $.boolean
          ),
          seq(
            kw('comment'),
            '=',
            $.string_literal
          )
        )
      )),
      ';'
    ),

    instructional_text_ml_property: $ => seq(
      'InstructionalTextML',
      $._ml_property_template
    ),

    // Phase 4A - High + Medium Priority Page Properties
    // Removed: access_by_permission_page_property - now using universal access_by_permission_property

    prompt_mode_property: $ => seq(
      'PromptMode',
      $._auto_always_never_enum_template
    ),

    refresh_on_activate_property: $ => seq(
      'RefreshOnActivate',
      $._boolean_property_template
    ),

    save_values_property: $ => seq(
      'SaveValues',
      $._boolean_property_template
    ),

    show_filter_property: $ => seq(
      alias(kw_with_eq('showfilter'), 'ShowFilter'),
      field('value', $.boolean),
      ';'
    ),

    additional_search_terms_property: $ => seq(
      kw('AdditionalSearchTerms'),
      '=',
      field('value', $.string_literal),
      optional(seq(',', kw('Locked'), '=', field('locked', $.boolean))),
      ';'
    ),

    additional_search_terms_ml_property: $ => seq(
      'AdditionalSearchTermsML',
      $._ml_property_template
    ),

    entity_caption_property: $ => seq(
      kw('entitycaption'),
      $._caption_string_template
    ),

    entity_caption_ml_property: $ => seq(
      kw('entitycaptionml'),
      $._ml_property_template
    ),

    entity_name_property: $ => seq(
      kw('entityname'),
      $._name_property_template
    ),

    entity_set_caption_property: $ => seq(
      kw('entitysetcaption'),
      $._caption_string_template
    ),

    entity_set_caption_ml_property: $ => seq(
      kw('entitysetcaptionml'),
      $._ml_property_template
    ),

    entity_set_name_property: $ => seq(
      kw('entitysetname'),
      $._name_property_template
    ),

    api_version_property: $ => seq(
      kw_with_eq('apiversion'),
      field('value', $.string_literal),
      ';'
    ),

    order_by_property: _value_property_template(
      $ => kw('orderby'),
      $ => $.order_by_list
    ),

    order_by_list: $ => seq(
      $.order_by_item,
      repeat(seq(',', $.order_by_item))
    ),

    order_by_item: $ => seq(
      choice(kw('ascending'), kw('descending')),
      '(',
      $._identifier_choice,
      repeat(seq(',', $._identifier_choice)),
      ')'
    ),

    multiplicity_property: $ => seq(
      kw('multiplicity'),
      $._multiplicity_enum_template
    ),

    api_group_property: $ => seq(
      kw('apigroup'),
      $._string_property_template
    ),

    api_publisher_property: $ => seq(
      kw('apipublisher'),
      $._string_property_template
    ),

    // api_version_property: duplicate definition removed - using the case-insensitive version above

    context_sensitive_help_page_property: $ => seq(
      kw('contextsensitivehelppage'),
      $._string_property_template
    ),

    help_link_property: $ => seq(
      alias(kw_with_eq('helplink'), 'HelpLink'),
      field('value', $.string_literal),
      ';'
    ),

    is_preview_property: $ => seq(
      alias(kw_with_eq('ispreview'), 'IsPreview'),
      field('value', $.boolean),
      ';'
    ),
    
    odata_key_fields_value: $ => $._identifier_choice_list,

    odata_key_fields_property: _value_property_template(
      $ => kw('ODataKeyFields'),
      $ => $.odata_key_fields_value
    ),

    query_category_property: $ => seq(
      kw('querycategory'),
      $._string_property_template
    ),

    data_access_intent_property: $ => seq(
      kw('dataaccessintent'),
      $._access_level_enum_template
    ),

    query_type_property: $ => seq(
      kw('querytype'),
      $._query_type_enum_template
    ),

    read_state_property: $ => seq(
      kw('ReadState'),
      '=',
      field('value', $.identifier),
      ';'
    ),
    
    top_number_of_rows_property: $ => seq(
      kw('TopNumberOfRows'),
      '=',
      field('value', $.integer),
      ';'
    ),

    // SourceTableView components
    field_reference: $ => prec(5, choice(
      $.string_literal,
      $.identifier,
      $._quoted_identifier
    )),
    
    field_reference_list: $ => seq(
      $.field_reference,
      repeat(seq(',', $.field_reference))
    ),
    
    sorting_clause: $ => choice(
      // Standard table sorting syntax: SORTING(field1, field2)
      seq(
        kw('sorting'),
        '(',
        field('fields', $.field_reference_list),
        ')'
      ),
      // View OrderBy syntax: ascending(field) or descending(field)
      $.sorting_element
    ),

    sorting_element: $ => prec(3, seq(
      field('sort_order', alias($.identifier, $.sort_order)),
      '(',
      field('field', $._identifier_choice),
      ')'
    )),
    
    order_direction: $ => choice(
      kw('ascending'),
      kw('descending')
    ),
    
    order_clause: $ => seq(
      kw('order'),
      '(',
      field('direction', $.order_direction),
      ')'
    ),
    
    filter_operator: $ => choice('=', '<>', '<=', '>=', '<', '>', 'IN'),
    
    filter_value: $ => choice(
      $.string_literal,
      $.integer,
      $.const_expression,
      $.filter_expression_function
    ),
    
    filter_expression_function: $ => seq(
      $._filter_keyword,
      '(',
      field('value', $._filter_value),
      ')'
    ),

    filter_or_expression: $ => prec.left(8, seq(
      $._filter_base_value,
      repeat1(seq(
        '|',
        $._filter_base_value
      ))
    )),

    filter_and_expression: $ => prec.left(9, seq(
      $._filter_base_value,
      repeat1(seq(
        '&',
        $._filter_base_value
      ))
    )),

    filter_not_equal_expression: $ => seq(
      '<>',
      field('value', choice(
        $.string_literal,
        $.integer,
        $.date_literal,
        $.time_literal,
        $.datetime_literal,
        $._quoted_identifier,
        $.identifier
      ))
    ),

    filter_equal_expression: $ => seq(
      '=',
      field('value', choice(
        $.string_literal,
        $.integer,
        $.date_literal,
        $.time_literal,
        $.datetime_literal,
        $._quoted_identifier,
        $.identifier,
        $.object_type_qualified_reference  // Support for Report::"Report Name" patterns
      ))
    ),

    filter_range_expression: $ => seq(
      optional(field('start', $._extended_value_choice)),
      '..',
      optional(field('end', $._extended_value_choice))
    ),

    // Comparison operators in filter expressions
    filter_less_than_expression: $ => _comparison_filter_template($, '<'),
    filter_greater_than_expression: $ => _comparison_filter_template($, '>'),
    filter_less_than_or_equal_expression: $ => _comparison_filter_template($, '<='),
    filter_greater_than_or_equal_expression: $ => _comparison_filter_template($, '>='),

    // Unified filter value pattern - used in all FILTER() contexts
    _filter_base_value: $ => choice(
      $.filter_not_equal_expression,
      $.filter_equal_expression,
      $.filter_less_than_expression,
      $.filter_greater_than_expression,
      $.filter_less_than_or_equal_expression,
      $.filter_greater_than_or_equal_expression,
      $.filter_range_expression,
      $.qualified_enum_value,  // Support for EnumType::Value patterns
      $.identifier,
      $._quoted_identifier,
      $.integer,
      $.boolean,  // Support for filter(true) and filter(false)
      $.string_literal,
      $.date_literal,
      $.time_literal,
      $.datetime_literal,
      $.object_type_qualified_reference  // Support for Report::"Report Name" patterns
    ),

    _filter_value: $ => choice(
      $.filter_and_expression,
      $.filter_or_expression,
      $._filter_base_value
    ),

    const_expression: $ => seq(
      kw('const'),
      '(',
      optional(choice(
        $._const_value,
        $.boolean
      )),
      ')'
    ),
    
    
    // Ensure at least one clause is present to avoid empty string match
    source_table_view_value: $ => choice(
      // At least sorting clause present
      seq(
        $.sorting_clause,
        optional($.order_clause),
        optional($.where_clause)
      ),
      // At least order clause present
      seq(
        optional($.sorting_clause),
        $.order_clause,
        optional($.where_clause)
      ),
      // At least where clause present
      seq(
        optional($.sorting_clause),
        optional($.order_clause),
        $.where_clause
      )
    ),
    
    source_table_view_property: $ => prec(8, seq(
      kw('sourcetableview'),
      '=',
      field('value', $.source_table_view_value),
      ';'
    )),

    elements_section: $ => seq(
      kw('elements'),
      '{',
      repeat($.dataitem_section),
      '}'
    ),

    dataitem_section: $ => seq(
      kw('dataitem'),
      '(',
      field('name', $._identifier_choice),
      ';',
      field('table_name', choice(
        $._identifier_choice,
        $.qualified_table_reference
      )),
      ')',
      '{',
      repeat($._dataitem_content_element),
      '}'
    ),

    _dataitem_content_element: $ => choice(
      $.column_section,
      $.dataitem_section,
      $.data_item_link_property,
      $.data_item_table_filter_property,
      $.sql_join_type_property,
      $.filters_property,
      $.filter_section,
      $.preproc_conditional_dataitem_content
    ),

    preproc_conditional_dataitem_content: $ => seq(
      $.preproc_if,
      repeat($._dataitem_content_element),
      optional(seq(
        $.preproc_else,
        repeat($._dataitem_content_element)
      )),
      $.preproc_endif
    ),

    data_item_link_property: _value_property_template(
      $ => kw('DataItemLink'),
      $ => $.data_item_link_value
    ),

    data_item_table_filter_property: _value_property_template(
      $ => kw('dataitemtablefilter'),
      $ => $.table_filter_value
    ),

    table_filter_value: $ => seq(
      field('field', $._identifier_choice),
      '=',
      field('filter', choice(
        $.string_literal,
        $._quoted_identifier,
        $.const_expression,
        $.simple_filter_expression
      )),
      repeat(seq(
        ',',
        field('field', $._identifier_choice),
        '=',
        field('filter', choice(
          $.string_literal,
          $._quoted_identifier,
          $.const_expression,
          $.simple_filter_expression
        ))
      ))
    ),

    simple_filter_expression: $ => seq(
      kw('filter'),
      '(',
      $._filter_value_simple,
      ')'
    ),

    _filter_value_simple: $ => choice(
      $.string_literal,
      $.identifier,
      $._quoted_identifier,
      $.integer,
      $.boolean,
      $.date_literal,
      $.time_literal,
      $.datetime_literal,
      // Support for comparison operators (including equals)
      seq(
        choice('=', '>', '<', '>=', '<=', '<>'),
        choice($.integer, $.identifier, $._quoted_identifier, $.string_literal, $.boolean, $.date_literal, $.time_literal, $.datetime_literal)
      ),
      // Support for comparison operators with pipe-separated alternatives
      seq(
        choice('=', '>', '<', '>=', '<=', '<>'),
        choice($.integer, $.identifier, $._quoted_identifier, $.string_literal, $.boolean, $.date_literal, $.time_literal, $.datetime_literal),
        repeat1(seq(
          '|',
          choice($.string_literal, $.identifier, $._quoted_identifier, $.integer, $.boolean, $.date_literal, $.time_literal, $.datetime_literal)
        ))
      ),
      // Support for pipe-separated values
      seq(
        choice($.string_literal, $.identifier, $._quoted_identifier),
        repeat1(seq(
          '|',
          choice($.string_literal, $.identifier, $._quoted_identifier)
        ))
      ),
      // Support for range expressions
      $.filter_range_expression
    ),

    data_item_link_value: $ => seq(
      field('field', $._identifier_choice),
      '=',
      choice(
        // Traditional dot syntax: RecordRef."Field Name"
        seq(
          field('linked_field', $._identifier_choice),
          '.',
          field('linked_field_name', $._identifier_choice)
        ),
        // FIELD() function syntax: FIELD("Field Name")
        seq(
          $._field_keyword,
          '(',
          field('linked_field_name', $._identifier_choice),
          ')'
        )
      ),
      repeat(seq(
        ',',
        field('field', $._identifier_choice),
        '=',
        choice(
          // Traditional dot syntax: RecordRef."Field Name"
          seq(
            field('linked_field', $._identifier_choice),
            '.',
            field('linked_field_name', $._identifier_choice)
          ),
          // FIELD() function syntax: FIELD("Field Name")
          seq(
            $._field_keyword,
            '(',
            field('linked_field_name', $._identifier_choice),
            ')'
          )
        )
      ))
    ),

    sql_join_type_property: $ => seq(
      kw('sqljointype'),
      $._sql_join_type_enum_template
    ),

    column_section: $ => seq(
      kw('column'),
      '(',
      choice(
        // Standard column: column(name; field_name)
        seq(
          field('name', $._identifier_choice),
          ';',
          field('field_name', $._identifier_choice)
        ),
        // Computed column: column(name) - no field reference
        field('name', $._identifier_choice)
      ),
      ')',
      '{',
      repeat(choice(
        $.column_filter_property,     // Add ColumnFilter property
        $._report_column_properties,  // Use centralized column properties
        $.generic_property            // Support generic properties like Method = Sum
      )),
      '}'
    ),

    column_filter_property: $ => seq(
      kw('ColumnFilter'),
      '=',
      field('field_name', $._identifier_choice),
      '=',
      choice(
        // filter(expression) pattern
        seq(
          kw('filter'),
          '(',
          field('filter_expression', $._filter_value),
          ')'
        ),
        // const(value) pattern
        seq(
          kw('const'),
          '(',
          field('const_value', choice(
            $.boolean,
            $.integer,
            $.string_literal,
            $._identifier_choice
          )),
          ')'
        )
      ),
      ';'
    ),

    filter_section: $ => seq(
      kw('filter'),
      '(',
      field('name', $._identifier_choice),
      ';',
      field('field_name', $._identifier_choice),
      ')',
      '{',
      repeat(choice(
        $.column_filter_property,  // Add specific ColumnFilter property
        $._universal_properties,  // Allow universal properties like Caption, etc.
        $.generic_property        // Generic property fallback
      )),
      '}'
    ),

    // Generic property rule for simple property assignments like Method = Sum
    generic_property: $ => prec(10, seq(
      field('name', $.identifier),
      '=',
      field('value', choice(
        $.identifier,
        $._quoted_identifier,
        $.string_literal,
        $.integer,
        $.boolean
      )),
      ';'
    )),

    pageextension_declaration: $ => seq(
      kw('pageextension'),
      $._object_header_base,
      kw('extends'),
      field('base_object', $._identifier_choice),
      '{',
      repeat($._pageextension_element),
      '}'
    ),

    _pageextension_element: $ => choice(
      $.attribute_item,
      $.layout_section,
      $.actions_section,
      $.views_section,  // Support views section in page extensions
      $._page_properties,     // Centralized page properties
      $.var_section,
      $.preproc_conditional_var_sections,
      $.trigger_declaration,
      $.procedure,
      $.preproc_split_procedure,
      $.preproc_procedure_body_split,
      $.preproc_region,
      $.preproc_endregion,
      $.pragma
    ),

    tableextension_declaration: $ => seq(
      kw('tableextension'),
      $._object_header_base,
      kw('extends'),
      field('base_object', $._identifier_choice),
      '{',
      repeat($._tableextension_element),
      '}'
    ),

    _tableextension_element: $ => choice(
      $.attribute_item,
      $.fields,
      $.modify_field_declaration,  // Add direct modify field support
      $.keys,
      $.fieldgroups_section,
      $.procedure,
      $.preproc_split_procedure,
      $.preproc_procedure_body_split,
      $.trigger_declaration,
      $.var_section,
      $.preproc_conditional_procedures,  // Support preprocessor conditional procedures
      $._table_properties     // Centralized table properties
    ),

    actions_section: $ => seq(
      choice('actions', 'Actions', 'ACTIONS'),
      '{',
      repeat(choice(
        $._action_element,
        $._action_group,
        $.action_group_section,
        $.area_action_section,
        $.preproc_conditional_actions
      )),
      '}'
    ),

    area_action_section: $ => seq(
      kw('area'),
      '(',
      field('type', choice(
        kw('processing'),
        kw('reporting'),
        kw('navigation'),
        kw('creation'),
        kw('promoted'),
        kw('systemactions'),
        kw('sections'),
        kw('embedding'),
        kw('promptguide'),
        kw('prompting')
      )),
      ')',
      '{',
      repeat(choice(
        $.tool_tip_property,  // Allow ToolTip property directly in area sections
        $._action_element,
        $.action_group_section,
        $.separator_action,
        $.preproc_conditional_actions
      )),
      '}'
    ),

    action_group_section: $ => seq(
      kw('group'),
      '(',
      field('name', $._identifier_choice),
      ')',
      '{',
      repeat(choice(
        $.action_declaration,
        $.actionref_declaration,
        $.customaction_declaration,  // Add support for customaction in groups
        $.action_group_section,
        $._action_property,
        $.separator_action,
        $.empty_statement,
        $.preproc_conditional_actions  // Add support for preprocessor conditionals in action groups
      )),
      '}'
    ),
    
    // Add separator action rule
    separator_action: $ => seq(
      kw('separator'),
      '(',
      field('name', $._identifier_choice),
      ')',
      '{',
      repeat($._action_property),
      '}'
    ),

    _action_group: $ => choice(
      $.addfirst_action_group,
      $.addlast_action_group,
      $.addafter_action_group,
      $.addbefore_action_group,
      $.modify_action_group,
      $.modify_action
    ),

    addfirst_action_group: $ => _modification_with_target_template(
      'addfirst',
      choice(
        $._action_element,
        $.action_group_section,
        $.separator_action,
        $.preproc_conditional_actions
      )
    )($),

    addlast_action_group: $ => _modification_with_target_template(
      'addlast',
      choice(
        $._action_element,
        $.action_group_section,
        $.separator_action,
        $.preproc_conditional_actions
      )
    )($),

    addafter_action_group: $ => _modification_with_target_template(
      'addafter',
      choice(
        $._action_element,
        $.action_group_section,
        $.separator_action,
        $.preproc_conditional_actions
      )
    )($),

    addbefore_action_group: $ => _modification_with_target_template(
      'addbefore',
      choice(
        $._action_element,
        $.action_group_section,
        $.separator_action,
        $.preproc_conditional_actions
      )
    )($),

    modify_action_group: $ => seq(
      kw('modify'),
      '(',
      field('target', $._identifier_choice),
      ')',
      '{',
      repeat(choice(
        $._action_element,
        $.action_group_section,
        $.separator_action
      )),
      '}'
    ),

    modify_action: $ => prec(2, seq(
      kw('modify'),
      '(',
      field('target', $._identifier_choice),
      ')',
      '{',
      repeat(choice(
        $._action_property,
        $.attribute_item,
        $.trigger_declaration,
        ';'
      )),
      '}'
    )),

    _action_element: $ => choice(
      $.action_declaration,
      $.actionref_declaration,
      $.systemaction_declaration,
      $.fileuploadaction_declaration,
      $.customaction_declaration
    ),

    action_declaration: $ => seq(
      kw('action'),
      '(',
      field('name', $._identifier_choice),
      ')',
      '{',
      repeat(choice(
        $._action_property,
        $.trigger_declaration,
        $.var_section,
        $.preproc_conditional_action_properties,
        ';'
      )),
      '}'
    ),

    actionref_declaration: $ => seq(
      kw('actionref'),
      '(',
      field('promoted_name', $._identifier_choice),
      ';',
      field('action_name', $._identifier_choice),
      ')',
      '{',
      repeat(choice(
        $._action_property,
        $.trigger_declaration,
        $.var_section,
        ';'
      )),
      '}'
    ),

    systemaction_declaration: $ => seq(
      kw('systemaction'),
      '(',
      field('name', $._identifier_choice),
      ')',
      '{',
      repeat(choice(
        $._action_property,
        $.trigger_declaration,
        $.var_section,
        $.preproc_conditional_action_properties,
        ';'
      )),
      '}'
    ),

    fileuploadaction_declaration: $ => seq(
      kw('fileuploadaction'),
      '(',
      field('name', $._identifier_choice),
      ')',
      '{',
      repeat(choice(
        $._action_property,
        $.fileuploadaction_trigger,
        $.var_section,
        ';'
      )),
      '}'
    ),

    customaction_declaration: $ => seq(
      kw('customaction'),
      '(',
      field('name', $._identifier_choice),
      ')',
      '{',
      repeat(choice(
        $._action_property,
        ';'
      )),
      '}'
    ),

    fileuploadaction_trigger: $ => seq(
      kw('trigger'),
      field('name', alias(kw('OnAction'), $.trigger_name)),
      '(',
      optional($.parameter_list),
      ')',
      optional($.var_section),
      $.code_block
    ),

    _action_property: $ => $._action_properties,

    application_area_property: $ => seq(
      'ApplicationArea',
      '=',
      field('value', seq(
        $._flexible_identifier_choice,
        repeat(seq(',', $._flexible_identifier_choice))
      )),
      ';'
    ),

    usage_category_property: _value_property_template(
      $ => kw('UsageCategory'),
      $ => $.usage_category_value
    ),

    source_table_property: $ => seq(
      kw_with_eq('sourcetable'),
      field('value', $._object_reference),
      ';'
    ),

    page_type_property: $ => seq(
      kw('PageType'),
      '=',
      field('value', choice(
        kw('card'),
        kw('list'),
        kw('rolecenter'),
        kw('worksheet'),
        kw('standarddialog'),
        kw('confirmdialog'),
        kw('navigationpane'),
        kw('headlines'),
        kw('document'),
        kw('api'),
        kw('cardpart'),
        $.string_literal,
        $.identifier,
        $._quoted_identifier
      )),
      ';'
    ),

    cardpart_property: $ => seq(
      $._cardpart_keyword,
      '=',
      field('value', choice(
        $.boolean,
        $.integer,
        $.identifier,
        $._quoted_identifier
      )),
      ';'
    ),

    image_property: $ => seq(
      kw('Image'),
      $._mixed_identifier_string_property_template
    ),

    run_object_property: _value_property_template(
      $ => kw('RunObject'),
      $ => $.run_object_value
    ),

    run_object_value: $ => seq(
      choice(
        kw('page'), 
        kw('report'),
        kw('codeunit'),
        kw('table'),
        kw('xmlport'),
        kw('query')
      ),
      field('object_ref', choice(
        $._object_reference,
        $.member_expression  // Support fully qualified names like Microsoft.Manufacturing.StandardCost."Standard Cost Worksheet Names"
      ))
    ),

    run_page_link_property: $ => seq(
      'RunPageLink',
      '=',
      seq(
        $.run_page_link_value,
        repeat(seq(',', $.run_page_link_value))
      ),
      ';'
    ),

    run_page_view_property: _value_property_template(
      $ => kw('RunPageView'),
      $ => $.source_table_view_value
    ),

    run_form_link_type_property: $ => seq(
      kw('runformlinktype'),
      '=',
      field('value', choice(
        kw('onetomany'),
        kw('onetoone'),
        kw('many'),
        $.identifier
      )),
      ';'
    ),

    _const_value: $ => choice(
      prec(20, $.database_reference),  // Higher precedence for Database:: patterns
      prec(9, $.qualified_enum_value),  // Allow Enum::Value patterns
      prec(5, $.boolean),  // Add boolean with precedence to avoid conflicts
      $.identifier,
      $._quoted_identifier,
      $.integer,
      $.string_literal
    ),

    run_page_link_value: $ => seq(
      field('field', $._identifier_choice),
      '=',
      field('filter_type', choice(
        seq(
          kw('const'),
          '(',
          field('const_value', $._const_value),
          ')'
        ),
        seq(
          kw('field'),
          '(',
          field('field_value', choice(
            $._identifier_choice,
            seq(
              kw('filter'),
              '(',
              field('filter_value', $._identifier_choice),
              ')'
            )
          )),
          ')'
        ),
        seq(
          kw('filter'),
          '(',
          field('filter_value', $._filter_value),
          ')'
        )
      ))
    ),

    enabled_property: $ => seq(
      kw('enabled'),
      $._expression_property_template
    ),

    visible_property: $ => seq(
      field('name', alias(kw_with_eq('visible'), 'Visible')),
      field('value', $._expression),
      ';'
    ),

    scope_property: $ => seq(
      kw_with_eq('scope'),
      field('value', $._identifier_choice),
      ';'
    ),

    promoted_property: $ => seq(
      kw('promoted'),
      $._boolean_property_template
    ),

    promoted_category_property: _value_property_template(
      $ => kw('PromotedCategory'),
      $ => $._flexible_identifier_choice
    ),

    promoted_only_property: $ => seq(
      'PromotedOnly',
      $._boolean_property_template
    ),

    promoted_is_big_property: $ => seq(
      'PromotedIsBig',
      $._boolean_property_template
    ),

    shortcut_key_property: $ => prec(8, seq(
      kw('shortcutkey'),
      '=',
      field('value', choice(
        $.string_literal,
        $._quoted_identifier,
        $.identifier,
        // Allow keywords as shortcut key values (e.g., return, delete, escape)
        kw('return'),
        kw('delete'),
        kw('escape'),
        kw('end'),
        kw('home')
      )),
      ';'
    )),

    in_footer_bar_property: $ => seq(
      'InFooterBar',
      $._boolean_property_template
    ),

    run_page_mode_property: $ => seq(
      'RunPageMode',
      '=',
      field('value', $.run_page_mode_value),
      ';'
    ),

    run_page_on_rec_property: $ => seq(
      'RunPageOnRec',
      $._boolean_property_template
    ),

    _assignment_operator: $ => token(choice(':=', '+=', '-=', '*=', '/=')),
    _double__colon: $ => token(prec(10, '::')), // Moderate precedence
    _colon: $ => ':',

    table_no_property: $ => seq(
      alias(kw_with_eq('tableno'), 'TableNo'),
      field('value', alias($._table_no_value, $.value)),
      ';'
    ),

    subtype_property: $ => seq(
      kw_with_eq('subtype'),
      field('value', alias($.subtype_value, $.value)),
      ';'
    ),

    single_instance_property: $ => seq(
      'SingleInstance',
      '=',
      field('value', alias($.single_instance_value, $.value)),
      ';'
    ),

    event_subscriber_instance_property: $ => seq(
      kw('eventsubscriberinstance'),
      '=',
      field('value', alias($.event_subscriber_instance_value, $.value)),
      ';'
    ),

    test_isolation_property: $ => seq(
      kw('testisolation'),
      '=',
      field('value', alias($.test_isolation_value, $.value)),
      ';'
    ),

    test_http_request_policy_property: $ => seq(
      kw('testhttprequestpolicy'),
      '=',
      field('value', choice(
        alias(kw('blockoutboundrequests'), $.value),
        alias(kw('allowoutboundfromhandler'), $.value),
        alias(kw('allowoutbound'), $.value)
      )),
      ';'
    ),

    drilldown_pageid_property: $ => seq(
      kw('drilldownpageid'),
      '=', 
      field('value', alias($.page_id_value, $.value)),
      ';'
    ),

    lookup_pageid_property: $ => seq(
      kw('lookuppageid'),
      '=',
      field('value', alias($.page_id_value, $.value)),
      ';'
    ),

    card_page_id_property: $ => seq(
      kw('cardpageid'),
      '=',
      field('value', $.page_id_value),
      ';'
    ),

    promoted_action_categories_property: $ => seq(
      kw('promotedactioncategories'),
      $._string_property_template
    ),

    implementation_property: $ => seq(
      'Implementation',
      '=',
      field('value', $.implementation_value_list),
      ';'
    ),

    implementation_value_list: $ => prec.right(repeat1(
      choice(
        $.implementation_value,
        ',',
        $.preproc_if,
        $.preproc_endif,
        $.preproc_else
      )
    )),

    default_implementation_property: $ => seq(
      kw('defaultimplementation'),
      '=',
      field('value', $.implementation_value_list),
      ';'
    ),

    unknown_value_implementation_property: $ => seq(
      kw('unknownvalueimplementation'),
      '=',
      field('value', $.implementation_value_list),
      ';'
    ),

    table_declaration: $ => seq(
      kw('table'),
      $._object_header_base,
      '{',
      repeat($._table_element),
      '}'
    ),

    codeunit_declaration: $ => seq(
      kw('codeunit'),
      $._object_header_base,
      optional($.implements_clause),
      '{',
      repeat(choice(
        $.attribute_item,
        prec(4, $._codeunit_properties), // Use individual properties
        $.preproc_conditional_object_properties,
        $.var_section,
        $.preproc_conditional_var_sections,
        $.procedure,
        $.preproc_split_procedure,
        $.preproc_procedure_body_split,
        $.onrun_trigger,
        $.trigger_declaration,
        $.preproc_conditional_procedures,
        // Lower precedence to prefer pragma inside var_section
        prec(-10, $.pragma),

        // Region directives for code organization
        $.preproc_region,
        $.preproc_endregion
      )),
      '}'
    ),





    preproc_conditional_procedures: $ => seq(
      $.preproc_if,
      repeat1(choice($.attribute_item, $.procedure, $.onrun_trigger, $.trigger_declaration)),
      optional(seq(
        $.preproc_else,
        repeat1(choice($.attribute_item, $.procedure, $.onrun_trigger, $.trigger_declaration))
      )),
      $.preproc_endif
    ),

    preproc_conditional_var_sections: $ => seq(
      $.preproc_if,
      repeat1($.var_section),
      optional(seq(
        $.preproc_else,
        repeat1($.var_section)
      )),
      $.preproc_endif
    ),

    // Handle mixed var sections and procedures in preprocessor
    preproc_conditional_mixed_content: $ => seq(
      $.preproc_if,
      repeat1(choice(
        $.var_section,
        $.attribute_item,
        $.procedure,
        $.trigger_declaration,
        $.actions_section,   // Allow conditional actions sections
        $.layout_section     // Allow conditional layout sections
      )),
      optional(seq(
        $.preproc_else,
        repeat1(choice(
          $.var_section,
          $.attribute_item,
          $.procedure,
          $.trigger_declaration,
          $.actions_section,
          $.layout_section
        ))
      )),
      $.preproc_endif
    ),

    implements_clause: $ => seq(
      kw('implements'),
      field('interface', $._identifier_choice),
      repeat(seq(',', field('interface', $._identifier_choice)))
    ),

    // Generic trigger rule for codeunits etc.

    page_declaration: $ => seq(
      kw('page'),
      $._object_header_base,
      '{',
      repeat(seq(optional(';'), $._page_element)),
      '}'
    ),

    pagecustomization_declaration: $ => seq(
      kw('pagecustomization'),
      field('object_name', $._identifier_choice),
      kw('customizes'),
      field('target_page', $._identifier_choice),
      '{',
      repeat($._pagecustomization_element),
      '}'
    ),

    profile_declaration: $ => seq(
      kw('profile'),
      field('object_name', $._identifier_choice),
      '{',
      repeat($._profile_element),
      '}'
    ),

    profileextension_declaration: $ => seq(
      kw('profileextension'),
      field('object_name', $._identifier_choice),
      kw('extends'),
      field('base_object', $._identifier_choice),
      '{',
      repeat($._profile_element),
      '}'
    ),

    controladdin_declaration: $ => seq(
      kw('controladdin'),
      field('object_name', $._identifier_choice),
      '{',
      repeat($._controladdin_element),
      '}'
    ),

    _controladdin_element: $ => choice(
      $.attribute_item,
      $._controladdin_properties,    // Centralized properties
      $.controladdin_event,          // ControlAddIn structural elements
      $.controladdin_procedure,      // ControlAddIn procedures without attributes
      $.property_list,               // Generic fallback
      $.preproc_conditional_controladdin_elements
    ),

    entitlement_declaration: $ => seq(
      kw('entitlement'),
      field('object_name', $._identifier_choice),
      '{',
      repeat($._entitlement_element),
      '}'
    ),

    _entitlement_element: $ => choice(
      $._entitlement_properties,      // Entitlement-specific properties
      $.property_list,                // Generic property container
      $.preproc_conditional_entitlement_properties
    ),

    entitlement_type_property: $ => seq(
      kw('type'),
      '=',
      field('value', choice(
        kw('applicationscope'),                    // ApplicationScope
        kw('peruserserviceplan'),            // PerUserServicePlan
        kw('role'),                                                                      // Role
        $.identifier                                                                              // Allow other identifiers
      )),
      ';'
    ),

    entitlement_role_type_property: $ => seq(
      kw('roletype'),
      '=',
      field('value', choice(
        kw('delegated'),                  // Delegated
        kw('local'),                                    // Local
        $.identifier                                                // Allow other identifiers
      )),
      ';'
    ),

    entitlement_id_property: $ => seq(
      kw('id'),
      $._string_property_template
    ),

    entitlement_group_name_property: $ => seq(
      kw('groupname'),
      $._string_property_template
    ),

    object_entitlements_property: $ => seq(
      kw('objectentitlements'),
      '=',
      field('value', choice(
        $._identifier_choice,
        seq(
          $._identifier_choice,
          repeat(seq(',', $._identifier_choice))
        )
      )),
      ';'
    ),

    controladdin_property: $ => seq(
      field('name', $.identifier),
      '=',
      field('value', choice(
        $.integer,
        $.boolean,
        $.string_literal,
        seq(
          $.string_literal,
          repeat(seq(',', $.string_literal))
        )
      )),
      optional(';')
    ),

    controladdin_event: $ => seq(
      'event',
      field('name', $.identifier),
      '(',
      optional($.parameter_list),
      ')',
      optional(';')
    ),

    controladdin_procedure: $ => seq(
      kw('procedure'),
      field('name', $.identifier),
      '(',
      optional($.parameter_list),
      ')',
      optional(';')
    ),


    interface_declaration: $ => seq(
      kw('interface', 10),
      field('object_name', $._identifier_choice),
      optional(seq(
        kw('extends'),
        field('extends_interface', $._identifier_choice)
      )),
      optional(seq(
        kw('access'),
        '=',
        field('access_value', choice(
          kw('internal'),
          kw('public'),
          $.identifier
        ))
      )),
      '{',
      repeat(choice(
        $.attribute_item,
        $._interface_properties,
        $.interface_procedure
      )),
      '}'
    ),

    interface_procedure: $ => seq(
      kw('procedure'),
      field('name', $._identifier_choice),
      '(',
      optional($.parameter_list),
      ')',
      optional(choice(
        // Named return (Identifier : Type) - higher precedence to prefer shift when identifier follows
        prec(11, $._procedure_named_return),
        // Anonymous return (: Type)
        $._interface_return_specification
      )),
      optional(';')
    ),
    
    _interface_return_specification: $ => prec(50, seq(
      ':',
      field('return_type', $.return_type)
    )),


    report_declaration: $ => seq(
      kw('report'),
      $._object_header_base,
      '{',
      repeat($._report_element),
      '}'
    ),

    reportextension_declaration: $ => seq(
      kw('reportextension'),
      $._object_header_base,
      kw('extends'),
      field('base_object', $._identifier_choice),
      '{',
      repeat($._reportextension_element),
      '}'
    ),

    _reportextension_element: $ => choice(
      // Report extension can modify dataset, requestpage, etc.
      $.attribute_item,
      $.dataset_section,
      $.requestpage_section,
      $.rendering_section,
      $._report_properties,
      $.var_section,
      $.preproc_conditional_var_sections,
      $.procedure,
      $.preproc_split_procedure,
      $.preproc_procedure_body_split,
      $.trigger_declaration,
      $.preproc_region,
      $.preproc_endregion,
      $.pragma
    ),

    _report_element: $ => choice(
      $.attribute_item,
      // Structural report elements (not properties)
      $.dataset_section,
      $.labels_section,
      $.requestpage_section,
      $.rendering_section,
      $.actions_section,
      $.var_section,
      $.preproc_conditional_var_sections,

      // Report procedures and triggers
      $.procedure,
      $.preproc_split_procedure,
      $.preproc_procedure_body_split,
      $.trigger_declaration,
      $.preproc_conditional_procedures,

      // Preprocessor conditional report properties
      $.preproc_conditional_report_properties,

      // All report properties now centralized
      $._report_properties,

      // Region directives for code organization
      $.preproc_region,
      $.preproc_endregion
    ),

    labels_section: $ => seq(
      kw('labels'),
      '{',
      repeat($._label_element),
      '}'
    ),

    _label_element: $ => choice(
      $.label_declaration
    ),

    rendering_section: $ => seq(
      kw('rendering'),
      '{',
      repeat($.rendering_layout),
      '}'
    ),

    rendering_layout: $ => seq(
      choice('layout', 'Layout', 'LAYOUT'),
      '(',
      field('name', $._identifier_choice),
      ')',
      '{',
      repeat($._rendering_layout_property),
      '}'
    ),

    _rendering_layout_property: $ => choice(
      $.rendering_type_property,
      $.layout_file_property,
      $.mime_type_property,
      $.summary_property,
      $._universal_properties  // includes caption_property
    ),

    rendering_type_property: $ => seq(
      kw('Type'),
      '=',
      field('value', choice(
        kw('Excel'),
        kw('Word'),
        kw('PDF'),
        kw('RDLC'),
        $.identifier
      )),
      ';'
    ),

    layout_file_property: $ => seq(
      kw('LayoutFile'),
      '=',
      field('value', $.string_literal),
      ';'
    ),

    mime_type_property: $ => seq(
      kw('MimeType'),
      '=',
      field('value', $.string_literal),
      ';'
    ),

    summary_property: $ => seq(
      kw('Summary'),
      '=',
      field('value', $.string_literal),
      ';'
    ),

    label_declaration: $ => seq(
      field('name', $.identifier),
      '=',
      field('value', $.string_literal),
      repeat(seq(
        ',',
        choice(
          seq(
            kw('comment'),
            '=',
            field('comment', $.string_literal)
          ),
          seq(
            kw('locked'),
            '=',
            field('locked', $.boolean)
          ),
          seq(
            kw('maxlength'),
            '=',
            field('maxlength', $.integer)
          )
        )
      )),
      ';'
    ),

    dataset_section: $ => seq(
      'dataset',
      '{',
      repeat(choice(
        $.report_dataitem_section,
        $.preproc_conditional_report_dataitems,
        $.add_dataitem,
        $.addafter_dataitem,
        $.addbefore_dataitem,
        $.addfirst_dataitem,
        $.addlast_dataitem,
        $.modify_dataitem  // Support modify in report extensions
      )),
      '}'
    ),

    preproc_conditional_report_dataitems: _preproc_conditional_block_template($ => choice(
      $.report_dataitem_section,
      $.preproc_conditional_report_dataitems
    )),

    add_dataitem: $ => seq(
      kw('add'),
      '(',
      field('target', $._identifier_choice),
      ')',
      '{',
      repeat(choice(
        $.report_column_section,
        $.preproc_conditional_report_columns
      )),
      '}'
    ),

    addafter_dataitem: $ => _modification_with_target_template(
      'addafter',
      $.report_dataitem_section
    )($),

    addbefore_dataitem: $ => _modification_with_target_template(
      'addbefore',
      $.report_dataitem_section
    )($),

    addfirst_dataitem: $ => choice(
      _modification_with_target_template(
        'addfirst',
        $.report_dataitem_section
      )($),
      _modification_without_target_template(
        'addfirst',
        $.report_dataitem_section
      )($)
    ),

    addlast_dataitem: $ => choice(
      _modification_with_target_template(
        'addlast',
        $.report_dataitem_section
      )($),
      _modification_without_target_template(
        'addlast',
        $.report_dataitem_section
      )($)
    ),

    modify_dataitem: $ => seq(
      kw('modify'),
      '(',
      field('target', $._identifier_choice),
      ')',
      '{',
      repeat(choice(
        $.trigger_declaration,         // OnAfterAfterGetRecord and other triggers
        $.report_column_section,        // column definitions
        $.preproc_conditional_report_columns
      )),
      '}'
    ),

    // Interface-specific properties
    _interface_properties: $ => choice(
      $._universal_properties,  // Includes obsolete properties
      $.inherent_permissions_property,
      $.access_property
    ),

    report_dataitem_section: $ => seq(
      'dataitem',
      '(',
      field('name', $._identifier_choice),
      ';',
      field('table_name', choice(
        $._identifier_choice,
        $.qualified_table_reference
      )),
      ')',
      '{',
      repeat($._report_dataitem_content_element),
      '}'
    ),

    _report_dataitem_content_element: $ => choice(
      $.report_column_section,
      $.report_dataitem_section,
      $._dataitem_properties,
      $.attribute_item,
      $.trigger_declaration,
      $.preproc_conditional_report_dataitem_content
    ),

    preproc_conditional_report_dataitem_content: $ => seq(
      $.preproc_if,
      repeat($._report_dataitem_content_element),
      optional(seq(
        $.preproc_else,
        repeat($._report_dataitem_content_element)
      )),
      $.preproc_endif
    ),

    report_column_section: $ => seq(
      'column',
      '(',
      field('name', $._identifier_choice),
      ';',
      field('source', $._expression),
      ')',
      '{',
      repeat($._report_column_properties),
      '}'
    ),

    requestpage_section: $ => seq(
      'requestpage',
      '{',
      repeat(choice(
        $._page_properties,
        $.layout_section, 
        $.actions_section,
        $.trigger_declaration
      )),
      '}'
    ),

    permissionset_declaration: $ => seq(
      kw('permissionset'),
      $._object_header_base,
      '{',
      repeat($._permissionset_element),
      '}'
    ),

    _permissionset_element: $ => choice(
      $._permissionset_properties,   // Centralized properties
      prec(2, $.permissionset_permissions),   // PermissionSet structural elements - higher precedence
      $.preproc_conditional_permissionset_properties
    ),

    permissionsetextension_declaration: $ => seq(
      kw('permissionsetextension'),
      field('object_id', $.integer),
      field('object_name', $._identifier_choice),
      kw('extends'),
      field('extends_target', $._identifier_choice),
      '{',
      repeat($._permissionsetextension_element),
      '}'
    ),

    _permissionsetextension_element: $ => choice(
      $._permissionset_properties,   // Reuse permissionset properties
      prec(2, $.permissionset_permissions),   // PermissionSet structural elements - higher precedence
      $.property_list,               // Generic fallback
      $.preproc_conditional_permissionset_properties
    ),

    assignable_property: $ => seq(
      'Assignable',
      '=',
      field('value', $._boolean_value),
      ';'
    ),

    included_permission_sets_property: $ => seq(
      kw('includedpermissionsets'),
      '=',
      field('value', $.included_permission_sets_list),
      ';'
    ),

    excluded_permission_sets_property: $ => seq(
      kw('excludedpermissionsets'),
      '=',
      field('value', $.excluded_permission_sets_list),
      ';'
    ),

    included_permission_sets_list: $ => $._identifier_choice_list,

    excluded_permission_sets_list: $ => $._identifier_choice_list,

    permissionset_permissions: $ => seq(
      choice('Permissions', 'permissions', 'PERMISSIONS'),
      '=',
      $.permission_list,
      ';',
      repeat(';')  // Allow trailing semicolons
    ),

    permission_list: $ => seq(
      choice(
        $.permission_entry,
        $.preproc_conditional_permissions  // Allow starting with #if
      ),
      repeat(choice(
        prec(2, seq(',', $.permission_entry)),
        prec(2, seq(',', $.preproc_conditional_permissions)),
        prec(1, $.preproc_conditional_permissions),  // Allow conditional after #endif without comma
        prec(1, $.permission_entry)  // Allow entry after conditional without comma
      ))
    ),

    preproc_conditional_permissions: $ => seq(
      $.preproc_if,
      repeat(choice(
        seq($.permission_entry, ','),  // Prioritize entry with comma
        $.permission_entry
      )),
      optional(seq(
        $.preproc_else,
        repeat(choice(
          seq($.permission_entry, ','),  // Prioritize entry with comma
          $.permission_entry
        ))
      )),
      $.preproc_endif
    ),

    permission_entry: $ => prec(2, seq(
      field('object_type', choice(
        $.identifier,
        alias(kw('tabledata'), $.identifier)  // Allow tabledata as object type
      )),
      field('object_reference', choice(
        $._quoted_identifier,
        $.identifier,
        $.integer,
        '*'  // Wildcard support
      )),
      '=',
      field('permission', $.permission_type)
    )),

    dotnet_declaration: $ => seq(
      kw('dotnet'),
      '{',
      repeat($.assembly_declaration),
      '}'
    ),

    assembly_declaration: $ => seq(
      kw('assembly'),
      '(',
      field('name', choice(
        $.string_literal, 
        $._quoted_identifier,
        $.dotnet_assembly_name
      )),
      ')',
      '{',
      repeat(choice(
        $.assembly_property,
        $.type_declaration
      )),
      '}'
    ),

    // Assembly names can contain dots but not special characters
    dotnet_assembly_name: $ => token(seq(
      new RustRegex('[A-Za-z_][A-Za-z0-9_]*'),
      repeat(seq('.', new RustRegex('[A-Za-z_][A-Za-z0-9_]*')))
    )),

    assembly_property: $ => choice(
      seq('Version', '=', field('value', choice($.string_literal, $._quoted_identifier)), ';'),
      seq('Culture', '=', field('value', choice($.string_literal, $._quoted_identifier)), ';'),
      seq('PublicKeyToken', '=', field('value', choice($.string_literal, $._quoted_identifier)), ';')
    ),

    type_declaration: $ => seq(
      kw('type'),
      '(',
      field('dotnet_type', choice(
        $.string_literal, 
        $._quoted_identifier,
        $.dotnet_type_name
      )),
      ';',
      field('al_name', choice(
        $.string_literal, 
        $._quoted_identifier,
        $.identifier
      )),
      ')',
      '{',
      // Type body can be empty or contain additional declarations
      repeat(choice(
        seq(kw('IsControlAddIn'), '=', $.boolean, ';')
      )),
      '}'
    ),

    dotnet_type_name: $ => token(seq(
      new RustRegex('[A-Za-z_][A-Za-z0-9_]*'),
      repeat(seq('.', new RustRegex('[A-Za-z_][A-Za-z0-9_]*')))
    )),

    _page_element: $ => choice(
      $.attribute_item,
      // Structural page elements (not properties)
      $.layout_section,
      $.actions_section,
      $.views_section,  // Support page views section
      $.procedure,
      // Use prec.dynamic to prefer var_section continuation over split procedures
      prec.dynamic(-50, $.preproc_split_procedure),
      $.preproc_procedure_body_split,
      $.var_section,
      $.preproc_conditional_var_sections, // Support preprocessor conditional var sections
      $.trigger_declaration,
      $.preproc_conditional_procedures,  // Support preprocessor conditional procedures
      $.preproc_conditional_mixed_content,  // Support mixed trigger and var sections in preprocessor

      // Region directives for code organization
      $.preproc_region,
      $.preproc_endregion,

      // All page properties now centralized
      $._page_properties,

      // Lower dynamic precedence to prefer var_section continuation
      prec.dynamic(-100, $.preproc_conditional_page_properties),

      // Special case: source_table_view_property at the top for higher precedence
      $.source_table_view_property,
    ),

    layout_section: $ => seq(
      choice('layout', 'Layout', 'LAYOUT'),
      '{',
      repeat($._layout_element),
      '}'
    ),

    views_section: $ => seq(
      kw('views'),
      '{',
      repeat(choice(
        $.view_definition,
        $.addafter_views,
        $.addfirst_views,
        $.addlast_views,
        $.modify_views
      )),
      '}'
    ),
    
    modify_views: $ => seq(
      kw('modify'),
      '(',
      field('target', $.identifier),
      ')',
      '{',
      repeat($._view_property),
      '}'
    ),

    view_caption_property: $ => seq(
      kw('caption'),
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // Uses kw_with_eq to distinguish property from variable name
    view_filters_property: $ => seq(
      alias(kw_with_eq('filters'), 'Filters'),
      field('value', $.where_clause),
      ';'
    ),

    view_order_by_property: $ => prec(2, seq(
      kw('orderby'),
      '=',
      field('value', choice(
        $.sorting_clause,
        $.source_table_view_value
      )),
      ';'
    )),

    shared_layout_property: $ => seq(
      kw('sharedlayout'),
      $._boolean_property_template
    ),

    _layout_element: $ => choice(
      $.area_section,
      $.group_section,
      $.cuegroup_section,
      $.grid_section,
      $.repeater_section,
      $.field_section,
      $.part_section,
      $.systempart_section,
      $.usercontrol_section,
      $.fixed_section,
      $.label_section,
      $.actions_section,
      $.addfirst_layout_modification,
      $.addlast_layout_modification,
      $.addafter_layout_modification,
      $.addbefore_layout_modification,
      $.modify_layout_modification,
      $.movefirst_layout_modification,
      $.movelast_layout_modification,
      $.moveafter_layout_modification,
      $.movebefore_layout_modification,
      $.preproc_conditional_layout,
      $.pragma
    ),

    // Layout modification rules for pageextensions
    addfirst_layout_modification: $ => _modification_with_target_template(
      'addfirst',
      $._layout_element
    )($),

    addlast_layout_modification: $ => _modification_with_target_template(
      'addlast',
      $._layout_element
    )($),

    addafter_layout_modification: $ => _modification_with_target_template(
      'addafter',
      $._layout_element
    )($),

    addbefore_layout_modification: $ => _modification_with_target_template(
      'addbefore',
      $._layout_element
    )($),

    modify_layout_modification: $ => seq(
      kw('modify'),
      '(',
      field('target', $._identifier_choice),
      ')',
      '{',
      repeat(choice(
        $._page_properties,
        $.attribute_item,
        $.trigger_declaration
      )),
      '}'
    ),

    movefirst_layout_modification: $ => seq(
      kw('movefirst'),
      $._move_layout_modification_template
    ),

    movelast_layout_modification: $ => seq(
      kw('movelast'),
      $._move_layout_modification_template
    ),

    moveafter_layout_modification: $ => seq(
      kw('moveafter'),
      $._move_layout_modification_template
    ),

    movebefore_layout_modification: $ => seq(
      kw('movebefore'),
      $._move_layout_modification_template
    ),

    area_section: $ => seq(
      kw('area'),
      '(',
      field('type', choice(
        kw('content'),
        kw('factboxes'),
        kw('filter'),
        kw('rolecenter'),
        kw('promptoptions'),
        kw('prompt'),
        kw('prompting'),
        kw('systemactions'),
        kw('processing')
      )),
      ')',
      '{',
      repeat($._layout_element),
      '}'
    ),

    group_section: $ => seq(
      kw('group'),
      '(',
      field('name', $._identifier_choice),
      ')',
      '{',
      repeat(choice(
        $._page_properties,
        $._layout_element,
        $.preproc_conditional_group_content
      )),
      '}'
    ),

    cuegroup_section: $ => seq(
      kw('cuegroup'),
      '(',
      field('name', $._identifier_choice),
      ')',
      '{',
      repeat(choice(
        $._page_properties,
        $.field_section,
        $.actions_section,
        $.cuegroup_section,
        $.preproc_conditional_group_content
      )),
      '}'
    ),

    grid_section: $ => seq(
      kw('grid'),
      '(',
      field('name', $._identifier_choice),
      ')',
      '{',
      repeat(choice(
        $._page_properties,
        $._layout_element,
        $.preproc_conditional_group_content
      )),
      '}'
    ),

    fixed_section: $ => seq(
      kw('fixed'),
      '(',
      field('name', $._identifier_choice),
      ')',
      '{',
      repeat(choice(
        $._page_properties,
        $._layout_element,
        $.preproc_conditional_group_content
      )),
      '}'
    ),

    label_section: $ => seq(
      kw('label'),
      '(',
      field('name', $._identifier_choice),
      ')',
      '{',
      repeat(choice(
        $._universal_properties,
        $._display_properties
      )),
      '}'
    ),

    repeater_section: $ => seq(
      kw('repeater'),
      '(',
      field('name', $._identifier_choice),
      ')',
      '{',
      repeat(choice(
        $._page_properties,
        $._layout_element,
        $.preproc_conditional_group_content
      )),
      '}'
    ),

    field_section: $ => seq(
      kw('field'),
      '(',
      field('control_id', choice($.string_literal, $._quoted_identifier, $.integer, $.identifier)),
      optional(seq(
        ';',
        field('source_or_field_name', $._expression)
      )),
      ')',
      optional(seq(
        '(',
        field('control_name', $._identifier_choice),
        ')'
      )),
      '{',
      repeat($._field_properties),
      '}'
    ),

    part_section: $ => seq(
      kw('part'),
      '(',
      field('name', choice($.string_literal, $.identifier, $._quoted_identifier)),
      ';',
      field('page_name', $._identifier_choice),
      ')',
      '{',
      repeat(choice(
        $._page_properties,
        $.empty_statement,
        $.preproc_conditional_group_content
      )),
      '}'
    ),

    systempart_section: $ => seq(
      kw('systempart'),
      '(',
      field('control_id', choice($.string_literal, $.identifier, $._quoted_identifier)),
      ';',
      field('systempart_type', $._identifier_choice),
      ')',
      '{',
      repeat(choice(
        $._page_properties,
        $.empty_statement,
        $.preproc_conditional_group_content
      )),
      '}'
    ),

    usercontrol_section: $ => seq(
      kw('usercontrol'),
      '(',
      field('control_id', $._identifier_choice),
      ';',
      field('addin_name', $._identifier_choice),
      ')',
      '{',
      repeat(choice(
        $._page_properties,
        $.trigger_declaration,
        $.var_section,
        $.code_block,
        $.preproc_conditional_properties,
        $.preproc_conditional_group_content,
        $.pragma
      )),
      '}'
    ),

    sub_page_link_property: $ => seq(
      kw('SubPageLink'),
      '=',
      $._sub_page_link_list,
      ';'
    ),

    _sub_page_link_list: $ => seq(
      $._sub_page_link_item,
      repeat(seq(
        optional(','),
        $._sub_page_link_item
      )),
      optional(',')
    ),

    _sub_page_link_item: $ => choice(
      $.run_page_link_value,
      $.preproc_conditional_sub_page_link
    ),

    preproc_conditional_sub_page_link: _preproc_conditional_block_template($ => seq(
      $.run_page_link_value,
      optional(',')
    )),

    sub_page_view_property: $ => seq(
      'SubPageView',
      '=',
      field('value', choice(
        $.string_literal,
        $.identifier, // Simple identifier like 'Ascending'
        $.source_table_view_value // Support full table view syntax including sorting(...) where(...)
      )),
      ';'
    ),

    source_expr_property: $ => seq(
      'SourceExpr',
      '=',
      field('value', choice(
        $.identifier,
        $._quoted_identifier,
        $.string_literal,
        $.member_expression,
        $.field_access
      )),
      ';'
    ),

    qualified_trigger_name: $ => seq(
      field('provider', $.identifier),
      '::',
      field('event', $.identifier)
    ),

    trigger_declaration: $ => seq(
      kw('trigger'),
      field('name', alias(
        choice(
          $.identifier,
          $.qualified_trigger_name
        ),
        $.trigger_name
      )),
      choice(
        seq('(', optional($.parameter_list), ')'),
        seq()
      ),
      optional(choice(
        seq(':', $.type_specification), // Simple return type
        $._procedure_named_return        // Named return value
      )),
      choice(
        // Standard trigger with code block
        prec(2, seq(
          optional(';'), // Allow optional semicolon after trigger declaration
          optional(choice(
            $.var_section,
            $.preproc_conditional_var_sections
          )),
          $.code_block
        )),
        // Control add-in trigger declaration ending with semicolon (without code block)
        prec(1, ';')
      )
    ),

    // Property value types for specific properties
    _table_no_value: $ => $._object_reference,

    subtype_value: $ => choice(
      // Codeunit SubType values
      kw('install'),
      kw('upgrade'),
      kw('test'),
      // BLOB SubType values
      kw('userdefined'),
      kw('bitmap'),
      kw('json'),
      // Other potential values (like PurchaseHeader)
      $.identifier  // Allow any identifier to be future-proof
    ),

    single_instance_value: $ => $._boolean_value,

    event_subscriber_instance_value: $ => choice(
      kw('manual'),
      kw('static'),
      kw('staticautomatic')
    ),

    test_isolation_value: $ => choice(
      kw('codeunit'),
      kw('function'),
      kw('page'),
      kw('disabled')
    ),

    implementation_value: $ => seq(
      field('interface', $._identifier_choice),
      '=',
      field('implementation', $._identifier_choice)
    ),

    field_class_value: $ => choice(
      kw('flowfield'),
      kw('flowfilter'),
      kw('normal')
    ),


    extended_datatype_value: $ => choice(
      kw('none'),
      kw('phoneno'),
      kw('url'), 
      kw('email'),
      kw('ratio'),
      kw('duration'),
      kw('masked'),
      kw('richcontent'),
      kw('barcode'),
      kw('person')
    ),

    // Values for the first 5 missing Page Field Properties
    column_span_value: $ => $.integer,
    
    importance_value: $ => choice(
      kw('standard'),
      kw('additional'),
      kw('promoted'),
      prec(10, $._quoted_identifier)  // Higher precedence for quoted values
    ),

    style_value: $ => choice(
      seq(optional('"'), kw('none'), optional('"')),
      seq(optional('"'), kw('standard'), optional('"')),
      seq(optional('"'), kw('standardaccent'), optional('"')),
      seq(optional('"'), kw('strong'), optional('"')),
      seq(optional('"'), kw('strongaccent'), optional('"')),
      seq(optional('"'), kw('attention'), optional('"')),
      seq(optional('"'), kw('attentionaccent'), optional('"')),
      seq(optional('"'), kw('favorable'), optional('"')),
      seq(optional('"'), kw('unfavorable'), optional('"')),
      seq(optional('"'), kw('subordinate'), optional('"')),
      seq(optional('"'), kw('ambiguous'), optional('"'))
    ),

    run_page_mode_value: $ => choice(
      kw('edit'),
      kw('view'),
      kw('create')
    ),

    // First 5 missing Page Field Properties
    assist_edit_property: $ => seq(
      'AssistEdit',
      $._boolean_property_template
    ),
    
    column_span_property: _value_property_template('ColumnSpan', $ => $.column_span_value),
    
    drill_down_property: $ => seq(
      'DrillDown',
      $._boolean_property_template
    ),

    lookup_property: $ => prec(1, seq(
      'Lookup',
      $._boolean_property_template
    )),
    
    hide_value_property: $ => seq(
      'HideValue',
      $._expression_property_template
    ),
    
    multi_line_property: $ => seq(
      kw('multiline'),
      $._boolean_property_template
    ),
    
    importance_property: $ => seq(
      kw_with_eq('importance'),
      field('value', $.importance_value),
      ';'
    ),

    navigation_page_id_property: $ => seq(
      'NavigationPageId',
      '=',
      field('value', $.page_id_value),
      ';'
    ),

    quick_entry_property: $ => seq(
      'QuickEntry',
      $._boolean_property_template
    ),

    row_span_property: $ => seq(
      'RowSpan',
      $._integer_property_template
    ),

    width_property: $ => seq(
      kw_with_eq('width'),
      field('value', $.integer),
      ';'
    ),

    show_caption_property: $ => seq(
      kw('showcaption'),
      $._caption_boolean_template
    ),

    show_as_tree_property: $ => seq(
      kw('ShowAsTree'),
      $._boolean_property_template
    ),

    tree_initial_state_property: $ => seq(
      kw('TreeInitialState'),
      '=',
      field('value', choice(
        kw('CollapseAll'),
        kw('ExpandAll')
      )),
      ';'
    ),

    grid_layout_property: $ => seq(
      kw('gridlayout'),
      '=',
      field('value', $.grid_layout_value),
      ';'
    ),

    show_mandatory_property: $ => seq(
      'ShowMandatory',
      $._expression_property_template
    ),

    style_property: $ => seq(
      kw_with_eq('style'),
      field('value', $.style_value),
      ';'
    ),

    style_expr_property: $ => seq(
      kw_with_eq('styleexpr'),
      field('value', $._expression),
      ';'
    ),

    page_id_value: $ => $._object_reference,


    blank_zero_value: $ => $._boolean_value,

    option_caption_value: $ => $.string_literal,

    table_type_value: $ => choice(
      kw('normal'),
      kw('temporary'),
      kw('external'),
      kw('system'),
      kw('crm'),
      kw('exchangeobject'),
      kw('externalsql'),
      kw('exchange'),
      kw('microsoftgraph'),
      kw('masterdataintegration')
    ),

    closing_dates_value: $ => $._boolean_value,
    char_allowed_value: $ => choice(
      $.string_literal,     // 'AZ', '0-9', etc.
      $.boolean,           // true/false (legacy?)
      $.identifier         // Variable reference
    ),
    compressed_value: $ => $._boolean_value,
    date_formula_value: $ => choice(
      $.string_literal,
      $.boolean,
      $.identifier  // Allow variable references
    ),
    usage_category_value: $ => choice(
      kw('administration'),
      kw('documents'),
      kw('lists'),
      kw('reports'),
      kw('tasks'),
      kw('reportsandanalysis'),
      $.identifier,
      $._quoted_identifier
    ),
    external_name_value: $ => $.string_literal,
    external_type_value: $ => choice(
      $.string_literal,
      // Also support bare identifiers for compatibility
      kw('Uniqueidentifier'),
      kw('DateTime'), 
      kw('Lookup'),
      kw('Owner'),
      kw('State'),
      kw('Status'),
      kw('BigInt'),
      kw('Integer'),
      kw('String'),
      kw('Boolean'),
      kw('Picklist')
    ),
    not_blank_value: $ => $._boolean_value,
    numeric_value: $ => $._boolean_value,
    obsolete_reason_value: $ => $.string_literal,
    obsolete_state_value: $ => choice(
      kw('pending'),
      kw('removed'),
      kw('moved')
    ),
    obsolete_tag_value: $ => $.string_literal,
    option_ordinal_values_value: $ => choice(
      $.string_literal,
      $.option_ordinal_values_list
    ),
    
    option_ordinal_values_list: $ => seq(
      choice($.integer, $.unary_expression),  // Support negative integers
      repeat(seq(',', choice($.integer, $.unary_expression)))
    ),
    paste_is_valid_value: $ => $.boolean,
    sign_displacement_value: $ => $.boolean,
    sql_data_type_value: $ => choice(
      kw('BigInt'),
      kw('Bit'),
      kw('Char'),
      kw('DateTime'),
      kw('Decimal'),
      kw('Float'),
      kw('Int'),
      kw('Money'),
      kw('NChar'),
      kw('NText'),
      kw('NVarchar'),
      kw('Real'),
      kw('SmallDateTime'),
      kw('SmallInt'),
      kw('SmallMoney'),
      kw('Text'),
      kw('Timestamp'),
      kw('TinyInt'),
      kw('UniqueIdentifier'),
      kw('Varchar'),
      kw('Variant'),
      kw('Xml')
    ),
    sql_timestamp_value: $ => $.boolean,
    test_table_relation_value: $ => $.boolean,
    tool_tip_value: $ => seq(
      $.string_literal,
      repeat(seq(
        ',',
        choice(
          seq(kw('comment'), '=', $.string_literal),
          seq(kw('locked'), '=', $.boolean)
        )
      ))
    ),
    unique_value: $ => $.boolean,
    validate_table_relation_value: $ => $.boolean,
    values_allowed_value: $ => seq(
      choice(
        $._flexible_identifier_choice, 
        $.integer,
        $.unary_expression  // Support negative integers
      ),
      repeat(seq(',', choice(
        $._flexible_identifier_choice, 
        $.integer,
        $.unary_expression  // Support negative integers
      )))
    ),

    // NEW HIGH PRIORITY PROPERTIES - Value Rules
    data_caption_fields_value: $ => seq(
      $._flexible_identifier_choice,
      repeat(seq(',', $._flexible_identifier_choice))
    ),

    extensible_value: $ => $.boolean,

    data_per_company_value: $ => $.boolean,

    replicate_data_value: $ => $.boolean,

    assignment_compatibility_value: $ => $.boolean,

    column_store_index_value: $ => seq(
      $._identifier_choice,
      repeat(seq(',', $._identifier_choice))
    ),

    compression_type_value: $ => choice(
      kw('none'),
      kw('page'),
      kw('row'),
      kw('unspecified')
    ),

    inherent_permissions_value: $ => $.permission_type,

    inherent_entitlements_value: $ => $.permission_type,

    access_value: $ => choice(
      kw('public'),
      kw('internal'),
      kw('private')
    ),

    access_by_permission_value: $ => choice(
      // TableData object permissions
      $._tabledata_permission_template,
      // System object permissions  
      $._system_permission_template,
      // Table object permissions
      seq(
        kw('table'),
        $._standard_permission_template
      ),
      // Page object permissions
      seq(
        kw('page'),
        $._standard_permission_template
      ),
      // Report object permissions
      seq(
        kw('report'),
        $._standard_permission_template
      ),
      // Codeunit object permissions
      seq(
        kw('codeunit'),
        $._standard_permission_template
      ),
      // XMLport object permissions
      seq(
        kw('xmlport', 10),
        $._standard_permission_template
      ),
      // Query object permissions
      seq(
        kw('query'),
        $._standard_permission_template
      )
    ),


    auto_format_type_value: $ => choice(
      $.integer,  // Accept any integer value
      '0', // None
      '1', // Phone Number
      '2', // Currency
      '3', // Date
      '4', // Time
      '5', // Date and Time
      '6', // Amount
      '7', // Quantity
      '8', // Percentage
      '9', // Custom
      '10' // Custom with Format Expression
    ),

    auto_increment_value: $ => $.boolean,

    blank_numbers_value: $ => choice(
      $.boolean,
      $.string_literal,     // String literal values like "BlankNeg"
      $.identifier,         // Variable or property references like "BlankZero"
      $._quoted_identifier  // Quoted property references
    ),

    table_type_property: $ => seq(
      field('name', alias(kw_with_eq('tabletype'), 'TableType')),
      field('value', alias($.table_type_value, $.value)),
      ';'
    ),

    access_by_permission_property: $ => seq(
      kw('AccessByPermission'),
      '=',
      field('value', alias($.access_by_permission_value, $.value)),
      ';'
    ),

    allow_in_customizations_property: $ => prec(1, seq(
      kw('AllowInCustomizations'), 
      '=',
      field('value', alias(choice(
        $.boolean,
        kw('never')
      ), $.value)),
      ';'
    )),

    auto_format_expression_property: $ => seq(
      kw('AutoFormatExpression'),
      $._expression_property_template
    ),

    auto_format_type_property: $ => seq(
      kw('AutoFormatType'),
      '=',
      field('value', alias($.auto_format_type_value, $.value)),
      ';'
    ),

    auto_increment_property: $ => seq(
      'AutoIncrement',
      '=',
      field('value', alias($.auto_increment_value, $.value)),
      ';'
    ),

    blank_numbers_property: $ => seq(
      'BlankNumbers',
      '=',
      field('value', alias($.blank_numbers_value, $.value)),
      ';'
    ),

    access_property: $ => seq(
      choice('Access', 'access', 'ACCESS'),
      '=',
      field('value', alias($.access_value, $.value)),
      ';'
    ),

    closing_dates_property: $ => seq(
      kw('ClosingDates'),
      '=',
      field('value', $.closing_dates_value),
      ';'
    ),

    char_allowed_property: $ => seq(
      'CharAllowed',
      '=',
      field('value', alias($.char_allowed_value, $.value)),
      ';'
    ),

    compressed_property: $ => seq(
      kw('compressed'), 
      '=',
      field('value', $.compressed_value),
      ';'
    ),

    date_formula_property: $ => seq(
      kw('dateformula'),
      '=',
      field('value', $.date_formula_value),
      ';'
    ),

    description_property: $ => seq(
      alias(kw_with_eq('description'), 'Description'),
      field('value', $.string_literal),
      ';'
    ),


    external_name_property: $ => seq(
      kw('ExternalName'),
      '=',
      field('value', $.external_name_value),
      ';'
    ),

    external_type_property: $ => seq(
      kw('ExternalType'),
      '=',
      field('value', $.external_type_value),
      ';'
    ),

    init_value_property: $ => seq(
      kw('initvalue'),
      $._expression_property_template
    ),

    max_value_property: $ => seq(
      kw('maxvalue'),
      $._expression_property_template
    ),

    min_value_property: $ => seq(
      kw('minvalue'),
      $._expression_property_template
    ),

    not_blank_property: $ => seq(
      kw('notblank'),
      '=',
      field('value', $.not_blank_value),
      ';'
    ),

    numeric_property: $ => seq(
      kw('numeric'),
      '=',
      field('value', $.numeric_value),
      ';'
    ),

    obsolete_reason_property: $ => seq(
      'ObsoleteReason',
      '=',
      field('value', $.obsolete_reason_value),
      ';'
    ),

    obsolete_state_property: $ => seq(
      'ObsoleteState',
      '=',
      field('value', $.obsolete_state_value),
      ';'
    ),

    obsolete_tag_property: $ => seq(
      'ObsoleteTag',
      '=',
      field('value', $.obsolete_tag_value),
      ';'
    ),

    option_ordinal_values_property: $ => seq(
      kw('OptionOrdinalValues'),
      '=',
      field('value', $.option_ordinal_values_value),
      ';'
    ),

    paste_is_valid_property: $ => seq(
      'PasteIsValid',
      '=',
      $.paste_is_valid_value,
      ';'
    ),

    sign_displacement_property: $ => seq(
      'SignDisplacement',
      '=',
      $.sign_displacement_value,
      ';'
    ),

    sql_data_type_property: $ => seq(
      kw('SqlDataType'),
      '=',
      field('value', $.sql_data_type_value),
      ';'
    ),

    sql_timestamp_property: $ => seq(
      kw('SqlTimestamp'),
      '=',
      field('value', $.sql_timestamp_value),
      ';'
    ),

    test_table_relation_property: $ => seq(
      kw('TestTableRelation'),
      '=',
      field('value', $.test_table_relation_value),
      ';'
    ),

    tool_tip_property: $ => seq(
      kw('tooltip'),
      $._tooltip_template
    ),

    unique_property: $ => seq(
      'Unique',
      '=',
      $.unique_value,
      ';'
    ),

    validate_table_relation_property: $ => seq(
      'ValidateTableRelation',
      '=',
      $.validate_table_relation_value,
      ';'
    ),

    values_allowed_property: $ => seq(
      kw('ValuesAllowed'),
      '=',
      field('value', $.values_allowed_value),
      ';'
    ),

    extended_datatype_property: $ => seq(
      kw('extendeddatatype'),
      '=',
      field('value', $.extended_datatype_value),
      ';'
    ),

    // NEW HIGH PRIORITY PROPERTIES - Property Rules
    data_caption_fields_property: $ => seq(
      kw('datacaptionfields'),
      '=',
      field('value', $.data_caption_fields_value),
      ';'
    ),

    extensible_property: _value_property_template(
      $ => choice('Extensible', 'extensible', 'EXTENSIBLE'),
      $ => $.extensible_value
    ),

    data_per_company_property: _value_property_template(
      $ => kw('datapercompany'),
      $ => $.data_per_company_value
    ),

    replicate_data_property: _value_property_template(
      $ => kw('replicatedata'),
      $ => $.replicate_data_value
    ),

    assignment_compatibility_property: _value_property_template(
      $ => kw('assignmentcompatibility'),
      $ => $.assignment_compatibility_value
    ),

    column_store_index_property: _value_property_template(
      $ => kw('columnstoreindex'),
      $ => $.column_store_index_value
    ),

    compression_type_property: _value_property_template(
      $ => kw('compressiontype'),
      $ => $.compression_type_value
    ),


    external_access_property: _value_property_template(
      $ => kw('externalaccess'),
      $ => choice(
        kw('insert'),
        kw('modify'),
        kw('delete'),
        kw('read'),
        kw('full'),
        $.identifier
      )
    ),

    inherent_permissions_property: _value_property_template(
      $ => kw('inherentpermissions'),
      $ => $.inherent_permissions_value
    ),

    inherent_entitlements_property: _value_property_template(
      $ => kw('inherententitlements'),
      $ => $.inherent_entitlements_value
    ),

    caption_ml_property: $ => seq(
      kw('captionml'),
      $._ml_property_template
    ),

    option_caption_ml_property: $ => seq(
      kw('optioncaptionml'),
      '=',
      field('ml_values', seq(
        $.ml_value_pair,
        repeat(seq(',', $.ml_value_pair))
      )),
      optional(seq(
        ',',
        kw('locked'),
        '=',
        $.boolean
      )),
      ';'
    ),

    tool_tip_ml_property: $ => seq(
      kw('tooltipml'),
      $._ml_property_template
    ),

    ml_value_list: $ => seq(
      $.ml_value_pair,
      repeat(seq(',', $.ml_value_pair))
    ),

    ml_value_pair: $ => seq(
      field('language', $.identifier),
      '=',
      field('value', $.string_literal)
    ),

    data_classification_value: $ => choice(
      kw('customercontent'),
      kw('enduseridentifiableinformation'),
      kw('accountdata'),
      kw('enduserpseudonymousidentifiers'),
      kw('organizationidentifiableinformation'),
      kw('systemmetadata'),
      kw('tobeclassified')
    ),


    onrun_trigger: $ => seq(
      $._trigger_keyword,
      kw('onrun'),
      $._trigger_parameters,
      optional(';'), // Allow optional semicolon after OnRun() like other triggers
      optional($.var_section),
      $.code_block
    ),


    _table_element: $ => prec(1, choice(
      $.attribute_item,
      // Structural table elements (not properties)
      $.fields,  // Fields section should be primary
      $.keys,
      $.fieldgroups_section,
      $.var_section,
      $.preproc_conditional_var_sections,
      $.preproc_conditional_mixed_content,  // Add mixed content support

      // Table triggers
      $.named_trigger,

      // Procedures
      $.procedure,
      $.preproc_split_procedure,
      $.preproc_procedure_body_split,
      $.preproc_conditional_procedures,

      // All table properties now centralized
      $._table_properties,

      // Preprocessor conditional table properties
      $.preproc_conditional_table_properties,

      // Allow standalone semicolons (empty statements)
      $.empty_statement,

      // Region directives for code organization
      $.preproc_region,
      $.preproc_endregion
    )),

    // For single table permission property
    permissions_property: $ => seq(
      choice('Permissions', 'permissions', 'PERMISSIONS'),
      '=',
      optional($.tabledata_permission_list),
      ';'
    ),

    test_permissions_property: $ => seq(
      kw('TestPermissions'),
      '=',
      field('value', alias(choice(
        kw('disabled'), 
        kw('nonrestrictive'), 
        kw('restrictive'), 
        kw('inherentpermissions'),
        kw('nonrestrictedproperties'),
        kw('restrictedproperties')
      ), $.test_permissions_value)),
      ';'
    ),

    permission_type: $ => token(
      prec(-1, choice(
        new RustRegex('[rRiImMdDxX]+'),
        'RCMDXI'  // Allow specific full permission string
      ))
    ),


    named_trigger: $ => choice(
      // Regular trigger
      seq(
        $._trigger_keyword,
        field('name', choice(
          kw('oninsert'),
          kw('onmodify'),
          kw('ondelete'),
          kw('onrename'),
          kw('onvalidate'),
          kw('onaftergetrecord'),
          kw('onafterinsertevent'),
          kw('onaftermodifyevent'),
          kw('onafterdeleteevent'),
          kw('onbeforeinsertevent'),
          kw('onbeforemodifyevent'),
          kw('onbeforedeleteevent'),
          kw('onbeforeinsertrecord')  // XMLPort-specific trigger
        )),
        $._trigger_parameters,
        optional(';'),  // Allow optional semicolon after trigger declaration
        optional($.var_section),
        $.code_block
      ),
      // Trigger with preprocessor conditional var section
      seq(
        $._trigger_keyword,
        field('name', choice(
          kw('oninsert'),
          kw('onmodify'),
          kw('ondelete'),
          kw('onrename'),
          kw('onvalidate'),
          kw('onaftergetrecord'),
          kw('onafterinsertevent'),
          kw('onaftermodifyevent'),
          kw('onafterdeleteevent'),
          kw('onbeforeinsertevent'),
          kw('onbeforemodifyevent'),
          kw('onbeforedeleteevent'),
          kw('onbeforeinsertrecord')  // XMLPort-specific trigger
        )),
        $._trigger_parameters,
        optional(';'),  // Allow optional semicolon after trigger declaration
        $.preproc_conditional_var_sections,
        $.code_block
      )
    ),
    
    property_list: $ => prec.left(3, seq(
      $.property,
      repeat($.property)
    )),

    property: $ => prec(2, choice(
      $.access_by_permission_property,
      $.allow_in_customizations_property,
      $.auto_format_expression_property,
      $.calc_fields_property,
      $.caption_class_property,
      $.table_no_property,
      $.subtype_property,
      $.single_instance_property,
      $.event_subscriber_instance_property,
      $.test_isolation_property,
      $.drilldown_pageid_property,
      $.lookup_pageid_property,
      $.card_page_id_property,
      $.promoted_action_categories_property,
      $.test_permissions_property,
      $.table_relation_property,
      $.field_class_property,
      $.calc_formula_property,
      $.blank_zero_property,
      $.editable_property,
      $.processing_only_property,
      $.use_request_page_property,
      $.option_members_property,
      $.option_caption_property,
      $.data_classification_property,
      $.extended_datatype_property,
      $.source_table_property,
      $.page_type_property,
      $.application_area_property,
      $.usage_category_property,
      $.cardpart_property,
      $.description_property,
      $.obsolete_state_property,
      $.obsolete_reason_property,
      $.obsolete_tag_property,
      $.access_property, 
      $.caption_property, 
      // NEW HIGH PRIORITY PROPERTIES
      $.data_caption_fields_property,
      $.data_per_company_property,
      $.replicate_data_property,
      $.column_store_index_property,
      $.compression_type_property,
      $.inherent_permissions_property,
      $.inherent_entitlements_property,
      // NEW LOW PRIORITY PROPERTIES (First 5)
      $.auto_replace_property,
      $.auto_save_property,
      $.auto_update_property,
      $.external_schema_property,
      $.link_fields_property,
      // NEW LOW PRIORITY PROPERTIES (Next 5)
      $.link_table_property,
      $.link_table_force_insert_property,
      $.max_occurs_property,
      $.min_occurs_property,
      $.namespace_prefix_property,
      // NEW LOW PRIORITY PROPERTIES (Next 5)
      $.unbound_property,
      $.xml_name_property,
      $.moved_from_property,
      $.moved_to_property,
      $.linked_in_transaction_property,
      // FINAL LOW PRIORITY PROPERTIES
      $.linked_object_property,
      $.request_filter_fields_property,
      $.request_filter_heading_property,
      $.request_filter_heading_ml_property,
      // First 5 missing Page Field Properties
      $.assist_edit_property,
      $.column_span_property,
      $.freeze_column_property,
      $.indentation_column_property,
      $.indentation_controls_property,
      $.grid_layout_property,
      $.drill_down_property,
      $.lookup_property,
      $.hide_value_property,
      $.multi_line_property,
      $.importance_property,
      $.navigation_page_id_property,
      $.quick_entry_property,
      $.row_span_property,
      $.width_property,
      $.show_caption_property,
      $.show_as_tree_property,
      $.tree_initial_state_property,
      $.show_mandatory_property,
      $.style_property,
      $.style_expr_property,
      $.save_values_property,
      $.show_filter_property,
      $.data_item_table_view_property,
      $.promoted_only_property,
      $.shortcut_key_property,
      $.additional_search_terms_property,
      $.additional_search_terms_ml_property,
      $.instructional_text_property,
      $.instructional_text_ml_property,
      $.sub_page_link_property,
      $.sub_page_view_property,
      $.update_propagation_property,
      $.visible_property,
      $.provider_property,
      $.allow_in_customizations_property
    )),

    caption_property: $ => seq(
      field('name', alias(kw_with_eq('caption'), 'Caption')),
      $.string_literal,
      repeat(seq(
        ',',
        choice(
          seq(
            kw('locked'),
            '=',
            $.boolean
          ),
          seq(
            kw('comment'),
            '=',
            $.string_literal
          ),
          seq(
            kw('maxlength'),
            '=',
            $.integer
          )
        )
      )),
      optional(','),  // Support trailing comma
      ';'
    ),

    caption_class_property: $ => seq(
      alias(kw_with_eq('captionclass'), 'CaptionClass'),
      field('value', $._expression),
      ';'
    ),

    calc_fields_property: $ => seq(
      kw('CalcFields'),
      '=',
      field('fields', $.calc_fields_list),
      ';'
    ),

    auto_calc_field_property: $ => seq(
      kw('AutoCalcField'),
      $._boolean_property_template
    ),

    calc_fields_list: $ => seq(
      $.calc_field,
      repeat(seq(',', $.calc_field))
    ),

    calc_field: $ => choice(
      $.identifier,
      $._quoted_identifier
    ),

    data_classification_property: $ => seq(
      kw('DataClassification'),
      '=',
      field('value', $.data_classification_value),
      ';'
    ),


    tabledata_permission_list: $ => seq(
      choice(
        $.tabledata_permission,
        $.preproc_conditional_tabledata_permissions  // Allow starting with #if
      ),
      repeat(choice(
        prec(2, seq(',', $.tabledata_permission)),
        prec(2, seq(',', $.preproc_conditional_tabledata_permissions)),
        prec(1, $.preproc_conditional_tabledata_permissions),  // Allow conditional after #endif without comma
        prec(1, $.tabledata_permission)  // Allow entry after conditional without comma
      ))
    ),

    preproc_conditional_tabledata_permissions: $ => seq(
      $.preproc_if,
      repeat(choice(
        seq($.tabledata_permission, ','),  // Prioritize entry with comma
        $.tabledata_permission
      )),
      optional(seq(
        $.preproc_else,
        repeat(choice(
          seq($.tabledata_permission, ','),
          $.tabledata_permission
        ))
      )),
      $.preproc_endif
    ),

    tabledata_permission: $ => seq(
      field('keyword', alias(choice(
        kw('tabledata'),
        /[Tt][Aa][Bb][Ll][Ee][Dd][Aa][Tt][Aa]/  // Fallback regex for preprocessor contexts
      ), $.tabledata_keyword)),
      field('table_name', $._table_reference),
      '=',
      field('permission', $.permission_type)
    ),


    decimal_places_property: $ => seq(
      kw('DecimalPlaces'),
      '=',
      choice(
        // Simple format: DecimalPlaces = 2;
        field('value', $.integer),
        // Complex format: DecimalPlaces = 2:5; or DecimalPlaces = 0 :;
        seq(
          field('precision', $.integer),
          ':',
          optional(field('scale', $.integer))
        )
      ),
      ';'
    ),

    var_section: $ => prec.right(10, seq(
      optional(kw('protected')),
      kw('var'),
      repeat(prec.right(20, choice(
        $.comment,
        $.multiline_comment,
        $.pragma,
        $.variable_declaration,
        seq(
          repeat1($.attribute_item),
          repeat(choice($.comment, $.multiline_comment, $.pragma)),
          $.variable_declaration
        ),
        // Scanner discrimination + high dynamic precedence forces parser to stay in var_section
        prec.dynamic(100, seq($.preproc_var_continuation, $.preproc_conditional_variables)),
        // Pragma followed by variable - scanner detects this and emits token to continue var_section
        prec.dynamic(100, seq($._pragma_var_continuation, $.pragma)),
        // Attribute followed by variable - scanner detects this and emits token to continue var_section
        prec.dynamic(100, seq(
          $._attribute_var_continuation,
          repeat1($.attribute_item),
          repeat(choice($.comment, $.multiline_comment, $.pragma)),
          $.variable_declaration
        ))
      )))
    )),

    // Variable declaration with attributes (e.g., [RunOnClient])

    // Helper rule for unquoted variable names (allows certain keywords as identifiers)
    _unquoted_variable_name: $ => choice(
      $.identifier,
      // Allow the keyword 'Description' to be treated as an identifier in variable contexts
      alias(kw('description'), $.identifier),
      // Allow the keyword 'Importance' to be treated as an identifier in variable contexts
      alias(kw('importance'), $.identifier),
      // Allow the keyword 'SourceTable' to be treated as an identifier in variable contexts
      alias(kw('sourcetable'), $.identifier),
      // Allow the keyword 'IncludeCaption' to be treated as an identifier in variable contexts
      alias(kw('includecaption'), $.identifier),
      // Allow the keyword 'ExcludeCaption' to be treated as an identifier in variable contexts
      alias(kw('excludecaption'), $.identifier),
      // Allow IsPreview as identifier - using kw() for parser consistency
      alias(kw('ispreview'), $.identifier),
      // Allow the keyword 'SubType' to be treated as an identifier in variable contexts
      alias(kw('subtype'), $.identifier),
      // Allow the keyword 'CuegroupLayout' to be treated as an identifier in variable contexts
      alias(kw('cuegrouplayout'), $.identifier),
      // Allow the keyword 'Caption' to be treated as an identifier in variable contexts
      alias(kw('caption'), $.identifier),
      // Allow the keyword 'Scope' to be treated as an identifier in variable contexts
      alias(kw('scope'), $.identifier),
      // Allow the keyword 'TableNo' to be treated as an identifier in variable contexts
      alias(kw('tableno'), $.identifier),
      // Allow the keyword 'PrintOnlyIfDetail' to be treated as an identifier in variable contexts
      alias(kw('printonlyifdetail'), $.identifier),
      // Allow the keyword 'MaxIteration' to be treated as an identifier in variable contexts
      alias(kw('maxiteration'), $.identifier),
      // Allow the keyword 'Style' to be treated as an identifier in variable contexts
      alias('Style', $.identifier),
      alias('style', $.identifier),
      alias('STYLE', $.identifier),
      // Allow the keyword 'StyleExpr' to be treated as an identifier in variable contexts
      alias('StyleExpr', $.identifier),
      alias('styleexpr', $.identifier),
      alias('STYLEEXPR', $.identifier),
      // Allow the keyword 'Width' to be treated as an identifier in variable contexts
      alias(kw('width'), $.identifier),
      // Allow the keyword 'Height' to be treated as an identifier in variable contexts
      alias(kw('height'), $.identifier),
      // Allow common End* identifiers that conflict with 'end' keyword
      alias(kw('end'), $.identifier),
      alias(kw('endingtime'), $.identifier),
      alias(kw('endindex'), $.identifier),
      alias(kw('endvalue'), $.identifier),
      alias(kw('enddata'), $.identifier),
      alias(kw('endpoint'), $.identifier),
      alias(kw('enddate'), $.identifier),
      alias(kw('endtime'), $.identifier),
      // Allow 'field' to be used as an identifier in variable contexts
      alias(kw('field'), $.identifier),
      // Allow 'CustomActionType' to be used as an identifier in variable contexts
      alias(kw('customactiontype'), $.identifier),
      // Allow 'TableType' to be used as an identifier in variable contexts
      alias('TableType', $.identifier),
      alias('tabletype', $.identifier),
      alias('TABLETYPE', $.identifier),
      alias('Tabletype', $.identifier),
      // Allow 'ShowFilter' to be used as an identifier in variable contexts
      alias('ShowFilter', $.identifier),
      alias('showfilter', $.identifier),
      alias('SHOWFILTER', $.identifier),
      alias('Showfilter', $.identifier),
      // Allow 'DataCaptionExpression' to be used as an identifier in variable contexts
      alias(kw('datacaptionexpression'), $.identifier),
      // Allow 'Enum' to be used as an identifier in variable contexts
      alias(kw('enum'), $.identifier),
      // Allow 'ReadOnly' to be used as an identifier in variable contexts
      alias(kw('readonly'), $.identifier),
      // Allow 'ApiVersion' to be used as an identifier in variable contexts
      alias(kw('apiversion'), $.identifier),
      // Allow 'Filters' to be used as an identifier in variable contexts
      alias(kw('filters'), $.identifier),
      // Allow 'Visible' to be used as an identifier in variable contexts
      alias('Visible', $.identifier),
      alias('visible', $.identifier),
      alias('VISIBLE', $.identifier),
      // Allow 'HelpLink' to be used as an identifier in variable contexts - using kw() for parser consistency
      alias(kw('helplink'), $.identifier),
      // Allow 'Layout' to be used as an identifier in variable contexts
      alias('Layout', $.identifier),
      alias('layout', $.identifier),
      alias('LAYOUT', $.identifier),
      // Allow 'Actions' to be used as an identifier in variable contexts
      alias('Actions', $.identifier),
      alias('actions', $.identifier),
      alias('ACTIONS', $.identifier),
      // Allow 'Permissions' to be used as an identifier in variable contexts
      alias('Permissions', $.identifier),
      alias('permissions', $.identifier),
      alias('PERMISSIONS', $.identifier),
      // Note: 'Trigger' cannot be aliased as identifier - it breaks trigger declarations
      // Allow 'Extensible' to be used as an identifier in variable contexts
      alias('Extensible', $.identifier),
      alias('extensible', $.identifier),
      alias('EXTENSIBLE', $.identifier),
      // Allow 'Access' to be used as an identifier in variable contexts
      alias('Access', $.identifier),
      alias('access', $.identifier),
      alias('ACCESS', $.identifier),
      // Allow 'CaptionClass' to be used as an identifier in variable contexts
      alias(kw('captionclass'), $.identifier)
    ),

    // Helper rule for comma-separated variable names
    _variable_name_list: $ => seq(
      field('name', choice($._unquoted_variable_name, $._quoted_identifier)),
      repeat(seq(',', field('name', choice($._unquoted_variable_name, $._quoted_identifier))))
    ),

    variable_declaration: $ => choice(
      // Variable with value assignment (using :=)
      prec(3, seq(
        field('names', $._variable_name_list),
        ':',
        optional(field('type', $.type_specification)),
        ':=',
        field('value', $._expression),
        ';'
      )),
      // Label variable declaration with string literal value and optional attributes
      prec(5, seq(
        field('names', $._variable_name_list),
        ':',
        field('type', $.basic_type),
        field('value', $.string_literal),
        optional(seq(
          ',',
          field('attributes', seq(
            $.label_attribute,
            repeat(seq(',', $.label_attribute))
          ))
        )),
        ';'
      )),
      // Regular variable declaration without value
      prec(1, seq(
        field('names', $._variable_name_list),
        ':',
        field('type', $.type_specification),
        optional(field('temporary', $.temporary)),
        ';'
      ))
    ),

    // Simplified parameter rule using the main type_specification
    // parameter: $ => seq( // Original rule moved into the choice below
    //   optional(field('modifier', $.modifier)),
    //   field('parameter_name', alias($.identifier, $.name)),
    //   ':',
    //   field('parameter_type', $.type_specification) // Use the main type_specification
    // ),

    // Specific rule for inline option parameters
    _parameter_option: $ => seq(
      optional(field('modifier', $.modifier)),
      field('parameter_name', alias($._identifier_choice, $.name)),
      ':',
      kw('option'), // Match the keyword
      field('parameter_type', alias($.option_member_list, $.option_type)) // Reuse option_member_list for members
    ),

    // Updated parameter rule to choose between standard types and inline options
    parameter: $ => choice(
      $._parameter_option, // Try matching inline option first
      seq( // Standard parameter with type_specification
        optional(field('modifier', $.modifier)),
        field('parameter_name', alias($._identifier_choice, $.name)),
        ':',
        field('parameter_type', $.type_specification),
        // Add optional temporary keyword after type for records
        optional(field('temporary', $.temporary)) 
      )
    ),

    label_attribute: $ => seq(
      field('name', $.identifier),
      optional('='), // Make the equals sign explicitly optional
      field('value', choice($.boolean, $.string_literal, $.integer))
    ),

type_specification: $ => choice(
  prec(2, $.array_type),
  prec(2, $.list_type),
  prec(2, $.dictionary_type),
  prec(1, $.text_type),
  prec(1, $.code_type),
  $.basic_type,
  $.record_type,
  $.recordref_type,
  $.fieldref_type,
  $.codeunit_type, 
  $.query_type,
  $.testpage_type,
  $.testrequestpage_type,
  $.report_type,
  $.xmlport_type,
  $.dotnet_type,
  $.page_type,
  $.enum_type,
  $.option_type,
  $.interface_type,
  $.controladdin_type,
  $.identifier, // Allow plain identifiers as types (e.g., HttpClient, DotNet types)
  $._quoted_identifier // Allow quoted identifiers as types
),

// Handles 'Option' type keyword followed by optional members
option_type: $ => prec.right(1, seq(
  kw('option'),
  optional($.option_member_list) // Members are part of the type
)),

// Helper for comma-separated list of option members  
option_member_list: $ => prec.left(1, choice(
  // List starting with empty string ""
  seq(
    '""',
    repeat(seq(',', optional($.option_member)))
  ),
  // List with at least one member
  seq(
    $.option_member,
    repeat(seq(',', optional($.option_member)))
  ),
  // List starting with comma (empty first member)
  seq(
    repeat1(seq(',', optional($.option_member)))
  )
)),

interface_type: $ => seq(
  prec(1, kw('interface')),
  field('reference', choice(
    prec(2, $.qualified_interface_reference),
    prec(1, $._interface_reference)
  ))
),

// Interface reference (simple identifier or quoted)
_interface_reference: $ => choice(
  $._quoted_identifier,
  $.identifier
),

// Namespace-qualified interface reference
qualified_interface_reference: $ => prec.right(8, seq(
  field('namespace', $._identifier_choice),
  repeat1(seq('.', $._identifier_choice)),
  '.',
  field('interface', $._quoted_identifier)
)),

controladdin_type: $ => seq(
  kw('controladdin'),
  field('reference', choice(
    $.identifier,
    $._quoted_identifier
  ))
),

enum_type: $ => prec(1, seq(
  kw('enum'),
  field('enum_name', choice(
    $.identifier,
    $._quoted_identifier,
    $.namespace_qualified_enum_name
  ))
)),

    namespace_qualified_enum_name: $ => prec(2, seq(
      $.identifier,
      repeat1(seq('.', $.identifier)),
      '.',
      $._identifier_choice
    )),

    page_type: $ => seq(
      prec(1, kw('page')),
      field('reference', choice(
        $.integer,
        $._quoted_identifier,
        $.identifier,
        $.namespace_qualified_reference  // Support Microsoft.Inventory.Tracking."Item Tracking Lines"
      ))
    ),

    report_type: $ => seq(
      prec(1, kw('report')),
      field('reference', choice(
        $.integer,
        $._quoted_identifier,
        $.identifier,
        $._namespace_qualified_type_reference
      ))
    ),
    
    _namespace_qualified_type_reference: $ => prec(3, seq(
      field('namespace', seq(
        $.identifier,
        repeat(seq('.', $.identifier))
      )),
      '.',
      field('type_name', $._quoted_identifier)
    )),

    xmlport_type: $ => seq(
      prec(1, kw('xmlport')),
      field('reference', choice(
        $.integer,
        $._quoted_identifier,
        $.identifier,
        $.namespace_qualified_reference
      ))
    ),

    list_type: $ => seq(
      kw('list'), 
      kw('of'), 
      '[', 
      $.type_specification, 
      ']'
    ),

    dictionary_type: $ => seq(
      kw('dictionary'), 
      kw('of'), 
      '[', 
      $.type_specification, 
      ',', 
      $.type_specification, 
      ']'
    ),


    basic_type: $ => choice(
      // Numeric Types
      prec(1, kw('integer')),
      prec(1, kw('biginteger')),
      prec(1, kw('decimal')),
      prec(1, kw('byte')),
      
      // Text Types
      prec(1, kw('char')),
      prec(10, kw('label')),  // High precedence for label type
      
      // Date/Time Types
      prec(1, kw('date')),
      prec(1, kw('time')),
      prec(1, kw('datetime')),
      prec(1, kw('duration')),
      kw('dateformula'),
      
      // Other Types
      prec(1, kw('boolean')),
      // Option removed, handled by option_type
      prec(1, kw('guid')),
      prec(1, kw('recordid')),
      prec(1, kw('variant')),
      prec(1, kw('dialog')),
      prec(1, kw('action')),
      prec(1, kw('blob')),
      prec(1, kw('filterpagebuilder')),
      prec(1, kw('jsontoken')),
      prec(1, kw('jsonvalue')),
      prec(1, kw('jsonarray')),
      prec(1, kw('jsonobject')),
      prec(1, kw('media')),
      prec(1, kw('mediaset')),
      prec(1, kw('ostream')),
      prec(1, kw('instream')),
      prec(1, kw('outstream')),
      prec(1, kw('secrettext')),
      prec(1, kw('moduleinfo')), 
      prec(1, kw('objecttype')), 
      prec(1, kw('keyref')), 

      // XML Types
      kw('xmldocument'),
      prec(1, kw('xmlnode')),
      prec(1, kw('xmlelement')),
      prec(1, kw('xmlnodelist')),
      prec(1, kw('xmlattribute')),
      prec(1, kw('xmlattributecollection'))
    ),

    text_type: $ => choice(
      // Text[100] - higher precedence to prefer shift when '[' follows
      prec(11, seq(
        kw('text'),
        '[',
        field('length', $.integer),
        ']'
      )),
      // Plain "Text" - lower precedence
      prec(10, kw('text'))
    ),

    code_type: $ => choice(
      // Code[20] - higher precedence to prefer shift when '[' follows
      prec(11, seq(
        kw('code'),
        '[',
        field('length', $.integer),
        ']'
      )),
      // Plain "Code" - lower precedence
      prec(10, kw('code'))
    ),

    record_type: $ => prec.right(seq(
      prec(1, kw('record')),
      field('reference', choice(
        prec(2, $.qualified_table_reference),
        prec(1, $._table_reference)
      ))
    )),

    // Dedicated rule for namespace-qualified table references (requires at least one dot)
    qualified_table_reference: $ => prec.right(8, seq(
      field('namespace', $._identifier_choice),
      repeat1(seq('.', field('part', $._identifier_choice)))
    )),
    recordref_type: $ => kw('recordref'),
    fieldref_type: $ => kw('fieldref'),

    // Use existing _table_reference rule that already handles both plain and quoted identifiers 
    _table_reference: $ => choice(
      $.integer,
      $._identifier_choice,  // Unified identifier pattern
      $.qualified_table_reference  // Namespace-qualified tables
    ),

    codeunit_type: $ => prec.right(10, seq(
      kw('codeunit'),
      field('reference', choice(
        $.integer,
        $._quoted_identifier,
        $.identifier,
        $.member_expression,
        $.namespace_qualified_reference
      ))
    )),

    query_type: $ => seq(
      prec(1, kw('query')),
      field('reference', $.query_type_value)
    ),

    testpage_type: $ => seq(
      prec(1, kw('testpage')),
      field('reference', choice(
        $.integer,
        $._quoted_identifier,
        $.identifier,
        $.namespace_qualified_reference
      ))
    ),

    testrequestpage_type: $ => seq(
      prec(1, kw('testrequestpage')),
      field('reference', choice(
        $.integer,
        $._quoted_identifier,
        $.identifier,
        $.namespace_qualified_reference
      ))
    ),

    query_type_value: $ => choice(
      $.integer,
      $._quoted_identifier,
      $.identifier
    ),

    dotnet_type: $ => seq(
      kw('dotnet', 100),
      field('reference', choice($.dotnet_type_name, $.identifier, $.string_literal, $._quoted_identifier))
    ),

    array_type: $ => seq(
      prec(1, kw('array')),
      '[',
      field('sizes', seq(
        $.integer,
        repeat(seq(',', $.integer))
      )),
      ']',
      kw('of'),
      $.type_specification
    ),

    fields: $ => seq(
      kw('fields'),
      '{',
      repeat(choice(
        seq(repeat($.attribute_item), $.field_declaration),
        seq(repeat($.attribute_item), $.modify_field_declaration),
        $.preproc_conditional_fields
      )),
      '}'
    ),

    field_declaration: $ => seq(
      kw('field'),
      '(',
      field('id', $.integer),
      token(';'),  // Make semi_colon an explicit token
      field('name', choice(
        $._quoted_identifier,
        $.identifier
      )),
      token(';'),  // Make semi_colon an explicit token
      // Use the consistent type_specification rule
      field('type', $.type_specification),
      ')',
      optional(seq(
        '{',
        repeat($._field_properties),
        '}'
      ))
    ),

    modify_field_declaration: $ => seq(
      kw('modify'),
      '(',
      field('name', choice(
        $._quoted_identifier,
        $.identifier
      )),
      ')',
      '{',
      repeat(choice(
        $._field_properties,
        $.attribute_item,
        $.trigger_declaration
      )),
      '}'
    ),

    table_relation_property: $ => prec.left(seq(
      'TableRelation',
      '=',
      field('relation', $.table_relation_expression),
      optional(';')
    )),

    table_relation_expression: $ => choice(
      $.simple_table_relation,
      $.if_table_relation,
      $.preproc_conditional_table_relation
    ),

    preproc_conditional_table_relation: $ => seq(
      $.preproc_if,
      choice(
        seq($.table_relation_expression, ';'),
        $.table_relation_expression
      ),
      optional(seq(
        $.preproc_else,
        choice(
          seq($.table_relation_expression, ';'),
          $.table_relation_expression
        )
      )),
      $.preproc_endif
    ),

    // Unified where clause implementation
    where_clause: $ => seq(
      kw('where', 15),  // High precedence to ensure WHERE is recognized
      '(',
      field('conditions', $.where_conditions),
      ')'
    ),

    if_table_relation: $ => prec.right(15, seq(
      kw('if', 10),
      '(',
      field('condition', $.unified_where_conditions),
      ')',
      field('then_relation', $.simple_table_relation),
      optional(seq(
        kw('else', 10),
        field('else_relation', $.table_relation_expression)
      ))
    )),

    simple_table_relation: $ => prec.right(20, seq(
      field('table', $._table_reference),
      optional(seq('.', field('field', $.field_ref))),
      optional(prec(25, $.where_clause))  // Very high precedence for WHERE
    )),

    const_filter: $ => prec(8, seq(
      field('field', $.field_ref),
      '=',
      kw('const'),
      '(',
      optional(field('value', choice(
        $._const_value,
        $.boolean
      ))),
      ')'
    )),

    field_filter: $ => prec(8, seq(
      field('field', $.field_ref),
      '=', 
      kw('field'),
      '(',
      field('value', $.field_ref),
      ')'
    )),

    filter_condition: $ => prec(8, seq(
      field('field', $.field_ref),
      '=',
      field('filter', $.filter_expression_function)
    )),

    where_condition: $ => choice(
      $.simple_filter_expression,  // Add simple_filter_expression for SourceTableView
      $.const_filter,
      $.field_reference_condition,  // Use updated field reference condition that supports upperlimit
      $.field_filter,               // Keep for backward compatibility
      $.filter_condition,
      $.filter_expression_condition  // Add support for filter expressions like Field = filter('>0')
    ),

    where_conditions: $ => seq(
      $._where_condition_element,
      repeat(seq(
        optional(','),
        $._where_condition_element
      )),
      optional(',')
    ),
    
    _where_condition_element: $ => choice(
      $.where_condition,
      $.preproc_conditional_where_condition
    ),
    
    // Preprocessor template that allows where conditions with optional trailing commas
    preproc_conditional_where_condition: _preproc_conditional_block_template($ => 
      seq($.where_condition, optional(','))
    ),


    explicit_field_ref: $ => prec(12, seq(
      kw('field'),
      '(',
      field('field', $._chained_expression),
      ')'
    )),

    field_ref: $ => prec(2, choice(
      $.explicit_field_ref,
      $._non_call_chained_expression,
      $.identifier
    )),

    _non_call_chained_expression: $ => prec(3, choice(
      $.member_expression,
      $.field_access,
      $.qualified_enum_value_tail,
      $._quoted_identifier
    )),

    calc_field_ref: $ => alias(prec(12, choice(
      $.explicit_field_ref,
      $.member_expression,
      $.field_access
    )), $.field_reference),



    field_class_property: $ => seq(
      'FieldClass',
      '=',
      field('value', choice(
        $.string_literal,
        $._quoted_identifier,
        $.field_class_value
      )),
      ';'
    ),

    calc_formula_property: $ => seq(
      'CalcFormula',
      '=',
      $._calc_formula_expression,
      ';'
    ),

    _calc_formula_expression: $ => choice(
      $.lookup_formula,
      $.count_formula,
      $.sum_formula, 
      $.average_formula,
      $.min_formula,
      $.max_formula,
      $.exist_formula,
      // Support for negated formulas
      seq('-', choice(
        $.sum_formula,
        $.average_formula,
        $.min_formula,
        $.max_formula,
        $.count_formula,
        $.exist_formula
      ))
    ),

    lookup_formula: $ => prec(25, seq(
      kw('lookup'),
      '(',
      field('target', choice(
        prec(30, $.field_access),
        prec(28, $.member_expression),
        prec(26, $._quoted_identifier),
        prec(24, $.identifier)
      )),
      optional(prec(35, seq(
        kw('where'),
        '(',
        $.lookup_where_conditions,
        ')'
      ))),
      ')'
    )),


    lookup_where_conditions: $ => prec.left(15, seq(
      $.lookup_where_condition,
      repeat(prec.left(16, seq(',', $.lookup_where_condition)))
    )),

    lookup_where_condition: $ => prec.left(10, seq(
      field('field', prec(15, $.field_ref)),
      '=',
      choice(
        // field("No.") - special handling for field() function
        $._lookup_field_function,
        // filter(value) pattern
        seq(
          kw('filter'),
          '(',
          field('filter_value', $._filter_value_simple),
          ')'
        ),
        seq(
          field('keyword', alias(kw('const'), $.const)),
          '(',
          optional(field('value', choice($.string_literal, $.identifier, $._quoted_identifier, $.integer))),
          ')'
        )
      )
    )),
    
    // Special rule for field() function in lookup context with very high precedence
    _lookup_field_function: $ => prec(100, seq(
      kw('field'),
      '(',
      field('value', alias(prec(105, choice(
        $.identifier,
        $._quoted_identifier,
        $.member_expression,
        $.field_access
      )), $.field_ref)),
      ')'
    )),

    // Rule for calc formula WHERE conditions with higher precedence to resolve conflicts
    // === Unified WHERE Condition Types ===
    
    // Filter expression condition (standard style with operators)
    // Higher precedence to match before const_value_condition in TableRelation contexts
    filter_expression_condition: $ => prec(3, seq(
      field('field', $.field_ref),
      field('operator', $.filter_operator),
      field('value', $.filter_value)
    )),
    
    // FIELD(...) reference condition for formulas
    field_reference_condition: $ => prec(14, seq(
      field('field', $.field_ref),
      '=',
      kw('field'),
      '(',
      field('reference', $.field_reference_expression),
      ')'
    )),
    
    // Field reference expression supports: field_ref, upperlimit(field_ref), filter(field_ref), upperlimit(filter(field_ref))
    field_reference_expression: $ => choice(
      $.field_ref,
      $.upperlimit_expression,
      $.formula_filter_expression,
      $.upperlimit_filter_expression
    ),
    
    upperlimit_expression: $ => seq(
      kw('upperlimit'),
      '(',
      $.field_ref,
      ')'
    ),
    
    formula_filter_expression: $ => seq(
      kw('filter'),
      '(',
      $.field_ref,
      ')'
    ),
    
    upperlimit_filter_expression: $ => seq(
      kw('upperlimit'),
      '(',
      $.formula_filter_expression,
      ')'
    ),
    
    // Removed const_value_condition - it was an old pattern causing conflicts
    // CONST(...) is properly handled as a filter_value in filter_expression_condition
    
    // Unified where condition rule
    unified_where_condition: $ => choice(
      $.filter_expression_condition,
      $.field_reference_condition
      // Removed const_value_condition - it was causing conflicts and is not needed
    ),
    
    // Unified where conditions list that handles both styles
    unified_where_conditions: $ => choice(
      // AND-separated style (filter expressions)
      seq(
        $.unified_where_condition,
        repeat(seq(
          optional(kw('and')),
          $.unified_where_condition
        ))
      ),
      // Comma-separated style (calc/lookup formulas)
      seq(
        $.unified_where_condition,
        repeat(seq(',', $.unified_where_condition))
      )
    ),
    
    // Keep the original calc-related rules for backward compatibility during migration
    count_formula: $ => seq(
      kw('count'),
      '(',
      field('table', alias($._table_reference, $.table_reference)),
      optional($.where_clause),
      ')'
    ),

    sum_formula: $ => seq(
      kw('sum'),
      '(',
      field('target', $.calc_field_ref),
      optional($.where_clause),
      ')'
    ),

    average_formula: $ => seq(
      kw('average'),
      '(',
      field('target', $.calc_field_ref),
      optional($.where_clause),
      ')'
    ),

    min_formula: $ => seq(
      kw('min'),
      '(',
      field('target', $.calc_field_ref),
      optional($.where_clause),
      ')'
    ),

    max_formula: $ => seq(
      kw('max'),
      '(',
      field('target', $.calc_field_ref),
      optional($.where_clause),
      ')'
    ),

    exist_formula: $ => seq(
      kw('exist'),
      '(',
      field('table', alias($._table_reference, $.table_reference)),
      $.where_clause,
      ')'
    ),


    blank_zero_property: $ => seq(
      'BlankZero',
      '=',
      $.blank_zero_value,
      ';'
    ),

    editable_property: $ => seq(
      kw('Editable'),
      $._expression_property_template
    ),

    processing_only_property: $ => seq(
      'ProcessingOnly',
      '=',
      choice(
        kw('true'),
        kw('false')
      ),
      ';'
    ),

    use_request_page_property: $ => seq(
      'UseRequestPage',
      $._boolean_property_template
    ),

    default_namespace_property: $ => seq(
      kw('defaultnamespace'),
      $._string_property_template
    ),

    encoding_property: $ => seq(
      kw('encoding'),
      '=',
      field('value', choice(
        kw('utf8'),
        kw('utf16'),
        kw('iso88591'),
        $.identifier
      )),
      ';'
    ),

    namespaces_property: $ => prec(10, seq(
      kw('namespaces'),
      '=',
      field('value', $.namespace_list),
      ';'
    )),

    namespace_list: $ => prec.right(seq(
      $.namespace_mapping,
      repeat(seq(',', $.namespace_mapping))
    )),

    namespace_mapping: $ => prec.right(3, seq(
      field('prefix', choice(
        alias('""', $.empty_namespace_prefix),  // Empty string for default namespace  
        $.string_literal,  // Other string literals
        $.identifier       // Named prefix like 'cac', 'cbc', etc.
      )),
      '=',
      field('uri', $.string_literal)
    )),

    format_evaluate_property: $ => seq(
      kw('formatevaluate', 20),  // Higher precedence than Format (10)
      '=',
      field('value', choice(
        kw('xml'),
        kw('c/side'),
        $.identifier
      )),
      ';'
    ),

    use_default_namespace_property: $ => seq(
      kw('usedefaultnamespace'),
      $._boolean_property_template
    ),

    preserve_whitespace_property: $ => seq(
      kw('preservewhitespace'),
      $._boolean_property_template
    ),

    table_separator_property: $ => seq(
      kw('TableSeparator'),
      '=',
      field('value', choice(
        $.string_literal,
        kw('NewLine'),
        kw('TAB'),
        kw('None')
      )),
      ';'
    ),

    text_encoding_property: _value_property_template($ => kw('TextEncoding'), $ => choice(
      kw('utf8'),
      kw('utf16'),
      kw('windows'),
      kw('msdos'),
      $.identifier
    )),

    option_members_property: $ => prec(1, seq(
      kw('OptionMembers'),
      '=',
      field('value', $.option_member_list),
      ';'
    )),

    // Rule for option members (used in lists like parameters or OptionMembers property)
    option_member: $ => choice(
      $.identifier,
      $._quoted_identifier,
      $.string_literal
    ),

    option_caption_property: $ => seq(
      kw('optioncaption'),
      $._option_caption_template
    ),

    field_trigger_declaration: $ => seq(
      $._trigger_keyword,
      field('type', alias(choice(
        kw('onvalidate'),
        kw('onaftervalidate'),
        kw('onlookup'),
        kw('onafterlookup'),
        kw('onassistedit'),
        kw('ondrilldown')
      ), $.trigger_type)),
      choice(
        seq('(', optional($.parameter_list), ')'),
        seq()
      ),
      optional(choice(
        seq(':', $.type_specification), // Simple return type
        $._procedure_named_return        // Named return value
      )),
      optional(';'),  // Allow optional semicolon after return type
      optional(choice(
        $.var_section,
        $.preproc_conditional_var_sections
      )),
      $.code_block
    ),

    keys: $ => seq(
      kw('keys'),
      '{',
      repeat(choice(
        $.key_declaration,
        $.preproc_conditional_keys
      )),
      '}'
    ),

    preproc_conditional_keys: _preproc_conditional_block_template($ => choice(
      $.key_declaration,
      $.preproc_conditional_keys
    )),

    preproc_conditional_key_properties: _preproc_conditional_block_template($ => $._key_properties),

    key_declaration: $ => seq(
      kw('key'),
      '(',
      field('name', alias(choice($.identifier, $._quoted_identifier), $.name)),
      ';',
      field('fields', $.key_field_list),
      ')',
      optional(seq(
        '{',
        repeat($._key_properties),
        '}'
      ))
    ),
    
    // Composed property group for key properties
    _key_properties: $ => choice(
      $.clustered_property,
      $.enabled_property,
      $.unique_property,
      $.included_fields_property,
      $.maintain_sift_index_property,
      $.maintain_sql_index_property,
      $.sql_index_property,
      $.sum_index_fields_property,
      $.obsolete_reason_property,
      $.obsolete_state_property,
      $.obsolete_tag_property,
      $.preproc_conditional_key_properties,
      $.property,
      $.empty_statement  // Allow standalone semicolons
    ),

    // Key property rules
    included_fields_property: $ => seq(
      'IncludedFields',
      '=',
      $.key_field_list,
      ';'
    ),
    
    maintain_sift_index_property: $ => seq(
      kw('MaintainSIFTIndex'),
      '=',
      $.boolean,
      ';'
    ),
    
    maintain_sql_index_property: $ => seq(
      kw('MaintainSQLIndex'),
      '=',
      $.boolean,
      ';'
    ),
    
    sql_index_property: $ => seq(
      kw('SQLIndex'),
      '=',
      $.key_field_list,
      ';'
    ),
    
    sum_index_fields_property: $ => seq(
      kw('SumIndexFields'),
      '=',
      $.key_field_list,
      ';'
    ),

    key_field_list: $ => seq(
      $._identifier_choice,
      repeat(seq(',', $._identifier_choice))
    ),

    // NEW: Attribute as a statement (Rust-style refactor - Phase 1)
    // This allows attributes to be peers with declarations, not embedded within them
    attribute_item: $ => seq(
      '[',
      field('attribute', $.attribute_content),
      ']'
    ),

    // NEW: Attribute content (shared structure)
    attribute_content: $ => seq(
      field('name', $.identifier),
      optional(field('arguments', $.attribute_arguments))
    ),

    // LEGACY: Keep for backward compatibility during migration
    // Will be deprecated after Phase 4-6

    attribute: $ => seq(
      '[',
      field('attribute_name', $.identifier),
      optional($.attribute_arguments),
      ']'
    ),

    attribute_arguments: $ => seq(
      '(',
      field('arguments', optional($.expression_list)),
      ')'
    ),

    expression_list: $ => seq(
      $._expression,
      repeat(seq(',', $._expression))
    ),

    return_value: $ => field('return_value', choice(
      $._identifier_choice,
      // Allow Description as a return value name
      alias(kw('description'), $.identifier)
    )),

    _procedure_return_specification: $ => seq(
      ':',
      field('return_type', $.return_type),
      optional(field('temporary', $.temporary))
    ),

    _procedure_named_return: $ => seq(
      $.return_value,
      $._procedure_return_specification
    ),

    // Use the consistent type_specification rule for return types
    return_type: $ => $.type_specification,

    _procedure_name: $ => alias($._identifier_choice, $.name),

    procedure_modifier: $ => choice(kw('local'), kw('internal'), kw('protected')),

    procedure: $ => choice(
      // Regular procedure
      seq(
        optional(field('modifier', $.procedure_modifier)), 
        kw('procedure'),
        field('name', $._procedure_name),
        '(',
        optional($.parameter_list),
        ')',
        // Return type can be followed by optional semicolon or directly by var/begin
        optional(choice(
          seq(
            choice(
              $._procedure_return_specification, // : ReturnType
              $._procedure_named_return // ReturnValue : ReturnType
            ),
            optional(';')
          )
        )),
        // Optional semicolon even when there's no return type (for test procedures)
        optional(';'),
        repeat($.pragma),
        optional(choice(
          $.var_section,
          $.preproc_conditional_var_sections
        )),
        $.code_block
      ),
      // Procedure with conditional return type
      $.preproc_conditional_procedure
    ),

    // Handle procedure declarations with split return type syntax
    preproc_conditional_procedure: $ => seq(
      optional(field('modifier', $.procedure_modifier)), 
      kw('procedure'),
      field('name', $._procedure_name),
      '(',
      optional($.parameter_list),
      ')',
      $.preproc_if,
      choice(
        $._procedure_return_specification, // : ReturnType
        $._procedure_named_return // ReturnValue : ReturnType
      ),
      $.preproc_else,
      choice(
        $._procedure_return_specification, // : ReturnType
        $._procedure_named_return // ReturnValue : ReturnType
      ),
      $.preproc_endif,
      optional(';'),
      repeat($.pragma),
      optional(choice(
        $.var_section,
        $.preproc_conditional_var_sections
      )),
      $.code_block
    ),

    // Split procedure with separate headers (optionally with attributes in branches)
    preproc_split_procedure: $ => seq(
      $.preproc_if,
      repeat($.attribute_item),  // Optional attributes before procedure in #if branch
      field('if_header', $.procedure_header),
      $.preproc_else,
      repeat($.attribute_item),  // Optional attributes before procedure in #else branch
      field('else_header', $.procedure_header),
      $.preproc_endif,
      optional(';'),
      repeat($.pragma),
      optional(choice(
        $.var_section,
        $.preproc_conditional_var_sections
      )),
      $.code_block
    ),

    // Procedure where header is complete but body is conditionally included
    preproc_procedure_body_split: $ => prec(2, seq(
      optional(field('modifier', $.procedure_modifier)), 
      kw('procedure'),
      field('name', $._procedure_name),
      '(',
      optional($.parameter_list),
      ')',
      optional(choice(
        seq(
          choice(
            $._procedure_return_specification, // : ReturnType
            $._procedure_named_return // ReturnValue : ReturnType
          ),
          optional(';')
        )
      )),
      $.preproc_if,
      repeat($.pragma),
      optional($.var_section),
      kw('begin'),
      repeat($._statement),
      repeat($.pragma),
      $.preproc_else,
      kw('begin'),
      $.preproc_endif,
      repeat($._statement),
      kw('end'),
      ';'
    )),

    // Split if-else statement where else is inside preprocessor but body is outside
    preproc_split_if_else: $ => seq(
      $.preproc_if,
      seq(
        kw('if', 10),
        field('condition', $._expression),
        kw('then', 10),
        field('then_branch', choice(
          $.code_block,
          $._if_then_body
        )),
        kw('else', 10)
      ),
      $.preproc_endif,
      field('else_branch', choice(
        $.code_block,
        $._if_then_body
      ))
    ),

    // Split if statement where condition is inside preprocessor but body is outside
    preproc_split_if: $ => seq(
      $.preproc_if,
      seq(
        kw('if', 10),
        field('condition', $._expression),
        kw('then', 10)
      ),
      $.preproc_endif,
      field('then_branch', choice(
        $.code_block,
        $._if_then_body
      ))
    ),

    // Split if-then-begin statement where begin is inside preprocessor, body outside, end in another preprocessor
    // Pattern: #if COND \n if X then begin \n #endif \n body... \n #if COND \n end; \n #endif
    preproc_split_if_then_begin: $ => prec(25, seq(
      $.preproc_if,  // Opening #if
      seq(
        kw('if', 10),
        field('condition', $._expression),
        kw('then', 10),
        kw('begin', 10)
      ),
      $.preproc_endif,  // First #endif
      repeat($._statement_or_preprocessor),  // Body statements (outside preprocessor)
      $.preproc_if,  // Second #if wrapping the end
      kw('end'),
      optional(';'),
      $.preproc_endif  // Second #endif
    )),

    // Handle complex preprocessor pattern where if-else is fragmented across multiple #if blocks
    // Pattern: normal if-else with "end else begin", then #endif, else body, then #if wrapping "end;", then #endif
    preproc_fragmented_if_else: $ => prec(20, seq(
      // Normal if statement up to "end else begin"
      kw('if', 10),
      field('condition', $._expression),
      kw('then', 10),
      field('then_branch', $.code_block),
      kw('else', 10),
      kw('begin', 10),
      // Then a preprocessor endif that closes some earlier #if
      $.preproc_endif,
      // The else body statements
      repeat($._statement_or_preprocessor),
      // Then a preprocessor if that wraps just the closing end;
      $.preproc_if,
      kw('end'),
      optional(';'),
      $.preproc_endif
    )),

    // Complete fragmented if-else including the leading #if that opens the block
    // Pattern: #if COND ... if expr then begin ... end else begin #endif ... #if COND end; #endif
    // The leading #if's #endif is consumed by the fragmented pattern itself
    preproc_wrapped_fragmented_if_else: $ => prec(25, seq(
      $.preproc_if,  // Opening #if before the if statement
      kw('if', 10),
      field('condition', $._expression),
      kw('then', 10),
      field('then_branch', $.code_block),
      kw('else', 10),
      kw('begin', 10),
      $.preproc_endif,  // This matches the opening #if
      repeat($._statement_or_preprocessor),
      $.preproc_if,
      kw('end'),
      optional(';'),
      $.preproc_endif
    )),

    // Handle if statements where the condition varies by preprocessor but body is shared
    // Pattern: #if CONDITION1 \n if (expr1) then \n #else \n if (expr2) then \n #endif \n shared_body
    preproc_variant_condition_if: $ => prec(25, seq(
      $.preproc_if,
      // First variant: if (condition1) then
      seq(
        kw('if', 10),
        field('condition_if', $._expression),
        kw('then', 10)
      ),
      // Can have multiple elif branches with different conditions
      repeat(seq(
        $.preproc_elif,
        seq(
          kw('if', 10),
          field('condition_elif', $._expression),
          kw('then', 10)
        )
      )),
      // Else branch with different condition
      optional(seq(
        $.preproc_else,
        seq(
          kw('if', 10),
          field('condition_else', $._expression),
          kw('then', 10)
        )
      )),
      $.preproc_endif,
      // Shared body after preprocessor
      field('shared_body', choice(
        $.code_block,
        $._if_then_body
      ))
    )),


    // Procedure header without body (for split procedures)
    procedure_header: $ => seq(
      optional(field('modifier', $.procedure_modifier)), 
      kw('procedure'),
      field('name', $._procedure_name),
      '(',
      optional($.parameter_list),
      ')',
      optional(choice(
        seq(
          choice(
            $._procedure_return_specification, // : ReturnType
            $._procedure_named_return // ReturnValue : ReturnType
          )
        )
      ))
    ),

    comparison_operator: $ => choice(
      '>=',
      '<=',
      '>',
      '<',
      '<>',
      '='
    ),

    parameter_list: $ => seq(
      seq(repeat($.attribute_item), $.parameter),
      repeat(seq(';', seq(repeat($.attribute_item), $.parameter)))
    ),

    modifier: $ => kw('var'),

    // Explicit identifier token
    identifier: $ => ident(),

    _quoted_identifier: $ => alias(
      token(prec(10, seq(
        '"',
        repeat1(choice(
          new RustRegex('[^"\\n]+'),
          '""'  // Escaped double quote
        )),
        '"'
      ))),
      $.quoted_identifier
    ),

    // Namespace-qualified reference for type specifications
    // Examples: Microsoft.Inventory.Tracking."Item Tracking Lines"
    //          System.DateTime
    namespace_qualified_reference: $ => prec.left(2, seq(
      field('namespace', $._identifier_choice),
      repeat1(seq(
        '.',
        field('segment', $._identifier_choice)
      ))
    )),

    string_literal: $ => token(
      choice(
        // Empty string
        seq("'", "'"),
        
        // Non-empty string - simplified to handle single backslash
        seq(
          "'",
          repeat1(choice(
            new RustRegex('[^\'\\n]+'),     // One or more chars except quote or newline (allows backslash)
            "''"           // Two consecutive single quotes as an escape
          )),
          "'"
        )
      )
    ),

    // Duration string format: [d.]hh:mm:ss[.fffffff]
    duration_string: $ => token(
      seq(
        "'",
        seq(
          // Optional days part
          optional(seq(
            /\d+/,    // days
            '.'
          )),
          /\d{1,2}/, // hours (1-2 digits)
          ':',
          /\d{2}/,   // minutes (exactly 2 digits)
          ':',
          /\d{2}/,   // seconds (exactly 2 digits)
          // Optional fractional seconds
          optional(seq(
            '.',
            /\d{1,7}/ // up to 7 digits
          ))
        ),
        "'"
      )
    ),

    clustered_property: $ => seq(
      'Clustered',
      $._boolean_property_template
    ),

    unique_property: $ => seq(
      kw('Unique'),
      $._boolean_property_template
    ),

    // Define boolean literals as tokens with precedence
    boolean: $ => choice(
      prec(1, kw('true')),
      prec(1, kw('false'))
    ),

    // Centralized boolean value rule for property definitions
    _boolean_value: $ => $.boolean,

    grid_layout_value: $ => choice(
      kw('rows'),
      kw('columns')
    ),

    temporary: $ => kw('temporary'),


    // Define code blocks with explicit keyword handling
    code_block: $ => prec.right(1, seq(
      kw('begin', 10),
      optional(repeat($._statement_or_preprocessor)),
      kw('end'),
      optional(token(';')) // Explicit token
    )),

    _statement_or_preprocessor: $ => choice(
      $._statement,
      $.preproc_conditional_statements,
      $.preproc_conditional_if_statement,
      $.preproc_wrapped_fragmented_if_else,
      $.pragma
    ),

    preproc_conditional_statements: _preproc_conditional_block_template($ => $._statement),

    _expression_statement: $ => $._expression, // New rule

    // Rule for empty statements (standalone semicolons)
    empty_statement: $ => ';',

    // Preprocessor conditional if statement where entire if structures vary
    preproc_conditional_if_statement: $ => prec(10, _preproc_conditional_block_template($ => $.if_statement)($)),

    _statement: $ => prec.right(seq(
      choice(
        // Most common statements first
        $.assignment_statement,
        $._expression_statement,
        $.if_statement,
        $.exit_statement,
        // Less common statements
        $.case_statement,
        $.for_statement,
        $.repeat_statement,
        $.while_statement,
        $.foreach_statement,
        $.with_statement,
        $.asserterror_statement,
        $.empty_statement // Least common - standalone semicolons
      ),
      optional(';')
    )),

    while_statement: $ => prec.right(seq(
      kw('while', 10),
      field('condition', $._expression),
      kw('do', 10),
      field('body', choice(
        $._statement_or_preprocessor,
        $.code_block
      ))
    )),

    with_statement: $ => prec.right(seq(
      kw('with', 10),
      field('record_variable', $._expression),
      kw('do', 10),
      field('body', choice(
        $._statement_or_preprocessor,
        $.code_block
      ))
    )),

    for_statement: $ => prec.right(seq(
      kw('for', 10),
      field('variable', choice(
        $.identifier,
        $.field_access,
        $.member_expression
      )),
      ':=',
      field('start', $._expression),
      field('direction', choice(
        prec(2, alias(kw('to'), $.to)),
        alias(kw('downto', 10), $.downto)
      )),
      field('end', $._expression),
      kw('do', 10),
      field('body', choice(
        $._statement_or_preprocessor,
        $.code_block
      ))
    )),

    foreach_statement: $ => prec.right(seq(
      kw('foreach', 10),
      field('variable', choice($.identifier, $._quoted_identifier)),
      kw('in', 10),
      field('iterable', $._expression),
      kw('do', 10),
      field('body', choice(
        $._statement_or_preprocessor,
        $.code_block
      ))
    )),

    // Removed procedure_call rule

    repeat_statement: $ => seq(
      kw('repeat', 10),
      repeat($._statement_or_preprocessor),
      kw('until', 10),
      field('condition', $._expression)
    ),

    exit_statement: $ => prec(13, seq(
      kw('exit', 10),
      optional(seq(
        token.immediate('('), // Ensure '(' immediately follows 'exit' if present
        optional(field('return_value', $._expression)),
        ')'
      )))
    ),

    asserterror_statement: $ => prec(14, choice(
      // asserterror with expression or code block
      seq(
        kw('asserterror', 10),
        field('body', choice(
          $._expression,
          $.code_block
        ))
      ),
      // Standalone asserterror; (raises last error)
      seq(kw('asserterror', 10), ';')
    )),

    assignment_statement: $ => seq(
      field('left', $._assignable_expression),
      field('operator', $._assignment_operator),
      field('right', $._expression)
    ),

    // Assignment as expression (returns the assigned value)
    assignment_expression: $ => seq(
      field('left', $._assignable_expression),
      field('operator', $._assignment_operator),
      field('right', $._expression)
    ),

    _assignable_expression: $ => $._expression,

    // Unified call expression rule
// Unified call expression rule
    call_expression: $ => prec(12, seq( // Increased precedence to 12 (higher than member_expression)
      // Function can be an identifier, member access, field access, or qualified enum value
      field('function', choice(
        $.identifier,
        $.member_expression,
        $.field_access,
        $.qualified_enum_value,
        $.enum_value_expression
      )),
      field('arguments', $.argument_list)
    )),
    
    argument_list: $ => seq(
      '(',
      optional(seq(
        $._expression,
        repeat(seq(',', $._expression))
      )),
      ')'
    ),




    _chained_expression: $ => prec(3, choice(
      $.member_expression,
      $.call_expression,
      $.field_access,
      $.qualified_enum_value_tail,
      $._quoted_identifier
    )),


    qualified_enum_value_tail: $ => prec.left(13, seq( // Higher precedence to attach to field_access
      '::',
      $._identifier_choice
    )),

    unary_expression: $ => prec.right(7, seq( // Keep at 7 but verify context
      // WARNING: 'not' must use choice() instead of kw() to avoid precedence conflicts
      field('operator', alias(choice('+', '-', choice('not', 'NOT', 'Not')), $.unary_operator)),
      field('operand', $._expression)
    )),

    _expression: $ => choice(
      // --- Binary Operators First ---
      $.range_expression,       // (prec 8)
      $.multiplicative_expression, // (prec 7) 
      $.additive_expression,    // (prec 6)
      $.comparison_expression,  // (prec 4)
      // 'in' expression (prec 5)
      prec.left(5, seq(
        field('left', $._expression),
        field('operator', $.in_operator),
        field('right', $.list_literal) // Right side is typically a list literal
      )),
      // 'is' expression (prec 5) - interface type checking
      prec.left(5, seq(
        field('left', $._expression),
        field('operator', kw('is', 5)),
        field('right', $.type_specification)
      )),
      // 'as' expression (prec 5) - interface casting
      prec.left(5, seq(
        field('left', $._expression),
        field('operator', kw('as', 5)),
        field('right', $.type_specification)
      )),
      $.logical_expression,
      $.conditional_expression,  // Add ternary operator
      // --- Other Expression Forms ---
      // Put database_reference FIRST with highest precedence for DATABASE:: patterns
      $.database_reference,
      // Put qualified_enum_value with high precedence
      prec(50, $.qualified_enum_value), // (prec 50) - moderate precedence
      // Method chains (put this first among non-binary expressions for higher precedence)
      $.call_expression, // (prec 12)
      $.enum_keyword_qualified_value, // (prec 9)
      // Add high precedence for 'enum' as identifier to prevent conflict with enum_type_reference
      prec(20, alias(kw('enum'), $.identifier)),
      $.enum_type_reference, // (prec 8)
      $.field_access,  // (prec 12)
      $.member_expression, // (prec 11)
      $.subscript_expression, // (prec 9)
      $.identifier,
      // Allow 'End' to be used as identifier in expressions
      alias(kw('end'), $.identifier),
      $._quoted_identifier,
      $._literal_value,
      $.parenthesized_expression,
      $.unary_expression, // (prec 7)
      // Assignment as expression (for asserterror and other contexts)
      prec.left(1, $.assignment_expression)
    ),

    // Explicit binary expression rules for proper precedence handling
    range_expression: $ => prec.left(8, seq(
      field('left', $._expression),
      field('operator', '..'),
      field('right', $._expression)
    )),

    multiplicative_expression: $ => prec.left(7, seq(
      field('left', $._expression),
      field('operator', choice('*', '/', choice('div', 'DIV', 'Div'), choice('mod', 'MOD', 'Mod'))),
      field('right', $._expression)
    )),

    additive_expression: $ => prec.left(6, seq(
      field('left', $._expression),
      field('operator', choice('+', '-')),
      field('right', $._expression)
    )),

    comparison_expression: $ => prec.left(4, seq(
      field('left', $._expression),
      field('operator', $.comparison_operator),
      field('right', $._expression)
    )),

    logical_expression: $ => choice(
      // Logical AND expression (prec 3)
      // WARNING: logical operators must use choice() instead of kw() to avoid expression conflicts
      prec.left(3, seq(
        field('left', $._expression),
        field('operator', choice('and', 'AND', 'And')),
        field('right', $._expression)
      )),
      // Logical OR expression (prec 2)
      prec.left(2, seq(
        field('left', $._expression),
        field('operator', choice('or', 'OR', 'Or')),
        field('right', $._expression)
      )),
      // Logical XOR expression (prec 2)
      prec.left(2, seq(
        field('left', $._expression),
        field('operator', choice('xor', 'XOR', 'Xor')),
        field('right', $._expression)
      ))
    ),

    // Conditional/ternary expression (? :)
    conditional_expression: $ => prec.right(1, seq(
      field('condition', $._expression),
      '?',
      field('then_value', $._expression),
      ':',
      field('else_value', $._expression)
    )),

    // 'in' operator
    in_operator: $ => kw('in', 5),

    // List literal for 'in' expression or other contexts
    list_literal: $ => seq(
      '[',
      optional($.expression_list), // Use existing expression_list for comma-separated expressions
      ']'
    ),

    // Rule for array indexing/subscript expressions (supports multi-dimensional arrays)
    subscript_expression: $ => prec.left(9, seq(
      field('array', $._expression),
      '[',
      field('indices', $.expression_list),
      ']'
    )),

    member_expression: $ => prec.left(11, seq( // Increased precedence to match field_access
      field('object', $._expression),
      '.',
      field('property', $._identifier_choice)
    )),

    field_access: $ => prec.left(12, seq( // Increased precedence over member_expression
      field('record', $._expression),
      '.',
      field('field', $._quoted_identifier)
    )),

    enum_value_expression: $ => prec(13, seq( // Increased precedence to beat field_access
      field('enum', choice(
        $.field_access,
        $.member_expression,
        $.identifier,
        $._quoted_identifier
      )),
      $._double__colon,
      field('enum_member', choice(
        $.identifier,
        $._quoted_identifier
      ))
    )),

    if_statement: $ => choice(
      // Normal if statement
      prec.right(seq(
        kw('if', 10),
        field('condition', $._expression),
        kw('then', 10),
        field('then_branch', choice(
          $.code_block,
          $._if_then_body
        )),
        optional(seq(
          kw('else', 10),
          field('else_branch', choice(
            $.code_block,
            prec(1, $.if_statement),
            $._if_then_body
          ))
        ))
      )),
      // Split if-else statement
      $.preproc_split_if_else,
      // Split if statement (condition in preprocessor, body outside)
      $.preproc_split_if,
      // Split if-then-begin statement (begin in preprocessor, body outside, end in preprocessor)
      $.preproc_split_if_then_begin,
      // Fragmented if-else statement (complex preprocessor pattern)
      $.preproc_fragmented_if_else,
      // If statement with variant conditions but shared body
      $.preproc_variant_condition_if
    ),

    // Helper rule for if statement bodies
    _if_then_body: $ => prec.right(seq(
      repeat($.pragma),
      choice(
        $._statement,
        $.preproc_conditional_statements
      ),
      repeat($.pragma)
    )),

    // Case expression uses the general _expression rule
    _case_expression: $ => $._expression,

    case_statement: $ => prec(2, seq(
      kw('case', 10),
      field('expression', $._case_expression),
      kw('of', 10),
      repeat($._case_item),
      optional(choice(
        $.else_branch,
        $.preproc_conditional_else_branch
      )),
      kw('end')
    )),

    _case_item: $ => choice(
      $.case_branch,
      $.preproc_conditional_case
    ),

    case_branch: $ => seq(
      field('pattern', $._case_pattern),
      $._colon,
      field('statements', choice(
        $.code_block,
        $._statement_or_preprocessor
      ))
    ),

    preproc_conditional_case: _preproc_conditional_block_template($ => $.case_branch, true),
    
    // Preprocessor conditional else branch for case statements
    preproc_conditional_else_branch: _preproc_conditional_block_template($ => $.else_branch, true),

    // _case_pattern now directly handles single or multiple patterns
    // Updated to handle pragmas that may split pattern lists
    _case_pattern: $ => choice(
      // Case 1: Multiple patterns separated by commas
      seq(
        optional(','), // Allow optional leading comma for pragma-split patterns
        $._single_pattern,
        repeat(seq(',', optional($._single_pattern))) // Make patterns optional after comma for pragma handling
      ),
      // Case 2: A single pattern element
      $._single_pattern
    ),

    // _single_pattern defines the elements allowed within a case pattern
    _single_pattern: $ => choice(
      $._literal_value,
      $.enum_value_expression, // Match the full Record.Field::Value pattern
      $.qualified_enum_value,   // Match EnumType::EnumValue pattern
      $.enum_keyword_qualified_value, // Match Enum::"EnumType"::Value pattern
      // Arithmetic expressions (high precedence for DATABASE::"Table" + 1 patterns)
      prec(11, $.additive_expression),
      prec(11, $.multiplicative_expression),
      $.database_reference, // Allow DATABASE::"Table Name" patterns
      $._chained_expression, // Allow member expressions like Value.IsInteger
      $.unary_expression, // Allow NOT expressions in case patterns
      $.call_expression, // Allow method calls like SalesLine.Type::Item.AsInteger()
      // Complex parenthesized expressions for CASE TRUE OF patterns
      prec(12, $.parenthesized_expression),
      // Boolean expressions for CASE TRUE OF patterns  
      prec(10, seq(
        field('left', $._expression),
        field('operator', $.comparison_operator),
        field('right', $._expression)
      )),
      prec(10, seq(
        field('left', $._expression),
        field('operator', choice('and', 'AND', 'And')),
        field('right', $._expression)
      )),
      prec(10, seq(
        field('left', $._expression),
        field('operator', choice('or', 'OR', 'Or')),
        field('right', $._expression)
      )),
      prec(10, seq(
        field('left', $._expression),
        field('operator', choice('xor', 'XOR', 'Xor')),
        field('right', $._expression)
      )),
      // IN expressions for CASE TRUE OF patterns like Text[i] IN ['A' .. 'Z']
      prec(10, seq(
        field('left', $._expression),
        field('operator', $.in_operator),
        field('right', $.list_literal)
      )),
      $.range_expression, // Allow range expressions like 'A'..'Z'
      $.identifier, // Keep for simple identifiers
      $._quoted_identifier // Keep for quoted identifiers
    ),


    decimal: $ => token(seq(
      optional('-'),  // Only allow negative sign
      seq(new RustRegex('\\d+'), '.', new RustRegex('\\d+'))
    )),

    integer: $ => token(seq(
      optional('-'),  // Only allow negative sign
      new RustRegex('\\d+')
    )),

    biginteger: $ => token(seq(
      optional('-'),  // Only allow negative sign
      new RustRegex('\\d+'),
      new RustRegex('[lL]')  // L suffix for BigInteger
    )),

    time_literal: $ => token(seq(
      optional('-'),
      new RustRegex('\\d+(\\.\\d+)?'),  // Allow decimal time values like 235959.999T
      new RustRegex('[tT]')
    )),

    datetime_literal: $ => token(prec(3, seq(
      optional('-'),
      new RustRegex('\\d+'),
      new RustRegex('[dD][tT]')
    ))),

    date_literal: $ => token(prec(2, seq(
      optional('-'),
      new RustRegex('\\d{1,8}'),  // Can be 0 for undefined date or yyyymmdd
      new RustRegex('[dD]')
    ))),

    // Duration in AL is just a number representing milliseconds
    // It doesn't have a special suffix, so we handle it as an integer in context

    _literal_value: $ => choice(
      $.time_literal, 
      $.datetime_literal,
      $.date_literal,
      $.biginteger,  // BigInteger literals with L suffix (e.g., 123L)
      $.integer,
      $.decimal,
      $.boolean,
      $.string_literal
    ),

    parenthesized_expression: $ => seq(
      '(',
      $._expression,
      ')'
    ),

    else_branch: $ => seq(
      kw('else', 10),
      field('statements', $._branch_statements)
    ),

    // DATABASE references (DATABASE::Customer pattern)
    database_reference: $ => prec(300, seq(  // Increased precedence to beat qualified_enum_value
      field('keyword', alias(kw('database'), 'database')),
      '::',
      field('table_name', $._identifier_choice)
    )),

    // Object type qualified references (Report::"Report Name", Page::"Page Name", etc.)
    // Uses kw_with_coloncolon to prevent standalone keywords from matching (e.g., filter(Table) should work)
    object_type_qualified_reference: $ => prec(300, seq(  // High precedence for object type patterns
      choice(
        kw_with_coloncolon('report'),
        kw_with_coloncolon('page'),
        kw_with_coloncolon('codeunit'),
        kw_with_coloncolon('table'),
        kw_with_coloncolon('xmlport'),
        kw_with_coloncolon('query')
      ),
      field('object_name', $._identifier_choice)
    )),

    // Rule for expressions using Enum keyword with double qualification (Enum::"Type"::"Value")
    enum_keyword_qualified_value: $ => prec.left(9, seq( // Increased precedence
      kw('enum'),
      field('operator1', $._double__colon),
      field('enum_type', choice(
        $._quoted_identifier,
        $.identifier
      )),
      field('operator2', $._double__colon),
      field('value', choice(
        $._quoted_identifier,
        $.identifier
      ))
    )),

    // Rule for enum type references (Enum::"Type") used for static method calls
    enum_type_reference: $ => prec.left(8, seq(
      kw('enum'),
      field('operator', $._double__colon),
      field('enum_type', choice(
        $._quoted_identifier,
        $.identifier
      ))
    )),

    qualified_enum_value: $ => prec.left(50, seq(
      field('enum_type', choice(
        $._enum_type_reference,
        $.identifier,
        $._quoted_identifier,
        $.member_expression,
        $.field_access,
        $.subscript_expression,
        $._chained_expression
      )),
      field('operator', $._double__colon),
      field('value', choice(
        $._enum_value_reference,
        $._quoted_identifier,
        $.identifier,
        $.string_literal,
        $._chained_expression
      ))
    )),

    _enum_type_reference: $ => prec.left(2, choice(
      $._quoted_identifier,
      $.identifier,
      $._chained_expression
    )),

    _enum_value_reference: $ => prec.left(10, choice( // Increase precedence
      $._enum_keyword,  // Put keywords first with higher precedence
      $._quoted_identifier,
      $.identifier,
      $._chained_expression,
      $.string_literal
    )),

    _branch_statements: $ => choice(
      $._statement,
      $.code_block,
      $.preproc_conditional_statements
    ),

    fieldgroup_declaration: $ => seq(
      kw('fieldgroup', 10),
      '(',
      field('group_type', $.identifier),
      ';',
      field('fields', $.fieldgroup_list),
      ')',
      optional(seq(
        '{',
        repeat(choice(
          $.caption_property,
          $.property
        )),
        '}'
      ))
    ),

    fieldgroups_section: $ => prec(3, seq(
      kw('fieldgroups'),
      '{',
      repeat(choice(
        $.fieldgroup_declaration,
        $.fieldgroup_modification,
        $.preproc_conditional_fieldgroups
      )),
      '}'
    )),

    preproc_conditional_fieldgroups: _preproc_conditional_block_template($ => choice(
      $.fieldgroup_declaration,
      $.fieldgroup_modification,
      $.preproc_conditional_fieldgroups
    )),

    fieldgroup_modification: $ => choice(
      $.addfirst_fieldgroup,
      $.addlast_fieldgroup,
      $.addafter_fieldgroup,
      $.addbefore_fieldgroup
    ),

    addfirst_fieldgroup: $ => seq(
      kw('addfirst'),
      '(',
      field('group_type', $.identifier),
      ';',
      field('fields', $.fieldgroup_list),
      ')',
      optional(seq(
        '{',
        '}'
      ))
    ),

    addlast_fieldgroup: $ => seq(
      kw('addlast'),
      '(',
      field('group_type', $.identifier),
      ';',
      field('fields', $.fieldgroup_list),
      ')',
      optional(seq(
        '{',
        '}'
      ))
    ),

    addafter_fieldgroup: $ => seq(
      kw('addafter'),
      '(',
      field('group_type', $.identifier),
      ';',
      field('target', $._identifier_choice),
      ';',
      field('fields', $.fieldgroup_list),
      ')',
      optional(seq(
        '{',
        '}'
      ))
    ),

    addbefore_fieldgroup: $ => seq(
      kw('addbefore'),
      '(',
      field('group_type', $.identifier),
      ';',
      field('target', $._identifier_choice),
      ';',
      field('fields', $.fieldgroup_list),
      ')',
      optional(seq(
        '{',
        '}'
      ))
    ),

    fieldgroup_list: $ => seq(
      $.fieldgroup_field,
      repeat(seq(',', $.fieldgroup_field))
    ),

    fieldgroup_field: $ => choice(
      $.identifier,
      $._quoted_identifier
    ),


    update_propagation_property: $ => seq(
      'UpdatePropagation',
      '=',
      field('value', $.update_propagation_value),
      ';'
    ),

    update_propagation_value: $ => choice(
      kw('no'),
      kw('updated'),
      kw('both'),
      $.string_literal,
      $.identifier,
      $._quoted_identifier
    ),

    cuegroup_layout_property: $ => seq(
      kw('CueGroupLayout', 10),
      '=',
      field('value', $._flexible_identifier_choice),
      ';'
    ),

    freeze_column_property: $ => seq(
      'FreezeColumn',
      '=',
      field('value', $._flexible_identifier_choice),
      ';'
    ),

    indentation_column_property: $ => seq(
      kw('IndentationColumn'),
      $._expression_property_template
    ),

    indentation_controls_property: $ => seq(
      kw('IndentationControls'),
      '=',
      field('value', choice(
        $._expression,
        seq($._expression, repeat(seq(',', $._expression)))
      )),
      ';'
    ),

    allowed_file_extensions_property: $ => seq(
      'AllowedFileExtensions',
      '=',
      field('value', seq(
        $.string_literal,
        repeat(seq(',', $.string_literal))
      )),
      ';'
    ),

    allow_multiple_files_property: $ => seq(
      'AllowMultipleFiles',
      $._boolean_property_template
    ),

    file_upload_action_property: $ => seq(
      'FileUploadAction',
      '=',
      field('value', $._flexible_identifier_choice),
      ';'
    ),

    file_upload_row_action_property: $ => seq(
      'FileUploadRowAction',
      '=',
      field('value', $._flexible_identifier_choice),
      ';'
    ),

    custom_action_type_property: $ => seq(
      kw('CustomActionType', 10),
      '=',
      field('value', $._identifier_choice),
      ';'
    ),

    flow_template_category_name_property: $ => seq(
      kw('FlowTemplateCategoryName'),
      '=',
      field('value', $.string_literal),
      ';'
    ),

    flow_environment_id_property: $ => seq(
      kw('FlowEnvironmentId'),
      '=',
      field('value', $.string_literal),
      ';'
    ),

    flow_caption_property: $ => seq(
      kw('FlowCaption'),
      '=',
      field('value', $.string_literal),
      ';'
    ),

    flow_id_property: $ => seq(
      kw('FlowId'),
      '=',
      field('value', $.string_literal),
      ';'
    ),

    flow_template_id_property: $ => seq(
      kw('FlowTemplateId'),
      '=',
      field('value', $.string_literal),
      ';'
    ),

    odata_edm_type_property: $ => seq(
      'ODataEDMType',
      '=',
      field('value', $._flexible_identifier_choice),
      ';'
    ),

    // Missing page properties - Clear operations
    clear_actions_property: $ => seq(
      'ClearActions',
      $._boolean_property_template
    ),

    clear_layout_property: $ => seq(
      'ClearLayout',
      $._boolean_property_template
    ),

    clear_views_property: $ => seq(
      'ClearViews',
      $._boolean_property_template
    ),

    // ShowAs property (different from ShowAsTree)
    show_as_property: $ => seq(
      'ShowAs',
      '=',
      field('value', choice(
        kw('splitbutton'),  // SplitButton
        kw('menu'),         // Menu
        kw('button'),       // Button
        kw('standard')      // Standard
      )),
      ';'
    ),

    // Low priority properties
    importance_additional_property: $ => seq(
      kw('importanceadditional'),
      $._boolean_property_template
    ),

    include_caption_property: $ => seq(
      kw_with_eq('includecaption'),
      field('value', $._boolean_value),
      ';'
    ),

    // Critical report layout properties
    default_layout_property: $ => seq(
      kw('defaultlayout'),
      '=',
      field('value', $.identifier),  // Values like RDLC, Word, Excel
      ';'
    ),

    default_rendering_layout_property: $ => seq(
      'DefaultRenderingLayout',
      '=',
      field('value', $._flexible_identifier_choice),
      ';'
    ),

    excel_layout_property: $ => seq(
      'ExcelLayout',
      '=',
      field('value', $._flexible_identifier_choice),
      ';'
    ),

    rdlc_layout_property: $ => seq(
      'RDLCLayout',
      '=',
      field('value', $._flexible_identifier_choice),
      ';'
    ),

    word_layout_property: $ => seq(
      'WordLayout',
      '=',
      field('value', $._flexible_identifier_choice),
      ';'
    ),

    // High priority report properties
    allow_scheduling_property: $ => seq(
      'AllowScheduling',
      $._boolean_property_template
    ),

    preview_mode_property: $ => seq(
      'PreviewMode',
      '=',
      field('value', choice(
        kw('normal'),        // Normal
        kw('printlayout'),  // PrintLayout
        kw('none')                 // None
      )),
      ';'
    ),

    show_print_status_property: $ => seq(
      'ShowPrintStatus',
      $._boolean_property_template
    ),

    transaction_type_property: $ => seq(
      'TransactionType',
      '=',
      field('value', choice(
        kw('update'),        // Update
        kw('updatenolocks'), // UpdateNoLocks
        kw('snapshot'), // Snapshot
        kw('browse')          // Browse
      )),
      ';'
    ),

    execution_timeout_property: $ => seq(
      kw('ExecutionTimeout'),
      '=',
      field('value', $.duration_string),
      ';'
    ),

    format_region_property: $ => seq(
      'FormatRegion',
      '=',
      field('value', $._flexible_identifier_choice),
      ';'
    ),

    use_system_printer_property: $ => seq(
      'UseSystemPrinter',
      $._boolean_property_template
    ),

    maximum_dataset_size_property: $ => seq(
      'MaximumDatasetSize',
      $._integer_property_template
    ),

    // Table external/integration properties
    optimize_for_text_search_property: $ => seq(
      choice('optimizefortextsearch', 'OptimizeForTextSearch', 'OPTIMIZEFORTEXTSEARCH'),
      $._boolean_property_template
    ),

    // Medium priority report properties
    enable_external_assemblies_property: $ => seq(
      'EnableExternalAssemblies',
      $._boolean_property_template
    ),

    enable_external_images_property: $ => seq(
      'EnableExternalImages',
      $._boolean_property_template
    ),

    enable_hyperlinks_property: $ => seq(
      'EnableHyperlinks',
      $._boolean_property_template
    ),

    excel_layout_multiple_data_sheets_property: $ => seq(
      'ExcelLayoutMultipleDataSheets',
      $._boolean_property_template
    ),

    maximum_document_count_property: $ => seq(
      'MaximumDocumentCount',
      $._integer_property_template
    ),

    paper_source_default_page_property: $ => seq(
      'PaperSourceDefaultPage',
      '=',
      field('value', $._flexible_identifier_choice),
      ';'
    ),

    paper_source_first_page_property: $ => seq(
      'PaperSourceFirstPage',
      '=',
      field('value', $._flexible_identifier_choice),
      ';'
    ),

    paper_source_last_page_property: $ => seq(
      'PaperSourceLastPage',
      '=',
      field('value', $._flexible_identifier_choice),
      ';'
    ),

    // Low priority report properties
    pdf_font_embedding_property: $ => seq(
      'PdfFontEmbedding',
      '=',
      field('value', choice(
        kw('yes'),                    // Yes
        kw('no'),                       // No
        kw('nonstandard') // NonStandard
      )),
      ';'
    ),

    print_only_if_detail_property: $ => seq(
      kw('printonlyifdetail'),
      $._boolean_property_template
    ),

    word_merge_data_item_property: $ => seq(
      'WordMergeDataItem',
      '=',
      field('value', $._flexible_identifier_choice),
      ';'
    ),

    data_item_link_reference_property: $ => seq(
      kw('DataItemLinkReference'),
      '=',
      field('value', $._flexible_identifier_choice),
      ';'
    ),

    title_property: $ => seq(
      'Title',
      $._boolean_property_template
    ),

    // Uses kw_with_eq to distinguish property from variable name
    filters_property: $ => seq(
      alias(kw_with_eq('filters'), 'Filters'),
      field('value', choice(
        $.identifier,
        $._quoted_identifier,
        $.string_literal,
        $.simple_filter_expression
      )),
      ';'
    ),

    // CONSOLIDATED: Removing duplicate - use the more comprehensive one above

    ellipsis_property: $ => seq(
      'Ellipsis',
      $._boolean_property_template
    ),

    gesture_property: $ => seq(
      'Gesture',
      '=',
      field('value', $._flexible_identifier_choice),
      ';'
    ),

    is_header_property: $ => seq(
      'IsHeader',
      $._boolean_property_template
    ),

    provider_property: $ => seq(
      'Provider',
      '=',
      field('value', $._flexible_identifier_choice),
      ';'
    ),


    // shared_layout_property: duplicate definition removed - using the case-insensitive version above

    data_item_table_view_property: $ => seq(
      'DataItemTableView',
      '=',
      field('value', $.source_table_view_value),
      ';'
    ),

    max_iteration_property: $ => seq(
      kw('maxiteration'),
      $._integer_property_template
    ),



    // Preprocessor conditional rules for layout sections
    preproc_conditional_layout: _preproc_conditional_block_template($ => $._layout_element),

    // Preprocessor conditional rules for group content (properties or layout elements)
    preproc_conditional_group_content: _preproc_conditional_block_template($ => choice(
      $._page_properties,
      $._layout_element
    )),

    // Preprocessor conditional rules for properties
    preproc_conditional_properties: _preproc_conditional_block_template($ => $._page_properties),

    // Preprocessor conditional rules for object-level properties
    preproc_conditional_object_properties: _preproc_conditional_block_template($ => $.property),

    // Preprocessor conditional rules for table properties
    preproc_conditional_table_properties: _preproc_conditional_block_template($ => $._table_properties),

    // Preprocessor conditional rules for page properties
    preproc_conditional_page_properties: _preproc_conditional_block_template($ => $._page_properties),

    // Preprocessor conditional rules for report properties
    preproc_conditional_report_properties: _preproc_conditional_block_template($ => $._report_properties),

    // Preprocessor conditional rules for report columns
    preproc_conditional_report_columns: _preproc_conditional_block_template($ => $.report_column_section),

    // Preprocessor conditional rules for xmlport properties
    preproc_conditional_xmlport_properties: _preproc_conditional_block_template($ => $._xmlport_properties),

    // Preprocessor conditional rules for query properties
    preproc_conditional_query_properties: _preproc_conditional_block_template($ => choice($._universal_properties, $._query_properties, $.property_list)),

    // Preprocessor conditional rules for enum properties
    preproc_conditional_enum_properties: _preproc_conditional_block_template($ => $._enum_properties),

    // Preprocessor conditional rules for enum values
    preproc_conditional_enum_values: _preproc_conditional_block_template($ => $.enum_value_declaration),

    // Preprocessor conditional rules for mixed enum content (properties and values together)
    preproc_conditional_enum_content: $ => seq(
      $.preproc_if,
      repeat(choice(
        $._enum_properties,
        $.enum_value_declaration
      )),
      repeat(seq(
        $.preproc_elif,
        repeat(choice(
          $._enum_properties,
          $.enum_value_declaration
        ))
      )),
      optional(seq(
        $.preproc_else,
        repeat(choice(
          $._enum_properties,
          $.enum_value_declaration
        ))
      )),
      $.preproc_endif
    ),

    // Preprocessor conditional rules for permissionset properties and permissions
    preproc_conditional_permissionset_properties: _preproc_conditional_block_template($ => choice(
      $._permissionset_properties,
      $.permissionset_permissions
    )),

    // Preprocessor conditional rules for controladdin properties
    preproc_conditional_controladdin_properties: _preproc_conditional_block_template($ => choice($._controladdin_properties, $.property_list)),

    preproc_conditional_controladdin_elements: _preproc_conditional_block_template($ => choice(
      $.attribute_item,
      $._controladdin_properties,
      $.controladdin_event,
      $.controladdin_procedure,
      $.property_list,
      $.preproc_conditional_controladdin_elements  // Allow nesting
    )),

    preproc_conditional_entitlement_properties: _preproc_conditional_block_template($ => choice($._entitlement_properties, $.property_list)),

    // Preprocessor conditional rules for profile properties
    preproc_conditional_profile_properties: _preproc_conditional_block_template($ => $._profile_properties),
    
    // Preprocessor conditional rules for XMLPort table elements
    preproc_conditional_xmlport_elements: _preproc_conditional_block_template($ => choice(
      $.xmlport_table_property,
      $.xmlport_table_element,
      $.xmlport_field_attribute,
      $.xmlport_text_attribute,
      $.named_trigger,
      $.trigger_declaration
    )),

    // Preprocessor conditional rules for actions
    preproc_conditional_actions: _preproc_conditional_block_template($ => choice(
        $._action_element,
        $._action_group,
        $.action_group_section,
        $.area_action_section,
        $.separator_action
      )),

    // Preprocessor conditional rules for action properties
    preproc_conditional_action_properties: _preproc_conditional_block_template($ => choice(
        $._action_property,
        ';'
      )),

    // Preprocessor conditional rules for variable declarations
    preproc_conditional_variables: _preproc_conditional_block_template($ => choice(
        // Bare variable declaration (no attributes) - prefer within preproc var blocks
        prec.dynamic(3, $.variable_declaration),
        // Attributed variable (requires at least one attribute)
        prec.dynamic(3, seq(
          repeat1($.attribute_item),
          repeat(choice($.comment, $.multiline_comment, $.pragma)),
          $.variable_declaration
        )),
        $.comment,
        $.multiline_comment,
        $.pragma,
        $.var_section  // Allow nested var sections (including protected var) inside preprocessor conditionals
      )),

    preproc_conditional_field_properties: _preproc_conditional_block_template($ => $._field_properties),

    preproc_conditional_fields: _preproc_conditional_block_template($ => choice(
      $.field_declaration,
      $.modify_field_declaration
    )),

    preproc_if: $ => seq(
      choice('#if', '#IF', '#If'),
      field('condition', choice(
        $.identifier,
        $.preproc_not_expression
      ))
    ),

    preproc_not_expression: $ => seq(
      choice('not', 'NOT', 'Not'),
      $.identifier
    ),

    preproc_else: $ => choice('#else', '#ELSE', '#Else'),

    preproc_elif: $ => seq(
      choice('#elif', '#ELIF', '#Elif'),
      field('condition', choice(
        $.identifier,
        $.preproc_not_expression
      ))
    ),

    preproc_endif: $ => choice('#endif', '#ENDIF', '#Endif'),

    preproc_conditional_using: $ => prec(1, seq(
      $.preproc_if,
      repeat($.using_statement),
      optional(seq(
        $.preproc_else,
        repeat($.using_statement)
      )),
      $.preproc_endif
    )),

    pragma: $ => new RustRegex('#pragma[^\\n\\r]*'),

    preproc_region: $ => new RustRegex('(?i)#\\s*region[^\\n\\r]*'),

    preproc_endregion: $ => new RustRegex('(?i)#\\s*endregion[^\\n\\r]*'),

    comment: $ => token(seq('//', new RustRegex('[^\\n\\r]*'))),

    multiline_comment: $ => token(seq(
      '/*',
      new RustRegex('[^*]*\\*+([^/*][^*]*\\*+)*'),
      '/'
    )),

    // AL keywords that can be used as enum values
    // Comprehensive list covering object types, data types, control flow, and other common keywords
    _enum_keyword: $ => choice(
      // Object types
      kw('Table'),
      kw('Page'),
      kw('Report'),
      kw('Codeunit'),
      kw('Query'),
      kw('XMLport'),
      kw('Enum'),
      kw('Interface'),
      kw('ControlAddin'),
      
      // Data types
      kw('Code'),
      kw('Integer'),
      kw('Decimal'),
      kw('Boolean'),
      kw('Date'),
      kw('Time'),
      kw('DateTime'),
      kw('Guid'),
      kw('Blob'),
      kw('BigInteger'),
      kw('Option'),
      kw('Record'),
      
      // Control flow keywords
      kw('If'),
      kw('Then'),
      kw('Else'),
      kw('While'),
      kw('For'),
      kw('Repeat'),
      kw('Until'),
      kw('Case'),
      kw('Of'),
      kw('Exit'),
      kw('Break'),
      
      // Visibility and scope
      kw('Local'),
      kw('Global'),
      kw('Protected'),
      kw('Internal'),
      kw('Public'),
      
      // Boolean values
      kw('True'),
      kw('False'),
      
      // Operators
      kw('And'),
      kw('Or'),
      kw('Xor'),
      kw('Not'),
      kw('Div'),
      kw('Mod'),
      
      // Other common keywords
      kw('Var'),
      kw('Procedure'),
      kw('Function'),
      kw('Trigger'),
      kw('Begin'),
      kw('End'),
      kw('With'),
      kw('Do')
    ),

    // Page customization elements
    _pagecustomization_element: $ => choice(
      $.views_customization_section,
      $.layout_section,
      $.actions_section
    ),

    views_customization_section: $ => seq(
      kw('views'),
      '{',
      repeat($._views_modification),
      '}'
    ),

    _views_modification: $ => choice(
      $.addfirst_views,
      $.addlast_views,
      $.addafter_views,
      $.addbefore_views
    ),

    addfirst_views: $ => _modification_without_target_template(
      'addfirst',
      $.view_definition
    )($),

    addlast_views: $ => _modification_without_target_template(
      'addlast',
      $.view_definition
    )($),

    addafter_views: $ => _modification_with_target_template(
      'addafter',
      $.view_definition
    )($),

    addbefore_views: $ => _modification_with_target_template(
      'addbefore',
      $.view_definition
    )($),

    view_definition: $ => seq(
      'view',
      '(',
      field('name', $._identifier_choice),
      ')',
      '{',
      repeat($._view_property),
      '}'
    ),

    _view_property: $ => choice(
      $.view_caption_property,
      $.caption_ml_property,
      $.view_filters_property,
      $.view_order_by_property,
      $.shared_layout_property,
      $.visible_property
    ),


    // Profile elements
    _profile_element: $ => choice(
      $._profile_properties,                  // Centralized properties
      $.preproc_conditional_profile_properties
      // Removed property_list to avoid conflicts
    ),

    // CONSOLIDATED: profile_description_property → description_property

    profile_rolecenter_property: $ => seq(
      kw('rolecenter'),
      '=',
      field('value', choice(
        $.integer,
        $._identifier_choice
      )),
      ';'
    ),

    // CONSOLIDATED: profile_caption_property -> caption_property

    profile_customizations_property: $ => seq(
      kw('customizations', 10),
      '=',
      field('value', optional($.customizations_list)),
      ';'
    ),

    customizations_list: $ => seq(
      $._identifier_choice,
      repeat(seq(',', $._identifier_choice))
    ),

    // CONSOLIDATED: profile_enabled_property → enabled_property

    profile_description_property2: $ => seq(
      'ProfileDescription',
      $._string_property_template
    ),

    // CONSOLIDATED: profile_promoted_property → promoted_property

    // =============================================================================
    // CENTRALIZED PROPERTY CATEGORIES
    // =============================================================================
    // Semantic property organization for DRY principle and easier maintenance

    // Universal properties - apply to most AL object types
    _universal_properties: $ => choice(
      // Core metadata properties
      $.caption_property,
      $.caption_ml_property,
      $.caption_class_property,
      $.description_property,
      $.application_area_property,
      $.tool_tip_property,
      $.tool_tip_ml_property,
      $.obsolete_reason_property,
      $.obsolete_state_property,
      $.obsolete_tag_property,
      $.usage_category_property,
      $.subtype_property,
      
      // Help and documentation properties
      $.about_title_property,
      $.about_text_property,
      $.about_title_ml_property,
      $.about_text_ml_property,
      $.context_sensitive_help_page_property,
      $.additional_search_terms_property,
      $.additional_search_terms_ml_property,
      $.help_link_property,
      
      // User interface text properties
      $.instructional_text_property,
      $.instructional_text_ml_property,
      
      // Data access properties
      $.data_access_intent_property,
      
      // Scope and extensibility properties
      $.scope_property,
      $.extensible_property,
    ),

    // Display/UI control properties
    _display_properties: $ => choice(
      $.visible_property,             // Element visibility
      $.enabled_property,             // Interaction enabled state
      $.editable_property,           // Edit permission
      $.style_property,              // Visual styling
      $.style_expr_property,         // Dynamic styling
      $.width_property,              // Element width
      $.row_span_property,           // Grid row spanning
      $.column_span_property,        // Grid column spanning
      $.freeze_column_property,      // Column freezing in repeaters
      $.indentation_column_property, // Column indentation in repeaters
      $.indentation_controls_property, // Controls to indent in repeaters
      $.grid_layout_property,        // Grid layout direction (Rows/Columns)
      $.importance_property,         // Priority/emphasis level
      $.show_caption_property,       // Caption visibility
      $.show_as_tree_property,       // Tree-style presentation
      $.tree_initial_state_property,  // Initial tree expansion state
      $.show_mandatory_property,     // Mandatory field indication
      $.multi_line_property,         // Multi-line text support
      $.hide_value_property,         // Value masking (e.g., passwords)
    ),

    // Data validation properties
    _validation_properties: $ => choice(
      $.min_value_property,          // Minimum allowed value
      $.max_value_property,          // Maximum allowed value
      $.not_blank_property,          // Required field validation
      $.numeric_property,            // Numeric input only
      $.decimal_places_property,     // Decimal precision
      $.blank_zero_property,         // Display blank for zero
      $.blank_numbers_property,     // Blank number display rules
      $.unique_property,             // Uniqueness constraint
      $.values_allowed_property,     // Enumerated valid values
      $.validate_table_relation_property, // FK validation
      $.char_allowed_property,       // Character input restrictions
      $.date_formula_property,       // Date formula validation
      $.closing_dates_property,      // Allow closing date selection
      $.allow_in_customizations_property, // Control field availability in customizations
    ),

    // Data source/relationship properties
    _data_properties: $ => choice(
      $.source_expr_property,        // Data source expression
      $.table_relation_property,     // Foreign key relationship
      $.calc_fields_property,        // Calculated field definition
      $.calc_formula_property,       // Calculation formula
      $.lookup_property,             // Lookup behavior
      $.auto_format_expression_property, // Format expression
      $.auto_format_type_property,   // Format type
      $.auto_increment_property,     // Auto-increment behavior
      $.field_class_property,        // Field classification
      $.init_value_property,         // Default value
      $.sql_data_type_property,      // SQL data type mapping
      $.sql_timestamp_property,      // SQL timestamp behavior
      $.test_table_relation_property, // Test table relation validation
      $.compressed_property,         // Field compression behavior
      $.external_access_property,    // External access control for fields
    ),

    // Navigation/interaction properties
    _navigation_properties: $ => choice(
      $.lookup_pageid_property,      // Lookup page reference
      $.drilldown_pageid_property,   // Drill-down page reference
      $.navigation_page_id_property, // Navigation target
      $.run_object_property,         // Action target object
      $.run_page_link_property,      // Page link parameters
      $.run_page_view_property,      // Page view/filter to apply
      $.run_form_link_type_property, // Link type for forms
      $.shortcut_key_property,       // Keyboard shortcut
      $.card_page_id_property,       // Associated card page
    ),

    // Access control properties
    _access_properties: $ => choice(
      $.access_property,             // Access level
      $.inherent_permissions_property, // Built-in permissions
      $.inherent_entitlements_property, // Built-in entitlements
      $.test_permissions_property,   // Test environment permissions
      $.access_by_permission_property, // General access by permission (used in actions)
      // Note: Pages use access_by_permission_page_property; other objects use access_by_permission_property
      // Note: permissions_property is added to specific objects that support tabledata permissions
    ),

    // Object-specific properties that are unique to specific object types
    // These only make sense in particular contexts and cannot be universally applied
    _page_specific_properties: $ => choice(
      $.page_type_property,          // Page type (List, Card, etc.)
      $.source_table_property,       // Source table reference
    ),

    _codeunit_specific_properties: $ => choice(
      $.table_no_property,           // Associated table
      $.single_instance_property,    // Singleton pattern
      $.event_subscriber_instance_property, // Event handling
    ),
    
    _table_specific_properties: $ => choice(
      $.table_type_property,         // Table type (Normal, Temporary, etc.)
      $.data_per_company_property,   // Multi-tenancy support
      $.replicate_data_property,     // Replication settings
    ),
    
    _report_specific_properties: $ => choice(
      $.processing_only_property,    // Processing-only report
      $.use_request_page_property,   // Request page usage
    ),
    
    _object_specific_properties: $ => choice(
      $._page_specific_properties,
      $._codeunit_specific_properties,
      $._table_specific_properties,
      $._report_specific_properties,
    ),

    // Query-specific properties that are unique to query objects
    _query_properties: $ => choice(
      $.permissions_property,        // Query-level tabledata permissions
      $.query_type_property,         // Query type (Normal, API, Filter)
      $.read_state_property,         // Read state (ReadCommitted, ReadUncommitted)
      $.query_category_property,     // Query categorization
      $.order_by_property,           // Order by clause
      $.top_number_of_rows_property, // Top number of rows to return
      // API-specific properties
      $.entity_caption_property,     // API entity caption
      $.entity_caption_ml_property,  // API entity caption (multi-language)
      $.entity_name_property,        // API entity name
      $.entity_set_caption_property, // API entity set caption
      $.entity_set_caption_ml_property, // API entity set caption (multi-language)
      $.entity_set_name_property,    // API entity set name
      $.api_group_property,          // API group
      $.api_publisher_property,      // API publisher
      $.api_version_property,        // API version
    ),

    // PermissionSet-specific properties that are unique to permissionset objects
    _permissionset_properties: $ => choice(
      $._universal_properties,       // caption, description, obsolete_*
      $._access_properties,         // access, permissions, inherent_*
      // PermissionSet-specific
      $.assignable_property,
      $.included_permission_sets_property,
      $.excluded_permission_sets_property,
    ),

    // ControlAddIn-specific properties that are unique to controladdin objects
    _controladdin_properties: $ => choice(
      $._universal_properties,       // caption, description, obsolete_*, application_area
      // ControlAddIn-specific
      $.controladdin_property,
    ),

    // Entitlement-specific properties that are unique to entitlement objects
    _entitlement_properties: $ => choice(
      $._universal_properties,       // caption, description, obsolete_*
      // Entitlement-specific
      $.entitlement_type_property,
      $.entitlement_role_type_property,
      $.entitlement_id_property,
      $.entitlement_group_name_property,
      $.object_entitlements_property,
    ),

    // Profile-specific properties that are unique to profile objects
    _profile_properties: $ => choice(
      // All profile-relevant properties in one place to avoid conflicts
      $.description_property,
      $.caption_property,
      $.profile_rolecenter_property,
      $.profile_customizations_property,
      $.profile_description_property2,
      $.promoted_property,
      $.enabled_property,
      $.visible_property,
      $.obsolete_state_property,
      $.obsolete_reason_property,
      $.obsolete_tag_property,
      $.application_area_property,
      $.tool_tip_property,
      $.tool_tip_ml_property
    ),

    // Enum-specific properties that are unique to enum objects
    _enum_properties: $ => choice(
      $._universal_properties,       // caption, description, obsolete_*, application_area
      $._access_properties,         // access, permissions, inherent_*
      // Enum-specific
      $.assignment_compatibility_property,
      $.implementation_property,    // Interface implementations
      $.default_implementation_property, // Default interface implementation
      $.unknown_value_implementation_property, // Unknown value interface implementation
    ),

    // Composed property groups for different object contexts
    _field_properties: $ => choice(
      $._universal_properties,
      $._display_properties,
      $._validation_properties,
      $._data_properties,
      $._navigation_properties,
      $._access_properties,           // Access property for fields
      $.field_trigger_declaration,   // Field-specific triggers
      // Field-specific additional properties
      $.assist_edit_property,
      $.quick_entry_property,
      $.option_caption_property,
      $.option_caption_ml_property,
      $.option_members_property,
      $.option_ordinal_values_property,
      $.sign_displacement_property,
      $.data_classification_property,
      $.title_property,
      $.extended_datatype_property,
      // AboutTitleML and AboutTextML are now in _universal_properties
      $.odata_edm_type_property,
      $.drill_down_property,
      $.image_property,              // Image property for field icons
      $.optimize_for_text_search_property,  // Field-level text search optimization
      $.moved_from_property,  // Add MovedFrom property for fields
      $.moved_to_property,    // Add MovedTo property for fields
      $.external_type_property,  // External type mapping for fields
      $.external_name_property,  // External name mapping for fields
      $.preproc_conditional_field_properties,
      $.empty_statement,  // Allow standalone semicolons in field property lists
    ),

    // Composed property group for page-level properties
    // This replaces the scattered page property list in _page_element
    _page_properties: $ => choice(
      $._universal_properties,
      $._display_properties,
      $._access_properties,
      $._navigation_properties,
      $._object_specific_properties,
      $.permissions_property,        // Page-level tabledata permissions
      
      // API properties needed in parts
      $.multiplicity_property,
      $.entity_name_property,
      $.entity_set_name_property,
      
      // Page-specific data management properties
      $.data_caption_expression_property,
      $.data_caption_fields_property,
      
      // Page behavior properties
      $.delete_allowed_property,
      $.insert_allowed_property,
      $.modify_allowed_property,
      $.source_table_temporary_property,
      $.analysis_mode_enabled_property,
      $.auto_split_key_property,
      $.change_tracking_allowed_property,
      $.delayed_insert_property,
      $.links_allowed_property,
      $.multiple_new_lines_property,
      $.populate_all_fields_property,
      
      // Page UI properties
      $.image_property,
      // AboutTextML and AboutTitleML are now in _universal_properties
      
      // Page workflow properties
      $.prompt_mode_property,
      $.refresh_on_activate_property,
      $.save_values_property,
      $.show_filter_property,
      
      // Page inheritance and layout properties
      $.clear_actions_property,
      $.clear_layout_property,
      $.clear_views_property,
      $.show_as_property,
      $.importance_additional_property,
      $.include_caption_property,
      $.cuegroup_layout_property,
      
      // Web service properties
      $.entity_caption_property,
      $.entity_caption_ml_property,
      $.entity_name_property,
      $.entity_set_caption_property,
      $.entity_set_caption_ml_property,
      $.entity_set_name_property,
      $.odata_key_fields_property,
      $.api_version_property,
      $.api_group_property,
      $.api_publisher_property,
      $.multiplicity_property,
      
      // Help and documentation properties
      $.is_preview_property,
      
      // Page action properties
      $.promoted_property,
      $.promoted_category_property,
      $.promoted_only_property,
      $.promoted_is_big_property,
      $.promoted_action_categories_property,
      
      // Page part properties
      $.provider_property,
      $.sub_page_link_property,
      $.sub_page_view_property,
      $.update_propagation_property,
      
      // Query and filter properties
      $.query_category_property,
      $.filters_property,
      $.order_by_property,
      $.shared_layout_property,
      $.data_item_table_view_property,
      
      // Field-specific properties needed in page modify blocks
      $.quick_entry_property,
      
      // Note: access_by_permission_property is now in _access_properties for universal use
    ),

    // Composed property group for table-level properties
    // This replaces the scattered table property list in _table_element
    _table_properties: $ => choice(
      $._universal_properties,
      $._access_properties,
      $._navigation_properties,
      $._object_specific_properties,
      $.permissions_property,        // Table-level tabledata permissions
      
      // Table-specific data management properties
      $.data_caption_fields_property,
      $.column_store_index_property,
      $.compression_type_property,
      // Note: data_per_company_property, replicate_data_property, and table_type_property are in _object_specific_properties
      
      // Table metadata properties
      $.external_schema_property,
      $.paste_is_valid_property,
      $.external_name_property,
      // Note: table_type_property is already included in _object_specific_properties
      
      // Table relationship properties
      $.moved_from_property,
      $.moved_to_property,
      $.linked_in_transaction_property,
      $.linked_object_property,
      
      // Table-specific classification
      $.data_classification_property,
      
      // Table external/integration properties
      $.optimize_for_text_search_property,
    ),

    // Composed property group for codeunit-level properties
    _codeunit_properties: $ => choice(
      $._universal_properties,
      $._access_properties,
      $._navigation_properties,
      $._object_specific_properties,
      $.permissions_property,        // Codeunit-level tabledata permissions
      
      // Additional codeunit-specific properties not in other groups
      $.test_isolation_property,
      $.test_http_request_policy_property
    ),

    // Composed property group for report-level properties
    // This replaces the scattered report property list in _report_element
    _report_properties: $ => choice(
      $._universal_properties,
      $._access_properties,
      $._object_specific_properties,
      $.permissions_property,        // Report-level tabledata permissions
      
      // Report-specific properties
      
      // Report layout properties (critical)
      $.default_layout_property,
      $.default_rendering_layout_property,
      $.excel_layout_property,
      $.rdlc_layout_property,
      $.word_layout_property,
      
      // Report execution properties
      $.allow_scheduling_property,
      $.preview_mode_property,
      $.show_print_status_property,
      $.transaction_type_property,
      $.execution_timeout_property,
      $.format_region_property,
      $.use_system_printer_property,
      $.maximum_dataset_size_property,
      
      // Report external features
      $.enable_external_assemblies_property,
      $.enable_external_images_property,
      $.enable_hyperlinks_property,
      $.excel_layout_multiple_data_sheets_property,
      $.maximum_document_count_property,
      
      // Report print settings
      $.paper_source_default_page_property,
      $.paper_source_first_page_property,
      $.paper_source_last_page_property,
      $.pdf_font_embedding_property,
      $.print_only_if_detail_property,
      
      // Report data item properties
      $.word_merge_data_item_property,
      $.data_item_link_reference_property,
      
      // Note: processing_only_property and use_request_page_property are in _object_specific_properties
    ),

    // Report dataitem-specific properties
    _dataitem_properties: $ => choice(
      $._universal_properties,
      $.data_item_table_filter_property,
      $.data_item_table_view_property,
      $.max_iteration_property,
      $.data_item_link_property,
      $.data_item_link_reference_property,
      $.request_filter_fields_property,
      $.request_filter_heading_property,
      $.print_only_if_detail_property,
      $.sql_join_type_property,
      $.use_temporary_property,
      $.calc_fields_property,
    ),

    // Report column-specific properties
    _report_column_properties: $ => choice(
      // Column appearance properties
      $.include_caption_property,
      $.caption_property,
      
      // Column formatting properties
      $.auto_format_expression_property,
      $.auto_format_type_property,
      $.decimal_places_property,
      $.auto_calc_field_property,
      
      // Option-specific properties
      $.option_caption_property,
      $.option_members_property,
      
      // Obsolete properties (for backwards compatibility)
      $.obsolete_state_property,
      $.obsolete_reason_property,
      $.obsolete_tag_property,
    ),

    // =============================================================================
    // CENTRALIZED TRIGGER ARCHITECTURE
    // =============================================================================
    // Semantic trigger organization for DRY principle and easier maintenance

    // XMLPort property group - leverages centralized categories
    _xmlport_properties: $ => choice(
      $._universal_properties,    // caption, application_area, tool_tip, obsolete_*, description
      $._access_properties,       // inherent_permissions, inherent_entitlements, access
      $.permissions_property,     // XMLPort-level tabledata permissions
      
      // XMLPort-specific properties only
      $.direction_property,
      $.format_evaluate_property,  // Move before format_property to avoid conflict
      $.format_property,
      $.field_delimiter_property,
      $.field_separator_property,
      $.default_fields_validation_property,
      $.table_separator_property,
      $.text_encoding_property,
      $.paste_is_valid_property,
      $.moved_from_property,
      $.moved_to_property,
      $.linked_in_transaction_property,
      $.linked_object_property,
      $.external_schema_property,
      $.use_request_page_property,
      $.default_namespace_property,
      $.encoding_property,
      $.namespaces_property,
      $.use_default_namespace_property,
      $.preserve_whitespace_property,
    ),

    // Action property group - leverages centralized categories  
    _action_properties: $ => choice(
      $._universal_properties,    // caption, application_area, obsolete_*, tool_tip
      $._display_properties,      // enabled, visible
      $._navigation_properties,   // run_object, run_page_link, shortcut_key
      $._access_properties,       // access_by_permission
      
      // Action-specific properties only
      // AboutTitleML and AboutTextML are now in _universal_properties
      $.allowed_file_extensions_property,
      $.allow_multiple_files_property,
      $.custom_action_type_property,
      $.ellipsis_property,
      $.file_upload_action_property,
      $.file_upload_row_action_property,
      $.flow_template_category_name_property,
      $.flow_environment_id_property,
      $.flow_caption_property,
      $.flow_id_property,
      $.flow_template_id_property,
      $.gesture_property,
      $.image_property,
      $.in_footer_bar_property,
      $.is_header_property,
      $.promoted_property,
      $.promoted_category_property,
      $.promoted_is_big_property,
      $.promoted_only_property,
      $.run_page_mode_property,
      $.run_page_on_rec_property,
      $.show_as_property,
    ),

    // Centralized trigger components for DRY principle
    _trigger_keyword: $ => kw('trigger'),

    // Trigger parameter patterns (simplified from '()' duplication)
    _trigger_parameters: $ => '()',

    // Centralized identifier choice pattern (appears 35+ times)
    _identifier_choice: $ => prec(2, choice(
      $.identifier,
      $._quoted_identifier,
      // Allow common End* identifiers that conflict with 'end' keyword
      alias(kw('end'), $.identifier),
      alias(kw('endingtime'), $.identifier),
      alias(kw('endindex'), $.identifier),
      alias(kw('endvalue'), $.identifier),
      alias(kw('enddata'), $.identifier),
      alias(kw('endpoint'), $.identifier),
      alias(kw('enddate'), $.identifier),
      alias(kw('endtime'), $.identifier),
      // Allow 'enum' to be used as an identifier in expression contexts
      alias(kw('enum'), $.identifier)
    )),

    // Flexible identifier choice pattern (includes string literals)
    _flexible_identifier_choice: $ => choice($.identifier, $._quoted_identifier, $.string_literal),

    // Extended value choice pattern (includes integers and identifiers)
    _extended_value_choice: $ => choice(
      $.integer, 
      $.identifier, 
      $._quoted_identifier, 
      $.string_literal,
      $.date_literal,
      $.time_literal,
      $.datetime_literal
    ),

    // Object reference pattern (for referencing AL objects by ID or name)
    _object_reference: $ => choice($.integer, $.identifier, $._quoted_identifier),

    // Qualified table reference pattern (for namespace-qualified table names)
    qualified_table_reference: $ => prec.left(seq(
      $.identifier,
      repeat1(seq('.', $.identifier)),
      optional(seq('.', $._quoted_identifier))
    )),

    // Centralized property template for DRY principle
    _boolean_property_template: $ => seq(
      '=',
      field('value', $._boolean_value),
      ';'
    ),

    _string_property_template: $ => seq(
      '=',
      field('value', $.string_literal),
      ';'
    ),

    _identifier_property_template: $ => seq(
      '=',
      field('value', $._identifier_choice),
      ';'
    ),

    _mixed_identifier_string_property_template: $ => seq(
      '=',
      field('value', $._flexible_identifier_choice),
      ';'
    ),

    // Enum property templates for common patterns
    _access_level_enum_template: $ => seq(
      '=',
      field('value', choice(
        kw('readonly'),
        kw('readwrite'),
        $.identifier,
        $._quoted_identifier
      )),
      ';'
    ),

    _auto_always_never_enum_template: $ => seq(
      '=',
      field('value', choice(
        kw('auto'),
        kw('always'),
        kw('never'),
        kw('generate')
      )),
      ';'
    ),

    // Explicit keyword rules for multiplicity values
    zeroorone_keyword: $ => kw('zeroorone', 1),
    zeroormany_keyword: $ => kw('zeroormany', 1),
    one_keyword: $ => kw('one', 1),
    many_keyword: $ => kw('many', 1),

    _multiplicity_enum_template: $ => seq(
      '=',
      field('value', choice(
        $.zeroorone_keyword,
        $.zeroormany_keyword,
        $.one_keyword,
        $.many_keyword,
        $.identifier
      )),
      ';'
    ),

    _query_type_enum_template: $ => seq(
      '=',
      field('value', choice(
        kw('normal'),
        kw('api'),
        kw('filter')
      )),
      ';'
    ),


    _sql_join_type_enum_template: $ => seq(
      '=',
      field('value', choice(
        kw('innerjoin'),
        kw('leftouterjoin'),
        kw('crossjoin')
      )),
      ';'
    ),



    // String value template (used for simple string properties)
    _string_value_template: $ => seq(
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // DEPRECATED: Use _string_value_template instead
    _caption_string_template: $ => $._string_value_template,

    _caption_boolean_template: $ => seq(
      '=',
      field('value', $._boolean_value),
      ';'
    ),

    _option_caption_template: $ => seq(
      '=',
      $.option_caption_value,
      repeat(seq(
        ',',
        choice(
          seq(
            kw('comment'),
            '=',
            $.string_literal
          ),
          seq(
            kw('locked'),
            '=',
            $.boolean
          )
        )
      )),
      optional(','),  // Support trailing comma
      ';'
    ),

    // ToolTip property templates for consolidation
    _tooltip_template: $ => seq(
      '=',
      $.tool_tip_value,
      ';'
    ),


    // About property templates (same as caption_full_template)
    _about_template: $ => seq(
      '=',
      field('value', $.string_literal),
      repeat(seq(
        ',',
        choice(
          seq(
            kw('locked'),
            '=',
            $.boolean
          ),
          seq(
            kw('comment'),
            '=',
            $.string_literal
          )
        )
      )),
      ';'
    ),


    // Unified ML property template for all multilanguage properties
    _ml_property_template: $ => seq(
      '=',
      field('value', $.ml_value_list),
      ';'
    ),

    // DEPRECATED: Use _string_value_template instead
    // Unified name property template for entity names
    _name_property_template: $ => $._string_value_template,

    // Unified integer property template for integer-only properties
    _integer_property_template: $ => seq(
      '=',
      field('value', $.integer),
      ';'
    ),

    // Unified expression property template for expression-based properties
    _expression_property_template: $ => seq(
      '=',
      field('value', $._expression),
      ';'
    ),

    // Unified permission object templates for access by permission patterns
    _standard_permission_template: $ => seq(
      field('object_name', choice($.string_literal, $._quoted_identifier, $.identifier)),
      '=',
      field('permission', $.permission_type)
    ),

    _system_permission_template: $ => seq(
      kw('system'),
      field('object_name', choice($.string_literal, $._quoted_identifier)),
      '=',
      field('permission', $.permission_type)
    ),

    _tabledata_permission_template: $ => seq(
      field('keyword', alias(kw('tabledata'), $.tabledata_keyword)),
      field('table_name', $._table_reference),
      '=',
      field('permission', $.permission_type)
    ),


    // Centralized extension object pattern for DRY principle

    // Centralized layout modification template for DRY principle
    _layout_modification_template: $ => seq(
      '(',
      field('target', $._identifier_choice),
      ')',
      '{',
      repeat($._layout_element),
      '}'
    ),

    _move_layout_modification_template: $ => seq(
      '(',
      field('target', $._identifier_choice),
      ';',
      field('element', $._identifier_choice),
      ')'
    ),

    // Centralized object declaration header for DRY principle
    _object_header_base: $ => seq(
      field('object_id', $.integer),
      field('object_name', $._identifier_choice)
    ),

    // Centralized comma-separated list templates for DRY principle
    _identifier_choice_list: $ => seq(
      $._identifier_choice,
      repeat(seq(',', $._identifier_choice))
    ),


    // Centralized case-insensitive keyword patterns for DRY principle
    _field_keyword: $ => kw('field'),
    _filter_keyword: $ => kw('filter'),
    _cardpart_keyword: $ => kw('cardpart'),

    // Missing alias target rules
    const: $ => kw('const'),
    name: $ => $._identifier_choice,
    quoted_identifier: $ => $._quoted_identifier,
    table_reference: $ => $._table_reference,
    trigger_name: $ => $.identifier,
    trigger_type: $ => $.identifier,
    value: $ => choice(
      $.identifier,
      $._quoted_identifier,
      $.string_literal,
      $.integer,
      $.boolean,
      $._expression
    ),

  },

});
