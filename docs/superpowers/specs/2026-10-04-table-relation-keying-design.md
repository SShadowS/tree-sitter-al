# B5: `TableRelation` keyed by name, one relation target, dotted values are expressions (G10)

**Status:** approved in conversation on 2026-10-04, section by section. Revised the same day
after a gpt-6.1-sol review: 9 findings, all verified against the decompiled compiler and the
grammar before they were adopted (§9). This revision awaits review.
**Roadmap row:** B5 (`docs/superpowers/plans/2026-09-28-roadmap-remaining-work.md`).
**Resolves:** deferred-work items 13 (G10) and 15. It also fixes the relation target shape, which
was found while writing this spec (§1, case 4).
**Deviates from roadmap decision 2.** Decision 2 asked for a neutral reference node and "no
broad name-keying". The compiler reaches its relation grammar through one property name,
`TableRelation`, and nothing else (§2.1). So this spec keys that one name, the way B4 keyed
the ML names, and adds no neutral node. The choice was made in conversation on 2026-10-04,
over decision 2 as written and over a hybrid of the two.
**Ships in:** the next major. It changes trees for every `TableRelation` value and for 14,011
dotted values of other properties (§4.2).

## 1. Problem

```al
TableRelation = Customer;                     // 1. value: (identifier)               -- not a relation
AutoFormatExpression = Rec."Currency Code";   // 2. (table_relation_value ... table: (identifier 'Rec')) -- an expression
Visible = Rec.A
#if X
 and B
#endif
;                                             // 3. table_relation_value with an ERROR arm (G10)
TableRelation = Customer."No." where(...);    // 4. table: (identifier 'Customer') table: (quoted_identifier '"No."')
TableRelation = MakeCustomer()."No.";         // 5. clean table: (member_expression (call_expression ...))
```

1. A bare `TableRelation` value gets the generic leaf. A query for relations finds 25,714 of
   61,832 production relations, 42%.
2. `_property_value` offers `table_relation_value` to every property. So every dotted value
   becomes a "relation", with `Rec` fielded `table:`.
3. When an expression continues past a `#if`, the relation reading still wins, and its arms
   cannot hold `and B`.
4. `namespacedRefFielded` (`grammar.js:42`) fields **every** segment `table:`, including the
   field segment. alc reads the target as ONE qualified name (§2.1).
5. `simple_table_relation` also accepts `field('table', $.member_expression)`
   (`grammar.js:1658`). `member_expression.object` is any expression, so calls, subscripts and
   arithmetic all parse clean as relation targets.

In production this branch is reached only by namespace-qualified targets whose first segment
is a keyword:

| file | line | target |
|---|---|---|
| `ReplicationRecordLinkBuffer.Table.al` | 57 | `System.Environment.Company.Name` |
| `UserPermissionsBuffer.Table.al` | 39 | `System.Environment.Company.Name` |
| `RequisitionLine.Table.al` | 753, 795 | `System.Reflection.AllObjWithCaption."Object ID"` |
| `UserGroupPlan.Table.al` | 19, 20 | `System.Azure.Identity.Plan."Plan ID"` |

## 2. Ground truth

### 2.1 How the compiler parses these values

**Source.** alc 18.0.41.62505, `Microsoft.Dynamics.Nav.CodeAnalysis.dll` (net10.0), decompiled
with ilspycmd 11.0. Line numbers are in the decompiled `ObjectParser.cs`.

**Dispatch is by name × host.** `ObjectParser` keeps one `PropertyTypeInfo` table per host
kind ("Field", "Page", "PageField", "PageAction", ...). Each table is keyed by the upper-cased
name, and each entry carries its own parse delegate. `PropertyNameToSyntaxDefinition` is a
name-only summary, and it is not the dispatch: it says Boolean for `Enabled`, while page fields
parse `Enabled` as a client-side boolean expression.

**The relation grammar.** `ParseTableRelationPropertyValue` (11423) is reached from the
`TableRelation` entries of the table-field and page-field hosts (857, 2503). It parses:
- an optional `if (...)`;
- **one** `relatedTableField = ParseQualifiedName()`;
- optional table filters (`where`);
- an optional `else`, followed by a recursive relation.

The target is a single qualified name. The compiler makes no table/field split, and the target
is never an expression.

**The eight properties whose dotted values are misparsed today (class D2, §4.2), by host:**

