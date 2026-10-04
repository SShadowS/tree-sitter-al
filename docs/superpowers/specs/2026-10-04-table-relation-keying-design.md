# B5: `TableRelation` keyed by name; dotted values are expressions (G10)

**Status:** approved in conversation on 2026-10-04, section by section; this written spec
awaits review.
**Roadmap row:** B5 (`docs/superpowers/plans/2026-09-28-roadmap-remaining-work.md`).
**Resolves:** deferred-work items 13 (G10) and 15.
**Deviates from roadmap decision 2.** Decision 2 asked for a neutral reference node and "no
broad name-keying". The compiler's own table (§2.1) shows that exactly one property,
`TableRelation`, has relation grammar, so this spec keys that one name, the same way B4 keyed
the ML names. No new neutral node type is added. This direction was chosen in conversation on
2026-10-04, over decision 2 as written and over a hybrid of the two.
**Ships in:** the next major. It changes trees: 36,118 bare-name `TableRelation` values and
14,011 dotted values of other properties change shape (§4.2).

## 1. Problem

```al
TableRelation = Customer;                  // today: value: (identifier)                       -- not a relation
TableRelation = Customer."No.";            // today: (table_relation_value ... table: ...)     -- right
AutoFormatExpression = Rec."Currency Code"; // today: (table_relation_value ... table: (identifier 'Rec')) WRONG
Visible = Rec.A
#if X
 and B
#endif
;                                          // today: table_relation_value with an ERROR arm    WRONG (G10)
```

`_property_value` offers `table_relation_value` to every property. A dotted name is a
complete `simple_table_relation`, so every dotted value of every property becomes a
"relation" with `Rec` fielded `table:`. When an expression continues past a `#if`, the
relation reading still wins, and its arms cannot hold `and B`: that is G10.

The same defect works the other way inside `TableRelation`. A bare `TableRelation = Customer;`
gets the generic `identifier` leaf, not a relation. So a consumer that queries
`(simple_table_relation table: (_) @t)` finds 25,714 of 61,832 production relations, 42%.

## 2. Ground truth

### 2.1 The compiler keys relation grammar by one name

The source is alc 18.0.41.62505, `Microsoft.Dynamics.Nav.CodeAnalysis.dll` (the net10.0 build
the `al` tool loads), decompiled with ilspycmd 11.0.
`PropertyNameToSyntaxDefinition.GetPropertyValueDefinition(name)` maps names to value grammars:

| property | compiler value grammar |
|---|---|
| `TableRelation` | `TableRelationPropertyValueSyntaxDefinition`, the only name that maps to it |
| `ValidateTableRelation`, `TestTableRelation` | `BooleanPropertyValueSyntaxDefinition` |
| `AutoFormatExpression`, `CaptionClass`, `DataCaptionExpression` | `TextExpressionPropertyValueSyntaxDefinition` |
| `Visible`, `ShowMandatory`, `HideValue`, `QuickEntry` | `ClientSideBooleanExpressionPropertyValueSyntaxDefinition` |
| `StyleExpr` | `StyleExpressionPropertyValueSyntaxDefinition` |
| `IndentationColumn` | `IntegerExpressionPropertyValueSyntaxDefinition` |
| `Enabled`, `Editable` | `BooleanPropertyValueSyntaxDefinition` (accepts `Rec."Can Try"` in production) |

The lookup is case-insensitive, as B4 established for the same table (`ObjectParser` keys its
`PropertyTypeInfo` tables by the upper-cased name).

This meets the keying rule in CLAUDE.md. The compiler parses `TableRelation`'s value with
its own grammar, and that grammar cannot be told apart from an expression in ours:
`Customer."No."` is both a relation and a member access.

### 2.2 Production census

The census covers BC.History, DC, BC28.1 and BCApps-29.0. It was run on 2026-10-04 at
`6b15b9b`, over every `property` node.

**`TableRelation`** (61,832 values):

| today's value node | sites |
|---|---|
| `quoted_identifier` (bare) | 28,604 |
| `identifier` (bare) | 7,514 |
| `table_relation_value` | 25,712: `where` 13,680, plain dotted 7,093, `if`/`else` 4,939 |
| `table_relation_value` with a `#if` inside (an `if`/`else` chain split by `#if`, DC) | 2 |
| `preproc_conditional_property_value` (whole-value `#if`) | 0 |

