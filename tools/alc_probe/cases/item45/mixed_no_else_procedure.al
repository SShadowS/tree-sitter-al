// Still a gap (deferred item 76): a group without #else holds a declaration; with X off the attribute belongs to the procedure after the group. The recognizer declines and the input ERRORs, as before item 45.
// expect: * accept
// source: deferred item 45 (batch4/item45), measured with tools.alc_probe, 2026-11-09
codeunit 50100 P
{
    var
        G: Integer;
    [NonDebuggable]
#if X
    B: Integer;
#endif
    procedure Q()
    begin
    end;

    procedure Z()
    begin
    end;
}
