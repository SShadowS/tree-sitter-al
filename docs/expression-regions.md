# `#if` inside expressions: transparent regions (B7b-2)

AL lets an `#if` group stand anywhere inside an expression: after a complete operand, inside another group's arm,
in place of a whole operand, around the first operand with its operator, and in every expression slot of every
statement. alc accepts each of these in every configuration. A CFG parser cannot give one tree whose nesting is
right in every configuration when a group splits an operator chain:

```al
x := 2 *
#if X
    3 + 4      // X:      (2 * 3) + 4
#else
    5          // not X:  2 * 5
#endif
    ;
```

So this grammar gives such an expression one tree whose nesting is **not** a grouping claim, and states the rule a
consumer applies to recover the meaning of any configuration. This page is that rule for consumers of the tree
(the query files point here: `queries/README.md`).
Design and measurements: `docs/superpowers/specs/2026-10-20-b7b-2-expression-continuations-design.md` (sections 3,
5 and 6 and the execution amendments for Tasks 3, 4, 7 and 10).

## The three group nodes

| node | where it stands | arms hold | fields |
|---|---|---|---|
| `preproc_conditional_expression_tail` | after a complete operand, beside the region root's expression | `operator operand` continuations, nested tails; after `#endif`, more continuations | each continuation's operand is `operand` (multiple); a keyword operator is `operator: (in_keyword \| is_keyword \| as_keyword)` |
| `preproc_operand_prefix` | between a binary's `operator` and `right` (including a typed prefix before the typed right of `in`/`is`/`as`); between a unary's `operator` and `operand`; or before a region root's expression (a leading prefix), as an unfielded child of the root's host: a statement, `argument_list`, `list_literal`, `range_expression`, `ternary_expression`, `case_branch` (and the split case hosts) before a case pattern, `property_expression` before a property value | `operand operator` (the arm supplies an operand and the operator after it) | each arm's operand is `operand` (multiple); each arm's operator is `operator`: an anonymous token (`+`, `*`, `and`, ...), `comparison_operator`, or `in_keyword` / `is_keyword` / `as_keyword` (the last two in the typed prefix, whose operand is a `type_specification`) |
| `preproc_conditional_operand` | in place of one whole operand | one operand per arm, with optional prefixes before it and tails after it | each arm's operand is `operand` (multiple); the group takes the field of the position it fills (`right`, `left`, `operand`, `object`, `function`, ...) |

`preproc_if`, `preproc_elif`, `preproc_else` and `preproc_endif` are children of each group, as in every other
conditional node. `tools/check-field-types.py` pins every field these nodes widened.

The examples on this page write a group on one line (`x := 1 #if X + 2 #endif;`) for brevity; that text ERRORs as
written. In real code each directive (`#if`, `#elif`, `#else`, `#endif`) stands on its own line, as in the fixtures
and the worked examples below.

## Regions

An edge from a parent node to a child is a **region edge** when it is one of:
- `left` or `right` of `multiplicative_expression`, `additive_expression`, `comparison_expression`,
  `logical_expression`; `left` of `in_expression`, `is_expression`, `as_expression`;
- `operand` of `unary_expression`;
- **every edge into a group**: the unfielded edge from any node to a `preproc_operand_prefix` or
  `preproc_conditional_expression_tail` child, and every edge to a `preproc_conditional_operand` (which takes the
  field of the position it fills). In particular:
  - from a binary node to each prefix between its `operator` and `right`, including a typed prefix before the typed
    right of `in`/`is`/`as`;
  - from a `unary_expression` to each prefix between its `operator` and `operand`:
    `I := - #if X J + #endif 1;` (X: `-J + 1` = `(-J) + 1`) holds the prefix as an unfielded child of the unary,
    and the prefix is in the unary's region, never an atom of an inner one;
  - from a region root's host to a leading prefix before the root's expression, and to the tail after it (below);
- any child of the three group nodes above.

A binary or unary node's `operator` child (an anonymous token, `comparison_operator`, or an `in`/`is`/`as` keyword
node) is an operator of the region, never an atom; so is each `operator` of a group's arm.

**Which region a group belongs to.** A group is never an atom. Read its parent:
1. The parent is a binary, `in`/`is`/`as`, unary or group node: the group is in that node's region.
2. An operand group in a root slot (`I := #if X 1 #else 2 #endif;`, `right:` of the statement) is that region's
   root expression, like any operand there.
