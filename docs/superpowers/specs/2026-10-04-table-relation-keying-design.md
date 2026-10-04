# B5: `TableRelation` keyed by name, one relation target, dotted values are expressions (G10)

**Status:** approved in conversation on 2026-10-04, section by section. Revised the same day
after a gpt-6.1-sol review: 9 findings, all verified against the decompiled compiler and the
grammar before they were adopted (§9). Revised again after a second round of that review: 6
findings, all adopted (§9). This revision 3 awaits review.
**Revision 4 (2026-10-05, Task 1 compiler evidence).** Three probe results amend this spec.
Where an older passage disagrees, this block wins:
1. **Segments.** alc accepts `begin`, `end` and `then` as relation-target segments, and rejects
   `if`, `else` and `where`. The segment rule is therefore "a word the property-value lexer
   makes an identifier", not the 101-kind `IsKeywordAllowedIdentifier` list.
   `_qualified_name_segment` is `identifier | quoted_identifier`, with no keyword list. In the
   keyed states, the only keyword tokens tree-sitter's keyword extraction can produce are `if`
   (value start) and `where` / `else` (after a target), which matches alc's rejections. The
   facts file stays: the containment test uses it as a word list.
2. **Empty value and integer targets.** `TableRelation = ;` and the four integer forms are
   rejected (AL0107). The keyed arm's value is required, and all five are negatives.
3. **A value-start `#if` followed by a shared `else` continuation** is accepted
   (`#if X if (..) A #else if (..) B #endif else C`, split and flat). It parses as
   `table_relation_value(preproc_conditional_table_relation ..., else_table_relation_fragment
   ...)`, the mirror of the existing `relation preproc_conditional_table_relation` split. It
   costs one declared conflict between that reading and the whole-value wrapper, decided at the
   token after `#endif`. It ERRORs today, and has 0 production sites.

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

**The segment grammar.** `ParseQualifiedName` (`LanguageParser.cs:696`) reads one
`ParseIdentifierName()` per segment, separated by `.`. `ParseIdentifierName` takes a token for
which `SyntaxKind.IsTokenIdentifier()` holds (`SyntaxFacts.cs:3792`):
- an `IdentifierToken`, which covers plain and double-quoted names;
- or one of the **101 keyword kinds** in `IsKeywordAllowedIdentifier`, among them `System`,
  `Table`, `TableData`, `Page`, `Codeunit`, `Field`, `Type`, `Filter`, `Order`, `Enum` and
  `Namespace`.

No integer or other literal token is a segment. The 101 spellings are committed as data with
their provenance: `tools/alc_facts/keyword-allowed-identifiers.txt`, alc version, DLL sha256,
and the method each was read from. That list, not the corpus, defines the segment rule (§3.2
item 1).

**The eight D2 properties: what the compiler expects, by host.** `ObjectParser`'s
`PropertyTypeInfo` tables are generated data, not prose. One row per (upper-cased name, host
kind, value kind, parse delegate) is extracted from the decompiled tables into
`tools/alc_facts/property-hosts.tsv`, with the same provenance header as the keyword list. Hand
transcription is what put wrong host rows in revision 2 of this spec: line 1084 is a Key entry,
and `IndentationColumn` is registered on PageGroup.

The rule the census enforces (§5.5) reads that file. A D2 site is legitimate only if every
compiler host its tree context can map to gives that name a delegate that reaches
`ParseExpressionPropertyValue`.

The four expression delegates do reach it:
- `ParseTextExpressionPropertyValue` (10083);
- `ParseClientSideBooleanExpressionPropertyValue` (10088);
- `ParseStyleExpressionPropertyValue` (9973);
- `ParseIntegerExpressionPropertyValue` (9978).

`ParseBooleanPropertyValue` (9968) does not: it calls `ParseBooleanLiteralValue`. So
`Enabled = Rec."X";` is valid in a page field (ClientSideBooleanExpression) and invalid in a
table field (Boolean).

**Mapping a tree context to a compiler host** is an explicit table in the census, with one row
per context:
- table field;
- tableextension added field;
- page field;
- page action;
- page group;
- page part;
- page label;
- report and xmlport request-page field, which reach `ParsePageLayout` (10706-10722,
  11574-11592), so page-field dispatch;
- control `modify`, which resolves through `LookupAnyControlProperty`, a field-first lookup
  chain (9482-9485, 9552-9561): all hosts in the chain;
