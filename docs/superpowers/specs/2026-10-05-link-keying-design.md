# B5b: the link family keyed by name (link-syntax leak)

**Status:** approved in conversation on 2026-10-05, section by section. This written spec
awaits review.
**Roadmap row:** B5b (`docs/superpowers/plans/2026-09-28-roadmap-remaining-work.md`).
**Method:** B5's (`docs/superpowers/specs/2026-10-04-table-relation-keying-design.md`). It
reuses B5's tools:
- `tools/alc_facts/property-hosts.tsv`;
- `tools/alc_probe`;
- `tools/relation_census.py`;
- the scanner's single-read keyed dispatch.

**Ships in:** the same major release as B5. Production trees are expected NOT to change (§4.2).

## 1. Problem

```al
RunPageLink = "No." = field("No.");           // link_value_list -- right
Visible = Flag = Rec.OtherFlag;               // link_value_list -- WRONG: a comparison
Enabled = Status = const(Open);               // link_value_list -- WRONG for any non-link name
```

**Every property can take link grammar.** `_property_value` offers `link_value_list` to all of
them (`grammar.js:1177`), and `link_value` carries `prec.dynamic(1)` (`grammar.js:1594-1599`). So
a one-entry `A = B.C` or `A = field(B)` takes the link reading under any property name.

The `prec.dynamic` was added so that single-entry `RunPageLink` / `SubPageLink` /
`DataItemLink` / `ColumnFilter` values stopped becoming comparisons. That made the link
reading win everywhere: a silent wrong tree for hand-written code like
`Visible = Flag = Rec.OtherFlag;`.

## 2. Ground truth

### 2.1 The compiler keys link grammar by name

The source is `tools/alc_facts/property-hosts.tsv`, extracted from alc 18.0.41.62505,
`Microsoft.Dynamics.Nav.CodeAnalysis.dll`, sha256 794a6660….

| name | value kind / delegate | hosts |
|---|---|---|
| `SubPageLink` | TableFilter, `ParseTableFilterPropertyValue` | PagePart, PageChartPart, PageSystemPart |
| `RunPageLink` | TableFilter, `ParseTableFilterPropertyValue` | PageAction |
| `LinkFields` | TableFilter, `ParseTableFilterPropertyValue` | XmlPortTableElement |
| `DataItemTableFilter` | TableFilter, `ParseTableFilterPropertyValue` | QueryDataItem |
| `ColumnFilter` | TableFilter, `ParseTableFilterPropertyValue` | QueryColumn, QueryFilter |
| `DataItemLink` | ReportDataItemLink / QueryDataItemLink | ReportDataItem / QueryDataItem |

No other name maps to these delegates.

The two `DataItemLink` grammars are both lists of `Field = <value>` pairs, and our `link_value`
covers both:
- the report form uses `field(...)`, `const(...)` and `filter(...)`;
- the query form uses `DataItem.Field`.

So one keyed token serves the whole family. Every other property that production writes as a
dotted value or as a call is an expression to the compiler, per B5 §2.1.

This meets the CLAUDE.md keying rule. The compiler parses these values with their own grammar,
and a one-entry list cannot be told apart from a comparison expression in ours.

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

The leak has **0 production sites**. The family's 20,004 values are already right.

## 3. Mechanism

### 3.1 Scanner (`src/scanner.c`)

- Add `LINK_PROPERTY_NAME` (index 18) to `TokenType` and to `externals`, after
  `TABLE_RELATION_PROPERTY_NAME`.
- `read_identifier_word` gains `WORD_LINK_PROPERTY`. It is a whole-word, case-insensitive match
  against `subpagelink`, `runpagelink`, `linkfields`, `dataitemtablefilter`, `columnfilter`
  and `dataitemlink`. The longest is 19 characters, inside the 32-byte buffer.
- Each name is checked against `property-hosts.tsv` (§2.1) and never derived from a suffix.
  `FooLink` and `SubPageLinkX` stay generic.
- The emission order becomes CalcFormula → ML → Namespaces → TableRelation → Link → generic
  `PROPERTY_NAME` → decline. The keyed token is emitted only when `valid_symbols` offers it;
  otherwise the name falls back to the generic token.
- Add the token to all three guards: error recovery, identifier-dispatch entry, and
  property-block entry.

### 3.2 Grammar (`grammar.js`)

1. **`property`** gets a keyed arm. Its value is optional only if the §5.1 probe accepts
   `RunPageLink = ;`.

   ```javascript
   seq(
     field('name', alias($._link_property_name, $.property_name)),
     '=',
     field('value', $._link_property_value),
     ';'
   ),
   ```
