// B7b-2 Task 9 witness (REJECTED/over-accepts(syntax)): family parenthesized, base placement op-only, 4 cells; representative bnd:parenthesized_expression:1:end@parenthesized_expression#op-only/arithmetic
// Fixture b7b2_parenthesized_test.txt#B7b-2 parenthesized / op-only: moved from b7_gap_parenthesized_test.txt#0
// expect: !X reject(AL0104,AL0111)
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell bnd:parenthesized_expression:1:end@parenthesized_expression#op-only/arithmetic in tools/b7_audit/evidence.jsonl.gz; the group is OVERACCEPT since B7b-2 Phase B parses the split tree clean (Task 9)
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
I := (
I
#if X
+
#endif
2
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