- action `modify`, which resolves through `LookupAnyActionProperty` (9369-9378): all hosts in
  that chain.

An unmapped context fails visibly. It is never guessed.

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

1. **New node `qualified_name`**, the relation target. It follows `ParseQualifiedName` (§2.1):
   ```javascript
   qualified_name: $ => prec.right(seq(
     $._qualified_name_segment,
     repeat(seq('.', $._qualified_name_segment)),
   )),
   _qualified_name_segment: $ => choice($.identifier, $.quoted_identifier),   // rev 4
   // The compiler's IsKeywordAllowedIdentifier set, one bare kw() per spelling, generated
   // from tools/alc_facts/keyword-allowed-identifiers.txt.
   _keyword_allowed_identifier: $ => choice(kw('system'), kw('table'), /* ... all 101 */),
   ```
   - **Spellings.** They are the compiler's own keyword texts (`SyntaxFacts` text for each
     kind), not the `SyntaxKind` names. `PageGroupKeyword` is spelled `group`, not `pagegroup`.
     The data file records kind → text.
   - **Leaf shape.** The alternatives are **bare** `kw()` tokens aliased to `identifier`, so a
     keyword segment is a childless `identifier` leaf. That is the `keyword_as_identifier`
     direction in `.claude/rules/contextual-keywords.md`: the outer node claims to be an
     identifier, so the named `*_keyword` rules must not be used here.
   - **Containment.** These tokens become valid only in the keyed `TableRelation` target
     states: the value start, the token after `.`, and the target after `if (...)` or `else`.
     No generic property state gains them, so the `word`-extraction hazard described at
     `_plain_name` (`grammar.js:6290-6330`) cannot reach other properties. The plan verifies
     this from `src/parser.c` lex states. A keyword token that does leak into a generic state is
     a stop.
   - **Fields.** Segments have none. The node names the whole target, and nothing asserts which
     segment is the table.
2. **`simple_table_relation`** becomes:
   ```javascript
   seq(field('target', $.qualified_name), optional(prec(25, $.where_clause)))
   ```
   - It loses the repeated `table:` fields and the `member_expression` alternative.
   - **No integer target.** `ParseQualifiedName` reads identifier tokens only. `TableRelation
     = 18;` is a decide-by-probe case (§5.1), expected to be rejected. If alc accepts it, the
     probe shows the accepting path, and `integer` is added back to `target` with that evidence.
3. **`property`** gets a fourth keyed arm:
   ```javascript
   seq(
     field('name', alias($._table_relation_property_name, $.property_name)),
     '=',
     optional(field('value', $._table_relation_property_value)),
     ';'
   ),
   ```
   Rev 4: the value is required (`TableRelation = ;` is AL0107), so drop the `optional()`.
4. **The keyed value, written out.** Root and continuation are separated by structure:
   ```javascript
   // A value-start relation: never begins with #if.
   _table_relation_head: $ => choice($.simple_table_relation, $.if_table_relation),
   _table_relation_property_value: $ => choice(
     alias($._table_relation_rooted, $.table_relation_value),
     alias($._table_relation_whole_conditional, $.preproc_conditional_property_value),
   ),
   _table_relation_rooted: $ => prec.right(5, seq(
     alias($._table_relation_head, $.table_relation_expression),
     optional($.preproc_conditional_table_relation),   // the continued split, as today
   )),
   _table_relation_whole_conditional: $ => keyedValueConditional($,
     seq(field('value', $._table_relation_property_value), optional(';'))),
   // `;` inside the arms (no `;` after #endif): the keyed _table_relation_split_value.
   _table_relation_keyed_split: $ => choice(
     seq(alias($._table_relation_head, $.table_relation_expression),
         $.preproc_conditional_table_relation),
     alias($._table_relation_open_if, $.table_relation_expression),   // unchanged prec(-1) if_table_relation
   ),
   ```
   - **Continuations nested under `else` are unchanged.** `if_table_relation.else_relation` is
     still `table_relation_expression`, and that still includes
     `preproc_conditional_table_relation`. The DC witness (`ELSE` then `#if BC24 IF ...; #else
     IF ...; #endif`, no `;` after `#endif`;
     `DC/Cloud/.dependencies/DC/Table/CDCDataTranslation.Table.al:129-148`) takes
     `_table_relation_open_if` → `if_table_relation` → `else_relation:
     table_relation_expression(preproc_conditional_table_relation ...)`. That is the parse it
     gets today, apart from D3 targets.
   - **Where `#if` is unreachable.** `table_relation_value`'s own bare
     `preproc_conditional_table_relation` alternatives are removed: the old
     `table_relation_value` rule has no remaining user once item 5 lands, and `_table_relation_rooted`
     replaces it. A value-start `#if` therefore has exactly one derivation, the whole-value
     wrapper. Arms are recursive, so a nested whole value is a nested
     `preproc_conditional_property_value`.
   - **Value-start `#if` followed by a continuation**, e.g. `#if X if (...) A #else if (...) B
     #endif else C`: superseded by rev 4 item 3, because alc accepts it. Original text: it has no derivation under this design. alc is probed first (§5.1). If alc
     accepts it, this item is redesigned before any grammar change.
