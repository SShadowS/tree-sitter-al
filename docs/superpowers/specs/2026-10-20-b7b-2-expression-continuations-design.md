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
  (every consecutive prefix), and from a region root to a leading prefix (6.3); this includes the typed prefix
  between an `in_expression`/`is_expression`/`as_expression`'s `operator` and its typed `right` (execution
  amendments, Task 4 item 5): the prefix is in the region of the `in`/`is`/`as` node, its arm's typed `operand` (a
  list, a type) enters as one atom like the `right`, which stays a boundary;
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

## Execution amendments

### Task 3: attachment spike (4.4)

Throwaway branch `spike/b7b-2-attachment`, head `27fdabda` (sketches v1 `86fcd673`, v3 `252f7781`, v4 `296906a3`,
v5 `27fdabda`; v5 is the recorded grammar, `git show 27fdabda:grammar.js`). The branch is kept at least until the
Task 10 review. This section is self-contained: trees, conflicts and dynamic values are all below. Each input was
parsed with
`tree-sitter parse -d normal` (directives on their own lines). tree-sitter's `-d` log does not report a decision made
when two stack versions MERGE (`ts_stack_merge` keeps the higher dynamic precedence silently); where a row is decided
there, the evidence is an ablation that changes the value and flips the tree.

**Generator rule used throughout** (tree-sitter 0.27 `build_parse_table.rs` / `item.rs`): an item's precedence and
associativity are those of the step BEFORE the dot; shift precedence comes from in-progress items (`step_index > 0`)
whose next symbol can start the lookahead; associativity only from the reduce item. So a `prec.right(n, seq(..., X,
optional(tail)))` makes `X • #if` a static shift into the tail, and a `prec(-1)` reduction loses statically to any
competing reduction at 0. Every fix below either takes the tail step out of the precedence-carrying rule (a hidden
rule) or equalises the competing reductions, then declares the conflict so GLR keeps both.

**Static decisions found (the B7b-3 amendment 5 trap), each measured and restructured:**
1. `ternary_expression`'s `prec.right(1)` around a condition or else tail: the tail shift beat every reduce at `e •
   #if`, so `x := 1 #if X Foo(); #endif` (statement group), `Foo(1 #if X , 2 #else , 3 #endif)`,
   `x := Ok ? 1 : 2 #if X Foo(); #endif` and `Foo(Ok ? 1 : 2 #if X , 3 #endif)` ERRORed (v1). Fix: hidden
   `_ternary_condition`, `_ternary_else`, `_range_right`, each `choice(plain, prec.dynamic(1, seq(operand, tail)))`;
   `_ternary_else`'s plain arm keeps `prec.right(1)` and `_range_right`'s `prec.left(0)` (base reductions).
2. The tail rule's own `prec.right`: `#if` after a root tail's `#endif` was a static shift into a consecutive tail,
   so `Foo(1 #if X + 2 #endif #if Y , 3 #endif)` read both groups as comma-less argument arms (v2). Fix: no
   `prec.right`; a root tail is `_tail_group cont* [prec.dynamic(1, tail)]` and a NESTED tail (an arm item,
   `alias(_nested_tail, preproc_conditional_expression_tail)`) has no trail, so an operator after a nested `#endif`
   belongs to the arm and `+` after a root `#endif` is outside the host's follow set (no conflict); `#if` there is a
   declared fork `[preproc_conditional_expression_tail]`.
3. `call_statement`'s and `_expression_statement`'s `prec(-1)` (B6/B7b-3): at a statement start `#if X Foo #endif`
   the bare name's `call_statement` reduction lost statically to the operand-group arm's (0), so every bare call alone
   in a statement-group arm ERRORed (v3; 43 `b7b3_case_separator_test` cases and 3 `b7b3_call_terminator_test`
   cases). v4 tried arm names at `prec(-1)` instead: that made literal and call arms lose statically to argument and
   pattern atoms (rows 6 and 7 regressed). v5 fix: both statement rules at prec 0, with the competitors that needed the
   -1 removed instead: `assignment_statement.left` is `_assign_target` (postfix-safe atoms or a receiver group: no
   binary, unary, literal, list or ternary left, so no statement starts with `[`, `-` or a literal), and
   `member_expression.object` / `subscript_expression.object` are `_postfix_operand` (the receiver set of 3.4, plus an
   aliased receiver group whose arms are `_postfix_operand`); binaries, unaries, ternaries and list literals were
   statically dead in those positions. Declared: `[call_statement, _postfix_operand]`,
   `[_expression_statement, _postfix_operand]` and their case-pattern supersets.
4. `_case_pattern_run`'s `prec.right`: once an operand group may start a pattern, `p , • #if` was a static shift
   (operand group) and `DATABASE::"A", #if ... DATABASE::"B", #endif ...` ERRORed. Fix: `prec.right` on the repeat
   only, trailing comma bare, `[_case_pattern_run]` declared.
5. `_dangling_operand` with `_expression`: the `_expression -> _continuation_operand` reduction had to precede the
   operator and the binary shift beat it, so the production prefix shape (dangling `or`,
   `preproc_dangling_operator_continuation_test`) ERRORed. Fix: `operand: _continuation_operand` (5.1 fragment site).

