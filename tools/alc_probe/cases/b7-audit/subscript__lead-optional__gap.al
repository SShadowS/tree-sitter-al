// B7a Task 10 witness (GAP): family subscript, base placement lead-optional, 21 cells; representative occ:subscript_expression:0.4.0.0@case_branch#lead-optional
// Fixture b7_gap_subscript_test.txt#B7a GAP: subscript / lead-optional (21 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative occ:subscript_expression:0.4.0.0@case_branch%23lead-optional#0
// expect: !X reject(AL0122)
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:subscript_expression:0.4.0.0@case_branch#lead-optional in tools/b7_audit/evidence.jsonl.gz
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
case I of
Arr2[
#if X
1 ,
#endif
2
]:
Bar();
end;
    end;

    procedure Bar()
    begin
    end;

    procedure Foo(A: Integer; B: Integer): Integer
    begin
        exit(A + B);
    end;
}
