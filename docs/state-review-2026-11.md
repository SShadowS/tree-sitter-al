# State review, 2026-11: where the parser states are and how to cut them

Reviewed: main `abc77b25` (v5.1.0). Worktree `/work/tsal/.claude/worktrees/agent-ae5b801d0cb507521`, branch
`state-review/candidates` (three commits, one per candidate). Nothing was pushed or merged.

Every number here was measured on 2026-11-10 and 11 in that worktree or in scratch copies of its `grammar.js` /
`src/grammar.json`, with tree-sitter CLI 0.27.0. A number marked *proxy* comes from a grammar that was only
generated, never built or run; it measures states, not trees. A number marked *upper bound* comes from deleting a
rule family, so it is what the family costs, not what a refactor would save.

## Summary

| | STATE_COUNT | LARGE_STATE_COUNT | `parser.c` |
|---|---|---|---|
| main `abc77b25` | 31,618 | 10,133 | 70,306,929 B (67.0 MiB) |
| C1: `#endif` is a grammar regex | 20,161 | 6,405 | 44,917,168 B (42.8 MiB) |
| C1 + C2: is/as right is a name-like type | 18,898 | 5,741 | 41,341,306 B (39.4 MiB) |
| C1 + C2 + C3: `end` is a grammar token | **16,720 (-47.1%)** | **4,609 (-54.5%)** | **34,606,030 B (33.0 MiB, -50.8%)** |

The one finding that matters: **77% of the parser's states are copies of other states, and the generator is barred
from merging them by external tokens in their lookahead sets.** Two tokens do almost all of it: `#endif` and `end`.
Making them grammar tokens again needs no tree change. On the four corpora every tree of a file that parses on main
is byte-identical; `node-types.json` is byte-identical.

**None of the three candidates is green on `tree-sitter test`.** 28 of 3,827 cases fail at the tip. All 28 are
deliberate negatives or known-gap witnesses that pin an error-recovery tree, and the recovery tree is what changed
(`#endif` and `end` are now lexable during recovery). I did not update them: that is the owner's call, as it was
for D1's C2. Section B lists them.

## A. Where the states are

### A.1 Three instruments

1. **The generator's own log.** `tree-sitter generate --log` prints one line for every pair of states the minimizer
   refuses to merge, with the reason (`minimize_parse_table.rs`, "split states A B - ..."). Aggregated
   (`scratchpad/sr/splitlog.py`):

   | reason | main | tip (C1+C2+C3) |
   |---|---|---|
   | split events, total | 585,088 | 146,463 |
   | external token in one lookahead set only | 319,120 | 69,985 |
   | successors already split (propagated from a root reason) | 247,329 | 62,250 |
   | lexical conflict between two grammar tokens | 15,768 | 12,828 |
   | differing action counts / unequal actions | 2,871 | 1,400 |

   On main, 95% of the root reasons (everything except "successors split") are external tokens. By token, main:
   `continue_as_identifier` 128,970, `preproc_close` 84,918, `property_name` 49,633, `preproc_open` 18,561,
   `end_keyword` 18,530, `begin_keyword` 16,808; the largest lexical one is `assignment_operator` against `-`
   (10,846). The log names only the FIRST reason for a pair (lowest symbol), so these counts rank suspects; they do
   not say what removing one token saves. The proxies in A.3 do.

2. **LR(0) cores.** `--report-states-for-rule RULE` dumps every state that holds an item of RULE, with items and
   lookaheads. Run once per rule (1,123 rules, `scratchpad/sr/dumpall.sh`) and joined by state index, that is every
   state of the parser. The minimizer only ever merges states with the same item-set core, so the number of distinct
   cores is the floor for this grammar.

   **main: 31,615 states dumped, 7,336 distinct cores, 24,279 states (77%) are clones.** States by how many clones
   their core has: 1 (unique) 2,290; 2: 4,232; 3-4: 3,291; 5-8: 6,868; 9-16: 7,578; 17-32: 6,376; 33-64: 980.
   The expression core is the clearest case: `logical_expression` appears in 793 states over 83 cores, each core
   copied up to 32 times, once per combination of statement context (plain block, case branch, repeat, after a
   split `#endif`, inside a split-procedure arm, ...).

