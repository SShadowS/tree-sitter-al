// Pre-existing gap, NOT B7b-1 (recorded by Task 14; fixed by deferred item 45, 2026-11-09): second attribute inside a group before a var name (the lookahead declined at the `[` inside the group). alc accepts it in every configuration. Fixture `var attribute group: second attribute inside a group (attr_in_group_var)`.
// expect: * accept
// source: B7b-1 Task 12 review probe, measured with tools.alc_probe, 2026-10-07
codeunit 50100 P
{
    var
        [NonDebuggable]
#if X
        [NonDebuggable]
#endif
        A: Integer;

    procedure Q()
    begin
    end;
}
