// B7a Task 10 witness (REJECTED/over-accepts(syntax)): family while-condition, base placement op-only, 6 cells; representative bnd:while_statement:condition:end@statement_block#op-only/comparison
// Fixture b7_gap_while_condition_test.txt#B7a REJECTED/over-accepts(syntax): while-condition / op-only (6 cells, verdict of the representative MIXED); alc rejects with a syntax code (AL0104,AL0111) but the parser is clean; representative bnd:while_statement:condition:end@statement_block%23op-only/comparison#0
// expect: !X reject(AL0104,AL0111)
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell bnd:while_statement:condition:end@statement_block#op-only/comparison in tools/b7_audit/evidence.jsonl.gz
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
while 
Ok
#if X
=
#endif
true
 do
Bar();
    end;

    procedure Bar()
    begin
    end;

    procedure Foo(A: Integer; B: Integer): Integer
    begin
        exit(A + B);
    end;
}