3. Otherwise a prefix or tail is an unfielded child of the host of one or more region roots (a statement,
   `argument_list`, `list_literal`, `parenthesized_expression`, `subscript_expression`, `range_expression`,
   `ternary_expression`, `case_branch` or a split case host, `property_expression`, a split host, an arguments or
   list-elements group's arm), beside a root's expression: a **prefix** (and a run of consecutive prefixes) belongs
   to the region of the root expression that **follows** it; a **tail** belongs to the region of the root
   expression that **precedes** it. In `range_expression` and `ternary_expression` that is the `left`/`right`, or
   `condition`/`then_value`/`else_value`, beside the group; in `case_branch` a leading prefix belongs to the case
   pattern after it; in `property_expression` to the property value after it.
4. A group behind a boundary is in the inner region (as for any node).

The oracle implements exactly this: `region_edge` in `tools/config_oracle/lowering/regions.py` returns true for any
edge into or out of a group, and the region assembler collects a root's leading prefixes and trailing tail from the
host's children beside the root.

Every other edge is a **boundary**: a call's `function` and `arguments`, a member's `object`, a subscript's `object`
and indices, a parenthesized expression's inner, a list element, each ternary part, each range end, and the `right`
of `in`/`is`/`as` (a list literal, a range set or a `type_specification` enters the region as one atom; its own
interior is its own region or none).

A **region** is the node reached by a boundary edge (its **root**), together with everything reachable from it by
region edges only. Nodes reached through a boundary are the region's atoms: calls, member accesses, subscripts,
parenthesized expressions, ternaries, list literals, literals, names. A region **contains a group** when a tail,
prefix or operand group is reachable from its root by region edges only. A group behind a boundary belongs to the
inner region: in `x := a * b + Foo(1 #if X + 2 #endif);` the outer region has no group.

The region roots that carry a tail (the `contSlot` slots in `grammar.js`, hidden `_region_root_*` rules): the
assignment right, `if`/`while`/`repeat ... until` conditions, `case` expressions, `for` start and end, `exit`
value, call arguments, subscript indices, list elements (including each element of a
`preproc_conditional_list_elements` arm), ternary condition, then and else, parenthesized inner,
range left and right, `with` record, `foreach` iterable, the split-if heads and the split-call arguments. Two more
roots take leading prefixes through their own rules: each **case pattern** (`case_branch.pattern` and the patterns
of the split case hosts; the prefix is an unfielded child of the host before the pattern, and a tail on a pattern
is item 56), and each **property value** (the expression child of `property_expression`; the prefix and the tail
are unfielded children of `property_expression`, on B12's route `_property_value_with_split`, which takes the same
tail rule).

## Meaning

**In a region that contains a group, the nesting of the region's binary and unary nodes is not a grouping claim.**
Its meaning in one configuration is:

1. **Splice.** Replace each group by its active arm's content, or by nothing when no arm is active; recurse into
   nested groups.
2. **Flatten** the result to a run of atoms, unary operators and binary operators.
3. **Group the run by the ladder** below.
4. **Validate after composing.** A missing operand or a dangling operator in the composed run is an invalid
   configuration. A group that contributed nothing is not by itself an error: `x := 1 #if X + 2 #endif;` and
   `x := a + #if X b + #endif c;` are valid at X=0.

**The ladder** (one numeric convention: larger binds tighter, as in `tools/config_oracle/lowering/expression.py`;
measured with alc, `docs/al-operator-precedence.md`):

| level | operators | associativity |
|---|---|---|
| 7 | unary `not` `-` `+` | right (prefix) |
| 6 | `*` `/` `div` `mod` | left |
| 5 | `+` `-` | left |
| 4 | `in` `is` `as` | left |
| 3 | `and` | left |
| 2 | `or` `xor` | left |
| 1 | comparisons `=` `<>` `<` `<=` `>` `>=` | left |

A region without a group keeps the ordinary trees and their ordinary grouping claim. Grouping never crosses a
boundary.

## How the tree is built (what was built, not what was first planned)

- **Placement A.** `preproc_conditional_operand` is one alternative of `_continuation_operand` (the operand rule
  of every binary, unary and `in`/`is`/`as` left, every tail and prefix operand), so one rule covers every operand
  position. A separate operand slot per position (placement B) was measured and not taken.
- **No positional dynamic bonuses.** An operand group is an ordinary operand: the binaries' static precedence nests
  it like any other operand, in every position. The tree's nesting around a group is therefore the ladder's
  grouping of the tree as written, which the contract above does not rely on. An earlier version that scored the
  group by position inverted the ladder somewhere every time and was deleted (spec amendments, Task 10 fix rounds 1
  and 2).
- **Left associativity holds around a group.** `2 + g + 1` is `(2 + g) + 1`:
  `right: (additive_expression left: (additive_expression left: (integer) right: (preproc_conditional_operand ...)) right: (integer))`
  (`test/corpus/b7b2_operand_group_test.txt`, "unary-paren arm").
- **The comma-less competitors lose through a penalty on the sign, not a bonus on the group.** `Foo(#if X 1 #else 2
  #endif + 3)` could also be an argument group followed by a comma-less, signed argument `+3`. `unary_expression`
  carries a global `prec.dynamic(-2)`, so the operand reading (group -1) beats the argument reading (argument group
  0 + unary -2). The scanner lexes `-1` before `;`, `,`, `#` or EOF as one `NEGATIVE_INTEGER`, which is no unary, so
  the same `prec.dynamic(-2)` sits on both signed `option_member` alternatives (`Visible = G - 1;` is an
  `additive_expression`, not an option-member list). **Risk:** dynamic precedence only acts where GLR forks, and any
  fork whose two readings differ only by a sign now picks the reading without it. Unforked parses ignore it (the
  production delta is 0); `MinValue = - 1;` without a group is a tie that GLR order decides, pinned in
  `test/corpus/negative_literal_property_value_test.txt`.
- **Typed rights.** `is`/`as` take `_type_right`: a `type_specification`, or an operand group (aliased to
  `preproc_conditional_operand`) whose arms are `type_specification`. `in`'s right is `list_literal` or the GENERAL
  operand group, a cost decision (the typed list variant measured over the state ceiling), so `in` over-accepts a
  non-list arm: `b := i in #if X [1, 2] #else 3 #endif;` parses, alc rejects X=0 (`docs/deferred-work.md` item 58).
- **The receiver group.** In a receiver position (`member_expression.object`, `subscript_expression.object`,
  `call_expression.function`, an assignment target) the group's arms are postfix-safe atoms only (a name, literal,
  call, member access, subscript, parenthesized expression), so the postfix applies to the whole arm:
  `#if X Foo #else Bar #endif (1);` gives
  `(call_expression function: (preproc_conditional_operand ... operand: (identifier) ... operand: (identifier) ...) arguments: (argument_list (integer)))`
  (`b7b2_operand_group_test.txt`, "call function: a receiver group as the callee").
  An arm with a binary or unary top before a postfix is a crossing form and ERRORs (below).