| property | host(s) where production uses a dotted value | parse delegate | reaches |
|---|---|---|---|
| `AutoFormatExpression`, `DataCaptionExpression` | field / page | `ParseTextExpressionPropertyValue` (10083) | `ParseExpressionPropertyValue` |
| `Visible`, `ShowMandatory` | page field, action, group | `ParseClientSideBooleanExpressionPropertyValue` (10088) | `ParseExpressionPropertyValue` |
| `Enabled`, `Editable` | page field, action, group | ClientSideBooleanExpression (2407, 2414, 2662, 1686) | `ParseExpressionPropertyValue` |
| `StyleExpr` | page field | `ParseStyleExpressionPropertyValue` (9973) | `ParseExpressionPropertyValue` |
| `IndentationColumn` | page | `ParseIntegerExpressionPropertyValue` (9978) | `ParseExpressionPropertyValue` |

`Enabled` and `Editable` in the table-field and page hosts (862, 871, 1084, 1295) are literal
Boolean (`ParseBooleanLiteralValue`, 9968). A dotted value there is invalid AL. The census
records each D2 site's host (§5.5), and the gate fails if any D2 site sits in a host whose
delegate is not an expression parser.

**Relation-like grammars that are NOT relations.** They are out of scope here:
- the TableFilter kind (`SubPageLink`, `RunPageLink`, `LinkFields`, `DataItemTableFilter`,
  `ColumnFilter`), parsed by `ParseTableRelationConditionValue`;
- the TableView and Filters kinds, parsed by `ParseTableFilters`;
- object references (`SourceTable`, `LookupPageId`, ...), parsed by `ParseObjectReferenceSyntax`.

None of them reaches the full relation grammar, and none of their production values is a
`table_relation_value` today (§2.2).

This meets the keying rule in CLAUDE.md. `TableRelation`'s value has its own grammar, and
`Customer."No."` cannot be told apart from a member access in ours.

### 2.2 Production census

**Scope.** BC.History, DC, BC28.1 and BCApps-29.0, at `6b15b9b`, over every `property` node.
The scripts are the starting point for the committed census (§5.5).

**`TableRelation`** (61,832 values):

| today's value node | sites |
|---|---|
| `quoted_identifier` (bare) | 28,604 |
| `identifier` (bare) | 7,514 |
| `table_relation_value` | 25,712: `where` 13,680, plain 7,093, `if`/`else` 4,939; 6 of these reach the `member_expression` branch (§1, case 5) |
| `table_relation_value` with a `#if` inside (an `if`/`else` chain split by `#if`, DC) | 2 |
| `preproc_conditional_property_value` (whole-value `#if`) | 0 |

**Every other property whose value is `table_relation_value`:** 14,011, all of them plain
dotted names. The census found no `where`, `if` or `#if` outside `TableRelation`.

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

**What this census does not prove.** It counts value nodes. It does not check `has_error`,
and it detects dottedness only through `member_expression`. So it cannot show that G10 has no
production sites. §5.5 replaces it with a per-site manifest.

## 3. Mechanism

### 3.1 Scanner (`src/scanner.c`)

- Add `TABLE_RELATION_PROPERTY_NAME` to `TokenType` and to `externals` in `grammar.js`, after
  `NAMESPACES_PROPERTY_NAME`.
- `read_identifier_word` gains `WORD_TABLE_RELATION`, a whole-word, case-insensitive match on
  `tablerelation`. That is 13 characters, inside the 32-byte buffer. `ValidateTableRelation`
  and `TestTableRelation` stay `WORD_OTHER`.
- The emission order becomes CalcFormula → ML → Namespaces → TableRelation → generic
  `PROPERTY_NAME` → decline. Each keyed token is emitted only if `valid_symbols` offers it.
- Add the token to all three guards that list the keyed tokens:
  - the error-recovery all-valid guard (~555);
  - the identifier-dispatch entry guard (~951);
  - the property-block entry guard (~1023).

  B4 needed all three. Missing one leaves the keyed token unreachable in some states.

### 3.2 Grammar (`grammar.js`)

1. **New node `qualified_name`**, the relation target:
   ```javascript
   qualified_name: $ => prec.right(seq(
     $._qualified_name_segment,
     repeat(seq('.', $._qualified_name_segment)),
   )),
   ```
   - A segment is an `identifier` or `quoted_identifier` leaf.
   - A keyword spelling used as a segment is aliased to `identifier`. That covers `System` in
     the §1 targets, and any keyword the corpus shows in segment position.
   - The plan takes the keyword list from the production targets and pins each one.
   - Segments have no field. The node names the whole target, and nothing asserts which segment
     is the table.
