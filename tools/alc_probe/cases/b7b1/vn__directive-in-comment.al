// B7b-1 Task 2 var-name attribute probe (spec 5.1): directive line inside a block comment between names, beside a real group
// expect: * accept
// source: predicted by B7b-1 Task 2 (spec 5.1), measured with tools.alc_probe, 2026-10-07
codeunit 50100 P
{
    var
        [NonDebuggable]
        A, /*
#if X
        */ B
#if Y
        , C
#endif
        : Integer;

    procedure Q()
    begin
    end;
}
