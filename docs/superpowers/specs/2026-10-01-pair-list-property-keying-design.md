# B4: name-keyed pair-list properties (G9)

**Status:** approved in conversation on 2026-10-01, section by section; this written spec
awaits review.
**Roadmap row:** B4 (`docs/superpowers/plans/2026-09-28-roadmap-remaining-work.md`).
**Resolves:** deferred-work item 11 (G9). Roadmap decision 1, "ML name-keying, narrow", is the
mandate.
**Ships in:** the next major. It changes trees: the 6 `Namespaces` files per Microsoft corpus
get a new node type, and one-pair ML values get a new node.

## 1. Problem

```al
CaptionML = ENU='c';            // today: (property_expression (comparison_expression ...))  WRONG
CaptionML = ENU='a', DAN='b';   // today: (ml_value_list (ml_value_pair) (ml_value_pair))    right
Namespaces = bc = 'urn:x';      // today: comparison_expression                               WRONG
Visible = A = 'b';              // a real comparison, and it must stay one
```

With one pair, `X='s'` is also a complete comparison expression. No value-shape rule can
separate `CaptionML = ENU='c'` from `Visible = A = 'b'`. Only the property **name** can.

**Two of Microsoft's own documented examples parse wrong today:**
- `RequestFilterHeadingML = DAN='Kundeliste';`, from the RequestFilterHeadingML page.
- `Namespaces = bc = 'urn:microsoft-dynamics-bc/xmlports/x100';`, from the Namespaces page.

alc accepts both. The RequestFilterHeadingML example was verified in a report data item, and
it parses as `comparison_expression` today.

**Production impact today is zero.** Every ML and `Namespaces` site in BC.History, DC, BC28.1
and BCApps-29.0 has two or more pairs:
- 4 ML lines in 2 files per corpus;
- 6 `Namespaces` files per Microsoft corpus.

The defect shows up in hand-written code, in the docs examples, and in the config oracle's
strict xfail `test_single_pair_ml_arm_before_endif`
(`tools/config_oracle/tests/test_property_value_conditional.py:153`).

## 2. Ground truth

### 2.1 The compiler keys value grammar by property name

The source is alc 18.0.41.62505, `Microsoft.Dynamics.Nav.CodeAnalysis.dll`, decompiled with
ilspycmd. The DLL's sha256 is in `tools/alc_probe` identity output.

**How the compiler picks a value grammar:**
- `PropertyNameToSyntaxDefinition.GetPropertyValueDefinition(name)` maps a property name to
  a value syntax.
- `ObjectParser`'s `PropertyTypeInfo` tables are keyed by the **upper-cased** name, so the
  lookup is case-insensitive. That is confirmed by probe: `captionml` and `CAPTIONML` compile.

**13 names map to `MultilanguagePropertyValueSyntax`:** AboutTextML, AboutTitleML,
AdditionalSearchTermsML, CaptionML, EntityCaptionML, EntitySetCaptionML,
InstructionalTextML, OptionCaptionML, ProfileDescriptionML, PromotedActionCategoriesML,
RequestFilterHeadingML, SummaryML, ToolTipML.
- All 13 are parsed by `ObjectParser.ParseMultilanguagePropertyValue`, which calls
  `ParseCommaSeparatedIdentifierEqualsStringList`.

**1 more name, `Namespaces`, uses the same list parser:**
`ParseCommaSeparatedIdentifierEqualsStringListPropertyValue`, kind
"CommaSeparatedIdentifierEqualsStringList".

