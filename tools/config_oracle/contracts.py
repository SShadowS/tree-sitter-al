"""The authoritative, hand-maintained registry of special node types (spec section 3).

node-types.json is a CENSUS input, never the source of this list: checking a
hand-written expectation against a generated declaration can fail; deriving the
expectation from the declaration cannot (tools/check-field-types.py pattern).
"""
from __future__ import annotations

import importlib
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Entry:
    type: str
    kind: str
    handler: str | None = None
    hosts: dict = field(default_factory=dict)
    alias_to: str | None = None
    arm: frozenset | None = None
    reading: str | None = None


READINGS = frozenset({"arm:if", "arm:else", "arm:inactive", "arm:not-else-led"})

# Registered in milestone 1, before `arm` existed. Their arms admit a whole
# statement or body-element set; declaring it would restate _statement and
# _body_element. Milestone 3 decides whether to.
ARM_EXEMPT = frozenset({"preproc_conditional", "preproc_conditional_statement",
                        "preproc_conditional_var_block", "preproc_pragma_only"})


REGISTRY: dict[str, Entry] = {}


def register(type_, kind, handler=None, hosts=None, alias_to=None, arm=None, reading=None):
    if type_ in REGISTRY:
        raise ValueError(f"duplicate registry entry: {type_}")
    if kind == "token-alias" and not alias_to:
        raise ValueError(f"token-alias entry without alias_to: {type_}")
    if reading is not None and reading not in READINGS:
        raise ValueError(f"unknown reading {reading!r} for {type_}")
    REGISTRY[type_] = Entry(type_, kind, handler, dict(hosts or {}), alias_to,
                            frozenset(arm) if arm else None, reading)


def resolve_handler(entry):
    mod, _, name = entry.handler.rpartition(".")
    return getattr(importlib.import_module(mod), name)


# --- statement-position hosts, shared by every node that fills a _statement slot
_STATEMENT_HOSTS = {
    "statement_block:<children>": "splice-repeat",
    "preproc_conditional_statement:<children>": "splice-repeat",
    # asserterror_statement: `optional(field('body', $._statement_inner))` (grammar.js:4694).
    # Every other statement field is a bare fieldedStatement (grammar.js:70-76, 4286-4304): mandatory.
    "asserterror_statement:body": "optional-slot", "case_branch:body": "single-slot",
    "for_statement:body": "single-slot", "foreach_statement:body": "single-slot",
    "if_statement:else_branch": "single-slot", "if_statement:then_branch": "single-slot",
    "while_statement:body": "single-slot", "with_statement:body": "single-slot",
    "preproc_guarded_statement:then_branch": "single-slot",
    "preproc_split_case_branch:body": "single-slot", "preproc_split_case_end_branch:body": "single-slot",
    "preproc_split_case_extended:body": "single-slot",
    "preproc_split_if_else_statement:else_branch": "single-slot",
    # then_branch is `fieldedStatement($, 'then_branch')` (grammar.js:70-76) inside
    # _preproc_if_then_else_head (grammar.js:3583-3589) — one field, never a repeat,
    # set once per #if/#elif/#else ARM of preproc_split_if_else_statement itself.
    # node-types.json's multiple: true reflects the field recurring across those
    # arms, not one arm producing more than one node — same shape as
    # if_statement:then_branch. Reverted from splice-repeat (round-1 misreading:
    # two sibling then_branch nodes were one-per-arm, not a genuine repeat of the
    # field at one position). single-slot is correct.
    "preproc_split_if_else_statement:then_branch": "single-slot",
    "preproc_split_if_statement:else_branch": "single-slot",
    "preproc_split_if_statement:then_branch": "single-slot",
    "preproc_fragmented_else_tail:<children>": "splice-repeat",
    "preproc_split_code_block_end:<children>": "splice-repeat",
    "preproc_split_code_block_over_endif:<children>": "splice-repeat",
    "preproc_split_else_begin_over_endif:<children>": "splice-repeat",
    "preproc_split_if_begin_asymmetric:<children>": "splice-repeat",
    "preproc_split_if_begin_else:<children>": "splice-repeat",
    "preproc_split_if_then_begin:<children>": "splice-repeat",
    "preproc_split_if_then_begin_else_shared:<children>": "splice-repeat",
    # preproc_split_open_statement (BC 29 family G): branch preambles and the
    # guarded tail are statement runs; `continuation` is the one statement that
    # completes a then/else; then_branch is the if-then-else head's, one per arm.
    "preproc_split_open_statement:<children>": "splice-repeat",
    "preproc_split_open_statement:continuation": "single-slot",
    "preproc_split_open_statement:then_branch": "single-slot",
    # The two procedure-boundary block closings (BC 29 family H): statement runs.
    "preproc_split_block_end_in_else:<children>": "splice-repeat",
    "preproc_split_block_close_after_endif:<children>": "splice-repeat",
}

