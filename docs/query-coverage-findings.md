# Grammar defects found by the query-coverage harness

Found while building `tools/query_coverage/` (see its README). **All eight are fixed in
4.0.0.** This file is now the record of what the harness found and what closed it, not a
triage list.

Every entry was confirmed by parsing real AL and inspecting the resulting tree, not by
reading the grammar. Each one was invisible to all three pre-existing gates: the file parsed
with **zero ERROR nodes**, the s-expression tree was stable, and the corpus tests passed.
`tree-sitter parse` emits named nodes only, so a hidden token that is lexed and then dropped
changes no tree hash.

| # | Defect | Fixed by | Verified effect on BC.History |
|---|---|---|---|
| 1 | Dangling `else` binds to the wrong construct | `ae90aea`, completed by `9332d16` + `e4a7440` | census 25 sites / 23 files → **0 / 0**; `case_else_branch` 1,445 → 1,470 |
| 2 | `begin`/`end` straddling two `#if` blocks | `bad36e4` | `call_statement`, which the misparse produced from `end;`, is **0 corpus-wide** — a `corpus\|never-observed` cluster in `baseline.json` |
| 3 | `object_reference_type.object_type` | `8c23096` | part of +29,770 nodes across 5,212 files (six fields, nothing lost) |
| 4 | `area_section.type` | `8c23096` | ” |
| 5 | `action_area_section.type` | `8c23096` | ” |
| 6 | `assignment_statement` / `assignment_expression` `.operator` | `37771f1` | **+243,044** `assignment_operator` across 8,559 files, 0 removed |
| 7 | `xmlport_element.element_type` / `xmlport_attribute.attribute_type` | `8c23096` | part of the +29,770 above |
| 8 | `field()` / `const()` / `upperlimit()` inside `where()` produce no node | `5a39bcf` | **+29,017** across 2,651 files: `field_keyword` 12,844, `const_keyword` 8,925, `where_keyword` 7,208, `upperlimit_keyword` 40 |

## About the counts below

**The per-site counts in the entries below are 500-file sample extrapolations and are
order-of-magnitude only.** Measured against the eventual full-corpus censuses they run about
**3x high**. The `:=` count taken this way — "22,964 `:=` per 500 files", still carried by
the comment at `grammar.js:3594` — implies ~705,000 corpus-wide against a true **243,044**.
The 17,440 quoted below for defect 3 was 16,140 — and counted
`object_reference_type` occurrences rather than the `testpage`/`testrequestpage` split it was
presented as, so it was not a count of that defect at all.

The table above carries the verified figures: full-corpus censuses over all 15,358 files
rather than projections — `tools/tree-harness.sh` node-instance diffs for the node counts, a
dedicated census script for defect 1. **Census before quoting any number from the sections
below.**

## 1. Dangling `else` binds to the wrong construct

**Fixed by `ae90aea`, completed by the terminator restructure `9332d16` + `e4a7440`.**

**9 sites (sample-derived).** The fix's own census, run over all 15,358 files, found **25
sites in 23 files** and left **0**. Plain AL — no preprocessor, no comments.

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

**Fixed by `bad36e4`.**

**4 sites (sample-derived).**

A `begin`/`end` pair that brackets an entire `#if`/`#endif` block plus trailing shared code,
or an asymmetric single-branch wrap, is covered by none of the ~12 `preproc_split_*` rules —
those handle a pair split *across branches of one conditional*. Both keywords fall back to
`identifier` and `end;` reparses as a `call_statement`.

This is the same signature as the `PREPROC_SPLIT_END` bug fixed in 4.0.0, in shapes that fix
did not cover. Sites:
`Warehouse/Structure/WhseIntegrationManagement.Codeunit.al:110-118` and
`Manufacturing/Finance/Dimension/MfgDimensionManagement.Codeunit.al:32-40`.

## 3. `object_reference_type.object_type` — "17,440 occurrences"

**Fixed by `8c23096`.** The 17,440 is doubly wrong: the census figure is 16,140, and it
counted `object_reference_type` occurrences rather than the `testpage`/`testrequestpage`
split described below, so it never was a count of this defect. The verified figure for the
change is +29,770 node instances across 5,212 files for all six fields together.

`grammar.js:1372-1373` use bare `kw('testpage')` and `kw('testrequestpage')`, while the
other eight alternatives in the same `choice()` go through named keyword rules
(`$.page_keyword`, `$.report_keyword`, …). `node-types.json` lists only those eight.

```
TestPage "Cust Card"  ->  child_by_field_name('object_type') == None
Page     "Cust Card"  ->  <Node type=page_keyword>
```

A 2-of-10 inconsistency in one rule. Every `TestPage` / `TestRequestPage` reference silently
drops its type.

## 4. `area_section.type` — 5,138 occurrences (sample-derived)

## 5. `action_area_section.type` — 3,629 occurrences (sample-derived)

**Both fixed by `8c23096`.**

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

**Fixed by `37771f1`: 243,044 `assignment_operator` nodes gained across 8,559 files, none
lost.** Corroborated against the raw text — 241,368 literal `:=` in 8,563 files, the surplus
being the compound operators and the shortfall the `for` statements.

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
matches only the visible `':='` inside `for_statement`. Measured on a file with three
assignments and one `for`, the shipped pattern captured 1 site; `37771f1` added
`(assignment_operator) @operator` alongside it, taking that file to 4 and reaching `+=`,
`-=`, `*=` and `/=` for the first time.