2. **`simple_table_relation`** becomes:
   ```javascript
   seq(field('target', choice($.integer, $.qualified_name)), optional(prec(25, $.where_clause)))
   ```
   - It loses the repeated `table:` fields and the `member_expression` alternative.
   - `integer` keeps `TableRelation = 18;`. The probe checks that alc accepts it.
3. **`property`** gets a fourth keyed arm:
   ```javascript
   seq(
     field('name', alias($._table_relation_property_name, $.property_name)),
     '=',
     optional(field('value', $._table_relation_property_value)),
     ';'
   ),
   ```
4. **`_table_relation_property_value`** separates the whole value from relation continuation:
   - A **value-start relation**, aliased to `table_relation_value`. It begins with a
     `simple_table_relation` or an `if_table_relation`, **never with a `#if`**, and may then
     continue into `preproc_conditional_table_relation`, the existing split form.
   - A **whole-value conditional**, aliased to `preproc_conditional_property_value`. It is built
     with B4's `keyedValueConditional`, and each arm is recursive:
     `seq(field('value', $._table_relation_property_value), optional(';'))`.

   A `#if` at value start is therefore always the whole-value wrapper, and an arm can hold a
   nested whole value. That gives one derivation per input. `table_relation_value`'s bare
   `preproc_conditional_table_relation` alternative and `table_relation_expression`'s are no
   longer reachable at value start.

   The plan checks whether alc accepts a continuation after a value-start `#if`, e.g.
   `#if X if (...) A #else if (...) B #endif else C`. If alc accepts it, this item is revisited
   before any grammar change.
5. **`_property_value`** loses `$.table_relation_value`.
6. **`_property_with_terminator_in_if` and `_property_whole_value_in_if`** lose the generic
   relation form, `alias($._table_relation_split_value, $.table_relation_value)`. Each gains a
   keyed `TableRelation` arm:
   - **`_property_with_terminator_in_if`:** the keyed conditional, plus the relation continued
     into a `#if` whose arms carry the `;`.
   - **`_property_whole_value_in_if`:** the keyed conditional only.

   After this item and item 5, no route from a generic property reaches
   `table_relation_value`, `preproc_conditional_table_relation` or `simple_table_relation`.
   Every reference is checked by grep in the plan.
7. **Conflicts.** The `conflicts` entries that pair `preproc_conditional_table_relation` with
   the generic conditionals (around `grammar.js:356-406`) are re-checked after the change. An
   entry the generator no longer needs is deleted, with the STATE_COUNT measured.
8. **Unchanged:**
   - `if_table_relation`, keeping `then_relation:` and `else_relation:`;
   - `else_table_relation_fragment`;
   - `where_clause`;
   - `preproc_conditional_table_relation`'s own arm grammar.

### 3.3 G10: the first task, measured

There is an existing route:
- `_property_value` → `_property_value_with_split` → `_expression`;
- then `preproc_conditional_expression_tail`, whose continuation takes `and B`
  (`grammar.js:1080-1102`, `1189-1197`, `4684-4790`).

The reviewer predicts that the G10 input parses as `property_expression` with a member
prefix and that tail once **both** generic relation routes are gone (§3.2 items 5 and 6).

The plan's first task makes exactly that removal in isolation. It generates, then asserts the
G10 tree with exact parents and fields, flat and split. Only then does the rest of B5 proceed.
If the expression path still ERRORs, its fix is a separate task inside B5. Keeping the relation
reading is not a fallback.

## 4. Node contract and deltas

### 4.1 Contract

```
TableRelation = Customer."No." where(...);
  -> (property name: (property_name)
       value: (table_relation_value
                (table_relation_expression
                  (simple_table_relation
                    target: (qualified_name (identifier) (quoted_identifier))
                    (where_clause ...)))))
TableRelation = 18;            -> ... (simple_table_relation target: (integer))
TableRelation = if (...) A else B;   -> if_table_relation, unchanged apart from the targets
TableRelation = #if ... #endif [;]
  -> (property name: (property_name)
       value: (preproc_conditional_property_value
                (preproc_if ...)
                value: (table_relation_value ...) | (preproc_conditional_property_value ...)
                ...
                (preproc_endif ...)))
TableRelation = ;              -> (property name: (property_name))   -- only if alc accepts it (§5.1)
<other name> = A.B;            -> (property name: (property_name) value: (property_expression (member_expression ...)))
```

