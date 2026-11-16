// B7a witness (GAP): family arguments, base placement elif, 6 cells; representative occ:_paren_close_cont_semi_arm:2@semi_argument_list#elif
// Fixture b7_gap_arguments_test.txt#B7a GAP: arguments / elif (6 cells, an every-arm-`;` arm's terminator, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative occ:_paren_close_cont_semi_arm:2@semi_argument_list%23elif#0
// expect: * accept
// source: issue #44 F1 fix pass, 2026-11-15: the alc split verdicts of cell occ:_paren_close_cont_semi_arm:2@semi_argument_list#elif in tools/b7_audit/evidence.jsonl.gz (a #if group around or at the `;` inside an arm of an every-arm-`;` preproc_split_paren_close; deferred item 110)
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
I := Foo(1, 2
#if TPL

)
#if X
;
#elif Y
;
#else
;
#endif

#else
);
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
