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

## 3. The dangling-operator residual — RESOLVED 2026-10-01

**Established:** measured directly; resolved by roadmap B3 (branch
`fix/b3-dangling-operator`). Step 0 found 0 sites of either shape in BC.History, DC,
BC 28.1 and BCApps 29.0.

**Shape 1, an incomplete condition.** `#if FOO and` with the operand on the following
line was absorbed into `condition: (preproc_and_expression FOO BAR)` with zero `ERROR`
nodes; alc rejects it in every configuration (AL0629). The newline terminator could not
fire while the condition was grammatically incomplete. **Fix:** the scanner's
`opener_line_is_malformed` (the B2 check on the rest of an `#if`/`#elif` line) also
refuses a line whose last condition word before any `//` is `and`/`or`/`not`, or whose
parentheses do not balance, so `_malformed_directive` makes the line an ERROR. alc
evidence: `probe_alc.py` `dangling_*`, `unbalanced_*_paren_rejected` and three accepted
controls. The tripwire fixture became
`test/corpus/preproc_dangling_operator_negative_test.txt` (11 deliberate negatives).
**An empty condition is the same class, and B3 at first missed it** (fix round 1, review
I1): `#if`, `#if ` or `#if // c` (or `#elif`) with `A` on the next line parsed clean as
`condition: A`, read across the newline, and alc rejects all four with AL0629 (probe_alc
`empty_*_next_line_rejected`). The earlier note here, that an empty condition "was already
an ERROR", held only when the next line could not be read as a condition, and even then
it was a hidden-only MISSING that `tree-sitter parse` does not show. The check now starts
from "dangling", so a line with no condition word is incomplete. 0 production sites.

**Shape 2, an operator alone in an arm** (found 2026-09-29, A3 review):
`i := 1` / `#if X` / ` +` / `#endif` / ` 2;`. alc: X undefined REJECT (AL0104, AL0111),
X defined ACCEPT, split and flat (`tools/alc_probe/cases/oracle-negative/split-operator.al`).
The parser ERRORed in every configuration. **Fix:** `preproc_conditional_expression_tail`
gained a second form whose arms each hold ONE operator, the operand after `#endif`, through
the hidden complete unit `_preproc_operator_arms`. Same node type, fields and hosts, so the
oracle's `expression_tail` lowering is unchanged; `node-types.json` is byte-identical.
Measured: STATE_COUNT 15,870 -> 15,973 (+0.65%; the same arms spelled inline cost +260),
no new conflict, `tools.perf ab` over DC 24 rounds 1.006 (CI 0.992-1.019). The fixture is
now the positive `test/corpus/preproc_split_operator_test.txt` (4 cases, fields pinned);
the X=0 configuration of its first case is classified `negative` in `fixture-classes.tsv`,
and the `debt(B3)` line is gone. Shape 2 also fixed a silent wrong tree:
`i := 7 #if X mod #endif 2;` (and `xor`) parsed clean with `mod`/`xor` as an identifier
STATEMENT and the operand a loose statement; fixture case 5 pins the tail tree (alc:
probe_alc `split_keyword_operator_*`). An arm mixing the two forms
(`#if X + #else + 3 #endif 2`) still ERRORs; one configuration of it is invalid AL anyway.

## 4. `_expression_statement` accepts any expression as a statement — RESOLVED 2026-10-06

**Resolved by B6** (`8217c85` narrowing and de-inlining, `9dbf281` reserved set `code_names`; evidence `9dcd7c9`,
fixtures `46da22e`, `bb97903`, audit `b576b60`, oracle `be4d14c`, `c74b55e`; spec
`docs/superpowers/specs/2026-10-06-expression-statement-narrowing-design.md`). The rule is an invocation (call,
member, bare or quoted name, `Order`/`Table`) and is no longer in `inline`; the lead below was right. Literal,
unary, operator-led, comparison, parenthesised and subscript statements now ERROR, as alc rejects them (AL0104,
AL0117). STATE_COUNT 23,186 -> 23,213; valid trees byte-identical in BC.History, DC and BC28.1, and in BCApps two
files that already hold an ERROR change their recovery (`docs/b6-audit.md`). Left open: items 39 (B7 gaps) and 40.
The record below is kept as written.

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

## 9. `&&` and `||` in `#if` conditions: the grammar accepts what alc rejects — RESOLVED 2026-10-01

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

**Fixed (roadmap B2, decision 3):** 1d01707 removes both alternatives from
`preproc_or_expression`/`preproc_and_expression` and the `"&&"`/`"||"` captures from
`queries/highlights.scm`. `#if A && B` is now an ERROR in the condition, pinned by two
cases of `test/corpus/directive_line_rejected_negative_test.txt`. The resolver's
`unsupported-condition-token` refusal keeps its classification (fixture-classes.tsv).
Production: still 0 sites in the four corpora; tree-harness: all 15,358 BC.History trees
byte-identical.

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

