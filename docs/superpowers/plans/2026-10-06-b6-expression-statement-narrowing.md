# B6: Narrowing `_expression_statement` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A statement expression is an invocation (call, member, bare name) and nothing else, and the
seven operator words are never a bare identifier in code, so invalid statements and detached `#if`
fragments become ERRORs while every valid tree stays byte-identical.

**Architecture:** `_expression_statement` leaves the `inline` array and is narrowed to
`prec(-1, choice(call_expression, member_expression, identifier, quoted_identifier,
alias(_value_start_keyword_name, identifier)))`; one singleton conflict `[assignment_statement]` keeps
the `x := e • #if` decision a GLR fork. A third contextual reserved-word set, `code_names`, reserves
`and or xor div mod in not` where code reads a bare identifier.

**Tech Stack:** tree-sitter 0.27 grammar DSL (`grammar.js`), py-tree-sitter pytest
(`tools/config_oracle/tests/`), corpus fixtures (`test/corpus/`), alc 18.0.41 via `tools/alc_probe`.

**Spec:** `docs/superpowers/specs/2026-10-06-expression-statement-narrowing-design.md`. Read it first;
section numbers below (§N) refer to it.

## Global Constraints

- The goal is the CORRECT tree, not merely no ERROR (CLAUDE.md). Valid AL keeps its tree.
- Never edit `src/parser.c`; run `./tools/ts-lock.sh tree-sitter generate`, and commit `src/parser.c`,
  `src/grammar.json`, `src/node-types.json` together.
- Every commit message ends with a MEASURED `[BC.History: N errors, X% success]` line.
- Budgets are guidelines, not caps (user, 2026-10-06): STATE_COUNT guideline +1% (≤ 23,418 from
  23,186); perf guideline 1% on the `tools.perf ab` ratio. An overrun is measured, attributed to the
  edit that caused it, and put to the user with the §4.3 fallback; it never auto-reverts work.
- Use Git Bash with Windows paths; never `2>nul`; never `find /`; never `tail -f | grep` watches.
- Wrap every tool that builds or loads `al.dll` in `./tools/ts-lock.sh`.
- `tree-sitter test -u` traps (CLAUDE.md): read every hunk; run `git diff --stat test/corpus` after
  every `-u` and restore files you did not target; check the suite total moves by exactly the cases added.
- Do not mix `$.x_keyword` and bare `kw()` in one `choice()`; reserved-set entries must be rule
  symbols, not fresh `kw()` (CLAUDE.md "Reserved-word sets").
