# B5b: the link family keyed by name (link-syntax leak)

**Status:** revision 4, 2026-10-05. Revision 3 had a third gpt-6.1-sol round: 1 blocker,
3 majors and 1 minor, all verified and adopted (§9, round 3). Revision 2's round: §9, round 2.
**Revision 2 history:** 2026-10-05. Revision 1 was approved in conversation section by section,
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
2. **The two terminator placements get two conditionals, with different arm rules.** This
   mirrors the generic pair (`_property_value_conditional`, whose arms take an optional `;`, and
   `_property_value_conditional_in_if`). B5's single conditional is NOT reused.

   ```javascript
   _link_property_value: $ => choice(
     $.link_value_list,
     alias($._link_whole_conditional, $.preproc_conditional_property_value),
   ),
   // `;` after #endif (the property arm). Arms MAY end in `;`, as the generic rule's arms do:
   // `#if X A = field(B); #else A = field(C) #endif ;` is valid AL. With X defined it is a
   // terminated property plus an empty property, and the compiler's property list accepts a
   // standalone `;` (ObjectParser.cs:7505-7516). It parses clean today through the generic path.
   _link_whole_conditional: $ => keyedValueConditional($, choice(
     seq(field('value', $._link_property_value), optional(';')),
     ';',   // only if §5.1 enables empty values; unfielded
   )),
   ```

   **The `;`-inside-the-arms conditional** (`_link_whole_conditional_in_if`, used only by
   `_property_with_terminator_in_if`) takes no `;` after `#endif`. Its rules:
   - **Arms may be absent, and `#else` is optional**, as in the generic `_in_if` route
     (`grammar.js:1059-1072`). A source can be valid in some configurations only: the repo
     parses every branch and classifies the invalid ones (`invalid-config`, the
     `fixture-classes.tsv` header). Exhaustive conditions without `#else` are also valid AL in
     every configuration: `#if X ...; #elif not X ...; #endif`.
   - **Every present value-bearing arm ends in `;`.** The `;` may be the only content of an arm
     if §5.1 enables empty values; that arm is unfielded.
   - **A present arm may be this conditional again**, nested. A nested conditional counts as
     present only if it itself contains a present arm.
   - **The conditional must contain at least one present arm, recursively.** This is the
     termination witness. It excludes the empty-prefix split, `#if X #endif B = field(A);`,
     without evaluating configurations.

   A grammar sketch (the plan settles the exact form against the generator):

   ```javascript
   _link_in_if_arm: $ => choice(
     seq(field('value', $._link_property_value), ';'),
     ';',   // only if §5.1 enables empty values
     field('value', alias($._link_whole_conditional_in_if, $.preproc_conditional_property_value)),
   ),
   _link_in_if_tail: $ => seq(       // the rest, arms optional
     repeat(seq($.preproc_elif, optional($._link_in_if_arm))),
     optional(seq($.preproc_else, optional($._link_in_if_arm))),
     $.preproc_endif,
   ),
   _link_whole_conditional_in_if: $ => choice(
     seq($.preproc_if, $._link_in_if_arm, $._link_in_if_tail),   // the #if arm is the witness
     seq($.preproc_if,                                           // a later arm is the witness
       repeat(seq($.preproc_elif)),
       choice(
         seq($.preproc_elif, $._link_in_if_arm, $._link_in_if_tail),
         seq($.preproc_else, $._link_in_if_arm, $.preproc_endif),
       )),
   ),
   ```

   **This excludes both G11 splits structurally:**
   - the non-empty unterminated prefix, `#if X A = field(B), #endif B = field(A);`;
   - the empty prefix, `#if X #endif B = field(A);`.

   **The empty prefix is a silent split TODAY** (live parse at `821c914`: two properties,
   `SubPageLink` and `B`). B5b fixes it for the link family. The generic `_in_if` route has the
   same shape, which matters wherever a continuation can look like a property (e.g.
   `Implementation` pairs). That becomes a deferred-work item (§6).

   **A standalone whole value still has two complete readings:** the whole-value wrapper, and a
   list opening with `preproc_conditional_link_values`. Today a declared conflict and GLR decide
   between them (G11), and the fixture pins the wrapper
   (`link_list_opening_conditional_test.txt:336-401`). The keyed rules are new symbols, so the
   conflicts that decide this get declared for them too, with comments naming both readings.

   The empty-value arm (`seq(';')`, or an empty arm in the outside conditional) exists only if
   §5.1 accepts an empty value. It is represented as an arm with no `value` field, never as an
   empty `link_value_list`.

   **What must hold, checked against the generated parser:**
   - all eight G11 fixture cases keep their exact trees;
   - mixed-placement and nested mixed-placement cases parse as ONE property, with correct spans.
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
   - **A signed value is a local rule, NOT the external `NEGATIVE_INTEGER` / `NEGATIVE_DECIMAL`
     tokens.** Those decline before `)` (`src/scanner.c:599`), and they must keep their
     boundaries. The rule:

     ```javascript
     _const_unsigned_numeric: $ => choice($.integer, $.decimal, $.biginteger_literal),
     _const_negative: $ => seq(field('operator', '-'), field('operand', $._const_unsigned_numeric)),
     _const_numeric: $ => choice(
       $._const_unsigned_numeric,
       alias($._const_negative, $.unary_expression),
     ),
     ```

     **Implementation note (Task 3):** the negative sequence must be a named hidden rule
     (`_const_negative`) aliased to `unary_expression`. An alias wrapped around an inline `seq`
     applies to each child separately, not to the sequence, so it does not produce one node.

     `_const_numeric` REPLACES the existing standalone `$.integer` alternative of the `const`
     argument (`grammar.js:1608-1614`); it does not add a second route to `integer`. It goes
     inside the existing `const` argument's `field('value', ...)`, so sign and magnitude
     form ONE value node with `unary_expression`'s existing fields (`grammar.js:5717-5720`), and
     no new public type. Do not field the magnitude alone, alias a signed sequence to `integer`,
     or admit unrestricted `_expression`.
   - **More probes:** `-1.5`, a signed biginteger, a space or a comment between the sign and the
     magnitude, and unary `+`. Unary `+` is added only if accepted.
   - **`tools/check-field-types.py` pins `link_value.value`'s exact type set**
     (`tools/check-field-types.py:77-84`). Each form the probes approve is added to that set
     (`decimal`, `biginteger_literal`, `unary_expression`, as approved), keeping `multiple=True`
     and no anonymous members.
   - **Conflicts.** `qualified_enum_value` admits expression bases, so a numeric prefix may
     overlap it. The generated conflicts touching `_const_numeric` are audited, and no complete
     wrong reading of `const(-1)` may survive.
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
| L3 | a family pair that fell back to an expression (a form item 6 adds) → the equivalent `link_value` | 0 (§2.2) |
| — | the 20,004 family values, the 3 list-internal `SubPageLink` sites, every G11 fixture | **unchanged** |