_BODY_HOSTS = {f"{p}:<children>": "splice-repeat" for p in (
    "action_group_body", "controladdin_body", "dataset_mod_body", "declaration_body", "interface_body",
    "layout_container_body", "preproc_conditional", "preproc_conditional_controladdin",
    "preproc_conditional_layout_mixed", "preproc_conditional_query", "preproc_conditional_report",
    "preproc_conditional_xmlport", "preproc_split_var_section_tail", "query_body", "report_body",
    "xmlport_body")}
# var_body is NOT a body host any more: since the item-8 fix it admits only
# variable declarations (grammar.js var_body). preproc_conditional_var is
# registered separately below (Task 5), also admitting only declarations, not
# a member of _BODY_HOSTS. preproc_split_var_section_tail holds body elements
# in `repeat1`/`repeat` after its `variables`, so splice-repeat.

# preproc_split_procedure_preamble is NOT an exception, despite round-1 briefly
# treating it as one: _procedure_preamble (grammar.js:3074-3080) has
# `optional(choice($.var_section, $.preproc_conditional_var_block))` — a single
# optional, never a repeat of preproc_conditional_var_block itself. It is
# inlined once per ARM of preproc_split_procedure_preamble's own #if/#elif/#else
# structure (grammar.js:3085-3089), so two var-block nodes seen in one parse
# were one per arm of the OUTER conditional, not a genuine repeat at one
# position — same shape as the other three routine-tail hosts.
# At most one node, and zero is legal: the slot is optional(...) in both
# _procedure_preamble (grammar.js:3075-3079) and _routine_regular_body
# (grammar.js:3005-3008), which serves procedure, preproc_split_procedure and
# trigger_declaration (grammar.js:3238). Hence optional-slot, not single-slot.
_ROUTINE_TAIL_HOSTS = {f"{p}:<children>": "optional-slot" for p in (
    "preproc_split_procedure", "preproc_split_procedure_preamble", "procedure", "trigger_declaration")}

# _body_element (grammar.js:667-714): every object/section-body member, shared
# by preproc_conditional_layout_mixed, preproc_conditional_report and (Task 6)
# preproc_conditional_query/xmlport/controladdin. Defined once (round-1 review
# of Task 4: the member list was repeated inline at each of its arms).
_BODY_ELEMENT = frozenset({
    "property", "preproc_split_permissions_property", "empty_statement", "fields_section",
    "keys_section", "fieldgroups_section", "enum_value_declaration", "labels_section",
    "layout_section", "actions_section", "views_section", "analysisviews_section",
    "dataset_section", "requestpage_section", "rendering_section", "elements_section",
    "schema_section", "assembly_declaration", "procedure", "trigger_declaration", "var_section",
    "attribute_item", "event_declaration", "preproc_split_procedure",
    "preproc_split_procedure_preamble", "preproc_conditional", "preproc_split_var_section_tail",
    "modify_modification",
})
# _layout_element (grammar.js:2115-2141): every layout-container member,
# including its own self-reference to preproc_conditional_layout. Shared by
# preproc_conditional_layout's own arm and preproc_conditional_layout_mixed's.
_LAYOUT_ELEMENT = frozenset({
    "area_section", "group_section", "repeater_section", "cuegroup_section", "fixed_section",
    "grid_section", "page_field", "part_section", "systempart_section", "usercontrol_section",
    "label_section", "preproc_conditional_layout", "preproc_split_field",
    "addfirst_modification", "addlast_modification", "addafter_modification",
    "addbefore_modification", "modify_modification", "preproc_split_modify",
    "movefirst_modification", "movelast_modification", "moveafter_modification",
    "movebefore_modification",
})

# --- directive plumbing: consumed by whichever owner contains it
for t in ("preproc_if", "preproc_elif", "preproc_else", "preproc_endif", "preproc_open", "preproc_close",
          "preproc_and_expression", "preproc_or_expression", "preproc_not_expression",
          "preproc_parenthesized_expression"):
    register(t, "directive")

