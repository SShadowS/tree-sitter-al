# B11: property values made of a run of `#if` groups

**Status:** revision 4, 2026-10-05. Revision 3 had a third gpt-6.1-sol round: 1 blocker,
4 majors and 1 minor, all verified against the code and adopted (§9, round 3). Earlier rounds:
§9, rounds 1 and 2. This revision awaits review.
**Roadmap row:** B11, new (`docs/superpowers/plans/2026-09-28-roadmap-remaining-work.md`).
Absorbs deferred-work items 33 and 35, and the ML empty-prefix split recorded under item 33
during B8.
**Ships in:** the next major release. Adds one node type,
`preproc_conditional_property_value_sequence`. **Previously correct trees do not change**,
except the contract migrations named in §3.4. That is a measurement target, proven over all
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
- **value-bearing:** at least one arm holds a value, recursively.
- **terminated:** the group has `#else`, and every arm is present and ends in `;`,
  recursively. Every configuration has then emitted a `;` by the group's `#endif`.

**No bare-`;` arms.** An arm holding only `;` (`#if X ; #else true; #endif`) is not admitted,
as today: every arm production that carries a `;` carries a value before it. alc's verdict on
the bare-`;` arm is recorded by a probe (§5.1). So "terminated" implies "value-bearing" arm by
arm, and a `;` is never erased as a decoration.

### 3.1 Routing a run

A run is routed by what its groups' arms can be. There are three kinds, and the grammar forms
only the first two:

| run kind | when | tree |
|---|---|---|
| **(a) alternatives** | every group is value-bearing or directive-only empty; every arm value is a complete value of the family; no arm has the family list's own separator at its edge (below); and no group after the first value-bearing one holds a *continuation-capable* value (below) | 2+ value-bearing groups: `value: (preproc_conditional_property_value_sequence …)`; 1: unchanged |
| **(b) list concatenation** | link, Implementation or `OptionMembers`, when the family list's own separator sits at an arm edge, or the list has unconditional members or separators | the family's element conditionals, as today. `OptionMembers` gains the entirely conditional form (§4.1) |
| **(c) other concatenation** | anything else that concatenates across groups | not formed: it stays an ERROR, visible, owned by roadmap row **B13** (§6) |

A value is never given a tree whose reading is silently wrong in the configurations where
several groups are active. When the grammar cannot give the concatenation its own structure,
it gives no structure (c).

**The family list's own separator** is a `,` that is a direct separator child of the family's
top-level list production at this value site:
- `link_value_list`'s `,`;
- `implementation_value_list`'s `,`;
- `option_member_list`'s `,`.

These commas are **not** it:
- commas nested deeper: in `where_conditions`, call arguments, `sorting(...)` fields, or a nested
  group's own list;
- commas of a non-list value's own punctuation: a caption's `, Locked = true`, ML and
  Namespaces pairs.

