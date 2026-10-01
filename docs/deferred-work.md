# Deferred work

Open items carried past 4.0.0, with **how each one was established** so the next
person can tell a measurement from a recollection. Nothing here is a "known
limitation" in the sense the project philosophy forbids — every item is a defect
with a known shape, parked because the release shipped, not because it was judged
unfixable.

**Re-verify before acting on any of these.** They were measured against the 4.0.0
tree; several touch areas the release itself changed. An item whose probe no longer
reproduces is finished — say so and delete the entry.

---

## The instrument these items depend on

Most items below are "does the AL compiler accept this?" questions, and the answer
is only trustworthy from `al compile` (see CLAUDE.md, *Validating AL Syntax
Questions*). One extra rule applies to every `#if`-related probe:

**alc does not parse inactive branches.** A file with `#if FOO` … `#else` … `#endif`
must therefore be compiled **four** ways before a verdict means anything:

| config | what it proves |
|---|---|
| flat, symbol undefined | the else-branch text is valid on its own |
| flat, symbol defined | the then-branch text is valid on its own |
| split, symbol undefined | alc accepts the split file taking the else branch |
| split, symbol defined | alc accepts the split file taking the then branch |

`python -m tools.alc_probe run <case.al>` runs all four (all 2^n for n symbols) and
reports a broken project as `BROKEN` rather than a rejection; see item 7.
`preprocessorSymbols` in `app.json` selects the config. A single-config probe is
worthless and has already produced one false ACCEPT and one false REJECT in this
project's history — one of which reached a committed fixture before it was caught
(`ef4cc7e`). `AL1021` appears in the log of successful runs too; judge by whether
`out.app` was produced, not by the log being empty.

---

## 1. Six separator positions have no preprocessor host

**Established:** an audit that enumerated all 26 separator sites in `grammar.js`,
mapped each to its owning rule, and probed the unhosted ones against `alc`. Done
during 4.0.0, after the run/group rework in `812ace7`. Not re-run since.

`812ace7` made every comma-separated list a sequence of **runs** with preproc
**groups** between them, which is what lets a `#if` branch supply the separator its
neighbour is missing. Five families got that treatment. These six positions did not,
so a `#if` at the separator is an `ERROR` here while `alc` accepts the file:

- `argument_list` — **RESOLVED** (BC 29 family I): `preproc_conditional_arguments`,
  both sides of the comma pinned by `test/corpus/split_comma_lists_test.txt`
- `parameter_list` (the `;`-led form)
- `implements_clause`
- `option_member_list`, **comma-leading** shape (see item 2)
- `link_value_list`, **comma-leading** shape. Reproducer:
  `SubPageLink = B = field(A) #if X , D = field(C) #endif , F = field(E);`
  (each directive on its own line). It ERRORs at `3c6ca40` (pre-G8), `a9a170d`
  and after G11 (`5f3f6b9`); alc accepts it in all four configurations (G11
  review probe, 2026-09-28). Cause not traced.
- key field list
- `ml_value_list`

Per-host enumeration is still the tractable approach at this count — the
scanner-classification design sketched during the release is an architecture
upgrade, not a prerequisite.

## 2. A rule existing is not the same as the shape being covered

**Established:** by construction, during the same audit. This is the reason item 1
says "shape" rather than "site".

`preproc_conditional_option_members` exists and handles

```al
X, #if FOO Y #endif
```

and **errors** on

```al
X #if FOO , Y #endif
```

Same program, same `alc` verdict, different side of the comma. Every host needs
**both** placements pinned by a fixture, or the next audit will read the rule's
existence as coverage — as this one nearly did.

## 3. The dangling-operator residual

**Established:** measured directly, and pinned as a fixture.

`test/corpus/preproc_dangling_operator_known_wrong_test.txt` asserts a tree this
project believes is **WRONG**. `#if FOO and` with the operand on the following line
is absorbed into `condition: (preproc_and_expression FOO BAR)` with zero `ERROR`
nodes; `alc` rejects the same input in both configs with `AL0629`. The newline
terminator added to `preproc_if` cannot fire while the condition is grammatically
incomplete.

The fixture is a **tripwire**: its header says the expectation is the defect, so a
failure there most likely means someone fixed the parser and should update the
fixture — not that they broke it. Do not regenerate it with `tree-sitter test -u`
without reading the header.

**A second shape, found 2026-09-29 (A3 review):** an operator ALONE inside a `#if`
arm, `i := 1` / `#if X` / ` +` / `#endif` / ` 2;`
(`test/corpus/preproc_split_operator_negative_test.txt`). It was filed as a deliberate
negative on a one-configuration alc probe. The four-way probe
(`tools/alc_probe/cases/oracle-negative/split-operator.al`, alc 18.0.41) says:
X undefined REJECT (AL0104, AL0111), **X defined ACCEPT, split and flat**. So with X
defined this is valid AL, and the parser ERRORs on it: a grammar gap. The fixture still
asserts the ERROR, and `fixture-classes.tsv` classifies that configuration
`debt(B3)`. Both must change when B3 fixes it.

## 4. `_expression_statement` accepts any expression as a statement

**Established:** two measured attempts, both reverted. Their diffs are stashed with
the messages `failed: _expression_statement restriction (BC 35.7%)` and
`failed: fail-loud backstop (BC 33.3%)` — find them by message, since `stash@{N}`
indices shift whenever any stash is dropped.

`_expression_statement: $ => $._expression` lets a bare literal stand where a
statement belongs. Narrowing it to call/member forms dropped BC.History to 35.7%;
a wider set with `prec(20)` and a declared conflict gave 33.3%. The unexplored lead,
recorded in the rule's own comment in `grammar.js`, is that the rule sits in the
`inline` array — removing it there changes what the conflict resolution can see.
Both prior attempts left it inlined.

## 5. Gate self-test: 5 of 23 cases had never been green on a runner — RESOLVED 2026-09-09

**Established:** output captured from run `31548406743`, job `93965657846`
(`gh run view <id> --job <id> --log`). Final line: `gate-selftest: 17 passed,
5 failed, 1 skipped, of 23 selected`. The five fell into two clusters — the whole
step-6 AL-parsing path dead on the runner (3 cases, including the harness's own
control `step6-clean-corpus-passes`), and both ts-lock guard cases reporting
`holder A never acquired the lock`.