# --- extras
for t in ("preproc_region", "preproc_endregion", "preproc_define", "preproc_undef"):
    register(t, "trivia")

# --- milestone-1 implemented handlers
register("preproc_split_begin", "token-alias", "tools.config_oracle.lowering.select.token_alias",
         hosts={h: "any" for h in ("preproc_fragmented_else_tail:<children>",
                                   "preproc_split_if_begin_asymmetric:<children>",
                                   "preproc_split_if_then_begin:<children>",
                                   "preproc_split_if_then_begin_else_shared:<children>",
                                   "preproc_split_open_statement:<children>")},
         alias_to="begin_keyword")
register("preproc_split_end", "token-alias", "tools.config_oracle.lowering.select.token_alias",
         hosts={"preproc_split_code_block_end:<children>": "any"}, alias_to="end_keyword")
register("preproc_conditional", "branch-select", "tools.config_oracle.lowering.select.branch_select",
         hosts=_BODY_HOSTS)
register("preproc_conditional_statement", "branch-select", "tools.config_oracle.lowering.select.branch_select",
         hosts=_STATEMENT_HOSTS)
register("preproc_conditional_var_block", "branch-select", "tools.config_oracle.lowering.select.branch_select",
         hosts=_ROUTINE_TAIL_HOSTS)
register("preproc_pragma_only", "branch-select", "tools.config_oracle.lowering.select.branch_select",
         hosts={"field_declaration:<children>": "splice-repeat", "preproc_split_procedure:<children>": "splice-repeat",
                "procedure:<children>": "splice-repeat", "source_file:<children>": "splice-repeat",
                # trigger_declaration shares _procedure_tail since the BC 29 family-F fix.
                "trigger_declaration:<children>": "splice-repeat"})
register("preproc_split_code_block_end", "assembler",
         "tools.config_oracle.lowering.assemblers.split_code_block_end",
         hosts={"code_block:<children>": "consumed"})
register("preproc_split_case_statement_end", "assembler",
         "tools.config_oracle.lowering.assemblers.split_case_statement_end", hosts=_STATEMENT_HOSTS)
register("preproc_split_case_end_branch", "fragment", None,
         hosts={"preproc_split_case_statement_end:<children>": "consumed"})
register("preproc_split_procedure", "assembler", "tools.config_oracle.lowering.assemblers.split_procedure",
         hosts=dict(_BODY_HOSTS))

# --- branch-select, part A (Task 4): object, actions, layout, layout_mixed, report,
# rendering, dataset. Arm sets are each type's own rule in grammar.js, with hidden
# choices (_object, _action_element, _layout_element, _body_element,
# _report_body_element, _report_dataitem_variant) expanded to their visible members;
# cross-checked against each type's own `children` entry in node-types.json (which
# already reflects the hidden-rule inlining) and they agree exactly. Host sets are
# the census output — every one is a repeat slot (verified against the host rule),
# so splice-repeat throughout.
register("preproc_conditional_object", "branch-select", "tools.config_oracle.lowering.select.branch_select",
         hosts={"source_file:<children>": "splice-repeat",
                "preproc_conditional_object:<children>": "splice-repeat"},
         arm={"namespace_declaration", "using_statement", "preproc_conditional_object",
              "table_declaration", "tableextension_declaration", "page_declaration",
              "pageextension_declaration", "pagecustomization_declaration", "codeunit_declaration",
              "report_declaration", "reportextension_declaration", "query_declaration",
              "xmlport_declaration", "enum_declaration", "enumextension_declaration",
              "interface_declaration", "controladdin_declaration", "dotnet_declaration",
              "profile_declaration", "profileextension_declaration", "permissionset_declaration",
              "permissionsetextension_declaration", "entitlement_declaration", "preproc_split_declaration"})
register("preproc_conditional_actions", "branch-select", "tools.config_oracle.lowering.select.branch_select",
         hosts={"action_body:<children>": "splice-repeat", "action_group_body:<children>": "splice-repeat",
                "preproc_conditional_actions:<children>": "splice-repeat"},
         arm={"action_area_section", "action_group_section", "action_declaration", "separator_action",
              "actionref_declaration", "systemaction_declaration", "fileuploadaction_declaration",
              "customaction_declaration", "property", "trigger_declaration", "attribute_item",
              "addfirst_action_modification", "addlast_action_modification",
              "addafter_action_modification", "addbefore_action_modification",
              "modify_action_modification", "preproc_split_modify", "movefirst_modification",
              "movelast_modification", "moveafter_modification", "movebefore_modification",
              "preproc_conditional_actions"})
