"""SILENT witnesses of the B7a audit (spec 8, Task 10 ruling): one representative cell (the lexicographically first
id) per (family, base placement) SILENT group of docs/b7-separator-continuation-matrix.md.

alc accepts the configurations in question and the parser is clean, but the tree is wrong. Each case asserts the
representative's CURRENT defect, so the grammar change that removes it makes the case fail:
  - "oracle:<config>:<status>": the config oracle reports that discrepancy for that configuration;
  - "refusal:<kind>": a witness flipped to its spec 6.4 named refusal (every configuration refused with <kind>);
  - "assertion": its row in tools/b7_audit/assertions.tsv (the cell row, else its class row; the first row of a
    duplicated key wins, as in report.py) does not hold.
The fix flips the case to require oracle `pass` and a holding assertion: "tree" (B7b-2 Phase A) requires both, the
assertion row being written from the contract. SILENT inputs never go into test/corpus/:
the quick tier reads corpus sources and cannot classify a discrepancy.

OVERACCEPT_NO_CORPUS pins two REJECTED/over-accepts groups whose every cell also has an oracle discrepancy in a
configuration alc rejects, so they cannot be corpus cases either: the parser is clean on input alc rejects (their alc
side is tools/alc_probe/cases/b7-audit/integer-list__holes-*__overaccept.al).
"""
import functools

import pytest

import tools.config_oracle.runner as oracle_runner
from tools.b7_audit import evidence, judge

