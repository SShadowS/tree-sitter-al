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
    rows = registry.load(Path(__file__).parent.parent / "registry.tsv")   # populated by Task 4
    assert rows and all(r.role in registry.ROLES for r in rows)


def _mh():
    g = grammar.load(MINI)
    pairs = census.census(g)
    k = next(k for k, r in pairs if r.host == "caller")
    return g, k


def _row(k, hosts, reason="same rules"):
    return registry.Row(k, hosts, "list-separator", "f", "x ⟨HOLE⟩", "", reason, "a, b")


def test_multi_host_row_covers_all_and_exposes_witness():
    g = grammar.load(MINI)
    pairs = census.census(g)
    k, hs = next((k, [r.host for kk, r in pairs if kk == k]) for k, _ in pairs
                 if len([r for kk, r in pairs if kk == k]) > 1)
    row = _row(k, ",".join(hs))
    assert row.hosts == tuple(hs) and row.witness == hs[0]
    rest = [_row(kk, r.host) for kk, r in pairs if kk != k]
    assert registry.gate(pairs, [row] + rest) == ([], [], [])


def test_multi_host_without_reason_invalid():
    g = grammar.load(MINI)
    pairs = census.census(g)
    k, hs = next((k, [r.host for kk, r in pairs if kk == k]) for k, _ in pairs
                 if len([r for kk, r in pairs if kk == k]) > 1)
    assert registry.gate(pairs, [_row(k, ",".join(hs), "")])[2]


def test_new_caller_missing_despite_multi_host_row():
    g = grammar.load(MINI)
    for h in ("host_a", "host_b"):
        g["rules"][h] = {"type": "SEQ", "members": [{"type": "STRING", "value": h}, {"type": "SYMBOL", "name": "_helper"}]}
    pairs = census.census(g)
    k = next(k for k, r in pairs if r.host == "host_a")
    row = _row(k, "host_a,host_b")
    g["rules"]["host_c"] = {"type": "SEQ", "members": [{"type": "STRING", "value": "c"}, {"type": "SYMBOL", "name": "_helper"}]}
    missing, _, _ = registry.gate(census.census(g), [row])
    assert any(r.host == "host_c" and kk == k for kk, r in missing)


def test_listed_host_not_a_route_is_stale():
    g, k = _mh()
    _, stale, _ = registry.gate(census.census(g), [_row(k, "caller,nonexistent")])
    assert stale


def test_pair_covered_twice_invalid():
    g, k = _mh()
    _, _, invalid = registry.gate(census.census(g), [_row(k, "caller"), _row(k, "caller")])
    assert invalid


def test_cli_bad_header_and_missing_registry_exit_2(tmp_path, monkeypatch):
    from tools.b7_audit import __main__ as m
    bad = tmp_path / "r.tsv"
    bad.write_text("k" + chr(9) + "h" + chr(9) + "terminator" + chr(10), encoding="utf-8")
    monkeypatch.setattr(m, "REGISTRY", bad)
    assert m.main(["census", "--check"]) == 2
    monkeypatch.setattr(m, "REGISTRY", tmp_path / "absent.tsv")
    assert m.main(["census", "--check"]) == 2


def test_templated_row_needs_plain():
    p = [("k", census.Route("h", ("h",)))]
    no_plain = registry.Row("k", "h", "terminator", "f", "x ⟨HOLE⟩", "", "", "")
    assert registry.gate(p, [no_plain])[2]
    assert not registry.gate(p, [registry.Row("k", "h", "terminator", "f", "x ⟨HOLE⟩", "", "", "y;")])[2]


def test_load_plain_column(tmp_path):
    f = tmp_path / "r.tsv"
    f.write_text(registry.HEADER + "\nk\th\tterminator\tf\ta ⟨HOLE⟩\t\t\tI := 1;\\nJ := 2;\n", encoding="utf-8")
    (r,) = registry.load(f)
    assert registry.HEADER.endswith("\treason\tplain") and r.plain == "I := 1;\nJ := 2;"


# --- key aliases (B7b-3 Task 4 ruling) ------------------------------------------------------------
def _alias_world():
    """The live key `occ:new:0` has host `h1` in the grammar; `occ:old:0` is gone but its rows cover h1 and h2."""
    pairs = [("occ:new:0", census.Route("h1", ("h1",)))]
    old = [registry.Row("occ:old:0", "h1", "terminator", "fam", "x ⟨HOLE⟩", "", "", "x;"),
           registry.Row("occ:old:0", "h2", "terminator", "fam", "x ⟨HOLE⟩", "", "", "x;")]
    live = [registry.Row("occ:new:0", "h1", "terminator", "fam", "x ⟨HOLE⟩", "occ:old:0", "moved", "x;")]
    return pairs, old + live


