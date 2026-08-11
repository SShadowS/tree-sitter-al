# Dangling-Else Fix: IncomingDocument.Table.al

> **RESOLVED in 4.0.0.** The file named below now parses with **0 ERROR/MISSING
> nodes**, verified against the released grammar. The `else` in a `case true of`
> binds to the inner `if`, which is what the program means.
>
> This document is kept as the record of the decision, not as open work. The
> problem statement and the four options are deliberately preserved: which fix
> was chosen and what was rejected is the thing nobody writes down and everybody
> later wants. Read the tense below as historical.
>
> **Chosen:** the grammar option, not a scanner or precedence workaround — the
> `case_branch` no longer offers an `else` arm that can steal the inner `if`'s.
> Pinned by `test/corpus/` fixtures asserting the shape rather than the error
> count, since the defect produced a *wrong tree*, and for 133 other files it
> produced no error at all.
>
> The 43 cascading ERROR nodes cited below were this file's symptom. They were
> the loud instance of a defect that was silent everywhere else, which is why
> the fix is pinned by structure and not by an error count.

## Problem

**File:** `BC.History/BaseApp/Source/Base Application/eServices/EDocument/IncomingDocument.Table.al`

The `else` keyword in a `case true of` statement is incorrectly consumed as an `if-else` branch instead of the `case else` branch, causing 43 cascading ERROR nodes.

## Failing Pattern

```al
case true of
    SalesCrMemoHeader.Get(DocNo):
        if SalesCrMemoHeader."Posting Date" = PostingDate then
            exit("Document Type"::"Sales Credit Memo");
    else                           // ← intended as case-else, parsed as if-else
        GLEntry.SetRange("Posting Date", PostingDate);
        GLEntry.SetRange("Document No.", DocNo);
        IsPosted := not GLEntry.IsEmpty();
        exit("Document Type"::Journal);
end;
```

Because `else` binds to the preceding `if` (standard dangling-else resolution via `prec.right`), only ONE statement fits the if-else body. The remaining 3 statements are orphaned → cascade of ERRORs.

## Root Cause

Grammar defines:
- `case_branch` body: `choice($.code_block, $._statement)` — single statement
- `case_else_branch` body: `repeat($._statement)` — multiple statements

The `else` keyword is ambiguous: is it an `if-else` tail or a `case else` branch? Tree-sitter resolves in favour of `if-else` (standard dangling-else, `prec.right`).

## Fix Options

### Option A: Require `begin`/`end` for multi-statement case-else
Not viable — the real AL compiler accepts bare multi-statement case-else bodies.

### Option B: Grammar precedence on `case_else_branch`
Give `case_else_branch` higher precedence than `if_else_clause` so the `else` is consumed by the outer `case` statement first.

```javascript
// Increase precedence of case_else_branch so it wins over if-else
case_else_branch: $ => prec(10, seq(
  kw('else'),
  repeat($._statement),
)),

// Or use a dedicated precedence declaration
precedences: $ => [
  ['case_else', 'if_else'],
],
```

### Option C: Make `if-else` inside `case_branch` require `begin`/`end`
Restrict the grammar so that `if-else` inside a case branch must use a code_block — enforcing that a bare `else` at the case level is always `case_else_branch`.

### Option D: Contextual parsing (most robust)
Track that we are inside a `case` statement body and prefer `case_else_branch` in that context. May require scanner changes or `inline` rules.

## Recommended Fix

**Option B** — try raising precedence on `case_else_branch`. This is a one-line change, testable immediately.

If Option B causes conflicts elsewhere (since `else` appears in many contexts), fall back to **Option C** which is more surgical.

## Test Case

```
========================================================================
Case else multi-statement without begin/end
========================================================================
codeunit 50100 Test {
    procedure Test() {
        var DocNo: Code[20];
        var PostingDate: Date;
        var IsPosted: Boolean;
    begin
        case true of
            DocNo = '':
                if PostingDate = 0D then
                    exit;
            else
                IsPosted := true;
                exit;
        end;
    end;
}
------------------------------------------------------------------------
(source_file ...)
```