**Every other property whose value is `table_relation_value`:** 14,011, all plain dotted
names. No `where`, `if` or `#if` occurs outside `TableRelation`.

| property | sites |
|---|---|
| `AutoFormatExpression` | 13,100 |
| `Enabled` | 232 |
| `StyleExpr` | 215 |
| `DataCaptionExpression` | 124 |
| `Visible` | 117 |
| `IndentationColumn` | 116 |
| `Editable` | 64 |
| `ShowMandatory` | 43 |

**Whole-value `#if` today.** `TableRelation = #if X Customer where(...) #else Vendor #endif`
parses as `preproc_conditional_property_value`, with one `table_relation_value` arm and one
bare `identifier` arm: two shapes in one value. Both `;` placements parse clean.

## 3. Mechanism

### 3.1 Scanner (`src/scanner.c`)

- Add `TABLE_RELATION_PROPERTY_NAME` to `TokenType` and to `externals` in `grammar.js`, after
  `NAMESPACES_PROPERTY_NAME`.
- `read_identifier_word` gains `WORD_TABLE_RELATION`, a whole-word, case-insensitive match
  on `tablerelation`. That is 13 characters, inside the 32-byte buffer. `ValidateTableRelation`
  and `TestTableRelation` are other words and stay `WORD_OTHER`.
- Emission order in the property block: CalcFormula → ML → Namespaces → TableRelation →
  generic `PROPERTY_NAME` → decline. Each keyed token is emitted only if `valid_symbols`
  offers it. Otherwise the name falls back to `PROPERTY_NAME`, as the other three do.
- Add the token to the error-recovery guard, the all-valid check, as B4 did for its two.

### 3.2 Grammar (`grammar.js`)

1. **`property`** gets a fourth keyed arm:
   ```javascript
   seq(
     field('name', alias($._table_relation_property_name, $.property_name)),
     '=',
     optional(field('value', $._table_relation_property_value)),
     ';'
   ),
   ```
2. **`_table_relation_property_value`** is a choice of two shapes:
   - `table_relation_value`;
   - a whole-value conditional, aliased to `preproc_conditional_property_value`, built with the
     B4 helper `keyedValueConditional`. Each arm is
     `seq(field('value', $.table_relation_value), optional(';'))`. That is the B4 pattern: one
     conditional per family serves both `;` placements.
3. **`_property_value`** loses `$.table_relation_value`. Nothing else in the generic list
   changes.
4. **`_property_with_terminator_in_if` and `_property_whole_value_in_if`** lose the generic
   relation form (`alias($._table_relation_split_value, $.table_relation_value)`), and gain a
   keyed arm, as B4 did:
   - **`_property_with_terminator_in_if`:** the keyed conditional, plus the relation
     continued into a `#if` whose arms carry the `;`. That continued form is
     `_table_relation_split_value`, now under the keyed name only.
   - **`_property_whole_value_in_if`:** the keyed conditional only.
5. **`simple_table_relation`, `table_relation_value`, `preproc_conditional_table_relation`,
   `if_table_relation` and `else_table_relation_fragment`** are unchanged. Under the keyed arm
   a bare `Customer` can only be a relation, so it parses as
   `simple_table_relation table: (identifier)` with no new rule.
6. **Conflicts.** The `conflicts` entries that list `preproc_conditional_table_relation`
   beside `_property_value_conditional` or `_property_value_conditional_in_if` (`grammar.js`,
   the block around line 356-406) exist because generic values offered both readings.
   Re-check each after the change: an entry the generator no longer needs is deleted, with the
   measured STATE_COUNT in the commit.

### 3.3 G10 by construction

Without a relation reading at a generic property, `Visible = Rec.A #if X and B #endif ;`
must take the expression path. That path has `preproc_conditional_expression_tail` for
exactly this shape (G5). Item 13 records that why that reading lost was never traced. **The
first implementation task tests this hypothesis before anything else.** If the expression path
still ERRORs once the relation reading is gone, that is fixed inside B5, as a separate task
with its own fixture. Keeping the relation reading is not a fallback.

## 4. Node contract and deltas

### 4.1 Contract

