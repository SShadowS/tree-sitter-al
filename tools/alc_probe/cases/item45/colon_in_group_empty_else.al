// Item 45: an attribute, a group with a declaration arm and an EMPTY #else arm, then a declaration (the empty arm falls through to C). Fixture `var attribute group: declaration arm and empty else`.
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
#endif
    C: Integer;

    procedure Z()
    begin
    end;
}