5. **`_property_value`** loses `$.table_relation_value`.
6. **`_property_with_terminator_in_if` and `_property_whole_value_in_if`** lose the generic
   relation form, `alias($._table_relation_split_value, $.table_relation_value)`. Each gains a
   keyed `TableRelation` arm:
   - **`_property_with_terminator_in_if`:** two values, `alias($._table_relation_whole_conditional,
     $.preproc_conditional_property_value)` and `alias($._table_relation_keyed_split,
     $.table_relation_value)`.
   - **`_property_whole_value_in_if`:** the whole conditional only.

   `_table_relation_split_value` is deleted.

   After items 4, 5 and 6, no route from a generic property reaches `table_relation_value`,
   `preproc_conditional_table_relation`, `simple_table_relation` or `qualified_name`. The plan
   checks every reference by grep and by a debug parse.
7. **Conflicts.** The `conflicts` entries that pair `preproc_conditional_table_relation` with
   the generic conditionals (around `grammar.js:356-406`) are re-checked after the change. An
   entry the generator no longer needs is deleted, with the STATE_COUNT measured.
8. **Unchanged:**
   - `if_table_relation`, keeping `then_relation:` and `else_relation:`, and its
     `else_relation` route into `preproc_conditional_table_relation`;
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
TableRelation = System.Environment.Company.Name;  -> target: (qualified_name (identifier) (identifier) (identifier) (identifier))
TableRelation = if (...) A else B;   -> if_table_relation, unchanged apart from the targets
TableRelation = #if ... #endif [;]
  -> (property name: (property_name)
       value: (preproc_conditional_property_value
                (preproc_if ...)
                value: (table_relation_value ...) | (preproc_conditional_property_value ...)
                ...
                (preproc_endif ...)))
TableRelation = #if X if (..) A #else if (..) B #endif else C;
  -> (table_relation_value (preproc_conditional_table_relation ...) (else_table_relation_fragment ...))   -- rev 4
<other name> = A.B;            -> (property name: (property_name) value: (property_expression (member_expression ...)))
```

**Field rules:**
- `property.name` is `property_name` in every arm.
- `simple_table_relation.target` is exactly one `qualified_name`. It is never repeated and
  never an expression. An integer target exists only if the §5.1 probe proves alc accepts one.
- `qualified_name` has no fields. Its children are segment leaves, each an `identifier` or a
  `quoted_identifier`, in source order. A keyword segment such as `System` is a childless
  `identifier`.
- Every arm `value:` of a `TableRelation` whole-value `#if` is a `table_relation_value` or a
  nested `preproc_conditional_property_value`. Both `;` placements give the same tree.
- A split inside a relation keeps its node: `table_relation_value` holding
  `preproc_conditional_table_relation`. Only its targets change, as everywhere else.

**Who enforces what:**
- **`tools/check-field-types.py`**, which checks `node-types.json`, gets the type-level rules:
  - `simple_table_relation.target`: single, `{qualified_name}`;
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
| D3 | `simple_table_relation` with one or more `table:` children, or `table: member_expression` | `target: (qualified_name ...)` whose segment sequence equals the old target's normalised sequence (below) | every relation under `TableRelation`: 25,714 values, each `simple_table_relation` in them |

**Fixture-only classes** (input that does not occur in production):
- **F1:** a `TableRelation` whole-value `#if`. Arms become uniformly `table_relation_value`;
  nested whole values become a nested `preproc_conditional_property_value`.
