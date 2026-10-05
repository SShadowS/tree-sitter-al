# B11: property values made of a run of `#if` groups

**Status:** revision 6, 2026-10-05. Revision 5 had a fifth gpt-6.1-sol round: no blocker,
4 majors and 1 minor, all verified against the code and adopted (§9, round 5). Earlier rounds:
§9, rounds 1-4. This revision awaits review.
**Roadmap row:** B11, new (`docs/superpowers/plans/2026-09-28-roadmap-remaining-work.md`).
Absorbs deferred-work items 33 and 35, and the ML empty-prefix split recorded under item 33
during B8.
**Ships in:** the next major release. Adds one node type,
`preproc_conditional_property_value_sequence`. **Previously correct trees do not change**,
except the intended corrections named in §3.4. That is a measurement target, proven over all
four corpora (§5.4), not a conclusion.

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
- A *value site* is a position that holds one whole value:
  - the *property site*, from `=` to the property's terminator;
  - an *arm site*, from an arm's directive header to the arm's `;` or the next directive.
- The *run* is the maximal sequence of consecutive `#if … #endif` groups at a value site.

**Group predicates.** These are three separate predicates, each carried by its own production
state:
- **directive-only empty:** recursively, every arm is absent or holds only directive-only
  empty groups. No value, no `;`. Only these are decorations, lowered to nothing.
- **value-contributing:** at least one arm contributes a value, recursively. A syntactic value
  that is itself an all-empty conditional contributes none.
- **terminated:** the group has `#else`, and every arm is present and ends in `;`,
  recursively. Every configuration has then emitted a `;` by the group's `#endif`.
- **core-bearing:** not directive-only empty. At least one arm holds a syntactic value or a
  `;`. This is what routing counts (§3.1).

Syntactic value presence and value contribution are different. A group whose only arms are
empty-value terminated arms (`#if X #if Y #endif ; #endif`) is core-bearing and contributes no
value. It lowers to no value node plus its terminator (§5.3).

**Fragments are not groups of a run.** An arm must parse as a complete value of the family, or
as an empty-value terminated arm, for its group to take part in a run. Fragment arms never
form a whole-value group. They are either the existing continuation forms (TableRelation's
relation splits, §4.4), or an ERROR, as today. This is decided before §3.1's step 1. Examples:
- TableRelation `."No."`, or `where(...)` alone;
- a lone `-` before a formula;
- a pair list ending in `,`.

**Bare `;` arms.** An arm holding only `;` (`#if X ; #else true; #endif`) is not admitted, as
today. An arm whose syntactic value is a directive-only empty conditional followed by `;` *is*
admitted today wherever the family's value is optional (link: `#if X #if Y #endif ; #else
A = field(B); #endif`, live parse). It stays admitted: it is a terminated arm that contributes
no value, the empty-value case of §3.2. It is never erased, because it carries a `;`. Both shapes
are probed (§5.1).

### 3.1 Routing a run

A run is routed in this order. Each step applies only if the previous ones did not. The steps
are mutually exclusive by construction:

| # | condition | kind | tree |
|---|---|---|---|
| 1 | the run has at most one core-bearing group | — | that group (or plain value) is the core, as today; directive-only empty groups around it are decorations |
| 2 | **`;` inside:** every present arm of every core-bearing group ends in `;`, recursively. An unconditional `;` may follow the run directly | (a) | `value: (preproc_conditional_property_value_sequence …)`; a directly following `;` is the property's own, as it is for a single group today |
| 3 | **`;` after:** some arm lacks its own `;`, and an unconditional `;` follows the run; list family (link, Implementation, `OptionMembers`), and no arm carries its own `;` | (b) | the family's element conditionals: today's tree for link and Implementation; `OptionMembers` gains the entirely conditional form (§4.1) |
| 4 | **`;` after**, as in step 3, in CalcFormula, TableRelation, ML or Namespaces. Arms may carry their own `;` (mixed placement) | (a) | sequence |
| 5 | anything else: a generic `;`-after run of 2+ core-bearing groups, and a list-family `;`-after run in which some arm carries its own `;` | (c) | not formed: a visible ERROR, owned by roadmap row **B13** (§6) |