There is no blanket class for whole-value fixtures: a fixture that does not change is unchanged.
Only measured deltas are classified, each hunk traced.

**L1 and L3 are leaf rewrites, not whole-value predicates.** The census finds each rewrite root
by descending through UNCHANGED conditional envelopes. The envelope's kind, arm fields, ordering,
delimiters and spans must be identical. At each root it compares field names, source spans,
operators, marker keywords and argument structure:
- **L1** requires the old link pair and the new comparison to cover the same tokens;
- **L3** requires a family property whose old comparison and new link pair cover the same tokens,
  and whose `const` ARGUMENT is one of the specifically approved added forms (item 6). It is not
  a marker keyword: `const` already exists. Any other `const` argument fails classification.

**The wrappers differ, and the predicate maps them explicitly:**
- old `property_expression → comparison_expression`;
- new `link_value_list → link_value`.

The left-hand name, the `=` token, the right-hand form (marker kind, spans, ordered arguments)
and any numeric sign and magnitude are normalised before comparing. An unrecognised wrapper or
argument structure is a finding.

**The census interface changes.** `classify(name, old, new)` returns one class per property
(`tools/relation_census.py:354-409`). It becomes an envelope walker that returns a list of
rewrite records `(property site ID, slot path, class)`. The unchanged envelope is compared with
an all-child cursor walk, not `_sexp`, because `_sexp` skips anonymous children (285-305); only
authorised rewrite roots are masked.

One envelope may hold several rewrites, each reported with its own class. Anything else is a
finding. Reparenting (same span, different parent) is caught by the per-corpus full-tree
tree-harness, not by the census, and the spec says so.

**The production gate is exact, over all four corpora:**
- `tree-harness verify` against a fresh per-corpus baseline reports **0 changed files** for each
  of BC.History, DC, BC28.1 and BCApps-29.0;
- `relation_census.py delta --expect-no-rows` reports **0 rows and 0 findings**. The new flag makes
  any classified row exit 1. Today a run with rows and no findings exits 0
  (`tools/relation_census.py:462`).

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
  - Delegate-valid variants of each G11 shape: `field(...)` pairs for report `DataItemLink`,
    `DataItem.Field` pairs for query `DataItemLink`, and `field`/`const`/`filter` pairs for
    TableFilter. The original G11 fixtures stay unchanged, including the two generic `Caption`
    cases. Over-acceptance fixtures are kept separate and labelled.
  - The mixed `;` placement (§3.2 item 2), and a nested mixed placement.
  - The empty-prefix G11 shape (`#if X #endif B = field(A);`), with `X` defined and undefined.
  - The `;`-inside-the-arms route without `#else`:
    - exhaustive (`#if X ...; #elif not X ...; #endif`);
    - independent `X`/`Y`, where `!X & !Y` is classified `invalid-config` with alc evidence;
    - nested;
    - empty arms beside a terminated arm.
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

- **`link_keying_test.txt`.** Every row of §4.1, the delegate-valid G11 variants of §5.1, item 6's
  added forms, and the leak cases (`Visible = Flag = Rec.OtherFlag;`, `Caption = A = B.C;`).
