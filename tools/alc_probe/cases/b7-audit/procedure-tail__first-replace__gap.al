// B7a Task 10 witness (GAP): family procedure-tail, base placement first-replace, 12 cells; representative occ:_routine_regular_body:0.2.0@preproc_split_procedure#first-replace
// Fixture b7_gap_procedure_tail_test.txt#B7a GAP: procedure-tail / first-replace (12 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:_routine_regular_body:0.2.0@preproc_split_procedure%23first-replace#0
// expect: !TPL2 !X accept
// expect: !TPL2 X accept
// expect: TPL2 !X accept
// expect: TPL2 X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell occ:_routine_regular_body:0.2.0@preproc_split_procedure#first-replace in tools/b7_audit/evidence.jsonl.gz
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
   
    begin
    
#if X
end
#else
end
#endif
;

}
