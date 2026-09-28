# Configuration-Consistency Oracle — Milestone 2 Design

Amends `2026-09-27-config-consistency-oracle-design.md` (the base spec). Everything
the base spec says still holds unless this file changes it. Section numbers such
as "base §3" refer to that file.

## Why milestone 2 changed

The base spec's milestone 2 covered the hard shapes: the split-procedure witness
matrix, report-brace ownership, and expression continuation. Its reason was to
de-risk the fragment design before the many simple handlers were written.

A census of special node types in the multi-configuration trees of production
code, taken 2026-09-28, shows where the unvalidated code actually is:

| Type | BC.History nodes | BCApps 29.0 nodes | State at milestone 1 |
|---|---|---|---|
| `preproc_conditional` | 2,226 | 3,410 | supported |
| `preproc_conditional_statement` | 646 | 1,569 | supported |
| `preproc_conditional_object` | 401 | 1,278 | unsupported |
| `preproc_conditional_actions` | 249 | 1,131 | unsupported |
| `preproc_conditional_fields` | 142 | 915 | unsupported |
| `preproc_conditional_var` | 353 | 657 | unsupported |
| `preproc_conditional_layout` | 155 | 274 | unsupported |
| `preproc_conditional_report` + `_rendering` | 6 | 227 | unsupported |
| `preproc_conditional_permissions` | 194 | 145 | unsupported |
| all `preproc_split_*` combined | about 150 | about 90 | mostly unsupported |
| `preproc_conditional_expression_tail` | 0 | 0 | unsupported |

Most production special nodes are plain conditionals whose arms are complete
units. The hard shapes are rare: expression tails occur nowhere in production,
and report-brace ownership occurs once, in BC 29.

**Decision (user, 2026-09-28): milestone 2 does both.** It covers the frequent
branch-select and list-run families, which validate production code, and the
base spec's hard shapes, which de-risk the design. It then runs the oracle over
production for the first time, with no gate.

The BC 29 grammar work of 2026-09-28 added 13 special types
(`docs/bc29-parse-gaps.md`). Several of them show only one configuration's
nesting. This milestone gives those a declared reading (P4), so their other
configuration cannot pass silently.

## Work packages

P1 comes first. P2 and P3 extend the registry and branch selection. P4 needs
P2's registry attributes. P5 needs the fragment machinery exercised by P3's
table-relation assembler. P6 needs all of the others.

### P1. Small fixes

1. **The BOM is trivia at any offset.** `compare.coverage` treats U+FEFF as
   trivia wherever it occurs, not only at offset 0. `grammar.js` declares it an
   extra (deferred-work item 6).
   - `scanner_single_read_dispatch_test.txt#3`, `CLEAN22=0`, turns from a
     discrepancy into a pass. This is the last discrepancy in the quick tier.
   - A new control puts a BOM between two statements. The reference parse must
     also treat it as trivia, and the configuration must pass.
2. **BCApps-29.0 joins the resolve sweep.** The resolver and single-configuration
   parse run over every `#if` file in `H:/Git/BCApps-29.0`, alongside BC.History,
   DC and BC 28.1. The base milestone-1 rule applies: zero
   `cannot-validate: resolver-*` and zero `reference-error` over flat production
   AL, or each one is investigated and classified.
3. **The 13 BC 29 types are classified.** Each gets a handler in this milestone
   or stays `unsupported`. An `unsupported` entry's registry comment names the
   milestone that handles it. The table in "Registry state at exit" below is
   the assignment.

### P2. Branch-select families

Each entry gains two hand-written attributes, and each is checked against its
rule in `grammar.js` before it is registered (base §3).

- **`arm`: the child kinds an arm may contain.** After selection, the engine
  asserts that every child of the chosen arm has one of these kinds. Any other
  kind is `lowering:arm-content`: the tree holds something the rule's author did
  not declare.
- **`policy`:** as in base §3 (`splice-repeat`, `single-slot`, `optional-slot`),
  plus `list-run` (P3).

Host slots still come from the `node-types.json` census and are classified by
hand. A new host slot fails the census until it is classified.

Members, all `splice-repeat` into the host's repeat slot:

