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


@pytest.mark.xfail(reason="handlers land in Tasks 10 and 12", strict=True)
def test_every_handler_resolves():
    for e in contracts.REGISTRY.values():
        if e.handler:
            assert contracts.resolve_handler(e) is not None, e.type
