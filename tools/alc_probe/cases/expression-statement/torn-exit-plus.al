// B6 (_expression_statement narrowing): torn exit plus
// source: recorded by B6 task 1, 2026-10-06; docs/deferred-work.md item 4
// expect: X reject(AL0104,AL0111)
// expect: !X accept
table 50100 T { fields { field(1; K; Code[20]) { } field(2; Name; Text[30]) { } } }
codeunit 50101 Probe
{
    procedure Foo(): Boolean begin exit(true); end;
    procedure "My Proc"() begin end;
    procedure Bar() begin end;
    procedure Main(): Integer
    var Rec: Record T; X: Integer; Arr: array[3] of Integer; C: Boolean;
    begin
        exit(1)
#if X
        + 2
#endif
        ;
    end;
}
