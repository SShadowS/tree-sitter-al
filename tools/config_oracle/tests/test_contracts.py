import json

import pytest

from tools.config_oracle import contracts
from tools.query_coverage import loader


def node_types():
    return json.loads((loader.REPO_ROOT / "src" / "node-types.json").read_text(encoding="utf-8"))


def test_census_is_clean_against_the_shipped_grammar():
    assert contracts.census(node_types()) == []


def test_duplicate_registration_raises():
    with pytest.raises(ValueError):
        contracts.register("preproc_conditional", "branch-select")


def test_census_catches_an_unregistered_type():
    nt = node_types() + [{"type": "preproc_split_new_shape", "named": True}]
    assert any("unregistered" in p for p in contracts.census(nt))


def test_census_catches_a_new_host_slot():
    nt = node_types()
    for t in nt:
        if t["type"] == "while_statement":
            t["fields"]["body"]["types"].append({"type": "preproc_conditional_var_block", "named": True})
    assert any("host" in p for p in contracts.census(nt))


def test_census_catches_a_stale_host_slot():
    # preproc_conditional_statement is registered as a host of if_statement:then_branch.
    # Drop that alternative from the shipped grammar's own declaration and the
    # registry's entry is now claiming a slot the (modified) grammar no longer offers.
    nt = node_types()
    for t in nt:
        if t["type"] == "if_statement":
            t["fields"]["then_branch"]["types"] = [
                x for x in t["fields"]["then_branch"]["types"] if x["type"] != "preproc_conditional_statement"
            ]
    assert any("stale host slot" in p for p in contracts.census(nt))


def test_pragma_only_hosts_are_splice_repeat():
    # field_declaration (grammar.js ~1593, `repeat($.preproc_pragma_only)`) and
    # procedure/preproc_split_procedure (grammar.js ~2961-2966, `_procedure_tail`'s
    # `repeat1($.preproc_pragma_only)`/`repeat($.preproc_pragma_only)` arms) all wrap
    # preproc_pragma_only in a repeat: two consecutive #if/#pragma/#endif blocks parse
    # as two sibling preproc_pragma_only nodes with zero errors, so single-slot (which
    # would reject more than one) is wrong for all three.
    hosts = contracts.REGISTRY["preproc_pragma_only"].hosts
    assert hosts["field_declaration:<children>"] == "splice-repeat"
    assert hosts["procedure:<children>"] == "splice-repeat"
    assert hosts["preproc_split_procedure:<children>"] == "splice-repeat"
    assert hosts["source_file:<children>"] == "splice-repeat"


def test_split_procedure_preamble_var_block_host_is_optional_slot():
    # _procedure_preamble (grammar.js:3074-3080) has
    # `optional(choice($.var_section, $.preproc_conditional_var_block))` — a single
    # optional, never a repeat of preproc_conditional_var_block itself. It is
    # inlined once per ARM of preproc_split_procedure_preamble's own #if/#elif/#else
    # structure (grammar.js:3085-3089), so two var-block nodes seen in one parse are
    # one per arm of the OUTER conditional, not a genuine repeat at one position —
    # same shape as its three siblings (procedure, trigger_declaration,
    # preproc_split_procedure), all at most one node. The slot is optional(...) in
    # both _procedure_preamble (grammar.js:3075-3079) and _routine_regular_body
    # (grammar.js:3005-3008), so zero nodes is legal: optional-slot.
    hosts = contracts.REGISTRY["preproc_conditional_var_block"].hosts
    assert hosts["preproc_split_procedure_preamble:<children>"] == "optional-slot"
    assert hosts["procedure:<children>"] == "optional-slot"
    assert hosts["trigger_declaration:<children>"] == "optional-slot"
    assert hosts["preproc_split_procedure:<children>"] == "optional-slot"


def test_split_if_else_then_branch_host_is_single_slot():
    # then_branch is `fieldedStatement($, 'then_branch')` (grammar.js:70-76) inside
    # _preproc_if_then_else_head (grammar.js:3583-3589) — one field, never a repeat,
    # set once per #if/#elif/#else ARM of preproc_split_if_else_statement itself.
    # node-types.json's multiple: true reflects the field recurring across arms, not
    # one arm producing more than one node — same shape as if_statement:then_branch.
    for owner in ("preproc_conditional_statement", "preproc_split_case_statement_end"):
        hosts = contracts.REGISTRY[owner].hosts
        assert hosts["preproc_split_if_else_statement:then_branch"] == "single-slot"
        assert hosts["preproc_split_if_else_statement:else_branch"] == "single-slot"


def test_statement_slot_optionality():
    # asserterror_statement: `optional(field('body', $._statement_inner))`
    # (grammar.js:4694) -> optional-slot. Every other statement field is a bare
    # fieldedStatement (grammar.js:70-76, 4286-4304) -> mandatory single-slot.
    for owner in ("preproc_conditional_statement", "preproc_split_case_statement_end"):
        hosts = contracts.REGISTRY[owner].hosts
        assert hosts["asserterror_statement:body"] == "optional-slot"
        for slot in ("if_statement:then_branch", "if_statement:else_branch", "case_branch:body",
                     "for_statement:body", "while_statement:body"):
            assert hosts[slot] == "single-slot", slot


def test_token_alias_requires_alias_to():
    with pytest.raises(ValueError):
        contracts.register("preproc_test_alias_without_target", "token-alias", "x.y")
    assert "preproc_test_alias_without_target" not in contracts.REGISTRY


@pytest.mark.xfail(reason="handlers land in Tasks 10 and 12", strict=True)
def test_every_handler_resolves():
    for e in contracts.REGISTRY.values():
        if e.handler:
            assert contracts.resolve_handler(e) is not None, e.type
