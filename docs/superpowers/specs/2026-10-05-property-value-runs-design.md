# B11: property values made of a run of `#if` groups

**Status:** revision 2, 2026-10-05. Revision 1 was approved in conversation section by section,
then reviewed by gpt-6.1-sol: 2 blockers, 8 majors, 1 minor. All were verified against the
code and live parses before they were adopted (§9, round 1). This revision awaits review.
**Roadmap row:** B11, new (`docs/superpowers/plans/2026-09-28-roadmap-remaining-work.md`).
Absorbs deferred-work items 33 and 35, and the ML empty-prefix split recorded under item 33
during B8.
**Ships in:** the next major release. Adds one node type,
`preproc_conditional_property_value_sequence`. **Previously correct trees do not change.** The
intended changes are named in §3.4. That is a measurement target, proven over all four corpora
(§5.4), not a conclusion.

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

SubPageLink =                // silent split: SubPageLink, then a property A (item 35)
#if X
    A = field(B);
#endif
#if not X
    A = field(C);
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

They are committed as the B11 evidence in the first task (§5.1). alc does not parse inactive
branches (`docs/deferred-work.md`, the four-way probe rule). So a property's text, and where it
ends, is a function of the configuration.

### 2.2 Measured today (live parses at `bf72a2d`)

| family | empty prefix | run, `;` inside | run, `;` after |
|---|---|---|---|
| generic (`Caption`, `Visible`) | clean, value `option_member_list` (wrong) | ERROR | ERROR |
| `CaptionML` | clean, **two properties** | ERROR | ERROR |
| `Namespaces` | clean, **two properties** | ERROR | ERROR |
| `Implementation` | clean, **two properties** | ERROR | clean, list of two element conditionals |
| `TableRelation` | ERROR | ERROR | ERROR |
| `CalcFormula` | clean, unfielded prefix (right, B8) | ERROR | ERROR |
| `SubPageLink` | clean, element conditional in the list | unquoted `A = field(..)`: clean, **two properties** (item 35); quoted `"No."`: ERROR | clean, list of two element conditionals |
| `OptionMembers` | clean, element conditional in the list | ERROR | ERROR |

A single whole-value group is one `preproc_conditional_property_value` in every family. That
includes `OptionMembers` (`#if X A,B #else C #endif;` gives arms `option_member_list` and
`identifier`) and the link family (B5b).

### 2.3 Production census (discovery, not proof)

A text scan over BC.History, DC, BC28.1 and BCApps-29.0 for `=` at the end of a line followed by
an `#if` line finds **9 sites, all `Permissions`** (`permissions_property`, out of scope). The
scan misses comments after `=` and intervening comment lines. The plan's first task repeats it
with trivia skipped, over parsed trees: every `property` whose value position holds or is
preceded by a `#if` group. It also counts empty groups after ordinary values. The proof that no
previously correct tree changes is the full-tree zero-delta gate over all four corpora (§5.4),
not this scan.

## 3. Tree contract

**Terms.**
- The *run* is the maximal sequence of consecutive `#if … #endif` groups at a value site.
- A group is *empty* when, recursively, no arm holds a value: every arm is absent, or holds
  only empty groups.
- A group is *value-bearing* otherwise.
- A *value site* is the value position of `property`, and the value position of every
  whole-value arm.

### 3.1 Shapes

