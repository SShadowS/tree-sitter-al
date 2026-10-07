// B7b-1 Task 2 procedure-attribute counterpart (spec 5.1): nested groups choosing the header
// expect: * accept
// source: predicted by B7b-1 Task 2 (spec 5.1), measured with tools.alc_probe, 2026-10-07
codeunit 50100 P
{
    var
        G: Integer;

    [NonDebuggable]
#if X
#if Y
    procedure Q()
#else
    procedure Q(I: Integer)
#endif
#else
    procedure Q(J: Code[10])
#endif
    begin
    end;
}