**The list parser's shape:** `ParseSeparatedList(IdentifierToken, CommaToken,
close=SemicolonToken, ParseIdentifierEqualsString)`. That is identifier `=` string,
comma-separated, with no trailing modifiers.

**The compiler keys other value kinds by name too** (89 boolean, 13 label, member reference
and so on). None of those is out of scope by accident: their values are not ambiguous with
an expression in this grammar today (§8).

### 2.2 Microsoft Learn

All 14 property pages exist (`.../developer/properties/devenv-<name>-property`). No
docs page names an ML property outside the compiler's 13.

**Runtime and hosts from the docs:**

| Property | Runtime | Hosts ("Applies to") |
|---|---|---|
| CaptionML | 1.0 | 29: table, table field, page field, field group, page, request page, page label/group/part/system part, page action/separator/group, xml port, report, query, query column/filter, enum value, page custom/system/file upload action, page view, page analysis view, report column, report layout, profile, enum type, permission set |
| ToolTipML | 18.0 at page level | page, page label/field/part/system part/chart part, action area, action, action group, custom/system/file upload action, page analysis view, report column, query column, table field |
| OptionCaptionML | 1.0 | table field, page field, report column |
| InstructionalTextML | 1.0 | page, request page, page field, page group |
| PromotedActionCategoriesML | 1.0 | page |
| AboutTextML, AboutTitleML | 10.0 | custom/file upload action, query, page, page action, action group, page field, page part, page group, request page |
| AdditionalSearchTermsML | 3.0 | page, report |
| EntityCaptionML, EntitySetCaptionML | 6.0 | page, query |
| ProfileDescriptionML | 4.0 | profile |
| RequestFilterHeadingML | 1.0 | xml port table element, report data item |
| SummaryML | 9.0 | report layout |
| Namespaces | 1.0 | xml port |

**Known docs errors.** The compiler is the authority here. Do not "fix" the grammar to match
these pages:
- **InstructionalTextML** shows `;` between entries. alc rejects `ENU='a'; ESP='b';` with
  AL0124 and accepts the comma form.
- **ToolTipML** shows unquoted values (`DAN=text;ENG=text`). alc rejects `DAN=Dette felt;`
  with AL0104 and AL0219.
- **RequestFilterHeadingML** says "semicolons separate entries". Its own example is one pair.

These three are C/SIDE-era text.

**Caption vs CaptionML.** The Caption page documents `Locked`, `Comment` and `MaxLength`
parameters on **Caption**, not on CaptionML.

### 2.3 Compiler probe matrix

All probes ran on alc 18.0.41 with runtime 15.0 (ToolTipML page-level needs 18.0), through
`tools.alc_probe`. Every split verdict matched its flat compile.

| Input | alc | Error | Parser contract |
|---|---|---|---|
| `CaptionML = ENU='c';` | ACCEPT | | `ml_value_list`, 1 pair |
| `CaptionML = ENU='a', DAN='b';` | ACCEPT | | `ml_value_list`, 2 pairs |
| `captionml = …`, `CAPTIONML = …` | ACCEPT | | keyed, any case |
| `CaptionML = ;`, `Namespaces = ;` | ACCEPT | | keyed property, no value |
| `ENU='a', Comment='x'` | ACCEPT | | `Comment` is just a pair |
| `ENU='a', Locked='x'` | REJECT | AL0160 InvalidLanguageId | pair (semantic, not validated) |
| `"ENU"='a'` | REJECT | AL0160 | pair, quoted language |
| `Namespaces = "" = 'urn'` | ACCEPT | | `namespace_pair`, quoted prefix |
| `Namespaces = cac = 'urn'` | ACCEPT | | `namespace_value_list`, 1 pair |
| `ENU='a', Locked = true`, in ML, TextConst and Namespaces | REJECT | AL0104, AL0219 ExpectedStringLiteral | ERROR |
| `TextConst ENU='a', MaxLength = 5` | REJECT | AL0104, AL0219 | ERROR |
| `ENU='a',;` | REJECT | AL0301 ListCannotEndWithSeparator | ERROR |
| `ENU='a' DAN='b'` | REJECT | AL0104 SyntaxError | ERROR |
| `CaptionML = 'abc';` | REJECT | AL0107 IdentifierExpected | ERROR |
| `CaptionML = ENU=Foo;` | REJECT | AL0104, AL0219 | ERROR |
| `InstructionalTextML = ENU='a'; ESP='b';` | REJECT | AL0124 | ERROR, visible, not a clean second property |
| `ToolTipML = DAN=Dette felt;` | REJECT | AL0104, AL0219 | ERROR |
| `TextConst ENU='a'` and `TextConst ENU='a', Comment='x'` | ACCEPT | | unchanged |

**Rule:** a semantic rejection (AL0160) still parses as structure, by "parse structure,
don't validate". A syntactic rejection (AL0104, AL0107, AL0124, AL0219, AL0301) must give an
ERROR on the keyed path. It must never quietly fall back to the comparison reading.

## 3. Mechanism: scanner-keyed names (the CalcFormula route)

### 3.1 Scanner (`src/scanner.c`)

**Two new externals**, added to the `TokenType` enum and to `grammar.js` `externals` in the
same order:
- `ML_PROPERTY_NAME` and `NAMESPACES_PROPERTY_NAME`.
- Grammar side: hidden `_ml_property_name` and `_namespaces_property_name`, each used only
  through `alias(…, $.property_name)`.

**`read_identifier_word`:**
- The buffer grows from 12 to 32 bytes. The longest name is `promotedactioncategoriesml`,
  26 characters.
- It gains `WORD_ML_PROPERTY` and `WORD_NAMESPACES`, compared as whole lowercase words, like
  `calcformula`. A word longer than the buffer stays `WORD_OTHER` (overflow is a miss). The
  identifier is still consumed whole.
- Prefixes therefore never match: `CaptionMLX` and `ToolTipML2` are `WORD_OTHER`.

**Name table:** one `static const char *const` table of the 13 ML names, plus `namespaces`.
Its comment carries the provenance: alc 18.0.41,
`ObjectParser`/`PropertyNameToSyntaxDefinition`, 2026-10-01.

**Emission.** This happens in the existing `=` lookahead branch, the one that already picks
`CALC_FORMULA_PROPERTY_NAME`:
- word is ML and `valid_symbols[ML_PROPERTY_NAME]`: emit `ML_PROPERTY_NAME`;
- word is `namespaces` and `valid_symbols[NAMESPACES_PROPERTY_NAME]`: emit
  `NAMESPACES_PROPERTY_NAME`;
- otherwise, if `valid_symbols[PROPERTY_NAME]`: emit `PROPERTY_NAME`;
- otherwise decline. Never return a token the state did not offer.

**Guards and ordering.** The identifier-dispatch entry guard and the error-recovery guard
include the two new tokens, exactly as `CALC_FORMULA_PROPERTY_NAME` is included today.
Before `mark_end`, consume the identifier. Then skip whitespace and comments, including a
newline before `=`, then test `=`. **No new serialized scanner state.**

**After `tree-sitter generate`:** read `ts_external_scanner_states` in `src/parser.c` and
record which combinations offer the new tokens beside `PROPERTY_NAME`, `BEGIN_KEYWORD` and
`CONTINUE_AS_IDENTIFIER`. Do not argue co-validity from the grammar
(`.claude/rules/scanner.md`).

### 3.2 Grammar (`grammar.js`)

**`property` gains two arms**, next to the CalcFormula arm:

```javascript
seq(field('name', alias($._ml_property_name, $.property_name)), '=',
    optional(field('value', $._ml_property_value)), ';'),