**Field rules:**
- `property.name` is `property_name` in every arm.
- `simple_table_relation.target` is exactly one node, `qualified_name` or `integer`. It is
  never repeated and never an expression.
- `qualified_name` has no fields. Its segment children are `identifier` or `quoted_identifier`.
- Every arm `value:` of a `TableRelation` whole-value `#if` is a `table_relation_value` or a
  nested `preproc_conditional_property_value`. Both `;` placements give the same tree.
- A split inside a relation keeps its node: `table_relation_value` holding
  `preproc_conditional_table_relation`. Only its targets change, as everywhere else.

**Who enforces what:**
- **`tools/check-field-types.py`**, which checks `node-types.json`, gets the type-level rules:
  - `simple_table_relation.target`: single, `{integer, qualified_name}`;
  - `qualified_name`: no fields;
  - the `table` field on `simple_table_relation` is gone.
- **The runtime census (§5.5)** enforces the rules that depend on the property name.
  `check-field-types.py` cannot see the name: every keyed arm aliases to the same `property`
  type.

### 4.2 Intended deltas

**Production classes** (four corpora; every changed subtree must be exactly one of these):

| class | before | after | sites |
|---|---|---|---|
| D1 | `TableRelation` value `identifier` / `quoted_identifier` | `table_relation_value(table_relation_expression(simple_table_relation target: (qualified_name (same leaf))))` | 36,118 |
| D2 | other property value `table_relation_value(...)` | `property_expression(...)`, with the expression the value really is: `member_expression`, or a subscript base for `CustLedgEntry[6]."Currency Code"` | 14,011 |
| D3 | `simple_table_relation` with one or more `table:` children, or `table: member_expression` | `target: (qualified_name ...)` or `target: (integer)`, same segments in source order | every relation under `TableRelation`: 25,714 values, each `simple_table_relation` in them |

**Fixture-only classes** (input that does not occur in production):
- **F1:** a `TableRelation` whole-value `#if`. Arms become uniformly `table_relation_value`;
  nested whole values become a nested `preproc_conditional_property_value`.
- **F2:** G10, ERROR → `property_expression` + `preproc_conditional_expression_tail`.
- **F3:** a generic property's whole-value `#if` whose arm held a `table_relation_value`. The
  arm becomes `property_expression`.

A changed file is not proof. The gate compares each changed subtree against its class (§5.5).

### 4.3 Consumers

- **`queries/`:** no capture references `table_relation_value`, `simple_table_relation` or
  `table:`. `folds.scm:207` and `indents.scm:167` match `preproc_conditional_table_relation`,
  which stays. A query capture test pins one D1, one D2 and one D3 site.
- **Oracle registry** (`tools/config_oracle/contracts.py`):
  - `table_relation_value` stays a legal arm of `preproc_conditional_property_value`;
  - `preproc_conditional_table_relation` keeps its hosts;
  - `qualified_name` is not a conditional, so it needs no registry entry.
  
  The quick tier and the registry census confirm all three.
- **Traversal policy:** `qualified_name` is a new type, and the traversal census decides
  whether it needs an entry.
- **CHANGELOG migration note:**
  1. A relation's target is `simple_table_relation target: (qualified_name ...)`. Read its
     text whole; which segment is the table needs symbol resolution.
  2. Every `TableRelation` value is relation-shaped, so match the property named
     `TableRelation`, or `simple_table_relation`.
  3. A dotted value of any other property is an expression.
  4. A generic property can still take link syntax. That is roadmap row B5b, not fixed here.

## 5. Verification

### 5.1 Compiler evidence

Cases go under `tools/alc_probe/cases/table-relation-keying/`, written and run **before** any
grammar change.

- **Accept, each in a table field and in a page field:**
  - bare, quoted, dotted;
  - namespace-qualified, with a keyword first segment (`System.Environment.Company.Name`);
  - `where`, `if`/`else`;
  - lowercase `tablerelation`;
  - `TableRelation = 18;`;
  - whole-value `#if` with both `;` placements, and nested;
  - `AutoFormatExpression = Rec."Currency Code";`;
  - `AutoFormatExpression = CustLedgEntry[6]."Currency Code";`.