- **The host × property matrix.** Each row is one compiler host and the one family property it
  owns, and each needs alc to accept it. The placements are the columns: flat, `;` after
  `#endif`, `;` in the arms, mixed, list-internal `#if`, a comment between the name and `=`,
  and the whole property inside a body-level `#if` / `#else`.

  | host | property |
  |---|---|
  | page action (`actions` area) | `RunPageLink` |
  | page part | `SubPageLink` |
  | page system part | `SubPageLink` |
  | pageextension `addafter` action | `RunPageLink` |
  | pageextension `addafter` part | `SubPageLink` |
  | pageextension `modify` action | `RunPageLink`, if alc allows it (first-match lookup, B5 Ruling L) |
  | pageextension `modify` part | `SubPageLink`, if alc allows it |
  | report data item | `DataItemLink`, `field(...)` form |
  | reportextension added data item | `DataItemLink`, if alc accepts it |
  | report request-page part / system part / action | `SubPageLink` / `RunPageLink` |
  | xmlport request-page part / system part / action | `SubPageLink` / `RunPageLink` |
  | query data item | `DataItemLink`, `DataItem.Field` form; `DataItemTableFilter` |
  | query column | `ColumnFilter` |
  | query filter | `ColumnFilter` |
  | xmlport table element | `LinkFields` |

  A request page's root owns none of the six names (§2.1). Body-level `#if` is a placement
  applied to these rows, not a host. **Every expanded host × property × placement tuple gets
  its own probe and fixture case.** That splits the combined rows (request-page part, system
  part and action; query data item `DataItemLink` and `DataItemTableFilter`). It also adds
  report-extension and page-extension request-page contexts where the probes establish
  acceptance.

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
  - a dropped property (census);
  - a reparented property (per-corpus tree-harness: the census cannot see it);
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
  - `chartpart` if accepted;
  - the empty-prefix silent split in the generic `_in_if` route (e.g. `Implementation =`,
    then `#if X` / `#endif`, then `A = B;`). It is pre-existing, outside the link family, and
    needs a probe and a production count.

## 7. Risks

| Risk | Mitigation |
|---|---|
| An empty-prefix or empty-arm conditional ends the property early | §3.2 item 2: every inside-route arm is present and terminated, and `#else` is required. The empty-prefix shape is probed and pinned |
| Mixed `;` placement stops parsing | §3.2 item 2: outside-route arms keep an optional `;`, as the generic route does today |
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

**Round 2** (revision 2). The reviewer marked 4 of the 9 findings resolved and 5 partly
resolved, then raised 1 blocker and 4 majors. All were verified before adoption:

1. **The outside conditional forbade arm semicolons (blocker).** Verified: the mixed placement
   parses clean today, and the compiler's property list accepts a standalone `;`
   (`ObjectParser.cs:7505-7516`). Adopted: outside arms take an optional `;`; empty arms are
   represented without a `value` field.
2. **G11 ownership not structurally guaranteed.** Verified: the empty-prefix shape is a silent
   split TODAY (live parse: two properties). Adopted: the inside route requires every arm to be
   present and terminated, plus an `#else`. Conflicts are declared for the keyed symbols, and
   the "structure alone preserves G11" overclaim is gone. The generic route's empty-prefix split
   becomes a deferred item.
3. **Signed `const` needs a local rule.** Verified: the negative-number scanner tokens decline
   before `)`. Adopted: `_const_numeric`, aliased to `unary_expression`.
4. **L3 was not a safe predicate; zero rows not enforced.** Verified: the census exits 0 when
   there are rows and no findings (`tools/relation_census.py:462`). Adopted: leaf-rewrite roots
   through unchanged envelopes, `--expect-no-rows`, and reparenting assigned to tree-harness.
5. **The host matrix had an impossible row.** Adopted: explicit host × property rows, and
   delegate-valid G11 variants.

**Round 3** (revision 3). The reviewer marked round-2 finding 3 resolved and the rest partly
resolved, then raised 1 blocker, 3 majors and 1 minor. All were verified before adoption:

1. **A mandatory `#else` rejected valid AL (blocker).** Verified:
   - `#if X ...; #elif not X ...; #endif` is exhaustive with no `#else`;
   - the generic `_in_if` route allows absent arms and no `#else` (`grammar.js:1059-1072`);
   - the repo accepts configuration-partial sources (`invalid-config`, `fixture-classes.tsv`).

   Adopted: a recursive termination witness (at least one present arm) replaces "every arm plus
   `#else`".
2. **The outside conditional had no `;`-only arm.** Adopted, gated on the empty-value decision.
3. **The numeric additions contradicted the `link_value.value` pin.** Verified at
   `check-field-types.py:77-84`. Adopted: the pin is updated, `_const_numeric` replaces the
   `integer` alternative, and conflicts with `qualified_enum_value` are audited.
4. **L3 tested a marker keyword.** Adopted: the probed `const` argument forms, an explicit
   wrapper mapping, and a census envelope walker returning rewrite records with an all-child
   cursor comparison.
5. **The matrix rows still combined hosts.** Adopted: one tuple per host × property × placement,
   and the contradictory G11 wording is fixed.