**Placement is decided by arm termination, not by the trailing `;` alone.**
- When every present arm ends in `;`, the run is step 2 whether or not a `;` follows it. A
  directly following `;` is owned by the property, as today's single-group tree already does:
  `Caption = #if X 'a'; #else 'b'; #endif ;` gives `property` children `=`, the group, `;`
  (live parse). The engine's mixed-placement rule then makes it a standalone `;` in every
  configuration (§5.3).
- When some arm lacks its `;`, the trailing `;` is required and ends the value, which is the
  `;`-after placement.

The spikes keep both readings alive until the run's last `#endif` and the token after it
(§4.3).

**Why each step is sound.**
- **Step 2.** A terminated arm ends the value, so groups cannot concatenate *at this site*:
  in each configuration, the first active arm ends the property. The only open question is a
  configuration-dependent boundary, the one-reading residue of §3.4 (B12). Each arm's core is
  its own value site, routed by these same rules. An inner generic two-group `;`-after run
  inside a terminated arm is step 5 at the inner site, and so an ERROR, even though the outer
  run is step 2.
- **Step 3.** Element conditionals already represent both alternatives and comma
  concatenation. The configured list is the selected elements spliced together, and the list
  validator checks the separators per configuration (§5.3). No separator analysis is needed in
  the grammar, so nested groups carrying the joining `,` need no special state.
- **Step 4.** In these four families, a complete value cannot be followed by another complete
  value of the same family to form one value:
  - a formula is closed;
  - a relation's continuations (`where`, `else`, `if`) are not complete relation values, and
    have their own existing forms (§4.4);
  - ML and Namespaces pair lists join only through `,`, so an arm ending or starting with `,`
    is not a complete value, and the run falls to step 5.

  Two active groups therefore cannot form one value. In a configuration where both are active
  before the `;`, the text is invalid, and the configuration is classified invalid-config.
- **Step 5.** The generic `_property_value` union concatenates in many ways:
  - `Page` + `"P"` is an object reference;
  - `F` + `(1)` is a call;
  - `0 :` + `5` is a decimal range;
  - `sorting(...)` + `where(...)` is a view;
  - `'x',` + `Locked = true` is a caption.

  A tree for those runs needs prefix/suffix-compatible states over the whole union, which is
  B13's work. Until then they stay the visible ERRORs they are today. No previously correct
  tree becomes an ERROR.

A value is never given a tree whose reading is silently wrong in the configurations where
several groups are active.

**Inside a sequence:**
- each core-bearing group is `value: (preproc_conditional_property_value …)`;
- directive-only empty groups between two core-bearing groups are unfielded children;
- the sequence spans from its first core-bearing group to its last.

**Only the core is fielded.** The field `value` goes on the site's core: the plain value, the
group or the sequence. Decorations are never fielded and never wrapped, so `property.value`
stays `multiple=False` and each arm still holds at most one `value:`.

### 3.2 Ownership of `;` and empty groups

Each row applies at every value site. "The site's node" is `property` at the property site,
and the enclosing group at an arm site.

| placement | token | parent |
|---|---|---|
| `;` after the last `#endif` | the trailing `;` | the site's node, unfielded, as today |
| `;` after the last `#endif` | directive-only empty groups between the core and the `;` | the site's node, unfielded |
| either | an arm's own `;` | its group, unfielded, outside `value:`, as today |
| `;` inside the arms | directive-only empty groups after the last core-bearing group | **not** the site: the site ends at that group's terminated arms, so they are ordinary content after it, parsed as today |
| either | directive-only empty groups before the core | the site's node, unfielded |
| either, directly after the run | an unconditional `;` | the property, unfielded, as today (§3.1). Mixed placement makes it standalone per configuration |
| either, after a **terminated** group and a following block | anything after that block, including an unconditional `;` | **not** the site: every configuration ended the value at the group, so the block and what follows are ordinary content (the §4.2 example) |

**The core is optional exactly where the family's value is optional today.** The matrix is read
from the `property` arms in `grammar.js`:

| family | property value today | all-empty site |
|---|---|---|
| generic | optional | parses: decorations and `;`, no `value:` |
| ML | optional (`optional(field('value', …))`) | parses |
| Namespaces | optional | parses |
| link | optional | parses |
| TableRelation | required | ERROR |
| CalcFormula | required | ERROR |