| shape at a value site | tree |
|---|---|
| plain value, or one value-bearing group | unchanged |
| empty groups around a plain value or one value-bearing group | each empty group is an unfielded `preproc_conditional_property_value` sibling of the value (B8's form), at every value site |
| a run that is the entire value and holds 2+ value-bearing groups | `value: (preproc_conditional_property_value_sequence …)` |

**Inside a sequence:**
- each value-bearing group is `value: (preproc_conditional_property_value …)`;
- empty groups between two value-bearing groups are unfielded children;
- the sequence spans from its first value-bearing group to its last.

**Entire value.** The run is the entire value when nothing but the property's own `;`, empty
groups or the end of the property follows it, and nothing but `=` or empty groups precedes it.
- This holds in every family, list families included. A single whole-value group is already a
  whole value in every family (§2.2), so a sequence is that rule extended to several groups.
- Element conditionals (`preproc_conditional_link_values`, `preproc_conditional_impl_values`,
  `preproc_conditional_option_members`) remain where the list has unconditional members or
  separators outside the groups (`#if X A = field(B), #endif B = field(A)`).

### 3.2 Ownership of `;` and empty groups

| placement | token | parent |
|---|---|---|
| `;` after the last `#endif` | the trailing `;` | `property`, unfielded, as today |
| `;` after the last `#endif` | empty groups between the last value-bearing group and the `;` | `property`, unfielded |
| either | an arm's own `;` | its group, unfielded, outside `value:`, as today |
| `;` inside the arms | empty groups after the last value-bearing group | **not** the property: the property ends at that group's terminated arms, so these are ordinary content of the host body, parsed as today |
| either | empty groups before the first value-bearing group | `property`, unfielded |

### 3.3 Why a new node type

Each alternative fails silently for a consumer that does not know about it:
- **Sibling `value:` fields under `property`** would revert the G5 invariant
  `property.value multiple=False` (`tools/check-field-types.py`).
  `child_by_field_name('value')` would then read only the first group.
- **Several groups inside one `preproc_conditional_property_value`** would break the oracle's
  one-group selector (`split_arms`, `property_value_select`), again silently.

A new type fails loudly instead. The gates force every consumer surface to classify it (§5.5).

**Field pins:**
- `preproc_conditional_property_value_sequence.value`: `multiple=True`, types
  `{preproc_conditional_property_value}`, no anonymous members;
- `property.value`: stays `multiple=False`.

### 3.4 What the sequence asserts, and the intended changes

**A sequence is a one-reading construct.** It reads the run as one value, assuming that in each
configuration at most one group supplies it before the property ends. That assumption is
exactly right when the groups' conditions are mutually exclusive (`#if X … #endif #if not X …
#endif`), the shape the probes and the deferred items record.

When the conditions are not exclusive, the property's boundary moves with the configuration,
and no single tree is every configuration's flat tree. For example:

```al
Visible =
#if X
    true;
#endif
#if X
    Caption = 'x';
#else
    false;
#endif
```

- X defined: `Visible = true; Caption = 'x';`, two properties.
- X undefined: `Visible = false;`, one.

The tree reads it as a sequence, the only reading under which every arm parses. The oracle
validates the configurations consistent with that reading and refuses the others as
`lowering:one-reading` (§5.3). They are classified, never passed. The existing one-reading
mechanism, P4's `reading` contracts, works the same way.

**Intended changes to clean trees,** named so that the zero-delta gates can allow exactly these
and nothing else:
- the generic empty prefix (`option_member_list` → value plus unfielded prefix);
- the ML, Namespaces and Implementation empty-prefix splits (two properties → one);
- the link and Implementation `;`-after runs that are the entire value (list of element
  conditionals → sequence; §3.1 "entire value");
- the item 35 unquoted split (two properties → one, with a sequence).

## 4. Mechanism (`grammar.js`)

### 4.1 One helper, six families

A helper, generalising `keyedValueConditional`, generates the value-site rules from a family's
value rule and arm content. The families are:
- generic `_property_value`, which covers `Implementation` and `OptionMembers`;
- `_ml_property_value`;
- `_namespaces_property_value`;
- `_table_relation_property_value`;
- `_link_property_value`;
- `_calc_formula_value`.

The six families therefore cannot drift apart.

**Empty groups.** The empty group is one shared, recursive rule, `_empty_value_conditional`
(directive headers and nested empty groups, no value), aliased to
`preproc_conditional_property_value`. B8's `_calc_formula_empty_conditional` becomes this rule.

**Witness.** A value-bearing group rule requires at least one present value, recursively
(B5b's termination witness).

**All-empty whole values.** Whether today's all-empty whole value (`N = #if X #endif ;`) keeps
parsing is decided per family by alc probe:
- where alc rejects it as syntax, it becomes a deliberate negative;
- where the rejection is only semantic, as with an empty `DataItemLink` (AL0171), it keeps
  parsing, as an empty group followed by the property's `;`, with no value.

### 4.2 `;` after the last `#endif`

The run continues until the property's `;`, and arms may carry their own `;` (mixed placement).
The value site is `prefix* (plain | group | sequence) suffix* ';'`, with
`sequence = group (empty* group)+`.

An arm `;` in a non-last group makes the property's boundary configuration-dependent (§3.4,
second example in §9 round 1). The tree is still the sequence. The oracle refuses the
configurations in which a later group is active after an earlier arm's `;` (§5.3).

### 4.3 `;` inside the arms

**Complete and incomplete groups.** A group is *complete* when it has `#else` and every arm is
present, terminated and, if nested, complete. Every configuration has then emitted its `;`.
Otherwise it is *incomplete*.

The complete and incomplete group productions are **disjoint**:
- the incomplete production requires a missing `#else`, or at least one absent or
  incomplete arm;
- "holds a value", "holds a terminator" and "every configuration terminates" are separate
  predicates, each carried by its own production state.

**G11's rule stays.** Every present value-bearing arm ends in `;`, recursively.

**Continuation:**
- **After a complete group, the property ends.** A following `#if` block is ordinary content.
  This is deterministic: the run offers no continuation after a complete group.
- **After an incomplete group, a following value-bearing group continues the sequence**,
  preferred by a declared conflict and `prec.dynamic` even when its arms would also parse as
  properties.
  - It is the only reading under which an arm like `false;` parses at all (§3.4).
  - In the exclusive-condition case it is every configuration's reading.
  - Configurations where it is not are refused by the oracle as one-reading (§3.4).
- **The last value-bearing group may be complete or incomplete.** Every earlier one is
  incomplete.
- **The termination witness:** the run holds at least one present, terminated arm.

**Feasibility is gated by a spike.** Before the main grammar task, a generation spike builds the
generic family's productions:
- the disjoint complete/incomplete group states;
- the recursive witnesses;
- the empty rule;
- the sequence alias.

It reports STATE_COUNT, the generator-required conflicts, and the trees of the §5.2 boundary
counterexamples. The remaining families follow only if the spike's trees are right.

### 4.4 Hosts and preserved forms

| placement | rule | families |
|---|---|---|
| `;` after | each family's arm of `property` | all six |
| `;` inside | `_property_with_terminator_in_if` | all six |
| `;` inside | `_property_whole_value_in_if` (action and assembly hosts, G11 parity) | generic, ML |

alc rejects the other families at the action and assembly hosts (AL0124).

**Preserved, with unchanged trees** (fixtures and the zero-delta gates):
- every TableRelation form:
  - `_table_relation_keyed_split`;
  - a relation head followed by `preproc_conditional_table_relation`;
  - a conditional head with a shared `else_table_relation_fragment`;
  - `_table_relation_open_if`;
- CalcFormula's formula-only arms, where a no-`where` aggregate never falls back to a call
  (issue #21);
- the existing `prec(-1)` / `prec(-2)` relations, the link precedences and the conflict list,
  audited against the generated rules. A static precedence can discard a reading before GLR
  sees it (`grammar.js` link comments), so the audit is per rule, not assumed.

### 4.5 Cost

STATE_COUNT rises: six families × two placements, plus the complete/incomplete split. It is
measured, first by the spike, and reported against the +2% guideline, not designed to a cap.
Parse speed is measured with `tools.perf ab` over DC.

## 5. Verification

### 5.1 Compiler evidence (`tools/alc_probe/cases/value-runs/`)

Committed before any grammar change, with `--check` clean:
- the 24 probes of §2.1, with real `// expect:` / `// source:` headers;
- `#elif` and `#else` runs, a three-group run, and nested empty groups
  (`#if X #if Y #endif #endif`);
- empty groups between and after value-bearing groups, in both placements;
- the configuration-dependent boundaries:
  - §3.4's example;
  - the `;`-after mixed example of §9 round 1;
  - the complementary three-group run (`#if X a; #endif #if not X b; #endif #if Y P = v;
    #endif`);
  - each configuration's verdict recorded;
- the all-empty whole value per family (§4.1);
- `OptionMembers` and link runs with commas inside and between groups, missing separators, and a
  configuration leaving one option member;
- the action and assembly hosts for generic and ML values.

### 5.2 Fixtures

**`test/corpus/property_value_run_test.txt`.** The expectations are generated from
`tree-sitter parse` output, so every field is labelled. It holds:
- every §5.1 shape × family, including nested-empty, nested-prefix and nested-run cases at arm
  value sites;
- the complete-then-property block (the property ends);
- the configuration-dependent boundary examples;
- the list-family runs (entire value → sequence; with unconditional members → element
  conditionals, unchanged).

Each tree is checked by hand against the flat tree of every configuration. A `bogus:` field
rename must fail the file, and the suite total must move by exactly the number of cases added.

**Preservation fixtures:**
- the TableRelation forms of §4.4;
- CalcFormula aggregates without `where`;
- a following conditional property block after a complete group;
- a following procedure after a run.

**Negatives.** Shapes alc rejects as syntax (§4.1) go in `tools/deliberate-negatives.txt`.

### 5.3 Oracle

**Assembler: ordered lowering.** `preproc_conditional_property_value_sequence` is registered as
an assembler, contract `whole-value-run`:
- **Walk:** the groups are walked in source order. Each group's selected arm is lowered through
  `property_value_select`, which returns its value node (fielded `value`, taking the
  sequence's field) and any `Terminator` fragment.
- **Before the first selected terminator:** at most one value may be selected. A second
  selected value raises `lowering:one-reading` at the sequence (§3.4).
- **At the first selected terminator:** the property ends there. The fragment passes up, and
  the engine's existing terminator hoist and mixed-placement handling apply unchanged
  (`engine.py`, the B5b mixed-placement branch: the earlier `;` ends the property, a later
  standalone `;` becomes an `empty_statement` sibling).
- **After the first selected terminator:** any further selected **value** raises
  `lowering:one-reading`. That content belongs to the host body in that configuration, and a
  value node cannot be re-read as body content. Further selected **terminators** follow the
  mixed-placement rule.
- **Zero selected values:** the assembler emits no value. Validity is left to the flat
  reference parse: a family where alc rejects `N = ;` gives a reference error, classified
  invalid-config with alc evidence; one where alc accepts it passes. Zero values are never
  ruled a discrepancy by the assembler.
- **Accounting:** empty groups and unselected arms are accounted as directives and inactive
  arms.

**Hosts:**
- `property:value` (single-slot) for the sequence;
- `preproc_conditional_property_value_sequence:value` for its groups;
- `preproc_conditional_property_value_sequence:<children>` for its interior empty groups;
- `property:<children>` and `preproc_conditional_property_value:<children>` (optional-slot) for
  prefix and suffix empty groups at both kinds of value site.

**Classification:**
- every `lowering:one-reading` record is classified in `fixture-classes.tsv` as
  `debt(B11-boundary)`, pinned to the record's reason and host, with a deferred-work entry
  (§6);
- every invalid-config record carries alc evidence;
- no discrepancy is ever classified, and the runner's rule stays as it is.

**Tiers:** quick tier clean; full tier over the four corpora clean.

### 5.4 Gates

- **Full-tree zero delta, every corpus:** a fresh `tree-harness` snapshot per corpus
  (BC.History, DC, BC28.1, BCApps-29.0), taken before the change and verified after it, plus
  `relation_census` zero-delta. Only the §3.4 intended changes may appear, and production
  holds none.
- **Fixtures:** the existing corpus fixtures are unchanged except the cases named in §3.4. A
  `git diff --stat test/corpus` review is required after every `-u`.
- **Error gates:** `has_error_sweep` over the four corpora and the corpus fixtures;
  `tree-sitter test`; `validate-grammar.sh --full`.
- **Coverage gates:**
  - `qc`: a new cluster must be justified, not blanket-accepted;
  - traversal census;
  - `tools/check-field-types.py` (Step 5b).
- **Incremental parse:** a pytest that toggles a run between one and two groups, between
  complete and incomplete, and between `;` inside and `;` after.
- **WASM:** `check-wasm-fresh` after a rebuild in its own commit.

### 5.5 Consumer surfaces

- **`traversal/policy.json`:** `preproc_conditional_property_value_sequence` is
  `class: assembler`, `arm_boundary: none`. It owns no directives; its child groups do, and
  `split_info()` on a child gives that group's arms.
  - Python, JS and Rust runtime witnesses (a `walk` over a sequence fixture) pin that a
    consumer reaches every group's arms.
  - `tools/traversal_census.py` gates the class against the oracle registry.
- **`queries/`:** folds, textobjects and highlights, wherever `preproc_conditional_property_value`
  appears, are checked and extended for the sequence.
- **CHANGELOG:** a Changed entry, with a migration note, naming:
  - the new node type and the shapes that produce it;
  - the intended tree changes of §3.4;
  - that a sequence is a one-reading construct.

## 6. Docs

- CHANGELOG: as §5.5.
- `docs/deferred-work.md`:
  - item 33 RESOLVED;
  - item 35 RESOLVED; its recorded unquoted split is confirmed at `bf72a2d`, and the quoted
    probe ERRORs instead;
  - a new entry, `B11-boundary`, for the configuration-dependent boundaries of §3.4, with the
    probes, the fixtures and the classified records. It also records the alternatives
    considered and not adopted: tracking condition text in the scanner, and a
    multi-configuration representation.
- Roadmap: row B11 added, marked done when it lands.
- CLAUDE.md / `.claude/rules`: the run mechanism, wherever whole-value conditionals are
  described.

## 7. Risks

- **A following conditional property block absorbed into a run.** It happens only after an
  incomplete group (§4.3). The configurations it misreads are refused by the oracle, never
  passed. Production has no such site, as the zero-delta gates show.
- **GLR cost of the declared conflicts.** Measured by the spike and `tools.perf ab`.
- **The spike shows the complete/incomplete split is too costly or conflicts with existing
  rules.** In that case the design returns to review with the measurement. It is not narrowed
  silently.

## 8. Not in scope

- `Permissions` (`permissions_property`): its own list-internal `#if` rule; production sites
  exist and parse correctly.
- Values continued across `#if` with an operator (`preproc_conditional_expression_tail`, B3).
- Condition evaluation in the scanner, or a multi-configuration tree (§6, `B11-boundary`).

## 9. Review record

**Round 1** (revision 1, gpt-6.1-sol, static review). 2 blockers, 8 majors and 1 minor. Each was
verified against the code or live parses before adoption:

1. **Configuration-dependent boundaries (blocker).** Verified by construction, since alc does
   not parse inactive arms: `Visible = #if X true; #endif #if X Caption = 'x'; #else false;
   #endif` is two properties for X and one for !X. The `;`-after mixed form,
   `#if X true; #else false #endif #if X Caption = 'x' #endif ;`, has the same issue.
   Adopted: the sequence is declared a one-reading construct (§3.4). The ordered oracle
   lowering refuses the inconsistent configurations (§5.3), and revision 1's claim of
   unambiguity for §4.2 is withdrawn.
2. **A discrepancy cannot be classified (blocker).** Verified: `runner.is_classified` accepts
   only `cannot-validate`, and a `LoweringError` yields cannot-validate. Adopted: refusals are
   `lowering:one-reading`, classified as debt; no discrepancy is classified (§5.3).
3. **No sound construction for complete/incomplete.** Adopted: disjoint productions, separate
   predicates, G11's per-arm termination, and a generation spike gating the main task (§4.3).
4. **Suffix ownership contradicted itself between §3 and §4.3, and "the `;` stays outside the
   sequence" was impossible for the inside placement.** Verified. Adopted: the ownership table
   (§3.2).
5. **The list-family exception was inconsistent.** Verified: `OptionMembers` `;`-after runs
   ERROR today, and `Implementation` and `OptionMembers` reach the grammar through generic
   `_property_value`. A single whole-value group is one `preproc_conditional_property_value`
   in every family, `OptionMembers` included (live parse). Adopted: the uniform "entire value"
   rule (§3.1). It names the link and Implementation `;`-after changes as intended (§3.4).
6. **"Exactly one value" was not a sufficient oracle contract.** Verified against
   `engine.py`'s mixed-placement branch. Adopted: the ordered lowering of §5.3, with zero
   values left to the reference parse.
7. **Nested empty groups were not defined.** Adopted: recursive emptiness, and decorations at
   every value site (§3).
8. **TableRelation split forms and static precedence.** Adopted: a preservation list and a
   per-rule precedence audit (§4.4).
9. **The compatibility promise and production proof were overstated.** Verified: revision 1's
   §5.5 promised no previously clean tree changes while fixing clean misparses, and the
   full-tree gate covered BC.History only. Adopted: the "previously correct" promise, the
   named intended changes (§3.4), four-corpus full-tree baselines (§5.4), and the scan demoted
   to discovery (§2.3).
10. **Traversal.** Verified: `split_info()` handles several groups, and
    `preproc_conditional_property_value` is `assembler` / `own-directives`. Adopted:
    `assembler` / `none` with runtime witnesses. The inaccurate traversal rationale is removed
    (§3.3, §5.5).
11. **Item 35 was not stale.** Verified: the recorded unquoted reproducer still splits
    silently at HEAD, and only the quoted probe ERRORs. Adopted: corrected in §1, §2.2 and §6.
