// B6 (_expression_statement narrowing): torn call or
// Fixture expression_statement_negative_test.txt#B6 negative: call torn by a keyword-operator %23if arm#0
// source: recorded by B6 task 1, 2026-10-06; docs/deferred-work.md item 4
// expect: A reject(AL0117)
// expect: !A accept
table 50100 T { fields { field(1; K; Code[20]) { } field(2; Name; Text[30]) { } } }
codeunit 50101 Probe
{
    procedure Foo(): Boolean begin exit(true); end;
    procedure "My Proc"() begin end;
    procedure Bar() begin end;
    procedure Main()
    var Rec: Record T; X: Integer; Arr: array[3] of Integer; C: Boolean;
    begin
        Foo()
#if A
        or (2 = 2)
#endif
        ;
    end;
}