- Baselines: `.snapshots/baseline-b6-{bc,dc,bc28,bcapps}` were taken from main at 803876a^ grammar
  (identical to main's), before any edit. If `git log main -1 -- grammar.js src/` shows a grammar
  change after `48d04e2`, retake them before Task 2.
- The research build (narrowed, hidden, non-inlined, measured zero-delta) is in the stash
  `b6-research: hidden non-inlined narrowed _expression_statement ...`; use it as a reference, do not
  pop it onto this branch.

## Review Focus

1. **A valid split assignment chooses the wrong fork.** `B := A #if X and (C) #else or (D) #endif;`
   must stay ONE `assignment_statement` with the tail attached, never a call named `and`/`or`
   (Task 4 adversarial fixture, Task 5 reserved set).
2. **A procedure or variable named with a keyword is called bare.** `Order;`, `Table`, `Continue(X);`,
   `"and"(B);` must stay clean (Task 1 fixture, Task 4).
3. **Declaring an operator word.** `value(0; and)`, an option member `or`, a field `div`, a variable
   `and: Boolean;`, `procedure and()` must stay clean after the reserved set (Task 5 fixture).
4. **`is`/`as` as names in code** (41 production `is` member sites in BCApps) must stay identifiers
   (Task 5 fixture with `Rec.is`, `is := 1`, Task 6 zero-delta).
5. **Incremental reuse across the new fork.** Editing `Foo();` into `1 + Foo();` and back, or adding
   and deleting a `#if` group after an assignment, must give the fresh tree (Task 6).

---

## File Structure

- `grammar.js` — the rule, `inline`, `conflicts`, `reserved`, operator tokens, comments.
- `src/parser.c`, `src/grammar.json`, `src/node-types.json` — generated.
- `tools/alc_probe/cases/expression-statement/*.al` — compiler evidence (exists untracked; Task 1 fixes it).
- `tools/config_oracle/tests/test_expression_statement.py` — new: has_error contract (red first).
- `tools/config_oracle/tests/test_expression_statement_incremental.py` — new: incremental contract.
- `test/corpus/expression_statement_test.txt` — new: positive shapes, fields pinned.
- `test/corpus/expression_statement_split_test.txt` — new: GLR adversarial shapes (hand-written trees).
- `test/corpus/expression_statement_negative_test.txt` — new: invalid AL, deliberate negative.
- `test/corpus/expression_statement_b7_gap_test.txt` — new: valid AL that B6 makes loud and B7 must parse.
- `test/corpus/exit_statement_spacing_test.txt`, `verbatim_string_unterminated_test.txt`,
  `range_not_an_expression_negative_test.txt` — existing, Task 4.
- `tools/deliberate-negatives.txt`, `tools/config_oracle/fixture-classes.tsv` — bookkeeping.
- `CHANGELOG.md`, `docs/deferred-work.md`, `docs/superpowers/plans/2026-09-28-roadmap-remaining-work.md`,
  `CLAUDE.md` — Task 8.

---

### Task 1: Compiler evidence

**Files:**
- Modify: `tools/alc_probe/cases/expression-statement/*.al` (17 untracked files)
- Create: `tools/alc_probe/cases/expression-statement/` operator-word and torn-shape cases (listed below)

**Interfaces:**
- Produces: case files named in Task 7's `fixture-classes.tsv` evidence (`evidence: alc_probe <case .al>`).

- [ ] **Step 1: Correct the measured codes.** In these 5 files replace `// expect: * reject(AL0104)` by
  `// expect: * reject(AL0117)` (alc returned AL0117 for them, §2.2):
  `reject-comparison.al`, `reject-parenthesized.al`, `reject-subscript.al`, `semantic-bare-variable.al`,
  `semantic-member-field.al`. Rename the last two to `reject-bare-variable-al0117.al` and
  `reject-member-field-al0117.al` and change their first comment line to say the parser ACCEPTS them
  (symbols needed) while alc rejects with AL0117.

- [ ] **Step 2: Add operator-word cases.** Each uses the same template as the existing files (copy
  `accept-call.al`, change the description line, the `expect:`, and the body / declarations). Write:

| file | declarations added to `codeunit 50101` | body of `Main` | expect |
|---|---|---|---|
| `reject-stmt-start-and.al` | `procedure "and"(X: Boolean) begin end;` | `and(C);` | `* reject(AL0104)` |
| `reject-stmt-start-or.al` | `procedure "or"(X: Boolean) begin end;` | `or(C);` | `* reject(AL0104)` |
| `reject-stmt-start-xor.al` | `procedure "xor"(X: Boolean) begin end;` | `xor(C);` | `* reject(AL0104)` |
| `reject-stmt-start-div.al` | `procedure "div"(X: Boolean) begin end;` | `div(C);` | `* reject(AL0104)` |
| `reject-stmt-start-mod.al` | `procedure "mod"(X: Boolean) begin end;` | `mod(C);` | `* reject(AL0104)` |
| `reject-stmt-start-in.al` | `procedure "in"(X: Boolean) begin end;` | `in(C);` | `* reject(AL0104)` |
| `reject-stmt-start-not.al` | `procedure "not"(X: Boolean) begin end;` | `not(C);` | `* reject(AL0104)` |
| `reject-assign-to-and.al` | var `"and": Boolean;` | `and := true;` | `* reject(AL0104)` |
| `reject-read-and-in-expression.al` | var `"and": Boolean;` | `C := and;` | `* reject(AL0224)` |
| `accept-declare-and-procedure.al` | `procedure and(X: Boolean) begin end;` | `C := true;` | `* accept` |
| `accept-quoted-and-call.al` | `procedure "and"(X: Boolean) begin end;` | `"and"(C);` | `* accept` |
| `accept-stmt-start-is.al` | `procedure "is"(X: Boolean) begin end;` | `is(C);` | `* accept` |
| `accept-stmt-start-as.al` | `procedure "as"(X: Boolean) begin end;` | `as(C);` | `* accept` |
| `accept-bare-order.al` | `procedure Order() begin end;` | `Order;` | `* accept` |
| `accept-bare-table-before-end.al` | `procedure Table() begin end;` | `Table` | `* accept` |

  (`C` is the `Boolean` already declared in the template's `var`; the template's var list reads
  `var Rec: Record T; X: Integer; Arr: array[3] of Integer; C: Boolean;` — append new vars there.)

- [ ] **Step 3: Add torn-shape cases with per-configuration verdicts** (the probe resolves `#if`):

`torn-call-plus.al`, body:
```al
        Foo()
#if X
        + 2
#endif
        ;
```
expect lines: `// expect: X reject(AL0117)` and `// expect: !X accept`.

`torn-exit-plus.al` (in a procedure with return type `Integer`; add `procedure Main2(): Integer begin exit(1) #if X + 2 #endif; end;` style body spread over lines as above):
```al
        exit(1)
#if X
        + 2
#endif
        ;
```
expect: `X accept` if alc accepts `exit(1) + 2;`, else `X reject(<code>)`; `!X accept`. Write your
prediction (`X reject(AL0104)`), run, and if alc disagrees record the real code in the file and in
your task report — the run is the evidence, not the prediction.

`torn-until-and.al`, body:
```al
        repeat
            Foo();
        until C
#if X
            and (C)
#endif
        ;
```
expect: `// expect: X accept` and `// expect: !X accept` (valid in both: this is a B7 gap, §7).

`torn-call-or.al`, body: `Foo()` / `#if X` / `or (2 = 2)` / `#endif` / `;` (one per line);
expect: `X reject(AL0117)`, `!X accept`.

- [ ] **Step 4: Run the evidence.**
```bash
MSYS_NO_PATHCONV=1 ./tools/ts-lock.sh python -m tools.alc_probe run tools/alc_probe/cases/expression-statement --check
```
Expected: last line `... 0 unexpected MISMATCH, 0 drifted from expect`, exit 0. A `BROKEN` row means
the template is wrong (AL0440 came from a procedure named `Run`; keep `Main`). A drift means your
prediction was wrong: change that file's `expect:` to the measured verdict ONLY for files you created
in this task, and list each such change in your report.

- [ ] **Step 5: Commit.**
```bash
git add tools/alc_probe/cases/expression-statement
git commit -m "test(alc): B6 evidence -- statement shapes, operator words, torn continuations

[BC.History: 0 errors, 100% success]"
```

---

### Task 2: The has_error contract (red)

**Files:**
- Create: `tools/config_oracle/tests/test_expression_statement.py`

**Interfaces:**
- Consumes: the `al_parser` pytest fixture (`tools/config_oracle/tests/conftest.py`).
- Produces: `ACCEPT` and `REJECT` lists that Task 3 and Task 5 turn green.

- [ ] **Step 1: Write the test.**
```python
"""B6: a statement expression is an invocation; operator words are not names in code.

Spec docs/superpowers/specs/2026-10-06-expression-statement-narrowing-design.md; alc evidence
tools/alc_probe/cases/expression-statement. has_error, not the ERROR count, is the contract:
it is the only view that also sees a MISSING hidden token (CLAUDE.md).
"""
import pytest

HOST = (b"codeunit 50101 P {\n"
        b"  procedure Main()\n"
        b"  var Rec: Record T; X: Integer; Arr: array[3] of Integer; C: Boolean;\n"
        b"  begin\n%s\n  end;\n}\n")

# Valid AL (alc ACCEPT) or symbol-dependent (alc AL0117 only with symbols): must parse clean.
ACCEPT = [
    b"Foo();",
    b"Rec.Get();",
    b"Rec.Reset;",
    b"Bar",                                   # parenless, no `;`, before end
    b"if C then Bar else Foo();",             # parenless before else
    b'"My Proc";',
    b'"My Proc"',
    b"Order;",
    b"Table",
    b"if C then Order else Table;",
    b"Continue(X);",
    b'"and"(C);',
    b"is(C);",
    b"as(C);",
    b"Rec.is;",
    b"this.Foo();",
    b"Codeunit.Run(Codeunit::\"X\");",
    b"Arr[1].Reset;",
    b"X;",                                    # AL0117 needs symbols: parser accepts
    b"Rec.Name;",                             # likewise
    b"X := 1\n#if A\n  + 2\n#endif\n  ;",
    b"X := 1\n#if A\n  and (C)\n#else\n  or (C)\n#endif\n  ;",
    b"X := 1\n#if A\n  +\n#else\n  -\n#endif\n  2;",
    b"#if A\n  Foo();\n#else\n  Bar;\n#endif",
    b"X := 1;\n#if A\n  Foo();\n#endif\n  Bar();",
]

# Invalid AL (alc AL0104 / AL0117 decidable without symbols / AL0224): must ERROR.
REJECT = [
    b"1;", b"'abc';", b"1 + 2;", b"+ 3;", b"-Foo();", b"not Foo();", b"(Foo());",
    b"Rec.Get() = true;", b"Arr[1];", b"Foo()[1];",
    b"and(C);", b"or(C);", b"xor(C);", b"div(C);", b"mod(C);", b"in(C);", b"not(C);",
    b"and := true;", b"C := and;",
    b"Foo()\n#if A\n  + 2\n#endif\n  ;",
    b"Foo()\n#if A\n  or (2 = 2)\n#endif\n  ;",
    b"exit(1)\n#if A\n  + 2\n#endif\n  ;",
]

# Valid AL in every configuration that B6 makes LOUD and B7 must parse (spec §7).
B7_GAP = [
    b"repeat Foo(); until C\n#if A\n  and (C)\n#endif\n  ;",
]


@pytest.mark.parametrize("stmt", ACCEPT, ids=repr)
def test_accepted_statement_parses_clean(al_parser, stmt):
    assert al_parser.parse(HOST % stmt).root_node.has_error is False


@pytest.mark.parametrize("stmt", REJECT, ids=repr)
def test_rejected_statement_errors(al_parser, stmt):
    assert al_parser.parse(HOST % stmt).root_node.has_error is True


@pytest.mark.parametrize("stmt", B7_GAP, ids=repr)
def test_b7_gap_is_loud_not_silent(al_parser, stmt):
    assert al_parser.parse(HOST % stmt).root_node.has_error is True


DECLARATIONS = [
    b"enum 50100 E { value(0; and) { } value(1; or) { } value(2; in) { } value(3; mod) { } }\n",
    b"table 50100 T { fields { field(1; div; Integer) { } field(2; K; Option) { OptionMembers = and,or,is; } } }\n",
    b"codeunit 50102 Q { procedure and(X: Boolean) begin end; var \"and\": Boolean; }\n",
]


@pytest.mark.parametrize("src", DECLARATIONS, ids=repr)
def test_operator_words_still_declare(al_parser, src):
    assert al_parser.parse(src).root_node.has_error is False
```

- [ ] **Step 2: Run it on main's grammar.**
```bash
./tools/ts-lock.sh python -m pytest tools/config_oracle/tests/test_expression_statement.py -q
```
Expected: FAIL. Every `REJECT` and `B7_GAP` case fails (main parses them clean), except
`b"Foo()[1];"`, which may already ERROR — note any REJECT case that already passes in your report.
Every `ACCEPT` and `DECLARATIONS` case passes. If an ACCEPT case fails on main, stop: the case is
wrong or main has a gap; report it, do not continue.

- [ ] **Step 3: Commit (red test).**
```bash
git add tools/config_oracle/tests/test_expression_statement.py
git commit -m "test(b6): has_error contract for statement shapes (red)

[BC.History: 0 errors, 100% success]"
```

---

### Task 3: Narrow `_expression_statement`

**Files:**
- Modify: `grammar.js` — `inline` (~line 889), `conflicts` (~line 520 `[$.assignment_statement, $.assignment_expression]` and the `[$._single_pattern, $._expression]` entry), `_expression_statement` and its comment (~line 5462-5489)
- Generated: `src/parser.c`, `src/grammar.json`, `src/node-types.json`

**Interfaces:**
- Consumes: Task 2's test.
- Produces: the narrowed hidden rule `_expression_statement`; conflict `[$.assignment_statement]`.

- [ ] **Step 1: Remove the rule from `inline`.**
```javascript
  inline: $ => [
    $._field_source,
  ],
```

- [ ] **Step 2: Replace the rule and its KNOWN comment** (the whole comment block starting
`// KNOWN: this accepts ANY expression as a statement` through `_expression_statement: $ => $._expression,`):
```javascript
    // A statement expression is an INVOCATION and nothing else (roadmap B6, spec
    // docs/superpowers/specs/2026-10-06-expression-statement-narrowing-design.md).
    // alc accepts only assignments and method invocations as statements: a literal,
    // unary or operator-led statement is AL0104, and a comparison, parenthesised or
    // subscript statement is AL0117 ("Only assignment and method invocation can be
    // used as a statement"; tools/alc_probe/cases/expression-statement). `X;` and
    // `Rec.Name;` are AL0117 too, but only symbols tell a variable from a procedure or
    // a field from a method, so a bare name and a member stay accepted.
    //
    // This is the fail-loud backstop: a fragment of an unhosted `#if` continuation
    // (`Foo()` / `#if A` / `+ 2` / `#endif` / `;`) used to reparse as a statement, the
    // host keeping a truncated expression and the rest floating off with no ERROR.
    // Now it ERRORs. It attaches nothing: hosts with no continuation facility
    // (`repeat ... until`, `foreach ... in`, `with`) still need B7.
    //
    // NOT in `inline`, on purpose. Two earlier narrowings left it inlined, so its
    // precedence and conflicts were macro-substituted into each host separately, and
    // BC.History fell to 35.7% / 33.3%. De-inlined, the four corpora are byte-identical.
    //
    // prec(-1): at `begin X • -` the statement reduction and the `_expression` one
    // compete; no statement can be followed by an operator, so the expression wins.
    // The `_value_start_keyword_name` arm: `table`/`order` are live keyword tokens at
    // statement start, so a parenless call to a procedure named `Order` arrives as one.
    _expression_statement: $ => prec(-1, choice(
      $.call_expression,
      $.member_expression,
      $.identifier,
      $.quoted_identifier,
      alias($._value_start_keyword_name, $.identifier),
    )),
```

- [ ] **Step 3: Conflicts.** Add, directly after the `conflicts: $ => [` opening's existing
`[$.assignment_statement, $.assignment_expression],` line (then delete that line in Step 5 if
generate reports it unnecessary):
```javascript
    // B6: narrowing _expression_statement exposes the decision at `x := e • #if`:
    // continue the right-hand side (preproc_conditional_expression_tail) or end the
    // assignment and open a preproc_conditional_statement. Only the arm content
    // decides, so it stays a GLR fork; static precedence would commit first (see
    // _expression_continuation's comment for what that did).
    [$.assignment_statement],
```

- [ ] **Step 4: Generate.**
```bash
./tools/ts-lock.sh tree-sitter generate 2>&1 | tail -8; grep -E 'define (STATE|LARGE_STATE|SYMBOL)_COUNT' src/parser.c
```
Expected: success with `Warning: unnecessary conflicts:` listing `_single_pattern`, `_expression` and
`assignment_statement`, `assignment_expression`; STATE_COUNT 23,211. If generate fails with
`os error 1224` (a mapped-file lock on `src/`), re-run it; it is transient on this machine.

- [ ] **Step 5: Delete the two unnecessary conflicts**, `[$._single_pattern, $._expression],` and
`[$.assignment_statement, $.assignment_expression],`, together with any comment lines that describe
only them (read the comment above each first; keep a comment that also covers a neighbour). Re-run
Step 4: expected no warning, STATE_COUNT recorded in your report.

- [ ] **Step 6: Run the contract.**
```bash
./tools/ts-lock.sh python -m pytest tools/config_oracle/tests/test_expression_statement.py -q
```
Expected: every ACCEPT, DECLARATIONS and B7_GAP case passes; every REJECT case passes EXCEPT the
operator-word ones (`and(C);` ... `not(C);`, `and := true;`, `C := and;`, the `or (2 = 2)` torn case),
which Task 5 fixes. `not(C);` may already pass (unary). Record the exact failing list.

- [ ] **Step 7: Zero-delta.**
```bash
for c in bc:./BC.History dc:./DC bc28:H:/Git/BC28.1 bcapps:H:/Git/BCApps-29.0; do echo "== ${c%%:*}"; ./tools/ts-lock.sh ./tools/tree-harness.sh verify ${c#*:} .snapshots/baseline-b6-${c%%:*} 2>&1 | tail -2; done
```
Expected: `VERIFIED` for bc, dc, bc28; bcapps reports exactly 1 changed file,
`src/Layers/APAC/Tests/SINGLESERVER/ERMPurchaseReportsIII.Codeunit.al`. Any other changed file stops
the task: report it.

- [ ] **Step 8: Commit** (generated files together):
```bash
git add grammar.js src/parser.c src/grammar.json src/node-types.json
git commit -m "fix(b6): _expression_statement is an invocation, not inlined

[BC.History: 0 errors, 100% success]"
```
(Measure the trailer: `./tools/ts-lock.sh ./parse-al-parallel.sh ./BC.History/ . 2>&1 | tail -3`.)

---

### Task 4: Fixtures for the narrowed rule

**Files:**
- Create: `test/corpus/expression_statement_test.txt`, `test/corpus/expression_statement_split_test.txt`,
  `test/corpus/expression_statement_negative_test.txt`, `test/corpus/expression_statement_b7_gap_test.txt`
- Modify: `test/corpus/exit_statement_spacing_test.txt`, `test/corpus/verbatim_string_unterminated_test.txt`,
  `test/corpus/range_not_an_expression_negative_test.txt`, `tools/deliberate-negatives.txt`

**Interfaces:**
- Consumes: Task 3's grammar.

- [ ] **Step 1: Record the suite total before.** `./tools/ts-lock.sh tree-sitter test 2>&1 | tail -1`
  (expect `failed parses: 3` — the three existing fixtures). Note the total parses number T0.

- [ ] **Step 2: Positive fixture** `expression_statement_test.txt`. One case per line of this list,
  each a full codeunit with the statement in a procedure body (same HOST as Task 2), case header in
  the corpus format (contiguous `====` header, `---` divider — CLAUDE.md traps 3 and 4):
  call, member call, parenless member, bare identifier before `end` (no `;`), bare identifier before
  `else`, bare quoted identifier with and without `;`, `Order;`, `Table` before `end`,
  `if C then Order else Table;`, `Continue(X);`, `"and"(C);`, `is(C);`, `Rec.is;`, `this.Foo();`,
  `Arr[1].Reset;`, a guard preamble (`#if A` / `Foo();` / `if C then` / `#endif` / `Bar();`),
  statements inside `#if`/`#elif`/`#else` arms, nested `#if`, and `exit; Foo();`.
  Generate each expected tree with `python tools/snip.py --sexp '<statement>'` (never `-u`): its
  output is the corpus test format WITH field labels (`--raw -f FILE` for a whole file). Read each tree: every statement must be the node the source says (a call is a
  `call_expression` or `call_statement`, never split, no ERROR).

- [ ] **Step 3: Prove a field can fail.** Rename one `function:` label to `bogus:` in the new file,
  run `./tools/ts-lock.sh tree-sitter test --file-name expression_statement_test.txt`, see it FAIL,
  restore the label, see it PASS.

- [ ] **Step 4: Split adversarial fixture** `expression_statement_split_test.txt`. Cases (each as an
  assignment or statement in a procedure body):
  1. `B := A` / `#if X` / `+ 2` / `#else` / `- 3` / `#endif` / `* 4;`
  2. `B := 1` / `#if X` / `+` / `#else` / `-` / `#endif` / `2;`
  3. `B := A` / `#if X` / `and (C)` / `#else` / `or (D)` / `#endif` / `;`
  4. `B := A;` / `#if X` / `Foo();` / `#else` / `Bar();` / `#endif` / `Baz();`  (`;` before `#if`: calls are statements)
  5. `B := A` / `#if X` / `+ 1;` / `Foo();` / `#else` / `;` / `#endif`  (`;` inside each arm)
  6. case 1 with `#elif Y` / `- 5` added, and with `// c` comments at the end of each directive line
  7. case 3 nested inside `case X of 1: begin ... end; end;` and inside `if C then ... else ...`
  Write each expected tree BY HAND from the flat reading first (what the tree must be: one
  `assignment_statement` whose `preproc_conditional_expression_tail` holds the arms), then compare
  with `python tools/snip.py --sexp`; a difference is a finding to report, not a reason to paste the
  parser's tree. Cases 4 and 5 must keep the calls as separate statements.

- [ ] **Step 5: Negative fixture** `expression_statement_negative_test.txt` with a `;` documentation
  header naming alc's code per case (from Task 1): each REJECT input of Task 2 except the
  operator-word ones (Task 5 adds those), and `exit; (a + b);` moved from
  `exit_statement_spacing_test.txt` (its tree must still show `(exit_statement (exit_keyword))` with
  no value). Expected trees from `python tools/snip.py --sexp`, each ERROR read and placed on the
  rejected statement. Add the basename to `tools/deliberate-negatives.txt` with a comment
  `# B6: invalid statements (alc AL0104 / AL0117); the ERROR is the assertion.`

- [ ] **Step 6: B7 gap fixture** `expression_statement_b7_gap_test.txt`, header: valid AL in every
  configuration (alc `torn-until-and.al`), loud since B6, B7 must parse it. Case:
  `repeat Foo(); until C` / `#if X` / `and (C)` / `#endif` / `;` (add after Task 5 if the tree
  changes there — leave a note in your report). Add the basename to `tools/deliberate-negatives.txt`
  with a comment `# B6 -> B7: valid AL, loud ERROR until B7 gives repeat-until a continuation.`

- [ ] **Step 7: The three existing fixtures.**
  - `exit_statement_spacing_test.txt`: delete only the `bare exit does not swallow ...` case (it moved
    in Step 5); the `exit (42)` case stays and must pass.
  - `verbatim_string_unterminated_test.txt`: add the basename to `tools/deliberate-negatives.txt`
    (`# B6: alc rejects this file (AL0104); the leftover is no longer a legal statement.`), update the
    header sentence "both legal statements under _expression_statement" to say they are now an ERROR,
    and regenerate the expected tree from `snip.py --raw --sexp -f`. Check: the `verbatim_string` node
    still ends exactly where it did before (closing quote of `'a'`).
  - `range_not_an_expression_negative_test.txt`: regenerate the one failing case's tree; explain every
    hunk in your report.

- [ ] **Step 8: Run the suite and count.**
```bash
./tools/ts-lock.sh tree-sitter test 2>&1 | tail -1; git diff --stat test/corpus
```
Expected: 0 failures; total = T0 + (cases you added) − 1 (the moved exit case is counted once, in the
negative file, so +0 for it). Any file in `git diff --stat` you did not intend to touch: restore it.

- [ ] **Step 9: Gates for fixtures.**
```bash
./tools/ts-lock.sh python tools/has_error_sweep.py --corpus-fixtures; ./validate-grammar.sh 2>&1 | grep -E '✓|✗' | sed 's/\x1b\[[0-9;]*m//g'
```
Expected: sweep exit 0; validate all ✓ except Step 9 (WASM stale, fixed in Task 8) and possibly 5d
(qc, Task 7) and 5e (oracle, Task 7).

- [ ] **Step 10: Commit.**
```bash
git add test/corpus tools/deliberate-negatives.txt
git commit -m "test(b6): statement-shape, split, negative and B7-gap fixtures

[BC.History: 0 errors, 100% success]"
```

---

### Task 5: Operator words are not names in code

**Files:**
- Modify: `grammar.js` — `reserved` block (~line 440-463), operator uses (~lines 4868-4883, 5599-5603,
  6354, 6438-6452, 6499, 6847), new hidden token rules beside `_true_token` (~line 1927)
- Generated: `src/*`
- Modify: `test/corpus/expression_statement_negative_test.txt`, `test/corpus/expression_statement_test.txt`

**Interfaces:**
- Consumes: Task 3's rule.
- Produces: reserved set `code_names`; hidden tokens `_and_token`, `_or_token`, `_xor_token`,
  `_div_token`, `_mod_token`, `_in_token`, `_not_token`.

- [ ] **Step 1: Token symbols.** Next to `_true_token`/`_false_token` add:
```javascript
    // B6: the operator words as rule symbols, so the `code_names` reserved set can list
    // them (a reserved entry must be a symbol, not a fresh kw()).
    _and_token: $ => kw('and'),
    _or_token: $ => kw('or'),
    _xor_token: $ => kw('xor'),
    _div_token: $ => kw('div'),
    _mod_token: $ => kw('mod'),
    _in_token: $ => kw('in'),
    _not_token: $ => kw('not'),
```
  and replace every `alias(kw('and'), 'and')` by `alias($._and_token, 'and')`, likewise for `or`,
  `xor`, `div`, `mod`, `not`, and `in_keyword`'s `alias(kw('in'), 'in')` by `alias($._in_token, 'in')`
  (`grep -nE "kw\('(and|or|xor|div|mod|in|not)'\)" grammar.js` must print nothing afterwards).
  Generate; run the tree-harness verify loop of Task 3 Step 7: must be unchanged from Task 3's result
  (this step alone changes no tree). If generate reports a lexical conflict, stop and report it.

- [ ] **Step 2: The reserved set.** In `reserved:` after `relation_target_names` add:
```javascript
    // B6: in code, alc never reads these seven words as a bare identifier: a statement
    // starting with one is AL0104 and an expression reading one is AL0224
    // (tools/alc_probe/cases/expression-statement). Declaring one is fine
    // (`procedure and()`, `value(0; and)`, a field `div`), and is then referenced
    // quoted. `is`/`as` are names in code and are NOT here. Without this set a torn
    // keyword-operator continuation (`until A #if X and (B) #endif ;`) read as a call
    // to a function named `and`, with no ERROR.
    code_names: $ => [$._and_token, $._or_token, $._xor_token, $._div_token,
                      $._mod_token, $._in_token, $._not_token],
```

- [ ] **Step 3: Apply it, first attempt: `_expression`.** Wrap `_expression`'s body:
`_expression: $ => reserved('code_names', choice( ...unchanged... )),`. Also wrap the `function`
choice of `call_expression` and the body of `_expression_statement` in `reserved('code_names', ...)`
(each names `$.identifier` directly; the set applies only where the rule's next step is `identifier`
itself). Generate. Record STATE_COUNT.

- [ ] **Step 4: Measure.**
```bash
./tools/ts-lock.sh python -m pytest tools/config_oracle/tests/test_expression_statement.py -q
for r in ./BC.History ./DC H:/Git/BC28.1 H:/Git/BCApps-29.0; do ./tools/ts-lock.sh python tools/has_error_sweep.py --root $r 2>&1 | tail -1; done
```
Expected: pytest all green; sweeps clean (BCApps: the 2 pre-existing visible files only). If an
operator-word REJECT case still fails, the set did not reach that state: add `reserved('code_names', …)`
to the rule that names `$.identifier` at that position (find it with `python tools/snip.py` on the
case: the parent of the identifier node), regenerate, re-measure. If a DECLARATIONS case fails, the set
reached a declaration state: move the wrapper inward to the code-only rule and re-measure.
STATE_COUNT above ~23,418: record it, and also build the §4.3 fallback (wrap only
`_expression_statement` and `call_expression.function`, not `_expression`) to report both numbers;
do not choose — the user decides (Global Constraints).

- [ ] **Step 5: Zero-delta** — the Task 3 Step 7 loop. Expected: same as Task 3 (bc/dc/bc28
  VERIFIED, bcapps exactly the one ERROR file).

- [ ] **Step 6: Fixtures.** Add to `expression_statement_negative_test.txt` one case per operator word
  at statement start (`and(C);` ... `not(C);`), `and := true;`, `C := and;`, and the torn
  `Foo()` / `#if X` / `or (2 = 2)` / `#endif` / `;`; add to `expression_statement_test.txt` the
  declaration cases of Task 2's `DECLARATIONS` and `"and"(C);`, `is(C);`, `as(C);`, `Rec.is;`. Trees
  from `snip.py --sexp`, read. If the B7 gap tree changed, update `expression_statement_b7_gap_test.txt`.
  Suite total moves by exactly the cases added.

- [ ] **Step 7: Commit.**
```bash
git add grammar.js src/parser.c src/grammar.json src/node-types.json test/corpus
git commit -m "fix(b6): operator words are not names in code (reserved set code_names)

[BC.History: 0 errors, 100% success]"
```

---

### Task 6: Audits and the incremental contract

**Files:**
- Create: `tools/config_oracle/tests/test_expression_statement_incremental.py`
- Create: `docs/b6-audit.md` (the record of Steps 2-4)

- [ ] **Step 1: Incremental test.**
```python
"""B6: incremental re-parse after an edit equals a fresh parse, across the new fork."""
import pytest

from tools.config_oracle.tests.test_link_incremental import _edit

HOST = (b"codeunit 50101 P {\n  procedure Main()\n  var X: Integer; C: Boolean;\n"
        b"  begin\n%s\n  end;\n}\n")

EDITS = [
    (b"Foo();", b"1 + Foo();"),
    (b"1 + Foo();", b"Foo();"),
    (b"Foo();", b"(Foo());"),
    (b"(Foo());", b"Foo();"),
    (b"Foo();\n  Bar();", b"Foo()\n  Bar();"),
    (b"Order();", b"Order;"),
    (b"Order;", b"Order();"),
    (b"X := 1;\n  Foo();", b"X := 1\n#if A\n  + 2\n#endif\n  ;\n  Foo();"),
    (b"X := 1\n#if A\n  + 2\n#endif\n  ;\n  Foo();", b"X := 1;\n  Foo();"),
    (b"X := 1\n#if A\n  + 2\n#endif\n  ;", b"X := 1;\n#if A\n  Foo();\n#endif"),
    (b"X := 1;\n#if A\n  Foo();\n#endif", b"X := 1\n#if A\n  + 2\n#endif\n  ;"),
    (b"Foo(C);", b"and(C);"),
    (b"and(C);", b"Foo(C);"),
]


@pytest.mark.parametrize("before,after", EDITS, ids=repr)
def test_incremental_equals_fresh(al_parser, before, after):
    incremental = _edit(al_parser, HOST % before, HOST % after)
    fresh = al_parser.parse(HOST % after)
    assert str(incremental.root_node) == str(fresh.root_node)
    assert incremental.root_node.has_error == fresh.root_node.has_error
```
Run: `./tools/ts-lock.sh python -m pytest tools/config_oracle/tests/test_expression_statement_incremental.py -q` — expected PASS.
A failure is an incremental-reuse defect: report it with the edit, do not weaken the test.

- [ ] **Step 2: The `prec(-1)` audit.** Build a comparison grammar in which the precedence is replaced
  by a declared conflict, so GLR keeps both readings: in `grammar.js` temporarily change
  `_expression_statement: $ => prec(-1, choice(` to `choice(` (drop the matching `)`), add
  `[$._expression_statement, $._expression],` to `conflicts`, generate. If generate demands further
  entries, add exactly what it names and list them. Then run the Task 3 Step 7 verify loop against the
  SAME baselines and the full fixture suite. Record in `docs/b6-audit.md`: generate's conflicts, the
  STATE_COUNT, the verify results, the test totals. Expected: identical trees to the `prec(-1)` build
  (the precedence only resolves an ambiguity no valid input needs). Any difference: record the file and
  hunk, restore the `prec(-1)` grammar, and report — do not choose. Restore the `prec(-1)` grammar and
  regenerate in all cases (`git diff grammar.js` must show nothing after restoring).

- [ ] **Step 3: BCApps hunk review.** `./tools/ts-lock.sh ./tools/tree-harness.sh verify H:/Git/BCApps-29.0 .snapshots/baseline-b6-bcapps > /tmp/b6-bcapps.diff 2>&1`;
  for every hunk, record in `docs/b6-audit.md` its line range and the nearest ERROR node's range in the
  OLD tree, read from the hunk's `<` (snapshot) side and its surrounding context. Pass: every changed node lies inside or immediately
  adjacent to a region that is ERROR in the old tree. A changed valid procedure outside such a region
  fails the task: report it.

- [ ] **Step 4: Perf.**
```bash
python -m tools.perf ab --help | head -20
```
Build the base library from main and the new library from this branch as `tools.perf ab` documents
(`--lib-a OLD.dll --lib-b NEW.dll --corpus dc`, at least 24 rounds; three independent runs). Also
create a synthetic file in the scratchpad (not the repo): 5,000 copies of
`X := 1\n#if A\n  + 2\n#else\n  - 3\n#endif\n  ;\n` inside one procedure, and time
`./tools/ts-lock.sh tree-sitter parse --time <file>` on both libraries, three runs each. Record ratios
and CIs in `docs/b6-audit.md`. Over the 1% guideline: record and report; it does not fail the task.

- [ ] **Step 5: Commit.**
```bash
git add tools/config_oracle/tests/test_expression_statement_incremental.py docs/b6-audit.md
git commit -m "test(b6): incremental contract; prec(-1) audit, BCApps hunk review, perf

[BC.History: 0 errors, 100% success]"
```

---

### Task 7: Oracle, qc and the full gate

**Files:**
- Modify: `tools/config_oracle/fixture-classes.tsv`, `tools/query_coverage/baseline.json` (only if qc reports a new cluster)

- [ ] **Step 1: Oracle quick tier.**
```bash
./tools/ts-lock.sh python -m tools.config_oracle run --tier quick; echo EXIT=$?
```
Expected: exit 0, or exit 1 naming unclassified cannot-validate records for the new fixtures. For each,
add a line to `fixture-classes.tsv` in the documented format (read the file header first):
- a case from `expression_statement_negative_test.txt` whose configuration alc rejects:
  `negative: <why>; evidence: alc_probe tools/alc_probe/cases/expression-statement/<case>.al`, and add
  `// Fixture <case_id>` to that probe file;
- a torn case valid in one configuration only (`Foo()` + `#if X + 2`): `invalid-config: <why>; evidence: alc_probe .../torn-call-plus.al`;
- the B7 gap case: `debt(B7): repeat-until has no continuation facility (spec §7)`.
Re-run until exit 0. An entry for a record that does not exist is stale and fails: add only what the
run names.

- [ ] **Step 2: Replay and the alc check.**
```bash
./tools/ts-lock.sh python -m tools.config_oracle replay; echo EXIT=$?
MSYS_NO_PATHCONV=1 ./tools/ts-lock.sh python -m tools.alc_probe run tools/alc_probe/cases --check | tail -1
```
Expected: both exit 0.

- [ ] **Step 3: qc.** `./tools/ts-lock.sh python -m tools.query_coverage.qc run; echo EXIT=$?` — expected 0
(no new node types). A new cluster: explain it in your report before any `qc accept`.

- [ ] **Step 4: Full validation and sweeps.**
```bash
./validate-grammar.sh --full 2>&1 | grep -E '✓|✗' | sed 's/\x1b\[[0-9;]*m//g'
for r in ./BC.History ./DC H:/Git/BC28.1 H:/Git/BCApps-29.0; do ./tools/ts-lock.sh python tools/has_error_sweep.py --root $r 2>&1 | tail -1; done
./tools/ts-lock.sh python -m pytest tools/config_oracle/tests -q 2>&1 | tail -2
```
Expected: all ✓ except Step 9 (WASM, Task 8); sweeps clean (BCApps 2 pre-existing); pytest green.

- [ ] **Step 5: Commit.**
```bash
git add tools/config_oracle/fixture-classes.tsv tools/alc_probe/cases tools/query_coverage/baseline.json
git commit -m "test(b6): oracle classifications for the new fixtures

[BC.History: 0 errors, 100% success]"
```

---

### Task 8: Documentation and WASM

**Files:**
- Modify: `CHANGELOG.md`, `docs/deferred-work.md` (item 4), `docs/superpowers/plans/2026-09-28-roadmap-remaining-work.md` (row B6),
  `CLAUDE.md` ("Reserved-word sets" bullet in Key Design Principles), `tree-sitter-al.wasm`, `tree-sitter-al.wasm.inputs.sha256`

- [ ] **Step 1: CHANGELOG.** Under `## [Unreleased]` → the EXISTING `### Fixed` section (there is one
  after `### Changed`; do not add a second), first entry:
  `**A statement must be an invocation, and the operator words are not names in code (roadmap B6,
  deferred-work item 4).**` followed by: what parsed clean before (`1 + 2;`, `'abc';`, detached `#if`
  fragments, keyword-operator tears) and now ERRORs, with alc codes; what stays accepted (`X;`,
  `Rec.Name;`, bare/quoted/`Order` parenless calls); the reserved set and its exclusions (`is`, `as`,
  declarations); STATE_COUNT before → after; the perf ratio; "valid-AL trees byte-identical in all four
  corpora (BCApps: one file with a pre-existing ERROR changes its recovery)"; the B7 gap.
- [ ] **Step 2: deferred-work item 4** → `— RESOLVED 2026-10-06`, a `**Resolved by**` paragraph with the
  commit hashes, keeping the old record "as written" (follow items 31/32/34's format).
- [ ] **Step 3: roadmap row B6** → `**DONE 2026-10-06 (branch fix/b6-expression-statement).**` with the
  numbers, keeping the original row text after "Original row:" (follow B5b's format).
- [ ] **Step 4: CLAUDE.md** — the "Reserved-word sets, two contextual sets" bullet becomes "three", and
  gains one sentence for `code_names` (what it reserves, why, `is`/`as` excluded, where it sits).
  Update the `reserved:` comment in `grammar.js` ("at exactly one site each") if Task 5 used more than
  one site.
- [ ] **Step 5: Commit docs.**
```bash
git add CHANGELOG.md docs/deferred-work.md docs/superpowers/plans/2026-09-28-roadmap-remaining-work.md CLAUDE.md grammar.js
git commit -m "docs(b6): changelog, deferred-work 4 resolved, roadmap B6 done, reserved sets

[BC.History: 0 errors, 100% success]"
```
- [ ] **Step 6: WASM.**
```bash
./tools/ts-lock.sh tree-sitter build --wasm -o tree-sitter-al.wasm && tools/check-wasm-fresh.sh --update && tools/check-wasm-fresh.sh
git add tree-sitter-al.wasm tree-sitter-al.wasm.inputs.sha256
git commit -m "build(wasm): rebuild for B6

[BC.History: 0 errors, 100% success]"
```
- [ ] **Step 7: Final gate on the combined state.** `./validate-grammar.sh --full` → every step ✓.
  Delete `.snapshots/baseline-b6-*` only after this passes.
