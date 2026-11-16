// expect: * accept
// source: gh issue #44 repro 5; recorded 2026-11-15, alc 18.0.41
codeunit 50100 T
{
#if V16
    internal
#endif
    procedure A()
    begin
    end;
}