## 11. A one-pair ML value parses as a comparison (G9) — RESOLVED 2026-10-04

**Resolution (7dea427, c3858ff, roadmap B4):** the compiler's 13 ML names and
`Namespaces` are keyed by name in the scanner (`ML_PROPERTY_NAME`,
`NAMESPACES_PROPERTY_NAME`), like CalcFormula. A one-pair ML value is `ml_value_list`,
flat and in a whole-value `#if` arm with either `;` placement; `Namespaces` is
`namespace_value_list`. The strict xfail below now passes and is no longer an xfail.
Correction to the text below: the keyed set is **the compiler's 13**, read from alc's
own tables, not "every name ending in `ML`" (`FooML`, `CaptionMLX` stay generic).
Spec: docs/superpowers/specs/2026-10-01-pair-list-property-keying-design.md.

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

## 13. Candidate G10: `Visible = Rec.A #if X and B #endif ;` ERRORs — RESOLVED 2026-10-05

**Resolution (e0f9e8c, roadmap B5):** `TableRelation` is keyed by name and a dotted value
of any other property is an expression, so `Visible = Rec.A #if X and B #endif ;` parses as
the expression continued across the `#if`, like the flat `Visible = Rec.A and B;`. Spec:
docs/superpowers/specs/2026-10-04-table-relation-keying-design.md. The text below is the
original finding.

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

## 15. Dotted property references are classified as table relations — RESOLVED 2026-10-05

**Resolution (e0f9e8c, roadmap B5):** correction to the root question below: the compiler
answers it with per-host dispatch. It reaches its relation grammar
(`ParseTableRelationPropertyValue`) through the one property name `TableRelation` and
nothing else, so the fix is the CalcFormula route after all: name-keying that one name
(`TABLE_RELATION_PROPERTY_NAME`), with no neutral node. A relation target is one
`qualified_name`; 14,011 dotted values of other properties became expressions. Spec §2.1.
The text below is the original finding.

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

## 16. `CalcFormula` has no whole-value conditional — RESOLVED 2026-10-05

**RESOLVED 2026-10-05 (roadmap B8).** alc accepts the whole-value `#if` in every shape probed
(`tools/alc_probe/cases/calcformula-conditional`, 10 cases, 48 compiles); a `tableextension`
`modify` host is rejected (AL0171) and gets no grammar. `_calc_formula_value` adds a keyed
conditional (`keyedValueConditional`, arms `value:` `aggregate_formula` / `lookup_formula`, the
ML pattern with an optional arm `;`), `_property_with_terminator_in_if` gains a CalcFormula arm
for the `;`-in-the-arms placement, and an all-empty `#if` before the formula is an unfielded
prefix inside the property. Pinned by `test/corpus/calcformula_conditional_test.txt` and
`tools/config_oracle/tests/test_calcformula_incremental.py`. The text below is the original report.

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

## 20. `#endif;`: the grammar accepts a token after `#endif` that alc rejects — RESOLVED 2026-10-01

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

**Fixed (roadmap B2):** 1d01707. The scanner's `#` dispatch checks the rest of an
`#endif`/`#else` line after `mark_end`: anything but spaces and a `//` comment makes the
line the hidden external `_malformed_directive`, which no rule takes, so it is an ERROR.
The same dispatch rejects prefix forms (`#elsewhere`, `#regionx`, AL0621) and a block
comment on an `#if`/`#elif` line. Pinned now: `tools/config_oracle/probe_alc.py`
`endif_semicolon_rejected`, `endif_trailing_word_rejected`, `else_semicolon_rejected`
(probe_alc.py compiles raw, past the resolver that keeps these out of alc_probe), and
`test/corpus/directive_line_rejected_negative_test.txt`. `#endregion;` stays clean
(`directive_line_accepted_test.txt`, probe `endregion_semicolon_accepted`).

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


## 24. F0 traversal helper: residuals from the final review (fix before the next release)

**Established:** 2026-10-01. These are the final whole-branch review and scoped
re-review of F0 (merge f557dc7). The SDD process allows one fix wave, and the user
chose to merge with these open.

