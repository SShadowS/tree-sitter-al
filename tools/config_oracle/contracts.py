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


REGISTRY: dict[str, Entry] = {}


def register(type_, kind, handler=None, hosts=None, alias_to=None):
    if type_ in REGISTRY:
        raise ValueError(f"duplicate registry entry: {type_}")
    if kind == "token-alias" and not alias_to:
        raise ValueError(f"token-alias entry without alias_to: {type_}")
    REGISTRY[type_] = Entry(type_, kind, handler, dict(hosts or {}), alias_to)


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
}

_BODY_HOSTS = {f"{p}:<children>": "splice-repeat" for p in (
    "action_group_body", "controladdin_body", "dataset_mod_body", "declaration_body", "interface_body",
    "layout_container_body", "preproc_conditional", "preproc_conditional_controladdin",
    "preproc_conditional_layout_mixed", "preproc_conditional_query", "preproc_conditional_report",
    "preproc_conditional_xmlport", "preproc_split_var_section_tail", "query_body", "report_body",
    "xmlport_body")}
# preproc_conditional_var and var_body are NOT body hosts any more: since the
# item-8 fix they admit only variable declarations (grammar.js var_body /
# preproc_conditional_var). preproc_split_var_section_tail holds body elements
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
                                   "preproc_split_if_then_begin_else_shared:<children>")},
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

# --- registered, not yet lowered (milestones 2-3). Unsupported is explicit, never a default.
for t in ("preproc_conditional_actions", "preproc_conditional_case", "preproc_conditional_case_patterns",
          "preproc_conditional_controladdin", "preproc_conditional_dataset", "preproc_conditional_expression_tail",
          "preproc_conditional_fieldgroups", "preproc_conditional_fields", "preproc_conditional_impl_values",
          "preproc_conditional_keys", "preproc_conditional_labels", "preproc_conditional_layout",
          "preproc_conditional_layout_mixed", "preproc_conditional_link_values",
          "preproc_conditional_list_elements", "preproc_conditional_object", "preproc_conditional_option_members",
          "preproc_conditional_permissions", "preproc_conditional_query", "preproc_conditional_rendering",
          "preproc_conditional_report", "preproc_conditional_table_relation", "preproc_conditional_var",
          "preproc_conditional_where", "preproc_conditional_xmlport", "preproc_fragmented_else_tail",
          "preproc_guarded_statement", "preproc_operand_prefix", "preproc_split_brace_close",
          "preproc_split_brace_close_if_only", "preproc_split_call_statement", "preproc_split_case_branch",
          "preproc_split_case_extended", "preproc_split_code_block_over_endif", "preproc_split_complete_body",
          "preproc_split_declaration", "preproc_split_else_begin_over_endif", "preproc_split_field",
          "preproc_split_if_begin_asymmetric", "preproc_split_if_begin_else", "preproc_split_if_else_statement",
          "preproc_split_if_statement", "preproc_split_if_then_begin", "preproc_split_if_then_begin_else_shared",
          "preproc_split_procedure_body", "preproc_split_procedure_preamble", "preproc_split_report_brace_close",
          "preproc_split_report_dataitem_header", "preproc_split_report_dataitem_open_over_endif",
          "preproc_split_table_field"):
    register(t, "unsupported")

# Added with the var_body fix (deferred-work item 8). Lowering must merge each
# branch's `variables` into the PRECEDING sibling var_section — a cross-sibling
# rewrite the engine has no fragment for yet (milestone 2).
register("preproc_split_var_section_tail", "unsupported")

# Added with the BC 29 family-I fixes. preproc_conditional_arguments splices
# its branch arguments into argument_list (a list-group, like the other
# preproc_conditional_* lists); preproc_split_permissions_property assembles
# one property per branch from that branch's head plus the shared tail.
register("preproc_conditional_arguments", "unsupported")
register("preproc_split_permissions_property", "unsupported")
# BC 29 family E: per-branch header, shared body after #endif (assembler shape).
register("preproc_split_key", "unsupported")
register("preproc_split_modify", "unsupported")
# BC 29 family D: only the #if-taken configuration is valid AL, so lowering the
# other configuration must report cannot-validate, never a discrepancy.
register("preproc_split_table_field_open", "unsupported")

# Non-prefixed special type: completes an earlier table relation (spec section 3).
register("else_table_relation_fragment", "unsupported")

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
    return problems