register("preproc_conditional_layout", "branch-select", "tools.config_oracle.lowering.select.branch_select",
         hosts={"layout_body:<children>": "splice-repeat", "layout_container_body:<children>": "splice-repeat",
                "preproc_conditional_layout:<children>": "splice-repeat",
                "preproc_conditional_layout_mixed:<children>": "splice-repeat",
                "preproc_split_brace_close:<children>": "splice-repeat",
                "preproc_split_brace_close_if_only:<children>": "splice-repeat"},
         arm=_LAYOUT_ELEMENT)
register("preproc_conditional_layout_mixed", "branch-select", "tools.config_oracle.lowering.select.branch_select",
         hosts={"layout_container_body:<children>": "splice-repeat"},
         # _body_element | _layout_element (grammar.js seq at preproc_conditional_layout_mixed):
         # neither expansion includes preproc_conditional_layout_mixed itself.
         arm=_BODY_ELEMENT | _LAYOUT_ELEMENT)
register("preproc_conditional_report", "branch-select", "tools.config_oracle.lowering.select.branch_select",
         hosts={"report_body:<children>": "splice-repeat",
                "preproc_conditional_report:<children>": "splice-repeat"},
         # _report_body_element (grammar.js:2766-2775): its own 4 members, plus
         # _body_element, plus its self-reference.
         arm={"report_column", "report_dataitem", "preproc_split_report_dataitem_header",
              "preproc_split_report_dataitem_open_over_endif",
              "preproc_conditional_report"} | _BODY_ELEMENT)
register("preproc_conditional_rendering", "branch-select", "tools.config_oracle.lowering.select.branch_select",
         hosts={"rendering_body:<children>": "splice-repeat"},
         arm={"rendering_layout"})
register("preproc_conditional_dataset", "branch-select", "tools.config_oracle.lowering.select.branch_select",
         hosts={"dataset_body:<children>": "splice-repeat"},
         arm={"report_dataitem", "preproc_split_report_dataitem_header",
              "preproc_split_report_dataitem_open_over_endif", "attribute_item"})

# --- branch-select, part B (Task 5): fields, keys, fieldgroups, var. Arm sets
# are each type's own rule in grammar.js, with the hidden branch-item rules
# (_field_branch_items, _key_branch_items) expanded to their visible members;
# cross-checked against the census, which agrees exactly. preproc_split_table_field_open
# and preproc_split_key are themselves unsupported (milestone 3), but they are
# still real host slots for preproc_conditional_fields/keys per the census, so
# they are declared here with the policy the shared repeat rule implies.
register("preproc_conditional_fields", "branch-select", "tools.config_oracle.lowering.select.branch_select",
         hosts={"fields_body:<children>": "splice-repeat",
                "preproc_conditional_fields:<children>": "splice-repeat",
                "preproc_split_table_field_open:<children>": "splice-repeat"},
         # _field_branch_items (grammar.js:1672-1674).
         arm={"field_declaration", "attribute_item", "modify_modification", "preproc_conditional_fields"})
register("preproc_conditional_keys", "branch-select", "tools.config_oracle.lowering.select.branch_select",
         hosts={"keys_body:<children>": "splice-repeat",
                "preproc_conditional_keys:<children>": "splice-repeat",
                "preproc_split_key:<children>": "splice-repeat"},
         # _key_branch_items (grammar.js:1765).
         arm={"key_declaration", "attribute_item", "preproc_conditional_keys"})
register("preproc_conditional_fieldgroups", "branch-select", "tools.config_oracle.lowering.select.branch_select",
         hosts={"fieldgroups_body:<children>": "splice-repeat",
                "preproc_conditional_fieldgroups:<children>": "splice-repeat"},
         # own rule (grammar.js:1806-1812): fieldgroup_declaration or a nested
         # preproc_conditional_fieldgroups, nothing else -- no attribute_item, no
         # modification (the addlast/addfirst fieldgroup modifications sit in
         # fieldgroups_body directly, not inside this conditional).
         arm={"fieldgroup_declaration", "preproc_conditional_fieldgroups"})
