// B7a Task 10 witness (GAP): family split-if-begin, base placement elif, 87 cells; representative occ:preproc_split_if_begin_asymmetric:0.3.0@case_branch#elif
// Fixture b7_gap_split_if_begin_test.txt#B7a GAP: split-if-begin / elif (87 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:preproc_split_if_begin_asymmetric:0.3.0@case_branch%23elif#0
// expect: !TPL !X !Y accept
// expect: !TPL !X Y accept
// expect: !TPL X !Y accept
// expect: !TPL X Y accept
// expect: TPL !X !Y accept
// expect: TPL !X Y accept
// expect: TPL X !Y accept
// expect: TPL X Y accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:preproc_split_if_begin_asymmetric:0.3.0@case_branch#elif in tools/b7_audit/evidence.jsonl.gz
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
#if TPL
if Ok then begin
#endif
Bar();

end
#if X
;
#elif Y
;
#else
;
#endif

end;
#if TPL
    end;
#endif

    procedure Bar()
    begin
    end;

    procedure Foo(A: Integer; B: Integer): Integer
    begin
        exit(A + B);
    end;
}
