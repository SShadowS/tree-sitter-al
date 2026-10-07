// B7a Task 10 witness (REJECTED/over-accepts(syntax)): family assignment, base placement op-only, 48 cells; representative bnd:assignment_statement:right:end@asserterror_statement#op-only/arithmetic
// Fixture b7_gap_assignment_test.txt#B7a REJECTED/over-accepts(syntax): assignment / op-only (48 cells, verdict of the representative MIXED); alc rejects with a syntax code (AL0104,AL0111) but the parser is clean; representative bnd:assignment_statement:right:end@asserterror_statement%23op-only/arithmetic#0
// expect: !X reject(AL0104,AL0111)
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell bnd:assignment_statement:right:end@asserterror_statement#op-only/arithmetic in tools/b7_audit/evidence.jsonl.gz
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
asserterror
I := 
1
#if X
+
#endif
2
;
    end;

    procedure Bar()
    begin
    end;

    procedure Foo(A: Integer; B: Integer): Integer
    begin
        exit(A + B);
    end;
}
