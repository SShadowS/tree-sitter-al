# B5b: the link family keyed by name (link-syntax leak)

**Status:** revision 2, 2026-10-05. Revision 1 was approved in conversation section by section,
then reviewed by gpt-6.1-sol. All 9 of its findings were verified against the decompiled
compiler, the grammar and live parses before they were adopted (§9). This revision awaits
review.
**Roadmap row:** B5b (`docs/superpowers/plans/2026-09-28-roadmap-remaining-work.md`).
**Method:** B5's (`docs/superpowers/specs/2026-10-04-table-relation-keying-design.md`). It
reuses B5's tools:
- `tools/alc_facts/property-hosts.tsv`;
- `tools/alc_probe`;
- `tools/relation_census.py`;
- the scanner's single-read keyed dispatch.

**Ships in:** the same major release as B5. Production trees are expected NOT to change (§4.2).
That expectation is a measurement target, proven over all four corpora, not a conclusion.

## 1. Problem

```al
RunPageLink = "No." = field("No.");           // link_value_list -- right
Visible = Flag = Rec.OtherFlag;               // link_value_list -- WRONG: a comparison
Enabled = Status = const(Open);               // link_value_list -- WRONG for any non-link name
RunPageLink = Amount = const(1.5);            // property_expression -- WRONG the other way
```

**Every property can take link grammar.** `_property_value` offers `link_value_list` to every
property (`grammar.js:1177`), and `link_value` carries `prec.dynamic(1)`
(`grammar.js:1594-1599`). So a one-entry `A = B.C` or `A = field(B)` takes the link reading under
any property name.

**The fallback also runs the other way.** A link value whose form `link_value`'s arms lack falls
back silently to a generic `property_expression`. `const(1.5)` and `const(-1)` are measured
examples (§2.3). Both directions are silent wrong trees.

## 2. Ground truth

### 2.1 The compiler keys link grammar by name, with three value grammars

The source is `tools/alc_facts/property-hosts.tsv`, extracted from alc 18.0.41.62505,
`Microsoft.Dynamics.Nav.CodeAnalysis.dll`. Line numbers below are in the decompiled
`ObjectParser.cs` / `LanguageParser.cs`.

| name | hosts | delegate |
|---|---|---|
| `SubPageLink` | PagePart, PageChartPart, PageSystemPart | TableFilter |
| `RunPageLink` | PageAction | TableFilter |
| `LinkFields` | XmlPortTableElement | TableFilter |
| `DataItemTableFilter` | QueryDataItem | TableFilter |
| `ColumnFilter` | QueryColumn, QueryFilter | TableFilter |
| `DataItemLink` | ReportDataItem | ReportDataItemLink |
| `DataItemLink` | QueryDataItem | QueryDataItemLink |

No other name maps to these delegates.

**The three delegates accept different forms:**

| delegate | list | pair right-hand side | empty value |
|---|---|---|---|
| TableFilter (`ParseTableRelationConditionValue`, 11490) | at least one `ParsePropertyExpression`, comma-separated | `field(Name)`, `field(filter(Name))`, `field(upperlimit(Name))`, `field(upperlimit(filter(Name)))`, `const(<identifier, literal or option access>)`, `filter(<filter expression>)` (8435-8492) | not accepted: the first pair is parsed unconditionally |
| ReportDataItemLink (10143) | `ParseSeparatedList` | exactly `field(Name)` (10149-10156) | accepted by the parser: the list loop exits at `;` (`LanguageParser.cs:323-369`) |
| QueryDataItemLink (10057) | `ParseSeparatedList` | `Name` or `DataItem.Name`: a member reference, never a call (10063-10076, 10325-10334) | accepted by the parser (same helper) |

A trailing separator is an error in all three: TableFilter parses another pair, and
`ParseSeparatedList` reports `ERR_ListCannotEndWithSeparator`.

**Our grammar uses one neutral union grammar.** It is `link_value`, with arms for `field(...)`,
`const(...)`, `filter(...)`, `upperlimit(...)` and `DataItem.Field`, under one keyed token. That
is **deliberate over-acceptance**, not compiler equivalence:
- `RunPageLink = A = B.C` gets a clean link tree, though TableFilter rejects it.
- `DataItemLink = A = const(1)` gets a clean link tree, though both DataItemLink grammars reject
  it.

