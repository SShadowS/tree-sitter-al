# BC 29 parse gaps (microsoft/BCApps releases/29.0)

**Status:** families A, B, C, F and I RESOLVED (move* lists; move* in actions;
nested `#if` among fields and keys; split routine body; split argument list and
split Permissions head); E partly (split key and modify headers; EDocumentDE's
nested open headers remain); D (field body opened in #if, closed after #endif)
; G (branches ending in an open statement prefix, one general rule) — BCApps
29.0 error files 33 -> 5. Remaining: E (EDocumentDE), H; J is invalid source. ProdOrderComponent.Table.al still fails, on H.
Corpus: `H:/Git/BCApps-29.0` (shallow clone of microsoft/BCApps
`releases/29.0`, commit e16d6c30, 36,716 .al files, includes BaseApp layers).
This analysis was produced by root-cause bisection of every failing file; the
reproducers and alc probes it cites were run on 2026-09-28.

---

# BC 29.0 (BCApps releases/29.0) parse-failure analysis

Corpus: `H:/Git/BCApps-29.0`, 36,716 `.al` files, 33 with ERROR/MISSING (99.91%).
Grammar: `U:\Git\tree-sitter-al` at `df0e5b5` (main). Research only, nothing in the repo edited.

## Method

- **First-error dump** of all 33 with py-tree-sitter (`scratchpad/errs.py` -> `first.txt`).
- **#if isolation** (`scratchpad/iso.py`). Keep one top-level `#if` group verbatim, flatten every
  other group to one branch, and report the groups that still error on their own. That
  finds the root group even when recovery reports the error at line 1.
  `scratchpad/flat.py` does the reverse: it resolves one group and reports whether the
  whole file comes out clean.
- **Substitution check** (`scratchpad/sub.py`). Rewrite the suspected construct in memory and
  confirm the error count drops to 0. Used for the move-list family: all 9 files go 1 -> 0.
- **Minimal reproducers** in `scratchpad/r/*.al` and `scratchpad/alc/p_*.al`. Every `p_*`
  probe file also errors in tree-sitter (checked).
- **alc probes**: `scratchpad/alc/probe.sh <file> <runtime> [symbols]`. The project has no
  application or dependencies keys. The installed `al` is 18.0.41 and supports runtimes
  15.0-18.0 (19.0 and 20.0 give AL1043). Sanity probe accepted; two negative move probes
  rejected with AL0104 and AL0270, so the probe discriminates.
  - Every `#if` probe was compiled with its symbol **undefined and defined** (split file,
    both configs). alc does not parse inactive branches, so each split config is the flat
    text of that branch. The flat pair of the four-way rule is therefore implied, not run
    separately.

## Summary table

| # | Family | Files | New syntax? | Effort |
|---|---|---|---|---|
| A | `move*` with a **list** of controls | 9 | No (alc runtime 15.0 accepts) | Low |
| B | `move*` inside pageextension `actions` | 1 | No (runtime 15.0 accepts) | Low |
| C | Nested `#if` directly among `fields` | 3 (+1 shared) | Placement | Low |
| F | Split routine body: trigger host / `#else` branch has statements | 2 | Placement | Low |
| I | Split comma lists (argument list, `Permissions =` head) | 3 | Placement | Low-Med |
| E | Split section **header**, shared body (`modify`/`add*`/`key`) | 3 | Placement | Medium |
| D | Field `{` opened inside `#if`, closed after `#endif` (one-config-valid) | 3 | Placement, **invalid in the other config** | Medium |
| G | Branch ends in an open statement prefix (`if..then`, `..else`, `else begin`) | 5 | Placement | Med-Hard |
| H | Branch closes an enclosing construct and reopens a sibling | 2 (+1 shared) | Placement | Hard |
| J | Source genuinely invalid (missing `end;`) | 1 | n/a, not a parser bug | None |

Total: 9+1+3+2+3+3+3+5+2+1 = 32, plus ProdOrderComponent.Table.al, which needs both C and H = 33.

**None of the 33 is new BC 29 language syntax.** A and B are old syntax that no earlier
corpus used, and the rest are new `#if` placements in the localized layers (IT, FR, NO, GB,
ES, IN, CZ, DE) plus one W1 file.

---

## A. `move*` with a list of controls (9 files)

Reproducer (errors):
```al
pageextension 50101 E extends P { layout { moveafter("Address 2"; City, CountyGroup) } }
```
- **Grammar:** `grammar.js:2254-2288`. `movefirst/movelast/moveafter/movebefore_modification`
  take exactly one `field('element', $._identifier_or_quoted)`, so the `,` is an ERROR.
- **alc:** `moveafter(A; C, B)`, `movefirst(G; C, B)`, `movelast(G; A, B)` and
  `movebefore(A; C, B)` all ACCEPT at runtime 15.0, 17.0 and 18.0 (`alc/mv_*.al`).
  Negative controls: `moveafter(A; C B)` gives AL0104 "',' expected"; `moveafter(A; Nope)`
  gives AL0270. This is old syntax that simply appears for the first time in this corpus.
- **Files:**
  - `Apps/CZ/BankingDocumentsLocalization/app/Src/PageExtensions/BankAccountCardCZB.PageExt.al` (movelast)
  - `Apps/CZ/CoreLocalizationPack/app/Src/PageExtensions/GeneralLedgerSetupCZL.PageExt.al` (movefirst)
  - `Apps/FR/PaymentManagementFR/app/src/PageExtensions/BankAccountCard.PageExt.al` (moveafter, 4 controls, inside `#if CLEAN28`)
  - `Apps/GB/IdealPostcodes/app/ext/IPCBankAccountCard.PageExt.al`
  - `Apps/GB/IdealPostcodes/app/ext/IPCContactAltAddressCard.PageExt.al`
  - `Apps/GB/IdealPostcodes/app/ext/IPCLocationCard.PageExt.al`
  - `Apps/GB/UKPostcodeGetAddressIO/app/src/PageExt/BankAccountCard.PageExt.al`
  - `Apps/GB/UKPostcodeGetAddressIO/app/src/PageExt/ContactAltAddressCard.PageExt.al`
  - `Apps/GB/UKPostcodeGetAddressIO/app/src/PageExt/LocationCard.PageExt.al`
- **Verified sole cause:** rewriting the list to its first element takes every file from 1 error to 0.
- **Fix direction:** make the element a comma list in all four rules. The
  `field('element', …)` + `repeat(seq(',', field('element', …)))` form keeps the field name
  and repeats it, which is less churn for consumers than a new list node. Consider one shared
  hidden `_move_args` so the four rules cannot drift. B also needs this.
  `tools/check-field-types.py` needs updating if `element` becomes multiple.

## B. `move*` in pageextension `actions` (1 file)

Reproducer (errors):
```al
pageextension 50101 E extends P { actions { movebefore(Submit_Promoted; Generate_Promoted) } }
```
- **Grammar:** the move rules are referenced only from the layout element choice
  (`grammar.js:1995-1998`). `_action_element` (`grammar.js:2300-2321`) has
  `add*_action_modification` and `modify_action_modification` but no move.
- **alc:** `movebefore(X; Z)` and `movebefore(X; Z, Y)` in `actions` both ACCEPT at 15.0, 17.0 and 18.0 (`alc/mv_actions*.al`).
- **File:** `Apps/CZ/CoreLocalizationPack/app/Src/PageExtensions/VATReportCZL.PageExt.al:188`.
  Deleting that one line takes the file to 0 errors. The first ERROR spans the whole
  `actions` section (69-247), so the reported location is far from the cause.
- **Fix:** add the four move rules, list-capable after A, to `_action_element`.

## C. Nested `#if` directly among table fields (3 files + ProdOrderComponent) — RESOLVED

Reproducer (errors):
```al
table 50100 T { fields {
#if not S31
#if not C28
    field(2; B; Integer) { }
#endif
    field(3; C; Integer) { }
#endif
} }
```
- **Grammar:** `preproc_conditional_fields` (`grammar.js:1563-1575`). Its branches accept only
  `field_declaration | attribute_item | modify_modification`, not itself.
  `preproc_conditional_keys` (1611) has the same gap, which is latent: `r/keysnest.al` errors
  and no file hits it yet. `preproc_conditional_fieldgroups` (1665) already recurses. Page
  layout and actions nesting parse fine.
- **alc:** `alc/p_nested_fields.al` ACCEPTs with symbols undefined and with `S31,C28` defined.
- **Files:**
  - `Layers/IT/BaseApp/Manufacturing/Document/ProdOrderRoutingLine.Table.al:797`
  - `Layers/IT/BaseApp/Purchases/Archive/PurchaseLineArchive.Table.al:1146`
  - `Layers/IT/BaseApp/Purchases/Document/PurchaseLine.Table.al:4058`
  - `Layers/IT/BaseApp/Manufacturing/Document/ProdOrderComponent.Table.al:942`, which also has H
- **Fix:** add `$.preproc_conditional_fields` to its own three branch choices, copying
  fieldgroups. Do the same for keys. This is a generic host change and needs no split rule.

## D. Field body opened inside `#if`, closed after `#endif` (3 files) — RESOLVED

Reproducer (errors):
```al
table 50100 T { fields {
    field(1; A; Integer) { }
#if not S31
    field(2; B; Integer)
    {
        Caption = 'X';
#endif
    }
    field(3; C; Integer) { }
} }
```
- **Validity:** this text is valid **only with the symbol undefined**. alc/p_field_open.al:
  undefined ACCEPT, `S31` REJECT (AL0104 "'}' expected", AL0198). The FixedAssetShift
  variant with a trailing trigger (`alc/p_field_open_trigger.al`): undefined ACCEPT,
  `CLEANSCHEMA26` REJECT (AL0104, AL0162). So Microsoft ships files that do not compile in
  their own CLEANSCHEMA configuration. They are removed-field schema blocks that nobody
  builds clean.
- **Grammar:** `preproc_split_table_field` (`grammar.js:2145`) needs the whole header list
  and `#endif` *before* the `{`. `preproc_conditional_fields` needs complete fields.
- **Files:**
  - `Apps/IN/INFADepreciation/app/src/table/FixedAssetShift.Table.al:195`: header plus
    properties in `#if`, and `trigger OnValidate … }` after it.
  - `Apps/W1/SalesOrderAgent/app/src/Setup/SOASetup.Table.al:28`: nested property `#if` inside the open body.
  - `Layers/FR/BaseApp/Bank/BankAccount/BankAccount.Table.al:1032`: three fields, the last field's `}` after `#endif`.
- **Fix direction:** a dedicated rule, say `preproc_split_table_field_open`:
  `#if <fields>* field-header '{' <declaration_body items>* #endif <declaration_body items>* '}'`.
  Only the `#if`-taken reading exists, so the tree is unambiguous. It is the table-field
  analogue of `preproc_split_code_block_over_endif`. Medium effort. The fixture must pin that
  only one config is valid, and must not claim the other is.

## E. Split section header with a shared body (3 files)

Reproducers (all error):
```al
// ServiceCreditMemoES (layout)
#if not C27
        modify("A")
#else
        modify("B")
#endif
        { Caption = 'C'; }
// ItemLedgerEntry: the branch has complete keys, then a trailing header
#if not C28
        key(K2; B) { }
        key(K3; B, A)
#else
        key(K2; B, A)
#endif
        { }
// EDocumentServiceDE: two nested open headers per branch, with properties
#if not C27
        addafter(G) { group(Export) { Caption = 'E';
#else
        addlast(H) { group(BuyerReference) { ShowCaption = false;
#endif
            field(F; Rec.A) { } } }
```
- **alc:** `p_modify_split`, `p_key` and `p_addsplit` all ACCEPT in both configs. The key
  probe needed non-PK-prefixed fields: AL0260 is a semantic rule and was first mistaken for a
  rejection. The simple `addafter(A) #else addlast(B) #endif {…}` (`r/ed2.al`) also errors.
- **Grammar:** only `preproc_split_field` and `preproc_split_table_field`
  (`grammar.js:2135-2152`) do the "header list, then shared body" shape. `modify`,
  `add{first,last,after,before}` (layout and action variants) and `key` have no such rule.
- **Files:**
  - `Layers/ES/BaseApp/Service/Local/Document/ServiceCreditMemoES.PageExt.al:144` (modify, layout)
  - `Layers/IT/BaseApp/Inventory/Ledger/ItemLedgerEntry.Table.al:717` (key header, with complete keys earlier in the branch)
  - `Apps/DE/EDocumentDE/app/src/EDocumentServiceDE.PageExt.al:12` (add* + group, nested open headers)
- **Fix direction:** one generic "split header" rule per host family, modelled on
  `preproc_split_field`. Each branch is `<complete siblings>* <header>`, so the branch may
  lead with complete elements, which ItemLedgerEntry needs. Headers are `modify(...)`,
  `add*(...)` and `key(...; list)`, followed by `#endif` and the shared `{ … }`. Modify and
  key are Medium. EDocumentDE is a nested pair of open headers with properties on each side
  and needs the D-style "open body over `#endif`" rule applied to a layout container. Do it last.

## F. Split routine body (2 files) — RESOLVED

Reproducers (both error):
```al
codeunit 50100 T {
    trigger OnRun()            // trigger host: procedure P() here parses
#if not C28
    var I: Integer;
    begin
        if I = 0 then Error('x');
#else
    begin
#endif
        Message('y');
    end;
}
codeunit 50101 U {
    procedure P(): Text
#if C29
    var I: Integer;
    begin
        if I = 0 then exit('a');
#else
    begin
        exit('b');             // <- the #else branch contributes a statement
#endif
    end;
}
```
- **alc:** `p_trigger_body` and `p_proc_else_body` ACCEPT in both configs.
- **Grammar:**
  - `trigger_declaration` (`grammar.js:3226-3240`) offers only `_routine_regular_body |
    preproc_split_complete_body`. `procedure` uses `_procedure_tail` (2953), which also has
    `preproc_split_procedure_body`.
  - `_pspb_else_branch` (3038) is `[var] begin #endif`, so the `#else` branch cannot hold
    statements.
- **Files:**
  - `Apps/FR/PaymentManagementFR/app/src/Codeunits/PaymentManagementFR.Codeunit.al:30` (trigger OnRun). Reported at line 1 because recovery gave up.
  - `Layers/NO/BaseApp/Sales/History/SalesInvoiceHeader.Table.al:1659` and `:1676` (two procedures).
- **Fix:** give the trigger the same tail as the procedure: `_procedure_tail`, or at least the
  `preproc_split_procedure_body` arm. Change `_pspb_else_branch` to
  `[var] $._preproc_begin_body_to_endif`, the existing helper that already covers "begin plus
  statements before `#endif`". Both are Low.

## I. Split comma lists (3 files), docs/deferred-work.md items 1 and 2 — RESOLVED

1. `argument_list` (**deferred item 1, still open**). Reproducer:
   ```al
   R.SetLoadFields(A,
   #if not C28
       B,
   #endif
       C);
   ```
   `p_setload` ACCEPTs in both configs. File:
   `Layers/IT/BaseApp/Inventory/Transfer/ReleaseTransferDocument.Codeunit.al:125`.
   Fix: the run/group treatment from `812ace7` applied to `argument_list`.
2. `Permissions =` **head repeated per branch** (not a list-internal `#if`). Reproducer:
   ```al
   #if not C29
       Permissions = tabledata A = RIMD,
                     tabledata B = RIMD,
   #else
       Permissions = tabledata B = RIMD,
   #endif
                     tabledata C = RIMD;
   ```
   `p_perm` ACCEPTs in both configs. The list-internal form
   `Permissions = a, #if … b, #endif c;` already parses (`r/perm2.al`), through
   `preproc_conditional_permissions` (`grammar.js:1272`). The new part is that the property
   name and `=` sit inside the branch, followed by a trailing comma that runs into the shared
   tail. Files: `Layers/NO/BaseApp/Permissions/local.permissionset.al:16` and
   `localread.permissionset.al:16`. Fix direction: a dedicated `preproc_split_permissions_head`,
   `#if (Permissions = <seq> ,)+ [#else …] #endif <seq> ;`, with the same shape as
   `preproc_split_call_statement` (split call prefix, shared argument tail). Low-Medium.

## G. A branch ends in an open statement prefix (5 files) — RESOLVED

Every one of these is a branch whose last token is `then`, `else` or `else begin`. The
statement that completes it comes after `#endif`. The existing rules each cover one fixed
shape, and these are the neighbours:

| File | Minimal shape (errors) | Nearest existing rule and why it declines |
|---|---|---|
| `Layers/NO/BaseApp/Local/Finance/VAT/NorwegianVATTools.Codeunit.al:152` (case branch) | `#if if A=0 then begin..end else #else if A<>0 then #endif C:=2;` | `preproc_split_if_statement` wants every branch to be `if..then`, and `preproc_split_if_else_statement` wants every branch to be `if..then..else`. **Mixed** branches match neither (`r/no2.al`; `no4`, both `then`, parses). |
| `Layers/IT/BaseApp/Manufacturing/Planning/CalculateSubcontracts.Report.al:392` | `#if S; if B then M else begin #endif A:=1; #if end; #endif` | `preproc_split_if_else_statement` → `_preproc_if_then_else_head` allows no **preamble statement** before the `if` (`r/cs3` errors, `cs4` without the preamble parses). |
| `Layers/IT/BaseApp/Manufacturing/Reports/DetailedCalculation.Report.al:160` | `then #if begin …; if Y then begin..end else #endif C:=2; #if end; #endif` | `preproc_split_code_block_over_endif` (3838) needs complete statements before `#endif`. Here the last one is an open `if..else` head (`r/dc3`; `dc4` with complete statements parses). The `#pragma` lines are irrelevant: `dc2` without them still errors. |
| `Layers/GB/BaseApp/Bank/Check/Check.Report.al:1183` | `A() #if else begin #else else #endif B(); #if C(); end; #endif` | `preproc_fragmented_else_tail` expects `else` *before* the `#if`. Here `else` sits inside both branches, once with `begin` and once without (`r/ck1`, `ck2`; `ck3` with `else` hoisted parses). |
| `Layers/W1/BaseApp/Manufacturing/Inventory/Requisition/MfgCarryOutAction.Codeunit.al:276` (**W1**) | case: `A:=1 #if C29 else #else else begin B:=2; #endif C:=3; #if not C29 end; #endif end;` | The same `else` / `else begin` alternation as Check.Report, in the **case-else** host (`preproc_split_case_*` has no such arm). |

- **alc:** `p_no_case`, `p_calcsub`, `p_detailed`, `p_check_else` and `p_case_else` all
  ACCEPT in both configs.
- **Fix direction.** Stop adding one rule per shape. Introduce one hidden
  `_preproc_open_stmt_prefix` branch item:
  `[stmts]* ( if E then | if E then S else | else | else begin [stmts]* )`.
  - Make split-if accept any mix of prefixes per branch. That fixes NO and CalcSubcontracts.
  - Let `preproc_split_code_block_over_endif` and `_preproc_begin_body_to_endif` end with
    one. That fixes DetailedCalculation.
  - Add an "else-alternation" arm, `#if else begin #else else #endif` and its mirror, in both
    the if-else and case-else hosts. That fixes Check.Report and MfgCarryOutAction.
  - The shared tail after `#endif` is `_statement`, plus the existing `_preproc_end_guard`
    when a `begin` was opened.
  - Watch for GLR forks against `preproc_conditional_statement`. Build the fixture set first
    and run `tree-harness` verify. Med-Hard.

## H. A branch closes an enclosing construct and reopens a sibling (2 files + ProdOrderComponent)

The text balances in both configs, but each branch has a different nesting, so no single
tree is correct for both.

| File | Shape | Probe |
|---|---|---|
| `Layers/IT/BaseApp/Manufacturing/Document/ProdOrderComponent.Table.al:209` | `if A then begin X; #if end else if D then begin Y; #endif end;` (the real file closes 2 blocks and reopens 2) | `p_reopen_block` ACCEPT ×2 |
| `Layers/FR/BaseApp/Bank/BankAccount/BankAccountCard.Page.al:387` | `group(G){ f(A) #if } group(R){ Caption; f(B) #endif f(C) }` | `p_reopen_group` ACCEPT ×2 |
| `Layers/GB/Tests/ERM-Finance/ERMFinancialReportsIII.Codeunit.al:2172` | `P() begin …; #if B(); #else C(); end; procedure Q(): Text begin exit(''); #endif end;` | `p_reopen_proc` ACCEPT ×2 |

- **Grammar:** `preproc_split_else_begin_over_endif` (3205) is the one instance that already
  exists, `#if end else begin … #endif … end`. It rejects `end else if D then begin`
  (`r/poc1.al`, MISSING end_keyword) and any leading statements (`poc3`).
- **Fix direction:**
  - ProdOrderComponent: generalise 3205 so the reopen tail is `else <open stmt prefix ending
    in begin>`, with an optional leading `repeat(_statement) end;`. This shares the prefix
    item from G.
  - BankAccountCard.Page: a layout-level `#if '}' group-header '{' elems #endif` rule, the
    sibling of `preproc_split_brace_close_if_only` (2042). It represents one config: the
    `#if` reading, where the fields after `#endif` belong to the new group.
  - ERMFinancialReportsIII: splits at the object-member level across a procedure boundary. A
    `preproc_split_procedure_boundary` would have to host `end;` + a whole `procedure` header
    and body inside `#else`. This is the least tractable of the 33. It is a test codeunit, so
    it is also the least valuable.
  - The honest general answer for H is a config-aware re-parse: parse the file once per
    `#if` assignment and merge. That is an architecture change. Recorded here so it is not
    filed as a "known limitation".

## J. Invalid source (1 file)

`Layers/APAC/Tests/SINGLESERVER/ERMPurchaseReportsIII.Codeunit.al:2202`.
`VerifyValueEntryItemLedgerEntry` has no `end;` before the next `local procedure`. The file
contains no preprocessor directives at all. It was added in BCApps commit `e16d6c30`
(2026-09-28, "[29.0]-Incident 51000001968459"). Inserting `end;` after line 2201 takes it
from 131 errors to 0. The parser is right here and nothing needs fixing, but this file must
be excluded from any "0 errors on BC 29" claim.

---

## Ranked fix order (impact per effort)

1. **A + B, move lists and move in actions**: 10 files, Low effort, no `#if` interaction. Update the field-type contract.
2. **C, recursive `preproc_conditional_fields`/`_keys`**: 3 files plus half of ProdOrderComponent, a one-line change each.
3. **F, trigger tail and `_pspb_else_branch`**: 2 files, reuses existing helpers.
4. **I.1, `argument_list` host (deferred item 1)**: 1 file, but it closes a known item. **I.2, permissions head split**: 2 files.
5. **E, split headers for modify, add\* and key**: 2 files straightforward, EDocumentDE later.
6. **D, table field open over `#endif`**: 3 files, one-config-valid. Needs careful fixture wording.
7. **G, unified open-statement-prefix item**: 5 files, the largest `#if` family, highest GLR risk.
8. **H**: 3 files. ProdOrderComponent falls out of G's prefix item. BankAccountCard.Page is Medium. ERMFinancialReportsIII is Hard.
9. **J**: none.

After 1-4, 18 of 33 files are fixed (10+3+2+3), all with Low/Low-Med changes.

## Surprises

- **The two "line 1" files are not file-level.** PaymentManagementFR.Codeunit is F (the
  trigger has no split-body arm). ProdOrderComponent.Table is C + H. Four more files report
  at line 1 or 0 (NorwegianVATTools, CalculateSubcontracts, DetailedCalculation,
  MfgCarryOutAction). All are G, and recovery gave up on the whole file. The BOM is
  irrelevant: BC.History has 1,788 BOM files.
- **The "procedure boundary" test files are two unrelated things.** APAC is invalid AL
  (missing `end;`). GB ERMFinancialReportsIII is a real `#else` branch that closes one
  procedure and opens another (H).
- **D: Microsoft ships files that do not compile in the CLEANSCHEMA config**, and alc
  confirms it. The parser can only represent the non-clean reading.
- **The move-list syntax is not new.** Runtime 15.0 accepts it; BC 29 is just the first
  corpus that uses it.
- **Latent gaps found along the way:** nested `#if` in `keys` errors (`r/keysnest.al`), and
  a plain `#if addafter(A) #else addlast(B) #endif { }` split errors (`r/ed2.al`). No file
  in this corpus hits either yet.
- **`r/ck4.al` needs checking.** `A() #if else #else else #endif B();` gives 0 errors, and
  the tree may be wrong. It was not inspected; take it to the al-file-validation skill.