- **Consecutive groups have two shapes, both pinned in `test/corpus/b7b2_tail_test.txt`.** At a root (and after
  the B3 operator-only form) the second group is the LAST CHILD of the first, so N consecutive groups nest N deep
  ("consecutive groups at a root nest"). Inside an arm (a tail arm or a prefix arm) groups are SIBLINGS, because a
  nested tail has no trailing items ("consecutive groups inside an arm are siblings"). Under the contract both splice
  to the same flat run; the difference is the cost of the root shape, quadratic in N (`docs/deferred-work.md`
  item 52), accepted because real code has at most 3 back-to-back groups.

## Worked examples

Each tree is the `right:` (or host) subtree of the named fixture's expected tree, as `tree-sitter parse` prints it.
Directive nodes are shown as in the fixture.

### A tail

`test/corpus/b7b2_region_roots_test.txt`, "a tail before in continues the root (spec 4.3 witness)":

```al
b := i
#if X
    + 1
#endif
    in [1, 2] and Ok;
```

```
(assignment_statement left: (identifier) operator: (assignment_operator)
  right: (identifier)
  (preproc_conditional_expression_tail
    (preproc_if (preproc_open) condition: (identifier))
    operand: (integer)
    (preproc_endif (preproc_close))
    operator: (in_keyword)
    operand: (list_literal (integer) (integer))
    operand: (identifier)))
```

`in_expression.left` is not a tail site, so the group belongs to the assignment root and `in [1, 2]` and `and Ok`
are the tail's trailing items. Regrouped: X gives `i + 1 in [1, 2] and Ok` = `((i + 1) in [1, 2]) and Ok`; not X
gives `(i in [1, 2]) and Ok`.

