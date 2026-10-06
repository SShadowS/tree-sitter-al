// B7a Task 10 witness (GAP): family assignment, base placement nested, 48 cells; representative bnd:assignment_statement:right:end@asserterror_statement#nested/arithmetic
// Fixture b7_gap_assignment_test.txt#B7a GAP: assignment / nested (48 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative bnd:assignment_statement:right:end@asserterror_statement%23nested/arithmetic#0
// expect: !X !Y accept
// expect: !X Y accept
// expect: X !Y accept
// expect: X Y accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell bnd:assignment_statement:right:end@asserterror_statement#nested/arithmetic in tools/b7_audit/evidence.jsonl.gz
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
+ 2
#if Y
+ 3
#endif
#endif
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
