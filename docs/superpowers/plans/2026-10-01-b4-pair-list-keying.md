# B4 name-keyed pair-list properties: implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task by task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** a one-pair value of the 13 compiler ML properties, and of `Namespaces`, parses as a
pair list instead of a comparison, matching alc 18.0.41.

**Architecture:**
- The external scanner's single-read identifier dispatch emits two new tokens,
  `ML_PROPERTY_NAME` and `NAMESPACES_PROPERTY_NAME`, for the compiler's names, the way it
  emits `CALC_FORMULA_PROPERTY_NAME` today.
- `property` gets one arm per family whose value is that family's list or a keyed whole-value
  `#if`.
- `Namespaces` gets its own `namespace_value_list` and `namespace_pair` nodes.
- `ml_value_list` loses its `Locked = <boolean>` tail, which alc rejects.

**Tech stack:**
- tree-sitter 0.27 grammar DSL (`grammar.js`) and its C external scanner (`src/scanner.c`).
- Corpus fixtures (`test/corpus/`).
- pytest under `tools/config_oracle/tests` and `tests/`.
- `tools.alc_probe` and `tools/config_oracle/probe_alc.py` for compiler evidence.

**Spec:** `docs/superpowers/specs/2026-10-01-pair-list-property-keying-design.md` (approved
2026-10-01). Read it before any task. Section numbers below (§) refer to it.

## Global constraints

- **Rules files bind every task:** CLAUDE.md, `.claude/rules/*.md` and
  `docs/agent-brief-rules.md`.
- **Git Bash with Windows paths.** Never `2>nul`. Run `tree-sitter` only through
  `./tools/ts-lock.sh`. `python -m tools.perf ab` takes the lock itself, so do not wrap it.
- **Branch:** `fix/b4-pair-list-keying`, off main at `db7e291`. Do not push.
- **Forbidden commands:**
  - `git stash`, `git reset --hard`, `git checkout --`, `git restore`, `git clean -f`.
  - `find /`, or any search outside the repo, the scratchpad or the four corpus roots.
  - `tail -f | grep` watchers.
- **Generated files:** commit `grammar.js`, `src/parser.c`, `src/grammar.json` and
  `src/node-types.json` together, plus `src/scanner.c` when it changed.
- **Commit messages:** every message ends with `[BC.History: N errors, X% success]`,
  measured, not copied.
- **The keyed family is exactly** these 13 ML names: AboutTextML, AboutTitleML,
  AdditionalSearchTermsML, CaptionML, EntityCaptionML, EntitySetCaptionML,
  InstructionalTextML, OptionCaptionML, ProfileDescriptionML, PromotedActionCategoriesML,
  RequestFilterHeadingML, SummaryML, ToolTipML. Plus `Namespaces`. Match them
  case-insensitively, whole word only.
- **Hard limits on the change:**
  - BC.History trees may change ONLY in the 6 `Namespaces` files.
  - STATE_COUNT growth ≤ 2% over `db7e291`.
  - No new declared conflicts unless necessary, and each one must be explained in a comment.
- **`-u` traps:** after any `tree-sitter test -u`, run `git diff --stat test/corpus`.
  Restore untargeted files with `git show HEAD:path > path`.
- **Report** as text, because report files are blocked. Do not dispatch subagents.
- **Scratchpad** (`$SCRATCH` in the commands below; set it first with `SCRATCH=<that path>`):
  `C:/Users/SShadowS/AppData/Local/Temp/claude/U--Git-tree-sitter-al/2c3b5bda-3840-41dc-8b36-f953b380f9a7/scratchpad`.

## Review focus

1. **A parse state that offers `PROPERTY_NAME` but not the keyed token.** A keyed name there
   silently takes the generic comparison path. Pinned in Task 2 Step 8, which audits
   `ts_external_scanner_states` and adds one host fixture per documented host class.
2. **Edits that turn a keyed name into an unknown one, or back.** The incremental tree must
   equal a fresh parse. Task 4.
3. **An unknown `…ML` name, or a keyed name with a suffix** (`FooML`, `CaptionMLX`). It must
   keep today's tree. Task 2, regression fixtures.
4. **A malformed keyed value.** It must ERROR visibly, and never become a clean second
   property or a comparison. Task 2 and Task 3 negatives, including the InstructionalTextML
   `;` form.
5. **A whole-value `#if` with a one-pair arm and `;` after `#endif`.** That is the oracle's
   strict xfail, and it must flip to a pass. Task 3.

---

### Task 1: setup, baselines and compiler evidence

