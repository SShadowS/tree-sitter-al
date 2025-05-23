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
  extras: $ => [/\s/, $.comment, $.pragma],

  rules: {
    source_file: $ => repeat($._object),

    _object: $ => choice(
      $.table_declaration,
      $.codeunit_declaration,
      $.pageextension_declaration,
      $.page_declaration,
      $.query_declaration,
      $.enumextension_declaration // Added enumextension
    ),

    enumextension_declaration: $ => seq(
      /[eE][nN][uU][mM][eE][xX][tT][eE][nN][sS][iI][oO][nN]/,
      field('object_id', $.object_id),
      field('object_name', $.object_name),
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
      field('object_id', $.object_id),
      field('object_name', $.object_name),
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

    context_sensitive_help_page_property: $ => seq(
      'ContextSensitiveHelpPage',
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
      field('object_id', $.object_id),
      field('object_name', $.object_name),
      /[eE][xX][tT][eE][nN][dD][sS]/,
      field('base_object', choice($._quoted_identifier, $.identifier)),
      '{',
      repeat($._pageextension_element),
      '}'
    ),

    _pageextension_element: $ => choice(
      $.actions_section,
      $.property_list
    ),

    actions_section: $ => seq(
      /[aA][cC][tT][iI][oO][nN][sS]/,
      '{',
      repeat(choice(
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
        /[cC][rR][eE][aA][tT][iI][oO][nN]/
      )),
      ')',
      '{',
      repeat(choice(
        $.action_declaration,
        $.action_group_section
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
        $.action_property,
        $.property_list
      )),
      '}'
    ),

    _action_group: $ => choice(
      $.addfirst_action_group,
      $.addlast_action_group,
      $.addafter_action_group,
      $.addbefore_action_group,
      $.modify_action_group
    ),

    addfirst_action_group: $ => seq(
      /[aA][dD][dD][fF][iI][rR][sS][tT]/,
      '(',
      field('target', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat($._action_element),
      '}'
    ),

    addlast_action_group: $ => seq(
      /[aA][dD][dD][lL][aA][sS][tT]/,
      '(',
      field('target', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat($._action_element),
      '}'
    ),

    addafter_action_group: $ => seq(
      /[aA][dD][dD][aA][fF][tT][eE][rR]/,
      '(',
      field('target', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat($._action_element),
      '}'
    ),

    addbefore_action_group: $ => seq(
      /[aA][dD][dD][bB][eE][fF][oO][rR][eE]/,
      '(',
      field('target', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat($._action_element),
      '}'
    ),

    modify_action_group: $ => seq(
      /[mM][oO][dD][iI][fF][yY]/,
      '(',
      field('target', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat($._action_element),
      '}'
    ),

    _action_element: $ => choice(
      $.action_declaration,
      $.actionref_declaration
    ),

    action_declaration: $ => seq(
      /[aA][cC][tT][iI][oO][nN]/,
      '(',
      field('name', choice($.identifier, $._quoted_identifier)),
      ')',
      '{',
      repeat(choice(
        $.action_property,
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
        $.action_property,
        $.trigger_declaration,
        $.var_section
      )),
      '}'
    ),

    action_property: $ => choice(
      $.application_area_property,
      $.caption_property,
      $.image_property,
      $.run_object_property,
      $.run_page_link_property,
      $.run_page_view_property,
      $.tool_tip_property,
      $.enabled_property,
      $.visible_property,
      $.scope_property,
      $.promoted_property,
      $.promoted_category_property,
      $.promoted_only_property,
      $.promoted_is_big_property,
      $.shortcut_key_property
    ),

    application_area_property: $ => seq(
      'ApplicationArea',
      '=',
      field('value', choice($.identifier, $._quoted_identifier, $.string_literal)),
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
      field('value', choice($.identifier, $._quoted_identifier)),
      ';'
    ),

    run_object_property: $ => seq(
      'RunObject',
      '=',
      field('value', $.run_object_value),
      ';'
    ),

    run_object_value: $ => seq(
      choice('Page', 'PAGE', 'page', 'Report', 'REPORT', 'report'),
      field('page_name', choice($.identifier, $._quoted_identifier))
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
        )
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
          field('const_value', choice($.identifier, $._quoted_identifier)),
          ')'
        ),
        seq(
          /[fF][iI][eE][lL][dD]/,
          '(',
          field('field_value', choice($.identifier, $._quoted_identifier)),
          ')'
        )
      )),
      repeat(seq(
        ',',
        field('field', choice($.identifier, $._quoted_identifier)),
        '=',
        field('filter_type', choice(
          seq(
            /[cC][oO][nN][sS][tT]/,
            '(',
            field('const_value', choice($.identifier, $._quoted_identifier)),
            ')'
          ),
          seq(
            /[fF][iI][eE][lL][dD]/,
            '(',
            field('field_value', choice($.identifier, $._quoted_identifier)),
            ')'
          )
        ))
      ))
    ),

    enabled_property: $ => seq(
      'Enabled',
      '=',
      field('value', choice($.boolean, $.identifier, $._quoted_identifier)),
      ';'
    ),

    visible_property: $ => seq(
      'Visible',
      '=',
      field('value', choice($.boolean, $.identifier, $._quoted_identifier)),
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

    shortcut_key_property: $ => seq(
      'ShortCutKey',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    _assignment_operator: $ => token(choice(':=', '+=', '-=', '*=', '/=')),
    _double__colon: $ => token(prec(1, '::')),
    _colon: $ => ':',


    object_id: $ => seq($.integer),
    object_name: $ => field('name', choice(
      $._quoted_identifier,
      $.identifier
    )),

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

    drilldown_pageid_property: $ => seq(
      'DrillDownPageId',
      '=', 
      field('value', alias($.page_id_value, $.value)),
      ';'
    ),

    lookup_pageid_property: $ => seq(
      'LookupPageId',
      '=',
      field('value', alias($.page_id_value, $.value)),
      ';'
    ),

    card_page_id_property: $ => seq(
      'CardPageId',
      '=',
      field('value', alias($.page_id_value, $.value)),
      ';'
    ),

    promoted_action_categories_property: $ => seq(
      'PromotedActionCategories',
      '=',
      field('value', $.string_literal),
      ';'
    ),

    table_declaration: $ => seq(
      /[tT][aA][bB][lL][eE]/,
      field('object_id', $.object_id),
      field('object_name', $.object_name),
      '{',
      repeat($._table_element),
      '}'
    ),

    codeunit_declaration: $ => seq(
      /[cC][oO][dD][eE][uU][nN][iI][tT]/,
      field('object_id', $.object_id),
      field('object_name', $.object_name),
      '{',
      prec(4, optional($.property_list)), // Prioritize properties over procedures starting with same keywords
      repeat(choice(
        $.var_section,
        seq(optional($.attribute_list), $.procedure),
        seq(optional($.attribute_list), $.onrun_trigger),
        seq(optional($.attribute_list), $.generic_trigger) // Added generic trigger support
      )),
      '}'
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
      field('object_id', $.object_id),
      field('object_name', $.object_name),
      '{',
      repeat($._page_element),
      '}'
    ),

    _page_element: $ => choice(
      $.property_list,
      $.layout_section,
      $.actions_section,
      $.procedure,
      $.var_section,
      $.trigger_declaration,
      $.description_property,
      $.caption_property,
      $.scope_property,
      $.promoted_property,
      $.promoted_category_property,
      $.promoted_only_property,
      $.promoted_is_big_property,
      $.run_object_property,
      $.run_page_link_property,
      $.run_page_view_property,
      $.image_property,
      $.tool_tip_property
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
      $.repeater_section,
      $.field_section,
      $.part_section
    ),

    area_section: $ => seq(
      /[aA][rR][eE][aA]/,
      '(',
      field('type', choice(
        /[cC][oO][nN][tT][eE][nN][tT]/,
        /[fF][aA][cC][tT][bB][oO][xX][eE][sS]/,
        /[fF][iI][lL][tT][eE][rR]/
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
        $.property_list
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
        $.property_list
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
          $.property_list,
          $.caption_property,
          $.application_area_property,
          $.tool_tip_property,
          $.visible_property,
          $.enabled_property,
          $.source_expr_property,
          $.editable_property,
          $.description_property,
          $.lookup_pageid_property,
          $.field_trigger_declaration
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
          $.property_list,
          $.caption_property,
          $.application_area_property,
          $.tool_tip_property,
          $.visible_property,
          $.enabled_property,
          $.source_expr_property,
          $.editable_property,
          $.description_property,
          $.lookup_pageid_property,
          $.field_trigger_declaration
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
          $.property_list,
          $.caption_property,
          $.application_area_property,
          $.tool_tip_property,
          $.visible_property,
          $.enabled_property,
          $.lookup_pageid_property,
          $.run_object_property,
          $.run_page_link_property,
          $.source_expr_property,
          $.editable_property,
          $.field_trigger_declaration
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
        $.sub_page_link_property
      )),
      '}'
    ),

    sub_page_link_property: $ => seq(
      'SubPageLink',
      '=',
      field('value', $.run_page_link_value),
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
        /[oO][nN][aA][cC][tT][iI][oO][nN]/
      ), $.trigger_type)),
      '()',
      // Give higher precedence to the standard structure
      prec(1, seq(
        optional($.var_section),
        $.code_block
      ))
      // Removed the ambiguous alternative structure for now
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

    field_class_value: $ => choice(
      /[fF][lL][oO][wW][fF][iI][eE][lL][dD]/,
      /[fF][lL][oO][wW][fF][iI][lL][tT][eE][rR]/,
      /[nN][oO][rR][mM][aA][lL]/
    ),

    editable_value: $ => $.boolean,

    extended_datatype_value: $ => choice(
      /[pP][hH][oO][nN][eE][nN][oO]/,
      /[uU][rR][lL]/, 
      /[eE][mM][aA][iI][lL]/,
      /[rR][aA][tT][iI][oO]/,
      /[dD][uU][rR][aA][tT][iI][oO][nN]/,
      /[mM][aA][sS][kK][eE][dD]/
    ),

    page_id_value: $ => choice(
      $.integer,
      $.identifier,
      prec(1, $._quoted_identifier)
    ),

    permissions_value: $ => $.tabledata_permission_list,

    calc_formula_value: $ => $._calc_formula_expression,

    blank_zero_value: $ => $.boolean,

    option_members_value: $ => choice(
      $.string_literal,
      seq(
      $.option_member,
      repeat(seq(',', $.option_member))
      )
    ),

    option_caption_value: $ => $.string_literal,

    table_type_value: $ => choice(
      /[nN][oO][rR][mM][aA][lL]/,
      /[tT][eE][mM][pP][oO][rR][aA][rR][yY]/,
      /[eE][xX][tT][eE][rR][nN][aA][lL]/,
      /[sS][yY][sS][tT][eE][mM]/
    ),

    closing_dates_value: $ => $.boolean,
    char_allowed_value: $ => $.boolean,
    compressed_value: $ => $.boolean,
    date_formula_value: $ => $.string_literal,
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
      choice($._quoted_identifier, $.string_literal),
      repeat(seq(',', choice($._quoted_identifier, $.string_literal)))
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

    auto_format_expression_value: $ => $.string_literal,

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

    blank_numbers_value: $ => $.boolean,

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
      $.closing_dates_value,
      ';'
    ),

    char_allowed_property: $ => seq(
      'CharAllowed',
      '=',
      $.char_allowed_value,
      ';'
    ),

    compressed_property: $ => seq(
      'Compressed', 
      '=',
      $.compressed_value,
      ';'
    ),

    date_formula_property: $ => seq(
      'DateFormula',
      '=',
      $.date_formula_value,
      ';'
    ),

    description_property: $ => seq(
      'Description',
      '=',
      $.description_value,
      ';'
    ),

    external_access_property: $ => seq(
      'ExternalAccess',
      '=',
      $.external_access_value,
      ';'
    ),

    external_name_property: $ => seq(
      'ExternalName',
      '=',
      $.external_name_value,
      ';'
    ),

    external_type_property: $ => seq(
      'ExternalType',
      '=',
      $.external_type_value,
      ';'
    ),

    init_value_property: $ => seq(
      'InitValue',
      '=',
      $.init_value_value,
      ';'
    ),

    max_value_property: $ => seq(
      'MaxValue',
      '=',
      $.max_value_value,
      ';'
    ),

    min_value_property: $ => seq(
      'MinValue',
      '=',
      $.min_value_value,
      ';'
    ),

    not_blank_property: $ => seq(
      'NotBlank',
      '=',
      $.not_blank_value,
      ';'
    ),

    numeric_property: $ => seq(
      'Numeric',
      '=',
      $.numeric_value,
      ';'
    ),

    obsolete_reason_property: $ => seq(
      'ObsoleteReason',
      '=',
      $.obsolete_reason_value,
      ';'
    ),

    obsolete_state_property: $ => seq(
      'ObsoleteState',
      '=',
      $.obsolete_state_value,
      ';'
    ),

    obsolete_tag_property: $ => seq(
      'ObsoleteTag',
      '=',
      $.obsolete_tag_value,
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
      '[',
      repeat1($.ml_value_pair),
      ']'
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
      $.procedure,
      $.caption_property,
      $.data_classification_property,
      $.var_section,
      $.permissions_property,
      $.drilldown_pageid_property,
      $.lookup_pageid_property,
      $.table_type_property,
      $.access_property,
      $.fieldgroups_section
    )),

    // For single table permission property
    permissions_property: $ => seq(
      'Permissions',
      '=',
      $.tabledata_permission_list,
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
    
    member: $ => choice(
      $.identifier,
      $._quoted_identifier
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
      $.drilldown_pageid_property,
      $.lookup_pageid_property,
      $.card_page_id_property,
      $.promoted_action_categories_property,
      $.permissions_property,
      $.table_relation_property,
      $.field_class_property,
      $.calc_formula_property,
      $.blank_zero_property,
      $.editable_property,
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
      $.access_property, // Added Access property
      $.caption_property, // Added Caption property for enum values
      // NEW HIGH PRIORITY PROPERTIES
      $.data_caption_fields_property,
      $.extensible_property,
      $.data_per_company_property,
      $.replicate_data_property,
      $.column_store_index_property,
      $.compression_type_property,
      $.inherent_permissions_property,
      $.inherent_entitlements_property
    )),

    caption_property: $ => seq(
      'Caption',
      '=',
      $.string_literal,
      ';'
    ),

    caption_class_property: $ => seq(
      'CaptionClass',
      '=',
      field('value', $.string_literal),
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
      'tabledata', 
      field('table_name', $._table_identifier),
      '=',
      field('permission', $.permission_type)
    ),

    _table_identifier: $ => choice(
      $.identifier,
      $._quoted_identifier
    ),


    decimal_places_property: $ => seq(
      'DecimalPlaces',
      '=',
      field('precision', $.integer),
      ':',
      field('scale', $.integer),
      ';'
    ),

    var_section: $ => seq(
      choice('var', 'VAR', 'Var'),
      repeat($.variable_declaration)
    ),

    // Helper rule for comma-separated variable names
    _variable_name_list: $ => seq(
      field('name', $.identifier),
      repeat(seq(',', field('name', $.identifier)))
    ),

    variable_declaration: $ => choice(
      // Special case for Label with string literal and optional attributes
      // Note: Labels typically don't support multiple declarations on one line in standard AL,
      // but we keep the structure consistent for now. If issues arise, this might need adjustment.
      seq(
        field('names', $._variable_name_list), // Use list rule
        ':',
        choice('Label', 'LABEL', 'label'),
        field('value', $.string_literal),
        optional(seq(
          ',',  // Comma separator
          field('attributes', seq(
            $.label_attribute,
            repeat(seq(',', $.label_attribute))
          ))
        )),
        ';'
      ),
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
      // Regular variable declaration (supporting multiple names)
      seq(
        field('names', $._variable_name_list), // Use list rule
        ':',
        field('type', $.type_specification),
        optional(field('temporary', $.temporary)),
        ';'
      )
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
        field('parameter_name', alias($.identifier, $.name)),
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
  $.dotnet_type,
  $.list_type,
  $.dictionary_type,
  $.page_type,
  $.enum_type,
  $.option_type,
  $.interface_type,
  $.identifier, // Allow plain identifiers as types (e.g., HttpClient, DotNet types)
  $._quoted_identifier // Allow quoted identifiers as types
),

// Handles 'Option' type keyword followed by optional members
option_type: $ => prec(10, seq( // Increased precedence
  choice('Option', 'OPTION', 'Option'),
  optional($.option_member_list) // Members are part of the type
)),

// Helper for comma-separated list of option members
option_member_list: $ => prec.left(1, seq( // Re-added precedence
  $.option_member,
  repeat(seq(',', $.option_member))
)), // Removed extra parenthesis

interface_type: $ => seq(
  prec(1, choice('Interface', 'INTERFACE', 'interface')),
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
      prec(1, choice('ModuleInfo', 'MODULEINFO', 'Moduleinfo')), // Added ModuleInfo
      prec(1, choice('ObjectType', 'OBJECTTYPE', 'Objecttype')), // Added ObjectType
      prec(1, choice('KeyRef', 'KEYREF', 'Keyref')), // Added KeyRef

      // XML Types
      prec(1, choice('XmlDocument', 'XMLDOCUMENT', 'Xmldocument')),
      prec(1, choice('XmlNode', 'XMLNODE', 'Xmlnode')),
      prec(1, choice('XmlElement', 'XMLELEMENT', 'Xmlelement')),
      prec(1, choice('XmlNodeList', 'XMLNODELIST', 'Xmlnodelist')),
      prec(1, choice('XmlAttribute', 'XMLATTRIBUTE', 'Xmlattribute')),
      prec(1, choice('XmlAttributeCollection', 'XMLATTRIBUTECOLLECTION', 'Xmlattributecollection'))
    ),

    text_type: $ => seq(
      prec(1, 'Text'),
      optional(seq(
        '[',
        field('length', $.integer),
        ']'
      ))
    ),

    code_type: $ => seq(
      prec(1, 'Code'),
      optional(seq(
        '[',
        field('length', $.integer),
        ']'
      ))
    ),

    record_type: $ => prec.right(seq(
      prec(1, 'Record'),
      field('reference', $._table_reference),
      optional('Temporary')
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
      prec(1, 'Codeunit'),
      field('reference', choice(
        $.integer,
        $._quoted_identifier,
        $.identifier
      ))
    ),

    query_type: $ => seq(
      prec(1, 'Query'),
      field('reference', $.query_type_value)
    ),

    query_type_value: $ => choice(
      $.integer,
      $._quoted_identifier,
      $.identifier
    ),

    dotnet_type: $ => seq(
      prec(1, 'DotNet'),
      field('reference', choice($.identifier, $.string_literal))
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

    if_table_relation: $ => prec.right(seq(
      choice('IF', 'if', 'If'),
      '(',
      field('condition', $.where_conditions),
      ')',
      field('then_relation', $._simple_table_relation),
      optional(seq(
        choice('ELSE', 'else', 'Else'),
        field('else_relation', $.table_relation_expression)
      ))
    )),

    _simple_table_relation: $ => seq(
      field('table', $._table_reference),
      optional(seq($._double__colon, field('field', $.field_ref))),
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
        $.boolean
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
      choice('FILTER', 'filter', 'Filter'),
      '(',
      field('value', $.filter_criteria),
      ')'
    )),

    where_condition: $ => choice(
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
      $._non_call_chained_expression
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

    where_clause: $ => seq(
      choice('where', 'WHERE', 'Where'),
      '(',
      field('conditions', $.where_conditions),
      ')'
    ),


    field_class_property: $ => seq(
      'FieldClass',
      '=',
      optional('"'),
      $.field_class_value,
      optional('"'),
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
      $.max_formula
    ),

    lookup_formula: $ => seq(
      choice('lookup', 'LOOKUP', 'Lookup'),
      '(',
      field('target', $.field_ref),
      optional(seq(
        choice('where', 'WHERE', 'Where'),
        '(',
        $.lookup_where_conditions,
        ')'
      )),
      ')'
    ),

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
          optional(field('value', $.string_literal)),
          ')'
        )
      )
    ),

    count_formula: $ => seq(
      choice('count', 'COUNT', 'Count'),
      '(',
      field('table', alias($._table_reference, $.table_reference)),
      optional($.where_clause),
      ')'
    ),

    sum_formula: $ => seq(
      choice('sum', 'SUM', 'Sum'),
      '(',
      field('target', $.calc_field_ref),
      optional($.where_clause),
      ')'
    ),

    average_formula: $ => seq(
      choice('average', 'AVERAGE', 'Average'),
      '(',
      field('target', $.calc_field_ref),
      optional($.where_clause),
      ')'
    ),

    min_formula: $ => seq(
      choice('min', 'MIN', 'Min'),
      '(',
      field('target', $.calc_field_ref),
      optional($.where_clause),
      ')'
    ),

    max_formula: $ => seq(
      choice('max', 'MAX', 'Max'),
      '(',
      field('target', $.calc_field_ref),
      optional($.where_clause),
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
      $.string_literal // Added string literal for members like " "
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
      '()',
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
          $.property
        )),
        '}'
      ))
    ),

    key_field_list: $ => seq(
      choice($._quoted_identifier, $.identifier),
      repeat(seq(',', choice($._quoted_identifier, $.identifier)))
    ),

    attribute_list: $ => repeat1($.attribute),

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
      // Return type block
      optional(';'),
      optional(choice(
        $._procedure_return_specification, // : ReturnType
        $._procedure_named_return // ReturnValue : ReturnType
      )),
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

    arithmetic_operator: $ => choice(
      '+',
      '-',
      '*',
      '/',
      /[dD][iI][vV]/, // Add case-insensitive div
      /[mM][oO][dD]/  // Add case-insensitive mod
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

    data_type: $ => choice(
      /[iI][nN][tT][eE][gG][eE][rR]/,
      seq(/[cC][oO][dD][eE]/, '[', field('size', $.integer), ']'),
      seq(/[tT][eE][xX][tT]/, '[', field('size', $.integer), ']'),
      /[dD][eE][cC][iI][mM][aA][lL]/,
      /[bB][oO][oO][lL][eE][aA][nN]/,
      /[oO][pP][tT][iI][oO][nN]/,
      /[rR][eE][cC][oO][rR][dD][iI][dD]/,
      /[dD][aA][tT][eE][tT][iI][mM][eE]/,
      /[dD][aA][tT][eE]/,
      /[tT][iI][mM][eE]/,
      /[bB][lL][oO][bB]/,
      /[dD][uU][rR][aA][tT][iI][oO][nN]/,
      /[bB][iI][gG][iI][nN][tT][eE][gG][eE][rR]/,
      /[gG][uU][iI][dD]/
    ),

    // Define code blocks with explicit keyword handling
    code_block: $ => prec.right(1, seq(
      choice('begin', 'BEGIN', 'Begin'),
      optional(repeat($._statement)),
      choice('end', 'END', 'End'),
      optional(token(';')) // Explicit token
    )),

    _expression_statement: $ => $._expression, // New rule

    _statement: $ => prec.right(seq(
      choice(
        $.assignment_statement,
        $.exit_statement,
        // $.call_expression, // Removed direct call_expression
        $.if_statement,
        $.repeat_statement,
        $.case_statement,
        $.for_statement,
        $.while_statement, // Added while statement
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

    // Removed procedure_call rule

    repeat_statement: $ => seq(
      choice('repeat', 'REPEAT', 'Repeat'),
      repeat1($._statement),
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
      $.qualified_enum_value_tail,
      $._quoted_identifier
    )),


    qualified_enum_value_tail: $ => seq(
      '::',
      choice($.identifier, $._quoted_identifier)
    ),

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
      $.enum_keyword_qualified_value, // (prec 9)
      $.qualified_enum_value, // (prec 9)
      $.field_access,  // (prec 12)
      $.member_expression, // (prec 11)
      $.subscript_expression, // (prec 9)
      $.call_expression, // (prec 12)
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

    // 'in' expression rule (precedence 5, lower than comparisons)
    in_expression: $ => prec.left(5, seq(
      field('left', $._expression),
      field('operator', $.in_operator),
      field('right', $.list_literal) // Right side is typically a list literal
    )),

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

    // Individual method definitions
    // Common base pattern for record operations
    _record_operation: $ => prec(3, seq(
      field('record', alias($.identifier, $.record)),
      '.'
    )),


    enum_value_expression: $ => prec(11, seq( // Adjusted precedence (was 13)
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
      /\d+/,
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
      $.time_literal, // Added time_literal
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
      'else',
      field('statements', $._branch_statements)
    ),

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

    qualified_enum_value: $ => prec.left(9, seq( // Increased precedence
      field('enum_type', choice(
        $._enum_type_reference,
        $.identifier,
        $._quoted_identifier,
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
      $.string_literal
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

    fieldgroups_section: $ => seq(
      /[fF][iI][eE][lL][dD][gG][rR][oO][uU][pP][sS]/,
      '{',
      repeat($.fieldgroup_declaration),
      '}'
    ),

    fieldgroup_list: $ => seq(
      $.fieldgroup_field,
      repeat(seq(',', $.fieldgroup_field))
    ),

    fieldgroup_field: $ => choice(
      $.identifier,
      $._quoted_identifier
    ),

    pragma: $ => /#[^\n]*/, // Match any line starting with #

    comment: $ => token(seq('//', /.*/)),

  },

});
