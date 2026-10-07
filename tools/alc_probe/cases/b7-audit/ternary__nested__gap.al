// B7a Task 10 witness (GAP): family ternary, base placement nested, 19 cells; representative bnd:ternary_expression:condition:end@ternary_expression#nested/comparison
// Fixture b7_gap_ternary_test.txt#B7a GAP: ternary / nested (19 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative bnd:ternary_expression:condition:end@ternary_expression%23nested/comparison#0
// expect: !X !Y accept
// expect: !X Y accept
// expect: X !Y accept
// expect: X Y accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell bnd:ternary_expression:condition:end@ternary_expression#nested/comparison in tools/b7_audit/evidence.jsonl.gz
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
I := 
Ok
#if X
= true
#if Y
= false
#endif
#endif
 ? 1 : 2;
    end;

    procedure Bar()
    begin
    end;

    procedure Foo(A: Integer; B: Integer): Integer
    begin
        exit(A + B);
    end;
}