| Type | Arm content (from `grammar.js`) |
|---|---|
| `preproc_conditional_object` | `namespace_declaration`, `using_statement`, objects, nested `preproc_conditional_object`. Spliced into `source_file` |
| `preproc_conditional_actions` | `_action_element` |
| `preproc_conditional_fields` | `field_declaration`, `attribute_item`, `modify_modification`, nested `preproc_conditional_fields` (the BC 29 family-C fix), via `_field_branch_items` |
| `preproc_conditional_keys` | `key_declaration`, `attribute_item`, nested `preproc_conditional_keys`, via `_key_branch_items` |
| `preproc_conditional_fieldgroups` | `fieldgroup_declaration`, nested `preproc_conditional_fieldgroups` |
| `preproc_conditional_var` | `variable_declaration`, `var_attribute_item` (item-8 fix) |
| `preproc_conditional_layout` | `_layout_element` |
| `preproc_conditional_layout_mixed` | `_body_element`, `_layout_element` |
| `preproc_conditional_report` | `_report_body_element` |
| `preproc_conditional_rendering` | `rendering_layout` |
| `preproc_conditional_case` | the rule's case-branch content |
| `preproc_conditional_labels`, `_query`, `_xmlport`, `_controladdin`, `_dataset` | each rule's own element set, read from `grammar.js` when the entry is written |

Nested conditionals need no special handling, because the engine recurses into
a selected arm.

Witnesses per type (base §5): the first arm, a later `#elif`, `#else`, no arm
selected, an empty arm, nesting, and identical content in two arms. Each type
also has one mutation that swaps its declared policy, which must trip
`lowering:policy`.

### P3. The list-run policy

`list-run` splices the active arm's items **and separators** into the host
list, and leaves the result for the comparison to judge. The comparable form
keeps anonymous tokens (`ir.py`), so commas and `;` are compared like any other
leaf.

- **Alternation assertion.** After splicing, the list must read item,
  separator, item. A doubled or missing separator is `lowering:list-separator`.
  The reference parse usually rejects such text first, because alc does. So
  this is a guard, not the main check.
- **Named rewrite `terminator-hoist`.** A permissions or table-relation arm may
  carry the property's own `;` (base §3, known exceptions). After splicing, a
  `;` at the end of the list moves to the parent property, after its `value`
  field, which is where the reference parse puts it. This contract alone may
  make that edge change.
- **Assembler `else-relation-join`.** A table-relation arm may select an
  `else_table_relation_fragment`, which completes an earlier relation. It
  lowers to a `RelationContinuation` fragment, and the enclosing
  `table_relation` value consumes it. A fragment that reaches anything else is
  `unconsumed-fragment` (base §3).

Members: `preproc_conditional_permissions`, `preproc_conditional_arguments`,
`preproc_conditional_list_elements`, `preproc_conditional_where`,
`preproc_conditional_link_values`, `preproc_conditional_option_members`,
`preproc_conditional_table_relation`.

Mutations, per member:
- dropping a separator must trip `list-separator`;
- for the two terminator carriers, leaving the `;` inside the list must trip
  `structure`.

### P4. One-reading contracts

Some rules cover text whose nesting crosses the `#if` ranges. No properly
nested tree can hold both configurations, so each of these rules shows one of
them. A new registry attribute, `reading`, names the configuration class the
tree shows, for example `arm:if` or `arm:else`.

- **Configurations of that reading** lower through the type's handler as
  normal.
- **Every other configuration** gets `cannot-validate: one-reading:<type>`. It
  is counted and reported, never a pass.

| Type | Reading |
|---|---|
| `preproc_split_container_reopen` | `arm:if` |
| `preproc_split_block_end_in_else` + `preproc_split_block_close_after_endif` | `arm:else` |
| `preproc_split_else_begin_over_endif`, **widened shapes only**: more than one `end` before the `else`, or an `if … then begin` chain after it | `arm:inactive` (its tail's single `end` is the host block's in the configuration where the arm is not selected; the rule comment says so) |
| `preproc_split_open_statement` | a configuration whose active arm opens with `else` is one-reading: the tree shows that `else` as the next sibling of a complete if or case, not as its else branch. Configurations whose active arm is a complete prefix are milestone 3's (see "Registry state at exit") |

