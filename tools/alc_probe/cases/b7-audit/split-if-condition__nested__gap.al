// B7a Task 10 witness (GAP): family split-if-condition, base placement nested, 40 cells; representative bnd:_preproc_if_header:condition:end@preproc_guarded_statement#nested/comparison
// Fixture b7_gap_split_if_condition_test.txt#B7a GAP: split-if-condition / nested (40 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative bnd:_preproc_if_header:condition:end@preproc_guarded_statement%23nested/comparison#0
// expect: !TPL !X !Y accept
// expect: !TPL !X Y accept
// expect: !TPL X !Y accept
// expect: !TPL X Y accept
// expect: TPL !X !Y accept
// expect: TPL !X Y accept
// expect: TPL X !Y accept
// expect: TPL X Y accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell bnd:_preproc_if_header:condition:end@preproc_guarded_statement#nested/comparison in tools/b7_audit/evidence.jsonl.gz
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
#if TPL
Bar();
if 
Ok
#if X
= true
#if Y
= false
#endif
#endif
 then
#endif
Bar();
    end;

    procedure Bar()
    begin
    end;

    procedure Foo(A: Integer; B: Integer): Integer
    begin
        exit(A + B);
    end;
}
