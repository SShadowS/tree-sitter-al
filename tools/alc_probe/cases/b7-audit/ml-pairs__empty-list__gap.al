// B7a Task 10 witness (GAP): family ml-pairs, base placement empty-list, 3 cells; representative occ:ml_value_list:0.1.0.0@variable_declaration#empty-list
// Fixture b7_gap_ml_pairs_test.txt#B7a GAP: ml-pairs / empty-list (3 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:ml_value_list:0.1.0.0@variable_declaration%23empty-list#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:ml_value_list:0.1.0.0@variable_declaration#empty-list in tools/b7_audit/evidence.jsonl.gz
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
        TC: TextConst 
#if X
ENU = 'a' , DAN = 'b'
#endif
;
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
}
