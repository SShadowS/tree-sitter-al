// B7a Task 10 witness (GAP): family parameter-list, base placement trail, 9 cells; representative occ:parameter_list:2.0.0@preproc_split_procedure#trail
// Fixture b7_gap_parameter_list_test.txt#B7a GAP: parameter-list / trail (9 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative occ:parameter_list:2.0.0@preproc_split_procedure%23trail#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X reject(AL0301)
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:parameter_list:2.0.0@preproc_split_procedure#trail in tools/b7_audit/evidence.jsonl.gz
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
Bar();
    end;

    procedure Bar()
    begin
    end;

    procedure Foo(A: Integer; B: Integer): Integer
    begin
        exit(A + B);
    end;

#if TPL
    procedure Z(
A: Integer ;
#if X
B: Integer
#endif
)
#else
    procedure Z(A: Integer)
#endif
    begin
    end;
}