- **F2:** G10, ERROR → `property_expression` + `preproc_conditional_expression_tail`.
- **F3:** a generic property's whole-value `#if` whose arm held a `table_relation_value`. The
  arm becomes `property_expression`.

**D3 segment normalisation.** This is how the gate compares an old target with a new one. The
old target is mapped recursively to a sequence of segments, each a source span plus its exact
text:
- `identifier` or `quoted_identifier` → one segment;
- `keyword_identifier` (e.g. `System` reached through the old `member_expression` route) → one
  segment over its own span, recorded as an authorised keyword → `identifier` conversion;
- `member_expression` → the normalisation of its `object`, then its `member` as one segment;
- the repeated `table:` children of the old `namespacedRefFielded` form → one segment each, in
  order;
- anything else → **classification failure**. That covers a call, a subscript or an arithmetic
  base.

The new target's sequence is its segment children. They must match span for span and text for
text, quotes and casing included. Splitting text on `.` is never used: a quoted segment can
contain a dot. Everything outside the target must be unchanged: the `where_clause`, the `if`
condition, `else` attachment, and every conditional's position.

The six production `member_expression` targets (§1) are pinned individually.

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

**Self-contained probes.** Every probe declares the tables it relates to, so a missing symbol
cannot look like a rejection (CLAUDE.md, the AL0185 trap). Each verdict records syntactic
diagnostics separately from symbol diagnostics. A namespace-qualified target declares its
namespace.

- **Accept, each in a table field and in a page field:**
  - bare, quoted, dotted;
  - namespace-qualified, with a keyword first segment (`System.Environment.Company.Name`);
  - `where`, `if`/`else`;
  - lowercase `tablerelation`;
  - whole-value `#if` with both `;` placements, and nested;
  - the DC witness shape: `else` then a `#if` whose arms carry the `;`;
  - `AutoFormatExpression = Rec."Currency Code";`;
  - `AutoFormatExpression = CustLedgEntry[6]."Currency Code";`.
- **Keyword segments (§3.2 item 1).** A sample of the 101 compiler-allowed keywords in first,
  middle and last position, each spelled in mixed case and as a quoted identifier. The sample
  has at least 12 spellings, and includes `System`, `Table`, `Field`, `Order`, `Filter` and one
  page keyword whose text differs from its kind name, e.g. `group`. Every one should be
  accepted. Two keywords *outside* the set, e.g. `begin` and `where`, should be rejected as
  segments.
- **Decide by probe:**
  - `TableRelation = ;`. Accept means the contract keeps the empty value. Reject means the
    empty arm goes, and the case becomes a negative.
  - Integer targets: `TableRelation = 18;`, `TableRelation = 18."No.";`,
    `TableRelation = Customer.18;`, and `TableRelation = 18 where(...)`. All are expected to be
    rejected (§3.2 item 2). An accepted form is added to `target` with the accepting path
    named.
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
- **The two production `else` + `#if` sites** are pinned as fixtures, with exact parents and
  fields, in their real layout. One is `CDCDataTranslation.Table.al:129-148`; the plan finds
  the other from the census manifest.
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
exit codes follow `has_error_sweep.py`: 0 clean, 1 finding, 2 cannot run. A census that cannot
run never reports clean.

**Two modes.**
- `check` validates one parser library's trees against the contract.
- `delta` takes a **baseline** library (built from `6b15b9b`) and a **current** library, parses
  the same source with both, and classifies every difference.

`tree-harness verify` only reports differences and exits 1 on any intended change
(`tools/tree-harness.sh`). So `delta` is the gate for B5's changes, and tree-harness stays the
zero-change gate for everything else.

**Inventories.** Each mode builds an immutable inventory per library: every `property` node
and every relation node, keyed by a **site ID** of path, start byte and end byte, plus the
file's sha256. The source hashes must be identical between the two inventories, or the census
exits 2. A property present in one inventory and missing from the other is a finding; that
covers a dropped or reparented property.

**`check` enforces, in both directions:**

| check | what it requires |
|---|---|
| relation shape | every nonempty `TableRelation` value is `table_relation_value` or `preproc_conditional_property_value`, recursively through whole-value arms |
| relations stay put | no `table_relation_value`, `preproc_conditional_table_relation`, `simple_table_relation` or `qualified_name` appears outside a `TableRelation` property |
| target | every `simple_table_relation` has exactly one `target` child, it is a `qualified_name`, no `table` field occurs, and every segment child is an `identifier` or `quoted_identifier` leaf with no children |
| D2 hosts | every D2 site's tree context maps, through the census's context table (§2.1), to compiler hosts whose delegate for that name reaches `ParseExpressionPropertyValue` in `tools/alc_facts/property-hosts.tsv`; an unmapped context fails |
| errors | `has_error` per file, compared between the two inventories: a file that newly errors is a finding |

