// B7b-1 Task 2 var-name attribute probe (spec 5.1): group holding a name and a trailing separator, between names
// expect: * accept
// source: predicted by B7b-1 Task 2 (spec 5.1), measured with tools.alc_probe, 2026-10-07
codeunit 50100 P
{
    var
        [NonDebuggable]
        A,
#if X
        B,
#endif
        C: Integer;

    procedure Q()
    begin
    end;
}
