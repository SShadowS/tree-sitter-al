// B7b-1 Task 2 var-name attribute probe (spec 5.1): group directly after the attribute holding the first name and its separator
// expect: * accept
// source: predicted by B7b-1 Task 2 (spec 5.1), measured with tools.alc_probe, 2026-10-07
codeunit 50100 P
{
    var
        [NonDebuggable]
#if X
        A,
#endif
        B: Integer;

    procedure Q()
    begin
    end;
}
