# B11: property values made of a run of `#if` groups

**Status:** revision 1, 2026-10-05. Approved in conversation section by section (§3 tree
shapes, §4 mechanism, §5 verification); awaiting written-spec review.
**Roadmap row:** B11, new (`docs/superpowers/plans/2026-09-28-roadmap-remaining-work.md`).
Absorbs deferred-work items 33 and 35, and the ML empty-prefix split recorded under item 33
during B8.
**Ships in:** the next major release. Adds one node type,
`preproc_conditional_property_value_sequence`. No production tree is expected to change
(§2.3). That expectation is a measurement target, proven over all four corpora, not a
conclusion.

## 1. Problem

A property value may be written as several consecutive `#if … #endif` groups, and alc
accepts every such shape (§2.1). The grammar handles exactly one whole-value group (G6, B4,
B5, B5b, B8). Any other run of groups is silently wrong or an ERROR:

```al
CaptionML =                  // silent split: property CaptionML (empty value), property ENU
#if X
#endif
    ENU='a';

Caption =                    // silent wrong shape: value is an option_member_list
#if X
#endif
    'a';

SubPageLink =                // ERROR (item 35's "has_error False" is stale at HEAD)
#if X
    "No." = field("No.");
#endif
#if not X
    "No." = field(Name);
#endif
```

## 2. Ground truth

### 2.1 Compiler evidence (alc 18.0.41, scratch probes, 2026-10-05)

8 families × 3 shapes, each compiled split and flat for X defined and undefined: **24 cases,
96 compiles, all ACCEPT**.
- **Families:** generic `Caption`, generic `Visible`, `CaptionML`, `Namespaces`,
  `TableRelation`, `CalcFormula`, `Implementation`, `SubPageLink`.
- **Shapes:**
  - empty prefix: `N =` / `#if X` / `#endif` / `v;`;
  - run, `;` inside the arms: `#if X a; #endif #if not X b; #endif`;
  - run, `;` after: `#if X a #endif #if not X b #endif ;`.

They are committed as the B11 evidence in Task 1 (§5.1).

### 2.2 Measured today (live parses at `bf72a2d`)

| family | empty prefix | run, `;` inside | run, `;` after |
|---|---|---|---|
| generic (`Caption`, `Visible`) | clean, value `option_member_list` (wrong) | ERROR | ERROR |
| `CaptionML` | clean, **two properties** | ERROR | ERROR |
| `Namespaces` | clean, **two properties** | ERROR | ERROR |
| `Implementation` | clean, **two properties** | ERROR | clean, list of two element conditionals (right) |
| `TableRelation` | ERROR | ERROR | ERROR |
| `CalcFormula` | clean, unfielded prefix (right, B8) | ERROR | ERROR |
| `SubPageLink` | clean, element conditional in the list (right) | ERROR | clean, list of two element conditionals (right) |
| `OptionMembers` | clean, element conditional in the list (right) | ERROR | ERROR |

### 2.3 Production census

A text scan over BC.History, DC, BC28.1 and BCApps-29.0 for `=` at the end of a line followed by
an `#if` line finds **9 sites, all `Permissions`** (`permissions_property`, a separate rule,
out of scope). No production property value starts with an `#if` group. The fix therefore
cannot change a production tree through the shapes it targets. The byte-identical gates (§5.4)
prove that it changes none through any other path.

## 3. Tree shapes (node contract)

**Terms.** The *run* is the maximal sequence of consecutive `#if … #endif` groups between `=`
and the end of the property. A group is *empty* when every arm is absent, and
*value-bearing* when at least one arm holds a value.

| shape | tree |
|---|---|
| plain value, or one value-bearing group | **unchanged** |
| empty groups around a plain value or one value-bearing group | each empty group is an unfielded `preproc_conditional_property_value` child of `property`, before or after `value:`. This is B8's form, extended to every non-list family. |
| 2+ value-bearing groups | `value: (preproc_conditional_property_value_sequence …)` |

**Inside a sequence:**
- each value-bearing group is `value: (preproc_conditional_property_value …)`;
- an empty group between two value-bearing groups is an unfielded child;
- the sequence spans from its first value-bearing group to its last;
- empty groups before the first value-bearing group and after the last one are property-level
  children, as in the single-group case;
- the property's `;` stays outside the sequence.

