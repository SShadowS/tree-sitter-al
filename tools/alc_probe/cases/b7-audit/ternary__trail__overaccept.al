// B7b-2 Task 12 witness (REJECTED/over-accepts(syntax)): family ternary, base placement trail, 3 cells; representative occ:ternary_expression:0.3@ternary_expression#trail
// Fixture b7b2_ternary_test.txt#B7b-2 ternary / trail: moved from b7_gap_ternary_test.txt#0
// expect: !X reject(AL0224)
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:ternary_expression:0.3@ternary_expression#trail in tools/b7_audit/evidence.jsonl.gz; the group is OVERACCEPT since B7b-2 Phase C parses the split tree clean (Task 12)
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
I := Ok ?
1 :
#if X
2
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