**Files:**
- Create: `tools/alc_probe/cases/pair-list-keying/*.al` (one file per §2.3 row)
- Modify: `tools/config_oracle/probe_alc.py` (raw cases for every negative)

**Interfaces:**
- Produces:
  - the snapshot `.snapshots/baseline-b4`;
  - the base library copy `$SCRATCH/al_base.dll`;
  - probe names, used by Tasks 2 and 3 as `evidence: probe_alc <name>`:
    - `ml_locked_true_rejected`, `textconst_locked_true_rejected`, `namespaces_locked_true_rejected`;
    - `ml_trailing_comma_rejected`, `ml_missing_comma_rejected`;
    - `ml_string_value_rejected`, `ml_identifier_value_rejected`;
    - `textconst_maxlength_rejected`, `instructionaltextml_semicolon_rejected`, `tooltipml_unquoted_rejected`.

- [ ] **Step 1: Branch and baselines**

```bash
cd U:/Git/tree-sitter-al
git checkout -b fix/b4-pair-list-keying
./tools/ts-lock.sh ./tools/tree-harness.sh snapshot ./BC.History .snapshots/baseline-b4
./tools/metrics.sh > "$SCRATCH/metrics-base.txt"; cat "$SCRATCH/metrics-base.txt"
./tools/ts-lock.sh tree-sitter build -o "$SCRATCH/al_base.dll"
```

Expected: the snapshot reports 15,358 files, `metrics-base.txt` shows STATE_COUNT=15973, and
`$SCRATCH/al_base.dll` exists.

- [ ] **Step 2: Write the alc_probe cases.** Write one file per row of spec §2.3, using the
  header format from `tools/alc_probe/README.md`. Example,
  `tools/alc_probe/cases/pair-list-keying/ml-one-pair.al`:

```al
// One-pair CaptionML: alc reads the value as a pair list (G9, B4).
// source: docs/superpowers/specs/2026-10-01-pair-list-property-keying-design.md §2.3
// expect: * accept
table 50100 T
{
    CaptionML = ENU='c';
    fields { field(1; F; Integer) { } }
}
```

  The rejecting rows use `// expect: * reject(AL0104,AL0219)`, with that row's codes from
  §2.3. For the RequestFilterHeadingML docs example, declare the table in the same file so
  the case stays self-contained:

```al
// Microsoft Learn's RequestFilterHeadingML example, one pair, with a trailing comment.
// source: learn.microsoft.com .../devenv-requestfilterheadingml-property
// expect: * accept
table 50101 T { fields { field(1; F; Integer) { } } }
report 50100 R
{
    dataset { dataitem(D; T) { RequestFilterHeadingML = DAN='Kundeliste'; // Customer list
    } }
}
```

- [ ] **Step 3: Run the cases and pin them**

Run: `python -m tools.alc_probe run tools/alc_probe/cases/pair-list-keying --check`
Expected: exit 0, with every case matching its `expect`. A drift means the matrix in §2.3 is
wrong. Stop and report; do not edit `expect` to make it pass.

- [ ] **Step 4: Add `probe_alc.py` raw cases** for the ten negative names in the Interfaces
  block, in the existing case-list style, with the recorded codes from §2.3.

Run: `python -m tools.config_oracle.probe_alc --check`
Expected: exit 0, and the case count grows by 10.

- [ ] **Step 5: Commit**

```bash
git add tools/alc_probe/cases/pair-list-keying tools/config_oracle/probe_alc.py
git commit -m "test(alc): B4 pair-list keying evidence -- alc 18.0.41 accept/reject matrix

[BC.History: 0 errors, 100% success]"
```

---

### Task 2: scanner keying, the flat property arms and the node shapes

**Files:**
- Modify: `src/scanner.c`:
  - the `TokenType` enum (`:14-30`);
  - the `IdentifierWord` enum and `read_identifier_word` (`:274-312`);
  - the recovery guard (`:534-546`);
  - the identifier-dispatch guard (`:927-929`);
  - the `=` emission branch (`:1001-1028`).
- Modify: `grammar.js`:
  - `externals` (`:192-209`);
  - `property` (`:793-826`);
  - `ml_value_list` (`:1166-1170`);
  - a new `namespace_value_list` and `namespace_pair` next to it.
- Modify: `tools/check-field-types.py`
- Create:
  - `test/corpus/pair_list_property_keying_test.txt`
  - `test/corpus/pair_list_property_keying_negative_test.txt`
- Modify:
  - `tools/deliberate-negatives.txt`
  - `tools/config_oracle/fixture-classes.tsv`, only if the quick tier asks for it

