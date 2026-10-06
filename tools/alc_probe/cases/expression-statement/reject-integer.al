// B6 (_expression_statement narrowing): reject-integer.
// source: docs/deferred-work.md item 4; roadmap B6
// expect: * reject(AL0104)
table 50100 T { fields { field(1; K; Code[20]) { } field(2; Name; Text[30]) { } } }
codeunit 50101 Probe
{
    procedure Foo(): Boolean begin exit(true); end;
    procedure "My Proc"() begin end;
    procedure Bar() begin end;
    procedure Main()
    var Rec: Record T; X: Integer; Arr: array[3] of Integer; C: Boolean;
    begin
        1;
    end;
}