Recovery before the fix: slice the source between `left.end_byte` and `right.start_byte`.
No longer needed — read the `operator` field.

`is_expression` / `as_expression` declare the same field over hidden tokens but lose nothing
— their node *types* already encode the operator.

## 7. `xmlport_element.element_type` / `xmlport_attribute.attribute_type`

**Fixed by `8c23096`.** These two had no `$.identifier` fallback, so the field never
appeared in `node-types.json` at all — the "field absent entirely" shape, as against
defects 4 and 5's "declared but always `None`".

`grammar.js:2431` and `:2466` declare these fields over `choice(kw(...), kw(...))` — all
hidden. Both node types expose only `['body', 'name', 'source']`. Parsing a probe XmlPort
shows the `textelement` / `fieldattribute` keyword text absent from the tree entirely.

## 8. A `field()` reference inside `where()` produces no node

**Fixed by `5a39bcf`, and it was worse than written here.** `where(X = field(N))`,
`where(X = const(N))` and `where(X = upperlimit(N))` produced **byte-for-byte identical
subtrees**, differing only in offsets — three different database queries with nothing in the
tree recording which was written. That is a semantic misread, not a missing keyword.
`filter(…)`, in the same `choice()`, was already correct as `filter_keyword`, which is how
the inconsistency stayed invisible. The construct was duplicated in `where_condition` and
`link_value`, so `DataItemLink`, `RunPageLink`, `SubPageLink` and `ColumnFilter` had it too;
both sites are fixed.

```al
TableRelation = Other.Code where(X = field(N));
```

bottomed out at `where_condition`, whose children were `identifier X`, `=`, `(`,
`identifier N`, `)`. The `field` keyword was a bare `kw()` and was dropped, as was `where`.
There was no node for the reference itself.

At the time, the **field declaration** keyword was deliberately left alone: `field` is also
`field(1; A; Code[10])` and `field(Name; Source)` and appears in `keyword_as_identifier`, so
`field_keyword` was used only by the where/link markers — verified then across all 15,358
files, every `field_keyword` node's parent being `where_condition` or `link_value` and zero
inside `field_declaration` or `page_field`.

**4.0.0 reversed that.** The losslessness work made `field_declaration` and `page_field`
emit `field_keyword` too, so the sentence above now describes only history: re-censused on
the merged 4.0.0 grammar, there are **96,729 lexical `field(` sites and 96,729
`field_keyword` nodes**, exact, in **0 mismatching files**. `field_declaration` (36,145),
`page_field` (47,738) and `preproc_split_field` (1) are all *additional* to that total
rather than components of it, because each now contains a keyword of its own.

That is what removed the harness's `field(` exclusion. Both of its reasons were true when
written and were falsified by a later grammar fix rather than by an error:

1. "a field reference inside a where() clause produces no node" — false as of `5a39bcf`.
2. a field header split across `#if` branches spells `field(` once per branch but yields a
   single `preproc_split_field`, a 1:N mapping no node-type **sum** can express — correct
   about the sum, wrong about the conclusion. `field_keyword` is emitted once per *lexical*
   spelling, including once per branch, so counting the keyword alone sidesteps the
   collapsed node instead of trying to reconcile it.

`field(` is therefore a live anchor in `ANCHORS` as of 4.0.0 with `node_types=("field_keyword",)`,
and `EXCLUDED_ANCHORS` is now empty. The old four-type sum would **double-count** —
it mismatches on 6,371 of 15,358 files. See the note at the anchor's definition in
`tools/query_coverage/anchors.py`.

## The pattern

Six of the eight are the same mistake: **a `field()` wrapping a bare `kw()` or a
`token(choice(...))`**. tree-sitter renders anonymous pattern tokens as hidden `aux_sym_*`
symbols, so the field silently disappears while the bytes are still consumed.

`tools/query_coverage`'s detector 3 finds this class statically — every `field('x', ...)`
in `src/grammar.json` cross-checked against `src/node-types.json`, per owning type — and its
dynamic half catches the subtler case where a `choice()` mixes visible and hidden
alternatives, so the field survives in `node-types.json` but is absent on instances that took
the hidden branch (defects 4 and 5).

The fix shape was the same throughout: route the alternatives through named keyword rules, as
the other eight alternatives in defect 3 already did.

## Reproducing

```bash
python -m tools.query_coverage.qc run --full-corpus --all   # ~6.8 min, all 15,358 files
python -m tools.query_coverage.qc run                       # ~11 s, the 59-file manifest
```

The full-corpus figure was ~31 min until `81ab477`; it is **407 s measured** on the merged
release branch. The four fixes were per-file `Query` recompilation and a per-node constant
rebuild — parsing itself was only 26 s of the original ~31 min.

Findings land in `tools/query_coverage/reports/findings.jsonl` (one per line, stable order)
and `summary.md`. Defects 1 and 2 were sparse — 16 findings in 11 files — so they appeared
only in a `--full-corpus` run, not in the manifest gate. Both now report zero.

`--full-corpus` is a **reporting** pass, not a gate: `cmd_run` sets an empty `Diff()` on that
branch, so its exit 0 means only "it ran". The gating run is the 59-file manifest one.