SILENT = [
    ("bnd:_argument_expression:0:end@argument_list#consecutive/arithmetic", "tree"),  # arguments / consecutive, 2 cells (B7b-2 Phase A, Task 6: nested shape)
    ("bnd:_argument_expression:0:end@argument_list#nested/arithmetic", "tree"),  # arguments / nested, 2 cells (B7b-2 Phase A; region assembler, Task 5)
    ("bnd:additive_expression:left:end@case_branch#consecutive/arithmetic", "assertion"),  # binary-operand / consecutive, 22 cells
    ("bnd:additive_expression:left:end@case_branch#first-only/arithmetic", "tree"),  # binary-operand / first-only, 16 cells (B7b-2 Phase C, Task 10: an operand group is the additive left; Task 11: the oracle passes it)
    ("bnd:additive_expression:left:end@case_branch#nested/arithmetic", "assertion"),  # binary-operand / nested, 22 cells
    ("bnd:additive_expression:left:end@case_branch#suffix/arithmetic", "assertion"),  # binary-operand / suffix, 22 cells
    ("occ:event_declaration:0.5.0@controladdin_body#adjacent-compl", "oracle:X=0:discrepancy"),  # event-declaration / adjacent-compl, 6 cells
    ("occ:event_declaration:0.5.0@controladdin_body#elif", "oracle:X=0,Y=0:discrepancy"),  # event-declaration / elif, 6 cells
    ("occ:event_declaration:0.5.0@controladdin_body#empty", "oracle:X=0:discrepancy"),  # event-declaration / empty, 6 cells
    ("occ:event_declaration:0.5.0@controladdin_body#first-replace", "oracle:X=0:discrepancy"),  # event-declaration / first-replace, 6 cells
    ("occ:event_declaration:0.5.0@controladdin_body#nested", "oracle:X=0,Y=0:discrepancy"),  # event-declaration / nested, 6 cells
    ("occ:event_declaration:0.5.0@controladdin_body#sep-only", "oracle:X=0:discrepancy"),  # event-declaration / sep-only, 6 cells
    ("occ:event_declaration:0.5.0@controladdin_body#trail", "oracle:X=1:discrepancy"),  # event-declaration / trail, 6 cells
    ("bnd:preproc_conditional_expression_tail:operand:end@argument_list#consecutive/arithmetic", "tree"),  # expression-tail / consecutive, 2 cells (B7b-2 Task 9: two groups in an argument tail's arm read as an extra unary argument in preproc_conditional_arguments; fixed in Phase C, Task 10: _nested_tail prec.dynamic(1). The oracle never passed the old tree: it refused the TPL=1 configurations as list-separator cannot-validate, so only the assertion saw it)
    ("bnd:preproc_conditional_expression_tail:operand:end@argument_list#chain/arithmetic", "tree"),  # expression-tail / chain, 1 cells (B7b-2 Phase A; Task 5)
    ("bnd:preproc_conditional_expression_tail:operand:end@argument_list#suffix/arithmetic", "tree"),  # expression-tail / suffix, 2 cells (B7b-2 Phase A; Task 5)
    ("bnd:preproc_conditional_expression_tail:operand:end@argument_list#suffix-else/arithmetic", "tree"),  # expression-tail / suffix-else, 2 cells (B7b-2 Phase A; Task 5)
    ("occ:signed_integer_list:0.0.1.0.0@declaration_body#sep-after", "oracle:TPL=1,X=1:discrepancy"),  # integer-list / sep-after, 9 cells
    ("occ:interface_procedure_suffix:0.1.0@interface_procedure#adjacent-compl", "oracle:X=0:discrepancy"),  # interface-procedure / adjacent-compl, 6 cells
    ("occ:interface_procedure_suffix:0.1.0@interface_procedure#elif", "oracle:X=0,Y=0:discrepancy"),  # interface-procedure / elif, 6 cells
    ("occ:interface_procedure_suffix:0.1.0@interface_procedure#empty", "oracle:X=0:discrepancy"),  # interface-procedure / empty, 6 cells
    ("occ:interface_procedure_suffix:0.1.0@interface_procedure#nested", "oracle:X=0,Y=0:discrepancy"),  # interface-procedure / nested, 6 cells
    ("occ:interface_procedure_suffix:0.1.0@interface_procedure#sep-only", "oracle:X=0:discrepancy"),  # interface-procedure / sep-only, 6 cells
    ("occ:interface_procedure_suffix:0.1.0@interface_procedure#trail", "oracle:X=1:discrepancy"),  # interface-procedure / trail, 6 cells
    ("occ:_routine_regular_body:0.2.0@preproc_split_procedure#adjacent-compl", "oracle:TPL2=0,X=0:discrepancy"),  # procedure-tail / adjacent-compl, 6 cells
    ("occ:_routine_regular_body:0.2.0@preproc_split_procedure#elif", "oracle:TPL2=0,X=0,Y=0:discrepancy"),  # procedure-tail / elif, 6 cells
    ("occ:_routine_regular_body:0.2.0@preproc_split_procedure#empty", "oracle:TPL2=0,X=0:discrepancy"),  # procedure-tail / empty, 6 cells
    ("occ:_routine_regular_body:0.2.0@preproc_split_procedure#nested", "oracle:TPL2=0,X=0,Y=0:discrepancy"),  # procedure-tail / nested, 6 cells
    ("occ:_routine_regular_body:0.2.0@preproc_split_procedure#sep-only", "oracle:TPL2=0,X=0:discrepancy"),  # procedure-tail / sep-only, 6 cells
    ("occ:_routine_regular_body:0.2.0@preproc_split_procedure#trail", "oracle:TPL2=0,X=1:discrepancy"),  # procedure-tail / trail, 6 cells
    ("seed:value-runs__boundary-complementary-three", "assertion"),  # property-value / seed:value-runs__boundary-complementary-three, 1 cells
    ("seed:value-runs__boundary-visible-caption", "assertion"),  # property-value / seed:value-runs__boundary-visible-caption, 1 cells
    ("bnd:range_expression:right:end@range_expression#chain/arithmetic", "oracle:X=0:pass"),  # range / chain, 2 cells (B7b-2 Phase A: _range_right root)
    ("bnd:range_expression:right:end@case_branch#consecutive/arithmetic", "tree"),  # range / consecutive, 4 cells (B7b-2 Phase B, Task 9: nested shape, spec 6.5 case host)
    ("bnd:range_expression:right:end@case_branch#nested/arithmetic", "tree"),  # range / nested, 4 cells (B7b-2 Phase B, Task 9)
    ("bnd:range_expression:right:end@range_expression#op-only/arithmetic", "fixed"),  # range / op-only, 4 cells (B7b-2 Phase A; X=0 is invalid AL)
    ("bnd:range_expression:right:end@case_branch#suffix/arithmetic", "tree"),  # range / suffix, 8 cells (B7b-2 Phase B, Task 9)
    ("bnd:range_expression:right:end@range_expression#suffix-else/arithmetic", "oracle:X=0:pass"),  # range / suffix-else, 4 cells (B7b-2 Phase A)
    ("occ:call_statement:0.1@if_statement#adjacent-compl", "oracle:X=0:pass"),  # statement-terminator / adjacent-compl, 42 cells
    ("occ:call_statement:0.1@if_statement#elif", "oracle:X=0,Y=0:pass"),  # statement-terminator / elif, 24 cells
    ("occ:call_statement:0.1@if_statement#empty", "oracle:X=0:pass"),  # statement-terminator / empty, 45 cells
    ("occ:call_statement:0.1@case_branch#first-replace", "oracle:X=0:pass"),  # statement-terminator / first-replace, 30 cells
    ("occ:call_statement:0.1@if_statement#nested", "oracle:X=0,Y=0:pass"),  # statement-terminator / nested, 24 cells
    ("occ:call_statement:0.1@if_statement#sep-only", "oracle:X=0:pass"),  # statement-terminator / sep-only, 24 cells
    ("occ:call_statement:0.1@if_statement#trail", "oracle:X=1:pass"),  # statement-terminator / trail, 24 cells
    ("occ:empty_statement:@if_statement#adjacent-compl", "oracle:X=0:pass"),  # statement-terminator / adjacent-compl (old rep), B7b-3 Task 10
    ("occ:empty_statement:@preproc_conditional_statement#empty", "oracle:TPL2=1,X=0:discrepancy"),  # statement-terminator / empty, 18 cells (deferred B7)
    ("occ:empty_statement:@preproc_guarded_statement#adjacent-compl", "refusal:lowering:unsupported-type"),  # statement-terminator / adjacent-compl, 12 cells
    ("occ:preproc_split_if_begin_asymmetric:0.3.0@case_branch#adjacent-compl", "assertion"),  # split-if-begin / adjacent-compl, 18 cells
    ("occ:preproc_split_if_begin_asymmetric:0.3.0@case_branch#elif", "assertion"),  # split-if-begin / elif, 18 cells
    ("occ:preproc_split_if_begin_asymmetric:0.3.0@case_branch#empty", "assertion"),  # split-if-begin / empty, 21 cells
    ("occ:preproc_split_if_begin_asymmetric:0.3.0@case_branch#nested", "assertion"),  # split-if-begin / nested, 18 cells
    ("occ:preproc_split_if_begin_asymmetric:0.3.0@case_branch#sep-only", "assertion"),  # split-if-begin / sep-only, 18 cells
    ("occ:preproc_split_if_begin_asymmetric:0.3.0@case_branch#trail", "assertion"),  # split-if-begin / trail, 18 cells
    ("bnd:ternary_expression:condition:end@ternary_expression#chain/logical", "oracle:X=0:pass"),  # ternary / chain, 4 cells (B7b-2 Phase A: _ternary_condition root)
    ("bnd:ternary_expression:condition:end@ternary_expression#op-only/comparison", "fixed"),  # ternary / op-only, 10 cells (B7b-2 Phase A; X=0 is invalid AL)
    ("bnd:ternary_expression:else_value:end@ternary_expression#suffix/arithmetic", "oracle:X=1:pass"),  # ternary / suffix, 4 cells (B7b-2 Phase A: _ternary_else root)
    ("bnd:ternary_expression:else_value:end@ternary_expression#suffix-else/arithmetic", "oracle:X=0:pass"),  # ternary / suffix-else, 4 cells (B7b-2 Phase A)
    ("bnd:as_expression:left:end@as_expression#consecutive/type-test", "tree"),  # type-test / consecutive, 4 cells (B7b-2 Phase A: `as` tail, item 41 inverted)
    ("bnd:as_expression:left:end@as_expression#nested/type-test", "tree"),  # type-test / nested, 4 cells (B7b-2 Phase A, item 41 inverted)
    ("bnd:as_expression:left:end@as_expression#suffix/type-test", "tree"),  # type-test / suffix, 4 cells (B7b-2 Phase A, item 41 inverted)
    ("bnd:unary_expression:operand:end@case_branch#consecutive/arithmetic", "assertion"),  # unary-operand / consecutive, 4 cells
    ("bnd:unary_expression:operand:end@case_branch#nested/arithmetic", "assertion"),  # unary-operand / nested, 4 cells
    ("bnd:unary_expression:operand:end@case_branch#suffix/arithmetic", "assertion"),  # unary-operand / suffix, 4 cells
]

