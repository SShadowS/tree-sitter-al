// The modifier group inside an arm of a member-level group.
// expect: * accept
// source: recorded 2026-11-15, alc 18.0.41 (issue #44 family F4)
codeunit 50100 T
{
#if A
#if B
    internal
#endif
    procedure P1()
    begin
    end;
#endif
}
