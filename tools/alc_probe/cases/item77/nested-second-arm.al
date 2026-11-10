// expect: * accept
// source: deferred item 77, the nested header group in the #else arm, attribute before the group
codeunit 50100 P
{
    [NonDebuggable]
#if X
    procedure Q()
#else
#if Y
    procedure Q(I: Integer)
#else
    procedure Q(J: Code[10])
#endif
#endif
    begin
    end;
}