1. **A trailing comment on an `#endif` line is listed in a split node's `shared`.**
   - The same comment on an `#if`, `#elif` or `#else` line is excluded, because
     `split_info` excludes each opener's directive line.
   - Spec §3.3 treats all four directive kinds the same: the masked line includes any
     trailing `//`.
   - Repro: in `tests/traversal/fixtures/cross_node.al`, write `#endif // c-endif`.
     `preproc_split_block_close_after_endif.shared` then lists the comment.
   - Why it matters: `shared` is public API in the next major, so changing it after the
     release is breaking.
   - Fix: in `split_info`, add `(closer.start, line_end(closer))` to the excluded ranges
     in Python, JS and Rust. Add an `#endif // c` case inside an assembler and regenerate
     the expected files.
2. **The CHANGELOG over-claims.**
   - It says the `exports` map "keeps every existing deep path open", and it calls the
     package change "additive".
   - Deep imports that relied on extension or directory lookup no longer resolve.
     `bindings/node` and `traversal` are the exceptions.
   - Fix: add a Changed/breaking line saying that deep imports must name the file,
     extension included.
3. **`docs/traversal.md:65` describes `shared` wrongly.** It says `shared` lies "outside
   every directive line". Correct it together with point 1.
4. **Nit: the dedupe snippet in `docs/traversal.md`** calls `collect(v.node, None)`, so a
   piece walked before its `SplitInfo` loses its arm attribution. Use `v.arms`.

These were parked as polish, with no dependent work:
- Rust `Policy` has no `alias_to` accessor.
- The runtimes raise different error types for a malformed policy, and all three accept
  an empty policy.
- A node from another tree is accepted silently.
- API naming differs beyond what the docs table covers.

**Owner:** E1/E3 release gating. Points 1–3 must be fixed before the next major is
published.

## 25. `#if not A and B` grouped as `not (A and B)` (roadmap B1) — RESOLVED 2026-10-01

**Established:** 2026-09-28 (grep, all four corpora) and reproduced at 6b3ee0b:
`preproc_not_expression` had no precedence, so the tree read `not (A and B)` where alc
reads `(not A) and B` (`docs/preproc-directive-semantics.md`, probes `prec_*`). A silent
wrong tree: no ERROR, and no gate looked at condition grouping.

**Fixed:** 81076bf makes `not` `prec(3)`, above `and` (2) and `or` (1). STATE_COUNT
15870 before and after, no new conflict. Production impact re-measured: 0 `not X and/or Y`
sites in the four corpora; tree-harness over BC.History: all 15,358 trees byte-identical.
`test/corpus/preproc_condition_precedence_test.txt` pins 11 cases (4 failed before), and
`lossless_keyword_nodes_test.txt`, which asserted the defect, was corrected by hand.

**Gated:** 9733550 adds the config oracle's condition-structure stage, which evaluates the
tree's grouping per configuration against the resolver's. The B1 review (I1) showed that a
truth table alone is blind under an in-file `#define` (`#define B` above `#if not A and B`:
every reached configuration evaluates both groupings alike), so the stage also requires the
tree's condition AST to equal the resolver's, parentheses dropped. Replays 7 and 8
(81076bf^, 8 is that `#define` case) catch the old grammar; gate_selftest `oracle-quick-condition-structure` and
`step5e-oracle-condition-structure` revert the prec and go red.

## 26. A directive after code on the same line parses clean; alc rejects it (AL0620)

**Established:** 2026-10-01, B2 fix-round-2 re-review (N1), against 675e626 and 39626c7
(same behaviour at both, so not a B2 regression). alc 18.0.41 verdicts:

