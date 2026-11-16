// NOT COVERED by the F4 design: an attribute inside the arm, before the modifier. Prototyped
// (+27 states) and dropped: the attribute would sit inside `procedure`, where every
// configuration's own parse has it as a sibling before the procedure (oracle discrepancy).
// expect: * accept
// source: recorded 2026-11-15, alc 18.0.41 (issue #44 family F4)
codeunit 50100 T
{
#if A
    [Obsolete('x', '1.0')]
    internal
#endif
    procedure P2()
    begin
    end;
}
