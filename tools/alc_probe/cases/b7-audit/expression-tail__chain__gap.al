// B7a Task 10 witness (GAP): family expression-tail, base placement chain, 17 cells; representative bnd:_expression_continuation:operand:end@preproc_conditional_expression_tail#chain/arithmetic
// Fixture b7_gap_expression_tail_test.txt#B7a GAP: expression-tail / chain (17 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative bnd:_expression_continuation:operand:end@preproc_conditional_expression_tail%23chain/arithmetic#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell bnd:_expression_continuation:operand:end@preproc_conditional_expression_tail#chain/arithmetic in tools/b7_audit/evidence.jsonl.gz
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
I := 1
#if TPL
+ 
2 * 2
#if X
+ 3
#endif
* 4

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