| input (in a trigger body) | alc | parser |
|---|---|---|
| `Message('t'); #if A` | REJECT AL0620 (probe `if_after_code_rejected`) | clean |
| `#if A` / `Message('b'); #endif` | REJECT AL0620 (probe `endif_after_code_rejected`) | clean |
| `Message('t'); #else`, `…; #region R`, `…; #pragma …` | REJECT, same rule (re-review's own compiles) | clean |

`docs/preproc-directive-semantics.md`'s first "Directive lines" row: a directive must be
the first token on its line.

**Why B2 does not catch it:** the scanner's `#` dispatch decides from the directive word and
the REST of its line. At a `#` it cannot see what started the line, because the scanner
holds no column or "line has code" state and tree-sitter hands it no context. It needs
its own design: for example a serialized "last token ended on this line" flag, or a check in
the token BEFORE the `#` (every statement terminator would have to look ahead), and both
change the scanner's state contract.

**Production impact:** 0 sites in BC.History, DC, BC 28.1 and BCApps 29.0 (grep for a
directive word after non-blank, non-`//` text on a line, excluding `#` inside quoted
strings and the BOM-prefixed first line; 2026-10-01).

**Sibling, fixed in B2 fix round 2:** a second directive on an `#if`/`#elif` line
(`#if A #region R`, `#if A #pragma …`, `#elif A #region R`; AL0631) parsed clean too. The
dispatch now refuses any `#` before a `//` on an opener line (`opener_line_is_malformed`);
pinned by three cases of `test/corpus/directive_line_rejected_negative_test.txt`.

**Owner:** unassigned (a B-row candidate). A fix must add AL0620 negatives and keep
`#endregion;`, trailing `//` comments and indented directives clean.

## 27. `identifier` has two shapes: a `TableData` option member keeps an anonymous `"tabledata"` child

**Established:** 2026-10-01, by the shape census added on `chore/workflow-tools`
(`python tools/snip.py --census --root DIR`, which flags any `*_keyword`/`*identifier` type
with more than one `(named, anonymous)` child shape):

| root | `identifier` named=0 anon=0 | named=0 anon=1 | exit |
|---|---|---|---|
| BC.History | (one shape) | 0 | 0 |
| DC | 399,599 | 5 | 1 |
| BCApps-29.0 | 17,762,156 | 1 | 1 |
| BC28.1 | (one shape) | 0 | 0 |

Every one of the 6 is an option member spelled `TableData`, in a variable's
`Option TableData,"Table",Form,…` (DC: `CDCCaptureEngine.Codeunit.al:25`,
`CDCCaptureUIHandling.Codeunit.al:42`, `CDCContiniaLicenseMgt.Codeunit.al:13` and `:63`,
`CDCSustainabilityMgt.Codeunit.al:41`) or an `OptionMembers = TableData,…` property
(BCApps: `Layers/NL/BaseApp/Local/Bank/Reconciliation/ImportProtocol.Table.al:27`).

**Cause:** `option_member` reaches `tabledata_keyword` through `alias(…, $.identifier)`, and
`tabledata_keyword` is `alias(kw('tabledata'), 'tabledata')`, so the aliased "identifier"
keeps the visible anonymous `"tabledata"` child. Every other `identifier` is a leaf. That is
the two-shape defect `.claude/rules/contextual-keywords.md` forbids ("demote the named ones"
for an outer node that claims to be an `identifier`). The comment above `tabledata_keyword`
in `grammar.js` (around lines 1616-1633) calls the child deliberate ("merely gives it the
anonymous "tabledata" child"). It argues that one rule must serve both sites to avoid two
competing reductions, which is a constraint on the fix, not a reason for the shape.

**Also to correct with the fix:** CLAUDE.md ("`_tabledata_keyword` is deliberately
excluded: it is a *hidden* … token helper") and `.claude/rules/contextual-keywords.md`
("`_tabledata_keyword` is not in these counts: it is a *hidden* … token helper") describe a
rule that no longer exists. It is the visible `tabledata_keyword` now, and the
`option_member` use is exactly this defect.

**Owner:** roadmap B (grammar correctness). A fix must keep `Permissions = tabledata X = R`
and `OptionMembers = TableData,…` both clean, and end with the census at 0 flagged on all
four roots.

## 28. `Visible = Where;` ERRORs

**Established:** 2026-10-05, found in the B5 Task 4 review. Pre-existing at the B4 merge
(`6b15b9b`) and not caused by B5.

A property value that is the single word `where` ERRORs: `where_keyword` wins the lexer at
value start, where no keyword can be an identifier in the generic value position, so the
word never becomes an `identifier`. Whether alc accepts `Visible = Where;` was not probed.

**Production sites:** 0 in all four corpora, measured with
`./tools/corpus-grep.sh -P -i -c '^\s*\w+\s*=\s*where\s*;'` (BC.History, DC, BC28.1,
BCApps-29.0: 0 lines, 0 files each).

**Owner:** unassigned. Probe alc first (`python -m tools.alc_probe`); if accepted, fix by
reserved-word handling at value start, as B5 did for `_qualified_name_segment`.

## 29. Four `TableRelation` shapes with `#if` inside the chain ERROR

**Established:** 2026-10-05, found in the B5 final review with `python tools/snip.py --raw`
inside a table field. Not B5 regressions (the shapes ERROR the same way before B5). alc
validity was not probed. Production sites: 0.

| shape (`TableRelation = ...;`) | tree today |
|---|---|
| `if (A = const(X)) Item #if X else if (A = const(Y)) Vendor #endif else Customer` | ERROR on `else Customer` (mid-chain `#if` plus a shared `else`) |
| `Customer #if X where(A = const(1)) #endif` | one ERROR spanning the whole value |
| `#if X Item #else Resource #endif where(A = const(1))` | one ERROR spanning the whole value |
| `if (A = const(X)) #if X Item #else Vendor #endif` | ERROR on `#if X` and on `#else Vendor #endif;` |

**Next step:** the four-way alc probe (`python -m tools.alc_probe run`) on each shape; fix
only the ones alc accepts.

**Owner:** unassigned.

## 30. A trailing comma in a link list is accepted (`RunPageLink = A = field(B),;`)

**Established:** 2026-10-05, B5b. alc 18.0.41 REJECTS it (AL0104, AL0107, AL0292; probe
`tools/alc_probe/cases/link-keying/decide-trailing-comma.al`). The grammar accepts it as a clean
`link_value_list` (`_link_value_run`'s `optional(',')`, the separator placement). Production sites
in the link properties: 0 (`./tools/corpus-grep.sh -P -i -c '(SubPageLink|RunPageLink|LinkFields|DataItemTableFilter|ColumnFilter|DataItemLink)\s*=[^;]*,\s*;'`, single-line form).

**Next step:** roadmap B7 (separator audit), with the comma-leading link list it already carries.

**Owner:** B7.

## 31. `filter((1|2)&3)` ERRORs — RESOLVED 2026-10-06

**Resolved by `4c61c96`** (evidence `43b824a`, `tools/alc_probe/cases/deferred-31-32-34`). `filter_value` gains a recursive
`filter_group` (`(` `filter_value` `)`), shared by the link and `where` hosts; unbalanced parentheses stay an ERROR, as alc
rejects them (AL0104). The record below is kept as written.

**Established:** 2026-10-05, B5b. alc ACCEPTS `RunPageLink = Amount = filter((1|2)&3);` (probe
`decide-filter-parenthesized.al`). `filter_value` has no parentheses, so the grammar ERRORs; the rule
is shared with `where_clause`, so a fix covers both hosts. Production sites: 0
(`./tools/corpus-grep.sh -P -c 'filter\s*\(\s*\('`).

**Next step:** parenthesised groups in `filter_value`, checked against both hosts.

**Owner:** unassigned.

## 32. `chartpart` has no grammar rule — RESOLVED 2026-10-06

**Resolved by `4c61c96`.** `chartpart_section` (fields `name`, `source`) and `chartpart_keyword` join `_layout_element`
beside `part`/`systempart`. alc rejects chartpart in a repeater (AL0376), a host rule the parser does not enforce, as for `part`.
`chartpart` is reserved in alc (AL0104 as a name) but still parses as an identifier, unchanged. The record below is kept as written.

**Established:** 2026-10-05, B5b. A bare `chartpart(C; "Sales Chart") { }` in a page layout is ERROR in
the grammar (pre-existing, not a B5b regression). alc ACCEPTS it (probe in the B5b Task 6 session:
split and flat ACCEPT on alc 18.0.41; committed as `tools/alc_probe/cases/link-keying/decide-chartpart-bare.al`). `SubPageLink` inside a chartpart is rejected by alc (AL0171,
`tools/alc_probe/cases/link-keying/decide-chartpart-subpagelink.al`), so that is not the reason to add it. Production sites: 0
(`./tools/corpus-grep.sh -P -i -c '^\s*chartpart\s*\('`).

**Next step:** a `chartpart` rule beside `part`/`systempart`, with the hosts the compiler allows.

**Owner:** unassigned.

## 33. A generic property whose value follows an empty `#if` block parses clean, with the wrong shape — RESOLVED 2026-10-06

**Resolved by B11** (`de14527`, `ee410df`, `1a7caaa`, `4d6f6dd` generic, Permissions and Implementation, including a nested
empty prefix; `fbeb24b` ML; `33e1b49` Namespaces, TableRelation, CalcFormula). An empty `#if` before the value is a
decoration of the value in every family: a value plus an unfielded prefix, one property. Spec
`docs/superpowers/specs/2026-10-05-property-value-runs-design.md` 3.4. The record below is kept as written.

**Established:** 2026-10-05, B5b. `Visible =` / `#if X` / `#endif` / ` false;` in a page field is
ACCEPTED by alc for both X assignments (split and flat). The grammar gives no ERROR but the value is an
`option_member_list` holding a `preproc_conditional_option_members` (the empty `#if ... #endif`) and an
`option_member (boolean)`: the generic `_in_if` route reads the empty prefix as a split list, not as
a transparent block before one value. Same family as the B5b G11 empty-prefix shapes, which the keyed
link rules handle. Production sites: 0 in all four corpora (a multi-line scan for
`Name =` followed by `#if` and an immediate `#endif`/`#else`/`#elif`). Probe:
`tools/alc_probe/cases/link-keying/decide-generic-empty-prefix-visible.al` (accept, X=0 and X=1, split and flat).

The milder-looking `Visible` case is the `option_member_list` shape. The same pattern under
`Implementation` is worse, a silent split into TWO properties, `has_error` False, identical at the
pre-B5b base library: `Implementation =` / `#if X` / `#endif` / `IFoo = FooImpl;` in an enum value
parses as a `property` `Implementation` whose value is an empty `preproc_conditional_property_value`,
followed by a separate `property` named `IFoo`. alc ACCEPTS it for both X assignments, split and flat
(`tools/alc_probe/cases/link-keying/decide-generic-empty-prefix-implementation.al`). Production sites: 0
(`./tools/corpus-grep.sh -P -i` for a line ending in a link-family name or `Implementation`, 16 hits over the four
corpora, none followed on the next line by `#if`).

**Also, observed in B8 (2026-10-05), not probed:** `CaptionML =` / `#if X` / `#endif` / ` ENU='a';`
splits silently the same way, the ML keyed conditional (B4) allowing all arms absent: a `property`
whose value is the empty conditional, then a property `ENU`. CalcFormula (B8) does not split: its
keyed value takes an all-empty `#if` as an unfielded prefix inside the property, a template for the
keyed families here.

**Next step:** decide with an alc four-way probe whether the generic value should treat an empty
arm as transparent; fix only if a production shape needs it.

**Owner:** unassigned.

## 34. `where(B = const(-1))` ERRORs — RESOLVED 2026-10-06

**Resolved by `4c61c96`.** `where_condition`'s const value is `_const_numeric`, as in a link's const, so `const(-1)`,
`const(1.5)` and `const(1000L)` parse, a signed number as one `unary_expression`. The record below is kept as written.

**Established:** 2026-10-05, found in the B5b Task 3 review; pre-existing. `where_condition`'s `const`
takes no signed number, so `TableRelation = Cust."No." where(Amount = const(-1));` ERRORs on the `-1`.
alc ACCEPTS it (probe `tools/alc_probe/cases/link-keying/decide-where-const-negative.al`, split and flat). Link `const` arguments were fixed
in B5b; the `where` const was not. Production sites: 0 (`./tools/corpus-grep.sh -P -i -c 'where\s*\([^)]*=\s*const\s*\(\s*-'`).

**Next step:** reuse the `_const_negative` rule in `where_condition`'s const.

**Owner:** unassigned.

## 35. Two sequential conditionals forming one link value split silently — RESOLVED 2026-10-06

**Resolved by B11** (`fbeb24b`). The unquoted reproducer below is now one `SubPageLink` property whose value is a
`preproc_conditional_property_value_sequence` of two `link_value_list` groups, `has_error` False. The quoted form
(`"No." = field(B)`) ERRORed at the base library and is the same tree now (spec 1, 2.2). Both measured on 2026-10-06.
The record below is kept as written.

**Established:** 2026-10-05, B5b final review; pre-existing, the same tree at the pre-B5b base
library. Both conditionals are valid AL in every configuration (alc ACCEPTS X defined and undefined,
split and flat: `tools/alc_probe/cases/link-keying/decide-two-conditionals-one-link.al`):

```al
SubPageLink =
#if X
    A = field(B);
#endif
#if not X
    A = field(C);
#endif
```

At HEAD, `has_error` is False and the tree is silently wrong: the `SubPageLink` property holds a
`preproc_conditional_property_value` with the first arm's `link_value_list`, and the second `#if not X`
arm becomes a separate `preproc_conditional` holding a `property` `A` whose value is a
`property_expression` (`field(C)`, a call). The spec 3.2 witness covers the shapes it names
(nested, nested-after, nested-mixed, empty-prefix, exhaustive-elif-not, independent-no-else) but not
this third shape, a second, separate conditional continuing a value the first one opened.
Production sites: 0 (the oracle full tier is clean; a scan of every link-family name ending a line
with `=`, 16 hits over four corpora, none followed by `#if`).

**Next step:** decide whether a conditional after a conditional-terminated link value continues it,
with an alc four-way probe, in the link rules (`_link_whole_conditional_in_if`).

**Owner:** unassigned.

## 36. Configuration-dependent property boundaries (roadmap B12)

**Established:** 2026-10-06, B11 (spec 3.4 and the revision 1 blocker). alc does not parse inactive arms, so where a property
ends can depend on the configuration:

```al
Visible =
#if X
    true;
#endif
#if X
    Caption = 'x';
#else
    false;
#endif
```

X defined is `Visible = true; Caption = 'x';`, two properties. X undefined is `Visible = false;`, one. No single tree is every
configuration's flat tree. The grammar reads a run as one value (a sequence), the only reading under which every arm parses,
so the tree is exact for the configurations consistent with that reading and the oracle refuses the others.

**Continuation absorption** (spec 3.4 amendment 7) is the same residue seen from the other side. A non-terminated `;`-inside
group followed by a conditional block whose arms also parse as properties is read as a continuation of the value:
`Caption = #if X 'a'; #endif #if Y Editable = false; #endif` is one sequence, and the complementary three-group run
(`Caption = #if X 'a'; #endif #if not X 'b'; #endif #if Y Visible = true; #endif`) one three-group sequence. That is a
one-reading guess, wrong in the Y=1 configurations (there the earlier group already ended the property, and the last group
is a property of its own); it is chosen because without condition evaluation it cannot be told from the ML and link
continuations B11 fixes (`ENU='b';` parses as a property too).

**Evidence:** alc accepts each configuration flat (`tools/alc_probe/cases/value-runs/boundary-complementary-three.al`,
`boundary-mixed-after.al`, `boundary-visible-caption.al`: accept in every configuration;
`continuation-absorption-editable.al`: accept with X defined). Fixtures:
`test/corpus/property_value_run_test.txt` ("configuration-dependent boundary (spec 3.4)", the complementary three-group run),
`test/corpus/property_value_run_review_test.txt` (the `Editable` absorption case).
Oracle, debt(B12) records in `tools/config_oracle/fixture-classes.tsv` (`production-classes.tsv` has none, since the corpora
hold no such site), never a discrepancy:
- **2 hook records (b1).** A `;`-inside site whose configuration selects no terminator (`Caption = #if X 'a'; #endif #if Y
  #endif ;` at X=0, which lowers to `Caption = ;`) is refused by the property-level hook `_check_site_boundary` in
  `tools/config_oracle/lowering/engine.py` as `lowering:one-reading`. The hook decides from the selection: a selected
  terminator that does not end the property is `contract-shape`, a lowering defect, never this debt.
- **4 `value_run_select` records.** A second value, or a value after a selected terminator, in a sequence
  (`assemblers.value_run_select`): the Visible/Caption boundary (X=1), the complementary three-group run (X=0,Y=1 and
  X=1,Y=1; reason "one-reading guess, wrong in Y=1 configurations") and the `Editable` absorption (X=1,Y=1).
Ruling-1 configurations (a terminated group, an empty block, then `;`) are `invalid-config` instead: the oracle refuses them as
`reference-error` and alc rejects them (AL0104, AL0124).

**Alternatives considered:**
- **Condition text in the scanner.** The scanner would evaluate `X`/`not X` to decide where a property ends. Rejected: the
  grammar has no symbol table, `#define` is per file and configuration is external input, so the tree would depend on
  something the parser does not have.
- **A multi-configuration tree.** One tree per configuration, or a tree holding every boundary. That is roadmap F1 (the
  representation decision, A7), not a grammar change.

**Next step:** decide with F1. Until then the sequence is a one-reading construct and the refusals stay classified.

**Owner:** unassigned.

## 37. Conditional value fragments (roadmap B13)

**Established:** 2026-10-06, B11. A run whose groups are fragments of ONE value, not alternative values, cannot be told from the
generic union without prefix/suffix-compatible states over the whole `_property_value` (spec 3.1 step 5). These shapes are valid AL
(alc accepts X defined; the X undefined configuration leaves `N = ;` and is rejected for some) and stay visible ERRORs. Every one
is a case in `test/corpus/property_value_run_b13_gap_test.txt` (10 cases), pinned as an ERROR with its probe in
`tools/alc_probe/cases/value-runs/`:

| shape | probe |
|---|---|
| generic `Caption`, two groups, `;` after the last `#endif` | `caption-seq-after.al` |
| RunObject `Page` then `CustList` across groups | `b13-runobject-page-p.al` |
| call `Format` then `(1)` | `b13-call-f-paren.al` |
| decimal range `0 :` then `5` | `b13-decimal-range.al` |
| SourceTableView `sorting()` then `where()` | `b13-sorting-where.al` |
| ML pairs joined by `,` across groups | `b13-ml-pairs-comma.al` |
| Namespaces pairs joined by `,` across groups | `b13-namespaces-pairs-comma.al` |
| Caption `'a',` then `Locked = true` | `b13-caption-locked.al` |
| comma-free `OptionMembers` alternatives, `;` after (`#if X A #endif #if not X B #endif ;`) | `b13-optionmembers-comma-free.al` |
| ML conditional terminator (`#if X ENU='a' #else ENU='b'; #endif #if X #if Y #endif ; #endif`) | `b13-ml-conditional-terminator.al` |

Also not supported, outside the gap file:
- **Bare `;` arms.** alc accepts `CaptionML = #if X ; #else ENU='a'; #endif` and the Namespaces equivalent in every
  configuration (an empty ML or Namespaces value is valid; `bare-semi-arm-captionml.al`, `bare-semi-arm-namespaces.al`), and
  the grammar does not admit an arm holding only `;` (it ERRORs). Every other family rejects the active bare-`;` arm, so only
  ML and Namespaces are gaps.
- **A `,` after a conditional member, outside the group.** `OptionMembers = #if X A #endif , B;` ERRORs; alc accepts both
  configurations (`b13-optionmembers-trailing-after-comma.al`).

The comma-free `OptionMembers` form is a spec 3.1 step-3 deviation: `OptionMembers` reaches the grammar through the generic
`_property_value`, so without the property name the run cannot be told from the generic step-5 run. Keying `OptionMembers` by name
in the scanner would lift it, as it did for the five other families.

The arm-site shape of a nested group, a decoration, then `;` is NOT a gap: it parses and is pinned
(`nested-empty-semi-arm-*.al` probes, accepted for the configurations where the arm is not active).

**Deferred by the controller (B11 final review, Minor 1): `OptionMembers` adjacency over-acceptance.**
`OptionMembers = #if X A, #endif #if Y B, #endif C D;` parses clean at head (an ERROR at the base library) although it is
invalid AL in every configuration (`C D` are two members without a separator). The structural over-acceptance comes from the
entirely conditional `OptionMembers` form (spec 3.1 step 3). The oracle catches it: every configuration's flat parse ERRORs, so
each is `reference-error:error`, never a silent pass (measured 2026-10-06; no fixture, 0 production sites). Keying `OptionMembers` by name (above) is where it would be fixed.

**Next step:** a generic prefix/suffix-compatible value state set, or per-family keying, whichever the state budget allows (D1 first).

**Owner:** unassigned.

## 38. An all-comma conditional `OptionMembers` run reads as a `tabledata_permission_list`

**Established:** 2026-10-06, B11 precedence audit. `OptionMembers = #if X , #endif #if Y , #endif ;` parses as a
`tabledata_permission_list` of two `preproc_conditional_permissions`. The reading is pre-existing (the base library gives the
identical tree, controller A/B) and the text is invalid AL in every configuration (alc AL0153,
`optionmembers-blank-slots-only.al`). It is pinned in `test/corpus/property_value_run_audit_test.txt` as a change detector for the
`prec.dynamic(-1)` that preserves base trees, and not endorsed. Production sites: 0.

**Next step:** none required; revisit if `OptionMembers` is keyed by name (item 37), which would remove the ambiguity.

**Owner:** unassigned.

## 39. Two valid split shapes that B6 made a loud ERROR (roadmap B7)

**Established:** 2026-10-06, B6. Both are valid AL in every configuration, parsed clean and wrong before B6, and ERROR
since:

1. A repeat-until condition continued by a keyword-operator `#if` arm: `repeat Foo(); until C` / `#if X` / `and (C)` /
   `#endif` / `;`. Before B6 the continuation read as a call to a function named `and`; `code_names` now reserves the
   word. alc accepts both configurations (`tools/alc_probe/cases/expression-statement/torn-until-and.al`).
   `repeat ... until` has no continuation facility.
2. An assignment continued with `;` inside every arm: `B := A` / `#if X` / `+ 1;` / `Foo();` / `#else` / `;` /
   `#endif`. Before B6 `+ 1` was a unary statement; a statement is now an invocation. alc accepted both configurations
   (B6 Task 4 split probe, not committed). The assignment's tail takes only `;`-after-`#endif` arms.

Pinned in `test/corpus/expression_statement_b7_gap_test.txt` (listed in `tools/deliberate-negatives.txt`) and in the
`B7_GAP` list of `tools/config_oracle/tests/test_expression_statement.py`; the oracle classifies both `debt(B7)`.
Production sites: 0 (tree-harness over the four corpora shows no valid tree changed).

**Next step:** B7 gives both hosts a continuation, moves the two cases to a positive fixture, and inverts
`test_b7_gap_is_loud_not_silent` (has_error must become False).

**Owner:** B7.

## 40. A bare parenless call has two shapes: `Bar;` and `Order;`

**Established:** 2026-10-06, B6 Task 4; pre-existing, not changed by B6. `Bar;` parses as
`(call_statement function: (identifier))`, but `Bar` before `end` (no `;`) and `Order;` give a bare `(identifier)`
statement: `call_statement` takes only identifier and quoted-identifier tokens, and `Order` arrives through
`_value_start_keyword_name`. Pinned in `test/corpus/expression_statement_test.txt` as current behaviour, not a contract.

**Next step:** pick one shape for "a bare name as a statement" and route every arm to it.

**Owner:** unassigned.

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
