# Property families and the V2 grammar design notes

Carried out of `CLAUDE.md` on 2026-10-21 so that the always-loaded file holds rules and
pointers only. Everything below is the design record of the V2 architecture, the five
name-keyed property families (B4, B5, B5b), property value runs (B11), strict conditional
lists (B7b-1) and statement terminators (B7b-3), with the measurements each decision rested
on. The rule each paragraph defends is restated in one line in `CLAUDE.md`; the comment at the
rule in `grammar.js` is the other home. Counts quoted here are the ones measured at the time
named; re-measure before quoting.

## Key design principles (V2 architecture)

- **Parse structure, don't validate** — Accept any `Name = Value ;` as a property. Semantic
  validation belongs in linters/LSP servers, not the parser.
- **Scanner-based property disambiguation** — The `PROPERTY_NAME` scanner token distinguishes
  `identifier =` (property) from `identifier :` (variable) via 1-char lookahead.
- **Generic property rule** — ONE `property` rule handles all simple properties (vs V1's 291
  individual rules).
- **Generic preprocessor** — ONE `preproc_conditional` rule + ~12 dedicated split-construct
  rules (vs V1's 63).
- **Named keyword nodes** — 154 keywords exposed as named nodes for query matching (152 grammar
  rules + the external `begin_keyword`/`end_keyword`), all with a uniform shape: one anonymous
  child typed as the canonical lowercase spelling (`.claude/rules/contextual-keywords.md`,
  `docs/keyword-shape-audit.md`).
- **Stateful scanner** — a `uint32_t` depth counter tracks `#if`/`#endif` nesting (it was a
  `uint8_t` until 4.0.0 and wrapped at 256); `begin`/`end` are named at every depth, and the
  depth counter decides only whether a `PREPROC_SPLIT_*` token gets first refusal
  (`docs/scanner-design-notes.md`).
- **Reserved-word sets, three contextual sets** — `reserved: { global: [], implementation_names:
  [...], relation_target_names: [...], code_names: [...] }` (tree-sitter ≥ 0.25). `global` is
  empty on purpose; `implementation_names` reserves `true`/`false` inside
  `implementation_value`'s two names, which is what lets `prec.dynamic` favour the mapping
  reading of `A = B` without stealing `Visible = HideActions = false;`. Two rules the docs do
  not state, both measured while fixing issue #20: an entry must be a rule **symbol**
  (`$._true_token`), not a fresh `kw()`; and a parse state takes the largest set among items
  whose **next step is `identifier` itself**, so the set must sit on a rule that names
  `$.identifier` directly (`_implementation_name`) — wrapping a reference to
  `_identifier_or_quoted` reserves nothing. `relation_target_names` (B5) reserves `if`, `else`
  and `where` on `_qualified_name_segment`, which alc rejects as relation-target segments, at 0
  extra states. `code_names` (B6) reserves `and`, `or`, `xor`, `div`, `mod`, `in` and `not` in
  code (alc: AL0104 at a statement start, AL0224 read in an expression; `is`/`as` stay names,
  declarations are unaffected) on `_expression`, `call_expression`'s `function` choice and
  `_expression_statement`; because a first option member shares the generic property value's
  first state, `option_member` takes the seven words back as identifiers (alc accepts them
  there), STATE_COUNT +2. Audit: `docs/b6-audit.md`.
- **Single-read identifier dispatch** — all eleven identifier-initial scanner tokens are
  decided in one scan over one read of the word (`.claude/rules/scanner.md`).
- **A statement's `;` belongs to its host route, not to the statement** — the `_statement`
  wrapper (`seq($._statement_inner, optional(';'))`), `case_branch` and the three split case
  wrappers, or the guard sequence of `_preproc_guard_block` own it. Since B7b-3
  `call_statement` is only "a bare name in statement position" (`field('function', identifier
  | quoted_identifier | Order/Table)`, reached through `_expression_statement`; its B6
  `prec(-1)` was removed in B7b-2 Phase C so a receiver group can start a statement, the
  operand reading dying at `end`), so `Bar;`, `Bar` before `end`/`else`/`until` and `Order;`
  share one shape, and `preproc_split_call_statement` ends at `)`. `empty_statement` is the one
  self-terminating form left: it IS a `;`. Giving a statement rule its own `;` back makes that
  `;` unreachable from an `#if` arm (the B7b-3 SILENT cells) and gives a bare name two shapes
  (deferred item 40).

## Property handling

Properties use a generic rule — no per-property validation:

```javascript
property: $ => seq(
  field('name', $.property_name),   // PROPERTY_NAME scanner token
  '=',
  field('value', $._property_value),
  ';'
),
```

**Complex properties** (~36 rules) have unique syntax and remain as individual rules:
- CalcFormula, TableRelation, Permissions, AccessByPermission
- DataItemLink, RunPageLink, SubPageLink, ColumnFilter
- SourceTableView (and related view properties)
- Caption/ToolTip (with Locked/Comment sub-fields)
- ML properties (multilingual key=value lists)
- List properties (comma-separated identifiers)
- DecimalPlaces, OrderBy, Implementation

**Adding new property support:** Most properties work automatically via the generic rule. Only
add a dedicated rule if the property has syntax beyond `Name = Expression ;`.

### Name-keyed properties: five families, and the scanner keys them

`PROPERTY_NAME`'s lookahead reads the word once and emits a keyed token instead, falling back
to `PROPERTY_NAME` where the parse state does not offer it (order: CalcFormula → ML →
Namespaces → TableRelation → Link → generic → decline). `property` has one arm per family,
whose value has that family's grammar only.

- **`CalcFormula`** → `CALC_FORMULA_PROPERTY_NAME`. Its value
  (`sum/count/exist/min/max/average/lookup(Table.Field [where(...)])`) is also a complete call
  expression when there is no `where()`, and only the name separates `CalcFormula = Count(X)`
  from `DataCaptionExpression = Caption(Rec)`. Before issue #21 the GLR tiebreak gave 22
  no-`where` aggregates in BC.History to `property_expression`.
- **The compiler's 13 ML names** (`CaptionML`, `ToolTipML`, `OptionCaptionML`,
  `PromotedActionCategoriesML`, …; the list is in `src/scanner.c`) → `ML_PROPERTY_NAME`, value
  `ml_value_list`. A one-pair `ENU='x'` is also a complete comparison, so before B4 every
  one-pair ML value was a `comparison_expression` (G9).
