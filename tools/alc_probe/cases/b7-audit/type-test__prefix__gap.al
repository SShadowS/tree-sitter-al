// B7a Task 10 witness (GAP): family type-test, base placement prefix, 4 cells; representative bnd:as_expression:left:end@as_expression#prefix/type-test
// Fixture b7_gap_type_test_test.txt#B7a GAP: type-test / prefix (4 cells, verdict of the representative GAP); the parser ERRORs on configurations alc accepts; representative bnd:as_expression:left:end@as_expression%23prefix/type-test#0
// expect: !X accept
// expect: X accept
// source: recorded by B7a Task 10, 2026-10-07: the alc split verdicts of cell bnd:as_expression:left:end@as_expression#prefix/type-test in tools/b7_audit/evidence.jsonl.gz
interface IFoo
{
}

codeunit 50103 Impl implements IFoo
{
}
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
        Intf: Interface IFoo;
        Intf2: Interface IFoo;
    begin
Intf2 := 
Intf as
#if X
IFoo as
#endif
IFoo
 as IFoo;
    end;

    procedure Bar()
    begin
    end;

    procedure Foo(A: Integer; B: Integer): Integer
    begin
        exit(A + B);
    end;
}
