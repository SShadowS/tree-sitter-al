// B7a Task 10 witness (GAP): family split-call, base placement consecutive, 10 cells; representative bnd:_expression_list:0:end@preproc_split_call_statement#consecutive/arithmetic
// Fixture b7_gap_split_call_test.txt#B7a GAP: split-call / consecutive (10 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative bnd:_expression_list:0:end@preproc_split_call_statement%23consecutive/arithmetic#0
// expect: !TPL !X !Y accept
// expect: !TPL !X Y accept
// expect: !TPL X !Y accept
// expect: !TPL X Y accept
// expect: TPL !X !Y accept
// expect: TPL !X Y accept
// expect: TPL X !Y accept
// expect: TPL X Y accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell bnd:_expression_list:0:end@preproc_split_call_statement#consecutive/arithmetic in tools/b7_audit/evidence.jsonl.gz
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
#if TPL
Foo(1,
#else
Foo(2,
#endif

3
#if X
+ 2
#endif
#if Y
+ 3
#endif
);
    end;

    procedure Bar()
    begin
    end;

    procedure Foo(A: Integer; B: Integer): Integer
    begin
        exit(A + B);
    end;
}