2. **`_link_property_value`** is defined with B5's helper:

   ```javascript
   _link_property_value: $ => choice(
     $.link_value_list,
     alias($._link_whole_conditional, $.preproc_conditional_property_value),
   ),
   _link_whole_conditional: $ => keyedValueConditional($,
     seq(field('value', $._link_property_value), optional(';'))),
   ```

   **One derivation per input.** Unlike `table_relation_value`, `link_value_list` cannot start
   with `#if`, because `_link_value_seq`'s `#if`-first arm requires a preceding run or a leading
   comma inside the branch. If generation shows a value-start conflict anyway, record the
   generator's exact message. Then resolve it the B5 way: one derivation per input, and a
   declared conflict only where the reading depends on the token after `#endif`.
3. **`_property_value`** loses `$.link_value_list`.
4. **`_property_with_terminator_in_if`** gains a keyed link arm with the whole conditional,
   following B5. That covers the `;`-inside-the-arms placement.
   **`_property_whole_value_in_if`** gets a keyed link arm only if one of its hosts accepts a
   link-family name. Its hosts are the action area and the dotnet assembly body. `RunPageLink`
   is a PageAction property, not an action-area one, so expect AL0124 and no arm (B5 Ruling M).
   A §5.1 probe decides this.
5. **`link_value` loses `prec.dynamic(1)`.** With keying there is nothing for it to decide: a
   keyed name only ever offers the link reading, and a generic name only ever offers the
   expression reading. Its comment is rewritten to say why the tiebreak is gone.