```
TableRelation = <value>;  -> (property name: (property_name) value: (table_relation_value ...))
TableRelation = #if ... #endif [;]
                          -> (property name: (property_name)
                               value: (preproc_conditional_property_value
                                        (preproc_if ...) value: (table_relation_value ...) ...
                                        (preproc_endif ...)))
TableRelation = ;         -> (property name: (property_name))
<other name> = A.B;       -> (property name: (property_name)
                               value: (property_expression (member_expression ...)))
```

**Field rules:**
- `property.name` is `property_name` in every arm.
- A `simple_table_relation`, and so a `table:` field, occurs only below a property named
  `TableRelation`. A corpus census checks this (§5.5).
- Every arm `value:` of a `TableRelation` whole-value `#if` is a `table_relation_value`. Both
  `;` placements give the same tree.
- A split inside a relation is unchanged: `table_relation_value` holding
  `preproc_conditional_table_relation`, with arms `table_relation_expression` or
  `else_table_relation_fragment`.

**`tools/check-field-types.py`** gains invariants for:
- the keyed property value: `table_relation_value | preproc_conditional_property_value`;
- the `value` field of `preproc_conditional_property_value`, which keeps `table_relation_value`
  as a legal arm type.

`simple_table_relation.table` keeps its existing entry.

### 4.2 Intended production deltas (four corpora)

| class | before | after | sites |
|---|---|---|---|
| D1 | `TableRelation` value `identifier` / `quoted_identifier` | `table_relation_value(table_relation_expression(simple_table_relation table: (same leaf)))` | 36,118 |
| D2 | other property value `table_relation_value(... simple_table_relation ...)` | `property_expression(member_expression ...)` (or the expression the dotted value really is, e.g. a subscript base) | 14,011 |
| — | `TableRelation` values that are already `table_relation_value` | unchanged | 25,714 |

No other tree may change. `tree-harness verify` against a fresh baseline must account for
every changed file as D1 or D2. Any other diff is a defect. G10 and the whole-value
`TableRelation` `#if` have no production sites, so they change fixtures only.

### 4.3 Consumers

- **`queries/`:** no captures reference `table_relation_value`, `simple_table_relation` or
  `table:`. `folds.scm:207` and `indents.scm:167` match `preproc_conditional_table_relation`,
  which stays. A query capture test pins one D1 and one D2 site, so a future capture on either
  is written against the new shapes.
- **Oracle registry** (`tools/config_oracle/contracts.py`): no change is expected.
  `table_relation_value` stays a legal arm of `preproc_conditional_property_value`,
  `property_expression` already is one, and `preproc_conditional_table_relation` keeps its
  hosts. The quick tier confirms this.
- **Traversal policy:** no node type is added or removed. The census confirms this.
- **CHANGELOG migration note:**
  1. Relations: match `simple_table_relation`, or the property named `TableRelation`. This
     now finds every relation, not 42%.
  2. A dotted value of any other property is an ordinary `member_expression` inside
     `property_expression`.

## 5. Verification

### 5.1 Compiler evidence

New cases under `tools/alc_probe/cases/table-relation-keying/`, each with `// expect:` and
`// source:` headers. They are written and run **before** any grammar change.
- **Accept:**
  - bare, quoted, dotted, `where`, `if`/`else`;
  - lowercase `tablerelation`;
  - whole-value `#if` with the `;` after `#endif`, and with the `;` inside every arm;
  - `AutoFormatExpression = Rec."Currency Code";`.
- **G10, four-way:** `X` defined and undefined, each with the file as written and resolved
  flat.
- **Reject:** at least one malformed relation, for the negative fixture, e.g. `where` with no
  table, or `if` without a relation.

### 5.2 Fixtures (`test/corpus/`)

- **`table_relation_keying_test.txt`**, with expected trees generated from `tree-sitter parse`
  so they carry field labels. Each is proven able to fail by renaming one field to `bogus:`.
  - every row of §4.1;
  - G10;
  - `ValidateTableRelation = false;` and `TestTableRelation = false;` stay generic;
  - casing (`TABLERELATION`, `tablerelation`);
  - a comment between the name and `=`;
  - one fixture per host class from the scanner-state audit (§5.4).
- **`table_relation_keying_negative_test.txt`:** the alc-rejected forms. Each must ERROR
  inside the value, never become a clean expression or a clean second property.
- **Existing fixtures** that assert the old shapes are rewritten by hand, each hunk traced to
  D1, D2 or G10. Never use a blind `-u` (CLAUDE.md traps 1, 2 and 5). Run
  `git diff --stat test/corpus` after every `-u`.

