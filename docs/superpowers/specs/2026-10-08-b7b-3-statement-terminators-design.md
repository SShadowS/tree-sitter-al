# B7b-3: statement terminators, case separators and the move header (design, rev 3)

Roadmap B7, sub-project B7b-3 (user decisions 2026-10-08: B7b-3 before B7b-2 and B7b-1b..g, because
ordering principle 3 puts silent wrong trees first; `call_statement` stops owning its `;`, accepting
that a recovered identifier in a tree with errors may become a `call_statement`; scope = parenless
calls, case-branch separators and the move fixed `;`). Input: the B7a matrix
`docs/b7-separator-continuation-matrix.md` (families `statement-terminator` and `move-modification`),
probes `tools/alc_probe/cases/b7-audit/`, deferred items 40 and 46. Rev 1 folded in three gpt-6.1-sol
design rounds; rev 2 adopts its spec review (15 findings), rev 3 its re-review (9 findings). Mapping
in section 10. Status: implemented on branch `feat/b7b-3-terminators`; where it differs from this text, the
"Rev 3 execution amendments" at the end govern.

## 1. Problem

Three defects share one cause: a `;` (or the move header's fixed `;`) that the grammar binds to a
fixed position cannot come from an `#if` group or be absent.

1. **Parenless calls (SILENT, and flat production).** `call_statement` (`grammar.js:5652-5655`) is
   `prec(13, seq(field('function', identifier | quoted_identifier), ';'))`; it owns its `;`. Today a
   statement's `;` is owned by one of these, per host route: the `_statement` wrapper
   (`seq($._statement_inner, optional(';'))`, ~5594-5615); `case_branch` (~6147-6153); the guard
   sequence of `_preproc_guard_block` (~5152-5155); or a self-terminating form: `call_statement`,
   `preproc_split_call_statement` (~5380-5390) and `empty_statement`, which IS a `;`. B7b-0's
   arm-terminator lowering covers the `_statement` route. A parenless call whose `;` sits in an `#if`
   arm, follows an empty group, or is absent degrades to a bare `identifier` expression statement:
   - `if Ok then Bar #if X ; #endif` gives `then_branch: identifier`; flat `if Ok then Bar;` gives
     `then_branch: call_statement`.
   - Flat code without any `#if`: `begin SetUserRegionalSettings end` (last statement, no `;`) and
     `IF C THEN AddLineAmountToTotals ELSE X;`. Census over the four corpora (2026-10-07): 3,367
     `call_statement` nodes and 117 bare-name statements, all real parenless calls, in DC, BC28.1 and
     BCApps (0 in BC.History, which has no parenless calls).
   - `Order;` arrives through `_value_start_keyword_name` and is never a call (deferred item 40).
   - Matrix: `statement-terminator` SILENT 213 cells (`tools/b7_audit/tests/test_silent.py`, the
     `occ:call_statement:0.1@if_statement#*` and `@case_branch#first-replace` witnesses).
2. **Case-branch separators (GAP / OVERACCEPT).** `case_branch` is `pattern ':' body optional(';')` and
   `preproc_conditional_case` arms hold only branches (~6132-6139), so a `;` in a group after a branch
   ERRORs even for an assignment (`case I of 1: I := 2 #if X ; #endif end;`). Matrix: GAP 84,
   OVERACCEPT 33 (`occ:empty_statement:@case_branch#trail`).
3. **Move header (GAP).** `moveArgs` (`grammar.js:96-103`) is `'(' target ';' strictListBody(move_elements) ')'`;
   a group replacing the target or supplying the fixed `;` ERRORs. Matrix: GAP 72 cells, 0 production
   sites, placements adjacent-compl, elif, first-replace, nested, sep-before-end (MIXED: `!X` AL0104,
   `X` accept), sep-only.

## 2. Phase 0: alc evidence first

No grammar work starts before these verdicts are recorded under `tools/alc_probe/cases/b7b3/`, each
with `// expect:` and `// source:` headers, run with
`MSYS_NO_PATHCONV=1 python -m tools.alc_probe run tools/alc_probe/cases/b7b3 --check`, split AND
resolved-flat, every symbol assignment. Syntax acceptance is recorded separately from semantic
rejection (AL0104/AL0107 versus AL0171-style) and from oracle status.

- **Calls:** `Bar end`, `Bar else`, `repeat Bar until C`, `Order;`, `Table;`, quoted names;
  `continue` before `;` / `end` / `until` / directives; `Continue(`, `Continue.`, comments between
  `Continue` and `(`.
- **Case separators:** bodies {assignment, parenless call, parenful call, block, nested if,
  `asserterror`} × {0, 1, 2 separators before `end`, before another branch, before the case `else`};
  `case I of ; end`; `1: ;`, `1: ;;`, `1: X;;`; a lone-`;` group after a terminated and after an
  unterminated branch; an empty group (and a nested empty group) before an outside `;`; nested,
  complementary-adjacent and independent groups; groups holding both a `;` and whole branches; the
  else-ownership probe `1: if C then Foo #if X ; #endif else Bar;`.
- **Move header:** the six GAP placements; the spanning group `#if X T1; A #else T2; B #endif`; the
  comma continuations `T #if X ; A #endif , B` and `#if X T; A #endif , B` (comma inside and outside
  the group); the cross-group role example of section 5.3; target-only and `;`-only groups next to an
  empty group; `moveafter(T;)`; a group holding two targets; leading/trailing-comma fragments;
  independent groups; quoted and contextual names; comments at every boundary.

**Rule:** a verdict that contradicts sections 3-5 comes back to the user as a spec amendment before
any grammar work. Section 4.2 rule 3 is provisional until the case verdicts are in.

## 3. Parenless calls

### 3.1 Shape

```js
call_statement: $ => field('function', choice(
  $.identifier,
  $.quoted_identifier,
  alias($._value_start_keyword_name, $.identifier),   // Order / Table (deferred item 40)
)),

_expression_statement: $ => prec(-1, reserved('code_names', choice(
  $.call_expression,
  $.member_expression,
  $.call_statement,
))),
```

`call_statement` is "a bare name in statement position". It has no `;` and no precedence of its own;
it is reached only through `_expression_statement`, which stays NOT inlined and keeps B6's `prec(-1)`
and the `code_names` reserved set. The intermediate reduction and the reserved-word behaviour are
measured (section 3.6 boundary fixtures). If `code_names` no longer rejects operator words under the
wrapper, `reserved()` moves onto the choice inside `call_statement`.

### 3.2 Deletions (one commit)

- The `call_statement` arm of `_statement` (~5611).
- The `call_statement` arm of `fieldedStatement()` (`grammar.js:160`).
- The `field('then_branch', $.call_statement)` arm of `if_statement` (~5932). The
  `field('then_branch', $.empty_statement)` arm stays: an empty statement still consumes a `;`.
- The comment blocks that justify `;` ownership are rewritten, not left stale.

Dangling else keeps its existing structure: one seq with an optional else, `prec.right`, and the
dynamic precedence on else attachment are unchanged.

### 3.3 The other self-terminating route and the guard

- **`preproc_split_call_statement`** (~5380-5390) also owns its final `;`. It is externalised: the rule
  ends at `)`, and the `;` is then owned by whatever host route encloses it (`_statement`, or the case
  branch). 0 production sites. The oracle keeps it registered `unsupported`
  (`tools/config_oracle/contracts.py:392`); no assembler is added.
- **`_preproc_guard_block`** (~5152-5155) keeps its existing ownership: its sequence
  `seq(prec(2, $._expression_statement), ';')` owns each guard statement's `;`. No change; a parenless
  guard call becomes a `call_statement`.
- **`empty_statement`** remains a self-terminating form; nested bodies may still consume a `;`
  through it (`fieldedStatement`, ~159-165).

### 3.4 Result

One shape for every parenless call: `Bar;`, `Bar` before `end` / `else` / `until`, `Order;`, and
`Bar` followed by a group that holds or precedes the `;`. Deferred item 40 closes.

### 3.5 Queries

`queries/highlights.scm` gains `(call_statement function: (identifier) @function.call)` and the
quoted form; `queries/tags.scm` gains a matching `@reference.call` capture. Both get query fixtures.
Today parenless calls are neither highlighted nor tagged (only `call_expression` is captured,
`highlights.scm:750-756`, `tags.scm:316-322`).

### 3.6 Pinned fixtures

Every expected tree in this sub-project that matters for its fields is **hand-written** from the
intended structure, then compared with the parser's output; never generated by `tree-sitter parse` or
`-u` (B7b-1 spec 4.1/7 precedent). Each is proven able to fail by renaming one field to `bogus:`.

- The dangling-else trio, each with call, assignment, block, loop and `asserterror` bodies, with all
  `then_branch` / `else_branch` / `body` fields: `if A then if B then Foo else Bar;`,
  `case I of 1: if C then Foo; else Bar; end;`, `case I of 1: if C then Foo else Bar; else Baz; end;`.
- `repeat Bar until C;`, `Bar end`, `Order;`, `"My Proc";`, a parenless guard call.
- Boundaries, complete: `Bar := 1;`, `Bar += 1;`, `Bar.Baz;`, `Bar(1);`, `Bar[1] := 2;`, an operator
  word after a name (`code_names`).
- `continue` stays `continue_statement` before `;` / `end` / `until` / directives; `Continue(` and
  `Continue.` stay calls through `CONTINUE_AS_IDENTIFIER`.
- `preproc_split_call_statement` in then, else, loop and case positions, with `else` right after `)`
  AND with `;` before `else`.
- Item 40's pin in `test/corpus/expression_statement_test.txt` flips.

## 4. Case-branch separators

### 4.1 Placement

In the split tree, a conditional case group that holds a `;` or whole branches is a sibling
`preproc_conditional_case` in `case_body`; an arm's lone `;` is an `empty_statement`, the reading
B7b-0 gives statement blocks. **Exception:** a directive-only empty group between a branch body and
that branch's own `;` is a decoration inside the branch (rule 4.2.2), not a sibling. In the configured
tree, a selected `;` is appended to the immediately preceding case branch, outside its `body` field.
That moves a `;` into a different parent, which B7b-0 never does; section 6.2 is the contract.

### 4.2 Grammar

1. `preproc_conditional_case` arms accept `case_branch`, `empty_statement` and a nested
   `preproc_conditional_case` (arms are not recursive today), plus the existing optional
   `case_else_branch`.
2. **Decoration.** A hidden rule `_case_empty_group` is a directive-only group whose arms hold only
   nested decorations (recursively empty, possibly with `#elif`/`#else`). EVERY occurrence, the
   recursive ones included, goes through one helper, so nested groups stay distinct visible nodes:
   ```js
   function caseEmptyGroup($) { return alias($._case_empty_group, $.preproc_conditional_case); }
   _case_empty_group: $ => seq(
     $.preproc_if,
     repeat(caseEmptyGroup($)),
     repeat(seq($.preproc_elif, repeat(caseEmptyGroup($)))),
     optional(seq($.preproc_else, repeat(caseEmptyGroup($)))),
     $.preproc_endif,
   ),
   ```
   It may stand only unfielded, immediately before a branch's own `;`, in exactly three hosts:
   `case_branch` (`pattern ':' body optional(seq(repeat(caseEmptyGroup($)), ';'))`),
   `preproc_split_case_branch` and `preproc_split_case_extended` (the same change to their
   `optional(';')`). Empty groups after a branch with no `;` following stay sibling
   `preproc_conditional_case` nodes. A `;` after empty groups therefore needs a branch before it by
   construction: no loophole at the start of `case_body` and no extra `;` per adjacent group. A fixture
   pins a nested decoration with distinct inner and outer nodes. The visible type is shared, so neither
   `node-types.json` nor a query can tell a decoration from an ordinary group: the oracle checks it in
   context (section 6.2).
3. No general bare `;` in `case_body`: `case I of ; end` and flat `1: X;;` keep today's behaviour
   unless Phase 0 shows alc accepts them (then: spec amendment).
4. A form invalid in every configuration that now parses (e.g. `1: X; #if A ; #endif` if alc rejects
   `;;`) is a classified over-acceptance, deferred item 44 precedent: the parser does not track
   separators per arm.

### 4.3 Competing derivations

Rule 4.2.2 separates sibling and decoration ownership, but other derivations remain and are measured,
never assumed away:

- **Optional bodies.** In `1: asserterror #if X #endif ;` the empty group can be the `asserterror`
  body (`grammar.js` ~5469-5482) or a decoration after a bodyless `asserterror`. **Required split tree:**
  the decoration reading, `case_branch(pattern, body: asserterror_statement, preproc_conditional_case, ";")`.
  Both readings configure to the same flat text; the fixture pins the required one with hand-written
  fields. If generation cannot produce it without a new conflict, the plan's Phase 3 spike reports the
  measured winner and the spec is amended before going on.
- **Split case rules.** The new arms share the `#if` prefix with `preproc_split_case_branch` and
  `preproc_split_case_extended` (~6160-6195). Discriminating fixtures: a group of complete branches; a
  group of patterns only (`#if … patterns … #endif shared-pattern: body`); a group ending in a header
  (`#if … branches … header: #endif shared-body`). Each also with a nested empty group and with a `;`
  group just before the shared suffix.
- Conflicts and states are measured, never added up front.

### 4.4 Else ownership

`1: if C then Foo #if X ; #endif else Bar;` reads `then Foo; else Bar;` with X (the else goes to the
case) and `then Foo else Bar;` without (the else goes to the if). The tree shows one reading. If alc
accepts both configurations, the oracle refuses the other explicitly as `lowering:one-reading` (B12
debt, classified); never a silent pass. If alc rejects one configuration, that configuration is
classified invalid; this is not an all-configurations over-acceptance. A fixture pins the tree; the
refusal is recorded beside it.

## 5. The move header

### 5.1 The group and the routes

The group is generated by the B7b-1 generator with a mixed separator; its arm language is therefore
exactly B7b-1's fragment model (`grammar.js:106-150`), unchanged:

```js
...strictConditionalList('move_args', $ => $._identifier_or_quoted, choice(';', ',')),
// yields _move_args_e, _move_args_t, preproc_conditional_move_args, _move_args_b, _move_args_r:
//   preproc_conditional_move_args: preproc_if [B] (preproc_elif [B])* [preproc_else [B]] preproc_endif
//   _move_args_b:  sep [R] | R            -- an arm body: optional leading separator
//   _move_args_r:  E (sep E)* [sep]       -- a run, optional trailing separator
//   _move_args_e:  name [T] | T           -- a name with an optional trailing group, or a group
//   _move_args_t:  G [E]                  -- a group followed by an optional further E
//   sep = ';' | ','                        -- either separator, anywhere, inside the conditional route only

function moveArgs($) {
  const sep = choice(';', ',');
  return seq('(', choice(
    // 1. Flat / B7b-1 route, unchanged: the element region stays required.
    seq(field('target', $._identifier_or_quoted), ';', ...strictListBody($, 'move_elements', ',')),
    // 2. A raw target, then a group (the witness), then any further run.
    seq(field('target', $._identifier_or_quoted), $._move_args_t, repeat(seq(sep, $._move_args_e))),
    // 3. A group first (spanning or replacing the target), then any further run.
    seq($._move_args_t, repeat(seq(sep, $._move_args_e))),
  ), ')');
}
```

- **Arm language, explicit:** an arm is empty, or an optional leading `;`/`,` followed by an optional
  run of names and nested groups separated by `;`/`,`, with an optional trailing `;`/`,`. Two raw names
  are never adjacent without a separator; two raw separators are never adjacent. Nesting is recursive.
  The grammar does not check which separator stands where: that is per-configuration validation
  (section 6.3).
- **Routes are disjoint at their first tokens.** Route 1 is `name ;`, route 2 is `name #if`, route 3
  is `#if`. Flat `moveafter(T;)`, `moveafter(T, B)`, `moveafter(T; B; C)` keep ERRORing: the mixed
  separator and any missing content are reachable only after a group.
- **Comma continuation:** `T #if X ; A #endif , B` (route 2) and `#if X T; A #endif , B` (route 3)
  parse because the tail repeats `sep E` with `sep` including `,`.
- Route 1 keeps B7b-1's `preproc_conditional_move_elements`; routes 2-3 use only
  `preproc_conditional_move_args`, so two visible group types never compete for the same text.
- Directive-only empty groups are ordinary (empty-armed) `preproc_conditional_move_args` nodes on
  routes 2-3, and `preproc_conditional_move_elements` on route 1, as in B7b-1.
- **Positive split-tree fixtures (hand-written):** the six placements, the spanning group, both comma
  continuations, `G(T; A,) B`, `T G(;) A G(, B)`, `T G(; A,) B`, nested and `#elif` arms.
- **Negative fixtures (`:error`):** flat `moveafter(T;)`, `moveafter(T, B)`, `moveafter(T; B; C)`,
  `moveafter(T)`, `moveafter()`.
- **Deliberately admitted (classified, section 5.4):** a conditional-route input whose every
  configuration is not `name ; name (, name)*`, e.g. `T #if X , A #endif` (a `,` where the `;` belongs).
- Hidden partitions between the group and the tail are measured (conflicts, identical trees, scaling).
  New separator occurrences in `_move_args_b` / `_move_args_r` / the route tails get B7a registry rows
  (section 8.2).

### 5.2 Fields

Frozen policy:

- Route 1: unchanged, `target` and `element` (B7b-1).
- Route 2: its first raw name keeps `target` (its role is structurally known).
- Every other name on routes 2-3, inside or outside a group, is **unfielded**.
- The host's direct `target` field becomes `required: false` (route 3 has none);
  `tools/check-field-types.py` gets that aggregate invariant. `node-types.json` shows the union of the
  routes, so "no `element` on routes 2-3" and "only route 2's first name is `target`" are checked per
  instance: in the oracle's route validation (6.3) and in the hand-written fixtures.

### 5.3 Why other roles cannot be static

```al
moveafter(
#if X
    T;
#endif
#if Y
    A
#else
    B
#endif
#if not X
    ; C
#endif
)
```

With X, `A`/`B` are elements; without X, the target. No fixed parent-child field is right in both
configurations. In the configured tree the oracle assigns `target`/`element` to the unfielded names
after validation (section 6.3); the CHANGELOG states that on routes 2-3 the split tree carries roles
only where they are structurally known.

### 5.4 Over-acceptance

The grammar does not count separators per arm; a group whose arm lacks the `;` still parses. alc
decides each configuration: an over-acceptance that fails in every configuration is classified (item 44
precedent); per-configuration invalidity is recorded as such. The precedent covers classified
conditional over-acceptances on routes 2-3, never widening the flat grammar.

## 6. Config oracle

### 6.1 Calls

A call's `;` is now owned by its host route like any statement's, so B7b-0's arm-terminator
normalisation applies on the `_statement` route and section 6.2 on the case route.
`preproc_split_call_statement` stays `unsupported`.

### 6.2 Case separators

- **Termination** is defined by the branch's own direct `;`: an anonymous `;` child of `case_branch`
  (or of a lowered split-case branch), outside `body`. A `;` inside the body never counts.
- **Marking:** every `empty_statement` that is a direct arm child of a `preproc_conditional_case` in a
  case run is marked `CASE_SEMI`, including arms that also hold branches, at any nesting depth. The
  marker is case-specific, never the statement-block `ARM_SEMI`, and survives nested selection.
- **Normalisation** runs once the complete enclosing case run is selected and flattened, in source
  order. For each marked `;`, only the immediately preceding surviving item counts: an unterminated
  `case_branch` gets the `;` appended (outside `body`; its span and its ancestors' spans recomputed from
  their retained children and token offsets); a terminated branch, an `empty_statement`, a
  `case_else_branch` or the start of the run: no attachment, and never a search further back. The first
  attachment is visible to the second. Each attachment is logged as rewrite `case-terminator-attach`.
- **Decorations** (rule 4.2.2) are deleted by selection: they emit no node and no separator and never
  carry `CASE_SEMI`. Before deletion, EVERY arm, inactive arms included, is validated as recursively
  directive-only; anything else (a branch, a `;`, a statement) is a representation error, never
  discarded. The registry has one handler per type, so `preproc_conditional_case` gets one
  context-dispatched handler: under `case_body` or a group arm it is the ordinary branch-select; directly
  under `case_branch`, `preproc_split_case_branch` or `preproc_split_case_extended`, immediately before
  the host's own `;`, it is the decoration handler.
- **Split-case wrappers:** attachment inspects the lowered result, so a lowered
  `preproc_split_case_branch` / `preproc_split_case_extended` counts as a `case_branch`. Where a wrapper
  is not lowerable today, the run keeps today's refusal.
- **Registry:** `contracts.py` (~283-310) gets the recursive host, `empty_statement` as an allowed arm
  member, and the three decoration hosts (`case_branch`, `preproc_split_case_branch`,
  `preproc_split_case_extended`, plus decoration-in-decoration) through the context-dispatched handler. The existing
  `case_else_branch` exclusion stays explicitly: a conditional `case_else_branch` remains cannot-validate
  debt, out of scope.
- **Else ownership:** the check is driven by the selected separators and never reads the reference
  parse (`engine.py:14-16`). Pinned both ways: the represented configuration lowers correctly; the other
  valid one is refused as `lowering:one-reading`.
- **Mutation tests:** `;` left beside the branch; `;` attached across a terminated branch; `;` placed
  inside `body`; a `;` inside the body counted as termination; nested or decoration provenance lost; a
  decoration emitting a `;`; a branch or `;` injected into an INACTIVE decoration arm and silently
  dropped; missing refusal. Leaf accounting (`engine.py:315-325`) holds: every leaf
  emitted exactly once, body fields unchanged.

### 6.3 Move header

One move-interior adapter replaces the move-elements adapter (`conditional_lists.py` finds the `;` as
a direct host child and `HOST_FAMILY` allows one family per host, ~106-120, 201-207).

- **Dispatch by host kind:** the adapter runs for every `movefirst/movelast/moveafter/movebefore`
  modification, whether or not it holds a group, so a host holding only `preproc_conditional_move_args`
  cannot bypass validation (`engine.py:385-393` today dispatches on group presence).
- **Before selection:** identify the route (1, 2 or 3); validate the parenthesised region, group and arm
  containment, order, allowed node types per route, and the field policy of section 5.2 (route 1's and
  route 2's existing fields are checked as they stand, never relabelled).
- **After selection:** flatten both group types in source order and require `name ; name (, name)*`.
  Only then assign `target` / `element` to the configured names. Reject an extra target, a duplicate
  `;`, a missing `;` and bad commas; never repair by relabelling.
- **Empty element region:** stays on the reference-error path while flat `T;` stays an error (B7b-1
  rev 2 amendment: cardinality is evidence, not lowering policy).
- **Mutation tests:** a second target silently turned into an element; a duplicate `;` ignored; a wrong
  field silently corrected; a group-only host bypassing validation; a `;`-bearing group checked against
  the old direct-`;` region; wrong group ownership or arm containment; reordered or lost leaves; a
  configuration-dependent role.

### 6.4 Expected statuses

Two kinds of fixture, held to different rules:

- **Repair fixtures** (the GAP and SILENT shapes this sub-project fixes: conditional call terminators,
  case separators and decorations, move routes 2-3). Every alc-accepted configuration must PASS
  lowering and comparison. The only permitted refusal is the alternate reading of section 4.4
  (`lowering:one-reading`). No blanket `unsupported` exception.
- **Representation and preservation fixtures** (shapes pinned for their split tree whose host the
  oracle does not lower today: `preproc_split_call_statement`, `preproc_guarded_statement` with a
  parenless guard call, split-case wrappers that are not lowerable, a conditional `case_else_branch`).
  Each keeps today's refusal, frozen individually by name and reason.

**Where statuses live.** For corpus fixtures: `tools/config_oracle/fixture-classes.tsv`, whose quick-tier
check already fails on an unclassified refusal and on a stale row; each permitted refusal above is one
explicit row. For manifest cells: the B7b-3 manifest gains an `expected_oracle` column (the oracle status
per configuration, e.g. `X=0:pass,X=1:pass` or `X=0:pass,X=1:lowering:one-reading`), checked by
`manifest --check` against a fresh oracle run on the cell. Any other refusal or new debt classification
fails. `python -m tools.config_oracle replay` and the mutation tests run in the gate.
alc verdicts stay separate from oracle outcomes, and a classified refusal is never counted as validated
(`CLAUDE.md`, config oracle gate 0); assertion-closed matrix results are not a substitute for
configured validation.

## 7. Production delta

### 7.1 Two separate gates

- **Production preservation:** previously clean production trees in the four corpora may change only
  by the classes of 7.2. Any unexplained change fails.
- **Repair validation:** formerly erroneous inputs (the GAP shapes, the new case and move forms) are
  validated by hand-written expected trees in `test/corpus/` (section 3.6), never by a delta class.

### 7.2 Classes (composable atomic edits)

A changed file is explained when its old tree is transformed into its new tree by a sequence of these
edits; each edit is checked structurally, not by diff text:

- **E1 call-terminator-out.** A `call_statement` loses its last child, an anonymous `;`; its
  `function` child keeps its type, grammar symbol, span and field. The call's new end is the end of
  `function`. Every ancestor whose old end was that `;`'s end is recomputed from its retained children.
  The `;` (same byte span) becomes a child of exactly one approved owner: the `_statement` route's
  enclosing parent, right after the outermost such ancestor; or the enclosing `case_branch` (or split
  case wrapper), as its own `;`.
- **E2 split-call-terminator-out.** `preproc_split_call_statement` loses its final anonymous `;`; every
  other child (the directive, prefix and shared-argument children) is retained unchanged; its new end is
  its `)`. Ancestors and the `;` follow E1's owner rule. 0 expected sites.
- **Extras under E1/E2.** A comment or other extra between the callee (or `)`) and the `;` keeps its
  type, byte span and source order. Exactly two placements are permitted: unchanged parent, or moved to
  the `;`'s new parent immediately before the `;`. Pinned by comment fixtures (line and block comment,
  one each for E1 and E2). Any other extra reparenting is not explained.
- **E3 bare-name-wrap.** A name gains a `call_statement` parent with the same span; the name keeps its
  grammar symbol, span and original parent field, which moves to the `call_statement`; the new inner edge
  is `function`. Eligible slots, frozen (parent type, slot):
  | parent | slot |
  |---|---|
  | `statement_block`, `preproc_conditional_statement` arm | unfielded statement child |
  | `if_statement` | `then_branch`, `else_branch` |
  | `while_statement`, `for_statement`, `foreach_statement`, `with_statement`, `repeat_statement` | `body` |
  | `case_branch`, `preproc_split_case_branch`, `preproc_split_case_extended`, `case_else_branch` | `body` |
  | `preproc_guarded_statement` (the hidden `_preproc_guard_block` sequence) | unfielded statement child; `then_branch` |
  Never eligible: a case pattern, any `condition` / `expression` / `left` / `right` slot, any other
  `body` (declarations, triggers, code blocks). The plan derives this table from the grammar's actual
  `_expression_statement` routes and fails if a route is missing from it. Admitted texts: any
  `quoted_identifier`; an `identifier` whose text is outside the frozen keyword table (the `code_names`
  set, the statement keywords `if then else begin end case of repeat until while do for to downto
  foreach in with exit asserterror`, and `true false`); `Order` / `Table` (case-insensitive) through the
  `_value_start_keyword_name` route, by explicit whitelist. `is` and `as` are not in the table: alc
  accepts them as names (B6), so they are eligible.
- **Not admitted:** an `else` (or any other keyword text outside the whitelist) becoming a call (the
  orphan-`else` over-acceptance, deferred-work ~1628); any other reparenting; any change in a file that
  had errors before or after. These fail the gate and are reviewed individually.
- Case decorations and move routes change no previously clean production tree (their inputs ERRORed);
  an occurrence in production fails the gate until it is reviewed and either added as a named class
  with a spec amendment or fixed.

BC.History is expected to show 0 changes; it is run through the classifier like the others.

### 7.3 The classifier

`python -m tools.perf delta --lib-a <main.dll> --lib-b <branch.dll> --corpus all` (a new subcommand
beside `parity`). It loads both libraries itself and compares complete cursor rows
(`tools/perf/incremental.rows`: every node, named and anonymous, type, grammar symbol, fields, spans,
has_error), pairs nodes by structure, and explains each changed file with E1-E3. Output: a JSON report
(per file: the edits applied, unexplained remainder) and a summary. Exit 0 = every change explained,
1 = an unexplained change or a forbidden edit, 2 = cannot run (a library fails to load, a corpus root
is missing). Tests: a positive synthetic pair for each class, composed pairs (E1 inside E3's host), and
one injected example of each forbidden edit, including: a case pattern wrapped, a name in an
ineligible `body` wrapped, the callee replaced, a parent field reassigned, an `else` wrapped, and an
extra moved to an unapproved parent.

## 8. Phasing and gates

### 8.1 Phases (each reviewed before the next)

0. alc evidence (section 2).
1. Frozen route manifest `tools/b7_audit/b7b3-manifest.tsv` (section 8.2 scope rule): the
   `statement-terminator` and `move-modification` cells plus item 40's shapes, each with a frozen
   per-configuration vector and target verdict; fresh named baselines (tree-harness, main library,
   parity inputs); the `delta` classifier with its tests.
2. Calls (section 3).
3. Case separators (sections 4 and 6.2), opening with the 4.3 optional-body spike.
4. Move header (sections 5 and 6.3).
5. Close-out: `assert --refresh`, full `run`, `report`, both manifest checks; WASM; CHANGELOG
   migration notes, CLAUDE.md, roadmap, deferred item 40 closed and 46 updated.

### 8.2 Gates (at each phase and at the end)

- `tree-sitter test` (suite delta equals cases added), `./validate-grammar.sh --full`.
- `python tools/has_error_sweep.py`: corpus fixtures and all four production corpora.
- Oracle: quick tier; full tier over four corpora with 0 discrepancies; the expected statuses of 6.4;
  `replay`; new `fixture-classes.tsv` rows.
- **Manifests.** `tools/b7_audit/manifest.py` gains a manifest scope: each manifest declares its family
  universe in a header line (`# families: ...`), replacing the hard-coded `FAMILIES`, and
  `manifest --check --manifest PATH` checks that manifest against its own universe. Two checks run:
  `--manifest tools/b7_audit/b7b1-manifest.tsv` (B7b-1 preservation: every frozen admitted id still
  resolves with an unchanged vector and verdict; no cell disappears only because its rule path
  changed) and `--manifest tools/b7_audit/b7b3-manifest.tsv` (B7b-3 targets). **Transfer set:** the
  B7b-1-excluded cells owned by B7b-3 (the move header cells, owner `B7b-3`) stay `excluded` in the B7b-1
  manifest, which records history, and are admitted in the B7b-3 manifest. The B7b-1 check exempts from
  its VERDICT comparison only cells that are in this explicit transfer set AND present in the B7b-3
  manifest AND passing its target check; it still checks their identity, vectors and coverage, and it
  checks verdicts of every other excluded or deferred cell as today. The scope header is mandatory; the
  checker rejects an unknown family, a row outside the declared scope, and a scope header that does not
  round-trip. New separator occurrences (for `move_args`, both the `;` and the `,` branch of `sep`, each
  with its own member path) get reviewed `equiv` or new-scope rows in `tools/b7_audit/registry.tsv`.
- Every SILENT witness of the two families flips to a passing configured status, except a witness
  whose configuration is one of 6.4's named exclusions, which flips to that classified refusal. GAP
  witnesses become positive fixtures.
- `tools/check-field-types.py`, `traversal/policy.json` and the traversal census;
  `python tools/nodetypes.py diff main`, reviewed line by line.
- Query fixtures for the parenless-call captures.
- Incremental equals fresh for each family.
- **Performance.** `ab` refuses to time libraries whose trees differ (`tools/perf/ab.py:20-23`).
  BC.History is EXPECTED to have identical trees (7.2), which the delta classifier confirms first; then
  `python -m tools.perf ab --lib-a <main.dll> --lib-b <branch.dll> --corpus bc-history --rounds 24`,
  run twice with A = main and B = the candidate. Accepted when both runs' `ratio_a_over_b.median` is
  >= 0.97, checked by a small acceptance script over the two JSON results (`ab` itself enforces no
  threshold). If BC.History trees differ, the phase stops and reports.
- **Scaling.** Candidate-only series for case groups (lone `;` groups, nested empty groups, mixed arms)
  and move groups (spanning, nested), added to `tools/perf/strict_lists_scaling.py` and using its grid
  and criteria unchanged: lengths `10 * 2**k` for k = 0..10 and depths 1, 2, 4, 8, 16, 20 (doubling
  steps, so the last-step ratio is real), 5 repeats, batches of about 0.02 s; time ratio per doubling
  under `RATIO_LIMIT = 2.5` by both its fitted and last-step measures (near-linear, not a proof of
  linearity); `MEMORY_LIMIT` 256 MiB growth and `PEAK_LIMIT` 1 GiB. Each input also gets a 10 s ceiling
  enforced by running it in a killable worker process. If hidden partitions yield different trees for
  one input, or a series fails, the phase stops and reports.
- STATE_COUNT budget +3% (over: back to the user); parser.c size reported (51.3 MiB now; GitHub's hard
  limit is 100 MB).
- Production delta (section 7), all four corpora.
- Measured `[BC.History: N errors, X% success]` trailer on every commit.

### 8.3 Release note

The change alters trees for consumers: the call shape, the move fields on routes 2-3, the case-arm
children and decorations. The CHANGELOG gets a migration section with old/new examples (roadmap E2).
Whether it alone triggers a major version is decided at release.

## 9. Out of scope

B7b-2 (expression continuations), B7b-1b..g (deferred item 46), the declaration SILENT families
(`event-declaration`, `interface-procedure`, `procedure-tail`, unowned), a conditional
`case_else_branch` in the oracle, an assembler for `preproc_split_call_statement`, B12 boundaries.

## 10. Review mapping (gpt-6.1-sol, 2026-10-08)

- Design round 1: keep B6's priority, delete all duplicate call routes, other `;`-owning routes (3.1-3.3);
  no unrestricted case-body empties, case lowering reparents (4, 6.2); configuration-dependent else
  ownership (4.4); positional move adapter (5, 6.3); queries (3.5); structural delta (7).
- Design round 2: measured wrapper and `code_names` (3.1); split-call stays `unsupported` (3.3); in-branch
  decorations replace the seam (4.2.2); split-case discriminating fixtures (4.3); attachment, marking,
  registry, case-else exclusion, refusal, mutation tests (6.2).
- Design round 3: spanning group and flat `T;` (5.1); one group type per route (5.1); static roles (5.2-5.3);
  manifest mapping (8.2); over-acceptance wording (5.4).
- Spec review (rev 1 -> rev 2):
  1. comma continuation (5.1 `sep` tail); 2. group grammar defined via the B7b-1 generator (5.1);
  3. frozen field policy (5.2); 4. decoration node, recursion, registry, zero-node lowering, sibling
  exception (4.1, 4.2.2, 6.2); 5. optional-body competition, required tree (4.3); 6. termination by the
  branch's own `;`, run-wide marking, decoration deletion, split-case wrappers, rewrite log (6.2);
  7. preservation vs repair gates and E2 (7.1-7.2); 8. span recomputation, comments, whitelist,
  composable edits, positive tests (7.2-7.3); 9. `ab` on BC.History plus candidate-only scaling (8.2);
  10. the classifier loads both libraries (7.3); 11. manifest scope (8.2); 12. hand-written expected
  trees (3.6); 13. frozen per-configuration statuses (6.4); 14. adapter dispatch by host kind, numeric
  perf criteria (6.3, 8.2); 15. ownership by host route (1, 3.3, 6.1).
- Spec re-review (rev 2 -> rev 3; 1-3, 5, 7, 10, 12, 15 resolved, the rest PARTLY, plus new):
  1. every recursive decoration occurrence aliased through `caseEmptyGroup` (4.2.2); 2. three decoration
  hosts, context-dispatched handler, every arm validated directive-only before deletion (4.2.2, 6.2);
  3. repair vs representation fixtures, refusals frozen individually (6.4); 4. E2 defined on its own,
  extras placement bounded (7.2); 5. E3 eligibility table, keyword table, negative classifier pairs
  (7.2-7.3); 6. explicit transfer set, scope header validation, where statuses live (8.2, 6.4);
  7. `ab --corpus bc-history --rounds 24` with an acceptance script (8.2); 8. doubling grid and the
  real `RATIO_LIMIT`, killable worker (8.2); 9. route-specific field checks per instance (5.2).

## Rev 3 execution amendments (2026-10-08)

Recorded at the end of execution (plan `docs/superpowers/plans/2026-10-08-b7b-3-statement-terminators.md`, Task 11).
The sections above are left as reviewed; where they differ from what shipped, these amendments and their controller
rulings govern.

1. **§3.1, `call_statement` carries `prec(-1)`** (Task 4, `3955dbf`). Without a precedence `tree-sitter generate` fails at
   `begin_keyword identifier • '-'` (`_expression` vs `call_statement`). The `-1` that B6 put on `_expression_statement`
   reached that reduction before the change; it moved down to `call_statement`. No conflict was added: a declared
   conflict would reopen the GLR fork B6 measured (`X[1] := 2;` read as `X` plus a list-literal statement). The
   wrapper still inherits B6's priority, which was §3.1's intent; `_expression_statement` keeps its own `prec(-1)` and
   `code_names`.
2. **§7.2, the E3 / E1 table is derived, not frozen by hand** (Task 3, `fac0d21`). `tools/perf/delta.py
   statement_positions()` walks `src/grammar.json` and finds every (visible host, field-or-unfielded) slot that routes
   into `_statement`, `_statement_inner` or `_expression_statement` (32 positions); a test pins the delta tables to it.
   Two rows of the table above are stale and dropped, `repeat_statement.body` and `case_else_branch.body` (their body is
   always a `statement_block`, whose unfielded statement slot is eligible); `preproc_guarded_statement` is not an E1
   owner (it hosts no `_statement`). The split hosts and `asserterror_statement.body` were added.
3. **§7.3, reviewed recovery-only files** (Task 4, `bc55e43`). A file whose tree has an ERROR before and after and
   changes only under error recovery is admitted only when `tools/perf/delta-reviewed.tsv` lists it with a matching
   sha256 of the source and `has_error` before or after; otherwise the gate fails as §7.2 says. One row:
   BCApps-29.0 `ERMPurchaseReportsIII.Codeunit.al` (a procedure body without `end;` at line 2201; every hunk is a
   recovered name becoming a `call_statement`).
4. **§8.2, retired census keys map to live keys** (Tasks 4 and 10, `1b5f2ab`, `9858e2a`). Deleting the `call_statement`
   arm renumbered `_statement`'s `;` key and removed `occ:call_statement:0.1` and `occ:preproc_split_call_statement:0.7`;
   the move routes moved the move keys. `tools/b7_audit/key-aliases.tsv` (retired key, live key, role, family, reason,
   commit) maps each; `census --check` accepts a registry row under a retired key iff the alias exists, the live key is
   present with the same role (`na` rows exempt), the live key's hosts are a SUBSET of the retired key's (a merged key has fewer hosts), the
   family is checked on the retired side (the split call's `;` moved from `split-call` to `statement-terminator`), and
   the retired side has a row with the alias's role. Frozen manifest and evidence cell ids are unchanged.
5. **§4.3, an empty group before an optional body's `;` is that body** (Task 6, `e085ac8`). In
   `1: asserterror #if X #endif ;` the measured winner is `body: (preproc_conditional_statement ...)` on the
   `asserterror_statement`, not a decoration: `asserterror_statement` is `prec.right(14, ...)`, so the shift into the
   body wins statically and the decoration reading is never explored (`prec.dynamic` cannot change that). Forcing the
   decoration (`prec(14)` plus a conflict) produced the required tree but changed about 3,800 production trees (891 in
   BC.History alone), unexplained by any delta class. Every configuration's flat text is `asserterror ;` either way;
   the oracle lowers an empty-group body to a bodyless `asserterror`. Decorations apply after a non-optional body.
   0 production sites have this shape.
6. **§4.2.2, four decoration hosts** (Task 6 fix round 1, `39cfe92`): `preproc_split_case_end_branch` gets the same
   `optional(seq(repeat(caseEmptyGroup($)), ';'))` before its `end`. Production delta unchanged, census 0/0/0, no new
   conflict. A `;` group BESIDE that end branch still has no slot (deferred-work item 50, 18 cells, owner B7).
7. **§4.2.1, `preproc_split_case_extended`'s arms take a case group's arm items** (Task 6, `e085ac8`): `repeat($._case_group_item)`
   (`case_branch`, `empty_statement`, nested `preproc_conditional_case`) instead of `repeat(case_branch)`. §4.3's
   header-group fixtures need a `;` item or a nested group among the extra branches, and sharing one repeat after `#if`
   with `preproc_conditional_case` removed the declared conflict between the two rules. It widens one over-acceptance
   (deferred-work item 44, `overaccept-leading-semi-ext-arm`).
8. **§4.3, where "a `;` group just before the shared suffix" stands** (Task 6). Directly after `#endif`, before the
   shared suffix, it is invalid AL. The discriminating fixtures place it before the split group
   (`0: Z #if Y ; #else ; #endif` then the split construct) and, for the header group, inside the header arm
   (`1: A #if Y ; #else ; #endif 2:`).
9. **§6.2, attachment follows the flat grammar** (Tasks 6 and 7, `bc45b44`). A selected `;` goes where the flat parse
   puts it: into a preceding body that owns an optional trailing `;` it lacks (`SEMI_OWNING_BODIES` in
   `tools/config_oracle/lowering/case_terminators.py`: `preproc_split_if_begin_asymmetric`,
   `preproc_split_if_then_begin_else_shared`, pinned to the grammar by a test), otherwise onto the branch, outside
   `body`. The six split-if-begin shapes in case branches (alc accepts every configuration) parse since Task 6 and are
   representation fixtures (`test/corpus/b7b3_case_separator_split_if_begin_test.txt`): the asymmetric host is not
   lowered (C1), and where its `end` is the case's in one configuration the boundary is one-reading (B12).
10. **§6.2, statement-run rewrites added** (Tasks 7 and 10, `989cdf1`, `0453b2d`, `cca9985`), each a named
    normalisation that follows the flat grammar and is tested (`select.EMPTY_BODIES` and `engine.ORPHANS` are
    mutation switches):
    - `empty-body-terminator`: selection removed a whole body (a case branch's, a split case wrapper's, or an if
      then/else or while/for/foreach/with body) and the next `;` (bare or a marked arm `;`) becomes
      `body: empty_statement`, as flat `1: ;` and `if C then ;` read. On if/while bodies this also normalises a then
      group that is empty in every configuration; accepted (review M1), because no correct alternative tree exists
      without a decoration rule for if/while.
    - `filled-terminator`: after a fill, an unmarked `empty_statement` directly after that statement becomes its `;`.
      A second emptied body on the same statement is refused (the pre-rewrite `policy` refusal on the first group).
    - `orphan-terminator`, narrowed in the Task 10 fix round: a bare `;` with no statement before it becomes an
      `empty_statement` ONLY when its original preceding sibling is a statement group with an arm ending in a statement
      without its own `;` (the reading depends on the configuration). Split trees that are wrong in every
      configuration are left to fail (deferred-work item 48). The test is stricter than that rule in four shapes,
      `#if A x := 1 #if B #endif #endif ;` and `#if A x := 1 #endif #if B #endif ;` (discrepancy at A=0), and, found by
      the final review (M2), `x := 1 #if A ; #endif ;` and `if C then Bar #if X ; #endif ;` (discrepancy at A=1 / X=1):
      they fail loud and are recorded in item 48 and the `absorb_arm_terminators` docstring.
11. **§6.4 and §8.2, manifest dispositions by the variant test** (Tasks 2, 7 and 10, `7a42b3a`). A cell whose oracle
    refusal is unchanged when B7b-3's mechanism is taken out (the parenless call replaced by `Bar()`, or the preceding
    statement by an assignment) is a host limitation and is `deferred` with the host's owner (B12 one-reading, C1
    unsupported-type, B7 for items 48 and 50), never admitted with a refusal §6.4 does not name. Per-cell assertion rows
    added to close a cell must fail on main's library and hold on the branch, except rows ruled non-discriminating, which
    are allowed only where the tree is byte-identical to main and the oracle passes. Re-recorded cells carry a ledger
    line. End state of the tasks: 1,785 cells, 1,116 admitted, 669 deferred. The final fix wave (review I1) added the
    families `case-branch` and `split-call` to the scope, with assertion rows under the same rule for the cells B7b-3
    repaired (96 case-branch cells, 399 split-call cells): 2,699 cells, 1,251 admitted, 1,448 deferred (deferred-work
    item 49), `manifest --check` 0 problems.
12. **§5.1, flat `moveafter(T;)` stays a negative fixture as parser policy** (Task 1, `795d6a4`; Task 8, `28dfdbc`). alc's
    AL0319 there is a semantic rejection, not a syntax one; the fixture's wording says so and cites B7b-1 spec 4.2
    case 4 (an empty region rejected only semantically gets the same parse policy as a syntax rejection).
