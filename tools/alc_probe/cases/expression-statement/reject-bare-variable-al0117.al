// B6: the parser ACCEPTS this (symbols are needed to tell) while alc rejects it with AL0117.
// source: docs/deferred-work.md item 4; roadmap B6
// expect: * reject(AL0117)
table 50100 T { fields { field(1; K; Code[20]) { } field(2; Name; Text[30]) { } } }
codeunit 50101 Probe
{
    procedure Foo(): Boolean begin exit(true); end;
    procedure "My Proc"() begin end;
    procedure Bar() begin end;
    procedure Main()
    var Rec: Record T; X: Integer; Arr: array[3] of Integer; C: Boolean;
    begin
        X;
    end;
}
