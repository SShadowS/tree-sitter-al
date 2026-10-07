// B7b-1 Task 2 var-name attribute probe (spec 5.1): attributed multi-name local variable with a group
// expect: * accept
// source: predicted by B7b-1 Task 2 (spec 5.1), measured with tools.alc_probe, 2026-10-07
codeunit 50100 P
{
    procedure Q()
    var
        [NonDebuggable]
        C
#if X
        , D
#endif
        : Integer;
    begin
    end;
}
