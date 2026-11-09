// Pre-existing gap, NOT B7b-1 (recorded by Task 14; fixed by deferred item 45, 2026-11-09): attribute, then whole declarations in the arms of a group (the var_attribute_open lookahead declined at the `:` inside the group). alc accepts it in every configuration. Fixture `var attribute group: whole declarations in the arms (colon_in_group)`.
// expect: * accept
// source: B7b-1 Task 12 review probe, measured with tools.alc_probe, 2026-10-07
codeunit 50100 P
{
    var
        [NonDebuggable]
#if X
        A: Integer;
#else
        B: Integer;
#endif

    procedure Q()
    begin
    end;
}
