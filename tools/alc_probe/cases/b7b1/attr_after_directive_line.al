// Pre-existing gap, NOT B7b-1 (deferred work, docs/deferred-work.md item 45): an attribute, an empty group, then a second attribute before the var name. The first attribute's var_attribute_open lookahead passes the group and declines at the second `[`; ERRORs on main and on the branch.
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