**`_continuation_operand` mechanism (5.2): removal, not a penalty.** `_expression := _continuation_operand |
ternary_expression | prec.left(1, assignment_expression)`, where `_continuation_operand` is today's primary choice
without the last two (it carries `reserved('code_names')`). Every left-recursive or operator-adjacent operand takes
`_continuation_operand`: binary `left` and `right`, `in`/`is`/`as` `left`, `unary_expression.operand`, the ternary
condition, the tail items' operands, `_dangling_operand`, the B3 form's operand, operand-group arms. A ternary there
was statically dead in the base grammar (every binary, unary and postfix level outranks the ternary's 1), so only dead
derivations go; with them gone no tail-operand state contains a ternary item. The four declared conflicts that named
`_expression` (`filter_value`, `_plain_name`, `_implementation_head`, `_property_value`/`option_member`) now name
`_continuation_operand`. Shown: with tail operands back on `_expression` the generator immediately reports a ternary
inside a tail item (`_continuation_operator _ternary_condition ? _expression : ...`).

**Root rule (5.2), also by removal.** At every root, the tail-bearing production takes `_continuation_operand`:
`choice(field(f, _expression), prec.dynamic(1, seq(field(f, _continuation_operand), tail)))` (assignment:
`prec.dynamic(11, ...)` inside the rule's 10; nested `prec.dynamic` keeps the larger absolute value, measured). A root
whose expression is a ternary or a range therefore has no tail derivation of its own: the tail can only attach to the
inner `else_value` / range right. This replaces 5.1's `expr, optional(tail)` shape for `contSlot`; trees are the
same for every input whose root expression is not a ternary or range.

**Per row (v5).** "Fork" = both derivations alive at the decision; "merge" = decided at the stack merge.

Trees are abbreviated: directive nodes and `condition:` are omitted, the host is `codeunit 50100 P`, and directives
sit on their own lines. "Losing tree" is the fixture mutation that must fail. Where removal leaves no losing derivation
in v5, the column gives the base tree (ad3190f) and the ablation result.

| # | input | both reach? / deciding action | mechanism | winning tree | losing tree |
|---|---|---|---|---|---|
| 1a | `x := Ok ? 1 : 2 #if X + 3 #endif;` | no outer derivation in v5. The fork at `#if` is with the statement group, which dies at `+` (`detect_error lookahead:+`) | removal (root rule) + item 1 | `right: (ternary_expression condition then_value else_value: (integer) (preproc_conditional_expression_tail operand: (integer)))` | base: `right: (ternary_expression condition then_value else_value)` with the tail a SIBLING of `right` in `assignment_statement`. Ablation (outer derivation restored): `select_earlier symbol:_statement` |
| 1b | `x := [1..5 #if X + 2 #endif];` | no outer derivation; the list-element reading dies at `+` | removal (list first-element tail production is `_continuation_operand`, never a range) + item 1 | `(list_literal (range_expression left right: (integer) (preproc_conditional_expression_tail operand: (integer))))` | base: `(list_literal (range_expression left right) (preproc_conditional_expression_tail operand: (integer)))`. Ablation `_range_right` -1: still the inner tree (no outer derivation) |
| 1c | `x := Ok or true #if X and false #endif or Ok ? 1 : 2;` (5.2) | the assignment-root reading dies at `?` (`detect_error lookahead:and`/`?` in the forks) | removal (`_continuation_operand` in tail items); `_ternary_condition` root | `right: (ternary_expression condition: (logical_expression left: (identifier) right: (boolean)) (preproc_conditional_expression_tail operand: (boolean) operand: (identifier)) then_value: (integer) else_value: (integer))` | base: `right: (logical_expression Ok true)` with an assignment-root tail whose last `operand:` is `(ternary_expression Ok 1 2)`. Ablation (tail operand `_expression`): generate reports new conflicts with a ternary inside a tail item |
| 2 | `i2 := i #if X as IFoo #endif;` | fork, 5 versions. `select_higher_precedence symbol:statement_block, prec:11, ... other_prec:10` | assignment tail production `prec.dynamic(11)`. Nested `prec.dynamic` keeps the larger absolute value: 9 inside 10 reads 10 and gives `select_earlier`. Operators: `_expression_continuation` gains `in_keyword list_literal` and `is/as_keyword type_specification` arms | `right: (identifier) (preproc_conditional_expression_tail operator: (as_keyword) operand: (type_specification (identifier)))` | `right: (identifier)`, then a sibling `(preproc_conditional_statement (call_statement function: (identifier)) (call_statement function: (identifier)))` (base tree; ablation ties) |
| 3a | `Foo(1 #if X + 2 #endif);` | fork at `#if`, merge at `)` (state 5130) | `_argument_expression` tail production `prec.dynamic(1)`. Ablation -1 flips the tree | `arguments: (argument_list (integer) (preproc_conditional_expression_tail operand: (integer)))` | `(argument_list (integer) (preproc_conditional_arguments (unary_expression operand: (integer))))` |
| 3b | `Foo(1 #if X + 2 #endif #if Y + 3 #endif, 2);` | `select_higher_precedence symbol:_argument_expression_list, prec:2 ... other_prec:1` | consecutive step `prec.dynamic(1)`. Without it (v3): `select_earlier` | `(argument_list (integer) (preproc_conditional_expression_tail operand: (integer) (preproc_conditional_expression_tail operand: (integer))) (integer))` | `(argument_list (integer) (preproc_conditional_expression_tail operand: (integer)) (preproc_conditional_arguments (unary_expression operand: (integer))) (integer))` |
| 3c | `Foo(1 #if X + 2 #endif #if Y , 3 #endif);` | fork; the consecutive tail dies at `,` | item 2 | `(argument_list (integer) (preproc_conditional_expression_tail operand: (integer)) (preproc_conditional_arguments (integer)))` | v2 (static consecutive shift): `(argument_list (integer) (preproc_conditional_arguments (unary_expression operand: (integer))) (preproc_conditional_arguments (integer)))` |
| 4 | `case i of 1..5 #if X + 2 #endif : Foo(); end;` | `select_higher_precedence symbol:case_branch, prec:1 ... other_prec:0`. No `prec(25)` interference measured | `_range_right` tail production `prec.dynamic(1)`. Ablation -1 flips the tree | `(case_branch pattern: (range_expression left right (preproc_conditional_expression_tail operand: (integer))) body: (call_expression))` | `(case_branch pattern: (range_expression left right) (preproc_conditional_case_patterns pattern: (unary_expression operand: (integer))) body: (call_expression))` |
| 5 | `#if X a #else b #endif .Foo();` | fork at `a • #else`; the statement group dies at `.` | item 3 (receiver set, statement rules at 0) | `(call_expression function: (member_expression object: (preproc_conditional_operand operand: (identifier) operand: (identifier)) member: (identifier)) arguments: (argument_list))` | statement-group reading, which completes nowhere in v5. Base: `(preproc_conditional_statement (call_statement) (preproc_else) (call_statement)) (ERROR) (call_expression Foo)` |
| 5' | `#if X Foo #endif` (alone in a block) | fork at `Foo • #endif`; the operand reading dies at `end` | item 3 | `(preproc_conditional_statement (call_statement function: (identifier)))` | v3 (static -1 loss): `(ERROR (preproc_conditional_operand ...))` |
| 6a | `Foo(#if X 1 #else 2 #endif + 3);` | 3 versions (argument group, operand group, receiver group). The receiver dies at `+`; merge at `)` | operand group `prec.dynamic(-1)`, plus `additive_expression`'s second production `prec.dynamic(2, seq(field('left', preproc_conditional_operand), ...))` (net +1 over the comma-less reading's 0). Its shift of `+`/`-` is static over `_continuation_operand -> group`. Only `+`/`-` need it, because a comma-less reading needs a signed next item. Ablation 2 -> 0 flips the tree | `(argument_list (additive_expression left: (preproc_conditional_operand operand: (integer) (preproc_else) operand: (integer)) right: (integer)))` | `(argument_list (preproc_conditional_arguments (integer) (preproc_else) (integer)) (unary_expression operand: (integer)))` |
| 6b | `x := [#if X 1 #else 2 #endif + 3];` | single derivation: list-element groups cannot open a list, and the receiver dies at `+` | none | `(list_literal (additive_expression left: (preproc_conditional_operand ...) right: (integer)))` | none in v5. Base: ERROR |
| 7 | `case i of #if X 1 #else 2 #endif + 3: Foo(); end;` | fork; competitors are `preproc_split_case_branch` and the pattern group; merge | as 6a. Ablation 2 -> 0 flips the tree | `(case_branch pattern: (additive_expression left: (preproc_conditional_operand ...) right: (integer)) body: (call_expression))` | `(case_branch (preproc_split_case_branch pattern: (integer) (preproc_else) pattern: (integer) pattern: (unary_expression operand: (integer)) body: (call_expression)))` |
| 7' | `case i of 1, #if X 2 #else 3 #endif + 4: Foo(); end;` | `select_higher_precedence symbol:case_branch, prec:1 ... other_prec:0` | item 4, then as 6a. Ablation 2 -> 0 flips the tree | `(case_branch pattern: (integer) pattern: (additive_expression left: (preproc_conditional_operand ...) right: (integer)) body: ...)` | `(case_branch pattern: (integer) (preproc_conditional_case_patterns pattern: (integer) pattern: (integer)) pattern: (unary_expression operand: (integer)) body: ...)` |
| 8a | `Foo(1 #if X , 2 #else , 3 #endif);` | no operand derivation: a group cannot follow a complete operand. The tail dies at `,` | none | `(argument_list (integer) (preproc_conditional_arguments (integer) (preproc_else) (integer)))` | none derivable. v1: ERROR (static ternary-condition shift, item 1) |
| 8b | `case i of 1 #if X , 2 #endif : Foo(); end;` | no operand derivation: no arm starts with `,` | none | `(case_branch pattern: (integer) (preproc_conditional_case_patterns pattern: (integer)) body: ...)` | none derivable |
| P | `Foo(#if X 1, #endif 2);` | one version throughout | none | `(argument_list (preproc_conditional_arguments (integer)) (integer))` | none derivable |
| P' | `Foo(#if X 1 #else 2 #endif);` | fork, 3 versions; the argument group wins. **Unproven:** not ablated, so the decider is not shown | operand group `prec.dynamic(-1)` is the intended decider | `(argument_list (preproc_conditional_arguments (integer) (preproc_else) (integer)))` | `(argument_list (preproc_conditional_operand operand: (integer) (preproc_else) operand: (integer)))` |

**Task 10 obligation (P').** Ablate the operand group's -1 (to 0 and to +1), prove that a dynamic-precedence
comparison decides `Foo(#if X 1 #else 2 #endif)`, and pin a losing-tree fixture.

**Dynamic and static precedence values (v5), all of them:**

| site | value | role |
|---|---|---|
| `assignment_statement` tail production | `prec.dynamic(11)` inside the rule's `prec.dynamic(10)` | tail beats the torn statement group (row 2) |
| `_argument_expression` tail production | `prec.dynamic(1)` | tail beats a comma-less argument arm (row 3a) |
| `list_literal` first-element tail production | `prec.dynamic(1)` | tail beats a comma-less element reading |
| `_ternary_condition` tail production | `prec.dynamic(1)` | condition root |
| `_ternary_else` tail production; plain arm | `prec.dynamic(1)`; plain arm `prec.right(1)` (base ternary reduce) | else root |
| `_range_right` tail production; plain arm | `prec.dynamic(1)`; plain arm `prec.left(0)` (base range reduce) | range root (row 4) |
| consecutive step of a root tail | `optional(prec.dynamic(1, tail))` | consecutive beats tail + comma-less group (row 3b) |
| `preproc_conditional_operand` | `prec.dynamic(-1)` | alone it loses to a list group (P', unproven) |
| receiver group (`_receiver_group`, aliased to `preproc_conditional_operand`) | `prec.dynamic(-1)` | as the general group; it never reached a both-complete decision in the measured inputs |
| `additive_expression` operand-group-left production | `prec.dynamic(2)` | net +1 against comma-less readings (rows 6a, 7, 7') |
| `call_statement`, `_expression_statement` | static `prec(-1)` removed (now 0) | item 3 |
| `_case_pattern_run` | `prec.right` on the repeat only | item 4 |
| `preproc_conditional_expression_tail` | `prec.right` removed | item 2 |

**Declared-conflict delta (base 230 -> v5 255: 6 removed, 31 added).** "Demanded at" is generate's symbol sequence
(the `interface X {` prefix is omitted).

| change | entry | reason / demanded at |
|---|---|---|
| removed | `[_argument_expression]` | generate reports it unnecessary, superseded by `[_expression, _ternary_condition, _argument_expression]` |
| removed | `[assignment_statement]` | unnecessary, superseded by `[assignment_statement, _expression, _ternary_condition]` |
| renamed | `[filter_value, _expression]` -> `[filter_value, _continuation_operand]` | the atom reduction is now `_continuation_operand -> atom` |
| renamed | `[_expression, _plain_name]` -> `[_continuation_operand, _plain_name]` | same |
| renamed | `[_implementation_head, _expression, _plain_name]` -> `[_implementation_head, _continuation_operand, _plain_name]` | same |
| renamed | `[_property_value, option_member, _expression]` -> `[_property_value, option_member, _continuation_operand]` | same |
| added | `[_expression, _ternary_condition]` | root fork `e • #if`: the root's tail or a following group vs a ternary-condition tail. Demanded at `property_name = _continuation_operand • preproc_open` |
| added | `[_expression, _ternary_condition, list_literal]` | the same at a list's first element: `property_name = [ _continuation_operand • preproc_open` |
| added | `[_expression, _ternary_condition, _argument_expression]` | the same in an argument: `continue_as_identifier ( _continuation_operand • preproc_open` |
| added | `[assignment_statement, _expression, _ternary_condition]` | the same at the assignment root: `begin _expression := _continuation_operand • preproc_open` |
| added | `[_expression, _range_right, _ternary_condition]` | the same at the range right: `[ _expression .. _continuation_operand • preproc_open` |
| added | `[_expression, _ternary_condition, _ternary_else]` | the same at the else root: `_ternary_condition ? _expression : _continuation_operand • preproc_open` |
| added | `[_operand_arm, _expression, _ternary_condition]` | an operand-group arm (nested tail item) vs a B11 arm value with a root tail vs a ternary-condition tail: `property_name = preproc_if _continuation_operand • preproc_open` |
| added | `[_operand_arm, _expression]` | argument group arm vs operand group arm (rows 6a, P'): `continue_as_identifier ( preproc_if _continuation_operand • preproc_elif` |
| added | `[preproc_conditional_expression_tail]` | item 2: `#if` after a root tail's `#endif` (consecutive tail vs the host's groups). Demanded at `property_name = _negative_integer _preproc_operator_arms _continuation_operand • preproc_open` |
| added | `[preproc_conditional_expression_tail, _nested_tail]` | a B11 arm value with a root tail (with trail) vs an operand-group arm with a nested tail (no trail): `property_name = preproc_if _continuation_operand _tail_group • =` |
| added | `[_case_pattern_run]` | item 4: `case _expression of _single_pattern , • preproc_open` |
| added | `[_single_pattern, _continuation_operand]` | a pattern followed by a pattern group vs the same atom as a ternary condition (range `left` is `_expression`) with a tail: `case _expression of identifier • preproc_open` |
| added | `[call_statement, _single_pattern, _continuation_operand]` | in a case group arm: statement vs pattern vs operand-group arm followed by a nested tail: `case _expression of preproc_if identifier • preproc_open` |
| added | `[_expression_statement, _single_pattern, _continuation_operand]` | the same with a call: `... preproc_if call_expression • preproc_open` |
| added | `[call_statement, _postfix_operand]` | item 3, the statement-start fork (row 5): `begin preproc_if identifier • preproc_elif` |
| added | `[_expression_statement, _postfix_operand]` | the same with a call: `begin preproc_if call_expression • preproc_elif` |
| added | `[_postfix_operand, _continuation_operand]` | receiver-group arm vs general operand-group arm in any expression slot: `property_name = preproc_if continue_as_identifier • preproc_elif` |
| added | `[_property_value, option_member, _postfix_operand, _continuation_operand]` | the same in a property value, where B11 arms and option members also read the atom: `property_name = preproc_if identifier • preproc_elif` |
| added | `[property_expression, _postfix_operand, _continuation_operand]` | a B11 property-value arm's `property_expression` vs receiver / general group arms. Reason inferred; the exact symbol sequence was not recorded: the generator demanded it in a property-value `#if` arm after the two entries above |
| added | `[_assign_target, _continuation_operand]` | an arm atom followed by `:=`: assignment target (statement arm) vs `assignment_expression` left (operand arm): `case _expression of preproc_if continue_as_identifier • :=` |
| added | `[_postfix_operand, _single_pattern, _continuation_operand]` | a case group arm: receiver arm vs pattern vs general arm: `case _expression of preproc_if identifier • preproc_elif` |
| added | `[call_statement, _postfix_operand, _single_pattern, _continuation_operand]` | the same nested one level, with a statement: `case _expression of preproc_if preproc_if identifier • preproc_elif` |
| added | `[_expression_statement, _postfix_operand, _single_pattern, _continuation_operand]` | the same with a call: `... preproc_if preproc_if call_expression • preproc_elif` |
| added | `[call_statement, _single_pattern]` | became a tie when `call_statement` lost `prec(-1)`; before, `_single_pattern` won statically: `case _expression of preproc_if preproc_if preproc_else identifier • preproc_close` |
| added | `[_expression_statement, _single_pattern]` | the same with a call: `... preproc_else call_expression • preproc_close` |
| added | `[_attribute_argument, _literal_value]` | reason not stated with certainty. Demanded in v1 at `[ identifier ( preproc_if string_literal • preproc_elif` (attribute-argument group arm `'a'` vs the same literal as an operand-group arm reached through `_attribute_argument`'s `member_expression` object). It stayed required in v5, where that object is `_postfix_operand` |
| added | `[_attribute_argument, _postfix_operand]` | attribute-argument group arm vs a receiver-group arm (the object of `_attribute_argument`'s `member_expression`): `[ identifier ( preproc_if identifier • preproc_elif` |

**Sketch metrics** (base 23,737 / 7,482 / 1,279; parser.c 53,974,023 bytes): v1 26,554 / 9,254 / 1,284; v3 26,734 /
9,317 / 1,290; **v5 27,931 / 10,119 / 1,294** (STATE_COUNT +17.7%, LARGE_STATE_COUNT +35.2%), parser.c 65,912,122
bytes (62.9 MiB), declared conflicts 230 -> 255. The sketch holds Phase A, B and C pieces at once (tails, three roots,
placement A operand group, receiver set), so the per-phase +3% guideline is not measured here; Tasks 4, 7 and 10 must.

**Production and suite (v5).** `tree-harness verify` against the Phase 0 baselines: BC.History, DC and BC28.1
byte-identical (the `_continuation_operand`, `_postfix_operand`, `_assign_target` and statement-precedence changes
remove dead derivations only); BCApps-29.0 one file, `ERMPurchaseReportsIII.Codeunit.al`, which already holds ERRORs
(recovery shape only). `tree-sitter test`: 3,268 / 3,429; of the 161 failures 142 are B7a gap witnesses that now
parse, 1 an op-only REJECTED representative, 17 deliberate negatives whose ERROR shape moved (still ERROR), and one
real regression: `preproc_whole_value_arms_test` "Whole-value #if arms" (`Visible = #if X A and B #else C #endif ;`):
placement A's operand group competes with B11's whole-value group in a property value and the tree ERRORs. Task 10
must keep the operand group out of property-value sites (placement B there) or resolve that competition.

#### User decisions (2026-10-20, after the Task 3 spike)

1. **Cost.** The user accepted the spike's measured cost without reduction ("Raise budget, no reduction"). Tasks 4, 7
   and 10 implement the v5 mechanisms directly. A whole-branch reference replaces the +3%-per-phase guideline of 8.5:
   STATE_COUNT up to **28,770** (v5's 27,931 +3%) and LARGE_STATE_COUNT up to **10,423** (v5's 10,119 +3%). If either
   is exceeded, the task stops and reports. Two stops are unchanged: parser.c at 80 MiB, and the `tools.perf ab` gate
   (both medians of `ratio_a_over_b` >= 0.97 against main).
2. **Approved deviations.** The user approved the following as spec amendments. The task that implements each one
   must pin it with fixtures, and the existing B6/B7b-3 fixtures plus the four-corpus byte-identity check
   (`tree-harness verify` against the Phase 0 snapshots, `tools.perf delta`) are the gate for it.
   - Rules outside B7b-2's list:
     - `call_statement` and `_expression_statement` drop their static `prec(-1)` and run at prec 0, with the declared
       conflicts `[call_statement, _postfix_operand]` and `[_expression_statement, _postfix_operand]` and their
       case-pattern supersets.
     - `member_expression.object` and `subscript_expression.object` become `_postfix_operand`, the receiver set of
       3.4 plus an aliased receiver group. They no longer accept a list literal, binary, unary or ternary object.
     - `assignment_statement.left` becomes `_assign_target`: postfix-safe atoms or a receiver group. It no longer
       accepts a binary, unary, literal, list or ternary left.
     - Every binary `left`/`right`, `in`/`is`/`as` `left` and `unary_expression.operand` becomes
       `_continuation_operand`, which is `_expression` without the ternary and assignment expressions.
     - `_case_pattern_run` keeps `prec.right` on its repeat only, has a bare trailing comma, and declares
       `[_case_pattern_run]`.
   - Shape deviations from 5.1:
     - `contSlot` expands to `choice(field(f, _expression), prec.dynamic(1, seq(field(f, _continuation_operand),
       tail)))` instead of `expr, optional(tail)`. Inside the assignment rule's 10 this branch is `prec.dynamic(11)`.
     - A nested tail (an arm item) has no trailing items: whatever follows its `#endif` belongs to the enclosing arm.
     - A root tail's trail is `cont* [tail]`. The consecutive group owns everything after it, and the consecutive
       step carries `prec.dynamic(1)`.
     - The hidden root rules `_ternary_condition`, `_ternary_else` and `_range_right` (coordinator ruling,
       2026-10-20, within the user's approval to implement the v5 mechanisms directly). They exist so the tail step
       is out of `ternary_expression`'s `prec.right(1)` and `range_expression`'s `prec.left(0)`; otherwise the tail
       shift is static (item 1). Obligation for Task 7: every continuation key they move gets a
       `tools/b7_audit/key-aliases.tsv` row, with frozen cell ids unchanged.

### Task 4: Phase A grammar

Implemented: the recursive tail (`_tail_group`, `_nested_tail`, `_tail_item`, root trail `cont* [prec.dynamic(1,
tail)]`, no `prec.right`), `_continuation_operand` by removal (`_expression := _continuation_operand |
ternary_expression | prec.left(1, assignment_expression)`; every binary, unary and in/is/as operand and every tail and
prefix operand takes it), the typed `in`/`is`/`as` continuation arms, the prefix-arm fragment site
(`_dangling_operand := operand, _tail_item*, operator`), and the root rule at the assignment (`prec.dynamic(11)`)
and argument (`prec.dynamic(1)`) roots. Rows 2, 3a, 3b, 3c and P behave as the Task 3 table says; their fixtures are
`test/corpus/b7b2_tie_break_test.txt`, with a recorded losing-tree mutation each (P has no derivable losing tree).

**Taken from a later phase, with the reason:**
- The hidden roots `_ternary_condition`, `_ternary_else` and `_range_right` (Phase B). With the root rule at the
  assignment and argument roots but no inner roots, a tail after a ternary or a range had no derivation at all:
  measured, 36 B-owned RC5 cells went from SILENT/MIXED to GAP and 8 SILENT witnesses of `test_silent.py` broke. With
  them, rows 1a, 1b and 1c hold (fixtures in `b7b2_tie_break_test.txt`, mutations recorded). Cost: +130 states.
  Their census keys moved: six `tools/b7_audit/key-aliases.tsv` rows (`bnd:ternary_expression:condition|else_value`,
  `bnd:range_expression:right`, `end` and `start`, to the hidden rules' keys), frozen cell ids unchanged; this
  discharges that part of Task 7's obligation.

**Departures from v5, each measured:**
1. `member_expression.object` and `subscript_expression.object` are `_continuation_operand`, not v5's
   `_postfix_operand` (Phase C, with the receiver group). With `_expression` there, an operand before `[` or `.` had
   two reductions (`_expression` for the object, `_continuation_operand` ending a B3 tail): generate refused
   (`... _preproc_operator_arms _continuation_operand • '['`). A ternary or assignment-expression object was
   statically dead, so this removes dead derivations only (four corpora byte-identical).
2. `assignment_statement.left` and `assignment_expression.left` are `_continuation_operand`, not v5's `_assign_target`
   (Phase C). With `_expression`, the ternary-condition root's `#if` shift reached every statement start and beat
   `call_statement`'s `prec(-1)` statically: 44 B7b-3 fixtures failed (`b7b3_case_separator_test` and kin, a bare
   call before a `;` group) and 5 others. `call_statement` and `_expression_statement` keep their `prec(-1)` in Phase A (v5 drops it in
   Phase C, where the operand group needs it). A ternary or assignment-expression left was dead (`c ? a : b := 1`).
3. The list literal's first element keeps its base shape `_list_element, optional(tail)` instead of the root rule:
   the removal form moves every list census key (`bnd:list_literal:1.0.0`, `1.0.2.0.1`, `occ:list_literal:1.0.2.0.0`)
   and its new hosts cannot be aliased (the alias check refuses hosts the retired rows never covered). A ternary or
   range first element followed by a tail now has two derivations; the inner root's `prec.dynamic(1)` wins (rows 1b
   and the inner-root fixture pin it), as at the unconverted if/while/exit/for/subscript roots. Task 7 converts it with
   `contSlot` and owns its census keys. The `[_expression, _ternary_condition, list_literal]` conflict is gone.
4. The prefix arm carries `_tail_item*` (v5 had none): spec 5.1's fragment site, `a + #if X b #if Y + c #endif +
   #endif d` (fixture "a tail inside a prefix arm"; alc `prefixes/fragment.al`). +9 states.
5. Typed operand prefixes in `in`/`is`/`as` (spec 5.3 last sentence; alc accepts every configuration,
   `keyword_ops/{in,is,as}-prefix.al`): `in_expression` takes `optional(alias(_in_operand_prefix,
   preproc_operand_prefix))` with arms `operand: list_literal, operator: in_keyword`; `is`/`as` take
   `_type_operand_prefix` with arms `operand: type_specification, operator: is|as`. The arm's type is `_dangling_type`,
   a `type_specification` without option, array, List and Dictionary types (aliased to `type_specification`): with
   the full type the dangling keyword became valid after every option-list comma and BCApps
   `GetCoverage.Page.al` (`Option ...,"IN",IS,IT`) ERRORed. +190 states. They fix the A-owned `prefix/membership`
   and `prefix/type-test` cells (58 cells, all the `[list] in` / `Type as` arm shape).
6. §5.3 scope decision (Task 3 review carry-over): `in`/`is`/`as` are typed arms of `_expression_continuation`, not
   members of `_continuation_operator`, so the B3 operator-only form and the generic prefix arm do not take them. Gaps
   this leaves, no B7a cell covering them: `b := i #if X in #endif [1];` (operator-only `in`), a generic prefix arm
   ending in a keyword operator inside another binary (`x := a + #if X b in #endif [1];`), and a typed prefix arm
   with continuations before its keyword (`Ok in #if X [true] and Ok in #endif [false]`). Owner: Phase C (spec 6.3,
   prefixes). Fix round 1: alc accepts all three in every configuration
   (`tools/alc_probe/cases/b7b-2/keyword_ops/in-operator-only.al`, `in-ends-generic-prefix.al`,
   `in-prefix-with-continuation.al`); `:error` witnesses in `test/corpus/b7b2_scope_gap_test.txt`; docs/deferred-work.md
   item 51.

**Known limit (fix round 1, user decision 2026-10-20):** N consecutive groups at the assignment or argument root parse
in quadratic time (fitted ~2.9-3.2, last step ~3.8 per doubling, against 8.5's 2.5); not fixed, because the longest
back-to-back `#if` run in the four corpora is 3. Measurements, cause and the rejected linear shapes: docs/deferred-work.md
item 52. Task 6 classifies the `root_tails` / `argument_tails` series as an explicit exception.

**Consecutive groups, two shapes (for the Task 13 docs):** at a root (and after a B3 form) the second group is the
LAST CHILD of the first (`cont* [tail]`), so N consecutive groups nest N deep; inside an arm (tail or prefix arm)
groups are SIBLINGS, a nested tail having no trail. Both pinned in `b7b2_tail_test.txt`.

**B7a census** (`tools/b7_audit/census.py`): `_continuation_operand` counts as an expression name like `_expression`
(else every binary and unary slot key went stale and 265 pairs were missing), `_expression` itself is not a host, and
the root rule's two arms of one slot are one boundary with an optional tail (fielded: `assignment_statement.right`;
unfielded top-level choice: `_argument_expression`), so those keys are unchanged. Sixteen `equiv` registry rows
(no new cells) cover the new routes: the six alias live keys, a continuation inside a prefix arm, the nested B3
operand (`_nested_tail`), the B3 operand at the ternary and range roots, and a list literal as the typed operand of an
`in` arm (four list keys).

**Oracle until Task 5:** `contracts.py` lists the new tail slots (`preproc_conditional_expression_tail`,
`preproc_operand_prefix`, `range_expression`, `ternary_expression` children) and the typed prefixes (in/is/as
children) as `unsupported`; the new fixtures' nested and consecutive tails are `debt(B7b-2/A-oracle)` in
`tools/config_oracle/fixture-classes.tsv` (Ruling S1; `fixtures.py` accepts the three `B7b-2/<phase>-oracle` owners).

**Metrics** (base 23,737 / 7,482 / 1,279; parser.c 53,974,023 bytes): STATE_COUNT 26,440 (+11.4%),
LARGE_STATE_COUNT 9,043 (+20.9%), SYMBOL_COUNT 1,294, parser.c 61,390,503 bytes (58.5 MiB); declared conflicts 230 ->
237 (removed `[_argument_expression]`, `[assignment_statement]`; four renamed `_expression` -> `_continuation_operand`;
added `[preproc_conditional_expression_tail]`, `[_expression, _ternary_condition]` and its argument, assignment,
range-right and else supersets, `[_single_pattern, _continuation_operand]`, `[call_statement | _expression_statement,
_single_pattern, _continuation_operand]`). Under the whole-branch reference (28,770 / 10,423).

### Task 7: Phase B grammar

Implemented: `contSlot($, expr, fieldName?, dyn = 1)` (`grammar.js`, beside `strictListBody`), the root rule of the
Task 3 amendment, `choice(f(expr), prec.dynamic(dyn, seq(f(_continuation_operand), tail)))`. The existing hosts moved
onto it first (refactor checkpoint: full suite 3,462/3,462, four corpora byte-identical, BCApps-29.0's known
recovery-only file unchanged); then every 5.1 root: repeat-until condition, case and split case-end expression,
ternary then, parenthesized inner, range left, for start, subscript 2nd+ index, list 2nd+ element (and the first,
Task 4 departure 3 resolved), with record, foreach iterable, the seven split-if head conditions, the four split-call
argument positions. The property route is untouched. v5 had only the ternary, range-right and list-first roots; every
other root is new here.

**Departures, each measured:**
1. **Hidden root rules, not an inlined `contSlot` (5.1 "inlined, never a hidden rule").** One hidden rule per field,
   `_region_root_<field>` (condition, expression, start, end, iterable, record, return_value, left, then_value,
   index), plus `_region_root` (unfielded: parenthesized, subscript 2nd+, split-call) and `_region_root_list_element`;
   each is `contSlot` and the field propagates, so the trees are the inline form's. Inlined at every root:
   STATE_COUNT 28,959, LARGE 10,421, parser.c 70,343,945 bytes, above the user's 28,770 reference. Attribution by
   stubbing one group back to the plain slot: split-if heads -1,707 / -1,104 (seven hosts each copying the expression
   automaton), case -288, every other group under 100. Shared hidden rules: 26,611 / 9,210. The reason 5.1 gave for
   inlining (census keys) is kept by teaching the census: `census._region_roots` reads every `_region_root*` rule
   (refusing one that is not a `contSlot` body) and expands it into its callers like `_list_element`, slot = its
   field, end/between edge with the optional tail; no slot key moved because of the wrappers. The assignment root
   stays inline (`dyn` 11 inside the rule's 10, v5) and `_argument_expression` already was this hidden form.
   **Cost of this departure:** `tools/query_coverage` skips fields inside hidden rules, so its
   `fields|skipped|hidden-rule` cluster grew 114 -> 120 (baseline accepted) and qc no longer checks the host fields
   that moved into `_region_root*` (condition, expression, start, end, iterable, record, return_value, left,
   then_value, index). `tools/check-field-types.py` (validate Step 5b) carries that check instead: one row per host
   field reached through a `_region_root*` rule, pinning its pre-Phase-B multiple/required shape (24 rows, fix
   round 1 added `exit_statement.return_value` and the ten split-if hosts' `condition`); each row fails when its
   `multiple` or `required` is flipped.
2. **Dynamic precedence of a hidden root is summed, not maxed.** Inside an inlined choice the generator keeps the
   larger absolute value of the production (the host's `prec.dynamic(20)` at `if_statement` absorbed the tail arm's
   1); a hidden rule's own 1 is added to the host's total. No fixture or production tree changed.
3. **`_if_statement_no_else` takes `_region_root_condition` too** (not in the 5.1 table). With its plain field every
   `if C • then` in a case branch was a declared reduce/reduce fork between the two if rules
   (`[_if_statement_no_else, _region_root_condition]`); converting it removes the fork for +11 states and gives the
   case-branch if the same root. Census: four new tail routes (case_branch and the three split case hosts).
4. **Range left uses the hidden root, not a `_range_left` beside `_range_right`.** The hidden rule already takes the
   tail step out of `range_expression`'s `prec.left(0)` (amendment item 1); its key stays `bnd:range_expression:left`.
5. **Census keys that moved:** removing the hosts' `field, optional(tail)` pairs shifted two repeats one member left:
   `bnd:subscript_expression:0.4.0.1:between` -> `0.3.0.1`, `occ:subscript_expression:0.4.0.0` -> `0.3.0.0`,
   `bnd:list_literal:1.0.2.0.1:between` -> `1.0.1.0.1`, `occ:list_literal:1.0.2.0.0` -> `1.0.1.0.0`
   (`tools/b7_audit/key-aliases.tsv`, 19 live `equiv` registry rows, frozen cell ids unchanged). New tail routes
   (the 21 Phase B hosts) extend the existing `bnd:preproc_conditional_expression_tail:operand:*` equiv rows.

**Conflicts 237 -> 240.** Removed `[_preproc_call_prefix, _argument_expression]` (generate: unnecessary). Added, with
the symbol sequence generate demanded them at (the `interface X {` prefix omitted):
`[_expression, _ternary_condition, _region_root_left, _region_root_list_element]` at `property_name = [
_continuation_operand • preproc_open` (list element vs range left vs ternary condition); `[_expression,
_ternary_condition, _region_root_condition]` at `begin repeat until _continuation_operand • preproc_open`;
`[_region_root, _argument_expression]` at `begin preproc_if identifier ( _expression • ,` (split-call prefix
argument vs call argument in a statement arm); `[_expression, _ternary_condition, _region_root, _argument_expression]`
at `begin preproc_if identifier ( _continuation_operand • preproc_open`.

**Tie-breaks.** The 5.4 inner-root row at the Phase B roots (repeat, case, parenthesized, for start, list 2nd element)
and row 4 (`case i of 1..5 #if X + 2 #endif :`) already held at Task 6 (the Phase A inner roots win); their fixtures
now pin them against the new host derivations (`b7b2_tie_break_test.txt`; losing-tree mutations fail). The RC5 rows
1a-1c were pinned in Task 4.

**Fixture expectations: a deviation from the plan's Global Constraint.** The region-roots and tie-break trees are
hand-written. The 53 moved gap witnesses (`b7b2_<family>_test.txt`) were written with placeholder trees and filled by
`tree-sitter test -u --file-name`, which the plan forbids. Verification instead: the placeholders carried a field, so
`-u` wrote fielded trees (a `bogus:` rename fails case-expression/suffix and range/suffix); every untargeted file each
`-u` run rewrote was restored from HEAD (CLAUDE.md trap 5, `git diff --stat test/corpus` checked); the implementer
reviewed all 53 trees against the contract (tail beside the root slot inside its host, consecutive group the last
child of the first tail, nested group inside the arm, op-only the B3 form, chain trailing items) and the Task 7
reviewer sampled 33 of 53 against it. Their sources are trimmed; each header names its untrimmed B7a witness
(`tools/alc_probe/cases/b7-audit/<family>__<placement>__gap.al`), whose verdicts `alc_probe --check` confirmed on
2026-10-21 (67 witnesses, 0 drift).

**Oracle.** Every Phase B fixture validates with Task 5's region assembler (a root tail is one item of its host's
item loop); `contracts.py` lists the new hosts `consumed`. Only the split hosts (preproc_split_call_statement,
preproc_guarded_statement, preproc_split_if_statement) stay C1 for their own node type, so Ruling S1 needed no
`debt(B7b-2/B-oracle)` entry and Task 8's root-host work is reduced to verification.

**Metrics** (Phase B base 26,440 / 9,043 / 1,294; parser.c 61,390,503 bytes): refactor checkpoint (inline) 26,619 /
9,085; all roots inline 28,959 / 10,421 (rejected); hidden roots 26,611 / 9,210; final 26,622 / 9,212, SYMBOL_COUNT
1,307, parser.c 62,283,683 bytes (59.4 MiB). Phase B: +182 STATE, +169 LARGE; headroom left for Phase C 2,148 STATE,
1,211 LARGE.

### Task 10: Phase C grammar (operand groups and leading prefixes)

Implemented: `preproc_conditional_operand` (`prec.dynamic(-1)`, arms `_operand_arm` = `repeat(prefix)
field('operand', _continuation_operand) repeat(_tail_item)`) as one alternative of `_continuation_operand`; the
receiver variant (`_receiver_group`, arms `_postfix_operand`, aliased to the same node) at member/subscript object and
in `_assign_target` (assignment left); leading prefixes (`leadingPrefixed`, a third `contSlot` arm
`seq(repeat1(prefix), f(_continuation_operand), optional(tail))`, plus the same arm in `_ternary_condition`,
`_ternary_else`, `_range_right`, the property_expression leading arm and `_case_pattern_item`); every binary's
`optional(prefix)` became `repeat(prefix)` (consecutive prefixes); typed rights for `is`/`as`.

**Placement (6.3), measured by stubbing.** A (the group an alternative of `_continuation_operand`): 27,929 STATE /
10,150 LARGE, 109 of the gap witnesses parse, but the `Whole-value #if arms` fixture
(`preproc_whole_value_arms_test.txt`, case 2) regressed. B (a separate operand slot, stub): 27,951 / 10,056 with 5
extra generated conflicts, 104 witnesses parse, the whole-value fixture keeps its tree. Four-corpus parity was 0 diffs
for both (BCApps-29.0's recovery-only file aside). **Chosen: A**, with the whole-value regression fixed by moving
property_expression's four binaries out of its `prec(-2)` choice plus the declared
`[property_expression, _continuation_operand]` conflict; the fixture is a losing-tree mutation (placement A's
pre-fix tree fails it).

**Row P' ablation (5.4).** With the operand group at `prec.dynamic(-1)` or `0` the argument group wins `Foo(#if X 1
#else 2 #endif)`; at `+1` the operand group wins. So a dynamic comparison decides, and `-1` keeps the argument group
(the B7b-1 shape) with a margin.

**Additive bonus (rows 6a, 6a-minus, 7, 7').** An operand group followed by `+`/`-` competes with the comma-less
argument / pattern reading (`#if X 1 #else 2 #endif + 3` read as a group then a signed `+3`). The first version, a
whole extra additive production, broke the prefix-arm dangling operator and cost +141 STATE / +116 LARGE; replaced by
`_additive_group_left: prec.dynamic(2, preproc_conditional_operand)` as an additive left (net +1 over the argument
group). `*` has no comma-less competitor and needs none. **Fix round 1 (review I1):** the bonus fired after any
tighter operator too, `a * g + 1` -> `a * (g + 1)`, `a div g - 1` -> `a div (g - 1)`, `- g + 1` -> `-(g + 1)`,
inverting the ladder (and `2 + g + 1` nested right). A group as the right of `* / div mod` or `+ -`, or as a unary
operand, now scores +3 (`_tight_group_operand`, one more than the bonus), through one hidden operand rule per host
that carries the host's static precedence (`_tight_operand_un` 8 right, `_mul` 7 left, `_add` 6 left; a bare
wrapper drops it and `-A * B` read `-(A * B)`). Result: `(a * g) + 1`, `(a div g) - 1`, `(-g) + 1`, and `2 + g + 1`
associates left, `(2 + g) + 1`; rows 6a/7/7' unchanged (the bonus still beats the comma-less reading where no
tighter operator precedes the group). Cost +14 STATE / -2 LARGE (inline choices at three sites: 28,835; at two:
28,791, over the ceiling). Pinned by the four `tie-break ladder` fixtures (the three inversions fail with the Task 10
library; `not g and D` is a control).

**Fix round 2 (re-review): no positional bonus at all.** Round 1's +3 on the right of `+`/`-` closed the addition
before a following `*` (`a + g * b` -> `(a + g) * b`). Any dynamic score attached to a position is summed over the
tree and loses to static precedence somewhere else. So `_additive_group_left` and the `_tight_*` rules are deleted:
the group is a plain `_continuation_operand`, and the binaries' static precedence groups it like any operand, in
every position. The comma-less readings of rows 6a, 6a-minus, 7 and 7' are beaten instead by `unary_expression`'s
`prec.dynamic(-2)`: operand group -1 beats argument / pattern group 0 + unary -2. A unary decides no other GLR fork,
and two readings with the same unaries tie as before. Unforked parses ignore dynamic precedence: the production delta
is 0. The ladder matrix (`test/corpus/b7b2_ladder_matrix_test.txt`) holds 21 cases / 66 statements; every expected
tree is composed from the 3.2 ladder by an operator-precedence generator, not taken from parser output.
- It pairs every level with itself and with its adjacent levels (`*`, `-`, `in`, `and`, `or`, `=`), with G first,
  middle and last.
- It adds four-operand chains, unary `-` and `not` before G, and G inside a ternary condition.
- Pass counts (cases / statements): 29a6eb2 15/21, 56/66; 70237e8 18/21, 63/66; fix round 2 21/21, 66/66.

Cost: 28,688 STATE / 10,523 LARGE, -64 / -12 against round 1.

**Fix round 3 (re-review 2): a signed option member.** Before `;` `,` `#` or EOF the scanner lexes `-1` as one
`NEGATIVE_INTEGER`, which is not a unary. So `Visible = G - 1;` and `Visible = G -1;` read as an option-members group
followed by a comma-less `(option_member (integer))`: option group 0 against operand group -1. The two signed
`option_member` alternatives (`_negative_integer` and `seq('-', integer)`) now carry `prec.dynamic(-2)`, like the
unary. The operand reading wins: `property_expression (additive_expression left: G right: (integer))`.
`option_member` has no negative-decimal alternative, so `G - 1.5` was never affected. +54 STATE / +39 LARGE; a hidden
`_signed_option_member` rule needs an extra `[_property_value, _signed_option_member]` conflict.

The positions file `test/corpus/b7b2_ladder_positions_test.txt` (10 cases / 104 items, same generator method)
carries the ladder into every expression position: call argument first and later, list item, case pattern, exit
value, ternary then and else, if condition, repeat-until and property value.
- It adds `/`, `div`, `mod`, `+`, `xor`, `is` and `as`, groups whose arm holds an operator, and the signed forms
  `G - 1` and `G -1` (property: also `G - 1.5` and `G -1.5`).
- It also covers `G, -1` in a call argument and in a list. In an argument list, a whole-argument group is the
  argument group (row P').
- Pass counts (cases / items): 29a6eb2 0/10, 88/104; 70237e8 0/10, 90/104; 634d548 9/10, 102/104 (the property `G - 1`
  and `G -1`); fix round 3 10/10, 104/104. Final 28,742 / 10,562.

**Call function receiver (fix round 1, review M4).** `call_expression.function` also takes the receiver group,
`#if X Foo #else Bar #endif (1)` (spec 3.4; alc: operand_groups/call-function.al), +57 STATE / +14 LARGE. The census
now routes `bnd:_receiver_group:operand:*` to host `call_expression` (its only visible caller; the member, subscript
and assignment sites are reached through expression names, where the census records the target itself).

**Typed rights (6.2), user decision 2026-10-21.** The aliased typed groups for all three of `in`/`is`/`as` cost +720
STATE / +285 LARGE over the general group, above the LARGE ceiling of the time. The user raised LARGE_STATE_COUNT to
10,723 (STATE stays 28,770) and asked for the cheapest typed variant: `is`/`as` take `_type_right` =
`choice(type_specification, alias(_type_operand_group, preproc_conditional_operand))` whose arms are
`type_specification`; `in`'s right stays `choice(list_literal, preproc_conditional_operand)` (the general group),
because the aliased list-literal group measured 28,951 STATE, over 28,770. The B3 operator-only form gained
`_typed_operator_arms` (`in`/`is`/`as` arms followed by a typed operand) after the general form gave a SILENT torn
tree for the type-test op-only witness.

**Item 51 (deferred-work).** Shape 1 (`in` in the B3 operator-only form) and shape 2 (a generic prefix whose arms end
in `in`, via `_dangling_operand`'s `repeat(_dangling_tail_item)`, operands `prec(10)` so a tail item does not swallow
the dangling operator) now parse. Shape 3 (a typed `in` prefix arm with a continuation before its keyword) stays a
`:error` witness (`b7b2_scope_gap_test.txt`): the static precedence of the `in` shift (5) beats the `and` reduce (4) and
no dynamic precedence reaches a shift/reduce decided statically; changing it was measured and reverted.

**SILENT carry.** `Foo(1 #if TPL + 2 #if X +2 #endif #if Y +3 #endif #endif, 2)` read the arm as a unary argument of
`preproc_conditional_arguments` plus two tails. `_nested_tail` is now `prec.dynamic(1)` like a root tail, so the root
tail with two nested tails (3) beats the argument group (2). The oracle never passed the old tree: it refused the
TPL=1 configurations as `lowering:list-separator` cannot-validate (an argument list that does not alternate), not a
discrepancy, so only the B7a assertion saw the defect (plan Task 11: a non-alternating list whose flat text parses as
one item should be a discrepancy). The witness is `tree` in `tools/b7_audit/tests/test_silent.py`; binary-operand /
first-only became `fixed` (tree right, oracle pending).

**Census (B7a).** `census.py` learnt three Phase C shapes, keeping every slot key: the receiver sets
(`_postfix_operand`, `_assign_target`) are expression names like `_continuation_operand`; a leadingPrefixed arm (a
symbol after `repeat1(prefix)`) is the prefix mechanism of its slot, not a slot (in `_region_root*`,
`_argument_expression`, `contSlot` inline and property_expression); `repeat(prefix)` before a binary right is the
optional operand-prefix mechanism. Keys that moved: `occ:_case_pattern_run:0.1.0.0` -> `1.0.0.0` and `0.2.0` -> `2.0`
(the rule's `prec.right` moved onto its repeat; two `key-aliases.tsv` rows, ten live equiv rows). New keys and routes,
all `equiv` (no new cells): `_operand_arm`, `_receiver_group`, `_nested_tail`, `_dangling_tail_item`,
`_dangling_b3_tail` operands, and new hosts `preproc_conditional_operand` (continuation operand, list literal) and
`preproc_conditional_list_elements` (tail operand). `census --check`: 2,955 pairs, 0 missing / 0 stale / 0 invalid.

**Fixtures.** No `tree-sitter test -u` in the final state: one `-u --file-name` run rewrote 114 untargeted files; the
user approved restoring them from HEAD and every pinned tree since was written by Edit from CLI `tree-sitter parse`
output. The moved B7a gap witnesses (`b7b2_<family>_test.txt`, compact trees) were checked with the CLI; eight gap
files emptied by the move stay as comment-only files because the committed matrix cites them (the Phase C gate
regenerates the matrix and the probes' `// Fixture` lines, then deletes them).

**Conflicts 240 -> 273** (+33, none removed): the receiver / postfix sets against `_continuation_operand`, the
statement-start sets (`call_statement`, `_expression_statement`) and the attribute argument, the leading-prefix arms
against the ternary / range / argument / region roots, the case-pattern supersets, `_additive_group_left` (removed with its rule in fix round 2; 272 after it),
`[_tail_item, _dangling_tail_item]`, `[preproc_conditional_expression_tail, _nested_tail]`, and the property_expression
sets of the placement fix.

**Metrics:** final 28,681 STATE / 10,523 LARGE / 1,326 SYMBOL, parser.c 68,541,580 bytes (65.4 MiB); vs Phase B
+2,059 STATE, +1,311 LARGE (ceilings 28,770 / 10,723, 80 MiB). After fix round 1: 28,752 / 10,535 / 1,330,
parser.c 68,617,736 bytes. After fix round 2: 28,688 / 10,523 / 1,325. After fix round 3: 28,742 / 10,562 / 1,325.

### Tasks 11-13: oracle, final audit, close-out (no grammar change after Task 10)

- **Task 11 (oracle).** Section 7's region assembler, as specified, with two hardenings from review: a
  non-alternating argument list or list literal whose flat text parses as one item is a discrepancy unless the second
  item opens an arm holding a separator (list spanning, 3.4, keeps its refusal), and an anonymous token that is not a
  binary's `operator` is never a region atom. Grouping inside a region is not checked (3.2, "not a grouping claim"):
  a hand-built `(a+g)*b` where flat is `a+(g*b)` passes; the ladder fixtures and the B7a assertions guard it
  (`docs/deferred-work.md` item 55).
- **Task 12 (final audit).** Manifests final (`--final B7b-2/ --require-oracle` 0 problems), full oracle tier 0
  discrepancies, matrix regenerated. 55 `first` class rows were widened to `(_ (preproc_operand_prefix ...) (_))` and
  7 list-literal rows re-rooted to `_`; the 231 B12 cells that now parse have no manifest (item 60). DC `tools.perf ab`
  0.957-0.964 against main, accepted by the user as report-only (item 54).
- **Task 13 (close-out).** Consumer documentation `docs/expression-regions.md`; deferred items 39 (shape 1) and 41
  closed, 44, 51 and 52 updated, 54-60 added; 116 cell rows in `tools/b7_audit/assertions.tsv` restore the
  pre-Task-12 pattern for exactly the class members it still fits (`assert --refresh`: 0 flips); a new alc probe
  `tools/alc_probe/cases/b7b-2/typed_rights/in-non-list-arm.al` (item 58). The rebuilt `tree-sitter-al.wasm` is
  byte-identical to the committed one (built at `d09ebe9` from the same `src/parser.c` and `src/scanner.c`).

### Final whole-branch review (2026-10-21): docs and records only, no grammar change

- **3.1, the prefix bullet, amended.** Section 3.1 names two prefix edges (from a binary node between `operator` and
  `right`, and from a region root to a leading prefix). The grammar puts `preproc_operand_prefix` in three more
  places, and the oracle already treats every edge into a group as a region edge (`region_edge` in
  `tools/config_oracle/lowering/regions.py`). The bullet reads, as amended: **every edge into a group is a region
  edge**: the unfielded edge from any node to a prefix or a tail, including from a `unary_expression` to each prefix
  between its `operator` and `operand` (`- #if X J + #endif 1`, X: `(-J) + 1`), and the edge into a
  `preproc_conditional_operand`. A group whose parent is a binary, `in`/`is`/`as`, unary or group node is in that
  node's region; a group whose parent is a root's host (a statement, `argument_list`, `list_literal`,
  `range_expression`, `ternary_expression`, `case_branch` or a split case host, `property_expression`) belongs to the
  region of the root expression beside it, the one after a prefix and the one before a tail. Case patterns and
  property values are region roots that take leading prefixes. `docs/expression-regions.md` carries the full rule.
- **3.3 and 8.6, "the query README".** None existed; `queries/README.md` was created with a section pointing at
  `docs/expression-regions.md`.
- **Records.** A unary-operator-only arm (`#if X - #endif 1`) ERRORs on main and on the branch, and alc accepts it:
  `docs/deferred-work.md` item 61, probe `tools/alc_probe/cases/b7b-2/prefixes/unary-operator-only.al`, witnesses
  `test/corpus/b7b2_unary_op_only_gap_test.txt`. List spanning across an `#else` (`Foo(1 #if X + 2 #else , 3
  #endif)`, a clean wrong tree identical on main) is a SILENT input in `tools/b7_audit/tests/test_silent.py`, and a
  tail before a postfix (an ERROR) is a `:error` witness in `b7b2_crossing_gap_test.txt`; both item 57.