- **Decide by probe:**
  - `TableRelation = ;`. Accept means the contract keeps the empty value. Reject means the
    empty arm goes, and the case becomes a negative.
  - A continuation after a value-start `#if` (§3.2 item 4).
- **G10, four-way:** `X` defined and undefined, each as written and resolved flat.
- **Reject:**
  - `TableRelation = MakeCustomer()."No.";`
  - `TableRelation = Customers[1]."No.";`
  - `TableRelation = (A + B).F;`
  - `where` with no target;
  - `Enabled = Rec."X";` in a table field, a literal-Boolean host.

### 5.2 Fixtures (`test/corpus/`)

- **`table_relation_keying_test.txt`**, with expected trees generated from `tree-sitter parse`
  so they carry field labels. Each is proven able to fail by renaming one field to `bogus:`.
  It contains:
  - every row of §4.1;
  - G10;
  - `ValidateTableRelation = false;` and `TestTableRelation = false;` staying generic;
  - casing;
  - a comment between the name and `=`;
  - one case per host:

    | host | flat | whole-value `#if` | continued |
    |---|---|---|---|
    | table field | ✓ | ✓ | ✓ |
    | tableextension added field | ✓ | ✓ | ✓ |
    | tableextension `modify` | ✓ | ✓ | ✓ |
    | page field | ✓ | ✓ | ✓ |
    | pageextension `modify` | ✓ | ✓ | ✓ |
    | report request-page field | ✓ | | |
    | xmlport request-page field | ✓ | | |

    Each host case must be accepted by alc.
- **`table_relation_keying_negative_test.txt`:** the §5.1 rejects. Each ERRORs inside the
  value. None becomes a clean expression, a clean target or a clean second property.
- **Existing fixtures** that assert old shapes are rewritten by hand, each hunk traced to D1–D3
  or F1–F3. Never use a blind `-u` (CLAUDE.md traps 1, 2 and 5). Run
  `git diff --stat test/corpus` after every `-u`.

### 5.3 Oracle

- **Quick tier:** exit 0. New fixture records are classified, with alc_probe evidence.
- **Full tier over the four corpora:** exit 0, 0 discrepancies.
- **`test_table_relation.py` and `test_property_value_conditional.py`:** both keep passing. A
  test that asserted a relation reading for a non-`TableRelation` value is rewritten to F3, with
  the reason in the commit.

### 5.4 Scanner-state audit

After generating, read `ts_external_scanner_states` in `src/parser.c`. Two directions:
- Every row offering `PROPERTY_NAME` also offers `TABLE_RELATION_PROPERTY_NAME`, or is
  documented as a host where `TableRelation` cannot occur, with a debug parse as evidence.
- Every row offering a keyed token is checked against the generic token too.

This is B4 Task 2 Step 8's method. §5.2's host list is the fixture side; shared scanner rows
are not proof of context coverage.

### 5.5 Gates

**The committed relation census**, `tools/relation_census.py`, run over the four corpora. Its
exit codes follow `has_error_sweep.py`. It enforces, in both directions:

| check | what it requires |
|---|---|
| relation shape | every nonempty `TableRelation` value is `table_relation_value` or `preproc_conditional_property_value`, recursively through whole-value arms |
| relations stay put | no `table_relation_value`, `simple_table_relation` or `qualified_name` appears outside a `TableRelation` property |
| target | every `simple_table_relation` has exactly one `target`, and no `table` field |
| D2 hosts | every D2 site's host has an expression-parser delegate for that name (§2.1) |
| errors | `has_error` is reported per file |

It also writes a per-site manifest:
- path, line and source hash;
- property name and host;
- old and new subtree shape;
- the D/F class.

**Mutation proof.** The census is proven able to fail in both directions:
- force a `TableRelation` onto the generic path, by disabling the keyed token in a scratch
  build;
- force a generic dotted value onto the relation path, by restoring `table_relation_value` to
  `_property_value`.

**The other gates:**
- **`tree-harness verify` against a fresh `.snapshots/baseline-b5`:** every changed subtree
  matches its manifest class, and nothing else changes.
- **`validate-grammar.sh --full`:** exit 0, BC.History 0 errors.
- **has_error sweeps over all four corpora:** no new error files.
- **The usual suite:** `snip.py --census`, `qc run`, the traversal census and pytest, and
  `npm test`.