def _alias(**kw):
    a = dict(retired="occ:old:0", live="occ:new:0", role="terminator", family="fam", reason="moved", commit="abc")
    a.update(kw)
    return registry.Alias(**a)


def test_valid_alias_keeps_retired_rows():
    pairs, rows = _alias_world()
    assert registry.gate(pairs, rows, [_alias()]) == ([], [], [])


def test_unaliased_retired_key_is_stale():
    pairs, rows = _alias_world()
    _, stale, _ = registry.gate(pairs, rows)
    assert {r.route_host for r in stale} == {"h1", "h2"}


def test_alias_to_a_missing_live_key_fails():
    pairs, rows = _alias_world()
    _, stale, invalid = registry.gate(pairs, rows, [_alias(live="occ:nowhere:0")])
    assert stale and any("not in the grammar" in why for _, why in invalid)


def test_alias_role_or_family_mismatch_fails():
    pairs, rows = _alias_world()
    for bad in (_alias(role="list-separator"), _alias(family="other")):
        _, stale, invalid = registry.gate(pairs, rows, [bad])
        assert stale and any("role/family" in why for _, why in invalid)
    live_role = [r if r.route_host != "h1" or r.equiv == "" else
                 registry.Row(r.key, r.route_host, "fixed-separator", r.family, r.template, r.equiv, r.reason, r.plain)
                 for r in rows]
    _, stale, invalid = registry.gate(pairs, live_role, [_alias()])
    assert stale and any("no registry row with role" in why for _, why in invalid)


def test_alias_with_na_rows_on_both_sides_passes():
    """B7b-3 Task 8: a key with `na` hosts aliases with its na rows; na is exempt from the role check only."""
    pairs, rows = _alias_world()
    pairs = pairs + [("occ:new:0", census.Route("h2", ("h2",)))]
    rows = ([r if r.route_host != "h2" else
             registry.Row(r.key, r.route_host, "na", r.family, "", "", "no valid AL here", "") for r in rows]
            + [registry.Row("occ:new:0", "h2", "na", "fam", "", "occ:old:0", "no valid AL here", "")])
    assert registry.gate(pairs, rows, [_alias()]) == ([], [], [])
    only_na = [r for r in rows if not (r.key == "occ:new:0" and r.role == "terminator")]
    _, stale, invalid = registry.gate(pairs, only_na, [_alias()])
    assert stale and any("no registry row with role" in why for _, why in invalid)


def test_alias_whose_retired_rows_are_all_na_fails():
    """B7b-3 Task 10 carry: the retired side, like the live side, needs one row with the alias's role."""
    pairs, rows = _alias_world()
    rows = [r if r.key != "occ:old:0" else
            registry.Row(r.key, r.route_host, "na", r.family, "", "", "no valid AL here", "") for r in rows]
    _, stale, invalid = registry.gate(pairs, rows, [_alias()])
    assert stale and any("occ:old:0 has no registry row with role" in why for _, why in invalid)


def test_alias_whose_live_rows_cover_a_new_host_fails():
    pairs, rows = _alias_world()
    pairs = pairs + [("occ:new:0", census.Route("h3", ("h3",)))]
    rows = rows + [registry.Row("occ:new:0", "h3", "terminator", "fam", "x ⟨HOLE⟩", "occ:old:0", "moved", "x;")]
    _, stale, invalid = registry.gate(pairs, rows, [_alias()])
    assert stale and any("never covered" in why for _, why in invalid)


def _factored_world():
    """D1 C1: `bnd:r1:f:end` (host s1) and `bnd:r2:f:end` (host s2) moved into the hidden `_h` factored out of r1
    and r2, so the live key `bnd:_h:f:end` has the hosts r1 and r2."""
    row = lambda k, h, eq="": registry.Row(k, h, "terminator", "fam", "x ⟨HOLE⟩", eq, "moved" if eq else "", "x;")
    pairs = [("bnd:_h:f:end", census.Route("r1", ("r1",))), ("bnd:_h:f:end", census.Route("r2", ("r2",)))]
    rows = [row("bnd:r1:f:end", "s1"), row("bnd:r2:f:end", "s2"),
            row("bnd:_h:f:end", "r1", "bnd:r1:f:end"), row("bnd:_h:f:end", "r2", "bnd:r2:f:end")]
    aliases = [_alias(retired="bnd:r1:f:end", live="bnd:_h:f:end"), _alias(retired="bnd:r2:f:end", live="bnd:_h:f:end")]
    return pairs, rows, aliases


