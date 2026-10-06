from collections import Counter
from pathlib import Path

from tools.config_oracle.directives import resolve
from tools.b7_audit import placements, registry

REGISTRY = Path(__file__).resolve().parents[1] / "registry.tsv"

ROW = registry.Row("occ:x:0", "x", "list-separator", "f",
                   "codeunit 50100 P { procedure Q() var A, B, C, D: Integer; begin Foo(⟨HOLE⟩); end; "
                   "procedure Foo(A: Integer; B: Integer; C: Integer) begin end; }", "", "", "A, B, C, D")


def flat(cell, env):
    return resolve(cell.source.encode(), env).masked.decode()


def test_assignments_every_subset_sorted():
    a = placements.assignments(("Y", "X"))
    assert a == [frozenset(), frozenset({"X"}), frozenset({"Y"}), frozenset({"X", "Y"})]


def test_sep_before_shape():
    c = {c.placement: c for c in placements.cells_for(ROW)}["sep-before"]
    assert "#if X" in c.source and c.symbols == ("X",)
    assert "A" in flat(c, frozenset()) and "B" not in flat(c, frozenset()).split("Foo(")[1]


def test_every_placement_meets_its_vector():
    # by construction: every intended-valid assignment flattens to a list with no doubled,
    # leading or trailing separator (unless the host allows holes), every other assignment does not
    cells = placements.cells_for(ROW)
    assert {"sep-after", "count-differs", "nested", "trail", "sep-after+comments", "trail+not"} <= {c.placement for c in cells}
    for c in cells:
        for env in placements.assignments(c.symbols):
            text = flat(c, env).split("Foo(", 1)[1].split(")", 1)[0]
            well_formed = placements.well_formed_list(text, ",")
            assert well_formed == (env in c.intended_valid), (c.placement, sorted(env), text)


def test_semi_in_arms_only_for_statement_hosts():
    cont = registry.Row("bnd:if_statement:condition:end", "if_statement", "continuation", "if-condition",
                        "codeunit 50100 P { procedure Q() var B: Boolean; begin if ⟨HOLE⟩ then; end; }", "", "", "B")
    assert "semi-in-arms" not in {c.placement.split("/")[0] for c in placements.cells_for(cont)}
    assert ("semi-in-arms", "host is not a statement whose expression may end it") in placements.skipped_for(cont)


def test_semi_in_arms_for_assignment():
    row = registry.Row("bnd:assignment_statement:value:end", "assignment_statement", "continuation", "assignment",
                       "codeunit 50100 P { procedure Q() var I: Integer; begin I := ⟨HOLE⟩; end; "
                       "procedure Bar() begin end; }", "", "", "1")
    c = {c.placement: c for c in placements.cells_for(row)}["semi-in-arms/arithmetic"]
    assert "Bar();" in flat(c, frozenset({"X"})) and "Bar();" not in flat(c, frozenset())


def test_na_and_token_only_skips():
    na = registry.Row("occ:y:0", "y", "na", "", "", "", "not reachable", "")
    assert placements.cells_for(na) == [] and placements.skipped_for(na)
    tok = registry.Row("occ:t:0", "t", "terminator", "statement-terminator",
                       "codeunit 50100 P { procedure Q() begin Bar()⟨HOLE⟩ end; procedure Bar() begin end; }",
                       "", "", ";")
    assert ("first-replace", "token-only hole") in placements.skipped_for(tok)
    assert "sep-only" in {c.placement for c in placements.cells_for(tok)}


def test_link_name_variants_keep_value_grammar():
    # query dataitem: DataItemLink (QueryDataItemLink) would keep a TableFilter value -> no variant
    rows = [r for r in registry.load(REGISTRY) if r.family == "link-list" and "DataItemTableFilter" in r.template]
    names = {c.placement.rsplit("@", 1)[1] for c in placements.cells_for(rows[0])}
    assert names == {"DataItemTableFilter"}
    why = "no witness container; covered by link-keying seeds (Task 6)"
    assert ("@RunPageLink", why) in placements.skipped_for(rows[0])
    assert ("@ColumnFilter", why) in placements.skipped_for(rows[0])


def _hole(text, cell):
    return text.encode()[cell.hole[0]:cell.hole[1]].decode()


def test_real_registry_generator_model_consistent():
    """Every cell over the real registry: the hole resolved alone is well-formed exactly when the
    placement assignment is intended valid; in the full source the hole reads the same or is wholly
    inactive (a template arm is off), and is active for at least one template assignment."""
    rows = registry.load(REGISTRY)
    ids, per_role = set(), Counter()
    for row in rows:
        cells = placements.cells_for(row)
        if not cells:
            assert placements.skipped_for(row), row
        for c in cells:
            assert c.id not in ids, c.id
            ids.add(c.id)
            per_role[row.role] += 1
            assert c.intended_valid, c.id                         # never invalid everywhere
            assert row.plain in c.plain and "⟨HOLE⟩" not in c.source
            hole_src = _hole(c.source, c)
            psyms = {s for s in c.symbols if s in ("X", "Y")}
            seen_active = False
            for env in placements.assignments(c.symbols):
                alone = resolve(hole_src.encode(), env & psyms).masked.decode()
                assert placements.well_formed(c, alone, env) == (env in c.intended_valid), (c.id, sorted(env), alone)
                full = _hole(flat(c, env), c)
                if full.strip():
                    assert full == alone, (c.id, sorted(env))
                    seen_active = True
            assert seen_active, c.id
    assert per_role["continuation"] and per_role["terminator"] and per_role["list-separator"]


