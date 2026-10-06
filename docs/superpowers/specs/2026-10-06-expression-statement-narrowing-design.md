# B6: narrowing `_expression_statement` (design)

Roadmap row B6 (decision 4), deferred-work item 4. Status: design, awaiting review.

## 1. Problem

`_expression_statement: $ => $._expression`, listed in `inline`, lets any expression stand as a
statement. alc accepts only assignments and invocations as statements, so the grammar parses
invalid code as clean trees, and, worse, it lets a fragment of a valid `#if` continuation
detach from its host and float as its own statement, with no ERROR node:

```
Foo(1)                      main today:  call_expression 'Foo(1)'
#if X                                    preproc_conditional_statement
+ 2                                        unary_expression '+ 2'     <- detached
#endif                                   has_error False
;
```

The same holds for `1 + 2;`, `'abc';`, `exit(1)` followed by `#if X + 2 #endif ;`. A second
route survives any narrowing to invocations: a keyword-operator fragment reads as a call to a
function named after the operator.

```
repeat Foo(); until A       main and the narrowed rule alike:
#if X                         repeat_statement ends at A
and (B)                       preproc_conditional_statement
#endif                          call_expression function: identifier 'and'
;                             has_error False
```

Both configurations of that input are valid AL (`until A;` and `until A and (B);`). The tree is
wrong and silent. The grammar's own comment documents the identical mechanism for `or`
(`_expression_continuation`'s comment block).

The goal is a fail-loud backstop: these shapes become ERRORs, in every position, including
positions nobody has enumerated. It attaches nothing: hosts without a continuation facility
(`repeat ... until`, `foreach ... in`, `with`) still need B7 to parse their valid split forms.

## 2. Evidence

### 2.1 What production uses as an expression statement

Census with the rule made visible and not inlined (no other change; STATE_COUNT unchanged), over
BC.History, DC, BC28.1 and BCApps-29.0: 70,355 files, 4,871,288 expression statements.

| child | in files with no ERROR | in files with an ERROR |
|---|---|---|
| `call_expression` | 4,862,738 | 828 |
| `member_expression` | 7,541 | 0 |
| `identifier` | 29 | 97 |
| `subscript_expression` | 0 | 37 |
| `keyword_identifier` | 0 | 18 |

The 29 clean `identifier` sites are parenless calls without a `;`, before `ELSE` or `end`
(`IF C THEN AddLineAmountToTotals ELSE ...`). The ERROR-file shapes are all in
`BCApps-29.0/.../APAC/Tests/SINGLESERVER/ERMPurchaseReportsIII.Codeunit.al`, a pre-existing gap.

Corpus fixtures hold three non-invocation statements: `(a + b);` as filler in
`exit_statement_spacing_test.txt`, the leftover `'; // trailing '` in
`verbatim_string_unterminated_test.txt` (whose header says it is "legal under
_expression_statement"; alc rejects the file), and an integer inside a deliberate negative.

### 2.2 alc (18.0.41), split and flat identical

| input | verdict |
|---|---|
| `Foo();` / bare `Bar` before `end` / bare `Bar` before `else` / `"My Proc";` / `Rec.Reset;` / `Rec.Get();` | ACCEPT |
| `1;` `'abc';` `1 + 2;` `+ 3;` `-Foo();` `not Foo();` | AL0104 (syntax) |
| `Rec.Get() = true;` `(Foo());` `Arr[1];` `X;` (X a variable) `Rec.Name;` (a field) | AL0117 "Illegal statement. Only assignment and method invocation can be used as a statement." |
| statement starting with bare `and`/`or`/`xor`/`div`/`mod`/`in`/`not`, as a call or an assignment target | AL0104 |
| bare `and` read in an expression (`B := and;`, `B := and(B);`) | AL0224 "Expression expected" |
| `procedure and(...)`, `procedure mod(...)`, a variable `and: Boolean;` | ACCEPT (declaring is fine) |
| `"and"(B);`, `B := "and"(B);` | ACCEPT (quoted reference) |
| `is(B);`, `as(B);` | ACCEPT |

So alc's parser accepts identifier- and paren-led expressions syntactically and rejects the
non-invocations in a later pass (AL0117); and in code, the seven operator words are never a bare
identifier, though they may be declared and then referenced quoted.

### 2.3 Operator words in production

Every unquoted `identifier` spelled `and`/`or`/`xor`/`div`/`mod`/`not`/`in`/`is`/`as` across the
four corpora: 120. The seven reserved words occur only in declaration positions
(`enum_value_declaration`, `option_member`, `field_declaration`, `action_group_section`); every
code-position site is `is` or `as`, which stay identifiers.

### 2.4 Why both earlier attempts collapsed

They narrowed the rule while it stayed in `inline`, so its precedence and its conflicts were
macro-substituted into each host separately (the rule's comment named this lead).
Measured today: de-inlined and narrowed, BC.History, DC and BC28.1 are byte-identical, BCApps
differs in one file (the ERROR file above), and 2,179 of 2,182 fixtures pass, the 3 failures
being exactly the three fixtures in 2.1.

## 3. Decisions

1. **The invocation line (user, 2026-10-06).** A statement expression is a call, a member
   access, a bare identifier or a bare quoted identifier, and nothing else. That rejects AL0104
   and every AL0117 shape decidable without symbols (comparison, unary, parenthesized, subscript,
   binary, literal). `X;` and `Rec.Name;` stay accepted: only symbols tell a variable from a
   procedure or a field from a method. This is a symbol-free structural restriction, not a copy of
   alc's two passes.
2. **Keyword-operator tears are fixed in B6 (user, 2026-10-06)**, by a contextual reserved-word
   set (3.2), not documented and deferred.
3. **Tree shape.** No new node type. Valid AL keeps its tree: the four corpora are byte-identical
   (2.4) and the fixtures in 5 pin the shapes no corpus holds. Invalid input that used to parse
   clean now carries an ERROR. Not a breaking change for consumers of valid code.

## 4. Design

### 4.1 `_expression_statement`

```javascript
// inline: [$._field_source],            // _expression_statement removed
_expression_statement: $ => prec(-1, choice(
  $.call_expression,
  $.member_expression,
  $.identifier,
  $.quoted_identifier,
  alias($._value_start_keyword_name, $.identifier),   // `Order;` / `Table` (procedures)
)),
```

- It stays hidden, so trees do not gain a node.
- The `_value_start_keyword_name` arm is required: `table`/`order` are live keyword tokens at
  statement start (`_value_start_keyword_name`'s comment), and without it a parenless call to a
  procedure named `Order` or `Table` ERRORs, measured on the research build
  (`Order;`, `if C then Order else Table;`). `_expression` and seven other sites carry it.
- `prec(-1)`: without it generation fails with a reduce/reduce at `begin identifier • '-'`
  (`_expression` vs the statement). Static precedence prunes the statement reduction before GLR
  sees it, so it is safe only where no valid statement can be followed by that lookahead. The
  implementation audits every state where it decides (5.3) and pins the boundaries.
- Its two hosts are unchanged: `_statement_inner` and `_preproc_guard_block` (whose
  `prec(2, ...)` acts on its own boundary and is not a safety override). The old comment's "four
  consumers" is stale; `grep -n '_expression_statement' grammar.js` lists these two.

### 4.2 Conflicts

- Add `[$.assignment_statement]`. Narrowing exposes the decision at `x := e • #if`: shift into
  `preproc_conditional_expression_tail`, or finish the assignment and start a
  `preproc_conditional_statement`. Only the arm content decides, so it must stay a GLR fork;
  static precedence would commit before the discriminator (the history in
  `_expression_continuation`'s comment). A singleton is scoped to exactly this parent set.
- Delete the two conflicts tree-sitter then reports unnecessary:
  `[$._single_pattern, $._expression]` and `[$.assignment_statement, $.assignment_expression]`.

### 4.3 Reserved words in code

A new contextual set, `code_names: [and, or, xor, div, mod, in, not]`, applied with
`reserved('code_names', ...)` where code reads a bare identifier, so that an operator word cannot
lex as an identifier in a statement or an expression:

- It must sit on a rule that names `$.identifier` directly, and its entries must be rule
  symbols, not fresh `kw()` tokens (the two rules measured for issue #20, CLAUDE.md "Reserved-word
  sets"). The implementation finds the narrowest such site that covers the statement start, the
  call callee and the expression primary, and records the site in the grammar comment.
- Declaration sites (procedure, variable, parameter, field, enum value, option member, action
  group, label names) must stay unreserved; fixtures pin each one with a production spelling from
  2.3.
- `is` and `as` are not in the set: alc accepts them as bare names in code.
- `in` and `not` are already operators; reserving them as names changes no valid tree (2.3).
- If a site that covers expressions costs more than the state budget (6), the fallback is the
  statement start only (the call callee and the assignment target), which still closes every
  tear that begins a statement, and the expression residual becomes a deferred item.

### 4.4 Comments

The `_expression_statement` KNOWN comment is replaced by the line (3.1), the two codes, the
cause of the two old collapses, and what B6 does not cover (hosts without continuation, B7).

## 5. Tests and evidence

### 5.1 alc probes

`tools/alc_probe/cases/expression-statement/`: the 17 cases of 2.2 with their real codes (the
first drafts predicted AL0104 for the AL0117 shapes; the `// expect:` lines take the measured
codes), plus the operator-word cases of 2.2. `--check` clean.

### 5.2 Fixtures

Positive (`test/corpus/expression_statement_test.txt`), fields pinned and proved by a `bogus:`
rename:
- every accepted shape: call, member call, parenless member, bare identifier and bare quoted
  identifier before `end` and before `else` without `;`, `Order;`, `Table`, `if C then Order else
  Table;`, `this.Foo()`, `Codeunit.Run(...)`, `Arr[1].Reset;`, `"and"(B);`;
- the same inside `#if` arms, `#elif`, nested, and in a guard preamble;
- the operator words declared: `procedure and`, a variable `and`, `value(0; and)`, an option member
  `and`, a field `div`;
- an `exit; Foo();` control.

GLR adversarial (positive, the trees written by hand from the flat reading, not taken from `-u`):
- `B := A #if X + 2 #else - 3 #endif * 4;`, one assignment, tail attached;
- operator-only arms, `B := 1 #if X + #else - #endif 2;`;
- keyword-operator tails, `B := A #if X and (C) #else or (D) #endif;`, no detached call;
- `;` inside each arm followed by calls: the calls are statements, not right-hand side;
- `#elif`, nesting, a comment at each boundary, case bodies and nested if/else around them.

Negative (`test/corpus/expression_statement_negative_test.txt`, listed in
`tools/deliberate-negatives.txt`): each rejected shape of 2.2; `Foo(1)` and `exit(1)` followed by
`#if X + 2 #endif ;`; the keyword-operator tears `until A #if X and (B) #endif ;` and
`Foo(1) #if X or (2 = 2) #endif ;` for `and`, `or`, `xor`, `div`, `mod`, with a parenthesized and
an identifier operand.

Existing fixtures:
- `exit_statement_spacing_test.txt`: the valid `exit (42)` case stays; the `exit; (a + b);` case
  moves to the negative file, still pinning `exit_statement` as valueless.
- `verbatim_string_unterminated_test.txt` becomes a deliberate negative (alc AL0104). Its lexical
  assertion stays: the verbatim string still ends at the closing quote of `'a'`; recovery must not
  shorten it.
- `range_not_an_expression_negative_test.txt` takes its new recovery tree, every hunk explained.

### 5.3 Gates

- Fresh tree-harness baselines (`.snapshots/baseline-b6-*`, taken before any edit) and
  zero-delta on all four corpora. In BCApps, every changed hunk of `ERMPurchaseReportsIII` is
  read and shown to lie inside the recovery region; an unrelated valid procedure tree changing
  fails the gate.
- `has_error` sweeps over the four corpora and the corpus fixtures.
- The `prec(-1)` audit: list each parse state where the precedence removes a statement reduction,
  with its lookaheads, from `tree-sitter generate --report-states-for-rule` or the parse table,
  and show that no valid statement is followed by those lookaheads.
- `validate-grammar.sh --full`; `python -m tools.query_coverage.qc run`.
- Config oracle quick tier and `replay`. The split families it refuses
  (`preproc_guarded_statement`, split calls, split-if) count as unchecked there; the hand-written
  fixtures of 5.2 are their witness.
- Incremental: an edit sequence compared fresh against incremental after every step:
  `Foo();` to `1 + Foo();` and back, adding and removing parentheses and `;`, `Order()` to `Order`,
  inserting and deleting a whole `#if` group, an arithmetic-tail arm to a complete-statement arm.
- Performance: `tools.perf ab` over DC, at least 24 rounds, three independent runs, budget 1% on
  the ratio, plus a synthetic directive-heavy assignment file for tail latency.
- `src/parser.c`, `src/grammar.json`, `src/node-types.json` committed together; WASM rebuilt in its
  own commit, the final gates run on the combined state.

## 6. Budgets

STATE_COUNT: the research build is 23,211 (+25). The reserved set adds lex states, not parse
states, in principle; the budget for the whole of B6 is +1% (23,418). Over budget, take the
4.3 fallback before anything else.

## 7. Out of scope

- Hosts without a continuation facility (`repeat ... until`, `foreach ... in`, `with`): their
  valid split forms stay ERRORs, now loud; B7.
- `(Foo)();`, `(Foo())();`, `Foo()();`: never accepted by the grammar; probe alc and record a
  deferred item if alc accepts any.
- Type checks on the receiver or callee: semantic.

## 8. Documentation

CHANGELOG `### Fixed` entry (valid trees unchanged in four corpora; invalid statements and
detached fragments now ERROR; reserved words in code); deferred-work item 4 RESOLVED; roadmap B6
DONE; CLAUDE.md "Reserved-word sets" gains the third set.