def test_alias_live_host_may_be_the_factored_rule():
    pairs, rows, aliases = _factored_world()
    _, stale, invalid = registry.gate(pairs, rows, aliases)
    assert stale == [] and invalid == []


def test_alias_live_host_outside_factored_rules_fails():
    """A guard: passes before and after the D1 extension (R11)."""
    pairs, rows, aliases = _factored_world()
    pairs = pairs + [("bnd:_h:f:end", census.Route("r3", ("r3",)))]
    rows = rows + [registry.Row("bnd:_h:f:end", "r3", "terminator", "fam", "x ⟨HOLE⟩", "bnd:r1:f:end", "moved", "x;")]
    _, stale, invalid = registry.gate(pairs, rows, aliases)
    assert any("never covered" in why for _, why in invalid)


def test_alias_live_host_must_be_its_own_rows_factored_rule():
    """A live row may cover a factored host only when that host is the rule its own `equiv` was factored out of."""
    pairs, rows, aliases = _factored_world()
    rows = [r for r in rows if r.key != "bnd:_h:f:end"]
    rows += [registry.Row("bnd:_h:f:end", "r2", "terminator", "fam", "x ⟨HOLE⟩", "bnd:r1:f:end", "moved", "x;"),
             registry.Row("bnd:_h:f:end", "r1", "terminator", "fam", "x ⟨HOLE⟩", "bnd:r2:f:end", "moved", "x;")]
    _, _, invalid = registry.gate(pairs, rows, aliases)
    assert any("never covered" in why for _, why in invalid)


def test_alias_live_row_without_equiv_on_a_factored_host_is_invalid_not_a_crash():
    """A live row with an empty `equiv` names no rule, so a factored host on it is reported, not an IndexError."""
    pairs, rows, aliases = _factored_world()
    rows = rows + [registry.Row("bnd:_h:f:end", "r1", "terminator", "fam", "x ⟨HOLE⟩", "", "", "x;")]
    _, _, invalid = registry.gate(pairs, rows, aliases)
    assert any("never covered" in why for _, why in invalid)


def test_alias_live_row_equiv_must_be_an_aliased_retired_key():
    """The factored rule is not enough: `equiv` must be the retired key of an alias to this live key."""
    pairs, rows, aliases = _factored_world()
    rows = [r if not (r.key == "bnd:_h:f:end" and r.route_host == "r1") else
            registry.Row(r.key, "r1", "terminator", "fam", "x ⟨HOLE⟩", "bnd:r1:other:end", "moved", "x;")
            for r in rows]
    _, _, invalid = registry.gate(pairs, rows, aliases)
    assert any("never covered" in why for _, why in invalid)


def test_same_rule_alias_cannot_add_the_rule_itself_as_host():
    """`occ:R:a -> occ:R:b` moves a slot inside R; R is not a rule the slot was factored out of."""
    row = lambda k, h, eq="": registry.Row(k, h, "terminator", "fam", "x ⟨HOLE⟩", eq, "moved" if eq else "", "x;")
    pairs = [("occ:R:1.0", census.Route("s1", ("s1",))), ("occ:R:1.0", census.Route("R", ("R",)))]
    rows = [row("occ:R:3.0", "s1"), row("occ:R:1.0", "s1", "occ:R:3.0"), row("occ:R:1.0", "R", "occ:R:3.0")]
    _, _, invalid = registry.gate(pairs, rows, [_alias(retired="occ:R:3.0", live="occ:R:1.0")])
    assert any("never covered" in why for _, why in invalid)


def test_alias_for_a_key_still_in_the_grammar_fails():
    pairs, rows = _alias_world()
    pairs = pairs + [("occ:old:0", census.Route("h1", ("h1",)))]
    _, _, invalid = registry.gate(pairs, rows, [_alias()])
    assert any("still in the grammar" in why for _, why in invalid)


def test_real_registry_with_aliases_passes_census():
    g = grammar.load(Path("src/grammar.json"))
    here = Path(__file__).parent.parent
    rows, aliases = registry.load(here / "registry.tsv"), registry.load_aliases(here / "key-aliases.tsv")
    assert aliases
    assert registry.gate(census.census(g), rows, aliases) == ([], [], [])
    assert registry.gate(census.census(g), rows)[1], "without the aliases the retired rows are stale"