# B7b-0 (ruling Option A + oracle arm-terminator): the five empty-statement-ownership groups (rep
# occ:_else_begin_block:4.0@preproc_split_if_then_begin_else_shared#*) and the five split-code-block groups (rep
# occ:preproc_split_else_begin_over_endif:0.3.0.0.0@code_block#*) are gone: their cells are CONSISTENT (3 trail cells
# UNCHECKED, representative vector mismatch). The statement-terminator groups' old representatives
# (occ:_statement:0.2.1.0@preproc_conditional_statement#*) are CONSISTENT; the groups remain with if_statement
# representatives, whose discrepancy is the bare-call shape (`then Bar` + `;`: flat call_statement owns the `;`).
# B7b-3 Task 4: call_statement owns no `;` any more, so the seven statement-terminator witnesses (the six
# if_statement ones and case_branch#first-replace, whose group replaces the call and leaves the `;` to the branch)
# now pass in every configuration and are flipped to `pass`.
# B7b-3 Task 10: the oracle's empty-body-terminator rewrite (engine.absorb_arm_terminators) makes the old
# adjacent-compl rep empty_statement@if_statement#adjacent-compl pass (flipped to `pass`). The empty group
# (rep @preproc_conditional_statement#empty, 18 cells) stays SILENT: a `;` after empty group(s) is a bare `;` in a
# split tree where EVERY configuration reads an empty_statement; the fix-round-1 ruling defers it to B7 as a grammar
# item (a decoration-aware `_statement` terminator), and the narrowed orphan-terminator must not mask it, so the
# witness pins the discrepancy. The adjacent-compl group stays SILENT on 12 cells deferred
# to C1 (b7b3-manifest.tsv), represented by preproc_guarded_statement, which spec 6.4 names as a representation host:
# that witness flips to its named refusal, `refusal:<kind>` (every configuration refused with that kind).
# The six split-if-begin groups (case_branch host, SILENT since B7b-3 Task 6) are outside B7b-3's two families: their
# split tree is pinned by representation fixtures (Task 6 ruling) and the oracle refuses the asymmetric host
# (unsupported-type, C1); the witnesses pin the current class-assertion defect.

