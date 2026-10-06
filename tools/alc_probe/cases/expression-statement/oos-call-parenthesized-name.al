// B6 (_expression_statement narrowing): oos-call-parenthesized-name, `(Foo)();` (spec section 7, out of scope: an invocation of a non-name callee)
// source: B6 task 8, 2026-10-06; prediction written before the run: reject(AL0117); measured REJECT(AL0125) split and flat
// expect: * reject(AL0125)
table 50100 T { fields { field(1; K; Code[20]) { } field(2; Name; Text[30]) { } } }
codeunit 50101 Probe
{
    procedure Foo(): Boolean begin exit(true); end;
    procedure Main()
    begin
        (Foo)();
    end;
}
