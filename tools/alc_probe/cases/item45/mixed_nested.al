// Still a gap (deferred item 76): a nested group without #else; with X on and Y off the attribute belongs to the procedure after the outer group. The recognizer declines and the input ERRORs, as before item 45.
// expect: * accept
// source: deferred item 45 (batch4/item45), measured with tools.alc_probe, 2026-11-09
codeunit 50100 P
{
    var
        G: Integer;
    [NonDebuggable]
#if X
#if Y
    B: Integer;
#endif
#else
    D: Integer;
#endif
    procedure Q()
    begin
    end;

    procedure Z()
    begin
    end;
}
