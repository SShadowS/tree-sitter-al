// B6 (_expression_statement narrowing): torn call or
// source: recorded by B6 task 1, 2026-10-06; docs/deferred-work.md item 4
// expect: X reject(AL0117)
// expect: !X accept
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
#if X
        or (2 = 2)
#endif
        ;
    end;
}