The base shape of `preproc_split_else_begin_over_endif`, `#if end else begin …
#endif … end`, is **not** one-reading. It is replay 1's shape, and it lowers in
both configurations through the P5 assembler `else-begin-over-endif`.

Controls, per member:
- a positive control that passes in its reading;
- a mutation that declares the wrong reading, which must turn that pass into a
  discrepancy.

`preproc_split_table_field_open` needs no `reading`, because its other
configuration is invalid AL (the rule's comment gives alc's verdict). A fixture
pins that the other configuration surfaces as
`cannot-validate: reference-error`, never as a discrepancy.

### P5. Hard shapes (the base spec's milestone 2)

1. **Split-procedure witness matrix.** The existing `split_procedure` assembler
   is run over every tail form in `_procedure_tail`: regular,
   `[;] pragma-only* body`, `preproc_split_procedure_body` (including the
   `#else` statements added 2026-09-28), `preproc_split_complete_body`, and
   trigger hosts, which share the tail since 2026-09-28. No code changes unless
   the matrix finds something.
2. **Assembler `report-brace-owner`.** The one production site is BCApps 29.0
   `Layers/GB/BaseApp/Sales/History/SalesShipment.Report.al`. At line 536,
   `preproc_split_report_dataitem_open_over_endif` opens an outer dataitem in
   one configuration. At line 580, the inner dataitem's `}` sits inside an `#if`
   (`preproc_split_report_brace_close`). The two configurations' brace depths
   differ by one from line 541 to line 590, then reconverge. The two nodes are
   one construct.
   - The open node lowers to a `DataitemOpen` fragment and the brace node to a
     `BraceClose` fragment. The assembler consumes both.
   - Where the open arm is active, the outer dataitem exists, and the inner one
     closes at the arm's brace.
   - Where it is not, the outer dataitem dissolves. Its body elements after the
     inner dataitem become the inner dataitem's, and its `}` becomes the
     inner's.
   - The only edge change allowed is the named rewrite
     `report-brace-owner`.
   - A `BraceClose` without its `DataitemOpen` is `unconsumed-fragment`.
   - Fixtures: the GB site's shape reduced, a variant with an `#elif`, and a
     hand-built bad tree with the trigger left in the outer dataitem, labelled
     as hand-built.
3. **Expression continuation.** Hosts: `preproc_conditional_expression_tail`
   and `preproc_operand_prefix`.
   - The base expression's unparenthesised binary chain is flattened into an
     operand/operator list, together with the active arm's continuations and
     those after `#endif`. Operands are flattened too: the parser may have
     grouped `* 2 + 3` inside one operand, which is only right after
     recomposition.
   - The list is recomposed with a **hand-written precedence table**, taken from
     the compiler-verified groupings in `test/corpus/operator_precedence_test.txt`
     (AL is Pascal-derived: comparisons bind looser than `and`/`or`/`xor`),
     never from the grammar's `prec()` values (base §3). The
     levels, tightest first, are the ones in that fixture's header: unary
     (`not`, `-`, `+`); `*`, `/`, `div`, `mod`; `+`, `-`; `in`, `is`, `as`;
     `and`; `or`, `xor`; the comparisons. All binary levels are
     left-associative. A parenthesised expression is an atom. *(Corrected
     while planning: an earlier draft of this line put `and` with `*` and
     `or`/`xor` with `+`, which is Pascal's ladder, not the one alc
     measured.)*
   - **Self-test:** every grouping in `test/corpus/operator_precedence_test.txt`
     is flattened and recomposed, and must equal its fixture tree. All 18 cases
     must pass.
   - The replay-4 HEAD control turns from a strict xfail into a pass.
4. **Assembler `else-begin-over-endif`,** for the base shape of
   `preproc_split_else_begin_over_endif`
   (`if C then begin A; #if X end else begin B; #endif C; end;`).
   - Where the arm is not selected, the node lowers to its tail: the host block's
     statements continue with the tail's statements, and the tail's `end` closes
     the host block.
   - Where the arm is selected, the host block ends at the arm's `end`. The
     arm's `else begin` becomes the `else_branch` code_block of the `if_statement`
     that owns the host block. The arm's statements, then the tail's, form its
     body, and the tail's `end` closes it.
   - The only edge change allowed is the named rewrite `else-begin-over-endif`.
   - A host block not owned by an `if_statement`'s `then_branch` is
     `lowering:policy`.
   - The widened shapes are one-reading (P4).
