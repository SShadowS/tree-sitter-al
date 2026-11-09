// Still a gap (deferred item 76): the attribute's target is a variable with X on and a procedure with X off. The recognizer declines (the `[` stays a procedure attribute_item) and the input ERRORs, as before item 45.
// expect: * accept
// source: deferred item 45 (batch4/item45), measured with tools.alc_probe, 2026-11-09
codeunit 50100 P
{
    var
        G: Integer;
    [NonDebuggable]
#if X
    B: Integer;
#else
    procedure Q()
    begin
    end;
#endif

    procedure Z()
    begin
    end;
}