Over-acceptance is allowed by "parse structure, don't validate", because each accepted form has a
truthful structure: a field/value pair. Two things are NOT allowed:
- **missing a valid form**, so that valid AL ERRORs or falls back to an expression;
- **inventing a wrong structure.**

§3.2 item 6 addresses the first.

This meets the CLAUDE.md keying rule. Each delegate is reached only through these names, and a
one-entry list cannot be told apart from a comparison in our grammar.

**Not covered by this section.** "Every other dotted or call value is an expression" is not
claimed. TableView properties (SourceTableView, SubPageView, RunPageView, DataItemTableView),
`Filters`, `CalcFormula` and `TableRelation` have their own compiler paths, and their own grammar
routes (`where_clause`, `sorting_value`, the keyed arms). Those routes do not depend on
`link_value_list` in `_property_value`, and §5.2 pins each of them as a regression.

### 2.2 Production census

**Scope.** BC.History, DC, BC28.1 and BCApps-29.0, at `821c914`, files decoded as
`has_error_sweep` does.

| property | values | today |
|---|---|---|
| `RunPageLink` | 10,269 | all `link_value_list` |
| `SubPageLink` | 5,526 | all `link_value_list`, 3 with a list-internal `#if` |
| `DataItemLink` | 3,289 | all `link_value_list` |
| `DataItemTableFilter` | 444 | all `link_value_list` |
| `ColumnFilter` | 272 | all `link_value_list` |
| `LinkFields` | 204 | all `link_value_list` |
| any other property holding a `link_value*` node | **0** | — |

Other production counts (`corpus-grep`, four corpora):
- `chartpart(`: 0;
- `const(` with a decimal or negative number: 0.

### 2.3 Measured today (live parses at `821c914`, page action host)