register("preproc_conditional_var", "branch-select", "tools.config_oracle.lowering.select.branch_select",
         hosts={"var_body:<children>": "splice-repeat"},
         # own rule (grammar.js:3520-3532), post item-8 fix: declarations only,
         # no self-nesting (unlike fields/keys/fieldgroups).
         arm={"variable_declaration", "var_attribute_item"})

# --- branch-select, part C (Task 6): case, labels, query, xmlport, controladdin.
register("preproc_conditional_case", "branch-select", "tools.config_oracle.lowering.select.branch_select",
         hosts={"case_body:<children>": "splice-repeat"},
         # own rule (grammar.js:4727-4734): repeat($.case_branch) then optional
         # ($.case_else_branch), no self-nesting. The task-5 brief described this
         # arm as holding a nested preproc_conditional_case; the rule itself has
         # no such reference (only preproc_split_case_branch nests, one level
         # down, inside case_branch's own choice) -- read from grammar.js, not
         # the brief.
         #
         # case_else_branch is declared here (grammar-true) but deliberately
         # EXCLUDED from the arm. It is one of case_body's repeat1 members only
         # in the multi-config tree (via preproc_conditional_case); in every
         # single-configuration parse case_statement carries it as its OWN
         # optional field, a SIBLING of case_body, never case_body's child
         # (grammar.js:4585-4592: `optional(field('body', case_body)),
         # optional(case_else_branch), end_keyword`). Splicing it into case_body
         # like an ordinary arm member is a genuine structural discrepancy, not
         # a policy mismatch: found live over BC.History
         # (case_preprocessor_else.txt, config CLEAN25=0) as `case_body.body/
         # case_else_branch` (lowered) vs `case_statement.-/case_else_branch`
         # (reference) -- extra/missing at the same two paths. Re-parenting a
         # fragment from case_body to its case_statement grandparent needs a
         # new Fragment kind that survives a NON-last original child (case_body
         # is not case_statement's last child; end_keyword is), which none of
         # engine.py's four Fragment types do today. Left unsupported
         # (arm-content -> cannot-validate) rather than papered over; milestone 3.
         arm={"case_branch"})
register("preproc_conditional_labels", "branch-select", "tools.config_oracle.lowering.select.branch_select",
         hosts={"labels_body:<children>": "splice-repeat"},
         # own rule (grammar.js:2072-2078): label_declaration only, no self-nesting.
         arm={"label_declaration"})
register("preproc_conditional_query", "branch-select", "tools.config_oracle.lowering.select.branch_select",
         hosts={"query_body:<children>": "splice-repeat",
                "preproc_conditional_query:<children>": "splice-repeat"},
         # _query_body_element (grammar.js:2873-2879): its own 3 members, _body_element, self-reference.
         arm={"query_column", "query_filter", "query_dataitem", "preproc_conditional_query"} | _BODY_ELEMENT)
register("preproc_conditional_xmlport", "branch-select", "tools.config_oracle.lowering.select.branch_select",
         hosts={"xmlport_body:<children>": "splice-repeat",
                "preproc_conditional_xmlport:<children>": "splice-repeat"},
         # _xmlport_body_element (grammar.js:2949-2954): its own 2 members, _body_element, self-reference.
         arm={"xmlport_element", "xmlport_attribute", "preproc_conditional_xmlport"} | _BODY_ELEMENT)
register("preproc_conditional_controladdin", "branch-select", "tools.config_oracle.lowering.select.branch_select",
         hosts={"controladdin_body:<children>": "splice-repeat",
                "preproc_conditional_controladdin:<children>": "splice-repeat"},
         # own rule (grammar.js:589-601): _body_element, interface_procedure, self-reference.
         arm={"interface_procedure", "preproc_conditional_controladdin"} | _BODY_ELEMENT)