6. **Conflicts.** Re-check every `conflicts` entry that names `preproc_conditional_link_values`
   (`grammar.js:353-434`, 11 entries) after the change. Delete any entry the generator no
   longer needs, and remove the token from an entry when only that token became unnecessary
   (B5 Task 2's experience). Record the measured STATE_COUNT.
7. **Unchanged:**
   - `link_value_list`;
   - `link_value`'s arms;
   - `_link_value_seq`;
   - `preproc_conditional_link_values`;
   - `_link_value_branch`.

## 4. Node contract and deltas

### 4.1 Contract

```
RunPageLink = "No." = field("No."), Type = const(Item);
  -> (property name: (property_name) value: (link_value_list (link_value field: ... value: ...) ...))
RunPageLink = "No." = field("No.");                      -- one entry: still link_value_list
RunPageLink = #if X ... #else ... #endif [;]
  -> (property name: (property_name) value: (preproc_conditional_property_value
       (preproc_if ...) value: (link_value_list ...) | (preproc_conditional_property_value ...) ...))
<other name> = A = Rec.B;      -> value: (property_expression (comparison_expression ...))
<other name> = A = field(B);   -> value: (property_expression (comparison_expression ... (call_expression ...)))
```

**Field rules:**
- `link_value_list` and `link_value` occur only below a property whose name is one of the six.
- A list-internal `#if` keeps today's shape: `link_value_list` holding
  `preproc_conditional_link_values`.

**Who enforces what:**
- The runtime census enforces the name-dependent rules (§5.5), as B5 does. `check-field-types.py`
  cannot see property names.

### 4.2 Intended deltas

| class | change | production sites |
|---|---|---|
| L1 | a non-family property whose value held `link_value*` → `property_expression` | 0 (§2.2) |
| L2 | a family whole-value `#if`: every arm becomes `link_value_list` (today a one-entry arm goes through generic `_property_value`) | 0; fixtures only |
| — | the 20,004 family values | **unchanged** |

**The production gate is exact:**
- `tree-harness verify` against a fresh baseline must report **0 changed files** in BC.History;
- `relation_census.py delta` over all four corpora must report **0 rows**.

Fixture deltas are counted in the plan's first task and traced hunk by hunk.

### 4.3 Consumers

- **Queries:** no query captures `link_value`. `folds.scm` and `indents.scm` match
  `preproc_conditional_link_values`, which stays.
- **Oracle registry:** `preproc_conditional_link_values` keeps its hosts. Removing it from
  generic values may make a registered host unreachable; the registry census reports that.
- **Traversal:** no node type is added or removed.
- **CHANGELOG `[Unreleased]` / `### Changed`:**
  - link syntax (`link_value_list`) now appears only under the six link properties;
  - a dotted or `field(...)` comparison under any other property is a `property_expression`;
  - production trees are unchanged.

## 5. Verification

### 5.1 Compiler evidence

Cases go under `tools/alc_probe/cases/link-keying/`. Each one is self-contained, declaring the
tables, pages and queries it references, and they are written and run before any grammar
change.

- **Accept:** each name in its real host, from §2.1:
  - `RunPageLink` on a page action;
  - `SubPageLink` on a page part;
  - `LinkFields` on an xmlport table element;
  - `DataItemTableFilter` and `ColumnFilter` on a query data item and a query column;
  - `DataItemLink` in a report data item and in a query data item, the latter using the
    `DataItem.Field` form.

  Also accept:
  - a one-entry list;
  - `filter(...)` and `upperlimit(...)`;
  - lowercase names;
  - whole-value `#if` with both `;` placements;
  - a list-internal `#if`;
  - `Visible = Flag = Rec.OtherFlag;` on a page field.
- **Decide by probe:**
  - `RunPageLink = ;`, which decides whether the value is optional;
  - `RunPageLink` on an action area, which decides the `_property_whole_value_in_if` arm
    (expected AL0124);
  - `Enabled = Status = const(Open)` on a page field. If alc rejects it, the case becomes a
    negative whose tree is pinned as it really comes out. If alc accepts it, it is an L1
    fixture.
- **Reject:**
  - a trailing comma in a link list;
  - a missing `=` in a pair;
  - `const` without parentheses.

### 5.2 Fixtures (`test/corpus/`)

- **`link_keying_test.txt`.** Every row of §4.1, one host case per §2.1 host, and the leak
  cases (`Visible = Flag = Rec.OtherFlag;`, `Caption = A = B.C;`). It also holds regressions,
  each of which must be unchanged:
  - `Implementation = A = B;`;
  - `SourceTableView = where(...)`;
  - `SubPageView = sorting(...) where(...)`;
  - `FooLink = A = field(B);`, which is generic and therefore an expression;
  - the 3 production `SubPageLink` list-internal `#if` sites, verbatim.

  Expected trees are generated from `tree-sitter parse` with field labels, and each is proven
  able to fail by renaming a field to `bogus:`.
- **`link_keying_negative_test.txt`:** the §5.1 rejects.
- **Existing fixtures** are rewritten by hand, each hunk traced to L1 or L2. The B5 `-u` rules
  apply.

### 5.3 Oracle

- **Quick tier:** exit 0. A new record is classified with alc_probe evidence.
- **Full tier over the four corpora:** exit 0, 0 discrepancies.

### 5.4 Scanner-state audit

Run in both directions, as in B4 and B5. Every row offering `PROPERTY_NAME` without
`LINK_PROPERTY_NAME` must be a host where no family name can occur.

### 5.5 Gates

- **`tools/relation_census.py` gains `link-outside`.** The check fails if a `link_value_list`
  or `link_value` sits under a property not in the family.
- **The census `delta` mode gains class L1.** `check` over the four corpora stays clean, apart
  from the 2 known BCApps has-error files, and its `validate-grammar.sh --full` step covers the
  new check.
- **Production deltas:**
  - `delta` over the four corpora against a pre-change library: **0 rows**;
  - `tree-harness verify`: **0 changed files**.
- **The usual suite:**
  - `validate-grammar.sh --full`;
  - has_error sweeps;
  - `qc`;
  - the traversal census and pytest;
  - `npm test`.
- **Incremental test:** `RunPageLink` ↔ `RunPageLinkX` ↔ `Visible`, inserting a one-entry list,
  and wrapping it in `#if`.

### 5.6 Budget

- STATE_COUNT ≤ 17,567 (B5's 17,223 × 1.02). A decrease is expected.
- `tools.perf ab` against the B5 library (`821c914`) over the full DC corpus. B5b changes no DC
  tree, so `ab` can time every file. The confidence interval must contain 1.0, or the slowdown
  must be within the A/B test's resolution.
- Over budget is a stop: report the numbers.

## 6. Docs

- **CHANGELOG:** the §4.3 entry.
- **CLAUDE.md:** keyed families go from four to five, plus a `LINK_PROPERTY_NAME` token-table
  row and the emission order.
- **`.claude/rules/scanner.md`:** the token row, "Eleven tokens", the emission order, and the
  three guards.
- **Roadmap:** a B5b done note (STATE_COUNT, `ab`, the delta: 0 production changes).
- **`docs/deferred-work.md`:** an entry only if a decide-by-probe case leaves something open.

## 7. Risks

| Risk | Mitigation |
|---|---|
| A family host whose state lacks the keyed token: a link value ERRORs, or becomes an expression | §5.4 audit, plus one fixture per §2.1 host. tree-harness requires 0 production changes, so a production host regression fails the gate |
| Removing `prec.dynamic` exposes a different tie inside the keyed arm | The keyed arm offers no expression reading. The generator and the one-entry fixtures show it |
| A family value that relied on the generic whole-value path (`;`-inside-the-arms at a host) loses it | §3.2 item 4, and the host fixtures cover both placements |
| `Enabled = Status = const(Open)`-style input that alc accepts as an expression | It becomes `property_expression(comparison_expression ... call_expression)`. The §5.1 decide-by-probe case pins it either way |

## 8. Not in scope

- **`implementation_value`'s own `prec.dynamic`** (`grammar.js:1867-1884`). It belongs to the
  Implementation family, B4 era, which has a reserved-word set.
- **Separator placement inside link lists** (comma-leading lists, link/property ambiguity at
  separators): roadmap B7.
- **Validating link field names or values:** linter work.