OVERACCEPT_NO_CORPUS = [
    "occ:signed_integer_list:0.0.1.0.0@declaration_body#holes-lead",   # integer-list / holes-lead, 6 cells
    "occ:signed_integer_list:0.0.1.0.0@declaration_body#holes-mid",    # integer-list / holes-mid, 6 cells
]

# SILENT inputs that no B7a cell generates, pinned the same way ("oracle:<config>:<status>"). Found by the B7b-2
# final review: list spanning across an #else (docs/deferred-work.md item 57, pre-existing and identical on main).
# X=1 is `Foo(1 + 2)`, but the argument group reads `+2` as a comma-less second argument; alc accepts both
# configurations (tools/alc_probe/cases/b7b-2/crossing/list-spanning-else-call.al).
SILENT_INPUTS = [
    ("b7b2-final-review:list-spanning-else-call",
     "codeunit 50100 P\n{\n    procedure Q()\n    begin\n        I := Foo(1\n#if X\n            + 2\n#else\n"
     "            , 3\n#endif\n            );\n    end;\n}\n",
     "oracle:X=1:discrepancy"),
]

TERNARY = "bnd:ternary_expression:else_value:end@ternary_expression#suffix/arithmetic"


@functools.lru_cache(maxsize=None)
def _universe():
    return {e.cell.id: e for e in evidence.universe()}


@pytest.fixture(scope="module")
def assertion_rows():
    rows = {}
    for a in judge.load_assertions():
        rows.setdefault(a.cell_or_class, a)       # first duplicate wins (report.analyse's rule)
    return rows


def _assertion(rows, entry):
    return rows.get(entry.cell.id) or rows.get("/".join(entry.cls))


