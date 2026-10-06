// B7a Task 10 witness (GAP): family type-arguments, base placement elif, 3 cells; representative occ:dictionary_type:4@type_specification#elif
// Fixture b7_gap_type_arguments_test.txt#B7a GAP: type-arguments / elif (3 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:dictionary_type:4@type_specification%23elif#0
// expect: !X !Y accept
// expect: !X Y accept
// expect: X !Y accept
// expect: X Y accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:dictionary_type:4@type_specification#elif in tools/b7_audit/evidence.jsonl.gz
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
        D: Dictionary of [
Integer
#if X
,
#elif Y
,
#else
,
#endif
Text
];
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
