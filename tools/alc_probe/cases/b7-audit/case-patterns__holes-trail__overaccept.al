// B7a Task 10 witness (REJECTED/over-accepts(syntax)): family case-patterns, base placement holes-trail, 15 cells; representative occ:_case_pattern_branch:0.0@preproc_conditional_case_patterns#holes-trail
// Fixture b7_gap_case_patterns_test.txt#B7a REJECTED/over-accepts(syntax): case-patterns / holes-trail (15 cells, verdict of the representative MIXED); alc rejects with a syntax code (AL0104,AL0224) but the parser is clean; representative occ:_case_pattern_branch:0.0@preproc_conditional_case_patterns%23holes-trail#0
// expect: !TPL !X accept
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X reject(AL0104,AL0224)
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_case_pattern_branch:0.0@preproc_conditional_case_patterns#holes-trail in tools/b7_audit/evidence.jsonl.gz
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
1
#if TPL

,
2 , 21
#if X
,
#endif

#endif
:
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
