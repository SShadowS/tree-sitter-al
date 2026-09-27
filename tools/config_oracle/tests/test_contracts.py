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


def test_split_procedure_preamble_var_block_host_is_splice_repeat():
    # preproc_split_procedure_preamble repeats its header per branch
    # (grammar.js ~3085-3089, `repeat(seq($.preproc_elif, $._procedure_preamble))`),
    # and each branch's header may carry its own preproc_conditional_var_block: a
    # #if/#elif pair each nesting a var-guarding #if parses as two sibling
    # preproc_conditional_var_block children, zero errors — unlike its three siblings
    # (procedure, trigger_declaration, preproc_split_procedure), which only ever have one.
    hosts = contracts.REGISTRY["preproc_conditional_var_block"].hosts
    assert hosts["preproc_split_procedure_preamble:<children>"] == "splice-repeat"
    assert hosts["procedure:<children>"] == "single-slot"
    assert hosts["trigger_declaration:<children>"] == "single-slot"
    assert hosts["preproc_split_procedure:<children>"] == "single-slot"


def test_split_if_else_then_branch_host_is_splice_repeat():
    # then_branch is set once per #if/#elif/#else head (_preproc_if_then_else_head,
    # grammar.js:3583), and node-types.json marks the field multiple: true. A
    # #if/#elif split parses two sibling then_branch-fielded statements, zero errors.
    for owner in ("preproc_conditional_statement", "preproc_split_case_statement_end"):
        hosts = contracts.REGISTRY[owner].hosts
        assert hosts["preproc_split_if_else_statement:then_branch"] == "splice-repeat"
        assert hosts["preproc_split_if_else_statement:else_branch"] == "single-slot"


@pytest.mark.xfail(reason="handlers land in Tasks 10 and 12", strict=True)
def test_every_handler_resolves():
    for e in contracts.REGISTRY.values():
        if e.handler:
            assert contracts.resolve_handler(e) is not None, e.type
