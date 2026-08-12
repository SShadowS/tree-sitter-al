# tree-sitter-al — grammar improvements requested by the owned-IR consumer

**Requested by:** the `al-call-hierarchy` owned-AL-syntax-IR migration (a consumer that
lowers the CST into an owned IR; it generates a typed node layer from `node-types.json`).
**Grammar baseline:** `eeb2839` (v3.0.1) — the rev the consumer currently pins.
**Status:** proposal. None are blocking (the consumer has workarounds); they materially
improve `node-types.json` quality and fix one correctness footgun.

> **Validation contract (how to prove a fix is behavior-preserving):** after each change,
> `tree-sitter generate`, then in `al-call-hierarchy` bump the submodule pin and run
> `cargo run -p xtask -- gen-syntax` (regenerates the raw vocab + hash) and
> `cargo test --test ir_dual_run` (the dual-run parity harness: legacy-vs-IR feature
> streams over the real `.al` corpus) plus the differential goldens. **Parity preserved =
> safe.** The dual-run harness is the source of truth for "did engine-visible behavior
> change?".

---

## Issue 1 — `left`/`operator`/`right` field bleed onto ~every node (HIGH)

### Symptom
In `node-types.json`, the vast majority of named nodes — `if_statement`, `while_statement`,
`for_statement`, `with_statement`, `case_statement`, `assignment_statement`,
`statement_block`, `argument_list`, `parenthesized_expression`, `case_else_branch`, … —
carry three spurious fields:

```
left     -> <~30-member _expression union>   (multiple)
operator -> in_keyword                         (multiple)
right    -> list_literal, type_specification   (multiple)
```

They are noise on those nodes (an `if_statement` already has the real
`condition`/`then_branch`/`else_branch` fields). A consumer that generates typed field
accessors must special-case every node to know which fields are real, and each bled field
becomes a useless accessor.

### Root cause (grammar.js, `_expression` choice ~line 3507)
The `in` / `is` / `as` expression variants are written as **inline anonymous `seq()`s** with
field labels, directly inside the `_expression` choice:

```js
_expression: $ => choice(
  // ...
  prec.left(5, seq(field('left', $._expression), field('operator', $.in_keyword),  field('right', $.list_literal))),
  prec.left(5, seq(field('left', $._expression), field('operator', kw('is', 5)),   field('right', $.type_specification))),
  prec.left(5, seq(field('left', $._expression), field('operator', kw('as', 5)),   field('right', $.type_specification))),
  // ...
),
```

Because these `seq()`s have **no node name**, their `field()` labels are not contained on a
named node — tree-sitter attaches them to whichever *named* node ultimately produces the
`_expression`. That is every statement/expression node, hence the bleed. (The named binary
rules like `additive_expression` do NOT bleed, confirming naming is the fix.)

### Fix
Promote the three inline variants to **named rules** and reference them in the choice:

```js
in_expression: $ => prec.left(5, seq(field('left', $._expression), field('operator', $.in_keyword),  field('right', $.list_literal))),
is_expression: $ => prec.left(5, seq(field('left', $._expression), field('operator', kw('is', 5)),   field('right', $.type_specification))),
as_expression: $ => prec.left(5, seq(field('left', $._expression), field('operator', kw('as', 5)),   field('right', $.type_specification))),

_expression: $ => choice(/* ... */ $.in_expression, $.is_expression, $.as_expression /* ... */),
```

Now the fields live on `in_expression`/`is_expression`/`as_expression` and disappear from
every unrelated node. **Note:** this ADDS three node kinds (consumers must classify them) and
changes how `x in [..]` / `x is T` / `x as T` parse (now a named node, not a bare field on the
parent). The consumer welcomes this — it is strictly cleaner. Validate via the dual-run
harness: the consumer currently lowers these via the parent's `left`/`right`; after the fix it
lowers the named nodes. Parity must hold on the corpus.

---

## Issue 2 — `case_else_branch` is inconsistent with `case_branch` (correctness footgun)

### Symptom
The else branch of a `case` is structurally asymmetric to the normal branches, which silently
dropped else-branch statements in a naive consumer until special-cased.

### Root cause (grammar.js ~3261, ~3286, ~3399)
```js
case_statement: $ => prec(2, seq(
  $.case_keyword, field('expression', $._expression), $.of_keyword,
  optional(field('body', $.case_body)),     // <- branches live here
  optional($.case_else_branch),             // <- else is a SIBLING, not under case_body
  choice($.end_keyword, kw('end')),
)),
case_branch: $ => choice(seq(field('pattern', $._case_pattern), ':',
  field('body', choice($.code_block, alias($._if_statement_no_else, $.if_statement), $._statement))), ...),
case_else_branch: $ => prec.left(seq($.else_keyword,
  choice($.code_block, repeat($._statement)),   // <- NO `body` field; statements are direct children
)),
```

So: (a) `case_else_branch` is a direct child of `case_statement`, NOT under `case_body`; and
(b) `case_branch` has a `body` field but `case_else_branch` does not. A consumer that iterates
`case_body` for branches and reads each branch's `body` field misses the else entirely.

### Fix (pick one; first preferred)
1. **Field-wrap the else body** so it mirrors `case_branch`:
   ```js
   case_else_branch: $ => prec.left(seq($.else_keyword,
     field('body', choice($.code_block, repeat($._statement))),
   )),
   ```
   (If `field()` over `repeat()` is awkward, wrap multi-statement else bodies in an implicit
   block node, or constrain to `code_block | _statement` like branches.)
2. Additionally/alternatively, **move `case_else_branch` under `case_body`** so all branches
   are found in one place.

Either makes consumers symmetric. Validate via dual-run (the consumer already special-cases
this; after the fix the special-case can be removed and parity must hold).

---

## Issue 3 — `statement_block` carries `left`/`operator`/`right` fields

Same root cause as Issue 1 (a `statement_block` can directly hold an `_expression` in
expression-statement position, so the bled fields land on it). Fixing Issue 1 should remove
these. Verify `statement_block` has no `left`/`operator`/`right` after the Issue 1 fix.

---

## Issue 4 — `trigger_declaration.name` is `multiple:true` and includes a bare `::` token (LOW)

`trigger_declaration.name` has type set `::, identifier, quoted_identifier` with
`multiple: true` — member triggers (e.g. a field's `OnValidate`) span multiple tokens via a
raw `::`. An anonymous `::` inside a `name` field's types is awkward for consumers. Consider a
structured member-trigger-name node (e.g. `member_trigger_name` holding the member + trigger
identifiers) so `name` is a single, well-typed child. Low priority; the consumer reads the
field's text today.

---

## Timing / sequencing recommendation

- These can be developed **in a separate session in this repo at any time** — the consumer
  pins `eeb2839`, so grammar changes here do NOT disturb the in-flight IR migration until the
  consumer deliberately bumps the pin.
- The consumer should **adopt** the new grammar only once its IR lowerer is at broad dual-run
  parity (end of its Phase 1), so the bump is validated by a comprehensive parity net rather
  than a partial one.
- Suggested order to implement here: **Issue 2** (small, fixes a real footgun), then **Issue 1**
  (bigger, removes the pervasive bleed and subsumes Issue 3), then **Issue 4** (optional).
- After each: `tree-sitter generate` + run the grammar's own corpus tests; the consumer then
  validates engine-behavior preservation via its dual-run harness on bump.
