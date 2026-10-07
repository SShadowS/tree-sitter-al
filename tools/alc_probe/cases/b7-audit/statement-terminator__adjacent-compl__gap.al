// B7a Task 10 witness (GAP): family statement-terminator, base placement adjacent-compl, 24 cells; representative occ:call_statement:0.1@case_branch#adjacent-compl
// Fixture b7_gap_statement_terminator_test.txt#B7a GAP: statement-terminator / adjacent-compl (24 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:call_statement:0.1@case_branch%23adjacent-compl#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:call_statement:0.1@case_branch#adjacent-compl in tools/b7_audit/evidence.jsonl.gz
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

Bar
#if X
;
#endif
#if not X
;
#endif

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