5. **Assembler `var-tail-merge`,** for `preproc_split_var_section_tail`. The
   active arm's `variables` append to the `var_body` of the preceding sibling
   `var_section`. The arm's body elements become siblings after that section.
   This is the only edge change allowed.
6. **Replays 1 and 6** (base §5). Parsers are built from the commits just before
   each fix. Each replay must be caught with its expected kind, with no earlier
   `cannot-validate` masking it. Replay 6 still does not count as evidence for
   the silent class (base §5).

### P6. First production run, with no gate

This is the base milestone 5's first stage, "a run over the corpora with no
baseline and no gate, recorded", brought forward. P2 to P5 are what make it
meaningful.

- `python -m tools.config_oracle run --tier full` over BC.History, BCApps-29.0,
  DC and BC 28.1.
- Recorded in the milestone results document, per corpus:
  - configurations checked, pass, discrepancy, and `cannot-validate` by reason;
  - elapsed time and peak memory, which set the full tier's time budget.
- Every discrepancy is clustered by `(check, kind, special type)` and triaged
  as one of:
  - **(a) grammar defect.** Fixed in its own commit, with a fixture, an alc
    probe in every configuration, tree-harness verification, and the error
    count in the commit message. This is how item 8 was handled.
  - **(b) oracle defect.** Fixed, with a regression fixture.
  - **(c) accepted.** A reason is recorded, for example a declared one-reading
    type.
- No baseline file and no gate. Those are milestone 5's.

## Registry state at exit

Types handled in this milestone:

| Package | Types |
|---|---|
| P2 | object, actions, fields, keys, fieldgroups, var, layout, layout_mixed, report, rendering, case, labels, query, xmlport, controladdin, dataset |
| P3 | permissions, arguments, list_elements, where, link_values, option_members, table_relation, `else_table_relation_fragment` |
| P4 | `reading` declared on the types in the P4 table |
| P5 | split_procedure (matrix), report brace pair, expression_tail, operand_prefix, split_var_section_tail, split_else_begin_over_endif (base shape) |

Everything else stays `unsupported` with milestone 3 named in its registry
comment. That includes the whole split-if family, which shares one "prefix
plus continuation" assembler: `preproc_split_if_statement`,
`preproc_split_if_else_statement`, and the complete arms of
`preproc_split_open_statement`. Also in milestone 3: `preproc_split_key`,
`preproc_split_modify`, `preproc_split_permissions_property`,
`preproc_split_table_field(_open)`, `preproc_split_field`,
`preproc_split_declaration`, and the remaining split types.

## Testing rules

Unchanged from milestone 1:

- Every handler has a witness matrix (base §5). A handler that has run only on
  inactive content has not been tested.
- Every contract and assembler has a mutation that trips it and nothing else.
- The comparator mutations must still fail as before.
- Replays 2 to 5 stay caught.
- `tools/config_oracle/tests` passes, and the census reports no problems.

## Exit, demonstrated

- The quick tier has zero discrepancies.
- Replays 1 to 6 are caught with their expected kinds, and the replay-4 HEAD
  control passes.
- The precedence self-test passes all 18 cases.
- Every P2 to P5 type has a complete witness matrix and its mutations.
- The resolve sweep over all four corpora is clean, or each exception is
  classified.
- The P6 run is recorded, every cluster is classified, and every (a) is fixed.
- `unsupported` remains only on types assigned to milestone 3.

## Out of scope

- Milestone 3's types (see "Registry state at exit").
- A baseline or a gate over production. Those are milestone 5's.
- EDocumentDE's split layout-open (`docs/deferred-work.md` item 10), which has
  no grammar rule to lower.
- A configuration-aware parse. Item 10 records it as the general answer to
  crossing constructs. It is an architecture change, and a different project.
