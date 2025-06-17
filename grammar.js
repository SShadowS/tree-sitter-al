/**
 * @file AL for Business Central
 * @author Torben Leth <sshadows@sshadows.dk>
 * @license MIT
 */

/// <reference types="tree-sitter-cli/dsl" />
// @ts-check

module.exports = grammar({
  name: "al",


  word: $ => $.identifier,
  extras: $ => [/\s/, $.comment, $.multiline_comment, $.pragma],

  rules: {
    source_file: $ => choice(
      // Standard source file structure
      seq(
        optional($.namespace_declaration),
        repeat($.using_statement),
        repeat(choice($._object, $.pragma))
      ),
      // Preprocessor-wrapped source file
      $.preprocessor_file_conditional
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

    _source_content: $ => seq(
      optional($.namespace_declaration),
      repeat($.using_statement),
      repeat1(choice($._object, $.pragma))  // At least one object or pragma required
    ),

    _object: $ => choice(
      $.table_declaration,
      $.tableextension_declaration,
      $.codeunit_declaration,
      $.pageextension_declaration,
      $.page_declaration,
      $.pagecustomization_declaration,
      $.profile_declaration,
      $.query_declaration,
      $.enum_declaration,
      $.enumextension_declaration, 
      $.xmlport_declaration,
      $.interface_declaration,
      $.dotnet_declaration,
      $.report_declaration,
      $.permissionset_declaration,
      $.controladdin_declaration
    ),

    namespace_declaration: $ => seq(
      'namespace',
      field('name', $.namespace_name),
      ';'
    ),

    namespace_name: $ => seq(
      $.identifier,
      repeat(seq('.', $.identifier))
    ),

    using_statement: $ => seq(
      'using',
      field('namespace', $.namespace_name),
      ';'
    ),
    
    xmlport_declaration: $ => seq(
      /[xX][mM][lL][pP][oO][rR][tT]/,
      $._object_header_base,
      '{',
      repeat($._xmlport_element),
      '}'
    ),
    
    _xmlport_element: $ => choice(
      $.xmlport_schema_element,
      $.var_section,
      $.procedure,
      $.trigger_declaration,
      $._xmlport_properties,
      $.preproc_conditional_xmlport_properties
    ),
    
    // XMLPort specific properties
    direction_property: $ => seq(
      'Direction',
      '=',
      field('value', choice(
        /[eE][xX][pP][oO][rR][tT]/,
        /[iI][mM][pP][oO][rR][tT]/,
        /[bB][oO][tT][hH]/
      )),
      ';'
    ),
    
    format_property: $ => seq(
      'Format',
      '=',
      field('value', choice(
        /[xX][mM][lL]/,
        /[vV][aA][rR][iI][aA][bB][lL][eE]/,
        /[vV][aA][rR][iI][aA][bB][lL][eE][tT][eE][xX][tT]/,
        /[fF][iI][xX][eE][dD]/,
        /[fF][iI][xX][eE][dD][tT][eE][xX][tT]/
      )),
      ';'
    ),
    
    xmlport_schema_element: $ => seq(
      /[sS][cC][hH][eE][mM][aA]/,
      '{',
      repeat($.xmlport_table_element),
      '}'
    ),
    
    xmlport_table_element: $ => seq(
      choice(
        /[tT][aA][bB][lL][eE][eE][lL][eE][mM][eE][nN][tT]/,
        /[fF][iI][eE][lL][dD][eE][lL][eE][mM][eE][nN][tT]/,
        /[tT][eE][xX][tT][eE][lL][eE][mM][eE][nN][tT]/
      ),
      '(',
      field('name', choice($.identifier, $._quoted_identifier)),
      optional(seq(
        ';',
        field('source_table', choice(
          $.identifier, 
          $._quoted_identifier,
          $.field_access  // Support Table.Field syntax
        ))
      )),
      ')',
      '{',
      repeat(choice(
        $.xmlport_table_property,
        $.xmlport_table_element  // Allow nesting of elements
      )),
      '}'
    ),
    
    xmlport_table_property: $ => choice(
      $._universal_properties,    // caption, application_area, tool_tip, tool_tip_ml
      
      // XMLPort table-specific properties
      $.auto_replace_property,
      $.auto_save_property, 
      $.auto_update_property,
      $.link_fields_property,
      $.external_schema_property,
      $.link_table_property,
      $.link_table_force_insert_property,
      $.max_occurs_property,
      $.min_occurs_property,
      $.namespace_prefix_property,
      $.unbound_property,
      $.xml_name_property,
      $.request_filter_fields_property,
      $.request_filter_heading_property,
      $.request_filter_heading_ml_property,
    ),
    
    // 11. Unbound Property
    unbound_property: $ => seq('Unbound', $._boolean_property_template),
    
    // 12. XmlName Property
    xml_name_property: $ => seq('XmlName', $._string_property_template),
    
    // 13. MovedFrom Property
    moved_from_property: $ => seq('MovedFrom', $._string_property_template),
    
    // 14. MovedTo Property
    moved_to_property: $ => seq('MovedTo', $._string_property_template),
    
    // 15. LinkedInTransaction Property
    linked_in_transaction_property: $ => seq('LinkedInTransaction', $._boolean_property_template),
    
    // 16. LinkedObject Property
    linked_object_property: $ => seq('LinkedObject', $._string_property_template),
    
    // 17. RequestFilterFields Property
    request_filter_fields_value: $ => $._identifier_choice_list,
    
    request_filter_fields_property: $ => seq(
      choice('RequestFilterFields', 'requestfilterfields'),
      '=',
      field('value', $.request_filter_fields_value),
      ';'
    ),
    
    // 18. RequestFilterHeading Property
    request_filter_heading_property: $ => seq(
      choice('RequestFilterHeading', 'requestfilterheading'),
      '=',
      field('value', $.string_literal),
      ';'
    ),
    
    // 19. RequestFilterHeadingML Property
    request_filter_heading_ml_property: $ => seq(
      'RequestFilterHeadingML',
      '=',
      $.ml_value_list,
      ';'
    ),
    
    // 6. LinkTable Property
    link_table_property: $ => seq(
      'LinkTable',
      '=',
      field('value', choice($.identifier, $._quoted_identifier)),
      ';'
    ),
    
    // 7. LinkTableForceInsert Property
    link_table_force_insert_property: $ => seq('LinkTableForceInsert', $._boolean_property_template),
    
    // 8. MaxOccurs Property
    max_occurs_value: $ => choice(
      $.integer,
      /[uU][nN][bB][oO][uU][nN][dD][eE][dD]/
    ),
    
    max_occurs_property: $ => seq(
      'MaxOccurs',
      '=',
      field('value', $.max_occurs_value),
      ';'
    ),
    
    // 9. MinOccurs Property
    min_occurs_value: $ => choice(
      $.integer,
      /[oO][nN][cC][eE]/,
      /[zZ][eE][rR][oO]/
    ),
    
    min_occurs_property: $ => seq(
      'MinOccurs',
      '=',
      field('value', $.min_occurs_value),
      ';'
    ),
    
    // 10. NamespacePrefix Property
    namespace_prefix_property: $ => seq(
      'NamespacePrefix',
      '=',
      $.string_literal,
      ';'
    ),
    
    // 5. ExternalSchema
    external_schema_property: $ => seq(
      'ExternalSchema',
      '=',
      $.string_literal,
      ';'
    ),
    
    // First 5 LOW PRIORITY properties
    
    // 1. AutoReplace
    auto_replace_property: $ => seq(
      'AutoReplace',
      '=',
      $.boolean,
      ';'
    ),
    
    // 2. AutoSave
    auto_save_property: $ => seq(
      'AutoSave',
      '=',
      $.boolean,
      ';'
    ),
    
    // 3. AutoUpdate
    auto_update_property: $ => seq(
      'AutoUpdate',
      '=',
      $.boolean,
      ';'
    ),
    
    // 4. LinkFields
    link_fields_property: $ => seq(
      'LinkFields',
      '=',
      $.link_fields_value,
      ';'
    ),
    
    link_fields_value: $ => seq(
      $.field_mapping,
      repeat(seq(',', $.field_mapping))
    ),
    
    field_mapping: $ => seq(
      choice($.identifier, $._quoted_identifier),
      '=',
      choice(
        $.identifier, 
        $._quoted_identifier,
        // Support FIELD("FieldName") syntax
        seq(
          $._field_keyword,
          '(',
          choice($.identifier, $._quoted_identifier, $.string_literal),
          ')'
        )
      )
    ),

    enum_declaration: $ => seq(
      /[eE][nN][uU][mM]/,
      $._object_header_base,
      optional(seq(
        /[iI][mM][pP][lL][eE][mM][eE][nN][tT][sS]/,
        field('interface', $._identifier_choice)
      )),
      '{',
      repeat(choice(
        $._enum_properties, 
        $.enum_value_declaration,
        $.preproc_conditional_enum_properties
      )),
      '}'
    ),

    enumextension_declaration: $ => seq(
      /[eE][nN][uU][mM][eE][xX][tT][eE][nN][sS][iI][oO][nN]/,
      $._object_header_base,
      /[eE][xX][tT][eE][nN][dD][sS]/,
      field('base_object', $._identifier_choice),
      '{',
      repeat($.enum_value_declaration),
      '}'
    ),

    enum_value_declaration: $ => seq(
      /[vV][aA][lL][uU][eE]/,
      '(',
      field('value_id', $.integer),
      ';',
      field('value_name', choice($._quoted_identifier, $.identifier, $.string_literal)), // Allow string literal for value name
      ')',
      '{',
      repeat($._enum_properties), // Use centralized enum properties
      '}'
    ),

    query_declaration: $ => seq(
      /[qQ][uU][eE][rR][yY]/,
      $._object_header_base,
      '{',
      repeat($._query_element),
      '}'
    ),

    _query_element: $ => choice(
      $._universal_properties,       // caption, description, application_area, etc.
      $._query_properties,           // query-specific properties
      $.elements_section,            // dataitem and column definitions
      $.property_list,               // generic property container
      $.preproc_conditional_query_properties
    ),

    about_title_property: $ => seq(
      choice('AboutTitle', 'ABOUTTITLE', 'abouttitle'),
      '=',
      field('value', $.string_literal),
      repeat(seq(
        ',',
        choice(
          seq(
            choice('Locked', 'locked', 'LOCKED'),
            '=',
            $.boolean
          ),
          seq(
            choice('Comment', 'comment', 'COMMENT'),
            '=',
            $.string_literal
          )
        )
      )),
      ';'
    ),

    about_text_property: $ => seq(
      choice('AboutText', 'ABOUTTEXT', 'abouttext'),
      '=',
      field('value', $.string_literal),
      repeat(seq(
        ',',
        choice(
          seq(
            choice('Locked', 'locked', 'LOCKED'),
            '=',
            $.boolean
          ),
          seq(
            choice('Comment', 'comment', 'COMMENT'),
            '=',
            $.string_literal
          )
        )
      )),
      ';'
    ),

    // CONSOLIDATED: page_about_text_property → about_text_property

    // Page-specific version of AboutTextML
    page_about_text_ml_property: $ => seq(
      'AboutTextML',
      '=',
      field('value', $.ml_value_list),
      ';'
    ),

    // CONSOLIDATED: page_about_title_property → about_title_property

    // Page-specific version of AboutTitleML
    page_about_title_ml_property: $ => seq(
      'AboutTitleML',
      '=',
      field('value', $.ml_value_list),
      ';'
    ),

    // Delete Allowed Property
    delete_allowed_property: $ => seq('DeleteAllowed', $._boolean_property_template),

    // Insert Allowed Property
    insert_allowed_property: $ => seq('InsertAllowed', $._boolean_property_template),

    // Modify Allowed Property
    modify_allowed_property: $ => seq('ModifyAllowed', $._boolean_property_template),

    // Source Table Temporary Property
    source_table_temporary_property: $ => seq('SourceTableTemporary', $._boolean_property_template),

    // Phase 2A - Medium Priority Boolean Page Properties
    analysis_mode_enabled_property: $ => seq('AnalysisModeEnabled', $._boolean_property_template),

    auto_split_key_property: $ => seq('AutoSplitKey', $._boolean_property_template),

    change_tracking_allowed_property: $ => seq('ChangeTrackingAllowed', $._boolean_property_template),

    delayed_insert_property: $ => seq('DelayedInsert', $._boolean_property_template),

    links_allowed_property: $ => seq('LinksAllowed', $._boolean_property_template),

    multiple_new_lines_property: $ => seq(
      'MultipleNewLines',
      '=',
      field('value', $.boolean),
      ';'
    ),

    populate_all_fields_property: $ => seq(
      'PopulateAllFields',
      '=',
      field('value', $.boolean),
      ';'
    ),

    // Phase 2B - Medium Priority Complex Page Properties
    data_caption_expression_property: $ => seq(
      /[dD][aA][tT][aA][cC][aA][pP][tT][iI][oO][nN][eE][xX][pP][rR][eE][sS][sS][iI][oO][nN]/,
      '=',
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
            choice('Locked', 'locked', 'LOCKED'),
            '=',
            $.boolean
          ),
          seq(
            choice('Comment', 'comment', 'COMMENT'),
            '=',
            $.string_literal
          )
        )
      )),
      ';'
    ),

    instructional_text_ml_property: $ => seq(
      'InstructionalTextML',
      '=',
      field('value', $.ml_value_list),
      ';'
    ),

    // Phase 4A - High + Medium Priority Page Properties
    // Removed: access_by_permission_page_property - now using universal access_by_permission_property

    prompt_mode_property: $ => seq(
      'PromptMode',
      '=',
      field('value', choice(
        /[aA][uU][tT][oO]/,
        /[aA][lL][wW][aA][yY][sS]/,
        /[nN][eE][vV][eE][rR]/
      )),
      ';'
    ),

    refresh_on_activate_property: $ => seq(
      'RefreshOnActivate',
      '=',
      field('value', $.boolean),
      ';'
    ),

    save_values_property: $ => seq(
      'SaveValues',
      '=',
      field('value', $.boolean),
      ';'
    ),

    show_filter_property: $ => seq(
      'ShowFilter',
      '=',
      field('value', $.boolean),
      ';'
    ),

    additional_search_terms_property: $ => seq(
      'AdditionalSearchTerms',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    additional_search_terms_ml_property: $ => seq(
      'AdditionalSearchTermsML',
      '=',
      field('value', $.ml_value_list),
      ';'
    ),

    entity_caption_property: $ => seq(
      /[eE][nN][tT][iI][tT][yY][cC][aA][pP][tT][iI][oO][nN]/,
      '=',
      field('value', $.string_literal),
      ';'
    ),

    entity_caption_ml_property: $ => seq(
      /[eE][nN][tT][iI][tT][yY][cC][aA][pP][tT][iI][oO][nN][mM][lL]/,
      '=',
      field('value', $.ml_value_list),
      ';'
    ),

    entity_name_property: $ => seq(
      /[eE][nN][tT][iI][tT][yY][nN][aA][mM][eE]/,
      '=',
      field('value', $.string_literal),
      ';'
    ),

    entity_set_caption_property: $ => seq(
      /[eE][nN][tT][iI][tT][yY][sS][eE][tT][cC][aA][pP][tT][iI][oO][nN]/,
      '=',
      field('value', $.string_literal),
      ';'
    ),

    entity_set_caption_ml_property: $ => seq(
      /[eE][nN][tT][iI][tT][yY][sS][eE][tT][cC][aA][pP][tT][iI][oO][nN][mM][lL]/,
      '=',
      field('value', $.ml_value_list),
      ';'
    ),

    entity_set_name_property: $ => seq(
      /[eE][nN][tT][iI][tT][yY][sS][eE][tT][nN][aA][mM][eE]/,
      '=',
      field('value', $.string_literal),
      ';'
    ),

    api_group_property: $ => seq(
      /[aA][pP][iI][gG][rR][oO][uU][pP]/,
      '=',
      field('value', $.string_literal),
      ';'
    ),

    api_publisher_property: $ => seq(
      /[aA][pP][iI][pP][uU][bB][lL][iI][sS][hH][eE][rR]/,
      '=',
      field('value', $.string_literal),
      ';'
    ),

    api_version_property: $ => seq(
      /[aA][pP][iI][vV][eE][rR][sS][iI][oO][nN]/,
      '=',
      field('value', $.string_literal),
      ';'
    ),

    context_sensitive_help_page_property: $ => seq(
      /[cC][oO][nN][tT][eE][xX][tT][sS][eE][nN][sS][iI][tT][iI][vV][eE][hH][eE][lL][pP][pP][aA][gG][eE]/,
      '=',
      field('value', $.string_literal),
      ';'
    ),

    help_link_property: $ => seq(
      'HelpLink',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    is_preview_property: $ => seq(
      'IsPreview',
      '=',
      field('value', $.boolean),
      ';'
    ),
    
    odata_key_fields_value: $ => $._identifier_choice_list,

    odata_key_fields_property: $ => seq(
      'ODataKeyFields',
      '=',
      field('value', $.odata_key_fields_value),
      ';'
    ),

    query_category_property: $ => seq(
      /[qQ][uU][eE][rR][yY][cC][aA][tT][eE][gG][oO][rR][yY]/,
      '=',
      field('value', $.string_literal),
      ';'
    ),

    data_access_intent_property: $ => seq(
      /[dD][aA][tT][aA][aA][cC][cC][eE][sS][sS][iI][nN][tT][eE][nN][tT]/,
      '=',
      field('value', choice(
        /[rR][eE][aA][dD][oO][nN][lL][yY]/,
        /[rR][eE][aA][dD][wW][rR][iI][tT][eE]/
      )),
      ';'
    ),

    query_type_property: $ => seq(
      /[qQ][uU][eE][rR][yY][tT][yY][pP][eE]/,
      '=',
      field('value', choice(
        /[nN][oO][rR][mM][aA][lL]/,
        /[aA][pP][iI]/,
        /[fF][iI][lL][tT][eE][rR]/
      )),
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
    
    sorting_clause: $ => seq(
      /[sS][oO][rR][tT][iI][nN][gG]/,
      '(',
      field('fields', $.field_reference_list),
      ')'
    ),
    
    order_direction: $ => choice(
      /[aA][sS][cC][eE][nN][dD][iI][nN][gG]/,
      /[dD][eE][sS][cC][eE][nN][dD][iI][nN][gG]/
    ),
    
    order_clause: $ => seq(
      /[oO][rR][dD][eE][rR]/,
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
      field('value', choice(
        $.filter_or_expression,
        $.filter_not_equal_expression,
        $.filter_equal_expression,
        $.range_expression,
        $.integer,
        $.string_literal,
        $._quoted_identifier,
        $.identifier
      )),
      ')'
    ),

    filter_or_expression: $ => prec(10, seq(
      choice($.integer, $.identifier, $._quoted_identifier, $.string_literal),
      repeat1(seq(
        '|',
        choice($.integer, $.identifier, $._quoted_identifier, $.string_literal)
      ))
    )),

    filter_not_equal_expression: $ => seq(
      '<>',
      field('value', choice(
        $.string_literal,
        $.integer,
        $._quoted_identifier,
        $.identifier
      ))
    ),

    filter_equal_expression: $ => seq(
      '=',
      field('value', choice(
        $.string_literal,
        $.integer,
        $._quoted_identifier,
        $.identifier
      ))
    ),

    range_expression: $ => seq(
      optional(field('start', choice($.integer, $.identifier, $._quoted_identifier, $.string_literal))),
      '..',
      optional(field('end', choice($.integer, $.identifier, $._quoted_identifier, $.string_literal)))
    ),

    const_expression: $ => seq(
      /[cC][oO][nN][sS][tT]/,
      '(',
      optional(choice(
        $.string_literal,
        $.identifier,
        $._quoted_identifier,
        $.integer,
        $.boolean,
        $.database_reference
      )),
      ')'
    ),
    
    filter_expression: $ => seq(
      choice(
        $.where_clause,
        $.sorting_clause,
        seq($.where_clause, $.sorting_clause),
        seq($.sorting_clause, $.where_clause)
      )
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
    
    source_table_view_property: $ => prec(10, seq(
      choice('SourceTableView', 'sourcetableview', 'SOURCETABLEVIEW'),
      '=',
      field('value', $.source_table_view_value),
      ';'
    )),

    elements_section: $ => seq(
      /[eE][lL][eE][mM][eE][nN][tT][sS]/,
      '{',
      repeat($.dataitem_section),
      '}'
    ),

    dataitem_section: $ => seq(
      /[dD][aA][tT][aA][iI][tT][eE][mM]/,
      '(',
      field('name', choice($.identifier, $._quoted_identifier)),
      ';',
      field('table_name', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat(choice(
        $.column_section,
        $.dataitem_section,
        $.data_item_link_property
      )),
      '}'
    ),

    data_item_link_property: $ => seq(
      'DataItemLink',
      '=',
      field('value', $.data_item_link_value),
      ';'
    ),

    data_item_link_value: $ => seq(
      field('field', choice($.identifier, $._quoted_identifier)),
      '=',
      choice(
        // Traditional dot syntax: RecordRef."Field Name"
        seq(
          field('linked_field', choice($.identifier, $._quoted_identifier)),
          '.',
          field('linked_field_name', choice($.identifier, $._quoted_identifier))
        ),
        // FIELD() function syntax: FIELD("Field Name")
        seq(
          $._field_keyword,
          '(',
          field('linked_field_name', choice($.identifier, $._quoted_identifier)),
          ')'
        )
      ),
      repeat(seq(
        ',',
        field('field', choice($.identifier, $._quoted_identifier)),
        '=',
        choice(
          // Traditional dot syntax: RecordRef."Field Name"
          seq(
            field('linked_field', choice($.identifier, $._quoted_identifier)),
            '.',
            field('linked_field_name', choice($.identifier, $._quoted_identifier))
          ),
          // FIELD() function syntax: FIELD("Field Name")
          seq(
            $._field_keyword,
            '(',
            field('linked_field_name', choice($.identifier, $._quoted_identifier)),
            ')'
          )
        )
      ))
    ),

    column_section: $ => seq(
      /[cC][oO][lL][uU][mM][nN]/,
      '(',
      field('name', choice($.identifier, $._quoted_identifier)),
      ';',
      field('field_name', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat(choice(
        $.property_list
      )),
      '}'
    ),

    pageextension_declaration: $ => seq(
      /[pP][aA][gG][eE][eE][xX][tT][eE][nN][sS][iI][oO][nN]/,
      $._object_header_base,
      /[eE][xX][tT][eE][nN][dD][sS]/,
      field('base_object', $._identifier_choice),
      '{',
      repeat($._pageextension_element),
      '}'
    ),

    _pageextension_element: $ => choice(
      $.layout_section,
      $.actions_section,
      $._page_properties,     // Centralized page properties
      $.var_section,
      $.trigger_declaration,
      seq(optional($.attribute_list), $.procedure),
      $.preproc_region,
      $.preproc_endregion,
      $.pragma
    ),

    tableextension_declaration: $ => seq(
      /[tT][aA][bB][lL][eE][eE][xX][tT][eE][nN][sS][iI][oO][nN]/,
      $._object_header_base,
      /[eE][xX][tT][eE][nN][dD][sS]/,
      field('base_object', $._identifier_choice),
      '{',
      repeat($._tableextension_element),
      '}'
    ),

    _tableextension_element: $ => choice(
      $.fields,
      $.modify_field_declaration,  // Add direct modify field support
      $.keys,
      $.fieldgroups_section,
      $.procedure,
      $.var_section,
      $.trigger_declaration,
      $._table_properties     // Centralized table properties
    ),

    actions_section: $ => seq(
      /[aA][cC][tT][iI][oO][nN][sS]/,
      '{',
      repeat(choice(
        $._action_element,
        $._action_group,
        $.action_group_section,
        $.area_action_section
      )),
      '}'
    ),

    area_action_section: $ => seq(
      /[aA][rR][eE][aA]/,
      '(',
      field('type', choice(
        /[pP][rR][oO][cC][eE][sS][sS][iI][nN][gG]/,
        /[rR][eE][pP][oO][rR][tT][iI][nN][gG]/,
        /[nN][aA][vV][iI][gG][aA][tT][iI][oO][nN]/,
        /[cC][rR][eE][aA][tT][iI][oO][nN]/,
        /[pP][rR][oO][mM][oO][tT][eE][dD]/,
        /[sS][yY][sS][tT][eE][mM][aA][cC][tT][iI][oO][nN][sS]/,
        /[sS][eE][cC][tT][iI][oO][nN][sS]/,
        /[eE][mM][bB][eE][dD][dD][iI][nN][gG]/
      )),
      ')',
      '{',
      repeat(choice(
        $._action_element,
        $.action_group_section,
        $.separator_action
      )),
      '}'
    ),

    action_group_section: $ => seq(
      /[gG][rR][oO][uU][pP]/,
      '(',
      field('name', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat(choice(
        $.action_declaration,
        $.actionref_declaration,
        $.action_group_section,
        $._action_property,
        $.separator_action,
        $.empty_statement
      )),
      '}'
    ),
    
    // Add separator action rule
    separator_action: $ => seq(
      /[sS][eE][pP][aA][rR][aA][tT][oO][rR]/,
      '(',
      field('name', choice($.identifier, $._quoted_identifier)),
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

    addfirst_action_group: $ => seq(
      /[aA][dD][dD][fF][iI][rR][sS][tT]/,
      '(',
      field('target', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat(choice(
        $._action_element,
        $.action_group_section,
        $.separator_action
      )),
      '}'
    ),

    addlast_action_group: $ => seq(
      /[aA][dD][dD][lL][aA][sS][tT]/,
      '(',
      field('target', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat(choice(
        $._action_element,
        $.action_group_section,
        $.separator_action
      )),
      '}'
    ),

    addafter_action_group: $ => seq(
      /[aA][dD][dD][aA][fF][tT][eE][rR]/,
      '(',
      field('target', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat(choice(
        $._action_element,
        $.action_group_section,
        $.separator_action
      )),
      '}'
    ),

    addbefore_action_group: $ => seq(
      /[aA][dD][dD][bB][eE][fF][oO][rR][eE]/,
      '(',
      field('target', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat(choice(
        $._action_element,
        $.action_group_section,
        $.separator_action
      )),
      '}'
    ),

    modify_action_group: $ => seq(
      /[mM][oO][dD][iI][fF][yY]/,
      '(',
      field('target', choice($.identifier, $._quoted_identifier)),
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
      /[mM][oO][dD][iI][fF][yY]/,
      '(',
      field('target', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat(choice(
        $._action_property,
        seq(optional($.attribute_list), $.trigger_declaration),
        ';'
      )),
      '}'
    )),

    _action_element: $ => choice(
      $.action_declaration,
      $.actionref_declaration,
      $.systemaction_declaration
    ),

    action_declaration: $ => seq(
      /[aA][cC][tT][iI][oO][nN]/,
      '(',
      field('name', choice($.identifier, $._quoted_identifier)),
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

    actionref_declaration: $ => seq(
      /[aA][cC][tT][iI][oO][nN][rR][eE][fF]/,
      '(',
      field('promoted_name', choice($.identifier, $._quoted_identifier)),
      ';',
      field('action_name', choice($.identifier, $._quoted_identifier)),
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
      /[sS][yY][sS][tT][eE][mM][aA][cC][tT][iI][oO][nN]/,
      '(',
      field('name', choice($.identifier, $._quoted_identifier)),
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

    _action_property: $ => $._action_properties,

    application_area_property: $ => seq(
      'ApplicationArea',
      '=',
      field('value', seq(
        choice($.identifier, $._quoted_identifier, $.string_literal),
        repeat(seq(',', choice($.identifier, $._quoted_identifier, $.string_literal)))
      )),
      ';'
    ),

    usage_category_property: $ => seq(
      'UsageCategory',
      '=',
      field('value', $.usage_category_value),
      ';'
    ),

    source_table_property: $ => seq(
      /[sS][oO][uU][rR][cC][eE][tT][aA][bB][lL][eE]/,
      '=',
      field('value', choice($.integer, $.identifier, $._quoted_identifier)),
      ';'
    ),

    page_type_property: $ => seq(
      'PageType',
      '=',
      field('value', choice(
        /[cC][aA][rR][dD]/,
        /[lL][iI][sS][tT]/,
        /[rR][oO][lL][eE][cC][eE][nN][tT][eE][rR]/,
        /[wW][oO][rR][kK][sS][hH][eE][eE][tT]/,
        /[sS][tT][aA][nN][dD][aA][rR][dD][dD][iI][aA][lL][oO][gG]/,
        /[cC][oO][nN][fF][iI][rR][mM][dD][iI][aA][lL][oO][gG]/,
        /[nN][aA][vV][iI][gG][aA][tT][iI][oO][nN][pP][aA][nN][eE]/,
        /[hH][eE][aA][dD][lL][iI][nN][eE][sS]/,
        /[dD][oO][cC][uU][mM][eE][nN][tT]/,
        /[aA][pP][iI]/,
        /[cC][aA][rR][dD][pP][aA][rR][tT]/,
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
      'Image',
      '=',
      field('value', choice($.identifier, $._quoted_identifier, $.string_literal)),
      ';'
    ),

    run_object_property: $ => seq(
      'RunObject',
      '=',
      field('value', $.run_object_value),
      ';'
    ),

    run_object_value: $ => seq(
      choice(
        'Page', 'PAGE', 'page', 
        'Report', 'REPORT', 'report',
        'Codeunit', 'CODEUNIT', 'codeunit',
        'Table', 'TABLE', 'table'
      ),
      field('object_ref', choice($.integer, $.identifier, $._quoted_identifier))
    ),

    run_page_link_property: $ => seq(
      'RunPageLink',
      '=',
      field('value', seq(
        $.run_page_link_value,
        repeat(seq(',', $.run_page_link_value))
      )),
      ';'
    ),

    run_page_view_property: $ => seq(
      'RunPageView',
      '=',
      field('value', $.source_table_view_value),
      ';'
    ),

    run_page_link_value: $ => seq(
      field('field', choice($.identifier, $._quoted_identifier)),
      '=',
      field('filter_type', choice(
        seq(
          /[cC][oO][nN][sS][tT]/,
          '(',
          field('const_value', choice($.identifier, $._quoted_identifier, $.integer, $.string_literal)),
          ')'
        ),
        seq(
          /[fF][iI][eE][lL][dD]/,
          '(',
          field('field_value', choice($.identifier, $._quoted_identifier)),
          ')'
        ),
        seq(
          /[fF][iI][lL][tT][eE][rR]/,
          '(',
          field('filter_value', choice(
            $.filter_or_expression,
            $.filter_not_equal_expression,
            $.filter_equal_expression,
            $.range_expression,
            $.identifier, 
            $._quoted_identifier, 
            $.integer, 
            $.string_literal
          )),
          ')'
        )
      ))
    ),

    enabled_property: $ => seq(
      choice('Enabled', 'ENABLED', 'enabled'),
      '=',
      field('value', $._expression),
      ';'
    ),

    visible_property: $ => seq(
      'Visible',
      '=',
      field('value', $._expression),
      ';'
    ),

    scope_property: $ => seq(
      'Scope',
      '=',
      field('value', choice($.identifier, $._quoted_identifier)),
      ';'
    ),

    promoted_property: $ => seq(
      choice('Promoted', 'PROMOTED', 'promoted'),
      '=',
      field('value', $.boolean),
      ';'
    ),

    promoted_category_property: $ => seq(
      'PromotedCategory',
      '=',
      field('value', choice($.identifier, $._quoted_identifier, $.string_literal)),
      ';'
    ),

    promoted_only_property: $ => seq(
      'PromotedOnly',
      '=',
      field('value', $.boolean),
      ';'
    ),

    promoted_is_big_property: $ => seq(
      'PromotedIsBig',
      '=',
      field('value', $.boolean),
      ';'
    ),

    shortcut_key_property: $ => prec(10, seq(
      choice('ShortcutKey', 'ShortCutKey', 'SHORTCUTKEY', 'shortcutkey'),
      '=',
      field('value', choice($.string_literal, $._quoted_identifier)),
      ';'
    )),

    in_footer_bar_property: $ => seq(
      'InFooterBar',
      '=',
      field('value', $.boolean),
      ';'
    ),

    run_page_mode_property: $ => seq(
      'RunPageMode',
      '=',
      field('value', $.run_page_mode_value),
      ';'
    ),

    run_page_on_rec_property: $ => seq(
      'RunPageOnRec',
      '=',
      field('value', $.boolean),
      ';'
    ),

    _assignment_operator: $ => token(choice(':=', '+=', '-=', '*=', '/=')),
    _double__colon: $ => token(prec(1, '::')),
    _colon: $ => ':',

    table_no_property: $ => seq(
      alias(/[tT][aA][bB][lL][eE][nN][oO]/, 'TableNo'),
      '=',
      field('value', alias($._table_no_value, $.value)),
      ';'
    ),

    subtype_property: $ => seq(
      choice('Subtype', 'SubType', 'subtype', 'SUBTYPE'),
      '=', 
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
      choice('EventSubscriberInstance', 'eventsubscriberinstance', 'EVENTSUBSCRIBERINSTANCE'),
      '=',
      field('value', alias($.event_subscriber_instance_value, $.value)),
      ';'
    ),

    test_isolation_property: $ => seq(
      choice('TestIsolation', 'testisolation', 'TESTISOLATION'),
      '=',
      field('value', alias($.test_isolation_value, $.value)),
      ';'
    ),

    drilldown_pageid_property: $ => seq(
      choice('DrillDownPageId', 'DrillDownPageID'),
      '=', 
      field('value', alias($.page_id_value, $.value)),
      ';'
    ),

    lookup_pageid_property: $ => seq(
      choice('LookupPageId', 'LookupPageID'),
      '=',
      field('value', alias($.page_id_value, $.value)),
      ';'
    ),

    card_page_id_property: $ => seq(
      /[cC][aA][rR][dD][pP][aA][gG][eE][iI][dD]/,
      '=',
      field('value', $.page_id_value),
      ';'
    ),

    promoted_action_categories_property: $ => seq(
      choice('PromotedActionCategories', 'promotedactioncategories', 'PROMOTEDACTIONCATEGORIES'),
      '=',
      field('value', $.string_literal),
      ';'
    ),

    implementation_property: $ => seq(
      'Implementation',
      '=',
      field('value', $.implementation_value),
      ';'
    ),

    table_declaration: $ => seq(
      /[tT][aA][bB][lL][eE]/,
      $._object_header_base,
      '{',
      repeat($._table_element),
      '}'
    ),

    codeunit_declaration: $ => seq(
      /[cC][oO][dD][eE][uU][nN][iI][tT]/,
      $._object_header_base,
      optional($.implements_clause),
      '{',
      repeat(choice(
        prec(4, $._codeunit_properties), // Use individual properties
        $.preproc_conditional_object_properties,
        $.var_section,
        $.attributed_procedure,
        $.attributed_onrun_trigger, 
        $.attributed_trigger,
        $.preproc_conditional_procedures,
        $.pragma
      )),
      '}'
    ),

    preproc_conditional_attributes: $ => seq(
      $.preproc_if,
      $.attribute_list,
      $.preproc_endif
    ),

    attributed_procedure: $ => choice(
      seq(choice($.attribute_list, $.preproc_conditional_attributes), repeat($.pragma), $.procedure),
      $.procedure
    ),

    attributed_trigger: $ => choice(
      seq(choice($.attribute_list, $.preproc_conditional_attributes), repeat($.pragma), $.trigger_declaration),
      $.trigger_declaration
    ),

    attributed_onrun_trigger: $ => choice(
      seq(choice($.attribute_list, $.preproc_conditional_attributes), repeat($.pragma), $.onrun_trigger),
      $.onrun_trigger
    ),

    preproc_conditional_procedures: $ => seq(
      $.preproc_if,
      repeat1(seq(optional($.attribute_list), choice($.procedure, $.onrun_trigger, $.trigger_declaration))),
      optional(seq(
        $.preproc_else,
        repeat1(seq(optional($.attribute_list), choice($.procedure, $.onrun_trigger, $.trigger_declaration)))
      )),
      $.preproc_endif
    ),

    implements_clause: $ => seq(
      /[iI][mM][pP][lL][eE][mM][eE][nN][tT][sS]/,
      field('interface', choice($._quoted_identifier, $.identifier))
    ),

    // Generic trigger rule for codeunits etc.

    page_declaration: $ => seq(
      /[pP][aA][gG][eE]/,
      $._object_header_base,
      '{',
      repeat(seq(optional(';'), $._page_element)),
      '}'
    ),

    pagecustomization_declaration: $ => seq(
      /[pP][aA][gG][eE][cC][uU][sS][tT][oO][mM][iI][zZ][aA][tT][iI][oO][nN]/,
      field('object_name', $._identifier_choice),
      /[cC][uU][sS][tT][oO][mM][iI][zZ][eE][sS]/,
      field('target_page', $._identifier_choice),
      '{',
      repeat($._pagecustomization_element),
      '}'
    ),

    profile_declaration: $ => seq(
      /[pP][rR][oO][fF][iI][lL][eE]/,
      field('object_name', $._identifier_choice),
      '{',
      repeat($._profile_element),
      '}'
    ),

    controladdin_declaration: $ => seq(
      /[cC][oO][nN][tT][rR][oO][lL][aA][dD][dD][iI][nN]/,
      field('object_name', $._identifier_choice),
      '{',
      repeat($._controladdin_element),
      '}'
    ),

    _controladdin_element: $ => choice(
      $._controladdin_properties,    // Centralized properties
      $.controladdin_event,          // ControlAddIn structural elements
      $.controladdin_procedure,      // ControlAddIn structural elements
      $.property_list,               // Generic fallback
      $.preproc_conditional_controladdin_properties
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
      optional($.attribute_list),
      'event',
      field('name', $.identifier),
      '(',
      optional($.parameter_list),
      ')',
      optional(';')
    ),

    controladdin_procedure: $ => seq(
      'procedure',
      field('name', $.identifier),
      '(',
      optional($.parameter_list),
      ')',
      optional(';')
    ),

    interface_declaration: $ => seq(
      /[iI][nN][tT][eE][rR][fF][aA][cC][eE]/,
      field('object_name', $._identifier_choice),
      '{',
      repeat($.interface_procedure),
      '}'
    ),

    interface_procedure: $ => seq(
      /[pP][rR][oO][cC][eE][dD][uU][rR][eE]/,
      field('name', $.identifier),
      '(',
      optional($.parameter_list),
      ')',
      optional(seq(':', field('return_type', $.type_specification))),
      optional(';')
    ),

    report_declaration: $ => seq(
      /[rR][eE][pP][oO][rR][tT]/,
      $._object_header_base,
      '{',
      repeat($._report_element),
      '}'
    ),

    _report_element: $ => choice(
      // Structural report elements (not properties)
      $.dataset_section,
      $.labels_section,
      $.requestpage_section,
      $.actions_section,
      $.var_section,
      
      // Report procedures and triggers
      seq(optional($.attribute_list), $.procedure),
      seq(optional($.attribute_list), $.trigger_declaration),
      
      // Preprocessor conditional report properties
      $.preproc_conditional_report_properties,
      
      // All report properties now centralized
      $._report_properties,
    ),

    labels_section: $ => seq(
      /[lL][aA][bB][eE][lL][sS]/,
      '{',
      repeat($._label_element),
      '}'
    ),

    _label_element: $ => choice(
      $.label_declaration
    ),

    label_declaration: $ => seq(
      field('name', $.identifier),
      '=',
      field('value', $.string_literal),
      ';'
    ),

    dataset_section: $ => seq(
      'dataset',
      '{',
      repeat($.report_dataitem_section),
      '}'
    ),

    report_dataitem_section: $ => seq(
      'dataitem',
      '(',
      field('name', choice($.identifier, $._quoted_identifier)),
      ';',
      $._identifier_choice,
      ')',
      '{',
      repeat(choice(
        $.report_column_section, 
        $.report_dataitem_section,
        $._dataitem_properties,
        seq(optional($.attribute_list), $.trigger_declaration)
      )),
      '}'
    ),

    report_column_section: $ => seq(
      'column',
      '(',
      field('name', $.identifier),
      ';',
      field('source', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat($._field_properties),
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
      /[pP][eE][rR][mM][iI][sS][sS][iI][oO][nN][sS][eE][tT]/,
      $._object_header_base,
      '{',
      repeat($._permissionset_element),
      '}'
    ),

    _permissionset_element: $ => choice(
      $._permissionset_properties,   // Centralized properties
      $.permissionset_permissions,   // PermissionSet structural elements
      $.property_list,               // Generic fallback
      $.preproc_conditional_permissionset_properties
    ),

    assignable_property: $ => seq(
      'Assignable',
      '=',
      choice('true', 'false'),
      ';'
    ),

    included_permission_sets_property: $ => seq(
      'IncludedPermissionSets',
      '=',
      field('value', $.included_permission_sets_list),
      ';'
    ),

    included_permission_sets_list: $ => $._identifier_choice_list,

    permissionset_permissions: $ => seq(
      'Permissions',
      '=',
      $.permission_list,
      ';'
    ),

    permission_list: $ => seq(
      $.permission_entry,
      repeat(choice(
        seq(',', optional($.pragma), $.permission_entry),
        $.pragma
      ))
    ),

    permission_entry: $ => choice(
      $.tabledata_permission_entry,
      $.table_permission_entry,
      $.page_permission_entry,
      $.report_permission_entry,
      $.codeunit_permission_entry,
      $.system_permission_entry
    ),

    tabledata_permission_entry: $ => prec(1, seq(
      $._tabledata_keyword,
      choice($._quoted_identifier, $.identifier, $.integer),
      '=',
      $.permission_type
    )),

    table_permission_entry: $ => seq(
      $._table_permission_keyword,
      choice($._quoted_identifier, $.identifier, $.integer),
      '=',
      $.permission_type
    ),

    page_permission_entry: $ => seq(
      choice('page', 'Page', 'PAGE'),
      $._identifier_choice,
      '=',
      $.permission_type
    ),

    report_permission_entry: $ => seq(
      choice('report', 'Report', 'REPORT'),
      $._identifier_choice,
      '=',
      $.permission_type
    ),

    codeunit_permission_entry: $ => seq(
      choice('codeunit', 'Codeunit', 'CODEUNIT'),
      $._identifier_choice,
      '=',
      $.permission_type
    ),

    system_permission_entry: $ => seq(
      choice('system', 'System', 'SYSTEM'),
      $._identifier_choice,
      '=',
      $.permission_type
    ),

    dotnet_declaration: $ => seq(
      /[dD][oO][tT][nN][eE][tT]/,
      '{',
      repeat($.assembly_declaration),
      '}'
    ),

    assembly_declaration: $ => seq(
      /[aA][sS][sS][eE][mM][bB][lL][yY]/,
      '(',
      field('name', choice($.string_literal, $._quoted_identifier)),
      ')',
      '{',
      repeat(choice(
        $.assembly_property,
        $.type_declaration
      )),
      '}'
    ),

    assembly_property: $ => choice(
      seq('Version', '=', field('value', choice($.string_literal, $._quoted_identifier)), ';'),
      seq('Culture', '=', field('value', choice($.string_literal, $._quoted_identifier)), ';'),
      seq('PublicKeyToken', '=', field('value', choice($.string_literal, $._quoted_identifier)), ';')
    ),

    type_declaration: $ => seq(
      /[tT][yY][pP][eE]/,
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
      '}'
    ),

    dotnet_type_name: $ => token(seq(
      /[A-Za-z_][A-Za-z0-9_]*/,
      repeat(seq('.', /[A-Za-z_][A-Za-z0-9_]*/))
    )),

    _page_element: $ => choice(
      // Structural page elements (not properties)
      $.layout_section,
      $.actions_section,
      seq(optional($.attribute_list), $.procedure),  // Support attributed procedures in pages
      $.var_section,
      $.trigger_declaration,
      
      // All page properties now centralized
      $._page_properties,
      
      // Preprocessor conditional page properties
      $.preproc_conditional_page_properties,
      
      // Special case: source_table_view_property at the top for higher precedence  
      $.source_table_view_property,
    ),

    layout_section: $ => seq(
      /[lL][aA][yY][oO][uU][tT]/,
      '{',
      repeat($._layout_element),
      '}'
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
    addfirst_layout_modification: $ => seq(
      /[aA][dD][dD][fF][iI][rR][sS][tT]/,
      $._layout_modification_template
    ),

    addlast_layout_modification: $ => seq(
      /[aA][dD][dD][lL][aA][sS][tT]/,
      $._layout_modification_template
    ),

    addafter_layout_modification: $ => seq(
      /[aA][dD][dD][aA][fF][tT][eE][rR]/,
      $._layout_modification_template
    ),

    addbefore_layout_modification: $ => seq(
      /[aA][dD][dD][bB][eE][fF][oO][rR][eE]/,
      $._layout_modification_template
    ),

    modify_layout_modification: $ => seq(
      /[mM][oO][dD][iI][fF][yY]/,
      '(',
      field('target', $._identifier_choice),
      ')',
      '{',
      repeat(choice(
        $._page_properties,
        seq(optional($.attribute_list), $.trigger_declaration)
      )),
      '}'
    ),

    movefirst_layout_modification: $ => seq(
      /[mM][oO][vV][eE][fF][iI][rR][sS][tT]/,
      $._move_layout_modification_template
    ),

    movelast_layout_modification: $ => seq(
      /[mM][oO][vV][eE][lL][aA][sS][tT]/,
      $._move_layout_modification_template
    ),

    moveafter_layout_modification: $ => seq(
      /[mM][oO][vV][eE][aA][fF][tT][eE][rR]/,
      $._move_layout_modification_template
    ),

    movebefore_layout_modification: $ => seq(
      /[mM][oO][vV][eE][bB][eE][fF][oO][rR][eE]/,
      $._move_layout_modification_template
    ),

    area_section: $ => seq(
      /[aA][rR][eE][aA]/,
      '(',
      field('type', choice(
        /[cC][oO][nN][tT][eE][nN][tT]/,
        /[fF][aA][cC][tT][bB][oO][xX][eE][sS]/,
        /[fF][iI][lL][tT][eE][rR]/,
        /[rR][oO][lL][eE][cC][eE][nN][tT][eE][rR]/,
        /[pP][rR][oO][mM][pP][tT][oO][pP][tT][iI][oO][nN][sS]/,
        /[sS][yY][sS][tT][eE][mM][aA][cC][tT][iI][oO][nN][sS]/
      )),
      ')',
      '{',
      repeat($._layout_element),
      '}'
    ),

    group_section: $ => seq(
      /[gG][rR][oO][uU][pP]/,
      '(',
      field('name', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat(choice(
        $._page_properties,
        $._layout_element
      )),
      '}'
    ),

    cuegroup_section: $ => seq(
      /[cC][uU][eE][gG][rR][oO][uU][pP]/,
      '(',
      field('name', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat(choice(
        $._page_properties,
        $.field_section,
        $.actions_section
      )),
      '}'
    ),

    grid_section: $ => seq(
      /[gG][rR][iI][dD]/,
      '(',
      field('name', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat(choice(
        $._page_properties,
        $._layout_element
      )),
      '}'
    ),

    fixed_section: $ => seq(
      /[fF][iI][xX][eE][dD]/,
      '(',
      field('name', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat(choice(
        $._page_properties,
        $._layout_element
      )),
      '}'
    ),

    label_section: $ => seq(
      /[lL][aA][bB][eE][lL]/,
      '(',
      field('name', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat(choice(
        $._universal_properties,
        $._display_properties
      )),
      '}'
    ),

    repeater_section: $ => seq(
      /[rR][eE][pP][eE][aA][tT][eE][rR]/,
      '(',
      field('name', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat(choice(
        $._page_properties,
        $._layout_element
      )),
      '}'
    ),

    field_section: $ => choice(
      // Standard field: field(Name) { ... }
      seq(
        /[fF][iI][eE][lL][dD]/,
        '(',
        field('name', choice($.identifier, $._quoted_identifier)),
        ')',
        '{',
        repeat($._field_properties),
        '}'
      ),
      // Field with control name: field(Name)(ControlName) { ... }
      seq(
        /[fF][iI][eE][lL][dD]/,
        '(',
        field('name', choice($.identifier, $._quoted_identifier)),
        ')',
        '(',
        field('control_name', choice($.identifier, $._quoted_identifier)),
        ')',
        '{',
        repeat($._field_properties),
        '}'
      ),
      // Combined field: field(ControlId; SourceOrFieldName) { ... }
      seq(
        /[fF][iI][eE][lL][dD]/,
        '(',
        // ControlId can be string, quoted identifier, integer, or identifier
        field('control_id', choice($.string_literal, $._quoted_identifier, $.integer, $.identifier)),
        ';',
        // SourceOrFieldName can be identifier, quoted identifier, or complex expression
        field('source_or_field_name', $._expression),
        ')',
        '{',
        repeat($._field_properties),
        '}'
      )
    ),

    part_section: $ => seq(
      /[pP][aA][rR][tT]/,
      '(',
      field('name', choice($.string_literal, $.identifier, $._quoted_identifier)),
      ';',
      field('page_name', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat(choice(
        $._page_properties,
        $.empty_statement
      )),
      '}'
    ),

    systempart_section: $ => seq(
      /[sS][yY][sS][tT][eE][mM][pP][aA][rR][tT]/,
      '(',
      field('control_id', choice($.string_literal, $.identifier, $._quoted_identifier)),
      ';',
      field('systempart_type', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat(choice(
        $._page_properties,
        $.empty_statement
      )),
      '}'
    ),

    usercontrol_section: $ => seq(
      /[uU][sS][eE][rR][cC][oO][nN][tT][rR][oO][lL]/,
      '(',
      field('control_id', choice($.identifier, $._quoted_identifier)),
      ';',
      field('addin_name', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat(choice(
        $._page_properties,
        $.trigger_declaration,
        $.var_section,
        $.code_block,
        $.preproc_conditional_properties,
        $.pragma
      )),
      '}'
    ),

    sub_page_link_property: $ => seq(
      'SubPageLink',
      '=',
      field('value', seq(
        $.run_page_link_value,
        repeat(seq(',', $.run_page_link_value))
      )),
      ';'
    ),

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

    trigger_declaration: $ => seq(
      choice('trigger', 'TRIGGER', 'Trigger'),
      field('name', alias($.identifier, $.trigger_name)), // Unified to use 'name' like generic_trigger
      choice(
        seq('(', optional($.parameter_list), ')'),
        seq()
      ),
      optional(seq(':', $.type_specification)),
      choice(
        // Standard trigger with code block
        prec(2, seq(
          optional(';'), // Allow optional semicolon after trigger declaration
          optional($.var_section),
          $.code_block
        )),
        // Control add-in trigger declaration ending with semicolon (without code block)
        prec(1, ';')
      )
    ),

    // Property value types for specific properties
    _table_no_value: $ => choice(
      $.integer,
      $.identifier,
      $._quoted_identifier
    ),

    subtype_value: $ => choice(
      // Codeunit SubType values
      /[iI][nN][sS][tT][aA][lL][lL]/,
      /[uU][pP][gG][rR][aA][dD][eE]/,
      /[tT][eE][sS][tT]/,
      // BLOB SubType values
      /[uU][sS][eE][rR][dD][eE][fF][iI][nN][eE][dD]/,
      /[bB][iI][tT][mM][aA][pP]/,
      /[jJ][sS][oO][nN]/,
      // Other potential values (like PurchaseHeader)
      $.identifier  // Allow any identifier to be future-proof
    ),

    single_instance_value: $ => $.boolean,

    event_subscriber_instance_value: $ => choice(
      /[mM][aA][nN][uU][aA][lL]/,
      /[sS][tT][aA][tT][iI][cC]/,
      /[sS][tT][aA][tT][iI][cC][aA][uU][tT][oO][mM][aA][tT][iI][cC]/
    ),

    test_isolation_value: $ => choice(
      /[cC][oO][dD][eE][uU][nN][iI][tT]/,
      /[fF][uU][nN][cC][tT][iI][oO][nN]/,
      /[pP][aA][gG][eE]/,
      /[dD][iI][sS][aA][bB][lL][eE][dD]/
    ),

    implementation_value: $ => seq(
      field('interface', $._identifier_choice),
      '=',
      field('implementation', $._identifier_choice)
    ),

    field_class_value: $ => choice(
      /[fF][lL][oO][wW][fF][iI][eE][lL][dD]/,
      /[fF][lL][oO][wW][fF][iI][lL][tT][eE][rR]/,
      /[nN][oO][rR][mM][aA][lL]/
    ),

    editable_value: $ => choice(
      prec(2, $.boolean),
      prec(1, $._expression)
    ),

    extended_datatype_value: $ => choice(
      /[pP][hH][oO][nN][eE][nN][oO]/,
      /[uU][rR][lL]/, 
      /[eE][mM][aA][iI][lL]/,
      /[rR][aA][tT][iI][oO]/,
      /[dD][uU][rR][aA][tT][iI][oO][nN]/,
      /[mM][aA][sS][kK][eE][dD]/,
      /[rR][iI][cC][hH][cC][oO][nN][tT][eE][nN][tT]/
    ),

    // Values for the first 5 missing Page Field Properties
    column_span_value: $ => $.integer,
    
    importance_value: $ => choice(
      /[sS][tT][aA][nN][dD][aA][rR][dD]/,
      /[aA][dD][dD][iI][tT][iI][oO][nN][aA][lL]/,
      /[pP][rR][oO][mM][oO][tT][eE][dD]/,
      prec(10, $._quoted_identifier)  // Higher precedence for quoted values
    ),

    style_value: $ => choice(
      seq(optional('"'), /[sS][tT][aA][nN][dD][aA][rR][dD]/, optional('"')),
      seq(optional('"'), /[sS][tT][aA][nN][dD][aA][rR][dD][aA][cC][cC][eE][nN][tT]/, optional('"')),
      seq(optional('"'), /[sS][tT][rR][oO][nN][gG]/, optional('"')),
      seq(optional('"'), /[sS][tT][rR][oO][nN][gG][aA][cC][cC][eE][nN][tT]/, optional('"')),
      seq(optional('"'), /[aA][tT][tT][eE][nN][tT][iI][oO][nN]/, optional('"')),
      seq(optional('"'), /[aA][tT][tT][eE][nN][tT][iI][oO][nN][aA][cC][cC][eE][nN][tT]/, optional('"')),
      seq(optional('"'), /[fF][aA][vV][oO][rR][aA][bB][lL][eE]/, optional('"')),
      seq(optional('"'), /[uU][nN][fF][aA][vV][oO][rR][aA][bB][lL][eE]/, optional('"')),
      seq(optional('"'), /[sS][uU][bB][oO][rR][dD][iI][nN][aA][tT][eE]/, optional('"'))
    ),

    run_page_mode_value: $ => choice(
      /[eE][dD][iI][tT]/,
      /[vV][iI][eE][wW]/,
      /[cC][rR][eE][aA][tT][eE]/
    ),

    // First 5 missing Page Field Properties
    assist_edit_property: $ => seq(
      'AssistEdit',
      '=',
      field('value', $.boolean),
      ';'
    ),
    
    column_span_property: $ => seq(
      'ColumnSpan',
      '=',
      field('value', $.column_span_value),
      ';'
    ),
    
    drill_down_property: $ => seq(
      'DrillDown',
      '=',
      field('value', $.boolean),
      ';'
    ),

    lookup_property: $ => prec(1, seq(
      'Lookup',
      '=',
      field('value', $.boolean),
      ';'
    )),
    
    hide_value_property: $ => prec(12, seq(
      'HideValue',
      '=',
      field('value', choice(
        prec(2, $.boolean),
        prec(1, $._expression)
      )),
      ';'
    )),
    
    multi_line_property: $ => seq(
      'MultiLine',
      '=',
      field('value', $.boolean),
      ';'
    ),
    
    importance_property: $ => seq(
      /[iI][mM][pP][oO][rR][tT][aA][nN][cC][eE]/,
      '=',
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
      '=',
      field('value', $.boolean),
      ';'
    ),

    row_span_property: $ => seq(
      'RowSpan',
      '=',
      field('value', $.integer),
      ';'
    ),

    width_property: $ => seq(
      'Width',
      '=',
      field('value', $.integer),
      ';'
    ),

    show_caption_property: $ => seq(
      /[sS][hH][oO][wW][cC][aA][pP][tT][iI][oO][nN]/,
      '=',
      field('value', $.boolean),
      ';'
    ),

    show_as_tree_property: $ => seq(
      'ShowAsTree',
      '=',
      field('value', $.boolean),
      ';'
    ),

    grid_layout_property: $ => seq(
      /[gG][rR][iI][dD][lL][aA][yY][oO][uU][tT]/,
      '=',
      field('value', $.grid_layout_value),
      ';'
    ),

    show_mandatory_property: $ => seq(
      'ShowMandatory',
      '=',
      field('value', $._expression),
      ';'
    ),

    style_property: $ => seq(
      'Style',
      '=',
      field('value', $.style_value),
      ';'
    ),

    style_expr_property: $ => seq(
      'StyleExpr',
      '=',
      field('value', choice(
        $.string_literal,
        $.identifier,
        $._quoted_identifier,
        $.call_expression,
        $.boolean,
        $.unary_expression,
        $.comparison_expression,
        $.qualified_enum_value
      )),
      ';'
    ),

    page_id_value: $ => choice(
      $.integer,
      $.identifier,
      prec(1, $._quoted_identifier)
    ),


    blank_zero_value: $ => $.boolean,

    option_caption_value: $ => $.string_literal,

    table_type_value: $ => choice(
      /[nN][oO][rR][mM][aA][lL]/,
      /[tT][eE][mM][pP][oO][rR][aA][rR][yY]/,
      /[eE][xX][tT][eE][rR][nN][aA][lL]/,
      /[sS][yY][sS][tT][eE][mM]/
    ),

    closing_dates_value: $ => $.boolean,
    char_allowed_value: $ => choice(
      $.string_literal,     // 'AZ', '0-9', etc.
      $.boolean,           // true/false (legacy?)
      $.identifier         // Variable reference
    ),
    compressed_value: $ => $.boolean,
    date_formula_value: $ => choice(
      $.string_literal,
      $.boolean,
      $.identifier  // Allow variable references
    ),
    usage_category_value: $ => choice(
      /[aA][dD][mM][iI][nN][iI][sS][tT][rR][aA][tT][iI][oO][nN]/,
      /[dD][oO][cC][uU][mM][eE][nN][tT][sS]/,
      /[lL][iI][sS][tT][sS]/,
      /[rR][eE][pP][oO][rR][tT][sS]/,
      /[tT][aA][sS][kK][sS]/,
      /[rR][eE][pP][oO][rR][tT][sS][aA][nN][dD][aA][nN][aA][lL][yY][sS][iI][sS]/,
      $.identifier,
      $._quoted_identifier
    ),
    external_access_value: $ => choice(
      /[eE][xX][tT][eE][rR][nN][aA][lL]/,
      /[iI][nN][tT][eE][rR][nN][aA][lL]/,
      /[lL][oO][cC][aA][lL]/
    ),
    external_name_value: $ => $.string_literal,
    external_type_value: $ => $.string_literal,
    init_value_value: $ => $._expression,
    max_value_value: $ => $._expression, 
    min_value_value: $ => $._expression,
    not_blank_value: $ => $.boolean,
    numeric_value: $ => $.boolean,
    obsolete_reason_value: $ => $.string_literal,
    obsolete_state_value: $ => choice(
      /[pP][eE][nN][dD][iI][nN][gG]/,
      /[rR][eE][mM][oO][vV][eE][dD]/
    ),
    obsolete_tag_value: $ => $.string_literal,
    option_ordinal_values_value: $ => $.string_literal,
    paste_is_valid_value: $ => $.boolean,
    sign_displacement_value: $ => $.boolean,
    sql_data_type_value: $ => $.string_literal,
    sql_timestamp_value: $ => $.boolean,
    test_table_relation_value: $ => $.boolean,
    tool_tip_value: $ => seq(
      $.string_literal,
      optional(seq(',', choice('Comment', 'comment', 'COMMENT'), '=', $.string_literal))
    ),
    unique_value: $ => $.boolean,
    validate_table_relation_value: $ => $.boolean,
    values_allowed_value: $ => seq(
      choice($.identifier, $._quoted_identifier, $.string_literal),
      repeat(seq(',', choice($.identifier, $._quoted_identifier, $.string_literal)))
    ),

    // NEW HIGH PRIORITY PROPERTIES - Value Rules
    data_caption_fields_value: $ => seq(
      choice($._quoted_identifier, $.string_literal, $.identifier),
      repeat(seq(',', choice($._quoted_identifier, $.string_literal, $.identifier)))
    ),

    extensible_value: $ => $.boolean,

    data_per_company_value: $ => $.boolean,

    replicate_data_value: $ => $.boolean,

    assignment_compatibility_value: $ => $.boolean,

    column_store_index_value: $ => seq(
      choice($.identifier, $._quoted_identifier),
      repeat(seq(',', choice($.identifier, $._quoted_identifier)))
    ),

    compression_type_value: $ => choice(
      /[nN][oO][nN][eE]/,
      /[pP][aA][gG][eE]/,
      /[rR][oO][wW]/,
      /[uU][nN][sS][pP][eE][cC][iI][fF][iI][eE][dD]/
    ),

    inherent_permissions_value: $ => $.permission_type,

    inherent_entitlements_value: $ => $.permission_type,

    access_value: $ => choice(
      /[pP][uU][bB][lL][iI][cC]/,
      /[iI][nN][tT][eE][rR][nN][aA][lL]/,
      /[pP][rR][iI][vV][aA][tT][eE]/
    ),

    access_by_permission_value: $ => seq(
      /[tT][aA][bB][lL][eE][dD][aA][tT][aA]/,
      field('table_name', $._table_reference),
      '=',
      field('permission', $.permission_type)
    ),

    auto_format_expression_value: $ => $._expression,

    auto_format_type_value: $ => choice(
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
      'TableType',
      '=',
      field('value', alias($.table_type_value, $.value)),
      ';'
    ),

    access_by_permission_property: $ => seq(
      'AccessByPermission',
      '=',
      field('value', alias($.access_by_permission_value, $.value)),
      ';'
    ),

    allow_in_customizations_property: $ => prec(1, seq(
      'AllowInCustomizations', 
      '=',
      field('value', choice(
        alias($.boolean, $.value),
        alias(choice('Never', 'NEVER', 'never'), $.value)
      )),
      ';'
    )),

    auto_format_expression_property: $ => seq(
      'AutoFormatExpression',
      '=',
      field('value', alias($.auto_format_expression_value, $.value)),
      ';'
    ),

    auto_format_type_property: $ => seq(
      'AutoFormatType',
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
      'Access',
      '=',
      field('value', alias($.access_value, $.value)),
      ';'
    ),

    closing_dates_property: $ => seq(
      'ClosingDates',
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
      'Compressed', 
      '=',
      field('value', $.compressed_value),
      ';'
    ),

    date_formula_property: $ => seq(
      'DateFormula',
      '=',
      field('value', $.date_formula_value),
      ';'
    ),

    description_property: $ => seq(
      alias(/[dD][eE][sS][cC][rR][iI][pP][tT][iI][oO][nN]/, 'Description'),
      '=',
      field('value', $.string_literal),
      ';'
    ),

    external_access_property: $ => seq(
      'ExternalAccess',
      '=',
      field('value', $.external_access_value),
      ';'
    ),

    external_name_property: $ => seq(
      'ExternalName',
      '=',
      field('value', $.external_name_value),
      ';'
    ),

    external_type_property: $ => seq(
      'ExternalType',
      '=',
      field('value', $.external_type_value),
      ';'
    ),

    init_value_property: $ => seq(
      'InitValue',
      '=',
      field('value', $.init_value_value),
      ';'
    ),

    max_value_property: $ => seq(
      'MaxValue',
      '=',
      field('value', $.max_value_value),
      ';'
    ),

    min_value_property: $ => seq(
      'MinValue',
      '=',
      field('value', $.min_value_value),
      ';'
    ),

    not_blank_property: $ => seq(
      'NotBlank',
      '=',
      field('value', $.not_blank_value),
      ';'
    ),

    numeric_property: $ => seq(
      'Numeric',
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
      'OptionOrdinalValues',
      '=',
      $.option_ordinal_values_value,
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
      'SqlDataType',
      '=',
      $.sql_data_type_value,
      ';'
    ),

    sql_timestamp_property: $ => seq(
      'SqlTimestamp',
      '=',
      $.sql_timestamp_value,
      ';'
    ),

    test_table_relation_property: $ => seq(
      'TestTableRelation',
      '=',
      $.test_table_relation_value,
      ';'
    ),

    tool_tip_property: $ => seq(
      choice('ToolTip', 'Tooltip', 'tooltip', 'TOOLTIP'),
      '=',
      $.tool_tip_value,
      ';'
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
      'ValuesAllowed',
      '=',
      field('value', $.values_allowed_value),
      ';'
    ),

    extended_datatype_property: $ => seq(
      'ExtendedDatatype',
      '=',
      field('value', $.extended_datatype_value),
      ';'
    ),

    // NEW HIGH PRIORITY PROPERTIES - Property Rules
    data_caption_fields_property: $ => seq(
      /[dD][aA][tT][aA][cC][aA][pP][tT][iI][oO][nN][fF][iI][eE][lL][dD][sS]/,
      '=',
      field('value', $.data_caption_fields_value),
      ';'
    ),

    extensible_property: $ => seq(
      'Extensible',
      '=',
      field('value', $.extensible_value),
      ';'
    ),

    data_per_company_property: $ => seq(
      'DataPerCompany',
      '=',
      field('value', $.data_per_company_value),
      ';'
    ),

    replicate_data_property: $ => seq(
      'ReplicateData',
      '=',
      field('value', $.replicate_data_value),
      ';'
    ),

    assignment_compatibility_property: $ => seq(
      'AssignmentCompatibility',
      '=',
      field('value', $.assignment_compatibility_value),
      ';'
    ),

    column_store_index_property: $ => seq(
      'ColumnStoreIndex',
      '=',
      field('value', $.column_store_index_value),
      ';'
    ),

    compression_type_property: $ => seq(
      'CompressionType',
      '=',
      field('value', $.compression_type_value),
      ';'
    ),

    inherent_permissions_property: $ => seq(
      'InherentPermissions',
      '=',
      field('value', $.inherent_permissions_value),
      ';'
    ),

    inherent_entitlements_property: $ => seq(
      'InherentEntitlements',
      '=',
      field('value', $.inherent_entitlements_value),
      ';'
    ),

    caption_ml_property: $ => seq(
      /[cC][aA][pP][tT][iI][oO][nN][mM][lL]/,
      '=',
      $.ml_value_list,
      ';'
    ),

    option_caption_ml_property: $ => seq(
      /[oO][pP][tT][iI][oO][nN][cC][aA][pP][tT][iI][oO][nN][mM][lL]/,
      '=',
      $.ml_value_list,
      ';'
    ),

    tool_tip_ml_property: $ => seq(
      'ToolTipML',
      '=',
      $.ml_value_list,
      ';'
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
      /[cC][uU][sS][tT][oO][mM][eE][rR][cC][oO][nN][tT][eE][nN][tT]/,
      /[eE][nN][dD][uU][sS][eE][rR][iI][dD][eE][nN][tT][iI][fF][iI][aA][bB][lL][eE][iI][nN][fF][oO][rR][mM][aA][tT][iI][oO][nN]/,
      /[aA][cC][cC][oO][uU][nN][tT][dD][aA][tT][aA]/,
      /[eE][nN][dD][uU][sS][eE][rR][pP][sS][eE][uU][dD][oO][nN][yY][mM][oO][uU][sS][iI][dD][eE][nN][tT][iI][fF][iI][eE][rR][sS]/,
      /[oO][rR][gG][aA][nN][iI][zZ][aA][tT][iI][oO][nN][iI][dD][eE][nN][tT][iI][fF][iI][aA][bB][lL][eE][iI][nN][fF][oO][rR][mM][aA][tT][iI][oO][nN]/,
      /[sS][yY][sS][tT][eE][mM][mM][eE][tT][aA][dD][aA][tT][aA]/,
      /[tT][oO][bB][eE][cC][lL][aA][sS][sS][iI][fF][iI][eE][dD]/
    ),


    onrun_trigger: $ => seq(
      $._trigger_keyword,
      choice('OnRun', 'ONRUN', 'Onrun'),
      $._trigger_parameters,
      optional($.var_section),
      $.code_block
    ),


    _table_element: $ => prec(1, choice(
      // Structural table elements (not properties)
      $.fields,  // Fields section should be primary
      $.keys,
      $.fieldgroups_section,
      $.var_section,
      
      // Table triggers
      $.oninsert_trigger,
      $.onmodify_trigger,
      $.ondelete_trigger,
      $.onrename_trigger,
      $.onvalidate_trigger,
      $.onaftergetrecord_trigger,
      $.onafterinsertevent_trigger,
      $.onaftermodifyevent_trigger,
      $.onafterdeleteevent_trigger,
      $.onbeforeinsertevent_trigger,
      $.onbeforemodifyevent_trigger,
      $.onbeforedeleteevent_trigger,
      
      // Procedures
      seq(optional($.attribute_list), $.procedure),
      
      // All table properties now centralized
      $._table_properties,
      
      // Preprocessor conditional table properties
      $.preproc_conditional_table_properties,
    )),

    // For single table permission property
    permissions_property: $ => seq(
      'Permissions',
      '=',
      $.tabledata_permission_list,
      ';'
    ),

    test_permissions_property: $ => seq(
      'TestPermissions',
      '=',
      choice('Disabled', 'NonRestrictive', 'Restrictive', 'InherentPermissions'),
      ';'
    ),

    permission_type: $ => token(
      prec(-1, choice(
        /[rRiImMdDxX]+/,
        'RCMDXI'  // Allow specific full permission string
      ))
    ),


    oninsert_trigger: $ => seq(
      $._trigger_keyword,
      choice('OnInsert', 'ONINSERT', 'Oninsert'),
      $._trigger_parameters,
      optional($.var_section),
      $.code_block
    ),

    onmodify_trigger: $ => seq(
      $._trigger_keyword,
      choice('OnModify', 'ONMODIFY', 'Onmodify'),
      $._trigger_parameters,
      optional($.var_section),
      $.code_block
    ),

    ondelete_trigger: $ => seq(
      $._trigger_keyword,
      choice('OnDelete', 'ONDELETE', 'Ondelete'),
      $._trigger_parameters,
      optional($.var_section),
      $.code_block
    ),

    onrename_trigger: $ => seq(
      $._trigger_keyword,
      choice('OnRename', 'ONRENAME', 'Onrename'),
      $._trigger_parameters,
      optional($.var_section),
      $.code_block
    ),

    onvalidate_trigger: $ => seq(
      $._trigger_keyword,
      choice('OnValidate', 'ONVALIDATE', 'Onvalidate'),
      $._trigger_parameters,
      optional($.var_section),
      $.code_block
    ),

    onaftergetrecord_trigger: $ => seq(
      $._trigger_keyword,
      choice('OnAfterGetRecord', 'ONAFTERGETRECORD', 'Onaftergetrecord'),
      $._trigger_parameters,
      optional($.var_section),
      $.code_block
    ),

    onafterinsertevent_trigger: $ => seq(
      $._trigger_keyword,
      choice('OnAfterInsertEvent', 'ONAFTERINSERTEVENT', 'Onafterinsertevent'),
      $._trigger_parameters,
      optional($.var_section),
      $.code_block
    ),

    onaftermodifyevent_trigger: $ => seq(
      $._trigger_keyword,
      choice('OnAfterModifyEvent', 'ONAFTERMODIFYEVENT', 'Onaftermodifyevent'),
      $._trigger_parameters,
      optional($.var_section),
      $.code_block
    ),

    onafterdeleteevent_trigger: $ => seq(
      $._trigger_keyword,
      choice('OnAfterDeleteEvent', 'ONAFTERDELETEEVENT', 'Onafterdeleteevent'),
      $._trigger_parameters,
      optional($.var_section),
      $.code_block
    ),

    onbeforeinsertevent_trigger: $ => seq(
      $._trigger_keyword,
      'OnBeforeInsertEvent',
      $._trigger_parameters,
      optional($.var_section),
      $.code_block
    ),

    onbeforemodifyevent_trigger: $ => seq(
      $._trigger_keyword,
      'OnBeforeModifyEvent',
      $._trigger_parameters,
      optional($.var_section),
      $.code_block
    ),

    onbeforedeleteevent_trigger: $ => seq(
      $._trigger_keyword,
      'OnBeforeDeleteEvent',
      $._trigger_parameters,
      optional($.var_section),
      $.code_block
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
      $.permissions_property,
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
      $.provider_property
    )),

    caption_property: $ => seq(
      field('name', alias(/[cC][aA][pP][tT][iI][oO][nN]/, 'Caption')),
      '=',
      $.string_literal,
      repeat(seq(
        ',',
        choice(
          seq(
            choice('Locked', 'locked', 'LOCKED'),
            '=',
            $.boolean
          ),
          seq(
            choice('Comment', 'comment', 'COMMENT'),
            '=',
            $.string_literal
          )
        )
      )),
      ';'
    ),

    caption_class_property: $ => seq(
      /[cC][aA][pP][tT][iI][oO][nN][cC][lL][aA][sS][sS]/,
      '=',
      field('value', $._expression),
      ';'
    ),

    calc_fields_property: $ => seq(
      'CalcFields',
      '=',
      field('fields', $.calc_fields_list),
      ';'
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
      'DataClassification',
      '=',
      $.data_classification_value,
      ';'
    ),


    tabledata_permission_list: $ => seq(
      $.tabledata_permission,
      repeat(seq(',', $.tabledata_permission)) // Changed optional to repeat for multiple permissions
    ),

    tabledata_permission: $ => seq(
      $._tabledata_keyword,
      field('table_name', $._table_identifier),
      '=',
      field('permission', $.permission_type)
    ),

    _table_identifier: $ => choice(
      $.identifier,
      $._quoted_identifier,
      $.integer
    ),


    decimal_places_property: $ => seq(
      'DecimalPlaces',
      '=',
      field('precision', $.integer),
      ':',
      field('scale', $.integer),
      ';'
    ),

    var_section: $ => prec.right(seq(
      optional(choice('protected', 'PROTECTED', 'Protected')),
      choice('var', 'VAR', 'Var'),
      repeat(choice(
        $.comment,
        $.multiline_comment,
        $.attribute_list,
        $.pragma,
        $.variable_declaration,
        $.preproc_conditional_variables
      ))
    )),

    // Helper rule for unquoted variable names (allows certain keywords as identifiers)
    _unquoted_variable_name: $ => choice(
      $.identifier,
      // Allow the keyword 'Description' to be treated as an identifier in variable contexts
      alias(/[dD][eE][sS][cC][rR][iI][pP][tT][iI][oO][nN]/, $.identifier),
      // Allow the keyword 'Importance' to be treated as an identifier in variable contexts
      alias(/[iI][mM][pP][oO][rR][tT][aA][nN][cC][eE]/, $.identifier),
      // Allow the keyword 'SourceTable' to be treated as an identifier in variable contexts
      alias(/[sS][oO][uU][rR][cC][eE][tT][aA][bB][lL][eE]/, $.identifier),
      // Allow the keyword 'IncludeCaption' to be treated as an identifier in variable contexts
      alias(/[iI][nN][cC][lL][uU][dD][eE][cC][aA][pP][tT][iI][oO][nN]/, $.identifier),
      // Allow the keyword 'ExcludeCaption' to be treated as an identifier in variable contexts
      alias(/[eE][xX][cC][lL][uU][dD][eE][cC][aA][pP][tT][iI][oO][nN]/, $.identifier),
      // Allow the keyword 'SubType' to be treated as an identifier in variable contexts
      alias('Subtype', $.identifier),
      // Allow the keyword 'Caption' to be treated as an identifier in variable contexts
      alias(/[cC][aA][pP][tT][iI][oO][nN]/, $.identifier),
      alias('SubType', $.identifier), 
      alias('subtype', $.identifier),
      alias('SUBTYPE', $.identifier),
      // Allow the keyword 'TableNo' to be treated as an identifier in variable contexts
      alias(/[tT][aA][bB][lL][eE][nN][oO]/, $.identifier)
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
      // Label variable declaration with string literal value
      prec(2, seq(
        field('names', $._variable_name_list),
        ':',
        field('type', alias(choice('Label', 'LABEL', 'label'), $.basic_type)),
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
      field('parameter_name', alias($.identifier, $.name)),
      ':',
      choice('option', 'OPTION', 'Option'), // Match the keyword
      field('parameter_type', alias($.option_member_list, $.option_type)) // Reuse option_member_list for members
    ),

    // Updated parameter rule to choose between standard types and inline options
    parameter: $ => choice(
      $._parameter_option, // Try matching inline option first
      seq( // Standard parameter with type_specification
        optional(field('modifier', $.modifier)),
        field('parameter_name', alias(choice($.identifier, $._quoted_identifier), $.name)),
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
  $.array_type,
  $.basic_type,
  $.text_type,
  $.code_type,
  $.record_type,
  $.recordref_type,
  $.fieldref_type,
  $.codeunit_type, 
  $.query_type,
  $.testpage_type,
  $.report_type,
  $.dotnet_type,
  $.list_type,
  $.dictionary_type,
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
  choice('Option', 'OPTION', 'option'),
  optional($.option_member_list) // Members are part of the type
)),

// Helper for comma-separated list of option members  
option_member_list: $ => prec.left(1, choice(
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
  prec(1, choice('Interface', 'INTERFACE', 'interface')),
  field('reference', choice(
    $._quoted_identifier,
    $.identifier
  ))
),

controladdin_type: $ => seq(
  choice('ControlAddIn', 'CONTROLADDIN', 'controladdin'),
  field('reference', choice(
    $._quoted_identifier,
    $.identifier
  ))
),

enum_type: $ => prec(1, seq(
  choice('Enum', 'ENUM', 'enum'),
  field('enum_name', choice($.identifier, $._quoted_identifier))
)),

    page_type: $ => seq(
      prec(1, choice('Page', 'PAGE', 'page')),
      field('reference', choice(
        $.integer,
        $._quoted_identifier,
        $.identifier
      ))
    ),

    report_type: $ => seq(
      prec(1, choice('Report', 'REPORT', 'report')),
      field('reference', choice(
        $.integer,
        $._quoted_identifier,
        $.identifier
      ))
    ),

    list_type: $ => seq(
      'List', 
      'of', 
      '[', 
      $.type_specification, 
      ']'
    ),

    dictionary_type: $ => seq(
      'Dictionary', 
      'of', 
      '[', 
      $.type_specification, 
      ',', 
      $.type_specification, 
      ']'
    ),


    basic_type: $ => choice(
      // Numeric Types
      prec(1, choice('Integer', 'INTEGER', 'Integer')),
      prec(1, choice('Decimal', 'DECIMAL', 'Decimal')),
      prec(1, choice('Byte', 'BYTE', 'Byte')),
      
      // Text Types
      prec(1, choice('Char', 'CHAR', 'Char')),
      
      // Date/Time Types
      prec(1, choice('Date', 'DATE', 'Date')),
      prec(1, choice('Time', 'TIME', 'Time')),
      prec(1, choice('DateTime', 'DATETIME', 'Datetime')),
      prec(1, choice('Duration', 'DURATION', 'Duration')),
      prec(1, choice('DateFormula', 'DATEFORMULA', 'Dateformula')),
      
      // Other Types
      prec(1, choice('Boolean', 'BOOLEAN', 'Boolean')),
      // Option removed, handled by option_type
      prec(1, choice('Guid', 'GUID', 'Guid')),
      prec(1, choice('RecordId', 'RECORDID', 'Recordid', 'RecordID')),
      prec(1, choice('Variant', 'VARIANT', 'Variant')),
      prec(1, choice('Label', 'LABEL', 'label')),
      prec(1, choice('Dialog', 'DIALOG', 'Dialog')),
      prec(1, choice('Action', 'ACTION', 'Action')),
      prec(1, choice('BLOB', 'Blob', 'blob')),
      prec(1, choice('FilterPageBuilder', 'FILTERPAGEBUILDER', 'Filterpagebuilder')),
      prec(1, choice('JsonToken', 'JSONTOKEN', 'Jsontoken')),
      prec(1, choice('JsonValue', 'JSONVALUE', 'Jsonvalue')),
      prec(1, choice('JsonArray', 'JSONARRAY', 'Jsonarray')),
      prec(1, choice('JsonObject', 'JSONOBJECT', 'Jsonobject')),
      prec(1, choice('Media', 'MEDIA', 'Media')),
      prec(1, choice('MediaSet', 'MEDIASET', 'Mediaset')),
      prec(1, choice('OStream', 'OSTREAM', 'Ostream')),
      prec(1, choice('InStream', 'INSTREAM', 'Instream')),
      prec(1, choice('OutStream', 'OUTSTREAM', 'Outstream')),
      prec(1, choice('SecretText', 'SECRETTEXT', 'Secrettext')),
      prec(1, choice('ModuleInfo', 'MODULEINFO', 'Moduleinfo')), 
      prec(1, choice('ObjectType', 'OBJECTTYPE', 'Objecttype')), 
      prec(1, choice('KeyRef', 'KEYREF', 'Keyref')), 

      // XML Types
      prec(1, choice('XmlDocument', 'XMLDOCUMENT', 'Xmldocument')),
      prec(1, choice('XmlNode', 'XMLNODE', 'Xmlnode')),
      prec(1, choice('XmlElement', 'XMLELEMENT', 'Xmlelement')),
      prec(1, choice('XmlNodeList', 'XMLNODELIST', 'Xmlnodelist')),
      prec(1, choice('XmlAttribute', 'XMLATTRIBUTE', 'Xmlattribute')),
      prec(1, choice('XmlAttributeCollection', 'XMLATTRIBUTECOLLECTION', 'Xmlattributecollection'))
    ),

    text_type: $ => prec.left(15, seq(
      choice('Text', 'TEXT', 'text'),
      optional(seq(
        '[',
        field('length', $.integer),
        ']'
      ))
    )),

    code_type: $ => prec.left(15, seq(
      choice('Code', 'CODE', 'code'),
      optional(seq(
        '[',
        field('length', $.integer),
        ']'
      ))
    )),

    record_type: $ => prec.right(seq(
      prec(1, choice('Record', 'RECORD', 'record')),
      field('reference', choice(
        prec(2, $.qualified_table_reference),
        prec(1, $._table_reference)
      )),
      optional(choice('Temporary', 'TEMPORARY', 'temporary'))
    )),

    // Dedicated rule for namespace-qualified table references (requires at least one dot)
    qualified_table_reference: $ => prec.right(10, seq(
      field('namespace', choice($.identifier, $._quoted_identifier)),
      repeat1(seq('.', field('part', choice($.identifier, $._quoted_identifier))))
    )),
    recordref_type: $ => /[rR][eE][cC][oO][rR][dD][rR][eE][fF]/,
    fieldref_type: $ => /[fF][iI][eE][lL][dD][rR][eE][fF]/,

    // Use existing _table_reference rule that already handles both plain and quoted identifiers 
    _table_reference: $ => choice(
      $.integer,
      $.identifier,
      $._quoted_identifier  // Already has precedence 2
    ),

    codeunit_type: $ => prec.right(20, seq(
      choice('Codeunit', 'codeunit', 'CODEUNIT', 'COdeunit'),
      field('reference', choice(
        $.integer,
        $._quoted_identifier,
        $.identifier,
        $.member_expression
      ))
    )),

    query_type: $ => seq(
      prec(1, 'Query'),
      field('reference', $.query_type_value)
    ),

    testpage_type: $ => seq(
      prec(1, choice(
        'TestPage',
        'Testpage',
        'TESTPAGE',
        'testpage'
      )),
      field('reference', choice(
        $.integer,
        $._quoted_identifier,
        $.identifier
      ))
    ),

    query_type_value: $ => choice(
      $.integer,
      $._quoted_identifier,
      $.identifier
    ),

    dotnet_type: $ => seq(
      prec(1, choice('DotNet', 'DOTNET', 'dotnet')),
      field('reference', choice($.dotnet_type_name, $.identifier, $.string_literal, $._quoted_identifier))
    ),

    array_type: $ => seq(
      prec(1, 'array'),
      '[',
      field('sizes', seq(
        $.integer,
        repeat(seq(',', $.integer))
      )),
      ']',
      'of',
      $.type_specification
    ),

    fields: $ => seq(
      choice('fields', 'FIELDS', 'Fields'),
      '{',
      repeat(choice($.field_declaration, $.modify_field_declaration)),
      '}'
    ),

    field_declaration: $ => seq(
      'field',
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
        repeat(choice(
          $.caption_property,
          $.caption_class_property,
          $.data_classification_property,
          $.decimal_places_property,
          $.field_trigger_declaration,
          $.access_by_permission_property,
          $.allow_in_customizations_property,
          $.auto_format_expression_property,
          $.auto_format_type_property,
          $.auto_increment_property,
          $.blank_numbers_property,
          $.auto_format_expression_property,
          $.table_relation_property,
          $.field_class_property,
          $.calc_formula_property,
          $.blank_zero_property,
          $.editable_property,
          $.option_members_property,
          $.option_caption_property,
          $.closing_dates_property,
          $.char_allowed_property,
          $.compressed_property,
          $.date_formula_property,
          $.description_property,
          $.external_access_property,
          $.external_name_property,
          $.external_type_property,
          $.init_value_property,
          $.max_value_property,
          $.min_value_property,
          $.not_blank_property,
          $.numeric_property,
          $.obsolete_reason_property,
          $.obsolete_state_property,
          $.obsolete_tag_property,
          $.option_ordinal_values_property,
          $.paste_is_valid_property,
          $.sign_displacement_property,
          $.sql_data_type_property,
          $.sql_timestamp_property,
          $.subtype_property,
          $.test_table_relation_property,
          $.tool_tip_property,
          $.unique_property,
          $.validate_table_relation_property,
          $.values_allowed_property,
          $.extended_datatype_property,
          $.caption_ml_property,
          $.option_caption_ml_property,
          $.tool_tip_ml_property,
          $.preproc_conditional_field_properties
        )),
        '}'
      ))
    ),

    modify_field_declaration: $ => seq(
      'modify',
      '(',
      field('name', choice(
        $._quoted_identifier,
        $.identifier
      )),
      ')',
      '{',
      repeat(choice(
        $.field_trigger_declaration,
        seq(optional($.attribute_list), $.trigger_declaration),
        $.caption_property,
        $.data_classification_property,
        $.decimal_places_property,
        $.access_by_permission_property,
        $.allow_in_customizations_property,
        $.auto_format_expression_property,
        $.auto_format_type_property,
        $.auto_increment_property,
        $.blank_numbers_property,
        $.table_relation_property,
        $.field_class_property,
        $.calc_formula_property,
        $.blank_zero_property,
        $.editable_property,
        $.option_members_property,
        $.option_caption_property,
        $.closing_dates_property,
        $.char_allowed_property,
        $.compressed_property,
        $.date_formula_property,
        $.description_property,
        $.external_access_property,
        $.external_name_property,
        $.external_type_property,
        $.init_value_property,
        $.max_value_property,
        $.min_value_property,
        $.not_blank_property,
        $.numeric_property,
        $.obsolete_reason_property,
        $.obsolete_state_property,
        $.obsolete_tag_property,
        $.option_ordinal_values_property,
        $.paste_is_valid_property,
        $.sign_displacement_property,
        $.sql_data_type_property,
        $.sql_timestamp_property,
        $.subtype_property,
        $.test_table_relation_property,
        $.tool_tip_property,
        $.unique_property,
        $.validate_table_relation_property,
        $.values_allowed_property,
        $.extended_datatype_property,
        $.caption_ml_property,
        $.option_caption_ml_property,
        $.tool_tip_ml_property,
        $.preproc_conditional_field_properties
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
        $.table_relation_expression,
        seq($.table_relation_expression, ';')
      ),
      optional(seq(
        $.preproc_else,
        choice(
          $.table_relation_expression,
          seq($.table_relation_expression, ';')
        )
      )),
      $.preproc_endif
    ),

    // Unified where clause implementation
    where_clause: $ => seq(
      /[wW][hH][eE][rR][eE]/,
      '(',
      field('conditions', $.where_conditions),
      ')'
    ),

    if_table_relation: $ => prec.right(1, seq(
      choice('IF', 'if', 'If'),
      '(',
      field('condition', $.unified_where_conditions),
      ')',
      field('then_relation', $.simple_table_relation),
      optional(seq(
        choice('ELSE', 'else', 'Else'),
        field('else_relation', $.table_relation_expression)
      ))
    )),

    simple_table_relation: $ => seq(
      field('table', $._table_reference),
      optional(seq('.', field('field', $.field_ref))),
      optional($.where_clause)
    ),

    const_filter: $ => prec(10, seq(
      field('field', $.field_ref),
      '=',
      choice('CONST', 'const', 'Const'),
      '(',
      optional(field('value', choice(
        $.string_literal,
        $.identifier,
        $._quoted_identifier,
        $.integer,
        $.boolean,
        $.database_reference
      ))),
      ')'
    )),

    field_filter: $ => prec(10, seq(
      field('field', $.field_ref),
      '=', 
      choice('FIELD', 'field', 'Field'),
      '(',
      field('value', $.field_ref),
      ')'
    )),

    filter_condition: $ => prec(10, seq(
      field('field', $.field_ref),
      '=',
      field('filter', $.filter_expression_function)
    )),

    where_condition: $ => choice(
      $.filter_expression,  // Add filter_expression for SourceTableView
      $.const_filter,
      $.field_filter,
      $.filter_condition
    ),

    where_conditions: $ => seq(
      $.where_condition,
      repeat(seq(',', $.where_condition))
    ),


    explicit_field_ref: $ => prec(12, seq(
      choice('field', 'FIELD', 'Field'),
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
        $.count_formula
      ))
    ),

    lookup_formula: $ => prec(10, seq(
      choice('lookup', 'LOOKUP', 'Lookup'),
      '(',
      field('target', choice(
        prec(20, $.member_expression),
        prec(15, $.field_access),
        prec(10, $._quoted_identifier),
        prec(5, $.identifier)
      )),
      optional(choice(
        // Original lookup where clause format
        seq(
          choice('where', 'WHERE', 'Where'),
          '(',
          $.lookup_where_conditions,
          ')'
        ),
        // New unified where clause format
        $.where_clause
      )),
      ')'
    )),


    lookup_where_conditions: $ => seq(
      $.lookup_where_condition,
      repeat(seq(',', $.lookup_where_condition))
    ),

    lookup_where_condition: $ => seq(
      field('field', $.field_ref),
      '=',
      choice(
        seq(
          choice('field', 'FIELD', 'Field'),
          '(',
          field('value', $.field_ref),
          ')'
        ),
        seq(
          field('keyword', alias(choice('const', 'CONST', 'Const'), $.const)),
          '(',
          optional(field('value', choice($.string_literal, $.identifier, $._quoted_identifier, $.integer))),
          ')'
        )
      )
    ),

    // Rule for calc formula WHERE conditions with higher precedence to resolve conflicts
    // === Unified WHERE Condition Types ===
    
    // Filter expression condition (standard style with operators)
    filter_expression_condition: $ => seq(
      field('field', $.field_ref),
      field('operator', $.filter_operator),
      field('value', $.filter_value)
    ),
    
    // FIELD(...) reference condition for formulas
    field_reference_condition: $ => prec(17, seq(
      field('field', $.field_ref),
      '=',
      choice('field', 'FIELD', 'Field'),
      '(',
      field('reference', $.field_ref),
      ')'
    )),
    
    // CONST(...) value condition for formulas
    const_value_condition: $ => prec(16, seq(
      field('field', $.field_ref),
      '=',
      choice('const', 'CONST', 'Const'),
      '(',
      optional(field('value', choice($.string_literal, $.field_ref, $.integer, $.boolean))),
      ')'
    )),
    
    // Unified where condition rule
    unified_where_condition: $ => choice(
      $.filter_expression_condition,
      $.field_reference_condition,
      $.const_value_condition
    ),
    
    // Unified where conditions list that handles both styles
    unified_where_conditions: $ => choice(
      // AND-separated style (filter expressions)
      seq(
        $.unified_where_condition,
        repeat(seq(
          optional(/[aA][nN][dD]/),
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
      choice('count', 'COUNT', 'Count'),
      '(',
      field('table', alias($._table_reference, $.table_reference)),
      $.where_clause,
      ')'
    ),

    sum_formula: $ => seq(
      choice('sum', 'SUM', 'Sum'),
      '(',
      field('target', $.calc_field_ref),
      $.where_clause,
      ')'
    ),

    average_formula: $ => seq(
      choice('average', 'AVERAGE', 'Average'),
      '(',
      field('target', $.calc_field_ref),
      $.where_clause,
      ')'
    ),

    min_formula: $ => seq(
      choice('min', 'MIN', 'Min'),
      '(',
      field('target', $.calc_field_ref),
      $.where_clause,
      ')'
    ),

    max_formula: $ => seq(
      choice('max', 'MAX', 'Max'),
      '(',
      field('target', $.calc_field_ref),
      $.where_clause,
      ')'
    ),

    exist_formula: $ => seq(
      choice('exist', 'EXIST', 'Exist'),
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
      'Editable',
      '=',
      $.editable_value,
      ';'
    ),

    processing_only_property: $ => seq(
      'ProcessingOnly',
      '=',
      choice(
        /[tT][rR][uU][eE]/,
        /[fF][aA][lL][sS][eE]/
      ),
      ';'
    ),

    use_request_page_property: $ => seq(
      'UseRequestPage',
      '=',
      choice(
        /[tT][rR][uU][eE]/,
        /[fF][aA][lL][sS][eE]/
      ),
      ';'
    ),

    option_members_property: $ => prec(1, seq(
      'OptionMembers',
      '=',
      choice(
        $.string_literal,  // Single string literal case
        field('value', $.option_member_list)  // Multiple members case
      ),
      ';'
    )),

    // Rule for option members (used in lists like parameters or OptionMembers property)
    option_member: $ => choice(
      $.identifier,
      $._quoted_identifier,
      $.string_literal 
    ),

    option_caption_property: $ => seq(
      /[oO][pP][tT][iI][oO][nN][cC][aA][pP][tT][iI][oO][nN]/,
      '=',
      $.option_caption_value,
      repeat(seq(
        ',',
        choice(
          seq(
            choice('Comment', 'comment', 'COMMENT'),
            '=',
            $.string_literal
          )
        )
      )),
      ';'
    ),

    field_trigger_declaration: $ => seq(
      $._trigger_keyword,
      field('type', alias(choice(
        choice('OnValidate', 'ONVALIDATE', 'Onvalidate'),
        choice('OnAfterValidate', 'ONAFTERVALIDATE', 'OnAfterValidate'),
        choice('OnLookup', 'ONLOOKUP', 'Onlookup'),
        choice('OnAssistEdit', 'ONASSISTEDIT', 'OnAssistEdit'),
        choice('OnDrillDown', 'ONDRILLDOWN', 'OnDrillDown')
      ), $.trigger_type)),
      choice(
        seq('(', optional($.parameter_list), ')'),
        seq()
      ),
      optional(seq(':', $.type_specification)),
      optional(';'),  // Allow optional semicolon after return type
      optional($.var_section),
      $.code_block
    ),

    keys: $ => seq(
      choice('keys', 'KEYS', 'Keys'),
      '{',
      repeat($.key_declaration),
      '}'
    ),

    key_declaration: $ => seq(
      'key',
      '(',
      field('name', alias($.identifier, $.name)),
      ';',
      field('fields', $.key_field_list),
      ')',
      optional(seq(
        '{',
        repeat(choice(
          $.clustered_property,
          $.included_fields_property,
          $.maintain_sift_index_property,
          $.maintain_sql_index_property,
          $.sql_index_property,
          $.sum_index_fields_property,
          $.property
        )),
        '}'
      ))
    ),

    // Key property rules
    included_fields_property: $ => seq(
      'IncludedFields',
      '=',
      $.key_field_list,
      ';'
    ),
    
    maintain_sift_index_property: $ => seq(
      'MaintainSiftIndex',
      '=',
      $.boolean,
      ';'
    ),
    
    maintain_sql_index_property: $ => seq(
      'MaintainSqlIndex',
      '=',
      $.boolean,
      ';'
    ),
    
    sql_index_property: $ => seq(
      'SqlIndex',
      '=',
      $.key_field_list,
      ';'
    ),
    
    sum_index_fields_property: $ => seq(
      'SumIndexFields',
      '=',
      $.key_field_list,
      ';'
    ),

    key_field_list: $ => seq(
      $._identifier_choice,
      repeat(seq(',', $._identifier_choice))
    ),

    attribute_list: $ => prec.left(repeat1($.attribute)),

    attribute: $ => seq(
      '[', 
      field('attribute_name', $.identifier), 
      optional($.attribute_arguments), 
      ']'
    ),

    attribute_arguments: $ => seq(
      '(',
      field('arguments', $.expression_list),
      ')'
    ),

    expression_list: $ => seq(
      $._expression,
      repeat(seq(',', $._expression))
    ),

    return_value: $ => field('return_value', choice($.identifier, $._quoted_identifier)),

    _procedure_return_specification: $ => seq(
      ':',
      field('return_type', $.return_type)
    ),

    _procedure_named_return: $ => seq(
      $.return_value,
      $._procedure_return_specification
    ),

    // Use the consistent type_specification rule for return types
    return_type: $ => $.type_specification,

    _procedure_name: $ => alias(choice($.identifier, $._quoted_identifier), $.name),

    procedure_modifier: $ => choice('local', 'LOCAL', 'Local', 'internal', 'INTERNAL', 'Internal', 'protected', 'PROTECTED', 'Protected'),

    procedure: $ => seq(
      optional(field('modifier', $.procedure_modifier)), 
      choice('procedure', 'PROCEDURE', 'Procedure'),
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
      optional($.var_section),
      $.code_block
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
      $.parameter,
      repeat(seq(';', $.parameter))
    ),

    modifier: $ => choice('var', 'VAR', 'Var'),

    identifier: $ => /[A-Za-z_][A-Za-z0-9_]*/,

    _quoted_identifier: $ => alias(
      token(prec(10, seq('"', /[^"\n]+/, '"'))),
      $.quoted_identifier
    ),

    string_literal: $ => token(
      choice(
        // Empty string
        seq("'", "'"),
        
        // Non-empty string - simplified to handle single backslash
        seq(
          "'",
          repeat1(choice(
            /[^'\n]+/,     // One or more chars except quote or newline (allows backslash)
            "''"           // Two consecutive single quotes as an escape
          )),
          "'"
        )
      )
    ),

    clustered_property: $ => seq(
      'Clustered',
      '=',
      field('value', $.boolean),
      ';'
    ),

    // Define boolean literals as tokens with precedence
    boolean: $ => choice(
      token(prec(1, choice('true', 'TRUE', 'True'))),
      token(prec(1, choice('false', 'FALSE', 'False')))
    ),

    grid_layout_value: $ => choice(
      'Rows',
      'Columns'
    ),

    temporary: $ => choice('temporary', 'TEMPORARY', 'Temporary'),


    // Define code blocks with explicit keyword handling
    code_block: $ => prec.right(1, seq(
      choice('begin', 'BEGIN', 'Begin'),
      optional(repeat($._statement_or_preprocessor)),
      choice('end', 'END', 'End'),
      optional(token(';')) // Explicit token
    )),

    _statement_or_preprocessor: $ => choice(
      $._statement,
      $.preproc_conditional_statements,
      $.pragma
    ),

    preproc_conditional_statements: $ => seq(
      $.preproc_if,
      repeat($._statement),
      optional(seq(
        $.preproc_else,
        repeat($._statement)
      )),
      $.preproc_endif
    ),

    _expression_statement: $ => $._expression, // New rule

    // Rule for empty statements (standalone semicolons)
    empty_statement: $ => ';',

    _statement: $ => prec.right(seq(
      choice(
        $.empty_statement, // Add support for standalone semicolons
        $.assignment_statement,
        $.exit_statement,
        // $.call_expression, // Removed direct call_expression
        $.if_statement,
        $.repeat_statement,
        $.case_statement,
        $.for_statement,
        $.foreach_statement,
        $.while_statement,
        $.with_statement,
        $._expression_statement
      ),
      optional(';')
    )),

    while_statement: $ => prec.right(seq(
      choice('while', 'WHILE', 'While'),
      field('condition', $._expression),
      choice('do', 'DO', 'Do'),
      field('body', choice(
        $._statement,
        $.code_block
      ))
    )),

    with_statement: $ => prec.right(seq(
      choice('with', 'WITH', 'With'),
      field('record_variable', $._expression),
      choice('do', 'DO', 'Do'),
      field('body', choice(
        $._statement,
        $.code_block
      ))
    )),

    for_statement: $ => prec.right(seq(
      choice('for', 'FOR', 'For'),
      field('variable', $.identifier),
      ':=',
      field('start', $._expression),
      field('direction', choice(
        choice('to', 'TO', 'To'),
        choice('downto', 'DOWNTO', 'Downto')
      )),
      field('end', $._expression),
      choice('do', 'DO', 'Do'),
      field('body', choice(
        $._statement,
        $.code_block
      ))
    )),

    foreach_statement: $ => prec.right(seq(
      choice('foreach', 'FOREACH', 'Foreach'),
      field('variable', $.identifier),
      choice('in', 'IN', 'In'),
      field('iterable', $._expression),
      choice('do', 'DO', 'Do'),
      field('body', choice(
        $._statement,
        $.code_block
      ))
    )),

    // Removed procedure_call rule

    repeat_statement: $ => seq(
      choice('repeat', 'REPEAT', 'Repeat'),
      repeat($._statement),
      choice('until', 'UNTIL', 'Until'),
      field('condition', $._expression)
    ),

    exit_statement: $ => prec(13, seq(
      choice('exit', 'EXIT', 'Exit'),
      optional(seq(
        token.immediate('('), // Ensure '(' immediately follows 'exit' if present
        optional(field('return_value', $._expression)),
        ')'
      )))
    ),

    assignment_statement: $ => seq(
      field('left', $._assignable_expression),
      field('operator', $._assignment_operator),
      field('right', $._expression)
    ),

    _assignable_expression: $ => $._expression,

    // Unified call expression rule
// Unified call expression rule
    call_expression: $ => prec(12, seq( // Increased precedence to 12 (higher than member_expression)
      // Function can be an identifier, member access, or field access
      field('function', choice(
        $.identifier,
        $.member_expression,
        $.field_access
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


    qualified_enum_value_tail: $ => prec.left(15, seq( // Higher precedence to attach to field_access
      '::',
      choice($.identifier, $._quoted_identifier)
    )),

    unary_expression: $ => prec.right(7, seq( // Keep at 7 but verify context
      choice('+', '-', 'not', 'Not', 'NOT'),
      $._expression
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
        field('operator', choice('is', 'IS', 'Is')),
        field('right', $.type_specification)
      )),
      // 'as' expression (prec 5) - interface casting
      prec.left(5, seq(
        field('left', $._expression),
        field('operator', choice('as', 'AS', 'As')),
        field('right', $.type_specification)
      )),
      $.logical_expression,
      // --- Other Expression Forms ---
      // Method chains (put this first among non-binary expressions for higher precedence)
      $.call_expression, // (prec 12)
      $.enum_keyword_qualified_value, // (prec 9)
      $.enum_type_reference, // (prec 8)
      $.qualified_enum_value, // (prec 20)
      $.database_reference, // (prec 9)
      $.field_access,  // (prec 12)
      $.member_expression, // (prec 11)
      $.subscript_expression, // (prec 9)
      $.identifier,
      $._quoted_identifier,
      $._literal_value,
      $.parenthesized_expression,
      $.unary_expression // (prec 7)
    ),

    // Explicit binary expression rules for proper precedence handling
    range_expression: $ => prec.left(8, seq(
      field('left', $._expression),
      field('operator', '..'),
      field('right', $._expression)
    )),

    multiplicative_expression: $ => prec.left(7, seq(
      field('left', $._expression),
      field('operator', choice('*', '/', /[dD][iI][vV]/, /[mM][oO][dD]/)),
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

    // 'in' operator
    in_operator: $ => choice('in', 'IN', 'In'),

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
      field('property', choice($.identifier, $._quoted_identifier))
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

    if_statement: $ => prec.right(seq(
      choice('if', 'IF', 'If'),
      field('condition', $._expression),
      choice('then', 'THEN', 'Then'),
      field('then_branch', choice(
        $.code_block,
        $._if_then_body
      )),
      optional(seq(
        choice('else', 'ELSE', 'Else'),
        field('else_branch', choice(
          $.code_block,
          prec(1, $.if_statement),
          $._if_then_body
        ))
      ))
    )),

    // Helper rule for if statement bodies
    _if_then_body: $ => prec.right(seq(
      repeat($.pragma),
      $._statement,
      repeat($.pragma)
    )),

    // Case expression uses the general _expression rule
    _case_expression: $ => $._expression,

    case_statement: $ => prec(2, seq(
      choice('case', 'CASE', 'Case'),
      field('expression', $._case_expression),
      choice('of', 'OF', 'Of'),
      repeat1($._case_item),
      optional($.else_branch),
      choice('end', 'END', 'End')
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
        $._statement
      ))
    ),

    preproc_conditional_case: $ => seq(
      $.preproc_if,
      repeat1($.case_branch),
      optional(seq(
        $.preproc_else,
        repeat1($.case_branch)
      )),
      $.preproc_endif
    ),

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
      // Arithmetic expressions (high precedence for DATABASE::"Table" + 1 patterns)
      prec(11, $.additive_expression),
      prec(11, $.multiplicative_expression),
      $.database_reference, // Allow DATABASE::"Table Name" patterns
      $._chained_expression, // Allow member expressions like Value.IsInteger
      $.unary_expression, // Allow NOT expressions in case patterns
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
      seq(/\d+/, '.', /\d+/)
    )),

    integer: $ => token(seq(
      optional('-'),  // Only allow negative sign
      /\d+/
    )),

    time_literal: $ => token(seq(
      optional('-'),
      /\d+(\.\d+)?/,  // Allow decimal time values like 235959.999T
      /[tT]/
    )),

    datetime_literal: $ => token(seq(
      optional('-'),
      /\d+/,
      /[dD][tT]/
    )),

    duration_literal: $ => token(seq(
      optional('-'),
      /\d+/,
      /[dD]/
    )),

    _literal_value: $ => choice(
      $.time_literal, 
      $.datetime_literal,
      $.duration_literal,
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
      choice('else', 'ELSE', 'Else'),
      field('statements', $._branch_statements)
    ),

    // DATABASE references (DATABASE::Customer pattern)
    database_reference: $ => prec.left(9, seq(
      choice('DATABASE', 'database', 'Database'),
      '::',
      field('table_name', choice($.identifier, $._quoted_identifier))
    )),

    // Rule for expressions using Enum keyword with double qualification (Enum::"Type"::"Value")
    enum_keyword_qualified_value: $ => prec.left(9, seq( // Increased precedence
      choice('Enum', 'ENUM', 'enum'),
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
      choice('Enum', 'ENUM', 'enum'),
      field('operator', $._double__colon),
      field('enum_type', choice(
        $._quoted_identifier,
        $.identifier
      ))
    )),

    qualified_enum_value: $ => prec.left(20, seq( // Increased precedence
      field('enum_type', choice(
        $._enum_type_reference,
        $.identifier,
        $._quoted_identifier,
        $.field_access,
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

    _enum_value_reference: $ => prec.left(2, choice(
      $._quoted_identifier,
      $.identifier,
      $._chained_expression,
      $.string_literal,
      $._enum_keyword  // Common AL keywords used as enum values
    )),

    _branch_statements: $ => choice(
      $._statement,
      $.code_block
    ),

    fieldgroup_declaration: $ => seq(
      /[fF][iI][eE][lL][dD][gG][rR][oO][uU][pP]/,
      '(',
      field('group_type', $.identifier),
      token(';'),
      field('fields', $.fieldgroup_list),
      ')',
      optional(seq(
        '{',
        // (Leave empty or add fieldgroup properties in the future)
        '}'
      ))
    ),

    fieldgroups_section: $ => prec(3, seq(
      /[fF][iI][eE][lL][dD][gG][rR][oO][uU][pP][sS]/,
      '{',
      repeat($.fieldgroup_declaration),
      '}'
    )),

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
      /[nN][oO]/,
      /[uU][pP][dD][aA][tT][eE][dD]/,
      /[bB][oO][tT][hH]/,
      $.string_literal,
      $.identifier,
      $._quoted_identifier
    ),

    cuegroup_layout_property: $ => seq(
      'CuegroupLayout',
      '=',
      field('value', choice($.identifier, $._quoted_identifier, $.string_literal)),
      ';'
    ),

    freeze_column_property: $ => seq(
      'FreezeColumn',
      '=',
      field('value', choice($.identifier, $._quoted_identifier, $.string_literal)),
      ';'
    ),

    indentation_column_property: $ => seq(
      'IndentationColumn',
      '=',
      field('value', choice($.integer, $.identifier, $._quoted_identifier)),
      ';'
    ),

    indentation_controls_property: $ => seq(
      'IndentationControls',
      '=',
      field('value', choice($.identifier, $._quoted_identifier)),
      ';'
    ),

    custom_action_type_property: $ => seq(
      'CustomActionType',
      '=',
      field('value', choice($.identifier, $._quoted_identifier, $.string_literal)),
      ';'
    ),

    allowed_file_extensions_property: $ => seq(
      'AllowedFileExtensions',
      '=',
      field('value', choice($.identifier, $._quoted_identifier, $.string_literal)),
      ';'
    ),

    allow_multiple_files_property: $ => seq(
      'AllowMultipleFiles',
      '=',
      field('value', $.boolean),
      ';'
    ),

    file_upload_action_property: $ => seq(
      'FileUploadAction',
      '=',
      field('value', choice($.identifier, $._quoted_identifier, $.string_literal)),
      ';'
    ),

    file_upload_row_action_property: $ => seq(
      'FileUploadRowAction',
      '=',
      field('value', choice($.identifier, $._quoted_identifier, $.string_literal)),
      ';'
    ),

    odata_edm_type_property: $ => seq(
      'ODataEDMType',
      '=',
      field('value', choice($.identifier, $._quoted_identifier, $.string_literal)),
      ';'
    ),

    // Missing page properties - Clear operations
    clear_actions_property: $ => seq(
      'ClearActions',
      '=',
      field('value', $.boolean),
      ';'
    ),

    clear_layout_property: $ => seq(
      'ClearLayout',
      '=',
      field('value', $.boolean),
      ';'
    ),

    clear_views_property: $ => seq(
      'ClearViews',
      '=',
      field('value', $.boolean),
      ';'
    ),

    // ShowAs property (different from ShowAsTree)
    show_as_property: $ => seq(
      'ShowAs',
      '=',
      field('value', choice(
        /[sS][pP][lL][iI][tT][bB][uU][tT][tT][oO][nN]/,  // SplitButton
        /[mM][eE][nN][uU]/,                               // Menu
        /[bB][uU][tT][tT][oO][nN]/                        // Button
      )),
      ';'
    ),

    // Low priority properties
    importance_additional_property: $ => seq(
      /[iI][mM][pP][oO][rR][tT][aA][nN][cC][eE][aA][dD][dD][iI][tT][iI][oO][nN][aA][lL]/,
      '=',
      field('value', $.boolean),
      ';'
    ),

    include_caption_property: $ => seq(
      /[iI][nN][cC][lL][uU][dD][eE][cC][aA][pP][tT][iI][oO][nN]/,
      '=',
      field('value', $.boolean),
      ';'
    ),

    // Critical report layout properties
    default_rendering_layout_property: $ => seq(
      'DefaultRenderingLayout',
      '=',
      field('value', choice($.identifier, $._quoted_identifier, $.string_literal)),
      ';'
    ),

    excel_layout_property: $ => seq(
      'ExcelLayout',
      '=',
      field('value', choice($.identifier, $._quoted_identifier, $.string_literal)),
      ';'
    ),

    rdlc_layout_property: $ => seq(
      'RDLCLayout',
      '=',
      field('value', choice($.identifier, $._quoted_identifier, $.string_literal)),
      ';'
    ),

    word_layout_property: $ => seq(
      'WordLayout',
      '=',
      field('value', choice($.identifier, $._quoted_identifier, $.string_literal)),
      ';'
    ),

    // High priority report properties
    allow_scheduling_property: $ => seq(
      'AllowScheduling',
      '=',
      field('value', $.boolean),
      ';'
    ),

    preview_mode_property: $ => seq(
      'PreviewMode',
      '=',
      field('value', choice(
        /[nN][oO][rR][mM][aA][lL]/,        // Normal
        /[pP][rR][iI][nN][tT][lL][aA][yY][oO][uU][tT]/,  // PrintLayout
        /[nN][oO][nN][eE]/                 // None
      )),
      ';'
    ),

    show_print_status_property: $ => seq(
      'ShowPrintStatus',
      '=',
      field('value', $.boolean),
      ';'
    ),

    transaction_type_property: $ => seq(
      'TransactionType',
      '=',
      field('value', choice(
        /[uU][pP][dD][aA][tT][eE]/,        // Update
        /[sS][nN][aA][pP][sS][hH][oO][tT]/, // Snapshot
        /[bB][rR][oO][wW][sS][eE]/          // Browse
      )),
      ';'
    ),

    execution_timeout_property: $ => seq(
      'ExecutionTimeout',
      '=',
      field('value', $.integer),
      ';'
    ),

    format_region_property: $ => seq(
      'FormatRegion',
      '=',
      field('value', choice($.identifier, $._quoted_identifier, $.string_literal)),
      ';'
    ),

    use_system_printer_property: $ => seq(
      'UseSystemPrinter',
      '=',
      field('value', $.boolean),
      ';'
    ),

    maximum_dataset_size_property: $ => seq(
      'MaximumDatasetSize',
      '=',
      field('value', $.integer),
      ';'
    ),

    // Table external/integration properties
    optimize_for_text_search_property: $ => seq(
      'OptimizeForTextSearch',
      '=',
      field('value', $.boolean),
      ';'
    ),

    // Medium priority report properties
    enable_external_assemblies_property: $ => seq(
      'EnableExternalAssemblies',
      '=',
      field('value', $.boolean),
      ';'
    ),

    enable_external_images_property: $ => seq(
      'EnableExternalImages',
      '=',
      field('value', $.boolean),
      ';'
    ),

    enable_hyperlinks_property: $ => seq(
      'EnableHyperlinks',
      '=',
      field('value', $.boolean),
      ';'
    ),

    excel_layout_multiple_data_sheets_property: $ => seq(
      'ExcelLayoutMultipleDataSheets',
      '=',
      field('value', $.boolean),
      ';'
    ),

    maximum_document_count_property: $ => seq(
      'MaximumDocumentCount',
      '=',
      field('value', $.integer),
      ';'
    ),

    paper_source_default_page_property: $ => seq(
      'PaperSourceDefaultPage',
      '=',
      field('value', choice($.identifier, $._quoted_identifier, $.string_literal)),
      ';'
    ),

    paper_source_first_page_property: $ => seq(
      'PaperSourceFirstPage',
      '=',
      field('value', choice($.identifier, $._quoted_identifier, $.string_literal)),
      ';'
    ),

    paper_source_last_page_property: $ => seq(
      'PaperSourceLastPage',
      '=',
      field('value', choice($.identifier, $._quoted_identifier, $.string_literal)),
      ';'
    ),

    // Low priority report properties
    pdf_font_embedding_property: $ => seq(
      'PdfFontEmbedding',
      '=',
      field('value', choice(
        /[yY][eE][sS]/,                    // Yes
        /[nN][oO]/,                       // No
        /[nN][oO][nN][sS][tT][aA][nN][dD][aA][rR][dD]/ // NonStandard
      )),
      ';'
    ),

    print_only_if_detail_property: $ => seq(
      'PrintOnlyIfDetail',
      '=',
      field('value', $.boolean),
      ';'
    ),

    word_merge_data_item_property: $ => seq(
      'WordMergeDataItem',
      '=',
      field('value', choice($.identifier, $._quoted_identifier, $.string_literal)),
      ';'
    ),

    data_item_link_reference_property: $ => seq(
      'DataItemLinkReference',
      '=',
      field('value', choice($.identifier, $._quoted_identifier, $.string_literal)),
      ';'
    ),

    title_property: $ => seq(
      'Title',
      '=',
      field('value', $.boolean),
      ';'
    ),

    filters_property: $ => seq(
      'Filters',
      '=',
      field('value', choice(
        $.identifier,
        $._quoted_identifier,
        $.string_literal,
        $.filter_expression
      )),
      ';'
    ),

    order_by_property: $ => seq(
      'OrderBy',
      '=',
      field('value', choice(
        $.identifier,
        $._quoted_identifier,
        $.string_literal
      )),
      ';'
    ),

    ellipsis_property: $ => seq(
      'Ellipsis',
      '=',
      field('value', $.boolean),
      ';'
    ),

    gesture_property: $ => seq(
      'Gesture',
      '=',
      field('value', choice($.identifier, $._quoted_identifier, $.string_literal)),
      ';'
    ),

    is_header_property: $ => seq(
      'IsHeader',
      '=',
      field('value', $.boolean),
      ';'
    ),

    provider_property: $ => seq(
      'Provider',
      '=',
      field('value', choice($.identifier, $._quoted_identifier, $.string_literal)),
      ';'
    ),


    shared_layout_property: $ => seq(
      'SharedLayout',
      '=',
      field('value', $.boolean),
      ';'
    ),

    data_item_table_view_property: $ => seq(
      'DataItemTableView',
      '=',
      field('value', $.source_table_view_value),
      ';'
    ),

    sorting_expression: $ => seq(
      choice('SORTING', 'Sorting', 'sorting'),
      '(',
      $.field_list,
      ')'
    ),

    field_list: $ => seq(
      choice($.identifier, $._quoted_identifier),
      repeat(seq(',', choice($.identifier, $._quoted_identifier)))
    ),

    // Preprocessor conditional rules for layout sections
    preproc_conditional_layout: $ => seq(
      $.preproc_if,
      repeat($._layout_element),
      optional(seq(
        $.preproc_else,
        repeat($._layout_element)
      )),
      $.preproc_endif
    ),

    // Preprocessor conditional rules for properties
    preproc_conditional_properties: $ => seq(
      $.preproc_if,
      repeat($._page_properties),
      optional(seq(
        $.preproc_else,
        repeat($._page_properties)
      )),
      $.preproc_endif
    ),

    // Preprocessor conditional rules for object-level properties
    preproc_conditional_object_properties: $ => seq(
      $.preproc_if,
      repeat($.property),
      optional(seq(
        $.preproc_else,
        repeat($.property)
      )),
      $.preproc_endif
    ),

    // Preprocessor conditional rules for table properties
    preproc_conditional_table_properties: $ => seq(
      $.preproc_if,
      repeat($._table_properties),
      optional(seq(
        $.preproc_else,
        repeat($._table_properties)
      )),
      $.preproc_endif
    ),

    // Preprocessor conditional rules for page properties
    preproc_conditional_page_properties: $ => seq(
      $.preproc_if,
      repeat($._page_properties),
      optional(seq(
        $.preproc_else,
        repeat($._page_properties)
      )),
      $.preproc_endif
    ),

    // Preprocessor conditional rules for report properties
    preproc_conditional_report_properties: $ => seq(
      $.preproc_if,
      repeat($._report_properties),
      optional(seq(
        $.preproc_else,
        repeat($._report_properties)
      )),
      $.preproc_endif
    ),

    // Preprocessor conditional rules for xmlport properties
    preproc_conditional_xmlport_properties: $ => seq(
      $.preproc_if,
      repeat($._xmlport_properties),
      optional(seq(
        $.preproc_else,
        repeat($._xmlport_properties)
      )),
      $.preproc_endif
    ),

    // Preprocessor conditional rules for query properties
    preproc_conditional_query_properties: $ => seq(
      $.preproc_if,
      repeat(choice($._universal_properties, $._query_properties, $.property_list)),
      optional(seq(
        $.preproc_else,
        repeat(choice($._universal_properties, $._query_properties, $.property_list))
      )),
      $.preproc_endif
    ),

    // Preprocessor conditional rules for enum properties
    preproc_conditional_enum_properties: $ => seq(
      $.preproc_if,
      repeat($._enum_properties),
      optional(seq(
        $.preproc_else,
        repeat($._enum_properties)
      )),
      $.preproc_endif
    ),

    // Preprocessor conditional rules for permissionset properties
    preproc_conditional_permissionset_properties: $ => seq(
      $.preproc_if,
      repeat(choice($._permissionset_properties, $.property_list)),
      optional(seq(
        $.preproc_else,
        repeat(choice($._permissionset_properties, $.property_list))
      )),
      $.preproc_endif
    ),

    // Preprocessor conditional rules for controladdin properties
    preproc_conditional_controladdin_properties: $ => seq(
      $.preproc_if,
      repeat(choice($._controladdin_properties, $.property_list)),
      optional(seq(
        $.preproc_else,
        repeat(choice($._controladdin_properties, $.property_list))
      )),
      $.preproc_endif
    ),

    // Preprocessor conditional rules for profile properties
    preproc_conditional_profile_properties: $ => seq(
      $.preproc_if,
      repeat(choice($._profile_properties, $.property_list)),
      optional(seq(
        $.preproc_else,
        repeat(choice($._profile_properties, $.property_list))
      )),
      $.preproc_endif
    ),

    // Preprocessor conditional rules for variable declarations
    preproc_conditional_variables: $ => seq(
      $.preproc_if,
      repeat(choice(
        $.variable_declaration,
        $.comment,
        $.multiline_comment,
        $.attribute_list,
        $.pragma
      )),
      optional(seq(
        $.preproc_else,
        repeat(choice(
          $.variable_declaration,
          $.comment,
          $.multiline_comment,
          $.attribute_list,
          $.pragma
        ))
      )),
      $.preproc_endif
    ),

    preproc_conditional_field_properties: $ => seq(
      $.preproc_if,
      repeat($._field_properties),
      optional(seq(
        $.preproc_else,
        repeat($._field_properties)
      )),
      $.preproc_endif
    ),

    preproc_if: $ => seq(
      choice('#if', '#IF', '#If'),
      field('condition', $.identifier)
    ),

    preproc_else: $ => choice('#else', '#ELSE', '#Else'),

    preproc_endif: $ => choice('#endif', '#ENDIF', '#Endif'),

    preproc_region: $ => seq(
      '#region',
      optional(field('name', /[^\n]*/))
    ),

    preproc_endregion: $ => '#endregion',

    pragma: $ => /#pragma[^\n]*/, // Match lines starting with #pragma specifically

    comment: $ => token(seq('//', /.*/)),

    multiline_comment: $ => token(seq(
      '/*',
      /[^*]*\*+([^/*][^*]*\*+)*/,
      '/'
    )),

    // AL keywords that can be used as enum values
    // Comprehensive list covering object types, data types, control flow, and other common keywords
    _enum_keyword: $ => choice(
      // Object types
      'DATABASE', 'database', 'Database',
      'Table', 'table', 'TABLE',
      'Page', 'page', 'PAGE', 
      'Report', 'report', 'REPORT',
      'Codeunit', 'codeunit', 'CODEUNIT',
      'Query', 'query', 'QUERY',
      'XMLport', 'xmlport', 'XMLPORT',
      'Enum', 'enum', 'ENUM',
      'Interface', 'interface', 'INTERFACE',
      'ControlAddin', 'controladdin', 'CONTROLADDIN',
      
      // Data types
      'Code', 'code', 'CODE',
      'Integer', 'integer', 'INTEGER',
      'Decimal', 'decimal', 'DECIMAL',
      'Boolean', 'boolean', 'BOOLEAN',
      'Date', 'date', 'DATE',
      'Time', 'time', 'TIME',
      'DateTime', 'datetime', 'DATETIME',
      'Guid', 'guid', 'GUID',
      'Blob', 'blob', 'BLOB',
      'BigInteger', 'biginteger', 'BIGINTEGER',
      'Option', 'option', 'OPTION',
      'Record', 'record', 'RECORD',
      
      // Control flow keywords
      'If', 'if', 'IF',
      'Then', 'then', 'THEN',
      'Else', 'else', 'ELSE',
      'While', 'while', 'WHILE',
      'For', 'for', 'FOR',
      'Repeat', 'repeat', 'REPEAT',
      'Until', 'until', 'UNTIL',
      'Case', 'case', 'CASE',
      'Of', 'of', 'OF',
      'Exit', 'exit', 'EXIT',
      'Break', 'break', 'BREAK',
      
      // Visibility and scope
      'Local', 'local', 'LOCAL',
      'Global', 'global', 'GLOBAL',
      'Protected', 'protected', 'PROTECTED',
      'Internal', 'internal', 'INTERNAL',
      'Public', 'public', 'PUBLIC',
      
      // Boolean values
      'True', 'true', 'TRUE',
      'False', 'false', 'FALSE',
      
      // Operators
      'And', 'and', 'AND',
      'Or', 'or', 'OR',
      'Not', 'not', 'NOT',
      'Div', 'div', 'DIV',
      'Mod', 'mod', 'MOD',
      
      // Other common keywords
      'Var', 'var', 'VAR',
      'Procedure', 'procedure', 'PROCEDURE',
      'Function', 'function', 'FUNCTION',
      'Trigger', 'trigger', 'TRIGGER',
      'Begin', 'begin', 'BEGIN',
      'End', 'end', 'END',
      'With', 'with', 'WITH',
      'Do', 'do', 'DO'
    ),

    // Page customization elements
    _pagecustomization_element: $ => choice(
      $.views_section
    ),

    views_section: $ => seq(
      /[vV][iI][eE][wW][sS]/,
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

    addfirst_views: $ => seq(
      /[aA][dD][dD][fF][iI][rR][sS][tT]/,
      '{',
      repeat($.view_definition),
      '}'
    ),

    addlast_views: $ => seq(
      /[aA][dD][dD][lL][aA][sS][tT]/,
      '{',
      repeat($.view_definition),
      '}'
    ),

    addafter_views: $ => seq(
      /[aA][dD][dD][aA][fF][tT][eE][rR]/,
      '(',
      field('target', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat($.view_definition),
      '}'
    ),

    addbefore_views: $ => seq(
      /[aA][dD][dD][bB][eE][fF][oO][rR][eE]/,
      '(',
      field('target', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat($.view_definition),
      '}'
    ),

    view_definition: $ => seq(
      'view',
      '(',
      field('name', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat($._view_property),
      '}'
    ),

    _view_property: $ => choice(
      $.view_caption_property,
      $.view_filters_property
    ),

    view_caption_property: $ => seq(
      field('name', alias(/[cC][aA][pP][tT][iI][oO][nN]/, 'Caption')),
      '=',
      field('value', $.string_literal),
      ';'
    ),

    view_filters_property: $ => seq(
      'Filters',
      '=',
      field('value', $.filter_expression),
      ';'
    ),

    // Profile elements
    _profile_element: $ => choice(
      $._profile_properties,         // Centralized properties
      $.property_list,               // Generic fallback
      $.preproc_conditional_profile_properties
    ),

    // CONSOLIDATED: profile_description_property → description_property

    profile_rolecenter_property: $ => seq(
      'RoleCenter',
      '=',
      field('value', $._identifier_choice),
      ';'
    ),

    // CONSOLIDATED: profile_caption_property -> caption_property

    profile_customizations_property: $ => seq(
      'Customizations',
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
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // CONSOLIDATED: profile_promoted_property → promoted_property

    // =============================================================================
    // CENTRALIZED PROPERTY CATEGORIES
    // =============================================================================
    // Semantic property organization for DRY principle and easier maintenance

    // Universal properties - apply to most AL object types
    _universal_properties: $ => choice(
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
      $.blank_numbers_property,      // Blank number display rules
      $.unique_property,             // Uniqueness constraint
      $.values_allowed_property,     // Enumerated valid values
      $.validate_table_relation_property, // FK validation
      $.char_allowed_property,       // Character input restrictions
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
    ),

    // Navigation/interaction properties
    _navigation_properties: $ => choice(
      $.lookup_pageid_property,      // Lookup page reference
      $.drilldown_pageid_property,   // Drill-down page reference
      $.navigation_page_id_property, // Navigation target
      $.run_object_property,         // Action target object
      $.run_page_link_property,      // Page link parameters
      $.run_page_view_property,      // Page view/filter to apply
      $.shortcut_key_property,       // Keyboard shortcut
      $.card_page_id_property,       // Associated card page
    ),

    // Access control properties
    _access_properties: $ => choice(
      $.access_property,             // Access level
      $.permissions_property,        // Permission definitions
      $.inherent_permissions_property, // Built-in permissions
      $.inherent_entitlements_property, // Built-in entitlements
      $.test_permissions_property,   // Test environment permissions
      $.access_by_permission_property, // General access by permission (used in actions)
      // Note: Pages use access_by_permission_page_property; other objects use access_by_permission_property
    ),

    // Object-specific properties that are unique to specific object types
    // These only make sense in particular contexts and cannot be universally applied
    _object_specific_properties: $ => choice(
      // Page-specific
      $.page_type_property,          // Page type (List, Card, etc.)
      $.source_table_property,       // Source table reference
      
      // Codeunit-specific
      $.table_no_property,           // Associated table
      $.single_instance_property,    // Singleton pattern
      $.event_subscriber_instance_property, // Event handling
      
      // Table-specific
      $.table_type_property,         // Table type (Normal, Temporary, etc.)
      $.data_per_company_property,   // Multi-tenancy support
      $.replicate_data_property,     // Replication settings
      
      // Report-specific
      $.processing_only_property,    // Processing-only report
      $.use_request_page_property,   // Request page usage
    ),

    // Query-specific properties that are unique to query objects
    _query_properties: $ => choice(
      $.query_type_property,         // Query type (Normal, API, Filter)
      $.about_title_property,        // Teaching tip title
      $.about_text_property,         // Teaching tip text  
      $.context_sensitive_help_page_property, // Help page reference
      $.data_access_intent_property, // Database replica access
      $.query_category_property,     // Query categorization
      // API-specific properties
      $.entity_caption_property,     // API entity caption
      $.entity_caption_ml_property,  // API entity caption (multi-language)
      $.entity_name_property,        // API entity name
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
    ),

    // ControlAddIn-specific properties that are unique to controladdin objects
    _controladdin_properties: $ => choice(
      $._universal_properties,       // caption, description, obsolete_*, application_area
      // ControlAddIn-specific
      $.controladdin_property,
    ),

    // Profile-specific properties that are unique to profile objects
    _profile_properties: $ => choice(
      // Profile-specific (higher precedence to override universal ones)
      $.description_property,
      $.profile_rolecenter_property,
      $.profile_customizations_property,
      $.profile_description_property2,
      $.caption_property,
      $.promoted_property,
      // Universal properties (lower precedence)
      $._universal_properties,       // obsolete_*, application_area, tool_tip_*
      $._display_properties,         // visible, style_*, width, importance, etc.
    ),

    // Enum-specific properties that are unique to enum objects
    _enum_properties: $ => choice(
      $._universal_properties,       // caption, description, obsolete_*, application_area
      $._access_properties,         // access, permissions, inherent_*
      // Enum-specific
      $.extensible_property,
      $.assignment_compatibility_property,
      $.implementation_property,    // Interface implementations
    ),

    // Composed property groups for different object contexts
    _field_properties: $ => choice(
      $._universal_properties,
      $._display_properties,
      $._validation_properties,
      $._data_properties,
      $._navigation_properties,
      $.field_trigger_declaration,   // Field-specific triggers
      // Field-specific additional properties
      $.assist_edit_property,
      $.quick_entry_property,
      $.option_caption_property,
      $.sign_displacement_property,
      $.title_property,
      $.extended_datatype_property,
      $.about_title_property,
      $.about_text_property,
      $.instructional_text_property,
      $.page_about_title_ml_property,
      $.page_about_text_ml_property,
      $.odata_edm_type_property,
      $.drill_down_property,
      $.preproc_conditional_field_properties,
      $.access_by_permission_property,
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
      
      // Page-specific data management properties
      $.data_caption_expression_property,
      $.data_access_intent_property,
      $.data_caption_fields_property,
      $.extensible_property,
      
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
      $.instructional_text_property,
      $.instructional_text_ml_property,
      $.image_property,
      $.about_text_property,
      $.page_about_text_ml_property,
      $.about_title_property,
      $.page_about_title_ml_property,
      
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
      
      // Help and documentation properties
      $.context_sensitive_help_page_property,
      $.help_link_property,
      $.is_preview_property,
      $.additional_search_terms_property,
      $.additional_search_terms_ml_property,
      
      // Page action properties
      $.scope_property,
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
      
      // Table-specific data management properties
      $.data_caption_fields_property,
      $.extensible_property,
      $.column_store_index_property,
      $.compression_type_property,
      // Note: data_per_company_property and replicate_data_property are in _object_specific_properties
      
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
      
      // Additional codeunit-specific properties not in other groups
      $.test_isolation_property
    ),

    // Composed property group for report-level properties
    // This replaces the scattered report property list in _report_element
    _report_properties: $ => choice(
      $._universal_properties,
      $._access_properties,
      $._object_specific_properties,
      
      // Report-specific properties
      $.scope_property,
      $.additional_search_terms_property,
      $.additional_search_terms_ml_property,
      
      // Report layout properties (critical)
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
      $.data_item_table_view_property,
      $.data_item_link_property,
      $.request_filter_fields_property,
      $.request_filter_heading_property,
    ),

    // =============================================================================
    // CENTRALIZED TRIGGER ARCHITECTURE
    // =============================================================================
    // Semantic trigger organization for DRY principle and easier maintenance

    // XMLPort property group - leverages centralized categories
    _xmlport_properties: $ => choice(
      $._universal_properties,    // caption, application_area, tool_tip, obsolete_*, description
      $._access_properties,       // inherent_permissions, inherent_entitlements, access
      
      // XMLPort-specific properties only
      $.direction_property,
      $.format_property,
      $.paste_is_valid_property,
      $.moved_from_property,
      $.moved_to_property,
      $.linked_in_transaction_property,
      $.linked_object_property,
      $.external_schema_property,
    ),

    // Action property group - leverages centralized categories  
    _action_properties: $ => choice(
      $._universal_properties,    // caption, application_area, obsolete_*, tool_tip
      $._display_properties,      // enabled, visible
      $._navigation_properties,   // run_object, run_page_link, shortcut_key
      $._access_properties,       // access_by_permission
      
      // Action-specific properties only
      $.about_title_property,
      $.about_text_property,
      $.page_about_title_ml_property,
      $.page_about_text_ml_property,
      $.allowed_file_extensions_property,
      $.allow_multiple_files_property,
      $.custom_action_type_property,
      $.ellipsis_property,
      $.file_upload_action_property,
      $.file_upload_row_action_property,
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
      $.scope_property,
    ),

    // Centralized trigger components for DRY principle
    _trigger_keyword: $ => choice('trigger', 'TRIGGER', 'Trigger'),

    // Trigger parameter patterns (simplified from '()' duplication)
    _trigger_parameters: $ => '()',

    // Centralized identifier choice pattern (appears 35+ times)
    _identifier_choice: $ => choice($._quoted_identifier, $.identifier),

    // Centralized property template for DRY principle
    _boolean_property_template: $ => seq(
      '=',
      field('value', $.boolean),
      ';'
    ),

    _string_property_template: $ => seq(
      '=',
      field('value', $.string_literal),
      ';'
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
    _field_keyword: $ => choice('FIELD', 'Field', 'field'),
    _filter_keyword: $ => choice('FILTER', 'filter', 'Filter'),
    _cardpart_keyword: $ => choice('CardPart', 'CARDPART', 'Cardpart'),
    _tabledata_keyword: $ => choice('tabledata', 'TableData', 'Tabledata', 'TABLEDATA'),
    _table_permission_keyword: $ => choice('table', 'Table', 'TABLE'),

    // Missing alias target rules
    const: $ => choice('const', 'CONST', 'Const'),
    name: $ => choice($.identifier, $._quoted_identifier),
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