seq(field('name', alias($._namespaces_property_name, $.property_name)), '=',
    optional(field('value', $._namespaces_property_value)), ';'),
```

- `_ml_property_value` is a choice of `ml_value_list` or the ML whole-value conditional
  (§3.3).
- `_namespaces_property_value` is a choice of `namespace_value_list` or its conditional.

**Keyed counterparts of the `;`-in-arm paths.** `_property_with_terminator_in_if`
(`grammar.js:886`) and `_property_whole_value_in_if` (`:918`) each get one keyed variant per
family. They keep the same prec and the same public node,
`preproc_conditional_property_value`. Do not reintroduce the G11 terminator ambiguity
(`grammar.js:895-905`).

**`ml_value_list`:**
- The `optional(seq(',', $.locked_keyword, '=', $.boolean))` tail is **removed**. alc rejects
  it in all three hosts, and 0 production files use it.
- Node name, fields and `prec.right` are unchanged.

**`ml_value_pair`:** unchanged.
- `language:` is already `_plain_name`, which is identifier, quoted identifier, or a value-start
  keyword aliased to identifier (`grammar.js:6218`). So `"ENU"='a'` and `Locked='x'` parse as
  pairs today.
- `value:` stays `string_literal`.

**New nodes** (`Namespaces` only):

```javascript
namespace_value_list: $ => prec.right(seq($.namespace_pair, repeat(seq(',', $.namespace_pair)))),
namespace_pair: $ => seq(field('prefix', $._plain_name),
                         '=', field('uri', $.string_literal)),
```

**Placement:**
- `namespace_value_list` is reached **only** from the Namespaces arms. It is not in
  `_property_value`: offering two identically shaped lists there would recreate the
  ambiguity for unknown names.
- `ml_value_list` **stays** in `_property_value`. An unknown name with two or more pairs keeps
  today's tree, and an unknown name with one pair stays a comparison. That matches the
  compiler, which has no pair grammar for unknown names.

**`TextConst`** (`grammar.js:3787`) keeps its direct `ml_value_list` reference. No token is
involved. It loses only the `Locked` tail, which alc rejects there too.

### 3.3 Whole-value `#if`

