/**
 * @file AL for Business Central (V2)
 * @author Torben Leth <sshadows@sshadows.dk>
 * @license MIT
 */

/// <reference types="tree-sitter-cli/dsl" />
// @ts-check

// Case-insensitive keyword via regex
function kw(word, precedence = null) {
  const regex = new RustRegex(`(?i)${word}`);
  return precedence !== null ? token(prec(precedence, regex)) : token(regex);
}

// Explicit case-spelling whitelist for compound (CamelCase) keywords.
//
// Unlike kw()'s case-insensitive regex, this matches ONLY the listed spellings,
// so every other case permutation stays available as an identifier — AL code
// really does use `eNuM` as a variable name, and `(?i)enum` would swallow it.
// The whitelist is load-bearing; do not "simplify" these rules to kw().
//
// Each spelling is aliased to the canonical lowercase form so that the node
// shape and the child's type match every other keyword rule, regardless of how
// the source spelled it.
function kwCases(canonical, ...spellings) {
  return choice(...spellings.map(s => s === canonical ? s : alias(s, canonical)));
}

// Dotted-name helper for fields over a namespaced reference.
//
// `field('x', $._namespaced_or_simple_ref)` puts the WHOLE dotted seq in one
// field, so the separating '.' inherits the field too and a consumer calling
// children_by_field_name('x') on `Record System.Reflection.Field` gets back
// [System, '.', Reflection, '.', Field]. Fielding each name part individually
// keeps the separators out of the field — the same fix applied to
// array_type.sizes and link_value.value.
//
// The field name differs per call site (reference / table / table_name), so
// this cannot live inside the shared `_namespaced_or_simple_ref` rule; each
// distinct field name gets its own hidden variant built from this helper.
function namespacedRefFielded($, name) {
  return choice(
    field(name, $.integer),
    prec.right(seq(
      field(name, $._identifier_or_quoted),
      repeat(seq('.', field(name, $._identifier_or_quoted)))
    )),
  );
}

// A statement in body/branch position, holding exactly one node.
//
// `_statement` is hidden and expands to `<statement> optional(';')`, so
// `field(name, $._statement)` labels the ';' too: a consumer calling
// children_by_field_name('body') on `while c do x := 1;` received
// [assignment_statement, ';'] -- two nodes for one body, and `multiple: true`.
//
// Since the terminator restructure this helper no longer carries an
// `optional(';')` of its own. Terminators are EXTERNAL to every branch rule and
// to `code_block`: the ';' belongs to the enclosing statement wrapper
// (`_statement`) or, for a case branch, to `case_branch` itself. That is what
// makes `if C then A; else B;` structurally impossible to read as one
// if_statement -- see the note on if_statement.
//
// `call_statement` is listed separately because it owns its ';' internally, and
// `empty_statement` IS a ';'. Both are still reachable in branch position
// (`while C do ;`, `case 1: Foo;`), but neither is reachable from
// `_statement_inner` any more, so the then-branch of an if can bar them.
function fieldedStatement($, name) {
  return choice(
    field(name, $.call_statement),
    field(name, $.empty_statement),
    field(name, $._statement_inner),
  );
}

// Object declaration helper — with object ID
function _object_with_id(keyword_name) {
  return $ => seq(
    $[keyword_name + '_keyword'],
    field('object_id', $.integer),
    field('object_name', $._identifier_or_quoted),
    '{',
    optional(field('body', $.declaration_body)),
    '}'
  );
}

// Object declaration helper — without object ID
function _object_without_id(keyword_name) {
  return $ => seq(
    $[keyword_name + '_keyword'],
    field('object_name', $._identifier_or_quoted),
    '{',
    optional(field('body', $.declaration_body)),
    '}'
  );
}

// Extension declaration helper — with object ID
function _extension_with_id(keyword_name) {
  return $ => seq(
    $[keyword_name + '_keyword'],
    field('object_id', $.integer),
    field('object_name', $._identifier_or_quoted),
    $.extends_keyword,
    field('base_object', $._identifier_or_quoted),
    '{',
    optional(field('body', $.declaration_body)),
    '}'
  );
}

// Extension declaration helper — without object ID
function _extension_without_id(keyword_name) {
  return $ => seq(
    $[keyword_name + '_keyword'],
    field('object_name', $._identifier_or_quoted),
    $.extends_keyword,
    field('base_object', $._identifier_or_quoted),
    '{',
    optional(field('body', $.declaration_body)),
    '}'
  );
}

