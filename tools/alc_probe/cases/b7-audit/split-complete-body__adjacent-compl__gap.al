// B7a Task 10 witness (GAP): family split-complete-body, base placement adjacent-compl, 3 cells; representative occ:_preproc_branch_body:4.0@preproc_split_complete_body#adjacent-compl
// Fixture b7_gap_split_complete_body_test.txt#B7a GAP: split-complete-body / adjacent-compl (3 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:_preproc_branch_body:4.0@preproc_split_complete_body%23adjacent-compl#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_preproc_branch_body:4.0@preproc_split_complete_body#adjacent-compl in tools/b7_audit/evidence.jsonl.gz
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
Bar();
    end;

    procedure Bar()
    begin
    end;

    procedure Foo(A: Integer; B: Integer): Integer
    begin
        exit(A + B);
    end;

#if TPL
    procedure Z()
#else
    procedure Z()
#endif
#if TPL
    begin
    
end
#if X
;
#endif
#if not X
;
#endif

#else
    begin
    end;
#endif
}
