// B7a Task 10 witness (GAP): family arguments, base placement holes-trail, 3 cells; representative occ:_argument_branch_run:1.0.0@preproc_conditional_arguments#holes-trail
// Fixture b7_gap_arguments_test.txt#B7a GAP: arguments / holes-trail (3 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative occ:_argument_branch_run:1.0.0@preproc_conditional_arguments%23holes-trail#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X reject(AL0301)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_argument_branch_run:1.0.0@preproc_conditional_arguments#holes-trail in tools/b7_audit/evidence.jsonl.gz
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

1 , 2
#if X
,
#endif

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
