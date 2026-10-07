// B7b-0 witness (REJECTED/over-accepts(syntax)): family guarded-statement, base placement trail, 3 cells; representative occ:_preproc_guard_block:0.0.1@preproc_guarded_statement#trail
// Fixture b7_gap_guarded_statement_test.txt#B7a REJECTED/over-accepts(syntax): guarded-statement / trail (3 cells, verdict of the representative MIXED); alc rejects with a syntax code (AL0111) but the parser is clean; representative occ:_preproc_guard_block:0.0.1@preproc_guarded_statement%23trail#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X reject(AL0111)
// expect: TPL X accept
// source: recorded by B7b-0, 2026-10-07: the alc split verdicts of cell occ:_preproc_guard_block:0.0.1@preproc_guarded_statement#trail in tools/b7_audit/evidence.jsonl.gz (a former empty_statement ruling cell; with the arm's `;` accepted, its worst configuration is this over-acceptance)
table 50100 T
{
    fields
    {
        field(1; K; Code[20]) { }
        field(2; N; Integer) { }
        field(3; B; Boolean) { }
        field(9; O; Option) { OptionMembers = A,B,C; }
    }
    keys
    {
        key(PK; K) { Clustered = true; }
    }
}
codeunit 50101 P
{
    procedure Q(): Integer
    var
        R: Record T;
        I: Integer;
        Ok: Boolean;
        L: List of [Integer];
        Arr: array[3] of Integer;
        Arr2: array[2, 2] of Integer;
        Recs: array[2] of Record T;
    begin
#if TPL

Bar()
#if X
;
#endif

if Ok then
#endif
Bar();
    end;

    procedure Bar()
    begin
    end;

    procedure Foo(A: Integer; B: Integer): Integer
    begin
        exit(A + B);
    end;
}