- **`Namespaces`** → `NAMESPACES_PROPERTY_NAME`, value `namespace_value_list` /
  `namespace_pair` (`prefix:`, `uri:`).
- **`TableRelation`** → `TABLE_RELATION_PROPERTY_NAME`, value `table_relation_value` (B5). The
  compiler reaches `ParseTableRelationPropertyValue` through that one name and reads the target
  with `ParseQualifiedName`, one qualified name, so the target is `target: (qualified_name)`
  and never a member expression. Before B5 every property's dotted value was offered as a
  relation (14,011 production sites), and G10 (`#if X and B #endif` after a dotted value)
  ERRORed. Other properties' dotted values are expressions.
- **The link family** (`SubPageLink`, `RunPageLink`, `LinkFields`, `DataItemTableFilter`,
  `ColumnFilter`, `DataItemLink`) → `LINK_PROPERTY_NAME`, value `link_value_list` (B5b). The
  compiler has three value grammars behind these names (TableFilter, ReportDataItemLink,
  QueryDataItemLink); ours is one neutral union, so the three delegates deliberately
  over-accept (`DataItemLink = A = const(1)`, `RunPageLink = A = B.C` parse clean though alc
  rejects them, a validation matter). Link syntax appears only under these six names:
  `Visible = Flag = Rec.OtherFlag;` and `Enabled = Status = const(Open);` are ordinary
  expressions, and a `const` argument may be signed, decimal or `L`-suffixed. The keyed value
  is optional: an empty `DataItemLink` value is rejected only semantically (AL0171), so the
  parser accepts it; the same shared arm structurally over-accepts `RunPageLink = ;`, which
  alc rejects as syntax (AL0104/AL0107).

