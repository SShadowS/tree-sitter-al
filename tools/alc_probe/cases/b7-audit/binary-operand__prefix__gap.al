// B7a Task 10 witness (GAP): family binary-operand, base placement prefix, 19 cells; representative bnd:logical_expression:left:end@case_branch#prefix/membership
// Fixture b7_gap_binary_operand_test.txt#B7a GAP: binary-operand / prefix (19 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative bnd:logical_expression:left:end@case_branch%23prefix/membership#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell bnd:logical_expression:left:end@case_branch#prefix/membership in tools/b7_audit/evidence.jsonl.gz
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
case Ok of

Ok in
#if X
[true, false] in
#endif
[true]
 and Ok:
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
