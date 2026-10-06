from pathlib import Path

from tools.b7_audit import census, grammar, registry

MINI = Path(__file__).with_name("mini_grammar.json")


def test_helper_reached_from_two_hosts():
    g = grammar.load(MINI)
    # brief's `caller` is visible (itself a host); a hidden `_mid` makes both hosts reach _helper
    g["rules"]["_mid"] = {"type": "SYMBOL", "name": "_helper"}
    for h in ("host_a", "host_b"):
        g["rules"][h] = {"type": "SEQ", "members": [{"type": "STRING", "value": h}, {"type": "SYMBOL", "name": "_mid"}]}
    hosts = {r.host for r in census.routes(g, "_helper")}
    assert {"host_a", "host_b"} <= hosts


def hosts(g, rule):
    return {r.host for r in census.routes(g, rule)}


def test_visible_target_climbs_to_callers_root_and_expression_stop():
    g = grammar.load(MINI)
    assert hosts(g, "item") >= {"list", "hdr"}
    assert hosts(g, "list") == {"list"}                       # root: no caller
    g["rules"]["_expression"] = {"type": "CHOICE", "members": [{"type": "SYMBOL", "name": "lit"}]}
    g["rules"]["lit"] = {"type": "STRING", "value": ","}
    g["rules"]["in_expr"] = {"type": "SYMBOL", "name": "lit"}
    assert hosts(g, "lit") == {"lit", "in_expr"}
    census.census(g)                                          # cycles terminate


def test_new_caller_fails_gate_visible_callee():
    g = grammar.load(MINI)
    rows = [registry.Row(k, r.host, "list-separator", "f", "x ⟨HOLE⟩", "", "") for k, r in census.census(g)]
    g["rules"]["host_new"] = {"type": "SEQ", "members": [{"type": "STRING", "value": "n"}, {"type": "SYMBOL", "name": "list"}]}
    missing, _, _ = registry.gate(census.census(g), rows)
    assert any(r.host == "host_new" for _, r in missing)


def test_real_grammar_hosts():
    g = grammar.load(Path("src/grammar.json"))
    assert hosts(g, "field_list") >= {"key_declaration", "fieldgroup_declaration", "preproc_split_key"}
    assert hosts(g, "parameter_list") >= {"procedure", "interface_procedure", "trigger_declaration", "event_declaration"}
    assert hosts(g, "list_literal") >= {"list_literal", "in_expression"}


def test_header_required(tmp_path):
    import pytest
    f = tmp_path / "r.tsv"
    f.write_text("k" + chr(9) + "h" + chr(9) + "terminator", encoding="utf-8")
    with pytest.raises(ValueError):
        registry.load(f)


def test_stale_row_fails_gate():
    rows = [registry.Row("occ:gone:0", "gone", "list-separator", "f", "x ⟨HOLE⟩", "", "")]
    _, stale, _ = registry.gate([], rows)
    assert stale


def test_na_requires_reason():
    rows = [registry.Row("occ:list:1.0.0", "list", "na", "", "", "", "")]
    _, _, invalid = registry.gate([("occ:list:1.0.0", census.Route("list", ("list",)))], rows)
    assert invalid


def test_unknown_role_template_and_equiv_invalid():
    p = [("k", census.Route("h", ("h",)))]
    bad = [registry.Row("k", "h", "bogus", "", "", "", "r"),
           registry.Row("k", "h", "terminator", "f", "no hole", "", ""),
           registry.Row("k", "h", "qualifier", "", "", "same-as x", "")]
    for r in bad:
        assert registry.gate(p, [r])[2]
    assert not registry.gate(p, [registry.Row("k", "h", "qualifier", "", "", "", "")])[2]


def test_load_header_only_and_escapes(tmp_path):
    f = tmp_path / "r.tsv"
    f.write_text("# c\n" + registry.HEADER + "\nk\th\tterminator\tf\ta\\n⟨HOLE⟩\t\t\n", encoding="utf-8")
    (r,) = registry.load(f)
    assert r.template == "a\n⟨HOLE⟩" and r.equiv == ""
    assert registry.load(Path(__file__).parent.parent / "registry.tsv") == []
