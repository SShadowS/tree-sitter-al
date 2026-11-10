// B7b-1e (deferred item 46): an all-empty #if group right after an Option type's last member, where the host could also own it: before a parameter list's `)`, between a return type and `begin`, after an interface procedure's return type (the parser gives each to the host, as on main). alc accepts both configurations. The same group before a variable's `;` is option_type_trailing_empty_group.al.
// expect: * accept
// source: B7b-1e probe, measured with tools.alc_probe, 2026-11-09
codeunit 50100 P
{
    procedure F(Q: Option A, B
#if X
#endif
        )
    begin
    end;

    procedure G(): Option A, B
#if X
#endif
    begin
    end;
}

interface I50101
{
    procedure K();
    procedure H(): Option A
#if X
#endif
}