**`delta` classifies each difference by comparison root.**
- **D1 and D2:** the root is the property's `value` subtree.
- **D3:** the root is each `simple_table_relation`'s `target` subtree, with the rest of the
  relation compared node for node.

Roots are disjoint by construction: D3 is evaluated inside values that D1 and D2 do not claim.
A difference matching no class predicate is a finding, and so is a site matching two.

**Predicates:**
- **D1:** the old value is a leaf, and the new value is the wrapper whose target's single
  segment equals that leaf's span and text.
- **D2:** the property name is not `TableRelation`, and the old value is `table_relation_value`.
  The new value is `property_expression`, and its normalised dotted chain equals the old
  segment sequence.
- **D3:** the §4.2 normalisation.

The census writes a per-site manifest (site ID, property name, mapped host, class, old and new
shape) to `reports/`. The manifest's totals go in the B5 done note.

**Mutation proof.** The census is shown to fail, with the expected finding, on each of these
scratch builds or edited trees:
- a `TableRelation` forced onto the generic path, by disabling the keyed token;
- a generic dotted value forced onto the relation path, by restoring `table_relation_value` to
  `_property_value`;
- a dropped property;
- two segments reordered;
- `target` replaced by a `table` field;
- a segment wrapped in a non-leaf node;
- a `preproc_conditional_table_relation` moved from `else_relation` to the root.

**The other gates:**
- **`relation_census.py delta`** against the `6b15b9b` library: every difference is classified,
  and no finding is left.
- **`tree-harness verify` against a fresh `.snapshots/baseline-b5`:** every changed file is one
  the census manifest lists. tree-harness cannot classify a change, only list it.
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
| A compiler-allowed keyword segment is missing from `_keyword_allowed_identifier`, or one of its tokens leaks into a generic property state | The list is generated from the compiler (§2.1), and the probes sample it (§5.1). The plan checks lex states in `src/parser.c` for leaks. Census `has_error` fails on a production miss |
| An integer or other non-identifier target is valid AL after all | Decide-by-probe before any grammar change (§5.1). It is added back with the accepting path as evidence |
| The DC `else` + `#if` witness loses its attachment | Pinned with exact parents and fields (§5.2). The census mutation moves the conditional (§5.5). The oracle cannot validate this attachment (`test_table_relation.py:38-68`, and `production-classes.tsv` debt), so its exit 0 is not evidence here |
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

**Round 2** (same reviewer, revision 2). It marked findings 2, 4, 5, 8 and 9 resolved, and 1, 3,
6 and 7 partly resolved. Six findings followed, all adopted:

1. **Corpus-derived keyword segments.** Replaced by the compiler's `IsKeywordAllowedIdentifier`
   set, read from `SyntaxFacts.cs:3792` and from `ParseQualifiedName` / `ParseIdentifierName`
   (`LanguageParser.cs:403`, `:696`). They are bare `kw()` tokens aliased to `identifier`, and a
   leak check is added (§3.2 item 1, §5.1).
2. **Integer target assumed.** `ParseQualifiedName` reads identifier tokens only, so integers
   are decide-by-probe (§3.2 item 2, §5.1).
3. **The nested-`else` split route not explicit.** The productions are written out (§3.2
   item 4), and the DC witnesses are pinned (§5.2).
4. **Host matrix errors**: line 1084 is Key, and `IndentationColumn` is PageGroup. Replaced by
   generated `tools/alc_facts/property-hosts.tsv` and an explicit context → host table that
   includes the `modify` lookup chains (§2.1).
5. **D3 equivalence undefined.** A recursive normalisation over spans and text is added (§4.2).
6. **Census incomplete.** It now has `check` and `delta` modes, before and after inventories
   with byte-range site IDs, runtime segment checks, disjoint comparison roots and more
   mutations (§5.5).

**Round 3** (Task 1 compiler evidence, 2026-10-05). These are not review findings. They are probe
verdicts, recorded as revision 4 at the top of this spec.