| input | today |
|---|---|
| `RunPageLink = A = field(B),;` | clean `link_value_list`: the trailing comma is accepted (`_link_value_run`'s `optional(',')`, `grammar.js:1556-1560`) |
| `RunPageLink = Amount = const(1.5);` | `property_expression`: the link arms have no decimal |
| `RunPageLink = Amount = const(-1);` | `property_expression`: the link arms have no signed number |
| `RunPageLink = Amount = filter((1\|2)&3);` | ERROR: `filter_value` has no parentheses |

`chartpart` has no grammar rule (`_layout_element`, `grammar.js:2493-2519`), though the compiler
dispatches it (`SyntaxFacts.cs:4270-4274`; `ObjectParser.cs:9785-9794`).

## 3. Mechanism

### 3.1 Scanner (`src/scanner.c`)

- Add `LINK_PROPERTY_NAME` (index 18) to `TokenType` and to `externals`, after
  `TABLE_RELATION_PROPERTY_NAME`.
- `read_identifier_word` gains `WORD_LINK_PROPERTY`. It is a whole-word, case-insensitive match
  against the six names, taken from `property-hosts.tsv` and never from a suffix. The longest,
  `dataitemtablefilter`, is 19 characters, inside the 32-byte buffer. `FooLink` and
  `SubPageLinkX` stay generic.
- The emission order becomes CalcFormula → ML → Namespaces → TableRelation → Link → generic
  `PROPERTY_NAME` → decline. The keyed token is emitted only when `valid_symbols` offers it.
- Add the token to all three guards: error recovery, identifier-dispatch entry, and
  property-block entry.

### 3.2 Grammar (`grammar.js`)

1. **`property`** gets a keyed arm. The value is `optional()` if any family delegate accepts an
   empty value, which §5.1 probes per delegate. One shared arm then over-accepts
   `RunPageLink = ;` as structure, and that is a validation matter, not a parse matter (§2.1). If
   every probe rejects, the value is required.

   ```javascript
   seq(
     field('name', alias($._link_property_name, $.property_name)),
     '=',
     optional(field('value', $._link_property_value)),   // per §5.1
     ';'
   ),
   ```
2. **The two terminator placements get two conditionals.** This mirrors the generic
   `_property_value_conditional` / `_property_value_conditional_in_if` pair. B5's single
   optional-`;` conditional must NOT be reused here: for links it revives G11, the documented
   silent split that the `_in_if` comment describes at `grammar.js:1019-1028`. A link run accepts
   a trailing comma (§2.3), so an arm `A = field(B),` could end the property at `#endif` and leave
   `B = field(A);` as a second property.

   ```javascript
   _link_property_value: $ => choice(
     $.link_value_list,
     alias($._link_whole_conditional, $.preproc_conditional_property_value),
   ),
   // `;` after #endif: arms carry no `;`
   _link_whole_conditional: $ => keyedValueConditional($,
     field('value', $._link_property_value)),
   // `;` inside the arms: every non-empty arm ENDS in `;`, or is this conditional again
   _link_whole_conditional_in_if: $ => keyedValueConditional($, choice(
     seq(field('value', $._link_property_value), ';'),
     field('value', alias($._link_whole_conditional_in_if, $.preproc_conditional_property_value)),
   )),
   ```

   The G11 trees must stay exactly as `test/corpus/link_list_opening_conditional_test.txt` pins
   them: a `#if` that opens a list continued after `#endif` is list-internal, and the last four
   cases are whole-value forms. The structure above is what preserves them; a tiebreak or a STOP
   gate is not. Every G11 case is re-run under the keyed name.
3. **`_property_value`** loses `$.link_value_list`.
4. **The `_in_if` hosts.**
   - `_property_with_terminator_in_if` gains a keyed link arm whose value is
     `_link_whole_conditional_in_if`.
   - `_property_whole_value_in_if` gets a keyed link arm only if one of its hosts (action area,
     dotnet assembly body) accepts a family name. `RunPageLink` is a PageAction property, so
     expect AL0124 and no arm (B5 Ruling M). §5.1 decides.
5. **`link_value` loses `prec.dynamic(1)`.**
   - **What it decided:** link reading against comparison reading under a generic name.
   - **Why it can go:** keying removes the expression competitor. The keyed arm, and both keyed
     conditionals' arms, recurse through `_link_property_value`, never `_property_value`.
   - **What still competes:** whole-value against list-opening `#if` (G11). Both readings
     contain the same pairs and received the same increment, so `prec.dynamic` never decided it;
     the structure in item 2 and the existing conflicts do.
   - The comment is rewritten to say exactly this.
6. **Value forms, evidence-driven.** `link_value`'s arms widen where §5.1 proves alc accepts a
   form they lack. Keying removes the generic fallback, so a missing form would turn today's
   silent `property_expression` into an ERROR.
   - **`const(...)`:** decimals, signed numbers, bigintegers, dates, times and datetimes are each
     probed. The compiler's `TryParseIdentifierOrLiteralOrOptionAccessExpression` takes literal
     tokens (10384-10409).
   - **`filter(...)` with parentheses** (8821-8831): probed. If accepted, it is recorded as a
     deferred-work item rather than built in B5b. That is a `filter_value` grammar change shared
     with `where_clause`, it ERRORs today already (§2.3), and it has 0 production sites.
7. **Conflicts.** Re-check every `conflicts` entry naming `preproc_conditional_link_values`,
   `_link_value_branch` or `link_value_list`, which is `grammar.js:353-434` including 375, 390
   and 427-430. Delete an entry the generator no longer needs, or remove just the unnecessary
   token from it. Record the generator's exact messages and the STATE_COUNT.
8. **Unchanged:**
   - `link_value_list`;
   - `_link_value_seq` and `_link_value_run`, including the trailing `optional(',')`, which
     carries a comma before a `#if`;
   - `preproc_conditional_link_values` and `_link_value_branch`;
   - `link_value`'s existing arms, apart from item 6's additions.

## 4. Node contract and deltas

### 4.1 Contract

```
RunPageLink = "No." = field("No."), Type = const(Item);
  -> (property name: (property_name) value: (link_value_list (link_value field: ... value: ...) ...))
RunPageLink = "No." = field("No.");                      -- one entry: link_value_list
RunPageLink = #if X ... #else ... #endif [;]             -- either placement
  -> (property name: (property_name) value: (preproc_conditional_property_value
       (preproc_if ...) value: (link_value_list ...) | (preproc_conditional_property_value ...) ...))
RunPageLink = #if X A = field(B), #endif B = field(A);    -- G11: list-internal, one property
  -> (property ... value: (link_value_list (preproc_conditional_link_values ...) (link_value ...)))
<other name> = A = Rec.B;      -> value: (property_expression (comparison_expression ...))
<other name> = A = field(B);   -> value: (property_expression (comparison_expression ... (call_expression ...)))
```

**Field rules:**
- `link_value_list` and `link_value` occur only below a family property.
- Every non-empty family value is a `link_value_list` or a whole-value
  `preproc_conditional_property_value`, whose arms are recursively the same.
- List-internal `#if`s keep today's shape.

**Who enforces what:** the runtime census enforces the name-dependent rules, in both directions
(§5.5).

### 4.2 Intended deltas

| class | change | production sites |
|---|---|---|
| L1 | a non-family property whose value held `link_value*` → `property_expression`, including inside a whole-value `#if` arm | 0 (§2.2) |
| L3 | a family value that fell back to `property_expression` (a form item 6 adds) → `link_value_list` | 0 (§2.2) |
| — | the 20,004 family values, the 3 list-internal `SubPageLink` sites, every G11 fixture | **unchanged** |

There is no blanket class for whole-value fixtures: a fixture that does not change is unchanged.
Only measured deltas are classified, each hunk traced.

**The production gate is exact, over all four corpora:**
- `tree-harness verify` against a fresh per-corpus baseline reports **0 changed files** for each
  of BC.History, DC, BC28.1 and BCApps-29.0;
- `relation_census.py delta` reports **0 rows and 0 findings**.

### 4.3 Consumers

- **Queries:** none capture `link_value`. `folds.scm` and `indents.scm` match
  `preproc_conditional_link_values`, which stays.
- **Oracle registry:** removing generic link values may make a registered
  `preproc_conditional_link_values` host unreachable; the registry census reports that.
- **Traversal:** no type is added or removed.
- **CHANGELOG `[Unreleased]` / `### Changed`:**
  - link syntax appears only under the six link properties;
  - a dotted or `field(...)` comparison elsewhere is a `property_expression`;
  - link values with decimal or signed `const` (if added) are links;
  - production trees are unchanged.

## 5. Verification

### 5.1 Compiler evidence

Cases go under `tools/alc_probe/cases/link-keying/`. Each is self-contained, declaring every
table, page, query and report it references, and they are written and run before any grammar
change.

- **Accept, per delegate and host:**
  - TableFilter: `RunPageLink` on a page action; `SubPageLink` on a page part and a system part;
    `LinkFields`; `DataItemTableFilter`; `ColumnFilter` on a query column and a query filter.
  - `DataItemLink` on a report data item, with `field(...)`.
  - `DataItemLink` on a query data item, with `DataItem.Field` and with a bare `Field`.
  - One-entry lists.
  - Every TableFilter `field(...)` form from §2.1, plus `const(...)` and `filter(...)`.
  - Lowercase names.
  - Whole-value `#if` with both `;` placements, and nested.
  - Every G11 fixture case, under each delegate kind.
  - `Visible = Flag = Rec.OtherFlag;` on a page field.
- **Decide by probe:**
  - An empty value, for each delegate: `RunPageLink = ;`, `DataItemLink = ;` on a report and on
    a query. §2.1 predicts TableFilter rejects it and both DataItemLink grammars accept it.
  - `const(1.5)`, `const(-1)`, a biginteger, a date, a time and a datetime, in TableFilter
    `const`.
  - `filter((1|2)&3)`.
  - `RunPageLink` on an action area, expected AL0124.
  - `chartpart` with `SubPageLink`. If alc accepts it, it becomes a deferred-work item: a layout
    grammar gap with 0 production sites, outside this row.
  - `Enabled = Status = const(Open)` on a page field: an expression to alc, or rejected?
- **Reject, the cross-delegate negatives:**
  - `RunPageLink = A = B.C;`
  - `DataItemLink = A = const(1);` on a report and on a query
  - a missing `=`
  - `const` without parentheses

  Each is pinned as it really parses. Over-accepted ones (§2.1) are clean link trees, and the
  fixture comment says so.
- **Not a reject case:** the trailing comma. alc rejects `A = field(B),;`, but the grammar keeps
  its trailing comma (item 8), so it parses clean. It is recorded as a deferred item for B7
  (separator placement), with the probe as evidence.

### 5.2 Fixtures (`test/corpus/`)

- **`link_keying_test.txt`.** Every row of §4.1, every G11 case under a keyed name, item 6's
  added forms, and the leak cases (`Visible = Flag = Rec.OtherFlag;`, `Caption = A = B.C;`).
- **The host × placement matrix.** Each row is one host, with alc accepting each case:

  | host | flat | `;` after `#endif` | `;` in the arms | list-internal `#if` | comment between name and `=` |
  |---|---|---|---|---|---|
  | page action | ✓ | ✓ | ✓ | ✓ | ✓ |
  | page part, page system part | ✓ | ✓ | ✓ | ✓ | ✓ |
  | pageextension `addafter` part/action | ✓ | ✓ | ✓ | ✓ | ✓ |
  | pageextension `modify` part/action, if alc allows the property there (first-match lookup, B5 Ruling L) | ✓ | ✓ | ✓ | ✓ | ✓ |
  | report data item, request page | ✓ | ✓ | ✓ | ✓ | ✓ |
  | query data item, column, filter | ✓ | ✓ | ✓ | ✓ | ✓ |
  | xmlport table element | ✓ | ✓ | ✓ | ✓ | ✓ |
  | a whole family property inside a body-level `#if` / `#else` | ✓ | ✓ | ✓ | ✓ | ✓ |

- **Regressions,** each unchanged:
  - `SourceTableView`, `SubPageView`, `RunPageView` and `DataItemTableView` with `where(...)`
    and `sorting(...)`;
  - `Filters`;
  - `CalcFormula` with `where(...)`;
  - `TableRelation` with `where(...)`;
  - `Implementation = A = B;`;
  - `FooLink = A = field(B);`, which is generic and therefore an expression;
  - the 3 production list-internal `SubPageLink` sites and a comment-bearing production
    `DataItemLink`, verbatim, with parents, fields and spans.
- **`link_keying_negative_test.txt`:** the §5.1 rejects, as they really parse.
- **Mechanics:** expected trees come from `tree-sitter parse` with field labels, each proven
  able to fail. Existing fixtures are rewritten by hand, each hunk traced to L1 or L3. The B5
  `-u` rules apply.

### 5.3 Oracle

- Quick tier: exit 0.
- Full tier over the four corpora: exit 0, 0 discrepancies.

### 5.4 Scanner-state audit

Run in both directions, as in B4 and B5. Every row offering `PROPERTY_NAME` without
`LINK_PROPERTY_NAME` must be a host where no family name can occur, with a debug parse as
evidence. §5.2's matrix is the context-coverage side; shared scanner rows are not proof.

### 5.5 Gates

- **`tools/relation_census.py` gains two link checks**, mirroring B5's relation pair:

  | check | what it requires |
  |---|---|
  | `link-shape` | every non-empty family value is `link_value_list` or a whole-value conditional whose arms are recursively the same; a list-internal conditional stays inside `link_value_list` |
  | `link-outside` | no `link_value_list`, `link_value` or `preproc_conditional_link_values` sits under a non-family property |

- **The census `delta` mode gains L1 and L3.** L1 is compared recursively through whole-value
  arms.
- **Mutation proofs:**
  - a family name forced onto the generic path, by disabling the keyed token;
  - `link_value_list` restored to `_property_value`;
  - a dropped or reparented property;
  - a whole-value conditional misclassified as list-internal, and the reverse.
- **Production deltas (§4.2), over all four corpora:**
  - `tree-harness verify` with fresh per-corpus baselines: 0 changed files for each corpus;
  - census `delta`: 0 rows, 0 findings.
- **The usual suite:**
  - `validate-grammar.sh --full`, whose census step covers the new checks;
  - has_error sweeps;
  - `qc`;
  - the traversal census and pytest;
  - `npm test`.
- **Incremental test:**
  - `RunPageLink` ↔ `RunPageLinkX` ↔ `Visible`;
  - `DataItemLink` ↔ `dataitemlink`;
  - inserting a one-entry list;
  - wrapping it in `#if`;
  - deleting the trailing pair after a G11 `#endif`.

### 5.6 Budget

- STATE_COUNT ≤ 17,567 (B5's 17,223 × 1.02). The second conditional costs states, and removing
  link grammar from generic values saves them.
- `tools.perf ab` against the B5 library (`821c914`) over the full DC corpus. B5b changes no DC
  tree, so every file is timed. The confidence interval must contain 1.0, or the slowdown must be
  within the A/B test's resolution.
- Over budget is a stop: report the numbers and `--report-states-for-rule`.

## 6. Docs

- **CHANGELOG:** the §4.3 entry.
- **CLAUDE.md:** keyed families go from four to five, plus a `LINK_PROPERTY_NAME` token-table row
  and the emission order. The keyed-properties section gains one sentence on deliberate
  over-acceptance across the three delegates.
- **`.claude/rules/scanner.md`:** the token row, "Eleven tokens", the emission order, and the
  three guards.
- **Roadmap:** a B5b done note.
- **`docs/deferred-work.md`:** new items for whatever §5.1 leaves open:
  - the trailing comma (B7);
  - `filter((...))` if accepted;
  - `chartpart` if accepted.

## 7. Risks

| Risk | Mitigation |
|---|---|
| G11's silent split returns through the `;`-inside-the-arms conditional | §3.2 item 2: required arm `;`, structurally, as the generic `_in_if` conditional does. Every G11 case is re-run under a keyed name |
| A valid link form missing from `link_value` turns a fallback into an ERROR | §3.2 item 6 and §5.1's value-form probes. Production: 0 sites (§2.2), confirmed by the 0-delta gate |
| Empty-value decision taken from one delegate | §5.1 probes all three delegates |
| A family host whose state lacks the keyed token | §5.4 audit plus §5.2's host × placement matrix. Per-corpus tree-harness requires 0 production changes |
| Removing `prec.dynamic` changes a G11 or whole-value tree | §3.2 item 5: it never decided those. The G11 fixtures and the 0-delta gate catch any change |
| A family value silently becoming a comparison | The census `link-shape` check, and its mutation |

## 8. Not in scope

- **`implementation_value`'s own `prec.dynamic`** (`grammar.js:1867-1884`). That is the
  Implementation family, which has a reserved-word set.
- **Separator placement in link lists**, the trailing comma included: roadmap B7.
- **`filter_value` parentheses and `chartpart`:** deferred-work items if §5.1 shows alc accepts
  them.
- **Validating which delegate a value's forms belong to:** deliberate over-acceptance (§2.1),
  linter work.

## 9. Review record

A gpt-6.1-sol review of revision 1 raised 2 blockers and 7 majors. Each one was verified
against the source before it was adopted:

1. **§2.1 conflated three grammars.** Verified: ReportDataItemLink is `field(Name)` only
   (10149-10156); Query is a member reference (10063-10076); TableFilter is
   `field`/`const`/`filter`, with `upperlimit` nested (8435-8492). Adopted as the form matrix,
   with over-acceptance stated as such.
2. **Empty value decided from one probe (blocker).** Verified: `ParseSeparatedList` exits at `;`
   with an empty list (`LanguageParser.cs:323-369`), while TableFilter parses a pair
   unconditionally (11490-11514). Adopted as probes per delegate (§3.2 item 1, §5.1).
3. **G11 revived by an optional-`;` `_in_if` conditional (blocker).** Verified against the
   `grammar.js:1019-1028` comment and the trailing-comma acceptance measured in §2.3. Adopted as
   two conditionals, with a required arm `;` (§3.2 item 2). Also checked: B4's and B5's keyed
   conditionals do NOT split silently. The list-continued `Namespaces` and ML forms ERROR
   visibly (their list-internal splits belong to B7), and the `TableRelation` case parses
   correctly.
4. **"Reject trailing comma" contradicted the unchanged grammar.** Verified by a live parse
   (§2.3). Adopted: it is not a reject case, and it is deferred to B7.
5. **Missing `const` and `filter` forms.** Verified: `const(1.5)` and `const(-1)` fall back to
   `property_expression` today, and `filter((…))` ERRORs. Adopted as §3.2 item 6 and the value
   probes. Production count: 0.
6. **Conflict audit missed `_link_value_branch`.** Verified at `grammar.js:375`, 390 and
   427-430. Adopted (§3.2 item 7). The `prec.dynamic` rationale is restated (item 5).
7. **Host matrix incomplete; `chartpart` missing.** Verified: `_layout_element` has no chartpart,
   and its production count is 0. Adopted: the host × placement matrix, and a decide-by-probe
   `chartpart` case.
8. **The census checked one direction only.** Adopted: `link-shape` and its mutations.
9. **The exact-zero gate covered BC.History only, and the L2 class was blanket.** Adopted:
   per-corpus tree-harness over all four corpora, L2 dropped, measured classes only, and the
   wider regression list.
