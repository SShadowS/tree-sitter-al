// B7a Task 10 witness (GAP): family procedure-tail, base placement trail, 18 cells; representative occ:_procedure_regular_tail:0.0.0@preproc_split_procedure#trail
// Fixture b7_gap_procedure_tail_test.txt#B7a GAP: procedure-tail / trail (18 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:_procedure_regular_tail:0.0.0@preproc_split_procedure%23trail#0
// expect: !TPL2 !X accept
// expect: !TPL2 X accept
// expect: TPL2 !X accept
// expect: TPL2 X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_procedure_regular_tail:0.0.0@preproc_split_procedure#trail in tools/b7_audit/evidence.jsonl.gz
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
Bar();
    end;

    procedure Bar()
    begin
    end;

    procedure Foo(A: Integer; B: Integer): Integer
    begin
        exit(A + B);
    end;

#if TPL2
    procedure Z()
#else
    procedure Z()
#endif
   

#if X
;
#endif

    begin
    end;
}