**Interfaces:**
- Consumes: Task 1 probe names.
- Produces, used by Task 3:
  - the grammar symbols `$._ml_property_name` and `$._namespaces_property_name`
    (externals [15] and [16]);
  - the node types `namespace_value_list` and `namespace_pair` (fields `prefix`, `uri`);
  - the hidden rules `_ml_property_value` and `_namespaces_property_value`. In this task each
    is just its list; Task 3 adds the conditional alternative.

- [ ] **Step 1: Write the failing positive fixture.** Create
  `test/corpus/pair_list_property_keying_test.txt`. Write the expected trees by hand, WITH
  field labels (CLAUDE.md trap 2). Cases:

  **One pair:** one per ML name, each in a documented host from spec §2.2. Use:
  - CaptionML on a table field, page action, enum value, profile, permission set, page view
    and query column;
  - ToolTipML on a page field;
  - OptionCaptionML on a table field;
  - InstructionalTextML on a page;
  - PromotedActionCategoriesML on a page;
  - AboutTextML and AboutTitleML on a page action;
  - AdditionalSearchTermsML on a report;
  - EntityCaptionML and EntitySetCaptionML on a query;
  - ProfileDescriptionML on a profile;
  - RequestFilterHeadingML on a report data item, the docs example verbatim;
  - SummaryML on a report layout.

  **Two pairs:** CaptionML and OptionCaptionML (the production shapes).

  **Namespaces:**
  - the docs one-pair example verbatim;
  - `"" = 'urn:a'`;
  - the six-pair production line from
    `BC.History/BaseApp/Source/Base Application/Sales/Peppol/SalesInvoicePEPPOL20.XmlPort.al:17`.

  **Name and pair forms:**
  - `captionml = ENU='c';` and `CAPTIONML = ENU='c';`;
  - `CaptionML /* c */ = ENU='c';`;
  - `CaptionML` followed by a newline, then `= ENU='c';`;
  - `CaptionML = "ENU"='a';`, `CaptionML = ENU='a', Locked='x';` and
    `CaptionML = ENU='a', Comment='x';` as pairs;
  - `CaptionML = ;` as a property with no value field.

  **Regression (today's trees, unchanged):**
  - `Visible = A = 'b';`, `FooML = A = 'b';`, `CaptionMLX = A = 'b';` and
    `ToolTipML2 = A = 'b';` all stay comparisons;
  - `FooML = A='x', B='y';` stays `ml_value_list` through the generic path;
  - `Caption = 'x', Locked = true, Comment = 'y', MaxLength = 20;` is unchanged;
  - `T: TextConst ENU='a';` and `T: TextConst ENU='a', DAN='b';` are unchanged;
  - `CalcFormula = count(T);` is unchanged.

  Expected shapes, from spec §4:

```
(property name: (property_name) "=" value: (ml_value_list
  (ml_value_pair language: (identifier) "=" value: (string_literal))) ";")
(property name: (property_name) "=" value: (namespace_value_list
  (namespace_pair prefix: (identifier) "=" uri: (string_literal))) ";")
```

- [ ] **Step 2: Run it and watch it fail**

Run: `./tools/ts-lock.sh tree-sitter test --file-name pair_list_property_keying_test.txt`
Expected: FAIL on every one-pair case (the actual tree is `comparison_expression`) and on
every `Namespaces` case (the actual tree is `ml_value_list`). The regression cases pass.

- [ ] **Step 3: Scanner.** In `src/scanner.c`:

```c
// enum TokenType -- append, never renumber
  ML_PROPERTY_NAME = 15,          // one of the 13 compiler ML names followed by =
  NAMESPACES_PROPERTY_NAME = 16,  // `Namespaces` followed by =

// enum IdentifierWord -- append after WORD_CALCFORMULA
  WORD_ML_PROPERTY,  // value grammar: CommaSeparatedIdentifierEqualsStringList (B4)
  WORD_NAMESPACES,   // same list grammar, its own node (B4)

// The compiler's pair-list property names, lowercase. Source: alc 18.0.41.62505,
// Microsoft.Dynamics.Nav.CodeAnalysis.dll, ObjectParser (PropertyTypeInfo tables keyed by
// the upper-cased name) and PropertyNameToSyntaxDefinition, read 2026-10-01. These 13 map
// to MultilanguagePropertyValueSyntax; Namespaces uses the same list parser. Never derive
// this from a suffix: `FooML` has no pair grammar in alc.
static const char *const ML_PROPERTY_NAMES[] = {
  "abouttextml", "abouttitleml", "additionalsearchtermsml", "captionml",
  "entitycaptionml", "entitysetcaptionml", "instructionaltextml", "optioncaptionml",
  "profiledescriptionml", "promotedactioncategoriesml", "requestfilterheadingml",
  "summaryml", "tooltipml",
};
```

  In `read_identifier_word`:
  - change the buffer to `char buf[32];  // longest word tested: "promotedactioncategoriesml" (26) plus the NUL`;
  - after the `calcformula` line, add:

```c
  if (len == 10 && strcmp(buf, "namespaces") == 0) return WORD_NAMESPACES;
  for (size_t i = 0; i < sizeof(ML_PROPERTY_NAMES) / sizeof(ML_PROPERTY_NAMES[0]); i++) {
    if (strcmp(buf, ML_PROPERTY_NAMES[i]) == 0) return WORD_ML_PROPERTY;
  }
```

  **Recovery guard:** add `&& valid_symbols[ML_PROPERTY_NAME] && valid_symbols[NAMESPACES_PROPERTY_NAME]`.

  **Dispatch guard** (`:927`): add `|| valid_symbols[ML_PROPERTY_NAME] || valid_symbols[NAMESPACES_PROPERTY_NAME]`.

  **Emission branch:** widen the `if (valid_symbols[PROPERTY_NAME] || …)` guard the same
  way. Replace the ternary with:

```c
        if (word == WORD_CALCFORMULA && valid_symbols[CALC_FORMULA_PROPERTY_NAME]) {
          lexer->result_symbol = CALC_FORMULA_PROPERTY_NAME;
        } else if (word == WORD_ML_PROPERTY && valid_symbols[ML_PROPERTY_NAME]) {
          lexer->result_symbol = ML_PROPERTY_NAME;
        } else if (word == WORD_NAMESPACES && valid_symbols[NAMESPACES_PROPERTY_NAME]) {
          lexer->result_symbol = NAMESPACES_PROPERTY_NAME;
        } else if (valid_symbols[PROPERTY_NAME]) {
          lexer->result_symbol = PROPERTY_NAME;  // a keyed name where the state offers only the generic token
        } else {
          return false;
        }
        return true;
```

  Keep the existing comment block above the emission branch, and extend it with one
  sentence on the two new families that cites the spec.

- [ ] **Step 4: Grammar.** In `grammar.js`:

```javascript
// externals: append after $._scanner_hook
    $._ml_property_name,        // [15] one of the 13 compiler ML names followed by = (B4)
    $._namespaces_property_name, // [16] `Namespaces` followed by = (B4)

// property: two arms after the CalcFormula arm
      seq(
        field('name', alias($._ml_property_name, $.property_name)),
        '=',
        optional(field('value', $._ml_property_value)),
        ';'
      ),
      seq(
        field('name', alias($._namespaces_property_name, $.property_name)),
        '=',
        optional(field('value', $._namespaces_property_value)),
        ';'
      ),

    _ml_property_value: $ => $.ml_value_list,
    _namespaces_property_value: $ => $.namespace_value_list,

    ml_value_list: $ => prec.right(seq(
      $.ml_value_pair,
      repeat(seq(',', $.ml_value_pair)),
    )),

    namespace_value_list: $ => prec.right(seq(
      $.namespace_pair,
      repeat(seq(',', $.namespace_pair)),
    )),

    namespace_pair: $ => seq(
      field('prefix', $._plain_name),
      '=',
      field('uri', $.string_literal)
    ),
```

  Write a comment above the new `property` arms that gives the reason in three sentences:
  name-keyed like CalcFormula, the one-pair ambiguity, and the compiler source. Write a
  comment at `ml_value_list` saying the `Locked = <boolean>` tail was removed because alc
  rejects it with AL0219 in all three hosts and 0 corpus files use it.

  `namespace_value_list` must NOT be added to `_property_value`.

- [ ] **Step 5: Generate and run the fixture**

```bash
./tools/ts-lock.sh tree-sitter generate 2>&1 | tail -5
./tools/ts-lock.sh tree-sitter test --file-name pair_list_property_keying_test.txt
```

Expected: generation reports no new conflicts, and every case passes. If a case fails, read
the actual tree. Never `-u` it into passing without tracing the hunk.

- [ ] **Step 6: Prove the fixture can fail.** Rename one `prefix:` to `bogus:` and one
  `language:` to `bogus:`, run Step 5's test, see FAIL, then revert both renames.

- [ ] **Step 7: Negative fixture.** Create
  `test/corpus/pair_list_property_keying_negative_test.txt` with one case per negative probe
  from Task 1:
  - Locked true in ML, in TextConst and in Namespaces;
  - a trailing comma; a missing comma;
  - `CaptionML = 'abc';` and `CaptionML = ENU=Foo;`;
  - TextConst `MaxLength = 5`;
  - `InstructionalTextML = ENU='a'; ESP='b';`;
  - `ToolTipML = DAN=Dette felt;`.

  Write each expected tree by hand, as it really comes out, with the ERROR on the offending
  line. Add the file name to `tools/deliberate-negatives.txt`, with a comment that cites the
  Task 1 probe names.

  Then run:
  - `./tools/ts-lock.sh tree-sitter test --file-name pair_list_property_keying_negative_test.txt`
    (PASS);
  - `python tools/has_error_sweep.py --corpus-fixtures` (exit 0: negatives may be visible,
    never hidden).

- [ ] **Step 8: The host audit (Review focus 1).**

```bash
grep -n "ts_external_scanner_states" -A60 src/parser.c | head -90
```

  For each external-scanner state row, record two things:
  - whether it has `property_name` without `_ml_property_name`;
  - which grammar host owns it. Map the state back with
    `tree-sitter generate --report-states-for-rule property`, or by elimination.

  Every such host must be one where no ML or `Namespaces` property can appear. Examples:
  the `caption_value` sub-fields (`grammar.js:1154`), `permissions_property` (`:834`), and
  `_permissions_head` (`:863`).

  List the result in a comment in the fixture file header. If a real property host lacks the
  keyed token, give it the keyed arms. Do not paper over it.

- [ ] **Step 9: Field contract.** Add `inv(...)` rows to `tools/check-field-types.py` in the
  existing style:
  - `namespace_pair.prefix` (multiple False, `anon=set()`, types `identifier`/`quoted_identifier`);
  - `namespace_pair.uri` (types `{'string_literal'}`);
  - `ml_value_pair.language`, pinning today's set.

  Run: `python tools/check-field-types.py`
  Expected: exit 0.

- [ ] **Step 10: Whole suite, quick validation, tree-harness**

```bash
./tools/ts-lock.sh ./validate-grammar.sh
./tools/ts-lock.sh ./tools/tree-harness.sh verify ./BC.History .snapshots/baseline-b4
```

Expected:
- `validate-grammar.sh` exits 0, and the case count equals the pre-change total plus exactly
  the cases added.
- The tree-harness delta is exactly the 6 `Namespaces` files. Read every hunk: only
  `ml_value_list` → `namespace_value_list`, `ml_value_pair` → `namespace_pair`,
  `language:` → `prefix:` and `value:` → `uri:`. Any other file changing is a STOP.

- [ ] **Step 11: Commit.** Run the full parse for the count:
  `./parse-al-parallel.sh ./BC.History/ .`.

```bash
git add src/scanner.c grammar.js src/parser.c src/grammar.json src/node-types.json \
  tools/check-field-types.py tools/deliberate-negatives.txt \
  test/corpus/pair_list_property_keying_test.txt test/corpus/pair_list_property_keying_negative_test.txt
git commit -m "fix(grammar): key the 13 ML properties and Namespaces by name (B4, G9)

[BC.History: 0 errors, 100% success]"
```

---

### Task 3: keyed whole-value `#if`, and the oracle

**Files:**
- Modify: `grammar.js`:
  - `_ml_property_value` and `_namespaces_property_value` (from Task 2);
  - new conditional rules;
  - `_property_with_terminator_in_if` (`:886`) and `_property_whole_value_in_if` (`:918`).
- Modify: `tools/config_oracle/contracts.py:466-476` (the `arm=` set of
  `preproc_conditional_property_value`).
- Modify: `tools/config_oracle/tests/test_property_value_conditional.py:151-154` (remove the
  xfail; add both families).
- Modify: `test/corpus/pair_list_property_keying_test.txt` and the negative file.
- Modify, only if the census demands it: `traversal/policy.json`.

**Interfaces:**
- Consumes: Task 2 symbols.
- Produces: no new public node types. Keyed conditionals alias to
  `preproc_conditional_property_value`.

- [ ] **Step 1: Failing tests.** Append cases to the positive fixture, both families, with
  expected trees written by hand. The public node is `preproc_conditional_property_value`,
  and each arm's `value:` is a list:

```al
    CaptionML = #if X ENU='a' #else ENU='b' #endif;              // ; after #endif
    CaptionML = #if X ENU='a'; #else ENU='b', DAN='c'; #endif    // ; in every arm
    CaptionML = #if X ENU='a' #elif Y ENU='b' #else ENU='c' #endif;
    CaptionML = #if X #if Y ENU='a' #else ENU='b' #endif #else ENU='c' #endif;
    Namespaces = #if X bc = 'urn:a' #else bc = 'urn:b' #endif;
```

  Put each directive on its own line in the fixture: AL requires that. The forms above are
  compressed only for reading here.

  Then remove the `@pytest.mark.xfail(...)` decorator from
  `test_single_pair_ml_arm_before_endif`, and add a sibling test for `Namespaces`, built
  with the existing `_whole_page` helper or an xmlport equivalent.

Run:
- `./tools/ts-lock.sh tree-sitter test --file-name pair_list_property_keying_test.txt`
- `./tools/ts-lock.sh python -m pytest tools/config_oracle/tests/test_property_value_conditional.py -q`

Expected: the new fixture cases FAIL (ERROR or comparison arms), and the un-xfailed test
FAILS.

- [ ] **Step 2: Grammar.** Add a JS helper above `module.exports`, plus four rules:

```javascript
// A keyed property's whole-value #if (B4). Same arm structure and public node as
// _property_value_conditional / _property_value_conditional_in_if, but every arm holds the
// family's own list, never _property_value, so a one-pair arm cannot become a comparison.
function keyedValueConditional($, branch) {
  return seq(
    $.preproc_if,
    optional(branch),
    repeat(seq($.preproc_elif, optional(branch))),
    optional(seq($.preproc_else, optional(branch))),
    $.preproc_endif,
  );
}
```

```javascript
    _ml_property_value: $ => choice(
      $.ml_value_list,
      alias($._ml_value_conditional, $.preproc_conditional_property_value),
    ),
    _ml_value_conditional: $ => keyedValueConditional($,
      seq(field('value', $._ml_property_value), optional(';'))),
    _ml_value_conditional_in_if: $ => keyedValueConditional($, choice(
      seq(field('value', $._ml_property_value), ';'),
      field('value', alias($._ml_value_conditional_in_if, $.preproc_conditional_property_value)),
    )),
    // _namespaces_property_value, _namespaces_value_conditional and
    // _namespaces_value_conditional_in_if: the same three rules with namespace_value_list.
```

  Write the three Namespaces rules out in full; do not leave the comment as code. Then turn
  `_property_with_terminator_in_if` and `_property_whole_value_in_if` into a
  `prec(N, choice(<existing seq>, <ML seq>, <Namespaces seq>))`, keeping their current prec,
  where the ML seq is:

```javascript
      seq(
        field('name', alias($._ml_property_name, $.property_name)),
        '=',
        field('value', alias($._ml_value_conditional_in_if, $.preproc_conditional_property_value)),
      ),
```

- [ ] **Step 3: Generate and test**

```bash
./tools/ts-lock.sh tree-sitter generate 2>&1 | tail -5
./tools/ts-lock.sh tree-sitter test --file-name pair_list_property_keying_test.txt
./tools/ts-lock.sh python -m pytest tools/config_oracle/tests/test_property_value_conditional.py -q
```

Expected: all pass. If generation reports a conflict, record the edit you tried, then
resolve it with precedence on the keyed rules. Add a declared conflict only if precedence
cannot settle it, with a comment explaining why (CLAUDE.md, "Two rules about
verification").

- [ ] **Step 4: Conditional negatives.** Add these to the negative fixture:
  - a keyed arm holding a comparison (`CaptionML = #if X A = 1 #endif;`);
  - an arm with a trailing comma.

  Both must ERROR inside the arm. Add `probe_alc` cases for both, if alc rejects them;
  probe them first.

- [ ] **Step 5: Oracle registry and census.** Add `"namespace_value_list"` to the `arm=` set
  of `register("preproc_conditional_property_value", ...)` in `contracts.py`. Then run:

```bash
python -m tools.config_oracle run --tier quick
python tools/traversal_census.py
```

Expected: both exit 0. If the census flags `namespace_value_list` or `namespace_pair`, add
`traversal/policy.json` entries with the class the census names (spec 2026-10-01 §6.1)
and a witness, then run `./tools/ts-lock.sh python -m pytest tests/traversal -q`. Any
`fixture-classes.tsv` entry the quick tier reports stale is removed. Any new unclassified
fixture record gets an entry with `evidence: probe_alc <name>`.

- [ ] **Step 6: tree-harness and commit.** Run
  `./tools/ts-lock.sh ./tools/tree-harness.sh verify ./BC.History .snapshots/baseline-b4`.
  The delta must still be exactly the 6 `Namespaces` files. Then:

```bash
git add grammar.js src/parser.c src/grammar.json src/node-types.json \
  tools/config_oracle/contracts.py tools/config_oracle/tests/test_property_value_conditional.py \
  test/corpus/pair_list_property_keying_test.txt test/corpus/pair_list_property_keying_negative_test.txt
# plus traversal/policy.json, tools/config_oracle/fixture-classes.tsv and tools/config_oracle/probe_alc.py if changed
git commit -m "fix(grammar): keyed whole-value #if for ML and Namespaces; G9 xfail passes (B4)

[BC.History: 0 errors, 100% success]"
```

---

### Task 4: incremental parsing (Review focus 2)

**Files:**
- Create: `tools/config_oracle/tests/test_pair_list_incremental.py`

**Interfaces:**
- Consumes: the `al_parser` fixture from `tools/config_oracle/tests/conftest.py`.

- [ ] **Step 1: Write the test**

```python
"""B4: incremental re-parse after an edit equals a fresh parse (spec §5.4)."""
import pytest

HOST = b"table 50100 T\n{\n    %s\n    fields { field(1; F; Integer) { } }\n}\n"

EDITS = [  # (before, after) property lines
    (b"CaptionML = ENU='c';", b"Namespaces = ENU='c';"),
    (b"CaptionML = ENU='c';", b"Visible = ENU='c';"),
    (b"CaptionML = ENU='c';", b"CaptionMLX = ENU='c';"),
    (b"Visible = ENU='c';", b"CaptionML = ENU='c';"),
    (b"CaptionML = ENU='c';", b"captionml = ENU='c';"),
    (b"CaptionML = ENU='c';", b"CaptionML := ENU='c';"),
    (b"CaptionML = ENU='c';", b"CaptionML /* c */ = ENU='c';"),
    (b"CaptionML = ENU='c';", b"CaptionML = ENU='c', DAN='d';"),
    (b"CaptionML = ENU='c';", b"CaptionML =\n#if X\n ENU='c'\n#endif\n;"),
    (b"CaptionML = ENU='c';", b"CaptionML  = ENU='c';"),  # just past the name's marked end
]


def _edit(parser, old_src, new_src):
    tree = parser.parse(old_src)
    n = min(len(old_src), len(new_src))
    prefix = next((i for i in range(n) if old_src[i] != new_src[i]), n)
    suffix = 0
    while (suffix < n - prefix
           and old_src[len(old_src) - 1 - suffix] == new_src[len(new_src) - 1 - suffix]):
        suffix += 1
    start, old_end, new_end = prefix, len(old_src) - suffix, len(new_src) - suffix

    def point(src, off):
        line = src.count(b"\n", 0, off)
        return (line, off - (src.rfind(b"\n", 0, off) + 1))
    tree.edit(start_byte=start, old_end_byte=old_end, new_end_byte=new_end,
              start_point=point(old_src, start), old_end_point=point(old_src, old_end),
              new_end_point=point(new_src, new_end))
    return parser.parse(new_src, tree)


@pytest.mark.parametrize("before,after", EDITS)
def test_incremental_equals_fresh(al_parser, before, after):
    old_src, new_src = HOST % before, HOST % after
    incremental = _edit(al_parser, old_src, new_src)
    fresh = al_parser.parse(new_src)
    assert str(incremental.root_node) == str(fresh.root_node)
    assert incremental.root_node.has_error == fresh.root_node.has_error
```

  Check `conftest.py` for the exact name of the parser fixture and use it. If
  py-tree-sitter's `Tree.edit` signature differs in the installed version, adapt the call,
  and keep the comparison.

- [ ] **Step 2: Run it.** `./tools/ts-lock.sh python -m pytest tools/config_oracle/tests/test_pair_list_incremental.py -q`
  Expected: PASS. A failure is a real incremental-reuse defect. Report it with the
  failing pair; do not weaken the assertion.

- [ ] **Step 3: Prove it can fail.** Temporarily change one `after` so the incremental
  parse uses `old_src`'s tree without calling `edit`. See FAIL, then revert.

- [ ] **Step 4: Commit**

```bash
git add tools/config_oracle/tests/test_pair_list_incremental.py
git commit -m "test(b4): incremental parse equals fresh across keyed-name edits

[BC.History: 0 errors, 100% success]"
```

---

### Task 5: gates, performance, WASM and docs

**Files:**
- Modify:
  - `CHANGELOG.md`
  - `CLAUDE.md` ("Property Handling" and the scanner token table)
  - `.claude/rules/scanner.md`
  - `queries/highlights.scm`
  - `docs/deferred-work.md` (item 11)
  - `docs/superpowers/plans/2026-09-28-roadmap-remaining-work.md` (rows B4 and B7)
  - `tree-sitter-al.wasm` and `tree-sitter-al.wasm.inputs.sha256`

- [ ] **Step 1: Size and performance**

```bash
./tools/metrics.sh --vs db7e291
./tools/ts-lock.sh tree-sitter build -o "$SCRATCH/al_b4.dll"
python -m tools.perf ab --lib-a "$SCRATCH/al_base.dll" --lib-b "$SCRATCH/al_b4.dll" --corpus dc --rounds 24
```

Expected: STATE_COUNT ≤ 15973 × 1.02 = 16292. The `ab` confidence interval must contain 1.0,
or the slowdown must be within its stated resolution. Over budget is a STOP: report the
numbers.

- [ ] **Step 2: Full gates**

```bash
./tools/ts-lock.sh ./validate-grammar.sh --full
for r in ./BC.History ./DC H:/Git/BC28.1 H:/Git/BCApps-29.0; do python tools/has_error_sweep.py --root "$r"; done
python tools/snip.py --census --root ./BC.History
python -m tools.query_coverage.qc run
./tools/ts-lock.sh python -m tools.config_oracle run --tier full --root ./BC.History --root ./DC --root H:/Git/BC28.1 --root H:/Git/BCApps-29.0
./tools/ts-lock.sh python -m pytest tests/traversal -q && npm test
cargo test --features traversal   # only if traversal/policy.json changed
```

Expected:
- `validate-grammar.sh --full` exits 0, with BC.History at 0 errors.
- The has_error sweeps show no new error files (BCApps keeps its 2 known visible files).
- The census flags 0 types, `qc` exits 0, and the oracle full tier exits 0 with 0
  discrepancies.
- The traversal suites pass.

Run the oracle full tier in the background with an `until` loop on its output file, never
`tail -f`.

- [ ] **Step 3: WASM**

```bash
./tools/ts-lock.sh tree-sitter build --wasm -o tree-sitter-al.wasm
./tools/check-wasm-fresh.sh --update
./tools/check-wasm-fresh.sh
```

Expected: the second command reports the WASM as fresh. Commit the WASM and its stamp in a commit of their own.

- [ ] **Step 4: Docs**, each edit as specified in spec §6:
  - **CHANGELOG `[Unreleased]`:** the three breaking lines.
  - **CLAUDE.md:** rewrite the CalcFormula paragraph into a "name-keyed properties" section
    covering three families, with the replacement rule quoted from spec §6. Add rows for
    `ML_PROPERTY_NAME` and `NAMESPACES_PROPERTY_NAME` to the scanner token table.
  - **`.claude/rules/scanner.md`:** the token table rows, and in the identifier-dispatch
    section the buffer (32) and the longest word (`promotedactioncategoriesml`, 26). Also
    the emission order (CalcFormula → ML → Namespaces → generic → decline).
  - **`queries/highlights.scm`:** `(namespace_pair prefix: (_) @namespace)` and
    `(namespace_pair uri: (string_literal) @string.special.url)`, next to the existing ML
    captures. Run `python -m tools.query_coverage.qc run` again: exit 0.
  - **`docs/deferred-work.md` item 11:** mark it RESOLVED with the commit hashes, and correct
    "every name ending in `ML`" to "the compiler's 13".
  - **Roadmap B4 row:** add a done note with the measured STATE_COUNT, `ab` and the
    tree-harness delta. In the B4 test list, replace "list-internal splits" with a pointer to
    B7. In B7, add "ML and Namespaces pair-list separator hosts".

- [ ] **Step 5: Commit the docs**

```bash
git add CHANGELOG.md CLAUDE.md .claude/rules/scanner.md queries/highlights.scm \
  docs/deferred-work.md docs/superpowers/plans/2026-09-28-roadmap-remaining-work.md
git commit -m "docs: B4 done -- name-keyed pair-list properties, CHANGELOG, rules, roadmap

[BC.History: 0 errors, 100% success]"
```

- [ ] **Step 6: Cleanup.** Delete `.snapshots/baseline-b4` with
  `rm -rf "${P:?}"`, where `P=.snapshots/baseline-b4`. Kill any background process you
  started (`./tools/session-cleanup.sh --procs` lists them).
