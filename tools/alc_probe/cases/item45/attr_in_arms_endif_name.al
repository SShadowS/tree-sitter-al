// Item 45: an attribute in each arm of a group opened before it, the name after `#endif` (var_name_list_follows crosses the #endif; an #else skips the remaining arms). Fixture `var attribute group: attribute in every arm, name after the group`.
// expect: * accept
// source: deferred item 45 (batch4/item45), measured with tools.alc_probe, 2026-11-09
codeunit 50100 P
{
    var
        G: Integer;
#if X
    [NonDebuggable]
#else
    [NonDebuggable]
#endif
    C: Integer;

    procedure Z()
    begin
    end;
}
