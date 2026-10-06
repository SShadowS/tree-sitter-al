// B7a Task 10 witness (REJECTED/over-accepts(syntax)): family split-if-begin, base placement trail, 36 cells; representative occ:preproc_split_if_begin_asymmetric:0.3.0@asserterror_statement#trail
// Fixture b7_gap_split_if_begin_test.txt#B7a REJECTED/over-accepts(syntax): split-if-begin / trail (36 cells, verdict of the representative MIXED); alc rejects with a syntax code (AL0104) but the parser is clean; representative occ:preproc_split_if_begin_asymmetric:0.3.0@asserterror_statement%23trail#0
// expect: !TPL !X reject(AL0104)
// expect: !TPL X accept
// expect: TPL !X accept
// expect: TPL X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:preproc_split_if_begin_asymmetric:0.3.0@asserterror_statement#trail in tools/b7_audit/evidence.jsonl.gz
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
asserterror
#if TPL
if Ok then begin
#endif
Bar();

end
#if X
;
#endif

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
