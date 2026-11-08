// B7a Task 10 witness (GAP): family case-branch, base placement empty, 12 cells; representative occ:preproc_split_case_extended:0.3@case_body#empty
// Fixture b7_gap_case_branch_test.txt#B7a GAP: case-branch / empty (12 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:preproc_split_case_extended:0.3@case_body%23empty#0
// expect: * accept
// source: recorded 2026-11-08 from the alc split verdicts of cell occ:preproc_split_case_extended:0.3@case_body#empty in tools/b7_audit/evidence.jsonl.gz; the former representative occ:case_branch:0.1 was fixed by deferred item 67
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
#if TPL
1:
Bar();

2 :
#if X
#endif


#else
2, 1:
#endif
Bar();
end;
    end;

    procedure Bar()
    begin
    end;

    procedure Foo(A: Integer; B: Integer): Integer
    begin
        exit(A + B);
    end;
}