At an arm site the core is required: an arm is absent, or holds a value (no bare-`;` arm).
B11 narrows no family's optionality.

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
- the item 35 unquoted `;`-inside run (two properties → one, with a sequence).

**No contract migrations.** The link and Implementation `;`-after runs keep their element
conditionals (§3.1 step 3).

**New support, no clean tree changed:**
- `;`-inside runs in every family (step 2);
- `;`-after runs in CalcFormula, TableRelation, ML and Namespaces (step 4);
- the entirely conditional `OptionMembers` `;`-after run (step 3).

**Not supported, unchanged ERRORs owned by B13:** step 5, including the generic `;`-after
runs that the §2.1 probes accept (`Caption`, `Visible`).

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

**Witness.** A core-bearing group rule requires at least one present arm holding a value or an empty-value `;`, recursively
(B5b's termination witness).

**All-empty sites** follow the §3.2 matrix:
- generic, ML, Namespaces and link parse them;
- TableRelation and CalcFormula ERROR.

Each is pinned against an alc probe. Structural acceptance and compiler validity are recorded
separately: where the grammar accepts what alc rejects as syntax, it is recorded as
over-acceptance, as `RunPageLink = ;` already is (B5b, CLAUDE.md). The parser does not
validate.

**`OptionMembers` (step 3).** Today an opening `preproc_conditional_option_members` requires a
following ordinary member, and an entirely conditional comma run ERRORs (live parse). The
option-list production gains the entirely conditional form, with element conditionals carrying
their `,` exactly as the link list does, and blank slots preserved:
- leading `,`;
- consecutive `,,`;
- trailing `,`.

Every comma and every ordinal survives in the tree.

### 4.2 `;` after the last `#endif`

Per family (§3.1):
- **List families:** element conditionals (step 3).
- **CalcFormula, TableRelation, ML and Namespaces:** the site is `prefix* core? suffix* ';'`,
  where `core` is a plain value, a group, or `sequence = group (empty* group)+` (step 4). Arms
  may carry their own `;` (mixed placement).
- **Generic:** one core-bearing group at most (step 1). A second makes the run step 5.

**A terminated group ends the site in both placements.** No continuation is offered after a
terminated group (§3.2), so an unconditional `;` after it is a standalone `;`:

```al
Visible =
#if X
    true;
#else
    false;
#endif
#if Y
    Caption = 'c';
#endif
;
```

This is `Visible` (one group), then a conditional `Caption` property, then an `empty_statement`.

In step 4, an arm `;` in a non-last, non-terminated group makes the boundary
configuration-dependent (§3.4). The tree is the sequence. The oracle refuses the configurations
in which a later group is active after an earlier arm's `;` (§5.3).

### 4.3 `;` inside the arms

**Terminated and non-terminated groups** (§3). The two group productions are **disjoint**:
- the non-terminated production requires a missing `#else`, or at least one absent or
  non-terminated arm;
- value contribution, terminator presence and termination of every configuration are separate
  predicates, each carried by its own production state.

**G11's rule stays.** In this placement, every present arm ends in `;`, recursively.

**Continuation:**
- **After a terminated group, the site ends.** A following `#if` block is ordinary content.
  This is deterministic: the run offers no continuation after a terminated group.
- **After a non-terminated group, a following core-bearing group continues the
  sequence**, preferred by a declared conflict and `prec.dynamic` even when its arms would
  also parse as properties.
  - It is the only reading under which an arm like `false;` parses at all (§3.4).
  - In the exclusive-condition case it is every configuration's reading.
  - Configurations where it is not are refused by the oracle as one-reading (§3.4).
- **The last core-bearing group may be terminated or not.** Every earlier one is
  non-terminated.
- **The termination witness:** the run holds at least one present, terminated arm.

**Feasibility is gated by spikes, of grammar and lowering together.** Before the main grammar
task, three spikes are built: generic, link and ML. ML has its own keyed rules.

**Families.**
- **Generic:**
  - the step 2 sequence, with disjoint terminated / non-terminated group states, recursive
    witnesses, the empty rule and the sequence alias;
  - step 1 decorations;
  - step 5 staying an ERROR for the `;`-after placement.
- **Link:**
  - step 3 element conditionals against the step 2 sequence, under link precedence 6;
  - nested groups carrying the joining `,`;
  - item 35.
- **ML:** step 4 against step 5 (a comma-edge arm).

**Delayed decisions.** The placement is known only at the end of the run (a `;` after the last
`#endif`, or not), so the spikes keep the `;`-inside and `;`-after readings alive across the
whole run. They also keep continuation and the end of the site alive. No decision may commit at
the first group.

**Common prefixes.** The spikes are tested on common prefixes ending in each of:
- ordinary members;
- separators outside the groups;
- the property's `;`;
- nested-arm delimiters;
- trailing empty groups;
- a terminated group followed by a conditional property and an unconditional `;`.

**Precedence.** Conflicting arm reductions keep compatible static precedence. A
`prec.dynamic` preference applies only to a completed interpretation, never to a conditional
prefix.

**Step 5 witnesses.** Each spike checks that the following yield no sequence and stay an
ERROR, rather than becoming a silent tree:
- `RunObject = #if X Page #endif #if Y "P" #endif ;`;
- `sorting(...)` then `where(...)` across groups;
- a caption with `, Locked = true` across groups;
- ML pairs across groups with `,`;
- a generic two-group `;`-after alternative (`Caption = #if X 'a' #endif #if not X 'b'
  #endif ;`).

**Step 2 counterpart.** The same generic alternatives with `;` inside the arms
(`SourceTableView = #if X where(..); #endif #if not X where(..); #endif`) form a sequence.

**Lowering.** Each spike also runs the §5.3 lowering on its trees.

**Report.** STATE_COUNT, the generator-required conflicts, the trees, and the oracle records.
The remaining families follow only if all three spikes are right.

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

STATE_COUNT rises: six families × two placements, plus the terminated/non-terminated split. It is
measured, first by the spike, and reported against the +2% guideline, not designed to a cap.
Parse speed is measured with `tools.perf ab` over DC.

## 5. Verification

### 5.1 Compiler evidence (`tools/alc_probe/cases/value-runs/`)

Committed before any grammar change, with `--check` clean:
- the 24 probes of §2.1, with real `// expect:` / `// source:` headers;
- `#elif` and `#else` runs, a three-group run, and nested empty groups
  (`#if X #if Y #endif #endif`);
- directive-only empty groups between and after core-bearing groups, in both placements;
- the configuration-dependent boundaries:
  - §3.4's example;
  - the `;`-after mixed example of §9 round 1;
  - the complementary three-group run (`#if X a; #endif #if not X b; #endif #if Y P = v;
    #endif`);
  - each configuration's verdict recorded;
- the all-empty whole value per family (§4.1);
- `OptionMembers` and link runs with commas inside and between groups, missing separators, and a
  configuration leaving one option member;
- the entirely conditional two-entry list of §3.1, every configuration valid, for link,
  Implementation and `OptionMembers`;
- `OptionMembers` blank slots across groups: leading, consecutive and trailing `,`;
- the step 5 shapes, each with its alc verdict:
  - `RunObject` `Page` then `"P"`;
  - `F` then `(1)`;
  - `0 :` then `5`;
  - `SourceTableView` `sorting(...)` then `where(...)`;
  - ML and Namespaces pairs joined by `,`;
  - a caption with `, Locked = true`;
- the step 2 generic alternatives with `;` inside the arms, with and without a directly
  following `;`;
- `SubPageLink = #if X A = field(B); #endif #if not X A = field(C); #endif ;` (step 2, the
  trailing `;` the property's own);
- a run whose first group holds only an empty-value terminated arm (`DataItemLink = #if X
  #if Y #endif ; #endif #if not X A = field(B); #endif`);
- link and Implementation entirely conditional runs with missing, leading and trailing
  separators, and with no member selected;
- a bare-`;` arm, and a nested-empty-then-`;` arm, per family (§3, "Bare `;` arms");
- an entirely conditional `OptionMembers` run whose every configuration selects nothing, and
  one that selects only blank slots;
- the terminated-group-then-property example of §4.2;
- the action and assembly hosts for generic and ML values.

### 5.2 Fixtures

**`test/corpus/property_value_run_test.txt`.** The expectations are generated from
`tree-sitter parse` output, so every field is labelled. It holds:
- every §5.1 shape × family, including nested-empty, nested-prefix and nested-run cases at arm
  value sites;
- the terminated-group-then-property block (the property ends);
- the configuration-dependent boundary examples;
- the list-family runs under the §3.1 routing: `;` inside → sequence (step 2); `;` after,
  including entirely conditional comma runs → element conditionals (step 3; unchanged for link
  and Implementation, new for `OptionMembers`);
- the terminated-group-then-property example of §4.2, with the final standalone `;`;
- nested groups carrying the joining `,` of a link list (step 3), and the same with
  directive-only decorations after the `,`.

**Known gaps go in a separate file: `test/corpus/property_value_run_b13_gap_test.txt`.** It holds
only the step 5 shapes.
- **The exemption is basename-wide**, so this file, and only this file, is listed in
  `tools/deliberate-negatives.txt`. `property_value_run_test.txt` stays under the strict
  positive sweep.
- **Each case says what it is:** valid AL whose structure is deferred (B13), not invalid
  input.
- **B13 work turns them positive and moves them out of this file.** No previously correct tree
  may enter it.

Each tree is checked by hand against the flat tree of every configuration. A `bogus:` field
rename must fail the file, and the suite total must move by exactly the number of cases added.

**Preservation fixtures:**
- the TableRelation forms of §4.4;
- CalcFormula aggregates without `where`;
- a following conditional property block after a terminated group;
- a following procedure after a run.

**Negatives.** Shapes alc rejects as syntax (§4.1) go in `tools/deliberate-negatives.txt`.

### 5.3 Oracle

**Selector changes, not reuse.** `property_value_select` gets a sibling selector for whole-value
sites, `whole_value_select`. TableRelation's `table_relation_select` and the shared `_select_arm`
keep their behaviour.

`whole_value_select`:
- **Decorations.** Recognizes empty groups in an arm and lowers them as directives (no
  nodes), apart from the arm's core.
- **Nesting.** Dispatches a nested `preproc_conditional_property_value` and a nested sequence
  recursively, preserving their ordered fragments. Today only a same-kind nested group gets
  fragment-preserving dispatch, and `_lower_all` refuses the rest.
- **Arm kinds.** Registers the sequence in the arm set, at the hosts `property:value` and
  `preproc_conditional_property_value:value`.

**Sequence assembler: ordered lowering, zero or one value.**
`preproc_conditional_property_value_sequence` is an assembler, contract `whole-value-run`. Its
output is **zero or one** value node: the host's `single-slot` is metadata here, and the
assembler enforces the cardinality itself.
- **Walk.** The groups are walked in source order, each through `whole_value_select`.
- **Before the first selected terminator,** at most one value may be selected. A second one
  raises `lowering:one-reading` at the sequence.
- **At the first selected terminator,** the property ends. The fragment passes up to the
  engine's terminator hoist.
- **After it,** a further selected **value** raises `lowering:one-reading`. That content is
  host-body content in that configuration, and a value node cannot be re-read as body content.
  Further selected terminators become standalone `;`.
- **Accounting.** Empty groups and unselected arms are accounted as directives and inactive
  arms.

**The predicate is the sequence's own**, with `reading=None`, using the existing
`lowering:one-reading` refusal category. `ExpressionContinuation` (G7) refuses the same way
without a registry reading. The P4 arm-reading predicates (`READINGS`) do not describe a run,
and `reading_active()` needs a directly owned directive group, which the sequence does not
have. So no new `READINGS` entry is added.

These are registered on the `preproc_conditional_property_value` entry. `branch_select`'s
exactly-one behaviour is never substituted for the assembler's zero-or-one rule.

**`OptionMembers` validator: holes allowed.** The list-run path for `option_member_list` gets
a family-specific, hole-aware check:
- leading, consecutive and trailing `,` are legal;
- every `,` and every ordinal is preserved;
- the one-member unwrap (`option-member-list-unwrap`) still applies.

Link and Implementation keep the strict `item (, item)*` check (`_check_alternation`).

**Emptied lists: `list-value-empty`.** A step 3 run can select nothing in a configuration, in
any of the three list families:
- `link_value_list`;
- `implementation_value_list`;
- `option_member_list`.

None of them is in `EMPTY_REMOVABLE`, so `_lower_ordinary` raises `empty-node` before the
one-member unwrap.

The fix is a named, site-aware rewrite, `list-value-empty`. It removes an emptied list of these
three kinds only when the list sits at an optional value site:
- the value of a `property` whose family value is optional (§3.2);
- the value of a whole-value arm (`preproc_conditional_property_value:value`) whose property
  is such a property.

A comma-only `OptionMembers` value is not empty, and keeps its separators and ordinals.

The tests cover, per family and at both kinds of site:
- zero members;
- comma-only values;
- one bare member, which unwraps for `OptionMembers`;
- one member plus blank slots, which does not unwrap.

**Engine fix: ordered standalone `;`.** Today each later terminator becomes its own
`SiblingsAfter`, inserted at anchor+1, so a third `;` lands before the second. The fix collects
every later terminator of one property into ONE source-ordered `SiblingsAfter`. This applies to
mixed placement today as well. Tests cover three and four active `;`, with and without the
property's own trailing `;`.

**Zero selected values.** The contract is:
- zero selected values produce no value node;
- a reference parse error becomes cannot-validate (`reference-error`), classified
  invalid-config with alc evidence;
- a clean reference is compared normally, whole structure and boundary.

The reference is a tree-sitter parse of the configured text, not an alc compilation. Compiler
validity is established separately by the §5.1 probes, and known over-acceptance (an empty
`RunPageLink`) is recorded there, not inferred from the oracle.

**Hosts.**

| host slot | node | policy |
|---|---|---|
| `property:value` | sequence | single-slot (cardinality enforced by the assembler) |
| `preproc_conditional_property_value:value` | sequence | single-slot |
| `preproc_conditional_property_value_sequence:value` | its groups | optional-slot (each group lowers to zero or one value; the assembler enforces the total) |
| `preproc_conditional_property_value_sequence:<children>` | interior directive-only empty groups | optional-slot (zero nodes) |
| `property:<children>` | decorations at the property site | optional-slot |
| `preproc_conditional_property_value:<children>` | decorations at an arm site | optional-slot |

**Classification.**
- **Configuration-dependent boundaries.** The residue gets its own roadmap row, **B12**
  ("configuration-dependent property boundaries"), the owner that would remove the debt with
  a multi-configuration representation. Its records are classified `debt(B12)`, each pinned
  to the refusal kind, the sequence node and its host.
  - `tools/config_oracle/fixtures.py` `ROADMAP` gains B10, which is missing today, B11, B12
    and B13.
  - Loader tests pin the new owners.
- **B13 records.** The step 5 fixtures have a clean flat reference and an errored
  multi-configuration tree, so the runner reports `cannot-validate:multi-config-parse:…`.
  Each such record is classified `debt(B13)`, never `negative` or `invalid-config`: those
  categories claim compiler rejection.
- **invalid-config records** carry alc evidence. This includes the step 4 configurations
  where two groups are active before the `;`.
- **Discrepancies** are never classified; the runner's rule is unchanged.

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
  - a new entry for the configuration-dependent boundaries of §3.4 (roadmap row B12), with the
    probes, the fixtures and the classified records. It also records the alternatives
    considered and not adopted: tracking condition text in the scanner, and a
    multi-configuration representation.
- Roadmap: rows added:
  - B11, marked done when it lands;
  - B12, the configuration-dependent boundaries' owner;
  - B13, conditional value fragments: the kind (c) concatenations, each with its probe.
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
- Condition evaluation in the scanner, or a multi-configuration tree (§6, roadmap row B12).
- Kind (c) concatenations: `sorting`/`order`/`where` across groups, ML and Namespaces pair
  concatenation across groups, caption attributes across groups (roadmap row B13). They stay
  visible ERRORs.

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

**Round 2** (revision 2). Round-1 status: 2, 10 and 11 resolved, and 8 resolved as acceptance
criteria; 1, 3, 4, 5, 6, 7 and 9 partly resolved. New: 1 blocker, 7 majors and 1 minor, each
verified against the code before adoption:

1. **An entirely conditional list can concatenate (blocker).** Verified by construction: two
   groups whose arms carry `,` form one two-entry list in every configuration, and §5.3 of
   revision 2 would have refused all of them. Adopted: the separator rule (§3.1) replaces the
   "entire value" rule. The contract migrations are named apart from the preservation promise
   (§3.4, Status).
2. **The spike omitted the delayed sequence-against-list decision.** Adopted: a link spike
   beside the generic one, with common-prefix cases and the precedence rule (§4.3).
3. **§4.2 bypassed the terminated-group boundary.** Verified: revision 2 stated it for the
   inside placement only. Adopted: a terminated group ends the site in both placements, and
   the fixture has the final standalone `;` (§3.2, §4.2).
4. **Recursive site ownership and the all-empty core.** Adopted:
   - property and arm sites with explicit owners;
   - only the core fielded;
   - the core optional exactly where the family's value is optional today (§3, §4.1).
5. **`property_value_select` cannot lower the nested shapes.** Verified: `_select_arm` raises
   contract-shape on more than one item, and only a same-kind nested group gets
   fragment-preserving dispatch. Adopted: `whole_value_select`, with decorations, recursive
   dispatch, the nested sequence host, and the assembler enforcing zero-or-one (§5.3).
6. **`SiblingsAfter` order.** Verified: each fragment inserts at anchor+1. Adopted: one
   source-ordered `SiblingsAfter` per property, with 3- and 4-`;` tests (§5.3).
7. **`debt(B11-boundary)` fails the loader.** Verified: the owner regex is `[A-Za-z0-9]+`, and
   `ROADMAP` covers B1-B9, so B10 is missing too. Adopted: roadmap row B12 as the owner, and
   `ROADMAP` gains B10, B11 and B12, with loader tests (§5.3).
8. **The reference parse is not alc.** Verified: `reference.extract` parses the configured
   text with tree-sitter. Adopted: the zero-value contract restated, and compiler validity
   kept separate (§5.3).
9. **P4 terminology.** Verified: `ExpressionContinuation` raises one-reading with no registry
   reading. Adopted: the sequence's own predicate, with `reading=None` (§5.3).

**Round 3** (revision 3). Round-2 status: 2, 6, 7, 8 and 9 resolved; 1, 3, 4 and 5 partly
resolved. New: 1 blocker, 4 majors and 1 minor, each verified before adoption:

1. **No crossing comma does not imply alternatives (blocker).** Verified:
   - `sorting_value` is `sorting(...) [order] [where]` (`grammar.js` `sorting_value`), and
     `where_clause` is a complete `_property_value` alone;
   - the reviewer's `SourceTableView` run ERRORs today (live parse).

   Adopted: three run kinds (§3.1). Alternatives exclude continuation-capable values per family.
   Other concatenations are not formed, stay visible ERRORs, and are owned by the new row B13.
   This keeps them out of B12 and out of any silent tree.
2. **Crossing comma lacked a grammar-level definition.** Adopted: the family list's own
   separator, a direct separator child of the top-level `link_value_list`,
   `implementation_value_list` or `option_member_list`, at an arm edge. It excludes nested
   commas and caption, ML and Namespaces punctuation (§3.1). Verified: ML and Namespaces have
   no element-conditional production, so their comma concatenation is kind (c).
3. **The optional-core matrix was wrong.** Verified: ML and Namespaces use
   `optional(field('value', …))`. Adopted: the matrix in §3.2. No family's optionality is
   narrowed.
4. **Value-empty and terminator-free were conflated.** Adopted: three predicates (§3), with
   only directive-only empty groups erased. Bare-`;` arms are not admitted (as today) and are
   probed, so a `;` is never erased.
5. **`OptionMembers` concatenation needed a hole-aware contract.** Verified: `_check_alternation`
   raises on a trailing separator, and today's entirely conditional option run ERRORs (live
   parse), while the link and Implementation ones parse as element conditionals. Adopted: the
   production extension (§4.1) and a family-specific hole-aware validator, with link and
   Implementation kept strict (§5.3).
6. **Sequence-child host policies were blank (minor).** Adopted: optional-slot for both, on
   the group's registry entry, with the assembler enforcing zero-or-one (§5.3).

**Round 4** (revision 4). Round-3 status: 3 and 6 resolved; 5 resolved in design; 1, 2 and 4
partly resolved. New: 1 blocker and 5 majors, each verified before adoption:

1. **The generic continuation table was incomplete (blocker).** Verified:
   `RunObject = #if X Page #endif #if Y "P" #endif ;` ERRORs today (live parse), and its
   arms are complete generic values that concatenate into an object reference. So do calls,
   decimal ranges, views and captions. Adopted: continuation tables are dropped. Routing is by
   placement and family (§3.1). Generic `;`-after runs of 2+ value-contributing groups are
   step 5 (B13), while generic `;`-inside runs are sequences, because terminated arms cannot
   concatenate.
2. **The predicates were not exhaustive or disjoint.** Adopted: five ordered steps, mutually
   exclusive by construction. The reviewer's terminated `where` alternatives are step 2, and an
   unconditional member with conditional alternatives in a list is step 3.
3. **Nested groups can carry the joining `,`.** Adopted: list families never analyse
   separators in the grammar. They always use element conditionals in the `;`-after
   placement, the per-configuration list validator judges the separators, and nested cases are
   fixtures (§5.2). This also removes revision 4's link and Implementation contract
   migrations.
4. **Excluding bare `;` does not imply value contribution.** Verified:
   `DataItemLink = #if X #if Y #endif ; #else A = field(B); #endif ;` parses today (live
   parse). Adopted: syntactic presence and value contribution are separate predicates. The
   nested-empty-then-`;` arm stays admitted as a terminated empty-value arm and is never erased
   (§3).
5. **B13 weakened the error gates.** Verified: `has_error_sweep` matches deliberate negatives by
   basename. Adopted: a separate B13 gap fixture file, the strict sweep kept for the positive
   file, and exact `debt(B13)` classifications (§5.2, §5.3).
6. **An entirely conditional `OptionMembers` can lower to no members.** Verified:
   `option_member_list` is not in `EMPTY_REMOVABLE`. Adopted: the site-aware rewrite
   `option-member-list-empty`, with tests (§5.3).

**Round 5** (revision 5). Round-4 status:
- resolved in design: 1 and 3;
- resolved: 5;
- partly resolved: 2, 4 and 6.

The reviewer confirmed that step 4's complete-value closure holds: TableRelation, CalcFormula,
ML and Namespaces fragments are not complete values. They also confirmed that the link and
Implementation element productions exist (`_link_value_seq`, `_impl_value_seq`).

New: 4 majors and 1 minor, each verified before adoption:

1. **Step 1 could not represent non-contributing groups that carry a `;`.** Adopted:
   - routing counts core-bearing groups;
   - an empty-value terminated arm lowers to no value plus its terminator;
   - fragments are excluded before step 1 (§3).

   Step 2's soundness is also qualified per site: inner sites are routed independently.
2. **A trailing `;` did not determine placement.** Verified by live parse: today,
   `Caption = #if X 'a'; #else 'b'; #endif ;` gives the property the trailing `;`, so
   revision 5's §3.2 row "anything after a terminated group, including `;`, is not the site"
   contradicted a current tree. Adopted: placement is decided by arm termination, and a
   directly following `;` is the property's, as today (§3.1, §3.2). Only content after a
   following block leaves the site.
3. **Implementation has no list-run lowering.** Verified: `preproc_conditional_impl_values` is
   registered unsupported and is absent from `LIST_RUN_TYPES`. Adopted: handler, arm set,
   hosts, `LIST_RUN_TYPES` and the strict validator. Separator refusals are classified only
   with alc evidence (§5.3).
4. **Empty-list handling was incomplete.** Adopted: `list-value-empty` for all three list
   families, at property and nested whole-value arm sites. Comma-only `OptionMembers` values are
   kept (§5.3).
5. **Spike count was stale (minor).** Adopted: three spikes, generic, link and ML (§4.3).
