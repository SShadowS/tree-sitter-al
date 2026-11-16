// An attribute before the group, a comment and a pragma between the group and the
// procedure, and a nested group.
// expect: * accept
// source: recorded 2026-11-15, alc 18.0.41 (issue #44 family F4)
codeunit 50100 T
{
    [Obsolete('x', '1.0')]
#if A
    internal
#endif
    procedure P1()
    begin
    end;

#if A
    internal
#endif
    // a comment
#pragma warning disable AA0137
    procedure P3()
#pragma warning restore AA0137
    begin
    end;

#if A
#if B
    internal
#else
    local
#endif
#endif
    procedure P4()
    begin
    end;
}
