# Grammar defects found by the query-coverage harness

Found while building `tools/query_coverage/` (see its README). **None are fixed** — that
work was deliberately out of scope, and this file is the triage list.

Every entry was confirmed by parsing real AL and inspecting the resulting tree, not by
reading the grammar. Each one is invisible to all three pre-existing gates: the file parses
with **zero ERROR nodes**, the s-expression tree is stable, and the corpus tests pass.
`tree-sitter parse` emits named nodes only, so a hidden token that is lexed and then dropped
changes no tree hash.

Counts are occurrences across the 15,358-file BC.History corpus unless stated otherwise.

## 1. Dangling `else` binds to the wrong construct

**9 sites. Plain AL — no preprocessor, no comments.**

```al
case X of
  1:
    if X = 0 then
      X := 1
    else
      X := 2;
  else
    X := 3;
end;
```

The inner `if`'s `else` is taken by `case_else_branch`. The resulting `if_statement` has
children `[if_keyword, comparison_expression, then_keyword, assignment_statement]` — no
`else` at all. `case_else_branch` absorbs `X := 2`, the genuine case-`else` is demoted to a
bare `identifier` sitting loose in the tree, and `X := 3` becomes a second statement in the
same branch. `has_error` is False throughout.

**Why it matters:** `X := 2` should run when `X <> 0`. Any consumer reading this tree gets
the control flow wrong — a linter, a formatter, or a refactoring tool would all act on a
misreading. Example site:
`BaseApp/Source/Base Application/Bank/Reconciliation/MatchBankPayments.Codeunit.al:1184`.

Detected by the reserved-keyword detector, via the stray `identifier` whose text is `else`.

## 2. `begin`/`end` straddling two `#if` blocks

**4 sites.**

A `begin`/`end` pair that brackets an entire `#if`/`#endif` block plus trailing shared code,
or an asymmetric single-branch wrap, is covered by none of the ~12 `preproc_split_*` rules —
those handle a pair split *across branches of one conditional*. Both keywords fall back to
`identifier` and `end;` reparses as a `call_statement`.

This is the same signature as the `PREPROC_SPLIT_END` bug fixed in 4.0.0, in shapes that fix
did not cover. Sites:
`Warehouse/Structure/WhseIntegrationManagement.Codeunit.al:110-118` and
`Manufacturing/Finance/Dimension/MfgDimensionManagement.Codeunit.al:32-40`.

## 3. `object_reference_type.object_type` — 17,440 occurrences

`grammar.js:1372-1373` use bare `kw('testpage')` and `kw('testrequestpage')`, while the
other eight alternatives in the same `choice()` go through named keyword rules
(`$.page_keyword`, `$.report_keyword`, …). `node-types.json` lists only those eight.

```
TestPage "Cust Card"  ->  child_by_field_name('object_type') == None
Page     "Cust Card"  ->  <Node type=page_keyword>
```

A 2-of-10 inconsistency in one rule. Every `TestPage` / `TestRequestPage` reference silently
drops its type.

## 4. `area_section.type` — 5,138 occurrences

## 5. `action_area_section.type` — 3,629 occurrences

`grammar.js:1609` declares
`field('type', choice(kw('content'), kw('factboxes'), kw('processing'), kw('rolecenter'), kw('prompting'), kw('prompt'), $.identifier))`.
Every `kw()` branch is hidden, so the field is `None` on real pages:

```
area(content)     ->  type field: None
area(factboxes)   ->  type field: None
```

A consumer cannot tell a content area from a factboxes area. Worse than a plain omission:
`node-types.json` **claims** `area_section` has a `type` field of type `['identifier']`,
because the rare `$.identifier` fallback keeps the declaration alive. The declaration is
misleading rather than merely incomplete. `action_area_section` has the identical shape.

## 6. `assignment_statement.operator` / `assignment_expression.operator`

`grammar.js:3436` and `:3442` declare `field('operator', $._assignment_operator)`, where
`_assignment_operator` is `token(choice(':=', '+=', '-=', '*=', '/='))` — a hidden token, so
the field is dropped.

```
'i := 1;'  ->  (assignment_statement left: (identifier) right: (integer))
'i += 2;'  ->  (assignment_statement left: (identifier) right: (integer))
   IDENTICAL
```

All five operators collapse into one indistinguishable node, and the bytes belong to no node
so there is no text fallback. `i += 2` means `i := i + 2`, so dataflow analysis is silently
wrong. `queries/highlights.scm:155` (`":=" @operator`) can never match an assignment — it
matches only the visible `':='` inside `for_statement`.

Recovery until fixed: slice the source between `left.end_byte` and `right.start_byte`.

`is_expression` / `as_expression` declare the same field over hidden tokens but lose nothing
— their node *types* already encode the operator.

## 7. `xmlport_element.element_type` / `xmlport_attribute.attribute_type`

`grammar.js:2431` and `:2466` declare these fields over `choice(kw(...), kw(...))` — all
hidden. Both node types expose only `['body', 'name', 'source']`. Parsing a probe XmlPort
shows the `textelement` / `fieldattribute` keyword text absent from the tree entirely.

## 8. A `field()` reference inside `where()` produces no node

```al
TableRelation = Other.Code where(X = field(N));
```

bottoms out at `where_condition`, whose children are `identifier X`, `=`, `(`,
`identifier N`, `)`. The `field` keyword is a bare `kw()` and is dropped, as is `where`.
There is no node for the reference itself.

This is why the harness's `field(` anchor is excluded from detector 5 — one
`field_declaration` plus one where-clause reference counts 2 lexically and 1 structurally,
and no node-type sum reconciles that.

## The pattern

Six of the eight are the same mistake: **a `field()` wrapping a bare `kw()` or a
`token(choice(...))`**. tree-sitter renders anonymous pattern tokens as hidden `aux_sym_*`
symbols, so the field silently disappears while the bytes are still consumed.

`tools/query_coverage`'s detector 3 finds this class statically — every `field('x', ...)`
in `src/grammar.json` cross-checked against `src/node-types.json`, per owning type — and its
dynamic half catches the subtler case where a `choice()` mixes visible and hidden
alternatives, so the field survives in `node-types.json` but is absent on instances that took
the hidden branch (defects 4 and 5).

The fix shape is the same throughout: route the alternatives through named keyword rules, as
the other eight alternatives in defect 3 already do.

## Reproducing

```bash
python -m tools.query_coverage.qc run --full-corpus --all   # ~31 min, all 15,358 files
python -m tools.query_coverage.qc run                       # ~11 s, the 59-file manifest
```

Findings land in `tools/query_coverage/reports/findings.jsonl` (one per line, stable order)
and `summary.md`. Defects 1 and 2 are sparse — 16 findings in 11 files — so they appear only
in a `--full-corpus` run, not in the manifest gate.
