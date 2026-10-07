// B7b-1 Task 2 procedure-attribute counterpart (spec 5.1): group payload with names, colons and a comma (inside Dictionary of [..]) in the parameter list
// expect: * accept
// source: predicted by B7b-1 Task 2 (spec 5.1), measured with tools.alc_probe, 2026-10-07
codeunit 50100 P
{
    var
        G: Integer;

    [NonDebuggable]
#if X
    procedure Q(A: Integer; D: Dictionary of [Integer, Text])
#else
    procedure Q(A: Integer; B: Text)
#endif
    begin
    end;
}