**Why a new node type.** The alternatives fail silently for a consumer that does not know
about them; a new type fails loudly, and the project's gates force every consumer surface to
classify it (§5.5).
- **Sibling `value:` fields under `property`** would revert the G5 invariant
  `property.value multiple=False` (`tools/check-field-types.py`). A consumer calling
  `child_by_field_name('value')` would silently read only the first group.
- **Several groups inside one `preproc_conditional_property_value`** would break the
  one-group-per-node assumption of the oracle's `split_arms` and of the traversal helper,
  again silently.

**Field pins.**
- `preproc_conditional_property_value_sequence.value`: `multiple=True`, types
  `{preproc_conditional_property_value}`, no anonymous members.
- `property.value`: stays `multiple=False`.

**List families** (link, `Implementation`, `OptionMembers`): their `;`-after run keeps today's
list-element reading, which is the flat-correct reading. A list-family sequence exists only for
the `;`-inside form, which ERRORs today.

**CalcFormula:** arms keep the formula kinds (`aggregate_formula` / `lookup_formula`), so its
sequence holds formula groups only. This keeps the issue #21 guarantee.

## 4. Mechanism (`grammar.js`)

### 4.1 One helper, six families

A helper, generalising `keyedValueConditional`, generates the run rules from a family's value
rule and arm content:
- generic `_property_value`;
- `_ml_property_value`;
- `_namespaces_property_value`;
- `_table_relation_property_value`;
- `_link_property_value`;
- `_calc_formula_value`.

The six families cannot drift apart. The empty group is ONE shared rule,
`_empty_value_conditional` (`#if`, `#elif`…, `#else`?, `#endif`, no arm content), aliased to
`preproc_conditional_property_value`. B8's `_calc_formula_empty_conditional` becomes this rule.

