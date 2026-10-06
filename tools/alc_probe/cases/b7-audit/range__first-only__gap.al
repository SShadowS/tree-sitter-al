// B7a Task 10 witness (GAP): family range, base placement first-only, 38 cells; representative bnd:range_expression:left:end@case_branch#first-only/arithmetic
// Fixture b7_gap_range_test.txt#B7a GAP: range / first-only (38 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative bnd:range_expression:left:end@case_branch%23first-only/arithmetic#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell bnd:range_expression:left:end@case_branch#first-only/arithmetic in tools/b7_audit/evidence.jsonl.gz
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

#if X
1
#else
2
#endif
..5:
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
