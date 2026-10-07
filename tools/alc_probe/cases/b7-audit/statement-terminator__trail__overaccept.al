// B7a Task 10 witness (REJECTED/over-accepts(syntax)): family statement-terminator, base placement trail, 33 cells; representative occ:empty_statement:@case_branch#trail
// Fixture b7_gap_statement_terminator_test.txt#B7a REJECTED/over-accepts(syntax): statement-terminator / trail (33 cells, verdict of the representative MIXED); alc rejects with a syntax code (AL0104,AL0224) but the parser is clean; representative occ:empty_statement:@case_branch%23trail#0
// expect: !X reject(AL0104,AL0224)
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:empty_statement:@case_branch#trail in tools/b7_audit/evidence.jsonl.gz
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
1:


#if X
;
#endif

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
