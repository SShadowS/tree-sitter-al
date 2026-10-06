// B7a Task 10 witness (GAP): family list-literal, base placement empty-list, 6 cells; representative occ:list_literal:1.0.2.0.0@in_expression#empty-list
// Fixture b7_gap_list_literal_test.txt#B7a GAP: list-literal / empty-list (6 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative occ:list_literal:1.0.2.0.0@in_expression%23empty-list#0
// expect: !X reject(AL0104,AL0224)
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:list_literal:1.0.2.0.0@in_expression#empty-list in tools/b7_audit/evidence.jsonl.gz
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
Ok := I in [
#if X
1 , 2
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