# --- branch-select, part D (Task 7): the list-run lists. Each arm splices items AND
# separators into its host list (select.branch_select, list-run); the host list is
# then checked for item/separator alternation (engine._check_alternation). Arm sets
# are each type's own `_*_branch` / `_*_seq` / `_*_run` helpers with the hidden
# rules expanded to visible members; host sets are the census output.
# _expression (grammar.js:5023-5055), with _literal_value (grammar.js:5572-5582)
# expanded. _value_start_keyword_name and continue_as_identifier alias to identifier.
_EXPRESSION = frozenset({
    "multiplicative_expression", "additive_expression", "comparison_expression",
    "logical_expression", "in_expression", "is_expression", "as_expression",
    "qualified_enum_value", "database_reference", "call_expression", "member_expression",
    "subscript_expression", "identifier", "quoted_identifier", "integer", "decimal", "boolean",
    "string_literal", "verbatim_string", "datetime_literal", "date_literal", "time_literal",
    "biginteger_literal", "parenthesized_expression", "unary_expression", "list_literal",
    "keyword_identifier", "ternary_expression", "assignment_expression",
})
_LIST_RUN = "tools.config_oracle.lowering.select.branch_select"
register("preproc_conditional_permissions", "branch-select", _LIST_RUN,
         hosts={"tabledata_permission_list:<children>": "list-run",
                "preproc_conditional_permissions:<children>": "list-run"},
         # _permission_branch / _permission_seq / _permission_run (grammar.js:1349-1391):
         # the trailing ';' is the property's own terminator (terminator-hoist).
         arm={"tabledata_permission", "preproc_conditional_permissions", ",", ";"})
register("preproc_conditional_arguments", "branch-select", _LIST_RUN,
         hosts={"argument_list:<children>": "list-run"},
         # _argument_branch / _argument_branch_run (grammar.js:5366-5386), each item an
         # _argument_expression (grammar.js:5388-5391). No ';' and no self-nesting.
         arm=_EXPRESSION | {"preproc_conditional_expression_tail", ","})
register("preproc_conditional_list_elements", "branch-select", _LIST_RUN,
         hosts={"list_literal:<children>": "list-run"},
         # own rule (grammar.js:5480-5486): repeat1(seq(',', _list_element)), and
         # _list_element (grammar.js:5488-5491) is range_expression | _expression.
         arm=_EXPRESSION | {"range_expression", ","})
register("preproc_conditional_option_members", "branch-select", _LIST_RUN,
         hosts={"option_member_list:<children>": "list-run"},
         # _option_members_branch (grammar.js:1597-1612): option_member and ','; no self-nesting.
         arm={"option_member", ","})
register("preproc_conditional_where", "branch-select", _LIST_RUN,
         hosts={"where_conditions:<children>": "list-run",
                "preproc_conditional_where:<children>": "list-run"},
         # _where_branch / _where_seq / _where_run (grammar.js:1044-1076).
         arm={"where_condition", "preproc_conditional_where", ","})
register("preproc_conditional_link_values", "branch-select", _LIST_RUN,
         hosts={"link_value_list:<children>": "list-run",
                "preproc_conditional_link_values:<children>": "list-run"},
         # _link_value_branch / _link_value_seq / _link_value_run (grammar.js:1190-1224).
         arm={"link_value", "preproc_conditional_link_values", ","})

# --- registered, not yet lowered (milestones 2-3). Unsupported is explicit, never a default.
for t in ("preproc_conditional_case_patterns",
          "preproc_conditional_impl_values",
          "preproc_fragmented_else_tail",
          "preproc_guarded_statement", "preproc_split_brace_close",
          "preproc_split_brace_close_if_only", "preproc_split_call_statement", "preproc_split_case_branch",
          "preproc_split_case_extended", "preproc_split_code_block_over_endif", "preproc_split_complete_body",
          "preproc_split_declaration", "preproc_split_field",
          "preproc_split_if_begin_asymmetric", "preproc_split_if_begin_else", "preproc_split_if_else_statement",
          "preproc_split_if_statement", "preproc_split_if_then_begin", "preproc_split_if_then_begin_else_shared",
          "preproc_split_procedure_body", "preproc_split_procedure_preamble",
          "preproc_split_report_dataitem_header",
          "preproc_split_table_field"):
    register(t, "unsupported")

