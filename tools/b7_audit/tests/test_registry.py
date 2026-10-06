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


def test_visible_target_is_own_host_and_cycles_terminate():
    g = grammar.load(MINI)
    assert [r.host for r in census.routes(g, "list")] == ["list"]
    census.census(g)


def test_new_caller_fails_gate():
    g = grammar.load(MINI)
    rows = [registry.Row(k, r.host, "list-separator", "f", "x ⟨HOLE⟩", "", "") for k, r in census.census(g)]
    assert registry.gate(census.census(g), rows) == ([], [], [])
    # a visible callee is its own host; a new caller is seen through a hidden callee
    g["rules"]["host_new"] = {"type": "SEQ", "members": [{"type": "STRING", "value": "n"}, {"type": "SYMBOL", "name": "_helper"}]}
    missing, stale, invalid = registry.gate(census.census(g), rows)
    assert any(r.host == "host_new" for _, r in missing)


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
