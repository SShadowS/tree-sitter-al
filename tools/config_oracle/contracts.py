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
    REGISTRY[type_] = Entry(type_, kind, handler, dict(hosts or {}), alias_to)


def resolve_handler(entry):
    mod, _, name = entry.handler.rpartition(".")
    return getattr(importlib.import_module(mod), name)


# --- statement-position hosts, shared by every node that fills a _statement slot
_STATEMENT_HOSTS = {
    "statement_block:<children>": "splice-repeat",
    "preproc_conditional_statement:<children>": "splice-repeat",
    "asserterror_statement:body": "single-slot", "case_branch:body": "single-slot",
    "for_statement:body": "single-slot", "foreach_statement:body": "single-slot",
    "if_statement:else_branch": "single-slot", "if_statement:then_branch": "single-slot",
    "while_statement:body": "single-slot", "with_statement:body": "single-slot",
    "preproc_guarded_statement:then_branch": "single-slot",
    "preproc_split_case_branch:body": "single-slot", "preproc_split_case_end_branch:body": "single-slot",
    "preproc_split_case_extended:body": "single-slot",
    "preproc_split_if_else_statement:else_branch": "single-slot",
    # then_branch is set once per #if/#elif/#else head (_preproc_if_then_else_head,
    # grammar.js:3583, used in the main #if arm at :3566 and repeated for every
    # #elif/#else arm at :3573-3574) — node-types.json marks this field
    # multiple: true, and a #if/#elif/#else split parses two sibling
    # then_branch-fielded assignment_statement nodes with zero errors.
    "preproc_split_if_else_statement:then_branch": "splice-repeat",
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
    "preproc_conditional_var", "preproc_conditional_xmlport", "query_body", "report_body", "xmlport_body")}

# preproc_split_procedure also lands inside var_body (grammar.js:3284,
# `var_body: $ => repeat1(choice(..., $.preproc_split_procedure))`) — the same
# repeat1-of-choice shape as declaration_body and friends, so splice-repeat.
_BODY_HOSTS_WITH_VAR = dict(_BODY_HOSTS, **{"var_body:<children>": "splice-repeat"})

_ROUTINE_TAIL_HOSTS = {f"{p}:<children>": "single-slot" for p in (
    "preproc_split_procedure", "procedure", "trigger_declaration")}
# preproc_split_procedure_preamble is the one exception: its own header repeats
# per branch (_procedure_preamble is used once for #if, then again for every
# #elif via `repeat(seq($.preproc_elif, $._procedure_preamble))`, and once more
# for an optional #else — grammar.js:3085-3089), and each branch's header may
# carry its own preproc_conditional_var_block. A #if/#elif pair each nesting a
# var-guarding #if parses as two sibling preproc_conditional_var_block children
# of one preproc_split_procedure_preamble, zero errors — genuinely repeat, not
# single-slot, unlike the other three routine-tail hosts.
_ROUTINE_TAIL_HOSTS["preproc_split_procedure_preamble:<children>"] = "splice-repeat"

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
                "procedure:<children>": "splice-repeat", "source_file:<children>": "splice-repeat"})
register("preproc_split_code_block_end", "assembler",
         "tools.config_oracle.lowering.assemblers.split_code_block_end",
         hosts={"code_block:<children>": "consumed"})
register("preproc_split_case_statement_end", "assembler",
         "tools.config_oracle.lowering.assemblers.split_case_statement_end", hosts=_STATEMENT_HOSTS)
register("preproc_split_case_end_branch", "fragment", None,
         hosts={"preproc_split_case_statement_end:<children>": "consumed"})
register("preproc_split_procedure", "assembler", "tools.config_oracle.lowering.assemblers.split_procedure",
         hosts=dict(_BODY_HOSTS_WITH_VAR))

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
