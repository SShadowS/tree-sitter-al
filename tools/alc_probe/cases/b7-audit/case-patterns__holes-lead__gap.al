// B7a Task 10 witness (GAP): family case-patterns, base placement holes-lead, 6 cells; representative occ:_case_pattern_run:0.1.0.0@preproc_split_case_extended#holes-lead
// Fixture b7_gap_case_patterns_test.txt#B7a GAP: case-patterns / holes-lead (6 cells, verdict of the representative MIXED); the parser ERRORs on configurations alc accepts; representative occ:_case_pattern_run:0.1.0.0@preproc_split_case_extended%23holes-lead#0
// expect: !TPL2 !X accept
// expect: !TPL2 X accept
// expect: TPL2 !X accept
// expect: TPL2 X reject(AL0104,AL0111,AL0224)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_case_pattern_run:0.1.0.0@preproc_split_case_extended#holes-lead in tools/b7_audit/evidence.jsonl.gz
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
#if TPL2
7:
Bar();

#if X
,
#endif
1 , 2
:
#else
6:
#endif
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
