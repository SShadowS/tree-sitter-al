// B7b-3 Task 10 witness (GAP): family case-branch, base placement trail, 6 cells; representative occ:preproc_split_case_end_branch:1.0@preproc_split_case_statement_end#trail (deferred B7 in b7b3-manifest.tsv: the split case end branch has no slot for a `;` beside it)
// Fixture b7_gap_case_branch_test.txt#B7a GAP: case-branch / trail (6 cells, verdict of the representative GAP, deferred B7: no slot for a `;` beside the end branch); the parser ERRORs on configurations alc accepts; representative occ:preproc_split_case_end_branch:1.0@preproc_split_case_statement_end#trail#0
// expect: * accept
// source: recorded by B7a, re-read by B7b-3 Task 10, 2026-10-08: the alc split verdicts of cell occ:preproc_split_case_end_branch:1.0@preproc_split_case_statement_end#trail in tools/b7_audit/evidence.jsonl.gz
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
case I of
1:
Bar();
2:
#if TPL

Bar()
#if X
;
#endif

end;
I := 1;
#else
begin
Bar();
end
end;
I := 2;
#endif
    end;

    procedure Bar()
    begin
    end;

    procedure Foo(A: Integer; B: Integer): Integer
    begin
        exit(A + B);
    end;
}
