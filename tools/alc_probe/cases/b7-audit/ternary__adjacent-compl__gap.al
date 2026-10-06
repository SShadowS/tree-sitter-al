// B7a Task 10 witness (GAP): family ternary, base placement adjacent-compl, 3 cells; representative occ:ternary_expression:0.3@ternary_expression#adjacent-compl
// Fixture b7_gap_ternary_test.txt#B7a GAP: ternary / adjacent-compl (3 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:ternary_expression:0.3@ternary_expression%23adjacent-compl#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:ternary_expression:0.3@ternary_expression#adjacent-compl in tools/b7_audit/evidence.jsonl.gz
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
1
#if X
:
#endif
#if not X
:
#endif
2
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