At an *arm edge* means the last token before the arm's closing directive, or the first token
after its opening directive. The decision is local to the group (the separator is inside it,
or at the next group's first arm token), so the spikes keep both readings alive across that
one boundary (§4.3).

**Continuation-capable values** are complete values that some other complete value of the same
family can precede, forming one value. They are listed per family, from the flat grammar:

| family | continuation-capable kinds |
|---|---|
| generic | `where_clause`; the `order(...)`-only `sorting_value` (both can follow a `sorting(...)`: `sorting_value` is `sorting(...) [order] [where]`) |
| ML, Namespaces | none as complete values; their pair lists concatenate only through `,`, which is (c) |
| TableRelation | none at the whole-value level; relation continuations are the existing relation forms (§4.4) |
| CalcFormula | none |
| link, Implementation, OptionMembers | none besides their lists' `,`, which is (b) |

The spikes (§4.3) check this table against the generated grammar: a second complete value
following a first must yield no sequence.

**A single whole-value group** is already one `preproc_conditional_property_value` in every
family (§2.2). A sequence extends that rule to several groups.

**Inside a sequence:**
- each value-bearing group is `value: (preproc_conditional_property_value …)`;
- directive-only empty groups between two value-bearing groups are unfielded children;
- the sequence spans from its first value-bearing group to its last.

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
| `;` inside the arms | directive-only empty groups after the last value-bearing group | **not** the site: the site ends at that group's terminated arms, so they are ordinary content after it, parsed as today |
| either | directive-only empty groups before the core | the site's node, unfielded |
| either, after a **terminated** group | anything that follows, including an unconditional `;` | **not** the site: every configuration has already ended the value. An unconditional `;` there is a standalone `;` (`empty_statement`), as B5b's mixed placement already gives |

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
- the ML, Namespaces and Implementation empty-prefix splits (two properties → one).

**Contract migrations.** These are flat-correct today, and are changed deliberately for
uniformity:
- the link and Implementation `;`-after runs of kind (a), with no list separator at an arm
  edge and no unconditional member;
- the item 35 unquoted run.

They go from a list of element conditionals (or a split) to a sequence. That is the
representation a single group already has, and the CHANGELOG names it as a migration.

**New support, no clean tree changed:**
- runs of kind (a) that ERROR today, in every family;
- the entirely conditional `OptionMembers` run of kind (b).

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

**All-empty sites** follow the §3.2 matrix:
- generic, ML, Namespaces and link parse them;
- TableRelation and CalcFormula ERROR.

Each is pinned against an alc probe. Structural acceptance and compiler validity are recorded
separately: where the grammar accepts what alc rejects as syntax, it is recorded as
over-acceptance, as `RunPageLink = ;` already is (B5b, CLAUDE.md). The parser does not
validate.

**`OptionMembers` (kind (b)).** Today an opening `preproc_conditional_option_members` requires a
following ordinary member, and an entirely conditional comma run ERRORs (live parse). The
option-list production gains the entirely conditional form, with element conditionals carrying
their `,` exactly as the link list does, and blank slots preserved:
- leading `,`;
- consecutive `,,`;
- trailing `,`.

Every comma and every ordinal survives in the tree.

### 4.2 `;` after the last `#endif`

The run continues until the property's `;`, and arms may carry their own `;` (mixed placement).
The site is `prefix* core? suffix* ';'`, where `core` is a plain value, a group, or
`sequence = group (empty* group)+`.

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

An arm `;` in a non-last, non-terminated group still makes the boundary configuration-dependent
(§3.4). The tree is the sequence. The oracle refuses the configurations in which a later group
is active after an earlier arm's `;` (§5.3).

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

**Feasibility is gated by a spike, of grammar and lowering together.** Before the main grammar
task, two spikes are built.

**Families.**
- **Generic:** the disjoint terminated / non-terminated group states, the recursive
  witnesses, the empty rule and the sequence alias.
- **Link:** the separator rule against the element-conditional reading, under link
  precedence 6.

**Delayed decisions.** Both spikes must keep two readings alive until they are decided:
- sequence against list-element (the separator may sit in a later group);
- continuation against the end of the site.

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

**Kind (c) witnesses.** Each spike checks that the following yield no sequence and stay an
ERROR, rather than becoming a silent tree:
- `sorting(...)` then `where(...)` across groups;
- ML pairs across groups with `,`;
- a caption with `, Locked = true` across groups;
- comma-edge arms in non-list families.

**Lowering.** Each spike also runs the §5.3 lowering on its trees.

**Report.** STATE_COUNT, the generator-required conflicts, the trees, and the oracle records.
The remaining families follow only if both spikes are right.

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
- the entirely conditional two-entry list of §3.1, every configuration valid, for link,
  Implementation and `OptionMembers`;
- `OptionMembers` blank slots across groups: leading, consecutive and trailing `,`;
- the kind (c) shapes:
  - `SourceTableView` `sorting(...)` then `where(...)` across groups;
  - ML and Namespaces pairs joined by `,` across groups;
  - a caption with `, Locked = true` across groups;
- a bare-`;` arm, per family (§3, "No bare-`;` arms");
- the terminated-group-then-property example of §4.2;
- the action and assembly hosts for generic and ML values.

### 5.2 Fixtures

**`test/corpus/property_value_run_test.txt`.** The expectations are generated from
`tree-sitter parse` output, so every field is labelled. It holds:
- every §5.1 shape × family, including nested-empty, nested-prefix and nested-run cases at arm
  value sites;
- the terminated-group-then-property block (the property ends);
- the configuration-dependent boundary examples;
- the list-family runs under the separator rule (§3.1): no separator crossing a boundary →
  sequence; separators crossing boundaries, including the entirely conditional two-entry list
  of §3.1 → element conditionals, unchanged;
- the terminated-group-then-property example of §4.2, with the final standalone `;`;
- the kind (c) shapes as deliberate ERRORs owned by B13. They are listed in
  `tools/deliberate-negatives.txt`, with a note that they are valid AL whose structure is
  deferred, not invalid input.

Each tree is checked by hand against the flat tree of every configuration. A `bogus:` field
rename must fail the file, and the suite total must move by exactly the number of cases added.

**Preservation fixtures:**
- the TableRelation forms of §4.4;
- CalcFormula aggregates without `where`;
- a following conditional property block after a complete group;
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
- **invalid-config records** carry alc evidence.
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
