# B7b-2: expression continuations across `#if` (design, rev 3)

Roadmap B7, sub-project B7b-2 (user decision 2026-10-20: next in roadmap order after B7b-3; the user handed the
design to Claude without a question round, so every decision not traced to an earlier ruling is marked
**[Claude's call]** and is open to the user's review). Input: the B7a matrix `docs/b7-separator-continuation-matrix.md`
(role `continuation`; current at main `4d75846`: its evidence header's `src/parser.c` hash equals HEAD's), deferred
items 39, 41, 42, 44 and 46, and a recon report of 2026-10-20 (kept outside the repo; Phase 0 re-derives every
number below). Rev 1 was reviewed by a builder check (4 questions) and gpt-6.1-sol (13 findings); rev 2 adopted
both; rev 3 adopts gpt-6.1-sol's re-review (11 findings). Mapping in section 11.

## 1. Problem

AL lets an `#if` group stand anywhere inside an expression: as a tail after a complete operand, inside another
group's arm, in place of a whole operand, around the first operand with its operator, and in every expression slot
of every statement. alc accepts each of these in every configuration. Our grammar has two narrow facilities:

- `preproc_conditional_expression_tail` (`grammar.js` ~5768-5790): ONE group after a complete expression, arms of
  `(operator operand)+`, optional trailing `(operator operand)*` after `#endif`, plus the B3 form whose arms hold one
  operator each. It is a flat SIBLING of the expression it continues. It is reachable at nine slots: assignment
  right, `if` and `while` conditions, the `for` END bound, `exit` value, call arguments (`_argument_expression`),
  the FIRST subscript index, the FIRST list element, and property values (`_property_value_with_split`, B12).
- `preproc_operand_prefix` (~5834-5845): between the `operator` and `right` of the `+`, `*`, comparison and logical
  rules, arms of exactly one `operand operator` pair.

The oracle already treats both as transparent: it flattens the tail with the expression before it, and the prefix
with its whole binary chain, regroups by the alc-measured ladder (`tools/config_oracle/lowering/expression.py`, from
`test/corpus/operator_precedence_test.txt`; `docs/al-operator-precedence.md`), and lets an inactive group
contribute nothing (`engine.py` ~173-175, `assemblers.py` ~575-585).

Everything else is a GAP (ERROR) or SILENT (clean, wrong tree). The continuation role has 7,894 cells; 6,667 are
defective. Production weight is zero: the four corpora hold 0 tails and 3 operand prefixes (BCApps-29.0, all
CONSISTENT), and every B7b-2 family has 0 matching production sites. This is completeness work toward the
project's goal (parse AL correctly), and its production gate is "no production tree changes".

### 1.1 Root causes

One primary cause per defective cell (counts are primary attributions; many cells need two):

| # | cause | GAP | SILENT | example |
|---|---|---|---|---|
| RC1 | the tail admits one group; an arm cannot hold a group; no second group after `#endif` | 1,143 | 5 | `r := 1 #if X + 2 #endif #if Y + 3 #endif;` ERROR |
| RC2 | no group can stand where an operand is expected (whole operand, first operand, unary/signed operand, member object, `with` record) | 1,747 | 0 | `r := 1 + #if X 2 #else 3 #endif;` ERROR |
| RC3 | about 15 expression slots have no tail at all | 511 (+ RC1/RC2 cells of those hosts) | 0 | `repeat Bar(); until b #if X and c #endif;` ERROR (item 39 shape 1) |
| RC4 | `in`, `is`, `as` are not continuation operators | 294 | 12 | `i2 := i #if X as IFoo #endif;` clean: the arm is torn into `call_statement`s `as`, `IFoo` (item 41) |
| RC5 | a tail anchored at the host regroups across a ternary or range | 0 | 36 | `x := Ok or true #if X and false #endif or Ok ? 1 : 2;` reads the ternary as the tail's last operand |
| RC6 | case-pattern slot: `_case_pattern_branch` arms need no comma, so `1 #if X + 1 #endif :` reads `+1` as a second pattern | 2,124 | 106 | out of scope (section 9), with tie-breaks where shared rules reach it (6.5) |
| RC6b | `_argument_branch` arms need no comma: `Foo(1 #if X + 2 #endif #if Y + 3 #endif, 2)` reads `+ 3` as an argument | 0 | 4 | a both-clean ambiguity once RC1 lands (6.4) |
| RC7 | `;` and statements inside a continuation arm (item 39 shape 2, placement `semi-in-arms`) | 44 | 0 | out of scope (section 9) |
| RC8 | `op-only`: `E #if X op #endif F` is invalid AL at X=0; the parser has one tree for both | (157 OVERACCEPT) | | classification only (9) |

Placement legend (`tools/b7_audit/placements.py`): `suffix` `E #if X op F #endif`; `suffix-else`; `op-only`;
`prefix` `E op #if X F op #endif G`; `whole-operand` `E op #if X F #else G #endif`; `first` `#if X E op #endif F`;
`first-only` `#if X E #else F #endif`; `chain`; `consecutive` (two sibling groups); `nested` (a group in an arm);
`unary-paren`, `unary-minus`, `unary-not`, `signed` (operand-position arms of those shapes); `semi-in-arms`. Every
placement except `op-only` is alc-valid in every configuration (97-100% of measured cells accept; the rest are type
errors and item-42 generator imprecisions).

## 2. Goals, non-goals, anti-goals

**Goals.** Every in-scope continuation cell (8.1) parses clean with a tree that the oracle validates, or that a
structural assertion row pins where the host is oracle-blind (C1). Item 41 and item 39 shape 1 close. One
representation contract (section 3) covers tails, prefixes and operand groups.

**Non-goals.** Case-pattern continuations (RC6), `;` inside continuation arms (RC7), property values (B12), the
list-literal separator family (B7b-1c), the crossing forms of 3.4, any production tree change.

**Anti-goals** (a technically passing result that is still a failure):
- A form that parses clean in two ways and lets GLR pick one. Every both-clean ambiguity gets a deterministic,
  demonstrated tie-break (5.4) and a fixture that FAILS on the losing tree. An error count proves nothing here:
  6044689, e0ab7a4 and item 41 were all clean and wrong.
- A CST node that claims a grouping AL does not have, outside the contract of section 3.
- `prec.right` on a host's tail slot (it cost 200 and 376 BC.History files, `grammar.js` ~6873-6882).
- The tail inside `_expression` (it reopens the `_single_pattern` vs `_expression` conflict 812ace7 removed, ~6895).
- A grammar `prec()` number standing in for AL precedence.
- Masking: an oracle rewrite that makes a split tree that is wrong in every configuration agree (B7b-3 Task 10 C1).

## 3. The representation contract: transparent regions

A CFG parser cannot give one tree whose nesting is right in every configuration when an `#if` group splits an
operator chain: `2 * #if X 3 + 4 #else 5 #endif` is `(2*3)+4` at X and `2*5` otherwise. The grammar already answers
this for tails and prefixes by making them transparent. Rev 3 states that answer as the contract for all of
B7b-2, defined by CST edges so a consumer can apply it from the tree.

### 3.1 Region edges

An edge from a parent node to a child is a **region edge** when it is one of:
- `left` or `right` of `multiplicative_expression`, `additive_expression`, `comparison_expression`,
  `logical_expression`; `left` of `in_expression`, `is_expression`, `as_expression`;
- `operand` of `unary_expression`;
- the unfielded edge from a binary node to each `preproc_operand_prefix` between its `operator` and `right`
  (every consecutive prefix), and from a region root to a leading prefix (6.3);
- any child of `preproc_conditional_expression_tail`, `preproc_operand_prefix` or `preproc_conditional_operand`
  (their arms and items), and the edge from a region root's expression to the tail beside it (5.1).

A binary node's `operator` child (an anonymous token, `comparison_operator`, or an `in`/`is`/`as` keyword node) is an
operator component of the region, never an atom. Today's chain walker already includes the unfielded prefix child
(`tools/config_oracle/lowering/expression.py` ~155-174); the region walker keeps that.

Every other edge is a **boundary**: a call's arguments, a member's object, a subscript's object and indices, a
parenthesized expression's inner, a list element, each ternary part, each range end, and the right operand of
`in`/`is`/`as` (a typed unit: a `list_literal`, a range set, a `type_specification`; it enters the region as one
atom, its own interior is its own region or none).

A **region** is a node reached by a boundary edge (or a slot of 5.1) together with everything reachable from it by
region edges only. Nodes reached through a boundary are atoms of the region (calls, member accesses, subscripts,
parenthesized expressions, ternaries, list literals, literals, names). A region **contains a group** when a tail,
prefix or operand group is reachable from its root by region edges only; a group behind a boundary belongs to the
inner region and waives nothing outside it (`x := a * b + Foo(1 #if X + 2 #endif);`: the outer region has no
group).

### 3.2 Meaning

In a region that contains a group, the nesting of the region's binary and unary nodes is not a grouping claim. The
region's meaning in a configuration is: replace each group by its active arm's content, or by nothing when no arm is
active (fragment splicing, recursively); read the result as a flat run of atoms, unary operators and binary
operators; group it by the ladder. Validity is checked after composition: a missing operand or a dangling operator
in the composed run is an invalid configuration, never a group that merely contributed nothing (`x := 1 #if X + 2
#endif;` and `x := a + #if X b + #endif c;` are valid at X=0).

Ladder (one numeric convention, larger binds tighter, as in `expression.py`): unary `not` `-` `+` 7,
right-associative (prefix); `* / div mod` 6; `+ -` 5; `in is as` 4; `and` 3; `or xor` 2; comparisons 1; all binary
levels left-associative (`docs/al-operator-precedence.md`). A region without a group keeps today's trees and
claims. Boundaries are hard: grouping never crosses one.

### 3.3 Why this and not a new flat node

A dedicated flat node for any region with a group would make the claim explicit in the tree, but it changes the
three production prefix trees (the production gate forbids that) and re-derives every chain rule.
**User decision 2026-10-20** (approved with the spec): the transparent-region contract, because the grammar and oracle already do
it for tails and prefixes. Consumers get the rule from section 3.1-3.2 alone. Phase D documents it in `docs/` and
in the query README; the traversal helper (`docs/traversal.md`) does not expose regions today, and adding a region
API is a separate item (section 9), not a B7b-2 deliverable.

### 3.4 Crossing forms: restricted in the grammar, deferred

Three shapes would let a group cross a boundary, which the contract cannot express. The grammar refuses them (they
stay ERROR, each with an `:error` gap witness and alc probe); a follow-up item owns them (section 9):
- **Receiver crossing.** A group directly followed by a postfix (`.Trim()`, `[1]`, `(args)`) whose arm is not itself
  a postfix-safe atom: `#if X a + b #else c #endif .Trim()` is `a + b.Trim()` at X, not `(a+b).Trim()`. In a
  receiver position (member object, subscript object, call function) the operand group's arms are restricted to
  postfix-safe atoms (a name, literal, call, member access, subscript, parenthesized expression). Arms with a
  unary or binary top in that position: deferred.
- **Ternary crossing.** A `?`/`:` inside any arm (tail, prefix or operand group): `b := false #if X or true ? true :
  false #endif;`, `b := flag and #if X a ? p : q #else r #endif;`, `b := #if X a ? p : q #else r #endif ? s : t;`.
  Arms take `_continuation_operand`, an `_expression` that is not a `ternary_expression`; this applies to the
  existing prefix arm too (`_dangling_operand`, no production site has a ternary there). Deferred.
- **List spanning.** One group that both continues an expression and supplies further list items: `Foo(1 #if X + 2,
  3 #endif)` (X=1: `Foo(1 + 2, 3)`). The existing argument group reads it today (a comma-less `+2` argument), a
  pre-existing wrong tree; the oracle refuses it at the list's alternation check. Not changed by B7b-2; deferred with
  a witness pinning that refusal.

## 4. Phase 0: evidence and harness

1. **Re-derive** section 1.1 from the evidence; freeze the scoped manifest (8.4).
2. **alc probes** (`tools/alc_probe/cases/b7b-2/`, `// expect:` + `// source:` headers, four-way via
   `python -m tools.alc_probe run`) for forms no cell covers: `in`/`is`/`as` arms in every tail placement and as
   operand-prefix operators; operand groups whose arms carry continuations; nested operand groups; an operand group
   followed by a tail; operand groups at the typed right of `in`/`is`/`as` (6.2); consecutive operand prefixes; the
   three crossing forms of 3.4; the 4.3 witnesses below with a type that makes the two groupings give different alc
   verdicts (the `docs/al-operator-precedence.md` method).
3. **Grouping witnesses** (each must lower to the right tree and FAIL on the named wrong one):
   `not a #if X and c #endif` = `(not a) and c`, not `not (a and c)`; `a * b #if X + c #endif` = `(a*b)+c`;
   `a - b #if X - c #endif` = `(a-b)-c`; `(-a #if X + b #endif)` = `((-a)+b)` (with the parenthesized wrapper);
   `-(a #if X + b #endif)` = `-(a+b)`; `2 * #if X 3 + 4 #else 5 #endif` = `(2*3)+4`;
   `true and #if X a = c #else d #endif` = `(true and a) = c`; `- #if X a + b #else c #endif` = `(-a)+b`;
   `not #if X not a #else a #endif` = `not (not a)`; `Ok ? 1 : 2 #if X + 3 #endif` = `Ok ? 1 : (2+3)`;
   `[1..5 #if X + 2 #endif]` = `[1..(5+2)]`; `Ok or true #if X and false #endif or Ok ? 1 : 2` =
   `((Ok or (true and false)) or Ok) ? 1 : 2`; `x := 1 #if X + 2 #endif;` and `x := a + #if X b + #endif c;` valid
   at X=0; `b := i #if X + 1 #endif in [1, 2] and Ok;` = `((i+1) in [1,2]) and Ok`.
4. **Attachment spike** (5.4): before Phase A, a throwaway branch shows for every tie-break in 5.4 that both
   derivations survive to the decision point and that the intended one wins. Record the parser actions
   (`tree-sitter parse -d`) in the execution amendments.
5. **Baselines**: a fresh `./tools/tree-harness.sh snapshot` per corpus at the branch point, a main library build
   for `tools.perf ab` (git worktree outside the repo), `./tools/metrics.sh` numbers.

## 5. Tails

### 5.1 Tail grammar, region roots and fragment sites (RC1, RC3)

```
preproc_conditional_expression_tail :=
    #if   _tail_item+   (#elif _tail_item+)*   [#else _tail_item+]   #endif   _tail_item*
  | _preproc_operator_arms  operand:_continuation_operand  _tail_item*          (B3 form)
_tail_item := _expression_continuation | preproc_conditional_expression_tail
```

A nested or consecutive group is a visible, recursive `preproc_conditional_expression_tail`: `consecutive` gives
tail1 containing, after its `#endif`, tail2; `nested` gives tail2 inside tail1's arm; an arm may start with a nested
group. **[Claude's call]**: one node type means one query and one assembler; sibling tails at the host would turn
nine hosts' `optional(tail)` into `repeat(tail)`. The builder may factor `_tail_item` and the arms as hidden
complete units (`docs/state-reduction-method.md` section 2) and measures inline against hidden by stubbing.

**Region roots** carry a tail. One helper writes them: `contSlot($, expr, fieldName?)` expands to
`[field(fieldName, expr) | expr], optional($.preproc_conditional_expression_tail)`, fielded or unfielded so every
existing slot keeps its fields exactly; inlined, never a hidden rule, so the B7a census keys keep their rule paths
(a moved key gets a `tools/b7_audit/key-aliases.tsv` row). Each insertion is an `optional()` with a declared conflict
where generation demands one, never `prec.right`.

| region root | family |
|---|---|
| assignment right, `if`/`while` condition, `for` END, `exit` value, call argument, subscript FIRST index, list FIRST element | existing (move onto the helper with byte-identical trees) |
| `repeat_statement.condition` | repeat-until (item 39 shape 1) |
| `case_statement.expression`, `preproc_split_case_statement_end` expression | case-expression |
| `ternary_expression` condition, then, else | ternary |
| `parenthesized_expression` inner | parenthesized |
| `range_expression` left, right | range |
| `for_statement.start` | for-bounds |
| `subscript_expression` 2nd+ index | subscript |
| `list_literal` 2nd+ element | list-literal (continuation cells only) |
| `with_statement.record`, `foreach_statement.iterable` | with (foreach has no cells; included for uniformity, **[Claude's call]**) |
| `_preproc_if_header` and the split-if heads | split-if-condition (C1, assertion rows) |
| `_expression_list` / `_preproc_call_prefix` arguments | split-call (C1, assertion rows) |

**Fragment sites** carry tail items without being region roots: the operand of a prefix arm. `_dangling_operand`
becomes `operand: _continuation_operand, _tail_item*, operator: _continuation_operator`, so `a + #if X b #if Y + c
#endif + #endif d` parses; the items belong to the enclosing region (3.1: children of a prefix are region edges).

Not tail sites at all: binary `left`/`right`, `unary_expression.operand`, `in_expression.left`. A group after one
of them belongs to the enclosing root's tail; that is how the `unary-operand`, `in-operand` and `binary-operand`
cells are fixed (RC1/RC2/RC4 at the root).

**The property route is excluded from mechanical conversion.** `_property_value_with_split` (~2051-2058) requires
its tail and admits the scanner's signed literals; it stays as it is (B12 owns property values). **[Claude's call]**.

### 5.2 Attachment across a boundary (RC5)

Where a region root's expression ends with an inner region, two clean readings exist: `Ok ? 1 : 2 #if X + 3 #endif`
can put the tail in the ternary's `else_value` root or at the assignment root after the whole ternary; `[1..5 #if X
+ 2 #endif]` in the range's right root or at the list element root. Only the ternary's else part and the range's
right end create this, because nothing closes them. Rule: **the tail belongs to the innermost region that ends where
its `#if` begins**: `else_value`, the range's right end. That is AL's reading, and it matches the anchored
assertion in `tools/b7_audit/tests/test_silent.py` (~166-177).

The trailing items of a tail cannot reach past a boundary either: after `#endif`, `or Ok ? 1 : 2` must leave `?` to
an enclosing ternary whose `condition` root holds the tail, so a `_tail_item`'s operand is `_continuation_operand`
(3.4). Then `x := Ok or true #if X and false #endif or Ok ? 1 : 2;` has one parse. The mechanism (a narrowed choice
or a hidden `_continuation_operand`) is the builder's, but it must remove the ternary production, not penalise it:
a negative dynamic precedence still wins where nothing else completes.

### 5.3 `in`, `is`, `as` (RC4)

Add the three keyword operators to `_continuation_operator` (field `operator`, the existing `in_keyword`,
`is_keyword`, `as_keyword` nodes). Their operand is what `in_expression`/`is_expression`/`as_expression` take on
their right side (a list or range set; a `type_specification`), not `_expression`, and it is a typed atom (3.1).
The torn reading (`#if X as IFoo #endif` as a statement group of two parenless calls) still parses clean because
`is`/`as` are names in code (B6); the tie-break in 5.4 makes the continuation win. **[Claude's call]**: not reserving
`is`/`as`, because alc accepts them as names. Fixtures: item 41's three cells (`suffix`, `consecutive`, `nested`),
each asserting `operator: (as_keyword)` in the tail and failing on a `call_statement` named `as`. Operand prefixes in
`in_expression`/`is_expression`/`as_expression` only where probe 4.2 shows alc accepts them.

### 5.4 Tie-breaks

| competing readings | input | winner |
|---|---|---|
| tail in `else_value` / range right vs at the enclosing root | `Ok ? 1 : 2 #if X + 3 #endif` | inner root |
| tail with `in`/`is`/`as` vs a statement group of parenless calls | `i2 := i #if X as IFoo #endif;` | tail |
| tail vs a comma-less `preproc_conditional_arguments` arm (RC6b) | `Foo(1 #if X + 2 #endif)`, `Foo(1 #if X + 2 #endif #if Y + 3 #endif, 2)`, `Foo(1 #if X + 2 #endif #if Y , 3 #endif)` | tail |
| tail vs a comma-less `preproc_conditional_case_patterns` arm | `case i of 1..5 #if X + 2 #endif : Foo(); end;` | tail |
| operand group vs a statement group at a statement start | `#if X a #else b #endif .Foo();` | 6.3 |
| operand group vs an argument / list-element group at an item start | `Foo(#if X 1 #else 2 #endif + 3)`, `[#if X 1 #else 2 #endif + 3]` | operand group |
| operand group vs a case-pattern group at a pattern start | `case i of #if X 1 #else 2 #endif + 3: Foo(); end;` | operand group |
| comma-separated group vs operand group | `Foo(1 #if X , 2 #else , 3 #endif)`, `case i of 1 #if X , 2 #endif : ...` | list / pattern group |

The rule behind the last four rows decides only between two derivations that both complete: there, a list or
pattern group owns the `#if` when a separator stands at its seam (an arm that is separator-led or separator-trailed,
or a separator or the list's end after `#endif`); a group followed by an operator after `#endif` with no separator
at either seam is an operand group. Ownership follows the separators around the group, not whether an arm could
stand alone as an item. A group only one derivation completes keeps it: `Foo(#if X 1, #endif 2)` (X=0 `Foo(2)`,
X=1 `Foo(1, 2)`) stays the argument group, pinned by a preservation fixture.

Dynamic precedence decides only between derivations that both reach the decision. Where a static shift/reduce
(`unary_expression`'s `prec.right(8)`, `ternary_expression`'s `prec.right(1)`, `preproc_split_case_branch`'s
`prec(25)`) settles a choice before that, a dynamic value has no effect (the B7b-3 amendment 5 trap). The Phase 0
spike (4.4) demonstrates each row; a row it cannot demonstrate gets a grammar restructuring or goes to the user.

## 6. Operand groups and prefixes (RC2)

### 6.1 The node

`preproc_conditional_operand`: `#if arm (#elif arm)* [#else arm] #endif`, each arm one `_continuation_operand`
followed by `_tail_item*`. It stands where one operand stands. Under section 3 it is transparent:
`2 * #if X 3 + 4 #else 5 #endif` gives `multiplicative_expression right: (preproc_conditional_operand ...)`, which is
not a claim that `3 + 4` is grouped. In a receiver position its arms are postfix-safe atoms (3.4). Fields: an arm's
first operand is `operand` (multiple); the group takes the field of the position it fills;
`tools/check-field-types.py` lists every widened field (`right` of each binary rule, `operand` of
`unary_expression`, the slots' fields, `object`, `record`).

### 6.2 Typed right operands

`in_expression.right` takes a `list_literal` (or range set) and `is_expression`/`as_expression`.right a
`type_specification`, not `_expression`, so an `_expression`-level group does not reach them. Where probe 4.2 shows alc
accepts a group there (`b := i in #if X [1, 2] #else [3] #endif;`, `j := i as #if X IFoo #else IBar #endif;`), the
right slot accepts a `preproc_conditional_operand` whose arms hold that slot's own node kind (an aliased typed
variant, same visible type, fields preserved). A form alc rejects is not added.

### 6.3 Leading prefixes and placement

`first` (`#if X E op #endif F`): an operand prefix at a region's start, followed by the region's operand. Consecutive
prefixes (`a + #if X b + #endif #if Y c * #endif d`) are `preproc_operand_prefix+`, only if probe 4.2 shows alc
accepts every configuration.

Placement of the operand group, measured by stubbing (`docs/state-reduction-method.md`): STATE_COUNT,
LARGE_STATE_COUNT, declared conflicts, four-corpus parity:
- **A, primary**: one alternative of `_expression`'s primary choice, plus the receiver and typed variants; covers the
  `_expression` operand positions at once; competes with every group that reads `#if` at an expression start
  (`preproc_conditional_statement`, `preproc_conditional_arguments`, `preproc_conditional_list_elements`,
  `preproc_conditional_case_patterns`, the B11 property-value groups) and the `[$._single_pattern, $._expression]`
  history (~739-747).
- **B, positions**: binary `right`, unary operand, region-root starts, `member_expression`'s object, `with`'s record,
  the typed rights of 6.2.

Take A unless it changes a production tree or costs clearly more than B; record the numbers. At a statement start
(`#if X a #else b #endif .Foo();`) the statement group wins where its arms are complete statements; the operand group
wins where the group is followed by a postfix, an operator or `:=`. The spike demonstrates it.

### 6.4 Call arguments (RC6b)

B7b-1's strict-list generator does NOT remove the comma-less arm reading (its `E := atom [T] | T`, `T := group [E]`
admits an atom directly followed by a group whose arm starts with another atom: `grammar.js` ~158-173, item 44), so
rev 1's conversion is dropped. The tail wins over a comma-less argument arm (5.4), pinned by losing-tree fixtures.
The argument group itself is unchanged, and so is the oracle's argument family. List spanning is 3.4.

### 6.5 Case hosts reached through shared rules

`range_expression`, `unary_expression`, `parenthesized_expression`, `subscript_expression`, `in_expression` and the
binary rules are shared with `_single_pattern` (~6286-6336). Their new region roots and operand groups are reachable
in case patterns, so the case hosts are NOT untouched. **[Claude's call]**: no case-specific rule variants (they would
duplicate the expression rules); instead the case cells these shared rules reach are in scope for the 5.4
tie-breaks and fixtures, and every case cell whose tree changes is recorded in the manifests (8.4). The case-pattern
slot's own tail (`1 #if X + 1 #endif :`, `_single_pattern` itself) stays out of scope (RC6).

## 7. Oracle: one region assembler

Replace `assemblers.expression_tail` and `assemblers.operand_prefix` with one region assembler that implements
3.1-3.2:
1. **Ownership.** Exactly one invocation per region, at its root (the node reached by a boundary edge or a 5.1
   slot). The assembler walks region edges only, consumes every node it reaches, and lowers each boundary-reached
   atom by the ordinary engine first (an inner region is assembled by its own root's invocation). The engine's
   binary-chain-top hook (`engine.py` ~466-496) and its single-top guard are replaced by this root dispatch; leaf
   accounting (`engine.py` ~425-443) stays and must see each leaf exactly once.
2. **Select by splicing.** Replace each group by its active arm's content, or by nothing; recurse into nested groups.
3. **Compose and validate.** Flatten to a run of atoms, unary operators and binary operators; compose with the ladder
   of 3.2 (add unary at 7, right-associative, to `lowering/expression.py` with the measured witnesses). A missing
   operand or dangling operator in the composed run is `contract-shape` (invalid configuration).
4. **Fields.** The result keeps the root's field; a region without a group is lowered exactly as today.
5. **Property compatibility.** The property route keeps its named behaviour: the `property-expression-unwrap` rewrite
   and the signed-literal `one-reading` refusal (`engine.py` ~149-179, `assemblers.py` ~548-570) are reproduced in the
   new assembler for the property host, with their existing tests unchanged.

Hosts are census-driven `hosts=` entries in `contracts.py` for every region root of 5.1. Split-if and split-call roots
stay `lowering:unsupported-type` (C1) and are closed by assertion rows. Unit tests: every 4.3 witness lowers to its
right tree, and a mutation per witness producing its wrong tree is caught; a double-ownership test (a prefix chain
under a rooted tail: `x := a * #if X b + #endif c #if Y + d #endif;`).

## 8. Scope, phasing, gates

### 8.1 In scope

Families (continuation role; case-pattern-slot cells, `semi-in-arms` cells and the 3.4 crossing forms excluded):
`expression-tail`, `operand-prefix`, `arguments`, `type-test`, `in-operand`, `assignment`, `exit-value`,
`if-condition`, `while-condition`, `for-bounds`, `repeat-until`, `case-expression`, `ternary`, `parenthesized`,
`range`, `unary-operand`, `binary-operand`, `subscript`, `member-access`, `with`, `split-if-condition`, `split-call`,
the continuation cells of `list-literal` (**[Claude's call]**: they are expression slots; the list's separator cells
stay B7b-1c), plus the case cells of 6.5. `op-only` cells are in scope except the 157 already-clean OVERACCEPT cells
(by cell id): an `op-only` GAP (`repeat Foo(); until a #if X and #endif b;`) needs its root like any other cell.

### 8.2 Phases

One branch, `feat/b7b-2-continuations`; each phase is planned, built, reviewed and gated before the next; one merge at
the end (**[Claude's call]**, the B7b-3 model).

| phase | content | primary cells (approx.) |
|---|---|---|
| 0 | section 4 (evidence, probes, witnesses, spike, baselines, manifest and checker changes) | - |
| A | RC1 tail closure and prefix-arm fragments, RC4, RC6b tie-break, the region assembler | ~1,450 |
| B | region roots (5.1 table), RC5 boundary attachment, the case tie-breaks of 6.5 | ~550 plus RC1/RC2 cells of the new roots |
| C | RC2 operand groups (receiver, typed and leading variants), placement measured | ~1,750 |
| D | docs: section 3's contract in `docs/` and the query README, deferred items (section 9), CHANGELOG, CLAUDE.md, roadmap row, matrix refresh, metrics | - |

### 8.3 Fixtures

- Hand-written expected trees for every attachment, ownership and grouping case (the 4.3 witnesses, the 5.4
  tie-breaks, item 41). Write them from the contract first; use CLI output to diagnose a difference, never to decide
  it (B7b-3 spec ~136-140). Each gets a mutation for its actual losing tree (unary absorption, right-associated
  subtraction, extra argument, host-anchored ternary tail, torn `as` call, case pattern group) that must fail it.
- In-scope `test/corpus/b7_gap_<family>_test.txt` cases move to positive `b7b2_<family>_test.txt` fixtures as each
  phase fixes them; new `:error` gap witnesses for the 3.4 forms; expected ERROR trees, where any are pinned, come
  from `tree-sitter parse`, never `snip`; `tools/deliberate-negatives.txt` updated in the same commit. Mind the `-u`
  traps (CLAUDE.md): read every hunk, `git diff --stat test/corpus` after each `-u`, the suite count moves by exactly
  the cases written.
- SILENT witnesses of the in-scope groups in `tools/b7_audit/tests/test_silent.py` become positive tests. Item 41's
  tests invert. **Item 39 shape 1 only**: split the `B7_GAP` parametrisation in
  `tools/config_oracle/tests/test_expression_statement.py` (~63-84) so shape 2 stays a deferred negative.

### 8.4 Manifest

The checker (`tools/b7_audit/manifest.py`) scopes by FAMILY, requires a row for every cell of a scoped family, and
checks `expected_oracle` for every disposition (~237-250). So:
- `tools/b7_audit/b7b2-manifest.tsv` lists every cell of the 8.1 families: in-scope cells, and the excluded ones
  (case-pattern slot, `semi-in-arms`, list-literal separators, the 157 op-only OVERACCEPT cells by id, the 3.4
  crossing forms) with reason and owner.
- **Per phase**: a cell a later phase fixes is recorded `deferred`, owner `B7b-2/B` or `B7b-2/C`, with its CURRENT
  verdict and oracle outcome frozen; when its phase admits it, the row switches to its target verdict and outcome.
- **Target oracle outcomes per configuration**: `pass` on every supported host; a C1 refusal named per cell with its
  assertion row.
- **Checker changes (Phase 0, with tests)**: a final mode that fails while any row is owned by `B7b-2/*`; a mode that
  requires `expected_oracle` on admitted rows; and a reviewed re-recording for overlap. B7b-3 froze `split-call` and
  case families with deferred rows (owner C1 or B7b+); a row of another manifest whose verdict B7b-2 changes is
  re-recorded there by an explicit `--rerecord <manifest> <cell ids>` listed in the phase report, keeping the cell's
  identity and vector checks intact; nothing changes silently. B7b-1 and B7b-3 manifests stay at 0 problems.

### 8.5 Gates (each phase and the end)

- `./validate-grammar.sh --full` exit 0; `tree-sitter test` count moves by exactly the cases written.
- Production trees byte-identical in all four corpora: `./tools/tree-harness.sh verify` against the Phase 0
  snapshots and `python -m tools.perf delta` 0 files changed. The 3 operand prefixes and the 1
  `preproc_conditional_arguments` site are named checks.
- `python tools/has_error_sweep.py` over the corpus fixtures and the production corpora.
- Oracle: `--tier quick` 0, `replay`, and at the end the full tier with 0 discrepancies.
- B7 audit: `assert --refresh`, a full `run`, `report` (matrix byte-identical to `report` output); the three
  manifests `--check` 0 problems; `census --check` 0.
- `./tools/ts-lock.sh python -m pytest tools/b7_audit/tests tools/config_oracle/tests tests/traversal -q`.
- `tools/check-field-types.py`, `traversal/policy.json` and the traversal census; `python tools/nodetypes.py diff main`
  reviewed line by line.
- **Scaling**: candidate-only series in `tools/perf/strict_lists_scaling.py` with its grid and criteria unchanged
  (B7b-3 spec ~518-525): lengths `10 * 2**k` for k = 0..10 and depths 1, 2, 4, 8, 16, 20, 5 repeats, batches of about
  0.02 s; time ratio per doubling under `RATIO_LIMIT = 2.5` by both its fitted and last-step measures;
  `MEMORY_LIMIT` 256 MiB growth, `PEAK_LIMIT` 1 GiB; a 10 s ceiling per input in a killable worker. Series: repeated
  argument tails (`Foo(1 #if X +2 #endif ... #if X +N #endif)`), repeated root tails, nested tails, nested operand
  groups, mixed prefixes, operand groups and tails. A failing series stops the phase.
- **Incremental equals fresh** for edits that change arm openers, operators, parentheses and group adjacency.
- **Speed**: `python -m tools.perf ab --corpus bc-history --rounds 24` twice (A = main, B = candidate), accepted when
  both medians of `ratio_a_over_b` are >= 0.97; also over DC. Same session, pinned.
- **Cost** (guideline, not cap): STATE_COUNT +3% per phase over that phase's base; over it, measure, attribute and
  put it to the user before continuing (**[Claude's call]**, B7b-3's figure). parser.c: report bytes and margin per
  phase; at 80 MiB stop and ask (GitHub warns above 50 MB and refuses a file over 100 MB; today 51.5 MiB). Report
  STATE_COUNT, LARGE_STATE_COUNT, SYMBOL_COUNT and declared conflicts per phase with `./tools/metrics.sh --vs`.
- Measured `[BC.History: N errors, X% success]` trailer on every commit.

### 8.6 Release note

CHANGELOG under Unreleased: continuations at every expression slot, nested and consecutive groups, `in`/`is`/`as`,
operand groups; the transparent-region contract; item 41 and item 39 shape 1 closed; new node type
`preproc_conditional_operand`; widened fields; the 3.4 forms still ERROR; production trees unchanged.

## 9. Out of scope, with owners (deferred-work items written in Phase D)

- **Case-pattern slot continuations (RC6, ~2,230 cells).** Prerequisite: separator tracking for case-pattern groups
  and C1 lowering of the case hosts. Owner: B7b-1h, then a B7b-2 follow-up.
- **`;` inside continuation arms (RC7, item 39 shape 2, 44 cells).** Owner: B7 terminators, with items 47 and 48.
- **The 3.4 crossing forms** (receiver, ternary, list spanning). Owner: B7b-2 follow-up; each needs a representation
  that can say "a group crosses this boundary", which the contract of section 3 cannot.
- **A region API in the traversal helper.** Owner: roadmap F (traversal).
- **Property values.** B12 (item 36). **The list-literal separator family.** B7b-1c (item 46).
- **`op-only` OVERACCEPT (RC8, 157 cells).** Classified over-acceptance like item 44: valid at X=1, invalid at X=0,
  one tree for both; a parser that refused it would refuse the valid configuration too.

## 10. Left to the builder

The hidden-unit factoring of the tail; the `_continuation_operand` mechanism (5.2's constraint holds); Phase C's
placement after measurement; how the receiver and typed variants are realised (6.1-6.2's node and field contract
holds); dynamic-precedence values once the spike shows each row is reachable; per-slot conflict declarations; test
and witness file names. Each choice is recorded with its measurement in this spec's execution amendments.

## 11. Review mapping

**Rev 1 -> rev 2** (builder check; gpt-6.1-sol round 1)

| finding | rev 2 |
|---|---|
| pi 1, builder 1: innermost-slot rule wrong for unary and binary right | regions; roots exclude operands; boundary rule only |
| pi 2: strict arguments keep the comma-less reading | conversion dropped; tie-break |
| pi 3: operand groups are not atoms | transparent contract; region assembler |
| pi 4: ternary exclusion breaks arms; range exclusion a no-op | refined again in rev 3 (3.4) |
| pi 5: dynamic precedence may be unreachable | spike (4.4); 5.4 rule |
| pi 6: leading prefix has no consumer | 6.3, section 7 |
| pi 7: strict-list schema cannot hold expression plus tail | moot |
| pi 8, builder 2: case hosts reached through shared rules | 6.5 |
| pi 9, builder 4: manifest scope, phases, oracle, overlap | 8.4 |
| pi 10: parser-generated expectations too weak | 8.3 |
| pi 11: no scaling or incremental gate | 8.5 |
| pi 12: helper loses unfielded slots; property route | 5.1 |
| pi 13: item 39 shape 2 swept in | 8.3 |
| builder 3: no budget | 8.5 |

**Rev 2 -> rev 3** (gpt-6.1-sol round 2)

| finding | rev 3 |
|---|---|
| 1 Critical: inactive groups rejected | 3.2 fragment splicing, validity after composition; 7 step 2-3; 4.3 X=0 witnesses |
| 2 Critical: receiver crossing (`.Trim()`, `[1]`) | 3.4 receiver restriction, deferred; 6.1 |
| 3 Critical: ternary arm not safe as "whole region" | 3.4: no `?`/`:` in any arm, prefix arms included; deferred |
| 4 Important: region membership, typed atoms, numeric convention | 3.1 edges, local membership, typed right operands as atoms; 3.2 one convention (unary 7); traversal claim removed (3.3, item in 9) |
| 5 Important: typed rights of `in`/`is`/`as` | 6.2 |
| 6 Important: tail inside a prefix arm | 5.1 fragment sites |
| 7 Important: leading case group winner | 5.4 rows and separator-ownership rule |
| 8 Important: one group continuing and supplying arguments | 3.4 list spanning, deferred with witness |
| 9 Important: assembler dispatch; property behaviour | 7 steps 1 and 5; double-ownership test |
| 10 Important: manifest phase freezing, op-only scope, enforcement | 8.1 op-only by id; 8.4 current-then-target, checker modes, `--rerecord` |
| 11 Minor: scaling criteria | 8.5 B7b-3 harness and numbers |
| witness: chained unary | 4.3 |

**Rev 3 final check** (gpt-6.1-sol round 3: round-2 findings 1-3 and 5-11 resolved, 4 not)

| finding | fix |
|---|---|
| Critical: the edge into an operand prefix was not a region edge (`x := a * #if X b + #endif c;`) | 3.1: binary-to-prefix and root-to-leading-prefix edges; operator children are operator components |
| Important: the separator rule excluded a trailing-comma argument group (`Foo(#if X 1, #endif 2)`) | 5.4: the rule applies only between two completing derivations; separator-trailed arms count; preservation fixture |
