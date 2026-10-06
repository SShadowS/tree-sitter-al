// B7a Task 10 witness (GAP): family list-literal, base placement sep-before-end, 9 cells; representative occ:preproc_conditional_list_elements:1.0.0@list_literal#sep-before-end
// Fixture b7_gap_list_literal_test.txt#B7a GAP: list-literal / sep-before-end (9 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:preproc_conditional_list_elements:1.0.0@list_literal%23sep-before-end#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:preproc_conditional_list_elements:1.0.0@list_literal#sep-before-end in tools/b7_audit/evidence.jsonl.gz
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
Ok := I in [1
#if TPL

,
2
#if X
, 3
#endif

#endif
];
    end;

    procedure Bar()
    begin
    end;

    procedure Foo(A: Integer; B: Integer): Integer
    begin
        exit(A + B);
    end;
}
