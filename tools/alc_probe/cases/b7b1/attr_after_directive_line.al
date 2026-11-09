// Pre-existing gap, NOT B7b-1 (fixed by deferred item 45, 2026-11-09): an attribute, an empty group, then a second attribute before the var name. The first attribute's var_attribute_open lookahead passed the group and declined at the second `[`. Fixture `var attribute group: attribute, empty group, attribute (attr_after_directive_line)`.
// expect: * accept
// source: B7b-1 final review M4, measured with tools.alc_probe, 2026-10-07
codeunit 50100 P
{
    var
        [NonDebuggable]
#if X
#endif
        [NonDebuggable]
        A: Integer;

    procedure Q()
    begin
    end;
}
