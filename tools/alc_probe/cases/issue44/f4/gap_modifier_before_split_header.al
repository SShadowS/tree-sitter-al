// NOT COVERED by the F4 design (measured +163 states): a modifier group before a split header.
// expect: * accept
// source: recorded 2026-11-15, alc 18.0.41 (issue #44 family F4)
codeunit 50100 T
{
#if B
    internal
#endif
#if A
    procedure P2()
#else
    procedure P2(I: Integer)
#endif
    begin
    end;
}
