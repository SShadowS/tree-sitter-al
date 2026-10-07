// B7a Task 10 witness (GAP): family case-patterns, base placement count-differs, 18 cells; representative occ:_case_pattern_run:0.1.0.0@preproc_conditional_case_patterns#count-differs
// Fixture b7_gap_case_patterns_test.txt#B7a GAP: case-patterns / count-differs (18 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:_case_pattern_run:0.1.0.0@preproc_conditional_case_patterns%23count-differs#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_case_pattern_run:0.1.0.0@preproc_conditional_case_patterns#count-differs in tools/b7_audit/evidence.jsonl.gz
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
8,
#if TPL

1
#if X
, 2 , 21
#else
, 22
#endif
,
#endif
9:
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