# preproc_split_permissions_property assembles one property per branch from
# that branch's head plus the shared tail. milestone 3.
register("preproc_split_permissions_property", "unsupported")
# BC 29 family E: per-branch header, shared body after #endif (assembler shape). milestone 3.
register("preproc_split_key", "unsupported")
register("preproc_split_modify", "unsupported")
# BC 29 family D: only the #if-taken configuration is valid AL, so lowering the
# other configuration must report cannot-validate, never a discrepancy. milestone 3.
register("preproc_split_table_field_open", "unsupported")
# --- Task 9: one-reading contracts (spec P4). The tree shows ONE configuration's
# nesting (`reading`); every other configuration reports lowering:one-reading.
_ASM = "tools.config_oracle.lowering.assemblers."
# BC 29 family G: branches end in an open statement prefix, tail completes it.
# An else-led arm is one-reading; complete-prefix arms stay unsupported-type (milestone 3).
# case_body:<children> is a census host outside _STATEMENT_HOSTS: case_body's
# repeat admits preproc_split_open_statement (grammar.js case_body), a repeat slot.
register("preproc_split_open_statement", "assembler", _ASM + "open_statement_reading",
         hosts={**_STATEMENT_HOSTS, "case_body:<children>": "splice-repeat"}, reading="arm:not-else-led")
# BC 29 family H: a branch closes a layout container and opens a sibling. The
# tree is the #if reading.
register("preproc_split_container_reopen", "assembler", _ASM + "container_reopen",
         hosts={f"{k}_section:<children>": "consumed" for k in ("group", "repeater", "cuegroup", "fixed", "grid")},
         reading="arm:if")
# A procedure boundary inside #else: the tree is the #else reading, split over
# two procedures' block closings. Both decide the same group's reading.
register("preproc_split_block_end_in_else", "assembler", _ASM + "block_end_in_else",
         hosts={"code_block:<children>": "consumed"}, reading="arm:else")
# `end else begin` over #endif: the base shape lowers in both configurations; the
# widened shapes (ProdOrderComponent) are one-reading, the tree being the
# arm-not-selected reading (the rule comment says so).
register("preproc_split_else_begin_over_endif", "assembler", _ASM + "else_begin_over_endif",
         hosts={"code_block:<children>": "consumed"}, reading="arm:inactive")
register("preproc_split_block_close_after_endif", "assembler", _ASM + "block_close_after_endif",
         hosts={"code_block:<children>": "consumed"}, reading="arm:else")

# --- Task 8: table relation, contract else-relation-join (assemblers.table_relation_select).
# Hosts are the census output. Two grammar rules build this node type:
#  * property:value -- _table_relation_whole_conditional (the whole value is the
#    #if): each arm is one `_property_value` (G8; before it, identifier |
#    quoted_identifier | table_relation_value (G2) or a literal leaf (G4)), the
#    shape a flat parse of the arm gives, then an optional ';'.
#  * table_relation_value:<children> -- preproc_conditional_table_relation after
#    the relation it continues (G1): arm _tr_branch, i.e. table_relation_expression
#    | else_table_relation_fragment, then an optional ';'.
register("preproc_conditional_table_relation", "assembler",
         "tools.config_oracle.lowering.assemblers.table_relation_select",
         # Nested inside an else chain the arm's relation must merge into the
         # enclosing table_relation_expression, a rewrite this contract does not
         # name: refused as unsupported-type.
         # preproc_conditional_table_relation:<children>: a whole-value #if nested
         # in a whole-value arm (G3), lowered as the arm's value.
         hosts={"property:value": "single-slot",
                "preproc_conditional_table_relation:<children>": "single-slot",
                "table_relation_expression:<children>": "unsupported",
                "table_relation_value:<children>": "single-slot"},
         # The literal leaves are the whole-value arm's (G4): any property's whole
         # value may be a #if, and each arm holds the leaf its flat parse gives.
         arm={"identifier", "quoted_identifier", "table_relation_value",
              "table_relation_expression", "else_table_relation_fragment", ";",
              "boolean", "integer", "decimal", "string_literal", "verbatim_string",
              "date_literal", "time_literal", "datetime_literal",
              "preproc_conditional_table_relation",
              # G8 (Task 18): a whole-value arm is `_property_value` itself, so
              # every compound value it offers (grammar.js _property_value) is an
              # arm kind too. The table_relation_value:<children> host's arms
              # (_tr_branch) never produce these.
              "caption_value", "ml_value_list", "tabledata_permission_list",
              "order_by_list", "implementation_value_list", "option_member_list",
              "sorting_value", "link_value_list", "property_expression",
              "keyword_identifier", "where_clause", "object_reference_value",
              "decimal_range_value", "signed_integer_list"})
# Non-prefixed special type: completes an earlier table relation (spec section 3).
# Consumed by table_relation_select as a RelationContinuation; never lowered directly.
register("else_table_relation_fragment", "fragment", None,
         hosts={"preproc_conditional_table_relation:<children>": "consumed"})

