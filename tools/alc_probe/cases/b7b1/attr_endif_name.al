// Pre-existing gap, NOT B7b-1 (recorded by Task 14; fixed by deferred item 45, 2026-11-09): attribute inside a group, name after `#endif` (the attribute's lookahead declined at `#endif` with no `#if`). alc accepts it in every configuration. Fixture `var attribute group: attribute alone in a group, name after the endif (attr_endif_name)`.
// expect: * accept
// source: B7b-1 Task 12 review probe, measured with tools.alc_probe, 2026-10-07
codeunit 50100 P
{
    var
#if X
        [NonDebuggable]
#endif
        A: Integer;

    procedure Q()
    begin
    end;
}
