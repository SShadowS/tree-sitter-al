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
    source_file: $ => repeat($._object),

    _object: $ => choice(
      $.table_declaration,
      $.tableextension_declaration,
      $.codeunit_declaration,
      $.pageextension_declaration,
      $.page_declaration,
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
    
    xmlport_declaration: $ => seq(
      /[xX][mM][lL][pP][oO][rR][tT]/,
      field('object_id', $.integer),
      field('object_name', choice($._quoted_identifier, $.identifier)),
      '{',
      repeat($._xmlport_element),
      '}'
    ),
    
    _xmlport_element: $ => choice(
      $.xmlport_schema_element,
      $.var_section,
      $.procedure,
      $.trigger_declaration,
      
      // All XMLPort properties directly
      $.caption_property,
      $.inherent_permissions_property,
      $.inherent_entitlements_property,
      $.caption_ml_property,
      $.description_property,
      $.external_schema_property,
      $.paste_is_valid_property,
      $.obsolete_reason_property,
      $.obsolete_state_property,
      $.obsolete_tag_property,
      $.moved_from_property,
      $.moved_to_property,
      $.linked_in_transaction_property,
      $.linked_object_property,
      $.application_area_property,
      $.access_property,
      $.direction_property,
      $.format_property
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
        /[fF][iI][xX][eE][dD]/
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
        field('source_table', choice($.identifier, $._quoted_identifier))
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
      $.caption_property,
      $.application_area_property,
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
      $.tool_tip_property,
      $.tool_tip_ml_property
    ),
    
    // 11. Unbound Property
    unbound_property: $ => seq(
      'Unbound',
      '=',
      field('value', $.boolean),
      ';'
    ),
    
    // 12. XmlName Property
    xml_name_property: $ => seq(
      'XmlName',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    
    // 13. MovedFrom Property
    moved_from_property: $ => seq(
      'MovedFrom',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    
    // 14. MovedTo Property
    moved_to_property: $ => seq(
      'MovedTo',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    
    // 15. LinkedInTransaction Property
    linked_in_transaction_property: $ => seq(
      'LinkedInTransaction',
      '=',
      field('value', $.boolean),
      ';'
    ),
    
    // 16. LinkedObject Property
    linked_object_property: $ => seq(
      'LinkedObject',
      '=',
      field('value', $.string_literal),
      ';'
    ),
    
    // 17. RequestFilterFields Property
    request_filter_fields_value: $ => seq(
      choice($.identifier, $._quoted_identifier),
      repeat(seq(',', choice($.identifier, $._quoted_identifier)))
    ),
    
    request_filter_fields_property: $ => seq(
      'RequestFilterFields',
      '=',
      $.request_filter_fields_value,
      ';'
    ),
    
    // 18. RequestFilterHeading Property
    request_filter_heading_property: $ => seq(
      'RequestFilterHeading',
      '=',
      $.string_literal,
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
    link_table_force_insert_property: $ => seq(
      'LinkTableForceInsert',
      '=',
      field('value', $.boolean),
      ';'
    ),
    
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
          choice('FIELD', 'Field', 'field'),
          '(',
          choice($.identifier, $._quoted_identifier, $.string_literal),
          ')'
        )
      )
    ),

    enum_declaration: $ => seq(
      /[eE][nN][uU][mM]/,
      field('object_id', $.integer),
      field('object_name', choice($._quoted_identifier, $.identifier)),
      optional(seq(
        /[iI][mM][pP][lL][eE][mM][eE][nN][tT][sS]/,
        field('interface', choice($._quoted_identifier, $.identifier))
      )),
      '{',
      repeat(choice($.property, $.enum_value_declaration)),
      '}'
    ),

    enumextension_declaration: $ => seq(
      /[eE][nN][uU][mM][eE][xX][tT][eE][nN][sS][iI][oO][nN]/,
      field('object_id', $.integer),
      field('object_name', choice($._quoted_identifier, $.identifier)),
      /[eE][xX][tT][eE][nN][dD][sS]/,
      field('base_object', choice($._quoted_identifier, $.identifier)),
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
      repeat($.property), // Reuse existing property rule, might need refinement
      '}'
    ),

    query_declaration: $ => seq(
      /[qQ][uU][eE][rR][yY]/,
      field('object_id', $.integer),
      field('object_name', choice($._quoted_identifier, $.identifier)),
      '{',
      repeat($._query_element),
      '}'
    ),

    _query_element: $ => choice(
      $.query_type_property,
      $.caption_property,
      $.about_title_property,
      $.about_text_property,
      $.context_sensitive_help_page_property,
      $.usage_category_property,
      $.data_access_intent_property,
      $.elements_section,
      $.property_list
    ),

    about_title_property: $ => seq(
      'AboutTitle',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    about_text_property: $ => seq(
      'AboutText',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // Page-specific version of AboutText
    page_about_text_property: $ => seq(
      'AboutText',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // Page-specific version of AboutTextML
    page_about_text_ml_property: $ => seq(
      'AboutTextML',
      '=',
      field('value', $.ml_value_list),
      ';'
    ),

    // Page-specific version of AboutTitle
    page_about_title_property: $ => seq(
      'AboutTitle',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    // Page-specific version of AboutTitleML
    page_about_title_ml_property: $ => seq(
      'AboutTitleML',
      '=',
      field('value', $.ml_value_list),
      ';'
    ),

    // Delete Allowed Property
    delete_allowed_property: $ => seq(
      'DeleteAllowed',
      '=',
      field('value', $.boolean),
      ';'
    ),

    // Insert Allowed Property
    insert_allowed_property: $ => seq(
      'InsertAllowed',
      '=',
      field('value', $.boolean),
      ';'
    ),

    // Modify Allowed Property
    modify_allowed_property: $ => seq(
      'ModifyAllowed',
      '=',
      field('value', $.boolean),
      ';'
    ),

    // Source Table Temporary Property
    source_table_temporary_property: $ => seq(
      'SourceTableTemporary',
      '=',
      field('value', $.boolean),
      ';'
    ),

    // Phase 2A - Medium Priority Boolean Page Properties
    analysis_mode_enabled_property: $ => seq(
      'AnalysisModeEnabled',
      '=',
      field('value', $.boolean),
      ';'
    ),

    auto_split_key_property: $ => seq(
      'AutoSplitKey',
      '=',
      field('value', $.boolean),
      ';'
    ),

    change_tracking_allowed_property: $ => seq(
      'ChangeTrackingAllowed',
      '=',
      field('value', $.boolean),
      ';'
    ),

    delayed_insert_property: $ => seq(
      'DelayedInsert',
      '=',
      field('value', $.boolean),
      ';'
    ),

    links_allowed_property: $ => seq(
      'LinksAllowed',
      '=',
      field('value', $.boolean),
      ';'
    ),

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
      'DataCaptionExpression',
      '=',
      field('value', choice(
        $.string_literal,
        $.identifier,
        $._quoted_identifier,
        $.call_expression
      )),
      ';'
    ),

    instructional_text_property: $ => seq(
      'InstructionalText',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    instructional_text_ml_property: $ => seq(
      'InstructionalTextML',
      '=',
      field('value', $.ml_value_list),
      ';'
    ),

    // Phase 4A - High + Medium Priority Page Properties
    access_by_permission_page_property: $ => seq(
      'AccessByPermission',
      '=',
      field('value', $.access_by_permission_value),
      ';'
    ),

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
      'EntityCaption',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    entity_caption_ml_property: $ => seq(
      'EntityCaptionML',
      '=',
      field('value', $.ml_value_list),
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
      field('value', $.ml_value_list),
      ';'
    ),

    entity_set_name_property: $ => seq(
      'EntitySetName',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    context_sensitive_help_page_property: $ => seq(
      'ContextSensitiveHelpPage',
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
    
    odata_key_fields_value: $ => seq(
      choice($.identifier, $._quoted_identifier),
      repeat(seq(',', choice($.identifier, $._quoted_identifier)))
    ),

    odata_key_fields_property: $ => seq(
      'ODataKeyFields',
      '=',
      field('value', $.odata_key_fields_value),
      ';'
    ),

    query_category_property: $ => seq(
      'QueryCategory',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    data_access_intent_property: $ => seq(
      'DataAccessIntent',
      '=',
      field('value', choice(
        /[rR][eE][aA][dD][oO][nN][lL][yY]/,
        /[rR][eE][aA][dD][wW][rR][iI][tT][eE]/
      )),
      ';'
    ),

    query_type_property: $ => seq(
      'QueryType',
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
      choice('FILTER', 'filter', 'Filter'),
      '(',
      field('value', choice(
        $.filter_or_expression,
        $.filter_not_equal_expression,
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
      field('field', $.field_reference),
      field('operator', $.filter_operator),
      field('value', $.filter_value)
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
      field('linked_field', choice($.identifier, $._quoted_identifier)),
      '.',
      field('linked_field_name', choice($.identifier, $._quoted_identifier)),
      repeat(seq(
        ',',
        field('field', choice($.identifier, $._quoted_identifier)),
        '=',
        field('linked_field', choice($.identifier, $._quoted_identifier)),
        '.',
        field('linked_field_name', choice($.identifier, $._quoted_identifier))
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
      field('object_id', $.integer),
      field('object_name', choice($._quoted_identifier, $.identifier)),
      /[eE][xX][tT][eE][nN][dD][sS]/,
      field('base_object', choice($._quoted_identifier, $.identifier)),
      '{',
      repeat($._pageextension_element),
      '}'
    ),

    _pageextension_element: $ => choice(
      $.layout_section,
      $.actions_section,
      $.property_list,
      $.var_section,
      $.trigger_declaration,
      $.procedure
    ),

    tableextension_declaration: $ => seq(
      /[tT][aA][bB][lL][eE][eE][xX][tT][eE][nN][sS][iI][oO][nN]/,
      field('object_id', $.integer),
      field('object_name', choice($._quoted_identifier, $.identifier)),
      /[eE][xX][tT][eE][nN][dD][sS]/,
      field('base_object', choice($._quoted_identifier, $.identifier)),
      '{',
      repeat($._tableextension_element),
      '}'
    ),

    _tableextension_element: $ => choice(
      $.fields,
      $.keys,
      $.fieldgroups_section,
      $.procedure,
      $.var_section,
      $.trigger_declaration,
      $.property_list
    ),

    actions_section: $ => seq(
      /[aA][cC][tT][iI][oO][nN][sS]/,
      '{',
      repeat(choice(
        $._action_element,
        $._action_group,
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
        /[sS][yY][sS][tT][eE][mM][aA][cC][tT][iI][oO][nN][sS]/
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
        $.separator_action
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
      repeat($._action_property),
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
        $.var_section
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
        $.var_section
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
        $.var_section
      )),
      '}'
    ),

    _action_property: $ => choice(
      $.access_by_permission_property,
      $.allowed_file_extensions_property,
      $.allow_multiple_files_property,
      $.application_area_property,
      $.caption_property,
      $.custom_action_type_property,
      $.ellipsis_property,
      $.enabled_property,
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
      $.run_object_property,
      $.run_page_link_property,
      $.run_page_mode_property,
      $.run_page_on_rec_property,
      $.run_page_view_property,
      $.scope_property,
      $.shortcut_key_property,
      $.tool_tip_property,
      $.visible_property
    ),

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
      field('value', choice(
        /[aA][dD][mM][iI][nN][iI][sS][tT][rR][aA][tT][iI][oO][nN]/,
                /[dD][oO][cC][uU][mM][eE][nN][tT][sS]/,
        /[lL][iI][sS][tT][sS]/,
        /[rR][eE][pP][oO][rR][tT][sS]/,
        /[tT][aA][sS][kK][sS]/,
        $.identifier,
        $._quoted_identifier
      )),
      ';'
    ),

    source_table_property: $ => seq(
      'SourceTable',
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
      choice('CardPart', 'CARDPART', 'Cardpart'),
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
      field('value', choice(
        $.string_literal,
        $.identifier, // Simple identifier like 'Ascending'
        seq( // sorting(...) pattern
          $.identifier, // e.g., 'sorting'
          '(',
          // Comma-separated list of one or more quoted identifiers
          seq(
            $._quoted_identifier,
            repeat(seq(',', $._quoted_identifier))
          ),
          ')'
        ),
        $.where_clause // Support WHERE clause syntax
      )),
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
        )
      ))
    ),

    enabled_property: $ => seq(
      'Enabled',
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
      'Promoted',
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
      'TableNo',
      '=',
      field('value', alias($._table_no_value, $.value)),
      ';'
    ),

    subtype_property: $ => seq(
      'Subtype',
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
      'EventSubscriberInstance',
      '=',
      field('value', alias($.event_subscriber_instance_value, $.value)),
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
      field('object_id', $.integer),
      field('object_name', choice($._quoted_identifier, $.identifier)),
      '{',
      repeat($._table_element),
      '}'
    ),

    codeunit_declaration: $ => seq(
      /[cC][oO][dD][eE][uU][nN][iI][tT]/,
      field('object_id', $.integer),
      field('object_name', choice($._quoted_identifier, $.identifier)),
      optional($.implements_clause),
      '{',
      prec(4, optional($.property_list)), // Prioritize properties over procedures starting with same keywords
      repeat(choice(
        $.var_section,
        seq(optional($.attribute_list), $.procedure),
        seq(optional($.attribute_list), $.onrun_trigger),
        seq(optional($.attribute_list), $.generic_trigger) 
      )),
      '}'
    ),

    implements_clause: $ => seq(
      /[iI][mM][pP][lL][eE][mM][eE][nN][tT][sS]/,
      field('interface', choice($._quoted_identifier, $.identifier))
    ),

    // Generic trigger rule for codeunits etc.
    generic_trigger: $ => seq(
      choice('trigger', 'TRIGGER', 'Trigger'),
      field('name', alias($.identifier, $.trigger_name)), // Use identifier for the trigger name
      '(',
      optional($.parameter_list), // Allow optional parameters
      ')',
      optional($.var_section),
      $.code_block
    ),

    page_declaration: $ => seq(
      /[pP][aA][gG][eE]/,
      field('object_id', $.integer),
      field('object_name', choice($._quoted_identifier, $.identifier)),
      '{',
      repeat($._page_element),
      '}'
    ),

    controladdin_declaration: $ => seq(
      /[cC][oO][nN][tT][rR][oO][lL][aA][dD][dD][iI][nN]/,
      field('object_name', choice($._quoted_identifier, $.identifier)),
      '{',
      repeat($._controladdin_element),
      '}'
    ),

    _controladdin_element: $ => choice(
      $.controladdin_property,
      $.controladdin_event,
      $.controladdin_procedure
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
      ';'
    ),

    controladdin_event: $ => seq(
      optional($.attribute_list),
      'event',
      field('name', $.identifier),
      '(',
      optional($.parameter_list),
      ')',
      ';'
    ),

    controladdin_procedure: $ => seq(
      'procedure',
      field('name', $.identifier),
      '(',
      optional($.parameter_list),
      ')',
      ';'
    ),

    interface_declaration: $ => seq(
      /[iI][nN][tT][eE][rR][fF][aA][cC][eE]/,
      field('object_name', choice($._quoted_identifier, $.identifier)),
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
      ';'
    ),

    report_declaration: $ => seq(
      /[rR][eE][pP][oO][rR][tT]/,
      field('object_id', $.integer),
      field('object_name', choice($._quoted_identifier, $.identifier)),
      '{',
      repeat($._report_element),
      '}'
    ),

    _report_element: $ => choice(
      $.property_list,
      $.dataset_section,
      $.labels_section,
      $.requestpage_section,
      $.actions_section,
      $.var_section,
      seq(optional($.attribute_list), $.procedure),
      seq(optional($.attribute_list), $.generic_trigger)
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
      choice($._quoted_identifier, $.identifier),
      ')',
      '{',
      repeat(choice(
        $.report_column_section, 
        $.report_dataitem_section,
        $.property,
        seq(optional($.attribute_list), $.generic_trigger)
      )),
      '}'
    ),

    report_column_section: $ => seq(
      'column',
      '(',
      field('name', $.identifier),
      ';',
      field('source', $.identifier),
      ')',
      '{',
      repeat($.property),
      '}'
    ),

    requestpage_section: $ => seq(
      'requestpage',
      '{',
      repeat(choice(
        $.property,
        $.layout_section, 
        $.actions_section,
        $.generic_trigger
      )),
      '}'
    ),

    permissionset_declaration: $ => seq(
      /[pP][eE][rR][mM][iI][sS][sS][iI][oO][nN][sS][eE][tT]/,
      field('object_id', $.integer),
      field('object_name', choice($._quoted_identifier, $.identifier)),
      '{',
      repeat($._permissionset_element),
      '}'
    ),

    _permissionset_element: $ => choice(
      $.assignable_property,
      $.caption_property,
      $.permissionset_permissions
    ),

    assignable_property: $ => seq(
      'Assignable',
      '=',
      choice('true', 'false'),
      ';'
    ),

    permissionset_permissions: $ => seq(
      'Permissions',
      '=',
      $.permission_list,
      ';'
    ),

    permission_list: $ => seq(
      $.permission_entry,
      repeat(seq(',', $.permission_entry))
    ),

    permission_entry: $ => choice(
      $.tabledata_permission_entry,
      $.table_permission_entry,
      $.page_permission_entry,
      $.report_permission_entry,
      $.codeunit_permission_entry,
      $.system_permission_entry
    ),

    tabledata_permission_entry: $ => seq(
      choice('tabledata', 'TableData', 'Tabledata', 'TABLEDATA'),
      choice($._quoted_identifier, $.identifier, $.integer),
      '=',
      $.permission_type
    ),

    table_permission_entry: $ => seq(
      choice('table', 'Table', 'TABLE'),
      choice($._quoted_identifier, $.identifier, $.integer),
      '=',
      $.permission_type
    ),

    page_permission_entry: $ => seq(
      choice('page', 'Page', 'PAGE'),
      choice($._quoted_identifier, $.identifier),
      '=',
      $.permission_type
    ),

    report_permission_entry: $ => seq(
      choice('report', 'Report', 'REPORT'),
      choice($._quoted_identifier, $.identifier),
      '=',
      $.permission_type
    ),

    codeunit_permission_entry: $ => seq(
      choice('codeunit', 'Codeunit', 'CODEUNIT'),
      choice($._quoted_identifier, $.identifier),
      '=',
      $.permission_type
    ),

    system_permission_entry: $ => seq(
      choice('system', 'System', 'SYSTEM'),
      choice($._quoted_identifier, $.identifier),
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
      // Place source_table_view_property at the top for higher precedence
      $.source_table_view_property,
      $.layout_section,
      $.actions_section,
      seq(optional($.attribute_list), $.procedure),  // Support attributed procedures in pages
      $.var_section,
      $.trigger_declaration,
      
      // All page properties directly as elements
      $.page_type_property,
      $.source_table_property,
      $.editable_property,        // Add missing editable property
      $.enabled_property,         // Add missing enabled property
      $.visible_property,         // Add missing visible property
      $.data_caption_fields_property,
      $.extensible_property,
      $.inherent_permissions_property,
      $.inherent_entitlements_property,
      $.caption_ml_property,
      $.description_property,
      $.usage_category_property,
      $.application_area_property,
      $.caption_property,
      $.scope_property,
      $.promoted_property,
      $.promoted_category_property,
      $.promoted_only_property,
      $.promoted_is_big_property,
      $.promoted_action_categories_property,
      $.run_object_property,
      $.run_page_link_property,
      $.run_page_view_property,
      $.image_property,
      $.tool_tip_property,
      $.permissions_property,
      
      // Phase 1 additions - high priority page properties
      $.page_about_text_property,
      $.page_about_text_ml_property,
      $.page_about_title_property,
      $.page_about_title_ml_property,
      $.card_page_id_property,
      $.delete_allowed_property,
      $.insert_allowed_property,
      $.modify_allowed_property,
      $.source_table_temporary_property,
      
      // Phase 2A additions - medium priority boolean page properties
      $.analysis_mode_enabled_property,
      $.auto_split_key_property,
      $.change_tracking_allowed_property,
      $.delayed_insert_property,
      $.links_allowed_property,
      $.multiple_new_lines_property,
      $.populate_all_fields_property,
      
      // Phase 2B additions - medium priority complex page properties
      $.data_access_intent_property,
      $.data_caption_expression_property,
      $.instructional_text_property,
      $.instructional_text_ml_property,
      
      // Phase 4A additions - high + medium priority page properties
      $.access_by_permission_page_property,
      $.prompt_mode_property,
      $.refresh_on_activate_property,
      $.save_values_property,
      $.show_filter_property,
      $.additional_search_terms_property,
      $.additional_search_terms_ml_property,
      
      // Phase 4B Batch 2 - Web Service Properties
      $.entity_caption_property,
      $.entity_caption_ml_property,
      $.entity_name_property,
      $.entity_set_caption_property,
      $.entity_set_caption_ml_property,
      $.entity_set_name_property,
      
      // Phase 4C - Remaining Low Priority Properties
      $.context_sensitive_help_page_property,
      $.help_link_property,
      $.is_preview_property,
      $.odata_key_fields_property,
      $.query_category_property,
      
      // Page View Properties
      $.filters_property,
      
      // Obsolete Properties
      $.obsolete_reason_property,
      $.obsolete_state_property,
      $.obsolete_tag_property,
      $.order_by_property,
      $.shared_layout_property,
      $.data_item_table_view_property
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
      $.addbefore_layout_modification
    ),

    // Layout modification rules for pageextensions
    addfirst_layout_modification: $ => seq(
      /[aA][dD][dD][fF][iI][rR][sS][tT]/,
      '(',
      field('target', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat($._layout_element),
      '}'
    ),

    addlast_layout_modification: $ => seq(
      /[aA][dD][dD][lL][aA][sS][tT]/,
      '(',
      field('target', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat($._layout_element),
      '}'
    ),

    addafter_layout_modification: $ => seq(
      /[aA][dD][dD][aA][fF][tT][eE][rR]/,
      '(',
      field('target', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat($._layout_element),
      '}'
    ),

    addbefore_layout_modification: $ => seq(
      /[aA][dD][dD][bB][eE][fF][oO][rR][eE]/,
      '(',
      field('target', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat($._layout_element),
      '}'
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
        $._layout_element,
        $.property_list,
        $.instructional_text_property,
        $.visible_property,
        $.enabled_property,
        $.cuegroup_layout_property,
        $.freeze_column_property,
        $.grid_layout_property,
        $.indentation_column_property,
        $.indentation_controls_property,
        $.show_as_tree_property,
        $.tree_initial_state_property
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
        $.field_section,
        $.actions_section,
        $.property_list,
        $.caption_property,
        $.visible_property,
        $.enabled_property,
        $.cuegroup_layout_property
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
        $._layout_element,
        $.property_list,
        $.caption_property,
        $.show_caption_property,
        $.visible_property,
        $.enabled_property,
        $.grid_layout_property
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
        $._layout_element,
        $.property_list,
        $.visible_property,
        $.enabled_property
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
        $.property_list,
        $.application_area_property,
        $.caption_property,
        $.caption_ml_property,
        $.visible_property,
        $.enabled_property,
        $.show_caption_property,
        $.style_property,
        $.style_expr_property
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
        $._layout_element,
        $.property_list,
        $.visible_property,
        $.freeze_column_property
      )),
      '}'
    ),

    field_section: $ => choice(
      // Standard field
      seq(
        /[fF][iI][eE][lL][dD]/,
        '(',
        field('name', choice($.identifier, $._quoted_identifier)),
        ')',
        '{',
        repeat(choice(
      $.caption_property,
      $.caption_class_property,
      $.application_area_property,
      $.tool_tip_property,
      $.tool_tip_ml_property,
      $.visible_property,
      $.enabled_property,
      $.source_expr_property,
      $.editable_property,
      $.description_property,
      $.lookup_property,
      $.lookup_pageid_property,
      $.drilldown_pageid_property,
      $.option_caption_property,
      $.table_relation_property,
      $.decimal_places_property,
      $.field_trigger_declaration,
      // First 5 missing Page Field Properties
      $.assist_edit_property,
      $.column_span_property,
      $.drill_down_property,
      $.hide_value_property,
      $.multi_line_property,
      $.importance_property,
      $.navigation_page_id_property,
      $.quick_entry_property,
      $.row_span_property,
      $.show_caption_property,
      $.show_mandatory_property,
      $.style_property,
      $.style_expr_property,
      $.blank_zero_property,
      $.extended_datatype_property,
      $.auto_format_expression_property,
      $.auto_format_type_property,
      // Missing field properties
      $.access_by_permission_property,
      // Obsolete Properties for fields
      $.obsolete_reason_property,
      $.obsolete_state_property,
      $.obsolete_tag_property
        )),
        '}'
      ),
      // Field with control name
      seq(
        /[fF][iI][eE][lL][dD]/,
        '(',
        field('name', choice($.identifier, $._quoted_identifier)),
        ')',
        '(',
        field('control_name', choice($.identifier, $._quoted_identifier)),
        ')',
        '{',
        repeat(choice(
          $.caption_property,
          $.caption_class_property,
          $.application_area_property,
          $.tool_tip_property,
          $.tool_tip_ml_property,
          $.visible_property,
          $.enabled_property,
          $.source_expr_property,
          $.editable_property,
          $.description_property,
          $.lookup_property,
          $.lookup_pageid_property,
          $.option_caption_property,
          $.table_relation_property,
          $.decimal_places_property,
          $.sign_displacement_property,
          $.title_property,
          $.odata_edm_type_property,
          $.field_trigger_declaration,
          $.blank_zero_property,
          $.extended_datatype_property,
          $.auto_format_expression_property,
          $.auto_format_type_property,
          // Missing field properties
          $.access_by_permission_property,
          // Obsolete Properties for fields
          $.obsolete_reason_property,
          $.obsolete_state_property,
          $.obsolete_tag_property
        )),
        '}'
      ),
      // Combined field with ID and Source/Name: field(ControlId; SourceOrFieldName) { ... }
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
        // Combined list of possible properties from both original patterns
        repeat(choice(
          $.caption_property,
          $.caption_class_property,
          $.application_area_property,
          $.tool_tip_property,
          $.tool_tip_ml_property,
          $.visible_property,
          $.enabled_property,
          $.lookup_property,
          $.lookup_pageid_property,
          $.drilldown_pageid_property,
          $.run_object_property,
          $.run_page_link_property,
          $.source_expr_property,
          $.editable_property,
          $.option_caption_property,
          $.table_relation_property,
          $.decimal_places_property,
          $.field_trigger_declaration,
          // First 5 missing Page Field Properties
          $.assist_edit_property,
          $.column_span_property,
          $.drill_down_property,
          $.hide_value_property,
          $.multi_line_property,
          $.importance_property,
          $.navigation_page_id_property,
          $.quick_entry_property,
          $.row_span_property,
          $.show_caption_property,
          $.show_mandatory_property,
          $.sign_displacement_property,
          $.style_property,
          $.style_expr_property,
          $.title_property,
          $.odata_edm_type_property,
          $.blank_zero_property,
          $.extended_datatype_property,
          // Missing field properties
          $.access_by_permission_property,
          // Obsolete Properties for fields
          $.obsolete_reason_property,
          $.obsolete_state_property,
          $.obsolete_tag_property
        )),
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
        $.property_list,
        $.application_area_property,
        $.caption_property,
        $.multiplicity_property,
        $.provider_property,
        $.show_filter_property,
        $.sub_page_link_property,
        $.sub_page_view_property,
        $.update_propagation_property,
        $.visible_property
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
        $.property_list,
        $.application_area_property,
        $.visible_property
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
        $.application_area_property,
        $.visible_property,
        $.enabled_property,
        $.editable_property,
        $.trigger_declaration,
        $.var_section,
        $.code_block
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
        seq( // sorting(...) pattern
          $.identifier, // e.g., 'sorting'
          '(',
          // Comma-separated list of one or more quoted identifiers
          seq(
            $._quoted_identifier,
            repeat(seq(',', $._quoted_identifier))
          ),
          ')'
        ),
        $.where_clause // Support WHERE clause syntax
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
      field('type', alias(choice(
        /[oO][nN][aA][fF][tT][eE][rR][gG][eE][tT][rR][eE][cC][oO][rR][dD]/,
        /[oO][nN][iI][nN][iI][tT]/,
        /[oO][nN][oO][pP][eE][nN][pP][aA][gG][eE]/,
        /[oO][nN][cC][lL][oO][sS][eE][pP][aA][gG][eE]/,
        /[oO][nN][fF][iI][nN][dD][rR][eE][cC][oO][rR][dD]/,
        /[oO][nN][nN][eE][xX][tT][rR][eE][cC][oO][rR][dD]/,
        /[oO][nN][qQ][uU][eE][rR][yY][cC][lL][oO][sS][eE]/,
        /[oO][nN][aA][cC][tT][iI][oO][nN]/,
        // Additional page-level triggers
        /[oO][nN][aA][fF][tT][eE][rR][gG][eE][tT][cC][uU][rR][rR][rR][eE][cC][oO][rR][dD]/,
        /[oO][nN][nN][eE][wW][rR][eE][cC][oO][rR][dD]/,
        /[oO][nN][iI][nN][sS][eE][rR][tT][rR][eE][cC][oO][rR][dD]/,
        /[oO][nN][mM][oO][dD][iI][fF][yY][rR][eE][cC][oO][rR][dD]/,
        /[oO][nN][dD][eE][lL][eE][tT][eE][rR][eE][cC][oO][rR][dD]/,
        /[oO][nN][qQ][uU][eE][rR][yY][cC][lL][oO][sS][eE][pP][aA][gG][eE]/,
        // Support for custom trigger names (Control Add-in triggers, etc.)
        $.identifier
      ), $.trigger_type)),
      choice(
        seq('(', optional($.parameter_list), ')'),
        seq()
      ),
      optional(seq(':', $.type_specification)),
      choice(
        // Standard trigger with code block
        prec(2, seq(
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
      $.identifier
    ),

    subtype_value: $ => choice(
      /[iI][nN][sS][tT][aA][lL][lL]/,
      /[uU][pP][gG][rR][aA][dD][eE]/,
      /[tT][eE][sS][tT]/
    ),

    single_instance_value: $ => $.boolean,

    event_subscriber_instance_value: $ => choice(
      /[mM][aA][nN][uU][aA][lL]/,
      /[sS][tT][aA][tT][iI][cC]/
    ),

    implementation_value: $ => seq(
      field('interface', $._quoted_identifier),
      '=',
      field('implementation', $._quoted_identifier)
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
      /[sS][tT][aA][nN][dD][aA][rR][dD]/,
      /[sS][tT][aA][nN][dD][aA][rR][dD][aA][cC][cC][eE][nN][tT]/,
      /[sS][tT][rR][oO][nN][gG]/,
      /[sS][tT][rR][oO][nN][gG][aA][cC][cC][eE][nN][tT]/,
      /[aA][tT][tT][eE][nN][tT][iI][oO][nN]/,
      /[fF][aA][vV][oO][rR][aA][bB][lL][eE]/,
      /[uU][nN][fF][aA][vV][oO][rR][aA][bB][lL][eE]/
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

    promoted_only_property: $ => seq(
      'PromotedOnly',
      '=',
      field('value', $.boolean),
      ';'
    ),
    
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
      'Importance',
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

    show_caption_property: $ => seq(
      'ShowCaption',
      '=',
      field('value', $.boolean),
      ';'
    ),

    show_mandatory_property: $ => seq(
      'ShowMandatory',
      '=',
      field('value', $.boolean),
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
        $.call_expression
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
    description_value: $ => $.string_literal,
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
    tool_tip_value: $ => $.string_literal,
    unique_value: $ => $.boolean,
    validate_table_relation_value: $ => $.boolean,
    values_allowed_value: $ => seq(
      $.string_literal,
      repeat(seq(',', $.string_literal))
    ),

    // NEW HIGH PRIORITY PROPERTIES - Value Rules
    data_caption_fields_value: $ => seq(
      choice($._quoted_identifier, $.string_literal, $.identifier),
      repeat(seq(',', choice($._quoted_identifier, $.string_literal, $.identifier)))
    ),

    extensible_value: $ => $.boolean,

    data_per_company_value: $ => $.boolean,

    replicate_data_value: $ => $.boolean,

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

    auto_format_expression_value: $ => choice(
      $.string_literal,
      // Also allow unquoted format expressions like <precision, 2:2><standard format,0>
      $.identifier,
      $._quoted_identifier
    ),

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
      field('value', alias($.boolean, $.value)),
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
      /[dD][eE][sS][cC][rR][iI][pP][tT][iI][oO][nN]/,
      '=',
      field('value', $.description_value),
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
      'ToolTip',
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
      $.values_allowed_value,
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
      'DataCaptionFields',
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
      'CaptionML',
      '=',
      $.ml_value_list,
      ';'
    ),

    option_caption_ml_property: $ => seq(
      'OptionCaptionML',
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
      choice('trigger', 'TRIGGER', 'Trigger'),
      choice('OnRun', 'ONRUN', 'Onrun'),
      '()',
      optional($.var_section),
      $.code_block
    ),


    _table_element: $ => prec(1, choice(
      $.fields,  // Fields section should be primary
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
      $.keys,
      seq(optional($.attribute_list), $.procedure),
      $.caption_property,
      $.data_classification_property,
      $.var_section,
      $.permissions_property,
      $.drilldown_pageid_property,
      $.lookup_pageid_property,
      $.table_type_property,
      $.access_property,
      $.fieldgroups_section,
      
      // Existing table-related properties
      $.moved_from_property,
      $.moved_to_property,
      $.linked_in_transaction_property,
      $.linked_object_property,
      
      // HIGH PRIORITY properties
      $.data_caption_fields_property,
      $.extensible_property,
      $.data_per_company_property,
      $.replicate_data_property,
      $.column_store_index_property,
      $.compression_type_property,
      $.inherent_permissions_property,
      $.inherent_entitlements_property,
      
      // MEDIUM/LOW PRIORITY properties
      $.external_schema_property,
      $.paste_is_valid_property,
      $.description_property,
      $.obsolete_reason_property,
      $.obsolete_state_property,
      $.obsolete_tag_property,
      $.caption_ml_property,
      $.external_name_property
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
      prec(-1, /[rRiImMdDxX]+/)
    ),


    oninsert_trigger: $ => seq(
      choice('trigger', 'TRIGGER', 'Trigger'),
      choice('OnInsert', 'ONINSERT', 'Oninsert'),
      '()',
      optional($.var_section),
      $.code_block
    ),

    onmodify_trigger: $ => seq(
      choice('trigger', 'TRIGGER', 'Trigger'),
      choice('OnModify', 'ONMODIFY', 'Onmodify'),
      '()',
      optional($.var_section),
      $.code_block
    ),

    ondelete_trigger: $ => seq(
      choice('trigger', 'TRIGGER', 'Trigger'),
      choice('OnDelete', 'ONDELETE', 'Ondelete'),
      '()',
      optional($.var_section),
      $.code_block
    ),

    onrename_trigger: $ => seq(
      choice('trigger', 'TRIGGER', 'Trigger'),
      choice('OnRename', 'ONRENAME', 'Onrename'),
      '()',
      optional($.var_section),
      $.code_block
    ),

    onvalidate_trigger: $ => seq(
      choice('trigger', 'TRIGGER', 'Trigger'),
      choice('OnValidate', 'ONVALIDATE', 'Onvalidate'),
      '()',
      optional($.var_section),
      $.code_block
    ),

    onaftergetrecord_trigger: $ => seq(
      choice('trigger', 'TRIGGER', 'Trigger'),
      choice('OnAfterGetRecord', 'ONAFTERGETRECORD', 'Onaftergetrecord'),
      '()',
      optional($.var_section),
      $.code_block
    ),

    onafterinsertevent_trigger: $ => seq(
      choice('trigger', 'TRIGGER', 'Trigger'),
      choice('OnAfterInsertEvent', 'ONAFTERINSERTEVENT', 'Onafterinsertevent'),
      '()',
      optional($.var_section),
      $.code_block
    ),

    onaftermodifyevent_trigger: $ => seq(
      choice('trigger', 'TRIGGER', 'Trigger'),
      choice('OnAfterModifyEvent', 'ONAFTERMODIFYEVENT', 'Onaftermodifyevent'),
      '()',
      optional($.var_section),
      $.code_block
    ),

    onafterdeleteevent_trigger: $ => seq(
      choice('trigger', 'TRIGGER', 'Trigger'),
      choice('OnAfterDeleteEvent', 'ONAFTERDELETEEVENT', 'Onafterdeleteevent'),
      '()',
      optional($.var_section),
      $.code_block
    ),

    onbeforeinsertevent_trigger: $ => seq(
      'trigger',
      'OnBeforeInsertEvent',
      '()',
      optional($.var_section),
      $.code_block
    ),

    onbeforemodifyevent_trigger: $ => seq(
      'trigger',
      'OnBeforeModifyEvent',
      '()',
      optional($.var_section),
      $.code_block
    ),

    onbeforedeleteevent_trigger: $ => seq(
      'trigger',
      'OnBeforeDeleteEvent',
      '()',
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
      $.drilldown_pageid_property,
      $.lookup_pageid_property,
      $.card_page_id_property,
      $.promoted_action_categories_property,
      $.implementation_property,
      $.permissions_property,
      $.test_permissions_property,
      $.table_relation_property,
      $.field_class_property,
      $.calc_formula_property,
      $.blank_zero_property,
      $.editable_property,
      $.processing_only_property,
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
      $.extensible_property,
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
      $.drill_down_property,
      $.lookup_property,
      $.hide_value_property,
      $.multi_line_property,
      $.importance_property,
      $.navigation_page_id_property,
      $.quick_entry_property,
      $.row_span_property,
      $.show_caption_property,
      $.show_mandatory_property,
      $.style_property,
      $.style_expr_property,
      $.save_values_property,
      $.data_item_table_view_property,
      $.promoted_only_property,
      $.shortcut_key_property
    )),

    caption_property: $ => seq(
      /[cC][aA][pP][tT][iI][oO][nN]/,
      '=',
      $.string_literal,
      ';'
    ),

    caption_class_property: $ => seq(
      'CaptionClass',
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
      choice('tabledata', 'TableData', 'TABLEDATA'), 
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
        $.attribute_list,
        $.variable_declaration
      ))
    )),

    // Helper rule for comma-separated variable names
    _variable_name_list: $ => seq(
      field('name', choice($.identifier, $._quoted_identifier)),
      repeat(seq(',', field('name', choice($.identifier, $._quoted_identifier))))
    ),

    variable_declaration: $ => choice(
      // Special case for Label with string literal and optional attributes
      // Note: Labels typically don't support multiple declarations on one line in standard AL,
      // but we keep the structure consistent for now. If issues arise, this might need adjustment.
      prec(2, seq(
        field('names', $._variable_name_list), // Use list rule
        ':',
        field('type', choice('Label', 'LABEL', 'label')),
        field('value', $.string_literal),
        optional(seq(
          ',',  // Comma separator
          field('attributes', seq(
            $.label_attribute,
            repeat(seq(',', $.label_attribute))
          ))
        )),
        ';'
      )),
      // Variable with value assignment (Multiple assignment on one line is not standard AL)
      // This part might need review if complex initializations are common.
      seq(
        field('names', $._variable_name_list), // Use list rule
        ':',
        optional(field('type', $.type_specification)),
        ':=',
        field('value', $._expression), // Assigns the same value to all variables in the list
        ';'
      ),
      // Regular variable declaration (supporting multiple names) with optional attributes
      prec(1, seq(
        field('names', $._variable_name_list), // Use list rule
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
option_type: $ => prec.left(10, seq( // Increased precedence, left associative
  choice('Option', 'OPTION', 'Option'),
  optional($.option_member_list) // Members are part of the type
)),

// Helper for comma-separated list of option members  
option_member_list: $ => prec.left(1, choice(
  // Standard case: member followed by optional members
  seq(
    $.option_member,
    repeat(seq(',', optional($.option_member)))
  ),
  // Edge case: starts with empty but has content
  repeat1(seq(',', optional($.option_member)))
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
      prec(1, choice('RecordId', 'RECORDID', 'Recordid')),
      prec(1, choice('Variant', 'VARIANT', 'Variant')),
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
      prec(1, choice('Label', 'LABEL', 'Label')),
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

    text_type: $ => seq(
      prec(1, choice('Text', 'TEXT', 'text')),
      optional(seq(
        '[',
        field('length', $.integer),
        ']'
      ))
    ),

    code_type: $ => seq(
      prec(1, choice('Code', 'CODE', 'code')),
      optional(seq(
        '[',
        field('length', $.integer),
        ']'
      ))
    ),

    record_type: $ => prec.right(seq(
      prec(1, choice('Record', 'RECORD', 'record')),
      field('reference', $._table_reference),
      optional(choice('Temporary', 'TEMPORARY', 'temporary'))
    )),
    recordref_type: $ => /[rR][eE][cC][oO][rR][dD][rR][eE][fF]/,
    fieldref_type: $ => /[fF][iI][eE][lL][dD][rR][eE][fF]/,

    // Use existing _table_reference rule that already handles both plain and quoted identifiers 
    _table_reference: $ => choice(
      $.integer,
      $.identifier,
      $._quoted_identifier  // Already has precedence 2
    ),

    codeunit_type: $ => seq(
      prec(1, choice('Codeunit', 'codeunit')),
      field('reference', choice(
        $.integer,
        $._quoted_identifier,
        $.identifier,
        $.member_expression
      ))
    ),

    query_type: $ => seq(
      prec(1, 'Query'),
      field('reference', $.query_type_value)
    ),

    testpage_type: $ => seq(
      prec(1, 'TestPage'),
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
      field('reference', choice($.identifier, $.string_literal, $._quoted_identifier))
    ),

    array_type: $ => seq(
      prec(1, 'array'),
      '[',
      field('size', $.integer),
      ']',
      'of',
      $.type_specification
    ),

    fields: $ => seq(
      choice('fields', 'FIELDS', 'Fields'),
      '{',
      repeat($.field_declaration),
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
          $.test_table_relation_property,
          $.tool_tip_property,
          $.unique_property,
          $.validate_table_relation_property,
          $.values_allowed_property,
          $.extended_datatype_property,
          $.caption_ml_property,
          $.option_caption_ml_property,
          $.tool_tip_ml_property
        )),
        '}'
      ))
    ),


    table_relation_property: $ => seq(
      'TableRelation',
      '=',
      field('relation', $.table_relation_expression),
      ';'
    ),

    table_relation_expression: $ => choice(
      $._simple_table_relation,
      $.if_table_relation
    ),

    // Unified where clause implementation
    where_clause: $ => seq(
      /[wW][hH][eE][rR][eE]/,
      '(',
      field('conditions', $.where_conditions),
      ')'
    ),

    if_table_relation: $ => prec.right(seq(
      choice('IF', 'if', 'If'),
      '(',
      field('condition', $.unified_where_conditions),
      ')',
      field('then_relation', $._simple_table_relation),
      optional(seq(
        choice('ELSE', 'else', 'Else'),
        field('else_relation', $.table_relation_expression)
      ))
    )),

    _simple_table_relation: $ => seq(
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

    filter_criteria: $ => /[^)]+/,

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
      $.exist_formula
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

    lookup_field_ref: $ => prec(15, choice(
      $.member_expression,
      $.field_access,
      $._quoted_identifier,
      $.identifier
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
      choice('true', 'false'),
      ';'
    ),

    option_members_property: $ => prec(1, seq(
      'OptionMembers',
      '=',
      choice(
        $.string_literal,  // Single string literal case
        seq(               // Multiple identifiers case
          optional($.option_member),
          repeat(seq(',', optional($.option_member)))
        )
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
      'OptionCaption',
      '=',
      $.option_caption_value,
      ';'
    ),

    field_trigger_declaration: $ => seq(
      choice('trigger', 'TRIGGER', 'Trigger'),
      field('type', alias(choice(
        choice('OnValidate', 'ONVALIDATE', 'Onvalidate'),
        choice('OnLookup', 'ONLOOKUP', 'Onlookup'),
        choice('OnAssistEdit', 'ONASSISTEDIT', 'OnAssistEdit'),
        choice('OnDrillDown', 'ONDRILLDOWN', 'OnDrillDown')
      ), $.trigger_type)),
      choice(
        seq('(', optional($.parameter_list), ')'),
        seq()
      ),
      optional(seq(':', $.type_specification)),
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
      choice($._quoted_identifier, $.identifier),
      repeat(seq(',', choice($._quoted_identifier, $.identifier)))
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

    return_value: $ => field('return_value', $.identifier),

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

    procedure_modifier: $ => choice('local', 'LOCAL', 'Local', 'internal', 'INTERNAL', 'Internal'),

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
      optional($.var_section),
      $.code_block,
      optional(';')
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
      token(prec(10, seq('"', /[^"\n\\]+/, '"'))),
      $.quoted_identifier
    ),

    string_literal: $ => token(
      choice(
        // Empty string
        seq("'", "'"),
        
        // Non-empty string
        seq(
          "'",
          repeat1(choice(
            /[^'\\\n]+/,   // One or more chars except quote, backslash, or newline
            /\\./,         // Match any escaped character (e.g., \\, \', \", \#, etc.)
            /\\/,          // Single backslash (for character literals like '\')
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
      token(prec(1, 'true')),
      token(prec(1, 'false'))
    ),

    temporary: $ => choice('temporary', 'TEMPORARY', 'Temporary'),


    // Define code blocks with explicit keyword handling
    code_block: $ => prec.right(1, seq(
      choice('begin', 'BEGIN', 'Begin'),
      optional(repeat($._statement)),
      choice('end', 'END', 'End'),
      optional(token(';')) // Explicit token
    )),

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


    for_statement: $ => prec.right(seq(
      choice('for', 'FOR', 'For'),
      field('variable', $.identifier),
      ':=',
      field('start', $._expression),
      choice('to', 'TO', 'To'),
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

    _literal_argument: $ => prec(1, choice(
      alias($._quoted_identifier, $.quoted_identifier),
      $.string_literal,
      $.integer,
      $.decimal,
      $.boolean
    )),

    _primary_expression: $ => choice(
      $._literal_value,
      $.identifier,
      $.parenthesized_expression,
      $.unary_expression,
      // $.call_expression, // Handled in _expression
      $.member_expression
    ),

    _base_expression: $ => prec(1, choice(
      $._primary_expression,
      $._chained_expression
    )),

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
      choice('-', 'not', 'Not', 'NOT'),
      $._expression
    )),

    _expression: $ => choice(
      // --- Binary Operators First ---
      // Arithmetic operator expression (*, /, div, mod) (prec 7)
      prec.left(7, seq(
        field('left', $._expression),
        // Explicitly list operators for this precedence level
        field('operator', choice('*', '/', /[dD][iI][vV]/, /[mM][oO][dD]/)),
        field('right', $._expression)
      )),
      // Arithmetic operator expression (+, -) (prec 6)
      prec.left(6, seq(
        field('left', $._expression),
        field('operator', choice('+', '-')),
        field('right', $._expression)
      )),
      // Comparison operator expression (prec 6)
      prec.left(6, seq(
        field('left', $._expression),
        field('operator', $.comparison_operator),
        field('right', $._expression)
      )),
      // 'in' expression (prec 5)
      prec.left(5, seq(
        field('left', $._expression),
        field('operator', $.in_operator),
        field('right', $.list_literal) // Right side is typically a list literal
      )),
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
      // --- Other Expression Forms ---
      // Method chains (put this first among non-binary expressions for higher precedence)
      $.call_expression, // (prec 12)
      $.enum_keyword_qualified_value, // (prec 9)
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

    // 'in' operator
    in_operator: $ => choice('in', 'IN', 'In'),

    // List literal for 'in' expression or other contexts
    list_literal: $ => seq(
      '[',
      optional($.expression_list), // Use existing expression_list for comma-separated expressions
      ']'
    ),

    // Rule for array indexing/subscript expressions
    subscript_expression: $ => prec.left(9, seq(
      field('array', $._expression),
      '[',
      field('index', $._expression),
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
        $._statement,
        $.code_block
      )),
      optional(seq(
        choice('else', 'ELSE', 'Else'),
        field('else_branch', choice(
          $._statement,
          $.code_block
        ))
      ))
    )),

    // Case expression uses the general _expression rule
    _case_expression: $ => $._expression,

    case_statement: $ => prec(2, seq(
      choice('case', 'CASE', 'Case'),
      field('expression', $._case_expression),
      choice('of', 'OF', 'Of'),
      repeat1($.case_branch),
      optional($.else_branch),
      choice('end', 'END', 'End')
    )),

    case_branch: $ => seq(
      field('pattern', $._case_pattern),
      $._colon,
      field('statements', choice(
        $.code_block,
        $._statement
      ))
    ),

    // _case_pattern now directly handles single or multiple patterns
    _case_pattern: $ => choice(
      // Case 1: Multiple patterns separated by commas
      seq(
        $._single_pattern,
        repeat1(seq(',', $._single_pattern))
      ),
      // Case 2: A single pattern element
      $._single_pattern
    ),

    // _single_pattern defines the elements allowed within a case pattern
    _single_pattern: $ => choice(
      $._literal_value,
      $.enum_value_expression, // Match the full Record.Field::Value or EnumType::Value pattern
      $.database_reference, // Allow DATABASE::"Table Name" patterns
      $._chained_expression, // Allow member expressions like Value.IsInteger
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
      $.string_literal,
      $.boolean
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

    multiplicity_property: $ => seq(
      'Multiplicity',
      '=',
      field('value', $.multiplicity_value),
      ';'
    ),

    multiplicity_value: $ => choice(
      /[oO][nN][eE]/,
      /[mM][aA][nN][yY]/
    ),

    show_filter_property: $ => seq(
      'ShowFilter',
      '=',
      field('value', $.boolean),
      ';'
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

    grid_layout_property: $ => seq(
      'GridLayout',
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

    tree_initial_state_property: $ => seq(
      'TreeInitialState',
      '=',
      field('value', $.tree_initial_state_value),
      ';'
    ),

    tree_initial_state_value: $ => choice(
      /[cC][oO][lL][lL][aA][pP][sS][eE][aA][lL][lL]/,
      /[eE][xX][pP][aA][nN][dD][aA][lL][lL]/
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

    sign_displacement_property: $ => seq(
      'SignDisplacement',
      '=',
      field('value', $.boolean),
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

    filter_expression: $ => seq(
      choice(
        $.where_clause,
        $.sorting_clause,
        seq($.where_clause, $.sorting_clause),
        seq($.sorting_clause, $.where_clause)
      )
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

    indentation_column_property: $ => seq(
      'IndentationColumn',
      '=',
      field('value', choice($.identifier, $._quoted_identifier, $.string_literal)),
      ';'
    ),

    indentation_controls_property: $ => seq(
      'IndentationControls',
      '=',
      field('value', choice(
        $.identifier,
        $._quoted_identifier,
        $.string_literal
      )),
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
      field('value', choice(
        $.sorting_expression,
        $.source_table_view_value
      )),
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

    pragma: $ => /#[^\n]*/, // Match any line starting with #

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
      'Text', 'text', 'TEXT',
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




  },

});
