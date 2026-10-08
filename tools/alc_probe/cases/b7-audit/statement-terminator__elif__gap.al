// B7b-3 final review M4 witness (GAP): family statement-terminator, base placement elif, 3 cells; representative occ:call_statement:0.1@preproc_split_case_end_branch#elif (deferred B7 in b7b3-manifest.tsv, deferred-work item 50: a `;` group beside the split case's end branch has no slot)
// Fixture b7_gap_case_branch_test.txt#B7a GAP: statement-terminator / elif (3 cells, verdict of the representative GAP, deferred B7: no slot for a `;` group beside the end branch, deferred-work item 50); the parser ERRORs on configurations alc accepts; representative occ:call_statement:0.1@preproc_split_case_end_branch%23elif#0
// expect: !TPL2 !X !Y accept
// expect: !TPL2 !X Y accept
// expect: !TPL2 X !Y accept
// expect: !TPL2 X Y accept
// expect: TPL2 !X !Y accept
// expect: TPL2 !X Y accept
// expect: TPL2 X !Y accept
// expect: TPL2 X Y accept
// source: recorded by B7a, re-read by the B7b-3 final fix wave, 2026-10-08: the alc split verdicts of cell occ:call_statement:0.1@preproc_split_case_end_branch#elif in tools/b7_audit/evidence.jsonl.gz
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
Bar();
2:
#if TPL2

Bar
#if X
;
#elif Y
;
#else
;
#endif

end;
Bar();
#else
begin
Bar();
end
end;
Bar();
#endif
    end;

    procedure Bar()
    begin
    end;

    procedure Foo(A: Integer; B: Integer): Integer
    begin
        exit(A + B);
    end;
}