Each keyed value may also be a whole-value `#if` whose arms are that family's list again, with
the `;` after `#endif` or inside every arm (`preproc_conditional_property_value`). The rule for
adding a family:

> Key a name only when the compiler parses that name's value with its own grammar *and* that
> grammar cannot be told apart from an expression in ours. The keyed list comes from the
> compiler's tables, never from a naming pattern such as "ends in ML".

`FooML` and `CaptionMLX` stay generic, and fixtures pin that.

### Property value runs (B11)

A value may be several consecutive `#if ... #endif` groups at one value site (the property, or
an arm). Routing (spec `docs/superpowers/specs/2026-10-05-property-value-runs-design.md` 3.1),
in order: (1) at most one core-bearing group, so that group is the core and empty groups
around it are decorations; (2) `;` inside every arm:
`value: (preproc_conditional_property_value_sequence ...)`; (3) `;` after in a list family
(link, Implementation, `OptionMembers`, and Permissions, which behaves as one): the family's
element conditionals; (4) `;` after in CalcFormula, TableRelation, ML or Namespaces: a
sequence; (5) anything else, a generic `;`-after run, stays a visible ERROR (B13). The
sequence's only field is `value` (multiple, each a `preproc_conditional_property_value`);
`property.value` stays single (`tools/check-field-types.py`). Directive-only empty groups are
unfielded decorations, never wrapped, and carry no `value:`, with three suffix exceptions (an
empty group after a plain value, before the property's `;`, spec 3.2/4.2 execution
amendment): in link (`listValue`), Implementation and Permissions it stays the list's element
conditional, and in TableRelation it stays inside `table_relation_value` (all base trees);
`OptionMembers = A,B #if X #endif ;` makes it a property decoration (base ERROR). Rules come
from the generators `valueRunRules`, `afterGroupRules`, `afterSequenceRules` and
`listOpenerRules`; read their comments before touching one. Boundaries: a sequence is a
one-reading construct, so a property boundary that depends on the configuration is refused by
the oracle (B12, item 36); this includes continuation absorption, where a conditional block
after a non-terminated `;`-inside group whose arm also parses as a property
(`Caption = #if X 'a'; #endif #if Y Editable = false; #endif`) is read as part of the value,
wrong where the earlier group already ended the property (spec 3.4 amendment 7); and fragment
runs are B13 (item 37, gap file `test/corpus/property_value_run_b13_gap_test.txt`).
Precedence decisions and their witnesses: `docs/b11-precedence-audit.md`.

### Strict conditional lists (B7b-1)

A homogeneous delimited list in which an `#if` group may stand at any separator (implements,
field lists, sorting / order-by inner lists, move elements, array dimensions, attribute
arguments, var names) is generated by two helpers in `grammar.js`:
`...strictConditionalList('<family>', $ => <atom>, '<sep>'[, groupDynamic])` spread into
`rules` (hidden seam helpers `_<family>_e/_t/_b/_r` plus the visible group
`preproc_conditional_<family>`), and `...strictListBody($, '<family>', '<sep>')` written into
the host in place of `item, repeat(seq(sep, item))`. The body is inlined, never a hidden
`_F_list` rule, because the B7a census keys a separator by its rule path and a hidden rule
would orphan the frozen manifest's cell ids. Field the atom as the host fields its items (the
field then reaches the group too, `multiple`, `required: false`); unfielded hosts stay
unfielded. The oracle side is the family-schema registry `FAMILIES` in
`tools/config_oracle/lowering/conditional_lists.py` (region adapter, item kinds, separator,
alc cardinality; split-tree validation and per-configuration `item (sep item)*`). Adding a
host: the "Host Conversion Procedure" in
`docs/superpowers/plans/2026-10-07-b7b-1-strict-conditional-lists.md` (hand-written RED
fixture, the two helpers, field invariants in `tools/check-field-types.py`,
`traversal/policy.json`, a `FAMILIES` entry and the oracle's `contracts.py`, four-corpus
`python -m tools.perf parity` 0), the three arm-separator rows per family in
`tools/b7_audit/registry.tsv` (keys `occ:_<family>_b:0.0`, `occ:_<family>_r:1.0.0`,
`occ:_<family>_r:2.0`, each with `equiv occ:<host>:<path>`, no new cells), the family's
`GROUP` entry in `tools/b7_audit/strict_list_assertions.py`, plus a manifest or matrix re-run
(`python -m tools.b7_audit`). One scanner change came with it: a variable attribute's `[`
(`VAR_ATTRIBUTE_OPEN`) is now decided by `var_name_list_follows` in `src/scanner.c`, which
accepts a conditional name list ending at `:` (`.claude/rules/scanner.md`). A group whose arms
supply no separator still parses (no per-arm separator tracking): those
all-configurations-invalid forms are classified over-acceptances, `docs/deferred-work.md`
item 44.

