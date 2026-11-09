// Item 45: an attribute, then a group without #else whose arm is a whole declaration; with X off the attribute belongs to C, so the scan goes on after the #endif. Fixture `var attribute group: declaration in a group without else, declaration after it`.
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
    C: Integer;

    procedure Z()
    begin
    end;
}