3. **Family removal** (`scratchpad/sr/prune.py`, D1's method): every rule matching a regex becomes the empty
   language, propagated. An upper bound on what the family costs.

### A.2 The mechanism

`minimize_parse_table.rs::token_conflicts`: when two states with the same core differ by a lookahead token, the
token may be added to the other state only if it is not external ("Do not add external tokens; they could conflict
lexically with any of the state's existing lookahead tokens") and does not conflict lexically with a token already
there. A refused merge propagates backwards: two states whose successors are in different groups cannot merge
either. So **one external token at the END of a construct clones the whole construct per host**, if the hosts'
follow sets differ by it.

`#endif` was the external `PREPROC_CLOSE`. It is in the follow set of everything that can end a `#if` arm and of
nothing outside one, so every statement, expression, type and property value existed once "inside an arm" and once
"outside", times every other such split. `end` is in the follow set of a statement inside `begin..end` and not of
one in `repeat..until` or a bare then-branch.

The grammar already records this effect in the other direction, at `preproc_elif` in `grammar.js`: making
`#elif`/`#else` external "was measured and rejected (B2): STATE_COUNT 15,870 -> 25,301". And at `preproc_if`: a
token valid only after an if's then-branch "split every state below it (+9,206 states, measured)". `#endif` and
`end` are the same effect, never measured because they were external from the start.

### A.3 What each external token costs (*proxy*: the token made a regex in `grammar.json`, generate only)

| made internal | on main (31,618) | on C1+C2+C3 proxy (16,800) |
|---|---|---|
| `preproc_close` (`#endif`) | 20,106 (**-11,512**) | done |
| `end_keyword` | 28,512 (-3,106); with `#endif`: 17,861 | done |
| `begin_keyword` | 32,164 (+546) | 16,719 (-81) |
| `preproc_open` (`#if`) | 31,592 (-26) | 16,536 (-264) |
| `continue_as_identifier` | 31,141 (-477) | 16,965 (+165) |
| `property_name` | 33,158 (+1,540) | 17,090 (+290) |
| `preproc_split_end`, `preproc_split_begin`, `var_attribute_open`, `_directive_eol`, negative literals | within 22 | within 22 |
| `#endif` + `end` + `begin` + `#if` + `continue` + split tokens + `var_attribute_open` | 17,678 | |
| on the real tip: `continue` + `begin` + `#if` + `_preproc_open_before_else` together | | 16,690 (-30) |

After `#endif` and `end` nothing is left in the externals. The log still names `continue_as_identifier` first on
the tip (36,330 events), but those pairs are also held apart by something else (A.5).

### A.4 What the `#if` constructs cost (*upper bound*, family removed)

Remaining STATE_COUNT after removal, and the family's cost in brackets:

| family removed | main 31,618 | C1 20,161 | tip 16,720 |
|---|---|---|---|
| **every `#if` construct** (312 rules) | 3,532 (28,086) | 3,532 (16,629) | 3,055 (13,665) |
| split statement rules: `preproc_split_if*`, `_block*`, `_code_block*`, `_else_begin*`, `_open_statement`, `_call_statement`, `_complete_body`, `_case*`, guarded, fragmented (20) | 24,573 (7,045) | 15,872 (4,289) | 13,777 (2,943) |
| split declaration-level rules: declaration, field, key, modify, report, brace, permissions, container, var-section, procedure, trigger (18) | 28,622 (2,996) | 18,055 (2,106) | 14,614 (2,106) |
| of which the split procedure/trigger header and preamble family (9) | 29,620 (1,998) | 18,866 (1,295) | 15,425 (1,295) |
| `_property_with_terminator_in_if` + `_property_whole_value_in_if` (2 rules) | | | 14,412 (**2,308**) |
| keywords as names: `keyword_identifier`, `keyword_as_identifier`, `_value_start_keyword_name` | 28,363 (3,255) | 18,185 (1,976) | 14,846 (1,874) |
| `is` / `as` expressions with their typed groups | 28,494 (3,124) | 18,062 (2,099) | 16,225 (495) |
| split case rules (4) | 28,779 (2,839) | 18,672 (1,489) | 15,843 (877) |
| strict conditional list groups (35 rules, all families) | 30,336 (1,282) | 19,083 (1,078) | 15,643 (1,077) |
| statement empty groups / else decoration / case empty group | 30,519 (1,099) | 19,248 (913) | 15,915 (805) |
| `preproc_conditional_statement` with the empty groups | | | 15,866 (854) |
| nested header / preamble groups (items 77, 82, 83, 85: 3 rules) | | | 15,768 (952) |
| split preamble rules (4) | | | 15,975 (745) |
| label / caption tails (B7b-1d, 22 rules) | | | 16,066 (654) |
| operand groups (`preproc_conditional_operand`, receiver, typed) | | | 16,140 (580) |
| value runs, per family: ML | 30,377 (1,241) | 19,490 (671) | 16,049 (671) |
| Namespaces | 30,440 (1,178) | 19,519 (642) | 16,078 (642) |
| TableRelation | 30,646 (972) | 19,624 (537) | 16,183 (537) |
| CalcFormula | 30,687 (931) | 19,647 (514) | 16,206 (514) |
| link | 30,966 (652) | 19,805 (356) | 16,364 (356) |
| OptionMembers | 30,944 (674) | 19,796 (365) | 16,355 (365) |
| option-type groups (B7b-1e) | 30,842 (776) | 19,666 (495) | 16,622 (98) |
| pair-list groups (B7b-1c) | | | 16,535 (185) |

Could not be removed alone (the generator reports an unresolved conflict; the family holds up a precedence or a
declared conflict of a neighbour): `preproc_split_if*` alone, the expression tail, the operand prefix, the ternary,
`_empty_value_conditional`, `_value_decoration`, the generic value run, `preproc_conditional_case*`, all value-run
families at once.

Read with A.2: the flat AL grammar is about 3,000 states. The `#if` constructs are 82% of the tip. They are
expensive less for their own rules than for where they END: a construct that ends at `#endif` with no terminator of
its own takes its host's follow set, and is copied per host.

### A.5 What is still unexplained on the tip

16,720 states against a floor near 7,300 cores. The tip's log: external tokens 69,985 root events
(`continue_as_identifier` 36,330, `property_name` 16,566, `preproc_open` 8,233, `begin_keyword` 7,739), lexical
conflicts 12,828 (`assignment_operator` against `-` 7,777; `fieldelement` against `field` 1,903; `actions` against
`action` 1,427; `=` against `filter_operator` 384). Internalizing the four statement-start externals together saves
30 states, so the pairs they are named for are also separated by a later reason the log does not print.
`property_name` is different: it is the first token of a property, so it is in the follow set of everything that
can precede one, and D.1 is about it.

## B. Reductions measured and built

All three are committed on `state-review/candidates`, in this order. The diffs are the commits.

### C1. `#endif` is a grammar regex; the depth decrement moves to a zero-width mark (`3424755b`)

```js
// externals[3]
$._endif_mark,      // was $.preproc_close
// rules
preproc_close: $ => new RustRegex('(?i)#[ \\t]*endif'),
preproc_endif: $ => seq($.preproc_close, $._endif_mark),
```

`src/scanner.c`: `PREPROC_CLOSE` becomes `ENDIF_MARK` (same index). A new first block after the recovery guard
returns the zero-width mark whenever it is valid and decrements `depth` there. In the `#` dispatch `#endif` is
handled as `#else` is: a malformed line is `MALFORMED_DIRECTIVE`, a well-formed one is declined to the regex.

Why a mark and not just the regex: scanner state is saved only with a returned token, and `depth` is read by the
split-token tests and by `var_name_list_follows`. The mark is valid only in the one state right after the regex,
so it is in no follow set.

- **31,618 -> 20,161 STATE (-11,457, -36.2%)**, LARGE 10,133 -> 6,405, `parser.c` 70,306,929 -> 44,917,168 B.
  SYMBOL_COUNT +1. Declared conflicts unchanged.
- `node-types.json`: byte-identical. The tree is `(preproc_endif (preproc_close))` as before.
- tree-harness: BC.History 15,358, DC 1,352, BC28.1 16,928 byte-identical. BCApps-29.0: 1 of 36,716 differs,
  `src/Apps/DE/EDocumentDE/app/src/EDocumentServiceDE.PageExt.al`. It ERRORs on main (deferred item 10) and still
  does; only its recovery tree changed.
- `has_error_sweep.py`, four corpora: clean=70,353, visible=2, hidden-only=0. Same on main (the two files are the
  one above and `ERMPurchaseReportsIII.Codeunit.al`).
- Corpus-case inputs, complete cursor trees (anonymous tokens, fields, spans) main against C1
  (`scratchpad/sr/fixdiff.py`): 0 inputs that are clean on either side differ; 314 already-erroring inputs recover
  differently.
- `tree-sitter test`: 3,802 of 3,823 pass. **21 fail**, all pinned recovery trees (list below).
- `pytest tools/config_oracle/tests`: 2,612 passed.
- Conflicts and forking: no conflict added or removed. Speed was measured on the tip only (Combined, below).
- Behaviour change on invalid input: during error recovery `#endif` is now a token the lexer can produce, so
  recovery can resynchronise on it. In the changed fixtures the directive shows up as `(preproc_close)` inside the
  ERROR where it was `(UNEXPECTED 'i')` plus stray identifiers. A `#endif` with trailing text where no `#endif` is
  valid is now a `MALFORMED_DIRECTIVE` line instead of an unlexable `#`; an ERROR both ways.

### C2. The right of `is` / `as` is a name-like type (`be84fb74`) — a correctness fix that cuts states

```js
_type_right: $ => choice(
  alias($._dangling_type, $.type_specification),   // was $.type_specification
  alias($._type_operand_group, $.preproc_conditional_operand),
),
```

`_dangling_type` is the rule the typed `#if` arms already use: no option, array, `List` or `Dictionary` type. With
the full `type_specification`, every expression context carried the whole type grammar, including option member
lists and their `#if` groups (`_option_type_group_w` sat in 702 states on main).

alc 18.0.41 (`tools/alc_probe/cases/is-as-type/`, `--check` green): `I is IFoo` and `I as IFoo` are accepted;
`I is array[2] of Integer`, `I is Option A,B`, `I is List of [Integer]`, `I is Dictionary of [Integer, Text]` and
the same four after `as` are AL0104. main parses all eight clean. With C2 exactly those eight ERROR. (alc also
rejects `is Record P`, `is Codeunit P`, `is Interface IFoo` with AL0111 and `is Integer`, `is Text[30]`, a bare
`is Option` with the semantic AL0185; C2 still parses those, so an over-acceptance remains.)

- **On top of C1: 20,161 -> 18,898 (-1,263)**, LARGE 6,405 -> 5,741, `parser.c` -> 41,341,306 B.
  **Alone on main: 31,618 -> 29,774 (-1,844)**, `parser.c` 64,793,755 B (generate only).
- `node-types.json`: byte-identical.
- tree-harness against the main snapshots: BC.History, DC, BC28.1 byte-identical; BCApps only the C1 file.
- New fixture `test/corpus/is_as_type_right_negative_test.txt`: 4 `:error` cases, clean on main (red), ERROR with
  C2 (green); listed in `tools/deliberate-negatives.txt`. Suite 3,823 -> 3,827 cases.
- `tree-sitter test`: C1's 21 plus one more pinned recovery tree, "TableRelation keying negative: integer target
  with where (AL0107)" (a `(filter_operator)` moves inside the ERROR).
- This is not a zero-behaviour-change reduction: it changes what is accepted. It is listed here because no tree of
  a valid input changes.

### C3. `end` is a grammar token (`443d4fe3`, tip of the branch)

```js
// externals[5]: a never-valid placeholder, so the scanner enum keeps its numbering
$._end_unused,                       // was $.end_keyword
// rules
end_keyword: $ => kw('end'),         // a childless leaf, as the external token was
// reserved
statement_names: $ => [ ...code_names, $.end_keyword ],
_expression_statement: $ => reserved('statement_names', choice(...)),   // was 'code_names'
_assign_target:        $ => reserved('statement_names', choice(...)),   // was 'code_names'
```

`src/scanner.c`: the scanner still gives `PREPROC_SPLIT_END` first refusal (it runs before the lexer) and no longer
returns `END_KEYWORD`. The issue #40/#41 check (`end` read as a name where a statement starts) was
`BEGIN valid && !END valid`; the scanner can no longer see whether `end` is valid, so the grammar does it with a
reserved word at the two statement-start rules. One case is left to the scanner: the next declaration of a var
section (`var A: Integer; End: Integer;`, AL0519), the only state that offers `BEGIN_KEYWORD` and
`VAR_ATTRIBUTE_OPEN` together.

- **On top of C1+C2: 18,898 -> 16,720 (-2,178)**, LARGE 5,741 -> 4,609, `parser.c` -> 34,606,030 B.
  Alone on main (*proxy*): 28,512 (-3,106).
- `node-types.json`: byte-identical.
- tree-harness against the main snapshots: BC.History, DC, BC28.1 byte-identical; BCApps only the C1 file.
- `has_error_sweep.py`, four corpora: clean=70,353 visible=2 hidden-only=0; fixtures: clean=3,325 visible=502
  hidden-only=0 (the 4 new negatives).
- Corpus-case inputs, complete trees main against the tip: the only inputs clean on either side that differ are
  C2's four new negatives; 323 erroring inputs recover differently.
- `tree-sitter test`: 3,799 of 3,827; the 22 above plus 6 more pinned recovery trees.
- `pytest tools/config_oracle/tests` on the tip: exit 0, 2,612 passed.
- Fifteen `end`-as-a-name probes, main against C3 (`scratchpad/sr/endprobes/`): `A := End;`, `T(End);`,
  `R.End();`, a parameter named `End`, a quoted `"End"`, a split `end;` in both arms: same trees. `End := 1;`,
  a second variable named `End`, an `end` in a statement arm: ERROR on both. Five inputs that ERROR on both
  recover differently (`if C then` / `else` / `while .. do` / `case .. of 1:` / `repeat` directly before `end`).
- Before the var-section check was added, `var A: Integer; End: Integer;` parsed clean (ERROR on main). That is the
  kind of regression this change can make; I found one and there may be another I did not probe.
- Loose end: the placeholder external. A clean version deletes `externals[5]` and renumbers the scanner enum
  (6..20 move down by one) and the three guards.

### The 28 pinned recovery trees that fail at the tip

Every one is an input that ERRORs on main and at the tip. Fail from C1 (21): the eleven `#elsex` / `#elsewhere` /
`#elifx` / `#endif;` / `#endif X` / `#endif /* c */` / `#else B` / `#else /* c */` / `#else;` / `#elif A /* c */` /
`#elif A #region R` negatives; "`#` then a bare LF then `if`"; "B7 gap: assignment continued with the semicolon
inside every arm"; "B4 negative: a keyed whole-value #if arm holding a comparison"; "B11 negative: TableRelation
all-empty value"; six "B13 gap" cases (RunObject, `Format`, decimal range, SourceTableView, Caption, generic two
groups). From C2 (1): "TableRelation keying negative: integer target with where". From C3 (6): `#xendif` control,
`#endifx`, `#iendif`, `#ifendif`, "`#regionX` inside a member expression", "A BOM glued to the END of a keyword".
In `#iendif` the line is still an ERROR and still no `preproc_close`; the `end` after it is now an `(end_keyword)`
where it was a `call_statement` named `end`.

Landing them means regenerating each expectation from the CLI and reading each diff, or moving these cases to the
`:error` attribute as the `b7_gap_*` witnesses already are.

### Combined

C1 + C2 + C3 at the branch tip, against main: **STATE 31,618 -> 16,720 (-14,898, -47.1%); LARGE 10,133 -> 4,609;
`parser.c` 70,306,929 -> 34,606,030 B (-50.8%)**; SYMBOL_COUNT +2; grammar.js +31 lines; declared conflicts
unchanged. Item 72 (GitHub's 100 MB limit) moves from 67 MiB to 33 MiB. The compiled library
(`tree-sitter build`) goes from 31,939,936 to 14,912,864 bytes.

Gates run on the tip, main's library against the tip's (both from `tree-sitter build`):

| gate | result |
|---|---|
| `git diff main -- src/node-types.json` | exit 0, byte-identical |
| tree-harness, four corpora against main's snapshots | BC.History, DC, BC28.1 exit 0; BCApps exit 1, the one item-10 file |
| `tools.perf delta --corpus all` (complete trees, anonymous tokens included) | exit 1: bc-history 15,358 / dc 1,352 / bc28.1 16,928 files, 0 changed; bcapps-29.0 36,716 files, 1 changed, `EDocumentServiceDE.PageExt.al`, `has_error` old True new True, not in `delta-reviewed.tsv` |
| `has_error_sweep.py`, four corpora | exit 1 as on main: clean=70,353 visible=2 hidden-only=0 |
| `has_error_sweep.py --corpus-fixtures` | exit 0: clean=3,325 visible=502 hidden-only=0 |
| `tree-sitter test` | exit 1: 3,799 of 3,827, the 28 recovery trees below |
| `pytest tools/config_oracle/tests` | exit 0: 2,612 passed |
| `tools.b7_audit census --check` | exit 0: 3,229 pairs, 0 missing, 0 stale |
| `tools/check-field-types.py` | exit 0: 129/129 |
| `tools/traversal_census.py` | exit 0: 112 entries, 0 problems |
| `tools.perf incremental --corpus dc` | exit 0 (300-file sample, incremental equals fresh) |
| `tools.perf ab --corpus dc --rounds 8` (load average 4 to 6) | exit 0: identical complete trees on 1,352 files; time main / time tip median 0.992 (min 0.944, max 1.008, within-run CI 0.971-1.006). The tool's own verdict: -0.8% is below its resolution at 8 rounds. No speed change shown either way. |

## C. Attempts that did not land

Each is the edit that was tried, not a limit of the grammar.

| edit | result |
|---|---|
| D1's C4 on the tip: hidden `_case_branch_tail = seq(_case_body_branch, optional(seq(repeat(caseEmptyGroup), ';')))` in `case_branch`, `preproc_split_case_branch`, `preproc_split_case_extended` | unresolved conflict at `_case_body_branch • #if`. With `[$._case_branch_tail]` declared: 16,720 -> 16,637 (-83). A self-conflict at every case branch for 83 states: not built. |
| *proxy* `begin_keyword` as a regex | +546 on main, -81 on the tip. Not worth the scanner change. |
| *proxy* `preproc_open` as a regex | -26 on main, -264 on the tip. `depth++` would need a mark as in C1, and `_preproc_open_before_else` must stay external. Possible; small. |
| *proxy* `continue_as_identifier`, `property_name`, split tokens, `var_attribute_open`, negative literals as regexes | A.3: nothing, or worse. |
| *proxy* one unfielded `_region_root` for the eleven fielded `_region_root_*` rules | unresolved conflict at `[ operand • #if` (list element against region root). Fields would be lost anyway. |
| *proxy* a statement always ends in `;` (`seq(_statement_inner, ';')`) | tip 16,720 -> 15,928 (-792); on C1+C2 18,898 -> 17,157. It rejects a last statement without `;`, so it is only a measure of what `optional(';')` costs: every statement-start token is in the follow set of every expression in a statement. See D.4. |
| *proxy* a zero-width end mark after `_property_with_terminator_in_if` / `_property_whole_value_in_if` | tip 16,720 -> 15,198 (**-1,522**), no conflict asked for. Not built: with a greedy mark the reading "the run continues with the next `#if`" dies. See D.1. |
| stubbing a family with dummy tokens (D1's first method) | unresolved conflicts for most `#if` families; replaced by removal (A.4). |

## D. Refactor designs, ranked by saving against risk

The bar for each: no tree the parser gets right today is lost. C1 to C3 show the largest savings need no tree
change at all, so most of what follows is a minor-version refactor in tree terms; I mark where a tree or the
accepted language would change.

### D.0 A rule for every future token: nothing external in a follow set

Not a refactor, the lesson of C1/C3 written as a gate. An external token may open a construct or sit inside one. If
it can FOLLOW a construct (close it, separate it, start the next sibling), it is in that construct's follow set,
and every host whose follow set lacks it gets its own copy of the construct. Where the scanner is needed for a side
effect, use a regex plus a zero-width mark right after it (C1). Where it is needed for a decision, try a reserved
word (C3). A cheap gate: `tree-sitter generate --log` piped through `splitlog.py`, failing when "external token X"
appears for a token not on an allow-list. Whether the last batch's +2,343 was this effect was not measured; on the
tip the same rules cost what A.4 lists.

### D.1 Close open-ended `#if` constructs with a zero-width end mark (*proxy* -1,522 for the first site)

**Problem.** `Caption = #if X 'A'; #else 'B'; #endif` ends at `#endif`. Nothing of its own closes it, so the whole
value-run machinery under it (arms, tails, groups, sequences) carries the host's follow set, and the first token of
the next sibling is often `property_name`, an external token. Cost on the tip: 2,308 states for two rules.

**Design.** A hidden zero-width external `_value_end` closes the no-`;` form:
`_property_with_terminator_in_if: seq(<today's body>, $._value_end)`. The scanner returns it whenever it is valid
and the next token is not `;`. The machinery's lookahead is then `;` or the mark at every host.

**The hard part, and why this is a design and not a commit.** After a NON-terminated group a `#if` may follow, and
today GLR keeps two readings: the run continues, or the property ended and the `#if` is host content. One state
holds both, so one token must serve both. Two ways:
1. the scanner returns a second mark, `_value_end_before_if`, when a `#if` follows; both readings take it first
   (the sequence step, the decorations after a value, and the ended property), and GLR forks after it as today; or
2. the ended reading is written as a hidden pair in the host, `seq(alias(<body>, $.property), <host #if element>)`,
   whose follow is `#if` in every host. The children are siblings in the host, so the tree is today's. This needs
   the `#if`-led alternatives of `_body_element`, `_action_element` and `assembly_body` named as one hidden choice
   each.

I would prototype 2 first: it adds no scanner decision. Measure it against the -1,522 proxy; the pair costs some
of it back.

**Tree and consumers.** Unchanged by intent: hidden token, same nodes. Gate: the four-corpus harness and the B11
fixtures. **Risks.** A hidden zero-width token that is missing is the `hidden-only` class
(`has_error_sweep.py` is the gate); two zero-width tokens in a row (`_endif_mark`, then this) rely on the first
changing scanner state; incremental reparse must be checked (item 63 is in this area).
**Deferred items.** Helps none directly. Makes item 48 (an orphan `;` around empty groups) and item 90 (`;` group
after a keyed pair list) easier to reason about, because "the site has ended" becomes a token.

**Where else the same shape occurs** (candidates for the same mark, cost from A.4): the option type's trailing
member list (`Option A, B #if ..` ends wherever the type's host ends: variable, parameter, return type; 98 states
left on the tip, it was 776 on main); the split preamble and nested header groups before a shared body (745 and
952); `preproc_conditional_statement` and the empty statement groups (854, 805), which end a statement with no `;`.

### D.2 One split-header rule instead of four (procedure / trigger, header / preamble) — tree-shape change, major

**Problem.** `preproc_split_procedure` (arms are headers, then `_procedure_tail`) and
`preproc_split_procedure_preamble` (arms are header plus var section, then a `code_block`) read the same
`#if procedure P(...)` prefix as two rules, each with its own nested-group rule (`preproc_conditional_procedure_header`,
`_preamble`), and the trigger pair repeats it. Their arm rules had to be inlined ("a wrapper reduction would
conflict with `_procedure_preamble` at `#elif`"). The family is 1,295 states on the tip; the last batch added
1,110 of them (items 82, 83, 85).

**Design.** One rule: `preproc_split_routine: #if arm (#elif arm)* [#else arm] #endif tail`, where an arm is
`[attributes] header [var region]` or a nested group of arms, and the tail is today's `_procedure_tail` (which
already allows a var section and a body). Whether an arm had a var section is visible as a child, not as a
different node type. One nested-group node type.

**Tree and consumers.** Breaking: `preproc_split_procedure_preamble`, `preproc_split_trigger_preamble`,
`preproc_conditional_procedure_preamble`, `preproc_conditional_trigger_preamble` disappear into two node types.
al-sem selects an arm and reads the header; with one rule it has one code path where it has two. The oracle's
lowering (`tools/config_oracle/lowering`) loses a module's worth of cases; item 94 (the oracle does not lower a
flat split preamble) goes away with the node.
**Estimated saving.** Up to 745 (the preamble rules' cost) of the 1,295; *not prototyped*. The risk is the var
section: a var section in an arm AND after `#endif` must stay rejected or be defined.
**Deferred items.** Fixes the shape behind item 95 (first arm without a var section, a later arm with one) and
item 96 (a split preamble followed by a split body), which exist because the two rules cannot hand over to each
other.

### D.3 Statement splits: fewer, wider units — no tree change intended

The split statement rules cost 2,943 states on the tip (7,045 on main, so C1/C3 already took most). D1 showed what
works here: complete units ending at a hard terminator. Left from D1 and still valid: C5's `_case_head` (-19, no
conflict). C4 is measured above and is not worth its fork. I did not find a new unit in this family; after C1 the
remaining cost is the item sets themselves (thirteen rules that each spell `#if stmts* if C then ...`), and the
real lever is to stop adding one rule per tear shape. A generic "an arm may leave N blocks open, the tail closes
them" rule was measured at +2,540 states in its recursive form (`_open_prefix` comment); that number is from
before C1 and should be re-measured, because most of it was cloning.

### D.4 A statement list with a real separator — changes the accepted language

`_statement` is `seq(_statement_inner, optional(';'))`, so `A := 1 B := 2` parses and every statement-start token
is in the follow set of every expression that ends a statement. The *proxy* (mandatory `;`) is -792 on the tip.
A real version is `stmt (';' stmt)* [';']` with the `#if` routes of B7b-3 reworked on top; alc rejects the
separator-less form (AL0111), so it would remove an over-acceptance. It reopens B7b-3, the largest terminator
design in the repo, for under 5% of the tip. Not recommended on its own; worth doing only together with a reason
on the correctness side (item 74's `else` after a `;` that one arm supplies lives here).

### D.5 Value runs: one machinery for all families — not recommended as designed before

The six keyed families cost 356 to 671 states each, 3,085 together on the tip (the generic family could not be
removed alone). D1 tried to merge ML and Namespaces and failed at
generate (`ENU='x'` is both pair kinds), and merging over-accepts. I did not find a way to share the run automaton
across families without sharing the value language. D.1 attacks the same cost from the other side (the machinery
is copied per HOST more than per family), so do D.1 first and re-measure A.4's value-run rows.

### Ranking

| | saving | tree change | risk |
|---|---|---|---|
| C1 + C3 (built) | -13,635 with C2's 1,263 excluded | none on valid input | 28 pinned recovery trees; a hidden zero-width token; `end` reserved at statement starts |
| D.1 end marks | about -1,500 at the property site (*proxy*), more at four other sites | none intended | the continue-or-end fork after a non-terminated group |
| D.2 one split-routine rule | up to -745 (*upper bound*) | major | var-section placement; consumers migrate four node types |
| D.4 statement separator | about -800 (*proxy*) | none; language narrows | reopens B7b-3 |
| D.3, D.5 | not established | | |

Migration order: C1, then C3 (each alone, each with its recovery fixtures decided), C2 whenever the owner accepts
the narrowing; then the D.0 gate so the next batch cannot re-add an external follower; then D.1 route 2 as a
prototype; D.2 with the next major.

## E. Not measured, not done

- **Speed is measured once, on DC, at 8 rounds, on the tip only** (table in B). The host's load average was 25 to
  290 for most of the session and 4 to 6 during that run. Not measured: BC.History, 24 rounds, a second
  independent run, each candidate alone, the wasm build. C3 moves the #40/#41 kill from the scanner to a reserved
  word; the fixtures for those issues pass, and the pathological-fork probe
  (`tools/perf/strict_lists_scaling.py`) was not run.
- **Incremental against fresh** ran on DC only (300-file sample). C1 adds a zero-width external token; the other
  three corpora are the ones not checked.
- **The full and resolve oracle tiers, `b7_audit assert` / `run`, `validate-grammar.sh`, `qc`, the wasm build.**
  The B7a census, the field-type invariants and the traversal census pass on the tip.
- **The gates in B's table ran on the tip.** C1 alone had the harness, both sweeps, the fixture comparison and the
  oracle tests; C2 alone had the harness and the suite.
- **`tree-sitter test` is red at every commit of the branch** (21, 22, 28 pinned recovery trees). No `-u` was run.
- **The rule files still describe the old tokens.** `.claude/rules/scanner.md` (the token table, the scan order,
  the `#` dispatch), `.claude/rules/contextual-keywords.md` ("begin/end are scanner tokens"),
  `docs/scanner-design-notes.md` and CLAUDE.md's "`begin`/`end` are scanner-exclusive" were not updated, and no
  CHANGELOG entry was written.
- **C3 alone on main and C2+C3 without C1** were not built; C3's alone number is a proxy.
- **What separates the remaining clones on the tip** (A.5). The log gives the first reason only. The next
  instrument is a generator patched to print every reason for a pair, or to count states with a token class
  exempted; the 0.27.0 source of `tree-sitter-generate` is public and builds with cargo.
- **alc** was asked only about is/as (16 probes). The `end` probes were parsed with main and C3, not compiled.
- **CLI 0.27.2** (item 71): every number is from 0.27.0.
- D.2, D.3 and D.5 have no prototype. D.1's and D.4's numbers are proxies that lose inputs the grammar parses
  today.
- Scratch tools are in `/tmp/claude-1000/-work-tsal-wt-main/97b0c583-7d25-4579-bc56-6dcc8d248d3a/scratchpad/sr/`
  (`splitlog.py`, `dumpall.sh` + `digest.py` + `analyze.py`, `prune.py`, `internalize.py`, `fixdiff.py`,
  `gates.sh`); none is committed.