module.exports = grammar({
  name: "al",

  word: $ => $.identifier,

  extras: $ => [
    /\s/,
    $.comment,
    $.multiline_comment,
    $.pragma,
    $.preproc_region,
    $.preproc_endregion,
    $.preproc_define,
    $.preproc_undef,
    /\uFEFF/,  // BOM
  ],

  externals: $ => [
    $.property_name,            // [0] identifier followed by = (not :=)
    $.continue_as_identifier,   // [1] 'continue' followed by ':=' (used as variable)
    $.preproc_open,             // [2] #if — depth++
    $.preproc_close,            // [3] #endif — depth--
    $.begin_keyword,            // [4] 'begin' — any depth, unless split claims it
    $.end_keyword,              // [5] 'end' — any depth, unless split claims it
    $.preproc_split_begin,      // [6] 'begin' at depth > 0, immediately before #endif
    $.preproc_split_end,        // [7] 'end' at depth > 0, followed by ; then #elif/#else/#endif
    $.var_attribute_open,       // [8] '[' when attribute is followed by variable declaration
  ],

  conflicts: $ => [
    // An empty #if/#endif (pragma-only, pragmas are extras) after a bodiless
    // field can attach either field-internally (preproc_pragma_only, then `{`
    // body) or at section level (preproc_conditional_fields). GLR explores both;
    // the field-internal path is the only one that doesn't orphan the body.
    [$.field_declaration],
    // A file-leading pragma-only #if/#endif before the namespace can read as
    // preproc_pragma_only or an empty preproc_conditional_object; GLR explores
    // both and the pragma-only path is the one that lets the namespace follow.
    [$.preproc_pragma_only, $.preproc_conditional_object],
    // A pragma-only #if between a procedure header and its body can also read as
    // the body's leading preproc_conditional_var_block; GLR explores both.
    [$.preproc_pragma_only, $.preproc_conditional_var_block],
    [$._property_value, $.option_member],
    [$._property_value, $.option_member, $._identifier_or_quoted],
    [$.caption_value, $.option_member],
    [$.assignment_statement, $.assignment_expression],
    [$.preproc_conditional, $.preproc_conditional_layout],
    [$.preproc_conditional, $.preproc_conditional_layout, $.preproc_conditional_layout_mixed],
    [$.preproc_conditional, $.preproc_conditional_layout_mixed],
    [$.preproc_conditional_layout, $.preproc_conditional_layout_mixed],
    [$.preproc_conditional, $.preproc_conditional_actions],
    [$._expression, $._identifier_or_quoted],
    [$._preproc_split_then_begin_open, $.preproc_split_if_then_begin_else_shared, $.preproc_split_if_begin_else, $._preproc_branch_statement],
    // Inside a preprocessor branch a statement can be read as belonging to the
    // conditional or to an enclosing statement_block. The two were previously
    // indistinguishable because both used `repeat($._statement)` and tree-sitter
    // shared one generated repeat symbol; giving the conditional its own branch
    // content (which also admits a code_block) separates them and exposes the
    // ambiguity that was always there. GLR resolves it by which parse completes.
    [$._preproc_branch_statement, $._preproc_split_then_begin_open,
     $.preproc_split_if_then_begin_else_shared, $.preproc_split_if_begin_else,
     $._preproc_end_branch],
    [$._body_element, $.preproc_conditional_var],
    [$.filter_value, $._literal_value],
    [$.filter_value, $._expression],
    [$._body_element, $._action_element],
    [$._body_element, $._layout_element],
    [$.modify_modification, $.modify_action_modification],
    [$._signed_integer, $.option_member],
    [$.option_member, $._literal_value],
    [$._body_element, $._procedure_header],
    [$._body_element, $._action_element, $._procedure_header],
    [$.page_field, $._field_header],
    [$.field_declaration, $._table_field_header],
    // Fielded variant inherits the property-value ambiguity that the unfielded
    // `_namespaced_or_simple_ref` used to carry here.
    [$._property_value, $.option_member, $._namespaced_ref_table],
    // `Prop = table Foo.Bar` is object_reference_value (unfielded ref) until
    // the '=' that would make it a tabledata_permission (fielded ref) appears,
    // so both dotted-name forms stay live across the dots.
    [$._namespaced_or_simple_ref, $._namespaced_ref_table_name],
    [$.addafter_modification, $.addafter_views_modification],
    [$.addbefore_modification, $.addbefore_views_modification],
    [$._report_body_element, $.preproc_conditional],
    [$._query_body_element, $.preproc_conditional],
    // area_section wraps its leading layout content in layout_body, but its
    // closing brace may be a preproc_split_brace_close (#if-led). GLR must
    // decide whether a #if continues layout_body or opens the split brace.
    [$.layout_body],
    [$.preproc_conditional_report, $.preproc_conditional],
    [$.preproc_conditional_query, $.preproc_conditional],
    [$._xmlport_body_element, $.preproc_conditional],
    [$.preproc_conditional_xmlport, $.preproc_conditional],
    [$._body_element, $._procedure_header, $.preproc_conditional_var],
    [$._body_element],
    [$.calc_field_reference, $._expression],
    [$.option_member, $._identifier_or_quoted],
    [$._single_pattern, $._expression],
    [$.preproc_conditional_link_values, $.preproc_conditional_permissions, $.preproc_conditional_impl_values, $.preproc_conditional_table_relation],
    [$.preproc_conditional_permissions, $.preproc_conditional_table_relation],
    [$.tabledata_permission_list],
    [$._namespaced_ref_table, $._literal_value],
    [$.preproc_conditional_link_values, $.preproc_conditional_permissions, $.preproc_conditional_impl_values],
    [$.preproc_conditional_link_values, $.preproc_conditional_impl_values],
    [$.preproc_conditional_controladdin, $.preproc_conditional],
    [$.procedure, $.interface_procedure_suffix],
    [$.procedure, $._procedure_header, $.interface_procedure_suffix],
    [$._procedure_header, $.interface_procedure_suffix],
    [$.procedure, $._procedure_header],
    [$.procedure, $._procedure_header, $.interface_procedure],
    [$.preproc_conditional_case, $.preproc_split_case_branch, $.preproc_conditional_case_patterns],
    [$.case_branch, $.preproc_split_case_branch, $.preproc_conditional_case_patterns],
    [$.case_branch, $.preproc_split_case_branch, $.preproc_conditional_case_patterns, $.preproc_split_case_extended],
    // Was [$._preproc_guard_block, $._statement]; splitting the terminator out
    // of `_statement` moved this reduction to `_statement_inner`, so the entry
    // is retargeted rather than added to. Guard-block terminator vs statement
    // terminator: `#if C  stmt; if X then  #endif  shared;`
    [$._preproc_guard_block, $._statement_inner],
    [$.if_statement, $._if_statement_no_else],  // dangling-else in case branches
    // if_statement hangs its `else` off `_then_branch_open` directly, while
    // `_if_statement_no_else` and the preproc_split_if_* rules take the whole
    // `_then_branch`. After a then-branch that could be either, only the NEXT
    // token says which — LR cannot see that far, so GLR explores both and the
    // lookahead settles it. Required: generation fails without it. (This
    // replaces the old [$._then_branch, $._then_branch_no_semi] entry, which
    // was the same ambiguity between the pre-restructure then-branch variants.)
    [$.if_statement, $._then_branch],
    // statement_block vs preproc_split_code_block_end after the statement run
    [$.statement_block],
    // var_body run terminates at the following begin (no closing delimiter)
    [$.var_body],
  ],

  // Trivial pass-through wrappers — macro-substituted to drop a layer of indirection.
  inline: $ => [
    $._field_source,
    $._expression_statement,
  ],

  rules: {
    source_file: $ => seq(
      // BC wraps file-leading `#pragma warning disable` in `#if not CLEANxx`
      // before the namespace. Pragmas are extras, so this block is pragma-only.
      repeat($.preproc_pragma_only),
      optional($.namespace_declaration),
      repeat(choice(
        $.using_statement,
        $._object,
        $.preproc_conditional_object,
      )),
    ),

    // Preprocessor conditional wrapping entire objects or using statements
    preproc_conditional_object: $ => seq(
      $.preproc_if,
      optional($.namespace_declaration),
      repeat(choice($.using_statement, $._object, $.preproc_conditional_object)),
      repeat(seq(
        $.preproc_elif,
        optional($.namespace_declaration),
        repeat(choice($.using_statement, $._object, $.preproc_conditional_object)),
      )),
      optional(seq(
        $.preproc_else,
        optional($.namespace_declaration),
        repeat(choice($.using_statement, $._object, $.preproc_conditional_object)),
      )),
      $.preproc_endif,
    ),

    // --- Namespace / Using ---

    namespace_declaration: $ => seq(
      $.namespace_keyword,
      field('name', $.namespace_name),
      ';'
    ),

    using_statement: $ => seq(
      $.using_keyword,
      field('namespace', $.namespace_name),
      ';'
    ),

    namespace_name: $ => prec.right(seq(
      $.identifier,
      repeat(seq('.', $.identifier))
    )),

    // --- Object types ---

    _object: $ => choice(
      $.table_declaration,
      $.tableextension_declaration,
      $.page_declaration,
      $.pageextension_declaration,
      $.pagecustomization_declaration,
      $.codeunit_declaration,
      $.report_declaration,
      $.reportextension_declaration,
      $.query_declaration,
      $.xmlport_declaration,
      $.enum_declaration,
      $.enumextension_declaration,
      $.interface_declaration,
      $.controladdin_declaration,
      $.dotnet_declaration,
      $.profile_declaration,
      $.profileextension_declaration,
      $.permissionset_declaration,
      $.permissionsetextension_declaration,
      $.entitlement_declaration,
      $.preproc_split_declaration,
    ),

    // Preprocessor-split object declaration:
    // #if ... codeunit 1 "Name" implements A #else codeunit 1 "Name" implements B #endif { body }
    // Also handles nested: #if A header1 #else #if B header2 #else header3 #endif #endif { body }
    preproc_split_declaration: $ => prec(25, seq(
      $.preproc_if,
      $._object_header,
      repeat(seq($.preproc_elif, $._object_header)),
      optional(seq($.preproc_else, choice(
        $._object_header,
        // Nested: #else #if ... #endif
        seq(
          $.preproc_if,
          $._object_header,
          repeat(seq($.preproc_elif, $._object_header)),
          optional(seq($.preproc_else, $._object_header)),
          $.preproc_endif,
        ),
      ))),
      $.preproc_endif,
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    )),

    // Object header without body (used in preproc split declarations)
    _object_header: $ => choice(
      seq($.codeunit_keyword, field('object_id', $.integer), field('object_name', $._identifier_or_quoted), optional($.implements_clause)),
      seq($.enum_keyword, field('object_id', $.integer), field('object_name', $._identifier_or_quoted), optional($.implements_clause)),
      seq(choice($.table_keyword, $.page_keyword, $.report_keyword, $.query_keyword, $.xmlport_keyword, $.permissionset_keyword),
        field('object_id', $.integer), field('object_name', $._identifier_or_quoted)),
      seq(choice($.tableextension_keyword, $.pageextension_keyword, $.reportextension_keyword, $.enumextension_keyword, $.permissionsetextension_keyword),
        field('object_id', $.integer), field('object_name', $._identifier_or_quoted), $.extends_keyword, field('base_object', $._identifier_or_quoted)),
      seq($.interface_keyword, field('object_name', $._identifier_or_quoted)),
    ),

    // --- With ID, no extends ---

    table_declaration: _object_with_id('table'),
    // Issue #19: content-only body node under `body` field for textobject
    // queries. Delimiters `{` `}` stay on the declaration; the declaration_body node
    // spans exactly the content (no braces) so Helix `@class.inside` can capture
    // a single node. declaration_body uses repeat1 (tree-sitter forbids a named rule
    // that matches the empty string), so it is wrapped in optional(): an empty
    // `{ }` emits NO body node. Consumers must tolerate the missing node.
    page_declaration: $ => seq(
      $.page_keyword,
      field('object_id', $.integer),
      field('object_name', $._identifier_or_quoted),
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    ),
    declaration_body: $ => repeat1($._body_element),
    report_declaration: _object_with_id('report'),
    query_declaration: _object_with_id('query'),
    xmlport_declaration: _object_with_id('xmlport'),
    permissionset_declaration: _object_with_id('permissionset'),

    // --- With ID + optional implements ---

    codeunit_declaration: $ => seq(
      $.codeunit_keyword,
      field('object_id', $.integer),
      field('object_name', $._identifier_or_quoted),
      optional($.implements_clause),
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    ),

    enum_declaration: $ => seq(
      $.enum_keyword,
      field('object_id', $.integer),
      field('object_name', $._identifier_or_quoted),
      optional($.implements_clause),
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    ),

    // --- With ID + extends ---

    tableextension_declaration: _extension_with_id('tableextension'),
    pageextension_declaration: _extension_with_id('pageextension'),
    reportextension_declaration: _extension_with_id('reportextension'),
    enumextension_declaration: _extension_with_id('enumextension'),
    permissionsetextension_declaration: _extension_with_id('permissionsetextension'),

    // --- Without ID ---

    controladdin_declaration: $ => seq(
      $.controladdin_keyword,
      field('object_name', $._identifier_or_quoted),
      '{',
      optional(field('body', $.controladdin_body)),
      '}'
    ),
    controladdin_body: $ => repeat1(choice($._body_element, $.interface_procedure, $.preproc_conditional_controladdin)),

    // Preprocessor conditional inside controladdin bodies (needs interface_procedure support)
    preproc_conditional_controladdin: $ => seq(
      $.preproc_if,
      repeat(choice($._body_element, $.interface_procedure, $.preproc_conditional_controladdin)),
      repeat(seq(
        $.preproc_elif,
        repeat(choice($._body_element, $.interface_procedure, $.preproc_conditional_controladdin)),
      )),
      optional(seq(
        $.preproc_else,
        repeat(choice($._body_element, $.interface_procedure, $.preproc_conditional_controladdin)),
      )),
      $.preproc_endif,
    ),
    profile_declaration: _object_without_id('profile'),
    entitlement_declaration: _object_without_id('entitlement'),

    // --- Without ID + extends ---

    profileextension_declaration: _extension_without_id('profileextension'),

    // --- Interface (without ID, optional extends) ---

    interface_declaration: $ => seq(
      $.interface_keyword,
      field('object_name', $._identifier_or_quoted),
      optional(seq(
        $.extends_keyword,
        field('extends_interface', $._identifier_or_quoted)
      )),
      optional(seq(
        $.access_keyword,
        '=',
        field('access_value', choice(
          $.internal_keyword,
          $.public_keyword,
          $.identifier
        ))
      )),
      '{',
      optional(field('body', $.interface_body)),
      '}'
    ),
    interface_body: $ => repeat1(choice($._body_element, $.interface_procedure)),

    // --- Pagecustomization (without ID, uses customizes) ---

    pagecustomization_declaration: $ => seq(
      $.pagecustomization_keyword,
      field('object_name', $._identifier_or_quoted),
      $.customizes_keyword,
      field('target_page', $._identifier_or_quoted),
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    ),

    // --- Dotnet (no ID, no name) ---

    dotnet_declaration: $ => seq(
      $.dotnet_keyword,
      '{',
      optional(field('body', $.dotnet_body)),
      '}'
    ),
    dotnet_body: $ => repeat1($.assembly_declaration),

    // --- Implements clause ---

    implements_clause: $ => seq(
      $.implements_keyword,
      field('interface', $._identifier_or_quoted),
      repeat(seq(',', field('interface', $._identifier_or_quoted)))
    ),

    // =====================================================================
    // Body elements — all sections/declarations that can appear in object bodies
    // =====================================================================

    _body_element: $ => choice(
      $.property,
      alias($.permissions_property, $.property),
      alias($.table_relation_property, $.property),
      $.empty_statement,
      // Table internals
      $.fields_section,
      $.keys_section,
      $.fieldgroups_section,
      // Enum values
      $.enum_value_declaration,
      // Labels
      $.labels_section,
      // Page layout & actions
      $.layout_section,
      $.actions_section,
      $.views_section,
      $.analysisviews_section,
      // Report sections
      $.dataset_section,
      $.requestpage_section,
      $.rendering_section,
      // Query sections
      $.elements_section,
      // XMLport sections
      $.schema_section,
      // DotNet internals
      $.assembly_declaration,
      // Code structure
      $.procedure,
      $.trigger_declaration,
      $.var_section,
      $.attribute_item,
      // ControlAddIn event declarations
      $.event_declaration,
      // Preprocessor-split procedure: header variants in #if/#else, shared body
      $.preproc_split_procedure,
      // Preprocessor-split procedure preamble: header+var in #if/#else, shared body after #endif
      $.preproc_split_procedure_preamble,
      // Preprocessor conditionals
      $.preproc_conditional,
      // Extension modifications (table/page extensions)
      $.modify_modification,
    ),

    // =====================================================================
    // Properties
    // =====================================================================

    // --- Generic property: Name = Value ; ---
    // The scanner's PROPERTY_NAME token disambiguates from variables (Name : Type)
    // All properties share this structure; complex value types are part of _property_value.
    property: $ => seq(
      field('name', $.property_name),   // Scanner token: identifier followed by =
      '=',
      optional(field('value', $._property_value)),
      ';'
    ),

    // --- Permissions property: Name = tabledata_permission_list (no trailing ;) ---
    // Used when the terminating ';' is consumed inside the permission list's preproc branch.
    // Pattern: Permissions = tabledata Foo = rimd, tabledata Bar = rimd #if ... ; #endif
    // The alias ensures the AST node type remains 'property'.
    // Lower precedence than 'property' so 'property' (with ';') is preferred when ';' follows.
    permissions_property: $ => prec(-1, seq(
      field('name', $.property_name),
      '=',
      field('value', $.tabledata_permission_list),
    )),

    // --- TableRelation property variant: ';' may be consumed inside preproc branches ---
    // Used when the terminating ';' is inside #if/#else branches of a conditional table relation.
    // Pattern: TableRelation = if (...) Item else #if BC24 if (...) Table; #else IF (...) Table; #endif
    // Restricted to preproc_conditional_table_relation (not plain table_relation_value) to avoid
    // ambiguity with AccessByPermission/Permissions properties that use keyword identifiers.
    // The alias ensures the AST node type remains 'property'.
    // Lower precedence than 'property' so 'property' (with ';') is preferred when ';' follows.
    table_relation_property: $ => prec(-1, seq(
      field('name', $.property_name),
      '=',
      field('value', choice(
        $.preproc_conditional_table_relation,
        seq($.table_relation_expression, $.preproc_conditional_table_relation),
        $.if_table_relation,
      )),
    )),

    _property_value: $ => choice(
      // Simple values
      $.boolean,
      $.integer,
      $.decimal,
      $.string_literal,
      $.verbatim_string,
      $.identifier,
      $.quoted_identifier,
      // Complex value types
      $.caption_value,              // 'Text', Locked = true, Comment = '...'
      $.ml_value_list,              // ENU='English', DEU='German'
      $._calc_formula_expression,   // sum("Table".Field where(...))
      $.tabledata_permission_list,  // tabledata X = R, tabledata Y = RIMD
      $.order_by_list,              // ascending("No.", Name)
      $.implementation_value_list,  // "IFace" = "Impl", ...
      $.option_member_list,         // Option1, Option2, "Option 3"
      $.table_relation_value,       // Customer where(...) or if(...) Item else Resource
      $.sorting_value,              // sorting("Starting Date")
      $.link_value_list,            // "Field" = field(Other), ...
      $.property_expression,        // Expressions used as property values
      $.keyword_identifier,         // Keywords used as simple property values (TestIsolation = Codeunit)
      $.where_clause,               // SourceTableView/SubPageView = where(...)
      $.object_reference_value,     // RunObject = Codeunit "BOM-Explode BOM"
      $.decimal_range_value,        // DecimalPlaces = 0 : 5
      $.signed_integer_list,        // OptionOrdinalValues = -1, 0, 1
      $.time_literal,               // InitValue = 000000T
      $.date_literal,               // InitValue = 0D
      $.datetime_literal,           // InitValue = 0DT
    ),

    // Decimal range: N : M (used by DecimalPlaces property)
    decimal_range_value: $ => prec(5, seq(
      field('min', $.integer),
      ':',
      optional(field('max', $.integer))
    )),

    // Signed integer list: -1, 0, 1, 2 (used by OptionOrdinalValues)
    signed_integer_list: $ => prec.left(5, seq(
      $._signed_integer,
      repeat1(seq(',', $._signed_integer))
    )),

    _signed_integer: $ => choice(
      $.integer,
      seq('-', $.integer),
    ),

    // Object reference as property value: Codeunit "BOM-Explode BOM"
    // Also supports namespace: Page Microsoft.Sales."Sales Order"
    object_reference_value: $ => prec(3, seq(
      choice(
        $.codeunit_keyword,
        $.page_keyword,
        $.report_keyword,
        $.query_keyword,
        $.xmlport_keyword,
        $.table_keyword,
      ),
      $._namespaced_or_simple_ref,
    )),

    // Expressions that can appear as property values (member access, function calls, etc.)
    property_expression: $ => prec(-2, choice(
      $.call_expression,
      $.member_expression,
      $.qualified_enum_value,
      $.database_reference,
      $.unary_expression,
      $.additive_expression,
      $.multiplicative_expression,
      $.comparison_expression,
      $.logical_expression,
      $.ternary_expression,         // DataCaptionExpression = Cond ? A : B
      $.parenthesized_expression,
      $.subscript_expression,
    )),

    boolean: $ => choice(kw('true'), kw('false')),

    decimal: $ => token(seq(/\d+/, '.', /\d+/)),

    // --- Caption value with sub-fields (Locked, Comment, MaxLength) ---
    // 'My Caption', Locked = true, Comment = 'text', MaxLength = 100
    // Also handles trailing comma: Caption = 'text',;
    // Uses property_name (scanner token) since the sub-fields follow Name = Value pattern
    caption_value: $ => prec.right(seq(
      choice($.string_literal, $.verbatim_string),
      choice(
        seq(
          repeat1(seq(
            ',',
            $.property_name,
            '=',
            choice($.boolean, $.string_literal, $.integer),
          )),
          optional(','),  // Trailing comma after sub-fields
        ),
        ',',  // Trailing comma only (no sub-fields): Caption = 'text',;
      ),
    )),

    // --- ML (Multilingual) value list ---
    // ENU='English', DEU='German'
    ml_value_list: $ => prec.right(seq(
      $.ml_value_pair,
      repeat(seq(',', $.ml_value_pair)),
      optional(seq(',', $.locked_keyword, '=', $.boolean))
    )),

    ml_value_pair: $ => seq(
      field('language', $._identifier_or_quoted),
      '=',
      field('value', $.string_literal)
    ),

    // --- CalcFormula values ---
    // sum("Ledger Entry".Amount where("No." = field("No.")))
    _calc_formula_expression: $ => choice(
      $.lookup_formula,
      $.aggregate_formula,
    ),

    lookup_formula: $ => seq(
      $.lookup_keyword,
      '(',
      field('target', $.calc_field_reference),
      optional($.where_clause),
      ')'
    ),

    aggregate_formula: $ => prec(15, seq(
      // Negated formulas (CalcFormula = -Sum(...)). The sign belongs to the
      // formula: as a sibling branch `seq('-', $.aggregate_formula)` under the
      // hidden `_calc_formula_expression`, the '-' landed as a direct child of
      // `property` and inherited the `value` field, so
      // children_by_field_name('value') returned ['-', aggregate_formula].
      optional('-'),
      field('function', alias($.identifier, $.aggregate_function)),
      '(',
      field('target', $.calc_field_reference),
      optional($.where_clause),
      ')'
    )),

    // Table.Field or "Table"."Field" or Namespace.Table."Field" reference used in CalcFormula
    calc_field_reference: $ => prec.left(seq(
      choice($._identifier_or_quoted, $.keyword_identifier),
      repeat(seq('.', choice($._identifier_or_quoted, $.keyword_identifier)))
    )),

    // WHERE(conditions) clause — shared by CalcFormula, TableRelation, etc.
    where_clause: $ => seq(
      $.where_keyword,
      '(',
      $.where_conditions,
      ')'
    ),

    where_conditions: $ => repeat1(choice(
      seq($.where_condition, optional(',')),
      $.preproc_conditional_where,
    )),

    preproc_conditional_where: $ => seq(
      $.preproc_if,
      repeat(seq($.where_condition, optional(','))),
      repeat(seq(
        $.preproc_elif,
        repeat(seq($.where_condition, optional(','))),
      )),
      optional(seq(
        $.preproc_else,
        repeat(seq($.where_condition, optional(','))),
      )),
      $.preproc_endif,
    ),

    where_condition: $ => seq(
      field('field', $._identifier_or_quoted),
      '=',
      choice(
        // field("No.") or field(upperlimit("Date Filter")) or field(filter(Totaling))
        seq(
          choice($.field_keyword, $.upperlimit_keyword),
          '(',
          choice(
            field('value', $._identifier_or_quoted),
            // field(filter(...)) — field with filter applied
            seq($.filter_keyword, '(', field('value', $._identifier_or_quoted), ')'),
            // field(upperlimit(...)) — field with upperlimit
            seq($.upperlimit_keyword, '(', choice(
              field('value', $._identifier_or_quoted),
              // upperlimit(filter(...)) — upperlimit with filter
              seq($.filter_keyword, '(', field('value', $._identifier_or_quoted), ')'),
            ), ')'),
          ),
          ')'
        ),
        // const(value) — also accepts keyword identifiers like Report, Page, Codeunit, Action
        seq($.const_keyword, '(', optional(field('value', choice(
          $.string_literal, $.identifier, $.quoted_identifier, $.integer, $.boolean,
          $.database_reference, $.qualified_enum_value, $.keyword_identifier,
          $.datetime_literal, $.date_literal, $.time_literal,
        ))), ')'),
        // filter(expression)
        seq($.filter_keyword, '(', field('value', $.filter_value), ')'),
      )
    ),

    // Filter values — simplified, allows comparison operators, ranges, etc.
    filter_value: $ => repeat1(choice(
      $.string_literal,
      $.identifier,
      $.quoted_identifier,
      $.integer,
      $.decimal,
      $.boolean,               // true/false in filters
      $.date_literal,          // 0D, 20200101D
      $.time_literal,          // 0T, 120000T
      $.datetime_literal,      // 0DT
      $.biginteger_literal,    // 1000L
      $.qualified_enum_value,  // Enum::Value references
      $.database_reference,    // Report::"Name", Page::"Name", etc.
      $.keyword_identifier,    // Keywords used as filter values (Page, Codeunit, etc.)
      '..',  // Range operator
      seq('-', $.integer),     // Negative integer: -1, -100
      '-',   // Negation sign (standalone)
      $.filter_operator,
    )),

    // AL filter operators: <> | = > < >= <= & @ * %, in any run.
    //
    // Named, not an inline token(). As an inline token(PATTERN) it was an
    // anonymous hidden symbol, so `Type = const(Item) & "No." <> ''` covered the
    // bytes of `&` and `<>` with no node — 890 occurrences across BC.History,
    // 354 of them the bare `|` alternation. The pattern is a run, so two
    // adjacent operators separated only by whitespace surfaced as one gap
    // ("& <>"), which is why the cluster list read like a set of compound
    // operators that do not exist in AL.
    //
    // Same shape as assignment_operator and permission_type: a named rule whose
    // whole body is one token collapses INTO that token, giving a visible
    // childless leaf that covers its own bytes. This is deliberately NOT
    // comparison_operator — that rule is a choice of string literals for
    // *expression* comparison, already visible, and its members are single
    // operators rather than the runs a filter allows.
    filter_operator: $ => token(prec(-1, /[<>=|&@*%]+/)),

    // --- Sorting/SourceTableView value ---
    // sorting("Starting Date") order(ascending) where("Status" = const(Active))
    sorting_value: $ => prec(5, seq(
      $.sorting_keyword,
      '(',
      $._identifier_or_quoted,
      repeat(seq(',', $._identifier_or_quoted)),
      ')',
      optional(seq(
        $.order_keyword,
        '(',
        choice($.ascending_keyword, $.descending_keyword),
        ')',
      )),
      optional($.where_clause),
    )),

    // --- Link value list ---
    // "Field" = field(OtherField), "Field2" = const(Value)
    // Used by SubPageLink, SubPageView, DataItemLink, etc.
    link_value_list: $ => prec.left(6, repeat1(choice(
      seq($.link_value, optional(',')),
      $.preproc_conditional_link_values,
    ))),

    preproc_conditional_link_values: $ => seq(
      $.preproc_if,
      repeat(seq($.link_value, optional(','))),
      repeat(seq(
        $.preproc_elif,
        repeat(seq($.link_value, optional(','))),
      )),
      optional(seq(
        $.preproc_else,
        repeat(seq($.link_value, optional(','))),
      )),
      $.preproc_endif,
    ),

    link_value: $ => seq(
      field('field', $._identifier_or_quoted),
      '=',
      choice(
        // --- Structured link forms -------------------------------------------
        // field()/const()/filter()/upperlimit() and the dotted DataItem.Field
        // reference are unambiguously link syntax. A one-entry list is still a
        // complete `A = B` expression though, so property_expression ->
        // comparison_expression parses it too; the tie survives to a GLR
        // ambiguity, where static prec does not apply and the arbitrary
        // symbol-id tiebreak used to hand every single-entry DataItemLink /
        // RunPageLink / SubPageLink / ColumnFilter to property_expression.
        // prec.dynamic settles it in favour of the link reading so one query
        // on link_value finds every link site, not just the comma-separated
        // ones. Two-or-more entries were never ambiguous — the comma already
        // rules property_expression out — so this only moves the single-entry
        // trees.
        prec.dynamic(1, choice(
          seq(
            choice($.field_keyword, $.upperlimit_keyword),
            '(',
            choice(
              field('value', $._identifier_or_quoted),
              seq($.filter_keyword, '(', field('value', $._identifier_or_quoted), ')'),
              seq($.upperlimit_keyword, '(', choice(
                field('value', $._identifier_or_quoted),
                seq($.filter_keyword, '(', field('value', $._identifier_or_quoted), ')'),
              ), ')'),
            ),
            ')'
          ),
          seq($.const_keyword, '(', optional(field('value', choice(
            $.string_literal, $.identifier, $.quoted_identifier, $.integer, $.boolean,
            $.database_reference, $.qualified_enum_value, $.keyword_identifier,
            $.datetime_literal, $.date_literal, $.time_literal,
          ))), ')'),
          seq($.filter_keyword, '(', field('value', $.filter_value), ')'),
          // Direct reference: DataItem.FieldName (used in query DataItemLink).
          // Each identifier carries its own field; wrapping the seq put the
          // anonymous '.' inside the value field's declared type set.
          prec(3, seq(
            field('value', $._identifier_or_quoted),
            '.',
            field('value', $._identifier_or_quoted)
          )),
        )),
        // --- Bare value: Field = "Value" or Field = Value ---------------------
        // Deliberately NOT dynamic-boosted. A single `Prop = A = B` with a bare
        // right-hand side is never a link in practice — it is Implementation /
        // DefaultImplementation / UnknownValueImplementation syntax (which wants
        // implementation_value_list) or an ordinary boolean property expression
        // such as `Visible = HideActions = false`. Leaving this branch at
        // dynamic 0 keeps all of those trees exactly as they are.
        field('value', prec(-1, $._identifier_or_quoted)),
      )
    ),

    // --- TableRelation value ---
    // Customer where("No." = field("Customer No."))
    // if("Type" = const(Item)) Item else Resource
    table_relation_value: $ => prec.right(5, choice(
      $.table_relation_expression,
      $.preproc_conditional_table_relation,
    )),

    // Preprocessor conditionals inside TableRelation value
    preproc_conditional_table_relation: $ => seq(
      $.preproc_if,
      optional($._tr_branch),
      repeat(seq($.preproc_elif, optional($._tr_branch))),
      optional(seq($.preproc_else, optional($._tr_branch))),
      $.preproc_endif,
    ),

    // One #if/#elif/#else branch of a TableRelation conditional
    _tr_branch: $ => seq(
      $._table_relation_branch_content,
      optional(';'),
    ),

    // Branch content inside preproc_conditional_table_relation.
    // Can be a full table_relation_expression OR an else-continuation fragment
    // (e.g. 'else if (Type = const("Alloc")) "Table"' which is the tail of an
    // if_table_relation chain whose head is outside the #if block).
    _table_relation_branch_content: $ => choice(
      $.table_relation_expression,
      $.else_table_relation_fragment,
    ),

    // Fragment for 'else <table_relation_expression>' inside a preproc branch.
    // Used when the preceding if-chain ends before the #if and this branch continues it.
    else_table_relation_fragment: $ => prec.right(15, seq(
      $.else_keyword,
      field('else_relation', $.table_relation_expression),
    )),

    table_relation_expression: $ => choice(
      $.simple_table_relation,
      $.if_table_relation,
      $.preproc_conditional_table_relation,
    ),

    if_table_relation: $ => prec.right(15, seq(
      $.if_keyword,
      '(',
      $.where_conditions,
      ')',
      field('then_relation', $.simple_table_relation),
      optional(seq(
        $.else_keyword,
        field('else_relation', $.table_relation_expression)
      ))
    )),

    simple_table_relation: $ => prec.right(20, seq(
      choice($._namespaced_ref_table, field('table', $.member_expression)),
      optional(prec(25, $.where_clause))
    )),

    // --- Permissions value list ---
    // tabledata Customer = R, tabledata "Sales Header" = RIMD
    // Permission list that allows preprocessor conditionals between items
    // Items separated by commas, with preproc blocks interleaved
    tabledata_permission_list: $ => repeat1(choice(
      seq($.tabledata_permission, optional(',')),
      $.preproc_conditional_permissions,
    )),

    // Preprocessor conditionals inside permission lists
    // Comma may appear inside #if when wrapping trailing entries
    // Semicolon may also appear when the property's terminating ; is inside the #if block
    preproc_conditional_permissions: $ => seq(
      $.preproc_if,
      optional($._permission_branch),
      repeat(seq($.preproc_elif, optional($._permission_branch))),
      optional(seq($.preproc_else, optional($._permission_branch))),
      $.preproc_endif,
    ),

    // One non-empty #if/#elif/#else branch of a permission list:
    // [,] item*  — the leading comma or at least one item.
    _permission_branch: $ => choice(
      seq(',', repeat($._permission_item)),
      repeat1($._permission_item),
    ),

    _permission_item: $ => choice(
      seq($.tabledata_permission, optional(choice(',', ';'))),
      $.preproc_conditional_permissions,
    ),

    // Visible since the losslessness pass. It was `_tabledata_keyword`, a hidden
    // rule over a bare kw(), and was the largest single byte-gap cluster left
    // after the type keywords: 23,481 occurrences across BC.History where
    //   Permissions = tabledata Customer = R, table Customer = X;
    // covered the bytes spelling `table` with `table_keyword -> "table"` and the
    // bytes spelling `tabledata` with nothing at all.
    //
    // ONE rule, referenced from both sites, is what keeps that safe. It is also
    // reached via the `alias(..., $.identifier)` route in `option_member` below,
    // so `OptionMembers = TableData,...` — where bare unquoted `TableData`
    // case-insensitively collides with this exact keyword — resolves as a plain
    // identifier option member instead of erroring (previously: ERROR,
    // first-position-only; the same `tabledata_permission`/`option_member`
    // ambiguity that `table_keyword` settles via `keyword_as_identifier`).
    // Splitting this into a visible rule here plus a second bare kw() there would
    // reintroduce that collision: both spellings are the same terminal, so two
    // rules over it put two competing reductions in one state. Aliasing the
    // named rule to $.identifier keeps the option-member node an `identifier`,
    // as before, and merely gives it the anonymous "tabledata" child.
    tabledata_keyword: $ => alias(kw('tabledata'), 'tabledata'),

    tabledata_permission: $ => seq(
      choice(
        $.tabledata_keyword,
        $.table_keyword,
        $.codeunit_keyword,
        $.page_keyword,
        $.report_keyword,
        $.query_keyword,
        $.xmlport_keyword,
        // Must be the SAME `system_keyword` rule that `keyword_identifier` uses,
        // not a bare kw(). Both rules are reachable from a property value, so
        // with one side named and the other bare the parser has to decide which
        // rule owns the token before it can see the `*`/name that disambiguates,
        // and `tree-sitter generate` fails with an unresolved conflict between
        // `tabledata_permission` and `system_keyword`. Routing both through the
        // one rule removes the choice instead of forking on it.
        //
        // It also gives `system` a node here, which it did not have before —
        // the same leaf gap `tabledata_keyword` carried until the losslessness
        // pass closed it, one entry above.
        $.system_keyword,
      ),
      // '*' keeps the field: the wildcard IS the table name, so an anonymous
      // node in this field's type set is correct here (cf. operator fields).
      choice($._namespaced_ref_table_name, field('table_name', '*')),
      '=',
      field('permission', $.permission_type)
    ),

    permission_type: $ => token(prec(-1, new RustRegex('[rRiImMdDxX]+'))),

    // --- OrderBy value list ---
    // ascending("No.", Name)
    order_by_list: $ => prec.left(5, seq(
      $.order_by_item,
      repeat(seq(',', $.order_by_item))
    )),

    order_by_item: $ => seq(
      choice($.ascending_keyword, $.descending_keyword),
      '(',
      $._identifier_or_quoted,
      repeat(seq(',', $._identifier_or_quoted)),
      ')'
    ),

    // --- Implementation value list ---
    // "My Interface" = "My Codeunit"
    implementation_value_list: $ => prec.left(repeat1(choice(
      seq($.implementation_value, optional(',')),
      $.preproc_conditional_impl_values,
    ))),

    preproc_conditional_impl_values: $ => seq(
      $.preproc_if,
      repeat(seq($.implementation_value, optional(','))),
      repeat(seq(
        $.preproc_elif,
        repeat(seq($.implementation_value, optional(','))),
      )),
      optional(seq(
        $.preproc_else,
        repeat(seq($.implementation_value, optional(','))),
      )),
      $.preproc_endif,
    ),

    implementation_value: $ => seq(
      field('interface', $._identifier_or_quoted),
      '=',
      field('implementation', $._identifier_or_quoted)
    ),

    // --- OptionMembers value list ---
    // Option1, Option2, "Option 3"
    // Also supports leading/trailing commas for blank entries: ,Sale,"Total Sale"
    option_member_list: $ => prec.right(choice(
      // Standard: Member, Member, ... (also supports empty slots: Member,,Member)
      // A #if/#endif may wrap comma-terminated members (BC gates legacy
      // IncludedPermissionSets entries behind `#if not CLEANxx`). The preproc
      // block is gated behind a comma so a bare `value #if` (next property
      // guarded) does NOT fork the single-value case.
      seq(
        $.option_member,
        repeat(seq(
          ',',
          choice(
            optional($.option_member),
            seq($.preproc_conditional_option_members, optional($.option_member))
          )
        ))
      ),
      // With leading commas (blank entries): ,,,Member,Member
      // Used by OptionMembers property and Option type: ,Sale,"Total Sale"
      seq(
        repeat1(','),
        optional(seq(
          $.option_member,
          repeat(seq(',', optional($.option_member)))
        ))
      ),
    )),

    // #if/#endif wrapping comma-terminated option members inside a list value
    // (e.g. IncludedPermissionSets entries gated by `#if not CLEANxx`). Each
    // wrapped member keeps its trailing comma so the list continues cleanly.
    preproc_conditional_option_members: $ => seq(
      $.preproc_if,
      repeat(seq($.option_member, ',')),
      optional($.option_member),
      repeat(seq(
        $.preproc_elif,
        repeat(seq($.option_member, ',')),
        optional($.option_member),
      )),
      optional(seq(
        $.preproc_else,
        repeat(seq($.option_member, ',')),
        optional($.option_member),
      )),
      $.preproc_endif,
    ),

    option_member: $ => choice(
      $.identifier,
      $.quoted_identifier,
      $.string_literal,
      $.integer,             // Numeric option members (ValuesAllowed = 0, None, Partial)
      seq('-', $.integer),   // Negative integer option members (ValuesAllowed = -1)
      $.keyword_identifier,  // System, Action, etc.
      alias($.keyword_as_identifier, $.identifier),  // Type, Field, etc.
      alias($.tabledata_keyword, $.identifier),  // TableData (first-position collision fix)
      $.local_keyword,       // 'Local' as option member
      $.internal_keyword,    // 'Internal' as option member
      $.protected_keyword,   // 'Protected' as option member
      $.boolean,             // true/false as option member
    ),

    // =====================================================================
    // Table internals
    // =====================================================================

    // --- Fields section ---
    // fields { field(1; "No."; Code[20]) { } }
    fields_section: $ => seq(
      $.fields_keyword,
      '{',
      optional(field('body', $.fields_body)),
      '}'
    ),
    fields_body: $ => repeat1(choice(
      $.field_declaration,
      $.attribute_item,
      $.preproc_conditional_fields,
      $.preproc_split_table_field,
      // Extension modifications inside fields section
      $.modify_modification,
    )),

    preproc_conditional_fields: $ => seq(
      $.preproc_if,
      repeat(choice($.field_declaration, $.attribute_item, $.modify_modification)),
      repeat(seq(
        $.preproc_elif,
        repeat(choice($.field_declaration, $.attribute_item, $.modify_modification)),
      )),
      optional(seq(
        $.preproc_else,
        repeat(choice($.field_declaration, $.attribute_item, $.modify_modification)),
      )),
      $.preproc_endif,
    ),

    field_declaration: $ => seq(
      $.field_keyword,
      '(',
      field('id', $.integer),
      ';',
      field('name', $._identifier_or_quoted),
      ';',
      field('type', $.type_specification),
      ')',
      // A pragma-only #if/#endif may sit between the field header and its body
      // (Microsoft BC wraps `#pragma warning disable/restore ASxxxx` in
      // `#if not CLEANxx`/`#endif`). It only attaches here when a `{` body
      // follows, so an #if-wrapped sibling field stays at section level.
      // Zero preproc → repeat matches nothing → tree is byte-identical.
      optional(seq(
        repeat($.preproc_pragma_only),
        '{',
        optional(field('body', $.declaration_body)),
        '}'
      ))
    ),

    // --- Keys section ---
    // keys { key(PK; "No.") { Clustered = true; } }
    keys_section: $ => seq(
      $.keys_keyword,
      '{',
      optional(field('body', $.keys_body)),
      '}'
    ),
    keys_body: $ => repeat1(choice(
      $.key_declaration,
      $.attribute_item,
      $.preproc_conditional_keys,
    )),

    preproc_conditional_keys: $ => seq(
      $.preproc_if,
      repeat(choice($.key_declaration, $.attribute_item)),
      repeat(seq($.preproc_elif, repeat(choice($.key_declaration, $.attribute_item)))),
      optional(seq($.preproc_else, repeat(choice($.key_declaration, $.attribute_item)))),
      $.preproc_endif,
    ),

    key_declaration: $ => seq(
      $.key_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ';',
      field('fields', $.field_list),
      ')',
      optional(seq(
        '{',
        optional(field('body', $.declaration_body)),
        '}'
      ))
    ),

    // Comma-separated list of field names
    field_list: $ => seq(
      $._identifier_or_quoted,
      repeat(seq(',', $._identifier_or_quoted))
    ),

    // --- Fieldgroups section ---
    // fieldgroups { fieldgroup(DropDown; "No.", Name) { } }
    fieldgroups_section: $ => seq(
      $.fieldgroups_keyword,
      '{',
      optional(field('body', $.fieldgroups_body)),
      '}'
    ),
    fieldgroups_body: $ => repeat1(choice(
      $.fieldgroup_declaration,
      $.preproc_conditional_fieldgroups,
      // Extension modifications for fieldgroups
      $.addlast_fieldgroup_modification,
      $.addfirst_fieldgroup_modification,
    )),

    addlast_fieldgroup_modification: $ => seq(
      $.addlast_keyword, '(', field('target', $._identifier_or_quoted), ';',
      field('fields', $.field_list), ')',
      optional(seq('{', '}'))
    ),

    addfirst_fieldgroup_modification: $ => seq(
      $.addfirst_keyword, '(', field('target', $._identifier_or_quoted), ';',
      field('fields', $.field_list), ')',
      optional(seq('{', '}'))
    ),

    preproc_conditional_fieldgroups: $ => seq(
      $.preproc_if,
      repeat(choice($.fieldgroup_declaration, $.preproc_conditional_fieldgroups)),
      repeat(seq($.preproc_elif, repeat(choice($.fieldgroup_declaration, $.preproc_conditional_fieldgroups)))),
      optional(seq($.preproc_else, repeat(choice($.fieldgroup_declaration, $.preproc_conditional_fieldgroups)))),
      $.preproc_endif,
    ),

    fieldgroup_declaration: $ => seq(
      $.fieldgroup_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ';',
      field('fields', $.field_list),
      ')',
      optional(seq(
        '{',
        optional(field('body', $.declaration_body)),
        '}'
      ))
    ),

    // =====================================================================
    // Type system
    // =====================================================================

    type_specification: $ => choice(
      prec(2, $.array_type),
      prec(2, $.list_type),
      prec(2, $.dictionary_type),
      prec(1, $.text_type),
      prec(1, $.code_type),
      $.option_type,
      $.record_type,
      $.dotnet_type,
      $.object_reference_type,  // Codeunit, Page, Report, Query, Xmlport, Enum, Interface
      $.basic_type,
      $.identifier,             // Fallback for unknown types (HttpClient, DotNet, etc.)
      $.quoted_identifier,      // Quoted type references
    ),

    // Text[100] or plain Text
    text_type: $ => choice(
      prec(11, seq($.text_keyword, '[', field('length', $.integer), ']')),
      prec(10, $.text_keyword)
    ),

    // Code[20] or plain Code
    code_type: $ => choice(
      prec(11, seq($.code_keyword, '[', field('length', $.integer), ']')),
      prec(10, $.code_keyword)
    ),

    // Option with optional member list: Option OptionA, OptionB
    // Supports leading commas: Option ,,,,"Page","Query"
    option_type: $ => prec.right(1, seq(
      $.option_keyword,
      optional($.option_member_list)
    )),

    // Record "Customer" or Record Customer or Record 2000000041 [temporary]
    // Also: Record System.Reflection.Field temporary
    record_type: $ => prec.right(seq(
      prec(1, $.record_keyword),
      $._namespaced_ref_reference,
      optional($.temporary_keyword)
    )),

    // DotNet "System.Text.StringBuilder" or DotNet System.DateTime type reference
    dotnet_type: $ => prec.right(seq(
      $.dotnet_keyword,
      choice(
        field('reference', $.string_literal),
        $._namespaced_ref_reference,
      )
    )),

    // Object reference types: Codeunit "Sales-Post", Page "Customer Card", etc.
    // Also supports namespaced: Codeunit System.Environment."Client Type Management"
    object_reference_type: $ => prec.right(seq(
      field('object_type', choice(
        $.codeunit_keyword,
        $.page_keyword,
        $.report_keyword,
        $.query_keyword,
        $.xmlport_keyword,
        $.enum_keyword,
        $.interface_keyword,
        $.testpage_keyword,
        $.testrequestpage_keyword,
        $.controladdin_keyword,
      )),
      $._namespaced_ref_reference
    )),

    // Handles: "Name", Name, Namespace.Name, Namespace."Name", etc.
    // Unfielded form — used where the reference carries no field of its own.
    _namespaced_or_simple_ref: $ => choice(
      $.integer,
      prec.right(seq(
        $._identifier_or_quoted,
        repeat(seq('.', $._identifier_or_quoted))
      )),
    ),

    // Fielded forms of the above — one per distinct field name. Each name part
    // carries the field individually so the separating '.' does not.
    _namespaced_ref_reference: $ => namespacedRefFielded($, 'reference'),
    _namespaced_ref_table: $ => namespacedRefFielded($, 'table'),
    _namespaced_ref_table_name: $ => namespacedRefFielded($, 'table_name'),

    // array[10] of Integer, array[10,20] of Text[100]
    //
    // Each size carries its OWN field('sizes', …). Wrapping the whole
    // comma-separated seq in one field puts the anonymous ',' inside the field,
    // so children_by_field_name('sizes') yields 10, ',', 20 — the same shape
    // that made the owned-IR lowerer panic on case patterns.
    array_type: $ => seq(
      prec(1, $.array_keyword),
      '[',
      field('sizes', $.integer),
      repeat(seq(',', field('sizes', $.integer))),
      ']',
      $.of_keyword,
      field('element_type', $.type_specification)
    ),

    // List of [Integer]
    list_type: $ => seq(
      $.list_keyword,
      $.of_keyword,
      '[',
      field('element_type', $.type_specification),
      ']'
    ),

    // Dictionary of [Text, Integer]
    dictionary_type: $ => seq(
      $.dictionary_keyword,
      $.of_keyword,
      '[',
      field('key_type', $.type_specification),
      ',',
      field('value_type', $.type_specification),
      ']'
    ),

    // Common built-in types
    //
    // These ~50 bare kw()s are the largest remaining block of bare kw() in the
    // grammar, and they were CONSIDERED and deliberately left alone by the
    // losslessness pass. They are already lossless, for a reason worth knowing
    // before "fixing" them: a named rule whose body is a choice() of hidden
    // tokens has no visible child, so the `basic_type` node is ITSELF the
    // childless leaf covering the bytes. `Integer` is `(basic_type)` with text
    // `Integer` — nothing is dropped, and the byte-gap detector never flagged
    // one of them across all 15,358 BC.History files.
    //
    // record_type, code_type, text_type, option_type, array_type, list_type and
    // dictionary_type could NOT use this pattern, which is why they got keyword
    // rules instead: each has real children (a length, an element type, a
    // reference), so the enclosing node is not a leaf and the keyword's bytes
    // fall between leaves. That is the whole distinction.
    //
    // Routing these 50 through keyword rules would move every type node in the
    // corpus and buy nothing. `boolean`, `keyword_identifier` and
    // `keyword_as_identifier` are lossless by the same argument.
    basic_type: $ => choice(
      // Numeric
      prec(1, kw('integer')),
      prec(1, kw('biginteger')),
      prec(1, kw('decimal')),
      prec(1, kw('byte')),
      // Text
      prec(1, kw('char')),
      prec(10, kw('label')),
      prec(1, kw('textbuilder')),
      prec(1, kw('textconst')),
      // Date/Time
      prec(1, kw('date')),
      prec(1, kw('time')),
      prec(1, kw('datetime')),
      prec(1, kw('duration')),
      kw('dateformula'),
      // Core
      prec(1, kw('boolean')),
      prec(1, kw('guid')),
      prec(1, kw('blob')),
      prec(1, kw('recordid')),
      prec(1, kw('recordref')),
      prec(1, kw('fieldref')),
      prec(1, kw('variant')),
      prec(1, kw('dialog')),
      prec(1, kw('action')),
      prec(1, kw('secrettext')),
      // JSON
      prec(1, kw('jsontoken')),
      prec(1, kw('jsonvalue')),
      prec(1, kw('jsonarray')),
      prec(1, kw('jsonobject')),
      // Media
      prec(1, kw('media')),
      prec(1, kw('mediaset')),
      // Stream
      prec(1, kw('instream')),
      prec(1, kw('outstream')),
      // HTTP
      prec(1, kw('httpclient')),
      prec(1, kw('httpcontent')),
      prec(1, kw('httpheaders')),
      prec(1, kw('httprequestmessage')),
      prec(1, kw('httpresponsemessage')),
      // Notification
      prec(1, kw('notification')),
      // Filter/Table
      prec(1, kw('filterpagebuilder')),
      prec(1, kw('tablefilter')),
      prec(1, kw('tableconnectiontype')),
      // XML
      prec(1, kw('xmldocument')),
      prec(1, kw('xmlelement')),
      prec(1, kw('xmlnode')),
      prec(1, kw('xmlnodelist')),
      prec(1, kw('xmlattribute')),
      // Error/Session
      prec(1, kw('errorinfo')),
      prec(1, kw('sessionsettings')),
      // File
      prec(1, kw('file')),
      prec(1, kw('fileupload')),
      // Other common types
      prec(1, kw('moduleinfo')),
      prec(1, kw('verbosity')),
      prec(1, kw('datatransfer')),
      prec(1, kw('version')),
      // Web
      prec(1, kw('webserviceactioncontext')),
    ),

    // =====================================================================
    // Enum values
    // =====================================================================

    // value(0; "None") { Caption = 'None'; }
    enum_value_declaration: $ => seq(
      $.value_keyword,
      '(',
      field('value_id', $.integer),
      ';',
      field('value_name', choice($._identifier_or_quoted, $.string_literal)),
      ')',
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    ),

    // =====================================================================
    // Labels section (report labels)
    // =====================================================================

    labels_section: $ => seq(
      $.labels_keyword,
      '{',
      optional(field('body', $.labels_body)),
      '}'
    ),
    labels_body: $ => repeat1(choice($.label_declaration, $.preproc_conditional_labels)),

    // Report `labels { }` with label(s) wrapped in #if/#endif (BC gates legacy
    // labels behind `#if not CLEANxx`). Mirrors preproc_conditional_fields.
    preproc_conditional_labels: $ => seq(
      $.preproc_if,
      repeat($.label_declaration),
      repeat(seq($.preproc_elif, repeat($.label_declaration))),
      optional(seq($.preproc_else, repeat($.label_declaration))),
      $.preproc_endif,
    ),

    // name = 'value', Locked = true, Comment = 'text';
    label_declaration: $ => seq(
      field('name', $.identifier),
      '=',
      field('value', choice($.string_literal, $.verbatim_string)),
      repeat(seq(
        ',',
        choice(
          seq($.comment_keyword, '=', field('comment', $.string_literal)),
          seq($.locked_keyword, '=', field('locked', $.boolean)),
          seq($.maxlength_keyword, '=', field('maxlength', $.integer)),
        )
      )),
      ';'
    ),

    // =====================================================================
    // Page layout structure
    // =====================================================================

    layout_section: $ => seq(
      $.layout_keyword,
      '{',
      optional(field('body', $.layout_body)),
      '}'
    ),
    layout_body: $ => repeat1($._layout_element),
    // Shared body for layout containers (group/repeater/cuegroup/fixed/grid):
    // they accept properties, nested layout elements, and mixed preproc blocks.
    layout_container_body: $ => repeat1(choice(
      $._body_element,
      $._layout_element,
      $.preproc_conditional_layout_mixed,
    )),

    _layout_element: $ => choice(
      $.area_section,
      $.group_section,
      $.repeater_section,
      $.cuegroup_section,
      $.fixed_section,
      $.grid_section,
      $.page_field,
      $.part_section,
      $.systempart_section,
      $.usercontrol_section,
      $.label_section,
      // Preprocessor in layout
      $.preproc_conditional_layout,
      $.preproc_split_field,
      // Extension layout modifications
      $.addfirst_modification,
      $.addlast_modification,
      $.addafter_modification,
      $.addbefore_modification,
      $.modify_modification,
      $.movefirst_modification,
      $.movelast_modification,
      $.moveafter_modification,
      $.movebefore_modification,
    ),

    // area(Content) { ... }
    area_section: $ => seq(
      $.area_keyword,
      '(',
      field('type', choice(
        $.content_keyword,
        $.factboxes_keyword,
        $.processing_keyword,
        $.rolecenter_keyword,
        $.prompting_keyword,
        $.prompt_keyword,
        $.promptoptions_keyword,
        $.systemactions_keyword,
        $.identifier,  // Fallback for future area types
      )),
      ')',
      '{',
      optional(field('body', $.layout_body)),
      choice(
        '}',
        // Split closing brace: } inside both #if and #else branches
        $.preproc_split_brace_close,
        // Split closing brace: } inside #if only (no #else)
        $.preproc_split_brace_close_if_only,
      )
    ),

    // Split closing brace: #if content } #else content } #endif
    // Used when a section's closing } differs across preprocessor branches.
    preproc_split_brace_close: $ => prec(25, seq(
      $.preproc_if,
      repeat($._layout_element),
      '}',
      $.preproc_else,
      repeat($._layout_element),
      '}',
      $.preproc_endif,
    )),

    // Split closing brace (if-only): #if content } #endif  (no #else branch)
    // Used when a section's closing } is inside a #if with no #else.
    preproc_split_brace_close_if_only: $ => prec(25, seq(
      $.preproc_if,
      repeat($._layout_element),
      '}',
      $.preproc_endif,
    )),

    // group(General) { ... }
    group_section: $ => seq(
      $.group_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.layout_container_body)),
      '}'
    ),

    // repeater(Lines) { ... }
    repeater_section: $ => seq(
      $.repeater_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.layout_container_body)),
      '}'
    ),

    // cuegroup(Cues) { ... }
    cuegroup_section: $ => seq(
      $.cuegroup_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.layout_container_body)),
      '}'
    ),

    // fixed(Fixed) { ... }
    fixed_section: $ => seq(
      $.fixed_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.layout_container_body)),
      '}'
    ),

    // grid(Grid) { ... }
    grid_section: $ => seq(
      $.grid_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.layout_container_body)),
      '}'
    ),

    // Page field: field(Name; SourceExpr) { }
    // Different from table field — no ID, no type, uses source expression
    page_field: $ => seq(
      $.field_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ';',
      field('source', $._field_source),
      ')',
      optional(seq(
        '{',
        optional(field('body', $.declaration_body)),
        '}'
      ))
    ),

    // Source expression for page fields — uses full expression grammar
    _field_source: $ => $._expression,

    // part(PartName; PageName) { }
    part_section: $ => seq(
      $.part_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ';',
      field('source', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    ),

    // systempart(Links; "Record Link") { }
    systempart_section: $ => seq(
      $.systempart_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ';',
      field('source', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    ),

    // usercontrol(ControlName; ControlAddinName) { }
    usercontrol_section: $ => seq(
      $.usercontrol_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ';',
      field('source', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    ),

    // Preprocessor-split page field: #if field(...) #else field(...) #endif { props }
    preproc_split_field: $ => prec(25, seq(
      $.preproc_if,
      $._field_header,
      repeat(seq($.preproc_elif, $._field_header)),
      optional(seq($.preproc_else, $._field_header)),
      $.preproc_endif,
      optional(seq('{', optional(field('body', $.declaration_body)), '}'))
    )),

    // Table field split: #if field(id; name; type) #else field(id; name; type) #endif { }
    preproc_split_table_field: $ => prec(25, seq(
      $.preproc_if,
      $._table_field_header,
      repeat(seq($.preproc_elif, $._table_field_header)),
      optional(seq($.preproc_else, $._table_field_header)),
      $.preproc_endif,
      optional(seq('{', optional(field('body', $.declaration_body)), '}'))
    )),

    // Page field header: field(Name; SourceExpression) — used in preproc_split_field
    _field_header: $ => seq(
      $.field_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ';',
      field('source', $._field_source),
      ')',
    ),

    // Table field header: field(id; name; type) — used in preproc_split_table_field
    _table_field_header: $ => seq(
      $.field_keyword,
      '(',
      field('id', $.integer),
      ';',
      field('name', $._identifier_or_quoted),
      ';',
      field('type', $.type_specification),
      ')',
    ),

    // label(LabelName) { ... } — page label (not report label)
    label_section: $ => seq(
      $.label_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    ),

    // =====================================================================
    // Extension layout modifications
    // =====================================================================

    // addfirst(AreaName) { field(...) { } }
    addfirst_modification: $ => seq(
      $.addfirst_keyword,
      '(',
      field('target', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.layout_body)),
      choice(
        '}',
        $.preproc_split_brace_close,
        $.preproc_split_brace_close_if_only,
      )
    ),

    addlast_modification: $ => seq(
      $.addlast_keyword,
      '(',
      field('target', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.layout_body)),
      choice(
        '}',
        $.preproc_split_brace_close,
        $.preproc_split_brace_close_if_only,
      )
    ),

    addafter_modification: $ => seq(
      $.addafter_keyword,
      '(',
      field('target', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.layout_body)),
      choice(
        '}',
        $.preproc_split_brace_close,
        $.preproc_split_brace_close_if_only,
      )
    ),

    addbefore_modification: $ => seq(
      $.addbefore_keyword,
      '(',
      field('target', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.layout_body)),
      choice(
        '}',
        $.preproc_split_brace_close,
        $.preproc_split_brace_close_if_only,
      )
    ),

    // modify("Name") { Visible = false; }
    modify_modification: $ => prec(2, seq(
      $.modify_keyword,
      '(',
      field('target', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    )),

    // movefirst(Content; "No.")
    movefirst_modification: $ => seq(
      $.movefirst_keyword,
      '(',
      field('target', $._identifier_or_quoted),
      ';',
      field('element', $._identifier_or_quoted),
      ')'
    ),

    movelast_modification: $ => seq(
      $.movelast_keyword,
      '(',
      field('target', $._identifier_or_quoted),
      ';',
      field('element', $._identifier_or_quoted),
      ')'
    ),

    moveafter_modification: $ => seq(
      $.moveafter_keyword,
      '(',
      field('target', $._identifier_or_quoted),
      ';',
      field('element', $._identifier_or_quoted),
      ')'
    ),

    movebefore_modification: $ => seq(
      $.movebefore_keyword,
      '(',
      field('target', $._identifier_or_quoted),
      ';',
      field('element', $._identifier_or_quoted),
      ')'
    ),

    // =====================================================================
    // Actions structure
    // =====================================================================

    actions_section: $ => seq(
      $.actions_keyword,
      '{',
      optional(field('body', $.action_body)),
      '}'
    ),
    action_body: $ => repeat1($._action_element),

    _action_element: $ => choice(
      $.action_area_section,
      $.action_group_section,
      $.action_declaration,
      $.separator_action,
      $.actionref_declaration,
      $.systemaction_declaration,
      $.fileuploadaction_declaration,
      $.customaction_declaration,
      // Properties/triggers directly in action areas
      $.property,
      $.trigger_declaration,
      $.attribute_item,
      // Extension action modifications
      $.addfirst_action_modification,
      $.addlast_action_modification,
      $.addafter_action_modification,
      $.addbefore_action_modification,
      $.modify_action_modification,
      // Preprocessor in actions
      $.preproc_conditional_actions,
    ),

    // area(Processing) { ... }
    action_area_section: $ => seq(
      $.area_keyword,
      '(',
      field('type', choice(
        $.processing_keyword,
        $.reporting_keyword,
        $.navigation_keyword,
        $.creation_keyword,
        $.promoted_keyword,
        $.systemactions_keyword,
        $.sections_keyword,
        $.embedding_keyword,
        $.promptguide_keyword,
        $.prompting_keyword,
        $.identifier,  // Fallback
      )),
      ')',
      '{',
      optional(field('body', $.action_body)),
      '}'
    ),

    // group(ActionGroup) { ... }
    action_group_section: $ => seq(
      $.group_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.action_group_body)),
      '}'
    ),
    action_group_body: $ => repeat1(choice(
      $._action_element,
      $._body_element,
    )),

    // action(MyAction) { ... }
    action_declaration: $ => seq(
      $.action_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    ),

    // separator { } or separator(Name) { Caption = ''; IsHeader = true; }
    separator_action: $ => seq(
      $.separator_keyword,
      optional(seq('(', field('name', $._identifier_or_quoted), ')')),
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    ),

    // actionref(RefName; ActionName) { }
    actionref_declaration: $ => seq(
      $.actionref_keyword,
      '(',
      field('promoted_name', $._identifier_or_quoted),
      ';',
      field('action_name', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    ),

    // systemaction(Name) { }
    systemaction_declaration: $ => seq(
      $.systemaction_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    ),

    // fileuploadaction(Name) { }
    fileuploadaction_declaration: $ => seq(
      $.fileuploadaction_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    ),

    // customaction(Name) { }
    customaction_declaration: $ => seq(
      $.customaction_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    ),

    // =====================================================================
    // Extension action modifications
    // =====================================================================

    addfirst_action_modification: $ => seq(
      $.addfirst_keyword,
      '(',
      field('target', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.action_body)),
      '}'
    ),

    addlast_action_modification: $ => seq(
      $.addlast_keyword,
      '(',
      field('target', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.action_body)),
      '}'
    ),

    addafter_action_modification: $ => seq(
      $.addafter_keyword,
      '(',
      field('target', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.action_body)),
      '}'
    ),

    addbefore_action_modification: $ => seq(
      $.addbefore_keyword,
      '(',
      field('target', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.action_body)),
      '}'
    ),

    modify_action_modification: $ => prec(2, seq(
      $.modify_keyword,
      '(',
      field('target', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    )),

    // =====================================================================
    // Views section
    // =====================================================================

    // Page `analysisviews { analysisview("Name") { Caption=…; DefinitionFile=…; } }`
    analysisviews_section: $ => seq(
      $.analysisviews_keyword,
      '{',
      optional(field('body', $.analysisviews_body)),
      '}'
    ),
    analysisviews_body: $ => repeat1($.analysisview_declaration),

    analysisview_declaration: $ => seq(
      $.analysisview_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    ),

    views_section: $ => seq(
      $.views_keyword,
      '{',
      optional(field('body', $.views_body)),
      '}'
    ),
    views_body: $ => repeat1(choice(
      $.view_definition,
      // Extension modifications for views (with or without target)
      $.addfirst_modification,
      $.addlast_modification,
      $.addafter_modification,
      $.addbefore_modification,
      $.modify_modification,
      $.addfirst_views_modification,
      $.addlast_views_modification,
      $.addafter_views_modification,
      $.addbefore_views_modification,
    )),

    // Views extensions without target: addfirst { view(...) { } }
    addfirst_views_modification: $ => seq(
      $.addfirst_keyword,
      '{',
      optional(field('body', $.views_mod_body)),
      '}'
    ),

    addlast_views_modification: $ => seq(
      $.addlast_keyword,
      '{',
      optional(field('body', $.views_mod_body)),
      '}'
    ),

    // Views extensions with target: addafter(ViewName) { view(...) { } }
    addafter_views_modification: $ => seq(
      $.addafter_keyword,
      '(', field('target', $._identifier_or_quoted), ')',
      '{',
      optional(field('body', $.views_mod_body)),
      '}'
    ),

    addbefore_views_modification: $ => seq(
      $.addbefore_keyword,
      '(', field('target', $._identifier_or_quoted), ')',
      '{',
      optional(field('body', $.views_mod_body)),
      '}'
    ),

    views_mod_body: $ => repeat1($.view_definition),

    view_definition: $ => seq(
      $.view_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    ),

    // =====================================================================
    // Report sections
    // =====================================================================

    // dataset { dataitem(...) { column(...) { } } }
    dataset_section: $ => seq(
      $.dataset_keyword,
      '{',
      optional(field('body', $.dataset_body)),
      '}'
    ),
    dataset_body: $ => repeat1(choice(
      $.report_dataitem,
      $.attribute_item,
      $.preproc_conditional_dataset,
      // Extension modifications for dataset
      $.addfirst_dataset_modification,
      $.addlast_dataset_modification,
      $.addafter_dataset_modification,
      $.addbefore_dataset_modification,
      $.add_dataset_modification,
      $.modify_modification,
    )),

    // Preprocessor conditionals at dataset section level (around dataitems)
    preproc_conditional_dataset: $ => seq(
      $.preproc_if,
      repeat(choice($.report_dataitem, $.attribute_item)),
      repeat(seq($.preproc_elif, repeat(choice($.report_dataitem, $.attribute_item)))),
      optional(seq($.preproc_else, repeat(choice($.report_dataitem, $.attribute_item)))),
      $.preproc_endif,
    ),

    report_dataitem: $ => seq(
      $.dataitem_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ';',
      $._namespaced_ref_table_name,
      ')',
      '{',
      optional(field('body', $.report_body)),
      '}'
    ),
    report_body: $ => repeat1($._report_body_element),

    _report_body_element: $ => choice(
      $.report_column,
      $.report_dataitem,  // Nested dataitems
      $._body_element,
      $.preproc_conditional_report,
    ),

    preproc_conditional_report: $ => seq(
      $.preproc_if,
      repeat($._report_body_element),
      repeat(seq($.preproc_elif, repeat($._report_body_element))),
      optional(seq($.preproc_else, repeat($._report_body_element))),
      $.preproc_endif,
    ),

    report_column: $ => seq(
      $.column_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ';',
      field('source', $._field_source),
      ')',
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    ),

    // Extension dataset modifications
    add_dataset_modification: $ => seq(
      $.add_keyword, '(', field('target', $._identifier_or_quoted), ')',
      '{', optional(field('body', $.dataset_mod_body)), '}'
    ),
    addfirst_dataset_modification: $ => seq(
      $.addfirst_keyword,
      optional(seq('(', field('target', $._identifier_or_quoted), ')')),
      '{', optional(field('body', $.dataset_mod_body)), '}'
    ),
    addlast_dataset_modification: $ => seq(
      $.addlast_keyword, '(', field('target', $._identifier_or_quoted), ')',
      '{', optional(field('body', $.dataset_mod_body)), '}'
    ),
    addafter_dataset_modification: $ => seq(
      $.addafter_keyword, '(', field('target', $._identifier_or_quoted), ')',
      '{', optional(field('body', $.dataset_mod_body)), '}'
    ),
    addbefore_dataset_modification: $ => seq(
      $.addbefore_keyword, '(', field('target', $._identifier_or_quoted), ')',
      '{', optional(field('body', $.dataset_mod_body)), '}'
    ),
    dataset_mod_body: $ => repeat1(choice($.report_dataitem, $.report_column, $._body_element)),

    // requestpage { layout { ... } actions { ... } }
    requestpage_section: $ => seq(
      $.requestpage_keyword,
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    ),

    // rendering { layout(Name) { ... } }
    rendering_section: $ => seq(
      $.rendering_keyword,
      '{',
      optional(field('body', $.rendering_body)),
      '}'
    ),
    rendering_body: $ => repeat1(choice($.rendering_layout, $.preproc_conditional_rendering)),

    // A report `rendering` whose layout(s) are wrapped in #if/#endif (BC wraps
    // RDLC layouts in `#if not CLEANxx` as they are phased out). Mirrors
    // preproc_conditional_fields / preproc_conditional_keys.
    preproc_conditional_rendering: $ => seq(
      $.preproc_if,
      repeat($.rendering_layout),
      repeat(seq($.preproc_elif, repeat($.rendering_layout))),
      optional(seq($.preproc_else, repeat($.rendering_layout))),
      $.preproc_endif,
    ),

    rendering_layout: $ => seq(
      $.layout_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    ),

    // =====================================================================
    // Query sections
    // =====================================================================

    // elements { dataitem(...) { column(...) { } filter(...) { } } }
    elements_section: $ => seq(
      $.elements_keyword,
      '{',
      optional(field('body', $.elements_body)),
      '}'
    ),
    elements_body: $ => repeat1($.query_dataitem),

    query_dataitem: $ => seq(
      $.dataitem_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ';',
      $._namespaced_ref_table_name,
      ')',
      '{',
      optional(field('body', $.query_body)),
      '}'
    ),
    query_body: $ => repeat1($._query_body_element),

    _query_body_element: $ => choice(
      $.query_column,
      $.query_filter,
      $.query_dataitem,  // Nested dataitems
      $._body_element,
      $.preproc_conditional_query,
    ),

    preproc_conditional_query: $ => seq(
      $.preproc_if,
      repeat($._query_body_element),
      repeat(seq($.preproc_elif, repeat($._query_body_element))),
      optional(seq($.preproc_else, repeat($._query_body_element))),
      $.preproc_endif,
    ),

    query_column: $ => seq(
      $.column_keyword,
      '(',
      choice(
        // Standard: column(Name; FieldName)
        seq(
          field('name', $._identifier_or_quoted),
          ';',
          field('field_name', $._identifier_or_quoted)
        ),
        // Computed: column(Name)
        field('name', $._identifier_or_quoted)
      ),
      ')',
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    ),

    query_filter: $ => seq(
      $.filter_keyword,
      '(',
      field('name', $._identifier_or_quoted),
      ';',
      field('field_name', $._identifier_or_quoted),
      ')',
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    ),

    // =====================================================================
    // XMLport sections
    // =====================================================================

    // schema { tableelement(...) { fieldelement(...) { } } }
    schema_section: $ => seq(
      $.schema_keyword,
      '{',
      optional(field('body', $.schema_body)),
      '}'
    ),
    schema_body: $ => repeat1($.xmlport_element),

    // tableelement/fieldelement/textelement(Name; Source) { ... }
    xmlport_element: $ => seq(
      field('element_type', choice(
        $.tableelement_keyword,
        $.fieldelement_keyword,
        $.textelement_keyword,
      )),
      '(',
      field('name', $._identifier_or_quoted),
      optional(seq(
        ';',
        field('source', $._field_source)
      )),
      ')',
      '{',
      optional(field('body', $.xmlport_body)),
      '}'
    ),
    xmlport_body: $ => repeat1($._xmlport_body_element),

    _xmlport_body_element: $ => choice(
      $.xmlport_element,
      $.xmlport_attribute,
      $._body_element,
      $.preproc_conditional_xmlport,
    ),

    preproc_conditional_xmlport: $ => seq(
      $.preproc_if,
      repeat($._xmlport_body_element),
      repeat(seq($.preproc_elif, repeat($._xmlport_body_element))),
      optional(seq($.preproc_else, repeat($._xmlport_body_element))),
      $.preproc_endif,
    ),

    // fieldattribute/textattribute(Name; Source) { ... }
    xmlport_attribute: $ => seq(
      field('attribute_type', choice(
        $.fieldattribute_keyword,
        $.textattribute_keyword,
      )),
      '(',
      field('name', $._identifier_or_quoted),
      optional(seq(
        ';',
        field('source', $._field_source)
      )),
      ')',
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    ),

    // =====================================================================
    // DotNet internals
    // =====================================================================

    assembly_declaration: $ => seq(
      $.assembly_keyword,
      '(',
      field('name', choice(
        $.string_literal,
        $.quoted_identifier,
        $.dotnet_assembly_name
      )),
      ')',
      '{',
      optional(field('body', $.assembly_body)),
      '}'
    ),
    assembly_body: $ => repeat1(choice(
      $.type_declaration,
      $.property,
      $.empty_statement,
    )),

    // THE THIRD COPY of an identifier-ish character class, and it deliberately
    // does NOT track `identifier`. This names a .NET assembly / namespace, not
    // an AL identifier, so it keeps the narrower `[\p{L}_][\p{L}\p{N}_]*` that
    // `identifier` carried before Nl/Mn/Mc/Pc/Cf were added to match alc's AL
    // rule. Widening it would be claiming something about .NET naming that has
    // not been measured.
    //
    // It is called out because it is a silent-drift hazard by construction:
    // `identifier` and src/scanner.c's tables are generated from one source and
    // cannot diverge, but this literal is hand-written and shares neither. It is
    // safe today only because nothing in src/scanner.c consults it -- the
    // scanner mediates PROPERTY_NAME and VAR_ATTRIBUTE_OPEN, which are about
    // `identifier`. If a scanner token ever needs this class, generate it too
    // rather than copying the regex a fourth time.
    dotnet_assembly_name: $ => token(seq(
      /[\p{L}_][\p{L}\p{N}_]*/u,
      repeat(seq('.', /[\p{L}_][\p{L}\p{N}_]*/u))
    )),

    type_declaration: $ => seq(
      $.type_keyword,
      '(',
      field('dotnet_type', choice(
        $.string_literal,
        $.quoted_identifier,
        $.dotnet_assembly_name
      )),
      ';',
      field('al_name', choice(
        $.string_literal,
        $.quoted_identifier,
        $.identifier
      )),
      ')',
      '{',
      optional(field('body', $.declaration_body)),
      '}'
    ),

    // =====================================================================
    // ControlAddIn event declarations
    // =====================================================================

    // event OnReady();
    event_declaration: $ => prec.right(seq(
      $.event_keyword,
      field('name', $._identifier_or_quoted),
      '(',
      optional(field('parameters', $.parameter_list)),
      ')',
      optional(';')
    )),

    // =====================================================================
    // Procedures
    // =====================================================================

    procedure: $ => prec.right(seq(
      optional(field('modifier', $.procedure_modifier)),
      $.procedure_keyword,
      $._procedure_name_and_params,
      optional(choice(
        seq(
          choice(
            $._procedure_return_specification,
            $._procedure_named_return,
          ),
          optional(';')
        )
      )),
      optional(';'),
      // Pragma-only #if/#endif between the procedure header and its body
      // (BC wraps `#pragma warning restore ASxxxx` in `#if not CLEANxx`).
      repeat($.preproc_pragma_only),
      choice(
        $._routine_regular_body,
        $.preproc_split_procedure_body,
        $.preproc_split_complete_body,
      )
    )),

    // Shared procedure name + parameter list, terminating at the hard ')'
    _procedure_name_and_params: $ => seq(
      field('name', $._identifier_or_quoted),
      '(',
      optional(field('parameters', $.parameter_list)),
      ')',
    ),

    // Regular routine body: [var section] then code_block — a complete unit.
    // The code_block is exposed via the `body` field for textobject queries
    // (issue #19). Unlike brace constructs, begin/end stay inside code_block
    // (Rust `block` model) since code_block is also reused as a nested
    // statement block.
    // prec.right resolves the shift/reduce on the trailing `optional(';')`,
    // which `code_block` used to own and therefore never exposed here.
    _routine_regular_body: $ => prec.right(seq(
      optional(choice(
        $.var_section,
        $.preproc_conditional_var_block,
      )),
      field('body', $.code_block),
      // The body's terminator. `code_block` no longer carries it — see the note
      // there. Kept outside field('body') so the field stays a single node.
      optional(';'),
    )),

    // Preprocessor split procedure body: var+begin+preamble in #if, begin in #else
    // #if / [var] begin [preamble] [if-guard then] / #else / begin / #endif / shared_stmts end;
    // The #if branch may end with an if-then guard whose then-branch is the shared code.
    preproc_split_procedure_body: $ => prec.right(25, seq(
      $._pspb_if_branch,
      $._pspb_else_branch,
      optional(field('body', $.statement_block)),
      $.end_keyword,
      optional(';'),
    )),

    // #if branch of a split procedure body — complete unit ending at #else
    _pspb_if_branch: $ => seq(
      $.preproc_if,
      optional($.var_section),
      $.begin_keyword,
      optional(field('body', $.statement_block)),
      optional($._preproc_if_header),  // trailing if-then guard (body is shared code)
      $.preproc_else,
    ),

    // #else branch opener of a split procedure body — complete unit ending at #endif
    _pspb_else_branch: $ => seq(
      optional($.var_section),
      $.begin_keyword,
      $.preproc_endif,
    ),

    // Preprocessor split complete body: each #if/#else branch has a full var+begin+end body
    // No shared code after #endif — the entire body differs across branches.
    // Example: trigger OnValidate() #if ... var ... begin ... end; #else ... var ... begin ... end; #endif
    preproc_split_complete_body: $ => prec.right(25, seq(
      $.preproc_if,
      $._preproc_branch_body,
      repeat(seq($.preproc_elif, $._preproc_branch_body)),
      optional(seq($.preproc_else, $._preproc_branch_body)),
      $.preproc_endif,
    )),

    // Shared body block for a single preprocessor branch: [var] begin stmts end [;]
    _preproc_branch_body: $ => seq(
      optional($.var_section),
      $.begin_keyword,
      optional(field('body', $.statement_block)),
      $.end_keyword,
      optional(';'),
    ),

    // Preprocessor-split procedure: header variants in #if/#else, shared body
    preproc_split_procedure: $ => prec(25, seq(
      $.preproc_if,
      $._procedure_header,
      repeat(seq($.preproc_elif, $._procedure_header)),
      optional(seq($.preproc_else, $._procedure_header)),
      $.preproc_endif,
      optional(';'),
      $._routine_regular_body,
    )),

    // Procedure preamble: header + optional var section (used in preproc_split_procedure_preamble)
    _procedure_preamble: $ => seq(
      $._procedure_header,
      optional(choice(
        $.var_section,
        $.preproc_conditional_var_block,
      )),
    ),

    // Preprocessor-split procedure preamble: header+var variants in #if/#else, shared body after #endif
    // Example: procedure signature AND var section differ across branches, shared begin...end follows
    // prec.right for the trailing `optional(';')` the code_block stopped owning.
    preproc_split_procedure_preamble: $ => prec.right(25, seq(
      $.preproc_if,
      $._procedure_preamble,
      repeat(seq($.preproc_elif, $._procedure_preamble)),
      optional(seq($.preproc_else, $._procedure_preamble)),
      $.preproc_endif,
      $.code_block,
      optional(';'),
    )),

    // Procedure header without body (used in preproc split procedures)
    _procedure_header: $ => seq(
      repeat($.attribute_item),
      optional(field('modifier', $.procedure_modifier)),
      $.procedure_keyword,
      $._procedure_name_and_params,
      optional(choice(
        seq(
          choice(
            $._procedure_return_specification,
            $._procedure_named_return,
          ),
          optional(';')
        )
      )),
    ),

    // Interface procedure declaration (no body, just signature)
    // Uses prec.dynamic to prefer full procedure when body follows
    interface_procedure: $ => prec.dynamic(-1, prec.right(-5, seq(
      $.procedure_keyword,
      $._procedure_name_and_params,
      optional($.interface_procedure_suffix),
    ))),

    // Suffix for interface_procedure: return type and/or semicolon
    // Separated as a named rule to avoid state-sharing with _procedure_header
    interface_procedure_suffix: $ => choice(
      seq($._procedure_return_specification, optional(';')),
      seq($._procedure_named_return, optional(';')),
      ';',
    ),

    procedure_modifier: $ => choice(
      $.local_keyword,
      $.internal_keyword,
      $.protected_keyword,
    ),

    // Return type: `: TypeSpec`
    _procedure_return_specification: $ => seq(
      ':',
      field('return_type', $.type_specification),
    ),

    // Named return: `result: TypeSpec`
    _procedure_named_return: $ => prec(15, seq(
      field('return_value', $._identifier_or_quoted),
      $._procedure_return_specification,
    )),

    // Parameter list: semicolon-separated parameters
    parameter_list: $ => seq(
      optional(repeat1($.attribute_item)),
      $.parameter,
      repeat(seq(';', optional(repeat1($.attribute_item)), $.parameter)),
    ),

    parameter: $ => seq(
      optional(field('modifier', $.var_keyword)),
      field('name', $._identifier_or_quoted),
      ':',
      field('type', $.type_specification),
    ),

    // code_block: begin ... end;
    // begin/end are scanner-exclusive at EVERY depth: the scanner emits
    // begin_keyword/end_keyword unless a PREPROC_SPLIT_* lookahead claims the
    // keyword first. There is deliberately no kw('begin')/kw('end') fallback —
    // a scanner/literal split for the same text is what GLR forks on, and the
    // anonymous kw() form is a token(PATTERN), which tree-sitter renders as a
    // HIDDEN auxiliary symbol, so the keyword would vanish from the tree.
    // The block does NOT own the ';' that follows its `end`. It used to, and
    // that single `optional(';')` was the root cause of the ae90aea regression:
    // being under prec.right it was GREEDY, so in `if C then begin … end; else X;`
    // the block consumed the terminator before any rule downstream of the
    // then-branch could test for one. The else arm therefore stayed available,
    // and the else bound to the if instead of to the enclosing case — 23 sites,
    // zero ERROR nodes. Three targeted workarounds were tried and all three had
    // worse collateral than the bug.
    //
    // The terminator is now EXTERNAL at every use site: `_routine_regular_body`,
    // `preproc_split_procedure_preamble`, `_preproc_branch_statement` and
    // `case_else_branch` each take their own `optional(';')`, and in statement
    // and branch position it belongs to `_statement` / `case_branch`. Do not put
    // it back here — a terminator that is inside the block is invisible to
    // everything that needs to see it.
    code_block: $ => prec.right(seq(
      $.begin_keyword,
      optional(field('body', $.statement_block)),
      choice(
        $.end_keyword,
        // Split ending: 'end' is inside #if, with different structure in #else
        // Scanner's PREPROC_SPLIT_END only fires when end;#else or end;#endif
        $.preproc_split_code_block_end,
        $.preproc_split_else_begin_over_endif,
      ),
    )),

    // A code_block closed by an `end` inside a conditional, which then opens an
    // `else begin` whose own `end;` sits OUTSIDE the `#endif`:
    //
    //     if C then begin  A();  #if COND  end else begin  B();  #endif  end;
    //
    // Sibling of preproc_split_code_block_end, whose `_preproc_end_branch`
    // requires the else-block's `end` to close inside the same conditional.
    // Here it closes after `#endif`, so that rule declines.
    //
    // Silent before this existed: `end`, `else` and `begin` each fell out as a
    // bare `identifier` inside preproc_conditional_statement, the else branch's
    // statements were flattened next to them, and the whole if/else read as a
    // single then-branch. Zero ERROR nodes. Real site: BaseApp
    // Integration/D365Sales/CRMSetupDefaults.Codeunit.al:76-84.
    preproc_split_else_begin_over_endif: $ => prec.right(25, seq(
      $.preproc_if,
      $.end_keyword,
      $.else_keyword,
      $.begin_keyword,
      repeat($._statement),
      $.preproc_endif,
      repeat($._statement),
      $.end_keyword,
    )),

    // Content-only statement run (no begin/end) so a statement container can
    // expose its inside as a single node. repeat1 (tree-sitter forbids
    // empty-matching rules) -> wrapped in optional() at each use site.
    statement_block: $ => repeat1($._statement),

    // =====================================================================
    // Triggers
    // =====================================================================

    trigger_declaration: $ => seq(
      $.trigger_keyword,
      field('name', $._trigger_name),
      '(',
      optional(field('parameters', $.parameter_list)),
      ')',
      optional(choice(
        $._procedure_return_specification,
        $._procedure_named_return,
      )),
      optional(';'),
      choice(
        $._routine_regular_body,
        $.preproc_split_complete_body,
      )
    ),

    // Preprocessor conditional wrapping a var section before begin
    preproc_conditional_var_block: $ => seq(
      $.preproc_if,
      optional($.var_section),
      repeat(seq(
        $.preproc_elif,
        optional($.var_section),
      )),
      optional(seq(
        $.preproc_else,
        optional($.var_section),
      )),
      $.preproc_endif,
    ),

    // Trigger name: a simple name, or a scoped member-trigger name
    // (`UserTours::ShowTourWizard`). The scoped form is a single NAMED node so the
    // `name` field binds one value — never spreading over the `::` token (which would
    // make `name` `multiple:true` with an anonymous `::` in its type set, and make
    // `field("name")` return only the object half, dropping the member).
    _trigger_name: $ => choice(
      $.member_trigger_name,
      $._identifier_or_quoted,
    ),

    member_trigger_name: $ => seq(
      field('object', $._identifier_or_quoted),
      '::',
      field('member', $._identifier_or_quoted),
    ),

    // =====================================================================
    // Variable declarations
    // =====================================================================

    var_section: $ => prec.right(seq(
      optional(choice($.protected_keyword, $.local_keyword)),
      $.var_keyword,
      optional(field('body', $.var_body)),
    )),

    var_body: $ => repeat1(choice(
      $.variable_declaration,
      $.var_attribute_item,
      $.preproc_conditional_var,
      $.preproc_split_procedure,
    )),

    // Attribute inside a var section — uses scanner token to ensure the attribute
    // is followed by a variable declaration (not a procedure or other construct).
    // This prevents var_section from greedily consuming procedure-level attributes.
    var_attribute_item: $ => seq(
      $.var_attribute_open,  // scanner-disambiguated '['
      field('attribute', $.attribute_content),
      ']'
    ),

    preproc_conditional_var: $ => seq(
      $.preproc_if,
      repeat(choice($.variable_declaration, $.var_attribute_item, $.attribute_item, $._body_element)),
      repeat(seq(
        $.preproc_elif,
        repeat(choice($.variable_declaration, $.var_attribute_item, $.attribute_item, $._body_element)),
      )),
      optional(seq(
        $.preproc_else,
        repeat(choice($.variable_declaration, $.var_attribute_item, $.attribute_item, $._body_element)),
      )),
      $.preproc_endif,
    ),

    variable_declaration: $ => choice(
      // Label variable: Name: Label 'text', Locked = true;
      prec(5, seq(
        field('name', $._identifier_or_quoted),
        ':',
        // Conventionally a Label, but the rule accepts any basic_type — the
        // "must" is a semantic rule for a linter, not something the grammar
        // enforces (parse structure, don't validate).
        field('type', $.basic_type),
        field('value', choice($.string_literal, $.verbatim_string)),
        optional(seq(
          ',',
          optional(seq(
            $.label_attribute,
            repeat(seq(',', $.label_attribute))
          ))
        )),
        ';'
      )),
      // TextConst variable: Name: TextConst ENU='text', DEU='text';
      prec(4, seq(
        field('name', $._identifier_or_quoted),
        ':',
        field('type', alias(kw('textconst'), $.basic_type)),
        $.ml_value_list,
        ';'
      )),
      // Multi-name variable: Name1, Name2, Name3 : Type;
      prec(3, seq(
        field('name', $._identifier_or_quoted),
        repeat1(seq(',', field('name', $._identifier_or_quoted))),
        ':',
        field('type', $.type_specification),
        ';'
      )),
      // Regular variable: Name: Type;
      prec(1, seq(
        field('name', $._identifier_or_quoted),
        ':',
        field('type', $.type_specification),
        ';'
      )),
    ),

    label_attribute: $ => seq(
      field('name', $.identifier),
      '=',
      field('value', choice($.boolean, $.string_literal, $.integer))
    ),

    // =====================================================================
    // Attributes
    // =====================================================================

    attribute_item: $ => seq(
      '[',
      field('attribute', $.attribute_content),
      ']'
    ),

    attribute_content: $ => seq(
      field('name', $.identifier),
      optional(field('arguments', $.attribute_arguments)),
    ),

    attribute_arguments: $ => seq(
      '(',
      optional($.attribute_argument_list),
      ')'
    ),

    attribute_argument_list: $ => seq(
      $._attribute_argument,
      repeat(seq(',', $._attribute_argument)),
    ),

    _attribute_argument: $ => choice(
      $.boolean,
      $.integer,
      $.string_literal,
      $.identifier,
      $.quoted_identifier,
      $.qualified_enum_value,
      $.database_reference,
      $.member_expression,
    ),

    // =====================================================================
    // Preprocessor directives
    // =====================================================================

    // Structural preprocessor conditionals: #if/#elif/#else/#endif
    preproc_conditional: $ => seq(
      $.preproc_if,
      repeat($._body_element),
      repeat(seq(
        $.preproc_elif,
        repeat($._body_element),
      )),
      optional(seq(
        $.preproc_else,
        repeat($._body_element),
      )),
      $.preproc_endif,
    ),

    // Scanner-exclusive: $.preproc_open is the ONLY route to this token (no
    // grammar-literal fallback). The external scanner now consumes '#',
    // optional horizontal whitespace, and the case-insensitive keyword as ONE
    // token (see scanner.c PREPROC_OPEN) — spaced (`# if`) and unspaced
    // (`#if`) forms are both scanner-owned, so there is no overlapping
    // scanner/literal lexer state for GLR to fork on (the reverted
    // literal-variant attempt hit exactly that trap — see CHANGELOG.md 3.1.0
    // "Not supported (reviewed and explicitly rejected)", now resolved in
    // 3.2.0).
    preproc_if: $ => seq(
      $.preproc_open,
      field('condition', $._preproc_expression)
    ),

    // A preprocessor conditional whose only content is pragmas/comments (both
    // are `extras`, so no structural children appear between the directives).
    // Used where MS BC wraps `#pragma warning disable/restore` in `#if/#endif`
    // at a construct-internal boundary (e.g. between a field header and body).
    preproc_pragma_only: $ => seq(
      $.preproc_if,
      repeat($.preproc_elif),
      optional($.preproc_else),
      $.preproc_endif,
    ),

    _preproc_expression: $ => choice(
      $.identifier,
      $.preproc_parenthesized_expression,
      $.preproc_not_expression,
      $.preproc_or_expression,
      $.preproc_and_expression,
    ),

    // `#if (FOO)` and `#if not (FOO and BAR)` — alc accepts both. Without this
    // the condition was a MISSING identifier and the `(…)` leaked into the
    // branch body as an expression statement.
    preproc_parenthesized_expression: $ => seq(
      '(', $._preproc_expression, ')'
    ),

    preproc_or_expression: $ => prec.left(1, seq(
      $._preproc_expression,
      choice(alias(kw('or'), 'or'), '||'),
      $._preproc_expression,
    )),

    preproc_and_expression: $ => prec.left(2, seq(
      $._preproc_expression,
      choice(alias(kw('and'), 'and'), '&&'),
      $._preproc_expression,
    )),

    preproc_not_expression: $ => seq(
      alias(kw('not'), 'not'),
      $._preproc_expression
    ),

    // Pure grammar literals — elif, like else, has NO external-scanner token
    // and touches no scanner state (it doesn't change #if/#endif nesting
    // depth, unlike preproc_open/preproc_close). Horizontal whitespace after
    // the '#' is tolerated the same way the scanner tolerates it for
    // #if/#endif. `[ \t]*` NEVER `\s*` — the regex crate's `\s` matches '\n',
    // which would let the token span a newline and swallow the next line's
    // source. `elif` and `else` carry no external token and touch no depth
    // state, so a regex here is a plain literal-vs-regex swap with no
    // scanner interaction. See the Task 4 design note for the full "why
    // elif differs from if/endif" reasoning.
    preproc_elif: $ => seq(
      new RustRegex('(?i)#[ \\t]*elif'),
      field('condition', $._preproc_expression)
    ),

    preproc_else: $ => new RustRegex('(?i)#[ \\t]*else'),

    // Scanner-exclusive: $.preproc_close is the ONLY route to this token (no
    // grammar-literal fallback, spaced or unspaced) — see preproc_if above
    // for the rationale. This RETIRES the pre-3.2.0 '# endif' literal
    // fallback, which matched a spaced close WITHOUT decrementing the
    // scanner's depth counter (a latent depth-corruption bug); the scanner
    // now owns spaced '# endif' too, so every close — spaced or not —
    // decrements depth correctly.
    preproc_endif: $ => $.preproc_close,

    // Preprocessor-split if statement: if header varies across #if/#else, body is shared
    // Pattern 1: #if COND / if (expr) then / #else / if (expr) then / #endif / body;
    // Pattern 2: #if COND / if (expr) then / #endif / body;  (no #else)
    preproc_split_if_statement: $ => prec.right(seq(
      $.preproc_if,
      $._preproc_if_header,
      repeat(seq($.preproc_elif, $._preproc_if_header)),
      optional(seq($.preproc_else, $._preproc_if_header)),
      $.preproc_endif,
      $._then_branch,
      optional(seq(
        $.else_keyword,
        $._else_branch
      ))
    )),

    // If-then header (condition only, no body) — used in preproc split if statements
    _preproc_if_header: $ => seq(
      $.if_keyword,
      field('condition', $._expression),
      $.then_keyword,
    ),

    // Preprocessor-guarded statement: guard statements + split if-then before shared code
    // #if COND / guard_stmts; if X then / #endif / shared_statement;
    // In COND mode: guard_stmts; if X then shared_statement;
    // Otherwise: just shared_statement;
    preproc_guarded_statement: $ => prec.right(seq(
      $.preproc_if,
      $._preproc_guard_block,
      $.preproc_endif,
      $._then_branch,
    )),

    // Guard block: one or more expression statements followed by an if-then header
    // Uses _expression_statement to avoid consuming if-statements that could
    // be mistaken for _preproc_if_header
    _preproc_guard_block: $ => seq(
      repeat1(seq(prec(2, $._expression_statement), ';')),
      $._preproc_if_header,
    ),

    // Preprocessor-split if-else: full if-then-X-else inside #if, Y outside
    // #if COND / if X then Y else / #endif / Z;
    preproc_split_if_else_statement: $ => prec.right(seq(
      $.preproc_if,
      $.if_keyword,
      field('condition', $._expression),
      $.then_keyword,
      $._then_branch,
      $.else_keyword,
      choice(
        // Fragmented: else begin #endif stmts #if end; #endif
        // The if-then-begin-...-end-else-begin pattern where begin opens shared body
        $.preproc_fragmented_else_tail,
        // Normal: else followed by #elif/#else/#endif variants, then shared else body
        seq(
          repeat(seq($.preproc_elif,
            $.if_keyword,
            field('condition', $._expression),
            $.then_keyword,
            $._then_branch,
            $.else_keyword,
          )),
          optional(seq($.preproc_else,
            $.if_keyword,
            field('condition', $._expression),
            $.then_keyword,
            $._then_branch,
            $.else_keyword,
          )),
          $.preproc_endif,
          $._else_branch_simple,
        ),
      ),
    )),

    // Preprocessor split if-then-begin:
    // #if COND / [preamble] if EXPR then begin / #endif / statements / #if COND / end[;] or end else begin...end; / #endif
    preproc_split_if_then_begin: $ => prec(26, seq(
      $._preproc_split_then_begin_open,
      repeat($._statement),
      $.preproc_if,
      repeat($._statement),           // allow preamble before end
      $.end_keyword,
      choice(
        optional(';'),                // Pattern A: just end;
        $._else_begin_block,          // Pattern B: end else begin ... end;
      ),
      $.preproc_endif,
    )),

    // Complete split-if opening unit: #if [preamble] if EXPR then begin #endif
    // Ends at #endif — a complete preprocessor-delimited unit, not a mid-construct prefix.
    _preproc_split_then_begin_open: $ => seq(
      $.preproc_if,
      repeat($._statement),           // allow preamble statements before if
      $.if_keyword,
      field('condition', $._expression),
      $.then_keyword,
      $.preproc_split_begin,          // 'begin' at depth > 0, before #endif
      $.preproc_endif,
    ),

    // Complete preprocessor-guarded end: #if end [;] #endif
    _preproc_end_guard: $ => seq(
      $.preproc_if,
      $.end_keyword,
      optional(';'),
      $.preproc_endif,
    ),

    // Complete else-branch begin block: else begin stmts end [;] — a complete unit
    _else_begin_block: $ => seq(
      $.else_keyword,
      $.begin_keyword,
      repeat($._statement),
      $.end_keyword,
      optional(';'),
    ),

    // Asymmetric if-then-begin: if...then begin is inside #if, but end is outside
    // Pattern: #if / if EXPR then begin / #endif / shared_stmts end;
    preproc_split_if_begin_asymmetric: $ => prec.right(26, seq(
      $._preproc_split_then_begin_open,
      repeat($._statement),
      $.end_keyword,
      optional(';'),
    )),

    // Split if-then-begin where BOTH branches end with `then begin` and a single
    // shared `end;` follows after #endif (BC gates the differing if-header behind
    // `#if not CLEANxx`/`#else`). The #if-branch begin precedes #else, so the
    // split lookahead misses and the scanner emits begin_keyword; the
    // #else-branch begin precedes #endif, so it is PREPROC_SPLIT_BEGIN.
    // Pattern: #if [pre] if A then begin [stmts] #else [pre] if B then begin #endif shared end;
    preproc_split_if_then_begin_else_shared: $ => prec.right(26, seq(
      $.preproc_if,
      repeat($._statement),
      $.if_keyword,
      field('condition', $._expression),
      $.then_keyword,
      $.begin_keyword,
      repeat($._statement),
      $.preproc_else,
      repeat($._statement),
      $.if_keyword,
      field('condition', $._expression),
      $.then_keyword,
      $.preproc_split_begin,
      $.preproc_endif,
      repeat($._statement),
      $.end_keyword,
      optional(';'),
    )),

    // Split if-then-begin with #else alternative: #if branch has begin+extra stmts, #else has just if-then
    // Pattern: #if / [preamble] if EXPR then begin <stmts> / #else / [preamble] if EXPR then / #endif / shared_stmts / #if / end; / #endif
    // The #if branch wraps shared code in begin/end with extra preamble; #else branch uses bare if-then.
    preproc_split_if_begin_else: $ => prec(26, seq(
      $.preproc_if,
      repeat($._statement),              // optional preamble in #if branch
      $.if_keyword,
      field('condition', $._expression),
      $.then_keyword,
      $.begin_keyword,
      repeat($._statement),              // extra stmts in #if branch after begin
      $.preproc_else,
      repeat($._statement),              // optional preamble in #else branch
      $.if_keyword,
      field('condition', $._expression),
      $.then_keyword,
      $.preproc_endif,
      repeat($._statement),              // shared statements after #endif
      $._preproc_end_guard,
    )),

    // Split code_block ending: #if end; #else [stmts] end else begin stmts end; #endif
    // Split call statement: function call where first argument(s) differ across #if/#else
    // Each branch: func_name(arg, arg,   (ends with trailing comma)
    // After #endif: remaining_args);
    preproc_split_call_statement: $ => prec(25, seq(
      $.preproc_if,
      $._preproc_call_prefix,
      repeat(seq($.preproc_elif, $._preproc_call_prefix)),
      optional(seq($.preproc_else, $._preproc_call_prefix)),
      $.preproc_endif,
      // Shared remaining arguments
      optional($._expression_list),
      ')',
      ';'
    )),

    // Call prefix inside a preproc branch: func(arg1, arg2,
    _preproc_call_prefix: $ => seq(
      choice(
        $.identifier,
        $.member_expression,
        $.qualified_enum_value,
        $.keyword_identifier,
        $.subscript_expression,
      ),
      '(',
      $._expression,
      repeat(seq(',', $._expression)),
      ','  // trailing comma leads into shared args
    ),

    // Used in code_block when the closing end (and optional else branch)
    // differs across preprocessor branches. Scanner's PREPROC_SPLIT_END ensures
    // this only matches when 'end' at depth>0 is followed by ';' then a branch
    // continuation (#elif/#else/#endif).
    //
    // #elif is a full peer of #else here. Every branch is an alternative
    // completion of the same code_block, so each one independently contributes
    // either a bare `end;` or the longer `end … else begin … end;` tail — hence
    // _preproc_end_branch rather than a fixed first-is-bare/last-is-tail shape.
    // Before this, #elif was absent from both the scanner's target set and this
    // rule, so `#if … end; #elif …` degraded into a call_statement plus loose
    // identifiers (a wrong tree, though the MISSING end_keyword it left behind
    // did keep the error gate honest). alc accepts the #elif form.
    preproc_split_code_block_end: $ => prec(25, seq(
      $.preproc_if,
      $._preproc_end_branch,
      repeat(seq($.preproc_elif, $._preproc_end_branch)),
      optional(seq($.preproc_else, $._preproc_end_branch)),
      $.preproc_endif,
    )),

    // One branch of preproc_split_code_block_end: either the split `end;` on its
    // own, or statements followed by the full end/else-begin tail.
    _preproc_end_branch: $ => choice(
      seq($.preproc_split_end, optional(';')),
      seq(repeat($._statement), $.end_keyword, $._else_begin_block),
    ),

    // A code_block whose `begin` opens inside one conditional and whose `end;`
    // closes inside a LATER one, with shared code in between:
    //
    //     #if COND        begin  A();   #endif   B();   #if COND  end;  #endif
    //
    // Sibling of preproc_fragmented_else_tail, which is the same shape when the
    // `begin` sits immediately before its `#endif` and so arrives as
    // PREPROC_SPLIT_BEGIN. Here a statement follows the `begin`, the split
    // lookahead declines, and the scanner emits a plain begin_keyword — which is
    // why this needs its own rule rather than reusing that one.
    //
    // Before this existed the whole construct fell apart silently: `begin` became
    // an `identifier`, `end;` a `call_statement`, and the bracketed statements
    // became siblings of the `begin` instead of its children, with zero ERROR
    // nodes. Real site: BaseApp Warehouse/Structure/WhseIntegrationManagement.
    preproc_split_code_block_over_endif: $ => prec(25, seq(
      $.preproc_if,
      $.begin_keyword,
      repeat($._statement),
      $.preproc_endif,
      repeat($._statement),
      $._preproc_end_guard,
    )),

    // Fragmented else tail: begin #endif stmts #if end; #endif
    // Used after else_keyword when the else branch's begin/end is split across preprocessor blocks
    preproc_fragmented_else_tail: $ => prec(25, seq(
      $.preproc_split_begin,          // 'begin' at depth > 0, before #endif
      $.preproc_endif,
      repeat($._statement),
      $._preproc_end_guard,
    )),

    // Preprocessor conditionals in statements context
    preproc_conditional_statement: $ => prec.right(seq(
      $.preproc_if,
      repeat($._preproc_branch_statement),
      repeat(seq(
        $.preproc_elif,
        repeat($._preproc_branch_statement),
      )),
      optional(seq(
        $.preproc_else,
        repeat($._preproc_branch_statement),
      )),
      $.preproc_endif,
    )),

    // A preproc conditional fills a `_statement` slot, but the position that slot
    // sits in may accept more than a statement: case_else_branch takes a
    // `code_block` directly, and alc accepts a bare `begin … end;` compound
    // statement anywhere a statement is allowed (verified against alc
    // 18.0.37.11445). Wrapping such a block in `#if` must not take the option
    // away. Without this, `else #if X … #else begin A(); end; #endif` lost the
    // block entirely — `begin` fell back to `identifier`, `end;` reparsed as a
    // `call_statement`, no `code_block` was produced, and the statements became
    // siblings of the `begin` instead of its children. Zero ERROR nodes, so no
    // gate saw it.
    //
    // `code_block` is deliberately NOT added to `_statement_inner`, which would
    // be the more general statement of the same truth: that makes every
    // `while … do begin`, `if … then begin` and `for … do begin` ambiguous
    // between "loop/branch body" and "standalone block", forcing a dangling-block
    // conflict on each host and a GLR fork on every `begin` in the corpus. The
    // narrow rule keeps the fork inside preprocessor branches.
    _preproc_branch_statement: $ => choice(
      $._statement,
    ),

    // Preprocessor conditionals in actions context
    preproc_conditional_actions: $ => seq(
      $.preproc_if,
      repeat($._action_element),
      repeat(seq(
        $.preproc_elif,
        repeat($._action_element),
      )),
      optional(seq(
        $.preproc_else,
        repeat($._action_element),
      )),
      $.preproc_endif,
    ),

    // Preprocessor conditionals in layout context
    preproc_conditional_layout: $ => seq(
      $.preproc_if,
      repeat($._layout_element),
      repeat(seq(
        $.preproc_elif,
        repeat($._layout_element),
      )),
      optional(seq(
        $.preproc_else,
        repeat($._layout_element),
      )),
      $.preproc_endif,
    ),

    // Preprocessor conditionals in mixed layout+body contexts (grid, group, etc.)
    // Uses prec.dynamic(-1) so pure-property or pure-layout preproc rules are
    // preferred when they can parse; this only wins when content is truly mixed.
    preproc_conditional_layout_mixed: $ => prec.dynamic(-1, seq(
      $.preproc_if,
      repeat(choice($._body_element, $._layout_element)),
      repeat(seq(
        $.preproc_elif,
        repeat(choice($._body_element, $._layout_element)),
      )),
      optional(seq(
        $.preproc_else,
        repeat(choice($._body_element, $._layout_element)),
      )),
      $.preproc_endif,
    )),

    // Pragma and region directives (extras — can appear anywhere).
    // Whitespace between `#` and the keyword is HORIZONTAL ONLY (`[ \t]*`),
    // never `\s*` — the regex crate's `\s` matches `\n`/`\r` too, which would
    // let the token span a newline and silently swallow real source on the
    // NEXT line (confirmed pre-fix: `#\nregion Foo` parsed as a single
    // `preproc_region` spanning both lines). `[^\n\r]*` already bounds the
    // token to one line on the tail end; `[ \t]*` bounds it on the head end.
    pragma: $ => new RustRegex('(?i)#[ \\t]*pragma([^\\n\\r0-9A-Za-z_][^\\n\\r]*)?'),

    preproc_region: $ => new RustRegex('(?i)#[ \\t]*region([^\\n\\r0-9A-Za-z_][^\\n\\r]*)?'),

    preproc_endregion: $ => new RustRegex('(?i)#[ \\t]*endregion([^\\n\\r0-9A-Za-z_][^\\n\\r]*)?'),

    // Symbol definition directives. Line-level like #pragma/#region: they take a
    // single symbol name, never open or close a conditional, and so must NOT
    // touch the scanner's #if/#endif depth counter.
    //
    // Positionally the AL compiler is far stricter than this rule — verified
    // against alc 18.0.37 (full accept/reject matrix in
    // docs/preproc-define-undef.md):
    //   * accepted ONLY before the first real token of the file — comments,
    //     #pragma, #region/#endregion and whole #if/#else/#endif blocks may
    //     precede or wrap them, but a `namespace`, `using` or object
    //     declaration ends the window (error AL0625, "Cannot define/undefine
    //     preprocessor symbols after first token in file")
    //   * the symbol must be a bare identifier — letters, digits, underscores
    //     (error AL0107 on a missing or quoted name)
    //   * only a trailing `//` comment may follow the symbol (error AL0631)
    //   * `#` and the directive must share a line (error AL0621)
    // Per "parse structure, don't validate", those are semantic checks for a
    // linter, so these stay `extras` alongside the other line-level directives.
    // That also buys reachability for free: file-leading position, inside a
    // leading pragma-only #if block, and after leading comments/pragmas are all
    // the same rule with no new parser states and no GLR conflicts.
    preproc_define: $ => new RustRegex('(?i)#[ \\t]*define([^\\n\\r0-9A-Za-z_][^\\n\\r]*)?'),

    preproc_undef: $ => new RustRegex('(?i)#[ \\t]*undef([^\\n\\r0-9A-Za-z_][^\\n\\r]*)?'),

    // =====================================================================
    // Statements
    // =====================================================================

    _statement: $ => prec.right(choice(
      // A bare `;`. Moved here out of `_statement_inner` by the terminator
      // restructure: an empty statement IS a terminator, so leaving it inside
      // `_statement_inner` made every `_statement_inner` position — including
      // the then-branch of an `if` — able to swallow a ';' after the
      // restructure had taken the ';' out of everything else. `if C then ;`
      // must TERMINATE the if (alc AL0110), so the then-branch reaches
      // `empty_statement` only through the arm that bars a following `else`.
      $.empty_statement,
      // A parenless no-arg call (`Initialize;`) — a bare identifier in statement
      // position that OWNS its terminating `;`. Owning the `;` is what makes a real
      // parenless call structurally distinct from tree-sitter ERROR-recovery debris
      // (a bare identifier rescued after a syntax error has no terminator and stays a
      // raw identifier, never reducing to `call_statement`). The engine lowers a
      // `call_statement` to a parenless call edge; a bare identifier is treated as
      // recovery debris / a value statement and is NOT a call. Higher precedence than
      // the `_expression_statement` branch so `Foo;` deterministically reduces here.
      $.call_statement,
      seq($._statement_inner, optional(';'))
    )),

    // The statement itself, without the terminating ';'. Split out of
    // `_statement` so that body/branch positions can field the statement
    // WITHOUT the field spilling onto the ';' — see fieldedStatement().
    _statement_inner: $ => choice(
          $.code_block,
          $.assignment_statement,
          $.asserterror_statement,
          $.if_statement,
          $.exit_statement,
          $.continue_statement,
          $.break_statement,
          $.case_statement,
          $.for_statement,
          $.repeat_statement,
          $.while_statement,
          $.foreach_statement,
          $.with_statement,
          $._expression_statement,
          $.preproc_conditional_statement,
          $.preproc_split_if_statement,
          $.preproc_split_if_else_statement,
          $.preproc_split_if_then_begin,
          $.preproc_split_if_begin_asymmetric,
          $.preproc_split_if_begin_else,
          $.preproc_split_if_then_begin_else_shared,
          $.preproc_guarded_statement,
          $.preproc_split_call_statement,
          $.preproc_split_code_block_over_endif,
    ),

    // Parenless no-arg call statement (`Initialize;`). Requires the `;` terminator —
    // see the note in `_statement`. Only a bare identifier / quoted identifier is a
    // parenless call here; `Foo()` stays a `call_expression` and `Rec.Find;` stays a
    // `member_expression` (unchanged), so this adds no blast to parenful calls or
    // record operations. prec(13) > call_expression's prec(12) so the reduction wins.
    call_statement: $ => prec(13, seq(
      field('function', choice($.identifier, $.quoted_identifier)),
      ';'
    )),

    _expression_statement: $ => $._expression,

    empty_statement: $ => ';',

    // --- Assignment ---

    assignment_statement: $ => prec.dynamic(10, seq(
      field('left', $._expression),
      field('operator', $.assignment_operator),
      field('right', $._expression)
    )),

    assignment_expression: $ => prec.dynamic(1, prec.right(seq(
      field('left', $._expression),
      field('operator', $.assignment_operator),
      field('right', $._expression)
    ))),

    // Named, not hidden. As `_assignment_operator` this was a hidden rule over a
    // single token, so `field('operator', …)` on assignment_statement and
    // assignment_expression had nothing visible to attach to and the field was
    // dropped from node-types.json entirely. The bytes belonged to no node, so
    // there was no text fallback either: `i := 1` and `i += 2` produced
    // byte-identical trees, and any consumer doing dataflow read a plain
    // assignment where the source compounds. 22,964 `:=` per 500 files.
    //
    // The token() wrapper is load-bearing and must stay. It keeps this a single
    // atomic token distinct from the literal ':=' in for_statement; dropping it
    // makes the two collide and the grammar no longer generates. It is also why
    // queries/highlights.scm's `":=" @operator` never matched an assignment —
    // that pattern only ever saw for_statement's literal.
    assignment_operator: $ => token(choice(':=', '+=', '-=', '*=', '/=')),

    // --- If/Then/Else ---

    // alc is unambiguous here (verified against 18.0.37.11445):
    //
    //   if C then A else B;      accepted -- else binds to the nearest if
    //   if C then A; else B;     REJECTED, AL0110 "Orphaned ELSE statement"
    //
    // So a ';' TERMINATES the if: an else after one cannot belong to it. That is
    // now enforced by CONSTRUCTION rather than by a guard. The if owns no ';' of
    // its own and no then-branch form reachable here can hold one, so in
    // `if C then A; else B;` the ';' can only be taken by the enclosing
    // statement wrapper — which requires reducing this if_statement first, at
    // which point the else is out of reach. `case 1: if C then A; else B; end;`
    // therefore has only the no-else reading and the else is the CASE's, while
    // `case 1: if C then A else B; else C; end;` has no ';' and the else binds
    // here.
    //
    // ae90aea tried to express the same thing as a guard —
    // `choice(seq(else_keyword, _else_branch), optional(';'))` — which only bars
    // the else while the ';' is still UNCONSUMED at this point. `code_block`,
    // a nested `if_statement` and `empty_statement` all ate it first, so the
    // guard never fired and the else took the case's, at 23 sites with zero
    // ERROR nodes. Externalising the terminator is what makes the test possible
    // at all; a guard here cannot substitute for it.
    //
    // Dangling else. The ONE-seq shape with optional(else) plus prec.right is
    // load-bearing and must not be split into two alternatives: that is what
    // makes the else shift into the INNERMOST unmatched if. Splitting it into
    // `choice(with-else, without-else)` turns the decision into a choice between
    // two productions, which associativity does not govern, and
    // `if A then if B then if C then begin … end else X;` then binds the else to
    // an OUTER if — verified against a real BC file
    // (Assembly/Document/AssemblyAvailabilityMgt.Codeunit.al:144-149).
    //
    // The remaining ambiguity is against case_else_branch, and it is genuine:
    // for `case 1: if C then A else B; else D; end;` BOTH parses complete, so
    // static precedence cannot reach it (prec.right(30) on the else arm had no
    // effect at all). Only dynamic precedence can, and it has to be DIRECTIONAL.
    //
    // prec.dynamic(20) on the whole rule — the ae90aea shape — gives the
    // with-else and without-else productions the SAME score, so the tie fell
    // through to tree-sitter's structural tiebreak in ts_subtree_compare, which
    // ranks by symbol id. That is not a decision about AL; it is an artifact of
    // symbol numbering, and it silently flipped to the wrong parse when this
    // restructure renumbered the symbols. The wrong parse is the defect-1 shape:
    // the if loses its else, case_else_branch swallows it, and the real
    // case-else lexes as a bare `identifier` (`kw()` builds a regex token, so
    // keyword extraction never applies and `else` matches the identifier
    // pattern in statement position).
    //
    // The 30 on the else arm makes the preference explicit: BIND THE ELSE. Two
    // parses that differ only in whether an else attached to an if resolve
    // toward attachment, which is what alc does.
    //
    // This is safe only because the ';' cases no longer depend on precedence at
    // all. `case 1: if C then A; else B; end;` cannot reach the else arm under
    // ANY precedence now — the if owns no ';', so that parse does not exist.
    // Pinned by "A ';' before the else gives it to the CASE" in
    // test/corpus/dangling_else_case_branch_test.txt, which passes with the
    // dynamic precedences removed entirely.
    // Two then-branch forms are still SELF-TERMINATING after the restructure,
    // and they get the same treatment the others got by having their terminator
    // moved out: an `else` may not follow them.
    //
    //   * `call_statement` owns its ';' internally (`if C then Foo; else …`).
    //     Dropping it from the then-branch entirely is not an option — the node
    //     would degrade to a bare `identifier`, which the engine reads as
    //     recovery debris rather than a call.
    //   * `empty_statement` IS a ';' (`if C then ; else …`). Real site, and the
    //     last of the 25 census hits: Manufacturing/Document/
    //     CopyProductionOrderDocument.Report.al:79, where four `StatusType::`
    //     case branches each end `then ;` and the `else` is plainly the case's.
    //
    // So they are separate arms here with no `else` after them, and the else
    // hangs off the two forms that cannot hold a ';'. That exclusion holds only
    // because `_statement_inner` no longer contains `empty_statement` — it is
    // otherwise trivially routed around.
    //
    // The open pair is written out here rather than factored into a hidden
    // rule: a hidden rule carrying `field('then_branch', …)` cannot surface in
    // node-types.json, and the query-coverage harness counts each one
    // (`fields|skipped|hidden-rule`). Inlining keeps the fields attributable to
    // if_statement and the harness green.
    //
    // Splitting on the then-branch does NOT disturb the dangling-else
    // associativity the comment above warns about: the shift/reduce on `else`
    // is still one seq with `optional(else)` under prec.right, which is what
    // binds the else to the INNERMOST unmatched if. Pinned by "Nested ifs: the
    // else binds to the NEAREST unmatched if".
    if_statement: $ => prec.right(prec.dynamic(20, seq(
      $.if_keyword,
      field('condition', $._expression),
      $.then_keyword,
      choice(
        seq(
          field('then_branch', $._statement_inner),
          optional(prec.dynamic(30, seq($.else_keyword, $._else_branch))),
        ),
        field('then_branch', $.call_statement),
        field('then_branch', $.empty_statement),
      ),
    ))),

    // If statement without else clause — used as case branch body so that
    // `case 1: if C then A; else B; end;` can give the else to the CASE.
    // From 0f1871e (March); prec.dynamic(10) is that commit's value and is
    // deliberately unchanged — verified that all six dangling-else shapes still
    // resolve correctly with it, so there was no reason to touch it.
    //
    // It was NOT the cause of the dangling-else defect, though the obvious
    // reading says it was. Deleting this rule entirely leaves
    // `case 1: if C then A else B; else C; end;` misparsing exactly as before:
    // both readings are complete parses and GLR was picking between them on
    // DYNAMIC precedence, which this rule does not participate in — the losing
    // reading uses plain `if_statement` without its else arm, not this variant.
    // The fix is in if_statement: the ';' now decides structurally, and the
    // else arm carries prec.dynamic(20) to win the tie that remains.
    _if_statement_no_else: $ => prec.dynamic(10, seq(
      $.if_keyword,
      field('condition', $._expression),
      $.then_keyword,
      $._then_branch,
    )),

    // Shared then-branch body: a complete code_block or single statement.
    // Each of these carries its own field() internally rather than being
    // fielded at the call site, so the ';' that `_statement` owns stays out of
    // the field. See fieldedStatement().
    //
    // There used to be a second, near-identical `_then_branch_no_semi` for
    // if_statement's use, with a declared conflict between the pair. The
    // terminator restructure made them the same rule: no then-branch form
    // carries a ';' any more, so there is nothing left for the two variants to
    // differ on.
    _then_branch: $ => fieldedStatement($, 'then_branch'),

    // Shared else-branch body: code_block, nested if (else-if chain), or single statement
    _else_branch: $ => choice(
      prec(1, field('else_branch', $.if_statement)),
      fieldedStatement($, 'else_branch'),
    ),

    // else-branch without the else-if chain (preproc split if-else shared tail)
    _else_branch_simple: $ => fieldedStatement($, 'else_branch'),

    // Loop / with body: a code_block or a single statement
    _body_branch: $ => fieldedStatement($, 'body'),

    // Case-branch body: also admits a dangling-else-free nested if
    _case_body_branch: $ => choice(
      field('body', alias($._if_statement_no_else, $.if_statement)),
      fieldedStatement($, 'body'),
    ),

    // --- Case ---

    case_statement: $ => prec(2, seq(
      $.case_keyword,
      field('expression', $._expression),
      $.of_keyword,
      optional(field('body', $.case_body)),
      optional($.case_else_branch),
      $.end_keyword
    )),

    case_body: $ => repeat1(choice(
      $.case_branch,
      $.preproc_conditional_case,
      $.preproc_split_case_extended,
    )),

    // Preprocessor conditionals inside case statements
    preproc_conditional_case: $ => seq(
      $.preproc_if,
      repeat($.case_branch),
      optional($.case_else_branch),
      repeat(seq($.preproc_elif, repeat($.case_branch), optional($.case_else_branch))),
      optional(seq($.preproc_else, repeat($.case_branch), optional($.case_else_branch))),
      $.preproc_endif,
    ),

    // A case branch is its own terminator scope: nothing encloses it that would
    // take the ';' (the case's own ';' comes after `end`), so it takes the one
    // that `fieldedStatement`/`code_block` stopped carrying. This is also what
    // hands the else to the case in `case 1: if C then A; else B; end;` — the
    // branch consumes that ';', which is only reachable once the inner
    // if_statement has reduced without its else.
    case_branch: $ => choice(
      seq(
        $._case_pattern,
        ':',
        $._case_body_branch,
        optional(';'),
      ),
      // Preprocessor-split case branch: #if wraps extra patterns before the main pattern
      // #if COND  pattern1,  #endif  pattern2: body;
      $.preproc_split_case_branch,
    ),

    // Case branch where some patterns are conditionally included via preprocessor
    preproc_split_case_branch: $ => prec(25, seq(
      $.preproc_if,
      repeat($._case_pattern_item),
      repeat(seq(
        $.preproc_elif,
        repeat($._case_pattern_item),
      )),
      optional(seq(
        $.preproc_else,
        repeat($._case_pattern_item),
      )),
      $.preproc_endif,
      // Pattern(s) after the preprocessor block, ending with ':'
      $._case_pattern,
      ':',
      $._case_body_branch,
      optional(';'),
    )),

    // Extended case split: #if adds complete branches + provides header for next shared branch
    // Example: #if DOSMTP  1: begin DoSMTP(); end;  2:  #else  2, 1:  #endif  begin DoEmail(); end;
    preproc_split_case_extended: $ => prec(25, seq(
      $.preproc_if,
      repeat($.case_branch),  // zero or more complete extra branches
      $._case_pattern,        // header-only for the next branch
      ':',
      repeat(seq(
        $.preproc_elif,
        repeat($.case_branch),
        $._case_pattern,
        ':',
      )),
      optional(seq(
        $.preproc_else,
        repeat($.case_branch),
        $._case_pattern,
        ':',
      )),
      $.preproc_endif,
      // Shared body for the split branch
      $._case_body_branch,
      optional(';'),
    )),

    // Case pattern list: supports preprocessor conditionals interleaved with patterns.
    _case_pattern: $ => repeat1(choice(
      $._case_pattern_item,
      $.preproc_conditional_case_patterns,
    )),

    // One case-pattern value (+ an optional trailing comma). The `pattern` field lives
    // HERE, on the value node — never on the `,`/`:` separators. The previous shape
    // wrapped the whole inlined `_case_pattern` list in `field('pattern', …)`, which
    // distributed the field over the comma tokens too, so `children_by_field('pattern')`
    // returned anonymous `,` nodes (the owned-IR lowerer panicked on `case 1, 2:`).
    _case_pattern_item: $ => seq(field('pattern', $._single_pattern), optional(',')),

    // Preprocessor conditional wrapping case pattern entries mid-list
    preproc_conditional_case_patterns: $ => seq(
      $.preproc_if,
      repeat($._case_pattern_item),
      repeat(seq(
        $.preproc_elif,
        repeat($._case_pattern_item),
      )),
      optional(seq(
        $.preproc_else,
        repeat($._case_pattern_item),
      )),
      $.preproc_endif,
    ),

    _single_pattern: $ => choice(
      $._literal_value,
      $.qualified_enum_value,
      $.database_reference,
      $.range_expression,
      $.call_expression,
      $.identifier,
      $.quoted_identifier,
      $.member_expression,
      $.unary_expression,
      $.parenthesized_expression,
      $.keyword_identifier,
      // Expressions as case patterns (case true of: X > 0: ...)
      $.comparison_expression,
      $.logical_expression,
      $.additive_expression,
      $.multiplicative_expression,
      $.subscript_expression,
      // In expression as case pattern (case true of: X in [...]: ...). The NAMED
      // `in_expression` (not an inline seq) keeps the `pattern` field a single value
      // instead of spreading it over left/operator/right.
      $.in_expression,
    ),

    case_else_branch: $ => prec.left(seq(
      $.else_keyword,
      // body is ONE node, never a raw repeat — a fielded repeat($._statement)
      // makes body multiple:true and drags the anonymous ';' into the field,
      // breaking the single-node body invariant the textobject queries rely on
      // (issue #19). repeat_statement already uses statement_block this way.
      // optional() preserves `else` with zero statements before `end` (see
      // "Empty case else branch" in test/corpus/case_statement.txt) — neither
      // code_block nor statement_block (repeat1) can match an empty body.
      // The two arms are separate because only the code_block one needs a
      // terminator of its own: `code_block` stopped owning the ';' after its
      // `end` (see the note there), while `statement_block` is a run of
      // `_statement`, each of which already takes its own. Folding them back
      // into one `choice` under a shared trailing `optional(';')` would make
      // `else A;` ambiguous between the two owners of that ';'.
      optional(field('body', $.statement_block))
    )),

    // --- For loop ---

    for_statement: $ => prec.right(seq(
      $.for_keyword,
      field('variable', choice(
        $.identifier,
        $.quoted_identifier,
        $.member_expression,
      )),
      ':=',
      field('start', $._expression),
      field('direction', choice(
        $.to_keyword,
        $.downto_keyword,
      )),
      field('end', $._expression),
      $.do_keyword,
      $._body_branch
    )),

    // --- Foreach ---

    foreach_statement: $ => prec.right(seq(
      $.foreach_keyword,
      field('variable', choice($.identifier, $.quoted_identifier)),
      $.in_keyword,
      field('iterable', $._expression),
      $.do_keyword,
      $._body_branch
    )),

    // --- While ---

    while_statement: $ => prec.right(seq(
      $.while_keyword,
      field('condition', $._expression),
      $.do_keyword,
      $._body_branch
    )),

    // --- Repeat/Until ---

    repeat_statement: $ => seq(
      $.repeat_keyword,
      optional(field('body', $.statement_block)),
      $.until_keyword,
      field('condition', $._expression)
    ),

    // --- With ---

    with_statement: $ => prec.right(seq(
      $.with_keyword,
      field('record', $._expression),
      $.do_keyword,
      $._body_branch
    )),

    // --- Exit ---

    // The '(' is a PLAIN literal, never token.immediate — alc accepts
    // `exit (42);` and with token.immediate the spaced form parsed SILENTLY as
    // a bare exit_statement plus a detached sibling parenthesized_expression,
    // dropping the return value with no ERROR node.
    //
    // The two forms are separate choice alternatives with DIFFERENT precedences
    // rather than one seq with an optional group. `exit` followed by `(` is
    // genuinely ambiguous (continue the exit vs. reduce and start a
    // parenthesized-expression statement) and the parenthesised alternative
    // must win. The precedence has to sit ON the alternative: prec() nested
    // inside optional() does not reach the conflicting item, so the single-seq
    // shape leaves the conflict unresolved. Other resolutions (e.g. a declared
    // `conflicts` entry) may also work — this is the one that does, not the
    // only one that could. Both alternatives are pinned by
    // test/corpus/exit_statement_spacing_test.txt; the prec(14) arm is the one
    // that can silently start swallowing a following parenthesized-expression
    // statement, so keep that fixture green.
    exit_statement: $ => choice(
      prec(14, seq(
        $.exit_keyword,
        '(',
        optional(field('return_value', $._expression)),
        ')'
      )),
      prec(13, $.exit_keyword)
    ),

    // --- Continue / Break ---

    continue_statement: $ => prec(13, $.continue_keyword),
    break_statement: $ => prec(13, $.break_keyword),

    // --- Asserterror ---

    asserterror_statement: $ => prec.right(14, seq(
      $.asserterror_keyword,
      optional(field('body', choice(
        $._expression,
        $.code_block,
      )))
    )),

    // =====================================================================
    // Expressions
    // =====================================================================

    // In / Is / As expressions — NAMED so their left/operator/right fields stay
    // contained on these nodes instead of bleeding onto every node that holds an
    // _expression (owned-IR consumer request).
    in_expression: $ => prec.left(5, seq(
      field('left', $._expression),
      field('operator', $.in_keyword),
      field('right', $.list_literal)
    )),
    is_expression: $ => prec.left(5, seq(
      field('left', $._expression),
      field('operator', $.is_keyword),
      field('right', $.type_specification)
    )),
    as_expression: $ => prec.left(5, seq(
      field('left', $._expression),
      field('operator', $.as_keyword),
      field('right', $.type_specification)
    )),

    _expression: $ => choice(
      // Binary operators
      $.multiplicative_expression,
      $.additive_expression,
      $.comparison_expression,
      $.logical_expression,
      $.in_expression,
      $.is_expression,
      $.as_expression,
      // Other expression forms
      $.qualified_enum_value,
      $.database_reference,
      $.call_expression,
      $.member_expression,
      $.subscript_expression,
      $.identifier,
      $.quoted_identifier,
      $._literal_value,
      $.parenthesized_expression,
      $.unary_expression,
      $.list_literal,
      // Keywords that can be used as identifiers in expressions
      $.keyword_identifier,
      // 'continue' as identifier when followed by ':='
      alias($.continue_as_identifier, $.identifier),
      // Ternary expression: condition ? then_value : else_value
      $.ternary_expression,
      // Assignment as expression (for asserterror and other contexts)
      prec.left(1, $.assignment_expression),
    ),

    // Keywords that can appear as identifiers in expressions (e.g., Codeunit.Run())
    //
    // All thirteen alternatives are named keyword rules, so `keyword_identifier`
    // has ONE shape: exactly one named `*_keyword` child.
    //
    // Seven of them used to be bare `kw()`. A bare kw() is a token(PATTERN),
    // which tree-sitter renders as a HIDDEN symbol, so `keyword_identifier` came
    // out two different ways depending only on which word the source used:
    //
    //   Codeunit.Run()  ->  (keyword_identifier (codeunit_keyword))
    //   Record.Get()    ->  (keyword_identifier)          <- childless leaf
    //
    // Not a byte gap — `keyword_identifier` itself covers the bytes either way,
    // which is why the query-coverage harness reported nothing and this outlived
    // the losslessness work. It was a SHAPE inconsistency: a consumer asking
    // "which keyword is this?" by descending into the child got an answer for six
    // spellings and nothing for the other seven.
    //
    // Aliasing does NOT change what the token matches. kw(w) is
    // token(RustRegex('(?i)w')) and alias() wraps that same token, so these seven
    // stayed exactly as case-insensitive as they already were and no spelling
    // moved between `identifier` and `keyword_identifier`. That is the reason the
    // kwCases() whitelist argument does not apply here: kwCases() exists to stop
    // kw() from WIDENING a compound keyword over spellings AL uses as
    // identifiers, and nothing here widens anything.
    keyword_identifier: $ => prec(-5, choice(
      $.codeunit_keyword,
      $.page_keyword,
      $.report_keyword,
      $.query_keyword,
      $.xmlport_keyword,
      $.record_keyword,
      $.enum_keyword,
      $.system_keyword,
      $.session_keyword,
      $.dialog_keyword,
      $.database_keyword,
      $.file_keyword,
      $.action_keyword,
    )),

    // --- Range ---
    //
    // `..` is NOT an expression operator in AL, and this rule is deliberately
    // absent from `_expression`. Compiler-measured: a parenthesised range as an
    // operand of `+` is `AL0104: Syntax error, ')' expected` — a SYNTAX error,
    // not a type error, so `1 + (1 .. 4)` has no reading at all. Ranges occur
    // only as a whole list-literal element (`x in [1 .. 5]`) or a whole case
    // pattern (`1 .. 5:`), which is exactly what the corpus shows: of the 141
    // `range_expression` nodes in BC.History, 103 sit under `list_literal` and
    // 34 under `case_branch`.
    //
    // It USED to be `prec.left(8)` inside `_expression`, i.e. binding tighter
    // than both `multiplicative_expression` (7) and `additive_expression` (6),
    // which is the exact inverse of the compiler. That produced four
    // meaning-changing misparses in BC.History, all silent — every byte covered,
    // no ERROR node, no node type changed:
    //
    //   0D .. NextCountingStartDate - 1   parsed as (0D .. NextCountingStartDate) - 1
    //   Round(Qty / 2, 1) + 1 .. Qty      parsed as Round(...) + (1 .. Qty)
    //   [-MaximumSetLength .. 0]          parsed as -(MaximumSetLength .. 0)   (x2)
    //
    // Keeping it out of `_expression` rather than lowering its precedence number
    // makes those trees UNREPRESENTABLE instead of merely disfavoured: with no
    // range in `_expression`, a `unary_expression` operand cannot be a range at
    // all, so the last two have only one derivation. A precedence number would
    // leave both trees reachable and rely on the number staying correct.
    //
    // The precedence still matters, for a DIFFERENT decision than the one it
    // used to make. Removing the rule from `_expression` fixes the `left`
    // operand and the unary case, but not the `right` one: at `0D ..
    // NextCountingStartDate - 1` the parser reaches `-` holding a complete
    // `right`, and must choose between reducing `range_expression` and shifting
    // into `additive_expression`. At 8 the reduce won, and because
    // `_case_pattern_item`'s comma is optional the leftover `- 1` was silently
    // accepted as a SECOND case pattern — a different wrong tree, still with no
    // ERROR node. It must be BELOW every operator that can appear inside an
    // operand (additive 6, comparison 4, logical 2/3), so 0: a range's operands
    // extend as far as they can, which is what makes `..` outermost.
    range_expression: $ => prec.left(0, seq(
      field('left', $._expression),
      '..',
      field('right', $._expression)
    )),

    // --- Binary expressions ---

    multiplicative_expression: $ => prec.left(7, seq(
      field('left', $._expression),
      // alias() pins the anonymous node name so queries keep matching "div"
      // and "mod" whatever the source casing. Without it a bare kw() token is
      // auto-named multiplicative_expression_token1.
      field('operator', choice('*', '/', alias(kw('div'), 'div'), alias(kw('mod'), 'mod'))),
      field('right', $._expression)
    )),

    additive_expression: $ => prec.left(6, seq(
      field('left', $._expression),
      field('operator', choice('+', '-')),
      field('right', $._expression)
    )),

    // 2, BELOW `and` (4) and `or`/`xor` (3). AL is Pascal-derived and the
    // logical operators bind TIGHTER than the comparisons — the exact inverse
    // of what this rule declared until now, and the reason every BC codebase
    // writes `if (a = b) and (c = d) then` with parentheses that look
    // redundant and are not.
    //
    // Compiler-measured with alc 18.0.37.11445. Accept/reject cannot
    // discriminate `and`/`or`/`xor` grouping — every operand must be Boolean
    // under either reading — so this uses the operand-type message, which
    // names the operator AND the order of the types:
    //
    //   b := 1 = 1 and 2 = 2;   AL0175 Operator 'and' … 'Integer' and 'Integer'
    //   b := 1 < 2 and 3 < 4;   AL0175 Operator 'and' … 'Integer' and 'Integer'
    //   b := 1 < 2 or 3 < 4;    AL0175 Operator 'or'  … 'Integer' and 'Integer'
    //   b := 1 <> 2 xor 3 <> 4; AL0175 Operator 'xor' … 'Integer' and 'Integer'
    //   b := (1 = 1) and (2 = 2);  ACCEPT                              (control)
    //
    // `'Integer' and 'Integer'` is producible only by `1 and 2`, i.e. alc read
    // `1 = (1 and 2) = 2`, and the parenthesised control compiles — so the
    // instrument discriminates. Both directions were probed:
    //
    //   b := 1 = 1 and true;    'and' 'Integer' and 'Boolean' => 1 = (1 and true)
    //   b := true and 1 = 1;    'and' 'Boolean' and 'Integer' => (true and 1) = 1
    //
    // The two groupings are NOT equivalent. With A, B, C all Boolean and all
    // false, `A = B and C` is TRUE under the compiler and was FALSE here.
    //
    // Only 3 BC.History sites write an unparenthesised comparison as an operand
    // of a logical operator, and all three are the `… and X = true` idiom where
    // the two readings happen to agree. That is luck, not safety.
    comparison_expression: $ => prec.left(2, seq(
      field('left', $._expression),
      field('operator', $.comparison_operator),
      field('right', $._expression)
    )),

    comparison_operator: $ => choice(
      '>=',
      '<=',
      '>',
      '<',
      '<>',
      '='
    ),

    // Measured ladder: `and` binds tighter than `or`/`xor`, which are one level
    // and left-associative, and all three bind tighter than the comparisons.
    // Only the last part changed here — the relative order of the three was
    // already right, confirmed by six alc probes (`true or 1 and true` reports
    // 'and', `true or 1 xor true` reports 'or', and so on).
    logical_expression: $ => choice(
      // AND (prec 4) — above OR/XOR, below `in`/`is`/`as` (5)
      prec.left(4, seq(
        field('left', $._expression),
        field('operator', alias(kw('and'), 'and')),
        field('right', $._expression)
      )),
      // OR (prec 3)
      prec.left(3, seq(
        field('left', $._expression),
        field('operator', alias(kw('or'), 'or')),
        field('right', $._expression)
      )),
      // XOR (prec 3) — same level as OR, so `a or b xor c` is `(a or b) xor c`
      prec.left(3, seq(
        field('left', $._expression),
        field('operator', alias(kw('xor'), 'xor')),
        field('right', $._expression)
      )),
    ),

    // --- Ternary expression ---
    // condition ? then_value : else_value
    ternary_expression: $ => prec.right(1, seq(
      field('condition', $._expression),
      '?',
      field('then_value', $._expression),
      ':',
      field('else_value', $._expression)
    )),

    // --- Unary expression ---

    // 8, not 7. It was 7 — the SAME level as `multiplicative_expression` — and
    // because this rule is prec.RIGHT while that one is prec.LEFT, the unary won
    // every tie: `-2 * 3` parsed as `-(2 * 3)`, and `-Amount * "Bal. VAT %"` as
    // `-(Amount * "Bal. VAT %")`. 629 sites in 193 BC.History files.
    //
    // Compiler-measured with alc: the operand-type message names which operator
    // received the mismatched pair, which pins the grouping exactly.
    //
    //   i := -b * 2;      AL0173  Operator '-' cannot be applied to an operand
    //                             of type 'Boolean'      => (-b) * 2
    //   i := -b div 2;    AL0173  same                   => (-b) div 2
    //   i := -b mod 2;    AL0173  same                   => (-b) mod 2
    //   i := -(b * 2);    AL0175  Operator '*' ... 'Boolean' and 'Integer'   (control)
    //   i := (-b) * 2;    AL0173  Operator '-' ... 'Boolean'                 (control)
    //
    // The two controls flip, so the instrument discriminates.
    //
    // 8 puts it strictly between `multiplicative_expression` (7) and
    // `subscript_expression` (9), which is the measured AL ladder: postfix
    // (`.` 11, `[]` 9, `()` 12) binds tighter than unary, unary tighter than
    // `* / div mod`. `-x.y`, `-a[1]` and `-f(1)` therefore keep grouping the
    // postfix first, as they already did.
    //
    // No AL value changes: over truncating integer division and decimal
    // arithmetic `-(a op b) == (-a) op b` for `*`, `/`, `div` and `mod` alike.
    // The TREE was wrong, not the arithmetic — which is precisely why nothing
    // caught it. `not X * Y` is never valid AL under either grouping, so only
    // the arithmetic unaries reach real code.
    unary_expression: $ => prec.right(8, seq(
      field('operator', choice('+', '-', alias(kw('not'), 'not'))),
      field('operand', $._expression)
    )),

    // --- Postfix expressions ---

    call_expression: $ => prec(12, seq(
      field('function', choice(
        $.identifier,
        $.quoted_identifier,      // "My Proc"(42) — alc accepts; call_statement
                                  // already allowed this, call_expression did not
        $.member_expression,
        $.qualified_enum_value,
        $.keyword_identifier,     // System(), Dialog(), etc.
        $.subscript_expression,   // X[1]()
      )),
      field('arguments', $.argument_list)
    )),

    argument_list: $ => seq(
      '(',
      optional($._expression_list),
      ')'
    ),

    // Comma-separated expression list — a complete unit bounded by the caller's delimiter
    _expression_list: $ => seq(
      $._expression,
      repeat(seq(',', $._expression))
    ),

    member_expression: $ => prec.left(11, seq(
      field('object', $._expression),
      '.',
      field('member', $._identifier_or_quoted)
    )),

    subscript_expression: $ => prec.left(9, seq(
      field('object', $._expression),
      '[',
      field('index', $._expression),
      repeat(seq(',', $._expression)),
      ']'
    )),

    parenthesized_expression: $ => seq(
      '(',
      $._expression,
      ')'
    ),

    // --- List literal ---

    // A list literal is the one expression context where a range is legal, so it
    // takes `_list_element` rather than `_expression_list`. `argument_list` keeps
    // `_expression_list` — `f(1 .. 5)` is not AL.
    list_literal: $ => seq(
      '[',
      optional(seq($._list_element, repeat(seq(',', $._list_element)))),
      ']'
    ),

    _list_element: $ => choice(
      $.range_expression,
      $._expression,
    ),

    // --- Qualified enum value ---
    // Status::Active, Enum::"Sales Line Type"::Item

    qualified_enum_value: $ => prec.left(50, seq(
      field('enum_type', choice(
        $.identifier,
        $.quoted_identifier,
        $.member_expression,
        $.subscript_expression,  // Allow X[1]::Value
        $.call_expression,       // Allow Func()::Value
        $.qualified_enum_value,  // Chained: Enum::"Type"::"Value"
        $.keyword_identifier,    // Allow Enum::, Record::, etc.
      )),
      '::',
      field('value', $._identifier_or_quoted)
    )),

    // --- Database reference ---
    // DATABASE::"Customer"

    // `database` is aliased to a visible STRING exactly like the five named
    // alternatives beside it, so `object_type_keyword` has ONE shape.
    //
    // It used to be a bare `kw('database')`. That builds a token(PATTERN), which
    // tree-sitter renders as a HIDDEN symbol, while the five `$.*_keyword` rules
    // carry visible aliased STRING tokens -- so the same node type came out two
    // different ways:
    //
    //   (object_type_keyword text='Page')      children=[("page", anonymous)]
    //   (object_type_keyword text='DATABASE')  children=[]          <- childless
    //
    // Not a byte gap: the outer alias() covers the bytes, so the CST stayed
    // lossless and the query-coverage harness reported nothing. It was a SHAPE
    // inconsistency, and a consumer that descended into the child got nothing
    // for every DATABASE:: in the corpus while its five siblings worked.
    //
    // Scale, at BC.History scope (15,358 .al files): 22,988 of 40,674
    // `object_type_keyword` nodes were the childless kind. Quote the NODE count,
    // not a grep: the 23,065 textual `database::` occurrences in those files
    // resolve as 22,988 object_type_keyword + 75 comment + 2 string_literal
    // (measured, not subtracted), and the last 77 never become one of these
    // nodes at all.
    //
    // DO NOT "SIMPLIFY" THIS BY NESTING THE ALIASES. The obvious one-liner
    //
    //     alias(alias(kw('database'), 'database'), $.object_type_keyword)
    //
    // looks equivalent and is not: the two aliases do not compose. The inner one
    // wins, the DATABASE case loses its `object_type_keyword` node ENTIRELY, and
    // the `keyword` field then points straight at an anonymous token -- strictly
    // worse than the childless node this replaced, because the node type
    // disappears rather than merely varying. A named rule is what makes the outer
    // alias see the same thing it sees for the other five. That was the first
    // attempt here; test/corpus/object_type_keyword_uniform_shape_test.txt fails
    // on exactly it, but a failing fixture tells you THAT the nested form is
    // wrong, not why, which is what this paragraph is for.
    //
    // Reading a keyword's text from the node itself still works for both shapes
    // and remains the advice; this just removes the need for it here.
    database_reference: $ => prec(300, seq(
      field('keyword', alias(
        choice(
          $.database_keyword,
          $.page_keyword,
          $.report_keyword,
          $.codeunit_keyword,
          $.xmlport_keyword,
          $.query_keyword,
        ),
        $.object_type_keyword
      )),
      '::',
      field('table_name', choice($._identifier_or_quoted, $.integer))
    )),

    // --- Literal values ---

    _literal_value: $ => choice(
      $.integer,
      $.decimal,
      $.boolean,
      $.string_literal,
      $.verbatim_string,
      $.datetime_literal,
      $.date_literal,
      $.time_literal,
      $.biginteger_literal,
    ),

    // DateTime: 0DT or YYYYMMDDTHHmmssZ
    datetime_literal: $ => token(prec(2, choice(
      /\d+DT/,
      new RustRegex('\\d{8}T\\d{6}[A-Z]?'),
    ))),

    // Date: 0D or YYYYMMDD
    date_literal: $ => token(prec(1, /\d+D/)),

    // Time: 0T or HHmmssT or HHmmss.mmmT
    time_literal: $ => token(prec(2, choice(
      /\d+\.\d+T/,  // Decimal time: 235959.999T
      /\d+T/,        // Integer time: 000000T, 0T
    ))),

    // BigInteger: 1000L
    biginteger_literal: $ => token(prec(1, /\d+L/)),

    // =====================================================================
    // Named keyword rules
    // =====================================================================

    // --- Tier 1: Control flow ---

    // AL is fully case-insensitive. Spelling out three casings meant `iF`,
    // `tHEN`, `eLSe` — all legal AL, all accepted by alc — failed, and because
    // _statement carries optional(';') the failure was SILENT: the if-structure
    // collapsed into a flat statement run with no ERROR node. kw() is a
    // case-insensitive regex; asserterror_keyword already used this form.
    //
    // The 10 stays OUTSIDE kw() so it remains *parse* precedence, exactly as
    // the old prec(10, choice('if','IF','If')) had it. kw('in', 10) would put
    // it inside token(), making it *lexical*, where it outranks the prec-0
    // `integer` token in the keyword lexer and stops `Integer` from ever
    // matching past `In` — silently demoting basic_type to identifier.
    //
    // alias() keeps the anonymous lowercase child. A named rule whose whole
    // body is a single token collapses INTO that token, so a bare kw() would
    // turn if_keyword into a childless leaf and delete the anonymous "if" node
    // type that queries and tree-walkers rely on (see CLAUDE.md § Keyword
    // Architecture, which uses exit_keyword as its worked example). One alias
    // per keyword now covers every source casing.
    if_keyword: $ => prec(10, alias(kw('if'), 'if')),
    then_keyword: $ => prec(10, alias(kw('then'), 'then')),
    else_keyword: $ => prec(10, alias(kw('else'), 'else')),
    case_keyword: $ => prec(10, alias(kw('case'), 'case')),
    of_keyword: $ => prec(10, alias(kw('of'), 'of')),
    for_keyword: $ => prec(10, alias(kw('for'), 'for')),
    foreach_keyword: $ => prec(10, alias(kw('foreach'), 'foreach')),
    while_keyword: $ => prec(10, alias(kw('while'), 'while')),
    do_keyword: $ => prec(10, alias(kw('do'), 'do')),
    repeat_keyword: $ => prec(10, alias(kw('repeat'), 'repeat')),
    until_keyword: $ => prec(10, alias(kw('until'), 'until')),
    exit_keyword: $ => prec(10, alias(kw('exit'), 'exit')),
    continue_keyword: $ => prec(10, alias(kw('continue'), 'continue')),
    break_keyword: $ => prec(10, alias(kw('break'), 'break')),
    with_keyword: $ => prec(10, alias(kw('with'), 'with')),
    asserterror_keyword: $ => alias(kw('asserterror', 10), 'asserterror'),
    in_keyword: $ => prec(10, alias(kw('in'), 'in')),
    to_keyword: $ => prec(10, alias(kw('to'), 'to')),
    downto_keyword: $ => prec(10, alias(kw('downto'), 'downto')),

    // --- Tier 2: Object types ---

    table_keyword: $ => alias(kw('table'), 'table'),
    tableextension_keyword: $ => prec(10, kwCases('tableextension', 'tableextension', 'TABLEEXTENSION', 'Tableextension', 'TableExtension', 'tableExtension')),
    // `database` in `DATABASE::"Customer"`. A real keyword rule rather than a
    // bare kw(), so that database_reference's outer alias() to
    // object_type_keyword sees the same thing it sees for the five siblings
    // beside it and produces the SAME node shape. See database_reference.
    database_keyword: $ => alias(kw('database'), 'database'),

    // The other six words `keyword_identifier` accepts. Named rules for the same
    // reason as database_keyword: so that rule has one shape instead of two.
    //
    // Only THREE are defined here. `record_keyword`, `action_keyword` and
    // `system_keyword` live with their own construct groups further down,
    // because the losslessness pass gave the basic_type, action_declaration and
    // property sites named rules of their own — so those three words are now
    // SHARED between both uses rather than defined twice.
    //
    // That sharing is not optional. A grammar.js rule table is a JS object
    // literal, so a duplicate key is silently accepted and the LAST definition
    // wins: `tree-sitter generate` succeeds, the parser is correct, and nothing
    // reports it. Merging this branch with the losslessness branch produced
    // exactly that — three words defined twice with identical bodies, caught
    // only by re-deriving the keyword count and finding 155 rule lines against
    // 152 unique names. `validate-grammar.sh`'s duplicate-key check is what
    // gates it now; do not add a second definition of a keyword that already
    // has one somewhere else in this file.
    //
    // The earlier claim here — that these are "deliberately NOT reused by the
    // basic_type / record_type / action_declaration sites, which keep their own
    // bare kw()" — was true on this branch alone and is void after the merge.
    // Those sites are exactly what closed the `record`/`code`/`text` byte gaps.
    session_keyword: $ => alias(kw('session'), 'session'),
    dialog_keyword: $ => alias(kw('dialog'), 'dialog'),
    file_keyword: $ => alias(kw('file'), 'file'),

    page_keyword: $ => alias(kw('page'), 'page'),
    pageextension_keyword: $ => prec(10, kwCases('pageextension', 'pageextension', 'PAGEEXTENSION', 'Pageextension', 'PageExtension', 'pageExtension')),
    codeunit_keyword: $ => prec(10, kwCases('codeunit', 'codeunit', 'CODEUNIT', 'Codeunit', 'CodeUnit', 'COdeunit', 'codeUnit')),
    report_keyword: $ => alias(kw('report'), 'report'),
    reportextension_keyword: $ => prec(10, kwCases('reportextension', 'reportextension', 'REPORTEXTENSION', 'Reportextension', 'ReportExtension', 'reportExtension')),
    query_keyword: $ => alias(kw('query'), 'query'),
    xmlport_keyword: $ => prec(10, kwCases('xmlport', 'xmlport', 'XMLPORT', 'Xmlport', 'XMLport', 'XMLPort', 'XmlPort')),
    enum_keyword: $ => prec(10, kwCases('enum', 'enum', 'ENUM', 'Enum', 'eNUM', 'eNum', 'ENum')),
    enumextension_keyword: $ => prec(10, kwCases('enumextension', 'enumextension', 'ENUMEXTENSION', 'Enumextension', 'EnumExtension', 'enumExtension')),
    interface_keyword: $ => alias(kw('interface'), 'interface'),
    controladdin_keyword: $ => prec(10, kwCases('controladdin', 'controladdin', 'CONTROLADDIN', 'Controladdin', 'ControlAddIn', 'ControlAddin', 'controlAddIn', 'controlAddin')),
    dotnet_keyword: $ => prec(10, kwCases('dotnet', 'dotnet', 'DOTNET', 'Dotnet', 'DotNet', 'dotNet')),
    profile_keyword: $ => alias(kw('profile'), 'profile'),
    profileextension_keyword: $ => prec(10, kwCases('profileextension', 'profileextension', 'PROFILEEXTENSION', 'Profileextension', 'ProfileExtension', 'profileExtension')),
    permissionset_keyword: $ => prec(10, kwCases('permissionset', 'permissionset', 'PERMISSIONSET', 'Permissionset', 'PermissionSet', 'permissionSet')),
    permissionsetextension_keyword: $ => prec(10, kwCases('permissionsetextension', 'permissionsetextension', 'PERMISSIONSETEXTENSION', 'Permissionsetextension', 'PermissionSetExtension', 'permissionSetExtension')),
    entitlement_keyword: $ => alias(kw('entitlement'), 'entitlement'),
    pagecustomization_keyword: $ => prec(10, kwCases('pagecustomization', 'pagecustomization', 'PAGECUSTOMIZATION', 'Pagecustomization', 'PageCustomization', 'pageCustomization')),
    namespace_keyword: $ => alias(kw('namespace'), 'namespace'),
    using_keyword: $ => alias(kw('using'), 'using'),
    implements_keyword: $ => alias(kw('implements'), 'implements'),
    extends_keyword: $ => alias(kw('extends'), 'extends'),
    customizes_keyword: $ => alias(kw('customizes'), 'customizes'),

    // --- Tier 3: Declarations & modifiers ---

    procedure_keyword: $ => alias(kw('procedure'), 'procedure'),
    trigger_keyword: $ => alias(kw('trigger'), 'trigger'),
    var_keyword: $ => alias(kw('var'), 'var'),
    local_keyword: $ => alias(kw('local'), 'local'),
    internal_keyword: $ => alias(kw('internal'), 'internal'),
    protected_keyword: $ => alias(kw('protected'), 'protected'),
    event_keyword: $ => alias(kw('event'), 'event'),
    temporary_keyword: $ => alias(kw('temporary'), 'temporary'),

    // --- Tier 3: Sections ---

    fields_keyword: $ => alias(kw('fields'), 'fields'),
    keys_keyword: $ => alias(kw('keys'), 'keys'),
    key_keyword: $ => alias(kw('key'), 'key'),
    fieldgroups_keyword: $ => alias(kw('fieldgroups'), 'fieldgroups'),
    fieldgroup_keyword: $ => alias(kw('fieldgroup'), 'fieldgroup'),
    actions_keyword: $ => alias(kw('actions'), 'actions'),
    layout_keyword: $ => alias(kw('layout'), 'layout'),
    area_keyword: $ => alias(kw('area'), 'area'),
    group_keyword: $ => alias(kw('group'), 'group'),
    repeater_keyword: $ => alias(kw('repeater'), 'repeater'),
    cuegroup_keyword: $ => alias(kw('cuegroup'), 'cuegroup'),
    fixed_keyword: $ => alias(kw('fixed'), 'fixed'),
    grid_keyword: $ => alias(kw('grid'), 'grid'),
    part_keyword: $ => alias(kw('part'), 'part'),
    systempart_keyword: $ => alias(kw('systempart'), 'systempart'),
    usercontrol_keyword: $ => alias(kw('usercontrol'), 'usercontrol'),
    dataset_keyword: $ => alias(kw('dataset'), 'dataset'),
    elements_keyword: $ => alias(kw('elements'), 'elements'),
    dataitem_keyword: $ => alias(kw('dataitem'), 'dataitem'),
    column_keyword: $ => alias(kw('column'), 'column'),
    // where()/field()/const()/upperlimit() markers, named in 4.0.0. filter_keyword
    // below was already correct and sat in the SAME choice() as these three, which
    // is how the inconsistency stayed invisible: `filter(...)` produced a node and
    // its siblings produced nothing. All four were bare kw(), i.e. token(PATTERN),
    // which tree-sitter hides — so `where(X = field(N))`, `where(X = const(N))` and
    // `where(X = upperlimit(N))` produced BYTE-IDENTICAL subtrees. That is a
    // semantic misread, not a cosmetic one: const(N) is the literal N, field(N) is
    // the value of field N in the current record, and upperlimit(N) is a range
    // bound. Three different database queries, one tree.
    //
    // field_keyword covers BOTH the where/link marker and the field DECLARATION
    // keyword (field_declaration, page_field, _field_header, _table_field_header).
    // It was marker-only until the losslessness pass: the declaration sites were
    // bare kw('field') and dropped 83,885 keyword occurrences across BC.History.
    // One rule for one word — the constructs are told apart by the parent node,
    // never by the keyword's own type. keyword_as_identifier keeps its bare
    // kw('field'): that alternative is a choice arm with no visible sibling, so
    // the aliased-to-identifier node is itself the leaf covering those bytes.
    //
    // where_keyword keeps kw()'s second argument: it promotes parse precedence to
    // LEXICAL precedence, and dropping it can make other rules unreachable.
    where_keyword: $ => alias(kw('where', 15), 'where'),
    field_keyword: $ => alias(kw('field'), 'field'),
    const_keyword: $ => alias(kw('const'), 'const'),
    upperlimit_keyword: $ => alias(kw('upperlimit'), 'upperlimit'),
    filter_keyword: $ => alias(kw('filter'), 'filter'),
    labels_keyword: $ => alias(kw('labels'), 'labels'),
    rendering_keyword: $ => alias(kw('rendering'), 'rendering'),
    requestpage_keyword: $ => alias(kw('requestpage'), 'requestpage'),
    schema_keyword: $ => alias(kw('schema'), 'schema'),
    views_keyword: $ => alias(kw('views'), 'views'),
    analysisviews_keyword: $ => alias(kw('analysisviews'), 'analysisviews'),
    analysisview_keyword: $ => alias(kw('analysisview'), 'analysisview'),
    view_keyword: $ => alias(kw('view'), 'view'),

    // Section/element-type keywords, added in 4.0.0. Each of these sat inside a
    // field() as a bare kw(), which is a token(PATTERN) and therefore an
    // invisible aux_sym_* — the bytes were consumed and the FIELD silently
    // vanished. Routing them through a named rule (the same alias(kw(),'') shape
    // as the 82 rules above) is what makes object_type / type / element_type /
    // attribute_type / access_value reachable at all.
    //
    // These are NOT kwCases() candidates even though several are CamelCase. That
    // rule governs narrowing a keyword FROM an explicit spelling whitelist; these
    // alternatives were already bare kw() and already case-insensitive, so the
    // alias changes visibility only, never what is matched. It cannot steal an
    // identifier that was not already being stolen.
    //
    // processing, prompting and systemactions each appear in two of the sites
    // below and share ONE rule here.
    testpage_keyword: $ => alias(kw('testpage'), 'testpage'),
    testrequestpage_keyword: $ => alias(kw('testrequestpage'), 'testrequestpage'),
    content_keyword: $ => alias(kw('content'), 'content'),
    factboxes_keyword: $ => alias(kw('factboxes'), 'factboxes'),
    processing_keyword: $ => alias(kw('processing'), 'processing'),
    rolecenter_keyword: $ => alias(kw('rolecenter'), 'rolecenter'),
    prompting_keyword: $ => alias(kw('prompting'), 'prompting'),
    prompt_keyword: $ => alias(kw('prompt'), 'prompt'),
    promptoptions_keyword: $ => alias(kw('promptoptions'), 'promptoptions'),
    systemactions_keyword: $ => alias(kw('systemactions'), 'systemactions'),
    reporting_keyword: $ => alias(kw('reporting'), 'reporting'),
    navigation_keyword: $ => alias(kw('navigation'), 'navigation'),
    creation_keyword: $ => alias(kw('creation'), 'creation'),
    promoted_keyword: $ => alias(kw('promoted'), 'promoted'),
    sections_keyword: $ => alias(kw('sections'), 'sections'),
    embedding_keyword: $ => alias(kw('embedding'), 'embedding'),
    promptguide_keyword: $ => alias(kw('promptguide'), 'promptguide'),
    tableelement_keyword: $ => alias(kw('tableelement'), 'tableelement'),
    fieldelement_keyword: $ => alias(kw('fieldelement'), 'fieldelement'),
    textelement_keyword: $ => alias(kw('textelement'), 'textelement'),
    fieldattribute_keyword: $ => alias(kw('fieldattribute'), 'fieldattribute'),
    textattribute_keyword: $ => alias(kw('textattribute'), 'textattribute'),
    public_keyword: $ => alias(kw('public'), 'public'),

    // --- Tier 4: keywords named for losslessness ---
    //
    // Every rule below existed only as a bare kw() at its call site until the
    // 4.0.0 losslessness pass. A bare kw() is a token(PATTERN), which tree-sitter
    // renders as a hidden aux_sym_* symbol: the bytes were lexed and then landed
    // in no node at all. Measured over BC.History's 15,358 files, the sites these
    // rules replace accounted for 574,694 dropped keyword occurrences — `Record`
    // alone was 305,922, i.e. every variable and parameter of record type in
    // Business Central had an unhighlightable, unqueryable type keyword.
    //
    // Same shape as every rule above: alias(kw(w), w), one anonymous child typed
    // as the canonical lowercase spelling. NOT kwCases() — that whitelist governs
    // the 13 object-declaration keywords, where narrowing FROM an explicit
    // spelling list is the point. These were already bare kw() and already
    // case-insensitive, so the alias changes visibility only and cannot steal an
    // identifier that was not already being taken.
    //
    // Type-position keywords. basic_type deliberately does NOT move: it is a
    // choice() of bare kw()s with no visible sibling, so the basic_type node is
    // itself the leaf carrying the text. These six cannot use that pattern —
    // each has real children (a length, an element type, a reference), so the
    // enclosing node is not a leaf and the keyword needs a node of its own.
    record_keyword: $ => alias(kw('record'), 'record'),
    code_keyword: $ => alias(kw('code'), 'code'),
    text_keyword: $ => alias(kw('text'), 'text'),
    option_keyword: $ => alias(kw('option'), 'option'),
    array_keyword: $ => alias(kw('array'), 'array'),
    list_keyword: $ => alias(kw('list'), 'list'),
    dictionary_keyword: $ => alias(kw('dictionary'), 'dictionary'),

    // Action-family declaration keywords.
    action_keyword: $ => alias(kw('action'), 'action'),
    actionref_keyword: $ => alias(kw('actionref'), 'actionref'),
    systemaction_keyword: $ => alias(kw('systemaction'), 'systemaction'),
    fileuploadaction_keyword: $ => alias(kw('fileuploadaction'), 'fileuploadaction'),
    customaction_keyword: $ => alias(kw('customaction'), 'customaction'),
    separator_keyword: $ => alias(kw('separator'), 'separator'),

    // Extension modification keywords. One rule per word, shared by all of that
    // word's call sites (addafter alone had four: layout, action, views and
    // dataset). The construct is told apart by the parent node — never by the
    // keyword's own type — which is the same rule the field_keyword split above
    // follows.
    add_keyword: $ => alias(kw('add'), 'add'),
    addfirst_keyword: $ => alias(kw('addfirst'), 'addfirst'),
    addlast_keyword: $ => alias(kw('addlast'), 'addlast'),
    addafter_keyword: $ => alias(kw('addafter'), 'addafter'),
    addbefore_keyword: $ => alias(kw('addbefore'), 'addbefore'),
    modify_keyword: $ => alias(kw('modify'), 'modify'),
    movefirst_keyword: $ => alias(kw('movefirst'), 'movefirst'),
    movelast_keyword: $ => alias(kw('movelast'), 'movelast'),
    moveafter_keyword: $ => alias(kw('moveafter'), 'moveafter'),
    movebefore_keyword: $ => alias(kw('movebefore'), 'movebefore'),

    // Property-value and declaration keywords.
    //
    // ascending_keyword/descending_keyword keep kw()'s second argument, which is
    // LEXICAL precedence, not parse precedence. The two call sites disagreed
    // before they shared a rule: sorting_value used a plain kw() and
    // order_by_item used kw(w, 5) — two different terminals for one word. They
    // are now one terminal at prec 5, the higher of the two. Raising is the safe
    // direction: `ascending` and an identifier spelled `Ascending` are the same
    // LENGTH, so wherever both are valid the tie is broken by precedence, and
    // order_by_item's author set 5 deliberately to win it. Lowering
    // order_by_item to 0 would have handed that tie back to declaration order.
    sorting_keyword: $ => alias(kw('sorting'), 'sorting'),
    order_keyword: $ => alias(kw('order'), 'order'),
    ascending_keyword: $ => alias(kw('ascending', 5), 'ascending'),
    descending_keyword: $ => alias(kw('descending', 5), 'descending'),
    lookup_keyword: $ => alias(kw('lookup'), 'lookup'),
    system_keyword: $ => alias(kw('system'), 'system'),
    value_keyword: $ => alias(kw('value'), 'value'),
    label_keyword: $ => alias(kw('label'), 'label'),
    assembly_keyword: $ => alias(kw('assembly'), 'assembly'),
    type_keyword: $ => alias(kw('type'), 'type'),
    access_keyword: $ => alias(kw('access'), 'access'),
    comment_keyword: $ => alias(kw('comment'), 'comment'),
    locked_keyword: $ => alias(kw('locked'), 'locked'),
    maxlength_keyword: $ => alias(kw('maxlength'), 'maxlength'),

    // `is` / `as` operator keywords. Both keep kw()'s second argument — that is
    // LEXICAL precedence and it is load-bearing here, exactly as the note on
    // in_keyword above explains for the opposite case: `in` must NOT have it,
    // because inside token() it outranks the `integer` token and stops `Integer`
    // from ever matching past `In`. These two are already inside token() with
    // prec 5 and were so before they had rules; the alias changes visibility
    // only. They were the operator fields of is_expression/as_expression, so the
    // dropped token took a declared `operator` field down with it.
    is_keyword: $ => alias(kw('is', 5), 'is'),
    as_keyword: $ => alias(kw('as', 5), 'as'),

    // =====================================================================
    // Shared rules
    // =====================================================================

    _identifier_or_quoted: $ => choice(
      $.identifier,
      $.quoted_identifier,
      // Contextual keywords that can also be used as identifiers
      alias($.keyword_as_identifier, $.identifier),
    ),

    // Keywords that need to be usable as identifiers (variable names, parameter names, etc.)
    keyword_as_identifier: $ => prec(-10, choice(
      kw('field'),
      $.key_keyword,
      kw('value'),
      kw('separator'),
      $.dataset_keyword,
      kw('type'),
      kw('version'),
      kw('action'),
      $.table_keyword,
      kw('assembly'),
    )),

    // Identifiers — Unicode-aware
    // AL's identifier rule is C#'s. Measured against alc 18.0.37.11445 with a
    // discriminating control on every probe:
    //
    //   start     Lu Ll Lt Lm Lo Nl _          (Mn, Cf, Nd, No all REJECTED)
    //   continue  start + Mn Mc Nd Pc Cf
    //
    // `\p{L}` covers Lu Ll Lt Lm Lo, so the start class adds only `\p{Nl}`
    // (U+2160 ROMAN NUMERAL ONE is a legal identifier start to alc), and the
    // continue class adds the four alc accepts and `\p{L}\p{N}` missed:
    // Mn (combining marks), Mc (spacing marks), Pc (connectors) and Cf (ZWNJ
    // and friends). Before this, `Oa<U+0301>k: Integer;` -- valid AL that alc
    // compiles -- shredded into an identifier plus an ERROR node.
    //
    // DELIBERATELY still broader than alc in two ways, per "parse structure,
    // don't validate": `\p{N}` keeps `No` (alc rejects `O<U+00B2>k`, AL0107),
    // and nothing here is capped to the BMP (alc rejects astral codepoints,
    // AL0183). Both are the parser accepting more than the compiler, which is
    // the safe direction and is recorded rather than closed.
    //
    // U+FEFF IS IN \p{Cf} AND IN `extras` AND IN the scanner's whitespace set,
    // all three deliberately, and it is NOT excluded here. Do not "simplify"
    // that by dropping U+FEFF from the class or from `extras`: each is
    // load-bearing in a different position, and both are pinned by fixtures.
    //   * alc ACCEPTS U+FEFF mid-identifier -- `O<U+FEFF>k: Integer;` compiles,
    //     as do U+200B, U+200C, U+200D, U+00AD, U+2060, U+061C. So excluding it
    //     would put us back to rejecting valid AL.
    //   * The two components do NOT split it. tree-sitter's longest match makes
    //     the identifier win, and src/scanner.c's read_word_ci consumes U+FEFF
    //     through this same generated table, so PROPERTY_NAME spans exactly the
    //     bytes the grammar's lexer would. Verified in six positions.
    //   * Consequence, and it is CORRECT: `begin<U+FEFF>` is an identifier, not
    //     a begin_keyword, so a BOM glued to a keyword breaks it. alc breaks the
    //     same way (AL0104; `codeunit<U+FEFF>` is AL0198). Before this widening
    //     we accepted those files with zero errors -- accepting what the
    //     compiler rejects. A BOM at file start and a BOM BETWEEN statements
    //     still parse cleanly, and alc accepts both.
    //
    // src/unicode_id.h MUST be regenerated whenever this line changes -- the
    // scanner reads those tables to decide where PROPERTY_NAME and
    // VAR_ATTRIBUTE_OPEN end, and a stale table makes the scanner disagree with
    // this regex. That drift is exactly what 586478a fixed.
    // `python tools/gen-unicode-id-table.py --check` fails loudly if it drifts.
    identifier: $ => token(/[\p{L}\p{Nl}_][\p{L}\p{N}\p{Mn}\p{Mc}\p{Pc}\p{Cf}_]*/u),

    quoted_identifier: $ => token(prec(10, seq(
      '"',
      repeat(choice(
        new RustRegex('[^"\\n]+'),
        '""'  // Escaped double quote
      )),
      '"'
    ))),

    // Comments (including XML doc comments /// ...)
    comment: $ => token(seq('//', /[^\n]*/)),
    multiline_comment: $ => token(seq('/*', /[^*]*\*+([^/*][^*]*\*+)*/, '/')),

    // Literals
    string_literal: $ => token(
      choice(
        seq("'", "'"),
        seq(
          "'",
          repeat1(choice(
            new RustRegex("[^'\\n]+"),
            "''"
          )),
          "'"
        )
      )
    ),

    // Verbatim string literal: @'...' — allows newlines and backslash-continuations
    verbatim_string: $ => token(
      seq(
        "@'",
        repeat(choice(
          new RustRegex("[^']+"),
          "''"
        )),
        "'"
      )
    ),

    integer: $ => token(/\d+/),
  },
});