**ML family.** A hidden `_ml_property_value_conditional` with the same public alias,
`preproc_conditional_property_value`, and the same `#if`/`#elif`/`#else`/`#endif` arm
structure as `_property_value_conditional` (`grammar.js:956`):
- Every non-empty arm holds `ml_value_list`, or a nested ML conditional, never
  `_property_value`.
- It covers both terminator placements: one `;` after `#endif`, and `;` inside every arm
  (the keyed `_in_if` variant).
- **Namespaces** follows the same pattern.
- The public node and field shape match today's generic conditional, so consumers and the
  F0 traversal policy see no new conditional node.

**Out of scope (B7):** `#if` splits **inside** a list, between pairs
(`ENU='a', #if X DAN='b' #endif`), and comma-leading or comma-trailing branches.
- Roadmap B7 orders the ML separator host after B4.
- B4 records witnesses for these as tracked xfails, or as `debt(B7)` fixture classifications,
  and claims no coverage of them.
- The B4 roadmap row's test list ("list-internal splits") is corrected to point at B7.

## 4. Node contract

```
(property name: (property_name) value: (ml_value_list
   (ml_value_pair language: (identifier|quoted_identifier) value: (string_literal)) ...))
(property name: (property_name) value: (namespace_value_list
   (namespace_pair prefix: (identifier|quoted_identifier) uri: (string_literal)) ...))
(property name: (property_name) value: (preproc_conditional_property_value ...))  ; arms as above
(property name: (property_name))                                                    ; `CaptionML = ;`
```

**Field rules:**
- `property.name` is `property_name` in every arm, so the name node shape is unchanged.
- `property.value` never includes the `;`.
- Each pair has exactly one name-role field and one string-role field.

**`tools/check-field-types.py`** (the hand-maintained contract) gains entries for
`namespace_value_list`, `namespace_pair.prefix` and `namespace_pair.uri`, plus a pin on
`ml_value_pair.language`.

## 5. Verification

### 5.1 Fixtures (`test/corpus/`)

Every fixture carries field labels. For each pair fixture, prove it can fail by renaming a
field to `bogus:`. Check that the suite count moves by exactly the cases added.

**Positive:**
- **All 13 ML names,** one pair and two pairs. Each one-pair case sits in one of that name's
  documented hosts (§2.2). Together they cover profile, report layout, xmlport table
  element, report data item, enum value, permission set, page action, page view, query
  column and report column.
- **Docs examples verbatim:** `RequestFilterHeadingML = DAN='Kundeliste'; // Customer list`
  and `Namespaces = bc = 'urn:microsoft-dynamics-bc/xmlports/x100';`.
- **Name variations:** `captionml`, `CAPTIONML`; a comment between name and `=`; a newline
  before `=`.
- **`Namespaces` forms:** with `""`, one pair, six pairs (production shape).
- **Pair edge cases:** `"ENU"='a'`, `Locked='x'` and `Comment='x'` as pairs; `CaptionML = ;`.

**Unchanged (regression):**
- `Visible = A = 'b';`
- `FooML = A = 'b';`, an unknown `…ML` name, stays a comparison.
- `CaptionMLX = A = 'b';` and `ToolTipML2 = …` stay generic.
- CalcFormula unchanged.
- `Caption = 'x', Locked = true, Comment = 'y', MaxLength = 20;` unchanged.
- `TextConst` with one and with many pairs.
- An unknown name with two pairs stays `ml_value_list` via the generic path.

**Whole-value `#if`:**
- One-pair and many-pair arms.
- `;` after `#endif`, and `;` in every arm.
- `#elif`/`#else`.
- Nested.
- Both families.

**Negative** (each listed in `tools/deliberate-negatives.txt`, each ERROR placed on the
offending line, each with `probe_alc` evidence):
- `Locked = true` in ML, in TextConst and in Namespaces;
- a trailing comma;
- a missing comma;
- a string-only value;
- an identifier value;
- `MaxLength = 5` in TextConst;
- the InstructionalTextML `;` form;
- the ToolTipML unquoted form.

### 5.2 Compiler evidence

- **`tools/alc_probe/cases/pair-list-keying/`:** the §2.3 matrix as committed cases with
  `// expect:` and `// source:` headers. `--check` must pass.
- **`tools/config_oracle/probe_alc.py`:** raw cases for every negative fixture. `--check`
  must pass.

### 5.3 Oracle and traversal

- **The xfail becomes a pass.** `test_single_pair_ml_arm_before_endif` now passes, so remove
  its `xfail(strict=True)`.