**Resolved:** the two clusters were **one cause**, not two bugs. Four scripts were
committed as mode 100644: `parse-al-parallel.sh`, `tools/ts-lock.sh`,
`tools/gate-fixtures/ts-lock-release-guard.sh` and
`tools/gate-fixtures/json-offsetting-loss/tree-sitter`. The harness runs each gate
through `bash`, so the gates themselves did not need the bit — but
`validate-grammar.sh` Step 6 execs `./parse-al-parallel.sh` directly (Linux:
`Permission denied`, exit 126 → "no readable summary" → cluster A), the ts-lock guard
execs `../ts-lock.sh` with stderr silenced (holder A never creates the lock → cluster
B), and PATH lookup skips a 100644 shim (the real `tree-sitter` runs, nothing is
injected, `pap-offsetting-loss` exits 0). None of it reproduces on Windows, where the
repo is written: `core.fileMode=false`, so index modes are invisible to `ls`, to
`git status` and to Git Bash, which runs a 644 script. The same class had already
hit `tools/check-wasm-fresh.sh` once (bed960a) and was fixed for that one file.

Established by reproducing in a fresh Linux clone (WSL, tree-sitter 0.27.0), which
checks out index modes: byte-identical failure messages to CI, then 21/23 passing
after `git update-index --chmod=+x` on every tracked `*.sh` and shim. The control
still exited 1 for a second reason hidden behind the first: Step 9 (WASM freshness,
added in 4.0.1 after this harness) failed in the scratch copy with
`missing tree-sitter-al.wasm`, because the scratch never carried the wasm or its
stamp. Both are copied now, and Step 9 gained its own mutation case,
`step9-wasm-stale`. Final: 23 passed, 1 skipped (no C toolchain), of 24.

The assertions were not relaxed. The gate for the class is `tools/check-exec-bits.sh`
(validate-grammar.sh Step 10, and its own CI step): it reads the git index, so it
answers the same on every platform. Full write-up in the CHANGELOG entry for the
release after 4.1.0.

## 6. Three uncovered bytes: a doubled UTF-8 BOM

**Established:** measured at the 4.0.1 release with a leaf-walking gap scanner
over both corpora — 36,852 files, exactly 3 non-whitespace bytes covered by no
leaf, all in
`DO.Support/BC/BaseApp/Test/Tests-VAT/ERMVATServCharge.Codeunit.al`. BC.History is
clean at 0.

The file opens with **two** UTF-8 BOMs, at offsets 0 and 3. The first is file
preamble and correctly belongs to no node; the second is equally not AL source,
but it is not at offset 0, so nothing excludes it and no node claims it. Strictly,
the CST is not lossless over those 3 bytes.

Deliberately not "fixed" by widening the scanner's BOM exclusion: that would hide
it rather than decide it. The open question is what the tree *should* do with a
second BOM — alc's verdict on the file has not been probed, and that verdict
decides whether this is an extra to absorb or text to surface.

Two traps that any re-measurement will hit, both of which produced a wrong answer
first:

- **Excluding the leading BOM is mandatory.** Without it, 1,788 BC.History files
  report 3 bytes each (5,364 total) and the corpus looks broken.
  `tools/validate_al_file.py`'s `_significant()` excludes it for the same reason.
- **An `ERROR` node covers its own bytes**, so feeding the scanner deliberately
  broken AL produces *no gap* and proves nothing. The control that works is a
  build that ignores anonymous leaves: it must report gaps on a file the real
  scanner calls clean (22 bytes on a 6-line codeunit, 213 on a real
  PermissionSet).

## 7. Adopt the split-matrix probe tooling under `tools/` — RESOLVED 2026-09-29

