"""SILENT witnesses of the B7a audit (spec 8, Task 10 ruling): one representative cell (the lexicographically first
id) per (family, base placement) SILENT group of docs/b7-separator-continuation-matrix.md.

alc accepts the configurations in question and the parser is clean, but the tree is wrong. Each case asserts the
representative's CURRENT defect, so the grammar change that removes it makes the case fail:
  - "oracle:<config>:<status>": the config oracle reports that discrepancy for that configuration;
  - "assertion": its row in tools/b7_audit/assertions.tsv (the cell row, else its class row; the first row of a
    duplicated key wins, as in report.py) does not hold.
The fix flips the case to require oracle `pass` and a holding assertion. SILENT inputs never go into test/corpus/:
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
    ("bnd:_argument_expression:0:end@argument_list#consecutive/arithmetic", "assertion"),  # arguments / consecutive, 2 cells
    ("bnd:_argument_expression:0:end@argument_list#nested/arithmetic", "assertion"),  # arguments / nested, 2 cells
    ("bnd:additive_expression:left:end@case_branch#consecutive/arithmetic", "assertion"),  # binary-operand / consecutive, 22 cells
    ("bnd:additive_expression:left:end@case_branch#first-only/arithmetic", "assertion"),  # binary-operand / first-only, 16 cells
    ("bnd:additive_expression:left:end@case_branch#nested/arithmetic", "assertion"),  # binary-operand / nested, 22 cells
    ("bnd:additive_expression:left:end@case_branch#suffix/arithmetic", "assertion"),  # binary-operand / suffix, 22 cells
    ("occ:event_declaration:0.5.0@controladdin_body#adjacent-compl", "oracle:X=0:discrepancy"),  # event-declaration / adjacent-compl, 6 cells
    ("occ:event_declaration:0.5.0@controladdin_body#elif", "oracle:X=0,Y=0:discrepancy"),  # event-declaration / elif, 6 cells
    ("occ:event_declaration:0.5.0@controladdin_body#empty", "oracle:X=0:discrepancy"),  # event-declaration / empty, 6 cells
    ("occ:event_declaration:0.5.0@controladdin_body#first-replace", "oracle:X=0:discrepancy"),  # event-declaration / first-replace, 6 cells
    ("occ:event_declaration:0.5.0@controladdin_body#nested", "oracle:X=0,Y=0:discrepancy"),  # event-declaration / nested, 6 cells
    ("occ:event_declaration:0.5.0@controladdin_body#sep-only", "oracle:X=0:discrepancy"),  # event-declaration / sep-only, 6 cells
    ("occ:event_declaration:0.5.0@controladdin_body#trail", "oracle:X=1:discrepancy"),  # event-declaration / trail, 6 cells
    ("bnd:preproc_conditional_expression_tail:operand:end@argument_list#chain/arithmetic", "assertion"),  # expression-tail / chain, 1 cells
    ("bnd:preproc_conditional_expression_tail:operand:end@argument_list#suffix/arithmetic", "assertion"),  # expression-tail / suffix, 2 cells
    ("bnd:preproc_conditional_expression_tail:operand:end@argument_list#suffix-else/arithmetic", "assertion"),  # expression-tail / suffix-else, 2 cells
    ("occ:_preproc_guard_block:0.0.1@preproc_guarded_statement#adjacent-compl", "assertion"),  # guarded-statement / adjacent-compl, 3 cells
    ("occ:_preproc_guard_block:0.0.1@preproc_guarded_statement#elif", "assertion"),  # guarded-statement / elif, 3 cells
    ("occ:_preproc_guard_block:0.0.1@preproc_guarded_statement#nested", "assertion"),  # guarded-statement / nested, 3 cells
    ("occ:_preproc_guard_block:0.0.1@preproc_guarded_statement#sep-only", "assertion"),  # guarded-statement / sep-only, 3 cells
    ("occ:_preproc_guard_block:0.0.1@preproc_guarded_statement#trail", "assertion"),  # guarded-statement / trail, 3 cells
    ("occ:signed_integer_list:0.0.1.0.0@declaration_body#sep-after", "oracle:TPL=1,X=1:discrepancy"),  # integer-list / sep-after, 9 cells
    ("occ:interface_procedure_suffix:0.1.0@interface_procedure#adjacent-compl", "oracle:X=0:discrepancy"),  # interface-procedure / adjacent-compl, 6 cells
    ("occ:interface_procedure_suffix:0.1.0@interface_procedure#elif", "oracle:X=0,Y=0:discrepancy"),  # interface-procedure / elif, 6 cells
    ("occ:interface_procedure_suffix:0.1.0@interface_procedure#empty", "oracle:X=0:discrepancy"),  # interface-procedure / empty, 6 cells
    ("occ:interface_procedure_suffix:0.1.0@interface_procedure#nested", "oracle:X=0,Y=0:discrepancy"),  # interface-procedure / nested, 6 cells
    ("occ:interface_procedure_suffix:0.1.0@interface_procedure#sep-only", "oracle:X=0:discrepancy"),  # interface-procedure / sep-only, 6 cells
    ("occ:interface_procedure_suffix:0.1.0@interface_procedure#trail", "oracle:X=1:discrepancy"),  # interface-procedure / trail, 6 cells
    ("occ:preproc_split_procedure_preamble:0.6.0@declaration_body#adjacent-compl", "assertion"),  # procedure-header / adjacent-compl, 9 cells
    ("occ:preproc_split_procedure_preamble:0.6.0@declaration_body#elif", "assertion"),  # procedure-header / elif, 9 cells
    ("occ:preproc_split_procedure_preamble:0.6.0@declaration_body#nested", "assertion"),  # procedure-header / nested, 9 cells
    ("occ:preproc_split_procedure_preamble:0.6.0@declaration_body#sep-only", "assertion"),  # procedure-header / sep-only, 9 cells
    ("occ:_routine_regular_body:0.2.0@preproc_split_procedure#adjacent-compl", "oracle:TPL2=0,X=0:discrepancy"),  # procedure-tail / adjacent-compl, 12 cells
    ("occ:_routine_regular_body:0.2.0@preproc_split_procedure#elif", "oracle:TPL2=0,X=0,Y=0:discrepancy"),  # procedure-tail / elif, 12 cells
    ("occ:_routine_regular_body:0.2.0@preproc_split_procedure#empty", "oracle:TPL2=0,X=0:discrepancy"),  # procedure-tail / empty, 6 cells
    ("occ:_routine_regular_body:0.2.0@preproc_split_procedure#nested", "oracle:TPL2=0,X=0,Y=0:discrepancy"),  # procedure-tail / nested, 12 cells
    ("occ:_routine_regular_body:0.2.0@preproc_split_procedure#sep-only", "oracle:TPL2=0,X=0:discrepancy"),  # procedure-tail / sep-only, 12 cells
    ("occ:_routine_regular_body:0.2.0@preproc_split_procedure#trail", "oracle:TPL2=0,X=1:discrepancy"),  # procedure-tail / trail, 6 cells
    ("seed:value-runs__boundary-complementary-three", "assertion"),  # property-value / seed:value-runs__boundary-complementary-three, 1 cells
    ("seed:value-runs__boundary-visible-caption", "assertion"),  # property-value / seed:value-runs__boundary-visible-caption, 1 cells
    ("bnd:range_expression:right:end@range_expression#chain/arithmetic", "oracle:X=0:discrepancy"),  # range / chain, 2 cells
    ("bnd:range_expression:right:end@case_branch#consecutive/arithmetic", "assertion"),  # range / consecutive, 4 cells
    ("bnd:range_expression:right:end@case_branch#nested/arithmetic", "assertion"),  # range / nested, 4 cells
    ("bnd:range_expression:right:end@range_expression#op-only/arithmetic", "oracle:X=1:discrepancy"),  # range / op-only, 4 cells
    ("bnd:range_expression:right:end@case_branch#suffix/arithmetic", "assertion"),  # range / suffix, 8 cells
    ("bnd:range_expression:right:end@range_expression#suffix-else/arithmetic", "oracle:X=0:discrepancy"),  # range / suffix-else, 4 cells
    ("occ:_else_begin_block:4.0@preproc_split_if_then_begin_else_shared#adjacent-compl", "assertion"),  # split-code-block / adjacent-compl, 18 cells
    ("occ:_else_begin_block:4.0@preproc_split_if_then_begin_else_shared#elif", "assertion"),  # split-code-block / elif, 18 cells
    ("occ:_else_begin_block:4.0@preproc_split_if_then_begin_else_shared#nested", "assertion"),  # split-code-block / nested, 18 cells
    ("occ:_else_begin_block:4.0@preproc_split_if_then_begin_else_shared#sep-only", "assertion"),  # split-code-block / sep-only, 18 cells
    ("occ:_else_begin_block:4.0@preproc_split_if_then_begin_else_shared#trail", "assertion"),  # split-code-block / trail, 18 cells
    ("occ:preproc_split_if_begin_asymmetric:0.3.0@asserterror_statement#adjacent-compl", "assertion"),  # split-if-begin / adjacent-compl, 84 cells
    ("occ:preproc_split_if_begin_asymmetric:0.3.0@asserterror_statement#elif", "assertion"),  # split-if-begin / elif, 84 cells
    ("occ:preproc_split_if_begin_asymmetric:0.3.0@asserterror_statement#nested", "assertion"),  # split-if-begin / nested, 84 cells
    ("occ:preproc_split_if_begin_asymmetric:0.3.0@asserterror_statement#sep-only", "assertion"),  # split-if-begin / sep-only, 84 cells
    ("occ:preproc_split_if_begin_asymmetric:0.3.0@asserterror_statement#trail", "assertion"),  # split-if-begin / trail, 84 cells
    ("occ:_statement:0.2.1.0@preproc_conditional_statement#adjacent-compl", "oracle:TPL2=1,X=0:discrepancy"),  # statement-terminator / adjacent-compl, 111 cells
    ("occ:_statement:0.2.1.0@preproc_conditional_statement#elif", "oracle:TPL2=1,X=0,Y=0:discrepancy"),  # statement-terminator / elif, 93 cells
    ("occ:call_statement:0.1@if_statement#empty", "oracle:X=0:discrepancy"),  # statement-terminator / empty, 45 cells
    ("occ:call_statement:0.1@case_branch#first-replace", "oracle:X=0:discrepancy"),  # statement-terminator / first-replace, 30 cells
    ("occ:_statement:0.2.1.0@preproc_conditional_statement#nested", "oracle:TPL2=1,X=0,Y=0:discrepancy"),  # statement-terminator / nested, 93 cells
    ("occ:_statement:0.2.1.0@preproc_conditional_statement#sep-only", "oracle:TPL2=1,X=0:discrepancy"),  # statement-terminator / sep-only, 93 cells
    ("occ:_statement:0.2.1.0@preproc_conditional_statement#trail", "oracle:TPL2=1,X=1:discrepancy"),  # statement-terminator / trail, 93 cells
    ("bnd:ternary_expression:condition:end@ternary_expression#chain/logical", "oracle:X=0:discrepancy"),  # ternary / chain, 4 cells
    ("bnd:ternary_expression:condition:end@ternary_expression#op-only/comparison", "oracle:X=1:discrepancy"),  # ternary / op-only, 10 cells
    ("bnd:ternary_expression:else_value:end@ternary_expression#suffix/arithmetic", "oracle:X=1:discrepancy"),  # ternary / suffix, 4 cells
    ("bnd:ternary_expression:else_value:end@ternary_expression#suffix-else/arithmetic", "oracle:X=0:discrepancy"),  # ternary / suffix-else, 4 cells
    ("bnd:as_expression:left:end@as_expression#consecutive/type-test", "oracle:X=0,Y=0:discrepancy"),  # type-test / consecutive, 4 cells
    ("bnd:as_expression:left:end@as_expression#nested/type-test", "oracle:X=0,Y=0:discrepancy"),  # type-test / nested, 4 cells
    ("bnd:as_expression:left:end@as_expression#suffix/type-test", "oracle:X=0:discrepancy"),  # type-test / suffix, 4 cells
    ("bnd:unary_expression:operand:end@case_branch#consecutive/arithmetic", "assertion"),  # unary-operand / consecutive, 4 cells
    ("bnd:unary_expression:operand:end@case_branch#nested/arithmetic", "assertion"),  # unary-operand / nested, 4 cells
    ("bnd:unary_expression:operand:end@case_branch#suffix/arithmetic", "assertion"),  # unary-operand / suffix, 4 cells
]

OVERACCEPT_NO_CORPUS = [
    "occ:signed_integer_list:0.0.1.0.0@declaration_body#holes-lead",   # integer-list / holes-lead, 6 cells
    "occ:signed_integer_list:0.0.1.0.0@declaration_body#holes-mid",    # integer-list / holes-mid, 6 cells
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
    if finding == "assertion":
        a = _assertion(assertion_rows, entry)
        assert a is not None, "no assertion row"
        assert not judge.check_assertion(root, a), "the assertion now holds: flip this case"
    else:
        _, config, status = finding.split(":")
        got = {r.config: r.status for r in oracle_runner.check_input(al_parser, cid, src)}
        assert got.get(config) == status, f"oracle now says {got.get(config)} for {config}: flip this case"


@pytest.mark.parametrize("cid", OVERACCEPT_NO_CORPUS)
def test_overaccept_without_corpus_case(al_parser, cid):
    src = _universe()[cid].cell.source.encode("utf-8")
    assert not al_parser.parse(src).root_node.has_error, "the parser now rejects it: flip this case"


def test_anchored_tail_fragment_sees_the_wrong_level(al_parser, assertion_rows):
    """Fix round 1 ruling: a continuation fragment anchors on the host node and field. The ternary witness's tail
    sits beside assignment_statement `right:` (the whole ternary), not after the ternary's `else_value`: the
    unanchored fragment holds there, the committed anchored one does not."""
    root = al_parser.parse(_universe()[TERNARY].cell.source.encode("utf-8")).root_node
    anchored = assertion_rows[TERNARY]
    assert anchored.expect.startswith("(ternary_expression else_value: (_) (preproc_conditional_expression_tail")
    assert not judge.check_assertion(root, anchored)
    loose = judge.Assertion(TERNARY, "(_ (_) (preproc_conditional_expression_tail (preproc_if) operand: (_) "
                                     "(preproc_endif)))", (), "")
    assert judge.check_assertion(root, loose)