### Statement terminators, case separators, the move header (B7b-3)

Spec `docs/superpowers/specs/2026-10-08-b7b-3-statement-terminators-design.md` (rev 3 plus
"Rev 3 execution amendments"). Three places where a `;` that alc lets come from an `#if` group
or be absent was bound to a fixed position. (1) Calls: see the ownership principle above;
`call_statement` carried `prec(-1)` (B6's priority, moved down from `_expression_statement`)
until B7b-2 Phase C removed it. (2) Case branches: a `preproc_conditional_case` arm holds
`case_branch`, `empty_statement` (the preceding branch's `;` in that configuration) and nested
`preproc_conditional_case` (`_case_group_item`); a directive-only group between a branch body
and the branch's own `;` is a DECORATION inside the branch, built only through
`caseEmptyGroup($)` (`_case_empty_group` aliased to `preproc_conditional_case`, so a query
cannot tell it from an ordinary group), in four hosts: `case_branch`,
`preproc_split_case_branch`, `preproc_split_case_extended`, `preproc_split_case_end_branch`.
An empty group before an `asserterror`'s `;` is the asserterror's BODY, not a decoration
(amendment 5). (3) Move header: `moveArgs` in `grammar.js` has three routes, disjoint at their
first tokens: route 1 `T ; elements` is B7b-1's, unchanged; route 2 `T #if` and route 3 `#if`
use `...strictConditionalList('move_args', ..., choice(';', ','))` and the visible group
`preproc_conditional_move_args`; only route 2's first raw name is fielded (`target`, now
`required: false`), every other name on routes 2-3 is unfielded because its role can depend on
the configuration (spec 5.3). The oracle side is listed in `tools/config_oracle/README.md`.
Gates added: the structural production delta `python -m tools.perf delta` (E1/E2/E3 edit
classes, `tools/perf/delta-reviewed.tsv` for recovery-only files), `tools/perf/ab_accept.py`,
scoped manifests (`# families:` header; `manifest --check --manifest
tools/b7_audit/b7b3-manifest.tsv`), census key aliases (`tools/b7_audit/key-aliases.tsv`: a
separator key whose rule path moved maps to its live key, frozen cell ids unchanged). Known
debt: deferred-work items 43 (orphan `else` reads as a call), 44 (case over-acceptances) and
47-50.

## Preprocessor handling

**Line-level directives** are `extras` (reachable anywhere): `pragma`, `preproc_region`,
`preproc_endregion`, `preproc_define`, `preproc_undef`. They never touch the scanner's
`#if`/`#endif` depth counter. The AL compiler only accepts `#define`/`#undef` before the first
real token of a file — that positional rule is a linter's job, not the parser's. See
`docs/preproc-define-undef.md`.

**Generic conditionals** (most cases):
```javascript
preproc_conditional: $ => seq($.preproc_if, repeat($._any_content), ...)
```

**Dedicated split-construct rules** (`preproc_split_*` in `grammar.js`, for cross-branch fragments):
- `preproc_split_procedure` — procedure header variants in `#if`/`#else`
- `preproc_split_if_statement` — if-then header varies across branches
- `preproc_split_if_then_begin` — `begin` inside `#if`, `end` in second `#if`
- `preproc_fragmented_else_tail` — end-else-begin fragmented across `#if` blocks
- `preproc_split_declaration` — object declaration split across branches
- And others for case statements, fields, datasets, etc.