**RESOLVED 2026-09-29 (roadmap A2, commits `a9b0431`, `282aa1b`, `74fe12e`; fix round 1 `fc22ba2`).**
`python -m tools.alc_probe run <case.al|dir> [--check] [--json OUT]` compiles every
symbol assignment of a case split and flat (the oracle resolver's text), after a valid
and a garbage control, in isolated projects with a fresh `.app`, and records the
compiler's identity. A broken project (no error located in a `.al` file) is `BROKEN` and exits 2; a flat/split
disagreement is `MISMATCH`. The compile core, `tools/alc_probe/core.py`, is shared
with `tools/config_oracle/probe_alc.py`. The BC 29 and G11 probes (items 1, 17, 18,
19) are committed under `tools/alc_probe/cases/` and reproduce every recorded
verdict. Format and exit codes: `tools/alc_probe/README.md`. The text below is the
original entry.

**Still separate:** `tools/precedence/probe.sh` compiles its 196 cases through its own
bash loop, and reads any missing `.app` as a REJECT (its four controls are the only
guard against a broken rig). Porting it to `tools/alc_probe/core.py` means a Python
rewrite that keeps the `alc-results.tsv` first-error-message format, and re-validating
all 196 rows against a BC 28 symbol-package cache, since those results were taken with
alc 18.0.37. Not done in A2.

**Established:** the method (see *The instrument*, above) exists and works; the
tooling that automates it was written ad hoc during the release and never landed.

Automating the four-way compile is what makes items 1–3 cheap to re-verify. It
caught one of its own case-construction bugs during the release — a probe that
would otherwise have been filed as "alc rejects Implementation splits", which is
false.

## 8. `var_body` admits body elements: procedures land inside the global var section — RESOLVED 2026-09-28

**Resolution:** `var_body` no longer admits `preproc_split_procedure`, and
`preproc_conditional_var`'s branches admit only `variable_declaration` and
`var_attribute_item`. The conditional/split procedures now parse at body level,
as siblings of the var section. The one real crossing (a branch that continues
the var section and then starts procedures, `AOAIDeploymentsImpl.Codeunit.al:28`)
gets a new sibling rule, `preproc_split_var_section_tail`, whose `variables`
field holds the continued declarations. Measured after the fix:
- BC.History, DC and BC 28.1: 0 ERROR/MISSING nodes.
- tree-harness: exactly 59 BC.History files changed. Across them the only node
  changes are re-spanned `var_section`/`var_body` and 116 `preproc_conditional_var`
  -> 115 body-level `preproc_conditional` + 1 `preproc_split_var_section_tail`.
- Config-oracle quick tier: discrepancies 9 -> 1 (the remaining one is the known
  mid-file-BOM oracle false positive), pass 246 -> 264.
- STATE_COUNT 14,661 -> 13,902.
- Three fixtures had asserted the defect (a `protected var` section nested in
  another var section's body; procedures inside `var_body`) and were corrected.
- The oracle lowering for `preproc_split_var_section_tail` is milestone-2 work
  (a cross-sibling merge into the preceding var_section); it is registered
  `unsupported` until then.

The original finding follows.

**Established:** config-oracle quick tier, 2026-09-28 (milestone-1 results,
`docs/superpowers/plans/2026-09-27-config-oracle-milestone-1-results.md`), grammar
sha `61299ce05fb988e7`, HEAD `1243f8c`. Production census and alc probe the same day.

Two grammar paths let a `var` section absorb what follows it:

1. **Split shape.** `var_body: repeat1(choice(..., $.preproc_split_procedure))` lists the
   split procedure directly, so a `var` section followed by an `#if`-split procedure
   signature swallows the whole procedure and its attribute.
2. **Conditional shape.** `preproc_conditional_var` (the next rule after
   `var_attribute_item`) accepts `$.attribute_item` and `$._body_element` in every arm,
   so a COMPLETE `#if … procedure … #endif` after a global `var` section is swallowed
   too. Minimal repro:

   ```al
   codeunit 50100 P
   {
       var
           G: Integer;

   #if not CLEAN24
       procedure X()
       begin
       end;
   #endif
   }
   ```

   parses as `var_section > var_body > (variable_declaration) (preproc_conditional_var
   (preproc_if …) (procedure …) (preproc_endif …))`.

In both, the tree claims a procedure is a member of the var section. No configuration
of the text has that shape: the single-configuration reference ends `var_section` at
its last `variable_declaration` and puts the attribute and procedure in
`declaration_body` as siblings.

**Census** (every tree of the 2,386 `#if` files in the three roots, counting direct
`var_body` children that hold a non-variable body element; `pragma`-only conditionals
excluded, they are extras):

| corpus | split shape | conditional shape with procedure(s) | procedures inside | other |
|---|---|---|---|---|
| BC.History | 1 node / 1 file | 115 nodes / 58 files | 227 | 1 (`protected var` section nested in `var_body`, `Sales/Pricing/SalesPrice.Table.al:275`) |
| BC 28.1 | 0 | 66 nodes / 24 files | 212 | 0 |
| DC | 0 | 2 nodes / 2 files | 20 | 1 (procedure attribute alone in the `#if`, `Cloud Migration/CDCCloudMigrationMgt.Codeunit.al:16`) |
| **total** | **1** | **183 nodes / 84 files** | **459** | 2 |

Example sites (1-based rows):

- split: `BC.History/BaseApp/Source/Base Application/Foundation/Shipping/ShippingAgent.Table.al:87`
  (`GetTrackingInternetAddr`).
- conditional: `BC.History/System Application/Source/System Application/Password/src/PasswordDialogManagement.Codeunit.al:20`
  (its `var_section` spans rows 17–92 and holds five procedures).
- conditional: `H:/Git/BC28.1/Application Test Library/Source/Application Test Library/LibraryPatterns.Codeunit.al:390`
  (`var_section` rows 11–396).
- conditional: `DC/Cloud/.dependencies/DC/Codeunit/CDCCaptureRTCLibrary.Codeunit.al:23`
  (19 procedures in one conditional; `var_section` rows 8–213).

**Why the oracle reported only 8 of these.** The quick tier's 8 discrepancies are all
the split shape: `attribute_preproc_procedure.txt#0` (CLEAN24=0/1),
`preproc_interrupted_var_section.txt#0` (CLEAN24=0/1), `#1` (CLEAN25=0/1), `#2`
(CLEAN24=0/1); both files pin the wrong nesting as expected output. The conditional
shape is invisible for now: `preproc_conditional_var` has no lowering handler in
milestone 1, so every configuration containing one is `cannot-validate:
lowering:unsupported-type` (22 quick-tier configurations). The resolve tier does no
lowering and cannot see either shape.

**alc probe** (four-way; `tools/config_oracle/probe_alc.compile_probe`, not committed
as a script). The probe did **not** compile the table fixture or ShippingAgent: it used
an Integer-typed codeunit copy of the split fixture, so it needs no symbols:

```al
codeunit 50100 Probe
{
    var
        GlobalVar: Integer;

#if not CLEAN24
    [Obsolete('Field length will be increased', '24.0')]
    procedure TestProc(Param: Text[30]) Result: Text
#else
    procedure TestProc(Param: Text[50]) Result: Text
#endif
    var
        LocalVar: Text;
    begin
        Result := Param;
    end;
}
```

Flat undefined (the `#if not CLEAN24` arm with its directive lines removed), flat
defined (the `#else` arm), split with `[]` and split with `["CLEAN24"]`: all four
ACCEPT. Controls in the same session: `unit("        Message('x');")` ACCEPT and
`unit("        GARBAGE!! ;;; }{")` REJECT (AL0104, AL0111, AL0183, AL0198). The
conditional shape was not probed separately; its flat configurations are an ordinary
var section followed by procedures.

**Fix direction (not attempted):** `var_body`, and the arms of `preproc_conditional_var`
when it sits in `var_body`, admit only `variable_declaration`, `var_attribute_item` and
their own conditionals. A split or conditional procedure, and a procedure-level
attribute, then end the `var_section` and attach as its sibling in `declaration_body`
(which already hosts `preproc_split_procedure` and `preproc_conditional`). If
`preproc_conditional_var` still needs body elements elsewhere, split it into a
var-only form for `var_body`. The two fixtures' expected trees change and must be
re-derived from `tree-sitter parse`, not `-u`'d; the census above is the
before-measurement.

## 9. `&&` and `||` in `#if` conditions: the grammar accepts what alc rejects

**Established:** `tools/config_oracle/probe_alc.py` probes `ampamp_rejected` and
`pipepipe_rejected` (AL0631; `docs/preproc-directive-semantics.md`), against
grammar.js `preproc_or_expression` / `preproc_and_expression`, which each take
`choice(kw('or'|'and'), '||'|'&&')`.

The parser builds a clean `preproc_and_expression` over `#if A && B`; the compiler
refuses the file. The config oracle's resolver follows the compiler and reports
such a file as `cannot-validate: resolver:unsupported-condition-token`, so the
oracle cannot compare it. Production impact: zero — no `#if`/`#elif` line in
BC.History, DC or BC 28.1 uses `&&` or `||` (grep, 2026-09-28). Per "parse
structure, don't validate" this may be kept on purpose; if so, say so here and
close the item, otherwise remove the two string alternatives.

## 10. Split `add*` headers whose bodies stay open over `#endif` (EDocumentDE)

**Established:** by measurement on 2026-09-28, during the BC 29 family-E work
(`docs/bc29-parse-gaps.md`). alc accepts both configurations.

```al
#if not CLEAN27
    addafter(A) { group(X) { Caption = 'X';
#else
    addlast(B) { group(Y) { ShowCaption = false;
#endif
        field(F; Rec.F) { } } }
```

The one-level form fails too: `#if addafter(A) { #else addlast(B) { #endif … }`.
The only file is `Apps/DE/EDocumentDE/app/src/EDocumentServiceDE.PageExt.al`.
A `preproc_split_layout_open` rule parses it. Its cost against 14,630 states:

| attempt | STATE_COUNT |
|---|---|
| depth 1, branch `add*(…) {` only | +835 |
| depth 1, branch `add*(…) { <layout elements>` | +1,508 |
| depth 1, branch body as the shared `layout_body` | +2,270 |
| depths 1 and 2 (the real file) | `generate` still running after 600 s CPU; stopped |

**Why it costs this much.** After `#if add*(…) {`, `preproc_conditional_layout`
reads the same text as a complete `add*_modification`, until the `#else`. So
two nonterminals share the whole layout-body prefix, and LR must copy that
automaton for each. The same mechanism made the recursive `begin` arm of
`preproc_split_open_statement` cost +2,540 (family G). There, a narrower arm
solved it. Here no narrower arm exists: the headers and braces are the
construct.

**What would fix it cheaply.** The general answer to crossing constructs is a
configuration-aware parse: parse each configuration and merge the trees. This
is the same answer recorded for family H. The configuration-consistency oracle
already resolves configurations, so its resolver is a starting point. This is
an architecture change, not a rule, and it is not filed as a known limitation.

## 11. A one-pair ML value parses as a comparison (G9)

**Established:** 2026-09-28, config-oracle milestone 2 Task 18, while fixing G8.
alc accepts `CaptionML = ENU='c';` (probe: a table with that property compiles;
`CaptionML = ENU=;` is rejected with AL0219).

```al
CaptionML = ENU='c';            // (property_expression (comparison_expression ...))
CaptionML = ENU='a', DAN='b';   // (ml_value_list (ml_value_pair ...) (ml_value_pair ...))
```

With one pair, `ENU='c'` is also a complete expression, and the flat parse takes
`property_expression`. Nothing in the value tells the two apart: `Visible = A = 'b';`
really is a comparison. Only the property NAME does, which makes this the
`CalcFormula` situation (CLAUDE.md: the one property keyed by name, "do not
generalise this"). A fix is therefore a design decision, not a rule: key the ML
properties (`CaptionML`, `ToolTipML`, `OptionCaptionML`, ... every name ending in
`ML`) by name in the scanner, as `CALC_FORMULA_PROPERTY_NAME` does, or accept the
expression reading.

Production impact: zero. ML properties occur in 6 files over BC.History, DC,
BC 28.1 and BCApps 29.0 (`grep -rlE '^\s*\w+ML\s*='`), and every one has two or more
pairs. The config oracle sees it in exactly one shape: a whole-value `#if` whose
arm is a one-pair ML value with the `;` after `#endif` (the arm is `ml_value_list`
before the directive, the flat parse is a comparison before `;`). That shape is a
strict xfail, `test_single_pair_ml_arm_before_endif` in
`tools/config_oracle/tests/test_property_value_conditional.py` (moved there from
`test_table_relation.py` by G6, unchanged). **Still open after G6**: G6 renamed
the whole-value conditional (`preproc_conditional_property_value`) and did not
touch its arms, so the xfail still fails for the same reason.

---

## 12. Hidden MISSING tokens are invisible to `tree-sitter parse`, `--json-summary` and parse-al-parallel.sh — RESOLVED 2026-09-29

**Resolution (308f64c, roadmap A1):** `tools/has_error_sweep.py` classifies each
input as clean / visible / hidden-only and exits 1 on either error class, 2 when
it cannot run. It runs as validate-grammar.sh Step 3b (corpus fixtures) and
Step 6b (`--full`), and in CI over the fixtures and `tools/gate-fixtures/al-corpus`.
Measured: the 673528e^ parser gives hidden-only on 5 of the 8
`test_directive_eol.py` inputs (`tree-sitter parse --json-summary`: 8 of 8
successful). BC.History, DC, BC 28.1 and BCApps 29.0 have 0 hidden-only files.
BCApps has 2 visible (EDocumentDE, APAC ERMPurchaseReportsIII).
**Correction to the text below:** `tree-sitter test` is not blind. Its actual tree
prints `(MISSING _directive_eol)`, so a corpus fixture that holds the triggering
input fails Step 2. The blind tools are `tree-sitter parse`, `--json-summary` and
parse-al-parallel.sh.


**Established:** 2026-09-28, milestone 2 whole-branch review, then the
`_directive_eol` fix (`673528e`). Before it, `#if A` followed by `\f\n`, `\v\n`,
` ﻿\n` or `\r\r\n` gave a MISSING `_directive_eol`. py-tree-sitter's
`root_node.has_error` was True (`tools/config_oracle/tests/test_directive_eol.py`,
5 of 8 cases failing on the old scanner).

A MISSING node for a HIDDEN (`_`-prefixed) token is not printed. So
`tree-sitter parse` shows no `MISSING`, `--json-summary` reports `successful`,
and `parse-al-parallel.sh` counts the file as parsed OK. (`tree-sitter test` does
print `(MISSING _directive_eol)`, so a corpus case holding the input would fail;
none did.) The config oracle's replay 3 was the same class:
"CLI-silent, not API-silent".

Proposal: a gate that sweeps a corpus with py-tree-sitter and fails on any file
whose `root_node.has_error` is True while it has no visible ERROR/MISSING node.
The loader (`tools/query_coverage/loader.py`) and `ir.from_tree`'s
`has-error@` fallback already exist, so it is a small script plus a
`validate-grammar.sh --full` step. Until then, a fix touching a hidden token
needs a `has_error` pytest, not a corpus fixture.

---

## 13. Candidate G10: `Visible = Rec.A #if X and B #endif ;` ERRORs

**Established:** 2026-09-28, milestone 2 whole-branch review. Reproduced at
`673528e` (page field, `has_error` True). The review found it predates this branch.

```al
Visible = Rec.A
#if X
 and B
#endif
;
```

Flat, `Visible = Rec.A and B;` is `property_expression(logical_expression)` and
`Visible = Rec.A;` is `table_relation_value`. With the `#if` the
`table_relation_value` reading wins: the tree is `table_relation_value` holding a
`preproc_conditional_table_relation` whose arm is `ERROR (identifier)` for `and`.
Unchanged by G6 (re-parsed after it): this is the relation-continuation route,
which keeps `preproc_conditional_table_relation`. Item 15 is the root question.
G5's `preproc_conditional_expression_tail` would be
the flat-shaped reading; why it loses here is not yet traced. Production sites:
not measured. alc four-way probe not
yet run.

---

## 14. The resolve and full tiers exit 1 on production corpora — RESOLVED 2026-09-29

**Established:** 2026-09-28, milestone 2 Task 17 and the P6 runs (results doc,
"Resolve sweep" and "Run 3"). `runner.run` exits 0 only when every non-`pass`
record is classified, and only the quick tier loads a classification file
(`tools/config_oracle/fixture-classes.tsv`, fixtures only). Production records
that cannot validate (the 7 BCApps `reference-error:error` records of invalid
source, the milestone-3 `unsupported-type` records) are classified in the results
doc, not in any file the runner reads, so every production run exits 1 even when
it is clean. Needed before the full tier can gate: a production classification
file, keyed like `fixture-classes.tsv`, loaded by `--tier resolve|full`.

**2026-09-29 (roadmap A3):** the quick tier had the same defect. `fixture-classes.tsv`
listed nothing, so `run --tier quick` exited 1 on every clean tree. Its 150
cannot-validate records are now classified there, as `negative`, `invalid-config` or
`debt(C1)`, and the quick tier exits 0 and gates (Step 5e, CI). The production half
is still open (A4).

**2026-09-29 (roadmap A4): RESOLVED** in d4e32aa. `--tier resolve|full` load
`tools/config_oracle/production-classes.tsv`: 434 exact entries (debt(C1, M3) 413,
debt(F1, F1) 14, invalid-source 7, the last backed by `tools/alc_probe/cases/production-invalid/`).
Measured on all four corpora: full exits 0 (1,295 s; 14,228 pass, 434 classified, 0 stale,
0 discrepancies), resolve exits 0 (476 s; 14,655 pass, 7 classified). A classified
configuration still counts as not validated.

---

## 15. Dotted property references are classified as table relations

**Established:** 2026-09-28, G6 design review (gpt-6-astra, section 2E). Not
probed with alc; nothing here is a parse error.

`Visible = Rec.A;` is `table_relation_value(table_relation_expression(
simple_table_relation table: (member_expression)))`: an ordinary dotted
expression, claimed to be a table relation and fielded `table`. Renaming
`table_relation_value` alone would not help, because its descendants still say
`simple_table_relation` and `table`. Reachability from every property is not
the defect -- a relation-shaped value may be recognised without validating the
name -- the misclassification is. A fix needs one neutral representation for
an ambiguous dotted reference that the flat form AND the split forms (item 13,
G10) both give, or contextual parsing keyed by the property name (the
`CalcFormula` route, which CLAUDE.md says not to generalise lightly). G6 left
this open on purpose: it is a property-grammar redesign, not a rename.

---

## 16. `CalcFormula` has no whole-value conditional

**Established:** 2026-09-28, G6 design review (section 2F). Read from the
grammar, not probed.

`preproc_conditional_property_value` is reached through `_property_value`, and
the `CalcFormula` arm of `property` takes `_calc_formula_expression` instead,
so `CalcFormula = #if X sum(T.A) #else count(T) #endif;` does not get the new
node. Support, if alc accepts the form, must keep formula-shaped arms
(`aggregate_formula` / `lookup_formula`), not route them through
`_property_value`, where a no-`where` aggregate is a call (issue #21).

---

## 17. `_property_with_terminator_in_if` has no host parity: valid AL ERRORs at two hosts — RESOLVED 2026-09-28

**RESOLVED 2026-09-28 (G11, commit `04af3f6`).** `grammar.js` lists
`$.property` directly at exactly three hosts: `_body_element`,
`_action_element` and `assembly_body` (every other property host reaches it
through `_body_element`). The two without the variant now take
`_property_whole_value_in_if`: the whole-value form of
`_property_with_terminator_in_if`, without its relation form. Measured: the
full variant at both hosts cost +217 states (action +161, assembly +61), the
whole-value one +89 (action +66, assembly +28), with one conflict needed at
the action host. No relation property is valid at either host: alc rejects
`TableRelation` there (AL0124), and also `Permissions`, flat and split, so
`permissions_property` has no parity gap either. Pinned by
`test/corpus/property_terminator_in_if_hosts_test.txt` (area, assembly, and
an action group, which always parsed; alc four-way ACCEPTs all three) and
`test_semicolon_inside_arms_at_direct_property_hosts` in
`tools/config_oracle/tests/test_property_value_conditional.py`
(cannot-validate before, pass after). The text below is the original report.

**Established:** 2026-09-28, G6 design review (section 2F), then a four-way alc
probe in G6 fix round 1 (X defined/undefined x split/flat, runtime 15.0, no
symbol packages). The probe discriminated: `OptionMembers = A B;` and an
assembly `Version =` split whose arms lack the `;` were both rejected (AL0104)
in the same project.

The variant whose `;` sits inside a `#if` arm (`ToolTip = #if X 'a'; #else 'b';
#endif`, no `;` after `#endif`) is aliased to `property` only in
`_body_element`. Two hosts list `$.property` alone:

| host | probe | alc, all 4 configurations | this parser, split form |
|---|---|---|---|
| `_action_element`, via `action_body` (an `area(...)` in `actions`) | RoleCenter page, `area(Embedding) { ToolTip = #if X 'a'; #else 'b'; #endif action(A) { RunObject = page P; } }` | ACCEPT (exit 0, app written), flat and split | **ERROR** (3 ERROR nodes, from the `#if` line through `#endif`) |
| `assembly_body` | `dotnet { assembly(mscorlib) { Version = #if X '4.0.0.0'; #else '2.0.0.0'; #endif Culture = ...; PublicKeyToken = ...; type(System.DateTime; MyDateTime) { } } }` | ACCEPT, flat and split | **ERROR** (1 ERROR node over the conditional) |

The review also saw `Caption = #if X 'a'; #else 'b'; #endif` directly in
`area(Processing)` give a MISSING `;`. That form is not valid AL anyway:
AL0124, Caption cannot be used on an action area. ToolTip on `area(Embedding)`
is the production shape: 5 sites in BC.History, e.g.
`AccPayablesCoordinatorRC.Page.al:175`, all flat.

The after-`#endif` placement works everywhere `property` does. A property
inside `action(...) { }` or `group(...) { }` is unaffected: those bodies are
`declaration_body` or include `_body_element`. Production sites of the split
form at these two hosts: 0 (every file parses clean). To fix: add
`alias($._property_with_terminator_in_if, $.property)` to `_action_element`
and `assembly_body`, then measure the conflicts and states that adds.

---

## 18. A `#if` that opens a link list is split off as a whole value (G8 regression); an opening option-member `#if` ERRORs — RESOLVED 2026-09-28

**Link list: RESOLVED 2026-09-28 (G11, commit `28c601f`).** Traced:
`link_value_list`'s `prec.left(6)` beat
`_link_value_branch` (prec 0) in a reduce/reduce, which tree-sitter settles by
precedence before `conflicts`, so the list-internal reading was dropped at
generation time (measured: with only the arm `;` required, the unquoted form
ERRORed instead of misparsing). Fix: prec 6 on the arm plus a declared
conflict, and the `;`-inside-the-arms whole value
(`_property_value_conditional_in_if`) now requires each nonempty arm's `;`, so
it can no longer end a property with no terminator. alc four-way ACCEPTs the
unquoted, quoted and `RunPageLink` forms; all three now match pre-G8
(`3c6ca40`). Pinned by `test/corpus/link_list_opening_conditional_test.txt`
and `tools/config_oracle/tests/test_list_opening_conditional.py`.

**Option-member list: RESOLVED 2026-09-28 (G11, commit `6fed757`).**
`option_member_list` gained a head alternative, `preproc_conditional_option_members`
then a REQUIRED member, so a `#if` that opens the list and is continued after
`#endif` gives `option_member_list(preproc_conditional_option_members ...)`,
the mid-list shape. alc four-way ACCEPTs `A, #endif B, C;`, `A, #endif B;`,
both arms prefixes, quoted members, and an opening `#if` followed by a
mid-list one (X, Y all four); `A, #endif B C;` is rejected (AL0104). +68
states, eight conflicts. Pinned by
`test/corpus/option_list_opening_conditional_test.txt` and the oracle witness
above. A configuration that leaves ONE member is a bare leaf flat
(`OptionMembers = B;` is `value: identifier`), which the list cannot also be,
so the oracle gains a named rewrite, **option-member-list-unwrap**
(`lowering/engine.py`, with a mutant test). The history below is kept as it
was established.

**Established:** 2026-09-28, G6 acceptance fixtures, corrected in G6 fix round 1
after review. Trees below re-parsed at G6 (`e842a75`); the review found the same
at `def2879`. alc accepts every form here with the symbol defined and undefined
(probe discriminated: `OptionMembers = A B;` rejected in the same project).

**Link list, unquoted field names: a SILENT misparse, no ERROR.**

```al
SubPageLink =
#if X
    A = field(B),
#endif
    B = field(A);
```

gives TWO properties:

```
(property name: (property_name)                 ; SubPageLink, no `;`
  value: (preproc_conditional_property_value
    (preproc_if ...) value: (link_value_list (link_value ...)) (preproc_endif ...)))
(property name: (property_name)                 ; `B`
  value: (property_expression (call_expression function: (identifier) ...)))
```

The first is `_property_with_terminator_in_if` (whole-value arm, no
terminator); the second reads `B = field(A);` as a new property named `B`
whose value is a call. The tree has no ERROR and no MISSING, so
`parse-al-parallel.sh`, `validate-grammar.sh` and the corpus error-count gates
all report it as clean. `RunPageLink` inside an `action(...)` behaves the same
(review). At `3c6ca40`, the commit before G8, it was one
`link_value_list(preproc_conditional_link_values ...)`: a **G8 regression**.

**Link list, quoted field names: ERROR.**

```al
SubPageLink =
#if X
    "A" = field(B),
#endif
    "C" = field(D);
```

gives `property` holding `ERROR(preproc_conditional_property_value ...)` then
`value: link_value_list` (ERROR over the `#if` ... `#endif` lines). A quoted
name cannot start a property, so the split reading is not available and the
parse errors instead. At `3c6ca40` this form was
`link_value_list(preproc_conditional_link_values ...)` (measured).

The likely mechanism for both, NOT traced: since G8 a whole-value arm may be any
`_property_value`, so `A = field(B),` also reduces to `link_value_list`, and
that rule's `prec.left(6)` decides the reduce/reduce against
`_link_value_branch` statically; GLR never keeps the list-internal reading.

**Option-member list: ERROR, and never supported.**

```al
OptionMembers =
#if X
    A,
#endif
    B;
```

gives `property value: (preproc_conditional_property_value ... value:
(option_member_list (option_member (identifier))) ...)` with no terminator,
then `ERROR (identifier)` for `B` and an `empty_statement` for the `;`. It
ERRORed at `3c6ca40` too: `option_member_list` admits a conditional only after
a comma, so there is no list-internal reading to lose.

The permission form (`Permissions = #if X tabledata A = R, #endif tabledata B =
R;`) is unaffected and stays list-internal (pinned in
`test/corpus/property_value_conditional_node_test.txt`, as are the mid-list
link and option forms). Production sites: 0 for the ERROR forms; the silent
form is invisible to the error-count gates, but the G8 and G6 tree-harness runs
were byte-identical, so no BC.History or BC 28.5 file changed tree. None of
the opening forms is asserted by a fixture: the fixture would bless a defect.

---

## 19. A relation continued into a `#if` with the `;` after `#endif` loses its terminator — RESOLVED 2026-09-28

**RESOLVED 2026-09-28 (G11, commit `824fcf4`).** `table_relation_value`
gained a third form, `table_relation_expression preproc_conditional_table_relation`,
so the flat `property` holds the continuation and its `;`. alc four-way
ACCEPTs the `#if/#else` form, the no-`#else` form and an `else` before the
`#if` (the last always parsed); `else Resource Customer` is rejected (AL0104).
+31 states, one conflict. Pinned by
`test/corpus/table_relation_continuation_semicolon_after_test.txt` and
`test_else_join_with_semicolon_after_endif_every_config` in
`tools/config_oracle/tests/test_table_relation.py` (discrepancy before, pass
after). The text below is the original report.

**Established:** 2026-09-28, G6 acceptance fixtures; reproduced at `def2879`,
before G6.

```al
TableRelation = if (Type = const(Item)) Item
#if X
    else Resource
#else
    else Customer
#endif
    ;
```

No ERROR, but the `;` is an `empty_statement` sibling of the `property`, not
its terminator. `table_relation_value` is `choice(expression, conditional)`, so
the flat `property` cannot hold `expression conditional`; only
`_property_with_terminator_in_if` (via `_table_relation_split_value`) can,
and that variant takes no `;`. The flat parse of either configuration keeps the
`;` in the property. Not asserted by a fixture. alc not probed.

---

## 20. `#endif;`: the grammar accepts a token after `#endif` that alc rejects

**Established:** 2026-09-29, A3 (config-oracle gate) review and fix rounds 1-2. Manual
alc 18.0.41 compiles, each with X defined and undefined, runtime 15.0, no symbols
packages:

| input | alc |
|---|---|
| `TableRelation = #if X T; #else T; #endif;` (property) | REJECT, AL0631, both configurations |
| `begin #if X Message('a'); #endif; end;` (code block) | REJECT, AL0631, both configurations |
| the same two without the `;` after `#endif` (controls) | ACCEPT |
| `#endregion;` | ACCEPT (region lines take free text) |

**What the grammar does:** no ERROR, no MISSING (`has_error` is false, checked with
py-tree-sitter). `preproc_close` covers `#endif` alone, and the `;` is parsed as
something else in each of the two shapes:
- in a property it becomes the property's `;` terminator;
- in a code block it becomes an empty statement.

This is the same class as item 9 (the grammar accepts what alc rejects). Four positive
fixtures had this typo until A3 fix round 1 (45660ac) corrected them. So no fixture
exercises the shape now, and this item is its only record.

**Production impact:** 0 `#endif` lines with a trailing token in BC.History, DC,
BC 28.1 W1 (`H:/Git/BC28.1`) and BCApps 29.0 (`H:/Git/BCApps-29.0`). Measured with
`grep -rniE '^\s*#\s*endif\s*[^[:space:]/]' --include=*.al`. The two production
directive lines that do end in `;` are `#endregion;` (the Continia connector's
`ContiniaAPIRequests.Codeunit.al:882`, in BC 28.1 and BCApps 29.0), which alc
accepts.

**Owner:** roadmap B2 (directive-word boundaries, and what may follow a directive
word).

**Not pinned by alc_probe.** The oracle's resolver, which `alc_probe` uses for
discovery, refuses a token after `#endif` (`resolver:trailing-token`), so no
`alc_probe` case can hold this input. It is the same limit as the 13
resolver-refused deliberate negatives in `fixture-classes.tsv`. C2's raw-compile
mode, which skips the resolver, is what can pin it. Until then the table above is the
evidence. B2 should add a negative fixture asserting the ERROR once it is fixed.

## 21. The MSVC-built native library parses ~2x slower than clang -O2

**Established:** 2026-09-30, A5 (performance baselines) and its independent review.

**Evidence:**
- `tree-sitter build -v` shows the library every local tool loads (`al.dll`, via
  `tools/query_coverage/loader.ensure_library`) is built by MSVC 19.44 with
  `-nologo -MD -O2 -Brepro -std:c11 -W4 -LD -utf-8`: an optimised build, not a debug one.
- The reviewer built the same `src/parser.c` and `src/scanner.c` with `zig cc -shared -O2`
  (clang), loaded both DLLs into one py-tree-sitter process and timed DC (1,352 files)
  single-threaded, three interleaved passes after a warm-up, timing only `parse()`:
  MSVC 1.527-1.538 s, clang 0.741-0.749 s, i.e. **2.06x**. The two DLLs produce identical
  `rows()` trees on every DC file. Same runtime (`.pyd`) in both, so the difference is the
  grammar DLL's own code (generated lexer and parse tables, scanner), not call overhead; it
  holds on the largest files too.
- WASM (emscripten, clang) sits between the two: 1.009 s on DC. So "WASM is faster than
  native", which the first baseline reported, holds only against MSVC.
- `python -m tools.perf native --cc zig` reproduces the comparison over all four corpora;
  `docs/performance-baselines.md` ("Compiler sensitivity") has the recorded figures.

**Who ships MSVC code:** the Python wheels built on `windows-latest` in
`.github/workflows/publish-pypi.yml` (setuptools' MSVC defaults plus `/std:c11 /utf-8`
from `setup.py`), and every Windows `npm install` (no prebuilds are published;
node-gyp compiles `binding.gyp` with MSVC on the user's machine). So Windows consumers of
both bindings get this code generation.

**Answered by the compiler spike, 2026-09-30/10-01.** The report is
`.superpowers/sdd/spike-cc/spike-report.md`; the table is in `docs/performance-baselines.md`,
"Compiler sensitivity: the compiler spike". Every speed figure below is an `ab` ratio against
MSVC `-O2`.

- **Tree identity.** 33 builds were checked against MSVC's complete `rows()` trees on all four
  corpora (70,355 files), and all 33 are identical. No compiler-dependent parse was found.
- **The compiler decides; flags do not.**
  - MSVC `/Ox`, `/Ob3`, `/GL`+`/LTCG`, the setuptools wheel flags and the node-gyp Release
    flags (`/Ox /Ot /Ob2 /Oy /Oi /Gy /MT`; no LTCG, since `node_with_ltcg` is false) all
    measure **1.00x**.
  - clang-cl `/O2` measures **2.07x** on DC and **2.05x** on BC.History. clang `-O2`/`-O3`,
    `-flto` and `-march=native` all come out at 2.04-2.07x.
  - zig cc is about 1.5% behind clang-cl, and gcc 13 about 5% behind.
  - With the wheel's own flags, swapping MSVC for clang-cl gives **2.04x** on BC.History. With
    node-gyp's flags it gives 2.09x on DC.
- **PGO.**
  - MSVC PGO reaches 2.0x, about 2% behind plain clang-cl (two 24-round runs agree).
  - clang PGO adds 0-3% on top of clang-cl, which `ab` cannot resolve. The gap between
    training on the measured set and on a disjoint set is also below resolution.
- **Why (a hypothesis, not proven).**
  - In every slow MSVC build, `ts_lex_keywords` has a **14,952-byte stack frame**. At `-O1` it
    is 9,224 bytes, at `-Od` 232 bytes, and clang's is 32 bytes. The PGO builds have none.
  - Speed follows the frame: `-O2` 1.00x, `-O1` 1.11x, `-Od` **1.68x**, PGO 2.0x.
  - Removing the `__chkstk` probe (`-Gs32768`) changed nothing, so the likely cost is how
    MSVC's optimiser spills in that giant function.
  - It is not jump-table lowering: `-Od` has the same single jump table as `-O2`.
- **Build time** for `parser.c` + `scanner.c`: MSVC takes 11.3 s at `-O2` (13.3 s at `-O1`);
  clang, clang-cl and gcc take 2.7-2.8 s.
- **Tools.**
  - `tree-sitter build` and `tree-sitter test` honour `CC`.
  - `tree-sitter test` rewrites the mtimes of `src/*.c` on every run here, so it always
    recompiles: 11.9 s with MSVC, 3.2 s with `CC=clang-cl`.
  - ccache and sccache cannot cache `tree-sitter build`, which compiles both files in one call.
    They do help per-file builds: for example sccache+cl takes 0.8 s on a hit, across
    worktrees, and a `scanner.c`-only edit becomes 0.2-0.9 s. They do not help the CI wheel
    job or the grammar loop, because every grammar edit regenerates `parser.c`.

**Recommended action (E3):**
1. Build the Windows wheels with clang-cl: a `build_ext` override that sets the compiler
   executable, since setuptools ignores `CC` on Windows, keeping MS `link.exe`. Verify that
   LLVM is on the runner, and `ab` the built wheel's library before release.
2. Publish clang-cl-built Windows prebuilds for the Node binding. `node-gyp-build` already
   loads them. Keep the MSVC compile as the fallback. Do not set `msbuild_toolset: ClangCL`,
   which would make source installs need the VS clang component.
3. Document `CC=clang-cl` for the local dev loop. The fallback without LLVM is `-0`.
   **DONE 2026-10-01 (6fd1f36, 77fb11d):** clang-cl is now the default CC on Windows when LLVM
   is installed and `CC` is unset (`tools/default-cc.sh`, `loader.build_env`); opt out with
   `TS_AL_NO_CLANG=1`. BC.History trees are byte-identical between the two libraries
   (tree-harness). E3 still owns 1, 2 and 4.
4. Take `tools.perf` baselines with `CC=clang-cl`, and keep an MSVC-against-clang-cl `ab` row
   as a canary.

Rejected, with the reasons measured above:
- MSVC flag tuning: no effect.
- MSVC PGO: slower than clang-cl, and it needs a training step and a profile refresh on every
  grammar change.
- clang PGO: gain unresolved, same upkeep.

**Owner:** roadmap E3 (artifact verification), because shipped Windows wheels are affected;
D2 measures (its thresholds must be set per compiler: `tools/perf compare` warns when the
compiler or flags differ). Do not tune the grammar against MSVC numbers alone (D1).

## 22. `case_else_branch` has two shapes: a sibling of `case_body`, or inside it under `#if`

**Established:** 2026-10-01, A6, while closing
[`improvements-for-owned-ir-consumer.md`](improvements-for-owned-ir-consumer.md) issue 2.
The consumer's request is satisfied: `case_else_branch` has a single `body`
(`statement_block`), as `case_branch` does. This item is a consistency candidate that the
reconciliation turned up, not an open request.

**The two shapes.** A plain `else` is a direct child of `case_statement`, beside `case_body`
(`case_statement` has `optional($.case_else_branch)` after `field('body', $.case_body)`). An
`else` inside `#if` is a child of `preproc_conditional_case`, which sits inside `case_body`
(`grammar.js`, `preproc_conditional_case`, about line 4961: every branch takes
`optional($.case_else_branch)`). Parsed with this branch's library (py-tree-sitter 0.25.0,
both `has_error` False):

```
case X of 1: A(); else B(); end;          case X of 1: A();
                                          #if C
                                          else B();
                                          #endif
                                          end;

case_statement                            case_statement
  body: case_body                           body: case_body
    case_branch ...                           case_branch ...
  case_else_branch                            preproc_conditional_case
    else_keyword                                preproc_if ...
    body: statement_block                       case_else_branch
  end_keyword                                     else_keyword
                                                  body: statement_block
                                                preproc_endif ...
                                            end_keyword
```

**Production.** BC.History has 1,470 `case_else_branch` nodes: 1,468 as direct children of
`case_statement` (826 files), and 2 under `preproc_conditional_case`
(`Sales/Receivables/ApplyCustomerEntries.Page.al:1241`, an `else` that exists only under
`#if not CLEAN25`, and `Inventory/Availability/ItemAvailabilityLineList.Page.al:156`). So a
consumer that looks for the else only beside `case_body` misses 2 in BC.History. One that
looks only inside `case_body` misses the other 1,468.

**Options for the spec.** (a) Put every else under `case_body`, which moves 1,468 nodes in
826 files. (b) Give `case_statement` an `else` field, and let the `#if` form keep its node
inside the conditional, documented as the one place it appears. (c) Keep both shapes and
pin them in `tools/check-field-types.py` and the docs. Any option other than (c) is a
tree-shape change and needs E2's consumer migration check.

**Owner:** Phase B, roadmap row B10 (a tree-shape spec). It waits for user approval like
B4 to B6.


## 23. A `Permissions` list ending inside an `#if` arm ERRORs when a split procedure follows

**Established:** 2026-10-01, during F0 plan drafting. Reproduced with
`./tools/ts-lock.sh tree-sitter parse` at 0a8e220: the repro below gives 4 ERROR/MISSING
nodes. The same file without the split procedure gives 0.

```al
codeunit 50101 X
{
    Permissions = tabledata Customer = r,
#if CLEAN25
                  tabledata Vendor = r;
#else
                  tabledata Item = r;
#endif

#if CLEAN25
    procedure A()
#else
    procedure A(B: Integer)
#endif
    begin
    end;
}
```

Each configuration on its own is ordinary AL: a permissions list, then one procedure. The
failure comes from the interaction between the permissions split, whose `;` sits inside
the arms, and the `preproc_split_procedure` that follows it. It has 0 production sites:
all four corpora parse with 0 errors.

**Owner:** roadmap B7, the separator and continuation audit.

**Before fixing:** probe both configurations with `tools/alc_probe`.

## Longer-lived proposals, tracked separately

- [`python-bindings-modernization.md`](python-bindings-modernization.md) — the
  Python bindings still return a raw pointer via `PyLong_FromVoidPtr`; modern
  `tree-sitter` (0.24+) expects a `PyCapsule`. Written against `tree-sitter==0.25.2`
  as used by `code-graph-rag`.
- [`improvements-for-owned-ir-consumer.md`](improvements-for-owned-ir-consumer.md) —
  proposals from a downstream consumer that lowers the CST into an owned IR, made against
  v3.0.1 (`eeb2839`). **Closed 2026-10-01:** all four issues are fixed; the
  header gives the commits and the evidence. Item 22 is the one consistency follow-up.
- [`history-scanner-token-drop-v3.3.0.md`](history-scanner-token-drop-v3.3.0.md) —
  **historical.** The byte-gap measurement taken against the released v3.3.0 tag
  that started the losslessness work. Kept because the *method* is reusable, not
  because the numbers are current; 4.0.0 fixed the classes it describes.
