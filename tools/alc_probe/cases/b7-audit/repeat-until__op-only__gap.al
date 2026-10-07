// B7a Task 10 witness (GAP): family repeat-until, base placement op-only, 72 cells; representative bnd:repeat_statement:condition:end@asserterror_statement#op-only/comparison
// Fixture b7_gap_repeat_until_test.txt#B7a GAP: repeat-until / op-only (72 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative bnd:repeat_statement:condition:end@asserterror_statement%23op-only/comparison#0
// expect: !X reject(AL0104,AL0111)
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell bnd:repeat_statement:condition:end@asserterror_statement#op-only/comparison in tools/b7_audit/evidence.jsonl.gz
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
repeat
Bar();
until 
Ok
#if X
=
#endif
true
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