- **`tools/config_oracle/contracts.py`:** register `namespace_value_list` and
  `namespace_pair` so they can be lowered or classified. The quick-tier census stays clean.
- **`traversal/policy.json`:** add entries plus witnesses for the two new node types, with
  their class per spec 2026-10-01 §6.1. Step 5f stays clean. The F0 suites (`pytest
  tests/traversal`, `npm test`, `cargo test --features traversal`) pass.
- **Full tier** over the four corpora: exit 0, 0 discrepancies. Any `fixture-classes.tsv`
  entry that goes stale is removed.

### 5.4 Incremental parsing

Add a pytest that edits a source and compares the incremental tree with a fresh parse, byte
for byte. The edits:
- renaming CaptionML ↔ Namespaces ↔ Visible ↔ CaptionMLX;
- a case-only rename;
- `=` ↔ `:=`;
- inserting or removing a comment between the name and `=`;
- one pair ↔ two pairs;
- wrapping the value in `#if … #endif`;
- an edit just past the name token's marked end.

### 5.5 Gates

| Gate | Pass condition |
|---|---|
| tree-harness | Fresh baseline `baseline-b4` before any change. Changes are allowed **only** in the 6 BC.History `Namespaces` files, with every hunk read |
| `validate-grammar.sh`, quick and `--full` | Pass, BC.History 0 errors |
| has_error sweep, four corpora and corpus fixtures | No new error files; negatives visible, never hidden |
| `qc run` | No new cluster |
| Two-shape census (`snip.py --census`, BC.History) | 0 flagged |
| `metrics.sh --vs <base>` | STATE_COUNT growth ≤ 2%, no new declared conflicts |
| `tools.perf ab --corpus dc`, 24 rounds | Within resolution |
| WASM | Rebuilt and fresh |
| Commit | Grammar, parser.c, grammar.json and node-types.json committed together, plus scanner.c, and every message carries the BC.History count |

## 6. Migration and docs

**CHANGELOG `[Unreleased]`, breaking:**
- `Namespaces` values parse as `namespace_value_list`/`namespace_pair` (`prefix:`, `uri:`),
  not `ml_value_list`/`language:`.
- One-pair values of the 13 ML properties parse as `ml_value_list`, not
  `comparison_expression`.
- `, Locked = <boolean>` inside an ML list or a TextConst is now an ERROR, as alc reports
  AL0219.

**CLAUDE.md "Property Handling":** the CalcFormula paragraph becomes a short section on
name-keyed properties, which now cover three families. The "do not generalise this" rule is
replaced with:

> Key a name only when the compiler parses that name's value with its own grammar *and*
> that grammar cannot be told apart from an expression in ours. The keyed list comes from
> the compiler's tables, never from a naming pattern such as "ends in ML".

Update the scanner token table too.

**`.claude/rules/scanner.md`:** the token table, the identifier-dispatch section (buffer
size, longest word), and the `valid_symbols` fallback rule.

**`queries/highlights.scm`:** `namespace_pair` `prefix:` and `uri:` captures. Keep the ML
captures.

**`docs/deferred-work.md`:** mark item 11 RESOLVED. Correct its "every name ending in `ML`"
suggestion.

**Roadmap B4 row:** add a done note, and move "list-internal splits" to B7.

## 7. Risks

| Risk | Mitigation |
|---|---|
| A property host offers only `PROPERTY_NAME`, so a keyed name silently takes the generic path | Read `ts_external_scanner_states` after generation (§3.1). The fixtures cover every documented host class (§5.1). The census of hosts is part of the review |
| The new arms fork GLR on ordinary properties | tree-harness 0 changes outside `Namespaces`; `perf ab`; check `metrics.sh` for new conflicts |
| Incremental reuse across a name edit | §5.4 |
| The compiler table changes in a later alc | The provenance comment names the version. Re-check with the `alc_probe` cases on a compiler upgrade |
| Removing the `Locked` tail breaks a fixture that asserted it | Any such fixture asserted input that alc rejects. Rewrite it as a negative, with `probe_alc` evidence |

## 8. Not in scope

- **Keying the compiler's other value kinds:** boolean, label, member reference and so on.
  None of them is ambiguous with an expression today. If one becomes ambiguous, it gets its
  own roadmap row, using the same mechanism.
- **Validating language codes, URIs or hosts:** linter work.
- **`#if` inside a pair list:** roadmap B7.
