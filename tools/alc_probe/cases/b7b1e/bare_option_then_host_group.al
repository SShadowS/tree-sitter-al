// B7b-1e (deferred item 46): a bare `Option` type (no members) directly followed by a group the host owns: a parameter group after an option-typed parameter, and a var block between a bare option return type and `begin`. alc accepts both configurations; the parser ERRORs on both (main and B7b-1e), deferred item 79.
// expect: * accept
// source: B7b-1e probe, measured with tools.alc_probe, 2026-11-09
codeunit 50100 P
{
    procedure F(Q: Option
#if X
        ; R: Integer
#endif
        )
    begin
    end;

    procedure G(): Option
#if X
    var
        I: Integer;
#endif
    begin
    end;
}
