// Item 45: the arm skip (skip_to_arm_end) must not read `#endif` inside a string or a comment. Fixture `var attribute group: directive text inside a string and a comment`.
// expect: * accept
// source: deferred item 45 (batch4/item45), measured with tools.alc_probe, 2026-11-09
codeunit 50100 P
{
    var
        G: Integer;
    [NonDebuggable]
#if X
    B: Label 'a #endif b';
#else
    C: Integer; // #endif
#endif

    procedure Z()
    begin
    end;
}
