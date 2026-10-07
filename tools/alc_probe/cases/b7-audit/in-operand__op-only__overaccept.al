// B7a Task 10 witness (REJECTED/over-accepts(syntax)): family in-operand, base placement op-only, 4 cells; representative bnd:in_expression:left:end@in_expression#op-only/arithmetic
// Fixture b7_gap_in_operand_test.txt#B7a REJECTED/over-accepts(syntax): in-operand / op-only (4 cells, verdict of the representative MIXED); alc rejects with a syntax code (AL0104,AL0107,AL0198) but the parser is clean; representative bnd:in_expression:left:end@in_expression%23op-only/arithmetic#0
// expect: !X reject(AL0104,AL0107,AL0198)
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell bnd:in_expression:left:end@in_expression#op-only/arithmetic in tools/b7_audit/evidence.jsonl.gz
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
Ok := 
I
#if X
+
#endif
2
 in [1, 2];
    end;

    procedure Bar()
    begin
    end;

    procedure Foo(A: Integer; B: Integer): Integer
    begin
        exit(A + B);
    end;
}