CU = ("codeunit 50100 P {{ procedure Q() var I: Integer; Ok: Boolean; Intf: Interface IFoo; Intf2: Interface IFoo; "
      "R: Record T; Recs: array[2] of Record T; begin {body} end; procedure Bar() begin end; }} "
      "interface IFoo {{ }} table 50100 T {{ fields {{ field(1; K; Code[20]) {{ }} }} }}")


def _cells(row):
    return {c.placement: c for c in placements.cells_for(row)}


def test_terminator_trail_optional_before_end_until_and_procedure_begin():
    before_end = registry.Row("occ:s:0", "code_block", "terminator", "statement-terminator",
                              CU.format(body="Bar();\nif Ok then begin ⟨HOLE⟩ end;"), "", "", "Bar();")
    before_stmt = registry.Row("occ:s:1", "code_block", "terminator", "statement-terminator",
                               CU.format(body="⟨HOLE⟩\nBar();"), "", "", "Bar();")
    proc_tail = registry.Row("occ:p:0", "procedure", "terminator", "procedure-tail",
                             "codeunit 50100 P { procedure Z()\n⟨HOLE⟩\n#pragma warning disable AA0021\nbegin end; }",
                             "", "", ";")
    assert _cells(before_end)["trail"].intended_valid == frozenset(placements.assignments(("X",)))
    assert _cells(proc_tail)["trail"].intended_valid == frozenset(placements.assignments(("X",)))
    assert _cells(before_stmt)["trail"].intended_valid == frozenset({frozenset({"X"})})
    # template-dependent: `end` follows the hole only where TPL is defined (split-if-begin rows)
    mixed = [c for r in registry.load(REGISTRY) if r.family == "split-if-begin" and r.role == "terminator"
             for c in placements.cells_for(r) if c.placement == "trail"
             and 0 < len([e for e in c.intended_valid if "X" not in e]) < len(placements.assignments(c.symbols)) // 2]
    assert mixed


def test_word_operators_and_interface_slot():
    i = registry.Row("bnd:a:value:end", "assignment_statement", "continuation", "assignment",
                     CU.format(body="I := ⟨HOLE⟩;"), "", "", "1")
    b = registry.Row("bnd:a:value:end", "assignment_statement", "continuation", "assignment",
                     CU.format(body="Ok := ⟨HOLE⟩;"), "", "", "Ok")
    assert "suffix/word-arithmetic" in _cells(i) and "div" in _cells(i)["suffix/word-arithmetic"].source
    assert "suffix/xor" in _cells(b) and "xor" in _cells(b)["suffix/xor"].source
    rows = [r for r in registry.load(REGISTRY) if r.family == "type-test"]   # as_/is_expression left edges
    assert len(rows) == 4 and all(placements.cells_for(r) for r in rows)
    assert all(any("#if X\nas IFoo\n" in c.source for c in placements.cells_for(r)) for r in rows)


def test_quoted_and_keyword_element_samples():
    rows = registry.load(REGISTRY)
    var = next(r for r in rows if r.family == "var-names" and r.role == "list-separator")
    assert any('"X 6"' in c.source for c in placements.cells_for(var))
    opt = next(r for r in rows if r.family == "option-members" and r.plain.strip() == "A,B,C")
    assert any('"D E"' in c.source for c in placements.cells_for(opt))
    assert "ml-pairs" in placements.NO_IDENTIFIER_SAMPLES


def test_semi_in_arms_excluded_on_case_branch_witness():
    rows = [r for r in registry.load(REGISTRY) if r.family == "assignment" and r.witness == "case_branch"
            and ":right:" in r.key]                                        # the value, not the target
    assert rows and all(not any(c.placement.startswith("semi-in-arms") for c in placements.cells_for(r)) for r in rows)
    assert any(p == "semi-in-arms" and "case label" in why for p, why in placements.skipped_for(rows[0]))


def test_one_elem_move_modification_seed_guard_and_operand_first_only():
    rows = registry.load(REGISTRY)
    mv = next(r for r in rows if r.family == "move-modification" and r.role == "list-separator")
    assert "one-elem" not in _cells(mv) and any(p == "one-elem" for p, _ in placements.skipped_for(mv))
    seed = placements.Cell("s", "k", "h", "seed", "x", (), frozenset({frozenset()}), (0, 1), None)
    assert placements.well_formed(seed, "x") is None
    rec = registry.Row("bnd:m:object:start", "member_expression", "continuation", "member-access",
                       CU.format(body="⟨HOLE⟩.Init();"), "", "", "R")
    c = _cells(rec)["first-only/operand"]
    assert "Recs[1]" in c.source
