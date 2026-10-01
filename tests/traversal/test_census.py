"""tools/traversal_census.py (F0, D2): the policy against node-types.json and the registry."""
import copy
import importlib.util
import json
import re
import subprocess
import sys

import pytest

import support
from tools.config_oracle import contracts

SCRIPT = support.REPO / "tools" / "traversal_census.py"
_spec = importlib.util.spec_from_file_location("traversal_census", SCRIPT)
census_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(census_mod)


def policy():
    return json.loads(support.POLICY.read_text(encoding="utf-8"))


def node_types():
    return json.loads((support.REPO / "src" / "node-types.json").read_text(encoding="utf-8"))


def run(pol=None, nt=None, registry=None):
    return census_mod.census(pol or policy(), nt or node_types(), registry or contracts.REGISTRY,
                             contracts.host_slots)


def test_census_is_clean_against_the_shipped_grammar():
    assert run() == []


def test_cli_exits_0_and_reports_the_entry_count():
    p = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr
    assert re.search(r"traversal census: \d+ entries, 0 problem\(s\)", p.stdout)


def test_cli_exits_2_when_the_policy_is_missing(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "node-types.json").write_text("[]")
    p = subprocess.run([sys.executable, str(SCRIPT), "--root", str(tmp_path)], capture_output=True, text=True)
    assert p.returncode == 2, p.stdout + p.stderr


def test_expression_tail_misclassified_as_a_container_fails():
    """The D2 mutation: the spec's first-named exception, given the wrong class."""
    pol = policy()
    pol["types"]["preproc_conditional_expression_tail"]["class"] = "branch-container"
    problems = run(pol)
    assert ("class disagrees with the registry: preproc_conditional_expression_tail is branch-container, "
            "registry kind assembler means assembler") in problems


def test_an_unprefixed_type_holding_a_directive_is_detected():
    """Detection is structural: no name rule could find this type."""
    nt = node_types() + [{"type": "brand_new_split", "named": True, "children": {
        "multiple": True, "required": True,
        "types": [{"type": "preproc_if", "named": True}, {"type": "preproc_endif", "named": True}]}}]
    assert run(nt=nt) == ["unclassified: brand_new_split (holds a conditional directive)"]


def test_a_preproc_named_type_with_no_signal_is_not_flagged():
    """The converse: a `preproc_` name alone classifies nothing. (Its registry entry is
    contracts.census's job, which is prefix-based by design; this gate is not.)"""
    nt = copy.deepcopy(node_types()) + [{"type": "preproc_lookalike", "named": True}]
    for t in nt:
        if t["type"] == "statement_block":
            t["children"]["types"].append({"type": "preproc_lookalike", "named": True})
    assert run(nt=nt) == []


def test_an_unregistered_unprefixed_fragment_is_detected_through_its_parents():
    pol = policy()
    del pol["types"]["else_table_relation_fragment"]
    registry = {k: v for k, v in contracts.REGISTRY.items() if k != "else_table_relation_fragment"}
    assert run(pol, registry=registry) == [
        "unclassified: else_table_relation_fragment (only ever a child of special types)"]


def test_a_stale_entry_fails():
    pol = policy()
    pol["types"]["gone_type"] = {"class": "assembler", "arm_boundary": "none", "reason": "gone"}
    assert "stale entry, type no longer declared: gone_type" in run(pol)


def test_a_host_policy_that_disagrees_with_the_registry_fails():
    pol = policy()
    pol["types"]["preproc_conditional_permissions"]["hosts"]["tabledata_permission_list:<children>"] = "splice-repeat"
    assert run(pol) == ["host policy disagrees with the registry: preproc_conditional_permissions in "
                        "tabledata_permission_list:<children>: splice-repeat vs list-run"]


def test_a_hand_classified_container_host_slot_is_checked_against_node_types():
    """case_patterns is registry-unsupported, so its hosts come from the policy alone."""
    pol = policy()
    del pol["types"]["preproc_conditional_case_patterns"]["hosts"]["case_branch:<children>"]
    assert run(pol) == ["host slot not classified: preproc_conditional_case_patterns in case_branch:<children>"]


def test_an_unsupported_registry_type_may_not_be_ordinary():
    pol = policy()
    pol["types"]["preproc_split_key"]["class"] = "ordinary"
    assert "registry-unsupported type classified ordinary: preproc_split_key" in run(pol)


def test_arm_boundary_is_checked_against_the_declared_children():
    pol = policy()
    pol["types"]["preproc_split_block_end_in_else"]["arm_boundary"] = "own-directives"
    assert run(pol) == ["arm_boundary of preproc_split_block_end_in_else is own-directives, "
                        "its declared children say cross-node"]


@pytest.mark.parametrize("field, value", [("reason", " "), ("class", "special")])
def test_entry_shape_is_enforced(field, value):
    pol = policy()
    pol["types"]["pragma"][field] = value
    assert run(pol)


def test_no_traversal_source_classifies_by_name():
    """D2: classification is never by prefix. The walkers name no node type at all."""
    sources = [support.MODULE, support.REPO / "traversal" / "index.js",
               support.REPO / "bindings" / "rust" / "traversal.rs", SCRIPT]
    for path in sources:
        if not path.exists():
            continue                     # the JS and Rust walkers arrive in later tasks
        text = path.read_text(encoding="utf-8").split("#[cfg(test)]")[0]   # Rust: not its tests
        assert not re.search(r"(startswith|startsWith|starts_with)\(\s*['\"]preproc", text), path
        if path != SCRIPT:
            assert "preproc" not in text, f"{path.name} names a node type"
