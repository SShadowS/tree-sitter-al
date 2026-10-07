// B7a Task 10 witness (GAP): family case-expression, base placement op-only, 8 cells; representative bnd:case_statement:expression:end@statement_block#op-only/arithmetic
// Fixture b7_gap_case_expression_test.txt#B7a GAP: case-expression / op-only (8 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative bnd:case_statement:expression:end@statement_block%23op-only/arithmetic#0
// expect: !X reject(AL0104,AL0111,AL0224)
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell bnd:case_statement:expression:end@statement_block#op-only/arithmetic in tools/b7_audit/evidence.jsonl.gz
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
case 
I
#if X
+
#endif
2
 of
1:
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
