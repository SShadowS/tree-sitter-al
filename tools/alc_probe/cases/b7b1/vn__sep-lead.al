// B7b-1 Task 2 var-name attribute probe (spec 5.1): group holding a leading separator and a name
// expect: * accept
// source: predicted by B7b-1 Task 2 (spec 5.1), measured with tools.alc_probe, 2026-10-07
codeunit 50100 P
{
    var
        [NonDebuggable]
        A
#if X
        , B
#endif
        : Integer;

    procedure Q()
    begin
    end;
}