- **Incremental test**, following `test_pair_list_incremental.py`. It covers:
  - `TableRelation` ↔ `TableRelationX` ↔ `Visible`;
  - `TableRelation` ↔ `tablerelation`;
  - inserting `where(...)`;
  - wrapping the value in a `#if`;
  - B4's lookahead-boundary edit, one space past the name.

### 5.6 Budget

- **STATE_COUNT ≤ 17,231**, which is the post-B4 16,893 × 1.02. A decrease is expected.
- **Speed:** `tools.perf ab` against a library built from `6b15b9b`. The confidence interval
  must contain 1.0, or the slowdown must be within the A/B test's resolution.
- Over budget is a stop: report the numbers and `--report-states-for-rule`.

## 6. Docs

- **CHANGELOG `[Unreleased]`, breaking:** D1, D2, D3, the G10 fix, and the migration note
  (§4.3).
- **CLAUDE.md "Name-keyed properties":** four families. `TableRelation` gets its §2.1 evidence
  in one sentence, and the token table gets a row.
- **`.claude/rules/scanner.md`:** the token row, the dispatch list (ten tokens), the emission
  order, and the three guards.
- **`docs/deferred-work.md`:** items 13 and 15 RESOLVED, with commit hashes.
- **Roadmap:**
  - a B5 done note with STATE_COUNT, the A/B result and the manifest totals;
  - decision 2 recorded as superseded, and why;
  - a new row **B5b**, keying the link family (§8).

## 7. Risks

| Risk | Mitigation |
|---|---|
| A host offers `PROPERTY_NAME` without the keyed token | §5.4 in both directions, plus §5.2's host list |
| G10 still ERRORs on the expression path | §3.3: it is the first task, and its fix is in scope |
| A keyword spelling occurs as a target segment and is not covered by `qualified_name` | The plan derives the keyword list from the production targets. The census `has_error` check fails on any miss |
| A value-start `#if` followed by a continuation is valid AL | Probed first (§5.1). If alc accepts it, §3.2 item 4 is revisited before any grammar change |
| Removing `table_relation_value` from `_property_value` exposes another false generic reading, e.g. link syntax | Not prevented here. It is stated (§4.3, §8). The census fails if any relation node appears outside `TableRelation` |
| The target change hides a fixture that asserted `table:` segments as correct | That is D3. Each hunk is traced |

## 8. Not in scope

- **The link leak.** `Visible = Flag = Rec.OtherFlag;` parses today as a clean
  `link_value_list`, because `link_value`'s dotted-RHS arm carries dynamic precedence
  (`grammar.js:1550-1583`). That is the same root cause, a generic property offered a
  name-specific grammar, in a different family: the compiler's TableFilter and DataItemLink
  properties. It becomes roadmap row **B5b**, in the same major release.
- **Symbol resolution.** Which segment of a `qualified_name` is the namespace, the table or
  the field is linter or LSP work.
- **Keying the compiler's other value kinds.** Under this spec they are the generic expression
  reading, which is what alc parses for the D2 hosts.
- **`#if` inside a relation's `where` list:** roadmap B7.

## 9. Review record

A gpt-6.1-sol review of the first revision raised 9 findings. Each was checked against the
decompiled `ObjectParser.cs` and the grammar before it was adopted:

1. **Name table vs. per-host dispatch.** Adopted: §2.1 now has a name × host × delegate matrix,
   and Boolean is literal (9968).
2. **`table:` on every segment, against one `ParseQualifiedName`.** Adopted, in scope: D3 and
   `qualified_name`.
3. **Two derivations for a value-start `#if`, and non-recursive arms.** Adopted: §3.2 item 4.
4. **The `member_expression` escape in the target.** Adopted: §3.2 item 2. Production sites:
   the 6 namespace-qualified targets in §1.
5. **The link-syntax leak.** Confirmed live, and given its own row: §8, B5b.
6. **`check-field-types.py` cannot key on the property name.** Adopted: the runtime census
   (§5.5).
7. **D1/D2 incomplete; the census was weaker than claimed.** Adopted: D3, F1–F3 and the
   manifest.
8. **Host fixtures underspecified.** Adopted: the explicit table in §5.2.
9. **Two scanner guards missing; G10 needs both routes removed.** Adopted: §3.1 and §3.3.
