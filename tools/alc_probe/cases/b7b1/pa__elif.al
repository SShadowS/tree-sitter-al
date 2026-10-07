// B7b-1 Task 2 procedure-attribute counterpart (spec 5.1): #if/#elif/#else choosing the header
// expect: * accept
// source: predicted by B7b-1 Task 2 (spec 5.1), measured with tools.alc_probe, 2026-10-07
codeunit 50100 P
{
    var
        G: Integer;

    [NonDebuggable]
#if X
    procedure Q()
#elif Y
    local procedure Q()
#else
    internal procedure Q()
#endif
    begin
    end;
}