@pytest.mark.parametrize("cid,finding", SILENT, ids=[c for c, _ in SILENT])
def test_silent_witness(al_parser, assertion_rows, cid, finding):
    entry = _universe()[cid]
    src = entry.cell.source.encode("utf-8")
    root = al_parser.parse(src).root_node
    assert not root.has_error, "a SILENT witness parses clean"
    if finding == "tree":       # B7b-2 Phase A (plan Task 6 Step 3): a fixed witness pins the right tree
        a = _assertion(assertion_rows, entry)
        assert a is not None, "no assertion row: a positive witness asserts its tree"
        assert judge.check_assertion(root, a), "the assertion no longer holds: the fix regressed"
        got = {r.config: r.status for r in oracle_runner.check_input(al_parser, cid, src)}
        assert got and set(got.values()) == {"pass"}, f"oracle says {got}: the fix regressed"
    elif finding == "assertion":
        a = _assertion(assertion_rows, entry)
        assert a is not None, "no assertion row"
        assert not judge.check_assertion(root, a), "the assertion now holds: flip this case"
    elif finding == "fixed":    # B7b-2 Phase A grammar fix, oracle pending (plan Task 5): the tree is right,
        a = _assertion(assertion_rows, entry)          # no configuration is a discrepancy; Task 5/6 flip to `pass`
        assert a is None or judge.check_assertion(root, a), "the assertion no longer holds: the fix regressed"
        got = {r.config: r.status for r in oracle_runner.check_input(al_parser, cid, src)}
        assert got and set(got.values()) <= {"pass", "cannot-validate"}, f"oracle says {got}: the fix regressed"
        assert set(got.values()) != {"pass"}, f"oracle says {got}: every configuration passes, flip to pass"
    elif finding.startswith("refusal:"):    # flipped to a spec 6.4 named refusal: every configuration refused so
        kind = finding[len("refusal:"):]
        recs = oracle_runner.check_input(al_parser, cid, src)
        assert recs and all(r.status == "cannot-validate" and any(i.startswith(kind + ":") for i in r.items)
                            for r in recs), f"oracle says {[(r.config, r.status, r.items) for r in recs]}"
    else:
        _, config, status = finding.split(":")
        got = {r.config: r.status for r in oracle_runner.check_input(al_parser, cid, src)}
        if status == "pass":    # a flipped (fixed) witness: every configuration passes
            assert got and set(got.values()) == {"pass"}, f"oracle says {got}: the fix regressed"
            return
        assert got.get(config) == status, f"oracle now says {got.get(config)} for {config}: flip this case"


@pytest.mark.parametrize("iid,source,finding", SILENT_INPUTS, ids=[i for i, _, _ in SILENT_INPUTS])
def test_silent_input(al_parser, iid, source, finding):
    src = source.encode("utf-8")
    assert not al_parser.parse(src).root_node.has_error, "a SILENT witness parses clean"
    _, config, status = finding.split(":")
    got = {r.config: r.status for r in oracle_runner.check_input(al_parser, iid, src)}
    assert got.get(config) == status, f"oracle now says {got.get(config)} for {config}: flip this case"


@pytest.mark.parametrize("cid", OVERACCEPT_NO_CORPUS)
def test_overaccept_without_corpus_case(al_parser, cid):
    src = _universe()[cid].cell.source.encode("utf-8")
    assert not al_parser.parse(src).root_node.has_error, "the parser now rejects it: flip this case"


def test_anchored_tail_fragment_sees_the_wrong_level(al_parser, assertion_rows):
    """Fix round 1 ruling: a continuation fragment anchors on the host node and field. Until B7b-2 the ternary
    witness's tail sat beside assignment_statement `right:` (the whole ternary) and only the unanchored fragment
    held. Since B7b-2 Phase A (the _ternary_else root, spec 5.2) the tail sits after the ternary's `else_value`:
    the committed anchored fragment holds."""
    root = al_parser.parse(_universe()[TERNARY].cell.source.encode("utf-8")).root_node
    anchored = assertion_rows[TERNARY]
    assert anchored.expect.startswith("(ternary_expression else_value: (_) (preproc_conditional_expression_tail")
    assert judge.check_assertion(root, anchored)


def test_every_matrix_silent_group_has_a_witness():
    """B7b-3 Task 10: the list follows the committed matrix: each SILENT defect group's representative is pinned."""
    from pathlib import Path
    text = (Path(__file__).resolve().parents[3] / "docs/b7-separator-continuation-matrix.md").read_text(encoding="utf-8")
    groups = text.split("## Defect groups and their witnesses", 1)[1].split("\n## ", 1)[0]
    reps = {c.strip(" `") for line in groups.splitlines() if line.startswith("|")
            for cols in [line.split("|")] if len(cols) > 6 and cols[3].strip() == "SILENT" for c in [cols[5]]}
    assert reps and reps <= {c for c, _ in SILENT}
