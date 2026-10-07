// B7a Task 10 witness (GAP): family arguments, base placement sep-only, 6 cells; representative occ:_argument_branch_run:1.0.0@preproc_conditional_arguments#sep-only
// Fixture b7_gap_arguments_test.txt#B7a GAP: arguments / sep-only (6 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:_argument_branch_run:1.0.0@preproc_conditional_arguments%23sep-only#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_argument_branch_run:1.0.0@preproc_conditional_arguments#sep-only in tools/b7_audit/evidence.jsonl.gz
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
I := Foo(
#if TPL

1
#if X
,
#else
,
#endif
2

#else
3, 4
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