# --- Task 11: expressions split across #if arms, regrouped by the alc-measured
# precedence table (lowering/expression.py). Hosts are the census output.
# The tail follows the expression it continues and extends it (ToPrevious):
# assignment RHS, exit value, argument (also inside a preproc_conditional_arguments
# arm), if/while condition, for bound, subscript index, list element, property value
# (inside the property_expression that _property_value_with_split is aliased to, G5).
register("preproc_conditional_expression_tail", "assembler", _ASM + "expression_tail",
         hosts={h: "consumed" for h in (
             "argument_list:<children>", "assignment_statement:<children>", "exit_statement:<children>",
             "for_statement:<children>", "if_statement:<children>", "list_literal:<children>",
             "preproc_conditional_arguments:<children>", "property_expression:<children>",
             "subscript_expression:<children>", "while_statement:<children>")})
# The prefix sits inside a binary node, between `operator` and `right`. engine.lower's
# binary hook lowers the whole chain before any slot lookup; operand_prefix still
# checks these hosts, so the census and the handler agree.
register("preproc_operand_prefix", "assembler", _ASM + "operand_prefix",
         hosts={f"{k}:<children>": "consumed" for k in (
             "additive_expression", "comparison_expression", "logical_expression",
             "multiplicative_expression")})

# --- Task 12: var-tail-merge (assemblers.split_var_section_tail / engine.VarTailMerge).
# Added with the var_body fix (deferred-work item 8), unsupported until this task gave
# the engine a ToPrevious fragment for the cross-sibling merge into the PRECEDING
# var_section. Hosts are the census output (host_slots over node-types.json), which is
# exactly _BODY_HOSTS: this type is a `_body_element` member (grammar.js), so it appears
# everywhere every other body-element special type does.
register("preproc_split_var_section_tail", "assembler", _ASM + "split_var_section_tail",
         hosts=_BODY_HOSTS)

# --- Task 14: report-brace-owner (assemblers.report_brace_owner). One #if opens an
# outer dataitem; a later #if closes the inner one early. Hosts are the census
# output, every one a report/dataset body repeat. The brace close is consumed by
# the assembler through the inner dataitem it closes, never lowered on its own.
register("preproc_split_report_dataitem_open_over_endif", "assembler", _ASM + "report_brace_owner",
         hosts={f"{k}:<children>": "splice-repeat" for k in (
             "dataset_body", "dataset_mod_body", "preproc_conditional_dataset",
             "preproc_conditional_report", "report_body")})
register("preproc_split_report_brace_close", "fragment", None,
         hosts={"report_dataitem:<children>": "consumed"})

SPECIAL_NON_PREFIXED = {"else_table_relation_fragment"}


def host_slots(node_types, type_name):
    subtypes = {t["type"]: [s["type"] for s in t.get("subtypes", [])] for t in node_types if "subtypes" in t}

    def expand(ts):
        out = set()
        for t in ts:
            out |= expand(subtypes[t]) if t in subtypes else {t}
        return out

    slots = set()
    for t in node_types:
        specs = list(t.get("fields", {}).items())
        if "children" in t:
            specs.append(("<children>", t["children"]))
        for name, spec in specs:
            if type_name in expand(x["type"] for x in spec.get("types", [])):
                slots.add(f"{t['type']}:{name}")
    return slots


def census(node_types):
    problems = []
    declared = {t["type"] for t in node_types if t.get("named") and t["type"].startswith("preproc")}
    for t in sorted(declared - REGISTRY.keys()):
        problems.append(f"unregistered: {t}")
    for t in sorted(REGISTRY.keys() - declared - SPECIAL_NON_PREFIXED):
        problems.append(f"stale entry, type no longer declared: {t}")
    for e in REGISTRY.values():
        if e.kind in ("directive", "trivia", "unsupported") or not e.hosts:
            continue
        real = host_slots(node_types, e.type)
        for slot in sorted(real - e.hosts.keys()):
            problems.append(f"host slot not classified: {e.type} in {slot}")
        for slot in sorted(e.hosts.keys() - real):
            problems.append(f"stale host slot: {e.type} in {slot}")
    known = {t["type"] for t in node_types}
    for e in REGISTRY.values():
        for k in sorted(e.arm or ()):
            if k not in known:
                problems.append(f"arm kind does not exist: {k} in {e.type}")
    return problems
