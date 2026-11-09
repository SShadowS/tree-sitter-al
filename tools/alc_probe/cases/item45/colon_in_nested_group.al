// Item 45: an attribute, then a nested group whose every arm is a whole declaration (the inner group settles the outer arm). Fixture `var attribute group: declarations in nested arms`.
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
#else
    C: Integer;
#endif
#else
    D: Integer;
#endif

    procedure Z()
    begin
    end;
}
