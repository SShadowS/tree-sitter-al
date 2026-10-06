// host: repeat_statement
// valid: *
// seed-source: tools/alc_probe/cases/expression-statement/torn-until-and.al (verdicts measured by alc, as recorded in its expect lines)
// source: docs/deferred-work.md item 39 point 1
// B6 (_expression_statement narrowing): torn until and
// source: recorded by B6 task 1, 2026-10-06; docs/deferred-work.md item 4
// expect: X accept
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
        repeat
            Foo();
        until C
#if X
            and (C)
#endif
        ;
    end;
}