### A prefix

`test/corpus/b7b2_operand_group_test.txt`, "first: a leading operand prefix at the root":

```al
I :=
#if X
    2 +
#endif
    2 + 1;
```

```
(assignment_statement left: (identifier) operator: (assignment_operator)
  (preproc_operand_prefix
    (preproc_if (preproc_open) condition: (identifier))
    operand: (integer)
    (preproc_endif (preproc_close)))
  right: (additive_expression left: (integer) right: (integer)))
```

The tree nests `2 + 1` under `right`, but that is not a claim: X gives `2 + 2 + 1` = `(2 + 2) + 1`; not X gives
`2 + 1`. The same prefix between a binary's operator and right ("consecutive prefixes after a binary operator",
`I := I + #if X J + #endif #if Y 3 * #endif 4;`) is an unfielded child of the `additive_expression`: X and Y give
`I + J + 3 * 4` = `(I + J) + (3 * 4)`.

### An operand group

`test/corpus/b7b2_operand_group_test.txt`, "spec 4.3 witness 2 * group":

```al
I := 2 *
#if X
    3 + 4
#else
    5
#endif
    ;
```

```
right: (multiplicative_expression left: (integer)
  right: (preproc_conditional_operand
    (preproc_if (preproc_open) condition: (identifier))
    operand: (additive_expression left: (integer) right: (integer))
    (preproc_else)
    operand: (integer)
    (preproc_endif (preproc_close))))
```

X gives `2 * 3 + 4` = `(2 * 3) + 4` (the arm's `additive_expression` is not grouped as `2 * (3 + 4)`); not X gives
`2 * 5`.

## What guards the grouping

The oracle (`tools/config_oracle`, region assembler `lowering/regions.py`) implements exactly the contract: it
splices, flattens and regroups, so it checks every atom, operator and arm, but by design it does **not** check the
nesting inside a region (`docs/deferred-work.md` item 55). The tree's own nesting is guarded by:
- `test/corpus/b7b2_ladder_matrix_test.txt`: 21 cases / 66 statements, every ladder level against itself and its
  neighbours, the group first, middle and last, four-operand chains, unary `-` and `not` before the group, the group
  in a ternary condition;
- `test/corpus/b7b2_ladder_positions_test.txt`: 10 cases / 104 items carrying the ladder into every expression
  position (call argument first and later, list item, case pattern, `exit`, ternary then and else, `if`, `until`,
  property value), with `/ div mod + xor is as`, operator-bearing arms and the signed forms `G - 1` / `G -1`;
- the tie-break fixtures of `test/corpus/b7b2_tie_break_test.txt`, each with a recorded losing-tree mutation;
- the B7a structural assertions (`tools/b7_audit/assertions.tsv`).

Both ladder files' expected trees were composed by an operator-precedence generator from the ladder, never copied
from parser output.

## Not covered (each a numbered item in `docs/deferred-work.md`)

- **Crossing forms** (item 57): a group followed by a postfix whose arm is not a postfix-safe atom
  (`#if X a + b #else c #endif .Trim()`), a `?`/`:` inside any arm, and one group that both continues an expression and
  supplies list items (`Foo(1 #if X + 2, 3 #endif)`). They ERROR (the argument-list form reads as a pinned, known
  wrong comma-less argument).
- **Case-pattern slot continuations** (item 56): `case i of 1 #if X + 1 #endif : ...`.
- **Over-acceptances**: an operand group with no `#else` arm in a required operand position, and `op-only`
  (`E #if X op #endif F`), both item 44; `in`'s non-list arm, item 58.
- **List spanning across an `#else`** (item 57): `Foo(1 #if X + 2 #else , 3 #endif)` parses clean but reads `+2` as
  a comma-less second argument (X=1 is `Foo(1 + 2)`), as on main; pinned as a SILENT witness, never as a corpus tree.
  **A tail before a postfix** (`T1 #if X + T2 #endif .ToUpper()`) ERRORs (item 57).
- **Unary-operator-only arms** (item 61): `I := #if X - #endif 1;`, `B := Ok and #if X not #endif Ok;` and
  `if #if X not #endif Ok then;` ERROR, on main too; alc accepts every configuration.
- **No region API** in the traversal helper (item 59): a consumer applies this page itself; the oracle's region
  assembler is the reference implementation. Query authors: `queries/README.md`.