**Witness.** A value-bearing group rule requires at least one present arm, recursively
(B5b's termination witness). Whether today's all-empty whole value (`N = #if X #endif ;`) keeps
parsing is decided per family by alc probe. Where alc rejects it as syntax, it becomes an
ERROR negative. Where the rejection is only semantic, as with an empty `DataItemLink`
(AL0171), it keeps parsing as a value of the empty group.

### 4.2 `;` after the last `#endif`

The run continues until the `;`. Arms may also carry their own `;` (mixed placement, as today).
This form is unambiguous: the property's own `;` closes it. Grammar:
`prefix* (plain | group | sequence) suffix* ';'`, where `sequence = group (empty* group)+`.

### 4.3 `;` inside the arms

Here a following `#if` group is either the value's continuation or ordinary content after the
property. A group is **complete** when it has `#else` and every arm is present, terminated and
(if nested) complete. Every configuration has then already emitted its `;`. Otherwise it is
**incomplete**.

- **After a complete group the property ends.** A following `#if` block is ordinary content.
  This is deterministic: the run rule offers no continuation after a complete group.
- **After an incomplete group the next value-bearing group continues the value**, even when its
  arms would also parse as properties (`ENU='b';`, `A = field(C);`, `Visible = true;`).
  - **That is the compiler's reading.** In a configuration where the earlier groups supplied
    nothing, alc sees `Caption = Visible = true;`.
  - **The other reading is wrong.** Ending the property and starting a conditional property
    block leaves the property with no value in those configurations, which is exactly
    today's ML, Namespaces and Implementation splits.
  - **How it is enforced:** a declared conflict and `prec.dynamic` in the run's favour.
- **Every non-last value-bearing group of the run is incomplete.** The last may be either.
- **The property ends at the last value-bearing group.** Empty groups after it are ordinary
  content.
- **The termination witness:** a run holds at least one present, terminated arm.

**Residue: complementary conditions.** `#if X a; #endif #if not X b; #endif` is complete
semantically and incomplete structurally, so a third group after it is read as a continuation.
- **Why the grammar leaves it:** telling the two apart requires evaluating conditions, which
  this project leaves to the config oracle ("parse structure, don't validate").
- **The oracle catches it:** the configuration that activates the third group lowers to two
  values, a discrepancy.
- **It is recorded with evidence, not as unknown:**
  - an alc probe;
  - a fixture pinning the tree;
  - an oracle-classified record;
  - a deferred-work entry stating that tracking condition text in the scanner was considered
    and declined (new serialized state, 0 production sites).

### 4.4 Hosts

| placement | rule | families |
|---|---|---|
| `;` after | each family's arm of `property` | all six |
| `;` inside | `_property_with_terminator_in_if` | all six |
| `;` inside | `_property_whole_value_in_if` (action and assembly hosts, G11 parity) | generic, ML |

alc rejects the other families at the action and assembly hosts (AL0124).

### 4.5 Cost

STATE_COUNT rises: six families × two placements, plus the complete/incomplete split. It is
measured and reported against the +2% guideline, not designed to a cap. Parse speed is
measured with `tools.perf ab` over DC.

## 5. Verification

### 5.1 Compiler evidence (`tools/alc_probe/cases/value-runs/`)

Committed before any grammar change, with `--check` clean:
- the 24 probes of §2.1, with real `// expect:` / `// source:` headers;
- `#elif` and `#else` runs, a three-group run, and empty groups between and after
  value-bearing groups;
- the incomplete-then-property-shaped continuation
  (`Caption = #if X 'a'; #endif #if not X Visible = true; #endif`), with its flat texts;
- the complementary-condition residue (`#if X a; #endif #if not X b; #endif #if Y P = v;
  #endif`), recording each configuration's verdict;
- the all-empty whole value per family (§4.1 witness);
- the action and assembly hosts for generic and ML values.

### 5.2 Fixtures

**`test/corpus/property_value_run_test.txt`.** The expectations are generated from
`tree-sitter parse` output, so every field is labelled. It holds:
- every §5.1 shape × family;
- the complete-then-property block (the property ends);
- the residue;
- the list-family `;`-after cases (unchanged list-element reading).

Each tree is checked by hand against the flat tree of every configuration. A `bogus:` field
rename must fail the file, and the suite total must move by exactly the number of cases added.

**Negatives.** Shapes alc rejects as syntax (§4.1) are listed in
`tools/deliberate-negatives.txt`.

### 5.3 Oracle

- **`preproc_conditional_property_value_sequence`** is registered as an assembler:
  - each `value:` child is lowered through `property_value_select`;
  - empty groups are accounted as directives;
  - exactly one value per configuration (none, or two or more, is a discrepancy).
- **Hosts:**
  - `property:value` for the sequence;
  - `preproc_conditional_property_value_sequence:value` and `:<children>` for its groups;
  - `property:<children>` (optional-slot) for prefix and suffix empty groups.
- **Classification:** every invalid-config record (an incomplete run whose configuration has no
  value) is classified in `fixture-classes.tsv` with alc evidence. So is the residue's
  discrepancy.
- **Tiers:** quick tier clean; full tier over the four corpora clean.

### 5.4 Gates

- `./tools/tree-harness.sh verify` byte-identical over BC.History (fresh `baseline-b11`);
- `relation_census` zero-delta over the four corpora;
- `has_error_sweep` over the four corpora and the corpus fixtures;
- `tree-sitter test`;
- `validate-grammar.sh --full`;
- `qc` (a new cluster must be justified, not blanket-accepted);
- traversal census;
- `tools/check-field-types.py` (Step 5b);
- an incremental-parse pytest that toggles a run between one and two groups, between complete
  and incomplete, and between `;` inside and `;` after;
- `check-wasm-fresh` after a WASM rebuild in its own commit.

### 5.5 Consumer surfaces

- **`traversal/policy.json`:** classifies the new node as a conditional container, through
  `tools/traversal_census.py`.
- **`queries/`:** folds, textobjects and highlights, wherever `preproc_conditional_property_value`
  appears, are checked and extended for the sequence.
- **Owned-IR consumers:** the CHANGELOG Changed entry names the new node type, the shapes that
  produce it, and that no previously clean tree changes.

## 6. Docs

- CHANGELOG: Changed entry with a migration note.
- `docs/deferred-work.md`:
  - item 33 RESOLVED;
  - item 35 RESOLVED, its stale `has_error` claim corrected;
  - a new entry for the §4.3 residue, with evidence.
- Roadmap: row B11 added, marked done when it lands.
- CLAUDE.md / `.claude/rules`: the run mechanism, wherever whole-value conditionals are
  described.

## 7. Risks

- **A following conditional property block absorbed into a run.** It happens only after an
  incomplete group (§4.3), where it is the compiler's reading. Measured by the zero-delta
  gates; production has no such site (§2.3).
- **GLR cost of the declared conflicts.** Measured by `tools.perf ab`.
- **The residue.** Caught by the oracle; recorded with evidence.

## 8. Not in scope

- `Permissions` (`permissions_property`): its own list-internal `#if` rule; production sites
  exist and parse correctly.
- Values continued across `#if` with an operator (`preproc_conditional_expression_tail`, B3).
- Condition evaluation in the scanner (§4.3).

## 9. Review record

(empty; filled by the review rounds)
