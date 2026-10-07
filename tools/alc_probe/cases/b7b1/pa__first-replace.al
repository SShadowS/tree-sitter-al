// B7b-1 Task 2 procedure-attribute counterpart (spec 5.1): procedure header chosen by a group after the attribute; two-parameter header in the group (alc has no multi-name parameters: `Q(A, B: Integer)` is AL0104,AL0107)
// expect: * accept
// source: predicted by B7b-1 Task 2 (spec 5.1), measured with tools.alc_probe, 2026-10-07
codeunit 50100 P
{
    var
        G: Integer;

    [NonDebuggable]
#if X
    procedure Q(A: Integer; B: Integer)
#else
    procedure Q()
#endif
    begin
    end;
}
