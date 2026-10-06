// B6 (_expression_statement narrowing): assignment continued with the semicolon inside every arm
// source: B6 final review, 2026-10-06; docs/deferred-work.md item 39 point 2
// expect: X accept
// expect: !X accept
codeunit 50101 Probe
{
    procedure Foo() begin end;
    procedure Main()
    var A: Integer; B: Integer; X: Integer;
    begin
        B := A
#if X
            + 1;
        Foo();
#else
        ;
#endif
    end;
}
