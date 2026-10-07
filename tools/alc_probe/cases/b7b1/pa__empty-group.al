// B7b-1 Task 2 procedure-attribute counterpart (spec 5.1): empty group between attribute and procedure
// expect: * accept
// source: predicted by B7b-1 Task 2 (spec 5.1), measured with tools.alc_probe, 2026-10-07
codeunit 50100 P
{
    var
        G: Integer;

    [NonDebuggable]
#if X
#endif
    procedure Q()
    begin
    end;
}
