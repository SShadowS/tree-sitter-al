// Item 45: an attribute in each of three arms (#if/#elif/#else) of a group opened before it, the name after `#endif`. Fixture `var attribute group: attribute in if, elif and else arms`.
// expect: * accept
// source: deferred item 45 (batch4/item45), measured with tools.alc_probe, 2026-11-09
codeunit 50100 P
{
    var
        G: Integer;
#if X
    [NonDebuggable]
#elif Y
    [NonDebuggable]
#else
    [NonDebuggable]
#endif
    D: Integer;

    procedure Z()
    begin
    end;
}