### 5.3 Oracle

- **Quick tier:** exit 0. Any new fixture record is classified, with alc_probe evidence.
- **Full tier over the four corpora:** exit 0, 0 discrepancies.
- **Existing tests:** `tools/config_oracle/tests/test_table_relation.py` and
  `test_property_value_conditional.py` keep passing. A test that asserted a relation reading
  for a non-`TableRelation` value is rewritten to the expression reading, with the reason in
  the commit.

### 5.4 Scanner-state audit

After generating, read `ts_external_scanner_states` in `src/parser.c`. Every row that offers
`PROPERTY_NAME` either also offers `TABLE_RELATION_PROPERTY_NAME`, or is documented as a host
where `TableRelation` cannot occur, with a debug parse as evidence. This is B4 Task 2 Step 8's
method.

### 5.5 Gates

- `validate-grammar.sh --full`: exit 0, BC.History 0 errors.
- has_error sweeps over all four corpora: no new error files. BCApps keeps its 2 known files.
- `tree-harness verify` against a fresh `.snapshots/baseline-b5`: only D1 and D2 (§4.2).
- A `table:` census: 0 `simple_table_relation` nodes under a property not named
  `TableRelation`, over all four corpora.
- `snip.py --census`, `qc run`, the traversal census and pytest, and `npm test`.
- An incremental test, following `test_pair_list_incremental.py`. It edits
  `TableRelation` ↔ `TableRelationX` ↔ `Visible`, `TableRelation` ↔ `tablerelation`, inserts
  `where(...)`, and wraps the value in a `#if`. The incremental tree must equal a fresh parse.

### 5.6 Budget

- **STATE_COUNT ≤ 17,231**, which is the post-B4 16,893 × 1.02. B5 removes
  `table_relation_value` from every generic value position, so a decrease is expected.
- **Speed:** `tools.perf ab` against a library built from the B4 merge (`6b15b9b`). The
  confidence interval must contain 1.0, or the slowdown must be within the A/B test's
  resolution.
- Over budget is a stop: report the numbers and the per-rule cost (`--report-states-for-rule`).

## 6. Docs

- **CHANGELOG `[Unreleased]`, breaking:** D1, D2, the G10 fix, and the migration note (§4.3).
- **CLAUDE.md, "Name-keyed properties":** four families. Add `TableRelation`, with the §2.1
  evidence in one sentence. Add a `TABLE_RELATION_PROPERTY_NAME` row to the token table.
- **`.claude/rules/scanner.md`:** the token row, the dispatch list (now ten tokens), and the
  emission order.
- **`docs/deferred-work.md`:** items 13 and 15 RESOLVED with the commit hashes. Add a new item
  (§8).
- **Roadmap:** a B5 done note with STATE_COUNT, the A/B result and the tree-harness delta.
  Record that decision 2 was superseded and why (§2.1).

## 7. Risks

| Risk | Mitigation |
|---|---|
| A property host offers `PROPERTY_NAME` without the keyed token, so `TableRelation = X where(...)` ERRORs there | The §5.4 audit, plus one fixture per host class |
| G10 still ERRORs on the expression path | §3.3: it is the first task, and its fix is in scope |
| A D2 value's expression reading differs from what alc parses, e.g. `CustLedgEntry[6]."Currency Code"` | The census lists every D2 property. alc types them all as expressions (§2.1). The accept probe includes the subscript form |
| Removing `table_relation_value` from `_property_value` exposes a GLR fork between expression readings | tree-harness allows only D1 and D2. `metrics.sh` shows no new conflict entries |
| A fixture asserted the relation reading of a non-`TableRelation` value as correct | That is D2. The fixture is rewritten, and the hunk is traced in the commit |

## 8. Not in scope

- **`table:` on every segment.** `namespacedRefFielded` fields every segment of
  `Customer."No."` as `table:`, including the field segment. AL syntax cannot separate
  `Namespace.Table` from `Table.Field`. This becomes a new deferred-work item, which needs its
  own compiler-evidence pass (how alc's `TableRelationPropertyValueSyntax` splits the name).
- **Keying the compiler's other value kinds:** text, boolean, client-side boolean, style and
  integer expressions. Under this spec they are all the generic expression reading, which is
  what they are.
- **`#if` inside a relation's `where` list:** roadmap B7.
