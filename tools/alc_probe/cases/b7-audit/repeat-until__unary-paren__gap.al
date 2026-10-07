// B7a Task 10 witness (GAP): family repeat-until, base placement unary-paren, 72 cells; representative bnd:repeat_statement:condition:end@asserterror_statement#unary-paren/comparison
// Fixture b7_gap_repeat_until_test.txt#B7a GAP: repeat-until / unary-paren (72 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative bnd:repeat_statement:condition:end@asserterror_statement%23unary-paren/comparison#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell bnd:repeat_statement:condition:end@asserterror_statement#unary-paren/comparison in tools/b7_audit/evidence.jsonl.gz
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
Ok =
#if X
( true = false )
#else
false
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
